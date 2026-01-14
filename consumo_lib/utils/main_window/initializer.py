"""
Módulo: initializer.py

Gerencia a inicialização da MainWindow (AOIControllerApp).

Responsabilidades:
- Criar e configurar a UI (setup_ui)
- Configurar o menu da aplicação (setup_menu)
- Tentar conexão automática ao iniciar (attempt_auto_connect)

Author: Refactoring (2026-01-14)
"""

import logging
from PyQt6.QtCore import QTimer

logger = logging.getLogger(__name__)


class MainWindowInitializer:
    """
    Gerencia a inicialização da MainWindow.

    Coordena a criação da UI, configuração do menu e conexões automáticas.

    Attributes:
        main_window: Instância da MainWindow (AOIControllerApp)
        setup_coordinator: Coordenador de setup (SetupCoordinator)
    """

    def __init__(self, main_window, setup_coordinator=None):
        """
        Inicializa o MainWindowInitializer.

        Args:
            main_window: Instância da MainWindow (AOIControllerApp)
            setup_coordinator: SetupCoordinator (opcional)
        """
        self.main_window = main_window
        self.setup_coordinator = setup_coordinator

    def initialize_all(self):
        """
        Executa toda a sequência de inicialização.

        Ordem:
        1. setup_ui() - Cria a interface gráfica
        2. setup_menu() - Configura o menu
        3. attempt_auto_connect() - Tenta conexão automática
        """
        self.setup_ui()
        self.setup_menu()
        self.attempt_auto_connect()

        logger.info("Inicialização da MainWindow concluída")

    def setup_ui(self):
        """
        Configura a UI principal usando UIBuilder.

        O UIBuilder cria todos os widgets, layouts e abas da aplicação.
        """
        from consumo_lib.ui_builders import MainUIBuilder

        ui_builder = MainUIBuilder(self.main_window)
        ui_builder.build_ui()
        logger.info("UI criada via MainUIBuilder")

    def setup_menu(self):
        """Configura o menu da aplicação usando MenuHandler."""
        menubar = self.main_window.menuBar()

        # Usar MenuHandler para criar todos os menus
        self.main_window.menu_handler.create_menus(menubar)

        # Obter referências para actions dinâmicos (para compatibilidade)
        self.main_window.current_recipe_action = self.main_window.menu_handler.current_recipe_action
        self.main_window.current_stencil_action = self.main_window.menu_handler.current_stencil_action

        logger.info("Menu configurado via MenuHandler")

    def attempt_auto_connect(self):
        """
        Tenta conexão automática ao PLC e câmera ao iniciar a aplicação.

        Lê configuração e conecta automaticamente se auto_connect estiver habilitado.
        """
        config = self.main_window.config

        # Auto-connect câmera
        if config.get("connections", "auto_connect_camera", default=False):
            # Obtém ID salvo (pode ser int ou string URL)
            raw_id = config.get("connections", "last_camera_id", default=0)

            # Tenta converter para int se possível (para câmera USB padrão)
            try:
                cam_id = int(raw_id)
                cam_str = str(cam_id)
            except (ValueError, TypeError):
                # É uma URL/String
                cam_id = str(raw_id)
                cam_str = cam_id

            # Tenta achar na lista
            idx = self.main_window.camera_id_combo.findText(cam_str)
            if idx >= 0:
                self.main_window.camera_id_combo.setCurrentIndex(idx)
            else:
                # Se não achou (ex: é uma URL customizada), define o texto diretamente
                self.main_window.camera_id_combo.setCurrentText(cam_str)

            # Agenda conexão para 500ms depois (deixa UI carregar)
            QTimer.singleShot(500, self._connect_camera_delayed)

        # Auto-connect PLC já é feito pelo SetupCoordinator
        # Não precisa replicar aqui

        logger.debug("Auto-connect configurado")

    def _connect_camera_delayed(self):
        """Conecta a câmera após delay (chamado por QTimer)."""
        if hasattr(self.main_window, 'connect_camera'):
            self.main_window.connect_camera()
            logger.info("Câmera conectada automaticamente")

    def show_plc_connection_error(self, host: str, port: int, error: str):
        """
        Exibe mensagem de erro de conexão ao PLC.

        Args:
            host: Endereço do PLC
            port: Porta do PLC
            error: Mensagem de erro
        """
        from PyQt6.QtWidgets import QMessageBox

        QMessageBox.information(
            self.main_window,
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
