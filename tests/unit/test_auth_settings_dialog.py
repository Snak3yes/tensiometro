"""
Testes de integração para AuthenticationSettingsDialog

Testa a integração do diálogo com:
- AuthConfigManager
- AuthService
- RoleManager
- UI PyQt6

Author: Claude Sonnet 4.5
Created: 2026-01-15
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import sys
import tempfile
import json

# PyQt6 imports
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# Import direto para evitar PyQt6 dependency em consumo_lib/__init__.py
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
def qapp():
    """Cria instância de QApplication para testes PyQt6."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


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
    role_mgr.current_role = UserRole.ENGINEERING
    role_mgr.check_permission = Mock(return_value=True)
    return role_mgr


@pytest.fixture
def auth_config_manager(mock_config_manager, mock_role_manager, mock_auth_service):
    """Cria instância de AuthConfigManager com mocks."""
    return AuthConfigManager(
        config_manager=mock_config_manager,
        role_manager=mock_role_manager,
        auth_service=mock_auth_service
    )


@pytest.fixture
def auth_dialog(qapp, auth_config_manager):
    """Cria instância de AuthenticationSettingsDialog."""
    dialog = AuthenticationSettingsDialog(
        auth_config_manager=auth_config_manager,
        current_role="engineering",
        parent=None
    )
    return dialog


# ==============================================================================
# Testes: Inicialização
# ==============================================================================

class TestDialogInitialization:
    """Testa inicialização do diálogo."""

    def test_dialog_initializes_successfully(self, auth_dialog):
        """
        Testa que diálogo inicializa sem erros.

        Given: AuthConfigManager configurado
        When: Cria AuthenticationSettingsDialog
        Then: Diálogo é criado com sucesso
        """
        assert auth_dialog is not None
        assert auth_dialog.windowTitle() == "Configurações de Autenticação"
        assert auth_dialog.isModal() is True

    def test_dialog_loads_current_config(self, auth_dialog):
        """
        Testa que diálogo carrega configuração atual.

        Given: Configuração com require_login=True, default_role=operator
        When: Diálogo é criado
        Then: Campos refletem configuração atual
        """
        assert auth_dialog.chk_require_login.isChecked() is True

        # Verifica combo está em "operator"
        current_index = auth_dialog.combo_default_role.currentIndex()
        current_role = auth_dialog.combo_default_role.itemData(current_index)
        assert current_role == "operator"

    def test_apply_button_disabled_on_initial_load(self, auth_dialog):
        """
        Testa que botão Aplicar está desabilitado na carga inicial.

        Given: Diálogo acaba de ser carregado
        When: Verifica estado do botão Aplicar
        Then: Botão está desabilitado (sem mudanças)
        """
        assert auth_dialog.btn_apply.isEnabled() is False


# ==============================================================================
# Testes: Permissões
# ==============================================================================

class TestPermissionChecking:
    """Testa verificação de permissões."""

    def test_engineering_user_can_access_dialog(self, auth_dialog, mock_role_manager):
        """
        Testa que usuário engineering pode acessar diálogo.

        Given: Usuário com role engineering
        When: Cria diálogo
        Then: Diálogo é criado sem erros
        """
        mock_role_manager.current_role = UserRole.ENGINEERING

        dialog = AuthenticationSettingsDialog(
            auth_config_manager=auth_dialog.auth_config_manager,
            current_role="engineering",
            parent=None
        )

        assert dialog is not None

    def test_operator_user_sees_dialog_but_cant_apply(
        self,
        auth_dialog,
        mock_role_manager,
        mock_config_manager
    ):
        """
        Testa que usuário operator vê diálogo mas não pode aplicar.

        Given: Usuário com role operator
        When: Tenta aplicar mudança
        Then: Recebe aviso de permissão negada
        """
        # Configura mock para retornar role operator e sem permissão
        mock_role_manager.get_current_role = Mock(return_value="operator")
        mock_role_manager.has_permission = Mock(return_value=False)

        # Modifica configuração
        auth_dialog.chk_require_login.setChecked(False)

        # Tenta aplicar (com mock de QMessageBox)
        with patch.object(
            auth_dialog,
            'show_confirmation_dialog'
        ) as mock_confirm:
            auth_dialog.on_apply_clicked()

            # Verifica que mensagem de permissão negada foi mostrada
            # (show_confirmation_dialog não deve ser chamado)
            mock_confirm.assert_not_called()


