"""
fov_calibration_dialog.py
-------------------------
Permite calibrar o campo-de-visão da câmera em dois pontos de Z
(ex.: Z=0 e Z=700).  Os valores são gravados em settings.json.
"""
from PyQt6.QtWidgets import (
    QDialog, QGridLayout, QLabel, QSpinBox, QDoubleSpinBox,
    QPushButton, QHBoxLayout
)
from PyQt6.QtCore import Qt

class FOVCalibrationDialog(QDialog):
    def __init__(self, settings_mgr, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Calibração de Campo de Visão")
        self._s = settings_mgr
        self._orig = settings_mgr.camera_fov
        self._build_ui()

    # ----------------------- UI ---------------------------------
    def _build_ui(self):
        g = QGridLayout(self)
        # linha 0 – cabeçalhos
        g.addWidget(QLabel("Parâmetro"), 0, 0)
        g.addWidget(QLabel("Z-ref 0"), 0, 1)
        g.addWidget(QLabel("Z-ref 1"), 0, 2)
        # linha 1 – Z pulsos
        g.addWidget(QLabel("Z (pulsos):"), 1, 0)
        self.sp_z0 = QSpinBox(); self.sp_z0.setRange(-2_147_483_648, 2_147_483_647)
        self.sp_z1 = QSpinBox(); self.sp_z1.setRange(-2_147_483_648, 2_147_483_647)
        self.sp_z0.setValue(self._orig.get("z0_z_pulses", 0))
        self.sp_z1.setValue(self._orig.get("z1_z_pulses", 700))
        g.addWidget(self.sp_z0, 1, 1); g.addWidget(self.sp_z1, 1, 2)
        # linha 2 – largura
        g.addWidget(QLabel("Largura visível (mm):"), 2, 0)
        self.sp_w0 = QDoubleSpinBox(); self.sp_w0.setRange(0.01, 1000); self.sp_w0.setDecimals(2)
        self.sp_w1 = QDoubleSpinBox(); self.sp_w1.setRange(0.01, 1000); self.sp_w1.setDecimals(2)
        self.sp_w0.setValue(self._orig.get("z0_width_mm", 61.0))
        self.sp_w1.setValue(self._orig.get("z1_width_mm", 30.5))
        g.addWidget(self.sp_w0, 2, 1); g.addWidget(self.sp_w1, 2, 2)
        # linha 3 – altura
        g.addWidget(QLabel("Altura visível (mm):"), 3, 0)
        self.sp_h0 = QDoubleSpinBox(); self.sp_h0.setRange(0.01, 1000); self.sp_h0.setDecimals(2)
        self.sp_h1 = QDoubleSpinBox(); self.sp_h1.setRange(0.01, 1000); self.sp_h1.setDecimals(2)
        self.sp_h0.setValue(self._orig.get("z0_height_mm", 45.0))
        self.sp_h1.setValue(self._orig.get("z1_height_mm", 22.5))
        g.addWidget(self.sp_h0, 3, 1); g.addWidget(self.sp_h1, 3, 2)
        # botões
        h = QHBoxLayout()
        btn_ok  = QPushButton("Salvar"); btn_ok.clicked.connect(self._save)
        btn_can = QPushButton("Cancelar"); btn_can.clicked.connect(self.reject)
        h.addStretch(); h.addWidget(btn_ok); h.addWidget(btn_can)
        g.addLayout(h, 4, 0, 1, 3)

    # ----------------------- salvar ----------------------------
    def _save(self):
        fov = {
            "z0_z_pulses":   self.sp_z0.value(),
            "z0_width_mm":   self.sp_w0.value(),
            "z0_height_mm":  self.sp_h0.value(),
            "z1_z_pulses":   self.sp_z1.value(),
            "z1_width_mm":   self.sp_w1.value(),
            "z1_height_mm":  self.sp_h1.value()
        }
        self._s.camera_fov = fov
        self._s.save()
        self.accept()