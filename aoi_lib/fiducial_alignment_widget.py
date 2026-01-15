"""
fiducial_alignment_widget.py
----------------------------
Widget PyQt6 para alinhamento de fiduciais na inspeção de stencil.

Funcionalidades:
- Captura de templates de fiduciais A e B
- Busca automática de fiduciais em imagem/mosaico
- Posicionamento interativo do Gerber (clique e arraste)
- Cálculo de transformação (translação, rotação, escala)
- Ajuste fino manual da transformação
- Preview visual do alinhamento

Integração com o módulo fiducial_alignment.py
"""

import cv2
import numpy as np
import logging
from typing import Optional, List, Tuple, Callable
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QGroupBox, QPushButton, QLabel, QSpinBox, QDoubleSpinBox,
    QSlider, QMessageBox, QSizePolicy, QScrollArea, QFrame,
    QTabWidget, QFileDialog, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QPointF, QRectF, QTimer
from PyQt6.QtGui import (
    QImage, QPixmap, QPainter, QPen, QBrush, QColor, 
    QTransform, QMouseEvent, QWheelEvent
)

from .fiducial_alignment import (
    FiducialTemplate, FiducialMatchResult,
    AlignmentTransform, create_alignment_preview
)
from .fiducial_alignment_adapter import FiducialAlignmentAdapter

log = logging.getLogger(__name__)

# Parser Gerber para detecção automática de fiduciais
try:
    from .gerber_parser import (
        GerberParser, ParsedGerber, FiducialCandidate, GerberBounds
    )
    HAS_GERBER_PARSER = True
except ImportError:
    HAS_GERBER_PARSER = False
    log.warning("gerber_parser não disponível - detecção automática de fiduciais desabilitada")


# ============================================================================
#  WIDGET DE VISUALIZAÇÃO COM ZOOM/PAN E INTERAÇÃO
# ============================================================================

