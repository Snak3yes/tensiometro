# movement_controls_widget.py
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QDoubleValidator
from PyQt6.QtWidgets import (
    QWidget, QGroupBox, QGridLayout, QPushButton, QHBoxLayout,
    QLabel, QLineEdit, QVBoxLayout, QCheckBox, QMessageBox
)


class MovementControlsWidget(QWidget):
    """
    Painel com todos os controles de movimentação manual da CNC.
    A aplicação hospedeira conecta os sinais abaixo aos métodos do
    driver de movimento via CLP (Modbus TCP).

    Sinais:
        stepMoveRequested(axis, distance, feed)    – G90 (passo-a-passo)
        jogStart(axis, direction, feed)            – G91 pressionado
        jogStop()                                  – soltar botão em G91
        goToZeroRequested()
        emergencyStopToggled(engaged: bool)        – STOP / RESET
    """

    stepMoveRequested      = pyqtSignal(str, float, float)
    jogStart               = pyqtSignal(str, int, float)
    jogStop                = pyqtSignal()
    goToZeroRequested      = pyqtSignal()
    emergencyStopToggled   = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    # ------------------------------------------------------------------
    # interface pública
    # ------------------------------------------------------------------
    def feed_rate(self) -> float:
        """Retorna o feed-rate atual (mm/min)."""
        try:
            return float(self.ed_feed.text())
        except ValueError:
            return 1000.0

    def step_size(self) -> float:
        """Retorna o step size atual (mm)."""
        try:
            return float(self.ed_step.text())
        except ValueError:
            return 1.0

    # ------------------------------------------------------------------
    # construção da UI
    # ------------------------------------------------------------------
    def _build_ui(self):
        outer = QVBoxLayout(self)

        grp = QGroupBox("Movement Controls")
        grid = QGridLayout(grp)
        self.grid = grid

        # ------------------ botões direcionais -------------------------
        # Y2
        self.btn_up    = QPushButton("Y2+")   # Y2 +
        self.btn_down  = QPushButton("Y2-")   # Y2 –
        # X
        self.btn_left  = QPushButton("X-")   # X –
        self.btn_right = QPushButton("X+")   # X +
        # Y1
        self.btn_y1_up   = QPushButton("Y1+")   # Y1 +
        self.btn_y1_down = QPushButton("Y1-")   # Y1 –
        for b in (self.btn_up, self.btn_down, self.btn_left, self.btn_right, self.btn_y1_up, self.btn_y1_down):
            b.setMinimumSize(50, 50)
            f = QFont(); f.setPointSize(16); f.setBold(True); b.setFont(f)

        # LAYOUT
        # col0  col1  col2  col3  col4
        #  ─     Y2+  Y1+    ─     Z–
        #  X-    STOP  X+   (v)    ( )
        #  ─     Y2-  Y1-    ─     Z+
        grid.addWidget(self.btn_up,       0, 1)   # Y2+
        grid.addWidget(self.btn_y1_up,    0, 2)   # Y1+

        grid.addWidget(self.btn_left,     1, 0)   # X-
        grid.addWidget(self.btn_right,    1, 3)   # X+

        grid.addWidget(self.btn_down,     2, 1)   # Y2-
        grid.addWidget(self.btn_y1_down,  2, 2)   # Y1-

        # ------------------ Z +/– --------------------------------------
        # ------------------ Z +/– --------------------------------------
        # Origem em cima, positivo para baixo  →  Z– em cima, Z+ em baixo
        self.btn_z_up   = QPushButton("Z-")   # sobe
        self.btn_z_down = QPushButton("Z+")   # desce
        for b in (self.btn_z_up, self.btn_z_down):
            b.setMinimumSize(50, 50)
            f = QFont(); f.setPointSize(16); f.setBold(True); b.setFont(f)

        grid.addWidget(self.btn_z_up,   0, 4)   # Z-  (coluna 4)
        grid.addWidget(self.btn_z_down, 2, 4)   # Z+  (coluna 4)

        # ------------------ STOP / RESET -------------------------------
        self.btn_stop = QPushButton("STOP")
        self.btn_stop.setCheckable(True)
        self.btn_stop.setMinimumSize(90, 40)
        f = QFont(); f.setBold(True); self.btn_stop.setFont(f)
        self._set_stop_style(False)
        grid.addWidget(self.btn_stop, 1, 1, 1, 2, Qt.AlignmentFlag.AlignCenter)

        # ------------------ step size & feed rate ----------------------
        self.ed_step = QLineEdit("10")
        self.ed_feed = QLineEdit("1000")
        self.ed_step.setValidator(QDoubleValidator(0.001, 100000, 4, self))
        self.ed_feed.setValidator(QDoubleValidator(1, 30000, 0, self))

        h_step = QHBoxLayout()
        h_step.addWidget(QLabel("Step size:"))
        h_step.addWidget(self.ed_step)
        h_step.addWidget(QLabel("mm"))
        grid.addLayout(h_step, 3, 0, 1, 3)

        h_feed = QHBoxLayout()
        h_feed.addWidget(QLabel("Feed rate:"))
        h_feed.addWidget(self.ed_feed)
        h_feed.addWidget(QLabel("mm/min"))
        grid.addLayout(h_feed, 4, 0, 1, 3)

        # ------------------ modos de distância -------------------------
        h_mode = QHBoxLayout()
        self.btn_abs = QPushButton("(Passo)")
        self.btn_rel = QPushButton("(Contínuo)")
        self.btn_abs.setCheckable(True)
        self.btn_rel.setCheckable(True)
        self.btn_rel.setChecked(True)
        h_mode.addWidget(self.btn_abs); h_mode.addWidget(self.btn_rel)
        grid.addLayout(h_mode, 5, 0, 1, 3)

        # ------------------ Go to Zero ---------------------------------
        self.btn_gotozero = QPushButton("Go to Zero")
        self.btn_gotozero.setMinimumHeight(32)
        fz = QFont(); fz.setBold(True)
        self.btn_gotozero.setFont(fz)
        grid.addWidget(self.btn_gotozero, 6, 0, 1, 3)

        # ---------------------------------------------------------------
        #  NOVO: “Posição Atual” encaixado no espaço em branco (col-4)
        #  A grade fica: col-0..4 já usados; criamos col-5 só p/ leitura
        # ---------------------------------------------------------------
        self.lbl_pos_x  = QLabel("0");  self.lbl_pos_y2 = QLabel("0")
        self.lbl_pos_y1 = QLabel("0");  self.lbl_pos_z  = QLabel("0")
        for lab in (self.lbl_pos_x, self.lbl_pos_y2,
                    self.lbl_pos_y1, self.lbl_pos_z):
            lab.setAlignment(Qt.AlignmentFlag.AlignRight)
            lab.setMinimumWidth(60)
            lab.setStyleSheet("QLabel { background:gray; padding:1px; }")

        grid.setColumnStretch(5, 1)          # assegura 6.ª coluna

        # grid.addWidget(QLabel("<b>Posição</b>"), 0, 5, Qt.AlignmentFlag.AlignCenter)
        grid.addWidget(QLabel("X:"), 3, 3, Qt.AlignmentFlag.AlignRight)
        grid.addWidget(self.lbl_pos_x, 3, 4, Qt.AlignmentFlag.AlignRight)
        grid.addWidget(QLabel("Y2:"), 4, 3, Qt.AlignmentFlag.AlignRight)
        grid.addWidget(self.lbl_pos_y2, 4, 4, Qt.AlignmentFlag.AlignRight)
        grid.addWidget(QLabel("Y1:"), 5, 3, Qt.AlignmentFlag.AlignRight)
        grid.addWidget(self.lbl_pos_y1, 5, 4, Qt.AlignmentFlag.AlignRight)
        grid.addWidget(QLabel("Z:"), 6, 3, Qt.AlignmentFlag.AlignRight)
        grid.addWidget(self.lbl_pos_z, 6, 4, Qt.AlignmentFlag.AlignRight)

        # ------------------ finais -------------------------------------
        outer.addWidget(grp)
        outer.addStretch()

        # ligações
        self._connect_signals()

    # ------------------------ API pública -----------------------------
    def update_position(self, *, x: int, y2: int, y1: int, z: int):
        self.lbl_pos_x.setText(str(x))
        self.lbl_pos_y2.setText(str(y2))
        self.lbl_pos_y1.setText(str(y1))
        self.lbl_pos_z.setText(str(z))

    # ------------------------------------------------------------------
    # sinais internos → sinais públicos
    # ------------------------------------------------------------------
    def _connect_signals(self):

        # press / release – X e Y
        self.btn_up.pressed.connect(   lambda: self._direction_press("Y2", +1))
        self.btn_down.pressed.connect( lambda: self._direction_press("Y2", -1))
        self.btn_left.pressed.connect( lambda: self._direction_press("X", -1))
        self.btn_right.pressed.connect(lambda: self._direction_press("X", +1))

        # Y1
        self.btn_y1_up.pressed.connect(  lambda: self._direction_press("Y1", +1))
        self.btn_y1_down.pressed.connect(lambda: self._direction_press("Y1", -1))

        for b in (self.btn_up, self.btn_down, self.btn_left, self.btn_right, self.btn_y1_up, self.btn_y1_down):
            b.released.connect(self._direction_release)

        # press / release – Z   (atenção: sentidos trocados)
        self.btn_z_up.pressed.connect(  lambda: self._direction_press("Z", -1))  # Z-
        self.btn_z_down.pressed.connect(lambda: self._direction_press("Z", +1))  # Z+
        self.btn_z_up.released.connect(self._direction_release)
        self.btn_z_down.released.connect(self._direction_release)

        # STOP / RESET
        self.btn_stop.toggled.connect(self._on_stop_toggled)

        # Go to Zero
        self.btn_gotozero.clicked.connect(self.goToZeroRequested)

        # troca de modo
        self.btn_abs.clicked.connect(lambda: self._set_mode(True))
        self.btn_rel.clicked.connect(lambda: self._set_mode(False))

    # ------------------------------------------------------------------
    # handlers
    # ------------------------------------------------------------------
    def _direction_press(self, axis: str, direction: int):
        feed = self.feed_rate()
        if self.btn_abs.isChecked():           # G90 – passo / step
            distance = self.step_size() * direction
            self.stepMoveRequested.emit(axis, distance, feed)
        else:                                  # G91 – jog contínuo
            self.jogStart.emit(axis, direction, feed)

    def _direction_release(self):
        if self.btn_rel.isChecked():
            self.jogStop.emit()

    def _on_stop_toggled(self, engaged: bool):
        self._set_stop_style(engaged)
        self.emergencyStopToggled.emit(engaged)

    def _set_stop_style(self, engaged: bool):
        if engaged:   # RESET
            self.btn_stop.setText("RESET")
            self.btn_stop.setStyleSheet("background: orange; color: black;")
        else:         # STOP
            self.btn_stop.setText("STOP")
            self.btn_stop.setStyleSheet("background: red; color: white;")

    def _set_mode(self, absolute: bool):
        self.btn_abs.setChecked(absolute)
        self.btn_rel.setChecked(not absolute)

        # feedback optional (beep).  Se desejar avisar o usuário
        # QMessageBox.information(self, "Modo", "G90 selecionado" if absolute else "G91 selecionado")


# ----------------------------------------------------------------------
# Demonstração isolada
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    w = MovementControlsWidget()
    w.resize(350, 320)
    w.show()

    # Liga sinais a prints no console
    w.stepMoveRequested.connect(
        lambda ax, dist, f: print(f"[step] {ax} {dist}mm  F{f}")
    )
    w.jogStart.connect(
        lambda ax, dir, f: print(f"[jog]  {ax} dir={dir}  F{f}")
    )
    w.jogStop.connect(lambda: print("[jog]  stop"))
    w.emergencyStopToggled.connect(
        lambda engaged: print("STOP ->", "ENGAGED" if engaged else "released")
    )
    w.goToZeroRequested.connect(lambda: print("[cmd] G0 X0 Y0 Z0"))

    sys.exit(app.exec())
