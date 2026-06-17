from aoi_lib.report_generator import (
    MEASUREMENT_REPORT_DIR_NAME,
    STENCIL_HISTORY_REPORT_DIR_NAME,
    _resolve_report_output_dir,
)


def test_measurement_report_output_dir_uses_ptbr_folder_name(tmp_path):
    output_dir = _resolve_report_output_dir(
        str(tmp_path),
        MEASUREMENT_REPORT_DIR_NAME,
    )

    assert output_dir.name == "Relatório de medição"
    assert output_dir.exists()


def test_stencil_history_report_output_dir_uses_requested_ptbr_folder_name(tmp_path):
    output_dir = _resolve_report_output_dir(
        str(tmp_path),
        STENCIL_HISTORY_REPORT_DIR_NAME,
    )

    assert output_dir.name == "Histórico de Stencil"
    assert output_dir.exists()
