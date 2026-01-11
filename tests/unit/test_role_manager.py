"""
Testes Unitários para RoleManager

Testa o RoleManager de forma isolada, focando em:
- Criação e configuração de roles
- Verificação de permissões
- Validação de acessos
- Mudança de roles
"""

import pytest
from consumo_lib.managers.role_manager import (
    RoleManager,
    UserRole,
    PermissionDeniedError
)


class TestRoleManagerCreation:
    """Testa criação e inicialização do RoleManager."""

    def test_default_role_is_operator(self):
        """RoleManager deve ter role padrão 'operator'."""
        manager = RoleManager()

        assert manager.get_current_role() == "operator"

    def test_initial_operator_id_is_none(self):
        """Operator ID deve ser None inicialmente."""
        manager = RoleManager()

        assert manager.get_operator_id() is None

    def test_create_with_all_roles(self):
        """Todas as 4 roles devem estar disponíveis."""
        manager = RoleManager()

        available = manager.get_available_roles()

        assert len(available) == 4
        assert "operator" in available
        assert "engineering" in available
        assert "quality" in available
        assert "admin" in available


class TestRoleConfiguration:
    """Testa configuração de roles."""

    def test_set_role_to_engineering(self):
        """Deve conseguir mudar role para engineering."""
        manager = RoleManager()

        result = manager.set_role("engineering")

        assert result is True
        assert manager.get_current_role() == "engineering"

    def test_set_role_to_quality(self):
        """Deve conseguir mudar role para quality."""
        manager = RoleManager()

        result = manager.set_role("quality")

        assert result is True
        assert manager.get_current_role() == "quality"

    def test_set_role_to_admin(self):
        """Deve conseguir mudar role para admin."""
        manager = RoleManager()

        result = manager.set_role("admin")

        assert result is True
        assert manager.get_current_role() == "admin"

    def test_set_invalid_role_returns_false(self):
        """Deve retornar False para role inválida."""
        manager = RoleManager()

        result = manager.set_role("invalid_role")

        assert result is False
        # Role deve permanecer operator
        assert manager.get_current_role() == "operator"

    def test_set_operator_id(self):
        """Deve conseguir definir operator ID."""
        manager = RoleManager()

        manager.set_operator_id("OP-001")

        assert manager.get_operator_id() == "OP-001"


class TestPermissionChecking:
    """Testa verificação de permissões."""

    def test_operator_can_execute_inspection(self):
        """Operator deve ter permissão para executar inspeção."""
        manager = RoleManager()
        manager.set_role("operator")

        assert manager.has_permission("inspection.execute") is True

    def test_operator_cannot_access_engineering_settings(self):
        """Operator NÃO deve ter permissão para configurações de engenharia."""
        manager = RoleManager()
        manager.set_role("operator")

        assert manager.has_permission("settings.engineering") is False

    def test_engineering_can_access_engineering_settings(self):
        """Engineering DEVE ter permissão para configurações de engenharia."""
        manager = RoleManager()
        manager.set_role("engineering")

        assert manager.has_permission("settings.engineering") is True

    def test_engineering_can_manage_recipes(self):
        """Engineering deve ter permissão para gerenciar receitas."""
        manager = RoleManager()
        manager.set_role("engineering")

        assert manager.has_permission("recipe.edit") is True
        assert manager.can_manage_recipes() is True

    def test_operator_cannot_manage_recipes(self):
        """Operator NÃO deve ter permissão para gerenciar receitas."""
        manager = RoleManager()
        manager.set_role("operator")

        assert manager.has_permission("recipe.edit") is False
        assert manager.can_manage_recipes() is False

    def test_admin_has_all_permissions(self):
        """Admin deve ter todas as permissões verificadas."""
        manager = RoleManager()
        manager.set_role("admin")

        # Verifica algumas permissões críticas
        assert manager.has_permission("inspection.execute") is True
        assert manager.has_permission("settings.engineering") is True
        assert manager.has_permission("recipe.edit") is True
        assert manager.has_permission("user.manage") is True

    def test_quality_can_generate_reports(self):
        """Quality deve ter permissão para gerar relatórios."""
        manager = RoleManager()
        manager.set_role("quality")

        assert manager.has_permission("report.generate") is True
        assert manager.has_permission("report.export") is True

    def test_check_permission_raises_on_denied(self):
        """check_permission deve levantar exceção quando permissão negada."""
        manager = RoleManager()
        manager.set_role("operator")

        with pytest.raises(PermissionDeniedError) as exc_info:
            manager.check_permission("settings.engineering")

        assert "permissão" in str(exc_info.value).lower()

    def test_check_permission_returns_true_when_granted(self):
        """check_permission deve retornar True quando permitido."""
        manager = RoleManager()
        manager.set_role("engineering")

        result = manager.check_permission("settings.engineering")

        assert result is True


