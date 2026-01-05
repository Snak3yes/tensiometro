"""
coordinators/connection_coordinator.py
---------------------------------------

Gerencia centralizadamente todos os estados de conexão de hardware
(PLC via Modbus + Câmera USB) e elimina duplicação de checks.

Implementa padrão Observer para notificar mudanças de estado.
"""

import logging
from typing import Optional, Callable
from functools import wraps
from enum import Enum

from PyQt6.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)


class ConnectionStatus(Enum):
    """Estados possíveis de conexão"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


class ConnectionState(QObject):
    """
    Gerencia o estado de conexão de hardware usando Observer Pattern.

    Esta classe centraliza TODOS os checks de is_connected espalhados
    pelo código, eliminando duplicação.

    Signals:
        status_changed: Emitido quando o estado de conexão muda
            - ConnectionStatus (novo estado)
            - str (mensagem opcional)
    """

    status_changed = pyqtSignal(ConnectionStatus, str)

    def __init__(self):
        super().__init__()
        self._plc_status: ConnectionStatus = ConnectionStatus.DISCONNECTED
        self._camera_status: ConnectionStatus = ConnectionStatus.DISCONNECTED
        self._last_error: Optional[str] = None

    # ==================== PROPRIEDADES ====================

    @property
    def plc_connected(self) -> bool:
        """Retorna True se PLC está conectado."""
        return self._plc_status == ConnectionStatus.CONNECTED

    @property
    def camera_connected(self) -> bool:
        """Retorna True se câmera está conectada."""
        return self._camera_status == ConnectionStatus.CONNECTED

    @property
    def can_operate(self) -> bool:
        """
        Verifica se o sistema pode operar (pelo menos PLC conectado).

        Esta é a propriedade principal que substitui os checks de
        is_connected espalhados pelo código.
        """
        return self._plc_status == ConnectionStatus.CONNECTED

    @property
    def fully_connected(self) -> bool:
        """Retorna True se AMBOS PLC e câmera estão conectados."""
        return self.plc_connected and self.camera_connected

    @property
    def plc_status(self) -> ConnectionStatus:
        """Retorna o status atual da conexão PLC."""
        return self._plc_status

    @property
    def camera_status(self) -> ConnectionStatus:
        """Retorna o status atual da conexão da câmera."""
        return self._camera_status

    @property
    def last_error(self) -> Optional[str]:
        """Retorna o último erro de conexão."""
        return self._last_error

    # ==================== MÉTODOS PÚBLICOS ====================

    def set_plc_connecting(self):
        """Define estado PLC como conectando."""
        self._plc_status = ConnectionStatus.CONNECTING
        self.status_changed.emit(self._plc_status, "Conectando ao PLC...")
        logger.debug("PLC status: CONNECTING")

    def set_plc_connected(self):
        """Define estado PLC como conectado."""
        self._plc_status = ConnectionStatus.CONNECTED
        self._last_error = None
        self.status_changed.emit(self._plc_status, "PLC conectado")
        logger.info("PLC status: CONNECTED")

    def set_plc_disconnected(self):
        """Define estado PLC como desconectado."""
        self._plc_status = ConnectionStatus.DISCONNECTED
        self.status_changed.emit(self._plc_status, "PLC desconectado")
        logger.info("PLC status: DISCONNECTED")

    def set_plc_error(self, error: str):
        """
        Define estado PLC como erro.

        Args:
            error: Mensagem de erro
        """
        self._plc_status = ConnectionStatus.ERROR
        self._last_error = error
        self.status_changed.emit(self._plc_status, f"Erro PLC: {error}")
        logger.error(f"PLC status: ERROR - {error}")

    def set_camera_connecting(self):
        """Define estado câmera como conectando."""
        self._camera_status = ConnectionStatus.CONNECTING
        self.status_changed.emit(self._camera_status, "Conectando câmera...")
        logger.debug("Camera status: CONNECTING")

    def set_camera_connected(self):
        """Define estado câmera como conectada."""
        self._camera_status = ConnectionStatus.CONNECTED
        self._last_error = None
        self.status_changed.emit(self._camera_status, "Câmera conectada")
        logger.info("Camera status: CONNECTED")

    def set_camera_disconnected(self):
        """Define estado câmera como desconectada."""
        self._camera_status = ConnectionStatus.DISCONNECTED
        self.status_changed.emit(self._camera_status, "Câmera desconectada")
        logger.info("Camera status: DISCONNECTED")

    def set_camera_error(self, error: str):
        """
        Define estado câmera como erro.

        Args:
            error: Mensagem de erro
        """
        self._camera_status = ConnectionStatus.ERROR
        self._last_error = error
        self.status_changed.emit(self._camera_status, f"Erro câmera: {error}")
        logger.error(f"Camera status: ERROR - {error}")

    def reset(self):
        """Reseta todos os estados para desconectado."""
        self._plc_status = ConnectionStatus.DISCONNECTED
        self._camera_status = ConnectionStatus.DISCONNECTED
        self._last_error = None
        self.status_changed.emit(self._plc_status, "Conexões resetadas")
        logger.info("Connection states reset")


class ConnectionCoordinator(QObject):
    """
    Coordena todas as operações de conexão de hardware.

    Responsabilidades:
        - Centralizar lógica de conexão/desconexão
        - Gerenciar estado de conexão via ConnectionState
        - Emitir signals para notificar mudanças
        - Implementar retry logic e recovery

    Substitui a lógica duplicada de is_connection por todo o código.
    """

    # Signals para compatibilidade com ConnectionManager existente
    plc_connected = pyqtSignal()
    plc_disconnected = pyqtSignal()
    plc_connection_error = pyqtSignal(str)
    camera_connected = pyqtSignal()
    camera_disconnected = pyqtSignal()
    camera_error = pyqtSignal(str)

    def __init__(self, controller, config_manager):
        """
        Inicializa o coordinator.

        Args:
            controller: CNCAOIController
            config_manager: AOIConfigManager
        """
        super().__init__()
        self.controller = controller
        self.config = config_manager
        self.state = ConnectionState()

        # Conectar signals do estado aos signals públicos (para compatibilidade)
        self.state.status_changed.connect(self._on_status_changed)

    # ==================== MÉTODOS PLC ====================

    def connect_plc(self):
        """
        Conecta ao PLC usando o controlador existente.

        Emite signals:
            - plc_connected: em caso de sucesso
            - plc_connection_error: em caso de falha
        """
        from aoi_lib import PLCAxisController

        # Verificar se é PLCAxisController
        if not isinstance(self.controller.cnc, PLCAxisController):
            logger.warning("CNC não é PLCAxisController, ignorando conexão PLC")
            return

        plc = self.controller.cnc

        # Se já está conectado, ignora
        if plc.is_connected:
            logger.info("PLC já está conectado")
            return

        self.state.set_plc_connecting()

        logger.info(f"Tentando conectar ao PLC em {plc.host}:{plc.port}")
        try:
            plc.connect()
            logger.info(f"PLC conectado com sucesso em {plc.host}:{plc.port}")
            self.state.set_plc_connected()
        except Exception as e:
            error_msg = f"Falha ao conectar ao PLC em {plc.host}:{plc.port}: {e}"
            logger.error(error_msg)
            self.state.set_plc_error(error_msg)

    def disconnect_plc(self):
        """
        Desconecta do PLC.

        Emite signal plc_disconnected.
        """
        from aoi_lib import PLCAxisController

        if not isinstance(self.controller.cnc, PLCAxisController):
            logger.warning("CNC não é PLCAxisController, ignorando desconexão")
            return

        plc = self.controller.cnc

        if not plc.is_connected:
            logger.info("PLC já está desconectado")
            self.state.set_plc_disconnected()
            return

        try:
            plc.close()
            logger.info("PLC desconectado pelo usuário")
            self.state.set_plc_disconnected()
        except Exception as e:
            logger.error(f"Erro ao desconectar PLC: {e}")
            # Emite mesmo com erro, pois estado final é "desconectado"
            self.state.set_plc_disconnected()

    def toggle_plc(self):
        """
        Alterna estado de conexão do PLC (connect/disconnect).
        """
        from aoi_lib import PLCAxisController

        if not isinstance(self.controller.cnc, PLCAxisController):
            logger.warning("CNC não é PLCAxisController")
            return

        if self.state.plc_connected:
            self.disconnect_plc()
        else:
            self.connect_plc()

    # ==================== MÉTODOS CÂMERA ====================

    def connect_camera(self, camera_id=None):
        """
        Conecta à câmera.

        Args:
            camera_id: ID ou URL da câmera (opcional)
        """
        if camera_id is None:
            camera_id = self.config.get("connections", "last_camera_id", default=0)

        self.state.set_camera_connecting()

        try:
            success = self.controller.connect_camera(camera_id)
            if success:
                self.state.set_camera_connected()
            else:
                error = getattr(self.controller.camera, 'last_error', 'Erro desconhecido')
                self.state.set_camera_error(error)
        except Exception as e:
            error_msg = f"Exceção ao conectar câmera: {e}"
            self.state.set_camera_error(error_msg)

    def disconnect_camera(self):
        """Desconecta a câmera."""
        if hasattr(self.controller, 'camera') and self.controller.camera:
            try:
                self.controller.camera.disconnect()
                self.state.set_camera_disconnected()
            except Exception as e:
                logger.error(f"Erro ao desconectar câmera: {e}")
                self.state.set_camera_disconnected()

    # ==================== AUTO-CONNECT ====================

    def attempt_auto_connect(self):
        """
        Tenta conectar automaticamente ao PLC se configurado.

        Lê a configuração 'auto_connect_plc' e tenta conectar se True.
        """
        from aoi_lib import PLCAxisController

        if not isinstance(self.controller.cnc, PLCAxisController):
            logger.debug("CNC não é PLCAxisController, pulando auto-connect")
            return

        # Nota: A configuração pode ter outro nome, verificar no config_manager
        auto_connect = self.config.get("connections", "auto_connect_plc", default=False)

        if auto_connect:
            logger.info("Auto-connect PLC habilitado, tentando conectar...")
            self.connect_plc()
        else:
            logger.info("Auto-connect PLC desabilitado")

    # ==================== HANDLERS INTERNOS ====================

    def _on_status_changed(self, status: ConnectionStatus, message: str):
        """
        Handler interno para mudanças de estado.

        Converte mudanças de estado em signals compatíveis com o código existente.
        """
        if status == ConnectionStatus.CONNECTED:
            # Diferenciar PLC de câmera pela mensagem
            if "PLC" in message or "plc" in message.lower():
                self.plc_connected.emit()
            elif "Câmera" in message or "câmera" in message.lower():
                self.camera_connected.emit()

        elif status == ConnectionStatus.DISCONNECTED:
            if "PLC" in message or "plc" in message.lower():
                self.plc_disconnected.emit()
            elif "Câmera" in message or "câmera" in message.lower():
                self.camera_disconnected.emit()

        elif status == ConnectionStatus.ERROR:
            error_msg = self.state.last_error or message
            # Emit signal apropriado baseado no contexto
            if "PLC" in message or "plc" in message.lower():
                self.plc_connection_error.emit(error_msg)
            elif "Câmera" in message or "câmera" in message.lower():
                self.camera_error.emit(error_msg)


# ==================== DECORATOR ====================

def require_connection(func: Callable) -> Callable:
    """
    Decorator que verifica se o hardware está conectado antes de executar.

    Substitui checks manuais de is_connected por todo o código.

    Uso:
        @require_connection
        def move_to_position(self, x, y, z):
            self.controller.cnc.move_to(x, y, z)

    Levanta:
        ConnectionError: Se hardware não está conectado
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        # Verifica se o objeto tem connection_coordinator ou connection_state
        connection_state = None

        if hasattr(self, 'connection_coordinator'):
            connection_state = self.connection_coordinator.state
        elif hasattr(self, 'connection_state'):
            connection_state = self.connection_state
        elif hasattr(self, 'controller') and hasattr(self.controller, 'cnc'):
            # Fallback para código antigo
            if not getattr(self.controller.cnc, 'is_connected', False):
                raise ConnectionError("Hardware não conectado. Conecte o PLC primeiro.")
            return func(self, *args, **kwargs)
        else:
            # Se não encontrar nenhum gerenciador, executa sem verificação
            logger.warning(f"Nenhum gerenciador de conexão encontrado em {self.__class__.__name__}")
            return func(self, *args, **kwargs)

        # Verifica se pode operar
        if connection_state and not connection_state.can_operate:
            raise ConnectionError(
                "Hardware não conectado. Conecte o PLC primeiro.\n"
                "Use o botão 'Conectar PLC' na aba Controle CNC."
            )

        return func(self, *args, **kwargs)

    return wrapper
