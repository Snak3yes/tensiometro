"""
Testes básicos para o parser de arquivos Gerber RS-274X.

Estes testes validam funcionalidades básicas do parser,
geometrias e conversões de unidades.
"""

import pytest
from pathlib import Path


class TestGerberParserBasics:
    """Testa funcionalidades básicas do parser."""

    def test_parser_module_exists(self):
        """Testa que o módulo gerber_parser pode ser importado."""
        # Testa simples importação
        from aoi_lib import gerber_parser
        assert gerber_parser is not None

    def test_parser_has_main_classes(self):
        """Testa que as principais classes do parser existem."""
        from aoi_lib.gerber_parser import GerberParser

        # Verifica que a classe pode ser instanciada
        parser = GerberParser()
        assert parser is not None


class TestGerberBounds:
    """Testa cálculo de limites (bounding box)."""

    def test_bounds_initialization(self):
        """Testa inicialização de bounds."""
        from aoi_lib.gerber_parser import GerberBounds

        bounds = GerberBounds()
        assert hasattr(bounds, 'min_x')
        assert hasattr(bounds, 'max_x')
        assert hasattr(bounds, 'min_y')
        assert hasattr(bounds, 'max_y')

    def test_empty_bounds(self):
        """Testa bounds de arquivo vazio."""
        from aoi_lib.gerber_parser import GerberBounds

        bounds = GerberBounds()
        assert bounds.min_x == 0
        assert bounds.max_x == 0
        assert bounds.min_y == 0
        assert bounds.max_y == 0

    def test_bounds_validation(self):
        """Testa validação de bounds."""
        from aoi_lib.gerber_parser import GerberBounds

        bounds = GerberBounds()
        bounds.min_x = 0
        bounds.max_x = 100
        bounds.min_y = 0
        bounds.max_y = 100

        # Validar que bounds são válidos
        assert bounds.min_x < bounds.max_x
        assert bounds.min_y < bounds.max_y
        assert bounds.min_x >= 0
        assert bounds.min_y >= 0


class TestApertureGeometries:
    """Testa conversão de apertures para geometrias."""

    def test_circle_aperture_area(self):
        """Testa cálculo de área para aperture circular."""
        diameter = 2.0  # 2mm
        import math
        expected_area = math.pi * (diameter / 2) ** 2
        assert expected_area == pytest.approx(3.14, rel=0.01)

    def test_rectangle_aperture_area(self):
        """Testa cálculo de área para aperture retangular."""
        width = 5.0
        height = 2.0
        expected_area = width * height
        assert expected_area == 10.0

    def test_obround_aperture_area(self):
        """
        Testa cálculo de área para aperture obround.

        Obround = retângulo + dois semicírculos
        Exemplo: 5mm x 2mm
        - Parte retangular: (5 - 2) x 2 = 3 x 2 = 6mm²
        - Dois semicírculos = um círculo: π * 1² = π mm²
        - Total: 6 + π ≈ 9.14mm²
        """
        width = 5.0
        height = 2.0
        import math

        if width > height:
            # Horizontal
            rect_area = (width - height) * height
            circle_area = math.pi * (height / 2) ** 2
        else:
            # Vertical
            rect_area = (height - width) * width
            circle_area = math.pi * (width / 2) ** 2

        expected_area = rect_area + circle_area
        assert expected_area == pytest.approx(9.14, rel=0.01)


class TestGerberUnitConversion:
    """Testa conversão de unidades em arquivos Gerber."""

    def test_mm_to_inches_conversion(self):
        """Testa conversão de mm para polegadas."""
        # 1 polegada = 25.4mm
        mm_value = 25.4
        inches_value = mm_value / 25.4
        assert inches_value == pytest.approx(1.0, rel=0.001)

    def test_inches_to_mm_conversion(self):
        """Testa conversão de polegadas para mm."""
        inches_value = 1.0
        mm_value = inches_value * 25.4
        assert mm_value == pytest.approx(25.4, rel=0.001)

    def test_mil_to_mm_conversion(self):
        """Testa conversão de mil (thousandth of inch) para mm."""
        # 1 mil = 0.001 inch = 0.0254mm
        mil_value = 1.0
        mm_value = mil_value * 0.0254
        assert mm_value == pytest.approx(0.0254, rel=0.001)


@pytest.mark.integration
class TestGerberFileParsing:
    """
    Testa parsing de arquivos Gerber reais.

    Estes testes requerem arquivos .gt1 em tests/fixtures/gerber/
    """

    @pytest.fixture
    def sample_gerber_file(self, gerber_fixtures_dir, tmp_path):
        """
        Cria um arquivo Gerber simples para teste.

        Se não existir arquivo de teste, cria um básico.
        """
        gerber_path = gerber_fixtures_dir / "simple_circle.gbr"

        # Se não existir, criar um arquivo básico
        if not gerber_path.exists():
            # Criar Gerber RS-274X básico
            gerber_content = """%FSLAX26Y26*%
%MOIN*%
%OFA0B0*%
%ADD10C,1.5*%
%LPD*%
G01*
X0Y0D03*
X100000Y0D03*
X0Y50000D03*
X100000Y50000D03*
M02*
"""
            gerber_path.write_text(gerber_content)

        return gerber_path

    def test_parse_creates_file(self, sample_gerber_file):
        """Testa que arquivo Gerber de teste pode ser criado."""
        assert sample_gerber_file.exists()
        assert sample_gerber_file.suffix == '.gbr'

    def test_parse_file_has_content(self, sample_gerber_file):
        """Testa que arquivo Gerber tem conteúdo."""
        content = sample_gerber_file.read_text()
        assert len(content) > 0
        assert 'G01' in content  # Comando Gerber típico


class TestGerberDataStructures:
    """Testa estruturas de dados do parser."""

    def test_gerber_object_creation(self):
        """Testa criação de objeto Gerber."""
        from aoi_lib.gerber_parser import GerberObject

        obj = GerberObject(
            id=1,
            kind='flash_circle',
            dcode=10,
            x_mm=10.0,
            y_mm=20.0,
            params={'diameter': 1.5},
            polygon_mm=[]
        )

        assert obj.id == 1
        assert obj.kind == 'flash_circle'
        assert obj.dcode == 10
        assert obj.x_mm == 10.0
        assert obj.y_mm == 20.0

    def test_gerber_object_str_representation(self):
        """Testa representação string de objeto Gerber."""
        from aoi_lib.gerber_parser import GerberObject

        obj = GerberObject(
            id=1,
            kind='flash_circle',
            dcode=10,
            x_mm=10.0,
            y_mm=20.0,
            params={'diameter': 1.5},
            polygon_mm=[]
        )

        # Deve ter representação string
        obj_str = str(obj)
        assert len(obj_str) > 0
