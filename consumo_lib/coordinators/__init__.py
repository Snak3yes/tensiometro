"""
consumo_lib.coordinators
-----------------------

Coordinators são classes que orquestram interações entre
múltiplos managers e componentes, implementando padrões
como Coordinator, Mediator, e Observer.

Este pacote contém:
- ConnectionCoordinator: Gerencia estados de conexão de hardware
- TensionCoordinator: Gerencia medição de tensão
- SetupCoordinator: Orquestra toda inicialização da aplicação
"""

from .connection_coordinator import ConnectionCoordinator, ConnectionState, require_connection
from .tension_coordinator import TensionCoordinator, TensionStep, TensionConfig, TensionPoint, TensionResult
from .setup_coordinator import SetupCoordinator

__all__ = [
    'ConnectionCoordinator',
    'ConnectionState',
    'require_connection',
    'TensionCoordinator',
    'TensionStep',
    'TensionConfig',
    'TensionPoint',
    'TensionResult',
    'SetupCoordinator',
]
