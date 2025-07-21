# position_status_widget.py
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QWidget, QGroupBox, QLabel, QPushButton, QGridLayout, QVBoxLayout
)
from PyQt6.QtGui import QFont


class PositionStatusWidget(QWidget):
    """
    Widget que exibe a posição atual dos eixos, o estado da máquina
    e oferece botões para zerar X, Y, Z ou todos os eixos de uma vez.
    """

    # Sinais ─ a aplicação hospedeira deve conectá-los ao driver CNC
    zeroAllRequested = pyqtSignal()
    zeroXRequested   = pyqtSignal()
    zeroY2Requested  = pyqtSignal()
    zeroY1Requested  = pyqtSignal()
    zeroZRequested   = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    # ------------------------------------------------------------------
    # API pública para a aplicação hospedeira atualizar dados do widget
    # ------------------------------------------------------------------
    def update_position(self, x=0, y2=0, y1=0, z=0):
        """Atualiza as labels de posição (valores em pulsos)."""
        self.lbl_x.setText(str(x))
        self.lbl_y2.setText(str(y2))
        self.lbl_y1.setText(str(y1))
        self.lbl_z.setText(str(z))

    def update_status(self, status: str):
        """Atualiza o label de status da máquina (Idle, Run, Jog…)."""
        self.lbl_status.setText(status)

    # ------------------------------------------------------------------
    # Construção da interface
    # ------------------------------------------------------------------
    def _build_ui(self):
        outer = QVBoxLayout(self)

        grp = QGroupBox("Posição Atual (pulsos)")
        grid = QGridLayout(grp)

        font_values = QFont()
        font_values.setBold(True)

        # ----- eixo X ---------------------------------------------------
        grid.addWidget(QLabel("X:"), 0, 0)
        self.lbl_x = QLabel("0")
        self.lbl_x.setFont(font_values)
        grid.addWidget(self.lbl_x, 0, 1)

        # ----- eixo Y2 --------------------------------------------------
        grid.addWidget(QLabel("Y2:"), 1, 0)
        self.lbl_y2 = QLabel("0")
        self.lbl_y2.setFont(font_values)
        grid.addWidget(self.lbl_y2, 1, 1)

        # ----- eixo Y1 --------------------------------------------------
        grid.addWidget(QLabel("Y1:"), 2, 0)
        self.lbl_y1 = QLabel("0")
        self.lbl_y1.setFont(font_values)
        grid.addWidget(self.lbl_y1, 2, 1)

        # ----- eixo Z ---------------------------------------------------
        grid.addWidget(QLabel("Z:"), 3, 0)
        self.lbl_z = QLabel("0")
        self.lbl_z.setFont(font_values)
        grid.addWidget(self.lbl_z, 3, 1)

        # ----- status ---------------------------------------------------
        grid.addWidget(QLabel("Status:"), 4, 0)
        self.lbl_status = QLabel("Desconectado")
        grid.addWidget(self.lbl_status, 4, 1)

        outer.addWidget(grp)
        outer.addStretch()

# ----------------------------------------------------------------------
# Demo rápido: executa o widget numa janela isolada
# ----------------------------------------------------------------------
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys, random, time

    app = QApplication(sys.argv)
    w = PositionStatusWidget()
    w.resize(250, 200)
    w.show()

    # Simula atualização de posição/status a cada 500 ms
    from PyQt6.QtCore import QTimer
    def _simulate():
        w.update_position(
            x=random.uniform(0, 100),
            y=random.uniform(0, 100),
            z=random.uniform(0, 50)
        )
        w.update_status(random.choice(["Idle", "Run", "Jog"]))
    QTimer.singleShot(0, _simulate)
    timer = QTimer()
    timer.timeout.connect(_simulate)
    timer.start(500)

    sys.exit(app.exec())
