"""
history_builder.py
------------------
Construtor de relatório de histórico do stencil.

Este módulo contém a classe StencilHistoryReportBuilder responsável por gerar
relatórios PDF de histórico com gráfico de tendência, estatísticas e tabela de medições.
"""

from __future__ import annotations

import io
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# Reportlab para geração de PDF
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, HRFlowable
)

# Módulos locais
from aoi_lib.reports.config import ReportConfig, get_custom_styles
from aoi_lib.reports.chart_generator import create_trend_chart

log = logging.getLogger(__name__)


class StencilHistoryReportBuilder:
    """
    Construtor de relatório de histórico do stencil.

    Gera um PDF com:
    - Dados cadastrais do stencil
    - Gráfico de tendência de tensão
    - Histórico de todas as medições
    - Análise de degradação
    """

    def __init__(self, config: ReportConfig):
        self.config = config
        self.styles = get_custom_styles(config)

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

        # Criar documento
        doc = SimpleDocTemplate(
            output_path,
            pagesize=self.config.get_page_size(),
            rightMargin=15*mm, leftMargin=15*mm,
            topMargin=15*mm, bottomMargin=15*mm
        )

        # Construir conteúdo
        story = []

        # Cabeçalho
        story.extend(self._build_header(stencil))

        # Gráfico de tendência
        if self.config.include_charts and history:
            story.extend(self._build_trend_section(history))

        # Resumo estatístico
        story.extend(self._build_stats_section(history))

        # Histórico de medições
        story.extend(self._build_history_table(history))

        # Rodapé
        story.extend(self._build_footer())

        # Gerar PDF
        doc.build(story)
        log.info(f"Relatório de histórico gerado: {output_path}")

        return output_path

    def _build_header(self, stencil: Dict) -> List:
        """Constrói cabeçalho com dados do stencil."""
        elements = []

        elements.append(Paragraph(self.config.company_name, self.styles['Title']))
        elements.append(Paragraph("RELATÓRIO DE HISTÓRICO DO STENCIL", self.styles['Heading1']))
        elements.append(Spacer(1, 5*mm))

        # Dados do stencil
        info_data = [
            ["Código:", stencil.get('code', '-')],
            ["Descrição:", stencil.get('description', '-')],
            ["Receita Padrão:", stencil.get('recipe_name', '-')],
            ["Data de Cadastro:", stencil.get('created_at', '-')],
            ["Última Inspeção:", stencil.get('last_inspection', '-')],
            ["Total de Inspeções:", str(stencil.get('inspection_count', 0))],
            ["Status:", stencil.get('status', '-')],
        ]

        info_table = Table(info_data, colWidths=[40*mm, 120*mm])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.gray),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))

        elements.append(info_table)
        elements.append(Spacer(1, 8*mm))
        elements.append(HRFlowable(width="100%", thickness=1, color=self.config.get_primary_color()))
        elements.append(Spacer(1, 5*mm))

        return elements

    def _build_trend_section(self, history: List[Dict]) -> List:
        """Constrói seção com gráfico de tendência."""
        elements = []

        elements.append(Paragraph("TENDÊNCIA DE TENSÃO", self.styles['Heading2']))

        # Usar chart_generator para criar o gráfico
        chart_img = create_trend_chart(history, self.config)

        if chart_img:
            elements.append(chart_img)
        else:
            elements.append(Paragraph("Gráfico não disponível.", self.styles['Normal']))

        elements.append(Spacer(1, 5*mm))
        return elements

    def _build_stats_section(self, history: List[Dict]) -> List:
        """Constrói seção de estatísticas."""
        elements = []

        elements.append(Paragraph("ESTATÍSTICAS GERAIS", self.styles['Heading2']))

        if not history:
            elements.append(Paragraph("Nenhuma medição registrada.", self.styles['Normal']))
            return elements

        # Calcular estatísticas
        all_averages = [r.get('average_tension', 0) for r in history if r.get('average_tension')]

        total_measurements = len(history)
        total_ok = sum(r.get('ok_count', 0) for r in history)
        total_warn = sum(r.get('warning_count', 0) for r in history)
        total_nok = sum(r.get('nok_count', 0) for r in history)
        total_points = total_ok + total_warn + total_nok

        avg_of_avgs = sum(all_averages) / len(all_averages) if all_averages else 0

        stats_data = [
            ["Total de Inspeções:", str(total_measurements)],
            ["Total de Pontos Medidos:", str(total_points)],
            ["Tensão Média Geral:", f"{avg_of_avgs:.2f} N/cm"],
            ["Pontos OK:", f"{total_ok} ({100*total_ok/total_points:.0f}%)" if total_points else "0"],
            ["Pontos WARNING:", f"{total_warn} ({100*total_warn/total_points:.0f}%)" if total_points else "0"],
            ["Pontos NOK:", f"{total_nok} ({100*total_nok/total_points:.0f}%)" if total_points else "0"],
        ]

        stats_table = Table(stats_data, colWidths=[60*mm, 60*mm])
        stats_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))

        elements.append(stats_table)
        elements.append(Spacer(1, 8*mm))

        return elements

    def _build_history_table(self, history: List[Dict]) -> List:
        """Constrói tabela com histórico de medições."""
        elements = []

        elements.append(Paragraph("HISTÓRICO DE MEDIÇÕES", self.styles['Heading2']))

        if not history:
            elements.append(Paragraph("Nenhuma medição registrada.", self.styles['Normal']))
            return elements

        # Cabeçalho
        table_data = [["Data/Hora", "Média", "Mín", "Máx", "Resultado", "Operador"]]

        # Dados (últimas 50 entradas)
        for record in history[-50:]:
            ts = record.get('timestamp', '-')
            try:
                dt = datetime.fromisoformat(ts)
                ts_formatted = dt.strftime("%d/%m/%Y %H:%M")
            except:
                ts_formatted = ts

            result = record.get('result', 'OK').upper()
            result_symbol = {'OK': '✅', 'WARNING': '⚠️', 'NOK': '❌'}.get(result, '❓')

            table_data.append([
                ts_formatted,
                f"{record.get('average_tension', 0):.2f}",
                f"{record.get('min_tension', 0):.2f}",
                f"{record.get('max_tension', 0):.2f}",
                f"{result_symbol} {result}",
                record.get('operator', '-')[:15]  # Truncar nome
            ])

        # Criar tabela
        col_widths = [35*mm, 22*mm, 22*mm, 22*mm, 30*mm, 35*mm]
        table = Table(table_data, colWidths=col_widths)

        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (-1, 0), self.config.get_primary_color()),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 5*mm))

        return elements

    def _build_footer(self) -> List:
        """Constrói rodapé do relatório."""
        elements = []

        elements.append(Spacer(1, 10*mm))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))

        footer_text = f"""
        Relatório gerado automaticamente pelo {self.config.company_name}<br/>
        Data de geração: {datetime.now().strftime("%d/%m/%Y às %H:%M:%S")}
        """
        elements.append(Paragraph(footer_text, self.styles['Footer']))

        return elements
