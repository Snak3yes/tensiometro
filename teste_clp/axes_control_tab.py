# axes_control_tab.py
"""
Widget completo de controle de eixos (quatro eixos + inspeção +
salvar / carregar + sequência).  Reaproveita toda a lógica já existente
no MultiAxisMotorController; somente a parte visual fica aqui.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, QSizePolicy,
    QListWidget, QLabel, QGroupBox, QProgressBar,
    QPushButton
)
from mesa_plot_widget import MesaPlotWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap

from inspection_config_widget import AspectRatioLabel
from movement_controls_widget import MovementControlsWidget
from plate_flow import FlowState
from position_status_widget  import PositionStatusWidget
from inspection_positions_widget import InspectionPositionsWidget
from program_io_widget      import ProgramIOWidget
from positions_backend      import InspectionPositionsBackend
from sequence_control       import SequenceControlWidget
from sequence_control       import InspectionPosition                


class AxesControlTab(QWidget):
    """
    Aba completa de controle.  Recebe a instância do controlador principal
    (MultiAxisMotorController) para encaminhar sinais / slots.
    Se `primary=True`, alguns atributos comuns (pos_widget, mov_widget …)
    são expostos no controlador para que o código já existente continue
    funcionando sem alteração.
    """
    def __init__(self, controller, *, primary: bool = False):
        super().__init__()
        self.ctrl = controller
        # initialize per-mesa production counters and timers
        self._count_m1 = 0
        self._count_m2 = 0
        self._times_m1: list[float] = []
        self._times_m2: list[float] = []
        self.primary = primary
        self._build_ui()

    # ------------------------------------------------------------------
    #  CONSTRUÇÃO
    # ------------------------------------------------------------------
    def _build_ui(self):
        """Copia exatamente a UI usada anteriormente."""
        grid = QGridLayout(self)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(0)
        grid.setVerticalSpacing(0)

        # --------------------- (COLUNA ESQUERDA REMOVIDA) -------------
        # Os controles auxiliares ficam apenas nas abas de Mesa 1/2.

        # ------------------------- COLUNA CENTRAL (85 %) ---------------
        # ---------- VISUALIZAÇÃO DAS MESAS ----------------------------
        center_top = QFrame(objectName="centerTop")
        grid.addWidget(center_top, 0, 0)
        hplot = QHBoxLayout(center_top)
        hplot.setContentsMargins(2,2,2,2)
        hplot.setSpacing(4)
        # Para cada “mesa” teremos agora um container com 2 colunas:
        #   • Coluna 0 (stretch=3): plotagem de pontos
        #   • Coluna 1 (stretch=2): área livre para novas funcionalidades
        # Passa calibração steps/mm  → evita “esticamento” no eixo X
        self.plot_m1 = MesaPlotWidget(
            self.ctrl.table_limits[1],
            steps_per_mm=self.ctrl.steps_per_mm,
            y_axis='Y1',
            title="Mesa 1"
        )
        self.plot_m2 = MesaPlotWidget(
            self.ctrl.table_limits[2],
            steps_per_mm=self.ctrl.steps_per_mm,
            y_axis='Y2',
            title="Mesa 2"
        )
        # — Mesa 1
        m1_container = QWidget()
        m1_layout = QHBoxLayout(m1_container)
        # coluna de plotagem
        m1_layout.setContentsMargins(0,0,0,0)
        m1_layout.setSpacing(2)
        # coluna de plotagem
        m1_layout.addWidget(self.plot_m1)
        # coluna livre
        m1_blank = QFrame()
        m1_blank.setStyleSheet("QFrame { background-color:#303030; }")
        m1_blank.setSizePolicy(QSizePolicy.Policy.Expanding,
                                QSizePolicy.Policy.Expanding)
        m1_layout.addWidget(m1_blank)
        # ■■ agrupa botões de Mesa 1 dentro de um QGroupBox ■■■■■■■■■■■■■
        m1_btn_layout = QVBoxLayout(m1_blank)
        group_m1_actions = QGroupBox("Ações")
        group_m1_layout  = QVBoxLayout(group_m1_actions)
        btn_enviar_m1    = QPushButton("Enviar")
        # conecta “Enviar Mesa 1” → pulso M42
        btn_enviar_m1.clicked.connect(lambda: self.ctrl._pulse_coil("M42"))
        btn_retornar_m1  = QPushButton("Retornar")
        # guarda para controlar estado
        self.btn_retornar_m1 = btn_retornar_m1
        btn_abrirproj_m1 = QPushButton("Abrir Projeto")
        group_m1_layout.addWidget(btn_enviar_m1)
        group_m1_layout.addWidget(btn_retornar_m1)
        btn_retornar_m1.clicked.connect(lambda: self.ctrl.flow_mesa1._return_after_error())
        group_m1_layout.addWidget(btn_abrirproj_m1)
        group_m1_layout.addStretch()
        m1_btn_layout.addWidget(group_m1_actions)
        # ── limita altura do groupbox 'Ações' para caber só os botões ──
        group_m1_actions.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Maximum
        )
        group_m1_actions.setMaximumHeight(group_m1_actions.sizeHint().height())
        # conecta botão "Abrir Projeto" de Mesa 1
        btn_abrirproj_m1.clicked.connect(lambda: self._open_project_for_mesa(1))
        # ■■ GroupBox para exibir contagem e tempos (Mesa 1) ■■
        group_m1_stats = QGroupBox("Estatísticas de Produção")
        stats_m1_layout = QHBoxLayout(group_m1_stats)
        # – coluna esquerda: contador de placas
        vcount_m1 = QVBoxLayout()
        vcount_m1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vcount_m1.addWidget(QLabel("Placas Concluídas:"), alignment=Qt.AlignmentFlag.AlignCenter)
        self.lbl_count_m1 = QLabel("0")
        self.lbl_count_m1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vcount_m1.addWidget(self.lbl_count_m1)
        # – coluna direita: tempos
        vtime_m1 = QVBoxLayout()
        vtime_m1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vtime_m1.addWidget(QLabel("Tempo Total (s):"), alignment=Qt.AlignmentFlag.AlignCenter)
        self.lbl_time_elapsed_m1 = QLabel("0 s")
        self.lbl_time_elapsed_m1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vtime_m1.addWidget(self.lbl_time_elapsed_m1)
        vtime_m1.addWidget(QLabel("Tempo Médio (s):"), alignment=Qt.AlignmentFlag.AlignCenter)
        self.lbl_time_avg_m1 = QLabel("0 s")
        self.lbl_time_avg_m1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vtime_m1.addWidget(self.lbl_time_avg_m1)
        # adiciona as duas colunas ao layout principal
        stats_m1_layout.addLayout(vcount_m1)
        stats_m1_layout.addLayout(vtime_m1)
        m1_btn_layout.addWidget(group_m1_stats)
        m1_btn_layout.addStretch()
        # proporções internas (3:2)
        m1_layout.setStretch(0, 3)
        m1_layout.setStretch(1, 2)
        hplot.addWidget(m1_container)

        # — Mesa 2
        m2_container = QWidget()
        # coluna de plotagem
        m2_layout = QHBoxLayout(m2_container)
        m2_layout.setContentsMargins(0,0,0,0)
        m2_layout.setSpacing(2)
        # coluna de plotagem
        m2_layout.addWidget(self.plot_m2)
        # coluna livre
        m2_blank = QFrame()
        m2_blank.setStyleSheet("QFrame { background-color:#303030; }")
        m2_blank.setSizePolicy(QSizePolicy.Policy.Expanding,
                                QSizePolicy.Policy.Expanding)
        m2_layout.addWidget(m2_blank)
        # ■■ agrupa botões de Mesa 2 dentro de um QGroupBox ■■■■■■■■■■■■■
        m2_btn_layout = QVBoxLayout(m2_blank)
        group_m2_actions = QGroupBox("Ações")
        group_m2_layout  = QVBoxLayout(group_m2_actions)
        btn_enviar_m2    = QPushButton("Enviar")
        # conecta “Enviar Mesa 2” → pulso M43
        btn_enviar_m2.clicked.connect(lambda: self.ctrl._pulse_coil("M43"))
        btn_retornar_m2  = QPushButton("Retornar")
        # guarda para controlar estado
        self.btn_retornar_m2 = btn_retornar_m2
        btn_abrirproj_m2 = QPushButton("Abrir Projeto")
        group_m2_layout.addWidget(btn_enviar_m2)
        group_m2_layout.addWidget(btn_retornar_m2)
        btn_retornar_m2.clicked.connect(lambda: self.ctrl.flow_mesa2._return_after_error())
        group_m2_layout.addWidget(btn_abrirproj_m2)
        group_m2_layout.addStretch()
        m2_btn_layout.addWidget(group_m2_actions)
        # ── limita altura do groupbox 'Ações' para caber só os botões ──
        group_m2_actions.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Maximum
        )
        group_m2_actions.setMaximumHeight(group_m2_actions.sizeHint().height())
        # conecta botão "Abrir Projeto" de Mesa 2
        btn_abrirproj_m2.clicked.connect(lambda: self._open_project_for_mesa(2))
        # ■■ GroupBox para exibir contagem e tempos (Mesa 2) ■■
        group_m2_stats = QGroupBox("Estatísticas de Produção")
        stats_m2_layout = QHBoxLayout(group_m2_stats)
        # – coluna esquerda: contador de placas
        vcount_m2 = QVBoxLayout()
        vcount_m2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vcount_m2.addWidget(QLabel("Placas Concluídas:"), alignment=Qt.AlignmentFlag.AlignCenter)
        self.lbl_count_m2 = QLabel("0")
        self.lbl_count_m2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vcount_m2.addWidget(self.lbl_count_m2)
        # – coluna direita: tempos
        vtime_m2 = QVBoxLayout()
        vtime_m2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vtime_m2.addWidget(QLabel("Tempo Total (s):"), alignment=Qt.AlignmentFlag.AlignCenter)
        self.lbl_time_elapsed_m2 = QLabel("0 s")
        self.lbl_time_elapsed_m2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vtime_m2.addWidget(self.lbl_time_elapsed_m2)
        vtime_m2.addWidget(QLabel("Tempo Médio (s):"), alignment=Qt.AlignmentFlag.AlignCenter)
        self.lbl_time_avg_m2 = QLabel("0 s")
        self.lbl_time_avg_m2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vtime_m2.addWidget(self.lbl_time_avg_m2)
        # adiciona as duas colunas ao layout principal
        stats_m2_layout.addLayout(vcount_m2)
        stats_m2_layout.addLayout(vtime_m2)
        m2_btn_layout.addWidget(group_m2_stats)
        m2_btn_layout.addStretch()
        # proporções internas (3:2)
        m2_layout.setStretch(0, 3)
        m2_layout.setStretch(1, 2)
        hplot.addWidget(m2_container)

        # --------------------- COLUNA DIREITA (15 %) -------------------
        right_col = QVBoxLayout()

        # ■■ Preview de vídeo da câmera – dentro de um GroupBox ■■■■■■
        # Uses our AspectRatioLabel (4:3 by default) to respect camera ratio
        self.camera_label = AspectRatioLabel(aspect_ratio=4/3)
        self.camera_label.setStyleSheet(
            "QLabel { background-color: black; }"
        )
        # permite expandir até a largura da coluna
        self.camera_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )
        # ── encapsula o label de vídeo dentro de um QGroupBox ───────
        camera_group = QGroupBox("Câmera")
        camera_layout = QVBoxLayout(camera_group)
        camera_layout.setContentsMargins(0, 0, 0, 0)
        camera_layout.addWidget(self.camera_label)
        right_col.addWidget(camera_group)
        # hook up live frames
        if hasattr(self.ctrl, "camera_manager"):
            self.ctrl.camera_manager.frameReady.connect(
                self._update_camera_frame
            )
        # ── then the existing movement controls ─────────────────────
        self.mov_widget = MovementControlsWidget()
        right_col.addWidget(self.mov_widget)

        # --------------------------------------------------------------
        #  REMOVIDO O GROUPBOX “Posições de Inspeção” APENAS NESTA ABA
        #  – o widget continua existindo (para não quebrar callbacks
        #    internos do SequenceControl), mas fica oculto da UI.
        # --------------------------------------------------------------
        self.inspect_widget = InspectionPositionsWidget(
            get_current_position=self.ctrl._get_current_position_dict)
        self.inspect_widget.hide()          # invisível na aba

        # (não é adicionado ao layout right_col)

        # Aba de controle global → utiliza extensão genérica .json
        backend = InspectionPositionsBackend(self.inspect_widget)
        file_filter = "Programas (*.json)"
        self.prog_widget = ProgramIOWidget(
            backend,
            file_filter=file_filter,
            default_suffix=".json",
            default_dir=self.ctrl.projects_dir
        )
        right_col.addWidget(self.prog_widget)
        # Esconde grupo de botões (passará a ser acessado via menu)
        self.prog_widget.hide()

        self.seq_widget = SequenceControlWidget(
            motion=self.ctrl._plc_motion_backend,  # criado no controlador
            camera=None
        )
        # ------------------------------------------------------------
        #  Libera e exibe os botões Pause / Stop SOMENTE nesta aba
        # ------------------------------------------------------------
        self.seq_widget._btn_stop.show()
        self.seq_widget._btn_pause.show()
        # -----------------------------------------------------------------
        #  A B A  “ C O N T R O L E  D E  E I X O S ”
        #  Oculta os elementos VISUAIS que já existem no espelho inferior:
        #      – barra de progresso _progress
        #      – label de status     _status
        #      – label do código     _lbl_bc
        #  Eles continuam existindo (sinais/valores) e as demais abas
        #  permanecem inalteradas – apenas não aparecem aqui.
        # -----------------------------------------------------------------
        self.seq_widget._progress.setVisible(False)
        self.seq_widget._status.setVisible(False)
        self.seq_widget._lbl_bc.setVisible(False)
        # ------------------------------------------------------------------
        #  AJUSTE “START”
        #  – renomeia o botão e mantém o _toggle_ interno com Stop/Pause.
        #    Após a lógica interna (_start) ser executada, também
        #    chamamos start_global_cycle() para preparar as mesas.
        # ------------------------------------------------------------------
        # ------------------------------------------------------------------
        #  BOTÕES  Start / Pause / Stop  (ciclo GERAL)
        #  • Start   → ativa ciclo global  +  faz toggle dos botões
        #  • Pause   → envia pause/resume  +  ajusta texto
        #  • Stop    → encerra ciclo       +  refaz toggle
        # ------------------------------------------------------------------
        self.seq_widget._btn_execute.setText("Start")

        # ------------------------------------------------------------
        # 1) Remove TODAS as conexões anteriores dos botões
        #    (PyQt6: disconnect() sem args → remove tudo)
        # ------------------------------------------------------------
        for sig in (self.seq_widget._btn_execute.clicked,
                    self.seq_widget._btn_stop.clicked,
                    self.seq_widget._btn_pause.clicked):
            try:
                sig.disconnect()          # limpa ligações antigas
            except TypeError:
                print("AxesControlTab: _build_ui() - "
                      "erro ao desconectar sinal. ")
                # nenhum slot ligado → ignora
                pass

        # 2) Conecta aos novos controladores locais
        self.seq_widget._btn_execute.clicked.connect(self._on_global_start)
        self.seq_widget._btn_stop.clicked.connect(self._on_global_stop)
        self.seq_widget._btn_pause.clicked.connect(self._on_global_pause)

        # 3) Estado inicial
        self.seq_widget._btn_stop.setEnabled(False)
        self.seq_widget._btn_pause.setEnabled(False)

        # Mantém o botão Stop VISÍVEL para permitir o toggle.
        self.seq_widget._btn_stop.show()

        right_col.addWidget(self.seq_widget)
        right_col.addStretch()

        # ── timer para habilitar/desabilitar os botões “Retornar” ──
        self._return_timer = QTimer(self)
        self._return_timer.timeout.connect(self._update_return_buttons)
        self._return_timer.start(200)

        right_col.addStretch()
        # direita – faz o right_wrap ocupar TODA a altura (duas linhas)
        right_wrap = QWidget(); right_wrap.setLayout(right_col)
        grid.addWidget(right_wrap, 0, 1, 2, 1)

        # ------------------------------ LINHA INFERIOR -----------------
        # só o bottom_placeholder na coluna 0
        bottom_placeholder = QFrame(objectName="centerBottom")
        bottom_placeholder = QFrame(objectName="centerBottom")
        # ----------------------------------------------------------
        #  Fundo igual ao painel de cima (cinza-escuro)
        # ----------------------------------------------------------
        bottom_placeholder.setStyleSheet(
            "QFrame#centerBottom { background-color:#303030; }")
        bottom_placeholder.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding)

        bottom_lay = QHBoxLayout(bottom_placeholder)
        bottom_lay.setContentsMargins(0, 0, 0, 0)
        bottom_lay.setSpacing(0)

        def _make_half() -> QFrame:
            half = QFrame()
            # mesma cor do canvas onde são plotados os pontos
            half.setStyleSheet("QFrame { background-color:#303030; }")
            half.setSizePolicy(QSizePolicy.Policy.Expanding,
                               QSizePolicy.Policy.Expanding)
            return half

        left_half  = _make_half()
        right_half = _make_half()

        # ----------------------------------------------------------
        #  ESPELHO DAS POSIÇÕES  –  MESA 1
        # ----------------------------------------------------------
        left_half_lay = QVBoxLayout(left_half)
        left_half_lay.setContentsMargins(4, 4, 4, 4)

        self.mirror_m1_label = QLabel("Posições de Inspeção – Mesa 1")
        self.mirror_m1_label.setStyleSheet(
            "QLabel { color:#ECEFF1; font-weight:bold; }")

        # --- lista + espaço vazio (60 % | 40 %) --------------------
        self.mirror_m1_list = QListWidget()
        self.mirror_m1_list.setStyleSheet(
            "QListWidget { background:#424242; color:#ECEFF1; }")
        self.mirror_m1_list.setMinimumHeight(140)

        m1_row = QHBoxLayout()
        m1_row.setContentsMargins(0, 0, 0, 0)
        m1_row.addWidget(self.mirror_m1_list)
        self._m1_blank = QFrame()                  # área vazia 40 %
        self._m1_blank.setStyleSheet("QFrame { background:#303030; }")
        m1_row.addWidget(self._m1_blank)
        m1_row.setStretchFactor(self.mirror_m1_list, 3)   # ≈60 %
        m1_row.setStretchFactor(self._m1_blank,      2)   # ≈40 %
        # ===============  B L O C O  –  CONTROLE DE SEQUÊNCIA (M1) ===============
        self._seq_m1_box = QGroupBox("Controle de Sequência")
        vseq1 = QVBoxLayout(self._seq_m1_box)
        self.lbl_m1_fid   = QLabel("Fiducial: —")
        self.pb_m1        = QProgressBar(); self.pb_m1.setValue(0)
        self.lbl_m1_stat  = QLabel("Status: —")
        self.lbl_m1_code  = QLabel("Código: —")
        for w in (self.lbl_m1_fid, self.pb_m1, self.lbl_m1_stat, self.lbl_m1_code):
            vseq1.addWidget(w)
        vseq1.addStretch()
        self._m1_blank_layout = QVBoxLayout(self._m1_blank); 
        self._m1_blank_layout.setContentsMargins(0,0,0,0)
        self._m1_blank_layout.addWidget(self._seq_m1_box)
        left_half_lay.addWidget(self.mirror_m1_label)
        left_half_lay.addLayout(m1_row, 1)

        # ----------------------------------------------------------
        #  ESPELHO DAS POSIÇÕES  –  MESA 2   (lado direito)
        # ----------------------------------------------------------
        right_half_lay = QVBoxLayout(right_half)
        right_half_lay.setContentsMargins(4, 4, 4, 4)

        self.mirror_m2_label = QLabel("Posições de Inspeção – Mesa 2")
        self.mirror_m2_label.setStyleSheet(
            "QLabel { color:#ECEFF1; font-weight:bold; }")

        self.mirror_m2_list = QListWidget()
        self.mirror_m2_list.setStyleSheet(
            "QListWidget { background:#424242; color:#ECEFF1; }")
        self.mirror_m2_list.setMinimumHeight(140)

        m2_row = QHBoxLayout()
        m2_row.setContentsMargins(0, 0, 0, 0)
        m2_row.addWidget(self.mirror_m2_list)
        self._m2_blank = QFrame()
        self._m2_blank.setStyleSheet("QFrame { background:#303030; }")
        m2_row.addWidget(self._m2_blank)
        m2_row.setStretchFactor(self.mirror_m2_list, 3)
        m2_row.setStretchFactor(self._m2_blank,      2)
        # ===============  B L O C O  –  CONTROLE DE SEQUÊNCIA (M2) ===============
        self._seq_m2_box = QGroupBox("Controle de Sequência")
        vseq2 = QVBoxLayout(self._seq_m2_box)
        self.lbl_m2_fid   = QLabel("Fiducial: —")
        self.pb_m2        = QProgressBar(); self.pb_m2.setValue(0)
        self.lbl_m2_stat  = QLabel("Status: —")
        self.lbl_m2_code  = QLabel("Código: —")
        for w in (self.lbl_m2_fid, self.pb_m2, self.lbl_m2_stat, self.lbl_m2_code):
            vseq2.addWidget(w)
        vseq2.addStretch()
        self._m2_blank_layout = QVBoxLayout(self._m2_blank); 
        self._m2_blank_layout.setContentsMargins(0,0,0,0)
        self._m2_blank_layout.addWidget(self._seq_m2_box)

        right_half_lay.addWidget(self.mirror_m2_label)
        right_half_lay.addLayout(m2_row, 1)

        # As conexões dependem de controller.mesa_tabs,
        # que só estará disponível APÓS o controlador criar
        # as abas Mesa-1 / Mesa-2.  Programamos para o próximo
        # ciclo do event-loop.
        QTimer.singleShot(0, self._setup_mirror_connections)

        # divisor visual (1 px) para evidenciar as duas colunas
        divider = QFrame()
        divider.setFixedWidth(1)
        divider.setStyleSheet("QFrame { background-color:#505050; }")

        bottom_lay.addWidget(left_half,  1)
        bottom_lay.addWidget(divider)
        bottom_lay.addWidget(right_half, 1)

        # ---------------- LINHA INFERIOR ------------------
        # agora a cena inferior central ocupa 100% da coluna 0;
        # o spacer da direita permanece na coluna 1.
        grid.addWidget(bottom_placeholder, 1, 0)
        # --------- proporções (colunas 85|15, linhas 70|30) ---------
        grid.setColumnStretch(0, 85)
        grid.setColumnStretch(1, 15)
        grid.setRowStretch(0, 7)
        grid.setRowStretch(1, 3)

        # -------------------- CONEXÕES DE SINAIS -----------------------
        self.mov_widget.stepMoveRequested.connect(
            self.ctrl._on_step_move_requested)
        self.mov_widget.jogStart.connect(self.ctrl._on_widget_jog_start)
        self.mov_widget.jogStop.connect(self.ctrl._on_widget_jog_stop)
        self.mov_widget.goToZeroRequested.connect(self.ctrl._on_go_to_zero)
        self.mov_widget.emergencyStopToggled.connect(
            lambda e: self.ctrl.emergency_stop() if e else None)        

        # Como o widget está oculto, as conexões abaixo só são
        # necessárias caso outro código o utilize programaticamente.
        self.inspect_widget.positionAdded.connect(
            lambda _: self.seq_widget.set_positions(self._to_model()))
        self.inspect_widget.positionRemoved.connect(
            lambda _: self.seq_widget.set_positions(self._to_model()))
        self.prog_widget.fileLoaded.connect(
            lambda _: self.seq_widget.set_positions(self._to_model()))
        
        

        # logs salvar / carregar
        self.prog_widget.fileLoaded.connect(
            lambda f: self.ctrl.log(f"Programa carregado de: {f}"))
        self.prog_widget.fileSaved.connect(
            lambda f: self.ctrl.log(f"Programa salvo em: {f}"))

        # ---------- expõe widgets principais no controlador ------------
        if self.primary:
            self.ctrl.mov_widget  = self.mov_widget
            self.ctrl.inspect_widget = self.inspect_widget
            self.ctrl.prog_io_widget = self.prog_widget
            self.ctrl.seq_widget = self.seq_widget
            # feedback ciclo global → garante reset dos botões
            if hasattr(self.ctrl, "globalCycleFinished"):
                self.ctrl.globalCycleFinished.connect(
                    lambda: self._toggle_buttons(start_enabled=True))
            # expõe gráficos
            self.ctrl.mesa_plot_widgets = {1: self.plot_m1,
                                           2: self.plot_m2}
    # ------------------------------------------------------------------
    #  S L O T S   p/  c i c l o   g e r a l
    # ------------------------------------------------------------------
    def _toggle_buttons(self, *, start_enabled: bool):
        """Liga/desliga Start  x  Pause/Stop."""
        self.seq_widget._btn_execute.setEnabled(start_enabled)
        self.seq_widget._btn_stop.setEnabled(not start_enabled)
        self.seq_widget._btn_pause.setEnabled(not start_enabled)
        if start_enabled:
            self.seq_widget._btn_pause.setText("Pause")

    def _on_global_start(self):
        """Aciona ciclo geral + desabilita botão Start."""
        # 1) Chama start_global_cycle (exibe warning se não houver programa)
        if hasattr(self.ctrl, "start_global_cycle"):
            self.ctrl.start_global_cycle()
        # 2) Só se o ciclo realmente foi ativado é que desabilitamos Start
        #    e enviamos o pulso M40; caso contrário, nada muda na UI nem no CLP.
        if getattr(self.ctrl, "_global_cycle_active", False):
            # Desabilita Start e ativa Stop/Pause
            self._toggle_buttons(start_enabled=False)
            # Pulso momentâneo em M40 para sinalizar Start global
            if hasattr(self.ctrl, "_pulse_coil"):
                self.ctrl._pulse_coil("M40")

    def _on_global_stop(self):
        """Pede parada do ciclo geral e restabelece botão Start."""
        # Pulso momentâneo em M41 para sinalizar Stop global
        if hasattr(self.ctrl, "_pulse_coil"):
            self.ctrl._pulse_coil("M41")
        if hasattr(self.ctrl, "stop_global_cycle"):
            # desliga flag de ciclo geral
            self.ctrl.stop_global_cycle()
        # ── solicita parada dos runners em execução nas mesas ────────
        # quem já estiver no meio de uma sequência terminará o ponto atual
        # e abortará o restante da sequência.
        for tab in getattr(self.ctrl, "mesa_tabs", {}).values():
            seqw = getattr(tab, "seq_widget", None)
            if seqw and getattr(seqw, "_runner", None) and seqw._runner.isRunning():
                seqw._stop()
        # ── estrela: retorna todas as mesas ao operador ───────────
        # Depois de parar o ciclo global, força cada PlateFlowManager
        # a devolver a placa (movendo Y→limite+ e limpando estado).
        for mgr in (getattr(self.ctrl, 'flow_mesa1', None),
                    getattr(self.ctrl, 'flow_mesa2', None)):
            if mgr:
                try:
                    mgr._return_after_error()
                except Exception as exc:
                    # registra falha sem interromper a UI
                    self.ctrl.log(f"■ Falha ao devolver Mesa {getattr(mgr, '_mesa', '?')}: {exc}")
        # Reativa Start e desabilita Stop/Pause
        self._toggle_buttons(start_enabled=True)

    def _on_global_pause(self):
        """Alterna pausa/continuação do ciclo geral."""
        if hasattr(self.ctrl, "pause_global_cycle"):
            self.ctrl.pause_global_cycle()
        # toggling do próprio texto/estado

        if self.seq_widget._btn_pause.text() == "Pause":
            self.seq_widget._btn_pause.setText("Continuar")
            self.seq_widget._status.setText("Pausado")
        else:
            self.seq_widget._btn_pause.setText("Pause")
            self.seq_widget._status.setText("Executando…")

    def _open_project_for_mesa(self, mesa_id: int):
        """
        Abre o diálogo ‘Abrir Projeto…’ para a mesa especificada,
        exatamente como se você fosse na aba Mesa <n> e clicasse
        em Arquivo → Abrir Projeto….
        """
        tab = getattr(self.ctrl, "mesa_tabs", {}).get(mesa_id)
        if not tab or not hasattr(tab, "prog_widget"):
            return
        # abre o diálogo de Abrir Projeto na própria aba, sem trocar de aba
        tab.prog_widget._on_load_clicked()

    # --------- helper: converte lista p/ SequenceControl --------------
    def _to_model(self):
        lst = []
        for p in self.inspect_widget.positions():
            lst.append(
                InspectionPosition(
                    name=p.name,
                    x=p.x, y2=p.y2, y1=p.y1, z=p.z
                )
            )
        return lst
    
    def _update_camera_frame(self, img):
        """Receive QImage frames and display scaled in camera_label."""
        pix = QPixmap.fromImage(img).scaled(
            self.camera_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.camera_label.setPixmap(pix)

    def _update_return_buttons(self):
        """
        Ativa ou desativa os botões “Retornar”:
        – habilita enquanto o fluxo da mesa não estiver em IDLE,
        – desabilita em IDLE (mesa no limite positivo).
        """
        # Mesa 1 – habilita “Retornar” apenas enquanto estiver em fila
        mgr1 = getattr(self.ctrl, 'flow_mesa1', None)
        if mgr1 and mgr1._state is FlowState.QUEUED:
            self.btn_retornar_m1.setEnabled(True)
        else:
            self.btn_retornar_m1.setEnabled(False)
        # Mesa 2 – habilita “Retornar” apenas enquanto estiver em fila
        mgr2 = getattr(self.ctrl, 'flow_mesa2', None)
        if mgr2 and mgr2._state is FlowState.QUEUED:
            self.btn_retornar_m2.setEnabled(True)
        else:
            self.btn_retornar_m2.setEnabled(False)
    
    # -----------------------------------------------------------------
    #            S I N C  ■  M e s a   1   →   E s p e l h o
    # -----------------------------------------------------------------
    def _sync_mesa1_positions(self):
        """
        Copia as posições da aba “Mesa 1” para a lista espelhada
        exibida na parte inferior da aba “Controle de Eixos”.
        """
        try:
            pts = self.ctrl.mesa_tabs[1].inspect_widget.positions()
        except Exception:
            pts = []
        self.mirror_m1_list.blockSignals(True)
        self.mirror_m1_list.clear()
        for p in pts:
            self.mirror_m1_list.addItem(
                f"{p.name}.  X={p.x:.0f}  Y={p.y1:.0f}  Z={p.z:.0f}"
            )
        # mantém seleção actual
        row_sel = self.ctrl.mesa_tabs[1].inspect_widget.list_widget.currentRow()
        if row_sel >= 0 and row_sel < self.mirror_m1_list.count():
            self.mirror_m1_list.setCurrentRow(row_sel)
        self.mirror_m1_list.blockSignals(False)

    # -----------------------------------------------------------------
    #  Conecta-se aos sinais da aba Mesa-1 depois que ela existir
    # -----------------------------------------------------------------
    def _setup_mirror_connections(self):
        mesa1_tab = getattr(self.ctrl, "mesa_tabs", {}).get(1)
        if mesa1_tab is None:          # ainda não criado
            return
        m1w = mesa1_tab.inspect_widget
        for sig in (m1w.positionAdded,
                    m1w.positionRemoved,
                    m1w.positionInserted):
            sig.connect(lambda _=None: self._sync_mesa1_positions())
        mesa1_tab.prog_widget.fileLoaded.connect(
            lambda _=None: self._sync_mesa1_positions())
        # -------------------------------------------------------------
        #  SINCRONIZAÇÃO DO INDICADOR DE SELEÇÃO
        #  – sempre que o usuário (ou o SequenceRunner) mudar a linha
        #    selecionada na QListWidget da Mesa 1, o espelho na aba
        #    “Controle de Eixos” realça a mesma linha.
        # -------------------------------------------------------------
        mesa1_tab.inspect_widget.list_widget.currentRowChanged.connect(
            self._mirror_select_row)
        # -------- conexões de feedback (Mesa 1) ------------------------
        m1_seq = mesa1_tab.seq_widget
        m1_seq.fidMatch.connect(lambda sim,ok,x,y,w,h: self.lbl_m1_fid.setText(
            f"Fiducial: {'OK' if ok else 'Fail'} ({sim:.1f}%)"))
        m1_seq.fidClear.connect(lambda: self.lbl_m1_fid.setText("Fiducial: —"))
        # ────── SINCRONIZAÇÃO DA BARRA DE PROGRESSO (Mesa-1) ──────
        # Usa EXACTAMENTE o mesmo QProgressBar interno do SequenceControlWidget
        # – qualquer alteração de faixa ou valor será espelhada.
        # ────── SINCRONIZAÇÃO DA BARRA DE PROGRESSO (Mesa-1) ──────
        # QProgressBar não possui ‘rangeChanged’ → copiamos o intervalo
        # imediatamente antes de cada execução e sempre que as posições
        # forem alteradas.
        m1_seq._progress.valueChanged.connect(self.pb_m1.setValue)
        # antes de iniciar
        m1_seq._btn_execute.clicked.connect(
            lambda _=False, s=m1_seq: self._sync_progress_range(self.pb_m1, s))
        # quando a lista de pontos muda
        mesa1_tab.inspect_widget.positionAdded.connect(
            lambda _=None, s=m1_seq: self._sync_progress_range(self.pb_m1, s))
        mesa1_tab.inspect_widget.positionRemoved.connect(
            lambda _=None, s=m1_seq: self._sync_progress_range(self.pb_m1, s))
        # seq encerrada → garante barra completa
        m1_seq.sequenceFinished.connect(lambda: self.pb_m1.setValue(self.pb_m1.maximum()))
        m1_seq.sequenceError.connect(  lambda _msg: self.pb_m1.setValue(self.pb_m1.maximum()))
        m1_seq.sequenceFinished.connect(lambda: self.lbl_m1_stat.setText("Status: Concluído"))
        # increment Mesa 1 count only on successful finish
        m1_seq.sequenceFinished.connect(self._on_plate_done_m1)
        m1_seq.sequenceError.connect(lambda msg: self.lbl_m1_stat.setText(f"Status: Erro - {msg}"))
        m1_seq.bcMatch.connect(lambda ok,x,y,w,h,txt:
                               self.lbl_m1_code.setText(f"Código: {txt if ok else '—'}"))
        # -------- Mesa 2 ----------
        mesa2_tab = getattr(self.ctrl, "mesa_tabs", {}).get(2)
        if mesa2_tab:
            m2w = mesa2_tab.inspect_widget
            for sig in (m2w.positionAdded,
                        m2w.positionRemoved,
                        m2w.positionInserted):
                sig.connect(lambda _=None: self._sync_mesa2_positions())
            mesa2_tab.prog_widget.fileLoaded.connect(
                lambda _=None: self._sync_mesa2_positions())
            mesa2_tab.inspect_widget.list_widget.currentRowChanged.connect(
                self._mirror_select_row_m2)
            # -------- conexões de feedback (Mesa 2) -------------------
            m2_seq = mesa2_tab.seq_widget
            m2_seq.fidMatch.connect(lambda sim,ok,x,y,w,h: self.lbl_m2_fid.setText(
                f"Fiducial: {'OK' if ok else 'Fail'} ({sim:.1f}%)"))
            m2_seq.fidClear.connect(lambda: self.lbl_m2_fid.setText("Fiducial: —"))
            # ────── SINCRONIZAÇÃO DA BARRA DE PROGRESSO (Mesa-2) ──────
            # ────── SINCRONIZAÇÃO DA BARRA DE PROGRESSO (Mesa-2) ──────
            m2_seq._progress.valueChanged.connect(self.pb_m2.setValue)
            m2_seq._btn_execute.clicked.connect(
                lambda _=False, s=m2_seq: self._sync_progress_range(self.pb_m2, s))
            mesa2_tab.inspect_widget.positionAdded.connect(
                lambda _=None, s=m2_seq: self._sync_progress_range(self.pb_m2, s))
            mesa2_tab.inspect_widget.positionRemoved.connect(
                lambda _=None, s=m2_seq: self._sync_progress_range(self.pb_m2, s))
            m2_seq.sequenceFinished.connect(lambda: self.pb_m2.setValue(self.pb_m2.maximum()))
            m2_seq.sequenceError.connect(  lambda _msg: self.pb_m2.setValue(self.pb_m2.maximum()))
            m2_seq.sequenceFinished.connect(lambda: self.lbl_m2_stat.setText("Status: Concluído"))
            # increment Mesa 2 count only on successful finish
            m2_seq.sequenceFinished.connect(self._on_plate_done_m2)
            m2_seq.sequenceError.connect(lambda msg: self.lbl_m2_stat.setText(f"Status: Erro - {msg}"))
            m2_seq.bcMatch.connect(lambda ok,x,y,w,h,txt:
                                   self.lbl_m2_code.setText(f"Código: {txt if ok else '—'}"))
        # primeira sincronização
        self._sync_mesa1_positions()
        self._sync_mesa2_positions()

    # ---------- helper interno ------------------------------------
    @staticmethod
    def _sync_progress_range(ext_bar, seq_widget):
        """
        Copia min/max do QProgressBar interno (_progress) para a barra
        externa `ext_bar`.
        """
        ext_bar.setRange(seq_widget._progress.minimum(),
                         seq_widget._progress.maximum())
        ext_bar.setValue(seq_widget._progress.value())

    def _sync_mesa2_positions(self):
        """Reflete Mesa 2 na lista da direita."""
        try:
            pts = self.ctrl.mesa_tabs[2].inspect_widget.positions()
        except Exception:
            pts = []
        self.mirror_m2_list.blockSignals(True)
        self.mirror_m2_list.clear()
        for p in pts:
            self.mirror_m2_list.addItem(
                f"{p.name}.  X={p.x:.0f}  Y={p.y2:.0f}  Z={p.z:.0f}"
            )
        # mantém seleção
        row_sel = self.ctrl.mesa_tabs[2].inspect_widget.list_widget.currentRow()
        if 0 <= row_sel < self.mirror_m2_list.count():
            self.mirror_m2_list.setCurrentRow(row_sel)
        self.mirror_m2_list.blockSignals(False)

    # -----------------------------------------------------------------
    #  Seleção vinda da Mesa 1 → aplica no espelho
    # -----------------------------------------------------------------
    def _mirror_select_row(self, row: int):
        """
        Recebe índice da linha seleccionada na QListWidget original
        (Mesa 1) e replica a selecção no QListWidget espelhado.
        """
        if row < 0 or row >= self.mirror_m1_list.count():
            self.mirror_m1_list.clearSelection()
            return
        self.mirror_m1_list.blockSignals(True)
        self.mirror_m1_list.setCurrentRow(row)
        self.mirror_m1_list.blockSignals(False)

    # ---------------- Mesa 2 -----------------------------------------
    def _mirror_select_row_m2(self, row: int):
        if row < 0 or row >= self.mirror_m2_list.count():
            self.mirror_m2_list.clearSelection()
            return
        self.mirror_m2_list.blockSignals(True)
        self.mirror_m2_list.setCurrentRow(row)
        self.mirror_m2_list.blockSignals(False)

    # ------------------------------------------------------------------
    # Slots to count completed plates (only on successful sequence end)
    # ------------------------------------------------------------------
    def _on_plate_done_m1(self):
        """Increment and display Mesa 1 production count (only in APPLY mode)."""
        # only count if Mesa 1's sequence widget is in APPLY
        tab1 = getattr(self.ctrl, "mesa_tabs", {}).get(1)
        seq1 = getattr(tab1, "seq_widget", None)
        if not (seq1 and seq1.radio_apply.isChecked()):
            return
        self._count_m1 += 1
        self.lbl_count_m1.setText(str(self._count_m1))

    def _on_plate_done_m2(self):
        """Increment and display Mesa 2 production count (only in APPLY mode)."""
        # only count if Mesa 2's sequence widget is in APPLY
        tab2 = getattr(self.ctrl, "mesa_tabs", {}).get(2)
        seq2 = getattr(tab2, "seq_widget", None)
        if not (seq2 and seq2.radio_apply.isChecked()):
            return
        self._count_m2 += 1
        self.lbl_count_m2.setText(str(self._count_m2))

    # ------------------------------------------------------------------
    # Slot chamado por PlateFlowManager quando termina cada ciclo
    # ------------------------------------------------------------------
    def _on_plate_time(self, mesa_id: int, elapsed: float):
        """
        Atualiza:
          – lbl_time_elapsed_m<n>: tempo (s) do último ciclo com 2 decimais;
          – lbl_time_avg_m<n>: média de todos os tempos registrados.
        """
        # Só processa tempos quando estamos no modo APPLY
        if not self.seq_widget.radio_apply.isChecked():
            return
        if mesa_id == 1:
            self._times_m1.append(elapsed)
            self.lbl_time_elapsed_m1.setText(f"{elapsed:.2f} s")
            avg = sum(self._times_m1) / len(self._times_m1)
            self.lbl_time_avg_m1.setText(f"{avg:.2f} s")
        elif mesa_id == 2:
            self._times_m2.append(elapsed)
            self.lbl_time_elapsed_m2.setText(f"{elapsed:.2f} s")
            avg = sum(self._times_m2) / len(self._times_m2)
            self.lbl_time_avg_m2.setText(f"{avg:.2f} s")
    
    
