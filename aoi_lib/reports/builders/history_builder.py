"""
Stencil History Report Builder (Refatorado)

Construtor de relatório de histórico do stencil usando serviços especializados.
Responsável por orquestrar PDFGenerator, ChartGenerator, StatisticsCalculator e ReportLayoutManager.
"""

import io
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import Image

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


class StencilHistoryReportBuilder:
    """
    Refatorado: Construtor de relatório de histórico do stencil.

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
        Initialize history report builder with services.

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
        stencil: Dict[str, Any],
        history: List[Dict[str, Any]],
        output_path: Optional[str] = None
    ) -> str:
        """
        Gera relatório de histórico do stencil.

        Args:
            stencil: Dados do stencil (dict ou Stencil)
            history: Lista de registros de tensão
            output_path: Caminho de saída (opcional)

        Returns:
            Caminho do arquivo PDF gerado
        """
        # Determinar caminho de saída
        if output_path is None:
            output_dir = Path(self.config.output_dir) / "stencil"
            output_dir.mkdir(parents=True, exist_ok=True)

            stencil_code = stencil.get('code', 'unknown')
            timestamp = datetime.now().strftime("%Y-%m-%d")
            filename = f"{stencil_code}_history_{timestamp}.pdf"
            output_path = str(output_dir / filename)

        # Construir conteúdo
        elements = []

        # Cabeçalho
        elements.extend(self._build_header(stencil))

        # Linha horizontal
        self.pdf.add_horizontal_rule(elements, thickness=1)
        self.pdf.add_spacer(elements, height=5*mm)

        # Gráfico de tendência
        if self.config.include_charts and history:
            elements.extend(self._build_trend_section(history))

        # Resumo estatístico
        elements.extend(self._build_stats_section(history))

        # Histórico de medições
        elements.extend(self._build_history_table(history))

        # Rodapé
        elements.extend(self._build_footer())

        # Gerar PDF
        return self.pdf.build_document(elements, output_path)

    # ======================================================================== #
    # SEÇÃO BUILDERS
    # ======================================================================== #

    def _build_header(self, stencil: Dict) -> List:
        """Constrói cabeçalho com dados do stencil usando PDFGenerator."""
        elements = []

        # Título
        self.pdf.add_header(elements, title=self.config.company_name, subtitle="", include_logo=False)
        self.pdf.add_spacer(elements, height=3*mm)
        self.pdf.add_title(elements, text="RELATÓRIO DE HISTÓRICO DO STENCIL", level=1)
        self.pdf.add_spacer(elements, height=5*mm)

        # Dados do stencil
        info_data = [
            ("Código:", stencil.get('code', '-')),
            ("Descrição:", stencil.get('description', '-')),
            ("Receita Padrão:", stencil.get('recipe_name', '-')),
            ("Data de Cadastro:", self.layout.format_date(stencil.get('created_at'), "%d/%m/%Y")),
            ("Última Inspeção:", self.layout.format_date(stencil.get('last_inspection'), "%d/%m/%Y")),
            ("Total de Inspeções:", str(stencil.get('inspection_count', 0))),
            ("Status:", stencil.get('status', '-')),
        ]

        self.pdf.add_info_table(elements, info_data, label_width=40*mm, value_width=120*mm)
        self.pdf.add_spacer(elements, height=8*mm)

        return elements

    def _build_trend_section(self, history: List[Dict]) -> List:
        """Constrói seção com gráfico de tendência usando ChartGenerator."""
        elements = []

        self.pdf.add_title(elements, text="TENDÊNCIA DE TENSÃO", level=2)
        self.pdf.add_spacer(elements, height=3*mm)

        try:
            # Extrair dados para gráfico
            averages = []
            for record in history[-20:]:  # Últimas 20 medições
                avg = record.get('average_tension', 0)
                if avg:
                    averages.append(avg)

            if len(averages) >= 2:
                # Criar line plot
                fig = self.chart.create_line_plot(
                    x_data=list(range(len(averages))),
                    y_data=averages,
                    title="Evolução da Tensão Média",
                    xlabel="Medição",
                    ylabel="Tensão Média (N/cm)",
                    figsize=(7, 3),
                    dpi=100,
                    show_trendline=True,
                    fill_area=True
                )

                # Salvar para BytesIO
                buf = self.chart.save_as_image(fig, format="png", dpi=100)
                self.chart.close(fig)

                # Criar Image
                img = Image(buf, width=160*mm, height=70*mm)
                elements.append(img)
            else:
                self.pdf.add_paragraph(elements, "Gráfico não disponível (insuficiente dados).")

        except Exception as e:
            log.warning(f"Erro ao criar gráfico de tendência: {e}")
            self.pdf.add_paragraph(elements, "Gráfico não disponível.")

        self.pdf.add_spacer(elements, height=5*mm)
        return elements

    def _build_stats_section(self, history: List[Dict]) -> List:
        """Constrói seção de estatísticas usando StatisticsCalculator."""
        elements = []

        self.pdf.add_title(elements, text="ESTATÍSTICAS GERAIS", level=2)
        self.pdf.add_spacer(elements, height=3*mm)

        if not history:
            self.pdf.add_paragraph(elements, "Nenhuma medição registrada.")
            return elements

        # Calcular estatísticas usando StatisticsCalculator
        all_averages = [r.get('average_tension', 0) for r in history if r.get('average_tension')]
        basic_stats = self.stats.calculate_basic_stats(all_averages, include_cv=False)

        # Calcular totais
        total_measurements = len(history)
        total_ok = sum(r.get('ok_count', 0) for r in history)
        total_warn = sum(r.get('warning_count', 0) for r in history)
        total_nok = sum(r.get('nok_count', 0) for r in history)
        total_points = total_ok + total_warn + total_nok

        # Tabela de estatísticas
        stats_data = [
            ["Total de Inspeções:", str(total_measurements)],
            ["Total de Pontos Medidos:", str(total_points)],
            ["Tensão Média Geral:", f"{self.layout.format_number(basic_stats['mean'])} N/cm"],
            ["Pontos OK:", f"{total_ok} ({self.layout.format_percentage(100*total_ok/total_points if total_points else 0)})"],
            ["Pontos WARNING:", f"{total_warn} ({self.layout.format_percentage(100*total_warn/total_points if total_points else 0)})"],
            ["Pontos NOK:", f"{total_nok} ({self.layout.format_percentage(100*total_nok/total_points if total_points else 0)})"],
        ]

        self.pdf.add_table(elements, stats_data, col_widths=[60*mm, 60*mm])
        self.pdf.add_spacer(elements, height=8*mm)

        return elements

    def _build_history_table(self, history: List[Dict]) -> List:
        """Constrói tabela com histórico de medições."""
        elements = []

        self.pdf.add_title(elements, text="HISTÓRICO DE MEDIÇÕES", level=2)
        self.pdf.add_spacer(elements, height=3*mm)

        if not history:
            self.pdf.add_paragraph(elements, "Nenhuma medição registrada.")
            return elements

        # Cabeçalho
        table_data = [["Data/Hora", "Média", "Mín", "Máx", "Resultado", "Operador"]]

        # Dados (últimas 50 entradas)
        for record in history[-50:]:
            ts = record.get('timestamp', '-')
            ts_formatted = self.layout.format_datetime(ts, "%d/%m/%Y %H:%M")

            result = record.get('result', 'OK').upper()
            result_symbol = {'OK': '✅', 'WARNING': '⚠️', 'NOK': '❌'}.get(result, '❓')

            table_data.append([
                ts_formatted,
                self.layout.format_number(record.get('average_tension', 0)),
                self.layout.format_number(record.get('min_tension', 0)),
                self.layout.format_number(record.get('max_tension', 0)),
                f"{result_symbol} {result}",
                self.layout.truncate_text(record.get('operator', '-'), 15)
            ])

        # Criar tabela
        col_widths = [35*mm, 22*mm, 22*mm, 22*mm, 30*mm, 35*mm]
        self.pdf.add_table(elements, table_data, col_widths=col_widths)
        self.pdf.add_spacer(elements, height=5*mm)

        return elements

    def _build_footer(self) -> List:
        """Constrói rodapé do relatório usando PDFGenerator."""
        elements = []

        self.pdf.add_spacer(elements, height=10*mm)
        self.pdf.add_horizontal_rule(elements, thickness=0.5)

        footer_text = f"""
        Relatório gerado automaticamente pelo {self.config.company_name}<br/>
        Data de geração: {datetime.now().strftime("%d/%m/%Y às %H:%M:%S")}
        """
        self.pdf.add_paragraph(elements, footer_text, style="Footer")

        return elements
