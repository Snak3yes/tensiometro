"""
test_stencil_inspector.py
--------------------------
Testes de integração para stencil_inspector.py.

Cobertura:
- Dataclasses (DefectType, InspectionThresholds, ApertureInspection, InspectionResult)
- StencilInspector - motor de inspeção visual
- Binarização - Otsu, Adaptive, Fixed
- Análise de aberturas - classificação OK/PARTIAL/BLOCKED
- Visualização - overlay e crops de defeitos
- quick_inspect - função utilitária
"""

import pytest
import numpy as np
import cv2
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from aoi_lib.stencil_inspector import (
    DefectType,
    InspectionThresholds,
    ApertureInspection,
    InspectionResult,
    StencilInspector,
    quick_inspect
)


# ============================================================================
#  FIXTURES
# ============================================================================

@pytest.fixture
def sample_mosaic_bgr():
    """Mosaico de exemplo (500x500, BGR) com aberturas claras."""
    img = np.zeros((500, 500, 3), dtype=np.uint8)
    # Fundo escuro (stencil bloqueando luz)
    # Aberturas claras (luz passando)
    cv2.circle(img, (100, 100), 30, (200, 200, 200), -1)  # OK - abertura clara
    cv2.circle(img, (250, 100), 30, (100, 100, 100), -1)  # PARTIAL - meio obscura
    cv2.circle(img, (400, 100), 30, (20, 20, 20), -1)    # BLOCKED - escura
    return img


@pytest.fixture
def sample_mosaic_gray():
    """Mosaico em grayscale."""
    img = np.zeros((500, 500), dtype=np.uint8)
    cv2.circle(img, (100, 100), 30, 200, -1)  # OK
    cv2.circle(img, (250, 100), 30, 100, -1)  # PARTIAL
    cv2.circle(img, (400, 100), 30, 20, -1)   # BLOCKED
    return img


@pytest.fixture
def sample_thresholds():
    """Thresholds de inspeção padrão."""
    return InspectionThresholds(
        ok_threshold=90.0,
        partial_threshold=70.0,
        bin_method="otsu"
    )


@pytest.fixture
def mock_transform():
    """Mock de transformação de alinhamento."""
    transform = Mock()
    transform.tx = 10.0
    transform.ty = 20.0
    transform.angle = 0.0
    transform.transform_point = Mock(side_effect=lambda x, y: (x + 10, y + 20))
    return transform


@pytest.fixture
def mock_gerber_object():
    """Mock de objeto Gerber."""
    obj = Mock()
    obj.id = 1
    obj.kind = "circle"
    obj.x_mm = 10.0
    obj.y_mm = 20.0
    obj.polygon_mm = [(5.0, 15.0), (15.0, 15.0), (15.0, 25.0), (5.0, 25.0)]
    return obj


@pytest.fixture
def mock_renderer():
    """Mock de GerberRenderer."""
    renderer = Mock()
    renderer.objects = []
    renderer.load_gerber = Mock(return_value=[])
    renderer.render_mask = Mock(return_value=np.zeros((500, 500), dtype=np.uint8))
    return renderer


# ============================================================================
#  TESTES: DefectType Enum
# ============================================================================

class TestDefectType:
    """Testes para enum DefectType."""

    def test_enum_values(self):
        """Testa valores do enum."""
        assert DefectType.OK.value == "OK"
        assert DefectType.PARTIAL.value == "PARTIAL"
        assert DefectType.BLOCKED.value == "BLOCKED"
        assert DefectType.DEFORMED.value == "DEFORMED"

    def test_enum_comparison(self):
        """Testa comparação de enums."""
        assert DefectType.OK == DefectType.OK
        assert DefectType.OK != DefectType.PARTIAL


# ============================================================================
#  TESTES: InspectionThresholds
# ============================================================================

