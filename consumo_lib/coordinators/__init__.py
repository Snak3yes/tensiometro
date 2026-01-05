"""
consumo_lib.coordinators
-----------------------

Coordinators são classes que orquestram interações entre
múltiplos managers e componentes, implementando padrões
como Coordinator, Mediator, e Observer.

Este pacote contém:
- ConnectionCoordinator: Gerencia estados de conexão de hardware
- InspectionCoordinator: Orquestra fluxo de inspeção visual
- TensionCoordinator: Gerencia medição de tensão
"""

from .connection_coordinator import ConnectionCoordinator, ConnectionState, require_connection
from .inspection_coordinator import InspectionCoordinator, InspectionStep, InspectionConfig, InspectionResult
from .tension_coordinator import TensionCoordinator, TensionStep, TensionConfig, TensionPoint, TensionResult

__all__ = [
    'ConnectionCoordinator',
    'ConnectionState',
    'require_connection',
    'InspectionCoordinator',
    'InspectionStep',
    'InspectionConfig',
    'InspectionResult',
    'TensionCoordinator',
    'TensionStep',
    'TensionConfig',
    'TensionPoint',
    'TensionResult',
]
