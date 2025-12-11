"""
fov_calibration.py
------------------
Calibração de Campo de Visão (FOV) e conversão de coordenadas.

Este módulo permite:
- Calibrar a relação entre pixels da câmera e dimensões físicas (mm)
- Converter clique no vídeo em movimento da head
- A calibração considera a variação do FOV com a altura Z

Conceito:
- Em Z=Z0 (mais alto), a câmera vê uma área maior (largura W0 x altura H0)
- Em Z=Z1 (mais baixo), a câmera vê uma área menor (largura W1 x altura H1)
- A relação é linear: FOV(Z) = a*Z + b

Uso típico:
1. Calibrar em dois pontos de Z (ex: Z=0 e Z=200 pulsos)
2. O sistema calcula os coeficientes a e b para largura e altura
3. Para qualquer Z, calcula-se mm/pixel e converte clique em movimento
"""

import math
import logging
from typing import Dict, Tuple, Optional, Any
from dataclasses import dataclass, asdict

log = logging.getLogger(__name__)


# ============================================================================
#  ESTRUTURAS DE DADOS
# ============================================================================

@dataclass
class FOVCalibration:
    """
    Dados de calibração do campo de visão em dois pontos de Z.
    
    A relação FOV(Z) = a*Z + b é calculada por interpolação linear:
    - Em z0_z_pulses: largura = z0_width_mm, altura = z0_height_mm
    - Em z1_z_pulses: largura = z1_width_mm, altura = z1_height_mm
    """
    z0_z_pulses: int = 0
    z0_width_mm: float = 50.0
    z0_height_mm: float = 37.5
    
    z1_z_pulses: int = 200
    z1_width_mm: float = 30.0
    z1_height_mm: float = 22.5
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FOVCalibration":
        return cls(
            z0_z_pulses=data.get("z0_z_pulses", 0),
            z0_width_mm=data.get("z0_width_mm", 50.0),
            z0_height_mm=data.get("z0_height_mm", 37.5),
            z1_z_pulses=data.get("z1_z_pulses", 200),
            z1_width_mm=data.get("z1_width_mm", 30.0),
            z1_height_mm=data.get("z1_height_mm", 22.5),
        )


# ============================================================================
#  CLASSE DE CONVERSÃO DE COORDENADAS
# ============================================================================

