"""
Fiducial Matching Service - Template Matching usando OpenCV

Este serviço encapsula toda a lógica de template matching para detecção
de fiduciais em imagens, separando-a da camada de UI.

Responsabilidade única:
- Template matching usando OpenCV (cv2.matchTemplate)
- Validação de correlações
- Busca de múltiplos fiduciais

Author: Claude Code (Sonnet 4.5)
Created: 2026-01-15
Phase: SOLID Refactoring Phase 5B
"""

import logging
from typing import List, Optional, Tuple, Dict, Any, Callable
import numpy as np
import cv2

from .fiducial_models import (
    FiducialPoint,
    FiducialConfig,
    MatchingMethod
)

logger = logging.getLogger(__name__)


class MatchingError(Exception):
    """Exceção para erros de matching"""
    pass


class FiducialMatchingService:
    """
    Serviço para template matching de fiduciais.

    Este serviço é responsável por:
    - Encontrar templates em imagens usando OpenCV
    - Validar resultados de matching
    - Buscar múltiplos fiduciais em paralelo

    NOTA: Este serviço NÃO depende de PyQt6, sendo 100% testável.
    """

    def __init__(self, config: Optional[FiducialConfig] = None):
        """
        Inicializa o serviço de matching.

        Args:
            config: Configuração de matching (opcional)
        """
        self.config = config or FiducialConfig()
        logger.debug(f"FiducialMatchingService inicializado com método={self.config.matching_method}")

    def match_template(
        self,
        image: np.ndarray,
        template: np.ndarray,
        search_center: Tuple[float, float],
        search_radius: int
    ) -> Tuple[Optional[Tuple[float, float]], float]:
        """
        Executa template matching em uma região da imagem.

        Args:
            image: Imagem onde buscar (numpy array, grayscale ou BGR)
            template: Template a buscar (numpy array, grayscale ou BGR)
            search_center: Centro da busca (x, y) em pixels
            search_radius: Raio de busca em pixels

        Returns:
            ((matched_x, matched_y), max_correlation): Coordenada e correlação
            (None, 0.0): Se não encontrar nada acima do threshold

        Raises:
            MatchingError: Se parâmetros inválidos
        """
        # Validação
        if image is None or template is None:
            logger.warning("Imagem ou template é None")
            return None, 0.0

        if image.size == 0 or template.size == 0:
            logger.warning("Imagem ou template vazia")
            return None, 0.0

        if template.shape[0] > image.shape[0] or template.shape[1] > image.shape[1]:
            logger.warning(f"Template {template.shape} maior que imagem {image.shape}")
            return None, 0.0

        # Converter para grayscale se necessário
        if len(image.shape) == 3:
            image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            image_gray = image

        if len(template.shape) == 3:
            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        else:
            template_gray = template

        # Extrair região de interesse (ROI)
        x_center, y_center = search_center
        x_min = int(max(0, x_center - search_radius))
        y_min = int(max(0, y_center - search_radius))
        x_max = int(min(image_gray.shape[1], x_center + search_radius))
        y_max = int(min(image_gray.shape[0], y_center + search_radius))

        roi = image_gray[y_min:y_max, x_min:x_max]

        if roi.size == 0 or roi.shape[0] < template_gray.shape[0] or roi.shape[1] < template_gray.shape[1]:
            logger.warning(f"ROI {roi.shape} menor que template {template_gray.shape}")
            return None, 0.0

        # Executar template matching
        try:
            result = cv2.matchTemplate(roi, template_gray, self.config.matching_method.value)

            # NOTA: Métodos _NORMED (CCOEFF_NORMED, CCORR_NORMED, SQDIFF_NORMED)
            # já retornam valores normalizados entre 0 e 1

            # Encontrar melhor match
            min_val, max_val, min_loc, max_loc = (
                cv2.minMaxLoc(result)
            )

            # Para SQDIFF, menor valor é melhor
            if self.config.matching_method in [MatchingMethod.SQDIFF, MatchingMethod.SQDIFF_NORMED]:
                max_val = 1.0 - min_val
                max_loc = min_loc

            # Verificar threshold
            if max_val < self.config.matching_threshold:
                logger.debug(f"Correlação {max_val:.3f} abaixo do threshold {self.config.matching_threshold}")
                return None, 0.0

            # Calcular coordenada global (fora da ROI)
            matched_x = x_min + max_loc[0] + template_gray.shape[1] // 2
            matched_y = y_min + max_loc[1] + template_gray.shape[0] // 2

            logger.debug(f"Template encontrado em ({matched_x:.1f}, {matched_y:.1f}) com correlação {max_val:.3f}")

            return (matched_x, matched_y), max_val

        except cv2.error as e:
            logger.error(f"Erro no OpenCV durante matchTemplate: {e}")
            raise MatchingError(f"Erro no OpenCV: {e}")

    def locate_fiducials(
        self,
        image: np.ndarray,
        fiducials: List[FiducialPoint],
        progress_callback: Optional[Callable[..., None]] = None
    ) -> List[FiducialPoint]:
        """
        Busca múltiplos fiduciais na imagem.

        Args:
            image: Imagem onde buscar
            fiducials: Lista de fiduciais com templates
            progress_callback: Callback(opcional) para progresso

        Returns:
            Lista de fiduciais atualizada com coordenadas de match

        Raises:
            MatchingError: Se erro durante matching
        """
        if not fiducials:
            logger.warning("Lista de fiduciais vazia")
            return []

        matched_fiducials = []

        for idx, fiducial in enumerate(fiducials):
            # Notificar progresso
            if progress_callback:
                progress_callback(idx, len(fiducials), f"Buscando fiducial {idx + 1}/{len(fiducials)}")

            # Pular fiduciais sem template
            if not fiducial.has_template():
                logger.warning(f"Fiducial {idx} não possui template")
                matched_fiducials.append(fiducial)
                continue

            try:
                # Executar matching
                search_center = (fiducial.template_x, fiducial.template_y)
                match_result, correlation = self.match_template(
                    image=image,
                    template=fiducial.template,
                    search_center=search_center,
                    search_radius=fiducial.search_radius
                )

                # Atualizar fiducial com resultado
                if match_result is not None:
                    fiducial.matched_x, fiducial.matched_y = match_result
                    fiducial.correlation = correlation
                    fiducial.is_matched = True
                    logger.info(
                        f"Fiducial {idx}: encontrado em "
                        f"({fiducial.matched_x:.1f}, {fiducial.matched_y:.1f}) "
                        f"com correlação {correlation:.3f}"
                    )
                else:
                    fiducial.is_matched = False
                    fiducial.matched_x = None
                    fiducial.matched_y = None
                    fiducial.correlation = None
                    logger.warning(f"Fiducial {idx}: não encontrado (correlação abaixo do threshold)")

                matched_fiducials.append(fiducial)

            except MatchingError as e:
                logger.error(f"Erro ao buscar fiducial {idx}: {e}")
                # Adiciona fiducial sem match
                fiducial.is_matched = False
                matched_fiducials.append(fiducial)

        # Notificar conclusão
        if progress_callback:
            progress_callback(len(fiducials), len(fiducials), "Busca concluída")

        matched_count = sum(1 for f in matched_fiducials if f.is_matched)
        logger.info(f"Matching concluído: {matched_count}/{len(fiducials)} fiduciais encontrados")

        return matched_fiducials

    def validate_match(self, correlation: float) -> Tuple[bool, str]:
        """
        Valida se uma correlação é aceitável.

        Args:
            correlation: Valor de correlação (0-1)

        Returns:
            (is_valid, message): Tupla com validação e mensagem
        """
        if correlation < 0:
            return False, f"Correlação negativa: {correlation}"

        if correlation > 1:
            return False, f"Correlação > 1: {correlation}"

        if correlation < self.config.matching_threshold:
            return False, f"Correlação {correlation:.3f} abaixo do threshold {self.config.matching_threshold}"

        return True, "Correlação aceitável"

    def calculate_correlation_variance(self, fiducials: List[FiducialPoint]) -> float:
        """
        Calcula a variância das correlações dos fiduciais.

        Args:
            fiducials: Lista de fiduciais

        Returns:
            Variância das correlações (0-1)
        """
        matched = [f.correlation for f in fiducials if f.is_matched and f.correlation is not None]

        if not matched:
            return 0.0

        if len(matched) == 1:
            return 0.0

        mean_corr = sum(matched) / len(matched)
        variance = sum((c - mean_corr) ** 2 for c in matched) / len(matched)

        return float(variance)

    def validate_correlation_variance(self, fiducials: List[FiducialPoint]) -> Tuple[bool, str]:
        """
        Valida se a variância de correlações é aceitável.

        Uma variância muito alta indica que alguns fiduciais
        foram encontrados com muito mais certeza que outros,
        o que pode indicar problemas na calibração ou iluminação.

        Args:
            fiducials: Lista de fiduciais

        Returns:
            (is_valid, message): Tupla com validação e mensagem
        """
        variance = self.calculate_correlation_variance(fiducials)

        if variance > self.config.max_correlation_variance:
            return False, (
                f"Variância de correlação muito alta: {variance:.3f} "
                f"(máximo: {self.config.max_correlation_variance})"
            )

        return True, f"Variância de correlação aceitável: {variance:.3f}"

    def get_matching_summary(self, fiducials: List[FiducialPoint]) -> Dict[str, Any]:
        """
        Retorna resumo estatístico do matching.

        Args:
            fiducials: Lista de fiduciais

        Returns:
            Dicionário com estatísticas
        """
        matched = [f for f in fiducials if f.is_matched]
        correlations = [f.correlation for f in matched if f.correlation is not None]

        summary = {
            'total_fiducials': len(fiducials),
            'matched_fiducials': len(matched),
            'unmatched_fiducials': len(fiducials) - len(matched),
            'match_rate': len(matched) / len(fiducials) if fiducials else 0.0
        }

        if correlations:
            summary.update({
                'min_correlation': min(correlations),
                'max_correlation': max(correlations),
                'mean_correlation': sum(correlations) / len(correlations),
                'correlation_variance': self.calculate_correlation_variance(fiducials)
            })

        return summary
