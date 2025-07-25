# axes_control_tab.py
"""
Widget completo de controle de eixos (quatro eixos + inspeção +
salvar / carregar + sequência).  Reaproveita toda a lógica já existente
no MultiAxisMotorController; somente a parte visual fica aqui.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, QSizePolicy
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

        aux_group = self.ctrl.create_auxiliary_controls()
        left_col.addWidget(aux_group)
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

        
        bottom_placeholder = QFrame(objectName="centerBottom")
        bottom_placeholder.setStyleSheet(
            "QFrame { background-color:#ECEFF1; border: 1px dashed #B0BEC5; }")
        bottom_placeholder.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

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
    
    
