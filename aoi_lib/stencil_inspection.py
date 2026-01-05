# -*- coding: utf-8 -*-
"""
stencil_inspection.py
---------------------
Módulo de algoritmos de inspeção visual para stencils.

Baseado nos algoritmos da aplicação de inspeção original (Tkinter),
adaptado para uso independente com PyQt6 e OpenCV.

Algoritmos implementados:
  1. Inspeção de Preto e Branco (percent_white_or_black)
     - Conta percentual de pixels acima/abaixo de um threshold
     - Usado para verificar se aberturas do stencil estão obstruídas
  
  2. Comparação de Imagem (template matching)
     - Compara ROI capturado com imagem de referência
     - Retorna score de similaridade (0.0 a 1.0)

Autor adaptação: Sistema AOI Tensiometro
Data: 2024-12-10
"""

import cv2
import numpy as np
import os
import logging
from typing import Tuple, Optional, Dict, Any, List
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTES
# =============================================================================

HATCH_STEP = 5  # Espaçamento do hachurado em pixels


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class InspectionWindow:
    """
    Define uma janela de inspeção (região de interesse) dentro do stencil.
    
    Coordenadas normalizadas (0.0 a 1.0) em relação ao ROI pai.
    """
    # Posição normalizada (x, y) - canto superior esquerdo
    x: float = 0.0
    y: float = 0.0
    
    # Tamanho normalizado (width, height)
    width: float = 1.0
    height: float = 1.0
    
    # Parâmetros de inspeção
    threshold: int = 128  # Limiar para binarização (0-255)
    target_color: str = 'white'  # 'white' ou 'black' - qual cor contar
    min_percent: float = 95.0  # Percentual mínimo para aprovação
    
    # Estado
    enabled: bool = True
    result: float = 0.0  # Resultado da última inspeção
    status: bool = False  # True = aprovado, False = reprovado
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa para dicionário."""
        return {
            'posicao': [self.x, self.y],
            'tamanho': [self.width, self.height],
            'threshold': self.threshold,
            'cor_pixel': 'branco' if self.target_color == 'white' else 'preto',
            'percentual_minimo': self.min_percent,
            'habilitada': self.enabled,
            'resultado': self.result,
            'status': self.status
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InspectionWindow':
        """Deserializa de dicionário."""
        pos = data.get('posicao', [0, 0])
        size = data.get('tamanho', [1, 1])
        return cls(
            x=pos[0],
            y=pos[1],
            width=size[0],
            height=size[1],
            threshold=data.get('threshold', 128),
            target_color='white' if data.get('cor_pixel', 'branco') == 'branco' else 'black',
            min_percent=data.get('percentual_minimo', 95.0),
            enabled=data.get('habilitada', True),
            result=data.get('resultado', 0.0),
            status=data.get('status', False)
        )


@dataclass
class InspectionResult:
    """Resultado de uma inspeção."""
    window_id: int
    percent: float  # Percentual de pixels da cor alvo
    passed: bool  # Se passou no critério mínimo
    threshold_used: int
    target_color: str
    min_required: float


@dataclass
class ImageComparisonResult:
    """Resultado de comparação de imagem."""
    similarity: float  # Score de similaridade (0.0 a 1.0)
    passed: bool  # Se passou no critério mínimo
    min_required: float
    best_match_loc: Tuple[int, int] = (0, 0)


# =============================================================================
# FUNÇÕES DE PROCESSAMENTO DE IMAGEM
# =============================================================================

def apply_preprocessing(bgr: np.ndarray, cfg: Dict[str, Any]) -> np.ndarray:
    """
    Aplica cadeia de transformações de pré-processamento.
    
    Args:
        bgr: Imagem em BGR (np.ndarray)
        cfg: Dicionário de configuração contendo:
             blur_enabled, blur, contrast_enabled, contrast,
             brightness_enabled, brightness,
             threshold_enabled, threshold,
             normalization_enabled
    
    Returns:
        Imagem em escala de cinza pré-processada
    """
    logger.debug("[PRE] início blur=%s thresh=%s norm=%s shape=%s",
                 cfg.get("blur_enabled"), cfg.get("threshold_enabled"),
                 cfg.get("normalization_enabled"), bgr.shape)
    
    if bgr is None:
        raise ValueError("apply_preprocessing: imagem 'bgr' vazia")

    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY) if bgr.ndim == 3 else bgr.copy()

    # Blur legado (sempre executado para suavizar ruído)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)

    # Blur customizado
    if cfg.get("blur_enabled"):
        sigma = int(cfg.get("blur", 0))
        if sigma > 0:
            gray = cv2.GaussianBlur(gray, (5, 5), sigma)

    # Contraste / brilho
    if cfg.get("contrast_enabled") or cfg.get("brightness_enabled"):
        alpha = cfg.get("contrast", 1.0) if cfg.get("contrast_enabled") else 1.0
        beta = cfg.get("brightness", 0) if cfg.get("brightness_enabled") else 0
        gray = cv2.convertScaleAbs(gray, alpha=alpha, beta=beta)

    # Threshold (binarização)
    if cfg.get("threshold_enabled"):
        th = int(cfg.get("threshold", 128))
        _, gray = cv2.threshold(gray, th, 255, cv2.THRESH_BINARY)

    # Normalização
    if cfg.get("normalization_enabled"):
        gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
    
    logger.debug("[PRE] fim shape=%s dtype=%s", gray.shape, gray.dtype)
    return gray


def apply_mask(img: np.ndarray, mask_cfg: Dict[str, Any]) -> np.ndarray:
    """
    Aplica uma máscara retangular à imagem.
    
    Args:
        img: Imagem (grayscale ou BGR)
        mask_cfg: Configuração da máscara com x, y, width, height normalizados
    
    Returns:
        Imagem com região mascarada zerada
    """
    if not mask_cfg or not mask_cfg.get("enabled", False):
        return img.copy()

    h, w = img.shape[:2]
    x1 = int(mask_cfg["x"] * w)
    y1 = int(mask_cfg["y"] * h)
    x2 = int((mask_cfg["x"] + mask_cfg["width"]) * w)
    y2 = int((mask_cfg["y"] + mask_cfg["height"]) * h)

    out = img.copy()
    if out.ndim == 2:
        out[y1:y2, x1:x2] = 0
    else:
        out[y1:y2, x1:x2] = (0, 0, 0)
    return out


def clahe_enhance(img: np.ndarray, clip_limit: float = 4.0, 
                  grid_size: int = 8) -> np.ndarray:
    """
    Aplica CLAHE (Contrast Limited Adaptive Histogram Equalization).
    
    Args:
        img: Imagem BGR ou grayscale
        clip_limit: Limite de contraste
        grid_size: Tamanho do grid
    
    Returns:
        Imagem com contraste aprimorado (grayscale)
    """
    if img.ndim == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img
    
    clahe = cv2.createCLAHE(clipLimit=clip_limit, 
                            tileGridSize=(grid_size, grid_size))
    return clahe.apply(gray)


# =============================================================================
# ALGORITMOS DE INSPEÇÃO
# =============================================================================

def percent_white_or_black(gray_img: np.ndarray, threshold: int, 
                           target: str = 'white') -> float:
    """
    Calcula o percentual de pixels brancos ou pretos em uma imagem.
    
    Este é o algoritmo principal para verificar obstrução de aberturas
    em stencils. Com luz backlight:
    - Abertura LIMPA = alta proporção de branco (luz passa)
    - Abertura OBSTRUÍDA = alta proporção de preto (luz bloqueada)
    
    Args:
        gray_img: Imagem em escala de cinza (numpy array)
        threshold: Limiar para binarização (0-255)
        target: 'white' para contar pixels >= threshold,
                'black' para contar pixels < threshold
    
    Returns:
        Percentual de pixels da cor alvo (0.0 a 100.0)
    
    Example:
        >>> img = cv2.imread('abertura.png', cv2.IMREAD_GRAYSCALE)
        >>> percent = percent_white_or_black(img, threshold=128, target='white')
        >>> print(f"Abertura está {percent:.1f}% limpa")
    """
    if gray_img is None or gray_img.size == 0:
        return 0.0
    
    # Garantir grayscale
    if gray_img.ndim == 3:
        gray_img = cv2.cvtColor(gray_img, cv2.COLOR_BGR2GRAY)
    
    # Criar máscara binária
    if target == 'white':
        mask = gray_img >= threshold
    else:
        mask = gray_img < threshold
    
    # Calcular percentual
    percent = float(mask.mean() * 100.0)
    
    logger.debug(f"[PB] threshold={threshold} target={target} result={percent:.2f}%")
    return percent


def gray_mask(gray_img: np.ndarray, threshold: int, 
              target: str = 'white') -> np.ndarray:
    """
    Retorna máscara booleana para pixels selecionados.
    
    Args:
        gray_img: Imagem em escala de cinza
        threshold: Limiar de binarização
        target: 'white' ou 'black'
    
    Returns:
        Array booleano (True onde pixel está selecionado)
    """
    if target == 'white':
        return gray_img >= threshold
    else:
        return gray_img < threshold


def hatch_overlay(mask: np.ndarray, color: Tuple[int, int, int, int] = (255, 255, 0, 128),
                  step: int = HATCH_STEP) -> np.ndarray:
    """
    Gera uma imagem RGBA com linhas diagonais (hachurado) sobre uma máscara.
    
    Útil para visualização de áreas selecionadas pela inspeção.
    
    Args:
        mask: Máscara booleana (True onde desenhar)
        color: Cor RGBA do hachurado
        step: Espaçamento entre linhas
    
    Returns:
        Imagem RGBA com overlay hachurado
    """
    h, w = mask.shape
    overlay = np.zeros((h, w, 4), dtype=np.uint8)
    
    # Desenhar linhas diagonais
    for i in range(0, h + w, step):
        cv2.line(overlay, (i, 0), (0, i), color, 1, lineType=cv2.LINE_AA)
    
    # Aplicar alfa somente onde mask==True
    alpha = (mask * 255).astype(np.uint8)
    overlay[:, :, 3] = alpha
    
    return overlay


# =============================================================================
# COMPARAÇÃO DE IMAGEM (TEMPLATE MATCHING)
# =============================================================================

class ImageComparator:
    """
    Compara imagens usando template matching (correlação normalizada).
    
    Usado para:
    - Verificar se um componente está presente
    - Detectar deslocamentos em relação à referência
    - Validar qualidade visual
    """
    
    def __init__(self):
        self.last_score = 0.0
        self.last_location = (0, 0)
    
    def compare(self, roi_img: np.ndarray, reference_dir: str,
                cfg: Dict[str, Any]) -> Tuple[float, Optional[np.ndarray]]:
        """
        Compara ROI com todas as imagens de referência em um diretório.
        
        Args:
            roi_img: Imagem da região de interesse (BGR ou RGB)
            reference_dir: Caminho do diretório com imagens de referência (.png)
            cfg: Configuração contendo:
                 - similaridade_minima: threshold para aprovação (0.0 a 1.0)
                 - imagem_config: config de pré-processamento
                 - downscale: fator de redução para acelerar (default=1)
        
        Returns:
            (maior_score, melhor_template) - score entre 0.0 e 1.0
        """
        if not os.path.isdir(reference_dir):
            logger.warning(f"[CMP] Diretório não encontrado: {reference_dir}")
            return 0.0, None

        # Garantir BGR
        if roi_img.ndim == 3 and roi_img.shape[2] == 3:
            # Heurística: se canal 0 < canal 2, provavelmente é RGB
            if roi_img[..., 0].mean() < roi_img[..., 2].mean():
                roi_bgr = cv2.cvtColor(roi_img, cv2.COLOR_RGB2BGR)
                logger.debug("[CMP] ROI convertido de RGB para BGR")
            else:
                roi_bgr = roi_img
        else:
            roi_bgr = roi_img

        # Pré-processamento
        img_cfg = cfg.get("imagem_config", {})
        proc_roi = apply_preprocessing(roi_bgr, img_cfg)
        
        if img_cfg.get("mask_region", {}).get("enabled", False):
            proc_roi = apply_mask(proc_roi, img_cfg["mask_region"])

        # Downscale para acelerar
        ds = max(1, int(cfg.get("downscale", 1)))
        if ds > 1:
            small_roi = cv2.resize(proc_roi,
                                   (proc_roi.shape[1] // ds,
                                    proc_roi.shape[0] // ds))
        else:
            small_roi = proc_roi

        best = 0.0
        best_tmpl = None
        min_similarity = cfg.get("similaridade_minima", 0.975)

        # Iterar sobre templates
        for f in os.listdir(reference_dir):
            if not f.lower().endswith(".png"):
                continue
            
            tmpl_path = os.path.join(reference_dir, f)
            tmpl = cv2.imread(tmpl_path)
            
            if tmpl is None:
                continue

            # Conversão RGB->BGR se necessário
            if tmpl.ndim == 3 and tmpl[..., 0].mean() < tmpl[..., 2].mean():
                tmpl = cv2.cvtColor(tmpl, cv2.COLOR_RGB2BGR)

            # Verificar se template cabe no ROI
            if (tmpl.shape[0] > proc_roi.shape[0] or
                tmpl.shape[1] > proc_roi.shape[1]):
                logger.debug("[CMP] %s ignorado (template maior que ROI)",
                           os.path.basename(tmpl_path))
                continue
            
            # Processar template
            tmpl = apply_preprocessing(tmpl, img_cfg)
            
            if img_cfg.get("mask_region", {}).get("enabled", False):
                tmpl = apply_mask(tmpl, img_cfg["mask_region"])
            
            if ds > 1:
                small_tmpl = cv2.resize(tmpl,
                                        (tmpl.shape[1] // ds,
                                         tmpl.shape[0] // ds))
            else:
                small_tmpl = tmpl

            # Template matching
            ok, score, loc = self.template_match(small_roi, small_tmpl, min_similarity)
            
            logger.debug("[CMP] %-25s score=%.4f%s",
                        os.path.basename(tmpl_path), score,
                        " < min" if not ok else "")
            
            if score > best:
                best = score
                best_tmpl = tmpl
                self.last_location = loc

            if best >= min_similarity:
                break  # Encontrou match suficiente

        self.last_score = best
        logger.info("[CMP] Resultado final = %.4f", best)
        return best, best_tmpl

    def template_match(self, img: np.ndarray, tmpl: np.ndarray, 
                       threshold: float) -> Tuple[bool, float, Tuple[int, int]]:
        """
        Executa template matching usando correlação normalizada.
        
        Args:
            img: Imagem para buscar
            tmpl: Template a buscar
            threshold: Limiar de similaridade
        
        Returns:
            (passou, score, localização)
        """
        if img.size == 0 or tmpl.size == 0:
            return False, 0.0, (0, 0)
        
        try:
            res = cv2.matchTemplate(img, tmpl, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(res)
            return (max_val >= threshold, float(max_val), max_loc)
        except cv2.error as e:
            logger.error(f"[CMP] Erro no template matching: {e}")
            return False, 0.0, (0, 0)

    def compare_single(self, roi_img: np.ndarray, reference_img: np.ndarray,
                       preprocess_cfg: Optional[Dict] = None) -> float:
        """
        Compara ROI com uma única imagem de referência.
        
        Args:
            roi_img: Imagem da região de interesse
            reference_img: Imagem de referência
            preprocess_cfg: Configuração de pré-processamento (opcional)
        
        Returns:
            Score de similaridade (0.0 a 1.0)
        """
        cfg = preprocess_cfg or {}
        
        # Pré-processamento
        roi_prep = apply_preprocessing(roi_img, cfg)
        ref_prep = apply_preprocessing(reference_img, cfg)
        
        # Ajustar tamanho se necessário
        if (ref_prep.shape[0] > roi_prep.shape[0] or
            ref_prep.shape[1] > roi_prep.shape[1]):
            scale = min(roi_prep.shape[0] / ref_prep.shape[0],
                       roi_prep.shape[1] / ref_prep.shape[1])
            ref_prep = cv2.resize(
                ref_prep,
                (int(ref_prep.shape[1] * scale), 
                 int(ref_prep.shape[0] * scale)),
                interpolation=cv2.INTER_AREA
            )
        
        try:
            res = cv2.matchTemplate(roi_prep, ref_prep, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(res)
            return float(max_val)
        except Exception as e:
            logger.error(f"[CMP_SINGLE] Erro: {e}")
            return 0.0


# =============================================================================
# INSPETOR DE STENCIL
# =============================================================================

class StencilInspector:
    """
    Classe principal para inspeção de stencils.
    
    Combina algoritmos de:
    - Análise de preto/branco (verificar aberturas)
    - Comparação de imagem (verificar correspondência)
    """
    
    def __init__(self):
        self.image_comparator = ImageComparator()
        self.last_results: List[InspectionResult] = []
        self.overall_status = False
    
    def inspect_opening(self, image: np.ndarray, window: InspectionWindow,
                        full_roi_size: Tuple[int, int] = None) -> InspectionResult:
        """
        Inspeciona uma abertura do stencil usando análise de preto/branco.
        
        Com backlight ligado:
        - Luz passa pela abertura = pixels brancos
        - Luz bloqueada = pixels pretos
        
        Args:
            image: Imagem do ROI completo (BGR ou grayscale)
            window: Definição da janela de inspeção
            full_roi_size: Tamanho do ROI (width, height) se diferente da imagem
        
        Returns:
            InspectionResult com percentual e status
        """
        if not window.enabled:
            return InspectionResult(
                window_id=0,
                percent=0.0,
                passed=True,  # Janela desabilitada = passa
                threshold_used=window.threshold,
                target_color=window.target_color,
                min_required=window.min_percent
            )
        
        # Determinar tamanho do ROI
        if full_roi_size:
            roi_w, roi_h = full_roi_size
        else:
            roi_h, roi_w = image.shape[:2]
        
        # Calcular coordenadas da janela em pixels
        x1 = int(window.x * roi_w)
        y1 = int(window.y * roi_h)
        x2 = int((window.x + window.width) * roi_w)
        y2 = int((window.y + window.height) * roi_h)
        
        # Validar coordenadas
        if x2 <= x1 or y2 <= y1:
            logger.warning("Janela com dimensões inválidas")
            return InspectionResult(
                window_id=0, percent=0.0, passed=False,
                threshold_used=window.threshold,
                target_color=window.target_color,
                min_required=window.min_percent
            )
        
        # Recortar janela
        window_img = image[y1:y2, x1:x2]
        
        # Converter para grayscale se necessário
        if window_img.ndim == 3:
            window_gray = cv2.cvtColor(window_img, cv2.COLOR_BGR2GRAY)
        else:
            window_gray = window_img
        
        # Calcular percentual
        percent = percent_white_or_black(
            window_gray, 
            window.threshold, 
            window.target_color
        )
        
        # Determinar status
        passed = percent >= window.min_percent
        
        # Atualizar janela
        window.result = percent
        window.status = passed
        
        return InspectionResult(
            window_id=0,
            percent=percent,
            passed=passed,
            threshold_used=window.threshold,
            target_color=window.target_color,
            min_required=window.min_percent
        )
    
    def inspect_multiple_openings(self, image: np.ndarray, 
                                  windows: List[InspectionWindow]) -> List[InspectionResult]:
        """
        Inspeciona múltiplas aberturas do stencil.
        
        Args:
            image: Imagem do stencil (BGR ou grayscale)
            windows: Lista de janelas de inspeção
        
        Returns:
            Lista de resultados de inspeção
        """
        results = []
        roi_h, roi_w = image.shape[:2]
        
        for i, window in enumerate(windows):
            result = self.inspect_opening(image, window, (roi_w, roi_h))
            result.window_id = i
            results.append(result)
            
            logger.debug(f"Janela {i}: {result.percent:.1f}% "
                        f"({'OK' if result.passed else 'NOK'})")
        
        self.last_results = results
        self.overall_status = all(r.passed for r in results)
        
        return results
    
    def compare_with_reference(self, roi_image: np.ndarray, 
                               reference_path: str,
                               min_similarity: float = 0.975,
                               preprocess_cfg: Optional[Dict] = None) -> ImageComparisonResult:
        """
        Compara ROI do stencil com imagem de referência.
        
        Args:
            roi_image: Imagem capturada
            reference_path: Caminho da imagem ou diretório de referência
            min_similarity: Similaridade mínima para aprovação
            preprocess_cfg: Configuração de pré-processamento
        
        Returns:
            ImageComparisonResult com score e status
        """
        cfg = {
            'similaridade_minima': min_similarity,
            'imagem_config': preprocess_cfg or {}
        }
        
        if os.path.isdir(reference_path):
            score, _ = self.image_comparator.compare(roi_image, reference_path, cfg)
        elif os.path.isfile(reference_path):
            ref_img = cv2.imread(reference_path)
            if ref_img is None:
                return ImageComparisonResult(0.0, False, min_similarity)
            score = self.image_comparator.compare_single(
                roi_image, ref_img, preprocess_cfg
            )
        else:
            return ImageComparisonResult(0.0, False, min_similarity)
        
        return ImageComparisonResult(
            similarity=score,
            passed=score >= min_similarity,
            min_required=min_similarity,
            best_match_loc=self.image_comparator.last_location
        )


# =============================================================================
# FUNÇÕES UTILITÁRIAS
# =============================================================================

def create_inspection_visualization(image: np.ndarray, 
                                   windows: List[InspectionWindow],
                                   show_results: bool = True) -> np.ndarray:
    """
    Cria visualização das janelas de inspeção sobre a imagem.
    
    Args:
        image: Imagem base (BGR)
        windows: Lista de janelas de inspeção
        show_results: Se True, mostra resultado da última inspeção
    
    Returns:
        Imagem com anotações
    """
    result = image.copy()
    h, w = image.shape[:2]
    
    for i, win in enumerate(windows):
        if not win.enabled:
            continue
        
        x1 = int(win.x * w)
        y1 = int(win.y * h)
        x2 = int((win.x + win.width) * w)
        y2 = int((win.y + win.height) * h)
        
        # Cor baseada no status
        if show_results:
            color = (0, 255, 0) if win.status else (0, 0, 255)  # Verde/Vermelho
        else:
            color = (255, 0, 0)  # Azul
        
        # Desenhar retângulo
        cv2.rectangle(result, (x1, y1), (x2, y2), color, 2)
        
        # Texto com resultado
        if show_results:
            text = f"{win.result:.1f}%"
            cv2.putText(result, text, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    
    return result


def resize_with_aspect_ratio(image: np.ndarray, 
                             target_width: int, 
                             target_height: int) -> Tuple[np.ndarray, Tuple[int, int], Tuple[float, float]]:
    """
    Redimensiona imagem mantendo proporção.
    
    Args:
        image: Imagem original
        target_width: Largura alvo
        target_height: Altura alvo
    
    Returns:
        (imagem_redimensionada, (offset_x, offset_y), (scale_x, scale_y))
    """
    h, w = image.shape[:2]
    
    if w == 0 or h == 0:
        raise ValueError("Tamanho da imagem inválido")
    
    scale = min(target_width / w, target_height / h)
    new_w = int(w * scale)
    new_h = int(h * scale)
    
    offset = ((target_width - new_w) // 2, (target_height - new_h) // 2)
    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
    
    return resized, offset, (new_w / w, new_h / h)


# =============================================================================
# TESTE
# =============================================================================

if __name__ == "__main__":
    # Teste básico dos algoritmos
    print("=== Teste do módulo stencil_inspection ===\n")
    
    # Criar imagem de teste (simula abertura parcialmente obstruída)
    test_img = np.zeros((100, 100), dtype=np.uint8)
    test_img[20:80, 20:80] = 255  # Centro branco
    test_img[40:60, 40:60] = 0    # Obstrução no centro
    
    # Teste 1: percent_white_or_black
    percent = percent_white_or_black(test_img, threshold=128, target='white')
    print(f"Teste percent_white_or_black: {percent:.2f}% branco")
    
    # Teste 2: InspectionWindow
    window = InspectionWindow(
        x=0.2, y=0.2, width=0.6, height=0.6,
        threshold=128, target_color='white', min_percent=50.0
    )
    
    inspector = StencilInspector()
    result = inspector.inspect_opening(test_img, window)
    print(f"Teste inspect_opening: {result.percent:.2f}% - {'APROVADO' if result.passed else 'REPROVADO'}")
    
    print("\n=== Módulo carregado com sucesso! ===")
