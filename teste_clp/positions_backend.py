from __future__ import annotations
import json
from pathlib import Path
from typing import List

from program_io_widget import ProgramStorageBackend      # protocolo
from inspection_positions_widget import (
    InspectionPositionsWidget, InspectionPosition
)


class InspectionPositionsBackend(ProgramStorageBackend):
    """
    Backend que salva/carrega a lista de InspectionPosition em JSON.
    Estrutura gravada:
      [
        {"name":"1", "x":123, "y2":456, "y1":777, "z":0},
        ...
      ]
    """
    def __init__(self, widget: InspectionPositionsWidget):
        self._widget = widget

    # ---------------- ProgramStorageBackend --------------------------
    def save_to_file(self, filename: str) -> bool:
        data = [
            {
                "name": p.name,
                "x":   p.x,
                "y2":  p.y2,
                "y1":  p.y1,
                "z":   p.z,
                "meta": p.meta or {}
            }
            for p in self._widget.positions()
        ]
        Path(filename).write_text(json.dumps(data, indent=2),
                                  encoding="utf-8")
        return True

    def load_from_file(self, filename: str) -> bool:
        raw = json.loads(Path(filename).read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            raise ValueError("formato inválido – era esperado uma lista JSON")

        self._widget.clear()
        for d in raw:
            pos = InspectionPosition(
                name=str(d.get("name", "")),
                x=float(d.get("x", 0)),
                y2=float(d.get("y2", 0)),
                y1=float(d.get("y1", 0)),
                z=float(d.get("z", 0)),
                meta=d.get("meta")
            )
            self._widget.add_position(pos)
        return True
