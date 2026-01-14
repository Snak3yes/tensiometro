"""
reports/config.py
-----------------
Configuração e estilos para geração de relatórios PDF.
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, Tuple

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER


@dataclass
class ReportConfig:
    """
    Configuração personalizável para relatórios.

    Estas configurações são salvas no arquivo de config do usuário,
    permitindo personalização para diferentes clientes.
    """
    # Identidade visual
    company_name: str = "SeuStencil"
    company_subtitle: str = "Sistema de Inspeção de Stencils"
    logo_path: Optional[str] = None  # Caminho para imagem do logo

    # Diretório de saída
    output_dir: str = "reports"

    # Opções de geração
    include_charts: bool = True
    include_details_table: bool = True
    auto_generate_after_measurement: bool = False

    # Formato
    page_size: str = "A4"  # "A4" ou "letter"
    language: str = "pt-BR"

    # Cores do tema
    primary_color: Tuple[int, int, int] = (41, 128, 185)    # Azul
    success_color: Tuple[int, int, int] = (46, 204, 113)    # Verde
    warning_color: Tuple[int, int, int] = (241, 196, 15)    # Amarelo
    danger_color: Tuple[int, int, int] = (231, 76, 60)      # Vermelho

    def to_dict(self) -> Dict[str, Any]:
        """Serializa para dicionário."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReportConfig':
        """Deserializa de dicionário."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def get_page_size(self):
        """Retorna tamanho da página."""
        return A4 if self.page_size == "A4" else letter

    def get_primary_color(self):
        """Retorna cor primária como Color do reportlab."""
        r, g, b = self.primary_color
        return colors.Color(r/255, g/255, b/255)

    def get_success_color(self):
        r, g, b = self.success_color
        return colors.Color(r/255, g/255, b/255)

    def get_warning_color(self):
        r, g, b = self.warning_color
        return colors.Color(r/255, g/255, b/255)

    def get_danger_color(self):
        r, g, b = self.danger_color
        return colors.Color(r/255, g/255, b/255)


def get_custom_styles(config: ReportConfig) -> Dict[str, ParagraphStyle]:
    """Retorna estilos customizados para o documento."""
    styles = getSampleStyleSheet()

    custom = {
        'Title': ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=18,
            textColor=colors.Color(*[c/255 for c in config.primary_color]),
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
            textColor=colors.Color(*[c/255 for c in config.primary_color]),
            spaceBefore=16,
            spaceAfter=8,
        ),
        'Heading2': ParagraphStyle(
            'CustomHeading2',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.black,
            spaceBefore=12,
            spaceAfter=6,
        ),
        'Normal': ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6,
        ),
        'Small': ParagraphStyle(
            'CustomSmall',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.gray,
        ),
        'Footer': ParagraphStyle(
            'CustomFooter',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.gray,
            alignment=TA_CENTER,
        ),
        'OK': ParagraphStyle(
            'StatusOK',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.Color(*[c/255 for c in config.success_color]),
            alignment=TA_CENTER,
        ),
        'Warning': ParagraphStyle(
            'StatusWarning',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.Color(*[c/255 for c in config.warning_color]),
            alignment=TA_CENTER,
        ),
        'NOK': ParagraphStyle(
            'StatusNOK',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.Color(*[c/255 for c in config.danger_color]),
            alignment=TA_CENTER,
        ),
    }

    return custom
