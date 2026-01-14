"""
tension_builder.py
------------------
Construtor de relatório de medição de tensão.

Este módulo contém a classe TensionReportBuilder responsável por gerar
relatórios PDF de medição de tensão com mapa visual, estatísticas e tabela detalhada.
"""

from __future__ import annotations

import os
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
from aoi_lib.reports.chart_generator import create_tension_map_chart

log = logging.getLogger(__name__)


class TensionReportBuilder:
    """
    Construtor de relatório de medição de tensão.

    Gera um PDF com:
    - Cabeçalho com logo e informações
    - Mapa visual dos pontos de medição
    - Resumo estatístico
    - Tabela detalhada de pontos
    """

    def __init__(self, config: ReportConfig):
        self.config = config
        self.styles = get_custom_styles(config)

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
        story.extend(self._build_header(stencil_code, stencil_description, recipe_name, operator))

        # Linha horizontal
        story.append(HRFlowable(width="100%", thickness=1, color=self.config.get_primary_color()))
        story.append(Spacer(1, 10*mm))

        # Resumo e mapa de tensão lado a lado
        story.extend(self._build_summary_section(tension_data))

        # Critérios de aceitação
        story.extend(self._build_criteria_section(tension_data))

        # Tabela detalhada
        if self.config.include_details_table:
            story.extend(self._build_details_table(tension_data))

        # Rodapé
        story.extend(self._build_footer())

        # Gerar PDF
        doc.build(story)
        log.info(f"Relatório de tensão gerado: {output_path}")

        return output_path

    def _build_header(
        self,
        stencil_code: Optional[str],
        stencil_description: Optional[str],
        recipe_name: Optional[str],
        operator: Optional[str]
    ) -> List:
        """Constrói cabeçalho do relatório."""
        elements = []

        # Logo e título
        header_data = []

        # Coluna do logo
        if self.config.logo_path and os.path.exists(self.config.logo_path):
            try:
                logo = Image(self.config.logo_path, width=30*mm, height=30*mm)
                header_data.append([logo])
            except Exception as e:
                log.warning(f"Erro ao carregar logo: {e}")
                header_data.append([Paragraph(self.config.company_name, self.styles['Title'])])
        else:
            # Placeholder de texto se não houver logo
            header_data.append([Paragraph(self.config.company_name, self.styles['Title'])])

        # Título principal
        elements.append(Paragraph(self.config.company_name, self.styles['Title']))
        elements.append(Paragraph(self.config.company_subtitle, self.styles['Subtitle']))
        elements.append(Paragraph("RELATÓRIO DE MEDIÇÃO DE TENSÃO", self.styles['Heading1']))
        elements.append(Spacer(1, 5*mm))

        # Informações da medição
        now = datetime.now()
        info_data = [
            ["Data:", now.strftime("%d/%m/%Y"), "Hora:", now.strftime("%H:%M:%S")],
            ["Stencil:", stencil_code or "-", "Descrição:", stencil_description or "-"],
            ["Receita:", recipe_name or "-", "Operador:", operator or "-"],
        ]

        info_table = Table(info_data, colWidths=[25*mm, 55*mm, 25*mm, 55*mm])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.gray),
            ('TEXTCOLOR', (2, 0), (2, -1), colors.gray),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))

        elements.append(info_table)
        elements.append(Spacer(1, 5*mm))

        return elements

    def _build_summary_section(self, tension_data: Dict) -> List:
        """Constrói seção de resumo com mapa de tensão."""
        elements = []

        measurements = tension_data.get('measurements', [])
        if not measurements:
            elements.append(Paragraph("Nenhuma medição disponível.", self.styles['Normal']))
            return elements

        # Calcular estatísticas
        tensions = [m.get('tension', 0) for m in measurements]
        avg_tension = sum(tensions) / len(tensions) if tensions else 0
        min_tension = min(tensions) if tensions else 0
        max_tension = max(tensions) if tensions else 0

        # Contar por status
        ok_count = sum(1 for m in measurements if m.get('status', '').upper() == 'OK')
        warn_count = sum(1 for m in measurements if m.get('status', '').upper() in ('WARNING', 'WARN'))
        nok_count = sum(1 for m in measurements if m.get('status', '').upper() == 'NOK')
        total = len(measurements)

        # Seção de títulos
        elements.append(Paragraph("RESUMO DA MEDIÇÃO", self.styles['Heading2']))

        # Tabela de resumo
        summary_data = [
            ["Estatísticas", ""],
            ["Média:", f"{avg_tension:.2f} N/cm"],
            ["Mínimo:", f"{min_tension:.2f} N/cm"],
            ["Máximo:", f"{max_tension:.2f} N/cm"],
            ["Total de Pontos:", str(total)],
            ["", ""],
            ["Classificação", ""],
            ["✅ OK:", f"{ok_count} ({100*ok_count/total:.0f}%)" if total else "0"],
            ["⚠️ WARNING:", f"{warn_count} ({100*warn_count/total:.0f}%)" if total else "0"],
            ["❌ NOK:", f"{nok_count} ({100*nok_count/total:.0f}%)" if total else "0"],
        ]

        summary_table = Table(summary_data, colWidths=[50*mm, 40*mm])
        summary_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 6), (1, 6), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.9, 0.9, 0.9)),
            ('BACKGROUND', (0, 6), (-1, 6), colors.Color(0.9, 0.9, 0.9)),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))

        # Gráfico de mapa de tensão
        if self.config.include_charts:
            chart_img = create_tension_map_chart(tension_data, self.config)
            if chart_img:
                # Layout lado a lado
                layout_data = [[summary_table, chart_img]]
                layout_table = Table(layout_data, colWidths=[95*mm, 85*mm])
                layout_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                elements.append(layout_table)
            else:
                elements.append(summary_table)
        else:
            elements.append(summary_table)

        elements.append(Spacer(1, 8*mm))
        return elements

    def _build_criteria_section(self, tension_data: Dict) -> List:
        """Constrói seção de critérios de aceitação."""
        elements = []

        elements.append(Paragraph("CRITÉRIOS DE ACEITAÇÃO", self.styles['Heading2']))

        # Obter critérios do tension_data ou usar padrões
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

        elements.append(Paragraph(criteria_text, self.styles['Normal']))
        elements.append(Spacer(1, 5*mm))

        return elements

    def _build_details_table(self, tension_data: Dict) -> List:
        """Constrói tabela detalhada de pontos."""
        elements = []

        measurements = tension_data.get('measurements', [])
        if not measurements:
            return elements

        elements.append(Paragraph("DETALHES POR PONTO", self.styles['Heading2']))

        # Cabeçalho da tabela
        table_data = [["#", "X (mm)", "Y (mm)", "Tensão (N/cm)", "Status"]]

        # Dados
        for i, m in enumerate(measurements, 1):
            status = m.get('status', 'OK').upper()
            status_symbol = {'OK': '✅', 'WARNING': '⚠️', 'WARN': '⚠️', 'NOK': '❌'}.get(status, '❓')

            table_data.append([
                str(i),
                f"{m.get('x', 0):.1f}",
                f"{m.get('y', 0):.1f}",
                f"{m.get('tension', 0):.2f}",
                f"{status_symbol} {status}"
            ])

        # Criar tabela
        col_widths = [12*mm, 30*mm, 30*mm, 40*mm, 35*mm]
        table = Table(table_data, colWidths=col_widths)

        # Estilo base
        style = [
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), self.config.get_primary_color()),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
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

        table.setStyle(TableStyle(style))
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
