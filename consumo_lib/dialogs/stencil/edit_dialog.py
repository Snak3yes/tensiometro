"""
dialogs/stencil/edit_dialog.py
-------------------------------
Diálogo para editar informações de um stencil.
"""

import logging

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout,
    QLineEdit, QTextEdit, QComboBox, QPushButton,
    QDialogButtonBox, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from aoi_lib.stencil_tracker import StencilTracker, Stencil
from consumo_lib.ui import TYPO

log = logging.getLogger(__name__)


class StencilEditDialog(QDialog):
    """Diálogo para editar informações de um stencil."""

    def __init__(self, tracker: StencilTracker, stencil: Stencil, parent=None):
        super().__init__(parent)
        self.tracker = tracker
        self.stencil = stencil

        self.setWindowTitle(f"Editar Stencil - {stencil.code}")
        self.setMinimumWidth(400)

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()

        # Código (somente leitura)
        self.lbl_code = QLabel(self.stencil.code)
        self.lbl_code.setFont(TYPO.get_font(TYPO.BODY_MEDIUM, family="Consolas"))
        form.addRow("Código:", self.lbl_code)

        # Descrição
        self.txt_description = QLineEdit(self.stencil.description)
        form.addRow("Descrição:", self.txt_description)

        # Receita
        self.txt_recipe = QLineEdit(self.stencil.recipe_name or "")
        self.txt_recipe.setPlaceholderText("Nome da receita associada")
        form.addRow("Receita:", self.txt_recipe)

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
        self.stencil.recipe_name = self.txt_recipe.text().strip() or None
        self.stencil.status = self.cmb_status.currentText()
        self.stencil.notes = self.txt_notes.toPlainText().strip()

        try:
            self.tracker.update_stencil(self.stencil)
            self.accept()
        except Exception as e:
            QMessageBox.critical(
                self, "Erro ao Salvar",
                f"Erro: {str(e)}"
            )
