"""
Fiducial Models - Data Structures for Fiducial Alignment

Este módulo contém estruturas de dados (dataclasses) para representar:
- Pontos fiduciais (FiducialPoint)
- Transformação de alinhamento (AlignmentTransform)
- Estado de alinhamento (AlignmentState)
- Configuração de fiduciais (FiducialConfig)

Author: Claude Code (Sonnet 4.5)
Created: 2026-01-15
Phase: SOLID Refactoring Phase 5B
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any
from enum import Enum
import numpy as np
import cv2


class FiducialType(Enum):
    """Tipo de fiducial"""
    GERBER = "gerber"      # Fiducial do arquivo Gerber
    TEMPLATE = "template"  # Fiducial capturado da câmera


class MatchingMethod(Enum):
    """Método de matching para template matching"""
    SQDIFF = cv2.TM_SQDIFF        # Quadrado da diferença
    SQDIFF_NORMED = cv2.TM_SQDIFF_NORMED
    CCORR = cv2.TM_CCORR          # Correlação cruzada
    CCORR_NORMED = cv2.TM_CCORR_NORMED
    CCOEFF = cv2.TM_CCOEFF        # Coeficiente de correlação
    CCOEFF_NORMED = cv2.TM_CCOEFF_NORMED


@dataclass
class FiducialPoint:
    """
    Representa um ponto fiducial.

    Attributes:
        gerber_x: Coordenada X no arquivo Gerber (mm)
        gerber_y: Coordenada Y no arquivo Gerber (mm)
        fiducial_type: Tipo de fiducial (GERBER ou TEMPLATE)
        template: Imagem do template capturado (numpy array)
        template_x: Coordenada X do template na imagem (pixels)
        template_y: Coordenada Y do template na imagem (pixels)
        window_size: Tamanho da janela de captura (pixels)
        matched_x: Coordenada X onde foi encontrado (pixels)
        matched_y: Coordenada Y onde foi encontrado (pixels)
        correlation: Correlação do matching (0-1)
        is_matched: Se o fiducial foi encontrado com sucesso
        search_radius: Raio de busca em pixels
    """

    # Coordenadas no Gerber
    gerber_x: float
    gerber_y: float

    # Tipo e configuração
    fiducial_type: FiducialType = FiducialType.GERBER
    window_size: int = 50

    # Template capturado
    template: Optional[np.ndarray] = None
    template_x: Optional[float] = None
    template_y: Optional[float] = None

    # Resultado do matching
    matched_x: Optional[float] = None
    matched_y: Optional[float] = None
    correlation: Optional[float] = None
    is_matched: bool = False

    # Configuração de busca
    search_radius: int = 100

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário (para serialização)"""
        return {
            'gerber_x': self.gerber_x,
            'gerber_y': self.gerber_y,
            'fiducial_type': self.fiducial_type.value,
            'window_size': self.window_size,
            'template_x': self.template_x,
            'template_y': self.template_y,
            'matched_x': self.matched_x,
            'matched_y': self.matched_y,
            'correlation': self.correlation,
            'is_matched': self.is_matched,
            'search_radius': self.search_radius
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FiducialPoint':
        """Cria a partir de dicionário (para desserialização)"""
        return cls(
            gerber_x=data['gerber_x'],
            gerber_y=data['gerber_y'],
            fiducial_type=FiducialType(data.get('fiducial_type', 'gerber')),
            window_size=data.get('window_size', 50),
            template_x=data.get('template_x'),
            template_y=data.get('template_y'),
            matched_x=data.get('matched_x'),
            matched_y=data.get('matched_y'),
            correlation=data.get('correlation'),
            is_matched=data.get('is_matched', False),
            search_radius=data.get('search_radius', 100)
        )

    def has_template(self) -> bool:
        """Verifica se possui template capturado"""
        return self.template is not None and self.template_x is not None

    def has_match(self) -> bool:
        """Verifica se possui matching realizado"""
        return self.is_matched and self.matched_x is not None


@dataclass
class AlignmentTransform:
    """
    Representa uma transformação de alinhamento 2D.

    A transformação é composta de:
    - Translação (tx, ty): Deslocamento em pixels
    - Rotação (angle): Rotação em graus
    - Escala (scale_x, scale_y): Fator de escala

    Attributes:
        tx: Translação em X (pixels)
        ty: Translação em Y (pixels)
        angle: Ângulo de rotação (graus, anti-horário)
        scale_x: Fator de escala em X
        scale_y: Fator de escala em Y (default: igual a scale_x)
    """

    tx: float
    ty: float
    angle: float
    scale_x: float
    scale_y: Optional[float] = None

    def __post_init__(self):
        """Inicializa scale_y como igual a scale_x se não fornecido"""
        if self.scale_y is None:
            self.scale_y = self.scale_x

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário (para serialização)"""
        return {
            'tx': self.tx,
            'ty': self.ty,
            'angle': self.angle,
            'scale_x': self.scale_x,
            'scale_y': self.scale_y
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AlignmentTransform':
        """Cria a partir de dicionário (para desserialização)"""
        return cls(
            tx=data['tx'],
            ty=data['ty'],
            angle=data['angle'],
            scale_x=data['scale_x'],
            scale_y=data.get('scale_y', data['scale_x'])
        )

    def __str__(self) -> str:
        """Representação string legível"""
        return (
            f"AlignmentTransform("
            f"tx={self.tx:.1f}, ty={self.ty:.1f}, "
            f"angle={self.angle:.2f}°, "
            f"scale={self.scale_x:.4f})"
        )


@dataclass
class FiducialConfig:
    """
    Configuração para alinhamento de fiduciais.

    Attributes:
        matching_method: Método de template matching (default: CCORR_NORMED)
        matching_threshold: Limiar de correlação (0-1)
        search_radius: Raio de busca em pixels
        window_size: Tamanho da janela de captura
        min_fiducials: Número mínimo de fiduciais para calcular transformação
        max_correlation_variance: Variância máxima permitida entre correlações
    """

    matching_method: MatchingMethod = MatchingMethod.CCOEFF_NORMED
    matching_threshold: float = 0.7
    search_radius: int = 100
    window_size: int = 50
    min_fiducials: int = 2
    max_correlation_variance: float = 0.2

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário (para serialização)"""
        return {
            'matching_method': self.matching_method.value,
            'matching_threshold': self.matching_threshold,
            'search_radius': self.search_radius,
            'window_size': self.window_size,
            'min_fiducials': self.min_fiducials,
            'max_correlation_variance': self.max_correlation_variance
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FiducialConfig':
        """Cria a partir de dicionário (para desserialização)"""
        return cls(
            matching_method=MatchingMethod(data.get('matching_method', cv2.TM_CCOEFF_NORMED)),
            matching_threshold=data.get('matching_threshold', 0.7),
            search_radius=data.get('search_radius', 100),
            window_size=data.get('window_size', 50),
            min_fiducials=data.get('min_fiducials', 2),
            max_correlation_variance=data.get('max_correlation_variance', 0.2)
        )

    def validate(self) -> Tuple[bool, Optional[str]]:
        """
        Valida a configuração.

        Returns:
            (is_valid, error_message): Tupla com validação e mensagem de erro
        """
        if not 0 <= self.matching_threshold <= 1:
            return False, f"matching_threshold deve estar entre 0 e 1, got {self.matching_threshold}"

        if self.search_radius < 10:
            return False, f"search_radius deve ser >= 10, got {self.search_radius}"

        if self.window_size < 10:
            return False, f"window_size deve ser >= 10, got {self.window_size}"

        if self.min_fiducials < 2:
            return False, f"min_fiducials deve ser >= 2, got {self.min_fiducials}"

        if not 0 <= self.max_correlation_variance <= 1:
            return False, f"max_correlation_variance deve estar entre 0 e 1, got {self.max_correlation_variance}"

        return True, None


@dataclass
class AlignmentState:
    """
    Estado completo do alinhamento de fiduciais.

    Attributes:
        fiducials: Lista de pontos fiduciais
        transform: Transformação calculada (opcional)
        config: Configuração usada
        is_valid: Se o estado é válido (transformação calculada com sucesso)
        validation_message: Mensagem de validação
        timestamp: Timestamp da criação do estado
    """

    fiducials: List[FiducialPoint] = field(default_factory=list)
    transform: Optional[AlignmentTransform] = None
    config: FiducialConfig = field(default_factory=FiducialConfig)
    is_valid: bool = False
    validation_message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário (para serialização)"""
        return {
            'fiducials': [f.to_dict() for f in self.fiducials],
            'transform': self.transform.to_dict() if self.transform else None,
            'config': self.config.to_dict(),
            'is_valid': self.is_valid,
            'validation_message': self.validation_message
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AlignmentState':
        """Cria a partir de dicionário (para desserialização)"""
        fiducials = [FiducialPoint.from_dict(f) for f in data.get('fiducials', [])]
        transform_data = data.get('transform')
        transform = AlignmentTransform.from_dict(transform_data) if transform_data else None
        config = FiducialConfig.from_dict(data.get('config', {}))

        return cls(
            fiducials=fiducials,
            transform=transform,
            config=config,
            is_valid=data.get('is_valid', False),
            validation_message=data.get('validation_message', '')
        )

    def add_fiducial(self, fiducial: FiducialPoint) -> None:
        """Adiciona um fiducial à lista"""
        self.fiducials.append(fiducial)
        self._invalidate()

    def remove_fiducial(self, index: int) -> None:
        """Remove um fiducial da lista"""
        if 0 <= index < len(self.fiducials):
            self.fiducials.pop(index)
            self._invalidate()

    def update_fiducial(self, index: int, fiducial: FiducialPoint) -> None:
        """Atualiza um fiducial na lista"""
        if 0 <= index < len(self.fiducials):
            self.fiducials[index] = fiducial
            self._invalidate()

    def get_matched_fiducials(self) -> List[FiducialPoint]:
        """Retorna lista de fiduciais com match"""
        return [f for f in self.fiducials if f.has_match()]

    def get_fiducial_count(self) -> int:
        """Retorna número total de fiduciais"""
        return len(self.fiducials)

    def get_matched_count(self) -> int:
        """Retorna número de fiduciais com match"""
        return len(self.get_matched_fiducials())

    def _invalidate(self) -> None:
        """Invalida o estado (transformação precisa ser recalculada)"""
        self.is_valid = False
        self.validation_message = "Transformação precisa ser recalculada"


# Aliances para compatibilidade
FiducialData = FiducialPoint
AlignmentData = AlignmentTransform
