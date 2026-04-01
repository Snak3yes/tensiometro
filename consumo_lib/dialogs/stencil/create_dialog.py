"""
dialogs/stencil/create_dialog.py
--------------------------------
Diálogo para cadastrar novo stencil.
"""

import logging
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QDialogButtonBox, QMessageBox, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from aoi_lib.recipe_manager import RecipeManager
from aoi_lib.stencil_tracker import StencilTracker, Stencil
from consumo_lib.dialogs.recipe.recipe_edit_dialog import RecipeEditorDialog
from consumo_lib.ui import COLORS, TYPO, SPACE
from consumo_lib.ui.widget_standards import StandardButton

log = logging.getLogger(__name__)


class StencilCreateDialog(QDialog):
    """Diálogo para cadastrar novo stencil."""

    def __init__(self, tracker: StencilTracker,
                 initial_code: str = "",
                 parent=None):
        super().__init__(parent)
        self.tracker = tracker
        self.created_stencil: Optional[Stencil] = None
        self.recipe_manager = RecipeManager()

        self.setWindowTitle("Cadastrar Novo Stencil")
        self.setMinimumWidth(400)

        self._setup_ui()

        if initial_code:
            self.txt_code.setText(initial_code)

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        info = QLabel(
            "ℹ️ Cadastre um novo stencil.\n"
            "O código é o identificador único (código de barras)."
        )
        info.setWordWrap(True)
        info.setStyleSheet(f"color: {COLORS.TEXT_HINT}; margin-bottom: {SPACE.SM}px;")
        layout.addWidget(info)

        form = QFormLayout()

        # Código (obrigatório)
        self.txt_code = QLineEdit()
        # Fonte monospace para código
        font = QFont("Consolas", TYPO.BODY_MEDIUM)
        self.txt_code.setFont(font)
        self.txt_code.setPlaceholderText("Código de barras (obrigatório)")
        form.addRow("Código*:", self.txt_code)

        # Descrição
        self.txt_description = QLineEdit()
        self.txt_description.setPlaceholderText("Descrição auxiliar")
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
        self._refresh_recipe_options()

        layout.addLayout(form)

        # Botões
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._create)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _create(self):
        """Cria o stencil."""
        code = self.txt_code.text().strip()

        if not code:
            QMessageBox.warning(
                self, "Código Obrigatório",
                "Digite o código do stencil."
            )
            self.txt_code.setFocus()
            return

        if self.tracker.stencil_exists(code):
            QMessageBox.warning(
                self, "Código Já Existe",
                f"O código '{code}' já está cadastrado."
            )
            return

        try:
            self.created_stencil = self.tracker.create_stencil(
                code=code,
                description=self.txt_description.text().strip(),
                recipe_name=self.cmb_recipe.currentText().strip() or None,
            )
            self._notify_stencil_changed(self.created_stencil.code)
            self.accept()

        except Exception as e:
            QMessageBox.critical(
                self, "Erro ao Cadastrar",
                f"Erro: {str(e)}"
            )

    def get_created_stencil(self) -> Optional[Stencil]:
        return self.created_stencil

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
        """Cria nova receita a partir do fluxo de cadastro do stencil."""
        dialog = RecipeEditorDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            recipe = dialog.recipe
            if self.recipe_manager.save_recipe(recipe):
                self._refresh_recipe_options(recipe.name)
            else:
                QMessageBox.warning(self, "Receita", f"Não foi possível salvar a receita '{recipe.name}'.")

    def _edit_recipe(self):
        """Edita a receita selecionada no cadastro do stencil."""
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
