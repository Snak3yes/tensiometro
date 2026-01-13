"""
Testes unitários para EngineeringRecipeCoordinator

Testa conversão bidirecional entre:
- ProgramConfig (Engineering Wizard)
- Recipe (RecipeManager legado)

Funcionalidades testadas:
- Conversão ProgramConfig → Recipe
- Conversão Recipe → ProgramConfig
- Validação de conversão
- Mapeamento de campos
- Roundtrip (ProgramConfig → Recipe → ProgramConfig)
"""

import pytest
from datetime import datetime

from consumo_lib.coordinators.engineering_recipe_coordinator import EngineeringRecipeCoordinator
from consumo_lib.models.engineering.program_config import (
    ProgramConfig,
    FiducialConfig,
    MosaicConfig,
    AlignmentConfig,
    InspectionGroupConfig
)
from aoi_lib.recipe_manager import (
    Recipe,
    StencilInfo,
    TensionConfig,
    CaptureConfig,
    InspectionConfig,
    Point2D
)


class TestProgramToRecipe:
    """Testes para conversão ProgramConfig → Recipe."""

    @pytest.fixture
    def coordinator(self):
        """Cria coordinator."""
        return EngineeringRecipeCoordinator()

    @pytest.fixture
    def valid_program(self):
        """Cria ProgramConfig válido para conversão."""
        return ProgramConfig(
            stencil_code="STENCIL-001",
            program_name="Test Program",
            description="Test program for conversion",
            version="v1.0",
            gerber_file="test.ger",
            gerber_dimensions={"width": 400.0, "height": 300.0},
            aperture_count=100,
            fiducials=FiducialConfig(
                fiducial1={"x": 10.0, "y": 20.0},
                fiducial2={"x": 30.0, "y": 40.0}
            ),
            mosaic=MosaicConfig(
                corner1={"x": 0.0, "y": 0.0},
                corner2={"x": 300.0, "y": 200.0},
                grid_rows=4,
                grid_cols=4,
                total_fovs=16,
                capture_delay_ms=200
            ),
            alignment=AlignmentConfig(
                translation_x=1.0,
                translation_y=2.0,
                rotation=0.5,
                scale=1.0,
                alignment_score=95.0
            ),
            inspection_groups=[
                InspectionGroupConfig(
                    name="0.5mm Circle",
                    aperture_count=50,
                    ok_threshold=90.0,
                    confirmed=True
                )
            ],
            created_by="test_user"
        )

    def test_convert_valid_program(self, coordinator, valid_program):
        """Testa conversão de programa válido."""
        recipe = coordinator.program_to_recipe(valid_program)

        assert recipe.name == "Test Program"
        assert recipe.version == "1.0"
        assert recipe.created_by == "test_user"
        assert recipe.stencil.width_mm == 400.0
        assert recipe.stencil.height_mm == 300.0
        assert recipe.capture.enabled
        assert recipe.inspection.enabled

    def test_convert_stencil_info(self, coordinator, valid_program):
        """Testa conversão de StencilInfo."""
        recipe = coordinator.program_to_recipe(valid_program)

        assert recipe.stencil.width_mm == 400.0
        assert recipe.stencil.height_mm == 300.0
        assert recipe.stencil.thickness_mm == 0.12
        assert recipe.stencil.material == "Inox"

    def test_convert_capture_config(self, coordinator, valid_program):
        """Testa conversão de CaptureConfig."""
        recipe = coordinator.program_to_recipe(valid_program)

        assert recipe.capture.enabled
        assert recipe.capture.capture_delay_ms == 200
        assert recipe.capture.origin.x == 0.0
        assert recipe.capture.origin.y == 0.0
        assert recipe.capture.end.x == 300.0
        assert recipe.capture.end.y == 200.0

    def test_convert_inspection_config(self, coordinator, valid_program):
        """Testa conversão de InspectionConfig."""
        recipe = coordinator.program_to_recipe(valid_program)

        assert recipe.inspection.enabled
        assert recipe.inspection.gerber_file == "test.ger"
        assert recipe.inspection.default_min_percent == 90
        assert recipe.inspection.target_color == "black"

    def test_convert_tension_config_disabled(self, coordinator, valid_program):
        """Testa que TensionConfig é criado disabled."""
        recipe = coordinator.program_to_recipe(valid_program)

        assert not recipe.tension.enabled

    def test_convert_program_without_gerber_dimensions(self, coordinator):
        """Testa conversão com dimensões do Gerber não definidas."""
        program = ProgramConfig(
            stencil_code="STENCIL-001",
            program_name="Test",
            version="v1.0",
            gerber_file="test.ger",
            gerber_dimensions={"width": 0.0, "height": 0.0},
            fiducials=FiducialConfig(),
            mosaic=MosaicConfig(
                corner1={"x": 0.0, "y": 0.0},
                corner2={"x": 100.0, "y": 100.0},
                total_fovs=9
            ),
            alignment=AlignmentConfig(alignment_score=90.0)
        )

        recipe = coordinator.program_to_recipe(program)

        # Deve usar defaults
        assert recipe.stencil.width_mm == coordinator.DEFAULT_STENCIL_WIDTH
        assert recipe.stencil.height_mm == coordinator.DEFAULT_STENCIL_HEIGHT

    def test_convert_invalid_program_no_stencil_code(self, coordinator):
        """Testa erro quando stencil_code está vazio."""
        program = ProgramConfig(
            stencil_code="",  # Vazio
            program_name="Test",
            version="v1.0"
        )

        with pytest.raises(ValueError, match="stencil_code é obrigatório"):
            coordinator.program_to_recipe(program)

    def test_convert_invalid_program_no_gerber(self, coordinator):
        """Testa erro quando gerber_file não está definido."""
        program = ProgramConfig(
            stencil_code="STENCIL-001",
            program_name="Test",
            version="v1.0",
            gerber_file=None  # Não definido
        )

        with pytest.raises(ValueError, match="gerber_file não foi definido"):
            coordinator.program_to_recipe(program)

    def test_convert_invalid_program_no_mosaic(self, coordinator):
        """Testa erro quando mosaico não foi capturado."""
        program = ProgramConfig(
            stencil_code="STENCIL-001",
            program_name="Test",
            version="v1.0",
            gerber_file="test.ger",
            mosaic=MosaicConfig(total_fovs=0),  # Vazio
            alignment=AlignmentConfig(alignment_score=90.0)
        )

        with pytest.raises(ValueError, match="mosaico não foi capturado"):
            coordinator.program_to_recipe(program)

    def test_convert_invalid_program_low_alignment_score(self, coordinator):
        """Testa erro quando score de alinhamento é muito baixo."""
        program = ProgramConfig(
            stencil_code="STENCIL-001",
            program_name="Test",
            version="v1.0",
            gerber_file="test.ger",
            mosaic=MosaicConfig(total_fovs=9),
            alignment=AlignmentConfig(alignment_score=30.0)  # Muito baixo
        )

        with pytest.raises(ValueError, match="score de alinhamento muito baixo"):
            coordinator.program_to_recipe(program)


