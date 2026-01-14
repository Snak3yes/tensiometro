"""
Módulo: consumo_lib.utils.main_window

Componentes modulares da MainWindow (AOIControllerApp).

Este paceto contém 5 componentes que extraem lógica da MainWindow,
tornando-a um orchestrator puro (~300 linhas em vez de 1,385).

Componentes:
- app_state: Gerenciamento de estado da aplicação
- initializer: Configuração inicial (UI, menu, auto-connect)
- event_handlers: Handlers de eventos (login, inspeção, sequência, etc.)
- engineering_workflow: Workflow de engenharia (Engineering Wizard)
- inspection_workflow: Workflow de inspeção (posicionamento, modo, execução)

Author: Refactoring (2026-01-14)
"""

from .app_state import MainWindowState
from .initializer import MainWindowInitializer
from .event_handlers import MainWindowEventHandlers
from .engineering_workflow import MainWindowEngineeringWorkflow
from .inspection_workflow import MainWindowInspectionWorkflow

__all__ = [
    'MainWindowState',
    'MainWindowInitializer',
    'MainWindowEventHandlers',
    'MainWindowEngineeringWorkflow',
    'MainWindowInspectionWorkflow',
]
