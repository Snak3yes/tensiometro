"""
Interface PLC Position Reader - Contrato para leitura de posição

Define contrato para leitura de posição dos eixos.
"""

from abc import ABC, abstractmethod
from typing import Tuple


class IPLCPositionReader(ABC):
    """
    Interface para leitura de posição do PLC.

    Responsabilidades:
    - Ler posição atual dos eixos
    - Ler registradores Modbus
    - Obter posição XYZ como tupla
    """

    @abstractmethod
    def get_current_position(self) -> dict:
        """
        Retorna posição atual de todos os eixos.

        Returns:
            Dicionário com chaves 'X', 'Y', 'Z' e valores em pulsos
        """
        pass

    @abstractmethod
    def read_position(self, axis: str) -> float:
        """
        Lê posição do eixo especificado.

        Args:
            axis: Eixo a ser lido ('X', 'Y', ou 'Z')

        Returns:
            Posição atual em pulsos
        """
        pass

    @abstractmethod
    def read_register(self, register: int) -> int:
        """
        Lê valor de registro Modbus.

        Args:
            register: Número do registro

        Returns:
            Valor do registro
        """
        pass

    @abstractmethod
    def get_xyz_position(self) -> Tuple[float, float, float]:
        """
        Retorna posição XYZ como tupla.

        Returns:
            Tupla (x, y, z) em pulsos
        """
        pass
