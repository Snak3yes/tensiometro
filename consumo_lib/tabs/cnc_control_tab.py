"""
tabs/cnc_control_tab.py
-----------------------
Aba de controle CNC e visualização de câmera.
"""

from __future__ import annotations

import logging
from PyQt6.QtWidgets import QWidget, QHBoxLayout
from PyQt6.QtCore import pyqtSignal

from .base_tab import BaseTab

logger = logging.getLogger(__name__)


class CNCControlTab(BaseTab):
    """
    Aba de controle CNC e visualização de câmera.

    Esta aba combina:
    - CameraPreviewWidget: Preview da câmera em tempo real
    - MovementControlWidget: Controles de movimentação CNC
    """

    # Sinais específicos desta aba
    image_captured = pyqtSignal(str)  # Caminho da imagem capturada

    def __init__(self, controller, config_manager, parent=None):
        """
        Inicializa a aba de controle CNC.

        Args:
            controller: AOIController
            config_manager: AOIConfigManager
            parent: Widget pai (MainWindow)
        """
        self.controller = controller
        self.config_manager = config_manager

        super().__init__(parent)

    def build_ui(self):
        """Constrói a interface da aba."""
        # Layout horizontal: preview (esquerda) + controles (direita)
        tab_layout = QHBoxLayout(self)
        tab_layout.setContentsMargins(5, 5, 5, 5)
        tab_layout.setSpacing(5)

        # Importa widgets e services
        from consumo_lib.widgets import (
            CameraPreviewWidget,
            MovementControlWidget
        )
        from consumo_lib.services import MovementService, ClickToMoveService
        from aoi_lib.fov_calibration import CameraFOVConverter, FOVCalibration

        # Criar MovementService
        self.movement_service = MovementService(
            cnc_controller=self.controller.cnc,
            config_manager=self.config_manager
        )
        logger.debug("MovementService criado para CNCControlTab")

        # Criar FOVConverter para ClickToMoveService
        fov_converter = CameraFOVConverter()

        # Carrega calibração FOV salva se existir
        fov_data = self.config_manager.get("camera", "fov_calibration", default={})
        if fov_data:
            try:
                fov_converter.set_fov_calibration(FOVCalibration.from_dict(fov_data))
                logger.debug("FOV calibration carregada no CNCControlTab")
            except Exception as e:
                logger.warning(f"Erro ao carregar FOV calibration: {e}")

        # Carrega calibração de eixos
        pulses_per_mm = self.config_manager.get("movement", "pulses_per_mm", default=100.0)
        fov_converter.set_axis_calibration("X", pulses_per_mm)
        fov_converter.set_axis_calibration("Y", pulses_per_mm)

        # Criar ClickToMoveService
        self.click_to_move_service = ClickToMoveService(
            movement_service=self.movement_service,
            fov_converter=fov_converter
        )
        logger.debug("ClickToMoveService criado para CNCControlTab")

        # Left side: camera preview (maior espaço)
        self.camera_preview = CameraPreviewWidget(
            self.controller,
            self.config_manager,
            click_to_move_service=self.click_to_move_service,  # Injeta service
            fov_converter=fov_converter  # Injeta FOV converter
        )
        self.camera_preview.image_captured.connect(self._on_image_captured)
        tab_layout.addWidget(self.camera_preview, 3)  # Proporção 3

        # Right side: movement controls (menor espaço)
        cm_left_panel = QWidget()
        cm_left_layout = QHBoxLayout(cm_left_panel)
        cm_left_layout.setContentsMargins(0, 0, 0, 0)

        self.movement_widget = MovementControlWidget(
            self.controller,
            self.config_manager,
            movement_service=self.movement_service  # Passa o service
        )
        cm_left_layout.addWidget(self.movement_widget)

        tab_layout.addWidget(cm_left_panel, 1)  # Proporção 1

        # Adiciona o layout ao layout da classe base
        self.layout.addLayout(tab_layout)

    def _on_image_captured(self, image_path: str):
        """
        Handler quando uma imagem é capturada.

        Args:
            image_path: Caminho da imagem capturada
        """
        # Repassa o sinal para quem estiver ouvindo (MainWindow)
        self.image_captured.emit(image_path)
        self.show_status(f"Imagem capturada: {image_path}")

    def refresh(self):
        """Atualiza o preview da câmera."""
        if hasattr(self.camera_preview, 'refresh'):
            self.camera_preview.refresh()
