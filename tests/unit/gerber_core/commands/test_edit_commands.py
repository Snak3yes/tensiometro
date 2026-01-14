"""
Testes unitários para EditCommands (Command Pattern).

Este módulo testa o padrão Command para operações de edição em objetos Gerber,
seguindo TDD (Test-Driven Development).

Testes escritos ANTES da implementação (fase RED).
"""
from __future__ import annotations

import pytest
from typing import Dict, Any

from aoi_lib.gerber_core.models.gerber_model import (
    GerberObject,
    GerberLayer,
    ValidationError,
)
from aoi_lib.gerber_core.commands.edit_commands import (
    EditObjectCommand,
    EditCircleCommand,
    EditRectangleCommand,
    EditObroundCommand,
    EditRegionCommand,
    CommandExecutionError,
)


class TestEditCircleCommand:
    """Testes para EditCircleCommand."""

    def test_edit_circle_diameter(self):
        """Testa edição de diâmetro de círculo."""
        obj = GerberObject(obj_type="flash_circle", x=0.0, y=0.0, diameter=5.0)
        command = EditCircleCommand(obj, {"diameter": 10.0})

        result = command.execute()

        assert result.diameter == 10.0
        assert result.x == 0.0
        assert result.y == 0.0

    def test_edit_circle_position(self):
        """Testa edição de posição de círculo."""
        obj = GerberObject(obj_type="flash_circle", x=0.0, y=0.0, diameter=5.0)
        command = EditCircleCommand(obj, {"x": 10.0, "y": 20.0})

        result = command.execute()

        assert result.x == 10.0
        assert result.y == 20.0
        assert result.diameter == 5.0

    def test_edit_circle_all_attributes(self):
        """Testa edição de todos os atributos de círculo."""
        obj = GerberObject(obj_type="flash_circle", x=0.0, y=0.0, diameter=5.0)
        command = EditCircleCommand(
            obj,
            {"x": 15.0, "y": 25.0, "diameter": 12.0}
        )

        result = command.execute()

        assert result.x == 15.0
        assert result.y == 25.0
        assert result.diameter == 12.0

    def test_edit_circle_invalid_attribute(self):
        """Testa que atributo inválido é ignorado (warning)."""
        obj = GerberObject(obj_type="flash_circle", x=0.0, y=0.0, diameter=5.0)
        command = EditCircleCommand(obj, {"invalid_attr": 999.0})

        # Não deve levantar exceção, apenas ignorar
        result = command.execute()

        assert result.x == 0.0
        assert result.y == 0.0
        assert result.diameter == 5.0

    def test_edit_circle_undo(self):
        """Testa undo de edição de círculo."""
        obj = GerberObject(obj_type="flash_circle", x=0.0, y=0.0, diameter=5.0)
        command = EditCircleCommand(obj, {"diameter": 10.0})

        modified = command.execute()
        undone = command.undo(modified)

        assert undone.diameter == 5.0  # Valor original


class TestEditRectangleCommand:
    """Testes para EditRectangleCommand."""

    def test_edit_rectangle_width(self):
        """Testa edição de largura de retângulo."""
        obj = GerberObject(
            obj_type="flash_rect",
            x=0.0,
            y=0.0,
            width=5.0,
            height=3.0
        )
        command = EditRectangleCommand(obj, {"width": 10.0})

        result = command.execute()

        assert result.width == 10.0
        assert result.height == 3.0

    def test_edit_rectangle_height(self):
        """Testa edição de altura de retângulo."""
        obj = GerberObject(
            obj_type="flash_rect",
            x=0.0,
            y=0.0,
            width=5.0,
            height=3.0
        )
        command = EditRectangleCommand(obj, {"height": 6.0})

        result = command.execute()

        assert result.width == 5.0
        assert result.height == 6.0

    def test_edit_rectangle_all_attributes(self):
        """Testa edição de todos os atributos de retângulo."""
        obj = GerberObject(
            obj_type="flash_rect",
            x=0.0,
            y=0.0,
            width=5.0,
            height=3.0
        )
        command = EditRectangleCommand(
            obj,
            {"x": 20.0, "y": 30.0, "width": 15.0, "height": 8.0}
        )

        result = command.execute()

        assert result.x == 20.0
        assert result.y == 30.0
        assert result.width == 15.0
        assert result.height == 8.0

    def test_edit_rectangle_undo(self):
        """Testa undo de edição de retângulo."""
        obj = GerberObject(
            obj_type="flash_rect",
            x=0.0,
            y=0.0,
            width=5.0,
            height=3.0
        )
        command = EditRectangleCommand(obj, {"width": 10.0})

        modified = command.execute()
        undone = command.undo(modified)

        assert undone.width == 5.0
        assert undone.height == 3.0


