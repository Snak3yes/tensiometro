"""
Testes Unitários para Alignment State Model

Este módulo contém testes unitários para os modelos de estado do alinhamento:
- FiducialMatch
- AlignmentMetrics
- AlignmentState

Author: Claude Sonnet 4.5
Date: 2026-01-14
Track: solid_refactoring_phase2_20260114 (Phase 3 - Alignment Widget Refactoring)
"""

import pytest
from consumo_lib.models.alignment_state import (
    FiducialMatch,
    AlignmentMetrics,
    AlignmentState,
)


class TestFiducialMatch:
    """Testes para FiducialMatch."""

    def test_create_match_found(self):
        """Testa criação de match encontrado."""
        # Arrange & Act
        match = FiducialMatch(
            template_id=1,
            found=True,
            x=100.0,
            y=200.0,
            score=95.0,
            expected_x=105.0,
            expected_y=198.0
        )

        # Assert
        assert match.template_id == 1
        assert match.found is True
        assert match.x == 100.0
        assert match.y == 200.0
        assert match.score == 95.0
        assert match.error_x == -5.0  # 100 - 105
        assert match.error_y == 2.0   # 200 - 198

    def test_create_match_not_found(self):
        """Testa criação de match não encontrado."""
        # Arrange & Act
        match = FiducialMatch(
            template_id=2,
            found=False,
            expected_x=50.0,
            expected_y=50.0
        )

        # Assert
        assert match.found is False
        assert match.x == 0.0
        assert match.y == 0.0
        assert match.score == 0.0
        assert match.error_x == 0.0
        assert match.error_y == 0.0

    def test_error_magnitude(self):
        """Testa cálculo de magnitude do erro."""
        # Arrange
        match = FiducialMatch(
            template_id=1,
            found=True,
            x=103.0,
            y=104.0,
            expected_x=100.0,
            expected_y=100.0
        )

        # Act & Assert
        # magnitude = sqrt(3^2 + 4^2) = 5
        assert match.error_magnitude == 5.0

    def test_serialization(self):
        """Testa serialização para dict."""
        # Arrange
        match = FiducialMatch(
            template_id=1,
            found=True,
            x=100.0,
            y=200.0,
            score=95.0
        )

        # Act
        data = match.to_dict()
        match2 = FiducialMatch.from_dict(data)

        # Assert
        assert match2.template_id == match.template_id
        assert match2.found == match.found
        assert match2.x == match.x
        assert match2.y == match.y
        assert match2.score == match.score


