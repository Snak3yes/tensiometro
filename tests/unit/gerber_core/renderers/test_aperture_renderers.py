"""
Testes Unitários para Aperture Renderers

Este módulo contém testes unitários para todos os renderizadores de aperture,
seguindo o padrão Arrange-Act-Assert.

Cobertura de testes:
    - CircleRenderer: testes para renderização de círculos
    - RectangleRenderer: testes para renderização de retângulos
    - ObroundRenderer: testes para renderização de obrounds
    - MacroRenderer: testes para renderização de macros
    - RegionRenderer: testes para renderização de regiões
    - create_aperture_renderer: testes para Factory Function

Author: Claude Sonnet 4.5
Date: 2026-01-14
Track: solid_refactoring_phase2_20260114 (Phase 2 - Parser Refactoring)
"""

import pytest
from aoi_lib.gerber_core.apertures import ApertureInstance, ApertureMacro
from aoi_lib.gerber_core.renderers import (
    ApertureRenderer,
    CircleRenderer,
    RectangleRenderer,
    ObroundRenderer,
    MacroRenderer,
    RegionRenderer,
    create_aperture_renderer,
)


class TestCircleRenderer:
    """Testes para CircleRenderer."""

    def test_render_circle_valid(self):
        """Testa renderização de círculo com parâmetros válidos."""
        # Arrange
        renderer = CircleRenderer()
        aperture = ApertureInstance(
            kind="circle",
            dia_mm=1.5,
        )

        # Act
        polys, objects = renderer.render(x_mm=0.0, y_mm=0.0, dcode=10, aperture=aperture)

        # Assert
        assert len(polys) == 1
        assert len(objects) == 1
        assert objects[0].kind == "flash_circle"
        assert objects[0].params["dia_mm"] == 1.5
        assert objects[0].x_mm == 0.0
        assert objects[0].y_mm == 0.0
        assert objects[0].dcode == 10
        assert len(polys[0]) > 10  # Círculo aproximado por muitos pontos

    def test_render_circle_missing_dia_mm(self):
        """Testa que círculo sem dia_mm levanta ValueError."""
        # Arrange
        renderer = CircleRenderer()
        aperture = ApertureInstance(
            kind="circle",
        )

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            renderer.render(x_mm=0.0, y_mm=0.0, dcode=10, aperture=aperture)

        assert "missing 'dia_mm' parameter" in str(exc_info.value)

    def test_render_circle_invalid_dia_mm(self):
        """Testa que diâmetro inválido levanta ValueError."""
        # Arrange
        renderer = CircleRenderer()
        aperture = ApertureInstance(
            kind="circle",
            dia_mm="invalid",
        )

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            renderer.render(x_mm=0.0, y_mm=0.0, dcode=10, aperture=aperture)

        assert "Invalid dia_mm value" in str(exc_info.value)

    def test_render_circle_negative_diameter(self):
        """Testa que diâmetro negativo levanta ValueError."""
        # Arrange
        renderer = CircleRenderer()
        aperture = ApertureInstance(
            kind="circle",
            dia_mm=-1.5,
        )

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            renderer.render(x_mm=0.0, y_mm=0.0, dcode=10, aperture=aperture)

        assert "must be > 0" in str(exc_info.value)

    def test_render_circle_zero_diameter(self):
        """Testa que diâmetro zero levanta ValueError."""
        # Arrange
        renderer = CircleRenderer()
        aperture = ApertureInstance(
            kind="circle",
            dia_mm=0.0,
        )

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            renderer.render(x_mm=0.0, y_mm=0.0, dcode=10, aperture=aperture)

        assert "must be > 0" in str(exc_info.value)

    def test_render_circle_at_different_position(self):
        """Testa renderização de círculo em posição diferente."""
        # Arrange
        renderer = CircleRenderer()
        aperture = ApertureInstance(
            kind="circle",
            dia_mm=2.0,
        )

        # Act
        polys, objects = renderer.render(x_mm=5.0, y_mm=3.0, dcode=10, aperture=aperture)

        # Assert
        assert objects[0].x_mm == 5.0
        assert objects[0].y_mm == 3.0
        # Polígono deve estar centrado em (5.0, 3.0)
        assert polys[0][0][0] == pytest.approx(5.0, abs=1.1)  # X ± diâmetro
        assert polys[0][0][1] == pytest.approx(3.0, abs=1.1)  # Y ± diâmetro


