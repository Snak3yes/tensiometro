"""
test_fiducial_alignment.py
---------------------------
Testes de integração para fiducial_alignment.py.

Cobertura:
- Dataclasses (FiducialTemplate, FiducialMatchResult, AlignmentTransform)
- FiducialAligner - gerenciamento de fiduciais
- Template capture - captura de ROI
- Template matching - busca com OpenCV (mockado)
- Transform calculation - 2, 3, 4+ pontos
- Transform application - aplicar a pontos
- Serialization - to_dict/from_dict
- Utility functions - preview e error metrics
"""

import pytest
import numpy as np
import cv2
import math
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from aoi_lib.fiducial_alignment import (
    FiducialTemplate,
    FiducialMatchResult,
    AlignmentTransform,
    FiducialAligner,
    create_alignment_preview,
    calculate_error_metrics
)


# ============================================================================
#  FIXTURES
# ============================================================================

@pytest.fixture
def sample_image_bgr():
    """Imagem BGR de exemplo (100x100)."""
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    # Desenha um quadrado branco no centro
    cv2.rectangle(img, (40, 40), (60, 60), (255, 255, 255), -1)
    return img


@pytest.fixture
def sample_image_gray(sample_image_bgr):
    """Imagem grayscale de exemplo (100x100)."""
    return cv2.cvtColor(sample_image_bgr, cv2.COLOR_BGR2GRAY)


@pytest.fixture
def sample_template():
    """Template de fiducial de exemplo."""
    fid = FiducialTemplate(
        name="Fiducial A",
        window_size=50,
        search_radius=100,
        threshold=70.0,
        gerber_x=10.0,
        gerber_y=20.0
    )
    # Cria template sintético
    fid.template_bgr = np.zeros((50, 50, 3), dtype=np.uint8)
    cv2.circle(fid.template_bgr, (25, 25), 15, (255, 255, 255), -1)
    fid.template_gray = cv2.cvtColor(fid.template_bgr, cv2.COLOR_BGR2GRAY)
    return fid


@pytest.fixture
def aligner():
    """Instância do FiducialAligner."""
    return FiducialAligner()


@pytest.fixture
def aligner_with_2_fiducials(aligner):
    """Aligner com 2 fiduciais configurados."""
    # Fiducial A
    fid_a = FiducialTemplate(
        name="Fiducial A",
        window_size=50,
        search_radius=100,
        threshold=70.0,
        gerber_x=0.0,
        gerber_y=0.0
    )
    fid_a.template_gray = np.zeros((50, 50), dtype=np.uint8)
    cv2.circle(fid_a.template_gray, (25, 25), 15, 255, -1)
    if fid_a.template_bgr is None:
        fid_a.template_bgr = cv2.cvtColor(fid_a.template_gray, cv2.COLOR_GRAY2BGR)

    # Fiducial B
    fid_b = FiducialTemplate(
        name="Fiducial B",
        window_size=50,
        search_radius=100,
        threshold=70.0,
        gerber_x=100.0,
        gerber_y=0.0
    )
    fid_b.template_gray = np.zeros((50, 50), dtype=np.uint8)
    cv2.circle(fid_b.template_gray, (25, 25), 15, 255, -1)
    if fid_b.template_bgr is None:
        fid_b.template_bgr = cv2.cvtColor(fid_b.template_gray, cv2.COLOR_GRAY2BGR)

    aligner.fiducials = [fid_a, fid_b]
    return aligner


# ============================================================================
#  TESTES: FiducialTemplate
# ============================================================================

