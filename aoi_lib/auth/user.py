"""
Modelo de Usuário e Controle de Permissões

Define os perfis de usuário e suas permissões no sistema.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List


class UserRole(Enum):
    """Perfis de usuário do sistema"""
    OPERATOR = "operator"
    ENGINEERING = "engineering"
    ADMIN = "admin"


@dataclass
class User:
    """Representa um usuário do sistema"""

    username: str
    full_name: str
    role: UserRole
    is_active: bool = True

    def can_edit_programs(self) -> bool:
        """Verifica se usuário pode editar programas"""
        return self.role in [UserRole.ENGINEERING, UserRole.ADMIN]

    def can_execute_programs(self) -> bool:
        """Verifica se usuário pode executar programas"""
        return True  # Todos os perfis podem executar

    def can_view_history(self) -> bool:
        """Verifica se usuário pode ver histórico"""
        return True  # Todos os perfis podem ver histórico

    def can_edit_system_config(self) -> bool:
        """Verifica se usuário pode editar configurações do sistema"""
        return self.role in [UserRole.ENGINEERING, UserRole.ADMIN]

    def has_permission(self, permission: str) -> bool:
        """Verifica se usuário tem permissão específica"""
        role_permissions = PERMISSIONS.get(self.role, {})
        return role_permissions.get(permission, False)

    def __str__(self) -> str:
        """Representação string do usuário"""
        return f"{self.full_name} ({self.role.value})"


# Matriz de permissões por perfil
PERMISSIONS: Dict[UserRole, Dict[str, bool]] = {
    UserRole.OPERATOR: {
        "execute_programs": True,
        "edit_programs": False,
        "create_programs": False,
        "edit_system_config": False,
        "view_history": True,
        "generate_reports": True,
        "manage_users": False,
    },
    UserRole.ENGINEERING: {
        "execute_programs": True,
        "edit_programs": True,
        "create_programs": True,
        "edit_system_config": True,
        "view_history": True,
        "generate_reports": True,
        "manage_users": False,
    },
    UserRole.ADMIN: {
        "execute_programs": True,
        "edit_programs": True,
        "create_programs": True,
        "edit_system_config": True,
        "view_history": True,
        "generate_reports": True,
        "manage_users": True,
    }
}
