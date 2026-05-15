import json

from aoi_lib.stencil_tracker import Stencil
from consumo_lib.controllers.tension_measurement_controller import TensionMeasurementController
from consumo_lib.managers.measurement_pattern_manager import MeasurementPatternManager


def _write_pattern(patterns_dir, name, grid_size, modified_at):
    path = patterns_dir / f"{name}.json"
    path.write_text(
        json.dumps(
            {
                "name": name,
                "description": "",
                "parameters": {
                    "start": {"x": 0.0, "y": 0.0},
                    "end": {"x": 100.0, "y": 100.0},
                    "grid_size": grid_size,
                    "measurement_height": 5.0,
                    "movement_height": 10.0,
                    "stabilization_time": 500,
                    "movement_feed": 1000.0,
                },
                "created_at": modified_at,
                "modified_at": modified_at,
                "created_by": "",
            }
        ),
        encoding="utf-8",
    )


def test_pattern_manager_resolves_sfcs_grid_by_grid_size(tmp_path):
    _write_pattern(tmp_path, "Padrao 4x4 antigo", 4, "2026-04-01T08:00:00")
    _write_pattern(tmp_path, "Padrao 4x4 atual", 4, "2026-04-01T09:00:00")
    manager = MeasurementPatternManager(patterns_dir=str(tmp_path))

    pattern = manager.resolve_pattern_for_grid("4x4")

    assert pattern is not None
    assert pattern.name == "Padrao 4x4 atual"
    assert pattern.grid_parameters.grid_size == 4


def test_controller_resolves_pattern_from_stencil_grid(tmp_path):
    _write_pattern(tmp_path, "Grid 3x3", 3, "2026-04-01T09:00:00")
    controller = TensionMeasurementController.__new__(TensionMeasurementController)
    controller.pattern_manager = MeasurementPatternManager(patterns_dir=str(tmp_path))

    pattern = controller._resolve_pattern_for_stencil(Stencil(code="ABC123", recipe_name="3x3"))

    assert pattern is not None
    assert pattern.name == "Grid 3x3"
