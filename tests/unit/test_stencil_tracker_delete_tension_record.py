from aoi_lib.stencil_tracker import StencilTracker, TensionRecord


class _DummyChangeLog:
    def log_event(self, **kwargs):
        self.last_event = kwargs


def _record(timestamp: str, result: str, average: float) -> TensionRecord:
    return TensionRecord(
        timestamp=timestamp,
        measurements=[{"tension": average, "status": result}],
        average_tension=average,
        min_tension=average,
        max_tension=average,
        result=result,
        ok_count=1 if result == "OK" else 0,
        warning_count=1 if result == "WARNING" else 0,
        nok_count=1 if result == "NOK" else 0,
    )


def test_delete_tension_record_removes_only_selected_measurement_and_refreshes_metadata(
    tmp_path,
    monkeypatch,
):
    change_log = _DummyChangeLog()
    monkeypatch.setattr(
        "aoi_lib.stencil_tracker.get_system_change_log",
        lambda: change_log,
    )
    tracker = StencilTracker(data_dir=str(tmp_path / "stencils"))
    tracker.create_stencil("abc123")

    older = _record("2026-06-01T08:00:00", "OK", 38.0)
    newer = _record("2026-06-02T08:00:00", "NOK", 20.0)
    tracker.add_tension_record("abc123", older)
    tracker.add_tension_record("abc123", newer)

    assert tracker.delete_tension_record("abc123", newer.timestamp) is True

    history = tracker.get_tension_history("abc123")
    stencil = tracker.get_stencil("abc123")
    assert [record.timestamp for record in history] == [older.timestamp]
    assert stencil.inspection_count == 1
    assert stencil.last_inspection == older.timestamp
    assert stencil.status == "active"
    assert change_log.last_event["action"] == "tension_record_deleted"


def test_delete_last_tension_record_resets_stencil_measurement_metadata(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "aoi_lib.stencil_tracker.get_system_change_log",
        lambda: _DummyChangeLog(),
    )
    tracker = StencilTracker(data_dir=str(tmp_path / "stencils"))
    tracker.create_stencil("abc123")
    record = _record("2026-06-01T08:00:00", "WARNING", 29.0)
    tracker.add_tension_record("abc123", record)

    assert tracker.delete_tension_record("abc123", record.timestamp) is True

    stencil = tracker.get_stencil("abc123")
    assert tracker.get_tension_history("abc123") == []
    assert stencil.inspection_count == 0
    assert stencil.last_inspection is None
    assert stencil.status == "active"


def test_delete_tension_record_returns_false_when_timestamp_does_not_exist(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        "aoi_lib.stencil_tracker.get_system_change_log",
        lambda: _DummyChangeLog(),
    )
    tracker = StencilTracker(data_dir=str(tmp_path / "stencils"))
    tracker.create_stencil("abc123")
    record = _record("2026-06-01T08:00:00", "OK", 38.0)
    tracker.add_tension_record("abc123", record)

    assert tracker.delete_tension_record("abc123", "2026-06-02T08:00:00") is False
    assert [item.timestamp for item in tracker.get_tension_history("abc123")] == [record.timestamp]
