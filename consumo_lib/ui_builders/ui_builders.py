"""
UI Builders - Construtores de Interface do Usuário

Este módulo contém builders para criar a UI da aplicação de forma organizada.
"""

import logging
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QLineEdit, QComboBox, QSpinBox, QPushButton,
    QTabWidget, QSplitter, QTableWidget, QTableView,
    QHeaderView
)
from aoi_lib.plc_axis_controller import PLCAxisController
from consumo_lib.tabs import (
    TensionTab,
    TrackingTab,
)
from consumo_lib.widgets.movement_control import MovementControlWidget
from consumo_lib.widgets.position_list import PositionListWidget
from consumo_lib.widgets.sequence_control import SequenceControlWidget
from consumo_lib.widgets.plc_monitor import PLCMonitorWidget
from consumo_lib.controllers import ConnectionManagerController

# Design System
from consumo_lib.ui.widget_standards import StandardButton

logger = logging.getLogger(__name__)


class MainUIBuilder:
    """
    Builder para criar a UI principal da aplicação.

    Responsabilidade:
    - Criar todos os widgets da UI principal
    - Configurar layouts e splitter
    - Criar todas as abas
    - Conectar signals aos handlers do main_window
    - Atribuir widgets criados ao main_window
    """

    def __init__(self, main_window):
        """
        Inicializa o UI builder.

        Args:
            main_window: Instância de AOIControllerApp onde widgets serão criados
        """
        self.main_window = main_window
        self.window = main_window  # Alias para facilitar acesso

    def build_ui(self):
        """
        Constrói toda a UI principal.

        Este método:
        1. Cria widget central e layout principal
        2. Cria grupo de conexão
        3. Cria painel direito com abas (agora ocupando todo o espaço central)
        4. Cria painel de movimento (direita)
        5. Configura layout horizontal simplificado
        6. Inicializa controllers que dependem de UI widgets

        NOVO LAYOUT (Refatoração 2026-01-16):
        - Removeu painel esquerdo (agora na aba "Backup de Controles")
        - Layout simplificado: QHBoxLayout [QTabWidget | MovementControlWidget]
        - QTabWidget ocupa todo o espaço disponível
        - MovementControlWidget permanece visível (fixo à direita)
        """
        # Widget central
        central_widget = QWidget()
        self.window.setCentralWidget(central_widget)

        # Layout principal
        main_layout = QVBoxLayout(central_widget)

        # Cria grupos principais
        self._build_connection_group(main_layout)
        self._build_calibration_group(main_layout)

        # NOVO: Layout horizontal simplificado (sem splitter, sem left panel)
        content_layout = QHBoxLayout()

        # Painel esquerdo: QTabWidget (expanding, ocupa todo o espaço)
        right_panel = self._build_right_panel(None)  # None = não usa mais splitter
        content_layout.addWidget(right_panel, 1)  # stretch=1 para expandir

        # Painel direito: MovementControlWidget (fixed width, dentro de CNCControlTab)
        # NOTA: MovementControlWidget está dentro de CNCControlTab (self.window.movement_widget)
        # Ele já é visível na aba "Câmera & Movimento", então não precisamos adicioná-lo separadamente
        # O layout agora é apenas o QTabWidget expandido

        main_layout.addLayout(content_layout)

        # Barra de status
        self.window.statusBar().showMessage("Pronto para conectar")

    def _build_connection_group(self, main_layout):
        """Cria grupo de conexão (PLC, CNC, Camera)."""
        self.window.connection_group = QGroupBox("Conexão")
        connection_layout = QGridLayout()

        # PLC (Modbus TCP)
        connection_layout.addWidget(QLabel("IP PLC:"), 0, 0)
        self.window.plc_host_input = QLineEdit(
            self.window.config.get("connections", "plc_host", default="192.168.1.5")
        )
        connection_layout.addWidget(self.window.plc_host_input, 0, 1)

        connection_layout.addWidget(QLabel("Porta:"), 0, 2)
        self.window.plc_port_input = QSpinBox()
        self.window.plc_port_input.setRange(1, 65535)
        self.window.plc_port_input.setValue(
            self.window.config.get("connections", "plc_port", default=502)
        )
        self.window.plc_port_input.setFixedWidth(100)
        connection_layout.addWidget(self.window.plc_port_input, 0, 3)

        btn_label = "Conectar PLC" if isinstance(
            self.window.controller.cnc, PLCAxisController
        ) else "Conectar CNC"
        self.window.connect_cnc_btn = QPushButton(btn_label)
        self.window.connect_cnc_btn.clicked.connect(self.window._on_connect_btn_clicked)
        connection_layout.addWidget(self.window.connect_cnc_btn, 0, 4)

        # CNC Connection (serial legacy)
        connection_layout.addWidget(QLabel("Porta CNC:"), 1, 0)
        self.window.cnc_port_combo = QComboBox()
        self.window.refresh_ports()
        connection_layout.addWidget(self.window.cnc_port_combo, 1, 1)

        # Refresh ports button
        self.window.refresh_ports_btn = StandardButton("Atualizar Portas")
        self.window.refresh_ports_btn.clicked.connect(self.window.refresh_ports)
        connection_layout.addWidget(self.window.refresh_ports_btn, 1, 3)

        self.window.connection_group.setLayout(connection_layout)
        main_layout.addWidget(self.window.connection_group)

    def _build_calibration_group(self, main_layout):
        """Cria grupo de calibração (oculto por padrão)."""
        calibration_group = QGroupBox("Calibração de Movimento")
        calibration_layout = QHBoxLayout()

        # Campos permanecem criados porque são usados pela lógica de calibração
        self.window.pulses_input = QLineEdit(str(
            self.window.config.get("calibration", "pulses_per_rev", default=400)
        ))
        self.window.fuso_input = QLineEdit(str(
            self.window.config.get("calibration", "fuso_pitch", default=5)
        ))
        self.window.apply_calibration_btn = StandardButton("Aplicar Calibração", variant="primary")

        # Conecta ao CalibrationController
        self.window.apply_calibration_btn.clicked.connect(
            lambda: self.window.calibration_controller.show_dialog(
                self.window,
                self.window.pulses_per_rev_input.text(),
                self.window.fuso_input.text()
            ) if self.window.calibration_controller is not None else None
        )

        calibration_group.setLayout(calibration_layout)
        calibration_group.setVisible(False)  # Esconde grupo
        main_layout.addWidget(calibration_group)  # Mantém no DOM para uso interno

    def _build_left_panel(self):
        """Cria painel esquerdo (lista, sequência, resultados)."""
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # REMOVIDO: _build_position_group() - posição agora está em MovementControlWidget
        # Ver aba CNC Control → Movement Controls → "Posição Atual (mm)"

        # Widget de lista de posições
        self._build_position_list(left_layout)

        # Controle de sequência
        self._build_sequence_control(left_layout)

        # Tabela de resultados
        self._build_results_table(left_layout)

        return left_panel

    def _build_position_list(self, parent_layout):
        """Cria widget de lista de posições."""
        self.window.position_list_widget = PositionListWidget()
        self.window.position_list_widget.add_position_btn.clicked.connect(
            self.window.add_current_position
        )
        self.window.position_list_widget.remove_position_btn.clicked.connect(
            self.window.remove_position
        )
        self.window.position_list_widget.position_selected.connect(
            self.window.on_position_selected
        )

        parent_layout.addWidget(self.window.position_list_widget)

    def _build_sequence_control(self, parent_layout):
        """Cria widget de controle de sequência."""
        self.window.sequence_widget = SequenceControlWidget()
        self.window.sequence_widget.create_sequence_btn.clicked.connect(
            self.window.create_sequence
        )
        self.window.sequence_widget.run_sequence_btn.clicked.connect(
            self.window.run_sequence
        )
        self.window.sequence_widget.stop_sequence_btn.clicked.connect(
            self.window.stop_sequence
        )
        self.window.sequence_widget.save_btn.clicked.connect(
            self.window.save_program
        )
        self.window.sequence_widget.load_btn.clicked.connect(
            self.window.load_program
        )
        self.window.sequence_widget.save_gcode_btn.clicked.connect(
            self.window.save_gcode
        )
        self.window.sequence_widget.load_gcode_btn.clicked.connect(
            self.window.load_gcode
        )

        parent_layout.addWidget(self.window.sequence_widget)

    def _build_results_table(self, parent_layout):
        """Cria tabela de resultados de execução de sequência."""
        self.window.results_table = QTableWidget(0, 3)
        self.window.results_table.setHorizontalHeaderLabels(
            ["Posição", "Horário", "Status"]
        )
        # Make columns stretch to fill available space
        self.window.results_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        parent_layout.addWidget(self.window.results_table)

    def _build_backup_controls_tab(self, parent):
        """
        Cria aba "Backup de Controles" (NOVO - 2026-01-16).

        Esta aba contém todos os widgets que estavam anteriormente
        no painel esquerdo da aplicação:
        - PositionListWidget (lista de posições)
        - SequenceControlWidget (controle de sequência)
        - ResultsTable (tabela de resultados)

        Args:
            parent: QTabWidget onde a aba será adicionada
        """
        from PyQt6.QtWidgets import QWidget

        # Cria widget container para a aba
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)

        # Adiciona os widgets que estavam no left panel
        # (chamando os mesmos métodos de criação)
        self._build_position_list(tab_layout)
        self._build_sequence_control(tab_layout)
        self._build_results_table(tab_layout)

        # Adiciona a aba ao QTabWidget
        parent.addTab(tab_widget, "📦 Posições e Rotinas")

        # Expose referências para compatibilidade
        self.window.backup_controls_tab = tab_widget

    def _build_right_panel(self, splitter):
        """
        Cria painel direito com abas e controllers que dependem de UI.

        NOVO (2026-01-16): Parâmetro splitter ignorado (left panel foi removido)
        """
        # Cria QTabWidget para abas
        right_panel = QTabWidget()
        self.window.right_panel = right_panel

        # Aba 1: Movimento
        self._build_movement_tab(right_panel)

        # Criar ConnectionManagerController (preview de câmera é opcional)
        self._create_connection_manager_controller()

        # Abas restantes (incluindo nova aba "Backup de Controles")
        self._build_remaining_tabs(right_panel)

        # NOTA: As abas ficam habilitadas mesmo sem CLP conectado
        # O bloqueio agora é feito apenas nas ações que requerem movimento
        return right_panel

    def _build_movement_tab(self, parent):
        """Cria aba dedicada apenas ao controle de movimento."""
        tab_widget = QWidget(parent)
        tab_layout = QVBoxLayout(tab_widget)
        tab_layout.setContentsMargins(8, 8, 8, 8)

        self.window.movement_widget = MovementControlWidget(
            self.window.controller,
            self.window.config
        )
        tab_layout.addWidget(self.window.movement_widget)

        self.window.movement_tab = tab_widget
        self.window.camera_preview = None
        parent.addTab(tab_widget, "Movimento")

    def _create_connection_manager_controller(self):
        """Cria ConnectionManagerController após UI estar montada."""
        try:
            self.window.connection_manager_controller = ConnectionManagerController(
                self.window.controller,
                self.window.config,
                getattr(self.window, "camera_preview", None),
                self.window
            )
            logger.debug("ConnectionManagerController criado com sucesso")

            # Signals conectados via SignalAggregator
        except Exception as e:
            logger.error(f"Erro ao criar ConnectionManagerController: {e}")
            self.window.connection_manager_controller = None

    def _build_remaining_tabs(self, parent):
        """Cria abas restantes do painel direito."""
        # NOVO - FASE 2: Aba TreeView (Lista de Programas)
        from consumo_lib.tabs import TreeViewTab
        self.window.tree_view_tab = TreeViewTab(
            stencil_manager=self.window.stencil_tracker,
            parent=self.window
        )
        parent.addTab(self.window.tree_view_tab, "📋 Stencils")

        # Aba 2: Monitor CLP
        self.window.plc_monitor = PLCMonitorWidget(self.window.controller)
        parent.addTab(self.window.plc_monitor, "Monitor CLP")

        # Aba 3: Visualização de Tensão
        self.window.tension_visualization = TensionTab(parent=self.window)
        self.window.tension_viz_widget = self.window.tension_visualization.visualization
        parent.addTab(self.window.tension_visualization, "Visualização de Tensão")

        # Aba 4: Rastreabilidade
        self.window.tracking_tab = TrackingTab(
            self.window.stencil_tracker,
            parent=self.window
        )
        # Conecta sinais (exceto _on_* que são tratados pelo SignalAggregator)
        self.window.tracking_tab.tension_measurement_requested.connect(
            self.window._run_tension_measurement
        )
        self.window.tracking_tab.stencil_management_requested.connect(
            self.window.show_stencil_manager
        )
        self.window.tracking_tab.new_stencil_requested.connect(
            self.window.show_new_stencil_dialog
        )
        # Expose widget interno para compatibilidade
        self.window.stencil_identification = self.window.tracking_tab.stencil_identification
        self.window.btn_run_tension = self.window.tracking_tab.btn_run_tension
        parent.addTab(self.window.tracking_tab, "🏷️ Rastreabilidade")

        # REMOVIDO (release/v0.5-tension): Aba "Posições e Rotinas"
        # Esta aba é útil apenas para inspeção visual (main branch)
        # Para medição de tensão, usar TensionMeasurementDialog
        # self._build_backup_controls_tab(parent)
