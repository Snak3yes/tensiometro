"""
Inspection Report Builder (Refatorado)

Construtor de relatório de inspeção visual usando serviços especializados.
Responsável por orquestrar PDFGenerator, StatisticsCalculator e ReportLayoutManager.
"""

import os
import io
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Image

# Import ReportConfig from parent module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from report_generator import ReportConfig

# Import specialized services
from aoi_lib.reports.pdf_generator import PDFGenerator
from aoi_lib.reports.statistics_calculator import StatisticsCalculator
from aoi_lib.reports.report_layout_manager import ReportLayoutManager

log = logging.getLogger(__name__)


class InspectionReportBuilder:
    """
    Refatorado: Construtor de relatório de inspeção visual.

    Usa 3 serviços especializados:
    - PDFGenerator: operações PDF de baixo nível
    - StatisticsCalculator: cálculos estatísticos (percentuais OK/PARTIAL/BLOCKED)
    - ReportLayoutManager: formatação e layout

    NOTA: ChartGenerator não é necessário (relatórios de inspeção não possuem gráficos)

    Responsabilidade:
    - Orquestrar os serviços para gerar o relatório
    - Construir estrutura do relatório
    - Manter compatibilidade com interface original
    """

    def __init__(
        self,
        config: ReportConfig,
        pdf_generator: PDFGenerator = None,
        stats_calculator: StatisticsCalculator = None,
        layout_manager: ReportLayoutManager = None
    ):
        """
        Initialize inspection report builder with services.

        Args:
            config: Report configuration
            pdf_generator: PDF service (optional, created if None)
            stats_calculator: Statistics service (optional, created if None)
            layout_manager: Layout service (optional, created if None)
        """
        self.config = config

        # Initialize services (dependency injection)
        self.pdf = pdf_generator or PDFGenerator(config)
        self.stats = stats_calculator or StatisticsCalculator()
        self.layout = layout_manager or ReportLayoutManager(config)

    def build(
        self,
        inspection_result: Dict[str, Any],
        overlay_image_path: Optional[str] = None,
        stencil_code: Optional[str] = None,
        operator: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> str:
        """
        Gera relatório de inspeção visual.

        Args:
            inspection_result: Dicionário com resultado da inspeção
            overlay_image_path: Caminho da imagem de overlay (PNG)
            stencil_code: Código do stencil
            operator: Nome do operador
            output_path: Caminho de saída (opcional)

        Returns:
            Caminho do arquivo PDF gerado
        """
        # Determinar caminho de saída
        if output_path is None:
            output_dir = Path(self.config.output_dir) / "inspection"
            output_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            stencil_part = f"_{stencil_code}" if stencil_code else ""
            filename = f"{timestamp}{stencil_part}_inspection_report.pdf"
            output_path = str(output_dir / filename)

        # Construir conteúdo
        elements = []

        # Cabeçalho
        elements.extend(self._build_header(inspection_result, stencil_code, operator))

        # Linha horizontal
        self.pdf.add_horizontal_rule(elements, thickness=1)
        self.pdf.add_spacer(elements, height=8*mm)

        # Resumo
        elements.extend(self._build_summary_section(inspection_result))

        # Imagem de overlay
        if overlay_image_path and os.path.exists(overlay_image_path):
            elements.extend(self._build_overlay_section(overlay_image_path))

        # Tabela de defeitos
        elements.extend(self._build_defects_table(inspection_result))

        # Rodapé
        elements.extend(self._build_footer())

        # Gerar PDF
        return self.pdf.build_document(elements, output_path)

    # ======================================================================== #
    # SEÇÃO BUILDERS
    # ======================================================================== #

    def _build_header(
        self,
        result: Dict,
        stencil_code: Optional[str],
        operator: Optional[str]
    ) -> List:
        """Constrói cabeçalho do relatório usando PDFGenerator."""
        elements = []

        # Título e subtítulo
        self.pdf.add_header(elements, title=self.config.company_name, subtitle=self.config.company_subtitle, include_logo=False)
        self.pdf.add_spacer(elements, height=3*mm)
        self.pdf.add_title(elements, text="RELATÓRIO DE INSPEÇÃO VISUAL", level=1)
        self.pdf.add_spacer(elements, height=5*mm)

        # Status geral com destaque
        overall = result.get('overall_status', 'OK')
        status_colors_map = {
            'OK': self.config.get_success_color(),
            'WARNING': self.config.get_warning_color(),
            'NOK': self.config.get_danger_color()
        }
        status_color = status_colors_map.get(overall, colors.black)

        # Criar estilo customizado para status grande
        from reportlab.lib.styles import getSampleStyleSheet
        base_style = getSampleStyleSheet()['Title']
        status_style = ParagraphStyle(
            'StatusBig',
            parent=base_style,
            fontSize=24,
            textColor=status_color,
            alignment=TA_CENTER,
        )
        elements.append(Paragraph(f"RESULTADO: {overall}", status_style))
        self.pdf.add_spacer(elements, height=5*mm)

        # Informações da inspeção
        now = datetime.now()
        info_data = [
            ("Data:", now.strftime("%d/%m/%Y"), "Hora:", now.strftime("%H:%M:%S")),
            ("Stencil:", stencil_code or "-", "Operador:", operator or "-"),
            ("Taxa de Aprovação:", f"{result.get('approval_rate', 100):.1f}%", "", ""),
        ]

        self.pdf.add_info_table(elements, info_data, label_width=30*mm, value_width=50*mm)
        self.pdf.add_spacer(elements, height=5*mm)

        return elements

    def _build_summary_section(self, result: Dict) -> List:
        """Constrói seção de resumo usando PDFGenerator e StatisticsCalculator."""
        elements = []

        self.pdf.add_title(elements, text="RESUMO DA INSPEÇÃO", level=2)

        total = result.get('total_apertures', 0)
        ok = result.get('ok_count', 0)
        partial = result.get('partial_count', 0)
        blocked = result.get('blocked_count', 0)

        # Tabela de resumo
        summary_data = [
            ["Classificação", "Quantidade", "%"],
            ["✅ Aberturas OK", str(ok), f"{100*ok/total:.1f}%" if total else "0%"],
            ["⚠️ Parcialmente Obstruídas", str(partial), f"{100*partial/total:.1f}%" if total else "0%"],
            ["❌ Totalmente Obstruídas", str(blocked), f"{100*blocked/total:.1f}%" if total else "0%"],
            ["Total de Aberturas", str(total), "100%"],
        ]

        self.pdf.add_table(elements, summary_data, col_widths=[65*mm, 40*mm, 35*mm])
        self.pdf.add_spacer(elements, height=8*mm)

        return elements

    def _build_overlay_section(self, image_path: str) -> List:
        """Constrói seção com imagem do overlay usando PDFGenerator."""
        elements = []

        self.pdf.add_title(elements, text="IMAGEM DE INSPEÇÃO", level=2)

        try:
            # Calcular tamanho proporcional usando ReportLayoutManager
            from PIL import Image as PILImage
            with PILImage.open(image_path) as img:
                w, h = img.size

            # Escalar para caber na página (máx 160mm de largura)
            display_w, display_h = self.layout.calculate_image_width(
                original_width=w,
                page_width=160*mm,
                max_height=100*mm
            )

            img = Image(image_path, width=display_w, height=display_h)
            elements.append(img)

        except Exception as e:
            log.warning(f"Erro ao incluir imagem: {e}")
            self.pdf.add_paragraph(elements, "Imagem não disponível.")

        self.pdf.add_spacer(elements, height=5*mm)
        self.pdf.add_paragraph(elements, "<i>Verde = OK, Amarelo = Parcialmente obstruída, Vermelho = Totalmente obstruída</i>")
        self.pdf.add_spacer(elements, height=8*mm)

        return elements

    def _build_defects_table(self, result: Dict) -> List:
        """Constrói tabela de defeitos usando PDFGenerator."""
        elements = []

        defects = result.get('defects', [])
        if not defects:
            self.pdf.add_paragraph(elements, "✅ Nenhum defeito detectado.")
            return elements

        self.pdf.add_title(elements, text="DEFEITOS DETECTADOS", level=2)

        # Cabeçalho
        table_data = [["#", "ID", "Tipo", "Posição (mm)", "Área Livre", "Status"]]

        # Dados (máx 30 defeitos por página)
        for i, d in enumerate(defects[:30], 1):
            status = d.get('status', 'BLOCKED')
            if isinstance(status, str):
                status_val = status
            else:
                status_val = status.value if hasattr(status, 'value') else str(status)

            status_symbol = {'PARTIAL': '⚠️', 'BLOCKED': '❌'}.get(status_val, '❓')

            table_data.append([
                str(i),
                str(d.get('object_id', '-')),
                d.get('kind', '-'),
                f"({d.get('x_mm', 0):.1f}, {d.get('y_mm', 0):.1f})",
                f"{d.get('fill_percentage', d.get('fill_ratio', 0) * 100):.0f}%",
                f"{status_symbol} {status_val}"
            ])

        if len(defects) > 30:
            table_data.append(["...", f"+{len(defects)-30} mais", "", "", "", ""])

        # Criar tabela com cores por status
        col_widths = [10*mm, 20*mm, 25*mm, 40*mm, 30*mm, 35*mm]

        # Estilo base
        style = [
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]

        # Cores por status nas linhas de dados
        for i, d in enumerate(defects[:30]):
            row = i + 1  # +1 por causa do cabeçalho
            status = d.get('status', 'BLOCKED')
            status_val = status.value if hasattr(status, 'value') else str(status)

            if status_val == 'PARTIAL':
                style.append(('BACKGROUND', (0, row), (-1, row), colors.Color(1.0, 0.98, 0.9)))
            else:  # BLOCKED
                style.append(('BACKGROUND', (0, row), (-1, row), colors.Color(1.0, 0.9, 0.9)))

        self.pdf.add_table(elements, table_data, col_widths=col_widths, style_options=style)
        self.pdf.add_spacer(elements, height=5*mm)

        return elements

    def _build_footer(self) -> List:
        """Constrói rodapé do relatório usando PDFGenerator."""
        elements = []

        self.pdf.add_spacer(elements, height=10*mm)
        self.pdf.add_horizontal_rule(elements, thickness=0.5)

        footer_text = f"""
        Relatório de Inspeção Visual gerado automaticamente pelo {self.config.company_name}<br/>
        Data de geração: {datetime.now().strftime("%d/%m/%Y às %H:%M:%S")}
        """
        self.pdf.add_paragraph(elements, footer_text, style="Footer")

        return elements
