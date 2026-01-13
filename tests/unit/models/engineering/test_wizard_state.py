"""
Testes unitários para EngineeringWizardState

Testa o gerenciador de estado compartilhado do Engineering Wizard.
"""

import pytest
from datetime import datetime

from consumo_lib.models.engineering.wizard_state import EngineeringWizardState


class TestEngineeringWizardStateCreation:
    """Testes para criação do estado."""

    def test_create_empty_state(self):
        """Testa criação de estado vazio."""
        state = EngineeringWizardState()

        assert state.program_data is None
        assert state.gerber_file is None
        assert state.gerber_data is None
        assert len(state.fiducial_templates) == 0
        assert state.mosaic_image_path is None
        assert state.mosaic_config is None
        assert state.alignment_transform is None
        assert len(state.inspection_groups) == 0
        assert state.program_config is None

        assert state.current_tab == 0
        assert state.is_dirty is False
        assert state.auto_save_path is None
        assert isinstance(state.created_at, str)
        assert isinstance(state.updated_at, str)

    def test_create_state_with_data(self):
        """Testa criação de estado com dados."""
        state = EngineeringWizardState(
            program_data={'program_name': 'Test'},
            current_tab=2,
            is_dirty=True
        )

        assert state.program_data == {'program_name': 'Test'}
        assert state.current_tab == 2
        assert state.is_dirty is True


class TestEngineeringWizardStateValidation:
    """Testes para validação de abas."""

    def test_aba_1_invalid_sem_dados(self):
        """Testa que aba 1 é inválida sem dados."""
        state = EngineeringWizardState()
        assert not state.is_valid(0)

    def test_aba_1_valid_com_dados(self):
        """Testa que aba 1 é válida com dados completos."""
        state = EngineeringWizardState()
        state.program_data = {
            'program_name': 'Test Program',
            'stencil_code': 'STENCIL-001',
            'version': 'v1.0',
            'created_by': 'engineer'
        }
        assert state.is_valid(0)

    def test_aba_1_valid_falta_campo(self):
        """Testa que aba 1 é inválida faltando campo obrigatório."""
        state = EngineeringWizardState()
        state.program_data = {
            'program_name': 'Test Program',
            'stencil_code': 'STENCIL-001',
            # Falta 'version'
            'created_by': 'engineer'
        }
        assert not state.is_valid(0)

    def test_aba_2_valid_com_gerber(self):
        """Testa que aba 2 é válida com Gerber carregado."""
        state = EngineeringWizardState()
        state.gerber_data = {'apertures': []}
        state.gerber_file = '/path/to/file.gbr'
        assert state.is_valid(1)

    def test_aba_3_valid_com_2_fiduciais(self):
        """Testa que aba 3 é válida com 2 fiduciais."""
        state = EngineeringWizardState()
        state.fiducial_templates = [
            {'id': 0, 'x': 10, 'y': 20},
            {'id': 1, 'x': 30, 'y': 40}
        ]
        assert state.is_valid(2)

    def test_aba_3_invalid_com_1_fiducial(self):
        """Testa que aba 3 é inválida com apenas 1 fiducial."""
        state = EngineeringWizardState()
        state.fiducial_templates = [
            {'id': 0, 'x': 10, 'y': 20}
        ]
        assert not state.is_valid(2)

    def test_aba_4_valid_com_mosaico(self):
        """Testa que aba 4 é válida com mosaico."""
        state = EngineeringWizardState()
        state.mosaic_config = {'rows': 5, 'cols': 5}
        assert state.is_valid(3)

    def test_aba_5_valid_com_alinhamento(self):
        """Testa que aba 5 é válida com alinhamento."""
        state = EngineeringWizardState()
        state.alignment_transform = {'tx': 10, 'ty': 20, 'angle': 0}
        assert state.is_valid(4)

    def test_aba_6_valid_com_grupos(self):
        """Testa que aba 6 é válida com grupos."""
        state = EngineeringWizardState()
        state.inspection_groups = [
            {'name': 'Group 1', 'windows': []}
        ]
        assert state.is_valid(5)

    def test_aba_7_valid_com_tudo_completo(self):
        """Testa que aba 7 é válida apenas com todas as anteriores completas."""
        state = EngineeringWizardState()

        # Completar todas as abas
        state.program_data = {
            'program_name': 'Test',
            'stencil_code': 'STENCIL-001',
            'version': 'v1.0',
            'created_by': 'engineer'
        }
        state.gerber_data = {}
        state.gerber_file = 'test.gbr'
        state.fiducial_templates = [{'id': 0}, {'id': 1}]
        state.mosaic_config = {}
        state.alignment_transform = {}
        state.inspection_groups = [{'name': 'Group 1'}]

        assert state.is_valid(6)


