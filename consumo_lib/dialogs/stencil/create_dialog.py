"""
dialogs/stencil/create_dialog.py
--------------------------------
Diálogo para cadastrar novo stencil.
"""

import logging
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QDialogButtonBox, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from aoi_lib.stencil_tracker import StencilTracker, Stencil

log = logging.getLogger(__name__)


class StencilCreateDialog(QDialog):
    """Diálogo para cadastrar novo stencil."""

    def __init__(self, tracker: StencilTracker,
                 initial_code: str = "",
                 parent=None):
        super().__init__(parent)
        self.tracker = tracker
        self.created_stencil: Optional[Stencil] = None

        self.setWindowTitle("Cadastrar Novo Stencil")
        self.setMinimumWidth(400)

        self._setup_ui()

        if initial_code:
            self.txt_code.setText(initial_code)

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        info = QLabel(
            "ℹ️ Cadastre um novo programa de stencil.\n"
            "O código é o identificador único (código de barras)."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(info)

        form = QFormLayout()

        # Código (obrigatório)
        self.txt_code = QLineEdit()
        self.txt_code.setFont(QFont("Consolas", 11))
        self.txt_code.setPlaceholderText("Código de barras (obrigatório)")
        form.addRow("Código*:", self.txt_code)

        # Descrição
        self.txt_description = QLineEdit()
        self.txt_description.setPlaceholderText("Descrição auxiliar")
        form.addRow("Descrição:", self.txt_description)

        # Receita
        self.txt_recipe = QLineEdit()
        self.txt_recipe.setPlaceholderText("Nome exato da receita")
        form.addRow("Receita:", self.txt_recipe)

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
                recipe_name=self.txt_recipe.text().strip() or None,
            )
            self.accept()

        except Exception as e:
            QMessageBox.critical(
                self, "Erro ao Cadastrar",
                f"Erro: {str(e)}"
            )

    def get_created_stencil(self) -> Optional[Stencil]:
        return self.created_stencil
