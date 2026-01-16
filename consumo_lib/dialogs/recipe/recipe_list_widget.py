# -*- coding: utf-8 -*-
"""
recipe_list_widget.py
----------------------
Widget para listar e selecionar receitas.

Responsabilidade: Exibir lista de receitas em tabela e emitir sinais
de seleção para componentes pais.

Autor: Sistema AOI Tensiometro
Data: 2026-01-16 (Refatorado de recipe_dialogs.py)
"""

import logging
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView
)
from PyQt6.QtCore import pyqtSignal
from aoi_lib.recipe_manager import RecipeManager

logger = logging.getLogger(__name__)


class RecipeListWidget(QWidget):
    """
    Widget para listar e selecionar receitas.

    Responsabilidade:
    - Exibir tabela de receitas (Nome, ID, Modificado)
    - Emitir sinais quando receita é selecionada ou clicada
    - Gerenciar estado de seleção da tabela

    Signals:
    - recipe_selected(str): Emitido quando seleção muda (recipe_id)
    - recipe_double_clicked(str): Emitido com duplo clique (recipe_id)
    """

    recipe_selected = pyqtSignal(str)  # Emite recipe_id
    recipe_double_clicked = pyqtSignal(str)  # Emite recipe_id

    def __init__(self, recipe_manager: RecipeManager, parent=None):
        """
        Inicializa widget de lista de receitas.

        Args:
            recipe_manager: Instância de RecipeManager para listar receitas
            parent: Widget pai (opcional)
        """
        super().__init__(parent)
        self.manager = recipe_manager
        self.setup_ui()
        self.refresh_list()

    def setup_ui(self):
        """Configura interface do widget."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Tabela de receitas
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Nome", "ID", "Modificado"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.table.itemDoubleClicked.connect(self._on_double_click)

        layout.addWidget(self.table)

    def refresh_list(self):
        """
        Atualiza a lista de receitas na tabela.

        Lê todas as receitas do RecipeManager e popula a tabela.
        Formata data de modificação para mostrar apenas YYYY-MM-DD.
        """
        self.table.setRowCount(0)
        recipes = self.manager.list_recipes()

        for i, r in enumerate(recipes):
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(r['name']))
            self.table.setItem(i, 1, QTableWidgetItem(r['recipe_id']))

            # Formata data
            modified = r.get('modified_at', '')
            if modified:
                try:
                    modified = modified[:10]  # Apenas data
                except:
                    pass
            self.table.setItem(i, 2, QTableWidgetItem(modified))

    def _on_selection_changed(self):
        """
        Handler chamado quando seleção da tabela muda.

        Emite signal recipe_selected com o recipe_id da linha selecionada.
        """
        items = self.table.selectedItems()
        if items:
            row = items[0].row()
            recipe_id = self.table.item(row, 1).text()
            self.recipe_selected.emit(recipe_id)

    def _on_double_click(self, item):
        """
        Handler chamado quando há duplo clique em item da tabela.

        Emite signal recipe_double_clicked com o recipe_id da linha clicada.

        Args:
            item: QTableWidgetItem clicado
        """
        row = item.row()
        recipe_id = self.table.item(row, 1).text()
        self.recipe_double_clicked.emit(recipe_id)

    def get_selected_recipe_id(self) -> Optional[str]:
        """
        Retorna o ID da receita selecionada.

        Returns:
            recipe_id se houver seleção, None caso contrário
        """
        items = self.table.selectedItems()
        if items:
            row = items[0].row()
            return self.table.item(row, 1).text()
        return None
