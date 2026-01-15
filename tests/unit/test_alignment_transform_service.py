"""
Testes Unitários para AlignmentTransformService

Este módulo contém testes unitários para o serviço de transformações
geométricas, validando cálculos de translação, rotação e escala.

Author: Claude Code (Sonnet 4.5)
Created: 2026-01-15
Phase: SOLID Refactoring Phase 5B.2
"""

import sys
from pathlib import Path

# Adiciona diretório raiz ao sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
import numpy as np
import math

from aoi_lib.alignment_transform_service import (
    AlignmentTransformService,
    TransformError
)
from aoi_lib.fiducial_models import (
    FiducialPoint,
    AlignmentTransform
)


class TestAlignmentTransformService:
    """Testes para AlignmentTransformService"""

    def test_init(self):
        """Testa inicialização do serviço"""
        service = AlignmentTransformService()
        assert service is not None

    def test_calculate_translation_zero(self):
        """Testa cálculo de translação zero (mesmo ponto)"""
        service = AlignmentTransformService()

        tx, ty = service.calculate_translation(
            src_point=(10, 20),
            dst_point=(10, 20)
        )

        assert abs(tx) < 1e-6
        assert abs(ty) < 1e-6

    def test_calculate_translation_positive(self):
        """Testa cálculo de translação positiva"""
        service = AlignmentTransformService()

        tx, ty = service.calculate_translation(
            src_point=(0, 0),
            dst_point=(10, 20)
        )

        assert abs(tx - 10) < 1e-6
        assert abs(ty - 20) < 1e-6

    def test_calculate_translation_negative(self):
        """Testa cálculo de translação negativa"""
        service = AlignmentTransformService()

        tx, ty = service.calculate_translation(
            src_point=(20, 30),
            dst_point=(10, 10)
        )

        assert abs(tx - (-10)) < 1e-6
        assert abs(ty - (-20)) < 1e-6

    def test_calculate_rotation_one_point_fails(self):
        """Testa que rotação com 1 ponto lança exceção"""
        service = AlignmentTransformService()

        with pytest.raises(TransformError, match="pelo menos 2 pontos"):
            service.calculate_rotation(
                src_points=[(0, 0)],
                dst_points=[(10, 10)]
            )

    def test_calculate_rotation_no_rotation(self):
        """Testa cálculo de rotação zero (sem rotação)"""
        service = AlignmentTransformService()

        # Dois pontos alinhados horizontalmente, sem rotação
        src_points = [(0, 0), (10, 0)]
        dst_points = [(100, 100), (110, 100)]

        angle = service.calculate_rotation(src_points, dst_points)

        assert abs(angle) < 1.0  # Menos de 1 grau (permitindo erro numérico)

    def test_calculate_rotation_90_degrees(self):
        """Testa cálculo de rotação de 90 graus"""
        service = AlignmentTransformService()

        # Vetor horizontal (10, 0) → Vetor vertical (0, 10)
        src_points = [(0, 0), (10, 0)]
        dst_points = [(0, 0), (0, 10)]

        angle = service.calculate_rotation(src_points, dst_points)

        assert abs(angle - 90.0) < 1.0  # ~90 graus

    def test_calculate_rotation_negative_90_degrees(self):
        """Testa cálculo de rotação de -90 graus"""
        service = AlignmentTransformService()

        # Vetor horizontal (10, 0) → Vetor vertical (0, -10)
        src_points = [(0, 0), (10, 0)]
        dst_points = [(0, 0), (0, -10)]

        angle = service.calculate_rotation(src_points, dst_points)

        # Deve ser próximo de -90 ou 270 (ambos são equivalentes)
        assert abs(abs(angle) - 90.0) < 1.0

    def test_calculate_rotation_multiple_points(self):
        """Testa cálculo de rotação com múltiplos pontos"""
        service = AlignmentTransformService()

        # Quadrado rotacionado
        src_points = [(0, 0), (10, 0), (10, 10), (0, 10)]
        dst_points = [(0, 0), (0, 10), (-10, 10), (-10, 0)]  # Rotacionado 90°

        angle = service.calculate_rotation(src_points, dst_points)

        assert abs(angle - 90.0) < 5.0  # ~90 graus (permitindo maior erro)

    def test_calculate_rotation_unequal_points(self):
        """Testa que número diferente de pontos lança exceção"""
        service = AlignmentTransformService()

        with pytest.raises(TransformError, match="Número de pontos de origem e destino deve ser igual"):
            service.calculate_rotation(
                src_points=[(0, 0), (10, 0)],
                dst_points=[(0, 0), (20, 0), (30, 0)]  # 3 pontos vs 2
            )

    def test_calculate_scale_no_scale(self):
        """Testa cálculo de escala sem mudança (scale = 1.0)"""
        service = AlignmentTransformService()

        src_points = [(0, 0), (10, 0), (0, 10)]
        dst_points = [(100, 100), (110, 100), (100, 110)]

        scale_x, scale_y = service.calculate_scale(src_points, dst_points)

        assert abs(scale_x - 1.0) < 0.01
        assert abs(scale_y - 1.0) < 0.01

    def test_calculate_scale_double(self):
        """Testa cálculo de escala com dobramento (scale = 2.0)"""
        service = AlignmentTransformService()

        src_points = [(0, 0), (10, 0), (0, 10)]
        dst_points = [(0, 0), (20, 0), (0, 20)]  # 2x maior

        scale_x, scale_y = service.calculate_scale(src_points, dst_points)

        assert abs(scale_x - 2.0) < 0.01
        assert abs(scale_y - 2.0) < 0.01

    def test_calculate_scale_half(self):
        """Testa cálculo de escala com redução pela metade (scale = 0.5)"""
        service = AlignmentTransformService()

        src_points = [(0, 0), (10, 0), (0, 10)]
        dst_points = [(0, 0), (5, 0), (0, 5)]  # 0.5x

        scale_x, scale_y = service.calculate_scale(src_points, dst_points)

        assert abs(scale_x - 0.5) < 0.01
        assert abs(scale_y - 0.5) < 0.01

    def test_calculate_scale_anisotropic(self):
        """Testa cálculo de escala anisotrópica (diferente em X e Y)"""
        service = AlignmentTransformService()

        src_points = [(0, 0), (10, 0), (0, 10)]
        dst_points = [(0, 0), (20, 0), (0, 5)]  # 2x em X, 0.5x em Y

        scale_x, scale_y = service.calculate_scale(src_points, dst_points)

        assert abs(scale_x - 2.0) < 0.01
        assert abs(scale_y - 0.5) < 0.01

    def test_calculate_scale_one_point_fails(self):
        """Testa que escala com 1 ponto lança exceção"""
        service = AlignmentTransformService()

        with pytest.raises(TransformError, match="pelo menos 2 pontos"):
            service.calculate_scale(
                src_points=[(0, 0)],
                dst_points=[(10, 10)]
            )

    def test_calculate_scale_identical_points_fails(self):
        """Testa que pontos idênticos lança exceção"""
        service = AlignmentTransformService()

        with pytest.raises(TransformError, match="foi possível calcular escala"):
            service.calculate_scale(
                src_points=[(0, 0), (0, 0)],
                dst_points=[(10, 10), (10, 10)]
            )

    def test_calculate_transform_two_points(self):
        """Testa cálculo de transformação completa com 2 pontos"""
        service = AlignmentTransformService()

        src_points = [(0, 0), (10, 10)]
        dst_points = [(100, 100), (120, 120)]  # Translação + escala

        transform = service.calculate_transform(src_points, dst_points)

        assert transform is not None
        # Translação do centróide
        assert abs(transform.tx - 105) < 1.0  # Centróide de src (5,5) → dst (110,110)
        # Escala aproximada
        assert abs(transform.scale_x - 2.0) < 0.1

    def test_calculate_transform_multiple_points(self):
        """Testa cálculo de transformação com múltiplos pontos"""
        service = AlignmentTransformService()

        # Quadrado
        src_points = [(0, 0), (10, 0), (10, 10), (0, 10)]
        # Transladado e rotacionado
        dst_points = [(100, 100), (100, 120), (80, 120), (80, 100)]

        transform = service.calculate_transform(src_points, dst_points)

        assert transform is not None
        assert isinstance(transform, AlignmentTransform)

    def test_calculate_transform_insufficient_points(self):
        """Testa que poucos pontos lança exceção"""
        service = AlignmentTransformService()

        with pytest.raises(TransformError, match="pelo menos 2 pontos"):
            service.calculate_transform(
                src_points=[(0, 0)],
                dst_points=[(10, 10)]
            )

    def test_apply_identity_transform(self):
        """Testa aplicação de transformação identidade"""
        service = AlignmentTransformService()

        transform = AlignmentTransform(
            tx=0, ty=0, angle=0, scale_x=1, scale_y=1
        )

        result = service.apply_transform((10, 20), transform)

        assert abs(result[0] - 10) < 1e-6
        assert abs(result[1] - 20) < 1e-6

    def test_apply_translation_only(self):
        """Testa aplicação de apenas translação"""
        service = AlignmentTransformService()

        transform = AlignmentTransform(
            tx=5, ty=10, angle=0, scale_x=1, scale_y=1
        )

        result = service.apply_transform((10, 20), transform)

        assert abs(result[0] - 15) < 1e-6  # 10 + 5
        assert abs(result[1] - 30) < 1e-6  # 20 + 10

    def test_apply_scale_only(self):
        """Testa aplicação de apenas escala"""
        service = AlignmentTransformService()

        transform = AlignmentTransform(
            tx=0, ty=0, angle=0, scale_x=2, scale_y=3
        )

        result = service.apply_transform((10, 20), transform)

        assert abs(result[0] - 20) < 1e-6  # 10 * 2
        assert abs(result[1] - 60) < 1e-6  # 20 * 3

    def test_apply_rotation_90_degrees(self):
        """Testa aplicação de rotação de 90 graus"""
        service = AlignmentTransformService()

        transform = AlignmentTransform(
            tx=0, ty=0, angle=90, scale_x=1, scale_y=1
        )

        # Ponto (10, 0) rotacionado 90° → (0, 10)
        result = service.apply_transform((10, 0), transform)

        assert abs(result[0]) < 1e-6      # ~0
        assert abs(result[1] - 10) < 1e-6  # ~10

    def test_apply_combined_transform(self):
        """Testa aplicação de transformação combinada"""
        service = AlignmentTransformService()

        transform = AlignmentTransform(
            tx=5, ty=10, angle=0, scale_x=2, scale_y=2
        )

        result = service.apply_transform((10, 20), transform)

        # (10 * 2) + 5 = 25
        # (20 * 2) + 10 = 50
        assert abs(result[0] - 25) < 1e-6
        assert abs(result[1] - 50) < 1e-6

    def test_inverse_transform_identity(self):
        """Testa inversão de transformação identidade"""
        service = AlignmentTransformService()

        transform = AlignmentTransform(
            tx=0, ty=0, angle=0, scale_x=1, scale_y=1
        )

        result = service.inverse_transform((10, 20), transform)

        assert abs(result[0] - 10) < 1e-6
        assert abs(result[1] - 20) < 1e-6

    def test_inverse_transform_translation(self):
        """Testa inversão de translação"""
        service = AlignmentTransformService()

        transform = AlignmentTransform(
            tx=5, ty=10, angle=0, scale_x=1, scale_y=1
        )

        # Aplicar direta
        direct = service.apply_transform((10, 20), transform)
        # Aplicar inversa
        inverse = service.inverse_transform(direct, transform)

        # Deve voltar ao original
        assert abs(inverse[0] - 10) < 1e-6
        assert abs(inverse[1] - 20) < 1e-6

    def test_inverse_transform_scale(self):
        """Testa inversão de escala"""
        service = AlignmentTransformService()

        transform = AlignmentTransform(
            tx=0, ty=0, angle=0, scale_x=2, scale_y=3
        )

        # Aplicar direta
        direct = service.apply_transform((10, 20), transform)
        # Aplicar inversa
        inverse = service.inverse_transform(direct, transform)

        # Deve voltar ao original
        assert abs(inverse[0] - 10) < 1e-6
        assert abs(inverse[1] - 20) < 1e-6

    def test_inverse_transform_combined(self):
        """Testa inversão de transformação combinada"""
        service = AlignmentTransformService()

        transform = AlignmentTransform(
            tx=5, ty=10, angle=45, scale_x=2, scale_y=2
        )

        # Aplicar direta
        direct = service.apply_transform((10, 20), transform)
        # Aplicar inversa
        inverse = service.inverse_transform(direct, transform)

        # Deve voltar próximo ao original (permitindo erro numérico)
        assert abs(inverse[0] - 10) < 0.1
        assert abs(inverse[1] - 20) < 0.1

    def test_calculate_transform_from_fiducials_success(self):
        """Testa cálculo de transformação a partir de fiduciais"""
        service = AlignmentTransformService()

        fiducials = [
            FiducialPoint(
                gerber_x=0, gerber_y=0,
                matched_x=100, matched_y=100,
                is_matched=True
            ),
            FiducialPoint(
                gerber_x=10, gerber_y=10,
                matched_x=120, matched_y=120,
                is_matched=True
            )
        ]

        transform = service.calculate_transform_from_fiducials(fiducials)

        assert transform is not None
        assert isinstance(transform, AlignmentTransform)

    def test_calculate_transform_from_fiducials_insufficient(self):
        """Testa que fiduciais insuficientes retorna None"""
        service = AlignmentTransformService()

        fiducials = [
            FiducialPoint(
                gerber_x=0, gerber_y=0,
                matched_x=100, matched_y=100,
                is_matched=True
            )
        ]

        transform = service.calculate_transform_from_fiducials(fiducials)

        assert transform is None

    def test_calculate_residual_error_perfect(self):
        """Testa cálculo de erro residual com transformação perfeita"""
        service = AlignmentTransformService()

        src_points = [(0, 0), (10, 10)]
        dst_points = [(100, 100), (110, 110)]

        transform = service.calculate_transform(src_points, dst_points)

        error = service.calculate_residual_error(src_points, dst_points, transform)

        assert error['mean_error'] < 1.0  # Erro médio < 1 pixel
        assert error['max_error'] < 1.0   # Erro máximo < 1 pixel

    def test_calculate_residual_error_noisy(self):
        """Testa cálculo de erro residual com ruído"""
        service = AlignmentTransformService()

        src_points = [(0, 0), (10, 10), (20, 20)]
        dst_points = [(100, 100), (111, 110), (120, 121)]  # Com ruído

        transform = service.calculate_transform(src_points, dst_points)

        error = service.calculate_residual_error(src_points, dst_points, transform)

        # Deve ter algum erro
        assert error['mean_error'] > 0
        assert error['std_error'] >= 0


if __name__ == '__main__':
    # Executar testes
    pytest.main([__file__, '-v', '--tb=short'])
