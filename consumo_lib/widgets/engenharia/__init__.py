"""
Engineering workflow widgets for consumo_lib.

This package contains widgets for the engineering/program creation workflow.
"""

from consumo_lib.widgets.engenharia.alignment_widget import AlignmentWidget
from consumo_lib.widgets.engenharia.inspection_windows_widget import (
    InspectionWindowsWidget
)
from consumo_lib.widgets.engenharia.confirm_save_widget import (
    ConfirmSaveWidget
)

__all__ = [
    "AlignmentWidget",
    "InspectionWindowsWidget",
    "ConfirmSaveWidget",
]
