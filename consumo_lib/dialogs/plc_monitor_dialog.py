"""
dialogs/plc_monitor_dialog.py
-----------------------------

Diálogo de monitoramento do CLP.

Diálogo não-modal que permanece acima da janela principal,
mas não bloqueia a interação com ela.
"""

import logging
from PyQt6.QtWidgets import QDialog, QVBoxLayout
from PyQt6.QtCore import Qt

from consumo_lib.ui import SPACE

logger = logging.getLogger(__name__)


class PLCMonitorDialog(QDialog):
    """
    Diálogo de monitoramento do CLP.

    Características:
    - Não-modal: permite interagir com a janela principal
    - Sempre acima: permanece visível sobre outras janelas
    - Redimensionável: usuário pode ajustar tamanho
    - Sem botões: apenas o widget de monitor CLP
    """

    def __init__(self, controller, parent=None):
        """
        Inicializa o diálogo de monitor CLP.

        Args:
            controller: CNC controller
            parent: Widget pai (MainWindow)
        """
        super().__init__(parent)

        self.controller = controller

        # Configurações do diálogo
        self.setWindowTitle("Monitor CLP")
        self.setMinimumSize(600, 500)

        # Diálogo não-modal e sempre acima
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowStaysOnTopHint
        )
        # Não bloqueia a janela principal
        self.setModal(False)

        # Build UI
        self._build_ui()

        logger.debug("PLCMonitorDialog criado")

    def _build_ui(self):
        """Constrói a interface do diálogo."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            SPACE.MD, SPACE.MD, SPACE.MD, SPACE.MD
        )
        layout.setSpacing(SPACE.MD)

        # Import tardio para evitar import circular
        from consumo_lib.widgets.plc_monitor import PLCMonitorWidget

        # Widget de monitor CLP
        self.plc_monitor_widget = PLCMonitorWidget(
            self.controller,
            parent=self
        )

        layout.addWidget(self.plc_monitor_widget)

    def showEvent(self, a0):
        """Handler para quando o diálogo é mostrado."""
        super().showEvent(a0)
        # Garante que está acima da janela principal
        if self.parent():
            self.raise_()
            self.activateWindow()

    def closeEvent(self, a0):
        """Handler para fechamento do diálogo."""
        if a0:
            a0.accept()
        logger.debug("PLCMonitorDialog fechado")