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

    def __init__(self, main_window_class, factories=None):
        """
        Inicializa o coordenador de setup.

        Args:
            main_window_class: Classe AOIControllerApp (não instância ainda)
            factories: Dict com factories opcionais (Dependency Injection)
                    Se None, cria factories internamente (backward compatibility)
        """
        self.main_window_class = main_window_class
        self.window = None  # Será definido em setup()

        # Dependency Injection: usa factories fornecidas ou cria defaults
        if factories is None:
            from consumo_lib.factories import ApplicationComponentsFactory
            self.factory = ApplicationComponentsFactory()
        else:
            self.factory = factories

        logger.debug("SetupCoordinator inicializado com ApplicationComponentsFactory")

    def setup(self, window):
        """
        Executa todo o setup da aplicação usando factories.

        Args:
            window: Instância de AOIControllerApp já criada com super().__init__()
        """
        self.window = window

        # Usar factory para criar todos os componentes de uma vez
        # A factory já copia todos os componentes para a window automaticamente
        # Ordem de criação é gerenciada internamente pela factory
        all_components = self.factory.create_all_components(window)

        # NOTA: A factory já copia os componentes para a window via _copy_to_window()
        # Não precisamos fazer setattr() aqui pois a factory já fez isso
        # all_components é retornado para possível uso futuro, mas os componentes já estão na window

        # Ordem de setup é crítica! Executar métodos na ordem correta
        self._setup_basic_config_dependencies()     # 1. Config dependências
        self._setup_camera_config_dependencies()      # 2. Camera config dependências
        self._setup_ui()                            # 3. Interface gráfica
        self._setup_dependent_controllers()         # 4. Controllers dependentes de UI
        self._setup_keyboard_handler_dependencies()   # 5. Keyboard handler dependências
        self._setup_menu()                          # 6. Menu
        self._setup_signals_dependencies()          # 7. Signals dependencies
        self._setup_ui_state()                       # 8. Estado inicial da UI
        self._setup_auto_connect()                   # 9. Auto-connect
        self._setup_timers()                         # 10. Timers

        logger.info("Setup da aplicação concluído com sucesso via factories")

    def _setup_basic_config_dependencies(self):
        """
        Configuração básica da janela (usa config criado pela factory).

        Nota: config já foi criado pela factory, apenas configura a janela.
        """
        self.window.setWindowTitle("Controle de Inspeção Óptica Automatizada")
        self.window.setGeometry(100, 100, 1200, 800)

        logger.debug("Configuração básica concluída (config via factory)")

    # NOTA: Os métodos _setup_core_controller, _setup_managers, _setup_coordinators,
    # _setup_handlers, _setup_controllers, _setup_services foram removidos na Fase 8
    # porque a ApplicationComponentsFactory agora cria todos esses componentes.
    # A ordem de criação é gerenciada internamente pela factory.

    # NOTA: Os métodos _setup_coordinators, _setup_managers, _setup_handlers,
    # _setup_controllers, _setup_services foram removidos na Fase 8
    # porque a ApplicationComponentsFactory agora cria todos esses componentes.

    def _setup_camera_config_dependencies(self):
        """
        Carrega configurações de câmera (usa config criado pela factory).

        Nota: config já foi criado pela factory, apenas lê as configurações.
        """
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
            f"Configurações de câmera carregadas (via factory): "
            f"mirror_x={self.window._camera_mirror_x}, "
            f"mirror_y={self.window._camera_mirror_y}"
        )
    def _setup_ui(self):
        """Configura a interface gráfica."""
        self.window.setup_ui()
        logger.debug("UI criada via setup_ui()")

    def _setup_dependent_controllers(self):
        """
        Cria controllers que dependem de widgets da UI (via factory).

        Nota: Usa factory.create_dependent_controllers() que chama ControllersFactory.
        """
        # Chamar factory para criar controllers dependentes de UI
        dependent_controllers = self.factory.create_dependent_controllers(self.window)

        # Armazenar na window para compatibilidade
        for key, value in dependent_controllers.items():
            setattr(self.window, key, value)

        logger.debug(f"Controllers dependentes de UI criados via factory: {len(dependent_controllers)} componentes")


    def _setup_keyboard_handler_dependencies(self):
        """
        Configura KeyboardEventHandler após setup_ui (usa handler criado pela factory).

        Instala o eventFilter global para capturar eventos de teclado.
        """
        logger.info("🎹 _setup_keyboard_handler_dependencies() INICIADO")

        # Verificar se keyboard_handler existe (criado pela factory)
        if not hasattr(self.window, 'keyboard_handler'):
            logger.error("❌ window.keyboard_handler NÃO EXISTE (não foi criado pela factory)!")
            return
        logger.info(f"✅ keyboard_handler existe via factory: {self.window.keyboard_handler}")

        # O movement_widget está exposto diretamente na window
        # self.window.movement_widget = self.window.cnc_control_tab.movement_widget
        if hasattr(self.window, 'movement_widget') and self.window.movement_widget is not None:
            logger.info(f"✅ movement_widget existe na window: {self.window.movement_widget}")

            self.window.keyboard_handler.set_movement_widget(self.window.movement_widget)

            # Callback para verificar se keyboard control está habilitado
            # movement_widget tem o keyboard_control_checkbox
            if hasattr(self.window.movement_widget, 'keyboard_control_checkbox'):
                self.window.keyboard_handler.set_enable_control_callback(
                    lambda: self.window.movement_widget.keyboard_control_checkbox.isChecked()
                )
                logger.info("✅ Callback de checkbox configurado")
            else:
                logger.warning("⚠️ keyboard_control_checkbox não encontrado em movement_widget")
                # Define callback que retorna False (sempre desabilitado)
                self.window.keyboard_handler.set_enable_control_callback(lambda: False)

            logger.info("✅ KeyboardEventHandler configurado com movement_widget e callback")

            # CRÍTICO: Instalar o eventFilter no QApplication para capturar eventos globais
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()
            logger.info(f"QApplication.instance(): {app}")

            app.installEventFilter(self.window.keyboard_handler)
            logger.warning("eventFilter INSTALADO no QApplication - Deve capturar todos os eventos de teclado agora!")
        else:
            logger.error("movement_widget não existe na window!")
            logger.error(f"hasattr(window, 'movement_widget'): {hasattr(self.window, 'movement_widget')}")
            logger.error(f"window.movement_widget: {getattr(self.window, 'movement_widget', 'NOT_FOUND')}")

    def _setup_menu(self):
        """Configura o menu da aplicação."""
        self.window.setup_menu()
        logger.debug("Menu configurado")

    def _setup_signals_dependencies(self):
        """
        Configura signals distribuídos pelos controllers (criados pela factory).

        ANTES: SignalAggregator centralizava todos os handlers (anti-pattern)
        DEPOIS: Cada controller gerencia seus próprios handlers via setup_ui_handlers()

        Refatoração Fases 1.2.1 a 1.2.6 (2026-01-14):
        - Recipe handlers → RecipeManagerController
        - Tension handlers → TensionMeasurementController
        - Inspection handlers → InspectionUIController
        - Camera/Calibration handlers → CameraController/CalibrationController/FiducialAlignmentController
        - Map/Position handlers → MapController/PositionManagerController
        - Stencil/Report handlers → StencilManagerWrapper/ReportDialogController

        O SignalAggregator foi completamente removido (Fase 1.2.8).
        """
        # SignalAggregator removido - cada controller gerencia seus próprios handlers
        logger.debug("Signal handlers configurados via setup_ui_handlers() em cada controller")

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
            # REMOVIDO: cnc_status não existe mais no painel esquerdo
            # A posição agora está dentro de MovementControlWidget (aba CNC Control)
            if hasattr(self.window, 'cnc_status'):
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
