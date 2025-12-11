import sys
import cv2
import os
import time
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QGroupBox, 
                             QGridLayout, QLineEdit, 
                             QComboBox, QListWidget, QCheckBox, QListWidgetItem, 
                             QFileDialog, QMessageBox, QTabWidget, QSizePolicy,
                             QSplitter, QFrame, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QDialog, QInputDialog,
                             QProgressDialog, QDoubleSpinBox, QSpinBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QEvent, QRectF, QPointF
from PyQt6.QtGui import (QPixmap, QImage, QFont, QAction, QDoubleValidator, 
                         QPainter, QColor, QPen, QBrush)

from aoi_lib import CNCAOIController, InspectionPosition
from aoi_lib.plc_axis_controller import PLCAxisController
from grbl_streamer import GrblStreamer
from aoi_lib.utils.move_task import MoveTaskThread
from aoi_lib.config_manager import AOIConfigManager, SettingsDialog
from dataclasses import dataclass
from aoi_lib.stencil_tension import StencilTensionDialog
from aoi_lib.fov_calibration import (
    FOVCalibration, CameraFOVConverter, FOVCalibrationDialog, ClickableVideoLabel
)
from aoi_lib.stencil_tracker import StencilTracker, Stencil, TensionRecord
from aoi_lib.stencil_tracker_ui import (
    StencilIdentificationWidget, StencilHistoryDialog, 
    StencilManagerDialog, StencilCreateDialog
)
from aoi_lib.fiducial_alignment_widget import FiducialAlignmentWidget
from aoi_lib.report_generator import ReportGenerator, ReportConfig
from aoi_lib.report_settings_dialog import ReportSettingsDialog
import logging
import json
from mosaic_builder import compose_mosaic_from_folder