class TestPermissionMethods:
    """Testa métodos de conveniência para permissões."""

    def test_can_view_advanced_controls_for_engineering(self):
        """Engineering deve ver controles avançados."""
        manager = RoleManager()
        manager.set_role("engineering")

        assert manager.can_view_advanced_controls() is True

    def test_cannot_view_advanced_controls_for_operator(self):
        """Operator NÃO deve ver controles avançados."""
        manager = RoleManager()
        manager.set_role("operator")

        assert manager.can_view_advanced_controls() is False

    def test_quality_can_view_advanced_controls(self):
        """Quality deve ver controles avançados."""
        manager = RoleManager()
        manager.set_role("quality")

        assert manager.can_view_advanced_controls() is True

    def test_can_execute_inspection_for_all_roles(self):
        """Todas as roles devem conseguir executar inspeção."""
        manager = RoleManager()

        for role in ["operator", "engineering", "quality", "admin"]:
            manager.set_role(role)
            assert manager.can_execute_inspection(), f"{role} deve executar inspeção"


class TestPermissionLists:
    """Testa listagem de permissões."""

    def test_get_all_permissions_for_operator(self):
        """Deve retornar lista de permissões do operator."""
        manager = RoleManager()

        permissions = manager.get_all_permissions_for_role("operator")

        assert len(permissions) > 0
        assert "inspection.execute" in permissions
        assert "stencil.select" in permissions
        # Não deve ter permissões de engenharia
        assert "settings.engineering" not in permissions

    def test_get_all_permissions_for_engineering(self):
        """Deve retornar lista de permissões do engineering."""
        manager = RoleManager()

        permissions = manager.get_all_permissions_for_role("engineering")

        assert len(permissions) > 0
        # Engineering deve ter muito mais permissões que operator
        operator_perms = manager.get_all_permissions_for_role("operator")
        assert len(permissions) > len(operator_perms)

    def test_get_all_permissions_for_invalid_role(self):
        """Deve retornar lista vazia para role inválida."""
        manager = RoleManager()

        permissions = manager.get_all_permissions_for_role("invalid")

        assert len(permissions) == 0


class TestSignalEmission:
    """Testa emissão de signals."""

    def test_role_changed_signal_emitted_on_set_role(self):
        """Signal role_changed deve ser emitido ao mudar role."""
        manager = RoleManager()

        # Captura signals emitidos
        emitted_roles = []

        def capture_role(new_role):
            emitted_roles.append(new_role)

        manager.role_changed.connect(capture_role)

        # Muda role
        manager.set_role("engineering")

        assert len(emitted_roles) == 1
        assert emitted_roles[0] == "engineering"

    def test_permission_denied_signal_emitted(self):
        """Signal permission_denied deve ser emitido ao negar permissão."""
        manager = RoleManager()
        manager.set_role("operator")

        # Captura signals emitidos
        denied_permissions = []

        def capture_denied(permission):
            denied_permissions.append(permission)

        manager.permission_denied.connect(capture_denied)

        # Tenta acessar permissão negada
        manager.has_permission("settings.engineering")

        assert len(denied_permissions) == 1
        assert denied_permissions[0] == "settings.engineering"
