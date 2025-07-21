# barcode_scanner.py
"""
Leitura de códigos de barras / QR Codes em imagens estáticas.

Requisitos:
    pip install opencv-python pyzbar numpy Pillow
    # pyzbar é opcional: se faltar, o módulo continua lendo QR Codes
    # via OpenCV.QRCodeDetector, mas não lerá barcodes lineares.

API principal:
    from barcode_scanner import BarcodeScanner, ScanResult

    scanner = BarcodeScanner()                       # opções default
    results = scanner.scan(pil_image,
                           roi=(x, y, w, h))        # lista[ScanResult]

    if results:
        print(results[0].data, results[0].type)

    # imagem com marcações (para depuração / relatório)
    marked = scanner.draw_codes(pil_image, results)
"""

from __future__ import annotations

import cv2
import numpy as np
from dataclasses import dataclass
from typing import List, Sequence, Tuple, Optional, Any

try:
    from pyzbar.pyzbar import decode as _pyzbar_decode
    _PYZBAR_OK = True
except ImportError:                                 # pyzbar é opcional
    _PYZBAR_OK = False

try:
    from PIL import Image
    _PIL_OK = True
except ImportError:
    _PIL_OK = False


# ----------------------------------------------------------------------
#  Estruturas de dados públicas
# ----------------------------------------------------------------------
Point = Tuple[int, int]            # (x, y)

@dataclass
class ScanResult:
    """Resultado de um único código decodificado."""
    data:    str                   # conteúdo (texto)
    type:    str                   # 'CODE128', 'EAN13', 'QRCODE', …
    polygon: List[Point] | None    # pontos do contorno ou None


# ----------------------------------------------------------------------
#  Funções utilitárias privadas
# ----------------------------------------------------------------------
def _to_bgr(image: Any) -> np.ndarray:
    """
    Converte `image` para ndarray BGR:
        - aceita ndarray BGR / RGB / Gray
        - aceita PIL.Image
    """
    if isinstance(image, np.ndarray):
        arr = image
        if arr.ndim == 2:                                   # grayscale
            return cv2.cvtColor(arr, cv2.COLOR_GRAY2BGR)
        if arr.shape[2] == 3:                               # BGR ou RGB
            # heurística simples: média canal B < média canal R → RGB
            return (cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
                    if arr[..., 0].mean() < arr[..., 2].mean()
                    else arr.copy())
        raise ValueError("formato ndarray não suportado")
    if _PIL_OK and isinstance(image, Image.Image):
        img_rgb = image.convert("RGB")
        return cv2.cvtColor(np.array(img_rgb), cv2.COLOR_RGB2BGR)
    raise TypeError("tipo de imagem não suportado")


def _apply_preprocessing(
    bgr: np.ndarray,
    *,
    clahe_clip: float = 2.0,
    clahe_grid: int   = 8,
    blur_sigma: int   = 0,
    adaptive_thresh: bool = True
) -> np.ndarray:
    """
    Pipeline leve para melhorar contraste / ruído em barcodes.
    Ajuste os parâmetros conforme a necessidade.
    """
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    # CLAHE (equalização adaptativa)
    if clahe_clip > 0:
        clahe = cv2.createCLAHE(clipLimit=clahe_clip,
                                tileGridSize=(clahe_grid, clahe_grid))
        gray = clahe.apply(gray)

    # Blur gaussiano opcional
    if blur_sigma > 0:
        gray = cv2.GaussianBlur(gray, (5, 5), blur_sigma)

    # Binarização adaptativa (melhora contraste)
    if adaptive_thresh:
        gray = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            21, 10
        )

    return gray


