"""
consumo_lib.handlers
--------------------

Handlers são classes que gerenciam eventos de UI (teclado, menu, mouse),
callbacks de sistemas externos (GRBL), agregação de signals e roteamento de diálogos.

Este pacote contém:
- KeyboardEventHandler: Gerencia eventos de teclado para movimento CNC
- MenuHandler: Gerencia criação e organização de menus
- GRBLCallbackHandler: Gerencia callbacks complexos do GRBLStreamer
- DialogRouter: Centraliza abertura de diálogos da aplicação
"""

from .keyboard_handler import KeyboardEventHandler
from .menu_handler import MenuHandler
from .grbl_callback_handler import GRBLCallbackHandler
from .dialog_router import DialogRouter

__all__ = [
    'KeyboardEventHandler',
    'MenuHandler',
    'GRBLCallbackHandler',
    'DialogRouter',
]
