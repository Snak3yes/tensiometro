"""
dialogs package
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

__all__ = [
    'FOVCalibrationDialog',
    'CrosshairSettingsDialog',
    'InspectionSettingsDialog',
    'ReportSettingsDialog',
    'AboutDialog',
    'RecipeListWidget',
    'RecipeEditorDialog',
    'RecipeManagerDialog'
]

# TODO: Mover diálogos restantes em fases futuras:
# - CameraSettingsDialog (precisa verificar se existe)
# - CalibrationTestDialog (precisa verificar se existe)
# - StencilTensionDialog (stencil_tension.py - 962 linhas, muito grande)
# - FiducialAlignmentDialog (FiducialAlignmentWidget - 959 linhas, muito grande)
# - MapDefinitionDialog (show_definir_mapa_dialog - ~421 linhas, médio)
