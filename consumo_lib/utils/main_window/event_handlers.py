"""
Módulo: event_handlers.py

Gerencia handlers de eventos da MainWindow (AOIControllerApp).

Responsabilidades:
- Handlers de autenticação (on_login_result, apply_role_permissions)
- Handlers de inspeção (on_inspect_requested, on_inspection_complete, on_mode_selected)
- Handlers de sequência (on_sequence_completed, on_sequence_error, on_sequence_image_captured)
- Handlers de conexão (on_connect_btn_clicked)
- Handlers de timer (on_update_timer)

Author: Refactoring (2026-01-14)
"""

import logging
import time
from typing import Dict, Any
from PyQt6.QtWidgets import QMessageBox, QTableWidget, QTableWidgetItem

logger = logging.getLogger(__name__)


class MainWindowEventHandlers:
    """
    Gerencia handlers de eventos da MainWindow.

    Centraliza todos os handlers de eventos que antes estavam na MainWindow,
    facilitando manutenção e teste.

    Attributes:
        main_window: Instância da MainWindow (AOIControllerApp)
        state: MainWindowState para gerenciar estado da aplicação
    """

    def __init__(self, main_window, state=None):
        """
        Inicializa o MainWindowEventHandlers.

        Args:
            main_window: Instância da MainWindow (AOIControllerApp)
            state: MainWindowState (opcional)
        """
        self.main_window = main_window
        self.state = state

    # =========================================================================
    # HANDLERS DE AUTENTICAÇÃO
    # =========================================================================

    def on_login_result(self, success: bool, user=None):
        """
        Handler chamado quando login é completado.

        Args:
            success: True se login foi bem-sucedido
            user: Objeto User (se sucesso)
        """
        if success:
            logger.info(f"Login bem-sucedido: {user}")
            # Aplica permissões após UI ser construída
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(100, self.apply_role_permissions)
        else:
            logger.warning("Login falhou ou foi cancelado")

    def apply_role_permissions(self):
        """
        Aplica permissões de acesso baseadas no role do usuário.

        Delega para MainWindowState se disponível.
        """
        if self.state:
            self.state.apply_role_permissions()
        else:
            logger.warning("MainWindowState não disponível, não aplicando permissões")

    # =========================================================================
    # HANDLERS DE INSPEÇÃO
    # =========================================================================

    def on_inspect_requested(self, stencil: Dict[str, Any]):
        """
        Handler: Solicitação de inspeção da TreeView.

        Fluxo: TreeView → Posicionamento → Modo → Execução

        Args:
            stencil: Dicionário com dados do stencil
        """
        logger.info(f"Solicitação de inspeção: {stencil.get('code', 'N/A')}")

        # Importa workflow de inspeção
        from consumo_lib.utils.main_window.inspection_workflow import MainWindowInspectionWorkflow

        # Cria workflow e executa
        workflow = MainWindowInspectionWorkflow(self.main_window, self.state)
        workflow.execute_inspection_flow(stencil)

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

        mode = getattr(self.main_window, 'selected_inspection_mode', 'tension')
        results = getattr(self.main_window, 'inspection_results', {})

        dialog = InspectionResultsDialog(
            stencil['code'],
            mode,
            results,
            self.main_window
        )

        dialog.exec()

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
        if self.state:
            self.state.inspection_mode = mode
        else:
            self.main_window.selected_inspection_mode = mode

    # =========================================================================
    # HANDLERS DE SEQUÊNCIA
    # =========================================================================

    def on_sequence_completed(self):
        """
        Atualiza estado interno quando sequência completa.

        O service já atualizou a UI, este método apenas atualiza o estado interno.
        """
        if self.state:
            # O service já atualizou is_running, apenas sincroniza
            pass
        else:
            # Fallback para comportamento original
            if hasattr(self.main_window, 'sequence_execution_service') and self.main_window.sequence_execution_service:
                self.main_window.is_running_sequence = self.main_window.sequence_execution_service.is_running

    def on_sequence_error(self, error_message: str):
        """
        Log de erro na sequência.

        O service já tratou o erro, este método apenas loga.

        Args:
            error_message: Mensagem de erro
        """
        logger.error(f"Erro na sequência: {error_message}")

    def on_sequence_image_captured(self, result: Dict[str, Any]):
        """
        Chamado quando uma imagem é capturada durante execução da sequência.

        Atualiza UI com resultado da captura.

        Args:
            result: Dict com "position", "image", "timestamp"
        """
        position = result["position"]
        image = result["image"]
        timestamp = result["timestamp"]

        # Display the image on the existing camera_preview widget
        self.main_window.camera_preview.display_image(image)

        # Add to results table
        row = self.main_window.results_table.rowCount()
        self.main_window.results_table.insertRow(row)
        self.main_window.results_table.setItem(row, 0, QTableWidgetItem(position.name))
        self.main_window.results_table.setItem(
            row,
            1,
            QTableWidgetItem(time.strftime("%H:%M:%S", time.localtime(timestamp)))
        )
        self.main_window.results_table.setItem(row, 2, QTableWidgetItem("Capturado"))

    # =========================================================================
    # HANDLERS DE CONEXÃO
    # =========================================================================

    def on_connect_btn_clicked(self):
        """
        Botão conectar/desconectar clicado.

        Delega para ConnectionManager quando for PLC.
        Para GRBL, chama o método connect_cnc() original.
        """
        from aoi_lib.plc_axis_controller import PLCAxisController

        if isinstance(self.main_window.controller.cnc, PLCAxisController):
            # Delega para ConnectionManager
            self.main_window.connection_mgr.toggle_plc()
        else:
            # Usa implementação original para GRBL
            self.main_window.connect_cnc()

    # =========================================================================
    # HANDLERS DE TIMER
    # =========================================================================

    def on_update_timer(self):
        """
        Handler chamado pelo timer de atualização.

        Atualiza display de posição.
        """
        if self.state:
            self.state.update_position_display()
        else:
            # Fallback
            self.main_window.update_position_display()

    # =========================================================================
    # HANDLERS DE CAPTURA DE IMAGEM
    # =========================================================================

    def on_image_captured(self, image, position_name: str):
        """
        Handle captured image and register position.

        Args:
            image: Imagem capturada (numpy array)
            position_name: Nome da posição
        """
        # Display in image viewer
        self.main_window.image_viewer.display_image(image, f"Image: {position_name}")

        # Get current position
        if not self.main_window.controller.cnc.is_connected:
            QMessageBox.warning(self.main_window, "Error", "CNC not connected")
            return

        current_pos = self.main_window.controller.cnc.get_current_position()

        # Register position with image
        self.main_window.position_registry.add_position(
            position_name,
            current_pos['x'],
            current_pos['y'],
            current_pos['z'],
            image
        )

        self.main_window.statusBar().showMessage(
            f"Position '{position_name}' registered at X:{current_pos['x']:.3f}, Y:{current_pos['y']:.3f}"
        )
