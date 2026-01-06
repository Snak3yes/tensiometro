"""
coordinators/setup_coordinator.py
----------------------------------
Coordenador de setup e inicialização da aplicação.

Orquestra toda inicialização de controllers, coordinators, handlers, managers e services.
"""
import logging
from PyQt6.QtCore import QTimer
from aoi_lib import PLCAxisController

logger = logging.getLogger(__name__)


class SetupCoordinator:
    """
    Orquestra toda inicialização da aplicação.

    Responsabilidades:
        - Inicializar configurações e controller principal
        - Criar todos os managers (recipe, stencil, report, inspection)
        - Criar todos os coordinators (connection, inspection, tension)
        - Criar todos os handlers (keyboard, menu, GRBL, dialogs)
        - Criar todos os controllers (map, camera, calibration, etc.)
        - Criar todos os services (sequence execution, resource)
        - Configurar UI (setup_ui, setup_menu)
        - Conectar todos os signals
        - Configurar timers e auto-connect
    """

    def __init__(self, main_window_class):
        """
        Inicializa o coordenador de setup.

        Args:
            main_window_class: Classe AOIControllerApp (não instância ainda)
        """
        self.main_window_class = main_window_class
        self.window = None  # Será definido em setup()

    def setup(self, window):
        """
        Executa todo o setup da aplicação.

        Args:
            window: Instância de AOIControllerApp já criada com super().__init__()
        """
        self.window = window

        # Ordem de setup é crítica!
        self._setup_basic_config()              # 1. Config básica
        self._setup_core_controller()            # 2. Controller CNC principal
        self._setup_managers()                  # 3. Managers (recipe, stencil, report, inspection)
        self._setup_coordinators()              # 4. Coordinators (dependem de managers)
        self._setup_handlers()                  # 5. Handlers de UI
        self._setup_controllers()               # 6. Controllers
        self._setup_services()                  # 7. Services
        self._setup_camera_config()             # 8. Config de câmera
        self._setup_ui()                        # 9. Interface gráfica
        self._setup_dependent_controllers()     # 10. Controllers que dependem de UI
        self._setup_keyboard_handler()          # 11. Handler de teclado
        self._setup_menu()                      # 12. Menu
        self._setup_signals()                   # 13. Conectar todos os signals
        self._setup_ui_state()                  # 14. Estado inicial da UI
        self._setup_auto_connect()              # 15. Auto-connect
        self._setup_timers()                    # 16. Timers

        logger.info("Setup da aplicação concluído com sucesso")

    def _setup_basic_config(self):
        """Configuração básica da janela."""
        self.window.setWindowTitle("Controle de Inspeção Óptica Automatizada")
        self.window.setGeometry(100, 100, 1200, 800)

        # Carrega configurações do usuário
        from aoi_lib.config_manager import AOIConfigManager
        self.window.config = AOIConfigManager()

        logger.debug("Configuração básica concluída")

    def _setup_core_controller(self):
        """Inicializa o controller principal (CNCAOIController)."""
        from aoi_lib import CNCAOIController

        plc_host = self.window.config.get("connections", "plc_host", default="192.168.1.5")
        plc_port = self.window.config.get("connections", "plc_port", default=502)

        logger.debug("Inicializando CNCAOIController com PLCAxisController (sem conexão automática)")
        self.window.controller = CNCAOIController(
            plc_host=plc_host,
            plc_port=plc_port,
            auto_connect=False
        )

        logger.debug(
            "CNCAOIController inicializado; backend = %s",
            type(self.window.controller.cnc).__name__
        )

    def _setup_coordinators(self):
        """Cria todos os coordinators."""
        from consumo_lib.coordinators import ConnectionCoordinator, InspectionCoordinator, TensionCoordinator
        from consumo_lib.managers import ConnectionManager

        # Connection Manager (gerencia PLC, GRBL, serial ports)
        self.window.connection_mgr = ConnectionManager(
            self.window.controller,
            self.window.config
        )

        # Connection Coordinator (gerencia estados de conexão)
        self.window.connection_coordinator = ConnectionCoordinator(
            self.window.controller,
            self.window.config
        )

        # Inspection Coordinator
        self.window.inspection_coordinator = InspectionCoordinator(
            self.window.controller,
            self.window.config,
            self.window.inspection_manager  # Criado em _setup_managers
        )

        # Tension Coordinator
        self.window.tension_coordinator = TensionCoordinator(
            self.window.controller,
            self.window.config
        )

        logger.debug("Coordinators criados: connection, inspection, tension")

    def _setup_managers(self):
        """Cria todos os managers (recipe, stencil, report, inspection)."""
        from consumo_lib.managers import RecipeManagerWrapper, StencilManagerWrapper, ReportManagerWrapper, InspectionManager
        from consumo_lib.controllers import RecipeManagerController

        # Estado interno
        self.window.current_sequence = None
        self.window.is_running_sequence = False

        # Recipe Manager
        self.window.recipe_manager_wrapper = RecipeManagerWrapper(parent=self.window)
        self.window.recipe_manager = self.window.recipe_manager_wrapper.recipe_manager
        self.window.current_recipe = None

        # RecipeManagerController (depende de recipe_manager)
        try:
            self.window.recipe_manager_controller = RecipeManagerController(
                self.window.recipe_manager,
                self.window.recipe_manager_wrapper,
                self.window
            )
            logger.debug("RecipeManagerController criado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao criar RecipeManagerController: {e}")
            self.window.recipe_manager_controller = None

        # Stencil Manager
        self.window.stencil_manager_wrapper = StencilManagerWrapper(parent=self.window)
        self.window.stencil_tracker = self.window.stencil_manager_wrapper.stencil_tracker
        self.window.current_stencil = None

        # Report Manager
        self.window.report_manager_wrapper = ReportManagerWrapper(
            self.window.config,
            parent=self.window
        )
        self.window.report_config = self.window.report_manager_wrapper.get_config()
        self.window.report_generator = self.window.report_manager_wrapper.get_generator()

        # Inspection Manager
        self.window.inspection_manager = InspectionManager(
            self.window.config,
            parent=self.window
        )
        self.window.inspection_thresholds = self.window.inspection_manager.get_thresholds()
        self.window.stencil_inspector = self.window.inspection_manager.get_inspector()
        self.window._last_inspection_result = None
        self.window._last_inspection_overlay = None

        logger.debug("Managers criados: recipe, stencil, report, inspection")

    def _setup_handlers(self):
        """Cria todos os handlers."""
        from consumo_lib.handlers import KeyboardEventHandler, MenuHandler, GRBLCallbackHandler, DialogRouter

        # KeyboardEventHandler (será configurado após setup_ui)
        self.window.keyboard_handler = KeyboardEventHandler()

        # MenuHandler (será configurado em setup_menu)
        self.window.menu_handler = MenuHandler(main_window=self.window)

        # GRBLCallbackHandler
        self.window.grbl_callback_handler = GRBLCallbackHandler(self.window)

        # DialogRouter
        self.window.dialog_router = DialogRouter(self.window)

        logger.debug("Handlers criados: keyboard, menu, grbl_callback, dialog_router")

    def _setup_controllers(self):
        """Cria todos os controllers que não dependem de UI."""
        from consumo_lib.controllers import (
            MapController,
            CameraSettingsController,
            CalibrationController,
            InspectionUIController,
            ReportDialogController,
            SequenceController,
            FiducialAlignmentController,
            TensionMeasurementController,
            DialogManagerController
        )

        # Map Controller
        try:
            self.window.map_controller = MapController(
                self.window.controller,
                self.window.config,
                self.window
            )
            logger.debug("MapController criado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao criar MapController: {e}")
            self.window.map_controller = None

        # Camera Settings Controller
        try:
            self.window.camera_settings_controller = CameraSettingsController(
                self.window.controller,
                self.window.config,
                self.window
            )
            logger.debug("CameraSettingsController criado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao criar CameraSettingsController: {e}")
            self.window.camera_settings_controller = None

        # Calibration Controller
        try:
            self.window.calibration_controller = CalibrationController(
                self.window.controller,
                self.window.config,
                self.window
            )
            logger.debug("CalibrationController criado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao criar CalibrationController: {e}")
            self.window.calibration_controller = None

        # Inspection UI Controller
        try:
            self.window.inspection_ui_controller = InspectionUIController(
                self.window.inspection_manager,
                self.window.config,
                self.window
            )
            logger.debug("InspectionUIController criado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao criar InspectionUIController: {e}")
            self.window.inspection_ui_controller = None

        # Report Dialog Controller
        try:
            self.window.report_dialog_controller = ReportDialogController(
                self.window.report_manager_wrapper,
                self.window.stencil_manager_wrapper,
                self.window.stencil_tracker,
                self.window
            )
            logger.debug("ReportDialogController criado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao criar ReportDialogController: {e}")
            self.window.report_dialog_controller = None

        # Sequence Controller
        try:
            self.window.sequence_controller = SequenceController(
                self.window.controller,
                self.window
            )
            logger.debug("SequenceController criado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao criar SequenceController: {e}")
            self.window.sequence_controller = None

        # Fiducial Alignment Controller
        try:
            self.window.fiducial_alignment_controller = FiducialAlignmentController(
                self.window.config,
                self.window.controller.camera,
                self.window
            )
            logger.debug("FiducialAlignmentController criado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao criar FiducialAlignmentController: {e}")
            self.window.fiducial_alignment_controller = None

        # ConnectionManagerController será criado após setupUI()
        self.window.connection_manager_controller = None

        # Tension Measurement Controller
        try:
            self.window.tension_measurement_controller = TensionMeasurementController(
                self.window.controller,
                self.window.config,
                self.window.stencil_manager_wrapper,
                self.window
            )
            logger.debug("TensionMeasurementController criado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao criar TensionMeasurementController: {e}")
            self.window.tension_measurement_controller = None

        # Dialog Manager Controller
        try:
            self.window.dialog_manager_controller = DialogManagerController(
                self.window.stencil_manager_wrapper,
                self.window.report_manager_wrapper,
                self.window.report_config,
                self.window.controller,
                self.window
            )
            logger.debug("DialogManagerController criado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao criar DialogManagerController: {e}")
            self.window.dialog_manager_controller = None

        logger.debug("Controllers independentes de UI criados")

    def _setup_services(self):
        """Cria todos os services."""
        from consumo_lib.services import SequenceExecutionService, ResourceManager

        # Sequence Execution Service
        try:
            self.window.sequence_execution_service = SequenceExecutionService(
                self.window.controller,
                self.window
            )
            logger.debug("SequenceExecutionService criado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao criar SequenceExecutionService: {e}")
            self.window.sequence_execution_service = None

        # Connect signals from SequenceExecutionService
        if self.window.sequence_execution_service is not None:
            self.window.sequence_execution_service.image_captured.connect(
                self.window.on_sequence_image_captured
            )
            self.window.sequence_execution_service.sequence_completed.connect(
                self.window.on_sequence_completed
            )
            self.window.sequence_execution_service.sequence_error.connect(
                self.window.on_sequence_error
            )
            logger.debug("Signals de SequenceExecutionService conectados")

        # Resource Manager
        try:
            self.window.resource_manager = ResourceManager(self.window.controller)
            logger.debug("ResourceManager criado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao criar ResourceManager: {e}")
            self.window.resource_manager = None

        logger.debug("Services criados: sequence_execution, resource")

    def _setup_camera_config(self):
        """Carrega configurações de câmera salvas."""
        self.window._camera_mirror_x = self.window.config.get(
            "camera",
            "mirror_x",
            default=False
        )
        self.window._camera_mirror_y = self.window.config.get(
            "camera",
            "mirror_y",
            default=False
        )
        logger.debug(
            f"Configurações de câmera carregadas: "
            f"mirror_x={self.window._camera_mirror_x}, "
            f"mirror_y={self.window._camera_mirror_y}"
        )

    def _setup_ui(self):
        """Configura a interface gráfica."""
        self.window.setup_ui()
        logger.debug("UI criada via setup_ui()")

    def _setup_dependent_controllers(self):
        """Cria controllers que dependem de widgets da UI."""
        from consumo_lib.controllers import FileIOController, PositionManagerController

        # Configura widgets da UI no ConnectionManager para leitura de valores PLC
        # Isso permite que o ConnectionManager leia diretamente os valores digitados
        # pelo usuário antes de conectar (corrige bug de configurações não aplicadas)
        if hasattr(self.window, 'connection_mgr') and hasattr(self.window, 'plc_host_input') and hasattr(self.window, 'plc_port_input'):
            self.window.connection_mgr.set_ui_widgets(
                plc_host_input=self.window.plc_host_input,
                plc_port_input=self.window.plc_port_input
            )
            logger.debug("Widgets PLC configurados no ConnectionManager")

        # File IO Controller
        try:
            self.window.file_io_controller = FileIOController(
                self.window.controller,
                self.window.position_list_widget,
                self.window.sequence_widget,
                self.window
            )
            logger.debug("FileIOController criado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao criar FileIOController: {e}")
            self.window.file_io_controller = None

        # Position Manager Controller
        try:
            self.window.position_manager_controller = PositionManagerController(
                self.window.controller,
                self.window.position_list_widget,
                self.window
            )
            logger.debug("PositionManagerController criado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao criar PositionManagerController: {e}")
            self.window.position_manager_controller = None

        logger.debug("Controllers dependentes de UI criados")

    def _setup_keyboard_handler(self):
        """
        Configura KeyboardEventHandler após setup_ui.

        Instala o eventFilter global para capturar eventos de teclado
        e redirecionar para o MovementControlWidget quando o checkbox
        "Enable Keyboard Control" estiver marcado.
        """
        # O movement_widget está dentro da CNCControlTab
        if hasattr(self.window, 'cnc_tab') and hasattr(self.window.cnc_tab, 'movement_widget'):
            self.window.keyboard_handler.set_movement_widget(
                self.window.cnc_tab.movement_widget
            )
            # Callback para verificar se keyboard control está habilitado
            self.window.keyboard_handler.set_enable_control_callback(
                lambda: self.window.cnc_tab.movement_widget.keyboard_control_checkbox.isChecked()
                if hasattr(self.window.cnc_tab.movement_widget, 'keyboard_control_checkbox')
                else False
            )
            logger.debug("KeyboardEventHandler configurado com movement_widget")

            # CRÍTICO: Instalar o eventFilter no QApplication para capturar eventos globais
            from PyQt6.QtWidgets import QApplication
            QApplication.instance().installEventFilter(self.window.keyboard_handler)
            logger.debug("KeyboardEventHandler instalado como eventFilter global da QApplication")

    def _setup_menu(self):
        """Configura o menu da aplicação."""
        self.window.setup_menu()
        logger.debug("Menu configurado")

    def _setup_signals(self):
        """Cria SignalAggregator e conecta todos os signals."""
        from consumo_lib.handlers import SignalAggregator

        # Centraliza TODOS os handlers de signals
        self.window.signal_aggregator = SignalAggregator(self.window)
        logger.debug("SignalAggregator criado e todos os signals conectados")

    def _setup_ui_state(self):
        """Configura estado inicial da UI."""
        # Painel de conexão inicialmente oculto
        self.window.connection_group.setVisible(False)

        logger.debug("Estado inicial da UI configurado")

    def _setup_auto_connect(self):
        """Configura auto-connect se preferido."""
        logger.debug("Verificando auto-connect...")

        # Tenta auto-connect se configurado
        self.window.connection_coordinator.attempt_auto_connect()

        logger.debug(
            "Verificando conexão PLC no arranque; backend=%s, conectado=%s",
            type(self.window.controller.cnc).__name__,
            getattr(self.window.controller.cnc, 'is_connected', False)
        )

        if isinstance(self.window.controller.cnc, PLCAxisController):
            # Estado inicial - aguardando tentativa de conexão automática
            self.window.connect_cnc_btn.setText("Conectar PLC")
            self.window.cnc_status.setText("Iniciando...")
            self.window.statusBar().showMessage(
                "Iniciando aplicação - conexão automática ao PLC em breve..."
            )
            logger.info("Aplicação iniciada. Tentativa de conexão automática ao PLC agendada.")

        # Auto-connect apenas após a interface estar pronta
        QTimer.singleShot(500, self.window._attempt_auto_connect)

    def _setup_timers(self):
        """Configura timers."""
        # Timer para atualizar a posição
        self.window.update_timer = QTimer(self.window)
        self.window.update_timer.timeout.connect(self.window.on_update_timer)
        self.window.update_timer.start(1000)  # Atualiza a cada 1000ms

        logger.debug("Timers configurados")

        # Capturar eventos de teclado para movimentação via KeyboardEventHandler
        # (já está configurado em _setup_keyboard_handler)