class TestRectangleRenderer:
    """Testes para RectangleRenderer."""

    def test_render_rectangle_valid(self):
        """Testa renderização de retângulo com parâmetros válidos."""
        # Arrange
        renderer = RectangleRenderer()
        aperture = ApertureInstance(
            kind="rect",
            width_mm=2.0,
            height_mm=1.0,
        )

        # Act
        polys, objects = renderer.render(x_mm=0.0, y_mm=0.0, dcode=11, aperture=aperture)

        # Assert
        assert len(polys) == 1
        assert len(objects) == 1
        assert objects[0].kind == "flash_rect"
        assert objects[0].params["width_mm"] == 2.0
        assert objects[0].params["height_mm"] == 1.0
        assert objects[0].dcode == 11
        assert len(polys[0]) == 5  # Retângulo tem 4 vértices + fechamento

    def test_render_rectangle_missing_width(self):
        """Testa que retângulo sem width_mm levanta ValueError."""
        # Arrange
        renderer = RectangleRenderer()
        aperture = ApertureInstance(
            kind="rect",
            height_mm=1.0,
        )

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            renderer.render(x_mm=0.0, y_mm=0.0, dcode=11, aperture=aperture)

        assert "missing 'width_mm' or 'height_mm' parameter" in str(exc_info.value)

    def test_render_rectangle_negative_dimensions(self):
        """Testa que dimensões negativas levantam ValueError."""
        # Arrange
        renderer = RectangleRenderer()
        aperture = ApertureInstance(
            kind="rect",
            width_mm=-2.0,
            height_mm=1.0,
        )

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            renderer.render(x_mm=0.0, y_mm=0.0, dcode=11, aperture=aperture)

        assert "must be > 0" in str(exc_info.value)


class TestObroundRenderer:
    """Testes para ObroundRenderer."""

    def test_render_obround_valid(self):
        """Testa renderização de obround com parâmetros válidos."""
        # Arrange
        renderer = ObroundRenderer()
        aperture = ApertureInstance(
            kind="oval",
            width_mm=3.0,
            height_mm=2.0,
        )

        # Act
        polys, objects = renderer.render(x_mm=0.0, y_mm=0.0, dcode=12, aperture=aperture)

        # Assert
        assert len(polys) == 1
        assert len(objects) == 1
        assert objects[0].kind == "flash_oval"
        assert objects[0].params["width_mm"] == 3.0
        assert objects[0].params["height_mm"] == 2.0
        assert objects[0].dcode == 12
        assert len(polys[0]) > 10  # Obround tem muitos pontos

    def test_render_obround_missing_dimensions(self):
        """Testa que obround sem dimensões levanta ValueError."""
        # Arrange
        renderer = ObroundRenderer()
        aperture = ApertureInstance(
            kind="oval",
            width_mm=3.0,
        )

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            renderer.render(x_mm=0.0, y_mm=0.0, dcode=12, aperture=aperture)

        assert "missing 'width_mm' or 'height_mm' parameter" in str(exc_info.value)


class TestMacroRenderer:
    """Testes para MacroRenderer."""

    def test_render_macro_valid(self, mock_macro):
        """Testa renderização de macro com parâmetros válidos."""
        # Arrange
        renderer = MacroRenderer()
        renderer.set_macros({"test_macro": mock_macro})
        aperture = ApertureInstance(
            kind="macro",
            macro_name="test_macro",
        )

        # Act
        polys, objects = renderer.render(x_mm=0.0, y_mm=0.0, dcode=13, aperture=aperture)

        # Assert
        assert len(polys) == 1
        assert len(objects) == 1
        assert objects[0].kind == "flash_macro"
        assert objects[0].params["macro_name"] == "test_macro"
        assert objects[0].dcode == 13

    def test_render_macro_missing_name(self):
        """Testa que macro sem nome levanta ValueError."""
        # Arrange
        renderer = MacroRenderer()
        aperture = ApertureInstance(
            kind="macro",
        )

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            renderer.render(x_mm=0.0, y_mm=0.0, dcode=13, aperture=aperture)

        assert "missing 'macro_name' parameter" in str(exc_info.value)

    def test_render_macro_not_found(self):
        """Testa que macro inexistente levanta ValueError."""
        # Arrange
        renderer = MacroRenderer()
        renderer.set_macros({})  # Nenhuma macro disponível
        aperture = ApertureInstance(
            kind="macro",
            macro_name="nonexistent",
        )

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            renderer.render(x_mm=0.0, y_mm=0.0, dcode=13, aperture=aperture)

        assert "Macro not found" in str(exc_info.value)

    def test_render_macro_invalid_name_type(self):
        """Testa que nome de macro inválido levanta ValueError."""
        # Arrange
        renderer = MacroRenderer()
        aperture = ApertureInstance(
            kind="macro",
            macro_name=123,  # Deveria ser string
        )

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            renderer.render(x_mm=0.0, y_mm=0.0, dcode=13, aperture=aperture)

        assert "must be string" in str(exc_info.value)


