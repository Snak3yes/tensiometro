"""
PLC Position Reader Controller - Leitura de posição de eixos

Implementa IPLCPositionReader e encapsula lógica de leitura de posição.
"""

import logging
from typing import Tuple


logger = logging.getLogger(__name__)


class PLCPositionReaderController:
    """
    Controller para leitura de posição de eixos PLC.

    Implementa leitura de posição dos eixos em pulsos.
    """

    # Mapeamento de endereços para leitura de posição
    ADDRESSES = {
        'X': {
            'pos_reg': 3000    # D3000_X
        },
        'Y': {
            'pos_reg': 3200    # D3200_Y
        },
        'Z': {
            'pos_reg': 3400    # D3400_Z
        }
    }

    def __init__(self, connection_manager, pulses_per_mm: float = 1.0):
        """
        Inicializa o controller de leitura de posição.

        Args:
            connection_manager: Instância de PLCConnectionManager
            pulses_per_mm: Fator de conversão pulsos → mm (padrão: 1.0)
        """
        self.connection_manager = connection_manager
        self.pulses_per_mm = pulses_per_mm

        logger.debug(f"PLCPositionReaderController criado: pulses_per_mm={pulses_per_mm}")

    def _read_dword(self, address: int) -> int:
        """
        Lê INT32 assinado de dois registradores.

        Args:
            address: Endereço base do registrador

        Returns:
            Valor de 32 bits lido
        """
        client = self.connection_manager.client
        if not client:
            raise IOError("Cliente Modbus não inicializado")

        res = client.read_holding_registers(address, count=2)
        if res.isError():
            raise IOError(f"Falha na leitura DWORD em {address}")
        lo, hi = res.registers
        u32 = (hi << 16) | lo
        return u32 if u32 < 0x80000000 else u32 - 0x100000000

    def get_current_position(self) -> dict:
        """
        Retorna posição atual de todos os eixos.

        Returns:
            Dicionário com chaves 'X', 'Y', 'Z' e valores em pulsos
        """
        if not self.connection_manager.is_connected():
            raise IOError("PLC não conectado")

        positions = {}

        for axis, cfg in self.ADDRESSES.items():
            try:
                pos = self._read_dword(cfg['pos_reg'])
                positions[axis] = float(pos)
            except Exception as e:
                logger.error(f"Erro ao ler posição do eixo {axis}: {e}")
                positions[axis] = 0.0

        return positions

    def read_position(self, axis: str) -> float:
        """
        Lê posição do eixo especificado.

        Args:
            axis: Eixo a ser lido ('X', 'Y', ou 'Z')

        Returns:
            Posição atual em pulsos
        """
        axis = axis.upper()
        if axis not in self.ADDRESSES:
            raise ValueError(f"Eixo inválido: {axis}")

        if not self.connection_manager.is_connected():
            raise IOError("PLC não conectado")

        return float(self._read_dword(self.ADDRESSES[axis]['pos_reg']))

    def read_register(self, register: int) -> int:
        """
        Lê valor de registro Modbus.

        Args:
            register: Número do registro

        Returns:
            Valor do registro
        """
        if not self.connection_manager.is_connected():
            raise IOError("PLC não conectado")

        return self._read_dword(register)

    def get_xyz_position(self) -> Tuple[float, float, float]:
        """
        Retorna posição XYZ como tupla.

        Returns:
            Tupla (x, y, z) em pulsos
        """
        positions = self.get_current_position()
        return (
            positions.get('X', 0.0),
            positions.get('Y', 0.0),
            positions.get('Z', 0.0)
        )

    def get_current_position_mm(self) -> dict:
        """
        Retorna posição atual de todos os eixos em milímetros.

        Returns:
            Dicionário com chaves 'x', 'y', 'z' (minúsculas) e valores em mm
        """
        if not self.connection_manager.is_connected():
            raise IOError("PLC não conectado")

        positions = self.get_current_position()

        return {
            'x': positions['X'] / self.pulses_per_mm,
            'y': positions['Y'] / self.pulses_per_mm,
            'z': positions['Z'] / self.pulses_per_mm
        }


# Import correto para a interface
from aoi_lib.plc.interfaces.plc_position_reader_interface import IPLCPositionReader
IPLCPositionReader.register(PLCPositionReaderController)