class TestFiducialTemplate:
    """Testes para dataclass FiducialTemplate."""

    def test_initialization(self):
        """Testa inicialização com valores padrão."""
        fid = FiducialTemplate(name="Test")
        assert fid.name == "Test"
        assert fid.window_size == 50
        assert fid.search_radius == 100
        assert fid.threshold == 70.0
        assert fid.gerber_x == 0.0
        assert fid.gerber_y == 0.0
        assert fid.template_gray is None
        assert fid.template_bgr is None

    def test_initialization_with_values(self):
        """Testa inicialização com valores específicos."""
        fid = FiducialTemplate(
            name="Fiducial B",
            window_size=60,
            search_radius=150,
            threshold=80.0,
            gerber_x=50.0,
            gerber_y=100.0
        )
        assert fid.name == "Fiducial B"
        assert fid.window_size == 60
        assert fid.search_radius == 150
        assert fid.threshold == 80.0
        assert fid.gerber_x == 50.0
        assert fid.gerber_y == 100.0

    def test_to_dict_without_template(self):
        """Testa serialização sem template."""
        fid = FiducialTemplate(name="Test")
        data = fid.to_dict()

        assert data["name"] == "Test"
        assert data["window_size"] == 50
        assert data["search_radius"] == 100
        assert data["threshold"] == 70.0
        assert data["gerber_x"] == 0.0
        assert data["gerber_y"] == 0.0
        assert "template_png_b64" not in data

    def test_to_dict_with_template(self, sample_template):
        """Testa serialização com template."""
        data = sample_template.to_dict()

        assert "template_png_b64" in data
        assert isinstance(data["template_png_b64"], str)
        assert len(data["template_png_b64"]) > 0

    def test_from_dict_without_template(self):
        """Testa deserialização sem template."""
        data = {
            "name": "Test",
            "window_size": 60,
            "search_radius": 150,
            "threshold": 80.0,
            "gerber_x": 50.0,
            "gerber_y": 100.0
        }
        fid = FiducialTemplate.from_dict(data)

        assert fid.name == "Test"
        assert fid.window_size == 60
        assert fid.search_radius == 150
        assert fid.threshold == 80.0
        assert fid.gerber_x == 50.0
        assert fid.gerber_y == 100.0
        assert fid.template_gray is None
        assert fid.template_bgr is None

    def test_from_dict_with_template(self, sample_template):
        """Testa deserialização com template (round-trip)."""
        # Serializa
        data = sample_template.to_dict()

        # Deserializa
        fid_restored = FiducialTemplate.from_dict(data)

        # Verifica
        assert fid_restored.name == sample_template.name
        assert fid_restored.window_size == sample_template.window_size
        assert fid_restored.search_radius == sample_template.search_radius
        assert fid_restored.threshold == sample_template.threshold
        assert fid_restored.gerber_x == sample_template.gerber_x
        assert fid_restored.gerber_y == sample_template.gerber_y
        assert fid_restored.template_bgr is not None
        assert fid_restored.template_gray is not None
        # Compara imagens
        np.testing.assert_array_equal(fid_restored.template_bgr, sample_template.template_bgr)
        np.testing.assert_array_equal(fid_restored.template_gray, sample_template.template_gray)


# ============================================================================
#  TESTES: FiducialMatchResult
# ============================================================================

class TestFiducialMatchResult:
    """Testes para dataclass FiducialMatchResult."""

    def test_initialization_default(self):
        """Testa inicialização com valores padrão."""
        result = FiducialMatchResult()
        assert result.found is False
        assert result.similarity == 0.0
        assert result.image_x == 0.0
        assert result.image_y == 0.0
        assert result.offset_x == 0.0
        assert result.offset_y == 0.0
        assert result.match_rect == (0, 0, 0, 0)

    def test_initialization_with_values(self):
        """Testa inicialização com valores específicos."""
        result = FiducialMatchResult(
            found=True,
            similarity=85.5,
            image_x=100.0,
            image_y=200.0,
            offset_x=5.0,
            offset_y=-3.0,
            match_rect=(75, 175, 50, 50)
        )
        assert result.found is True
        assert result.similarity == 85.5
        assert result.image_x == 100.0
        assert result.image_y == 200.0
        assert result.offset_x == 5.0
        assert result.offset_y == -3.0
        assert result.match_rect == (75, 175, 50, 50)


# ============================================================================
#  TESTES: AlignmentTransform
# ============================================================================

