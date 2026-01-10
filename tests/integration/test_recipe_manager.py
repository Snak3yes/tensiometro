"""
test_recipe_manager.py
-----------------------
Testes de integração para recipe_manager.py.

Cobertura:
- Dataclasses (Point2D, Point3D, StencilInfo, TensionAcceptance, etc.)
- Recipe (serialização, validação)
- RecipeManager (CRUD de receitas)
"""

import pytest
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, Mock

from aoi_lib.recipe_manager import (
    Point2D, Point3D, StencilInfo, TensionAcceptance,
    TensionConfig, CaptureConfig, InspectionConfig, Recipe,
    RecipeManager, create_sample_recipe
)


# ============================================================================
#  FIXTURES
# ============================================================================

@pytest.fixture
def temp_recipes_dir(tmp_path):
    """Cria um diretório temporário para receitas."""
    recipes_dir = tmp_path / "recipes"
    recipes_dir.mkdir(parents=True, exist_ok=True)
    return recipes_dir


@pytest.fixture
def sample_point2d():
    """Ponto 2D de exemplo."""
    return Point2D(x=10.5, y=20.3)


@pytest.fixture
def sample_point3d():
    """Ponto 3D de exemplo."""
    return Point3D(x=10.5, y=20.3, z=-5.0)


@pytest.fixture
def sample_stencil_info():
    """Informações de stencil de exemplo."""
    return StencilInfo(
        width_mm=400.0,
        height_mm=300.0,
        thickness_mm=0.12,
        material="Inox 304",
        notes="Stencil para teste"
    )


@pytest.fixture
def sample_tension_acceptance():
    """Critérios de aceitação de tensão."""
    return TensionAcceptance(
        min_tension=25.0,
        max_tension=45.0,
        warning_low=28.0,
        warning_high=42.0
    )


@pytest.fixture
def sample_tension_config(sample_tension_acceptance):
    """Configuração de medição de tensão."""
    return TensionConfig(
        enabled=True,
        grid_rows=5,
        grid_cols=5,
        start_point=Point2D(50, 50),
        end_point=Point2D(350, 250),
        z_start=0.0,
        z_end=-5.0,
        z_speed=100.0,
        acceptance=sample_tension_acceptance
    )


@pytest.fixture
def sample_capture_config():
    """Configuração de captura."""
    return CaptureConfig(
        origin=Point2D(0, 0),
        end=Point2D(400, 300),
        step_x=50.0,
        step_y=50.0,
        feed_rate=2000.0,
        capture_delay_ms=200,
        backlight_enabled=True
    )


@pytest.fixture
def sample_inspection_config():
    """Configuração de inspeção."""
    return InspectionConfig(
        enabled=False,
        gerber_file=None,
        masks=[],
        default_threshold=128,
        default_min_percent=95.0,
        target_color="white"
    )


@pytest.fixture
def sample_recipe(sample_stencil_info, sample_tension_config,
                  sample_capture_config, sample_inspection_config):
    """Receita completa de exemplo."""
    return Recipe(
        recipe_id="TEST_001",
        name="Receita de Teste",
        version="1.0",
        created_by="tester",
        stencil=sample_stencil_info,
        tension=sample_tension_config,
        capture=sample_capture_config,
        inspection=sample_inspection_config
    )


# ============================================================================
#  TESTES: Point2D
# ============================================================================

class TestPoint2D:
    """Testes para dataclass Point2D."""

    def test_initialization_default(self):
        """Testa inicialização com valores padrão."""
        point = Point2D()
        assert point.x == 0.0
        assert point.y == 0.0

    def test_initialization_with_values(self, sample_point2d):
        """Testa inicialização com valores."""
        assert sample_point2d.x == 10.5
        assert sample_point2d.y == 20.3

    def test_to_dict(self, sample_point2d):
        """Testa conversão para dicionário."""
        result = sample_point2d.to_dict()
        assert result == {"x": 10.5, "y": 20.3}

    def test_from_dict(self):
        """Testa criação a partir de dicionário."""
        data = {"x": 15.7, "y": 25.9}
        point = Point2D.from_dict(data)
        assert point.x == 15.7
        assert point.y == 25.9

    def test_from_dict_with_defaults(self):
        """Testa from_dict com valores padrão."""
        point = Point2D.from_dict({})
        assert point.x == 0.0
        assert point.y == 0.0


