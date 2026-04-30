"""
dialogs/stencil/edit_dialog.py
------------------------------
Dialogo para editar informacoes de um stencil.
"""

import logging

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel,
    QLineEdit, QTextEdit, QComboBox, QHBoxLayout,
    QDialogButtonBox, QMessageBox, QWidget
)
from PyQt6.QtGui import QFont

from aoi_lib.stencil_tracker import StencilTracker, Stencil
from consumo_lib.dialogs.tension.select_pattern_dialog import SelectPatternDialog
from consumo_lib.managers.measurement_pattern_manager import MeasurementPatternManager
from consumo_lib.ui import TYPO
from consumo_lib.ui.widget_standards import StandardButton

log = logging.getLogger(__name__)


class StencilEditDialog(QDialog):
    """Dialogo para editar informacoes de um stencil."""

    def __init__(self, tracker: StencilTracker, stencil: Stencil, parent=None):
        super().__init__(parent)
        self.tracker = tracker
        self.stencil = stencil
        self.pattern_manager = MeasurementPatternManager()

        self.setWindowTitle(f"Editar Stencil - {stencil.code}")
        self.setMinimumWidth(460)

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.lbl_code = QLabel(self.stencil.code)
        self.lbl_code.setFont(QFont("Consolas", TYPO.BODY_MEDIUM))
        form.addRow("Leitura do código:", self.lbl_code)

        self.txt_model_name = QLineEdit(self.stencil.description)
        form.addRow("Nome do modelo:", self.txt_model_name)

        pattern_row = QWidget()
        pattern_layout = QHBoxLayout(pattern_row)
        pattern_layout.setContentsMargins(0, 0, 0, 0)

        self.txt_pattern = QLineEdit(self.stencil.recipe_name or "")
        self.txt_pattern.setReadOnly(True)
        self.txt_pattern.setPlaceholderText("Nenhum padrão selecionado")
        self.txt_pattern.setMinimumWidth(240)
        pattern_layout.addWidget(self.txt_pattern, 1)

        self.btn_select_pattern = StandardButton("Padrão de medição", variant="secondary")
        self.btn_select_pattern.clicked.connect(self._select_measurement_pattern)
        pattern_layout.addWidget(self.btn_select_pattern)

        form.addRow("Padrão de medição:", pattern_row)

        self.cmb_status = QComboBox()
        self.cmb_status.addItems(["active", "warning", "retired"])
        self.cmb_status.setCurrentText(self.stencil.status)
        form.addRow("Status:", self.cmb_status)

        self.txt_notes = QTextEdit()
        self.txt_notes.setPlainText(self.stencil.notes)
        self.txt_notes.setMaximumHeight(100)
        form.addRow("Observações:", self.txt_notes)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _save(self):
        """Salva alteracoes."""
        self.stencil.description = self.txt_model_name.text().strip()
        self.stencil.recipe_name = self.txt_pattern.text().strip() or None
        self.stencil.status = self.cmb_status.currentText()
        self.stencil.notes = self.txt_notes.toPlainText().strip()

        try:
            self.tracker.update_stencil(self.stencil)
            self._notify_stencil_changed(self.stencil.code)
            self.accept()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro ao Salvar",
                f"Erro: {str(e)}",
            )

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
