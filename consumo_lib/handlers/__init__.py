"""
consumo_lib.handlers
--------------------

Handlers são classes que gerenciam eventos de UI (teclado, menu, mouse)
e roteamento de diálogos.

Este pacote contém:
- KeyboardEventHandler: Gerencia eventos de teclado para movimento CNC
- MenuHandler: Gerencia criação e organização de menus
- DialogRouter: Centraliza abertura de diálogos da aplicação
"""

from .keyboard_handler import KeyboardEventHandler
from .menu_handler import MenuHandler
from .dialog_router import DialogRouter

__all__ = [
    'KeyboardEventHandler',
    'MenuHandler',
    'DialogRouter',
]
