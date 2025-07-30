"""
fiducial_config_widget.py
-------------------------
Configuração de captura / teste de fiducial.
Depende do OpenCV já usado pelo CameraManager.
"""
import cv2, numpy as np
from PyQt6.QtWidgets import (
    QGroupBox, QVBoxLayout, QFormLayout, QSpinBox, QPushButton, QLabel,
    QHBoxLayout, QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal


class FiducialConfigWidget(QGroupBox):
    """
    Widget contendo:
        • Janela (px)         – lado do quadrado central
        • Raio de busca (px)  – ±pixels ao redor
        • Similaridade mínima (%)   – 70…100
        • Botões  Capturar  /  Testar
        • Label resultado
    Guarda internamente o template (numpy array BGR) no atributo
    self._template.
    """
    parametersChanged = pyqtSignal(int, int)         # window, radius
    matchTested       = pyqtSignal(float, bool, int, int, int, int)

    def __init__(self, controller, parent=None):
        super().__init__("Config. Fiducial", parent)
        self._c = controller
        self._template = None         # imagem capturada
        self._build_ui()

    # --------------------------------------------------------------
    def _build_ui(self):
        v = QVBoxLayout(self)
        form = QFormLayout()
        self.spin_window = QSpinBox(); self.spin_window.setRange(5, 500); self.spin_window.setValue(50)
        self.spin_radius = QSpinBox(); self.spin_radius.setRange(0, 1000); self.spin_radius.setValue(80)
        self.spin_thresh = QSpinBox(); self.spin_thresh.setRange(50, 100); self.spin_thresh.setValue(80)
        form.addRow("Janela (px):",  self.spin_window)
        form.addRow("Raio busca (px):", self.spin_radius)
        form.addRow("Similaridade mínima (%):", self.spin_thresh)
        v.addLayout(form)

        h = QHBoxLayout()
        btn_cap  = QPushButton("Capturar Fiducial")
        btn_test = QPushButton("Testar")
        h.addWidget(btn_cap); h.addWidget(btn_test)
        v.addLayout(h)

        # -------- visores de imagens (template | match) --------------
        img_row = QHBoxLayout()
        self.lbl_templ = QLabel("Template")
        self.lbl_match = QLabel("Match")
        for lab in (self.lbl_templ, self.lbl_match):
            lab.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lab.setSizePolicy(QSizePolicy.Policy.Preferred,
                              QSizePolicy.Policy.Preferred)
            lab.setStyleSheet("QLabel { background:#263238; color:#CFD8DC; }")
        img_row.addWidget(self.lbl_templ); img_row.addWidget(self.lbl_match)
        v.addLayout(img_row)

        self.lbl_result = QLabel("—")
        self.lbl_result.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_result.setStyleSheet("QLabel { background:#ECEFF1; padding:4px; }")
        v.addWidget(self.lbl_result)
        v.addStretch()

        # sinais
        btn_cap.clicked.connect(self._on_capture)
        btn_test.clicked.connect(self._on_test)

        # emite alteração de parâmetros
        self.spin_window.valueChanged.connect(
            lambda _: self.parametersChanged.emit(self.spin_window.value(),
                                                  self.spin_radius.value()))
        self.spin_radius.valueChanged.connect(
            lambda _: self.parametersChanged.emit(self.spin_window.value(),
                                                  self.spin_radius.value()))
              
    # -------------- NOVO ------------------------------------------
    def load_from_meta(self, meta: dict):
        self.spin_window.setValue(int(meta.get("window", 50)))
        self.spin_radius.setValue(int(meta.get("radius", 80)))
        self.spin_thresh.setValue(int(meta.get("threshold", 70)))
        # template já está contido em meta; não há necessidade de
        # repor a imagem aqui.

    # --------------------------------------------------------------
    def _grab_frame(self):
        """Obtém o último frame RGB da CameraManager."""
        if not hasattr(self._c, "camera_manager"): return None
        cm = self._c.camera_manager
        # usa método interno _cap para pegar diretamente
        cap = getattr(cm, "_cap", None)
        if cap is None or not cap.isOpened():
            return None
        ok, frame = cap.read()
        return frame if ok else None

    def _on_capture(self):
        frame = self._grab_frame()
        if frame is None:
            QMessageBox.warning(self, "Câmera", "Frame indisponível.")
            return
        h, w, _ = frame.shape
        sz = self.spin_window.value()
        cx, cy = w // 2, h // 2
        x0 = max(0, cx - sz // 2)
        y0 = max(0, cy - sz // 2)
        roi = frame[y0:y0 + sz, x0:x0 + sz].copy()
        if roi.size == 0:
            QMessageBox.warning(self, "Erro", "ROI vazia.")
            return
        self._template_bgr = roi        # salvo p/ persistir depois
        self._template    = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        self.lbl_result.setText(f"Template capturado ({sz}×{sz}px)")
        self._show_pixmap(self.lbl_templ, roi)

    def _on_test(self):
        if self._template is None:
            QMessageBox.information(self, "Template", "Capture o fiducial primeiro.")
            return
        frame = self._grab_frame()
        if frame is None:
            QMessageBox.warning(self, "Câmera", "Frame indisponível.")
            return
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        res = cv2.matchTemplate(gray, self._template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        similarity = max_val * 100
        th = self.spin_thresh.value()

        # ------------ verifica raio de busca -------------------------
        win = self.spin_window.value()
        rad = self.spin_radius.value()
        cx, cy = gray.shape[1] // 2, gray.shape[0] // 2
        tx, ty = max_loc                      # canto superior-esquerdo
        mx = tx + self._template.shape[1] // 2
        my = ty + self._template.shape[0] // 2
        in_radius = (abs(mx - cx) <= rad) and (abs(my - cy) <= rad)
        # prepara sub-imagem do local encontrado para mostrar
        tx, ty = max_loc
        w0, h0 = self._template.shape[1], self._template.shape[0]
        sub = frame[ty:ty+h0, tx:tx+w0].copy()
        self._last_match_bgr = sub       # salvo p/ persistir depois
        ok_match = (similarity >= th) and in_radius

        if not ok_match:
            self.lbl_result.setStyleSheet("QLabel { background:#FFCDD2; }")
            # mensagem: mostra se falhou por limite ou por similaridade
            msg = (f"Fora do raio  (Δx={mx-cx}  Δy={my-cy})"
                   if similarity >= th else
                   f"{similarity:.1f}%  (<{th}%)")
            self.lbl_result.setText(f"Falhou: {msg}")
            self.matchTested.emit(similarity, False,
                                  tx, ty,
                                  self._template.shape[1],
                                  self._template.shape[0])
        else:
            
            cx, cy = gray.shape[1]//2, gray.shape[0]//2
            dx = tx + self._template.shape[1]//2 - cx
            dy = ty + self._template.shape[0]//2 - cy
            self.lbl_result.setStyleSheet("QLabel { background:#C8E6C9; }")
            self.lbl_result.setText(f"OK {similarity:.1f}%  Δx={dx}  Δy={dy}")
            self.matchTested.emit(similarity, True,
                                  tx, ty,
                                  self._template.shape[1],
                                  self._template.shape[0])
            
        # mostra sub-imagem com borda colorida
        brd_color = (0,255,0) if ok_match else (0,0,255)
        sub_brd = cv2.copyMakeBorder(sub, 2,2,2,2, cv2.BORDER_CONSTANT, value=brd_color)
        self._show_pixmap(self.lbl_match, sub_brd)

    # --------------------------------------------------------------
    # utilitário para mostrar numpy BGR em QLabel mantendo largura
    # --------------------------------------------------------------
    def _show_pixmap(self, label: QLabel, img_bgr):
        h, w, _ = img_bgr.shape
        # converte para QPixmap
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        from PyQt6.QtGui import QImage, QPixmap
        qimg = QImage(
            img_rgb.data, w, h, 3 * w,              # bytesPerLine = 3*w
            QImage.Format.Format_RGB888
        )
        px = QPixmap.fromImage(qimg)
        # largura = largura do botão Capturar (aprox.)
        btn_width = label.parent().findChild(QPushButton, "Capturar Fiducial")
        max_w = btn_width.width() if btn_width else 120
        px = px.scaledToWidth(max_w, Qt.TransformationMode.SmoothTransformation)
        label.setPixmap(px)

    # --------------------------------------------------------------
    #  Métodos auxiliares para exportar imagens (futuro save)
    # --------------------------------------------------------------
    def template_image(self):
        """Devolve numpy array BGR do template ou None."""
        return getattr(self, "_template_bgr", None)

    def last_match_image(self):
        """Devolve numpy array BGR do último match ou None."""
        return getattr(self, "_last_match_bgr", None)