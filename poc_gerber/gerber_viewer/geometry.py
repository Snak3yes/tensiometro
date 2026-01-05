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
    n_sides: int = 32,
) -> List[List[tuple[float, float]]]:
    """
    Gera um obround correto conforme o padrão Gerber: retângulo + semi-círculos.

    Se w > h: forma horizontal (retângulo no centro + semi-círculos esquerda/direita)
    Se h > w: forma vertical (retângulo no centro + semi-círculos cima/baixo)
    Se w == h: reduz para um círculo

    Args:
        xc: Coordenada X do centro em mm
        yc: Coordenada Y do centro em mm
        w_mm: Largura total em mm
        h_mm: Altura total em mm
        n_sides: Número de pontos por semi-círculo (padrão: 32)

    Returns:
        Lista contendo um polígono fechado
    """
    pts: List[tuple[float, float]] = []

    # Caso especial: círculo
    if abs(w_mm - h_mm) < 1e-6:
        return circle_to_polys_mm(xc, yc, w_mm, n_sides=n_sides * 2)

    if w_mm > h_mm:
        # Horizontal: retângulo no centro, semi-círculos nas pontas esquerda/direita
        radius = h_mm / 2.0
        rect_width = w_mm - h_mm  # largura do retângulo central
        half_rect = rect_width / 2.0

        # Semi-círculo esquerdo (180° a 0°, sentido anti-horário)
        for i in range(n_sides // 2 + 1):
            ang = math.pi - (math.pi * i / (n_sides // 2))
            x = xc - half_rect + radius * math.cos(ang)
            y = yc + radius * math.sin(ang)
            pts.append((x, y))

        # Semi-círculo direito (0° a -180°, sentido anti-horário)
        for i in range(n_sides // 2 + 1):
            ang = -math.pi * i / (n_sides // 2)
            x = xc + half_rect + radius * math.cos(ang)
            y = yc + radius * math.sin(ang)
            pts.append((x, y))
    else:
        # Vertical: retângulo no centro, semi-círculos em cima/baixo
        radius = w_mm / 2.0
        rect_height = h_mm - w_mm  # altura do retângulo central
        half_rect = rect_height / 2.0

        # Semi-círculo inferior (90° a 270°, sentido anti-horário)
        for i in range(n_sides // 2 + 1):
            ang = math.pi / 2 + math.pi * i / (n_sides // 2)
            x = xc + radius * math.cos(ang)
            y = yc - half_rect + radius * math.sin(ang)
            pts.append((x, y))

        # Semi-círculo superior (270° a 90°, sentido anti-horário)
        for i in range(n_sides // 2 + 1):
            ang = 3 * math.pi / 2 + math.pi * i / (n_sides // 2)
            x = xc + radius * math.cos(ang)
            y = yc + half_rect + radius * math.sin(ang)
            pts.append((x, y))

    # Fecha o polígono explicitamente
    if pts and pts[0] != pts[-1]:
        pts.append(pts[0])

    return [pts]
