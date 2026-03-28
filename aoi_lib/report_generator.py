"""
report_generator.py
--------------------
Gerador de relatórios PDF para o sistema AOI.

Este módulo oferece:
- Relatório de medição de tensão individual
- Relatório de histórico do stencil
- Relatório consolidado por período
- Configuração personalizável (logo, nome da empresa)
- Gráficos de mapa de tensão e tendência

Dependências:
    pip install reportlab matplotlib
"""

from __future__ import annotations

import os
import io
import logging
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

# Reportlab para geração de PDF
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, HRFlowable
)
from reportlab.graphics.shapes import Drawing, Rect, Circle, String
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.charts.legends import Legend
from reportlab.graphics import renderPDF

# Matplotlib para gráficos mais sofisticados
import matplotlib
matplotlib.use('Agg')  # Backend não-interativo
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import LinearSegmentedColormap
import numpy as np

log = logging.getLogger(__name__)


# ============================================================================
#  CONFIGURAÇÃO DO RELATÓRIO
# ============================================================================

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


# ============================================================================
#  ESTILOS DO DOCUMENTO
# ============================================================================

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


# ============================================================================
#  GERADOR DE RELATÓRIO DE TENSÃO
# ============================================================================

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
            chart_img = self._create_tension_map_chart(tension_data)
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
    
    def _create_tension_map_chart(self, tension_data: Dict) -> Optional[Image]:
        """Cria gráfico de mapa de tensão usando matplotlib."""
        measurements = tension_data.get('measurements', [])
        if not measurements:
            return None
        
        try:
            # Extrair dados
            xs = [m.get('x', 0) for m in measurements]
            ys = [m.get('y', 0) for m in measurements]
            tensions = [m.get('tension', 0) for m in measurements]
            statuses = [m.get('status', 'OK').upper() for m in measurements]
            
            # Criar figura
            fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
            
            # Cores por status
            status_colors = {
                'OK': '#2ecc71',      # Verde
                'WARNING': '#f1c40f', # Amarelo
                'WARN': '#f1c40f',
                'NOK': '#e74c3c',     # Vermelho
            }
            
            point_colors = [status_colors.get(s, '#3498db') for s in statuses]
            
            # Plotar pontos
            scatter = ax.scatter(xs, ys, c=point_colors, s=100, edgecolors='black', linewidths=0.5)
            
            # Adicionar valores de tensão
            for x, y, t in zip(xs, ys, tensions):
                ax.annotate(f'{t:.1f}', (x, y), textcoords="offset points", 
                           xytext=(0, 8), ha='center', fontsize=7)
            
            ax.set_xlabel('X (mm)', fontsize=9)
            ax.set_ylabel('Y (mm)', fontsize=9)
            ax.set_title('Mapa de Tensão', fontsize=10, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.set_aspect('equal')
            
            # Legenda
            from matplotlib.patches import Patch
            legend_elements = [
                Patch(facecolor='#2ecc71', edgecolor='black', label='OK'),
                Patch(facecolor='#f1c40f', edgecolor='black', label='WARNING'),
                Patch(facecolor='#e74c3c', edgecolor='black', label='NOK'),
            ]
            ax.legend(handles=legend_elements, loc='upper right', fontsize=7)
            
            plt.tight_layout()
            
            # Salvar em buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            buf.seek(0)
            plt.close(fig)
            
            # Criar Image do reportlab
            img = Image(buf, width=80*mm, height=60*mm)
            return img
            
        except Exception as e:
            log.warning(f"Erro ao criar gráfico de tensão: {e}")
            return None
    
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


# ============================================================================
#  GERADOR DE RELATÓRIO DE HISTÓRICO DO STENCIL
# ============================================================================

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
        
        try:
            # Extrair dados para gráfico
            dates = []
            averages = []
            
            for record in history[-20:]:  # Últimas 20 medições
                ts = record.get('timestamp', '')
                avg = record.get('average_tension', 0)
                if ts and avg:
                    try:
                        dt = datetime.fromisoformat(ts)
                        dates.append(dt)
                        averages.append(avg)
                    except:
                        pass
            
            if len(dates) >= 2:
                # Criar gráfico
                fig, ax = plt.subplots(figsize=(7, 3), dpi=100)
                
                ax.plot(range(len(averages)), averages, 'b-o', linewidth=2, markersize=6)
                ax.fill_between(range(len(averages)), averages, alpha=0.3)
                
                ax.set_xlabel('Medição', fontsize=9)
                ax.set_ylabel('Tensão Média (N/cm)', fontsize=9)
                ax.set_title('Evolução da Tensão Média', fontsize=10, fontweight='bold')
                ax.grid(True, alpha=0.3)
                
                # Linha de tendência
                if len(averages) >= 3:
                    z = np.polyfit(range(len(averages)), averages, 1)
                    p = np.poly1d(z)
                    ax.plot(range(len(averages)), p(range(len(averages))), 
                           'r--', alpha=0.7, label='Tendência')
                    ax.legend(fontsize=8)
                
                plt.tight_layout()
                
                # Salvar em buffer
                buf = io.BytesIO()
                plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
                buf.seek(0)
                plt.close(fig)
                
                # Criar Image
                img = Image(buf, width=160*mm, height=70*mm)
                elements.append(img)
        
        except Exception as e:
            log.warning(f"Erro ao criar gráfico de tendência: {e}")
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


# ============================================================================
#  CLASSE PRINCIPAL DO GERADOR
# ============================================================================

class ReportGenerator:
    """
    Classe principal para geração de relatórios.
    
    Uso:
        config = ReportConfig(company_name="MinhaEmpresa")
        generator = ReportGenerator(config)
        
        # Relatório de tensão
        path = generator.generate_tension_report(tension_data, stencil_code="STN-001")
        
        # Relatório de histórico
        path = generator.generate_stencil_history_report(stencil, history)
    """
    
    def __init__(self, config: Optional[ReportConfig] = None):
        self.config = config or ReportConfig()
    
    def generate_tension_report(
        self,
        tension_data: Dict[str, Any],
        stencil_code: Optional[str] = None,
        stencil_description: Optional[str] = None,
        recipe_name: Optional[str] = None,
        operator: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> str:
        """
        Gera relatório de medição de tensão.
        
        Returns:
            Caminho do arquivo PDF gerado
        """
        builder = TensionReportBuilder(self.config)
        return builder.build(
            tension_data=tension_data,
            stencil_code=stencil_code,
            stencil_description=stencil_description,
            recipe_name=recipe_name,
            operator=operator,
            output_path=output_path
        )
    
    def generate_stencil_history_report(
        self,
        stencil: Dict[str, Any],
        history: List[Dict[str, Any]],
        output_path: Optional[str] = None
    ) -> str:
        """
        Gera relatório de histórico do stencil.
        
        Returns:
            Caminho do arquivo PDF gerado
        """
        builder = StencilHistoryReportBuilder(self.config)
        return builder.build(
            stencil=stencil,
            history=history,
            output_path=output_path
        )
    
    def update_config(self, **kwargs):
        """Atualiza configuração."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)


# ============================================================================
#  EXEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    # Configuração
    config = ReportConfig(
        company_name="SeuStencil",
        company_subtitle="Sistema de Inspeção de Stencils",
        output_dir="reports"
    )
    
    generator = ReportGenerator(config)
    
    # Dados de exemplo
    tension_data = {
        "measurements": [
            {"x": -50, "y": -40, "tension": 28.3, "status": "OK"},
            {"x": -25, "y": -40, "tension": 24.1, "status": "WARNING"},
            {"x": 0, "y": -40, "tension": 29.5, "status": "OK"},
            {"x": 25, "y": -40, "tension": 31.2, "status": "OK"},
            {"x": 50, "y": -40, "tension": 27.8, "status": "OK"},
            {"x": -50, "y": 0, "tension": 26.5, "status": "OK"},
            {"x": -25, "y": 0, "tension": 22.8, "status": "NOK"},
            {"x": 0, "y": 0, "tension": 28.9, "status": "OK"},
            {"x": 25, "y": 0, "tension": 30.1, "status": "OK"},
            {"x": 50, "y": 0, "tension": 29.3, "status": "OK"},
            {"x": -50, "y": 40, "tension": 27.2, "status": "OK"},
            {"x": -25, "y": 40, "tension": 28.8, "status": "OK"},
            {"x": 0, "y": 40, "tension": 25.5, "status": "WARNING"},
            {"x": 25, "y": 40, "tension": 29.9, "status": "OK"},
            {"x": 50, "y": 40, "tension": 28.1, "status": "OK"},
        ],
        "acceptance_criteria": {
            "ok_min": 26.0,
            "ok_max": 32.0,
            "warning_low": 24.0,
            "warning_high": 35.0,
        }
    }
    
    # Gerar relatório de tensão
    print("\nGerando relatório de tensão...")
    path = generator.generate_tension_report(
        tension_data=tension_data,
        stencil_code="STN-2024-001",
        stencil_description="PCB Principal v2.1",
        recipe_name="PCB_Standard",
        operator="João Silva"
    )
    print(f"✅ Relatório gerado: {path}")
    
    # Dados de histórico para teste
    stencil = {
        "code": "STN-2024-001",
        "description": "PCB Principal v2.1",
        "recipe_name": "PCB_Standard",
        "created_at": "2024-01-15",
        "last_inspection": "2024-12-11",
        "inspection_count": 45,
        "status": "active"
    }
    
    history = [
        {"timestamp": "2024-11-01T10:30:00", "average_tension": 29.5, "min_tension": 26.0, 
         "max_tension": 32.0, "result": "OK", "ok_count": 15, "warning_count": 0, "nok_count": 0, "operator": "Maria"},
        {"timestamp": "2024-11-15T14:20:00", "average_tension": 28.8, "min_tension": 25.5, 
         "max_tension": 31.0, "result": "OK", "ok_count": 14, "warning_count": 1, "nok_count": 0, "operator": "João"},
        {"timestamp": "2024-12-01T09:45:00", "average_tension": 27.5, "min_tension": 24.0, 
         "max_tension": 30.0, "result": "WARNING", "ok_count": 12, "warning_count": 3, "nok_count": 0, "operator": "Maria"},
        {"timestamp": "2024-12-10T16:00:00", "average_tension": 26.8, "min_tension": 23.0, 
         "max_tension": 29.5, "result": "WARNING", "ok_count": 10, "warning_count": 4, "nok_count": 1, "operator": "João"},
    ]
    
    # Gerar relatório de histórico
    print("\nGerando relatório de histórico...")
    path = generator.generate_stencil_history_report(
        stencil=stencil,
        history=history
    )
    print(f"✅ Relatório gerado: {path}")