# ============================================================================
#  TESTES: Point3D
# ============================================================================

class TestPoint3D:
    """Testes para dataclass Point3D."""

    def test_initialization_default(self):
        """Testa inicialização com valores padrão."""
        point = Point3D()
        assert point.x == 0.0
        assert point.y == 0.0
        assert point.z == 0.0

    def test_initialization_with_values(self, sample_point3d):
        """Testa inicialização com valores."""
        assert sample_point3d.x == 10.5
        assert sample_point3d.y == 20.3
        assert sample_point3d.z == -5.0

    def test_to_dict(self, sample_point3d):
        """Testa conversão para dicionário."""
        result = sample_point3d.to_dict()
        assert result == {"x": 10.5, "y": 20.3, "z": -5.0}

    def test_from_dict(self):
        """Testa criação a partir de dicionário."""
        data = {"x": 15.7, "y": 25.9, "z": -3.0}
        point = Point3D.from_dict(data)
        assert point.x == 15.7
        assert point.y == 25.9
        assert point.z == -3.0


# ============================================================================
#  TESTES: StencilInfo
# ============================================================================

class TestStencilInfo:
    """Testes para dataclass StencilInfo."""

    def test_initialization_default(self):
        """Testa inicialização com valores padrão."""
        info = StencilInfo()
        assert info.width_mm == 400.0
        assert info.height_mm == 300.0
        assert info.thickness_mm == 0.12
        assert info.material == "Inox"
        assert info.notes == ""

    def test_initialization_with_values(self, sample_stencil_info):
        """Testa inicialização com valores."""
        assert sample_stencil_info.width_mm == 400.0
        assert sample_stencil_info.height_mm == 300.0
        assert sample_stencil_info.thickness_mm == 0.12
        assert sample_stencil_info.material == "Inox 304"
        assert sample_stencil_info.notes == "Stencil para teste"

    def test_to_dict(self, sample_stencil_info):
        """Testa conversão para dicionário."""
        result = sample_stencil_info.to_dict()
        assert result["width_mm"] == 400.0
        assert result["height_mm"] == 300.0
        assert result["material"] == "Inox 304"

    def test_from_dict(self):
        """Testa criação a partir de dicionário."""
        data = {
            "width_mm": 500.0,
            "height_mm": 400.0,
            "thickness_mm": 0.15,
            "material": "Aço",
            "notes": "Teste"
        }
        info = StencilInfo.from_dict(data)
        assert info.width_mm == 500.0
        assert info.material == "Aço"


# ============================================================================
#  TESTES: TensionAcceptance
# ============================================================================

class TestTensionAcceptance:
    """Testes para dataclass TensionAcceptance."""

    def test_initialization_default(self):
        """Testa inicialização com valores padrão."""
        acc = TensionAcceptance()
        assert acc.min_tension == 25.0
        assert acc.max_tension == 45.0
        assert acc.warning_low == 28.0
        assert acc.warning_high == 42.0

    def test_classify_ok(self, sample_tension_acceptance):
        """Testa classificação OK."""
        # Valores dentro da faixa warning
        assert sample_tension_acceptance.classify(30.0) == 'OK'
        assert sample_tension_acceptance.classify(35.0) == 'OK'
        assert sample_tension_acceptance.classify(40.0) == 'OK'

    def test_classify_warning_low(self, sample_tension_acceptance):
        """Testa classificação WARNING (abaixo)."""
        # Entre min e warning_low
        assert sample_tension_acceptance.classify(26.0) == 'WARNING'
        assert sample_tension_acceptance.classify(27.5) == 'WARNING'

    def test_classify_warning_high(self, sample_tension_acceptance):
        """Testa classificação WARNING (acima)."""
        # Entre warning_high e max
        assert sample_tension_acceptance.classify(43.0) == 'WARNING'
        assert sample_tension_acceptance.classify(44.5) == 'WARNING'

    def test_classify_nok_below(self, sample_tension_acceptance):
        """Testa classificação NOK (abaixo do mínimo)."""
        assert sample_tension_acceptance.classify(20.0) == 'NOK'
        assert sample_tension_acceptance.classify(24.9) == 'NOK'

    def test_classify_nok_above(self, sample_tension_acceptance):
        """Testa classificação NOK (acima do máximo)."""
        assert sample_tension_acceptance.classify(46.0) == 'NOK'
        assert sample_tension_acceptance.classify(50.0) == 'NOK'


