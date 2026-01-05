from __future__ import annotations

import math
from typing import Dict, List

from .config import GerberConfig
from .constants import INCH_TO_MM


class ApertureMacro:
    def __init__(self, name: str):
        self.name = name
        # cada item = (code, expo, params)
        self.primitives: List[tuple[int, int, List[str]]] = []

    def add_primitive(self, code: int, expo: int, params: List[str]):
        self.primitives.append((code, expo, params))

    def render(
        self,
        scale_x: float = 1.0,
        scale_y: float = 1.0,
        rot_deg: float = 0.0,
        trans: tuple[float, float] = (0.0, 0.0),
    ) -> List[List[tuple[float, float]]]:
        """
        Retorna lista de polígonos (listas de pontos) já transformados.
        O parâmetro `trans` permite posicionar a macro em coordenadas
        do mundo (útil para flashes de stencils).
        """
        polys: List[List[tuple[float, float]]] = []
        theta = math.radians(rot_deg)
        cos_t, sin_t = math.cos(theta), math.sin(theta)

        def transform(pt: tuple[float, float]) -> tuple[float, float]:
            x = pt[0] * scale_x
            y = pt[1] * scale_y
            # rotaciona
            xr = x * cos_t - y * sin_t
            yr = x * sin_t + y * cos_t
            # translada
            return (xr + trans[0], yr + trans[1])

        for code, expo, p in self.primitives:
            if code == 4:  # outline
                n = int(p[0])
                coords: List[tuple[float, float]] = []
                for i in range(n):
                    x = float(p[1 + 2 * i])
                    y = float(p[1 + 2 * i + 1])
                    coords.append(transform((x, y)))
                if expo == 1 and coords:
                    polys.append(coords + [coords[0]])  # fecha explicitamente
        return polys


def parse_macro(lines: List[str]) -> ApertureMacro:
    """
    Recebe lista de linhas entre %AM…* e % e devolve ApertureMacro.

    Args:
        lines: Lista de linhas do arquivo Gerber contendo a definição da macro

    Returns:
        ApertureMacro com os primitivos parseados

    Raises:
        ValueError: Se a definição da macro for inválida ou estiver malformada
    """
    if not lines:
        raise ValueError("Macro definition is empty")

    header = lines[0].strip()  # ex: "%AMacap0165_180*"

    # Valida formato do cabeçalho
    if not header.startswith("%AM"):
        raise ValueError(f"Invalid macro header: must start with '%AM', got: {header}")
    if not header.endswith("*"):
        raise ValueError(f"Invalid macro header: must end with '*', got: {header}")

    # Extrai nome da macro (entre "%AM" e o último "*")
    name = header[3:-1].strip()
    if not name:
        raise ValueError("Macro name is empty")

    mac = ApertureMacro(name)

    # Junta só as linhas que NÃO são o "%" final
    body = "".join(l for l in lines[1:] if l.strip() != '%')

    # Extrai apenas primitivas válidas (começam com dígito)
    prims = [
        s.strip()
        for s in body.split('*')
        if s.strip() and s.strip()[0].isdigit()
    ]

    # Parse cada primitiva
    for prim in prims:
        tokens = prim.split(',')
        if len(tokens) < 2:
            continue  # ignora primitivas malformadas silenciosamente

        try:
            code = int(tokens[0])
            expo = int(tokens[1])
            params = tokens[2:]
            mac.add_primitive(code, expo, params)
        except (ValueError, IndexError) as e:
            # Log warning mas continua parsing
            import warnings
            warnings.warn(f"Failed to parse macro primitive in '{name}': {e}")

    return mac