class TestRegionRenderer:
    """Testes para RegionRenderer."""

    def test_render_region_valid(self):
        """Testa renderização de região com polígono válido."""
        # Arrange
        renderer = RegionRenderer()
        polygon = [(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)]
        renderer.set_polygon(polygon)
        aperture = ApertureInstance(
            kind="region",
        )

        # Act
        polys, objects = renderer.render(x_mm=5.0, y_mm=5.0, dcode=0, aperture=aperture)

        # Assert
        assert len(polys) == 1
        assert len(objects) == 1
        assert objects[0].kind == "region"
        assert polys[0] == polygon

    def test_render_region_missing_polygon(self):
        """Testa que região sem polígono levanta ValueError."""
        # Arrange
        renderer = RegionRenderer()
        # NÃO chamar set_polygon()
        aperture = ApertureInstance(
            kind="region",
        )

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            renderer.render(x_mm=0.0, y_mm=0.0, dcode=0, aperture=aperture)

        assert "not set" in str(exc_info.value).lower()

    def test_render_region_insufficient_points(self):
        """Testa que região com <3 pontos levanta ValueError."""
        # Arrange
        renderer = RegionRenderer()
        polygon = [(0, 0), (10, 0)]  # Apenas 2 pontos
        renderer.set_polygon(polygon)
        aperture = ApertureInstance(
            kind="region",
        )

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            renderer.render(x_mm=0.0, y_mm=0.0, dcode=0, aperture=aperture)

        assert "at least 3 points" in str(exc_info.value)


class TestCreateApertureRenderer:
    """Testes para Factory Function create_aperture_renderer."""

    def test_factory_circle(self):
        """Testa factory function para circle."""
        # Arrange
        aperture = ApertureInstance(
            kind="circle",
            dia_mm=1.5,
        )

        # Act
        renderer = create_aperture_renderer(aperture)

        # Assert
        assert renderer is not None
        assert isinstance(renderer, CircleRenderer)

    def test_factory_rectangle(self):
        """Testa factory function para rect."""
        # Arrange
        aperture = ApertureInstance(
            kind="rect",
            width_mm=2.0,
            height_mm=1.0,
        )

        # Act
        renderer = create_aperture_renderer(aperture)

        # Assert
        assert renderer is not None
        assert isinstance(renderer, RectangleRenderer)

    def test_factory_obround(self):
        """Testa factory function para oval."""
        # Arrange
        aperture = ApertureInstance(
            kind="oval",
            width_mm=3.0,
            height_mm=2.0,
        )

        # Act
        renderer = create_aperture_renderer(aperture)

        # Assert
        assert renderer is not None
        assert isinstance(renderer, ObroundRenderer)

    def test_factory_macro(self, mock_macro):
        """Testa factory function para macro."""
        # Arrange
        aperture = ApertureInstance(
            kind="macro",
            macro_name="test_macro",
        )
        macros = {"test_macro": mock_macro}

        # Act
        renderer = create_aperture_renderer(aperture, macros=macros)

        # Assert
        assert renderer is not None
        assert isinstance(renderer, MacroRenderer)

    def test_factory_region(self):
        """Testa factory function para region."""
        # Arrange
        aperture = ApertureInstance(
            kind="region",
        )

        # Act
        renderer = create_aperture_renderer(aperture)

        # Assert
        assert renderer is not None
        assert isinstance(renderer, RegionRenderer)

    def test_factory_unsupported_kind(self):
        """Testa factory function para tipo não suportado."""
        # Arrange
        aperture = ApertureInstance(
            kind="unknown_type",
        )

        # Act
        renderer = create_aperture_renderer(aperture)

        # Assert
        assert renderer is None

    def test_factory_macro_without_macros(self, mock_macro):
        """Testa que macro sem dicionário macros retorna None."""
        # Arrange
        aperture = ApertureInstance(
            kind="macro",
            macro_name="test_macro",
        )

        # Act - NÃO passar macros
        renderer = create_aperture_renderer(aperture, macros=None)

        # Assert
        assert renderer is None


# Fixtures
@pytest.fixture
def mock_macro():
    """Cria um mock de ApertureMacro para testes."""
    macro = ApertureMacro(name="test_macro")
    # Mock do método render para retornar um polígono simples
    def mock_render(scale_x, scale_y, rot_deg, trans):
        tx, ty = trans
        return [[(tx, ty), (tx + 1, ty), (tx + 1, ty + 1), (tx, ty + 1), (tx, ty)]]

    macro.render = mock_render
    return macro
