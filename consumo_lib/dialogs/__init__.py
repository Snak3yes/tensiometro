"""
dialogs package - Diálogos configuráveis da aplicação.
"""
from .fov_calibration import FOVCalibrationDialog
from .crosshair_settings import CrosshairSettingsDialog
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

# Authentication settings dialog (NOVO - 2026-01-15)
from .auth_settings_dialog import AuthenticationSettingsDialog
__all__.append('AuthenticationSettingsDialog')

# Theme Settings dialog (NOVO - FASE 8)
from .theme_settings import ThemeSettingsDialog, show_theme_settings_dialog
__all__.append('ThemeSettingsDialog')
__all__.append('show_theme_settings_dialog')

# Movement dialog (NOVO - release/v0.5-tension)
from .movement_dialog import MovementDialog
__all__.append('MovementDialog')

# PLC Monitor dialog (NOVO - release/v0.5-tension)
from .plc_monitor_dialog import PLCMonitorDialog
__all__.append('PLCMonitorDialog')

# Connection dialog (NOVO - release/v0.5-tension)
from .connection_dialog import ConnectionDialog
__all__.append('ConnectionDialog')

# Tension Criteria dialog (NOVO - 2026-03-29)
from .tension_criteria_dialog import TensionCriteriaDialog
__all__.append('TensionCriteriaDialog')

# Tracking dialog (NOVO - 2026-03-29 - substitui aba Rastreabilidade)
from .tracking_dialog import TrackingDialog
__all__.append('TrackingDialog')

# Tensiometer calibration dialog
from .tensiometer_calibration_dialog import TensiometerCalibrationDialog
__all__.append('TensiometerCalibrationDialog')
