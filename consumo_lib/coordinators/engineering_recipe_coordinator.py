"""
EngineeringRecipeCoordinator - Conversor entre ProgramConfig e Recipe

Este módulo coordena a conversão bidirecional entre:
- ProgramConfig: Configuração do Engineering Wizard (novo)
- Recipe: Receita do sistema RecipeManager (legado)

Mapeamento de campos:
- ProgramConfig → Recipe: Conversão de wizard para receita
- Recipe → ProgramConfig: Edição de receita existente
- Validação: Verifica se conversão é possível

Author: Claude Code (Sonnet 4.5)
Date: 2026-01-13
"""

import logging
from typing import Tuple, Dict, List, Optional
from datetime import datetime

from consumo_lib.models.engineering.program_config import (
    ProgramConfig,
    FiducialConfig,
    MosaicConfig,
    AlignmentConfig
)
from aoi_lib.recipe_manager import (
    Recipe,
    StencilInfo,
    TensionConfig,
    CaptureConfig,
    InspectionConfig,
    Point2D
)

logger = logging.getLogger(__name__)


class EngineeringRecipeCoordinator:
    """
    Coordenador para conversão entre ProgramConfig e Recipe.

    Responsabilidades:
    - Converter ProgramConfig → Recipe (criar receita do wizard)
    - Converter Recipe → ProgramConfig (editar receita existente)
    - Validar se conversão é possível
    - Mapear campos entre os dois modelos
    """

    # Constantes para conversão
    DEFAULT_STENCIL_WIDTH = 400.0  # mm
    DEFAULT_STENCIL_HEIGHT = 300.0  # mm
    DEFAULT_STENCIL_THICKNESS = 0.12  # mm
    DEFAULT_STENCIL_MATERIAL = "Inox"

    DEFAULT_TENSION_MIN = 25.0  # N/cm²
    DEFAULT_TENSION_MAX = 45.0  # N/cm²

    DEFAULT_CAPTURE_STEP = 50.0  # mm
    DEFAULT_CAPTURE_DELAY = 200  # ms

    DEFAULT_INSPECTION_MIN_PERCENT = 70  # %
    DEFAULT_INSPECTION_THRESHOLD = 128

    # ========================================================================
    #  CONVERSÃO PROGRAMCONFIG → RECIPE
    # ========================================================================

    def program_to_recipe(self, program: ProgramConfig) -> Recipe:
        """
        Converte ProgramConfig para Recipe.

        Args:
            program: Configuração do programa do Engineering Wizard

        Returns:
            Recipe instância compatível com RecipeManager

        Raises:
            ValueError: Se conversão não for possível
        """
        logger.info(f"Convertendo ProgramConfig → Recipe: {program.program_name}")

        # Valida antes de converter
        can_convert, error_msg = self.can_convert_to_recipe(program)
        if not can_convert:
            raise ValueError(f"Cannot convert to Recipe: {error_msg}")

        # Mapeia campos
        recipe = Recipe(
            name=program.program_name,
            version=program.version.replace("v", ""),  # Remove "v" do version
            created_at=program.created_at,
            modified_at=program.modified_at or program.created_at,
            created_by=program.created_by or "Engineering Wizard",

            # StencilInfo (do ProgramConfig)
            stencil=self._convert_stencil_info(program),

            # TensionConfig (do ProgramConfig se disponível)
            tension=self._convert_tension_config(program),

            # CaptureConfig (do mosaic config)
            capture=self._convert_capture_config(program),

            # InspectionConfig (dos inspection groups)
            inspection=self._convert_inspection_config(program)
        )

        logger.info(f"✅ Recipe criada: {recipe.name} ({recipe.recipe_id})")
        return recipe

    def _convert_stencil_info(self, program: ProgramConfig) -> StencilInfo:
        """
        Converte dados do stencil do ProgramConfig.

        Args:
            program: ProgramConfig

        Returns:
            StencilInfo
        """
        # Extrai dimensões do Gerber se disponível
        width = program.gerber_dimensions.get("width", self.DEFAULT_STENCIL_WIDTH)
        height = program.gerber_dimensions.get("height", self.DEFAULT_STENCIL_HEIGHT)

        # Se dimensões do Gerber forem 0, usa defaults
        if width == 0.0:
            width = self.DEFAULT_STENCIL_WIDTH
        if height == 0.0:
            height = self.DEFAULT_STENCIL_HEIGHT

        return StencilInfo(
            width_mm=width,
            height_mm=height,
            thickness_mm=self.DEFAULT_STENCIL_THICKNESS,
            material=self.DEFAULT_STENCIL_MATERIAL,
            notes=f"Criado via Engineering Wizard a partir de {program.stencil_code}"
        )

    def _convert_tension_config(self, program: ProgramConfig) -> TensionConfig:
        """
        Converte configuração de tensão do ProgramConfig.

        NOTA: ProgramConfig não tem dados de tensão, retorna config disabled.

        Args:
            program: ProgramConfig

        Returns:
            TensionConfig (disabled por padrão)
        """
        return TensionConfig(
            enabled=False,  # ProgramConfig não tem dados de tensão
            grid_rows=3,
            grid_cols=3,
            start_point=Point2D(x=0.0, y=0.0),
            end_point=Point2D(x=100.0, y=100.0)
        )

    def _convert_capture_config(self, program: ProgramConfig) -> CaptureConfig:
        """
        Converte configuração de captura do ProgramConfig.

        Args:
            program: ProgramConfig

        Returns:
            CaptureConfig
        """
        # Calcula step baseado no grid do mosaico
        if program.mosaic.grid_rows > 0 and program.mosaic.grid_cols > 0:
            width = abs(program.mosaic.corner2.get("x", 0.0) - program.mosaic.corner1.get("x", 0.0))
            height = abs(program.mosaic.corner2.get("y", 0.0) - program.mosaic.corner1.get("y", 0.0))

            step_x = width / (program.mosaic.grid_cols - 1) if program.mosaic.grid_cols > 1 else self.DEFAULT_CAPTURE_STEP
            step_y = height / (program.mosaic.grid_rows - 1) if program.mosaic.grid_rows > 1 else self.DEFAULT_CAPTURE_STEP
        else:
            step_x = self.DEFAULT_CAPTURE_STEP
            step_y = self.DEFAULT_CAPTURE_STEP

        return CaptureConfig(
            enabled=True,
            step_x=step_x,
            step_y=step_y,
            capture_delay_ms=program.mosaic.capture_delay_ms,
            backlight_enabled=True,
            origin=Point2D(
                x=program.mosaic.corner1.get("x", 0.0),
                y=program.mosaic.corner1.get("y", 0.0)
            ),
            end=Point2D(
                x=program.mosaic.corner2.get("x", 100.0),
                y=program.mosaic.corner2.get("y", 100.0)
            ),
            feed_rate=2000.0
        )

    def _convert_inspection_config(self, program: ProgramConfig) -> InspectionConfig:
        """
        Converte configuração de inspeção do ProgramConfig.

        Args:
            program: ProgramConfig

        Returns:
            InspectionConfig
        """
        # Se houver grupos configurados, usa thresholds do primeiro grupo
        if program.inspection_groups:
            first_group = program.inspection_groups[0]
            min_percent = first_group.ok_threshold
        else:
            min_percent = self.DEFAULT_INSPECTION_MIN_PERCENT

        return InspectionConfig(
            enabled=True,
            default_min_percent=int(min_percent),
            target_color="black",  # Stencil inspection usa backlight
            default_threshold=self.DEFAULT_INSPECTION_THRESHOLD,
            gerber_file=program.gerber_file or "",
            masks=[]  # Masks são gerados dinamicamente pelo GerberRenderer
        )

    # ========================================================================
    #  CONVERSÃO RECIPE → PROGRAMCONFIG
    # ========================================================================

    def recipe_to_program(self, recipe: Recipe, program_name: Optional[str] = None) -> ProgramConfig:
        """
        Converte Recipe para ProgramConfig (edição).

        Args:
            recipe: Recipe existente
            program_name: Nome customizado (opcional, usa recipe.name se None)

        Returns:
            ProgramConfig para edição no Engineering Wizard

        Raises:
            ValueError: Se conversão não for possível
        """
        logger.info(f"Convertendo Recipe → ProgramConfig: {recipe.name}")

        # Usa nome fornecido ou nome da recipe
        name = program_name or recipe.name

        # Extrai código do stencil do nome (se seguir padrão)
        # Ex: "STENCIL-ABC-123" → "STENCIL-ABC-123"
        stencil_code = self._extract_stencil_code(name)

        # Mapeia campos
        program = ProgramConfig(
            # Aba 1: Dados do Programa
            stencil_code=stencil_code,
            program_name=name,
            description=f"Editado de Recipe: {recipe.recipe_id}",
            version=f"v{recipe.version}",
            recipe_name=recipe.name,

            # Aba 2: Gerber
            gerber_file=recipe.inspection.gerber_file,
            gerber_dimensions={
                "width": recipe.stencil.width_mm,
                "height": recipe.stencil.height_mm
            },
            aperture_count=0,  # Não disponível na Recipe
            detected_fiducials=0,  # Não disponível na Recipe

            # Aba 3: Fiduciais (vazio - precisa ser recapturado)
            fiducials=FiducialConfig(),

            # Aba 4: Mosaico (da CaptureConfig)
            mosaic=MosaicConfig(
                corner1={"x": recipe.capture.origin.x, "y": recipe.capture.origin.y},
                corner2={"x": recipe.capture.end.x, "y": recipe.capture.end.y},
                grid_rows=3,  # Default
                grid_cols=3,  # Default
                total_fovs=9,  # Default
                capture_delay_ms=recipe.capture.capture_delay_ms
            ),

            # Aba 5: Alinhamento (vazio - precisa ser recalculado)
            alignment=AlignmentConfig(),

            # Aba 6: Janelas de Inspeção (vazio - precisa ser reconfigurado)
            inspection_groups=[],
            total_apertures=0,

            # Metadados
            created_at=recipe.created_at,
            created_by=recipe.created_by,
            modified_at=recipe.modified_at,
            modified_by=recipe.created_by,
            notes=f"Convertido de Recipe {recipe.recipe_id}"
        )

        logger.info(f"✅ ProgramConfig criado: {program.program_name}")
        return program

    def _extract_stencil_code(self, name: str) -> str:
        """
        Extrai código do stencil de um nome.

        Args:
            name: Nome do programa/recipe

        Returns:
            Código do stencil (ou "UNKNOWN" se não conseguir extrair)
        """
        # Tenta padrão "STENCIL-XXX"
        if "STENCIL-" in name.upper():
            return name.split()[0]  # Primeira palavra

        # Se não seguir padrão, retorna upper case do nome
        return name.upper().replace(" ", "_")

    # ========================================================================
    #  VALIDAÇÃO
    # ========================================================================

    def can_convert_to_recipe(self, program: ProgramConfig) -> Tuple[bool, str]:
        """
        Verifica se ProgramConfig pode ser convertido para Recipe.

        Args:
            program: ProgramConfig a validar

        Returns:
            Tuple (can_convert, error_message)
            - can_convert: True se conversão é possível
            - error_message: Mensagem de erro se não for possível
        """
        # Verifica campos obrigatórios
        if not program.stencil_code:
            return False, "stencil_code é obrigatório"

        if not program.program_name:
            return False, "program_name é obrigatório"

        # Verifica se tem dados de Gerber
        if not program.gerber_file:
            return False, "gerber_file não foi definido"

        # Verifica se tem mosaico configurado
        if program.mosaic.total_fovs == 0:
            return False, "mosaico não foi capturado (total_fovs = 0)"

        # Verifica se tem alinhamento
        if program.alignment.alignment_score < 50.0:
            return False, f"score de alinhamento muito baixo: {program.alignment.alignment_score:.1f}%"

        # Verifica se tem pelo menos um grupo de inspeção
        if not program.inspection_groups:
            logger.warning("ProgramConfig não tem grupos de inspeção - usando defaults")

        return True, ""

    def can_convert_to_program(self, recipe: Recipe) -> Tuple[bool, str]:
        """
        Verifica se Recipe pode ser convertido para ProgramConfig.

        Args:
            recipe: Recipe a validar

        Returns:
            Tuple (can_convert, error_message)
        """
        # Verifica campos obrigatórios
        if not recipe.name:
            return False, "recipe.name é obrigatório"

        # Verifica se tem arquivo Gerber
        if not recipe.inspection.gerber_file:
            return False, "recipe.inspection.gerber_file não foi definido"

        # Verifica dimensões do stencil
        if recipe.stencil.width_mm <= 0 or recipe.stencil.height_mm <= 0:
            return False, "dimensões do stencil inválidas"

        return True, ""

    # ========================================================================
    #  UTILITÁRIOS
    # ========================================================================

    def get_conversion_summary(self, program: ProgramConfig) -> Dict[str, any]:
        """
        Retorna resumo da conversão ProgramConfig → Recipe.

        Args:
            program: ProgramConfig a converter

        Returns:
            Dicionário com resumo da conversão
        """
        can_convert, error_msg = self.can_convert_to_recipe(program)

        return {
            "program_name": program.program_name,
            "can_convert": can_convert,
            "error_message": error_msg,
            "stencil_code": program.stencil_code,
            "gerber_file": program.gerber_file,
            "aperture_count": program.aperture_count,
            "mosaic_fovs": program.mosaic.total_fovs,
            "alignment_score": program.alignment.alignment_score,
            "inspection_groups": len(program.inspection_groups),
            "recipe_name": program.program_name,
            "recipe_version": program.version,
        }
