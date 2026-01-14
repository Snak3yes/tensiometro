
"""Tension measurement dialogs package."""

from .tension_measurement_dialog import TensionMeasurementDialog

# Export with alias for backward compatibility
StencilTensionDialog = TensionMeasurementDialog

__all__ = ['TensionMeasurementDialog', 'StencilTensionDialog']

