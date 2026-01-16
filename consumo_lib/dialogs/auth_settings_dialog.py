"""
Dialog de Configurações de Autenticação

Implementa interface para configurar autenticação do sistema:
- Exigência de login ao iniciar
- Papel (role) padrão para auto-login
- Requer permissão engineering+ para modificar
- Confirmação de senha para segurança

Author: Claude Sonnet 4.5
Created: 2026-01-15
"""

import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QCheckBox, QComboBox, QPushButton, QMessageBox,
    QGroupBox, QFormLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from consumo_lib.managers.auth_config_manager import AuthConfigManager
from aoi_lib.auth.auth_service import AuthService

logger = logging.getLogger(__name__)


class AuthenticationSettingsDialog(QDialog):
    """
    Dialog de configurações de autenticação do sistema.

    Permite que usuários engineering+ configurem:
    - Se login é obrigatório ao iniciar aplicação
    - Qual papel (role) usar para auto-login

    Atributos:
        auth_config_manager: Gerenciador de configuração de autenticação
        current_role: Papel do usuário atual
        config_changed: Sinal emitido quando configuração muda
    """

    config_changed = pyqtSignal()

    # Roles válidos para auto-login
    ROLES = [
        ("operator", "Operador"),
        ("engineering", "Engenharia"),
        ("quality", "Qualidade"),
        ("admin", "Administrador")
    ]

    def __init__(
        self,
        auth_config_manager: AuthConfigManager,
        current_role: str,
        parent=None
    ):
        """
        Inicializa dialog de configurações de autenticação.

        Args:
            auth_config_manager: Gerenciador de configuração
            current_role: Papel do usuário atual
            parent: Widget pai
        """
        super().__init__(parent)
        self.auth_config_manager = auth_config_manager
        self.current_role = current_role
        self.original_config = {}
        self.confirming_user = ""

        self.setup_ui()
        self.load_current_config()

    def setup_ui(self):
        """Configura interface do dialog."""
        self.setWindowTitle("Configurações de Autenticação")
        self.setModal(True)
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Título
        title_label = QLabel("Configurações de Autenticação")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Informação de permissões
        permission_label = QLabel(
            "⚠️ Esta configuração requer privilégios de Engenharia ou superior.\n"
            "As alterações serão confirmadas com sua senha."
        )
        permission_label.setStyleSheet("color: #d9534f; padding: 10px; background-color: #f9f2f2; border-radius: 5px;")
        permission_label.setWordWrap(True)
        layout.addWidget(permission_label)

        # Grupo: Configurações de Login
        login_group = QGroupBox("Configurações de Login")
        login_layout = QFormLayout(login_group)

        # Checkbox: Solicitar login ao iniciar
        self.chk_require_login = QCheckBox(
            "Solicitar login ao iniciar a aplicação"
        )
        self.chk_require_login.setToolTip(
            "Se desmarcado, o aplicativo fará login automático com o papel padrão."
        )
        self.chk_require_login.stateChanged.connect(self.on_config_changed)
        login_layout.addRow("", self.chk_require_login)

        # ComboBox: Papel padrão
        self.lbl_default_role = QLabel("Papel padrão para auto-login:")
        self.combo_default_role = QComboBox()
        self.combo_default_role.setMinimumWidth(200)
        for role_id, role_name in self.ROLES:
            self.combo_default_role.addItem(role_name, role_id)
        self.combo_default_role.setToolTip(
            "Papel (role) usado quando login automático está ativado."
        )
        self.combo_default_role.currentIndexChanged.connect(self.on_config_changed)
        login_layout.addRow(self.lbl_default_role, self.combo_default_role)

        layout.addWidget(login_group)

        # Explicação
        info_text = QLabel(
            "<b>Nota:</b> Se 'Solicitar login ao iniciar' estiver desmarcado, "
            "o aplicativo ignorará a tela de login e iniciará diretamente com "
            "o papel padrão selecionado."
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet("color: #666; padding: 10px;")
        layout.addWidget(info_text)

        layout.addSpacing(20)

        # Botões
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        self.btn_apply = QPushButton("Aplicar")
        self.btn_apply.setMinimumHeight(40)
        self.btn_apply.setMinimumWidth(120)
        self.btn_apply.setEnabled(False)  # Desabilitado até mudar config
        self.btn_apply.clicked.connect(self.on_apply_clicked)
        buttons_layout.addWidget(self.btn_apply)

        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setMinimumHeight(40)
        self.btn_cancel.setMinimumWidth(120)
        self.btn_cancel.clicked.connect(self.reject)
        buttons_layout.addWidget(self.btn_cancel)

        layout.addLayout(buttons_layout)

    def load_current_config(self):
        """
        Carrega configuração atual e preenche campos.

        Também armazena configuração original para detectar mudanças.
        """
        try:
            config = self.auth_config_manager.get_current_config()
            self.original_config = config.copy()

            # Preenche campos
            self.chk_require_login.setChecked(config['require_login_on_startup'])

            # Encontra índice do role no combo
            for i in range(self.combo_default_role.count()):
                if self.combo_default_role.itemData(i) == config['default_role']:
                    self.combo_default_role.setCurrentIndex(i)
                    break

            # Atualiza estado do botão Aplicar
            self.on_config_changed()

            logger.debug(f"Configuração carregada: {config}")

        except Exception as e:
            logger.error(f"Erro ao carregar configuração: {e}")
            QMessageBox.critical(
                self,
                "Erro",
                f"Erro ao carregar configuração:\n{e}",
                QMessageBox.StandardButton.Ok
            )
            self.reject()

    def on_config_changed(self):
        """
        Handler chamado quando configuração é modificada.

        Habilita/desabilita botão Aplicar baseado em mudanças.
        """
        require_login = self.chk_require_login.isChecked()
        role_index = self.combo_default_role.currentIndex()
        default_role = self.combo_default_role.itemData(role_index)

        # Verifica se mudou em relação ao original
        changed = (
            require_login != self.original_config.get('require_login_on_startup') or
            default_role != self.original_config.get('default_role')
        )

        self.btn_apply.setEnabled(changed)

        # Atualiza visibilidade do combo
        self.lbl_default_role.setEnabled(not require_login)
        self.combo_default_role.setEnabled(not require_login)

        if not require_login:
            self.lbl_default_role.setToolTip(
                "Papel usado para login automático quando login NÃO é obrigatório."
            )
            self.combo_default_role.setToolTip(
                "Papel usado para login automático quando login NÃO é obrigatório."
            )
        else:
            self.lbl_default_role.setToolTip(
                "Quando login é obrigatório, esta opção não é usada."
            )
            self.combo_default_role.setToolTip(
                "Quando login é obrigatório, esta opção não é usada."
            )

    def on_apply_clicked(self):
        """
        Processa clique no botão Aplicar.

        Fluxo:
        1. Verifica permissão (deve ser engineering+)
        2. Se desabilitando login, mostra dialog de confirmação de senha
        3. Atualiza configuração
        4. Emite sinal config_changed
        5. Fecha dialog
        """
        # 1. Verificar permissão
        if not self.auth_config_manager.can_modify_config():
            QMessageBox.warning(
                self,
                "Permissão Negada",
                "Você não tem permissão para modificar configurações de autenticação.\n"
                "Esta operação requer privilégios de Engenharia ou superior.",
                QMessageBox.StandardButton.Ok
            )
            return

        # 2. Capturar novos valores
        require_login = self.chk_require_login.isChecked()
        role_index = self.combo_default_role.currentIndex()
        default_role = self.combo_default_role.itemData(role_index)

        # 3. Se está desabilitando login, requer confirmação de senha
        current_user = self.auth_config_manager.auth_service.get_current_user()
        if current_user:
            self.confirming_user = current_user.username
        else:
            # Sem usuário atual, não pode prosseguir
            QMessageBox.warning(
                self,
                "Usuário Não Autenticado",
                "Não há usuário autenticado para confirmar a mudança.",
                QMessageBox.StandardButton.Ok
            )
            return

        # 4. Mostrar dialog de confirmação com senha
        self.show_confirmation_dialog(require_login, default_role)

    def show_confirmation_dialog(self, require_login: bool, default_role: str):
        """
        Mostra dialog de confirmação de senha.

        Args:
            require_login: Novo valor para require_login_on_startup
            default_role: Novo valor para default_role
        """
        # Cria dialog simples de senha
        from PyQt6.QtWidgets import QLineEdit, QDialogButtonBox

        confirm_dialog = QDialog(self)
        confirm_dialog.setWindowTitle("Confirmar Alteração")
        confirm_dialog.setModal(True)
        confirm_dialog.setMinimumWidth(400)

        layout = QVBoxLayout(confirm_dialog)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Mensagem
        message = QLabel(
            f"Para confirmar a alteração de configuração,\n"
            f"digite sua senha:"
        )
        message.setWordWrap(True)
        layout.addWidget(message)

        # Campo de senha
        password_input = QLineEdit()
        password_input.setEchoMode(QLineEdit.EchoMode.Password)
        password_input.setMinimumHeight(35)
        password_input.setPlaceholderText("Senha")
        layout.addWidget(QLabel("Senha:"))
        layout.addWidget(password_input)

        # Botões
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(confirm_dialog.accept)
        buttons.rejected.connect(confirm_dialog.reject)
        layout.addWidget(buttons)

        # Focus e Enter
        password_input.setFocus()
        password_input.returnPressed.connect(confirm_dialog.accept)

        # Mostra dialog
        if confirm_dialog.exec() == QDialog.DialogCode.Accepted:
            password = password_input.text()

            # Tenta atualizar configuração
            try:
                success = self.auth_config_manager.update_config(
                    require_login=require_login,
                    default_role=default_role,
                    confirming_user=self.confirming_user,
                    password=password
                )

                if success:
                    QMessageBox.information(
                        self,
                        "Sucesso",
                        "Configuração de autenticação atualizada com sucesso!\n\n"
                        f"Login ao iniciar: {'Sim' if require_login else 'Não (auto-login)'}\n"
                        f"Papel padrão: {default_role}",
                        QMessageBox.StandardButton.Ok
                    )

                    # Emite sinal de mudança
                    self.config_changed.emit()

                    # Fecha dialog
                    self.accept()
                else:
                    QMessageBox.warning(
                        self,
                        "Erro",
                        "Não foi possível atualizar a configuração.",
                        QMessageBox.StandardButton.Ok
                    )

            except PermissionError as e:
                QMessageBox.critical(
                    self,
                    "Permissão Negada",
                    f"Permissão negada:\n{e}",
                    QMessageBox.StandardButton.Ok
                )

            except ValueError as e:
                QMessageBox.warning(
                    self,
                    "Erro de Validação",
                    f"Erro de validação:\n{e}",
                    QMessageBox.StandardButton.Ok
                )

            except Exception as e:
                logger.error(f"Erro ao atualizar configuração: {e}", exc_info=True)
                QMessageBox.critical(
                    self,
                    "Erro",
                    f"Erro ao atualizar configuração:\n{e}",
                    QMessageBox.StandardButton.Ok
                )

    def on_cancel_clicked(self):
        """Fecha dialog sem salvar mudanças."""
        self.reject()
