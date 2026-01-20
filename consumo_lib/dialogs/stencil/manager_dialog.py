"""
dialogs/stencil/manager_dialog.py
---------------------------------
Diálogo para gerenciamento de stencils cadastrados.
"""

import logging
from datetime import datetime
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from aoi_lib.stencil_tracker import StencilTracker
from consumo_lib.ui import COLORS

log = logging.getLogger(__name__)


class StencilManagerDialog(QDialog):
    """
    Diálogo para gerenciamento de stencils cadastrados.

    Permite:
    - Listar todos os stencils
    - Criar novos
    - Editar existentes
    - Filtrar por status
    """

    def __init__(self, tracker: StencilTracker, parent=None):
        super().__init__(parent)
        self.tracker = tracker

        self.setWindowTitle("Gerenciar Stencils")
        self.setMinimumSize(800, 500)

        self._setup_ui()
        self._load_stencils()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # ================== FILTROS ==================
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel("Filtrar por status:"))

        self.cmb_filter = QComboBox()
        self.cmb_filter.addItems(["Todos", "Ativos", "Alerta", "Retirados"])
        self.cmb_filter.currentIndexChanged.connect(self._load_stencils)
        filter_layout.addWidget(self.cmb_filter)

        filter_layout.addStretch()

        self.btn_new = QPushButton("➕ Novo Stencil")
        self.btn_new.clicked.connect(self._create_new)
        filter_layout.addWidget(self.btn_new)

        self.btn_refresh = QPushButton("🔄 Atualizar")
        self.btn_refresh.clicked.connect(self._load_stencils)
        filter_layout.addWidget(self.btn_refresh)

        layout.addLayout(filter_layout)

        # ================== TABELA ==================
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Código", "Descrição", "Receita", "Última Inspeção", "Inspeções", "Status"
        ])
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self._edit_selected)

        layout.addWidget(self.table, 1)

        # ================== BOTÕES ==================
        btn_layout = QHBoxLayout()

        self.btn_edit = QPushButton("✏️ Editar")
        self.btn_edit.clicked.connect(self._edit_selected)
        btn_layout.addWidget(self.btn_edit)

        self.btn_history = QPushButton("📊 Histórico")
        self.btn_history.clicked.connect(self._show_history)
        btn_layout.addWidget(self.btn_history)

        self.btn_delete = QPushButton("🗑️ Excluir")
        self.btn_delete.clicked.connect(self._delete_selected)
        self.btn_delete.setStyleSheet(f"color: {COLORS.ERROR};")
        btn_layout.addWidget(self.btn_delete)

        btn_layout.addStretch()

        btn_close = QPushButton("Fechar")
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)

        layout.addLayout(btn_layout)

    def _load_stencils(self):
        """Carrega lista de stencils."""
        filter_map = {
            0: None,  # Todos
            1: "active",
            2: "warning",
            3: "retired",
        }
        status_filter = filter_map.get(self.cmb_filter.currentIndex())

        stencils = self.tracker.list_stencils(status=status_filter)

        self.table.setRowCount(len(stencils))

        status_display = {
            "active": ("🟢 Ativo", COLORS.SUCCESS),
            "warning": ("🟡 Alerta", COLORS.WARNING),
            "retired": ("🔴 Retirado", COLORS.ERROR),
        }

        for row, stencil in enumerate(stencils):
            self.table.setItem(row, 0, QTableWidgetItem(stencil.code))
            self.table.setItem(row, 1, QTableWidgetItem(stencil.description))
            self.table.setItem(row, 2, QTableWidgetItem(stencil.recipe_name or ""))

            # Última inspeção
            if stencil.last_inspection:
                try:
                    dt = datetime.fromisoformat(stencil.last_inspection)
                    dt_str = dt.strftime("%d/%m/%Y %H:%M")
                except:
                    dt_str = stencil.last_inspection
            else:
                dt_str = "-"
            self.table.setItem(row, 3, QTableWidgetItem(dt_str))

            self.table.setItem(row, 4, QTableWidgetItem(str(stencil.inspection_count)))

            # Status com cor
            status_text, status_color = status_display.get(
                stencil.status, ("?", COLORS.SURFACE)
            )
            status_item = QTableWidgetItem(status_text)
            status_item.setBackground(COLORS.to_qcolor(status_color))
            self.table.setItem(row, 5, status_item)

    def _get_selected_code(self) -> Optional[str]:
        """Retorna código do stencil selecionado."""
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        return item.text() if item else None

    def _create_new(self):
        """Abre diálogo para criar novo stencil."""
        from consumo_lib.dialogs.stencil import StencilCreateDialog

        dialog = StencilCreateDialog(self.tracker, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._load_stencils()

    def _edit_selected(self):
        """Edita stencil selecionado."""
        code = self._get_selected_code()
        if not code:
            QMessageBox.warning(self, "Seleção", "Selecione um stencil.")
            return

        stencil = self.tracker.get_stencil(code)
        if stencil:
            from consumo_lib.dialogs.stencil import StencilEditDialog

            dialog = StencilEditDialog(self.tracker, stencil, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self._load_stencils()

    def _show_history(self):
        """Mostra histórico do stencil selecionado."""
        code = self._get_selected_code()
        if not code:
            QMessageBox.warning(self, "Seleção", "Selecione um stencil.")
            return

        from consumo_lib.dialogs.stencil import StencilHistoryDialog

        dialog = StencilHistoryDialog(self.tracker, code, self)
        dialog.exec()

    def _delete_selected(self):
        """Exclui stencil selecionado."""
        code = self._get_selected_code()
        if not code:
            QMessageBox.warning(self, "Seleção", "Selecione um stencil.")
            return

        reply = QMessageBox.question(
            self, "Confirmar Exclusão",
            f"Tem certeza que deseja excluir o stencil '{code}'?\n\n"
            "⚠️ Esta ação é irreversível e removerá todo o histórico!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.tracker.delete_stencil(code):
                self._load_stencils()
            else:
                QMessageBox.critical(
                    self, "Erro",
                    "Não foi possível excluir o stencil."
                )
