"""
dialogs/tracking_dialog.py
--------------------------

Diálogo de Rastreabilidade de Stencils.

Diálogo não-modal que permanece acima da janela principal,
mas não bloqueia a interação com ela.

Substitui a aba "Rastreabilidade" que foi removida da interface.

Autor: Claude Code
Data: 2026-03-29
"""

import logging
from PyQt6.QtWidgets import QDialog, QVBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal

from consumo_lib.ui import SPACE

logger = logging.getLogger(__name__)


class TrackingDialog(QDialog):
    """
    Diálogo de Rastreabilidade de Stencils.

    Características:
    - Não-modal: permite interagir com a janela principal
    - Sempre acima: permanece visível sobre outras janelas
    - Redimensionável: usuário pode ajustar tamanho
    - Contém StencilIdentificationWidget

    Signals (repassed from StencilIdentificationWidget):
        stencil_selected: Emitido quando stencil é selecionado
        stencil_cleared: Emitido quando seleção é limpa
        recipe_requested: Emitido quando receita é solicitada
    """

    # Repassed signals
    stencil_selected = pyqtSignal(object)  # Stencil
    stencil_cleared = pyqtSignal()
    recipe_requested = pyqtSignal(str)  # recipe_name
    measurement_requested = pyqtSignal()

    def __init__(self, stencil_tracker, parent=None):
        """
        Inicializa o diálogo de rastreabilidade.

        Args:
            stencil_tracker: StencilTracker instance
            parent: Widget pai (MainWindow)
        """
        super().__init__(parent)

        self.stencil_tracker = stencil_tracker

        # Configurações do diálogo
        self.setWindowTitle("Rastreabilidade - Identificação de Stencil")
        self.setMinimumSize(500, 400)

        # Diálogo não-modal e sempre acima
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowStaysOnTopHint
        )
        # Não bloqueia a janela principal
        self.setModal(False)

        # Build UI
        self._build_ui()

        logger.debug("TrackingDialog criado")

    def _build_ui(self):
        """Constrói a interface do diálogo."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACE.MD, SPACE.MD, SPACE.MD, SPACE.MD)
        layout.setSpacing(SPACE.MD)

        # Import tardio para evitar import circular
        from consumo_lib.widgets.stencil import StencilIdentificationWidget

        # Widget de identificação de stencil
        self.stencil_identification = StencilIdentificationWidget(
            self.stencil_tracker,
            parent=self
        )

        # Conecta sinais internos para repassar
        self.stencil_identification.stencil_selected.connect(self.stencil_selected.emit)
        self.stencil_identification.stencil_cleared.connect(self.stencil_cleared.emit)
        self.stencil_identification.recipe_requested.connect(self.recipe_requested.emit)
        self.stencil_identification.measurement_requested.connect(self.measurement_requested.emit)

        layout.addWidget(self.stencil_identification)

    def closeEvent(self, a0):
        """
        Handler para fechamento do diálogo.

        Apenas aceita o evento, permitindo reabertura rápida.
        """
        if a0:
            a0.accept()
        logger.debug("TrackingDialog fechado")

    def showEvent(self, a0):
        """Handler para quando o diálogo é mostrado."""
        super().showEvent(a0)
        # Garante que está acima da janela principal
        if self.parent():
            self.raise_()
            self.activateWindow()

    def get_current_stencil(self):
        """
        Retorna stencil atualmente selecionado.

        Returns:
            Stencil ou None se não houver seleção
        """
        return self.stencil_identification.get_current_stencil()
