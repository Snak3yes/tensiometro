"""
PLC Homing Controller - Operacoes de homing de eixos.

Implementa IPLCHoming e encapsula logica de homing e desbloqueio.
"""

import logging
import time


logger = logging.getLogger(__name__)


class PLCHomingController:
    """
    Controller para operacoes de homing de eixos PLC.

    O mapa atual do ladder expoe M1350 como inicio da rotina global de homing.
    Os bits M1500/M1000/M500 sao confirmacoes de homing por eixo.
    """

    HOME_ALL_COIL = 1350

    ADDRESSES = {
        "X": {"zero": 1500},
        "Y": {"zero": 1000},
        "Z": {"zero": 500},
    }

    def __init__(self, connection_manager, absolute_controller):
        self.connection_manager = connection_manager
        self.absolute_controller = absolute_controller
        logger.debug("PLCHomingController criado")

    def _pulse_coil(self, coil: int, duration_ms: int = 100):
        client = self.connection_manager.client
        if not client:
            raise IOError("Cliente Modbus nao inicializado")

        client.write_coil(coil, True)
        time.sleep(duration_ms / 1000.0)
        client.write_coil(coil, False)

    def home_all(self) -> bool:
        if not self.connection_manager.is_connected():
            raise IOError("PLC nao conectado")

        try:
            logger.info("Iniciando homing global via M%d", self.HOME_ALL_COIL)
            self._pulse_coil(self.HOME_ALL_COIL)
            logger.info("Homing global iniciado")
            return True
        except Exception as e:
            logger.error(f"Erro durante homing: {e}")
            return False

    def home_axis(self, axis: str) -> bool:
        axis = axis.upper()
        if axis not in self.ADDRESSES:
            raise ValueError(f"Eixo invalido: {axis}")

        # Mantem compatibilidade de API; o PLC executa homing global.
        return self.home_all()

    def unlock(self) -> None:
        logger.info("Desbloqueando eixos")
        self.absolute_controller.get_targets().clear()
        logger.info("Eixos desbloqueados")


from aoi_lib.plc.interfaces.plc_homing_interface import IPLCHoming

IPLCHoming.register(PLCHomingController)
