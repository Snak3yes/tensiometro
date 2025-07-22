# inspection_engine.py
"""
Módulo de inspeção visual – compara um ROI (posição mecânica)
com suas imagens-referência e avalia as sub-janelas de inspeção.

Principais recursos
-------------------
• Pipeline único de pré-processamento (blur, contraste, brilho,
  threshold, normalização) 100 % idempotente;
• Máscara opcional (x,y,w,h) normalizada à janela azul;
• Busca do melhor template via cv2.matchTemplate (TM_CCOEFF_NORMED)
  em versão downscaled para velocidade;
• Avaliação de múltiplas janelas de inspeção (percentual de pixels
  brancos ou pretos ≥ limiar do usuário).

Uso rápido
----------
from inspection_engine import (
    MechanicalPosition, InspectionWindow, Inspector, default_preproc_cfg
)

# --- descreve a posição mecânica ------------------------------
pos = MechanicalPosition(
    roi=(100, 200, 450, 550),                 # ROI ABSOLUTO (px)
    reference_dir="modelos/U1/referencia",    # *.png da janela azul
    sim_threshold=0.975,                      # similaridade mínima
    image_cfg=default_preproc_cfg(),          # pré-proc
    mask=dict(enabled=False, x=.4,y=.4,width=.2,height=.2)  # opcional
)

# --- descreve janelas de inspeção dentro da ROI (normalizado) --
pos.windows = [
    InspectionWindow((.10,.12), (.30,.25), 128, 'white', 0.85),
    InspectionWindow((.60,.15), (.25,.30), 100, 'black', 0.90),
]

# --- inspeciona -----------------------------------------------
insp = Inspector()
result = insp.inspect(cv2.imread("placa_atual.png"), pos)
print(result.ok, result.best_similarity, result.window_results)
"""

from __future__ import annotations

import os, cv2, numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any, Optional
from PIL import Image

# ----------------------------------------------------------------------
#  Estruturas de configuração pública
# ----------------------------------------------------------------------
@dataclass
class InspectionWindow:
    """
    Define uma “janela vermelha” dentro da ROI:
        pos_norm  – (x,y)     posição normalizada (0-1) à ROI mecânica
        size_norm – (w,h)     tamanho normalizado (0-1)
        threshold – valor de corte (0-255)
        pixel     – 'white' ou 'black'  ➜ pixel alvo
        min_pct   – percentual mínimo (0-1) para aprovar
    """
    pos_norm:  Tuple[float, float]
    size_norm: Tuple[float, float]
    threshold: int            = 128
    pixel:     str            = 'white'
    min_pct:   float          = .80
    enabled:   bool           = True

@dataclass
class MechanicalPosition:
    """
    Define a posição mecânica (janela amarela):
        roi           – (x1,y1,x2,y2) absoluto na placa
        reference_dir – pasta *.png da janela azul
        sim_threshold – similaridade mínima (0-1) da janela azul
        image_cfg     – dicionário de pré-proc (ver default_preproc_cfg)
        mask          – dicionário opcional {enabled,x,y,width,height}
    """
    roi:            Tuple[int,int,int,int]
    reference_dir:  str
    sim_threshold:  float = .975
    image_cfg:      Dict[str,Any] = field(default_factory=lambda: default_preproc_cfg())
    mask:           Dict[str,Any] = field(default_factory=dict)
    windows:        List[InspectionWindow] = field(default_factory=list)

@dataclass
class WindowResult:
    ok:         bool
    pct:        float

@dataclass
class InspectionResult:
    ok:                bool
    best_similarity:   float
    window_results:    List[WindowResult]

# ----------------------------------------------------------------------
#  Pré-processamento (adaptado de utils/image_processing.apply_preprocessing)
# ----------------------------------------------------------------------
def default_preproc_cfg()->Dict[str,Any]:
    return dict(
        blur_enabled=False,  blur=0,
        contrast_enabled=False, contrast=1.0,
        brightness_enabled=False, brightness=0,
        threshold_enabled=False, threshold=128,
        normalization_enabled=False
    )

def apply_preprocessing(bgr: np.ndarray, cfg: Dict[str,Any]) -> np.ndarray:
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY) if bgr.ndim==3 else bgr.copy()
    gray = cv2.GaussianBlur(gray, (5,5), 0)  # blur legado
    # blur custom
    if cfg.get("blur_enabled"):
        sigma = int(cfg.get("blur",0))
        if sigma>0:
            gray = cv2.GaussianBlur(gray,(5,5),sigma)
    # contraste / brilho
    if cfg.get("contrast_enabled") or cfg.get("brightness_enabled"):
        alpha = cfg.get("contrast",1.0) if cfg.get("contrast_enabled") else 1.0
        beta  = cfg.get("brightness",0) if cfg.get("brightness_enabled") else 0
        gray  = cv2.convertScaleAbs(gray, alpha=alpha, beta=beta)
    # threshold
    if cfg.get("threshold_enabled"):
        th = int(cfg.get("threshold",128))
        _, gray = cv2.threshold(gray, th, 255, cv2.THRESH_BINARY)
    # normalização
    if cfg.get("normalization_enabled"):
        gray = cv2.normalize(gray,None,0,255,cv2.NORM_MINMAX)
    return gray

