"""
Reports Package

PDF report generation services for the AOI system.

This package contains:
- Specialized services: PDFGenerator, ChartGenerator, StatisticsCalculator, ReportLayoutManager
- Report builders: TensionReportBuilder, StencilHistoryReportBuilder
- Main facade: ReportGenerator (orchestrates all services and builders)

Usage:
    from aoi_lib.reports import ReportGenerator, ReportConfig

    config = ReportConfig(company_name="MinhaEmpresa")
    generator = ReportGenerator(config)

    # Generate reports
    path = generator.generate_tension_report(tension_data)
    path = generator.generate_stencil_history_report(stencil, history)
"""

# Specialized services
from .pdf_generator import PDFGenerator
from .chart_generator import ChartGenerator
from .statistics_calculator import StatisticsCalculator
from .report_layout_manager import ReportLayoutManager

# Report builders
from .builders import (
    TensionReportBuilder,
    StencilHistoryReportBuilder,
)

# Main facade
from .report_generator import ReportGenerator

# Config (import from parent module for compatibility)
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from report_generator import ReportConfig

__all__ = [
    # Services
    "PDFGenerator",
    "ChartGenerator",
    "StatisticsCalculator",
    "ReportLayoutManager",
    # Builders
    "TensionReportBuilder",
    "StencilHistoryReportBuilder",
    # Facade
    "ReportGenerator",
    # Config
    "ReportConfig",
]
