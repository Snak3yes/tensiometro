
import pytest
from pathlib import Path
from aoi_lib.config_manager import AOIConfigManager
from aoi_lib.recipe_manager import RecipeManager, Recipe, StencilInfo, TensionConfig, CaptureConfig, MACHINE_LIMITS

@pytest.fixture
def recipe_manager(tmp_path):
    return RecipeManager(recipes_dir=str(tmp_path))


@pytest.fixture
def recipe_manager_with_custom_criteria(tmp_path):
    config_path = tmp_path / "aoi_config.json"
    config = AOIConfigManager(cfg_path=str(config_path))
    config.set("tension_criteria", "min_tension", value=31.0)
    config.set("tension_criteria", "max_tension", value=43.0)
    config.set("tension_criteria", "warning_low", value=33.0)
    config.set("tension_criteria", "warning_high", value=41.0)
    recipes_dir = tmp_path / "recipes"
    return RecipeManager(recipes_dir=str(recipes_dir), config_manager=config), config

def test_validate_valid_recipe(recipe_manager):
    recipe = recipe_manager.create_recipe("Valid Recipe")
    recipe.stencil.width_mm = 400
    recipe.stencil.height_mm = 300
    recipe.capture.step_x = 10
    recipe.capture.step_y = 10
    
    errors = recipe.validate()
    assert len(errors) == 0

def test_validate_invalid_dimensions(recipe_manager):
    recipe = recipe_manager.create_recipe("Invalid Dims")
    recipe.stencil.width_mm = MACHINE_LIMITS["max_width_mm"] + 10
    recipe.stencil.height_mm = -5
    
    errors = recipe.validate()
    assert any("Largura excede" in e for e in errors)
    assert any("Altura do stencil" in e for e in errors)

def test_validate_invalid_tension_grid(recipe_manager):
    recipe = recipe_manager.create_recipe("Invalid Grid")
    recipe.tension.enabled = True
    recipe.tension.grid_rows = 0
    
    errors = recipe.validate()
    assert any("Grid de tensão" in e for e in errors)

def test_validate_invalid_tension_area(recipe_manager):
    recipe = recipe_manager.create_recipe("Invalid Area")
    recipe.stencil.width_mm = 100
    recipe.stencil.height_mm = 100
    recipe.tension.enabled = True
    # Start point outside
    recipe.tension.start_point.x = 150
    
    errors = recipe.validate()
    assert any("Área de tensão excede" in e for e in errors)

def test_validate_invalid_capture_step(recipe_manager):
    recipe = recipe_manager.create_recipe("Invalid Step")
    recipe.capture.step_x = 0.05 # Limit is 0.1
    
    errors = recipe.validate()
    assert any("Steps de captura muito pequenos" in e for e in errors)

def test_crud_operations(recipe_manager):
    # Create
    recipe = recipe_manager.create_recipe("CRUD Test")
    recipe.stencil.width_mm = 200
    
    # Save
    assert recipe_manager.save_recipe(recipe) is True
    assert (recipe_manager.recipes_dir / f"{recipe.recipe_id}.json").exists()
    
    # Load
    loaded = recipe_manager.load_recipe(recipe.recipe_id)
    assert loaded is not None
    assert loaded.name == "CRUD Test"
    assert loaded.stencil.width_mm == 200
    
    # List
    recipes = recipe_manager.list_recipes()
    assert len(recipes) == 1
    assert recipes[0]['name'] == "CRUD Test"
    
    # Delete
    assert recipe_manager.delete_recipe(recipe.recipe_id) is True
    assert len(recipe_manager.list_recipes()) == 0


def test_create_recipe_uses_global_tension_criteria(recipe_manager_with_custom_criteria):
    manager, _ = recipe_manager_with_custom_criteria

    recipe = manager.create_recipe("Global Criteria")

    assert recipe.tension.acceptance.min_tension == 31.0
    assert recipe.tension.acceptance.max_tension == 43.0
    assert recipe.tension.acceptance.warning_low == 33.0
    assert recipe.tension.acceptance.warning_high == 41.0


def test_load_recipe_overrides_stored_acceptance_with_global_criteria(recipe_manager_with_custom_criteria, tmp_path):
    manager, _ = recipe_manager_with_custom_criteria
    recipe = Recipe(name="Stored Criteria")
    recipe.tension.enabled = True
    recipe.tension.acceptance.min_tension = 10.0
    recipe.tension.acceptance.max_tension = 90.0
    recipe.tension.acceptance.warning_low = 20.0
    recipe.tension.acceptance.warning_high = 80.0

    raw_file = Path(manager.recipes_dir) / "stored_recipe.json"
    raw_file.parent.mkdir(parents=True, exist_ok=True)
    raw_file.write_text(recipe.to_json(indent=2), encoding="utf-8")

    loaded = manager.load_recipe("stored_recipe")

    assert loaded is not None
    assert loaded.tension.acceptance.min_tension == 31.0
    assert loaded.tension.acceptance.max_tension == 43.0
    assert loaded.tension.acceptance.warning_low == 33.0
    assert loaded.tension.acceptance.warning_high == 41.0


