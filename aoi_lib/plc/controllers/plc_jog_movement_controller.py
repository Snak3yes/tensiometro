"""
PLC Jog Movement Controller - Movimento Jog (contínuo) de eixos

Implementa PLCJogMovement e encapsula lógica de movimento Jog.
"""

import logging
from typing import Dict, Optional


logger = logging.getLogger(__name__)


class PLCJogMovementController:
    """
    Controller para movimento Jog de eixos PLC.

    Implementa movimento contínuo (Jog) com velocidade controlada.
    """

    # Mapeamento de endereços para movimento Jog
    ADDRESSES = {
        'X': {
            'speed': 21000,       # D21000_X
            'jog_plus': 1070,     # M1070_X
            'jog_minus': 1080,    # M1080_X
            'jog_stop_plus': 1010,  # M1010_X
            'jog_stop_minus': 1011  # M1011_X
        },
        'Y': {
            'speed': 20500,       # D20500_Y
            'jog_plus': 570,      # M570_Y
            'jog_minus': 580,     # M580_Y
            'jog_stop_plus': 510,   # M510_Y
            'jog_stop_minus': 511   # M511_Y
        },
        'Z': {
            'speed': 21500,       # D21500_Z
            'jog_plus': 1570,     # M1570_Z
            'jog_minus': 1580,    # M1580_Z
            'jog_stop_plus': 1510,  # M1510_Z
            'jog_stop_minus': 1511  # M1511_Z
        }
    }

    def __init__(self, connection_manager, absolute_controller, pulses_per_mm: float = 1.0, max_feed: Optional[Dict] = None):
        """
        Inicializa o controller de movimento Jog.

        Args:
            connection_manager: Instância de PLCConnectionManager
            absolute_controller: Instância de PLCAbsoluteMovementController (para clamp_feed_rate)
            pulses_per_mm: Fator de conversão pulsos → mm (padrão: 1.0)
            max_feed: Limites máximos de feed por eixo
        """
        self.connection_manager = connection_manager
        self.absolute_controller = absolute_controller
        self.pulses_per_mm = pulses_per_mm
        self.max_feed = max_feed or {'x': float('inf'), 'y': float('inf'), 'z': float('inf')}

        # Rastreia estado Jog de cada eixo
        self._jog_state: Dict[str, str] = {'X': 'stopped', 'Y': 'stopped', 'Z': 'stopped'}

        logger.debug(f"PLCJogMovementController criado: pulses_per_mm={pulses_per_mm}")

    def _write_dword(self, address: int, value: int):
        """
        Escreve valor INT32 (little-endian) em dois registradores.

        Args:
            address: Endereço base do registrador
            value: Valor de 32 bits a escrever
        """
        client = self.connection_manager.client
        if not client:
            raise IOError("Cliente Modbus não inicializado")

        u32 = value & 0xFFFFFFFF
        lo = u32 & 0xFFFF
        hi = (u32 >> 16) & 0xFFFF
        return client.write_registers(address, [lo, hi])

    def jog_start(self, axis: str, speed: float) -> None:
        """
        Inicia movimento Jog no eixo especificado.

        Args:
            axis: Eixo para jog ('X', 'Y', ou 'Z')
            speed: Velocidade em pulsos/minuto
        """
        axis = axis.upper()
        if axis not in self.ADDRESSES:
            raise ValueError(f"Eixo inválido: {axis}")

        if not self.connection_manager.is_connected():
            raise IOError("PLC não conectado")

        cfg = self.ADDRESSES[axis]
        client = self.connection_manager.client

        # Converte speed (pulsos/min) para velocidade
        fr = self.absolute_controller._clamp_feed_rate(speed / self.pulses_per_mm)
        speed_pulses = int(round(fr * self.pulses_per_mm))
        self._write_dword(cfg['speed'], speed_pulses)

        # Aciona coil Jog Plus (movimento para frente)
        client.write_coil(cfg['jog_plus'], True)

        self._jog_state[axis] = 'forward'
        logger.info(f"🏃 Jog iniciado: eixo {axis}, velocidade={speed_pulses} pulsos/min")

    def jog_stop(self, axis: str) -> None:
        """
        Para movimento Jog no eixo especificado.

        Args:
            axis: Eixo a ser parado ('X', 'Y', ou 'Z')
        """
        axis = axis.upper()
        if axis not in self.ADDRESSES:
            raise ValueError(f"Eixo inválido: {axis}")

        if not self.connection_manager.is_connected():
            logger.warning("PLC não conectado - não é possível parar jog")
            return

        cfg = self.ADDRESSES[axis]
        client = self.connection_manager.client

        # Desliga ambos os coils (jog_plus e jog_minus)
        client.write_coil(cfg['jog_plus'], False)
        client.write_coil(cfg['jog_minus'], False)

        self._jog_state[axis] = 'stopped'
        logger.info(f"🛑 Jog parado: eixo {axis}")

    def is_jogging(self, axis: str) -> bool:
        """
        Verifica se eixo está em movimento Jog.

        Args:
            axis: Eixo a ser verificado ('X', 'Y', ou 'Z')

        Returns:
            True se jog ativo, False caso contrário
        """
        axis = axis.upper()
        if axis not in self.ADDRESSES:
            raise ValueError(f"Eixo inválido: {axis}")

        return self._jog_state.get(axis, 'stopped') != 'stopped'

    def stop_all_jog(self) -> None:
        """
        Para todos os movimentos Jog de todos os eixos.

        Método de conveniência para parar todos os eixos de uma vez.
        """
        for axis in ['X', 'Y', 'Z']:
            self.jog_stop(axis)

        logger.info("🛑 Todos os eixos parados")


# Import correto para a interface
from aoi_lib.plc.interfaces.plc_jog_movement_interface import PLCJogMovement
PLCJogMovement.register(PLCJogMovementController)
