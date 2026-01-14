"""
Testes para validação cruzada do EngineeringWizardState

Testa os métodos de validação:
- is_valid(): Verifica se aba tem dados completos
- get_validation_message(): Retorna mensagens específicas de validação
- validate_dependencies(): Verifica dependências entre abas
- can_proceed_to_tab(): Verifica se pode avançar para determinada aba
"""

import pytest
from datetime import datetime

from consumo_lib.models.engineering.wizard_state import EngineeringWizardState


class TestIsValidMethod:
    """Testes para o método is_valid()."""

    @pytest.fixture
    def empty_state(self):
        """Cria estado vazio."""
        return EngineeringWizardState()

    def test_aba_1_valid_with_all_fields(self, empty_state):
        """Testa que Aba 1 é válida com todos os campos obrigatórios."""
        empty_state.program_data = {
            'program_name': 'Test Program',
            'stencil_code': 'STENCIL-001',
            'version': 'v1.0',
            'created_by': 'test_user'
        }
        assert empty_state.is_valid(0) is True

    def test_aba_1_invalid_missing_field(self, empty_state):
        """Testa que Aba 1 é inválida se faltar campo obrigatório."""
        empty_state.program_data = {
            'program_name': 'Test Program',
            'stencil_code': 'STENCIL-001',
            # Faltam 'version' e 'created_by'
        }
        assert empty_state.is_valid(0) is False

    def test_aba_1_invalid_no_data(self, empty_state):
        """Testa que Aba 1 é inválida sem dados."""
        assert empty_state.is_valid(0) is False

    def test_aba_2_valid_with_gerber(self, empty_state):
        """Testa que Aba 2 é válida com Gerber carregado."""
        empty_state.gerber_file = "test.ger"
        empty_state.gerber_data = {"apertures": 100}
        assert empty_state.is_valid(1) is True

    def test_aba_2_invalid_no_file(self, empty_state):
        """Testa que Aba 2 é inválida sem arquivo."""
        empty_state.gerber_data = {"apertures": 100}
        assert empty_state.is_valid(1) is False

    def test_aba_3_valid_with_2_fiducials(self, empty_state):
        """Testa que Aba 3 é válida com 2 fiduciais."""
        empty_state.fiducial_templates = [
            {"x": 10, "y": 20},
            {"x": 30, "y": 40}
        ]
        assert empty_state.is_valid(2) is True

    def test_aba_3_invalid_only_1_fiducial(self, empty_state):
        """Testa que Aba 3 é inválida com apenas 1 fiducial."""
        empty_state.fiducial_templates = [
            {"x": 10, "y": 20}
        ]
        assert empty_state.is_valid(2) is False

    def test_aba_4_valid_with_mosaic(self, empty_state):
        """Testa que Aba 4 é válida com mosaico capturado."""
        empty_state.mosaic_config = {"grid_rows": 3, "grid_cols": 3}
        assert empty_state.is_valid(3) is True

    def test_aba_5_valid_with_alignment(self, empty_state):
        """Testa que Aba 5 é válida com alinhamento."""
        empty_state.alignment_transform = {"tx": 1.0, "ty": 2.0, "angle": 0.5}
        assert empty_state.is_valid(4) is True

    def test_aba_6_valid_with_groups(self, empty_state):
        """Testa que Aba 6 é válida com grupos de inspeção."""
        empty_state.inspection_groups = [
            {"name": "Group 1", "aperture_count": 50}
        ]
        assert empty_state.is_valid(5) is True

    def test_aba_6_invalid_no_groups(self, empty_state):
        """Testa que Aba 6 é inválida sem grupos."""
        empty_state.inspection_groups = []
        assert empty_state.is_valid(5) is False

    def test_aba_7_valid_all_previous_complete(self, empty_state):
        """Testa que Aba 7 é válida se todas anteriores estão completas."""
        # Preencher todas as abas
        empty_state.program_data = {
            'program_name': 'Test',
            'stencil_code': 'STENCIL-001',
            'version': 'v1.0',
            'created_by': 'test'
        }
        empty_state.gerber_file = "test.ger"
        empty_state.gerber_data = {}
        empty_state.fiducial_templates = [{"x": 0, "y": 0}, {"x": 1, "y": 1}]
        empty_state.mosaic_config = {}
        empty_state.alignment_transform = {}
        empty_state.inspection_groups = [{}]

        assert empty_state.is_valid(6) is True

    def test_aba_7_invalid_previous_incomplete(self, empty_state):
        """Testa que Aba 7 é inválida se alguma aba anterior está incompleta."""
        # Apenas algumas abas preenchidas
        empty_state.program_data = {
            'program_name': 'Test',
            'stencil_code': 'STENCIL-001',
            'version': 'v1.0',
            'created_by': 'test'
        }
        # Demais abas vazias

        assert empty_state.is_valid(6) is False