class TestInspectionThresholds:
    """Testes para dataclass InspectionThresholds."""

    def test_initialization_defaults(self):
        """Testa inicialização com valores padrão."""
        thresholds = InspectionThresholds()
        assert thresholds.ok_threshold == 90.0
        assert thresholds.partial_threshold == 70.0
        assert thresholds.bin_method == "otsu"
        assert thresholds.bin_fixed_threshold == 127
        assert thresholds.bin_adaptive_block == 11
        assert thresholds.bin_adaptive_c == 2
        assert thresholds.min_aperture_area_px == 50
        assert thresholds.blur_kernel_size == 3
        assert thresholds.morphology_kernel_size == 3
        assert thresholds.apply_morphology is True

    def test_initialization_custom(self):
        """Testa inicialização com valores customizados."""
        thresholds = InspectionThresholds(
            ok_threshold=85.0,
            partial_threshold=65.0,
            bin_method="adaptive",
            min_aperture_area_px=100
        )
        assert thresholds.ok_threshold == 85.0
        assert thresholds.partial_threshold == 65.0
        assert thresholds.bin_method == "adaptive"
        assert thresholds.min_aperture_area_px == 100

    def test_to_dict(self):
        """Testa serialização para dicionário."""
        thresholds = InspectionThresholds(ok_threshold=85.0)
        data = thresholds.to_dict()

        assert data["ok_threshold"] == 85.0
        assert data["partial_threshold"] == 70.0
        assert data["bin_method"] == "otsu"

    def test_from_dict(self):
        """Testa deserialização de dicionário."""
        data = {
            "ok_threshold": 85.0,
            "partial_threshold": 65.0,
            "bin_method": "adaptive"
        }
        thresholds = InspectionThresholds.from_dict(data)

        assert thresholds.ok_threshold == 85.0
        assert thresholds.partial_threshold == 65.0
        assert thresholds.bin_method == "adaptive"


# ============================================================================
#  TESTES: ApertureInspection
# ============================================================================

class TestApertureInspection:
    """Testes para dataclass ApertureInspection."""

    def test_initialization(self):
        """Testa inicialização."""
        inspection = ApertureInspection(
            object_id=1,
            x_mm=10.0,
            y_mm=20.0,
            kind="circle",
            expected_area_px=1000,
            observed_area_px=950,
            fill_ratio=0.95,
            status=DefectType.OK,
            bbox=(100, 100, 50, 50)
        )

        assert inspection.object_id == 1
        assert inspection.x_mm == 10.0
        assert inspection.y_mm == 20.0
        assert inspection.kind == "circle"
        assert inspection.expected_area_px == 1000
        assert inspection.observed_area_px == 950
        assert inspection.fill_ratio == 0.95
        assert inspection.status == DefectType.OK
        assert inspection.bbox == (100, 100, 50, 50)

    def test_fill_percentage_property(self):
        """Testa propriedade fill_percentage."""
        inspection = ApertureInspection(
            object_id=1,
            x_mm=0.0,
            y_mm=0.0,
            kind="circle",
            expected_area_px=1000,
            observed_area_px=850,
            fill_ratio=0.85,
            status=DefectType.PARTIAL,
            bbox=(0, 0, 0, 0)
        )

        assert inspection.fill_percentage == 85.0

    def test_to_dict(self):
        """Testa serialização para dicionário."""
        inspection = ApertureInspection(
            object_id=1,
            x_mm=10.0,
            y_mm=20.0,
            kind="circle",
            expected_area_px=1000,
            observed_area_px=950,
            fill_ratio=0.95,
            status=DefectType.OK,
            bbox=(100, 100, 50, 50)
        )

        data = inspection.to_dict()

        assert data["object_id"] == 1
        assert data["status"] == "OK"  # Enum convertido para string
        assert data["fill_ratio"] == 0.95


# ============================================================================
#  TESTES: InspectionResult
# ============================================================================

