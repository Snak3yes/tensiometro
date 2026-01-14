"""
Testes unitários para GerberModel.

Este módulo testa o Model do padrão MVC para Gerber Viewer, seguindo
TDD (Test-Driven Development).

Testes escritos ANTES da implementação (fase RED).
"""
from __future__ import annotations

import pytest
from dataclasses import dataclass
from typing import List, Dict, Any

from aoi_lib.gerber_core.models.gerber_model import (
    GerberModel,
    GerberObject,
    GerberLayer,
    ValidationError,
)


class TestGerberObject:
    """Testes para classe GerberObject (dataclass)."""

    def test_create_circle_object(self):
        """Testa criação de objeto circular."""
        obj = GerberObject(
            obj_type="flash_circle",
            x=10.0,
            y=20.0,
            diameter=5.0,
        )
        assert obj.obj_type == "flash_circle"
        assert obj.x == 10.0
        assert obj.y == 20.0
        assert obj.diameter == 5.0

    def test_create_rectangle_object(self):
        """Testa criação de objeto retangular."""
        obj = GerberObject(
            obj_type="flash_rect",
            x=0.0,
            y=0.0,
            width=10.0,
            height=5.0,
        )
        assert obj.obj_type == "flash_rect"
        assert obj.width == 10.0
        assert obj.height == 5.0

    def test_create_obround_object(self):
        """Testa criação de objeto obround (oval)."""
        obj = GerberObject(
            obj_type="flash_oval",
            x=5.0,
            y=5.0,
            width=8.0,
            height=4.0,
        )
        assert obj.obj_type == "flash_oval"
        assert obj.width == 8.0
        assert obj.height == 4.0


class TestGerberLayer:
    """Testes para classe GerberLayer."""

    def test_create_empty_layer(self):
        """Testa criação de camada vazia."""
        layer = GerberLayer(layer_name="top")
        assert layer.layer_name == "top"
        assert len(layer.objects) == 0

    def test_add_object_to_layer(self):
        """Testa adição de objeto à camada."""
        layer = GerberLayer(layer_name="top")
        obj = GerberObject(obj_type="flash_circle", x=0.0, y=0.0, diameter=5.0)

        layer.add_object(obj)

        assert len(layer.objects) == 1
        assert layer.objects[0] == obj

    def test_remove_object_from_layer(self):
        """Testa remoção de objeto da camada."""
        layer = GerberLayer(layer_name="top")
        obj = GerberObject(obj_type="flash_circle", x=0.0, y=0.0, diameter=5.0)
        layer.add_object(obj)

        layer.remove_object(0)

        assert len(layer.objects) == 0

    def test_remove_invalid_index_raises_error(self):
        """Testa que índice inválido levanta ValidationError."""
        layer = GerberLayer(layer_name="top")

        with pytest.raises(ValidationError):
            layer.remove_object(999)


