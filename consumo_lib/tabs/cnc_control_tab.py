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

        # Importa widgets
        from aoi_lib.stencil_tracker_ui import (
            CameraPreviewWidget,
            MovementControlWidget
        )

        # Left side: camera preview (maior espaço)
        self.camera_preview = CameraPreviewWidget(
            self.controller,
            self.config_manager
        )
        self.camera_preview.image_captured.connect(self._on_image_captured)
        tab_layout.addWidget(self.camera_preview, 3)  # Proporção 3

        # Right side: movement controls (menor espaço)
        cm_left_panel = QWidget()
        cm_left_layout = QHBoxLayout(cm_left_panel)
        cm_left_layout.setContentsMargins(0, 0, 0, 0)

        self.movement_widget = MovementControlWidget(
            self.controller,
            self.config_manager
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
