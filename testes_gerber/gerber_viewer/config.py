from __future__ import annotations

from typing import List

from .constants import INCH_TO_MM


class GerberConfig:
    """
    Configuração básica do arquivo Gerber:
      - unidade (inch/mm)
      - formato de coordenadas (número de dígitos inteiros e decimais)
    Ex.: %FSLAX26Y26*% → int=2, dec=6, unidade = polegadas (MOIN).
    """
    def __init__(self, unit: str = "inch", fmt_int: int = 2, fmt_dec: int = 6):
        self.unit = unit          # "inch" ou "mm"
        self.fmt_int = fmt_int    # dígitos inteiros
        self.fmt_dec = fmt_dec    # dígitos decimais


def parse_gerber_config(gerber_lines: List[str]) -> GerberConfig:
    """
    Lê o cabeçalho do Gerber e retorna unidade e formato de coordenadas.
    Procura por:
      - %FS...*  → formato (ex.: %FSLAX26Y26*%)
      - %MO...*  → unidade (MOIN/MOMM)
    """
    cfg = GerberConfig()

    for line in gerber_lines:
        s = line.strip()
        if s.startswith("%FS"):
            # Exemplo: %FSLAX26Y26*%
            content = s.strip("%*")  # "FSLAX26Y26"
            if "X" in content and "Y" in content:
                ix = content.index("X")
                iy = content.index("Y")
                xfmt = content[ix + 1:iy]  # "26"
                if len(xfmt) >= 2 and xfmt[0].isdigit() and xfmt[1].isdigit():
                    cfg.fmt_int = int(xfmt[0])
                    cfg.fmt_dec = int(xfmt[1])
        elif s.startswith("%MO"):
            up = s.upper()
            if "MOIN" in up:
                cfg.unit = "inch"
            elif "MOMM" in up:
                cfg.unit = "mm"

    return cfg


def parse_coord(val_str: str, cfg: GerberConfig) -> float:
    """
    Converte uma string de coordenada Gerber (sem ponto) em valor numérico
    na unidade base do arquivo (inch ou mm), considerando formato FS
    (número de dígitos inteiros e decimais) e zero suppression 'L' (leading).
    """
    s = val_str.strip()
    if not s:
        return 0.0

    sign = -1 if s[0] == "-" else 1
    if s[0] in "+-":
        s = s[1:]

    total_len = cfg.fmt_int + cfg.fmt_dec
    # leading zero suppression → faz left-pad até o tamanho esperado
    s = s.rjust(total_len, "0")

    int_part = int(s[:cfg.fmt_int])
    dec_part = int(s[cfg.fmt_int:]) / (10 ** cfg.fmt_dec)
    return sign * (int_part + dec_part)


def to_mm_from_unit(v: float, cfg: GerberConfig) -> float:
    """Converte um valor na unidade do arquivo (inch/mm) para mm."""
    if cfg.unit == "inch":
        return v * INCH_TO_MM
    return v