class TestRecipeToProgram:
    """Testes para conversão Recipe → ProgramConfig."""

    @pytest.fixture
    def coordinator(self):
        """Cria coordinator."""
        return EngineeringRecipeCoordinator()

    @pytest.fixture
    def valid_recipe(self):
        """Cria Recipe válida para conversão."""
        return Recipe(
            name="Test Recipe",
            version="2.0",
            created_at="2026-01-13T10:00:00",
            created_by="test_user",
            stencil=StencilInfo(
                width_mm=500.0,
                height_mm=400.0,
                thickness_mm=0.15,
                material="Inox"
            ),
            tension=TensionConfig(
                enabled=True,
                grid_rows=3,
                grid_cols=3
            ),
            capture=CaptureConfig(
                enabled=True,
                step_x=50.0,
                step_y=50.0,
                origin=Point2D(x=0.0, y=0.0),
                end=Point2D(x=300.0, y=200.0),
                capture_delay_ms=250
            ),
            inspection=InspectionConfig(
                enabled=True,
                default_min_percent=85,
                gerber_file="recipe_test.ger"
            )
        )

    def test_convert_valid_recipe(self, coordinator, valid_recipe):
        """Testa conversão de recipe válida."""
        program = coordinator.recipe_to_program(valid_recipe)

        assert program.program_name == "Test Recipe"
        assert program.description == f"Editado de Recipe: {valid_recipe.recipe_id}"
        assert program.version == "v2.0"
        assert program.created_by == "test_user"

    def test_convert_uses_recipe_name(self, coordinator, valid_recipe):
        """Testa que nome da recipe é usado se não fornecido."""
        program = coordinator.recipe_to_program(valid_recipe)

        assert program.program_name == "Test Recipe"

    def test_convert_custom_name(self, coordinator, valid_recipe):
        """Testa uso de nome customizado."""
        program = coordinator.recipe_to_program(
            valid_recipe,
            program_name="Custom Name"
        )

        assert program.program_name == "Custom Name"

    def test_convert_stencil_info(self, coordinator, valid_recipe):
        """Testa conversão de StencilInfo."""
        program = coordinator.recipe_to_program(valid_recipe)

        assert program.gerber_dimensions["width"] == 500.0
        assert program.gerber_dimensions["height"] == 400.0

    def test_convert_capture_config(self, coordinator, valid_recipe):
        """Testa conversão de CaptureConfig para MosaicConfig."""
        program = coordinator.recipe_to_program(valid_recipe)

        assert program.mosaic.corner1["x"] == 0.0
        assert program.mosaic.corner1["y"] == 0.0
        assert program.mosaic.corner2["x"] == 300.0
        assert program.mosaic.corner2["y"] == 200.0
        assert program.mosaic.capture_delay_ms == 250

    def test_convert_inspection_config(self, coordinator, valid_recipe):
        """Testa conversão de InspectionConfig."""
        program = coordinator.recipe_to_program(valid_recipe)

        assert program.gerber_file == "recipe_test.ger"

    def test_convert_empty_fiducials(self, coordinator, valid_recipe):
        """Testa que fiduciais ficam vazios (precisa ser recapturado)."""
        program = coordinator.recipe_to_program(valid_recipe)

        assert program.fiducials.fiducial1 == {"x": 0.0, "y": 0.0}
        assert program.fiducials.fiducial2 == {"x": 0.0, "y": 0.0}

    def test_convert_empty_alignment(self, coordinator, valid_recipe):
        """Testa que alinhamento fica vazio (precisa ser recalculado)."""
        program = coordinator.recipe_to_program(valid_recipe)

        assert program.alignment.translation_x == 0.0
        assert program.alignment.translation_y == 0.0
        assert program.alignment.rotation == 0.0
        assert program.alignment.scale == 1.0

    def test_convert_empty_inspection_groups(self, coordinator, valid_recipe):
        """Testa que grupos de inspeção ficam vazios."""
        program = coordinator.recipe_to_program(valid_recipe)

        assert len(program.inspection_groups) == 0

    def test_extract_stencil_code(self, coordinator):
        """Testa extração de código do stencil."""
        # Padrão STENCIL-XXX
        assert coordinator._extract_stencil_code("STENCIL-ABC-123 Test") == "STENCIL-ABC-123"

        # Sem padrão
        result = coordinator._extract_stencil_code("Test Program")
        assert result == "TEST_PROGRAM"

    def test_convert_invalid_recipe_no_name(self, coordinator):
        """Testa erro quando recipe não tem nome."""
        recipe = Recipe(
            name="",  # Vazio
            version="1.0"
        )

        with pytest.raises(ValueError, match="recipe.name é obrigatório"):
            coordinator.recipe_to_program(recipe)

    def test_convert_invalid_recipe_no_gerber(self, coordinator):
        """Testa erro quando recipe não tem arquivo Gerber."""
        recipe = Recipe(
            name="Test",
            version="1.0",
            inspection=InspectionConfig(gerber_file="")  # Vazio
        )

        with pytest.raises(ValueError, match="gerber_file não foi definido"):
            coordinator.recipe_to_program(recipe)

    def test_convert_invalid_recipe_invalid_dimensions(self, coordinator):
        """Testa erro quando dimensões são inválidas."""
        recipe = Recipe(
            name="Test",
            version="1.0",
            stencil=StencilInfo(width_mm=0.0, height_mm=0.0),  # Inválido
            inspection=InspectionConfig(gerber_file="test.ger")
        )

        with pytest.raises(ValueError, match="dimensões do stencil inválidas"):
            coordinator.recipe_to_program(recipe)


