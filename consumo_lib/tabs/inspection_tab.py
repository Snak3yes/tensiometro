"""
tabs/inspection_tab.py
----------------------
Aba de inspeção visual de stencils.
"""

from __future__ import annotations

import logging
from PyQt6.QtWidgets import QVBoxLayout, QGroupBox, QHBoxLayout, QPushButton
from PyQt6.QtCore import pyqtSignal

from .base_tab import BaseTab
from consumo_lib.ui import COLORS
from consumo_lib.ui.widget_standards import StandardButton

logger = logging.getLogger(__name__)


class InspectionTab(BaseTab):
    """
    Aba de inspeção visual de stencils.

    Permite:
    - Configurar parâmetros de inspeção
    - Executar inspeção visual
    - Visualizar resultados
    """

    # Sinais específicos desta aba
    inspection_requested = pyqtSignal()
    settings_requested = pyqtSignal()

    def __init__(self, parent=None):
        """
        Inicializa a aba de inspeção.

        Args:
            parent: Widget pai (MainWindow)
        """
        super().__init__(parent)
        self.inspection_configured = False

    def build_ui(self):
        """Constrói a interface da aba."""
        # Placeholder para futura implementação
        info_group = QGroupBox("🔍 Inspeção Visual")
        info_layout = QVBoxLayout(info_group)

        info_text = (
            "Esta aba será implementada em fases futuras.\n\n"
            "Funcionalidades planejadas:\n"
            "• Configuração de parâmetros de inspeção\n"
            "• Carga de arquivo Gerber\n"
            "• Alinhamento fiducial\n"
            "• Execução de inspeção visual\n"
            "• Visualização de resultados\n"
            "• Geração de relatórios"
        )

        from PyQt6.QtWidgets import QLabel
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        info_label.setStyleSheet(f"color: {COLORS.TEXT_HINT}; padding: 20px;")
        info_layout.addWidget(info_label)

        # Botões placeholder
        btn_layout = QHBoxLayout()

        btn_settings = StandardButton("⚙️ Configurar Parâmetros")
        btn_settings.clicked.connect(self._on_settings)
        btn_layout.addWidget(btn_settings)

        btn_inspect = StandardButton("🔍 Executar Inspeção", variant="primary")
        btn_inspect.setEnabled(False)
        btn_inspect.clicked.connect(self._on_inspect)
        btn_layout.addWidget(btn_inspect)

        info_layout.addLayout(btn_layout)

        self.layout.addWidget(info_group)
        self.layout.addStretch()

    def _on_settings(self):
        """Handler para botão de configurações."""
        self.settings_requested.emit()
        self.show_status("Abrindo configurações de inspeção...")

    def _on_inspect(self):
        """Handler para botão de executar inspeção."""
        self.inspection_requested.emit()
        self.show_status("Iniciando inspeção visual...")

    def refresh(self):
        """Atualiza o estado da aba."""
        pass
