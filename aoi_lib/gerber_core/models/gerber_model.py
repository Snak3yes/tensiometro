"""
GerberModel - Model Layer para Gerber Viewer.

Este módulo implementa o Model do padrão MVC, responsável por:
- Armazenar dados do arquivo Gerber
- Validar objetos e índices
- Transformações geométricas (escala, translação)
- Gerenciar camadas (layers), apertures e macros

Seguindo princípios SOLID:
- SRP: Apenas responsabilidades de dados
- DIP: Independente de PyQt6 (testável)
- OCP: Fácil extensão com novos tipos de objetos
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


# ============================================================================
#  EXCEPTIONS
# ============================================================================

class ValidationError(Exception):
    """Exceção levantada quando validação de objeto falha."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message


# ============================================================================
#  DATA CLASSES
# ============================================================================

@dataclass
class GerberObject:
    """
    Representa um objeto Gerber (aperture flash).

    Attributes:
        obj_type: Tipo do objeto (flash_circle, flash_rect, flash_oval, region)
        x: Posição X em mm
        y: Posição Y em mm
        diameter: Diâmetro (para círculos)
        width: Largura (para retângulos e ovais)
        height: Altura (para retângulos e ovais)
    """
    obj_type: str
    x: float
    y: float
    diameter: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None


@dataclass
class GerberLayer:
    """
    Representa uma camada (layer) do arquivo Gerber.

    Attributes:
        layer_name: Nome da camada (ex: "top", "bottom")
        objects: Lista de objetos na camada
    """
    layer_name: str
    objects: List[GerberObject] = field(default_factory=list)

    def add_object(self, obj: GerberObject) -> None:
        """
        Adiciona um objeto à camada.

        Args:
            obj: Objeto Gerber a adicionar
        """
        self.objects.append(obj)

    def remove_object(self, index: int) -> None:
        """
        Remove um objeto da camada por índice.

        Args:
            index: Índice do objeto a remover

        Raises:
            ValidationError: Se o índice for inválido
        """
        if index < 0 or index >= len(self.objects):
            raise ValidationError(
                f"Índice {index} inválido. Camada possui {len(self.objects)} objetos."
            )
        self.objects.pop(index)


# ============================================================================
#  MODEL CLASS
# ============================================================================

class GerberModel:
    """
    Model principal para dados do arquivo Gerber.

    Responsabilidades:
    - Armazenar linhas do arquivo Gerber
    - Armazenar configuração (GerberConfig)
    - Gerenciar camadas, apertures e macros
    - Validar objetos
    - Transformar objetos (escala, translação)
    - Fornecer estatísticas

    NOTA: Esta classe NÃO depende de PyQt6, sendo totalmente testável.
    """

    def __init__(self):
        """Inicializa modelo vazio."""
        self.gerber_lines: Optional[List[str]] = None
        self.gerber_cfg: Optional[Any] = None
        self.layers: List[GerberLayer] = []
        self.macros: Dict[str, Any] = {}
        self.apertures: Dict[int, Any] = {}

    # ========================================================================
    #  LOAD DATA
    # ========================================================================

    def load_gerber(
        self,
        lines: List[str],
        cfg: Any
    ) -> None:
        """
        Carrega dados do arquivo Gerber no modelo.

        Args:
            lines: Linhas do arquivo Gerber
            cfg: Configuração gerada pelo parser
        """
        self.gerber_lines = lines
        self.gerber_cfg = cfg

    # ========================================================================
    #  LAYERS
    # ========================================================================

    def add_layer(self, layer: GerberLayer) -> None:
        """Adiciona uma camada ao modelo."""
        self.layers.append(layer)

    # ========================================================================
    #  APERTURES
    # ========================================================================

    def add_aperture(self, dcode: int, aperture: Any) -> None:
        """Adiciona uma abertura (aperture) ao modelo."""
        self.apertures[dcode] = aperture

    # ========================================================================
    #  MACROS
    # ========================================================================

    def add_macro(self, name: str, macro: Any) -> None:
        """Adiciona uma macro ao modelo."""
        self.macros[name] = macro

    # ========================================================================
    #  QUERIES
    # ========================================================================

    def get_object_count(self) -> int:
        """Retorna o total de objetos em todas as camadas."""
        return sum(len(layer.objects) for layer in self.layers)

    def get_statistics(self) -> Dict[str, int]:
        """
        Retorna estatísticas do modelo.

        Returns:
            Dicionário com contagem de objetos, camadas, apertures e macros
        """
        return {
            "total_objects": self.get_object_count(),
            "total_layers": len(self.layers),
            "total_apertures": len(self.apertures),
            "total_macros": len(self.macros),
        }

    # ========================================================================
    #  VALIDATION
    # ========================================================================

    def validate_object(self, obj: GerberObject) -> None:
        """
        Valida um objeto Gerber.

        Args:
            obj: Objeto a validar

        Raises:
            ValidationError: Se o objeto for inválido
        """
        # Validar tipo
        valid_types = {
            "flash_circle",
            "flash_rect",
            "flash_oval",
            "region",
        }
        if obj.obj_type not in valid_types:
            raise ValidationError(
                f"Tipo de objeto inválido: {obj.obj_type}. "
                f"Tipos válidos: {valid_types}"
            )

        # Validar dimensões negativas
        if obj.diameter is not None and obj.diameter < 0:
            raise ValidationError(f"Diâmetro negativo: {obj.diameter}")
        if obj.width is not None and obj.width < 0:
            raise ValidationError(f"Largura negativa: {obj.width}")
        if obj.height is not None and obj.height < 0:
            raise ValidationError(f"Altura negativa: {obj.height}")

    # ========================================================================
    #  TRANSFORMATIONS
    # ========================================================================

    def transform_object(
        self,
        obj: GerberObject,
        scale_factor: float = 1.0,
        dx: float = 0.0,
        dy: float = 0.0
    ) -> GerberObject:
        """
        Aplica transformações geométricas em um objeto.

        Args:
            obj: Objeto a transformar
            scale_factor: Fator de escala (1.0 = sem escala)
            dx: Translação em X (mm)
            dy: Translação em Y (mm)

        Returns:
            Novo objeto transformado (não modifica o original)
        """
        # Copiar objeto
        import copy
        transformed = copy.copy(obj)

        # Aplicar escala
        if transformed.diameter is not None:
            transformed.diameter *= scale_factor
        if transformed.width is not None:
            transformed.width *= scale_factor
        if transformed.height is not None:
            transformed.height *= scale_factor

        # Aplicar translação
        transformed.x += dx
        transformed.y += dy

        return transformed
