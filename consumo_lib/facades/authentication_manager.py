"""
Authentication Manager - Interface simplificada para autenticação e permissões

Facade que proporciona uma interface simplificada para gerenciar
autenticação de usuários e controle de acesso.
"""

import logging
import sys
from typing import Optional

logger = logging.getLogger(__name__)

PUBLIC_TOOL_ACTIONS = {"tools.tensiometer_calibration"}


class AuthenticationManager:
    """
    Facade para gerenciar autenticação e permissões.

    Esta classe encapsula a complexidade de gerenciar autenticação,
    proporcionando uma interface simplificada para a MainWindow.

    Responsabilidades:
    - Exibir diálogo de login
    - Realizar auto-login
    - Aplicar permissões baseadas em role
    - Exibir configurações de autenticação
    - Notificar mudanças de configuração

    A facade delega para AuthService, mas proporciona métodos
    com nomes mais simples e adequados para a MainWindow.
    """

    def __init__(self, auth_service, auth_config_manager, main_window):
        """
        Inicializa o manager.

        Args:
            auth_service: Serviço de autenticação existente
            auth_config_manager: Gerenciador de configuração de autenticação
            main_window: Janela principal (para diálogos e UI)
        """
        self.auth_service = auth_service
        self.auth_config_manager = auth_config_manager
        self.main_window = main_window

        # Obter RoleManager do main_window se disponível
        self.role_manager = getattr(main_window, 'role_manager', None)

        logger.debug("AuthenticationManager inicializado")

    def show_login_dialog(self) -> bool:
        """
        Exibe o diálogo de login.

        Returns:
            True se login bem-sucedido, False caso contrário
        """
        try:
            from consumo_lib.dialogs import LoginDialog

            dialog = LoginDialog(self.auth_service, parent=self.main_window)

            if dialog.exec() == dialog.DialogCode.Accepted:
                user = self.auth_service.get_current_user()
                username = user.username if user else "N/A"
                role = user.role.value if user else "desconhecido"
                logger.info(f"Login bem-sucedido: {username} ({role})")
                if hasattr(self.main_window, "_sync_authenticated_user_state"):
                    self.main_window._sync_authenticated_user_state()
                return True
            else:
                logger.info("Login cancelado pelo usuário")
                return False
        except Exception as e:
            logger.error(f"Erro ao exibir diálogo de login: {e}")
            return False

    def perform_auto_login(self, default_role: str) -> bool:
        """
        Realiza auto-login com role padrão.

        Args:
            default_role: Role padrão para auto-login
                         (operator|engineering|quality|admin)

        Returns:
            True se auto-login bem-sucedido, False caso contrário
        """
        try:
            # Mapping de role para usuário padrão
            role_to_user = {
                'operator': ('operator', 'operator123'),
                'engineering': ('eng', 'eng123'),
                'quality': ('quality', 'quality123'),
                'admin': ('admin', 'admin123'),
            }

            if default_role not in role_to_user:
                logger.warning(f"Role desconhecido para auto-login: {default_role}")
                return False

            username, password = role_to_user[default_role]

            success = self.auth_service.authenticate(username, password)

            if success:
                logger.info(f"Auto-login bem-sucedido: {username} ({default_role})")
                # IMPORTANTE: Atualizar RoleManager com o role do usuário auto-logado
                self.role_manager.set_role(default_role)
                self.main_window.statusBar().showMessage(
                    f"Auto-login: {username} ({default_role})", 3000
                )
                return True
            else:
                logger.warning(f"Falha no auto-login para {username}")
                # Fallback para diálogo de login
                return self.show_login_dialog()
        except Exception as e:
            logger.error(f"Erro ao realizar auto-login: {e}")
            # Fallback para diálogo de login
            return self.show_login_dialog()

    def apply_role_permissions(self):
        """
        Aplica permissões baseadas no role do usuário atual.

        Habilita/desabilita elementos de UI baseado nas permissões
        do role do usuário autenticado.
        """
        try:
            if not self.auth_service.is_authenticated():
                logger.warning("Usuário não autenticado, não aplicando permissões")
                return

            user_role = self.auth_service.get_current_user().role

            # 🔥 CRÍTICO: Atualizar RoleManager com o role do usuário autenticado
            # Isso garante que has_permission() funciona corretamente
            if self.role_manager:
                self.role_manager.set_role(user_role.value)
                logger.info(f"RoleManager atualizado com role: {user_role.value}")

            # Aplica permissões baseado no role
            self._apply_menu_permissions(user_role)
            self._apply_button_permissions(user_role)
            self._apply_tab_permissions(user_role)

            if hasattr(self.main_window, "_sync_authenticated_user_state"):
                self.main_window._sync_authenticated_user_state()

            logger.info(f"Permissões aplicadas para role: {user_role.name}")
        except Exception as e:
            logger.error(f"Erro ao aplicar permissões: {e}")

    def _apply_menu_permissions(self, user_role):
        """
        Aplica permissões aos menus.

        Args:
            user_role: Role do usuário
        """
        try:
            can_access_tools = self.role_manager.can_access_engineering_settings()

            if hasattr(self.main_window, "menu_handler") and self.main_window.menu_handler:
                self.main_window.menu_handler.apply_tools_permissions(
                    can_access_tools,
                    public_action_keys=PUBLIC_TOOL_ACTIONS,
                )
                self.main_window.menu_handler.apply_system_permissions(
                    self.role_manager.get_current_role() == "admin"
                )

            # Menu Engenharia - apenas engineering+ (usa permissão correta)
            if hasattr(self.main_window, 'engineering_menu'):
                self.main_window.engineering_menu.setEnabled(can_access_tools)

            # Menu Admin - apenas admin (verifica role diretamente)
            if hasattr(self.main_window, 'admin_menu'):
                can_access = self.role_manager.get_current_role() == 'admin'
                self.main_window.admin_menu.setEnabled(can_access)
        except Exception as e:
            logger.error(f"Erro ao aplicar permissões de menu: {e}")

    def _apply_button_permissions(self, user_role):
        """
        Aplica permissões aos botões.

        Args:
            user_role: Role do usuário
        """
        try:
            # Botões de engenharia - apenas engineering+ (usa permissão correta)
            engineering_buttons = [
                'btn_run_tension',
                'btn_save_program',
                'btn_load_program',
            ]

            for btn_name in engineering_buttons:
                if hasattr(self.main_window, btn_name):
                    button = getattr(self.main_window, btn_name)
                    can_access = self.role_manager.can_access_engineering_settings()
                    button.setEnabled(can_access)
        except Exception as e:
            logger.error(f"Erro ao aplicar permissões de botão: {e}")

    def _apply_tab_permissions(self, user_role):
        """
        Aplica permissões às abas.

        Args:
            user_role: Role do usuário
        """
        try:
            # Tab de engenharia - apenas engineering+ (usa permissão correta)
            if hasattr(self.main_window, 'engineering_tab'):
                can_access = self.role_manager.can_access_engineering_settings()
                # Note: QTabWidget não tem setEnabled por índice diretamente
                # Precisa usar Qt.ItemFlags ou remover/adicionar aba
                pass
        except Exception as e:
            logger.error(f"Erro ao aplicar permissões de aba: {e}")

    def show_auth_settings(self):
        """Exibe o diálogo de configurações de autenticação."""
        try:
            # Verifica permissão (apenas engineering+)
            can_access = self.role_manager.can_access_engineering_settings()

            if not can_access:
                logger.warning("Usuário sem permissão para acessar configurações de autenticação")
                self.main_window.statusBar().showMessage(
                    "Acesso negado: Requer permissão Engineering+", 3000
                )
                return

            # Exibe diálogo
            from consumo_lib.dialogs import AuthenticationSettingsDialog

            dialog = AuthenticationSettingsDialog(
                self.auth_config_manager,
                self.auth_service,
                parent=self.main_window
            )

            dialog.auth_config_changed.connect(self._on_auth_config_changed)
            dialog.exec()

        except Exception as e:
            logger.error(f"Erro ao exibir configurações de autenticação: {e}")

    def _on_auth_config_changed(self):
        """
        Callback chamado quando configuração de autenticação muda.

        Atualiza comportamento da aplicação baseado na nova configuração.
        """
        try:
            require_login = self.auth_config_manager.get_require_login_on_startup()
            default_role = self.auth_config_manager.get_default_role()

            logger.info(f"Configuração de autenticação alterada: "
                       f"require_login={require_login}, default_role={default_role}")

            # Se modo de login mudou, notifica usuário
            self.main_window.statusBar().showMessage(
                "Configuração de autenticação atualizada. "
                "As mudanças serão aplicadas no próximo início.",
                5000
            )
        except Exception as e:
            logger.error(f"Erro ao processar mudança de configuração: {e}")

    def is_authenticated(self) -> bool:
        """
        Verifica se há usuário autenticado.

        Returns:
            True se autenticado, False caso contrário
        """
        return self.auth_service.is_authenticated()

    def get_current_user(self):
        """
        Retorna o usuário autenticado.

        Returns:
            User ou None se não autenticado
        """
        return self.auth_service.get_current_user()