class CameraFOVConverter:
    """
    Converte coordenadas de pixel da câmera para unidades físicas (mm, pulsos).
    
    A conversão considera:
    - Calibração de FOV em dois pontos de Z
    - Calibração de pulsos/mm por eixo
    - Tamanho do frame da câmera em pixels
    """
    
    def __init__(self, fov_calibration: Optional[FOVCalibration] = None):
        self.fov = fov_calibration or FOVCalibration()
        
        # Coeficientes calculados (FOV = a*Z + b)
        self._coeff_width_a: float = 0.0
        self._coeff_width_b: float = 50.0
        self._coeff_height_a: float = 0.0
        self._coeff_height_b: float = 37.5
        
        # Calibração de eixos (pulsos por mm)
        self._pulses_per_mm: Dict[str, float] = {
            "X": 100.0,
            "Y": 100.0,
            "Z": 100.0,
        }
        
        # Tamanho do frame da câmera (atualizado externamente)
        self.frame_width: int = 640
        self.frame_height: int = 480
        
        # Calcula coeficientes iniciais
        self._update_coefficients()
    
    def set_fov_calibration(self, fov: FOVCalibration):
        """Define calibração de FOV e recalcula coeficientes."""
        self.fov = fov
        self._update_coefficients()
    
    def set_axis_calibration(self, axis: str, pulses_per_mm: float):
        """Define calibração de um eixo (pulsos/mm)."""
        self._pulses_per_mm[axis] = pulses_per_mm
    
    def set_frame_size(self, width: int, height: int):
        """Define tamanho do frame da câmera."""
        self.frame_width = width
        self.frame_height = height
    
    def _update_coefficients(self):
        """Calcula coeficientes lineares a partir da calibração."""
        z0 = float(self.fov.z0_z_pulses)
        z1 = float(self.fov.z1_z_pulses)
        
        # Evita divisão por zero
        dz = z1 - z0
        if abs(dz) < 1e-6:
            dz = 1.0
        
        # Largura: w(z) = aX * z + bX
        w0 = self.fov.z0_width_mm
        w1 = self.fov.z1_width_mm
        self._coeff_width_a = (w1 - w0) / dz
        self._coeff_width_b = w0 - self._coeff_width_a * z0
        
        # Altura: h(z) = aY * z + bY
        h0 = self.fov.z0_height_mm
        h1 = self.fov.z1_height_mm
        self._coeff_height_a = (h1 - h0) / dz
        self._coeff_height_b = h0 - self._coeff_height_a * z0
        
        log.debug(f"Coeficientes FOV: "
                 f"width = {self._coeff_width_a:.4f}*Z + {self._coeff_width_b:.2f}, "
                 f"height = {self._coeff_height_a:.4f}*Z + {self._coeff_height_b:.2f}")
    
    def get_fov_at_z(self, z_pulses: int) -> Tuple[float, float]:
        """
        Retorna o campo de visão (largura, altura) em mm para uma posição Z.
        
        Returns:
            (width_mm, height_mm)
        """
        width_mm = self._coeff_width_a * z_pulses + self._coeff_width_b
        height_mm = self._coeff_height_a * z_pulses + self._coeff_height_b
        return width_mm, height_mm
    
    def get_mm_per_pixel(self, z_pulses: int) -> Tuple[float, float]:
        """
        Retorna a escala mm/pixel para uma posição Z.
        
        Returns:
            (mm_per_pixel_x, mm_per_pixel_y)
        """
        width_mm, height_mm = self.get_fov_at_z(z_pulses)
        
        mm_per_px_x = width_mm / self.frame_width if self.frame_width > 0 else 0.1
        mm_per_px_y = height_mm / self.frame_height if self.frame_height > 0 else 0.1
        
        return mm_per_px_x, mm_per_px_y
    
    def pixels_to_mm(self, dx_pixels: float, dy_pixels: float, 
                     z_pulses: int) -> Tuple[float, float]:
        """
        Converte deslocamento em pixels para deslocamento em mm.
        
        Args:
            dx_pixels: Deslocamento X em pixels
            dy_pixels: Deslocamento Y em pixels
            z_pulses: Posição Z atual em pulsos
            
        Returns:
            (dx_mm, dy_mm)
        """
        mm_per_px_x, mm_per_px_y = self.get_mm_per_pixel(z_pulses)
        
        dx_mm = dx_pixels * mm_per_px_x
        dy_mm = dy_pixels * mm_per_px_y
        
        return dx_mm, dy_mm
    
    def mm_to_pulses(self, dx_mm: float, dy_mm: float,
                     axis_x: str = "X", axis_y: str = "Y") -> Tuple[int, int]:
        """
        Converte deslocamento em mm para pulsos.
        
        Args:
            dx_mm: Deslocamento X em mm
            dy_mm: Deslocamento Y em mm
            axis_x: Nome do eixo X (para buscar calibração)
            axis_y: Nome do eixo Y (para buscar calibração)
            
        Returns:
            (dx_pulses, dy_pulses)
        """
        ppm_x = self._pulses_per_mm.get(axis_x, 100.0)
        ppm_y = self._pulses_per_mm.get(axis_y, 100.0)
        
        dx_pulses = int(round(dx_mm * ppm_x))
        dy_pulses = int(round(dy_mm * ppm_y))
        
        return dx_pulses, dy_pulses
    
    def pixels_to_pulses(self, dx_pixels: float, dy_pixels: float,
                         z_pulses: int,
                         axis_x: str = "X", axis_y: str = "Y") -> Tuple[int, int]:
        """
        Converte deslocamento em pixels diretamente para pulsos.
        
        Args:
            dx_pixels: Deslocamento X em pixels
            dy_pixels: Deslocamento Y em pixels
            z_pulses: Posição Z atual em pulsos
            axis_x: Nome do eixo X
            axis_y: Nome do eixo Y
            
        Returns:
            (dx_pulses, dy_pulses)
        """
        dx_mm, dy_mm = self.pixels_to_mm(dx_pixels, dy_pixels, z_pulses)
        return self.mm_to_pulses(dx_mm, dy_mm, axis_x, axis_y)
    
    def video_click_to_movement(self, 
                                 click_x: float, click_y: float,
                                 display_width: int, display_height: int,
                                 z_pulses: int,
                                 axis_x: str = "X", axis_y: str = "Y",
                                 invert_y: bool = False
                                 ) -> Tuple[int, int]:
        """
        Converte clique no preview de vídeo em movimento da head.
        
        Esta função considera:
        - Escala do display (QLabel pode ter tamanho diferente do frame)
        - Posição relativa ao centro (clique no centro = sem movimento)
        - Calibração de FOV para a altura Z atual
        
        Args:
            click_x, click_y: Coordenadas do clique no QLabel
            display_width, display_height: Tamanho do QLabel de vídeo
            z_pulses: Posição Z atual
            axis_x, axis_y: Nomes dos eixos
            invert_y: Se True, inverte direção Y (câmera espelhada)
            
        Returns:
            (dx_pulses, dy_pulses) - Movimento necessário para centralizar o ponto clicado
        """
        # Calcula escala aplicada pelo QPixmap.scaled(KeepAspectRatio)
        scale = min(
            display_width / self.frame_width,
            display_height / self.frame_height
        )
        
        # Tamanho efetivo da imagem no display
        pix_w = self.frame_width * scale
        pix_h = self.frame_height * scale
        
        # Offset (bordas pretas se aspect ratio diferente)
        offset_x = (display_width - pix_w) / 2
        offset_y = (display_height - pix_h) / 2
        
        # Verifica se clique está dentro da área da imagem
        if not (offset_x <= click_x <= offset_x + pix_w and
                offset_y <= click_y <= offset_y + pix_h):
            log.debug(f"Clique fora da área da imagem: ({click_x}, {click_y})")
            return 0, 0
        
        # Coordenada relativa ao centro da imagem, em pixels originais
        dx_pixels = (click_x - offset_x - pix_w / 2) / scale
        dy_pixels = (click_y - offset_y - pix_h / 2) / scale
        
        # Inversão de Y se necessário (câmera invertida)
        if invert_y:
            dy_pixels = -dy_pixels
        
        # Converte para pulsos
        dx_pulses, dy_pulses = self.pixels_to_pulses(
            dx_pixels, dy_pixels, z_pulses, axis_x, axis_y
        )
        
        log.debug(f"Clique: ({click_x:.0f}, {click_y:.0f}) → "
                 f"Δpix=({dx_pixels:.1f}, {dy_pixels:.1f}) → "
                 f"Δpulsos=({dx_pulses}, {dy_pulses})")
        
        return dx_pulses, dy_pulses


