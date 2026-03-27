"""
PLC Jog Movement Controller - Movimento jog de eixos.

Implementa PLCJogMovement e encapsula logica de jog.
"""

import logging
from typing import Dict, Optional


logger = logging.getLogger(__name__)


class PLCJogMovementController:
    """
    Controller para movimento jog de eixos PLC.
    """

    ADDRESSES = {
        "X": {
            "speed": 20500,
            "jog_plus": 570,
            "jog_minus": 580,
            "jog_stop_plus": 1010,
            "jog_stop_minus": 1011,
        },
        "Y": {
            "speed": 20500,
            "jog_plus": 670,
            "jog_minus": 680,
            "jog_stop_plus": 1020,
            "jog_stop_minus": 1021,
        },
        "Z": {
            "speed": 21500,
            "jog_plus": 770,
            "jog_minus": 780,
            "jog_stop_plus": 1030,
            "jog_stop_minus": 1031,
        },
    }

    def __init__(self, connection_manager, absolute_controller, pulses_per_mm: float = 1.0, max_feed: Optional[Dict] = None):
        self.connection_manager = connection_manager
        self.absolute_controller = absolute_controller
        self.pulses_per_mm = pulses_per_mm
        self.max_feed = max_feed or {"x": float("inf"), "y": float("inf"), "z": float("inf")}
        self._jog_state: Dict[str, str] = {"X": "stopped", "Y": "stopped", "Z": "stopped"}
        logger.debug("PLCJogMovementController criado: pulses_per_mm=%s", pulses_per_mm)

    def _write_dword(self, address: int, value: int):
        client = self.connection_manager.client
        if not client:
            raise IOError("Cliente Modbus nao inicializado")

        u32 = value & 0xFFFFFFFF
        lo = u32 & 0xFFFF
        hi = (u32 >> 16) & 0xFFFF
        return client.write_registers(address, [lo, hi])

    def jog_start(self, axis: str, speed: float, direction: int = 1) -> None:
        axis = axis.upper()
        if axis not in self.ADDRESSES:
            raise ValueError(f"Eixo invalido: {axis}")

        if not self.connection_manager.is_connected():
            raise IOError("PLC nao conectado")

        cfg = self.ADDRESSES[axis]
        client = self.connection_manager.client

        fr = self.absolute_controller._clamp_feed_rate(speed / self.pulses_per_mm)
        speed_pulses = int(round(fr * self.pulses_per_mm))
        self._write_dword(cfg["speed"], speed_pulses)

        client.write_coil(cfg["jog_plus"], False)
        client.write_coil(cfg["jog_minus"], False)

        coil = cfg["jog_plus"] if direction >= 0 else cfg["jog_minus"]
        client.write_coil(coil, True)

        self._jog_state[axis] = "forward" if direction >= 0 else "backward"
        logger.info(
            "Jog iniciado: eixo %s, sentido=%s, velocidade=%s pulsos/min",
            axis,
            self._jog_state[axis],
            speed_pulses,
        )

    def jog_stop(self, axis: str) -> None:
        axis = axis.upper()
        if axis not in self.ADDRESSES:
            raise ValueError(f"Eixo invalido: {axis}")

        if not self.connection_manager.is_connected():
            logger.warning("PLC nao conectado - nao e possivel parar jog")
            return

        cfg = self.ADDRESSES[axis]
        client = self.connection_manager.client
        client.write_coil(cfg["jog_plus"], False)
        client.write_coil(cfg["jog_minus"], False)

        self._jog_state[axis] = "stopped"
        logger.info("Jog parado: eixo %s", axis)

    def is_jogging(self, axis: str) -> bool:
        axis = axis.upper()
        if axis not in self.ADDRESSES:
            raise ValueError(f"Eixo invalido: {axis}")
        return self._jog_state.get(axis, "stopped") != "stopped"

    def stop_all_jog(self) -> None:
        for axis in ["X", "Y", "Z"]:
            self.jog_stop(axis)
        logger.info("Todos os eixos parados")


from aoi_lib.plc.interfaces.plc_jog_movement_interface import PLCJogMovement

PLCJogMovement.register(PLCJogMovementController)
