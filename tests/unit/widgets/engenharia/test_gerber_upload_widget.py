"""
Testes unitários para GerberUploadWidget (Aba 2)
"""

import pytest
from pathlib import Path
from consumo_lib.widgets.engenharia.gerber_upload_widget import GerberUploadWidget, GerberMetadata


class TestGerberUploadWidget:
    """Testes para GerberUploadWidget."""

    def test_widget_creation(self, qapp):
        """Testa criação do widget."""
        widget = GerberUploadWidget()
        assert widget is not None
        assert not widget.is_valid()

    def test_get_gerber_data_empty(self, qapp):
        """Testa get_gerber_data() sem arquivo carregado."""
        widget = GerberUploadWidget()
        data = widget.get_gerber_data()
        assert data == {}

    def test_preview_widget_creation(self, qapp):
        """Testa criação do widget de preview."""
        from consumo_lib.widgets.engenharia.gerber_upload_widget import GerberPreviewWidget
        preview = GerberPreviewWidget()
        assert preview is not None


class TestGerberMetadata:
    """Testes para dataclass GerberMetadata."""

    def test_creation(self):
        """Testa criação de GerberMetadata."""
        metadata = GerberMetadata(
            file_path="/path/to/file.gbr",
            file_name="file.gbr",
            file_size=1024,
            dimensions=(100.0, 50.0),
            aperture_count=50,
            fiducial_count=2,
            fiducial_positions=[{'x': 0, 'y': 0, 'd': 1.5}]
        )
        assert metadata.file_name == "file.gbr"
        assert metadata.aperture_count == 50

    def test_to_dict(self):
        """Testa conversão para dicionário."""
        metadata = GerberMetadata(
            file_path="/path/to/file.gbr",
            file_name="file.gbr",
            file_size=1024,
            dimensions=(100.0, 50.0),
            aperture_count=50,
            fiducial_count=2,
            fiducial_positions=[{'x': 0, 'y': 0, 'd': 1.5}]
        )
        dict_data = metadata.to_dict()
        assert dict_data['file_name'] == "file.gbr"
        assert dict_data['aperture_count'] == 50
        assert 'dimensions' in dict_data
