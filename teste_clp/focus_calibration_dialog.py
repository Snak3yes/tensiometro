# focus_calibration_dialog.py
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QSlider,
                             QPushButton, QHBoxLayout, QMessageBox,
                             QSpinBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui  import QImage, QPixmap, QPainter, QPen

class FocusCalibrationDialog(QDialog):
    """
    Passo-a-passo:
      1. mover Z ao topo, ajustar foco, 'Definir Foco Alto'
      2. mover Z ao fundo, ajustar foco, 'Definir Foco Baixo'
    """
    def __init__(self, ctrl, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Calibração de Foco (Z)")
        self.ctrl = ctrl        # MultiAxisMotorController
        self.a = 0.0; self.b = 0.0
        self._top_done = False
        self._build_ui()
        # ---- suspende auto-focus enquanto a janela estiver aberta ---
        self._prev_auto_state = ctrl.camera_manager.auto_enabled
        ctrl.camera_manager.enable_auto_focus(False)
        self._img = None

    def _build_ui(self):
        v = QVBoxLayout(self)

        

        # ------------ foco manual ---------------------------------
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0,1023)
        v.addWidget(self.slider)

        self.spin_focus = QSpinBox()
        self.spin_focus.setRange(0,1023)
        self.spin_focus.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.spin_focus.setFixedWidth(70)

        h_focus = QHBoxLayout()
        h_focus.addWidget(QLabel("Foco:"))
        h_focus.addWidget(self.spin_focus)
        h_focus.addStretch()
        v.addLayout(h_focus)

        # ligações bidirecionais
        self.slider.valueChanged.connect(self.spin_focus.setValue)
        self.spin_focus.valueChanged.connect(self.slider.setValue)

        # aplica foco em cada mudança
        self.slider.valueChanged.connect(self._apply_focus)
        # garante aplicação depois de soltar o mouse
        self.slider.sliderReleased.connect(lambda: self._apply_focus(self.slider.value()))
        self.spin_focus.editingFinished.connect(
            lambda: self._apply_focus(self.spin_focus.value()))
        
        # ------------- posição Z atual ----------------------------
        hZ = QHBoxLayout()
        hZ.addWidget(QLabel("Z atual:"))
        self.lbl_z = QLabel("0")
        self.lbl_z.setMinimumWidth(80)
        hZ.addWidget(self.lbl_z)
        hZ.addStretch()
        v.addLayout(hZ)

        # timer interno p/ refrescar posição Z
        self._timer = QTimer(self); self._timer.start(200)
        self._timer.timeout.connect(
            lambda: self.lbl_z.setText(str(self.ctrl.current_positions['Z'])))

        # ------------- JOG Z  (press / release) -------------------
        hJog = QHBoxLayout()
        btn_jog_up   = QPushButton("JOG Z-")
        btn_jog_down = QPushButton("JOG Z+")
        btn_jog_up.pressed.connect(  lambda: self.ctrl.jog_start('Z','-'))
        btn_jog_up.released.connect( lambda: self.ctrl.jog_stop('Z'))
        btn_jog_down.pressed.connect(lambda: self.ctrl.jog_start('Z','+'))
        btn_jog_down.released.connect(lambda: self.ctrl.jog_stop('Z'))
        hJog.addWidget(btn_jog_up); hJog.addWidget(btn_jog_down)
        v.addLayout(hJog)

        # ------------- mover para valor absoluto ------------------
        hAbs = QHBoxLayout()
        self.spin_abs = QSpinBox()
        self.spin_abs.setRange(-2_147_483_648, 2_147_483_647)
        hAbs.addWidget(QLabel("Ir para Z ="))
        hAbs.addWidget(self.spin_abs)
        btn_go_abs = QPushButton("Mover")
        btn_go_abs.clicked.connect(self._move_abs_z)
        hAbs.addWidget(btn_go_abs)
        v.addLayout(hAbs)

        # ---------------- Go To LIMITS -------------------------------
        hl = QHBoxLayout()
        btn_top = QPushButton("Go to limit −  (Z alto)")
        btn_bot = QPushButton("Go to limit +  (Z baixo)")
        btn_top.clicked.connect(self._go_top)
        btn_bot.clicked.connect(self._go_bottom)
        hl.addWidget(btn_top); hl.addWidget(btn_bot)
        v.addLayout(hl)

        # define foco top / bottom
        h2 = QHBoxLayout()
        self.btn_top = QPushButton("Definir Foco Alto")
        self.btn_bot = QPushButton("Definir Foco Baixo")
        self.btn_bot.setEnabled(False)
        self.btn_top.clicked.connect(self._set_top)
        self.btn_bot.clicked.connect(self._set_bot)
        h2.addWidget(self.btn_top); h2.addWidget(self.btn_bot)
        v.addLayout(h2)

        # OK/Cancelar
        bok = QPushButton("Salvar"); bok.clicked.connect(self._save)
        bcan= QPushButton("Cancelar"); bcan.clicked.connect(self.reject)
        h3 = QHBoxLayout(); h3.addStretch(); h3.addWidget(bok); h3.addWidget(bcan)
        v.addLayout(h3)

    # ---------------- movimento Z até limites ---------------------
    def _go_top(self):
        z0 = self.ctrl.read_dword(self.ctrl.addresses['D23080_Z'])   # limite-
        self.ctrl.pulsos_spin_Z.setValue(z0)
        self.ctrl.move_axis_absolute('Z')

    def _go_bottom(self):
        zmax = self.ctrl.read_dword(self.ctrl.addresses['D23120'])   # limite+
        if QMessageBox.question(self, "Atenção",
                "A cabeça irá DESCER até o limite POSITIVO de Z.\n"
                "Certifique-se de que não há obstáculos.\n\nContinuar?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return
        self.ctrl.pulsos_spin_Z.setValue(zmax)
        self.ctrl.move_axis_absolute('Z')

    def _set_top(self):
        z = self.ctrl.current_positions['Z']
        f = self.slider.value()
        self._z_top = z; self._f_top = f
        self._top_done = True
        self.btn_bot.setEnabled(True)
        QMessageBox.information(self, "Passo 1 concluído",
            "Agora baixe cuidadosamente o eixo Z\naté o limite inferior e ajuste o foco.\nDepois clique em 'Definir Foco Baixo'.")

    def _set_bot(self):
        z = self.ctrl.current_positions['Z']
        f = self.slider.value()
        if z == self._z_top:
            QMessageBox.warning(self,"Erro","A posição Z deve ser diferente.")
            return
        self._z_bot = z; self._f_bot = f
        self.accept()           # encerra diálogo

    def _save(self):
        if not self._top_done:
            QMessageBox.warning(self,"Incompleto","Defina os dois focos antes de salvar.")
            return
        
    # ---------- helper --------------------------------------------
    def _apply_focus(self, val:int):
        self.ctrl.camera_manager.set_focus(val)
    
    # ------------- move para posição absoluta --------------------
    def _move_abs_z(self):
        val = self.spin_abs.value()
        self.ctrl.pulsos_spin_Z.setValue(val)
        self.ctrl.move_axis_absolute('Z')

    # --------------------------------------------------------------
    def closeEvent(self, ev):
        # restaura estado anterior do auto-focus
        self.ctrl.camera_manager.enable_auto_focus(self._prev_auto_state)
        super().closeEvent(ev)
        # encerra timer interno
        self._timer.stop()
        # garante que JOG foi desligado
        self.ctrl.jog_stop('Z')
