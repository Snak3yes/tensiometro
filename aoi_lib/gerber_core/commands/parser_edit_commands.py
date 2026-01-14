"""
ParserEditCommands - Command Pattern para Parser GerberObject.

Este módulo implementa comandos de edição compatíveis com a estrutura
atual de GerberObject do parser (kind, params, polygon_mm).

Objetivo: Reduzir complexidade ciclomática de on_edit_object() (27 → <5)
e on_edit_many_objects() (46 → <5).

NOTA: Esta é uma solução temporária durante migração. Futuramente, migrar
para GerberModel/GerberController completamente.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import copy
import logging

from ..parser import GerberObject
from ..geometry import circle_to_polys_mm, rect_to_polys_mm, oval_to_polys_mm

logger = logging.getLogger(__name__)


# ============================================================================
#  COMMAND ABSTRACTION
# ============================================================================

class ParserEditObjectCommand(ABC):
    """
    Abstração base para comandos de edição de parser.GerberObject.

    Diferença de models.GerberObject:
    - Parser: kind, params, polygon_mm
    - Model: obj_type, x, y, diameter/width/height
    """

    def __init__(self, object: GerberObject):
        self.original = object

    @abstractmethod
    def execute(self, **changes) -> GerberObject:
        """
        Executa a edição do objeto.

        Args:
            **changes: Mudanças a aplicar (depende do tipo)

        Returns:
            Objeto modificado (NOVA instância, não modifica original)
        """
        pass


# ============================================================================
#  CONCRETE COMMANDS
# ============================================================================

class ParserEditCircleCommand(ParserEditObjectCommand):
    """
    Comando para editar objetos circulares (flash_circle).

    Estrutura do parser:
    - kind = "flash_circle"
    - params = {"dia_mm": float}
    - polygon_mm = [(x, y), ...] (calculado via circle_to_polys_mm)
    """

    def execute(self, new_dia_mm: Optional[float] = None, dx: float = 0.0, dy: float = 0.0) -> GerberObject:
        """
        Edita círculo.

        Args:
            new_dia_mm: Novo diâmetro em mm
            dx: Translação em X
            dy: Translação em Y

        Returns:
            Novo objeto modificado
        """
        # Criar cópia para não modificar original
        modified = copy.copy(self.original)
        modified.polygon_mm = copy.copy(modified.polygon_mm)

        # Atualizar diâmetro
        if new_dia_mm is not None:
            if new_dia_mm <= 0:
                raise ValueError(f"Diâmetro deve ser > 0, recebido: {new_dia_mm}")

            modified.params["dia_mm"] = new_dia_mm

            # Recalcular polígono
            if modified.x_mm is not None and modified.y_mm is not None:
                polys = circle_to_polys_mm(modified.x_mm, modified.y_mm, new_dia_mm)
                modified.polygon_mm = polys[0]

        # Aplicar translação
        if dx != 0.0 or dy != 0.0:
            if modified.x_mm is not None:
                modified.x_mm += dx
            if modified.y_mm is not None:
                modified.y_mm += dy

            # Recalcular polígono com nova posição
            dia = modified.params.get("dia_mm", 0.0)
            if modified.x_mm is not None and modified.y_mm is not None and dia > 0:
                polys = circle_to_polys_mm(modified.x_mm, modified.y_mm, dia)
                modified.polygon_mm = polys[0]

        logger.debug(f"Círculo editado: dia={new_dia_mm}, dx={dx}, dy={dy}")
        return modified


class ParserEditRectangleCommand(ParserEditObjectCommand):
    """
    Comando para editar objetos retangulares (flash_rect).

    Estrutura do parser:
    - kind = "flash_rect"
    - params = {"width_mm": float, "height_mm": float}
    - polygon_mm = [(x, y), ...] (calculado via rect_to_polys_mm)
    """

    def execute(
        self,
        new_width_mm: Optional[float] = None,
        new_height_mm: Optional[float] = None,
        scale_x: float = 1.0,
        scale_y: float = 1.0,
        dx: float = 0.0,
        dy: float = 0.0
    ) -> GerberObject:
        """
        Edita retângulo.

        Args:
            new_width_mm: Nova largura em mm
            new_height_mm: Nova altura em mm
            scale_x: Fator de escala em X
            scale_y: Fator de escala em Y
            dx: Translação em X
            dy: Translação em Y

        Returns:
            Novo objeto modificado
        """
        modified = copy.copy(self.original)
        modified.polygon_mm = copy.copy(modified.polygon_mm)

        # Obter dimensões atuais
        cur_w = float(modified.params.get("width_mm", 0.0))
        cur_h = float(modified.params.get("height_mm", 0.0))

        # Escala优先级更高 que dimensões absolutas
        if scale_x != 1.0:
            cur_w = cur_w * scale_x
        elif new_width_mm is not None:
            cur_w = new_width_mm

        if scale_y != 1.0:
            cur_h = cur_h * scale_y
        elif new_height_mm is not None:
            cur_h = new_height_mm

        if cur_w <= 0 or cur_h <= 0:
            raise ValueError(f"Largura/altura devem ser > 0: w={cur_w}, h={cur_h}")

        modified.params["width_mm"] = cur_w
        modified.params["height_mm"] = cur_h

        # Translação
        if dx != 0.0 and modified.x_mm is not None:
            modified.x_mm += dx
        if dy != 0.0 and modified.y_mm is not None:
            modified.y_mm += dy

        # Recalcular polígono
        if modified.x_mm is not None and modified.y_mm is not None:
            polys = rect_to_polys_mm(modified.x_mm, modified.y_mm, cur_w, cur_h)
            modified.polygon_mm = polys[0]

        logger.debug(f"Retângulo editado: w={cur_w}, h={cur_h}, dx={dx}, dy={dy}")
        return modified


class ParserEditObroundCommand(ParserEditObjectCommand):
    """
    Comando para editar objetos obround (flash_oval).

    Estrutura do parser:
    - kind = "flash_oval"
    - params = {"width_mm": float, "height_mm": float}
    - polygon_mm = [(x, y), ...] (calculado via oval_to_polys_mm)
    """

    def execute(
        self,
        new_width_mm: Optional[float] = None,
        new_height_mm: Optional[float] = None,
        scale_x: float = 1.0,
        scale_y: float = 1.0,
        dx: float = 0.0,
        dy: float = 0.0
    ) -> GerberObject:
        """Edita obround (mesma lógica que retângulo)."""
        modified = copy.copy(self.original)
        modified.polygon_mm = copy.copy(modified.polygon_mm)

        cur_w = float(modified.params.get("width_mm", 0.0))
        cur_h = float(modified.params.get("height_mm", 0.0))

        if scale_x != 1.0:
            cur_w = cur_w * scale_x
        elif new_width_mm is not None:
            cur_w = new_width_mm

        if scale_y != 1.0:
            cur_h = cur_h * scale_y
        elif new_height_mm is not None:
            cur_h = new_height_mm

        if cur_w <= 0 or cur_h <= 0:
            raise ValueError(f"Largura/altura devem ser > 0: w={cur_w}, h={cur_h}")

        modified.params["width_mm"] = cur_w
        modified.params["height_mm"] = cur_h

        if dx != 0.0 and modified.x_mm is not None:
            modified.x_mm += dx
        if dy != 0.0 and modified.y_mm is not None:
            modified.y_mm += dy

        if modified.x_mm is not None and modified.y_mm is not None:
            polys = oval_to_polys_mm(modified.x_mm, modified.y_mm, cur_w, cur_h)
            modified.polygon_mm = polys[0]

        logger.debug(f"Obround editado: w={cur_w}, h={cur_h}, dx={dx}, dy={dy}")
        return modified


class ParserEditRegionCommand(ParserEditObjectCommand):
    """
    Comando para editar regiões (region).

    Estrutura do parser:
    - kind = "region"
    - polygon_mm = [(x, y), ...] (lista de vértices)
    - params pode estar vazio ou ter metadados

    Regiões são editadas por escala do polígono em relação ao centro.
    """

    def execute(
        self,
        scale_x: float = 1.0,
        scale_y: float = 1.0,
        dx: float = 0.0,
        dy: float = 0.0
    ) -> GerberObject:
        """
        Edita região.

        Args:
            scale_x: Fator de escala em X
            scale_y: Fator de escala em Y
            dx: Translação em X
            dy: Translação em Y

        Returns:
            Novo objeto modificado
        """
        modified = copy.copy(self.original)

        if not modified.polygon_mm or len(modified.polygon_mm) < 3:
            raise ValueError("Região não possui polígono válido")

        # Calcular centro geométrico
        xs = [p[0] for p in modified.polygon_mm]
        ys = [p[1] for p in modified.polygon_mm]
        minx, maxx = min(xs), max(xs)
        miny, maxy = min(ys), max(ys)
        cx = (minx + maxx) / 2.0
        cy = (miny + maxy) / 2.0

        # Aplicar escala em relação ao centro
        new_poly = []
        for x, y in modified.polygon_mm:
            nx = cx + (x - cx) * scale_x + dx
            ny = cy + (y - cy) * scale_y + dy
            new_poly.append((nx, ny))

        # Garantir fechamento explícito
        if new_poly and new_poly[0] != new_poly[-1]:
            new_poly.append(new_poly[0])

        modified.polygon_mm = new_poly

        # Atualizar posição (opcional, para consistência)
        if modified.x_mm is not None:
            modified.x_mm += dx
        if modified.y_mm is not None:
            modified.y_mm += dy

        logger.debug(f"Região editada: scale_x={scale_x}, scale_y={scale_y}")
        return modified


# ============================================================================
#  FACTORY FUNCTION
# ============================================================================

def create_parser_edit_command(obj: GerberObject) -> Optional[ParserEditObjectCommand]:
    """
    Factory Function para criar comando apropriado.

    Elimina cadeia if/elif/else em mainwindow.py.

    Args:
        obj: Objeto parser.GerberObject

    Returns:
        Comando apropriado ou None se tipo não suportado

    Exemplo:
        >>> obj = GerberObject(kind="flash_circle", ...)
        >>> cmd = create_parser_edit_command(obj)
        >>> if cmd:
        >>>     modified = cmd.execute(new_dia_mm=10.0)
    """
    commands = {
        "flash_circle": ParserEditCircleCommand,
        "flash_rect": ParserEditRectangleCommand,
        "flash_oval": ParserEditObroundCommand,
        "region": ParserEditRegionCommand,
    }

    cmd_class = commands.get(obj.kind)
    if cmd_class is None:
        logger.warning(f"Tipo de objeto não suportado para edição: {obj.kind}")
        return None

    return cmd_class(obj)
