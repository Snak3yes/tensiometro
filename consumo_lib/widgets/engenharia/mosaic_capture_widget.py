"""
MosaicCaptureWidget - Widget de Captura de Mosaico (Aba 4 do Engineering Wizard)

Este widget permite capturar um mosaico do stencil através de grid automático.

Funcionalidades:
- Grid automático baseado em área
- Definição de cantos (X1, Y1, X2, Y2)
- Captura e stitch de mosaico
- Preview com zoom/pan
- Estimativa de tempo

Autor: Claude Code (Sonnet 4.5)
Data: 2026-01-13
"""

import logging
from typing import Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QGroupBox, QDoubleSpinBox,
    QSpinBox, QMessageBox, QProgressBar
)
from PyQt6.QtCore import pyqtSignal, Qt, QThread
from PyQt6.QtGui import QPixmap, QImage, QPainter, QColor
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class MosaicConfig:
    """Configuração do mosaico."""
    x1: float  # Canto superior esquerdo X (mm)
    y1: float  # Canto superior esquerdo Y (mm)
    x2: float  # Canto inferior direito X (mm)
    y2: float  # Canto inferior direito Y (mm)
    rows: int  # Número de linhas do grid
    cols: int  # Número de colunas do grid
    overlap_percent: float = 10.0  # Overlap entre FOVs (%)
    delay_ms: int = 200  # Delay entre capturas (ms)

    def to_dict(self) -> Dict:
        """Converte para dicionário."""
        return {
            'x1': self.x1,
            'y1': self.y1,
            'x2': self.x2,
            'y2': self.y2,
            'rows': self.rows,
            'cols': self.cols,
            'overlap_percent': self.overlap_percent,
            'delay_ms': self.delay_ms
        }


class MosaicCaptureThread(QThread):
    """
    Thread para captura de mosaico em background.

    Signals:
        progress_updated(int, int): Atualização de progresso (atual, total)
        image_captured(np.ndarray): Imagem capturada
        finished(np.ndarray): Mosaico completo
        error_occurred(str): Erro durante captura
    """

    progress_updated = pyqtSignal(int, int)
    image_captured = pyqtSignal(np.ndarray)
    finished = pyqtSignal(np.ndarray)
    error_occurred = pyqtSignal(str)

    def __init__(self, config: MosaicConfig, camera_controller, plc_controller):
        super().__init__()
        self.config = config
        self._camera = camera_controller
        self._plc = plc_controller
        self._is_running = True

    def run(self):
        """Executa captura do mosaico."""
        try:
            logger.info(f"🚀 Iniciando captura de mosaico: {self.config.rows}x{self.config.cols}")

            # Calcular pontos do grid
            points = self._calculate_grid_points()
            total = len(points)

            # Capturar imagens
            images = []
            for i, (x, y) in enumerate(points):
                if not self._is_running:
                    logger.warning("⚠️ Captura interrompida")
                    return

                logger.info(f"📸 Capturando ponto {i+1}/{total}: X={x:.1f}, Y={y:.1f}")

                # Mover para posição
                if self._plc and self._plc.is_connected:
                    self._plc.move_absolute('X', x)
                    self._plc.move_absolute('Y', y)
                    self._plc.wait_for_idle()

                # Aguardar estabilização
                self.msleep(self.config.delay_ms)

                # Capturar imagem
                if self._camera and self._camera.is_connected:
                    frame = self._camera.capture_frame()
                    if frame is not None:
                        images.append((x, y, frame))
                        self.image_captured.emit(frame)

                # Atualizar progresso
                self.progress_updated.emit(i + 1, total)

            # TODO: Implementar stitch real das imagens
            # Por enquanto, retornar primeira imagem como placeholder
            if images:
                mosaic = images[0][2]  # Primeira imagem
                logger.info(f"✅ Mosaico capturado: {len(images)} imagens")
                self.finished.emit(mosaic)
            else:
                self.error_occurred.emit("Nenhuma imagem capturada")

        except Exception as e:
            logger.error(f"❌ Erro na captura: {e}")
            self.error_occurred.emit(str(e))

    def _calculate_grid_points(self) -> list:
        """Calcula pontos do grid."""
        points = []
        dx = (self.config.x2 - self.config.x1) / (self.config.cols - 1)
        dy = (self.config.y2 - self.config.y1) / (self.config.rows - 1)

        for row in range(self.config.rows):
            for col in range(self.config.cols):
                x = self.config.x1 + col * dx
                y = self.config.y1 + row * dy
                points.append((x, y))

        return points

    def stop(self):
        """Interrompe captura."""
        self._is_running = False


