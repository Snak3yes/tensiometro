import json

from aoi_lib.tensiometer.measurement_orchestrator import MeasurementOrchestrator
from aoi_lib.tensiometer.models import GridParameters, MeasurementSession
from aoi_lib.tensiometer import measurement_orchestrator


class _FakeSignal:
    def __init__(self):
        self._callbacks = []

    def connect(self, callback):
        self._callbacks.append(callback)

    def emit(self, *args, **kwargs):
        for callback in self._callbacks:
            callback(*args, **kwargs)


class _FakeThread:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.progress_updated = _FakeSignal()
        self.measurement_completed = _FakeSignal()
        self.finished = _FakeSignal()
        self.error_occurred = _FakeSignal()
        self.started = False
        self.stop_requested = False
        self.running = False

    def start(self):
        self.started = True
        self.running = True

    def isRunning(self):
        return self.running

    def request_stop(self):
        self.stop_requested = True
        self.running = False


def _build_orchestrator(tmp_path):
    return MeasurementOrchestrator(cnc=object(), tensiometer=object(), save_directory=tmp_path)


def test_prepare_measurement_returns_session_points_and_statistics(tmp_path):
    orchestrator = _build_orchestrator(tmp_path)

    result = orchestrator.prepare_measurement(
        start_point=(0.0, 0.0),
        end_point=(10.0, 10.0),
        grid_size=2,
        z_height=5.0,
        z_move=10.0,
    )

    assert result["success"] is True
    assert result["statistics"]["total_points"] == 4
    assert len(result["points"]) == 4
    assert orchestrator.session is result["session"]


def test_prepare_measurement_returns_validation_error_for_invalid_bounds(tmp_path):
    orchestrator = _build_orchestrator(tmp_path)

    result = orchestrator.prepare_measurement(
        start_point=(0.0, 0.0),
        end_point=(0.0, 0.0),
        grid_size=2,
        z_height=5.0,
        z_move=10.0,
    )

    assert result["success"] is False
    assert result["error_type"] == "validation"


def test_start_measurement_requires_prepared_session(tmp_path):
    orchestrator = _build_orchestrator(tmp_path)

    assert orchestrator.start_measurement(points=[]) is False


def test_start_measurement_builds_thread_and_connects_callbacks(tmp_path, monkeypatch):
    orchestrator = _build_orchestrator(tmp_path)
    prepared = orchestrator.prepare_measurement(
        start_point=(0.0, 0.0),
        end_point=(10.0, 10.0),
        grid_size=2,
        z_height=5.0,
        z_move=10.0,
    )
    monkeypatch.setattr(measurement_orchestrator, "TensionMeasurementThread", _FakeThread)

    progress_events = []

    started = orchestrator.start_measurement(
        points=prepared["points"],
        on_progress=lambda current, total, message: progress_events.append((current, total, message)),
    )

    assert started is True
    assert isinstance(orchestrator.thread, _FakeThread)
    assert orchestrator.thread.started is True

    orchestrator.thread.progress_updated.emit(1, 4, "medindo")

    assert progress_events == [(1, 4, "medindo")]


def test_handle_measurement_preserves_point_metadata_and_callback(tmp_path):
    orchestrator = _build_orchestrator(tmp_path)
    prepared = orchestrator.prepare_measurement(
        start_point=(0.0, 0.0),
        end_point=(10.0, 10.0),
        grid_size=2,
        z_height=5.0,
        z_move=10.0,
    )

    received = []
    orchestrator._on_measurement = received.append

    orchestrator._handle_measurement(
        {
            "index": 3,
            "grid_position": {"row": 1, "col": 1},
            "x": 10.0,
            "y": 10.0,
            "z": 5.0,
            "tension": "28.5",
        }
    )

    measurement = orchestrator.session.measurements[0]
    assert measurement.point.index == 3
    assert measurement.point.grid_position == (1, 1)
    assert received[0]["tension"] == "28.5"
    assert prepared["session"] is orchestrator.session


def test_handle_finished_saves_results_and_calls_complete_callback(tmp_path):
    orchestrator = _build_orchestrator(tmp_path)
    orchestrator.session = MeasurementSession(
        parameters=GridParameters(
            start_point=(0.0, 0.0),
            end_point=(10.0, 10.0),
            grid_size=2,
            z_height=5.0,
            z_move=10.0,
        )
    )
    orchestrator._handle_measurement(
        {
            "index": 0,
            "grid_position": {"row": 0, "col": 0},
            "x": 0.0,
            "y": 0.0,
            "z": 5.0,
            "tension": "30.0",
        }
    )

    completed = []
    orchestrator._on_complete = completed.append

    orchestrator._handle_finished([{"tension": "30.0"}])

    assert completed
    saved_path = completed[0]["saved_to"]
    assert saved_path is not None

    with open(saved_path, "r", encoding="utf-8") as stream:
        payload = json.load(stream)

    assert payload["measurements"][0]["index"] == 0
    assert payload["statistics"]["measured_points"] == 1
