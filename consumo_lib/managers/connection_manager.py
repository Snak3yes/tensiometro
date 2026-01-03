"""
managers/connection_manager.py
------------------------------
Gerencia conexões de hardware (PLC + Câmera).
"""
import logging
from PyQt6.QtCore import QObject, pyqtSignal
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
        Aplica configurações de UI ao PLC.

        Este método lê configurações e as aplica ao controlador.
        Pode ser sobrescrito para aplicar configurações específicas da UI.
        """
        # Placeholder: implementar se necessário aplicar configurações específicas
        logger.debug("Aplicando configurações da UI ao PLC")
        self._plc_ui_settings_applied = True

    # TODO: Implementar métodos de câmera (connect_camera, test_camera, etc)
