"""
FiducialCaptureWidget - Widget de Captura de Fiduciais (Aba 3 do Engineering Wizard)

Este widget permite capturar templates dos 2 fiduciais do stencil
usados para alinhamento automático.

Funcionalidades:
- Preview de câmera em tempo real
- Clique para capturar template
- Definição de posição XYZ
- Preview do template capturado
- Validação de qualidade

Autor: Claude Code (Sonnet 4.5)
Data: 2026-01-13
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QGroupBox, QDoubleSpinBox,
    QSpinBox, QMessageBox
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QPixmap, QImage
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class FiducialTemplate:
    """Template de fiducial capturado."""
    id: int
    x: float
    y: float
    z: float
    image: np.ndarray
    window_size: int = 50
    captured_at: str = ""

    def to_dict(self) -> Dict:
        """Converte para dicionário."""
        return {
            'id': self.id,
            'x': self.x,
            'y': self.y,
            'z': self.z,
            'window_size': self.window_size,
            'captured_at': self.captured_at
        }


class FiducialPreviewWidget(QWidget):
    """
    Widget de preview de câmera com clique para captura.

    Features:
        - Preview em tempo real
        - Clique para capturar template
        - Crosshair no centro
    """

    capture_requested = pyqtSignal(float, float)  # x, y na imagem

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(640, 480)

        # Estado
        self._current_frame: Optional[np.ndarray] = None
        self._show_crosshair = True

        # Estilo
        self.setStyleSheet("""
            FiducialPreviewWidget {
                background-color: #000;
                border: 2px solid #444;
                border-radius: 4px;
            }
        """)

    def set_frame(self, frame: np.ndarray):
        """Define frame atual da câmera."""
        self._current_frame = frame
        self.update()

    def mousePressEvent(self, event):
        """Captura template na posição clicada."""
        if event.button() == Qt.MouseButton.LeftButton and self._current_frame is not None:
            x = event.pos().x()
            y = event.pos().y()
            self.capture_requested.emit(float(x), float(y))

    def paintEvent(self, event):
        """Renderiza frame + crosshair."""
        from PyQt6.QtGui import QPainter, QPen, QColor

        painter = QPainter(self)

        # Background preto
        painter.fillRect(self.rect(), QColor("#000000"))

        if self._current_frame is not None:
            # Converter numpy para QImage
            height, width = self._current_frame.shape[:2]
            bytes_per_line = 3 * width

            # Se grayscale, converter para RGB
            if len(self._current_frame.shape) == 2:
                frame_rgb = np.stack([
                    self._current_frame,
                    self._current_frame,
                    self._current_frame
                ], axis=2)
            else:
                frame_rgb = self._current_frame

            q_img = QImage(
                frame_rgb.data,
                width,
                height,
                bytes_per_line,
                QImage.Format.Format_RGB888
            )

            # Desenhar frame ajustado ao widget
            pixmap = QPixmap.fromImage(q_img)
            scaled_pixmap = pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            x_offset = (self.width() - scaled_pixmap.width()) // 2
            y_offset = (self.height() - scaled_pixmap.height()) // 2
            painter.drawPixmap(x_offset, y_offset, scaled_pixmap)

        # Desenhar crosshair
        if self._show_crosshair:
            pen = QPen(QColor("#00FF00"), 1)
            painter.setPen(pen)

            center_x = self.width() // 2
            center_y = self.height() // 2
            crosshair_size = 20

            # Linha horizontal
            painter.drawLine(center_x - crosshair_size, center_y,
                          center_x + crosshair_size, center_y)
            # Linha vertical
            painter.drawLine(center_x, center_y - crosshair_size,
                          center_x, center_y + crosshair_size)

        painter.end()


class FiducialCaptureWidget(QWidget):
    """
    Widget para capturar templates dos 2 fiduciais.

    Signals:
        fiducial_captured(dict): Emitido quando fiducial é capturado
        validation_changed(bool): Emitido quando validação muda
    """

    fiducial_captured = pyqtSignal(dict)
    validation_changed = pyqtSignal(bool)

    def __init__(self, parent=None, hardware_coordinator=None,
                 movement_controller=None, config_manager=None,
                 movement_orchestrator=None):
        """Inicializa o widget.

        Args:
            parent: Widget pai
            hardware_coordinator: EngineeringHardwareCoordinator (opcional)
            movement_controller: CNCAOIController para controle de movimento (opcional)
            config_manager: AOIConfigManager para configuração de movimento (opcional)
            movement_orchestrator: MovementOrchestrator para controle de movimento (opcional)
        """
        super().__init__(parent)
        logger.info("🎨 Inicializando FiducialCaptureWidget")

        # Estado
        self._fiducials: List[FiducialTemplate] = []
        self._current_fiducial_id = 0  # 0 ou 1
        self._window_size = 50
        self._is_valid = False

        # Hardware coordinator (nova arquitetura)
        self._hardware_coordinator = hardware_coordinator
        # Legado: camera_controller (para compatibilidade)
        self._camera_controller = None

        # Controle de movimento (opcional)
        self._movement_controller = movement_controller
        self._config_manager = config_manager
        self._movement_orchestrator = movement_orchestrator

        # Setup UI
        self._setup_ui()

        # Conectar signals
        self._connect_signals()

        # Atualizar estado inicial
        self._update_hardware_status()

        logger.info("✅ FiducialCaptureWidget inicializado")

    def set_hardware_coordinator(self, coordinator):
        """Define o coordenador de hardware (injeção de dependência).

        Args:
            coordinator: EngineeringHardwareCoordinator
        """
        self._hardware_coordinator = coordinator
        self._update_hardware_status()
        logger.info("🔧 Hardware coordinator definido")

    def _update_hardware_status(self):
        """Atualiza display de status do hardware."""
        # Verificar se hardware está disponível
        has_coordinator = self._hardware_coordinator is not None
        has_camera = self._camera_controller is not None

        if has_coordinator:
            # Usar coordinator
            from consumo_lib.coordinators.engineering_hardware_coordinator import HardwareType
            ready, _ = self._hardware_coordinator.is_hardware_ready([
                HardwareType.CAMERA,
                HardwareType.PLC
            ])
            status = "✅ Pronto" if ready else "⚠️ Hardware não conectado"
        elif has_camera:
            # Modo legado
            ready = self._camera_controller.is_connected
            status = "✅ Pronto" if ready else "⚠️ Câmera não conectada"
        else:
            status = "❌ Sem hardware"

        # Se existir label de hardware status, atualizar
        if hasattr(self, 'lbl_hardware_status'):
            self.lbl_hardware_status.setText(f"Hardware: {status}")

    def _setup_ui(self):
        """Configura interface do usuário."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Título
        title = QLabel("🎯 Capturar Fiduciais")
        title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2196F3;
                padding: 10px;
            }
        """)
        layout.addWidget(title)

        # Instrução
        instruction = QLabel(
            "Capture 2 fiduciais do stencil para alinhamento automático.\n"
            "Mova a máquina para cada fiducial e clique na imagem para capturar."
        )
        instruction.setStyleSheet("color: #757575; padding: 5px;")
        layout.addWidget(instruction)

        # Layout principal (preview | controles)
        main_layout = QHBoxLayout()

        # Preview da câmera
        preview_group = QGroupBox("Preview da Câmera")
        preview_layout = QVBoxLayout(preview_group)

        self.preview_widget = FiducialPreviewWidget()
        preview_layout.addWidget(self.preview_widget, 1)

        # Label de status
        self.lbl_camera_status = QLabel("⚠️ Câmera não conectada")
        self.lbl_camera_status.setStyleSheet("""
            QLabel {
                padding: 5px;
                background-color: #FFF3CD;
                border-radius: 4px;
                color: #856404;
            }
        """)
        preview_layout.addWidget(self.lbl_camera_status)

        main_layout.addWidget(preview_group, 2)

        # Controles de movimento (se disponível)
        if self._movement_controller and self._config_manager and self._movement_orchestrator:
            from consumo_lib.widgets.movement_control import MovementControlWidget

            movement_group = QGroupBox("Controle de Movimento")
            movement_layout = QVBoxLayout(movement_group)

            self.movement_control_widget = MovementControlWidget(
                self._movement_controller,
                self._config_manager,
                orchestrator=self._movement_orchestrator
            )
            movement_layout.addWidget(self.movement_control_widget)
            main_layout.addWidget(movement_group, 1)
        elif self._movement_controller or self._config_manager or self._movement_orchestrator:
            # Avisar que parâmetros estão faltando
            logger.warning("⚠️ Parâmetros de movimento incompletos - MovementControlWidget não será criado")

        # Controles
        controls_group = QGroupBox("Controles de Captura")
        controls_layout = QVBoxLayout(controls_group)

        # Seletor de fiducial
        controls_layout.addWidget(QLabel("Fiducial:"))
        self.fiducial_selector = QGridLayout()
        self.btn_fid1 = QPushButton("Fiducial 1")
        self.btn_fid2 = QPushButton("Fiducial 2")
        self.btn_fid1.setCheckable(True)
        self.btn_fid2.setCheckable(True)
        self.btn_fid1.setChecked(True)
        self.btn_fid1.setStyleSheet("""
            QPushButton:checked {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
            }
        """)
        self.btn_fid2.setStyleSheet("""
            QPushButton:checked {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
            }
        """)
        self.fiducial_selector.addWidget(self.btn_fid1, 0, 0)
        self.fiducial_selector.addWidget(self.btn_fid2, 0, 1)
        controls_layout.addLayout(self.fiducial_selector)

        # Posição XYZ
        controls_layout.addWidget(QLabel("Posição da Máquina:"))
        pos_layout = QGridLayout()

        pos_layout.addWidget(QLabel("X (mm):"), 0, 0)
        self.spin_x = QDoubleSpinBox()
        self.spin_x.setRange(-1000, 1000)
        self.spin_x.setDecimals(2)
        self.spin_x.setSuffix(" mm")
        pos_layout.addWidget(self.spin_x, 0, 1)

        pos_layout.addWidget(QLabel("Y (mm):"), 1, 0)
        self.spin_y = QDoubleSpinBox()
        self.spin_y.setRange(-1000, 1000)
        self.spin_y.setDecimals(2)
        self.spin_y.setSuffix(" mm")
        pos_layout.addWidget(self.spin_y, 1, 1)

        pos_layout.addWidget(QLabel("Z (mm):"), 2, 0)
        self.spin_z = QDoubleSpinBox()
        self.spin_z.setRange(-100, 100)
        self.spin_z.setDecimals(2)
        self.spin_z.setSuffix(" mm")
        pos_layout.addWidget(self.spin_z, 2, 1)

        controls_layout.addLayout(pos_layout)

        # Window size
        controls_layout.addWidget(QLabel("Tamanho do Template:"))
        self.spin_window = QSpinBox()
        self.spin_window.setRange(10, 200)
        self.spin_window.setValue(50)
        self.spin_window.setSuffix(" px")
        self.spin_window.setToolTip(
            "Tamanho da janela de captura ao redor do centro.\n"
            "Padrão: 50x50 pixels"
        )
        controls_layout.addWidget(self.spin_window)

        # Botão capturar
        self.btn_capture = QPushButton("📸 Capturar Template")
        self.btn_capture.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
                color: #757575;
            }
        """)
        self.btn_capture.setEnabled(False)
        controls_layout.addWidget(self.btn_capture)

        controls_layout.addStretch()

        # Status dos fiduciais
        controls_layout.addWidget(QLabel("Status:"))
        self.lbl_fid1_status = QLabel("❌ Fiducial 1: Não capturado")
        self.lbl_fid2_status = QLabel("❌ Fiducial 2: Não capturado")
        controls_layout.addWidget(self.lbl_fid1_status)
        controls_layout.addWidget(self.lbl_fid2_status)

        main_layout.addWidget(controls_group, 1)

        layout.addLayout(main_layout, 1)

        # Status geral
        self.status_label = QLabel("⚠️ Capture 2 fiduciais para continuar")
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
        self.btn_fid1.clicked.connect(lambda: self._select_fiducial(0))
        self.btn_fid2.clicked.connect(lambda: self._select_fiducial(1))
        self.preview_widget.capture_requested.connect(self._on_capture_requested)
        self.btn_capture.clicked.connect(self._on_capture_clicked)
        self.spin_window.valueChanged.connect(self._on_window_changed)

    def set_camera_controller(self, camera_controller):
        """Define controller de câmera (injeção de dependência)."""
        self._camera_controller = camera_controller
        if camera_controller and camera_controller.is_connected:
            self.lbl_camera_status.setText("✅ Câmera conectada")
            self.lbl_camera_status.setStyleSheet("""
                QLabel {
                    padding: 5px;
                    background-color: #D4EDDA;
                    border-radius: 4px;
                    color: #155724;
                }
            """)
            self.btn_capture.setEnabled(True)

    def _select_fiducial(self, fid_id: int):
        """Seleciona fiducial ativo."""
        self._current_fiducial_id = fid_id

        # Atualizar botões
        if fid_id == 0:
            self.btn_fid1.setChecked(True)
            self.btn_fid2.setChecked(False)
        else:
            self.btn_fid1.setChecked(False)
            self.btn_fid2.setChecked(True)

    def _on_window_changed(self, size: int):
        """Handler quando window size muda."""
        self._window_size = size

    def _on_capture_requested(self, x: float, y: float):
        """Handler quando usuário clica no preview."""
        # Capturar template
        self._capture_fiducial_at(x, y)

    def _on_capture_clicked(self):
        """Handler do botão capturar (captura no centro)."""
        if self.preview_widget.width() > 0 and self.preview_widget.height() > 0:
            center_x = self.preview_widget.width() / 2
            center_y = self.preview_widget.height() / 2
            self._capture_fiducial_at(center_x, center_y)

    def _capture_fiducial_at(self, x: float, y: float):
        """Captura template na posição especificada."""
        try:
            # Prioridade: Usar EngineeringHardwareCoordinator se disponível
            if self._hardware_coordinator:
                self._capture_with_coordinator(x, y)
            elif self._camera_controller:
                self._capture_with_camera_controller(x, y)
            else:
                QMessageBox.warning(
                    self,
                    "Hardware Não Disponível",
                    "Nenhum hardware disponível. Conecte o coordenador de hardware ou câmera."
                )
                return

        except Exception as e:
            logger.error(f"❌ Erro ao capturar fiducial: {e}")
            QMessageBox.critical(
                self,
                "Erro de Captura",
                f"Não foi possível capturar fiducial:\n{e}"
            )

    def _capture_with_coordinator(self, x: float, y: float):
        """Captura usando EngineeringHardwareCoordinator.

        Args:
            x: Posição X no preview (não usado, captura é no centro)
            y: Posição Y no preview (não usado, captura é no centro)
        """
        from consumo_lib.coordinators.engineering_hardware_coordinator import HardwareType

        # Verificar hardware
        ready, message = self._hardware_coordinator.is_hardware_ready([
            HardwareType.CAMERA,
            HardwareType.PLC
        ])
        if not ready:
            QMessageBox.warning(
                self,
                "Hardware Não Pronto",
                f"Hardware indisponível:\n{message}"
            )
            return

        # Obter posição dos spinboxes
        pos_x = self.spin_x.value()
        pos_y = self.spin_y.value()
        pos_z = self.spin_z.value()

        try:
            # Capturar usando coordinator
            result = self._hardware_coordinator.capture_fiducial_template(
                x=pos_x,
                y=pos_y,
                z=pos_z,
                window_size=self._window_size
            )

            # Criar fiducial
            fiducial = FiducialTemplate(
                id=self._current_fiducial_id,
                x=pos_x,
                y=pos_y,
                z=pos_z,
                image=result['image'],
                window_size=self._window_size,
                captured_at=result.get('captured_at', datetime.now().isoformat())
            )

            # Remover fiducial anterior do mesmo ID se existir
            self._fiducials = [f for f in self._fiducials if f.id != self._current_fiducial_id]
            self._fiducials.append(fiducial)

            # Emitir signal
            self.fiducial_captured.emit(fiducial.to_dict())

            # Atualizar UI
            self._update_status()

            logger.info(f"✅ Fiducial {self._current_fiducial_id + 1} capturado via coordinator")

        except RuntimeError as e:
            QMessageBox.warning(
                self,
                "Erro de Captura",
                f"Erro ao capturar fiducial:\n{e}"
            )

    def _capture_with_camera_controller(self, x: float, y: float):
        """Captura usando camera_controller (modo legado).

        Args:
            x: Posição X no preview
            y: Posição Y no preview
        """
        if not self._camera_controller or not self._camera_controller.is_connected:
            QMessageBox.warning(
                self,
                "Câmera Não Conectada",
                "Conecte a câmera antes de capturar fiduciais."
            )
            return

        # Obter frame atual
        frame = self._camera_controller.capture_frame()
        if frame is None:
            QMessageBox.warning(
                self,
                "Erro de Captura",
                "Não foi possível capturar imagem da câmera."
            )
            return

        # Extrair template (window ao redor do ponto)
        half_window = self._window_size // 2
        h, w = frame.shape[:2]
        x0 = int(max(0, x - half_window))
        y0 = int(max(0, y - half_window))
        x1 = int(min(w, x + half_window))
        y1 = int(min(h, y + half_window))

        template = frame[y0:y1, x0:x1]

        if template.size == 0:
            QMessageBox.warning(
                self,
                "Erro de Captura",
                "Região de captura inválida."
            )
            return

        # Obter posição da máquina
        pos_x = self.spin_x.value()
        pos_y = self.spin_y.value()
        pos_z = self.spin_z.value()

        # Criar fiducial
        fiducial = FiducialTemplate(
            id=self._current_fiducial_id,
            x=pos_x,
            y=pos_y,
            z=pos_z,
            image=template,
            window_size=self._window_size,
            captured_at=datetime.now().isoformat()
        )

        # Remover fiducial anterior do mesmo ID se existir
        self._fiducials = [f for f in self._fiducials if f.id != self._current_fiducial_id]
        self._fiducials.append(fiducial)

        # Emitir signal
        self.fiducial_captured.emit(fiducial.to_dict())

        # Atualizar UI
        self._update_status()

        logger.info(f"✅ Fiducial {self._current_fiducial_id + 1} capturado (modo legado)")

    def _update_status(self):
        """Atualiza display de status."""
        # Atualizar labels individuais
        fid1_captured = any(f.id == 0 for f in self._fiducials)
        fid2_captured = any(f.id == 1 for f in self._fiducials)

        if fid1_captured:
            self.lbl_fid1_status.setText("✅ Fiducial 1: Capturado")
            self.lbl_fid1_status.setStyleSheet("color: #4CAF50; font-weight: bold;")
        else:
            self.lbl_fid1_status.setText("❌ Fiducial 1: Não capturado")
            self.lbl_fid1_status.setStyleSheet("color: #F44336;")

        if fid2_captured:
            self.lbl_fid2_status.setText("✅ Fiducial 2: Capturado")
            self.lbl_fid2_status.setStyleSheet("color: #4CAF50; font-weight: bold;")
        else:
            self.lbl_fid2_status.setText("❌ Fiducial 2: Não capturado")
            self.lbl_fid2_status.setStyleSheet("color: #F44336;")

        # Validar
        is_valid = fid1_captured and fid2_captured
        was_valid = self._is_valid
        self._is_valid = is_valid

        if is_valid:
            self.status_label.setText(
                f"✅ 2 fiduciais capturados - Pronto para alinhamento"
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
        else:
            captured_count = len(self._fiducials)
            self.status_label.setText(
                f"⚠️ Capture {2 - captured_count} fiduciais para continuar"
            )
            self.status_label.setStyleSheet("""
                QLabel {
                    padding: 10px;
                    background-color: #FFF3CD;
                    border: 1px solid #FFC107;
                    border-radius: 4px;
                    color: #856404;
                }
            """)

        # Emitir signal se validação mudou
        if was_valid != is_valid:
            self.validation_changed.emit(is_valid)

    def get_fiducial_templates(self) -> List[Dict]:
        """
        Retorna templates capturados.

        Returns:
            Lista de dicts com dados dos fiduciais
        """
        return [f.to_dict() for f in self._fiducials]

    def is_valid(self) -> bool:
        """Verifica se 2 fiduciais foram capturados."""
        return self._is_valid

    def clear(self):
        """Limpa todas as capturas."""
        logger.info("🗑️ Limpando fiduciais")

        self._fiducials.clear()
        self._update_status()
