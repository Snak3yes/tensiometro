"""
Report Layout Manager Service

Layout and formatting service for report generation.
Responsible for table styles, number formatting, date formatting, and color management.
"""

import logging
from typing import Dict, Tuple, Optional, Any
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import TableStyle

# Import ReportConfig from parent module
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from report_generator import ReportConfig

log = logging.getLogger(__name__)


class ReportLayoutManager:
    """
    Report layout and formatting manager.

    Responsibilities:
    - Create table styles
    - Format numbers and dates
    - Get status colors
    - Create section titles
    - Create info table rows
    - Calculate image widths

    This service isolates all layout/formatting logic, making it easier
    to test and maintain report builders.
    """

    def __init__(self, config: ReportConfig):
        """
        Initialize layout manager with report configuration.

        Args:
            config: Report configuration with colors, logo, etc.
        """
        self.config = config

    # ======================================================================== #
    # TABLE STYLES
    # ======================================================================== #

    def create_table_style(
        self,
        has_header: bool = True,
        primary_color: bool = True,
        grid: bool = True
    ) -> TableStyle:
        """
        Create default table style.

        Args:
            has_header: Include header row styling
            primary_color: Use theme primary color for header
            grid: Show grid lines

        Returns:
            ReportLab TableStyle object
        """
        style = [
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]

        if grid:
            style.append(('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey))

        if has_header:
            if primary_color:
                bg_color = colors.Color(*[c/255 for c in self.config.primary_color])
                text_color = colors.whitesmoke
            else:
                bg_color = colors.Color(0.9, 0.9, 0.9)
                text_color = colors.black

            style.extend([
                ('BACKGROUND', (0, 0), (-1, 0), bg_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), text_color),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ])

        return TableStyle(style)

    def create_info_table_style(self) -> TableStyle:
        """
        Create style for information tables (label-value pairs).

        Returns:
            ReportLab TableStyle object
        """
        return TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.gray),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ])

    # ======================================================================== #
    # FORMATTING METHODS
    # ======================================================================== #

    def format_number(
        self,
        value: Any,
        decimals: int = 2
    ) -> str:
        """
        Format number for display.

        Args:
            value: Number to format
            decimals: Number of decimal places

        Returns:
            Formatted number string
        """
        if value is None:
            return "-"
        try:
            return f"{float(value):.{decimals}f}"
        except (ValueError, TypeError):
            return str(value)

    def format_percentage(
        self,
        value: Any,
        decimals: int = 1
    ) -> str:
        """
        Format number as percentage.

        Args:
            value: Number (0-100)
            decimals: Number of decimal places

        Returns:
            Formatted percentage string
        """
        if value is None:
            return "-"
        try:
            return f"{float(value):.{decimals}f}%"
        except (ValueError, TypeError):
            return str(value)

    def format_date(
        self,
        date: Any,
        format_str: str = "%d/%m/%Y %H:%M"
    ) -> str:
        """
        Format date for display.

        Args:
            date: Datetime object or string
            format_str: Format string

        Returns:
            Formatted date string
        """
        if date is None:
            return "-"

        if isinstance(date, str):
            try:
                date = datetime.fromisoformat(date)
            except ValueError:
                return date

        if isinstance(date, datetime):
            return date.strftime(format_str)

        return str(date)

    def format_datetime(
        self,
        dt: Any,
        format_str: str = "%d/%m/%Y %H:%M:%S"
    ) -> str:
        """
        Format datetime for display.

        Args:
            dt: Datetime object or string
            format_str: Format string

        Returns:
            Formatted datetime string
        """
        return self.format_date(dt, format_str)

    # ======================================================================== #
    # COLOR MANAGEMENT
    # ======================================================================== #

    def get_status_color(
        self,
        status: str
    ) -> Tuple[int, int, int]:
        """
        Get color for status.

        Args:
            status: Status string (OK, WARNING, NOK)

        Returns:
            RGB color tuple
        """
        status_map = {
            'OK': self.config.success_color,
            'WARNING': self.config.warning_color,
            'WARN': self.config.warning_color,
            'NOK': self.config.danger_color,
        }
        return status_map.get(status.upper(), (128, 128, 128))

    def get_status_color_reportlab(
        self,
        status: str
    ) -> colors.Color:
        """
        Get ReportLab Color object for status.

        Args:
            status: Status string (OK, WARNING, NOK)

        Returns:
            ReportLab Color object
        """
        r, g, b = self.get_status_color(status)
        return colors.Color(r/255, g/255, b/255)

    def get_theme_color(
        self,
        color_name: str
    ) -> Tuple[int, int, int]:
        """
        Get theme color by name.

        Args:
            color_name: 'primary', 'success', 'warning', 'danger'

        Returns:
            RGB color tuple

        Raises:
            KeyError: If color name not found
        """
        color_map = {
            'primary': self.config.primary_color,
            'success': self.config.success_color,
            'warning': self.config.warning_color,
            'danger': self.config.danger_color,
        }

        if color_name not in color_map:
            raise KeyError(
                f"Color '{color_name}' not found. "
                f"Available: {list(color_map.keys())}"
            )

        return color_map[color_name]

    # ======================================================================== #
    # LAYOUT HELPERS
    # ======================================================================== #

    def create_section_title(
        self,
        title: str,
        level: int = 2
    ) -> str:
        """
        Create section title.

        Args:
            title: Title text
            level: Heading level (1 or 2)

        Returns:
            Formatted title string
        """
        prefix = "#" * level
        return f"{prefix} {title}"

    def create_info_row(
        self,
        label: str,
        value: Any
    ) -> Tuple[str, str]:
        """
        Create row for information table (label-value pair).

        Args:
            label: Label text
            value: Value (any type)

        Returns:
            Tuple of (label, formatted_value)
        """
        if isinstance(value, (int, float)):
            formatted = self.format_number(value)
        elif isinstance(value, datetime):
            formatted = self.format_datetime(value)
        else:
            formatted = str(value) if value is not None else "-"

        return (label, formatted)

    def calculate_image_width(
        self,
        original_width: int,
        page_width: float = 170,
        margin: float = 40
    ) -> float:
        """
        Calculate image width to fit in page.

        Args:
            original_width: Original image width in pixels
            page_width: Page width in mm
            margin: Total margin in mm

        Returns:
            Width in mm
        """
        available_width = page_width - margin

        # Assume 96 DPI for images
        img_width_mm = original_width * 25.4 / 96

        if img_width_mm > available_width:
            return available_width
        return img_width_mm

    # ======================================================================== #
    # UTILITY METHODS
    # ======================================================================== #

    def truncate_text(
        self,
        text: str,
        max_length: int = 30,
        suffix: str = "..."
    ) -> str:
        """
        Truncate text to maximum length.

        Args:
            text: Text to truncate
            max_length: Maximum length
            suffix: Suffix to add if truncated

        Returns:
            Truncated text
        """
        if not text:
            return ""

        if len(text) <= max_length:
            return text

        return text[:max_length - len(suffix)] + suffix

    def safe_divide(
        self,
        numerator: float,
        denominator: float,
        default: float = 0.0
    ) -> float:
        """
        Safely divide two numbers.

        Args:
            numerator: Numerator
            denominator: Denominator
            default: Default value if division fails

        Returns:
            Result of division or default
        """
        try:
            if denominator == 0:
                return default
            return numerator / denominator
        except (TypeError, ZeroDivisionError):
            return default