class TestGetValidationMessage:
    """Testes para o método get_validation_message()."""

    @pytest.fixture
    def empty_state(self):
        """Cria estado vazio."""
        return EngineeringWizardState()

    def test_message_aba_1_complete(self, empty_state):
        """Testa mensagem de Aba 1 completa."""
        empty_state.program_data = {
            'program_name': 'Test',
            'stencil_code': 'STENCIL-001',
            'version': 'v1.0',
            'created_by': 'test'
        }
        msg = empty_state.get_validation_message(0)
        assert msg == "✓ Completo"

    def test_message_aba_1_no_data(self, empty_state):
        """Testa mensagem de Aba 1 sem dados."""
        msg = empty_state.get_validation_message(0)
        assert "Preencha todos os campos obrigatórios" in msg
        assert "⚠" in msg

    def test_message_aba_1_missing_fields(self, empty_state):
        """Testa mensagem de Aba 1 com campos faltando."""
        empty_state.program_data = {
            'program_name': 'Test',
            # Faltam: stencil_code, version, created_by
        }
        msg = empty_state.get_validation_message(0)
        assert "Campos faltando" in msg
        assert "stencil_code" in msg
        assert "⚠" in msg

    def test_message_aba_2_no_file(self, empty_state):
        """Testa mensagem de Aba 2 sem arquivo."""
        msg = empty_state.get_validation_message(1)
        assert "Carregue um arquivo Gerber" in msg
        assert "⚠" in msg

    def test_message_aba_2_complete(self, empty_state):
        """Testa mensagem de Aba 2 completa."""
        empty_state.gerber_file = "test.ger"
        empty_state.gerber_data = {}
        msg = empty_state.get_validation_message(1)
        assert msg == "✓ Completo"

    def test_message_aba_3_no_fiducials(self, empty_state):
        """Testa mensagem de Aba 3 sem fiduciais."""
        msg = empty_state.get_validation_message(2)
        assert "Capture pelo menos 2 fiduciais" in msg
        assert "(0/2)" in msg
        assert "⚠" in msg

    def test_message_aba_3_one_fiducial(self, empty_state):
        """Testa mensagem de Aba 3 com 1 fiducial."""
        empty_state.fiducial_templates = [{"x": 0, "y": 0}]
        msg = empty_state.get_validation_message(2)
        assert "Capture 1 fiducial adicional" in msg
        assert "(1/2)" in msg
        assert "⚠" in msg

    def test_message_aba_4_no_mosaic(self, empty_state):
        """Testa mensagem de Aba 4 sem mosaico."""
        msg = empty_state.get_validation_message(3)
        assert "Capture o mosaico" in msg
        assert "⚠" in msg

    def test_message_aba_5_no_alignment(self, empty_state):
        """Testa mensagem de Aba 5 sem alinhamento."""
        msg = empty_state.get_validation_message(4)
        assert "Execute o alinhamento" in msg
        assert "⚠" in msg

    def test_message_aba_6_no_groups(self, empty_state):
        """Testa mensagem de Aba 6 sem grupos."""
        msg = empty_state.get_validation_message(5)
        assert "Crie pelo menos 1 grupo de inspeção" in msg
        assert "⚠" in msg

    def test_message_aba_6_with_groups(self, empty_state):
        """Testa mensagem de Aba 6 com grupos."""
        empty_state.inspection_groups = [{}, {}]
        msg = empty_state.get_validation_message(5)
        assert "Configure grupos de inspeção" in msg
        assert "(2 grupos)" in msg
        assert "⚠" in msg


