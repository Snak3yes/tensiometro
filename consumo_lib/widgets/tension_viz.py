import numpy as np
import json
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton,
    QGridLayout, QFileDialog, QDoubleSpinBox, QSpinBox, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPen, QBrush, QPainter, QFont
from typing import List, Dict
import logging

from aoi_lib.config_manager import AOIConfigManager
from consumo_lib.ui import COLORS, TYPO, SPACE, DIM

logger = logging.getLogger(__name__)
class TensionVisualizationWidget(QWidget):
    """
    Widget para visualizar os resultados de medição de tensão do stencil.
    
    Suporta critérios de aceitação (OK/WARNING/NOK) vindos de receitas.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Inicializa atributos ANTES de setup_ui() para evitar erros
        self.measurements_data = None
        self.canvas_margin = 50
        self.point_radius = 15
        self.acceptance_criteria = None  # TensionAcceptance object
        
        # Agora inicializa a UI
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Título e controles
        title_layout = QHBoxLayout()
        
        title_label = QLabel("Visualização de Tensão do Stencil")
        title_label.setFont(TYPO.get_font(TYPO.HEADLINE_MEDIUM, bold=True))
        
        # Botão para carregar arquivo
        self.load_file_btn = QPushButton("📂 Carregar JSON")
        self.load_file_btn.clicked.connect(self.load_tension_file)
        
        # Botão para recarregar último arquivo
        self.reload_btn = QPushButton("🔄 Recarregar")
        self.reload_btn.clicked.connect(self.reload_last_file)
        self.reload_btn.setEnabled(False)
        
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(self.load_file_btn)
        title_layout.addWidget(self.reload_btn)
        
        layout.addLayout(title_layout)
        
        # ============ CRITÉRIOS DE ACEITAÇÃO ============
        criteria_group = QGroupBox("📊 Critérios de Aceitação (N/cm²)")
        criteria_layout = QGridLayout(criteria_group)
        
        # Tensão mínima
        criteria_layout.addWidget(QLabel("Mínimo:"), 0, 0)
        self.spin_min = QDoubleSpinBox()
        self.spin_min.setRange(0, 100)
        self.spin_min.setValue(25.0)
        self.spin_min.valueChanged.connect(self._on_criteria_changed)
        criteria_layout.addWidget(self.spin_min, 0, 1)
        
        # Warning baixo
        criteria_layout.addWidget(QLabel("Warning↓:"), 0, 2)
        self.spin_warn_low = QDoubleSpinBox()
        self.spin_warn_low.setRange(0, 100)
        self.spin_warn_low.setValue(28.0)
        self.spin_warn_low.valueChanged.connect(self._on_criteria_changed)
        criteria_layout.addWidget(self.spin_warn_low, 0, 3)
        
        # Warning alto
        criteria_layout.addWidget(QLabel("Warning↑:"), 0, 4)
        self.spin_warn_high = QDoubleSpinBox()
        self.spin_warn_high.setRange(0, 100)
        self.spin_warn_high.setValue(42.0)
        self.spin_warn_high.valueChanged.connect(self._on_criteria_changed)
        criteria_layout.addWidget(self.spin_warn_high, 0, 5)
        
        # Tensão máxima
        criteria_layout.addWidget(QLabel("Máximo:"), 0, 6)
        self.spin_max = QDoubleSpinBox()
        self.spin_max.setRange(0, 100)
        self.spin_max.setValue(45.0)
        self.spin_max.valueChanged.connect(self._on_criteria_changed)
        criteria_layout.addWidget(self.spin_max, 0, 7)
        
        # Carregar da receita
        self.btn_load_recipe = QPushButton("📋 Usar Receita")
        self.btn_load_recipe.setToolTip("Carrega critérios da receita atual")
        self.btn_load_recipe.clicked.connect(self.load_criteria_from_recipe)
        criteria_layout.addWidget(self.btn_load_recipe, 0, 8)
        
        layout.addWidget(criteria_group)
        
        # Informações do arquivo carregado
        self.info_label = QLabel("Nenhum arquivo carregado")
        self.info_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; font-style: italic;")
        layout.addWidget(self.info_label)
        
        # Canvas de visualização
        self.canvas = TensionCanvas()
        layout.addWidget(self.canvas, 1)  # Proporção 1 para expandir
        
        # ============ ESTATÍSTICAS DE RESULTADO ============
        self.stats_frame = QFrame()
        self.stats_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.stats_frame.setStyleSheet(f"background-color: {COLORS.SURFACE}; padding: {SPACE.XS}px;")
        stats_layout = QHBoxLayout(self.stats_frame)
        stats_layout.setContentsMargins(10, 5, 10, 5)

        self.stats_label = QLabel("Carregue um arquivo para ver estatísticas")
        self.stats_label.setStyleSheet(f"{TYPO.BODY_SMALL}")
        stats_layout.addWidget(self.stats_label)
        
        stats_layout.addStretch()
        
        # Indicador visual
        self.result_indicator = QLabel("---")
        self.result_indicator.setStyleSheet(f"""
            {TYPO.BODY_LARGE};
            font-weight: bold;
            padding: {SPACE.XS}px {SPACE.SM}px;
            border-radius: {DIM.RADIUS_SM}px;
            background-color: {COLORS.TEXT_DISABLED};
        """)
        stats_layout.addWidget(self.result_indicator)
        
        layout.addWidget(self.stats_frame)
        
        # Legenda
        self.legend_label = QLabel("")
        layout.addWidget(self.legend_label)
        
        self.last_file_path = None
        
        # Inicializa TensionAcceptance
        self._on_criteria_changed()
        
    def load_tension_file(self):
        """Carrega arquivo JSON com dados de tensão"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Carregar Dados de Tensão",
            "",
            "Arquivos JSON (*.json);;Todos os arquivos (*)"
        )
        
        if file_path:
            self.load_file(file_path)
            
    def load_file(self, file_path):
        """Carrega arquivo específico"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Valida se é um arquivo de tensão válido
            if data.get('type') != 'stencil_tension':
                QMessageBox.warning(
                    self, "Arquivo Inválido", 
                    "Este não é um arquivo de medição de tensão válido."
                )
                return
                
            self.measurements_data = data
            self.last_file_path = file_path
            self.reload_btn.setEnabled(True)
            
            # Atualiza informações
            self.update_info_display()
            
            # Atualiza canvas
            self.canvas.set_measurements(data)
            
            # Atualiza legenda
            self.update_legend()
            
        except Exception as e:
            QMessageBox.critical(
                self, "Erro", 
                f"Erro ao carregar arquivo:\n{str(e)}"
            )
            
    def reload_last_file(self):
        """Recarrega o último arquivo carregado"""
        if self.last_file_path:
            self.load_file(self.last_file_path)
            
    def update_info_display(self):
        """Atualiza informações do arquivo carregado"""
        if not self.measurements_data:
            return
            
        params = self.measurements_data.get('parameters', {})
        measurements = self.measurements_data.get('measurements', [])
        
        start = params.get('start', {})
        end = params.get('end', {})
        quantity = params.get('quantity', 0)
        
        info_text = (
            f"Arquivo carregado: {len(measurements)} pontos medidos | "
            f"Grid: {quantity}x{quantity} | "
            f"Área: X({start.get('x', 0):.1f} a {end.get('x', 0):.1f}) "
            f"Y({start.get('y', 0):.1f} a {end.get('y', 0):.1f})"
        )
        
        self.info_label.setText(info_text)
        self.info_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; font-weight: bold;")
        
    def update_legend(self):
        """Atualiza legenda com informações dos valores e classificação"""
        if not self.measurements_data:
            return
            
        measurements = self.measurements_data.get('measurements', [])
        if not measurements:
            return
            
        # Calcula estatísticas básicas
        tensions = [float(m.get('tension', 0)) for m in measurements]
        min_tension = min(tensions)
        max_tension = max(tensions)
        avg_tension = sum(tensions) / len(tensions)
        
        # Classifica cada medição
        counts = {'OK': 0, 'WARNING': 0, 'NOK': 0}
        if self.acceptance_criteria:
            for t in tensions:
                result = self.acceptance_criteria.classify(t)
                counts[result] = counts.get(result, 0) + 1
        
        total = len(tensions)
        ok_percent = (counts['OK'] / total * 100) if total > 0 else 0
        warn_percent = (counts['WARNING'] / total * 100) if total > 0 else 0
        nok_percent = (counts['NOK'] / total * 100) if total > 0 else 0
        
        # Atualiza legenda
        legend_text = (
            f"Tensão: Mín: {min_tension:.2f} | Máx: {max_tension:.2f} | Média: {avg_tension:.2f} N/cm² | "
            f"🟢 OK ({self.spin_warn_low.value()}-{self.spin_warn_high.value()}) | "
            f"🟡 WARNING | "
            f"🔴 NOK (<{self.spin_min.value()} ou >{self.spin_max.value()})"
        )
        self.legend_label.setText(legend_text)
        
        # Atualiza estatísticas
        self.stats_label.setText(
            f"🟢 OK: {counts['OK']} ({ok_percent:.1f}%) | "
            f"🟡 WARNING: {counts['WARNING']} ({warn_percent:.1f}%) | "
            f"🔴 NOK: {counts['NOK']} ({nok_percent:.1f}%) | "
            f"Total: {total} pontos"
        )
        
        # Atualiza indicador de resultado
        if nok_percent > 0:
            self.result_indicator.setText("❌ REPROVADO")
            self.result_indicator.setStyleSheet(f"""
                {TYPO.BODY_LARGE};
                font-weight: bold;
                padding: {SPACE.XS}px {SPACE.SM}px;
                border-radius: {DIM.RADIUS_SM}px;
                background-color: {COLORS.ERROR};
                color: {COLORS.BACKGROUND};
            """)
        elif warn_percent > 20:  # Mais de 20% warning
            self.result_indicator.setText("⚠️ ATENÇÃO")
            self.result_indicator.setStyleSheet(f"""
                {TYPO.BODY_LARGE};
                font-weight: bold;
                padding: {SPACE.XS}px {SPACE.SM}px;
                border-radius: {DIM.RADIUS_SM}px;
                background-color: {COLORS.WARNING};
                color: {COLORS.TEXT_PRIMARY};
            """)
        else:
            self.result_indicator.setText("✅ APROVADO")
            self.result_indicator.setStyleSheet(f"""
                {TYPO.BODY_LARGE};
                font-weight: bold;
                padding: {SPACE.XS}px {SPACE.SM}px;
                border-radius: {DIM.RADIUS_SM}px;
                background-color: {COLORS.SUCCESS};
                color: {COLORS.BACKGROUND};
            """)
        
        # Passa critérios para o canvas
        self.canvas.set_acceptance_criteria(self.acceptance_criteria)
    
    def _on_criteria_changed(self, value=None):
        """Callback quando os critérios de aceitação são alterados"""
        from aoi_lib.recipe_manager import TensionAcceptance
        
        self.acceptance_criteria = TensionAcceptance(
            min_tension=self.spin_min.value(),
            max_tension=self.spin_max.value(),
            warning_low=self.spin_warn_low.value(),
            warning_high=self.spin_warn_high.value()
        )
        
        # Atualiza se houver dados carregados
        if self.measurements_data:
            self.canvas.set_acceptance_criteria(self.acceptance_criteria)
            self.canvas.update()
            self.update_legend()
    
    def load_criteria_from_recipe(self):
        """Carrega critérios da receita atualmente selecionada"""
        # Tenta obter a receita do pai (AOIControllerApp)
        parent = self.parent()
        while parent and not hasattr(parent, 'current_recipe'):
            parent = parent.parent()
        
        if parent and hasattr(parent, 'current_recipe') and parent.current_recipe:
            recipe = parent.current_recipe
            acc = recipe.tension.acceptance
            
            # Bloqueia sinais para evitar múltiplas atualizações
            self.spin_min.blockSignals(True)
            self.spin_max.blockSignals(True)
            self.spin_warn_low.blockSignals(True)
            self.spin_warn_high.blockSignals(True)
            
            self.spin_min.setValue(acc.min_tension)
            self.spin_max.setValue(acc.max_tension)
            self.spin_warn_low.setValue(acc.warning_low)
            self.spin_warn_high.setValue(acc.warning_high)
            
            self.spin_min.blockSignals(False)
            self.spin_max.blockSignals(False)
            self.spin_warn_low.blockSignals(False)
            self.spin_warn_high.blockSignals(False)
            
            # Atualiza manualmente
            self._on_criteria_changed()
            
            QMessageBox.information(
                self, "Critérios Carregados",
                f"Critérios da receita '{recipe.name}' aplicados:\n\n"
                f"Mínimo: {acc.min_tension} N/cm²\n"
                f"Máximo: {acc.max_tension} N/cm²\n"
                f"Warning ↓: {acc.warning_low} N/cm²\n"
                f"Warning ↑: {acc.warning_high} N/cm²"
            )
        else:
            QMessageBox.warning(
                self, "Receita Não Encontrada",
                "Nenhuma receita está carregada.\n\n"
                "Acesse 'Receitas → Gerenciar Receitas' para carregar uma."
            )



class TensionCanvas(QWidget):
    """Canvas personalizado para desenhar os pontos de tensão com classificação OK/WARNING/NOK"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.measurements = None
        self.acceptance_criteria = None  # TensionAcceptance para classificação
        self.setMinimumSize(400, 400)
        
    def set_measurements(self, data):
        """Define os dados de medição"""
        self.measurements = data
        self.update()  # Força redesenho
    
    def set_acceptance_criteria(self, criteria):
        """Define os critérios de aceitação para colorização"""
        self.acceptance_criteria = criteria
        self.update()  # Força redesenho
        
    def paintEvent(self, event):
        """Desenha o canvas com os pontos de tensão"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Fundo branco
        painter.fillRect(self.rect(), COLORS.to_qcolor(COLORS.BACKGROUND))

        if not self.measurements:
            # Desenha mensagem quando não há dados
            painter.setPen(COLORS.to_qcolor(COLORS.TEXT_HINT))
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "Carregue um arquivo JSON para visualizar os dados"
            )
            return
            
        self._draw_measurements(painter)
        
    def _draw_measurements(self, painter):
        """Desenha as medições no canvas"""
        measurements_list = self.measurements.get('measurements', [])
        params = self.measurements.get('parameters', {})
        
        if not measurements_list:
            return
            
        # Calcula limites da área
        start = params.get('start', {'x': 0, 'y': 0})
        end = params.get('end', {'x': 100, 'y': 100})
        
        # Dimensões da área de trabalho
        work_width = abs(end['x'] - start['x'])
        work_height = abs(end['y'] - start['y'])
        
        # Dimensões do canvas (com margem)
        margin = 50
        canvas_width = self.width() - 2 * margin
        canvas_height = self.height() - 2 * margin
        
        # Usa o menor lado para manter proporção quadrada
        canvas_size = min(canvas_width, canvas_height)
        
        # Calcula escala
        scale_x = canvas_size / work_width if work_width > 0 else 1
        scale_y = canvas_size / work_height if work_height > 0 else 1
        scale = min(scale_x, scale_y)
        
        # Centro do canvas
        center_x = self.width() / 2
        center_y = self.height() / 2
        
        # Desenha bordas da área de trabalho
        self._draw_work_area_border(painter, center_x, center_y, work_width, work_height, scale)
        
        # Calcula estatísticas para coloração
        tensions = [float(m.get('tension', 0)) for m in measurements_list]
        min_tension = min(tensions) if tensions else 0
        max_tension = max(tensions) if tensions else 100
        tension_range = max_tension - min_tension if max_tension != min_tension else 1
        
        # Desenha cada ponto
        for measurement in measurements_list:
            self._draw_measurement_point(
                painter, measurement, start, center_x, center_y, 
                scale, min_tension, tension_range
            )
            
    def _draw_work_area_border(self, painter, center_x, center_y, work_width, work_height, scale):
        """Desenha a borda da área de trabalho"""
        # Calcula posição do retângulo da área de trabalho
        rect_width = work_width * scale
        rect_height = work_height * scale
        
        rect_x = center_x - rect_width / 2
        rect_y = center_y - rect_height / 2
        
        # Desenha borda
        painter.setPen(QPen(COLORS.to_qcolor(COLORS.BORDER_VARIANT), 2))
        painter.setBrush(QBrush())  # Sem preenchimento
        painter.drawRect(QRectF(rect_x, rect_y, rect_width, rect_height))

        # Desenha grid de referência (opcional)
        painter.setPen(QPen(COLORS.to_qcolor(COLORS.SURFACE_VARIANT), 1))
        
        # Linhas verticais
        for i in range(1, 3):  # Assume grid 3x3
            x = rect_x + (rect_width * i / 3)
            painter.drawLine(QPointF(x, rect_y), QPointF(x, rect_y + rect_height))
            
        # Linhas horizontais  
        for i in range(1, 3):
            y = rect_y + (rect_height * i / 3)
            painter.drawLine(QPointF(rect_x, y), QPointF(rect_x + rect_width, y))
            
    def _draw_measurement_point(self, painter, measurement, start, center_x, center_y, 
                              scale, min_tension, tension_range):
        """Desenha um ponto de medição individual"""
        x = measurement.get('x', 0)
        y = measurement.get('y', 0)
        tension = float(measurement.get('tension', 0))
        
        # Calcula dimensões da área de trabalho
        params = self.measurements.get('parameters', {})
        end = params.get('end', {'x': 100, 'y': 100})
        
        work_width = abs(end['x'] - start['x'])
        work_height = abs(end['y'] - start['y'])
        
        # Dimensões do retângulo de trabalho no canvas
        margin = 50
        canvas_size = min(self.width() - 2 * margin, self.height() - 2 * margin)
        scale = min(canvas_size / work_width, canvas_size / work_height) if work_width > 0 and work_height > 0 else 1
        
        rect_width = work_width * scale
        rect_height = work_height * scale
        
        # Posição do retângulo da área de trabalho (centralizado)
        rect_x = center_x - rect_width / 2
        rect_y = center_y - rect_height / 2
        
        # Normaliza a posição do ponto dentro da área de trabalho (0 a 1)
        norm_x = (x - start['x']) / work_width if work_width > 0 else 0
        norm_y = (y - start['y']) / work_height if work_height > 0 else 0
        
        # Mapeia para coordenadas do canvas
        # Nota: no canvas, Y cresce para baixo, então invertemos norm_y
        canvas_x = rect_x + (norm_x * rect_width)
        canvas_y = rect_y + ((1 - norm_y) * rect_height)  # Inverte Y para visualização correta
        # Determina cor baseada na tensão
        color = self._get_tension_color(tension, min_tension, tension_range)
        
        # Desenha círculo
        point_radius = 20
        painter.setPen(QPen(COLORS.to_qcolor(COLORS.TEXT_SECONDARY), 2))
        painter.setBrush(QBrush(color))

        painter.drawEllipse(
            QPointF(canvas_x, canvas_y),
            point_radius, point_radius
        )

        # Desenha texto com valor
        painter.setPen(COLORS.to_qcolor(COLORS.TEXT_PRIMARY))
        painter.setFont(TYPO.label_small(bold=True))

        # Texto centralizado no círculo
        text = f"{tension:.1f}"
        text_rect = painter.fontMetrics().boundingRect(text)
        text_x = canvas_x - text_rect.width() / 2
        text_y = canvas_y + text_rect.height() / 4

        painter.drawText(QPointF(text_x, text_y), text)

        # Desenha coordenadas menores abaixo
        coord_text = f"({x:.1f},{y:.1f})"
        painter.setFont(TYPO.LABEL_SMALL)
        painter.setPen(COLORS.to_qcolor(COLORS.TEXT_SECONDARY))
        
        coord_rect = painter.fontMetrics().boundingRect(coord_text)
        coord_x = canvas_x - coord_rect.width() / 2
        coord_y = canvas_y + point_radius + 15
        
        painter.drawText(QPointF(coord_x, coord_y), coord_text)
        
    def _get_tension_color(self, tension, min_tension, tension_range):
        """
        Retorna cor baseada no valor da tensão.
        
        Se há critérios de aceitação definidos, usa classificação OK/WARNING/NOK.
        Caso contrário, usa gradiente baseado no intervalo dos dados.
        """
        # Usa classificação se disponível
        if self.acceptance_criteria:
            result = self.acceptance_criteria.classify(tension)
            if result == 'OK':
                return COLORS.to_qcolor(COLORS.SUCCESS)
            elif result == 'WARNING':
                return COLORS.to_qcolor(COLORS.WARNING)
            else:  # NOK
                return COLORS.to_qcolor(COLORS.ERROR)
        
        # Fallback: gradiente baseado nos dados
        if tension_range == 0:
            return COLORS.to_qcolor(COLORS.SUCCESS)

        # Normaliza tensão (0-1)
        normalized = (tension - min_tension) / tension_range

        # Mapeia para cores: Verde (baixo) -> Amarelo (médio) -> Vermelho (alto)
        if normalized < 0.33:
            # Verde para amarelo
            ratio = normalized * 3
            return QColor.fromRgbF(0.39 + 0.61 * ratio, 0.78, 0.39 * (1 - ratio))
        elif normalized < 0.66:
            # Amarelo para laranja
            ratio = (normalized - 0.33) * 3
            return QColor.fromRgbF(1.0, 0.78 - 0.2 * ratio, 0.0)
        else:
            # Laranja para vermelho
            ratio = (normalized - 0.66) * 3
            return QColor.fromRgbF(1.0, 0.59 * (1 - ratio), 0.0)