def parse_all_macros(gerber_lines: List[str]) -> Dict[str, ApertureMacro]:
    """
    Varre o arquivo Gerber linha a linha e extrai todos os blocos de macro:
      %AMnome*
        ...
      %
    ou o formato clássico:
      %AMnome*
        ...
      ...0.00000*%

    Args:
        gerber_lines: Linhas do arquivo Gerber

    Returns:
        Dicionário mapeando nome da macro → ApertureMacro
    """
    if not gerber_lines:
        return {}

    macros: Dict[str, ApertureMacro] = {}
    i = 0
    n = len(gerber_lines)

    while i < n:
        line = gerber_lines[i].strip()
        if line.startswith("%AM"):
            block = [line]
            i += 1
            while (
                i < n
                and gerber_lines[i].strip() != "%"
                and not gerber_lines[i].strip().endswith("*%")
            ):
                block.append(gerber_lines[i].rstrip("\n"))
                i += 1

            if i < n:
                block.append(gerber_lines[i].rstrip("\n"))

            try:
                macro = parse_macro(block)
                macros[macro.name] = macro
            except (ValueError, IndexError) as e:
                # Avisa mas continua parsing de outras macros
                import warnings
                warnings.warn(f"Failed to parse macro at line {i}: {e}")

        i += 1

    return macros


class ApertureInstance:
    """
    Representa uma abertura associada a um D-code, após o parsing de %ADD...%:

      - kind:
          "circle" → círculo simples (C,diam)
          "rect"   → retângulo (R,WxH)
          "oval"   → oval/obround (O,WxH)
          "macro"  → macro Gerber (%AMxxx*)

      - params: dicionário com parâmetros em MILÍMETROS (para shapes simples)
                ou dados da macro (nome, rotação, escala, ...).
    """
    def __init__(self, kind: str, **params):
        self.kind = kind
        self.params = params


def _text_to_mm(val: str, cfg: GerberConfig) -> float:
    """Converte um valor numérico do ADD (diâmetros, larguras, etc.) para mm."""
    v = float(val)
    if cfg.unit == "inch":
        return v * INCH_TO_MM
    return v


def parse_add(
    gerber_lines: List[str],
    cfg: GerberConfig,
) -> Dict[int, ApertureInstance]:
    """
    Analisa todas as declarações %ADD...% e constrói um mapa:
        dcode (int) -> ApertureInstance
    """
    apertures: Dict[int, ApertureInstance] = {}

    for raw in gerber_lines:
        line = raw.strip()
        if not line.startswith("%ADD"):
            continue

        # remove delimitadores iniciais/finais
        s = line.strip("%").rstrip("*")
        # agora s é algo como "ADD10C,0.00100" ou "ADD102acap0150_90"
        if not s.startswith("ADD"):
            continue
        s = s[3:]  # remove "ADD"

        # dcode = sequência inicial de dígitos
        i = 0
        while i < len(s) and s[i].isdigit():
            i += 1
        if i == 0:
            continue

        dcode = int(s[:i])
        rest = s[i:]  # restante: tipo + parâmetros ou nome de macro

        if not rest:
            continue

        # Shape simples: C, R ou O
        if rest[0] in ("C", "R", "O"):
            shape_type = rest[0]
            params_str = rest[1:]  # ex: ",0.02000" ou ",0.02000X0.01400"
            if params_str.startswith(","):
                params_str = params_str[1:]

            if "X" in params_str:
                a_str, b_str = params_str.split("X", 1)
            else:
                a_str, b_str = params_str, None

            if shape_type == "C":
                dia_mm = _text_to_mm(a_str, cfg)
                apertures[dcode] = ApertureInstance("circle", dia_mm=dia_mm)
            elif shape_type == "R":
                if b_str is None:
                    continue
                w_mm = _text_to_mm(a_str, cfg)
                h_mm = _text_to_mm(b_str, cfg)
                apertures[dcode] = ApertureInstance(
                    "rect",
                    width_mm=w_mm,
                    height_mm=h_mm,
                )
            elif shape_type == "O":
                if b_str is None:
                    continue
                w_mm = _text_to_mm(a_str, cfg)
                h_mm = _text_to_mm(b_str, cfg)
                apertures[dcode] = ApertureInstance(
                    "oval",
                    width_mm=w_mm,
                    height_mm=h_mm,
                )
        else:
            # Macro: o restante é o nome da macro (ex.: "acap0150_90")
            macro_name = rest
            apertures[dcode] = ApertureInstance("macro", macro_name=macro_name)

    return apertures