# ============================================================================
#  TESTES: TensionConfig
# ============================================================================

class TestTensionConfig:
    """Testes para dataclass TensionConfig."""

    def test_initialization_default(self):
        """Testa inicialização com valores padrão."""
        config = TensionConfig()
        assert config.enabled is False
        assert config.grid_rows == 3
        assert config.grid_cols == 3
        assert config.z_start == 0.0
        assert config.z_end == -5.0
        assert config.z_speed == 100.0

    def test_to_dict(self, sample_tension_config):
        """Testa conversão para dicionário."""
        result = sample_tension_config.to_dict()
        assert result["enabled"] is True
        assert result["grid_rows"] == 5
        assert result["grid_cols"] == 5
        assert "start_point" in result
        assert "end_point" in result
        assert "z_start" in result
        assert "acceptance" in result

    def test_from_dict(self):
        """Testa criação a partir de dicionário."""
        data = {
            "enabled": False,
            "grid_rows": 3,
            "grid_cols": 3,
            "start_point": {"x": 0, "y": 0},
            "end_point": {"x": 100, "y": 100},
            "z_start": 5.0,
            "z_end": 0.0,
            "z_speed": 150.0,
            "acceptance": {
                "min_tension": 20.0,
                "max_tension": 40.0,
                "warning_low": 25.0,
                "warning_high": 35.0
            }
        }
        config = TensionConfig.from_dict(data)
        assert config.enabled is False
        assert config.grid_rows == 3
        assert config.grid_cols == 3
        assert config.z_start == 5.0
        assert config.z_end == 0.0
        assert config.z_speed == 150.0


# ============================================================================
#  TESTES: CaptureConfig
# ============================================================================

class TestCaptureConfig:
    """Testes para dataclass CaptureConfig."""

    def test_initialization_default(self):
        """Testa inicialização padrão."""
        config = CaptureConfig()
        assert config.enabled is True
        assert config.step_x == 50.0
        assert config.step_y == 50.0
        assert config.capture_delay_ms == 200
        assert config.backlight_enabled is False

    def test_to_dict(self, sample_capture_config):
        """Testa conversão para dicionário."""
        result = sample_capture_config.to_dict()
        assert result["step_x"] == 50.0
        assert result["step_y"] == 50.0
        assert result["feed_rate"] == 2000.0
        assert result["backlight_enabled"] is True

    def test_from_dict(self):
        """Testa criação a partir de dicionário."""
        data = {
            "origin": {"x": 10, "y": 20},
            "end": {"x": 200, "y": 200},
            "step_x": 25.0,
            "step_y": 25.0,
            "feed_rate": 1500.0,
            "capture_delay_ms": 100,
            "backlight_enabled": False
        }
        config = CaptureConfig.from_dict(data)
        assert config.step_x == 25.0
        assert config.feed_rate == 1500.0
        assert config.backlight_enabled is False


# ============================================================================
#  TESTES: InspectionConfig
# ============================================================================

class TestInspectionConfig:
    """Testes para dataclass InspectionConfig."""

    def test_initialization_default(self):
        """Testa inicialização padrão."""
        config = InspectionConfig()
        assert config.enabled is True
        assert config.default_min_percent == 70
        assert config.target_color == "black"

    def test_to_dict(self, sample_inspection_config):
        """Testa conversão para dicionário."""
        result = sample_inspection_config.to_dict()
        assert result["enabled"] is False
        assert result["default_threshold"] == 128
        assert result["target_color"] == "white"

    def test_from_dict(self):
        """Testa criação a partir de dicionário."""
        data = {
            "enabled": True,
            "gerber_file": "/path/to/file.gbr",
            "masks": [{"id": 1}, {"id": 2}],
            "default_threshold": 150,
            "default_min_percent": 90.0,
            "target_color": "black"
        }
        config = InspectionConfig.from_dict(data)
        assert config.enabled is True
        assert config.gerber_file == "/path/to/file.gbr"
        assert len(config.masks) == 2
        assert config.default_threshold == 150
        assert config.target_color == "black"


