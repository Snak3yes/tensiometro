# -*- coding: utf-8 -*-
"""
handlers_factory.py
------------------
Factory para criar todos os handlers da aplicação.

Responsabilidade: Criar 3 handlers (Keyboard, Menu, DialogRouter).

Autor: Sistema AOI Tensiometro
Data: 2026-01-16 (SOLID Refactoring Phase 2)
"""

import logging
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QWidget

logger = logging.getLogger(__name__)


class HandlersFactory:
    """
    Factory para criar todos os handlers da aplicação.

    Responsabilidade:
    - Criar KeyboardEventHandler (captura eventos de teclado)
    - Criar MenuHandler (gerencia menu da aplicação)
    - Criar DialogRouter (rotas de diálogos)

    Methods:
    - create_all_handlers(): Cria todos os 3 handlers
    """

    def create_all_handlers(self, window: 'QWidget') -> Dict[str, Any]:
        """
        Cria todos os handlers da aplicação.

        Args:
            window: Instância da janela principal

        Returns:
            Dict com todos os handlers criados
        """
        from consumo_lib.handlers import (
            KeyboardEventHandler,
            MenuHandler,
            DialogRouter,
        )

        handlers = {}

        # 1. KeyboardEventHandler (será configurado após setup_ui)
        logger.info("Criando KeyboardEventHandler via HandlersFactory...")
        handlers['keyboard_handler'] = KeyboardEventHandler()
        logger.info(f"KeyboardEventHandler criado via HandlersFactory: {handlers['keyboard_handler']}")

        # 2. MenuHandler (será configurado em setup_menu)
        handlers['menu_handler'] = MenuHandler(main_window=window)
        logger.debug("MenuHandler criado via HandlersFactory")

        # 3. DialogRouter
        handlers['dialog_router'] = DialogRouter(window)
        logger.debug("DialogRouter criado via HandlersFactory")

        logger.info("Todos os 3 handlers criados via HandlersFactory")

        return handlers