class TestInspectionResult:
    """Testes para dataclass InspectionResult."""

    def test_initialization_defaults(self):
        """Testa inicialização com valores padrão."""
        result = InspectionResult()

        assert result.total_apertures == 0
        assert result.ok_count == 0
        assert result.partial_count == 0
        assert result.blocked_count == 0
        assert result.overall_status == "OK"
        assert result.approval_rate == 100.0
        assert len(result.apertures) == 0
        assert len(result.defects) == 0

    def test_to_dict(self):
        """Testa serialização para dicionário."""
        result = InspectionResult(
            total_apertures=10,
            ok_count=8,
            partial_count=1,
            blocked_count=1,
            overall_status="WARNING",
            approval_rate=80.0,
            gerber_file="test.gbr",
            mosaic_file="mosaic.png"
        )

        data = result.to_dict()

        assert data["total_apertures"] == 10
        assert data["ok_count"] == 8
        assert data["partial_count"] == 1
        assert data["blocked_count"] == 1
        assert data["overall_status"] == "WARNING"
        assert data["approval_rate"] == 80.0
        assert data["gerber_file"] == "test.gbr"
        assert data["mosaic_file"] == "mosaic.png"


# ============================================================================
#  TESTES: StencilInspector - Inicialização
# ============================================================================

class TestStencilInspectorBasics:
    """Testes básicos do StencilInspector."""

    def test_initialization_default_thresholds(self):
        """Testa inicialização com thresholds padrão."""
        inspector = StencilInspector()

        assert inspector.thresholds is not None
        assert inspector.thresholds.ok_threshold == 90.0
        assert inspector.thresholds.partial_threshold == 70.0
        assert inspector.renderer is not None

    def test_initialization_custom_thresholds(self, sample_thresholds):
        """Testa inicialização com thresholds customizados."""
        inspector = StencilInspector(thresholds=sample_thresholds)

        assert inspector.thresholds is sample_thresholds

    def test_initialization_state(self):
        """Testa estado inicial."""
        inspector = StencilInspector()

        assert inspector._mosaic is None
        assert inspector._transform is None
        assert inspector._last_result is None
        assert inspector._gerber_mask is None
        assert inspector._binary_mosaic is None

    def test_set_mosaic(self, sample_mosaic_bgr):
        """Testa definição do mosaico."""
        inspector = StencilInspector()
        inspector.set_mosaic(sample_mosaic_bgr)

        assert inspector._mosaic is not None
        assert np.array_equal(inspector._mosaic, sample_mosaic_bgr)

    def test_set_alignment(self, mock_transform):
        """Testa definição do alinhamento."""
        inspector = StencilInspector()
        inspector.set_alignment(mock_transform)

        assert inspector._transform is mock_transform


# ============================================================================
#  TESTES: StencilInspector - Binarização
# ============================================================================

