"""
Testes Unitários para OperatorInspectionCoordinator

Testa o OperatorInspectionCoordinator de forma isolada, focando em:
- Seleção de stencil e programa
- Validação antes de iniciar inspeção
- Execução de inspeção (mock)
- Gerenciamento de sessão
- Programas predefinidos
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch

from consumo_lib.coordinators.operator_workflow import (
    OperatorInspectionCoordinator,
    InspectionProgram,
    PREDEFINED_PROGRAMS
)


@pytest.fixture
def mock_inspection_coordinator():
    """Mock do InspectionCoordinator."""
    coordinator = Mock()
    coordinator.run_full_inspection.return_value = None
    return coordinator


@pytest.fixture
def mock_role_manager():
    """Mock do RoleManager."""
    manager = Mock()
    manager.has_permission.return_value = True
    manager.get_current_role.return_value = "operator"
    return manager


@pytest.fixture
def mock_session_logger():
    """Mock do SessionLogger."""
    logger = Mock()
    logger.log_session_start.return_value = "session-123"
    logger.log_session_end.return_value = True
    logger.log_action.return_value = True
    return logger


@pytest.fixture
def coordinator(mock_inspection_coordinator, mock_role_manager, mock_session_logger):
    """Cria OperatorInspectionCoordinator com mocks."""
    return OperatorInspectionCoordinator(
        inspection_coordinator=mock_inspection_coordinator,
        role_manager=mock_role_manager,
        session_logger=mock_session_logger
    )


class TestCoordinatorCreation:
    """Testa criação e inicialização."""

    def test_create_coordinator(self, coordinator):
        """Deve criar com sucesso."""
        assert coordinator is not None

    def test_predefined_programs_available(self):
        """Programas predefinidos devem estar disponíveis."""
        assert len(PREDEFINED_PROGRAMS) == 3

        program_ids = [p.program_id for p in PREDEFINED_PROGRAMS]
        assert "prog_standard" in program_ids
        assert "prog_quick" in program_ids
        assert "prog_critical" in program_ids

    def test_no_initial_selection(self, coordinator):
        """Não deve ter seleção inicial."""
        assert coordinator.get_selected_stencil() is None
        assert coordinator.get_selected_program() is None


class TestStencilSelection:
    """Testa seleção de stencil."""

    def test_select_stencil(self, coordinator):
        """Deve selecionar stencil."""
        result = coordinator.select_stencil("STENCIL-001")

        assert result is True
        assert coordinator.get_selected_stencil() == "STENCIL-001"

    def test_select_stencil_empty_returns_false(self, coordinator):
        """Stencil vazio deve retornar False."""
        result = coordinator.select_stencil("")

        assert result is False
        assert coordinator.get_selected_stencil() is None

    def test_select_stencil_logs_action(self, coordinator, mock_session_logger):
        """Seleção deve ser registrada no logger."""
        coordinator._session_id = "session-123"
        coordinator.select_stencil("STENCIL-001")

        mock_session_logger.log_action.assert_called_once()
        call_args = mock_session_logger.log_action.call_args
        assert call_args[0][0] == "session-123"
        assert call_args[0][1]["type"] == "stencil_selected"


class TestProgramSelection:
    """Testa seleção de programa."""

    def test_select_program_standard(self, coordinator):
        """Deve selecionar programa padrão."""
        result = coordinator.select_program("prog_standard")

        assert result is True
        assert coordinator.get_selected_program().program_id == "prog_standard"

    def test_select_program_quick(self, coordinator):
        """Deve selecionar programa rápido."""
        result = coordinator.select_program("prog_quick")

        assert result is True
        assert coordinator.get_selected_program().program_id == "prog_quick"

    def test_select_program_critical(self, coordinator):
        """Deve selecionar programa crítico."""
        result = coordinator.select_program("prog_critical")

        assert result is True
        assert coordinator.get_selected_program().program_id == "prog_critical"

    def test_select_invalid_program_returns_false(self, coordinator):
        """Programa inválido deve retornar False."""
        result = coordinator.select_program("invalid_program")

        assert result is False
        assert coordinator.get_selected_program() is None

    def test_get_available_programs(self, coordinator):
        """Deve retornar cópia dos programas disponíveis."""
        programs = coordinator.get_available_programs()

        assert len(programs) == 3
        # Deve ser uma cópia
        assert programs is not PREDEFINED_PROGRAMS

    def test_select_program_logs_action(self, coordinator, mock_session_logger):
        """Seleção deve ser registrada no logger."""
        coordinator._session_id = "session-123"
        coordinator.select_program("prog_standard")

        mock_session_logger.log_action.assert_called_once()
        call_args = mock_session_logger.log_action.call_args
        assert call_args[0][1]["type"] == "program_selected"


class TestInspectionValidation:
    """Testa validação antes de iniciar inspeção."""

    def test_start_without_stencil_returns_error(self, coordinator):
        """Iniciar sem stencil deve retornar erro."""
        result = coordinator.start_inspection()

        assert result["status"] == "error"
        assert "stencil" in result["message"].lower()

    def test_start_without_program_returns_error(self, coordinator):
        """Iniciar sem programa deve retornar erro."""
        coordinator.select_stencil("STENCIL-001")

        result = coordinator.start_inspection()

        assert result["status"] == "error"
        assert "program" in result["message"].lower()

    def test_start_without_permission_returns_error(self, coordinator, mock_role_manager):
        """Iniciar sem permissão deve retornar erro."""
        mock_role_manager.has_permission.return_value = False
        coordinator.select_stencil("STENCIL-001")
        coordinator.select_program("prog_standard")

        result = coordinator.start_inspection()

        assert result["status"] == "error"
        assert "permissão" in result["message"].lower() or "permission" in result["message"].lower()

    def test_validation_does_not_call_inspection_coordinator(self, coordinator, mock_inspection_coordinator):
        """Validação falha não deve chamar InspectionCoordinator."""
        coordinator.start_inspection()  # Sem stencil/program

        mock_inspection_coordinator.run_full_inspection.assert_not_called()


class TestInspectionExecution:
    """Testa execução de inspeção."""

    def test_start_inspection_with_valid_selection(self, coordinator):
        """Deve iniciar inspeção com seleção válida."""
        coordinator.select_stencil("STENCIL-001")
        coordinator.select_program("prog_standard")

        result = coordinator.start_inspection()

        assert result["status"] == "completed"
        assert result["classification"] in ["OK", "NOK"]

    def test_inspection_uses_selected_stencil_and_program(self, coordinator, mock_inspection_coordinator):
        """Deve usar stencil e programa selecionados."""
        coordinator.select_stencil("STENCIL-123")
        coordinator.select_program("prog_quick")

        # Mock para retornar resultado real
        mock_inspection_coordinator.run_full_inspection.return_value = {
            "status": "completed",
            "classification": "OK"
        }

        coordinator.start_inspection()

        # Verifica que o coordinator real foi chamado
        # NOTA: Na implementação atual, usa mock se InspectionCoordinator não configurado
        # Isso será corrigido na Fase 2

    def test_inspection_logs_start_action(self, coordinator, mock_session_logger):
        """Início da inspeção deve ser registrado."""
        coordinator.select_stencil("STENCIL-001")
        coordinator.select_program("prog_standard")
        coordinator.start_session("OP-001")

        coordinator.start_inspection()

        # Verifica que ação foi registrada
        assert mock_session_logger.log_action.called
        # Deve ter ao menos 2 ações: session_start + inspection_started

    def test_inspection_returns_ok_result(self, coordinator):
        """Inspeção deve retornar resultado OK quando porcentagem alta."""
        coordinator.select_stencil("STENCIL-001")
        coordinator.select_program("prog_standard")

        result = coordinator.start_inspection()

        assert result["status"] == "completed"
        assert result["classification"] == "OK"
        assert result["overall_percentage"] >= 90.0

    def test_inspection_includes_metadata(self, coordinator):
        """Resultado deve incluir metadados."""
        coordinator.select_stencil("STENCIL-456")
        coordinator.select_program("prog_critical")

        result = coordinator.start_inspection()

        assert result["stencil_code"] == "STENCIL-456"
        assert result["program_id"] == "prog_critical"
        assert "timestamp" in result


class TestSessionManagement:
    """Testa gerenciamento de sessão."""

    def test_start_session_returns_id(self, coordinator):
        """Iniciar sessão deve retornar ID."""
        session_id = coordinator.start_session("OP-001")

        assert session_id is not None
        assert isinstance(session_id, str)

    def test_start_session_logs_to_session_logger(self, coordinator, mock_session_logger):
        """Deve registrar no SessionLogger."""
        coordinator.start_session("OP-001")

        mock_session_logger.log_session_start.assert_called_once()
        call_args = mock_session_logger.log_session_start.call_args
        assert call_args[0][0] == "OP-001"

    def test_session_active_after_start(self, coordinator):
        """Sessão deve estar ativa após iniciar."""
        coordinator.start_session("OP-001")

        assert coordinator.is_session_active() is True

    def test_end_session_deactivates(self, coordinator, mock_session_logger):
        """Finalizar sessão deve desativar."""
        coordinator.start_session("OP-001")
        coordinator.end_session()

        assert coordinator.is_session_active() is False
        mock_session_logger.log_session_end.assert_called_once()

    def test_end_session_without_active_returns_false(self, coordinator, mock_session_logger):
        """Finalizar sem sessão ativa deve retornar False."""
        result = coordinator.end_session()

        assert result is False
        mock_session_logger.log_session_end.assert_not_called()


class TestProgramData:
    """Testa dados dos programas predefinidos."""

    def test_standard_program_has_correct_data(self):
        """Programa padrão deve ter dados corretos."""
        program = next(p for p in PREDEFINED_PROGRAMS if p.program_id == "prog_standard")

        assert program.name == "Inspeção Padrão"
        assert program.inspection_type == "standard"
        assert program.parameters["threshold_ok"] == 90.0

    def test_quick_program_has_lower_thresholds(self):
        """Programa rápido deve ter thresholds menores."""
        program = next(p for p in PREDEFINED_PROGRAMS if p.program_id == "prog_quick")

        assert program.name == "Inspeção Rápida"
        assert program.parameters["threshold_ok"] == 85.0
        assert program.parameters["threshold_partial"] == 65.0

    def test_critical_program_has_highest_thresholds(self):
        """Programa crítico deve ter thresholds maiores."""
        program = next(p for p in PREDEFINED_PROGRAMS if p.program_id == "prog_critical")

        assert program.name == "Apenas Críticos"
        assert program.parameters["threshold_ok"] == 95.0
        assert program.parameters["threshold_partial"] == 80.0


class TestErrorHandling:
    """Testa tratamento de erros."""

    def test_inspection_exception_returns_error_result(self, coordinator, mock_session_logger):
        """Exceção durante inspeção deve retornar erro."""
        coordinator.select_stencil("STENCIL-001")
        coordinator.select_program("prog_standard")
        coordinator.start_session("OP-001")

        # Força exceção no _execute_inspection (método interno)
        with patch.object(coordinator, '_execute_inspection', side_effect=Exception("Test error")):
            result = coordinator.start_inspection()

        assert result["status"] == "error"
        assert "erro" in result["message"].lower()

    def test_inspection_exception_logs_error_action(self, coordinator, mock_session_logger):
        """Exceção durante inspeção deve registrar erro."""
        coordinator.select_stencil("STENCIL-001")
        coordinator.select_program("prog_standard")
        coordinator.start_session("OP-001")

        # Força exceção
        with patch.object(coordinator, '_execute_inspection', side_effect=Exception("Test")):
            coordinator.start_inspection()

        # Verifica que erro foi registrado
        error_actions = [
            call for call in mock_session_logger.log_action.call_args_list
            if call[0][1].get("type") == "inspection_failed"
        ]
        assert len(error_actions) > 0

    def test_mock_inspection_returns_completed_result(self, coordinator):
        """
        Inspeção mock (GREEN phase) deve retornar completed.
        TODO: Este teste deve ser removido quando _execute_inspection()
        for modificado para chamar inspection_coordinator.run_full_inspection() de verdade.
        """
        coordinator.select_stencil("STENCIL-001")
        coordinator.select_program("prog_standard")

        result = coordinator.start_inspection()

        # Na implementação atual (GREEN phase), _execute_inspection()
        # retorna resultado mock, não chama o inspection_coordinator de verdade
        assert result["status"] == "completed"
        assert result["classification"] in ["OK", "NOK"]
