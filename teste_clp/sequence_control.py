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
import time                    # ← NECESSÁRIO para wait_for_idle / trigger_dot
from typing import List, Protocol, Callable, Dict, Any
from dataclasses import dataclass
from PyQt6.QtCore import QThread, pyqtSignal, QObject, Qt
from pathlib import Path
from barcode_scanner import BarcodeScanner
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QGroupBox, QVBoxLayout, QHBoxLayout, QPushButton,
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
    # novo: habilita ou não o uso do offset câmera↔nozzle
    def set_offset_mode(self, apply_offset: bool): ...
    # opcional – grava SOMENTE a quantidade de dots
    def apply_dot_qty(self, qty: int): ...


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
    # ---------- feedback visual do fiducial -------------
    #  mesmo formato usado pelo FiducialConfigWidget
    #      similarity(%) , ok? , x , y , w , h
    fidMatch          = pyqtSignal(float, bool, int, int, int, int)
    fidClear          = pyqtSignal()
    # ---- overlay + código lido -------------------------------------
    bcMatch           = pyqtSignal(bool, int, int, int, int, str)  # ok,x,y,w,h,data
    bcClear           = pyqtSignal()

    def __init__(self,
                 motion: MotionBackend,
                 camera: CameraBackend | None,
                 positions: List[InspectionPosition],
                 *,
                 apply_mode: bool,              # True = APPLY  / False = VIEW
                 feed_rate: float = 1000.0):
        super().__init__()
        self._motion     = motion
        self._camera     = camera
        self._positions  = positions
        self._feed_rate  = feed_rate
        self._apply_mode = apply_mode      # guarda selecção do usuário
        self._stop_flag  = False
        # deslocamento acumulado por fiducial (pulsos)
        self._dx_acc = 0
        self._dy_acc = 0
        self._prev_was_fid = False
        self._prev_was_bc  = False

        self._scanner   = BarcodeScanner()
        self._session_dir: Path | None = None   # pasta logs/<…>

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
                
                # ---------------------------------------------------
                #  DECIDE SE OFFSET É APLICADO NESTE PONTO
                #  • VIEW  → nunca aplica
                #  • APPLY → depende do tipo da ação
                # ---------------------------------------------------
                if not self._apply_mode:           # modo VIEW
                    apply_off = False
                else:                              # modo APPLY
                    a = (pos.camera_params or {}).get("action")
                    apply_off = a not in ("barcode", "fiducial", "inspect")
                if hasattr(self._motion, "set_offset_mode"):
                    try:
                        self._motion.set_offset_mode(apply_off)
                    except Exception:
                        print("[seq] Falha ao definir modo de offset")
                        pass

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
                # --------------------------------------------------
                #  Após a CHEGADA ao ponto atual…………
                #  se o ponto ANTERIOR era um fiducial
                #  ⇒ limpamos o overlay agora (o retângulo ficou
                #     visível durante todo o deslocamento).
                # --------------------------------------------------
                if self._prev_was_fid:
                    self.fidClear.emit()

                # --------------------------------------------------
                #  limpa overlay do BARCODE
                # --------------------------------------------------
                if self._prev_was_bc:
                    self.bcClear.emit()

                # --------------------------------------------------
                # --------------------------------------------------
                #  AÇÃO “dot”
                #  A frequência (D24000) permanece a que o operador
                #  definiu na aba “Config. Registradores”.
                # --------------------------------------------------
                action = (pos.camera_params or {}).get("action")

                # ==================================================
                #          F  I  D  U  C  I  A  L
                # ==================================================
                if action == "fiducial":
                    err = self._process_fiducial(pos)
                    if err:
                        self.error.emit(err)
                        return
                    # marca que ESTE ponto é fiducial
                    self._prev_was_fid = True
                    self.progress.emit(idx, total)
                    continue
                else:
                    self._prev_was_fid = False
                
                # =================================================
                #          B  A  R  C  O  D  E
                # =================================================
                if action == "barcode":
                    err = self._process_barcode(pos)
                    if err:
                        self.error.emit(err); return
                    self._prev_was_bc = True
                    self.progress.emit(idx, total)
                    continue
                else:
                    self._prev_was_bc = False

                if action == "dot" and self._apply_mode:    # << APPLY apenas
                    # aplica configurações de dot (freq e qty)
                    qty = int((pos.camera_params or {}).get("dot_qty", 1))
                    if hasattr(self._motion, "apply_dot_qty"):
                        try:
                            self._motion.apply_dot_qty(qty)
                        except Exception:
                            print("[seq] Falha ao aplicar dot settings")
                            pass

                    # 1. envia PULSO em M5000
                    if hasattr(self._motion, "trigger_dot"):
                        ok = self._motion.trigger_dot()
                        if not ok:
                            self.error.emit("Falha ao acionar dot – M5000")
                            return

                    # 2. espera conclusão via M5001
                    if hasattr(self._motion, "wait_dot_complete"):
                        ok = self._motion.wait_dot_complete(timeout=10.0)
                        if not ok:
                            self.error.emit("Timeout aguardando fim do dot (M5001)")
                            return
                # Se modo VIEW, apenas registra que o ponto DOT foi visitado
                # (sem aplicar cola).
                if self._camera is not None:
                    try:
                        img = self._camera.capture(pos.camera_params or None)
                        self.imageCaptured.emit(img)
                    except Exception as exc:
                        print(f"[seq] Erro ao capturar imagem: {exc}")
                        self.error.emit(f"Erro na captura: {exc}")
                        return

                self.progress.emit(idx, total)

            self.finished.emit()

        except Exception as exc:
            print(f"[seq] Erro na execução da sequência: {exc}")
            self.error.emit(str(exc))

    # ------------------------------------------------------------------
    #  Processamento do ponto “barcode”
    # ------------------------------------------------------------------
    def _process_barcode(self, pos) -> str | None:
        meta = pos.camera_params or {}
        w_roi = int(meta.get("width", 400))
        h_roi = int(meta.get("height", 150))

        cam = getattr(self._motion, "_c").camera_manager

        # ------------------ calcula ROI central ----------------------
        # (basta fazer 1×; w_img/h_img só são precisos para cx/cy)
        ok, frame0 = cam._cap.read()
        if not ok:
            return "Frame indisponível"
        h_img, w_img, _ = frame0.shape
        cx, cy = w_img // 2, h_img // 2
        x0 = max(0, cx - w_roi // 2)
        y0 = max(0, cy - h_roi // 2)
        roi = (x0, y0, w_roi, h_roi)

        # ============================================================
        #  DELAYs:
        #     • 0,1 s para estabilizar depois do movimento
        #     • se falhar, +0,2 s e tenta novamente
        # ============================================================
        self.msleep(100)          # 0,1 s

        code = None
        for attempt in (1, 2):
            ok, frame = cam._cap.read()
            if not ok:
                return "Frame indisponível"
            results = self._scanner.scan(frame, roi=roi)
            if results:
                code = results[0].data.strip()
                break
            # primeira tentativa falhou → feedback vermelho + espera
            if attempt == 1:
                self.bcMatch.emit(False, x0, y0, w_roi, h_roi, "")
                self.msleep(200)      # +0,2 s

        if code is None:
            # segunda falha → erro
            self.bcMatch.emit(False, x0, y0, w_roi, h_roi, "")
            return "Leitura de código de barras falhou (2 tentativas)"

        # ---------------- sucesso -----------------------------------
        self.bcMatch.emit(True, x0, y0, w_roi, h_roi, code)

        # -------- grava no histórico ---------------------------------
        ctrl = getattr(self._motion, "_c")
        pm   = getattr(ctrl, "prog_mgr", None)
        if pm:
            try:
                if self._session_dir is None:
                    self._session_dir = pm.new_log_session(code)
                pm.append_json_log(self._session_dir, {
                    "evento": "barcode",
                    "codigo": code,
                    "t": datetime.now().isoformat()
                })
            except Exception as exc:
                ctrl.log(f"■ Falha ao registrar barcode: {exc}")

        ctrl.log(f"★ Barcode lido: {code}")
        return None

    # ------------------------------------------------------------------
    #  Processamento do ponto “fiducial”
    # ------------------------------------------------------------------
    def _process_fiducial(self, pos) -> str | None:
        """
        Executa template matching, move a cabeça para o centro
        encontrado e calcula novo offset para o backend.
        Retorna msg de erro  ou None em caso de sucesso.
        """
        meta = pos.camera_params or {}
        b64  = meta.get("template_png_b64")
        if not b64:
            return "Fiducial sem template"
        import base64, cv2, numpy as np, math, time

        # ----- converte template b64 → gray ---------------------------
        try:
            tmp_png = base64.b64decode(b64)
            tmp = cv2.imdecode(np.frombuffer(tmp_png, np.uint8),
                               cv2.IMREAD_GRAYSCALE)
        except Exception as exc:
            return f"Template inválido: {exc}"

        # captura frame atual (RGB numpy)
        cam = getattr(self._motion, "_c").camera_manager
        ok, frame_bgr = cam._cap.read()
        if not ok:
            return "Frame indisponível"
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)

        # template-matching
        res = cv2.matchTemplate(gray, tmp, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        if max_val*100 < meta.get("threshold", 70):
            return "Fiducial não encontrado (similaridade baixa)"

        # coordenadas do centro encontrado
        t_h, t_w = tmp.shape
        tx, ty   = max_loc
        cx_t = tx + t_w//2
        cy_t = ty + t_h//2

        # centro da imagem
        h, w = gray.shape
        cx_i = w//2
        cy_i = h//2

        similarity = max_val * 100
        dx_pix = cx_t - cx_i
        dy_pix = cy_t - cy_i

        # ----- converte para pulsos -----------------------------------
        ctrl  = getattr(self._motion, "_c")
        y_axis = 'Y1' if ctrl.tab_widget.currentWidget().y_axis == 'Y1' else 'Y2'
        z_cur = ctrl.current_positions['Z']
        dx_p, dy_p = ctrl.pulses_from_pixels(dx_pix, dy_pix, z_cur, y_axis)

        # ------------------------------------------------------------------
        # NÃO movemos a cabeça agora; usamos apenas offset dinâmico.
        # ------------------------------------------------------------------
        self._dx_acc += dx_p
        self._dy_acc += dy_p
        if hasattr(self._motion, "apply_dynamic_offset"):
            self._motion.apply_dynamic_offset(self._dx_acc, self._dy_acc)

        # ------------------- FEEDBACK VISUAL --------------------------
        # janela encontrada (verde se OK, vermelho se não passou no thresh)
        ok_match = similarity >= meta.get("threshold", 70)
        self.fidMatch.emit(similarity, ok_match, tx, ty, t_w, t_h)

        ctrl.log(f"★ Fiducial OK  ΔX={dx_p}  ΔY={dy_p} pulsos  "
                 f"(offset acumulado X={self._dx_acc}  Y={self._dy_acc})")
        return None


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
    # encaminha feedback do fiducial aos interessados (TableProgramTab)
    fidMatch = pyqtSignal(float, bool, int, int, int, int)
    fidClear = pyqtSignal()
    bcMatch  = pyqtSignal(bool, int, int, int, int, str)
    bcClear  = pyqtSignal()

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
            print(f"[seq] Falha ao carregar posições: {exc}")
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

        # ----------------------- FEEDBACK BARCODE -------------------
        self._lbl_bc = QLabel("Código: —")
        self._lbl_bc.setStyleSheet("QLabel { background:gray; padding:3px; }")

        v.addWidget(self._btn_execute)
        v.addWidget(self._btn_stop)

        # ------------------- NOVO SELETOR VIEW / APPLY ------------------
        hmode = QHBoxLayout()
        from PyQt6.QtWidgets import QRadioButton, QLabel as _QLabel
        self.radio_view   = QRadioButton("View")
        self.radio_apply  = QRadioButton("Apply")
        self.radio_apply.setChecked(True)          # default = aplicar offset
        hmode.addWidget(_QLabel("Offset:"))
        hmode.addWidget(self.radio_view)
        hmode.addWidget(self.radio_apply)
        hmode.addStretch()
        v.addLayout(hmode)

        v.addWidget(self._progress)
        v.addWidget(self._status)

        v.addWidget(self._lbl_bc)

        main = QVBoxLayout(self)
        main.addWidget(grp)
        main.addStretch()

        # ligações
        self._btn_execute.clicked.connect(self._start)
        self._btn_stop.clicked.connect(self._stop)

        # troca de modo view/apply
        self.radio_view.toggled.connect(
            lambda checked: self._on_mode_changed(checked))
 
    # ----------------------------- modo offset ------------------------
    def _on_mode_changed(self, view_checked: bool):
        """
        view_checked = True  → modo VIEW (não aplica offset)
        False                → radio_apply ativo (aplica offset)
        """
        apply_off = not view_checked
        if hasattr(self._motion, "set_offset_mode"):
            try:
                self._motion.set_offset_mode(apply_off)
            except Exception:
                print("[seq] Falha ao definir modo de offset")
                pass
        self._status.setText("Modo: VIEW (somente visualização)"
                             if view_checked else
                             "Modo: APPLY (produção)")



    # ------------------------ handlers -----------------------------
    def _start(self):
        # ----------------- verifica posições -----------------
        if not self._positions:
            QMessageBox.warning(self, "Aviso", "Nenhuma posição definida")
            return
        # ----------------- encerra runner anterior ------------
        if self._runner is not None:
            if self._runner.isRunning():
                QMessageBox.warning(self, "Execução",
                                    "A sequência ainda está em andamento.")
                return
            # desconecta e destrói completamente
            try:
                self._runner.finished.disconnect()
                self._runner.error.disconnect()
            except Exception:
                pass
            self._runner.deleteLater()
            self._runner = None

        self._progress.setRange(0, len(self._positions))
        self._progress.setValue(0)
        self._status.setText("Executando…")
        self._lbl_bc.setText("Código: —")
        self._btn_execute.setEnabled(False)
        self._btn_stop.setEnabled(True)

        self._runner = SequenceRunnerThread(
            self._motion,
            self._camera,
            self._positions,
            apply_mode=self.radio_apply.isChecked()   # passa modo global
        )
        self._runner.progress.connect(self._on_progress)
        self._runner.imageCaptured.connect(self.imageCaptured)
        self._runner.finished.connect(self._on_finished)
        self._runner.error.connect(self._on_error)
        self._runner.fidMatch.connect(self.fidMatch)
        self._runner.fidClear.connect(self.fidClear)
        self._runner.bcMatch.connect(self.bcMatch)
        self._runner.bcClear.connect(self.bcClear)

        # ---------- exibe código lido na própria UI -----------------
        self._runner.bcMatch.connect(self._on_bc_match)

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
        # ---------- encerra thread e limpa ponteiro -----------
        if self._runner:
            self._runner.wait(1000)
            self._runner.deleteLater()
            self._runner = None

    # ---------------------------------------------------------------
    #  B A R C O D E   s l o t
    # ---------------------------------------------------------------
    def _on_bc_match(self, ok: bool, x:int, y:int, w:int, h:int, text:str):
        """
        Atualiza label “Código:” logo abaixo do status.
        • ok = True  → mostra texto do código
        • ok = False → indica falha
        A label não é limpa pelo bcClear; permanece visível
        até nova leitura ou até o operador iniciar outra execução.
        """
        if ok and text:
            self._lbl_bc.setText(f"Código: {text}")
        else:
            self._lbl_bc.setText("Código: — (não lido)")

    def _on_error(self, msg: str):
        self._status.setText(f"Erro: {msg}")
        self._btn_execute.setEnabled(True)
        self._btn_stop.setEnabled(False)
        self.sequenceError.emit(msg)
        if self._runner:
            self._runner.wait(1000)
            self._runner.deleteLater()
            self._runner = None


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
