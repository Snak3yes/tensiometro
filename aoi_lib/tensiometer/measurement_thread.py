"""
Módulo: measurement_thread.py
Descrição: Thread QThread para medição de tensão em background
Permite medição assíncrona mantendo a interface responsiva
"""

import logging
import time
from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)


class TensionMeasurementThread(QThread):
    """
    Thread responsável por executar a medição de tensão em background,
    permitindo que a interface continue responsiva.

    Workflow:
    1. Move para safe height (Z_move)
    2. Para cada ponto (X, Y):
       a. Move XY mantendo safe height
       b. Desce para Z_down
       c. Aguarda estabilização
       d. Lê tensão do tensiômetro
       e. Sobe para safe height
    3. Emite sinal finalizado com lista de medições

    Sinais:
        progress_updated: (ponto_atual, total_pontos, status_msg)
        measurement_completed: (dict) - Ponto medido com dados {x, y, z, tension}
        finished: (list) - Lista completa de medições
        error_occurred: (str) - Mensagem de erro
    """

    # Sinais para comunicação com a interface
    progress_updated = pyqtSignal(int, int, str)  # ponto_atual, total_pontos, status_msg
    measurement_completed = pyqtSignal(dict)      # ponto medido com dados
    finished = pyqtSignal(list)                   # lista completa de medições
    error_occurred = pyqtSignal(str)              # mensagem de erro

    def __init__(self, cnc_controller, tensiometer, points, z_down, z_move,
                 user_feed, stabilization_time, parameters):
        """
        Inicializa thread de medição.

        Args:
            cnc_controller: Controlador CNC (PLCAxisController)
            tensiometer: Gerenciador serial do tensiômetro
            points: Lista de pontos [(x1, y1), (x2, y2), ...]
            z_down: Altura Z para medição (contato com stencil)
            z_move: Altura Z para movimentação (safe height)
            user_feed: Velocidade de avanço (mm/min)
            stabilization_time: Tempo de estabilização (ms)
            parameters: Parâmetros adicionais da medição
        """
        super().__init__()
        self.cnc = cnc_controller
        self.tensiometer = tensiometer
        self.points = points
        self.z_down = z_down
        self.z_move = z_move
        self.user_feed = user_feed
        self.stabilization_time = stabilization_time
        self.parameters = parameters
        self.measurements = []
        self._stop_requested = False

    def request_stop(self):
        """Solicita parada da medição."""
        self._stop_requested = True

    def run(self):
        """Executa o processo de medição."""
        try:
            log = logging.getLogger("TensionMeasurementThread")
            log.info("Iniciando medição de tensão em thread separada")

            # Garante modo absoluto
            if hasattr(self.cnc, "set_absolute_mode"):
                self.cnc.set_absolute_mode()
            else:
                if hasattr(self.cnc, "send_raw_gcode"):
                    self.cnc.send_raw_gcode("G90")

            # Move para altura de movimentação (safe height)
            self._move_abs(z=self.z_move, feed=self.user_feed)

            total_points = len(self.points)

            for idx, (x, y) in enumerate(self.points, 1):
                # Verifica se foi solicitada a parada
                if self._stop_requested:
                    log.info("Medição interrompida pelo usuário")
                    self.error_occurred.emit("Medição interrompida pelo usuário")
                    return

                log.debug("Ponto %d de %d -> X%.3f Y%.3f", idx, total_points, x, y)

                # Emite progresso
                self.progress_updated.emit(idx, total_points, f"Medindo ponto {idx}/{total_points}")

                # 1) Move XY mantendo a safe height
                self._move_abs(x=x, y=y, z=self.z_move, feed=self.user_feed)

                # 2) Desce até a altura de medição
                self._move_abs(z=self.z_down, feed=self.user_feed)

                # 3) Aguarda estabilização
                stabilization_sec = self.stabilization_time / 1000.0
                log.debug("Aguardando estabilização por %.1fs...", stabilization_sec)
                time.sleep(stabilization_sec)

                # 4) Lê tensão
                tension = self.tensiometer.read_tension_value()
                log.debug("Tensão medida no ponto %d: %s", idx, tension)

                # 5) Salva medição
                measurement = {"x": x, "y": y, "z": self.z_down, "tension": tension}
                self.measurements.append(measurement)

                # Emite medição individual
                self.measurement_completed.emit(measurement)

                # 6) Retorna para a safe height
                self._move_abs(z=self.z_move, feed=self.user_feed)

                # 7) Pequena pausa entre pontos
                time.sleep(0.1)

            # Emite resultado final
            log.info("Medição de tensão concluída com sucesso")

            # Desliga o sensor de tensão (pulso de 3000 ms na memória M0)
            try:
                if hasattr(self.cnc, "_pulse_coil"):
                    self.cnc._pulse_coil(0, 3000)
            except Exception as e:
                log.error(f"Falha ao desligar sensor: {e}")

            # Emite sinal de finalização
            self.finished.emit(self.measurements)

        except Exception as e:
            log.error(f"Erro durante medição: {e}", exc_info=True)
            self.error_occurred.emit(f"Erro durante medição: {str(e)}")

    def _move_abs(self, *, x=None, y=None, z=None, feed=None):
        """
        Move em coordenadas absolutas.

        Args:
            x: Coordenada X (opcional)
            y: Coordenada Y (opcional)
            z: Coordenada Z (opcional)
            feed: Velocidade de avanço (opcional)
        """
        if feed is not None:
            self.cnc.move_to_absolute_position(x=x, y=y, z=z, feed_rate=feed)
        else:
            self.cnc.move_to_absolute_position(x=x, y=y, z=z)
        self.cnc.wait_for_idle()

    def _move_rel(self, *, x=None, y=None, z=None, feed=None):
        """
        Move em coordenadas relativas.

        Args:
            x: Deslocamento X (opcional)
            y: Deslocamento Y (opcional)
            z: Deslocamento Z (opcional)
            feed: Velocidade de avanço (opcional)
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

        self.cnc.move_relative(**kwargs)
        self.cnc.wait_for_idle()
