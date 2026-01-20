"""
CameraCaptureWidget - Widget Unificado de Captura de Câmera

Este widget combina todas as funcionalidades de câmera em um único componente reutilizável:
- Live preview com Start/Stop
- Click-to-move (mover máquina clicando no vídeo)
- Captura de templates (fiducial, mosaic, etc)
- Crosshair no centro
- Configurações de espelhamento

Autor: Claude Code (Sonnet 4.5)
Data: 2026-01-17
"""

import cv2
import logging
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QLabel, QCheckBox, QSpinBox,
    QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QImage
import numpy as np

# Design System
from consumo_lib.ui import COLORS, SPACE, DIM

from aoi_lib.config_manager import AOIConfigManager
from aoi_lib.fov_calibration import (
    FOVCalibration, CameraFOVConverter, ClickableVideoLabel
)

logger = logging.getLogger(__name__)


class CameraCaptureWidget(QWidget):
    """
    Widget unificado de captura de câmera.

    Combina funcionalidades de:
    - CameraPreviewWidget (live preview + click-to-move)
    - FiducialPreviewWidget (captura de templates)
    - MosaicPreviewWidget (captura em grid)

    Signals:
        image_captured(np.ndarray, dict): Emitido quando template é capturado
        frame_ready(np.ndarray): Emitido quando novo frame está disponível
    """

    # Signals
    image_captured = pyqtSignal(np.ndarray, dict)  # image, metadata
    frame_ready = pyqtSignal(np.ndarray)  # Novo frame disponível

    def __init__(self, controller, cfg: AOIConfigManager,
                 click_to_move_service=None, fov_converter=None,
                 parent=None):
        """
        Inicializa o widget.

        Args:
            controller: AOIController
            cfg: AOIConfigManager
            click_to_move_service: ClickToMoveService (opcional)
            fov_converter: CameraFOVConverter (opcional)
            parent: Widget pai
        """
        super().__init__(parent)
        self.controller = controller
        self.cfg = cfg
        self.click_to_move_service = click_to_move_service
        self.current_image = None
        self._last_frame_size = (640, 480)
        self.preview_timer = QTimer(self)
        self.preview_timer.timeout.connect(self.update_preview)

        # Inicializa conversor de FOV
        if fov_converter is not None:
            self.fov_converter = fov_converter
        else:
            self._init_fov_converter()

        # Configurações de captura
        self._window_size = 50  # Tamanho padrão da janela de captura (px)

        self.setup_ui()

    def _init_fov_converter(self):
        """Inicializa o conversor de coordenadas pixel→pulsos"""
        self.fov_converter = CameraFOVConverter()

        # Carrega calibração salva se existir e cfg foi fornecido
        if self.cfg is not None:
            fov_data = self.cfg.get("camera", "fov_calibration", default={})
            if fov_data:
                self.fov_converter.set_fov_calibration(FOVCalibration.from_dict(fov_data))

            # Carrega calibração de eixos
            pulses_per_mm = self.cfg.get("movement", "pulses_per_mm", default=100.0)
            self.fov_converter.set_axis_calibration("X", pulses_per_mm)
            self.fov_converter.set_axis_calibration("Y", pulses_per_mm)

    def setup_ui(self):
        """Configura interface do usuário."""
        layout = QVBoxLayout(self)

        # GroupBox para preview da câmera
        preview_group = QGroupBox("Camera Preview")
        preview_group.setMinimumHeight(450)
        pg_layout = QVBoxLayout(preview_group)

        # Área de visualização - usa ClickableVideoLabel
        self.image_label = ClickableVideoLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setText("Camera Preview\n(Clique para mover a máquina)")
        self.image_label.setStyleSheet(f"""
            border: 1px solid gray;
            background-color: {COLORS.SURFACE};
        """)
        self.image_label.setMinimumSize(600, 450)
        self.image_label.clicked.connect(self._on_video_click)
        pg_layout.addWidget(self.image_label)

        # Checkbox para habilitar movimento por clique
        self.click_move_enabled = QCheckBox("Mover máquina ao clicar")
        self.click_move_enabled.setChecked(False)
        self.click_move_enabled.setToolTip(
            "Quando ativado, clicar no vídeo move a máquina para centralizar o ponto clicado"
        )
        pg_layout.addWidget(self.click_move_enabled)

        # Botões de preview
        btn_layout = QHBoxLayout()
        self.start_preview_btn = QPushButton("▶ Start Preview")
        self.start_preview_btn.clicked.connect(self.start_preview)
        self.stop_preview_btn = QPushButton("⏸ Stop Preview")
        self.stop_preview_btn.clicked.connect(self.stop_preview)
        self.stop_preview_btn.setEnabled(False)
        btn_layout.addWidget(self.start_preview_btn)
        btn_layout.addWidget(self.stop_preview_btn)
        pg_layout.addLayout(btn_layout)

        layout.addWidget(preview_group, 1)

        # GroupBox para configurações de captura
        capture_group = QGroupBox("Configurações de Captura")
        capture_layout = QHBoxLayout(capture_group)

        # Tamanho da janela de captura
        capture_layout.addWidget(QLabel("Tamanho da janela:"))
        self.window_size_spin = QSpinBox()
        self.window_size_spin.setRange(10, 200)
        self.window_size_spin.setValue(50)
        self.window_size_spin.setSuffix(" px")
        self.window_size_spin.setToolTip(
            "Tamanho da janela de captura ao redor do centro (padrão: 50x50 pixels)"
        )
        self.window_size_spin.valueChanged.connect(self._update_window_size)
        capture_layout.addWidget(self.window_size_spin)

        capture_layout.addStretch()

        # Botão de captura
        self.capture_btn = QPushButton("📸 Capturar Template")
        self.capture_btn.clicked.connect(self._capture_template)
        self.capture_btn.setEnabled(False)
        self.capture_btn.setToolTip(
            "Captura a região central do vídeo como template\n"
            "Requer: Preview ativo"
        )
        capture_layout.addWidget(self.capture_btn)

        layout.addWidget(capture_group)

    def _update_window_size(self, size: int):
        """Atualiza tamanho da janela de captura."""
        self._window_size = size
        logger.debug(f"Tamanho da janela atualizado: {size}x{size} pixels")

    def _on_video_click(self, click_x: float, click_y: float):
        """
        Handler para clique no preview de vídeo.

        Move a máquina para centralizar o ponto clicado se click-to-move estiver habilitado.
        """
        # Se clique para capturar template estiver habilitado (shift+clic), captura
        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.KeyboardModifier.ShiftModifier:
            self._capture_template_at(click_x, click_y)
            return

        # Verifica se movimento por clique está habilitado
        if not self.click_move_enabled.isChecked():
            return

        # Verifica se ClickToMoveService está disponível
        if self.click_to_move_service is None:
            logger.warning("ClickToMoveService não disponível")
            return

        # Verifica se CLP está conectado
        if not hasattr(self.controller, 'cnc') or not self.controller.cnc.is_connected:
            logger.warning("CLP não está conectado")
            return

        # Executar movimento
        self._move_via_service(click_x, click_y)

    def _move_via_service(self, click_x: float, click_y: float):
        """Move a posição usando ClickToMoveService."""
        try:
            # Obter tamanho atual da imagem
            image_size = (self.image_label.width(), self.image_label.height())

            # Obter posição Z atual
            z_current = self.controller.cnc.get_current_position().get('z', 0.0)

            # Obter feed rate do movement_widget
            main_window = self.window()
            if main_window and hasattr(main_window, 'movement_widget'):
                feed_rate = main_window.movement_widget.get_current_feed_rate()
            else:
                feed_rate = 1000.0

            # Obter configuração de espelhamento
            invert_y = getattr(main_window, '_camera_mirror_y', False) if main_window else False

            # Executar movimento via service
            result = self.click_to_move_service.move_to_pixel(
                pixel_x=int(click_x),
                pixel_y=int(click_y),
                image_size=image_size,
                z_current=z_current,
                feed_rate=feed_rate,
                invert_y=invert_y
            )

            if result.success:
                if result.movement_made:
                    dx, dy = result.distance_moved
                    logger.info(f"Click-to-move: Δ({dx:.3f}, {dy:.3f}) mm @ {feed_rate} mm/min")
                else:
                    logger.debug("Clique muito próximo do centro, ignorado")
            else:
                logger.error(f"Click-to-move falhou: {result.error_message}")

        except Exception as e:
            logger.error(f"Erro ao processar clique: {e}")

    def _capture_template_at(self, click_x: float, click_y: float):
        """
        Captura template na posição clicada.

        Útil para capturar fiduciais clicando neles diretamente.
        """
        if self.current_image is None:
            logger.warning("Sem imagem para capturar template")
            return

        try:
            h, w = self.current_image.shape[:2]

            # Calcular janela ao redor do ponto clicado
            half_window = self._window_size // 2
            x1 = max(0, int(click_x) - half_window)
            y1 = max(0, int(click_y) - half_window)
            x2 = min(w, int(click_x) + half_window)
            y2 = min(h, int(click_y) + half_window)

            # Extrair template
            template = self.current_image[y1:y2, x1:x2]

            # Obter posição atual da máquina
            pos = self.controller.cnc.get_current_position()
            metadata = {
                'x': pos.get('x', 0.0),
                'y': pos.get('y', 0.0),
                'z': pos.get('z', 0.0),
                'window_size': self._window_size,
                'pixel_x': click_x,
                'pixel_y': click_y
            }

            # Emitir signal
            self.image_captured.emit(template, metadata)
            logger.info(f"Template capturado em ({click_x:.1f}, {click_y:.1f}), tamanho: {template.shape}")

        except Exception as e:
            logger.error(f"Erro ao capturar template: {e}")

    def _capture_template(self):
        """Captura template no centro da imagem."""
        if self.current_image is None:
            QMessageBox.warning(self, "Erro", "Sem imagem para capturar")
            return

        h, w = self.current_image.shape[:2]
        center_x, center_y = w // 2, h // 2

        self._capture_template_at(float(center_x), float(center_y))

    def start_preview(self):
        """Inicia preview da câmera."""
        if not hasattr(self.controller.camera, 'is_connected') or not self.controller.camera.is_connected:
            logger.warning("Câmera não conectada")
            return

        self.preview_timer.start(100)  # Update every 100ms
        self.start_preview_btn.setEnabled(False)
        self.stop_preview_btn.setEnabled(True)
        self.capture_btn.setEnabled(True)
        logger.info("Preview iniciado")

    def stop_preview(self):
        """Para preview da câmera."""
        self.preview_timer.stop()
        self.start_preview_btn.setEnabled(True)
        self.stop_preview_btn.setEnabled(False)
        self.capture_btn.setEnabled(False)
        logger.info("Preview parado")

    def update_preview(self):
        """Atualiza o preview da câmera."""
        try:
            image = self.controller.camera.capture()
            if image is not None:
                # Salva tamanho do frame para conversão de clique
                h, w = image.shape[:2]
                self._last_frame_size = (w, h)

                # Exibe imagem
                self.display_image(image)
                self.current_image = image

                # Emit signal que frame está pronto
                self.frame_ready.emit(image)

        except Exception as e:
            logger.error(f"Erro ao atualizar preview: {e}")
            self.stop_preview()

    def display_image(self, image):
        """
        Exibe imagem na área de preview com crosshair no centro.

        Args:
            image: Imagem OpenCV (numpy array)
        """
        if image is None:
            return

        # Criar cópia para não modificar original
        display_img = image.copy()

        # Aplicar espelhamento se configurado
        main_window = self.window()
        if main_window and getattr(main_window, '_camera_mirror_x', False):
            display_img = cv2.flip(display_img, 1)  # Flip horizontal
        if main_window and getattr(main_window, '_camera_mirror_y', False):
            display_img = cv2.flip(display_img, 0)  # Flip vertical

        # Desenhar cruz de centralização
        h, w = display_img.shape[:2]
        center_x, center_y = w // 2, h // 2

        # Busca configurações da cruz
        crosshair_cfg = self.cfg.get("camera", "crosshair", default={})
        color_b = crosshair_cfg.get("color_b", 255)
        color_g = crosshair_cfg.get("color_g", 0)
        color_r = crosshair_cfg.get("color_r", 0)
        thickness = crosshair_cfg.get("thickness", 2)
        length_percent = crosshair_cfg.get("length_percent", 5)

        # Parâmetros da cruz
        color = (color_b, color_g, color_r)  # BGR format
        length = min(w, h) * length_percent // 100

        # Desenhar cruz
        cv2.line(display_img,
                (center_x - length, center_y),
                (center_x + length, center_y),
                color, thickness)
        cv2.line(display_img,
                (center_x, center_y - length),
                (center_x, center_y + length),
                color, thickness)

        # Converter para QPixmap
        h, w = display_img.shape[:2]
        bytes_per_line = 3 * w
        q_img = QImage(display_img.data, w, h, bytes_per_line,
                      QImage.Format.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(q_img)

        # Redimensionar para caber no widget mantendo proporção
        label_width = self.image_label.width()
        label_height = self.image_label.height()
        pixmap = pixmap.scaled(label_width, label_height,
                              Qt.AspectRatioMode.KeepAspectRatio,
                              Qt.TransformationMode.SmoothTransformation)

        self.image_label.setPixmap(pixmap)

    def resizeEvent(self, event):
        """Override para ajustar imagem quando widget for redimensionado."""
        super().resizeEvent(event)
        if self.current_image is not None:
            self.display_image(self.current_image)

    def get_current_image(self) -> Optional[np.ndarray]:
        """Retorna imagem atual capturada."""
        return self.current_image

    def get_window_size(self) -> int:
        """Retorna tamanho da janela de captura."""
        return self._window_size

    def set_window_size(self, size: int):
        """Define tamanho da janela de captura."""
        self.window_size_spin.setValue(size)
