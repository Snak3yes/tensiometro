"""
Measurement Thread for Tension Measurement

Executes tension measurement in background thread using QThread.
Keeps UI responsive during measurement operations.

Created: 2026-01-14 (Phase 1 - SOLID Refactoring)
Extracted from: aoi_lib/stencil_tension.py (lines 203-324)
"""

import logging
import time
from typing import List, Optional
from PyQt6.QtCore import QThread, pyqtSignal
from .models import GridPoint, TensionMeasurement, MeasurementSession

logger = logging.getLogger(__name__)


class TensionMeasurementThread(QThread):
    """
    Thread responsável por executar a medição de tensão em background.

    Sinais:
        progress_updated: (current, total, message) - Progresso da medição
        measurement_completed: (measurement_dict) - Medição individual finalizada
        finished: (measurements_list) - Todas medições completadas
        error_occurred: (error_message) - Erro durante medição

    Attributes:
        cnc: Controller CNC para movimentação
        tensiometer: Gerenciador serial do tensiômetro
        points: Lista de GridPoint para medir
        z_height: Altura Z de medição
        z_move: Altura Z segura para movimentação
        user_feed: Avanço para movimentos CNC (mm/min)
        stabilization_time_ms: Tempo de estabilização após descida Z (ms)
        session: MeasurementSession para armazenar resultados
        _stop_requested: Flag para solicitação de parada
    """

    # Sinais PyQt6
    progress_updated = pyqtSignal(int, int, str)  # atual, total, mensagem
    measurement_completed = pyqtSignal(dict)      # dict com medição
    finished = pyqtSignal(list)                   # lista de dicts
    error_occurred = pyqtSignal(str)              # mensagem de erro

    def __init__(
        self,
        cnc,
        tensiometer,
        points: List[GridPoint],
        z_height: float,
        z_move: float = 5.0,
        user_feed: float = 1000.0,
        stabilization_time_ms: int = 500
    ):
        """
        Inicializa thread de medição.

        Args:
            cnc: Controller CNC (deve ter move_to_absolute_position e wait_for_idle)
            tensiometer: TensiometerSerialManager
            points: Lista de GridPoint ordenados
            z_height: Altura Z para medição (mm)
            z_move: Altura Z segura para movimento entre pontos (mm)
            user_feed: Avanço (mm/min)
            stabilization_time_ms: Tempo de estabilização (ms)
        """
        super().__init__()
        self.cnc = cnc
        self.tensiometer = tensiometer
        self.points = points
        self.z_height = z_height
        self.z_move = z_move
        self.user_feed = user_feed
        self.stabilization_time_ms = stabilization_time_ms
        self.session = MeasurementSession(
            parameters=None,  # Será configurado pelo caller
            measurements=[],
            user_feed=user_feed,
            stabilization_time_ms=stabilization_time_ms
        )
        self._stop_requested = False

    def request_stop(self) -> None:
        """Solicita parada graciosa da medição."""
        logger.info("Solicitação de parada recebida")
        self._stop_requested = True

    def run(self) -> None:
        """Executa o processo de medição em background."""
        try:
            logger.info(f"Iniciando medição de {len(self.points)} pontos")

            # Configura modo absoluto
            self._setup_absolute_mode()

            # Move para altura segura inicial
            logger.debug(f"Movendo para altura segura Z={self.z_move}")
            self._move_abs(z=self.z_move, feed=self.user_feed)

            total_points = len(self.points)

            for idx, point in enumerate(self.points, 1):
                # Verifica parada solicitada
                if self._stop_requested:
                    logger.info("Medição interrompida pelo usuário")
                    self.error_occurred.emit("Medição interrompida pelo usuário")
                    return

                # Log detalhado
                logger.debug(
                    f"Ponto {idx}/{total_points}: ({point.x:.3f}, {point.y:.3f})"
                )

                # Emite progresso
                self.progress_updated.emit(
                    idx,
                    total_points,
                    f"Medindo ponto {idx}/{total_points}"
                )

                # 1) Move XY mantendo altura segura
                self._move_abs(
                    x=point.x,
                    y=point.y,
                    z=self.z_move,
                    feed=self.user_feed
                )

                # 2) Desce para altura de medição
                logger.debug(f"Descendo para Z={self.z_height}")
                self._move_abs(z=self.z_height, feed=self.user_feed)

                # 3) Aguarda estabilização
                stabilization_sec = self.stabilization_time_ms / 1000.0
                logger.debug(f"Estabilizando por {stabilization_sec:.1f}s...")
                time.sleep(stabilization_sec)

                # 4) Lê tensão
                tension_value = self.tensiometer.read_tension_value()
                logger.debug(f"Tensão lida: {tension_value}")

                # 5) Cria objeto de medição
                measurement = TensionMeasurement(
                    point=point,
                    z_height=self.z_height,
                    tension_value=tension_value
                )
                self.session.add_measurement(measurement)

                # 6) Emite sinal com medição individual
                self.measurement_completed.emit(measurement.to_dict())

                # 7) Retorna para altura segura
                logger.debug(f"Subindo para Z={self.z_move}")
                self._move_abs(z=self.z_move, feed=self.user_feed)

                # 8) Pequena pausa entre pontos
                time.sleep(0.1)

            # Medição completa com sucesso
            logger.info("Medição concluída com sucesso!")
            logger.info(
                f"Total medido: {len(self.session.measurements)} pontos"
            )

            # Desliga sensor de tensão (pulso na coil M0)
            self._disable_tension_sensor()

            # Emite resultado final
            measurements_dict = [m.to_dict() for m in self.session.measurements]
            self.finished.emit(measurements_dict)

        except Exception as e:
            logger.error(f"Erro durante medição: {e}", exc_info=True)
            self.error_occurred.emit(f"Erro durante medição: {str(e)}")

    def _setup_absolute_mode(self) -> None:
        """Configura CNC para modo de coordenadas absolutas (G90)."""
        try:
            if hasattr(self.cnc, 'set_absolute_mode'):
                self.cnc.set_absolute_mode()
            elif hasattr(self.cnc, 'send_raw_gcode'):
                self.cnc.send_raw_gcode('G90')
            else:
                logger.warning("Não foi possível configurar modo absoluto")
        except Exception as e:
            logger.error(f"Erro ao configurar modo absoluto: {e}")

    def _move_abs(self, x: Optional[float] = None, y: Optional[float] = None,
                  z: Optional[float] = None, feed: Optional[float] = None) -> None:
        """
        Move para coordenadas absolutas.

        Args:
            x: Coordenada X (mm)
            y: Coordenada Y (mm)
            z: Coordenada Z (mm)
            feed: Avanço (mm/min)
        """
        kwargs = {}
        if x is not None:
            kwargs['x'] = x
        if y is not None:
            kwargs['y'] = y
        if z is not None:
            kwargs['z'] = z

        if feed is not None:
            kwargs['feed_rate'] = feed

        # Executa movimento
        self.cnc.move_to_absolute_position(**kwargs)

        # Aguarda movimento completar
        self.cnc.wait_for_idle()

    def _disable_tension_sensor(self) -> None:
        """Desliga o sensor de tensão (pulso de 3000ms na coil M0)."""
        try:
            if hasattr(self.cnc, '_pulse_coil'):
                self.cnc._pulse_coil(0, 3000)
                logger.debug("Sensor de tensão desligado")
        except Exception as e:
            logger.error(f"Erro ao desligar sensor: {e}")

    @property
    def measurements(self) -> List[TensionMeasurement]:
        """Retorna lista de medições realizadas."""
        return self.session.measurements

    @property
    def is_running(self) -> bool:
        """Verifica se thread está em execução."""
        return self.isRunning()
