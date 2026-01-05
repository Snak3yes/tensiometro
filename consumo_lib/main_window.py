# Standard library
import sys
import os
import time
import logging

# Configure logger
logger = logging.getLogger(__name__)
import json
import cv2
import numpy as np
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

# PyQt6 - Widgets
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QGroupBox, QGridLayout, QLineEdit,
    QComboBox, QMessageBox, QTabWidget, QSplitter, QTableWidget,
    QTableWidgetItem, QDialog, QProgressDialog
)

# PyQt6 - Core
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSignalBlocker

# PyQt6 - GUI
from PyQt6.QtGui import QPixmap, QImage, QPainter, QColor

# AOI library
from aoi_lib import (
    CNCAOIController, InspectionPosition,
    StencilTracker, Stencil, TensionRecord
)
from aoi_lib.plc_axis_controller import PLCAxisController
from aoi_lib.config_manager import AOIConfigManager, SettingsDialog
from aoi_lib.fov_calibration import FOVCalibration, CameraFOVConverter, ClickableVideoLabel
from aoi_lib.stencil_inspector import StencilInspector, InspectionThresholds, InspectionResult
from aoi_lib.inspection_result_viewer import InspectionResultWidget

# External
from grbl_streamer import GrblStreamer
from mosaic_builder import compose_mosaic_from_folder

# Consumo lib - barrier packages
from consumo_lib.dialogs import (
    StencilManagerDialog, StencilCreateDialog,
    FOVCalibrationDialog, CrosshairSettingsDialog,
    InspectionSettingsDialog, ReportSettingsDialog, AboutDialog
)
from consumo_lib.tabs import (
    CNCControlTab, TensionTab, TrackingTab, InspectionTab, MapTab
)
from consumo_lib.controllers import (
    MapController, CameraSettingsController, CalibrationController,
    InspectionUIController, ReportDialogController, SequenceController,
    FiducialAlignmentController, ConnectionManagerController,
    TensionMeasurementController, DialogManagerController,
    FileIOController, PositionManagerController, RecipeManagerController
)
from consumo_lib.coordinators import SetupCoordinator
from consumo_lib.handlers import KeyboardEventHandler, MenuHandler, GRBLCallbackHandler, SignalAggregator, DialogRouter
from consumo_lib.ui_builders import MainUIBuilder
from consumo_lib.services import SequenceExecutionService, ResourceManager
from consumo_lib.managers import ConnectionManager, RecipeManagerWrapper, StencilManagerWrapper, InspectionManager, ReportManagerWrapper
from consumo_lib.widgets.tension_viz import TensionVisualizationWidget, TensionCanvas
from consumo_lib.widgets.image_viewer import ImageViewerWidget
from consumo_lib.widgets.position_list import PositionListWidget
from consumo_lib.widgets.sequence_control import SequenceControlWidget
from consumo_lib.widgets.position_registry import PositionRegistryWidget
from consumo_lib.widgets.camera_preview import CameraPreviewWidget
from consumo_lib.widgets.movement_control import MovementControlWidget
from consumo_lib.widgets.plc_monitor import PLCMonitorWidget
from consumo_lib.threads.sequence_runner import SequenceRunnerThread
from consumo_lib.threads.map_generator import MapGeneratorThread
from consumo_lib.utils.map_params import MapParams

