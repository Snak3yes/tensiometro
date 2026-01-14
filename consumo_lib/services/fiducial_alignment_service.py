"""
Fiducial Alignment Service - Serviço de Alinhamento Fiducial

Este módulo contém a lógica de negócio para alinhamento fiducial entre
Gerber e mosaico capturado, separada da UI.

Responsabilidades:
    - Orquestrar alinhamento fiducial completo
    - Validar transformações calculadas
    - Converter resultados para AlignmentState
    - Fornecer métodos de refino de transformação

Author: Claude Sonnet 4.5
Date: 2026-01-14
Track: solid_refactoring_phase2_20260114 (Phase 3 - Alignment Widget Refactoring)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
from numpy.typing import NDArray

from aoi_lib.fiducial_alignment import (
    FiducialAligner,
    FiducialTemplate,
    FiducialMatchResult,
    AlignmentTransform,
)
from consumo_lib.models.alignment_state import (
    AlignmentState,
    FiducialMatch,
    AlignmentMetrics,
)

logger = logging.getLogger(__name__)


class AlignmentResult:
    """
    Resultado completo do alinhamento fiducial.

    Atributos:
        success: Se alinhamento foi bem-sucedido
        state: Estado do alinhamento (AlignmentState)
        error: Mensagem de erro (se houver)
        matched_positions: Posições dos fiduciais encontrados [(x, y), ...]
        scores: Scores de matching para cada fiducial
    """

    def __init__(
        self,
        success: bool = False,
        state: Optional[AlignmentState] = None,
        error: Optional[str] = None,
        matched_positions: Optional[List[Tuple[float, float]]] = None,
        scores: Optional[List[float]] = None,
    ):
        self.success = success
        self.state = state or AlignmentState()
        self.error = error
        self.matched_positions = matched_positions or []
        self.scores = scores or []

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "success": self.success,
            "state": self.state.to_dict() if self.state else {},
            "error": self.error,
            "matched_positions": self.matched_positions,
            "scores": self.scores,
        }


class FiducialAlignmentService:
    """
    Serviço de alinhamento fiducial.

    Este serviço orquestra o processo completo de alinhamento fiducial:
    1. Prepara templates fiduciais
    2. Busca fiduciais na imagem (template matching)
    3. Calcula transformação
    4. Valida resultados
    5. Retorna estado completo

    Uso típico:
        service = FiducialAlignmentService()
        result = service.align(
            templates=templates,
            mosaic_image=mosaic_image,
            expected_positions=[(x1, y1), (x2, y2)]
        )

        if result.success:
            transform = result.state.to_aoi_lib_format()
            # Aplicar transformação ao Gerber
    """

    def __init__(
        self,
        min_score_threshold: float = 70.0,
        min_fiducials_required: int = 2,
        scale_gerber_to_pixels: float = 1.0,
    ):
        """
        Inicializa serviço de alinhamento.

        Args:
            min_score_threshold: Score mínimo para aceitar match (0-100)
            min_fiducials_required: Mínimo de fiduciais para calcular transformação
            scale_gerber_to_pixels: Fator de conversão Gerber (mm) → pixels
        """
        self.min_score_threshold = min_score_threshold
        self.min_fiducials_required = min_fiducials_required
        self.scale_gerber_to_pixels = scale_gerber_to_pixels

        # Aligner do aoi_lib (faz template matching e cálculo de transformação)
        self._aligner = FiducialAligner()

        # Configura aligner com parâmetros padrão
        self._aligner.default_threshold = min_score_threshold

    def prepare_templates(
        self,
        templates_data: List[Dict[str, Any]],
    ) -> bool:
        """
        Prepara templates fiduciais para alinhamento.

        Args:
            templates_data: Lista de dicionários com dados dos templates:
                [{
                    'image': np.ndarray (BGR),
                    'x': float (posição Gerber X),
                    'y': float (posição Gerber Y),
                    'z': float (posição Z, padrão 0.0),
                    'window_size': int (tamanho janela, padrão 50),
                    'search_radius': int (raio busca, padrão 100),
                    'threshold': float (score mínimo, padrão min_score_threshold)
                }, ...]

        Returns:
            True se templates preparados com sucesso
        """
        self._aligner.fiducials.clear()

        for i, template_data in enumerate(templates_data):
            # Extrai dados
            image = template_data.get("image")
            gerber_x = template_data.get("x", 0.0)
            gerber_y = template_data.get("y", 0.0)
            window_size = template_data.get("window_size", 50)
            search_radius = template_data.get("search_radius", 100)
            threshold = template_data.get("threshold", self.min_score_threshold)

            if image is None:
                logger.error(f"Template {i}: imagem não fornecida")
                return False

            # Cria template
            fid = self._aligner.add_fiducial(
                name=f"Fiducial_{i+1}",
                gerber_x=gerber_x,
                gerber_y=gerber_y,
            )

            # Configura parâmetros
            fid.window_size = window_size
            fid.search_radius = search_radius
            fid.threshold = threshold

            # Armazena imagem
            if len(image.shape) == 3:
                fid.template_bgr = image
                fid.template_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                fid.template_gray = image
                fid.template_bgr = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

            logger.info(
                f"Template {i+1} preparado: "
                f"pos=({gerber_x:.1f}, {gerber_y:.1f}), "
                f"size={window_size}, "
                f"radius={search_radius}"
            )

        return len(self._aligner.fiducials) >= self.min_fiducials_required

    def align(
        self,
        templates: List[Dict[str, Any]],
        mosaic_image: NDArray[np.uint8],
        expected_positions: Optional[List[Tuple[float, float]]] = None,
    ) -> AlignmentResult:
        """
        Executa alinhamento fiducial completo.

        Args:
            templates: Lista de templates (mesmo formato que prepare_templates)
            mosaic_image: Imagem do mosaico (BGR ou grayscale)
            expected_positions: Posições esperadas [(x, y), ...] para limitar busca

        Returns:
            AlignmentResult com estado completo
        """
        # Prepara templates
        if not self.prepare_templates(templates):
            return AlignmentResult(
                success=False,
                error=f"Menos de {self.min_fiducials_required} templates válidos",
            )

        # Converte para grayscale se necessário
        if len(mosaic_image.shape) == 3:
            image_gray = cv2.cvtColor(mosaic_image, cv2.COLOR_BGR2GRAY)
        else:
            image_gray = mosaic_image

        # Busca fiduciais
        match_results = self._aligner.find_all_fiducials(
            image_gray=image_gray,
            expected_positions=expected_positions,
        )

        # Conta fiduciais encontrados
        found_count = sum(1 for r in match_results if r.found)

        logger.info(
            f"Busca fiducial: {found_count}/{len(match_results)} encontrados "
            f"(threshold={self.min_score_threshold}%)"
        )

        # Verifica se encontrou suficiente
        if found_count < self.min_fiducials_required:
            return AlignmentResult(
                success=False,
                error=f"Apenas {found_count}/{len(match_results)} fiduciais encontrados",
            )

        # Calcula transformação
        transform = self._aligner.calculate_transform_from_fiducials(
            scale_gerber_to_pixels=self.scale_gerber_to_pixels,
        )

        if transform is None:
            return AlignmentResult(
                success=False,
                error="Não foi possível calcular transformação",
            )

        # Converte resultados para AlignmentState
        state = self._convert_to_alignment_state(
            transform=transform,
            match_results=match_results,
            templates=templates,
        )

        # Extrai posições e scores
        matched_positions = [(r.image_x, r.image_y) for r in match_results]
        scores = [r.similarity for r in match_results]

        logger.info(
            f"Alinhamento bem-sucedido: "
            f"score={state.score:.1f}%, "
            f"tx={transform.tx:.1f}, ty={transform.ty:.1f}, "
            f"angle={transform.angle:.2f}°, scale={transform.scale_x:.4f}"
        )

        return AlignmentResult(
            success=True,
            state=state,
            matched_positions=matched_positions,
            scores=scores,
        )

    def _convert_to_alignment_state(
        self,
        transform: AlignmentTransform,
        match_results: List[FiducialMatchResult],
        templates: List[Dict[str, Any]],
    ) -> AlignmentState:
        """
        Converte resultados do aligner para AlignmentState.

        Args:
            transform: Transformação calculada
            match_results: Resultados de matching
            templates: Templates originais (para posições esperadas)

        Returns:
            AlignmentState preenchido
        """
        # Converte FiducialMatchResult → FiducialMatch
        fiducial_matches = []
        for i, match_result in enumerate(match_results):
            template = templates[i] if i < len(templates) else {}
            expected_x = template.get("x", 0.0)
            expected_y = template.get("y", 0.0)

            fid_match = FiducialMatch(
                template_id=i + 1,
                found=match_result.found,
                x=match_result.image_x,
                y=match_result.image_y,
                score=match_result.similarity,
                expected_x=expected_x,
                expected_y=expected_y,
            )
            fiducial_matches.append(fid_match)

        # Cria estado com transformação
        state = AlignmentState(
            tx=transform.tx,
            ty=transform.ty,
            angle=transform.angle,
            scale=transform.scale_x,
            fiducial_matches=fiducial_matches,
        )

        # Métricas são calculadas automaticamente em __post_init__
        return state

    def validate_transform(
        self,
        state: AlignmentState,
        min_score: Optional[float] = None,
        min_fiducials: Optional[int] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Valida se transformação é aceitável.

        Args:
            state: Estado do alinhamento
            min_score: Score mínimo (padrão: min_score_threshold)
            min_fiducials: Mínimo de fiduciais (padrão: min_fiducials_required)

        Returns:
            (is_valid, error_message)
        """
        min_score = min_score or self.min_score_threshold
        min_fiducials = min_fiducials or self.min_fiducials_required

        # Verifica score
        if state.score < min_score:
            return False, f"Score {state.score:.1f}% abaixo do mínimo {min_score}%"

        # Verifica fiduciais encontrados
        found_count = state.metrics.fiducials_found if state.metrics else 0
        if found_count < min_fiducials:
            return False, f"Apenas {found_count} fiduciais encontrados (mínimo: {min_fiducials})"

        # Verifica se estado é válido
        if not state.is_valid:
            return False, "Transformação não é aceitável segundo métricas"

        return True, None

    def refine_transform(
        self,
        state: AlignmentState,
        mosaic_image: NDArray[np.uint8],
        templates: List[Dict[str, Any]],
        search_radius_multiplier: float = 0.5,
    ) -> Optional[AlignmentState]:
        """
        Refina transformação com busca adicional.

        Reduz o raio de busca e tenta melhorar a precisão do alinhamento.

        Args:
            state: Estado atual do alinhamento
            mosaic_image: Imagem do mosaico
            templates: Templates fiduciais
            search_radius_multiplier: Multiplicador do raio (0.5 = metade do raio)

        Returns:
            Novo AlignmentState refinado, ou None se falhou
        """
        if not state.has_transformation:
            logger.warning("Sem transformação para refinar")
            return None

        # Calcula posições esperadas a partir da transformação atual
        expected_positions = []
        for template in templates:
            gerber_x = template.get("x", 0.0) * self.scale_gerber_to_pixels
            gerber_y = template.get("y", 0.0) * self.scale_gerber_to_pixels

            # Aplica transformação atual
            transformed = state.to_aoi_lib_format()
            tx = transformed["tx"]
            ty = transformed["ty"]
            angle = transformed["angle"]
            scale = transformed["scale"]

            # Aplica rotação e escala
            cos_a = np.cos(np.radians(angle))
            sin_a = np.sin(np.radians(angle))

            x_rotated = scale * (gerber_x * cos_a - gerber_y * sin_a)
            y_rotated = scale * (gerber_x * sin_a + gerber_y * cos_a)

            # Adiciona translação
            expected_x = x_rotated + tx
            expected_y = y_rotated + ty

            expected_positions.append((expected_x, expected_y))

        # Reduz raio de busca
        refined_templates = []
        for template in templates:
            refined = template.copy()
            current_radius = refined.get("search_radius", 100)
            refined["search_radius"] = int(current_radius * search_radius_multiplier)
            refined_templates.append(refined)

        # Executa alinhamento refinado
        result = self.align(
            templates=refined_templates,
            mosaic_image=mosaic_image,
            expected_positions=expected_positions,
        )

        if result.success:
            logger.info(f"Transformação refinada: score {result.state.score:.1f}%")
            return result.state
        else:
            logger.warning(f"Refinamento falhou: {result.error}")
            return None

    def estimate_transform_from_two_points(
        self,
        point1_gerber: Tuple[float, float],
        point1_image: Tuple[float, float],
        point2_gerber: Tuple[float, float],
        point2_image: Tuple[float, float],
        scale_gerber_to_pixels: float = 1.0,
    ) -> Optional[AlignmentTransform]:
        """
        Estima transformação a partir de apenas 2 pontos correspondentes.

        Útil para alinhamento manual rápido onde usuário marca 2 pontos.

        Args:
            point1_gerber: Primeiro ponto no Gerber (x, y) em mm
            point1_image: Primeiro ponto na imagem (x, y) em pixels
            point2_gerber: Segundo ponto no Gerber (x, y) em mm
            point2_image: Segundo ponto na imagem (x, y) em pixels
            scale_gerber_to_pixels: Conversão Gerber → pixels

        Returns:
            AlignmentTransform estimada, ou None se falhou
        """
        # Converte Gerber para pixels
        g1x = point1_gerber[0] * scale_gerber_to_pixels
        g1y = point1_gerber[1] * scale_gerber_to_pixels
        g2x = point2_gerber[0] * scale_gerber_to_pixels
        g2y = point2_gerber[1] * scale_gerber_to_pixels

        gerber_points = [(g1x, g1y), (g2x, g2y)]
        image_points = [point1_image, point2_image]

        transform = self._aligner.calculate_transform(gerber_points, image_points)

        if transform:
            logger.info(
                f"Transformação estimada de 2 pontos: "
                f"tx={transform.tx:.1f}, ty={transform.ty:.1f}, "
                f"angle={transform.angle:.2f}°, scale={transform.scale_x:.4f}"
            )

        return transform
