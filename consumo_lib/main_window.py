# Standard library
import sys
import os
import time
import logging

# Configure logger
logger = logging.getLogger(__name__)

# Autenticação (NOVO - FASE 1)
from aoi_lib.auth import AuthService
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
    StencilTracker, Stencil, TensionRecord, InspectionRecord
)
from aoi_lib.plc_axis_controller import PLCAxisController
from aoi_lib.config_manager import AOIConfigManager, SettingsDialog
from aoi_lib.fov_calibration import FOVCalibration, CameraFOVConverter, ClickableVideoLabel
from aoi_lib.stencil_inspector import StencilInspector, InspectionThresholds, InspectionResult
from aoi_lib.inspection_result_viewer import InspectionResultWidget

# External
try:
    from grbl_streamer import GrblStreamer
except ImportError:
    # grbl_streamer.py não encontrado - será criado quando necessário
    GrblStreamer = None
    logger.warning("grbl_streamer.py não encontrado - funcionalidade GRBL desabilitada")

try:
    from tools.mosaic_builder import compose_mosaic_from_folder
except ImportError:
    # Fallback para importação legada (para compatibilidade)
    try:
        from mosaic_builder import compose_mosaic_from_folder
    except ImportError:
        compose_mosaic_from_folder = None
        logger.warning("mosaic_builder.py não encontrado - funcionalidade de mosaico desabilitada")

