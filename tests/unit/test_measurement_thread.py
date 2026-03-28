from aoi_lib.tensiometer.measurement_thread import (
    TENSIOMETER_POWER_COIL,
    TENSIOMETER_POWER_OFF_PULSE_MS,
    TENSIOMETER_POWER_ON_PULSE_MS,
    TensionMeasurementThread,
)
from aoi_lib.tensiometer.models import GridPoint
from aoi_lib.tensiometer import measurement_thread


class _FakeCNC:
    def __init__(self):
        self.absolute_mode_calls = 0
        self.moves = []
        self.wait_calls = 0
        self.coils = []

    def set_absolute_mode(self):
        self.absolute_mode_calls += 1

    def move_to_absolute_position(self, **kwargs):
        self.moves.append(kwargs)

    def wait_for_idle(self):
        self.wait_calls += 1

    def pulse_coil(self, coil, duration_ms):
        self.coils.append((coil, duration_ms))


class _FakeTensiometer:
    def __init__(self, values):
        self.values = list(values)
        self.read_calls = 0

    def read_tension_value(self):
        self.read_calls += 1
        return self.values.pop(0)


def test_run_measures_all_points_and_toggles_tensiometer(monkeypatch):
    monkeypatch.setattr(measurement_thread.time, "sleep", lambda _: None)

    cnc = _FakeCNC()
    tensiometer = _FakeTensiometer(["30.0", "31.5"])
    points = [
        GridPoint(x=1.0, y=2.0, index=0, grid_position=(0, 0)),
        GridPoint(x=3.0, y=4.0, index=1, grid_position=(0, 1)),
    ]

    thread = TensionMeasurementThread(
        cnc=cnc,
        tensiometer=tensiometer,
        points=points,
        z_height=1.5,
        z_move=8.0,
        user_feed=900.0,
        stabilization_time_ms=0,
    )

    measurements = []
    finished_payload = []
    thread.measurement_completed.connect(measurements.append)
    thread.finished.connect(finished_payload.append)

    thread.run()

    assert cnc.absolute_mode_calls == 1
    assert cnc.coils == [
        (TENSIOMETER_POWER_COIL, TENSIOMETER_POWER_ON_PULSE_MS),
        (TENSIOMETER_POWER_COIL, TENSIOMETER_POWER_OFF_PULSE_MS),
    ]
    assert cnc.moves == [
        {"z": 8.0, "feed_rate": 900.0},
        {"x": 1.0, "y": 2.0, "z": 8.0, "feed_rate": 900.0},
        {"z": 1.5, "feed_rate": 900.0},
        {"z": 8.0, "feed_rate": 900.0},
        {"x": 3.0, "y": 4.0, "z": 8.0, "feed_rate": 900.0},
        {"z": 1.5, "feed_rate": 900.0},
        {"z": 8.0, "feed_rate": 900.0},
    ]
    assert [item["tension"] for item in measurements] == ["30.0", "31.5"]
    assert [item["index"] for item in measurements] == [0, 1]
    assert len(finished_payload) == 1
    assert len(finished_payload[0]) == 2
    assert tensiometer.read_calls == 2


def test_run_disables_tensiometer_even_when_stop_is_requested(monkeypatch):
    monkeypatch.setattr(measurement_thread.time, "sleep", lambda _: None)

    cnc = _FakeCNC()
    tensiometer = _FakeTensiometer(["30.0"])
    thread = TensionMeasurementThread(
        cnc=cnc,
        tensiometer=tensiometer,
        points=[GridPoint(x=1.0, y=2.0, index=0, grid_position=(0, 0))],
        z_height=1.5,
        z_move=8.0,
        user_feed=900.0,
        stabilization_time_ms=0,
    )
    thread.request_stop()

    errors = []
    thread.error_occurred.connect(errors.append)

    thread.run()

    assert cnc.coils == [
        (TENSIOMETER_POWER_COIL, TENSIOMETER_POWER_ON_PULSE_MS),
        (TENSIOMETER_POWER_COIL, TENSIOMETER_POWER_OFF_PULSE_MS),
    ]
    assert errors == ["Medicao interrompida pelo usuario"]
    assert tensiometer.read_calls == 0
