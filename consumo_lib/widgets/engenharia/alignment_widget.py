"""
AlignmentWidget - Widget de Alinhamento (Track 5 do Engineering Wizard)

Este widget é a Aba 5 do fluxo de criação de programa de inspeção.
Responsável por alinhar o Gerber sobre o mosaico capturado.

Funcionalidades:
- Preview do mosaico + Gerber overlay com zoom/pan
- Controles manuais de ajuste (translação X/Y, rotação, escala)
- Controles finos (slider de opacidade, drag & move do overlay)
- Auto-tuning (template matching dos fiduciais)
- Score de matching (mostrar % e indicador visual)
- Reset (voltar ao estado inicial)
- Aplicar (salvar e avançar para próxima aba)

Signals:
- validationChanged(isValid) - Emitido quando validação muda
- alignmentApplied(transform) - Emitido quando alinhamento é aplicado
"""

import cv2
import numpy as np
import logging
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QGroupBox, QPushButton, QLabel, QSpinBox, QDoubleSpinBox,
    QSlider, QMessageBox, QSizePolicy, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QTimer
from PyQt6.QtGui import (
    QImage, QPixmap, QPainter, QPen, QBrush, QColor,
    QTransform, QWheelEvent
)

from aoi_lib.fiducial_alignment import (
    FiducialAligner, FiducialTemplate, FiducialMatchResult,
    AlignmentTransform
)
from aoi_lib.gerber_renderer import GerberRenderer

logger = logging.getLogger(__name__)


@dataclass
class AlignmentState:
    """Estado do alinhamento."""
    tx: float = 0.0
    ty: float = 0.0
    angle: float = 0.0
    scale: float = 1.0
    opacity: float = 0.5
    score: float = 0.0
    fiducials_found: bool = False


