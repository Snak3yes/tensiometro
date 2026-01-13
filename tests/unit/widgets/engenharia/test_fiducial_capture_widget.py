"""
Testes unitários para FiducialCaptureWidget (Aba 3)
"""

import pytest
import numpy as np
from consumo_lib.widgets.engenharia.fiducial_capture_widget import (
    FiducialCaptureWidget, FiducialTemplate
)


class TestFiducialCaptureWidget:
    """Testes para FiducialCaptureWidget."""

    def test_widget_creation(self, qapp):
        """Testa criação do widget."""
        widget = FiducialCaptureWidget()
        assert widget is not None
        assert not widget.is_valid()

    def test_get_fiducial_templates_empty(self, qapp):
        """Testa get_fiducial_templates() sem capturas."""
        widget = FiducialCaptureWidget()
        templates = widget.get_fiducial_templates()
        assert len(templates) == 0

    def test_initial_state(self, qapp):
        """Testa estado inicial."""
        widget = FiducialCaptureWidget()
        assert widget._current_fiducial_id == 0  # Fiducial 1 selecionado
        assert widget._window_size == 50

    def test_clear(self, qapp):
        """Testa limpeza das capturas."""
        widget = FiducialCaptureWidget()
        # Simular captura (não podemos testar sem hardware real)
        widget.clear()
        assert len(widget._fiducials) == 0


class TestFiducialTemplate:
    """Testes para dataclass FiducialTemplate."""

    def test_creation(self):
        """Testa criação de FiducialTemplate."""
        template = FiducialTemplate(
            id=0,
            x=10.0,
            y=20.0,
            z=5.0,
            image=np.zeros((50, 50)),
            window_size=50
        )
        assert template.id == 0
        assert template.x == 10.0
        assert template.window_size == 50

    def test_to_dict(self):
        """Testa conversão para dicionário."""
        template = FiducialTemplate(
            id=0,
            x=10.0,
            y=20.0,
            z=5.0,
            image=np.zeros((50, 50)),
            window_size=50,
            captured_at="2026-01-13"
        )
        dict_data = template.to_dict()
        assert dict_data['id'] == 0
        assert dict_data['x'] == 10.0
        assert dict_data['window_size'] == 50
        # Imagem não deve estar no dict (serialização problemática)
        assert 'image' not in dict_data
