from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGroupBox
from PyQt6.QtGui import QPixmap
import logging

logger = logging.getLogger(__name__)
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