class TestValidation:
    """Testes para validação de conversão."""

    @pytest.fixture
    def coordinator(self):
        """Cria coordinator."""
        return EngineeringRecipeCoordinator()

    def test_can_convert_to_recipe_valid(self, coordinator):
        """Testa validação de programa válido."""
        program = ProgramConfig(
            stencil_code="STENCIL-001",
            program_name="Test",
            version="v1.0",
            gerber_file="test.ger",
            mosaic=MosaicConfig(total_fovs=9),
            alignment=AlignmentConfig(alignment_score=90.0)
        )

        can_convert, error_msg = coordinator.can_convert_to_recipe(program)

        assert can_convert
        assert error_msg == ""

    def test_can_convert_to_recipe_invalid_no_code(self, coordinator):
        """Testa validação sem código do stencil."""
        program = ProgramConfig(
            stencil_code="",  # Vazio
            program_name="Test",
            version="v1.0"
        )

        can_convert, error_msg = coordinator.can_convert_to_recipe(program)

        assert not can_convert
        assert "stencil_code" in error_msg

    def test_can_convert_to_recipe_invalid_no_gerber(self, coordinator):
        """Testa validação sem arquivo Gerber."""
        program = ProgramConfig(
            stencil_code="STENCIL-001",
            program_name="Test",
            version="v1.0",
            gerber_file=None  # Não definido
        )

        can_convert, error_msg = coordinator.can_convert_to_recipe(program)

        assert not can_convert
        assert "gerber_file" in error_msg

    def test_can_convert_to_program_valid(self, coordinator):
        """Testa validação de recipe válida."""
        recipe = Recipe(
            name="Test",
            version="1.0",
            stencil=StencilInfo(width_mm=400.0, height_mm=300.0),
            inspection=InspectionConfig(gerber_file="test.ger")
        )

        can_convert, error_msg = coordinator.can_convert_to_program(recipe)

        assert can_convert
        assert error_msg == ""

    def test_can_convert_to_program_invalid_no_name(self, coordinator):
        """Testa validação de recipe sem nome."""
        recipe = Recipe(
            name="",  # Vazio
            version="1.0"
        )

        can_convert, error_msg = coordinator.can_convert_to_program(recipe)

        assert not can_convert
        assert "recipe.name" in error_msg


