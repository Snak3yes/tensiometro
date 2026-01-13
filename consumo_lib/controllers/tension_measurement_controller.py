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
        - CNC deve estar conectada

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

        # Validar conexão CNC
        if not self.controller.cnc.is_connected:
            error_msg = "Conecte o CLP antes de medir a tensão."
            QMessageBox.warning(
                self.parent_window,
                "CLP Não Conectado",
                error_msg
            )
            logger.warning("Tentativa de medição sem CNC conectada")
            self.measurement_failed.emit(error_msg)
            return

        # Importar diálogo aqui para evitar import circular
        from consumo_lib.dialogs.tension_measurement_dialog import StencilTensionDialog

        # Abre diálogo de medição de tensão
        logger.info(f"Iniciando medição de tensão para stencil {current_stencil.code}")
        self.measurement_started.emit()

        dlg = StencilTensionDialog(self.parent_window, self.controller.cnc)

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

        Este método apenas abre o diálogo para medição manual,
        sem associar a um stencil específico.
        """
        # Validar conexão CNC
        if not self.controller.cnc.is_connected:
            QMessageBox.warning(
                self.parent_window,
                "Aviso",
                "Conecte a CNC antes de medir a tensão do stencil."
            )
            return

        # Importar diálogo aqui para evitar import circular
        from consumo_lib.dialogs.tension_measurement_dialog import StencilTensionDialog

        dlg = StencilTensionDialog(self.parent_window, self.controller.cnc)
        dlg.exec()
