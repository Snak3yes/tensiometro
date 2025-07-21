# camera_manager.py
import cv2, sys
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtGui  import QImage, QPixmap

class CameraManager(QObject):
    frameReady = pyqtSignal(QImage)

    def __init__(self, cam_index: int = 0, parent=None):
        super().__init__(parent)
        self._idx = cam_index
        self._cap = None
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._grab)
        self.open(self._idx)
        # coeficientes foco = a·Z+b   (definidos pelo diálogo)
        self._a = 0.0
        self._b = 0.0
        self._auto_enabled = True

    # ----------------------------------------------------------
    def open(self, idx: int):
        self.close()
        self._idx = idx
        self._cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW if sys.platform.startswith("win") else 0)
        if self._cap.isOpened():
            self._timer.start(30)      # ~33 fps máx
            # tenta deixar o foco em modo manual
            self._cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
        else:
            self._timer.stop()

    # -------------- foco manual -----------------------------------
    def set_focus(self, value: int):
        """Define foco manual.  Range expandido 0-1023; converte se driver
           limitar a 0-255.  Desliga AF toda vez para garantir efeito."""
        if self._cap is None:
            return
        # força AF = OFF
        self._cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
        # descobre faixa aceita
        ok   = self._cap.set(cv2.CAP_PROP_FOCUS, int(value))
        if not ok:                       # talvez range 0-255
            val255 = int(value*255/1023)
            self._cap.set(cv2.CAP_PROP_FOCUS, val255)

    # chamada periódica pelo controlador
    def auto_focus(self, z_pulses: int):
        if not self._auto_enabled:
            return
        if self._a == 0.0 and self._b == 0.0:
            return                       # não calibrado
        foc = int(self._a * z_pulses + self._b)
        foc = max(0, min(foc, 1023))
        self.set_focus(foc)

    def load_calibration(self, a: float, b: float):
        self._a, self._b = a, b

    # -------------- liga / desliga auto-focus --------------------
    @property
    def auto_enabled(self) -> bool:
        return self._auto_enabled

    def enable_auto_focus(self, enabled: bool):
        self._auto_enabled = enabled

    def save_calibration(self):
        return {"a": self._a, "b": self._b}

    def close(self):
        self._timer.stop()
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    # ----------------------------------------------------------
    def _grab(self):
        if self._cap is None: return
        ok, frame = self._cap.read()
        if not ok: return
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, _ = frame.shape
        img = QImage(frame.data, w, h, QImage.Format.Format_RGB888)
        self.frameReady.emit(img)
