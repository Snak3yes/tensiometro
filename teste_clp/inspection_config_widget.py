from PyQt6.QtWidgets import (
    QGroupBox, QVBoxLayout, QFormLayout, QSpinBox, QPushButton,
    QLabel, QHBoxLayout, QSizePolicy, QDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
import cv2

# ------------------------------------------------------------------
#  Diálogo auxiliar em 2 colunas  (80 % região | 20 % controles)
# ------------------------------------------------------------------
class _AuxDialog(QDialog):
    def __init__(self,
                 pix_region,            # QPixmap da região capturada
                 ctrl_widget,           # InspectionConfigWidget (controles)
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle("Auxiliar de Inspeção")
        self.setWindowModality(Qt.WindowModality.NonModal)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)

        # ---------- coluna esquerda: apenas imagem 4:3 ---------------
        self.lbl_big = QLabel()
        self.lbl_big.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_big.setStyleSheet("QLabel { background:#000; }")
        self.lbl_big.setSizePolicy(QSizePolicy.Policy.Expanding,
                                   QSizePolicy.Policy.Expanding)
        # guarda o pixmap original em alta resolução;  
        # todas as redimensões posteriores usarão esta cópia
        self._orig_pix = pix_region or QPixmap()
        self._update_pix()                 # primeira exibição

        # ---------- layout principal ---------------------------------
        from PyQt6.QtWidgets import QHBoxLayout
        h = QHBoxLayout(self)
        h.addWidget(self.lbl_big, 4)       # 80 %
        h.addWidget(ctrl_widget, 1)        # 20 %

        # Garante que o preview interno e o botão auxiliar não apareçam
        for attr in ("lbl_region", "btn_aux"):
            if hasattr(ctrl_widget, attr) and getattr(ctrl_widget, attr):
                getattr(ctrl_widget, attr).setVisible(False)

        # ------------------------------------------------------------------
        #  Sempre que o usuário clicar em “Definir região” no painel direito,
        #  o sinal regionCaptured(img_bgr) será emitido.  Conectamos para que
        #  o novo ROI substitua imediatamente a imagem exibida na coluna
        #  esquerda (“Região de Inspeção”).
        # ------------------------------------------------------------------
        if hasattr(ctrl_widget, "regionCaptured"):
            ctrl_widget.regionCaptured.connect(self._on_region_captured)
            # Actualiza também o visor da JANELA PRINCIPAL
            if parent is not None and hasattr(parent, "_apply_external_roi"):
                ctrl_widget.regionCaptured.connect(parent._apply_external_roi)

        # ROI capturado na janela PRINCIPAL deve reflectir aqui
        if parent is not None and hasattr(parent, "regionCaptured"):
            parent.regionCaptured.connect(self._on_region_captured)

    # ------------ helpers internos ----------------------------------
    def _update_pix(self):
        """Escala novamente a partir da imagem original (evita cascata)."""
        if self._orig_pix.isNull():
            return
        scaled = self._orig_pix.scaled(
            self.lbl_big.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation)
        self.lbl_big.setPixmap(scaled)
    
    # ------------ slot: novo ROI vindo do painel --------------------
    def _on_region_captured(self, img_bgr):
        """
        Recebe numpy BGR do widget de controle e actualiza o visor grande
        sem efeito “cascata”.
        """
        try:
            # converte utilizando o helper já existente
            self._orig_pix = InspectionConfigWidget._bgr_to_pixmap(img_bgr)
            self._update_pix()
        except Exception:
            pass      # ignora falhas de conversão

    # mantém proporção 4:3 na imagem grande
    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        w = self.lbl_big.width()
        h = int(w * 3 / 4)
        self.lbl_big.setFixedHeight(h)
        # redimensiona sempre a partir do pixmap original de alta qualidade
        self._update_pix()

# ------------------------------------------------------------------
#  QLabel com proporção fixa (default = 4:3)
# ------------------------------------------------------------------
class AspectRatioLabel(QLabel):
    """
    QLabel que mantém width : height = 4 : 3
    (ou outro aspecto definido no construtor).
    Usa o mecanismo height-for-width do Qt ‑ sem precisar de
    resizeEvent personalizado no widget contêiner.
    """
    def __init__(self, *args, aspect_ratio: float = 4/3, **kwargs):
        super().__init__(*args, **kwargs)
        self._aspect_ratio = aspect_ratio        # width / height
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Expanding)

    # ---- height-for-width ----------------------------------------
    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, w: int) -> int:
        return int(w / self._aspect_ratio)

    # sizeHint garante 4:3 quando o layout consulta o widget
    def sizeHint(self):
        hint = super().sizeHint()
        hint.setHeight(self.heightForWidth(hint.width()))
        return hint

