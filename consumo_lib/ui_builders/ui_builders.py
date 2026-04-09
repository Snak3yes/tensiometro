"""
UI Builders - Construtores de Interface do Usuário

Este módulo contém builders para criar a UI da aplicação de forma organizada.
"""

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QLineEdit, QComboBox, QSpinBox, QPushButton,
    QTableWidget, QHeaderView
)
from aoi_lib.plc_axis_controller import PLCAxisController
from consumo_lib.controllers import ConnectionManagerController

# Design System
from consumo_lib.ui.widget_standards import StandardButton

# NOTA: Os imports abaixo são mantidos para compatibilidade com métodos não usados
# na release v0.5-tension (inspeção visual desabilitada)
from consumo_lib.widgets.movement_control import MovementControlWidget  # noqa: F401
from consumo_lib.widgets.position_list import PositionListWidget  # noqa: F401
from consumo_lib.widgets.sequence_control import SequenceControlWidget  # noqa: F401

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
        2. Cria painel direito com abas (ocupando todo o espaço central)
        3. Inicializa controllers que dependem de UI widgets

        NOTA: Conexão PLC movida para diálogo dedicado (menu Ferramentas → Conexões).
        Release v0.5-tension: groupbox de conexão removido da janela principal.
        """
        # Widget central
        central_widget = QWidget()
        self.window.setCentralWidget(central_widget)

        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        self._build_top_banner(main_layout)

        # Cria grupos principais (calibração oculto)
        self._build_calibration_group(main_layout)

        # Layout horizontal para o painel de abas
        content_layout = QHBoxLayout()

        # Painel principal: QTabWidget (expanding, ocupa todo o espaço)
        right_panel = self._build_right_panel(None)  # None = não usa mais splitter
        content_layout.addWidget(right_panel, 1)  # stretch=1 para expandir

        main_layout.addLayout(content_layout)

        # Barra de status
        self.window.statusBar().showMessage("Pronto para conectar")

    def _build_top_banner(self, main_layout):
        """Cria faixa superior para indicadores de modo."""
        banner_layout = QHBoxLayout()
        banner_layout.addStretch()

        self.window.login_mode_badge = QLabel("Modo: Eng/Admin")
        self.window.login_mode_badge.setVisible(False)
        self.window.login_mode_badge.setStyleSheet(
            """
            QLabel {
                border: 2px solid #F28C28;
                border-radius: 8px;
                background: #FFF4E8;
                color: #A65100;
                font-weight: 700;
                padding: 8px 14px;
            }
            """
        )
        banner_layout.addWidget(self.window.login_mode_badge)

        main_layout.addLayout(banner_layout)

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

    # NOTA: _build_connection_group() removido na release v0.5-tension
    # Conexão PLC agora é feita via diálogo (menu Ferramentas → Conexões)
    # Ver consumo_lib/dialogs/connection_dialog.py

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
        parent.addTab(tab_widget, "Posições e Rotinas")

        # Expose referências para compatibilidade
        self.window.backup_controls_tab = tab_widget

    def _build_right_panel(self, splitter):
        """
        Cria painel direito com aba de Medição de Tensão.

        REFACTORED (2026-03-29): QTabWidget removido - apenas uma aba resta.
        TensionMeasurementTab é colocada diretamente no layout.

        NOTA: Parâmetro splitter ignorado (left panel foi removido).
        """
        # Criar ConnectionManagerController (preview de câmera é opcional)
        self._create_connection_manager_controller()

        # Criar movement_widget oculto para compatibilidade com keyboard handler
        # (movido de TabFactory.create_all_tabs())
        self.window.movement_widget = MovementControlWidget(
            self.window.controller,
            self.window.config,
            parent=self.window
        )
        self.window.movement_widget.hide()  # Oculto - acessível via MovementDialog

        # Criar TensionMeasurementTab diretamente (sem QTabWidget)
        tension_measurement_tab = self._create_tension_measurement_tab()

        # Referência para compatibilidade
        self.window.right_panel = tension_measurement_tab  # Alias para compatibilidade
        self.window.tension_measurement_tab = tension_measurement_tab

        logger.info("TensionMeasurementTab criada diretamente (QTabWidget removido)")
        return tension_measurement_tab

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

    def _create_tension_measurement_tab(self):
        """Cria TensionMeasurementTab diretamente (sem QTabWidget wrapper)."""
        from consumo_lib.tabs import TensionMeasurementTab

        tab = TensionMeasurementTab(
            stencil_manager=self.window.stencil_tracker,
            parent=self.window
        )

        if hasattr(tab, "measure_stencil_requested"):
            tab.measure_stencil_requested.connect(self.window.open_tracking_dialog)

        if hasattr(tab, "program_selected"):
            tab.program_selected.connect(self._sync_selected_stencil_from_tension_tab)

        # NOTA: stencil_identification é definido em open_tracking_dialog()
        # TensionMeasurementTab usa stencil_manager internamente, não precisa de conexões

        logger.debug("TensionMeasurementTab criada")
        return tab

    def _sync_selected_stencil_from_tension_tab(self, stencil_data):
        """Sincroniza a seleção da tela inicial com o estado global da aplicação."""
        if not stencil_data:
            return

        stencil_code = stencil_data.get("code")
        if not stencil_code:
            return

        wrapper = getattr(self.window, "stencil_manager_wrapper", None)
        if wrapper is None:
            return

        stencil = wrapper.get_stencil(stencil_code)
        if stencil is not None:
            wrapper.select_stencil(stencil)