class TestValidateDependencies:
    """Testes para o método validate_dependencies()."""

    @pytest.fixture
    def empty_state(self):
        """Cria estado vazio."""
        return EngineeringWizardState()

    def test_aba_1_no_dependencies(self, empty_state):
        """Testa que Aba 1 não tem dependências."""
        valid, msg = empty_state.validate_dependencies(0)
        assert valid is True
        assert msg == ""

    def test_aba_2_requires_aba_1(self, empty_state):
        """Testa que Aba 2 depende da Aba 1."""
        valid, msg = empty_state.validate_dependencies(1)
        assert valid is False
        assert "Dados do Programa" in msg

    def test_aba_2_satisfied(self, empty_state):
        """Testa que Aba 2 é válida se Aba 1 está completa."""
        empty_state.program_data = {
            'program_name': 'Test',
            'stencil_code': 'STENCIL-001',
            'version': 'v1.0',
            'created_by': 'test'
        }
        valid, msg = empty_state.validate_dependencies(1)
        assert valid is True
        assert msg == ""

    def test_aba_3_requires_aba_2(self, empty_state):
        """Testa que Aba 3 depende da Aba 2."""
        empty_state.program_data = {
            'program_name': 'Test',
            'stencil_code': 'STENCIL-001',
            'version': 'v1.0',
            'created_by': 'test'
        }
        valid, msg = empty_state.validate_dependencies(2)
        assert valid is False
        assert "Carregue o arquivo Gerber" in msg

    def test_aba_7_requires_all_previous(self, empty_state):
        """Testa que Aba 7 depende de todas as abas anteriores."""
        # Apenas Aba 1 completa
        empty_state.program_data = {
            'program_name': 'Test',
            'stencil_code': 'STENCIL-001',
            'version': 'v1.0',
            'created_by': 'test'
        }
        valid, msg = empty_state.validate_dependencies(6)
        assert valid is False
        assert "Complete as abas anteriores" in msg


class TestCanProceedToTab:
    """Testes para o método can_proceed_to_tab()."""

    @pytest.fixture
    def empty_state(self):
        """Cria estado vazio."""
        state = EngineeringWizardState()
        state.current_tab = 0
        return state

    def test_cannot_skip_tabs(self, empty_state):
        """Testa que não pode pular abas."""
        empty_state.current_tab = 0
        can_proceed, msg = empty_state.can_proceed_to_tab(3)
        assert can_proceed is False
        assert "Complete a aba" in msg

    def test_can_proceed_to_next_if_valid(self, empty_state):
        """Testa que pode avançar para próxima se dependências atendidas."""
        empty_state.current_tab = 0
        empty_state.program_data = {
            'program_name': 'Test',
            'stencil_code': 'STENCIL-001',
            'version': 'v1.0',
            'created_by': 'test'
        }
        can_proceed, msg = empty_state.can_proceed_to_tab(1)
        assert can_proceed is True
        assert msg == ""

    def test_cannot_proceed_if_dependencies_not_met(self, empty_state):
        """Testa que não pode avançar se dependências não atendidas."""
        empty_state.current_tab = 0
        can_proceed, msg = empty_state.can_proceed_to_tab(1)
        assert can_proceed is False
        assert len(msg) > 0

    def test_can_go_back_anytime(self, empty_state):
        """Testa que pode voltar para aba anterior qualquer momento."""
        empty_state.current_tab = 3
        can_proceed, msg = empty_state.can_proceed_to_tab(2)
        # Voltar é permitido (não é pular abas)
        assert can_proceed is True
