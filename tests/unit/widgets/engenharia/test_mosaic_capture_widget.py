"""
Testes unitários para MosaicCaptureWidget (Aba 4)
"""

import pytest
from consumo_lib.widgets.engenharia.mosaic_capture_widget import (
    MosaicCaptureWidget, MosaicConfig
)


class TestMosaicCaptureWidget:
    """Testes para MosaicCaptureWidget."""

    def test_widget_creation(self, qapp):
        """Testa criação do widget."""
        widget = MosaicCaptureWidget()
        assert widget is not None
        assert not widget.is_valid()

    def test_get_mosaic_data_empty(self, qapp):
        """Testa get_mosaic_data() sem captura."""
        widget = MosaicCaptureWidget()
        data = widget.get_mosaic_data()
        assert data == {}

    def test_default_values(self, qapp):
        """Testa valores padrão dos campos."""
        widget = MosaicCaptureWidget()
        assert widget.spin_x1.value() == 0
        assert widget.spin_y1.value() == 0
        assert widget.spin_x2.value() == 100
        assert widget.spin_y2.value() == 50
        assert widget.spin_rows.value() == 5
        assert widget.spin_cols.value() == 5


class TestMosaicConfig:
    """Testes para dataclass MosaicConfig."""

    def test_creation(self):
        """Testa criação de MosaicConfig."""
        config = MosaicConfig(
            x1=0.0,
            y1=0.0,
            x2=100.0,
            y2=50.0,
            rows=5,
            cols=5,
            overlap_percent=10.0,
            delay_ms=200
        )
        assert config.x1 == 0.0
        assert config.rows == 5
        assert config.overlap_percent == 10.0

    def test_to_dict(self):
        """Testa conversão para dicionário."""
        config = MosaicConfig(
            x1=0.0,
            y1=0.0,
            x2=100.0,
            y2=50.0,
            rows=5,
            cols=5
        )
        dict_data = config.to_dict()
        assert dict_data['x1'] == 0.0
        assert dict_data['rows'] == 5
        assert dict_data['overlap_percent'] == 10.0
