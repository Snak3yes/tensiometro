# table_program_tab.py
"""
Aba de programação de uma mesa (Mesa 1 ou Mesa 2).
Mostra controles para X, Y (lógico) e Z apenas.
"""

from PyQt6.QtWidgets import QWidget, QGridLayout, QVBoxLayout, QFrame, QSizePolicy, QLabel
from PyQt6.QtCore    import Qt, QTimer
from PyQt6.QtGui     import QPixmap
import base64, cv2
import time

from inspection_config_widget import InspectionConfigWidget
from movement_controls_widget import MovementControlsWidget
from position_status_widget   import PositionStatusWidget
from inspection_positions_widget import InspectionPositionsWidget
from program_io_widget        import ProgramIOWidget
from table_positions_backend  import TablePositionsBackend
from sequence_control         import SequenceControlWidget, InspectionPosition
from dot_patterns_widget      import DotPatternsWidget
from dot_action_selector_widget import DotActionSelectorWidget
from action_config_placeholders import (
    BarcodeConfigWidget, FiducialConfigWidget, InspectionConfigWidget
)
from PyQt6.QtWidgets import QStackedWidget
from PyQt6.QtCore    import pyqtSignal

# ------------------------------------------------------------------
#  QLabel que emite sinal ao clicar – para mover a cabeça
# ------------------------------------------------------------------
class ClickableLabel(QLabel):
    # usa float porque ev.position().x()/y() devolvem qreal (float)
    clicked = pyqtSignal(float, float)   # x,y em pixels dentro do label
    def mousePressEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(ev.position().x(), ev.position().y())
        super().mousePressEvent(ev)