def test_save_recipe_persists_global_tension_criteria(recipe_manager_with_custom_criteria):
    manager, _ = recipe_manager_with_custom_criteria
    recipe = manager.create_recipe("Persist Global Criteria")
    recipe.tension.enabled = True
    recipe.tension.acceptance.min_tension = 5.0
    recipe.tension.acceptance.max_tension = 95.0
    recipe.tension.acceptance.warning_low = 10.0
    recipe.tension.acceptance.warning_high = 90.0

    assert manager.save_recipe(recipe) is True

    saved_data = Path(manager.recipes_dir, f"{recipe.recipe_id}.json").read_text(encoding="utf-8")
    loaded = Recipe.from_json(saved_data)

    assert loaded.tension.acceptance.min_tension == 31.0
    assert loaded.tension.acceptance.max_tension == 43.0
    assert loaded.tension.acceptance.warning_low == 33.0
    assert loaded.tension.acceptance.warning_high == 41.0

def test_duplicate_recipe(recipe_manager):
    original = recipe_manager.create_recipe("Original")
    recipe_manager.save_recipe(original)

    dup = recipe_manager.duplicate_recipe(original.recipe_id, "Copy")
    assert dup is not None
    assert dup.name == "Copy"
    assert dup.recipe_id != original.recipe_id
    assert recipe_manager.load_recipe(dup.recipe_id) is not None

# ===== NOVOS TESTES PARA COBRIR LINHAS FALTANTES =====

def test_point3d_to_dict(recipe_manager):
    """Cobre linha 67: Point3D.to_dict()"""
    from aoi_lib.recipe_manager import Point3D
    point = Point3D(x=1.0, y=2.0, z=3.0)
    result = point.to_dict()
    assert result == {"x": 1.0, "y": 2.0, "z": 3.0}

def test_tension_acceptance_classify_nok_low(recipe_manager):
    """Cobre linha 123: TensionAcceptance.classify() - NOK baixo"""
    from aoi_lib.recipe_manager import TensionAcceptance
    acc = TensionAcceptance(min_tension=25.0, max_tension=45.0)
    result = acc.classify(20.0)  # Abaixo do mínimo
    assert result == "NOK"

def test_tension_acceptance_classify_nok_high(recipe_manager):
    """Cobre linha 123: TensionAcceptance.classify() - NOK alto"""
    from aoi_lib.recipe_manager import TensionAcceptance
    acc = TensionAcceptance(min_tension=25.0, max_tension=45.0)
    result = acc.classify(50.0)  # Acima do máximo
    assert result == "NOK"

def test_tension_acceptance_classify_warning_low(recipe_manager):
    """Cobre linha 125: TensionAcceptance.classify() - WARNING baixo"""
    from aoi_lib.recipe_manager import TensionAcceptance
    acc = TensionAcceptance(min_tension=25.0, max_tension=45.0, warning_low=28.0)
    result = acc.classify(26.0)  # Entre min e warning_low
    assert result == "WARNING"

def test_tension_acceptance_classify_warning_high(recipe_manager):
    """Valores acima do warning_high e dentro do maximo devem ser OK."""
    from aoi_lib.recipe_manager import TensionAcceptance
    acc = TensionAcceptance(min_tension=25.0, max_tension=45.0, warning_high=42.0)
    result = acc.classify(44.0)  # Entre warning_high e max
    assert result == "OK"

def test_tension_acceptance_classify_warning_boundary(recipe_manager):
    """Valor no limite warning_high ainda deve ser WARNING."""
    from aoi_lib.recipe_manager import TensionAcceptance
    acc = TensionAcceptance(min_tension=30.0, max_tension=50.0, warning_high=34.0)
    assert acc.classify(34.0) == "WARNING"
    assert acc.classify(34.1) == "OK"
    assert acc.classify(50.0) == "OK"

def test_tension_acceptance_classify_ok(recipe_manager):
    """Cobre linha 127: TensionAcceptance.classify() - OK"""
    from aoi_lib.recipe_manager import TensionAcceptance
    acc = TensionAcceptance(min_tension=25.0, max_tension=45.0, warning_low=28.0, warning_high=42.0)
    result = acc.classify(42.1)  # Acima do warning_high e dentro do maximo
    assert result == "OK"

