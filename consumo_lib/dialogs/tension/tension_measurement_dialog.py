"""
Tension Measurement Dialog (Refactored)

PyQt6 dialog for tension measurement of stencils.
Uses MeasurementOrchestrator for business logic separation.

Created: 2026-01-14 (Phase 1 - SOLID Refactoring)
Refactored from: aoi_lib/stencil_tension.py (lines 447-1409, 962 lines)
"""

import logging
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QComboBox, QGroupBox,
    QProgressBar, QMessageBox, QTreeWidget, QTreeWidgetItem,
    QSplitter, QTabWidget, QWidget
)
from PyQt6.QtGui import QDoubleValidator, QIntValidator
from PyQt6.QtCore import Qt

from aoi_lib.config_manager import AOIConfigManager
from consumo_lib.ui import COLORS, TYPO, SPACE, DIM
from consumo_lib.ui.widget_standards import StandardButton
from consumo_lib.widgets.movement_control import MovementControlWidget

# Import refactored modules
from aoi_lib.tensiometer import (
    MeasurementOrchestrator,
    TensiometerSerialManager,
)

# Import pattern manager and dialogs
from consumo_lib.managers.measurement_pattern_manager import MeasurementPatternManager
from consumo_lib.dialogs.tension.save_pattern_dialog import SavePatternDialog
from consumo_lib.dialogs.tension.select_pattern_dialog import SelectPatternDialog

logger = logging.getLogger(__name__)

TENSIOMETER_POWER_COIL = 20
TENSIOMETER_POWER_ON_PULSE_MS = 100
TENSIOMETER_POWER_OFF_PULSE_MS = 3000
TENSIOMETER_CALIBRATE_COIL = 23
TENSIOMETER_ZERO_COIL = 24


