"""
Alignment Transform Service - Cálculos de Transformação Geométrica

Este serviço encapsula toda a lógica matemática para calcular e aplicar
transformações 2D entre sistemas de coordenadas (Gerber ↔ Imagem).

Responsabilidade única:
- Calcular translação entre pontos
- Calcular rotação entre vetores
- Calcular escala entre distâncias
- Compor transformações completas
- Aplicar transformações em pontos

Author: Claude Code (Sonnet 4.5)
Created: 2026-01-15
Phase: SOLID Refactoring Phase 5B
"""

import logging
from typing import List, Tuple, Optional, Dict
import numpy as np
import math

from .fiducial_models import (
    FiducialPoint,
    AlignmentTransform
)

logger = logging.getLogger(__name__)


class TransformError(Exception):
    """Exceção para erros de cálculo de transformação"""
    pass


class AlignmentTransformService:
    """
    Serviço para cálculo de transformações 2D de alinhamento.

    Este serviço é responsável por:
    - Calcular translação entre pares de pontos
    - Calcular rotação usando 2+ pontos
    - Calcular escala usando 2+ pontos
    - Compor transformação completa (translação + rotação + escala)
    - Aplicar transformação em pontos
    - Inverter transformação

    NOTA: Este serviço NÃO depende de PyQt6 ou OpenCV, sendo 100% testável.
    """

    def __init__(self):
        """Inicializa o serviço de transformação"""
        logger.debug("AlignmentTransformService inicializado")

    def calculate_translation(
        self,
        src_point: Tuple[float, float],
        dst_point: Tuple[float, float]
    ) -> Tuple[float, float]:
        """
        Calcula o vetor de translação entre dois pontos.

        Args:
            src_point: Ponto de origem (x, y)
            dst_point: Ponto de destino (x, y)

        Returns:
            (tx, ty): Vetor de translação
        """
        tx = dst_point[0] - src_point[0]
        ty = dst_point[1] - src_point[1]
        logger.debug(f"Translação: ({tx:.1f}, {ty:.1f})")
        return tx, ty

    def calculate_rotation(
        self,
        src_points: List[Tuple[float, float]],
        dst_points: List[Tuple[float, float]]
    ) -> float:
        """
        Calcula o ângulo de rotação médio entre duas listas de pontos.

        Usa o método de mínimos quadrados para estimar a rotação
        que melhor alinha os pontos de origem aos de destino.

        Args:
            src_points: Lista de pontos de origem [(x1, y1), (x2, y2), ...]
            dst_points: Lista de pontos de destino [(x1, y1), (x2, y2), ...]

        Returns:
            angle: Ângulo de rotação em graus (anti-horário)

        Raises:
            TransformError: Se não houver pontos suficientes
        """
        if len(src_points) < 2 or len(dst_points) < 2:
            raise TransformError("Precisa de pelo menos 2 pontos para calcular rotação")

        if len(src_points) != len(dst_points):
            raise TransformError("Número de pontos de origem e destino deve ser igual")

        # Calcular vetores entre pontos consecutivos
        n_points = len(src_points)

        angles = []
        for i in range(n_points - 1):
            # Vetor no sistema de origem
            src_dx = src_points[i + 1][0] - src_points[i][0]
            src_dy = src_points[i + 1][1] - src_points[i][1]
            src_angle = math.atan2(src_dy, src_dx)

            # Vetor no sistema de destino
            dst_dx = dst_points[i + 1][0] - dst_points[i][0]
            dst_dy = dst_points[i + 1][1] - dst_points[i][1]
            dst_angle = math.atan2(dst_dy, dst_dx)

            # Diferença de ângulo
            angle_diff = math.degrees(dst_angle - src_angle)
            angles.append(angle_diff)

        # Normalizar ângulos para [-180, 180]
        normalized_angles = []
        for angle in angles:
            while angle > 180:
                angle -= 360
            while angle < -180:
                angle += 360
            normalized_angles.append(angle)

        # Calcular média dos ângulos (considerando periodicidade)
        mean_angle = np.mean(normalized_angles)

        logger.debug(f"Rotação calculada: {mean_angle:.2f}° (média de {len(normalized_angles)} medições)")
        return float(mean_angle)

    def calculate_scale(
        self,
        src_points: List[Tuple[float, float]],
        dst_points: List[Tuple[float, float]]
    ) -> Tuple[float, float]:
        """
        Calcula o fator de escala médio entre duas listas de pontos.

        Args:
            src_points: Lista de pontos de origem [(x1, y1), (x2, y2), ...]
            dst_points: Lista de pontos de destino [(x1, y1), (x2, y2), ...]

        Returns:
            (scale_x, scale_y): Fatores de escala em X e Y

        Raises:
            TransformError: Se não houver pontos suficientes
        """
        if len(src_points) < 2 or len(dst_points) < 2:
            raise TransformError("Precisa de pelo menos 2 pontos para calcular escala")

        if len(src_points) != len(dst_points):
            raise TransformError("Número de pontos de origem e destino deve ser igual")

        # Calcular distâncias entre pontos consecutivos
        n_points = len(src_points)

        scales_x = []
        scales_y = []

        for i in range(n_points - 1):
            # Distância em X no sistema de origem
            src_dx = abs(src_points[i + 1][0] - src_points[i][0])
            # Distância em X no sistema de destino
            dst_dx = abs(dst_points[i + 1][0] - dst_points[i][0])

            # Escala em X
            if src_dx > 1e-6:  # Evitar divisão por zero
                scale_x = dst_dx / src_dx
                scales_x.append(scale_x)

            # Distância em Y no sistema de origem
            src_dy = abs(src_points[i + 1][1] - src_points[i][1])
            # Distância em Y no sistema de destino
            dst_dy = abs(dst_points[i + 1][1] - dst_points[i][1])

            # Escala em Y
            if src_dy > 1e-6:  # Evitar divisão por zero
                scale_y = dst_dy / src_dy
                scales_y.append(scale_y)

        if not scales_x or not scales_y:
            raise TransformError("Não foi possível calcular escala (pontos muito próximos)")

        mean_scale_x = np.mean(scales_x)
        mean_scale_y = np.mean(scales_y)

        logger.debug(
            f"Escala calculada: X={mean_scale_x:.4f}, Y={mean_scale_y:.4f} "
            f"(média de {len(scales_x)} medições)"
        )
        return float(mean_scale_x), float(mean_scale_y)

    def calculate_transform(
        self,
        src_points: List[Tuple[float, float]],
        dst_points: List[Tuple[float, float]]
    ) -> AlignmentTransform:
        """
        Calcula a transformação completa entre dois sistemas de coordenadas.

        A transformação é composta de:
        1. Translação: Usando o centróide dos pontos
        2. Rotação: Usando vetores entre pontos
        3. Escala: Usando distâncias entre pontos

        Args:
            src_points: Lista de pontos de origem [(x1, y1), (x2, y2), ...]
            dst_points: Lista de pontos de destino [(x1, y1), (x2, y2), ...]

        Returns:
            AlignmentTransform: Transformação calculada

        Raises:
            TransformError: Se não houver pontos suficientes ou erro no cálculo
        """
        if len(src_points) < 2 or len(dst_points) < 2:
            raise TransformError("Precisa de pelo menos 2 pontos para calcular transformação")

        if len(src_points) != len(dst_points):
            raise TransformError("Número de pontos de origem e destino deve ser igual")

        # 1. Calcular centróides
        src_centroid = (
            sum(p[0] for p in src_points) / len(src_points),
            sum(p[1] for p in src_points) / len(src_points)
        )
        dst_centroid = (
            sum(p[0] for p in dst_points) / len(dst_points),
            sum(p[1] for p in dst_points) / len(dst_points)
        )

        # 2. Calcular translação (entre centróides)
        tx, ty = self.calculate_translation(src_centroid, dst_centroid)

        # 3. Calcular rotação (usando pontos centrados no centróide)
        src_centered = [(p[0] - src_centroid[0], p[1] - src_centroid[1]) for p in src_points]
        dst_centered = [(p[0] - dst_centroid[0], p[1] - dst_centroid[1]) for p in dst_points]
        angle = self.calculate_rotation(src_centered, dst_centered)

        # 4. Calcular escala (usando pontos centrados)
        scale_x, scale_y = self.calculate_scale(src_centered, dst_centered)

        transform = AlignmentTransform(
            tx=tx,
            ty=ty,
            angle=angle,
            scale_x=scale_x,
            scale_y=scale_y
        )

        logger.info(
            f"Transformação calculada: tx={tx:.1f}, ty={ty:.1f}, "
            f"angle={angle:.2f}°, scale={scale_x:.4f}"
        )

        return transform

    def apply_transform(
        self,
        point: Tuple[float, float],
        transform: AlignmentTransform
    ) -> Tuple[float, float]:
        """
        Aplica uma transformação em um ponto.

        A ordem das operações é:
        1. Escala
        2. Rotação
        3. Translação

        Args:
            point: Ponto de origem (x, y)
            transform: Transformação a aplicar

        Returns:
            (x', y'): Ponto transformado
        """
        x, y = point

        # 1. Aplicar escala
        x_scaled = x * transform.scale_x
        y_scaled = y * transform.scale_y

        # 2. Aplicar rotação
        angle_rad = math.radians(transform.angle)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        x_rotated = x_scaled * cos_a - y_scaled * sin_a
        y_rotated = x_scaled * sin_a + y_scaled * cos_a

        # 3. Aplicar translação
        x_final = x_rotated + transform.tx
        y_final = y_rotated + transform.ty

        return (x_final, y_final)

    def inverse_transform(
        self,
        point: Tuple[float, float],
        transform: AlignmentTransform
    ) -> Tuple[float, float]:
        """
        Aplica a transformação inversa em um ponto.

        Útil para converter pontos do sistema de destino
        de volta para o sistema de origem.

        Args:
            point: Ponto no sistema de destino (x, y)
            transform: Transformação a inverter

        Returns:
            (x', y'): Ponto no sistema de origem
        """
        x, y = point

        # 1. Inverter translação
        x_translated = x - transform.tx
        y_translated = y - transform.ty

        # 2. Inverter rotação
        angle_rad = math.radians(-transform.angle)  # Ângulo negativo para inverter
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        x_unrotated = x_translated * cos_a - y_translated * sin_a
        y_unrotated = x_translated * sin_a + y_translated * cos_a

        # 3. Inverter escala
        x_final = x_unrotated / transform.scale_x if transform.scale_x != 0 else x_unrotated
        y_final = y_unrotated / transform.scale_y if transform.scale_y != 0 else y_unrotated

        return (x_final, y_final)

    def calculate_transform_from_fiducials(
        self,
        fiducials: List[FiducialPoint]
    ) -> Optional[AlignmentTransform]:
        """
        Calcula transformação a partir de uma lista de fiduciais.

        Args:
            fiducials: Lista de fiduciais com match realizado

        Returns:
            AlignmentTransform ou None se não for possível calcular
        """
        # Filtrar apenas fiduciais com match
        matched = [f for f in fiducials if f.has_match()]

        if len(matched) < 2:
            logger.warning(f"Pelo menos 2 fiduciais com match são necessários, got {len(matched)}")
            return None

        # Extrair pontos de origem (Gerber) e destino (Imagem)
        src_points = [(f.gerber_x, f.gerber_y) for f in matched]
        dst_points = [(f.matched_x, f.matched_y) for f in matched]

        try:
            return self.calculate_transform(src_points, dst_points)
        except TransformError as e:
            logger.error(f"Erro ao calcular transformação: {e}")
            return None

    def calculate_residual_error(
        self,
        src_points: List[Tuple[float, float]],
        dst_points: List[Tuple[float, float]],
        transform: AlignmentTransform
    ) -> Dict[str, float]:
        """
        Calcula o erro residual após aplicar a transformação.

        O erro residual é a distância média entre os pontos de destino
        e os pontos de origem transformados.

        Args:
            src_points: Lista de pontos de origem
            dst_points: Lista de pontos de destino
            transform: Transformação aplicada

        Returns:
            Dicionário com métricas de erro:
            - mean_error: Erro médio em pixels
            - max_error: Erro máximo em pixels
            - std_error: Desvio padrão do erro
        """
        if len(src_points) != len(dst_points):
            raise TransformError("Número de pontos deve ser igual")

        errors = []
        for src, dst in zip(src_points, dst_points):
            transformed = self.apply_transform(src, transform)
            error = math.sqrt(
                (transformed[0] - dst[0]) ** 2 +
                (transformed[1] - dst[1]) ** 2
            )
            errors.append(error)

        return {
            'mean_error': float(np.mean(errors)),
            'max_error': float(np.max(errors)),
            'std_error': float(np.std(errors))
        }
