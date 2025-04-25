from PyQt6.QtCore import QThread, pyqtSignal


class MoveTaskThread(QThread):
    """
    Executa um deslocamento absoluto sem bloquear a interface:
      – envia o G-code
      – aguarda a máquina ficar Idle
    """
    finished = pyqtSignal(float, float)   # x, y que foram alcançados
    error    = pyqtSignal(str)

    def __init__(self, cnc, x, y, feed):
        super().__init__()
        self._cnc  = cnc
        self._x    = x
        self._y    = y
        self._feed = feed

    def run(self):
        try:
            ok = self._cnc.move_to_absolute_position(self._x, self._y,
                                                     self._feed)
            if not ok:
                self.error.emit("Falha ao enviar comando de movimento")
                return
            self._cnc.wait_for_idle()
            self.finished.emit(self._x, self._y)
        except Exception as exc:
            self.error.emit(str(exc))