from unittest.mock import Mock

from aoi_lib.recipe_manager import TensionAcceptance
from aoi_lib.stencil_tracker import Stencil, TensionRecord
from consumo_lib.controllers.tension_measurement_controller import TensionMeasurementController


class _Signal:
    def emit(self, *args):
        return None


def _controller():
    controller = TensionMeasurementController.__new__(TensionMeasurementController)
    controller._last_external_send_attempt = None
    return controller


def test_nok_measurement_is_eligible_for_external_send_with_rejected_flag():
    controller = _controller()
    record = TensionRecord(
        timestamp="2026-04-30T10:00:00",
        measurements=[{"status": "OK"}, {"status": "NOK"}],
        result="NOK",
        ok_count=1,
        warning_count=0,
        nok_count=1,
    )

    assert controller._should_send_external_integration(record) is True
    assert controller._is_external_payload_approved(record) is False


def test_ok_measurement_is_eligible_for_external_send():
    controller = _controller()
    record = TensionRecord(
        timestamp="2026-04-30T10:00:00",
        measurements=[{"status": "OK"}, {"status": "WARNING"}],
        result="WARNING",
        ok_count=1,
        warning_count=1,
        nok_count=0,
    )

    assert controller._should_send_external_integration(record) is True
    assert controller._is_external_payload_approved(record) is True


def test_empty_measurement_skip_status_keeps_payload_local_only():
    controller = _controller()

    controller._mark_external_integration_skipped_for_empty_measurement(Stencil(code="ABC123"))

    assert controller._last_external_send_attempt == {
        "success": None,
        "skipped": True,
        "skip_reason": "empty_measurement",
        "error": None,
        "status_code": None,
        "payload_path": None,
        "send_log_path": None,
    }
    assert controller._build_external_send_status_text() == "Envio API: não executado (sem pontos)"


def test_classify_measurements_marks_values_above_warning_high_as_ok():
    controller = _controller()
    controller._get_global_acceptance_criteria = Mock(
        return_value=TensionAcceptance(
            min_tension=30.0,
            max_tension=50.0,
            warning_low=30.0,
            warning_high=34.0,
        )
    )

    classified = controller._classify_measurements_by_recipe(
        {
            "measurements": [
                {"tension": 34.0},
                {"tension": 34.1},
                {"tension": 50.0},
            ]
        },
        current_recipe=None,
    )

    assert [m["status"] for m in classified["measurements"]] == ["WARNING", "OK", "OK"]


def test_save_measurement_sends_nok_to_external_payload_with_approved_false():
    controller = _controller()
    controller.stencil_manager_wrapper = Mock()
    controller.stencil_manager_wrapper.add_tension_record.return_value = True
    controller.measurement_completed = _Signal()
    controller.measurement_saved = _Signal()
    controller._get_global_acceptance_criteria = Mock(return_value=None)
    controller._resolve_report_operator = Mock(return_value="operador")
    controller._classify_measurements_by_recipe = Mock(side_effect=lambda tension_data, recipe: tension_data)
    controller._enrich_report_tension_data = Mock(side_effect=lambda tension_data, **kwargs: tension_data)
    controller._persist_measurement_session_report_data = Mock()
    controller._save_external_integration_payload = Mock()

    record = controller._save_measurement_data(
        current_stencil=Stencil(code="ABC123"),
        current_recipe=None,
        tension_data={
            "measurements": [
                {"point": 1, "tension": 33.0, "status": "OK"},
                {"point": 2, "tension": 18.0, "status": "NOK"},
            ],
            "parameters": {},
        },
        emit_signals=False,
    )

    assert record.result == "NOK"
    controller._save_external_integration_payload.assert_called_once()
    assert controller._save_external_integration_payload.call_args.kwargs["approved"] is False
