"""
CalibrationController - Handles CNC movement calibration.

Extracted from MainWindow.show_calibration_dialog(), apply_calibration(),
and show_calibration_test_dialog().
Manages machine parameters (pulses per revolution, leadscrew pitch) and
calibration testing.
"""

import logging
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QMessageBox, QGridLayout
)

# Add project root to path for imports
import sys
from pathlib import Path as _Path
_current_file = _Path(__file__).resolve()
_root_dir = _current_file.parent.parent.parent
if str(_root_dir) not in sys.path:
    sys.path.insert(0, str(_root_dir))

from aoi_lib.plc_axis_controller import PLCAxisController

logger = logging.getLogger("consumo_lib")


class CalibrationController(QObject):
    """
    Controller for CNC movement calibration.

    Signals:
        calibration_applied: Emitted when calibration is applied (steps_per_mm)
        calibration_completed: Emitted when calibration dialog completes (pulses, fuso_pitch)
        test_completed: Emitted when calibration test completes (axis, distance, actual_distance)
    """

    calibration_applied = pyqtSignal(float)  # steps_per_mm
    calibration_completed = pyqtSignal(float, float)  # pulses, fuso_pitch
    test_completed = pyqtSignal(int, float, float)  # axis, distance, actual_distance

    def __init__(self, controller, config_manager, parent=None):
        """
        Initialize CalibrationController.

        Args:
            controller: CNCAOIController instance
            config_manager: AOIConfigManager instance
            parent: Optional parent QObject
        """
        super().__init__(parent)
        self.controller = controller
        self.config = config_manager

        # UI widgets (filled by dialogs)
        self.pulses_input = None
        self.fuso_input = None
        self.calibration_test_result = None

    def show_dialog(self, parent_widget=None, pulses_value: str = "", fuso_value: str = ""):
        """
        Show calibration configuration dialog.

        Args:
            parent_widget: Parent QWidget (usually MainWindow)
            pulses_value: Current pulses per revolution value (for display)
            fuso_value: Current fuso pitch value (for display)

        Returns:
            QDialog instance
        """
        dialog = QDialog(parent_widget)
        dialog.setWindowTitle("Calibração do Sistema CNC")
        dialog.setMinimumWidth(500)

        layout = QVBoxLayout(dialog)

        # Physical parameters group
        param_group = QGroupBox("Parâmetros da Máquina")
        param_layout = QGridLayout(param_group)

        param_layout.addWidget(QLabel("Pulsos por Revolução:"), 0, 0)
        self.pulses_input = QLineEdit(pulses_value)
        param_layout.addWidget(self.pulses_input, 0, 1)

        param_layout.addWidget(QLabel("Passo do Fuso (mm):"), 1, 0)
        self.fuso_input = QLineEdit(fuso_value)
        param_layout.addWidget(self.fuso_input, 1, 1)

        param_layout.addWidget(QLabel("Steps/mm calculado:"), 2, 0)
        steps_mm_result = QLabel("Calculando...")
        param_layout.addWidget(steps_mm_result, 2, 1)

        # Update calculation when values change
        def update_calculation():
            try:
                pulses = float(self.pulses_input.text())
                fuso = float(self.fuso_input.text())
                steps_mm = pulses / fuso
                steps_mm_result.setText(f"{steps_mm:.3f} steps/mm")
            except:
                steps_mm_result.setText("Erro no cálculo")

        self.pulses_input.textChanged.connect(update_calculation)
        self.fuso_input.textChanged.connect(update_calculation)
        update_calculation()  # Execute initial calculation

        layout.addWidget(param_group)

        # Action buttons
        buttons_layout = QHBoxLayout()

        apply_btn = QPushButton("Aplicar Parâmetros")

        def apply_and_close():
            dialog.accept()
            self.apply_calibration(self.pulses_input.text(), self.fuso_input.text())

        apply_btn.clicked.connect(apply_and_close)

        test_btn = QPushButton("Testar Calibração")
        test_btn.clicked.connect(lambda: [dialog.accept(), self.show_test_dialog(parent_widget)])

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(dialog.reject)

        buttons_layout.addWidget(apply_btn)
        buttons_layout.addWidget(test_btn)
        buttons_layout.addWidget(cancel_btn)

        layout.addLayout(buttons_layout)

        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            # Emit completion signal
            try:
                pulses = float(self.pulses_input.text())
                fuso = float(self.fuso_input.text())
                self.calibration_completed.emit(pulses, fuso)
            except ValueError:
                pass

        return dialog

    def apply_calibration(self, pulses_value: str = None, fuso_value: str = None):
        """
        Apply movement calibration based on user-provided values.
        Sends direct commands to GRBL to configure steps/mm.

        Args:
            pulses_value: Optional pulses per revolution string (uses UI if None)
            fuso_value: Optional fuso pitch string (uses UI if None)
        """
        # Get values from parameters or UI
        if pulses_value is None and hasattr(self, 'pulses_input'):
            pulses_value = self.pulses_input.text()
        if fuso_value is None and hasattr(self, 'fuso_input'):
            fuso_value = self.fuso_input.text()

        if not self.controller.cnc.is_connected:
            QMessageBox.warning(None, "Erro", "CNC não conectada. Conecte primeiro.")
            return

        # If PLC, update only internal conversion factor
        if isinstance(self.controller.cnc, PLCAxisController):
            try:
                pulses = float(pulses_value)
                fuso_pass = float(fuso_value)

                # Update PLC pulses/mm conversion factor
                self.controller.cnc.pulses_per_mm = pulses / fuso_pass

                # Save to JSON to persist configuration
                self.config.remember_calibration(pulses, fuso_pass)

                logger.info(f"Calibração PLC aplicada: {pulses / fuso_pass:.3f} pulsos/mm")
                QMessageBox.information(
                    None, "Calibração PLC",
                    f"Fator de conversão atualizado:\n{pulses / fuso_pass:.3f} pulsos/mm"
                )

                # Emit signal
                self.calibration_applied.emit(pulses / fuso_pass)

            except ValueError:
                QMessageBox.warning(None, "Erro", "Valores de calibração inválidos.")
            return

        # If GRBL, check if grbl attribute exists
        if not hasattr(self.controller.cnc, 'grbl') or not self.controller.cnc.grbl:
            QMessageBox.warning(None, "Erro", "Controlador GRBL não disponível.")
            return

        try:
            pulses = float(pulses_value)
            fuso_pass = float(fuso_value)

            # Calculate steps/mm: (pulses per revolution) / (leadscrew pitch in mm)
            steps_per_mm = pulses / fuso_pass

            # Store calculated value
            self.controller.cnc.steps_to_mm_factor = fuso_pass / pulses

            # Send commands to configure GRBL
            logger.info(f"CALIBRAÇÃO: Configurando steps/mm para {steps_per_mm}")

            # Ask user to confirm these values
            reply = QMessageBox.question(
                None,
                "Confirmar Calibração",
                f"Deseja enviar os seguintes parâmetros para o GRBL?\n\n"
                f"Steps/mm eixo X: {steps_per_mm:.3f}\n"
                f"Steps/mm eixo Y: {steps_per_mm:.3f}\n\n"
                f"Isso irá alterar a configuração do controlador.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                # Commands to configure X and Y axes
                self.controller.cnc.grbl.send_immediately(f"$100={steps_per_mm:.3f}")

                from PyQt6.QtCore import QTimer
                QTimer.singleShot(100, lambda: self.controller.cnc.grbl.send_immediately(f"$101={steps_per_mm:.3f}"))

                # Prompt user to run calibration test
                QTimer.singleShot(500, lambda: self.show_test_dialog(None))

                logger.info(f"Calibração aplicada: {steps_per_mm:.3f} steps/mm")

                # Save to JSON
                self.config.remember_calibration(pulses, fuso_pass)

                # Emit signal
                self.calibration_applied.emit(steps_per_mm)

            else:
                logger.info("Calibração cancelada pelo usuário")

        except ValueError:
            QMessageBox.warning(None, "Erro", "Valores de calibração inválidos.")

    def show_test_dialog(self, parent_widget=None):
        """
        Show dialog to test current calibration.

        Args:
            parent_widget: Parent QWidget (usually MainWindow)

        Returns:
            QDialog instance
        """
        dialog = QDialog(parent_widget)
        dialog.setWindowTitle("Teste de Calibração")
        dialog.setMinimumWidth(400)

        layout = QVBoxLayout(dialog)

        # Instructions
        instructions = QLabel(
            "Para testar a calibração:\n\n"
            "1. Coloque um papel milimetrado ou uma régua sob a cabeça da máquina\n"
            "2. Escolha uma distância de teste\n"
            "3. Clique em 'Mover X' ou 'Mover Y' para testar cada eixo\n"
            "4. Verifique se o deslocamento físico corresponde ao valor escolhido\n"
            "5. Se necessário, ajuste os valores de calibração e aplique novamente"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Test distance
        test_layout = QHBoxLayout()
        test_layout.addWidget(QLabel("Distância de teste:"))
        distance_input = QLineEdit("10")
        test_layout.addWidget(distance_input)
        test_layout.addWidget(QLabel("mm"))
        layout.addLayout(test_layout)

        # Test buttons
        buttons_layout = QHBoxLayout()

        move_x_btn = QPushButton("Mover X")
        move_x_btn.clicked.connect(lambda: self.test_calibration_move(0, float(distance_input.text())))

        move_y_btn = QPushButton("Mover Y")
        move_y_btn.clicked.connect(lambda: self.test_calibration_move(1, float(distance_input.text())))

        reset_position_btn = QPushButton("Zerar Posição")
        reset_position_btn.clicked.connect(self.set_zero_position)

        buttons_layout.addWidget(move_x_btn)
        buttons_layout.addWidget(move_y_btn)
        buttons_layout.addWidget(reset_position_btn)

        layout.addLayout(buttons_layout)

        # Results
        result_group = QGroupBox("Resultados")
        result_layout = QVBoxLayout(result_group)

        self.calibration_test_result = QLabel("Execute um teste para ver os resultados")
        result_layout.addWidget(self.calibration_test_result)

        layout.addWidget(result_group)

        # Control buttons
        control_layout = QHBoxLayout()
        close_btn = QPushButton("Concluir")
        close_btn.clicked.connect(dialog.accept)
        control_layout.addWidget(close_btn)

        layout.addLayout(control_layout)

        dialog.exec()

        return dialog

    def test_calibration_move(self, axis: int, distance: float):
        """
        Perform a test movement for calibration.

        Args:
            axis: 0 for X, 1 for Y
            distance: Distance in mm to move
        """
        if not self.controller.cnc.is_connected:
            QMessageBox.warning(None, "Erro", "CNC não conectada")
            return

        try:
            # Capture initial position
            initial_position = self.controller.cnc.get_current_position()

            # Prepare command
            # Set absolute mode for precision
            if hasattr(self.controller.cnc, 'grbl') and self.controller.cnc.grbl:
                self.controller.cnc.grbl.send_immediately("G90")

            # Calculate absolute position to reach
            target_position = {}
            target_position['x'] = initial_position['x'] + distance if axis == 0 else initial_position['x']
            target_position['y'] = initial_position['y'] + distance if axis == 1 else initial_position['y']

            # Send movement as absolute coordinate
            if axis == 0:
                self.controller.cnc.move_to_absolute_position(target_position['x'], None, 500)
            else:
                self.controller.cnc.move_to_absolute_position(None, target_position['y'], 500)
            self.controller.cnc.wait_for_idle()

            # Wait a bit for movement to complete
            from PyQt6.QtCore import QTimer
            import time
            time.sleep(0.5)

            # Capture final position
            final_position = self.controller.cnc.get_current_position()

            # Calculate actual movement
            if axis == 0:
                actual_distance = final_position['x'] - initial_position['x']
            else:
                actual_distance = final_position['y'] - initial_position['y']

            # Update result display
            axis_name = "X" if axis == 0 else "Y"
            result_text = (
                f"Teste Eixo {axis_name}:\n"
                f"Distância solicitada: {distance:.3f} mm\n"
                f"Posição inicial: ({initial_position['x']:.3f}, {initial_position['y']:.3f})\n"
                f"Posição final: ({final_position['x']:.3f}, {final_position['y']:.3f})\n"
                f"Distância realizada: {actual_distance:.3f} mm\n"
                f"Erro: {abs(actual_distance - distance):.3f} mm"
            )

            if self.calibration_test_result:
                self.calibration_test_result.setText(result_text)

            logger.info(f"Teste de calibração {axis_name}: {distance:.3f} mm solicitado, {actual_distance:.3f} mm realizado")

            # Emit signal
            self.test_completed.emit(axis, distance, actual_distance)

        except Exception as e:
            error_msg = f"Erro durante teste de calibração: {e}"
            if self.calibration_test_result:
                self.calibration_test_result.setText(error_msg)
            logger.error(error_msg)

    def set_zero_position(self):
        """Set current position as zero (origin)."""
        if not self.controller.cnc.is_connected:
            QMessageBox.warning(None, "Erro", "CNC não conectada")
            return

        try:
            # Send command to set zero position
            if hasattr(self.controller.cnc, 'grbl') and self.controller.cnc.grbl:
                # For GRBL, set workspace zero
                self.controller.cnc.grbl.send_immediately("G10 X0 Y0")
            elif isinstance(self.controller.cnc, PLCAxisController):
                # For PLC, reset current position
                self.controller.cnc.reset_position()

            logger.info("Posição zerada (origem definida)")
            QMessageBox.information(None, "Posição Zerada", "Posição atual definida como origem (0, 0)")

        except Exception as e:
            error_msg = f"Erro ao zerar posição: {e}"
            logger.error(error_msg)
            QMessageBox.warning(None, "Erro", error_msg)

    # =========================================================================
    # UI HANDLERS (Migrados do SignalAggregator)
    # =========================================================================

    def setup_ui_handlers(self):
        """
        Configura handlers de UI para signals de calibração.

        Este método conecta os signals internos do CalibrationController
        aos métodos que atualizam a UI do main_window.

        Deve ser chamado durante a inicialização do main_window.
        """
        # Conectar signals de teste a handlers de UI
        if hasattr(self, 'test_completed'):
            self.test_completed.connect(self._on_test_completed_show_result)

        logger.debug("UI handlers conectados no CalibrationController")

    def _on_test_completed_show_result(self, axis, distance, actual_distance):
        """
        Mostra resultado do teste de calibração.

        Args:
            axis: Eixo testado
            distance: Distância esperada
            actual_distance: Distância medida
        """
        # Calcula erro
        error_mm = abs(actual_distance - distance)
        error_percent = (error_mm / distance) * 100 if distance > 0 else 0

        movement_ok = error_percent < 5.0  # Tolerância de 5%

        status = "OK" if movement_ok else "FALHOU"
        message = f"Eixo {axis}: {distance:.1f}mm medido, {actual_distance:.1f}mm real (erro: {error_percent:.1f}%)"

        logger.info(f"Teste de calibração: {status} - {message}")

        from PyQt6.QtWidgets import QMessageBox
        if movement_ok:
            QMessageBox.information(
                self.parent(),
                "Teste de Calibração",
                f"Teste concluído com sucesso!\n\n{message}"
            )
        else:
            QMessageBox.warning(
                self.parent(),
                "Teste de Calibração",
                f"Teste falhou!\n\n{message}"
            )

        if hasattr(self.parent(), 'statusBar'):
            self.parent().statusBar().showMessage(f"Teste de calibração: {status}", 3000)

    def on_calibration_applied_update_config(self, steps_x, steps_y):
        """
        Atualiza configuração quando calibração é aplicada.

        Args:
            steps_x: Passos por mm no eixo X
            steps_y: Passos por mm no eixo Y
        """
        logger.info(f"Calibração aplicada: X={steps_x} steps/mm, Y={steps_y} steps/mm")

        # Atualiza configurações no config_manager se disponível
        if hasattr(self, 'config') and self.config:
            self.config.set("connections", "pulses_per_rev", value=int(steps_x * 10))
            self.config.set("connections", "fuso_pitch", value=10.0)
            self.config.save()

        if hasattr(self.parent(), 'statusBar'):
            self.parent().statusBar().showMessage(
                f"Calibração aplicada: {steps_x:.2f} x {steps_y:.2f} steps/mm",
                3000
            )

    def on_calibration_completed_update_status(self):
        """
        Atualiza statusBar quando calibração é completada.
        """
        logger.info("Calibração completada")
        if hasattr(self.parent(), 'statusBar'):
            self.parent().statusBar().showMessage("Calibração completada com sucesso", 3000)
