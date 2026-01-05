"""
consumo_lib.handlers
--------------------

Handlers são classes que gerenciam eventos de UI (teclado, menu, mouse).

Este pacote contém:
- KeyboardEventHandler: Gerencia eventos de teclado para movimento CNC
- MenuHandler: Gerencia criação e organização de menus
"""

from .keyboard_handler import KeyboardEventHandler
from .menu_handler import MenuHandler

__all__ = [
    'KeyboardEventHandler',
    'MenuHandler',
]