def test_recipe_from_json(recipe_manager):
    """Cobre linhas 314-315: Recipe.from_json()"""
    import json
    recipe_data = {
        "name": "Test Recipe",
        "recipe_id": "TEST_001",
        "stencil": {"width_mm": 400, "height_mm": 300, "thickness_mm": 0.12, "material": "Inox", "notes": ""},
        "tension_config": {"enabled": True, "grid_rows": 3, "grid_cols": 3},
        "capture_config": {"enabled": True, "step_x": 50, "step_y": 50},
        "inspection_config": {"enabled": False}
    }
    json_str = json.dumps(recipe_data)
    recipe = Recipe.from_json(json_str)
    assert recipe.name == "Test Recipe"
    assert recipe.recipe_id == "TEST_001"

def test_validate_empty_name(recipe_manager):
    """Cobre linha 332: Validação de nome vazio"""
    recipe = recipe_manager.create_recipe("")
    errors = recipe.validate()
    assert any("Nome da receita não pode estar vazio" in e for e in errors)

def test_validate_zero_width(recipe_manager):
    """Cobre linha 336: Validação de largura zero"""
    recipe = recipe_manager.create_recipe("Zero Width")
    recipe.stencil.width_mm = 0
    errors = recipe.validate()
    assert any("Largura do stencil deve ser maior que zero" in e for e in errors)

def test_validate_max_height_exceeded(recipe_manager):
    """Cobre linha 343: Validação de altura máxima"""
    recipe = recipe_manager.create_recipe("Max Height")
    recipe.stencil.height_mm = MACHINE_LIMITS["max_height_mm"] + 10
    errors = recipe.validate()
    assert any("Altura excede limite" in e for e in errors)

def test_validate_min_tension_below_limit(recipe_manager):
    """Cobre linha 352: Validação de tensão mínima abaixo do limite físico"""
    recipe = recipe_manager.create_recipe("Min Tension")
    recipe.tension.enabled = True
    recipe.tension.acceptance.min_tension = MACHINE_LIMITS["min_tension"] - 1
    errors = recipe.validate()
    assert any("Tensão mínima abaixo do limite físico" in e for e in errors)

def test_validate_max_tension_above_limit(recipe_manager):
    """Cobre linha 354: Validação de tensão máxima acima do limite físico"""
    recipe = recipe_manager.create_recipe("Max Tension")
    recipe.tension.enabled = True
    recipe.tension.acceptance.max_tension = MACHINE_LIMITS["max_tension"] + 10
    errors = recipe.validate()
    assert any("Tensão máxima acima do limite físico" in e for e in errors)

def test_validate_min_tension_greater_than_max(recipe_manager):
    """Cobre linha 356: Validação de min >= max"""
    recipe = recipe_manager.create_recipe("Min >= Max")
    recipe.tension.enabled = True
    recipe.tension.acceptance.min_tension = 40.0
    recipe.tension.acceptance.max_tension = 35.0
    errors = recipe.validate()
    assert any("Tensão mínima deve ser menor que máxima" in e for e in errors)

def test_validate_negative_tension_points(recipe_manager):
    """Cobre linha 362: Validação de pontos negativos"""
    recipe = recipe_manager.create_recipe("Negative Points")
    recipe.tension.enabled = True
    recipe.tension.start_point.x = -10
    errors = recipe.validate()
    assert any("Pontos de medição não podem ser negativos" in e for e in errors)

def test_recipe_manager_default_directory(recipe_manager):
    """Cobre linhas 395-396: RecipeManager com diretório padrão"""
    from aoi_lib.recipe_manager import RecipeManager, DEFAULT_RECIPES_DIR
    import sys
    from pathlib import Path

    # Remove recipes_dir para usar o padrão
    manager = RecipeManager(recipes_dir=None)
    # Verifica que o diretório padrão foi usado
    assert DEFAULT_RECIPES_DIR in str(manager.recipes_dir)

def test_list_recipes_empty_directory(recipe_manager, tmp_path):
    """Cobre linha 419: list_recipes com diretório vazio"""
    empty_dir = tmp_path / "empty_recipes"
    empty_dir.mkdir()
    manager = RecipeManager(recipes_dir=str(empty_dir))
    recipes = manager.list_recipes()
    assert recipes == []

def test_save_recipe_invalid(recipe_manager):
    """Cobre linhas 500-501: save_recipe com validação falhando"""
    recipe = recipe_manager.create_recipe("")  # Nome vazio = inválido
    result = recipe_manager.save_recipe(recipe)
    assert result is False