# ----------------------------------------------------------------------
#  Classe principal
# ----------------------------------------------------------------------
class BarcodeScanner:
    """
    Detector / decodificador de códigos de barras e QR Codes.
    Todos os parâmetros têm valor-padrão seguro; ajuste se necessário.
    """
    def __init__(
        self,
        *,
        clahe_clip: float = 2.0,
        clahe_grid: int   = 8,
        blur_sigma: int   = 0,
        adaptive_thresh: bool = True
    ):
        self.clahe_clip      = clahe_clip
        self.clahe_grid      = clahe_grid
        self.blur_sigma      = blur_sigma
        self.adaptive_thresh = adaptive_thresh
        self._qr_detector    = cv2.QRCodeDetector()

    # --------------  API pública  ------------------------------------
    def scan(
        self,
        image: Any,
        *,
        roi: Optional[Tuple[int, int, int, int]] = None,   # (x,y,w,h)
        preprocess: bool = True
    ) -> List[ScanResult]:
        """
        Decodifica códigos de barras / QR na imagem inteira
        ou dentro de uma ROI (x, y, w, h) em pixels.

        Retorna lista de ScanResult; vazia se nada encontrado.
        """
        bgr = _to_bgr(image)
        if roi is not None:
            x, y, w, h = map(int, roi)
            bgr = bgr[max(0, y):y + h, max(0, x):x + w]          # clamp

        proc = (_apply_preprocessing(bgr,
                                     clahe_clip=self.clahe_clip,
                                     clahe_grid=self.clahe_grid,
                                     blur_sigma=self.blur_sigma,
                                     adaptive_thresh=self.adaptive_thresh)
                if preprocess else
                cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY))

        results: List[ScanResult] = []

        # -- pyzbar (QR + barcodes lineares) ----------------------------
        if _PYZBAR_OK:
            for obj in _pyzbar_decode(proc):
                poly = [(p.x, p.y) for p in obj.polygon] if obj.polygon else None
                results.append(ScanResult(
                    data=obj.data.decode("utf-8", errors="ignore"),
                    type=obj.type.upper(),
                    polygon=poly
                ))

        # -- OpenCV QRCodeDetector (apenas QR) --------------------------
        data, points, _ = self._qr_detector.detectAndDecode(proc)
        if data:
            poly = [(int(p[0]), int(p[1])) for p in points] if points is not None else None
            # evita duplicar caso pyzbar já tenha encontrado o mesmo QR
            if not any(r.data == data for r in results):
                results.append(ScanResult(
                    data=data,
                    type="QRCODE",
                    polygon=poly
                ))

        return results

    def draw_codes(
        self,
        image: Any,
        codes: Sequence[ScanResult],
        *,
        copy: bool = True
    ) -> "Image.Image":
        """
        Desenha contornos e legendas dos códigos detectados sobre a imagem.
        Devolve objeto PIL.Image.  Se `copy=False`, sobrescreve a própria
        imagem (se for PIL); caso contrário, opera sobre uma cópia.
        """
        if not _PIL_OK:
            raise RuntimeError("Pillow não instalado – draw_codes indisponível")

        pil = image.copy() if copy and _PIL_OK else image
        if not isinstance(pil, Image.Image):
            pil = Image.fromarray(_to_bgr(image)[..., ::-1])   # BGR ➜ RGB

        import PIL.ImageDraw as ImageDraw
        import PIL.ImageFont as ImageFont

        draw = ImageDraw.Draw(pil)
        try:
            font = ImageFont.truetype("arial.ttf", 14)
        except Exception:
            font = ImageFont.load_default()

        for idx, code in enumerate(codes, 1):
            if code.polygon and len(code.polygon) >= 4:
                draw.line(code.polygon + [code.polygon[0]],
                          fill="red", width=3)
                x, y = code.polygon[0]
            else:
                x = y = 10
            label = f"{idx}: {code.type}"
            draw.text((x, y - 15), label, fill="yellow", font=font)
            draw.text((x, y - 30), code.data[:30] + ("…" if len(code.data) > 30 else ""),
                      fill="cyan", font=font)

        return pil


# ----------------------------------------------------------------------
#  Execução de teste rápida  (python barcode_scanner.py  <imagem>)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import sys, pathlib, os
    if len(sys.argv) < 2:
        print("Uso: python barcode_scanner.py <imagem.[png|jpg|bmp|etc]> "
              "[x y w h]")
        sys.exit(1)

    img_path = pathlib.Path(sys.argv[1])
    if not img_path.exists():
        print("Arquivo não encontrado:", img_path)
        sys.exit(2)

    roi = None
    if len(sys.argv) == 6:                           # ROI passada na linha
        roi = tuple(int(v) for v in sys.argv[2:6])

    from PIL import Image
    pil = Image.open(img_path)

    scanner = BarcodeScanner()
    codes = scanner.scan(pil, roi=roi)

    if not codes:
        print("Nenhum código encontrado.")
    else:
        print(f"{len(codes)} código(s) encontrado(s):")
        for c in codes:
            print(f" - {c.type:<8} {c.data}")

        out = scanner.draw_codes(pil, codes)
        out_name = img_path.with_name(img_path.stem + "_marked.png")
        out.save(out_name)
        print("Imagem marcada salva em:", out_name)
