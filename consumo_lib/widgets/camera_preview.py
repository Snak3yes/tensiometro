import cv2
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QHBoxLayout,
    QPushButton, QCheckBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QImage

from aoi_lib.config_manager import AOIConfigManager
from aoi_lib.fov_calibration import (
    FOVCalibration, CameraFOVConverter, ClickableVideoLabel
)

logger = logging.getLogger(__name__)
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
        if not hasattr(self.controller, 'cnc') or not self.controller.cnc.is_connected:
            QMessageBox.warning(
                self, "CLP Não Conectado",
                "O CLP não está conectado. Conecte antes de usar movimento por clique."
            )
            return
        
        try:
            # Obtém posição Z atual para calibração correta
            z_current = self.controller.cnc.get_current_position().get('z', 0)
            
            # Atualiza tamanho do frame no conversor
            self.fov_converter.set_frame_size(*self._last_frame_size)
            
            # Converte clique em movimento (retorna pulsos)
            # NOTA: Sistema de coordenadas de imagem (Y para baixo) vs CNC
            # A função video_click_to_movement já aplica a inversão necessária:
            # - Por padrão (invert_y=False): Y é negado para corrigir orientação
            # - Se _camera_mirror_y=True: imagem está espelhada, passa invert_y=True para cancelar a negação
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
                
                # Converte pulsos para mm
                dx_mm = dx_pulses / self.controller.cnc.pulses_per_mm if dx_pulses != 0 else None
                dy_mm = dy_pulses / self.controller.cnc.pulses_per_mm if dy_pulses != 0 else None
                
                # Usa mesma velocidade configurada no widget de movimento (mm/min)
                main_window = self.window()
                if hasattr(main_window, 'movement_widget'):
                    feed_rate = main_window.movement_widget.get_current_feed_rate()
                else:
                    feed_rate = 1000  # Fallback padrão
                
                # Usa move_relative do PLCAxisController (espera mm e mm/min)
                self.controller.cnc.move_relative(x=dx_mm, y=dy_mm, feed_rate=feed_rate)
            else:
                logger.debug("Clique muito próximo do centro, ignorado")
                
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
        
        # Desenhar a cruz de centralização no centro
        h, w = display_img.shape[:2]
        center_x, center_y = w // 2, h // 2
        
        # Busca configurações da cruz do config manager
        crosshair_cfg = self.cfg.get("camera", "crosshair", default={})
        color_b = crosshair_cfg.get("color_b", 255)
        color_g = crosshair_cfg.get("color_g", 0)
        color_r = crosshair_cfg.get("color_r", 0)
        thickness = crosshair_cfg.get("thickness", 2)
        length_percent = crosshair_cfg.get("length_percent", 5)
        
        # Parâmetros da cruz
        color = (color_b, color_g, color_r)  # BGR format for OpenCV
        length = min(w, h) * length_percent // 100  # Comprimento baseado em percentual
        
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



