"""
tabs package
"""

from .base_tab import BaseTab
from .cnc_control_tab import CNCControlTab
from .tension_tab import TensionTab
from .tension_measurement_tab import TensionMeasurementTab  # NOVO - Unificado v0.5
from .tracking_tab import TrackingTab
from .tree_view_tab import TreeViewTab  # NOVO - FASE 2

__all__ = [
    'BaseTab',
    'CNCControlTab',
    'TensionTab',
    'TensionMeasurementTab',  # NOVO - Unificado v0.5
    'TrackingTab',
    'TreeViewTab'  # NOVO - FASE 2
]
