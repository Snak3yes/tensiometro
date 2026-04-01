"""
dialogs/stencil/edit_dialog.py
-------------------------------
Diálogo para editar informações de um stencil.
"""

import logging

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel,
    QLineEdit, QTextEdit, QComboBox, QHBoxLayout,
    QDialogButtonBox, QMessageBox, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from aoi_lib.recipe_manager import RecipeManager
from aoi_lib.stencil_tracker import StencilTracker, Stencil
from consumo_lib.dialogs.recipe.recipe_edit_dialog import RecipeEditorDialog
from consumo_lib.ui import TYPO
from consumo_lib.ui.widget_standards import StandardButton

log = logging.getLogger(__name__)


class StencilEditDialog(QDialog):
    """Diálogo para editar informações de um stencil."""

    def __init__(self, tracker: StencilTracker, stencil: Stencil, parent=None):
        super().__init__(parent)
        self.tracker = tracker
        self.stencil = stencil
        self.recipe_manager = RecipeManager()

        self.setWindowTitle(f"Editar Stencil - {stencil.code}")
        self.setMinimumWidth(400)

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()

        # Código (somente leitura)
        self.lbl_code = QLabel(self.stencil.code)
        self.lbl_code.setFont(QFont("Consolas", TYPO.BODY_MEDIUM))
        form.addRow("Código:", self.lbl_code)

        # Descrição
        self.txt_description = QLineEdit(self.stencil.description)
        form.addRow("Descrição:", self.txt_description)

        # Receita
        recipe_row = QWidget()
        recipe_layout = QHBoxLayout(recipe_row)
        recipe_layout.setContentsMargins(0, 0, 0, 0)

        self.cmb_recipe = QComboBox()
        self.cmb_recipe.setEditable(True)
        self.cmb_recipe.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.cmb_recipe.setMinimumWidth(220)
        recipe_layout.addWidget(self.cmb_recipe, 1)

        self.btn_new_recipe = StandardButton("Nova Receita", variant="secondary")
        self.btn_new_recipe.clicked.connect(self._create_recipe)
        recipe_layout.addWidget(self.btn_new_recipe)

        self.btn_edit_recipe = StandardButton("Editar Receita", variant="secondary")
        self.btn_edit_recipe.clicked.connect(self._edit_recipe)
        recipe_layout.addWidget(self.btn_edit_recipe)

        form.addRow("Receita:", recipe_row)
        self._refresh_recipe_options(self.stencil.recipe_name or "")

        # Status
        self.cmb_status = QComboBox()
        self.cmb_status.addItems(["active", "warning", "retired"])
        self.cmb_status.setCurrentText(self.stencil.status)
        form.addRow("Status:", self.cmb_status)

        # Notas
        self.txt_notes = QTextEdit()
        self.txt_notes.setPlainText(self.stencil.notes)
        self.txt_notes.setMaximumHeight(100)
        form.addRow("Observações:", self.txt_notes)

        layout.addLayout(form)

        # Botões
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _save(self):
        """Salva alterações."""
        self.stencil.description = self.txt_description.text().strip()
        self.stencil.recipe_name = self.cmb_recipe.currentText().strip() or None
        self.stencil.status = self.cmb_status.currentText()
        self.stencil.notes = self.txt_notes.toPlainText().strip()

        try:
            self.tracker.update_stencil(self.stencil)
            self._notify_stencil_changed(self.stencil.code)
            self.accept()
        except Exception as e:
            QMessageBox.critical(
                self, "Erro ao Salvar",
                f"Erro: {str(e)}"
            )

    def _notify_stencil_changed(self, stencil_code: str):
        """Notifica o wrapper principal para atualizar a UI em tempo real."""
        widget = self.parentWidget()
        while widget is not None:
            wrapper = getattr(widget, "stencil_manager_wrapper", None)
            if wrapper is not None and hasattr(wrapper, "stencil_changed"):
                wrapper.stencil_changed.emit(stencil_code)
                return
            widget = widget.parentWidget()

    def _refresh_recipe_options(self, selected_name: str = ""):
        """Atualiza combo de receitas disponíveis."""
        current_text = selected_name or self.cmb_recipe.currentText().strip()
        self.cmb_recipe.clear()
        self.cmb_recipe.addItem("", "")
        for recipe in self.recipe_manager.list_recipes():
            name = recipe.get("name", "")
            if name:
                self.cmb_recipe.addItem(name, recipe.get("recipe_id"))

        if current_text:
            index = self.cmb_recipe.findText(current_text)
            if index >= 0:
                self.cmb_recipe.setCurrentIndex(index)
            else:
                self.cmb_recipe.setEditText(current_text)

    def _create_recipe(self):
        """Cria nova receita a partir do fluxo de edição do stencil."""
        dialog = RecipeEditorDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            recipe = dialog.recipe
            if self.recipe_manager.save_recipe(recipe):
                self._refresh_recipe_options(recipe.name)
            else:
                QMessageBox.warning(self, "Receita", f"Não foi possível salvar a receita '{recipe.name}'.")

    def _edit_recipe(self):
        """Edita a receita selecionada no stencil."""
        selected = self.cmb_recipe.currentData() or self.cmb_recipe.currentText().strip()
        if not selected:
            QMessageBox.warning(self, "Receita", "Selecione uma receita para editar.")
            return

        recipe = self.recipe_manager.load_recipe(selected)
        if recipe is None:
            QMessageBox.warning(self, "Receita", "Não foi possível carregar a receita selecionada.")
            return

        dialog = RecipeEditorDialog(recipe, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated = dialog.recipe
            if self.recipe_manager.save_recipe(updated):
                self._refresh_recipe_options(updated.name)
            else:
                QMessageBox.warning(self, "Receita", f"Não foi possível salvar a receita '{updated.name}'.")
