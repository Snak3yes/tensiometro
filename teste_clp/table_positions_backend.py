# table_positions_backend.py
"""
Backend de persistência específico das mesas.
Grava apenas X, Y (físico da mesa) e Z em JSON.
Extensões   Mesa 1 → *.m1
            Mesa 2 → *.m2
"""
from pathlib import Path
import json
from typing import List

from program_io_widget         import ProgramStorageBackend
from inspection_positions_widget import InspectionPositionsWidget, InspectionPosition


class TablePositionsBackend(ProgramStorageBackend):
    def __init__(self,
                 widget: InspectionPositionsWidget,
                 y_axis: str):                     # 'Y1' ou 'Y2'
        self._w = widget
        assert y_axis in ('Y1', 'Y2')
        self._y_axis = y_axis

    # ------------------ salvar ------------------
    def save_to_file(self, filename: str) -> bool:
        data: List[dict] = []
        for p in self._w.positions():
            y = p.y1 if self._y_axis == 'Y1' else p.y2
            data.append({"name": p.name,
                         "x":   p.x,
                         "y":   y,
                         "z":   p.z,
                         "meta": p.meta or {}})
        Path(filename).write_text(json.dumps(data, indent=2), 'utf-8')
        return True

    # ------------------ carregar ----------------
    def load_from_file(self, filename: str) -> bool:
        raw = json.loads(Path(filename).read_text('utf-8'))
        if not isinstance(raw, list):
            raise ValueError("formato inválido – esperada lista JSON")

        self._w.clear()
        for d in raw:
            y_val = float(d.get("y", 0))
            pos = InspectionPosition(
                name=str(d.get("name", "")),
                x=float(d.get("x", 0)),
                y1=y_val if self._y_axis == 'Y1' else 0.0,
                y2=y_val if self._y_axis == 'Y2' else 0.0,
                z=float(d.get("z", 0)),
                meta=d.get("meta")
            )
            self._w.add_position(pos)
        return True
