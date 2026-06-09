"""
Dialog for editing the external tension API endpoint.
"""

from __future__ import annotations

from urllib.parse import urlparse

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)


class IntegrationEndpointDialog(QDialog):
    """Small admin-only dialog for the tension integration endpoint URL."""

    def __init__(self, endpoint_url: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Endpoint da API de Tensao")
        self.setModal(True)
        self.setMinimumWidth(560)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        title = QLabel("Endpoint da API de Tensao")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        description = QLabel(
            "Altere somente a URL usada para enviar os resultados de tensao "
            "aprovados e reprovados para o servidor."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        form = QFormLayout()
        form.setSpacing(10)

        self.endpoint_input = QLineEdit()
        self.endpoint_input.setPlaceholderText(
            "http://servidor:porta/sfcs-print/stencil/stencil_tensiometro"
        )
        self.endpoint_input.setText(endpoint_url or "")
        self.endpoint_input.selectAll()
        form.addRow("URL:", self.endpoint_input)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Salvar")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def endpoint_url(self) -> str:
        """Return the normalized endpoint URL entered by the user."""
        return self.endpoint_input.text().strip()

    def accept(self) -> None:
        endpoint_url = self.endpoint_url()
        if not self.is_valid_endpoint_url(endpoint_url):
            QMessageBox.warning(
                self,
                "URL invalida",
                "Informe uma URL HTTP ou HTTPS valida para a API.",
            )
            self.endpoint_input.setFocus()
            return

        super().accept()

    @staticmethod
    def is_valid_endpoint_url(endpoint_url: str) -> bool:
        parsed = urlparse((endpoint_url or "").strip())
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
