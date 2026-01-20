"""
dialogs/fov_calibration.py
---------------------------
Diálogo para calibração de campo de visão (FOV) da câmera.
"""

from PyQt6.QtWidgets import (
    QDialog, QGridLayout, QLabel, QSpinBox, QDoubleSpinBox,
    QPushButton, QHBoxLayout, QVBoxLayout, QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt

from aoi_lib.fov_calibration import FOVCalibration
from consumo_lib.ui import COLORS, TYPO, SPACE
from consumo_lib.ui.widget_standards import StandardButton
import logging

log = logging.getLogger(__name__)


class FOVCalibrationDialog(QDialog):
    """
    Diálogo para calibração do campo de visão da câmera.

    Para o tensiômetro, a câmera é FIXA no eixo Z, então o FOV
    não varia com a altura. Apenas um ponto de calibração é necessário.
    """

    def __init__(self, config_manager=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Calibração de Campo de Visão")
        self.setMinimumWidth(400)

        self._config_manager = config_manager
        self._load_current_values()
        self._build_ui()

    def _load_current_values(self):
        """Carrega valores atuais do config_manager ou usa defaults."""
        if self._config_manager:
            data = self._config_manager.get_config("camera_fov", {})
            self._fov = FOVCalibration.from_dict(data)
        else:
            self._fov = FOVCalibration()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Instruções
        info = QLabel(
            "Configure o campo de visão da câmera.\n"
            "\n"
            "NOTA: A câmera do tensiômetro é FIXA no eixo Z, então\n"
            "o campo de visão é constante (não varia com a altura)."
        )
        info.setWordWrap(True)
        info.setStyleSheet(f"color: {COLORS.TEXT_HINT}; margin-bottom: {SPACE.SM}px;")
        layout.addWidget(info)

        # Grupo de calibração
        group = QGroupBox("Calibração do Campo de Visão")
        grid = QGridLayout(group)

        # Linha 1: Largura visível
        grid.addWidget(QLabel("Largura visível (mm):"), 0, 0)

        self.sp_w0 = QDoubleSpinBox()
        self.sp_w0.setRange(1, 1000)
        self.sp_w0.setDecimals(2)
        self.sp_w0.setValue(self._fov.z0_width_mm)
        grid.addWidget(self.sp_w0, 0, 1)

        # Linha 2: Altura visível
        grid.addWidget(QLabel("Altura visível (mm):"), 1, 0)

        self.sp_h0 = QDoubleSpinBox()
        self.sp_h0.setRange(1, 1000)
        self.sp_h0.setDecimals(2)
        self.sp_h0.setValue(self._fov.z0_height_mm)
        grid.addWidget(self.sp_h0, 1, 1)

        layout.addWidget(group)

        # Dica
        tip = QLabel(
            "💡 Dica: Para calibrar, posicione uma régua ou objeto de dimensões \n"
            "conhecidas no plano focal e meça a largura/altura visível no vídeo."
        )
        tip.setWordWrap(True)
        tip.setStyleSheet(f"color: {COLORS.TEXT_HINT}; font-size: {TYPO.LABEL_SMALL}px; margin-top: {SPACE.SM}px;")
        layout.addWidget(tip)

        # Botões
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_save = StandardButton("Salvar", variant="primary")
        btn_save.clicked.connect(self._save)
        btn_layout.addWidget(btn_save)

        btn_cancel = StandardButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        layout.addLayout(btn_layout)

    def _save(self):
        """Salva calibração no config_manager."""
        # Para câmera fixa, z1 = z0 (FOVCalibration força isso)
        fov = FOVCalibration(
            z0_z_pulses=0,
            z0_width_mm=self.sp_w0.value(),
            z0_height_mm=self.sp_h0.value(),
        )

        if self._config_manager:
            self._config_manager.set_config("camera_fov", fov.to_dict())
            log.info("Calibração de FOV salva")

        self._fov = fov
        self.accept()

    def get_calibration(self) -> FOVCalibration:
        """Retorna calibração atual."""
        return self._fov
