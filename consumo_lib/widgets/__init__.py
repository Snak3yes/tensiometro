"""
consumo_lib.widgets
-------------------

Widgets reutilizáveis da interface do Tensiometro.

Este módulo exporta todos os widgets para facilitar importação:
    from consumo_lib.widgets import CameraPreviewWidget, MovementControlWidget
"""

# Importa todos os widgets para exportação
from .camera_preview import CameraPreviewWidget
from .camera_capture import CameraCaptureWidget  # NOVO: Widget unificado de câmera
from .image_viewer import ImageViewerWidget
from .zoomable_image_view import ZoomableImageView
from .movement_control import MovementControlWidget
from .plc_monitor import PLCMonitorWidget
from .position_list import PositionListWidget
from .position_registry import PositionRegistryWidget
from .sequence_control import SequenceControlWidget
from .tension_viz import TensionVisualizationWidget, TensionCanvas
from .preview_suspender import _PreviewSuspender
from .operator_interface import (
    StencilSelector,
    ProgramSelector,
    InspectionResultsWidget
)
from .engenharia import (
    ConfirmSaveWidget
)

__all__ = [
    'CameraPreviewWidget',
    'CameraCaptureWidget',  # NOVO: Widget unificado de câmera
    'ImageViewerWidget',
    'ZoomableImageView',
    'MovementControlWidget',
    'PLCMonitorWidget',
    'PositionListWidget',
    'PositionRegistryWidget',
    'SequenceControlWidget',
    'TensionVisualizationWidget',
    'TensionCanvas',
    '_PreviewSuspender',
    'StencilSelector',
    'ProgramSelector',
    'InspectionResultsWidget',
    'ConfirmSaveWidget',
]