class TestAlignmentTransform:
    """Testes para dataclass AlignmentTransform."""

    def test_initialization_default(self):
        """Testa inicialização com valores padrão."""
        transform = AlignmentTransform()
        assert transform.tx == 0.0
        assert transform.ty == 0.0
        assert transform.angle == 0.0
        assert transform.scale_x == 1.0
        assert transform.scale_y == 1.0
        assert transform.center_x == 0.0
        assert transform.center_y == 0.0
        assert transform.matrix is None

    def test_get_affine_matrix_identity(self):
        """Testa matriz afim para transformação identidade."""
        transform = AlignmentTransform()
        matrix = transform.get_affine_matrix()

        expected = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
        np.testing.assert_array_almost_equal(matrix, expected, decimal=5)

    def test_get_affine_matrix_translation(self):
        """Testa matriz afim com translação apenas."""
        transform = AlignmentTransform(tx=10.0, ty=20.0)
        matrix = transform.get_affine_matrix()

        expected = np.array([[1.0, 0.0, 10.0], [0.0, 1.0, 20.0]])
        np.testing.assert_array_almost_equal(matrix, expected, decimal=5)

    def test_get_affine_matrix_rotation_90_degrees(self):
        """Testa matriz afim com rotação de 90 graus."""
        transform = AlignmentTransform(angle=90.0)
        matrix = transform.get_affine_matrix()

        # Rotação de 90°: (x, y) -> (-y, x)
        # [cos -sin] = [0 -1]
        # [sin  cos] = [1  0]
        expected = np.array([[0.0, -1.0, 0.0], [1.0, 0.0, 0.0]])
        np.testing.assert_array_almost_equal(matrix, expected, decimal=5)

    def test_get_affine_matrix_uniform_scale(self):
        """Testa matriz afim com escala uniforme."""
        transform = AlignmentTransform(scale_x=2.0, scale_y=2.0)
        matrix = transform.get_affine_matrix()

        expected = np.array([[2.0, 0.0, 0.0], [0.0, 2.0, 0.0]])
        np.testing.assert_array_almost_equal(matrix, expected, decimal=5)

    def test_get_affine_matrix_combined(self):
        """Testa matriz afim com translação + rotação + escala."""
        transform = AlignmentTransform(
            tx=10.0,
            ty=20.0,
            angle=45.0,
            scale_x=2.0,
            scale_y=2.0
        )
        matrix = transform.get_affine_matrix()

        # Verifica dimensões
        assert matrix.shape == (2, 3)
        # Verifica que é uma transformação válida (determinante != 0)
        det = np.linalg.det(matrix[:, :2])
        assert abs(det) > 1e-6

    def test_apply_to_point_identity(self):
        """Testa aplicação de transformação identidade a um ponto."""
        transform = AlignmentTransform()
        x, y = transform.apply_to_point(10.0, 20.0)

        assert abs(x - 10.0) < 1e-6
        assert abs(y - 20.0) < 1e-6

    def test_apply_to_point_translation(self):
        """Testa aplicação de translação a um ponto."""
        transform = AlignmentTransform(tx=5.0, ty=-3.0)
        x, y = transform.apply_to_point(10.0, 20.0)

        assert abs(x - 15.0) < 1e-6
        assert abs(y - 17.0) < 1e-6

    def test_apply_to_point_rotation_90_degrees(self):
        """Testa aplicação de rotação de 90° a um ponto."""
        transform = AlignmentTransform(angle=90.0)
        x, y = transform.apply_to_point(1.0, 0.0)

        # (1, 0) rotacionado 90° -> (0, 1)
        assert abs(x) < 1e-6
        assert abs(y - 1.0) < 1e-6

    def test_apply_to_point_scale(self):
        """Testa aplicação de escala a um ponto."""
        transform = AlignmentTransform(scale_x=2.0, scale_y=3.0)
        x, y = transform.apply_to_point(10.0, 20.0)

        assert abs(x - 20.0) < 1e-6
        assert abs(y - 60.0) < 1e-6

    def test_apply_to_points_empty(self):
        """Testa aplicação a array vazio."""
        transform = AlignmentTransform()
        points = np.array([], dtype=np.float64).reshape(0, 2)
        result = transform.apply_to_points(points)

        assert result.shape == (0, 2)

    def test_apply_to_points_multiple(self):
        """Testa aplicação a múltiplos pontos."""
        transform = AlignmentTransform(tx=5.0, ty=10.0)
        points = np.array([[0.0, 0.0], [10.0, 20.0], [30.0, 40.0]], dtype=np.float64)
        result = transform.apply_to_points(points)

        expected = np.array([[5.0, 10.0], [15.0, 30.0], [35.0, 50.0]], dtype=np.float64)
        np.testing.assert_array_almost_equal(result, expected, decimal=5)