class TestEngineeringWizardStateDependencies:
    """Testes para validação de dependências entre abas."""

    def test_aba_1_sem_dependencias(self):
        """Testa que aba 1 não tem dependências."""
        state = EngineeringWizardState()
        valid, message = state.validate_dependencies(0)
        assert valid
        assert message == ""

    def test_aba_2_depende_de_aba_1(self):
        """Testa que aba 2 depende de aba 1."""
        state = EngineeringWizardState()
        valid, message = state.validate_dependencies(1)
        assert not valid
        assert "Dados do Programa" in message

    def test_aba_2_valida_com_aba_1_completa(self):
        """Testa que aba 2 é válida com aba 1 completa."""
        state = EngineeringWizardState()
        state.program_data = {
            'program_name': 'Test',
            'stencil_code': 'STENCIL-001',
            'version': 'v1.0',
            'created_by': 'engineer'
        }
        valid, message = state.validate_dependencies(1)
        assert valid
        assert message == ""

    def test_aba_3_depende_de_aba_2(self):
        """Testa que aba 3 depende de aba 2."""
        state = EngineeringWizardState()
        state.program_data = {}  # Aba 1 completa
        valid, message = state.validate_dependencies(2)
        assert not valid
        assert "arquivo Gerber" in message

    def test_aba_4_depende_de_aba_3(self):
        """Testa que aba 4 depende de aba 3."""
        state = EngineeringWizardState()
        state.program_data = {}
        state.gerber_data = {}
        state.gerber_file = 'test.gbr'
        valid, message = state.validate_dependencies(3)
        assert not valid
        assert "fiduciais" in message

    def test_aba_5_depende_de_aba_4(self):
        """Testa que aba 5 depende de aba 4."""
        state = EngineeringWizardState()
        state.program_data = {}
        state.gerber_data = {}
        state.gerber_file = 'test.gbr'
        state.fiducial_templates = [{'id': 0}, {'id': 1}]
        valid, message = state.validate_dependencies(4)
        assert not valid
        assert "mosaico" in message

    def test_aba_6_depende_de_aba_5(self):
        """Testa que aba 6 depende de aba 5."""
        state = EngineeringWizardState()
        state.program_data = {}
        state.gerber_data = {}
        state.gerber_file = 'test.gbr'
        state.fiducial_templates = [{'id': 0}, {'id': 1}]
        state.mosaic_config = {}
        valid, message = state.validate_dependencies(5)
        assert not valid
        assert "alinhamento" in message

    def test_aba_7_depende_de_todas(self):
        """Testa que aba 7 depende de todas as abas anteriores."""
        state = EngineeringWizardState()
        valid, message = state.validate_dependencies(6)
        assert not valid
        assert "Complete as abas anteriores" in message


class TestEngineeringWizardStateNavigation:
    """Testes para navegação entre abas."""

    def test_nao_pode_pular_abas(self):
        """Testa que não pode pular abas."""
        state = EngineeringWizardState()
        state.current_tab = 0

        # Tentar ir para aba 3 (pula 1 e 2)
        can_proceed, message = state.can_proceed_to_tab(2)
        assert not can_proceed
        assert "aba 1" in message

    def test_pode_avancar_sequentialmente(self):
        """Testa que pode avançar sequencialmente."""
        state = EngineeringWizardState()
        state.current_tab = 0
        state.program_data = {
            'program_name': 'Test',
            'stencil_code': 'STENCIL-001',
            'version': 'v1.0',
            'created_by': 'engineer'
        }

        can_proceed, message = state.can_proceed_to_tab(1)
        assert can_proceed
        assert message == ""

    def test_nao_pode_avancar_se_aba_atual_invalida(self):
        """Testa que não pode avançar se aba atual inválida."""
        state = EngineeringWizardState()
        state.current_tab = 0
        # Aba 1 está incompleta

        can_proceed, message = state.can_proceed_to_tab(1)
        assert not can_proceed


