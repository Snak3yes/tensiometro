"""
Testes de integração para refatoração de mainwindow.py.

Este módulo testa a integração entre MainWindow, GerberController,
GerberModel e EditCommands durante a refatoração.

Garante backward compatibility durante a migração.
"""
from __future__ import annotations

import pytest
import sys
from pathlib import Path

# Adiciona path para importar MainWindow
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "poc_gerber"))

from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

from aoi_lib.gerber_core.models.gerber_model import (
    GerberModel,
    GerberObject,
    GerberLayer,
)
from aoi_lib.gerber_core.controllers.gerber_controller import (
    GerberController,
    ControllerError,
)
from aoi_lib.gerber_core.commands.edit_commands import (
    EditCircleCommand,
    EditRectangleCommand,
    EditObroundCommand,
    EditRegionCommand,
)


class TestMainWindowRefactoring:
    """
    Testes de integração para garantir backward compatibility
    durante refatoração de mainwindow.py.
    """

    def test_edit_single_object_circle(self):
        """
        Testa edição de objeto circular através da interface que será refatorada.
        """
        # Setup: Criar camada com objeto circular
        model = GerberModel()
        layer = GerberLayer(layer_name="top")
        obj = GerberObject(
            obj_type="flash_circle",
            x=0.0,
            y=0.0,
            diameter=5.0
        )
        layer.add_object(obj)
        model.add_layer(layer)

        # Criar controller
        controller = GerberController(model)

        # Selecionar e editar objeto
        controller.select_object(0, layer_name="top")
        controller.edit_selected_object({"diameter": 10.0})

        # Verificar que objeto foi modificado
        edited_obj = layer.objects[0]
        assert edited_obj.diameter == 10.0
        assert edited_obj.x == 0.0
        assert edited_obj.y == 0.0

    def test_edit_single_object_rectangle(self):
        """Testa edição de objeto retangular."""
        model = GerberModel()
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

        controller = GerberController(model)
        controller.select_object(0, layer_name="top")
        controller.edit_selected_object({"width": 10.0, "height": 6.0})

        edited_obj = layer.objects[0]
        assert edited_obj.width == 10.0
        assert edited_obj.height == 6.0

    def test_edit_multiple_objects_scale(self):
        """Testa edição em massa (escala) usando Controller."""
        model = GerberModel()
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

        # Criar controller e selecionar todos
        controller = GerberController(model)
        controller.select_objects([0, 1, 2], layer_name="top")

        # Editar: aplicar escala de 2x
        controller.edit_selected_objects(scale_factor=2.0)

        # Verificar que todos foram escalados
        for obj in layer.objects:
            assert obj.diameter == 10.0  # 5.0 * 2.0

    def test_edit_multiple_objects_translate(self):
        """Testa edição em massa (translação)."""
        model = GerberModel()
        layer = GerberLayer(layer_name="top")

        obj1 = GerberObject(obj_type="flash_circle", x=0.0, y=0.0, diameter=5.0)
        obj2 = GerberObject(obj_type="flash_circle", x=10.0, y=10.0, diameter=5.0)
        layer.add_object(obj1)
        layer.add_object(obj2)
        model.add_layer(layer)

        controller = GerberController(model)
        controller.select_objects([0, 1], layer_name="top")

        # Transladar 5mm em X, 3mm em Y
        controller.edit_selected_objects(dx=5.0, dy=3.0)

        assert layer.objects[0].x == 5.0  # 0.0 + 5.0
        assert layer.objects[0].y == 3.0  # 0.0 + 3.0
        assert layer.objects[1].x == 15.0  # 10.0 + 5.0
        assert layer.objects[1].y == 13.0  # 10.0 + 3.0

    def test_delete_selected_objects(self):
        """Testa exclusão de objetos selecionados."""
        model = GerberModel()
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

        controller = GerberController(model)
        controller.select_objects([1, 2, 3], layer_name="top")
        controller.delete_selected_objects()

        # Deve sobrar apenas 2 objetos (índices 0 e 4)
        assert len(layer.objects) == 2

    def test_selection_state(self):
        """Testa gerenciamento de estado de seleção."""
        model = GerberModel()
        layer = GerberLayer(layer_name="top")

        obj1 = GerberObject(obj_type="flash_circle", x=0.0, y=0.0, diameter=5.0)
        obj2 = GerberObject(obj_type="flash_circle", x=10.0, y=0.0, diameter=5.0)
        layer.add_object(obj1)
        layer.add_object(obj2)
        model.add_layer(layer)

        controller = GerberController(model)

        # Selecionar objeto único
        controller.select_object(0, layer_name="top")
        assert len(controller.selected_object_indices) == 1
        assert controller.selected_object_indices[0] == 0

        # Limpar seleção
        controller.clear_selection()
        assert len(controller.selected_object_indices) == 0

        # Selecionar múltiplos
        controller.select_objects([0, 1], layer_name="top")
        assert len(controller.selected_object_indices) == 2