class TestAlignmentMetrics:
    """Testes para AlignmentMetrics."""

    def test_create_metrics(self):
        """Testa criação de métricas."""
        # Arrange & Act
        metrics = AlignmentMetrics(
            overall_score=85.0,
            mean_error=2.5,
            max_error=5.0,
            std_error=1.2,
            fiducials_found=3,
            fiducials_total=3,
            is_acceptable=True
        )

        # Assert
        assert metrics.overall_score == 85.0
        assert metrics.mean_error == 2.5
        assert metrics.max_error == 5.0
        assert metrics.std_error == 1.2
        assert metrics.fiducials_found == 3
        assert metrics.fiducials_total == 3
        assert metrics.is_acceptable is True

    def test_success_rate(self):
        """Testa cálculo de taxa de sucesso."""
        # Arrange & Act
        metrics = AlignmentMetrics(
            fiducials_found=3,
            fiducials_total=4
        )

        # Assert
        assert metrics.success_rate == 0.75  # 3/4

    def test_from_matches_all_found(self):
        """Testa cálculo de métricas com todos fiduciais encontrados."""
        # Arrange
        matches = [
            FiducialMatch(
                template_id=1,
                found=True,
                x=100.0,
                y=100.0,
                score=90.0,
                expected_x=100.0,
                expected_y=100.0
            ),
            FiducialMatch(
                template_id=2,
                found=True,
                x=200.0,
                y=200.0,
                score=95.0,
                expected_x=200.0,
                expected_y=200.0
            )
        ]

        # Act
        metrics = AlignmentMetrics.from_matches(matches, min_score_threshold=70.0)

        # Assert
        assert metrics.fiducials_found == 2
        assert metrics.fiducials_total == 2
        assert metrics.overall_score == 92.5  # (90 + 95) / 2
        assert metrics.mean_error == 0.0
        assert metrics.max_error == 0.0
        assert metrics.std_error == 0.0
        assert metrics.is_acceptable is True

    def test_from_matches_partial_found(self):
        """Testa cálculo com fiduciais parcialmente encontrados."""
        # Arrange
        matches = [
            FiducialMatch(
                template_id=1,
                found=True,
                x=105.0,
                y=100.0,
                score=85.0,
                expected_x=100.0,
                expected_y=100.0
            ),
            FiducialMatch(
                template_id=2,
                found=False,
                expected_x=200.0,
                expected_y=200.0
            )
        ]

        # Act
        metrics = AlignmentMetrics.from_matches(matches, min_score_threshold=70.0)

        # Assert
        assert metrics.fiducials_found == 1
        assert metrics.fiducials_total == 2
        assert metrics.overall_score == 75.0  # 85 - 10 (penalty)
        assert metrics.mean_error == 5.0  # |105 - 100|
        assert metrics.max_error == 5.0
        assert metrics.is_acceptable is True  # 1 de 2 encontrado, score ok

    def test_from_matches_none_found(self):
        """Testa cálculo quando nenhum fiducial encontrado."""
        # Arrange
        matches = [
            FiducialMatch(
                template_id=1,
                found=False,
                expected_x=100.0,
                expected_y=100.0
            ),
            FiducialMatch(
                template_id=2,
                found=False,
                expected_x=200.0,
                expected_y=200.0
            )
        ]

        # Act
        metrics = AlignmentMetrics.from_matches(matches, min_score_threshold=70.0)

        # Assert
        assert metrics.fiducials_found == 0
        assert metrics.fiducials_total == 2
        assert metrics.overall_score == 0.0
        assert metrics.is_acceptable is False

    def test_from_matches_empty(self):
        """Testa cálculo com lista vazia."""
        # Arrange & Act
        metrics = AlignmentMetrics.from_matches([], min_score_threshold=70.0)

        # Assert
        assert metrics.fiducials_found == 0
        assert metrics.fiducials_total == 0
        assert metrics.overall_score == 0.0
        assert metrics.is_acceptable is False

    def test_serialization(self):
        """Testa serialização de métricas."""
        # Arrange
        metrics = AlignmentMetrics(
            overall_score=85.0,
            fiducials_found=2,
            fiducials_total=2
        )

        # Act
        data = metrics.to_dict()
        metrics2 = AlignmentMetrics.from_dict(data)

        # Assert
        assert metrics2.overall_score == metrics.overall_score
        assert metrics2.fiducials_found == metrics.fiducials_found
        assert metrics2.fiducials_total == metrics.fiducials_total


