"""
managers/stencil_manager.py
----------------------------
Gerencia rastreabilidade de stencils (StencilTracker).
"""
import logging
from PyQt6.QtCore import QObject, pyqtSignal
from aoi_lib.stencil_tracker import StencilTracker, Stencil, TensionRecord

logger = logging.getLogger(__name__)


class StencilManagerWrapper(QObject):
    """
    Gerencia rastreabilidade de stencils.

    Responsabilidades:
        - Gerenciar StencilTracker
        - Seleção de stencils
        - Salvamento de medições de tensão
        - Verificação de alertas de degradação
        - Consulta de histórico
        - Emitir signals de eventos
    """

    # Signals
    stencil_selected = pyqtSignal(object)  # Stencil
    stencil_cleared = pyqtSignal()
    tension_record_added = pyqtSignal(str, object)  # stencil_code, TensionRecord
    degradation_alert = pyqtSignal(str)  # alert_message
    stencil_error = pyqtSignal(str)  # error_message

    def __init__(self, parent=None):
        super().__init__(parent)
        self.stencil_tracker = StencilTracker()
        self.current_stencil = None

        logger.info(f"StencilTracker inicializado. Diretório: {self.stencil_tracker.data_dir}")

    def show_manager(self, parent_widget):
        """
        Abre o diálogo de gerenciamento de stencils.

        Args:
            parent_widget: Widget pai para o diálogo
        """
        from consumo_lib.dialogs.stencil import StencilManagerDialog

        dialog = StencilManagerDialog(self.stencil_tracker, parent_widget)
        dialog.exec()

    def create_new(self, parent_widget):
        """
        Abre o diálogo para criar um novo stencil.

        Args:
            parent_widget: Widget pai para o diálogo

        Returns:
            Stencil ou None se cancelado/erro
        """
        from consumo_lib.dialogs.stencil import StencilCreateDialog
        from PyQt6.QtWidgets import QDialog, QMessageBox

        dialog = StencilCreateDialog(self.stencil_tracker, parent=parent_widget)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            stencil = dialog.get_created_stencil()
            if stencil:
                logger.info(f"Stencil '{stencil.code}' criado com sucesso")
                return stencil
            else:
                error_msg = "Falha ao criar stencil"
                logger.error(error_msg)
                self.stencil_error.emit(error_msg)
        return None

    def get_stencil(self, code: str):
        """
        Obtém um stencil por código.

        Args:
            code: Código do stencil

        Returns:
            Stencil ou None se não encontrar
        """
        return self.stencil_tracker.get_stencil(code)

    def select_stencil(self, stencil: Stencil):
        """
        Define o stencil atualmente selecionado.

        Args:
            stencil: Stencil para selecionar
        """
        self.current_stencil = stencil
        self.stencil_selected.emit(stencil)
        logger.info(f"Stencil selecionado: {stencil.code}")

    def clear_selection(self):
        """Limpa a seleção de stencil."""
        self.current_stencil = None
        self.stencil_cleared.emit()
        logger.info("Seleção de stencil limpa")

    def get_current_stencil(self):
        """
        Retorna o stencil atualmente selecionado.

        Returns:
            Stencil ou None
        """
        return self.current_stencil

    def is_selected(self) -> bool:
        """
        Verifica se há um stencil selecionado.

        Returns:
            bool: True se há stencil selecionado
        """
        return self.current_stencil is not None

    def add_tension_record(self, stencil_code: str, record: TensionRecord, recipe_acceptance=None):
        """
        Adiciona um registro de tensão ao histórico do stencil.

        Args:
            stencil_code: Código do stencil
            record: TensionRecord para adicionar
            recipe_acceptance: Critérios de aceitação da receita (opcional)

        Returns:
            bool: True se adicionou com sucesso
        """
        try:
            # Salva no histórico
            self.stencil_tracker.add_tension_record(stencil_code, record)

            # Verifica alerta de degradação se houver critérios
            if recipe_acceptance:
                alert = self.stencil_tracker.check_degradation_alert(
                    stencil_code,
                    warning_low=recipe_acceptance.warning_low
                )
                if alert:
                    self.degradation_alert.emit(alert)

            # Emite signal
            self.tension_record_added.emit(stencil_code, record)

            logger.info(
                f"Medição de tensão salva no histórico do stencil "
                f"'{stencil_code}': {record.result}"
            )
            return True
        except Exception as e:
            error_msg = f"Erro ao salvar registro de tensão: {e}"
            logger.error(error_msg)
            self.stencil_error.emit(error_msg)
            return False

    def get_tension_history(self, stencil_code: str):
        """
        Obtém histórico de medições de tensão de um stencil.

        Args:
            stencil_code: Código do stencil

        Returns:
            Lista de TensionRecord ou None se erro
        """
        try:
            history = self.stencil_tracker.get_tension_history(stencil_code)
            return history
        except Exception as e:
            error_msg = f"Erro ao obter histórico de tensão: {e}"
            logger.error(error_msg)
            self.stencil_error.emit(error_msg)
            return None

    def list_stencils(self):
        """
        Lista todos os stencils cadastrados.

        Returns:
            Lista de Stencil
        """
        return self.stencil_tracker.list_stencils()

    def check_degradation_alert(self, stencil_code: str, warning_low: float = None):
        """
        Verifica se há alerta de degradação para um stencil.

        Args:
            stencil_code: Código do stencil
            warning_low: Limite inferior para warning (opcional)

        Returns:
            str: Mensagem de alerta ou None se não houver alerta
        """
        return self.stencil_tracker.check_degradation_alert(
            stencil_code,
            warning_low=warning_low
        )

    # =========================================================================
    # UI HANDLERS (Migrados do SignalAggregator)
    # =========================================================================

    def setup_ui_handlers(self, main_window):
        """
        Configura handlers de UI para signals de stencil.

        Este método conecta os signals internos do StencilManagerWrapper
        aos métodos que atualizam a UI do main_window.

        Args:
            main_window: Instância principal da janela

        Deve ser chamado durante a inicialização do main_window.
        """
        # Armazena referência ao main_window
        self.main_window = main_window

        # Conectar signals a handlers de UI
        self.stencil_selected.connect(self._on_stencil_selected_update_ui)
        self.stencil_cleared.connect(self._on_stencil_cleared_update_ui)
        self.tension_record_added.connect(self._on_tension_record_added_show_message)
        self.degradation_alert.connect(self._on_degradation_alert_show_message)
        self.stencil_error.connect(self._on_stencil_error_show_message)

        logger.debug("UI handlers conectados no StencilManagerWrapper")

    def _on_stencil_selected_update_ui(self, stencil):
        """
        Atualiza UI quando stencil é selecionado.

        Args:
            stencil: Stencil selecionado
        """
        self.main_window.current_stencil = stencil

        # Habilita botão de tensão
        if hasattr(self.main_window, 'btn_run_tension'):
            self.main_window.btn_run_tension.setEnabled(True)

        # Atualiza barra de status
        if hasattr(self.main_window, 'statusBar'):
            self.main_window.statusBar().showMessage(
                f"Stencil selecionado: {stencil.code} | "
                f"Receita: {stencil.recipe_name or 'Nenhuma'} | "
                f"Medições: {stencil.inspection_count}"
            )

        # Atualiza menu
        if hasattr(self.main_window, 'current_stencil_action'):
            self.main_window.current_stencil_action.setText(f"Stencil: {stencil.code}")

        logger.info(f"Stencil selecionado: {stencil.code}")

    def _on_stencil_cleared_update_ui(self):
        """Atualiza UI quando seleção de stencil é limpa."""
        self.main_window.current_stencil = None

        # Desabilita botão de tensão
        if hasattr(self.main_window, 'btn_run_tension'):
            self.main_window.btn_run_tension.setEnabled(False)

        # Atualiza statusBar
        if hasattr(self.main_window, 'statusBar'):
            self.main_window.statusBar().showMessage("Pronto")

        # Atualiza menu
        if hasattr(self.main_window, 'current_stencil_action'):
            self.main_window.current_stencil_action.setText("(Nenhum stencil selecionado)")

        logger.info("Seleção de stencil limpa")

    def _on_tension_record_added_show_message(self, stencil_code: str, record):
        """
        Mostra mensagem quando registro de tensão é adicionado.

        Args:
            stencil_code: Código do stencil
            record: TensionRecord adicionado
        """
        logger.info(
            f"Medição de tensão salva no histórico do stencil "
            f"'{stencil_code}': {record.result}"
        )

        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(
            self.main_window, "Medição Salva",
            f"Resultado da medição salvo no histórico.\n\n"
            f"Stencil: {stencil_code}\n"
            f"Resultado: {record.result}\n"
            f"Média: {record.average_tension:.2f} N/cm²"
        )

        # Atualiza widget de identificação para refletir nova medição
        stencil = self.get_stencil(stencil_code)
        if stencil and hasattr(self.main_window, 'stencil_identification'):
            self.main_window.stencil_identification._select_stencil(stencil)

    def _on_degradation_alert_show_message(self, alert: str):
        """
        Mostra alerta de degradação.

        Args:
            alert: Mensagem de alerta
        """
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.warning(
            self.main_window, "⚠️ Alerta de Degradação",
            f"Stencil: {self.main_window.current_stencil.code}\n\n{alert}"
        )

    def _on_stencil_error_show_message(self, error: str):
        """
        Mostra mensagem de erro de stencil.

        Args:
            error: Mensagem de erro
        """
        logger.error(f"Erro de stencil: {error}")

        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(
            self.main_window, "Erro de Stencil",
            f"Ocorreu um erro:\n{error}"
        )