class TestEditObroundCommand:
    """Testes para EditObroundCommand."""

    def test_edit_obround_dimensions(self):
        """Testa edição de dimensões de obround."""
        obj = GerberObject(
            obj_type="flash_oval",
            x=0.0,
            y=0.0,
            width=5.0,
            height=3.0
        )
        command = EditObroundCommand(
            obj,
            {"width": 12.0, "height": 7.0}
        )

        result = command.execute()

        assert result.width == 12.0
        assert result.height == 7.0

    def test_edit_obround_position(self):
        """Testa edição de posição de obround."""
        obj = GerberObject(
            obj_type="flash_oval",
            x=0.0,
            y=0.0,
            width=5.0,
            height=3.0
        )
        command = EditObroundCommand(obj, {"x": 50.0, "y": 60.0})

        result = command.execute()

        assert result.x == 50.0
        assert result.y == 60.0
        assert result.width == 5.0
        assert result.height == 3.0

    def test_edit_obround_undo(self):
        """Testa undo de edição de obround."""
        obj = GerberObject(
            obj_type="flash_oval",
            x=0.0,
            y=0.0,
            width=5.0,
            height=3.0
        )
        command = EditObroundCommand(obj, {"width": 10.0})

        modified = command.execute()
        undone = command.undo(modified)

        assert undone.width == 5.0
        assert undone.height == 3.0


class TestEditRegionCommand:
    """Testes para EditRegionCommand."""

    def test_edit_region_position(self):
        """Testa edição de posição de região."""
        obj = GerberObject(obj_type="region", x=0.0, y=0.0)
        command = EditRegionCommand(obj, {"x": 100.0, "y": 200.0})

        result = command.execute()

        assert result.x == 100.0
        assert result.y == 200.0

    def test_edit_region_undo(self):
        """Testa undo de edição de região."""
        obj = GerberObject(obj_type="region", x=0.0, y=0.0)
        command = EditRegionCommand(obj, {"x": 50.0})

        modified = command.execute()
        undone = command.undo(modified)

        assert undone.x == 0.0
        assert undone.y == 0.0


class TestCommandExecutionError:
    """Testes para exceção CommandExecutionError."""

    def test_command_error_message(self):
        """Testa mensagem de erro de comando."""
        error = CommandExecutionError("Test error")

        assert str(error) == "Test error"

    def test_raise_command_error(self):
        """Testa lançamento de CommandExecutionError."""
        with pytest.raises(CommandExecutionError) as exc_info:
            raise CommandExecutionError("Test")

        assert str(exc_info.value) == "Test"


class TestEditObjectCommandInterface:
    """Testes para interface abstrata EditObjectCommand."""

    def test_cannot_instantiate_abstract_command(self):
        """Testa que comando abstrato não pode ser instanciado."""
        obj = GerberObject(obj_type="flash_circle", x=0.0, y=0.0, diameter=5.0)

        # Tentar instanciar classe abstrata deve falhar
        with pytest.raises(TypeError):
            EditObjectCommand(obj, {})

    def test_concrete_commands_implement_interface(self):
        """Testa que comandos concretos implementam a interface."""
        obj_circle = GerberObject(
            obj_type="flash_circle",
            x=0.0,
            y=0.0,
            diameter=5.0
        )
        obj_rect = GerberObject(
            obj_type="flash_rect",
            x=0.0,
            y=0.0,
            width=5.0,
            height=3.0
        )

        cmd_circle = EditCircleCommand(obj_circle, {"diameter": 10.0})
        cmd_rect = EditRectangleCommand(obj_rect, {"width": 8.0})

        # Devem ter métodos execute() e undo()
        assert hasattr(cmd_circle, "execute")
        assert hasattr(cmd_circle, "undo")
        assert hasattr(cmd_rect, "execute")
        assert hasattr(cmd_rect, "undo")

        # Devem retornar GerberObject
        result_circle = cmd_circle.execute()
        result_rect = cmd_rect.execute()

        assert isinstance(result_circle, GerberObject)
        assert isinstance(result_rect, GerberObject)


class TestCommandValidation:
    """Testes para validação em comandos."""

    def test_edit_circle_negative_diameter(self):
        """Testa que diâmetro negativo é aceito (validation is model's job)."""
        obj = GerberObject(obj_type="flash_circle", x=0.0, y=0.0, diameter=5.0)
        command = EditCircleCommand(obj, {"diameter": -5.0})

        # Command não valida, isso é responsabilidade do Model
        result = command.execute()
        assert result.diameter == -5.0

    def test_edit_rectangle_negative_width(self):
        """Testa que largura negativa é aceita (validation is model's job)."""
        obj = GerberObject(
            obj_type="flash_rect",
            x=0.0,
            y=0.0,
            width=5.0,
            height=3.0
        )
        command = EditRectangleCommand(obj, {"width": -10.0})

        # Command não valida, isso é responsabilidade do Model
        result = command.execute()
        assert result.width == -10.0
