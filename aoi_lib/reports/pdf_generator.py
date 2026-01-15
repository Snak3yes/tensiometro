"""
PDF Generator Service

Low-level PDF generation service using ReportLab.
Responsible for creating documents, adding elements (headers, footers, tables, images),
and managing PDF structure.
"""

import os
import logging
from typing import Dict, List, Optional, Any, Tuple
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, HRFlowable
)
from reportlab.lib.enums import TA_CENTER

# Import ReportConfig from parent module
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from report_generator import ReportConfig

log = logging.getLogger(__name__)


class PDFGenerator:
    """
    Low-level PDF generation service using ReportLab.

    Responsibilities:
    - Create PDF documents
    - Add headers, footers, pages
    - Add paragraphs, tables, images
    - Manage document structure and styles

    This service isolates all ReportLab-specific code, making it easier
    to test and maintain report builders.
    """

    def __init__(self, config: ReportConfig):
        """
        Initialize PDF generator with report configuration.

        Args:
            config: Report configuration with styles, colors, logo, etc.
        """
        self.config = config
        self.styles = self._load_styles()
        self.page_size = self._get_page_size()

    def _load_styles(self) -> Dict[str, ParagraphStyle]:
        """
        Load custom styles based on report configuration.

        Returns:
            Dictionary of custom ReportLab ParagraphStyle objects
        """
        styles = getSampleStyleSheet()

        custom = {
            'Title': ParagraphStyle(
                'CustomTitle',
                parent=styles['Title'],
                fontSize=18,
                textColor=colors.Color(*[c/255 for c in self.config.primary_color]),
                spaceAfter=12,
                alignment=TA_CENTER,
            ),
            'Subtitle': ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Normal'],
                fontSize=12,
                textColor=colors.gray,
                spaceAfter=20,
                alignment=TA_CENTER,
            ),
            'Heading1': ParagraphStyle(
                'CustomHeading1',
                parent=styles['Heading1'],
                fontSize=14,
                textColor=colors.Color(*[c/255 for c in self.config.primary_color]),
                spaceBefore=16,
                spaceAfter=8,
            ),
            'Heading2': ParagraphStyle(
                'CustomHeading2',
                parent=styles['Heading2'],
                fontSize=12,
                textColor=colors.Color(*[c/255 for c in self.config.primary_color]),
                spaceBefore=12,
                spaceAfter=6,
            ),
            'Normal': ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=10,
                leading=14,
            ),
            'InfoText': ParagraphStyle(
                'InfoText',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.gray,
            ),
            'Success': ParagraphStyle(
                'SuccessText',
                parent=styles['Normal'],
                fontSize=12,
                textColor=colors.Color(*[c/255 for c in self.config.success_color]),
            ),
            'Warning': ParagraphStyle(
                'WarningText',
                parent=styles['Normal'],
                fontSize=12,
                textColor=colors.Color(*[c/255 for c in self.config.warning_color]),
            ),
            'Danger': ParagraphStyle(
                'DangerText',
                parent=styles['Normal'],
                fontSize=12,
                textColor=colors.Color(*[c/255 for c in self.config.danger_color]),
            ),
        }

        # Add/override custom styles in stylesheet
        for name, style in custom.items():
            if name in styles:
                # Override existing style
                styles[name].__dict__.update(style.__dict__)
            else:
                # Add new style
                styles.add(style, name)
        return styles

    def _get_page_size(self):
        """Get page size from configuration."""
        return A4 if self.config.page_size == "A4" else letter

    # ======================================================================== #
    # DOCUMENT CREATION
    # ======================================================================== #

    def create_document(self, output_path: str) -> SimpleDocTemplate:
        """
        Create a new PDF document.

        Args:
            output_path: Path where PDF will be saved

        Returns:
            SimpleDocTemplate ready to receive elements
        """
        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        doc = SimpleDocTemplate(
            output_path,
            pagesize=self.page_size,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=15*mm,
        )

        return doc

    # ======================================================================== #
    # ELEMENT ADDITION
    # ======================================================================== #

    def add_header(
        self,
        elements: List,
        title: str,
        subtitle: str = "",
        include_logo: bool = True,
    ) -> None:
        """
        Add header section to elements list.

        Args:
            elements: List to append header elements to
            title: Main title
            subtitle: Optional subtitle
            include_logo: Whether to include logo if available
        """
        # Logo and title
        if include_logo and self.config.logo_path and os.path.exists(self.config.logo_path):
            try:
                logo = Image(self.config.logo_path, width=30*mm, height=30*mm)
                elements.append(logo)
            except Exception as e:
                log.warning(f"Erro ao carregar logo: {e}")
                elements.append(Paragraph(self.config.company_name, self.styles['Title']))
        else:
            elements.append(Paragraph(self.config.company_name, self.styles['Title']))

        elements.append(Paragraph(self.config.company_name, self.styles['Title']))
        if subtitle:
            elements.append(Paragraph(subtitle, self.styles['Subtitle']))

        elements.append(Spacer(1, 5*mm))

    def add_title(
        self,
        elements: List,
        text: str,
        level: int = 1,
    ) -> None:
        """
        Add title/heading to elements list.

        Args:
            elements: List to append title to
            text: Title text
            level: Heading level (1=Heading1, 2=Heading2)
        """
        style_name = f'Heading{level}'
        if style_name in self.styles:
            elements.append(Paragraph(text, self.styles[style_name]))
        else:
            elements.append(Paragraph(text, self.styles['Heading1']))

    def add_paragraph(
        self,
        elements: List,
        text: str,
        style: str = "Normal",
    ) -> None:
        """
        Add paragraph to elements list.

        Args:
            elements: List to append paragraph to
            text: Paragraph text
            style: Style name from self.styles
        """
        if style in self.styles:
            elements.append(Paragraph(text, self.styles[style]))
        else:
            elements.append(Paragraph(text, self.styles['Normal']))

    def add_spacer(
        self,
        elements: List,
        height: float = 6*mm,
    ) -> None:
        """
        Add vertical spacer to elements list.

        Args:
            elements: List to append spacer to
            height: Height of spacer
        """
        elements.append(Spacer(1, height))

    def add_pagebreak(
        self,
        elements: List,
    ) -> None:
        """
        Add page break to elements list.

        Args:
            elements: List to append pagebreak to
        """
        elements.append(PageBreak())

    def add_horizontal_rule(
        self,
        elements: List,
        thickness: float = 1,
        color: Tuple[int, int, int] = None,
    ) -> None:
        """
        Add horizontal line to elements list.

        Args:
            elements: List to append HR to
            thickness: Line thickness
            color: RGB color tuple
        """
        if color is None:
            color = self.config.primary_color

        hr = HRFlowable(
            width="100%",
            thickness=thickness,
            color=colors.Color(*[c/255 for c in color])
        )
        elements.append(hr)

    def add_table(
        self,
        elements: List,
        data: List[List[Any]],
        headers: List[str] = None,
        col_widths: List[float] = None,
        style_options: List[Tuple] = None,
    ) -> None:
        """
        Add table to elements list.

        Args:
            elements: List to append table to
            data: Table data (list of rows, each row is list of cells)
            headers: Optional header row
            col_widths: Optional column widths
            style_options: Optional TableStyle commands
        """
        # Add headers if provided
        if headers:
            table_data = [headers] + data
        else:
            table_data = data

        # Create table
        table = Table(table_data, colWidths=col_widths)

        # Apply default style
        default_style = [
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]

        # Add header row style
        if headers:
            header_style = [
                ('BACKGROUND', (0, 0), (-1, 0), colors.Color(*[c/255 for c in self.config.primary_color])),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ]
            default_style.extend(header_style)

        # Apply custom style if provided
        if style_options:
            default_style.extend(style_options)

        table.setStyle(TableStyle(default_style))
        elements.append(table)

    def add_info_table(
        self,
        elements: List,
        info_data: List[Tuple[str, Any]],
        label_width: float = 40*mm,
        value_width: float = 120*mm,
    ) -> None:
        """
        Add information table (label-value pairs).

        Args:
            elements: List to append table to
            info_data: List of (label, value) tuples
            label_width: Width of label column
            value_width: Width of value column
        """
        table_data = [[label, value] for label, value in info_data]
        self.add_table(
            elements,
            table_data,
            col_widths=[label_width, value_width],
            style_options=[
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.gray),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ]
        )

    def add_image(
        self,
        elements: List,
        image_path: str,
        width: float = None,
        height: float = None,
        max_width: float = 170*mm,
    ) -> None:
        """
        Add image to elements list.

        Args:
            elements: List to append image to
            image_path: Path to image file
            width: Fixed width (None = auto)
            height: Fixed height (None = auto)
            max_width: Maximum width (scale down if needed)
        """
        if not os.path.exists(image_path):
            log.warning(f"Imagem não encontrada: {image_path}")
            return

        try:
            img = Image(image_path)

            # Scale down if too wide
            if max_width and img.drawWidth > max_width:
                ratio = max_width / img.drawWidth
                img.drawWidth = max_width
                img.drawHeight = img.drawHeight * ratio

            elements.append(img)
        except Exception as e:
            log.error(f"Erro ao adicionar imagem {image_path}: {e}")

    # ======================================================================== #
    # DOCUMENT BUILDING
    # ======================================================================== #

    def build_document(
        self,
        elements: List,
        output_path: str,
    ) -> str:
        """
        Build PDF document from elements.

        Args:
            elements: List of flowable elements
            output_path: Path to save PDF

        Returns:
            Path to generated PDF file
        """
        doc = self.create_document(output_path)

        try:
            doc.build(elements)
            log.info(f"PDF gerado com sucesso: {output_path}")
            return output_path
        except Exception as e:
            log.error(f"Erro ao gerar PDF: {e}")
            raise

    # ======================================================================== #
    # UTILITY METHODS
    # ======================================================================== #

    def get_style(self, style_name: str) -> ParagraphStyle:
        """
        Get a style by name.

        Args:
            style_name: Name of style (Title, Subtitle, Heading1, etc.)

        Returns:
            ParagraphStyle object

        Raises:
            KeyError: If style name not found
        """
        if style_name not in self.styles:
            raise KeyError(f"Style '{style_name}' not found")
        return self.styles[style_name]

    def get_color(
        self,
        color_name: str,
    ) -> colors.Color:
        """
        Get theme color by name.

        Args:
            color_name: 'primary', 'success', 'warning', 'danger'

        Returns:
            ReportLab Color object
        """
        color_map = {
            'primary': self.config.primary_color,
            'success': self.config.success_color,
            'warning': self.config.warning_color,
            'danger': self.config.danger_color,
        }

        if color_name not in color_map:
            raise KeyError(f"Color '{color_name}' not found. Available: {list(color_map.keys())}")

        rgb = color_map[color_name]
        return colors.Color(*[c/255 for c in rgb])

    def get_page_width(self) -> float:
        """Get page width in mm."""
        width, _ = self.page_size
        return width

    def get_page_height(self) -> float:
        """Get page height in mm."""
        _, height = self.page_size
        return height

    def calculate_available_width(
        self,
        margin: float = 40*mm,  # Total margin (left + right)
    ) -> float:
        """
        Calculate available content width.

        Args:
            margin: Total margin to subtract

        Returns:
            Available width in mm
        """
        return self.get_page_width() - margin

    def calculate_image_width(
        self,
        original_width: int,
        max_width: float = None,
    ) -> float:
        """
        Calculate image width to fit in page.

        Args:
            original_width: Original image width in pixels
            max_width: Maximum width in mm (None = use page default)

        Returns:
            Width in mm
        """
        if max_width is None:
            max_width = self.calculate_available_width()

        # Simple scaling: assume 96 DPI for images
        # This can be improved to read actual DPI from image
        img_width_mm = original_width * 25.4 / 96

        if img_width_mm > max_width:
            return max_width
        return img_width_mm

    def format_datetime(
        self,
        dt,
        format_str: str = "%d/%m/%Y %H:%M",
    ) -> str:
        """
        Format datetime for display.

        Args:
            dt: Datetime object
            format_str: Format string

        Returns:
            Formatted datetime string
        """
        if dt is None:
            return "-"
        return dt.strftime(format_str)

    def format_number(
        self,
        value: float,
        decimals: int = 2,
    ) -> str:
        """
        Format number for display.

        Args:
            value: Number to format
            decimals: Decimal places

        Returns:
            Formatted number string
        """
        if value is None:
            return "-"
        return f"{value:.{decimals}f}"

    def format_percentage(
        self,
        value: float,
        decimals: int = 1,
    ) -> str:
        """
        Format number as percentage.

        Args:
            value: Number (0-100)
            decimals: Decimal places

        Returns:
            Formatted percentage string
        """
        if value is None:
            return "-"
        return f"{value:.{decimals}f}%"
