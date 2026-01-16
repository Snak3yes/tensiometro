"""
Gerenciador de Configuração de Autenticação

Gerencia configurações de autenticação do sistema, incluindo:
- Exigência de login ao iniciar
- Papel (role) padrão para auto-login
- Controle de permissões para modificar configurações
- Auditoria de mudanças de configuração

Author: Claude Sonnet 4.5
Created: 2026-01-15
"""

import logging
from typing import Dict, Optional
from datetime import datetime

from aoi_lib.config_manager import AOIConfigManager
from aoi_lib.auth.auth_service import AuthService
from consumo_lib.managers.role_manager import RoleManager, UserRole

logger = logging.getLogger(__name__)


class AuthConfigManager:
    """
    Gerencia configurações de autenticação do sistema.

    Responsabilidades:
        - Ler configurações de autenticação do arquivo de configuração
        - Validar permissões para modificar configurações (engineering+)
        - Atualizar configurações com confirmação de senha
        - Auditar mudanças de configuração
        - Validar papéis (roles) válidos

    Atributos:
        config_manager: Gerenciador de configuração AOI
        role_manager: Gerenciador de papéis e permissões
        auth_service: Serviço de autenticação

    Exemplo:
        >>> auth_config = AuthConfigManager(config_mgr, role_mgr, auth_svc)
        >>> if auth_config.can_modify_config():
        ...     auth_config.update_config(
        ...         require_login=False,
        ...         default_role="operator",
        ...         confirming_user="eng",
        ...         password="eng123"
        ...     )
    """

    # Roles válidos para auto-login
    VALID_ROLES = ["operator", "engineering", "quality", "admin"]

    # Roles que podem modificar configuração de autenticação
    AUTH_CONFIG_PERMISSION = "settings.engineering"

    def __init__(
        self,
        config_manager: AOIConfigManager,
        role_manager: RoleManager,
        auth_service: AuthService
    ):
        """
        Inicializa gerenciador de configuração de autenticação.

        Args:
            config_manager: Gerenciador de configuração AOI
            role_manager: Gerenciador de papéis e permissões
            auth_service: Serviço de autenticação
        """
        self.config_manager = config_manager
        self.role_manager = role_manager
        self.auth_service = auth_service
        self.log = logger

    def can_modify_config(self) -> bool:
        """
        Verifica se o usuário atual pode modificar configuração de autenticação.

        Returns:
            True se usuário tem permissão engineering+, False caso contrário.
        """
        current_role = self.role_manager.get_current_role()

        # Verifica se usuário está autenticado
        if not current_role:
            self.log.warning("Tentativa de verificar permissões sem usuário autenticado")
            return False

        # Verifica permissão settings.engineering (usa has_permission, não check_permission)
        has_permission = self.role_manager.has_permission(
            self.AUTH_CONFIG_PERMISSION
        )

        if not has_permission:
            self.log.warning(
                f"Usuário {self.auth_service.get_current_user().username} "
                f"sem permissão para modificar configuração de autenticação"
            )

        return has_permission

    def get_current_config(self) -> Dict:
        """
        Lê configuração atual de autenticação.

        Returns:
            Dicionário com configurações atuais:
            {
                'require_login_on_startup': bool,
                'default_role': str
            }

            Se seção não existir, retorna valores padrão.
        """
        config = {
            'require_login_on_startup': self.config_manager.get_require_login_on_startup(),
            'default_role': self.config_manager.get_default_role()
        }

        self.log.debug(f"Configuração atual lida: {config}")
        return config

    def update_config(
        self,
        require_login: bool,
        default_role: str,
        confirming_user: str,
        password: str
    ) -> bool:
        """
        Atualiza configuração de autenticação com confirmação de senha.

        Args:
            require_login: True para exigir login ao iniciar, False para auto-login
            default_role: Papel padrão para auto-login (operator|engineering|quality|admin)
            confirming_user: Nome de usuário que está confirmando a mudança
            password: Senha do usuário para confirmação

        Returns:
            True se configuração foi atualizada com sucesso, False caso contrário.

        Raises:
            PermissionError: Se usuário não tem permissão engineering+
            ValueError: Se role é inválido ou senha incorreta
        """
        # 1. Verificar permissão
        if not self.can_modify_config():
            current_user = self.auth_service.get_current_user()
            error_msg = (
                f"Usuário {current_user.username if current_user else 'N/A'} "
                f"sem permissão para modificar configuração de autenticação"
            )
            self.log.error(error_msg)
            raise PermissionError(error_msg)

        # 2. Validar role
        if not self.validate_role(default_role):
            error_msg = f"Role inválido: {default_role}. Roles válidos: {self.VALID_ROLES}"
            self.log.error(error_msg)
            raise ValueError(error_msg)

        # 3. Capturar configuração atual para auditoria
        old_config = self.get_current_config()

        # 4. Confirmar senha do usuário que está modificando
        if not self.auth_service.authenticate(confirming_user, password):
            error_msg = f"Senha incorreta para usuário {confirming_user}"
            self.log.warning(error_msg)
            raise ValueError(error_msg)

        # 5. Atualizar configuração
        try:
            self.config_manager.set_require_login_on_startup(require_login)
            self.config_manager.set_default_role(default_role)

            new_config = {
                'require_login_on_startup': require_login,
                'default_role': default_role
            }

            # 6. Auditar mudança
            current_user = self.auth_service.get_current_user()
            self._log_config_change(
                user=current_user.username if current_user else confirming_user,
                old_config=old_config,
                new_config=new_config
            )

            self.log.info(
                f"Configuração de autenticação atualizada com sucesso: "
                f"require_login={require_login}, default_role={default_role}"
            )

            return True

        except Exception as e:
            self.log.error(f"Erro ao atualizar configuração: {e}")
            raise

    def validate_role(self, role: str) -> bool:
        """
        Verifica se role é válido.

        Args:
            role: Papel a validar

        Returns:
            True se role é válido, False caso contrário.
        """
        return role in self.VALID_ROLES

    def _log_config_change(
        self,
        user: str,
        old_config: Dict,
        new_config: Dict
    ):
        """
        Registra mudança de configuração no log de auditoria.

        Args:
            user: Nome de usuário que fez a mudança
            old_config: Configuração anterior
            new_config: Nova configuração
        """
        timestamp = datetime.now().isoformat()

        audit_log = (
            f"[{timestamp}] AUDIT: Configuração de autenticação modificada por {user}\n"
            f"  ANTES: require_login={old_config.get('require_login_on_startup')}, "
            f"default_role={old_config.get('default_role')}\n"
            f"  DEPOIS: require_login={new_config.get('require_login_on_startup')}, "
            f"default_role={new_config.get('default_role')}"
        )

        self.log.info(audit_log)

        # TODO: Persistir em arquivo de auditoria separado (futuro)
        # Por enquanto, apenas loga no logger principal
