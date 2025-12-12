"""
gerber_renderer.py
-------------------
Renderizador de objetos Gerber para imagens OpenCV/numpy.

Converte objetos GerberObject em:
- Máscaras binárias (para comparação com imagem real)
- Overlays coloridos (para visualização)

Usa a transformação de alinhamento (da Fase 6) para posicionar
corretamente os objetos Gerber sobre a imagem do mosaico.
"""

from __future__ import annotations

import logging
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass

import numpy as np
import cv2

# Importa do gerber_core local (cópia do gerber_viewer)
try:
    from .gerber_core.parser import GerberObject
    from .gerber_core.config import GerberConfig, parse_gerber_config
    from .gerber_core.apertures import parse_all_macros, parse_add
    from .gerber_core.parser import build_layer_objects_mm
except ImportError:
    # Fallback para importação direta do testes_gerber
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / "testes_gerber"))
    from gerber_viewer.parser import GerberObject, build_layer_objects_mm
    from gerber_viewer.config import GerberConfig, parse_gerber_config
    from gerber_viewer.apertures import parse_all_macros, parse_add

log = logging.getLogger(__name__)


@dataclass
class RenderBounds:
    """Limites do Gerber em mm."""
    min_x: float
    max_x: float
    min_y: float
    max_y: float
    
    @property
    def width(self) -> float:
        return self.max_x - self.min_x
    
    @property
    def height(self) -> float:
        return self.max_y - self.min_y
    
    @property
    def center(self) -> Tuple[float, float]:
        return (self.min_x + self.width/2, self.min_y + self.height/2)


@dataclass 
class AlignmentTransform:
    """Transformação de alinhamento Gerber → Imagem."""
    tx: float = 0.0       # Translação X (pixels)
    ty: float = 0.0       # Translação Y (pixels)
    angle: float = 0.0    # Rotação (graus)
    scale_x: float = 1.0  # Escala X (px/mm)
    scale_y: float = 1.0  # Escala Y (px/mm)
    
    def transform_point(self, x_mm: float, y_mm: float) -> Tuple[float, float]:
        """Transforma ponto de mm para pixels."""
        import math
        # Escala
        x_px = x_mm * self.scale_x
        y_px = y_mm * self.scale_y
        
        # Rotação
        if self.angle != 0:
            rad = math.radians(self.angle)
            cos_a = math.cos(rad)
            sin_a = math.sin(rad)
            x_rot = x_px * cos_a - y_px * sin_a
            y_rot = x_px * sin_a + y_px * cos_a
            x_px, y_px = x_rot, y_rot
        
        # Translação
        x_px += self.tx
        y_px += self.ty
        
        return (x_px, y_px)
    
    def to_cv2_matrix(self) -> np.ndarray:
        """Retorna matriz de transformação 2x3 para cv2.warpAffine."""
        import math
        rad = math.radians(self.angle)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)
        
        # Matriz: [escala*rotação | translação]
        M = np.array([
            [self.scale_x * cos_a, -self.scale_y * sin_a, self.tx],
            [self.scale_x * sin_a,  self.scale_y * cos_a, self.ty]
        ], dtype=np.float64)
        
        return M


