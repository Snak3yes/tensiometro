"""
Signal Aggregator

Este módulo contém o agregador de signals que centraliza TODOS os handlers
de events do main_window, removendo a necessidade de 93 métodos _on_*
espalhados pelo código.

Autor: Refatoração Session 20
Data: 2026-01-05
"""

import logging
import os
from typing import Optional

logger = logging.getLogger("consumo_lib")


class SignalAggregator:
    """
    Centraliza TODOS os handlers de signals do main_window.

    Responsabilidade:
    - Conectar signals de TODOS os controllers/coordinators/managers
    - Implementar handlers que atualizam UI e estado do main_window
    - Eliminar a necessidade de 93 métodos _on_* no main_window

    Atributos Gerenciados (do main_window):
    - current_recipe: Receita atualmente carregada
    - current_stencil: Stencil atualmente selecionado
    - current_sequence: Sequência atual
    - _last_inspection_result: Último resultado de inspeção
    - _last_inspection_overlay: Última overlay de inspeção
    - inspection_thresholds: Thresholds de inspeção
    - report_config: Configuração de relatório

    Nota: Este handler acessa e modifica atributos do main_window diretamente
    para manter compatibilidade com o código existente.
    """

    def __init__(self, main_window):
        """
        Inicializa o agregador de signals.

        Args:
            main_window: Referência para AOIControllerApp (usada para acessar
                        controllers, widgets e estado interno)
        """
        self.main_window = main_window
        self._setup_all_connections()

    def _setup_all_connections(self):
        """Conecta TODOS os signals de controllers/coordinators/managers."""

        # =========================================================================
        # RECIPE MANAGER SIGNALS
        # =========================================================================
        if self.main_window.recipe_manager_wrapper:
            self.main_window.recipe_manager_wrapper.recipe_loaded.connect(
                self._on_recipe_loaded
            )
            self.main_window.recipe_manager_wrapper.recipe_created.connect(
                self._on_recipe_created
            )
            self.main_window.recipe_manager_wrapper.recipe_applied_to_capture.connect(
                self._on_recipe_applied_to_capture
            )
            self.main_window.recipe_manager_wrapper.recipe_applied_to_tension.connect(
                self._on_recipe_applied_to_tension
            )
            self.main_window.recipe_manager_wrapper.recipe_error.connect(
                self._on_recipe_error
            )

        if self.main_window.recipe_manager_controller:
            self.main_window.recipe_manager_controller.recipe_loaded.connect(
                self._on_recipe_loaded_from_controller
            )
            self.main_window.recipe_manager_controller.recipe_created.connect(
                self._on_recipe_created_from_controller
            )
            self.main_window.recipe_manager_controller.recipe_applied_to_capture.connect(
                self._on_recipe_applied_to_capture_from_controller
            )
            self.main_window.recipe_manager_controller.recipe_applied_to_tension.connect(
                self._on_recipe_applied_to_tension_from_controller
            )
            self.main_window.recipe_manager_controller.recipe_error.connect(
                self._on_recipe_error_from_controller
            )

        # =========================================================================
        # STENCIL MANAGER SIGNALS
        # =========================================================================
        if self.main_window.stencil_manager_wrapper:
            self.main_window.stencil_manager_wrapper.stencil_selected.connect(
                self._on_stencil_selected
            )
            self.main_window.stencil_manager_wrapper.stencil_cleared.connect(
                self._on_stencil_cleared
            )
            self.main_window.stencil_manager_wrapper.tension_record_added.connect(
                self._on_tension_record_added
            )
            self.main_window.stencil_manager_wrapper.degradation_alert.connect(
                self._on_degradation_alert
            )
            self.main_window.stencil_manager_wrapper.stencil_error.connect(
                self._on_stencil_error
            )

        # =========================================================================
        # INSPECTION MANAGER SIGNALS
        # =========================================================================
        if self.main_window.inspection_manager:
            self.main_window.inspection_manager.inspection_completed.connect(
                self._on_inspection_completed
            )
            self.main_window.inspection_manager.inspection_failed.connect(
                self._on_inspection_failed
            )
            self.main_window.inspection_manager.thresholds_changed.connect(
                self._on_thresholds_changed
            )

        # =========================================================================
        # INSPECTION COORDINATOR SIGNALS
        # =========================================================================
        if self.main_window.inspection_coordinator:
            self.main_window.inspection_coordinator.step_changed.connect(
                self._on_inspection_step_changed
            )
            self.main_window.inspection_coordinator.progress_updated.connect(
                self._on_inspection_progress
            )
            self.main_window.inspection_coordinator.gerber_loaded.connect(
                self._on_gerber_loaded
            )
            self.main_window.inspection_coordinator.fiducials_captured.connect(
                self._on_fiducials_captured
            )
            self.main_window.inspection_coordinator.alignment_completed.connect(
                self._on_alignment_completed
            )
            self.main_window.inspection_coordinator.image_captured.connect(
                self._on_inspection_image_captured
            )
            self.main_window.inspection_coordinator.analysis_completed.connect(
                self._on_inspection_analysis_completed
            )
            self.main_window.inspection_coordinator.inspection_completed.connect(
                self._on_inspection_workflow_completed
            )
            self.main_window.inspection_coordinator.inspection_failed.connect(
                self._on_inspection_workflow_failed
            )

        # =========================================================================
        # INSPECTION UI CONTROLLER SIGNALS
        # =========================================================================
        if self.main_window.inspection_ui_controller:
            self.main_window.inspection_ui_controller.inspection_requested.connect(
                self._on_inspection_requested
            )
            self.main_window.inspection_ui_controller.inspection_completed.connect(
                self._on_inspection_completed_from_controller
            )
            self.main_window.inspection_ui_controller.inspection_failed.connect(
                self._on_inspection_failed
            )
            self.main_window.inspection_ui_controller.settings_updated.connect(
                self._on_inspection_settings_updated
            )

        # =========================================================================
        # TENSION COORDINATOR SIGNALS
        # =========================================================================
        if self.main_window.tension_coordinator:
            self.main_window.tension_coordinator.step_changed.connect(
                self._on_tension_step_changed
            )
            self.main_window.tension_coordinator.progress_updated.connect(
                self._on_tension_progress
            )
            self.main_window.tension_coordinator.grid_generated.connect(
                self._on_tension_grid_generated
            )
            self.main_window.tension_coordinator.point_started.connect(
                self._on_tension_point_started
            )
            self.main_window.tension_coordinator.point_completed.connect(
                self._on_tension_point_completed
            )
            self.main_window.tension_coordinator.measurement_taken.connect(
                self._on_tension_measurement_taken
            )
            self.main_window.tension_coordinator.all_measurements_completed.connect(
                self._on_tension_all_completed
            )
            self.main_window.tension_coordinator.heatmap_generated.connect(
                self._on_tension_heatmap_generated
            )
            self.main_window.tension_coordinator.measurement_completed.connect(
                self._on_tension_measurement_completed
            )
            self.main_window.tension_coordinator.measurement_failed.connect(
                self._on_tension_measurement_failed
            )

        # =========================================================================
        # REPORT MANAGER SIGNALS
        # =========================================================================
        if self.main_window.report_manager_wrapper:
            self.main_window.report_manager_wrapper.report_generated.connect(
                self._on_report_generated
            )
            self.main_window.report_manager_wrapper.report_failed.connect(
                self._on_report_failed
            )
            self.main_window.report_manager_wrapper.config_changed.connect(
                self._on_report_config_changed
            )

        # =========================================================================
        # REPORT DIALOG CONTROLLER SIGNALS
        # =========================================================================
        if self.main_window.report_dialog_controller:
            self.main_window.report_dialog_controller.tension_report_generated.connect(
                self._on_tension_report_generated
            )
            self.main_window.report_dialog_controller.stencil_report_generated.connect(
                self._on_stencil_report_generated
            )
            self.main_window.report_dialog_controller.period_query_executed.connect(
                self._on_period_query_executed
            )
            self.main_window.report_dialog_controller.report_error.connect(
                self._on_report_error
            )

        # =========================================================================
        # SEQUENCE CONTROLLER SIGNALS
        # =========================================================================
        if self.main_window.sequence_controller:
            self.main_window.sequence_controller.sequence_created.connect(
                self._on_sequence_created
            )
            self.main_window.sequence_controller.sequence_loaded.connect(
                self._on_sequence_loaded
            )
            self.main_window.sequence_controller.sequence_saved.connect(
                self._on_sequence_saved
            )
            self.main_window.sequence_controller.sequence_execution_started.connect(
                self._on_sequence_execution_started
            )
            self.main_window.sequence_controller.sequence_execution_stopped.connect(
                self._on_sequence_execution_stopped
            )
            self.main_window.sequence_controller.sequence_execution_finished.connect(
                self._on_sequence_execution_finished
            )
            self.main_window.sequence_controller.sequence_error.connect(
                self._on_sequence_error_from_controller
            )
            self.main_window.sequence_controller.position_captured.connect(
                self._on_position_captured
            )

        # =========================================================================
        # MAP CONTROLLER SIGNALS
        # =========================================================================
        if self.main_window.map_controller:
            self.main_window.map_controller.program_saved.connect(
                self._on_map_program_saved
            )
            self.main_window.map_controller.program_loaded.connect(
                self._on_map_program_loaded
            )
            self.main_window.map_controller.program_deleted.connect(
                self._on_map_program_deleted
            )
            self.main_window.map_controller.map_generated.connect(
                self._on_map_generated
            )
            self.main_window.map_controller.map_progress.connect(
                self._on_map_progress
            )
            self.main_window.map_controller.map_error.connect(
                self._on_map_error
            )

        # =========================================================================
        # CAMERA SETTINGS CONTROLLER SIGNALS
        # =========================================================================
        if self.main_window.camera_settings_controller:
            self.main_window.camera_settings_controller.settings_changed.connect(
                self._on_camera_settings_changed
            )
            self.main_window.camera_settings_controller.settings_applied.connect(
                self._on_camera_settings_applied
            )
            self.main_window.camera_settings_controller.settings_saved.connect(
                self._on_camera_settings_saved
            )
            self.main_window.camera_settings_controller.settings_loaded.connect(
                self._on_camera_settings_loaded
            )

        # =========================================================================
        # CALIBRATION CONTROLLER SIGNALS
        # =========================================================================
        if self.main_window.calibration_controller:
            self.main_window.calibration_controller.calibration_applied.connect(
                self._on_calibration_applied
            )
            self.main_window.calibration_controller.calibration_completed.connect(
                self._on_calibration_completed
            )
            self.main_window.calibration_controller.test_completed.connect(
                self._on_calibration_test_completed
            )

        # =========================================================================
        # FIDUCIAL ALIGNMENT CONTROLLER SIGNALS
        # =========================================================================
        if self.main_window.fiducial_alignment_controller:
            self.main_window.fiducial_alignment_controller.alignment_completed.connect(
                self._on_fiducial_alignment_completed
            )
            self.main_window.fiducial_alignment_controller.alignment_cancelled.connect(
                self._on_fiducial_alignment_cancelled
            )
            self.main_window.fiducial_alignment_controller.alignment_error.connect(
                self._on_fiducial_alignment_error
            )

        # =========================================================================
        # CONNECTION MANAGER CONTROLLER SIGNALS
        # =========================================================================
        if self.main_window.connection_manager_controller:
            self.main_window.connection_manager_controller.camera_connected.connect(
                self._on_camera_connected_from_controller
            )
            self.main_window.connection_manager_controller.camera_disconnected.connect(
                self._on_camera_disconnected_from_controller
            )
            self.main_window.connection_manager_controller.camera_connection_error.connect(
                self._on_camera_connection_error
            )
            self.main_window.connection_manager_controller.plc_settings_changed.connect(
                self._on_plc_settings_changed
            )
            self.main_window.connection_manager_controller.ports_refreshed.connect(
                self._on_ports_refreshed
            )

        # =========================================================================
        # TENSION MEASUREMENT CONTROLLER SIGNALS
        # =========================================================================
        if self.main_window.tension_measurement_controller:
            self.main_window.tension_measurement_controller.measurement_started.connect(
                self._on_tension_measurement_started
            )
            self.main_window.tension_measurement_controller.measurement_completed.connect(
                self._on_tension_measurement_completed_from_controller
            )
            self.main_window.tension_measurement_controller.measurement_failed.connect(
                self._on_tension_measurement_failed
            )
            self.main_window.tension_measurement_controller.measurement_saved.connect(
                self._on_tension_measurement_saved
            )

        # =========================================================================
        # DIALOG MANAGER CONTROLLER SIGNALS
        # =========================================================================
        if self.main_window.dialog_manager_controller:
            self.main_window.dialog_manager_controller.dialog_closed.connect(
                self._on_dialog_closed
            )
            self.main_window.dialog_manager_controller.stencil_created.connect(
                self._on_stencil_created_from_manager
            )
            self.main_window.dialog_manager_controller.report_settings_updated.connect(
                self._on_report_settings_updated_from_manager
            )

        # =========================================================================
        # POSITION MANAGER CONTROLLER SIGNALS
        # =========================================================================
        if self.main_window.position_manager_controller:
            self.main_window.position_manager_controller.position_updated.connect(
                self._on_position_updated
            )
            self.main_window.position_manager_controller.position_added.connect(
                self._on_position_added
            )
            self.main_window.position_manager_controller.position_removed.connect(
                self._on_position_removed
            )
            self.main_window.position_manager_controller.position_selected.connect(
                self._on_position_selected_from_controller
            )
            self.main_window.position_manager_controller.sequence_created.connect(
                self._on_sequence_created
            )
            self.main_window.position_manager_controller.position_captured.connect(
                self._on_position_captured
            )

    # =========================================================================
    # RECIPE MANAGER HANDLERS
    # =========================================================================

    def _on_recipe_loaded(self, recipe):
        """Handler quando uma receita é carregada (via RecipeManagerWrapper)."""
        self.main_window.current_recipe = recipe
        self.main_window.recipe_manager.set_current_recipe(recipe)

        # Atualiza o menu
        if hasattr(self.main_window, 'current_recipe_action'):
            self.main_window.current_recipe_action.setText(f"📋 {recipe.name}")
            self.main_window.current_recipe_action.setEnabled(True)

        # Mostra na barra de status
        self.main_window.statusBar().showMessage(f"Receita carregada: {recipe.name}")
        logger.info(f"Receita carregada: {recipe.name} ({recipe.recipe_id})")

    def _on_recipe_created(self, recipe_name: str):
        """Handler chamado quando nova receita é criada (via RecipeManagerWrapper)."""
        logger.info(f"Nova receita criada: {recipe_name}")

    def _on_recipe_applied_to_capture(self, settings: dict):
        """Handler chamado quando configurações de captura são aplicadas."""
        # Verifica se os atributos de mapa existem
        if not hasattr(self.main_window, 'map_origin'):
            self.main_window.map_origin = {}
        if not hasattr(self.main_window, 'map_end'):
            self.main_window.map_end = {}

        # Aplica configurações de captura
        self.main_window.map_origin = settings['origin']
        self.main_window.map_end = settings['end']

        # Tenta atualizar os widgets se existirem
        if hasattr(self.main_window, 'map_step_x_edit'):
            self.main_window.map_step_x_edit.setText(str(settings['step_x']))
        if hasattr(self.main_window, 'map_step_y_edit'):
            self.main_window.map_step_y_edit.setText(str(settings['step_y']))
        if hasattr(self.main_window, 'spin_capture_delay'):
            self.main_window.spin_capture_delay.setValue(settings['capture_delay_ms'])

        # Atualiza painel de informações calculadas
        self.main_window._update_adjusted_step_info()

        # Mostra confirmação
        r = self.main_window.current_recipe
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(
            self.main_window, "Receita Aplicada",
            f"Configurações de captura aplicadas:\n\n"
            f"• Origem: ({settings['origin']['x']}, {settings['origin']['y']})\n"
            f"• Final: ({settings['end']['x']}, {settings['end']['y']})\n"
            f"• Step X: {settings['step_x']} mm\n"
            f"• Step Y: {settings['step_y']} mm\n"
            f"• Delay: {settings['capture_delay_ms']} ms\n"
            f"• Backlight: {'Sim' if settings['backlight_enabled'] else 'Não'}\n\n"
            "Abra 'Definir Mapa' para verificar ou ajustar."
        )

    def _on_recipe_applied_to_tension(self, settings: dict):
        """Handler chamado quando configurações de tensão são aplicadas."""
        r = self.main_window.current_recipe

        # Mostra informações dos critérios de aceitação
        acc = settings['acceptance']
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(
            self.main_window, "Receita de Tensão",
            f"Configurações de tensão da receita '{r.name}':\n\n"
            f"📐 Grid: {settings['grid_rows']} x {settings['grid_cols']}\n"
            f"📍 Área: ({settings['start_point']['x']}, {settings['start_point']['y']}) → "
            f"({settings['end_point']['x']}, {settings['end_point']['y']})\n\n"
            f"📊 Critérios de Aceitação:\n"
            f"  • Mínimo: {acc['min_tension']} N/cm²\n"
            f"  • Máximo: {acc['max_tension']} N/cm²\n"
            f"  • Warning baixo: {acc['warning_low']} N/cm²\n"
            f"  • Warning alto: {acc['warning_high']} N/cm²\n\n"
            "ℹ️ Estes critérios serão usados para classificar as medições."
        )

    def _on_recipe_error(self, error: str):
        """Handler chamado quando ocorre um erro com receitas."""
        logger.error(f"Erro de receita: {error}")

    def _on_recipe_loaded_from_controller(self, recipe):
        """Handler chamado quando uma receita é carregada via controller."""
        logger.info(f"Receita carregada via controller: {recipe.name}")

    def _on_recipe_created_from_controller(self, recipe_name):
        """Handler chamado quando uma receita é criada via controller."""
        logger.info(f"Receita criada via controller: {recipe_name}")

    def _on_recipe_applied_to_capture_from_controller(self, settings):
        """Handler chamado quando configurações de captura são aplicadas via controller."""
        logger.info("Configurações de captura aplicadas via controller")

    def _on_recipe_applied_to_tension_from_controller(self, settings):
        """Handler chamado quando configurações de tensão são aplicadas via controller."""
        logger.info("Configurações de tensão aplicadas via controller")

    def _on_recipe_error_from_controller(self, error_message):
        """Handler chamado quando ocorre um erro com receita via controller."""
        logger.error(f"Erro de receita via controller: {error_message}")

    def _on_recipe_requested(self, recipe_name: str):
        """Handler quando o stencil solicita carregamento de receita."""
        self.main_window.recipe_manager_wrapper.load_recipe(recipe_name)

    # =========================================================================
    # STENCIL MANAGER HANDLERS
    # =========================================================================

    def _on_stencil_selected(self, stencil):
        """Handler quando um stencil é selecionado."""
        self.main_window.current_stencil = stencil
        self.main_window.btn_run_tension.setEnabled(True)

        # Atualiza barra de status
        self.main_window.statusBar().showMessage(
            f"Stencil selecionado: {stencil.code} | "
            f"Receita: {stencil.recipe_name or 'Nenhuma'} | "
            f"Inspeções: {stencil.inspection_count}"
        )

        # Atualiza menu
        self.main_window.current_stencil_action.setText(f"Stencil: {stencil.code}")

        logger.info(f"Stencil selecionado: {stencil.code}")

    def _on_stencil_cleared(self):
        """Handler quando a seleção de stencil é limpa."""
        self.main_window.current_stencil = None
        self.main_window.btn_run_tension.setEnabled(False)
        self.main_window.statusBar().showMessage("Pronto")

        # Atualiza menu
        self.main_window.current_stencil_action.setText("(Nenhum stencil selecionado)")

        logger.info("Seleção de stencil limpa")

    def _on_tension_record_added(self, stencil_code: str, record):
        """Handler chamado quando registro de tensão é adicionado."""
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

        # Atualiza widget de identificação para refletir nova inspeção
        stencil = self.main_window.stencil_manager_wrapper.get_stencil(stencil_code)
        if stencil:
            self.main_window.stencil_identification._select_stencil(stencil)

    def _on_degradation_alert(self, alert: str):
        """Handler chamado quando há alerta de degradação."""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.warning(
            self.main_window, "⚠️ Alerta de Degradação",
            f"Stencil: {self.main_window.current_stencil.code}\n\n{alert}"
        )

    def _on_stencil_error(self, error: str):
        """Handler chamado quando ocorre um erro com stencils."""
        logger.error(f"Erro de stencil: {error}")

        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(
            self.main_window, "Erro de Stencil",
            f"Ocorreu um erro:\n{error}"
        )

    # =========================================================================
    # INSPECTION MANAGER HANDLERS
    # =========================================================================

    def _on_inspection_completed(self, result, overlay):
        """Handler chamado quando inspeção é completada com sucesso."""
        import numpy as np

        # Salvar referências
        self.main_window._last_inspection_result = result
        self.main_window._last_inspection_overlay = overlay

        logger.info(f"Inspeção completada: {result.summary}")

        # Mostrar resultado
        self.main_window._show_inspection_result(result, overlay)

    def _on_inspection_failed(self, error: str):
        """Handler chamado quando inspeção falha."""
        logger.error(f"Inspeção falhou: {error}")

        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(
            self.main_window, "Erro na Inspeção",
            f"A inspeção falhou:\n{error}"
        )

    def _on_thresholds_changed(self, thresholds):
        """Handler chamado quando thresholds de inspeção mudam."""
        logger.info("Thresholds de inspeção alterados")

        # Atualiza referência local
        self.main_window.inspection_thresholds = thresholds
        self.main_window.stencil_inspector = self.main_window.inspection_manager.get_inspector()

    def _on_inspection_requested(self, gerber_file: str):
        """Handler para quando uma inspeção é solicitada."""
        logger.info(f"Inspeção solicitada para arquivo: {gerber_file}")

    # =========================================================================
    # INSPECTION COORDINATOR HANDLERS
    # =========================================================================

    def _on_inspection_step_changed(self, step, message: str):
        """Handler chamado quando a etapa da inspeção muda."""
        logger.info(f"Inspection step: {step.value} - {message}")
        self.main_window.statusBar().showMessage(message)

    def _on_inspection_progress(self, percent: int, message: str):
        """Handler chamado quando o progresso da inspeção atualiza."""
        logger.debug(f"Inspection progress: {percent}% - {message}")
        self.main_window.statusBar().showMessage(f"{message} ({percent}%)")

    def _on_gerber_loaded(self, gerber_data):
        """Handler chamado quando Gerber é carregado."""
        logger.info("Gerber carregado com sucesso")
        self.main_window.statusBar().showMessage("Gerber carregado - Capture fiduciais", 5000)

    def _on_fiducials_captured(self, templates: list):
        """Handler chamado quando fiduciais são capturados."""
        logger.info(f"Fiduciais capturados: {len(templates)} templates")
        self.main_window.statusBar().showMessage(f"Fiduciais capturados: {len(templates)} - Alinhe o sistema", 5000)

    def _on_alignment_completed(self, transformation):
        """Handler chamado quando alinhamento é completado."""
        logger.info("Alinhamento completado")
        self.main_window.statusBar().showMessage("Sistema alinhado - Capture imagem de inspeção", 5000)

    def _on_inspection_image_captured(self, image_path: str):
        """Handler chamado quando imagem de inspeção é capturada."""
        logger.info(f"Imagem capturada: {image_path}")
        self.main_window.statusBar().showMessage("Imagem capturada - Analisando...", 3000)

    def _on_inspection_analysis_completed(self, result, overlay):
        """Handler chamado quando análise é completada."""
        logger.info("Análise completada")
        self.main_window.statusBar().showMessage("Análise concluída", 3000)

    def _on_inspection_workflow_completed(self, result):
        """Handler chamado quando workflow completo termina."""
        if result.success:
            logger.info(f"Inspeção completada: {result.summary}")
            self.main_window.statusBar().showMessage("Inspeção concluída com sucesso", 5000)
        else:
            logger.error(f"Inspeção falhou: {result.error}")
            self.main_window.statusBar().showMessage("Inspeção falhou", 5000)

    def _on_inspection_workflow_failed(self, error: str):
        """Handler chamado quando workflow de inspeção falha."""
        logger.error(f"Workflow de inspeção falhou: {error}")

        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(self.main_window, "Erro na Inspeção", f"O workflow de inspeção falhou:\n{error}")

    # =========================================================================
    # INSPECTION UI CONTROLLER HANDLERS
    # =========================================================================

    def _on_inspection_completed_from_controller(self, result, overlay_path):
        """Handler chamado quando inspeção é completada via InspectionUIController."""
        logger.info(f"Inspeção completada via controller: {result}")

        # Gerar PDF se overlay_path foi fornecido
        if overlay_path:
            try:
                from consumo_lib.managers import ReportManagerWrapper
                report_manager = ReportManagerWrapper(self.main_window.report_generator, self.main_window.config)

                stencil_code = self.main_window.current_stencil.code if self.main_window.current_stencil else None

                pdf_path = report_manager.generate_inspection_report(
                    inspection_result=result,
                    overlay_image_path=overlay_path,
                    stencil_code=stencil_code,
                    operator=self.main_window.config.get("user", "name", default="Operador")
                )

                self.main_window.statusBar().showMessage(f"Relatório salvo: {pdf_path}", 5000)
            except Exception as e:
                logger.exception("Erro ao gerar relatório de inspeção")
                self.main_window.statusBar().showMessage(f"Erro ao gerar relatório: {str(e)}", 5000)

    def _on_inspection_settings_updated(self, thresholds):
        """Handler chamado quando configurações de inspeção são atualizadas."""
        logger.info(f"Configurações de inspeção atualizadas: {thresholds}")
        self.main_window.inspection_thresholds = thresholds

    # =========================================================================
    # TENSION COORDINATOR HANDLERS
    # =========================================================================

    def _on_tension_step_changed(self, step, message: str):
        """Handler chamado quando a etapa da medição muda."""
        logger.info(f"Tension measurement step: {step.value} - {message}")
        self.main_window.statusBar().showMessage(message)

    def _on_tension_progress(self, current: int, total: int, message: str):
        """Handler chamado quando o progresso da medição atualiza."""
        logger.debug(f"Tension progress: {current}/{total} - {message}")
        self.main_window.statusBar().showMessage(f"{message} ({current}/{total} pontos)")

    def _on_tension_grid_generated(self, points: list):
        """Handler chamado quando o grid de medição é gerado."""
        logger.info(f"Grid gerado: {len(points)} pontos")

    def _on_tension_point_started(self, index: int, point):
        """Handler chamado quando a medição de um ponto inicia."""
        logger.debug(f"Iniciando medição do ponto {index}: ({point.x:.1f}, {point.y:.1f})")

    def _on_tension_point_completed(self, index: int, point):
        """Handler chamado quando a medição de um ponto completa."""
        if point.tension is not None:
            logger.info(f"Ponto {index} medido: {point.tension:.2f} N/cm")
        else:
            logger.warning(f"Ponto {index} falhou")

    def _on_tension_measurement_taken(self, x: float, y: float, tension: float):
        """Handler chamado quando uma medição é tomada."""
        logger.debug(f"Medição tomada: ({x:.1f}, {y:.1f}) = {tension:.2f} N/cm")

    def _on_tension_all_completed(self, result):
        """Handler chamado quando todas as medições são completadas."""
        logger.info(f"Todas as medições completadas: {len(result.measurements)} pontos")
        self.main_window.statusBar().showMessage("Medições concluídas - Gerando relatório", 5000)

    def _on_tension_heatmap_generated(self, heatmap_path: str):
        """Handler chamado quando o heatmap é gerado."""
        logger.info(f"Heatmap gerado: {heatmap_path}")
        self.main_window.statusBar().showMessage("Heatmap gerado", 3000)

    def _on_tension_measurement_completed(self, result):
        """Handler chamado quando o workflow completo termina."""
        if result.success:
            classification = result.classification or "unknown"
            avg = result.average_tension or 0
            logger.info(f"Medição completada: {classification} (média: {avg:.2f} N/cm)")
            self.main_window.statusBar().showMessage(
                f"Medição concluída: {classification.upper()} ({avg:.2f} N/cm médio)",
                5000
            )
        else:
            logger.error("Medição falhou")
            self.main_window.statusBar().showMessage("Medição falhou", 5000)

    def _on_tension_measurement_failed(self, error: str):
        """Handler chamado quando workflow de tensão falha."""
        logger.error(f"Workflow de tensão falhou: {error}")

        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(self.main_window, "Erro na Medição", f"O workflow de medição falhou:\n{error}")

    # =========================================================================
    # REPORT MANAGER HANDLERS
    # =========================================================================

    def _on_report_generated(self, report_type: str, output_path: str):
        """Handler chamado quando relatório é gerado com sucesso."""
        logger.info(f"Relatório '{report_type}' gerado: {output_path}")

        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(
            self.main_window, "Relatório Gerado",
            f"Relatório de {report_type} gerado com sucesso!\n\n"
            f"Arquivo: {output_path}"
        )

    def _on_report_failed(self, report_type: str, error: str):
        """Handler chamado quando geração de relatório falha."""
        logger.error(f"Falha ao gerar relatório '{report_type}': {error}")

        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(
            self.main_window, "Erro no Relatório",
            f"Falha ao gerar relatório de {report_type}:\n{error}"
        )

    def _on_report_config_changed(self, config):
        """Handler chamado quando configuração de relatório muda."""
        logger.info("Configuração de relatório alterada")

        # Atualiza referência local
        self.main_window.report_config = config
        self.main_window.report_generator = self.main_window.report_manager_wrapper.get_generator()

    # =========================================================================
    # REPORT DIALOG CONTROLLER HANDLERS
    # =========================================================================

    def _on_tension_report_generated(self, output_path: str):
        """Handler chamado quando relatório de tensão é gerado."""
        logger.info(f"Relatório de tensão gerado: {output_path}")
        self.main_window.statusBar().showMessage(f"Relatório salvo: {output_path}", 5000)

    def _on_stencil_report_generated(self, output_path: str):
        """Handler chamado quando relatório de stencil é gerado."""
        logger.info(f"Relatório de stencil gerado: {output_path}")
        self.main_window.statusBar().showMessage(f"Relatório salvo: {output_path}", 5000)

    def _on_period_query_executed(self, record_count: int):
        """Handler chamado quando consulta por período é executada."""
        logger.info(f"Consulta por período executada: {record_count} registros")

    def _on_report_error(self, error: str):
        """Handler chamado quando ocorre erro na geração de relatório."""
        logger.error(f"Erro na geração de relatório: {error}")

    # =========================================================================
    # SEQUENCE CONTROLLER HANDLERS
    # =========================================================================

    def _on_sequence_created(self, sequence):
        """Handler chamado quando uma sequência é criada."""
        self.main_window.current_sequence = sequence
        self.main_window.statusBar().showMessage(
            f"Sequência '{sequence.name}' criada com {len(sequence.positions)} posições",
            5000
        )

    def _on_sequence_loaded(self, sequence, source):
        """Handler chamado quando uma sequência é carregada."""
        self.main_window.current_sequence = sequence
        self.main_window.statusBar().showMessage(
            f"Sequência carregada de {source}: {len(sequence.positions)} posições",
            5000
        )

    def _on_sequence_saved(self, filepath):
        """Handler chamado quando uma sequência é salva."""
        self.main_window.statusBar().showMessage(f"G-CODE salvo em {filepath}", 5000)

    def _on_sequence_execution_started(self, sequence_name):
        """Handler chamado quando a execução da sequência é iniciada."""
        self.main_window.is_running_sequence = True
        self.main_window.statusBar().showMessage(f"Executando sequência '{sequence_name}'...")

    def _on_sequence_execution_stopped(self):
        """Handler chamado quando a execução da sequência é parada."""
        self.main_window.is_running_sequence = False
        self.main_window.statusBar().showMessage("Execução de sequência interrompida", 5000)

    def _on_sequence_execution_finished(self):
        """Handler chamado quando a execução da sequência é finalizada."""
        self.main_window.is_running_sequence = False
        self.main_window.statusBar().showMessage("Execução de sequência concluída", 5000)

    def _on_sequence_error_from_controller(self, error_message):
        """Handler chamado quando ocorre um erro na execução da sequência."""
        logger.error(f"Erro na sequência: {error_message}")

    def _on_position_captured(self, position, image, timestamp):
        """Handler chamado quando uma posição é capturada."""
        import time
        self.main_window.statusBar().showMessage(
            f"Posição capturada: {position.name} ({position.x:.3f}, {position.y:.3f})",
            3000
        )

    # =========================================================================
    # MAP CONTROLLER HANDLERS
    # =========================================================================

    def _on_map_program_saved(self, name, path):
        """Handler quando um programa de mapa é salvo."""
        logger.info(f"Programa de mapa salvo: {name} -> {path}")
        self.main_window.statusBar().showMessage(f"Programa '{name}' salvo com sucesso", 3000)

    def _on_map_program_loaded(self, name, params):
        """Handler quando um programa de mapa é carregado."""
        logger.info(f"Programa de mapa carregado: {name}")
        self.main_window.statusBar().showMessage(f"Programa '{name}' carregado", 3000)

    def _on_map_program_deleted(self, name):
        """Handler quando um programa de mapa é excluído."""
        logger.info(f"Programa de mapa excluído: {name}")
        self.main_window.statusBar().showMessage(f"Programa '{name}' excluído", 3000)

    def _on_map_generated(self, mosaic_path):
        """Handler quando geração de mapa é completada."""
        logger.info(f"Mosaico gerado: {mosaic_path}")
        self.main_window.statusBar().showMessage(f"Mosaico gerado com sucesso", 5000)

        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(
            self.main_window, "Mosaico Gerado",
            f"O mosaico foi gerado com sucesso!\n\n"
            f"Arquivo: {mosaic_path}"
        )

    def _on_map_progress(self, current, total, message):
        """Handler durante progresso da geração do mapa."""
        logger.debug(f"Progresso do mapa: {current}/{total} - {message}")

    def _on_map_error(self, error_message):
        """Handler quando ocorre erro na geração do mapa."""
        logger.error(f"Erro no mapa: {error_message}")

        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(self.main_window, "Erro na Geração do Mapa", error_message)

    # =========================================================================
    # CAMERA SETTINGS CONTROLLER HANDLERS
    # =========================================================================

    def _on_camera_settings_changed(self, settings):
        """Handler quando configurações de câmera são alteradas."""
        logger.debug(f"Configurações de câmera alteradas: {settings}")

    def _on_camera_settings_applied(self, settings):
        """Handler quando configurações de câmera são aplicadas."""
        logger.info(f"Configurações de câmera aplicadas")

        # Atualiza variáveis internas
        self.main_window._camera_mirror_x = settings.get('mirror_x', False)
        self.main_window._camera_mirror_y = settings.get('mirror_y', False)

        # Aplica ao preview se disponível
        if hasattr(self.main_window, 'cnc_tab') and hasattr(self.main_window.cnc_tab, 'camera_preview'):
            self.main_window.cnc_tab.camera_preview.set_mirror(
                self.main_window._camera_mirror_x,
                self.main_window._camera_mirror_y
            )

        self.main_window.statusBar().showMessage("Configurações de câmera aplicadas", 3000)

    def _on_camera_settings_saved(self, preset_name):
        """Handler quando preset de câmera é salvo."""
        logger.info(f"Preset de câmera salvo: {preset_name}")
        self.main_window.statusBar().showMessage(f"Preset '{preset_name}' salvo", 3000)

    def _on_camera_settings_loaded(self, preset_name):
        """Handler quando preset de câmera é carregado."""
        logger.info(f"Preset de câmera carregado: {preset_name}")
        self.main_window.statusBar().showMessage(f"Preset '{preset_name}' carregado", 3000)

    # =========================================================================
    # CALIBRATION CONTROLLER HANDLERS
    # =========================================================================

    def _on_calibration_applied(self, steps_x, steps_y):
        """Handler quando calibração é aplicada."""
        logger.info(f"Calibração aplicada: X={steps_x} steps/mm, Y={steps_y} steps/mm")

        # Atualiza configurações
        self.main_window.config.set("connections", "pulses_per_rev", int(steps_x * 10))
        self.main_window.config.set("connections", "fuso_pitch", 10.0)
        self.main_window.config.save()

        self.main_window.statusBar().showMessage(
            f"Calibração aplicada: {steps_x:.2f} x {steps_y:.2f} steps/mm",
            3000
        )

    def _on_calibration_completed(self):
        """Handler quando calibração é completada."""
        logger.info("Calibração completada")
        self.main_window.statusBar().showMessage("Calibração completada com sucesso", 3000)

    def _on_calibration_test_completed(self, movement_ok, message):
        """Handler quando teste de calibração é completado."""
        status = "OK" if movement_ok else "FALHOU"
        logger.info(f"Teste de calibração: {status} - {message}")

        from PyQt6.QtWidgets import QMessageBox
        if movement_ok:
            QMessageBox.information(self.main_window, "Teste de Calibração", f"Teste concluído com sucesso!\n\n{message}")
        else:
            QMessageBox.warning(self.main_window, "Teste de Calibração", f"Teste falhou!\n\n{message}")

        self.main_window.statusBar().showMessage(f"Teste de calibração: {status}", 3000)

    # =========================================================================
    # FIDUCIAL ALIGNMENT CONTROLLER HANDLERS
    # =========================================================================

    def _on_fiducial_alignment_completed(self, transform):
        """Handler chamado quando o alinhamento de fiduciais é completado."""
        logger.info(f"Alinhamento de fiduciais completado: {transform}")
        self.main_window.statusBar().showMessage(
            f"Alinhamento aplicado: tx={transform.tx:.1f}, ty={transform.ty:.1f}, "
            f"rot={transform.angle:.2f}°",
            5000
        )

    def _on_fiducial_alignment_cancelled(self):
        """Handler chamado quando o alinhamento é cancelado."""
        logger.info("Alinhamento de fiduciais cancelado")
        self.main_window.statusBar().showMessage("Alinhamento cancelado", 3000)

    def _on_fiducial_alignment_error(self, error):
        """Handler chamado quando ocorre um erro no alinhamento."""
        logger.error(f"Erro no alinhamento de fiduciais: {error}")

    # =========================================================================
    # CONNECTION MANAGER CONTROLLER HANDLERS
    # =========================================================================

    def _on_camera_connected_from_controller(self, camera_id):
        """Handler chamado quando a câmera conecta com sucesso."""
        logger.info(f"Câmera {camera_id} conectada (via controller)")

    def _on_camera_disconnected_from_controller(self):
        """Handler chamado quando a câmera desconecta."""
        logger.info("Câmera desconectada (via controller)")

    def _on_camera_connection_error(self, error_message):
        """Handler chamado quando ocorre um erro de conexão da câmera."""
        logger.error(f"Erro de conexão da câmera: {error_message}")

    def _on_plc_settings_changed(self, host, port):
        """Handler chamado quando as configurações de PLC mudam."""
        logger.info(f"Configurações de PLC alteradas para {host}:{port}")

    def _on_ports_refreshed(self, ports_list):
        """Handler chamado quando a lista de portas é atualizada."""
        logger.debug(f"Lista de portas atualizada: {len(ports_list)} portas encontradas")

    # =========================================================================
    # TENSION MEASUREMENT CONTROLLER HANDLERS
    # =========================================================================

    def _on_tension_measurement_started(self):
        """Handler chamado quando a medição de tensão é iniciada."""
        logger.info("Medição de tensão iniciada (via controller)")

    def _on_tension_measurement_completed_from_controller(self, record):
        """Handler chamado quando a medição de tensão é completada."""
        logger.info(f"Medição de tensão completada: {record}")

    def _on_tension_measurement_saved(self, stencil_code, record):
        """Handler chamado quando a medição de tensão é salva no histórico."""
        logger.info(f"Medição de tensão salva para stencil {stencil_code}")

    # =========================================================================
    # DIALOG MANAGER CONTROLLER HANDLERS
    # =========================================================================

    def _on_dialog_closed(self, dialog_name):
        """Handler chamado quando um diálogo é fechado."""
        logger.debug(f"Diálogo '{dialog_name}' fechado")

    def _on_stencil_created_from_manager(self, stencil):
        """Handler chamado quando um novo stencil é criado."""
        logger.info(f"Stencil criado via DialogManager: {stencil.code}")

    def _on_report_settings_updated_from_manager(self, config):
        """Handler chamado quando as configurações de relatório são atualizadas."""
        logger.info("Configurações de relatório atualizadas via DialogManager")

    # =========================================================================
    # POSITION MANAGER CONTROLLER HANDLERS
    # =========================================================================

    def _on_position_updated(self, position):
        """Handler chamado quando a posição CNC é atualizada."""
        logger.debug(f"Posição atualizada: {position}")

    def _on_position_added(self, position):
        """Handler chamado quando uma posição é adicionada."""
        logger.info(f"Posição adicionada: {position.name}")

    def _on_position_removed(self, position_name):
        """Handler chamado quando uma posição é removida."""
        logger.info(f"Posição removida: {position_name}")

    def _on_position_selected_from_controller(self, position):
        """Handler chamado quando uma posição é selecionada."""
        logger.debug(f"Posição selecionada: {position.name}")
