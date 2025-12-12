from __future__ import annotations

import math

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

from .apertures import ApertureInstance, ApertureMacro
from .config import GerberConfig, parse_coord, to_mm_from_unit
from .geometry import (
    circle_to_polys_mm,
    rect_to_polys_mm,
    oval_to_polys_mm,
)

Point = Tuple[float, float]


@dataclass
class GerberObject:
    """
    Representa um elemento geométrico já interpretado do Gerber, em mm:

      - kind:
          "flash_circle", "flash_rect", "flash_oval", "flash_macro", "region"
      - dcode:
          D-code ativo no momento do flash (ou None para regiões)
      - x_mm, y_mm:
          posição do flash (para regiões pode ser None ou centro aproximado)
      - params:
          dicionário com parâmetros geométricos (ex.: dia_mm, width_mm, etc.)
      - polygon_mm:
          lista de pontos (x,y) em mm, já fechada (primeiro == último).
    """
    id: int
    kind: str
    dcode: Optional[int]
    x_mm: Optional[float]
    y_mm: Optional[float]
    params: Dict[str, float | str]
    polygon_mm: List[Point]


def _parse_xy_from_line(line: str) -> tuple[str | None, str | None]:
    """Extrai substrings de X e Y de uma linha Gerber (sem interpretá-las)."""
    x_str = None
    y_str = None
    if "X" in line:
        i = line.index("X") + 1
        j = i
        while j < len(line) and line[j] in "+-0123456789":
            j += 1
        x_str = line[i:j]
    if "Y" in line:
        i = line.index("Y") + 1
        j = i
        while j < len(line) and line[j] in "+-0123456789":
            j += 1
        y_str = line[i:j]
    return x_str, y_str


def gerber_to_records(gerber_lines: List[str]) -> List[str]:
    """
    Converte a lista de linhas do arquivo Gerber em uma lista de
    "registros" separados por '*', como definido no padrão RS-274X.
    """
    text = ""
    for line in gerber_lines:
        s = line.strip()
        if not s:
            continue
        text += s

    parts = text.split("*")
    records: List[str] = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        records.append(p + "*")
    return records


def _get_draw_mode(record: str) -> str | None:
    """
    Retorna o modo de desenho (D01/D02/D03) de um registro, aceitando
    tanto D01/D02/D03 quanto D1/D2/D3.
    """
    if "D" not in record:
        return None
    idx = record.rfind("D")
    if idx == -1:
        return None
    j = idx + 1
    num = ""
    while j < len(record) and record[j].isdigit():
        num += record[j]
        j += 1
    if not num:
        return None

    if num in ("1", "01"):
        return "D01"
    if num in ("2", "02"):
        return "D02"
    if num in ("3", "03"):
        return "D03"
    return None


def _parse_ij_from_record(record: str) -> tuple[str | None, str | None]:
    """Extrai substrings de I e J (centro relativo de arco) de um registro."""
    i_str = None
    j_str = None
    if "I" in record:
        k = record.index("I") + 1
        j = k
        while j < len(record) and j < len(record) and record[j] in "+-0123456789":
            j += 1
        i_str = record[k:j]
    if "J" in record:
        k = record.index("J") + 1
        j = k
        while j < len(record) and record[j] in "+-0123456789":
            j += 1
        j_str = record[k:j]
    return i_str, j_str


def _get_g_code(record: str) -> int | None:
    """
    Extrai o código G (2, 3, 36, 37, etc.) de um registro.
    Retorna um inteiro (por ex. 2 para G02, 3 para G03) ou None.
    """
    s = record.lstrip()
    if "G" not in s:
        return None
    idx = s.index("G") + 1
    j = idx
    digits = ""
    while j < len(s) and s[j].isdigit():
        digits += s[j]
        j += 1
    if not digits:
        return None
    try:
        return int(digits)
    except ValueError:
        return None


def _approx_arc_points(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    cx: float,
    cy: float,
    ccw: bool,
    max_seg_deg: float = 5.0,
) -> List[tuple[float, float]]:
    """
    Aproxima um arco circular (G02/G03) por uma sequência de pontos.

    - ccw = True  → arco anti‑horário (G03)
    - ccw = False → arco horário (G02)

    Retorna pontos **sem** o ponto inicial (x0,y0), e **com** o ponto final
    (x1,y1). O chamador deve garantir que já possui (x0,y0).
    """
    r0 = math.hypot(x0 - cx, y0 - cy)
    r1 = math.hypot(x1 - cx, y1 - cy)
    r = (r0 + r1) / 2.0 if (r0 > 0 and r1 > 0) else max(r0, r1)
    if r == 0:
        return [(x1, y1)]

    a0 = math.atan2(y0 - cy, x0 - cx)
    a1 = math.atan2(y1 - cy, x1 - cx)
    if ccw:
        if a1 <= a0:
            a1 += 2.0 * math.pi
    else:
        if a1 >= a0:
            a1 -= 2.0 * math.pi

    sweep = a1 - a0
    max_seg_rad = max_seg_deg * math.pi / 180.0
    n_seg = max(4, int(math.ceil(abs(sweep) / max_seg_rad)))

    pts: List[tuple[float, float]] = []
    for k in range(1, n_seg + 1):
        t = a0 + sweep * (k / n_seg)
        x = cx + r * math.cos(t)
        y = cy + r * math.sin(t)
        pts.append((x, y))
    return pts


