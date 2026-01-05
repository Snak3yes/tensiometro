"""
stencil_inspector.py
--------------------
Motor de inspeção visual de stencils.

Compara a imagem real capturada (mosaico) com a máscara gerada
a partir do arquivo Gerber para detectar defeitos nas aberturas.

Tipos de defeitos detectados:
- BLOCKED: Abertura totalmente obstruída
- PARTIAL: Abertura parcialmente obstruída
- OK: Abertura livre

Com backlight (luz por trás do stencil):
- Áreas claras = luz passando = abertura livre
- Áreas escuras = luz bloqueada = stencil ou obstrução
"""

from __future__ import annotations

import logging
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from enum import Enum

import numpy as np
import cv2

from .gerber_renderer import GerberRenderer, AlignmentTransform, RenderBounds

# Tenta importar GerberObject do módulo local
try:
    from .gerber_core.parser import GerberObject
except ImportError:
    from .gerber_renderer import GerberObject

log = logging.getLogger(__name__)


class DefectType(Enum):
    """Tipos de defeitos detectáveis."""
    OK = "OK"
    PARTIAL = "PARTIAL"         # Parcialmente obstruída
    BLOCKED = "BLOCKED"         # Totalmente obstruída
    DEFORMED = "DEFORMED"       # Formato alterado (futuro)


@dataclass
class InspectionThresholds:
    """
    Limiares configuráveis para inspeção.
    
    Estes valores podem ser ajustados pela engenharia.
    """
    # Thresholds de classificação (% de área livre)
    ok_threshold: float = 90.0        # >= 90% = OK
    partial_threshold: float = 70.0   # >= 70% e < 90% = PARTIAL
    # < 70% = BLOCKED
    
    # Binarização da imagem
    bin_method: str = "otsu"          # "otsu", "adaptive", "fixed"
    bin_fixed_threshold: int = 127    # Usado se bin_method == "fixed"
    bin_adaptive_block: int = 11      # Tamanho do bloco para adaptive
    bin_adaptive_c: int = 2           # Constante subtraída
    
    # Filtros
    min_aperture_area_px: int = 50    # Área mínima para considerar abertura
    blur_kernel_size: int = 3         # Tamanho do blur pré-processamento
    
    # Morphology para limpeza
    morphology_kernel_size: int = 3
    apply_morphology: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InspectionThresholds':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ApertureInspection:
    """Resultado de inspeção de uma abertura individual."""
    object_id: int
    x_mm: float
    y_mm: float
    kind: str                         # Tipo de abertura (circle, rect, etc)
    expected_area_px: int             # Área esperada (máscara Gerber)
    observed_area_px: int             # Área observada (imagem real)
    fill_ratio: float                 # 0.0 = totalmente obstruída, 1.0 = livre
    status: DefectType                # OK, PARTIAL, BLOCKED
    bbox: Tuple[int, int, int, int]   # (x, y, w, h) bounding box em pixels
    
    @property
    def fill_percentage(self) -> float:
        return self.fill_ratio * 100
    
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['status'] = self.status.value
        return d


@dataclass
class InspectionResult:
    """Resultado completo da inspeção de um stencil."""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Contadores
    total_apertures: int = 0
    ok_count: int = 0
    partial_count: int = 0
    blocked_count: int = 0
    
    # Status geral
    overall_status: str = "OK"        # OK, WARNING, NOK
    approval_rate: float = 100.0      # % de aberturas OK
    
    # Detalhes
    apertures: List[ApertureInspection] = field(default_factory=list)
    defects: List[ApertureInspection] = field(default_factory=list)  # Apenas defeitos
    
    # Configuração usada
    thresholds_used: Optional[InspectionThresholds] = None
    
    # Metadados
    gerber_file: Optional[str] = None
    mosaic_file: Optional[str] = None
    stencil_code: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp,
            'total_apertures': self.total_apertures,
            'ok_count': self.ok_count,
            'partial_count': self.partial_count,
            'blocked_count': self.blocked_count,
            'overall_status': self.overall_status,
            'approval_rate': self.approval_rate,
            'defects_count': len(self.defects),
            'gerber_file': self.gerber_file,
            'mosaic_file': self.mosaic_file,
            'stencil_code': self.stencil_code,
        }


