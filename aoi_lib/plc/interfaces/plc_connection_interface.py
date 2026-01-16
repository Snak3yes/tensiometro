"""
Interface PLC Connection - Contrato para gerenciamento de conexão PLC

Define contrato para conectar e desconectar do PLC via Modbus TCP.
"""

from abc import ABC, abstractmethod


class IPLCConnection(ABC):
    """
    Interface para gerenciamento de conexão PLC.

    Responsabilidades:
    - Conectar ao PLC via Modbus TCP
    - Desconectar do PLC
    - Verificar status de conexão
    - Configurar parâmetros de conexão
    """

    @abstractmethod
    def connect(self, host: str, port: int) -> bool:
        """
        Conecta ao PLC via Modbus TCP.

        Args:
            host: Endereço IP do PLC
            port: Porta Modbus (padrão: 502)

        Returns:
            True se conectado com sucesso, False caso contrário
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """
        Desconecta do PLC.
        """
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """
        Verifica se o PLC está conectado.

        Returns:
            True se conectado, False caso contrário
        """
        pass

    @abstractmethod
    def set_connection_params(self, slave_id: int, response_timeout: float) -> None:
        """
        Configura parâmetros de conexão Modbus.

        Args:
            slave_id: ID do escravo Modbus (padrão: 1)
            response_timeout: Timeout de resposta em segundos (padrão: 5.0)
        """
        pass

    @abstractmethod
    def get_connection_info(self) -> dict:
        """
        Retorna informações de conexão.

        Returns:
            Dicionário com host, port, slave_id, timeout
        """
        pass
