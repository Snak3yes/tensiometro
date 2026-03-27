"""
movement_orchestrator.py
------------------------
Orquestrador de movimentos e controle de maquina.
"""

import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class MovementResult:
    """Resultado de uma operacao de movimento/controle."""

    success: bool
    error_message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class MovementOrchestrator:
    """
    Orquestrador de logica de movimento.
    """

    def __init__(self, controller, config_manager=None):
        self.controller = controller
        self.config = config_manager
        self.cnc = controller.cnc if hasattr(controller, "cnc") else controller

    def _validate_connection(self) -> MovementResult:
        if not self.cnc.is_connected:
            return MovementResult(False, "CNC nao conectada")
        return MovementResult(True)

    def _validate_machine_state(self) -> MovementResult:
        status = getattr(self.cnc, "machine_status", "")
        if status and str(status).lower().startswith("alarm"):
            return MovementResult(False, f"Maquina em alarme: {status}")
        return MovementResult(True)

    def validate_feed_rate(self, feed: float) -> MovementResult:
        if not self.cnc.is_connected:
            return MovementResult(True, data={"feed": feed, "clamped": False})

        try:
            max_feeds = list(self.cnc.max_feed.values())
            max_limit = max(max_feeds) if max_feeds else 30000.0

            if feed > max_limit:
                return MovementResult(
                    True,
                    data={"feed": max_limit, "clamped": True, "original": feed, "limit": max_limit},
                )

            return MovementResult(True, data={"feed": feed, "clamped": False})
        except Exception as e:
            return MovementResult(False, f"Erro validando feed: {e}")

    def jog(self, axis: str, direction: int, feed: float) -> MovementResult:
        if not (res := self._validate_connection()).success:
            return res
        if not (res := self._validate_machine_state()).success:
            return res

        f_res = self.validate_feed_rate(feed)
        if not f_res.success:
            return f_res

        try:
            self.cnc.jog_start(axis, direction, f_res.data["feed"])
            return MovementResult(True)
        except Exception as e:
            logger.error(f"Erro no jog: {e}")
            return MovementResult(False, str(e))

    def stop_jog(self) -> MovementResult:
        try:
            self.cnc.jog_stop()
            return MovementResult(True)
        except Exception as e:
            return MovementResult(False, str(e))

    def step_move(self, axis: str, direction: int, step: float, feed: float) -> MovementResult:
        if not (res := self._validate_connection()).success:
            return res
        if not (res := self._validate_machine_state()).success:
            return res

        f_res = self.validate_feed_rate(feed)
        if not f_res.success:
            return f_res

        try:
            self.cnc.step_move(axis, step * direction, f_res.data["feed"])
            return MovementResult(True)
        except Exception as e:
            logger.error(f"Erro no step move: {e}")
            return MovementResult(False, str(e))

    def move_absolute(self, x: float, y: float, z: float, feed: float) -> MovementResult:
        if not (res := self._validate_connection()).success:
            return res
        if not (res := self._validate_machine_state()).success:
            return res

        f_res = self.validate_feed_rate(feed)
        valid_feed = f_res.data["feed"]

        try:
            self.cnc.move_to_absolute_position(x, y, z, feed_rate=valid_feed)
            return MovementResult(True)
        except Exception as e:
            return MovementResult(False, str(e))

    def home(self) -> MovementResult:
        if not (res := self._validate_connection()).success:
            return res
        if not (res := self._validate_machine_state()).success:
            return res

        try:
            if hasattr(self.cnc, "home_all"):
                self.cnc.home_all()
            else:
                self.cnc.move_to_absolute_position(0, 0, 0, feed_rate=1000)
            return MovementResult(True)
        except Exception as e:
            return MovementResult(False, f"Erro no homing: {e}")

    def set_backlight(self, on: bool) -> MovementResult:
        if not (res := self._validate_connection()).success:
            return res

        if hasattr(self.cnc, "backlight_set"):
            try:
                self.cnc.backlight_set(on)
                return MovementResult(True)
            except Exception as e:
                return MovementResult(False, str(e))

        return MovementResult(False, "Controlador nao suporta backlight")

    def emergency_stop(self) -> MovementResult:
        try:
            if hasattr(self.cnc, "send_soft_reset"):
                self.cnc.send_soft_reset()
                return MovementResult(True)
            return MovementResult(False, "Comando nao suportado")
        except Exception as e:
            return MovementResult(False, str(e))

    def unlock(self) -> MovementResult:
        try:
            if hasattr(self.cnc, "unlock"):
                self.cnc.unlock()
                return MovementResult(True)
            return MovementResult(False, "Comando nao suportado")
        except Exception as e:
            return MovementResult(False, str(e))
