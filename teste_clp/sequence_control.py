"""
sequence_control.py
-------------------
Módulo plug-and-play para executar uma sequência de posições (X,Y,Z)
num sistema CNC + câmera.

Dependências:
    PyQt6>=6.5
    (Opcional) o dataclass InspectionPosition já usado nos módulos anteriores.
               Caso não exista no projeto hospedeiro basta
               substituir por dicts {'x':..,'y':..,'z':..}.
"""

from __future__ import annotations
from typing import List, Protocol, Callable, Dict, Any
from dataclasses import dataclass

from PyQt6.QtCore import QThread, pyqtSignal, QObject, Qt
from PyQt6.QtWidgets import (
    QWidget, QGroupBox, QVBoxLayout, QPushButton,
    QProgressBar, QLabel, QFileDialog, QMessageBox
)


# ----------------------------------------------------------------------
# 1) Modelo de dados (reaproveitável)
# ----------------------------------------------------------------------
@dataclass
class InspectionPosition:
    name: str
    x: float
    y2: float
    y1: float
    z: float = 0.0
    camera_params: Dict[str, Any] | None = None


# ----------------------------------------------------------------------
# 2) Protocolos (interfaces) para back-ends
# ----------------------------------------------------------------------
class MotionBackend(Protocol):
    """Funções mínimas exigidas do sistema de movimento (GRBL, PLC etc.)."""
    def move_to_absolute_position(self,
                                  x:  float | None,
                                  y2: float | None,
                                  y1: float | None,
                                  z:  float | None,
                                  feed_rate: float = 1000) -> bool: ...
    def wait_for_idle(self) -> bool: ...
    # opcional, mas ajuda:
    def set_feed_rate(self, feed_rate: float): ...


class CameraBackend(Protocol):
    """Funções mínimas exigidas da câmera (pode ser dummy)."""
    def capture(self, params: Dict[str, Any] | None = None): ...


# ----------------------------------------------------------------------
# 3) Thread que percorre a sequência
# ----------------------------------------------------------------------
class SequenceRunnerThread(QThread):
    progress          = pyqtSignal(int, int)  # idx_atual, total
    imageCaptured     = pyqtSignal(object)    # imagem capturada
    finished          = pyqtSignal()
    error             = pyqtSignal(str)

    def __init__(self,
                 motion: MotionBackend,
                 camera: CameraBackend | None,
                 positions: List[InspectionPosition],
                 feed_rate: float = 1000.0):
        super().__init__()
        self._motion     = motion
        self._camera     = camera
        self._positions  = positions
        self._feed_rate  = feed_rate
        self._stop_flag  = False

    def request_stop(self):
        self._stop_flag = True

    def run(self):
        try:
            total = len(self._positions)
            if total == 0:
                self.error.emit("Sequência vazia")
                return
            # feed opcional
            if hasattr(self._motion, "set_feed_rate"):
                self._motion.set_feed_rate(self._feed_rate)

            for idx, pos in enumerate(self._positions, 1):
                if self._stop_flag:
                    self.error.emit("Execução interrompida pelo usuário")
                    return

                ok = self._motion.move_to_absolute_position(
                    pos.x, pos.y2, pos.y1, pos.z, feed_rate=self._feed_rate)
                if not ok:
                    self.error.emit(f"Falha ao enviar movimento para {pos.name}")
                    return
                if not self._motion.wait_for_idle():
                    self.error.emit("Timeout de movimento")
                    return

                # ------------ dwell 100 ms entre pontos --------------
                # evita que o próximo comando seja enfileirado antes
                # do CLP realmente liberar todos os eixos.
                self.msleep(100)            # (== 0,1 s)

                if self._camera is not None:
                    try:
                        img = self._camera.capture(pos.camera_params or None)
                        self.imageCaptured.emit(img)
                    except Exception as exc:
                        self.error.emit(f"Erro na captura: {exc}")
                        return

                self.progress.emit(idx, total)

            self.finished.emit()

        except Exception as exc:
            self.error.emit(str(exc))