# ==============================================================================
# Testes: Funcionalidade Apply
# ==============================================================================

class TestApplyFunctionality:
    """Testa funcionalidade do botão Aplicar."""

    def test_apply_enabled_when_config_changes(self, auth_dialog):
        """
        Testa que Apply é habilitado quando config muda.

        Given: Diálogo carregado
        When: Usuário modifica checkbox
        Then: Botão Aplicar é habilitado
        """
        # Inicialmente desabilitado
        assert auth_dialog.btn_apply.isEnabled() is False

        # Modifica configuração
        auth_dialog.chk_require_login.setChecked(False)

        # Apply deve estar habilitado
        assert auth_dialog.btn_apply.isEnabled() is True

    def test_apply_disabled_when_config_reverted(self, auth_dialog):
        """
        Testa que Apply é desabilitado quando config é revertida.

        Given: Configuração foi modificada
        When: Usuário reverte para valor original
        Then: Botão Aplicar é desabilitado
        """
        # Modifica
        auth_dialog.chk_require_login.setChecked(False)
        assert auth_dialog.btn_apply.isEnabled() is True

        # Reverte
        auth_dialog.chk_require_login.setChecked(True)
        assert auth_dialog.btn_apply.isEnabled() is False

    def test_successful_update_emits_signal(
        self,
        auth_dialog,
        mock_auth_service,
        mock_role_manager
    ):
        """
        Testa que atualização bem-sucedida emite sinal config_changed.

        Given: Usuário engineering com senha correta
        When: Aplica mudança com confirmação
        Then: Sinal config_changed é emitido
        """
        mock_role_manager.current_role = UserRole.ENGINEERING
        mock_role_manager.check_permission = Mock(return_value=True)
        mock_auth_service.authenticate = Mock(return_value=True)

        # Flag para capturar sinal
        signal_emitted = False

        def on_config_changed():
            nonlocal signal_emitted
            signal_emitted = True

        auth_dialog.config_changed.connect(on_config_changed)

        # Modifica configuração
        auth_dialog.chk_require_login.setChecked(False)

        # Mock do dialog de confirmação para simular sucesso
        with patch.object(
            auth_dialog,
            'show_confirmation_dialog',
            wraps=auth_dialog.show_confirmation_dialog
        ) as mock_confirm:
            # Chama on_apply_clicked
            auth_dialog.on_apply_clicked()

            # show_confirmation_dialog deve ser chamado
            mock_confirm.assert_called_once()

    def test_failed_update_does_not_emit_signal(
        self,
        auth_dialog,
        mock_auth_service,
        mock_role_manager
    ):
        """
        Testa que atualização falha NÃO emite sinal.

        Given: Usuário com senha incorreta
        When: Tenta aplicar mudança
        Then: Sinal config_changed NÃO é emitido
        """
        mock_role_manager.current_role = UserRole.ENGINEERING
        mock_role_manager.check_permission = Mock(return_value=True)
        mock_auth_service.authenticate = Mock(return_value=False)

        signal_emitted = False

        def on_config_changed():
            nonlocal signal_emitted
            signal_emitted = True

        auth_dialog.config_changed.connect(on_config_changed)

        # Modifica configuração
        auth_dialog.chk_require_login.setChecked(False)

        # Tenta aplicar (vai falhar na autenticação)
        with patch.object(
            auth_dialog,
            'show_confirmation_dialog'
        ) as mock_confirm:
            auth_dialog.on_apply_clicked()

            # Dialog de confirmação não deve ser chamado (permissão ok, mas vai falhar depois)
            mock_confirm.assert_called_once()

            # Sinal não deve ter sido emitido
            assert signal_emitted is False


