from dataclasses import dataclass
from typing import List, Dict
from pathlib import Path

@dataclass
class MapParams:
    """Parâmetros para geração de mapa."""
    origin: dict
    end: dict
    step_x: float
    step_y: float
    folder: str
    program_name: str