class TestAlignmentState:
    """Testes para AlignmentState."""

    def test_create_default(self):
        """Testa criação de estado padrão."""
        # Arrange & Act
        state = AlignmentState()

        # Assert
        assert state.tx == 0.0
        assert state.ty == 0.0
        assert state.angle == 0.0
        assert state.scale == 1.0
        assert state.opacity == 0.5
        assert state.zoom == 1.0
        assert state.score == 0.0
        assert state.fiducials_found is False
        assert len(state.fiducial_matches) == 0
        assert state.is_valid is False
        assert state.timestamp is not None

    def test_create_with_transform(self):
        """Testa criação com transformação."""
        # Arrange & Act
        state = AlignmentState(
            tx=10.0,
            ty=20.0,
            angle=5.0,
            scale=1.1
        )

        # Assert
        assert state.tx == 10.0
        assert state.ty == 20.0
        assert state.angle == 5.0
        assert state.scale == 1.1

    def test_reset_transform(self):
        """Testa reset de transformação."""
        # Arrange
        state = AlignmentState(tx=10.0, ty=20.0, angle=5.0, scale=1.1)

        # Act
        state.reset_transform()

        # Assert
        assert state.tx == 0.0
        assert state.ty == 0.0
        assert state.angle == 0.0
        assert state.scale == 1.0

    def test_update_from_transform_partial(self):
        """Testa atualização parcial de transformação."""
        # Arrange
        state = AlignmentState(tx=0.0, ty=0.0, angle=0.0, scale=1.0)

        # Act - atualiza apenas tx
        state.update_from_transform(tx=10.0)

        # Assert
        assert state.tx == 10.0
        assert state.ty == 0.0  # Mantido
        assert state.angle == 0.0  # Mantido
        assert state.scale == 1.0  # Mantido

    def test_update_from_transform_full(self):
        """Testa atualização completa de transformação."""
        # Arrange
        state = AlignmentState()

        # Act
        state.update_from_transform(
            tx=10.0,
            ty=20.0,
            angle=5.0,
            scale=1.1
        )

        # Assert
        assert state.tx == 10.0
        assert state.ty == 20.0
        assert state.angle == 5.0
        assert state.scale == 1.1

    def test_update_matches(self):
        """Testa atualização de matches."""
        # Arrange
        matches = [
            FiducialMatch(
                template_id=1,
                found=True,
                x=100.0,
                y=100.0,
                score=90.0,
                expected_x=100.0,
                expected_y=100.0
            )
        ]
        state = AlignmentState()

        # Act
        state.update_matches(matches)

        # Assert
        assert len(state.fiducial_matches) == 1
        assert state.fiducials_found is True
        assert state.score == 90.0
        assert state.metrics is not None
        assert state.metrics.overall_score == 90.0

    def test_has_transformation_true(self):
        """Testa detecção de transformação existente."""
        # Arrange & Act
        state = AlignmentState(tx=10.0)

        # Assert
        assert state.has_transformation is True

    def test_has_transformation_false(self):
        """Testa detecção de transformação inexistente."""
        # Arrange & Act
        state = AlignmentState()

        # Assert
        assert state.has_transformation is False

    def test_transform_summary(self):
        """Testa resumo de transformação."""
        # Arrange & Act
        state1 = AlignmentState()
        state2 = AlignmentState(tx=10.0, ty=20.0)
        state3 = AlignmentState(angle=5.0)
        state4 = AlignmentState(scale=1.1)

        # Assert
        assert "Sem transformação" in state1.transform_summary
        assert "Translação: (10.0, 20.0)" in state2.transform_summary
        assert "Rotação: 5.00°" in state3.transform_summary
        assert "Escala: 1.1000x" in state4.transform_summary

    def test_serialization(self):
        """Testa serialização completa de estado."""
        # Arrange
        matches = [
            FiducialMatch(
                template_id=1,
                found=True,
                x=100.0,
                y=100.0,
                score=90.0,
                expected_x=100.0,
                expected_y=100.0
            )
        ]
        state = AlignmentState(
            tx=10.0,
            ty=20.0,
            fiducial_matches=matches
        )

        # Act
        data = state.to_dict()
        state2 = AlignmentState.from_dict(data)

        # Assert
        assert state2.tx == state.tx
        assert state2.ty == state.ty
        assert len(state2.fiducial_matches) == 1
        assert state2.fiducial_matches[0].template_id == 1

    def test_to_aoi_lib_format(self):
        """Testa conversão para formato aoi_lib."""
        # Arrange
        state = AlignmentState(tx=10.0, ty=20.0, angle=5.0, scale=1.1)

        # Act
        data = state.to_aoi_lib_format()

        # Assert
        assert data['tx'] == 10.0
        assert data['ty'] == 20.0
        assert data['angle'] == 5.0
        assert data['scale'] == 1.1

    def test_from_aoi_lib_format(self):
        """Testa criação a partir de formato aoi_lib."""
        # Arrange
        transform = {'tx': 10.0, 'ty': 20.0, 'angle': 5.0, 'scale': 1.1}

        # Act
        state = AlignmentState.from_aoi_lib_format(transform)

        # Assert
        assert state.tx == 10.0
        assert state.ty == 20.0
        assert state.angle == 5.0
        assert state.scale == 1.1
        assert state.opacity == 0.5  # Valor padrão

    def test_copy(self):
        """Testa cópia profunda do estado."""
        # Arrange
        matches = [FiducialMatch(template_id=1, found=True, x=100.0, y=100.0)]
        state1 = AlignmentState(tx=10.0, fiducial_matches=matches)

        # Act
        state2 = state1.copy()
        state1.tx = 999.0  # Modifica original

        # Assert
        assert state2.tx == 10.0  # Cópia não foi afetada
        assert len(state2.fiducial_matches) == 1