def test_load_recipe_json_error(recipe_manager):
    """Cobre linhas 431-432, 464-465, 478-480: load_recipe com JSON corrompido"""
    import json

    # Cria um arquivo JSON inválido
    invalid_file = recipe_manager.recipes_dir / "invalid.json"
    with open(invalid_file, 'w') as f:
        f.write("{invalid json content")

    # Tenta carregar - deve retornar None sem crashar
    result = recipe_manager.load_recipe("invalid")
    assert result is None

def test_delete_recipe_not_found(recipe_manager):
    """Cobre linhas 553-568, 578-582: delete_recipe quando não encontrado"""
    result = recipe_manager.delete_recipe("nonexistent")
    assert result is False

def test_duplicate_recipe_not_found(recipe_manager):
    """Cobre linhas 597, 610: duplicate_recipe quando original não existe"""
    result = recipe_manager.duplicate_recipe("nonexistent", "Copy")
    assert result is None

def test_duplicate_recipe_save_fails(recipe_manager):
    """Cobre linha 610: duplicate_recipe quando save falha"""
    recipe = recipe_manager.create_recipe("Original")
    recipe_manager.save_recipe(recipe)

    # Tenta duplicar com nome vazio (vai falhar validação)
    dup = recipe_manager.duplicate_recipe(recipe.recipe_id, "")
    # O resultado deve ser None porque save_recipe falhou
    assert dup is None

def test_set_current_recipe(recipe_manager):
    """Cobre linha 614: set_current_recipe"""
    recipe = recipe_manager.create_recipe("Current")
    recipe_manager.set_current_recipe(recipe)
    assert recipe_manager.get_current_recipe() == recipe

def test_get_current_recipe_none(recipe_manager):
    """Cobre linha 618: get_current_recipe quando None"""
    result = recipe_manager.get_current_recipe()
    assert result is None

def test_create_sample_recipe(recipe_manager):
    """Cobre linhas 626-642: create_sample_recipe()"""
    from aoi_lib.recipe_manager import create_sample_recipe
    recipe = create_sample_recipe()
    assert recipe.name == "Stencil Exemplo PCB"
    assert recipe.recipe_id == "SAMPLE_001"
    assert recipe.stencil.width_mm == 400
    assert recipe.stencil.height_mm == 300
    assert recipe.tension.enabled is True
    assert recipe.tension.grid_rows == 3
    assert recipe.tension.grid_cols == 3
    assert recipe.capture.enabled is True
    assert recipe.capture.step_x == 50
    assert recipe.capture.step_y == 50

# ===== TESTES ADICIONAIS PARA COBRIR LINHAS RESTANTES =====

def test_point3d_from_dict(recipe_manager):
    """Cobre linha 71: Point3D.from_dict()"""
    from aoi_lib.recipe_manager import Point3D
    data = {"x": 1.0, "y": 2.0, "z": 3.0}
    point = Point3D.from_dict(data)
    assert point.x == 1.0
    assert point.y == 2.0
    assert point.z == 3.0

def test_list_recipes_nonexistent_directory(recipe_manager, tmp_path):
    """Cobre linha 419: list_recipes quando diretório não existe"""
    import os
    nonexistent_dir = tmp_path / "nonexistent"
    manager = RecipeManager(recipes_dir=str(nonexistent_dir))
    # Remove o diretório criado pelo __init__
    if manager.recipes_dir.exists():
        os.rmdir(manager.recipes_dir)
    recipes = manager.list_recipes()
    assert recipes == []

def test_load_recipe_by_content_id(recipe_manager):
    """Cobre linhas 454-461: load_recipe buscando por recipe_id dentro dos arquivos"""
    # Cria uma receita e salva com nome diferente do ID
    recipe = recipe_manager.create_recipe("Test Recipe")
    custom_filename = "custom_recipe_name"
    recipe_manager.save_recipe(recipe, filename=custom_filename)

    # Tenta carregar pelo recipe_id (não pelo filename)
    loaded = recipe_manager.load_recipe(recipe.recipe_id)
    assert loaded is not None
    assert loaded.name == "Test Recipe"

def test_delete_recipe_by_content_id(recipe_manager):
    """Cobre linhas 560-568: delete_recipe buscando por recipe_id"""
    # Cria uma receita e salva com nome diferente do ID
    recipe = recipe_manager.create_recipe("Delete Test")
    custom_filename = "custom_delete_recipe"
    recipe_manager.save_recipe(recipe, filename=custom_filename)

    # Deleta pelo recipe_id (não pelo filename)
    result = recipe_manager.delete_recipe(recipe.recipe_id)
    assert result is True
    # Verifica que foi deletado
    assert not (recipe_manager.recipes_dir / f"{custom_filename}.json").exists()
