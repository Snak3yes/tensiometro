"""
PLC Homing Controller - Operações de Homing de eixos

Implementa IPLCHoming e encapsula lógica de homing e desbloqueio.
"""

import logging
import time


logger = logging.getLogger(__name__)


class PLCHomingController:
    """
    Controller para operações de homing de eixos PLC.

    Implementa sequência de homing e desbloqueio de eixos.
    """

    # Mapeamento de endereços para homing
    ADDRESSES = {
        'X': {
            'zero': 1000      # M1000_X
        },
        'Y': {
            'zero': 500       # M500_Y
        },
        'Z': {
            'zero': 1500      # M1500_Z
        }
    }

    def __init__(self, connection_manager, absolute_controller):
        """
        Inicializa o controller de homing.

        Args:
            connection_manager: Instância de PLCConnectionManager
            absolute_controller: Instância de PLCAbsoluteMovementController
        """
        self.connection_manager = connection_manager
        self.absolute_controller = absolute_controller

        logger.debug("PLCHomingController criado")

    def _pulse_coil(self, coil: int, duration_ms: int = 100):
        """
        Pulsa coil por duração especificada.

        Args:
            coil: Endereço do coil
            duration_ms: Duração do pulso em ms
        """
        client = self.connection_manager.client
        if not client:
            raise IOError("Cliente Modbus não inicializado")

        client.write_coil(coil, True)
        time.sleep(duration_ms / 1000.0)
        client.write_coil(coil, False)

    def home_all(self) -> bool:
        """
        Realiza homing de todos os eixos (X, Y, Z).

        Sequência: Z primeiro, depois X e Y em paralelo.

        Returns:
            True se homing bem-sucedido
        """
        if not self.connection_manager.is_connected():
            raise IOError("PLC não conectado")

        try:
            logger.info("🏠 Iniciando homing de todos os eixos")

            # Homing Z primeiro (eixo vertical deve ser referenciado primeiro)
            logger.info("🏠 Homing eixo Z")
            self._pulse_coil(self.ADDRESSES['Z']['zero'])
            time.sleep(3.0)

            # Homing X e Y em paralelo
            logger.info("🏠 Homing eixos X e Y em paralelo")
            self._pulse_coil(self.ADDRESSES['X']['zero'])
            self._pulse_coil(self.ADDRESSES['Y']['zero'])

            logger.info("✅ Homing de todos os eixos concluído")
            return True

        except Exception as e:
            logger.error(f"❌ Erro durante homing: {e}")
            return False

    def home_axis(self, axis: str) -> bool:
        """
        Realiza homing de eixo único.

        Args:
            axis: Eixo para homing ('X', 'Y', ou 'Z')

        Returns:
            True se homing bem-sucedido
        """
        axis = axis.upper()
        if axis not in self.ADDRESSES:
            raise ValueError(f"Eixo inválido: {axis}")

        if not self.connection_manager.is_connected():
            raise IOError("PLC não conectado")

        try:
            logger.info(f"🏠 Iniciando homing do eixo {axis}")

            # Pulsa coil de zero do eixo
            self._pulse_coil(self.ADDRESSES[axis]['zero'])

            logger.info(f"✅ Homing do eixo {axis} concluído")
            return True

        except Exception as e:
            logger.error(f"❌ Erro durante homing do eixo {axis}: {e}")
            return False

    def unlock(self) -> None:
        """
        Desbloqueia eixos após erro ou parada de emergência.

        Este método apenas reseta o estado interno. O PLC pode
        requerer procedimento adicional de desbloqueio.
        """
        logger.info("🔓 Desbloqueando eixos")

        # Para qualquer movimento em andamento
        # (Nota: jog_stop deve ser chamado externamente se necessário)

        # Limpa alvos de movimento
        self.absolute_controller.get_targets().clear()

        logger.info("✅ Eixos desbloqueados")


# Import correto para a interface
from aoi_lib.plc.interfaces.plc_homing_interface import IPLCHoming
IPLCHoming.register(PLCHomingController)
