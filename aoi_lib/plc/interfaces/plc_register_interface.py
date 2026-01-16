"""
Interface PLC Register Operations - Contrato para operações de registradores

Define contrato para leitura e escrita de registradores Modbus.
"""

from abc import ABC, abstractmethod


class IPLCRegisterOperations(ABC):
    """
    Interface para operações de registradores do PLC.

    Responsabilidades:
    - Escrever em coils (outputs digitais)
    - Ler coils (inputs digitais)
    - Escrever words e dwords (registradores)
    - Snapshot de todos os registradores
    """

    @abstractmethod
    def pulse_coil(self, coil_address: int, pulse_time_ms: int = 100) -> bool:
        """
        Pulsa coil digital por tempo especificado.

        Args:
            coil_address: Endereço da coil (ex: M1050 para X/Y interpolation)
            pulse_time_ms: Tempo do pulso em milissegundos (padrão: 100)

        Returns:
            True se pulso bem-sucedido, False caso contrário
        """
        pass

    @abstractmethod
    def read_coil(self, coil_address: int) -> bool:
        """
        Lê estado de coil digital.

        Args:
            coil_address: Endereço da coil

        Returns:
            True se coil ativo, False se inativo
        """
        pass

    @abstractmethod
    def write_coil(self, coil_address: int, value: bool) -> bool:
        """
        Escreve valor em coil digital.

        Args:
            coil_address: Endereço da coil
            value: Valor a escrever (True/False)

        Returns:
            True se escrita bem-sucedida, False caso contrário
        """
        pass

    @abstractmethod
    def write_dword(self, register: int, value: int) -> bool:
        """
        Escreve word (16 bits) em registro Modbus.

        Args:
            register: Número do registro
            value: Valor de 16 bits

        Returns:
            True se escrita bem-sucedida, False caso contrário
        """

    @abstractmethod
    def read_dword(self, register: int) -> int:
        """
        Lê word (16 bits) de registro Modbus.

        Args:
            register: Número do registro

        Returns:
            Valor de 16 bits
        """
        pass

    @abstractmethod
    def write_register(self, register: int, value: int) -> bool:
        """
        Escreve valor em registro Modbus.

        Args:
            register: Número do registro
            value: Valor a ser escrito

        Returns:
            True se escrita bem-sucedida, False caso contrário
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
    def snapshot_registers(self) -> dict:
        """
        Cria snapshot de todos os registradores críticos.

        Returns:
            Dicionário com valores dos registradores
        """
        pass
