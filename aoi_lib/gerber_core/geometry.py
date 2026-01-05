from __future__ import annotations

import math
from typing import List


def circle_to_polys_mm(
    xc: float,
    yc: float,
    dia_mm: float,
    n_sides: int = 64,
) -> List[List[tuple[float, float]]]:
    """Aproxima um círculo por um polígono regular de n_sides lados."""
    r = dia_mm / 2.0
    pts: List[tuple[float, float]] = []
    for i in range(n_sides):
        ang = 2 * math.pi * i / n_sides
        pts.append((xc + r * math.cos(ang), yc + r * math.sin(ang)))
    if pts:
        pts.append(pts[0])
    return [pts]


def rect_to_polys_mm(
    xc: float,
    yc: float,
    w_mm: float,
    h_mm: float,
) -> List[List[tuple[float, float]]]:
    """Gera o polígono de um retângulo alinhado aos eixos, centrado em (xc, yc)."""
    hw = w_mm / 2.0
    hh = h_mm / 2.0
    pts = [
        (xc - hw, yc - hh),
        (xc + hw, yc - hh),
        (xc + hw, yc + hh),
        (xc - hw, yc + hh),
    ]
    pts.append(pts[0])
    return [pts]


def oval_to_polys_mm(
    xc: float,
    yc: float,
    w_mm: float,
    h_mm: float,
    n_sides: int = 64,
) -> List[List[tuple[float, float]]]:
    """
    Aproxima uma abertura OVAL (obround) por uma elipse de eixos w_mm x h_mm.
    Não é exatamente a construção "retângulo + semi-círculos", mas costuma
    ser suficiente para visualização / máscara raster.
    """
    a = w_mm / 2.0
    b = h_mm / 2.0
    pts: List[tuple[float, float]] = []
    for i in range(n_sides):
        ang = 2 * math.pi * i / n_sides
        pts.append((xc + a * math.cos(ang), yc + b * math.sin(ang)))
    if pts:
        pts.append(pts[0])
    return [pts]
