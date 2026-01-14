"""
Testes unitários para GerberController.

Este módulo testa o Controller do padrão MVC para Gerber Viewer, seguindo
TDD (Test-Driven Development).

Testes escritos ANTES da implementação (fase RED).
"""
from __future__ import annotations

import pytest
from unittest.mock import Mock, MagicMock
from typing import List, Dict, Any

from aoi_lib.gerber_core.controllers.gerber_controller import (
    GerberController,
    ControllerError,
)
from aoi_lib.gerber_core.models.gerber_model import (
    GerberModel,
    GerberObject,
    GerberLayer,
    ValidationError,
)


class TestGerberController:
    """Testes para classe GerberController."""

    def test_create_controller_with_model(self):
        """Testa criação de controller com model."""
        model = GerberModel()
        controller = GerberController(model)

        assert controller.model == model
        assert controller.selected_object_indices == []

    def test_import_gerber_file(self):
        """Testa importação de arquivo Gerber."""
        model = GerberModel()
        controller = GerberController(model)

        lines = ["%ADD10C,1.0*%", "X10Y10D10*%"]
        cfg = {"units": "mm"}

        controller.import_gerber(lines, cfg)

        assert model.gerber_lines == lines
        assert model.gerber_cfg == cfg

    def test_export_gerber_file(self):
        """Testa exportação para arquivo Gerber."""
        model = GerberModel()
        controller = GerberController(model)

        # Carregar dados primeiro
        lines = ["%ADD10C,1.0*%"]
        cfg = {"units": "mm"}
        model.load_gerber(lines, cfg)

        # Exportar
        exported = controller.export_gerber()

        assert exported == lines

    def test_edit_single_object_circle(self):
        """Testa edição de objeto circular."""
        model = GerberModel()
        controller = GerberController(model)
        layer = GerberLayer(layer_name="top")
        obj = GerberObject(obj_type="flash_circle", x=0.0, y=0.0, diameter=5.0)
        layer.add_object(obj)
        model.add_layer(layer)

        # Selecionar objeto
        controller.select_object(0, layer_name="top")

        # Editar: aumentar diâmetro
        changes = {"diameter": 10.0}
        controller.edit_selected_object(changes)

        # Verificar que objeto foi modificado
        edited_obj = layer.objects[0]
        assert edited_obj.diameter == 10.0

    def test_edit_single_object_rectangle(self):
        """Testa edição de objeto retangular."""
        model = GerberModel()
        controller = GerberController(model)
        layer = GerberLayer(layer_name="top")
        obj = GerberObject(
            obj_type="flash_rect",
            x=0.0,
            y=0.0,
            width=5.0,
            height=3.0
        )
        layer.add_object(obj)
        model.add_layer(layer)

        controller.select_object(0, layer_name="top")

        changes = {"width": 10.0, "height": 6.0}
        controller.edit_selected_object(changes)

        edited_obj = layer.objects[0]
        assert edited_obj.width == 10.0
        assert edited_obj.height == 6.0

    def test_edit_many_objects_scale(self):
        """Testa edição em massa (escala)."""
        model = GerberModel()
        controller = GerberController(model)
        layer = GerberLayer(layer_name="top")

        # Criar 3 objetos
        for i in range(3):
            obj = GerberObject(
                obj_type="flash_circle",
                x=float(i * 10),
                y=0.0,
                diameter=5.0
            )
            layer.add_object(obj)

        model.add_layer(layer)

        # Selecionar todos
        controller.select_objects([0, 1, 2], layer_name="top")

        # Editar: aplicar escala de 2x
        controller.edit_selected_objects(scale_factor=2.0)

        # Verificar que todos foram escalados
        for obj in layer.objects:
            assert obj.diameter == 10.0  # 5.0 * 2.0

    def test_edit_many_objects_translate(self):
        """Testa edição em massa (translação)."""
        model = GerberModel()
        controller = GerberController(model)
        layer = GerberLayer(layer_name="top")

        obj1 = GerberObject(obj_type="flash_circle", x=0.0, y=0.0, diameter=5.0)
        obj2 = GerberObject(obj_type="flash_circle", x=10.0, y=10.0, diameter=5.0)
        layer.add_object(obj1)
        layer.add_object(obj2)
        model.add_layer(layer)

        controller.select_objects([0, 1], layer_name="top")

        # Transladar 5mm em X, 3mm em Y
        controller.edit_selected_objects(dx=5.0, dy=3.0)

        assert layer.objects[0].x == 5.0  # 0.0 + 5.0
        assert layer.objects[0].y == 3.0  # 0.0 + 3.0
        assert layer.objects[1].x == 15.0  # 10.0 + 5.0
        assert layer.objects[1].y == 13.0  # 10.0 + 3.0

    def test_delete_selected_object(self):
        """Testa exclusão de objeto selecionado."""
        model = GerberModel()
        controller = GerberController(model)
        layer = GerberLayer(layer_name="top")
        obj = GerberObject(obj_type="flash_circle", x=0.0, y=0.0, diameter=5.0)
        layer.add_object(obj)
        model.add_layer(layer)

        controller.select_object(0, layer_name="top")
        controller.delete_selected_objects()

        assert len(layer.objects) == 0

    def test_delete_many_objects(self):
        """Testa exclusão de múltiplos objetos."""
        model = GerberModel()
        controller = GerberController(model)
        layer = GerberLayer(layer_name="top")

        for i in range(5):
            obj = GerberObject(
                obj_type="flash_circle",
                x=float(i),
                y=0.0,
                diameter=5.0
            )
            layer.add_object(obj)

        model.add_layer(layer)

        # Selecionar 3 objetos (índices 1, 2, 3)
        controller.select_objects([1, 2, 3], layer_name="top")
        controller.delete_selected_objects()

        # Deve sobrar apenas 2 objetos (índices 0 e 4)
        assert len(layer.objects) == 2

    def test_select_object(self):
        """Testa seleção de único objeto."""
        model = GerberModel()
        controller = GerberController(model)
        layer = GerberLayer(layer_name="top")
        obj = GerberObject(obj_type="flash_circle", x=0.0, y=0.0, diameter=5.0)
        layer.add_object(obj)
        model.add_layer(layer)

        controller.select_object(0, layer_name="top")

        assert len(controller.selected_object_indices) == 1
        assert controller.selected_object_indices[0] == 0
        assert controller.current_layer_name == "top"

    def test_select_many_objects(self):
        """Testa seleção de múltiplos objetos."""
        model = GerberModel()
        controller = GerberController(model)
        layer = GerberLayer(layer_name="top")

        for i in range(5):
            obj = GerberObject(
                obj_type="flash_circle",
                x=float(i),
                y=0.0,
                diameter=5.0
            )
            layer.add_object(obj)

        model.add_layer(layer)

        controller.select_objects([0, 2, 4], layer_name="top")

        assert len(controller.selected_object_indices) == 3
        assert controller.selected_object_indices == [0, 2, 4]

    def test_clear_selection(self):
        """Testa limpeza de seleção."""
        model = GerberModel()
        controller = GerberController(model)
        layer = GerberLayer(layer_name="top")
        obj = GerberObject(obj_type="flash_circle", x=0.0, y=0.0, diameter=5.0)
        layer.add_object(obj)
        model.add_layer(layer)

        controller.select_object(0, layer_name="top")
        assert len(controller.selected_object_indices) == 1

        controller.clear_selection()
        assert len(controller.selected_object_indices) == 0

    def test_validate_selection_empty(self):
        """Testa validação de seleção vazia."""
        model = GerberModel()
        controller = GerberController(model)

        with pytest.raises(ControllerError) as exc_info:
            controller._validate_selection()

        assert "Nenhum objeto selecionado" in str(exc_info.value)

    def test_validate_selection_with_selection(self):
        """Testa validação de seleção com objetos selecionados."""
        model = GerberModel()
        controller = GerberController(model)
        layer = GerberLayer(layer_name="top")
        obj = GerberObject(obj_type="flash_circle", x=0.0, y=0.0, diameter=5.0)
        layer.add_object(obj)
        model.add_layer(layer)

        controller.select_object(0, layer_name="top")

        # Não deve levantar exceção
        controller._validate_selection()

    def test_get_selected_objects(self):
        """Testa obtenção de objetos selecionados."""
        model = GerberModel()
        controller = GerberController(model)
        layer = GerberLayer(layer_name="top")

        obj1 = GerberObject(obj_type="flash_circle", x=0.0, y=0.0, diameter=5.0)
        obj2 = GerberObject(obj_type="flash_circle", x=10.0, y=0.0, diameter=7.0)
        layer.add_object(obj1)
        layer.add_object(obj2)
        model.add_layer(layer)

        controller.select_objects([0, 1], layer_name="top")
        selected = controller.get_selected_objects()

        assert len(selected) == 2
        assert selected[0] == obj1
        assert selected[1] == obj2

    def test_get_object_count(self):
        """Testa contagem total de objetos."""
        model = GerberModel()
        controller = GerberController(model)

        count = controller.get_object_count()
        assert count == 0

        # Adicionar objetos
        layer = GerberLayer(layer_name="top")
        for i in range(3):
            obj = GerberObject(
                obj_type="flash_circle",
                x=float(i),
                y=0.0,
                diameter=5.0
            )
            layer.add_object(obj)
        model.add_layer(layer)

        count = controller.get_object_count()
        assert count == 3


class TestControllerError:
    """Testes para exceção ControllerError."""

    def test_controller_error_message(self):
        """Testa mensagem de erro do controller."""
        error = ControllerError("Test error")

        assert str(error) == "Test error"

    def test_raise_controller_error(self):
        """Testa lançamento de ControllerError."""
        with pytest.raises(ControllerError) as exc_info:
            raise ControllerError("Test")

        assert str(exc_info.value) == "Test"
