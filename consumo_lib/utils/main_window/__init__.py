"""
Módulo: consumo_lib.utils.main_window

Componentes modulares da MainWindow (AOIControllerApp).

Este paceto contém 5 componentes que extraem lógica da MainWindow,
tornando-a um orchestrator puro (~300 linhas em vez de 1,385).

Componentes:
- app_state: Gerenciamento de estado da aplicação
- initializer: Configuração inicial (UI, menu, auto-connect)
- event_handlers: Handlers de eventos (login, sequência, etc.)

Author: Refactoring (2026-01-14)
"""

from .app_state import MainWindowState
from .initializer import MainWindowInitializer
from .event_handlers import MainWindowEventHandlers

__all__ = [
    'MainWindowState',
    'MainWindowInitializer',
    'MainWindowEventHandlers',
]
