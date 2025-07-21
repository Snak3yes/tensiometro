"""
cnc_calibration_widget.py
-------------------------
Widget genérico para calcular e aplicar a calibração de passos por
milímetro (steps/mm) em sistemas CNC que usem motores de passo.

Fórmula adoptada
    steps_per_mm = (motor_full_steps_rev · microsteps · gear_ratio) / screw_pitch_mm

onde
    • motor_full_steps_rev  – passos “inteiros” por volta (200 na maioria dos NEMA-17/23)
    • microsteps            – divisão electrónica do driver (1,2,4,8,16,32…)
    • gear_ratio            – relação de engrenagem/polia (se directo ⇒ 1.0)
    • screw_pitch_mm        – avanço do fuso (mm por volta).  Para correia
      dentada use pitch_mm = número_de_dentes_da_polia * passo_da_correa_mm.

O módulo expõe:
    1. classe CalibrationCalculator  (lógica pura → testável sem Qt)
    2. protocolo CalibrationBackend  (driver que receberá os novos steps/mm)
    3. widget CalibWidget            (interface PyQt 6)

Autor: 2025 – livre para uso sob MIT.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol

# --------------------- 1) Lógica pura ---------------------------------
@dataclass
class CalibrationParameters:
    motor_steps_rev: float = 200.0      # passos "cheios" por volta
    microsteps:      float = 16.0       # divisão do driver
    gear_ratio:      float = 1.0        # >1 se há redução; <1 se multiplicação
    screw_pitch_mm:  float = 5.0        # avanço do fuso (mm)

class CalibrationCalculator:
    """Funções estáticas que podem ser unit-testadas sem Qt."""
    @staticmethod
    def steps_per_mm(p: CalibrationParameters) -> float:
        if p.screw_pitch_mm <= 0:
            raise ValueError("screw_pitch_mm deve ser > 0")
        return (p.motor_steps_rev * p.microsteps * p.gear_ratio) / p.screw_pitch_mm

# --------------------- 2) Backend para aplicação ----------------------
class CalibrationBackend(Protocol):
    """
    Qualquer classe fornecida à GUI deve implementar:
        apply_steps_per_mm(steps: float) -> bool
    (pode aplicar nos eixos X/Y/Z conforme necessidade interna)
    """
    def apply_steps_per_mm(self, steps: float) -> bool: ...

# --------------------- 3) Interface PyQt 6 ----------------------------
from PyQt6.QtWidgets import (
    QWidget, QGroupBox, QFormLayout, QDoubleSpinBox, QHBoxLayout,
    QPushButton, QMessageBox, QLabel, QComboBox, QVBoxLayout
)
from PyQt6.QtCore import pyqtSignal

class CalibWidget(QWidget):
    """
    Widget completo para o utilizador introduzir parâmetros,
    ver o resultado em tempo-real e aplicar ao backend.

    Sinais:
        applied(float)  – emitido quando o backend confirma aplicação
    """
    applied = pyqtSignal(float)

    def __init__(self,
                 backend: CalibrationBackend | None = None,
                 parent=None):
        super().__init__(parent)
        self._backend = backend
        self._build_ui()

    # ---------------------- pública ------------------------
    def parameters(self) -> CalibrationParameters:
        return CalibrationParameters(
            motor_steps_rev=self.spin_steps_rev.value(),
            microsteps=float(self.cmb_micro.currentText()),
            gear_ratio=self.spin_gear.value(),
            screw_pitch_mm=self.spin_pitch.value()
        )

    # ---------------------- UI ------------------------------
    def _build_ui(self):
        box = QGroupBox("Calibração de Steps/mm")
        form = QFormLayout(box)

        # passos/volta – maioria é 200
        self.spin_steps_rev = QDoubleSpinBox()
        self.spin_steps_rev.setRange(1, 2000)
        self.spin_steps_rev.setValue(200)
        self.spin_steps_rev.setDecimals(0)
        form.addRow("Passos por volta (motor):", self.spin_steps_rev)

        # micro-steps – drop-down comum
        self.cmb_micro = QComboBox()
        self.cmb_micro.addItems([str(v) for v in (1, 2, 4, 8, 16, 32, 64, 128, 256)])
        self.cmb_micro.setCurrentText("16")
        form.addRow("Microsteps do driver:", self.cmb_micro)

        # relação de engrenagem
        self.spin_gear = QDoubleSpinBox()
        self.spin_gear.setRange(0.01, 100.0)
        self.spin_gear.setSingleStep(0.01)
        self.spin_gear.setValue(1.0)
        form.addRow("Relação engrenagem (1=directo):", self.spin_gear)

        # passo do fuso / avanço da correia
        self.spin_pitch = QDoubleSpinBox()
        self.spin_pitch.setRange(0.01, 100.0)
        self.spin_pitch.setSingleStep(0.05)
        self.spin_pitch.setValue(5.0)
        form.addRow("Passo do fuso (mm/volta):", self.spin_pitch)

        # resultado
        self.lbl_result = QLabel("0.000 steps/mm")
        form.addRow("Resultado:", self.lbl_result)

        # botões
        h = QHBoxLayout()
        self.btn_apply = QPushButton("Aplicar ao Controlador")
        h.addWidget(self.btn_apply)
        form.addRow(h)

        # layout externo
        v = QVBoxLayout(self)
        v.addWidget(box)
        v.addStretch()

        # conexões
        for w in (self.spin_steps_rev, self.cmb_micro,
                  self.spin_gear, self.spin_pitch):
            if hasattr(w, "valueChanged"):
                w.valueChanged.connect(self._update_result)
            else:  # QComboBox
                w.currentTextChanged.connect(self._update_result)
        self._update_result()
        self.btn_apply.clicked.connect(self._on_apply_clicked)

    # ---------------------- slots ---------------------------
    def _update_result(self):
        try:
            steps = CalibrationCalculator.steps_per_mm(self.parameters())
            self.lbl_result.setText(f"{steps:.3f} steps/mm")
        except Exception:
            self.lbl_result.setText("—")

    def _on_apply_clicked(self):
        if self._backend is None:
            QMessageBox.warning(self, "Sem backend",
                                "Nenhum backend de CNC foi fornecido.")
            return
        steps = CalibrationCalculator.steps_per_mm(self.parameters())
        ok = False
        try:
            ok = self._backend.apply_steps_per_mm(steps)
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Falha ao aplicar:\n{exc}")
            return
        if ok:
            QMessageBox.information(self, "Sucesso",
                                    f"Parâmetro aplicado: {steps:.3f} steps/mm")
            self.applied.emit(steps)
        else:
            QMessageBox.critical(self, "Erro",
                                 "Backend reportou falha ao aplicar o valor.")

# ---------------------- Demo isolado -----------------------
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys, logging
    logging.basicConfig(level=logging.INFO)

    # Backend fictício só para demonstração
    class _DummyBackend:
        def apply_steps_per_mm(self, steps: float) -> bool:
            print(f"[BACKEND] set $100=$101=$102 ← {steps:.3f}")
            return True

    app = QApplication(sys.argv)
    w = CalibWidget(_DummyBackend())
    w.setWindowTitle("Demo – Calibração CNC")
    w.resize(320, 220)
    w.show()
    sys.exit(app.exec())