# ============================================================================
#  DIÁLOGO DE CALIBRAÇÃO - PyQt6
# ============================================================================

try:
    from PyQt6.QtWidgets import (
        QDialog, QGridLayout, QLabel, QSpinBox, QDoubleSpinBox,
        QPushButton, QHBoxLayout, QVBoxLayout, QGroupBox, QMessageBox
    )
    from PyQt6.QtCore import Qt
    
    _PYQT_AVAILABLE = True
except ImportError:
    _PYQT_AVAILABLE = False


if _PYQT_AVAILABLE:
    class FOVCalibrationDialog(QDialog):
        """
        Diálogo para calibração do campo de visão da câmera.
        
        O usuário define:
        - Dois pontos de Z (altura)
        - Largura e altura visível da câmera em cada ponto
        
        O sistema interpola linearmente para qualquer Z.
        """
        
        def __init__(self, config_manager=None, parent=None):
            super().__init__(parent)
            self.setWindowTitle("Calibração de Campo de Visão")
            self.setMinimumWidth(400)
            
            self._config_manager = config_manager
            self._load_current_values()
            self._build_ui()
        
        def _load_current_values(self):
            """Carrega valores atuais do config_manager ou usa defaults."""
            if self._config_manager:
                data = self._config_manager.get_config("camera_fov", {})
                self._fov = FOVCalibration.from_dict(data)
            else:
                self._fov = FOVCalibration()
        
        def _build_ui(self):
            layout = QVBoxLayout(self)
            
            # Instruções
            info = QLabel(
                "Configure o campo de visão da câmera em dois pontos de altura Z.\n"
                "Isso permite converter cliques no vídeo em movimentos precisos."
            )
            info.setWordWrap(True)
            info.setStyleSheet("color: #666; margin-bottom: 10px;")
            layout.addWidget(info)
            
            # Grupo de calibração
            group = QGroupBox("Pontos de Calibração")
            grid = QGridLayout(group)
            
            # Cabeçalhos
            grid.addWidget(QLabel("Parâmetro"), 0, 0)
            grid.addWidget(QLabel("Ponto 1 (Z alto)"), 0, 1)
            grid.addWidget(QLabel("Ponto 2 (Z baixo)"), 0, 2)
            
            # Linha 1: Z pulsos
            grid.addWidget(QLabel("Posição Z (pulsos):"), 1, 0)
            
            self.sp_z0 = QSpinBox()
            self.sp_z0.setRange(-999999, 999999)
            self.sp_z0.setValue(self._fov.z0_z_pulses)
            grid.addWidget(self.sp_z0, 1, 1)
            
            self.sp_z1 = QSpinBox()
            self.sp_z1.setRange(-999999, 999999)
            self.sp_z1.setValue(self._fov.z1_z_pulses)
            grid.addWidget(self.sp_z1, 1, 2)
            
            # Linha 2: Largura visível
            grid.addWidget(QLabel("Largura visível (mm):"), 2, 0)
            
            self.sp_w0 = QDoubleSpinBox()
            self.sp_w0.setRange(1, 1000)
            self.sp_w0.setDecimals(2)
            self.sp_w0.setValue(self._fov.z0_width_mm)
            grid.addWidget(self.sp_w0, 2, 1)
            
            self.sp_w1 = QDoubleSpinBox()
            self.sp_w1.setRange(1, 1000)
            self.sp_w1.setDecimals(2)
            self.sp_w1.setValue(self._fov.z1_width_mm)
            grid.addWidget(self.sp_w1, 2, 2)
            
            # Linha 3: Altura visível
            grid.addWidget(QLabel("Altura visível (mm):"), 3, 0)
            
            self.sp_h0 = QDoubleSpinBox()
            self.sp_h0.setRange(1, 1000)
            self.sp_h0.setDecimals(2)
            self.sp_h0.setValue(self._fov.z0_height_mm)
            grid.addWidget(self.sp_h0, 3, 1)
            
            self.sp_h1 = QDoubleSpinBox()
            self.sp_h1.setRange(1, 1000)
            self.sp_h1.setDecimals(2)
            self.sp_h1.setValue(self._fov.z1_height_mm)
            grid.addWidget(self.sp_h1, 3, 2)
            
            layout.addWidget(group)
            
            # Dica
            tip = QLabel(
                "💡 Dica: Para calibrar, posicione uma régua no plano focal, "
                "ajuste Z e meça a largura/altura visível no vídeo."
            )
            tip.setWordWrap(True)
            tip.setStyleSheet("color: #888; font-size: 11px; margin-top: 10px;")
            layout.addWidget(tip)
            
            # Botões
            btn_layout = QHBoxLayout()
            btn_layout.addStretch()
            
            btn_save = QPushButton("Salvar")
            btn_save.clicked.connect(self._save)
            btn_layout.addWidget(btn_save)
            
            btn_cancel = QPushButton("Cancelar")
            btn_cancel.clicked.connect(self.reject)
            btn_layout.addWidget(btn_cancel)
            
            layout.addLayout(btn_layout)
        
        def _save(self):
            """Salva calibração no config_manager."""
            fov = FOVCalibration(
                z0_z_pulses=self.sp_z0.value(),
                z0_width_mm=self.sp_w0.value(),
                z0_height_mm=self.sp_h0.value(),
                z1_z_pulses=self.sp_z1.value(),
                z1_width_mm=self.sp_w1.value(),
                z1_height_mm=self.sp_h1.value(),
            )
            
            if self._config_manager:
                self._config_manager.set_config("camera_fov", fov.to_dict())
                log.info("Calibração de FOV salva")
            
            self._fov = fov
            self.accept()
        
        def get_calibration(self) -> FOVCalibration:
            """Retorna calibração atual."""
            return self._fov


# ============================================================================
#  WIDGET CLICÁVEL PARA VÍDEO
# ============================================================================

if _PYQT_AVAILABLE:
    from PyQt6.QtWidgets import QLabel
    from PyQt6.QtCore import pyqtSignal
    from PyQt6.QtGui import QMouseEvent
    
    class ClickableVideoLabel(QLabel):
        """
        QLabel que emite sinal ao clicar.
        Usado para mover a head clicando no preview de vídeo.
        """
        
        # Sinal emitido com coordenadas do clique (x, y em pixels do QLabel)
        clicked = pyqtSignal(float, float)
        
        def mousePressEvent(self, event: QMouseEvent):
            if event.button() == Qt.MouseButton.LeftButton:
                pos = event.position()
                self.clicked.emit(pos.x(), pos.y())
            super().mousePressEvent(event)
