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

import logging
from typing import Optional, Any

from PyQt6.QtCore import QObject, pyqtSignal, Qt
from PyQt6.QtWidgets import QMessageBox, QDialog, QProgressDialog

from aoi_lib.stencil_tracker import Stencil, TensionRecord
from aoi_lib.tensiometer import MeasurementOrchestrator, TensiometerSerialManager
from consumo_lib.managers.measurement_pattern_manager import MeasurementPatternManager
from consumo_lib.utils.error_handler import show_motion_interlock_dialog
from consumo_lib.utils.tension_measurement_data import load_tension_measurement_data

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
        self.pattern_manager = MeasurementPatternManager()

        self._active_progress_dialog: Optional[QProgressDialog] = None
        self._active_tensiometer: Optional[TensiometerSerialManager] = None
        self._active_orchestrator: Optional[MeasurementOrchestrator] = None
        self._active_stencil: Optional[Stencil] = None
        self._active_recipe = None
        self._active_ui_parent = None
        self._cancel_requested = False

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

        # Se houver receita vinculada, pré-configura o diálogo mesmo em receitas legadas
        # com tension.enabled=False. O usuário iniciou explicitamente a medição a partir
        # do stencil, então os parâmetros salvos da receita devem ser reaplicados.
        if current_recipe and getattr(current_recipe, "tension", None):
            logger.debug(
                "Aplicando parâmetros da receita %s à medição (enabled=%s)",
                current_recipe.name,
                current_recipe.tension.enabled,
            )
            dlg.apply_recipe(current_recipe)

        result = dlg.exec()

        # Se medição foi concluída, salva no histórico
        if result == QDialog.DialogCode.Accepted:
            self.save_measurement(current_stencil, current_recipe, dlg)

    def run_recipe_measurement(
        self,
        current_stencil: Optional[Stencil],
        current_recipe=None,
        interaction_parent=None,
    ) -> bool:
        """
        Executa medição operacional do stencil usando diretamente a receita.

        Este fluxo não abre o diálogo manual de medição. Ele resolve os
        parâmetros da receita/padrão, conecta o tensiômetro automaticamente e
        dispara o MeasurementOrchestrator em background.
        """
        ui_parent = interaction_parent or self.parent_window

        if not current_stencil:
            error_msg = "Selecione um stencil antes de iniciar a medição."
            QMessageBox.warning(ui_parent, "Stencil Não Selecionado", error_msg)
            self.measurement_failed.emit(error_msg)
            return False

        if not getattr(self.controller.cnc, "is_connected", False):
            error_msg = "Conecte o CLP antes de iniciar a medição do stencil."
            QMessageBox.warning(ui_parent, "CLP Não Conectado", error_msg)
            self.measurement_failed.emit(error_msg)
            return False

        recipe = self._resolve_recipe_for_stencil(current_stencil, current_recipe)
        if recipe is None:
            recipe_name = current_stencil.recipe_name or "(sem receita)"
            error_msg = (
                f"O stencil '{current_stencil.code}' não possui uma receita válida carregada.\n\n"
                f"Receita vinculada: {recipe_name}"
            )
            QMessageBox.warning(ui_parent, "Receita Não Encontrada", error_msg)
            self.measurement_failed.emit(error_msg)
            return False

        try:
            params = self._build_measurement_parameters_from_recipe(recipe)
        except Exception as exc:
            error_msg = f"Erro ao preparar os parâmetros da receita '{recipe.name}': {exc}"
            logger.exception("Falha ao resolver parâmetros de medição da receita")
            QMessageBox.critical(ui_parent, "Erro na Receita", error_msg)
            self.measurement_failed.emit(error_msg)
            return False

        try:
            tensiometer = self._connect_tensiometer_for_operator_flow()
        except Exception as exc:
            error_msg = f"Não foi possível conectar o tensiômetro: {exc}"
            logger.exception("Falha ao conectar tensiômetro no fluxo operacional")
            QMessageBox.critical(ui_parent, "Tensiômetro", error_msg)
            self.measurement_failed.emit(error_msg)
            return False

        orchestrator = MeasurementOrchestrator(self.controller.cnc, tensiometer)
        prepared = orchestrator.prepare_measurement(
            start_point=params["start_point"],
            end_point=params["end_point"],
            grid_size=params["grid_size"],
            z_height=params["z_height"],
            z_move=params["z_move"],
            user_feed=params["feed_rate"],
            stabilization_time_ms=params["stabilization_time_ms"],
        )

        if not prepared["success"]:
            self._disconnect_tensiometer(tensiometer)
            error_msg = prepared.get("error", "Falha desconhecida ao preparar a medição.")
            QMessageBox.critical(ui_parent, "Erro de Validação", error_msg)
            self.measurement_failed.emit(error_msg)
            return False

        self._active_ui_parent = ui_parent
        self._active_stencil = current_stencil
        self._active_recipe = recipe
        self._active_tensiometer = tensiometer
        self._active_orchestrator = orchestrator
        self._cancel_requested = False

        total_points = len(prepared.get("points", []))
        self._show_progress_dialog(
            total_points=total_points,
            stencil_code=current_stencil.code,
            recipe_name=recipe.name,
            source_description=params["source_description"],
        )

        self.measurement_started.emit()
        self.parent_window.statusBar().showMessage(
            f"Iniciando medição do stencil {current_stencil.code} com receita {recipe.name}"
        )
        logger.info(
            "Iniciando medição operacional do stencil %s com receita %s (%s)",
            current_stencil.code,
            recipe.name,
            params["source_description"],
        )

        started = orchestrator.start_measurement(
            points=prepared["points"],
            on_progress=self._on_runtime_progress,
            on_measurement=self._on_runtime_measurement,
            on_complete=self._on_runtime_complete,
            on_error=self._on_runtime_error,
        )
        if not started:
            self._close_progress_dialog()
            self._cleanup_runtime_measurement()
            error_msg = "Falha ao iniciar a thread de medição."
            QMessageBox.critical(ui_parent, "Erro", error_msg)
            self.measurement_failed.emit(error_msg)
            return False

        return True

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
            tension_data = load_tension_measurement_data(tension_dialog)
            self._save_measurement_data(current_stencil, current_recipe, tension_data)

        except Exception as e:
            error_msg = f"Erro ao salvar medição no histórico: {e}"
            logger.exception("Erro ao salvar medição de tensão")
            QMessageBox.warning(
                self.parent_window,
                "Erro",
                f"Erro ao salvar no histórico:\n{str(e)}"
            )
            self.measurement_failed.emit(error_msg)

    def save_measurement_results(self, current_stencil: Stencil, current_recipe, results: dict):
        """Salva no histórico um resultado vindo do fluxo operacional."""
        session_data = results.get("session") if isinstance(results, dict) else None
        if not isinstance(session_data, dict):
            raise ValueError("Resultado da medição não contém sessão válida para persistência.")
        return self._save_measurement_data(
            current_stencil,
            current_recipe,
            session_data,
            emit_signals=False,
        )

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

    def _resolve_recipe_for_stencil(self, current_stencil: Stencil, current_recipe):
        """Resolve a receita efetiva do stencil, recarregando por nome quando necessário."""
        desired_name = (current_stencil.recipe_name or "").strip()

        if current_recipe is not None and getattr(current_recipe, "name", None) == desired_name:
            return current_recipe

        if not desired_name:
            return current_recipe

        recipe_wrapper = getattr(self.parent_window, "recipe_manager_wrapper", None)
        if recipe_wrapper is not None:
            recipe = recipe_wrapper.load_recipe(desired_name)
            if recipe is not None:
                return recipe

        recipe_manager = getattr(self.parent_window, "recipe_manager", None)
        if recipe_manager is not None and hasattr(recipe_manager, "load_recipe"):
            return recipe_manager.load_recipe(desired_name)

        return None

    def _build_measurement_parameters_from_recipe(self, recipe) -> dict:
        """Monta os parâmetros operacionais a partir da receita ou do padrão vinculado."""
        if recipe is None or not getattr(recipe, "tension", None):
            raise ValueError("Receita sem configuração de tensão.")

        tension = recipe.tension
        pattern_name = (getattr(tension, "measurement_pattern_name", "") or "").strip()
        pattern = self.pattern_manager.load_pattern(pattern_name) if pattern_name else None

        recipe_feed_rate = getattr(tension, "feed_rate", None)
        if recipe_feed_rate is not None:
            try:
                recipe_feed_rate = float(recipe_feed_rate)
            except (TypeError, ValueError):
                recipe_feed_rate = None
            if recipe_feed_rate is not None and recipe_feed_rate <= 0:
                recipe_feed_rate = None

        stabilization_time_ms = self._get_global_delay_medidor_ms()

        if pattern is not None:
            grid_parameters = pattern.grid_parameters
            source_description = f"padrão '{pattern.name}'"
            # No fluxo operacional, o padrão define apenas geometria.
            # A velocidade deve vir da receita quando explicitamente configurada;
            # caso contrário, preservamos a velocidade já ativa no PLC.
            feed_rate = recipe_feed_rate
            grid_size = int(grid_parameters.grid_size)
            start_point = tuple(grid_parameters.start_point)
            end_point = tuple(grid_parameters.end_point)
            z_height = float(grid_parameters.z_height)
            z_move = float(grid_parameters.z_move)
        else:
            grid_rows = int(getattr(tension, "grid_rows", 0) or 0)
            grid_cols = int(getattr(tension, "grid_cols", 0) or 0)
            grid_size = max(grid_rows, grid_cols)
            if grid_size < 2:
                raise ValueError("A receita precisa ter um grid NxN com pelo menos 2 pontos por lado.")
            if grid_rows and grid_cols and grid_rows != grid_cols:
                logger.warning(
                    "Receita '%s' possui grid %sx%s; o fluxo operacional usará %sx%s.",
                    recipe.name,
                    grid_rows,
                    grid_cols,
                    grid_size,
                    grid_size,
                )

            source_description = "campos de tensão da receita"
            feed_rate = recipe_feed_rate
            start_point = (float(tension.start_point.x), float(tension.start_point.y))
            end_point = (float(tension.end_point.x), float(tension.end_point.y))
            z_height = float(tension.measurement_height)
            z_move = float(tension.movement_height)

        return {
            "grid_size": grid_size,
            "start_point": start_point,
            "end_point": end_point,
            "z_height": z_height,
            "z_move": z_move,
            "feed_rate": feed_rate,
            "stabilization_time_ms": stabilization_time_ms,
            "source_description": source_description,
        }

    def _get_global_delay_medidor_ms(self) -> int:
        """Retorna o Delay_Medidor configurado na aplicação."""
        if hasattr(self.config, "get_delay_medidor_ms"):
            return self.config.get_delay_medidor_ms()

        try:
            return max(0, int(self.config.get("tension", "delay_medidor_ms", default=500)))
        except (TypeError, ValueError):
            return 500

    def _connect_tensiometer_for_operator_flow(self) -> TensiometerSerialManager:
        """Conecta automaticamente o tensiômetro para o fluxo operacional."""
        tensiometer = TensiometerSerialManager()
        ports = tensiometer.get_available_ports()
        if not ports:
            raise RuntimeError("Nenhuma porta serial disponível para o tensiômetro.")

        selected_port = ports[0]
        logger.info("Fluxo operacional: tentando conectar tensiômetro em %s", selected_port)
        if not tensiometer.connect(selected_port):
            raise RuntimeError(tensiometer.last_error or f"Falha ao conectar em {selected_port}")
        return tensiometer

    def _show_progress_dialog(
        self,
        total_points: int,
        stencil_code: str,
        recipe_name: str,
        source_description: str,
    ) -> None:
        """Exibe um progresso operacional simples durante a medição."""
        dialog = QProgressDialog(self._active_ui_parent or self.parent_window)
        dialog.setWindowTitle("Medição do Stencil")
        dialog.setLabelText(
            f"Preparando medição de {stencil_code}\n"
            f"Receita: {recipe_name}\n"
            f"Base: {source_description}"
        )
        dialog.setCancelButtonText("Parar")
        dialog.setRange(0, max(1, total_points))
        dialog.setValue(0)
        dialog.setMinimumDuration(0)
        dialog.setAutoClose(False)
        dialog.setAutoReset(False)
        dialog.setWindowModality(Qt.WindowModality.WindowModal)
        dialog.canceled.connect(self._cancel_runtime_measurement)
        dialog.show()
        self._active_progress_dialog = dialog

    def _cancel_runtime_measurement(self):
        """Solicita parada da medição operacional em andamento."""
        if self._active_orchestrator is None:
            return
        self._cancel_requested = True
        self._active_orchestrator.stop_measurement()
        if self._active_progress_dialog is not None:
            self._active_progress_dialog.setLabelText("Parando medição...")
            self._active_progress_dialog.setCancelButton(None)

    def _on_runtime_progress(self, current: int, total: int, message: str):
        """Atualiza progresso da medição operacional."""
        self.on_tension_progress_update_status(current, total, message)
        if self._active_progress_dialog is not None:
            self._active_progress_dialog.setMaximum(max(1, total))
            self._active_progress_dialog.setValue(min(current, total))
            self._active_progress_dialog.setLabelText(message)

    def _on_runtime_measurement(self, measurement_dict: dict):
        """Atualiza a UI com a última leitura operacional."""
        tension_value = measurement_dict.get("tension", "--")
        point_index = int(measurement_dict.get("index", 0)) + 1
        self.parent_window.statusBar().showMessage(
            f"Ponto {point_index}: {tension_value} N/cm²"
        )

    def _on_runtime_complete(self, results: dict):
        """Finaliza o fluxo operacional após a medição concluir."""
        stencil = self._active_stencil
        recipe = self._active_recipe
        saved_path = results.get("saved_to")

        self._close_progress_dialog()

        try:
            record = self.save_measurement_results(stencil, recipe, results)
            self.parent_window.statusBar().showMessage(
                f"Medição concluída: {stencil.code} | Resultado {record.result}",
                10000,
            )
            self._refresh_runtime_views(saved_path)
        except Exception as exc:
            error_msg = f"Erro ao finalizar a medição do stencil: {exc}"
            logger.exception("Falha ao finalizar medição operacional")
            QMessageBox.critical(self._active_ui_parent or self.parent_window, "Erro", error_msg)
            self.measurement_failed.emit(error_msg)
        finally:
            self._cleanup_runtime_measurement()

    def _on_runtime_error(self, error_message: str):
        """Trata erros ou cancelamentos do fluxo operacional."""
        canceled = self._cancel_requested or "interrompida" in error_message.lower()
        self._close_progress_dialog()

        if canceled:
            self.parent_window.statusBar().showMessage("Medição interrompida pelo operador.", 5000)
        else:
            logger.error("Erro na medição operacional: %s", error_message)
            parent = self._active_ui_parent or self.parent_window
            if show_motion_interlock_dialog(parent, error_message, operation="medicao automatica"):
                self.measurement_failed.emit(error_message)
                self._cleanup_runtime_measurement()
                return
            QMessageBox.critical(
                parent,
                "Erro na Medição",
                error_message,
            )
            self.measurement_failed.emit(error_message)

        self._cleanup_runtime_measurement()

    def _close_progress_dialog(self):
        """Fecha o diálogo de progresso se estiver aberto."""
        if self._active_progress_dialog is not None:
            self._active_progress_dialog.blockSignals(True)
            self._active_progress_dialog.close()
            self._active_progress_dialog.deleteLater()
            self._active_progress_dialog = None

    def _cleanup_runtime_measurement(self):
        """Libera recursos usados pelo fluxo operacional."""
        if self._active_orchestrator is not None:
            try:
                self._active_orchestrator.cleanup()
            except Exception:
                logger.debug("Falha ignorada no cleanup do orchestrator", exc_info=True)

        self._disconnect_tensiometer(self._active_tensiometer)
        self._active_tensiometer = None
        self._active_orchestrator = None
        self._active_stencil = None
        self._active_recipe = None
        self._active_ui_parent = None
        self._cancel_requested = False

    def _disconnect_tensiometer(self, tensiometer: Optional[TensiometerSerialManager]) -> None:
        if tensiometer is None:
            return
        try:
            tensiometer.disconnect()
        except Exception:
            logger.debug("Falha ignorada ao desconectar tensiômetro", exc_info=True)

    def _refresh_runtime_views(self, saved_path: Optional[str]) -> None:
        """Atualiza a tela principal após uma medição operacional."""
        tension_tab = getattr(self.parent_window, "tension_measurement_tab", None)
        if tension_tab is not None:
            if hasattr(tension_tab, "load_stencils"):
                tension_tab.load_stencils()
            if saved_path and hasattr(tension_tab, "load_file"):
                try:
                    tension_tab.load_file(saved_path)
                except Exception:
                    logger.debug("Falha ao carregar arquivo salvo na aba de tensão", exc_info=True)

        stencil_identification = getattr(self.parent_window, "stencil_identification", None)
        active_stencil = self._active_stencil
        if stencil_identification is not None and active_stencil is not None:
            try:
                refreshed_stencil = self.stencil_manager_wrapper.get_stencil(active_stencil.code)
                if refreshed_stencil is not None:
                    stencil_identification._select_stencil(refreshed_stencil)
            except Exception:
                logger.debug("Falha ao atualizar widget de rastreabilidade apos medicao", exc_info=True)

    def _save_measurement_data(
        self,
        current_stencil: Stencil,
        current_recipe,
        tension_data: dict,
        emit_signals: bool = True
    ):
        """Cria e persiste o registro de tensão no histórico do stencil."""
        classified_data = self._classify_measurements_by_recipe(tension_data, current_recipe)
        record = TensionRecord.from_tension_data(
            classified_data,
            recipe_name=current_recipe.name if current_recipe else None,
            operator=None,
        )

        recipe_acceptance = None
        if current_recipe and getattr(current_recipe, "tension", None) and current_recipe.tension.acceptance:
            recipe_acceptance = current_recipe.tension.acceptance

        added = self.stencil_manager_wrapper.add_tension_record(
            current_stencil.code,
            record,
            recipe_acceptance=recipe_acceptance,
            emit_signals=emit_signals,
        )
        if not added:
            raise RuntimeError("O histórico do stencil recusou o registro da medição.")

        logger.info(f"Medição de tensão salva para stencil {current_stencil.code}")
        self.measurement_completed.emit(record)
        self.measurement_saved.emit(current_stencil.code, record)
        return record

    def _classify_measurements_by_recipe(self, tension_data: dict, current_recipe) -> dict:
        """Anota o status OK/WARNING/NOK de cada leitura usando os critérios da receita."""
        measurements = tension_data.get("measurements", [])
        if not measurements:
            return tension_data

        acceptance = None
        if current_recipe and getattr(current_recipe, "tension", None):
            acceptance = getattr(current_recipe.tension, "acceptance", None)
        if acceptance is None:
            return tension_data

        enriched_measurements = []
        for measurement in measurements:
            enriched = dict(measurement)
            tension_value = enriched.get("parsed_value", enriched.get("tension"))
            try:
                numeric_value = float(tension_value)
            except (TypeError, ValueError):
                enriched_measurements.append(enriched)
                continue
            enriched["status"] = acceptance.classify(numeric_value)
            enriched_measurements.append(enriched)

        enriched_data = dict(tension_data)
        enriched_data["measurements"] = enriched_measurements
        return enriched_data

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
