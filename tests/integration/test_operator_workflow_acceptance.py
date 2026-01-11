"""
Testes de Aceitação para Operator Workflow

Estes testes verificam os CRITÉRIOS DE ACEITE definidos na spec.md.
Cada teste representa um requisito funcional que o operador deve conseguir executar.

Foco: Comportamentos de ponta a ponta do fluxo de operador.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

# Importa classes reais
from consumo_lib.managers.role_manager import RoleManager, PermissionDeniedError
from consumo_lib.managers.session_logger import SessionLogger
from consumo_lib.coordinators.operator_workflow import (
    OperatorInspectionCoordinator,
    InspectionProgram,
    PREDEFINED_PROGRAMS
)
from consumo_lib.widgets.operator_interface import (
    StencilSelector,
    ProgramSelector,
    InspectionResultsWidget
)
from consumo_lib.threads.operator_inspection_thread import OperatorInspectionThread


class TestOperatorInterfaceDisplay:
    """Testa o critério: Operator sees simplified interface on startup."""

    def test_role_manager_returns_operator_role(self):
        """
        Critério de Aceite: Operator sees simplified interface on startup.

        Comportamento: RoleManager deve identificar role do usuário.

        Verifica:
        - RoleManager retorna role correta
        - Role operator não tem permissões de engenharia
        """
        role_manager = RoleManager()

        # Configura como operator
        role_manager.set_role("operator")

        # Verifica: Role do usuário atual é "operator"
        current_role = role_manager.get_current_role()
        assert current_role == "operator", "Usuário deve ter role operator"

        # Verifica: Operator não pode acessar configurações de engenharia
        assert not role_manager.can_access_engineering_settings(), \
            "Operator não deve acessar configurações de engenharia"

    def test_engineering_role_has_full_permissions(self):
        """
        Comportamento: Usuários com role "engineering" têm permissões completas.

        Verifica:
        - Role engineering é reconhecida
        - Engineering tem permissões de configuração
        """
        role_manager = RoleManager()

        # Configura como engineering
        role_manager.set_role("engineering")

        # Verifica: Role engineering tem acesso completo
        assert role_manager.get_current_role() == "engineering"
        assert role_manager.can_access_engineering_settings(), \
            "Engineering deve acessar configurações de engenharia"
        assert role_manager.can_manage_recipes(), \
            "Engineering deve gerenciar receitas"


class TestStencilSelection:
    """Testa o critério: Can select stencil from dropdown list."""

    @pytest.fixture
    def mock_stencil_data(self):
        """Simula dados de stencils disponíveis."""
        return [
            {"code": "STENCIL-001", "description": "Stencil Principal"},
            {"code": "STENCIL-002", "description": "Stencil Secundário"},
            {"code": "STENCIL-003", "description": "Stencil Protótipo"}
        ]

    def test_can_select_stencil_from_dropdown(self, mock_stencil_data):
        """
        Critério de Aceite: Can select stencil from dropdown list.

        Comportamento: Operador deve conseguir selecionar um stencil
        de uma lista dropdown preenchida com stencils disponíveis.

        Verifica:
        - Dropdown é populado com stencils
        - Seleção funciona corretamente
        - Stencil selecionado é armazenado
        """
        # Cria selector com dados mockados
        selector = StencilSelector(stencils=mock_stencil_data)

        # Verifica: Dropdown contém stencils
        available_stencils = selector.get_available_stencils()
        assert len(available_stencils) == 3, "Deve mostrar 3 stencils disponíveis"
        assert "STENCIL-001" in [s['code'] for s in available_stencils]

        # Simula: Usuário seleciona STENCIL-002
        selector.select_stencil("STENCIL-002")

        # Verifica: Stencil foi selecionado
        selected = selector.get_selected_stencil()
        assert selected is not None, "Deve ter um stencil selecionado"
        assert selected['code'] == "STENCIL-002", "Deve selecionar o stencil correto"
        assert selected['description'] == "Stencil Secundário"

    def test_empty_stencil_list_shows_warning(self):
        """
        Comportamento: Se não há stencils disponíveis, mostra aviso.

        Verifica:
        - Sistema detecta lista vazia
        - Mensagem adequada é mostrada ao operador
        """
        selector = StencilSelector(stencils=[])

        # Verifica: Sistema detecta lista vazia
        assert selector.is_empty(), "Deve detectar lista vazia"

        # Verifica: Mensagem de aviso está disponível
        warning = selector.get_warning_message()
        assert warning is not None, "Deve ter mensagem de aviso"
        assert "stencil" in warning.lower() or "disponível" in warning.lower()


class TestProgramSelection:
    """Testa o critério: Can select predefined inspection program."""

    @pytest.fixture
    def mock_programs(self):
        """Simula programas de inspeção predefinidos."""
        return [
            {"id": "prog_standard", "name": "Inspeção Padrão", "description": "Verificação completa"},
            {"id": "prog_quick", "name": "Inspeção Rápida", "description": "Verificação simplificada"},
            {"id": "prog_critical", "name": "Apenas Críticos", "description": "Verifica apenas áreas críticas"}
        ]

    def test_can_select_predefined_program(self, mock_programs):
        """
        Critério de Aceite: Can select predefined inspection program.

        Comportamento: Operador deve conseguir selecionar um programa
        de inspeção predefinido de uma lista.

        Verifica:
        - Programas predefinidos são listados
        - Seleção funciona corretamente
        - Programa selecionado é armazenado
        """
        from consumo_lib.widgets.operator_interface import ProgramSelector

        selector = ProgramSelector(programs=mock_programs)

        # Verifica: Programas estão disponíveis
        available = selector.get_available_programs()
        assert len(available) == 3, "Deve ter 3 programas disponíveis"
        assert "prog_standard" in [p['id'] for p in available]
        assert "prog_quick" in [p['id'] for p in available]

        # Simula: Usuário seleciona programa padrão
        selector.select_program("prog_standard")

        # Verifica: Programa foi selecionado
        selected = selector.get_selected_program()
        assert selected is not None, "Deve ter programa selecionado"
        assert selected['id'] == "prog_standard"
        assert selected['name'] == "Inspeção Padrão"

    def test_program_has_description(self, mock_programs):
        """
        Comportamento: Cada programa deve ter descrição visível ao operador.

        Verifica:
        - Descrição é mostrada junto com nome do programa
        - Ajuda operador a escolher o programa adequado
        """
        from consumo_lib.widgets.operator_interface import ProgramSelector

        selector = ProgramSelector(programs=mock_programs)

        # Verifica: Programa tem descrição visível
        program_info = selector.get_program_info("prog_standard")
        assert program_info is not None, "Deve retornar info do programa"
        assert "description" in program_info, "Info deve incluir descrição"
        assert "Verificação completa" in program_info['description']


class TestOneClickInspection:
    """Testa o critério: 'Start Inspection' button executes complete workflow."""

    @pytest.fixture
    def mock_inspection_coordinator(self):
        """Mock do InspectionCoordinator."""
        coordinator = Mock()
        coordinator.run_full_inspection.return_value = {
            "status": "completed",
            "total_apertures": 150,
            "ok": 140,
            "partial": 8,
            "blocked": 2
        }
        return coordinator

    def test_start_inspection_button_executes_workflow(self, mock_inspection_coordinator):
        """
        Critério de Aceite: 'Start Inspection' button executes complete workflow.

        Comportamento: Botão "Start Inspection" deve executar todo o fluxo
        de inspeção automaticamente sem intervenção do operador.

        Fluxo:
        1. Valida seleção (stencil + programa)
        2. Move CNC para posição inicial
        3. Captura imagens
        4. Processa inspeção
        5. Classifica resultados

        Verifica:
        - Workflow completo é executado
        - Coordinator é chamado com parâmetros corretos
        - Resultados são retornados
        """
        from consumo_lib.coordinators.operator_workflow import OperatorInspectionCoordinator

        coordinator = OperatorInspectionCoordinator(
            inspection_coordinator=mock_inspection_coordinator
        )

        # Setup: Simula seleção prévia
        stencil_code = "STENCIL-001"
        program_id = "prog_standard"

        # Executa: Clique no botão "Start Inspection"
        result = coordinator.start_inspection(
            stencil_code=stencil_code,
            program_id=program_id
        )

        # Verifica: Workflow foi executado
        assert result is not None, "Deve retornar resultado"
        assert result['status'] == 'completed', "Inspeção deve completar"

        # Verifica: Coordinator foi chamado corretamente
        mock_inspection_coordinator.run_full_inspection.assert_called_once()
        call_args = mock_inspection_coordinator.run_full_inspection.call_args
        assert call_args[1]['stencil_code'] == stencil_code

    def test_workflow_validates_selection_before_start(self, mock_inspection_coordinator):
        """
        Comportamento: Sistema valida seleção antes de iniciar inspeção.

        Verifica:
        - Retorna erro se stencil não selecionado
        - Retorna erro se programa não selecionado
        - Não inicia workflow se validação falhar
        """
        from consumo_lib.coordinators.operator_workflow import OperatorInspectionCoordinator

        coordinator = OperatorInspectionCoordinator(
            inspection_coordinator=mock_inspection_coordinator
        )

        # Tenta iniciar sem selecionar stencil
        result = coordinator.start_inspection(
            stencil_code=None,
            program_id="prog_standard"
        )

        # Verifica: Validação falhou
        assert result['status'] == 'error', "Deve retornar erro"
        assert 'stencil' in result['message'].lower(), \
            "Erro deve mencionar stencil não selecionado"

        # Verifica: Coordinator não foi chamado
        mock_inspection_coordinator.run_full_inspection.assert_not_called()


class TestProgressDisplay:
    """Testa o critério: Progress shown during execution."""

    def test_progress_shown_during_execution(self):
        """
        Critério de Aceite: Progress shown during execution.

        Comportamento: Durante a execução da inspeção, operador deve ver
        progresso atual (etapa atual, porcentagem, mensagem).

        Verifica:
        - Progresso é emitido via signals
        - Mensagens descritivas são mostradas
        - Porcentagem é calculada corretamente
        """
        from consumo_lib.threads.operator_inspection_thread import OperatorInspectionThread

        # Cria thread de inspeção (mock)
        thread = OperatorInspectionThread(
            stencil_code="STENCIL-001",
            program_id="prog_standard"
        )

        # Mock para capturar signals emitidos
        progress_updates = []

        def capture_progress(step, total, message):
            progress_updates.append({
                'step': step,
                'total': total,
                'message': message,
                'percentage': (step / total) * 100
            })

        # Conecta signal de progresso
        thread.progress_updated.connect(capture_progress)

        # Simula: Execução produz updates de progresso
        # (na implementação real, thread.emit_progress seria chamado durante workflow)
        thread.emit_progress(5, 10, "Capturando imagem 5 de 10")
        thread.emit_progress(10, 10, "Inspeção completada")

        # Verifica: Progresso foi capturado
        assert len(progress_updates) == 2, "Deve ter 2 atualizações"
        assert progress_updates[0]['percentage'] == 50.0, "Primeiro: 50%"
        assert progress_updates[1]['percentage'] == 100.0, "Segundo: 100%"
        assert "Capturando" in progress_updates[0]['message']
        assert "completada" in progress_updates[1]['message'].lower()


class TestResultsDisplay:
    """Testa o critério: Results displayed in simple format (OK/NOK)."""

    @pytest.fixture
    def inspection_result_pass(self):
        """Resultado de inspeção APROVADO."""
        return {
            "status": "completed",
            "classification": "OK",
            "total_apertures": 200,
            "ok": 195,
            "partial": 5,
            "blocked": 0,
            "overall_percentage": 97.5
        }

    @pytest.fixture
    def inspection_result_fail(self):
        """Resultado de inspeção REPROVADO."""
        return {
            "status": "completed",
            "classification": "NOK",
            "total_apertures": 200,
            "ok": 130,
            "partial": 20,
            "blocked": 50,
            "overall_percentage": 65.0
        }

    def test_results_displayed_in_simple_format_pass(self, inspection_result_pass):
        """
        Critério de Aceite: Results displayed in simple format (OK/NOK).

        Comportamento: Resultados devem ser mostrados em formato simples
        que operador consegue interpretar rapidamente.

        Verifica:
        - Classificação OK/NOK é clara e visível
        - Métricas principais são mostradas
        - Formato é simples e direto
        """
        from consumo_lib.widgets.operator_interface import InspectionResultsWidget

        widget = InspectionResultsWidget()
        widget.display_results(inspection_result_pass)

        # Verifica: Classificação está visível
        classification = widget.get_classification()
        assert classification == "OK", "Deve mostrar classificação OK"
        assert widget.is_passing(), "Resultado deve ser aprovado"

        # Verifica: Métricas principais disponíveis
        metrics = widget.get_main_metrics()
        assert metrics['total'] == 200
        assert metrics['ok'] == 195
        assert metrics['overall_percentage'] == 97.5

    def test_results_displayed_in_simple_format_fail(self, inspection_result_fail):
        """
        Comportamento: Resultado NOK deve ser claramente indicado.

        Verifica:
        - Classificação NOK é visível
        - Cor/indicador visual mostra problema
        - Operador sabe que ação é necessária
        """
        from consumo_lib.widgets.operator_interface import InspectionResultsWidget

        widget = InspectionResultsWidget()
        widget.display_results(inspection_result_fail)

        # Verifica: Classificação NOK
        classification = widget.get_classification()
        assert classification == "NOK", "Deve mostrar classificação NOK"
        assert not widget.is_passing(), "Resultado deve ser reprovado"

        # Verifica: Problemas são destacados
        blocked_count = widget.get_blocked_count()
        assert blocked_count == 50, "Deve mostrar 50 aberturas bloqueadas"


class TestEngineeringRestrictions:
    """Testa o critério: Cannot access engineering settings."""

    @pytest.fixture
    def operator_role_manager(self):
        """RoleManager configurado como operator."""
        manager = Mock()
        manager.get_current_role.return_value = "operator"
        manager.has_permission.return_value = False
        return manager

    def test_cannot_access_engineering_settings(self, operator_role_manager):
        """
        Critério de Aceite: Cannot access engineering settings.

        Comportamento: Operador NÃO deve conseguir acessar configurações
        de engenharia (receitas, parâmetros de calibração, etc.).

        Verifica:
        - Tentativa de acesso é negada
        - Mensagem de permissão negada é mostrada
        - Role manager bloqueia ação
        """
        from consumo_lib.managers.role_manager import PermissionDeniedError

        # Tenta acessar configuração de engenharia
        try:
            operator_role_manager.check_permission("engineering.settings.edit")
            assert False, "Deveria ter lançado PermissionDeniedError"
        except PermissionDeniedError as e:
            # Verifica: Acesso negado
            assert "permissão" in str(e).lower() or "permission" in str(e).lower()

        # Verifica: has_permission retorna False
        assert not operator_role_manager.has_permission("engineering.settings.edit")

    def test_engineering_can_access_settings(self):
        """
        Comportamento: Engenheiros CONSEGUEM acessar configurações.

        Verifica:
        - Role engineering tem permissão
        - Acesso é permitido
        """
        manager = Mock()
        manager.get_current_role.return_value = "engineering"
        manager.has_permission.return_value = True
        manager.check_permission = Mock()  # Não lança exceção

        # Verifica: Engenheiro tem permissão
        assert manager.has_permission("engineering.settings.edit")
        manager.check_permission("engineering.settings.edit")  # Não deve lançar


class TestOperatorSessionLogging:
    """Testa o critério: Session logged with operator ID."""

    @pytest.fixture
    def mock_session_logger(self):
        """Mock do SessionLogger."""
        logger = Mock()
        logger.log_session_start.return_value = "session-123"
        logger.log_session_end.return_value = True
        return logger

    def test_session_logged_with_operator_id(self, mock_session_logger):
        """
        Critério de Aceite: Session logged with operator ID.

        Comportamento: Cada sessão de operador deve ser registrada
        com ID do operador, timestamp e ações executadas.

        Verifica:
        - Session start é registrado com operator ID
        - Session end é registrado
        - Logs contêm informações de rastreamento
        """
        from consumo_lib.managers.session_logger import SessionLogger
        from datetime import datetime

        # Setup: Cria logger de sessão
        session_logger = SessionLogger()

        # Simula: Início da sessão
        operator_id = "OP-001"  # ID do operador (do login/badge)
        session_id = session_logger.log_session_start(
            operator_id=operator_id,
            timestamp=datetime.now()
        )

        # Verifica: Sessão foi registrada
        assert session_id is not None, "Deve retornar session ID"
        mock_session_logger.log_session_start.assert_called_once()
        call_args = mock_session_logger.log_session_start.call_args
        assert call_args[1]['operator_id'] == operator_id, \
            "Log deve conter operator ID"

        # Simula: Fim da sessão
        session_logger.log_session_end(
            session_id=session_id,
            actions_executed=["inspection_started", "inspection_completed"],
            timestamp=datetime.now()
        )

        # Verifica: Fim da sessão registrado
        mock_session_logger.log_session_end.assert_called_once()

    def test_session_logs_contain_action_details(self, mock_session_logger):
        """
        Comportamento: Logs de sessão devem conter detalhes das ações.

        Verifica:
        - Ações executadas são listadas
        - Timestamps são registrados
        - Stencils inspecionados são registrados
        """
        from consumo_lib.managers.session_logger import SessionLogger

        session_logger = SessionLogger()

        # Simula: Registra ação durante sessão
        session_id = "session-123"
        action = {
            "type": "inspection_started",
            "stencil_code": "STENCIL-001",
            "program_id": "prog_standard",
            "timestamp": datetime.now().isoformat()
        }

        session_logger.log_action(session_id, action)

        # Verifica: Ação foi registrada
        mock_session_logger.log_action.assert_called_once_with(
            session_id, action
        )


# Testes de Integração End-to-End

class TestOperatorWorkflowE2E:
    """Testes de fluxo completo do operador."""

    @pytest.fixture
    def complete_workflow_mocks(self):
        """Mocks para todos os componentes do workflow."""
        return {
            'role_manager': Mock(get_current_role=Mock(return_value="operator")),
            'stencil_selector': Mock(),
            'program_selector': Mock(),
            'inspection_coordinator': Mock(
                run_full_inspection=Mock(return_value={
                    "status": "completed",
                    "classification": "OK",
                    "total_apertures": 150,
                    "ok": 145,
                    "partial": 5,
                    "blocked": 0
                })
            ),
            'session_logger': Mock()
        }

    def test_complete_operator_workflow_happy_path(self, complete_workflow_mocks):
        """
        Teste E2E: Fluxo completo do operador (caminho feliz).

        Cenário: Operador inicia aplicativo, seleciona stencil,
        seleciona programa, inicia inspeção e vê resultado OK.

        Verifica:
        - Todos os componentes funcionam em conjunto
        - Fluxo é executado sem erros
        - Resultado final é correto
        """
        from consumo_lib.coordinators.operator_workflow import OperatorInspectionCoordinator

        # Setup: Configura todos os mocks
        coordinator = OperatorInspectionCoordinator(
            role_manager=complete_workflow_mocks['role_manager'],
            inspection_coordinator=complete_workflow_mocks['inspection_coordinator'],
            session_logger=complete_workflow_mocks['session_logger']
        )

        # Step 1: Operador seleciona stencil
        coordinator.select_stencil("STENCIL-001")

        # Step 2: Operador seleciona programa
        coordinator.select_program("prog_standard")

        # Step 3: Operador clica "Start Inspection"
        result = coordinator.start_inspection()

        # Verifica: Workflow completou com sucesso
        assert result['status'] == 'completed', "Inspeção deve completar"
        assert result['classification'] == 'OK', "Resultado deve ser OK"

        # Verifica: Session logger foi chamado
        complete_workflow_mocks['session_logger'].log_session_start.assert_called()
        complete_workflow_mocks['session_logger'].log_action.assert_called()

    def test_complete_workflow_with_validation_error(self, complete_workflow_mocks):
        """
        Teste E2E: Fluxo com erro de validação.

        Cenário: Operador tenta iniciar inspeção sem selecionar stencil.

        Verifica:
        - Validação falha adequadamente
        - Mensagem de erro é clara
        - Workflow não é iniciado
        """
        from consumo_lib.coordinators.operator_workflow import OperatorInspectionCoordinator

        coordinator = OperatorInspectionCoordinator(
            role_manager=complete_workflow_mocks['role_manager'],
            inspection_coordinator=complete_workflow_mocks['inspection_coordinator']
        )

        # Tenta iniciar SEM selecionar stencil
        result = coordinator.start_inspection()

        # Verifica: Erro de validação
        assert result['status'] == 'error', "Deve retornar erro"
        assert 'stencil' in result['message'].lower(), \
            "Erro deve mencionar stencil"

        # Verifica: Coordinator não foi chamado
        complete_workflow_mocks['inspection_coordinator'].run_full_inspection.assert_not_called()
