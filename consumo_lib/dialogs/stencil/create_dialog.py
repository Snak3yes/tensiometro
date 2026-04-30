"""
dialogs/stencil/create_dialog.py
--------------------------------
Dialogo para cadastrar novo stencil.
"""

import logging
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QDialogButtonBox, QMessageBox, QWidget
)
from PyQt6.QtGui import QFont

from aoi_lib.stencil_tracker import StencilTracker, Stencil, normalize_stencil_code
from consumo_lib.dialogs.tension.select_pattern_dialog import SelectPatternDialog
from consumo_lib.managers.measurement_pattern_manager import MeasurementPatternManager
from consumo_lib.ui import COLORS, TYPO, SPACE
from consumo_lib.ui.widget_standards import StandardButton

log = logging.getLogger(__name__)


class StencilCreateDialog(QDialog):
    """Dialogo para cadastrar novo stencil."""

    def __init__(
        self,
        tracker: StencilTracker,
        initial_code: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self.tracker = tracker
        self.created_stencil: Optional[Stencil] = None
        self.pattern_manager = MeasurementPatternManager()

        self.setWindowTitle("Cadastrar Novo Stencil")
        self.setMinimumWidth(460)

        self._setup_ui()

        if initial_code:
            self.txt_code.setText(normalize_stencil_code(initial_code))

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        info = QLabel(
            "Cadastre um novo stencil.\n"
            "O codigo e o identificador unico lido pelo codigo de barras."
        )
        info.setWordWrap(True)
        info.setStyleSheet(f"color: {COLORS.TEXT_HINT}; margin-bottom: {SPACE.SM}px;")
        layout.addWidget(info)

        form = QFormLayout()

        self.txt_model_name = QLineEdit()
        self.txt_model_name.setPlaceholderText("Nome do modelo")
        form.addRow("Nome do modelo:", self.txt_model_name)

        pattern_row = QWidget()
        pattern_layout = QHBoxLayout(pattern_row)
        pattern_layout.setContentsMargins(0, 0, 0, 0)

        self.txt_pattern = QLineEdit()
        self.txt_pattern.setReadOnly(True)
        self.txt_pattern.setPlaceholderText("Nenhum padrão selecionado")
        self.txt_pattern.setMinimumWidth(240)
        pattern_layout.addWidget(self.txt_pattern, 1)

        self.btn_select_pattern = StandardButton("Padrão de medição", variant="secondary")
        self.btn_select_pattern.clicked.connect(self._select_measurement_pattern)
        pattern_layout.addWidget(self.btn_select_pattern)

        form.addRow("Padrão de medição:", pattern_row)

        self.txt_code = QLineEdit()
        self.txt_code.setFont(QFont("Consolas", TYPO.BODY_MEDIUM))
        self.txt_code.setPlaceholderText("Leitura do código de barras")
        self.txt_code.textEdited.connect(self._normalize_code_input)
        form.addRow("Leitura do código*:", self.txt_code)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._create)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _create(self):
        """Cria o stencil."""
        code = normalize_stencil_code(self.txt_code.text())
        self.txt_code.setText(code)

        if not code:
            QMessageBox.warning(
                self,
                "Código Obrigatório",
                "Digite ou leia o código do stencil.",
            )
            self.txt_code.setFocus()
            return

        if self.tracker.stencil_exists(code):
            QMessageBox.warning(
                self,
                "Código Já Existe",
                f"O código '{code}' já está cadastrado.",
            )
            return

        try:
            self.created_stencil = self.tracker.create_stencil(
                code=code,
                description=self.txt_model_name.text().strip(),
                recipe_name=self.txt_pattern.text().strip() or None,
            )
            self._notify_stencil_changed(self.created_stencil.code)
            self.accept()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro ao Cadastrar",
                f"Erro: {str(e)}",
            )

    def get_created_stencil(self) -> Optional[Stencil]:
        return self.created_stencil

    def _normalize_code_input(self, text: str):
        """Mantem o codigo de stencil em maiusculas durante o cadastro."""
        normalized = normalize_stencil_code(text)
        if text == normalized:
            return

        cursor_position = self.txt_code.cursorPosition()
        self.txt_code.blockSignals(True)
        self.txt_code.setText(normalized)
        self.txt_code.setCursorPosition(min(cursor_position, len(normalized)))
        self.txt_code.blockSignals(False)

    def _select_measurement_pattern(self):
        """Abre a tela de selecao de padrao de medicao."""
        dialog = SelectPatternDialog(self.pattern_manager, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            pattern_name = dialog.get_selected_pattern()
            if pattern_name:
                self.txt_pattern.setText(pattern_name)

    def _notify_stencil_changed(self, stencil_code: str):
        """Notifica o wrapper principal para atualizar a UI em tempo real."""
        widget = self.parentWidget()
        while widget is not None:
            wrapper = getattr(widget, "stencil_manager_wrapper", None)
            if wrapper is not None and hasattr(wrapper, "stencil_changed"):
                wrapper.stencil_changed.emit(stencil_code)
                return
            widget = widget.parentWidget()