# ============================================================================
#  TESTES: Recipe
# ============================================================================

class TestRecipe:
    """Testes para dataclass Recipe."""

    def test_initialization_generates_id(self):
        """Testa que inicialização gera ID e timestamps."""
        recipe = Recipe(name="Test Recipe")
        assert recipe.name == "Test Recipe"
        assert recipe.recipe_id != ""
        assert recipe.created_at != ""
        assert recipe.modified_at != ""
        assert recipe.recipe_id.startswith("RECIPE_")

    def test_to_dict(self, sample_recipe):
        """Testa conversão para dicionário."""
        result = sample_recipe.to_dict()
        assert result["recipe_id"] == "TEST_001"
        assert result["name"] == "Receita de Teste"
        assert result["version"] == "1.0"
        assert "stencil" in result
        assert "tension_config" in result
        assert "capture_config" in result
        assert "inspection_config" in result

    def test_from_dict(self):
        """Testa criação a partir de dicionário."""
        data = {
            "recipe_id": "DICT_001",
            "name": "Receita from Dict",
            "version": "2.0",
            "created_at": "2024-01-01T10:00:00",
            "modified_at": "2024-01-01T11:00:00",
            "created_by": "user1",
            "stencil": {
                "width_mm": 400.0,
                "height_mm": 300.0,
                "thickness_mm": 0.12,
                "material": "Inox",
                "notes": ""
            },
            "tension_config": {
                "enabled": True,
                "grid": {"rows": 3, "cols": 3},
                "start_point": {"x": 0, "y": 0},
                "end_point": {"x": 100, "y": 100},
                "z_params": {"start_z": 0, "end_z": -5, "speed": 100},
                "acceptance": {
                    "min_tension": 25.0,
                    "max_tension": 45.0,
                    "warning_low": 28.0,
                    "warning_high": 42.0
                }
            },
            "capture_config": {
                "origin": {"x": 0, "y": 0},
                "end": {"x": 400, "y": 300},
                "step_x": 50.0,
                "step_y": 50.0,
                "feed_rate": 2000.0,
                "capture_delay_ms": 200,
                "backlight_enabled": True
            },
            "inspection_config": {
                "enabled": False,
                "gerber_file": None,
                "masks": [],
                "default_threshold": 128,
                "default_min_percent": 95.0,
                "target_color": "white"
            }
        }
        recipe = Recipe.from_dict(data)
        assert recipe.recipe_id == "DICT_001"
        assert recipe.name == "Receita from Dict"
        assert recipe.version == "2.0"

    def test_to_json(self, sample_recipe):
        """Testa serialização para JSON string."""
        json_str = sample_recipe.to_json()
        assert isinstance(json_str, str)
        # Verifica que é JSON válido
        data = json.loads(json_str)
        assert data["recipe_id"] == "TEST_001"

    def test_from_json(self):
        """Testa desserialização de JSON string."""
        # Cria uma receita e serializa para usar no teste
        temp_recipe = Recipe(
            recipe_id="JSON_001",
            name="JSON Recipe",
            version="1.0"
        )
        json_str = temp_recipe.to_json()
        # Desserializa
        recipe = Recipe.from_json(json_str)
        assert recipe.recipe_id == "JSON_001"
        assert recipe.name == "JSON Recipe"

    def test_update_modified(self, sample_recipe):
        """Testa atualização de timestamp de modificação."""
        old_modified = sample_recipe.modified_at
        # Pequena pausa para garantir diferença de timestamp
        import time
        time.sleep(0.01)
        sample_recipe.update_modified()
        assert sample_recipe.modified_at != old_modified

    def test_validate_valid_recipe(self, sample_recipe):
        """Testa validação de receita válida."""
        errors = sample_recipe.validate()
        assert errors == []

    def test_validate_empty_name(self, sample_recipe):
        """Testa validação com nome vazio."""
        sample_recipe.name = ""
        errors = sample_recipe.validate()
        assert len(errors) > 0
        assert any("Nome" in err for err in errors)

    def test_validate_invalid_width(self, sample_recipe):
        """Testa validação com largura inválida."""
        sample_recipe.stencil.width_mm = 0
        errors = sample_recipe.validate()
        assert len(errors) > 0
        assert any("Largura" in err for err in errors)

    def test_validate_invalid_height(self, sample_recipe):
        """Testa validação com altura inválida."""
        sample_recipe.stencil.height_mm = -10
        errors = sample_recipe.validate()
        assert len(errors) > 0
        assert any("Altura" in err for err in errors)

    def test_validate_invalid_grid(self, sample_recipe):
        """Testa validação com grid inválido."""
        sample_recipe.tension.grid_rows = 0
        errors = sample_recipe.validate()
        assert len(errors) > 0
        assert any("Grid" in err for err in errors)

    def test_validate_invalid_acceptance(self, sample_recipe):
        """Testa validação com critérios de aceitação inválidos."""
        sample_recipe.tension.acceptance.min_tension = 50.0
        sample_recipe.tension.acceptance.max_tension = 40.0
        errors = sample_recipe.validate()
        assert len(errors) > 0
        assert any("mínima" in err for err in errors)

    def test_validate_invalid_steps(self, sample_recipe):
        """Testa validação com steps inválidos."""
        sample_recipe.capture.step_x = 0
        errors = sample_recipe.validate()
        assert len(errors) > 0
        assert any("Steps" in err for err in errors)


