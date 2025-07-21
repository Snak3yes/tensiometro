"""
virtual_home_dialog.py
----------------------
Diálogo para configurar o “homing virtual” (posição zero lógica)
de cada mesa.  Salva em settings.json.
"""
from PyQt6.QtWidgets import (
    QDialog, QGridLayout, QLabel, QSpinBox, QPushButton, QHBoxLayout
)
from PyQt6.QtCore import Qt, pyqtSignal

class ConfigHomeDialog(QDialog):
    """
    Janela NÃO modal (always-on-top) para configurar o zero virtual.
    Sinal:
        acceptedAndSaved()  – emitido quando o utilizador clica OK.
    """
    acceptedAndSaved = pyqtSignal()
    def __init__(self, controller, parent=None):
        # NON-MODAL + sempre à frente
        super().__init__(parent, Qt.WindowType.Window)
        self.setWindowModality(Qt.WindowModality.NonModal)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.setWindowTitle("Configuração de Homing Virtual")
        self._c = controller
        self._orig = controller.virtual_home
        self._build_ui()

    # ------------------------- UI ---------------------------------
    def _build_ui(self):
        g = QGridLayout(self)
        self._spins = {}   # (mesa, coord) -> spin
        row = 0
        for mesa in (1, 2):
            # título mesa
            g.addWidget(QLabel(f"<b>Mesa {mesa}</b>"), row, 0, 1, 5)
            row += 1
            # linha X
            g.addWidget(QLabel("X:"), row, 0)
            spx = QSpinBox(); spx.setRange(-2_147_483_648, 2_147_483_647)
            spx.setValue(self._orig[mesa]["x"])
            g.addWidget(spx, row, 1)
            # botões
            btn_cap = QPushButton("Capturar posição atual")
            btn_cap.clicked.connect(lambda _=False, m=mesa: self._capture(m))
            btn_go  = QPushButton("Ir para Home")
            btn_go.clicked.connect(lambda _=False, m=mesa: self._goto(m))
            g.addWidget(btn_cap, row, 2, 1, 2)
            g.addWidget(btn_go,  row, 4)
            self._spins[(mesa, 'x')] = spx
            row += 1
            # linha Y
            g.addWidget(QLabel("Y:"), row, 0)
            spy = QSpinBox(); spy.setRange(-2_147_483_648, 2_147_483_647)
            spy.setValue(self._orig[mesa]["y"])
            g.addWidget(spy, row, 1)
            self._spins[(mesa, 'y')] = spy
            row += 1
        # ------------------- OK / Cancel --------------------------
        h = QHBoxLayout()
        ok  = QPushButton("OK");     ok.clicked.connect(self._on_ok)
        can = QPushButton("Cancelar"); can.clicked.connect(self.hide)
        h.addStretch(); h.addWidget(ok); h.addWidget(can)
        g.addLayout(h, row, 0, 1, 4)

    # ------------------- handlers --------------------------------
    def _on_ok(self):
        self.acceptedAndSaved.emit()
        self.hide()

    # ------------------- helpers ---------------------------------
    def _capture(self, mesa:int):
        """Lê posição atual do controlador e copia para os campos."""
        x = self._c.current_positions['X']
        y = self._c.current_positions['Y1' if mesa == 1 else 'Y2']
        self._spins[(mesa,'x')].setValue(x)
        self._spins[(mesa,'y')].setValue(y)

    def _goto(self, mesa:int):
        """Move para o ponto configurado nos spinBoxes atuais."""
        x = self._spins[(mesa,'x')].value()
        y = self._spins[(mesa,'y')].value()
        dx = x - self._c.current_positions['X']
        y_axis = 'Y1' if mesa == 1 else 'Y2'
        dy = y - self._c.current_positions[y_axis]
        if dx: self._c.move_relative('X', dx)
        if dy: self._c.move_relative(y_axis, dy)

    # ------------------- saída -----------------------------------
    def get_home_dict(self) -> dict[int,dict[str,int]]:
        return {
            1: {"x": self._spins[(1,'x')].value(),
                "y": self._spins[(1,'y')].value()},
            2: {"x": self._spins[(2,'x')].value(),
                "y": self._spins[(2,'y')].value()}
        }