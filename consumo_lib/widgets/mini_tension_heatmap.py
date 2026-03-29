"""
Widget de Heatmap Compacto para Medição de Tensão

Widget otimizado para exibição em painéis laterais compactos (300-350px de largura).
Grid 4x4 com visualização clara dos pontos de medição.
"""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush
from PyQt6.QtCore import Qt, QPointF
from typing import List, Dict

from consumo_lib.ui import COLORS, TYPO


class MiniTensionHeatmapWidget(QWidget):
    """
    Widget para visualização compacta de heatmap de tensão.

    Grid 4x4 otimizado para painel de 340px de largura.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.measurements: List[Dict] = []
        self.parameters: Dict = {}
        self.acceptance_criteria = None
        self.setMinimumSize(310, 220)  # Ajustado para caber em ~677px de altura útil

    def set_measurements(self, data: Dict):
        """Define dados de medição para visualização."""
        self.measurements = data.get('measurements', [])
        self.parameters = data.get('parameters', {})
        self.update()

    def set_acceptance_criteria(self, criteria):
        """Define critérios para colorização."""
        self.acceptance_criteria = criteria
        self.update()

    def paintEvent(self, event):
        """Desenha o heatmap."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Fundo
        painter.fillRect(self.rect(), COLORS.to_qcolor(COLORS.BACKGROUND))

        if not self.measurements:
            # Mensagem de placeholder
            painter.setPen(COLORS.to_qcolor(COLORS.TEXT_HINT))
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "Carregue um arquivo JSON para visualizar"
            )
            return

        # Desenha grid 4x4
        self._draw_grid(painter)

        # Desenha pontos de medição
        self._draw_measurement_points(painter)

    def _draw_grid(self, painter: QPainter):
        """Desenha grid 4x4."""
        margin = 10
        size = min(self.width(), self.height()) - 2 * margin

        painter.setPen(QPen(COLORS.to_qcolor(COLORS.BORDER), 1))

        # Retângulo externo
        painter.drawRect(margin, margin, size, size)

        # Linhas verticais
        for i in range(1, 4):
            x = margin + (size * i / 4)
            painter.drawLine(QPointF(x, margin), QPointF(x, margin + size))

        # Linhas horizontais
        for i in range(1, 4):
            y = margin + (size * i / 4)
            painter.drawLine(QPointF(margin, y), QPointF(margin + size, y))

    def _draw_measurement_points(self, painter: QPainter):
        """Desenha pontos de medição no grid 4x4."""
        if not self.measurements:
            return

        margin = 10
        size = min(self.width(), self.height()) - 2 * margin

        # Calcula limites da área
        params = self.parameters
        start = params.get('start', {'x': 0, 'y': 0})
        end = params.get('end', {'x': 100, 'y': 100})

        work_width = abs(end['x'] - start['x']) if end['x'] != start['x'] else 1
        work_height = abs(end['y'] - start['y']) if end['y'] != start['y'] else 1

        # Tamanho de cada célula do grid 4x4
        cell_width = size / 4
        cell_height = size / 4

        # Desenha cada ponto
        for measurement in self.measurements:
            x = measurement.get('x', 0)
            y = measurement.get('y', 0)
            tension = float(measurement.get('tension', 0))

            # Normaliza posição (0 a 1)
            norm_x = (x - start['x']) / work_width if work_width > 0 else 0
            norm_y = (y - start['y']) / work_height if work_height > 0 else 0

            # Mapeia para coordenadas do canvas (inverte Y para visualização correta)
            # Grid 4x4: cada ponto vai para uma célula específica
            cell_x = int(norm_x * 3.99)  # 0-3
            cell_y = int(norm_y * 3.99)  # 0-3

            # Limita a 0-3
            cell_x = max(0, min(3, cell_x))
            cell_y = max(0, min(3, cell_y))

            # Centro da célula
            center_x = margin + (cell_x * cell_width) + (cell_width / 2)
            center_y = margin + ((3 - cell_y) * cell_height) + (cell_height / 2)  # Inverte Y

            # Determina cor baseada na tensão
            color = self._get_tension_color(tension)

            # Desenha círculo (raio 14px conforme proposta)
            point_radius = 14
            painter.setPen(QPen(COLORS.to_qcolor(COLORS.TEXT_SECONDARY), 1))
            painter.setBrush(QBrush(color))
            painter.drawEllipse(QPointF(center_x, center_y), point_radius, point_radius)

            # Desenha valor da tensão
            painter.setPen(COLORS.to_qcolor(COLORS.TEXT_PRIMARY))
            painter.setFont(TYPO.get_font(TYPO.LABEL_SMALL, bold=True))
            text = f"{tension:.1f}"
            text_rect = painter.fontMetrics().boundingRect(text)
            text_x = center_x - text_rect.width() / 2
            text_y = center_y + text_rect.height() / 4
            painter.drawText(QPointF(text_x, text_y), text)

    def _get_tension_color(self, tension: float) -> QColor:
        """
        Retorna cor baseada no valor da tensão.

        Se há critérios de aceitação definidos, usa classificação OK/WARNING/NOK.
        Caso contrário, usa gradiente baseado no intervalo dos dados.
        """
        if self.acceptance_criteria:
            result = self.acceptance_criteria.classify(tension)
            if result == 'OK':
                return COLORS.to_qcolor(COLORS.SUCCESS)
            elif result == 'WARNING':
                return COLORS.to_qcolor(COLORS.WARNING)
            else:  # NOK
                return COLORS.to_qcolor(COLORS.ERROR)

        # Fallback: gradiente baseado nos dados
        tensions = [float(m.get('tension', 0)) for m in self.measurements]
        if not tensions:
            return COLORS.to_qcolor(COLORS.SUCCESS)

        min_tension = min(tensions)
        max_tension = max(tensions)
        tension_range = max_tension - min_tension if max_tension != min_tension else 1

        normalized = (tension - min_tension) / tension_range

        # Mapeia para cores: Verde (bom) -> Amarelo (médio) -> Vermelho (ruim)
        if normalized < 0.5:
            # Verde para amarelo
            ratio = normalized * 2
            r = int(0x10 + (0xF5 - 0x10) * ratio)
            g = int(0xB9 + (0x9E - 0xB9) * ratio)
            b = int(0x81 + (0x0B - 0x81) * ratio)
            return QColor(r, g, b)
        else:
            # Amarelo para vermelho
            ratio = (normalized - 0.5) * 2
            r = int(0xF5 + (0xEF - 0xF5) * ratio)
            g = int(0x9E + (0x44 - 0x9E) * ratio)
            b = int(0x0B + (0x44 - 0x0B) * ratio)
            return QColor(r, g, b)

    def clear(self):
        """Limpa o heatmap."""
        self.measurements = []
        self.parameters = {}
        self.update()