# ============================================================================
#  TESTES: FiducialAligner - Gerenciamento de Fiduciais
# ============================================================================

class TestFiducialAlignerBasics:
    """Testes básicos do FiducialAligner."""

    def test_initialization(self, aligner):
        """Testa inicialização do aligner."""
        assert len(aligner.fiducials) == 0
        assert len(aligner.last_results) == 0
        assert aligner.transform is None
        assert aligner.default_window_size == 50
        assert aligner.default_search_radius == 100
        assert aligner.default_threshold == 70.0

    def test_add_fiducial(self, aligner):
        """Testa adição de fiducial."""
        fid = aligner.add_fiducial("Fiducial A", 10.0, 20.0)

        assert len(aligner.fiducials) == 1
        assert fid.name == "Fiducial A"
        assert fid.gerber_x == 10.0
        assert fid.gerber_y == 20.0
        assert fid.window_size == aligner.default_window_size
        assert fid.search_radius == aligner.default_search_radius
        assert fid.threshold == aligner.default_threshold

    def test_add_multiple_fiducials(self, aligner):
        """Testa adição de múltiplos fiduciais."""
        aligner.add_fiducial("Fiducial A", 0.0, 0.0)
        aligner.add_fiducial("Fiducial B", 100.0, 0.0)
        aligner.add_fiducial("Fiducial C", 50.0, 100.0)

        assert len(aligner.fiducials) == 3

    def test_remove_fiducial(self, aligner):
        """Testa remoção de fiducial."""
        aligner.add_fiducial("Fiducial A", 0.0, 0.0)
        aligner.add_fiducial("Fiducial B", 100.0, 0.0)

        result = aligner.remove_fiducial("Fiducial A")
        assert result is True
        assert len(aligner.fiducials) == 1
        assert aligner.fiducials[0].name == "Fiducial B"

    def test_remove_nonexistent_fiducial(self, aligner):
        """Testa remoção de fiducial inexistente."""
        result = aligner.remove_fiducial("Inexistente")
        assert result is False

    def test_get_fiducial(self, aligner):
        """Testa recuperação de fiducial pelo nome."""
        aligner.add_fiducial("Fiducial A", 0.0, 0.0)
        aligner.add_fiducial("Fiducial B", 100.0, 0.0)

        fid = aligner.get_fiducial("Fiducial B")
        assert fid is not None
        assert fid.name == "Fiducial B"
        assert fid.gerber_x == 100.0

    def test_get_nonexistent_fiducial(self, aligner):
        """Testa recuperação de fiducial inexistente."""
        fid = aligner.get_fiducial("Inexistente")
        assert fid is None

    def test_clear_fiducials(self, aligner):
        """Testa limpeza de todos os fiduciais."""
        aligner.add_fiducial("Fiducial A", 0.0, 0.0)
        aligner.add_fiducial("Fiducial B", 100.0, 0.0)

        # Define transform e resultados
        aligner.transform = AlignmentTransform(tx=10.0)
        aligner.last_results = [FiducialMatchResult(found=True)]

        aligner.clear_fiducials()

        assert len(aligner.fiducials) == 0
        assert len(aligner.last_results) == 0
        assert aligner.transform is None


# ============================================================================
#  TESTES: FiducialAligner - Captura de Template
# ============================================================================

class TestFiducialAlignerCapture:
    """Testes para captura de template."""

    def test_capture_template_center(self, aligner, sample_image_bgr):
        """Testa captura de template no centro da imagem."""
        fid = aligner.add_fiducial("Test", 0.0, 0.0)

        result = aligner.capture_template(fid, sample_image_bgr)

        assert result is True
        assert fid.template_bgr is not None
        assert fid.template_gray is not None
        assert fid.template_bgr.shape == (50, 50, 3)
        assert fid.template_gray.shape == (50, 50)

    def test_capture_template_with_position(self, aligner, sample_image_bgr):
        """Testa captura de template em posição específica."""
        fid = aligner.add_fiducial("Test", 0.0, 0.0)

        result = aligner.capture_template(fid, sample_image_bgr, center_x=30, center_y=30)

        assert result is True
        assert fid.template_bgr is not None

    def test_capture_template_invalid_frame(self, aligner):
        """Testa captura com frame inválido."""
        fid = aligner.add_fiducial("Test", 0.0, 0.0)

        result = aligner.capture_template(fid, None)
        assert result is False

    def test_capture_template_empty_frame(self, aligner):
        """Testa captura com frame vazio."""
        fid = aligner.add_fiducial("Test", 0.0, 0.0)
        empty_img = np.array([], dtype=np.uint8)

        result = aligner.capture_template(fid, empty_img)
        assert result is False


