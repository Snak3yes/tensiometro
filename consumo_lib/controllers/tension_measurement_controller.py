"""
TensionMeasurementController - Controller para Medições de Tensão

Este controller gerencia o workflow completo de medição de tensão de stencils:
- Abre diálogo de medição de tensão
- Valida pré-condições (stencil selecionado, CNC conectada)
- Executa medição de tensão
- Salva resultados no histórico do stencil
- Notifica eventos via signals

Responsabilidade:
- Gerenciar workflow de medição de tensão
- Validar pré-condições antes da medição
- Salvar medições no histórico
- Notificar conclusão e erros via signals

Signals Emitidos:
- measurement_started() - Medições iniciadas
- measurement_completed(record) - Medição completada com sucesso
- measurement_failed(error) - Erro na medição
- measurement_saved(stencil_code, record) - Medição salva no histórico
"""

import json
import logging
import os
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QMessageBox, QDialog

from aoi_lib.stencil_tracker import Stencil, TensionRecord

logger = logging.getLogger("consumo_lib")


class TensionMeasurementController(QObject):
    """
    Controller para medições de tensão de stencils.

    Responsável por gerenciar todo o workflow de medição de tensão,
    incluindo validação de pré-condições, execução da medição
    e salvamento dos resultados.
    """

    # Signals
    measurement_started = pyqtSignal()
    measurement_completed = pyqtSignal(object)  # TensionRecord
    measurement_failed = pyqtSignal(str)  # error_message
    measurement_saved = pyqtSignal(str, object)  # stencil_code, TensionRecord

    def __init__(self, controller, config_manager, stencil_manager_wrapper, parent=None):
        """
        Inicializa o TensionMeasurementController.

        Args:
            controller: Instância de CNCAOIController
            config_manager: Instância de AOIConfigManager
            stencil_manager_wrapper: Wrapper para gerenciar stencils
            parent: Widget pai (geralmente main_window)
        """
        super().__init__(parent)
        self.controller = controller
        self.config = config_manager
        self.stencil_manager_wrapper = stencil_manager_wrapper
        self.parent_window = parent

        logger.debug("TensionMeasurementController inicializado")

    # =========================================================================
    # MÉTODOS PÚBLICOS
    # =========================================================================

    def run_measurement(self, current_stencil: Optional[Stencil], current_recipe=None):
        """
        Executa medição de tensão para o stencil selecionado.

        Valida pré-condições:
        - Stencil deve estar selecionado

        Exibe aviso se CNC não conectada, mas permite abrir o diálogo.

        Args:
            current_stencil: Stencil selecionado (ou None)
            current_recipe: Receita atual (opcional)

        Emits:
            measurement_started se medição iniciar
            measurement_failed se houver erro de validação
        """
        # Validar stencil selecionado
        if not current_stencil:
            error_msg = "Selecione um stencil antes de medir a tensão."
            QMessageBox.warning(
                self.parent_window,
                "Stencil Não Selecionado",
                error_msg
            )
            logger.warning("Tentativa de medição sem stencil selecionado")
            self.measurement_failed.emit(error_msg)
            return

        # Aviso se CNC não está conectada (mas não bloqueia)
        if not self.controller.cnc.is_connected:
            QMessageBox.warning(
                self.parent_window,
                "Aviso",
                "CNC não conectada. Algumas funcionalidades estarão limitadas.\n\n"
                "Conecte a CNC para realizar medições."
            )
            logger.warning("Diálogo de tensão aberto sem CNC conectada - funcionalidades limitadas")

        # Importar diálogo aqui para evitar import circular
        from consumo_lib.dialogs.tension import TensionMeasurementDialog

        # Abre diálogo de medição de tensão
        logger.info(f"Iniciando medição de tensão para stencil {current_stencil.code}")
        self.measurement_started.emit()

        dlg = TensionMeasurementDialog(self.parent_window, self.controller.cnc)

        # Se houver receita, pré-configura o diálogo
        if current_recipe and current_recipe.tension.enabled:
            # TODO: Passar parâmetros da receita para o diálogo
            logger.debug(f"Receita {current_recipe.name} tem tensão habilitada")
            pass

        result = dlg.exec()

        # Se medição foi concluída, salva no histórico
        if result == QDialog.DialogCode.Accepted:
            self.save_measurement(current_stencil, current_recipe, dlg)

    def save_measurement(self, current_stencil: Stencil, current_recipe, tension_dialog):
        """
        Salva resultado da medição de tensão no histórico do stencil.

        Args:
            current_stencil: Stencil selecionado
            current_recipe: Receita atual (opcional)
            tension_dialog: Diálogo de tensão com os dados da medição

        Emits:
            measurement_completed se salvamento bem-sucedido
            measurement_failed se erro no salvamento
            measurement_saved quando medição for salva
        """
        if not current_stencil:
            logger.error("Tentativa de salvar medição sem stencil selecionado")
            self.measurement_failed.emit("Stencil não selecionado")
            return

        try:
            # Tenta obter dados da medição do diálogo ou do último arquivo salvo
            measurements_file = "stencil_tension_measurements.json"

            if not os.path.exists(measurements_file):
                logger.warning("Arquivo de medições não encontrado")
                self.measurement_failed.emit("Arquivo de medições não encontrado")
                return

            # Lê arquivo de medições
            with open(measurements_file, "r", encoding="utf-8") as f:
                tension_data = json.load(f)

            # Cria registro de tensão
            record = TensionRecord.from_tension_data(
                tension_data,
                recipe_name=current_recipe.name if current_recipe else None,
                operator=None  # TODO: Implementar campo de operador
            )

            # Salva no histórico usando o wrapper
            recipe_acceptance = None
            if current_recipe and current_recipe.tension.acceptance:
                recipe_acceptance = current_recipe.tension.acceptance

            self.stencil_manager_wrapper.add_tension_record(
                current_stencil.code,
                record,
                recipe_acceptance=recipe_acceptance
            )

            logger.info(f"Medição de tensão salva para stencil {current_stencil.code}")

            # Emit signals
            self.measurement_completed.emit(record)
            self.measurement_saved.emit(current_stencil.code, record)

            # O resto é tratado pelos handlers conectados aos signals
            # (_on_tension_record_added, _on_degradation_alert)

        except Exception as e:
            error_msg = f"Erro ao salvar medição no histórico: {e}"
            logger.exception("Erro ao salvar medição de tensão")
            QMessageBox.warning(
                self.parent_window,
                "Erro",
                f"Erro ao salvar no histórico:\n{str(e)}"
            )
            self.measurement_failed.emit(error_msg)

    def open_simple_dialog(self):
        """
        Abre diálogo simples de medição de tensão (sem salvar no histórico).

        Exibe aviso se CNC não conectada, mas permite abrir o diálogo
        para configurações e visualização.
        """
        # Aviso se CNC não está conectada (mas não bloqueia)
        if not self.controller.cnc.is_connected:
            QMessageBox.warning(
                self.parent_window,
                "Aviso",
                "CNC não conectada. Algumas funcionalidades estarão limitadas.\n\n"
                "Conecte a CNC para realizar medições."
            )
            logger.warning("Diálogo de tensão aberto sem CNC conectada - funcionalidades limitadas")

        # Importar diálogo aqui para evitar import circular
        from consumo_lib.dialogs.tension import TensionMeasurementDialog

        dlg = TensionMeasurementDialog(self.parent_window, self.controller.cnc)
        dlg.exec()

    def setup_ui_handlers(self):
        """
        Configura handlers de UI para signals de medição de tensão.

        Este método conecta os signals do tension_measurement_dialog
        aos métodos que atualizam a UI do main_window.

        Deve ser chamado durante a inicialização do main_window.
        """
        # Nota: A conexão aos signals do diálogo é feita internamente no diálogo
        # Este método é um placeholder para futuras expansões
        logger.debug("UI handlers configurados no TensionMeasurementController")

    def on_tension_record_added_update_ui(self, stencil_code: str, record):
        """
        Atualiza UI quando registro de tensão é adicionado.

        Args:
            stencil_code: Código do stencil
            record: Registro de tensão adicionado
        """
        logger.info(
            f"Medição de tensão salva no histórico do stencil "
            f"'{stencil_code}': {record.result}"
        )

        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(
            self.parent_window, "Medição Salva",
            f"Resultado da medição salvo no histórico.\n\n"
            f"Stencil: {stencil_code}\n"
            f"Resultado: {record.result}\n"
            f"Média: {record.average_tension:.2f} N/cm²"
        )

        # Atualiza widget de identificação para refletir nova inspeção
        if hasattr(self.parent_window, 'stencil_manager_wrapper'):
            stencil = self.parent_window.stencil_manager_wrapper.get_stencil(stencil_code)
            if stencil and hasattr(self.parent_window, 'stencil_identification'):
                self.parent_window.stencil_identification._select_stencil(stencil)

    def on_degradation_alert_show_message(self, alert: str):
        """
        Mostra alerta de degradação.

        Args:
            alert: Mensagem de alerta
        """
        from PyQt6.QtWidgets import QMessageBox
        current_stencil = getattr(self.parent_window, 'current_stencil', None)
        stencil_info = f"Stencil: {current_stencil.code}\n\n" if current_stencil else ""

        QMessageBox.warning(
            self.parent_window, "⚠️ Alerta de Degradação",
            f"{stencil_info}{alert}"
        )

    def on_tension_step_changed_update_status(self, step, message: str):
        """
        Atualiza statusBar quando etapa da medição muda.

        Args:
            step: Etapa atual
            message: Mensagem de status
        """
        logger.info(f"Tension measurement step: {step.value if hasattr(step, 'value') else step} - {message}")
        self.parent_window.statusBar().showMessage(message)

    def on_tension_progress_update_status(self, current: int, total: int, message: str):
        """
        Atualiza statusBar com progresso da medição.

        Args:
            current: Ponto atual
            total: Total de pontos
            message: Mensagem de status
        """
        logger.debug(f"Tension progress: {current}/{total} - {message}")
        self.parent_window.statusBar().showMessage(f"{message} ({current}/{total} pontos)")

    def on_tension_measurement_completed_update_status(self, result):
        """
        Atualiza statusBar quando medição completa.

        Args:
            result: Resultado da medição
        """
        if result.success:
            classification = result.classification or "unknown"
            avg = result.average_tension or 0
            logger.info(f"Medição completada: {classification} (média: {avg:.2f} N/cm)")
            self.parent_window.statusBar().showMessage(
                f"Medição completada: {classification.upper()} (média: {avg:.2f} N/cm)",
                10000
            )
        else:
            logger.error(f"Medição falhou: {result.error or 'erro desconhecido'}")
            self.parent_window.statusBar().showMessage(
                f"Medição falhou: {result.error or 'erro desconhecido'}",
                10000
            )

    def on_tension_heatmap_generated_update_status(self, heatmap_path: str):
        """
        Atualiza statusBar quando heatmap é gerado.

        Args:
            heatmap_path: Caminho do heatmap gerado
        """
        logger.info(f"Heatmap gerado: {heatmap_path}")
        self.parent_window.statusBar().showMessage("Heatmap gerado", 3000)