def _build_layer_core_mm(
    gerber_lines: List[str],
    macros: Dict[str, ApertureMacro],
    apertures: Dict[int, ApertureInstance],
    cfg: GerberConfig,
) -> Tuple[List[List[Point]], List[GerberObject]]:
    """
    Núcleo comum:
      - interpreta o Gerber e gera
        (lista de polígonos, lista de GerberObject).
    """
    """
    Percorre o arquivo Gerber inteiro e retorna uma lista de polígonos
    em coordenadas absolutas **em milímetros**, combinando:
      - flashes D03 (pads instanciados via aperturas e macros)
      - regiões G36/G37 (polígonos sólidos)
    """
    all_polys: List[List[Point]] = []
    all_objects: List[GerberObject] = []

    current_dcode: int | None = None
    last_draw_mode: str | None = None  # "D01", "D02", "D03"
    current_g: int | None = None       # último G de interpolação (1,2,3)
    cur_x_mm: float | None = None
    cur_y_mm: float | None = None

    region_active = False
    region_pts: List[tuple[float, float]] = []

    

    def coord_to_mm(v_base: float) -> float:
        return to_mm_from_unit(v_base, cfg)

    # Converte texto em registros separados por '*'
    records = gerber_to_records(gerber_lines)

    for rec in records:
        line = rec.strip()
        if not line:
            continue

        # Comentários e comandos de configuração são ignorados aqui
        if line.startswith("G04") or line.startswith("%"):
            continue

        # Atualiza G-code atual (modo de interpolação) quando aparece
        g_tmp = _get_g_code(line)
        if g_tmp in (1, 2, 3):  # G01, G02, G03
            current_g = g_tmp

        # Início/fim de região (G36/G37)
        if "G36*" in line:
            region_active = True
            region_pts = []
            
            continue
        if "G37*" in line:
            if region_active and len(region_pts) > 1:
                if region_pts[0] != region_pts[-1]:
                    region_pts.append(region_pts[0])
                poly = region_pts.copy()
                
                all_polys.append(poly)

                # Cria objeto de região
                try:
                    xs = [p[0] for p in poly]
                    ys = [p[1] for p in poly]
                    cx = (min(xs) + max(xs)) / 2.0
                    cy = (min(ys) + max(ys)) / 2.0
                except Exception:
                    cx = cy = None

                obj = GerberObject(
                    id=len(all_objects),
                    kind="region",
                    dcode=None,
                    x_mm=cx,
                    y_mm=cy,
                    params={},
                    polygon_mm=poly,
                )
                all_objects.append(obj)
            region_active = False
            region_pts = []
            continue

        # Seleção de D-code: G54Dnn* ou Dnn* sozinho (sem X/Y)
        if line.startswith("G54D"):
            idx = line.index("D") + 1
            j = idx
            while j < len(line) and line[j].isdigit():
                j += 1
            if j > idx:
                current_dcode = int(line[idx:j])
            continue
        if (
            line.startswith("D")
            and "X" not in line
            and "Y" not in line
        ):
            idx = 1
            j = idx
            while j < len(line) and line[j].isdigit():
                j += 1
            if j > idx:
                current_dcode = int(line[idx:j])
            continue

        # Determina o modo de desenho atual (D01/D02/D03), aceitando D1/D2/D3
        draw_mode = _get_draw_mode(line)
        if draw_mode is not None:
            last_draw_mode = draw_mode
        else:
            draw_mode = last_draw_mode

        # Guarda posição anterior antes de atualizar
        prev_x_mm, prev_y_mm = cur_x_mm, cur_y_mm

        # Atualiza coordenadas X/Y (em mm)
        x_str, y_str = _parse_xy_from_line(line)
        if x_str is not None:
            base_x = parse_coord(x_str, cfg)
            cur_x_mm = coord_to_mm(base_x)
        if y_str is not None:
            base_y = parse_coord(y_str, cfg)
            cur_y_mm = coord_to_mm(base_y)

        # Se não temos ainda coordenadas válidas, não há o que fazer
        if cur_x_mm is None or cur_y_mm is None:
            continue

        # Tratamento de regiões (G36/G37)
        if region_active:
            g_code = current_g
            is_arc = g_code in (2, 3)  # G02 (CW) ou G03 (CCW)

            if draw_mode == "D02":
                region_pts = [(cur_x_mm, cur_y_mm)]
            elif draw_mode == "D01":
                if not region_pts:
                    region_pts = [(cur_x_mm, cur_y_mm)]
                else:
                    if is_arc:
                        start_x, start_y = region_pts[-1]
                        i_str, j_str = _parse_ij_from_record(line)
                        if i_str is not None or j_str is not None:
                            i_base = parse_coord(i_str, cfg) if i_str else 0.0
                            j_base = parse_coord(j_str, cfg) if j_str else 0.0
                            i_mm = coord_to_mm(i_base)
                            j_mm = coord_to_mm(j_base)
                            cx = start_x + i_mm
                            cy = start_y + j_mm
                            ccw = (g_code == 3)
                            arc_pts = _approx_arc_points(
                                start_x, start_y,
                                cur_x_mm, cur_y_mm,
                                cx, cy,
                                ccw=ccw,
                            )
                            region_pts.extend(arc_pts)
                        else:
                            region_pts.append((cur_x_mm, cur_y_mm))
                    else:
                        region_pts.append((cur_x_mm, cur_y_mm))
            continue

        # Flashes D03 (pads / furos do stencil)
        if draw_mode == "D03" and current_dcode is not None:
            ap = apertures.get(current_dcode)
            if ap is None:
                continue

            if ap.kind == "circle":
                dia_mm = float(ap.params["dia_mm"])
                polys = circle_to_polys_mm(cur_x_mm, cur_y_mm, dia_mm)
                for poly in polys:
                    all_polys.append(poly)
                    obj = GerberObject(
                        id=len(all_objects),
                        kind="flash_circle",
                        dcode=current_dcode,
                        x_mm=cur_x_mm,
                        y_mm=cur_y_mm,
                        params={"dia_mm": dia_mm},
                        polygon_mm=poly,
                    )
                    all_objects.append(obj)
            elif ap.kind == "rect":
                w_mm = float(ap.params["width_mm"])
                h_mm = float(ap.params["height_mm"])
                polys = rect_to_polys_mm(cur_x_mm, cur_y_mm, w_mm, h_mm)
                for poly in polys:
                    all_polys.append(poly)
                    obj = GerberObject(
                        id=len(all_objects),
                        kind="flash_rect",
                        dcode=current_dcode,
                        x_mm=cur_x_mm,
                        y_mm=cur_y_mm,
                        params={"width_mm": w_mm, "height_mm": h_mm},
                        polygon_mm=poly,
                    )
                    all_objects.append(obj)
            elif ap.kind == "oval":
                w_mm = float(ap.params["width_mm"])
                h_mm = float(ap.params["height_mm"])
                polys = oval_to_polys_mm(cur_x_mm, cur_y_mm, w_mm, h_mm)
                for poly in polys:
                    all_polys.append(poly)
                    obj = GerberObject(
                        id=len(all_objects),
                        kind="flash_oval",
                        dcode=current_dcode,
                        x_mm=cur_x_mm,
                        y_mm=cur_y_mm,
                        params={"width_mm": w_mm, "height_mm": h_mm},
                        polygon_mm=poly,
                    )
                    all_objects.append(obj)
            elif ap.kind == "macro":
                macro_name = ap.params.get("macro_name")
                mac = macros.get(macro_name)
                if mac is None:
                    continue
                polys = mac.render(
                    scale_x=1.0,
                    scale_y=1.0,
                    rot_deg=0.0,
                    trans=(cur_x_mm, cur_y_mm),
                )
                for poly in polys:
                    all_polys.append(poly)
                    obj = GerberObject(
                        id=len(all_objects),
                        kind="flash_macro",
                        dcode=current_dcode,
                        x_mm=cur_x_mm,
                        y_mm=cur_y_mm,
                        params={"macro_name": macro_name or ""},
                        polygon_mm=poly,
                    )
                    all_objects.append(obj)

    return all_polys, all_objects


def build_layer_polys_mm(
    gerber_lines: List[str],
    macros: Dict[str, ApertureMacro],
    apertures: Dict[int, ApertureInstance],
    cfg: GerberConfig,
) -> List[List[Point]]:
    """
    Interface antiga preservada:
      - retorna apenas a lista de polígonos em mm.
    """
    polys, _ = _build_layer_core_mm(gerber_lines, macros, apertures, cfg)
    return polys


def build_layer_objects_mm(
    gerber_lines: List[str],
    macros: Dict[str, ApertureMacro],
    apertures: Dict[int, ApertureInstance],
    cfg: GerberConfig,
) -> List[GerberObject]:
    """
    Nova interface:
      - retorna a lista de objetos Gerber (flash/região) já em mm,
        com tipo, D-code, posição, parâmetros e polígono associado.
    """
    _, objects = _build_layer_core_mm(gerber_lines, macros, apertures, cfg)
    return objects