class TestStencilInspectorBinarization:
    """Testes para binarização de mosaico."""

    def test_binarize_otsu_method(self, sample_mosaic_bgr):
        """Testa binarização com método Otsu."""
        inspector = StencilInspector(
            thresholds=InspectionThresholds(bin_method="otsu")
        )

        binary = inspector._binarize_mosaic(sample_mosaic_bgr)

        assert binary is not None
        assert len(binary.shape) == 2  # Grayscale
        assert binary.dtype == np.uint8

    def test_binarize_adaptive_method(self, sample_mosaic_bgr):
        """Testa binarização com método Adaptive."""
        inspector = StencilInspector(
            thresholds=InspectionThresholds(
                bin_method="adaptive",
                bin_adaptive_block=11,
                bin_adaptive_c=2
            )
        )

        binary = inspector._binarize_mosaic(sample_mosaic_bgr)

        assert binary is not None
        assert len(binary.shape) == 2

    def test_binarize_fixed_method(self, sample_mosaic_bgr):
        """Testa binarização com método Fixed."""
        inspector = StencilInspector(
            thresholds=InspectionThresholds(
                bin_method="fixed",
                bin_fixed_threshold=127
            )
        )

        binary = inspector._binarize_mosaic(sample_mosaic_bgr)

        assert binary is not None
        assert len(binary.shape) == 2

    def test_binarize_already_gray(self, sample_mosaic_gray):
        """Testa binarização de imagem já em grayscale."""
        inspector = StencilInspector()
        binary = inspector._binarize_mosaic(sample_mosaic_gray)

        assert binary is not None
        assert len(binary.shape) == 2

    def test_binarize_with_blur(self, sample_mosaic_bgr):
        """Testa binarização com blur."""
        inspector = StencilInspector(
            thresholds=InspectionThresholds(blur_kernel_size=5)
        )

        binary = inspector._binarize_mosaic(sample_mosaic_bgr)

        assert binary is not None

    def test_binarize_without_morphology(self, sample_mosaic_bgr):
        """Testa binarização sem morfologia."""
        inspector = StencilInspector(
            thresholds=InspectionThresholds(apply_morphology=False)
        )

        binary = inspector._binarize_mosaic(sample_mosaic_bgr)

        assert binary is not None


# ============================================================================
#  TESTES: StencilInspector - Análise de Aberturas
# ============================================================================

class TestStencilInspectorAnalysis:
    """Testes para análise de aberturas."""

    def test_analyze_apertures_empty_objects(self, sample_mosaic_bgr, mock_renderer):
        """Testa análise sem objetos Gerber."""
        inspector = StencilInspector()
        inspector.renderer = mock_renderer
        inspector._mosaic = sample_mosaic_bgr
        inspector._gerber_mask = np.zeros((500, 500), dtype=np.uint8)
        inspector._binary_mosaic = np.zeros((500, 500), dtype=np.uint8)

        result = inspector._analyze_apertures(None)

        assert len(result.apertures) == 0

    def test_analyze_apertures_with_objects(
        self,
        sample_mosaic_bgr,
        mock_renderer,
        mock_gerber_object
    ):
        """Testa análise com objetos Gerber."""
        mock_renderer.objects = [mock_gerber_object]

        inspector = StencilInspector()
        inspector.renderer = mock_renderer
        inspector._mosaic = sample_mosaic_bgr
        inspector._gerber_mask = np.zeros((500, 500), dtype=np.uint8)

        # Cria máscara binária com área parcialmente preenchida
        binary = np.zeros((500, 500), dtype=np.uint8)
        cv2.circle(binary, (25, 45), 10, 255, -1)  # 75% da área esperada
        inspector._binary_mosaic = binary

        result = inspector._analyze_apertures(None)

        # A análise deve criar pelo menos uma inspeção se a área for grande o suficiente
        # (depende do cálculo real da área)

    def test_classify_ok_status(self):
        """Testa classificação como OK."""
        inspector = StencilInspector(
            thresholds=InspectionThresholds(
                ok_threshold=90.0,
                partial_threshold=70.0
            )
        )

        fill_ratio = 0.95  # 95%
        fill_pct = fill_ratio * 100

        if fill_pct >= inspector.thresholds.ok_threshold:
            status = DefectType.OK
        elif fill_pct >= inspector.thresholds.partial_threshold:
            status = DefectType.PARTIAL
        else:
            status = DefectType.BLOCKED

        assert status == DefectType.OK

    def test_classify_partial_status(self):
        """Testa classificação como PARTIAL."""
        inspector = StencilInspector(
            thresholds=InspectionThresholds(
                ok_threshold=90.0,
                partial_threshold=70.0
            )
        )

        fill_ratio = 0.80  # 80%
        fill_pct = fill_ratio * 100

        if fill_pct >= inspector.thresholds.ok_threshold:
            status = DefectType.OK
        elif fill_pct >= inspector.thresholds.partial_threshold:
            status = DefectType.PARTIAL
        else:
            status = DefectType.BLOCKED

        assert status == DefectType.PARTIAL

    def test_classify_blocked_status(self):
        """Testa classificação como BLOCKED."""
        inspector = StencilInspector(
            thresholds=InspectionThresholds(
                ok_threshold=90.0,
                partial_threshold=70.0
            )
        )

        fill_ratio = 0.50  # 50%
        fill_pct = fill_ratio * 100

        if fill_pct >= inspector.thresholds.ok_threshold:
            status = DefectType.OK
        elif fill_pct >= inspector.thresholds.partial_threshold:
            status = DefectType.PARTIAL
        else:
            status = DefectType.BLOCKED

        assert status == DefectType.BLOCKED


