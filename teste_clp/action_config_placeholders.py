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
from inspection_config_widget import InspectionConfigWidget
from fiducial_config_widget import FiducialConfigWidget