# ============================================================================
#  TESTES: FiducialAligner - Template Matching
# ============================================================================

class TestFiducialAlignerMatching:
    """Testes para template matching."""

    def test_find_fiducial_no_template(self, aligner, sample_image_gray):
        """Testa busca sem template definido."""
        fid = FiducialTemplate(name="Test")
        result = aligner.find_fiducial(fid, sample_image_gray)

        assert result.found is False
        assert result.similarity == 0.0

    def test_find_fiducial_invalid_image(self, aligner, sample_template):
        """Testa busca com imagem inválida."""
        result = aligner.find_fiducial(sample_template, None)

        assert result.found is False

    @patch('cv2.matchTemplate')
    def test_find_fiducial_success(self, mock_match, aligner, sample_template, sample_image_gray):
        """Testa busca com sucesso (mockado)."""
        # Configura mock para retornar match perfeito
        mock_result = np.ones((sample_image_gray.shape[0] - 50 + 1,
                               sample_image_gray.shape[1] - 50 + 1), dtype=np.float32)
        mock_result[:, :] = 0.95  # 95% de similaridade
        mock_match.return_value = mock_result

        # Mock minMaxLoc
        with patch('cv2.minMaxLoc') as mock_minmax:
            mock_minmax.return_value = (0.0, 0.95, (0, 0), (25, 25))

            result = aligner.find_fiducial(sample_template, sample_image_gray)

            assert result.found is True
            assert result.similarity == pytest.approx(95.0, rel=0.1)
            assert result.image_x == 50.0  # 25 (top-left) + 50/2 (centro)
            assert result.image_y == 50.0

    @patch('cv2.matchTemplate')
    def test_find_fiducial_low_similarity(self, mock_match, aligner, sample_template, sample_image_gray):
        """Testa busca com similaridade baixa."""
        # Mock retorna similaridade baixa
        mock_result = np.zeros((sample_image_gray.shape[0] - 50 + 1,
                                sample_image_gray.shape[1] - 50 + 1), dtype=np.float32)
        mock_result[:, :] = 0.5  # 50% (abaixo do threshold de 70%)
        mock_match.return_value = mock_result

        with patch('cv2.minMaxLoc') as mock_minmax:
            mock_minmax.return_value = (0.0, 0.5, (0, 0), (25, 25))

            result = aligner.find_fiducial(sample_template, sample_image_gray)

            assert result.found is False
            assert result.similarity == pytest.approx(50.0, rel=0.1)

    def test_find_all_fiducials(self, aligner_with_2_fiducials, sample_image_gray):
        """Testa busca de todos os fiduciais."""
        # Mock do find_fiducial
        with patch.object(aligner_with_2_fiducials, 'find_fiducial') as mock_find:
            mock_find.side_effect = [
                FiducialMatchResult(found=True, similarity=85.0, image_x=50.0, image_y=50.0),
                FiducialMatchResult(found=True, similarity=90.0, image_x=150.0, image_y=50.0)
            ]

            results = aligner_with_2_fiducials.find_all_fiducials(sample_image_gray)

            assert len(results) == 2
            assert results[0].found is True
            assert results[1].found is True
            assert mock_find.call_count == 2


# ============================================================================
#  TESTES: FiducialAligner - Cálculo de Transformação
# ============================================================================

