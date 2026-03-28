"""
handlers/menu_handler.py
------------------------

Gerencia a criação e organização de menus da aplicação.

Centraliza toda a lógica de setup de menu, removendo
o método setup_menu() do main_window.py.
"""

import logging
from typing import Dict, Callable
from PyQt6.QtWidgets import QMenuBar
from PyQt6.QtGui import QAction
from PyQt6.QtCore import QObject

logger = logging.getLogger(__name__)


class MenuHandler(QObject):
    """
    Handler centralizado para criação e gerenciamento de menus.

    Responsabilidades:
        - Criar todos os menus da aplicação
        - Registrar actions de menu
        - Configurar shortcuts
        - Conectar signals aos handlers apropriados
        - Gerenciar estado dinâmico de menus (enabled/disabled)

    Estrutura de Menus:
        - Arquivo
        - Receitas
        - Stencils
        - Relatórios
        - Ferramentas
        - Sistema
        - Tensão do Stencil
        - Ajuda
    """

    def __init__(self, main_window=None):
        """
        Inicializa o handler de menu.

        Args:
            main_window: Referência para a janela principal (para conectar handlers)
        """
        super().__init__()
        self.main_window = main_window
        self.actions: Dict[str, QAction] = {}

        # Referências para actions dinâmicos (atualizados em runtime)
        self.current_recipe_action = None
        self.current_stencil_action = None

    def create_menus(self, menubar: QMenuBar):
        """
        Cria todos os menus e actions na barra de menu.

        Args:
            menubar: QMenuBar onde criar os menus
        """
        if not self.main_window:
            logger.error("main_window não definido, não é possível criar menus")
            return

        logger.info("Criando menus da aplicação")

        # Menu Arquivo
        self._create_file_menu(menubar)

        # Menu Receitas
        self._create_recipes_menu(menubar)

        # Menu Stencils
        self._create_stencils_menu(menubar)

        # Menu Relatórios
        self._create_reports_menu(menubar)

        # Menu Ferramentas
        self._create_tools_menu(menubar)

        # Menu Tensão do Stencil
        self._create_tension_menu(menubar)

        # Menu Sistema
        self._create_system_menu(menubar)

        # Menu Ajuda
        self._create_help_menu(menubar)

        logger.info(f"Menus criados: {len(self.actions)} actions registradas")

    # ==================== CRIAÇÃO DE MENUS ====================

    def _create_file_menu(self, menubar: QMenuBar):
        """Cria o menu Arquivo."""
        menu = menubar.addMenu('&Arquivo')

        # Sair
        exit_action = QAction('Sair', self.main_window)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.main_window.close)
        menu.addAction(exit_action)

        self._register_action('file.exit', exit_action)

    def _create_recipes_menu(self, menubar: QMenuBar):
        """Cria o menu Receitas."""
        menu = menubar.addMenu('&Receitas')

        # Gerenciar Receitas
        manage_action = QAction('📋 Gerenciar Receitas...', self.main_window)
        manage_action.setShortcut('Ctrl+R')
        manage_action.triggered.connect(self.main_window.show_recipe_manager)
        menu.addAction(manage_action)
        self._register_action('recipes.manage', manage_action)

        # Nova Receita
        new_action = QAction('➕ Nova Receita...', self.main_window)
        new_action.triggered.connect(self.main_window.show_new_recipe_dialog)
        menu.addAction(new_action)
        self._register_action('recipes.new', new_action)

        menu.addSeparator()

        # Receita Atual (dinâmico)
        self.current_recipe_action = QAction('(Nenhuma receita carregada)', self.main_window)
        self.current_recipe_action.setEnabled(False)
        menu.addAction(self.current_recipe_action)
        self._register_action('recipes.current', self.current_recipe_action)

        # Aplicar à Captura
        apply_capture_action = QAction('🔄 Aplicar Receita à Captura', self.main_window)
        apply_capture_action.triggered.connect(self.main_window.apply_recipe_to_capture)
        menu.addAction(apply_capture_action)
        self._register_action('recipes.apply_capture', apply_capture_action)

        # Aplicar à Tensão
        apply_tension_action = QAction('🔄 Aplicar Receita à Tensão', self.main_window)
        apply_tension_action.triggered.connect(self.main_window.apply_recipe_to_tension)
        menu.addAction(apply_tension_action)
        self._register_action('recipes.apply_tension', apply_tension_action)

    def _create_stencils_menu(self, menubar: QMenuBar):
        """Cria o menu Stencils."""
        menu = menubar.addMenu('&Stencils')

        # Gerenciar Stencils
        manage_action = QAction('📋 Gerenciar Stencils...', self.main_window)
        manage_action.setShortcut('Ctrl+T')
        manage_action.triggered.connect(self.main_window.show_stencil_manager)
        menu.addAction(manage_action)
        self._register_action('stencils.manage', manage_action)

        # Novo Stencil
        new_action = QAction('➕ Novo Stencil...', self.main_window)
        new_action.triggered.connect(self.main_window.show_new_stencil_dialog)
        menu.addAction(new_action)
        self._register_action('stencils.new', new_action)

        menu.addSeparator()

        # Stencil Atual (dinâmico)
        self.current_stencil_action = QAction('(Nenhum stencil selecionado)', self.main_window)
        self.current_stencil_action.setEnabled(False)
        menu.addAction(self.current_stencil_action)
        self._register_action('stencils.current', self.current_stencil_action)

    def _create_reports_menu(self, menubar: QMenuBar):
        """Cria o menu Relatórios."""
        menu = menubar.addMenu('&Relatórios')

        # Relatório de Tensão
        tension_action = QAction('📄 Relatório de Tensão...', self.main_window)
        tension_action.setShortcut('Ctrl+P')
        tension_action.setToolTip('Gera relatório PDF da última medição de tensão')
        tension_action.triggered.connect(self.main_window.show_tension_report_dialog)
        menu.addAction(tension_action)
        self._register_action('reports.tension', tension_action)

        # Relatório do Stencil
        stencil_action = QAction('📋 Relatório do Stencil...', self.main_window)
        stencil_action.setToolTip('Gera relatório PDF do histórico do stencil selecionado')
        stencil_action.triggered.connect(self.main_window.show_stencil_report_dialog)
        menu.addAction(stencil_action)
        self._register_action('reports.stencil', stencil_action)

        menu.addSeparator()

        # Consultar por Período
        period_action = QAction('📅 Consultar por Período...', self.main_window)
        period_action.triggered.connect(self.main_window.show_period_query_dialog)
        menu.addAction(period_action)
        self._register_action('reports.period', period_action)

        menu.addSeparator()

        # Configurações de Relatório
        settings_action = QAction('⚙️ Configurações de Relatório...', self.main_window)
        settings_action.triggered.connect(self.main_window.show_report_settings)
        menu.addAction(settings_action)
        self._register_action('reports.settings', settings_action)

    def _create_tools_menu(self, menubar: QMenuBar):
        """Cria o menu Ferramentas."""
        menu = menubar.addMenu('&Ferramentas')

        # Controle de Movimento (NOVO - release/v0.5-tension)
        movement_action = QAction('🎮 Controle de Movimento', self.main_window)
        movement_action.setShortcut('Ctrl+M')
        movement_action.setToolTip('Abre diálogo de controle de movimento CNC (não-modal)')
        movement_action.triggered.connect(self.main_window.open_movement_dialog)
        menu.addAction(movement_action)
        self._register_action('tools.movement', movement_action)

        menu.addSeparator()

        # Calibração CNC
        calib_action = QAction('Calibração CNC', self.main_window)
        calib_action.triggered.connect(self._on_show_calibration_dialog)
        menu.addAction(calib_action)
        self._register_action('tools.calibration', calib_action)

        menu.addSeparator()

        # Preferências
        pref_action = QAction('Preferências', self.main_window)
        pref_action.setShortcut('Ctrl+,')
        pref_action.triggered.connect(self.main_window.show_settings_dialog)
        menu.addAction(pref_action)
        self._register_action('tools.preferences', pref_action)

        menu.addSeparator()

        # Painel de Conexões
        conn_action = QAction('Conexões…', self.main_window)
        conn_action.setCheckable(True)
        conn_action.setChecked(False)
        conn_action.triggered.connect(
            lambda checked: self.main_window.connection_group.setVisible(checked)
        )
        menu.addAction(conn_action)
        self._register_action('tools.connections', conn_action)

    def _create_tension_menu(self, menubar: QMenuBar):
        """Cria o menu Tensão do Stencil."""
        tension_action = QAction('Tensão do Stencil', self.main_window)
        tension_action.triggered.connect(self.main_window.open_stencil_tension_dialog)
        menubar.addAction(tension_action)
        self._register_action('tension.dialog', tension_action)

    def _create_system_menu(self, menubar: QMenuBar):
        """Cria o menu Sistema."""
        menu = menubar.addMenu('&Sistema')

        # Configurações de Autenticação (NOVO - 2026-01-15)
        auth_settings_action = QAction('🔐 Configurações de Autenticação...', self.main_window)
        auth_settings_action.setToolTip(
            'Configura exigência de login ao iniciar e papel padrão para auto-login.\n'
            'Requer privilégios de Engenharia ou superior.'
        )
        auth_settings_action.triggered.connect(self.main_window.show_auth_settings)
        menu.addAction(auth_settings_action)
        self._register_action('system.auth_settings', auth_settings_action)

        menu.addSeparator()

        # Configurações de Tema
        theme_settings_action = QAction('🎨 Configurações de Tema...', self.main_window)
        theme_settings_action.setToolTip(
            'Alterne entre temas Claro, Escuro ou Automático (sistema operacional).\n'
            'A escolha é salva e aplicada em todos os componentes da aplicação.'
        )
        theme_settings_action.triggered.connect(self.main_window.show_theme_settings)
        menu.addAction(theme_settings_action)
        self._register_action('system.theme_settings', theme_settings_action)

        menu.addSeparator()

        # Verificar Permissões
        permissions_action = QAction('🔐 Verificar Permissões', self.main_window)
        permissions_action.setToolTip('Exibe as permissões do usuário atual')
        permissions_action.triggered.connect(self.main_window.show_permissions_info)
        menu.addAction(permissions_action)
        self._register_action('system.permissions', permissions_action)

    def _create_help_menu(self, menubar: QMenuBar):
        """Cria o menu Ajuda."""
        menu = menubar.addMenu('&Ajuda')

        about_action = QAction('Sobre', self.main_window)
        about_action.triggered.connect(self.main_window.show_about_dialog)
        menu.addAction(about_action)
        self._register_action('help.about', about_action)

    # ==================== MÉTODOS AUXILIARES ====================

    def _register_action(self, key: str, action: QAction):
        """
        Registra uma action no dicionário.

        Args:
            key: Chave única para a action
            action: QAction a registrar
        """
        self.actions[key] = action
        logger.debug(f"Action registrada: {key}")

    def get_action(self, key: str) -> QAction:
        """
        Retorna uma action registrada.

        Args:
            key: Chave da action

        Returns:
            QAction ou None se não existir
        """
        return self.actions.get(key)

    def update_current_recipe_text(self, text: str):
        """
        Atualiza o texto da action de receita atual.

        Args:
            text: Novo texto para exibir
        """
        if self.current_recipe_action:
            self.current_recipe_action.setText(text)
            logger.debug(f"Receita atual atualizada: {text}")

    def update_current_stencil_text(self, text: str):
        """
        Atualiza o texto da action de stencil atual.

        Args:
            text: Novo texto para exibir
        """
        if self.current_stencil_action:
            self.current_stencil_action.setText(text)
            logger.debug(f"Stencil atual atualizado: {text}")

    def enable_action(self, key: str, enabled: bool = True):
        """
        Habilita ou desabilita uma action.

        Args:
            key: Chave da action
            enabled: True para habilitar, False para desabilitar
        """
        action = self.get_action(key)
        if action:
            action.setEnabled(enabled)
            logger.debug(f"Action {key} {'habilitada' if enabled else 'desabilitada'}")

    def set_action_checked(self, key: str, checked: bool):
        """
        Define o estado checked de uma action.

        Args:
            key: Chave da action
            checked: Estado checked
        """
        action = self.get_action(key)
        if action and action.isCheckable():
            action.setChecked(checked)
            logger.debug(f"Action {key} checked = {checked}")

    # ==================== HANDLERS PARA CONTROLLERS ====================

    def _on_show_map_dialog(self):
        """Handler para mostrar diálogo de definição de mapa."""
        if not self.main_window:
            logger.error("main_window não definido")
            return

        # Obtém camera_preview da CNCControlTab se disponível
        camera_preview = None
        if hasattr(self.main_window, 'cnc_tab') and hasattr(self.main_window.cnc_tab, 'camera_preview'):
            camera_preview = self.main_window.cnc_tab.camera_preview

        self.main_window.map_controller.show_dialog(self.main_window, camera_preview)

    def _on_show_calibration_dialog(self):
        """Handler para mostrar diálogo de calibração CNC."""
        if not self.main_window:
            logger.error("main_window não definido")
            return

        # Obtém valores atuais dos campos de calibração se existirem
        pulses_value = ""
        fuso_value = ""
        if hasattr(self.main_window, 'calib_pulses_per_mm_edit'):
            pulses_value = self.main_window.calib_pulses_per_mm_edit.text()
        if hasattr(self.main_window, 'calib_fuso_pitch_edit'):
            fuso_value = self.main_window.calib_fuso_pitch_edit.text()

        self.main_window.calibration_controller.show_dialog(self.main_window, pulses_value, fuso_value)

    def get_all_actions(self) -> Dict[str, QAction]:
        """
        Retorna todas as actions registradas.

        Returns:
            Dicionário key → QAction
        """
        return self.actions.copy()
