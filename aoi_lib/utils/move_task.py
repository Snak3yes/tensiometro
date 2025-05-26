from PyQt6.QtCore import QThread, pyqtSignal


class MoveTaskThread(QThread):
    """
    Executa um deslocamento absoluto sem bloquear a interface:
      – envia o G-code
      – aguarda a máquina ficar Idle
    """
    finished = pyqtSignal(float, float, float)
    error    = pyqtSignal(str)

    def __init__(self, cnc, x=None, y=None, z=None, feed=1000):
        super().__init__()
        self._cnc  = cnc
        self._x    = x
        self._y    = y
        self._z    = z
        self._feed = feed

    def run(self):
        try:
            ok = self._cnc.move_to_absolute_position(
                    x=self._x, y=self._y, z=self._z, feed_rate=self._feed
                 )
            if not ok:
                self.error.emit("Falha ao enviar comando de movimento")
                return
            self._cnc.wait_for_idle()
            self.finished.emit(self._x or 0.0, self._y or 0.0, self._z or 0.0)
        except Exception as exc:
            self.error.emit(str(exc))