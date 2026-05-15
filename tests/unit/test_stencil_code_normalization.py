from aoi_lib.stencil_tracker import Stencil, StencilTracker, normalize_stencil_code
from consumo_lib.services.tension_external_payload_service import TensionExternalPayloadService


def test_normalize_stencil_code_uppercases_and_strips():
    assert normalize_stencil_code(" 75b01a849403741 ") == "75B01A849403741"


def test_stencil_model_normalizes_code_to_uppercase():
    stencil = Stencil(code="abc123")

    assert stencil.code == "ABC123"


def test_stencil_tracker_creates_and_gets_lowercase_code_as_uppercase(tmp_path):
    tracker = StencilTracker(data_dir=str(tmp_path))

    created = tracker.create_stencil("abc123", description="Teste")
    fetched = tracker.get_stencil("abc123")

    assert created.code == "ABC123"
    assert fetched is not None
    assert fetched.code == "ABC123"
    assert (tmp_path / "ABC123" / "info.json").exists()


def test_external_payload_uppercases_stencil_code():
    service = TensionExternalPayloadService()

    payload = service.build_payload(
        stencil_code="75b01a849403741",
        measurements=[{"index": 0, "tension": "33.1"}],
    )

    assert payload["codigo_stencil"] == "75B01A849403741"


def test_external_payload_includes_approved_flag():
    service = TensionExternalPayloadService()

    payload = service.build_payload(
        stencil_code="ABC123",
        measurements=[{"index": 0, "tension": "33.1"}],
        approved=False,
    )

    assert payload["aprovado"] is False


def test_external_payload_always_sends_line_as_null():
    service = TensionExternalPayloadService()

    payload = service.build_payload(
        stencil_code="ABC123",
        measurements=[{"index": 0, "tension": "33.1"}],
        line_name="IMC4-LM03",
    )

    assert payload["nmlinha"] is None
