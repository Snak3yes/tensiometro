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
from adhesive_program_manager import AdhesiveProgramManager
import os


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

        # ------------------------------------------------------------------
        #  NOVO: cria estrutura /modelos/<prog>/regioes/... sempre que
        #        existir pelo menos um ponto com ação = 'inspect'.
        # ------------------------------------------------------------------
        try:
            # Nome do programa = nome do arquivo sem extensão
            prog_name = Path(filename).stem
            # Raiz = mesma pasta do *.m?  (mantém simples)
            base_dir  = Path(filename).parent
            mgr = AdhesiveProgramManager(base_dir)
            # Se já existir não apaga – somente garante estrutura
            try:
                mgr.create_program(prog_name, overwrite=False)
            except FileExistsError:
                mgr.model_dir = Path(base_dir) / "modelos" / prog_name

            for idx, p in enumerate(self._w.positions(), 1):
                meta = p.meta or {}
                if meta.get("action") != "inspect":
                    continue
                componentes : dict = meta.get("componentes", {})
                if not componentes:
                    continue

                # Cada posição de inspeção recebe uma pasta “regiao_<n>”
                regiao = f"regiao_{idx}"
                for comp_name, comp_data in componentes.items():
                    inspecoes = comp_data.get("inspecoes", [])
                    # Cria sub-pastas w1, w2…
                    for i in range(max(1, len(inspecoes))):
                        w_name = f"w{i+1}"
                        mgr.ensure_position_dirs(regiao, comp_name, w_name)
        except Exception as exc:
            # não falha a gravação do programa se a estrutura de pastas
            # não puder ser criada (por exemplo, permissão)
            print("[WARN] Falha ao preparar pasta de inspeção:", exc)

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
