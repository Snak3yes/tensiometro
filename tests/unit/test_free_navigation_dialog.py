"""
Testes de integração para o dialog de configurações de autenticação
com suporte a navegação livre do Engineering Wizard.

Autor: Claude Code (Sonnet 4.5)
Data: 2026-01-17
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from PyQt6.QtWidgets import QApplication
import sys

from consumo_lib.dialogs.auth_settings_dialog import AuthenticationSettingsDialog
from consumo_lib.managers.auth_config_manager import AuthConfigManager


@pytest.fixture
def qapp():
    """Cria QApplication para testes PyQt6."""
    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance()
    return app


class TestAuthenticationSettingsDialogFreeNavigation:
    """Testes para dialog de configurações com navegação livre."""

    def test_dialog_shows_free_navigation_checkbox(self, qapp):
        """
        Testa se checkbox de navegação livre é mostrada.
        """
        # Arrange
        mock_auth_config_mgr = Mock()
        mock_auth_config_mgr.get_current_config = Mock(return_value={
            'require_login_on_startup': False,
            'default_role': 'engineering',
            'free_navigation_enabled': False
        })
        mock_auth_config_mgr.can_modify_config = Mock(return_value=True)

        # Act
        dialog = AuthenticationSettingsDialog(
            mock_auth_config_mgr,
            current_role="engineering",
            parent=None
        )

        # Assert
        assert hasattr(dialog, 'chk_free_navigation'), "Dialog deve ter checkbox de navegação livre"
        assert dialog.chk_free_navigation is not None, "Checkbox deve ser criada"
        assert not dialog.chk_free_navigation.isChecked(), "Checkbox deve estar desmarcada por padrão"

    def test_dialog_loads_free_navigation_config(self, qapp):
        """
        Testa se dialog carrega configuração de navegação livre corretamente.
        """
        # Arrange
        mock_auth_config_mgr = Mock()
        mock_auth_config_mgr.get_current_config = Mock(return_value={
            'require_login_on_startup': False,
            'default_role': 'engineering',
            'free_navigation_enabled': True  # Habilitado
        })
        mock_auth_config_mgr.can_modify_config = Mock(return_value=True)

        # Act
        dialog = AuthenticationSettingsDialog(
            mock_auth_config_mgr,
            current_role="engineering",
            parent=None
        )

        # Assert
        assert dialog.chk_free_navigation.isChecked(), "Checkbox deve estar marcada quando config é True"

    def test_dialog_detects_free_navigation_changes(self, qapp):
        """
        Testa se dialog detecta mudanças na configuração de navegação livre.
        """
        # Arrange
        mock_auth_config_mgr = Mock()
        mock_auth_config_mgr.get_current_config = Mock(return_value={
            'require_login_on_startup': False,
            'default_role': 'engineering',
            'free_navigation_enabled': False
        })
        mock_auth_config_mgr.can_modify_config = Mock(return_value=True)

        dialog = AuthenticationSettingsDialog(
            mock_auth_config_mgr,
            current_role="engineering",
            parent=None
        )

        # Act: Mudar estado da checkbox
        dialog.chk_free_navigation.setChecked(True)

        # Assert: Botão Apply deve estar habilitado
        # Nota: on_config_changed() é chamado pelo signal stateChanged
        assert dialog.btn_apply.isEnabled(), "Botão Apply deve ser habilitado quando config muda"

    def test_dialog_saves_free_navigation_on_apply(self, qapp):
        """
        Testa se dialog salva configuração de navegação livre ao aplicar.
        """
        # Arrange
        mock_auth_config_mgr = Mock(spec=AuthConfigManager)
        mock_auth_config_mgr.get_current_config = Mock(return_value={
            'require_login_on_startup': False,
            'default_role': 'engineering',
            'free_navigation_enabled': False
        })
        mock_auth_config_mgr.can_modify_config = Mock(return_value=True)
        mock_auth_config_mgr.update_config = Mock(return_value=True)
        mock_auth_config_mgr.set_free_navigation_enabled = Mock(return_value=True)

        mock_user = Mock()
        mock_user.username = "eng"
        mock_auth_config_mgr.auth_service = Mock()
        mock_auth_config_mgr.auth_service.get_current_user = Mock(return_value=mock_user)

        dialog = AuthenticationSettingsDialog(
            mock_auth_config_mgr,
            current_role="engineering",
            parent=None
        )

        # Act: Mudar configuração e chamar on_apply_clicked
        dialog.chk_free_navigation.setChecked(True)

        with patch.object(dialog, 'show_confirmation_dialog') as mock_confirm:
            dialog.on_apply_clicked()

            # Assert: show_confirmation_dialog deve ser chamado com free_navigation=True
            mock_confirm.assert_called_once()
            args = mock_confirm.call_args[0]
            assert args[2] is True, "show_confirmation_dialog deve receber free_navigation=True"

    def test_dialog_role_based_visibility(self, qapp):
        """
        Testa se checkbox é visível para engineering+ (controle de acesso é no save, não na visibilidade).
        """
        # Arrange
        mock_auth_config_mgr = Mock()
        mock_auth_config_mgr.get_current_config = Mock(return_value={
            'require_login_on_startup': False,
            'default_role': 'operator',
            'free_navigation_enabled': False
        })
        mock_auth_config_mgr.can_modify_config = Mock(return_value=True)

        # Act: Criar dialog com role engineering
        dialog = AuthenticationSettingsDialog(
            mock_auth_config_mgr,
            current_role="engineering",
            parent=None
        )

        # Assert: Checkbox deve existir e estar habilitada (controle de acesso é no save, não visibilidade)
        assert dialog.chk_free_navigation is not None, "Checkbox deve existir"
        assert dialog.chk_free_navigation.isEnabled(), "Checkbox deve estar habilitada"
        # Nota: can_modify_config() é chamado em on_apply_clicked para bloquear save