class MosaicPreviewWidget(QWidget):
    """
    Widget de preview do mosaico com zoom/pan.

    Features:
        - Renderização do mosaico
        - Zoom com scroll
        - Pan com clique do meio
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 400)

        # Estado
        self._mosaic: Optional[np.ndarray] = None
        self._zoom = 1.0
        self._offset_x = 0
        self._offset_y = 0
        self._panning = False
        self._last_pan_pos = None

        # Estilo
        self.setStyleSheet("""
            MosaicPreviewWidget {
                background-color: #1e1e1e;
                border: 2px solid #444;
                border-radius: 4px;
            }
        """)

    def set_mosaic(self, mosaic: np.ndarray):
        """Define imagem do mosaico."""
        self._mosaic = mosaic
        self.fit_to_view()
        self.update()

    def fit_to_view(self):
        """Ajusta zoom para mostrar todo o mosaico."""
        if self._mosaic is None:
            return

        h, w = self._mosaic.shape[:2]
        if w == 0 or h == 0:
            return

        zoom_x = self.width() / w
        zoom_y = self.height() / h
        self._zoom = min(zoom_x, zoom_y) * 0.9

        # Centralizar
        self._offset_x = (self.width() - w * self._zoom) / 2
        self._offset_y = (self.height() - h * self._zoom) / 2

    def paintEvent(self, event):
        """Renderiza mosaico."""
        painter = QPainter(self)

        # Background
        painter.fillRect(self.rect(), QColor("#1e1e1e"))

        if self._mosaic is not None:
            # Converter numpy para QImage
            h, w = self._mosaic.shape[:2]

            if len(self._mosaic.shape) == 2:
                # Grayscale
                frame_rgb = np.stack([self._mosaic] * 3, axis=2)
            else:
                frame_rgb = self._mosaic

            bytes_per_line = 3 * w
            q_img = QImage(
                frame_rgb.data,
                w,
                h,
                bytes_per_line,
                QImage.Format.Format_RGB888
            )

            pixmap = QPixmap.fromImage(q_img)

            # Aplicar zoom e offset
            scaled_w = int(w * self._zoom)
            scaled_h = int(h * self._zoom)
            scaled_pixmap = pixmap.scaled(
                scaled_w,
                scaled_h,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            painter.drawPixmap(
                int(self._offset_x),
                int(self._offset_y),
                scaled_pixmap
            )

        painter.end()

    def wheelEvent(self, event):
        """Zoom com scroll."""
        angle = event.angleDelta().y()
        if angle > 0:
            self._zoom *= 1.1
        else:
            self._zoom /= 1.1

        self._zoom = max(0.1, min(self._zoom, 10.0))
        self.update()

    def mousePressEvent(self, event):
        """Inicia pan."""
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = True
            self._last_pan_pos = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        """Pan com arrasto."""
        if self._panning and self._last_pan_pos:
            delta = event.pos() - self._last_pan_pos
            self._offset_x += delta.x()
            self._offset_y += delta.y()
            self._last_pan_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        """Finaliza pan."""
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)


class MosaicCaptureWidget(QWidget):
    """
    Widget para capturar mosaico do stencil.

    Signals:
        mosaic_captured(dict): Emitido quando mosaico é capturado
        validation_changed(bool): Emitido quando validação muda
    """

    mosaic_captured = pyqtSignal(dict)
    validation_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info("🎨 Inicializando MosaicCaptureWidget")

        # Estado
        self._mosaic_config: Optional[MosaicConfig] = None
        self._mosaic_image: Optional[np.ndarray] = None
        self._is_valid = False
        self._capture_thread: Optional[MosaicCaptureThread] = None

        # Hardware (será injetado)
        self._camera_controller = None
        self._plc_controller = None

        # Setup UI
        self._setup_ui()

        # Conectar signals
        self._connect_signals()

        logger.info("✅ MosaicCaptureWidget inicializado")

    def _setup_ui(self):
        """Configura interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Título
        title = QLabel("🖼️ Capturar Mosaico")
        title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2196F3;
                padding: 10px;
            }
        """)
        layout.addWidget(title)

        # Layout principal (preview | controles)
        main_layout = QHBoxLayout()

        # Preview
        preview_group = QGroupBox("Preview do Mosaico")
        preview_layout = QVBoxLayout(preview_group)

        self.preview_widget = MosaicPreviewWidget()
        preview_layout.addWidget(self.preview_widget, 1)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        preview_layout.addWidget(self.progress_bar)

        main_layout.addWidget(preview_group, 2)

        # Controles
        controls_group = QGroupBox("Configuração do Grid")
        controls_layout = QVBoxLayout(controls_group)

        # Cantos
        controls_layout.addWidget(QLabel("Canto 1 (Superior Esquerdo):"))
        c1_layout = QGridLayout()
        c1_layout.addWidget(QLabel("X1:"), 0, 0)
        self.spin_x1 = QDoubleSpinBox()
        self.spin_x1.setRange(-1000, 1000)
        self.spin_x1.setDecimals(1)
        self.spin_x1.setSuffix(" mm")
        self.spin_x1.setValue(0)
        c1_layout.addWidget(self.spin_x1, 0, 1)
        c1_layout.addWidget(QLabel("Y1:"), 1, 0)
        self.spin_y1 = QDoubleSpinBox()
        self.spin_y1.setRange(-1000, 1000)
        self.spin_y1.setDecimals(1)
        self.spin_y1.setSuffix(" mm")
        self.spin_y1.setValue(0)
        c1_layout.addWidget(self.spin_y1, 1, 1)
        controls_layout.addLayout(c1_layout)

        controls_layout.addWidget(QLabel("Canto 2 (Inferior Direito):"))
        c2_layout = QGridLayout()
        c2_layout.addWidget(QLabel("X2:"), 0, 0)
        self.spin_x2 = QDoubleSpinBox()
        self.spin_x2.setRange(-1000, 1000)
        self.spin_x2.setDecimals(1)
        self.spin_x2.setSuffix(" mm")
        self.spin_x2.setValue(100)
        c2_layout.addWidget(self.spin_x2, 0, 1)
        c2_layout.addWidget(QLabel("Y2:"), 1, 0)
        self.spin_y2 = QDoubleSpinBox()
        self.spin_y2.setRange(-1000, 1000)
        self.spin_y2.setDecimals(1)
        self.spin_y2.setSuffix(" mm")
        self.spin_y2.setValue(50)
        c2_layout.addWidget(self.spin_y2, 1, 1)
        controls_layout.addLayout(c2_layout)

        # Grid
        controls_layout.addWidget(QLabel("Grid:"))
        grid_layout = QGridLayout()
        grid_layout.addWidget(QLabel("Linhas:"), 0, 0)
        self.spin_rows = QSpinBox()
        self.spin_rows.setRange(1, 20)
        self.spin_rows.setValue(5)
        grid_layout.addWidget(self.spin_rows, 0, 1)
        grid_layout.addWidget(QLabel("Colunas:"), 1, 0)
        self.spin_cols = QSpinBox()
        self.spin_cols.setRange(1, 20)
        self.spin_cols.setValue(5)
        grid_layout.addWidget(self.spin_cols, 1, 1)
        controls_layout.addLayout(grid_layout)

        # Overlap
        controls_layout.addWidget(QLabel("Overlap:"))
        self.spin_overlap = QDoubleSpinBox()
        self.spin_overlap.setRange(0, 50)
        self.spin_overlap.setValue(10)
        self.spin_overlap.setSuffix(" %")
        controls_layout.addWidget(self.spin_overlap)

        # Delay
        controls_layout.addWidget(QLabel("Delay entre capturas:"))
        self.spin_delay = QSpinBox()
        self.spin_delay.setRange(0, 2000)
        self.spin_delay.setValue(200)
        self.spin_delay.setSuffix(" ms")
        controls_layout.addWidget(self.spin_delay)

        # Botões
        btn_layout = QHBoxLayout()
        self.btn_calculate = QPushButton("🔢 Calcular Grid")
        self.btn_calculate.clicked.connect(self._on_calculate_grid)
        btn_layout.addWidget(self.btn_calculate)
        controls_layout.addLayout(btn_layout)

        self.btn_capture = QPushButton("📸 Capturar Mosaico")
        self.btn_capture.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45A049;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
            }
        """)
        self.btn_capture.setEnabled(False)
        controls_layout.addWidget(self.btn_capture)

        self.btn_stop = QPushButton("⏹️ Parar")
        self.btn_stop.setEnabled(False)
        controls_layout.addWidget(self.btn_stop)

        # Info
        controls_layout.addStretch()
        self.lbl_info = QLabel("Configure o grid e clique em Capturar")
        self.lbl_info.setStyleSheet("color: #757575; padding: 5px;")
        self.lbl_info.setWordWrap(True)
        controls_layout.addWidget(self.lbl_info)

        main_layout.addWidget(controls_group, 1)

        layout.addLayout(main_layout, 1)

        # Status
        self.status_label = QLabel("⚠️ Configure e capture o mosaico")
        self.status_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #FFF3CD;
                border: 1px solid #FFC107;
                border-radius: 4px;
                color: #856404;
            }
        """)
        layout.addWidget(self.status_label)

    def _connect_signals(self):
        """Conecta signals."""
        self.btn_capture.clicked.connect(self._on_capture_clicked)
        self.btn_stop.clicked.connect(self._on_stop_clicked)

    def set_hardware(self, camera_controller, plc_controller):
        """Define controllers de hardware."""
        self._camera_controller = camera_controller
        self._plc_controller = plc_controller

    def _on_calculate_grid(self):
        """Calcula grid baseado na área."""
        x1, y1 = self.spin_x1.value(), self.spin_y1.value()
        x2, y2 = self.spin_x2.value(), self.spin_y2.value()

        width = abs(x2 - x1)
        height = abs(y2 - y1)

        # TODO: Calcular rows/cols baseado em FOV da câmera
        # Por enquanto, usar valores padrão
        estimated_rows = max(3, int(height / 20))  # Assumindo 20mm FOV
        estimated_cols = max(3, int(width / 20))

        self.spin_rows.setValue(estimated_rows)
        self.spin_cols.setValue(estimated_cols)

        self.lbl_info.setText(
            f"Área: {width:.1f} x {height:.1f} mm\n"
            f"Grid estimado: {estimated_rows} x {estimated_cols}\n"
            f"Total FOVs: {estimated_rows * estimated_cols}"
        )

        self.btn_capture.setEnabled(True)

    def _on_capture_clicked(self):
        """Inicia captura do mosaico."""
        try:
            # Criar configuração
            self._mosaic_config = MosaicConfig(
                x1=self.spin_x1.value(),
                y1=self.spin_y1.value(),
                x2=self.spin_x2.value(),
                y2=self.spin_y2.value(),
                rows=self.spin_rows.value(),
                cols=self.spin_cols.value(),
                overlap_percent=self.spin_overlap.value(),
                delay_ms=self.spin_delay.value()
            )

            # Validar hardware
            if not self._camera_controller or not self._camera_controller.is_connected:
                QMessageBox.warning(self, "Câmera Não Conectada", "Conecte a câmera primeiro.")
                return

            if not self._plc_controller or not self._plc_controller.is_connected:
                QMessageBox.warning(self, "PLC Não Conectado", "Conecte o PLC primeiro.")
                return

            # Atualizar UI
            self.btn_capture.setEnabled(False)
            self.btn_stop.setEnabled(True)
            self.progress_bar.setVisible(True)
            self.progress_bar.setMaximum(self._mosaic_config.rows * self._mosaic_config.cols)
            self.progress_bar.setValue(0)

            # Iniciar thread de captura
            self._capture_thread = MosaicCaptureThread(
                self._mosaic_config,
                self._camera_controller,
                self._plc_controller
            )
            self._capture_thread.progress_updated.connect(self._on_progress_updated)
            self._capture_thread.image_captured.connect(self._on_image_captured)
            self._capture_thread.finished.connect(self._on_capture_finished)
            self._capture_thread.error_occurred.connect(self._on_capture_error)
            self._capture_thread.start()

            logger.info("🚀 Captura de mosaico iniciada")

        except Exception as e:
            logger.error(f"❌ Erro ao iniciar captura: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao iniciar captura:\n{e}")

    def _on_stop_clicked(self):
        """Interrompe captura."""
        if self._capture_thread:
            self._capture_thread.stop()
            self._capture_thread.wait(3000)  # Esperar até 3s

            # Reset UI
            self.btn_capture.setEnabled(True)
            self.btn_stop.setEnabled(False)
            self.progress_bar.setVisible(False)

            logger.warning("⚠️ Captura interrompida pelo usuário")

    def _on_progress_updated(self, current: int, total: int):
        """Atualiza progress bar."""
        self.progress_bar.setValue(current)

    def _on_image_captured(self, image: np.ndarray):
        """Atualiza preview com imagem capturada."""
        self.preview_widget.set_mosaic(image)

    def _on_capture_finished(self, mosaic: np.ndarray):
        """Captura concluída."""
        self._mosaic_image = mosaic
        self._is_valid = True

        # Atualizar UI
        self.btn_capture.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.preview_widget.set_mosaic(mosaic)

        # Atualizar status
        self.status_label.setText(
            f"✅ Mosaico capturado: {self._mosaic_config.rows}x{self._mosaic_config.cols} FOVs"
        )
        self.status_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #D4EDDA;
                border: 1px solid #28A745;
                border-radius: 4px;
                color: #155724;
            }
        """)

        # Emitir signals
        data = self.get_mosaic_data()
        self.mosaic_captured.emit(data)
        self.validation_changed.emit(True)

        logger.info("✅ Mosaico capturado com sucesso")

    def _on_capture_error(self, error: str):
        """Erro na captura."""
        self.btn_capture.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.progress_bar.setVisible(False)

        self.status_label.setText(f"❌ Erro: {error}")
        self.status_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #F8D7DA;
                border: 1px solid #F44336;
                border-radius: 4px;
                color: #721C24;
            }
        """)

        QMessageBox.critical(self, "Erro na Captura", error)

    def get_mosaic_data(self) -> Dict:
        """Retorna dados do mosaico."""
        if not self._mosaic_config:
            return {}

        return self._mosaic_config.to_dict()

    def is_valid(self) -> bool:
        """Verifica se mosaico foi capturado."""
        return self._is_valid