class TestConversionSummary:
    """Testes para resumo de conversão."""

    @pytest.fixture
    def coordinator(self):
        """Cria coordinator."""
        return EngineeringRecipeCoordinator()

    def test_get_conversion_summary_valid(self, coordinator):
        """Testa resumo de conversão de programa válido."""
        program = ProgramConfig(
            stencil_code="STENCIL-001",
            program_name="Test Program",
            version="v1.0",
            gerber_file="test.ger",
            aperture_count=100,
            mosaic=MosaicConfig(total_fovs=16),
            alignment=AlignmentConfig(alignment_score=95.0),
            inspection_groups=[
                InspectionGroupConfig(name="Group 1", aperture_count=50),
                InspectionGroupConfig(name="Group 2", aperture_count=50)
            ]
        )

        summary = coordinator.get_conversion_summary(program)

        assert summary["program_name"] == "Test Program"
        assert summary["can_convert"] is True
        assert summary["error_message"] == ""
        assert summary["stencil_code"] == "STENCIL-001"
        assert summary["aperture_count"] == 100
        assert summary["mosaic_fovs"] == 16
        assert summary["alignment_score"] == 95.0
        assert summary["inspection_groups"] == 2

    def test_get_conversion_summary_invalid(self, coordinator):
        """Testa resumo de conversão de programa inválido."""
        program = ProgramConfig(
            stencil_code="",  # Inválido
            program_name="Test",
            version="v1.0"
        )

        summary = coordinator.get_conversion_summary(program)

        assert summary["can_convert"] is False
        assert len(summary["error_message"]) > 0


class TestRoundtrip:
    """Testes de conversão bidirecional (roundtrip)."""

    @pytest.fixture
    def coordinator(self):
        """Cria coordinator."""
        return EngineeringRecipeCoordinator()

    def test_roundtrip_preserves_name(self, coordinator):
        """Testa se nome é preservado no roundtrip."""
        original_program = ProgramConfig(
            stencil_code="STENCIL-001",
            program_name="Roundtrip Test",
            version="v1.0",
            gerber_file="test.ger",
            mosaic=MosaicConfig(total_fovs=9),
            alignment=AlignmentConfig(alignment_score=90.0)
        )

        # ProgramConfig → Recipe
        recipe = coordinator.program_to_recipe(original_program)

        # Recipe → ProgramConfig
        restored_program = coordinator.recipe_to_program(recipe)

        # Verifica nome
        assert restored_program.program_name == original_program.program_name

    def test_roundtrip_preserves_gerber_file(self, coordinator):
        """Testa se arquivo Gerber é preservado."""
        original_program = ProgramConfig(
            stencil_code="STENCIL-001",
            program_name="Test",
            version="v1.0",
            gerber_file="test.ger",
            mosaic=MosaicConfig(total_fovs=9),
            alignment=AlignmentConfig(alignment_score=90.0)
        )

        recipe = coordinator.program_to_recipe(original_program)
        restored_program = coordinator.recipe_to_program(recipe)

        assert restored_program.gerber_file == original_program.gerber_file

    def test_roundtrip_preserves_version(self, coordinator):
        """Testa se versão é preservada."""
        original_program = ProgramConfig(
            stencil_code="STENCIL-001",
            program_name="Test",
            version="v2.5",
            gerber_file="test.ger",
            mosaic=MosaicConfig(total_fovs=9),
            alignment=AlignmentConfig(alignment_score=90.0)
        )

        recipe = coordinator.program_to_recipe(original_program)
        restored_program = coordinator.recipe_to_program(recipe)

        assert restored_program.version == original_program.version
