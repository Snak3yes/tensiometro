"""
tabs/cnc_control_tab.py
-----------------------
Aba de controle CNC e visualização de câmera.
"""

from __future__ import annotations

import logging
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QStackedWidget
from PyQt6.QtCore import pyqtSignal, Qt

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
        # NOTA: Não passar 'self' como pai porque BaseTab já criou self.layout
        tab_layout = QHBoxLayout()
        tab_layout.setContentsMargins(5, 5, 5, 5)
        tab_layout.setSpacing(5)

        # Importa widgets e services
        from consumo_lib.widgets import (
            CameraPreviewWidget,
            MovementControlWidget
        )
        from consumo_lib.services import MovementService, ClickToMoveService
        from aoi_lib.fov_calibration import CameraFOVConverter, FOVCalibration
        from aoi_lib.movement_orchestrator import MovementOrchestrator

        # Criar MovementService (Legado para ClickToMove)
        self.movement_service = MovementService(
            cnc_controller=self.controller.cnc,
            config_manager=self.config_manager
        )
        logger.debug("MovementService criado para CNCControlTab")
        
        # Criar MovementOrchestrator (Novo para MovementWidget)
        self.orchestrator = MovementOrchestrator(
            controller=self.controller.cnc,
            config_manager=self.config_manager
        )
        logger.debug("MovementOrchestrator criado para CNCControlTab")

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

        # Right side: movement controls com QStackedWidget
        # Permite alternar visibilidade do movement_widget sem movê-lo
        # Camada 0: Widget de movimento visível em modo normal
        # Camada 1: Placeholder quando wizard está aberto
        from PyQt6.QtWidgets import QStackedWidget

        self.movement_stack = QStackedWidget()
        self.movement_stack.setMinimumSize(200, 400)

        # CAMADA 0: Widget de movimento visível em modo normal
        normal_widget = QWidget()
        normal_layout = QVBoxLayout(normal_widget)
        normal_layout.setContentsMargins(0, 0, 0, 0)

        self.movement_widget = MovementControlWidget(
            self.controller,
            self.config_manager,
            orchestrator=self.orchestrator
        )
        normal_layout.addWidget(self.movement_widget)

        self.movement_stack.addWidget(normal_widget)

        # CAMADA 1: Placeholder quando wizard está aberto
        wizard_placeholder_widget = QWidget()
        wizard_layout = QVBoxLayout(wizard_placeholder_widget)
        wizard_layout.setContentsMargins(10, 10, 10, 10)

        wizard_label = QLabel("Controle de movimento disponível na aba 3\ndo Engineering Wizard")
        wizard_label.setWordWrap(True)
        wizard_label.setStyleSheet("""
            QLabel {
                background-color: #FFF3CD;
                border: 1px solid #FFC107;
                border-radius: 4px;
                padding: 10px;
                color: #856404;
                font-weight: bold;
            }
        """)
        wizard_layout.addWidget(wizard_label)
        wizard_layout.addStretch()

        self.movement_stack.addWidget(wizard_placeholder_widget)

        # Mostrar camada 0 por padrão (modo normal)
        self.movement_stack.setCurrentIndex(0)

        tab_layout.addWidget(self.movement_stack, 1)  # Proporção 1

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

    def set_wizard_mode(self, wizard_open: bool):
        """
        Alterna a visibilidade do movement_widget baseado no estado do wizard.

        Args:
            wizard_open: True se wizard está aberto, False se está fechado
        """
        if wizard_open:
            # Wizard aberto: Mostra placeholder (camada 1)
            self.movement_stack.setCurrentIndex(1)
            logger.info("📖 MovementControlWidget oculto (wizard aberto)")
        else:
            # Wizard fechado: Mostra movement_widget (camada 0)
            self.movement_stack.setCurrentIndex(0)
            logger.info("✅ MovementControlWidget visível (wizard fechado)")