class GerberRenderer:
    """
    Renderiza objetos Gerber para imagens OpenCV/numpy.
    
    Uso:
        renderer = GerberRenderer()
        objects = renderer.load_gerber("stencil.gbr")
        
        # Máscara binária
        mask = renderer.render_mask(objects, image_size, transform)
        
        # Overlay colorido
        overlay = renderer.render_overlay(objects, background_image, transform)
    """
    
    def __init__(self):
        self.objects: List[GerberObject] = []
        self.bounds: Optional[RenderBounds] = None
        self._gerber_lines: Optional[List[str]] = None
        self._gerber_config: Optional[GerberConfig] = None
    
    def load_gerber(self, filepath: str) -> List[GerberObject]:
        """
        Carrega arquivo Gerber e retorna lista de objetos.
        
        Args:
            filepath: Caminho para o arquivo .gbr
            
        Returns:
            Lista de GerberObject parseados
        """
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        self._gerber_lines = lines
        self._gerber_config = parse_gerber_config(lines)
        
        macros = parse_all_macros(lines)
        apertures = parse_add(lines, self._gerber_config)
        
        self.objects = build_layer_objects_mm(
            lines, macros, apertures, self._gerber_config
        )
        
        # Calcular bounds
        self.bounds = self._calculate_bounds(self.objects)
        
        log.info(f"Gerber carregado: {len(self.objects)} objetos, "
                f"bounds: {self.bounds.width:.1f}x{self.bounds.height:.1f} mm")
        
        return self.objects
    
    def _calculate_bounds(self, objects: List[GerberObject]) -> RenderBounds:
        """Calcula bounding box dos objetos."""
        if not objects:
            return RenderBounds(0, 0, 0, 0)
        
        all_x = []
        all_y = []
        
        for obj in objects:
            if obj.polygon_mm:
                for x, y in obj.polygon_mm:
                    all_x.append(x)
                    all_y.append(y)
            elif obj.x_mm is not None and obj.y_mm is not None:
                all_x.append(obj.x_mm)
                all_y.append(obj.y_mm)
        
        if not all_x:
            return RenderBounds(0, 0, 0, 0)
        
        return RenderBounds(
            min_x=min(all_x),
            max_x=max(all_x),
            min_y=min(all_y),
            max_y=max(all_y)
        )
    
    def render_mask(
        self,
        objects: Optional[List[GerberObject]] = None,
        image_size: Tuple[int, int] = (1000, 1000),
        transform: Optional[AlignmentTransform] = None,
        invert: bool = False
    ) -> np.ndarray:
        """
        Renderiza objetos Gerber como máscara binária.
        
        Para inspeção com backlight:
        - Branco (255) = aberturas (luz passa)
        - Preto (0) = stencil (luz bloqueada)
        
        Args:
            objects: Lista de objetos (usa self.objects se None)
            image_size: (largura, altura) em pixels
            transform: Transformação de alinhamento
            invert: Se True, inverte a máscara
            
        Returns:
            Máscara binária (numpy array uint8)
        """
        objects = objects or self.objects
        if not objects:
            log.warning("Nenhum objeto para renderizar")
            return np.zeros(image_size[::-1], dtype=np.uint8)
        
        transform = transform or self._default_transform(objects, image_size)
        
        # Criar máscara preta
        mask = np.zeros((image_size[1], image_size[0]), dtype=np.uint8)
        
        for obj in objects:
            if not obj.polygon_mm or len(obj.polygon_mm) < 3:
                continue
            
            # Transformar polígono para pixels
            pts_px = []
            for x_mm, y_mm in obj.polygon_mm:
                x_px, y_px = transform.transform_point(x_mm, y_mm)
                pts_px.append([int(x_px), int(y_px)])
            
            pts = np.array(pts_px, dtype=np.int32)
            
            # Desenhar polígono preenchido
            cv2.fillPoly(mask, [pts], 255)
        
        if invert:
            mask = cv2.bitwise_not(mask)
        
        return mask
    
    def render_overlay(
        self,
        background: np.ndarray,
        objects: Optional[List[GerberObject]] = None,
        transform: Optional[AlignmentTransform] = None,
        color: Tuple[int, int, int] = (0, 255, 0),  # Verde
        alpha: float = 0.4,
        outline_only: bool = False,
        outline_thickness: int = 2
    ) -> np.ndarray:
        """
        Renderiza overlay colorido dos objetos Gerber sobre imagem de fundo.
        
        Args:
            background: Imagem de fundo (BGR)
            objects: Lista de objetos (usa self.objects se None)
            transform: Transformação de alinhamento
            color: Cor do overlay (B, G, R)
            alpha: Transparência (0.0 = invisível, 1.0 = opaco)
            outline_only: Se True, desenha apenas contorno
            outline_thickness: Espessura do contorno
            
        Returns:
            Imagem com overlay (BGR)
        """
        objects = objects or self.objects
        if not objects:
            return background.copy()
        
        h, w = background.shape[:2]
        transform = transform or self._default_transform(objects, (w, h))
        
        # Criar camada de overlay
        overlay = background.copy()
        
        for obj in objects:
            if not obj.polygon_mm or len(obj.polygon_mm) < 3:
                continue
            
            # Transformar polígono
            pts_px = []
            for x_mm, y_mm in obj.polygon_mm:
                x_px, y_px = transform.transform_point(x_mm, y_mm)
                pts_px.append([int(x_px), int(y_px)])
            
            pts = np.array(pts_px, dtype=np.int32)
            
            if outline_only:
                cv2.polylines(overlay, [pts], True, color, outline_thickness)
            else:
                cv2.fillPoly(overlay, [pts], color)
        
        # Blend com alpha
        result = cv2.addWeighted(background, 1 - alpha, overlay, alpha, 0)
        
        return result
    
    def render_individual_masks(
        self,
        objects: Optional[List[GerberObject]] = None,
        image_size: Tuple[int, int] = (1000, 1000),
        transform: Optional[AlignmentTransform] = None
    ) -> List[Tuple[int, np.ndarray, Tuple[int, int, int, int]]]:
        """
        Renderiza máscara individual para cada abertura.
        
        Útil para análise individual de cada abertura.
        
        Returns:
            Lista de (object_id, máscara, bounding_box)
            onde bounding_box = (x, y, w, h) da região
        """
        objects = objects or self.objects
        if not objects:
            return []
        
        transform = transform or self._default_transform(objects, image_size)
        
        results = []
        
        for i, obj in enumerate(objects):
            if not obj.polygon_mm or len(obj.polygon_mm) < 3:
                continue
            
            # Transformar polígono
            pts_px = []
            for x_mm, y_mm in obj.polygon_mm:
                x_px, y_px = transform.transform_point(x_mm, y_mm)
                pts_px.append([int(x_px), int(y_px)])
            
            pts = np.array(pts_px, dtype=np.int32)
            
            # Calcular bounding box
            x, y, w, h = cv2.boundingRect(pts)
            
            # Criar máscara para este objeto apenas
            obj_mask = np.zeros((image_size[1], image_size[0]), dtype=np.uint8)
            cv2.fillPoly(obj_mask, [pts], 255)
            
            results.append((obj.id, obj_mask, (x, y, w, h)))
        
        return results
    
    def _default_transform(
        self, 
        objects: List[GerberObject], 
        image_size: Tuple[int, int]
    ) -> AlignmentTransform:
        """
        Cria transformação padrão que centraliza e escala o Gerber na imagem.
        """
        bounds = self._calculate_bounds(objects)
        
        if bounds.width == 0 or bounds.height == 0:
            return AlignmentTransform()
        
        w, h = image_size
        margin = 20  # pixels
        
        # Escala para caber na imagem
        scale_x = (w - 2 * margin) / bounds.width
        scale_y = (h - 2 * margin) / bounds.height
        scale = min(scale_x, scale_y)
        
        # Translação para centralizar
        center_x_mm, center_y_mm = bounds.center
        tx = w / 2 - center_x_mm * scale
        ty = h / 2 + center_y_mm * scale  # Inverte Y para sistema de imagem
        
        return AlignmentTransform(
            tx=tx,
            ty=ty,
            scale_x=scale,
            scale_y=-scale  # Inverte Y
        )