class AlignmentImageView(QLabel):
    """
    Widget de visualização com zoom/pan e arraste do overlay.

    Funcionalidades:
    - Zoom com scroll do mouse
    - Pan com clique do meio ou Ctrl+clique
    - Arraste do overlay Gerber
    """

    positionDragged = pyqtSignal(float, float)  # delta X, delta Y em pixels
    zoomChanged = pyqtSignal(float)  # nível de zoom

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 400)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                background-color: #1e1e1e;
                border: 2px solid #444;
                border-radius: 4px;
            }
        """)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        self.setMouseTracking(True)

        # Estado da imagem
        self._image: Optional[np.ndarray] = None
        self._pixmap: Optional[QPixmap] = None

        # Estado de visualização
        self._zoom = 1.0
        self._offset = QPointF(0, 0)

        # Estado de interação
        self._dragging = False
        self._last_pos = QPointF()
        self._drag_mode = "view"  # "view" ou "overlay"

        # Overlay do Gerber
        self._gerber_overlay: Optional[QPixmap] = None
        self._gerber_offset = QPointF(0, 0)
        self._gerber_scale = 1.0
        self._gerber_angle = 0.0
        self._gerber_opacity = 0.5

        # Marcadores de fiduciais
        self._fiducial_markers: list = []

    def set_mosaic(self, image: np.ndarray):
        """Define imagem do mosaico capturado."""
        if image is None:
            self._image = None
            self._pixmap = None
            self.clear()
            return

        self._image = image.copy()

        # Converte para QPixmap
        if len(image.shape) == 2:
            h, w = image.shape
            qimg = QImage(image.data, w, h, w, QImage.Format.Format_Grayscale8)
        else:
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            h, w = rgb.shape[:2]
            qimg = QImage(rgb.data, w, h, w * 3, QImage.Format.Format_RGB888)

        self._pixmap = QPixmap.fromImage(qimg)
        self._update_display()

    def set_gerber_overlay(self, overlay: Optional[QPixmap]):
        """Define overlay do Gerber renderizado."""
        self._gerber_overlay = overlay
        self._update_display()

    def set_gerber_transform(
        self,
        offset_x: float,
        offset_y: float,
        scale: float = 1.0,
        angle: float = 0.0,
        opacity: float = 0.5
    ):
        """Define transformação do overlay Gerber."""
        self._gerber_offset = QPointF(offset_x, offset_y)
        self._gerber_scale = scale
        self._gerber_angle = angle
        self._gerber_opacity = opacity
        self._update_display()

    def set_fiducial_markers(self, markers: list):
        """Define marcadores de fiduciais: [(x, y, found), ...]"""
        self._fiducial_markers = markers
        self._update_display()

    def fit_in_view(self):
        """Ajusta zoom para mostrar toda a imagem."""
        if self._pixmap is None:
            return

        img_w, img_h = self._pixmap.width(), self._pixmap.height()
        view_w, view_h = self.width() - 20, self.height() - 20

        scale_x = view_w / img_w if img_w > 0 else 1.0
        scale_y = view_h / img_h if img_h > 0 else 1.0
        self._zoom = min(scale_x, scale_y, 1.0)
        self._offset = QPointF(0, 0)
        self._update_display()
        self.zoomChanged.emit(self._zoom)

    def set_zoom(self, zoom: float):
        """Define nível de zoom."""
        self._zoom = max(0.1, min(5.0, zoom))
        self._update_display()
        self.zoomChanged.emit(self._zoom)

    def _update_display(self):
        """Atualiza renderização da imagem."""
        if self._pixmap is None:
            self.clear()
            return

        # Cria pixmap final
        view_w, view_h = self.width(), self.height()
        result = QPixmap(view_w, view_h)
        result.fill(QColor("#1e1e1e"))

        painter = QPainter(result)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Calcula posição centralizada
        scaled_w = int(self._pixmap.width() * self._zoom)
        scaled_h = int(self._pixmap.height() * self._zoom)

        x = (view_w - scaled_w) / 2 + self._offset.x()
        y = (view_h - scaled_h) / 2 + self._offset.y()

        # Desenha mosaico
        painter.drawPixmap(int(x), int(y), scaled_w, scaled_h, self._pixmap)

        # Desenha overlay do Gerber
        if self._gerber_overlay is not None:
            painter.save()
            painter.setOpacity(self._gerber_opacity)

            # Aplica transformação
            gerber_x = x + self._gerber_offset.x() * self._zoom
            gerber_y = y + self._gerber_offset.y() * self._zoom

            transform = QTransform()
            transform.translate(gerber_x, gerber_y)
            transform.scale(
                self._gerber_scale * self._zoom,
                self._gerber_scale * self._zoom
            )
            transform.rotate(self._gerber_angle)

            painter.setTransform(transform)
            painter.drawPixmap(0, 0, self._gerber_overlay)
            painter.restore()

        # Desenha marcadores de fiduciais
        for fx, fy, found in self._fiducial_markers:
            vx = x + fx * self._zoom
            vy = y + fy * self._zoom

            color = QColor("#00ff00") if found else QColor("#ff0000")

            # Cruz
            pen = QPen(color, 2)
            painter.setPen(pen)
            painter.drawLine(int(vx - 10), int(vy), int(vx + 10), int(vy))
            painter.drawLine(int(vx), int(vy - 10), int(vx), int(vy + 10))

            # Círculo
            painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
            painter.drawEllipse(int(vx - 5), int(vy - 5), 10, 10)

        painter.end()
        self.setPixmap(result)

    def mousePressEvent(self, event):
        """Captura clique do mouse."""
        pos = event.position()

        if event.button() == Qt.MouseButton.MiddleButton or \
           (event.button() == Qt.MouseButton.LeftButton and
            event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            # Inicia pan da view
            self._dragging = True
            self._drag_mode = "view"
            self._last_pos = pos
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

        elif event.button() == Qt.MouseButton.LeftButton:
            # Verifica se clicou no overlay
            if self._is_over_overlay(pos.x(), pos.y()):
                # Inicia arraste do overlay
                self._dragging = True
                self._drag_mode = "overlay"
                self._last_pos = pos
                self.setCursor(Qt.CursorShape.SizeAllCursor)
            else:
                # Pan da view
                self._dragging = True
                self._drag_mode = "view"
                self._last_pos = pos
                self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        """Movimento do mouse."""
        if not self._dragging:
            return

        pos = event.position()
        delta = pos - self._last_pos
        self._last_pos = pos

        if self._drag_mode == "overlay":
            # Arrasta overlay
            self.positionDragged.emit(delta.x(), delta.y())
        else:
            # Pan da view
            self._offset += QPointF(delta.x(), delta.y())
            self._update_display()

    def mouseReleaseEvent(self, event):
        """Liberação do mouse."""
        if self._dragging:
            self._dragging = False
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def wheelEvent(self, event: QWheelEvent):
        """Zoom com scroll do mouse."""
        delta = event.angleDelta().y()
        factor = 1.1 if delta > 0 else 0.9

        old_zoom = self._zoom
        self._zoom = max(0.1, min(5.0, self._zoom * factor))

        # Ajusta offset para zoom centrado
        pos = event.position()
        ratio = self._zoom / old_zoom - 1.0
        self._offset -= QPointF(
            (pos.x() - self.width() / 2) * ratio,
            (pos.y() - self.height() / 2) * ratio
        )

        self._update_display()
        self.zoomChanged.emit(self._zoom)

    def _is_over_overlay(self, view_x: float, view_y: float) -> bool:
        """Verifica se posição está sobre o overlay."""
        if self._pixmap is None or self._gerber_overlay is None:
            return False

        # Simplificação: considera região central como overlay
        view_w, view_h = self.width(), self.height()
        center_x, center_y = view_w / 2, view_h / 2

        dx = abs(view_x - center_x)
        dy = abs(view_y - center_y)

        return dx < view_w / 4 and dy < view_h / 4

    def resizeEvent(self, event):
        """Redimensionamento."""
        super().resizeEvent(event)
        self._update_display()


class AlignmentWidget(QWidget):
    """
    Widget de Alinhamento (Track 5).

    Layout:
    - Esquerda: Preview do mosaico + Gerber overlay
    - Direita: Controles de ajuste e botões de ação
    """

    # Signals
    validationChanged = pyqtSignal(bool)  # isValid
    alignmentApplied = pyqtSignal(dict)  # transform data

    def __init__(self, parent=None, hardware_coordinator=None):
        """Inicializa o widget.

        Args:
            parent: Widget pai
            hardware_coordinator: EngineeringHardwareCoordinator (opcional)
        """
        super().__init__(parent)

        # Estado
        self._state = AlignmentState()
        self._mosaic_image: Optional[np.ndarray] = None
        self._gerber_data: Optional[dict] = None
        self._fiducial_templates: list = []
        self._initial_state: Optional[AlignmentState] = None

        # Hardware coordinator (nova arquitetura)
        self._hardware_coordinator = hardware_coordinator
        # Legado: aligner individual (para compatibilidade)
        self.aligner = FiducialAligner()

        self._build_ui()
        self._connect_signals()

        logger.debug("AlignmentWidget inicializado")

    def set_hardware_coordinator(self, coordinator):
        """Define o coordenador de hardware (injeção de dependência).

        Args:
            coordinator: EngineeringHardwareCoordinator
        """
        self._hardware_coordinator = coordinator
        logger.info("🔧 Hardware coordinator definido no AlignmentWidget")

    def _build_ui(self):
        """Constrói UI."""
        main_layout = QHBoxLayout(self)

        # ===== Painel Esquerdo: Preview =====
        left_panel = QVBoxLayout()

        # Título
        title = QLabel("📍 Alinhamento Gerber ↔ Mosaico")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1976D2;")
        left_panel.addWidget(title)

        # Instrução
        instruction = QLabel(
            "Arraste o overlay do Gerber para alinhar com os fiduciais no mosaico. "
            "Use os controles manuais para ajustes finos."
        )
        instruction.setWordWrap(True)
        instruction.setStyleSheet("color: #616161; font-size: 12px; padding: 4px;")
        left_panel.addWidget(instruction)

        # Preview image
        self.image_view = AlignmentImageView()
        left_panel.addWidget(self.image_view, 1)

        # Controles de zoom
        zoom_layout = QHBoxLayout()
        zoom_layout.addWidget(QLabel("Zoom:"))

        self.slider_zoom = QSlider(Qt.Orientation.Horizontal)
        self.slider_zoom.setRange(10, 300)
        self.slider_zoom.setValue(100)
        zoom_layout.addWidget(self.slider_zoom)

        self.lbl_zoom = QLabel("100%")
        self.lbl_zoom.setMinimumWidth(50)
        zoom_layout.addWidget(self.lbl_zoom)

        btn_fit = QPushButton("Ajustar à Janela")
        btn_fit.setMaximumWidth(120)
        btn_fit.clicked.connect(self.image_view.fit_in_view)
        zoom_layout.addWidget(btn_fit)

        left_panel.addLayout(zoom_layout)

        # Score de matching
        score_layout = QHBoxLayout()
        score_layout.addWidget(QLabel("Score de Alinhamento:"))

        self.lbl_score = QLabel("0.0%")
        self.lbl_score.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                padding: 4px 12px;
                background: #E0E0E0;
                border-radius: 4px;
            }
        """)
        score_layout.addWidget(self.lbl_score)

        # Indicador visual
        self.indicator_score = QLabel()
        self.indicator_score.setFixedSize(20, 20)
        self.indicator_score.setStyleSheet("""
            QLabel {
                background: #E0E0E0;
                border-radius: 10px;
            }
        """)
        score_layout.addWidget(self.indicator_score)

        score_layout.addStretch()
        left_panel.addLayout(score_layout)

        main_layout.addLayout(left_panel, 2)

        # ===== Painel Direito: Controles =====
        right_panel = QVBoxLayout()

        # Grupo: Transformação Manual
        group_transform = QGroupBox("🎛️ Controles Manuais")
        group_transform.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #E0E0E0;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        transform_layout = QFormLayout(group_transform)

        self.spin_tx = QDoubleSpinBox()
        self.spin_tx.setRange(-1000, 1000)
        self.spin_tx.setDecimals(1)
        self.spin_tx.setSuffix(" px")
        self.spin_tx.setValue(0.0)
        transform_layout.addRow("Translação X:", self.spin_tx)

        self.spin_ty = QDoubleSpinBox()
        self.spin_ty.setRange(-1000, 1000)
        self.spin_ty.setDecimals(1)
        self.spin_ty.setSuffix(" px")
        self.spin_ty.setValue(0.0)
        transform_layout.addRow("Translação Y:", self.spin_ty)

        self.spin_angle = QDoubleSpinBox()
        self.spin_angle.setRange(-180, 180)
        self.spin_angle.setDecimals(2)
        self.spin_angle.setSuffix("°")
        self.spin_angle.setValue(0.0)
        transform_layout.addRow("Rotação:", self.spin_angle)

        self.spin_scale = QDoubleSpinBox()
        self.spin_scale.setRange(0.1, 10.0)
        self.spin_scale.setDecimals(4)
        self.spin_scale.setValue(1.0)
        self.spin_scale.setSingleStep(0.01)
        transform_layout.addRow("Escala:", self.spin_scale)

        right_panel.addWidget(group_transform)

        # Grupo: Ajustes Finos
        group_fine = QGroupBox("🔧 Ajustes Finos")
        group_fine.setStyleSheet(group_transform.styleSheet())
        fine_layout = QFormLayout(group_fine)

        fine_layout.addRow(QLabel("Opacidade do Overlay:"))

        self.slider_opacity = QSlider(Qt.Orientation.Horizontal)
        self.slider_opacity.setRange(0, 100)
        self.slider_opacity.setValue(50)
        self.slider_opacity.valueChanged.connect(self._on_opacity_changed)
        fine_layout.addRow(self.slider_opacity)

        self.lbl_opacity = QLabel("50%")
        fine_layout.addRow("", self.lbl_opacity)

        right_panel.addWidget(group_fine)

        # Grupo: Auto-Tuning
        group_auto = QGroupBox("✨ Auto-Tuning")
        group_auto.setStyleSheet(group_transform.styleSheet())
        auto_layout = QVBoxLayout(group_auto)

        lbl_auto_info = QLabel(
            "Busca fiduciais automaticamente usando template matching "
            "e calcula a transformação ótima."
        )
        lbl_auto_info.setWordWrap(True)
        lbl_auto_info.setStyleSheet("color: #616161; font-size: 11px;")
        auto_layout.addWidget(lbl_auto_info)

        self.btn_auto_tune = QPushButton("🔍 Auto-Tuning")
        self.btn_auto_tune.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        self.btn_auto_tune.clicked.connect(self._on_auto_tune)
        auto_layout.addWidget(self.btn_auto_tune)

        right_panel.addWidget(group_auto)

        # Botões de Ação
        right_panel.addStretch()

        btn_layout = QVBoxLayout()

        self.btn_reset = QPushButton("🔄 Resetar")
        self.btn_reset.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        self.btn_reset.clicked.connect(self._on_reset)
        btn_layout.addWidget(self.btn_reset)

        self.btn_apply = QPushButton("✅ Aplicar Alinhamento")
        self.btn_apply.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45A049;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
                color: #757575;
            }
        """)
        self.btn_apply.clicked.connect(self._on_apply)
        btn_layout.addWidget(self.btn_apply)

        right_panel.addLayout(btn_layout)

        main_layout.addLayout(right_panel, 1)

    def _connect_signals(self):
        """Conecta sinais."""
        # Zoom
        self.slider_zoom.valueChanged.connect(
            lambda v: self.image_view.set_zoom(v / 100.0)
        )
        self.image_view.zoomChanged.connect(
            lambda z: (
                self.slider_zoom.setValue(int(z * 100)),
                self.lbl_zoom.setText(f"{z*100:.0f}%")
            )
        )

        # Arraste do overlay
        self.image_view.positionDragged.connect(self._on_overlay_dragged)

        # Transformação manual
        self.spin_tx.valueChanged.connect(self._on_transform_changed)
        self.spin_ty.valueChanged.connect(self._on_transform_changed)
        self.spin_angle.valueChanged.connect(self._on_transform_changed)
        self.spin_scale.valueChanged.connect(self._on_transform_changed)

    # ========================================================================
    #  MÉTODOS PÚBLICOS
    # ========================================================================

    def load_data(
        self,
        mosaic_image: np.ndarray,
        gerber_data: dict,
        fiducial_templates: list
    ):
        """
        Carrega dados para alinhamento.

        Args:
            mosaic_image: Imagem do mosaico capturado
            gerber_data: Dicionário com dados do Gerber {
                'parsed': ParsedGerber,
                'fiducial_positions': [(x1, y1), (x2, y2)]
            }
            fiducial_templates: Lista de templates capturados [
                {'name': 'Fiducial A', 'image': np.ndarray, 'position': (x, y)},
                ...
            ]
        """
        logger.info("Carregando dados no AlignmentWidget")

        self._mosaic_image = mosaic_image
        self._gerber_data = gerber_data
        self._fiducial_templates = fiducial_templates

        # Exibe mosaico
        self.image_view.set_mosaic(mosaic_image)
        self.image_view.fit_in_view()

        # Renderiza Gerber como overlay
        if gerber_data and 'parsed' in gerber_data:
            self._render_gerber_overlay(gerber_data['parsed'])

        # Configura fiduciais no aligner
        self._setup_fiducials(fiducial_templates)

        # Salva estado inicial
        self._initial_state = AlignmentState(
            tx=0.0, ty=0.0, angle=0.0, scale=1.0,
            opacity=0.5, score=0.0, fiducials_found=False
        )

        # Atualiza validação
        self._update_validation()

        logger.info("Dados carregados com sucesso")

    def get_alignment_data(self) -> dict:
        """
        Retorna dados do alinhamento.

        Returns:
            dict: {
                'transform': {
                    'tx': float, 'ty': float,
                    'angle': float, 'scale': float
                },
                'score': float,
                'fiducials_found': bool
            }
        """
        return {
            'transform': {
                'tx': self._state.tx,
                'ty': self._state.ty,
                'angle': self._state.angle,
                'scale': self._state.scale
            },
            'score': self._state.score,
            'fiducials_found': self._state.fiducials_found
        }

    def is_valid(self) -> bool:
        """Verifica se alinhamento é válido."""
        return self._state.score >= 70.0 or self._state.fiducials_found

    # ========================================================================
    #  MÉTODOS PRIVADOS
    # ========================================================================

    def _render_gerber_overlay(self, parsed_gerber):
        """Renderiza Gerber como QPixmap overlay."""
        try:
            # Cria imagem do tamanho do mosaico
            if self._mosaic_image is None:
                return

            h, w = self._mosaic_image.shape[:2]

            # Renderiza Gerber
            renderer = GerberRenderer(parsed_gerber)
            overlay_img = renderer.render_to_image(
                width=w,
                height=h,
                transform=None  # Sem transformação inicial
            )

            # Converte para QPixmap
            if len(overlay_img.shape) == 2:
                qimg = QImage(
                    overlay_img.data,
                    w, h, w,
                    QImage.Format.Format_Grayscale8
                )
            else:
                rgb = cv2.cvtColor(overlay_img, cv2.COLOR_BGR2RGB)
                qimg = QImage(rgb.data, w, h, w * 3, QImage.Format.Format_RGB888)

            pixmap = QPixmap.fromImage(qimg)
            self.image_view.set_gerber_overlay(pixmap)

            logger.debug("Gerber overlay renderizado")

        except Exception as e:
            logger.error(f"Erro ao renderizar Gerber: {e}")

    def _setup_fiducials(self, templates: list):
        """Configura fiduciais no aligner."""
        self.aligner.fiducials.clear()

        for i, template_data in enumerate(templates):
            name = template_data.get('name', f'Fiducial {i+1}')
            position = template_data.get('position', (0, 0))
            image = template_data.get('image')

            fid = self.aligner.add_fiducial(name, position[0], position[1])

            if image is not None:
                self.aligner.capture_template(fid, image)

            logger.debug(f"Fiducial configurado: {name} at {position}")

    def _on_transform_changed(self):
        """Handler: transformação manual alterada."""
        # Atualiza estado
        self._state.tx = self.spin_tx.value()
        self._state.ty = self.spin_ty.value()
        self._state.angle = self.spin_angle.value()
        self._state.scale = self.spin_scale.value()

        # Atualiza visualização
        self.image_view.set_gerber_transform(
            self._state.tx,
            self._state.ty,
            self._state.scale,
            self._state.angle,
            self._state.opacity
        )

        # Atualiza score (estimado baseado em transformação)
        self._estimate_score()
        self._update_validation()

        logger.debug(
            f"Transformação alterada: tx={self._state.tx:.1f}, "
            f"ty={self._state.ty:.1f}, angle={self._state.angle:.2f}°, "
            f"scale={self._state.scale:.4f}"
        )

    def _on_opacity_changed(self, value: int):
        """Handler: opacidade alterada."""
        opacity = value / 100.0
        self._state.opacity = opacity
        self.lbl_opacity.setText(f"{value}%")

        self.image_view.set_gerber_transform(
            self._state.tx,
            self._state.ty,
            self._state.scale,
            self._state.angle,
            opacity
        )

    def _on_overlay_dragged(self, dx: float, dy: float):
        """Handler: overlay arrastado."""
        # Atualiza spinboxes
        self.spin_tx.setValue(self.spin_tx.value() + dx)
        self.spin_ty.setValue(self.spin_ty.value() + dy)

    def _on_auto_tune(self):
        """Handler: auto-tuning (estratégia dual)."""
        if self._mosaic_image is None:
            QMessageBox.warning(
                self,
                "Erro",
                "Nenhum mosaico carregado."
            )
            return

        # Verifica pré-condições
        if self._hardware_coordinator:
            if len(self._fiducial_templates) < 2:
                QMessageBox.warning(
                    self,
                    "Erro",
                    "Mínimo de 2 templates fiduciais necessários."
                )
                return
        else:
            if not self.aligner.fiducials:
                QMessageBox.warning(
                    self,
                    "Erro",
                    "Nenhum fiducial configurado."
                )
                return

        try:
            logger.info("Iniciando auto-tuning")

            # Estratégia dual: coordinator vs legacy
            if self._hardware_coordinator:
                self._align_with_coordinator()
            else:
                self._align_with_legacy()

        except Exception as e:
            logger.exception("Erro no auto-tuning")
            QMessageBox.critical(
                self,
                "Erro",
                f"Erro durante auto-tuning:\n{str(e)}"
            )

    def _align_with_coordinator(self):
        """Executa alinhamento usando EngineeringHardwareCoordinator."""
        from consumo_lib.coordinators.engineering_hardware_coordinator import HardwareType

        logger.info("Usando EngineeringHardwareCoordinator para alinhamento")

        # Verifica hardware
        ready, message = self._hardware_coordinator.is_hardware_ready([])
        if not ready:
            QMessageBox.warning(
                self,
                "Auto-Tuning - Aviso",
                f"Hardware não está pronto:\n{message}\n\n"
                "Continuando mesmo assim..."
            )

        # Prepara templates no formato esperado pelo coordinator
        templates_for_coordinator = []
        for template_data in self._fiducial_templates:
            templates_for_coordinator.append({
                'image': template_data.get('image'),
                'x': template_data.get('position', (0, 0))[0],
                'y': template_data.get('position', (0, 0))[1],
                'z': 0.0,
                'window_size': template_data.get('window_size', 50)
            })

        # Executa alinhamento via coordinator
        result = self._hardware_coordinator.perform_fiducial_alignment(
            fiducial_templates=templates_for_coordinator,
            mosaic_image=self._mosaic_image
        )

        # Extrai transformação do resultado
        transform_data = result.get('transform', {})
        tx = transform_data.get('tx', 0.0)
        ty = transform_data.get('ty', 0.0)
        angle = transform_data.get('angle', 0.0)
        scale = transform_data.get('scale', 1.0)
        scores = result.get('scores', [])
        matched_positions = result.get('matched_positions', [])

        # Verifica se encontrou fiduciais suficientes
        found_count = len([s for s in scores if s >= 70.0])

        if found_count < 2:
            QMessageBox.warning(
                self,
                "Auto-Tuning - Falha",
                f"Apenas {found_count}/{len(scores)} fiduciais encontrados.\n\n"
                "Ajuste manualmente ou recapture os templates."
            )
            return

        # Aplica transformação
        self.spin_tx.blockSignals(True)
        self.spin_ty.blockSignals(True)
        self.spin_angle.blockSignals(True)
        self.spin_scale.blockSignals(True)

        self.spin_tx.setValue(tx)
        self.spin_ty.setValue(ty)
        self.spin_angle.setValue(angle)
        self.spin_scale.setValue(scale)

        self.spin_tx.blockSignals(False)
        self.spin_ty.blockSignals(False)
        self.spin_angle.blockSignals(False)
        self.spin_scale.blockSignals(False)

        # Atualiza estado e visualização
        self._on_transform_changed()
        self._state.fiducials_found = True

        # Atualiza marcadores
        markers = []
        for i, pos in enumerate(matched_positions):
            score = scores[i] if i < len(scores) else 0.0
            markers.append((
                pos[0],  # image_x
                pos[1],  # image_y
                score >= 70.0  # found
            ))
        self.image_view.set_fiducial_markers(markers)

        # Mostra resultado
        avg_score = sum(scores) / len(scores) if scores else 0.0
        self._state.score = avg_score
        self._update_score_display()

        QMessageBox.information(
            self,
            "✅ Auto-Tuning - Sucesso",
            f"Transformação calculada:\n\n"
            f"📍 Translação: ({tx:.1f}, {ty:.1f}) px\n"
            f"🔄 Rotação: {angle:.2f}°\n"
            f"📐 Escala: {scale:.4f}\n\n"
            f"Score médio: {avg_score:.1f}%"
        )

        logger.info(
            f"Auto-tuning concluído (coordinator): score={avg_score:.1f}%, "
            f"tx={tx:.1f}, ty={ty:.1f}, angle={angle:.2f}°"
        )

    def _align_with_legacy(self):
        """Executa alinhamento usando FiducialAligner (legado)."""
        logger.info("Usando FiducialAligner (legado) para alinhamento")

        # Busca fiduciais
        gray = cv2.cvtColor(self._mosaic_image, cv2.COLOR_BGR2GRAY)
        results = self.aligner.find_all_fiducials(gray)

        # Verifica se encontrou
        found_count = sum(1 for r in results if r.found)

        if found_count < 2:
            QMessageBox.warning(
                self,
                "Auto-Tuning - Falha",
                f"Apenas {found_count}/2 fiduciais encontrados.\n\n"
                "Ajuste manualmente ou recapture os templates."
            )
            return

        # Calcula transformação
        transform = self.aligner.calculate_transform_from_fiducials()

        if transform is None:
            QMessageBox.warning(
                self,
                "Auto-Tuning - Erro",
                "Não foi possível calcular a transformação."
            )
            return

        # Aplica transformação
        self.spin_tx.blockSignals(True)
        self.spin_ty.blockSignals(True)
        self.spin_angle.blockSignals(True)
        self.spin_scale.blockSignals(True)

        self.spin_tx.setValue(transform.tx)
        self.spin_ty.setValue(transform.ty)
        self.spin_angle.setValue(transform.angle)
        self.spin_scale.setValue(transform.scale_x)

        self.spin_tx.blockSignals(False)
        self.spin_ty.blockSignals(False)
        self.spin_angle.blockSignals(False)
        self.spin_scale.blockSignals(False)

        # Atualiza estado e visualização
        self._on_transform_changed()
        self._state.fiducials_found = True

        # Atualiza marcadores
        markers = []
        for result in results:
            markers.append((
                result.image_x,
                result.image_y,
                result.found
            ))
        self.image_view.set_fiducial_markers(markers)

        # Mostra resultado
        avg_score = sum(r.similarity for r in results) / len(results)
        self._state.score = avg_score
        self._update_score_display()

        QMessageBox.information(
            self,
            "✅ Auto-Tuning - Sucesso",
            f"Transformação calculada:\n\n"
            f"📍 Translação: ({transform.tx:.1f}, {transform.ty:.1f}) px\n"
            f"🔄 Rotação: {transform.angle:.2f}°\n"
            f"📐 Escala: {transform.scale_x:.4f}\n\n"
            f"Score médio: {avg_score:.1f}%"
        )

        logger.info(
            f"Auto-tuning concluído (legado): score={avg_score:.1f}%, "
            f"tx={transform.tx:.1f}, ty={transform.ty:.1f}, "
            f"angle={transform.angle:.2f}°"
        )

    def _on_reset(self):
        """Handler: resetar."""
        if self._initial_state is None:
            return

        reply = QMessageBox.question(
            self,
            "Resetar Alinhamento",
            "Deseja voltar ao estado inicial?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Restaura estado inicial
            self.spin_tx.blockSignals(True)
            self.spin_ty.blockSignals(True)
            self.spin_angle.blockSignals(True)
            self.spin_scale.blockSignals(True)
            self.slider_opacity.blockSignals(True)

            self.spin_tx.setValue(self._initial_state.tx)
            self.spin_ty.setValue(self._initial_state.ty)
            self.spin_angle.setValue(self._initial_state.angle)
            self.spin_scale.setValue(self._initial_state.scale)
            self.slider_opacity.setValue(int(self._initial_state.opacity * 100))

            self.spin_tx.blockSignals(False)
            self.spin_ty.blockSignals(False)
            self.spin_angle.blockSignals(False)
            self.spin_scale.blockSignals(False)
            self.slider_opacity.blockSignals(False)

            # Reseta estado
            self._state = AlignmentState(
                tx=self._initial_state.tx,
                ty=self._initial_state.ty,
                angle=self._initial_state.angle,
                scale=self._initial_state.scale,
                opacity=self._initial_state.opacity,
                score=0.0,
                fiducials_found=False
            )

            # Atualiza
            self._on_transform_changed()
            self.image_view.set_fiducial_markers([])

            logger.info("Alinhamento resetado")

    def _on_apply(self):
        """Handler: aplicar alinhamento."""
        if not self.is_valid():
            reply = QMessageBox.question(
                self,
                "⚠️ Alinhamento Ruim",
                f"Score de alinhamento: {self._state.score:.1f}%\n\n"
                "Deseja aplicar mesmo assim?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.No:
                return

        # Emitir sinal com dados
        self.alignmentApplied.emit(self.get_alignment_data())

        QMessageBox.information(
            self,
            "✅ Alinhamento Aplicado",
            f"Transformação aplicada com sucesso!\n\n"
            f"📍 Translação: ({self._state.tx:.1f}, {self._state.ty:.1f}) px\n"
            f"🔄 Rotação: {self._state.angle:.2f}°\n"
            f"📐 Escala: {self._state.scale:.4f}\n"
            f"Score: {self._state.score:.1f}%"
        )

        logger.info(
            f"Alinhamento aplicado: tx={self._state.tx:.1f}, "
            f"ty={self._state.ty:.1f}, angle={self._state.angle:.2f}°, "
            f"scale={self._state.scale:.4f}, score={self._state.score:.1f}%"
        )

    def _estimate_score(self):
        """Estima score baseado em transformação."""
        # Estimativa simples: quanto menor a translação/rotação, maior o score
        translation_penalty = min(abs(self._state.tx) + abs(self._state.ty), 100) / 10
        rotation_penalty = min(abs(self._state.angle), 45) / 45 * 20
        scale_penalty = abs(self._state.scale - 1.0) * 30

        estimated_score = max(0, 100 - translation_penalty - rotation_penalty - scale_penalty)

        # Arredonda
        self._state.score = round(estimated_score, 1)
        self._update_score_display()

    def _update_score_display(self):
        """Atualiza display do score."""
        score = self._state.score

        self.lbl_score.setText(f"{score:.1f}%")

        # Atualiza indicador visual
        if score >= 90:
            color = "#4CAF50"  # Verde
            bg = "#E8F5E9"
        elif score >= 70:
            color = "#FF9800"  # Laranja
            bg = "#FFF3E0"
        else:
            color = "#F44336"  # Vermelho
            bg = "#FFEBEE"

        self.lbl_score.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                font-weight: bold;
                padding: 4px 12px;
                background: {bg};
                color: {color};
                border-radius: 4px;
            }}
        """)

        self.indicator_score.setStyleSheet(f"""
            QLabel {{
                background: {color};
                border-radius: 10px;
            }}
        """)

    def _update_validation(self):
        """Atualiza estado de validação."""
        valid = self.is_valid()
        self.validationChanged.emit(valid)

        # Habilita/desabilita botão aplicar
        self.btn_apply.setEnabled(valid or self._state.score > 0)
