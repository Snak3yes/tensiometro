"""
tabs/tracking_tab.py
--------------------
Aba de rastreabilidade de stencils.
"""

from __future__ import annotations

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QHBoxLayout,
    QPushButton
)
from PyQt6.QtCore import pyqtSignal

from .base_tab import BaseTab

logger = logging.getLogger(__name__)


class TrackingTab(BaseTab):
    """
    Aba de rastreabilidade de stencils.

    Permite:
    - Seleção de stencil
    - Visualização de histórico
    - Ações rápidas (medição de tensão, gerenciamento)
    """

    # Sinais específicos desta aba
    stencil_selected = pyqtSignal(object)  # Stencil
    stencil_cleared = pyqtSignal()
    recipe_requested = pyqtSignal(str)  # recipe_name
    tension_measurement_requested = pyqtSignal()
    stencil_management_requested = pyqtSignal()
    new_stencil_requested = pyqtSignal()

    def __init__(self, stencil_tracker, parent=None):
        """
        Inicializa a aba de rastreabilidade.

        Args:
            stencil_tracker: StencilTracker
            parent: Widget pai (MainWindow)
        """
        self.stencil_tracker = stencil_tracker
        super().__init__(parent)

    def build_ui(self):
        """Constrói a interface da aba."""
        # Importa widgets
        from aoi_lib.stencil_tracker_ui import StencilIdentificationWidget

        # Widget de identificação de stencil
        self.stencil_identification = StencilIdentificationWidget(
            self.stencil_tracker,
            parent=self
        )

        # Conecta sinais
        self.stencil_identification.stencil_selected.connect(self._on_stencil_selected)
        self.stencil_identification.stencil_cleared.connect(self._on_stencil_cleared)
        self.stencil_identification.recipe_requested.connect(self._on_recipe_requested)

        self.layout.addWidget(self.stencil_identification)

        # Botões de ação rápida
        action_group = QGroupBox("⚡ Ações Rápidas")
        action_layout = QHBoxLayout(action_group)

        self.btn_run_tension = QPushButton("📐 Medir Tensão")
        self.btn_run_tension.setEnabled(False)
        self.btn_run_tension.setToolTip("Executa medição de tensão e salva no histórico do stencil")
        self.btn_run_tension.clicked.connect(self._on_run_tension)
        action_layout.addWidget(self.btn_run_tension)

        self.btn_manage_stencils = QPushButton("📋 Gerenciar Stencils")
        self.btn_manage_stencils.clicked.connect(self._on_manage_stencils)
        action_layout.addWidget(self.btn_manage_stencils)

        self.btn_new_stencil = QPushButton("➕ Novo Stencil")
        self.btn_new_stencil.clicked.connect(self._on_new_stencil)
        action_layout.addWidget(self.btn_new_stencil)

        self.layout.addWidget(action_group)

        # Espaço para futuras expansões
        self.layout.addStretch()

    def _on_stencil_selected(self, stencil):
        """
        Handler quando stencil é selecionado.

        Args:
            stencil: Stencil selecionado
        """
        # Habilita botão de medição de tensão
        self.btn_run_tension.setEnabled(True)
        # Repassa o sinal
        self.stencil_selected.emit(stencil)
        self.show_status(f"Stencil selecionado: {stencil.code}")

    def _on_stencil_cleared(self):
        """Handler quando seleção de stencil é limpa."""
        # Desabilita botão de medição de tensão
        self.btn_run_tension.setEnabled(False)
        # Repassa o sinal
        self.stencil_cleared.emit()
        self.show_status("Stencil desmarcado")

    def _on_recipe_requested(self, recipe_name: str):
        """
        Handler quando receita é solicitada.

        Args:
            recipe_name: Nome da receita
        """
        self.recipe_requested.emit(recipe_name)

    def _on_run_tension(self):
        """Handler para botão de medição de tensão."""
        self.tension_measurement_requested.emit()

    def _on_manage_stencils(self):
        """Handler para botão de gerenciar stencils."""
        self.stencil_management_requested.emit()

    def _on_new_stencil(self):
        """Handler para botão de novo stencil."""
        self.new_stencil_requested.emit()

    def refresh(self):
        """Atualiza a lista de stencils."""
        if hasattr(self.stencil_identification, 'refresh'):
            self.stencil_identification.refresh()
