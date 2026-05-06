from aoi_lib.recipe_manager import TensionAcceptance
from aoi_lib.stencil_tracker import TensionRecord
from consumo_lib.services.tension_reclassification_service import reclassify_tension_record


def test_reclassify_tension_record_uses_current_criteria():
    record = TensionRecord(
        timestamp="2026-05-05T10:00:00",
        measurements=[
            {"x": 0, "y": 0, "tension": 40.0, "status": "WARNING"},
            {"x": 1, "y": 0, "tension": 49.0, "status": "WARNING"},
        ],
        average_tension=44.5,
        min_tension=40.0,
        max_tension=49.0,
        result="WARNING",
        ok_count=0,
        warning_count=2,
        nok_count=0,
    )

    updated = reclassify_tension_record(
        record,
        TensionAcceptance(
            min_tension=30.0,
            max_tension=50.0,
            warning_low=30.0,
            warning_high=34.0,
        ),
    )

    assert updated.result == "OK"
    assert updated.ok_count == 2
    assert updated.warning_count == 0
    assert [measurement["status"] for measurement in updated.measurements] == ["OK", "OK"]
