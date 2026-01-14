"""
inspection_builder.py
---------------------
Construtor de relatório de inspeção visual.

Este módulo contém a classe InspectionReportBuilder responsável por gerar
relatórios PDF de inspeção visual com imagem, resumo estatístico e tabela de defeitos.
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
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, HRFlowable
)

# Módulos locais
from aoi_lib.reports.config import ReportConfig, get_custom_styles

log = logging.getLogger(__name__)


class InspectionReportBuilder:
    """
    Construtor de relatório de inspeção visual.

    Gera um PDF com:
    - Imagem do overlay de inspeção
    - Resumo estatístico (OK, PARTIAL, BLOCKED)
    - Tabela de defeitos detectados
    """

    def __init__(self, config: ReportConfig):
        self.config = config
        self.styles = get_custom_styles(config)

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
        story.extend(self._build_header(inspection_result, stencil_code, operator))

        # Linha horizontal
        story.append(HRFlowable(width="100%", thickness=1, color=self.config.get_primary_color()))
        story.append(Spacer(1, 8*mm))

        # Resumo
        story.extend(self._build_summary_section(inspection_result))

        # Imagem de overlay
        if overlay_image_path and os.path.exists(overlay_image_path):
            story.extend(self._build_overlay_section(overlay_image_path))

        # Tabela de defeitos
        story.extend(self._build_defects_table(inspection_result))

        # Rodapé
        story.extend(self._build_footer())

        # Gerar PDF
        doc.build(story)
        log.info(f"Relatório de inspeção gerado: {output_path}")

        return output_path

    def _build_header(
        self,
        result: Dict,
        stencil_code: Optional[str],
        operator: Optional[str]
    ) -> List:
        """Constrói cabeçalho do relatório."""
        elements = []

        elements.append(Paragraph(self.config.company_name, self.styles['Title']))
        elements.append(Paragraph(self.config.company_subtitle, self.styles['Subtitle']))
        elements.append(Paragraph("RELATÓRIO DE INSPEÇÃO VISUAL", self.styles['Heading1']))
        elements.append(Spacer(1, 5*mm))

        # Status geral com destaque
        overall = result.get('overall_status', 'OK')
        status_color = {
            'OK': self.config.get_success_color(),
            'WARNING': self.config.get_warning_color(),
            'NOK': self.config.get_danger_color()
        }.get(overall, colors.black)

        status_style = ParagraphStyle(
            'StatusBig',
            parent=self.styles['Title'],
            fontSize=24,
            textColor=status_color,
            alignment=TA_CENTER,
        )
        elements.append(Paragraph(f"RESULTADO: {overall}", status_style))
        elements.append(Spacer(1, 5*mm))

        # Informações da inspeção
        now = datetime.now()
        info_data = [
            ["Data:", now.strftime("%d/%m/%Y"), "Hora:", now.strftime("%H:%M:%S")],
            ["Stencil:", stencil_code or "-", "Operador:", operator or "-"],
            ["Taxa de Aprovação:", f"{result.get('approval_rate', 100):.1f}%", "", ""],
        ]

        info_table = Table(info_data, colWidths=[30*mm, 50*mm, 25*mm, 50*mm])
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

    def _build_summary_section(self, result: Dict) -> List:
        """Constrói seção de resumo."""
        elements = []

        elements.append(Paragraph("RESUMO DA INSPEÇÃO", self.styles['Heading2']))

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

        summary_table = Table(summary_data, colWidths=[65*mm, 40*mm, 35*mm])

        style = [
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (-1, 0), self.config.get_primary_color()),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            # Cores por tipo
            ('BACKGROUND', (0, 1), (-1, 1), colors.Color(0.9, 1.0, 0.9)),  # OK verde claro
            ('BACKGROUND', (0, 2), (-1, 2), colors.Color(1.0, 0.98, 0.9)),  # Partial amarelo
            ('BACKGROUND', (0, 3), (-1, 3), colors.Color(1.0, 0.9, 0.9)),  # Blocked vermelho
            ('BACKGROUND', (0, 4), (-1, 4), colors.Color(0.95, 0.95, 0.95)),  # Total cinza
            ('FONTNAME', (0, 4), (-1, 4), 'Helvetica-Bold'),
        ]

        summary_table.setStyle(TableStyle(style))
        elements.append(summary_table)
        elements.append(Spacer(1, 8*mm))

        return elements

    def _build_overlay_section(self, image_path: str) -> List:
        """Constrói seção com imagem do overlay."""
        elements = []

        elements.append(Paragraph("IMAGEM DE INSPEÇÃO", self.styles['Heading2']))

        try:
            # Calcular tamanho proporcional
            from PIL import Image as PILImage
            with PILImage.open(image_path) as img:
                w, h = img.size

            # Escalar para caber na página (máx 160mm de largura)
            max_w = 160*mm
            max_h = 100*mm

            ratio = min(max_w / w, max_h / h)
            display_w = w * ratio
            display_h = h * ratio

            img = Image(image_path, width=display_w, height=display_h)
            elements.append(img)

        except Exception as e:
            log.warning(f"Erro ao incluir imagem: {e}")
            elements.append(Paragraph("Imagem não disponível.", self.styles['Normal']))

        elements.append(Spacer(1, 5*mm))
        elements.append(Paragraph(
            "<i>Verde = OK, Amarelo = Parcialmente obstruída, Vermelho = Totalmente obstruída</i>",
            self.styles['Small']
        ))
        elements.append(Spacer(1, 8*mm))

        return elements

    def _build_defects_table(self, result: Dict) -> List:
        """Constrói tabela de defeitos."""
        elements = []

        defects = result.get('defects', [])
        if not defects:
            elements.append(Paragraph("✅ Nenhum defeito detectado.", self.styles['Normal']))
            return elements

        elements.append(Paragraph("DEFEITOS DETECTADOS", self.styles['Heading2']))

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

        # Criar tabela
        col_widths = [10*mm, 20*mm, 25*mm, 40*mm, 30*mm, 35*mm]
        table = Table(table_data, colWidths=col_widths)

        style = [
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (-1, 0), self.config.get_primary_color()),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
        ]

        # Cores por status
        for i, d in enumerate(defects[:30]):
            row = i + 1
            status = d.get('status', 'BLOCKED')
            status_val = status.value if hasattr(status, 'value') else str(status)

            if status_val == 'PARTIAL':
                style.append(('BACKGROUND', (0, row), (-1, row), colors.Color(1.0, 0.98, 0.9)))
            else:  # BLOCKED
                style.append(('BACKGROUND', (0, row), (-1, row), colors.Color(1.0, 0.9, 0.9)))

        table.setStyle(TableStyle(style))
        elements.append(table)
        elements.append(Spacer(1, 5*mm))

        return elements

    def _build_footer(self) -> List:
        """Constrói rodapé."""
        elements = []

        elements.append(Spacer(1, 10*mm))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))

        footer_text = f"""
        Relatório de Inspeção Visual gerado automaticamente pelo {self.config.company_name}<br/>
        Data de geração: {datetime.now().strftime("%d/%m/%Y às %H:%M:%S")}
        """
        elements.append(Paragraph(footer_text, self.styles['Footer']))

        return elements
