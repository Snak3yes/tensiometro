from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QLabel

def _make_box(title: str, text: str) -> QGroupBox:
    box = QGroupBox(title)
    v = QVBoxLayout(box)
    lab = QLabel(text); lab.setWordWrap(True)
    v.addWidget(lab)
    v.addStretch()
    return box

# Place-holders – serão substituídos por UI completa depois
from barcode_config_widget import BarcodeConfigWidget
InspectConfigWidget  = lambda: _make_box("Config. Inspeção",
                                         "Configurações de inspeção visual\n(a implementar)")
# ‘Fiducial’ agora é widget real – importado abaixo
from fiducial_config_widget import FiducialConfigWidget