# ----------------------------------------------------------------------
# 4) Widget de controle da sequência
# ----------------------------------------------------------------------
class SequenceControlWidget(QWidget):
    """
    Widget genérico com:
        • Botão Executar
        • Botão Parar
        • Barra de progresso
        • Status
    Sinais principais do runner são replicados para facilitar
    ligação com outros componentes da GUI.
    """

    imageCaptured = pyqtSignal(object)
    sequenceFinished = pyqtSignal()
    sequenceError = pyqtSignal(str)

    def __init__(self,
                 motion: MotionBackend,
                 camera: CameraBackend | None = None,
                 parent=None):
        super().__init__(parent)
        self._motion = motion
        self._camera = camera
        self._positions: List[InspectionPosition] = []
        self._runner: SequenceRunnerThread | None = None
        self._build_ui()

    # ------------------------ API pública --------------------------
    def set_positions(self, positions: List[InspectionPosition]):
        """Define/atualiza a lista de posições da sequência."""
        self._positions = positions
        self._status.setText(f"{len(positions)} posições prontas")

    def load_positions_from_callable(self, loader: Callable[[], List[InspectionPosition]]):
        """Permite ligar um botão 'Carregar…' externo a esta função."""
        try:
            self.set_positions(loader())
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Falha ao carregar posições:\n{exc}")

    # ------------------------ UI -----------------------------------
    def _build_ui(self):
        grp = QGroupBox("Controle de Sequência")
        v = QVBoxLayout(grp)

        self._btn_execute = QPushButton("Executar Sequência")
        self._btn_stop    = QPushButton("Parar")
        self._btn_stop.setEnabled(False)

        self._progress = QProgressBar()
        self._progress.setValue(0)
        self._progress.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._status = QLabel("Sem sequência")

        v.addWidget(self._btn_execute)
        v.addWidget(self._btn_stop)
        v.addWidget(self._progress)
        v.addWidget(self._status)

        main = QVBoxLayout(self)
        main.addWidget(grp)
        main.addStretch()

        # ligações
        self._btn_execute.clicked.connect(self._start)
        self._btn_stop.clicked.connect(self._stop)

    # ------------------------ handlers -----------------------------
    def _start(self):
        if not self._positions:
            QMessageBox.warning(self, "Aviso", "Nenhuma posição definida")
            return
        if self._runner and self._runner.isRunning():
            return     # já rodando

        self._progress.setRange(0, len(self._positions))
        self._progress.setValue(0)
        self._status.setText("Executando…")
        self._btn_execute.setEnabled(False)
        self._btn_stop.setEnabled(True)

        self._runner = SequenceRunnerThread(
            self._motion, self._camera, self._positions
        )
        self._runner.progress.connect(self._on_progress)
        self._runner.imageCaptured.connect(self.imageCaptured)
        self._runner.finished.connect(self._on_finished)
        self._runner.error.connect(self._on_error)
        self._runner.start()

    def _stop(self):
        if self._runner and self._runner.isRunning():
            self._runner.request_stop()

    def _on_progress(self, idx: int, total: int):
        self._progress.setValue(idx)
        self._status.setText(f"{idx}/{total} concluídos")

    def _on_finished(self):
        self._status.setText("Concluída")
        self._btn_execute.setEnabled(True)
        self._btn_stop.setEnabled(False)
        self.sequenceFinished.emit()

    def _on_error(self, msg: str):
        self._status.setText(f"Erro: {msg}")
        self._btn_execute.setEnabled(True)
        self._btn_stop.setEnabled(False)
        self.sequenceError.emit(msg)


# ----------------------------------------------------------------------
# 5) Demonstração stand-alone
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from random import random
    from PyQt6.QtWidgets import QApplication

    # --- Back-ends fictícios ----------------------------------------
    class _DummyMotion:
        def move_to_absolute_position(self, x, y2, y1, z, feed_rate=1000):
            print(f"[motion]  X={x:.2f}  Y2={y2:.2f}  Y1={y1:.2f}  Z={z:.2f}  F{feed_rate}")
            return True
        def wait_for_idle(self): pass
        def set_feed_rate(self, fr): print("[motion] Feed =", fr)

    class _DummyCamera:
        def capture(self, params=None):
            import numpy as np
            # gera imagem RGB aleatória 320x240
            return (np.random.rand(240, 320, 3) * 255).astype("uint8")

    # --- dados de exemplo -------------------------------------------
    demo_positions = [
        InspectionPosition(f"P{i+1}", random()*100, random()*80, 0.0)
        for i in range(5)
    ]

    # --- aplica ao widget ------------------------------------------
    app = QApplication(sys.argv)
    widget = SequenceControlWidget(_DummyMotion(), _DummyCamera())
    widget.set_positions(demo_positions)
    widget.resize(280, 200)
    widget.show()

    widget.imageCaptured.connect(lambda img: print("[seq] imagem capturada", type(img)))

    sys.exit(app.exec())
