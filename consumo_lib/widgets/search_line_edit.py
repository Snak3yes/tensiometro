"""
Widget de Busca Incremental com Debounce

Campo de busca que dispara sinal após período de inatividade.
"""

import logging
from PyQt6.QtWidgets import QLineEdit
from PyQt6.QtCore import QTimer, pyqtSignal

logger = logging.getLogger(__name__)


class SearchLineEdit(QLineEdit):
    """
    Campo de busca com debounce automático

    Sinais:
        searchPerformed: Emitido quando busca deve ser executada (após debounce)

    Atributos:
        debounce_time_ms: Tempo de debounce em milissegundos (padrão: 300ms)
    """

    searchPerformed = pyqtSignal(str)  # Emitido após debounce com termo de busca

    def __init__(self, parent=None):
        """
        Inicializa campo de busca

        Args:
            parent: Widget pai
        """
        super().__init__(parent)
        self.debounce_time_ms = 300

        # Configura aparência
        self.setPlaceholderText("Buscar programas...")
        self.setMinimumWidth(300)

        # Timer para debounce
        self.debounce_timer = QTimer()
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(self._perform_search)

        # Conecta mudança de texto ao timer
        self.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self, text: str):
        """
        Handler: Texto mudou

        Reinicia timer debounce quando texto muda.

        Args:
            text: Novo texto
        """
        self.debounce_timer.stop()

        # Só dispara busca se tiver pelo menos 2 caracteres
        # ou se estiver limpando a busca
        if len(text) >= 2 or len(text) == 0:
            self.debounce_timer.start(self.debounce_time_ms)

    def _perform_search(self):
        """Emite sinal de busca com termo atual"""
        search_term = self.text().strip()
        self.searchPerformed.emit(search_term)

    def clear_search(self):
        """
        Limpa busca e dispara sinal com string vazia

        Útil para botão "Limpar Filtros"
        """
        self.clear()
        self.searchPerformed.emit("")

    def set_debounce_time(self, milliseconds: int):
        """
        Define tempo de debounce

        Args:
            milliseconds: Tempo em milissegundos
        """
        self.debounce_time_ms = milliseconds
