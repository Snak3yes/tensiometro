"""
dialogs package - Diálogos configuráveis da aplicação.
"""
from .fov_calibration import FOVCalibrationDialog
from .crosshair_settings import CrosshairSettingsDialog
from .inspection_settings import InspectionSettingsDialog
from .report_settings import ReportSettingsDialog
from .about import AboutDialog

# Recipe dialogs
from .recipe_dialogs import (
    RecipeListWidget,
    RecipeEditorDialog,
    RecipeManagerDialog
)

# Stencil dialogs (de outros módulos, exportados aqui para conveniência)
from aoi_lib.stencil_tracker_ui import StencilManagerDialog, StencilCreateDialog
from aoi_lib.stencil_tension import StencilTensionDialog

__all__ = [
    # Calibration & Settings
    'FOVCalibrationDialog',
    'CrosshairSettingsDialog',
    'InspectionSettingsDialog',
    'ReportSettingsDialog',
    'AboutDialog',
    # Recipe
    'RecipeListWidget',
    'RecipeEditorDialog',
    'RecipeManagerDialog',
    # Stencil & Tension
    'StencilManagerDialog',
    'StencilCreateDialog',
    'StencilTensionDialog',
]

# TODO: Mover diálogos restantes em fases futuras:
# - CameraSettingsDialog (precisa verificar se existe)
# - CalibrationTestDialog (precisa verificar se existe)
# - MapDefinitionDialog (show_definir_mapa_dialog - ~421 linhas, médio)