# ------------------------------------------------------------------
#  InspectionConfigWidget
#  • show_region      → exibe/omite o visor grande na própria coluna
#  • show_aux_button  → exibe/omite o botão “Aux. de inspeção”
# ------------------------------------------------------------------
class InspectionConfigWidget(QGroupBox):
    """
    UI da Ação 'Inspeção'.
    """
    parametersChanged = pyqtSignal(int, int)       # width, height
    regionCaptured    = pyqtSignal(object)         # img_bgr

    def __init__(self, controller,
                 parent=None,
                 *,
                 show_region: bool = True,
                 show_aux_button: bool = True):
        super().__init__("Config. Inspeção", parent)
        self._c = controller
        self._show_region = show_region
        self._show_aux_button = show_aux_button
        self._template = None
        self._last_roi_bgr = None
        self._build_ui()

    # ---------------- construção ----------------------------
    def _build_ui(self):
        v = QVBoxLayout(self)

        form = QFormLayout()
        self._ratio = 4/3
        self._internal = False   # evita recursão ao sincronizar
        self.spin_w = QSpinBox(); self.spin_w.setRange(12, 4000); self.spin_w.setValue(400)
        self.spin_h = QSpinBox(); self.spin_h.setRange(9, 3000);  self.spin_h.setValue(int(400/ self._ratio))
        form.addRow("Largura (px):", self.spin_w)
        form.addRow("Altura  (px):", self.spin_h)
        v.addLayout(form)

        # botão capturar região
        self.btn_region = QPushButton("Definir região")
        v.addWidget(self.btn_region)

        # visor grande (4:3) – largura elástica, altura controlada
        self.lbl_region = AspectRatioLabel("Região")
        self._style_label(self.lbl_region)
        # já possui SizePolicy.Expanding|Expanding no construtor
        # exibe apenas se solicitado
        if self._show_region:
            v.addWidget(self.lbl_region)
        else:
            self.lbl_region.setVisible(False)

        # visor pequeno (ROI mecânico)
        # visor ROI menor (metade da largura, 4:3, centrado)
        self.lbl_roi = QLabel("ROI")
        self._style_label(self.lbl_roi)
        self.lbl_roi.setAlignment(
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        # largura controlada manualmente → Policy.Fixed evita “esticar”
        self.lbl_roi.setSizePolicy(QSizePolicy.Policy.Fixed,
                                   QSizePolicy.Policy.Fixed)
        v.addWidget(self.lbl_roi)
        # Garante que ambos os visores começam com a geometria correta
        self._update_roi_aspect()

        # similaridade + salvar
        hsim = QHBoxLayout()
        self.spin_sim = QSpinBox(); self.spin_sim.setRange(50, 100); self.spin_sim.setValue(95)
        hsim.addWidget(QLabel("Similaridade mínima %:"))
        hsim.addWidget(self.spin_sim)
        self.btn_save = QPushButton("Salvar")
        hsim.addWidget(self.btn_save)
        hsim.addStretch()
        v.addLayout(hsim)

        # linha de botões
        h = QHBoxLayout()
        self.btn_inspect = QPushButton("Inspecionar")
        self.btn_addimg  = QPushButton("Add imagem")
        h.addWidget(self.btn_inspect); h.addWidget(self.btn_addimg)
        v.addLayout(h)

        # botão auxiliar (opcional)
        if self._show_aux_button:
            self.btn_aux = QPushButton("Aux. de inspeção")
            v.addWidget(self.btn_aux)            
        else:
            self.btn_aux = None     # atributo presente para checagem externa
        v.addStretch()

        # sinais
        self.spin_w.valueChanged.connect(self._emit_params)
        self.spin_h.valueChanged.connect(self._emit_params)
        # mantém 4:3
        self.spin_w.valueChanged.connect(lambda w: self._sync_hw('w', w))
        self.spin_h.valueChanged.connect(lambda h: self._sync_hw('h', h))
        self.btn_region.clicked.connect(self._capture_region)
        # botão “Aux. de inspeção” só existe se show_aux_button=True
        if self.btn_aux is not None:
            self.btn_aux.clicked.connect(self._open_aux)

    # -------------------- tamanho fixo 4:3 ---------------------------
    def _update_region_aspect(self):
        """
        Agora é responsabilidade do próprio AspectRatioLabel via
        height-for-width.  Esta função existe apenas por compatibilidade
        e pode ser chamada livremente sem causar efeitos colaterais.
        """
        pass   # nada a fazer – proporção garantida pelo widget

    def _update_roi_aspect(self):
        """
        Ajusta SOMENTE o visor ROI.
        Passa a ser completamente independente do visor 'Região'.
        """
        col_w = self.width() or 1                  # largura real da coluna
        roi_w = max(10, int(col_w * 0.5))          # 50 % da coluna
        self.lbl_roi.setFixedWidth(roi_w)          # largura fixa
        self.lbl_roi.setFixedHeight(int(roi_w * 3 / 4))  # mantém 4:3

    def _style_label(self, lab: QLabel):
        lab.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lab.setStyleSheet("QLabel { background:#263238; color:#CFD8DC; }")

    # ---------------- ratio keeper ---------------------------------
    def _sync_hw(self, changed, val):
        if self._internal: return
        self._internal = True
        if changed == 'w':
            self.spin_h.setValue(int(val / self._ratio))
        else:
            self.spin_w.setValue(int(val * self._ratio))
        self._internal = False

    # ---------------- -- slots ------------------------------
    def _emit_params(self):
        self.parametersChanged.emit(self.spin_w.value(), self.spin_h.value())

    def _grab_frame(self):
        cm = getattr(self._c, "camera_manager", None)
        if not cm or not getattr(cm, "_cap", None): return None
        ok, frame = cm._cap.read()
        return frame if ok else None
    
    # ================================================================
    #  Sincronização com outras janelas
    # ================================================================
    def _apply_external_roi(self, img_bgr):
        """
        Recebe um ROI capturado em OUTRO InspectionConfigWidget
        (ex.: o widget embutido na janela Auxiliar) e apenas actualiza
        o visor + buffer interno, SEM re-emitir regionCaptured
        (assim evitamos loops infinitos de sinal).
        """
        if img_bgr is None:
            return
        self._last_roi_bgr = img_bgr
        self._show_pixmap(self.lbl_region, img_bgr, draw_border=True)

    def _capture_region(self):
        frame = self._grab_frame()
        if frame is None:
            return
        h_img, w_img, _ = frame.shape
        ww = self.spin_w.value(); hh = self.spin_h.value()
        cx, cy = w_img//2, h_img//2
        x0 = max(0, cx-ww//2); y0 = max(0, cy-hh//2)
        roi = frame[y0:y0 + hh, x0:x0 + ww].copy()
        self._last_roi_bgr = roi          # guarda original p/ alta qualidade
        self._show_pixmap(self.lbl_region, roi, draw_border=True)
        self.regionCaptured.emit(roi)

    def _show_pixmap(self, label: QLabel, img_bgr, *, draw_border=False):
        if img_bgr is None: return
        h,w,_ = img_bgr.shape
        if draw_border:
            img_bgr = cv2.rectangle(img_bgr.copy(), (0,0), (w-1,h-1),
                                    (0,255,255), 2)
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        from PyQt6.QtGui import QImage, QPixmap
        qimg = QImage(img_rgb.data, w, h, 3*w, QImage.Format.Format_RGB888)
        px = QPixmap.fromImage(qimg).scaled(
            label.width(), label.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation)
        label.setPixmap(px)

    def _open_aux(self):
        # 1) widget de controle (lado direito)
        # no painel à direita omitimos o visor da região E o botão auxiliar
        ctrl_w = InspectionConfigWidget(self._c,
                                        show_region=False,
                                        show_aux_button=False)
        ctrl_w.spin_w.setValue(self.spin_w.value())
        ctrl_w.spin_h.setValue(self.spin_h.value())
        ctrl_w.spin_sim.setValue(self.spin_sim.value())
        # 2) obtém ROI em resolução total, se disponível
        if self._last_roi_bgr is not None:
            pix = self._bgr_to_pixmap(self._last_roi_bgr)
        else:
            pix = self.lbl_region.pixmap()

        # 3) cria diálogo e mostra
        dlg = _AuxDialog(pix, ctrl_w, self)   # <-- 'self' = widget principal
        dlg.resize(900, 600)
        dlg.show()
    
    # ------------------------------------------------------------------
    #  Utilitário estático – converte numpy BGR → QPixmap sem downscale
    # ------------------------------------------------------------------
    @staticmethod
    def _bgr_to_pixmap(img_bgr):
        if img_bgr is None:
            return QPixmap()
        h, w, _ = img_bgr.shape
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        from PyQt6.QtGui import QImage, QPixmap
        qimg = QImage(img_rgb.data, w, h, 3 * w, QImage.Format.Format_RGB888)
        return QPixmap.fromImage(qimg)

    # exportação
    def roi_size(self):
        return self.spin_w.value(), self.spin_h.value()
    
    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        # region já é automático; apenas ROI necessita ajuste
        self._update_roi_aspect()
