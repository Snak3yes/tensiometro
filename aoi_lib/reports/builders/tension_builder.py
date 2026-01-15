"""
Tension Report Builder (Refatorado)

Construtor de relatório de medição de tensão usando serviços especializados.
Responsável por orquestrar PDFGenerator, ChartGenerator, StatisticsCalculator e ReportLayoutManager.
"""

import os
import io
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image, HRFlowable
)

# Import ReportConfig from parent module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from report_generator import ReportConfig

# Import specialized services
from aoi_lib.reports.pdf_generator import PDFGenerator
from aoi_lib.reports.chart_generator import ChartGenerator
from aoi_lib.reports.statistics_calculator import StatisticsCalculator
from aoi_lib.reports.report_layout_manager import ReportLayoutManager

log = logging.getLogger(__name__)


class TensionReportBuilder:
    """
    Refatorado: Construtor de relatório de medição de tensão.

    Usa 4 serviços especializados:
    - PDFGenerator: operações PDF de baixo nível
    - ChartGenerator: geração de gráficos
    - StatisticsCalculator: cálculos estatísticos
    - ReportLayoutManager: formatação e layout

    Responsabilidade:
    - Orquestrar os serviços para gerar o relatório
    - Construir estrutura do relatório
    - Manter compatibilidade com interface original
    """

    def __init__(
        self,
        config: ReportConfig,
        pdf_generator: PDFGenerator = None,
        chart_generator: ChartGenerator = None,
        stats_calculator: StatisticsCalculator = None,
        layout_manager: ReportLayoutManager = None
    ):
        """
        Initialize tension report builder with services.

        Args:
            config: Report configuration
            pdf_generator: PDF service (optional, created if None)
            chart_generator: Chart service (optional, created if None)
            stats_calculator: Statistics service (optional, created if None)
            layout_manager: Layout service (optional, created if None)
        """
        self.config = config

        # Initialize services (dependency injection)
        self.pdf = pdf_generator or PDFGenerator(config)
        self.chart = chart_generator or ChartGenerator(config)
        self.stats = stats_calculator or StatisticsCalculator()
        self.layout = layout_manager or ReportLayoutManager(config)

    def build(
        self,
        tension_data: Dict[str, Any],
        stencil_code: Optional[str] = None,
        stencil_description: Optional[str] = None,
        recipe_name: Optional[str] = None,
        operator: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> str:
        """
        Gera relatório de tensão em PDF.

        Args:
            tension_data: Dicionário com dados da medição
            stencil_code: Código do stencil
            stencil_description: Descrição do stencil
            recipe_name: Nome da receita utilizada
            operator: Nome do operador
            output_path: Caminho de saída (opcional)

        Returns:
            Caminho do arquivo PDF gerado
        """
        # Determinar caminho de saída
        if output_path is None:
            output_dir = Path(self.config.output_dir) / "tension"
            output_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            stencil_part = f"_{stencil_code}" if stencil_code else ""
            filename = f"{timestamp}{stencil_part}_tension_report.pdf"
            output_path = str(output_dir / filename)

        # Construir conteúdo
        elements = []

        # Cabeçalho
        elements.extend(self._build_header(stencil_code, stencil_description, recipe_name, operator))

        # Linha horizontal
        self.pdf.add_horizontal_rule(elements, thickness=1)

        # Resumo e mapa de tensão
        elements.extend(self._build_summary_section(tension_data))

        # Critérios de aceitação
        elements.extend(self._build_criteria_section(tension_data))

        # Tabela detalhada
        if self.config.include_details_table:
            elements.extend(self._build_details_table(tension_data))

        # Rodapé
        elements.extend(self._build_footer())

        # Gerar PDF
        return self.pdf.build_document(elements, output_path)

    # ======================================================================== #
    # SEÇÃO BUILDERS
    # ======================================================================== #

    def _build_header(
        self,
        stencil_code: Optional[str],
        stencil_description: Optional[str],
        recipe_name: Optional[str],
        operator: Optional[str]
    ) -> List:
        """Constrói cabeçalho do relatório usando PDFGenerator."""
        elements = []

        # Título e subtítulo
        self.pdf.add_header(elements, title=self.config.company_name, subtitle=self.config.company_subtitle, include_logo=False)
        self.pdf.add_spacer(elements, height=3*mm)
        self.pdf.add_title(elements, text="RELATÓRIO DE MEDIÇÃO DE TENSÃO", level=1)
        self.pdf.add_spacer(elements, height=5*mm)

        # Informações da medição
        now = datetime.now()
        info_data = [
            ("Data:", now.strftime("%d/%m/%Y"), "Hora:", now.strftime("%H:%M:%S")),
            ("Stencil:", stencil_code or "-", "Descrição:", stencil_description or "-"),
            ("Receita:", recipe_name or "-", "Operador:", operator or "-"),
        ]

        # Format info rows using layout manager
        formatted_info = []
        for label1, value1, label2, value2 in info_data:
            formatted_info.append([label1, value1, label2, value2])

        self.pdf.add_table(
            elements,
            formatted_info,
            col_widths=[25*mm, 55*mm, 25*mm, 55*mm],
            style_options=[
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.gray),
                ('TEXTCOLOR', (2, 0), (2, -1), colors.gray),
            ]
        )

        self.pdf.add_spacer(elements, height=5*mm)
        return elements

    def _build_summary_section(self, tension_data: Dict) -> List:
        """Constrói seção de resumo com mapa de tensão."""
        elements = []

        measurements = tension_data.get('measurements', [])
        if not measurements:
            self.pdf.add_paragraph(elements, "Nenhuma medição disponível.")
            return elements

        # Calcular estatísticas usando StatisticsCalculator
        tensions = [m.get('tension', 0) for m in measurements]
        basic_stats = self.stats.calculate_basic_stats(tensions, include_cv=False)

        # Calcular percentuais de classificação
        classifications = [m.get('status', 'OK') for m in measurements]
        class_pcts = self.stats.calculate_percentages(classifications)

        # Título
        self.pdf.add_title(elements, text="RESUMO DA MEDIÇÃO", level=2)
        self.pdf.add_spacer(elements, height=3*mm)

        # Tabela de resumo
        summary_data = [
            ["Estatísticas", ""],
            ["Média:", f"{basic_stats['mean']:.2f} N/cm"],
            ["Mínimo:", f"{basic_stats['min']:.2f} N/cm"],
            ["Máximo:", f"{basic_stats['max']:.2f} N/cm"],
            ["Total de Pontos:", str(basic_stats['count'])],
            ["", ""],
            ["Classificação", ""],
            ["✅ OK:", f"{class_pcts['ok_count']} ({self.layout.format_percentage(class_pcts['ok_pct'])})"],
            ["⚠️ WARNING:", f"{class_pcts['warning_count']} ({self.layout.format_percentage(class_pcts['warning_pct'])})"],
            ["❌ NOK:", f"{class_pcts['nok_count']} ({self.layout.format_percentage(class_pcts['nok_pct'])})"],
        ]

        self.pdf.add_table(elements, summary_data, col_widths=[50*mm, 40*mm])
        self.pdf.add_spacer(elements, height=3*mm)

        # Gráfico de mapa de tensão
        if self.config.include_charts:
            chart_img = self._create_tension_map_chart(tension_data)
            if chart_img:
                elements.append(chart_img)

        self.pdf.add_spacer(elements, height=8*mm)
        return elements

    def _create_tension_map_chart(self, tension_data: Dict) -> Optional[Image]:
        """Cria gráfico de mapa de tensão usando ChartGenerator."""
        measurements = tension_data.get('measurements', [])
        if not measurements:
            return None

        try:
            # Extrair dados
            x_data = [m.get('x', 0) for m in measurements]
            y_data = [m.get('y', 0) for m in measurements]
            tensions = [m.get('tension', 0) for m in measurements]
            statuses = [m.get('status', 'OK') for m in measurements]

            # Criar scatter plot
            fig = self.chart.create_scatter_plot(
                x_data=x_data,
                y_data=y_data,
                color_data=statuses,
                labels=[f"{t:.1f}" for t in tensions],
                title="Mapa de Tensão",
                xlabel="X (mm)",
                ylabel="Y (mm)",
                figsize=(4, 3),
                dpi=100,
                show_values=True,
                show_legend=True
            )

            # Salvar para BytesIO
            buf = self.chart.save_as_image(fig, format="png", dpi=100)
            self.chart.close(fig)

            # Criar Image do reportlab
            img = Image(buf, width=85*mm, height=65*mm)
            return img

        except Exception as e:
            log.warning(f"Erro ao criar gráfico de tensão: {e}")
            return None

    def _build_criteria_section(self, tension_data: Dict) -> List:
        """Constrói seção de critérios de aceitação."""
        elements = []

        self.pdf.add_title(elements, text="CRITÉRIOS DE ACEITAÇÃO", level=2)
        self.pdf.add_spacer(elements, height=3*mm)

        # Obter critérios
        criteria = tension_data.get('acceptance_criteria', {})
        ok_min = criteria.get('ok_min', 26.0)
        ok_max = criteria.get('ok_max', 32.0)
        warn_low = criteria.get('warning_low', 24.0)
        warn_high = criteria.get('warning_high', 35.0)

        criteria_text = f"""
        <b>✅ OK:</b> {ok_min:.1f} - {ok_max:.1f} N/cm<br/>
        <b>⚠️ WARNING:</b> {warn_low:.1f} - {ok_min:.1f} N/cm ou {ok_max:.1f} - {warn_high:.1f} N/cm<br/>
        <b>❌ NOK:</b> &lt; {warn_low:.1f} N/cm ou &gt; {warn_high:.1f} N/cm
        """

        self.pdf.add_paragraph(elements, criteria_text)
        self.pdf.add_spacer(elements, height=5*mm)

        return elements

    def _build_details_table(self, tension_data: Dict) -> List:
        """Constrói tabela detalhada de pontos."""
        elements = []

        measurements = tension_data.get('measurements', [])
        if not measurements:
            return elements

        self.pdf.add_title(elements, text="DETALHES POR PONTO", level=2)
        self.pdf.add_spacer(elements, height=3*mm)

        # Cabeçalho da tabela
        table_data = [["#", "X (mm)", "Y (mm)", "Tensão (N/cm)", "Status"]]

        # Dados
        for i, m in enumerate(measurements, 1):
            status = m.get('status', 'OK').upper()
            status_symbol = {'OK': '✅', 'WARNING': '⚠️', 'WARN': '⚠️', 'NOK': '❌'}.get(status, '❓')

            table_data.append([
                str(i),
                self.layout.format_number(m.get('x', 0), decimals=1),
                self.layout.format_number(m.get('y', 0), decimals=1),
                self.layout.format_number(m.get('tension', 0), decimals=2),
                f"{status_symbol} {status}"
            ])

        # Criar tabela com estilo base
        col_widths = [12*mm, 30*mm, 30*mm, 40*mm, 35*mm]

        # Estilo base
        style = [
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]

        # Cores por status nas linhas de dados
        for i, m in enumerate(measurements):
            row = i + 1  # +1 por causa do cabeçalho
            status = m.get('status', 'OK').upper()
            if status == 'OK':
                style.append(('BACKGROUND', (0, row), (-1, row), colors.Color(0.9, 1.0, 0.9)))
            elif status in ('WARNING', 'WARN'):
                style.append(('BACKGROUND', (0, row), (-1, row), colors.Color(1.0, 0.98, 0.9)))
            elif status == 'NOK':
                style.append(('BACKGROUND', (0, row), (-1, row), colors.Color(1.0, 0.9, 0.9)))

        self.pdf.add_table(elements, table_data, col_widths=col_widths, style_options=style)
        self.pdf.add_spacer(elements, height=5*mm)

        return elements

    def _build_footer(self) -> List:
        """Constrói rodapé do relatório."""
        elements = []

        self.pdf.add_spacer(elements, height=10*mm)
        self.pdf.add_horizontal_rule(elements, thickness=0.5)

        footer_text = f"""
        Relatório gerado automaticamente pelo {self.config.company_name}<br/>
        Data de geração: {datetime.now().strftime("%d/%m/%Y às %H:%M:%S")}
        """
        self.pdf.add_paragraph(elements, footer_text, style="Footer")

        return elements