class AlignmentImageView(QLabel):
    """
    Widget de visualização de imagem com:
    - Zoom com scroll do mouse
    - Pan com clique do meio ou Ctrl+clique
    - Clique para selecionar ponto de fiducial
    - Arraste para posicionar Gerber
    """
    
    # Sinais
    pointClicked = pyqtSignal(float, float)     # Clique para selecionar ponto (coordenadas da imagem original)
    positionDragged = pyqtSignal(float, float)  # Arraste de posição (delta X, delta Y)
    zoomChanged = pyqtSignal(float)             # Mudança de zoom
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 300)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("QLabel { background-color: #1e1e1e; border: 1px solid #444; }")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)
        
        # Imagem original
        self._image: Optional[np.ndarray] = None
        self._pixmap: Optional[QPixmap] = None
        
        # Estado de visualização
        self._zoom = 1.0
        self._offset = QPointF(0, 0)  # Offset do pan
        
        # Estado de interação
        self._dragging = False
        self._last_pos = QPoint()
        self._mode = "pan"  # "pan", "select", "drag_gerber"
        
        # Overlay do Gerber (para visualização)
        self._gerber_overlay: Optional[QPixmap] = None
        self._gerber_offset = QPointF(0, 0)
        self._gerber_scale = 1.0
        self._gerber_angle = 0.0
        
        # Marcadores de fiduciais
        self._fiducial_markers: List[Tuple[float, float, str, bool]] = []  # (x, y, name, found)
    
    def set_image(self, image: np.ndarray):
        """Define imagem BGR para exibição."""
        if image is None:
            self._image = None
            self._pixmap = None
            self.clear()
            return
        
        self._image = image.copy()
        
        # Converte para QPixmap
        if len(image.shape) == 2:
            # Grayscale
            h, w = image.shape
            qimg = QImage(image.data, w, h, w, QImage.Format.Format_Grayscale8)
        else:
            # BGR -> RGB
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            h, w = rgb.shape[:2]
            qimg = QImage(rgb.data, w, h, w * 3, QImage.Format.Format_RGB888)
        
        self._pixmap = QPixmap.fromImage(qimg)
        self._update_display()
    
    def set_gerber_overlay(self, overlay: Optional[QPixmap]):
        """Define overlay do Gerber para visualização."""
        self._gerber_overlay = overlay
        self._update_display()
    
    def set_gerber_transform(self, offset_x: float, offset_y: float, 
                              scale: float = 1.0, angle: float = 0.0):
        """Define transformação do overlay Gerber."""
        self._gerber_offset = QPointF(offset_x, offset_y)
        self._gerber_scale = scale
        self._gerber_angle = angle
        self._update_display()
    
    def set_fiducial_markers(self, markers: List[Tuple[float, float, str, bool]]):
        """Define marcadores de fiduciais: [(x, y, name, found), ...]"""
        self._fiducial_markers = markers
        self._update_display()
    
    def set_mode(self, mode: str):
        """Define modo de interação: 'pan', 'select', 'drag_gerber'"""
        self._mode = mode
        if mode == "pan":
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        elif mode == "select":
            self.setCursor(Qt.CursorShape.CrossCursor)
        elif mode == "drag_gerber":
            self.setCursor(Qt.CursorShape.SizeAllCursor)
    
    def fit_in_view(self):
        """Ajusta zoom para mostrar toda a imagem."""
        if self._pixmap is None:
            return
        
        img_w, img_h = self._pixmap.width(), self._pixmap.height()
        view_w, view_h = self.width() - 10, self.height() - 10
        
        scale_x = view_w / img_w if img_w > 0 else 1.0
        scale_y = view_h / img_h if img_h > 0 else 1.0
        self._zoom = min(scale_x, scale_y, 1.0)  # Não ultrapassa 100%
        self._offset = QPointF(0, 0)
        self._update_display()
        self.zoomChanged.emit(self._zoom)
    
    def zoom_to(self, zoom: float):
        """Define zoom específico."""
        self._zoom = max(0.1, min(5.0, zoom))
        self._update_display()
        self.zoomChanged.emit(self._zoom)
    
    def _update_display(self):
        """Atualiza renderização da imagem."""
        if self._pixmap is None:
            self.clear()
            return
        
        # Cria pixmap final com transformações
        view_w, view_h = self.width(), self.height()
        result = QPixmap(view_w, view_h)
        result.fill(QColor("#1e1e1e"))
        
        painter = QPainter(result)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calcula posição centralizada com offset
        scaled_w = int(self._pixmap.width() * self._zoom)
        scaled_h = int(self._pixmap.height() * self._zoom)
        
        x = (view_w - scaled_w) / 2 + self._offset.x()
        y = (view_h - scaled_h) / 2 + self._offset.y()
        
        # Desenha imagem principal
        painter.drawPixmap(
            int(x), int(y), scaled_w, scaled_h,
            self._pixmap
        )
        
        # Desenha overlay do Gerber
        if self._gerber_overlay is not None:
            painter.save()
            painter.setOpacity(0.5)
            
            # Aplica transformação do Gerber
            gerber_x = x + self._gerber_offset.x() * self._zoom
            gerber_y = y + self._gerber_offset.y() * self._zoom
            
            transform = QTransform()
            transform.translate(gerber_x, gerber_y)
            transform.scale(self._gerber_scale * self._zoom, self._gerber_scale * self._zoom)
            transform.rotate(self._gerber_angle)
            
            painter.setTransform(transform)
            painter.drawPixmap(0, 0, self._gerber_overlay)
            painter.restore()
        
        # Desenha marcadores de fiduciais
        for fx, fy, name, found in self._fiducial_markers:
            # Converte coordenadas da imagem para coordenadas da view
            vx = x + fx * self._zoom
            vy = y + fy * self._zoom
            
            color = QColor("#00ff00") if found else QColor("#ff0000")
            
            # Desenha cruz
            pen = QPen(color, 2)
            painter.setPen(pen)
            painter.drawLine(int(vx - 10), int(vy), int(vx + 10), int(vy))
            painter.drawLine(int(vx), int(vy - 10), int(vx), int(vy + 10))
            
            # Desenha nome
            painter.drawText(int(vx + 12), int(vy - 5), name)
        
        painter.end()
        self.setPixmap(result)
    
    def _view_to_image_coords(self, view_x: float, view_y: float) -> Tuple[float, float]:
        """Converte coordenadas da view para coordenadas da imagem original."""
        if self._pixmap is None:
            return 0, 0
        
        view_w, view_h = self.width(), self.height()
        scaled_w = self._pixmap.width() * self._zoom
        scaled_h = self._pixmap.height() * self._zoom
        
        x = (view_w - scaled_w) / 2 + self._offset.x()
        y = (view_h - scaled_h) / 2 + self._offset.y()
        
        img_x = (view_x - x) / self._zoom
        img_y = (view_y - y) / self._zoom
        
        return img_x, img_y
    
    # -------------------------------------------------------------------------
    #  EVENTOS DE MOUSE
    # -------------------------------------------------------------------------
    
    def mousePressEvent(self, event: QMouseEvent):
        pos = event.position()
        button = event.button()
        
        if button == Qt.MouseButton.MiddleButton or \
           (button == Qt.MouseButton.LeftButton and 
            event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            # Inicia pan
            self._dragging = True
            self._last_pos = pos.toPoint()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        
        elif button == Qt.MouseButton.LeftButton:
            if self._mode == "select":
                # Emite clique para seleção de ponto
                img_x, img_y = self._view_to_image_coords(pos.x(), pos.y())
                self.pointClicked.emit(img_x, img_y)
            
            elif self._mode == "drag_gerber":
                # Inicia arraste do Gerber
                self._dragging = True
                self._last_pos = pos.toPoint()
            
            elif self._mode == "pan":
                self._dragging = True
                self._last_pos = pos.toPoint()
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragging:
            pos = event.position().toPoint()
            delta = pos - self._last_pos
            self._last_pos = pos
            
            if self._mode == "drag_gerber":
                # Arrasta overlay do Gerber
                self.positionDragged.emit(delta.x() / self._zoom, delta.y() / self._zoom)
            else:
                # Pan da view
                self._offset += QPointF(delta.x(), delta.y())
                self._update_display()
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._dragging:
            self._dragging = False
            if self._mode == "pan":
                self.setCursor(Qt.CursorShape.OpenHandCursor)
            elif self._mode == "select":
                self.setCursor(Qt.CursorShape.CrossCursor)
            elif self._mode == "drag_gerber":
                self.setCursor(Qt.CursorShape.SizeAllCursor)
    
    def wheelEvent(self, event: QWheelEvent):
        # Zoom com scroll
        delta = event.angleDelta().y()
        factor = 1.1 if delta > 0 else 0.9
        
        # Zoom em torno do ponto do mouse
        pos = event.position()
        old_img_x, old_img_y = self._view_to_image_coords(pos.x(), pos.y())
        
        self._zoom = max(0.1, min(5.0, self._zoom * factor))
        
        # Ajusta offset para manter ponto sob o mouse
        new_img_x, new_img_y = self._view_to_image_coords(pos.x(), pos.y())
        self._offset.setX(self._offset.x() + (new_img_x - old_img_x) * self._zoom)
        self._offset.setY(self._offset.y() + (new_img_y - old_img_y) * self._zoom)
        
        self._update_display()
        self.zoomChanged.emit(self._zoom)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_display()


# ============================================================================
#  WIDGET DE CONFIGURAÇÃO DE FIDUCIAL INDIVIDUAL
# ============================================================================

class FiducialConfigPanel(QGroupBox):
    """Painel de configuração para um fiducial."""
    
    templateCaptured = pyqtSignal(str)   # Nome do fiducial
    testRequested = pyqtSignal(str)      # Nome do fiducial
    parametersChanged = pyqtSignal()
    
    def __init__(self, name: str = "Fiducial A", parent=None):
        super().__init__(name, parent)
        self._name = name
        self._template: Optional[FiducialTemplate] = None
        self._build_ui()
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        
        # Parâmetros
        form = QFormLayout()
        
        self.spin_window = QSpinBox()
        self.spin_window.setRange(20, 200)
        self.spin_window.setValue(50)
        self.spin_window.setSuffix(" px")
        form.addRow("Janela:", self.spin_window)
        
        self.spin_radius = QSpinBox()
        self.spin_radius.setRange(10, 500)
        self.spin_radius.setValue(100)
        self.spin_radius.setSuffix(" px")
        form.addRow("Raio de busca:", self.spin_radius)
        
        self.spin_threshold = QSpinBox()
        self.spin_threshold.setRange(50, 99)
        self.spin_threshold.setValue(70)
        self.spin_threshold.setSuffix(" %")
        form.addRow("Similaridade mín.:", self.spin_threshold)
        
        layout.addLayout(form)
        
        # Preview do template
        self.lbl_template = QLabel("Sem template")
        self.lbl_template.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_template.setMinimumSize(80, 80)
        self.lbl_template.setStyleSheet(
            "QLabel { background: #263238; border: 1px solid #555; }"
        )
        layout.addWidget(self.lbl_template)
        
        # Status
        self.lbl_status = QLabel("—")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setStyleSheet("padding: 4px;")
        layout.addWidget(self.lbl_status)
        
        # Botões
        btn_layout = QHBoxLayout()
        
        self.btn_capture = QPushButton("Capturar")
        self.btn_capture.clicked.connect(lambda: self.templateCaptured.emit(self._name))
        btn_layout.addWidget(self.btn_capture)
        
        self.btn_test = QPushButton("Testar")
        self.btn_test.clicked.connect(lambda: self.testRequested.emit(self._name))
        btn_layout.addWidget(self.btn_test)
        
        layout.addLayout(btn_layout)
        
        # Conexões
        self.spin_window.valueChanged.connect(self._on_params_changed)
        self.spin_radius.valueChanged.connect(self._on_params_changed)
        self.spin_threshold.valueChanged.connect(self._on_params_changed)
    
    def set_template(self, template: FiducialTemplate):
        """Define template associado."""
        self._template = template
        
        # Atualiza UI com valores do template
        self.spin_window.setValue(template.window_size)
        self.spin_radius.setValue(template.search_radius)
        self.spin_threshold.setValue(int(template.threshold))
        
        # Mostra preview se disponível
        if template.template_bgr is not None:
            self._show_template_preview(template.template_bgr)
        else:
            self.lbl_template.setText("Sem template")
    
    def get_parameters(self) -> dict:
        """Retorna parâmetros atuais."""
        return {
            "window_size": self.spin_window.value(),
            "search_radius": self.spin_radius.value(),
            "threshold": self.spin_threshold.value(),
        }
    
    def update_status(self, result: FiducialMatchResult):
        """Atualiza status com resultado de match."""
        if result.found:
            self.lbl_status.setText(
                f"OK {result.similarity:.1f}%  Δ=({result.offset_x:.0f}, {result.offset_y:.0f})"
            )
            self.lbl_status.setStyleSheet("background: #C8E6C9; padding: 4px;")
        else:
            self.lbl_status.setText(f"Falha: {result.similarity:.1f}%")
            self.lbl_status.setStyleSheet("background: #FFCDD2; padding: 4px;")
    
    def _show_template_preview(self, img_bgr: np.ndarray):
        """Mostra preview do template."""
        h, w = img_bgr.shape[:2]
        rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        qimg = QImage(rgb.data, w, h, w * 3, QImage.Format.Format_RGB888)
        pix = QPixmap.fromImage(qimg)
        pix = pix.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio,
                         Qt.TransformationMode.SmoothTransformation)
        self.lbl_template.setPixmap(pix)
    
    def _on_params_changed(self):
        if self._template:
            self._template.window_size = self.spin_window.value()
            self._template.search_radius = self.spin_radius.value()
            self._template.threshold = self.spin_threshold.value()
        self.parametersChanged.emit()