class StencilInspector:
    """
    Motor de inspeção visual de stencils.
    
    Uso:
        inspector = StencilInspector()
        
        # Carregar dados
        inspector.load_gerber("stencil.gbr")
        inspector.set_mosaic(mosaic_image)
        inspector.set_alignment(transform)
        
        # Executar inspeção
        result = inspector.inspect()
        
        # Visualizar
        overlay = inspector.get_result_overlay()
    """
    
    def __init__(self, thresholds: Optional[InspectionThresholds] = None):
        self.thresholds = thresholds or InspectionThresholds()
        self.renderer = GerberRenderer()
        
        self._mosaic: Optional[np.ndarray] = None
        self._transform: Optional[AlignmentTransform] = None
        self._last_result: Optional[InspectionResult] = None
        
        # Imagens intermediárias (para debug/visualização)
        self._gerber_mask: Optional[np.ndarray] = None
        self._binary_mosaic: Optional[np.ndarray] = None
    
    def load_gerber(self, filepath: str) -> int:
        """
        Carrega arquivo Gerber.
        
        Returns:
            Número de objetos/aberturas carregados
        """
        objects = self.renderer.load_gerber(filepath)
        log.info(f"Gerber carregado: {len(objects)} aberturas")
        return len(objects)
    
    def set_mosaic(self, image: np.ndarray):
        """Define a imagem do mosaico (BGR)."""
        self._mosaic = image
        log.info(f"Mosaico definido: {image.shape[1]}x{image.shape[0]} pixels")
    
    def set_alignment(self, transform: AlignmentTransform):
        """Define a transformação de alinhamento."""
        self._transform = transform
        log.info(f"Alinhamento definido: tx={transform.tx:.1f}, ty={transform.ty:.1f}, "
                f"angle={transform.angle:.2f}°")
    
    def inspect(
        self,
        mosaic: Optional[np.ndarray] = None,
        transform: Optional[AlignmentTransform] = None
    ) -> InspectionResult:
        """
        Executa inspeção completa do stencil.
        
        Args:
            mosaic: Imagem do mosaico (usa self._mosaic se None)
            transform: Transformação de alinhamento (usa self._transform se None)
            
        Returns:
            InspectionResult com todos os detalhes
        """
        mosaic = mosaic if mosaic is not None else self._mosaic
        transform = transform or self._transform
        
        if mosaic is None:
            raise ValueError("Mosaico não definido. Use set_mosaic() primeiro.")
        
        if not self.renderer.objects:
            raise ValueError("Gerber não carregado. Use load_gerber() primeiro.")
        
        h, w = mosaic.shape[:2]
        
        # 1. Renderizar máscara Gerber
        log.info("Renderizando máscara Gerber...")
        self._gerber_mask = self.renderer.render_mask(
            image_size=(w, h),
            transform=transform
        )
        
        # 2. Binarizar imagem real
        log.info("Binarizando mosaico...")
        self._binary_mosaic = self._binarize_mosaic(mosaic)
        
        # 3. Analisar cada abertura
        log.info("Analisando aberturas...")
        result = self._analyze_apertures(transform)
        
        # 4. Calcular estatísticas gerais
        result.total_apertures = len(result.apertures)
        result.ok_count = sum(1 for a in result.apertures if a.status == DefectType.OK)
        result.partial_count = sum(1 for a in result.apertures if a.status == DefectType.PARTIAL)
        result.blocked_count = sum(1 for a in result.apertures if a.status == DefectType.BLOCKED)
        
        result.defects = [a for a in result.apertures if a.status != DefectType.OK]
        
        if result.total_apertures > 0:
            result.approval_rate = (result.ok_count / result.total_apertures) * 100
        
        # 5. Determinar status geral
        if result.blocked_count > 0:
            result.overall_status = "NOK"
        elif result.partial_count > 0:
            result.overall_status = "WARNING"
        else:
            result.overall_status = "OK"
        
        result.thresholds_used = self.thresholds
        
        self._last_result = result
        
        log.info(f"Inspeção concluída: {result.total_apertures} aberturas, "
                f"{result.ok_count} OK, {result.partial_count} PARTIAL, "
                f"{result.blocked_count} BLOCKED → {result.overall_status}")
        
        return result
    
    def _binarize_mosaic(self, mosaic: np.ndarray) -> np.ndarray:
        """
        Binariza imagem do mosaico.
        
        Com backlight:
        - Pixels claros = luz passando = abertura livre
        - Pixels escuros = luz bloqueada
        """
        # Converter para escala de cinza
        if len(mosaic.shape) == 3:
            gray = cv2.cvtColor(mosaic, cv2.COLOR_BGR2GRAY)
        else:
            gray = mosaic.copy()
        
        # Aplicar blur para reduzir ruído
        if self.thresholds.blur_kernel_size > 1:
            gray = cv2.GaussianBlur(
                gray, 
                (self.thresholds.blur_kernel_size, self.thresholds.blur_kernel_size), 
                0
            )
        
        # Binarização
        if self.thresholds.bin_method == "otsu":
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        elif self.thresholds.bin_method == "adaptive":
            binary = cv2.adaptiveThreshold(
                gray, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                self.thresholds.bin_adaptive_block,
                self.thresholds.bin_adaptive_c
            )
        else:  # fixed
            _, binary = cv2.threshold(gray, self.thresholds.bin_fixed_threshold, 255, cv2.THRESH_BINARY)
        
        # Morphology para limpeza
        if self.thresholds.apply_morphology:
            kernel = cv2.getStructuringElement(
                cv2.MORPH_ELLIPSE,
                (self.thresholds.morphology_kernel_size, self.thresholds.morphology_kernel_size)
            )
            binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        return binary
    
    def _analyze_apertures(self, transform: Optional[AlignmentTransform]) -> InspectionResult:
        """Analisa cada abertura individualmente."""
        result = InspectionResult()
        
        h, w = self._gerber_mask.shape[:2]
        
        for obj in self.renderer.objects:
            if not obj.polygon_mm or len(obj.polygon_mm) < 3:
                continue
            
            # Transformar polígono para pixels
            pts_px = []
            for x_mm, y_mm in obj.polygon_mm:
                if transform:
                    x_px, y_px = transform.transform_point(x_mm, y_mm)
                else:
                    x_px, y_px = x_mm, y_mm
                pts_px.append([int(x_px), int(y_px)])
            
            pts = np.array(pts_px, dtype=np.int32)
            
            # Bounding box
            x, y, bw, bh = cv2.boundingRect(pts)
            
            # Verificar se está dentro da imagem
            if x < 0 or y < 0 or x + bw > w or y + bh > h:
                continue
            
            # Criar máscara para esta abertura
            aperture_mask = np.zeros((h, w), dtype=np.uint8)
            cv2.fillPoly(aperture_mask, [pts], 255)
            
            # Calcular área esperada (máscara Gerber)
            expected_area = cv2.countNonZero(aperture_mask)
            
            if expected_area < self.thresholds.min_aperture_area_px:
                continue  # Abertura muito pequena, ignorar
            
            # Calcular área observada (interseção com imagem binarizada)
            intersection = cv2.bitwise_and(aperture_mask, self._binary_mosaic)
            observed_area = cv2.countNonZero(intersection)
            
            # Calcular fill ratio
            fill_ratio = observed_area / expected_area if expected_area > 0 else 0
            
            # Classificar
            fill_pct = fill_ratio * 100
            if fill_pct >= self.thresholds.ok_threshold:
                status = DefectType.OK
            elif fill_pct >= self.thresholds.partial_threshold:
                status = DefectType.PARTIAL
            else:
                status = DefectType.BLOCKED
            
            # Criar resultado da abertura
            inspection = ApertureInspection(
                object_id=obj.id,
                x_mm=obj.x_mm or 0,
                y_mm=obj.y_mm or 0,
                kind=obj.kind,
                expected_area_px=expected_area,
                observed_area_px=observed_area,
                fill_ratio=fill_ratio,
                status=status,
                bbox=(x, y, bw, bh)
            )
            
            result.apertures.append(inspection)
        
        return result
    
    def get_result_overlay(
        self,
        show_all: bool = False,
        alpha: float = 0.4
    ) -> Optional[np.ndarray]:
        """
        Gera overlay visual do resultado da inspeção.
        
        Cores:
        - Verde: OK
        - Amarelo: PARTIAL
        - Vermelho: BLOCKED
        
        Args:
            show_all: Se True, mostra todas as aberturas; se False, só defeitos
            alpha: Transparência do overlay
            
        Returns:
            Imagem BGR com overlay
        """
        if self._mosaic is None or self._last_result is None:
            return None
        
        overlay = self._mosaic.copy()
        
        apertures = self._last_result.apertures if show_all else self._last_result.defects
        
        for apt in apertures:
            # Cor baseada no status
            if apt.status == DefectType.OK:
                color = (0, 255, 0)      # Verde
            elif apt.status == DefectType.PARTIAL:
                color = (0, 255, 255)    # Amarelo
            else:
                color = (0, 0, 255)      # Vermelho
            
            x, y, w, h = apt.bbox
            
            # Desenhar retângulo
            cv2.rectangle(overlay, (x, y), (x + w, y + h), color, 2)
            
            # Label com porcentagem
            label = f"{apt.fill_percentage:.0f}%"
            cv2.putText(overlay, label, (x, y - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        # Blend
        result = cv2.addWeighted(self._mosaic, 1 - alpha, overlay, alpha, 0)
        
        return result
    
    def get_defect_crops(
        self,
        padding: int = 20
    ) -> List[Tuple[ApertureInspection, np.ndarray]]:
        """
        Retorna crops das aberturas com defeito.
        
        Returns:
            Lista de (inspeção, imagem_crop)
        """
        if self._mosaic is None or self._last_result is None:
            return []
        
        crops = []
        h, w = self._mosaic.shape[:2]
        
        for apt in self._last_result.defects:
            x, y, bw, bh = apt.bbox
            
            # Adicionar padding
            x1 = max(0, x - padding)
            y1 = max(0, y - padding)
            x2 = min(w, x + bw + padding)
            y2 = min(h, y + bh + padding)
            
            crop = self._mosaic[y1:y2, x1:x2].copy()
            crops.append((apt, crop))
        
        return crops


# ============================================================================
#  FUNÇÕES DE CONVENIÊNCIA
# ============================================================================

def quick_inspect(
    gerber_path: str,
    mosaic_image: np.ndarray,
    transform: Optional[AlignmentTransform] = None,
    thresholds: Optional[InspectionThresholds] = None
) -> InspectionResult:
    """
    Inspeção rápida em uma única chamada.
    """
    inspector = StencilInspector(thresholds)
    inspector.load_gerber(gerber_path)
    inspector.set_mosaic(mosaic_image)
    if transform:
        inspector.set_alignment(transform)
    return inspector.inspect()


# ============================================================================
#  EXEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) < 3:
        print("Uso: python stencil_inspector.py <arquivo.gbr> <mosaico.png>")
        sys.exit(1)
    
    gerber_path = sys.argv[1]
    mosaic_path = sys.argv[2]
    
    # Carregar mosaico
    mosaic = cv2.imread(mosaic_path)
    if mosaic is None:
        print(f"Erro ao carregar: {mosaic_path}")
        sys.exit(1)
    
    # Executar inspeção
    inspector = StencilInspector()
    inspector.load_gerber(gerber_path)
    inspector.set_mosaic(mosaic)
    
    result = inspector.inspect()
    
    print(f"\n{'='*60}")
    print(f"RESULTADO DA INSPEÇÃO")
    print(f"{'='*60}")
    print(f"📁 Gerber: {gerber_path}")
    print(f"📷 Mosaico: {mosaic_path}")
    print(f"\n📊 Total de aberturas: {result.total_apertures}")
    print(f"   ✅ OK: {result.ok_count}")
    print(f"   ⚠️ PARTIAL: {result.partial_count}")
    print(f"   ❌ BLOCKED: {result.blocked_count}")
    print(f"\n📈 Taxa de aprovação: {result.approval_rate:.1f}%")
    print(f"📋 Status geral: {result.overall_status}")
    
    # Salvar overlay
    overlay = inspector.get_result_overlay(show_all=True)
    if overlay is not None:
        output = "inspection_result.png"
        cv2.imwrite(output, overlay)
        print(f"\n✅ Overlay salvo: {output}")