class TestFiducialAlignerTransform:
    """Testes para cálculo de transformação."""

    def test_calculate_transform_insufficient_points(self, aligner):
        """Testa cálculo com menos de 2 pontos."""
        result = aligner.calculate_transform([(0.0, 0.0)], [(10.0, 10.0)])
        assert result is None

    def test_calculate_transform_mismatched_counts(self, aligner):
        """Testa cálculo com números diferentes de pontos."""
        result = aligner.calculate_transform(
            [(0.0, 0.0), (100.0, 0.0)],
            [(10.0, 10.0)]
        )
        assert result is None

    def test_calculate_transform_2_points_translation_only(self, aligner):
        """Testa cálculo com 2 pontos (translação pura)."""
        gerber_pts = [(0.0, 0.0), (100.0, 0.0)]
        image_pts = [(10.0, 20.0), (110.0, 20.0)]

        transform = aligner.calculate_transform(gerber_pts, image_pts)

        assert transform is not None
        assert abs(transform.tx - 10.0) < 0.1  # Translação X
        assert abs(transform.ty - 20.0) < 0.1  # Translação Y
        assert abs(transform.scale_x - 1.0) < 0.01  # Sem escala
        assert abs(transform.scale_y - 1.0) < 0.01
        assert abs(transform.angle) < 0.1  # Sem rotação

    def test_calculate_transform_2_points_with_scale(self, aligner):
        """Testa cálculo com 2 pontos (com escala)."""
        gerber_pts = [(0.0, 0.0), (100.0, 0.0)]
        image_pts = [(0.0, 0.0), (200.0, 0.0)]  # Dobro da distância

        transform = aligner.calculate_transform(gerber_pts, image_pts)

        assert transform is not None
        assert abs(transform.scale_x - 2.0) < 0.01
        assert abs(transform.scale_y - 2.0) < 0.01
        assert abs(transform.angle) < 0.1

    def test_calculate_transform_2_points_with_rotation(self, aligner):
        """Testa cálculo com 2 pontos (com rotação)."""
        gerber_pts = [(0.0, 0.0), (100.0, 0.0)]
        # Rotação de 90°: (100, 0) -> (0, 100)
        image_pts = [(0.0, 0.0), (0.0, 100.0)]

        transform = aligner.calculate_transform(gerber_pts, image_pts)

        assert transform is not None
        assert abs(transform.angle - 90.0) < 1.0  # ~90 graus

    def test_calculate_transform_2_points_coincident(self, aligner):
        """Testa cálculo com pontos coincidentes (erro)."""
        gerber_pts = [(50.0, 50.0), (50.0, 50.0)]  # Mesmo ponto
        image_pts = [(100.0, 100.0), (100.0, 100.0)]

        transform = aligner.calculate_transform(gerber_pts, image_pts)

        assert transform is None  # Pontos muito próximos

    def test_calculate_transform_3_points_affine(self, aligner):
        """Testa cálculo com 3 pontos (transformação afim)."""
        gerber_pts = [(0.0, 0.0), (100.0, 0.0), (0.0, 100.0)]
        image_pts = [(10.0, 20.0), (110.0, 20.0), (10.0, 120.0)]

        with patch('cv2.getAffineTransform') as mock_get_affine:
            mock_matrix = np.array([
                [1.0, 0.0, 10.0],
                [0.0, 1.0, 20.0]
            ], dtype=np.float32)
            mock_get_affine.return_value = mock_matrix

            transform = aligner.calculate_transform(gerber_pts, image_pts)

            assert transform is not None
            assert transform.matrix is not None
            assert transform.matrix.shape == (3, 3)
            mock_get_affine.assert_called_once()

    def test_calculate_transform_from_fiducials_insufficient(self, aligner):
        """Testa cálculo com menos de 2 fiduciais."""
        aligner.add_fiducial("A", 0.0, 0.0)

        transform = aligner.calculate_transform_from_fiducials()
        assert transform is None

    def test_calculate_transform_from_fiducials_no_results(self, aligner_with_2_fiducials):
        """Testa cálculo sem resultados de busca."""
        # Nenhum resultado ainda
        transform = aligner_with_2_fiducials.calculate_transform_from_fiducials()
        assert transform is None

    def test_calculate_transform_from_fiducials_success(self, aligner_with_2_fiducials):
        """Testa cálculo a partir de fiduciais encontrados."""
        # Configura resultados de match
        aligner_with_2_fiducials.last_results = [
            FiducialMatchResult(found=True, similarity=85.0, image_x=100.0, image_y=200.0),
            FiducialMatchResult(found=True, similarity=90.0, image_x=200.0, image_y=200.0)
        ]

        # Mock do calculate_transform
        with patch.object(aligner_with_2_fiducials, 'calculate_transform') as mock_calc:
            expected_transform = AlignmentTransform(tx=10.0, ty=20.0)
            mock_calc.return_value = expected_transform

            transform = aligner_with_2_fiducials.calculate_transform_from_fiducials(scale_gerber_to_pixels=10.0)

            assert transform is not None
            mock_calc.assert_called_once()
            # Verifica que converteu coordenadas Gerber
            call_args = mock_calc.call_args
            gerber_pts = call_args[0][0]
            assert len(gerber_pts) == 2