# ============================================================================
#  TESTES: RecipeManager
# ============================================================================

class TestRecipeManagerInitialization:
    """Testes para inicialização do RecipeManager."""

    def test_initialization_with_default_dir(self):
        """Testa inicialização com diretório padrão."""
        manager = RecipeManager()
        # Verifica se termina com "recipes" (independente de ser absoluto ou relativo)
        assert manager.recipes_dir.name == "recipes"
        assert manager.current_recipe is None

    def test_initialization_with_custom_dir(self, temp_recipes_dir):
        """Testa inicialização com diretório customizado."""
        manager = RecipeManager(recipes_dir=str(temp_recipes_dir))
        assert manager.recipes_dir == temp_recipes_dir
        assert temp_recipes_dir.exists()

    def test_creates_recipes_directory(self, tmp_path):
        """Testa que cria diretório se não existir."""
        new_dir = tmp_path / "new_recipes"
        manager = RecipeManager(recipes_dir=str(new_dir))
        assert new_dir.exists()


class TestRecipeManagerCreate:
    """Testes para criação de receitas."""

    @pytest.fixture
    def recipe_manager(self, temp_recipes_dir):
        return RecipeManager(recipes_dir=str(temp_recipes_dir))

    def test_create_recipe(self, recipe_manager):
        """Testa criação de receita."""
        manager = recipe_manager
        recipe = manager.create_recipe("Nova Receita")
        
        assert isinstance(recipe, Recipe)
        assert recipe.name == "Nova Receita"
        # create_recipe não define current_recipe automaticamente na nova implementação
        # assert manager.current_recipe == recipe


class TestRecipeManagerSave:
    """Testes para salvamento de receitas."""

    def test_save_recipe(self, temp_recipes_dir, sample_recipe):
        """Testa salvamento de receita."""
        manager = RecipeManager(recipes_dir=str(temp_recipes_dir))
        result = manager.save_recipe(sample_recipe)
        assert result is True
        # Verifica que arquivo foi criado
        files = list(temp_recipes_dir.glob("*.json"))
        assert len(files) == 1

    def test_save_invalid_recipe(self, temp_recipes_dir, sample_recipe):
        """Testa salvamento de receita inválida."""
        manager = RecipeManager(recipes_dir=str(temp_recipes_dir))
        sample_recipe.name = ""  # Invalid
        result = manager.save_recipe(sample_recipe)
        assert result is False


class TestRecipeManagerLoad:
    """Testes para carregamento de receitas."""

    def test_load_recipe_by_filename(self, temp_recipes_dir, sample_recipe):
        """Testa carregamento por nome de arquivo."""
        manager = RecipeManager(recipes_dir=str(temp_recipes_dir))
        manager.save_recipe(sample_recipe, filename="test_recipe")
        loaded = manager.load_recipe("test_recipe")
        assert loaded is not None
        assert loaded.name == "Receita de Teste"

    def test_load_recipe_by_id(self, temp_recipes_dir, sample_recipe):
        """Testa carregamento por ID."""
        manager = RecipeManager(recipes_dir=str(temp_recipes_dir))
        manager.save_recipe(sample_recipe)
        loaded = manager.load_recipe("TEST_001")
        assert loaded is not None
        assert loaded.recipe_id == "TEST_001"

    def test_load_nonexistent_recipe(self, temp_recipes_dir):
        """Testa carregamento de receita inexistente."""
        manager = RecipeManager(recipes_dir=str(temp_recipes_dir))
        loaded = manager.load_recipe("NONEXISTENT")
        assert loaded is None


