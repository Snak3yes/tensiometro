"""
dialogs package
"""
from .fov_calibration import FOVCalibrationDialog
from .crosshair_settings import CrosshairSettingsDialog
from .inspection_settings import InspectionSettingsDialog
from .report_settings import ReportSettingsDialog
from .about import AboutDialog

__all__ = [
    'FOVCalibrationDialog',
    'CrosshairSettingsDialog',
    'InspectionSettingsDialog',
    'ReportSettingsDialog',
    'AboutDialog'
]

# TODO: Mover diálogos restantes em fases futuras:
# - CameraSettingsDialog (precisa verificar se existe)
# - CalibrationTestDialog (precisa verificar se existe)
# - FiducialAlignmentDialog (FiducialAlignmentWidget - 959 linhas, muito grande)
# - MapDefinitionDialog (show_definir_mapa_dialog - ~500 linhas, muito grande)
