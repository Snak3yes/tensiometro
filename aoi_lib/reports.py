"""
Compatibility exports for report-related classes.

Several application modules still import ``aoi_lib.reports`` even though the
implementation currently lives in ``aoi_lib.report_generator``. This shim keeps
those imports working without forcing broad call-site changes.
"""

from .report_generator import ReportConfig, ReportGenerator

__all__ = ["ReportConfig", "ReportGenerator"]
