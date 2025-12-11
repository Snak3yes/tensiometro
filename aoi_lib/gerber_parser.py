"""
gerber_parser.py
----------------
Parser Gerber com detecção automática de fiduciais para o sistema AOI.

Este módulo oferece:
- Parsing completo de arquivos Gerber RS-274X
- Identificação automática de candidatos a fiduciais
- Extração de bounding box e estatísticas
- Conversão para coordenadas em mm

Fiduciais são tipicamente:
- Círculos isolados nos cantos do stencil
- Posicionados fora da área de pads
- Usados para alinhamento visual
"""

from __future__ import annotations

import math
import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path

# Importar do parser existente (se existir) ou definir aqui
import sys
_gerber_viewer_path = Path(__file__).parent.parent / "testes_gerber"
if str(_gerber_viewer_path) not in sys.path:
    sys.path.insert(0, str(_gerber_viewer_path))

try:
    from gerber_viewer.parser import (
        GerberObject, build_layer_objects_mm, gerber_to_records
    )
    from gerber_viewer.apertures import (
        ApertureInstance, ApertureMacro, parse_all_macros, parse_add
    )
    from gerber_viewer.config import (
        GerberConfig, parse_gerber_config, parse_coord, to_mm_from_unit
    )
    from gerber_viewer.geometry import (
        circle_to_polys_mm, rect_to_polys_mm, oval_to_polys_mm
    )
except ImportError as e:
    raise ImportError(
        f"Gerber viewer modules not found. Ensure 'testes_gerber/gerber_viewer' exists: {e}"
    )

log = logging.getLogger(__name__)


# ============================================================================
#  DATACLASSES PARA RESULTADOS
# ============================================================================

