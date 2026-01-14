"""
reports package
---------------
Geração de relatórios PDF para o sistema AOI.
"""

from .config import ReportConfig, get_custom_styles
from .chart_generator import create_tension_map_chart, create_trend_chart
from .report_generator import ReportGenerator

# Builders
from .builders import (
    TensionReportBuilder,
    StencilHistoryReportBuilder,
    InspectionReportBuilder
)

__all__ = [
    # Config
    'ReportConfig',
    'get_custom_styles',

    # Chart generation
    'create_tension_map_chart',
    'create_trend_chart',

    # Main orchestrator
    'ReportGenerator',

    # Builders
    'TensionReportBuilder',
    'StencilHistoryReportBuilder',
    'InspectionReportBuilder',
]
