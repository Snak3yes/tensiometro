"""
reports/chart_generator.py
-------------------------
Geração de gráficos para relatórios PDF usando matplotlib.
"""

import io
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

import matplotlib
matplotlib.use('Agg')  # Backend não-interativo
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

from reportlab.platypus import Image
from reportlab.lib.units import mm

log = logging.getLogger(__name__)


def create_tension_map_chart(tension_data: Dict) -> Optional[Image]:
    """
    Cria gráfico de mapa de tensão usando matplotlib.

    Args:
        tension_data: Dicionário com dados da medição contendo 'measurements'

    Returns:
        Image do reportlab ou None em caso de erro
    """
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
        legend_elements = [
            patches.Patch(facecolor='#2ecc71', edgecolor='black', label='OK'),
            patches.Patch(facecolor='#f1c40f', edgecolor='black', label='WARNING'),
            patches.Patch(facecolor='#e74c3c', edgecolor='black', label='NOK'),
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


def create_trend_chart(history: List[Dict]) -> Optional[Image]:
    """
    Cria gráfico de tendência de tensão usando matplotlib.

    Args:
        history: Lista de registros de medição com 'timestamp' e 'average_tension'

    Returns:
        Image do reportlab ou None em caso de erro
    """
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

        if len(dates) < 2:
            return None

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
        return img

    except Exception as e:
        log.warning(f"Erro ao criar gráfico de tendência: {e}")
        return None
