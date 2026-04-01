# Standard library
import sys
import os
import logging

# Configure logger
logger = logging.getLogger(__name__)

# Autenticação
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
    StencilTracker, Stencil, TensionRecord
)
from aoi_lib.plc_axis_controller import PLCAxisController
from aoi_lib.config_manager import AOIConfigManager, SettingsDialog
from aoi_lib.fov_calibration import FOVCalibration, CameraFOVConverter, ClickableVideoLabel

# Consumo lib - barrier packages
from consumo_lib.dialogs import (
    StencilManagerDialog, StencilCreateDialog,
    FOVCalibrationDialog, CrosshairSettingsDialog,
    ReportSettingsDialog, AboutDialog,
    LoginDialog,
)
from consumo_lib.tabs import (
    CNCControlTab, TensionTab, TrackingTab
)
from consumo_lib.controllers import (
    MapController, CameraSettingsController, CalibrationController,
    ReportDialogController, SequenceController,
    ConnectionManagerController,
    TensionMeasurementController, DialogManagerController,
    FileIOController, PositionManagerController, RecipeManagerController
)
from consumo_lib.coordinators import SetupCoordinator
from consumo_lib.handlers import KeyboardEventHandler, MenuHandler, DialogRouter
from consumo_lib.ui_builders import MainUIBuilder
from consumo_lib.services import SequenceExecutionService, ResourceManager
from consumo_lib.managers import ConnectionManager, RecipeManagerWrapper, StencilManagerWrapper, ReportManagerWrapper
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

# NOVO: Componentes modulares da MainWindow
from consumo_lib.utils.main_window import (
    MainWindowState,
    MainWindowInitializer,
    MainWindowEventHandlers,
)

# NOVO (Fase 4): Factories para injeção de dependência
from consumo_lib.factories import ControllerFactory, HardwareFactory

# NOVO (Fase 4): Facades para interfaces simplificadas
from consumo_lib.facades import (
    HardwareConnectionFacade,
    PositionManagerFacade,
    AuthenticationManager
)

# NOVO (Fase 4): SequenceManager
from consumo_lib.managers.sequence_manager import SequenceManager


