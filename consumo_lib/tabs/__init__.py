"""
tabs package
"""

from .base_tab import BaseTab
from .cnc_control_tab import CNCControlTab
from .tension_tab import TensionTab
from .tracking_tab import TrackingTab
from .tree_view_tab import TreeViewTab  # NOVO - FASE 2

__all__ = [
    'BaseTab',
    'CNCControlTab',
    'TensionTab',
    'TrackingTab',
    'TreeViewTab'  # NOVO - FASE 2
]
