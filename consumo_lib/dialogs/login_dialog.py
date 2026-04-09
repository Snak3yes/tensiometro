"""
Dialogo de login do sistema.
"""

import logging

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from aoi_lib.auth.auth_service import AuthService
from consumo_lib.ui import COLORS, TYPO
from consumo_lib.ui.widget_standards import StandardButton

logger = logging.getLogger(__name__)


class LoginDialog(QDialog):
    """
    Dialogo de login baseado em DRT.

    Modos:
    - Operador: valida o DRT no sistema interno da Digiboard
    - Eng/Admin: usa senha mestre e registra o DRT localmente
    """

    login_successful = pyqtSignal()

    def __init__(self, auth_service: AuthService, parent=None):
        super().__init__(parent)
        self.auth_service = auth_service
        self.setup_ui()

    def setup_ui(self):
        """Configura a interface do dialogo."""
        self.setWindowTitle("Tensiometro - Login")
        self.setModal(True)
        self.setMinimumSize(480, 420)
        self.resize(500, 430)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)

        screen = QGuiApplication.primaryScreen()
        if screen:
            available = screen.availableGeometry()
            self.move(
                available.center().x() - self.width() // 2,
                available.center().y() - self.height() // 2,
            )

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(32, 28, 32, 28)

        title_label = QLabel("TENSIOMETRO")
        title_label.setFont(TYPO.get_font(24, bold=True))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        subtitle_label = QLabel("Identificacao de usuario")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet(f"color: {COLORS.TEXT_HINT};")
        layout.addWidget(subtitle_label)

        layout.addSpacing(4)

        layout.addWidget(QLabel("DRT:"))
        self.drt_input = QLineEdit()
        self.drt_input.setPlaceholderText("Informe o DRT")
        self.drt_input.setMinimumHeight(40)
        layout.addWidget(self.drt_input)

        mode_title = QLabel("Modo:")
        mode_title.setStyleSheet("font-weight: 700;")
        layout.addWidget(mode_title)

        mode_row_widget = QWidget()
        mode_row_layout = QHBoxLayout(mode_row_widget)
        mode_row_layout.setContentsMargins(0, 0, 0, 0)
        mode_row_layout.setSpacing(8)

        self.eng_admin_checkbox = QCheckBox("Engenharia/ADMIN")
        self.eng_admin_checkbox.setStyleSheet(
            """
            QCheckBox {
                border: none;
                background: transparent;
                spacing: 8px;
                font-weight: 600;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #F28C28;
                border-radius: 3px;
                background: #FFFFFF;
            }
            QCheckBox::indicator:checked {
                background: #F28C28;
                border-color: #F28C28;
                image: none;
            }
            QCheckBox::indicator:unchecked:hover {
                border-color: #D97706;
            }
            """
        )
        self.eng_admin_checkbox.toggled.connect(self._on_mode_toggled)
        mode_row_layout.addWidget(self.eng_admin_checkbox)
        mode_row_layout.addStretch()
        layout.addWidget(mode_row_widget)

        helper_label = QLabel(
            "Desmarcado: valida o DRT no sistema interno.\n"
            "Marcado: libera o campo de senha para o modo Eng/Admin."
        )
        helper_label.setWordWrap(True)
        helper_label.setStyleSheet(f"color: {COLORS.TEXT_HINT}; font-size: 11px;")
        layout.addWidget(helper_label)

        layout.addWidget(QLabel("Senha:"))
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Senha habilitada apenas no modo Eng/Admin")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumHeight(40)
        layout.addWidget(self.password_input)

        self.mode_feedback_label = QLabel("Modo operador: apenas DRT.")
        self.mode_feedback_label.setStyleSheet(f"color: {COLORS.TEXT_HINT};")
        layout.addWidget(self.mode_feedback_label)

        buttons_layout = QHBoxLayout()

        self.login_button = StandardButton(
            "Entrar",
            variant="primary-green",
            semantic_size="dialog-primary",
        )
        self.login_button.clicked.connect(self.on_login_clicked)
        buttons_layout.addWidget(self.login_button)

        self.cancel_button = StandardButton(
            "Cancelar",
            variant="secondary",
            semantic_size="dialog-secondary",
        )
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)

        layout.addSpacing(4)
        layout.addLayout(buttons_layout)

        self.drt_input.returnPressed.connect(self.on_login_clicked)
        self.password_input.returnPressed.connect(self.on_login_clicked)

        self._on_mode_toggled(False)
        self.drt_input.setFocus()

    def _on_mode_toggled(self, checked: bool):
        """Atualiza a tela conforme o modo selecionado."""
        self.password_input.setEnabled(checked)
        if checked:
            self.password_input.setPlaceholderText("Informe a senha de Eng/Admin")
            self.mode_feedback_label.setText("Modo Eng/Admin: DRT local + senha mestre.")
        else:
            self.password_input.clear()
            self.password_input.setPlaceholderText("Senha habilitada apenas no modo Eng/Admin")
            self.mode_feedback_label.setText("Modo operador: apenas DRT.")

    def on_login_clicked(self):
        """Processa o login conforme o modo selecionado."""
        drt = self.drt_input.text().strip()
        eng_admin_mode = self.eng_admin_checkbox.isChecked()
        password = self.password_input.text()

        if not drt:
            QMessageBox.warning(self, "Campo vazio", "Informe o DRT.")
            self.drt_input.setFocus()
            return

        if eng_admin_mode and not password:
            QMessageBox.warning(self, "Campo vazio", "Informe a senha de Eng/Admin.")
            self.password_input.setFocus()
            return

        self.setCursor(Qt.CursorShape.WaitCursor)
        self.login_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        try:
            if eng_admin_mode:
                success = self.auth_service.authenticate_eng_admin(drt, password)
            else:
                success = self.auth_service.authenticate_operator(drt)
        finally:
            self.unsetCursor()
            self.login_button.setEnabled(True)
            self.cancel_button.setEnabled(True)

        if success:
            logger.info(
                "Login realizado com sucesso: DRT=%s modo=%s",
                drt,
                self.auth_service.get_current_mode(),
            )
            self.login_successful.emit()
            self.accept()
            return

        error_message = self.auth_service.get_last_error() or "Falha ao autenticar."
        logger.warning("Falha no login: DRT=%s erro=%s", drt, error_message)
        QMessageBox.critical(self, "Erro de autenticacao", error_message)

        if eng_admin_mode:
            self.password_input.clear()
            self.password_input.setFocus()
        else:
            self.drt_input.selectAll()
            self.drt_input.setFocus()

    def show_error(self, message: str):
        """Exibe erro generico."""
        QMessageBox.critical(self, "Erro", message)