class AOIControllerApp(QMainWindow):
    """
    Aplicação Principal - Orchestrator Puro.

    Responsabilidades:
    - Coordenar inicialização via SetupCoordinator
    - Instanciar componentes modulares (state, initializer, event_handlers, workflows)
    - Delegar funcionalidades para componentes apropriados
    - Manter apenas coordenação de alto nível

    Antes da refatoração: 1,385 linhas, 54 métodos
    Depois da refatoração: ~300 linhas, métodos delegados
    """

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

        # NOVO - Carrega configuração primeiro (para auto-login)
        self.config_manager = AOIConfigManager()

        # NOVO - FASE 4: Criar RoleManager para verificação de permissões
        from consumo_lib.managers.role_manager import RoleManager
        self.role_manager = RoleManager()
        logger.info(f"RoleManager criado: role={self.role_manager.get_current_role()}")

        # NOVO - FASE 1: Autenticação de usuário (com auto-login)
        self.auth_service = AuthService()

        # Verifica se deve fazer auto-login
        require_login = self.config_manager.get_require_login_on_startup()

        if require_login:
            # Login obrigatório - mostra dialog
            if not self.show_login_dialog():
                logger.info("Login cancelado pelo usuário, fechando aplicação")
                sys.exit(0)
        else:
            # Auto-login habilitado
            default_role = self.config_manager.get_default_role()
            self._perform_auto_login(default_role)

        # ─────────────────────────────────────────────────────────────────────
        # NOVO: Inicializa componentes modulares ANTES do SetupCoordinator
        # ─────────────────────────────────────────────────────────────────────
        # Componente 1: Estado da aplicação (PRECISA SER PRIMEIRO)
        self._app_state = MainWindowState()

        # Inicializa stencil_identification como None
        # Será definido quando TrackingDialog for aberto ou pelo TabFactory (legado)
        self.stencil_identification = None
        self._tracking_dialog = None

        # Componente 2: Initializer (PRECISA SER ANTES do SetupCoordinator.setup)
        # Criamos o initializer, mas NÃO chamamos initialize_all() ainda
        # O SetupCoordinator vai chamar setup_ui(), setup_menu(), etc. individualmente
        setup_coordinator = SetupCoordinator(AOIControllerApp)
        self._initializer = MainWindowInitializer(self, setup_coordinator)

        # Agora sim, executa o SetupCoordinator
        setup_coordinator.setup(self)

        # ─────────────────────────────────────────────────────────────────────
        # Continua inicialização dos componentes modulares
        # ─────────────────────────────────────────────────────────────────────
        self._setup_modular_components(setup_coordinator)

        # Aplica permissões baseadas no role do usuário
        QTimer.singleShot(500, self._apply_role_permissions)

        # Conecta cleanup ao evento de fechamento
        QApplication.instance().aboutToQuit.connect(self._cleanup_resources)

    def _setup_modular_components(self, setup_coordinator):
        """
        Inicializa os componentes modulares da MainWindow.

        Args:
            setup_coordinator: SetupCoordinator para initializer

        NOTA:
        - _app_state e _initializer já foram inicializados antes do SetupCoordinator.setup()
        - setup_ui(), setup_menu() e _attempt_auto_connect() já foram chamados pelo SetupCoordinator

        NOVO (Fase 4): Injeta factories e cria facades para baixo acoplamento.
        """
        # ─────────────────────────────────────────────────────────────────────
        # Componentes modulares básicos
        # ─────────────────────────────────────────────────────────────────────
        # Componente 1: Estado da aplicação (já criado, agora configurar referências)
        self._app_state.set_references(self, self.auth_service)

        # Componente 2: Initializer (já criado, setup já foi chamado pelo SetupCoordinator)
        # Não chamar initialize_all() novamente pois isso duplicaria setup_ui(), setup_menu(), etc.

        # Componente 3: Event handlers
        self._event_handlers = MainWindowEventHandlers(self, self._app_state)



        # ─────────────────────────────────────────────────────────────────────
        # NOVO (Fase 4): Factories para criar componentes
        # ─────────────────────────────────────────────────────────────────────
        # Obtém controller e config do SetupCoordinator
        # NOTA: SetupCoordinator define self.controller e self.config na window
        controller = self.controller
        config = self.config

        # REMOVIDO (2026-03-29): TabFactory - MainUIBuilder cria TensionMeasurementTab diretamente

        # Factory 1: ControllerFactory - cria controllers
        self._controller_factory = ControllerFactory(
            controller,
            config,
            self
        )

        # Factory 3: HardwareFactory - cria componentes de hardware
        self._hardware_factory = HardwareFactory(
            controller,
            config,
            self
        )

        # ─────────────────────────────────────────────────────────────────────
        # NOVO (Fase 4): Facades para interfaces simplificadas
        # ─────────────────────────────────────────────────────────────────────
        # Facade 1: HardwareConnectionFacade - gerencia conexões de hardware
        connection_manager = self._hardware_factory.create_connection_manager()
        self.hardware_facade = HardwareConnectionFacade(
            connection_manager,
            self
        )

        # Facade 2: PositionManagerFacade - gerencia posições de inspeção
        position_controller = self._controller_factory.create_position_manager_controller()
        self.position_facade = PositionManagerFacade(
            position_controller,
            self
        )

        # Facade 3: AuthenticationManager - gerencia autenticação e permissões
        from consumo_lib.managers.auth_config_manager import AuthConfigManager
        auth_config_manager = AuthConfigManager(
            config_manager=config,
            role_manager=self.role_manager if hasattr(self, 'role_manager') else None,
            auth_service=self.auth_service
        )
        self.auth_manager = AuthenticationManager(
            self.auth_service,
            auth_config_manager,
            self
        )

        # Manager: SequenceManager - gerencia sequências de inspeção
        sequence_controller = self._controller_factory.create_sequence_controller()
        self.sequence_manager = SequenceManager(
            sequence_controller,
            self
        )

        logger.info("Componentes modulares da MainWindow inicializados (com factories e facades)")

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
            return getattr(self.dialog_router, name)
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    # =========================================================================
    # DELEGADORES PARA INITIALIZER (compatibilidade com SetupCoordinator)
    # =========================================================================

    def setup_ui(self):
        """
        Configura a UI principal (delega para MainWindowInitializer).

        Este método é chamado pelo SetupCoordinator._setup_ui().
        """
        if hasattr(self, '_initializer'):
            self._initializer.setup_ui()

    def setup_menu(self):
        """
        Configura o menu da aplicação (delega para MainWindowInitializer).

        Este método é chamado pelo SetupCoordinator._setup_menu().
        """
        if hasattr(self, '_initializer'):
            self._initializer.setup_menu()

    def _attempt_auto_connect(self):
        """
        Tenta conexão automática ao iniciar (delega para MainWindowInitializer).

        Este método é chamado pelo SetupCoordinator._setup_auto_connect().
        """
        if hasattr(self, '_initializer'):
            self._initializer.attempt_auto_connect()

    # =========================================================================
    # AUTENTICAÇÃO (NOVO - FASE 1)
    # =========================================================================

    def show_login_dialog(self) -> bool:
        """
        Exibe dialog de login e aguarda autenticação.

        NOVO (Fase 4): Delega para AuthenticationManager.

        Returns:
            True se login foi bem-sucedido, False se cancelado
        """
        if hasattr(self, 'auth_manager'):
            return self.auth_manager.show_login_dialog()
        else:
            # Fallback para implementação legada (enquanto auth_manager não está disponível)
            login_dialog = LoginDialog(self.auth_service, self)
            result = login_dialog.exec()

            if result == QDialog.DialogCode.Accepted:
                user = self.auth_service.get_current_user()
                logger.info(f"Usuário logado: {user}")
                QTimer.singleShot(100, self._apply_role_permissions)
                return True
            else:
                return False

    def _perform_auto_login(self, default_role: str):
        """
        Realiza auto-login com o papel padrão configurado.

        NOVO (Fase 4): Delega para AuthenticationManager.

        Args:
            default_role: Papel (role) padrão para auto-login
        """
        if hasattr(self, 'auth_manager'):
            self.auth_manager.perform_auto_login(default_role)
        else:
            # Fallback para implementação legada
            try:
                # Valida role
                from aoi_lib.auth.user import UserRole
                try:
                    role_enum = UserRole(default_role)
                except ValueError:
                    logger.warning(f"Role inválido para auto-login: {default_role}, usando 'operator'")
                    role_enum = UserRole.OPERATOR
                    default_role = "operator"

                # Busca usuário padrão para o role
                role_to_user = {
                    "operator": "operator",
                    "engineering": "eng",
                    "quality": "quality",
                    "admin": "admin"
                }

                username = role_to_user.get(default_role, "operator")

                # Autentica com o usuário padrão
                password_map = {
                    "operator": "operator123",
                    "eng": "eng123",
                    "quality": "quality123",
                    "admin": "admin123"
                }

                password = password_map.get(username, "operator123")

                if self.auth_service.authenticate(username, password):
                    logger.info(f"Auto-login bem-sucedido: {username} ({default_role})")
                    QTimer.singleShot(100, self._apply_role_permissions)
                else:
                    logger.warning(f"Falha no auto-login para {username}, mostrando diálogo")
                    self.show_login_dialog()
            except Exception as e:
                logger.error(f"Erro ao realizar auto-login: {e}")
                self.show_login_dialog()

    def _apply_role_permissions(self):
        """
        Aplica permissões baseadas no role do usuário.

        NOVO (Fase 4): Delega para AuthenticationManager.
        """
        if hasattr(self, 'auth_manager'):
            self.auth_manager.apply_role_permissions()
        else:
            # Fallback para implementação legada
            self._app_state.apply_role_permissions()

    def show_auth_settings(self):
        """
        Exibe diálogo de configurações de autenticação.

        Permite usuários engineering+ configurar:
        - Exigência de login ao iniciar
        - Papel padrão para auto-login
        """
        from consumo_lib.dialogs.auth_settings_dialog import AuthenticationSettingsDialog

        # Verifica se usuário está autenticado
        if not self.auth_service.is_authenticated():
            QMessageBox.warning(
                self,
                "Usuário Não Autenticado",
                "Você precisa estar autenticado para acessar configurações de autenticação.",
                QMessageBox.StandardButton.Ok
            )
            return

        # Verifica permissões
        current_role = self.role_manager.get_current_role()
        if not current_role:
            QMessageBox.warning(
                self,
                "Permissão Negada",
                "Não foi possível identificar seu papel (role) no sistema.",
                QMessageBox.StandardButton.Ok
            )
            return

        # Cria gerenciador de configuração de autenticação
        from consumo_lib.managers.auth_config_manager import AuthConfigManager
        auth_config_mgr = AuthConfigManager(
            config_manager=self.config_manager,
            role_manager=self.role_manager,
            auth_service=self.auth_service
        )

        # Cria e executa diálogo
        dialog = AuthenticationSettingsDialog(
            auth_config_manager=auth_config_mgr,
            current_role=current_role,
            parent=self
        )

        # Conecta sinal de mudança para atualizar menu se necessário
        dialog.config_changed.connect(self._on_auth_config_changed)

        dialog.exec()

    def show_theme_settings(self):
        """
        Exibe diálogo de configurações de tema.

        Permite usuários selecionar:
        - Light Theme (tema claro)
        - Dark Theme (tema escuro)
        - System Theme (segue OS)

        A escolha é aplicada imediatamente e salva na configuração.
        """
        from consumo_lib.dialogs.theme_settings import show_theme_settings_dialog
        from consumo_lib.ui.theme_manager import get_theme_manager

        # Obtém ThemeManager
        theme_mgr = get_theme_manager()
        if theme_mgr is None:
            QMessageBox.warning(
                self,
                "Gerenciador de Tema Não Disponível",
                "O gerenciador de temas não foi inicializado corretamente.",
                QMessageBox.StandardButton.Ok
            )
            return

        # Mostra diálogo de seleção de tema
        # Se o usuário confirmar, o diálogo já aplica e salva o tema
        selected_theme = show_theme_settings_dialog(theme_mgr, parent=self)

        if selected_theme:
            logger.info(f"Tema alterado via diálogo: {selected_theme}")

    def show_tension_criteria_dialog(self):
        """
        Exibe diálogo de configuração de critérios de tensão.

        Permite configurar:
        - Tensão mínima/máxima aceitável
        - Limites de warning (alerta)

        Critérios são globais e aplicados a todos os stencils.
        """
        from consumo_lib.dialogs.tension_criteria_dialog import TensionCriteriaDialog
        from consumo_lib.managers.tension_criteria_manager import TensionCriteriaManager

        # Cria gerenciador de critérios
        criteria_mgr = TensionCriteriaManager(self.config_manager)

        # Cria e executa diálogo
        dialog = TensionCriteriaDialog(
            criteria_manager=criteria_mgr,
            parent=self
        )

        # Conecta sinal para atualizar aba de medição quando critérios mudam
        dialog.criteria_changed.connect(self._on_tension_criteria_changed)

        dialog.exec()

    def _on_tension_criteria_changed(self, criteria):
        """
        Handler quando critérios de tensão são alterados.

        Args:
            criteria: TensionCriteriaConfig com novos valores
        """
        logger.info(f"Critérios de tensão atualizados: min={criteria.min_tension}, max={criteria.max_tension}")

        # Atualiza aba de medição de tensão se existir
        if hasattr(self, 'tension_measurement_tab') and self.tension_measurement_tab:
            self.tension_measurement_tab.update_criteria(criteria)

    def open_connection_dialog(self):
        """
        Abre o diálogo de conexão com o PLC.

        NOVO na release v0.5-tension:
        - Substitui o groupbox "Conexão" que estava na janela principal
        - Diálogo não-modal, permite operar a janela principal
        """
        from consumo_lib.dialogs import ConnectionDialog

        # Cria e mostra o diálogo (não-modal)
        if not hasattr(self, '_connection_dialog') or self._connection_dialog is None:
            self._connection_dialog = ConnectionDialog(self, parent=self)

        self._connection_dialog.show()
        self._connection_dialog.raise_()
        self._connection_dialog.activateWindow()

    def _on_auth_config_changed(self):
        """
        Handler chamado quando configuração de autenticação muda.

        Atualiza estado da aplicação se necessário.
        """
        logger.info("Configuração de autenticação foi alterada")
        # TODO: Implementar lógica de atualização se necessário
        # Por exemplo, atualizar label de usuário atual, etc.

    # =========================================================================
    # EVENT HANDLERS (Delegação para MainWindowEventHandlers)
    # =========================================================================

    def on_update_timer(self):
        """Delegate para MainWindowEventHandlers."""
        self._event_handlers.on_update_timer()

    def on_image_captured(self, image, position_name):
        """Delegate para MainWindowEventHandlers."""
        self._event_handlers.on_image_captured(image, position_name)

    def on_sequence_completed(self):
        """Delegate para MainWindowEventHandlers."""
        self._event_handlers.on_sequence_completed()

    def on_sequence_error(self, error_message):
        """Delegate para MainWindowEventHandlers."""
        self._event_handlers.on_sequence_error(error_message)

    def on_sequence_image_captured(self, result):
        """Delegate para MainWindowEventHandlers."""
        self._event_handlers.on_sequence_image_captured(result)

    def _on_connect_btn_clicked(self):
        """Delegate para MainWindowEventHandlers."""
        self._event_handlers.on_connect_btn_clicked()

    # =========================================================================
    # GERENCIAMENTO DE RECEITAS (Métodos delegados mantidos para compatibilidade)
    # =========================================================================

    def apply_recipe_to_capture(self):
        """Aplica configurações de captura da receita (delega para RecipeManagerController)."""
        if self.recipe_manager_controller is None:
            logger.error("RecipeManager não está disponível")
            return

        map_widgets = {k: v for k, v in {
            'map_step_x_edit': getattr(self, 'map_step_x_edit', None),
            'map_step_y_edit': getattr(self, 'map_step_y_edit', None),
            'spin_capture_delay': getattr(self, 'spin_capture_delay', None)
        }.items() if v is not None}

        self.recipe_manager_controller.apply_recipe_to_capture(self.current_recipe, map_widgets or None)

    def apply_recipe_to_tension(self):
        """Aplica configurações de tensão da receita (delega para RecipeManagerController)."""
        if self.recipe_manager_controller is None:
            logger.error("RecipeManager não está disponível")
            return
        self.recipe_manager_controller.apply_recipe_to_tension(self.current_recipe)

    def _run_tension_measurement(self):
        """Executa medição de tensão (delega para TensionMeasurementController)."""
        tracking_was_visible = (
            hasattr(self, '_tracking_dialog')
            and self._tracking_dialog is not None
            and self._tracking_dialog.isVisible()
        )

        if tracking_was_visible:
            self._tracking_dialog.hide()

        if self.tension_measurement_controller is not None:
            try:
                self.tension_measurement_controller.run_recipe_measurement(
                    self.current_stencil,
                    self.current_recipe,
                    interaction_parent=self._tracking_dialog if tracking_was_visible else self,
                )
            finally:
                if tracking_was_visible and self._tracking_dialog is not None:
                    self._tracking_dialog.show()
                    self._tracking_dialog.raise_()
                    self._tracking_dialog.activateWindow()
        else:
            try:
                logger.error("TensionMeasurementController não está disponível")
                QMessageBox.warning(self, "Erro", "TensionMeasurementController não está disponível")
            finally:
                if tracking_was_visible and self._tracking_dialog is not None:
                    self._tracking_dialog.show()
                    self._tracking_dialog.raise_()
                    self._tracking_dialog.activateWindow()

    def _save_tension_to_history(self, tension_dialog):
        """Salva resultado da medição de tensão (delega para TensionMeasurementController)."""
        if self.tension_measurement_controller is not None:
            self.tension_measurement_controller.save_measurement(
                self.current_stencil,
                self.current_recipe,
                tension_dialog
            )
        else:
            logger.error("TensionMeasurementController não está disponível")

    # =========================================================================
    # GERENCIAMENTO DE SEQUÊNCIAS (Métodos delegados mantidos para compatibilidade)
    # =========================================================================

    def create_sequence_from_registry(self):
        """Cria uma sequência a partir de posições registradas (delega para SequenceExecutionService)."""
        if self.sequence_execution_service is None:
            logger.error("SequenceExecutionService não está disponível")
            return

        sequence = self.sequence_execution_service.create_sequence_from_registry(
            self.position_registry,
            self.sequence_widget,
            self.position_list_widget
        )

        if sequence:
            self._app_state.sequence = sequence

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
        self.file_io_controller.save_gcode(self._app_state.sequence)

    def refresh_ports(self):
        """Atualiza a lista de portas seriais disponíveis (delega para ConnectionManager)."""
        self.connection_mgr.refresh_serial_ports(self.cnc_port_combo)

    def _apply_plc_ui_settings(self):
        """Atualiza IP/porta do PLC vindos da UI (delega para ConnectionManagerController)."""
        if self.connection_manager_controller is not None:
            self.connection_manager_controller.apply_plc_ui_settings(
                self.plc_host_input,
                self.plc_port_input
            )
        else:
            logger.error("ConnectionManagerController não está disponível")

    def connect_cnc(self):
        """Conecta/desconecta ao PLC (delega para ConnectionManager)."""
        # NOTA (release/v0.5-tension): GRBL removido, apenas PLC é suportado
        self.connection_mgr.toggle_plc()

    def connect_camera(self):
        """Conecta à câmera (delega para ConnectionManagerController)."""
        if not hasattr(self, 'camera_id_combo') or not hasattr(self, 'connect_camera_btn'):
            QMessageBox.information(
                self,
                "Indisponível",
                "Os controles de câmera foram removidos da interface."
            )
            return
        if self.connection_manager_controller is not None:
            self.connection_manager_controller.connect_camera(
                self.camera_id_combo,
                self.connect_camera_btn
            )
        else:
            logger.error("ConnectionManagerController não está disponível")

    def test_camera(self):
        """Testa a captura de imagem da câmera (delega para ConnectionManagerController)."""
        if getattr(self, 'camera_preview', None) is None:
            QMessageBox.information(
                self,
                "Indisponível",
                "O preview de câmera foi removido da interface."
            )
            return
        if self.connection_manager_controller is not None:
            self.connection_manager_controller.test_camera()
        else:
            logger.error("ConnectionManagerController não está disponível")

    def update_position_display(self):
        """Atualiza a exibição da posição atual (delega para MainWindowState)."""
        self._app_state.update_position_display()

    def add_current_position(self):
        """Adiciona a posição atual à lista (delega para PositionManagerController)."""
        if self.position_manager_controller is not None:
            self.position_manager_controller.add_current_position()
        else:
            logger.error("PositionManager não está disponível")

    def remove_position(self):
        """Remove a posição selecionada (delega para PositionManagerController)."""
        if self.position_manager_controller is not None:
            self.position_manager_controller.remove_position()
        else:
            logger.error("PositionManager não está disponível")

    def on_position_selected(self, position):
        """Manipula a seleção de uma posição (delega para PositionManagerController)."""
        if self.position_manager_controller is not None:
            self.position_manager_controller.on_position_selected(position)
        else:
            logger.error("PositionManager não está disponível")

    def create_sequence(self):
        """Cria uma nova sequência com as posições atuais (delega para PositionManagerController)."""
        if self.position_manager_controller is not None:
            current_sequence_ref = [self._app_state.sequence]
            self.position_manager_controller.create_sequence(
                self.sequence_widget.sequence_name,
                self.sequence_widget.sequence_status,
                current_sequence_ref
            )
            self._app_state.sequence = current_sequence_ref[0]
        else:
            logger.error("PositionManager não está disponível")

    def run_sequence(self):
        """Executa a sequência atual (delega para SequenceExecutionService)."""
        if self.sequence_execution_service is None:
            logger.error("SequenceExecutionService não está disponível")
            return

        self.sequence_execution_service.run_sequence(
            self._app_state.sequence,
            self.movement_widget,
            self.sequence_widget,
            self.results_table
        )

    def stop_sequence(self):
        """Para a execução da sequência atual (delega para SequenceExecutionService)."""
        if self.sequence_execution_service is None:
            logger.error("SequenceExecutionService não está disponível")
            return

        self.sequence_execution_service.stop_sequence(self.sequence_widget)

    def save_program(self):
        """Salva programa de inspeção atual (delega para FileIOController)."""
        if self.file_io_controller is None:
            logger.error("FileIO não está disponível")
            return
        self.file_io_controller.save_program(self._app_state.sequence)

    def load_program(self):
        """Carrega programa de inspeção salvo (delega para FileIOController)."""
        if self.file_io_controller is None:
            logger.error("FileIO não está disponível")
            return
        self.file_io_controller.load_program()

    def open_stencil_tension_dialog(self):
        """Abre diálogo simples de medição de tensão (delega para DialogManagerController)."""
        if self.dialog_manager_controller is not None:
            self.dialog_manager_controller.open_simple_tension_dialog()
        else:
            logger.error("DialogManagerController não está disponível")
            if not self.controller.cnc.is_connected:
                QMessageBox.warning(self, "Aviso", "Conecte a CNC antes de medir a tensão do stencil.")
                return
            from consumo_lib.dialogs.tension import TensionMeasurementDialog
            dlg = TensionMeasurementDialog(self, self.controller.cnc)
            dlg.exec()

    def open_movement_dialog(self):
        """
        Abre diálogo de controle de movimento CNC.

        O diálogo é não-modal e permanece acima da janela principal,
        mas não bloqueia a interação com ela.
        """
        from consumo_lib.dialogs import MovementDialog

        # Cria ou reutiliza o diálogo
        if not hasattr(self, '_movement_dialog') or self._movement_dialog is None:
            self._movement_dialog = MovementDialog(
                self.controller.cnc,
                self.config,
                parent=self
            )

        # Mostra o diálogo
        self._movement_dialog.show()
        self._movement_dialog.raise_()
        self._movement_dialog.activateWindow()
        logger.debug("MovementDialog aberto")

    def open_plc_monitor_dialog(self):
        """
        Abre diálogo de monitoramento do CLP.

        O diálogo é não-modal e permanece acima da janela principal,
        mas não bloqueia a interação com ela.
        """
        from consumo_lib.dialogs import PLCMonitorDialog

        # Cria ou reutiliza o diálogo
        if not hasattr(self, '_plc_monitor_dialog') or self._plc_monitor_dialog is None:
            self._plc_monitor_dialog = PLCMonitorDialog(
                self.controller,
                config_manager=self.config_manager,
                parent=self
            )

        # Mostra o diálogo
        self._plc_monitor_dialog.show()
        self._plc_monitor_dialog.raise_()
        self._plc_monitor_dialog.activateWindow()
        logger.debug("PLCMonitorDialog aberto")

    def open_tracking_dialog(self):
        """
        Abre diálogo de rastreabilidade (identificação de stencil).

        O diálogo é não-modal e permanece acima da janela principal,
        mas não bloqueia a interação com ela.

        Substitui a aba "Rastreabilidade" removida da interface.
        """
        from consumo_lib.dialogs import TrackingDialog

        # Cria ou reutiliza o diálogo
        if not hasattr(self, '_tracking_dialog') or self._tracking_dialog is None:
            self._tracking_dialog = TrackingDialog(
                self.stencil_tracker,
                parent=self
            )

            # Conecta sinais do diálogo ao StencilManagerWrapper
            self._tracking_dialog.stencil_selected.connect(
                self.stencil_manager_wrapper.select_stencil
            )
            self._tracking_dialog.stencil_cleared.connect(
                self.stencil_manager_wrapper.clear_selection
            )
            self._tracking_dialog.recipe_requested.connect(
                self.recipe_manager_controller.load_recipe
            )
            self._tracking_dialog.measurement_requested.connect(
                self._run_tension_measurement
            )

            # Mantém referência global para stencil_identification
            # (usado por controllers que precisam atualizar o widget)
            self.stencil_identification = self._tracking_dialog.stencil_identification

        # Mostra o diálogo
        self._tracking_dialog.show()
        self._tracking_dialog.raise_()
        self._tracking_dialog.activateWindow()
        logger.debug("TrackingDialog aberto")

    def _cleanup_resources(self):
        """Para tudo que possa manter o Qt vivo após o fechamento (delega para ResourceManager)."""
        if self.resource_manager is None:
            logger.error("ResourceManager não está disponível")
            return

        self.resource_manager.cleanup_all(self)

    def closeEvent(self, event):
        """Evento de fechamento da janela."""
        self._cleanup_resources()
        event.accept()

    # =========================================================================
    # PROPRIEDADES PARA COMPATIBILIDADE (Acesso via _app_state)
    # =========================================================================

    @property
    def current_sequence(self):
        """Retorna a sequência atual."""
        return self._app_state.sequence

    @current_sequence.setter
    def current_sequence(self, sequence):
        """Define a sequência atual."""
        self._app_state.sequence = sequence

    @property
    def is_running_sequence(self) -> bool:
        """Retorna True se sequência está em execução."""
        return self._app_state.sequence_running

    @is_running_sequence.setter
    def is_running_sequence(self, running: bool):
        """Define o estado de execução da sequência."""
        self._app_state.sequence_running = running


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AOIControllerApp()
    window.show()
    sys.exit(app.exec())
