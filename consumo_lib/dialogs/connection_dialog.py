"""
Connection Dialog - Diálogo de conexão com PLC.

Substitui o groupbox "Conexão" que estava na janela principal,
centralizando a configuração de conexão em um diálogo dedicado.
"""

import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout,
    QLabel, QLineEdit, QSpinBox, QGroupBox
)
from PyQt6.QtCore import Qt

from consumo_lib.ui.widget_standards import StandardButton

logger = logging.getLogger(__name__)


class ConnectionDialog(QDialog):
    """
    Diálogo para configurar e conectar ao PLC via Modbus TCP.

    Substitui o groupbox "Conexão" da janela principal,
    centralizando a configuração em um diálogo dedicado.

    Features:
        - Configuração de IP e Porta do PLC
        - Botão Conectar/Desconectar
        - Status de conexão
        - Não-modal (permite operar a janela principal)
    """

    def __init__(self, main_window, parent=None):
        """
        Inicializa o diálogo de conexão.

        Args:
            main_window: Referência à janela principal (AOIControllerApp)
            parent: Widget pai
        """
        super().__init__(parent)

        self.main_window = main_window
        self.setWindowTitle("Conexão PLC")
        self.setMinimumWidth(350)

        # Não-modal: permite operar a janela principal
        self.setWindowModality(Qt.WindowModality.NonModal)

        # Sempre no topo, com título e botão fechar
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowStaysOnTopHint
        )

        self._create_ui()
        self._connect_signals()

        logger.debug("ConnectionDialog criado")

    def _create_ui(self):
        """Cria a interface do diálogo."""
        layout = QVBoxLayout(self)

        # Grupo PLC
        plc_group = QGroupBox("PLC (Modbus TCP)")
        plc_layout = QGridLayout()

        # IP
        plc_layout.addWidget(QLabel("Endereço IP:"), 0, 0)
        self.ip_input = QLineEdit()
        self.ip_input.setText(
            self.main_window.config.get("connections", "plc_host", default="192.168.1.5")
        )
        plc_layout.addWidget(self.ip_input, 0, 1, 1, 2)

        # Porta
        plc_layout.addWidget(QLabel("Porta:"), 1, 0)
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(
            self.main_window.config.get("connections", "plc_port", default=502)
        )
        plc_layout.addWidget(self.port_input, 1, 1)

        # Botão Conectar (será substituído dinamicamente)
        self.connect_btn = StandardButton("Conectar", variant="primary-green")
        plc_layout.addWidget(self.connect_btn, 1, 2)

        plc_group.setLayout(plc_layout)
        layout.addWidget(plc_group)

        # Status
        self.status_label = QLabel("Status: Desconectado")
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.status_label)

        # Atualiza estado inicial do botão
        self._update_button_state()

    def _connect_signals(self):
        """Conecta os sinais dos widgets."""
        self.connect_btn.clicked.connect(self._on_connect_clicked)

    def _on_connect_clicked(self):
        """Handle do botão Conectar/Desconectar."""
        # Salva configurações
        self.main_window.config.set("connections", "plc_host", value=self.ip_input.text().strip())
        self.main_window.config.set("connections", "plc_port", value=self.port_input.value())

        # Delega para ConnectionManager
        if hasattr(self.main_window, 'connection_mgr'):
            self.main_window.connection_mgr.toggle_plc()

        # Atualiza estado do botão após toggle
        self._update_button_state()

    def _update_button_state(self):
        """Atualiza o estado do botão baseado no status de conexão."""
        if hasattr(self.main_window, 'controller') and hasattr(self.main_window.controller, 'cnc'):
            is_connected = self.main_window.controller.cnc.is_connected

            if is_connected:
                self.connect_btn.setText("Desconectar")
                self.status_label.setText("Status: Conectado")
                self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            else:
                self.connect_btn.setText("Conectar")
                self.status_label.setText("Status: Desconectado")
                self.status_label.setStyleSheet("color: #666; font-style: italic;")
        else:
            self.connect_btn.setText("Conectar")
            self.status_label.setText("Status: Indisponível")
            self.status_label.setStyleSheet("color: #FF5722; font-style: italic;")

    def showEvent(self, event):
        """Atualiza estado ao mostrar o diálogo."""
        super().showEvent(event)
        self._update_button_state()