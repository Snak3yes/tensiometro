import sys

import pytest
from PyQt6.QtWidgets import QApplication, QWidget, QAbstractSpinBox

from aoi_lib.config_manager import AOIConfigManager
from consumo_lib.dialogs.recipe.recipe_edit_dialog import RecipeEditorDialog
from consumo_lib.widgets.tension_viz import TensionVisualizationWidget


@pytest.fixture
def qapp():
    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance()
    return app


@pytest.fixture
def configured_parent(tmp_path, qapp):
    config_path = tmp_path / "aoi_config.json"
    config = AOIConfigManager(cfg_path=str(config_path))
    config.set("tension_criteria", "min_tension", value=30.0)
    config.set("tension_criteria", "max_tension", value=44.0)
    config.set("tension_criteria", "warning_low", value=32.0)
    config.set("tension_criteria", "warning_high", value=40.0)

    parent = QWidget()
    parent.config_manager = config
    return parent, config


def test_recipe_editor_displays_global_criteria_as_read_only(configured_parent):
    parent, _ = configured_parent

    dialog = RecipeEditorDialog(parent=parent)

    assert dialog.spin_tension_min.value() == 30.0
    assert dialog.spin_tension_max.value() == 44.0
    assert dialog.spin_warning_low.value() == 32.0
    assert dialog.spin_warning_high.value() == 40.0
    assert dialog.spin_tension_min.isReadOnly() is True
    assert dialog.spin_tension_max.isReadOnly() is True
    assert dialog.spin_warning_low.isReadOnly() is True
    assert dialog.spin_warning_high.isReadOnly() is True
    assert dialog.spin_tension_min.buttonSymbols() == QAbstractSpinBox.ButtonSymbols.NoButtons


def test_tension_visualization_displays_global_criteria_as_read_only(configured_parent):
    parent, _ = configured_parent

    widget = TensionVisualizationWidget(parent=parent)

    assert widget.spin_min.value() == 30.0
    assert widget.spin_max.value() == 44.0
    assert widget.spin_warn_low.value() == 32.0
    assert widget.spin_warn_high.value() == 40.0
    assert widget.spin_min.isReadOnly() is True
    assert widget.spin_max.isReadOnly() is True
    assert widget.spin_warn_low.isReadOnly() is True
    assert widget.spin_warn_high.isReadOnly() is True
    assert widget.spin_min.buttonSymbols() == QAbstractSpinBox.ButtonSymbols.NoButtons