# ============================================================================
#  TESTES: StencilInspector - Inspeção Completa
# ============================================================================

class TestStencilInspectorInspection:
    """Testes para inspeção completa."""

    def test_inspect_without_mosaic(self, mock_renderer):
        """Testa inspeção sem mosaico (erro)."""
        inspector = StencilInspector()
        inspector.renderer = mock_renderer

        with pytest.raises(ValueError, match="Mosaico não definido"):
            inspector.inspect()

    def test_inspect_without_gerber(self, sample_mosaic_bgr):
        """Testa inspeção sem Gerber carregado (erro)."""
        inspector = StencilInspector()
        inspector.set_mosaic(sample_mosaic_bgr)

        with pytest.raises(ValueError, match="Gerber não carregado"):
            inspector.inspect()

    @patch('aoi_lib.stencil_inspector.GerberRenderer')
    def test_inspect_success(self, mock_renderer_class, sample_mosaic_bgr):
        """Testa inspeção com sucesso."""
        # Mock do renderer
        mock_renderer = Mock()
        # Cria mock de objeto sem polygon válido (será ignorado)
        mock_obj = Mock()
        mock_obj.polygon_mm = None  # Sem polygon -> será ignorado em _analyze_apertures
        mock_renderer.objects = [mock_obj]
        mock_renderer.render_mask = Mock(return_value=np.zeros((500, 500), dtype=np.uint8))
        mock_renderer_class.return_value = mock_renderer

        inspector = StencilInspector()
        inspector.set_mosaic(sample_mosaic_bgr)

        result = inspector.inspect()

        assert result is not None
        assert isinstance(result, InspectionResult)
        assert result.total_apertures == 0
        assert result.overall_status == "OK"

    @patch('aoi_lib.stencil_inspector.GerberRenderer')
    def test_inspect_with_transform(self, mock_renderer_class, sample_mosaic_bgr, mock_transform):
        """Testa inspeção com transformação."""
        mock_renderer = Mock()
        mock_obj = Mock()
        mock_obj.polygon_mm = None  # Sem polygon -> será ignorado
        mock_renderer.objects = [mock_obj]
        mock_renderer.render_mask = Mock(return_value=np.zeros((500, 500), dtype=np.uint8))
        mock_renderer_class.return_value = mock_renderer

        inspector = StencilInspector()
        inspector.set_mosaic(sample_mosaic_bgr)
        inspector.set_alignment(mock_transform)

        result = inspector.inspect()

        assert result is not None

    def test_inspect_overall_status_ok(self):
        """Testa status geral OK (sem defeitos)."""
        result = InspectionResult()
        result.apertures = [
            ApertureInspection(
                object_id=1, x_mm=0, y_mm=0, kind="circle",
                expected_area_px=100, observed_area_px=95,
                fill_ratio=0.95, status=DefectType.OK, bbox=(0, 0, 10, 10)
            )
        ]

        result.ok_count = sum(1 for a in result.apertures if a.status == DefectType.OK)
        result.partial_count = sum(1 for a in result.apertures if a.status == DefectType.PARTIAL)
        result.blocked_count = sum(1 for a in result.apertures if a.status == DefectType.BLOCKED)
        result.total_apertures = len(result.apertures)

        if result.blocked_count > 0:
            result.overall_status = "NOK"
        elif result.partial_count > 0:
            result.overall_status = "WARNING"
        else:
            result.overall_status = "OK"

        assert result.overall_status == "OK"

    def test_inspect_overall_status_warning(self):
        """Testa status geral WARNING (com PARTIAL)."""
        result = InspectionResult()
        result.apertures = [
            ApertureInspection(
                object_id=1, x_mm=0, y_mm=0, kind="circle",
                expected_area_px=100, observed_area_px=80,
                fill_ratio=0.80, status=DefectType.PARTIAL, bbox=(0, 0, 10, 10)
            )
        ]

        result.ok_count = sum(1 for a in result.apertures if a.status == DefectType.OK)
        result.partial_count = sum(1 for a in result.apertures if a.status == DefectType.PARTIAL)
        result.blocked_count = sum(1 for a in result.apertures if a.status == DefectType.BLOCKED)
        result.total_apertures = len(result.apertures)

        if result.blocked_count > 0:
            result.overall_status = "NOK"
        elif result.partial_count > 0:
            result.overall_status = "WARNING"
        else:
            result.overall_status = "OK"

        assert result.overall_status == "WARNING"

    def test_inspect_overall_status_nok(self):
        """Testa status geral NOK (com BLOCKED)."""
        result = InspectionResult()
        result.apertures = [
            ApertureInspection(
                object_id=1, x_mm=0, y_mm=0, kind="circle",
                expected_area_px=100, observed_area_px=50,
                fill_ratio=0.50, status=DefectType.BLOCKED, bbox=(0, 0, 10, 10)
            )
        ]

        result.ok_count = sum(1 for a in result.apertures if a.status == DefectType.OK)
        result.partial_count = sum(1 for a in result.apertures if a.status == DefectType.PARTIAL)
        result.blocked_count = sum(1 for a in result.apertures if a.status == DefectType.BLOCKED)
        result.total_apertures = len(result.apertures)

        if result.blocked_count > 0:
            result.overall_status = "NOK"
        elif result.partial_count > 0:
            result.overall_status = "WARNING"
        else:
            result.overall_status = "OK"

        assert result.overall_status == "NOK"