# ============================================================================
#  FUNÇÕES DE CONVENIÊNCIA
# ============================================================================

def load_and_render_gerber(
    filepath: str,
    image_size: Tuple[int, int] = (2000, 2000)
) -> Tuple[List[GerberObject], np.ndarray]:
    """
    Carrega Gerber e renderiza como máscara.
    
    Returns:
        (objetos, máscara)
    """
    renderer = GerberRenderer()
    objects = renderer.load_gerber(filepath)
    mask = renderer.render_mask(objects, image_size)
    return objects, mask


# ============================================================================
#  EXEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) < 2:
        print("Uso: python gerber_renderer.py <arquivo.gbr>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    renderer = GerberRenderer()
    objects = renderer.load_gerber(filepath)
    
    print(f"\n📁 Arquivo: {filepath}")
    print(f"📊 Objetos: {len(objects)}")
    print(f"📐 Bounds: {renderer.bounds}")
    
    # Renderizar máscara
    mask = renderer.render_mask(image_size=(2000, 2000))
    
    # Salvar
    output = "gerber_mask.png"
    cv2.imwrite(output, mask)
    print(f"\n✅ Máscara salva: {output}")
    
    # Mostrar estatísticas
    white_pixels = np.count_nonzero(mask)
    total_pixels = mask.size
    fill_ratio = white_pixels / total_pixels * 100
    print(f"📊 Área de aberturas: {fill_ratio:.1f}%")