class TestGerberModel:
    """Testes para classe GerberModel (Model principal)."""

    def test_create_empty_model(self):
        """Testa criação de modelo vazio."""
        model = GerberModel()

        assert model.gerber_lines is None
        assert model.gerber_cfg is None
        assert len(model.layers) == 0
        assert model.macros == {}
        assert model.apertures == {}

    def test_load_gerber_data(self):
        """Testa carregamento de dados Gerber."""
        model = GerberModel()
        lines = ["%ADD10C,1.0*%", "X10Y10D10*%"]
        cfg = {}  # GerberConfig simplificado

        model.load_gerber(lines, cfg)

        assert model.gerber_lines == lines
        assert model.gerber_cfg == cfg

    def test_add_layer(self):
        """Testa adição de camada ao modelo."""
        model = GerberModel()
        layer = GerberLayer(layer_name="top")

        model.add_layer(layer)

        assert len(model.layers) == 1
        assert model.layers[0] == layer

    def test_add_aperture(self):
        """Testa adição de abertura (aperture)."""
        model = GerberModel()
        aperture = {"dcode": 10, "type": "circle", "diameter": 1.0}

        model.add_aperture(10, aperture)

        assert 10 in model.apertures
        assert model.apertures[10] == aperture

    def test_add_macro(self):
        """Testa adição de macro."""
        model = GerberModel()
        macro = {"name": "macro1", "content": "..."}

        model.add_macro("macro1", macro)

        assert "macro1" in model.macros
        assert model.macros["macro1"] == macro

    def test_get_object_count(self):
        """Testa contagem de objetos no modelo."""
        model = GerberModel()
        layer = GerberLayer(layer_name="top")
        obj = GerberObject(obj_type="flash_circle", x=0.0, y=0.0, diameter=5.0)
        layer.add_object(obj)
        model.add_layer(layer)

        count = model.get_object_count()

        assert count == 1

    def test_validate_object_with_valid_data(self):
        """Testa validação de objeto válido."""
        model = GerberModel()
        obj = GerberObject(obj_type="flash_circle", x=0.0, y=0.0, diameter=5.0)

        # Não deve levantar exceção
        model.validate_object(obj)

    def test_validate_object_with_invalid_type(self):
        """Testa validação de objeto com tipo inválido."""
        model = GerberModel()
        obj = GerberObject(obj_type="invalid_type", x=0.0, y=0.0)

        with pytest.raises(ValidationError):
            model.validate_object(obj)

    def test_validate_object_with_negative_diameter(self):
        """Testa validação de objeto com diâmetro negativo."""
        model = GerberModel()
        obj = GerberObject(obj_type="flash_circle", x=0.0, y=0.0, diameter=-1.0)

        with pytest.raises(ValidationError):
            model.validate_object(obj)

    def test_transform_object_scale(self):
        """Testa transformação de escala em objeto."""
        model = GerberModel()
        obj = GerberObject(obj_type="flash_circle", x=0.0, y=0.0, diameter=10.0)

        transformed = model.transform_object(obj, scale_factor=2.0)

        assert transformed.diameter == 20.0  # 10.0 * 2.0
        assert transformed.x == 0.0
        assert transformed.y == 0.0

    def test_transform_object_translate(self):
        """Testa transformação de translação em objeto."""
        model = GerberModel()
        obj = GerberObject(obj_type="flash_circle", x=10.0, y=20.0, diameter=5.0)

        transformed = model.transform_object(obj, dx=5.0, dy=3.0)

        assert transformed.x == 15.0  # 10.0 + 5.0
        assert transformed.y == 23.0  # 20.0 + 3.0
        assert transformed.diameter == 5.0

    def test_transform_object_combined(self):
        """Testa transformação combinada (escala + translação)."""
        model = GerberModel()
        obj = GerberObject(obj_type="flash_rect", x=10.0, y=10.0, width=5.0, height=3.0)

        transformed = model.transform_object(obj, scale_factor=2.0, dx=1.0, dy=2.0)

        # Escala: width=5.0*2.0=10.0, height=3.0*2.0=6.0
        # Translação: x=10.0+1.0=11.0, y=10.0+2.0=12.0
        assert transformed.width == 10.0
        assert transformed.height == 6.0
        assert transformed.x == 11.0
        assert transformed.y == 12.0

    def test_get_statistics_empty_model(self):
        """Testa obtenção de estatísticas de modelo vazio."""
        model = GerberModel()

        stats = model.get_statistics()

        assert stats["total_objects"] == 0
        assert stats["total_layers"] == 0
        assert stats["total_apertures"] == 0
        assert stats["total_macros"] == 0

    def test_get_statistics_with_data(self):
        """Testa obtenção de estatísticas com dados."""
        model = GerberModel()
        layer = GerberLayer(layer_name="top")
        obj = GerberObject(obj_type="flash_circle", x=0.0, y=0.0, diameter=5.0)
        layer.add_object(obj)
        model.add_layer(layer)
        model.add_aperture(10, {"dcode": 10, "type": "circle"})
        model.add_macro("macro1", {"name": "macro1"})

        stats = model.get_statistics()

        assert stats["total_objects"] == 1
        assert stats["total_layers"] == 1
        assert stats["total_apertures"] == 1
        assert stats["total_macros"] == 1


class TestValidationError:
    """Testes para exceção ValidationError."""

    def test_validation_error_message(self):
        """Testa mensagem de erro de validação."""
        error = ValidationError("Invalid object type")

        assert str(error) == "Invalid object type"

    def test_raise_validation_error(self):
        """Testa lançamento de ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError("Test error")

        assert str(exc_info.value) == "Test error"