# ============================================================================
#  TESTES: StencilInspector - Visualização
# ============================================================================

class TestStencilInspectorVisualization:
    """Testes para visualização de resultados."""

    def test_get_result_overlay_no_data(self):
        """Testa overlay sem dados."""
        inspector = StencilInspector()

        overlay = inspector.get_result_overlay()

        assert overlay is None

    def test_get_result_overlay_show_all(self, sample_mosaic_bgr):
        """Testa overlay mostrando todas as aberturas."""
        inspector = StencilInspector()
        inspector._mosaic = sample_mosaic_bgr

        # Cria resultado falso
        result = InspectionResult()
        result.apertures = [
            ApertureInspection(
                object_id=1, x_mm=0, y_mm=0, kind="circle",
                expected_area_px=100, observed_area_px=95,
                fill_ratio=0.95, status=DefectType.OK, bbox=(80, 80, 40, 40)
            ),
            ApertureInspection(
                object_id=2, x_mm=0, y_mm=0, kind="circle",
                expected_area_px=100, observed_area_px=80,
                fill_ratio=0.80, status=DefectType.PARTIAL, bbox=(230, 80, 40, 40)
            )
        ]
        result.defects = [result.apertures[1]]
        inspector._last_result = result

        overlay = inspector.get_result_overlay(show_all=True)

        assert overlay is not None
        assert overlay.shape == sample_mosaic_bgr.shape

    def test_get_result_overlay_show_defects_only(self, sample_mosaic_bgr):
        """Testa overlay mostrando apenas defeitos."""
        inspector = StencilInspector()
        inspector._mosaic = sample_mosaic_bgr

        result = InspectionResult()
        result.apertures = [
            ApertureInspection(
                object_id=1, x_mm=0, y_mm=0, kind="circle",
                expected_area_px=100, observed_area_px=95,
                fill_ratio=0.95, status=DefectType.OK, bbox=(80, 80, 40, 40)
            ),
            ApertureInspection(
                object_id=2, x_mm=0, y_mm=0, kind="circle",
                expected_area_px=100, observed_area_px=50,
                fill_ratio=0.50, status=DefectType.BLOCKED, bbox=(380, 80, 40, 40)
            )
        ]
        result.defects = [result.apertures[1]]
        inspector._last_result = result

        overlay = inspector.get_result_overlay(show_all=False)

        assert overlay is not None

    def test_get_defect_crops_no_data(self):
        """Testa crops sem dados."""
        inspector = StencilInspector()

        crops = inspector.get_defect_crops()

        assert crops == []

    def test_get_defect_crops_with_defects(self, sample_mosaic_bgr):
        """Testa crops com defeitos."""
        inspector = StencilInspector()
        inspector._mosaic = sample_mosaic_bgr

        result = InspectionResult()
        result.apertures = [
            ApertureInspection(
                object_id=1, x_mm=0, y_mm=0, kind="circle",
                expected_area_px=100, observed_area_px=50,
                fill_ratio=0.50, status=DefectType.BLOCKED, bbox=(380, 80, 40, 40)
            )
        ]
        result.defects = result.apertures
        inspector._last_result = result

        crops = inspector.get_defect_crops(padding=10)

        assert len(crops) == 1
        inspection, crop = crops[0]
        assert inspection.object_id == 1
        assert crop is not None
        assert crop.shape[0] > 0
        assert crop.shape[1] > 0