# ============================================================================
#  TESTES: FiducialAligner - Aplicação de Transformação
# ============================================================================

class TestFiducialAlignerTransformApplication:
    """Testes para aplicação de transformação."""

    def test_transform_point_no_transform(self, aligner):
        """Testa transformação de ponto sem transformação definida."""
        x, y = aligner.transform_point(10.0, 20.0)
        assert x == 10.0
        assert y == 20.0

    def test_transform_point_with_transform(self, aligner):
        """Testa transformação de ponto com transformação definida."""
        aligner.transform = AlignmentTransform(tx=5.0, ty=10.0)
        x, y = aligner.transform_point(10.0, 20.0)

        assert abs(x - 15.0) < 1e-6
        assert abs(y - 30.0) < 1e-6

    def test_transform_points_no_transform(self, aligner):
        """Testa transformação de lista sem transformação."""
        points = [(10.0, 20.0), (30.0, 40.0)]
        result = aligner.transform_points(points)

        assert result == points

    def test_transform_points_with_transform(self, aligner):
        """Testa transformação de lista com transformação."""
        aligner.transform = AlignmentTransform(tx=5.0, ty=10.0)
        points = [(10.0, 20.0), (30.0, 40.0)]
        result = aligner.transform_points(points)

        expected = [(15.0, 30.0), (35.0, 50.0)]
        assert len(result) == 2
        assert abs(result[0][0] - 15.0) < 1e-6
        assert abs(result[0][1] - 30.0) < 1e-6

    def test_transform_polygon_no_transform(self, aligner):
        """Testa transformação de polígono sem transformação."""
        polygon = np.array([[0.0, 0.0], [10.0, 0.0], [10.0, 10.0]], dtype=np.float64)
        result = aligner.transform_polygon(polygon)

        np.testing.assert_array_equal(result, polygon)

    def test_transform_polygon_with_transform(self, aligner):
        """Testa transformação de polígono com transformação."""
        aligner.transform = AlignmentTransform(tx=5.0, ty=10.0)
        polygon = np.array([[0.0, 0.0], [10.0, 0.0], [10.0, 10.0]], dtype=np.float64)
        result = aligner.transform_polygon(polygon)

        expected = np.array([[5.0, 10.0], [15.0, 10.0], [15.0, 20.0]], dtype=np.float64)
        np.testing.assert_array_almost_equal(result, expected, decimal=5)


# ============================================================================
#  TESTES: FiducialAligner - Serialização
# ============================================================================

class TestFiducialAlignerSerialization:
    """Testes para serialização do aligner."""

    def test_to_dict(self, aligner):
        """Testa serialização para dicionário."""
        aligner.add_fiducial("Fiducial A", 0.0, 0.0)
        aligner.add_fiducial("Fiducial B", 100.0, 0.0)
        aligner.default_window_size = 60
        aligner.default_search_radius = 150
        aligner.default_threshold = 80.0

        data = aligner.to_dict()

        assert len(data["fiducials"]) == 2
        assert data["default_window_size"] == 60
        assert data["default_search_radius"] == 150
        assert data["default_threshold"] == 80.0

    def test_from_dict(self, aligner):
        """Testa deserialização de dicionário."""
        data = {
            "fiducials": [
                {
                    "name": "Fiducial A",
                    "window_size": 50,
                    "search_radius": 100,
                    "threshold": 70.0,
                    "gerber_x": 0.0,
                    "gerber_y": 0.0
                },
                {
                    "name": "Fiducial B",
                    "window_size": 50,
                    "search_radius": 100,
                    "threshold": 70.0,
                    "gerber_x": 100.0,
                    "gerber_y": 0.0
                }
            ],
            "default_window_size": 60,
            "default_search_radius": 150,
            "default_threshold": 80.0
        }

        aligner.from_dict(data)

        assert len(aligner.fiducials) == 2
        assert aligner.fiducials[0].name == "Fiducial A"
        assert aligner.fiducials[1].name == "Fiducial B"
        assert aligner.default_window_size == 60
        assert aligner.default_search_radius == 150
        assert aligner.default_threshold == 80.0


