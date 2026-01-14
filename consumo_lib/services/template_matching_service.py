"""
Template Matching Service - Serviço de Template Matching

Este módulo contém a lógica de negócio para busca de fiduciais usando
template matching com OpenCV, separada da UI.

Responsabilidades:
    - Buscar fiduciais em imagens usando template matching
    - Calcular scores de similaridade
    - Validar resultados de matching
    - Fornecer interface simplificada para template matching

Author: Claude Sonnet 4.5
Date: 2026-01-14
Track: solid_refactoring_phase2_20260114 (Phase 3 - Alignment Widget Refactoring)
"""

from __future__ import annotations

import logging
from typing import List, Optional, Tuple

import cv2
import numpy as np
from numpy.typing import NDArray

from aoi_lib.fiducial_alignment import (
    FiducialAligner,
    FiducialTemplate,
    FiducialMatchResult,
)
from consumo_lib.models.alignment_state import FiducialMatch

logger = logging.getLogger(__name__)


class TemplateMatchingService:
    """
    Serviço de template matching para fiduciais.

    Este serviço fornece uma interface simplificada para buscar fiduciais
    em imagens usando template matching, encapsulando o FiducialAligner do aoi_lib.

    Uso típico:
        service = TemplateMatchingService(threshold=70.0)

        # Adiciona templates
        service.add_template("Fiducial A", template_image, x=100, y=100)
        service.add_template("Fiducial B", template_image, x=200, y=100)

        # Busca em imagem
        results = service.find_all(image_gray)

        for result in results:
            if result.found:
                print(f"Encontrado em ({result.image_x}, {result.image_y}), "
                      f"score={result.similarity:.1f}%")
    """

    def __init__(
        self,
        threshold: float = 70.0,
        search_radius: int = 100,
        window_size: int = 50,
    ):
        """
        Inicializa serviço de template matching.

        Args:
            threshold: Score mínimo para aceitar match (0-100)
            search_radius: Raio de busca em pixels
            window_size: Tamanho da janela de captura do template
        """
        self.threshold = threshold
        self.search_radius = search_radius
        self.window_size = window_size

        # Aligner do aoi_lib (faz template matching)
        self._aligner = FiducialAligner()

        # Configura aligner com parâmetros padrão
        self._aligner.default_threshold = threshold
        self._aligner.default_search_radius = search_radius
        self._aligner.default_window_size = window_size

    def add_template(
        self,
        name: str,
        template_image: NDArray[np.uint8],
        x: float,
        y: float,
        search_radius: Optional[int] = None,
        threshold: Optional[float] = None,
    ) -> bool:
        """
        Adiciona um template fiducial.

        Args:
            name: Nome identificador do template
            template_image: Imagem do template (BGR ou grayscale)
            x: Posição X esperada (no Gerber)
            y: Posição Y esperada (no Gerber)
            search_radius: Raio de busca (padrão: do serviço)
            threshold: Score mínimo (padrão: do serviço)

        Returns:
            True se template adicionado com sucesso
        """
        # Adiciona fiducial
        fid = self._aligner.add_fiducial(name=name, gerber_x=x, gerber_y=y)

        # Configura parâmetros específicos
        if search_radius is not None:
            fid.search_radius = search_radius
        else:
            fid.search_radius = self.search_radius

        if threshold is not None:
            fid.threshold = threshold
        else:
            fid.threshold = self.threshold

        # Armazena imagem
        if len(template_image.shape) == 3:
            fid.template_bgr = template_image
            fid.template_gray = cv2.cvtColor(template_image, cv2.COLOR_BGR2GRAY)
        else:
            fid.template_gray = template_image
            fid.template_bgr = cv2.cvtColor(template_image, cv2.COLOR_GRAY2BGR)

        logger.info(
            f"Template '{name}' adicionado: "
            f"pos=({x:.1f}, {y:.1f}), "
            f"threshold={fid.threshold:.1f}%, "
            f"radius={fid.search_radius}px"
        )

        return True

    def find_one(
        self,
        template_name: str,
        image: NDArray[np.uint8],
        expected_x: Optional[float] = None,
        expected_y: Optional[float] = None,
    ) -> Optional[FiducialMatchResult]:
        """
        Busca um template específico na imagem.

        Args:
            template_name: Nome do template a buscar
            image: Imagem onde buscar (BGR ou grayscale)
            expected_x: Posição X esperada (para limitar busca)
            expected_y: Posição Y esperada (para limitar busca)

        Returns:
            FiducialMatchResult com resultado, ou None se template não existe
        """
        # Busca template
        fid = self._aligner.get_fiducial(template_name)
        if fid is None:
            logger.error(f"Template '{template_name}' não encontrado")
            return None

        # Converte para grayscale se necessário
        if len(image.shape) == 3:
            image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            image_gray = image

        # Busca fiducial
        result = self._aligner.find_fiducial(
            fiducial=fid,
            image_gray=image_gray,
            expected_x=int(expected_x) if expected_x is not None else None,
            expected_y=int(expected_y) if expected_y is not None else None,
        )

        return result

    def find_all(
        self,
        image: NDArray[np.uint8],
        expected_positions: Optional[List[Tuple[float, float]]] = None,
    ) -> List[FiducialMatchResult]:
        """
        Busca todos os templates na imagem.

        Args:
            image: Imagem onde buscar (BGR ou grayscale)
            expected_positions: Posições esperadas [(x, y), ...] para cada template

        Returns:
            Lista de FiducialMatchResult (um para cada template)
        """
        # Converte para grayscale se necessário
        if len(image.shape) == 3:
            image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            image_gray = image

        # Busca todos fiduciais
        results = self._aligner.find_all_fiducials(
            image_gray=image_gray,
            expected_positions=expected_positions,
        )

        # Log de resultados
        found_count = sum(1 for r in results if r.found)
        logger.info(
            f"Template matching: {found_count}/{len(results)} encontrados "
            f"(threshold={self.threshold}%)"
        )

        return results

    def find_all_as_matches(
        self,
        image: NDArray[np.uint8],
        expected_positions: Optional[List[Tuple[float, float]]] = None,
    ) -> List[FiducialMatch]:
        """
        Busca todos os templates e retorna como FiducialMatch.

        Formato compatível com AlignmentState.

        Args:
            image: Imagem onde buscar (BGR ou grayscale)
            expected_positions: Posições esperadas [(x, y), ...] para cada template

        Returns:
            Lista de FiducialMatch
        """
        results = self.find_all(image, expected_positions)

        matches = []
        for i, result in enumerate(results):
            fid = self._aligner.fiducials[i] if i < len(self._aligner.fiducials) else None

            match = FiducialMatch(
                template_id=i + 1,
                found=result.found,
                x=result.image_x,
                y=result.image_y,
                score=result.similarity,
                expected_x=fid.gerber_x if fid else 0.0,
                expected_y=fid.gerber_y if fid else 0.0,
            )
            matches.append(match)

        return matches

    def calculate_match_score(self, results: List[FiducialMatchResult]) -> float:
        """
        Calcula score geral de matching.

        Args:
            results: Lista de resultados de matching

        Returns:
            Score médio (0-100), ou 0.0 se nenhum encontrado
        """
        if not results:
            return 0.0

        found_results = [r for r in results if r.found]
        if not found_results:
            return 0.0

        avg_score = sum(r.similarity for r in found_results) / len(found_results)

        # Aplica penalidade por fiduciais não encontrados
        missing_count = len(results) - len(found_results)
        penalty = missing_count * 10

        return max(0.0, avg_score - penalty)

    def validate_match(
        self,
        result: FiducialMatchResult,
        min_score: Optional[float] = None,
        max_distance: Optional[float] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Valida se um resultado de matching é aceitável.

        Args:
            result: Resultado de matching
            min_score: Score mínimo (padrão: threshold do serviço)
            max_distance: Distância máxima da posição esperada (padrão: search_radius)

        Returns:
            (is_valid, error_message)
        """
        min_score = min_score or self.threshold
        max_distance = max_distance or self.search_radius

        # Verifica se encontrado
        if not result.found:
            return False, "Fiducial não encontrado"

        # Verifica score
        if result.similarity < min_score:
            return False, f"Score {result.similarity:.1f}% abaixo do mínimo {min_score}%"

        # Verifica distância da posição esperada
        if max_distance > 0:
            distance = (result.offset_x**2 + result.offset_y**2) ** 0.5
            if distance > max_distance:
                return False, f"Distância {distance:.1f}px acima do máximo {max_distance}px"

        return True, None

    def clear_templates(self) -> None:
        """Remove todos os templates."""
        self._aligner.fiducials.clear()
        logger.info("Todos os templates removidos")

    @property
    def template_count(self) -> int:
        """Retorna número de templates configurados."""
        return len(self._aligner.fiducials)

    @property
    def has_templates(self) -> bool:
        """Retorna True se há templates configurados."""
        return len(self._aligner.fiducials) > 0
