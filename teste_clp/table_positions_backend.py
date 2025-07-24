# table_positions_backend.py
"""
Backend de persistência específico das mesas.
Grava apenas X, Y (físico da mesa) e Z em JSON.
Extensões   Mesa 1 → *.m1
            Mesa 2 → *.m2
"""
from pathlib import Path
from typing import List

from program_io_widget         import ProgramStorageBackend
from inspection_positions_widget import InspectionPositionsWidget, InspectionPosition
from adhesive_program_manager import AdhesiveProgramManager
import os, copy, json, cv2, numpy as np
from PIL import Image



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
        # ------------------------------------------------------------------
        #  EXTRA 1 ‑ gera estrutura de pastas + salva imagens (.png)
        # ------------------------------------------------------------------
        try:
            prog_name = Path(filename).stem
            base_dir  = Path(filename).parent
            mgr = AdhesiveProgramManager(base_dir)
            try:
                mgr.create_program(prog_name, overwrite=False)
            except FileExistsError:
                mgr.model_dir = Path(base_dir) / "modelos" / prog_name

            # percorre pontos para salvar imagens
            for idx, p in enumerate(self._w.positions(), 1):
                meta = p.meta or {}
                if meta.get("action") != "inspect":
                    continue

                # ---------------- imagem da REGIÃO -----------------
                regiao_name = f"regiao_{idx}"
                region_bytes = meta.get("_region_png")
                if not region_bytes:
                    continue
                np_img      = cv2.imdecode(np.frombuffer(region_bytes, np.uint8),
                                           cv2.IMREAD_COLOR)
                if np_img is None:
                    continue
                region_pil  = Image.fromarray(cv2.cvtColor(np_img,
                                                           cv2.COLOR_BGR2RGB))
                mgr.save_region(regiao_name, region_pil)
                # ---------------- janelas w* -----------------------
                componentes = meta.get("componentes", {})
                for posicao_nome, comp_data in componentes.items():
                    for insp in comp_data.get("inspecoes", []):
                        x, y   = insp.get("posicao", (0, 0))
                        w, h   = insp.get("tamanho", (0, 0))
                        roi    = np_img[y:y+h, x:x+w]
                        if roi.size == 0:
                            continue
                        roi_pil = Image.fromarray(cv2.cvtColor(roi,
                                                               cv2.COLOR_BGR2RGB))
                        w_nome  = insp.get("nome", "w?")
                        meta_js = {
                            "janela_azul": (x, y, w, h),
                            "similaridade": insp.get("similaridade", 0.9)
                        }
                        mgr.save_blue_reference(regiao_name,
                                                posicao_nome,
                                                w_nome,
                                                roi_pil,
                                                meta_js)

        except Exception as exc:
            print("[WARN] Falha ao salvar imagens de inspeção:", exc)

        # ------------------------------------------------------------------
        #  EXTRA 2 ‑ remove chaves temporárias antes de serializar JSON
        # ------------------------------------------------------------------
        json_ready: List[dict] = []
        for p in self._w.positions():
            y = p.y1 if self._y_axis == 'Y1' else p.y2
            m = copy.deepcopy(p.meta or {})
            if m.get("action") == "inspect":
                # descarta payload binário antes do JSON
                m.pop("_region_png", None)
            json_ready.append({
                "name": p.name,
                "x":    p.x,
                "y":    y,
                "z":    p.z,
                "meta": m
            })

        Path(filename).write_text(json.dumps(json_ready, indent=2), 'utf-8')

        # ------------------------------------------------------------------
        #  EXTRA 3 ‑ apenas garante árvore vazia quando não havia w*
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
