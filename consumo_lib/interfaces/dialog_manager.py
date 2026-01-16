"""
Interface Dialog Manager - Gerenciamento de Diálogos

Define contrato para exibição e gerenciamento de diálogos da aplicação.
"""

from abc import ABC, abstractmethod
from typing import Optional, Any


class IDialogManager(ABC):
    """
    Interface para gerenciamento de diálogos da aplicação.

    Responsabilidades:
    - Exibir diálogos modais e não-modais
    - Gerenciar diálogos de configuração
    - Gerenciar wizards
    - Gerenciar diálogos de autenticação
    """

    @abstractmethod
    def show_dialog(self, dialog_class: type, *args, **kwargs) -> Optional[Any]:
        """
        Exibe um diálogo modal.

        Args:
            dialog_class: Classe do diálogo
            *args: Argumentos posicionais para o diálogo
            **kwargs: Argumentos nomeados para o diálogo

        Returns:
            Resultado do diálogo ou None
        """
        pass

    @abstractmethod
    def show_stencil_manager(self) -> None:
        """Exibe o gerenciador de stencils."""
        pass

    @abstractmethod
    def show_recipe_manager(self) -> None:
        """Exibe o gerenciador de receitas."""
        pass

    @abstractmethod
    def show_inspection_settings(self) -> None:
        """Exibe as configurações de inspeção."""
        pass

    @abstractmethod
    def show_fov_calibration(self) -> None:
        """Exibe o diálogo de calibração FOV."""
        pass

    @abstractmethod
    def show_login_dialog(self) -> bool:
        """
        Exibe o diálogo de login.

        Returns:
            True se login bem-sucedido, False caso contrário
        """
        pass

    @abstractmethod
    def show_engineering_wizard(self) -> None:
        """Exibe o wizard de engenharia."""
        pass

    @abstractmethod
    def show_about_dialog(self) -> None:
        """Exibe o diálogo 'Sobre'."""
        pass
