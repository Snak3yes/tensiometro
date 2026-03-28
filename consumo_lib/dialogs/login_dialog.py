"""
Dialog de Login do Sistema

Implementa interface de autenticação com validação de campos.
"""

import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from aoi_lib.auth.auth_service import AuthService
from consumo_lib.ui import COLORS, TYPO
from consumo_lib.ui.widget_standards import StandardButton

logger = logging.getLogger(__name__)


class LoginDialog(QDialog):
    """
    Dialog de login do sistema Tensiômetro

    Sinais:
        login_successful: Emitido quando login é bem-sucedido
    """

    login_successful = pyqtSignal()

    def __init__(self, auth_service: AuthService, parent=None):
        """
        Inicializa dialog de login

        Args:
            auth_service: Instância do serviço de autenticação
            parent: Widget pai
        """
        super().__init__(parent)
        self.auth_service = auth_service
        self.setup_ui()

    def setup_ui(self):
        """Configura interface do dialog"""
        self.setWindowTitle("TENSIO METRO - Login")
        self.setModal(True)
        self.setFixedSize(450, 480)  # Aumentado de 350 para 480 para não cortar conteúdo

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        # Logo/Título
        title_label = QLabel("TENSIO METRO")
        title_label.setFont(TYPO.get_font(24, bold=True))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        subtitle_label = QLabel("Sistema de Tensão e Rastreabilidade")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label)

        layout.addSpacing(20)

        # Campo de usuário
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Usuário")
        self.username_input.setMinimumHeight(40)
        layout.addWidget(QLabel("Usuário:"))
        layout.addWidget(self.username_input)

        # Campo de senha
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Senha")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumHeight(40)
        layout.addWidget(QLabel("Senha:"))
        layout.addWidget(self.password_input)

        layout.addSpacing(10)

        # Botões
        buttons_layout = QHBoxLayout()

        # Botão primário (Entrar) - dialog-primary (48×120px)
        self.login_button = StandardButton(
            "Entrar",
            variant="primary-green",
            semantic_size="dialog-primary"
        )
        self.login_button.clicked.connect(self.on_login_clicked)
        buttons_layout.addWidget(self.login_button)

        # Botão secundário (Cancelar) - dialog-secondary (40×100px)
        self.cancel_button = StandardButton(
            "Cancelar",
            variant="secondary",
            semantic_size="dialog-secondary"
        )
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)

        layout.addLayout(buttons_layout)

        # Versão e informação
        version_label = QLabel("Versão 0.4.1")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet(f"color: {COLORS.TEXT_HINT}; font-size: {TYPO.LABEL_SMALL}px;")
        layout.addWidget(version_label)

        info_label = QLabel(
            "Usuários padrão:\n"
            "operator / operator123\n"
            "eng / eng123\n"
            "admin / admin123"
        )
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet(f"color: {COLORS.TEXT_HINT}; font-size: 10px;")
        layout.addWidget(info_label)

        # Conexões
        self.password_input.returnPressed.connect(self.on_login_clicked)

        # Focus inicial
        self.username_input.setFocus()

    def on_login_clicked(self):
        """
        Processa clique no botão Entrar

        Valida campos e tenta autenticar usuário.
        """
        username = self.username_input.text().strip()
        password = self.password_input.text()

        # Validação de campos vazios
        if not username:
            QMessageBox.warning(
                self,
                "Campo Vazio",
                "Por favor, informe o nome de usuário.",
                QMessageBox.StandardButton.Ok
            )
            self.username_input.setFocus()
            return

        if not password:
            QMessageBox.warning(
                self,
                "Campo Vazio",
                "Por favor, informe a senha.",
                QMessageBox.StandardButton.Ok
            )
            self.password_input.setFocus()
            return

        # Tenta autenticar
        if self.auth_service.authenticate(username, password):
            # Login bem-sucedido
            logger.info(f"Login bem-sucedido: {username}")
            self.login_successful.emit()
            self.accept()
        else:
            # Login falhou
            logger.warning(f"Tentativa de login falhou: {username}")
            QMessageBox.critical(
                self,
                "Erro de Autenticação",
                "Usuário ou senha incorretos.\n\n"
                "Verifique suas credenciais e tente novamente.",
                QMessageBox.StandardButton.Ok
            )
            self.password_input.clear()
            self.password_input.setFocus()

    def show_error(self, message: str):
        """
        Exibe mensagem de erro genérica

        Args:
            message: Mensagem de erro
        """
        QMessageBox.critical(self, "Erro", message)