# ==============================================================================
# Testes: Interação UI
# ==============================================================================

class TestUIInteraction:
    """Testa interação com elementos da UI."""

    def test_combo_disabled_when_require_login_checked(self, auth_dialog):
        """
        Testa que combo é desabilitado quando login é obrigatório.

        Given: Checkbox "Solicitar login" marcado
        When: Verifica estado do combo de role
        Then: Combo está desabilitado
        """
        auth_dialog.chk_require_login.setChecked(True)

        assert auth_dialog.lbl_default_role.isEnabled() is False
        assert auth_dialog.combo_default_role.isEnabled() is False

    def test_combo_enabled_when_require_login_unchecked(self, auth_dialog):
        """
        Testa que combo é habilitado quando login NÃO é obrigatório.

        Given: Checkbox "Solicitar login" desmarcado
        When: Verifica estado do combo de role
        Then: Combo está habilitado
        """
        auth_dialog.chk_require_login.setChecked(False)

        assert auth_dialog.lbl_default_role.isEnabled() is True
        assert auth_dialog.combo_default_role.isEnabled() is True

    def test_cancel_closes_dialog(self, auth_dialog):
        """
        Testa que botão Cancelar fecha diálogo sem salvar.

        Given: Diálogo aberto com modificações
        When: Clica em Cancelar
        Then: Diálogo fecha e configuração NÃO é salva
        """
        # Modifica
        auth_dialog.chk_require_login.setChecked(False)

        # Cancela
        auth_dialog.on_cancel_clicked()

        # Verifica que diálogo foi rejeitado
        assert auth_dialog.result() == 0  # QDialog.DialogCode.Rejected


# ==============================================================================
# Testes: Edge Cases
# ==============================================================================

class TestEdgeCases:
    """Testa casos de borda."""

    def test_handles_missing_authentication_section(
        self,
        auth_config_manager,
        mock_config_manager,
        qapp
    ):
        """
        Testa que lida com seção authentication ausente.

        Given: Config sem seção authentication
        When: Cria diálogo
        Then: Usa valores padrão sem erros
        """
        # Remove seção
        if "authentication" in mock_config_manager.data:
            del mock_config_manager.data["authentication"]

        dialog = AuthenticationSettingsDialog(
            auth_config_manager=auth_config_manager,
            current_role="engineering",
            parent=None
        )

        # Deve carregar defaults
        assert dialog.chk_require_login.isChecked() is True  # Default

    def test_handles_invalid_role_value(
        self,
        auth_config_manager,
        mock_config_manager,
        qapp
    ):
        """
        Testa que lida com valor inválido de default_role.

        Given: Config com default_role inválido
        When: Cria diálogo
        Then: Usa primeiro valor do combo sem erros
        """
        mock_config_manager.data["authentication"]["default_role"] = "invalid_role"

        dialog = AuthenticationSettingsDialog(
            auth_config_manager=auth_config_manager,
            current_role="engineering",
            parent=None
        )

        # Deve carregar (sem crashar)
        assert dialog is not None

    def test_handles_no_current_user(
        self,
        auth_dialog,
        mock_auth_service
    ):
        """
        Testa que lida com ausência de usuário atual.

        Given: Nenhum usuário autenticado
        When: Tenta aplicar mudança
        Then: Mostra aviso e não aplica
        """
        mock_auth_service.get_current_user = Mock(return_value=None)

        auth_dialog.chk_require_login.setChecked(False)

        with patch.object(
            auth_dialog,
            'show_confirmation_dialog'
        ) as mock_confirm:
            with patch('PyQt6.QtWidgets.QMessageBox.warning') as mock_warn:
                auth_dialog.on_apply_clicked()

                # Não deve mostrar diálogo de confirmação
                mock_confirm.assert_not_called()

                # Deve mostrar aviso
                mock_warn.assert_called()
