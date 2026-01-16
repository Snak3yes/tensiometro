"""
PLC Relative Movement Controller - Movimento relativo de eixos

Implementa PLCRelativeMovement e encapsula lógica de movimento relativo.
"""

import logging
import time
from typing import Optional
from pymodbus.client import ModbusTcpClient


logger = logging.getLogger(__name__)


class PLCRelativeMovementController:
    """
    Controller para movimento relativo de eixos PLC.

    Implementa movimento por distância relativa em pulsos.
    """

    # Mapeamento de endereços para movimento relativo
    ADDRESSES = {
        'X': {
            'move_abs': 1050,   # M1050 - Interpolação X/Y
            'pos_input': 1100,  # D1100_X
            'speed': 21000,     # D21000_X
            'pos_reg': 3000     # D3000_X
        },
        'Y': {
            'move_abs': 1050,   # M1050 - Interpolação X/Y
            'pos_input': 600,   # D600_Y
            'speed': 20500,     # D20500_Y
            'pos_reg': 3200     # D3200_Y
        },
        'Z': {
            'move_abs': 1600,   # M1600_Z
            'pos_input': 1600,  # D1600_Z
            'speed': 21500,     # D21500_Z
            'pos_reg': 3400     # D3400_Z
        }
    }

    def __init__(self, connection_manager, absolute_controller, pulses_per_mm: float = 1.0):
        """
        Inicializa o controller de movimento relativo.

        Args:
            connection_manager: Instância de PLCConnectionManager
            absolute_controller: Instância de PLCAbsoluteMovementController
            pulses_per_mm: Fator de conversão pulsos → mm (padrão: 1.0)
        """
        self.connection_manager = connection_manager
        self.absolute_controller = absolute_controller
        self.pulses_per_mm = pulses_per_mm

        logger.debug(f"PLCRelativeMovementController criado: pulses_per_mm={pulses_per_mm}")

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

    def move_relative(self, axis: str, distance: float, speed: float = 0.0) -> bool:
        """
        Move eixo por distância relativa.

        Args:
            axis: Eixo a ser movido ('X', 'Y', ou 'Z')
            distance: Distância relativa em pulsos
            speed: Taxa de avanço em pulsos/minuto

        Returns:
            True se movimento bem-sucedido
        """
        if axis not in self.ADDRESSES:
            raise ValueError(f"Eixo inválido: {axis}")

        current = self._read_dword(self.ADDRESSES[axis]['pos_reg'])
        target = current + int(round(distance))

        speed_mm = speed / self.pulses_per_mm if speed else None
        return self.absolute_controller.apply_motion_pulses({axis: target}, speed_mm)

    def move_relative_single_axis(self, axis: str, distance: float) -> bool:
        """
        Move único eixo em coordenadas relativas.

        Args:
            axis: Eixo a ser movido ('X', 'Y', ou 'Z')
            distance: Distância relativa em pulsos

        Returns:
            True se movimento bem-sucedido
        """
        return self.move_relative(axis, distance, speed=0.0)

    def step_move(self, axis: str, steps: int, direction: str) -> bool:
        """
        Executa movimento passo a passo (step) do eixo.

        Args:
            axis: Eixo a ser movido ('X', 'Y', ou 'Z')
            steps: Número de passos (cada passo = 1 pulso)
            direction: Direção ('forward' ou 'backward')

        Returns:
            True se movimento bem-sucedido
        """
        if axis not in self.ADDRESSES:
            raise ValueError(f"Eixo inválido: {axis}")

        if direction not in ['forward', 'backward']:
            raise ValueError(f"Direção inválida: {direction}. Use 'forward' ou 'backward'")

        # Converte direção para sinal
        direction_sign = 1 if direction == 'forward' else -1

        # Calcula distância em pulsos
        distance = steps * direction_sign

        # Executa movimento relativo
        return self.move_relative_single_axis(axis, distance)

    def get_position(self, axis: str) -> float:
        """
        Lê posição atual do eixo.

        Args:
            axis: Eixo a ser lido ('X', 'Y', ou 'Z')

        Returns:
            Posição atual em pulsos
        """
        if axis not in self.ADDRESSES:
            raise ValueError(f"Eixo inválido: {axis}")

        return float(self._read_dword(self.ADDRESSES[axis]['pos_reg']))


# Import correto para a interface
from aoi_lib.plc.interfaces.plc_relative_movement_interface import PLCRelativeMovement
PLCRelativeMovement.register(PLCRelativeMovementController)
