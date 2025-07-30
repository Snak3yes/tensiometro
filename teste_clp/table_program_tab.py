# table_program_tab.py
"""
Aba de programação de uma mesa (Mesa 1 ou Mesa 2).
Mostra controles para X, Y (lógico) e Z apenas.
"""

from PyQt6.QtWidgets import QWidget, QGridLayout, QVBoxLayout, QFrame, QSizePolicy, QLabel, QSpinBox, QPushButton, QMessageBox
from PyQt6.QtCore    import Qt, QTimer
from PyQt6.QtGui     import QPixmap
import base64, cv2
import numpy as np
from PIL import Image
import time
from helpers import read_fiducials
from sequence_control import SequenceRunnerThread
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

        # -------- estado da PRÉ-VISUALIZAÇÃO -------------
        self._preview_runner = None
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
        # -------------------------------------------------------------
        #  OVERLAY 1 – seletor em “fiducial” (edição)
        # -------------------------------------------------------------
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
        # -------------------------------------------------------------
        #  OVERLAY 2 – execução automática
        #     • Se _match_info existir, desenhamos o retângulo SEM
        #       limite de tempo; ele será limpo pelo sinal fidClear
        #       quando o cabeçote chegar ao próximo ponto.
        # -------------------------------------------------------------
        elif self._match_info and self.action_selector.current_action() != 'fiducial':
            sx = pix.width()  / self._last_frame_sz[0]
            sy = pix.height() / self._last_frame_sz[1]
            rect, color, t0 = self._match_info
            # mantém no máximo 2 s
            if time.time() - t0 > 2.0:
                self._match_info = None
            else:
                x, y, w0, h0 = rect
                pen_m = QPen(color, 2)
                pa.setPen(pen_m)
                pa.drawRect(int(x*sx), int(y*sy), int(w0*sx), int(h0*sy))
            
        elif (self.action_selector.current_action() == 'barcode' or self._bc_match):
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

        # ------------------------------------------------------------------
        #  Botões EDITAR e REMOVER – tratativa personalizada
        #  • Remove o handler padrão de remoção (sem confirmação)
        #  • Conecta nosso slot com caixa de diálogo
        # ------------------------------------------------------------------
        self.inspect_widget.btn_edit.clicked.connect(self._on_edit_clicked)
        try:
            # desconecta handler automático configurado no widget
            self.inspect_widget.btn_remove.clicked.disconnect()
        except TypeError:
            pass
        self.inspect_widget.btn_remove.clicked.connect(self._on_remove_clicked)

        # ――――― duplo-clique leva a cabeça até a posição ――――――
        self.inspect_widget.list_widget.itemDoubleClicked.connect(
            self._on_position_double_clicked)
        # qualquer mudança de seleção (clique simples, setas, PgUp, …)
        # bloqueia o botão até que outro duplo-clique seja feito
        self.inspect_widget.list_widget.itemSelectionChanged.connect(
            lambda: [self.inspect_widget.btn_edit.setEnabled(False),
                     self.inspect_widget.btn_remove.setEnabled(False)])

        v_right.addWidget(self.inspect_widget)

        # --- backend que salva 3 eixos + extensão dedicada ------------
        backend = TablePositionsBackend(self.inspect_widget, self.y_axis)
        file_filter   = f"Programa Mesa {self.mesa} (* .m{self.mesa})"
        self.prog_widget = ProgramIOWidget(
            backend,
            file_filter=file_filter,
            default_suffix=f".m{self.mesa}",
            default_dir=self.ctrl.projects_dir
        )
        v_right.addWidget(self.prog_widget)
        # remove botões Salvar/Carregar da interface desta aba
        self.prog_widget.hide()

        self.seq_widget = SequenceControlWidget(
            motion=self.ctrl._plc_motion_backend, camera=None)
        self.seq_widget.fidMatch.connect(self._on_fid_match)
        self.seq_widget.fidClear.connect(lambda: setattr(self, "_match_info", None))
        v_right.addWidget(self.seq_widget)

        # ---------- BARCODE em execução ------------------------------
        self.seq_widget.bcMatch.connect(self._on_bc_runtime)
        self.seq_widget.bcClear.connect(lambda: setattr(self, "_bc_match", None))

        # ---------- realça linha que está sendo executada ------------
        self.seq_widget.progressIdx.connect(self._on_exec_progress)

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

        # inserir posição dispara renumeração do gráfico
        self.inspect_widget.positionInserted.connect(
            lambda _: self.seq_widget.set_positions(self._to_model()))
        self.inspect_widget.positionAdded.connect(
            lambda _: self.seq_widget.set_positions(self._to_model()))
        # NOVO: criação imediata das pastas / imagens
        self.inspect_widget.positionAdded.connect(self._on_position_added)
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

    # ---------------------------------------------------------------
    #  Seleciona na lista a linha que o runner acabou de concluir
    # ---------------------------------------------------------------
    def _on_exec_progress(self, idx: int):
        """
        Recebe 1-based `idx` do SequenceRunnerThread e realça a linha
        correspondente (idx-1) no QListWidget.
        """
        row = idx - 1
        lw  = self.inspect_widget.list_widget
        if 0 <= row < lw.count():
            lw.setCurrentRow(row)
            lw.scrollToItem(lw.item(row))

    # ------------------------------------------------------------------
    def _on_edit_clicked(self):
        """
        Salva edição garantindo que o deslocamento seja
        SUBTRAÍDO antes de gravar as coordenadas base.
        """
        cur_item = self.inspect_widget.list_widget.currentItem()
        if cur_item is None:
            return
        row = self.inspect_widget.list_widget.row(cur_item)
        positions = self.inspect_widget.positions()
        if row >= len(positions):
            return
        # ------------------------ 1. nova AÇÃO ------------------------
        new_meta = self._current_action_context()
        if new_meta is None:
            QMessageBox.warning(self, "Ação inválida",
                                "Configure a ação antes de salvar.")
            return

        # ------------------------ 2. nova POSIÇÃO ---------------------
        cur_dict = self._get_current_position() or {}
        x  = float(cur_dict.get("x", 0))
        y1 = float(cur_dict.get("y1", 0))
        y2 = float(cur_dict.get("y2", 0))
        z  = float(cur_dict.get("z", 0))

         # --------- remove OFFSET dinâmico aplicado pelo runner -------
        dx_dyn = self.ctrl._plc_motion_backend._dx_dyn
        dy_dyn = self.ctrl._plc_motion_backend._dy_dyn
        if dx_dyn or dy_dyn:
            x -= dx_dyn
            if self.y_axis == 'Y1':
                y1 -= dy_dyn
            else:
                y2 -= dy_dyn

        # zera offset dinâmico no backend imediatamente
        self.ctrl._plc_motion_backend.apply_dynamic_offset(0, 0)

        # valida dentro da área da mesa
        if callable(self._validate_position):
            err = self._validate_position(x, y2, y1, z)
            if err:
                QMessageBox.warning(self, "Fora dos limites", err)
                return

        # ------------------------ 3. aplica ao objeto -----------------
        pos              = positions[row]      # objeto existente
        pos.x, pos.y1, pos.y2, pos.z = x, y1, y2, z
        pos.camera_params = new_meta
        setattr(pos, "meta", new_meta)         # retro-compat.

        # ------------------------ 4. refresca lista ------------------
        self.inspect_widget._renumber_items()
        self.inspect_widget._renumber_items()
        self.inspect_widget.btn_edit.setEnabled(False)
        # notifica sequence widget
        self.seq_widget.set_positions(self._to_model())
        self.ctrl.log(f"■ Posição {pos.name} atualizada: "
                      f"X={x:.0f}  Y={'Y1' if self.y_axis=='Y1' else 'Y2'}="
                      f"{y1 if self.y_axis=='Y1' else y2:.0f}  Z={z:.0f}")
    
    # -------- barcode recebido DURANTE A EXECUÇÃO --------------------
    def _on_bc_runtime(self, ok: bool, x:int, y:int, w:int, h:int, text:str):
        from PyQt6.QtGui import QColor
        color = Qt.GlobalColor.green if ok else Qt.GlobalColor.red
        self._bc_match = ((x, y, w, h), QColor(color), time.time())
        if ok:
            self.ctrl.log(f"■ Barcode={text}")

    # ==================================================================
    #  DUAS LINHAS →  duplo-clique na lista “Posições de Inspeção”
    # ==================================================================
    def _on_position_double_clicked(self, item):
        """
        Pré-visualiza ponto para EDIÇÃO reutilizando o mesmo runner de
        execução:
            • mini-sequência = [todos fiducials] + [ponto clicado]
            • runner aplica apply_dynamic_offset() internamente;
            • câmera chega EXACTAMENTE ao ponto corrigido;
            • botão “Editar” é habilitado se a leitura dos fiduciais
              tiver sucesso.
        """
        row = self.inspect_widget.list_widget.row(item)
        try:
            clicked_pos = self.inspect_widget.positions()[row]
        except IndexError:
            return

        # ‑-- monta micro-lista: todos fiducials (na ordem) + ponto alvo
        fid_points = [p for p in self.inspect_widget.positions()
                      if (p.meta or {}).get('action') == 'fiducial']

        # se não houver fiducial basta mover diretamente (fluxo antigo)
        if not fid_points:
            self._apply_offset_and_move(item, (0, 0))
            return

        # ------------------------------------------------------------------
        # O ponto clicado NÃO deve executar nenhuma ação real (dot / barcode…)
        # na pré-visualização – apenas movimentar a cabeça.
        # Criamos uma *cópia* sem campo "action".
        # ------------------------------------------------------------------
        import copy
        clicked_copy         = copy.deepcopy(clicked_pos)
        if isinstance(clicked_copy.meta, dict):
            clicked_copy.meta = clicked_copy.meta.copy()
            clicked_copy.meta.pop("action", None)   # neutraliza

        mini_list = fid_points + [clicked_copy]

        # converte para modelo SequenceRunnerThread (InspectionPosition)
        # --------------------------------------------------------------
        #  CONVERSOR → InspectionPosition
        #     • Usa SOMENTE o eixo físico da mesa (Y1  OU  Y2);
        #       o outro fica = None   →   backend NÃO envia comando.
        # --------------------------------------------------------------
        def _to_ip(p):
            cam = p.meta.copy() if isinstance(p.meta, dict) else None
            if self.y_axis == 'Y1':
                return InspectionPosition(
                    name=p.name,
                    x=p.x,
                    y1=p.y1,
                    y2=None,          # evita “Y2 = 0” que disparava eixo errado
                    z=p.z,
                    camera_params=cam)
            else:                    # Mesa 2
                return InspectionPosition(
                    name=p.name,
                    x=p.x,
                    y2=p.y2,
                    y1=None,
                    z=p.z,
                    camera_params=cam)

        positions_model = [_to_ip(p) for p in mini_list]

        # bloqueia botões enquanto corre
        self.inspect_widget.btn_edit.setEnabled(False)
        self.inspect_widget.btn_remove.setEnabled(False)

        # --------------------------------------------------------------
        #  garante que CameraManager possua método .capture(params)
        #  (SequenceRunnerThread passa um dict ou None)
        # --------------------------------------------------------------
        if not hasattr(self.ctrl.camera_manager, "capture"):
            def _cam_capture(_params=None, cm=self.ctrl.camera_manager):
                """
                Substituto mínimo para CameraManager.capture expected by
                SequenceRunnerThread.  Ignora quaisquer parâmetros e devolve
                o frame BGR ou None.
                """
                ok, frame = (cm._cap.read() if getattr(cm, "_cap", None)
                             else (False, None))
                return frame if ok else None

            setattr(self.ctrl.camera_manager, "capture", _cam_capture)

        # --------------------------------------------------------------
        #  1) Desliga aplicação do offset câmera↔nozzle
        #     (somente CAMERA deve chegar ao ponto, não o nozzle)
        #  2) Runner em modo VIEW  (apply_mode=False)
        # --------------------------------------------------------------
        if hasattr(self.ctrl._plc_motion_backend, "set_offset_mode"):
            self.ctrl._plc_motion_backend.set_offset_mode(False)

        # 3) dispara runner em thread próprio  (apply_mode=False garante
        #    que offset fixo câmera↔nozzle NÃO seja somado)
        # --------------------------------------------------------------
        self._preview_runner = SequenceRunnerThread(
            motion=self.ctrl._plc_motion_backend,
            camera=self.ctrl.camera_manager,
            positions=positions_model,
            apply_mode=False)
        # SequenceRunnerThread.finished  NÃO envia argumentos
        # → callback simplificado
        self._preview_runner.finished.connect(
            lambda it=item: self._preview_finished(it))
        # Se ocorrer erro → aborta edição
        self._preview_runner.error.connect(
            lambda msg, it=item: self._preview_failed(msg, it))
        # -------- FEEDBACK VISUAL (mesma UX do runner principal) ------
        self._preview_runner.fidMatch.connect(self._on_fid_match)
        self._preview_runner.fidClear.connect(
            lambda: setattr(self, "_match_info", None))
        # opcional: barcode (não afeta ponto editado)
        self._preview_runner.bcMatch.connect(self._on_bc_runtime)
        self._preview_runner.bcClear.connect(
            lambda: setattr(self, "_bc_match", None))
        self._preview_runner.start()

    # -------------------------------------------
    def _preview_finished(self, item):
        """
        Callback quando micro-runner concluiu.
        Se OK:
            – habilita Editar/Remover;
            – carrega meta nos widgets;
            – mantém offset dinâmico ativo para o usuário.
        Caso erro (fiducial não encontrado, etc.), aborta edição.
        """
        # offset dinâmico obtido ANTES do runner resetar (ver backend)
        dx, dy = self.ctrl._plc_motion_backend._last_offset
        self.ctrl.log(f"■ Pré-visualização concluída – ΔX={dx}  ΔY={dy}")

        # habilita botões e carrega meta
        self.inspect_widget.btn_edit.setEnabled(True)
        self.inspect_widget.btn_remove.setEnabled(True)
        row = self.inspect_widget.list_widget.row(item)
        pos = self.inspect_widget.positions()[row]
        self._load_meta_to_widgets(pos.meta or {})

        # garante seleção visual (pode ter sido alterada durante runner)
        self.inspect_widget.list_widget.setCurrentItem(item)

    # ---------------------------------------------------------------
    #  Falha na leitura dos fiduciais  →  aborta edição
    # ---------------------------------------------------------------
    def _preview_failed(self, msg: str, item):
        QMessageBox.warning(self, "Fiducial",
                            f"Falha na leitura dos fiduciais:\n{msg}")
        # limpa offset dinâmico
        self.ctrl._plc_motion_backend.apply_dynamic_offset(0, 0)
        # garante que botões permaneçam desativados
        self.inspect_widget.btn_edit.setEnabled(False)
        self.inspect_widget.btn_remove.setEnabled(False)
        # devolve seleção visual ao item (sem edição)
        self.inspect_widget.list_widget.setCurrentItem(item)

    # ---------------------------------------------------------------
    #  Remover posição selecionada
    # ---------------------------------------------------------------
    def _on_remove_clicked(self):
        item = self.inspect_widget.list_widget.currentItem()
        if item is None:
            return
        row = self.inspect_widget.list_widget.row(item)
        try:
            pos = self.inspect_widget.positions()[row]
        except IndexError:
            return

        ret = QMessageBox.question(
            self, "Remover posição",
            f"Deseja remover a posição {pos.name} ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel)
        if ret != QMessageBox.StandardButton.Yes:
            return

        removed = self.inspect_widget.remove_selected()
        if removed:
            # renumeração e refresh já são feitos pelo widget
            self.seq_widget.set_positions(self._to_model())
            self.ctrl.log(f"■ Posição {removed.name} removida.")
        # desabilita botões até novo duplo-clique
        self.inspect_widget.btn_edit.setEnabled(False)
        self.inspect_widget.btn_remove.setEnabled(False)

    # ------------------------------------------------------------------
    def _load_meta_to_widgets(self, meta: dict):
        """Preenche action_selector & widgets com o meta selecionado."""
        act = meta.get("action", "dot")
        self.action_selector.select_action(act)
        if act == "fiducial":
            self.fiducial_cfg.load_from_meta(meta)
        elif act == "barcode":
            self.barcode_cfg.load_from_meta(meta)
        elif act == "inspect":
            self.inspect_cfg.load_from_meta(meta)
        elif act == "dot":
            self.dots_view.select_pattern_by_id(meta.get("dot_id"))

    # ------------------------------------------------------------------
    #  NOVO  –  cria estrutura e salva imagens no ato da adição
    # ------------------------------------------------------------------
    def _on_position_added(self, pos):
        """
        Executado logo após o usuário clicar “Adicionar posição atual”.
        Cria as pastas da região / posição mecânica / w*  e salva:
            – imagem da região completa   (regioes/regiao_<n>/<...>.png)
            – ROI azul de cada janela     (…/w*/referencia/referencia.png)
            – JSON mínimo                 (…/<posicao>_w*.json)
        """
        if not getattr(self.ctrl, "prog_mgr", None):
            # programa ainda não criado (deveria existir)
            return
        meta = pos.meta or {}
        if meta.get("action") != "inspect":
            return
        try:
            # ---------------------- Nomes base -------------------------
            regiao_idx  = self.inspect_widget.positions().index(pos) + 1
            regiao_name = f"regiao_{regiao_idx}"
            # Posição mecânica usa o nome dado pelo ROI editor
            componentes = meta.get("componentes", {})
            region_png  = meta.get("_region_png")
            if region_png:
                np_img = cv2.imdecode(np.frombuffer(region_png, np.uint8),
                                      cv2.IMREAD_COLOR)
                if np_img is not None and np_img.size:
                    self.ctrl.prog_mgr.save_region(
                        regiao_name, Image.fromarray(
                            cv2.cvtColor(np_img, cv2.COLOR_BGR2RGB)))
            # ---------------------- w* e janelas -----------------------
            for posicao_nome, comp_data in componentes.items():
                inspecoes = comp_data.get("inspecoes", [])
                for insp in inspecoes:
                    # crop ROI azul da imagem da região
                    if region_png is None:
                        continue
                    # As coordenadas já vêm em pixels absolutos
                    x, y = insp.get("posicao", (0, 0))
                    w, h = insp.get("tamanho", (0, 0))
                    if w == 0 or h == 0:
                        continue
                    roi_bgr = np_img[y:y+h, x:x+w].copy()
                    if roi_bgr.size == 0:
                        continue
                    roi_pil = Image.fromarray(
                        cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2RGB))
                    w_nome  = insp.get("nome") or insp.get("window_name") \
                              or f"w{inspecoes.index(insp)+1}"
                    # salva estrutura + arquivos
                    self.ctrl.prog_mgr.save_blue_reference(
                        regiao_name,
                        posicao_nome,
                        w_nome,
                        roi_pil,
                        meta=insp      # JSON simples
                    )
        except Exception as exc:
            self.ctrl.log(f"■ Erro ao criar estrutura da posição: {exc}")
        # ------------------------------------------------------------------
        #  NOVO  –  limpa visores ‘Região’ e ‘ROI’ após adicionar INSPEÇÃO
        # ------------------------------------------------------------------
        try:
            if self.inspect_cfg:
                self.inspect_cfg.clear_views()
        except Exception as exc:
            self.ctrl.log(f"■ Erro ao limpar visores de inspeção: {exc}")

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
            # Usa diretamente os módulos importados no topo
            _, buf = cv2.imencode('.png', tmpl)
            b64 = base64.b64encode(buf).decode('ascii')
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
                'componentes': serializable_comp,                
                # ------------------------------------------------------------------
                #  ROI COMPLETA (PNG *bytes*, NÃO base64)
                #  • É apenas um payload temporário para o backend
                #    salvar os .png na árvore de pastas.
                #  • Será removido antes do JSON final, portanto não
                #    aparece no arquivo *.m1 / *.m2.
                # ------------------------------------------------------------------
                '_region_png': (lambda _img=self.inspect_cfg
                                          ._cached_auxiliary_data
                                          .get('region_image'):
                                (None if _img is None else
                                 cv2.imencode('.png', _img)[1].tobytes()))()
            }
        elif key == 'dot':
            pat = self.dots_view.current_pattern()
            if pat is None:
                return None      # impede adicionar sem seleção
            return {
                'action':   'dot',
                'dot_id':   pat.id,
                'dot_name': pat.name,
                'dot_qty':  pat.qty,
                # freq default será lida da aba Config Registradores
                'dot_freq_hz': self.ctrl.findChild(QSpinBox,
                                      "cfg_spin_D24000_FREQ").value()
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
            # ----------------------------------------------------------
            #  GUARDA META COMPLETA NO InspectionPosition
            #
            #  • Precisamos do campo dot_qty no runner para escrever
            #    D24100, portanto não pode ser descartado aqui.
            #  • camera_params agora recebe **todo** o dict meta
            #    (se existir) preservando "action", "dot_qty", etc.
            # ----------------------------------------------------------
            cam_params = (p.meta.copy()              # dict completo
                          if isinstance(p.meta, dict)
                          else None)
            # Salva somente X, Y (desta mesa) e Z
            if self.y_axis == 'Y1':
                out.append(InspectionPosition(name=p.name,
                                              x=p.x,
                                              y1=p.y1, y2=None,
                                              z=p.z,
                                              camera_params=cam_params))
            else:
                out.append(InspectionPosition(name=p.name,
                                              x=p.x,
                                              y2=p.y2, y1=None,
                                              z=p.z,
                                              camera_params=cam_params))
        return out
