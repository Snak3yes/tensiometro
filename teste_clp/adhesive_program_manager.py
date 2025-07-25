# adhesive_program_manager.py
"""
AdhesiveProgramManager
----------------------
Cria e gerencia a estrutura de diretórios/arquivos de um
programa de inspeção da adesivadora.

Estrutura-alvo  (ver txt original):
modelos/<nome_prog>/
    ├─ logs/<datahora>_<codigo>/              (# sessões de produção)
    │     ├─ <datahora>_<codigo>.json         (log consolidado)
    │     ├─ <datahora>_SFCS.json             (opcional)
    │     └─ regiao_<n>.png                   (snapshots)
    └─ regioes/
          └─ <regiao_X>/posicoes_mecanicas/
               └─ <posicao_mec_Y>/inspecoes/
                    └─ w1/ … w4/
                         ├─ correct/          (imagens OK)
                         ├─ incorrect/        (imagens NOK)
                         ├─ <posicao_wi>.json (meta)
                         ├─ <posicao_wi>.png  (ROI azul)
                         └─ referencia/referencia.png
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib     import Path
from datetime    import datetime
import json, shutil
from typing import List, Tuple, Dict, Any, Optional
from PIL import Image

# ------------------------------------------------------------------
# 1) Tipos de dados — opcionais, mas ajudam a manter contrato
# ------------------------------------------------------------------
@dataclass
class InspectionWindowInfo:
    posicao:   Tuple[int, int]      # x,y absolutos na ROI mecânica
    tamanho:   Tuple[int, int]      # w,h absolutos
    threshold: int                 = 128
    cor_pixel: str                 = 'branco'   # 'branco'|'preto'
    percentual_minimo: float       = .80        # 0-1
    # caminho para imagens corret/incorrect ficarão no disco

@dataclass
class MechanicalPositionInfo:
    """Informações persistidas no JSON ‘<posicao>_w?.json’."""
    janela_azul:   Tuple[int,int,int,int]        # x,y,w,h
    similaridade:  float                         # 0-1
    inspecoes:     List[InspectionWindowInfo]    # w1…w4

# ------------------------------------------------------------------
# 2) Classe principal
# ------------------------------------------------------------------
class AdhesiveProgramManager:
    def __init__(self, base_dir: str | Path = ".") -> None:
        self.base_dir = Path(base_dir).resolve()
        self.model_dir: Path | None = None

    # ------------------------------------------------------------------
    #  Propriedade de compatibilidade
    #  Várias partes do código legado ainda acessam `prog_mgr.path`.
    #  Para não precisar alterar todos os módulos, expomos `.path`
    #  como alias somente-leitura para `model_dir`.
    # ------------------------------------------------------------------
    @property
    def path(self) -> Path | None:
        """
        Alias para `model_dir`.
        Retorna None até `create_program()` ser chamado.
        """
        return self.model_dir

    # --------------- criação do PROGRAMA --------------------------
    def create_program(self, name: str, overwrite: bool = True) -> Path:
        """
        Cria ou abre um programa:
            modelos/<name>  + sub-pastas vazias.
        """
        self.model_dir = self.base_dir / "modelos" / name
        if self.model_dir.exists() and not overwrite:
            raise FileExistsError(f"Programa “{name}” já existe.")

        # limpa só se overwrite=True
        if self.model_dir.exists() and overwrite:
            shutil.rmtree(self.model_dir)

        # cria tronco principal
        # sub-pastas fixas
        for sub in ("logs", "regioes", "arquivos_auxiliares"):
            (self.model_dir / sub).mkdir(parents=True, exist_ok=True)

        # grava config.txt minimal   (mesma linha de raciocínio do PM original)
        cfg_txt = self.model_dir / "config.txt"
        cfg_txt.write_text(f"model_name={name}\n"
                           f"created_at={datetime.now()}\n"
                           f"created_by=adhesive_program_manager\n",
                           encoding="utf-8")

        return self.model_dir

    # --------------- regiões / posições ---------------------------
    def ensure_position_dirs(self,
                             regiao: str,
                             posicao: str,
                             w: str) -> Path:
        """
        Garante que …/regioes/<regiao>/posicoes_mecanicas/<posicao>/inspecoes/<w>/
        exista e devolve esse Path.
        """
        if not self.model_dir:
            raise RuntimeError("create_program() ainda não foi chamado.")

        target = (self.model_dir / "regioes" / regiao /
                  "posicoes_mecanicas" / posicao /
                  "inspecoes" / w)

        # sub-pastas fixas
        for p in ("correct", "incorrect", "referencia"):
            (target / p).mkdir(parents=True, exist_ok=True)
        return target

    # --------------- salvar imagens e JSONs -----------------------
    def save_blue_reference(self,
                            regiao: str,
                            posicao: str,
                            w: str,
                            roi_pil: Image.Image,
                            meta: MechanicalPositionInfo | Dict[str,Any]):
        """
        Salva:
          • ROI azul (…/<posicao>_<w>.png)
          • JSON    (…/<posicao>_<w>.json)
          Ambos dentro de …/inspecoes/<w>/
        """
        dest = self.ensure_position_dirs(regiao, posicao, w)

        png_path  = dest / f"{posicao}_{w}.png"
        json_path = dest / f"{posicao}_{w}.json"

        # imagem
        roi_pil.save(png_path, format="PNG", compress_level=0)

        # json
        if isinstance(meta, MechanicalPositionInfo):
            meta_to_dump = asdict(meta)
        else:
            meta_to_dump = meta
        json_path.write_text(json.dumps(meta_to_dump, indent=2), "utf-8")

        # referência global (janela azul) — sobrescreve
        ref_dir = dest / "referencia"
        roi_pil.save(ref_dir / "referencia.png", format="PNG", compress_level=0)

    # ------------------------------------------------------------------
    #  NOVO: salva imagem completa da região logo que é criada
    # ------------------------------------------------------------------
    def save_region(self, regiao: str, img_pil: "Image.Image"):
        """
        Salva  regioes/<regiao>/<regiao>.png  (sobre-escreve).
        """
        if not self.model_dir:
            raise RuntimeError("create_program() ainda não foi chamado.")
        target_dir = self.model_dir / "regioes" / regiao
        target_dir.mkdir(parents=True, exist_ok=True)
        img_pil.save(target_dir / f"{regiao}.png",
                     format="PNG", compress_level=0)

    # --------------- LOG de execução -----------------------------
    def new_log_session(self, codigo_lote: str) -> Path:
        """
        Cria pasta logs/<datahora>_<codigo>/ e devolve o Path.
        """
        if not self.model_dir:
            raise RuntimeError("create_program() ainda não foi chamado.")

        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = self.model_dir / "logs" / f"{ts}_{codigo_lote}"
        dest.mkdir(parents=True, exist_ok=True)
        return dest

    def append_json_log(self, session_dir: Path, data: Dict[str,Any]):
        """
        Acrescenta entrada a <session>/*.json (cria se não existir).
        """
        main_json = session_dir / f"{session_dir.name}.json"
        entries   : List[Dict] = []
        if main_json.exists():
            entries = json.loads(main_json.read_text("utf-8"))
            if not isinstance(entries, list):
                entries = [entries]
        entries.append(data)
        main_json.write_text(json.dumps(entries, indent=2), "utf-8")

    def save_snapshot(self, session_dir: Path,
                      regiao_idx: int,
                      img: Image.Image):
        """
        Guarda regiao_<n>.png dentro da pasta da sessão.
        """
        snap_path = session_dir / f"regiao_{regiao_idx}.png"
        img.save(snap_path, format="PNG", compress_level=0)

# ------------------------------------------------------------------
# 3) Exemplo de uso rápido
# ------------------------------------------------------------------
if __name__ == "__main__":                      # test-drive
    from PIL import Image, ImageDraw

    base = AdhesiveProgramManager(".")
    base.create_program("demo_prog", overwrite=True)

    # cria ROI fictícia só para teste
    roi = Image.new("RGB", (400, 300), "gray")
    d   = ImageDraw.Draw(roi); d.rectangle([50,50,350,250], outline="blue", width=4)

    insp_info = MechanicalPositionInfo(
        janela_azul=(50, 50, 300, 200),
        similaridade=.97,
        inspecoes=[
            InspectionWindowInfo((60,60),(80,60),128,'preto',.9),
            InspectionWindowInfo((200,80),(60,60),100,'branco',.8)
        ]
    )
    base.save_blue_reference("regiao_1", "posicao_mecanica_A", "w1",
                             roi_pil=roi, meta=insp_info)

    ses = base.new_log_session("L123")
    base.append_json_log(ses, {"evento":"start", "t":datetime.now().isoformat()})
    base.save_snapshot(ses, 1, roi)
    print("Estrutura criada em:", base.model_dir)
