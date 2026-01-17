"""
Testes unitários para integração de navegação livre no AuthConfigManager.

Este módulo testa os métodos de gerenciamento de configuração de navegação livre
com controle de acesso e auditoria.

Autor: Claude Code (Sonnet 4.5)
Data: 2026-01-17
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from consumo_lib.managers.auth_config_manager import AuthConfigManager
from aoi_lib.auth.auth_service import AuthService
from consumo_lib.managers.role_manager import RoleManager, UserRole


class TestFreeNavigationAuthConfig:
    """Testes para gerenciamento de navegação livre no AuthConfigManager."""

    def test_get_free_navigation_enabled_wrapper(self):
        """
        Testa get_free_navigation_enabled() como wrapper de config_manager.
        """
        # Arrange: Criar mocks
        mock_config_mgr = Mock()
        mock_config_mgr.get_free_navigation_enabled = Mock(return_value=True)
        mock_role_mgr = Mock()
        mock_auth_svc = Mock()

        # Act: Criar AuthConfigManager e chamar método
        auth_config = AuthConfigManager(mock_config_mgr, mock_role_mgr, mock_auth_svc)
        result = auth_config.get_free_navigation_enabled()

        # Assert: Deve chamar config_manager e retornar valor
        mock_config_mgr.get_free_navigation_enabled.assert_called_once()
        assert result is True, "Deve retornar True do config_manager"

    def test_set_free_navigation_enabled_with_password(self):
        """
        Testa set_free_navigation_enabled() com senha correta.
        """
        # Arrange: Criar mocks
        mock_config_mgr = Mock()
        mock_role_mgr = Mock()
        mock_role_mgr.has_permission = Mock(return_value=True)
        mock_auth_svc = Mock()
        mock_user = Mock()
        mock_user.username = "eng"
        mock_auth_svc.get_current_user = Mock(return_value=mock_user)
        mock_auth_svc.authenticate = Mock(return_value=True)

        # Act: Criar AuthConfigManager e chamar método
        auth_config = AuthConfigManager(mock_config_mgr, mock_role_mgr, mock_auth_svc)
        result = auth_config.set_free_navigation_enabled(
            enabled=True,
            confirming_user="eng",
            password="eng123"
        )

        # Assert: Deve atualizar configuração
        assert result is True, "Deve retornar True em sucesso"
        mock_config_mgr.set_free_navigation_enabled.assert_called_once_with(True)
        mock_auth_svc.authenticate.assert_called_once_with("eng", "eng123")

    def test_set_free_navigation_enabled_audit_logging(self):
        """
        Testa se set_free_navigation_enabled() gera log de auditoria.
        """
        # Arrange: Criar mocks com logger capturado
        mock_config_mgr = Mock()
        mock_config_mgr.get_free_navigation_enabled = Mock(return_value=False)
        mock_role_mgr = Mock()
        mock_role_mgr.has_permission = Mock(return_value=True)
        mock_auth_svc = Mock()
        mock_user = Mock()
        mock_user.username = "eng"
        mock_auth_svc.get_current_user = Mock(return_value=mock_user)
        mock_auth_svc.authenticate = Mock(return_value=True)

        # Act: Chamar método e capturar log
        with patch('consumo_lib.managers.auth_config_manager.logger') as mock_logger:
            auth_config = AuthConfigManager(mock_config_mgr, mock_role_mgr, mock_auth_svc)
            auth_config.set_free_navigation_enabled(
                enabled=True,
                confirming_user="eng",
                password="eng123"
            )

            # Assert: Deve gerar log de auditoria
            assert mock_logger.info.called, "Deve chamar logger.info para auditoria"
            log_calls = [str(call) for call in mock_logger.info.call_args_list]
            assert any("AUDIT" in call and "free_navigation" in call.lower() for call in log_calls), \
                "Log deve conter 'AUDIT' e 'free_navigation'"

    def test_set_free_navigation_enabled_permission_denied(self):
        """
        Testa se set_free_navigation_enabled() nega acesso sem permissão.
        """
        # Arrange: Criar mocks com usuário sem permissão
        mock_config_mgr = Mock()
        mock_role_mgr = Mock()
        mock_role_mgr.has_permission = Mock(return_value=False)  # Sem permissão
        mock_role_mgr.get_current_role = Mock(return_value=UserRole.OPERATOR)
        mock_auth_svc = Mock()
        mock_user = Mock()
        mock_user.username = "operator"
        mock_auth_svc.get_current_user = Mock(return_value=mock_user)

        # Act & Assert: Deve levantar PermissionError
        auth_config = AuthConfigManager(mock_config_mgr, mock_role_mgr, mock_auth_svc)
        with pytest.raises(PermissionError, match="sem permissão"):
            auth_config.set_free_navigation_enabled(
                enabled=True,
                confirming_user="operator",
                password="operator123"
            )

        # Assert: Não deve chamar set_free_navigation_enabled
        mock_config_mgr.set_free_navigation_enabled.assert_not_called()

    def test_set_free_navigation_enabled_wrong_password(self):
        """
        Testa se set_free_navigation_enabled() falha com senha errada.
        """
        # Arrange: Criar mocks com senha incorreta
        mock_config_mgr = Mock()
        mock_config_mgr.get_free_navigation_enabled = Mock(return_value=False)
        mock_role_mgr = Mock()
        mock_role_mgr.has_permission = Mock(return_value=True)  # Tem permissão
        mock_auth_svc = Mock()
        mock_user = Mock()
        mock_user.username = "eng"
        mock_auth_svc.get_current_user = Mock(return_value=mock_user)
        mock_auth_svc.authenticate = Mock(return_value=False)  # Senha incorreta

        # Act & Assert: Deve levantar ValueError
        auth_config = AuthConfigManager(mock_config_mgr, mock_role_mgr, mock_auth_svc)
        with pytest.raises(ValueError, match="Senha incorreta"):
            auth_config.set_free_navigation_enabled(
                enabled=True,
                confirming_user="eng",
                password="wrong_password"
            )

        # Assert: Não deve chamar set_free_navigation_enabled
        mock_config_mgr.set_free_navigation_enabled.assert_not_called()
