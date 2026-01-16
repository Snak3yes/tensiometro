"""
Interface Hardware Manager - Gerenciamento de Hardware

Define contrato para conexão e gerenciamento de hardware (PLC, CNC, Câmera).
"""

from abc import ABC, abstractmethod
from typing import Optional


class IHardwareManager(ABC):
    """
    Interface para gerenciamento de hardware da aplicação.

    Responsabilidades:
    - Conectar/desconectar PLC
    - Conectar/desconectar CNC
    - Conectar/desconectar câmera
    - Testar hardware
    - Atualizar portas disponíveis
    """

    @abstractmethod
    def connect_plc(self, host: str, port: int) -> bool:
        """
        Conecta ao PLC via Modbus TCP.

        Args:
            host: Endereço IP do PLC
            port: Porta Modbus

        Returns:
            True se conectado com sucesso, False caso contrário
        """
        pass

    @abstractmethod
    def disconnect_plc(self) -> None:
        """Desconecta do PLC."""
        pass

    @abstractmethod
    def is_plc_connected(self) -> bool:
        """
        Verifica se o PLC está conectado.

        Returns:
            True se conectado, False caso contrário
        """
        pass

    @abstractmethod
    def connect_cnc(self, port: str) -> bool:
        """
        Conecta ao CNC via serial.

        Args:
            port: Porta serial (ex: "COM3")

        Returns:
            True se conectado com sucesso, False caso contrário
        """
        pass

    @abstractmethod
    def disconnect_cnc(self) -> None:
        """Desconecta do CNC."""
        pass

    @abstractmethod
    def is_cnc_connected(self) -> bool:
        """
        Verifica se o CNC está conectado.

        Returns:
            True se conectado, False caso contrário
        """
        pass

    @abstractmethod
    def connect_camera(self, camera_id: str) -> bool:
        """
        Conecta à câmera.

        Args:
            camera_id: ID da câmera (0, 1, 2...) ou URL

        Returns:
            True se conectado com sucesso, False caso contrário
        """
        pass

    @abstractmethod
    def disconnect_camera(self) -> None:
        """Desconecta da câmera."""
        pass

    @abstractmethod
    def is_camera_connected(self) -> bool:
        """
        Verifica se a câmera está conectada.

        Returns:
            True se conectada, False caso contrário
        """
        pass

    @abstractmethod
    def test_camera(self) -> bool:
        """
        Testa a conexão da câmera.

        Returns:
            True se teste bem-sucedido, False caso contrário
        """
        pass

    @abstractmethod
    def refresh_ports(self) -> list[str]:
        """
        Atualiza lista de portas seriais disponíveis.

        Returns:
            Lista de portas disponíveis
        """
        pass
