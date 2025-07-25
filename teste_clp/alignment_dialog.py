from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal


class AlignmentDialog(QDialog):
    """
    Passo-a-passo para medir o deslocamento entre
    o centro da CÂMERA e o centro do NOZZLE.

    1. Leve o NOZZLE manualmente até um ponto de referência e clique
       “Capturar bico”.
    2. Leve a CÂMERA (centro da imagem) ao MESMO ponto e clique
       “Capturar câmera”.
    O diálogo calcula ΔX, ΔY e salva.
    """

    offsetSaved = pyqtSignal(dict)     # {'x':dx, 'y':dy}

    def __init__(self, ctrl, parent=None):
        super().__init__(parent, Qt.WindowType.Window)
        self.setWindowTitle("Alinhamento Nozzle ↔ Câmera")
        self.setWindowModality(Qt.WindowModality.NonModal)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)

        self._c = ctrl
        self._noz_pos = None   # (x,y)
        self._cam_pos = None

        self._build_ui()

    # ---------------- UI -----------------
    def _build_ui(self):
        v = QVBoxLayout(self)
        v.addWidget(QLabel(
            "1. Posicione o BICO sobre um ponto fixo e clique em "
            "<b>Capturar bico</b>.\n"
            "2. Mova a CÂMERA até o MESMO ponto (use o clique na imagem) "
            "e clique em <b>Capturar câmera</b>.\n"
            "3. Clique <b>Salvar</b> para gravar o offset."))

        # linha status
        self.lbl_status = QLabel("ΔX = 0   ΔY = 0")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(self.lbl_status)

        h1 = QHBoxLayout()
        self.btn_noz = QPushButton("Capturar bico")
        self.btn_cam = QPushButton("Capturar câmera")
        h1.addWidget(self.btn_noz)
        h1.addWidget(self.btn_cam)
        v.addLayout(h1)

        h2 = QHBoxLayout()
        btn_save = QPushButton("Salvar")
        btn_cancel = QPushButton("Fechar")
        h2.addStretch()
        h2.addWidget(btn_save)
        h2.addWidget(btn_cancel)
        v.addLayout(h2)

        # conexões
        self.btn_noz.clicked.connect(self._capture_nozzle)
        self.btn_cam.clicked.connect(self._capture_camera)
        btn_save.clicked.connect(self._on_save)
        btn_cancel.clicked.connect(self.close)

    # -------------- capturas ----------------
    def _capture_nozzle(self):
        self._noz_pos = (self._c.current_positions['X'],
                         self._c.current_positions['Y1'  # Y física da Mesa 1
                             if self._c.tab_widget.currentWidget() is self._c.mesa_tabs[1]
                             else 'Y2'])
        self._update_status()

    def _capture_camera(self):
        """
        Posição da CÂMERA é simplesmente a posição atual dos eixos,
        pois o usuário deve mover o cabeçote de forma que o ponto de
        interesse fique no centro da imagem.
        """
        self._cam_pos = (self._c.current_positions['X'],
                         self._c.current_positions['Y1'
                             if self._c.tab_widget.currentWidget() is self._c.mesa_tabs[1]
                             else 'Y2'])
        self._update_status()

    def _update_status(self):
        if self._noz_pos and self._cam_pos:
            dx = self._cam_pos[0] - self._noz_pos[0]
            dy = self._cam_pos[1] - self._noz_pos[1]
            self.lbl_status.setText(f"ΔX = {dx}   ΔY = {dy}")
        else:
            self.lbl_status.setText("ΔX = ?   ΔY = ?")

    # -------------- salvar ------------------
    def _on_save(self):
        if not (self._noz_pos and self._cam_pos):
            QMessageBox.warning(self, "Incompleto",
                                "Capture as duas posições antes de salvar.")
            return
        dx = self._cam_pos[0] - self._noz_pos[0]
        dy = self._cam_pos[1] - self._noz_pos[1]
        self.offsetSaved.emit({"x": dx, "y": dy})
        self.close()
