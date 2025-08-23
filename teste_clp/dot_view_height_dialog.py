from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QSpinBox, QPushButton
)
from PyQt6.QtCore import Qt

class DotViewHeightDialog(QDialog):
    """
    Diálogo para configurar a altura de visualização de pontos 'dot'.
    """
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Window)
        self.setWindowTitle("Altura de Visualização Dot")
        self.setWindowModality(Qt.WindowModality.NonModal)
        self._ctrl = parent
        self._build_ui()

    def _build_ui(self):
        v = QVBoxLayout(self)
        # linha de edição
        h = QHBoxLayout()
        lbl = QLabel("Altura de visualização (Z):")
        self.spin = QSpinBox()
        # defina limites compatíveis com seu sistema (pulsos ou mm)
        self.spin.setRange(0, 100000)
        h.addWidget(lbl)
        h.addWidget(self.spin)
        v.addLayout(h)

        # botão Salvar
        btn_save = QPushButton("Salvar")
        btn_save.clicked.connect(self._on_save)
        v.addWidget(btn_save, alignment=Qt.AlignmentFlag.AlignRight)

    def _on_save(self):
        # persiste no settings.json
        val = self.spin.value()
        s = self._ctrl.settings
        s.data["dot_view_height"] = val
        s.save()
        self._ctrl.log(f"■ Altura de visualização de Dot salva: Z={val}")
        self.close()