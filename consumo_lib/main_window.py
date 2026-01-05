import sys
import cv2
import os
import time
from pathlib import Path
from typing import Optional

# ===== FIX IMPORT PATH =====
# Garante que o diretório raiz do projeto esteja no sys.path
# Isso permite que o arquivo seja executado diretamente ou como módulo
_current_file = Path(__file__).resolve()
_root_dir = _current_file.parent.parent  # Sobe de consumo_lib/ para raiz
if str(_root_dir) not in sys.path:
    sys.path.insert(0, str(_root_dir))
# ===========================

import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QGroupBox,
                             QGridLayout, QLineEdit, QFormLayout,
                             QComboBox, QListWidget, QCheckBox, QListWidgetItem, 
                             QFileDialog, QMessageBox, QTabWidget, QSizePolicy,
                             QSplitter, QFrame, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QDialog, QInputDialog,
                             QProgressDialog, QDoubleSpinBox, QSpinBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QEvent, QRectF, QPointF, QSignalBlocker
from PyQt6.QtGui import (QPixmap, QImage, QFont, QAction, QDoubleValidator,
                         QPainter, QColor, QPen, QBrush, QIntValidator)

from aoi_lib import CNCAOIController, InspectionPosition
from aoi_lib.plc_axis_controller import PLCAxisController
from grbl_streamer import GrblStreamer
from aoi_lib.utils.move_task import MoveTaskThread
from aoi_lib.config_manager import AOIConfigManager, SettingsDialog
from dataclasses import dataclass
from aoi_lib.stencil_tension import StencilTensionDialog
from aoi_lib.fov_calibration import (
    FOVCalibration, CameraFOVConverter, FOVCalibrationDialog, ClickableVideoLabel
)
from aoi_lib.stencil_tracker import StencilTracker, Stencil, TensionRecord
from aoi_lib.stencil_tracker_ui import (
    StencilIdentificationWidget,
    StencilManagerDialog, StencilCreateDialog
)
from aoi_lib.fiducial_alignment_widget import FiducialAlignmentWidget
from aoi_lib.report_generator import ReportGenerator, ReportConfig
from consumo_lib.dialogs import (
    ReportSettingsDialog,
    InspectionSettingsDialog,
    FOVCalibrationDialog,
    CrosshairSettingsDialog,
    AboutDialog
)
from aoi_lib.stencil_inspector import StencilInspector, InspectionThresholds, InspectionResult
from aoi_lib.inspection_result_viewer import InspectionResultWidget
import logging
import json
from mosaic_builder import compose_mosaic_from_folder

# Imports de widgets movidos para o pacote consumo_lib
from consumo_lib.widgets.tension_viz import TensionVisualizationWidget, TensionCanvas
from consumo_lib.widgets.image_viewer import ImageViewerWidget
from consumo_lib.widgets.position_list import PositionListWidget
from consumo_lib.widgets.sequence_control import SequenceControlWidget
from consumo_lib.widgets.position_registry import PositionRegistryWidget
from consumo_lib.widgets.camera_preview import CameraPreviewWidget
from consumo_lib.widgets.movement_control import MovementControlWidget
from consumo_lib.widgets.plc_monitor import PLCMonitorWidget
from consumo_lib.widgets.preview_suspender import _PreviewSuspender
from consumo_lib.threads.sequence_runner import SequenceRunnerThread
from consumo_lib.threads.map_generator import MapGeneratorThread
from consumo_lib.utils.map_params import MapParams
from consumo_lib.managers import ConnectionManager, RecipeManagerWrapper, StencilManagerWrapper, InspectionManager, ReportManagerWrapper
from consumo_lib.coordinators import ConnectionCoordinator, InspectionCoordinator, TensionCoordinator
from consumo_lib.handlers import KeyboardEventHandler, MenuHandler

# Imports das novas abas semânticas
from consumo_lib.tabs import (
    CNCControlTab,
    TensionTab,
    TrackingTab,
    InspectionTab,
    MapTab
)

# Imports dos novos controllers
from consumo_lib.controllers import (
    MapController,
    CameraSettingsController,
    CalibrationController
)

logger = logging.getLogger("consumo_lib")
logger.setLevel(logging.DEBUG)
# Se necessário, adicione um handler:
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

# Pasta padrão para programas de captura de mapa
MAP_PROGRAMS_FOLDER = Path(__file__).parent / "map_programs"

class AOIControllerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Controle de Inspeção Óptica Automatizada")
        self.setGeometry(100, 100, 1200, 800)
        
        # Carrega configurações do usuário
        self.config = AOIConfigManager()
        
        # Inicializa o controlador AOI usando CLP (Modbus TCP),
        # mas sem conectar automaticamente (conexão será tentada depois)
        plc_host = self.config.get("connections", "plc_host", default="192.168.1.5")
        plc_port = self.config.get("connections", "plc_port", default=502)
        # Inicializa o controlador com PLC mas sem conectar automaticamente
        logger.debug("Inicializando CNCAOIController com PLCAxisController (sem conexão automática)")
        self.controller = CNCAOIController(
            plc_host=plc_host,
            plc_port=plc_port,
            auto_connect=False  # Não conecta automaticamente - permite que a app inicie sem CLP
        )
        logger.debug("CNCAOIController inicializado; backend = %s",
                     type(self.controller.cnc).__name__)

        # =========== COORDENADOR DE CONEXÕES ===========
        self.connection_coordinator = ConnectionCoordinator(self.controller, self.config)
        # Conectar signals do ConnectionCoordinator (compatibilidade com código existente)
        self.connection_coordinator.plc_connected.connect(self._on_plc_connected)
        self.connection_coordinator.plc_disconnected.connect(self._on_plc_disconnected)
        self.connection_coordinator.plc_connection_error.connect(self._on_plc_error)

        # Propriedade para compatibilidade com código existente
        self.connection_mgr = self.connection_coordinator

        self.current_sequence = None
        self.is_running_sequence = False
        
        # =========== SISTEMA DE RECEITAS ===========
        self.recipe_manager_wrapper = RecipeManagerWrapper(parent=self)
        # Conectar signals do RecipeManagerWrapper
        self.recipe_manager_wrapper.recipe_loaded.connect(self._on_recipe_loaded)
        self.recipe_manager_wrapper.recipe_created.connect(self._on_recipe_created)
        self.recipe_manager_wrapper.recipe_applied_to_capture.connect(self._on_recipe_applied_to_capture)
        self.recipe_manager_wrapper.recipe_applied_to_tension.connect(self._on_recipe_applied_to_tension)
        self.recipe_manager_wrapper.recipe_error.connect(self._on_recipe_error)
        # Propriedade para compatibilidade com código existente
        self.recipe_manager = self.recipe_manager_wrapper.recipe_manager
        self.current_recipe = None  # Receita atualmente carregada

        # =========== SISTEMA DE RASTREABILIDADE ===========
        self.stencil_manager_wrapper = StencilManagerWrapper(parent=self)
        # Conectar signals do StencilManagerWrapper
        self.stencil_manager_wrapper.stencil_selected.connect(self._on_stencil_selected)
        self.stencil_manager_wrapper.stencil_cleared.connect(self._on_stencil_cleared)
        self.stencil_manager_wrapper.tension_record_added.connect(self._on_tension_record_added)
        self.stencil_manager_wrapper.degradation_alert.connect(self._on_degradation_alert)
        self.stencil_manager_wrapper.stencil_error.connect(self._on_stencil_error)
        # Propriedade para compatibilidade com código existente
        self.stencil_tracker = self.stencil_manager_wrapper.stencil_tracker
        self.current_stencil = None  # Stencil atualmente selecionado


        # =========== SISTEMA DE RELATÓRIOS ===========
        self.report_manager_wrapper = ReportManagerWrapper(self.config, parent=self)
        # Conectar signals do ReportManagerWrapper
        self.report_manager_wrapper.report_generated.connect(self._on_report_generated)
        self.report_manager_wrapper.report_failed.connect(self._on_report_failed)
        self.report_manager_wrapper.config_changed.connect(self._on_report_config_changed)
        # Propriedades para compatibilidade com código existente
        self.report_config = self.report_manager_wrapper.get_config()
        self.report_generator = self.report_manager_wrapper.get_generator()


        # =========== SISTEMA DE INSPEÇÃO VISUAL ===========
        self.inspection_manager = InspectionManager(self.config, parent=self)
        # Conectar signals do InspectionManager
        self.inspection_manager.inspection_completed.connect(self._on_inspection_completed)
        self.inspection_manager.inspection_failed.connect(self._on_inspection_failed)
        self.inspection_manager.thresholds_changed.connect(self._on_thresholds_changed)
        # Propriedades para compatibilidade com código existente
        self.inspection_thresholds = self.inspection_manager.get_thresholds()
        self.stencil_inspector = self.inspection_manager.get_inspector()
        self._last_inspection_result = None
        self._last_inspection_overlay = None

        # =========== COORDENADOR DE INSPEÇÃO ===========
        self.inspection_coordinator = InspectionCoordinator(
            self.controller,
            self.config,
            self.inspection_manager
        )
        # Conectar signals do InspectionCoordinator
        self.inspection_coordinator.step_changed.connect(self._on_inspection_step_changed)
        self.inspection_coordinator.progress_updated.connect(self._on_inspection_progress)
        self.inspection_coordinator.gerber_loaded.connect(self._on_gerber_loaded)
        self.inspection_coordinator.fiducials_captured.connect(self._on_fiducials_captured)
        self.inspection_coordinator.alignment_completed.connect(self._on_alignment_completed)
        self.inspection_coordinator.image_captured.connect(self._on_inspection_image_captured)
        self.inspection_coordinator.analysis_completed.connect(self._on_inspection_analysis_completed)
        self.inspection_coordinator.inspection_completed.connect(self._on_inspection_workflow_completed)
        self.inspection_coordinator.inspection_failed.connect(self._on_inspection_workflow_failed)

        # =========== COORDENADOR DE TENSÃO ===========
        self.tension_coordinator = TensionCoordinator(self.controller, self.config)
        # Conectar signals do TensionCoordinator
        self.tension_coordinator.step_changed.connect(self._on_tension_step_changed)
        self.tension_coordinator.progress_updated.connect(self._on_tension_progress)
        self.tension_coordinator.grid_generated.connect(self._on_tension_grid_generated)
        self.tension_coordinator.point_started.connect(self._on_tension_point_started)
        self.tension_coordinator.point_completed.connect(self._on_tension_point_completed)
        self.tension_coordinator.measurement_taken.connect(self._on_tension_measurement_taken)
        self.tension_coordinator.all_measurements_completed.connect(self._on_tension_all_completed)
        self.tension_coordinator.heatmap_generated.connect(self._on_tension_heatmap_generated)
        self.tension_coordinator.measurement_completed.connect(self._on_tension_measurement_completed)
        self.tension_coordinator.measurement_failed.connect(self._on_tension_measurement_failed)

        # =========== HANDLERS DE UI ===========
        # KeyboardEventHandler (será configurado após setup_ui, quando movement_widget estiver disponível)
        self.keyboard_handler = KeyboardEventHandler()
        # MenuHandler (será configurado em setup_menu)
        self.menu_handler = MenuHandler(main_window=self)

        # =========== CONTROLLERS ===========
        try:
            self.map_controller = MapController(self.controller, self.config, self)
            logger.debug("MapController criado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao criar MapController: {e}")
            self.map_controller = None

        try:
            self.camera_settings_controller = CameraSettingsController(self.controller, self.config, self)
            logger.debug("CameraSettingsController criado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao criar CameraSettingsController: {e}")
            self.camera_settings_controller = None

        try:
            self.calibration_controller = CalibrationController(self.controller, self.config, self)
            logger.debug("CalibrationController criado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao criar CalibrationController: {e}")
            self.calibration_controller = None

        # Conectar signals do MapController
        if self.map_controller is not None:
            self.map_controller.program_saved.connect(self._on_map_program_saved)
            self.map_controller.program_loaded.connect(self._on_map_program_loaded)
            self.map_controller.program_deleted.connect(self._on_map_program_deleted)
            self.map_controller.map_generated.connect(self._on_map_generated)
            self.map_controller.map_progress.connect(self._on_map_progress)
            self.map_controller.map_error.connect(self._on_map_error)

        # Conectar signals do CameraSettingsController
        if self.camera_settings_controller is not None:
            self.camera_settings_controller.settings_changed.connect(self._on_camera_settings_changed)
            self.camera_settings_controller.settings_applied.connect(self._on_camera_settings_applied)
            self.camera_settings_controller.settings_saved.connect(self._on_camera_settings_saved)
            self.camera_settings_controller.settings_loaded.connect(self._on_camera_settings_loaded)

        # Conectar signals do CalibrationController
        if self.calibration_controller is not None:
            self.calibration_controller.calibration_applied.connect(self._on_calibration_applied)
            self.calibration_controller.calibration_completed.connect(self._on_calibration_completed)
            self.calibration_controller.test_completed.connect(self._on_calibration_test_completed)

        # Variável para armazenar o último valor de posição (para comparação)
        self.last_logged_position = None

        # Armazenar o offset do sistema de coordenadas de trabalho (WCS) ativo (ex: G54)
        self.current_wcs_offset = {'x': 0.0, 'y': 0.0, 'z': 0.0} # Inicializa o offset WCS padrão (G54)

        # Armazenar a última Posição da Máquina (MPos) conhecida
        self.current_mpos = {'x': 0.0, 'y': 0.0, 'z': 0.0} 
        # Armazenar o Sistema de Coordenadas de Trabalho (WCS) ativo (ex: "G54")
        self.active_wcs = "G54" # Assume G54 como padrão inicial
        # Mapeamento de WCS para número P do G10
        self.wcs_to_p = {"G54": 1, "G55": 2, "G56": 3, "G57": 4, "G58": 5, "G59": 6}
        
        # -------- Carrega configurações de câmera salvas --------
        self._camera_mirror_x = self.config.get("camera", "mirror_x", default=False)
        self._camera_mirror_y = self.config.get("camera", "mirror_y", default=False)
        logger.debug(f"Configurações de câmera carregadas: mirror_x={self._camera_mirror_x}, mirror_y={self._camera_mirror_y}")
        
        # Configuração da interface
        self.setup_ui()

        # Configurar KeyboardEventHandler (após setup_ui, quando movement_widget existe)
        # O movement_widget está dentro da CNCControlTab
        if hasattr(self, 'cnc_tab') and hasattr(self.cnc_tab, 'movement_widget'):
            self.keyboard_handler.set_movement_widget(self.cnc_tab.movement_widget)
            # Callback para verificar se keyboard control está habilitado
            self.keyboard_handler.set_enable_control_callback(
                lambda: self.cnc_tab.movement_widget.keyboard_control_checkbox.isChecked()
                if hasattr(self.cnc_tab.movement_widget, 'keyboard_control_checkbox')
                else False
            )
            logger.debug("KeyboardEventHandler configurado com movement_widget")

        # Configuração do menu
        self.setup_menu()

        # -------- Painel de conexão inicialmente oculto -------
        self.connection_group.setVisible(False)

        # -------- Auto-connect se preferido --------------------

        # Tenta auto-connect se configurado
        logger.debug("Verificando auto-connect...")
        self.connection_coordinator.attempt_auto_connect()

        logger.debug(
            "Verificando conexão PLC no arranque; backend=%s, conectado=%s",
            type(self.controller.cnc).__name__,
            getattr(self.controller.cnc, 'is_connected', False)
        )
        if isinstance(self.controller.cnc, PLCAxisController):
            # Estado inicial - aguardando tentativa de conexão automática
            self.connect_cnc_btn.setText("Conectar PLC")
            self.cnc_status.setText("Iniciando...")
            self.statusBar().showMessage("Iniciando aplicação - conexão automática ao PLC em breve...")
            logger.info("Aplicação iniciada. Tentativa de conexão automática ao PLC agendada.")
        
        # Auto-connect apenas após a interface estar pronta
        QTimer.singleShot(500, self._attempt_auto_connect)

        # Timer para atualizar a posição – agora conectamos a um método que loga a ação 
        self.update_timer = QTimer(self) 
        self.update_timer.timeout.connect(self.on_update_timer) 
        self.update_timer.start(1000) # Atualiza a cada 1000ms        

        # Capturar eventos de teclado para movimentação via KeyboardEventHandler
        QApplication.instance().installEventFilter(self.keyboard_handler)
        logger.debug("KeyboardEventHandler instalado como eventFilter global")

        # chama cleanup se o Qt encerrar por outros caminhos
        QApplication.instance().aboutToQuit.connect(self._cleanup_resources)

    #   Auto-connect com base no JSON de prefs
    def _attempt_auto_connect(self):
        """Tenta conexão automática ao PLC e câmera ao iniciar a aplicação."""

        # ========== CONEXÃO AUTOMÁTICA À CÂMERA ==========
        # ========== CONEXÃO AUTOMÁTICA À CÂMERA ==========
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
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        
        # Grupo de conexão (oculto por padrão; mostrado via menu)
        self.connection_group = QGroupBox("Conexão")
        connection_layout = QGridLayout()

        # PLC (Modbus TCP)
        connection_layout.addWidget(QLabel("IP PLC:"), 0, 0)
        self.plc_host_input = QLineEdit(self.config.get("connections", "plc_host", default="192.168.1.5"))
        connection_layout.addWidget(self.plc_host_input, 0, 1)

        connection_layout.addWidget(QLabel("Porta:"), 0, 2)
        self.plc_port_input = QSpinBox()
        self.plc_port_input.setRange(1, 65535)
        self.plc_port_input.setValue(self.config.get("connections", "plc_port", default=502))
        self.plc_port_input.setFixedWidth(100)
        connection_layout.addWidget(self.plc_port_input, 0, 3)

        btn_label = "Conectar PLC" if isinstance(self.controller.cnc, PLCAxisController) else "Conectar CNC"
        self.connect_cnc_btn = QPushButton(btn_label)
        self.connect_cnc_btn.clicked.connect(self._on_connect_btn_clicked)
        connection_layout.addWidget(self.connect_cnc_btn, 0, 4)

        # CNC Connection (serial legacy)
        connection_layout.addWidget(QLabel("Porta CNC:"), 1, 0)
        self.cnc_port_combo = QComboBox()
        self.refresh_ports()
        connection_layout.addWidget(self.cnc_port_combo, 1, 1)

        # Camera connection
        connection_layout.addWidget(QLabel("Câmera ID/URL:"), 2, 0)
        self.camera_id_combo = QComboBox()
        self.camera_id_combo.setEditable(True)
        self.camera_id_combo.setToolTip("Selecione ID (0,1...) ou digite URL (http://...)")
        self.camera_id_combo.addItems(["0", "1", "2", "3"])
        connection_layout.addWidget(self.camera_id_combo, 2, 1)

        self.connect_camera_btn = QPushButton("Conectar Câmera")
        self.connect_camera_btn.clicked.connect(self.connect_camera)
        connection_layout.addWidget(self.connect_camera_btn, 2, 2)

        # Refresh ports button
        self.refresh_ports_btn = QPushButton("Atualizar Portas")
        self.refresh_ports_btn.clicked.connect(self.refresh_ports)
        connection_layout.addWidget(self.refresh_ports_btn, 1, 3)

        # Test camera button
        self.test_camera_btn = QPushButton("Testar Câmera")
        self.test_camera_btn.clicked.connect(self.test_camera)
        connection_layout.addWidget(self.test_camera_btn, 2, 3)

        self.connection_group.setLayout(connection_layout)
        main_layout.addWidget(self.connection_group)

        # Grupo de Calibração de Movimento ------
        calibration_group = QGroupBox("Calibração de Movimento")
        calibration_layout = QHBoxLayout()

        # Campos permanecem criados porque são usados pela
        # lógica de calibração, porém o grupo ficará oculto.
        self.pulses_input = QLineEdit(str(
            self.config.get("calibration", "pulses_per_rev", default=400)
        ))
        self.fuso_input = QLineEdit(str(
            self.config.get("calibration", "fuso_pitch", default=5)
        ))
        self.apply_calibration_btn = QPushButton("Aplicar Calibração")
        # Conecta ao CalibrationController
        self.apply_calibration_btn.clicked.connect(
            lambda: self.calibration_controller.show_dialog(
                self,
                self.pulses_per_rev_input.text(),
                self.fuso_input.text()
            ) if self.calibration_controller is not None else None
        )

        # (os widgets não são adicionados ao layout visual)
        calibration_group.setLayout(calibration_layout)
        calibration_group.setVisible(False)       # ← esconde
        main_layout.addWidget(calibration_group)  # mantém no DOM para uso interno
        
        # Splitter para dividir a interface em painéis
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Painel esquerdo: controles e lista de posições
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Informações de posição
        position_group = QGroupBox("Posição Atual")
        position_layout = QGridLayout()

        # Exibe os valores X, Y, Z e status
        position_layout.addWidget(QLabel("X:"), 0, 0)
        self.x_position = QLabel("0.000 mm")
        position_layout.addWidget(self.x_position, 0, 1)
        position_layout.addWidget(QLabel("Y:"), 1, 0)
        self.y_position = QLabel("0.000 mm")
        position_layout.addWidget(self.y_position, 1, 1)
        position_layout.addWidget(QLabel("Z:"), 2, 0)
        self.z_position = QLabel("0.000 mm")
        position_layout.addWidget(self.z_position, 2, 1)
        position_layout.addWidget(QLabel("Status:"), 3, 0)
        self.cnc_status = QLabel("Desconectado")
        position_layout.addWidget(self.cnc_status, 3, 1)

        position_group.setLayout(position_layout)
        left_layout.addWidget(position_group)
        
        # Widget de lista de posições
        self.position_list_widget = PositionListWidget()
        self.position_list_widget.add_position_btn.clicked.connect(self.add_current_position)
        self.position_list_widget.remove_position_btn.clicked.connect(self.remove_position)
        self.position_list_widget.position_selected.connect(self.on_position_selected)
        
        left_layout.addWidget(self.position_list_widget)
        
        # Controle de sequência
        self.sequence_widget = SequenceControlWidget()
        self.sequence_widget.create_sequence_btn.clicked.connect(self.create_sequence)
        self.sequence_widget.run_sequence_btn.clicked.connect(self.run_sequence)
        self.sequence_widget.stop_sequence_btn.clicked.connect(self.stop_sequence)
        self.sequence_widget.save_btn.clicked.connect(self.save_program)
        self.sequence_widget.load_btn.clicked.connect(self.load_program)
        self.sequence_widget.save_gcode_btn.clicked.connect(self.save_gcode)
        self.sequence_widget.load_gcode_btn.clicked.connect(self.load_gcode)
        
        left_layout.addWidget(self.sequence_widget)

        # Table to display each step/result of the executed sequence
        self.results_table = QTableWidget(0, 3)
        self.results_table.setHorizontalHeaderLabels(["Posição", "Horário", "Status"])
        # Make columns stretch to fill available space
        self.results_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        left_layout.addWidget(self.results_table)
        
        # Painel direito: abas semânticas
        right_panel = QTabWidget()
        # guardamos para habilitar/desabilitar abas depois
        self.right_panel = right_panel

        # Aba 1: Câmera & Movimento
        self.cnc_control_tab = CNCControlTab(self.controller, self.config, parent=self)
        self.cnc_control_tab.image_captured.connect(self.on_image_captured)
        # Expose widgets internos para compatibilidade
        self.camera_preview = self.cnc_control_tab.camera_preview
        self.movement_widget = self.cnc_control_tab.movement_widget
        right_panel.addTab(self.cnc_control_tab, "Câmera & Movimento")

        # Aba 2: Monitor CLP (mantida como estava)
        self.plc_monitor = PLCMonitorWidget(self.controller)
        right_panel.addTab(self.plc_monitor, "Monitor CLP")

        # Aba 3: Visualização de Tensão
        self.tension_visualization = TensionTab(parent=self)
        # Expose widget interno para compatibilidade
        self.tension_viz_widget = self.tension_visualization.visualization
        right_panel.addTab(self.tension_visualization, "Visualização de Tensão")

        # Aba 4: Rastreabilidade
        self.tracking_tab = TrackingTab(self.stencil_tracker, parent=self)
        # Conecta sinais
        self.tracking_tab.stencil_selected.connect(self._on_stencil_selected)
        self.tracking_tab.stencil_cleared.connect(self._on_stencil_cleared)
        self.tracking_tab.recipe_requested.connect(self._on_recipe_requested)
        self.tracking_tab.tension_measurement_requested.connect(self._run_tension_measurement)
        self.tracking_tab.stencil_management_requested.connect(self.show_stencil_manager)
        self.tracking_tab.new_stencil_requested.connect(self.show_new_stencil_dialog)
        # Expose widget interno para compatibilidade
        self.stencil_identification = self.tracking_tab.stencil_identification
        self.btn_run_tension = self.tracking_tab.btn_run_tension
        right_panel.addTab(self.tracking_tab, "🏷️ Rastreabilidade")

        # Aba 5: Inspeção Visual (placeholder)
        self.inspection_tab = InspectionTab(parent=self)
        self.inspection_tab.settings_requested.connect(self.show_inspection_settings)
        self.inspection_tab.inspection_requested.connect(self._on_inspection_requested)
        right_panel.addTab(self.inspection_tab, "🔍 Inspeção")

        # Aba 6: Programação de Mapa (placeholder)
        self.map_tab = MapTab(parent=self)
        self.map_tab.map_definition_requested.connect(lambda: self.map_controller.show_dialog(self, self.cnc_tab.camera_preview if hasattr(self, "cnc_tab") else None))
        self.map_tab.mosaic_builder_requested.connect(self.show_mosaic_builder)
        right_panel.addTab(self.map_tab, "🗺️ Mapa")
        
        # ===================================================================
        # NOTA: As abas ficam habilitadas mesmo sem CLP conectado
        # O bloqueio agora é feito apenas nas ações que requerem movimento
        # (ex: _precheck_connected, _on_generate_map, etc.)
        # Isso permite usar câmera, receitas e visualização sem CLP
        # ===================================================================
        
        # Adiciona painéis ao splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(self.right_panel)
        splitter.setSizes([400, 800])
        
        main_layout.addWidget(splitter)
        
        # Barra de status
        self.statusBar().showMessage("Pronto para conectar")

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
        if not self.controller.cnc.is_connected:
            QMessageBox.warning(self, "Aviso", "Conecte a CNC antes de medir a tensão do stencil.")
            return
        dlg = StencilTensionDialog(self, self.controller.cnc)
        dlg.exec()

    # =========================================================================
    # GERENCIAMENTO DE RECEITAS
    # =========================================================================

    def show_recipe_manager(self):
        """Abre o diálogo de gerenciamento de receitas."""
        self.recipe_manager_wrapper.show_manager(self)

    def show_new_recipe_dialog(self):
        """Abre o diálogo para criar uma nova receita."""
        success = self.recipe_manager_wrapper.create_new(self)
        if success:
            QMessageBox.information(
                self, "Sucesso",
                "Receita criada com sucesso!\n\n"
                "Acesse Receitas > Gerenciar Receitas para carregar."
            )

    def _on_recipe_loaded(self, recipe):
        """Callback quando uma receita é carregada."""
        self.current_recipe = recipe
        self.recipe_manager.set_current_recipe(recipe)
        
        # Atualiza o menu
        if hasattr(self, 'current_recipe_action'):
            self.current_recipe_action.setText(f"📋 {recipe.name}")
            self.current_recipe_action.setEnabled(True)
        
        # Mostra na barra de status
        self.statusBar().showMessage(f"Receita carregada: {recipe.name}")
        logger.info(f"Receita carregada: {recipe.name} ({recipe.recipe_id})")
    
    def apply_recipe_to_capture(self):
        """Aplica as configurações de captura da receita atual ao diálogo de mapa."""
        settings = self.recipe_manager_wrapper.apply_to_capture()
        if settings is None:
            QMessageBox.warning(
                self, "Aviso",
                "Nenhuma receita carregada.\n\n"
                "Acesse Receitas > Gerenciar Receitas e carregue uma receita."
            )
            return

        # O resto será feito pelo handler _on_recipe_applied_to_capture
        # Mas o método público precisa existir para compatibilidade

    def apply_recipe_to_tension(self):
        """Aplica as configurações de tensão da receita atual ao diálogo de medição."""
        settings = self.recipe_manager_wrapper.apply_to_tension()
        if settings is None:
            QMessageBox.warning(
                self, "Aviso",
                "Nenhuma receita carregada.\n\n"
                "Acesse Receitas > Gerenciar Receitas e carregue uma receita."
            )
            return

        # O resto será feito pelo handler _on_recipe_applied_to_tension
        # Mas o método público precisa existir para compatibilidade

    # =========================================================================
    # GERENCIAMENTO DE STENCILS (RASTREABILIDADE)
    # =========================================================================
    
    def _on_stencil_selected(self, stencil: Stencil):
        """Handler quando um stencil é selecionado."""
        self.current_stencil = stencil
        self.btn_run_tension.setEnabled(True)
        
        # Atualiza barra de status
        self.statusBar().showMessage(
            f"Stencil selecionado: {stencil.code} | "
            f"Receita: {stencil.recipe_name or 'Nenhuma'} | "
            f"Inspeções: {stencil.inspection_count}"
        )
        
        # Atualiza menu
        self.current_stencil_action.setText(f"Stencil: {stencil.code}")
        
        logger.info(f"Stencil selecionado: {stencil.code}")
    
    def _on_stencil_cleared(self):
        """Handler quando a seleção de stencil é limpa."""
        self.current_stencil = None
        self.btn_run_tension.setEnabled(False)
        self.statusBar().showMessage("Pronto")
        
        # Atualiza menu
        self.current_stencil_action.setText("(Nenhum stencil selecionado)")
        
        logger.info("Seleção de stencil limpa")
    
    def _on_recipe_requested(self, recipe_name: str):
        """Handler quando o stencil solicita carregamento de receita."""
        self.recipe_manager_wrapper.load_recipe(recipe_name)
        # O restante é tratado pelo handler _on_recipe_loaded conectado ao signal

    # =========================================================================
    # HANDLERS DO RECIPEMANAGERWRAPPER
    # =========================================================================

    def _on_recipe_created(self, recipe_name: str):
        """Handler chamado quando nova receita é criada."""
        logger.info(f"Nova receita criada: {recipe_name}")
        # O método create_new() já mostrou QMessageBox

    def _on_recipe_applied_to_capture(self, settings: dict):
        """Handler chamado quando configurações de captura são aplicadas."""
        # Verifica se os atributos de mapa existem
        if not hasattr(self, 'map_origin'):
            self.map_origin = {}
        if not hasattr(self, 'map_end'):
            self.map_end = {}

        # Aplica configurações de captura
        self.map_origin = settings['origin']
        self.map_end = settings['end']

        # Tenta atualizar os widgets se existirem
        if hasattr(self, 'map_step_x_edit'):
            self.map_step_x_edit.setText(str(settings['step_x']))
        if hasattr(self, 'map_step_y_edit'):
            self.map_step_y_edit.setText(str(settings['step_y']))
        if hasattr(self, 'spin_capture_delay'):
            self.spin_capture_delay.setValue(settings['capture_delay_ms'])

        # Atualiza painel de informações calculadas
        self._update_adjusted_step_info()

        # Mostra confirmação
        r = self.current_recipe
        QMessageBox.information(
            self, "Receita Aplicada",
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
        r = self.current_recipe

        # Mostra informações dos critérios de aceitação
        acc = settings['acceptance']
        QMessageBox.information(
            self, "Receita de Tensão",
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
        # O método que chamou já tratou o erro com QMessageBox

    # =========================================================================
    # HANDLERS DO STENCILMANAGERWRAPPER
    # =========================================================================

    def _on_tension_record_added(self, stencil_code: str, record: TensionRecord):
        """Handler chamado quando registro de tensão é adicionado."""
        logger.info(
            f"Medição de tensão salva no histórico do stencil "
            f"'{stencil_code}': {record.result}"
        )

        QMessageBox.information(
            self, "Medição Salva",
            f"Resultado da medição salvo no histórico.\n\n"
            f"Stencil: {stencil_code}\n"
            f"Resultado: {record.result}\n"
            f"Média: {record.average_tension:.2f} N/cm²"
        )

        # Atualiza widget de identificação para refletir nova inspeção
        stencil = self.stencil_manager_wrapper.get_stencil(stencil_code)
        if stencil:
            self.stencil_identification._select_stencil(stencil)

    def _on_degradation_alert(self, alert: str):
        """Handler chamado quando há alerta de degradação."""
        QMessageBox.warning(
            self, "⚠️ Alerta de Degradação",
            f"Stencil: {self.current_stencil.code}\n\n{alert}"
        )

    def _on_stencil_error(self, error: str):
        """Handler chamado quando ocorre um erro com stencils."""
        logger.error(f"Erro de stencil: {error}")
        # Mostra erro ao usuário se necessário
        QMessageBox.critical(
            self, "Erro de Stencil",
            f"Ocorreu um erro:\n{error}"
        )

    # =========================================================================
    # HANDLERS DO INSPECTIONMANAGER
    # =========================================================================

    def _on_inspection_requested(self, gerber_file: str):
        """Handler para quando uma inspeção é solicitada."""
        logger.info(f"Inspeção solicitada para arquivo: {gerber_file}")
        # A inspeção será processada pelo InspectionManager
        pass

    def _on_inspection_completed(self, result, overlay):
        """Handler chamado quando inspeção é completada com sucesso."""
        import numpy as np

        # Salvar referências
        self._last_inspection_result = result
        self._last_inspection_overlay = overlay

        logger.info(f"Inspeção completada: {result.summary}")

        # Mostrar resultado
        self._show_inspection_result(result, overlay)

    def _on_inspection_failed(self, error: str):
        """Handler chamado quando inspeção falha."""
        logger.error(f"Inspeção falhou: {error}")
        QMessageBox.critical(
            self, "Erro na Inspeção",
            f"A inspeção falhou:\n{error}"
        )

    # =========================================================================
    # HANDLERS DO INSPECTIONCOORDINATOR (NOVO)
    # =========================================================================

    def _on_inspection_step_changed(self, step, message: str):
        """Handler chamado quando a etapa da inspeção muda."""
        logger.info(f"Inspection step: {step.value} - {message}")
        self.statusBar().showMessage(message)

    def _on_inspection_progress(self, percent: int, message: str):
        """Handler chamado quando o progresso da inspeção atualiza."""
        logger.debug(f"Inspection progress: {percent}% - {message}")
        self.statusBar().showMessage(f"{message} ({percent}%)")

    def _on_gerber_loaded(self, gerber_data):
        """Handler chamado quando Gerber é carregado."""
        logger.info("Gerber carregado com sucesso")
        self.statusBar().showMessage("Gerber carregado - Capture fiduciais", 5000)

    def _on_fiducials_captured(self, templates: list):
        """Handler chamado quando fiduciais são capturados."""
        logger.info(f"Fiduciais capturados: {len(templates)} templates")
        self.statusBar().showMessage(f"Fiduciais capturados: {len(templates)} - Alinhe o sistema", 5000)

    def _on_alignment_completed(self, transformation):
        """Handler chamado quando alinhamento é completado."""
        logger.info("Alinhamento completado")
        self.statusBar().showMessage("Sistema alinhado - Capture imagem de inspeção", 5000)

    def _on_inspection_image_captured(self, image_path: str):
        """Handler chamado quando imagem de inspeção é capturada."""
        logger.info(f"Imagem capturada: {image_path}")
        self.statusBar().showMessage("Imagem capturada - Analisando...", 3000)

    def _on_inspection_analysis_completed(self, result, overlay):
        """Handler chamado quando análise é completada."""
        logger.info("Análise completada")
        self.statusBar().showMessage("Análise concluída", 3000)

    def _on_inspection_workflow_completed(self, result):
        """Handler chamado quando workflow completo termina."""
        if result.success:
            logger.info(f"Inspeção completada: {result.summary}")
            self.statusBar().showMessage("Inspeção concluída com sucesso", 5000)
        else:
            logger.error(f"Inspeção falhou: {result.error}")
            self.statusBar().showMessage("Inspeção falhou", 5000)

    def _on_inspection_workflow_failed(self, error: str):
        """Handler chamado quando workflow falha."""
        logger.error(f"Workflow falhou: {error}")
        QMessageBox.critical(self, "Erro na Inspeção", f"O workflow de inspeção falhou:\n{error}")

    # =========================================================================
    # HANDLERS DO TENSIONCOORDINATOR (NOVO)
    # =========================================================================

    def _on_tension_step_changed(self, step, message: str):
        """Handler chamado quando a etapa da medição muda."""
        logger.info(f"Tension measurement step: {step.value} - {message}")
        self.statusBar().showMessage(message)

    def _on_tension_progress(self, current: int, total: int, message: str):
        """Handler chamado quando o progresso da medição atualiza."""
        logger.debug(f"Tension progress: {current}/{total} - {message}")
        self.statusBar().showMessage(f"{message} ({current}/{total} pontos)")

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
        self.statusBar().showMessage("Medições concluídas - Gerando relatório", 5000)

    def _on_tension_heatmap_generated(self, heatmap_path: str):
        """Handler chamado quando o heatmap é gerado."""
        logger.info(f"Heatmap gerado: {heatmap_path}")
        self.statusBar().showMessage("Heatmap gerado", 3000)

    def _on_tension_measurement_completed(self, result):
        """Handler chamado quando o workflow completo termina."""
        if result.success:
            classification = result.classification or "unknown"
            avg = result.average_tension or 0
            logger.info(f"Medição completada: {classification} (média: {avg:.2f} N/cm)")
            self.statusBar().showMessage(
                f"Medição concluída: {classification.upper()} ({avg:.2f} N/cm médio)",
                5000
            )
        else:
            logger.error("Medição falhou")
            self.statusBar().showMessage("Medição falhou", 5000)

    def _on_tension_measurement_failed(self, error: str):
        """Handler chamado quando workflow de tensão falha."""
        logger.error(f"Workflow de tensão falhou: {error}")
        QMessageBox.critical(self, "Erro na Medição", f"O workflow de medição falhou:\n{error}")

    def _on_thresholds_changed(self, thresholds):
        """Handler chamado quando thresholds de inspeção mudam."""
        logger.info("Thresholds de inspeção alterados")
        # Atualiza referência local
        self.inspection_thresholds = thresholds
        self.stencil_inspector = self.inspection_manager.get_inspector()

    # =========================================================================
    # HANDLERS DO REPORTMANAGERWRAPPER
    # =========================================================================

    def _on_report_generated(self, report_type: str, output_path: str):
        """Handler chamado quando relatório é gerado com sucesso."""
        logger.info(f"Relatório '{report_type}' gerado: {output_path}")

        QMessageBox.information(
            self, "Relatório Gerado",
            f"Relatório de {report_type} gerado com sucesso!\n\n"
            f"Arquivo: {output_path}"
        )

    def _on_report_failed(self, report_type: str, error: str):
        """Handler chamado quando geração de relatório falha."""
        logger.error(f"Falha ao gerar relatório '{report_type}': {error}")

        QMessageBox.critical(
            self, "Erro no Relatório",
            f"Falha ao gerar relatório de {report_type}:\n{error}"
        )

    def _on_report_config_changed(self, config):
        """Handler chamado quando configuração de relatório muda."""
        logger.info("Configuração de relatório alterada")
        # Atualiza referência local
        self.report_config = config
        self.report_generator = self.report_manager_wrapper.get_generator()





    def show_stencil_manager(self):
        """Abre o diálogo de gerenciamento de stencils."""
        self.stencil_manager_wrapper.show_manager(self)

    def show_new_stencil_dialog(self):
        """Abre o diálogo para criar um novo stencil."""
        stencil = self.stencil_manager_wrapper.create_new(self)
        if stencil:
            QMessageBox.information(
                self, "Sucesso",
                f"Stencil '{stencil.code}' cadastrado com sucesso!\n\n"
                "Escaneie ou digite o código para selecioná-lo."
            )

    
    def _run_tension_measurement(self):
        """Executa medição de tensão para o stencil selecionado."""
        if not self.current_stencil:
            QMessageBox.warning(
                self, "Stencil Não Selecionado",
                "Selecione um stencil antes de medir a tensão."
            )
            return
        
        if not self.controller.cnc.is_connected:
            QMessageBox.warning(
                self, "CLP Não Conectado",
                "Conecte o CLP antes de medir a tensão."
            )
            return
        
        # Abre diálogo de medição de tensão
        dlg = StencilTensionDialog(self, self.controller.cnc)
        
        # Se houver receita, pré-configura o diálogo
        if self.current_recipe and self.current_recipe.tension.enabled:
            # TODO: Passar parâmetros da receita para o diálogo
            pass
        
        result = dlg.exec()
        
        # Se medição foi concluída, salva no histórico
        if result == QDialog.DialogCode.Accepted:
            self._save_tension_to_history(dlg)

    def _save_tension_to_history(self, tension_dialog):
        """
        Salva resultado da medição de tensão no histórico do stencil.

        Args:
            tension_dialog: Diálogo de tensão com os dados da medição
        """
        if not self.current_stencil:
            return

        try:
            # Tenta obter dados da medição do diálogo ou do último arquivo salvo
            measurements_file = "stencil_tension_measurements.json"

            if os.path.exists(measurements_file):
                with open(measurements_file, "r", encoding="utf-8") as f:
                    tension_data = json.load(f)

                # Cria registro de tensão
                record = TensionRecord.from_tension_data(
                    tension_data,
                    recipe_name=self.current_recipe.name if self.current_recipe else None,
                    operator=None  # TODO: Implementar campo de operador
                )

                # Salva no histórico usando o wrapper
                recipe_acceptance = None
                if self.current_recipe and self.current_recipe.tension.acceptance:
                    recipe_acceptance = self.current_recipe.tension.acceptance

                self.stencil_manager_wrapper.add_tension_record(
                    self.current_stencil.code,
                    record,
                    recipe_acceptance=recipe_acceptance
                )

                # O resto é tratado pelos handlers conectados aos signals
                # (_on_tension_record_added, _on_degradation_alert)

            else:
                logger.warning("Arquivo de medições não encontrado")
                
        except Exception as e:
            logger.error(f"Erro ao salvar medição no histórico: {e}")
            QMessageBox.warning(
                self, "Erro",
                f"Erro ao salvar no histórico:\n{str(e)}"
            )

    def show_mosaic_builder(self):
        """Abre a janela do Mosaic Builder para montagem de imagens"""
        from mosaic_builder import MosaicBuilder
        self.mosaic_window = MosaicBuilder()
        self.mosaic_window.resize(1200, 900)
        self.mosaic_window.show()

    def show_camera_calibration_dialog(self):
        """Abre diálogo para calibração de câmera (correção de distorção)"""
        if not hasattr(self.controller.camera, 'is_connected') or not self.controller.camera.is_connected:
            QMessageBox.warning(self, "Aviso", "Conecte a câmera antes de calibrar.")
            return
        
        from camera_calibration import CameraCalibrationDialog
        self.camera_calib_dialog = CameraCalibrationDialog(self.controller.camera, self)
        self.camera_calib_dialog.resize(900, 750)
        self.camera_calib_dialog.show()

    def show_fov_calibration_dialog(self):
        """
        Abre diálogo para calibração de Campo de Visão (FOV).
        
        Esta calibração define a relação entre pixels da câmera e dimensões físicas (mm)
        em diferentes alturas Z, permitindo conversão precisa de clique no vídeo para
        movimento da head.
        """
        # Cria adaptador para o ConfigManager para usar o formato esperado pelo diálogo
        class ConfigAdapter:
            def __init__(self, cfg):
                self._cfg = cfg
            
            def get_config(self, key, default=None):
                if key == "camera_fov":
                    return self._cfg.get("camera", "fov_calibration", default=default or {})
                return default
            
            def set_config(self, key, value):
                if key == "camera_fov":
                    self._cfg.set("camera", "fov_calibration", value=value)
                    self._cfg.save()
        
        adapter = ConfigAdapter(self.config)
        
        dialog = FOVCalibrationDialog(adapter, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Atualiza o conversor FOV do CameraPreviewWidget
            if hasattr(self, 'camera_preview') and hasattr(self.camera_preview, 'fov_converter'):
                fov = dialog.get_calibration()
                self.camera_preview.fov_converter.set_fov_calibration(fov)
                logger.info(f"Calibração de FOV atualizada: {fov}")
            
            QMessageBox.information(
                self, "Calibração Salva",
                "A calibração de campo de visão foi salva.\n\n"
                "Agora você pode usar o clique no vídeo para mover a head\n"
                "com precisão baseada na altura Z atual."
            )

    def show_crosshair_settings_dialog(self):
        """
        Abre diálogo para configurar a cruz de centralização da câmera.

        Permite ajustar:
        - Cor da linha (seletor de cor visual)
        - Espessura da linha (1-10 pixels)
        - Comprimento da linha (1-50% da menor dimensão)
        """
        dialog = CrosshairSettingsDialog(self.config, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(
                self, "Configurações Salvas",
                "As configurações da cruz foram salvas.\n\n"
                "As mudanças serão aplicadas na próxima atualização do preview."
            )

    def show_fiducial_alignment_dialog(self):
        """
        Abre diálogo para alinhamento de fiduciais.
        
        Esta ferramenta permite:
        - Carregar arquivo Gerber e detectar fiduciais automaticamente
        - Capturar templates de fiduciais da câmera ou mosaico
        - Calcular transformação (translação, rotação, escala) para alinhar
        - Ajuste fino manual da transformação
        """
        dialog = QDialog(self)
        dialog.setWindowTitle("🎯 Alinhamento de Fiduciais")
        dialog.setMinimumSize(1000, 700)
        dialog.resize(1200, 800)
        
        layout = QVBoxLayout(dialog)
        
        # Widget principal de alinhamento
        alignment_widget = FiducialAlignmentWidget()
        layout.addWidget(alignment_widget)
        
        # Se temos um mosaico recente, usar como imagem base
        mosaic_path = self.config.get("mosaic", "last_output_path", default=None)
        if mosaic_path and os.path.exists(mosaic_path):
            try:
                img = cv2.imread(mosaic_path)
                if img is not None:
                    alignment_widget.set_image(img)
                    logger.info(f"Mosaico carregado para alinhamento: {mosaic_path}")
            except Exception as e:
                logger.warning(f"Erro ao carregar mosaico: {e}")
        
        # Callback para captura de frame da câmera
        def get_camera_frame():
            if hasattr(self, 'camera_preview') and self.controller.camera.is_connected:
                frame = self.controller.camera.get_frame()
                return frame
            return None
        
        alignment_widget.set_frame_callback(get_camera_frame)
        
        # Conectar sinais
        def on_alignment_complete(transform):
            logger.info(f"Alinhamento calculado: tx={transform.tx:.1f}, ty={transform.ty:.1f}, "
                       f"angle={transform.angle:.2f}°, scale={transform.scale_x:.4f}")
            
            # Salvar transformação nas configurações
            self.config.set("fiducial_alignment", "last_tx", transform.tx)
            self.config.set("fiducial_alignment", "last_ty", transform.ty)
            self.config.set("fiducial_alignment", "last_angle", transform.angle)
            self.config.set("fiducial_alignment", "last_scale", transform.scale_x)
            self.config.save()
            
            QMessageBox.information(
                dialog, "Alinhamento Aplicado",
                f"Transformação calculada:\n\n"
                f"📍 Translação: ({transform.tx:.1f}, {transform.ty:.1f}) px\n"
                f"🔄 Rotação: {transform.angle:.2f}°\n"
                f"📐 Escala: {transform.scale_x:.4f}\n\n"
                f"Os valores foram salvos nas configurações."
            )
            dialog.accept()
        
        def on_alignment_cancelled():
            dialog.reject()
        
        alignment_widget.alignmentComplete.connect(on_alignment_complete)
        alignment_widget.alignmentCancelled.connect(on_alignment_cancelled)
        
        # Botões de arquivo para carregar imagem
        btn_layout = QHBoxLayout()
        
        btn_load_image = QPushButton("📷 Carregar Imagem/Mosaico")
        def load_image():
            filepath, _ = QFileDialog.getOpenFileName(
                dialog, "Carregar Imagem",
                "", "Imagens (*.png *.jpg *.bmp *.tiff);;All Files (*)"
            )
            if filepath:
                img = cv2.imread(filepath)
                if img is not None:
                    alignment_widget.set_image(img)
                    logger.info(f"Imagem carregada: {filepath}")
        btn_load_image.clicked.connect(load_image)
        btn_layout.addWidget(btn_load_image)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        dialog.exec()

    # =========================================================================
    #  SISTEMA DE RELATÓRIOS
    # =========================================================================
    
    def show_report_settings(self):
        """Abre diálogo de configurações de relatório."""
        dialog = ReportSettingsDialog(self.report_config, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_config = dialog.get_config()
            self.report_manager_wrapper.update_config(new_config, save=True)
            self.report_config = new_config  # Atualiza referência local

            logger.info("Configuração de relatórios atualizada e salva")
            self.statusBar().showMessage("Configurações de relatório salvas", 3000)

    
    def show_tension_report_dialog(self):
        """Gera relatório de tensão da última medição."""
        # Tentar carregar última medição
        tension_file = Path("stencil_tension_measurements.json")

        if not tension_file.exists():
            QMessageBox.warning(
                self, "Sem Dados",
                "Nenhuma medição de tensão disponível.\n\n"
                "Execute uma medição de tensão primeiro."
            )
            return

        try:
            with open(tension_file, 'r', encoding='utf-8') as f:
                tension_data = json.load(f)

            # Obter informações do stencil atual
            stencil_code = None
            if self.current_stencil:
                stencil_code = self.current_stencil.code

            # Gerar relatório via manager
            output_path = self.report_manager_wrapper.generate_tension_report(
                tension_data=tension_data,
                stencil_code=stencil_code,
                operator=None  # TODO: Implementar campo de operador
            )

            if output_path:
                # Perguntar se quer abrir o PDF
                reply = QMessageBox.question(
                    self, "Relatório Gerado",
                    f"Relatório gerado com sucesso:\n{output_path}\n\n"
                    f"Deseja abrir o arquivo?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.Yes:
                    import subprocess
                    subprocess.Popen([output_path], shell=True)

                
        except Exception as e:
            logger.exception("Erro ao gerar relatório de tensão")
            QMessageBox.critical(
                self, "Erro",
                f"Erro ao gerar relatório:\n{str(e)}"
            )
    
    def show_stencil_report_dialog(self):
        """Gera relatório de histórico do stencil selecionado."""
        if not self.current_stencil:
            QMessageBox.warning(
                self, "Stencil Não Selecionado",
                "Selecione um stencil primeiro usando a aba de Rastreabilidade."
            )
            return

        # Obter histórico do stencil via manager
        history = self.stencil_manager_wrapper.get_tension_history(self.current_stencil.code)

        if not history:
            QMessageBox.warning(
                self, "Sem Histórico",
                f"O stencil {self.current_stencil.code} não possui histórico de medições."
            )
            return

        try:
            # Gerar relatório via manager
            output_path = self.report_manager_wrapper.generate_stencil_history_report(
                stencil_code=self.current_stencil.code,
                include_tension=True,
                include_inspections=True
            )

            if output_path:
                # Perguntar se quer abrir
                reply = QMessageBox.question(
                    self, "Relatório Gerado",
                    f"Relatório de histórico gerado:\n{output_path}\n\n"
                    f"Deseja abrir o arquivo?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.Yes:
                    import subprocess
                    subprocess.Popen([output_path], shell=True)

        except Exception as e:
            logger.exception("Erro ao gerar relatório de stencil")
            QMessageBox.critical(
                self, "Erro",
                f"Erro ao gerar relatório:\n{str(e)}"
            )

    
    def show_period_query_dialog(self):
        """Abre diálogo para consultar medições por período."""
        from PyQt6.QtWidgets import QDateEdit
        from PyQt6.QtCore import QDate
        
        dialog = QDialog(self)
        dialog.setWindowTitle("📅 Consultar por Período")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Seleção de período
        period_group = QGroupBox("Período de Consulta")
        period_layout = QFormLayout(period_group)
        
        date_start = QDateEdit()
        date_start.setDate(QDate.currentDate().addMonths(-1))
        date_start.setCalendarPopup(True)
        period_layout.addRow("Data Inicial:", date_start)
        
        date_end = QDateEdit()
        date_end.setDate(QDate.currentDate())
        date_end.setCalendarPopup(True)
        period_layout.addRow("Data Final:", date_end)
        
        layout.addWidget(period_group)
        
        # Opções
        options_group = QGroupBox("Opções")
        options_layout = QVBoxLayout(options_group)
        
        chk_all_stencils = QCheckBox("Todos os stencils")
        chk_all_stencils.setChecked(True)
        options_layout.addWidget(chk_all_stencils)
        
        layout.addWidget(options_group)
        
        # Lista de resultados
        from PyQt6.QtWidgets import QTableWidget
        result_table = QTableWidget()
        result_table.setColumnCount(5)
        result_table.setHorizontalHeaderLabels(["Data", "Stencil", "Média", "Resultado", "Operador"])
        result_table.setMinimumHeight(200)
        layout.addWidget(result_table)
        
        # Botões
        btn_layout = QHBoxLayout()
        
        btn_search = QPushButton("🔍 Buscar")
        def do_search():
            # Converter datas
            start = date_start.date().toPyDate()
            end = date_end.date().toPyDate()
            
            # Buscar em todos os stencils
            all_records = []
            stencils = self.stencil_tracker.list_stencils()
            
            for stencil in stencils:
                history = self.stencil_tracker.get_tension_history(stencil.code)
                for record in history:
                    try:
                        ts = record.timestamp if hasattr(record, 'timestamp') else record.get('timestamp', '')
                        from datetime import datetime
                        dt = datetime.fromisoformat(ts).date()
                        if start <= dt <= end:
                            all_records.append((stencil.code, record))
                    except:
                        pass
            
            # Preencher tabela
            result_table.setRowCount(len(all_records))
            for i, (code, record) in enumerate(all_records):
                ts = record.timestamp if hasattr(record, 'timestamp') else record.get('timestamp', '')
                avg = record.average_tension if hasattr(record, 'average_tension') else record.get('average_tension', 0)
                result_field = record.result if hasattr(record, 'result') else record.get('result', 'OK')
                op = record.operator if hasattr(record, 'operator') else record.get('operator', '-')
                
                result_table.setItem(i, 0, QTableWidgetItem(ts[:16]))
                result_table.setItem(i, 1, QTableWidgetItem(code))
                result_table.setItem(i, 2, QTableWidgetItem(f"{avg:.2f}"))
                result_table.setItem(i, 3, QTableWidgetItem(result_field))
                result_table.setItem(i, 4, QTableWidgetItem(op or "-"))
            
            self.statusBar().showMessage(f"{len(all_records)} registros encontrados", 3000)
        
        btn_search.clicked.connect(do_search)
        btn_layout.addWidget(btn_search)
        
        btn_export = QPushButton("📄 Exportar CSV")
        def do_export():
            if result_table.rowCount() == 0:
                QMessageBox.warning(dialog, "Sem Dados", "Execute uma busca primeiro.")
                return
            
            filepath, _ = QFileDialog.getSaveFileName(
                dialog, "Exportar CSV", "", "CSV (*.csv)"
            )
            if filepath:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write("Data,Stencil,Média,Resultado,Operador\n")
                    for row in range(result_table.rowCount()):
                        cols = [result_table.item(row, c).text() for c in range(5)]
                        f.write(",".join(cols) + "\n")
                QMessageBox.information(dialog, "Exportado", f"Dados exportados para:\n{filepath}")
        
        btn_export.clicked.connect(do_export)
        btn_layout.addWidget(btn_export)
        
        btn_layout.addStretch()
        
        btn_close = QPushButton("Fechar")
        btn_close.clicked.connect(dialog.accept)
        btn_layout.addWidget(btn_close)
        
        layout.addLayout(btn_layout)
        
        dialog.exec()

    # =========================================================================
    #  SISTEMA DE INSPEÇÃO VISUAL
    # =========================================================================
    
    def show_inspection_settings(self):
        """Abre diálogo de configuração dos parâmetros de inspeção."""
        dialog = InspectionSettingsDialog(self.inspection_thresholds, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_thresholds = dialog.get_thresholds()
            self.inspection_manager.update_thresholds(new_thresholds, save=True)
            self.inspection_thresholds = new_thresholds  # Atualiza referência local

            logger.info("Parâmetros de inspeção atualizados e salvos")
            self.statusBar().showMessage("Parâmetros de inspeção salvos", 3000)
    
    def show_inspection_dialog(self):
        """Abre diálogo para executar inspeção visual."""
        dialog = QDialog(self)
        dialog.setWindowTitle("🔬 Inspeção Visual de Stencil")
        dialog.setMinimumWidth(600)
        
        layout = QVBoxLayout(dialog)
        
        # Grupo: Arquivos
        files_group = QGroupBox("📁 Arquivos de Entrada")
        files_layout = QFormLayout(files_group)
        
        # Gerber
        gerber_layout = QHBoxLayout()
        self._insp_gerber_path = QLineEdit()
        self._insp_gerber_path.setPlaceholderText("Selecione o arquivo Gerber...")
        gerber_layout.addWidget(self._insp_gerber_path)
        btn_browse_gerber = QPushButton("📁")
        btn_browse_gerber.clicked.connect(self._browse_inspection_gerber)
        gerber_layout.addWidget(btn_browse_gerber)
        files_layout.addRow("Arquivo Gerber:", gerber_layout)
        
        # Mosaico
        mosaic_layout = QHBoxLayout()
        self._insp_mosaic_path = QLineEdit()
        self._insp_mosaic_path.setPlaceholderText("Selecione a imagem do mosaico...")
        
        # Auto-preencher com último mosaico
        last_mosaic = self.config.get("mosaic", "last_output_path", default="")
        if last_mosaic and os.path.exists(last_mosaic):
            self._insp_mosaic_path.setText(last_mosaic)
        
        mosaic_layout.addWidget(self._insp_mosaic_path)
        btn_browse_mosaic = QPushButton("📁")
        btn_browse_mosaic.clicked.connect(self._browse_inspection_mosaic)
        mosaic_layout.addWidget(btn_browse_mosaic)
        files_layout.addRow("Imagem Mosaico:", mosaic_layout)
        
        layout.addWidget(files_group)
        
        # Grupo: Informações
        info_group = QGroupBox("ℹ️ Informações")
        info_layout = QFormLayout(info_group)
        
        self._insp_stencil_label = QLabel(
            self.current_stencil.code if self.current_stencil else "(nenhum stencil selecionado)"
        )
        info_layout.addRow("Stencil:", self._insp_stencil_label)
        
        thresholds_text = (
            f"OK ≥ {self.inspection_thresholds.ok_threshold}%, "
            f"PARTIAL ≥ {self.inspection_thresholds.partial_threshold}%"
        )
        info_layout.addRow("Thresholds:", QLabel(thresholds_text))
        
        layout.addWidget(info_group)
        
        # Grupo: Alinhamento
        align_group = QGroupBox("🎯 Alinhamento Gerber ↔ Imagem")
        align_layout = QVBoxLayout(align_group)
        
        # Checkbox para usar alinhamento existente
        self._insp_use_alignment = QCheckBox("Usar transformação de alinhamento (fiduciais)")
        
        # Verificar se existe transformação salva
        saved_tx = self.config.get("fiducial_alignment", "last_tx", default=None)
        has_alignment = saved_tx is not None
        
        self._insp_use_alignment.setChecked(has_alignment)
        self._insp_use_alignment.setEnabled(has_alignment)
        
        if has_alignment:
            tx = self.config.get("fiducial_alignment", "last_tx", default=0)
            ty = self.config.get("fiducial_alignment", "last_ty", default=0)
            angle = self.config.get("fiducial_alignment", "last_angle", default=0)
            scale = self.config.get("fiducial_alignment", "last_scale", default=1)
            self._insp_use_alignment.setText(
                f"Usar transformação de alinhamento "
                f"(tx={tx:.0f}, ty={ty:.0f}, rot={angle:.1f}°, escala={scale:.3f})"
            )
        else:
            self._insp_use_alignment.setText(
                "Usar transformação de alinhamento (nenhuma configurada)"
            )
        
        align_layout.addWidget(self._insp_use_alignment)
        
        # Botão para configurar alinhamento
        btn_align = QPushButton("🎯 Configurar Alinhamento de Fiduciais...")
        btn_align.clicked.connect(lambda: self._open_fiducial_alignment_from_inspection(dialog))
        align_layout.addWidget(btn_align)
        
        layout.addWidget(align_group)
        
        # Status
        self._insp_status = QLabel("")
        layout.addWidget(self._insp_status)
        
        # Barra de progresso
        from PyQt6.QtWidgets import QProgressBar
        self._insp_progress = QProgressBar()
        self._insp_progress.setVisible(False)
        layout.addWidget(self._insp_progress)
        
        layout.addStretch()
        
        # Botões
        btn_layout = QHBoxLayout()
        
        btn_settings = QPushButton("⚙️ Parâmetros")
        btn_settings.clicked.connect(self.show_inspection_settings)
        btn_layout.addWidget(btn_settings)
        
        btn_layout.addStretch()
        
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(dialog.reject)
        btn_layout.addWidget(btn_cancel)
        
        btn_run = QPushButton("▶️ Executar Inspeção")
        btn_run.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        btn_run.clicked.connect(lambda: self._run_inspection(dialog))
        btn_layout.addWidget(btn_run)
        
        layout.addLayout(btn_layout)
        
        dialog.exec()
    
    def _browse_inspection_gerber(self):
        """Seleciona arquivo Gerber para inspeção."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Arquivo Gerber",
            "", "Gerber (*.gbr *.ger);;Todos (*)"
        )
        if filepath:
            self._insp_gerber_path.setText(filepath)
    
    def _browse_inspection_mosaic(self):
        """Seleciona imagem do mosaico para inspeção."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Imagem do Mosaico",
            "", "Imagens (*.png *.jpg *.bmp *.tiff);;Todos (*)"
        )
        if filepath:
            self._insp_mosaic_path.setText(filepath)
    
    def _run_inspection(self, dialog: QDialog):
        """Executa a inspeção visual."""
        gerber_path = self._insp_gerber_path.text()
        mosaic_path = self._insp_mosaic_path.text()

        # Validar
        if not gerber_path or not os.path.exists(gerber_path):
            QMessageBox.warning(dialog, "Erro", "Selecione um arquivo Gerber válido.")
            return

        if not mosaic_path or not os.path.exists(mosaic_path):
            QMessageBox.warning(dialog, "Erro", "Selecione uma imagem de mosaico válida.")
            return

        try:
            self._insp_status.setText("🔄 Carregando Gerber...")
            self._insp_progress.setVisible(True)
            self._insp_progress.setValue(10)
            QApplication.processEvents()

            # Carregar Gerber
            if not self.inspection_manager.load_gerber(gerber_path):
                return

            self._insp_status.setText("🔄 Carregando mosaico...")
            self._insp_progress.setValue(30)
            QApplication.processEvents()

            # Carregar mosaico
            mosaic = cv2.imread(mosaic_path)
            if mosaic is None:
                raise ValueError(f"Não foi possível carregar: {mosaic_path}")

            self.inspection_manager.set_mosaic(mosaic)

            # Carregar transformação de alinhamento se selecionada
            if self._insp_use_alignment.isChecked():
                from aoi_lib.gerber_renderer import AlignmentTransform
                tx = self.config.get("fiducial_alignment", "last_tx", default=0)
                ty = self.config.get("fiducial_alignment", "last_ty", default=0)
                angle = self.config.get("fiducial_alignment", "last_angle", default=0)
                scale = self.config.get("fiducial_alignment", "last_scale", default=1)

                transform = AlignmentTransform(
                    tx=tx, ty=ty, angle=angle,
                    scale_x=scale, scale_y=scale
                )
                self.inspection_manager.set_alignment(transform)
                self._insp_status.setText("🔄 Aplicando alinhamento...")
                QApplication.processEvents()

            self._insp_status.setText("🔄 Executando inspeção...")
            self._insp_progress.setValue(50)
            QApplication.processEvents()

            # Executar inspeção via manager (o resultado será tratado pelo signal)
            result, overlay = self.inspection_manager.run_inspection()

            if result is None:
                # Erro já tratado pelo signal inspection_failed
                return

            self._insp_progress.setValue(100)

            # Salvar resultados

            self._last_inspection_result = result
            self._last_inspection_overlay = overlay
            result.gerber_file = gerber_path
            result.mosaic_file = mosaic_path
            result.stencil_code = self.current_stencil.code if self.current_stencil else None
            
            # Fechar diálogo e mostrar resultado
            dialog.accept()
            
            # Mostrar resultado
            self._show_inspection_result(result, overlay)
            
        except Exception as e:
            logger.exception("Erro na inspeção visual")
            self._insp_progress.setVisible(False)
            QMessageBox.critical(
                dialog, "Erro",
                f"Erro ao executar inspeção:\n{str(e)}"
            )
    
    def _open_fiducial_alignment_from_inspection(self, parent_dialog: QDialog):
        """Abre o alinhamento de fiduciais a partir do diálogo de inspeção."""
        parent_dialog.hide()  # Esconder temporariamente
        
        self.show_fiducial_alignment_dialog()
        
        # Verificar se agora temos alinhamento
        saved_tx = self.config.get("fiducial_alignment", "last_tx", default=None)
        has_alignment = saved_tx is not None
        
        if has_alignment:
            tx = self.config.get("fiducial_alignment", "last_tx", default=0)
            ty = self.config.get("fiducial_alignment", "last_ty", default=0)
            angle = self.config.get("fiducial_alignment", "last_angle", default=0)
            scale = self.config.get("fiducial_alignment", "last_scale", default=1)
            self._insp_use_alignment.setText(
                f"Usar transformação de alinhamento "
                f"(tx={tx:.0f}, ty={ty:.0f}, rot={angle:.1f}°, escala={scale:.3f})"
            )
            self._insp_use_alignment.setChecked(True)
            self._insp_use_alignment.setEnabled(True)
        
        parent_dialog.show()  # Mostrar novamente
    
    def _show_inspection_result(self, result: InspectionResult, overlay: np.ndarray):
        """Exibe resultado da inspeção em uma janela."""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"📊 Resultado da Inspeção - {result.overall_status}")
        dialog.resize(1200, 800)
        
        layout = QVBoxLayout(dialog)
        
        # Widget de resultado
        result_widget = InspectionResultWidget()
        result_widget.set_result(result, overlay)
        
        # Conectar exportação
        def export_pdf():
            try:
                import tempfile
                from pathlib import Path
                
                # Salvar overlay em arquivo temporário
                temp_dir = Path(tempfile.gettempdir())
                overlay_path = str(temp_dir / "inspection_overlay_temp.png")
                cv2.imwrite(overlay_path, overlay)
                
                # Preparar dados da inspeção
                result_dict = result.to_dict() if hasattr(result, 'to_dict') else {
                    'total_apertures': result.total_apertures,
                    'ok_count': result.ok_count,
                    'partial_count': result.partial_count,
                    'blocked_count': result.blocked_count,
                    'overall_status': result.overall_status,
                    'approval_rate': result.approval_rate,
                    'defects': [d.to_dict() if hasattr(d, 'to_dict') else d for d in result.defects]
                }
                
                stencil_code = self.current_stencil.code if self.current_stencil else None
                
                # Gerar PDF
                pdf_path = self.report_generator.generate_inspection_report(
                    inspection_result=result_dict,
                    overlay_image_path=overlay_path,
                    stencil_code=stencil_code,
                    operator=self.config.get("user", "name", default="Operador")
                )
                
                QMessageBox.information(
                    dialog, "Relatório Gerado",
                    f"Relatório de inspeção visual salvo em:\n\n{pdf_path}"
                )
                
                # Abrir PDF
                os.startfile(pdf_path)
                
            except Exception as e:
                logger.exception("Erro ao gerar relatório de inspeção")
                QMessageBox.critical(
                    dialog, "Erro",
                    f"Erro ao gerar relatório:\n{str(e)}"
                )
        
        result_widget.exportRequested.connect(export_pdf)
        
        layout.addWidget(result_widget)
        
        # Botões
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_close = QPushButton("Fechar")
        btn_close.clicked.connect(dialog.accept)
        btn_layout.addWidget(btn_close)
        
        layout.addLayout(btn_layout)
        
        dialog.exec()
    
    def show_last_inspection_result(self):
        """Mostra o último resultado de inspeção."""
        if self._last_inspection_result is None:
            QMessageBox.information(
                self, "Sem Resultado",
                "Nenhuma inspeção foi executada ainda.\n\n"
                "Use 'Inspeção Visual' → 'Executar Inspeção' para realizar uma inspeção."
            )
            return
        
        self._show_inspection_result(
            self._last_inspection_result, 
            self._last_inspection_overlay
        )



    def show_settings_dialog(self):
        dlg = SettingsDialog(self.config, self)
        if dlg.exec():
            # Se o usuário modificou algo, re-aplica (se a CNC já estiver conectada)
            if self.controller.cnc.is_connected:
                self.config.apply_to_cnc(self.controller.cnc)
            # Atualiza campos rápidos de conexão do PLC
            if hasattr(self, "plc_host_input"):
                self.plc_host_input.setText(self.config.get("connections", "plc_host", default="192.168.1.5"))
            if hasattr(self, "plc_port_input"):
                self.plc_port_input.setValue(self.config.get("connections", "plc_port", default=502))
            self.statusBar().showMessage("Preferências salvas")


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
        """Create a sequence from registered positions"""
        if not self.position_registry.positions:
            QMessageBox.warning(self, "Warning", "No positions registered")
            return
            
        # Get sequence name
        sequence_name = self.sequence_widget.sequence_name.text()
        if not sequence_name:
            QMessageBox.warning(self, "Warning", "Please enter a sequence name")
            return
            
        # Clear existing positions in the position list widget
        self.position_list_widget.clear_positions()
        
        # Create positions for the sequence
        positions = []
        for pos in self.position_registry.positions:
            # Create position object with camera parameters
            camera_params = {"has_image": pos['image'] is not None}
            
            inspection_pos = InspectionPosition(
                pos['name'],
                pos['x'],
                pos['y'],
                pos.get('z', 0.0),
                camera_params
            )
            positions.append(inspection_pos)
            
            # Also add to the position list widget
            self.position_list_widget.add_position(inspection_pos)
            
        # Create the sequence
        self.current_sequence = self.controller.create_sequence(sequence_name, positions)
        
        # Update UI
        self.sequence_widget.sequence_status.setText(f"Created: {len(positions)} positions")
        self.statusBar().showMessage(f"Sequence '{sequence_name}' created with {len(positions)} positions")
        
        # Ask if user wants to save as G-CODE
        reply = QMessageBox.question(
            self, 
            "Save G-CODE", 
            "Do you want to save this sequence as G-CODE?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.save_gcode()

    def load_gcode(self):
        """Carrega uma sequência a partir de um arquivo G-CODE"""
        from aoi_lib.gcode_manager import GCodeManager
        gcode_manager = GCodeManager()
        
        filename, _ = QFileDialog.getOpenFileName(
            self, "Abrir G-CODE", "", "Arquivos G-CODE (*.gcode *.nc *.ngc)"
        )
        
        if filename:
            # Carrega o G-CODE
            result = gcode_manager.read_gcode_file(filename)
            
            if result:
                # Limpa posições atuais
                self.position_list_widget.clear_positions()
                
                # Cria sequência a partir dos dados do G-CODE
                positions = []
                for pos_data in result['positions']:
                    # Cria objeto de posição
                    position = InspectionPosition(
                        pos_data['name'], 
                        pos_data['x'], 
                        pos_data['y'],
                        pos_data['camera_params']
                    )
                    
                    # Adiciona à lista visual
                    self.position_list_widget.add_position(position)
                    
                    # Adiciona à lista interna
                    positions.append(position)
                
                # Cria a sequência
                self.current_sequence = self.controller.create_sequence(
                    result['sequence_name'], positions
                )
                
                # Atualiza interface
                self.sequence_widget.sequence_name.setText(result['sequence_name'])
                self.sequence_widget.sequence_status.setText(
                    f"Carregada do G-CODE: {len(positions)} posições"
                )
                
                self.statusBar().showMessage(f"G-CODE carregado de {filename}")
            else:
                QMessageBox.critical(self, "Erro", "Falha ao carregar o arquivo G-CODE")

    def save_gcode(self):
        """Salva a sequência atual como um arquivo G-CODE"""
        if not self.current_sequence:
            QMessageBox.warning(self, "Aviso", "Crie uma sequência primeiro")
            return

        from aoi_lib.gcode_manager import GCodeManager
        gcode_manager = GCodeManager()

        filename, _ = QFileDialog.getSaveFileName(
            self, "Salvar G-CODE", "", "Arquivos G-CODE (*.gcode *.nc *.ngc)"
        )

        if filename:
            # Adiciona extensão se necessário
            if not filename.endswith('.gcode') and not filename.endswith('.nc') and not filename.endswith('.ngc'):
                filename += '.gcode'

            # Salva usando o GCodeManager
            if gcode_manager.save_gcode_to_file(self.current_sequence, filename):
                self.statusBar().showMessage(f"G-CODE salvo em {filename}")
            else:
                QMessageBox.critical(self, "Erro", "Falha ao salvar o arquivo G-CODE")

    def show_about_dialog(self):
        """Exibe o diálogo Sobre"""
        from consumo_lib.dialogs import AboutDialog
        dialog = AboutDialog(self)
        dialog.exec()

    def refresh_ports(self):
        """Atualiza a lista de portas seriais disponíveis"""
        import serial.tools.list_ports

        self.cnc_port_combo.clear()
        ports = [port.device for port in serial.tools.list_ports.comports()]
        
        if ports:
            self.cnc_port_combo.addItems(ports)
            
            # Verificar se COM9 está na lista e selecionar
            com9_index = self.cnc_port_combo.findText("COM9")
            if com9_index >= 0:
                self.cnc_port_combo.setCurrentIndex(com9_index)
                self.statusBar().showMessage("Porta COM9 detectada")
        else:
            self.statusBar().showMessage("Nenhuma porta serial encontrada")

    def _apply_plc_ui_settings(self):
        """Atualiza IP/porta do PLC vindos da UI e persiste no config."""
        if not isinstance(self.controller.cnc, PLCAxisController):
            return

        host = (self.plc_host_input.text() or "").strip() or "192.168.1.5"
        port = int(self.plc_port_input.value())
        current_host = getattr(self.controller.cnc, "host", None)
        current_port = getattr(self.controller.cnc, "port", None)
        current_port_int = int(current_port) if current_port is not None else None

        # Persistência no arquivo de config
        self.config.set("connections", "plc_host", value=host)
        self.config.set("connections", "plc_port", value=port)

        if host == current_host and current_port_int == port:
            return

        try:
            self.controller.cnc.set_connection_params(host, port)
        except Exception as e:
            logger.error("Falha ao aplicar IP/porta do PLC: %s", e)
        else:
            self.statusBar().showMessage(f"Configurações do PLC atualizadas para {host}:{port}")

    def connect_cnc(self):
        """
        Conecta/desconecta à máquina CNC.

        NOTA: Para PLC, este método delega para ConnectionManager.
        Para GRBL, mantém a implementação original.
        """
        # Se for PLCAxisController, delega para ConnectionManager
        if isinstance(self.controller.cnc, PLCAxisController):
            self.connection_mgr.toggle_plc()
            return
        # Senão, cai no fluxo original GRBL…
        if hasattr(self.controller.cnc, 'grbl') and self.controller.cnc.grbl: 
            self.controller.cnc.grbl.poll_stop() 
            self.controller.cnc.grbl.disconnect() 
            self.controller.cnc.grbl = None
            self.controller.cnc.is_connected = False
            self.connect_cnc_btn.setText("Conectar CNC")
            self.cnc_status.setText("Desconectado")
            self.statusBar().showMessage("CNC desconectada")
    
        else:
            # Conectar
            port = self.cnc_port_combo.currentText()
            if not port:
                QMessageBox.warning(self, "Erro", "Selecione uma porta serial")
                return
                
            self.statusBar().showMessage(f"Conectando à CNC na porta {port}...")
            
            try:
                # Define função de callback para eventos do GrblStreamer
                def grbl_callback(eventstring, *data):
                    logger.debug(f"CALLBACK: Evento '{eventstring}' recebido com data: {data}") 

                    # Capturar offsets do sistema de coordenadas (G54, G55, etc.)
                    if eventstring == "on_hash_stateupdate":
                        if data and isinstance(data[0], dict):
                            hash_state = data[0]

                            # Processar G54 APENAS se o WCS ativo for G54
                            # Isso evita que a resposta tardia do $# sobrescreva um offset
                            # que foi definido manualmente via G10 L20 para G54.
                            if self.active_wcs == "G54": 
                                g54_offset_data = hash_state.get('G54') 
                                if isinstance(g54_offset_data, (list, tuple)) and len(g54_offset_data) >= 2:
                                    try:
                                        new_offset_x_phys = float(g54_offset_data[0])
                                        new_offset_y_phys = float(g54_offset_data[1])
                                        new_offset_z_phys = float(g54_offset_data[2]) if len(g54_offset_data) > 2 else 0.0

                                        # Converte Y físico → lógico (depende de invert_y)
                                        if self.controller.cnc.invert_y:
                                            new_offset_y_log = -new_offset_y_phys
                                        else:
                                            new_offset_y_log = new_offset_y_phys

                                        self.current_wcs_offset = {
                                            # X e Z permanecem iguais
                                            'x': new_offset_x_phys,
                                            # guardamos FÍSICO para operar com G10 L20.
                                            'y': new_offset_y_phys,
                                            'z': new_offset_z_phys
                                        }

                                        logger.info(
                                            "CALLBACK: Offset G54 atualizado "
                                            f"(físico): {{x:{new_offset_x_phys:.3f}, y:{new_offset_y_phys:.3f}, z:{new_offset_z_phys:.3f}}}; "
                                            f"(lógico Y={new_offset_y_log:.3f})"
                                        )
                                    except (ValueError, TypeError):
                                         logger.error(f"CALLBACK: Erro ao converter offset G54 de $#: {g54_offset_data}")
                                else:
                                    logger.warning(f"CALLBACK: Offset G54 não encontrado ou inválido nos dados hash para WCS ativo G54: {hash_state}")
                            else:
                                logger.debug(f"CALLBACK: Ignorando atualização de offset G54 de $# porque WCS ativo é {self.active_wcs}")
                            # TODO: Se precisar suportar outros WCS (G55-G59), adicionar lógica similar aqui
                
                    # Capturar estado do parser para saber o WCS ativo
                    elif eventstring == "on_gcode_parser_stateupdate":
                        # ... (código existente para atualizar self.active_wcs) ...
                        if data and isinstance(data[0], list) and len(data[0]) > 1:
                            parser_state = data[0]
                            # O índice 1 contém o WCS ativo (ex: "54", "55", etc.)
                            # O índice 0 contém o modo de movimento (ex: "1" para G1)
                            # O índice 4 contém o modo de distância (ex: "90" para G90)
                            new_active_wcs = f"G{parser_state[1]}"
                            new_distance_mode = f"G{parser_state[4]}"

                            if new_active_wcs != self.active_wcs:
                                logger.info(f"CALLBACK: WCS Ativo mudou de {self.active_wcs} para {new_active_wcs}")
                                self.active_wcs = new_active_wcs
                                # Ao mudar o WCS, seria ideal buscar o offset correspondente via $#
                                # ou ter todos os offsets armazenados. Por enquanto, apenas logamos.
                                # self.controller.cnc.grbl.send_immediately("$#") # Cuidado com loops

                            # Atualiza estado interno da aplicação sobre modos G90/G91
                            # Isso garante que a UI e a lógica de movimento estejam sincronizadas
                            # com o estado real do GRBL reportado por $G.
                            if hasattr(self, 'movement_widget'): # Verifica se o widget existe
                                if new_distance_mode == "G90":
                                    if not self.movement_widget.mode_absolute.isChecked():
                                        logger.info("CALLBACK ($G): Sincronizando UI para G90 (Absoluto)")
                                        self.movement_widget.mode_absolute.setChecked(True)
                                        self.movement_widget.mode_relative.setChecked(False)
                                elif new_distance_mode == "G91":
                                     if not self.movement_widget.mode_relative.isChecked():
                                        logger.info("CALLBACK ($G): Sincronizando UI para G91 (Relativo)")
                                        self.movement_widget.mode_absolute.setChecked(False)
                                        self.movement_widget.mode_relative.setChecked(True)
                    
                    elif eventstring == "on_stateupdate":
                        logger.info(f"CALLBACK: Processando 'on_stateupdate'. Dados brutos: {data}") 

                        if len(data) >= 3:
                            state = data[0]
                            mpos_tuple = data[1]  # Posição da Máquina (MPos)
                            # wpos_tuple = data[2] # Posição de Trabalho (WPos) - Ignorando pois está vindo zerado

                            logger.debug(f"CALLBACK DETALHADO: state={state}, mpos={mpos_tuple}") # Removido wpos do log detalhado
                            
                            # Atualiza estado da máquina
                            old_state = self.controller.cnc.machine_status if hasattr(self.controller.cnc, 'machine_status') else None
                            self.controller.cnc.machine_status = state
                            
                            if old_state != state:
                                logger.debug(f"CALLBACK: Estado da máquina mudou de '{old_state}' para '{state}'")
                            
                            # Calcular WPOS a partir de MPOS e do offset armazenado
                            if isinstance(mpos_tuple, (list, tuple)) and len(mpos_tuple) >= 2: 
                                try:
                                    # 1) valores FÍSICOS reportados pelo GRBL
                                    mpos_x_phys = float(mpos_tuple[0])
                                    mpos_y_phys = float(mpos_tuple[1])
                                    mpos_z_phys = float(mpos_tuple[2]) if len(mpos_tuple) > 2 else 0.0

                                    # 2) guarda MPos física para rotinas G10
                                    self.current_mpos = {
                                        'x': mpos_x_phys,
                                        'y': mpos_y_phys,
                                        'z': mpos_z_phys
                                    }

                                    # 3) converte considerando o modo de cinemática
                                    if self.controller.cnc.kinematics_mode == "corexy":
                                        # No modo CoreXY: mpos_x_phys = motor A, mpos_y_phys = motor B
                                        # Converte A,B para coordenadas cartesianas X,Y
                                        x_cart, y_cart = self.controller.cnc._convert_ab_to_xy(mpos_x_phys, mpos_y_phys)

                                        # CORREÇÃO: Converte o offset de coordenadas de motores para cartesianas
                                        off_a = self.current_wcs_offset['x']  # offset motor A
                                        off_b = self.current_wcs_offset['y']  # offset motor B
                                        off_x_cart, off_y_cart = self.controller.cnc._convert_ab_to_xy(off_a, off_b)
                                        off_z_cart = self.current_wcs_offset['z']
                                        
                                        # Aplica inversão lógica se configurada
                                        y_cart_log = -y_cart if self.controller.cnc.invert_y else y_cart
                                        z_cart_log = -mpos_z_phys if self.controller.cnc.invert_z else mpos_z_phys

                                        # Aplica inversão lógica também ao offset para consistência
                                        off_y_cart_log = -off_y_cart if self.controller.cnc.invert_y else off_y_cart
                                        off_z_cart_log = -off_z_cart if self.controller.cnc.invert_z else off_z_cart
                                        
                                        # Agora calcula WPos usando coordenadas cartesianas para ambos
                                        calculated_wpos_x = x_cart - off_x_cart
                                        calculated_wpos_y = y_cart_log - off_y_cart_log
                                        calculated_wpos_z = z_cart_log - off_z_cart_log

                                    else:
                                        # Modo cartesiano (comportamento original)
                                        mpos_y_log = -mpos_y_phys if self.controller.cnc.invert_y else mpos_y_phys
                                        mpos_z_log = -mpos_z_phys if self.controller.cnc.invert_z else mpos_z_phys
                                        off_y_log  = (-self.current_wcs_offset['y']
                                                    if self.controller.cnc.invert_y
                                                    else self.current_wcs_offset['y'])
                                        off_z_log  = (-self.current_wcs_offset['z']
                                                    if self.controller.cnc.invert_z
                                                    else self.current_wcs_offset['z'])
                                        calculated_wpos_x = mpos_x_phys - self.current_wcs_offset['x']
                                        calculated_wpos_y = mpos_y_log  - off_y_log
                                        calculated_wpos_z = mpos_z_log  - off_z_log

                                    new_position = {
                                        'x': calculated_wpos_x,
                                        'y': calculated_wpos_y,
                                        'z': calculated_wpos_z
                                    }

                                    old_position = None
                                    if hasattr(self.controller.cnc, 'current_position'):
                                        old_position = self.controller.cnc.current_position.copy() 
                                        # logger.debug(f"CALLBACK: Posição interna ANTES da atualização: {old_position}") # Log opcional

                                    logger.debug(f"CALLBACK: MPos={mpos_tuple}, Offset={self.current_wcs_offset}, WPos Calculada={new_position}")
                                    logger.debug(f"CALLBACK: Tentando atualizar posição interna (usando WPOS CALCULADA) para: {new_position}")

                                    # Compara new_position (WPos calculada) com old_position
                                    position_changed = (old_position is None) or \
                                                       (abs(old_position['x'] - new_position['x']) > 1e-4) or \
                                                       (abs(old_position['y'] - new_position['y']) > 1e-4) or \
                                                       (abs(old_position.get('z', 0.0) - new_position.get('z', 0.0)) > 1e-4)

                                    if position_changed:
                                        logger.info(f"CALLBACK: POSIÇÃO INTERNA ATUALIZADA (usando WPOS CALCULADA): {old_position} -> {new_position}")
                                        # Atualiza a posição no controlador com a WPos calculada
                                        self.controller.cnc.current_position = new_position 
                                    
                                except (ValueError, TypeError, IndexError) as e:
                                    logger.error(f"CALLBACK: Erro ao processar MPOS ou calcular WPOS: {e}, mpos={mpos_tuple}")
                            else:
                                logger.error(f"CALLBACK: Formato inválido para MPOS: {type(mpos_tuple)}, valor: {mpos_tuple}")

                        else:
                            logger.error(f"CALLBACK: 'on_stateupdate' recebido com dados insuficientes (len={len(data)}). Dados: {data}")

                    # ... (restante do código do callback para outros eventos: on_write, on_read, etc.) ...
                    elif eventstring == "on_write":
                        logger.debug(f"CALLBACK: Comando enviado para GRBL: {data[0] if data else 'vazio'}")
                    # ... (etc.) ...

                # --- INÍCIO DA MODIFICAÇÃO ---
                # Inicializa o GrblStreamer APENAS com o callback
                self.controller.cnc.grbl = GrblStreamer(grbl_callback) 
                # --- FIM DA MODIFICAÇÃO ---

                logger.debug(f"CONEXÃO: Tentando conectar à porta {port} com baudrate 115200")
                # Conecta usando o método cnect()
                self.controller.cnc.grbl.cnect(port, 115200) 
                time.sleep(2.0) 

                if not self.controller.cnc.grbl.connected:
                     logger.error("CONEXÃO: Falha ao estabelecer conexão serial (grbl.connected é False).")
                     raise ConnectionError("Falha ao conectar à porta serial após inicialização.")

                logger.debug("CONEXÃO: Enviando comando de desbloqueio $X")
                self.controller.cnc.grbl.send_immediately("$X")
                time.sleep(0.1) 

                logger.debug("CONEXÃO: Configurando $10=3 para relatório completo de posição")
                self.controller.cnc.grbl.send_immediately("$10=3") # Mantém $10=3 para receber MPos
                time.sleep(0.1)

                # --- INÍCIO DA MODIFICAÇÃO ---
                # Solicitar estado hash logo após conectar para obter offsets
                logger.debug("CONEXÃO: Solicitando estado hash ($#) para obter offsets")
                self.controller.cnc.grbl.send_immediately("$#") 
                time.sleep(0.1)
                # --- FIM DA MODIFICAÇÃO ---

                logger.debug("CONEXÃO: Configurando modo relativo G91")
                self.controller.cnc.grbl.send_immediately("G91")
                time.sleep(0.1)

                logger.debug("CONEXÃO: Iniciando polling de status")
                self.controller.cnc.grbl.poll_start()

                self.controller.cnc.is_connected = True
                self.config.apply_to_cnc(self.controller.cnc)
                self.config.remember_cnc_port(port)
                self.controller.cnc.machine_status = "Idle"  
                self.connect_cnc_btn.setText("Desconectar CNC")
                self.cnc_status.setText("Conectado")
                self.statusBar().showMessage(f"CNC conectada na porta {port}")
                
            except Exception as e:
                # ... (código de tratamento de erro de conexão) ...
                logger.error(f"CONEXÃO: Falha ao conectar ou configurar: {str(e)}", exc_info=True) 
                QMessageBox.critical(self, "Erro", f"Falha ao conectar a CNC: {str(e)}")
                if hasattr(self.controller.cnc, 'grbl') and self.controller.cnc.grbl:
                    try:
                        self.controller.cnc.grbl.disconnect()
                    except: pass
                self.controller.cnc.grbl = None
                self.controller.cnc.is_connected = False
                self.controller.cnc.machine_status = "Erro Conexão"
                self.connect_cnc_btn.setText("Conectar CNC")
                self.cnc_status.setText("Erro Conexão")

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

    def _on_plc_connected(self):
        """
        Handler para quando PLC conecta com sucesso.

        Atualiza:
            - Botão de conexão
            - Label de status
            - Status bar

        Signal origin:
            ConnectionManager.plc_connected
        """
        plc = self.controller.cnc
        self.connect_cnc_btn.setText("Desconectar PLC")
        self.cnc_status.setText("Conectado")
        self.statusBar().showMessage(f"PLC conectado em {plc.host}:{plc.port}")
        logger.info(f"PLC conectado em {plc.host}:{plc.port}")

    def _on_plc_disconnected(self):
        """
        Handler para quando PLC desconecta.

        Atualiza:
            - Botão de conexão
            - Label de status

        Signal origin:
            ConnectionManager.plc_disconnected
        """
        self.connect_cnc_btn.setText("Conectar PLC")
        self.cnc_status.setText("Desconectado")
        logger.info("PLC desconectado")

    def _on_plc_error(self, error: str):
        """
        Handler para erros de conexão PLC.

        Atualiza:
            - Label de status
            - Mostra QMessageBox ao usuário

        Signal origin:
            ConnectionManager.plc_connection_error
        """
        self.cnc_status.setText("Erro")
        QMessageBox.warning(
            self,
            "Erro de Conexão",
            f"Não foi possível conectar ao PLC:\n{error}"
        )
        logger.error(f"Erro de conexão PLC: {error}")

    def connect_camera(self):
        """Conecta à câmera"""
        if hasattr(self.controller.camera, 'is_connected') and self.controller.camera.is_connected:
            # Interrompe preview antes de liberar a câmera
            self.camera_preview.stop_preview()

            # Desconectar
            self.controller.camera.disconnect()
            self.connect_camera_btn.setText("Conectar Câmera")
            self.statusBar().showMessage("Câmera desconectada")
        else:
            # Conectar
            # Conectar
            try:
                # Obtém texto do combo (pode ser número ou URL)
                id_text = self.camera_id_combo.currentText().strip()
                
                # Tenta converter para int se for numérico
                if id_text.isdigit():
                    camera_id = int(id_text)
                else:
                    camera_id = id_text
                
                self.statusBar().showMessage(f"Conectando à câmera {camera_id}...")
                
                if self.controller.connect_camera(camera_id):
                    self.connect_camera_btn.setText("Desconectar Câmera")
                    self.statusBar().showMessage(f"Câmera {camera_id} conectada")
                    self.config.remember_camera_id(camera_id)
                else:
                    QMessageBox.critical(self, "Erro", f"Falha ao conectar à câmera: {self.controller.camera.last_error}")
            except Exception as e:
                QMessageBox.warning(self, "Erro", f"Erro ao conectar câmera: {e}")
                
    def test_camera(self):
        """Testa a captura de imagem da câmera"""
        if not hasattr(self.controller.camera, 'is_connected') or not self.controller.camera.is_connected:
            QMessageBox.warning(self, "Aviso", "Câmera não conectada")
            return
            
        image = self.controller.camera.capture()
        
        if image is not None:
            # Usa o widget de preview da câmera para exibir a imagem
            self.camera_preview.display_image(image)
            self.statusBar().showMessage("Imagem de teste capturada com sucesso")
        else:
            error_msg = getattr(self.controller.camera, 'last_error', 'Erro desconhecido')
            QMessageBox.warning(self, "Erro", f"Falha ao capturar imagem: {error_msg}")
            
    def update_position_display(self): 
        """Atualiza a exibição da posição atual (agora exibindo WPos calculada)""" 
        if not self.controller.cnc.is_connected: 
            # logger.debug("update_position_display: CNC não conectada.") # Log já existente
            return 
        try: 
            # get_current_position agora retorna a WPos calculada
            position = self.controller.cnc.get_current_position() 
            # logger.debug("update_position_display: posição (WPos calculada) obtida do CNC: %s", position) 
        except Exception as e: 
            logger.error("update_position_display: erro ao obter posição: %s", e) 
            return

        # Comparação para log (opcional, pode ser removido se poluir muito)
        if self.last_logged_position is not None:
            if position == self.last_logged_position:
                pass
                # logger.warning("update_position_display: posição (WPos calculada) inalterada: %s", position)
            else:
                # logger.debug("update_position_display: posição (WPos calculada) mudou de %s para %s", 
                #             self.last_logged_position, position)
                pass
        else:
            #logger.debug("update_position_display: nenhuma posição (WPos calculada) anterior registrada.")
            pass
        
        self.last_logged_position = position.copy()

        # Atualiza os labels da interface com a WPos calculada
        self.x_position.setText(f"{position['x']:.3f} mm")
        self.y_position.setText(f"{position['y']:.3f} mm")
        # -------- NOVO: eixo Z ----------
        if hasattr(self, "z_position"):
            self.z_position.setText(f"{position['z']:.3f} mm")
        self.cnc_status.setText(self.controller.cnc.machine_status)
        
    def add_current_position(self):
        """Adiciona a posição atual à lista"""
        if not self.controller.cnc.is_connected:
            QMessageBox.warning(self, "Aviso", "CNC não conectada")
            return
            
        position_name, ok = QInputDialog.getText(self, "Nova Posição", "Nome da posição:")
        
        if ok and position_name:
            position = self.controller.add_current_position(position_name)
            self.position_list_widget.add_position(position)
            self.statusBar().showMessage(f"Posição '{position_name}' adicionada")
            
    def remove_position(self):
        """Remove a posição selecionada"""
        position = self.position_list_widget.remove_selected_position()
        
        if position:
            self.controller.position_manager.remove_position(position.name)
            self.statusBar().showMessage(f"Posição '{position.name}' removida")
            
    def on_position_selected(self, position):
        """Manipula a seleção de uma posição"""
        # Poderia mover para esta posição, mostrar detalhes, etc.
        self.statusBar().showMessage(f"Posição selecionada: {position.name} ({position.x:.3f}, {position.y:.3f})")
        
    def create_sequence(self):
        """Cria uma nova sequência com as posições atuais"""
        positions = self.position_list_widget.get_all_positions()
        
        if not positions:
            QMessageBox.warning(self, "Aviso", "Adicione pelo menos uma posição")
            return
            
        sequence_name = self.sequence_widget.sequence_name.text()
        if not sequence_name:
            QMessageBox.warning(self, "Aviso", "Digite um nome para a sequência")
            return
            
        self.current_sequence = self.controller.create_sequence(sequence_name, positions)
        self.statusBar().showMessage(f"Sequência '{sequence_name}' criada com {len(positions)} posições")
        self.sequence_widget.sequence_status.setText(f"Criada: {len(positions)} posições")
        
    def run_sequence(self):
        """Executes the current sequence"""
        if not self.current_sequence:
            QMessageBox.warning(self, "Warning", "Create a sequence first")
            return
            
        if not self.controller.cnc.is_connected:
            QMessageBox.warning(self, "Warning", "CNC not connected")
            return
            
        if not hasattr(self.controller.camera, 'is_connected') or not self.controller.camera.is_connected:
            QMessageBox.warning(self, "Warning", "Camera not connected")
            return
            
        # Clear previous results
        self.results_table.setRowCount(0)
        
        # Configure UI for execution
        self.is_running_sequence = True
        self.sequence_widget.run_sequence_btn.setEnabled(False)
        self.sequence_widget.stop_sequence_btn.setEnabled(True)
        self.sequence_widget.sequence_status.setText("Executing...")
        
        # Start execution
        try:
            self.statusBar().showMessage(f"Executing sequence '{self.current_sequence.name}'...")
            # Configura velocidade no controlador baseada na interface
            self.controller.set_feed_rate(self.movement_widget.get_current_feed_rate())
            
            # Use a thread to run the sequence
            self.run_thread = SequenceRunnerThread(self.controller, self.current_sequence.name)
            self.run_thread.image_captured.connect(self.on_sequence_image_captured)
            self.run_thread.sequence_completed.connect(self.on_sequence_completed)
            self.run_thread.sequence_error.connect(self.on_sequence_error)
            self.run_thread.start()
            
        except Exception as e:
            self.statusBar().showMessage(f"Error executing sequence: {str(e)}")
            self.sequence_widget.sequence_status.setText("Error")
            self.on_sequence_completed()

    def on_sequence_image_captured(self, result):
        """Called when an image is captured during sequence execution"""
        position = result["position"]
        image = result["image"]
        timestamp = result["timestamp"]
        
        # Display the image on the existing camera_preview widget
        self.camera_preview.display_image(image)
        # Atualiza a status bar com o nome/posição
        self.statusBar().showMessage(
            f"Position captured: {position.name} ({position.x:.3f}, {position.y:.3f})"
        )
        
        # Add to results table
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        self.results_table.setItem(row, 0, QTableWidgetItem(position.name))
        self.results_table.setItem(row, 1, QTableWidgetItem(time.strftime("%H:%M:%S", time.localtime(timestamp))))
        self.results_table.setItem(row, 2, QTableWidgetItem("Captured"))
            
    def stop_sequence(self):
        """Para a execução da sequência atual"""
        if self.is_running_sequence:
            self.controller.stop_sequence()
            self.statusBar().showMessage("Execução de sequência interrompida")
            self.on_sequence_completed()
        
    def on_sequence_completed(self):
        """Chamado quando a execução da sequência é concluída"""
        self.is_running_sequence = False
        self.sequence_widget.run_sequence_btn.setEnabled(True)
        self.sequence_widget.stop_sequence_btn.setEnabled(False)
        self.sequence_widget.sequence_status.setText("Concluída")
        self.statusBar().showMessage("Execução de sequência concluída")
        
    def on_sequence_error(self, error_message):
        """Chamado quando ocorre um erro durante a execução da sequência"""
        QMessageBox.critical(self, "Erro na Sequência", error_message)
        self.on_sequence_completed()
        
    def save_program(self):
        """Salva o programa de inspeção atual"""
        if not self.current_sequence:
            QMessageBox.warning(self, "Aviso", "Crie uma sequência primeiro")
            return
            
        filename, _ = QFileDialog.getSaveFileName(self, "Salvar Programa", "", "Arquivos JSON (*.json)")
        
        if filename:
            if not filename.endswith('.json'):
                filename += '.json'
                
            if self.controller.save_positions(filename):
                self.statusBar().showMessage(f"Programa salvo em {filename}")
            else:
                QMessageBox.critical(self, "Erro", "Falha ao salvar o programa")
                
    def load_program(self):
        """Carrega um programa de inspeção salvo"""
        filename, _ = QFileDialog.getOpenFileName(self, "Carregar Programa", "", "Arquivos JSON (*.json)")
        
        if filename:
            if self.controller.load_positions(filename):
                # Atualiza a interface
                self.position_list_widget.clear_positions()
                
                # Adiciona posições carregadas à lista
                for name, position in self.controller.position_manager.positions.items():
                    self.position_list_widget.add_position(position)
                    
                # Se há sequências, usa a primeira como atual
                if self.controller.position_manager.sequences:
                    sequence_name = next(iter(self.controller.position_manager.sequences))
                    self.current_sequence = self.controller.position_manager.sequences[sequence_name]
                    self.sequence_widget.sequence_name.setText(sequence_name)
                    self.sequence_widget.sequence_status.setText(f"Carregada: {len(self.current_sequence.positions)} posições")
                    
                self.statusBar().showMessage(f"Programa carregado de {filename}")
            else:
                QMessageBox.critical(self, "Erro", "Falha ao carregar o programa")

    # ========== MAPCONTROLLER SIGNAL HANDLERS ==========

    def _on_map_program_saved(self, name, path):
        """Handler quando um programa de mapa é salvo."""
        logger.info(f"Programa de mapa salvo: {name} -> {path}")
        self.statusBar().showMessage(f"Programa '{name}' salvo com sucesso", 3000)

    def _on_map_program_loaded(self, name, params):
        """Handler quando um programa de mapa é carregado."""
        logger.info(f"Programa de mapa carregado: {name}")
        self.statusBar().showMessage(f"Programa '{name}' carregado", 3000)

    def _on_map_program_deleted(self, name):
        """Handler quando um programa de mapa é excluído."""
        logger.info(f"Programa de mapa excluído: {name}")
        self.statusBar().showMessage(f"Programa '{name}' excluído", 3000)

    def _on_map_generated(self, mosaic_path):
        """Handler quando geração de mapa é completada."""
        logger.info(f"Mosaico gerado: {mosaic_path}")
        self.statusBar().showMessage(f"Mosaico gerado com sucesso", 5000)
        QMessageBox.information(
            self, "Mosaico Gerado",
            f"O mosaico foi gerado com sucesso!\n\n"
            f"Arquivo: {mosaic_path}"
        )

    def _on_map_progress(self, current, total, message):
        """Handler durante progresso da geração do mapa."""
        logger.debug(f"Progresso do mapa: {current}/{total} - {message}")

    def _on_map_error(self, error_message):
        """Handler quando ocorre erro na geração do mapa."""
        logger.error(f"Erro no mapa: {error_message}")
        QMessageBox.critical(self, "Erro na Geração do Mapa", error_message)

    # ========== CAMERASETTINGSCONTROLLER SIGNAL HANDLERS ==========

    def _on_camera_settings_changed(self, settings):
        """Handler quando configurações de câmera são alteradas."""
        logger.debug(f"Configurações de câmera alteradas: {settings}")

    def _on_camera_settings_applied(self, settings):
        """Handler quando configurações de câmera são aplicadas."""
        logger.info(f"Configurações de câmera aplicadas")

        # Atualiza variáveis internas
        self._camera_mirror_x = settings.get('mirror_x', False)
        self._camera_mirror_y = settings.get('mirror_y', False)

        # Aplica ao preview se disponível
        if hasattr(self, 'cnc_tab') and hasattr(self.cnc_tab, 'camera_preview'):
            self.cnc_tab.camera_preview.set_mirror(self._camera_mirror_x, self._camera_mirror_y)

        self.statusBar().showMessage("Configurações de câmera aplicadas", 3000)

    def _on_camera_settings_saved(self, preset_name):
        """Handler quando preset de câmera é salvo."""
        logger.info(f"Preset de câmera salvo: {preset_name}")
        self.statusBar().showMessage(f"Preset '{preset_name}' salvo", 3000)

    def _on_camera_settings_loaded(self, preset_name):
        """Handler quando preset de câmera é carregado."""
        logger.info(f"Preset de câmera carregado: {preset_name}")
        self.statusBar().showMessage(f"Preset '{preset_name}' carregado", 3000)

    # ========== CALIBRATIONCONTROLLER SIGNAL HANDLERS ==========

    def _on_calibration_applied(self, steps_x, steps_y):
        """Handler quando calibração é aplicada."""
        logger.info(f"Calibração aplicada: X={steps_x} steps/mm, Y={steps_y} steps/mm")

        # Atualiza configurações
        self.config.set("connections", "pulses_per_rev", int(steps_x * 10))  # Converte para pulses por revolução
        self.config.set("connections", "fuso_pitch", 10.0)  # Assume fuso de 10mm
        self.config.save()

        self.statusBar().showMessage(f"Calibração aplicada: {steps_x:.2f} x {steps_y:.2f} steps/mm", 3000)

    def _on_calibration_completed(self):
        """Handler quando calibração é completada."""
        logger.info("Calibração completada")
        self.statusBar().showMessage("Calibração completada com sucesso", 3000)

    def _on_calibration_test_completed(self, movement_ok, message):
        """Handler quando teste de calibração é completado."""
        status = "OK" if movement_ok else "FALHOU"
        logger.info(f"Teste de calibração: {status} - {message}")

        if movement_ok:
            QMessageBox.information(self, "Teste de Calibração", f"Teste concluído com sucesso!\n\n{message}")
        else:
            QMessageBox.warning(self, "Teste de Calibração", f"Teste falhou!\n\n{message}")

        self.statusBar().showMessage(f"Teste de calibração: {status}", 3000)

    #  LIMPEZA GERAL  (Threads, Timers, Dispositivos)
    def _cleanup_resources(self):
        """Para tudo que possa manter o Qt vivo após o fechamento."""
        if getattr(self, "_already_clean", False):
            return                         # evita executar 2×
        self._already_clean = True

        # 1) Sequências em execução
        if getattr(self, "is_running_sequence", False):
            self.controller.stop_sequence()

        # 2) Timers ------------------------------------------------
        for tm_name in ("update_timer",):
            tm = getattr(self, tm_name, None)
            if tm and tm.isActive():
                tm.stop()
        if getattr(self, "camera_preview", None):
            self.camera_preview.stop_preview()

        # 3) QThreads ---------------------------------------------
        for th_name in ("run_thread", "map_thread", "_move_thread"):
            th = getattr(self, th_name, None)
            if th and th.isRunning():
                th.requestInterruption()
                th.quit()
                th.wait(2000)             # aguarda até 2 s

        # 4) Thread de status do GRBL dentro do controlador CNC
        if getattr(self.controller.cnc, "running", False):
            self.controller.cnc.running = False
            if getattr(self.controller.cnc, "status_thread", None):
                self.controller.cnc.status_thread.join(timeout=2)

        # 5) grbl-streamer (poll thread) --------------------------
        if getattr(self.controller.cnc, "grbl", None):
            try:
                self.controller.cnc.grbl.poll_stop()
                self.controller.cnc.grbl.disconnect()   # fecha serial + join
            except Exception:
                pass

        # 6) Dispositivos -----------------------------------------
        if getattr(self.controller.camera, "is_connected", False):
            self.controller.camera.disconnect()
        if getattr(self.controller.cnc, "is_connected", False):
            self.controller.cnc.disconnect()

    # closeEvent agora só dispara a limpeza
    def closeEvent(self, event):
        self._cleanup_resources()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AOIControllerApp()
    window.show()
    sys.exit(app.exec())
