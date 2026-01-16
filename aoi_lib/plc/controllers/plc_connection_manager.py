"""
PLC Connection Manager - Gerenciador de conexão PLC

Implementa IPLCConnection e encapsula lógica de conexão Modbus TCP.
"""

import logging
from typing import Dict, Optional
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException, ModbusIOException

from aoi_lib.plc.interfaces.plc_connection_interface import IPLCConnection

logger = logging.getLogger(__name__)


class PLCConnectionManager(IPLCConnection):
    """
    Gerenciador de conexão PLC via Modbus TCP.

    Implementa `IPLCConnection` e encapsula:
    - Conexão Modbus TCP
    - Status de conexão
    - Parâmetros de conexão
    """

    def __init__(self, host: str, port: int, slave_id: int = 1, response_timeout: float = 5.0):
        """
        Inicializa o gerenciador de conexão.

        Args:
            host: Endereço IP do PLC
            port: Porta Modbus (padrão: 502)
            slave_id: ID do escravo Modbus (padrão: 1)
            response_timeout: Timeout de resposta em segundos (padrão: 5.0)
        """
        self.host = host
        self.port = port
        self.slave_id = slave_id
        self.response_timeout = response_timeout

        # Cliente Modbus
        self.client = ModbusTcpClient(
            host=host,
            port=port,
            timeout=response_timeout
        )

        self._is_connected = False

        logger.debug(f"PLCConnectionManager criado: {host}:{port}")

    def connect(self) -> bool:
        """
        Conecta ao PLC via Modbus TCP.

        Returns:
            True se conectado com sucesso, False caso contrário
        """
        try:
            logger.info(f"Tentando conectar ao PLC em {self.host}:{self.port}")

            if not self.client.connect():
                logger.error(f"Falha ao conectar PLC em {self.host}:{self.port}")
                self._is_connected = False
                return False

            self._is_connected = True
            logger.info(f"✅ PLC conectado em {self.host}:{self.port}")
            return True

        except (ModbusIOException, ModbusException) as e:
            logger.error(f"Erro Modbus ao conectar PLC: {e}")
            self._is_connected = False
            return False

    def disconnect(self) -> None:
        """Desconecta do PLC."""
        if self.is_connected():
            try:
                self.client.close()
                self._is_connected = False
                logger.info(f"PLC desconectado de {self.host}:{self.port}")
            except Exception as e:
                logger.error(f"Erro ao desconectar PLC: {e}")

    def is_connected(self) -> bool:
        """
        Verifica se o PLC está conectado.

        Returns:
            True se conectado, False caso contrário
        """
        return self._is_connected

    def set_connection_params(self, slave_id: int, response_timeout: float) -> None:
        """
        Configura parâmetros de conexão Modbus.

        Args:
            slave_id: ID do escravo Modbus
            response_timeout: Timeout de resposta em segundos
        """
        self.slave_id = slave_id
        self.response_timeout = response_timeout

        # Recriar cliente se estiver conectado
        if self.is_connected():
            logger.warning("Tentativa de mudar parâmetros com PLC conectado - reconectando")
            self.disconnect()
            self.connect()

    def get_connection_info(self) -> Dict[str, any]:
        """
        Retorna informações de conexão.

        Returns:
            Dicionário com host, port, slave_id, timeout
        """
        return {
            'host': self.host,
            'port': self.port,
            'slave_id': self.slave_id,
            'response_timeout': self.response_timeout,
            'is_connected': self._is_connected
        }


# Registrar implementação
IPLCConnection.register(PLCConnectionManager)
