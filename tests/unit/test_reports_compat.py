from aoi_lib.reports import ReportConfig, ReportGenerator


def test_reports_module_exports_report_types():
    assert ReportConfig is not None
    assert ReportGenerator is not None
