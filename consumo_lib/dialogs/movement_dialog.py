"""
dialogs/movement_dialog.py
--------------------------

Diálogo de controle de movimento CNC.

Diálogo não-modal que permanece acima da janela principal,
mas não bloqueia a interação com ela.
"""

import logging
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QScrollArea
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QGuiApplication

from consumo_lib.ui import SPACE

logger = logging.getLogger(__name__)


class MovementDialog(QDialog):
    """
    Diálogo de controle de movimento CNC.

    Características:
    - Não-modal: permite interagir com a janela principal
    - Sempre acima: permanece visível sobre outras janelas
    - Redimensionável: usuário pode ajustar tamanho
    - Sem botões: apenas o widget de movimento
    """

    def __init__(self, controller, config, parent=None):
        """
        Inicializa o diálogo de movimento.

        Args:
            controller: CNC controller
            config: AOIConfigManager
            parent: Widget pai (MainWindow)
        """
        super().__init__(parent)

        self.controller = controller
        self.config = config

        # Configurações do diálogo
        self.setWindowTitle("Controle de Movimento CNC")
        self._apply_screen_aware_geometry()

        # Diálogo não-modal e sempre acima
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowStaysOnTopHint
        )
        # Não bloqueia a janela principal
        self.setModal(False)

        # Build UI
        self._build_ui()

        logger.debug("MovementDialog criado")

    def _build_ui(self):
        """Constrói a interface do diálogo."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            SPACE.MD, SPACE.MD, SPACE.MD, SPACE.MD
        )
        layout.setSpacing(SPACE.MD)

        # Import tardio para evitar import circular
        from consumo_lib.widgets.movement_control import MovementControlWidget

        # Widget de controle de movimento
        self.movement_widget = MovementControlWidget(
            self.controller,
            self.config,
            parent=self
        )

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setWidget(self.movement_widget)
        layout.addWidget(scroll)

    def _apply_screen_aware_geometry(self):
        screen = QGuiApplication.primaryScreen()
        available = screen.availableGeometry() if screen else QRect(0, 0, 1280, 720)
        target_width = min(520, max(420, available.width() - 80))
        target_height = min(680, max(520, available.height() - 80))
        self.setMinimumSize(min(target_width, 420), min(target_height, 520))
        self.resize(target_width, target_height)

    def closeEvent(self, a0):
        """
        Handler para fechamento do diálogo.

        Apenas esconde ao invés de fechar, permitindo reabertura rápida.
        """
        # Cancela qualquer movimento em andamento
        if hasattr(self.movement_widget, '_on_direction_release'):
            self.movement_widget._on_direction_release()

        # Esconde ao invés de fechar
        if a0:
            a0.accept()
        logger.debug("MovementDialog fechado")

    def showEvent(self, a0):
        """Handler para quando o diálogo é mostrado."""
        super().showEvent(a0)
        # Garante que está acima da janela principal
        if self.parent():
            self.raise_()
            self.activateWindow()