class TestRecipeManagerList:
    """Testes para listagem de receitas."""

    def test_list_empty_recipes(self, temp_recipes_dir):
        """Testa listagem com diretório vazio."""
        manager = RecipeManager(recipes_dir=str(temp_recipes_dir))
        recipes = manager.list_recipes()
        assert recipes == []

    def test_list_multiple_recipes(self, temp_recipes_dir):
        """Testa listagem de múltiplas receitas."""
        manager = RecipeManager(recipes_dir=str(temp_recipes_dir))
        # Cria 3 receitas
        for i in range(3):
            recipe = Recipe(name=f"Receita {i}")
            manager.save_recipe(recipe, filename=f"recipe_{i}")
        recipes = manager.list_recipes()
        assert len(recipes) == 3
        # Verifica ordenação (mais recente primeiro)
        assert recipes[0]['name'] == "Receita 2"


class TestRecipeManagerDelete:
    """Testes para exclusão de receitas."""

    def test_delete_recipe(self, temp_recipes_dir, sample_recipe):
        """Testa exclusão de receita."""
        manager = RecipeManager(recipes_dir=str(temp_recipes_dir))
        manager.save_recipe(sample_recipe, filename="to_delete")
        result = manager.delete_recipe("to_delete")
        assert result is True
        # Verifica que arquivo foi removido
        files = list(temp_recipes_dir.glob("*.json"))
        assert len(files) == 0

    def test_delete_nonexistent_recipe(self, temp_recipes_dir):
        """Testa exclusão de receita inexistente."""
        manager = RecipeManager(recipes_dir=str(temp_recipes_dir))
        result = manager.delete_recipe("nonexistent")
        assert result is False


class TestRecipeManagerDuplicate:
    """Testes para duplicação de receitas."""

    def test_duplicate_recipe(self, temp_recipes_dir, sample_recipe):
        """Testa duplicação de receita."""
        manager = RecipeManager(recipes_dir=str(temp_recipes_dir))
        manager.save_recipe(sample_recipe, filename="original")
        duplicated = manager.duplicate_recipe("original", "Cópia")
        assert duplicated is not None
        assert duplicated.name == "Cópia"
        assert duplicated.recipe_id != sample_recipe.recipe_id

    def test_duplicate_nonexistent_recipe(self, temp_recipes_dir):
        """Testa duplicação de receita inexistente."""
        manager = RecipeManager(recipes_dir=str(temp_recipes_dir))
        duplicated = manager.duplicate_recipe("nonexistent", "Cópia")
        assert duplicated is None


class TestRecipeManagerCurrent:
    """Testes para gerenciamento de receita atual."""

    def test_get_current_recipe(self, temp_recipes_dir, sample_recipe):
        """Testa obtenção de receita atual."""
        manager = RecipeManager(recipes_dir=str(temp_recipes_dir))
        manager.current_recipe = sample_recipe
        assert manager.get_current_recipe() == sample_recipe

    def test_set_current_recipe(self, temp_recipes_dir, sample_recipe):
        """Testa definição de receita atual."""
        manager = RecipeManager(recipes_dir=str(temp_recipes_dir))
        manager.set_current_recipe(sample_recipe)
        assert manager.current_recipe == sample_recipe


# ============================================================================
#  TESTES: Funções Utilitárias
# ============================================================================

class TestUtilityFunctions:
    """Testes para funções utilitárias."""

    def test_create_sample_recipe(self):
        """Testa criação de receita de exemplo."""
        recipe = create_sample_recipe()
        assert recipe.name == "Stencil Exemplo PCB"
        assert recipe.recipe_id == "SAMPLE_001"
        assert recipe.stencil.width_mm == 400
        assert recipe.tension.enabled is True