# ============================================================================
#  TESTES: Funções Utilitárias
# ============================================================================

class TestUtilityFunctions:
    """Testes para funções utilitárias."""

    def test_create_alignment_preview_basic(self, sample_image_bgr):
        """Testa criação de preview básico."""
        fid = FiducialTemplate(name="Test")
        result = FiducialMatchResult(
            found=True,
            similarity=85.0,
            image_x=50.0,
            image_y=50.0,
            match_rect=(25, 25, 50, 50)
        )

        preview = create_alignment_preview(
            sample_image_bgr,
            [fid],
            [result]
        )

        assert preview is not None
        assert preview.shape == sample_image_bgr.shape

    def test_create_alignment_preview_with_transform(self, sample_image_bgr):
        """Testa criação de preview com transformação."""
        fid = FiducialTemplate(name="Test")
        result = FiducialMatchResult(
            found=True,
            similarity=85.0,
            image_x=50.0,
            image_y=50.0,
            match_rect=(25, 25, 50, 50)
        )
        transform = AlignmentTransform(tx=10.0, ty=20.0)
        contour = np.array([[0.0, 0.0], [10.0, 0.0], [10.0, 10.0]], dtype=np.float64)

        preview = create_alignment_preview(
            sample_image_bgr,
            [fid],
            [result],
            transform,
            [contour]
        )

        assert preview is not None

    def test_calculate_error_metrics_basic(self):
        """Testa cálculo de métricas de erro."""
        gerber_pts = [(0.0, 0.0), (100.0, 0.0)]
        image_pts = [(0.0, 0.0), (100.0, 0.0)]
        transform = AlignmentTransform()  # Identidade

        metrics = calculate_error_metrics(gerber_pts, image_pts, transform)

        assert "max_error" in metrics
        assert "mean_error" in metrics
        assert "rms_error" in metrics
        assert metrics["max_error"] == 0.0
        assert metrics["mean_error"] == 0.0
        assert metrics["rms_error"] == 0.0

    def test_calculate_error_metrics_with_offset(self):
        """Testa cálculo de métricas com erro."""
        gerber_pts = [(0.0, 0.0), (100.0, 0.0)]
        image_pts = [(5.0, 5.0), (105.0, 5.0)]  # 5 pixels de offset
        transform = AlignmentTransform()  # Identidade (vai dar erro)

        metrics = calculate_error_metrics(gerber_pts, image_pts, transform)

        assert metrics["max_error"] > 0
        assert metrics["mean_error"] > 0
        assert metrics["rms_error"] > 0
        # Erro deve ser aprox 5 pixels (sqrt(5^2 + 5^2) = 7.07 para o primeiro ponto)
        assert abs(metrics["max_error"] - 7.07) < 0.1

    def test_calculate_error_metrics_mismatched_length(self):
        """Testa cálculo com números diferentes de pontos."""
        gerber_pts = [(0.0, 0.0), (100.0, 0.0)]
        image_pts = [(0.0, 0.0)]
        transform = AlignmentTransform()

        metrics = calculate_error_metrics(gerber_pts, image_pts, transform)

        assert metrics["max_error"] == float('inf')
        assert metrics["mean_error"] == float('inf')
        assert metrics["rms_error"] == float('inf')

    def test_calculate_error_metrics_empty(self):
        """Testa cálculo com listas vazias."""
        transform = AlignmentTransform()
        metrics = calculate_error_metrics([], [], transform)

        assert metrics["max_error"] == 0.0
        assert metrics["mean_error"] == 0.0
        assert metrics["rms_error"] == 0.0
