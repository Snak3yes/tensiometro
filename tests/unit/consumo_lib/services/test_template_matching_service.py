"""
Testes Unitários para Template Matching Service

Este módulo contém testes unitários para o serviço de template matching,
seguindo o padrão Arrange-Act-Assert.

Cobertura de testes:
    - TemplateMatchingService: testes para busca de fiduciais
    - Adição e remoção de templates
    - Validação de resultados
    - Cálculo de score

Author: Claude Sonnet 4.5
Date: 2026-01-14
Track: solid_refactoring_phase2_20260114 (Phase 3 - Alignment Widget Refactoring)
"""

import pytest
import numpy as np
import cv2

from consumo_lib.services.template_matching_service import TemplateMatchingService
from consumo_lib.models.alignment_state import FiducialMatch


class TestTemplateMatchingService:
    """Testes para TemplateMatchingService."""

    def test_create_default(self):
        """Testa criação de serviço com parâmetros padrão."""
        # Arrange & Act
        service = TemplateMatchingService()

        # Assert
        assert service.threshold == 70.0
        assert service.search_radius == 100
        assert service.window_size == 50
        assert service.template_count == 0
        assert service.has_templates is False

    def test_create_custom_params(self):
        """Testa criação de serviço com parâmetros customizados."""
        # Arrange & Act
        service = TemplateMatchingService(
            threshold=80.0,
            search_radius=150,
            window_size=60,
        )

        # Assert
        assert service.threshold == 80.0
        assert service.search_radius == 150
        assert service.window_size == 60

    def test_add_template_valid(self, sample_template_image):
        """Testa adição de template válido."""
        # Arrange
        service = TemplateMatchingService()

        # Act
        success = service.add_template(
            name="Fiducial A",
            template_image=sample_template_image,
            x=100.0,
            y=100.0,
        )

        # Assert
        assert success is True
        assert service.template_count == 1
        assert service.has_templates is True

    def test_add_template_with_custom_params(self, sample_template_image):
        """Testa adição de template com parâmetros customizados."""
        # Arrange
        service = TemplateMatchingService(threshold=70.0)

        # Act
        success = service.add_template(
            name="Fiducial B",
            template_image=sample_template_image,
            x=200.0,
            y=150.0,
            search_radius=80,
            threshold=85.0,
        )

        # Assert
        assert success is True
        assert service.template_count == 1

    def test_add_multiple_templates(self, sample_template_image):
        """Testa adição de múltiplos templates."""
        # Arrange
        service = TemplateMatchingService()

        # Act
        service.add_template("Fiducial A", sample_template_image, 0.0, 0.0)
        service.add_template("Fiducial B", sample_template_image, 100.0, 0.0)

        # Assert
        assert service.template_count == 2

    def test_find_one_success(self, sample_template_image, sample_search_image):
        """Testa busca de um template com sucesso."""
        # Arrange
        service = TemplateMatchingService()
        service.add_template("Fiducial A", sample_template_image, 100.0, 100.0)

        # Act
        result = service.find_one("Fiducial A", sample_search_image, 100, 100)

        # Assert
        assert result is not None
        assert result.found is True
        assert result.similarity >= 70.0
        assert result.image_x > 0
        assert result.image_y > 0

    def test_find_one_not_found(self, sample_template_image, blank_image):
        """Testa busca quando template não é encontrado."""
        # Arrange
        service = TemplateMatchingService()
        service.add_template("Fiducial A", sample_template_image, 100.0, 100.0)

        # Act
        result = service.find_one("Fiducial A", blank_image, 100, 100)

        # Assert
        assert result is not None
        assert result.found is False
        assert result.similarity == 0.0

    def test_find_one_nonexistent_template(self, sample_search_image):
        """Testa busca de template que não existe."""
        # Arrange
        service = TemplateMatchingService()

        # Act
        result = service.find_one("Nonexistent", sample_search_image)

        # Assert
        assert result is None

    def test_find_all_success(self, sample_template_image, sample_search_image):
        """Testa busca de todos os templates com sucesso."""
        # Arrange
        service = TemplateMatchingService()
        service.add_template("Fiducial A", sample_template_image, 100.0, 100.0)
        service.add_template("Fiducial B", sample_template_image, 200.0, 100.0)

        # Act
        results = service.find_all(sample_search_image)

        # Assert
        assert len(results) == 2
        assert results[0].found is True
        assert results[1].found is True

    def test_find_all_with_expected_positions(
        self, sample_template_image, sample_search_image
    ):
        """Testa busca com posições esperadas."""
        # Arrange
        service = TemplateMatchingService()
        service.add_template("Fiducial A", sample_template_image, 100.0, 100.0)

        # Act
        results = service.find_all(
            sample_search_image,
            expected_positions=[(100, 100)],
        )

        # Assert
        assert len(results) == 1
        assert results[0].found is True

    def test_find_all_as_matches(self, sample_template_image, sample_search_image):
        """Testa conversão de resultados para FiducialMatch."""
        # Arrange
        service = TemplateMatchingService()
        service.add_template("Fiducial A", sample_template_image, 100.0, 100.0)

        # Act
        matches = service.find_all_as_matches(sample_search_image)

        # Assert
        assert len(matches) == 1
        assert isinstance(matches[0], FiducialMatch)
        assert matches[0].template_id == 1
        assert matches[0].found is True

    def test_calculate_match_score_all_found(self):
        """Testa cálculo de score quando todos encontrados."""
        # Arrange
        from aoi_lib.fiducial_alignment import FiducialMatchResult

        service = TemplateMatchingService()
        results = [
            FiducialMatchResult(found=True, similarity=90.0),
            FiducialMatchResult(found=True, similarity=95.0),
        ]

        # Act
        score = service.calculate_match_score(results)

        # Assert
        assert score == pytest.approx(92.5, abs=0.1)  # (90 + 95) / 2

    def test_calculate_match_score_partial_found(self):
        """Testa cálculo de score com parcialmente encontrados."""
        # Arrange
        from aoi_lib.fiducial_alignment import FiducialMatchResult

        service = TemplateMatchingService()
        results = [
            FiducialMatchResult(found=True, similarity=85.0),
            FiducialMatchResult(found=False),
        ]

        # Act
        score = service.calculate_match_score(results)

        # Assert
        # 85 - 10 (penalty by missing fiducial) = 75
        assert score == pytest.approx(75.0, abs=0.1)

    def test_calculate_match_score_none_found(self):
        """Testa cálculo de score quando nenhum encontrado."""
        # Arrange
        from aoi_lib.fiducial_alignment import FiducialMatchResult

        service = TemplateMatchingService()
        results = [
            FiducialMatchResult(found=False),
            FiducialMatchResult(found=False),
        ]

        # Act
        score = service.calculate_match_score(results)

        # Assert
        assert score == 0.0

    def test_calculate_match_score_empty(self):
        """Testa cálculo de score com lista vazia."""
        # Arrange
        service = TemplateMatchingService()

        # Act
        score = service.calculate_match_score([])

        # Assert
        assert score == 0.0

    def test_validate_match_valid(self):
        """Testa validação de match válido."""
        # Arrange
        from aoi_lib.fiducial_alignment import FiducialMatchResult

        service = TemplateMatchingService(threshold=70.0)
        result = FiducialMatchResult(
            found=True,
            similarity=85.0,
            offset_x=5.0,
            offset_y=5.0,
        )

        # Act
        is_valid, error = service.validate_match(result)

        # Assert
        assert is_valid is True
        assert error is None

    def test_validate_match_not_found(self):
        """Testa validação de match não encontrado."""
        # Arrange
        from aoi_lib.fiducial_alignment import FiducialMatchResult

        service = TemplateMatchingService()
        result = FiducialMatchResult(found=False)

        # Act
        is_valid, error = service.validate_match(result)

        # Assert
        assert is_valid is False
        assert "não encontrado" in error

    def test_validate_match_low_score(self):
        """Testa validação de match com score baixo."""
        # Arrange
        from aoi_lib.fiducial_alignment import FiducialMatchResult

        service = TemplateMatchingService(threshold=80.0)
        result = FiducialMatchResult(found=True, similarity=60.0)

        # Act
        is_valid, error = service.validate_match(result)

        # Assert
        assert is_valid is False
        assert "abaixo do mínimo" in error

    def test_validate_match_too_far(self):
        """Testa validação de match muito distante."""
        # Arrange
        from aoi_lib.fiducial_alignment import FiducialMatchResult

        service = TemplateMatchingService(search_radius=50)
        result = FiducialMatchResult(
            found=True,
            similarity=90.0,
            offset_x=100.0,  # 100px > 50px radius
            offset_y=0.0,
        )

        # Act
        is_valid, error = service.validate_match(result)

        # Assert
        assert is_valid is False
        assert "acima do máximo" in error

    def test_clear_templates(self, sample_template_image):
        """Testa remoção de todos os templates."""
        # Arrange
        service = TemplateMatchingService()
        service.add_template("Fiducial A", sample_template_image, 0.0, 0.0)
        service.add_template("Fiducial B", sample_template_image, 100.0, 0.0)

        # Act
        service.clear_templates()

        # Assert
        assert service.template_count == 0
        assert service.has_templates is False

    def test_color_image_conversion(self, sample_template_image):
        """Testa conversão de imagem colorida para grayscale."""
        # Arrange
        # Cria imagem colorida (BGR)
        color_image = cv2.cvtColor(sample_template_image, cv2.COLOR_GRAY2BGR)
        service = TemplateMatchingService()

        # Act
        service.add_template("Fiducial A", color_image, 0.0, 0.0)

        # Assert
        assert service.template_count == 1
        # Template deve ter ambas versões
        fid = service._aligner.fiducials[0]
        assert fid.template_bgr is not None
        assert fid.template_gray is not None


# Fixtures


@pytest.fixture
def sample_template_image():
    """Cria imagem de template de exemplo."""
    # Círculo com cruz
    img = np.zeros((50, 50), dtype=np.uint8)
    cv2.circle(img, (25, 25), 20, 255, -1)
    cv2.line(img, (15, 25), (35, 25), 0, 2)
    cv2.line(img, (25, 15), (25, 35), 0, 2)
    return img


@pytest.fixture
def sample_search_image():
    """Cria imagem de busca com fiducial."""
    # Imagem maior com fiducial em posição conhecida
    img = np.zeros((200, 200), dtype=np.uint8)
    cv2.circle(img, (100, 100), 20, 255, -1)
    cv2.line(img, (90, 100), (110, 100), 0, 2)
    cv2.line(img, (100, 90), (100, 110), 0, 2)
    return img


@pytest.fixture
def blank_image():
    """Cria imagem em branco."""
    return np.zeros((200, 200), dtype=np.uint8)
