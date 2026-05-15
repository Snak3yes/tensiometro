from consumo_lib.services.sfcs_stencil_lookup_service import (
    SfcsStencilLookupService,
    SfcsStencilRecord,
)


class _Config:
    def __init__(self, data):
        self.data = data

    def get(self, *path, default=None):
        ref = self.data
        for part in path:
            if part not in ref:
                return default
            ref = ref[part]
        return ref


def test_build_endpoint_url_replaces_barcode_placeholder():
    service = SfcsStencilLookupService(
        _Config(
            {
                "sfcs_stencil_lookup": {
                    "endpoint_url": "http://server/sfcs-print/stencil/{codigo_barras}",
                }
            }
        )
    )

    assert service._build_endpoint_url("teste 123") == "http://server/sfcs-print/stencil/teste%20123"


def test_parse_payload_maps_sfcs_fields_to_record_and_stencil():
    service = SfcsStencilLookupService()
    record = service._parse_payload(
        {
            "t2_nmdescmodelo": "LEGIONS (R7) MB",
            "idstencil": 745,
            "codigo_barras": "teste 123",
            "tipo": 1,
            "stencil_status": "DISPONIVEL",
            "grid": "4x4",
        },
        fallback_code="fallback",
    )

    stencil = record.to_stencil(recipe_name="PADRAO_4X4")

    assert record.code == "TESTE 123"
    assert record.description == "LEGIONS (R7) MB"
    assert record.grid == "4x4"
    assert record.sfcs_id == 745
    assert stencil.code == "TESTE 123"
    assert stencil.description == "LEGIONS (R7) MB"
    assert stencil.recipe_name == "PADRAO_4X4"
    assert stencil.status == "active"


def test_resolve_recipe_name_uses_grid_pattern_map_when_configured():
    service = SfcsStencilLookupService(
        _Config(
            {
                "sfcs_stencil_lookup": {
                    "grid_pattern_map": {"4x4": "LOQ IRX9"},
                }
            }
        )
    )
    record = SfcsStencilRecord(
        code="ABC",
        description="Modelo",
        grid="4x4",
        sfcs_id=1,
        stencil_type=1,
        sfcs_status="DISPONIVEL",
        raw_payload={},
    )

    assert service.resolve_recipe_name(record) == "LOQ IRX9"


def test_resolve_recipe_name_falls_back_to_pattern_grid(monkeypatch):
    class _Pattern:
        name = "Padrao 4x4"

    class _PatternManager:
        def resolve_pattern_for_grid(self, grid):
            assert grid == "4x4"
            return _Pattern()

    monkeypatch.setattr(
        "consumo_lib.managers.measurement_pattern_manager.MeasurementPatternManager",
        _PatternManager,
    )
    service = SfcsStencilLookupService(_Config({"sfcs_stencil_lookup": {"grid_pattern_map": {}}}))
    record = SfcsStencilRecord(
        code="ABC",
        description="Modelo",
        grid="4x4",
        sfcs_id=1,
        stencil_type=1,
        sfcs_status="DISPONIVEL",
        raw_payload={},
    )

    assert service.resolve_recipe_name(record) == "Padrao 4x4"