@dataclass
class FiducialCandidate:
    """Candidato a fiducial identificado no arquivo Gerber."""
    id: int
    x_mm: float
    y_mm: float
    kind: str  # "circle", "rect", etc.
    diameter_mm: Optional[float] = None
    width_mm: Optional[float] = None
    height_mm: Optional[float] = None
    corner: Optional[str] = None  # "top_left", "top_right", "bottom_left", "bottom_right"
    score: float = 0.0  # Pontuação de confiança (0-100)
    gerber_object: Optional[GerberObject] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa para dicionário."""
        return {
            "id": self.id,
            "x_mm": self.x_mm,
            "y_mm": self.y_mm,
            "kind": self.kind,
            "diameter_mm": self.diameter_mm,
            "width_mm": self.width_mm,
            "height_mm": self.height_mm,
            "corner": self.corner,
            "score": self.score,
        }


@dataclass
class GerberBounds:
    """Limites do arquivo Gerber em mm."""
    min_x: float = 0.0
    max_x: float = 0.0
    min_y: float = 0.0
    max_y: float = 0.0
    
    @property
    def width(self) -> float:
        return self.max_x - self.min_x
    
    @property
    def height(self) -> float:
        return self.max_y - self.min_y
    
    @property
    def center(self) -> Tuple[float, float]:
        return (
            (self.min_x + self.max_x) / 2.0,
            (self.min_y + self.max_y) / 2.0
        )


@dataclass
class GerberStats:
    """Estatísticas do arquivo Gerber."""
    total_objects: int = 0
    circles: int = 0
    rectangles: int = 0
    ovals: int = 0
    macros: int = 0
    regions: int = 0
    bounds: Optional[GerberBounds] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_objects": self.total_objects,
            "circles": self.circles,
            "rectangles": self.rectangles,
            "ovals": self.ovals,
            "macros": self.macros,
            "regions": self.regions,
            "bounds": {
                "min_x": self.bounds.min_x if self.bounds else 0,
                "max_x": self.bounds.max_x if self.bounds else 0,
                "min_y": self.bounds.min_y if self.bounds else 0,
                "max_y": self.bounds.max_y if self.bounds else 0,
                "width": self.bounds.width if self.bounds else 0,
                "height": self.bounds.height if self.bounds else 0,
            }
        }


@dataclass
class ParsedGerber:
    """Resultado completo do parsing de um arquivo Gerber."""
    filepath: str
    config: Optional[GerberConfig] = None
    objects: List[GerberObject] = field(default_factory=list)
    stats: Optional[GerberStats] = None
    fiducial_candidates: List[FiducialCandidate] = field(default_factory=list)
    error: Optional[str] = None


# ============================================================================
#  CLASSE PRINCIPAL DE PARSING
# ============================================================================

class GerberParser:
    """
    Parser de arquivo Gerber com detecção automática de fiduciais.
    
    Uso típico:
        parser = GerberParser()
        result = parser.parse_file("stencil.gbr")
        
        if result.error:
            print(f"Erro: {result.error}")
        else:
            print(f"Objetos: {result.stats.total_objects}")
            print(f"Candidatos a fiducial: {len(result.fiducial_candidates)}")
    """
    
    # Parâmetros de detecção de fiduciais
    FIDUCIAL_MIN_DIAMETER_MM = 0.5   # Diâmetro mínimo
    FIDUCIAL_MAX_DIAMETER_MM = 3.0   # Diâmetro máximo
    CORNER_MARGIN_PERCENT = 0.15     # % da dimensão para considerar "canto"
    ISOLATION_RADIUS_MM = 5.0        # Raio de isolamento (sem vizinhos próximos)
    
    def __init__(self):
        self.last_result: Optional[ParsedGerber] = None
    
    def parse_file(self, filepath: str) -> ParsedGerber:
        """
        Faz o parsing de um arquivo Gerber.
        
        Args:
            filepath: Caminho do arquivo .gbr
            
        Returns:
            ParsedGerber com objetos, estatísticas e candidatos a fiduciais
        """
        path = Path(filepath)
        result = ParsedGerber(filepath=str(path))
        
        if not path.exists():
            result.error = f"Arquivo não encontrado: {filepath}"
            log.error(result.error)
            return result
        
        try:
            # Ler arquivo
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            log.info(f"Parsing Gerber: {path.name} ({len(lines)} linhas)")
            
            # Parsear configuração
            config = parse_gerber_config(lines)
            result.config = config
            log.debug(f"Config: unit={config.unit}, format={config.fmt_int}.{config.fmt_dec}")
            
            # Parsear macros e aberturas
            macros = parse_all_macros(lines)
            apertures = parse_add(lines, config)
            log.debug(f"Macros: {len(macros)}, Apertures: {len(apertures)}")
            
            # Parsear objetos
            objects = build_layer_objects_mm(lines, macros, apertures, config)
            result.objects = objects
            log.info(f"Objetos parseados: {len(objects)}")
            
            # Calcular estatísticas
            result.stats = self._calculate_stats(objects)
            
            # Detectar candidatos a fiduciais
            result.fiducial_candidates = self._detect_fiducials(objects, result.stats.bounds)
            log.info(f"Candidatos a fiducial: {len(result.fiducial_candidates)}")
            
            self.last_result = result
            
        except Exception as e:
            result.error = f"Erro no parsing: {str(e)}"
            log.exception(result.error)
        
        return result
    
    def parse_lines(self, lines: List[str]) -> ParsedGerber:
        """
        Faz o parsing de linhas de texto Gerber já carregadas.
        
        Args:
            lines: Lista de linhas do arquivo Gerber
            
        Returns:
            ParsedGerber com objetos, estatísticas e candidatos a fiduciais
        """
        result = ParsedGerber(filepath="<memory>")
        
        try:
            config = parse_gerber_config(lines)
            result.config = config
            
            macros = parse_all_macros(lines)
            apertures = parse_add(lines, config)
            
            objects = build_layer_objects_mm(lines, macros, apertures, config)
            result.objects = objects
            
            result.stats = self._calculate_stats(objects)
            result.fiducial_candidates = self._detect_fiducials(objects, result.stats.bounds)
            
            self.last_result = result
            
        except Exception as e:
            result.error = f"Erro no parsing: {str(e)}"
            log.exception(result.error)
        
        return result
    
    def _calculate_stats(self, objects: List[GerberObject]) -> GerberStats:
        """Calcula estatísticas do arquivo Gerber."""
        stats = GerberStats(total_objects=len(objects))
        
        all_x = []
        all_y = []
        
        for obj in objects:
            # Contar por tipo
            if obj.kind == "flash_circle":
                stats.circles += 1
            elif obj.kind == "flash_rect":
                stats.rectangles += 1
            elif obj.kind == "flash_oval":
                stats.ovals += 1
            elif obj.kind == "flash_macro":
                stats.macros += 1
            elif obj.kind == "region":
                stats.regions += 1
            
            # Coletar coordenadas para bounding box
            if obj.x_mm is not None:
                all_x.append(obj.x_mm)
            if obj.y_mm is not None:
                all_y.append(obj.y_mm)
            
            # Adicionar polígono ao bounding box
            for px, py in obj.polygon_mm:
                all_x.append(px)
                all_y.append(py)
        
        # Calcular bounds
        if all_x and all_y:
            stats.bounds = GerberBounds(
                min_x=min(all_x),
                max_x=max(all_x),
                min_y=min(all_y),
                max_y=max(all_y)
            )
        
        return stats
    
    def _detect_fiducials(
        self, 
        objects: List[GerberObject],
        bounds: Optional[GerberBounds]
    ) -> List[FiducialCandidate]:
        """
        Detecta candidatos a fiduciais nos objetos Gerber.
        
        Critérios de detecção:
        1. Geometria compatível (círculo ou retângulo pequeno)
        2. Dimensões típicas de fiducial (0.5-3mm)
        3. Posição próxima aos cantos
        4. Isolamento relativo (sem muitos vizinhos próximos)
        """
        if not bounds:
            return []
        
        candidates = []
        candidate_id = 0
        
        # Definir limites dos cantos
        margin_x = bounds.width * self.CORNER_MARGIN_PERCENT
        margin_y = bounds.height * self.CORNER_MARGIN_PERCENT
        
        corner_regions = {
            "bottom_left": (bounds.min_x, bounds.min_x + margin_x, 
                           bounds.min_y, bounds.min_y + margin_y),
            "bottom_right": (bounds.max_x - margin_x, bounds.max_x,
                            bounds.min_y, bounds.min_y + margin_y),
            "top_left": (bounds.min_x, bounds.min_x + margin_x,
                        bounds.max_y - margin_y, bounds.max_y),
            "top_right": (bounds.max_x - margin_x, bounds.max_x,
                         bounds.max_y - margin_y, bounds.max_y),
        }
        
        for obj in objects:
            if obj.x_mm is None or obj.y_mm is None:
                continue
            
            # Verificar tipo compatível
            if obj.kind not in ("flash_circle", "flash_rect"):
                continue
            
            # Verificar dimensões
            diameter = None
            width = None
            height = None
            
            if obj.kind == "flash_circle":
                diameter = obj.params.get("dia_mm", 0)
                if not (self.FIDUCIAL_MIN_DIAMETER_MM <= diameter <= self.FIDUCIAL_MAX_DIAMETER_MM):
                    continue
                    
            elif obj.kind == "flash_rect":
                width = obj.params.get("width_mm", 0)
                height = obj.params.get("height_mm", 0)
                max_dim = max(width, height)
                if not (self.FIDUCIAL_MIN_DIAMETER_MM <= max_dim <= self.FIDUCIAL_MAX_DIAMETER_MM):
                    continue
            
            # Verificar se está em um canto
            corner = None
            for corner_name, (x1, x2, y1, y2) in corner_regions.items():
                if x1 <= obj.x_mm <= x2 and y1 <= obj.y_mm <= y2:
                    corner = corner_name
                    break
            
            # Calcular score
            score = self._calculate_fiducial_score(
                obj, objects, bounds, corner
            )
            
            # Adicionar candidato se score mínimo
            if score >= 30:  # Score mínimo de 30%
                candidate = FiducialCandidate(
                    id=candidate_id,
                    x_mm=obj.x_mm,
                    y_mm=obj.y_mm,
                    kind=obj.kind.replace("flash_", ""),
                    diameter_mm=diameter,
                    width_mm=width,
                    height_mm=height,
                    corner=corner,
                    score=score,
                    gerber_object=obj
                )
                candidates.append(candidate)
                candidate_id += 1
        
        # Ordenar por score
        candidates.sort(key=lambda c: c.score, reverse=True)
        
        return candidates
    
    def _calculate_fiducial_score(
        self,
        obj: GerberObject,
        all_objects: List[GerberObject],
        bounds: GerberBounds,
        corner: Optional[str]
    ) -> float:
        """
        Calcula score de probabilidade de ser um fiducial.
        
        Fatores:
        - Estar em um canto: +40 pontos
        - Ser círculo: +20 pontos
        - Estar isolado: +30 pontos
        - Tamanho típico (1-2mm): +10 pontos
        """
        score = 0.0
        
        # Bônus por estar em canto
        if corner:
            score += 40.0
        
        # Bônus por ser círculo
        if obj.kind == "flash_circle":
            score += 20.0
            
            # Bônus por tamanho típico (1-2mm)
            dia = obj.params.get("dia_mm", 0)
            if 1.0 <= dia <= 2.0:
                score += 10.0
        
        # Verificar isolamento
        neighbors = 0
        for other in all_objects:
            if other.id == obj.id:
                continue
            if other.x_mm is None or other.y_mm is None:
                continue
            
            dist = math.hypot(obj.x_mm - other.x_mm, obj.y_mm - other.y_mm)
            if dist < self.ISOLATION_RADIUS_MM:
                neighbors += 1
        
        # Menos vizinhos = mais provável de ser fiducial
        if neighbors == 0:
            score += 30.0
        elif neighbors <= 2:
            score += 20.0
        elif neighbors <= 5:
            score += 10.0
        
        return min(100.0, score)
    
    def get_suggested_fiducials(
        self, 
        count: int = 2
    ) -> List[FiducialCandidate]:
        """
        Retorna os melhores candidatos a fiducial.
        
        Tenta retornar candidatos de cantos diferentes para melhor alinhamento.
        
        Args:
            count: Número de candidatos desejados
            
        Returns:
            Lista de candidatos ordenados por score
        """
        if not self.last_result or not self.last_result.fiducial_candidates:
            return []
        
        candidates = self.last_result.fiducial_candidates.copy()
        
        # Preferir candidatos de cantos diferentes
        result = []
        used_corners = set()
        
        # Primeira passada: pegar candidatos de cantos diferentes
        for c in candidates:
            if c.corner and c.corner not in used_corners:
                result.append(c)
                used_corners.add(c.corner)
                if len(result) >= count:
                    break
        
        # Segunda passada: completar com os melhores restantes
        if len(result) < count:
            for c in candidates:
                if c not in result:
                    result.append(c)
                    if len(result) >= count:
                        break
        
        return result[:count]
    
    def get_objects_in_region(
        self,
        x1_mm: float, y1_mm: float,
        x2_mm: float, y2_mm: float
    ) -> List[GerberObject]:
        """
        Retorna objetos dentro de uma região retangular.
        
        Args:
            x1_mm, y1_mm: Canto inferior esquerdo
            x2_mm, y2_mm: Canto superior direito
            
        Returns:
            Lista de objetos na região
        """
        if not self.last_result:
            return []
        
        min_x, max_x = min(x1_mm, x2_mm), max(x1_mm, x2_mm)
        min_y, max_y = min(y1_mm, y2_mm), max(y1_mm, y2_mm)
        
        return [
            obj for obj in self.last_result.objects
            if obj.x_mm is not None and obj.y_mm is not None
            and min_x <= obj.x_mm <= max_x
            and min_y <= obj.y_mm <= max_y
        ]


# ============================================================================
#  FUNÇÕES UTILITÁRIAS
# ============================================================================

def load_gerber_file(filepath: str) -> ParsedGerber:
    """
    Função helper para carregar arquivo Gerber rapidamente.
    
    Args:
        filepath: Caminho do arquivo .gbr
        
    Returns:
        ParsedGerber com resultados
    """
    parser = GerberParser()
    return parser.parse_file(filepath)


def get_gerber_bounds(filepath: str) -> Optional[GerberBounds]:
    """
    Retorna apenas o bounding box de um arquivo Gerber.
    
    Args:
        filepath: Caminho do arquivo .gbr
        
    Returns:
        GerberBounds ou None se erro
    """
    result = load_gerber_file(filepath)
    if result.error or not result.stats:
        return None
    return result.stats.bounds


# ============================================================================
#  EXEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    import sys
    
    logging.basicConfig(level=logging.DEBUG)
    
    if len(sys.argv) < 2:
        print("Uso: python gerber_parser.py <arquivo.gbr>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    print(f"\nParsing: {filepath}")
    print("-" * 60)
    
    result = load_gerber_file(filepath)
    
    if result.error:
        print(f"ERRO: {result.error}")
        sys.exit(1)
    
    # Estatísticas
    stats = result.stats
    print(f"\n📊 Estatísticas:")
    print(f"   Total objetos: {stats.total_objects}")
    print(f"   Círculos: {stats.circles}")
    print(f"   Retângulos: {stats.rectangles}")
    print(f"   Ovais: {stats.ovals}")
    print(f"   Macros: {stats.macros}")
    print(f"   Regiões: {stats.regions}")
    
    if stats.bounds:
        print(f"\n📐 Bounding Box:")
        print(f"   X: {stats.bounds.min_x:.3f} a {stats.bounds.max_x:.3f} mm")
        print(f"   Y: {stats.bounds.min_y:.3f} a {stats.bounds.max_y:.3f} mm")
        print(f"   Dimensões: {stats.bounds.width:.3f} x {stats.bounds.height:.3f} mm")
    
    # Candidatos a fiduciais
    if result.fiducial_candidates:
        print(f"\n🎯 Candidatos a Fiducial ({len(result.fiducial_candidates)}):")
        for c in result.fiducial_candidates[:8]:
            corner_str = f" [{c.corner}]" if c.corner else ""
            dim_str = f"Ø{c.diameter_mm:.2f}" if c.diameter_mm else f"{c.width_mm:.2f}x{c.height_mm:.2f}"
            print(f"   #{c.id}: ({c.x_mm:.2f}, {c.y_mm:.2f}) {c.kind} {dim_str}{corner_str} - Score: {c.score:.0f}%")
        
        parser = GerberParser()
        parser.last_result = result
        suggested = parser.get_suggested_fiducials(2)
        if suggested:
            print(f"\n✅ Fiduciais Sugeridos:")
            for c in suggested:
                print(f"   ({c.x_mm:.2f}, {c.y_mm:.2f}) - {c.corner or 'centro'}")
    else:
        print("\n⚠️ Nenhum candidato a fiducial detectado")
