# config_dialogs.py
from PyQt6.QtWidgets import (
    QDialog, QGridLayout, QLabel, QSpinBox, QPushButton, QHBoxLayout
)


class WorkAreaConfigDialog(QDialog):
    """
    Diálogo modal para ajustar os limites de X e Y de cada mesa.
    Só permite valores positivos em pulsos.
    """
    def __init__(self, limits: dict[int, dict[str, tuple[int, int]]], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Limites de Mesa")
        self._orig_limits = limits
        self._build_ui()

    # --------------------------- UI ------------------------------
    def _build_ui(self):
        g = QGridLayout(self)

        row = 0
        self._spins = {}      # {(mesa, eixo, kind): QSpinBox}
        for mesa in (1, 2):
            g.addWidget(QLabel(f"Mesa {mesa}"), row, 0, 1, 3)
            row += 1
            for eixo in ('x', 'y'):
                lim_min, lim_max = self._orig_limits[mesa][eixo]

                g.addWidget(QLabel(f"{eixo.upper()} mín:"), row, 0)
                sp_min = QSpinBox(); sp_min.setRange(0, 2_147_483_647)
                sp_min.setValue(lim_min)
                g.addWidget(sp_min, row, 1)

                g.addWidget(QLabel("máx:"), row, 2)
                sp_max = QSpinBox(); sp_max.setRange(1, 2_147_483_647)
                sp_max.setValue(lim_max)
                g.addWidget(sp_max, row, 3)

                self._spins[(mesa, eixo, 'min')] = sp_min
                self._spins[(mesa, eixo, 'max')] = sp_max
                row += 1

        # botão OK / Cancelar
        h = QHBoxLayout()
        ok  = QPushButton("OK");     ok.clicked.connect(self.accept)
        can = QPushButton("Cancelar"); can.clicked.connect(self.reject)
        h.addStretch(); h.addWidget(ok); h.addWidget(can)
        g.addLayout(h, row, 0, 1, 4)

    # --------------------------- API -----------------------------
    def get_limits(self) -> dict[int, dict[str, tuple[int, int]]]:
        """Devolve novo dicionário igual ao recebido mas com máx alterado."""
        new = {1: {}, 2: {}}
        for mesa in (1, 2):
            for eixo in ('x', 'y'):
                vmin = self._spins[(mesa, eixo, 'min')].value()
                vmax = self._spins[(mesa, eixo, 'max')].value()
                if vmax <= vmin:          # correção simples
                    vmax = vmin + 1
                new[mesa][eixo] = (vmin, vmax)
        return new
