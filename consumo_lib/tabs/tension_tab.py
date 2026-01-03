"""
tabs/tension_tab.py
-------------------
Aba de visualização de tensão do stencil.
"""

from __future__ import annotations

import logging
from PyQt6.QtWidgets import QVBoxLayout

from .base_tab import BaseTab

logger = logging.getLogger(__name__)


class TensionTab(BaseTab):
    """
    Aba de visualização de tensão.

    Exibe heatmap e gráficos de medição de tensão.
    """

    def __init__(self, parent=None):
        """
        Inicializa a aba de tensão.

        Args:
            parent: Widget pai (MainWindow)
        """
        super().__init__(parent)

    def build_ui(self):
        """Constrói a interface da aba."""
        # Importa widget de visualização
        from aoi_lib.stencil_tracker_ui import TensionVisualizationWidget

        # Cria o widget de visualização
        self.visualization = TensionVisualizationWidget()
        self.layout.addWidget(self.visualization)

    def load_tension_data(self, tension_data: dict):
        """
        Carrega dados de tensão para visualização.

        Args:
            tension_data: Dicionário com dados de medição de tensão
        """
        if hasattr(self.visualization, 'load_tension_data'):
            self.visualization.load_tension_data(tension_data)
            self.show_status("Dados de tensão carregados")

    def clear(self):
        """Limpa a visualização."""
        if hasattr(self.visualization, 'clear'):
            self.visualization.clear()
