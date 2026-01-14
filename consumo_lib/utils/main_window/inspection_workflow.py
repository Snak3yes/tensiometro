"""
Módulo: inspection_workflow.py

Gerencia o workflow de inspeção da MainWindow (AOIControllerApp).

Responsabilidades:
- Executar inspeção (run_inspection)
- Exibir resultados da inspeção (show_inspection_results)
- Salvar inspeção no histórico (save_inspection_to_history)
- Mostrar confirmação de posicionamento (show_positioning_confirmation)
- Mostrar seleção de modo (show_mode_selection)
- Exibir histórico de inspeção (show_inspection_history)

Author: Refactoring (2026-01-14)
"""

import logging
from datetime import datetime
from typing import Dict, Any
from PyQt6.QtWidgets import QDialog, QMessageBox

logger = logging.getLogger(__name__)


class MainWindowInspectionWorkflow:
    """
    Gerencia o workflow de inspeção da MainWindow.

    Centraliza toda lógica relacionada ao fluxo de inspeção:
    Posicionamento → Seleção de Modo → Execução → Resultados

    Attributes:
        main_window: Instância da MainWindow (AOIControllerApp)
        state: MainWindowState para gerenciar estado da aplicação
    """

    def __init__(self, main_window, state=None):
        """
        Inicializa o MainWindowInspectionWorkflow.

        Args:
            main_window: Instância da MainWindow (AOIControllerApp)
            state: MainWindowState (opcional)
        """
        self.main_window = main_window
        self.state = state

    # =========================================================================
    # WORKFLOW DE INSPEÇÃO
    # =========================================================================

    def execute_inspection_flow(self, stencil: Dict[str, Any]):
        """
        Executa o fluxo completo de inspeção.

        Fluxo: TreeView → Posicionamento → Modo → Execução

        Args:
            stencil: Dicionário com dados do stencil
        """
        logger.info(f"Solicitação de inspeção: {stencil.get('code', 'N/A')}")

        # FASE 3: Confirmar posicionamento
        if not self.show_positioning_confirmation(stencil):
            # Usuário cancelou
            logger.info("Posicionamento cancelado pelo usuário")
            return

        # FASE 4: Escolher modo de inspeção
        if not self.show_mode_selection(stencil):
            logger.info("Seleção de modo cancelada pelo usuário")
            return

        # FASE 5: Executar inspeção
        self.run_inspection(stencil)

    def run_inspection(self, stencil: Dict[str, Any]):
        """
        Executa inspeção com tela de progresso.

        Args:
            stencil: Dicionário com dados do stencil
        """
        from consumo_lib.dialogs import InspectionProgressDialog
        from consumo_lib.threads import InspectionWorker

        mode = self._get_inspection_mode()

        # Cria dialog de progresso
        progress_dialog = InspectionProgressDialog(
            stencil['code'],
            mode,
            self.main_window
        )

        # Cria worker thread
        worker = InspectionWorker(
            stencil['code'],
            mode,
            self.main_window
        )

        # Conecta sinais
        worker.execution_complete.connect(
            lambda success, msg: self.on_inspection_complete(success, msg, stencil)
        )

        # Inicia execução
        progress_dialog.start_execution(worker)

        # Mostra dialog modal
        progress_dialog.exec()

        # Se completou com sucesso, armazena resultados
        if progress_dialog.is_complete:
            results = progress_dialog.get_results()
            self._set_inspection_results(results)
            logger.info(f"Resultados da inspeção: {results}")

    def on_inspection_complete(self, success: bool, message: str, stencil: Dict[str, Any]):
        """
        Handler: Inspeção completada.

        Args:
            success: True se sucesso
            message: Mensagem de resultado
            stencil: Dados do stencil
        """
        if success:
            logger.info(f"Inspeção concluída: {stencil['code']} - {message}")

            # FASE 6: Exibir resultados
            self.show_inspection_results(stencil)
        else:
            logger.error(f"Inspeção falhou: {stencil['code']} - {message}")
            QMessageBox.warning(
                self.main_window,
                "Erro na Inspeção",
                f"A inspeção não pôde ser concluída:\n\n{message}"
            )

    def show_inspection_results(self, stencil: Dict[str, Any]):
        """
        Exibe dialog de resultados da inspeção.

        Args:
            stencil: Dicionário com dados do stencil
        """
        from consumo_lib.dialogs import InspectionResultsDialog

        mode = self._get_inspection_mode()
        results = self._get_inspection_results()

        dialog = InspectionResultsDialog(
            stencil['code'],
            mode,
            results,
            self.main_window
        )

        dialog.exec()

    def save_inspection_to_history(self, stencil: Dict[str, Any], results: Dict[str, Any], mode: str) -> bool:
        """
        Salva inspeção no histórico do stencil.

        Args:
            stencil: Dicionário com dados do stencil
            results: Resultados da inspeção
            mode: Modo executado ("tension", "inspection", "both")

        Returns:
            True se salvou com sucesso, False caso contrário
        """
        from aoi_lib import StencilTracker, Stencil, TensionRecord, InspectionRecord

        try:
            user = self.main_window.auth_service.get_current_user()
            timestamp = datetime.now().isoformat()

            # Verifica se stencil existe, senão cria
            tracker = StencilTracker()
            if not tracker.stencil_exists(stencil['code']):
                # Cria stencil básico
                new_stencil = Stencil(
                    code=stencil['code'],
                    description=stencil.get('description', ''),
                    recipe_name=stencil.get('recipe', 'Limpeza Padrão')
                )
                tracker.create_stencil(new_stencil)
                logger.info(f"Stencil {stencil['code']} criado automaticamente")

            # Salva registros dependendo do modo
            if mode in ["tension", "both"]:
                # Obtém dados de tensão
                if mode == "both":
                    tension_data = results.get('tension_results', {})
                else:
                    tension_data = results

                # Cria TensionRecord
                tension_record = TensionRecord(
                    timestamp=timestamp,
                    measurements=[],  # Vazio por enquanto (simulação)
                    average_tension=tension_data.get('tension_avg', 0.0),
                    min_tension=tension_data.get('tension_min', 0.0),
                    max_tension=tension_data.get('tension_max', 0.0),
                    result=tension_data.get('classification', 'OK'),
                    ok_count=1,  # Simulação
                    warning_count=0,
                    nok_count=0,
                    operator=user.username,
                    recipe_name=stencil.get('recipe', 'Limpeza Padrão')
                )

                tracker.add_tension_record(stencil['code'], tension_record)
                logger.info(f"Registro de tensão salvo: {stencil['code']}")

            if mode in ["inspection", "both"]:
                # Obtém dados de inspeção
                if mode == "both":
                    inspection_data = results.get('inspection_results', {})
                else:
                    inspection_data = results

                # Mapeia classification (OK/WARNING/NOK) para result (PASS/FAIL)
                classification = inspection_data.get('classification', 'OK')
                result = "PASS" if classification == "OK" else "FAIL"

                # Calcula pass_rate
                total = inspection_data.get('apertures_analyzed', 1)
                ok = inspection_data.get('ok_count', 0)
                partial = inspection_data.get('partial_count', 0)
                pass_rate = ((ok * 100) + (partial * 50)) / total if total > 0 else 100.0

                # Cria InspectionRecord
                inspection_record = InspectionRecord(
                    timestamp=timestamp,
                    total_apertures=inspection_data.get('apertures_analyzed', 0),
                    ok_count=inspection_data.get('ok_count', 0),
                    partial_count=inspection_data.get('partial_count', 0),
                    blocked_count=inspection_data.get('blocked_count', 0),
                    result=result,
                    pass_rate=pass_rate,
                    gerber_file=None,  # Vazio por enquanto
                    operator=user.username,
                    recipe_name=stencil.get('recipe', 'Limpeza Padrão'),
                    report_path=None,
                    defects=[],  # Vazio por enquanto
                    notes=""
                )

                tracker.add_inspection_record(stencil['code'], inspection_record)
                logger.info(f"Registro de inspeção salvo: {stencil['code']}")

            # Mensagem de sucesso
            QMessageBox.information(
                self.main_window,
                "Salvo com Sucesso",
                f"Inspeção do stencil {stencil['code']} foi salva no histórico!\n\n"
                f"Modo: {self._get_mode_title(mode)}\n"
                f"Operador: {user.username}\n"
                f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
            )

            return True

        except Exception as e:
            logger.error(f"Erro ao salvar inspeção: {e}")
            QMessageBox.critical(
                self.main_window,
                "Erro ao Salvar",
                f"Não foi possível salvar a inspeção:\n\n{str(e)}"
            )
            return False

    # =========================================================================
    # DIALOGS DE INSPEÇÃO
    # =========================================================================

    def show_positioning_confirmation(self, stencil: Dict[str, Any]) -> bool:
        """
        Exibe dialog de confirmação de posicionamento.

        Args:
            stencil: Dicionário com dados do stencil

        Returns:
            True se usuário confirmou, False se cancelou
        """
        from consumo_lib.dialogs import ConfirmPositioningDialog

        dialog = ConfirmPositioningDialog(stencil['code'], self.main_window)
        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            checklist_state = dialog.get_checklist_state()
            logger.info(f"Posicionamento confirmado: {stencil['code']}")
            logger.info(f"Checklist: {checklist_state}")
            return True
        else:
            logger.info(f"Posicionamento cancelado: {stencil['code']}")
            return False

    def show_mode_selection(self, stencil: Dict[str, Any]) -> bool:
        """
        Exibe dialog de seleção de modo de inspeção.

        Args:
            stencil: Dicionário com dados do stencil

        Returns:
            True se usuário selecionou modo, False se cancelou
        """
        from consumo_lib.dialogs import ModeSelectionDialog

        dialog = ModeSelectionDialog(stencil['code'], self.main_window)
        dialog.mode_selected.connect(self.on_mode_selected)
        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            selected_mode = dialog.get_selected_mode()
            logger.info(f"Modo de inspeção selecionado: {selected_mode}")
            return True
        else:
            logger.info(f"Seleção de modo cancelada: {stencil['code']}")
            return False

    def on_mode_selected(self, data: Dict[str, Any]):
        """
        Handler: Modo de inspeção selecionado.

        Args:
            data: Dict com "mode" e "stencil_code"
        """
        mode = data.get("mode")
        stencil_code = data.get("stencil_code")

        logger.info(f"Modo selecionado: {mode} para stencil {stencil_code}")

        # Armazena modo selecionado para uso na execução
        self._set_inspection_mode(mode)

    def show_inspection_history(self, stencil_code: str):
        """
        Exibe dialog de histórico do stencil.

        Args:
            stencil_code: Código do stencil
        """
        from consumo_lib.dialogs import InspectionHistoryDialog

        dialog = InspectionHistoryDialog(stencil_code, self.main_window)
        dialog.exec()

    # =========================================================================
    # MÉTODOS AUXILIARES
    # =========================================================================

    def _get_inspection_mode(self) -> str:
        """Retorna o modo de inspeção selecionado."""
        if self.state:
            return self.state.inspection_mode
        return getattr(self.main_window, 'selected_inspection_mode', 'tension')

    def _set_inspection_mode(self, mode: str):
        """Define o modo de inspeção."""
        if self.state:
            self.state.inspection_mode = mode
        else:
            self.main_window.selected_inspection_mode = mode

    def _get_inspection_results(self) -> Dict[str, Any]:
        """Retorna os resultados da inspeção."""
        if self.state:
            return self.state.results
        return getattr(self.main_window, 'inspection_results', {})

    def _set_inspection_results(self, results: Dict[str, Any]):
        """Define os resultados da inspeção."""
        if self.state:
            self.state.results = results
        else:
            self.main_window.inspection_results = results

    def _get_mode_title(self, mode: str) -> str:
        """Retorna título legível do modo."""
        titles = {
            "tension": "Medição de Tensão",
            "inspection": "Inspeção Visual",
            "both": "Completo (Tensão + Visual)"
        }
        return titles.get(mode, "Inspeção")
