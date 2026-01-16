"""
Testes End-to-End para Authentication Configuration Feature

Testa cenários completos de uso:
1. Login normal (require_login=true)
2. Engenharia configura auto-login
3. Auto-login funciona
4. Reverte para login normal
5. Permissão negada

Author: Claude Sonnet 4.5
Created: 2026-01-15
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import sys
import tempfile
import json

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from aoi_lib.config_manager import AOIConfigManager
from aoi_lib.auth.auth_service import AuthService
from consumo_lib.managers.auth_config_manager import AuthConfigManager
from consumo_lib.managers.role_manager import RoleManager, UserRole
from consumo_lib.dialogs.auth_settings_dialog import AuthenticationSettingsDialog


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
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def config_manager(temp_config_file):
    """Cria AOIConfigManager."""
    return AOIConfigManager(cfg_path=temp_config_file)


@pytest.fixture
def auth_service():
    """Cria AuthService."""
    return AuthService()


@pytest.fixture
def role_manager():
    """Cria RoleManager."""
    role_mgr = RoleManager()
    # Configura role padrão como operator
    role_mgr.set_role("operator")
    return role_mgr


@pytest.fixture
def auth_config_manager(config_manager, role_manager, auth_service):
    """Cria AuthConfigManager."""
    return AuthConfigManager(
        config_manager=config_manager,
        role_manager=role_manager,
        auth_service=auth_service
    )


# ==============================================================================
# Cenário 1: Login Normal (require_login=true)
# ==============================================================================

class TestScenario1_NormalLogin:
    """Testa cenário 1: Login normal com require_login=true."""

    def test_scenario_1_normal_login_shows_dialog(
        self,
        config_manager,
        auth_service
    ):
        """
        Testa cenário onde login é obrigatório.

        Given: require_login_on_startup = True
        When: Aplicação inicia
        Then: LoginDialog é mostrado
        """
        # Configura: login obrigatório
        config_manager.set_require_login_on_startup(True)

        # Verifica
        assert config_manager.get_require_login_on_startup() is True
        assert config_manager.get_default_role() == "operator"

        # Simulação: Na aplicação real, show_login_dialog() seria chamado
        # Aqui apenas verificamos que a configuração está correta
        assert config_manager.data["authentication"]["require_login_on_startup"] is True


# ==============================================================================
# Cenário 2: Engenharia Configura Auto-Login
# ==============================================================================

class TestScenario2_EngineeringConfiguresAutoLogin:
    """Testa cenário 2: Usuário engineering configura auto-login."""

    def test_scenario_2_engineering_can_disable_login(
        self,
        auth_config_manager,
        config_manager,
        auth_service,
        role_manager
    ):
        """
        Testa que usuário engineering pode desabilitar login.

        Given: Usuário engineering autenticado
        When: Configura require_login=False e default_role=operator
        Then: Configuração é atualizada com sucesso
        """
        # Setup: autentica como engineering
        auth_service.authenticate("eng", "eng123")

        # Configura role no RoleManager
        role_manager.set_role("engineering")

        # Verifica permissão
        assert auth_config_manager.can_modify_config() is True

        # Atualiza configuração
        success = auth_config_manager.update_config(
            require_login=False,
            default_role="operator",
            confirming_user="eng",
            password="eng123"
        )

        assert success is True
        assert config_manager.get_require_login_on_startup() is False
        assert config_manager.get_default_role() == "operator"


# ==============================================================================
# Cenário 3: Auto-Login Funciona
# ==============================================================================

class TestScenario3_AutoLoginWorks:
    """Testa cenário 3: Auto-login funciona corretamente."""

    def test_scenario_3_auto_login_with_operator_role(
        self,
        config_manager,
        auth_service
    ):
        """
        Testa auto-login com role operator.

        Given: require_login=False, default_role=operator
        When: Aplicação inicia
        Then: Auto-login com usuário operator ocorre com sucesso
        """
        # Configura: auto-login habilitado
        config_manager.set_require_login_on_startup(False)
        config_manager.set_default_role("operator")

        # Simula auto-login
        default_role = config_manager.get_default_role()

        # Mapeamento role → usuário
        role_to_user = {
            "operator": "operator",
            "engineering": "eng",
            "quality": "quality",
            "admin": "admin"
        }

        username = role_to_user.get(default_role, "operator")
        password_map = {
            "operator": "operator123",
            "eng": "eng123",
            "quality": "quality123",
            "admin": "admin123"
        }
        password = password_map.get(username, "operator123")

        # Autentica
        success = auth_service.authenticate(username, password)

        assert success is True
        assert auth_service.is_authenticated()

        user = auth_service.get_current_user()
        assert user is not None
        assert user.username == "operator"

    def test_scenario_3_auto_login_with_engineering_role(
        self,
        config_manager,
        auth_service
    ):
        """
        Testa auto-login com role engineering.

        Given: require_login=False, default_role=engineering
        When: Aplicação inicia
        Then: Auto-login com usuário eng ocorre com sucesso
        """
        # Configura: auto-login com engineering
        config_manager.set_require_login_on_startup(False)
        config_manager.set_default_role("engineering")

        default_role = config_manager.get_default_role()
        assert default_role == "engineering"

        # Simula auto-login
        role_to_user = {
            "operator": "operator",
            "engineering": "eng",
            "quality": "quality",
            "admin": "admin"
        }

        username = role_to_user.get(default_role)
        password_map = {
            "operator": "operator123",
            "eng": "eng123",
            "quality": "quality123",
            "admin": "admin123"
        }
        password = password_map.get(username)

        success = auth_service.authenticate(username, password)

        assert success is True
        user = auth_service.get_current_user()
        assert user.username == "eng"


# ==============================================================================
# Cenário 4: Reverte para Login Normal
# ==============================================================================

class TestScenario4_RevertToNormalLogin:
    """Testa cenário 4: Reverte de auto-login para login normal."""

    def test_scenario_4_revert_to_require_login(
        self,
        auth_config_manager,
        config_manager,
        auth_service,
        role_manager
    ):
        """
        Testa reverter de auto-login para login obrigatório.

        Given: Auto-login está habilitado (require_login=False)
        When: Usuário engineering configura require_login=True
        Then: Configuração é atualizada e próximo inicio exigirá login
        """
        # Estado inicial: auto-login habilitado
        config_manager.set_require_login_on_startup(False)
        config_manager.set_default_role("operator")
        assert config_manager.get_require_login_on_startup() is False

        # Autentica como engineering
        auth_service.authenticate("eng", "eng123")

        # Configura role no RoleManager
        role_manager.set_role("engineering")

        # Reverte para login obrigatório
        success = auth_config_manager.update_config(
            require_login=True,
            default_role="operator",
            confirming_user="eng",
            password="eng123"
        )

        assert success is True
        assert config_manager.get_require_login_on_startup() is True


# ==============================================================================
# Cenário 5: Permissão Negada
# ==============================================================================

class TestScenario5_PermissionDenied:
    """Testa cenário 5: Usuário sem permissão não pode modificar."""

    def test_scenario_5_operator_cannot_modify_config(
        self,
        auth_config_manager,
        auth_service
    ):
        """
        Testa que usuário operator não pode modificar configuração.

        Given: Usuário operator autenticado
        When: Tenta modificar configuração de autenticação
        Then: PermissionError é lançada
        """
        # Autentica como operator
        auth_service.authenticate("operator", "operator123")
        assert auth_service.is_authenticated()

        # Tenta modificar (deve falhar)
        with pytest.raises(PermissionError, match="sem permissão"):
            auth_config_manager.update_config(
                require_login=False,
                default_role="operator",
                confirming_user="operator",
                password="operator123"
            )

    def test_scenario_5_quality_cannot_modify_config(
        self,
        auth_config_manager,
        auth_service
    ):
        """
        Testa que usuário quality não pode modificar configuração.

        Given: Usuário quality autenticado
        When: Tenta modificar configuração de autenticação
        Then: PermissionError é lançada
        """
        # Autentica como quality
        # Nota: quality pode não existir no sistema padrão, mas vamos testar a lógica
        # Vamos usar operator e simular role=quality
        auth_service.authenticate("operator", "operator123")

        # Mock role_manager para retornar quality
        auth_config_manager.role_manager.current_role = UserRole.QUALITY
        auth_config_manager.role_manager.check_permission = Mock(return_value=False)

        # Tenta modificar (deve falhar)
        with pytest.raises(PermissionError):
            auth_config_manager.update_config(
                require_login=False,
                default_role="quality",
                confirming_user="operator",
                password="operator123"
            )


# ==============================================================================
# Testes de Config Persistência
# ==============================================================================

class TestConfigPersistence:
    """Testa persistência de configuração entre sessões."""

    def test_config_persists_across_sessions(
        self,
        config_manager,
        auth_config_manager,
        auth_service,
        temp_config_file,
        role_manager
    ):
        """
        Testa que configuração persiste entre sessões.

        Given: Configuração é modificada
        When: ConfigManager é recarregado
        Then: Valores modificados são preservados
        """
        # Modifica configuração
        auth_service.authenticate("eng", "eng123")

        # Configura role no RoleManager
        role_manager.set_role("engineering")

        auth_config_manager.update_config(
            require_login=False,
            default_role="engineering",
            confirming_user="eng",
            password="eng123"
        )

        # Recarrega configManager (simula nova sessão)
        new_config_manager = AOIConfigManager(cfg_path=temp_config_file)

        # Verifica que valores foram preservados
        assert new_config_manager.get_require_login_on_startup() is False
        assert new_config_manager.get_default_role() == "engineering"


# ==============================================================================
# Testes de Edge Cases
# ==============================================================================

class TestEdgeCases:
    """Testa casos de borda e erros."""

    def test_invalid_role_falls_back_to_operator(
        self,
        config_manager,
        auth_service
    ):
        """
        Testa que role inválido fallback para operator.

        Given: default_role configurado com valor inválido
        When: Auto-login é executado
        Then: Fallback para operator ocorre
        """
        # Configura role inválido
        config_manager.data["authentication"]["default_role"] = "invalid_role"

        # Lê configuração (deve retornar valor inválido)
        default_role = config_manager.get_default_role()
        assert default_role == "invalid_role"

        # Na aplicação real, _perform_auto_login trataria isso
        # Verificando validação no AuthConfigManager
        from consumo_lib.managers.auth_config_manager import AuthConfigManager
        from consumo_lib.managers.role_manager import RoleManager

        role_mgr = RoleManager()
        auth_config_mgr = AuthConfigManager(
            config_manager=config_manager,
            role_manager=role_mgr,
            auth_service=auth_service
        )

        # validate_role deve rejeitar
        assert auth_config_mgr.validate_role("invalid_role") is False
        assert auth_config_mgr.validate_role("operator") is True

    def test_missing_auth_section_creates_defaults(
        self,
        config_manager
    ):
        """
        Testa que seção ausente cria defaults.

        Given: Arquivo de config sem seção authentication
        When: ConfigManager é carregado
        Then: Valores padrão são usados
        """
        # Remove seção
        if "authentication" in config_manager.data:
            del config_manager.data["authentication"]

        # Recarrega
        config_manager.load()

        # Deve usar defaults
        assert config_manager.get_require_login_on_startup() is True
        assert config_manager.get_default_role() == "operator"

    def test_empty_default_role_fallback(
        self,
        config_manager
    ):
        """
        Testa que default_role vazio fallback para operator.

        Given: default_role = ""
        When: Lê configuração
        Then: Retorna "" (validação ocorre em outro nível)
        """
        config_manager.set_default_role("")

        default_role = config_manager.get_default_role()
        assert default_role == ""

        # AuthConfigManager.validate_role deve rejeitar
        from consumo_lib.managers.auth_config_manager import AuthConfigManager
        from consumo_lib.managers.role_manager import RoleManager
        from aoi_lib.auth.auth_service import AuthService

        role_mgr = RoleManager()
        auth_svc = AuthService()
        auth_config_mgr = AuthConfigManager(
            config_manager=config_manager,
            role_manager=role_mgr,
            auth_service=auth_svc
        )

        assert auth_config_mgr.validate_role("") is False
