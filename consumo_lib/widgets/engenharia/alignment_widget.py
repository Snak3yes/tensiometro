"""
AlignmentWidget - Widget de Alinhamento (Track 5 do Engineering Wizard)

Este widget é a Aba 5 do fluxo de criação de programa de inspeção.
Responsável por alinhar o Gerber sobre o mosaico capturado.

ARQUITETURA REFACTORADA (2026-01-15):
    - Responsabilidade: APENAS UI e handlers (PyQt6)
    - Lógica de negócio: FiducialAlignmentService (injetado)
    - Estado: AlignmentState (modelo em consumo_lib.models)

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
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QGroupBox, QPushButton, QLabel, QDoubleSpinBox,
    QSlider, QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QPointF
from PyQt6.QtGui import (
    QImage, QPixmap, QPainter, QPen, QBrush, QColor,
    QTransform, QWheelEvent
)

from aoi_lib.gerber_renderer import GerberRenderer
from consumo_lib.models.alignment_state import AlignmentState
from consumo_lib.services.fiducial_alignment_service import (
    FiducialAlignmentService,
    AlignmentResult
)
from consumo_lib.ui import COLORS, TYPO, SPACE, DIM

logger = logging.getLogger(__name__)


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
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS.SURFACE};
                border: 2px solid {COLORS.BORDER};
                border-radius: {DIM.RADIUS_SM}px;
            }}
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
        result.fill(COLORS.to_qcolor(COLORS.SURFACE))

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

            color = COLORS.to_qcolor(COLORS.SUCCESS) if found else COLORS.to_qcolor(COLORS.ERROR)

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
    Widget de Alinhamento (Track 5) - REFACTORADO.

    Responsabilidades:
    - UI e PyQt6 (construção de layout, handlers, sinais)
    - Delegar lógica de negócio para FiducialAlignmentService

    Layout:
    - Esquerda: Preview do mosaico + Gerber overlay
    - Direita: Controles de ajuste e botões de ação
    """

    # Signals
    validationChanged = pyqtSignal(bool)  # isValid
    alignmentApplied = pyqtSignal(dict)  # transform data

    def __init__(
        self,
        parent=None,
        fiducial_service: Optional[FiducialAlignmentService] = None,
        hardware_coordinator=None
    ):
        """
        Inicializa o widget.

        Args:
            parent: Widget pai
            fiducial_service: Serviço de alinhamento (injeção de dependência)
            hardware_coordinator: EngineeringHardwareCoordinator (opcional)
        """
        super().__init__(parent)

        # Estado (usando modelo do consumo_lib.models)
        self._state = AlignmentState()
        self._initial_state: Optional[AlignmentState] = None

        # Dados carregados
        self._mosaic_image: Optional[np.ndarray] = None
        self._gerber_data: Optional[dict] = None
        self._fiducial_templates: list = []

        # Serviços (injeção de dependência)
        if fiducial_service is None:
            logger.info("Nenhum serviço injetado, criando FiducialAlignmentService padrão")
            self._fiducial_service = FiducialAlignmentService()
        else:
            self._fiducial_service = fiducial_service

        # Hardware coordinator (nova arquitetura)
        self._hardware_coordinator = hardware_coordinator

        self._build_ui()
        self._connect_signals()

        logger.debug("AlignmentWidget inicializado (refatorado)")

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
        logger.info("Carregando dados no AlignmentWidget (refatorado)")

        self._mosaic_image = mosaic_image
        self._gerber_data = gerber_data
        self._fiducial_templates = fiducial_templates

        # Exibe mosaico
        self.image_view.set_mosaic(mosaic_image)
        self.image_view.fit_in_view()

        # Renderiza Gerber como overlay
        if gerber_data and 'parsed' in gerber_data:
            self._render_gerber_overlay(gerber_data['parsed'])

        # Salva estado inicial
        self._initial_state = AlignmentState(
            tx=0.0, ty=0.0, angle=0.0, scale=1.0,
            opacity=0.5, zoom=1.0, score=0.0, fiducials_found=False
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
                'fiducials_found': bool,
                'fiducial_matches': [...]
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
            'fiducials_found': self._state.fiducials_found,
            'fiducial_matches': [m.to_dict() for m in self._state.fiducial_matches]
        }

    def is_valid(self) -> bool:
        """Verifica se alinhamento é válido."""
        return self._state.is_valid

    # ========================================================================
    #  MÉTODOS PRIVADOS - UI
    # ========================================================================

    def _build_ui(self):
        """Constrói UI."""
        main_layout = QHBoxLayout(self)

        # ===== Painel Esquerdo: Preview =====
        left_panel = QVBoxLayout()

        # Título
        title = QLabel("📍 Alinhamento Gerber ↔ Mosaico")
        title.setStyleSheet(f"{TYPO.HEADLINE_LARGE}; font-weight: bold; color: {COLORS.PRIMARY};")
        left_panel.addWidget(title)

        # Instrução
        instruction = QLabel(
            "Arraste o overlay do Gerber para alinhar com os fiduciais no mosaico. "
            "Use os controles manuais para ajustes finos."
        )
        instruction.setWordWrap(True)
        instruction.setStyleSheet(f"color: {COLORS.TEXT_HINT}; {TYPO.BODY_SMALL}; padding: {SPACE.XXS}px;")
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
        self.lbl_score.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                font-weight: bold;
                padding: {SPACE.XXS}px {SPACE.SM}px;
                background: {COLORS.BORDER};
                border-radius: {DIM.RADIUS_SM}px;
            }}
        """)
        score_layout.addWidget(self.lbl_score)

        # Indicador visual
        self.indicator_score = QLabel()
        self.indicator_score.setFixedSize(20, 20)
        self.indicator_score.setStyleSheet(f"""
            QLabel {{
                background: {COLORS.BORDER};
                border-radius: 10px;
            }}
        """)
        score_layout.addWidget(self.indicator_score)

        score_layout.addStretch()
        left_panel.addLayout(score_layout)

        main_layout.addLayout(left_panel, 2)

        # ===== Painel Direito: Controles =====
        right_panel = QVBoxLayout()

        # Grupo: Transformação Manual
        group_transform = QGroupBox("🎛️ Controles Manuais")
        group_transform.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {COLORS.BORDER};
                border-radius: {DIM.RADIUS_SM}px;
                margin-top: {SPACE.SM}px;
                padding-top: {SPACE.SM}px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: {SPACE.SM}px;
                padding: 0 {SPACE.XXS}px;
            }}
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
        lbl_auto_info.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; {TYPO.BODY_SMALL}")
        auto_layout.addWidget(lbl_auto_info)

        self.btn_auto_tune = QPushButton("🔍 Auto-Tuning")
        self.btn_auto_tune.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.WARNING};
                color: {COLORS.TEXT_PRIMARY};
                {TYPO.BODY_MEDIUM};
                font-weight: bold;
                padding: {SPACE.SM}px;
                border-radius: {DIM.RADIUS_XS}px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.WARNING_DARK};
            }}
        """)
        self.btn_auto_tune.clicked.connect(self._on_auto_tune)
        auto_layout.addWidget(self.btn_auto_tune)

        right_panel.addWidget(group_auto)

        # Botões de Ação
        right_panel.addStretch()

        btn_layout = QVBoxLayout()

        self.btn_reset = QPushButton("🔄 Resetar")
        self.btn_reset.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.TEXT_SECONDARY};
                color: {COLORS.TEXT_PRIMARY};
                {TYPO.BODY_MEDIUM};
                padding: {SPACE.SM}px;
                border-radius: {DIM.RADIUS_XS}px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.TEXT_HINT};
            }}
        """)
        self.btn_reset.clicked.connect(self._on_reset)
        btn_layout.addWidget(self.btn_reset)

        self.btn_apply = QPushButton("✅ Aplicar Alinhamento")
        self.btn_apply.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.PRIMARY};
                color: {COLORS.ON_PRIMARY};
                {TYPO.BODY_MEDIUM};
                font-weight: bold;
                padding: {SPACE.SM}px;
                border-radius: {DIM.RADIUS_XS}px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.PRIMARY_DARK};
            }}
            QPushButton:disabled {{
                background-color: {COLORS.TEXT_DISABLED};
                color: {COLORS.TEXT_SECONDARY};
            }}
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
    #  HANDLERS DE UI
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

    def _on_transform_changed(self):
        """Handler: transformação manual alterada."""
        # Atualiza estado
        self._state.update_from_transform(
            tx=self.spin_tx.value(),
            ty=self.spin_ty.value(),
            angle=self.spin_angle.value(),
            scale=self.spin_scale.value()
        )

        # Atualiza visualização
        self.image_view.set_gerber_transform(
            self._state.tx,
            self._state.ty,
            self._state.scale,
            self._state.angle,
            self._state.opacity
        )

        # Atualiza validação
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
        """Handler: auto-tuning (DELEGA AO SERVIÇO)."""
        if self._mosaic_image is None:
            QMessageBox.warning(
                self,
                "Erro",
                "Nenhum mosaico carregado."
            )
            return

        # Verifica pré-condições
        if not self._fiducial_templates:
            QMessageBox.warning(
                self,
                "Erro",
                "Nenhum template fiducial configurado."
            )
            return

        try:
            logger.info("Iniciando auto-tuning (widget delega para serviço)")

            # Delega para o serviço
            result: AlignmentResult = self._fiducial_service.align(
                templates=self._fiducial_templates,
                mosaic_image=self._mosaic_image
            )

            if not result.success:
                QMessageBox.warning(
                    self,
                    "Auto-Tuning - Falha",
                    f"Erro durante auto-tuning:\n\n{result.error}"
                )
                return

            # Atualiza estado com resultado
            self._state = result.state

            # Atualiza UI com transformação
            self._update_ui_from_state()

            # Atualiza marcadores
            markers = []
            for match in self._state.fiducial_matches:
                markers.append((
                    match.x,  # image_x
                    match.y,  # image_y
                    match.found  # found
                ))
            self.image_view.set_fiducial_markers(markers)

            # Mostra resultado
            QMessageBox.information(
                self,
                "✅ Auto-Tuning - Sucesso",
                f"Transformação calculada:\n\n"
                f"📍 Translação: ({self._state.tx:.1f}, {self._state.ty:.1f}) px\n"
                f"🔄 Rotação: {self._state.angle:.2f}°\n"
                f"📐 Escala: {self._state.scale:.4f}\n\n"
                f"Score médio: {self._state.score:.1f}%"
            )

            logger.info(
                f"Auto-tuning concluído: score={self._state.score:.1f}%, "
                f"tx={self._state.tx:.1f}, ty={self._state.ty:.1f}, "
                f"angle={self._state.angle:.2f}°"
            )

        except Exception as e:
            logger.exception("Erro no auto-tuning")
            QMessageBox.critical(
                self,
                "Erro",
                f"Erro durante auto-tuning:\n{str(e)}"
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
            self._state = self._initial_state.copy()

            # Atualiza UI
            self._update_ui_from_state()
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

    # ========================================================================
    #  MÉTODOS AUXILIARES
    # ========================================================================

    def _update_ui_from_state(self):
        """Atualiza UI baseado no estado atual."""
        # Bloqueia sinais para evitar loop
        self.spin_tx.blockSignals(True)
        self.spin_ty.blockSignals(True)
        self.spin_angle.blockSignals(True)
        self.spin_scale.blockSignals(True)
        self.slider_opacity.blockSignals(True)

        # Atualiza valores
        self.spin_tx.setValue(self._state.tx)
        self.spin_ty.setValue(self._state.ty)
        self.spin_angle.setValue(self._state.angle)
        self.spin_scale.setValue(self._state.scale)
        self.slider_opacity.setValue(int(self._state.opacity * 100))

        # Restaura sinais
        self.spin_tx.blockSignals(False)
        self.spin_ty.blockSignals(False)
        self.spin_angle.blockSignals(False)
        self.spin_scale.blockSignals(False)
        self.slider_opacity.blockSignals(False)

        # Atualiza labels
        self.lbl_opacity.setText(f"{int(self._state.opacity * 100)}%")

        # Atualiza score
        self._update_score_display()

        # Atualiza visualização
        self.image_view.set_gerber_transform(
            self._state.tx,
            self._state.ty,
            self._state.scale,
            self._state.angle,
            self._state.opacity
        )

        # Atualiza validação
        self._update_validation()

    def _update_score_display(self):
        """Atualiza display do score."""
        score = self._state.score

        self.lbl_score.setText(f"{score:.1f}%")

        # Atualiza indicador visual
        if score >= 90:
            color = COLORS.SUCCESS  # Verde
            bg = COLORS.SUCCESS
        elif score >= 70:
            color = COLORS.WARNING  # Laranja
            bg = COLORS.WARNING_LIGHT
        else:
            color = COLORS.ERROR  # Vermelho
            bg = COLORS.ERROR_LIGHT

        self.lbl_score.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                font-weight: bold;
                padding: {SPACE.XXS}px {SPACE.SM}px;
                background: {bg};
                color: {color};
                border-radius: {DIM.RADIUS_SM}px;
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
