import sys
from unittest.mock import Mock

import pytest
from PyQt6.QtWidgets import QApplication

from aoi_lib.stencil_tracker import Stencil


@pytest.fixture
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def test_create_dialog_saves_model_name_pattern_and_uppercase_code(qapp):
    from consumo_lib.dialogs.stencil.create_dialog import StencilCreateDialog

    tracker = Mock()
    tracker.stencil_exists.return_value = False
    tracker.create_stencil.return_value = Stencil(
        code="ABC123",
        description="Modelo X",
        recipe_name="PADRAO 3X3",
    )

    dialog = StencilCreateDialog(tracker)
    dialog.txt_model_name.setText("Modelo X")
    dialog.txt_pattern.setText("PADRAO 3X3")
    dialog.txt_code.setText("abc123")

    dialog._create()

    tracker.create_stencil.assert_called_once_with(
        code="ABC123",
        description="Modelo X",
        recipe_name="PADRAO 3X3",
    )


def test_manager_dialog_shows_measurement_pattern_column(qapp):
    from consumo_lib.dialogs.stencil.manager_dialog import StencilManagerDialog

    tracker = Mock()
    tracker.list_stencils.return_value = []

    dialog = StencilManagerDialog(tracker)

    headers = [
        dialog.table.horizontalHeaderItem(index).text()
        for index in range(dialog.table.columnCount())
    ]

    assert headers[:3] == ["Código", "Nome do modelo", "Padrão de medição"]


def test_tension_controller_builds_parameters_from_stencil_pattern():
    from aoi_lib.tensiometer.models import GridParameters, MeasurementPattern
    from consumo_lib.controllers.tension_measurement_controller import TensionMeasurementController

    controller = TensionMeasurementController.__new__(TensionMeasurementController)
    controller.config = Mock()
    controller.config.get.return_value = 750

    pattern = MeasurementPattern(
        name="PADRAO 3X3",
        grid_parameters=GridParameters(
            start_point=(10.0, 20.0),
            end_point=(110.0, 120.0),
            grid_size=3,
            z_height=5.0,
            z_move=15.0,
        ),
    )

    params = controller._build_measurement_parameters_from_pattern(pattern)

    assert params["grid_size"] == 3
    assert params["start_point"] == (10.0, 20.0)
    assert params["end_point"] == (110.0, 120.0)
    assert params["z_height"] == 5.0
    assert params["z_move"] == 15.0
    assert params["source_description"] == "padrão 'PADRAO 3X3'"