# ============================================================================
#  WIDGET PRINCIPAL DE ALINHAMENTO
# ============================================================================

class FiducialAlignmentWidget(QWidget):
    """
    Widget principal para alinhamento de fiduciais.
    
    Integra:
    - Visualização da imagem/mosaico
    - Configuração de 2 fiduciais (A e B)
    - Controles de transformação manual
    - Botões de busca automática e alinhamento
    """
    
    # Sinais
    alignmentComplete = pyqtSignal(object)  # AlignmentTransform
    alignmentCancelled = pyqtSignal()
    
    def __init__(self, parent=None, adapter: Optional[FiducialAlignmentAdapter] = None):
        """
        Inicializa widget de alinhamento de fiduciais.

        Args:
            parent: Widget pai
            adapter: Adapter de alinhamento (opcional, cria um novo se não fornecido)
        """
        super().__init__(parent)

        # Dependency injection do adapter (ou cria um novo)
        self.adapter = adapter or FiducialAlignmentAdapter()
        self._current_image: Optional[np.ndarray] = None
        self._frame_callback: Optional[Callable[[], np.ndarray]] = None

        self._build_ui()
        self._setup_fiducials()
    
    def _build_ui(self):
        main_layout = QHBoxLayout(self)
        
        # ------ Painel esquerdo: visualização ------
        left_panel = QVBoxLayout()
        
        self.image_view = AlignmentImageView()
        left_panel.addWidget(self.image_view, 1)
        
        # Controles de zoom
        zoom_layout = QHBoxLayout()
        zoom_layout.addWidget(QLabel("Zoom:"))
        
        self.slider_zoom = QSlider(Qt.Orientation.Horizontal)
        self.slider_zoom.setRange(10, 300)
        self.slider_zoom.setValue(100)
        self.slider_zoom.valueChanged.connect(
            lambda v: self.image_view.zoom_to(v / 100.0)
        )
        zoom_layout.addWidget(self.slider_zoom)
        
        self.lbl_zoom = QLabel("100%")
        zoom_layout.addWidget(self.lbl_zoom)
        
        btn_fit = QPushButton("Ajustar")
        btn_fit.clicked.connect(self.image_view.fit_in_view)
        zoom_layout.addWidget(btn_fit)
        
        left_panel.addLayout(zoom_layout)
        
        main_layout.addLayout(left_panel, 2)
        
        # ------ Painel direito: controles ------
        right_panel = QVBoxLayout()
        
        # Tabs para fiduciais e transformação
        self.tabs = QTabWidget()
        
        # Tab 1: Fiduciais
        tab_fid = QWidget()
        tab_fid_layout = QVBoxLayout(tab_fid)
        
        # Fiducial A
        self.panel_fid_a = FiducialConfigPanel("Fiducial A")
        self.panel_fid_a.templateCaptured.connect(self._on_capture_template)
        self.panel_fid_a.testRequested.connect(self._on_test_fiducial)
        tab_fid_layout.addWidget(self.panel_fid_a)
        
        # Fiducial B
        self.panel_fid_b = FiducialConfigPanel("Fiducial B")
        self.panel_fid_b.templateCaptured.connect(self._on_capture_template)
        self.panel_fid_b.testRequested.connect(self._on_test_fiducial)
        tab_fid_layout.addWidget(self.panel_fid_b)
        
        # Botões de ação
        btn_load_gerber = QPushButton("📁 Carregar Gerber")
        btn_load_gerber.clicked.connect(self._load_gerber_file)
        if not HAS_GERBER_PARSER:
            btn_load_gerber.setEnabled(False)
            btn_load_gerber.setToolTip("Parser Gerber não disponível")
        tab_fid_layout.addWidget(btn_load_gerber)
        
        btn_search = QPushButton("🔍 Buscar Fiduciais")
        btn_search.clicked.connect(self._search_all_fiducials)
        tab_fid_layout.addWidget(btn_search)
        
        btn_calc = QPushButton("📐 Calcular Alinhamento")
        btn_calc.clicked.connect(self._calculate_alignment)
        tab_fid_layout.addWidget(btn_calc)
        
        tab_fid_layout.addStretch()
        self.tabs.addTab(tab_fid, "Fiduciais")
        
        # Tab 2: Ajuste Manual
        tab_manual = QWidget()
        tab_manual_layout = QVBoxLayout(tab_manual)
        
        # Controles de transformação
        transform_group = QGroupBox("Transformação Manual")
        transform_layout = QFormLayout(transform_group)
        
        self.spin_tx = QDoubleSpinBox()
        self.spin_tx.setRange(-10000, 10000)
        self.spin_tx.setDecimals(1)
        self.spin_tx.setSuffix(" px")
        transform_layout.addRow("Translação X:", self.spin_tx)
        
        self.spin_ty = QDoubleSpinBox()
        self.spin_ty.setRange(-10000, 10000)
        self.spin_ty.setDecimals(1)
        self.spin_ty.setSuffix(" px")
        transform_layout.addRow("Translação Y:", self.spin_ty)
        
        self.spin_angle = QDoubleSpinBox()
        self.spin_angle.setRange(-180, 180)
        self.spin_angle.setDecimals(2)
        self.spin_angle.setSuffix("°")
        transform_layout.addRow("Rotação:", self.spin_angle)
        
        self.spin_scale = QDoubleSpinBox()
        self.spin_scale.setRange(0.1, 10.0)
        self.spin_scale.setDecimals(4)
        self.spin_scale.setValue(1.0)
        transform_layout.addRow("Escala:", self.spin_scale)
        
        tab_manual_layout.addWidget(transform_group)
        
        # Modo de interação
        mode_group = QGroupBox("Modo de Interação")
        mode_layout = QVBoxLayout(mode_group)
        
        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["Pan/Zoom", "Selecionar Ponto", "Arrastar Gerber"])
        self.combo_mode.currentIndexChanged.connect(self._on_mode_changed)
        mode_layout.addWidget(self.combo_mode)
        
        tab_manual_layout.addWidget(mode_group)
        
        tab_manual_layout.addStretch()
        self.tabs.addTab(tab_manual, "Ajuste Manual")
        
        right_panel.addWidget(self.tabs)
        
        # Botões finais
        btn_layout = QHBoxLayout()
        
        btn_apply = QPushButton("✓ Aplicar Alinhamento")
        btn_apply.setStyleSheet("background: #4CAF50; color: white; font-weight: bold;")
        btn_apply.clicked.connect(self._apply_alignment)
        btn_layout.addWidget(btn_apply)
        
        btn_cancel = QPushButton("✕ Cancelar")
        btn_cancel.clicked.connect(self.alignmentCancelled.emit)
        btn_layout.addWidget(btn_cancel)
        
        right_panel.addLayout(btn_layout)
        
        main_layout.addLayout(right_panel, 1)
        
        # Conexões
        self.image_view.zoomChanged.connect(
            lambda z: (self.slider_zoom.setValue(int(z * 100)),
                      self.lbl_zoom.setText(f"{z*100:.0f}%"))
        )
        self.image_view.pointClicked.connect(self._on_point_clicked)
        self.image_view.positionDragged.connect(self._on_position_dragged)
        
        # Conexões de transformação manual
        self.spin_tx.valueChanged.connect(self._on_transform_changed)
        self.spin_ty.valueChanged.connect(self._on_transform_changed)
        self.spin_angle.valueChanged.connect(self._on_transform_changed)
        self.spin_scale.valueChanged.connect(self._on_transform_changed)
    
    def _setup_fiducials(self):
        """Configura fiduciais padrão usando o adapter."""
        # Cria templates legados para compatibilidade com a UI
        fid_a = FiducialTemplate(
            name="Fiducial A",
            gerber_x=0, gerber_y=0,
            window_size=50, search_radius=100, threshold=70
        )
        fid_b = FiducialTemplate(
            name="Fiducial B",
            gerber_x=0, gerber_y=0,
            window_size=50, search_radius=100, threshold=70
        )

        # Adiciona ao adapter
        self.adapter.add_template(fid_a)
        self.adapter.add_template(fid_b)

        # Atualiza painéis
        self.panel_fid_a.set_template(fid_a)
        self.panel_fid_b.set_template(fid_b)
    
    # -------------------------------------------------------------------------
    #  MÉTODOS PÚBLICOS
    # -------------------------------------------------------------------------
    
    def set_image(self, image: np.ndarray):
        """Define imagem para alinhamento (ex: mosaico capturado)."""
        self._current_image = image
        self.image_view.set_image(image)
        self.image_view.fit_in_view()
    
    def set_frame_callback(self, callback: Callable[[], np.ndarray]):
        """Define callback para obter frame da câmera (para captura de template)."""
        self._frame_callback = callback
    
    def set_gerber_overlay(self, overlay: QPixmap):
        """Define overlay do Gerber para visualização."""
        self.image_view.set_gerber_overlay(overlay)
    
    def set_fiducial_gerber_positions(self, pos_a: Tuple[float, float],
                                       pos_b: Tuple[float, float]):
        """Define posições dos fiduciais no Gerber."""
        # O adapter gerencia internamente as posições Gerber
        # Este método é para compatibilidade com código legado
        log.debug(f"Posições Gerber definidas: A={pos_a}, B={pos_b}")
    
    def get_transform(self) -> Optional[AlignmentTransform]:
        """Retorna transformação atual do adapter."""
        return self.adapter.get_legacy_transform()
    
    # -------------------------------------------------------------------------
    #  HANDLERS DE CAPTURA E TESTE
    # -------------------------------------------------------------------------
    
    def _on_capture_template(self, name: str):
        """Captura template de fiducial usando o adapter."""
        frame = None

        if self._frame_callback:
            frame = self._frame_callback()
        elif self._current_image is not None:
            # Usa imagem atual com seleção de ponto
            QMessageBox.information(
                self, "Captura",
                f"Clique no centro do {name} na imagem para capturar o template."
            )
            self._pending_capture = name
            self.combo_mode.setCurrentIndex(1)  # Modo seleção
            return

        if frame is None:
            QMessageBox.warning(self, "Erro", "Nenhuma imagem disponível para captura.")
            return

        # Obtém template legado atual e captura usando adapter
        template = self.panel_fid_a._template if name == "Fiducial A" else self.panel_fid_b._template

        if template and self.adapter.capture_template(template, frame):
            panel = self.panel_fid_a if name == "Fiducial A" else self.panel_fid_b
            panel.set_template(template)
            QMessageBox.information(self, "Sucesso", f"{name} capturado com sucesso!")
    
    def _on_test_fiducial(self, name: str):
        """Testa busca de fiducial usando o adapter."""
        if self._current_image is None:
            QMessageBox.warning(self, "Erro", "Nenhuma imagem carregada.")
            return

        template = self.panel_fid_a._template if name == "Fiducial A" else self.panel_fid_b._template

        if template is None or template.template_gray is None:
            QMessageBox.warning(self, "Erro", f"Capture o {name} primeiro.")
            return

        # Busca fiducial usando adapter
        results = self.adapter.locate_fiducials(self._current_image)

        # Encontra o resultado correspondente
        index = 0 if name == "Fiducial A" else 1
        if index < len(results):
            result = results[index]
            panel = self.panel_fid_a if name == "Fiducial A" else self.panel_fid_b
            panel.update_status(result)

            # Atualiza marcadores na view
            self._update_fiducial_markers_from_results(results)
    
    def _load_gerber_file(self):
        """Carrega arquivo Gerber e detecta candidatos a fiduciais."""
        if not HAS_GERBER_PARSER:
            QMessageBox.warning(
                self, "Erro",
                "Parser Gerber não disponível."
            )
            return
        
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Carregar Arquivo Gerber",
            "", "Gerber Files (*.gbr *.ger);;All Files (*)"
        )
        
        if not filepath:
            return
        
        # Parsear arquivo
        parser = GerberParser()
        result = parser.parse_file(filepath)
        
        if result.error:
            QMessageBox.critical(
                self, "Erro no Parsing",
                f"Erro ao processar arquivo Gerber:\n{result.error}"
            )
            return
        
        # Verificar candidatos
        if not result.fiducial_candidates:
            QMessageBox.warning(
                self, "Nenhum Fiducial Encontrado",
                f"O arquivo foi processado com sucesso:\n"
                f"- {result.stats.total_objects} objetos\n"
                f"- {result.stats.circles} círculos\n\n"
                f"Porém nenhum candidato a fiducial foi identificado.\n"
                f"Fiduciais típicos são círculos de 1-2mm nos cantos do stencil."
            )
            return
        
        # Obter os 2 melhores candidatos
        suggested = parser.get_suggested_fiducials(2)
        
        if len(suggested) < 2:
            QMessageBox.warning(
                self, "Poucos Candidatos",
                f"Apenas {len(suggested)} candidato(s) encontrado(s).\n"
                f"São necessários pelo menos 2 fiduciais para alinhamento."
            )
            return
        
        # Configurar fiduciais A e B
        fid_a = self.panel_fid_a._template
        fid_b = self.panel_fid_b._template

        if fid_a and fid_b:
            # Usar posições dos candidatos como coordenadas Gerber
            fid_a.gerber_x = suggested[0].x_mm
            fid_a.gerber_y = suggested[0].y_mm
            fid_b.gerber_x = suggested[1].x_mm
            fid_b.gerber_y = suggested[1].y_mm

            # Atualiza adapter com novas coordenadas
            self.adapter._fiducial_templates.clear()
            self.adapter.add_template(fid_a)
            self.adapter.add_template(fid_b)

            self.panel_fid_a.set_template(fid_a)
            self.panel_fid_b.set_template(fid_b)
        
        # Guardar informações do Gerber
        self._gerber_result = result
        self._gerber_bounds = result.stats.bounds
        
        # Mostrar resumo
        corners = []
        for c in suggested:
            if c.corner:
                corners.append(c.corner.replace("_", " ").title())
            else:
                corners.append("Centro")
        
        QMessageBox.information(
            self, "Fiduciais Detectados",
            f"✅ Arquivo: {Path(filepath).name}\n"
            f"📊 {result.stats.total_objects} objetos\n"
            f"🎯 {len(result.fiducial_candidates)} candidatos a fiducial\n\n"
            f"Fiduciais selecionados:\n"
            f"• A: ({suggested[0].x_mm:.2f}, {suggested[0].y_mm:.2f}) mm - {corners[0]}\n"
            f"• B: ({suggested[1].x_mm:.2f}, {suggested[1].y_mm:.2f}) mm - {corners[1]}\n\n"
            f"Agora capture os templates clicando nos fiduciais na imagem."
        )

    
    def _search_all_fiducials(self):
        """Busca todos os fiduciais usando o adapter."""
        if self._current_image is None:
            QMessageBox.warning(self, "Erro", "Nenhuma imagem carregada.")
            return

        # Busca todos fiduciais usando adapter
        results = self.adapter.locate_fiducials(self._current_image)

        # Atualiza painéis
        panels = [self.panel_fid_a, self.panel_fid_b]
        for panel, result in zip(panels, results):
            panel.update_status(result)

        # Atualiza marcadores
        self._update_fiducial_markers_from_results(results)

        # Resumo
        found = sum(1 for r in results if r.found)
        QMessageBox.information(
            self, "Busca Concluída",
            f"{found}/{len(results)} fiduciais encontrados."
        )
    
    def _calculate_alignment(self):
        """Calcula transformação baseada nos fiduciais usando o adapter."""
        # Verifica se há pelo menos 2 fiduciais com match
        matched_count = self.adapter.get_matched_fiducial_count()

        if matched_count < 2:
            QMessageBox.warning(
                self, "Erro",
                "Execute a busca de fiduciais primeiro."
            )
            return

        # Calcula alinhamento usando adapter
        transform = self.adapter.calculate_alignment_from_matched_fiducials()

        if transform is None:
            QMessageBox.warning(
                self, "Erro",
                "Não foi possível calcular a transformação.\n"
                "Verifique se ambos os fiduciais foram encontrados."
            )
            return

        # Atualiza controles de transformação manual
        self.spin_tx.setValue(transform.tx)
        self.spin_ty.setValue(transform.ty)
        self.spin_angle.setValue(transform.angle)
        self.spin_scale.setValue(transform.scale_x)

        QMessageBox.information(
            self, "Alinhamento Calculado",
            f"Translação: ({transform.tx:.1f}, {transform.ty:.1f}) px\n"
            f"Rotação: {transform.angle:.2f}°\n"
            f"Escala: {transform.scale_x:.4f}"
        )
    
    def _apply_alignment(self):
        """Aplica alinhamento e emite sinal usando o adapter."""
        # Obtém transformação do adapter (ou cria a partir dos controles)
        transform = self.adapter.get_legacy_transform()

        if transform is None:
            # Cria transformação a partir dos controles manuais
            transform = AlignmentTransform(
                tx=self.spin_tx.value(),
                ty=self.spin_ty.value(),
                angle=self.spin_angle.value(),
                scale_x=self.spin_scale.value(),
                scale_y=self.spin_scale.value()
            )

        self.alignmentComplete.emit(transform)
    
    # -------------------------------------------------------------------------
    #  HANDLERS DE INTERAÇÃO
    # -------------------------------------------------------------------------
    
    def _on_mode_changed(self, index: int):
        """Muda modo de interação."""
        modes = ["pan", "select", "drag_gerber"]
        self.image_view.set_mode(modes[index])
    
    def _on_point_clicked(self, x: float, y: float):
        """Ponto clicado na imagem."""
        if hasattr(self, '_pending_capture'):
            # Captura template no ponto clicado usando adapter
            name = self._pending_capture
            delattr(self, '_pending_capture')

            template = self.panel_fid_a._template if name == "Fiducial A" else self.panel_fid_b._template

            if template and self._current_image is not None:
                if self.adapter.capture_template_at_point(template, self._current_image, int(x), int(y)):
                    panel = self.panel_fid_a if name == "Fiducial A" else self.panel_fid_b
                    panel.set_template(template)

                    # Volta ao modo pan
                    self.combo_mode.setCurrentIndex(0)

        log.debug(f"Ponto clicado: ({x:.1f}, {y:.1f})")
    
    def _on_position_dragged(self, dx: float, dy: float):
        """Overlay do Gerber arrastado."""
        self.spin_tx.setValue(self.spin_tx.value() + dx)
        self.spin_ty.setValue(self.spin_ty.value() + dy)
    
    def _on_transform_changed(self):
        """Transformação manual alterada - atualiza adapter."""
        # Atualiza overlay do Gerber
        self.image_view.set_gerber_transform(
            self.spin_tx.value(),
            self.spin_ty.value(),
            self.spin_scale.value(),
            self.spin_angle.value()
        )

        # Atualiza transformação no adapter usando método auxiliar
        self.adapter.update_transform_from_controls(
            tx=self.spin_tx.value(),
            ty=self.spin_ty.value(),
            angle=self.spin_angle.value(),
            scale_x=self.spin_scale.value(),
            scale_y=self.spin_scale.value()
        )
    
    def _update_fiducial_markers(self):
        """Atualiza marcadores de fiduciais na view usando adapter."""
        markers = []

        for fid in self.adapter._fiducial_templates:
            # Busca resultado correspondente no estado
            # (para compatibilidade com código legado)
            markers.append((
                fid.gerber_x,  # Posição padrão (será atualizada após match)
                fid.gerber_y,
                fid.name,
                False  # Default: não encontrado
            ))

        self.image_view.set_fiducial_markers(markers)

    def _update_fiducial_markers_from_results(self, results: List[FiducialMatchResult]):
        """Atualiza marcadores de fiduciais na view a partir de resultados."""
        markers = []

        for template, result in zip(self.adapter._fiducial_templates, results):
            markers.append((
                result.image_x,
                result.image_y,
                template.name,
                result.found
            ))

        self.image_view.set_fiducial_markers(markers)
