import sys
import cv2
import os
import time
from pathlib import Path
from typing import Optional
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
from aoi_lib.report_settings_dialog import ReportSettingsDialog
from aoi_lib.stencil_inspector import StencilInspector, InspectionThresholds, InspectionResult
from aoi_lib.inspection_settings_dialog import InspectionSettingsDialog
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

        # =========== GERENCIADOR DE CONEXÕES ===========
        self.connection_mgr = ConnectionManager(self.controller, self.config)
        # Conectar signals do ConnectionManager
        self.connection_mgr.plc_connected.connect(self._on_plc_connected)
        self.connection_mgr.plc_disconnected.connect(self._on_plc_disconnected)
        self.connection_mgr.plc_connection_error.connect(self._on_plc_error)

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
        # Configuração do menu
        self.setup_menu()

        # -------- Painel de conexão inicialmente oculto -------
        self.connection_group.setVisible(False)

        # -------- Auto-connect se preferido --------------------
        
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

        # Capturar eventos de teclado para movimentação de qualquer widget:
        # instala o filter globalmente apenas UMA vez
        QApplication.instance().installEventFilter(self)

        # chama cleanup se o Qt encerrar por outros caminhos
        QApplication.instance().aboutToQuit.connect(self._cleanup_resources)

    #   Auto-connect com base no JSON de prefs
    def _attempt_auto_connect(self):
        """Tenta conexão automática ao PLC e câmera ao iniciar a aplicação."""

        # ========== CONEXÃO AUTOMÁTICA AO PLC ==========
        # Delega para ConnectionManager
        if isinstance(self.controller.cnc, PLCAxisController):
            plc = self.controller.cnc
            self.statusBar().showMessage(f"Tentando conexão automática ao PLC em {plc.host}:{plc.port}...")
            QApplication.processEvents()  # Atualiza a UI

            # Tenta conexão automática se configurado
            self.connection_mgr.attempt_auto_connect()
        
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

    def eventFilter(self, source, event):
        """
        Intercepta eventos de teclado e dispara start/stop de movimento
        se a opção estiver habilitada.
        """
        # KeyPress
        if event.type() == QEvent.Type.KeyPress and self.movement_widget.keyboard_control_checkbox.isChecked():
            if hasattr(event, 'isAutoRepeat') and event.isAutoRepeat():
                return True
            key = event.key()
            if key == Qt.Key.Key_Up:
                self.movement_widget.start_movement("Y", -1)
                return True
            elif key == Qt.Key.Key_Down:
                self.movement_widget.start_movement("Y", 1)
                return True
            elif key == Qt.Key.Key_Left:
                self.movement_widget.start_movement("X", -1)
                return True
            elif key == Qt.Key.Key_Right:
                self.movement_widget.start_movement("X", 1)
                return True
            elif key == Qt.Key.Key_PageUp:
                 self.movement_widget.start_movement("Z", -1)
                 return True
            elif key == Qt.Key.Key_PageDown:
                 self.movement_widget.start_movement("Z", 1)
                 return True
        # KeyRelease
        elif event.type() == QEvent.Type.KeyRelease and self.movement_widget.keyboard_control_checkbox.isChecked():
            if hasattr(event, 'isAutoRepeat') and event.isAutoRepeat():
                return True
            key = event.key()
            if key in (
                Qt.Key.Key_Up, 
                Qt.Key.Key_Down, 
                Qt.Key.Key_Left, 
                Qt.Key.Key_Right,
                Qt.Key.Key_PageUp,
                Qt.Key.Key_PageDown
            ):
                self.movement_widget.stop_movement()
                return True
        return super().eventFilter(source, event)

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
        self.apply_calibration_btn.clicked.connect(self.apply_calibration)

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
        
        # Painel direito: aba para Câmera & Movimento e Visualização de Tensão
        right_panel = QTabWidget()
        # guardamos para habilitar/desabilitar abas depois
        self.right_panel = right_panel
        
        # MOVER PARA AQUI: Adicionar a aba de Câmera & Movimento (após definir right_panel)
        # Tab para Camera & Movement
        camera_movement_tab = QWidget()
        camera_movement_layout = QHBoxLayout(camera_movement_tab)
        
        # Left side: controls and position registry
        cm_left_panel = QWidget()
        cm_left_layout = QVBoxLayout(cm_left_panel)
        
        # Movement controls 
        self.movement_widget = MovementControlWidget(self.controller, self.config)
        cm_left_layout.addWidget(self.movement_widget)
        
        # Right side: camera preview
        self.camera_preview = CameraPreviewWidget(self.controller, self.config)
        self.camera_preview.image_captured.connect(self.on_image_captured)
        
        # Inverter colunas: preview à esquerda (mais espaço) e controles à direita
        camera_movement_layout.addWidget(self.camera_preview, 3)      # Proporção 3 (preview)
        camera_movement_layout.addWidget(cm_left_panel, 1)            # Proporção 1 (controles)
        
        # Agora é seguro adicionar a nova aba ao right_panel que já foi definido
        right_panel.addTab(camera_movement_tab, "Câmera & Movimento")

        # Aba de monitoramento do CLP (endereços Modbus)
        self.plc_monitor = PLCMonitorWidget(self.controller)
        right_panel.addTab(self.plc_monitor, "Monitor CLP")

        # Aba de Visualização de Tensão
        self.tension_visualization = TensionVisualizationWidget()
        right_panel.addTab(self.tension_visualization, "Visualização de Tensão")
        
        # ================== ABA DE RASTREABILIDADE ==================
        stencil_tab = QWidget()
        stencil_layout = QVBoxLayout(stencil_tab)
        
        # Widget de identificação de stencil
        self.stencil_identification = StencilIdentificationWidget(
            self.stencil_tracker, 
            parent=self
        )
        # Conecta sinais
        self.stencil_identification.stencil_selected.connect(self._on_stencil_selected)
        self.stencil_identification.stencil_cleared.connect(self._on_stencil_cleared)
        self.stencil_identification.recipe_requested.connect(self._on_recipe_requested)
        
        stencil_layout.addWidget(self.stencil_identification)
        
        # Botões de ação rápida
        action_group = QGroupBox("⚡ Ações Rápidas")
        action_layout = QHBoxLayout(action_group)
        
        self.btn_run_tension = QPushButton("📐 Medir Tensão")
        self.btn_run_tension.setEnabled(False)
        self.btn_run_tension.clicked.connect(self._run_tension_measurement)
        self.btn_run_tension.setToolTip("Executa medição de tensão e salva no histórico do stencil")
        action_layout.addWidget(self.btn_run_tension)
        
        self.btn_manage_stencils = QPushButton("📋 Gerenciar Stencils")
        self.btn_manage_stencils.clicked.connect(self.show_stencil_manager)
        action_layout.addWidget(self.btn_manage_stencils)
        
        self.btn_new_stencil = QPushButton("➕ Novo Stencil")
        self.btn_new_stencil.clicked.connect(self.show_new_stencil_dialog)
        action_layout.addWidget(self.btn_new_stencil)
        
        stencil_layout.addWidget(action_group)
        
        # Espaço para futuras expansões (inspeção visual, etc.)
        stencil_layout.addStretch()
        
        right_panel.addTab(stencil_tab, "🏷️ Rastreabilidade")
        
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
        """Configura o menu da aplicação"""
        menubar = self.menuBar()
        
        # Menu de Arquivo
        file_menu = menubar.addMenu('&Arquivo')
        
        exit_action = QAction('Sair', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # =========== MENU DE RECEITAS ===========
        recipes_menu = menubar.addMenu('&Receitas')
        
        # Gerenciador de Receitas
        manage_recipes_action = QAction('📋 Gerenciar Receitas...', self)
        manage_recipes_action.setShortcut('Ctrl+R')
        manage_recipes_action.triggered.connect(self.show_recipe_manager)
        recipes_menu.addAction(manage_recipes_action)
        
        # Nova Receita
        new_recipe_action = QAction('➕ Nova Receita...', self)
        new_recipe_action.triggered.connect(self.show_new_recipe_dialog)
        recipes_menu.addAction(new_recipe_action)
        
        recipes_menu.addSeparator()
        
        # Receita Atual
        self.current_recipe_action = QAction('(Nenhuma receita carregada)', self)
        self.current_recipe_action.setEnabled(False)
        recipes_menu.addAction(self.current_recipe_action)
        
        # Aplicar à Captura
        apply_to_capture_action = QAction('🔄 Aplicar Receita à Captura', self)
        apply_to_capture_action.triggered.connect(self.apply_recipe_to_capture)
        recipes_menu.addAction(apply_to_capture_action)
        
        # Aplicar à Tensão
        apply_to_tension_action = QAction('🔄 Aplicar Receita à Tensão', self)
        apply_to_tension_action.triggered.connect(self.apply_recipe_to_tension)
        recipes_menu.addAction(apply_to_tension_action)
        
        # =========== MENU DE STENCILS ===========
        stencils_menu = menubar.addMenu('&Stencils')
        
        # Gerenciador de Stencils
        manage_stencils_action = QAction('📋 Gerenciar Stencils...', self)
        manage_stencils_action.setShortcut('Ctrl+T')
        manage_stencils_action.triggered.connect(self.show_stencil_manager)
        stencils_menu.addAction(manage_stencils_action)
        
        # Novo Stencil
        new_stencil_action = QAction('➕ Novo Stencil...', self)
        new_stencil_action.triggered.connect(self.show_new_stencil_dialog)
        stencils_menu.addAction(new_stencil_action)
        
        stencils_menu.addSeparator()
        
        # Stencil Atual
        self.current_stencil_action = QAction('(Nenhum stencil selecionado)', self)
        self.current_stencil_action.setEnabled(False)
        stencils_menu.addAction(self.current_stencil_action)
        
        # =========== MENU DE RELATÓRIOS ===========
        reports_menu = menubar.addMenu('&Relatórios')
        
        # Gerar Relatório de Tensão
        tension_report_action = QAction('📄 Relatório de Tensão...', self)
        tension_report_action.setShortcut('Ctrl+P')
        tension_report_action.setToolTip('Gera relatório PDF da última medição de tensão')
        tension_report_action.triggered.connect(self.show_tension_report_dialog)
        reports_menu.addAction(tension_report_action)
        
        # Relatório do Stencil
        stencil_report_action = QAction('📋 Relatório do Stencil...', self)
        stencil_report_action.setToolTip('Gera relatório PDF do histórico do stencil selecionado')
        stencil_report_action.triggered.connect(self.show_stencil_report_dialog)
        reports_menu.addAction(stencil_report_action)
        
        reports_menu.addSeparator()
        
        # Consultar por Período
        period_report_action = QAction('📅 Consultar por Período...', self)
        period_report_action.triggered.connect(self.show_period_query_dialog)
        reports_menu.addAction(period_report_action)
        
        reports_menu.addSeparator()
        
        # Configurações de Relatório
        report_settings_action = QAction('⚙️ Configurações de Relatório...', self)
        report_settings_action.triggered.connect(self.show_report_settings)
        reports_menu.addAction(report_settings_action)
        
        # Menu de Ferramentas
        tools_menu = menubar.addMenu('&Ferramentas')

        # ação para definir mapa
        definir_mapa_action = QAction('Definir Mapa', self)
        definir_mapa_action.triggered.connect(self.show_definir_mapa_dialog)
        tools_menu.addAction(definir_mapa_action)

        # Ação para abrir o Mosaic Builder
        mosaic_action = QAction('Montar Mosaico de Imagens', self)
        mosaic_action.triggered.connect(self.show_mosaic_builder)
        tools_menu.addAction(mosaic_action)

        tools_menu.addSeparator()
        
        calibration_action = QAction('Calibração CNC', self)
        calibration_action.triggered.connect(self.show_calibration_dialog)
        tools_menu.addAction(calibration_action)

        # Calibração de Câmera (correção de distorção)
        camera_calib_action = QAction('Calibração de Câmera (Distorção)', self)
        camera_calib_action.triggered.connect(self.show_camera_calibration_dialog)
        tools_menu.addAction(camera_calib_action)

        # Configurações de Câmera
        camera_settings_action = QAction('Configurações de Câmera', self)
        camera_settings_action.triggered.connect(self.show_camera_settings_dialog)
        tools_menu.addAction(camera_settings_action)

        # Calibração de Campo de Visão (FOV) - para movimento por clique
        fov_calib_action = QAction('📐 Calibração de FOV (Campo de Visão)', self)
        fov_calib_action.setToolTip('Configura a relação pixel↔mm para movimento por clique no vídeo')
        fov_calib_action.triggered.connect(self.show_fov_calibration_dialog)
        tools_menu.addAction(fov_calib_action)

        # Configurações da Cruz de Centralização
        crosshair_action = QAction('✛ Configurar Cruz de Centralização', self)
        crosshair_action.setToolTip('Ajusta cor, espessura e comprimento da cruz central')
        crosshair_action.triggered.connect(self.show_crosshair_settings_dialog)
        tools_menu.addAction(crosshair_action)

        # Alinhamento de Fiduciais (para inspeção visual)
        fiducial_action = QAction('🎯 Alinhamento de Fiduciais', self)
        fiducial_action.setToolTip('Abre ferramenta de alinhamento Gerber ↔ Imagem usando fiduciais')
        fiducial_action.setShortcut('Ctrl+F')
        fiducial_action.triggered.connect(self.show_fiducial_alignment_dialog)
        tools_menu.addAction(fiducial_action)

        tools_menu.addSeparator()

        # Preferências
        pref_action = QAction('Preferências', self)
        pref_action.setShortcut('Ctrl+,')
        pref_action.triggered.connect(self.show_settings_dialog)
        tools_menu.addAction(pref_action)

        # ---------------------------------------------------------------
        # Item de menu "Tensão do Stencil" – abre o diálogo de medição
        # ---------------------------------------------------------------
        tension_action = QAction('Tensão do Stencil', self)
        tension_action.triggered.connect(self.open_stencil_tension_dialog)
        menubar.addAction(tension_action)

        # =========== MENU DE INSPEÇÃO VISUAL ===========
        inspection_menu = menubar.addMenu('&Inspeção Visual')
        
        # Executar Inspeção
        run_inspection_action = QAction('🔬 Executar Inspeção...', self)
        run_inspection_action.setShortcut('Ctrl+I')
        run_inspection_action.setToolTip('Executa inspeção visual comparando mosaico com Gerber')
        run_inspection_action.triggered.connect(self.show_inspection_dialog)
        inspection_menu.addAction(run_inspection_action)
        
        # Visualizar Último Resultado
        view_result_action = QAction('📊 Visualizar Último Resultado', self)
        view_result_action.triggered.connect(self.show_last_inspection_result)
        inspection_menu.addAction(view_result_action)
        
        inspection_menu.addSeparator()
        
        # Configurações de Inspeção
        inspection_settings_action = QAction('⚙️ Parâmetros de Inspeção...', self)
        inspection_settings_action.triggered.connect(self.show_inspection_settings)
        inspection_menu.addAction(inspection_settings_action)

        # --------  painel de conexões -----------------
        conn_panel = QAction('Conexões…', self)
        conn_panel.setCheckable(True)
        conn_panel.setChecked(False)
        conn_panel.triggered.connect(
            lambda checked: self.connection_group.setVisible(checked)
        )
        tools_menu.addAction(conn_panel)
        
        # Menu de Ajuda
        help_menu = menubar.addMenu('&Ajuda')
        
        about_action = QAction('Sobre', self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

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
        from aoi_lib.crosshair_settings import CrosshairSettingsDialog
        
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


    def show_camera_settings_dialog(self):
        """Abre diálogo para configurações de câmera"""
        if not hasattr(self.controller.camera, 'is_connected') or not self.controller.camera.is_connected:
            QMessageBox.warning(self, "Aviso", "Conecte a câmera antes de ajustar as configurações.")
            return
        
        # Obtém o objeto VideoCapture
        cap = self.controller.camera.camera  # O atributo 'camera' do CameraController é o VideoCapture
        if cap is None:
            QMessageBox.warning(self, "Erro", "Câmera não disponível.")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Configurações de Câmera")
        dialog.setMinimumWidth(500)
        
        layout = QVBoxLayout(dialog)
        
        from PyQt6.QtWidgets import QSlider
        from PyQt6.QtWidgets import QLineEdit, QGroupBox as QGB
        from PyQt6.QtWidgets import QHBoxLayout as QHL, QVBoxLayout as QVL
        from PyQt6.QtWidgets import QPushButton as QPB
        # guarda referência ao cap para aplicar em bloco
        self._camera_cap_ref = cap
        # Valores salvos para foco
        saved_focus = self.config.get("camera", "focus", default=0)
        saved_auto_focus = self.config.get("camera", "auto_focus", default=True)
        
        # ============== ESPELHAMENTO ==============
        mirror_group = QGroupBox("Espelhamento da Imagem")
        mirror_layout = QHBoxLayout(mirror_group)
        
        self.chk_mirror_x = QCheckBox("Espelhar Horizontalmente (X)")
        # Carrega do config ou usa atributo local
        saved_mirror_x = self.config.get("camera", "mirror_x", default=False)
        self._camera_mirror_x = getattr(self, '_camera_mirror_x', saved_mirror_x)
        self.chk_mirror_x.setChecked(self._camera_mirror_x)
        mirror_layout.addWidget(self.chk_mirror_x)
        
        self.chk_mirror_y = QCheckBox("Espelhar Verticalmente (Y)")
        saved_mirror_y = self.config.get("camera", "mirror_y", default=False)
        self._camera_mirror_y = getattr(self, '_camera_mirror_y', saved_mirror_y)
        self.chk_mirror_y.setChecked(self._camera_mirror_y)
        mirror_layout.addWidget(self.chk_mirror_y)
        
        layout.addWidget(mirror_group)
        
        # ============== AJUSTES DE IMAGEM ==============
        settings_group = QGroupBox("Ajustes de Imagem")
        settings_layout = QGridLayout(settings_group)
        
        # Função para criar slider com label
        def create_slider_row(row, label, prop_id, min_val, max_val, default, scale=1.0):
            settings_layout.addWidget(QLabel(f"{label}:"), row, 0)
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(min_val, max_val)
            
            # Tenta ler valor atual
            try:
                current = cap.get(prop_id)
                if current != -1 and current != 0:
                    slider.setValue(int(current * scale))
                else:
                    slider.setValue(default)
            except:
                slider.setValue(default)
            
            lbl = QLabel(str(slider.value()))
            slider.valueChanged.connect(lambda v: lbl.setText(str(v)))
            slider.valueChanged.connect(lambda v: self._apply_camera_prop(cap, prop_id, v / scale))
            
            settings_layout.addWidget(slider, row, 1)
            settings_layout.addWidget(lbl, row, 2)
            return slider
        
        # Brilho (0-255 na maioria das câmeras)
        self.slider_brightness = create_slider_row(0, "Brilho", cv2.CAP_PROP_BRIGHTNESS, 0, 255, 128, 1.0)
        
        # Contraste (0-255)
        self.slider_contrast = create_slider_row(1, "Contraste", cv2.CAP_PROP_CONTRAST, 0, 255, 128, 1.0)
        
        # Saturação (0-255)
        self.slider_saturation = create_slider_row(2, "Saturação", cv2.CAP_PROP_SATURATION, 0, 255, 128, 1.0)
        
        # Exposição (-13 a 0 para câmeras USB típicas)
        settings_layout.addWidget(QLabel("Exposição:"), 3, 0)
        self.slider_exposure = QSlider(Qt.Orientation.Horizontal)
        self.slider_exposure.setRange(-13, 0)
        try:
            exp = int(cap.get(cv2.CAP_PROP_EXPOSURE))
            self.slider_exposure.setValue(exp if -13 <= exp <= 0 else -6)
        except:
            self.slider_exposure.setValue(-6)
        self.lbl_exposure = QLabel(str(self.slider_exposure.value()))
        self.slider_exposure.valueChanged.connect(lambda v: self.lbl_exposure.setText(str(v)))
        self.slider_exposure.valueChanged.connect(lambda v: self._apply_camera_prop(cap, cv2.CAP_PROP_EXPOSURE, v))
        settings_layout.addWidget(self.slider_exposure, 3, 1)
        settings_layout.addWidget(self.lbl_exposure, 3, 2)
        
        # Ganho (0-255)
        self.slider_gain = create_slider_row(4, "Ganho", cv2.CAP_PROP_GAIN, 0, 255, 128, 1.0)

        # Foco (0-255)
        self.slider_focus = create_slider_row(5, "Foco", cv2.CAP_PROP_FOCUS, 0, 255, saved_focus, 1.0)
        def _on_focus_change(v):
            # Se usuário mexeu no foco, desliga auto-foco e fixa o valor
            if hasattr(self, "chk_auto_focus") and self.chk_auto_focus.isChecked():
                self.chk_auto_focus.blockSignals(True)
                self.chk_auto_focus.setChecked(False)
                self.chk_auto_focus.blockSignals(False)
                self._apply_focus_mode(cap, False)
            self._apply_camera_prop(cap, cv2.CAP_PROP_FOCUS, v)
        self.slider_focus.valueChanged.connect(_on_focus_change)
        
        layout.addWidget(settings_group)
        
        # ============== EXPOSIÇÃO AUTOMÁTICA ==============
        auto_group = QGroupBox("Controle Automático")
        auto_layout = QHBoxLayout(auto_group)
        
        self.chk_auto_exp = QCheckBox("Exposição Automática")
        try:
            auto_val = cap.get(cv2.CAP_PROP_AUTO_EXPOSURE)
            self.chk_auto_exp.setChecked(auto_val == 3 or auto_val == 1)
        except:
            self.chk_auto_exp.setChecked(True)
        self.chk_auto_exp.toggled.connect(
            lambda on: self._apply_camera_prop(cap, cv2.CAP_PROP_AUTO_EXPOSURE, 3 if on else 1)
        )
        auto_layout.addWidget(self.chk_auto_exp)
        
        self.chk_auto_wb = QCheckBox("Balanço de Branco Automático")
        try:
            wb_val = cap.get(cv2.CAP_PROP_AUTO_WB)
            self.chk_auto_wb.setChecked(wb_val == 1)
        except:
            self.chk_auto_wb.setChecked(True)
        self.chk_auto_wb.toggled.connect(
            lambda on: self._apply_camera_prop(cap, cv2.CAP_PROP_AUTO_WB, 1 if on else 0)
        )
        auto_layout.addWidget(self.chk_auto_wb)

        # Foco automático
        self.chk_auto_focus = QCheckBox("Foco Automático")
        try:
            af_val = cap.get(cv2.CAP_PROP_AUTOFOCUS)
            auto_focus_on = (af_val == 1)
        except Exception:
            auto_focus_on = saved_auto_focus
        self.chk_auto_focus.setChecked(auto_focus_on)
        self.chk_auto_focus.toggled.connect(lambda on: self._apply_focus_mode(cap, on))
        auto_layout.addWidget(self.chk_auto_focus)
        # Ajusta estado inicial (habilita/desabilita slider)
        self._apply_focus_mode(cap, auto_focus_on)
        
        layout.addWidget(auto_group)

        # ============== PERFIS DE CÂMERA ==============
        presets_grp = QGB("Perfis de Câmera")
        presets_layout = QVL(presets_grp)

        # Seleção de preset
        sel_row = QHL()
        sel_row.addWidget(QLabel("Perfil:"))
        self.combo_cam_presets = QComboBox()
        self._load_camera_presets_into_combo()
        sel_row.addWidget(self.combo_cam_presets, 1)
        btn_load_preset = QPB("Carregar")
        btn_load_preset.clicked.connect(self._load_selected_camera_preset)
        sel_row.addWidget(btn_load_preset)
        presets_layout.addLayout(sel_row)

        # Salvar/atualizar preset
        save_row = QHL()
        save_row.addWidget(QLabel("Nome:"))
        self.edit_preset_name = QLineEdit()
        save_row.addWidget(self.edit_preset_name, 1)
        btn_save_preset = QPB("Salvar/Atualizar")
        btn_save_preset.clicked.connect(self._save_current_camera_preset)
        save_row.addWidget(btn_save_preset)
        presets_layout.addLayout(save_row)

        # Aplicar e exportar
        action_row = QHL()
        btn_apply_now = QPB("Aplicar Ajustes")
        btn_apply_now.clicked.connect(lambda: self._apply_current_camera_settings(cap))
        action_row.addWidget(btn_apply_now)
        btn_export_preset = QPB("Exportar JSON")
        btn_export_preset.clicked.connect(self._export_current_camera_settings)
        action_row.addWidget(btn_export_preset)
        presets_layout.addLayout(action_row)

        layout.addWidget(presets_grp)
        
        # ============== BOTÕES ==============
        btn_layout = QHBoxLayout()
        
        btn_reset = QPushButton("Restaurar Padrão")
        btn_reset.clicked.connect(lambda: self._reset_camera_props(cap))
        btn_layout.addWidget(btn_reset)
        
        btn_apply = QPushButton("Aplicar Espelhamento")
        btn_apply.clicked.connect(self._apply_mirror_settings)
        btn_layout.addWidget(btn_apply)

        btn_apply_all = QPushButton("Aplicar Ajustes (Câmera)")
        btn_apply_all.clicked.connect(lambda: self._apply_current_camera_settings(cap))
        btn_layout.addWidget(btn_apply_all)
        
        btn_close = QPushButton("Fechar")
        btn_close.clicked.connect(dialog.accept)
        btn_layout.addWidget(btn_close)
        
        layout.addLayout(btn_layout)
        
        # Nota informativa
        note = QLabel("<i>Nota: Algumas configurações podem não funcionar com todas as câmeras.</i>")
        note.setWordWrap(True)
        layout.addWidget(note)
        
        dialog.exec()
        
        # Salva configurações de espelhamento
        self._camera_mirror_x = self.chk_mirror_x.isChecked()
        self._camera_mirror_y = self.chk_mirror_y.isChecked()

    def _apply_camera_prop(self, cap, prop_id, value):
        """Aplica uma propriedade à câmera OpenCV"""
        try:
            result = cap.set(prop_id, value)
            if result:
                logger.debug(f"Câmera: Propriedade {prop_id} = {value}")
            else:
                logger.warning(f"Câmera: Falha ao definir propriedade {prop_id} = {value}")
        except Exception as e:
            logger.warning(f"Erro ao aplicar configuração de câmera: {e}")

    def _gather_camera_settings(self) -> dict:
        """Coleta valores atuais da UI de câmera em um dicionário."""
        return {
            "mirror_x": self.chk_mirror_x.isChecked(),
            "mirror_y": self.chk_mirror_y.isChecked(),
            "brightness": self.slider_brightness.value(),
            "contrast": self.slider_contrast.value(),
            "saturation": self.slider_saturation.value(),
            "exposure": self.slider_exposure.value(),
            "gain": self.slider_gain.value(),
            "focus": self.slider_focus.value() if hasattr(self, "slider_focus") else 0,
            "auto_exposure": self.chk_auto_exp.isChecked(),
            "auto_white_balance": self.chk_auto_wb.isChecked(),
            "auto_focus": self.chk_auto_focus.isChecked() if hasattr(self, "chk_auto_focus") else True,
        }

    def _apply_current_camera_settings(self, cap):
        """Aplica ao dispositivo de câmera todos os ajustes atuais da UI."""
        try:
            settings = self._gather_camera_settings()
            # Automáticos
            self._apply_camera_prop(cap, cv2.CAP_PROP_AUTO_EXPOSURE, 3 if settings["auto_exposure"] else 1)
            self._apply_camera_prop(cap, cv2.CAP_PROP_AUTO_WB, 1 if settings["auto_white_balance"] else 0)
            self._apply_focus_mode(cap, settings["auto_focus"])
            # Valores manuais
            self._apply_camera_prop(cap, cv2.CAP_PROP_BRIGHTNESS, settings["brightness"])
            self._apply_camera_prop(cap, cv2.CAP_PROP_CONTRAST, settings["contrast"])
            self._apply_camera_prop(cap, cv2.CAP_PROP_SATURATION, settings["saturation"])
            self._apply_camera_prop(cap, cv2.CAP_PROP_EXPOSURE, settings["exposure"])
            self._apply_camera_prop(cap, cv2.CAP_PROP_GAIN, settings["gain"])
            if not settings["auto_focus"]:
                self._apply_camera_prop(cap, cv2.CAP_PROP_FOCUS, settings["focus"])
            self.statusBar().showMessage("Ajustes de câmera aplicados.")
        except Exception as e:
            logger.warning(f"Falha ao aplicar ajustes de câmera: {e}")

    def _apply_focus_mode(self, cap, auto_on: bool):
        """
        Liga/desliga auto-foco e ajusta UI de foco.
        """
        try:
            self._apply_camera_prop(cap, cv2.CAP_PROP_AUTOFOCUS, 1 if auto_on else 0)
        except Exception:
            pass

        if hasattr(self, "slider_focus"):
            self.slider_focus.setEnabled(not auto_on)

        # Quando auto-foco está desligado, reaplica o valor manual atual
        if not auto_on and hasattr(self, "slider_focus"):
            try:
                self._apply_camera_prop(cap, cv2.CAP_PROP_FOCUS, self.slider_focus.value())
            except Exception:
                pass

    def _reset_camera_props(self, cap):
        """Restaura configurações padrão da câmera"""
        self.slider_brightness.setValue(128)
        self.slider_contrast.setValue(128)
        self.slider_saturation.setValue(128)
        self.slider_exposure.setValue(-6)
        self.slider_gain.setValue(128)
        self.chk_auto_exp.setChecked(True)
        self.chk_auto_wb.setChecked(True)
        if hasattr(self, "slider_focus"):
            self.slider_focus.blockSignals(True)
            self.slider_focus.setValue(self.config.get("camera", "focus", default=0))
            self.slider_focus.blockSignals(False)
        if hasattr(self, "chk_auto_focus"):
            self.chk_auto_focus.setChecked(True)
            self._apply_focus_mode(cap, True)
        self.chk_mirror_x.setChecked(False)
        self.chk_mirror_y.setChecked(False)

    def _apply_mirror_settings(self):
        """Salva configurações de espelhamento no config"""
        self._camera_mirror_x = self.chk_mirror_x.isChecked()
        self._camera_mirror_y = self.chk_mirror_y.isChecked()
        
        # Salva todas as configurações de câmera no arquivo
        try:
            self.config.remember_camera_settings(
                mirror_x=self._camera_mirror_x,
                mirror_y=self._camera_mirror_y,
                brightness=self.slider_brightness.value(),
                contrast=self.slider_contrast.value(),
                saturation=self.slider_saturation.value(),
                exposure=self.slider_exposure.value(),
                gain=self.slider_gain.value(),
                focus=self.slider_focus.value(),
                auto_exp=self.chk_auto_exp.isChecked(),
                auto_wb=self.chk_auto_wb.isChecked(),
                auto_focus=self.chk_auto_focus.isChecked()
            )
            logger.info("Configurações de câmera salvas")
        except Exception as e:
            logger.warning(f"Erro ao salvar configurações de câmera: {e}")
        
        self.statusBar().showMessage(
            f"Espelhamento: X={'Sim' if self._camera_mirror_x else 'Não'}, "
            f"Y={'Sim' if self._camera_mirror_y else 'Não'} (Salvo)"
        )

    # ========= PERFIS DE CÂMERA =========
    def _load_camera_presets_into_combo(self):
        """Atualiza o combo com os presets salvos."""
        presets = self.config.list_camera_presets()
        self.combo_cam_presets.clear()
        self.combo_cam_presets.addItem("Selecione…", userData=None)
        for name in presets:
            self.combo_cam_presets.addItem(name, userData=name)

    def _save_current_camera_preset(self):
        name = self.edit_preset_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Nome obrigatório", "Informe um nome para salvar o perfil.")
            return
        data = self._gather_camera_settings()
        try:
            self.config.save_camera_preset(name, data)
            self._load_camera_presets_into_combo()
            self.statusBar().showMessage(f"Perfil '{name}' salvo.")
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Falha ao salvar perfil: {e}")

    def _load_selected_camera_preset(self):
        name = self.combo_cam_presets.currentData()
        if not name:
            QMessageBox.information(self, "Selecione", "Escolha um perfil para carregar.")
            return
        preset = self.config.get_camera_preset(name)
        if not preset:
            QMessageBox.warning(self, "Erro", f"Perfil '{name}' não encontrado.")
            return
        try:
            from PyQt6.QtCore import QSignalBlocker
            with QSignalBlocker(self.slider_brightness):
                self.slider_brightness.setValue(int(preset.get("brightness", 128)))
            with QSignalBlocker(self.slider_contrast):
                self.slider_contrast.setValue(int(preset.get("contrast", 128)))
            with QSignalBlocker(self.slider_saturation):
                self.slider_saturation.setValue(int(preset.get("saturation", 128)))
            with QSignalBlocker(self.slider_exposure):
                self.slider_exposure.setValue(int(preset.get("exposure", -6)))
            with QSignalBlocker(self.slider_gain):
                self.slider_gain.setValue(int(preset.get("gain", 128)))
            if hasattr(self, "slider_focus"):
                with QSignalBlocker(self.slider_focus):
                    self.slider_focus.setValue(int(preset.get("focus", 0)))
            self.chk_mirror_x.setChecked(bool(preset.get("mirror_x", False)))
            self.chk_mirror_y.setChecked(bool(preset.get("mirror_y", False)))
            self.chk_auto_exp.setChecked(bool(preset.get("auto_exposure", True)))
            self.chk_auto_wb.setChecked(bool(preset.get("auto_white_balance", True)))
            if hasattr(self, "chk_auto_focus"):
                self.chk_auto_focus.setChecked(bool(preset.get("auto_focus", True)))
                self._apply_focus_mode(self._camera_cap_ref, self.chk_auto_focus.isChecked())
            # Aplica no dispositivo
            self._apply_current_camera_settings(self._camera_cap_ref)
            self.statusBar().showMessage(f"Perfil '{name}' carregado e aplicado.")
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Falha ao carregar perfil: {e}")

    def _export_current_camera_settings(self):
        """Exporta as configurações atuais de câmera para um JSON."""
        filepath, _ = QFileDialog.getSaveFileName(self, "Exportar Configuração de Câmera", "", "JSON (*.json)")
        if not filepath:
            return
        settings = self._gather_camera_settings()
        try:
            with open(filepath, "w", encoding="utf-8") as fp:
                json.dump(settings, fp, indent=2, ensure_ascii=False)
            self.statusBar().showMessage(f"Configuração exportada para {filepath}")
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Falha ao exportar: {e}")


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

    def show_calibration_dialog(self):
        """Mostra um diálogo para configuração de calibração"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Calibração do Sistema CNC")
        dialog.setMinimumWidth(500)
        
        layout = QVBoxLayout(dialog)
        
        # Grupo de parâmetros físicos
        param_group = QGroupBox("Parâmetros da Máquina")
        param_layout = QGridLayout(param_group)
        
        param_layout.addWidget(QLabel("Pulsos por Revolução:"), 0, 0)
        pulses_input = QLineEdit(self.pulses_input.text())
        param_layout.addWidget(pulses_input, 0, 1)
        
        param_layout.addWidget(QLabel("Passo do Fuso (mm):"), 1, 0)
        fuso_input = QLineEdit(self.fuso_input.text())
        param_layout.addWidget(fuso_input, 1, 1)
        
        param_layout.addWidget(QLabel("Steps/mm calculado:"), 2, 0)
        steps_mm_result = QLabel("Calculando...")
        param_layout.addWidget(steps_mm_result, 2, 1)
        
        # Atualiza o cálculo quando os valores mudam
        def update_calculation():
            try:
                pulses = float(pulses_input.text())
                fuso = float(fuso_input.text())
                steps_mm = pulses / fuso
                steps_mm_result.setText(f"{steps_mm:.3f} steps/mm")
            except:
                steps_mm_result.setText("Erro no cálculo")
        
        pulses_input.textChanged.connect(update_calculation)
        fuso_input.textChanged.connect(update_calculation)
        update_calculation()  # Executa o cálculo inicial
        
        layout.addWidget(param_group)
        
        # Botões de ação
        buttons_layout = QHBoxLayout()
        
        apply_btn = QPushButton("Aplicar Parâmetros")
        def apply_and_close():
            self.pulses_input.setText(pulses_input.text())
            self.fuso_input.setText(fuso_input.text())
            dialog.accept()
            self.apply_calibration()
        apply_btn.clicked.connect(apply_and_close)
        
        test_btn = QPushButton("Testar Calibração")
        test_btn.clicked.connect(lambda: [dialog.accept(), self.show_calibration_test_dialog()])
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(dialog.reject)
        
        buttons_layout.addWidget(apply_btn)
        buttons_layout.addWidget(test_btn)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
        
        dialog.exec()

    def show_about_dialog(self):
        """Mostra informações sobre o aplicativo"""
        QMessageBox.about(self, "Sobre HesaiVision", 
                        "HesaiVision v1.0\n\n"
                        "Sistema de Inspeção Óptica Automatizada\n"
                        "Desenvolvido para controle de CNC com GRBL\n\n"
                        "© 2025 HesaiVision")
        
    def show_definir_mapa_dialog(self):
        """Abre diálogo para definir cantos e gerar mapa (modeless, sempre no topo)."""
        # 1) Cria sem flags inválidas
        dialog = QDialog(self)
        dialog.setWindowTitle("Definir Mapa")
        dialog.setMinimumWidth(900)
        dialog.setMinimumHeight(600)

        # 2) Non‐modal: permite operar a janela principal
        dialog.setWindowModality(Qt.WindowModality.NonModal)

        # 3) Sempre no topo, com título e botão de fechar
        dialog.setWindowFlags(
            dialog.windowFlags()
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowStaysOnTopHint
        )

        # Layout principal com splitter
        main_layout = QHBoxLayout(dialog)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ================== PAINEL ESQUERDO: PROGRAMAS SALVOS ==================
        programs_widget = QWidget()
        programs_layout = QVBoxLayout(programs_widget)
        programs_layout.setContentsMargins(0, 0, 0, 0)

        programs_group = QGroupBox("📁 Programas Salvos")
        programs_group_layout = QVBoxLayout(programs_group)

        # TreeView de programas
        from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem
        self.map_programs_tree = QTreeWidget()
        self.map_programs_tree.setHeaderLabels(["Nome", "Dimensão", "Data"])
        self.map_programs_tree.setColumnWidth(0, 150)
        self.map_programs_tree.setColumnWidth(1, 100)
        self.map_programs_tree.itemDoubleClicked.connect(
            lambda item: self._load_map_program(Path(item.data(0, Qt.ItemDataRole.UserRole))) if item else None
        )
        programs_group_layout.addWidget(self.map_programs_tree)

        # Botões de gerenciamento
        btn_programs_layout = QHBoxLayout()
        
        btn_load_program = QPushButton("📂 Carregar")
        btn_load_program.clicked.connect(lambda: self._on_load_map_program_clicked())
        btn_programs_layout.addWidget(btn_load_program)
        
        btn_delete_program = QPushButton("🗑️ Excluir")
        btn_delete_program.clicked.connect(lambda: self._delete_map_program())
        btn_programs_layout.addWidget(btn_delete_program)
        
        btn_refresh_programs = QPushButton("🔄")
        btn_refresh_programs.setMaximumWidth(40)
        btn_refresh_programs.clicked.connect(lambda: self._refresh_map_programs())
        btn_programs_layout.addWidget(btn_refresh_programs)
        
        programs_group_layout.addLayout(btn_programs_layout)
        programs_layout.addWidget(programs_group)

        # ================== PAINEL DIREITO: CONFIGURAÇÕES ==================
        config_widget = QWidget()
        layout = QVBoxLayout(config_widget)
        layout.setContentsMargins(10, 0, 0, 0)

        # Nome do programa
        h1 = QHBoxLayout()
        h1.addWidget(QLabel("Nome do Programa:"))
        self.map_program_name_edit = QLineEdit()
        # Carrega último nome de programa usado
        last_program = self.config.get("mosaic", "last_program_name", default="")
        self.map_program_name_edit.setText(last_program)
        h1.addWidget(self.map_program_name_edit)
        
        # Botão salvar programa
        btn_save_program = QPushButton("💾 Salvar")
        btn_save_program.clicked.connect(lambda: self._save_map_program())
        h1.addWidget(btn_save_program)
        layout.addLayout(h1)

        # Pasta de salvamento (base para os projetos) - agora usa MAP_PROGRAMS_FOLDER
        h2 = QHBoxLayout()
        h2.addWidget(QLabel("Pasta de Salvamento:"))
        self.map_folder_edit = QLineEdit()
        # Usa pasta map_programs como padrão
        default_folder = str(MAP_PROGRAMS_FOLDER)
        last_folder = self.config.get("mosaic", "last_folder", default=default_folder)
        self.map_folder_edit.setText(last_folder)
        self.map_folder_edit.setToolTip(
            "Pasta base onde serão criadas as subpastas dos programas.\n"
            "Estrutura: [Pasta]/[Nome do Programa]/Imagens/"
        )
        h2.addWidget(self.map_folder_edit)
        btn_browse = QPushButton("Buscar…")
        btn_browse.clicked.connect(self._select_map_folder)
        h2.addWidget(btn_browse)
        layout.addLayout(h2)

        # Passos X/Y
        h3 = QHBoxLayout()
        h3.addWidget(QLabel("Passo X (mm):"))
        self.map_step_x_edit = QLineEdit()
        # Carrega valores salvos
        saved_step_x = self.config.get("map", "step_x", default=10.0)
        self.map_step_x_edit.setText(str(saved_step_x))
        h3.addWidget(self.map_step_x_edit)
        h3.addWidget(QLabel("Passo Y (mm):"))
        self.map_step_y_edit = QLineEdit()
        saved_step_y = self.config.get("map", "step_y", default=10.0)
        self.map_step_y_edit.setText(str(saved_step_y))
        h3.addWidget(self.map_step_y_edit)
        layout.addLayout(h3)

        # ============== PAINEL DE INFORMAÇÕES CALCULADAS ==============
        info_group = QGroupBox("📊 Cálculo da Grade (ajuste automático)")
        info_layout = QGridLayout(info_group)
        info_layout.setColumnStretch(1, 1)
        info_layout.setColumnStretch(3, 1)
        
        # Labels para exibir valores calculados
        info_layout.addWidget(QLabel("Passo X ajustado:"), 0, 0)
        self.lbl_adjusted_step_x = QLabel("--")
        self.lbl_adjusted_step_x.setStyleSheet("font-weight: bold; color: #2196F3;")
        info_layout.addWidget(self.lbl_adjusted_step_x, 0, 1)
        
        info_layout.addWidget(QLabel("Passo Y ajustado:"), 0, 2)
        self.lbl_adjusted_step_y = QLabel("--")
        self.lbl_adjusted_step_y.setStyleSheet("font-weight: bold; color: #2196F3;")
        info_layout.addWidget(self.lbl_adjusted_step_y, 0, 3)
        
        info_layout.addWidget(QLabel("Colunas:"), 1, 0)
        self.lbl_cols = QLabel("--")
        self.lbl_cols.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(self.lbl_cols, 1, 1)
        
        info_layout.addWidget(QLabel("Linhas:"), 1, 2)
        self.lbl_rows = QLabel("--")
        self.lbl_rows.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(self.lbl_rows, 1, 3)
        
        info_layout.addWidget(QLabel("Total de imagens:"), 2, 0)
        self.lbl_total_images = QLabel("--")
        self.lbl_total_images.setStyleSheet("font-weight: bold; font-size: 14px; color: #4CAF50;")
        info_layout.addWidget(self.lbl_total_images, 2, 1)
        
        info_layout.addWidget(QLabel("Área (mm):"), 2, 2)
        self.lbl_area = QLabel("--")
        self.lbl_area.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(self.lbl_area, 2, 3)
        
        # Mensagem de status
        self.lbl_adjustment_status = QLabel("")
        self.lbl_adjustment_status.setWordWrap(True)
        self.lbl_adjustment_status.setStyleSheet("color: #666; font-style: italic;")
        info_layout.addWidget(self.lbl_adjustment_status, 3, 0, 1, 4)
        
        layout.addWidget(info_group)
        
        # Conecta eventos para atualização dinâmica
        self.map_step_x_edit.textChanged.connect(lambda: self._update_adjusted_step_info())
        self.map_step_y_edit.textChanged.connect(lambda: self._update_adjusted_step_info())
        
        # Atualiza informações iniciais
        self._update_adjusted_step_info()

        # ============== OPÇÕES DE MOSAICO ==============
        from PyQt6.QtWidgets import QSpinBox
        mosaic_group = QGroupBox("Montagem de Mosaico")
        mosaic_layout = QGridLayout(mosaic_group)
        
        # Checkbox para ativar montagem automática
        self.chk_auto_mosaic = QCheckBox("Montar mosaico automaticamente após captura")
        saved_auto_build = self.config.get("mosaic", "auto_build", default=True)
        self.chk_auto_mosaic.setChecked(saved_auto_build)
        mosaic_layout.addWidget(self.chk_auto_mosaic, 0, 0, 1, 4)
        
        # Margem de corte (para remover distorção de lente)
        mosaic_layout.addWidget(QLabel("Margem de corte (px):"), 1, 0)
        self.spin_mosaic_margin = QSpinBox()
        self.spin_mosaic_margin.setRange(0, 500)
        saved_margin = self.config.get("mosaic", "margin", default=50)
        self.spin_mosaic_margin.setValue(saved_margin)
        self.spin_mosaic_margin.setToolTip("Pixels a remover de cada borda para eliminar distorção de lente")
        mosaic_layout.addWidget(self.spin_mosaic_margin, 1, 1)
        
        # Blending nas junções
        mosaic_layout.addWidget(QLabel("Blending (px):"), 1, 2)
        self.spin_mosaic_blend = QSpinBox()
        self.spin_mosaic_blend.setRange(0, 100)
        saved_blend = self.config.get("mosaic", "blend_size", default=20)
        self.spin_mosaic_blend.setValue(saved_blend)
        self.spin_mosaic_blend.setToolTip("Tamanho da zona de transição gradual entre tiles")
        mosaic_layout.addWidget(self.spin_mosaic_blend, 1, 3)
        
        layout.addWidget(mosaic_group)
        # ============== FIM OPÇÕES DE MOSAICO ==============

        # ============== TEMPO DE ESPERA ANTES DA CAPTURA ==============
        capture_group = QGroupBox("Configurações de Captura")
        capture_layout = QHBoxLayout(capture_group)
        
        capture_layout.addWidget(QLabel("Tempo de espera antes da captura (ms):"))
        self.spin_capture_delay = QSpinBox()
        self.spin_capture_delay.setRange(50, 5000)
        saved_delay = self.config.get("mosaic", "capture_delay_ms", default=200)
        self.spin_capture_delay.setValue(saved_delay)
        self.spin_capture_delay.setSingleStep(50)
        self.spin_capture_delay.setToolTip(
            "Tempo de estabilização após movimento antes de capturar a imagem.\n"
            "Aumente se a câmera for lenta ou a imagem sair tremida."
        )
        capture_layout.addWidget(self.spin_capture_delay)
        capture_layout.addWidget(QLabel("ms"))
        capture_layout.addStretch()
        
        layout.addWidget(capture_group)
        # ============== FIM CONFIGURAÇÕES DE CAPTURA ==============

        # Botões de definição de canto
        btn_origin = QPushButton("Definir canto inferior esquerdo")
        btn_origin.clicked.connect(lambda: self._define_map_corner('origin'))
        layout.addWidget(btn_origin)

        btn_end = QPushButton("Definir canto superior direito")
        btn_end.clicked.connect(lambda: self._define_map_corner('end'))
        layout.addWidget(btn_end)

        # Botão gerar mapa
        btn_generate = QPushButton("🔧 Gerar Mapa de Imagens")
        btn_generate.setMinimumHeight(40)
        btn_generate.clicked.connect(lambda: self._on_generate_map(dialog))
        layout.addWidget(btn_generate)

        # ================== MONTAGEM DO SPLITTER ==================
        splitter.addWidget(programs_widget)
        splitter.addWidget(config_widget)
        splitter.setSizes([250, 650])  # Proporção inicial
        main_layout.addWidget(splitter)

        # Atualiza lista de programas
        self._refresh_map_programs()

        dialog.show()  # modeless, não bloqueia a janela principal

    def _select_map_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Selecione pasta para salvar imagens")
        if folder:
            self.map_folder_edit.setText(folder)

    def _define_map_corner(self, which):
        pos = self.controller.cnc.get_current_position()
        if which == 'origin':
            self.map_origin = {'x': pos['x'], 'y': pos['y']}
            # Usa statusBar em vez de MessageBox para evitar bloqueio
            # (o diálogo está como WindowStaysOnTopHint)
            self.statusBar().showMessage(
                f"✅ Origem definida: X={pos['x']:.3f}, Y={pos['y']:.3f}"
            )
        else:
            self.map_end = {'x': pos['x'], 'y': pos['y']}
            self.statusBar().showMessage(
                f"✅ Limite definido: X={pos['x']:.3f}, Y={pos['y']:.3f}"
            )
        
        # Atualiza painel de informações calculadas
        self._update_adjusted_step_info()

    def _update_adjusted_step_info(self):
        """
        Atualiza o painel de informações com os passos ajustados calculados.
        Chamado quando o usuário muda os passos ou define os cantos.
        """
        # Verifica se as labels existem
        if not hasattr(self, 'lbl_adjusted_step_x'):
            return
        
        # Obtém origem e fim
        origin = getattr(self, 'map_origin', None)
        end = getattr(self, 'map_end', None)
        
        if not origin or not end:
            self.lbl_adjusted_step_x.setText("--")
            self.lbl_adjusted_step_y.setText("--")
            self.lbl_cols.setText("--")
            self.lbl_rows.setText("--")
            self.lbl_total_images.setText("--")
            self.lbl_area.setText("--")
            self.lbl_adjustment_status.setText("⚠️ Defina os cantos (origem e limite) para calcular a grade.")
            return
        
        # Tenta ler os passos
        try:
            step_x = float(self.map_step_x_edit.text())
            step_y = float(self.map_step_y_edit.text())
        except ValueError:
            self.lbl_adjustment_status.setText("⚠️ Passos X/Y inválidos.")
            return
        
        if step_x <= 0 or step_y <= 0:
            self.lbl_adjustment_status.setText("⚠️ Os passos devem ser maiores que zero.")
            return
        
        # Calcula ajustes
        try:
            from aoi_lib import CNCAOIController
            adjusted = CNCAOIController.calculate_adjusted_steps(origin, end, step_x, step_y)
            
            # Atualiza labels
            self.lbl_adjusted_step_x.setText(f"{adjusted['step_x']:.3f} mm")
            self.lbl_adjusted_step_y.setText(f"{adjusted['step_y']:.3f} mm")
            self.lbl_cols.setText(str(adjusted['cols']))
            self.lbl_rows.setText(str(adjusted['rows']))
            self.lbl_total_images.setText(str(adjusted['total_images']))
            self.lbl_area.setText(f"{adjusted['dx']:.1f} x {adjusted['dy']:.1f}")
            
            # Monta mensagem de status
            messages = []
            if adjusted['adjusted_x']:
                delta_x = adjusted['step_x'] - step_x
                messages.append(f"Passo X ajustado de {step_x:.3f} → {adjusted['step_x']:.3f} mm ({'+' if delta_x > 0 else ''}{delta_x:.3f})")
            if adjusted['adjusted_y']:
                delta_y = adjusted['step_y'] - step_y
                messages.append(f"Passo Y ajustado de {step_y:.3f} → {adjusted['step_y']:.3f} mm ({'+' if delta_y > 0 else ''}{delta_y:.3f})")
            
            if messages:
                self.lbl_adjustment_status.setText("ℹ️ " + " | ".join(messages))
                self.lbl_adjustment_status.setStyleSheet("color: #FF9800; font-style: italic;")
            else:
                self.lbl_adjustment_status.setText("✅ Os passos dividem a área uniformemente.")
                self.lbl_adjustment_status.setStyleSheet("color: #4CAF50; font-style: italic;")
                
        except ValueError as e:
            self.lbl_adjustment_status.setText(f"⚠️ {str(e)}")
            self.lbl_adjustment_status.setStyleSheet("color: #F44336; font-style: italic;")
        except Exception as e:
            logger.warning(f"Erro ao calcular passos ajustados: {e}")
            self.lbl_adjustment_status.setText(f"⚠️ Erro no cálculo: {e}")

    # ================== GERENCIAMENTO DE PROGRAMAS DE MAPA ==================

    def _refresh_map_programs(self, base_folder: Path | None = None):
        """Atualiza a lista de programas salvos na TreeView sem travar a UI"""
        if not hasattr(self, 'map_programs_tree'):
            return
            
        from PyQt6.QtWidgets import QTreeWidgetItem
        from datetime import datetime
        # Usa pasta configurada na interface, caindo para pasta padrão
        base_dir = Path(base_folder) if base_folder else Path(self.map_folder_edit.text() or MAP_PROGRAMS_FOLDER)
        
        self.map_programs_tree.clear()
        
        # Garante que a pasta existe
        base_dir.mkdir(parents=True, exist_ok=True)
        
        # Lista todas as subpastas que contêm config.json
        for idx, prog_dir in enumerate(sorted(base_dir.iterdir())):
            if not prog_dir.is_dir():
                continue
            
            config_file = prog_dir / "config.json"
            if not config_file.exists():
                continue
            
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Extrai informações
                name = data.get("name", prog_dir.name)
                capture = data.get("capture_params", {})
                origin = capture.get("origin", {})
                end = capture.get("end", {})
                
                # Calcula dimensão
                if origin and end:
                    dx = abs(end.get("x", 0) - origin.get("x", 0))
                    dy = abs(end.get("y", 0) - origin.get("y", 0))
                    dimension = f"{dx:.0f}x{dy:.0f}mm"
                else:
                    dimension = "-"
                
                # Data de modificação
                mod_time = datetime.fromtimestamp(config_file.stat().st_mtime)
                date_str = mod_time.strftime("%Y-%m-%d %H:%M")
                
                # Adiciona à tree
                item = QTreeWidgetItem([name, dimension, date_str])
                item.setData(0, Qt.ItemDataRole.UserRole, str(prog_dir))
                self.map_programs_tree.addTopLevelItem(item)

                # Processa eventos periodicamente para manter a UI responsiva
                if idx % 20 == 0:
                    QApplication.processEvents()
                
            except Exception as e:
                logger.warning(f"Erro ao carregar programa {prog_dir}: {e}")

    def _save_map_program(self):
        """Salva o programa atual com suas configurações"""
        from datetime import datetime
        
        prog_name = self.map_program_name_edit.text().strip()
        if not prog_name:
            QMessageBox.warning(self, "Erro", "Informe um nome para o programa.")
            return
        
        # Sanitiza nome
        safe_name = "".join(c for c in prog_name if c.isalnum() or c in "._- ").strip()
        if not safe_name:
            QMessageBox.warning(self, "Erro", "Nome de programa inválido.")
            return
        
        # Cria pasta do programa
        base_folder = Path(self.map_folder_edit.text().strip() or str(MAP_PROGRAMS_FOLDER))
        program_folder = base_folder / safe_name
        images_folder = program_folder / "Imagens"
        
        try:
            images_folder.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao criar pasta:\n{e}")
            return
        
        # Coleta dados
        origin = getattr(self, 'map_origin', None)
        end = getattr(self, 'map_end', None)
        
        try:
            step_x = float(self.map_step_x_edit.text())
            step_y = float(self.map_step_y_edit.text())
        except ValueError:
            step_x, step_y = 10.0, 10.0
        
        config_data = {
            "version": "1.0",
            "name": prog_name,
            "created_at": datetime.now().isoformat(),
            "modified_at": datetime.now().isoformat(),
            "capture_params": {
                "origin": origin if origin else {"x": 0, "y": 0},
                "end": end if end else {"x": 0, "y": 0},
                "step_x": step_x,
                "step_y": step_y
            },
            "mosaic_params": {
                "auto_build": self.chk_auto_mosaic.isChecked(),
                "margin": self.spin_mosaic_margin.value(),
                "blend_size": self.spin_mosaic_blend.value(),
                "capture_delay_ms": self.spin_capture_delay.value()
            },
            "status": {
                "images_captured": len(list(images_folder.glob("*.png"))),
                "mosaic_generated": (program_folder / "mosaic.png").exists(),
                "last_capture_date": None
            }
        }
        
        # Salva config.json
        config_file = program_folder / "config.json"
        try:
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            self.statusBar().showMessage(f"✅ Programa '{prog_name}' salvo com sucesso!")
            logger.info(f"Programa salvo: {config_file}")
            
            # Atualiza TreeView usando a pasta do programa salvo
            self._refresh_map_programs(base_folder=program_folder.parent)
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao salvar programa:\n{e}")

    def _on_load_map_program_clicked(self):
        """Callback para o botão Carregar - carrega programa selecionado na TreeView"""
        if not hasattr(self, 'map_programs_tree'):
            return
            
        current = self.map_programs_tree.currentItem()
        if not current:
            QMessageBox.warning(self, "Seleção", "Selecione um programa na lista.")
            return
        
        program_path = Path(current.data(0, Qt.ItemDataRole.UserRole))
        self._load_map_program(program_path)

    def _load_map_program(self, program_path: Path):
        """Carrega um programa a partir de seu diretório"""
        config_file = program_path / "config.json"
        
        if not config_file.exists():
            QMessageBox.warning(self, "Erro", f"Arquivo de configuração não encontrado:\n{config_file}")
            return
        
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Preenche campos
            name = data.get("name", program_path.name)
            self.map_program_name_edit.setText(name)
            
            # Pasta base
            self.map_folder_edit.setText(str(program_path.parent))
            
            # Parâmetros de captura
            capture = data.get("capture_params", {})
            self.map_step_x_edit.setText(str(capture.get("step_x", 10.0)))
            self.map_step_y_edit.setText(str(capture.get("step_y", 10.0)))
            
            # Define origin/end
            origin = capture.get("origin", {})
            end = capture.get("end", {})
            if origin.get("x") is not None and origin.get("y") is not None:
                self.map_origin = origin
            if end.get("x") is not None and end.get("y") is not None:
                self.map_end = end
            
            # Parâmetros de mosaico
            mosaic = data.get("mosaic_params", {})
            self.chk_auto_mosaic.setChecked(mosaic.get("auto_build", True))
            self.spin_mosaic_margin.setValue(mosaic.get("margin", 50))
            self.spin_mosaic_blend.setValue(mosaic.get("blend_size", 20))
            self.spin_capture_delay.setValue(mosaic.get("capture_delay_ms", 200))
            
            # Atualiza painel de informações calculadas
            self._update_adjusted_step_info()
            
            # Feedback
            msg = f"✅ Programa '{name}' carregado"
            if self.map_origin and self.map_end:
                msg += f" | Área: ({self.map_origin['x']:.1f},{self.map_origin['y']:.1f}) → ({self.map_end['x']:.1f},{self.map_end['y']:.1f})"
            self.statusBar().showMessage(msg)
            logger.info(f"Programa carregado: {program_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao carregar programa:\n{e}")

    def _delete_map_program(self):
        """Exclui o programa selecionado"""
        if not hasattr(self, 'map_programs_tree'):
            return
            
        current = self.map_programs_tree.currentItem()
        if not current:
            QMessageBox.warning(self, "Seleção", "Selecione um programa para excluir.")
            return
        
        program_path = Path(current.data(0, Qt.ItemDataRole.UserRole))
        program_name = current.text(0)
        
        # Confirma exclusão
        reply = QMessageBox.question(
            self, "Confirmar Exclusão",
            f"Deseja excluir o programa '{program_name}'?\n\n"
            f"Pasta: {program_path}\n\n"
            "Esta ação removerá a pasta e todo seu conteúdo (imagens, mosaico, etc.)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            import shutil
            shutil.rmtree(program_path)
            
            self.statusBar().showMessage(f"✅ Programa '{program_name}' excluído")
            logger.info(f"Programa excluído: {program_path}")
            
            # Atualiza TreeView na mesma pasta
            self._refresh_map_programs(base_folder=program_path.parent)
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao excluir programa:\n{e}")

    def _on_generate_map(self, dialog):
        # Verifica conexão CNC - bloqueia APENAS a geração, não o diálogo
        if not self.controller.cnc.is_connected:
            QMessageBox.warning(
                dialog, "CNC Não Conectado",
                "A geração do mapa requer conexão com o CLP para movimentar a máquina.\n\n"
                "Você pode:\n"
                "• Conectar o CLP e tentar novamente\n"
                "• Configurar e salvar os parâmetros na receita para uso posterior\n\n"
                "As demais funcionalidades (câmera, receitas) continuam disponíveis."
            )
            return
                
        # Passo 1 – coletar e validar parâmetros ---------------------
        params = self._collect_map_params(dialog)
        if params is None:      # validação falhou ⇒ aborta
            return

        # Passo 2 – iniciar thread de geração -----------------------
        self._start_map_thread(params, dialog)

    def _collect_map_params(self, parent_dialog=None) -> MapParams | None:
        """
        Valida inputs da UI e devolve objeto MapParams ou None em caso de erro.
        Usa parent_dialog para exibir mensagens sobre o diálogo flutuante.
        """
        # Usa o diálogo como parent para os MessageBox evitando conflito
        # com WindowStaysOnTopHint
        msg_parent = parent_dialog if parent_dialog else self
        
        origin = getattr(self, 'map_origin', None)
        end    = getattr(self, 'map_end',    None)
        if not origin or not end:
            QMessageBox.warning(msg_parent, "Erro", "Defina ambos os cantos antes de gerar o mapa.")
            return None

        try:
            step_x = float(self.map_step_x_edit.text())
            step_y = float(self.map_step_y_edit.text())
        except ValueError:
            QMessageBox.warning(msg_parent, "Erro", "Passos X/Y inválidos.")
            return None

        dx, dy = end['x'] - origin['x'], end['y'] - origin['y']
        if step_x <= 0 or step_y <= 0:
            QMessageBox.warning(msg_parent, "Erro", "Os passos devem ser maiores que zero.")
            return None

        # Ajuste opcional se o passo superar dimensão
        if step_x > dx or step_y > dy:
            if QMessageBox.question(
                    msg_parent,
                    "Passo maior que dimensão",
                    ("Algum passo é maior que a dimensão da placa. "
                     "Deseja ajustar automaticamente?"),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            ) == QMessageBox.StandardButton.No:
                return None
            step_x = min(step_x, dx)
            step_y = min(step_y, dy)
            self.map_step_x_edit.setText(f"{step_x:.3f}")
            self.map_step_y_edit.setText(f"{step_y:.3f}")

        base_folder = self.map_folder_edit.text().strip()
        prog = self.map_program_name_edit.text().strip()
        if not base_folder or not prog:
            QMessageBox.warning(msg_parent, "Erro", "Informe o nome do programa e a pasta de salvamento.")
            return None

        # ========== CRIA ESTRUTURA DE PASTAS ==========
        # Estrutura: [Pasta Base]/[Nome do Programa]/Imagens/
        # Sanitiza o nome do programa para uso em pasta
        safe_prog_name = "".join(c for c in prog if c.isalnum() or c in "._- ").strip()
        if not safe_prog_name:
            QMessageBox.warning(msg_parent, "Erro", "Nome do programa inválido para criar pasta.")
            return None
        
        # Cria a estrutura de pastas
        program_folder = Path(base_folder) / safe_prog_name
        images_folder = program_folder / "Imagens"
        
        try:
            images_folder.mkdir(parents=True, exist_ok=True)
            logger.info(f"Estrutura de pastas criada: {images_folder}")
        except Exception as e:
            QMessageBox.critical(msg_parent, "Erro", f"Falha ao criar pasta:\n{images_folder}\n\nErro: {e}")
            return None
        
        # A pasta de imagens é onde as capturas serão salvas
        final_folder = str(images_folder)

        # ========== SALVA CONFIGURAÇÕES PARA PRÓXIMA VEZ ==========
        try:
            # Salva a pasta BASE (não a pasta de imagens) para que o usuário possa reusar
            self.config.remember_map_params(step_x, step_y, base_folder, prog)
            self.config.remember_mosaic_settings(
                auto_build=self.chk_auto_mosaic.isChecked(),
                margin=self.spin_mosaic_margin.value(),
                blend_size=self.spin_mosaic_blend.value(),
                capture_delay_ms=self.spin_capture_delay.value()
            )
            logger.debug("Configurações de mapa/mosaico salvas")
        except Exception as e:
            logger.warning(f"Erro ao salvar configurações de mapa: {e}")
        # ==========================================================

        # Usa a pasta de imagens como destino final
        return MapParams(origin, end, step_x, step_y, final_folder, prog)

    def _start_map_thread(self, p: MapParams, dialog):
        """
        Separa a configuração da thread e da UI/ProgressBar.
        """
        # Obtém o tempo de espera configurado
        capture_delay = getattr(self, 'spin_capture_delay', None)
        delay_ms = capture_delay.value() if capture_delay else 200
        
        # Context manager garante preview restaurado
        with _PreviewSuspender(self.camera_preview):
            self.map_thread = MapGeneratorThread(
                self.controller, p.origin, p.end,
                p.step_x, p.step_y, p.folder, p.program_name,
                feed_rate=None,              # Usa velocidade ja gravada no CLP (nao sobrescreve)
                capture_delay_ms=delay_ms    # Tempo de espera antes da captura
            )

            # Progress dialog simples
            self.map_progress = QProgressDialog("Gerando mapa…", "Cancelar", 0, 0, self)
            self.map_progress.setWindowTitle("Progresso do Mapa")
            self.map_progress.setWindowModality(Qt.WindowModality.NonModal)
            self.map_progress.show()

            # Conexões de sinal ⇄ slots
            self.map_thread.progress.connect(self._on_map_progress)
            self.map_thread.image_captured.connect(self.camera_preview.display_image)
            self.map_thread.finished.connect(lambda: self._on_map_finished(dialog))
            self.map_thread.error.connect(self._on_map_error)

            self.map_progress.canceled.connect(self.map_thread.requestInterruption)
            self.map_thread.start()
    def _get_current_feed_rate(self):
        """Obtém a velocidade de movimentação configurada na interface"""
        try:
            return float(self.movement_widget.feed_rate.text())
        except (ValueError, AttributeError):
            return 1000.0  # fallback

    # ---------- slots da geração de mapa ----------------------------

    def _on_map_progress(self, done: int, total: int):
        self.map_progress.setMaximum(total)
        self.map_progress.setValue(done)
        pct = int(done / total * 100) if total else 0
        self.map_progress.setLabelText(f"Capturadas {done}/{total} imagens ({pct}%)")

    def _on_map_finished(self, dialog):
        self.map_progress.close()
        
        # IMPORTANTE: Fecha o diálogo ANTES de exibir mensagens
        # Isso evita conflito com WindowStaysOnTopHint
        dialog.accept()
        
        # ========== SINCRONIZA BOTÃO DE BACKLIGHT ==========
        self._sync_backlight_button()
        
        # Obtém parâmetros da pasta e opções de mosaico
        folder = getattr(self, 'map_folder_edit', None)
        folder_path = folder.text().strip() if folder else ""
        
        # Verifica se montagem automática está habilitada
        auto_mosaic = getattr(self, 'chk_auto_mosaic', None)
        should_build_mosaic = auto_mosaic.isChecked() if auto_mosaic else True
        
        if should_build_mosaic and folder_path and os.path.isdir(folder_path):
            # Obtém parâmetros de margem e blending
            margin = getattr(self, 'spin_mosaic_margin', None)
            margin_value = margin.value() if margin else 50
            
            blend = getattr(self, 'spin_mosaic_blend', None)
            blend_value = blend.value() if blend else 20
            
            # Monta o mosaico
            self.statusBar().showMessage("Montando mosaico das imagens capturadas...")
            QApplication.processEvents()
            
            try:
                mosaic_path = compose_mosaic_from_folder(
                    folder_path,
                    invert_rows=True,  # Origem no canto inferior-esquerdo
                    margin=margin_value,
                    blend_size=blend_value,
                )
                
                if mosaic_path:
                    QMessageBox.information(
                        self, "Concluído", 
                        f"✅ Mapa gerado com sucesso!\n\n"
                        f"📁 Imagens salvas em:\n{folder_path}\n\n"
                        f"🖼️ Mosaico montado:\n{mosaic_path}"
                    )
                    self.statusBar().showMessage(f"Mosaico salvo: {mosaic_path}")
                else:
                    QMessageBox.information(
                        self, "Concluído",
                        "Mapa gerado com sucesso.\n\n"
                        "⚠️ Falha ao montar mosaico (sem imagens válidas encontradas)."
                    )
            except Exception as e:
                logger.error(f"Erro ao montar mosaico: {e}")
                QMessageBox.information(
                    self, "Concluído", 
                    f"Mapa gerado com sucesso.\n\n"
                    f"⚠️ Erro ao montar mosaico: {e}"
                )
        else:
            QMessageBox.information(self, "Concluído", "Mapa gerado com sucesso.")

    def _on_map_error(self, msg: str):
        self.map_progress.close()
        # Sincroniza botão de backlight após erro
        self._sync_backlight_button()
        QMessageBox.critical(self, "Erro", msg)
    
    def _sync_backlight_button(self):
        """
        Sincroniza o estado visual do botão de backlight com o estado real do CLP.
        Chamado após operações que podem alterar o backlight programaticamente.
        """
        try:
            # Verifica se o widget de movimento existe
            if not hasattr(self, 'movement_widget'):
                return
            
            # Verifica se o controlador está conectado e tem suporte a backlight
            if (not hasattr(self.controller, 'cnc') or 
                not self.controller.cnc.is_connected or
                not hasattr(self.controller.cnc, 'backlight_on')):
                return
            
            # Obtém estado atual do backlight
            is_on = self.controller.cnc.backlight_on
            
            # Atualiza o botão sem disparar o sinal toggled
            self.movement_widget.backlight_button.blockSignals(True)
            self.movement_widget.backlight_button.setChecked(is_on)
            self.movement_widget.backlight_button.setText(
                "💡 Backlight ON" if is_on else "💡 Backlight OFF"
            )
            self.movement_widget.backlight_button.blockSignals(False)
            
            logger.debug(f"Backlight sincronizado: {'ON' if is_on else 'OFF'}")
        except Exception as e:
            logger.error(f"Erro ao sincronizar botão de backlight: {e}")

    def save_gcode(self):
        """Salva a sequência atual como arquivo G-CODE"""
        if not self.current_sequence:
            QMessageBox.warning(self, "Aviso", "Crie uma sequência primeiro")
            return
            
        from aoi_lib.gcode_manager import GCodeManager
        gcode_manager = GCodeManager()
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Salvar como G-CODE", "", "Arquivos G-CODE (*.gcode *.nc *.ngc)"
        )
        
        if filename:
            if not filename.lower().endswith(('.gcode', '.nc', '.ngc')):
                filename += '.gcode'
                
            if gcode_manager.save_gcode_to_file(self.current_sequence, filename):
                self.statusBar().showMessage(f"G-CODE salvo em {filename}")
            else:
                QMessageBox.critical(self, "Erro", "Falha ao salvar o arquivo G-CODE")

    def apply_calibration(self):
        """
        Aplica a calibração de movimento com base nos valores informados pelo usuário.
        Envia comandos diretos para o GRBL para configurar os steps/mm.
        """
        if not self.controller.cnc.is_connected:
            QMessageBox.warning(self, "Erro", "CNC não conectada. Conecte primeiro.")
            return
        
        # Se for PLC, atualiza apenas o fator de conversão interno
        if isinstance(self.controller.cnc, PLCAxisController):
            try:
                pulses = float(self.pulses_input.text())
                fuso_pass = float(self.fuso_input.text())
                
                # Atualiza o fator de conversão pulsos/mm do PLC
                self.controller.cnc.pulses_per_mm = pulses / fuso_pass
                
                # Salva no JSON para persistir a configuração
                self.config.remember_calibration(pulses, fuso_pass)
                
                self.statusBar().showMessage(f"Calibração PLC aplicada: {pulses / fuso_pass:.3f} pulsos/mm")
                QMessageBox.information(
                    self, "Calibração PLC",
                    f"Fator de conversão atualizado:\n{pulses / fuso_pass:.3f} pulsos/mm"
                )
            except ValueError:
                QMessageBox.warning(self, "Erro", "Valores de calibração inválidos.")
            return
        
        # Se for GRBL, verifica se tem o atributo grbl
        if not hasattr(self.controller.cnc, 'grbl') or not self.controller.cnc.grbl:
            QMessageBox.warning(self, "Erro", "Controlador GRBL não disponível.")
            return
            
        try:
            pulses = float(self.pulses_input.text())
            fuso_pass = float(self.fuso_input.text())
            
            # Calcula steps/mm: (pulsos por revolução) / (passo do fuso em mm)
            steps_per_mm = pulses / fuso_pass
            
            # Armazena o valor calculado
            self.controller.cnc.steps_to_mm_factor = fuso_pass / pulses
            
            # Envia comandos para configurar o GRBL
            logger.info(f"CALIBRAÇÃO: Configurando steps/mm para {steps_per_mm}")
            
            # Verifica se o usuário deseja realmente enviar estes valores
            reply = QMessageBox.question(
                self, 
                "Confirmar Calibração", 
                f"Deseja enviar os seguintes parâmetros para o GRBL?\n\n"
                f"Steps/mm eixo X: {steps_per_mm:.3f}\n"
                f"Steps/mm eixo Y: {steps_per_mm:.3f}\n\n"
                f"Isso irá alterar a configuração do controlador.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Comandos para configurar os eixos X e Y
                self.controller.cnc.grbl.send_immediately(f"$100={steps_per_mm:.3f}")
                QTimer.singleShot(100, lambda: self.controller.cnc.grbl.send_immediately(f"$101={steps_per_mm:.3f}"))
                
                # Solicita ao usuário que faça um teste de calibração
                QTimer.singleShot(500, self.show_calibration_test_dialog)
                
                self.statusBar().showMessage(f"Calibração aplicada: {steps_per_mm:.3f} steps/mm")

                # --------- salva no JSON ----------
                self.config.remember_calibration(pulses, fuso_pass)

            else:
                self.statusBar().showMessage("Calibração cancelada pelo usuário")
                
        except ValueError:
            QMessageBox.warning(self, "Erro", "Valores de calibração inválidos.")

    def show_calibration_test_dialog(self):
        """
        Exibe um diálogo para testar a calibração atual.
        """
        dialog = QDialog(self)
        dialog.setWindowTitle("Teste de Calibração")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Instruções
        instructions = QLabel(
            "Para testar a calibração:\n\n"
            "1. Coloque um papel milimetrado ou uma régua sob a cabeça da máquina\n"
            "2. Escolha uma distância de teste\n"
            "3. Clique em 'Mover X' ou 'Mover Y' para testar cada eixo\n"
            "4. Verifique se o deslocamento físico corresponde ao valor escolhido\n"
            "5. Se necessário, ajuste os valores de calibração e aplique novamente"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Distância de teste
        test_layout = QHBoxLayout()
        test_layout.addWidget(QLabel("Distância de teste:"))
        distance_input = QLineEdit("10")
        test_layout.addWidget(distance_input)
        test_layout.addWidget(QLabel("mm"))
        layout.addLayout(test_layout)
        
        # Botões de teste
        buttons_layout = QHBoxLayout()
        
        move_x_btn = QPushButton("Mover X")
        move_x_btn.clicked.connect(lambda: self.test_calibration_move(0, float(distance_input.text())))
        
        move_y_btn = QPushButton("Mover Y")
        move_y_btn.clicked.connect(lambda: self.test_calibration_move(1, float(distance_input.text())))
        
        reset_position_btn = QPushButton("Zerar Posição")
        reset_position_btn.clicked.connect(self.set_zero_position)
        
        buttons_layout.addWidget(move_x_btn)
        buttons_layout.addWidget(move_y_btn)
        buttons_layout.addWidget(reset_position_btn)
        
        layout.addLayout(buttons_layout)
        
        # Resultados
        result_group = QGroupBox("Resultados")
        result_layout = QVBoxLayout(result_group)
        
        self.calibration_test_result = QLabel("Execute um teste para ver os resultados")
        result_layout.addWidget(self.calibration_test_result)
        
        layout.addWidget(result_group)
        
        # Botões de controle
        control_layout = QHBoxLayout()
        close_btn = QPushButton("Concluir")
        close_btn.clicked.connect(dialog.accept)
        control_layout.addWidget(close_btn)
        
        layout.addLayout(control_layout)
        
        dialog.exec()

    def test_calibration_move(self, axis, distance):
        """
        Realiza um movimento de teste para calibração.
        
        Args:
            axis: 0 para X, 1 para Y
            distance: Distância em mm para mover
        """
        if not self.controller.cnc.is_connected:
            QMessageBox.warning(self, "Erro", "CNC não conectada")
            return
        
        try:
            # Captura posição inicial
            initial_position = self.controller.cnc.get_current_position()

            # Prepara o comando
            # Define o modo absoluto para garantir precisão
            self.controller.cnc.grbl.send_immediately("G90")
            
            # Calcula a posição absoluta a ser atingida
            target_position = {}
            target_position['x'] = initial_position['x'] + distance if axis == 0 else initial_position['x']
            target_position['y'] = initial_position['y'] + distance if axis == 1 else initial_position['y']
            
            # Envia o movimento como coordenada absoluta
            if axis == 0:
                self.controller.cnc.move_to_absolute_position(target_position['x'], None, 500)
            else:
                self.controller.cnc.move_to_absolute_position(None, target_position['y'], 500)
            self.controller.cnc.wait_for_idle()
            
            # Aguarda um pouco para o movimento ser concluído
            QTimer.singleShot(1500, lambda: self.verify_calibration_result(axis, initial_position, distance))
            
        except Exception as e:
            logger.error(f"CALIBRAÇÃO: Erro no teste de calibração: {e}")
            QMessageBox.warning(self, "Erro", f"Erro no teste: {str(e)}")

    def _show_calibration_result(self, axis, initial_position, expected_distance):
        """
        Calcula deslocamento real, erro e atualiza o QLabel de resultados.
        Executado de forma assíncrona pelo QTimer.
        """
        try:
            current_position = self.controller.cnc.get_current_position()

            axis_name = "x" if axis == 0 else "y"
            actual_distance = current_position[axis_name] - initial_position[axis_name]

            error = actual_distance - expected_distance
            error_percent = (error / expected_distance * 100) if expected_distance else 0

            result_text = (
                f"Eixo: {axis_name.upper()}\n"
                f"Movimento comandado: {expected_distance:.3f} mm\n"
                f"Movimento real: {actual_distance:.3f} mm\n"
                f"Erro: {error:.3f} mm ({error_percent:.2f}%)\n\n"
            )

            if abs(error_percent) < 1:
                result_text += "■ Calibração excelente (erro < 1%)"
            elif abs(error_percent) < 5:
                result_text += "✓ Calibração aceitável (erro < 5%)"
            else:
                result_text += "■ Calibração insatisfatória – ajuste os parâmetros"

            if hasattr(self, "calibration_test_result"):
                self.calibration_test_result.setText(result_text)

            logger.info(
                "CALIBRAÇÃO: Resultado – %s",
                result_text.replace("\n", " | ")
            )
        except Exception as e:
            logger.error(f"CALIBRAÇÃO: Erro ao calcular resultado: {e}")

    def verify_calibration_result(self, axis, initial_position, expected_distance):
        """
        Verifica o resultado do teste de calibração.
        
        Args:
            axis: 0 para X, 1 para Y
            initial_position: Posição antes do movimento
            expected_distance: Distância esperada do movimento
        """
        try:
            # 1) força a atualização de status
            self.controller.cnc.grbl.send_immediately("?")

            # 2) Agenda o cálculo daqui a 250 ms para NÃO travar a GUI
            QTimer.singleShot(
                250,
                lambda: self._show_calibration_result(
                    axis, initial_position, expected_distance
                )
            )
            return
            
        except Exception as e:
            logger.error(f"CALIBRAÇÃO: Erro ao verificar resultado: {e}")

    

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