logger = logging.getLogger("consumo_lib")
logger.setLevel(logging.DEBUG)
# Se necessário, adicione um handler:
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

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
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(14)
        title_label.setFont(title_font)
        
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
        self.info_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.info_label)
        
        # Canvas de visualização
        self.canvas = TensionCanvas()
        layout.addWidget(self.canvas, 1)  # Proporção 1 para expandir
        
        # ============ ESTATÍSTICAS DE RESULTADO ============
        self.stats_frame = QFrame()
        self.stats_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.stats_frame.setStyleSheet("background-color: #f8f8f8; padding: 5px;")
        stats_layout = QHBoxLayout(self.stats_frame)
        stats_layout.setContentsMargins(10, 5, 10, 5)
        
        self.stats_label = QLabel("Carregue um arquivo para ver estatísticas")
        self.stats_label.setStyleSheet("font-size: 12px;")
        stats_layout.addWidget(self.stats_label)
        
        stats_layout.addStretch()
        
        # Indicador visual
        self.result_indicator = QLabel("---")
        self.result_indicator.setStyleSheet("""
            font-size: 14px; 
            font-weight: bold; 
            padding: 5px 15px;
            border-radius: 5px;
            background-color: #ccc;
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
        self.info_label.setStyleSheet("color: #333; font-weight: bold;")
        
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
            self.result_indicator.setStyleSheet("""
                font-size: 14px; font-weight: bold; padding: 5px 15px;
                border-radius: 5px; background-color: #FF6B6B; color: white;
            """)
        elif warn_percent > 20:  # Mais de 20% warning
            self.result_indicator.setText("⚠️ ATENÇÃO")
            self.result_indicator.setStyleSheet("""
                font-size: 14px; font-weight: bold; padding: 5px 15px;
                border-radius: 5px; background-color: #FFE66D; color: #333;
            """)
        else:
            self.result_indicator.setText("✅ APROVADO")
            self.result_indicator.setStyleSheet("""
                font-size: 14px; font-weight: bold; padding: 5px 15px;
                border-radius: 5px; background-color: #4ECDC4; color: white;
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
        painter.fillRect(self.rect(), QColor(255, 255, 255))
        
        if not self.measurements:
            # Desenha mensagem quando não há dados
            painter.setPen(QColor(128, 128, 128))
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
        painter.setPen(QPen(QColor(200, 200, 200), 2))
        painter.setBrush(QBrush())  # Sem preenchimento
        painter.drawRect(QRectF(rect_x, rect_y, rect_width, rect_height))
        
        # Desenha grid de referência (opcional)
        painter.setPen(QPen(QColor(240, 240, 240), 1))
        
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
        painter.setPen(QPen(QColor(100, 100, 100), 2))
        painter.setBrush(QBrush(color))
        
        painter.drawEllipse(
            QPointF(canvas_x, canvas_y), 
            point_radius, point_radius
        )
        
        # Desenha texto com valor
        painter.setPen(QColor(0, 0, 0))
        painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        
        # Texto centralizado no círculo
        text = f"{tension:.1f}"
        text_rect = painter.fontMetrics().boundingRect(text)
        text_x = canvas_x - text_rect.width() / 2
        text_y = canvas_y + text_rect.height() / 4
        
        painter.drawText(QPointF(text_x, text_y), text)
        
        # Desenha coordenadas menores abaixo
        coord_text = f"({x:.1f},{y:.1f})"
        painter.setFont(QFont("Arial", 6))
        painter.setPen(QColor(80, 80, 80))
        
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
                return QColor(76, 205, 196)  # Verde-azulado (#4ECDC4)
            elif result == 'WARNING':
                return QColor(255, 230, 109)  # Amarelo (#FFE66D)
            else:  # NOK
                return QColor(255, 107, 107)  # Vermelho (#FF6B6B)
        
        # Fallback: gradiente baseado nos dados
        if tension_range == 0:
            return QColor(100, 200, 100)  # Verde padrão
            
        # Normaliza tensão (0-1)
        normalized = (tension - min_tension) / tension_range
        
        # Mapeia para cores: Verde (baixo) -> Amarelo (médio) -> Vermelho (alto)
        if normalized < 0.33:
            # Verde para amarelo
            ratio = normalized * 3
            return QColor(int(100 + 155 * ratio), 200, int(100 * (1 - ratio)))
        elif normalized < 0.66:
            # Amarelo para laranja
            ratio = (normalized - 0.33) * 3
            return QColor(255, int(200 - 50 * ratio), 0)
        else:
            # Laranja para vermelho
            ratio = (normalized - 0.66) * 3
            return QColor(255, int(150 * (1 - ratio)), 0)

class ImageViewerWidget(QWidget):
    """Widget para exibir imagens capturadas pela câmera"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        
        # Label para exibir a imagemgit
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setText("Nenhuma imagem capturada")
        self.image_label.setStyleSheet("border: 1px solid gray; background-color: #f0f0f0;")
        self.image_label.setMinimumSize(400, 300)
        
        # Informações da imagem
        self.info_label = QLabel("Informações da imagem:")
        
        self.layout.addWidget(self.image_label)
        self.layout.addWidget(self.info_label)
        
    def display_image(self, image, info_text=None):
        """Mostra uma imagem no widget"""
        if image is None:
            self.image_label.setText("Imagem inválida")
            return
            
        # Converte imagem OpenCV para QPixmap
        h, w, c = image.shape
        bytes_per_line = 3 * w
        q_img = QImage(image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(q_img)
        
        # Redimensiona se for muito grande
        if pixmap.width() > 800 or pixmap.height() > 600:
            pixmap = pixmap.scaled(800, 600, Qt.AspectRatioMode.KeepAspectRatio)
            
        self.image_label.setPixmap(pixmap)
        
        # Atualiza informações
        if info_text:
            self.info_label.setText(info_text)
        else:
            self.info_label.setText(f"Imagem: {w}x{h}px")

class PositionListWidget(QWidget):
    """Widget para gerenciar lista de posições"""
    position_selected = pyqtSignal(object)  # Emite a posição selecionada
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        
        # Título
        title_label = QLabel("Posições de Inspeção")
        title_font = QFont()
        title_font.setBold(True)
        title_label.setFont(title_font)
        
        # Lista de posições
        self.positions_list = QListWidget()
        self.positions_list.currentItemChanged.connect(self.on_position_selected)
        
        # Botões
        buttons_layout = QHBoxLayout()
        self.add_position_btn = QPushButton("Adicionar Posição Atual")
        self.remove_position_btn = QPushButton("Remover")
        buttons_layout.addWidget(self.add_position_btn)
        buttons_layout.addWidget(self.remove_position_btn)
        
        self.layout.addWidget(title_label)
        self.layout.addWidget(self.positions_list)
        self.layout.addLayout(buttons_layout)
        
        # Mapeia id(QListWidgetItem) ➜ InspectionPosition.
        # QListWidgetItem NÃO é hashable, portanto usamos id(item).
        self.positions: dict[int, InspectionPosition] = {}
        
    def add_position(self, position: InspectionPosition):
        """Adiciona uma posição à lista"""
        item_text = f"{position.name} ({position.x:.2f}, {position.y:.2f}, {getattr(position,'z',0.0):.2f})"
        item = QListWidgetItem(item_text)
        self.positions_list.addItem(item)
        self.positions[id(item)] = position
        
    def remove_selected_position(self):
        """Remove a posição selecionada"""
        current_item = self.positions_list.currentItem()
        if current_item:
            position = self.positions.pop(id(current_item))
            row = self.positions_list.row(current_item)
            self.positions_list.takeItem(row)
            return position
        return None
        
    def clear_positions(self):
        """Limpa todas as posições"""
        self.positions_list.clear()
        self.positions = {}
        
    def get_all_positions(self):
        """Retorna todas as posições"""
        return list(self.positions.values())
        
    def on_position_selected(self, current, previous):
        """Manipula evento de seleção de posição"""
        if current:
            pos = self.positions.get(id(current))
            if pos:
                self.position_selected.emit(pos)

class SequenceControlWidget(QWidget):
    """Widget para controlar a execução da sequência"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        
        # Grupo de sequência
        sequence_group = QGroupBox("Controle de Sequência")
        sequence_layout = QGridLayout()
        
        # Nome da sequência
        sequence_layout.addWidget(QLabel("Nome:"), 0, 0)
        self.sequence_name = QLineEdit("Sequência PCB")
        sequence_layout.addWidget(self.sequence_name, 0, 1)
        
        # Botões de controle
        self.create_sequence_btn = QPushButton("Criar Sequência")
        self.run_sequence_btn = QPushButton("Executar Sequência")
        self.stop_sequence_btn = QPushButton("Parar")
        self.stop_sequence_btn.setEnabled(False)
        
        sequence_layout.addWidget(self.create_sequence_btn, 1, 0)
        sequence_layout.addWidget(self.run_sequence_btn, 1, 1)
        sequence_layout.addWidget(self.stop_sequence_btn, 2, 0, 1, 2)
        
        # Status
        sequence_layout.addWidget(QLabel("Status:"), 3, 0)
        self.sequence_status = QLabel("Pronto")
        sequence_layout.addWidget(self.sequence_status, 3, 1)
        
        sequence_group.setLayout(sequence_layout)
        
        # Grupo de arquivo
        file_group = QGroupBox("Salvar/Carregar")
        file_layout = QVBoxLayout()
        self.save_btn = QPushButton("Salvar Programa (JSON)")
        self.load_btn = QPushButton("Carregar Programa (JSON)")
        self.save_gcode_btn = QPushButton("Exportar para G-CODE")
        self.load_gcode_btn = QPushButton("Importar de G-CODE")
        file_layout.addWidget(self.save_btn)
        file_layout.addWidget(self.load_btn)
        file_layout.addWidget(self.save_gcode_btn)
        file_layout.addWidget(self.load_gcode_btn)
        
        file_group.setLayout(file_layout)
        
        self.layout.addWidget(sequence_group)
        self.layout.addWidget(file_group)
        self.layout.addStretch()

class PositionRegistryWidget(QWidget):
    """Widget for showing registered positions"""
    def __init__(self, controller, cfg: AOIConfigManager, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.cfg        = cfg
        self.cfg        = cfg
        self.positions  = []
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Registered Positions")
        title_font = QFont()
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Registered positions table
        self.positions_table = QTableWidget(0, 3)
        self.positions_table.setHorizontalHeaderLabels(["Name", "X (mm)", "Y (mm)"])
        self.positions_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.positions_table)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.delete_button = QPushButton("Delete Selected")
        self.delete_button.clicked.connect(self.delete_position)
        
        self.create_sequence_btn = QPushButton("Create Sequence")
        
        buttons_layout.addWidget(self.delete_button)
        buttons_layout.addWidget(self.create_sequence_btn)
        
        layout.addLayout(buttons_layout)
        
    def add_position(self, name, x, y, z=0.0, image=None):
        """Add a position to the registry"""
        # Create position object
        position = {
            'name': name,
            'x': x,
            'y': y,
            'z': z,
            'image': image,
        }
        
        # Add to internal list
        self.positions.append(position)
        
        # Add to table
        row = self.positions_table.rowCount()
        self.positions_table.insertRow(row)
        self.positions_table.setItem(row, 0, QTableWidgetItem(name))
        self.positions_table.setItem(row, 1, QTableWidgetItem(f"{x:.3f}"))
        self.positions_table.setItem(row, 2, QTableWidgetItem(f"{y:.3f}"))
        
    def delete_position(self):
        """Delete selected position"""
        selected_rows = self.positions_table.selectedItems()
        if not selected_rows:
            return
            
        row = selected_rows[0].row()
        if row >= 0 and row < len(self.positions):
            del self.positions[row]
            self.positions_table.removeRow(row)
            
    def clear_positions(self):
        """Clear all positions"""
        self.positions.clear()
        while self.positions_table.rowCount() > 0:
            self.positions_table.removeRow(0)

class CameraPreviewWidget(QWidget):
    """Widget for displaying camera preview and capturing images"""
    image_captured = pyqtSignal(object, str)  # Emits the captured image and position name
    
    def __init__(self, controller, cfg: AOIConfigManager, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.cfg = cfg
        self.current_image = None
        self._last_frame_size = (640, 480)  # Tamanho do frame da câmera
        self.preview_timer = QTimer(self)
        self.preview_timer.timeout.connect(self.update_preview)
        
        # Inicializa conversor de FOV para clique no vídeo
        self._init_fov_converter()
        
        self.setup_ui()
    
    def _init_fov_converter(self):
        """Inicializa o conversor de coordenadas pixel→pulsos"""
        self.fov_converter = CameraFOVConverter()
        
        # Carrega calibração salva se existir
        fov_data = self.cfg.get("camera", "fov_calibration", default={})
        if fov_data:
            self.fov_converter.set_fov_calibration(FOVCalibration.from_dict(fov_data))
        
        # Carrega calibração de eixos
        pulses_per_mm = self.cfg.get("movement", "pulses_per_mm", default=100.0)
        self.fov_converter.set_axis_calibration("X", pulses_per_mm)
        self.fov_converter.set_axis_calibration("Y", pulses_per_mm)
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        # GroupBox para preview da câmera (inclui botões de controle)
        preview_group = QGroupBox("Camera Preview")
        preview_group.setMinimumHeight(450)
        pg_layout = QVBoxLayout(preview_group)

        # Área de visualização - usa ClickableVideoLabel para detectar cliques
        self.image_label = ClickableVideoLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setText("Camera Preview\n(Clique para mover a head)")
        self.image_label.setStyleSheet("border: 1px solid gray; background-color: #f0f0f0;")
        self.image_label.setMinimumSize(600, 450)
        self.image_label.clicked.connect(self._on_video_click)
        pg_layout.addWidget(self.image_label)

        # Checkbox para habilitar movimento por clique
        self.click_move_enabled = QCheckBox("Mover head ao clicar")
        self.click_move_enabled.setChecked(False)
        self.click_move_enabled.setToolTip("Quando ativado, clicar no vídeo move a head para centralizar o ponto clicado")
        pg_layout.addWidget(self.click_move_enabled)

        # Botões de preview dentro da mesma groupbox
        btn_layout = QHBoxLayout()
        self.start_preview_btn = QPushButton("Start Preview")
        self.start_preview_btn.clicked.connect(self.start_preview)
        self.stop_preview_btn = QPushButton("Stop Preview")
        self.stop_preview_btn.clicked.connect(self.stop_preview)
        self.stop_preview_btn.setEnabled(False)
        btn_layout.addWidget(self.start_preview_btn)
        btn_layout.addWidget(self.stop_preview_btn)
        pg_layout.addLayout(btn_layout)

        layout.addWidget(preview_group, 1)
    
    def _on_video_click(self, click_x: float, click_y: float):
        """
        Handler para clique no preview de vídeo.
        Move a head para centralizar o ponto clicado.
        """
        # Verifica se movimento por clique está habilitado
        if not self.click_move_enabled.isChecked():
            return
        
        # Verifica se CLP está conectado
        if not hasattr(self.controller, 'plc') or not self.controller.plc.connected:
            QMessageBox.warning(
                self, "CLP Não Conectado",
                "O CLP não está conectado. Conecte antes de usar movimento por clique."
            )
            return
        
        try:
            # Obtém posição Z atual para calibração correta
            z_current = self.controller.plc.current_positions.get('Z', 0)
            
            # Atualiza tamanho do frame no conversor
            self.fov_converter.set_frame_size(*self._last_frame_size)
            
            # Converte clique em movimento
            dx_pulses, dy_pulses = self.fov_converter.video_click_to_movement(
                click_x, click_y,
                self.image_label.width(),
                self.image_label.height(),
                z_current,
                axis_x="X", axis_y="Y",
                invert_y=getattr(self.window(), '_camera_mirror_y', False)
            )
            
            # Executa movimento se houver deslocamento significativo
            if abs(dx_pulses) > 5 or abs(dy_pulses) > 5:
                logger.info(f"Clique no vídeo: movendo ΔX={dx_pulses}, ΔY={dy_pulses} pulsos")
                
                if dx_pulses != 0:
                    self.controller.plc.move_relative('X', int(dx_pulses))
                if dy_pulses != 0:
                    self.controller.plc.move_relative('Y', int(dy_pulses))
            else:
                logger.debug(f"Clique muito próximo do centro, ignorado")
                
        except Exception as e:
            logger.error(f"Erro ao processar clique no vídeo: {e}")
            QMessageBox.warning(self, "Erro", f"Erro ao mover: {e}")
        
    def start_preview(self):
        """Start camera preview"""
        if not hasattr(self.controller.camera, 'is_connected') or not self.controller.camera.is_connected:
            QMessageBox.warning(self, "Error", "Camera not connected")
            return
        self.preview_timer.start(100)  # Update every 100ms
        self.start_preview_btn.setEnabled(False)
        self.stop_preview_btn.setEnabled(True)
        
    def stop_preview(self):
        """Stop camera preview"""
        self.preview_timer.stop()
        self.start_preview_btn.setEnabled(True)
        self.stop_preview_btn.setEnabled(False)
        
    def update_preview(self):
        """Update the camera preview"""
        try:
            image = self.controller.camera.capture()
            if image is not None:
                # Salva tamanho do frame para conversão de clique
                h, w = image.shape[:2]
                self._last_frame_size = (w, h)
                
                self.display_image(image)
                self.current_image = image
        except Exception as e:
            print(f"Error updating preview: {e}")
            self.stop_preview()
            
    def capture_image(self):
        """Capture an image and emit signal with position name"""
        if not hasattr(self.controller.camera, 'is_connected') or not self.controller.camera.is_connected:
            QMessageBox.warning(self, "Error", "Camera not connected")
            return
        position_name = self.position_name.text()
        if not position_name:
            QMessageBox.warning(self, "Error", "Please enter a position name")
            return
        try:
            image = self.controller.camera.capture()
            if image is not None:
                self.display_image(image)
                self.current_image = image
                self.image_captured.emit(image, position_name)
                self.position_name.clear()
            else:
                QMessageBox.warning(self, "Error", "Failed to capture image")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Capture error: {e}")
            
    def display_image(self, image):
        """Display an image in the preview area with a crosshair in the center"""
        if image is None:
            return
            
        # Criar uma cópia da imagem para não modificar a original
        display_img = image.copy()
        
        # Aplicar espelhamento se configurado na janela principal
        main_window = self.window()
        if hasattr(main_window, '_camera_mirror_x') and main_window._camera_mirror_x:
            display_img = cv2.flip(display_img, 1)  # Flip horizontal
        if hasattr(main_window, '_camera_mirror_y') and main_window._camera_mirror_y:
            display_img = cv2.flip(display_img, 0)  # Flip vertical
        
        # Desenhar a cruz vermelha no centro
        h, w = display_img.shape[:2]
        center_x, center_y = w // 2, h // 2
        
        # Parâmetros da cruz
        color = (0, 0, 255)  # Vermelho em BGR
        thickness = 2
        length = min(w, h) // 20  # 5% do tamanho da dimensão menor
        
        # Desenhar a cruz
        # Linha horizontal
        cv2.line(display_img, 
                (center_x - length, center_y), 
                (center_x + length, center_y), 
                color, thickness)
        # Linha vertical
        cv2.line(display_img, 
                (center_x, center_y - length), 
                (center_x, center_y + length), 
                color, thickness)
                
        # Converter a imagem OpenCV para QPixmap
        h, w = display_img.shape[:2]
        c = display_img.shape[2] if len(display_img.shape) == 3 else 1
        bytes_per_line = 3 * w
        q_img = QImage(display_img.data, w, h, bytes_per_line, QImage.Format.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(q_img)
        
        # Obter tamanho do widget de exibição
        label_width = self.image_label.width()
        label_height = self.image_label.height()
        
        # Redimensionar a imagem para caber no espaço disponível mantendo proporções
        pixmap = pixmap.scaled(label_width, label_height, 
                           Qt.AspectRatioMode.KeepAspectRatio, 
                           Qt.TransformationMode.SmoothTransformation)
                           
        self.image_label.setPixmap(pixmap)
        
    def resizeEvent(self, event):
        """Override do evento de redimensionamento para ajustar a imagem quando o widget for redimensionado"""
        super().resizeEvent(event)
        if self.current_image is not None:
            self.display_image(self.current_image)

class MovementControlWidget(QWidget):
    """Widget for controlling CNC movement (jog)"""
    def __init__(self, controller, cfg: AOIConfigManager, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.cfg        = cfg 
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Group box for movement controls
        movement_group = QGroupBox("Movement Controls")
        # Vertical size fixed to its contents (no stretch)
        movement_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        movement_layout = QGridLayout()
        
        # Directional control buttons
        self.up_button = QPushButton("↑")
        self.down_button = QPushButton("↓")
        self.left_button = QPushButton("←")
        self.right_button = QPushButton("→")
        
        # Style the buttons
        for btn in [self.up_button, self.down_button, self.left_button, self.right_button]:
            btn.setMinimumSize(50, 50)
            font = QFont()
            font.setBold(True)
            font.setPointSize(16)
            btn.setFont(font)
        
        # Connect press/release events for continuous movement
        self.up_button.pressed.connect(lambda: self._on_direction_press("Y",  -1))
        self.up_button.released.connect(self._on_direction_release)
        self.down_button.pressed.connect(lambda: self._on_direction_press("Y", 1))
        self.down_button.released.connect(self._on_direction_release)
        self.left_button.pressed.connect(lambda: self._on_direction_press("X", -1))
        self.left_button.released.connect(self._on_direction_release)
        self.right_button.pressed.connect(lambda: self._on_direction_press("X", 1))
        self.right_button.released.connect(self._on_direction_release)

        # --------- NOVOS BOTÕES Z -----------------
        self.z_up_button   = QPushButton("Z+")
        self.z_down_button = QPushButton("Z-")
        for zbtn in (self.z_up_button, self.z_down_button):
            zbtn.setMinimumSize(50, 30)
        self.z_up_button.pressed.connect(  lambda: self._on_direction_press("Z",  -1))
        self.z_up_button.released.connect(self._on_direction_release)
        self.z_down_button.pressed.connect(lambda: self._on_direction_press("Z", 1))
        self.z_down_button.released.connect(self._on_direction_release)
        
        # Add buttons to grid
        movement_layout.addWidget(self.up_button, 0, 1)
        movement_layout.addWidget(self.left_button, 1, 0)
        movement_layout.addWidget(self.right_button, 1, 2)
        movement_layout.addWidget(self.down_button, 2, 1)

        # Coloca Z+ acima de STOP e Z- abaixo
        movement_layout.addWidget(self.z_up_button,   0, 3)
        movement_layout.addWidget(self.z_down_button, 2, 3)

        # Botão de Emergency Stop / Reset
        self.emergency_stop_button = QPushButton("STOP")
        self.emergency_stop_button.setCheckable(True) # Torna o botão toggle
        self.emergency_stop_button.setMinimumSize(100, 40)
        font_stop = QFont()
        font_stop.setBold(True)
        self.emergency_stop_button.setFont(font_stop)
        # Estilo inicial (vermelho)
        self.emergency_stop_button.setStyleSheet("background-color: red; color: white;")
        self.emergency_stop_button.toggled.connect(self.on_emergency_stop_toggle) # Conecta ao handler

        # Adiciona o botão ao layout, centralizado abaixo dos direcionais
        movement_layout.addWidget(self.emergency_stop_button, 1, 1, Qt.AlignmentFlag.AlignCenter) # Coloca no centro (linha 1, coluna 1)
        
        # Step size and feed rate controls
        step_layout = QHBoxLayout()
        step_layout.addWidget(QLabel("Step Size:"))
        # ---------- STEP SIZE ---------------
        default_step = self.cfg.get("movement", "step_size", default=10.0)
        self.step_size = QLineEdit(f"{default_step}")
        # ▸ VALIDAÇÃO numérica (>=0)
        self.step_size.setValidator(QDoubleValidator(0.0001, 100000.0, 4, self))
        step_layout.addWidget(self.step_size)
        step_layout.addWidget(QLabel("mm"))
        
        feed_layout = QHBoxLayout()
        feed_layout.addWidget(QLabel("Feed Rate:"))

        # ---------- FEED RATE ---------------
        default_feed = self.cfg.get("movement", "feed_rate", default=1000.0)
        self.feed_rate = QLineEdit(f"{default_feed}")
        # ▸ feed entre 1 e 30000 mm/min
        self.feed_rate.setValidator(QDoubleValidator(1.0, 30000.0, 0, self))
        feed_layout.addWidget(self.feed_rate)
        feed_layout.addWidget(QLabel("mm/min"))
        
        # Add step and feed rate controls
        movement_layout.addLayout(step_layout, 3, 0, 1, 3)
        movement_layout.addLayout(feed_layout, 4, 0, 1, 3)

        # ---- grava no JSON quando o usuário termina de editar -----
        self.step_size.editingFinished.connect(self._save_step_feed)
        self.feed_rate.editingFinished.connect(self._save_step_feed)

        self.go_to_zero_btn = QPushButton("Go to Zero")
        self.go_to_zero_btn.clicked.connect(self.go_to_zero)
        self.go_to_zero_btn.setMinimumHeight(40)  # Altura mínima para facilitar o clique
        font = QFont()
        font.setBold(True)
        self.go_to_zero_btn.setFont(font)
        movement_layout.addWidget(self.go_to_zero_btn, 6, 0, 1, 3)  # Posiciona abaixo dos controles existentes

        # Botão para deslocar a head para posição de trabalho definida pelo usuário (WPos)
        self.go_to_position_btn = QPushButton("Go to Position")
        self.go_to_position_btn.setToolTip("Ir para posição de trabalho específica (WPos)")
        self.go_to_position_btn.clicked.connect(self.show_go_to_dialog)
        movement_layout.addWidget(self.go_to_position_btn, 7, 0, 1, 3)

        # Checkbox "Enable Keyboard Control" agora na linha 8 (posição anterior do Test Motor Hold)
        self.keyboard_control_checkbox = QCheckBox("Enable Keyboard Control")
        self.keyboard_control_checkbox.setChecked(False)
        movement_layout.addWidget(self.keyboard_control_checkbox, 8, 0, 1, 3)
        
        # ========== BOTÃO DE BACKLIGHT ==========
        # Controla a iluminação inferior (Y0.7) para inspeção de stencil
        self.backlight_button = QPushButton("💡 Backlight OFF")
        self.backlight_button.setCheckable(True)
        self.backlight_button.setMinimumHeight(35)
        self.backlight_button.setStyleSheet("""
            QPushButton { background-color: #444; color: white; border-radius: 5px; }
            QPushButton:checked { background-color: #FFD700; color: black; font-weight: bold; }
        """)
        self.backlight_button.toggled.connect(self._on_backlight_toggle)
        movement_layout.addWidget(self.backlight_button, 9, 0, 1, 4)  # Ocupa toda a largura
        
        # Movement mode (G90/G91)
        mode_layout = QHBoxLayout()
        self.mode_absolute = QPushButton("Passo")
        self.mode_absolute.setCheckable(True)
        self.mode_absolute.clicked.connect(lambda: self.set_motion_mode("G90"))
        
        self.mode_relative = QPushButton("Contínuo")
        self.mode_relative.setCheckable(True)
        self.mode_relative.setChecked(True)  # Default to relative mode
        self.mode_relative.clicked.connect(lambda: self.set_motion_mode("G91"))
        
        mode_layout.addWidget(self.mode_absolute)
        mode_layout.addWidget(self.mode_relative)
        movement_layout.addLayout(mode_layout, 5, 0, 1, 3)
        
        movement_group.setLayout(movement_layout)
        layout.addWidget(movement_group)
        # Keep the groupbox at top without stretching
        layout.setAlignment(movement_group, Qt.AlignmentFlag.AlignTop)

    def _save_step_feed(self):
        try:
            step = float(self.step_size.text())
            feed = float(self.feed_rate.text())
            self.cfg.remember_step_feed(step, feed)
        except ValueError:
            # silencioso – validação já existe
            return
    
    def _on_backlight_toggle(self, checked: bool):
        """
        Controla o backlight (iluminação inferior do stencil).
        Liga/desliga a saída Y0.7 do CLP.
        """
        if not hasattr(self.controller, 'cnc') or not self.controller.cnc.is_connected:
            # Bloqueia sinais para evitar loop infinito ao reverter o estado
            self.backlight_button.blockSignals(True)
            self.backlight_button.setChecked(not checked)
            self.backlight_button.blockSignals(False)
            QMessageBox.warning(self, "Erro", "CLP não conectado")
            return
        
        # Verifica se o controlador tem suporte a backlight
        if not hasattr(self.controller.cnc, 'backlight_set'):
            self.backlight_button.blockSignals(True)
            self.backlight_button.setChecked(not checked)
            self.backlight_button.blockSignals(False)
            QMessageBox.warning(self, "Erro", "Controlador não suporta backlight")
            return
        
        # Aciona o backlight
        success = self.controller.cnc.backlight_set(checked)
        
        if success:
            if checked:
                self.backlight_button.setText("💡 Backlight ON")
                logger.info("ILUMINAÇÃO: Backlight ligado (Y0.7 = HIGH)")
            else:
                self.backlight_button.setText("💡 Backlight OFF")
                logger.info("ILUMINAÇÃO: Backlight desligado (Y0.7 = LOW)")
        else:
            # Bloqueia sinais para evitar loop infinito ao reverter o estado
            self.backlight_button.blockSignals(True)
            self.backlight_button.setChecked(not checked)
            self.backlight_button.blockSignals(False)
            QMessageBox.warning(self, "Erro", "Falha ao controlar backlight")
        
    def _on_direction_press(self, axis: str, direction: int):
        """
        Chamada quando o usuário pressiona um botão (ou tecla).
        Decide entre STEP ou JOG e delega ao GRBLCNCController.
        """
        if not self._precheck_connected():
            return

        feed = self._get_feed_rate()
        step = self._get_step_size()
        if feed is None or step is None:
            return
        
        # --- grava imediatamente no JSON ---
        self.cfg.remember_step_feed(step, feed)

        # “Passo-a-passo” = botão G90 selecionado  ➜  usa step_move
        if self.mode_absolute.isChecked():
            self.controller.cnc.step_move(axis, step * direction, feed)
        # “Contínuo” = G91 selecionado  ➜  jog
        else:
            self.controller.cnc.jog_start(axis, direction, feed)

    def _on_direction_release(self):
        """Interrompe jog se estivermos em modo contínuo."""
        if not self._precheck_connected():
            return
        if self.mode_relative.isChecked():      # só há jog se G91
            self.controller.cnc.jog_stop()

    def start_movement(self, axis: str, direction: int):
        """
        Mantido apenas para chamadas vindas de eventFilter (atalhos de
        teclado). Encaminha para _on_direction_press.
        """
        self._on_direction_press(axis, direction)

    def _get_feed_rate(self) -> float | None:
        """Lê o feed-rate; devolve None e avisa em caso de erro."""
        try:
            val = float(self.feed_rate.text())

            if self.controller.cnc.is_connected:
                max_lim = max(self.controller.cnc.max_feed.values())
                if val > max_lim + 1e-3:
                    resp = QMessageBox.question(
                        self, "Feed acima do limite",
                        (f"O valor F={val:.0f} mm/min excede o limite atual "
                         f"(≤ {max_lim:.0f}).\n\n"
                         "Deseja atualizar $110 e $111 para permitir essa "
                         "velocidade em X e Y?"),
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    if resp == QMessageBox.StandardButton.Yes:
                        # novo limite com folga de 10 %
                        new_lim = int(val * 1.1)                 # 10 % de folga
                        new_acc = int((new_lim / 60) * 5)        # ≈5 s para atingir Vmáx

                        cmds = [
                            f"$110={new_lim}", f"$111={new_lim}",
                            f"$120={new_acc}", f"$121={new_acc}"
                        ]
                        for c in cmds:
                            self.controller.cnc.send_command(c, priority=True)

                        # actualiza cache interno
                        self.controller.cnc.max_feed['x'] = new_lim
                        self.controller.cnc.max_feed['y'] = new_lim
                        self.controller.cnc.max_acc ['x'] = new_acc
                        self.controller.cnc.max_acc ['y'] = new_acc
                        # desabilita avisos futuros de clamp
                        self.controller.cnc._feed_clamp_warned = True
                        QMessageBox.information(
                            self, "Limites actualizados",
                            (f"Feed-máx X/Y = {new_lim} mm/min\n"
                             f"Aceleração X/Y = {new_acc} mm/s²")
                        )
                    else:
                        # clampará ao valor máximo existente
                        QMessageBox.information(self, "Feed ajustado",
                                                f"A velocidade será limitada a {max_lim} mm/min.")
                        val = max_lim
            return val
        except ValueError:
            QMessageBox.warning(self, "Erro", "Feed-rate inválido")
            return None

    def _get_step_size(self) -> float | None:
        """Lê o step-size; devolve None e avisa em caso de erro."""
        try:
            return float(self.step_size.text())
        except ValueError:
            QMessageBox.warning(self, "Erro", "Step size inválido")
            return None

    def _precheck_connected(self) -> bool:
        if not self.controller.cnc.is_connected:
            QMessageBox.warning(self, "Erro", "CNC não conectada")
            return False
        return True

    def go_to_zero(self):
        """
        Dispara homing no CLP: envia pulso de 100 ms em cada coil de sensor:
          - M1350 → eixo X
          - M850  → eixo Y
          - M185  → eixo Z
        """
        if not self._precheck_connected():
            return
        # PLC backend → pulso de 100 ms em cada coil de homing
        if isinstance(self.controller.cnc, PLCAxisController):
            status = self.controller.cnc.machine_status
            if status in ("Run", "Jog", "Alarm"):
                QMessageBox.warning(self, "Aviso", f"Máquina ocupada ({status})")
                return
            # Endereços dos coils de homing
            homing_coils = {
                'X': 1350,  # M1350_X
                'Y': 850,   # M850_Y
                'Z': 1850    # M185_Z
            }
            for axis, coil in homing_coils.items():
                try:
                    # sobe borda
                    self.controller.cnc.client.write_coil(coil, True)
                    time.sleep(0.1)
                    # desce borda
                    self.controller.cnc.client.write_coil(coil, False)
                except Exception as e:
                    logger.error(f"Homing CLP: falha no pulso de {axis} (coil {coil}): {e}")
            # aguarda término de todos os eixos
            self.controller.cnc.wait_for_idle()
            # atualiza interface
            self.window().update_position_display()
            self.window().statusBar().showMessage("Homing CLP concluído")
            return
        # GRBL or other → fallback ao “go to zero” por movimento absoluto
        # evita travar se já em movimento/alarm
        status = self.controller.cnc.machine_status
        if status in ("Run", "Jog", "Alarm"):
            QMessageBox.warning(self, "Aviso", f"Máquina ocupada ({status})")
            return
        feed = self._get_feed_rate()
        if feed is None:
            return
        self._start_move_thread(x=0, y=0, z=0, feed=feed,
                                status_msg="Movendo para posição zero")
    
    def get_current_feed_rate(self):
        """Método público para outras classes acessarem a velocidade configurada"""
        try:
            return float(self.feed_rate.text())
        except ValueError:
            return 1000.0  # fallback

    def stop_movement(self):
        self._on_direction_release()

    def show_go_to_dialog(self):
        """Exibe diálogo para coletar coordenadas de destino (WPos)."""
        from PyQt6.QtWidgets import QDialog, QLabel, QLineEdit, QHBoxLayout, QPushButton, QMessageBox
        from PyQt6.QtGui import QDoubleValidator

        dialog = QDialog(self)
        dialog.setWindowTitle("Go to Position")
        dialog.setModal(True)
        layout = QGridLayout(dialog)

        # Captura a posição de trabalho atual (WPos) para pré‑preencher os campos
        try:
            current = self.controller.cnc.get_current_position()
        except Exception:
            current = {'x': 0.0, 'y': 0.0}

        layout.addWidget(QLabel("X (mm):"), 0, 0)
        x_input = QLineEdit()
        x_input.setValidator(QDoubleValidator(-10000.0, 10000.0, 4, x_input))
        x_input.setText(f"{current.get('x', 0.0):.3f}")
        layout.addWidget(x_input, 0, 1)

        layout.addWidget(QLabel("Y (mm):"), 1, 0)
        y_input = QLineEdit()
        y_input.setValidator(QDoubleValidator(-10000.0, 10000.0, 4, y_input))
        y_input.setText(f"{current.get('y', 0.0):.3f}")
        layout.addWidget(y_input, 1, 1)

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout, 2, 0, 1, 2)

        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                x = float(x_input.text())
                y = float(y_input.text())
                self.go_to_position(x, y)
            except ValueError:
                QMessageBox.warning(self, "Erro", "Valores inválidos para X ou Y")

    def go_to_position(self, x, y):
        """Realiza movimento para a posição absoluta de trabalho (WPos)."""
        from PyQt6.QtWidgets import QMessageBox
        from PyQt6.QtCore import QTimer

        # 1. Verifica se há conexão
        if not self.controller.cnc.is_connected:
            QMessageBox.warning(self, "Erro", "CNC não conectada")
            return

        # 2. Verifica se a máquina está livre
        status = self.controller.cnc.machine_status
        if status in ("Alarm", "Run", "Jog"):
            QMessageBox.warning(self, "Aviso", f"Máquina ocupada ({status})")
            return

        # 3. Guarda modo de distância atual (G90 ou G91)
        prev_mode = "G90" if self.mode_absolute.isChecked() else "G91"

        # 4. Obtém feed rate
        try:
            feed_rate = float(self.feed_rate.text())
        except:
            feed_rate = 1000

        # 5. Deslocamento assíncrono
        self._start_move_thread(x, y, feed_rate,
                                status_msg=f"Movendo para X:{x:.3f}, Y:{y:.3f}")

    def _start_move_thread(self, x=None, y=None, z=None,
                           feed=1000, status_msg="Movendo…"):
        stbar = self.window().statusBar()
        stbar.showMessage(status_msg)

        self._move_thread = MoveTaskThread(
                                self.controller.cnc, x, y, z, feed
                            )

        def _on_done(xx, yy, zz):
            stbar.showMessage(f"Head em X:{xx:.3f}, Y:{yy:.3f}, Z:{zz:.3f}")
            # força atualização UI
            QTimer.singleShot(50, self.window().update_position_display)

        def _on_err(msg):
            QMessageBox.critical(self, "Erro", msg)
            stbar.showMessage("Falha no deslocamento")

        self._move_thread.finished.connect(_on_done)
        self._move_thread.error.connect(_on_err)
        self._move_thread.start()

    def _execute_resume_and_update(self):
        """Executa o resumo após parada e força atualização de posição em sequência"""
        try:
            # Primeiro envia o comando para retomar após hold
            self.controller.cnc.grbl.send_immediately("~")
            logger.debug("MOVIMENTO: Enviado comando de retomada (~)")

            # --- INÍCIO DA MODIFICAÇÃO ---
            # REMOVIDO: Chamada para _force_position_update. A atualização agora
            # dependerá do polling regular iniciado em connect_cnc.
            # QTimer.singleShot(150, lambda: self._force_position_update(1))
            logger.debug("MOVIMENTO: Atualização de posição dependerá do polling regular.")
            # --- FIM DA MODIFICAÇÃO ---

        except Exception as e:
            logger.error(f"MOVIMENTO: Erro ao executar sequência de retomada: {e}")
            
    # A função _force_position_update pode ser mantida, mas não será mais chamada
    # a partir de _execute_resume_and_update.
    def _force_position_update(self, attempt=1):
        """Força múltiplas atualizações de posição para garantir precisão

        Args:
            attempt: Número da tentativa atual (para limitar tentativas)
        """
        if not hasattr(self.controller.cnc, 'grbl') or not self.controller.cnc.is_connected:
            return

        try:
            # Envia comando de status para obter posição atualizada
            # --- INÍCIO DA MODIFICAÇÃO ---
            # logger.debug(f"MOVIMENTO: Forçando atualização de posição - tentativa {attempt}") # REMOVIDO/COMENTADO
            # --- FIM DA MODIFICAÇÃO ---
            self.controller.cnc.grbl.send_immediately("?")

            # Se ainda estamos dentro do limite de tentativas, agenda outra verificação
            if attempt < 3:
                # Aumento progressivo do tempo entre tentativas (150ms, 200ms, 250ms)
                delay = 150 + (attempt * 50)
                # A chamada recursiva ainda existe, mas o log dentro dela foi removido
                QTimer.singleShot(delay, lambda: self._force_position_update(attempt + 1))

        except Exception as e:
            # Manter o log de erro
            logger.error(f"MOVIMENTO: Erro ao forçar atualização de posição: {e}")
            
    def set_motion_mode(self, mode):
        """Set the motion mode (G90/G91)"""
        # Se for PLC, não existe GRBL: apenas atualiza UI e guarda modo internamente
        
        if isinstance(self.controller.cnc, PLCAxisController):
            if mode == "G90":
                self.mode_absolute.setChecked(True)
                self.mode_relative.setChecked(False)
            else:
                self.mode_absolute.setChecked(False)
                self.mode_relative.setChecked(True)
            # opcional: armazenar no controller para referência futura
            self.controller.cnc.current_motion_mode = mode
            logger.info(f"MOVIMENTO (PLC): modo de movimento definido para {mode}")
            return

        # Se não estiver conectado (nem PLC, nem GRBL), só atualiza UI e volta
        if not self.controller.cnc.is_connected:
            if mode == "G90":
                self.mode_absolute.setChecked(True)
                self.mode_relative.setChecked(False)
            else:
                self.mode_absolute.setChecked(False)
                self.mode_relative.setChecked(True)
            logger.warning(f"MOVIMENTO: CNC não conectada, modo {mode} definido apenas na UI.")
            return

        # Atualiza a UI (GRBL)
        if mode == "G90":
            self.mode_absolute.setChecked(True)
            self.mode_relative.setChecked(False)
        else:  # G91
            self.mode_absolute.setChecked(False)
            self.mode_relative.setChecked(True)
        # Envia o comando G90/G91 para o GRBL
        try:
            logger.debug(f"MOVIMENTO: Definindo modo de movimento para {mode}")
            self.controller.cnc.grbl.send_immediately(mode)
        except Exception as e:
            logger.error(f"MOVIMENTO: Erro ao definir modo de movimento: {e}")
            QMessageBox.warning(self, "Error", f"Error setting motion mode: {e}")

    def on_emergency_stop_toggle(self, checked):
        """
        Manipula o clique no botão Emergency Stop/Reset.
        """
        if not hasattr(self.controller.cnc, 'is_connected') or not self.controller.cnc.is_connected:
            QMessageBox.warning(self, "Erro", "CNC não conectada")
            self.emergency_stop_button.setChecked(not checked)
            return
            
        if checked:
            # Botão foi pressionado para entrar no modo RESET
            logger.info("EMERGENCY STOP: Botão pressionado. Enviando Soft Reset.")
            if self.controller.cnc.send_soft_reset():
                # Configura visual do botão para Reset
                self.emergency_stop_button.setText("Reset")
                self.emergency_stop_button.setStyleSheet("background-color: orange; color: black;")
                
                # Atualiza status
                main_window = self.window()
                if hasattr(main_window, 'statusBar'):
                    main_window.statusBar().showMessage("Máquina parada. Clique em Reset para desbloquear.")
            else:
                # Soft reset falhou, reverte o botão
                logger.error("EMERGENCY STOP: Falha ao enviar Soft Reset")
                QMessageBox.critical(self, "Erro", "Falha ao enviar comando de parada")
                self.emergency_stop_button.setChecked(False)
        else:
            # Botão foi pressionado para sair do modo RESET
            logger.info("RESET: Botão pressionado para desbloquear. Enviando $X.")
            if self.controller.cnc.unlock():
                # Configura visual do botão para STOP
                self.emergency_stop_button.setText("STOP")
                self.emergency_stop_button.setStyleSheet("background-color: red; color: white;")
                
                # Atualiza status
                main_window = self.window()
                if hasattr(main_window, 'statusBar'):
                    main_window.statusBar().showMessage("Máquina desbloqueada e pronta.")
                    
                # Solicita atualização de status para verificar nova condição
                QTimer.singleShot(200, lambda: self.controller.cnc.grbl.send_immediately("?"))
            else:
                # Desbloqueio falhou, reverte o botão
                logger.error("RESET: Falha ao enviar comando de desbloqueio")
                QMessageBox.critical(self, "Erro", "Falha ao desbloquear a máquina")
                self.emergency_stop_button.setChecked(True)

    def _auto_unlock_after_reset(self):
        """Executa sequência automática de desbloqueio após reset de emergência"""
        logger.info("AUTO UNLOCK: Iniciando sequência de desbloqueio automático após reset")
        
        try:
            # 1. Envia comando de desbloqueio
            self.controller.cnc.grbl.send_immediately("$X")
            logger.info("AUTO UNLOCK: Comando $X enviado")
            
            # 2. Pequena pausa
            QTimer.singleShot(200, lambda: self._check_if_unlocked())
        except Exception as e:
            logger.error(f"AUTO UNLOCK: Erro ao enviar comando de desbloqueio: {e}")
            main_window = self.window()
            if hasattr(main_window, 'statusBar'):
                main_window.statusBar().showMessage(f"Erro no desbloqueio automático: {e}")

    def _check_if_unlocked(self):
        """Verifica se o desbloqueio foi bem-sucedido e restaura configurações se necessário"""
        try:
            # Solicita status para conferir se saiu do alarme
            self.controller.cnc.grbl.send_immediately("?")
            
            # Exibe mensagem de sucesso
            main_window = self.window()
            if hasattr(main_window, 'statusBar'):
                main_window.statusBar().showMessage("Sistema parado e desbloqueado automaticamente.")
                
            logger.info("AUTO UNLOCK: Sequência de desbloqueio automático concluída")
        except Exception as e:
            logger.error(f"AUTO UNLOCK: Erro ao verificar status após desbloqueio: {e}")

@dataclass
class MapParams:
    origin: dict
    end: dict
    step_x: float
    step_y: float
    folder: str
    program_name: str


class _PreviewSuspender:
    """
    Context-manager que pausa o preview da câmera e garante reativação
    mesmo em caso de exceções.
    """
    def __init__(self, preview_widget):
        self.preview_widget = preview_widget
        self.was_running   = preview_widget and preview_widget.preview_timer.isActive()

    def __enter__(self):
        if self.was_running:
            self.preview_widget.stop_preview()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.was_running:
            self.preview_widget.start_preview()

class AOIControllerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Controle de Inspeção Óptica Automatizada")
        self.setGeometry(100, 100, 1200, 800)
        
        # Carrega configurações do usuário
        self.config = AOIConfigManager()
        
        # Inicializa o controlador AOI usando CLP (Modbus TCP),
        # mas sem conectar automaticamente (conexão será tentada depois)
        plc_host = self.config.get("connections", "plc_host", default="192.168.0.5")
        plc_port = self.config.get("connections", "plc_port", default=502)
        # Inicializa o controlador com PLC mas sem conectar automaticamente
        logger.debug("Inicializando CNCAOIController com PLCAxisController (sem conexão automática)")
        self.controller = CNCAOIController(
            plc_host=plc_host,
            plc_port=plc_port,
            auto_connect=False  # Não conecta automaticamente - permite que a app inicie sem CLP
        )
        logger.debug("CNCAOIController inicializado; backend = %s",
                     type(self.controller.cnc).__name__)
        self.current_sequence = None
        self.is_running_sequence = False
        
        # =========== SISTEMA DE RECEITAS ===========
        from aoi_lib.recipe_manager import RecipeManager
        self.recipe_manager = RecipeManager()
        self.current_recipe = None  # Receita atualmente carregada
        logger.info(f"RecipeManager inicializado. Diretório: {self.recipe_manager.recipes_dir}")
        
        # =========== SISTEMA DE RASTREABILIDADE ===========
        self.stencil_tracker = StencilTracker()  # Usa diretório padrão: data/stencils
        self.current_stencil = None  # Stencil atualmente selecionado
        logger.info(f"StencilTracker inicializado. Diretório: {self.stencil_tracker.data_dir}")
        
        # =========== SISTEMA DE RELATÓRIOS ===========
        self._init_report_generator()
        
        # Variável para armazenar o último valor de posição (para comparação)
        self.last_logged_position = None

        # Armazenar o offset do sistema de coordenadas de trabalho (WCS) ativo (ex: G54)
        self.current_wcs_offset = {'x': 0.0, 'y': 0.0, 'z': 0.0} # Inicializa o offset WCS padrão (G54)

        # Armazenar a última Posição da Máquina (MPos) conhecida
        self.current_mpos = {'x': 0.0, 'y': 0.0, 'z': 0.0} 
        # Armazenar o Sistema de Coordenadas de Trabalho (WCS) ativo (ex: "G54")
        self.active_wcs = "G54" # Assume G54 como padrão inicial
        # Mapeamento de WCS para número P do G10
        self.wcs_to_p = {"G54": 1, "G55": 2, "G56": 3, "G57": 4, "G58": 5, "G59": 6}
        
        # -------- Carrega configurações de câmera salvas --------
        self._camera_mirror_x = self.config.get("camera", "mirror_x", default=False)
        self._camera_mirror_y = self.config.get("camera", "mirror_y", default=False)
        logger.debug(f"Configurações de câmera carregadas: mirror_x={self._camera_mirror_x}, mirror_y={self._camera_mirror_y}")
        
        # Configuração da interface
        self.setup_ui()
        # Configuração do menu
        self.setup_menu()

        # -------- Painel de conexão inicialmente oculto -------
        self.connection_group.setVisible(False)

        # -------- Auto-connect se preferido --------------------
        
        logger.debug(
            "Verificando conexão PLC no arranque; backend=%s, conectado=%s",
            type(self.controller.cnc).__name__,
            getattr(self.controller.cnc, 'is_connected', False)
        )
        if isinstance(self.controller.cnc, PLCAxisController):
            # Estado inicial - aguardando tentativa de conexão automática
            self.connect_cnc_btn.setText("Conectar PLC")
            self.cnc_status.setText("Iniciando...")
            self.statusBar().showMessage("Iniciando aplicação - conexão automática ao PLC em breve...")
            logger.info("Aplicação iniciada. Tentativa de conexão automática ao PLC agendada.")
        
        # Auto-connect apenas após a interface estar pronta
        QTimer.singleShot(500, self._attempt_auto_connect)

        # Timer para atualizar a posição – agora conectamos a um método que loga a ação 
        self.update_timer = QTimer(self) 
        self.update_timer.timeout.connect(self.on_update_timer) 
        self.update_timer.start(1000) # Atualiza a cada 1000ms        

        # Capturar eventos de teclado para movimentação de qualquer widget:
        # instala o filter globalmente apenas UMA vez
        QApplication.instance().installEventFilter(self)

        # chama cleanup se o Qt encerrar por outros caminhos
        QApplication.instance().aboutToQuit.connect(self._cleanup_resources)

    #   Auto-connect com base no JSON de prefs
    def _attempt_auto_connect(self):
        """Tenta conexão automática ao PLC e câmera ao iniciar a aplicação."""
        
        # ========== CONEXÃO AUTOMÁTICA AO PLC ==========
        if isinstance(self.controller.cnc, PLCAxisController):
            plc = self.controller.cnc
            plc_host = plc.host
            plc_port = plc.port
            
            self.statusBar().showMessage(f"Tentando conexão automática ao PLC em {plc_host}:{plc_port}...")
            QApplication.processEvents()  # Atualiza a UI
            
            logger.info(f"Iniciando conexão automática ao PLC em {plc_host}:{plc_port}")
            
            try:
                # Tenta conectar usando o controller existente
                plc.connect()
                
                # Atualiza UI
                self.connect_cnc_btn.setText("Desconectar PLC")
                self.cnc_status.setText("Conectado")
                self.statusBar().showMessage(f"✅ PLC conectado automaticamente em {plc_host}:{plc_port}")
                logger.info(f"PLC conectado automaticamente com sucesso em {plc_host}:{plc_port}")
                
            except Exception as e:
                # Conexão falhou - exibe mensagem para o usuário
                error_msg = str(e)
                self.connect_cnc_btn.setText("Conectar PLC")
                self.cnc_status.setText("Desconectado")
                self.statusBar().showMessage(f"⚠️ CLP não conectado - A aplicação funcionará sem controle de movimento")
                logger.warning(f"Falha na conexão automática ao PLC em {plc_host}:{plc_port}: {e}")
                
                # Exibe mensagem informativa (não-bloqueante)
                QTimer.singleShot(1000, lambda: self._show_plc_connection_error(plc_host, plc_port, error_msg))
        
        # ========== CONEXÃO AUTOMÁTICA À CÂMERA ==========
        if self.config.get("connections", "auto_connect_camera", default=False):
            cam_id = int(self.config.get("connections", "last_camera_id", default=0))
            idx = self.camera_id_combo.findText(str(cam_id))
            if idx >= 0:
                self.camera_id_combo.setCurrentIndex(idx)
            QTimer.singleShot(500, self.connect_camera)

    def _show_plc_connection_error(self, host: str, port: int, error: str):
        """Exibe mensagem de erro de conexão ao PLC."""
        QMessageBox.information(
            self,
            "CLP Não Conectado",
            f"O CLP (Controlador Lógico Programável) não está conectado.\n\n"
            f"A aplicação iniciará normalmente, porém as funções de controle de movimento "
            f"estarão indisponíveis até que o CLP seja conectado.\n\n"
            f"Detalhes da tentativa de conexão:\n"
            f"• Endereço: {host}:{port}\n"
            f"• Erro: {error}\n\n"
            f"Para conectar o CLP:\n"
            f"1. Verifique se o CLP está ligado e na mesma rede\n"
            f"2. Confirme o endereço IP em 'Ferramentas → Preferências'\n"
            f"3. Use 'Ferramentas → Conexões' para conectar manualmente"
        )

    def eventFilter(self, source, event):
        """
        Intercepta eventos de teclado e dispara start/stop de movimento
        se a opção estiver habilitada.
        """
        # KeyPress
        if event.type() == QEvent.Type.KeyPress and self.movement_widget.keyboard_control_checkbox.isChecked():
            if hasattr(event, 'isAutoRepeat') and event.isAutoRepeat():
                return True
            key = event.key()
            if key == Qt.Key.Key_Up:
                self.movement_widget.start_movement("Y", -1)
                return True
            elif key == Qt.Key.Key_Down:
                self.movement_widget.start_movement("Y", 1)
                return True
            elif key == Qt.Key.Key_Left:
                self.movement_widget.start_movement("X", -1)
                return True
            elif key == Qt.Key.Key_Right:
                self.movement_widget.start_movement("X", 1)
                return True
            elif key == Qt.Key.Key_PageUp:
                 self.movement_widget.start_movement("Z", -1)
                 return True
            elif key == Qt.Key.Key_PageDown:
                 self.movement_widget.start_movement("Z", 1)
                 return True
        # KeyRelease
        elif event.type() == QEvent.Type.KeyRelease and self.movement_widget.keyboard_control_checkbox.isChecked():
            if hasattr(event, 'isAutoRepeat') and event.isAutoRepeat():
                return True
            key = event.key()
            if key in (
                Qt.Key.Key_Up, 
                Qt.Key.Key_Down, 
                Qt.Key.Key_Left, 
                Qt.Key.Key_Right,
                Qt.Key.Key_PageUp,
                Qt.Key.Key_PageDown
            ):
                self.movement_widget.stop_movement()
                return True
        return super().eventFilter(source, event)

    def on_update_timer(self):
        #logger.debug("Timer fired: atualizando tela de posição da head.")
        self.update_position_display()
        
    def setup_ui(self):
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        
        # Grupo de conexão (oculto por padrão; mostrado via menu)
        self.connection_group = QGroupBox("Conexão")
        connection_layout = QGridLayout()
        
        # CNC Connection
        connection_layout.addWidget(QLabel("Porta CNC:"), 0, 0)
        self.cnc_port_combo = QComboBox()
        self.refresh_ports()
        connection_layout.addWidget(self.cnc_port_combo, 0, 1)
        
        self.connect_cnc_btn = QPushButton("Conectar CNC")
        self.connect_cnc_btn.clicked.connect(self.connect_cnc)
        connection_layout.addWidget(self.connect_cnc_btn, 0, 2)
        
        # Camera connection
        connection_layout.addWidget(QLabel("Câmera ID:"), 1, 0)
        self.camera_id_combo = QComboBox()
        self.camera_id_combo.addItems(["0", "1", "2", "3"])
        connection_layout.addWidget(self.camera_id_combo, 1, 1)
        
        self.connect_camera_btn = QPushButton("Conectar Câmera")
        self.connect_camera_btn.clicked.connect(self.connect_camera)
        connection_layout.addWidget(self.connect_camera_btn, 1, 2)
        
        # Refresh ports button
        self.refresh_ports_btn = QPushButton("Atualizar Portas")
        self.refresh_ports_btn.clicked.connect(self.refresh_ports)
        connection_layout.addWidget(self.refresh_ports_btn, 0, 3)
        
        # Test camera button
        self.test_camera_btn = QPushButton("Testar Câmera")
        self.test_camera_btn.clicked.connect(self.test_camera)
        connection_layout.addWidget(self.test_camera_btn, 1, 3)
        
        self.connection_group.setLayout(connection_layout)
        main_layout.addWidget(self.connection_group)

        # Grupo de Calibração de Movimento ------
        calibration_group = QGroupBox("Calibração de Movimento")
        calibration_layout = QHBoxLayout()

        # Campos permanecem criados porque são usados pela
        # lógica de calibração, porém o grupo ficará oculto.
        self.pulses_input = QLineEdit(str(
            self.config.get("calibration", "pulses_per_rev", default=400)
        ))
        self.fuso_input = QLineEdit(str(
            self.config.get("calibration", "fuso_pitch", default=5)
        ))
        self.apply_calibration_btn = QPushButton("Aplicar Calibração")
        self.apply_calibration_btn.clicked.connect(self.apply_calibration)

        # (os widgets não são adicionados ao layout visual)
        calibration_group.setLayout(calibration_layout)
        calibration_group.setVisible(False)       # ← esconde
        main_layout.addWidget(calibration_group)  # mantém no DOM para uso interno
        
        # Splitter para dividir a interface em painéis
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Painel esquerdo: controles e lista de posições
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Informações de posição
        position_group = QGroupBox("Posição Atual")
        position_layout = QGridLayout()

        # Exibe os valores X, Y, Z e status
        position_layout.addWidget(QLabel("X:"), 0, 0)
        self.x_position = QLabel("0.000 mm")
        position_layout.addWidget(self.x_position, 0, 1)
        position_layout.addWidget(QLabel("Y:"), 1, 0)
        self.y_position = QLabel("0.000 mm")
        position_layout.addWidget(self.y_position, 1, 1)
        position_layout.addWidget(QLabel("Z:"), 2, 0)
        self.z_position = QLabel("0.000 mm")
        position_layout.addWidget(self.z_position, 2, 1)
        position_layout.addWidget(QLabel("Status:"), 3, 0)
        self.cnc_status = QLabel("Desconectado")
        position_layout.addWidget(self.cnc_status, 3, 1)

        position_group.setLayout(position_layout)
        left_layout.addWidget(position_group)
        
        # Widget de lista de posições
        self.position_list_widget = PositionListWidget()
        self.position_list_widget.add_position_btn.clicked.connect(self.add_current_position)
        self.position_list_widget.remove_position_btn.clicked.connect(self.remove_position)
        self.position_list_widget.position_selected.connect(self.on_position_selected)
        
        left_layout.addWidget(self.position_list_widget)
        
        # Controle de sequência
        self.sequence_widget = SequenceControlWidget()
        self.sequence_widget.create_sequence_btn.clicked.connect(self.create_sequence)
        self.sequence_widget.run_sequence_btn.clicked.connect(self.run_sequence)
        self.sequence_widget.stop_sequence_btn.clicked.connect(self.stop_sequence)
        self.sequence_widget.save_btn.clicked.connect(self.save_program)
        self.sequence_widget.load_btn.clicked.connect(self.load_program)
        self.sequence_widget.save_gcode_btn.clicked.connect(self.save_gcode)
        self.sequence_widget.load_gcode_btn.clicked.connect(self.load_gcode)
        
        left_layout.addWidget(self.sequence_widget)

        # Table to display each step/result of the executed sequence
        self.results_table = QTableWidget(0, 3)
        self.results_table.setHorizontalHeaderLabels(["Posição", "Horário", "Status"])
        # Make columns stretch to fill available space
        self.results_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        left_layout.addWidget(self.results_table)
        
        # Painel direito: aba para Câmera & Movimento e Visualização de Tensão
        right_panel = QTabWidget()
        # guardamos para habilitar/desabilitar abas depois
        self.right_panel = right_panel
        
        # MOVER PARA AQUI: Adicionar a aba de Câmera & Movimento (após definir right_panel)
        # Tab para Camera & Movement
        camera_movement_tab = QWidget()
        camera_movement_layout = QHBoxLayout(camera_movement_tab)
        
        # Left side: controls and position registry
        cm_left_panel = QWidget()
        cm_left_layout = QVBoxLayout(cm_left_panel)
        
        # Movement controls 
        self.movement_widget = MovementControlWidget(self.controller, self.config)
        cm_left_layout.addWidget(self.movement_widget)
        
        # Right side: camera preview
        self.camera_preview = CameraPreviewWidget(self.controller, self.config)
        self.camera_preview.image_captured.connect(self.on_image_captured)
        
        # Inverter colunas: preview à esquerda (mais espaço) e controles à direita
        camera_movement_layout.addWidget(self.camera_preview, 3)      # Proporção 3 (preview)
        camera_movement_layout.addWidget(cm_left_panel, 1)            # Proporção 1 (controles)
        
        # Agora é seguro adicionar a nova aba ao right_panel que já foi definido
        right_panel.addTab(camera_movement_tab, "Câmera & Movimento")

        # Aba de Visualização de Tensão
        self.tension_visualization = TensionVisualizationWidget()
        right_panel.addTab(self.tension_visualization, "Visualização de Tensão")
        
        # ================== ABA DE RASTREABILIDADE ==================
        stencil_tab = QWidget()
        stencil_layout = QVBoxLayout(stencil_tab)
        
        # Widget de identificação de stencil
        self.stencil_identification = StencilIdentificationWidget(
            self.stencil_tracker, 
            parent=self
        )
        # Conecta sinais
        self.stencil_identification.stencil_selected.connect(self._on_stencil_selected)
        self.stencil_identification.stencil_cleared.connect(self._on_stencil_cleared)
        self.stencil_identification.recipe_requested.connect(self._on_recipe_requested)
        
        stencil_layout.addWidget(self.stencil_identification)
        
        # Botões de ação rápida
        action_group = QGroupBox("⚡ Ações Rápidas")
        action_layout = QHBoxLayout(action_group)
        
        self.btn_run_tension = QPushButton("📐 Medir Tensão")
        self.btn_run_tension.setEnabled(False)
        self.btn_run_tension.clicked.connect(self._run_tension_measurement)
        self.btn_run_tension.setToolTip("Executa medição de tensão e salva no histórico do stencil")
        action_layout.addWidget(self.btn_run_tension)
        
        self.btn_manage_stencils = QPushButton("📋 Gerenciar Stencils")
        self.btn_manage_stencils.clicked.connect(self.show_stencil_manager)
        action_layout.addWidget(self.btn_manage_stencils)
        
        self.btn_new_stencil = QPushButton("➕ Novo Stencil")
        self.btn_new_stencil.clicked.connect(self.show_new_stencil_dialog)
        action_layout.addWidget(self.btn_new_stencil)
        
        stencil_layout.addWidget(action_group)
        
        # Espaço para futuras expansões (inspeção visual, etc.)
        stencil_layout.addStretch()
        
        right_panel.addTab(stencil_tab, "🏷️ Rastreabilidade")
        
        # ===================================================================
        # NOTA: As abas ficam habilitadas mesmo sem CLP conectado
        # O bloqueio agora é feito apenas nas ações que requerem movimento
        # (ex: _precheck_connected, _on_generate_map, etc.)
        # Isso permite usar câmera, receitas e visualização sem CLP
        # ===================================================================
        
        # Adiciona painéis ao splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(self.right_panel)
        splitter.setSizes([400, 800])
        
        main_layout.addWidget(splitter)
        
        # Barra de status
        self.statusBar().showMessage("Pronto para conectar")

    def setup_menu(self):
        """Configura o menu da aplicação"""
        menubar = self.menuBar()
        
        # Menu de Arquivo
        file_menu = menubar.addMenu('&Arquivo')
        
        exit_action = QAction('Sair', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # =========== MENU DE RECEITAS ===========
        recipes_menu = menubar.addMenu('&Receitas')
        
        # Gerenciador de Receitas
        manage_recipes_action = QAction('📋 Gerenciar Receitas...', self)
        manage_recipes_action.setShortcut('Ctrl+R')
        manage_recipes_action.triggered.connect(self.show_recipe_manager)
        recipes_menu.addAction(manage_recipes_action)
        
        # Nova Receita
        new_recipe_action = QAction('➕ Nova Receita...', self)
        new_recipe_action.triggered.connect(self.show_new_recipe_dialog)
        recipes_menu.addAction(new_recipe_action)
        
        recipes_menu.addSeparator()
        
        # Receita Atual
        self.current_recipe_action = QAction('(Nenhuma receita carregada)', self)
        self.current_recipe_action.setEnabled(False)
        recipes_menu.addAction(self.current_recipe_action)
        
        # Aplicar à Captura
        apply_to_capture_action = QAction('🔄 Aplicar Receita à Captura', self)
        apply_to_capture_action.triggered.connect(self.apply_recipe_to_capture)
        recipes_menu.addAction(apply_to_capture_action)
        
        # Aplicar à Tensão
        apply_to_tension_action = QAction('🔄 Aplicar Receita à Tensão', self)
        apply_to_tension_action.triggered.connect(self.apply_recipe_to_tension)
        recipes_menu.addAction(apply_to_tension_action)
        
        # =========== MENU DE STENCILS ===========
        stencils_menu = menubar.addMenu('&Stencils')
        
        # Gerenciador de Stencils
        manage_stencils_action = QAction('📋 Gerenciar Stencils...', self)
        manage_stencils_action.setShortcut('Ctrl+T')
        manage_stencils_action.triggered.connect(self.show_stencil_manager)
        stencils_menu.addAction(manage_stencils_action)
        
        # Novo Stencil
        new_stencil_action = QAction('➕ Novo Stencil...', self)
        new_stencil_action.triggered.connect(self.show_new_stencil_dialog)
        stencils_menu.addAction(new_stencil_action)
        
        stencils_menu.addSeparator()
        
        # Stencil Atual
        self.current_stencil_action = QAction('(Nenhum stencil selecionado)', self)
        self.current_stencil_action.setEnabled(False)
        stencils_menu.addAction(self.current_stencil_action)
        
        # =========== MENU DE RELATÓRIOS ===========
        reports_menu = menubar.addMenu('&Relatórios')
        
        # Gerar Relatório de Tensão
        tension_report_action = QAction('📄 Relatório de Tensão...', self)
        tension_report_action.setShortcut('Ctrl+P')
        tension_report_action.setToolTip('Gera relatório PDF da última medição de tensão')
        tension_report_action.triggered.connect(self.show_tension_report_dialog)
        reports_menu.addAction(tension_report_action)
        
        # Relatório do Stencil
        stencil_report_action = QAction('📋 Relatório do Stencil...', self)
        stencil_report_action.setToolTip('Gera relatório PDF do histórico do stencil selecionado')
        stencil_report_action.triggered.connect(self.show_stencil_report_dialog)
        reports_menu.addAction(stencil_report_action)
        
        reports_menu.addSeparator()
        
        # Consultar por Período
        period_report_action = QAction('📅 Consultar por Período...', self)
        period_report_action.triggered.connect(self.show_period_query_dialog)
        reports_menu.addAction(period_report_action)
        
        reports_menu.addSeparator()
        
        # Configurações de Relatório
        report_settings_action = QAction('⚙️ Configurações de Relatório...', self)
        report_settings_action.triggered.connect(self.show_report_settings)
        reports_menu.addAction(report_settings_action)
        
        # Menu de Ferramentas
        tools_menu = menubar.addMenu('&Ferramentas')

        # ação para definir mapa
        definir_mapa_action = QAction('Definir Mapa', self)
        definir_mapa_action.triggered.connect(self.show_definir_mapa_dialog)
        tools_menu.addAction(definir_mapa_action)

        # Ação para abrir o Mosaic Builder
        mosaic_action = QAction('Montar Mosaico de Imagens', self)
        mosaic_action.triggered.connect(self.show_mosaic_builder)
        tools_menu.addAction(mosaic_action)

        tools_menu.addSeparator()
        
        calibration_action = QAction('Calibração CNC', self)
        calibration_action.triggered.connect(self.show_calibration_dialog)
        tools_menu.addAction(calibration_action)

        # Calibração de Câmera (correção de distorção)
        camera_calib_action = QAction('Calibração de Câmera (Distorção)', self)
        camera_calib_action.triggered.connect(self.show_camera_calibration_dialog)
        tools_menu.addAction(camera_calib_action)

        # Configurações de Câmera
        camera_settings_action = QAction('Configurações de Câmera', self)
        camera_settings_action.triggered.connect(self.show_camera_settings_dialog)
        tools_menu.addAction(camera_settings_action)

        # Calibração de Campo de Visão (FOV) - para movimento por clique
        fov_calib_action = QAction('📐 Calibração de FOV (Campo de Visão)', self)
        fov_calib_action.setToolTip('Configura a relação pixel↔mm para movimento por clique no vídeo')
        fov_calib_action.triggered.connect(self.show_fov_calibration_dialog)
        tools_menu.addAction(fov_calib_action)

        # Alinhamento de Fiduciais (para inspeção visual)
        fiducial_action = QAction('🎯 Alinhamento de Fiduciais', self)
        fiducial_action.setToolTip('Abre ferramenta de alinhamento Gerber ↔ Imagem usando fiduciais')
        fiducial_action.setShortcut('Ctrl+F')
        fiducial_action.triggered.connect(self.show_fiducial_alignment_dialog)
        tools_menu.addAction(fiducial_action)

        tools_menu.addSeparator()

        # Preferências
        pref_action = QAction('Preferências', self)
        pref_action.setShortcut('Ctrl+,')
        pref_action.triggered.connect(self.show_settings_dialog)
        tools_menu.addAction(pref_action)

        # ---------------------------------------------------------------
        # Item de menu "Tensão do Stencil" – abre o diálogo de medição
        # ---------------------------------------------------------------
        tension_action = QAction('Tensão do Stencil', self)
        tension_action.triggered.connect(self.open_stencil_tension_dialog)
        menubar.addAction(tension_action)

        # --------  painel de conexões -----------------
        conn_panel = QAction('Conexões…', self)
        conn_panel.setCheckable(True)
        conn_panel.setChecked(False)
        conn_panel.triggered.connect(
            lambda checked: self.connection_group.setVisible(checked)
        )
        tools_menu.addAction(conn_panel)
        
        # Menu de Ajuda
        help_menu = menubar.addMenu('&Ajuda')
        
        about_action = QAction('Sobre', self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

    # abre o diálogo de medição de tensão
    def open_stencil_tension_dialog(self):
        if not self.controller.cnc.is_connected:
            QMessageBox.warning(self, "Aviso", "Conecte a CNC antes de medir a tensão do stencil.")
            return
        dlg = StencilTensionDialog(self, self.controller.cnc)
        dlg.exec()

    # =========================================================================
    # GERENCIAMENTO DE RECEITAS
    # =========================================================================
    
    def show_recipe_manager(self):
        """Abre o diálogo de gerenciamento de receitas."""
        from aoi_lib.recipe_dialog import RecipeManagerDialog
        
        dialog = RecipeManagerDialog(self.recipe_manager, self)
        dialog.recipe_loaded.connect(self._on_recipe_loaded)
        dialog.exec()
    
    def show_new_recipe_dialog(self):
        """Abre o diálogo para criar uma nova receita."""
        from aoi_lib.recipe_dialog import RecipeEditorDialog
        from aoi_lib.recipe_manager import Recipe
        
        dialog = RecipeEditorDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            recipe = dialog.recipe
            if self.recipe_manager.save_recipe(recipe):
                QMessageBox.information(
                    self, "Sucesso",
                    f"Receita '{recipe.name}' criada com sucesso!\n\n"
                    "Acesse Receitas > Gerenciar Receitas para carregar."
                )
    
    def _on_recipe_loaded(self, recipe):
        """Callback quando uma receita é carregada."""
        self.current_recipe = recipe
        self.recipe_manager.set_current_recipe(recipe)
        
        # Atualiza o menu
        if hasattr(self, 'current_recipe_action'):
            self.current_recipe_action.setText(f"📋 {recipe.name}")
            self.current_recipe_action.setEnabled(True)
        
        # Mostra na barra de status
        self.statusBar().showMessage(f"Receita carregada: {recipe.name}")
        logger.info(f"Receita carregada: {recipe.name} ({recipe.recipe_id})")
    
    def apply_recipe_to_capture(self):
        """Aplica as configurações de captura da receita atual ao diálogo de mapa."""
        if self.current_recipe is None:
            QMessageBox.warning(
                self, "Aviso",
                "Nenhuma receita carregada.\n\n"
                "Acesse Receitas > Gerenciar Receitas e carregue uma receita."
            )
            return
        
        r = self.current_recipe
        
        # Verifica se os atributos de mapa existem
        if not hasattr(self, 'map_origin'):
            self.map_origin = {}
        if not hasattr(self, 'map_end'):
            self.map_end = {}
        
        # Aplica configurações de captura
        self.map_origin = {'x': r.capture.origin.x, 'y': r.capture.origin.y}
        self.map_end = {'x': r.capture.end.x, 'y': r.capture.end.y}
        
        # Tenta atualizar os widgets se existirem
        if hasattr(self, 'step_x_spin'):
            self.step_x_spin.setValue(r.capture.step_x)
        if hasattr(self, 'step_y_spin'):
            self.step_y_spin.setValue(r.capture.step_y)
        if hasattr(self, 'spin_capture_delay'):
            self.spin_capture_delay.setValue(r.capture.capture_delay_ms)
        
        QMessageBox.information(
            self, "Receita Aplicada",
            f"Configurações de captura aplicadas:\n\n"
            f"• Origem: ({r.capture.origin.x}, {r.capture.origin.y})\n"
            f"• Final: ({r.capture.end.x}, {r.capture.end.y})\n"
            f"• Step X: {r.capture.step_x} mm\n"
            f"• Step Y: {r.capture.step_y} mm\n"
            f"• Delay: {r.capture.capture_delay_ms} ms\n"
            f"• Backlight: {'Sim' if r.capture.backlight_enabled else 'Não'}\n\n"
            "Abra 'Definir Mapa' para verificar ou ajustar."
        )
        logger.info(f"Configurações de captura da receita '{r.name}' aplicadas")
    
    def apply_recipe_to_tension(self):
        """Aplica as configurações de tensão da receita atual ao diálogo de medição."""
        if self.current_recipe is None:
            QMessageBox.warning(
                self, "Aviso",
                "Nenhuma receita carregada.\n\n"
                "Acesse Receitas > Gerenciar Receitas e carregue uma receita."
            )
            return
        
        r = self.current_recipe
        
        if not r.tension.enabled:
            QMessageBox.information(
                self, "Aviso",
                f"A medição de tensão está desabilitada nesta receita.\n\n"
                "Edite a receita para habilitar."
            )
            return
        
        # Mostra informações dos critérios de aceitação
        acc = r.tension.acceptance
        QMessageBox.information(
            self, "Receita de Tensão",
            f"Configurações de tensão da receita '{r.name}':\n\n"
            f"📐 Grid: {r.tension.grid_rows} x {r.tension.grid_cols}\n"
            f"📍 Área: ({r.tension.start_point.x}, {r.tension.start_point.y}) → "
            f"({r.tension.end_point.x}, {r.tension.end_point.y})\n\n"
            f"📊 Critérios de Aceitação:\n"
            f"  • Mínimo: {acc.min_tension} N/cm²\n"
            f"  • Máximo: {acc.max_tension} N/cm²\n"
            f"  • Warning baixo: {acc.warning_low} N/cm²\n"
            f"  • Warning alto: {acc.warning_high} N/cm²\n\n"
            "ℹ️ Estes critérios serão usados para classificar as medições."
        )
        logger.info(f"Configurações de tensão da receita '{r.name}' exibidas")

    # =========================================================================
    # GERENCIAMENTO DE STENCILS (RASTREABILIDADE)
    # =========================================================================
    
    def _on_stencil_selected(self, stencil: Stencil):
        """Handler quando um stencil é selecionado."""
        self.current_stencil = stencil
        self.btn_run_tension.setEnabled(True)
        
        # Atualiza barra de status
        self.statusBar().showMessage(
            f"Stencil selecionado: {stencil.code} | "
            f"Receita: {stencil.recipe_name or 'Nenhuma'} | "
            f"Inspeções: {stencil.inspection_count}"
        )
        
        # Atualiza menu
        self.current_stencil_action.setText(f"Stencil: {stencil.code}")
        
        logger.info(f"Stencil selecionado: {stencil.code}")
    
    def _on_stencil_cleared(self):
        """Handler quando a seleção de stencil é limpa."""
        self.current_stencil = None
        self.btn_run_tension.setEnabled(False)
        self.statusBar().showMessage("Pronto")
        
        # Atualiza menu
        self.current_stencil_action.setText("(Nenhum stencil selecionado)")
        
        logger.info("Seleção de stencil limpa")
    
    def _on_recipe_requested(self, recipe_name: str):
        """Handler quando o stencil solicita carregamento de receita."""
        recipe = self.recipe_manager.load_recipe(recipe_name)
        if recipe:
            self._on_recipe_loaded(recipe)
            logger.info(f"Receita '{recipe_name}' carregada automaticamente para stencil")
        else:
            logger.warning(f"Receita '{recipe_name}' não encontrada")
    
    def show_stencil_manager(self):
        """Abre o diálogo de gerenciamento de stencils."""
        dialog = StencilManagerDialog(self.stencil_tracker, self)
        dialog.exec()
    
    def show_new_stencil_dialog(self):
        """Abre o diálogo para criar um novo stencil."""
        dialog = StencilCreateDialog(self.stencil_tracker, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            stencil = dialog.get_created_stencil()
            if stencil:
                QMessageBox.information(
                    self, "Sucesso",
                    f"Stencil '{stencil.code}' cadastrado com sucesso!\n\n"
                    "Escaneie ou digite o código para selecioná-lo."
                )
    
    def _run_tension_measurement(self):
        """Executa medição de tensão para o stencil selecionado."""
        if not self.current_stencil:
            QMessageBox.warning(
                self, "Stencil Não Selecionado",
                "Selecione um stencil antes de medir a tensão."
            )
            return
        
        if not self.controller.cnc.is_connected:
            QMessageBox.warning(
                self, "CLP Não Conectado",
                "Conecte o CLP antes de medir a tensão."
            )
            return
        
        # Abre diálogo de medição de tensão
        dlg = StencilTensionDialog(self, self.controller.cnc)
        
        # Se houver receita, pré-configura o diálogo
        if self.current_recipe and self.current_recipe.tension.enabled:
            # TODO: Passar parâmetros da receita para o diálogo
            pass
        
        result = dlg.exec()
        
        # Se medição foi concluída, salva no histórico
        if result == QDialog.DialogCode.Accepted:
            self._save_tension_to_history(dlg)
    
    def _save_tension_to_history(self, tension_dialog):
        """
        Salva resultado da medição de tensão no histórico do stencil.
        
        Args:
            tension_dialog: Diálogo de tensão com os dados da medição
        """
        if not self.current_stencil:
            return
        
        try:
            # Tenta obter dados da medição do diálogo ou do último arquivo salvo
            measurements_file = "stencil_tension_measurements.json"
            
            if os.path.exists(measurements_file):
                with open(measurements_file, "r", encoding="utf-8") as f:
                    tension_data = json.load(f)
                
                # Cria registro de tensão
                record = TensionRecord.from_tension_data(
                    tension_data,
                    recipe_name=self.current_recipe.name if self.current_recipe else None,
                    operator=None  # TODO: Implementar campo de operador
                )
                
                # Salva no histórico
                self.stencil_tracker.add_tension_record(
                    self.current_stencil.code, 
                    record
                )
                
                # Verifica alerta de degradação
                if self.current_recipe and self.current_recipe.tension.acceptance:
                    alert = self.stencil_tracker.check_degradation_alert(
                        self.current_stencil.code,
                        warning_low=self.current_recipe.tension.acceptance.warning_low
                    )
                    if alert:
                        QMessageBox.warning(
                            self, "⚠️ Alerta de Degradação",
                            f"Stencil: {self.current_stencil.code}\n\n{alert}"
                        )
                
                logger.info(
                    f"Medição de tensão salva no histórico do stencil "
                    f"'{self.current_stencil.code}': {record.result}"
                )
                
                QMessageBox.information(
                    self, "Medição Salva",
                    f"Resultado da medição salvo no histórico.\n\n"
                    f"Stencil: {self.current_stencil.code}\n"
                    f"Resultado: {record.result}\n"
                    f"Média: {record.average_tension:.2f} N/cm²"
                )
                
                # Atualiza widget de identificação para refletir nova inspeção
                stencil = self.stencil_tracker.get_stencil(self.current_stencil.code)
                if stencil:
                    self.stencil_identification._select_stencil(stencil)
            else:
                logger.warning("Arquivo de medições não encontrado")
                
        except Exception as e:
            logger.error(f"Erro ao salvar medição no histórico: {e}")
            QMessageBox.warning(
                self, "Erro",
                f"Erro ao salvar no histórico:\n{str(e)}"
            )

    def show_mosaic_builder(self):
        """Abre a janela do Mosaic Builder para montagem de imagens"""
        from mosaic_builder import MosaicBuilder
        self.mosaic_window = MosaicBuilder()
        self.mosaic_window.resize(1200, 900)
        self.mosaic_window.show()

    def show_camera_calibration_dialog(self):
        """Abre diálogo para calibração de câmera (correção de distorção)"""
        if not hasattr(self.controller.camera, 'is_connected') or not self.controller.camera.is_connected:
            QMessageBox.warning(self, "Aviso", "Conecte a câmera antes de calibrar.")
            return
        
        from camera_calibration import CameraCalibrationDialog
        self.camera_calib_dialog = CameraCalibrationDialog(self.controller.camera, self)
        self.camera_calib_dialog.resize(900, 750)
        self.camera_calib_dialog.show()

    def show_fov_calibration_dialog(self):
        """
        Abre diálogo para calibração de Campo de Visão (FOV).
        
        Esta calibração define a relação entre pixels da câmera e dimensões físicas (mm)
        em diferentes alturas Z, permitindo conversão precisa de clique no vídeo para
        movimento da head.
        """
        # Cria adaptador para o ConfigManager para usar o formato esperado pelo diálogo
        class ConfigAdapter:
            def __init__(self, cfg):
                self._cfg = cfg
            
            def get_config(self, key, default=None):
                if key == "camera_fov":
                    return self._cfg.get("camera", "fov_calibration", default=default or {})
                return default
            
            def set_config(self, key, value):
                if key == "camera_fov":
                    self._cfg.set("camera", "fov_calibration", value)
                    self._cfg.save()
        
        adapter = ConfigAdapter(self.config)
        
        dialog = FOVCalibrationDialog(adapter, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Atualiza o conversor FOV do CameraPreviewWidget
            if hasattr(self, 'camera_preview') and hasattr(self.camera_preview, 'fov_converter'):
                fov = dialog.get_calibration()
                self.camera_preview.fov_converter.set_fov_calibration(fov)
                logger.info(f"Calibração de FOV atualizada: {fov}")
            
            QMessageBox.information(
                self, "Calibração Salva",
                "A calibração de campo de visão foi salva.\n\n"
                "Agora você pode usar o clique no vídeo para mover a head\n"
                "com precisão baseada na altura Z atual."
            )

    def show_fiducial_alignment_dialog(self):
        """
        Abre diálogo para alinhamento de fiduciais.
        
        Esta ferramenta permite:
        - Carregar arquivo Gerber e detectar fiduciais automaticamente
        - Capturar templates de fiduciais da câmera ou mosaico
        - Calcular transformação (translação, rotação, escala) para alinhar
        - Ajuste fino manual da transformação
        """
        dialog = QDialog(self)
        dialog.setWindowTitle("🎯 Alinhamento de Fiduciais")
        dialog.setMinimumSize(1000, 700)
        dialog.resize(1200, 800)
        
        layout = QVBoxLayout(dialog)
        
        # Widget principal de alinhamento
        alignment_widget = FiducialAlignmentWidget()
        layout.addWidget(alignment_widget)
        
        # Se temos um mosaico recente, usar como imagem base
        mosaic_path = self.config.get("mosaic", "last_output_path", default=None)
        if mosaic_path and os.path.exists(mosaic_path):
            try:
                import cv2
                img = cv2.imread(mosaic_path)
                if img is not None:
                    alignment_widget.set_image(img)
                    logger.info(f"Mosaico carregado para alinhamento: {mosaic_path}")
            except Exception as e:
                logger.warning(f"Erro ao carregar mosaico: {e}")
        
        # Callback para captura de frame da câmera
        def get_camera_frame():
            if hasattr(self, 'camera_preview') and self.controller.camera.is_connected:
                frame = self.controller.camera.get_frame()
                return frame
            return None
        
        alignment_widget.set_frame_callback(get_camera_frame)
        
        # Conectar sinais
        def on_alignment_complete(transform):
            logger.info(f"Alinhamento calculado: tx={transform.tx:.1f}, ty={transform.ty:.1f}, "
                       f"angle={transform.angle:.2f}°, scale={transform.scale_x:.4f}")
            
            # Salvar transformação nas configurações
            self.config.set("fiducial_alignment", "last_tx", transform.tx)
            self.config.set("fiducial_alignment", "last_ty", transform.ty)
            self.config.set("fiducial_alignment", "last_angle", transform.angle)
            self.config.set("fiducial_alignment", "last_scale", transform.scale_x)
            self.config.save()
            
            QMessageBox.information(
                dialog, "Alinhamento Aplicado",
                f"Transformação calculada:\n\n"
                f"📍 Translação: ({transform.tx:.1f}, {transform.ty:.1f}) px\n"
                f"🔄 Rotação: {transform.angle:.2f}°\n"
                f"📐 Escala: {transform.scale_x:.4f}\n\n"
                f"Os valores foram salvos nas configurações."
            )
            dialog.accept()
        
        def on_alignment_cancelled():
            dialog.reject()
        
        alignment_widget.alignmentComplete.connect(on_alignment_complete)
        alignment_widget.alignmentCancelled.connect(on_alignment_cancelled)
        
        # Botões de arquivo para carregar imagem
        btn_layout = QHBoxLayout()
        
        btn_load_image = QPushButton("📷 Carregar Imagem/Mosaico")
        def load_image():
            filepath, _ = QFileDialog.getOpenFileName(
                dialog, "Carregar Imagem",
                "", "Imagens (*.png *.jpg *.bmp *.tiff);;All Files (*)"
            )
            if filepath:
                img = cv2.imread(filepath)
                if img is not None:
                    alignment_widget.set_image(img)
                    logger.info(f"Imagem carregada: {filepath}")
        btn_load_image.clicked.connect(load_image)
        btn_layout.addWidget(btn_load_image)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        dialog.exec()

    # =========================================================================
    #  SISTEMA DE RELATÓRIOS
    # =========================================================================
    
    def _init_report_generator(self):
        """Inicializa o gerador de relatórios com configurações salvas."""
        # Carregar configuração de relatórios
        report_config_data = self.config.get("reports", "config", default=None)
        
        if report_config_data:
            try:
                self.report_config = ReportConfig.from_dict(report_config_data)
                logger.info("Configuração de relatórios carregada")
            except Exception as e:
                logger.warning(f"Erro ao carregar config de relatórios: {e}")
                self.report_config = ReportConfig()
        else:
            self.report_config = ReportConfig()
        
        self.report_generator = ReportGenerator(self.report_config)
        logger.info(f"ReportGenerator inicializado. Diretório: {self.report_config.output_dir}")
    
    def show_report_settings(self):
        """Abre diálogo de configurações de relatório."""
        dialog = ReportSettingsDialog(self.report_config, self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.report_config = dialog.get_config()
            self.report_generator = ReportGenerator(self.report_config)
            
            # Salvar configuração
            self.config.set("reports", "config", self.report_config.to_dict())
            self.config.save()
            
            logger.info("Configuração de relatórios atualizada e salva")
            self.statusBar().showMessage("Configurações de relatório salvas", 3000)
    
    def show_tension_report_dialog(self):
        """Gera relatório de tensão da última medição."""
        # Tentar carregar última medição
        tension_file = Path("stencil_tension_measurements.json")
        
        if not tension_file.exists():
            QMessageBox.warning(
                self, "Sem Dados",
                "Nenhuma medição de tensão disponível.\n\n"
                "Execute uma medição de tensão primeiro."
            )
            return
        
        try:
            with open(tension_file, 'r', encoding='utf-8') as f:
                tension_data = json.load(f)
            
            # Obter informações do stencil atual
            stencil_code = None
            stencil_desc = None
            if self.current_stencil:
                stencil_code = self.current_stencil.code
                stencil_desc = self.current_stencil.description
            
            # Obter nome da receita
            recipe_name = None
            if self.current_recipe:
                recipe_name = self.current_recipe.get('name')
            
            # Gerar relatório
            output_path = self.report_generator.generate_tension_report(
                tension_data=tension_data,
                stencil_code=stencil_code,
                stencil_description=stencil_desc,
                recipe_name=recipe_name,
                operator=None  # TODO: Implementar campo de operador
            )
            
            # Perguntar se quer abrir o PDF
            reply = QMessageBox.question(
                self, "Relatório Gerado",
                f"Relatório gerado com sucesso:\n{output_path}\n\n"
                f"Deseja abrir o arquivo?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                import subprocess
                subprocess.Popen([output_path], shell=True)
                
        except Exception as e:
            logger.exception("Erro ao gerar relatório de tensão")
            QMessageBox.critical(
                self, "Erro",
                f"Erro ao gerar relatório:\n{str(e)}"
            )
    
    def show_stencil_report_dialog(self):
        """Gera relatório de histórico do stencil selecionado."""
        if not self.current_stencil:
            QMessageBox.warning(
                self, "Stencil Não Selecionado",
                "Selecione um stencil primeiro usando a aba de Rastreabilidade."
            )
            return
        
        try:
            # Obter histórico do stencil
            history = self.stencil_tracker.get_tension_history(self.current_stencil.code)
            
            if not history:
                QMessageBox.warning(
                    self, "Sem Histórico",
                    f"O stencil {self.current_stencil.code} não possui histórico de medições."
                )
                return
            
            # Converter Stencil para dict
            from dataclasses import asdict
            stencil_dict = asdict(self.current_stencil)
            
            # Converter TensionRecords para dicts
            history_dicts = []
            for record in history:
                if hasattr(record, '__dict__'):
                    history_dicts.append(record.__dict__ if not hasattr(record, 'to_dict') else record.to_dict())
                else:
                    history_dicts.append(record)
            
            # Gerar relatório
            output_path = self.report_generator.generate_stencil_history_report(
                stencil=stencil_dict,
                history=history_dicts
            )
            
            # Perguntar se quer abrir
            reply = QMessageBox.question(
                self, "Relatório Gerado",
                f"Relatório de histórico gerado:\n{output_path}\n\n"
                f"Deseja abrir o arquivo?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                import subprocess
                subprocess.Popen([output_path], shell=True)
                
        except Exception as e:
            logger.exception("Erro ao gerar relatório de stencil")
            QMessageBox.critical(
                self, "Erro",
                f"Erro ao gerar relatório:\n{str(e)}"
            )
    
    def show_period_query_dialog(self):
        """Abre diálogo para consultar medições por período."""
        from PyQt6.QtWidgets import QDateEdit
        from PyQt6.QtCore import QDate
        
        dialog = QDialog(self)
        dialog.setWindowTitle("📅 Consultar por Período")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Seleção de período
        period_group = QGroupBox("Período de Consulta")
        period_layout = QFormLayout(period_group)
        
        date_start = QDateEdit()
        date_start.setDate(QDate.currentDate().addMonths(-1))
        date_start.setCalendarPopup(True)
        period_layout.addRow("Data Inicial:", date_start)
        
        date_end = QDateEdit()
        date_end.setDate(QDate.currentDate())
        date_end.setCalendarPopup(True)
        period_layout.addRow("Data Final:", date_end)
        
        layout.addWidget(period_group)
        
        # Opções
        options_group = QGroupBox("Opções")
        options_layout = QVBoxLayout(options_group)
        
        chk_all_stencils = QCheckBox("Todos os stencils")
        chk_all_stencils.setChecked(True)
        options_layout.addWidget(chk_all_stencils)
        
        layout.addWidget(options_group)
        
        # Lista de resultados
        from PyQt6.QtWidgets import QTableWidget
        result_table = QTableWidget()
        result_table.setColumnCount(5)
        result_table.setHorizontalHeaderLabels(["Data", "Stencil", "Média", "Resultado", "Operador"])
        result_table.setMinimumHeight(200)
        layout.addWidget(result_table)
        
        # Botões
        btn_layout = QHBoxLayout()
        
        btn_search = QPushButton("🔍 Buscar")
        def do_search():
            # Converter datas
            start = date_start.date().toPyDate()
            end = date_end.date().toPyDate()
            
            # Buscar em todos os stencils
            all_records = []
            stencils = self.stencil_tracker.list_stencils()
            
            for stencil in stencils:
                history = self.stencil_tracker.get_tension_history(stencil.code)
                for record in history:
                    try:
                        ts = record.timestamp if hasattr(record, 'timestamp') else record.get('timestamp', '')
                        from datetime import datetime
                        dt = datetime.fromisoformat(ts).date()
                        if start <= dt <= end:
                            all_records.append((stencil.code, record))
                    except:
                        pass
            
            # Preencher tabela
            result_table.setRowCount(len(all_records))
            for i, (code, record) in enumerate(all_records):
                ts = record.timestamp if hasattr(record, 'timestamp') else record.get('timestamp', '')
                avg = record.average_tension if hasattr(record, 'average_tension') else record.get('average_tension', 0)
                result_field = record.result if hasattr(record, 'result') else record.get('result', 'OK')
                op = record.operator if hasattr(record, 'operator') else record.get('operator', '-')
                
                result_table.setItem(i, 0, QTableWidgetItem(ts[:16]))
                result_table.setItem(i, 1, QTableWidgetItem(code))
                result_table.setItem(i, 2, QTableWidgetItem(f"{avg:.2f}"))
                result_table.setItem(i, 3, QTableWidgetItem(result_field))
                result_table.setItem(i, 4, QTableWidgetItem(op or "-"))
            
            self.statusBar().showMessage(f"{len(all_records)} registros encontrados", 3000)
        
        btn_search.clicked.connect(do_search)
        btn_layout.addWidget(btn_search)
        
        btn_export = QPushButton("📄 Exportar CSV")
        def do_export():
            if result_table.rowCount() == 0:
                QMessageBox.warning(dialog, "Sem Dados", "Execute uma busca primeiro.")
                return
            
            filepath, _ = QFileDialog.getSaveFileName(
                dialog, "Exportar CSV", "", "CSV (*.csv)"
            )
            if filepath:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write("Data,Stencil,Média,Resultado,Operador\n")
                    for row in range(result_table.rowCount()):
                        cols = [result_table.item(row, c).text() for c in range(5)]
                        f.write(",".join(cols) + "\n")
                QMessageBox.information(dialog, "Exportado", f"Dados exportados para:\n{filepath}")
        
        btn_export.clicked.connect(do_export)
        btn_layout.addWidget(btn_export)
        
        btn_layout.addStretch()
        
        btn_close = QPushButton("Fechar")
        btn_close.clicked.connect(dialog.accept)
        btn_layout.addWidget(btn_close)
        
        layout.addLayout(btn_layout)
        
        dialog.exec()


    def show_camera_settings_dialog(self):
        """Abre diálogo para configurações de câmera"""
        if not hasattr(self.controller.camera, 'is_connected') or not self.controller.camera.is_connected:
            QMessageBox.warning(self, "Aviso", "Conecte a câmera antes de ajustar as configurações.")
            return
        
        # Obtém o objeto VideoCapture
        cap = self.controller.camera.camera  # O atributo 'camera' do CameraController é o VideoCapture
        if cap is None:
            QMessageBox.warning(self, "Erro", "Câmera não disponível.")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Configurações de Câmera")
        dialog.setMinimumWidth(500)
        
        layout = QVBoxLayout(dialog)
        
        from PyQt6.QtWidgets import QSlider
        
        # ============== ESPELHAMENTO ==============
        mirror_group = QGroupBox("Espelhamento da Imagem")
        mirror_layout = QHBoxLayout(mirror_group)
        
        self.chk_mirror_x = QCheckBox("Espelhar Horizontalmente (X)")
        # Carrega do config ou usa atributo local
        saved_mirror_x = self.config.get("camera", "mirror_x", default=False)
        self._camera_mirror_x = getattr(self, '_camera_mirror_x', saved_mirror_x)
        self.chk_mirror_x.setChecked(self._camera_mirror_x)
        mirror_layout.addWidget(self.chk_mirror_x)
        
        self.chk_mirror_y = QCheckBox("Espelhar Verticalmente (Y)")
        saved_mirror_y = self.config.get("camera", "mirror_y", default=False)
        self._camera_mirror_y = getattr(self, '_camera_mirror_y', saved_mirror_y)
        self.chk_mirror_y.setChecked(self._camera_mirror_y)
        mirror_layout.addWidget(self.chk_mirror_y)
        
        layout.addWidget(mirror_group)
        
        # ============== AJUSTES DE IMAGEM ==============
        settings_group = QGroupBox("Ajustes de Imagem")
        settings_layout = QGridLayout(settings_group)
        
        # Função para criar slider com label
        def create_slider_row(row, label, prop_id, min_val, max_val, default, scale=1.0):
            settings_layout.addWidget(QLabel(f"{label}:"), row, 0)
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(min_val, max_val)
            
            # Tenta ler valor atual
            try:
                current = cap.get(prop_id)
                if current != -1 and current != 0:
                    slider.setValue(int(current * scale))
                else:
                    slider.setValue(default)
            except:
                slider.setValue(default)
            
            lbl = QLabel(str(slider.value()))
            slider.valueChanged.connect(lambda v: lbl.setText(str(v)))
            slider.valueChanged.connect(lambda v: self._apply_camera_prop(cap, prop_id, v / scale))
            
            settings_layout.addWidget(slider, row, 1)
            settings_layout.addWidget(lbl, row, 2)
            return slider
        
        # Brilho (0-255 na maioria das câmeras)
        self.slider_brightness = create_slider_row(0, "Brilho", cv2.CAP_PROP_BRIGHTNESS, 0, 255, 128, 1.0)
        
        # Contraste (0-255)
        self.slider_contrast = create_slider_row(1, "Contraste", cv2.CAP_PROP_CONTRAST, 0, 255, 128, 1.0)
        
        # Saturação (0-255)
        self.slider_saturation = create_slider_row(2, "Saturação", cv2.CAP_PROP_SATURATION, 0, 255, 128, 1.0)
        
        # Exposição (-13 a 0 para câmeras USB típicas)
        settings_layout.addWidget(QLabel("Exposição:"), 3, 0)
        self.slider_exposure = QSlider(Qt.Orientation.Horizontal)
        self.slider_exposure.setRange(-13, 0)
        try:
            exp = int(cap.get(cv2.CAP_PROP_EXPOSURE))
            self.slider_exposure.setValue(exp if -13 <= exp <= 0 else -6)
        except:
            self.slider_exposure.setValue(-6)
        self.lbl_exposure = QLabel(str(self.slider_exposure.value()))
        self.slider_exposure.valueChanged.connect(lambda v: self.lbl_exposure.setText(str(v)))
        self.slider_exposure.valueChanged.connect(lambda v: self._apply_camera_prop(cap, cv2.CAP_PROP_EXPOSURE, v))
        settings_layout.addWidget(self.slider_exposure, 3, 1)
        settings_layout.addWidget(self.lbl_exposure, 3, 2)
        
        # Ganho (0-255)
        self.slider_gain = create_slider_row(4, "Ganho", cv2.CAP_PROP_GAIN, 0, 255, 128, 1.0)
        
        layout.addWidget(settings_group)
        
        # ============== EXPOSIÇÃO AUTOMÁTICA ==============
        auto_group = QGroupBox("Controle Automático")
        auto_layout = QHBoxLayout(auto_group)
        
        self.chk_auto_exp = QCheckBox("Exposição Automática")
        try:
            auto_val = cap.get(cv2.CAP_PROP_AUTO_EXPOSURE)
            self.chk_auto_exp.setChecked(auto_val == 3 or auto_val == 1)
        except:
            self.chk_auto_exp.setChecked(True)
        self.chk_auto_exp.toggled.connect(
            lambda on: self._apply_camera_prop(cap, cv2.CAP_PROP_AUTO_EXPOSURE, 3 if on else 1)
        )
        auto_layout.addWidget(self.chk_auto_exp)
        
        self.chk_auto_wb = QCheckBox("Balanço de Branco Automático")
        try:
            wb_val = cap.get(cv2.CAP_PROP_AUTO_WB)
            self.chk_auto_wb.setChecked(wb_val == 1)
        except:
            self.chk_auto_wb.setChecked(True)
        self.chk_auto_wb.toggled.connect(
            lambda on: self._apply_camera_prop(cap, cv2.CAP_PROP_AUTO_WB, 1 if on else 0)
        )
        auto_layout.addWidget(self.chk_auto_wb)
        
        layout.addWidget(auto_group)
        
        # ============== BOTÕES ==============
        btn_layout = QHBoxLayout()
        
        btn_reset = QPushButton("Restaurar Padrão")
        btn_reset.clicked.connect(lambda: self._reset_camera_props(cap))
        btn_layout.addWidget(btn_reset)
        
        btn_apply = QPushButton("Aplicar Espelhamento")
        btn_apply.clicked.connect(self._apply_mirror_settings)
        btn_layout.addWidget(btn_apply)
        
        btn_close = QPushButton("Fechar")
        btn_close.clicked.connect(dialog.accept)
        btn_layout.addWidget(btn_close)
        
        layout.addLayout(btn_layout)
        
        # Nota informativa
        note = QLabel("<i>Nota: Algumas configurações podem não funcionar com todas as câmeras.</i>")
        note.setWordWrap(True)
        layout.addWidget(note)
        
        dialog.exec()
        
        # Salva configurações de espelhamento
        self._camera_mirror_x = self.chk_mirror_x.isChecked()
        self._camera_mirror_y = self.chk_mirror_y.isChecked()

    def _apply_camera_prop(self, cap, prop_id, value):
        """Aplica uma propriedade à câmera OpenCV"""
        try:
            result = cap.set(prop_id, value)
            if result:
                logger.debug(f"Câmera: Propriedade {prop_id} = {value}")
            else:
                logger.warning(f"Câmera: Falha ao definir propriedade {prop_id} = {value}")
        except Exception as e:
            logger.warning(f"Erro ao aplicar configuração de câmera: {e}")

    def _reset_camera_props(self, cap):
        """Restaura configurações padrão da câmera"""
        self.slider_brightness.setValue(128)
        self.slider_contrast.setValue(128)
        self.slider_saturation.setValue(128)
        self.slider_exposure.setValue(-6)
        self.slider_gain.setValue(128)
        self.chk_auto_exp.setChecked(True)
        self.chk_auto_wb.setChecked(True)
        self.chk_mirror_x.setChecked(False)
        self.chk_mirror_y.setChecked(False)

    def _apply_mirror_settings(self):
        """Salva configurações de espelhamento no config"""
        self._camera_mirror_x = self.chk_mirror_x.isChecked()
        self._camera_mirror_y = self.chk_mirror_y.isChecked()
        
        # Salva todas as configurações de câmera no arquivo
        try:
            self.config.remember_camera_settings(
                mirror_x=self._camera_mirror_x,
                mirror_y=self._camera_mirror_y,
                brightness=self.slider_brightness.value(),
                contrast=self.slider_contrast.value(),
                saturation=self.slider_saturation.value(),
                exposure=self.slider_exposure.value(),
                gain=self.slider_gain.value(),
                auto_exp=self.chk_auto_exp.isChecked(),
                auto_wb=self.chk_auto_wb.isChecked()
            )
            logger.info("Configurações de câmera salvas")
        except Exception as e:
            logger.warning(f"Erro ao salvar configurações de câmera: {e}")
        
        self.statusBar().showMessage(
            f"Espelhamento: X={'Sim' if self._camera_mirror_x else 'Não'}, "
            f"Y={'Sim' if self._camera_mirror_y else 'Não'} (Salvo)"
        )


    def show_settings_dialog(self):
        dlg = SettingsDialog(self.config, self)
        if dlg.exec():
            # Se o usuário modificou algo, re-aplica (se a CNC já estiver conectada)
            if self.controller.cnc.is_connected:
                self.config.apply_to_cnc(self.controller.cnc)
            self.statusBar().showMessage("Preferências salvas")

    def show_calibration_dialog(self):
        """Mostra um diálogo para configuração de calibração"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Calibração do Sistema CNC")
        dialog.setMinimumWidth(500)
        
        layout = QVBoxLayout(dialog)
        
        # Grupo de parâmetros físicos
        param_group = QGroupBox("Parâmetros da Máquina")
        param_layout = QGridLayout(param_group)
        
        param_layout.addWidget(QLabel("Pulsos por Revolução:"), 0, 0)
        pulses_input = QLineEdit(self.pulses_input.text())
        param_layout.addWidget(pulses_input, 0, 1)
        
        param_layout.addWidget(QLabel("Passo do Fuso (mm):"), 1, 0)
        fuso_input = QLineEdit(self.fuso_input.text())
        param_layout.addWidget(fuso_input, 1, 1)
        
        param_layout.addWidget(QLabel("Steps/mm calculado:"), 2, 0)
        steps_mm_result = QLabel("Calculando...")
        param_layout.addWidget(steps_mm_result, 2, 1)
        
        # Atualiza o cálculo quando os valores mudam
        def update_calculation():
            try:
                pulses = float(pulses_input.text())
                fuso = float(fuso_input.text())
                steps_mm = pulses / fuso
                steps_mm_result.setText(f"{steps_mm:.3f} steps/mm")
            except:
                steps_mm_result.setText("Erro no cálculo")
        
        pulses_input.textChanged.connect(update_calculation)
        fuso_input.textChanged.connect(update_calculation)
        update_calculation()  # Executa o cálculo inicial
        
        layout.addWidget(param_group)
        
        # Botões de ação
        buttons_layout = QHBoxLayout()
        
        apply_btn = QPushButton("Aplicar Parâmetros")
        def apply_and_close():
            self.pulses_input.setText(pulses_input.text())
            self.fuso_input.setText(fuso_input.text())
            dialog.accept()
            self.apply_calibration()
        apply_btn.clicked.connect(apply_and_close)
        
        test_btn = QPushButton("Testar Calibração")
        test_btn.clicked.connect(lambda: [dialog.accept(), self.show_calibration_test_dialog()])
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(dialog.reject)
        
        buttons_layout.addWidget(apply_btn)
        buttons_layout.addWidget(test_btn)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
        
        dialog.exec()

    def show_about_dialog(self):
        """Mostra informações sobre o aplicativo"""
        QMessageBox.about(self, "Sobre HesaiVision", 
                        "HesaiVision v1.0\n\n"
                        "Sistema de Inspeção Óptica Automatizada\n"
                        "Desenvolvido para controle de CNC com GRBL\n\n"
                        "© 2025 HesaiVision")
        
    def show_definir_mapa_dialog(self):
        """Abre diálogo para definir cantos e gerar mapa (modeless, sempre no topo)."""
        # 1) Cria sem flags inválidas
        dialog = QDialog(self)
        dialog.setWindowTitle("Definir Mapa")

        # 2) Non‐modal: permite operar a janela principal
        dialog.setWindowModality(Qt.WindowModality.NonModal)

        # 3) Sempre no topo, com título e botão de fechar
        dialog.setWindowFlags(
            dialog.windowFlags()
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowStaysOnTopHint
        )

        layout = QVBoxLayout(dialog)

        # Nome do programa
        h1 = QHBoxLayout()
        h1.addWidget(QLabel("Nome do Programa:"))
        self.map_program_name_edit = QLineEdit()
        # Carrega último nome de programa usado
        last_program = self.config.get("mosaic", "last_program_name", default="")
        self.map_program_name_edit.setText(last_program)
        h1.addWidget(self.map_program_name_edit)
        layout.addLayout(h1)

        # Pasta de salvamento (base para os projetos)
        h2 = QHBoxLayout()
        h2.addWidget(QLabel("Pasta de Salvamento:"))
        self.map_folder_edit = QLineEdit()
        # Carrega última pasta usada ou usa padrão "Projetos"
        import os
        default_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Projetos")
        last_folder = self.config.get("mosaic", "last_folder", default=default_folder)
        self.map_folder_edit.setText(last_folder)
        self.map_folder_edit.setToolTip(
            "Pasta base onde serão criadas as subpastas dos programas.\n"
            "Estrutura: [Pasta]/[Nome do Programa]/Imagens/"
        )
        h2.addWidget(self.map_folder_edit)
        btn_browse = QPushButton("Buscar…")
        btn_browse.clicked.connect(self._select_map_folder)
        h2.addWidget(btn_browse)
        layout.addLayout(h2)

        # Passos X/Y
        h3 = QHBoxLayout()
        h3.addWidget(QLabel("Passo X (mm):"))
        self.map_step_x_edit = QLineEdit()
        # Carrega valores salvos
        saved_step_x = self.config.get("map", "step_x", default=10.0)
        self.map_step_x_edit.setText(str(saved_step_x))
        h3.addWidget(self.map_step_x_edit)
        h3.addWidget(QLabel("Passo Y (mm):"))
        self.map_step_y_edit = QLineEdit()
        saved_step_y = self.config.get("map", "step_y", default=10.0)
        self.map_step_y_edit.setText(str(saved_step_y))
        h3.addWidget(self.map_step_y_edit)
        layout.addLayout(h3)

        # ============== OPÇÕES DE MOSAICO ==============
        from PyQt6.QtWidgets import QSpinBox
        mosaic_group = QGroupBox("Montagem de Mosaico")
        mosaic_layout = QGridLayout(mosaic_group)
        
        # Checkbox para ativar montagem automática
        self.chk_auto_mosaic = QCheckBox("Montar mosaico automaticamente após captura")
        saved_auto_build = self.config.get("mosaic", "auto_build", default=True)
        self.chk_auto_mosaic.setChecked(saved_auto_build)
        mosaic_layout.addWidget(self.chk_auto_mosaic, 0, 0, 1, 4)
        
        # Margem de corte (para remover distorção de lente)
        mosaic_layout.addWidget(QLabel("Margem de corte (px):"), 1, 0)
        self.spin_mosaic_margin = QSpinBox()
        self.spin_mosaic_margin.setRange(0, 500)
        saved_margin = self.config.get("mosaic", "margin", default=50)
        self.spin_mosaic_margin.setValue(saved_margin)
        self.spin_mosaic_margin.setToolTip("Pixels a remover de cada borda para eliminar distorção de lente")
        mosaic_layout.addWidget(self.spin_mosaic_margin, 1, 1)
        
        # Blending nas junções
        mosaic_layout.addWidget(QLabel("Blending (px):"), 1, 2)
        self.spin_mosaic_blend = QSpinBox()
        self.spin_mosaic_blend.setRange(0, 100)
        saved_blend = self.config.get("mosaic", "blend_size", default=20)
        self.spin_mosaic_blend.setValue(saved_blend)
        self.spin_mosaic_blend.setToolTip("Tamanho da zona de transição gradual entre tiles")
        mosaic_layout.addWidget(self.spin_mosaic_blend, 1, 3)
        
        layout.addWidget(mosaic_group)
        # ============== FIM OPÇÕES DE MOSAICO ==============

        # ============== TEMPO DE ESPERA ANTES DA CAPTURA ==============
        capture_group = QGroupBox("Configurações de Captura")
        capture_layout = QHBoxLayout(capture_group)
        
        capture_layout.addWidget(QLabel("Tempo de espera antes da captura (ms):"))
        self.spin_capture_delay = QSpinBox()
        self.spin_capture_delay.setRange(50, 5000)
        saved_delay = self.config.get("mosaic", "capture_delay_ms", default=200)
        self.spin_capture_delay.setValue(saved_delay)
        self.spin_capture_delay.setSingleStep(50)
        self.spin_capture_delay.setToolTip(
            "Tempo de estabilização após movimento antes de capturar a imagem.\n"
            "Aumente se a câmera for lenta ou a imagem sair tremida."
        )
        capture_layout.addWidget(self.spin_capture_delay)
        capture_layout.addWidget(QLabel("ms"))
        capture_layout.addStretch()
        
        layout.addWidget(capture_group)
        # ============== FIM CONFIGURAÇÕES DE CAPTURA ==============

        # Botões de definição de canto
        btn_origin = QPushButton("Definir canto inferior esquerdo")
        btn_origin.clicked.connect(lambda: self._define_map_corner('origin'))
        layout.addWidget(btn_origin)

        btn_end = QPushButton("Definir canto superior direito")
        btn_end.clicked.connect(lambda: self._define_map_corner('end'))
        layout.addWidget(btn_end)

        # Botão gerar mapa
        btn_generate = QPushButton("🔧 Gerar Mapa de Imagens")
        btn_generate.setMinimumHeight(40)
        btn_generate.clicked.connect(lambda: self._on_generate_map(dialog))
        layout.addWidget(btn_generate)

        dialog.show()  # modeless, não bloqueia a janela principal

    def _select_map_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Selecione pasta para salvar imagens")
        if folder:
            self.map_folder_edit.setText(folder)

    def _define_map_corner(self, which):
        pos = self.controller.cnc.get_current_position()
        if which == 'origin':
            self.map_origin = {'x': pos['x'], 'y': pos['y']}
            # Usa statusBar em vez de MessageBox para evitar bloqueio
            # (o diálogo está como WindowStaysOnTopHint)
            self.statusBar().showMessage(
                f"✅ Origem definida: X={pos['x']:.3f}, Y={pos['y']:.3f}"
            )
        else:
            self.map_end = {'x': pos['x'], 'y': pos['y']}
            self.statusBar().showMessage(
                f"✅ Limite definido: X={pos['x']:.3f}, Y={pos['y']:.3f}"
            )

    def _on_generate_map(self, dialog):
        # Verifica conexão CNC - bloqueia APENAS a geração, não o diálogo
        if not self.controller.cnc.is_connected:
            QMessageBox.warning(
                dialog, "CNC Não Conectado",
                "A geração do mapa requer conexão com o CLP para movimentar a máquina.\n\n"
                "Você pode:\n"
                "• Conectar o CLP e tentar novamente\n"
                "• Configurar e salvar os parâmetros na receita para uso posterior\n\n"
                "As demais funcionalidades (câmera, receitas) continuam disponíveis."
            )
            return
                
        # Passo 1 – coletar e validar parâmetros ---------------------
        params = self._collect_map_params(dialog)
        if params is None:      # validação falhou ⇒ aborta
            return

        # Passo 2 – iniciar thread de geração -----------------------
        self._start_map_thread(params, dialog)

    def _collect_map_params(self, parent_dialog=None) -> MapParams | None:
        """
        Valida inputs da UI e devolve objeto MapParams ou None em caso de erro.
        Usa parent_dialog para exibir mensagens sobre o diálogo flutuante.
        """
        # Usa o diálogo como parent para os MessageBox evitando conflito
        # com WindowStaysOnTopHint
        msg_parent = parent_dialog if parent_dialog else self
        
        origin = getattr(self, 'map_origin', None)
        end    = getattr(self, 'map_end',    None)
        if not origin or not end:
            QMessageBox.warning(msg_parent, "Erro", "Defina ambos os cantos antes de gerar o mapa.")
            return None

        try:
            step_x = float(self.map_step_x_edit.text())
            step_y = float(self.map_step_y_edit.text())
        except ValueError:
            QMessageBox.warning(msg_parent, "Erro", "Passos X/Y inválidos.")
            return None

        dx, dy = end['x'] - origin['x'], end['y'] - origin['y']
        if step_x <= 0 or step_y <= 0:
            QMessageBox.warning(msg_parent, "Erro", "Os passos devem ser maiores que zero.")
            return None

        # Ajuste opcional se o passo superar dimensão
        if step_x > dx or step_y > dy:
            if QMessageBox.question(
                    msg_parent,
                    "Passo maior que dimensão",
                    ("Algum passo é maior que a dimensão da placa. "
                     "Deseja ajustar automaticamente?"),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            ) == QMessageBox.StandardButton.No:
                return None
            step_x = min(step_x, dx)
            step_y = min(step_y, dy)
            self.map_step_x_edit.setText(f"{step_x:.3f}")
            self.map_step_y_edit.setText(f"{step_y:.3f}")

        base_folder = self.map_folder_edit.text().strip()
        prog = self.map_program_name_edit.text().strip()
        if not base_folder or not prog:
            QMessageBox.warning(msg_parent, "Erro", "Informe o nome do programa e a pasta de salvamento.")
            return None

        # ========== CRIA ESTRUTURA DE PASTAS ==========
        # Estrutura: [Pasta Base]/[Nome do Programa]/Imagens/
        import os
        from pathlib import Path
        
        # Sanitiza o nome do programa para uso em pasta
        safe_prog_name = "".join(c for c in prog if c.isalnum() or c in "._- ").strip()
        if not safe_prog_name:
            QMessageBox.warning(msg_parent, "Erro", "Nome do programa inválido para criar pasta.")
            return None
        
        # Cria a estrutura de pastas
        program_folder = Path(base_folder) / safe_prog_name
        images_folder = program_folder / "Imagens"
        
        try:
            images_folder.mkdir(parents=True, exist_ok=True)
            logger.info(f"Estrutura de pastas criada: {images_folder}")
        except Exception as e:
            QMessageBox.critical(msg_parent, "Erro", f"Falha ao criar pasta:\n{images_folder}\n\nErro: {e}")
            return None
        
        # A pasta de imagens é onde as capturas serão salvas
        final_folder = str(images_folder)

        # ========== SALVA CONFIGURAÇÕES PARA PRÓXIMA VEZ ==========
        try:
            # Salva a pasta BASE (não a pasta de imagens) para que o usuário possa reusar
            self.config.remember_map_params(step_x, step_y, base_folder, prog)
            self.config.remember_mosaic_settings(
                auto_build=self.chk_auto_mosaic.isChecked(),
                margin=self.spin_mosaic_margin.value(),
                blend_size=self.spin_mosaic_blend.value(),
                capture_delay_ms=self.spin_capture_delay.value()
            )
            logger.debug("Configurações de mapa/mosaico salvas")
        except Exception as e:
            logger.warning(f"Erro ao salvar configurações de mapa: {e}")
        # ==========================================================

        # Usa a pasta de imagens como destino final
        return MapParams(origin, end, step_x, step_y, final_folder, prog)

    def _start_map_thread(self, p: MapParams, dialog):
        """
        Separa a configuração da thread e da UI/ProgressBar.
        """
        # Obtém o tempo de espera configurado
        capture_delay = getattr(self, 'spin_capture_delay', None)
        delay_ms = capture_delay.value() if capture_delay else 200
        
        # Context manager garante preview restaurado
        with _PreviewSuspender(self.camera_preview):
            self.map_thread = MapGeneratorThread(
                self.controller, p.origin, p.end,
                p.step_x, p.step_y, p.folder, p.program_name,
                self._get_current_feed_rate(),  # Passa velocidade configurada
                delay_ms  # Tempo de espera antes da captura
            )

            # Progress dialog simples
            self.map_progress = QProgressDialog("Gerando mapa…", "Cancelar", 0, 0, self)
            self.map_progress.setWindowTitle("Progresso do Mapa")
            self.map_progress.setWindowModality(Qt.WindowModality.NonModal)
            self.map_progress.show()

            # Conexões de sinal ⇄ slots
            self.map_thread.progress.connect(self._on_map_progress)
            self.map_thread.image_captured.connect(self.camera_preview.display_image)
            self.map_thread.finished.connect(lambda: self._on_map_finished(dialog))
            self.map_thread.error.connect(self._on_map_error)

            self.map_progress.canceled.connect(self.map_thread.requestInterruption)
            self.map_thread.start()
    def _get_current_feed_rate(self):
        """Obtém a velocidade de movimentação configurada na interface"""
        try:
            return float(self.movement_widget.feed_rate.text())
        except (ValueError, AttributeError):
            return 1000.0  # fallback

    # ---------- slots da geração de mapa ----------------------------

    def _on_map_progress(self, done: int, total: int):
        self.map_progress.setMaximum(total)
        self.map_progress.setValue(done)
        pct = int(done / total * 100) if total else 0
        self.map_progress.setLabelText(f"Capturadas {done}/{total} imagens ({pct}%)")

    def _on_map_finished(self, dialog):
        self.map_progress.close()
        
        # IMPORTANTE: Fecha o diálogo ANTES de exibir mensagens
        # Isso evita conflito com WindowStaysOnTopHint
        dialog.accept()
        
        # ========== SINCRONIZA BOTÃO DE BACKLIGHT ==========
        self._sync_backlight_button()
        
        # Obtém parâmetros da pasta e opções de mosaico
        folder = getattr(self, 'map_folder_edit', None)
        folder_path = folder.text().strip() if folder else ""
        
        # Verifica se montagem automática está habilitada
        auto_mosaic = getattr(self, 'chk_auto_mosaic', None)
        should_build_mosaic = auto_mosaic.isChecked() if auto_mosaic else True
        
        if should_build_mosaic and folder_path and os.path.isdir(folder_path):
            # Obtém parâmetros de margem e blending
            margin = getattr(self, 'spin_mosaic_margin', None)
            margin_value = margin.value() if margin else 50
            
            blend = getattr(self, 'spin_mosaic_blend', None)
            blend_value = blend.value() if blend else 20
            
            # Monta o mosaico
            self.statusBar().showMessage("Montando mosaico das imagens capturadas...")
            QApplication.processEvents()
            
            try:
                mosaic_path = compose_mosaic_from_folder(
                    folder_path,
                    invert_rows=True,  # Origem no canto inferior-esquerdo
                    margin=margin_value,
                    blend_size=blend_value,
                )
                
                if mosaic_path:
                    QMessageBox.information(
                        self, "Concluído", 
                        f"✅ Mapa gerado com sucesso!\n\n"
                        f"📁 Imagens salvas em:\n{folder_path}\n\n"
                        f"🖼️ Mosaico montado:\n{mosaic_path}"
                    )
                    self.statusBar().showMessage(f"Mosaico salvo: {mosaic_path}")
                else:
                    QMessageBox.information(
                        self, "Concluído", 
                        f"Mapa gerado com sucesso.\n\n"
                        f"⚠️ Falha ao montar mosaico (sem imagens válidas encontradas)."
                    )
            except Exception as e:
                logger.error(f"Erro ao montar mosaico: {e}")
                QMessageBox.information(
                    self, "Concluído", 
                    f"Mapa gerado com sucesso.\n\n"
                    f"⚠️ Erro ao montar mosaico: {e}"
                )
        else:
            QMessageBox.information(self, "Concluído", "Mapa gerado com sucesso.")

    def _on_map_error(self, msg: str):
        self.map_progress.close()
        # Sincroniza botão de backlight após erro
        self._sync_backlight_button()
        QMessageBox.critical(self, "Erro", msg)
    
    def _sync_backlight_button(self):
        """
        Sincroniza o estado visual do botão de backlight com o estado real do CLP.
        Chamado após operações que podem alterar o backlight programaticamente.
        """
        try:
            # Verifica se o widget de movimento existe
            if not hasattr(self, 'movement_widget'):
                return
            
            # Verifica se o controlador está conectado e tem suporte a backlight
            if (not hasattr(self.controller, 'cnc') or 
                not self.controller.cnc.is_connected or
                not hasattr(self.controller.cnc, 'backlight_on')):
                return
            
            # Obtém estado atual do backlight
            is_on = self.controller.cnc.backlight_on
            
            # Atualiza o botão sem disparar o sinal toggled
            self.movement_widget.backlight_button.blockSignals(True)
            self.movement_widget.backlight_button.setChecked(is_on)
            self.movement_widget.backlight_button.setText(
                "💡 Backlight ON" if is_on else "💡 Backlight OFF"
            )
            self.movement_widget.backlight_button.blockSignals(False)
            
            logger.debug(f"Backlight sincronizado: {'ON' if is_on else 'OFF'}")
        except Exception as e:
            logger.error(f"Erro ao sincronizar botão de backlight: {e}")

    def save_gcode(self):
        """Salva a sequência atual como arquivo G-CODE"""
        if not self.current_sequence:
            QMessageBox.warning(self, "Aviso", "Crie uma sequência primeiro")
            return
            
        from aoi_lib.gcode_manager import GCodeManager
        gcode_manager = GCodeManager()
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Salvar como G-CODE", "", "Arquivos G-CODE (*.gcode *.nc *.ngc)"
        )
        
        if filename:
            if not filename.lower().endswith(('.gcode', '.nc', '.ngc')):
                filename += '.gcode'
                
            if gcode_manager.save_gcode_to_file(self.current_sequence, filename):
                self.statusBar().showMessage(f"G-CODE salvo em {filename}")
            else:
                QMessageBox.critical(self, "Erro", "Falha ao salvar o arquivo G-CODE")

    def apply_calibration(self):
        """
        Aplica a calibração de movimento com base nos valores informados pelo usuário.
        Envia comandos diretos para o GRBL para configurar os steps/mm.
        """
        if not self.controller.cnc.is_connected:
            QMessageBox.warning(self, "Erro", "CNC não conectada. Conecte primeiro.")
            return
        
        # Se for PLC, atualiza apenas o fator de conversão interno
        if isinstance(self.controller.cnc, PLCAxisController):
            try:
                pulses = float(self.pulses_input.text())
                fuso_pass = float(self.fuso_input.text())
                
                # Atualiza o fator de conversão pulsos/mm do PLC
                self.controller.cnc.pulses_per_mm = pulses / fuso_pass
                
                # Salva no JSON para persistir a configuração
                self.config.remember_calibration(pulses, fuso_pass)
                
                self.statusBar().showMessage(f"Calibração PLC aplicada: {pulses / fuso_pass:.3f} pulsos/mm")
                QMessageBox.information(
                    self, "Calibração PLC",
                    f"Fator de conversão atualizado:\n{pulses / fuso_pass:.3f} pulsos/mm"
                )
            except ValueError:
                QMessageBox.warning(self, "Erro", "Valores de calibração inválidos.")
            return
        
        # Se for GRBL, verifica se tem o atributo grbl
        if not hasattr(self.controller.cnc, 'grbl') or not self.controller.cnc.grbl:
            QMessageBox.warning(self, "Erro", "Controlador GRBL não disponível.")
            return
            
        try:
            pulses = float(self.pulses_input.text())
            fuso_pass = float(self.fuso_input.text())
            
            # Calcula steps/mm: (pulsos por revolução) / (passo do fuso em mm)
            steps_per_mm = pulses / fuso_pass
            
            # Armazena o valor calculado
            self.controller.cnc.steps_to_mm_factor = fuso_pass / pulses
            
            # Envia comandos para configurar o GRBL
            logger.info(f"CALIBRAÇÃO: Configurando steps/mm para {steps_per_mm}")
            
            # Verifica se o usuário deseja realmente enviar estes valores
            reply = QMessageBox.question(
                self, 
                "Confirmar Calibração", 
                f"Deseja enviar os seguintes parâmetros para o GRBL?\n\n"
                f"Steps/mm eixo X: {steps_per_mm:.3f}\n"
                f"Steps/mm eixo Y: {steps_per_mm:.3f}\n\n"
                f"Isso irá alterar a configuração do controlador.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Comandos para configurar os eixos X e Y
                self.controller.cnc.grbl.send_immediately(f"$100={steps_per_mm:.3f}")
                QTimer.singleShot(100, lambda: self.controller.cnc.grbl.send_immediately(f"$101={steps_per_mm:.3f}"))
                
                # Solicita ao usuário que faça um teste de calibração
                QTimer.singleShot(500, self.show_calibration_test_dialog)
                
                self.statusBar().showMessage(f"Calibração aplicada: {steps_per_mm:.3f} steps/mm")

                # --------- salva no JSON ----------
                self.config.remember_calibration(pulses, fuso_pass)

            else:
                self.statusBar().showMessage("Calibração cancelada pelo usuário")
                
        except ValueError:
            QMessageBox.warning(self, "Erro", "Valores de calibração inválidos.")

    def show_calibration_test_dialog(self):
        """
        Exibe um diálogo para testar a calibração atual.
        """
        dialog = QDialog(self)
        dialog.setWindowTitle("Teste de Calibração")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Instruções
        instructions = QLabel(
            "Para testar a calibração:\n\n"
            "1. Coloque um papel milimetrado ou uma régua sob a cabeça da máquina\n"
            "2. Escolha uma distância de teste\n"
            "3. Clique em 'Mover X' ou 'Mover Y' para testar cada eixo\n"
            "4. Verifique se o deslocamento físico corresponde ao valor escolhido\n"
            "5. Se necessário, ajuste os valores de calibração e aplique novamente"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Distância de teste
        test_layout = QHBoxLayout()
        test_layout.addWidget(QLabel("Distância de teste:"))
        distance_input = QLineEdit("10")
        test_layout.addWidget(distance_input)
        test_layout.addWidget(QLabel("mm"))
        layout.addLayout(test_layout)
        
        # Botões de teste
        buttons_layout = QHBoxLayout()
        
        move_x_btn = QPushButton("Mover X")
        move_x_btn.clicked.connect(lambda: self.test_calibration_move(0, float(distance_input.text())))
        
        move_y_btn = QPushButton("Mover Y")
        move_y_btn.clicked.connect(lambda: self.test_calibration_move(1, float(distance_input.text())))
        
        reset_position_btn = QPushButton("Zerar Posição")
        reset_position_btn.clicked.connect(self.set_zero_position)
        
        buttons_layout.addWidget(move_x_btn)
        buttons_layout.addWidget(move_y_btn)
        buttons_layout.addWidget(reset_position_btn)
        
        layout.addLayout(buttons_layout)
        
        # Resultados
        result_group = QGroupBox("Resultados")
        result_layout = QVBoxLayout(result_group)
        
        self.calibration_test_result = QLabel("Execute um teste para ver os resultados")
        result_layout.addWidget(self.calibration_test_result)
        
        layout.addWidget(result_group)
        
        # Botões de controle
        control_layout = QHBoxLayout()
        close_btn = QPushButton("Concluir")
        close_btn.clicked.connect(dialog.accept)
        control_layout.addWidget(close_btn)
        
        layout.addLayout(control_layout)
        
        dialog.exec()

    def test_calibration_move(self, axis, distance):
        """
        Realiza um movimento de teste para calibração.
        
        Args:
            axis: 0 para X, 1 para Y
            distance: Distância em mm para mover
        """
        if not self.controller.cnc.is_connected:
            QMessageBox.warning(self, "Erro", "CNC não conectada")
            return
        
        try:
            # Captura posição inicial
            initial_position = self.controller.cnc.get_current_position()
            
            # Prepara o comando
            axis_name = "X" if axis == 0 else "Y"
            
            # Define o modo absoluto para garantir precisão
            self.controller.cnc.grbl.send_immediately("G90")
            
            # Calcula a posição absoluta a ser atingida
            target_position = {}
            target_position['x'] = initial_position['x'] + distance if axis == 0 else initial_position['x']
            target_position['y'] = initial_position['y'] + distance if axis == 1 else initial_position['y']
            
            # Envia o movimento como coordenada absoluta
            if axis == 0:
                self.controller.cnc.move_to_absolute_position(target_position['x'], None, 500)
            else:
                self.controller.cnc.move_to_absolute_position(None, target_position['y'], 500)
            self.controller.cnc.wait_for_idle()
            
            # Aguarda um pouco para o movimento ser concluído
            QTimer.singleShot(1500, lambda: self.verify_calibration_result(axis, initial_position, distance))
            
        except Exception as e:
            logger.error(f"CALIBRAÇÃO: Erro no teste de calibração: {e}")
            QMessageBox.warning(self, "Erro", f"Erro no teste: {str(e)}")

    def _show_calibration_result(self, axis, initial_position, expected_distance):
        """
        Calcula deslocamento real, erro e atualiza o QLabel de resultados.
        Executado de forma assíncrona pelo QTimer.
        """
        try:
            current_position = self.controller.cnc.get_current_position()

            axis_name = "x" if axis == 0 else "y"
            actual_distance = current_position[axis_name] - initial_position[axis_name]

            error = actual_distance - expected_distance
            error_percent = (error / expected_distance * 100) if expected_distance else 0

            result_text = (
                f"Eixo: {axis_name.upper()}\n"
                f"Movimento comandado: {expected_distance:.3f} mm\n"
                f"Movimento real: {actual_distance:.3f} mm\n"
                f"Erro: {error:.3f} mm ({error_percent:.2f}%)\n\n"
            )

            if abs(error_percent) < 1:
                result_text += "■ Calibração excelente (erro < 1%)"
            elif abs(error_percent) < 5:
                result_text += "✓ Calibração aceitável (erro < 5%)"
            else:
                result_text += "■ Calibração insatisfatória – ajuste os parâmetros"

            if hasattr(self, "calibration_test_result"):
                self.calibration_test_result.setText(result_text)

            logger.info(
                "CALIBRAÇÃO: Resultado – %s",
                result_text.replace("\n", " | ")
            )
        except Exception as e:
            logger.error(f"CALIBRAÇÃO: Erro ao calcular resultado: {e}")

    def verify_calibration_result(self, axis, initial_position, expected_distance):
        """
        Verifica o resultado do teste de calibração.
        
        Args:
            axis: 0 para X, 1 para Y
            initial_position: Posição antes do movimento
            expected_distance: Distância esperada do movimento
        """
        try:
            # 1) força a atualização de status
            self.controller.cnc.grbl.send_immediately("?")

            # 2) Agenda o cálculo daqui a 250 ms para NÃO travar a GUI
            QTimer.singleShot(
                250,
                lambda: self._show_calibration_result(
                    axis, initial_position, expected_distance
                )
            )
            return
            
        except Exception as e:
            logger.error(f"CALIBRAÇÃO: Erro ao verificar resultado: {e}")

    

    def on_image_captured(self, image, position_name):
        """Handle captured image and register position"""
        # Display in image viewer
        self.image_viewer.display_image(image, f"Image: {position_name}")
        
        # Get current position
        if not self.controller.cnc.is_connected:
            QMessageBox.warning(self, "Error", "CNC not connected")
            return
            
        current_pos = self.controller.cnc.get_current_position()
        
        # Register position with image
        self.position_registry.add_position(
            position_name,
            current_pos['x'],
            current_pos['y'],
            current_pos['z'],
            image
        )
        
        self.statusBar().showMessage(f"Position '{position_name}' registered at X:{current_pos['x']:.3f}, Y:{current_pos['y']:.3f}")

    def create_sequence_from_registry(self):
        """Create a sequence from registered positions"""
        if not self.position_registry.positions:
            QMessageBox.warning(self, "Warning", "No positions registered")
            return
            
        # Get sequence name
        sequence_name = self.sequence_widget.sequence_name.text()
        if not sequence_name:
            QMessageBox.warning(self, "Warning", "Please enter a sequence name")
            return
            
        # Clear existing positions in the position list widget
        self.position_list_widget.clear_positions()
        
        # Create positions for the sequence
        positions = []
        for pos in self.position_registry.positions:
            # Create position object with camera parameters
            camera_params = {"has_image": pos['image'] is not None}
            
            inspection_pos = InspectionPosition(
                pos['name'],
                pos['x'],
                pos['y'],
                pos.get('z', 0.0),
                camera_params
            )
            positions.append(inspection_pos)
            
            # Also add to the position list widget
            self.position_list_widget.add_position(inspection_pos)
            
        # Create the sequence
        self.current_sequence = self.controller.create_sequence(sequence_name, positions)
        
        # Update UI
        self.sequence_widget.sequence_status.setText(f"Created: {len(positions)} positions")
        self.statusBar().showMessage(f"Sequence '{sequence_name}' created with {len(positions)} positions")
        
        # Ask if user wants to save as G-CODE
        reply = QMessageBox.question(
            self, 
            "Save G-CODE", 
            "Do you want to save this sequence as G-CODE?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.save_gcode()

    def load_gcode(self):
        """Carrega uma sequência a partir de um arquivo G-CODE"""
        from aoi_lib.gcode_manager import GCodeManager
        gcode_manager = GCodeManager()
        
        filename, _ = QFileDialog.getOpenFileName(
            self, "Abrir G-CODE", "", "Arquivos G-CODE (*.gcode *.nc *.ngc)"
        )
        
        if filename:
            # Carrega o G-CODE
            result = gcode_manager.read_gcode_file(filename)
            
            if result:
                # Limpa posições atuais
                self.position_list_widget.clear_positions()
                
                # Cria sequência a partir dos dados do G-CODE
                positions = []
                for pos_data in result['positions']:
                    # Cria objeto de posição
                    position = InspectionPosition(
                        pos_data['name'], 
                        pos_data['x'], 
                        pos_data['y'],
                        pos_data['camera_params']
                    )
                    
                    # Adiciona à lista visual
                    self.position_list_widget.add_position(position)
                    
                    # Adiciona à lista interna
                    positions.append(position)
                
                # Cria a sequência
                self.current_sequence = self.controller.create_sequence(
                    result['sequence_name'], positions
                )
                
                # Atualiza interface
                self.sequence_widget.sequence_name.setText(result['sequence_name'])
                self.sequence_widget.sequence_status.setText(
                    f"Carregada do G-CODE: {len(positions)} posições"
                )
                
                self.statusBar().showMessage(f"G-CODE carregado de {filename}")
            else:
                QMessageBox.critical(self, "Erro", "Falha ao carregar o arquivo G-CODE")
        
    def refresh_ports(self):
        """Atualiza a lista de portas seriais disponíveis"""
        import serial.tools.list_ports
        
        self.cnc_port_combo.clear()
        ports = [port.device for port in serial.tools.list_ports.comports()]
        
        if ports:
            self.cnc_port_combo.addItems(ports)
            
            # Verificar se COM9 está na lista e selecionar
            com9_index = self.cnc_port_combo.findText("COM9")
            if com9_index >= 0:
                self.cnc_port_combo.setCurrentIndex(com9_index)
                self.statusBar().showMessage("Porta COM9 detectada")
        else:
            self.statusBar().showMessage("Nenhuma porta serial encontrada")
            
    def connect_cnc(self): 
        """Conecta à máquina CNC usando a biblioteca grbl-streamer""" 
        # Se for PLCAxisController, alterna Modbus connect/disconnect
        if isinstance(self.controller.cnc, PLCAxisController):
            plc = self.controller.cnc
            if plc.is_connected:
                # desconectar
                plc.close()
                self.connect_cnc_btn.setText("Conectar PLC")
                self.cnc_status.setText("Desconectado")
                self.statusBar().showMessage("PLC desconectado")
                logger.info("PLC desconectado pelo usuário")
                # NOTA: Abas permanecem habilitadas para permitir
                # uso de câmera, receitas e outras funcionalidades
            else:
                # Tenta conectar usando o controller existente
                logger.info(f"Tentando conectar ao PLC em {plc.host}:{plc.port}")
                try:
                    plc.connect()
                except Exception as e:
                    QMessageBox.warning(
                        self,
                        "Erro de Conexão",
                        f"Falha ao conectar ao PLC em {plc.host}:{plc.port}:\n{e}"
                    )
                    logger.error(f"Falha ao conectar ao PLC em {plc.host}:{plc.port}: {e}")
                else:
                    self.connect_cnc_btn.setText("Desconectar PLC")
                    self.cnc_status.setText("Conectado")
                    self.statusBar().showMessage(f"PLC conectado em {plc.host}:{plc.port}")
                    logger.info(f"PLC conectado com sucesso em {plc.host}:{plc.port}")
            return
        # Senão, cai no fluxo original GRBL…
        if hasattr(self.controller.cnc, 'grbl') and self.controller.cnc.grbl: 
            self.controller.cnc.grbl.poll_stop() 
            self.controller.cnc.grbl.disconnect() 
            self.controller.cnc.grbl = None
            self.controller.cnc.is_connected = False
            self.connect_cnc_btn.setText("Conectar CNC")
            self.cnc_status.setText("Desconectado")
            self.statusBar().showMessage("CNC desconectada")
    
        else:
            # Conectar
            port = self.cnc_port_combo.currentText()
            if not port:
                QMessageBox.warning(self, "Erro", "Selecione uma porta serial")
                return
                
            self.statusBar().showMessage(f"Conectando à CNC na porta {port}...")
            
            try:
                # Define função de callback para eventos do GrblStreamer
                def grbl_callback(eventstring, *data):
                    logger.debug(f"CALLBACK: Evento '{eventstring}' recebido com data: {data}") 

                    # Capturar offsets do sistema de coordenadas (G54, G55, etc.)
                    if eventstring == "on_hash_stateupdate":
                        if data and isinstance(data[0], dict):
                            hash_state = data[0]

                            # Processar G54 APENAS se o WCS ativo for G54
                            # Isso evita que a resposta tardia do $# sobrescreva um offset
                            # que foi definido manualmente via G10 L20 para G54.
                            if self.active_wcs == "G54": 
                                g54_offset_data = hash_state.get('G54') 
                                if isinstance(g54_offset_data, (list, tuple)) and len(g54_offset_data) >= 2:
                                    try:
                                        new_offset_x_phys = float(g54_offset_data[0])
                                        new_offset_y_phys = float(g54_offset_data[1])
                                        new_offset_z_phys = float(g54_offset_data[2]) if len(g54_offset_data) > 2 else 0.0

                                        # Converte Y físico → lógico (depende de invert_y)
                                        if self.controller.cnc.invert_y:
                                            new_offset_y_log = -new_offset_y_phys
                                        else:
                                            new_offset_y_log = new_offset_y_phys

                                        self.current_wcs_offset = {
                                            # X e Z permanecem iguais
                                            'x': new_offset_x_phys,
                                            # guardamos FÍSICO para operar com G10 L20.
                                            'y': new_offset_y_phys,
                                            'z': new_offset_z_phys
                                        }

                                        logger.info(
                                            "CALLBACK: Offset G54 atualizado "
                                            f"(físico): {{x:{new_offset_x_phys:.3f}, y:{new_offset_y_phys:.3f}, z:{new_offset_z_phys:.3f}}}; "
                                            f"(lógico Y={new_offset_y_log:.3f})"
                                        )
                                    except (ValueError, TypeError):
                                         logger.error(f"CALLBACK: Erro ao converter offset G54 de $#: {g54_offset_data}")
                                else:
                                    logger.warning(f"CALLBACK: Offset G54 não encontrado ou inválido nos dados hash para WCS ativo G54: {hash_state}")
                            else:
                                logger.debug(f"CALLBACK: Ignorando atualização de offset G54 de $# porque WCS ativo é {self.active_wcs}")
                            # TODO: Se precisar suportar outros WCS (G55-G59), adicionar lógica similar aqui
                
                    # Capturar estado do parser para saber o WCS ativo
                    elif eventstring == "on_gcode_parser_stateupdate":
                        # ... (código existente para atualizar self.active_wcs) ...
                        if data and isinstance(data[0], list) and len(data[0]) > 1:
                            parser_state = data[0]
                            # O índice 1 contém o WCS ativo (ex: "54", "55", etc.)
                            # O índice 0 contém o modo de movimento (ex: "1" para G1)
                            # O índice 4 contém o modo de distância (ex: "90" para G90)
                            new_active_wcs = f"G{parser_state[1]}" 
                            new_motion_mode = f"G{parser_state[0]}"
                            new_distance_mode = f"G{parser_state[4]}"

                            if new_active_wcs != self.active_wcs:
                                logger.info(f"CALLBACK: WCS Ativo mudou de {self.active_wcs} para {new_active_wcs}")
                                self.active_wcs = new_active_wcs
                                # Ao mudar o WCS, seria ideal buscar o offset correspondente via $#
                                # ou ter todos os offsets armazenados. Por enquanto, apenas logamos.
                                # self.controller.cnc.grbl.send_immediately("$#") # Cuidado com loops

                            # Atualiza estado interno da aplicação sobre modos G90/G91
                            # Isso garante que a UI e a lógica de movimento estejam sincronizadas
                            # com o estado real do GRBL reportado por $G.
                            if hasattr(self, 'movement_widget'): # Verifica se o widget existe
                                if new_distance_mode == "G90":
                                    if not self.movement_widget.mode_absolute.isChecked():
                                        logger.info("CALLBACK ($G): Sincronizando UI para G90 (Absoluto)")
                                        self.movement_widget.mode_absolute.setChecked(True)
                                        self.movement_widget.mode_relative.setChecked(False)
                                elif new_distance_mode == "G91":
                                     if not self.movement_widget.mode_relative.isChecked():
                                        logger.info("CALLBACK ($G): Sincronizando UI para G91 (Relativo)")
                                        self.movement_widget.mode_absolute.setChecked(False)
                                        self.movement_widget.mode_relative.setChecked(True)
                    
                    elif eventstring == "on_stateupdate":
                        logger.info(f"CALLBACK: Processando 'on_stateupdate'. Dados brutos: {data}") 

                        if len(data) >= 3:
                            state = data[0]
                            mpos_tuple = data[1]  # Posição da Máquina (MPos)
                            # wpos_tuple = data[2] # Posição de Trabalho (WPos) - Ignorando pois está vindo zerado

                            logger.debug(f"CALLBACK DETALHADO: state={state}, mpos={mpos_tuple}") # Removido wpos do log detalhado
                            
                            # Atualiza estado da máquina
                            old_state = self.controller.cnc.machine_status if hasattr(self.controller.cnc, 'machine_status') else None
                            self.controller.cnc.machine_status = state
                            
                            if old_state != state:
                                logger.debug(f"CALLBACK: Estado da máquina mudou de '{old_state}' para '{state}'")
                            
                            # Calcular WPOS a partir de MPOS e do offset armazenado
                            if isinstance(mpos_tuple, (list, tuple)) and len(mpos_tuple) >= 2: 
                                try:
                                    # 1) valores FÍSICOS reportados pelo GRBL
                                    mpos_x_phys = float(mpos_tuple[0])
                                    mpos_y_phys = float(mpos_tuple[1])
                                    mpos_z_phys = float(mpos_tuple[2]) if len(mpos_tuple) > 2 else 0.0

                                    # 2) guarda MPos física para rotinas G10
                                    self.current_mpos = {
                                        'x': mpos_x_phys,
                                        'y': mpos_y_phys,
                                        'z': mpos_z_phys
                                    }

                                    # 3) converte considerando o modo de cinemática
                                    if self.controller.cnc.kinematics_mode == "corexy":
                                        # No modo CoreXY: mpos_x_phys = motor A, mpos_y_phys = motor B
                                        # Converte A,B para coordenadas cartesianas X,Y
                                        x_cart, y_cart = self.controller.cnc._convert_ab_to_xy(mpos_x_phys, mpos_y_phys)

                                        # CORREÇÃO: Converte o offset de coordenadas de motores para cartesianas
                                        off_a = self.current_wcs_offset['x']  # offset motor A
                                        off_b = self.current_wcs_offset['y']  # offset motor B
                                        off_x_cart, off_y_cart = self.controller.cnc._convert_ab_to_xy(off_a, off_b)
                                        off_z_cart = self.current_wcs_offset['z']
                                        
                                        # Aplica inversão lógica se configurada
                                        y_cart_log = -y_cart if self.controller.cnc.invert_y else y_cart
                                        z_cart_log = -mpos_z_phys if self.controller.cnc.invert_z else mpos_z_phys

                                        # Aplica inversão lógica também ao offset para consistência
                                        off_y_cart_log = -off_y_cart if self.controller.cnc.invert_y else off_y_cart
                                        off_z_cart_log = -off_z_cart if self.controller.cnc.invert_z else off_z_cart
                                        
                                        # Agora calcula WPos usando coordenadas cartesianas para ambos
                                        calculated_wpos_x = x_cart - off_x_cart
                                        calculated_wpos_y = y_cart_log - off_y_cart_log
                                        calculated_wpos_z = z_cart_log - off_z_cart_log

                                    else:
                                        # Modo cartesiano (comportamento original)
                                        mpos_y_log = -mpos_y_phys if self.controller.cnc.invert_y else mpos_y_phys
                                        mpos_z_log = -mpos_z_phys if self.controller.cnc.invert_z else mpos_z_phys
                                        off_y_log  = (-self.current_wcs_offset['y']
                                                    if self.controller.cnc.invert_y
                                                    else self.current_wcs_offset['y'])
                                        off_z_log  = (-self.current_wcs_offset['z']
                                                    if self.controller.cnc.invert_z
                                                    else self.current_wcs_offset['z'])
                                        calculated_wpos_x = mpos_x_phys - self.current_wcs_offset['x']
                                        calculated_wpos_y = mpos_y_log  - off_y_log
                                        calculated_wpos_z = mpos_z_log  - off_z_log

                                    new_position = {
                                        'x': calculated_wpos_x,
                                        'y': calculated_wpos_y,
                                        'z': calculated_wpos_z
                                    }

                                    old_position = None
                                    if hasattr(self.controller.cnc, 'current_position'):
                                        old_position = self.controller.cnc.current_position.copy() 
                                        # logger.debug(f"CALLBACK: Posição interna ANTES da atualização: {old_position}") # Log opcional

                                    logger.debug(f"CALLBACK: MPos={mpos_tuple}, Offset={self.current_wcs_offset}, WPos Calculada={new_position}")
                                    logger.debug(f"CALLBACK: Tentando atualizar posição interna (usando WPOS CALCULADA) para: {new_position}")

                                    # Compara new_position (WPos calculada) com old_position
                                    position_changed = (old_position is None) or \
                                                       (abs(old_position['x'] - new_position['x']) > 1e-4) or \
                                                       (abs(old_position['y'] - new_position['y']) > 1e-4) or \
                                                       (abs(old_position.get('z', 0.0) - new_position.get('z', 0.0)) > 1e-4)

                                    if position_changed:
                                        logger.info(f"CALLBACK: POSIÇÃO INTERNA ATUALIZADA (usando WPOS CALCULADA): {old_position} -> {new_position}")
                                        # Atualiza a posição no controlador com a WPos calculada
                                        self.controller.cnc.current_position = new_position 
                                    
                                except (ValueError, TypeError, IndexError) as e:
                                    logger.error(f"CALLBACK: Erro ao processar MPOS ou calcular WPOS: {e}, mpos={mpos_tuple}")
                            else:
                                logger.error(f"CALLBACK: Formato inválido para MPOS: {type(mpos_tuple)}, valor: {mpos_tuple}")

                        else:
                            logger.error(f"CALLBACK: 'on_stateupdate' recebido com dados insuficientes (len={len(data)}). Dados: {data}")

                    # ... (restante do código do callback para outros eventos: on_write, on_read, etc.) ...
                    elif eventstring == "on_write":
                        logger.debug(f"CALLBACK: Comando enviado para GRBL: {data[0] if data else 'vazio'}")
                    # ... (etc.) ...

                # --- INÍCIO DA MODIFICAÇÃO ---
                # Inicializa o GrblStreamer APENAS com o callback
                self.controller.cnc.grbl = GrblStreamer(grbl_callback) 
                # --- FIM DA MODIFICAÇÃO ---

                logger.debug(f"CONEXÃO: Tentando conectar à porta {port} com baudrate 115200")
                # Conecta usando o método cnect()
                self.controller.cnc.grbl.cnect(port, 115200) 
                time.sleep(2.0) 

                if not self.controller.cnc.grbl.connected:
                     logger.error("CONEXÃO: Falha ao estabelecer conexão serial (grbl.connected é False).")
                     raise ConnectionError("Falha ao conectar à porta serial após inicialização.")

                logger.debug("CONEXÃO: Enviando comando de desbloqueio $X")
                self.controller.cnc.grbl.send_immediately("$X")
                time.sleep(0.1) 

                logger.debug("CONEXÃO: Configurando $10=3 para relatório completo de posição")
                self.controller.cnc.grbl.send_immediately("$10=3") # Mantém $10=3 para receber MPos
                time.sleep(0.1)

                # --- INÍCIO DA MODIFICAÇÃO ---
                # Solicitar estado hash logo após conectar para obter offsets
                logger.debug("CONEXÃO: Solicitando estado hash ($#) para obter offsets")
                self.controller.cnc.grbl.send_immediately("$#") 
                time.sleep(0.1)
                # --- FIM DA MODIFICAÇÃO ---

                logger.debug("CONEXÃO: Configurando modo relativo G91")
                self.controller.cnc.grbl.send_immediately("G91")
                time.sleep(0.1)

                logger.debug("CONEXÃO: Iniciando polling de status")
                self.controller.cnc.grbl.poll_start()

                self.controller.cnc.is_connected = True
                self.config.apply_to_cnc(self.controller.cnc)
                self.config.remember_cnc_port(port)
                self.controller.cnc.machine_status = "Idle"  
                self.connect_cnc_btn.setText("Desconectar CNC")
                self.cnc_status.setText("Conectado")
                self.statusBar().showMessage(f"CNC conectada na porta {port}")
                
            except Exception as e:
                # ... (código de tratamento de erro de conexão) ...
                logger.error(f"CONEXÃO: Falha ao conectar ou configurar: {str(e)}", exc_info=True) 
                QMessageBox.critical(self, "Erro", f"Falha ao conectar a CNC: {str(e)}")
                if hasattr(self.controller.cnc, 'grbl') and self.controller.cnc.grbl:
                    try:
                        self.controller.cnc.grbl.disconnect()
                    except: pass
                self.controller.cnc.grbl = None
                self.controller.cnc.is_connected = False
                self.controller.cnc.machine_status = "Erro Conexão"
                self.connect_cnc_btn.setText("Conectar CNC")
                self.cnc_status.setText("Erro Conexão")
                
    def connect_camera(self):
        """Conecta à câmera"""
        if hasattr(self.controller.camera, 'is_connected') and self.controller.camera.is_connected:
            # Interrompe preview antes de liberar a câmera
            self.camera_preview.stop_preview()

            # Desconectar
            self.controller.camera.disconnect()
            self.connect_camera_btn.setText("Conectar Câmera")
            self.statusBar().showMessage("Câmera desconectada")
        else:
            # Conectar
            try:
                camera_id = int(self.camera_id_combo.currentText())
                
                self.statusBar().showMessage(f"Conectando à câmera ID {camera_id}...")
                
                if self.controller.connect_camera(camera_id):
                    self.connect_camera_btn.setText("Desconectar Câmera")
                    self.statusBar().showMessage(f"Câmera ID {camera_id} conectada")
                    self.config.remember_camera_id(camera_id)
                else:
                    QMessageBox.critical(self, "Erro", f"Falha ao conectar à câmera: {self.controller.camera.last_error}")
            except ValueError:
                QMessageBox.warning(self, "Erro", "ID de câmera inválido")
                
    def test_camera(self):
        """Testa a captura de imagem da câmera"""
        if not hasattr(self.controller.camera, 'is_connected') or not self.controller.camera.is_connected:
            QMessageBox.warning(self, "Aviso", "Câmera não conectada")
            return
            
        image = self.controller.camera.capture()
        
        if image is not None:
            # Usa o widget de preview da câmera para exibir a imagem
            self.camera_preview.display_image(image)
            self.statusBar().showMessage("Imagem de teste capturada com sucesso")
        else:
            error_msg = getattr(self.controller.camera, 'last_error', 'Erro desconhecido')
            QMessageBox.warning(self, "Erro", f"Falha ao capturar imagem: {error_msg}")
            
    def update_position_display(self): 
        """Atualiza a exibição da posição atual (agora exibindo WPos calculada)""" 
        if not self.controller.cnc.is_connected: 
            # logger.debug("update_position_display: CNC não conectada.") # Log já existente
            return 
        try: 
            # get_current_position agora retorna a WPos calculada
            position = self.controller.cnc.get_current_position() 
            # logger.debug("update_position_display: posição (WPos calculada) obtida do CNC: %s", position) 
        except Exception as e: 
            logger.error("update_position_display: erro ao obter posição: %s", e) 
            return

        # Comparação para log (opcional, pode ser removido se poluir muito)
        if self.last_logged_position is not None:
            if position == self.last_logged_position:
                pass
                # logger.warning("update_position_display: posição (WPos calculada) inalterada: %s", position)
            else:
                # logger.debug("update_position_display: posição (WPos calculada) mudou de %s para %s", 
                #             self.last_logged_position, position)
                pass
        else:
            #logger.debug("update_position_display: nenhuma posição (WPos calculada) anterior registrada.")
            pass
        
        self.last_logged_position = position.copy()

        # Atualiza os labels da interface com a WPos calculada
        self.x_position.setText(f"{position['x']:.3f} mm")
        self.y_position.setText(f"{position['y']:.3f} mm")
        # -------- NOVO: eixo Z ----------
        if hasattr(self, "z_position"):
            self.z_position.setText(f"{position['z']:.3f} mm")
        self.cnc_status.setText(self.controller.cnc.machine_status)
        
    def add_current_position(self):
        """Adiciona a posição atual à lista"""
        if not self.controller.cnc.is_connected:
            QMessageBox.warning(self, "Aviso", "CNC não conectada")
            return
            
        position_name, ok = QInputDialog.getText(self, "Nova Posição", "Nome da posição:")
        
        if ok and position_name:
            position = self.controller.add_current_position(position_name)
            self.position_list_widget.add_position(position)
            self.statusBar().showMessage(f"Posição '{position_name}' adicionada")
            
    def remove_position(self):
        """Remove a posição selecionada"""
        position = self.position_list_widget.remove_selected_position()
        
        if position:
            self.controller.position_manager.remove_position(position.name)
            self.statusBar().showMessage(f"Posição '{position.name}' removida")
            
    def on_position_selected(self, position):
        """Manipula a seleção de uma posição"""
        # Poderia mover para esta posição, mostrar detalhes, etc.
        self.statusBar().showMessage(f"Posição selecionada: {position.name} ({position.x:.3f}, {position.y:.3f})")
        
    def create_sequence(self):
        """Cria uma nova sequência com as posições atuais"""
        positions = self.position_list_widget.get_all_positions()
        
        if not positions:
            QMessageBox.warning(self, "Aviso", "Adicione pelo menos uma posição")
            return
            
        sequence_name = self.sequence_widget.sequence_name.text()
        if not sequence_name:
            QMessageBox.warning(self, "Aviso", "Digite um nome para a sequência")
            return
            
        self.current_sequence = self.controller.create_sequence(sequence_name, positions)
        self.statusBar().showMessage(f"Sequência '{sequence_name}' criada com {len(positions)} posições")
        self.sequence_widget.sequence_status.setText(f"Criada: {len(positions)} posições")
        
    def run_sequence(self):
        """Executes the current sequence"""
        if not self.current_sequence:
            QMessageBox.warning(self, "Warning", "Create a sequence first")
            return
            
        if not self.controller.cnc.is_connected:
            QMessageBox.warning(self, "Warning", "CNC not connected")
            return
            
        if not hasattr(self.controller.camera, 'is_connected') or not self.controller.camera.is_connected:
            QMessageBox.warning(self, "Warning", "Camera not connected")
            return
            
        # Clear previous results
        self.results_table.setRowCount(0)
        
        # Configure UI for execution
        self.is_running_sequence = True
        self.sequence_widget.run_sequence_btn.setEnabled(False)
        self.sequence_widget.stop_sequence_btn.setEnabled(True)
        self.sequence_widget.sequence_status.setText("Executing...")
        
        # Start execution
        try:
            self.statusBar().showMessage(f"Executing sequence '{self.current_sequence.name}'...")
            # Configura velocidade no controlador baseada na interface
            self.controller.set_feed_rate(self.movement_widget.get_current_feed_rate())
            
            # Use a thread to run the sequence
            self.run_thread = SequenceRunnerThread(self.controller, self.current_sequence.name)
            self.run_thread.image_captured.connect(self.on_sequence_image_captured)
            self.run_thread.sequence_completed.connect(self.on_sequence_completed)
            self.run_thread.sequence_error.connect(self.on_sequence_error)
            self.run_thread.start()
            
        except Exception as e:
            self.statusBar().showMessage(f"Error executing sequence: {str(e)}")
            self.sequence_widget.sequence_status.setText("Error")
            self.on_sequence_completed()

    def on_sequence_image_captured(self, result):
        """Called when an image is captured during sequence execution"""
        position = result["position"]
        image = result["image"]
        timestamp = result["timestamp"]
        
        # Display the image on the existing camera_preview widget
        self.camera_preview.display_image(image)
        # Atualiza a status bar com o nome/posição
        self.statusBar().showMessage(
            f"Position captured: {position.name} ({position.x:.3f}, {position.y:.3f})"
        )
        
        # Add to results table
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        self.results_table.setItem(row, 0, QTableWidgetItem(position.name))
        self.results_table.setItem(row, 1, QTableWidgetItem(time.strftime("%H:%M:%S", time.localtime(timestamp))))
        self.results_table.setItem(row, 2, QTableWidgetItem("Captured"))
            
    def stop_sequence(self):
        """Para a execução da sequência atual"""
        if self.is_running_sequence:
            self.controller.stop_sequence()
            self.statusBar().showMessage("Execução de sequência interrompida")
            self.on_sequence_completed()
        
    def on_sequence_completed(self):
        """Chamado quando a execução da sequência é concluída"""
        self.is_running_sequence = False
        self.sequence_widget.run_sequence_btn.setEnabled(True)
        self.sequence_widget.stop_sequence_btn.setEnabled(False)
        self.sequence_widget.sequence_status.setText("Concluída")
        self.statusBar().showMessage("Execução de sequência concluída")
        
    def on_sequence_error(self, error_message):
        """Chamado quando ocorre um erro durante a execução da sequência"""
        QMessageBox.critical(self, "Erro na Sequência", error_message)
        self.on_sequence_completed()
        
    def save_program(self):
        """Salva o programa de inspeção atual"""
        if not self.current_sequence:
            QMessageBox.warning(self, "Aviso", "Crie uma sequência primeiro")
            return
            
        filename, _ = QFileDialog.getSaveFileName(self, "Salvar Programa", "", "Arquivos JSON (*.json)")
        
        if filename:
            if not filename.endswith('.json'):
                filename += '.json'
                
            if self.controller.save_positions(filename):
                self.statusBar().showMessage(f"Programa salvo em {filename}")
            else:
                QMessageBox.critical(self, "Erro", "Falha ao salvar o programa")
                
    def load_program(self):
        """Carrega um programa de inspeção salvo"""
        filename, _ = QFileDialog.getOpenFileName(self, "Carregar Programa", "", "Arquivos JSON (*.json)")
        
        if filename:
            if self.controller.load_positions(filename):
                # Atualiza a interface
                self.position_list_widget.clear_positions()
                
                # Adiciona posições carregadas à lista
                for name, position in self.controller.position_manager.positions.items():
                    self.position_list_widget.add_position(position)
                    
                # Se há sequências, usa a primeira como atual
                if self.controller.position_manager.sequences:
                    sequence_name = next(iter(self.controller.position_manager.sequences))
                    self.current_sequence = self.controller.position_manager.sequences[sequence_name]
                    self.sequence_widget.sequence_name.setText(sequence_name)
                    self.sequence_widget.sequence_status.setText(f"Carregada: {len(self.current_sequence.positions)} posições")
                    
                self.statusBar().showMessage(f"Programa carregado de {filename}")
            else:
                QMessageBox.critical(self, "Erro", "Falha ao carregar o programa")
                
    #  LIMPEZA GERAL  (Threads, Timers, Dispositivos)
    def _cleanup_resources(self):
        """Para tudo que possa manter o Qt vivo após o fechamento."""
        if getattr(self, "_already_clean", False):
            return                         # evita executar 2×
        self._already_clean = True

        # 1) Sequências em execução
        if getattr(self, "is_running_sequence", False):
            self.controller.stop_sequence()

        # 2) Timers ------------------------------------------------
        for tm_name in ("update_timer",):
            tm = getattr(self, tm_name, None)
            if tm and tm.isActive():
                tm.stop()
        if getattr(self, "camera_preview", None):
            self.camera_preview.stop_preview()

        # 3) QThreads ---------------------------------------------
        for th_name in ("run_thread", "map_thread", "_move_thread"):
            th = getattr(self, th_name, None)
            if th and th.isRunning():
                th.requestInterruption()
                th.quit()
                th.wait(2000)             # aguarda até 2 s

        # 4) Thread de status do GRBL dentro do controlador CNC
        if getattr(self.controller.cnc, "running", False):
            self.controller.cnc.running = False
            if getattr(self.controller.cnc, "status_thread", None):
                self.controller.cnc.status_thread.join(timeout=2)

        # 5) grbl-streamer (poll thread) --------------------------
        if getattr(self.controller.cnc, "grbl", None):
            try:
                self.controller.cnc.grbl.poll_stop()
                self.controller.cnc.grbl.disconnect()   # fecha serial + join
            except Exception:
                pass

        # 6) Dispositivos -----------------------------------------
        if getattr(self.controller.camera, "is_connected", False):
            self.controller.camera.disconnect()
        if getattr(self.controller.cnc, "is_connected", False):
            self.controller.cnc.disconnect()

    # closeEvent agora só dispara a limpeza
    def closeEvent(self, event):
        self._cleanup_resources()
        event.accept()

class SequenceRunnerThread(QThread):
    """Thread para executar uma sequência de inspeção"""
    image_captured = pyqtSignal(dict)  # Emite resultados da captura
    sequence_completed = pyqtSignal()  # Emite quando a sequência é concluída
    sequence_error = pyqtSignal(str)   # Emite quando ocorre um erro
    
    def __init__(self, controller, sequence_name):
        super().__init__()
        self.controller = controller
        self.sequence_name = sequence_name
        
    def run(self):
        try:
            # Execute a sequência e processe os resultados
            def process_result(result):
                self.image_captured.emit(result)
                
            self.controller.run_sequence(self.sequence_name, process_result)
            self.sequence_completed.emit()
            
        except Exception as e:
            self.sequence_error.emit(str(e))

class MapGeneratorThread(QThread):
    """
    Thread responsável por percorrer a grade, movimentar a CNC e capturar
    as imagens sem travar a GUI.
    
    Otimizações de velocidade:
    - Movimento direto sem espera inicial desnecessária
    - Delay mínimo de estabilização configurável
    - Usa feed_rate para maximizar velocidade de movimento
    """
    progress = pyqtSignal(int, int)       # imagens_capturadas, total
    image_captured = pyqtSignal(object)   # cv2 image (opcional para preview)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, controller, origin, end, sx, sy, folder, prog_name, feed_rate=1000, capture_delay_ms=100):
        super().__init__()
        self.ctrl = controller
        self.origin = origin
        self.end = end
        self.sx = sx
        self.sy = sy
        self.folder = folder
        self.prog_name = prog_name
        # Usa no mínimo 2000 mm/min para movimento rápido
        self.feed_rate = max(feed_rate, 2000)
        # Delay mínimo de 50ms para estabilização
        self.capture_delay_ms = max(capture_delay_ms, 50)

    def run(self):
        log = logging.getLogger("MapGeneratorThread")
        backlight_was_on = False  # Para restaurar estado original ao final
        
        try:
            points = list(self.ctrl._grid_points(self.origin, self.end,
                                             self.sx, self.sy))
            total = len(points)
            os.makedirs(self.folder, exist_ok=True)

            # Converte delay de ms para segundos
            delay_sec = self.capture_delay_ms / 1000.0
            log.info(f"MapGeneratorThread: Delay={self.capture_delay_ms}ms, FeedRate={self.feed_rate}mm/min, Total={total} pontos")

            # ========== CONTROLE DO BACKLIGHT - INÍCIO ==========
            # Liga o backlight 2 segundos antes de iniciar as capturas
            if hasattr(self.ctrl.cnc, 'backlight_set'):
                # Salva estado anterior para restaurar depois
                backlight_was_on = getattr(self.ctrl.cnc, 'backlight_on', False)
                
                log.info("MapGeneratorThread: Ligando backlight (Y0.7)")
                self.ctrl.cnc.backlight_turn_on()
                
                # Aguarda 2 segundos para estabilização da iluminação
                log.info("MapGeneratorThread: Aguardando 2s para estabilização do backlight")
                time.sleep(2.0)
            # ========== CONTROLE DO BACKLIGHT - FIM ==========

            # Descarta frames antigos do buffer da câmera antes de iniciar
            for _ in range(3):
                self.ctrl.camera.capture()

            captured = 0
            last_x, last_y = None, None
            
            for r, col, x, y in points:
                if self.isInterruptionRequested():
                    log.warning("Mapa cancelado pelo usuário")
                    # Desliga backlight antes de sair
                    self._turn_off_backlight(log, backlight_was_on)
                    self.error.emit("Operação cancelada")
                    return
                
                # Move apenas se a posição mudou
                need_move = (last_x is None or last_y is None or 
                            abs(x - last_x) > 0.01 or abs(y - last_y) > 0.01)
                
                if need_move:
                    self.ctrl.cnc.move_to_absolute_position(x, y, feed_rate=self.feed_rate)
                    self.ctrl.cnc.wait_for_idle(tolerance=2, timeout=15)
                    last_x, last_y = x, y
                    
                    # Aguarda estabilização apenas se houve movimento
                    if delay_sec > 0:
                        time.sleep(delay_sec)

                # Captura imagem
                img = self.ctrl.camera.capture()
                if img is not None:
                    fname = f"{self.prog_name}_r{r:03d}_c{col:03d}.png"
                    cv2.imwrite(os.path.join(self.folder, fname), img)
                    self.image_captured.emit(img)
                else:
                    log.warning(f"Falha ao capturar imagem em r={r}, c={col}")
                    
                captured += 1
                self.progress.emit(captured, total)

            log.info(f"MapGeneratorThread: Finalizado - {captured} imagens capturadas")
            
            # ========== DESLIGA BACKLIGHT APÓS 2 SEGUNDOS ==========
            self._turn_off_backlight(log, backlight_was_on)
            
            self.finished.emit()
        except Exception as exc:
            log.exception("Erro na geração do mapa")
            # Garante que o backlight seja desligado em caso de erro
            self._turn_off_backlight(log, backlight_was_on)
            self.error.emit(str(exc))
    
    def _turn_off_backlight(self, log, restore_previous_state: bool):
        """
        Desliga o backlight após aguardar 2 segundos.
        
        Args:
            log: Logger para registrar mensagens
            restore_previous_state: Se True, restaura o estado anterior do backlight
        """
        if not hasattr(self.ctrl.cnc, 'backlight_set'):
            return
        
        try:
            # Aguarda 2 segundos antes de desligar
            log.info("MapGeneratorThread: Aguardando 2s antes de desligar backlight")
            time.sleep(2.0)
            
            if restore_previous_state:
                # Restaura estado anterior
                log.info(f"MapGeneratorThread: Restaurando backlight para estado anterior: {'ON' if restore_previous_state else 'OFF'}")
                self.ctrl.cnc.backlight_set(restore_previous_state)
            else:
                # Desliga
                log.info("MapGeneratorThread: Desligando backlight (Y0.7)")
                self.ctrl.cnc.backlight_turn_off()
        except Exception as e:
            log.error(f"MapGeneratorThread: Erro ao controlar backlight: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AOIControllerApp()
    window.show()
    sys.exit(app.exec())