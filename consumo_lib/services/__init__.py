"""
consumo_lib.services
--------------------

Services são classes que contêm lógica de negócio sem dependência de PyQt.

Este pacote contém:
- MovementService: Orquestra movimentos CNC
- ClickToMoveService: Converte cliques em coordenadas CNC
"""

from .movement_service import MovementService, MovementResult
from .click_to_move_service import ClickToMoveService, ClickMoveResult

__all__ = [
    'MovementService',
    'MovementResult',
    'ClickToMoveService',
    'ClickMoveResult',
]
