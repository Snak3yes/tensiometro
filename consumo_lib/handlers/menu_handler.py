"""
handlers/menu_handler.py
------------------------

Gerencia a criação e organização de menus da aplicação.

Centraliza toda a lógica de setup de menu, removendo
o método setup_menu() do main_window.py.
"""

import logging
from typing import Dict
from PyQt6.QtWidgets import QMenu, QMenuBar
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

    Estrutura de Menus (v0.5-tension - Consolidada):
        - Arquivo (Sair)
        - Relatórios (Tensão, Stencil, Período, Configurações)
        - Ferramentas (Movimento, CLP, Calibração, Conexões, Preferências)
        - Sistema (Autenticação, Tema, Permissões, Sobre)

    NOTA: Menu Receitas removido na v0.5-tension (funcionalidade não implementada).
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
        self.menus: Dict[str, QMenu] = {}

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

        # Menu Login
        self._create_login_menu(menubar)

        # Menu Relatórios
        self._create_reports_menu(menubar)

        # Menu Ferramentas (inclui Nova Medição de Tensão)
        self._create_tools_menu(menubar)

        # Menu Sistema (inclui Sobre)
        self._create_system_menu(menubar)

        logger.info(f"Menus criados: {len(self.actions)} actions registradas")

    # ==================== CRIAÇÃO DE MENUS ====================

    def _create_login_menu(self, menubar: QMenuBar):
        """Cria o menu Login."""
        menu = menubar.addMenu("&Login")
        self._register_menu("login", menu)

        change_user_action = QAction("Trocar Usuário", self.main_window)
        change_user_action.triggered.connect(self.main_window.change_user)
        menu.addAction(change_user_action)
        self._register_action("login.change_user", change_user_action)

        menu.addSeparator()

        # Sair
        exit_action = QAction("Sair", self.main_window)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.main_window.close)
        menu.addAction(exit_action)

        self._register_action("login.exit", exit_action)

    def _create_cadastros_menu(self, menubar: QMenuBar):
        """Cadastro manual de stencils removido: dados vêm do SFCS."""
        return

    def _create_reports_menu(self, menubar: QMenuBar):
        """Cria o menu Relatórios."""
        menu = menubar.addMenu("&Relatórios")
        self._register_menu("reports", menu)

        # Relatório de Tensão
        tension_action = QAction('Relatório de Tensão...', self.main_window)
        tension_action.setShortcut('Ctrl+P')
        tension_action.setToolTip('Gera relatório PDF da última medição de tensão')
        tension_action.triggered.connect(self.main_window.show_tension_report_dialog)
        menu.addAction(tension_action)
        self._register_action('reports.tension', tension_action)

        # Relatório do Stencil
        stencil_action = QAction('Relatório do Stencil...', self.main_window)
        stencil_action.setToolTip('Gera relatório PDF do histórico do stencil selecionado')
        stencil_action.triggered.connect(self.main_window.show_stencil_report_dialog)
        menu.addAction(stencil_action)
        self._register_action('reports.stencil', stencil_action)

        menu.addSeparator()

        # Consultar por Período
        period_action = QAction('Consultar por Período...', self.main_window)
        period_action.triggered.connect(self.main_window.show_period_query_dialog)
        menu.addAction(period_action)
        self._register_action('reports.period', period_action)

        menu.addSeparator()

        # Configurações de Relatório
        settings_action = QAction('Configurações de Relatório...', self.main_window)
        settings_action.triggered.connect(self.main_window.show_report_settings)
        menu.addAction(settings_action)
        self._register_action('reports.settings', settings_action)

    def _create_tools_menu(self, menubar: QMenuBar):
        """Cria o menu Ferramentas (inclui Nova Medição de Tensão)."""
        menu = menubar.addMenu("&Ferramentas")
        self._register_menu("tools", menu)
        menu.menuAction().setVisible(False)

        # Rastreabilidade (NOVO - 2026-03-29 - substitui aba)
        tracking_action = QAction('Rastreabilidade...', self.main_window)
        tracking_action.setShortcut('Ctrl+R')
        tracking_action.setToolTip(
            'Abre diálogo de identificação de stencil (não-modal)\n'
            'Substitui a aba "Rastreabilidade" removida.'
        )
        tracking_action.triggered.connect(self.main_window.open_tracking_dialog)
        menu.addAction(tracking_action)
        self._register_action('tools.tracking', tracking_action)

        menu.addSeparator()

        # Padrões de Medição (fluxo manual)
        tension_action = QAction('Padrões de Medição...', self.main_window)
        tension_action.setToolTip(
            'Abre a tela manual de medição para criar, ajustar e salvar padrões.'
        )
        tension_action.triggered.connect(self.main_window.open_stencil_tension_dialog)
        menu.addAction(tension_action)
        self._register_action('tools.tension_new', tension_action)

        # Critérios de Tensão (NOVO - 2026-03-29)
        criteria_action = QAction('Critérios de Tensão...', self.main_window)
        criteria_action.setToolTip('Configura critérios globais de aceitação de tensão (aplicado a todos os stencils)')
        criteria_action.triggered.connect(self.main_window.show_tension_criteria_dialog)
        menu.addAction(criteria_action)
        self._register_action('tools.tension_criteria', criteria_action)

        menu.addSeparator()

        # Controle de Movimento (NOVO - release/v0.5-tension)
        movement_action = QAction('Controle de Movimento', self.main_window)
        movement_action.setShortcut('Ctrl+M')
        movement_action.setToolTip('Abre diálogo de controle de movimento CNC (não-modal)')
        movement_action.triggered.connect(self.main_window.open_movement_dialog)
        menu.addAction(movement_action)
        self._register_action('tools.movement', movement_action)

        # Monitor CLP (NOVO - release/v0.5-tension)
        plc_monitor_action = QAction('Monitor CLP', self.main_window)
        plc_monitor_action.setShortcut('Ctrl+L')
        plc_monitor_action.setToolTip('Abre diálogo de monitoramento do CLP (não-modal)')
        plc_monitor_action.triggered.connect(self.main_window.open_plc_monitor_dialog)
        menu.addAction(plc_monitor_action)
        self._register_action('tools.plc_monitor', plc_monitor_action)

        tensiometer_calibration_action = QAction('Calibrar medidor de tensao', self.main_window)
        tensiometer_calibration_action.setToolTip(
            'Abre a tela de calibracao automatica e manual do medidor de tensao'
        )
        tensiometer_calibration_action.triggered.connect(
            self.main_window.open_tensiometer_calibration_dialog
        )
        menu.addAction(tensiometer_calibration_action)
        self._register_action('tools.tensiometer_calibration', tensiometer_calibration_action)

        menu.addSeparator()

        # Calibração CNC
        calib_action = QAction('Calibração CNC', self.main_window)
        calib_action.triggered.connect(self._on_show_calibration_dialog)
        menu.addAction(calib_action)
        self._register_action('tools.calibration', calib_action)

        menu.addSeparator()

        # Conexões (NOVO - abre diálogo dedicado)
        conn_action = QAction('Conexões...', self.main_window)
        conn_action.setToolTip('Abre diálogo de conexão com o PLC')
        conn_action.triggered.connect(self.main_window.open_connection_dialog)
        menu.addAction(conn_action)
        self._register_action('tools.connections', conn_action)

        menu.addSeparator()

        # Preferências
        pref_action = QAction('Preferências', self.main_window)
        pref_action.setShortcut('Ctrl+,')
        pref_action.triggered.connect(self.main_window.show_settings_dialog)
        menu.addAction(pref_action)
        self._register_action('tools.preferences', pref_action)

    def _create_system_menu(self, menubar: QMenuBar):
        """Cria o menu Sistema (inclui Sobre)."""
        menu = menubar.addMenu("&Sistema")
        self._register_menu("system", menu)

        # Configurações de Autenticação (NOVO - 2026-01-15)
        auth_settings_action = QAction('Configurações de Autenticação...', self.main_window)
        auth_settings_action.setToolTip(
            'Configura exigência de login ao iniciar e papel padrão para auto-login.\n'
            'Requer privilégios de Engenharia ou superior.'
        )
        auth_settings_action.triggered.connect(self.main_window.show_auth_settings)
        menu.addAction(auth_settings_action)
        self._register_action('system.auth_settings', auth_settings_action)

        menu.addSeparator()

        # Configurações de Tema
        theme_settings_action = QAction('Configurações de Tema...', self.main_window)
        theme_settings_action.setToolTip(
            'Alterne entre temas Claro, Escuro ou Automático (sistema operacional).\n'
            'A escolha é salva e aplicada em todos os componentes da aplicação.'
        )
        theme_settings_action.triggered.connect(self.main_window.show_theme_settings)
        menu.addAction(theme_settings_action)
        self._register_action('system.theme_settings', theme_settings_action)

        menu.addSeparator()

        # Verificar Permissões
        permissions_action = QAction('Verificar Permissões', self.main_window)
        permissions_action.setToolTip('Exibe as permissões do usuário atual')
        permissions_action.triggered.connect(self.main_window.show_permissions_info)
        menu.addAction(permissions_action)
        self._register_action('system.permissions', permissions_action)

        menu.addSeparator()

        # Sobre (movido de menu Ajuda)
        about_action = QAction('Sobre', self.main_window)
        about_action.triggered.connect(self.main_window.show_about_dialog)
        menu.addAction(about_action)
        self._register_action('system.about', about_action)

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

    def _register_menu(self, key: str, menu: QMenu):
        """
        Registra um menu no dicionario interno.

        Args:
            key: Chave unica do menu
            menu: Instancia do menu
        """
        self.menus[key] = menu
        logger.debug(f"Menu registrado: {key}")

    def get_action(self, key: str) -> QAction:
        """
        Retorna uma action registrada.

        Args:
            key: Chave da action

        Returns:
            QAction ou None se não existir
        """
        return self.actions.get(key)

    def get_menu(self, key: str) -> QMenu | None:
        """
        Retorna um menu registrado.

        Args:
            key: Chave do menu

        Returns:
            QMenu ou None se nao existir
        """
        return self.menus.get(key)

    def update_current_recipe_text(self, text: str):
        """
        Atualiza o texto da action de receita atual.

        NOTA: Menu Receitas foi removido na v0.5-tension.
        Este método é mantido para compatibilidade mas não faz nada.

        Args:
            text: Novo texto para exibir (ignorado)
        """
        # Menu Receitas removido - método mantido para compatibilidade
        pass

    def update_current_stencil_text(self, text: str):
        """
        Atualiza o texto da action de stencil atual.

        NOTA (release/v0.5-tension): Stencil Atual removido do menu.
        Este método é mantido para compatibilidade mas não faz nada.

        Args:
            text: Novo texto para exibir (ignorado)
        """
        # Stencil Atual removido - método mantido para compatibilidade
        pass

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

    def set_menu_visible(self, key: str, visible: bool):
        """
        Mostra ou oculta um menu.

        Args:
            key: Chave do menu
            visible: True para exibir, False para ocultar
        """
        menu = self.get_menu(key)
        if menu:
            menu.menuAction().setVisible(visible)
            menu.setEnabled(visible)
            logger.debug(f"Menu {key} {'visivel' if visible else 'oculto'}")

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