class TensionMeasurementDialog(QDialog):
    """
    Dialog for measuring tension of stencils in NxN grid.

    This dialog uses the MeasurementOrchestrator to coordinate
    the measurement process, keeping UI logic separate from
    business logic.

    Responsibilities (UI ONLY):
    - User input collection
    - Progress display
    - Status updates
    - Error messages

    Business Logic (delegated to MeasurementOrchestrator):
    - Parameter validation
    - Grid calculation
    - Thread management
    - Result persistence
    """

    def __init__(self, parent=None, cnc_controller=None):
        """
        Initialize dialog.

        Args:
            parent: Parent widget
            cnc_controller: CNC controller for movement
        """
        super().__init__(parent)
        self.cnc = cnc_controller
        self.config = getattr(parent, "config", None) or AOIConfigManager()

        # Business logic components
        self.tensiometer = TensiometerSerialManager()
        self.orchestrator: Optional[MeasurementOrchestrator] = None

        # Pattern manager
        self.pattern_manager = MeasurementPatternManager()

        # UI State
        self.current_points = []
        self.is_measuring = False
        self.selected_pattern_name: Optional[str] = None

        # Setup UI
        self.setWindowTitle("MediÃ§Ã£o de TensÃ£o do Stencil")
        self.setMinimumSize(900, 600)
        self._build_ui()

        # Connect tensiometer
        self._refresh_ports()

        # Load patterns
        self._load_patterns_tree()

    def _build_ui(self):
        """Build user interface."""
        outer_layout = QVBoxLayout(self)
        outer_layout.setSpacing(SPACE.MD)
        outer_layout.setContentsMargins(SPACE.MD, SPACE.MD, SPACE.MD, SPACE.MD)

        self.tabs = QTabWidget(self)
        outer_layout.addWidget(self.tabs)

        measurement_tab = QWidget(self)
        self.tabs.addTab(measurement_tab, "MediÃƒÂ§ÃƒÂ£o")

        main_layout = QHBoxLayout(measurement_tab)
        main_layout.setSpacing(SPACE.MD)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # ==================== SPLITTER (COLUNA ESQUERDA | DIREITA) ====================
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(4)

        # ==================== COLUNA ESQUERDA: PADRÃ•ES (30%) ====================
        left_widget = self._build_patterns_column()
        splitter.addWidget(left_widget)

        # ==================== COLUNA DIREITA: CONTEÃšDO PRINCIPAL (70%) ====================
        right_widget = self._build_main_content()
        splitter.addWidget(right_widget)

        # Define proporÃ§Ã£o 30/70
        splitter.setStretchFactor(0, 0)  # Esquerda: tamanho fixo
        splitter.setStretchFactor(1, 1)  # Direita: expande
        splitter.setCollapsible(0, False)

        main_layout.addWidget(splitter, 1)

        movement_tab = QWidget(self)
        movement_layout = QVBoxLayout(movement_tab)
        movement_layout.setContentsMargins(0, 0, 0, 0)
        movement_layout.setSpacing(0)

        self.movement_widget = MovementControlWidget(
            self.cnc,
            self.config,
            parent=movement_tab
        )
        movement_layout.addWidget(self.movement_widget)
        self.tabs.addTab(movement_tab, "Movimento")

    def _build_patterns_column(self) -> QWidget:
        """ConstrÃ³i coluna esquerda com treeview de padrÃµes."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(SPACE.SM)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header_label = QLabel("PadrÃµes de MediÃ§Ã£o")
        header_label.setFont(TYPO.get_font(TYPO.TITLE_SMALL, bold=True))
        layout.addWidget(header_label)

        # TreeView
        self.pattern_tree = QTreeWidget()
        self.pattern_tree.setHeaderLabels(["Nome", "Grid"])
        self.pattern_tree.setColumnWidth(0, 140)
        self.pattern_tree.setColumnWidth(1, 50)
        self.pattern_tree.setMinimumWidth(200)
        self.pattern_tree.setMaximumWidth(280)
        self.pattern_tree.itemClicked.connect(self._on_pattern_selected)
        self.pattern_tree.itemDoubleClicked.connect(self._on_pattern_double_clicked)

        # Estilo
        self.pattern_tree.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {COLORS.SURFACE_VARIANT};
                border: 1px solid {COLORS.BORDER};
                border-radius: {DIM.RADIUS_SM}px;
                font-size: {TYPO.BODY_SMALL}px;
            }}
            QHeaderView::section {{
                padding: 4px 8px;
                font-size: {TYPO.LABEL_SMALL}px;
                min-height: 24px;
                background-color: {COLORS.SURFACE_VARIANT};
                border: none;
                border-right: 1px solid {COLORS.BORDER};
                border-bottom: 1px solid {COLORS.BORDER};
                font-weight: bold;
            }}
            QTreeWidget::item {{
                min-height: 20px;
                padding: 4px 2px;
                border-bottom: 1px solid {COLORS.BORDER};
            }}
            QTreeWidget::item:selected {{
                background-color: #05966915;
                border: 1px solid #059669;
                color: {COLORS.TEXT_PRIMARY};
            }}
            QTreeWidget::item:hover:!selected {{
                background-color: {COLORS.SURFACE_VARIANT};
            }}
        """)
        layout.addWidget(self.pattern_tree, 1)

        # BotÃµes de aÃ§Ã£o
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(SPACE.SM)

        self.btn_load_pattern = StandardButton(
            "Carregar",
            variant="primary-blue",
            semantic_size="inline-primary"
        )
        self.btn_load_pattern.clicked.connect(self._on_load_pattern)
        btn_layout.addWidget(self.btn_load_pattern)

        layout.addLayout(btn_layout)

        # Label do padrÃ£o atual
        self.current_pattern_label = QLabel("Nenhum padrÃ£o selecionado")
        self.current_pattern_label.setStyleSheet(
            f"color: {COLORS.TEXT_HINT}; font-size: {TYPO.LABEL_SMALL}px;"
        )
        self.current_pattern_label.setWordWrap(True)
        layout.addWidget(self.current_pattern_label)

        return container

    def _build_main_content(self) -> QWidget:
        """ConstrÃ³i coluna direita com conteÃºdo principal do diÃ¡logo."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(SPACE.MD)
        layout.setContentsMargins(0, 0, 0, 0)

        # ==================== TENSIONOMETER CONNECTION ====================
        conn_group = QGroupBox("ConexÃ£o do TensiÃ´metro")
        conn_layout = QGridLayout(conn_group)
        conn_layout.setSpacing(8)

        # Port selection
        conn_layout.addWidget(QLabel("Porta:"), 0, 0)
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(120)
        conn_layout.addWidget(self.port_combo, 0, 1)

        # Refresh ports button
        self.refresh_ports_btn = StandardButton("Atualizar")
        self.refresh_ports_btn.setMaximumWidth(80)
        self.refresh_ports_btn.clicked.connect(self._refresh_ports)
        conn_layout.addWidget(self.refresh_ports_btn, 0, 2)

        # Connect/Disconnect button
        self.connect_btn = StandardButton("Conectar")
        self.connect_btn.clicked.connect(self._toggle_connection)
        conn_layout.addWidget(self.connect_btn, 0, 3, 1, 2)

        # Status label
        self.conn_status_label = QLabel("Status: Desconectado")
        self.conn_status_label.setStyleSheet(f"color: {COLORS.TEXT_HINT};")
        conn_layout.addWidget(self.conn_status_label, 1, 0, 1, 5)

        # Test button
        self.test_btn = StandardButton("Testar Leitura")
        self.test_btn.clicked.connect(self._test_reading)
        self.test_btn.setEnabled(False)
        conn_layout.addWidget(self.test_btn, 2, 0, 1, 5)

        self.turn_on_btn = StandardButton("Ligar")
        self.turn_on_btn.clicked.connect(self._turn_on_tensiometer)
        self.turn_on_btn.setEnabled(False)
        conn_layout.addWidget(self.turn_on_btn, 3, 0)

        self.turn_off_btn = StandardButton("Desligar")
        self.turn_off_btn.clicked.connect(self._turn_off_tensiometer)
        self.turn_off_btn.setEnabled(False)
        conn_layout.addWidget(self.turn_off_btn, 3, 1)

        self.calibrate_btn = StandardButton("Calibrar")
        self.calibrate_btn.clicked.connect(self._calibrate_tensiometer)
        self.calibrate_btn.setEnabled(False)
        conn_layout.addWidget(self.calibrate_btn, 3, 2)

        self.zero_btn = StandardButton("Zerar")
        self.zero_btn.clicked.connect(self._zero_tensiometer)
        self.zero_btn.setEnabled(False)
        conn_layout.addWidget(self.zero_btn, 3, 3, 1, 2)

        layout.addWidget(conn_group)

        # ==================== GRID CONFIGURATION ====================
        grid_group = QGroupBox("ConfiguraÃ§Ã£o do Grid")
        grid_layout = QGridLayout(grid_group)
        grid_layout.setSpacing(8)

        # Start position
        grid_layout.addWidget(QLabel("Ponto Inicial (X, Y):"), 0, 0)
        self.start_x_input = QLineEdit("0.0")
        self.start_x_input.setValidator(QDoubleValidator())
        self.start_x_input.setMaximumWidth(80)
        grid_layout.addWidget(self.start_x_input, 0, 1)

        self.start_y_input = QLineEdit("0.0")
        self.start_y_input.setValidator(QDoubleValidator())
        self.start_y_input.setMaximumWidth(80)
        grid_layout.addWidget(self.start_y_input, 0, 2)

        self.capture_start_btn = StandardButton("Capturar")
        self.capture_start_btn.clicked.connect(self._capture_start_position)
        grid_layout.addWidget(self.capture_start_btn, 0, 3)

        # End position
        grid_layout.addWidget(QLabel("Ponto Final (X, Y):"), 1, 0)
        self.end_x_input = QLineEdit("100.0")
        self.end_x_input.setValidator(QDoubleValidator())
        self.end_x_input.setMaximumWidth(80)
        grid_layout.addWidget(self.end_x_input, 1, 1)

        self.end_y_input = QLineEdit("100.0")
        self.end_y_input.setValidator(QDoubleValidator())
        self.end_y_input.setMaximumWidth(80)
        grid_layout.addWidget(self.end_y_input, 1, 2)

        self.capture_end_btn = StandardButton("Capturar")
        self.capture_end_btn.clicked.connect(self._capture_end_position)
        grid_layout.addWidget(self.capture_end_btn, 1, 3)

        # Grid size
        grid_layout.addWidget(QLabel("Grid Size (N):"), 2, 0)
        self.grid_size_input = QLineEdit("3")
        self.grid_size_input.setValidator(QIntValidator(2, 20))
        self.grid_size_input.setMaximumWidth(80)
        grid_layout.addWidget(self.grid_size_input, 2, 1)
        grid_layout.addWidget(QLabel("Para grid NxN"), 2, 2)

        # Z heights
        grid_layout.addWidget(QLabel("Altura MediÃ§Ã£o (Z):"), 3, 0)
        self.z_height_input = QLineEdit("5.0")
        self.z_height_input.setValidator(QDoubleValidator())
        self.z_height_input.setMaximumWidth(80)
        self.z_height_input.setToolTip(
            "Neste CLP, valores maiores de Z significam posicao fisica mais baixa."
        )
        grid_layout.addWidget(self.z_height_input, 3, 1)

        grid_layout.addWidget(QLabel("Altura Movimento:"), 3, 2)
        self.z_move_input = QLineEdit("10.0")
        self.z_move_input.setValidator(QDoubleValidator())
        self.z_move_input.setMaximumWidth(80)
        self.z_move_input.setToolTip(
            "Use um valor menor que o Z de medicao para manter a altura segura."
        )
        grid_layout.addWidget(self.z_move_input, 3, 3)

        layout.addWidget(grid_group)

        # ==================== PROGRESS DISPLAY ====================
        progress_group = QGroupBox("Progresso da MediÃ§Ã£o")
        progress_layout = QVBoxLayout(progress_group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("Pronto para iniciar")
        progress_layout.addWidget(self.progress_label)

        self.current_value_label = QLabel("Ãšltima leitura: --")
        self.current_value_label.setStyleSheet(f"font-size: {TYPO.BODY_MEDIUM}px; font-weight: bold;")
        progress_layout.addWidget(self.current_value_label)

        layout.addWidget(progress_group)

        # ==================== CONTROL BUTTONS ====================
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(SPACE.SM)

        self.btn_save_pattern = StandardButton(
            "ðŸ’¾ Salvar como PadrÃ£o",
            variant="primary-green",
            semantic_size="inline-primary"
        )
        self.btn_save_pattern.clicked.connect(self._on_save_pattern)
        self.btn_save_pattern.setEnabled(False)
        btn_layout.addWidget(self.btn_save_pattern)

        btn_layout.addStretch()

        self.start_btn = StandardButton("â–¶ Iniciar MediÃ§Ã£o", variant="primary-green", semantic_size="dialog-primary")
        self.start_btn.setEnabled(False)
        self.start_btn.clicked.connect(self._on_start)
        btn_layout.addWidget(self.start_btn)

        self.stop_btn = StandardButton("â¹ Parar", variant="emergency", semantic_size="dialog-secondary")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._on_stop)
        btn_layout.addWidget(self.stop_btn)

        self.close_btn = StandardButton("Fechar", variant="secondary", semantic_size="dialog-secondary")
        self.close_btn.clicked.connect(self.close)
        btn_layout.addWidget(self.close_btn)

        layout.addLayout(btn_layout)

        return container

    # ==================== CONNECTION HANDLERS ====================

    def _refresh_ports(self):
        """Refresh list of available serial ports."""
        ports = self.tensiometer.get_available_ports()
        self.port_combo.clear()
        self.port_combo.addItems(ports)
        logger.debug(f"Portas disponÃ­veis: {ports}")

    def _toggle_connection(self):
        """Toggle tensiometer connection."""
        if self.tensiometer.is_connected:
            self.tensiometer.disconnect()
            self._update_connection_ui(False)
            logger.info("TensiÃ´metro desconectado")
        else:
            port = self.port_combo.currentText()
            if not port:
                QMessageBox.warning(self, "Aviso", "Selecione uma porta serial primeiro.")
                return

            success = self.tensiometer.connect(port)
            if success:
                self._update_connection_ui(True)
                # Initialize orchestrator
                self.orchestrator = MeasurementOrchestrator(self.cnc, self.tensiometer)
                logger.info(f"TensiÃ´metro conectado em {port}")
            else:
                QMessageBox.critical(
                    self,
                    "Erro de ConexÃ£o",
                    f"Falha ao conectar em {port}:\n{self.tensiometer.last_error}"
                )

    def _update_connection_ui(self, connected: bool):
        """Update UI based on connection state."""
        if connected:
            self.connect_btn.setText("Desconectar")
            self.conn_status_label.setText("Status: âœ… Conectado")
            self.conn_status_label.setStyleSheet(f"color: {COLORS.SUCCESS};")
            self.test_btn.setEnabled(True)
            self.start_btn.setEnabled(True)
            plc_ready = self._can_control_tensiometer_hardware(show_message=False)
            self.turn_on_btn.setEnabled(plc_ready)
            self.turn_off_btn.setEnabled(plc_ready)
            self.calibrate_btn.setEnabled(plc_ready)
            self.zero_btn.setEnabled(plc_ready)
        else:
            self.connect_btn.setText("Conectar")
            self.conn_status_label.setText("Status: Desconectado")
            self.conn_status_label.setStyleSheet(f"color: {COLORS.TEXT_HINT};")
            self.test_btn.setEnabled(False)
            self.start_btn.setEnabled(False)
            self.turn_on_btn.setEnabled(False)
            self.turn_off_btn.setEnabled(False)
            self.calibrate_btn.setEnabled(False)
            self.zero_btn.setEnabled(False)

    def _test_reading(self):
        """Test tensiometer reading."""
        if not self.tensiometer.is_connected:
            QMessageBox.warning(self, "Aviso", "Conecte o tensiÃ´metro primeiro.")
            return

        value = self.tensiometer.read_tension_value()
        QMessageBox.information(
            self,
            "Leitura Teste",
            f"Valor lido: {value} N/cmÂ²"
        )
        logger.info(f"Leitura teste: {value} N/cmÂ²")

    def _can_control_tensiometer_hardware(self, show_message: bool = True) -> bool:
        """Check whether PLC control for the tensiometer is available."""
        if self.cnc is None:
            if show_message:
                QMessageBox.warning(self, "Aviso", "Controller CNC nÃƒÂ£o disponÃƒÂ­vel.")
            return False

        if not getattr(self.cnc, "is_connected", False):
            if show_message:
                QMessageBox.warning(self, "Aviso", "Conecte o CLP antes de acionar o tenciÃƒÂ´metro.")
            return False

        if not hasattr(self.cnc, "pulse_coil") and not hasattr(self.cnc, "_pulse_coil"):
            if show_message:
                QMessageBox.warning(
                    self,
                    "Aviso",
                    "O controlador atual nÃƒÂ£o expÃƒÂµe pulso de coil para o tenciÃƒÂ´metro."
                )
            return False

        return True

    def _pulse_tensiometer_coil(self, coil: int, action_name: str, duration_ms: int = 100) -> bool:
        """Send a PLC pulse command to the tensiometer."""
        if not self._can_control_tensiometer_hardware():
            return False

        try:
            if hasattr(self.cnc, "pulse_coil"):
                self.cnc.pulse_coil(coil, duration_ms)
            else:
                self.cnc._pulse_coil(coil, duration_ms)

            self.progress_label.setText(f"{action_name} enviado ao tenciÃƒÂ´metro")
            logger.info(f"Comando enviado ao tenciÃƒÂ´metro: {action_name} (M{coil})")
            return True
        except Exception as e:
            logger.exception(f"Erro ao executar comando {action_name} no tenciÃƒÂ´metro")
            QMessageBox.critical(
                self,
                "Erro no TenciÃƒÂ´metro",
                f"Falha ao executar '{action_name}':\n{e}"
            )
            return False

    def _turn_on_tensiometer(self):
        """Turn on tensiometer via PLC."""
        if self._pulse_tensiometer_coil(
            TENSIOMETER_POWER_COIL,
            "Ligar",
            duration_ms=TENSIOMETER_POWER_ON_PULSE_MS,
        ):
            QMessageBox.information(self, "TenciÃƒÂ´metro", "Comando de ligar enviado.")

    def _turn_off_tensiometer(self):
        """Turn off tensiometer via PLC."""
        if self._pulse_tensiometer_coil(
            TENSIOMETER_POWER_COIL,
            "Desligar",
            duration_ms=TENSIOMETER_POWER_OFF_PULSE_MS,
        ):
            QMessageBox.information(self, "TenciÃƒÂ´metro", "Comando de desligar enviado.")

    def _calibrate_tensiometer(self):
        """Send calibration command to tensiometer via PLC."""
        if self._pulse_tensiometer_coil(TENSIOMETER_CALIBRATE_COIL, "Calibrar"):
            QMessageBox.information(self, "TenciÃƒÂ´metro", "Comando de calibraÃƒÂ§ÃƒÂ£o enviado.")

    def _zero_tensiometer(self):
        """Send zero command to tensiometer via PLC."""
        if self._pulse_tensiometer_coil(TENSIOMETER_ZERO_COIL, "Zerar"):
            QMessageBox.information(self, "TenciÃƒÂ´metro", "Comando de zerar enviado.")

    # ==================== POSITION CAPTURE ====================

    def _capture_start_position(self):
        """Capture current CNC position as start point."""
        if self.cnc is None:
            QMessageBox.warning(self, "Aviso", "Controller CNC nÃ£o disponÃ­vel.")
            return

        try:
            x, y = self._read_current_xy_for_measurement()
            self.start_x_input.setText(f"{x:.2f}")
            self.start_y_input.setText(f"{y:.2f}")
            logger.info(f"PosiÃ§Ã£o inicial capturada: ({x:.2f}, {y:.2f})")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao ler posiÃ§Ã£o:\n{e}")

    def _capture_end_position(self):
        """Capture current CNC position as end point."""
        if self.cnc is None:
            QMessageBox.warning(self, "Aviso", "Controller CNC nÃ£o disponÃ­vel.")
            return

        try:
            x, y = self._read_current_xy_for_measurement()
            self.end_x_input.setText(f"{x:.2f}")
            self.end_y_input.setText(f"{y:.2f}")
            logger.info(f"PosiÃ§Ã£o final capturada: ({x:.2f}, {y:.2f})")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao ler posiÃ§Ã£o:\n{e}")

    def _measurement_coordinate_unit(self) -> str:
        """Return the coordinate unit currently available for automatic measurement."""
        pulses_per_mm = float(getattr(self.cnc, "pulses_per_mm", 1.0) or 1.0)
        return "mm" if pulses_per_mm > 1.0 else "pulsos"

    def _read_current_xy_for_measurement(self) -> tuple[float, float]:
        """
        Read current XY using the same unit expected by the automatic routine.

        If the machine is calibrated, use mm. Otherwise keep the legacy pulse mode.
        """
        pulses_per_mm = float(getattr(self.cnc, "pulses_per_mm", 1.0) or 1.0)

        if pulses_per_mm > 1.0 and hasattr(self.cnc, "get_current_position"):
            current = self.cnc.get_current_position()
            if isinstance(current, dict):
                if "x" in current and "y" in current:
                    return float(current["x"]), float(current["y"])
                if "X" in current and "Y" in current:
                    return float(current["X"]), float(current["Y"])

        return float(self.cnc.read_position('X')), float(self.cnc.read_position('Y'))

    # ==================== PATTERN TREE METHODS ====================

    def _load_patterns_tree(self):
        """Carrega padrÃµes na treeview da coluna esquerda."""
        self.pattern_tree.clear()
        patterns = self.pattern_manager.list_patterns()

        for pattern in patterns:
            item = QTreeWidgetItem()
            name = pattern.get('name', 'Sem Nome')
            grid_size = pattern.get('grid_size', 0)

            item.setText(0, name)
            item.setText(1, f"{grid_size}x{grid_size}")
            item.setData(0, Qt.ItemDataRole.UserRole, pattern)

            self.pattern_tree.addTopLevelItem(item)

        # Seleciona primeiro item se existir
        if self.pattern_tree.topLevelItemCount() > 0:
            self.pattern_tree.setCurrentItem(self.pattern_tree.topLevelItem(0))

    def _on_pattern_selected(self, item: QTreeWidgetItem, column: int):
        """Handle quando padrÃ£o Ã© selecionado na treeview."""
        pattern_data = item.data(0, Qt.ItemDataRole.UserRole)
        self.selected_pattern_name = pattern_data.get('name')
        self.current_pattern_label.setText(f"PadrÃ£o selecionado: {self.selected_pattern_name}")
        logger.info(f"PadrÃ£o selecionado na treeview: {self.selected_pattern_name}")

    def _on_pattern_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle para double-click - carrega padrÃ£o automaticamente."""
        self._on_pattern_selected(item, column)
        if self.selected_pattern_name:
            self._load_pattern(self.selected_pattern_name)

    # ==================== PATTERN HANDLERS ====================

    def _on_load_pattern(self):
        """Handle para carregar padrÃ£o salvo."""
        dialog = SelectPatternDialog(self.pattern_manager, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            pattern_name = dialog.get_selected_pattern()
            if pattern_name:
                self._load_pattern(pattern_name)

    def _load_pattern(self, pattern_name: str):
        """
        Carrega padrÃ£o de mediÃ§Ã£o salvo.

        Args:
            pattern_name: Nome do padrÃ£o
        """
        pattern = self.pattern_manager.load_pattern(pattern_name)
        if pattern is None:
            QMessageBox.critical(
                self, "Erro",
                f"NÃ£o foi possÃ­vel carregar o padrÃ£o '{pattern_name}'."
            )
            return

        # Aplica parÃ¢metros do padrÃ£o aos campos
        grid_params = pattern.grid_parameters

        self.start_x_input.setText(f"{grid_params.start_point[0]:.2f}")
        self.start_y_input.setText(f"{grid_params.start_point[1]:.2f}")
        self.end_x_input.setText(f"{grid_params.end_point[0]:.2f}")
        self.end_y_input.setText(f"{grid_params.end_point[1]:.2f}")
        self.grid_size_input.setText(str(grid_params.grid_size))
        self.z_height_input.setText(f"{grid_params.z_height:.2f}")
        self.z_move_input.setText(f"{grid_params.z_move:.2f}")

        # Atualiza label do padrÃ£o atual
        self.current_pattern_label.setText(f"PadrÃ£o atual: {pattern.name}")
        self.current_pattern_label.setStyleSheet(
            f"color: {COLORS.SUCCESS}; font-size: {TYPO.LABEL_SMALL}px; font-weight: bold;"
        )

        logger.info(f"PadrÃ£o carregado: {pattern.name}")
        QMessageBox.information(
            self, "PadrÃ£o Carregado",
            f"PadrÃ£o '{pattern.name}' carregado com sucesso!\n\n"
            f"Grid: {grid_params.grid_size}x{grid_params.grid_size}\n"
            f"Ãrea: ({grid_params.start_point[0]:.1f}, {grid_params.start_point[1]:.1f}) -> "
            f"({grid_params.end_point[0]:.1f}, {grid_params.end_point[1]:.1f})\n"
            f"Altura Z: {grid_params.z_height:.2f}mm"
        )

    def _on_save_pattern(self):
        """Handle para salvar configuraÃ§Ã£o atual como padrÃ£o."""
        # ObtÃ©m parÃ¢metros atuais
        try:
            start_x = float(self.start_x_input.text())
            start_y = float(self.start_y_input.text())
            end_x = float(self.end_x_input.text())
            end_y = float(self.end_y_input.text())
            grid_size = int(self.grid_size_input.text())
            z_height = float(self.z_height_input.text())
            z_move = float(self.z_move_input.text())

        except ValueError:
            QMessageBox.warning(
                self, "ParÃ¢metros InvÃ¡lidos",
                "Por favor, preencha todos os campos corretamente antes de salvar o padrÃ£o."
            )
            return

        # Abre diÃ¡logo de salvamento
        dialog = SavePatternDialog(
            parent=self,
            start_point=(start_x, start_y),
            end_point=(end_x, end_y),
            grid_size=grid_size,
            z_height=z_height,
            z_move=z_move,
            stabilization_time_ms=500,  # Default
            feed_rate=1000.0  # Default
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            name, description = dialog.get_pattern_data()

            # Cria padrÃ£o
            pattern = self.pattern_manager.create_pattern_from_dialog_params(
                name=name,
                description=description,
                start_point=(start_x, start_y),
                end_point=(end_x, end_y),
                grid_size=grid_size,
                z_height=z_height,
                z_move=z_move,
                stabilization_time_ms=dialog.stabilization_time_ms,
                feed_rate=dialog.feed_rate,
                created_by=""  # Poderia pegar do sistema de autenticaÃ§Ã£o
            )

            if pattern:
                success = self.pattern_manager.save_pattern(pattern)
                if success:
                    logger.info(f"PadrÃ£o salvo: {name}")
                    QMessageBox.information(
                        self, "PadrÃ£o Salvo",
                        f"PadrÃ£o '{name}' salvo com sucesso!\n\n"
                        f"Agora vocÃª pode reutilizar esta configuraÃ§Ã£o em futuras mediÃ§Ãµes."
                    )
                    # Atualiza label
                    self.current_pattern_label.setText(f"PadrÃ£o atual: {name}")
                    self.current_pattern_label.setStyleSheet(
                        f"color: {COLORS.SUCCESS}; font-size: {TYPO.LABEL_SMALL}px; font-weight: bold;"
                    )
                    self.selected_pattern_name = name
                    self._load_patterns_tree()
                else:
                    QMessageBox.critical(
                        self, "Erro",
                        "Erro ao salvar padrÃ£o. Verifique se o nome jÃ¡ existe."
                    )

    # ==================== MEASUREMENT HANDLERS ====================

    def _on_start(self):
        """Start measurement process."""
        if not self.tensiometer.is_connected:
            QMessageBox.warning(self, "Aviso", "Conecte o tensiÃ´metro primeiro.")
            return

        if self.orchestrator is None:
            self.orchestrator = MeasurementOrchestrator(self.cnc, self.tensiometer)

        # Get parameters from UI
        try:
            start_x = float(self.start_x_input.text())
            start_y = float(self.start_y_input.text())
            end_x = float(self.end_x_input.text())
            end_y = float(self.end_y_input.text())
            grid_size = int(self.grid_size_input.text())
            z_height = float(self.z_height_input.text())
            z_move = float(self.z_move_input.text())

            logger.info(f"ParÃ¢metros: start=({start_x}, {start_y}), end=({end_x}, {end_y}), "
                       f"grid={grid_size}x{grid_size}, Z={z_height}")

        except ValueError as e:
            QMessageBox.critical(self, "Erro de ParÃ¢metros",
                               "Preencha todos os campos corretamente.")
            return

        # Prepare measurement
        result = self.orchestrator.prepare_measurement(
            start_point=(start_x, start_y),
            end_point=(end_x, end_y),
            grid_size=grid_size,
            z_height=z_height,
            z_move=z_move,
            user_feed=None
        )

        if not result['success']:
            QMessageBox.critical(self, "Erro de ValidaÃ§Ã£o",
                               f"ParÃ¢metros invÃ¡lidos:\n{result['error']}")
            return

        # Store points
        self.current_points = result['points']

        # Show grid info
        stats = result['statistics']
        QMessageBox.information(
            self,
            "Grid Preparado",
            f"Grid {stats['grid_size']}x{stats['grid_size']} gerado:\n"
            f"Total de pontos: {stats['total_points']}\n"
            f"DistÃ¢ncia total: {stats['total_distance_mm']} mm"
        )

        # Habilita botÃ£o de salvar padrÃ£o apÃ³s grid preparado com sucesso
        self.btn_save_pattern.setEnabled(True)

        # Start measurement
        success = self.orchestrator.start_measurement(
            points=self.current_points,
            on_progress=self._on_progress,
            on_measurement=self._on_measurement,
            on_complete=self._on_complete,
            on_error=self._on_error
        )

        if success:
            self._set_measuring_state(True)
            logger.info("MediÃ§Ã£o iniciada")
        else:
            QMessageBox.critical(self, "Erro", "Falha ao iniciar mediÃ§Ã£o.")

    def _on_stop(self):
        """Stop measurement."""
        if self.orchestrator:
            self.orchestrator.stop_measurement()
            self._set_measuring_state(False)
            logger.info("MediÃ§Ã£o interrompida")

    def _on_progress(self, current: int, total: int, message: str):
        """Handle progress update."""
        percentage = int((current / total) * 100)
        self.progress_bar.setValue(percentage)
        self.progress_label.setText(message)
        logger.debug(f"Progresso: {current}/{total} ({percentage}%)")

    def _on_measurement(self, measurement_dict: dict):
        """Handle individual measurement."""
        value = measurement_dict.get('tension', '0')
        self.current_value_label.setText(f"Ãšltima leitura: {value} N/cmÂ²")
        logger.debug(f"MediÃ§Ã£o: {value} N/cmÂ²")

    def _on_complete(self, results: dict):
        """Handle measurement completion."""
        self._set_measuring_state(False)

        # Show results
        analysis = results.get('analysis', {})
        if 'statistics' in analysis:
            stats = analysis['statistics']
            msg = (
                f"âœ… MediÃ§Ã£o ConcluÃ­da!\n\n"
                f"MÃ©dia: {stats['mean']} N/cmÂ²\n"
                f"Mediana: {stats['median']} N/cmÂ²\n"
                f"Desvio padrÃ£o: {stats['std']} N/cmÂ²\n"
                f"MÃ­nimo: {stats['min']} N/cmÂ²\n"
                f"MÃ¡ximo: {stats['max']} N/cmÂ²\n\n"
            )

            if 'classification' in analysis:
                cls = analysis['classification']
                msg += f"ClassificaÃ§Ã£o: {cls['category']}\n{cls['message']}"

            saved_path = results.get('saved_to')
            if saved_path:
                msg += f"\n\nSalvo em:\n{saved_path}"

            QMessageBox.information(self, "MediÃ§Ã£o ConcluÃ­da", msg)

        # Generate and show report
        if self.orchestrator:
            report = self.orchestrator.get_report()
            logger.info("\n" + report)

    def _on_error(self, error_message: str):
        """Handle measurement error."""
        self._set_measuring_state(False)
        QMessageBox.critical(self, "Erro na MediÃ§Ã£o", error_message)

    def _set_measuring_state(self, measuring: bool):
        """Update UI state based on measurement status."""
        self.is_measuring = measuring

        if measuring:
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.progress_bar.setValue(0)
        else:
            self.start_btn.setEnabled(self.tensiometer.is_connected)
            self.stop_btn.setEnabled(False)

    # ==================== LIFECYCLE ====================

    def closeEvent(self, a0: any) -> None:
        """Handle dialog close."""
        # Stop measurement if running
        if self.is_measuring:
            reply = QMessageBox.question(
                self,
                "MediÃ§Ã£o em Andamento",
                "MediÃ§Ã£o ainda estÃ¡ rodando. Deseja parar e fechar?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._on_stop()
            else:
                a0.ignore()
                return

        # Cleanup
        if self.orchestrator:
            self.orchestrator.cleanup()

        if self.tensiometer.is_connected:
            self.tensiometer.disconnect()

        a0.accept()
        logger.debug("DiÃ¡logo fechado")

