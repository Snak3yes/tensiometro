
import pytest
from pathlib import Path
from aoi_lib.recipe_manager import RecipeManager, Recipe, StencilInfo, TensionConfig, CaptureConfig, MACHINE_LIMITS

@pytest.fixture
def recipe_manager(tmp_path):
    return RecipeManager(recipes_dir=str(tmp_path))

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

def test_duplicate_recipe(recipe_manager):
    original = recipe_manager.create_recipe("Original")
    recipe_manager.save_recipe(original)
    
    dup = recipe_manager.duplicate_recipe(original.recipe_id, "Copy")
    assert dup is not None
    assert dup.name == "Copy"
    assert dup.recipe_id != original.recipe_id
    assert recipe_manager.load_recipe(dup.recipe_id) is not None
