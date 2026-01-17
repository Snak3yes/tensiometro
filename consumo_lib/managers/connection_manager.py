"""
managers/connection_manager.py
------------------------------
Gerencia conexões de hardware (PLC + Câmera).
"""
import logging
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QMessageBox
from aoi_lib import PLCAxisController

logger = logging.getLogger(__name__)


class ConnectionManager(QObject):
    """
    Gerencia conexões com hardware (PLC via Modbus + Câmera).

    Responsabilidades:
        - Conectar/desconectar PLC
        - Conectar/desconectar câmera
        - Auto-connection ao iniciar
        - Emitir signals de status
    """

    # Signals PLC
    plc_connected = pyqtSignal()
    plc_disconnected = pyqtSignal()
    plc_connection_error = pyqtSignal(str)

    # Signals Câmera (para implementação futura)
    camera_connected = pyqtSignal()
    camera_disconnected = pyqtSignal()
    camera_error = pyqtSignal(str)

    def __init__(self, controller, config):
        super().__init__()
        self.controller = controller
        self.config = config
        self._plc_ui_settings_applied = False
        # Referências opcionais aos widgets da UI (para leitura de valores)
        self.plc_host_input = None
        self.plc_port_input = None

    def set_ui_widgets(self, plc_host_input=None, plc_port_input=None):
        """
        Define referências aos widgets da UI para leitura de valores.

        Isso permite que o ConnectionManager leia diretamente os valores
        digitados pelo usuário antes de conectar.

        Args:
            plc_host_input: QLineEdit com host do PLC
            plc_port_input: QSpinBox com porta do PLC
        """
        self.plc_host_input = plc_host_input
        self.plc_port_input = plc_port_input
        logger.debug("Widgets da UI configurados no ConnectionManager")

    def connect_plc(self):
        """
        Conecta ao PLC usando o controlador existente.

        Emite signals:
            - plc_connected: em caso de sucesso
            - plc_connection_error: em caso de falha
        """
        # Verificar se é PLCAxisController
        if not isinstance(self.controller.cnc, PLCAxisController):
            logger.warning("CNC não é PLCAxisController, ignorando conexão PLC")
            return

        plc = self.controller.cnc

        # Se já está conectado, ignora
        if plc.is_connected:
            logger.info("PLC já está conectado")
            self.plc_connected.emit()
            return

        # Aplica configurações da UI antes de conectar
        self._apply_plc_ui_settings()

        logger.info(f"Tentando conectar ao PLC em {plc.host}:{plc.port}")
        try:
            plc.connect()
            logger.info(f"PLC conectado com sucesso em {plc.host}:{plc.port}")
            self.plc_connected.emit()
        except Exception as e:
            error_msg = f"Falha ao conectar ao PLC em {plc.host}:{plc.port}: {e}"
            logger.error(error_msg)
            self.plc_connection_error.emit(error_msg)

    def disconnect_plc(self):
        """
        Desconecta do PLC.

        Emite signal plc_disconnected.
        """
        # Verificar se é PLCAxisController
        if not isinstance(self.controller.cnc, PLCAxisController):
            logger.warning("CNC não é PLCAxisController, ignorando desconexão")
            return

        plc = self.controller.cnc

        # Se não está conectado, ignora
        if not plc.is_connected:
            logger.info("PLC já está desconectado")
            self.plc_disconnected.emit()
            return

        try:
            plc.close()
            logger.info("PLC desconectado pelo usuário")
            self.plc_disconnected.emit()
        except Exception as e:
            logger.error(f"Erro ao desconectar PLC: {e}")
            # Emite mesmo com erro, pois estado final é "desconectado"
            self.plc_disconnected.emit()

    def toggle_plc(self):
        """
        Alterna estado de conexão do PLC (connect/disconnect).
        """
        plc = self.controller.cnc

        # Verificar se é PLCAxisController
        if not isinstance(plc, PLCAxisController):
            logger.warning("CNC não é PLCAxisController")
            return

        if plc.is_connected:
            self.disconnect_plc()
        else:
            self.connect_plc()

    def attempt_auto_connect(self):
        """
        Tenta conectar automaticamente ao PLC se configurado.

        Lê a configuração 'auto_connect_plc' e tenta conectar se True.
        """
        if not isinstance(self.controller.cnc, PLCAxisController):
            logger.debug("CNC não é PLCAxisController, pulando auto-connect")
            return

        if self.config.get("connections", "auto_connect_plc", default=False):
            logger.info("Auto-connect PLC habilitado, tentando conectar...")
            self.connect_plc()
        else:
            logger.info("Auto-connect PLC desabilitado")

    def _apply_plc_ui_settings(self):
        """
        Aplica configurações de UI ao PLC antes de conectar.

        Prioriza ler dos widgets da UI (se disponíveis) para obter os valores
        mais recentes digitados pelo usuário. Se os widgets não estiverem
        disponíveis, lê do arquivo de configuração.

        Aplica os valores ao controlador PLC se forem diferentes dos valores atuais.
        """
        from aoi_lib import PLCAxisController

        if not isinstance(self.controller.cnc, PLCAxisController):
            logger.debug("CNC não é PLCAxisController, pulando aplicação de configurações")
            return

        plc = self.controller.cnc

        # Tenta ler dos widgets da UI primeiro (valores mais recentes)
        if self.plc_host_input is not None and self.plc_port_input is not None:
            host = (self.plc_host_input.text() or "").strip() or "192.168.1.5"
            port = int(self.plc_port_input.value())
            logger.debug(f"Lendo configurações dos widgets da UI: {host}:{port}")

            # Atualiza o config com os valores da UI
            self.config.set("connections", "plc_host", value=host)
            self.config.set("connections", "plc_port", value=port)
            self.config.save()
            logger.debug(f"Configurações salvas no arquivo de config")
        else:
            # Fallback: lê do arquivo de configuração
            host = self.config.get("connections", "plc_host", default="192.168.1.5")
            port = self.config.get("connections", "plc_port", default=502)
            logger.debug(f"Lendo configurações do arquivo: {host}:{port}")

        # Verifica se os valores mudaram
        current_host = getattr(plc, "host", None)
        current_port = getattr(plc, "port", None)
        current_port_int = int(current_port) if current_port is not None else None

        if host == current_host and current_port_int == port:
            logger.debug(f"Configurações do PLC inalteradas: {host}:{port}")
            self._plc_ui_settings_applied = True
            return

        # Aplica novos valores ao controlador
        try:
            logger.info(f"Atualizando configurações do PLC: {current_host}:{current_port} → {host}:{port}")
            plc.set_connection_params(host, port)
            self._plc_ui_settings_applied = True
            logger.info(f"Configurações do PLC atualizadas com sucesso: {host}:{port}")
        except Exception as e:
            logger.error(f"Falha ao aplicar configurações do PLC: {e}")
            self._plc_ui_settings_applied = False

    def refresh_serial_ports(self, port_combo):
        """
        Atualiza a lista de portas seriais disponíveis.

        Args:
            port_combo: QComboBox para preencher com portas
        """
        import serial.tools.list_ports

        port_combo.clear()
        ports = serial.tools.list_ports.comports()

        if ports:
            for port in ports:
                port_combo.addItem(port.device)
            logger.info(f"Portas seriais encontradas: {[p.device for p in ports]}")
        else:
            port_combo.addItem("Nenhuma porta encontrada")
            logger.warning("Nenhuma porta serial encontrada")

    # TODO: Implementar métodos de câmera (connect_camera, test_camera, etc)