def apply_mask(img: np.ndarray, mcfg: Dict[str,Any]) -> np.ndarray:
    if not mcfg or not mcfg.get("enabled", False):
        return img
    h,w = img.shape[:2]
    x1 = int(mcfg["x"]*w); y1 = int(mcfg["y"]*h)
    x2 = int((mcfg["x"]+mcfg["width"])*w)
    y2 = int((mcfg["y"]+mcfg["height"])*h)
    out = img.copy()
    out[y1:y2,x1:x2] = 0
    return out

# ----------------------------------------------------------------------
#  Núcleo de comparação (derivado de utils.image_comparator.ImageComparator)
# ----------------------------------------------------------------------
class ROIComparator:
    def compare(self, roi_bgr: np.ndarray, ref_dir:str,
                cfg:Dict[str,Any]) -> float:
        """
        Percorre todos os *.png em ref_dir e devolve o maior score (0-1).
        """
        if not os.path.isdir(ref_dir):
            return 0.0
        proc_roi = apply_preprocessing(roi_bgr, cfg.get("image_cfg",{}))
        if cfg.get("mask",{}).get("enabled",False):
            proc_roi = apply_mask(proc_roi, cfg["mask"])
        ds = max(1,int(cfg.get("downscale",1)))
        small_roi = cv2.resize(proc_roi,(proc_roi.shape[1]//ds,
                                         proc_roi.shape[0]//ds)) if ds>1 else proc_roi
        best = 0.0
        for f in os.listdir(ref_dir):
            if not f.lower().endswith(".png"):
                continue
            tmpl = cv2.imread(os.path.join(ref_dir,f))
            if tmpl is None: continue
            if tmpl.ndim==3:
                tmpl = cv2.cvtColor(tmpl,cv2.COLOR_BGR2GRAY)
            tmpl = apply_preprocessing(tmpl, cfg.get("image_cfg",{}))
            if cfg.get("mask",{}).get("enabled",False):
                tmpl = apply_mask(tmpl, cfg["mask"])
            if ds>1:
                tmpl = cv2.resize(tmpl,(tmpl.shape[1]//ds, tmpl.shape[0]//ds))
            if (tmpl.shape[0]>small_roi.shape[0] or
                tmpl.shape[1]>small_roi.shape[1]):
                continue
            res = cv2.matchTemplate(small_roi, tmpl, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(res)
            best = max(best, float(max_val))
            if best>=cfg.get("sim_threshold",.975):
                break
        return best

# ----------------------------------------------------------------------
#  Lógica completa de inspeção
# ----------------------------------------------------------------------
class Inspector:
    def __init__(self):
        self._cmp = ROIComparator()

    # ---------- interface pública ------------------------------------
    def inspect(self, img_bgr: np.ndarray|Image.Image,
                pos : MechanicalPosition) -> InspectionResult:
        if isinstance(img_bgr, Image.Image):
            img_bgr = cv2.cvtColor(np.array(img_bgr), cv2.COLOR_RGB2BGR)
        x1,y1,x2,y2 = map(int,pos.roi)
        roi_bgr = img_bgr[y1:y2, x1:x2]
        # 1) janela azul (similaridade global)
        sim = self._cmp.compare(roi_bgr, pos.reference_dir,
                                dict(image_cfg=pos.image_cfg,
                                     mask=pos.mask,
                                     sim_threshold=pos.sim_threshold))
        # 2) janelas vermelhas
        win_results : List[WindowResult]=[]
        roi_gray = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2GRAY)
        for w in pos.windows:
            if not w.enabled:
                win_results.append(WindowResult(True,0.0))
                continue
            wx,wy = w.pos_norm; ww,hh = w.size_norm
            rx1 = int(wx*roi_gray.shape[1]); ry1=int(wy*roi_gray.shape[0])
            rx2 = rx1+int(ww*roi_gray.shape[1]); ry2=ry1+int(hh*roi_gray.shape[0])
            sub = roi_gray[ry1:ry2, rx1:rx2]
            if sub.size==0:
                win_results.append(WindowResult(False,0.0)); continue
            if w.pixel.lower()=='white':
                pct = float((sub>=w.threshold).mean())
            else:
                pct = float((sub<w.threshold).mean())
            ok = pct >= w.min_pct
            win_results.append(WindowResult(ok,pct))
        overall_ok = (sim >= pos.sim_threshold and all(r.ok for r in win_results))
        return InspectionResult(overall_ok, sim, win_results)
