"""
managers/role_manager.py
------------------------
Gerencia roles e permissões de usuários (RoleManager).
"""
import logging
from PyQt6.QtCore import QObject, pyqtSignal
from enum import Enum
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class UserRole(Enum):
    """Roles disponíveis no sistema."""
    OPERATOR = "operator"
    ENGINEERING = "engineering"
    QUALITY = "quality"
    ADMIN = "admin"


class PermissionDeniedError(Exception):
    """Exceção lançada quando permissão é negada."""
    pass


class RoleManager(QObject):
    """
    Gerencia roles e permissões de usuários.

    Responsabilidades:
        - Definir roles disponíveis
        - Checar permissões baseado em role
        - Gerenciar role do usuário atual
        - Validar acesso a funcionalidades

    Permissões por Role:
        - operator: Pode executar medições, visualizar resultados básicos
        - engineering: Pode configurar receitas, calibrar sistema, ver controles avançados
        - quality: Pode gerar relatórios, ver histórico detalhado
        - admin: Acesso total a configurações do sistema
    """

    # Signals
    role_changed = pyqtSignal(str)  # new_role
    permission_denied = pyqtSignal(str)  # attempted_permission

    # Definição de permissões por role
    ROLE_PERMISSIONS: Dict[UserRole, List[str]] = {
        UserRole.OPERATOR: [
            "tension.execute",
            "tension.view_results",
            "stencil.select",
            "program.select",
            "session.log"
        ],
        UserRole.ENGINEERING: [
            "tension.execute",
            "tension.view_results",
            "tension.configure_parameters",
            "stencil.select",
            "stencil.create",
            "stencil.edit",
            "program.select",
            "program.configure",
            "recipe.create",
            "recipe.edit",
            "recipe.delete",
            "cnc.manual_control",
            "calibration.configure",
            "settings.engineering"
        ],
        UserRole.QUALITY: [
            "tension.execute",
            "tension.view_results",
            "tension.view_history",
            "stencil.select",
            "program.select",
            "report.generate",
            "report.export",
            "statistics.view"
        ],
        UserRole.ADMIN: [
            "tension.execute",
            "tension.view_results",
            "tension.configure_parameters",
            "stencil.select",
            "stencil.create",
            "stencil.edit",
            "stencil.delete",
            "program.select",
            "program.configure",
            "recipe.create",
            "recipe.edit",
            "recipe.delete",
            "cnc.manual_control",
            "calibration.configure",
            "settings.engineering",
            "settings.system",
            "user.manage",
            "report.generate",
            "report.export",
            "statistics.view"
        ]
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_role: Optional[UserRole] = UserRole.OPERATOR  # Default: operator
        self._operator_id: Optional[str] = None

        logger.info(f"RoleManager inicializado. Role atual: {self._current_role.value}")

    def get_current_role(self) -> str:
        """
        Retorna a role do usuário atual.

        Returns:
            Role atual como string (e.g., "operator", "engineering")
        """
        return self._current_role.value

    def set_role(self, role: str) -> bool:
        """
        Define a role do usuário atual.

        Args:
            role: Role como string ("operator", "engineering", etc.)

        Returns:
            True se role foi definida com sucesso
        """
        try:
            old_role = self._current_role
            logger.debug(f"set_role() chamado: role='{role}', current_role='{old_role.value if old_role else None}'")

            new_role = UserRole(role)
            self._current_role = new_role

            logger.info(f"Role alterada: {old_role.value if old_role else 'None'} → {new_role.value}")
            self.role_changed.emit(new_role.value)
            return True
        except ValueError:
            logger.error(f"Role inválida: {role}")
            return False

    def set_operator_id(self, operator_id: str):
        """
        Define o ID do operador atual (para logging de sessões).

        Args:
            operator_id: ID único do operador (e.g., "OP-001", badge ID)
        """
        self._operator_id = operator_id
        logger.info(f"Operator ID definido: {operator_id}")

    def get_operator_id(self) -> Optional[str]:
        """
        Retorna o ID do operador atual.

        Returns:
            Operator ID ou None se não definido
        """
        return self._operator_id

    def has_permission(self, permission: str) -> bool:
        """
        Verifica se a role atual tem uma permissão específica.

        Args:
            permission: Permissão a verificar (e.g., "tension.execute")

        Returns:
            True se role tem a permissão, False caso contrário
        """
        allowed_permissions = self.ROLE_PERMISSIONS.get(self._current_role, [])
        has_perm = permission in allowed_permissions

        logger.debug(
            f"has_permission('{permission}'): role={self._current_role.value}, "
            f"allowed={allowed_permissions}, has_perm={has_perm}"
        )

        if not has_perm:
            logger.warning(
                f"Permissão negada: role={self._current_role.value}, "
                f"permission={permission}"
            )
            self.permission_denied.emit(permission)

        return has_perm

    def check_permission(self, permission: str) -> bool:
        """
        Verifica permissão e lança exceção se negada.

        Args:
            permission: Permissão a verificar

        Returns:
            True se tem permissão

        Raises:
            PermissionDeniedError: Se não tem permissão
        """
        if not self.has_permission(permission):
            raise PermissionDeniedError(
                f"Role '{self._current_role.value}' não tem permissão para '{permission}'"
            )
        return True

    def can_view_advanced_controls(self) -> bool:
        """
        Verifica se role atual pode ver controles avançados.

        Returns:
            True se engineering, quality ou admin
        """
        return self._current_role in [
            UserRole.ENGINEERING,
            UserRole.QUALITY,
            UserRole.ADMIN
        ]

    def can_execute_inspection(self) -> bool:
        """
        Verifica se role atual pode executar medições de tensão.

        Returns:
            True se tem permissão de execução
        """
        return self.has_permission("tension.execute")

    def can_manage_recipes(self) -> bool:
        """
        Verifica se role atual pode gerenciar receitas.

        Returns:
            True se pode criar/editar receitas
        """
        return self.has_permission("recipe.edit")

    def can_access_engineering_settings(self) -> bool:
        """
        Verifica se role atual pode acessar configurações de engenharia.

        Returns:
            True se engineering ou admin
        """
        return self._current_role in [UserRole.ENGINEERING, UserRole.ADMIN]

    def get_all_permissions_for_role(self, role: str) -> List[str]:
        """
        Retorna todas as permissões de uma role específica.

        Args:
            role: Role como string

        Returns:
            Lista de permissões da role
        """
        try:
            role_enum = UserRole(role)
            return self.ROLE_PERMISSIONS.get(role_enum, [])
        except ValueError:
            logger.error(f"Role inválida ao buscar permissões: {role}")
            return []

    def get_available_roles(self) -> List[str]:
        """
        Retorna todas as roles disponíveis no sistema.

        Returns:
            Lista de roles como strings
        """
        return [r.value for r in UserRole]