class TableProgramTab(QWidget):
    """
    Mesa 1 → usa eixo físico Y1
    Mesa 2 → usa eixo físico Y2
    """
    def __init__(self, controller, mesa_id: int):
        super().__init__()
        assert mesa_id in (1, 2)
        self.ctrl   = controller
        self.mesa   = mesa_id          # 1 ou 2
        self.y_axis = 'Y1' if mesa_id == 1 else 'Y2'
        # orientação do Y: +1 → clicar acima do centro move Y+
        #                    -1 → clicar acima move Y-
        # sua câmera está “invertida”, portanto usamos +1
        self._PIXEL_TO_Y_SIGN = +1
        self._build_ui()
        self._jog_active_axis: str | None = None
        QTimer.singleShot(0, self._fix_video_size)
        self.ctrl.camera_manager.frameReady.connect(self._update_frame)

    # ------------------------------------------------------------------
    #  TAMANHO FIXO DO VÍDEO
    # ------------------------------------------------------------------
    def _fix_video_size(self):
        """Define largura/altura fixas para o lbl_video em ≈70 % da
           janela e muda o SizePolicy para Fixed, impedindo que o layout
           redimensione esse label no futuro."""
        win = self.window()
        if not win:
            return
        w = int(win.width()  * 1.0)
        h = int(win.height() * 1.0 * 1.0    )  
        # mantém razão 4:3 aproximada
        if h * 4 < w * 3:
            w = int(h * 4 / 3)
        else:
            h = int(w * 3 / 4)
        self.lbl_video.setSizePolicy(QSizePolicy.Policy.Fixed,
                                     QSizePolicy.Policy.Fixed)
        self.lbl_video.setFixedSize(w, h)
        

    # ------------------------- ATUALIZAÇÃO DO QUADRO -------------------------
    def _update_frame(self, img):
        # escala mantendo proporção
        # guarda tamanho original para coordenadas
        self._last_frame_sz = (img.width(), img.height())
        pix = QPixmap.fromImage(img).scaled(
            self.lbl_video.size(), Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation)
        
        # ---- desenha cruz -----------------
        p = QPixmap(pix.size())
        p.fill(Qt.GlobalColor.transparent)
        from PyQt6.QtGui import QPainter, QPen
        pa = QPainter(p)
        pen = QPen(Qt.GlobalColor.red, 4, Qt.PenStyle.SolidLine)
        pa.setPen(pen)
        cx = p.width()//2; cy = p.height()//2
        pa.drawLine(cx-100, cy, cx+100, cy)
        pa.drawLine(cx, cy-100, cx, cy+100)
        # -------- overlays se ação = fiducial -----------------------
        if self.action_selector.current_action() == 'fiducial':
            win = self._fid_window
            rad = self._fid_radius
            sx = pix.width()  / self._last_frame_sz[0]
            sy = pix.height() / self._last_frame_sz[1]
            # ROI (amarelo cheio)
            pen_y = QPen(Qt.GlobalColor.yellow, 2, Qt.PenStyle.SolidLine)
            pa.setPen(pen_y)
            rw = int(win * sx); rh = int(win * sy)
            pa.drawRect(cx - rw//2, cy - rh//2, rw, rh)
            # ÁREA DE BUSCA (amarelo tracejado)
            pen_d = QPen(Qt.GlobalColor.yellow, 1, Qt.PenStyle.DashLine)
            pa.setPen(pen_d)
            r2 = win + 2*rad
            rw2 = int(r2 * sx); rh2 = int(r2 * sy)
            pa.drawRect(cx - rw2//2, cy - rh2//2, rw2, rh2)
            # Resultado do último teste (2 s)
            if self._match_info:
                rect, color, t0 = self._match_info
                if time.time() - t0 < 2.0:
                    pen_m = QPen(color, 2)
                    pa.setPen(pen_m)
                    x, y, w, h = rect
                    pa.drawRect(int(x*sx), int(y*sy), int(w*sx), int(h*sy))
                else:
                    self._match_info = None
        elif self.action_selector.current_action() == 'barcode':
            bw, bh = self._bc_w, self._bc_h
            sx = pix.width()  / self._last_frame_sz[0]
            sy = pix.height() / self._last_frame_sz[1]
            pen_b = QPen(Qt.GlobalColor.yellow, 2)
            pa.setPen(pen_b)
            # retângulo da ROI (amarelo) – converte para int
            rx = int(cx - bw*sx/2)
            ry = int(cy - bh*sy/2)
            rw = int(bw * sx)
            rh = int(bh * sy)
            pa.drawRect(rx, ry, rw, rh)
            if self._bc_match and time.time()-self._bc_match[2] < 2.0:
                rect, color, t0 = self._bc_match
                pen_m = QPen(color, 2)
                pa.setPen(pen_m)
                x,y,w,h = rect
                pa.drawRect(int(x*sx), int(y*sy), int(w*sx), int(h*sy))
            elif self._bc_match:
                self._bc_match = None
        elif self.action_selector.current_action() == 'inspect':
            iw, ih = self._insp_w, self._insp_h
            sx = pix.width()/self._last_frame_sz[0]
            sy = pix.height()/self._last_frame_sz[1]
            pen_i = QPen(Qt.GlobalColor.yellow, 2)
            pa.setPen(pen_i)
            rx = int(cx - iw*sx/2)
            ry = int(cy - ih*sy/2)
            rw = int(iw*sx); rh = int(ih*sy)
            pa.drawRect(rx, ry, rw, rh)
            if self._insp_match and time.time()-self._insp_match[2]<2.0:
                rect,color,t0 = self._insp_match
                pen_m = QPen(color,2); pa.setPen(pen_m)
                x,y,w,h = rect
                pa.drawRect(int(x*sx), int(y*sy), int(w*sx), int(h*sy))
            elif self._insp_match:
                self._insp_match=None
        pa.end()
        qp = QPixmap(pix.size())
        qp.fill(Qt.GlobalColor.transparent)
        painter = QPainter(qp); painter.drawPixmap(0,0,pix); painter.drawPixmap(0,0,p); painter.end()
        self.lbl_video.setPixmap(qp)
    
    # ---------------- overlay helpers -------------------------------
    def _on_fid_params(self, win:int, rad:int):
        self._fid_window = win
        self._fid_radius = rad
    def _on_fid_match(self, sim:float, ok:bool, x:int, y:int, w:int, h:int):
        from PyQt6.QtGui import QColor
        self._match_info = ((x, y, w, h),
                            QColor(Qt.GlobalColor.green if ok else Qt.GlobalColor.red),
                            time.time())
    
    # -------- barcode helpers --------------------------------------
    def _set_barcode_roi(self, w:int, h:int):
        self._bc_w, self._bc_h = w, h
    def _on_bc_test(self, ok:bool, x:int, y:int, w:int, h:int):
        from PyQt6.QtGui import QColor
        self._bc_match = ((x,y,w,h),
                          QColor(Qt.GlobalColor.green if ok else Qt.GlobalColor.red),
                          time.time())
        
    # -------- inspeção helpers --------------------------------------
    def _set_insp_roi(self,w:int,h:int):
        self._insp_w=w; self._insp_h=h
    def _on_insp_region(self,img):
        # último retângulo verde (sempre OK por definição)
        from PyQt6.QtGui import QColor
        self._insp_match=((0,0,self._insp_w,self._insp_h),
                          QColor(Qt.GlobalColor.green),
                          time.time())

    def _build_ui(self):
        grid = QGridLayout(self)
        grid.setContentsMargins(0, 0, 0, 0)

        # proporções
        grid.setColumnStretch(0, 15)
        grid.setColumnStretch(1, 70)
        grid.setColumnStretch(2, 15)
        grid.setRowStretch(0, 7)
        grid.setRowStretch(1, 3)

        # -------------------- COLUNA ESQUERDA (posições) --------------
        v_left = QVBoxLayout()

        aux = self.ctrl.create_auxiliary_controls()
        v_left.addWidget(aux)
        v_left.addStretch()

        # ---------- SELETOR DE AÇÃO --------------------------------
        self.action_selector = DotActionSelectorWidget()
        v_left.addWidget(self.action_selector)
        # ---------- STACK DE CONFIGURAÇÕES -------------------------
        self._config_stack = QStackedWidget()
        # página 0 – DOTS
        self.dots_view = DotPatternsWidget()
        self._config_stack.addWidget(self.dots_view)
        # página 1 – BARCODE (widget real)
        self.barcode_cfg = BarcodeConfigWidget(self.ctrl)
        self._config_stack.addWidget(self.barcode_cfg)
        # página 2 – INSPEÇÃO (widget real)
        self.inspect_cfg = InspectionConfigWidget(self.ctrl)
        self._config_stack.addWidget(self.inspect_cfg)
        # página 3 – FIDUCIAL (widget real – precisa do controller)
        self.fiducial_cfg = FiducialConfigWidget(self.ctrl)
        self._config_stack.addWidget(self.fiducial_cfg)   # index 3

        # -------- overlay barcode ---------------------------------
        self._bc_w = 400; self._bc_h = 150
        self._bc_match = None   # (rect,color,t0)
        self.barcode_cfg.parametersChanged.connect(
            lambda w,h: self._set_barcode_roi(w,h))
        self.barcode_cfg.testFinished.connect(self._on_bc_test)

        # -------- overlay fiducial ---------------------------------
        self._fid_window = 50
        self._fid_radius = 80
        self._match_info = None    # (rect, color, t0)
        self.fiducial_cfg.parametersChanged.connect(self._on_fid_params)
        self.fiducial_cfg.matchTested.connect(self._on_fid_match)
        # -------- overlay inspeção -----------------------------------
        self._insp_w=400; self._insp_h=300
        self._insp_match=None
        self.inspect_cfg.parametersChanged.connect(
            lambda w,h: self._set_insp_roi(w,h))
        self.inspect_cfg.regionCaptured.connect(self._on_insp_region)

        v_left.addWidget(self._config_stack, 1)   # ocupa o restante

        # conecta mudança de ação
        self.action_selector.actionChanged.connect(self._show_action_config)
        # seleção default: Dot
        self.action_selector._group.buttons()[1].setChecked(True)  # 'dot'
        self._show_action_config('dot')

        w_left = QWidget(); w_left.setLayout(v_left)
        grid.addWidget(w_left, 0, 0)

        # -------------------- COLUNA CENTRAL (preview câmera) ----------
        
        self.lbl_video = ClickableLabel("Sem vídeo")
        self.lbl_video.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_video.setStyleSheet(
            "QLabel { background:#000; color:#FFF; border:1px dashed #607D8B; }")
        # não deixa o label pedir altura maior que a célula
        self.lbl_video.setSizePolicy(
            QSizePolicy.Policy.Expanding,      # horizontal livre
            QSizePolicy.Policy.Preferred)      # vertical controlado
        # mantém o label FIXO (já dimensionado por _fix_video_size) e
        # o coloca sempre no centro da célula  (h & v).
        grid.addWidget(self.lbl_video, 0, 1,
                       alignment=Qt.AlignmentFlag.AlignCenter)
        # clique → mover cabeça
        self.lbl_video.clicked.connect(self._on_video_click)

        # -------------------- COLUNA DIREITA (controles) --------------
        v_right = QVBoxLayout()

        self.mov_widget = MovementControlsWidget()    # padrão completo
        v_right.addWidget(self.mov_widget)

        # limites provenientes do controlador
        self._limits = self.ctrl.table_limits[self.mesa]

        # Posições de inspeção (X,Y,Z apenas, com validação)
        self.inspect_widget = InspectionPositionsWidget(
            get_current_position=self._get_current_position,
            validate_position=self._validate_position,
            get_action_context=self._current_action_context
        )
        v_right.addWidget(self.inspect_widget)

        # --- backend que salva 3 eixos + extensão dedicada ------------
        backend = TablePositionsBackend(self.inspect_widget, self.y_axis)
        file_filter   = f"Programa Mesa {self.mesa} (* .m{self.mesa})"
        self.prog_widget = ProgramIOWidget(
            backend,
            file_filter=file_filter,
            default_suffix=f".m{self.mesa}"
        )
        v_right.addWidget(self.prog_widget)
        # remove botões Salvar/Carregar da interface desta aba
        self.prog_widget.hide()

        self.seq_widget = SequenceControlWidget(
            motion=self.ctrl._plc_motion_backend, camera=None)
        v_right.addWidget(self.seq_widget)

        v_right.addStretch()
        w_right = QWidget(); w_right.setLayout(v_right)
        grid.addWidget(w_right, 0, 2)

        # ------------------------- LINHA INFERIOR ---------------------
        left_sp = QWidget(); right_sp = QWidget()
        for s in (left_sp, right_sp):
            s.setSizePolicy(QSizePolicy.Policy.Expanding,
                            QSizePolicy.Policy.Preferred)
        
        bottom = QFrame()
        bottom.setStyleSheet(
            "QFrame { background:#ECEFF1; border:1px dashed #B0BEC5;}")
        # garante que a linha 1 tenha “peso” para competir com o vídeo
        bottom.setSizePolicy(QSizePolicy.Policy.Expanding,
                             QSizePolicy.Policy.Expanding)

        grid.addWidget(left_sp, 1, 0)
        grid.addWidget(bottom, 1, 1)
        grid.addWidget(right_sp, 1, 2)

        # ------------------------- SINAIS -----------------------------
        self.mov_widget.stepMoveRequested.connect(self._on_step_move)
        self.mov_widget.jogStart.connect(self._on_jog_start)
        self.mov_widget.jogStop.connect(self._on_jog_stop)
        self.mov_widget.goToZeroRequested.connect(self._go_center)

        self.inspect_widget.positionAdded.connect(
            lambda _: self.seq_widget.set_positions(self._to_model()))
        self.inspect_widget.positionRemoved.connect(
            lambda _: self.seq_widget.set_positions(self._to_model()))
        self.prog_widget.fileLoaded.connect(
            lambda _: self.seq_widget.set_positions(self._to_model()))

        # logs
        self.prog_widget.fileLoaded.connect(
            lambda f: self.ctrl.log(f"[Mesa {self.mesa}] Programa carregado: {f}"))
        self.prog_widget.fileSaved.connect(
            lambda f: self.ctrl.log(f"[Mesa {self.mesa}] Programa salvo: {f}"))
        
        # -------------------- GRÁFICO -----------------------------
        # sempre que houver mudança nos pontos ou carregamento de um
        # programa, envia nova lista ao MesaPlotWidget da mesa.
        for sig in (self.inspect_widget.positionAdded,
                    self.inspect_widget.positionRemoved,
                    self.prog_widget.fileLoaded):
            sig.connect(lambda _=None: self._update_plot())

        QTimer.singleShot(0, self._update_plot)   # primeira vez

        # ============================ PERSONALIZAÇÃO UI ================
        self._adapt_widgets_for_single_y()

    # ------------------------------------------------------------------
    #  Clique no vídeo → mover cabeça
    # ------------------------------------------------------------------
    def _on_video_click(self, px: float, py: float):
        if not hasattr(self, "_last_frame_sz"):
            return
        # --------------------------------- 1. Conversão pixel → mm ----
        # ------------------------------------------------------------
        #  Determina retângulo efetivo da imagem dentro do QLabel
        # ------------------------------------------------------------
        disp_w = self.lbl_video.width()
        disp_h = self.lbl_video.height()
        orig_w, orig_h = self._last_frame_sz
        # escala aplicada pelo QPixmap.scaled(KeepAspectRatio)
        scale = min(disp_w / orig_w, disp_h / orig_h)
        pix_w = orig_w * scale
        pix_h = orig_h * scale
        offset_x = (disp_w - pix_w) / 2
        offset_y = (disp_h - pix_h) / 2
        # ignora clique fora da imagem
        if not (offset_x <= px <= offset_x + pix_w and
                offset_y <= py <= offset_y + pix_h):
            return
        # coordenada relativa ao centro da imagem, em pixels
        dx_pix = (px - offset_x - pix_w/2) / scale
        dy_pix = (py - offset_y - pix_h/2) / scale
        # conserta orientação Y
        dy_pix *= self._PIXEL_TO_Y_SIGN
        # ----------------------- 4. Escala MM/PX – modelo óptico -----
        z_cur = self.ctrl.current_positions['Z']
        c     = self.ctrl._fov_coeffs
        w_mm  = c["aX"] * z_cur + c["bX"]
        h_mm  = c["aY"] * z_cur + c["bY"]
        mmpp_x = w_mm / orig_w
        mmpp_y = h_mm / orig_h

        dx_mm = dx_pix * mmpp_x
        dy_mm = dy_pix * mmpp_y
        # --------------------------------- 2. Converte para pulsos ----
        dx_pulses = self.ctrl.pulses_from_mm('X', dx_mm)
        dy_pulses = self.ctrl.pulses_from_mm(self.y_axis, dy_mm)

        # --------------------------------- 3. Calcula alvo absoluto ---
        cur_x = self.ctrl.current_positions['X']
        cur_y = self.ctrl.current_positions[self.y_axis]
        tgt_x = cur_x + dx_pulses
        tgt_y = cur_y + dy_pulses

        # limita dentro da área de trabalho da mesa
        x_min, x_max = self._limits['x']
        y_min, y_max = self._limits['y']
        tgt_x = max(x_min, min(x_max, tgt_x))
        tgt_y = max(y_min, min(y_max, tgt_y))

        # deslocamentos corrigidos
        dx_corr = tgt_x - cur_x
        dy_corr = tgt_y - cur_y

        # evita comandos nulos / redundantes
        if dx_corr:
            self.ctrl.move_relative('X', int(dx_corr))
        if dy_corr:
            self.ctrl.move_relative(self.y_axis, int(dy_corr))

        self.ctrl.log(f"■ Clique: ΔX={dx_corr}  ΔY={dy_corr} pulsos  "
                      f"(destino X={tgt_x}, Y={tgt_y})")

    # ----------------------- helpers ação ---------------------------
    def _current_action_context(self) -> dict | None:
        key = self.action_selector.current_action()
        if not key:
            return None
        if key == 'fiducial':
            # precisa haver template capturado
            tmpl = self.fiducial_cfg.template_image()
            if tmpl is None:
                return None
            _, buf = self.cv2.imencode('.png', tmpl)
            b64 = self.base64.b64encode(buf).decode('ascii')
            return {
                'action': 'fiducial',
                'window': self.fiducial_cfg.spin_window.value(),
                'radius': self.fiducial_cfg.spin_radius.value(),
                'threshold': self.fiducial_cfg.spin_thresh.value(),
                'template_png_b64': b64
            }
        elif key == 'barcode':
            w,h = self.barcode_cfg.roi_size()
            return {'action':'barcode', 'width':w, 'height':h}
        elif key == 'inspect':
            # 1) Dados completos (posições mecânicas + janelas azuis)
            aux_data = self.inspect_cfg.get_cached_auxiliary_data()
            comp_dict = aux_data.get('componentes', {})

            # -----------------------------------------------------------------
            #  SANITIZAÇÃO:
            #     • mantemos SOMENTE coordenadas e dimensões das janelas;
            #     • cada janela ('w1' …) recebe sua própria “similaridade”;
            #     • campo 'nome' é salvo para uso futuro.
            # -----------------------------------------------------------------
            sim_min = float(self.inspect_cfg.spin_sim.value()) / 100.0

            def _clean_inspecao(idx: int, insp: dict) -> dict:
                return {
                    'nome':       f"w{idx+1}",
                    'posicao':    tuple(insp.get('posicao', (0, 0))),
                    'tamanho':    tuple(insp.get('tamanho', (0, 0))),
                    'similaridade': sim_min
                }

            serializable_comp = {}
            
            for nome, dados in comp_dict.items():
                insp_list = dados.get('inspecoes', [])
                serializable_comp[nome] = dict(
                    posicao    = tuple(dados.get('posicao', (0, 0))),
                    dimensoes  = tuple(dados.get('dimensoes', (0, 0))),
                    inspecoes  = [_clean_inspecao(i, insp)
                                  for i, insp in enumerate(insp_list)]
                )

            return {
                'action':      'inspect',
                'componentes': serializable_comp
            }
        elif key == 'dot':
            pat = self.dots_view.current_pattern()
            if pat is None:
                return None      # impede adicionar sem seleção
            return {
                'action':   'dot',
                'dot_id':   pat.id,
                'dot_name': pat.name,
                'dot_qty':  pat.qty
            }
        else:
            return {'action': key}

    # ------------------------------------------------------------------
    #  Exibe página conforme ação escolhida
    # ------------------------------------------------------------------
    def _show_action_config(self, action_key: str):
        index_map = {
            'dot':      0,
            'barcode':  1,
            'inspect':  2,
            'fiducial': 3
        }
        idx = index_map.get(action_key, 0)
        self._config_stack.setCurrentIndex(idx)

    # ------------------------------------------------------------------
    #  Actualiza gráfico correspondente à mesa
    # ------------------------------------------------------------------
    def _update_plot(self):
        if not hasattr(self.ctrl, "mesa_plot_widgets"):
            return
        pts = []
        for p in self.inspect_widget.positions():
            y_val = p.y1 if self.y_axis == 'Y1' else p.y2
            pts.append((p.x, y_val))
        self.ctrl.mesa_plot_widgets[self.mesa].update_points(pts)

    # ------------ pode ser chamado externamente ----------------------
    def set_limits(self, limits: dict[str, tuple[int, int]]):
        """Atualiza área de trabalho desta aba."""
        self._limits = limits

    # ------------------------------------------------------------------
    # valida ponto em relação à área de trabalho desta mesa
    # ------------------------------------------------------------------
    def _validate_position(self, x, y2, y1, z) -> str | None:
        # escolhe o Y físico desta mesa
        y_val = y1 if self.y_axis == 'Y1' else y2

        x_ok = self._limits['x'][0] <= x <= self._limits['x'][1]
        y_ok = self._limits['y'][0] <= y_val <= self._limits['y'][1]

        if not x_ok or not y_ok:
            return (f"Coordenada fora dos limites da Mesa {self.mesa}.\n"
                    f"Permitido X:{self._limits['x']}  "
                    f"Y:{self._limits['y']}\n"
                    f"Recebido X={x:.0f}  Y={y_val:.0f}")
        return None

    # ------------------------------------------------------------------

    def _adapt_widgets_for_single_y(self):
        """
        Oculta/renomeia elementos de Y1 ou Y2 para que cada aba
        mostre apenas um eixo ‘Y’.
        """
        # ---- PositionStatusWidget -----------------------------------
        # --- trata rótulos e valores de Y --------------------------------
        # ---- Oculta linha Y que não pertence à mesa -----------------
        if self.y_axis == 'Y1':
            self.mov_widget.lbl_pos_y2.hide()
            self.mov_widget.lbl_pos_y1.setText("0")          # rename
        else:
            self.mov_widget.lbl_pos_y1.hide()
            self.mov_widget.lbl_pos_y2.setText("0")

        # ---- MovementControlsWidget  (oculta e realinha) -------------
        g: QGridLayout = self.mov_widget.grid          # grid de botões

        if self.y_axis == 'Y1':
            # Oculta botões Y2 (btn_up / btn_down) e renomeia Y1
            for b in ('btn_up', 'btn_down'):
                getattr(self.mov_widget, b).hide()
            self.mov_widget.btn_y1_up.setText("Y+")
            self.mov_widget.btn_y1_down.setText("Y-")

            # Reposiciona Y+ / Y- da mesa na coluna do STOP (col 1)
            g.removeWidget(self.mov_widget.btn_y1_up)
            g.removeWidget(self.mov_widget.btn_y1_down)
            g.addWidget(self.mov_widget.btn_y1_up,   0, 1)
            g.addWidget(self.mov_widget.btn_y1_down, 2, 1)
        else:
            # Oculta botões Y1 e renomeia Y2
            self.mov_widget.btn_y1_up.hide()
            self.mov_widget.btn_y1_down.hide()
            self.mov_widget.btn_up.setText("Y+")
            self.mov_widget.btn_down.setText("Y-")
 
            # Reposiciona Y+ / Y- padrão para coluna do STOP
            g.removeWidget(self.mov_widget.btn_up)
            g.removeWidget(self.mov_widget.btn_down)
            g.addWidget(self.mov_widget.btn_up,   0, 1)
            g.addWidget(self.mov_widget.btn_down, 2, 1)

    # ------------------------------------------------------------------
    def _get_current_position(self):
        """Retorna posição atual só com o eixo Y físico desta mesa."""
        if self.y_axis == 'Y1':
            return {
                'x': self.ctrl.current_positions['X'],
                'y1': self.ctrl.current_positions['Y1'],
                'y2': 0,
                'z': self.ctrl.current_positions['Z']
            }
        else:  # mesa 2 → usa Y2
            return {
                'x': self.ctrl.current_positions['X'],
                'y2': self.ctrl.current_positions['Y2'],
                'y1': 0,
                'z': self.ctrl.current_positions['Z']
            }

    # --------------------- callbacks movimento ------------------------
    def _on_step_move(self, axis, dist, feed):
        if axis == 'Y1' or axis == 'Y2':
            axis = self.y_axis           # força usar o eixo da mesa
        self.ctrl.move_relative(axis, int(dist))

    def _on_jog_start(self, axis, direction, feed):
        # converte Y lógico → eixo físico da mesa
        if axis in ('Y1', 'Y2'):
            axis = self.y_axis

        self._jog_active_axis = axis              # memoriza
        self.ctrl.jog_start(axis, '+' if direction > 0 else '-')

    def _on_jog_stop(self):
        if self._jog_active_axis:
            self.ctrl.jog_stop(self._jog_active_axis)
            self._jog_active_axis = None

    # --------------------- homing / center ----------------------------
    def _go_center(self):
        """Leva o cabeçote ao homing virtual configurado p/ esta mesa."""
        self.ctrl.goto_virtual_home(self.mesa)

    # ------------------------------------------------------------------
    def _to_model(self):
        out = []
        for p in self.inspect_widget.positions():
            # Salva somente X, Y (desta mesa) e Z
            if self.y_axis == 'Y1':
                out.append(InspectionPosition(name=p.name,
                                              x=p.x, y1=p.y1, y2=None, z=p.z))
            else:
                out.append(InspectionPosition(name=p.name,
                                              x=p.x, y2=p.y2, y1=None, z=p.z))
        return out