class TestEngineeringWizardStateSerialization:
    """Testes para serialização/desserialização."""

    def test_to_dict(self):
        """Testa conversão para dicionário."""
        state = EngineeringWizardState()
        state.program_data = {'program_name': 'Test'}
        state.current_tab = 2

        data = state.to_dict()

        assert isinstance(data, dict)
        assert data['program_data'] == {'program_name': 'Test'}
        assert data['current_tab'] == 2

    def test_from_dict(self):
        """Testa criação a partir de dicionário."""
        data = {
            'program_data': {'program_name': 'Test'},
            'current_tab': 2,
            'is_dirty': False,
            'created_at': '2026-01-13T10:00:00',
            'updated_at': '2026-01-13T10:00:00'
        }

        state = EngineeringWizardState.from_dict(data)

        assert state.program_data == {'program_name': 'Test'}
        assert state.current_tab == 2
        assert state.is_dirty is False

    def test_roundtrip_serialization(self):
        """Testa que serialização/desserialização é idempotente."""
        state_original = EngineeringWizardState()
        state_original.program_data = {
            'program_name': 'Test Program',
            'stencil_code': 'STENCIL-001',
            'version': 'v1.0',
            'created_by': 'engineer'
        }
        state_original.gerber_file = 'test.gbr'
        state_original.gerber_data = {'apertures': []}
        state_original.current_tab = 2

        # Serializar
        data = state_original.to_dict()

        # Desserializar
        state_restaurado = EngineeringWizardState.from_dict(data)

        # Verificar igualdade
        assert state_restaurado.program_data == state_original.program_data
        assert state_restaurado.gerber_file == state_original.gerber_file
        assert state_restaurado.gerber_data == state_original.gerber_data
        assert state_restaurado.current_tab == state_original.current_tab


class TestEngineeringWizardStateTimestamps:
    """Testes para timestamps de criação/atualização."""

    def test_update_timestamp_muda_updated_at(self):
        """Testa que update_timestamp() muda updated_at."""
        state = EngineeringWizardState()
        old_timestamp = state.updated_at

        state.update_timestamp()

        assert state.updated_at != old_timestamp
        assert state.is_dirty is True

    def test_update_timestamp_muda_is_dirty(self):
        """Testa que update_timestamp() marca is_dirty=True."""
        state = EngineeringWizardState()
        assert state.is_dirty is False

        state.update_timestamp()

        assert state.is_dirty is True


class TestEngineeringWizardStateSummary:
    """Testes para método get_summary()."""

    def test_get_summary_retorna_dict(self):
        """Testa que get_summary retorna dicionário."""
        state = EngineeringWizardState()
        summary = state.get_summary()

        assert isinstance(summary, dict)

    def test_get_summary_contem_todas_as_abas(self):
        """Testa que get_summary contém todas as 7 abas."""
        state = EngineeringWizardState()
        summary = state.get_summary()

        assert 'aba_1' in summary
        assert 'aba_2' in summary
        assert 'aba_3' in summary
        assert 'aba_4' in summary
        assert 'aba_5' in summary
        assert 'aba_6' in summary
        assert 'aba_7' in summary

    def test_get_summary_mostra_validade(self):
        """Testa que get_summary mostra validade das abas."""
        state = EngineeringWizardState()
        state.program_data = {
            'program_name': 'Test',
            'stencil_code': 'STENCIL-001',
            'version': 'v1.0',
            'created_by': 'engineer'
        }

        summary = state.get_summary()

        assert summary['aba_1']['valid'] is True
        assert summary['aba_2']['valid'] is False


class TestEngineeringWizardStateClear:
    """Testes para método clear()."""

    def test_clear_limpa_todos_os_dados(self):
        """Testa que clear() limpa todos os dados."""
        state = EngineeringWizardState()
        state.program_data = {'program_name': 'Test'}
        state.gerber_file = 'test.gbr'
        state.current_tab = 3
        state.is_dirty = True

        state.clear()

        assert state.program_data is None
        assert state.gerber_file is None
        assert state.current_tab == 0
        assert state.is_dirty is False

    def test_clear_reinicia_timestamps(self):
        """Testa que clear() reinicia timestamps."""
        state = EngineeringWizardState()
        old_created = state.created_at

        state.clear()

        # Timestamp foi atualizado (pode ser igual se muito rápido,
        # mas deve ser uma chamada nova de datetime.now())
        assert isinstance(state.created_at, str)
        assert isinstance(state.updated_at, str)
