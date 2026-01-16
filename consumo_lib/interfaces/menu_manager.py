"""
Interface Menu Manager - Gerenciamento de Menus

Define contrato para criação e gerenciamento de menus da aplicação.
"""

from abc import ABC, abstractmethod
from typing import Callable, Optional
from PyQt6.QtWidgets import QMainWindow, QMenu, QAction, QMenuBar


class IMenuManager(ABC):
    """
    Interface para gerenciamento de menus da aplicação.

    Responsabilidades:
    - Criar menus (File, Edit, View, etc.)
    - Adicionar ações aos menus
    - Conectar ações a callbacks
    - Gerenciar barra de menu
    """

    @abstractmethod
    def create_menu(self, menu_name: str) -> QMenu:
        """
        Cria um novo menu na barra de menu.

        Args:
            menu_name: Nome do menu (ex: "File", "Edit")

        Returns:
            Instância de QMenu criado
        """
        pass

    @abstractmethod
    def add_action(self,
                   menu: QMenu,
                   action_name: str,
                   callback: Callable,
                   shortcut: Optional[str] = None,
                   status_tip: Optional[str] = None) -> QAction:
        """
        Adiciona uma ação a um menu.

        Args:
            menu: Menu onde adicionar a ação
            action_name: Nome da ação
            callback: Função a ser chamada
            shortcut: Atalho de teclado (opcional)
            status_tip: Dica de status (opcional)

        Returns:
            QAction criada
        """
        pass

    @abstractmethod
    def add_separator(self, menu: QMenu) -> None:
        """
        Adiciona um separador ao menu.

        Args:
            menu: Menu onde adicionar separador
        """
        pass

    @abstractmethod
    def get_menu_bar(self) -> QMenuBar:
        """
        Retorna a barra de menu da janela.

        Returns:
            QMenuBar da janela principal
        """
        pass

    @abstractmethod
    def get_menu(self, menu_name: str) -> Optional[QMenu]:
        """
        Busca um menu pelo nome.

        Args:
            menu_name: Nome do menu

        Returns:
            QMenu ou None se não encontrado
        """
        pass
