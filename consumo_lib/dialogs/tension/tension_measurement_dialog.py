"""
Tension Measurement Dialog (Refactored)

PyQt6 dialog for tension measurement of stencils.
Uses MeasurementOrchestrator for business logic separation.

Created: 2026-01-14 (Phase 1 - SOLID Refactoring)
Refactored from: aoi_lib/stencil_tension.py (lines 447-1409, 962 lines)
"""

import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QGroupBox,
    QProgressBar, QMessageBox, QWidget
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QDoubleValidator, QIntValidator

from consumo_lib.ui import COLORS, TYPO, SPACE, DIM

# Import refactored modules
from aoi_lib.tensiometer import (
    MeasurementOrchestrator,
    TensiometerSerialManager,
    ValidationError
)

logger = logging.getLogger(__name__)


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

        # Business logic components
        self.tensiometer = TensiometerSerialManager()
        self.orchestrator: Optional[MeasurementOrchestrator] = None

        # UI State
        self.current_points = []
        self.is_measuring = False

        # Setup UI
        self.setWindowTitle("Medição de Tensão do Stencil")
        self.setMinimumSize(700, 500)
        self._build_ui()

        # Connect tensiometer
        self._refresh_ports()

    def _build_ui(self):
        """Build user interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)

        # ==================== TENSIONOMETER CONNECTION ====================
        conn_group = QGroupBox("🔌 Conexão do Tensiômetro")
        conn_layout = QGridLayout(conn_group)
        conn_layout.setSpacing(8)

        # Port selection
        conn_layout.addWidget(QLabel("Porta:"), 0, 0)
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(120)
        conn_layout.addWidget(self.port_combo, 0, 1)

        # Refresh ports button
        self.refresh_ports_btn = QPushButton("🔄")
        self.refresh_ports_btn.setMaximumWidth(40)
        self.refresh_ports_btn.clicked.connect(self._refresh_ports)
        conn_layout.addWidget(self.refresh_ports_btn, 0, 2)

        # Connect/Disconnect button
        self.connect_btn = QPushButton("🔗 Conectar")
        self.connect_btn.clicked.connect(self._toggle_connection)
        conn_layout.addWidget(self.connect_btn, 0, 3, 1, 2)

        # Status label
        self.conn_status_label = QLabel("Status: Desconectado")
        self.conn_status_label.setStyleSheet(f"color: {COLORS.TEXT_HINT};")
        conn_layout.addWidget(self.conn_status_label, 1, 0, 1, 5)

        # Test button
        self.test_btn = QPushButton("🧪 Testar Leitura")
        self.test_btn.clicked.connect(self._test_reading)
        self.test_btn.setEnabled(False)
        conn_layout.addWidget(self.test_btn, 2, 0, 1, 5)

        main_layout.addWidget(conn_group)

        # ==================== GRID CONFIGURATION ====================
        grid_group = QGroupBox("📐 Configuração do Grid")
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

        self.capture_start_btn = QPushButton("📍 Capturar")
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

        self.capture_end_btn = QPushButton("📍 Capturar")
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
        grid_layout.addWidget(QLabel("Altura Medição (Z):"), 3, 0)
        self.z_height_input = QLineEdit("5.0")
        self.z_height_input.setValidator(QDoubleValidator())
        self.z_height_input.setMaximumWidth(80)
        grid_layout.addWidget(self.z_height_input, 3, 1)

        grid_layout.addWidget(QLabel("Altura Movimento:"), 3, 2)
        self.z_move_input = QLineEdit("10.0")
        self.z_move_input.setValidator(QDoubleValidator())
        self.z_move_input.setMaximumWidth(80)
        grid_layout.addWidget(self.z_move_input, 3, 3)

        main_layout.addWidget(grid_group)

        # ==================== PROGRESS DISPLAY ====================
        progress_group = QGroupBox("📊 Progresso da Medição")
        progress_layout = QVBoxLayout(progress_group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("Pronto para iniciar")
        progress_layout.addWidget(self.progress_label)

        self.current_value_label = QLabel("Última leitura: --")
        self.current_value_label.setStyleSheet(f"font-size: {TYPO.BODY_MEDIUM}px; font-weight: bold;")
        progress_layout.addWidget(self.current_value_label)

        main_layout.addWidget(progress_group)

        # ==================== CONTROL BUTTONS ====================
        btn_layout = QHBoxLayout()

        self.start_btn = QPushButton("▶ Iniciar Medição")
        self.start_btn.setEnabled(False)
        self.start_btn.clicked.connect(self._on_start)
        self.start_btn.setStyleSheet(f"background-color: {COLORS.PRIMARY}; color: {COLORS.ON_PRIMARY}; font-weight: bold; padding: {SPACE.MD}px;")
        btn_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("⏹ Parar")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._on_stop)
        self.stop_btn.setStyleSheet(f"background-color: {COLORS.ERROR}; color: {COLORS.TEXT_PRIMARY}; font-weight: bold; padding: {SPACE.MD}px;")
        btn_layout.addWidget(self.stop_btn)

        self.close_btn = QPushButton("Fechar")
        self.close_btn.clicked.connect(self.close)
        btn_layout.addWidget(self.close_btn)

        main_layout.addLayout(btn_layout)

    # ==================== CONNECTION HANDLERS ====================

    def _refresh_ports(self):
        """Refresh list of available serial ports."""
        ports = self.tensiometer.get_available_ports()
        self.port_combo.clear()
        self.port_combo.addItems(ports)
        logger.debug(f"Portas disponíveis: {ports}")

    def _toggle_connection(self):
        """Toggle tensiometer connection."""
        if self.tensiometer.is_connected:
            self.tensiometer.disconnect()
            self._update_connection_ui(False)
            logger.info("Tensiômetro desconectado")
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
                logger.info(f"Tensiômetro conectado em {port}")
            else:
                QMessageBox.critical(
                    self,
                    "Erro de Conexão",
                    f"Falha ao conectar em {port}:\n{self.tensiometer.last_error}"
                )

    def _update_connection_ui(self, connected: bool):
        """Update UI based on connection state."""
        if connected:
            self.connect_btn.setText("🔌 Desconectar")
            self.conn_status_label.setText("Status: ✅ Conectado")
            self.conn_status_label.setStyleSheet(f"color: {COLORS.SUCCESS};")
            self.test_btn.setEnabled(True)
            self.start_btn.setEnabled(True)
        else:
            self.connect_btn.setText("🔗 Conectar")
            self.conn_status_label.setText("Status: Desconectado")
            self.conn_status_label.setStyleSheet(f"color: {COLORS.TEXT_HINT};")
            self.test_btn.setEnabled(False)
            self.start_btn.setEnabled(False)

    def _test_reading(self):
        """Test tensiometer reading."""
        if not self.tensiometer.is_connected:
            QMessageBox.warning(self, "Aviso", "Conecte o tensiômetro primeiro.")
            return

        value = self.tensiometer.read_tension_value()
        QMessageBox.information(
            self,
            "Leitura Teste",
            f"Valor lido: {value} N/cm²"
        )
        logger.info(f"Leitura teste: {value} N/cm²")

    # ==================== POSITION CAPTURE ====================

    def _capture_start_position(self):
        """Capture current CNC position as start point."""
        if self.cnc is None:
            QMessageBox.warning(self, "Aviso", "Controller CNC não disponível.")
            return

        try:
            x = self.cnc.read_position('X')
            y = self.cnc.read_position('Y')
            self.start_x_input.setText(f"{x:.2f}")
            self.start_y_input.setText(f"{y:.2f}")
            logger.info(f"Posição inicial capturada: ({x:.2f}, {y:.2f})")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao ler posição:\n{e}")

    def _capture_end_position(self):
        """Capture current CNC position as end point."""
        if self.cnc is None:
            QMessageBox.warning(self, "Aviso", "Controller CNC não disponível.")
            return

        try:
            x = self.cnc.read_position('X')
            y = self.cnc.read_position('Y')
            self.end_x_input.setText(f"{x:.2f}")
            self.end_y_input.setText(f"{y:.2f}")
            logger.info(f"Posição final capturada: ({x:.2f}, {y:.2f})")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao ler posição:\n{e}")

    # ==================== MEASUREMENT HANDLERS ====================

    def _on_start(self):
        """Start measurement process."""
        if not self.tensiometer.is_connected:
            QMessageBox.warning(self, "Aviso", "Conecte o tensiômetro primeiro.")
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

            logger.info(f"Parâmetros: start=({start_x}, {start_y}), end=({end_x}, {end_y}), "
                       f"grid={grid_size}x{grid_size}, Z={z_height}")

        except ValueError as e:
            QMessageBox.critical(self, "Erro de Parâmetros",
                               "Preencha todos os campos corretamente.")
            return

        # Prepare measurement
        result = self.orchestrator.prepare_measurement(
            start_point=(start_x, start_y),
            end_point=(end_x, end_y),
            grid_size=grid_size,
            z_height=z_height,
            z_move=z_move
        )

        if not result['success']:
            QMessageBox.critical(self, "Erro de Validação",
                               f"Parâmetros inválidos:\n{result['error']}")
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
            f"Distância total: {stats['total_distance_mm']} mm"
        )

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
            logger.info("Medição iniciada")
        else:
            QMessageBox.critical(self, "Erro", "Falha ao iniciar medição.")

    def _on_stop(self):
        """Stop measurement."""
        if self.orchestrator:
            self.orchestrator.stop_measurement()
            self._set_measuring_state(False)
            logger.info("Medição interrompida")

    def _on_progress(self, current: int, total: int, message: str):
        """Handle progress update."""
        percentage = int((current / total) * 100)
        self.progress_bar.setValue(percentage)
        self.progress_label.setText(message)
        logger.debug(f"Progresso: {current}/{total} ({percentage}%)")

    def _on_measurement(self, measurement_dict: dict):
        """Handle individual measurement."""
        value = measurement_dict.get('tension', '0')
        self.current_value_label.setText(f"Última leitura: {value} N/cm²")
        logger.debug(f"Medição: {value} N/cm²")

    def _on_complete(self, results: dict):
        """Handle measurement completion."""
        self._set_measuring_state(False)

        # Show results
        analysis = results.get('analysis', {})
        if 'statistics' in analysis:
            stats = analysis['statistics']
            msg = (
                f"✅ Medição Concluída!\n\n"
                f"Média: {stats['mean']} N/cm²\n"
                f"Mediana: {stats['median']} N/cm²\n"
                f"Desvio padrão: {stats['std']} N/cm²\n"
                f"Mínimo: {stats['min']} N/cm²\n"
                f"Máximo: {stats['max']} N/cm²\n\n"
            )

            if 'classification' in analysis:
                cls = analysis['classification']
                msg += f"Classificação: {cls['category']}\n{cls['message']}"

            saved_path = results.get('saved_to')
            if saved_path:
                msg += f"\n\n💾 Salvo em:\n{saved_path}"

            QMessageBox.information(self, "Medição Concluída", msg)

        # Generate and show report
        if self.orchestrator:
            report = self.orchestrator.get_report()
            logger.info("\n" + report)

    def _on_error(self, error_message: str):
        """Handle measurement error."""
        self._set_measuring_state(False)
        QMessageBox.critical(self, "Erro na Medição", error_message)

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

    def closeEvent(self, event):
        """Handle dialog close."""
        # Stop measurement if running
        if self.is_measuring:
            reply = QMessageBox.question(
                self,
                "Medição em Andamento",
                "Medição ainda está rodando. Deseja parar e fechar?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._on_stop()
            else:
                event.ignore()
                return

        # Cleanup
        if self.orchestrator:
            self.orchestrator.cleanup()

        if self.tensiometer.is_connected:
            self.tensiometer.disconnect()

        event.accept()
        logger.debug("Diálogo fechado")
