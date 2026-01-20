"""
tabs/map_tab.py
---------------
Aba de programação de mapa de imagens.
"""

from __future__ import annotations

import logging
from PyQt6.QtWidgets import QVBoxLayout, QGroupBox, QHBoxLayout, QPushButton
from PyQt6.QtCore import pyqtSignal

from .base_tab import BaseTab
from consumo_lib.ui import COLORS
from consumo_lib.ui.widget_standards import StandardButton

logger = logging.getLogger(__name__)


class MapTab(BaseTab):
    """
    Aba de programação de mapa.

    Permite:
    - Definir áreas de captura
    - Programar grid de imagens
    - Gerar mapas para mosaicagem
    """

    # Sinais específicos desta aba
    map_definition_requested = pyqtSignal()
    mosaic_builder_requested = pyqtSignal()

    def __init__(self, parent=None):
        """
        Inicializa a aba de mapa.

        Args:
            parent: Widget pai (MainWindow)
        """
        super().__init__(parent)

    def build_ui(self):
        """Constrói a interface da aba."""
        # Placeholder para futura implementação
        info_group = QGroupBox("🗺️ Programação de Mapa")
        info_layout = QVBoxLayout(info_group)

        info_text = (
            "Esta aba será implementada em fases futuras.\n\n"
            "Funcionalidades planejadas:\n"
            "• Definir cantos da área de captura\n"
            "• Configurar grid de imagens\n"
            "• Gerar programa de mapa\n"
            "• Salvar/carregar programas\n"
            "• Integrar com Mosaic Builder"
        )

        from PyQt6.QtWidgets import QLabel
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        info_label.setStyleSheet(f"color: {COLORS.TEXT_HINT}; padding: 20px;")
        info_layout.addWidget(info_label)

        # Botões de ação
        btn_layout = QHBoxLayout()

        btn_define = StandardButton("📐 Definir Mapa")
        btn_define.setToolTip("Abre diálogo para definir cantos e gerar programa de mapa")
        btn_define.clicked.connect(self._on_define_map)
        btn_layout.addWidget(btn_define)

        btn_mosaic = StandardButton("🖼️ Montar Mosaico")
        btn_mosaic.setToolTip("Abre o Mosaic Builder para montar imagens capturadas")
        btn_mosaic.clicked.connect(self._on_mosaic_builder)
        btn_layout.addWidget(btn_mosaic)

        info_layout.addLayout(btn_layout)

        self.layout.addWidget(info_group)
        self.layout.addStretch()

    def _on_define_map(self):
        """Handler para botão de definir mapa."""
        self.map_definition_requested.emit()
        self.show_status("Abrindo definição de mapa...")

    def _on_mosaic_builder(self):
        """Handler para botão de montar mosaico."""
        self.mosaic_builder_requested.emit()
        self.show_status("Abrindo Mosaic Builder...")

    def refresh(self):
        """Atualiza o estado da aba."""
        pass
