"""
Interface Tab Manager - Gerenciamento de Abas

Define contrato para criação e gerenciamento de abas na aplicação.
"""

from abc import ABC, abstractmethod
from typing import Optional
from PyQt6.QtWidgets import QWidget, QTabWidget


class ITabManager(ABC):
    """
    Interface para gerenciamento de abas da aplicação.

    Responsabilidades:
    - Criar novas abas
    - Adicionar abas ao QTabWidget
    - Remover abas
    - Buscar abas por índice ou nome
    """

    @abstractmethod
    def create_tab(self, widget: QWidget, name: str, icon: Optional[str] = None) -> int:
        """
        Cria e adiciona uma nova aba.

        Args:
            widget: Widget a ser exibido na aba
            name: Nome da aba
            icon: Caminho para ícone (opcional)

        Returns:
            Índice da aba criada
        """
        pass

    @abstractmethod
    def remove_tab(self, index: int) -> None:
        """
        Remove uma aba pelo índice.

        Args:
            index: Índice da aba a ser removida
        """
        pass

    @abstractmethod
    def get_tab_widget(self) -> QTabWidget:
        """
        Retorna o QTabWidget gerenciado.

        Returns:
            Instância de QTabWidget
        """
        pass

    @abstractmethod
    def get_tab_count(self) -> int:
        """
        Retorna o número de abas.

        Returns:
            Número de abas
        """
        pass
