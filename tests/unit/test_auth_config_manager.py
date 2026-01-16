"""
Testes unitários para AuthConfigManager

Testa a gerência de configurações de autenticação, incluindo:
- Verificação de permissões
- Leitura de configurações
- Validação de roles
- Atualização de configurações com confirmação de senha
- Auditoria de mudanças

Author: Claude Sonnet 4.5
Created: 2026-01-15
"""

import pytest
from unittest.mock import Mock
from pathlib import Path
import sys
import tempfile
import json

# Import direto para evitar PyQt6 dependency em consumo_lib/__init__.py
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from aoi_lib.config_manager import AOIConfigManager
from aoi_lib.auth.auth_service import AuthService
from consumo_lib.managers.auth_config_manager import AuthConfigManager
from consumo_lib.managers.role_manager import RoleManager, UserRole


# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def temp_config_file():
    """Cria arquivo de configuração temporário."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        config_data = {
            "cnc": {"system_type": "cartesian"},
            "connections": {"plc_host": "192.168.1.5"},
            "authentication": {
                "require_login_on_startup": True,
                "default_role": "operator"
            }
        }
        json.dump(config_data, f)
        temp_path = f.name
    yield temp_path
    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def mock_config_manager(temp_config_file):
    """Cria mock de AOIConfigManager."""
    config = AOIConfigManager(cfg_path=temp_config_file)
    return config


@pytest.fixture
def mock_auth_service():
    """Cria mock de AuthService."""
    auth_service = Mock(spec=AuthService)
    auth_service.authenticate = Mock(return_value=True)
    auth_service.get_current_user = Mock(
        return_value=Mock(
            username="eng",
            full_name="Engenheiro",
            role=UserRole.ENGINEERING
        )
    )
    return auth_service


@pytest.fixture
def mock_role_manager():
    """Cria mock de RoleManager."""
    role_mgr = Mock(spec=RoleManager)
    role_mgr.get_current_role = Mock(return_value="engineering")
    role_mgr.has_permission = Mock(return_value=True)
    return role_mgr


@pytest.fixture
def auth_config_manager(mock_config_manager, mock_role_manager, mock_auth_service):
    """Cria instância de AuthConfigManager com mocks."""
    return AuthConfigManager(
        config_manager=mock_config_manager,
        role_manager=mock_role_manager,
        auth_service=mock_auth_service
    )


# ==============================================================================
# Testes: can_modify_config()
# ==============================================================================

class TestCanModifyConfig:
    """Testa verificação de permissões para modificar configuração."""

    def test_engineering_user_can_modify_config(self, auth_config_manager, mock_role_manager):
        """
        Testa que usuário engineering pode modificar configuração.

        Given: Usuário com role engineering
        When: Verifica se pode modificar configuração
        Then: Retorna True
        """
        mock_role_manager.get_current_role = Mock(return_value="engineering")
        mock_role_manager.has_permission = Mock(return_value=True)

        result = auth_config_manager.can_modify_config()

        assert result is True
        mock_role_manager.has_permission.assert_called_once_with("settings.engineering")

    def test_admin_user_can_modify_config(self, auth_config_manager, mock_role_manager):
        """
        Testa que usuário admin pode modificar configuração.

        Given: Usuário com role admin
        When: Verifica se pode modificar configuração
        Then: Retorna True
        """
        mock_role_manager.get_current_role = Mock(return_value="admin")
        mock_role_manager.has_permission = Mock(return_value=True)

        result = auth_config_manager.can_modify_config()

        assert result is True

    def test_operator_user_cannot_modify_config(self, auth_config_manager, mock_role_manager):
        """
        Testa que usuário operator NÃO pode modificar configuração.

        Given: Usuário com role operator
        When: Verifica se pode modificar configuração
        Then: Retorna False
        """
        mock_role_manager.get_current_role = Mock(return_value="operator")
        mock_role_manager.has_permission = Mock(return_value=False)

        result = auth_config_manager.can_modify_config()

        assert result is False

    def test_quality_user_cannot_modify_config(self, auth_config_manager, mock_role_manager):
        """
        Testa que usuário quality NÃO pode modificar configuração.

        Given: Usuário com role quality
        When: Verifica se pode modificar configuração
        Then: Retorna False
        """
        mock_role_manager.get_current_role = Mock(return_value="quality")
        mock_role_manager.has_permission = Mock(return_value=False)

        result = auth_config_manager.can_modify_config()

        assert result is False

    def test_no_authenticated_user_cannot_modify_config(self, auth_config_manager, mock_role_manager):
        """
        Testa que usuário não autenticado NÃO pode modificar configuração.

        Given: Nenhum usuário autenticado (get_current_role() = None)
        When: Verifica se pode modificar configuração
        Then: Retorna False
        """
        mock_role_manager.get_current_role = Mock(return_value=None)

        result = auth_config_manager.can_modify_config()

        assert result is False


# ==============================================================================
# Testes: get_current_config()
# ==============================================================================

class TestGetCurrentConfig:
    """Testa leitura de configuração atual."""

    def test_returns_default_values_when_section_missing(self, auth_config_manager, mock_config_manager):
        """
        Testa que retorna valores padrão quando seção não existe.

        Given: Seção 'authentication' não existe no config
        When: Lê configuração atual
        Then: Retorna valores padrão (require_login=True, default_role='operator')
        """
        # Remove seção authentication
        if "authentication" in mock_config_manager.data:
            del mock_config_manager.data["authentication"]

        config = auth_config_manager.get_current_config()

        assert config['require_login_on_startup'] is True
        assert config['default_role'] == 'operator'

    def test_returns_existing_values_when_config_present(self, auth_config_manager, mock_config_manager):
        """
        Testa que retorna valores existentes quando configuração está presente.

        Given: Seção 'authentication' existe com valores customizados
        When: Lê configuração atual
        Then: Retorna valores customizados
        """
        # Configura valores customizados
        mock_config_manager.set("authentication", "require_login_on_startup", value=False)
        mock_config_manager.set("authentication", "default_role", value="engineering")

        config = auth_config_manager.get_current_config()

        assert config['require_login_on_startup'] is False
        assert config['default_role'] == 'engineering'

    def test_handles_invalid_values_gracefully(self, auth_config_manager, mock_config_manager):
        """
        Testa que lida com valores inválidos sem falhar.

        Given: Seção 'authentication' com valor inválido para default_role
        When: Lê configuração atual
        Then: Retorna valor inválido (deixa validação para camada superior)
        """
        # Configura valor inválido
        mock_config_manager.data["authentication"]["default_role"] = "invalid_role"

        config = auth_config_manager.get_current_config()

        # Deve retornar o valor, mesmo que inválido
        assert config['default_role'] == 'invalid_role'


# ==============================================================================
# Testes: validate_role()
# ==============================================================================

class TestValidateRole:
    """Testa validação de roles."""

    def test_accepts_valid_role_operator(self, auth_config_manager):
        """Testa que aceita role 'operator'."""
        assert auth_config_manager.validate_role("operator") is True

    def test_accepts_valid_role_engineering(self, auth_config_manager):
        """Testa que aceita role 'engineering'."""
        assert auth_config_manager.validate_role("engineering") is True

    def test_accepts_valid_role_quality(self, auth_config_manager):
        """Testa que aceita role 'quality'."""
        assert auth_config_manager.validate_role("quality") is True

    def test_accepts_valid_role_admin(self, auth_config_manager):
        """Testa que aceita role 'admin'."""
        assert auth_config_manager.validate_role("admin") is True

    def test_rejects_invalid_role(self, auth_config_manager):
        """Testa que rejeita role inválido."""
        assert auth_config_manager.validate_role("invalid_role") is False

    def test_rejects_empty_role(self, auth_config_manager):
        """Testa que rejeita role vazio."""
        assert auth_config_manager.validate_role("") is False

    def test_rejects_case_sensitive_variants(self, auth_config_manager):
        """Testa que validação é case-sensitive."""
        assert auth_config_manager.validate_role("Operator") is False
        assert auth_config_manager.validate_role("OPERATOR") is False
        assert auth_config_manager.validate_role("Engineering") is False


# ==============================================================================
# Testes: update_config()
# ==============================================================================

class TestUpdateConfig:
    """Testa atualização de configuração."""

    def test_successful_update_with_valid_credentials(
        self,
        auth_config_manager,
        mock_config_manager,
        mock_auth_service,
        mock_role_manager
    ):
        """
        Testa atualização bem-sucedida com credenciais válidas.

        Given: Usuário engineering com senha correta
        When: Atualiza configuração
        Then: Configuração é atualizada e retorna True
        """
        mock_role_manager.get_current_role = Mock(return_value="engineering")
        mock_role_manager.has_permission = Mock(return_value=True)
        mock_auth_service.authenticate = Mock(return_value=True)

        result = auth_config_manager.update_config(
            require_login=False,
            default_role="operator",
            confirming_user="eng",
            password="eng123"
        )

        assert result is True
        assert mock_config_manager.get_require_login_on_startup() is False
        assert mock_config_manager.get_default_role() == "operator"
        mock_auth_service.authenticate.assert_called_once_with("eng", "eng123")

    def test_fails_with_invalid_password(
        self,
        auth_config_manager,
        mock_auth_service,
        mock_role_manager
    ):
        """
        Testa que falha com senha incorreta.

        Given: Usuário engineering com senha incorreta
        When: Tenta atualizar configuração
        Then: Lança ValueError e configuração NÃO é alterada
        """
        mock_role_manager.get_current_role = Mock(return_value="engineering")
        mock_role_manager.has_permission = Mock(return_value=True)
        mock_auth_service.authenticate = Mock(return_value=False)

        with pytest.raises(ValueError, match="Senha incorreta"):
            auth_config_manager.update_config(
                require_login=False,
                default_role="operator",
                confirming_user="eng",
                password="wrong_password"
            )

    def test_fails_for_non_engineering_user(
        self,
        auth_config_manager,
        mock_auth_service,
        mock_role_manager
    ):
        """
        Testa que falha para usuário sem permissão engineering+.

        Given: Usuário operator tentando modificar configuração
        When: Tenta atualizar configuração
        Then: Lança PermissionError
        """
        mock_role_manager.get_current_role = Mock(return_value="operator")
        mock_role_manager.has_permission = Mock(return_value=False)

        with pytest.raises(PermissionError, match="sem permissão"):
            auth_config_manager.update_config(
                require_login=False,
                default_role="operator",
                confirming_user="operator",
                password="operator123"
            )

    def test_fails_for_invalid_role(
        self,
        auth_config_manager,
        mock_auth_service,
        mock_role_manager
    ):
        """
        Testa que falha para role inválido.

        Given: Role inválido fornecido
        When: Tenta atualizar configuração
        Then: Lança ValueError
        """
        mock_role_manager.get_current_role = Mock(return_value="engineering")
        mock_role_manager.has_permission = Mock(return_value=True)

        with pytest.raises(ValueError, match="Role inválido"):
            auth_config_manager.update_config(
                require_login=False,
                default_role="invalid_role",
                confirming_user="eng",
                password="eng123"
            )

    def test_logs_configuration_changes(
        self,
        auth_config_manager,
        mock_config_manager,
        mock_auth_service,
        mock_role_manager,
        caplog
    ):
        """
        Testa que mudanças de configuração são auditadas.

        Given: Usuário engineering atualizando configuração
        When: Atualiza configuração
        Then: Mudança é registrada no log de auditoria
        """
        import logging

        mock_role_manager.get_current_role = Mock(return_value="engineering")
        mock_role_manager.has_permission = Mock(return_value=True)
        mock_auth_service.authenticate = Mock(return_value=True)

        # Configura estado inicial
        mock_config_manager.set_require_login_on_startup(True)
        mock_config_manager.set_default_role("operator")

        with caplog.at_level(logging.INFO):
            auth_config_manager.update_config(
                require_login=False,
                default_role="engineering",
                confirming_user="eng",
                password="eng123"
            )

        # Verifica se log de auditoria foi criado
        assert any("AUDIT" in record.message for record in caplog.records)
        assert any("eng" in record.message for record in caplog.records)


# ==============================================================================
# Testes: Backward Compatibility
# ==============================================================================

class TestBackwardCompatibility:
    """Testa compatibilidade com versões anteriores."""

    def test_works_when_authentication_section_missing(self, auth_config_manager, mock_config_manager):
        """
        Testa que funciona quando seção authentication não existe.

        Given: Arquivo de config sem seção 'authentication'
        When: Lê configuração
        Then: Retorna valores padrão sem erro
        """
        # Remove seção authentication se existir
        if "authentication" in mock_config_manager.data:
            del mock_config_manager.data["authentication"]

        config = auth_config_manager.get_current_config()

        assert config['require_login_on_startup'] is True  # Default
        assert config['default_role'] == 'operator'  # Default

    def test_creates_section_with_defaults_on_first_update(
        self,
        auth_config_manager,
        mock_config_manager,
        mock_auth_service,
        mock_role_manager
    ):
        """
        Testa que cria seção com defaults na primeira atualização.

        Given: Arquivo de config sem seção 'authentication'
        When: Atualiza configuração pela primeira vez
        Then: Seção é criada com valores atualizados
        """
        # Remove seção authentication
        if "authentication" in mock_config_manager.data:
            del mock_config_manager.data["authentication"]

        mock_role_manager.get_current_role = Mock(return_value="engineering")
        mock_role_manager.has_permission = Mock(return_value=True)
        mock_auth_service.authenticate = Mock(return_value=True)

        auth_config_manager.update_config(
            require_login=False,
            default_role="engineering",
            confirming_user="eng",
            password="eng123"
        )

        # Verifica que seção foi criada
        assert "authentication" in mock_config_manager.data
        assert mock_config_manager.get_require_login_on_startup() is False
        assert mock_config_manager.get_default_role() == "engineering"
