"""
tabs/base_tab.py
----------------
Classe base para todas as abas da aplicação.
"""

from __future__ import annotations

import logging
from typing import Optional

from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import pyqtSignal, QObject

logger = logging.getLogger(__name__)


class BaseTab(QWidget):
    """
    Classe base para todas as abas da aplicação.

    Fornece interface comum e métodos utilitários para todas as abas.
    Cada aba específica deve herdar desta classe e implementar
    o método build_ui().
    """

    # Sinais comuns que todas as abas podem emitir
    status_changed = pyqtSignal(str)  # Mensagem de status para a barra de status
    error_occurred = pyqtSignal(str)  # Mensagem de erro
    action_requested = pyqtSignal(str, dict)  # Solicita ação ao MainWindow

    def __init__(self, parent=None):
        """
        Inicializa a aba.

        Args:
            parent: Widget pai (geralmente a MainWindow)
        """
        super().__init__(parent)
        self.main_window = parent  # Referência à MainWindow
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Layout principal
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)

        # Constrói a UI específica da aba
        self.build_ui()

    def build_ui(self):
        """
        Constrói a interface da aba.

        Este método DEVE ser sobrescrito pelas classes filhas.
        """
        raise NotImplementedError(f"{self.__class__.__name__} deve implementar build_ui()")

    def on_tab_activated(self):
        """
        Chamado quando a aba é ativada (selecionada).

        Pode ser sobrescrito para realizar ações específicas
        quando a aba ganha foco.
        """
        pass

    def on_tab_deactivated(self):
        """
        Chamado quando a aba é desativada (outra aba é selecionada).

        Pode ser sobrescrito para realizar ações de limpeza
        ou salvar estado.
        """
        pass

    def refresh(self):
        """
        Atualiza o conteúdo da aba.

        Pode ser sobrescrito para recarregar dados ou atualizar visualização.
        """
        pass

    def get_config(self, *keys, default=None):
        """
        Obtém configuração do ConfigManager da MainWindow.

        Args:
            *keys: Chaves de configuração (ex: "connections", "plc_host")
            default: Valor padrão se não encontrado

        Returns:
            Valor da configuração ou default
        """
        if self.main_window and hasattr(self.main_window, 'config'):
            return self.main_window.config.get(*keys, default=default)
        return default

    def set_config(self, *keys, value):
        """
        Define configuração no ConfigManager da MainWindow.

        Args:
            *keys: Chaves de configuração
            value: Valor a definir
        """
        if self.main_window and hasattr(self.main_window, 'config'):
            self.main_window.config.set(*keys, value=value)
            self.main_window.config.save()

    def show_status(self, message: str, timeout: int = 3000):
        """
        Exibe mensagem na barra de status da MainWindow.

        Args:
            message: Mensagem a exibir
            timeout: Tempo em ms (0 = permanente)
        """
        if self.main_window and hasattr(self.main_window, 'statusBar'):
            self.main_window.statusBar().showMessage(message, timeout)
        self.status_changed.emit(message)

    def show_error(self, message: str):
        """
        Exibe mensagem de erro.

        Args:
            message: Mensagem de erro
        """
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(self, "Erro", message)
        self.error_occurred.emit(message)

    def get_controller(self):
        """
        Obtém referência ao controller da MainWindow.

        Returns:
            AOIController ou None
        """
        if self.main_window and hasattr(self.main_window, 'controller'):
            return self.main_window.controller
        return None
