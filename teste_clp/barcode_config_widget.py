"""
barcode_config_widget.py
------------------------
Configuração de leitura de código de barras / QR.
"""
from PyQt6.QtWidgets import (
    QGroupBox, QVBoxLayout, QFormLayout, QSpinBox, QPushButton,
    QLabel, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
import cv2
from barcode_scanner import BarcodeScanner


class BarcodeConfigWidget(QGroupBox):
    parametersChanged = pyqtSignal(int, int)  # width, height
    testFinished      = pyqtSignal(bool, int, int, int, int)  # ok,x,y,w,h
    def __init__(self, controller, parent=None):
        super().__init__("Config. Barcode", parent)
        self._c = controller
        self._scanner = BarcodeScanner()
        self._build_ui()

    def _build_ui(self):
        v = QVBoxLayout(self)
        form = QFormLayout()
        self.spin_w = QSpinBox(); self.spin_w.setRange(20, 2000); self.spin_w.setValue(400)
        self.spin_h = QSpinBox(); self.spin_h.setRange(20, 2000); self.spin_h.setValue(150)
        form.addRow("Largura (px):",  self.spin_w)
        form.addRow("Altura  (px):",  self.spin_h)
        v.addLayout(form)
        btn_test = QPushButton("Testar Leitura")
        v.addWidget(btn_test)
        self.lbl_result = QLabel("—")
        self.lbl_result.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_result.setStyleSheet("QLabel { background:#ECEFF1; padding:4px; }")
        v.addWidget(self.lbl_result)
        v.addStretch()
        # sinais
        self.spin_w.valueChanged.connect(
            lambda _: self.parametersChanged.emit(self.spin_w.value(), self.spin_h.value()))
        self.spin_h.valueChanged.connect(
            lambda _: self.parametersChanged.emit(self.spin_w.value(), self.spin_h.value()))
        btn_test.clicked.connect(self._on_test)

    # --------------------- helpers ----------------------------
    def _grab_frame(self):
        cm = getattr(self._c, "camera_manager", None)
        if not cm or not getattr(cm, "_cap", None): return None
        ok, frame = cm._cap.read()
        return frame if ok else None

    def _on_test(self):
        frame = self._grab_frame()
        if frame is None:
            QMessageBox.warning(self, "Câmera", "Frame indisponível.")
            return
        h_img, w_img, _ = frame.shape
        ww = self.spin_w.value(); hh = self.spin_h.value()
        cx, cy = w_img // 2, h_img // 2
        x0 = max(0, cx - ww // 2); y0 = max(0, cy - hh // 2)
        roi = (x0, y0, ww, hh)
        results = self._scanner.scan(frame, roi=roi)
        if results:
            r = results[0]
            self.lbl_result.setStyleSheet("QLabel { background:#C8E6C9; padding:4px; }")
            self.lbl_result.setText(f"{r.type}: {r.data}")
            self.testFinished.emit(True, x0, y0, ww, hh)
        else:
            self.lbl_result.setStyleSheet("QLabel { background:#FFCDD2; padding:4px; }")
            self.lbl_result.setText("Nenhum código encontrado")
            self.testFinished.emit(False, x0, y0, ww, hh)

    # exportação p/ meta-dados
    def roi_size(self):
        return self.spin_w.value(), self.spin_h.value()