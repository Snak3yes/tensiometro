"""
Measurement Thread for Tension Measurement

Executes tension measurement in background thread using QThread.
Keeps UI responsive during measurement operations.
"""

import logging
import time
from typing import List, Optional
from PyQt6.QtCore import QThread, pyqtSignal
from .models import GridPoint, TensionMeasurement, MeasurementSession

logger = logging.getLogger(__name__)

TENSIOMETER_ENABLE_COIL = 20
TENSIOMETER_DISABLE_COIL = 22


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
        user_feed: float = 1000.0,
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

        self.cnc.move_to_absolute_position(**kwargs)
        self.cnc.wait_for_idle()

    def _enable_tension_sensor(self) -> None:
        try:
            if hasattr(self.cnc, "pulse_coil"):
                self.cnc.pulse_coil(TENSIOMETER_ENABLE_COIL, 100)
                logger.debug("Tenciometro ligado via M20")
            elif hasattr(self.cnc, "_pulse_coil"):
                self.cnc._pulse_coil(TENSIOMETER_ENABLE_COIL, 100)
                logger.debug("Tenciometro ligado via M20")
            else:
                logger.warning("Controlador CNC nao expoe interface para ligar o tenciometro")
        except Exception as e:
            logger.error(f"Erro ao ligar sensor: {e}")

    def _disable_tension_sensor(self) -> None:
        try:
            if hasattr(self.cnc, "pulse_coil"):
                self.cnc.pulse_coil(TENSIOMETER_DISABLE_COIL, 100)
                logger.debug("Tenciometro desligado via M22")
            elif hasattr(self.cnc, "_pulse_coil"):
                self.cnc._pulse_coil(TENSIOMETER_DISABLE_COIL, 100)
                logger.debug("Tenciometro desligado via M22")
            else:
                logger.warning("Controlador CNC nao expoe interface para desligar o tenciometro")
        except Exception as e:
            logger.error(f"Erro ao desligar sensor: {e}")

    @property
    def measurements(self) -> List[TensionMeasurement]:
        return self.session.measurements

    @property
    def is_running(self) -> bool:
        return self.isRunning()
