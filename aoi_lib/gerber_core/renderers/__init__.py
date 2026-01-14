"""
Gerber Core Renderers Package

Este pacote contém renderizadores para diferentes tipos de apertures Gerber,
seguindo o Strategy Pattern para reduzir complexidade ciclomática.

Components:
    - ApertureRenderer: Classe base abstrata
    - CircleRenderer: Renderizador para apertures circulares
    - RectangleRenderer: Renderizador para apertures retangulares
    - ObroundRenderer: Renderizador para apertures obround (oval)
    - MacroRenderer: Renderizador para apertures macro
    - RegionRenderer: Renderizador para regiões (G36/G37)
    - create_aperture_renderer: Factory Function

Example:
    >>> from aoi_lib.gerber_core.renderers import create_aperture_renderer
    >>> from aoi_lib.gerber_core.apertures import ApertureInstance
    >>>
    >>> aperture = ApertureInstance(kind="circle", params={"dia_mm": 1.5}, ...)
    >>> renderer = create_aperture_renderer(aperture)
    >>> if renderer:
    ...     polys, obj = renderer.render(x_mm=0.0, y_mm=0.0, dcode=10, aperture=aperture)
"""

from .aperture_renderer import (
    ApertureRenderer,
    CircleRenderer,
    RectangleRenderer,
    ObroundRenderer,
    MacroRenderer,
    RegionRenderer,
    create_aperture_renderer,
)

__all__ = [
    "ApertureRenderer",
    "CircleRenderer",
    "RectangleRenderer",
    "ObroundRenderer",
    "MacroRenderer",
    "RegionRenderer",
    "create_aperture_renderer",
]
