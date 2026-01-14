"""
Testes unitários para ParserEditCommands.

Testa Command Pattern aplicado à estrutura parser.GerberObject.
"""
from __future__ import annotations

import pytest
import sys
from pathlib import Path

# Adiciona path para importar parser
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "poc_gerber"))

from aoi_lib.gerber_core.parser import GerberObject
from aoi_lib.gerber_core.commands.parser_edit_commands import (
    ParserEditCircleCommand,
    ParserEditRectangleCommand,
    ParserEditObroundCommand,
    ParserEditRegionCommand,
    create_parser_edit_command,
)


class TestParserEditCircleCommand:
    """Testes para ParserEditCircleCommand."""

    def test_edit_circle_diameter(self):
        """Testa edição de diâmetro de círculo."""
        obj = GerberObject(id=0,
            kind="flash_circle",
            dcode=10,
            x_mm=0.0,
            y_mm=0.0,
            params={"dia_mm": 5.0},
            polygon_mm=[(0.0, 2.5), (2.5, 0.0), (0.0, -2.5), (-2.5, 0.0)]
        )

        command = ParserEditCircleCommand(obj)
        modified = command.execute(new_dia_mm=10.0)

        assert modified.params["dia_mm"] == 10.0
        assert modified.x_mm == 0.0
        assert modified.y_mm == 0.0
        assert modified.polygon_mm is not None
        assert len(modified.polygon_mm) > 0

    def test_edit_circle_position(self):
        """Testa translação de círculo."""
        obj = GerberObject(id=0,
            kind="flash_circle",
            dcode=10,
            x_mm=0.0,
            y_mm=0.0,
            params={"dia_mm": 5.0},
            polygon_mm=[(0.0, 2.5), (2.5, 0.0), (0.0, -2.5), (-2.5, 0.0)]
        )

        command = ParserEditCircleCommand(obj)
        modified = command.execute(dx=5.0, dy=3.0)

        assert modified.x_mm == 5.0
        assert modified.y_mm == 3.0
        assert modified.params["dia_mm"] == 5.0  # Diâmetro inalterado

    def test_edit_circle_invalid_diameter(self):
        """Testa que diâmetro inválido levanta exceção."""
        obj = GerberObject(id=0,
            kind="flash_circle",
            dcode=10,
            x_mm=0.0,
            y_mm=0.0,
            params={"dia_mm": 5.0},
            polygon_mm=[]
        )

        command = ParserEditCircleCommand(obj)

        with pytest.raises(ValueError) as exc_info:
            command.execute(new_dia_mm=-5.0)

        assert "Diâmetro deve ser > 0" in str(exc_info.value)

    def test_edit_circle_combined(self):
        """Testa edição combinada (diâmetro + posição)."""
        obj = GerberObject(id=0,
            kind="flash_circle",
            dcode=10,
            x_mm=0.0,
            y_mm=0.0,
            params={"dia_mm": 5.0},
            polygon_mm=[]
        )

        command = ParserEditCircleCommand(obj)
        modified = command.execute(new_dia_mm=8.0, dx=10.0, dy=15.0)

        assert modified.params["dia_mm"] == 8.0
        assert modified.x_mm == 10.0
        assert modified.y_mm == 15.0


class TestParserEditRectangleCommand:
    """Testes para ParserEditRectangleCommand."""

    def test_edit_rectangle_dimensions(self):
        """Testa edição de dimensões de retângulo."""
        obj = GerberObject(id=0,
            kind="flash_rect",
            dcode=11,
            x_mm=0.0,
            y_mm=0.0,
            params={"width_mm": 5.0, "height_mm": 3.0},
            polygon_mm=[]
        )

        command = ParserEditRectangleCommand(obj)
        modified = command.execute(new_width_mm=10.0, new_height_mm=6.0)

        assert modified.params["width_mm"] == 10.0
        assert modified.params["height_mm"] == 6.0

    def test_edit_rectangle_scale(self):
        """Testa escala de retângulo."""
        obj = GerberObject(id=0,
            kind="flash_rect",
            dcode=11,
            x_mm=0.0,
            y_mm=0.0,
            params={"width_mm": 5.0, "height_mm": 3.0},
            polygon_mm=[]
        )

        command = ParserEditRectangleCommand(obj)
        modified = command.execute(scale_x=2.0, scale_y=2.0)

        assert modified.params["width_mm"] == 10.0  # 5.0 * 2.0
        assert modified.params["height_mm"] == 6.0  # 3.0 * 2.0

    def test_edit_rectangle_translation(self):
        """Testa translação de retângulo."""
        obj = GerberObject(id=0,
            kind="flash_rect",
            dcode=11,
            x_mm=0.0,
            y_mm=0.0,
            params={"width_mm": 5.0, "height_mm": 3.0},
            polygon_mm=[]
        )

        command = ParserEditRectangleCommand(obj)
        modified = command.execute(dx=5.0, dy=3.0)

        assert modified.x_mm == 5.0
        assert modified.y_mm == 3.0
        assert modified.params["width_mm"] == 5.0
        assert modified.params["height_mm"] == 3.0

    def test_edit_rectangle_invalid_dimensions(self):
        """Testa que dimensões inválidas levantam exceção."""
        obj = GerberObject(id=0,
            kind="flash_rect",
            dcode=11,
            x_mm=0.0,
            y_mm=0.0,
            params={"width_mm": 5.0, "height_mm": 3.0},
            polygon_mm=[]
        )

        command = ParserEditRectangleCommand(obj)

        with pytest.raises(ValueError) as exc_info:
            command.execute(new_width_mm=-10.0)

        assert "Largura/altura devem ser > 0" in str(exc_info.value)