class TestCommandPatternIntegration:
    """
    Testa integração do Command Pattern com Controller.
    """

    def test_command_factory_pattern(self):
        """
        Testa Factory Method para criar comandos apropriados.

        Este padrão será usado em MainWindow para eliminar
        cadeias if/elif/else.
        """
        # Setup
        model = GerberModel()
        layer = GerberLayer(layer_name="top")

        circle = GerberObject(obj_type="flash_circle", x=0.0, y=0.0, diameter=5.0)
        rect = GerberObject(obj_type="flash_rect", x=10.0, y=10.0, width=5.0, height=3.0)
        obround = GerberObject(obj_type="flash_oval", x=20.0, y=20.0, width=8.0, height=4.0)
        region = GerberObject(obj_type="region", x=30.0, y=30.0)

        layer.add_object(circle)
        layer.add_object(rect)
        layer.add_object(obround)
        layer.add_object(region)
        model.add_layer(layer)

        # Factory Function
        def create_command(obj: GerberObject, changes: Dict[str, Any]):
            """Factory Method para criar comando apropriado."""
            commands = {
                "flash_circle": EditCircleCommand,
                "flash_rect": EditRectangleCommand,
                "flash_oval": EditObroundCommand,
                "region": EditRegionCommand,
            }
            cmd_class = commands.get(obj.obj_type)
            if cmd_class is None:
                raise ValueError(f"Unknown object type: {obj.obj_type}")
            return cmd_class(obj, changes)

        # Testar cada tipo
        cmd_circle = create_command(circle, {"diameter": 10.0})
        assert isinstance(cmd_circle, EditCircleCommand)
        result = cmd_circle.execute()
        assert result.diameter == 10.0

        cmd_rect = create_command(rect, {"width": 8.0})
        assert isinstance(cmd_rect, EditRectangleCommand)
        result = cmd_rect.execute()
        assert result.width == 8.0

        cmd_obround = create_command(obround, {"height": 6.0})
        assert isinstance(cmd_obround, EditObroundCommand)
        result = cmd_obround.execute()
        assert result.height == 6.0

        cmd_region = create_command(region, {"x": 35.0})
        assert isinstance(cmd_region, EditRegionCommand)
        result = cmd_region.execute()
        assert result.x == 35.0


class TestBackwardCompatibility:
    """
    Testa que funcionalidades existentes continuam funcionando
    após refatoração.
    """

    def test_import_export_workflow(self):
        """Testa fluxo completo de importação/exportação."""
        model = GerberModel()
        controller = GerberController(model)

        # Importar dados
        lines = ["%ADD10C,1.0*%", "X10Y10D10*%"]
        cfg = {"units": "mm"}

        controller.import_gerber(lines, cfg)

        assert model.gerber_lines == lines
        assert model.gerber_cfg == cfg

        # Exportar dados
        exported = controller.export_gerber()
        assert exported == lines

    def test_error_handling_no_selection(self):
        """Testa tratamento de erros quando não há seleção."""
        model = GerberModel()
        controller = GerberController(model)

        # Tentar editar sem seleção deve falhar
        with pytest.raises(ControllerError) as exc_info:
            controller.edit_selected_object({"diameter": 10.0})

        assert "Nenhum objeto selecionado" in str(exc_info.value)

    def test_get_statistics(self):
        """Testa obtenção de estatísticas do modelo."""
        model = GerberModel()
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

        stats = model.get_statistics()
        assert stats["total_objects"] == 5
        assert stats["total_layers"] == 1


class TestMainWindowIntegration:
    """
    Testes de integração específicos para MainWindow refatorado.

    NOTA: Estes testes assumem que MainWindow será refatorado para
    delegar lógica para GerberController.
    """

    @pytest.mark.skip(reason="MainWindow refactoring not yet implemented")
    def test_mainwindow_uses_controller(self):
        """Testa que MainWindow usa Controller para edições."""
        # TODO: Após refatoração, instanciar MainWindow e verificar
        # que ele delega operações para GerberController
        pass

    @pytest.mark.skip(reason="MainWindow refactoring not yet implemented")
    def test_mainwindow_selection_sync(self):
        """Testa sincronização de seleção entre UI e Controller."""
        # TODO: Testar que seleção na UI atualiza estado do Controller
        pass

    @pytest.mark.skip(reason="MainWindow refactoring not yet implemented")
    def test_mainwindow_undo_redo(self):
        """Testa funcionalidade undo/redo integrada."""
        # TODO: Testar que undo/redo funciona com Command Pattern
        pass
