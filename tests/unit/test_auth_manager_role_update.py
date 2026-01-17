"""
Testes para verificar se AuthenticationManager atualiza RoleManager corretamente

Testa a correção do bug onde RoleManager não era atualizado quando usuário fazia login.

Author: Claude Sonnet 4.5
Created: 2026-01-17
"""

import pytest
from unittest.mock import Mock, MagicMock
from pathlib import Path
import sys

# Import direto para evitar PyQt6 dependency
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from aoi_lib.auth.user import User, UserRole
from aoi_lib.auth.auth_service import AuthService
from consumo_lib.managers.role_manager import RoleManager
from consumo_lib.facades.authentication_manager import AuthenticationManager


# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def mock_auth_service():
    """Cria mock do AuthService."""
    service = Mock(spec=AuthService)
    service.is_authenticated.return_value = True

    # Criar usuário engineering
    eng_user = User(
        username="eng",
        role=UserRole.ENGINEERING,
        full_name="Engineering User"
    )
    service.get_current_user.return_value = eng_user

    return service


@pytest.fixture
def mock_auth_config_manager():
    """Cria mock do AuthConfigManager."""
    manager = Mock()
    manager.get_require_login_on_startup.return_value = False
    manager.get_default_role.return_value = "operator"
    manager.get_free_navigation_enabled.return_value = False
    return manager


@pytest.fixture
def role_manager():
    """Cria RoleManager com role padrão operator."""
    manager = RoleManager()
    # Verificar que role padrão é operator
    assert manager.get_current_role() == "operator"
    return manager


@pytest.fixture
def mock_main_window(role_manager):
    """Cria mock da MainWindow com RoleManager."""
    window = Mock()
    window.role_manager = role_manager
    window.statusBar = Mock()
    window.statusBar.return_value.showMessage = Mock()
    return window


@pytest.fixture
def auth_manager(mock_auth_service, mock_auth_config_manager, mock_main_window):
    """Cria AuthenticationManager para testes."""
    return AuthenticationManager(
        mock_auth_service,
        mock_auth_config_manager,
        mock_main_window
    )


# ==============================================================================
# Testes Principais
# ==============================================================================

class TestAuthenticationManagerRoleUpdate:
    """Testa se AuthenticationManager atualiza RoleManager corretamente."""

    def test_apply_role_permissions_updates_role_manager(
        self,
        auth_manager,
        role_manager,
        mock_auth_service
    ):
        """
        Testa se apply_role_permissions() atualiza RoleManager.

        BUG: Antes da correção, RoleManager continuava com role "operator"
        mesmo após usuário "eng" fazer login.
        """
        # Arrange: RoleManager começa com role padrão "operator"
        initial_role = role_manager.get_current_role()
        assert initial_role == "operator", "Role inicial deve ser operator"

        # Act: Aplicar permissões (simula pós-login)
        auth_manager.apply_role_permissions()

        # Assert: RoleManager deve ser atualizado para "engineering"
        final_role = role_manager.get_current_role()
        assert final_role == "engineering", (
            f"Role deve ser atualizado para 'engineering', mas é '{final_role}'. "
            "BUG: RoleManager não foi atualizado em apply_role_permissions()"
        )

    def test_role_manager_has_permission_after_update(
        self,
        auth_manager,
        role_manager,
        mock_auth_service
    ):
        """
        Testa se has_permission() funciona corretamente após atualização.

        BUG: Antes da correção, has_permission('settings.engineering')
        retornava False mesmo para usuário engineering.
        """
        # Arrange & Act: Aplicar permissões
        auth_manager.apply_role_permissions()

        # Assert: has_permission deve funcionar corretamente
        assert role_manager.has_permission('settings.engineering'), (
            "Usuário engineering deve ter permissão 'settings.engineering'"
        )
        assert role_manager.has_permission('cnc.manual_control'), (
            "Usuário engineering deve ter permissão 'cnc.manual_control'"
        )

    def test_can_access_engineering_settings(
        self,
        auth_manager,
        role_manager,
        mock_auth_service
    ):
        """
        Testa se can_access_engineering_settings() retorna True após atualização.
        """
        # Arrange & Act: Aplicar permissões
        auth_manager.apply_role_permissions()

        # Assert
        assert role_manager.can_access_engineering_settings(), (
            "Usuário engineering deve poder acessar configurações de engenharia"
        )

    def test_role_manager_updates_from_operator_to_admin(
        self,
        role_manager,
        mock_main_window
    ):
        """
        Testa se RoleManager é atualizado de operator para admin.
        """
        # Arrange: Criar usuário admin
        auth_service = Mock()
        admin_user = User(
            username="admin",
            role=UserRole.ADMIN,
            full_name="Administrator"
        )
        auth_service.is_authenticated.return_value = True
        auth_service.get_current_user.return_value = admin_user

        # Criar auth_manager com usuário admin
        auth_config_mgr = Mock()
        auth_manager = AuthenticationManager(
            auth_service,
            auth_config_mgr,
            mock_main_window
        )

        # Act: Aplicar permissões
        auth_manager.apply_role_permissions()

        # Assert: RoleManager deve ser atualizado para "admin"
        assert role_manager.get_current_role() == "admin"

    def test_role_manager_updates_from_operator_to_engineering(
        self,
        role_manager,
        mock_main_window
    ):
        """
        Testa se RoleManager é atualizado de operator para engineering.
        """
        # Arrange: Criar usuário engineering
        auth_service = Mock()
        engineering_user = User(
            username="eng",
            role=UserRole.ENGINEERING,
            full_name="Engineering User"
        )
        auth_service.is_authenticated.return_value = True
        auth_service.get_current_user.return_value = engineering_user

        # Criar auth_manager com usuário engineering
        auth_config_mgr = Mock()
        auth_manager = AuthenticationManager(
            auth_service,
            auth_config_mgr,
            mock_main_window
        )

        # Act: Aplicar permissões
        auth_manager.apply_role_permissions()

        # Assert: RoleManager deve ser atualizado para "engineering"
        assert role_manager.get_current_role() == "engineering"


# ==============================================================================
# Testes de Regressão
# ==============================================================================

class TestRegressionRoleUpdateBug:
    """Testes de regressão para garantir que o bug não retorne."""

    def test_operator_login_does_not_change_role(
        self,
        role_manager,
        mock_main_window
    ):
        """
        Testa que login com operator não muda role (já é operator).

        Este teste garante que a atualização de role não é redundante.
        """
        # Arrange: Criar usuário operator
        auth_service = Mock()
        operator_user = User(
            username="operator",
            role=UserRole.OPERATOR,
            full_name="Operator"
        )
        auth_service.is_authenticated.return_value = True
        auth_service.get_current_user.return_value = operator_user

        # Criar auth_manager
        auth_config_mgr = Mock()
        auth_manager = AuthenticationManager(
            auth_service,
            auth_config_mgr,
            mock_main_window
        )

        # Act: Aplicar permissões
        auth_manager.apply_role_permissions()

        # Assert: Role deve continuar "operator"
        assert role_manager.get_current_role() == "operator"

    def test_role_not_updated_when_not_authenticated(
        self,
        auth_manager,
        role_manager
    ):
        """
        Testa que RoleManager NÃO é atualizado quando usuário não está autenticado.
        """
        # Arrange: Simular não autenticado
        auth_manager.auth_service.is_authenticated.return_value = False

        # Act: Tentar aplicar permissões
        auth_manager.apply_role_permissions()

        # Assert: Role deve continuar "operator" (não modificado)
        assert role_manager.get_current_role() == "operator"
