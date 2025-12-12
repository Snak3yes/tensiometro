from __future__ import annotations

from typing import List, Tuple

from PIL import Image, ImageDraw


def render_polys_to_image(
    polys: List[List[Tuple[float, float]]],
    img_size: tuple[int, int] = (500, 500),
    margin: int = 20,
    fill="black",
    bg="white",
) -> Image.Image:
    """
    Constrói um objeto PIL.Image a partir da lista de polígonos.
    """
    # Extrai todos os X e Y para determinar bounds
    xs = [pt[0] for poly in polys for pt in poly]
    ys = [pt[1] for poly in polys for pt in poly]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)

    # Tamanho do “mundo”
    w_world = maxx - minx
    h_world = maxy - miny
    if w_world == 0 or h_world == 0:
        raise RuntimeError("Polígonos degenerados")

    # Fator de escala para caber na imagem (mantendo aspecto)
    scale_x = (img_size[0] - 2 * margin) / w_world
    scale_y = (img_size[1] - 2 * margin) / h_world
    scale = min(scale_x, scale_y)

    # Cria imagem
    img = Image.new("RGB", img_size, bg)
    draw = ImageDraw.Draw(img)

    # Desenha cada polígono, invertendo Y para o sistema de imagem
    for poly in polys:
        pts = []
        for x, y in poly:
            xx = (x - minx) * scale + margin
            yy = img_size[1] - ((y - miny) * scale + margin)
            pts.append((xx, yy))
        draw.polygon(pts, fill=fill)

    return img


def draw_polys(
    polys: List[List[tuple[float, float]]],
    filename: str = "macro.png",
    img_size: tuple[int, int] = (500, 500),
    margin: int = 20,
) -> None:
    """
    Desenha a lista de polígonos em um PNG.
    """
    img = render_polys_to_image(polys, img_size=img_size, margin=margin)
    img.save(filename)
    print(f"Imagem salva em: {filename}")
