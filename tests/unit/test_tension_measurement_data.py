from pathlib import Path

from aoi_lib.tensiometer.models import GridParameters, GridPoint, MeasurementSession, TensionMeasurement
from consumo_lib.utils.tension_measurement_data import (
    find_latest_tension_measurement_file,
    load_tension_measurement_data,
)


class _FakeOrchestrator:
    def __init__(self, session):
        self.session = session


class _FakeDialog:
    def __init__(self, session):
        self.orchestrator = _FakeOrchestrator(session)


def _build_session() -> MeasurementSession:
    session = MeasurementSession(
        parameters=GridParameters(
            start_point=(0.0, 0.0),
            end_point=(10.0, 10.0),
            grid_size=2,
            z_height=5.0,
            z_move=10.0,
        )
    )
    session.add_measurement(
        TensionMeasurement(
            point=GridPoint(x=1.0, y=2.0, index=0, grid_position=(0, 0)),
            z_height=5.0,
            tension_value="23.4",
        )
    )
    return session


def test_load_tension_measurement_data_prefers_dialog_session(tmp_path: Path):
    legacy_file = tmp_path / "stencil_tension_measurements.json"
    legacy_file.write_text('{"measurements": [{"tension": "99.9"}]}', encoding="utf-8")

    dialog = _FakeDialog(_build_session())

    data = load_tension_measurement_data(dialog, base_path=tmp_path)

    assert data["type"] == "stencil_tension_session"
    assert data["measurements"][0]["tension"] == "23.4"


def test_find_latest_tension_measurement_file_uses_new_orchestrator_output(tmp_path: Path):
    routines_dir = tmp_path / "tension_routines"
    routines_dir.mkdir()

    older = routines_dir / "tension_measurement_20260101_000000.json"
    newer = routines_dir / "tension_measurement_20260102_000000.json"
    older.write_text("{}", encoding="utf-8")
    newer.write_text('{"measurements": [{"tension": "12.0"}]}', encoding="utf-8")

    latest = find_latest_tension_measurement_file(tmp_path)

    assert latest == newer


def test_load_tension_measurement_data_reads_latest_saved_file(tmp_path: Path):
    routines_dir = tmp_path / "tension_routines"
    routines_dir.mkdir()
    saved_file = routines_dir / "tension_measurement_20260102_000000.json"
    saved_file.write_text('{"measurements": [{"tension": "31.0"}]}', encoding="utf-8")

    data = load_tension_measurement_data(base_path=tmp_path)

    assert data["measurements"][0]["tension"] == "31.0"
