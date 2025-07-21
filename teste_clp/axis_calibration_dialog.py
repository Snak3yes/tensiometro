"""
axis_calibration_dialog.py
--------------------------
Diálogo modal que reutiliza CalibWidget (de cnc_calibration_widget.py)
e permite escolher qual eixo X/Y2/Y1/Z será calibrado.
"""
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QComboBox, QLabel, QPushButton, \
                            QHBoxLayout
from cnc_calibration_widget import CalibWidget

AXES = ("X", "Y2", "Y1", "Z")

class _BackendAdapter:
    """
    Implementa CalibrationBackend e redireciona apply_steps_per_mm(...)
    para o controlador principal, fixando o eixo escolhido.
    """
    def __init__(self, controller, axis: str):
        self._c = controller
        self._axis = axis
    # protocolo ------------------
    def apply_steps_per_mm(self, steps: float) -> bool:
        self._c._set_axis_steps(self._axis, steps)
        return True

class AxisCalibrationDialog(QDialog):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Calibração de Eixos")
        self._c = controller
        self._build_ui()

    # --------------------------- UI ---------------------------------
    def _build_ui(self):
        v = QVBoxLayout(self)
        # seleção de eixo
        hsel = QHBoxLayout()
        hsel.addWidget(QLabel("Eixo:"))
        self.cmb_axis = QComboBox()
        self.cmb_axis.addItems(AXES)
        hsel.addWidget(self.cmb_axis); hsel.addStretch()
        v.addLayout(hsel)

        # widget de calibração (backend definido depois)
        self.calib_widget = CalibWidget(None)   # backend placeholder
        v.addWidget(self.calib_widget)

        # botões OK / Fechar
        bok = QPushButton("Fechar")
        bok.clicked.connect(self.accept)
        h = QHBoxLayout(); h.addStretch(); h.addWidget(bok)
        v.addLayout(h)

        # sinais
        self.cmb_axis.currentTextChanged.connect(self._on_axis_changed)
        self._on_axis_changed(self.cmb_axis.currentText())

    # --------------------------- handlers ---------------------------
    def _on_axis_changed(self, axis: str):
        # troca backend para refletir eixo actual
        self.calib_widget._backend = _BackendAdapter(self._c, axis)
        # mostra passos/mm atuais
        cur = self._c.steps_per_mm.get(axis, 1.0)
        self.calib_widget.lbl_result.setText(f"{cur:.3f} steps/mm (atual)")
