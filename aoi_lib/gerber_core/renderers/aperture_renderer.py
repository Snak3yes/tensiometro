"""
Aperture Renderers - Strategy Pattern for Gerber Aperture Rendering

Este módulo implementa renderizadores para diferentes tipos de apertures Gerber,
seguindo o Strategy Pattern para eliminar cadeias if/elif/else e reduzir
complexidade ciclomática (47 → <5).

Design Pattern: Strategy + Template Method
- Strategy: Diferentes algoritmos para cada tipo de aperture
- Template Method: Estrutura compartilhada em ApertureRenderer

Components:
    - ApertureRenderer (ABC): Classe base com estrutura compartilhada
    - CircleRenderer: Renderiza círculos (kind="circle")
    - RectangleRenderer: Renderiza retângulos (kind="rect")
    - ObroundRenderer: Renderiza obrounds (kind="oval")
    - MacroRenderer: Renderiza macros (kind="macro")
    - RegionRenderer: Renderiza regiões (kind="region")
    - create_aperture_renderer(): Factory Function

Author: Claude Sonnet 4.5
Date: 2026-01-14
Track: solid_refactoring_phase2_20260114 (Phase 2 - Parser Refactoring)
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..apertures import ApertureInstance, ApertureMacro
    from ..parser import GerberObject

from ..geometry import (
    circle_to_polys_mm,
    rect_to_polys_mm,
    oval_to_polys_mm,
)

Point = tuple[float, float]
logger = logging.getLogger(__name__)


class ApertureRenderer(ABC):
    """
    Classe base abstrata para renderizadores de aperture.

    Implementa o Template Method Pattern: define a estrutura do algoritmo
    de renderização, mas delega detalhes específicos para subclasses.

    Responsabilidades:
        - Renderizar aperture para lista de polígonos
        - Criar GerberObject com metadados apropriados
        - Validação de parâmetros

    Subclasses devem implementar:
        - _get_polygons(): Renderizar geometria específica
        - _get_object_kind(): Retornar kind string apropriado
        - _get_params(): Retornar dicionário de parâmetros
    """

    def __init__(self) -> None:
        """Inicializa renderizador."""
        self._logger = logger

    def render(
        self,
        x_mm: float,
        y_mm: float,
        dcode: int,
        aperture: ApertureInstance,
    ) -> tuple[list[list[Point]], list[GerberObject]]:
        """
        Template Method: Renderiza aperture e retorna polígonos + objetos.

        Este método define a estrutura do algoritmo de renderização:
        1. Renderizar polígonos específicos (delegado para subclasses)
        2. Criar GerberObject com metadados
        3. Retornar tupla (polígonos, objetos)

        Args:
            x_mm: Posição X em mm
            y_mm: Posição Y em mm
            dcode: D-code ativo
            aperture: Instância de aperture a renderizar

        Returns:
            Tupla (polígonos, objetos) onde:
                - polígonos: lista de listas de pontos (x,y)
                - objetos: lista de GerberObject criados

        Raises:
            ValueError: Se parâmetros da aperture forem inválidos
        """
        from ..parser import GerberObject

        # Passo 1: Renderizar polígonos (delegado para subclasses)
        polys = self._get_polygons(x_mm, y_mm, aperture)

        # Passo 2: Criar objetos Gerber
        objects = []
        for poly in polys:
            obj = GerberObject(
                id=0,  # Será atribuído pelo caller
                kind=self._get_object_kind(),
                dcode=dcode,
                x_mm=x_mm,
                y_mm=y_mm,
                params=self._get_params(aperture),
                polygon_mm=poly,
            )
            objects.append(obj)

        return polys, objects

    @abstractmethod
    def _get_polygons(
        self,
        x_mm: float,
        y_mm: float,
        aperture: ApertureInstance,
    ) -> list[list[Point]]:
        """
        Renderiza geometria específica da aperture.

        Este método deve ser implementado por subclasses para renderizar
        a geometria específica do tipo de aperture (círculo, retângulo, etc).

        Args:
            x_mm: Posição X em mm
            y_mm: Posição Y em mm
            aperture: Instância de aperture

        Returns:
            Lista de polígonos (cada polígono é lista de pontos x,y)

        Raises:
            ValueError: Se parâmetros da aperture forem inválidos
        """
        pass

    @abstractmethod
    def _get_object_kind(self) -> str:
        """
        Retorna o tipo (kind) do GerberObject.

        Returns:
            String representando o tipo (ex: "flash_circle", "flash_rect")
        """
        pass

    @abstractmethod
    def _get_params(self, aperture: ApertureInstance) -> dict[str, float | str]:
        """
        Extrai parâmetros da aperture para o GerberObject.

        Args:
            aperture: Instância de aperture

        Returns:
            Dicionário de parâmetros (ex: {"dia_mm": 1.5})
        """
        pass


class CircleRenderer(ApertureRenderer):
    """
    Renderizador para apertures circulares (kind="circle").

    Gerber Specification:
        - Códigos: C, código padrão
        - Parâmetros: dia_mm (diâmetro em mm)
        - Geometria: Círculo centrado em (x_mm, y_mm)

    Example:
        >>> renderer = CircleRenderer()
        >>> polys, objs = renderer.render(x_mm=0.0, y_mm=0.0, dcode=10, aperture)
        >>> polys[0]  # Lista de pontos do polígono aproximando círculo
    """

    def _get_polygons(
        self,
        x_mm: float,
        y_mm: float,
        aperture: ApertureInstance,
    ) -> list[list[Point]]:
        """Renderiza círculo usando circle_to_polys_mm."""
        dia_mm_str = aperture.params.get("dia_mm")
        if dia_mm_str is None:
            raise ValueError("Circle aperture missing 'dia_mm' parameter")

        try:
            dia_mm = float(dia_mm_str)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid dia_mm value: {dia_mm_str}") from e

        if dia_mm <= 0:
            raise ValueError(f"Circle diameter must be > 0, got: {dia_mm}")

        polys = circle_to_polys_mm(x_mm, y_mm, dia_mm)
        self._logger.debug(f"🔵 Rendered circle at ({x_mm:.3f}, {y_mm:.3f}), dia={dia_mm:.3f}mm")
        return polys

    def _get_object_kind(self) -> str:
        """Retorna 'flash_circle'."""
        return "flash_circle"

    def _get_params(self, aperture: ApertureInstance) -> dict[str, float | str]:
        """Extrai parâmetro dia_mm."""
        dia_mm_str = aperture.params.get("dia_mm")
        if dia_mm_str is None:
            raise ValueError("Circle aperture missing 'dia_mm' parameter")

        try:
            dia_mm = float(dia_mm_str)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid dia_mm value: {dia_mm_str}") from e

        return {"dia_mm": dia_mm}


class RectangleRenderer(ApertureRenderer):
    """
    Renderizador para apertures retangulares (kind="rect").

    Gerber Specification:
        - Códigos: R, código 20
        - Parâmetros: width_mm, height_mm
        - Geometria: Retângulo centrado em (x_mm, y_mm)

    Example:
        >>> renderer = RectangleRenderer()
        >>> polys, objs = renderer.render(x_mm=0.0, y_mm=0.0, dcode=10, aperture)
        >>> polys[0]  # Lista de 4 pontos do retângulo
    """

    def _get_polygons(
        self,
        x_mm: float,
        y_mm: float,
        aperture: ApertureInstance,
    ) -> list[list[Point]]:
        """Renderiza retângulo usando rect_to_polys_mm."""
        width_str = aperture.params.get("width_mm")
        height_str = aperture.params.get("height_mm")

        if width_str is None or height_str is None:
            raise ValueError("Rectangle aperture missing 'width_mm' or 'height_mm' parameter")

        try:
            width_mm = float(width_str)
            height_mm = float(height_str)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid dimensions: width={width_str}, height={height_str}") from e

        if width_mm <= 0 or height_mm <= 0:
            raise ValueError(
                f"Rectangle dimensions must be > 0: width={width_mm}, height={height_mm}"
            )

        polys = rect_to_polys_mm(x_mm, y_mm, width_mm, height_mm)
        self._logger.debug(
            f"🟦 Rendered rectangle at ({x_mm:.3f}, {y_mm:.3f}), "
            f"size={width_mm:.3f}x{height_mm:.3f}mm"
        )
        return polys

    def _get_object_kind(self) -> str:
        """Retorna 'flash_rect'."""
        return "flash_rect"

    def _get_params(self, aperture: ApertureInstance) -> dict[str, float | str]:
        """Extrai parâmetros width_mm e height_mm."""
        width_str = aperture.params.get("width_mm")
        height_str = aperture.params.get("height_mm")

        if width_str is None or height_str is None:
            raise ValueError("Rectangle aperture missing 'width_mm' or 'height_mm' parameter")

        try:
            width_mm = float(width_str)
            height_mm = float(height_str)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid dimensions: width={width_str}, height={height_str}") from e

        return {"width_mm": width_mm, "height_mm": height_mm}


class ObroundRenderer(ApertureRenderer):
    """
    Renderizador para apertures obround (kind="oval").

    Gerber Specification:
        - Códigos: O, código 21
        - Parâmetros: width_mm, height_mm
        - Geometria: Obround (retângulo com semi-círculos nas extremidades)

    Example:
        >>> renderer = ObroundRenderer()
        >>> polys, objs = renderer.render(x_mm=0.0, y_mm=0.0, dcode=10, aperture)
        >>> polys[0]  # Lista de pontos do obround
    """

    def _get_polygons(
        self,
        x_mm: float,
        y_mm: float,
        aperture: ApertureInstance,
    ) -> list[list[Point]]:
        """Renderiza obround usando oval_to_polys_mm."""
        width_str = aperture.params.get("width_mm")
        height_str = aperture.params.get("height_mm")

        if width_str is None or height_str is None:
            raise ValueError("Obround aperture missing 'width_mm' or 'height_mm' parameter")

        try:
            width_mm = float(width_str)
            height_mm = float(height_str)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid dimensions: width={width_str}, height={height_str}") from e

        if width_mm <= 0 or height_mm <= 0:
            raise ValueError(
                f"Obround dimensions must be > 0: width={width_mm}, height={height_mm}"
            )

        polys = oval_to_polys_mm(x_mm, y_mm, width_mm, height_mm)
        self._logger.debug(
            f"🔵 Rendered obround at ({x_mm:.3f}, {y_mm:.3f}), "
            f"size={width_mm:.3f}x{height_mm:.3f}mm"
        )
        return polys

    def _get_object_kind(self) -> str:
        """Retorna 'flash_oval'."""
        return "flash_oval"

    def _get_params(self, aperture: ApertureInstance) -> dict[str, float | str]:
        """Extrai parâmetros width_mm e height_mm."""
        width_str = aperture.params.get("width_mm")
        height_str = aperture.params.get("height_mm")

        if width_str is None or height_str is None:
            raise ValueError("Obround aperture missing 'width_mm' or 'height_mm' parameter")

        try:
            width_mm = float(width_str)
            height_mm = float(height_str)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid dimensions: width={width_str}, height={height_str}") from e

        return {"width_mm": width_mm, "height_mm": height_mm}


class MacroRenderer(ApertureRenderer):
    """
    Renderizador para apertures macro (kind="macro").

    Gerber Specification:
        - Códigos: AM (Aperture Macro)
        - Parâmetros: macro_name (string)
        - Geometria: Definida pela macro (pode ser complexa)

    Macros são renderizadas usando o método render() próprio da ApertureMacro.

    Example:
        >>> renderer = MacroRenderer()
        >>> polys, objs = renderer.render(x_mm=0.0, y_mm=0.0, dcode=10, aperture, macros)
        >>> polys[0]  # Polígono da macro
    """

    def __init__(self) -> None:
        """Inicializa renderizador de macro."""
        super().__init__()
        self._macros: dict[str, ApertureMacro] = {}

    def set_macros(self, macros: dict[str, ApertureMacro]) -> None:
        """
        Define dicionário de macros disponíveis.

        Args:
            macros: Dicionário mapping macro_name → ApertureMacro
        """
        self._macros = macros

    def _get_polygons(
        self,
        x_mm: float,
        y_mm: float,
        aperture: ApertureInstance,
    ) -> list[list[Point]]:
        """Renderiza macro usando ApertureMacro.render()."""
        macro_name = aperture.params.get("macro_name")
        if macro_name is None:
            raise ValueError("Macro aperture missing 'macro_name' parameter")

        if not isinstance(macro_name, str):
            raise ValueError(f"macro_name must be string, got: {type(macro_name)}")

        macro = self._macros.get(macro_name)
        if macro is None:
            raise ValueError(f"Macro not found: {macro_name}")

        # Renderizar macro com parâmetros padrão
        polys = macro.render(
            scale_x=1.0,
            scale_y=1.0,
            rot_deg=0.0,
            trans=(x_mm, y_mm),
        )

        self._logger.debug(
            f"📐 Rendered macro '{macro_name}' at ({x_mm:.3f}, {y_mm:.3f}), "
            f"{len(polys)} polygons"
        )
        return polys

    def _get_object_kind(self) -> str:
        """Retorna 'flash_macro'."""
        return "flash_macro"

    def _get_params(self, aperture: ApertureInstance) -> dict[str, float | str]:
        """Extrai parâmetro macro_name."""
        macro_name = aperture.params.get("macro_name")
        if macro_name is None:
            raise ValueError("Macro aperture missing 'macro_name' parameter")

        if not isinstance(macro_name, str):
            raise ValueError(f"macro_name must be string, got: {type(macro_name)}")

        return {"macro_name": macro_name}


class RegionRenderer(ApertureRenderer):
    """
    Renderizador para regiões G36/G37 (kind="region").

    Gerber Specification:
        - Códigos: G36 (início), G37 (fim)
        - Parâmetros: Nenhum (região definida por contorno)
        - Geometria: Polígono arbitrário definido por movimentos D01/D02

    Regions são renderizadas diretamente pelo parser, não por aperture.
    Este renderizador é usado apenas para completude do Strategy Pattern.

    Example:
        >>> renderer = RegionRenderer()
        >>> polys, objs = renderer.render(polygon=[(0,0), (10,0), (10,10), (0,10), (0,0)])
        >>> polys[0]  # Polígono da região
    """

    def __init__(self) -> None:
        """Inicializa renderizador de região."""
        super().__init__()
        self._polygon: list[Point] | None = None

    def set_polygon(self, polygon: list[Point]) -> None:
        """
        Define polígono da região.

        Args:
            polygon: Lista de pontos (x,y) definindo contorno da região
        """
        self._polygon = polygon

    def _get_polygons(
        self,
        x_mm: float,
        y_mm: float,
        aperture: ApertureInstance,
    ) -> list[list[Point]]:
        """Retorna polígono da região (definido previamente via set_polygon)."""
        if self._polygon is None:
            raise ValueError("Region polygon not set. Call set_polygon() first.")

        if len(self._polygon) < 3:
            raise ValueError(f"Region must have at least 3 points, got: {len(self._polygon)}")

        # Retornar cópia do polígono
        return [self._polygon.copy()]

    def _get_object_kind(self) -> str:
        """Retorna 'region'."""
        return "region"

    def _get_params(self, aperture: ApertureInstance) -> dict[str, float | str]:
        """Regiões não têm parâmetros de aperture."""
        return {}


def create_aperture_renderer(
    aperture: ApertureInstance,
    macros: dict[str, ApertureMacro] | None = None,
) -> ApertureRenderer | None:
    """
    Factory Function: Cria renderizador apropriado baseado no tipo de aperture.

    Esta função elimina cadeias if/elif/else no parser, retornando o
    renderizador correto baseado no campo aperture.kind.

    Tipos suportados:
        - "circle" → CircleRenderer
        - "rect" → RectangleRenderer
        - "oval" → ObroundRenderer
        - "macro" → MacroRenderer
        - "region" → RegionRenderer

    Args:
        aperture: Instância de aperture a renderizar
        macros: Dicionário de macros (necessário para MacroRenderer)

    Returns:
        Instância de ApertureRenderer apropriada ou None se tipo não suportado

    Example:
        >>> aperture = ApertureInstance(kind="circle", params={"dia_mm": 1.5}, ...)
        >>> renderer = create_aperture_renderer(aperture)
        >>> if renderer is None:
        ...     raise ValueError(f"Unsupported aperture kind: {aperture.kind}")
        >>>
        >>> polys, objs = renderer.render(x_mm=0.0, y_mm=0.0, dcode=10, aperture=aperture)
    """
    renderer_map: dict[str, type[ApertureRenderer]] = {
        "circle": CircleRenderer,
        "rect": RectangleRenderer,
        "oval": ObroundRenderer,
        "macro": MacroRenderer,
        "region": RegionRenderer,
    }

    renderer_class = renderer_map.get(aperture.kind)
    if renderer_class is None:
        logger.warning(f"⚠️ Unsupported aperture kind: {aperture.kind}")
        return None

    renderer = renderer_class()

    # Configurar renderizadores que precisam de contexto adicional
    if aperture.kind == "macro":
        if macros is None:
            logger.error("❌ MacroRenderer requires macros dictionary")
            return None
        macro_renderer = renderer
        assert isinstance(macro_renderer, MacroRenderer)
        macro_renderer.set_macros(macros)

    return renderer
