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
from consumo_lib.dialogs.stencil import (
    StencilManagerDialog,
    StencilCreateDialog,
    StencilHistoryDialog,
    StencilEditDialog,
    StencilFullHistoryDialog,
)
# Tension measurement dialog (refactored 2026-01-14)
# Import with alias for backward compatibility
from consumo_lib.dialogs.tension import TensionMeasurementDialog as StencilTensionDialog

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
    'StencilHistoryDialog',
    'StencilEditDialog',
    'StencilFullHistoryDialog',
    'StencilTensionDialog',
]

# TODO: Mover diálogos restantes em fases futuras:
# - CameraSettingsDialog (precisa verificar se existe)
# - CalibrationTestDialog (precisa verificar se existe)
# - MapDefinitionDialog (show_definir_mapa_dialog - ~421 linhas, médio)

# Auth dialogs (NOVO - FASE 1)
from .login_dialog import LoginDialog
__all__.append('LoginDialog')

# Positioning dialogs (NOVO - FASE 3)
from .confirm_positioning_dialog import ConfirmPositioningDialog
__all__.append('ConfirmPositioningDialog')

# Mode selection dialogs (NOVO - FASE 4)
from .mode_selection_dialog import ModeSelectionDialog
__all__.append('ModeSelectionDialog')

# Progress dialogs (NOVO - FASE 5)
from .inspection_progress_dialog import InspectionProgressDialog
__all__.append('InspectionProgressDialog')

# Results dialogs (NOVO - FASE 6)
from .inspection_results_dialog import InspectionResultsDialog
__all__.append('InspectionResultsDialog')

# History dialogs (NOVO - FASE 7)
from .inspection_history_dialog import InspectionHistoryDialog
__all__.append('InspectionHistoryDialog')

# Final decision dialogs (NOVO - FASE 5)
from .final_decision_dialog import FinalDecisionDialog
__all__.append('FinalDecisionDialog')

# Defect judgment dialogs (NOVO - FASE 5)
from .defect_judgment_dialog import DefectJudgmentDialog
__all__.append('DefectJudgmentDialog')

# Operator workflow dialogs (NOVO - FASE 3)
from .operator_workflow_dialog import OperatorWorkflowDialog
__all__.append('OperatorWorkflowDialog')

# Engineering Wizard dialog (NOVO - FASE 1)
from .engineering_wizard_dialog import EngineeringWizardDialog
__all__.append('EngineeringWizardDialog')