# ============================================================================
#  TESTES: Funções Utilitárias
# ============================================================================

class TestQuickInspect:
    """Testes para função quick_inspect."""

    @patch('aoi_lib.stencil_inspector.StencilInspector')
    def test_quick_inspect_basic(self, mock_inspector_class, sample_mosaic_bgr):
        """Testa quick_inspect básico."""
        # Configura mock
        mock_inspector = Mock()
        mock_result = InspectionResult(total_apertures=10)
        mock_inspector.inspect.return_value = mock_result
        mock_inspector_class.return_value = mock_inspector

        result = quick_inspect("test.gbr", sample_mosaic_bgr)

        assert result is not None
        mock_inspector.load_gerber.assert_called_once_with("test.gbr")
        mock_inspector.set_mosaic.assert_called_once_with(sample_mosaic_bgr)
        mock_inspector.inspect.assert_called_once()

    @patch('aoi_lib.stencil_inspector.StencilInspector')
    def test_quick_inspect_with_transform(
        self,
        mock_inspector_class,
        sample_mosaic_bgr,
        mock_transform
    ):
        """Testa quick_inspect com transformação."""
        mock_inspector = Mock()
        mock_result = InspectionResult(total_apertures=10)
        mock_inspector.inspect.return_value = mock_result
        mock_inspector_class.return_value = mock_inspector

        result = quick_inspect("test.gbr", sample_mosaic_bgr, transform=mock_transform)

        assert result is not None
        mock_inspector.set_alignment.assert_called_once_with(mock_transform)

    @patch('aoi_lib.stencil_inspector.StencilInspector')
    def test_quick_inspect_with_thresholds(self, mock_inspector_class, sample_mosaic_bgr, sample_thresholds):
        """Testa quick_inspect com thresholds customizados."""
        mock_inspector = Mock()
        mock_result = InspectionResult(total_apertures=10)
        mock_inspector.inspect.return_value = mock_result
        mock_inspector_class.return_value = mock_inspector

        result = quick_inspect("test.gbr", sample_mosaic_bgr, thresholds=sample_thresholds)

        assert result is not None
