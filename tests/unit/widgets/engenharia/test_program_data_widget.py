"""
Testes unitários para ProgramDataWidget (Aba 1)
"""

import pytest
from consumo_lib.widgets.engenharia.program_data_widget import ProgramDataWidget, ProgramData


class TestProgramDataWidget:
    """Testes para ProgramDataWidget."""

    def test_widget_creation(self, qapp):
        """Testa criação do widget."""
        widget = ProgramDataWidget()
        assert widget is not None
        assert not widget.is_valid()

    def test_default_values(self, qapp):
        """Testa valores padrão dos campos."""
        widget = ProgramDataWidget()
        assert widget.field_version.text() == "v1.0"
        assert widget.field_creator.text() == "engineer"

    def test_get_data_empty(self, qapp):
        """Testa get_data() com campos vazios."""
        widget = ProgramDataWidget()
        data = widget.get_data()
        assert data['program_name'] == ""
        assert data['stencil_code'] == ""
        assert data['version'] == "v1.0"
        assert 'created_at' in data

    def test_set_and_get_data(self, qapp):
        """Testa set_data() e get_data()."""
        widget = ProgramDataWidget()
        test_data = {
            'program_name': 'Test Program',
            'stencil_code': 'STENCIL-123',
            'description': 'Test description',
            'version': 'v2.0',
            'created_by': 'test_user'
        }
        widget.set_data(test_data)
        data = widget.get_data()
        assert data['program_name'] == 'Test Program'
        assert data['stencil_code'] == 'STENCIL-123'
        assert data['description'] == 'Test description'

    def test_validation_empty_fields(self, qapp):
        """Testa validação com campos vazios."""
        widget = ProgramDataWidget()
        assert not widget.is_valid()

    def test_validation_valid_data(self, qapp):
        """Testa validação com dados válidos."""
        widget = ProgramDataWidget()
        widget.field_name.setText("Test Program")
        widget.field_stencil.setText("STENCIL-123")
        # version e creator já têm valores padrão válidos
        assert widget.is_valid()

    def test_clear(self, qapp):
        """Testa limpeza dos campos."""
        widget = ProgramDataWidget()
        widget.field_name.setText("Test")
        widget.field_stencil.setText("TEST-123")
        widget.clear()
        assert widget.field_name.text() == ""
        assert widget.field_stencil.text() == ""
        assert widget.field_version.text() == "v1.0"


class TestProgramData:
    """Testes para dataclass ProgramData."""

    def test_creation(self):
        """Testa criação de ProgramData."""
        data = ProgramData(
            program_name="Test",
            stencil_code="STENCIL-123",
            description="Desc",
            version="v1.0",
            created_by="user",
            created_at="2026-01-13"
        )
        assert data.program_name == "Test"
        assert data.stencil_code == "STENCIL-123"

    def test_to_dict(self):
        """Testa conversão para dicionário."""
        data = ProgramData(
            program_name="Test",
            stencil_code="STENCIL-123",
            description="Desc",
            version="v1.0",
            created_by="user",
            created_at="2026-01-13"
        )
        dict_data = data.to_dict()
        assert dict_data['program_name'] == "Test"
        assert 'created_at' in dict_data

    def test_from_dict(self):
        """Testa criação a partir de dicionário."""
        dict_data = {
            'program_name': "Test",
            'stencil_code': "STENCIL-123",
            'description': "Desc",
            'version': "v1.0",
            'created_by': "user",
            'created_at': "2026-01-13"
        }
        data = ProgramData.from_dict(dict_data)
        assert data.program_name == "Test"