class AOIControllerApp(QMainWindow):
    def __init__(self):
        """
        Inicializa a aplicação usando SetupCoordinator.

        O SetupCoordinator orquestra toda inicialização de:
        - Configurações e controller principal
        - Managers (recipe, stencil, report, inspection)
        - Coordinators (connection, inspection, tension)
        - Handlers (keyboard, menu, GRBL, dialogs)
        - Controllers (map, camera, calibration, etc.)
        - Services (sequence execution, resource)
        - Interface gráfica
        - Signals
        - Timers e auto-connect
        """
        # Inicialização básica da janela
        super().__init__()

        # Usa SetupCoordinator para orquestrar toda inicialização
        setup_coordinator = SetupCoordinator(AOIControllerApp)
        setup_coordinator.setup(self)

        # Conecta cleanup ao evento de fechamento
        QApplication.instance().aboutToQuit.connect(self._cleanup_resources)

    def __getattr__(self, name):
        """
        Delega chamadas show_* para DialogRouter dinamicamente.

        Isso permite remover 18 métodos wrapper (72 linhas) que apenas
        delegavam para self.dialog_router.*, mantendo a mesma interface.

        Exemplo:
            self.show_recipe_manager() → self.dialog_router.show_recipe_manager()

        Raises:
            AttributeError: Se o atributo não começa com 'show_' ou não existe no router.
        """
        if name.startswith('show_') and hasattr(self, 'dialog_router'):
            # Delega para DialogRouter
            return getattr(self.dialog_router, name)
        # Comportamento padrão para atributos não encontrados
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def _attempt_auto_connect(self):
        """Tenta conexão automática ao PLC e câmera ao iniciar a aplicação."""
        if self.config.get("connections", "auto_connect_camera", default=False):
            # Obtém ID salvo (pode ser int ou string URL)
            raw_id = self.config.get("connections", "last_camera_id", default=0)
            
            # Tenta converter para int se possível (para câmera USB padrão)
            try:
                cam_id = int(raw_id)
                cam_str = str(cam_id)
            except ValueError:
                # É uma URL/String
                cam_id = str(raw_id)
                cam_str = cam_id
            
            # Tenta achar na lista
            idx = self.camera_id_combo.findText(cam_str)
            if idx >= 0:
                self.camera_id_combo.setCurrentIndex(idx)
            else:
                # Se não achou (ex: é uma URL customizada), define o texto diretamente
                self.camera_id_combo.setCurrentText(cam_str)
                
            QTimer.singleShot(500, self.connect_camera)

    def _show_plc_connection_error(self, host: str, port: int, error: str):
        """Exibe mensagem de erro de conexão ao PLC."""
        QMessageBox.information(
            self,
            "CLP Não Conectado",
            f"O CLP (Controlador Lógico Programável) não está conectado.\n\n"
            f"A aplicação iniciará normalmente, porém as funções de controle de movimento "
            f"estarão indisponíveis até que o CLP seja conectado.\n\n"
            f"Detalhes da tentativa de conexão:\n"
            f"• Endereço: {host}:{port}\n"
            f"• Erro: {error}\n\n"
            f"Para conectar o CLP:\n"
            f"1. Verifique se o CLP está ligado e na mesma rede\n"
            f"2. Confirme o endereço IP em 'Ferramentas → Preferências'\n"
            f"3. Use 'Ferramentas → Conexões' para conectar manualmente"
        )

    def on_update_timer(self):
        #logger.debug("Timer fired: atualizando tela de posição da head.")
        self.update_position_display()
        
    def setup_ui(self):
        """
        Configura a UI principal usando UIBuilder.

        O UIBuilder cria todos os widgets, layouts e abas da aplicação.
        """
        ui_builder = MainUIBuilder(self)
        ui_builder.build_ui()
        logger.info("UI criada via MainUIBuilder")

    def setup_menu(self):
        """Configura o menu da aplicação usando MenuHandler."""
        menubar = self.menuBar()

        # Usar MenuHandler para criar todos os menus
        self.menu_handler.create_menus(menubar)

        # Obter referências para actions dinâmicos (para compatibilidade)
        self.current_recipe_action = self.menu_handler.current_recipe_action
        self.current_stencil_action = self.menu_handler.current_stencil_action

        logger.info("Menu configurado via MenuHandler")

    # abre o diálogo de medição de tensão
    def open_stencil_tension_dialog(self):
        """
        Abre diálogo simples de medição de tensão.

        Delega para DialogManagerController.
        """
        if self.dialog_manager_controller is not None:
            self.dialog_manager_controller.open_simple_tension_dialog()
        else:
            logger.error("DialogManagerController não está disponível")
            if not self.controller.cnc.is_connected:
                QMessageBox.warning(self, "Aviso", "Conecte a CNC antes de medir a tensão do stencil.")
                return
            from aoi_lib.stencil_tension import StencilTensionDialog
            dlg = StencilTensionDialog(self, self.controller.cnc)
            dlg.exec()

    # =========================================================================
    # GERENCIAMENTO DE RECEITAS
    # =========================================================================

    def apply_recipe_to_capture(self):
        """Aplica configurações de captura da receita ao diálogo de mapa (delega para RecipeManagerController)."""
        if self.recipe_manager_controller is None:
            logger.error("RecipeManager não está disponível")
            return

        # Prepara widgets de mapa de forma compacta
        map_widgets = {k: v for k, v in {
            'map_step_x_edit': getattr(self, 'map_step_x_edit', None),
            'map_step_y_edit': getattr(self, 'map_step_y_edit', None),
            'spin_capture_delay': getattr(self, 'spin_capture_delay', None)
        }.items() if v is not None}

        self.recipe_manager_controller.apply_recipe_to_capture(self.current_recipe, map_widgets or None)

    def apply_recipe_to_tension(self):
        """Aplica configurações de tensão da receita ao diálogo de medição (delega para RecipeManagerController)."""
        if self.recipe_manager_controller is None:
            logger.error("RecipeManager não está disponível")
            return
        self.recipe_manager_controller.apply_recipe_to_tension(self.current_recipe)

    def _run_tension_measurement(self):
        """
        Executa medição de tensão para o stencil selecionado.

        Delega para TensionMeasurementController.
        """
        if self.tension_measurement_controller is not None:
            self.tension_measurement_controller.run_measurement(
                self.current_stencil,
                self.current_recipe
            )
        else:
            logger.error("TensionMeasurementController não está disponível")
            QMessageBox.warning(
                self,
                "Erro",
                "TensionMeasurementController não está disponível"
            )

    def _save_tension_to_history(self, tension_dialog):
        """
        Salva resultado da medição de tensão no histórico do stencil.

        Delega para TensionMeasurementController.

        Args:
            tension_dialog: Diálogo de tensão com os dados da medição
        """
        if self.tension_measurement_controller is not None:
            self.tension_measurement_controller.save_measurement(
                self.current_stencil,
                self.current_recipe,
                tension_dialog
            )
        else:
            logger.error("TensionMeasurementController não está disponível")

    def on_image_captured(self, image, position_name):
        """Handle captured image and register position"""
        # Display in image viewer
        self.image_viewer.display_image(image, f"Image: {position_name}")
        
        # Get current position
        if not self.controller.cnc.is_connected:
            QMessageBox.warning(self, "Error", "CNC not connected")
            return
            
        current_pos = self.controller.cnc.get_current_position()
        
        # Register position with image
        self.position_registry.add_position(
            position_name,
            current_pos['x'],
            current_pos['y'],
            current_pos['z'],
            image
        )
        
        self.statusBar().showMessage(f"Position '{position_name}' registered at X:{current_pos['x']:.3f}, Y:{current_pos['y']:.3f}")

    def create_sequence_from_registry(self):
        """
        Cria uma sequência a partir de posições registradas.

        Delega para SequenceExecutionService.
        """
        if self.sequence_execution_service is None:
            logger.error("SequenceExecutionService não está disponível")
            return

        sequence = self.sequence_execution_service.create_sequence_from_registry(
            self.position_registry,
            self.sequence_widget,
            self.position_list_widget
        )

        if sequence:
            self.current_sequence = sequence

    def load_gcode(self):
        """Carrega sequência de arquivo G-CODE (delega para FileIOController)."""
        if self.file_io_controller is None:
            logger.error("FileIO não está disponível")
            return
        self.file_io_controller.load_gcode()

    def save_gcode(self):
        """Salva sequência atual como arquivo G-CODE (delega para FileIOController)."""
        if self.file_io_controller is None:
            logger.error("FileIO não está disponível")
            return
        self.file_io_controller.save_gcode(self.current_sequence)

    def refresh_ports(self):
        """
        Atualiza a lista de portas seriais disponíveis.

        Delega para ConnectionManager.
        """
        self.connection_mgr.refresh_serial_ports(self.cnc_port_combo)

    def _apply_plc_ui_settings(self):
        """
        Atualiza IP/porta do PLC vindos da UI e persiste no config.

        Delega para ConnectionManagerController.
        """
        if self.connection_manager_controller is not None:
            self.connection_manager_controller.apply_plc_ui_settings(
                self.plc_host_input,
                self.plc_port_input
            )
        else:
            logger.error("ConnectionManagerController não está disponível")

    def connect_cnc(self):
        """
        Conecta/desconecta à máquina CNC.

        Delega para ConnectionManager (tanto PLC quanto GRBL).
        """
        # Se for PLCAxisController, delega para ConnectionManager
        if isinstance(self.controller.cnc, PLCAxisController):
            self.connection_mgr.toggle_plc()
            return

        # Para GRBL, verifica se está conectado e alterna
        if hasattr(self.controller.cnc, 'grbl') and self.controller.cnc.grbl:
            # Desconectar
            self.connection_mgr.disconnect_grbl(
                self.connect_cnc_btn,
                self.cnc_status,
                self.statusBar(),
                self
            )
        else:
            # Conectar
            port = self.cnc_port_combo.currentText()
            self.connection_mgr.connect_grbl(
                port,
                self.connect_cnc_btn,
                self.cnc_status,
                self.statusBar(),
                self.grbl_callback_handler,
                self
            )

    # =========================================================================
    # HANDLERS DO CONNECTIONMANAGER
    # =========================================================================

    def _on_connect_btn_clicked(self):
        """
        Botão conectar/desconectar clicado.

        Delega para ConnectionManager quando for PLC.
        Para GRBL, chama o método connect_cnc() original.
        """
        if isinstance(self.controller.cnc, PLCAxisController):
            # Delega para ConnectionManager
            self.connection_mgr.toggle_plc()
        else:
            # Usa implementação original para GRBL
            self.connect_cnc()

    def connect_camera(self):
        """
        Conecta à câmera.

        Delega para ConnectionManagerController.
        """
        if self.connection_manager_controller is not None:
            self.connection_manager_controller.connect_camera(
                self.camera_id_combo,
                self.connect_camera_btn
            )
        else:
            logger.error("ConnectionManagerController não está disponível")

    def test_camera(self):
        """
        Testa a captura de imagem da câmera.

        Delega para ConnectionManagerController.
        """
        if self.connection_manager_controller is not None:
            self.connection_manager_controller.test_camera()
        else:
            logger.error("ConnectionManagerController não está disponível")
            
    def update_position_display(self):
        """
        Atualiza a exibição da posição atual (WPos calculada).

        Delega para PositionManagerController.
        """
        if self.position_manager_controller is not None:
            # Obtém labels Z e CNC status opcionalmente
            z_label = self.z_position if hasattr(self, "z_position") else None
            self.position_manager_controller.update_position_display(
                self.x_position,
                self.y_position,
                z_position_label=z_label,
                cnc_status_label=self.cnc_status
            )
        else:
            logger.error("PositionManager não está disponível")
            return
    def add_current_position(self):
        """
        Adiciona a posição atual à lista.

        Delega para PositionManagerController.
        """
        if self.position_manager_controller is not None:
            self.position_manager_controller.add_current_position()
        else:
            logger.error("PositionManager não está disponível")
            return
    def remove_position(self):
        """
        Remove a posição selecionada.

        Delega para PositionManagerController.
        """
        if self.position_manager_controller is not None:
            self.position_manager_controller.remove_position()
        else:
            logger.error("PositionManager não está disponível")
            return
    def on_position_selected(self, position):
        """
        Manipula a seleção de uma posição.

        Delega para PositionManagerController.
        """
        if self.position_manager_controller is not None:
            self.position_manager_controller.on_position_selected(position)
        else:
            logger.error("PositionManager não está disponível")
            return
    def create_sequence(self):
        """
        Cria uma nova sequência com as posições atuais.

        Delega para PositionManagerController.
        """
        if self.position_manager_controller is not None:
            # Prepara referência mutable para current_sequence
            current_sequence_ref = [self.current_sequence]

            self.position_manager_controller.create_sequence(
                self.sequence_widget.sequence_name,
                self.sequence_widget.sequence_status,
                current_sequence_ref
            )

            # Atualiza self.current_sequence com o resultado
            self.current_sequence = current_sequence_ref[0]
        else:
            logger.error("PositionManager não está disponível")
            return
    def run_sequence(self):
        """
        Executa a sequência atual.

        Delega para SequenceExecutionService.
        """
        if self.sequence_execution_service is None:
            logger.error("SequenceExecutionService não está disponível")
            return

        self.sequence_execution_service.run_sequence(
            self.current_sequence,
            self.movement_widget,
            self.sequence_widget,
            self.results_table
        )

    def on_sequence_image_captured(self, result):
        """
        Chamado quando uma imagem é capturada durante execução da sequência.

        Atualiza UI com resultado da captura (delegação de responsabilidade do service).
        """
        position = result["position"]
        image = result["image"]
        timestamp = result["timestamp"]

        # Display the image on the existing camera_preview widget
        self.camera_preview.display_image(image)

        # Add to results table
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        self.results_table.setItem(row, 0, QTableWidgetItem(position.name))
        self.results_table.setItem(row, 1, QTableWidgetItem(time.strftime("%H:%M:%S", time.localtime(timestamp))))
        self.results_table.setItem(row, 2, QTableWidgetItem("Capturado"))
            
    def stop_sequence(self):
        """
        Para a execução da sequência atual.

        Delega para SequenceExecutionService.
        """
        if self.sequence_execution_service is None:
            logger.error("SequenceExecutionService não está disponível")
            return

        self.sequence_execution_service.stop_sequence(self.sequence_widget)

    def on_sequence_completed(self):
        """Atualiza estado interno quando sequência completa (service já atualizou UI)."""
        if hasattr(self, 'sequence_execution_service') and self.sequence_execution_service:
            self.is_running_sequence = self.sequence_execution_service.is_running

    def on_sequence_error(self, error_message):
        """Log de erro na sequência (service já tratou o erro)."""
        logger.error(f"Erro na sequência: {error_message}")

    def save_program(self):
        """Salva programa de inspeção atual (delega para FileIOController)."""
        if self.file_io_controller is None:
            logger.error("FileIO não está disponível")
            return
        self.file_io_controller.save_program(self.current_sequence)

    def load_program(self):
        """Carrega programa de inspeção salvo (delega para FileIOController)."""
        if self.file_io_controller is None:
            logger.error("FileIO não está disponível")
            return
        self.file_io_controller.load_program()

    def _cleanup_resources(self):
        """
        Para tudo que possa manter o Qt vivo após o fechamento.

        Delega para ResourceManager.
        """
        if self.resource_manager is None:
            logger.error("ResourceManager não está disponível")
            return

        self.resource_manager.cleanup_all(self)

    # closeEvent agora só dispara a limpeza
    def closeEvent(self, event):
        self._cleanup_resources()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AOIControllerApp()
    window.show()
    sys.exit(app.exec())