class TestParserEditObroundCommand:
    """Testes para ParserEditObroundCommand."""

    def test_edit_obround_dimensions(self):
        """Testa edição de dimensões de obround."""
        obj = GerberObject(id=0,
            kind="flash_oval",
            dcode=12,
            x_mm=0.0,
            y_mm=0.0,
            params={"width_mm": 8.0, "height_mm": 4.0},
            polygon_mm=[]
        )

        command = ParserEditObroundCommand(obj)
        modified = command.execute(new_width_mm=12.0, new_height_mm=6.0)

        assert modified.params["width_mm"] == 12.0
        assert modified.params["height_mm"] == 6.0

    def test_edit_obround_scale(self):
        """Testa escala de obround."""
        obj = GerberObject(id=0,
            kind="flash_oval",
            dcode=12,
            x_mm=0.0,
            y_mm=0.0,
            params={"width_mm": 8.0, "height_mm": 4.0},
            polygon_mm=[]
        )

        command = ParserEditObroundCommand(obj)
        modified = command.execute(scale_x=1.5, scale_y=1.5)

        assert modified.params["width_mm"] == 12.0  # 8.0 * 1.5
        assert modified.params["height_mm"] == 6.0  # 4.0 * 1.5


class TestParserEditRegionCommand:
    """Testes para ParserEditRegionCommand."""

    def test_edit_region_scale(self):
        """Testa escala de região."""
        # Quadrado 10x10 centrado em (5, 5)
        polygon = [
            (0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0), (0.0, 0.0)
        ]
        obj = GerberObject(id=0,
            kind="region",
            dcode=0,
            x_mm=5.0,
            y_mm=5.0,
            params={},
            polygon_mm=polygon
        )

        command = ParserEditRegionCommand(obj)
        modified = command.execute(scale_x=2.0, scale_y=2.0)

        # Verificar que polígono foi escalado
        assert modified.polygon_mm is not None
        assert len(modified.polygon_mm) == len(polygon)

        # Centro deve permanecer em (5, 5)
        xs = [p[0] for p in modified.polygon_mm]
        ys = [p[1] for p in modified.polygon_mm]
        cx = (min(xs) + max(xs)) / 2.0
        cy = (min(ys) + max(ys)) / 2.0
        assert abs(cx - 5.0) < 0.01
        assert abs(cy - 5.0) < 0.01

    def test_edit_region_invalid_polygon(self):
        """Testa que polígono inválido levanta exceção."""
        obj = GerberObject(id=0,
            kind="region",
            dcode=0,
            x_mm=0.0,
            y_mm=0.0,
            params={},
            polygon_mm=[]  # Vazio
        )

        command = ParserEditRegionCommand(obj)

        with pytest.raises(ValueError) as exc_info:
            command.execute(scale_x=2.0)

        assert "não possui polígono válido" in str(exc_info.value)


class TestFactoryFunction:
    """Testa Factory Function create_parser_edit_command."""

    def test_factory_circle(self):
        """Testa criação de comando para círculo."""
        obj = GerberObject(id=0,
            kind="flash_circle",
            dcode=10,
            x_mm=0.0,
            y_mm=0.0,
            params={},
            polygon_mm=[]
        )

        cmd = create_parser_edit_command(obj)

        assert isinstance(cmd, ParserEditCircleCommand)

    def test_factory_rectangle(self):
        """Testa criação de comando para retângulo."""
        obj = GerberObject(id=0,
            kind="flash_rect",
            dcode=11,
            x_mm=0.0,
            y_mm=0.0,
            params={},
            polygon_mm=[]
        )

        cmd = create_parser_edit_command(obj)

        assert isinstance(cmd, ParserEditRectangleCommand)

    def test_factory_obround(self):
        """Testa criação de comando para obround."""
        obj = GerberObject(id=0,
            kind="flash_oval",
            dcode=12,
            x_mm=0.0,
            y_mm=0.0,
            params={},
            polygon_mm=[]
        )

        cmd = create_parser_edit_command(obj)

        assert isinstance(cmd, ParserEditObroundCommand)

    def test_factory_region(self):
        """Testa criação de comando para região."""
        obj = GerberObject(id=0,
            kind="region",
            dcode=0,
            x_mm=0.0,
            y_mm=0.0,
            params={},
            polygon_mm=[]
        )

        cmd = create_parser_edit_command(obj)

        assert isinstance(cmd, ParserEditRegionCommand)

    def test_factory_unsupported_type(self):
        """Testa que tipo não suportado retorna None."""
        obj = GerberObject(id=0,
            kind="macro",  # Tipo não suportado
            dcode=0,
            x_mm=0.0,
            y_mm=0.0,
            params={},
            polygon_mm=[]
        )

        cmd = create_parser_edit_command(obj)

        assert cmd is None
