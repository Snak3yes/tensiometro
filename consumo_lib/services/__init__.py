"""
consumo_lib.services
--------------------

Services são classes que contêm lógica de negócio sem dependência de PyQt.

Este pacote contém:
- MovementService: Orquestra movimentos CNC
- ClickToMoveService: Converte cliques em coordenadas CNC
- SequenceExecutionService: Gerencia execução de sequências de inspeção
- ResourceManager: Gerencia limpeza e ciclo de vida de recursos
"""

from .movement_service import MovementService, MovementResult
from .click_to_move_service import ClickToMoveService, ClickMoveResult
from .sequence_execution_service import SequenceExecutionService
from .resource_manager import ResourceManager

__all__ = [
    'MovementService',
    'MovementResult',
    'ClickToMoveService',
    'ClickMoveResult',
    'SequenceExecutionService',
    'ResourceManager',
]
