# axes_control_tab.py
"""
Widget completo de controle de eixos (quatro eixos + inspeção +
salvar / carregar + sequência).  Reaproveita toda a lógica já existente
no MultiAxisMotorController; somente a parte visual fica aqui.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, QSizePolicy,
    QListWidget, QLabel
)
from mesa_plot_widget import MesaPlotWidget
from PyQt6.QtCore import Qt, QTimer

from movement_controls_widget import MovementControlsWidget
from position_status_widget  import PositionStatusWidget
from inspection_positions_widget import InspectionPositionsWidget
from program_io_widget      import ProgramIOWidget
from positions_backend      import InspectionPositionsBackend
from sequence_control       import SequenceControlWidget
from sequence_control       import InspectionPosition                # typing


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

        # --------------------- COLUNA ESQUERDA (15 %) ------------------
        left_col = QVBoxLayout()
        # ------------------------------------------------------------
        # 01-Ago-2025
        # Removido o GroupBox “CONTROLES AUXILIARES” SOMENTE desta aba
        # (“Controle de Eixos”).  As mesas 1 e 2 continuam exibindo-o.
        # ------------------------------------------------------------
        #  left_col.addWidget(self.ctrl.create_auxiliary_controls())
        left_col.addStretch()

        left_wrap = QWidget(); left_wrap.setLayout(left_col)
        grid.addWidget(left_wrap, 0, 0)

        # ------------------------- COLUNA CENTRAL (70 %) ---------------
        # ---------- VISUALIZAÇÃO DAS MESAS ----------------------------
        center_top = QFrame(objectName="centerTop")
        grid.addWidget(center_top, 0, 1)
        hplot = QHBoxLayout(center_top); hplot.setContentsMargins(2,2,2,2)
        # cria widgets gráficos para cada mesa
        self.plot_m1 = MesaPlotWidget(self.ctrl.table_limits[1], title="Mesa 1")
        self.plot_m2 = MesaPlotWidget(self.ctrl.table_limits[2], title="Mesa 2")
        hplot.addWidget(self.plot_m1); hplot.addWidget(self.plot_m2)

        # --------------------- COLUNA DIREITA (15 %) -------------------
        right_col = QVBoxLayout()

        self.mov_widget = MovementControlsWidget()
        right_col.addWidget(self.mov_widget)

        # Posições de inspeção
        self.inspect_widget = InspectionPositionsWidget(
            get_current_position=self.ctrl._get_current_position_dict)
        self.inspect_widget.setMaximumHeight(260)
        right_col.addWidget(self.inspect_widget)

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
        # ------------------------------------------------------------------
        #  AJUSTE “START GERAL”
        #  – renomeia o botão principal e liga ao controlador
        # ------------------------------------------------------------------
        try:                                            # remove conexão antiga
            self.seq_widget._btn_execute.clicked.disconnect()
        except Exception:
            pass
        self.seq_widget._btn_execute.setText("Start Geral")
        self.seq_widget._btn_execute.clicked.connect(self.ctrl.start_global_cycle)
        # botão “Parar” deixa de ser usado
        self.seq_widget._btn_stop.hide()

        right_col.addWidget(self.seq_widget)

        right_col.addStretch()
        right_wrap = QWidget(); right_wrap.setLayout(right_col)
        grid.addWidget(right_wrap, 0, 2)

        # ------------------------------ LINHA INFERIOR -----------------
        left_spacer  = QWidget()
        right_spacer = QWidget()
        for s in (left_spacer, right_spacer):
            s.setSizePolicy(QSizePolicy.Policy.Expanding,
                            QSizePolicy.Policy.Preferred)

        
        # --------------------------------------------------------------
        #  REGIÃO INFERIOR CENTRAL
        #  – agora dividida em duas metades com fundo cinza
        # --------------------------------------------------------------
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
        self.mirror_m1_list = QListWidget()
        self.mirror_m1_list.setStyleSheet(
            "QListWidget { background:#424242; color:#ECEFF1; }")
        self.mirror_m1_list.setMinimumHeight(140)

        left_half_lay.addWidget(self.mirror_m1_label)
        left_half_lay.addWidget(self.mirror_m1_list, 1)

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

        right_half_lay.addWidget(self.mirror_m2_label)
        right_half_lay.addWidget(self.mirror_m2_list, 1)

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

        grid.addWidget(left_spacer,        1, 0)
        grid.addWidget(bottom_placeholder, 1, 1)
        grid.addWidget(right_spacer,       1, 2)

        # --------- proporções (colunas 15|70|15, linhas 70|30) ---------
        grid.setColumnStretch(0, 15)
        grid.setColumnStretch(1, 70)
        grid.setColumnStretch(2, 15)
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
            # expõe gráficos
            self.ctrl.mesa_plot_widgets = {1: self.plot_m1,
                                           2: self.plot_m2}

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
        # primeira sincronização
        self._sync_mesa1_positions()
        self._sync_mesa2_positions()

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
    
    
