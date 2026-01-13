"""
Engineering workflow widgets for consumo_lib.

This package contains widgets for the engineering/program creation workflow.
"""

from consumo_lib.widgets.engenharia.program_data_widget import ProgramDataWidget
from consumo_lib.widgets.engenharia.gerber_upload_widget import GerberUploadWidget
from consumo_lib.widgets.engenharia.fiducial_capture_widget import FiducialCaptureWidget
from consumo_lib.widgets.engenharia.mosaic_capture_widget import MosaicCaptureWidget
from consumo_lib.widgets.engenharia.alignment_widget import AlignmentWidget
from consumo_lib.widgets.engenharia.inspection_windows_widget import (
    InspectionWindowsWidget
)
from consumo_lib.widgets.engenharia.confirm_save_widget import (
    ConfirmSaveWidget
)

__all__ = [
    # Aba 1
    "ProgramDataWidget",
    # Aba 2
    "GerberUploadWidget",
    # Aba 3
    "FiducialCaptureWidget",
    # Aba 4
    "MosaicCaptureWidget",
    # Aba 5
    "AlignmentWidget",
    # Aba 6
    "InspectionWindowsWidget",
    # Aba 7
    "ConfirmSaveWidget",
]
