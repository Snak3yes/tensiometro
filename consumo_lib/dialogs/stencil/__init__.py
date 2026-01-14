"""
dialogs/stencil
---------------
Diálogos para gerenciamento de stencils.
"""

from .history_dialog import StencilHistoryDialog
from .edit_dialog import StencilEditDialog
from .create_dialog import StencilCreateDialog
from .manager_dialog import StencilManagerDialog
from .full_history_dialog import StencilFullHistoryDialog

__all__ = [
    'StencilHistoryDialog',
    'StencilEditDialog',
    'StencilCreateDialog',
    'StencilManagerDialog',
    'StencilFullHistoryDialog',
]
