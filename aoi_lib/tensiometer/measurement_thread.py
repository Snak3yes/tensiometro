"""
Measurement Thread for Tension Measurement

Executes tension measurement in background thread using QThread.
Keeps UI responsive during measurement operations.
"""

import logging
import math
import time
from typing import List, Optional
from PyQt6.QtCore import QThread, pyqtSignal
from .models import GridPoint, TensionMeasurement, MeasurementSession

logger = logging.getLogger(__name__)

TENSIOMETER_POWER_COIL = 20
TENSIOMETER_POWER_ON_PULSE_MS = 100
TENSIOMETER_POWER_OFF_PULSE_MS = 3000


class TensionMeasurementThread(QThread):
    """
    Thread responsavel por executar a medicao de tensao em background.
    """

    progress_updated = pyqtSignal(int, int, str)
    measurement_completed = pyqtSignal(dict)
    finished = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(
        self,
        cnc,
        tensiometer,
        points: List[GridPoint],
        z_height: float,
        z_move: float = 5.0,
        user_feed: Optional[float] = None,
        stabilization_time_ms: int = 500,
    ):
        super().__init__()
        self.cnc = cnc
        self.tensiometer = tensiometer
        self.points = points
        self.z_height = z_height
        self.z_move = z_move
        self.user_feed = user_feed
        self.stabilization_time_ms = stabilization_time_ms
        self.session = MeasurementSession(
            parameters=None,
            measurements=[],
            user_feed=user_feed,
            stabilization_time_ms=stabilization_time_ms,
        )
        self._stop_requested = False

    def request_stop(self) -> None:
        logger.info("Solicitacao de parada recebida")
        self._stop_requested = True

    def run(self) -> None:
        try:
            logger.info(f"Iniciando medicao de {len(self.points)} pontos")
            self._setup_absolute_mode()
            self._enable_tension_sensor()
            self._move_abs(z=self.z_move, feed=self.user_feed)

            total_points = len(self.points)
            for idx, point in enumerate(self.points, 1):
                if self._stop_requested:
                    logger.info("Medicao interrompida pelo usuario")
                    self.error_occurred.emit("Medicao interrompida pelo usuario")
                    return

                logger.debug(f"Ponto {idx}/{total_points}: ({point.x:.3f}, {point.y:.3f})")
                self.progress_updated.emit(idx, total_points, f"Medindo ponto {idx}/{total_points}")

                self._move_abs(x=point.x, y=point.y, z=self.z_move, feed=self.user_feed)
                self._move_abs(z=self.z_height, feed=self.user_feed)

                stabilization_sec = self.stabilization_time_ms / 1000.0
                logger.debug(f"Estabilizando por {stabilization_sec:.1f}s...")
                time.sleep(stabilization_sec)

                tension_value = self.tensiometer.read_tension_value()
                logger.debug(f"Tensao lida: {tension_value}")

                measurement = TensionMeasurement(
                    point=point,
                    z_height=self.z_height,
                    tension_value=tension_value,
                )
                self.session.add_measurement(measurement)
                self.measurement_completed.emit(measurement.to_dict())

                self._move_abs(z=self.z_move, feed=self.user_feed)
                time.sleep(0.1)

            logger.info("Medicao concluida com sucesso")
            logger.info(f"Total medido: {len(self.session.measurements)} pontos")
            self.finished.emit([m.to_dict() for m in self.session.measurements])

        except Exception as e:
            logger.error(f"Erro durante medicao: {e}", exc_info=True)
            self.error_occurred.emit(f"Erro durante medicao: {str(e)}")
        finally:
            self._move_z_to_absolute_zero()
            self._disable_tension_sensor()

    def _setup_absolute_mode(self) -> None:
        try:
            if hasattr(self.cnc, "set_absolute_mode"):
                self.cnc.set_absolute_mode()
            elif hasattr(self.cnc, "send_raw_gcode"):
                self.cnc.send_raw_gcode("G90")
            else:
                logger.warning("Nao foi possivel configurar modo absoluto")
        except Exception as e:
            logger.error(f"Erro ao configurar modo absoluto: {e}")

    def _move_abs(
        self,
        x: Optional[float] = None,
        y: Optional[float] = None,
        z: Optional[float] = None,
        feed: Optional[float] = None,
    ) -> None:
        kwargs = {}
        if x is not None:
            kwargs["x"] = x
        if y is not None:
            kwargs["y"] = y
        if z is not None:
            kwargs["z"] = z
        if feed is not None:
            kwargs["feed_rate"] = feed

        timeout = self._calculate_timeout_seconds(x=x, y=y, z=z, feed=feed)
        self.cnc.move_to_absolute_position(**kwargs)

        if not self.cnc.wait_for_idle(timeout=timeout):
            target_desc = ", ".join(f"{axis}={value}" for axis, value in kwargs.items() if axis != "feed_rate")
            raise RuntimeError(
                f"Movimento nao concluiu dentro do timeout para {target_desc or 'destino desconhecido'}"
            )

    def _calculate_timeout_seconds(
        self,
        x: Optional[float] = None,
        y: Optional[float] = None,
        z: Optional[float] = None,
        feed: Optional[float] = None,
    ) -> int:
        """
        Estimate a timeout proportional to the requested move.

        When no feed is provided, keep the timeout conservative and rely on the PLC's
        current speed registers.
        """
        if feed is None or feed <= 0:
            return 30

        current = self._read_current_position_for_timeout()
        if current is None:
            return 30

        deltas = []
        if x is not None:
            deltas.append(abs(x - current.get("x", 0.0)))
        if y is not None:
            deltas.append(abs(y - current.get("y", 0.0)))
        if z is not None:
            deltas.append(abs(z - current.get("z", 0.0)))

        if not deltas:
            return 30

        longest_move = max(deltas)
        expected_seconds = (longest_move / feed) * 60.0
        return max(15, min(300, int(math.ceil(expected_seconds * 1.5 + 5))))

    def _read_current_position_for_timeout(self) -> Optional[dict]:
        """Read current XYZ using the same user-facing unit used by absolute moves."""
        try:
            if hasattr(self.cnc, "get_current_position"):
                position = self.cnc.get_current_position()
                if isinstance(position, dict):
                    if {"x", "y", "z"}.issubset(position.keys()):
                        return {
                            "x": float(position["x"]),
                            "y": float(position["y"]),
                            "z": float(position["z"]),
                        }
                    if {"X", "Y", "Z"}.issubset(position.keys()):
                        return {
                            "x": float(position["X"]),
                            "y": float(position["Y"]),
                            "z": float(position["Z"]),
                        }

            if hasattr(self.cnc, "read_position"):
                return {
                    "x": float(self.cnc.read_position("X")),
                    "y": float(self.cnc.read_position("Y")),
                    "z": float(self.cnc.read_position("Z")),
                }
        except Exception as exc:
            logger.debug("Falha ao ler posicao atual para timeout de movimento: %s", exc)

        return None

    def _enable_tension_sensor(self) -> None:
        try:
            if hasattr(self.cnc, "pulse_coil"):
                self.cnc.pulse_coil(TENSIOMETER_POWER_COIL, TENSIOMETER_POWER_ON_PULSE_MS)
                logger.debug("Tenciometro ligado via M20 com pulso curto")
            elif hasattr(self.cnc, "_pulse_coil"):
                self.cnc._pulse_coil(TENSIOMETER_POWER_COIL, TENSIOMETER_POWER_ON_PULSE_MS)
                logger.debug("Tenciometro ligado via M20 com pulso curto")
            else:
                logger.warning("Controlador CNC nao expoe interface para ligar o tenciometro")
        except Exception as e:
            logger.error(f"Erro ao ligar sensor: {e}")

    def _disable_tension_sensor(self) -> None:
        try:
            if hasattr(self.cnc, "pulse_coil"):
                self.cnc.pulse_coil(TENSIOMETER_POWER_COIL, TENSIOMETER_POWER_OFF_PULSE_MS)
                logger.debug("Tenciometro desligado via M20 com pulso de 3s")
            elif hasattr(self.cnc, "_pulse_coil"):
                self.cnc._pulse_coil(TENSIOMETER_POWER_COIL, TENSIOMETER_POWER_OFF_PULSE_MS)
                logger.debug("Tenciometro desligado via M20 com pulso de 3s")
            else:
                logger.warning("Controlador CNC nao expoe interface para desligar o tenciometro")
        except Exception as e:
            logger.error(f"Erro ao desligar sensor: {e}")

    def _move_z_to_absolute_zero(self) -> None:
        """Ao encerrar a rotina, reposiciona o eixo Z na origem absoluta."""
        try:
            logger.info("Encerrando medicao: movendo Z para posicao absoluta 0")
            self._move_abs(z=0.0, feed=self.user_feed)
        except Exception as e:
            logger.error(f"Erro ao mover Z para zero absoluto no encerramento: {e}")

    @property
    def measurements(self) -> List[TensionMeasurement]:
        return self.session.measurements

    @property
    def is_running(self) -> bool:
        return self.isRunning()