# Consumo lib - barrier packages
from consumo_lib.dialogs import (
    StencilManagerDialog, StencilCreateDialog,
    FOVCalibrationDialog, CrosshairSettingsDialog,
    InspectionSettingsDialog, ReportSettingsDialog, AboutDialog,
    LoginDialog  # NOVO - FASE 1
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

        # NOVO - FASE 1: Autenticação de usuário
        # Exibe dialog de login antes de continuar
        self.auth_service = AuthService()
        if not self.show_login_dialog():
            # Usuário cancelou o login ou fechou o dialog
            logger.info("Login cancelado pelo usuário, fechando aplicação")
            sys.exit(0)

        # Usa SetupCoordinator para orquestrar toda inicialização
        setup_coordinator = SetupCoordinator(AOIControllerApp)
        setup_coordinator.setup(self)

        # Aplica permissões baseadas no role do usuário (NOVO - FASE 2)
        # Usa delay maior aqui pois a UI acaba de ser montada
        QTimer.singleShot(500, self._apply_role_permissions)

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

    # =========================================================================
    # AUTENTICAÇÃO (NOVO - FASE 1)
    # =========================================================================

    def show_login_dialog(self) -> bool:
        """
        Exibe dialog de login e aguarda autenticação.

        Returns:
            True se login foi bem-sucedido, False se cancelado
        """
        login_dialog = LoginDialog(self.auth_service, self)
        result = login_dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            # Login bem-sucedido
            user = self.auth_service.get_current_user()
            logger.info(f"Usuário logado: {user}")

            # Aplica permissões baseadas no role (FASE 2)
            # Isso será chamado novamente após a UI ser construída
            # Mas chamamos aqui também para configurar o estado
            QTimer.singleShot(100, self._apply_role_permissions)

            return True
        else:
            # Usuário cancelou ou fechou o dialog
            return False

    def _apply_role_permissions(self):
        """
        Aplica permissões de acesso baseadas no role do usuário.

        Regras:
        - OPERATOR: Apenas aba "Programas" habilitada
        - ENGINEERING: Todas as abas habilitadas
        - ADMIN: Todas as abas habilitadas
        """
        if not hasattr(self, 'right_panel') or not self.right_panel:
            logger.warning("right_panel ainda não criado, permissões serão aplicadas depois")
            return

        user = self.auth_service.get_current_user()
        if not user:
            logger.warning("Nenhum usuário logado, não aplicando permissões")
            return

        from aoi_lib.auth import UserRole

        if user.role == UserRole.OPERATOR:
            # Operador: Apenas aba "Programas" (TreeViewTab)
            logger.info(f"Aplicando permissões OPERATOR para {user.username}")

            # Desabilita todas as abas exceto "Programas"
            for i in range(self.right_panel.count()):
                tab_text = self.right_panel.tabText(i)
                if "Programas" not in tab_text:
                    self.right_panel.setTabEnabled(i, False)
                    logger.debug(f"Aba desabilitada: {tab_text}")

            # Garante que aba "Programas" esteja habilitada e selecionada
            for i in range(self.right_panel.count()):
                if "Programas" in self.right_panel.tabText(i):
                    self.right_panel.setTabEnabled(i, True)
                    self.right_panel.setCurrentIndex(i)
                    logger.debug(f"Aba habilitada e selecionada: {self.right_panel.tabText(i)}")
                    break

            # Desabilita grupos de conexão e calibração (painel esquerdo)
            if hasattr(self, 'connection_group'):
                self.connection_group.setEnabled(False)
            if hasattr(self, 'calibration_group'):
                self.calibration_group.setEnabled(False)

        elif user.role in [UserRole.ENGINEERING, UserRole.ADMIN]:
            # Engineering/Admin: Todas as abas habilitadas
            logger.info(f"Aplicando permissões {user.role.value.upper()} para {user.username}")

            # Habilita todas as abas
            for i in range(self.right_panel.count()):
                self.right_panel.setTabEnabled(i, True)
                logger.debug(f"Aba habilitada: {self.right_panel.tabText(i)}")

            # Habilita grupos de conexão e calibração
            if hasattr(self, 'connection_group'):
                self.connection_group.setEnabled(True)
            if hasattr(self, 'calibration_group'):
                # Calibração fica oculta mesmo para admin, mas habilitada
                self.calibration_group.setEnabled(True)

    def _on_inspect_requested(self, stencil: dict):
        """
        Handler: Solicitação de inspeção da TreeView

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

    def run_inspection(self, stencil: dict):
        """
        Executa inspeção com tela de progresso

        Args:
            stencil: Dicionário com dados do stencil
        """
        from consumo_lib.dialogs import InspectionProgressDialog
        from consumo_lib.threads import InspectionWorker

        mode = getattr(self, 'selected_inspection_mode', 'tension')

        # Cria dialog de progresso
        progress_dialog = InspectionProgressDialog(
            stencil['code'],
            mode,
            self
        )

        # Cria worker thread
        worker = InspectionWorker(
            stencil['code'],
            mode,
            self
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
            self.inspection_results = progress_dialog.get_results()
            logger.info(f"Resultados da inspeção: {self.inspection_results}")

    def on_inspection_complete(self, success: bool, message: str, stencil: dict):
        """
        Handler: Inspeção completada

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
                self,
                "Erro na Inspeção",
                f"A inspeção não pôde ser concluída:\n\n{message}"
            )

    def show_inspection_results(self, stencil: dict):
        """
        Exibe dialog de resultados da inspeção

        Args:
            stencil: Dicionário com dados do stencil
        """
        from consumo_lib.dialogs import InspectionResultsDialog

        mode = getattr(self, 'selected_inspection_mode', 'tension')
        results = getattr(self, 'inspection_results', {})

        dialog = InspectionResultsDialog(
            stencil['code'],
            mode,
            results,
            self
        )

        dialog.exec()

    def save_inspection_to_history(self, stencil: dict, results: dict, mode: str) -> bool:
        """
        Salva inspeção no histórico do stencil

        Args:
            stencil: Dicionário com dados do stencil
            results: Resultados da inspeção
            mode: Modo executado ("tension", "inspection", "both")

        Returns:
            True se salvou com sucesso, False caso contrário
        """
        from datetime import datetime

        try:
            user = self.auth_service.get_current_user()
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
                self,
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
                self,
                "Erro ao Salvar",
                f"Não foi possível salvar a inspeção:\n\n{str(e)}"
            )
            return False

    def _get_mode_title(self, mode: str) -> str:
        """Retorna título legível do modo"""
        titles = {
            "tension": "Medição de Tensão",
            "inspection": "Inspeção Visual",
            "both": "Completo (Tensão + Visual)"
        }
        return titles.get(mode, "Inspeção")

    def show_inspection_history(self, stencil_code: str):
        """
        Exibe dialog de histórico do stencil

        Args:
            stencil_code: Código do stencil
        """
        from consumo_lib.dialogs import InspectionHistoryDialog

        dialog = InspectionHistoryDialog(stencil_code, self)
        dialog.exec()

    def show_positioning_confirmation(self, stencil: dict) -> bool:
        """
        Exibe dialog de confirmação de posicionamento

        Args:
            stencil: Dicionário com dados do stencil

        Returns:
            True se usuário confirmou, False se cancelou
        """
        from consumo_lib.dialogs import ConfirmPositioningDialog

        dialog = ConfirmPositioningDialog(stencil['code'], self)
        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            checklist_state = dialog.get_checklist_state()
            logger.info(f"Posicionamento confirmado: {stencil['code']}")
            logger.info(f"Checklist: {checklist_state}")
            return True
        else:
            logger.info(f"Posicionamento cancelado: {stencil['code']}")
            return False

    def show_mode_selection(self, stencil: dict) -> bool:
        """
        Exibe dialog de seleção de modo de inspeção

        Args:
            stencil: Dicionário com dados do stencil

        Returns:
            True se usuário selecionou modo, False se cancelou
        """
        from consumo_lib.dialogs import ModeSelectionDialog

        dialog = ModeSelectionDialog(stencil['code'], self)
        dialog.mode_selected.connect(self.on_mode_selected)
        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            selected_mode = dialog.get_selected_mode()
            logger.info(f"Modo de inspeção selecionado: {selected_mode}")
            return True
        else:
            logger.info(f"Seleção de modo cancelada: {stencil['code']}")
            return False

    def on_mode_selected(self, data: dict):
        """
        Handler: Modo de inspeção selecionado

        Args:
            data: Dict com "mode" e "stencil_code"
        """
        mode = data.get("mode")
        stencil_code = data.get("stencil_code")

        logger.info(f"Modo selecionado: {mode} para stencil {stencil_code}")

        # Armazena modo selecionado para uso na FASE 5
        self.selected_inspection_mode = mode

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

        # Garantir que self.cnc_status existe (para código GRBL legado)
        if not hasattr(self, 'cnc_status'):
            self.cnc_status = QLabel("Desconectado")

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

        Atualiza apenas MovementControlWidget (dentro da aba CNC Control).
        Os labels antigos do painel esquerdo foram removidos - posição
        agora é exibida dentro da groupbox Movement Controls.
        """
        # ─────────────────────────────────────────────────────────────────────
        # Atualizar MovementControlWidget (dentro da aba CNC Control)
        # ─────────────────────────────────────────────────────────────────────
        self._update_movement_widget_position()

        # NOTA: PositionManagerController.update_position_display() foi removido
        # pois os labels do painel esquerdo não existem mais.
        # O signal position_updated ainda é emitido por PositionManagerController
        # em outros contextos onde necessário.

    def _update_movement_widget_position(self):
        """
        Atualiza display de posição no MovementControlWidget.

        Obtém posição atual e status do CNC e atualiza os labels dentro
        da groupbox Movement Controls.
        """
        if not hasattr(self, 'right_panel') or not self.right_panel:
            return

        # Acessar primeira aba (CNC Control)
        cnc_tab = self.right_panel.widget(0)
        if not cnc_tab:
            return

        # Verificar se o movimento widget existe
        if not hasattr(cnc_tab, 'movement_widget'):
            return

        try:
            # Obter posição atual do CNC
            pos = self.controller.cnc.get_current_position()

            # Obter status da máquina
            status = getattr(self.controller.cnc, 'machine_status', 'Desconectado')

            # Atualizar widget com posição e status
            cnc_tab.movement_widget.update_position(
                x=pos['x'],
                y=pos['y'],
                z=pos.get('z', 0.0),
                status=status
            )
        except Exception as e:
            logger.debug(f"Erro ao atualizar posição no MovementControlWidget: {e}")
            # Silencioso - pode não estar conectado ainda
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
