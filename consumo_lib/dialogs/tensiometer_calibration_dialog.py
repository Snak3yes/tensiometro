"""
Dialogo dedicado para calibracao do medidor de tensao.
"""

import logging
import time

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QRect
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import (
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from aoi_lib.config_manager import AOIConfigManager
from consumo_lib.ui import SPACE
from consumo_lib.ui.widget_standards import StandardButton
from consumo_lib.widgets.movement_control import MovementControlWidget

logger = logging.getLogger(__name__)

HOME_ALL_COIL = 1350
HOME_COMPLETE_COIL = 33
TENSIOMETER_POWER_COIL = 20
TENSIOMETER_POWER_ON_PULSE_MS = 100
TENSIOMETER_POWER_OFF_PULSE_MS = 3000
TENSIOMETER_CALIBRATE_COIL = 23
TENSIOMETER_ZERO_COIL = 24

CALIBRATION_X_PULSES = 33871
CALIBRATION_Y_PULSES = 34130
CALIBRATION_Z_PULSES = 9207
CALIBRATION_SETTLE_DELAY_SEC = 2.0
HOME_TIMEOUT_SEC = 120
MOVE_TIMEOUT_SEC = 120


class TensiometerAutoCalibrationWorker(QThread):
    """Executa a rotina automatica de calibracao em background."""

    status_changed = pyqtSignal(str)
    calibration_finished = pyqtSignal()
    calibration_failed = pyqtSignal(str)

    def __init__(self, cnc):
        super().__init__()
        self.cnc = cnc

    def run(self) -> None:
        try:
            self._ensure_plc_ready()

            self._run_home_cycle("Executando home inicial.")

            self._emit_status("Ligando medidor de tensao.")
            self._pulse_coil(TENSIOMETER_POWER_COIL, TENSIOMETER_POWER_ON_PULSE_MS)

            self._emit_status("Zerando medidor de tensao.")
            self._pulse_coil(TENSIOMETER_ZERO_COIL, 100)

            self._emit_status(
                f"Movendo X/Y para X={CALIBRATION_X_PULSES} Y={CALIBRATION_Y_PULSES}."
            )
            self._move_absolute_pulses({"X": CALIBRATION_X_PULSES, "Y": CALIBRATION_Y_PULSES})

            self._emit_status(f"Descendo Z para {CALIBRATION_Z_PULSES}.")
            self._move_absolute_pulses({"Z": CALIBRATION_Z_PULSES})

            self._emit_status(
                f"Aguardando {CALIBRATION_SETTLE_DELAY_SEC:.1f}s antes da calibracao."
            )
            time.sleep(CALIBRATION_SETTLE_DELAY_SEC)

            self._emit_status("Enviando comando de calibracao do medidor.")
            self._pulse_coil(TENSIOMETER_CALIBRATE_COIL, 100)

            self._run_home_cycle("Retornando para home final.")

            self._emit_status("Calibracao automatica concluida. Equipamento em home.")
            self.calibration_finished.emit()
        except Exception as exc:
            logger.exception("Falha na calibracao automatica do medidor")
            self.calibration_failed.emit(str(exc))

    def _ensure_plc_ready(self) -> None:
        if self.cnc is None:
            raise RuntimeError("Controlador CNC nao disponivel.")
        if not getattr(self.cnc, "is_connected", False):
            raise RuntimeError("Conecte o CLP antes de iniciar a calibracao.")
        if not hasattr(self.cnc, "pulse_coil") and not hasattr(self.cnc, "_pulse_coil"):
            raise RuntimeError("O backend atual nao suporta pulso de coil.")

    def _emit_status(self, message: str) -> None:
        logger.info("Calibracao do medidor: %s", message)
        self.status_changed.emit(message)

    def _pulse_coil(self, coil: int, duration_ms: int) -> None:
        if hasattr(self.cnc, "pulse_coil"):
            self.cnc.pulse_coil(coil, duration_ms)
        else:
            self.cnc._pulse_coil(coil, duration_ms)

    def _run_home_cycle(self, status_message: str) -> None:
        self._emit_status(status_message)
        self._pulse_coil(HOME_ALL_COIL, 100)
        self._wait_for_home_complete()

    def _wait_for_home_complete(self) -> None:
        if not hasattr(self.cnc, "read_coil"):
            time.sleep(5.0)
            return

        started_at = time.time()
        while time.time() - started_at < HOME_TIMEOUT_SEC:
            if self.cnc.read_coil(HOME_COMPLETE_COIL):
                self._emit_status("Home global concluido.")
                return
            time.sleep(0.1)

        raise RuntimeError("Timeout aguardando conclusao do homing global (M33).")

    def _move_absolute_pulses(self, targets_pulses: dict[str, int]) -> None:
        if hasattr(self.cnc, "_apply_motion_pulses"):
            self.cnc._apply_motion_pulses(targets_pulses)
        else:
            pulses_per_mm = float(getattr(self.cnc, "pulses_per_mm", 0) or 0)
            if pulses_per_mm <= 0:
                raise RuntimeError("pulses_per_mm invalido para converter pulsos em mm.")

            kwargs = {}
            if "X" in targets_pulses:
                kwargs["x"] = targets_pulses["X"] / pulses_per_mm
            if "Y" in targets_pulses:
                kwargs["y"] = targets_pulses["Y"] / pulses_per_mm
            if "Z" in targets_pulses:
                kwargs["z"] = targets_pulses["Z"] / pulses_per_mm
            self.cnc.move_to_absolute_position(**kwargs)

        if not self.cnc.wait_for_idle(timeout=MOVE_TIMEOUT_SEC):
            raise RuntimeError(f"Timeout aguardando movimento para {targets_pulses}.")


class TensiometerCalibrationDialog(QDialog):
    """Tela dedicada para calibracao automatica e manual do medidor."""

    def __init__(self, controller, config=None, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.cnc = controller.cnc if hasattr(controller, "cnc") else controller
        self.config = config or AOIConfigManager()
        self._worker = None

        self.setWindowTitle("Calibrar medidor de tensao")
        self._apply_screen_aware_geometry()
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setModal(False)

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACE.MD, SPACE.MD, SPACE.MD, SPACE.MD)
        layout.setSpacing(SPACE.MD)

        title = QLabel("Calibracao do Medidor de Tensao")
        title.setStyleSheet("font-size: 18px; font-weight: 700;")
        layout.addWidget(title)

        auto_group = QGroupBox("Calibracao automatica")
        auto_layout = QVBoxLayout(auto_group)
        auto_layout.addWidget(
            QLabel(
                "Fluxo fixo: Home > ligar medidor > zerar medidor > "
                "X/Y = 33871/34130 > Z = 9207 > aguardar 2 s > "
                "Calibrar > Home final."
            )
        )

        self.auto_start_btn = StandardButton("Iniciar calibracao automatica", variant="primary")
        self.auto_start_btn.clicked.connect(self._start_automatic_calibration)
        auto_layout.addWidget(self.auto_start_btn)

        self.status_label = QLabel("Aguardando comando.")
        auto_layout.addWidget(self.status_label)

        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumBlockCount(200)
        self.log_output.setMinimumHeight(160)
        auto_layout.addWidget(self.log_output)
        layout.addWidget(auto_group)

        manual_group = QGroupBox("Calibracao manual")
        manual_layout = QVBoxLayout(manual_group)
        manual_layout.addWidget(
            QLabel(
                "Use o JOG para posicionamento manual e os botoes abaixo para controlar o medidor."
            )
        )

        manual_buttons = QHBoxLayout()
        self.turn_on_btn = StandardButton("Ligar", variant="secondary")
        self.turn_on_btn.clicked.connect(
            lambda: self._run_manual_command(
                TENSIOMETER_POWER_COIL,
                "Ligar",
                TENSIOMETER_POWER_ON_PULSE_MS,
            )
        )
        manual_buttons.addWidget(self.turn_on_btn)

        self.turn_off_btn = StandardButton("Desligar", variant="secondary")
        self.turn_off_btn.clicked.connect(
            lambda: self._run_manual_command(
                TENSIOMETER_POWER_COIL,
                "Desligar",
                TENSIOMETER_POWER_OFF_PULSE_MS,
            )
        )
        manual_buttons.addWidget(self.turn_off_btn)

        self.calibrate_btn = StandardButton("Calibrar", variant="secondary")
        self.calibrate_btn.clicked.connect(
            lambda: self._run_manual_command(TENSIOMETER_CALIBRATE_COIL, "Calibrar", 100)
        )
        manual_buttons.addWidget(self.calibrate_btn)

        self.zero_btn = StandardButton("Zerar", variant="secondary")
        self.zero_btn.clicked.connect(
            lambda: self._run_manual_command(TENSIOMETER_ZERO_COIL, "Zerar", 100)
        )
        manual_buttons.addWidget(self.zero_btn)

        manual_layout.addLayout(manual_buttons)

        self.movement_widget = MovementControlWidget(
            self.controller,
            self.config,
            parent=self,
        )
        movement_scroll = QScrollArea(self)
        movement_scroll.setWidgetResizable(True)
        movement_scroll.setWidget(self.movement_widget)
        manual_layout.addWidget(movement_scroll)

        layout.addWidget(manual_group, 1)

    def _apply_screen_aware_geometry(self) -> None:
        screen = QGuiApplication.primaryScreen()
        available = screen.availableGeometry() if screen else QRect(0, 0, 1280, 720)
        target_width = min(820, max(640, available.width() - 100))
        target_height = min(900, max(680, available.height() - 100))
        self.setMinimumSize(min(target_width, 640), min(target_height, 680))
        self.resize(target_width, target_height)

    def _start_automatic_calibration(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            QMessageBox.warning(self, "Calibracao", "Ja existe uma calibracao automatica em andamento.")
            return

        self._append_log("Iniciando calibracao automatica.")
        self.status_label.setText("Iniciando calibracao automatica.")
        self.auto_start_btn.setEnabled(False)

        self._worker = TensiometerAutoCalibrationWorker(self.cnc)
        self._worker.status_changed.connect(self._on_worker_status)
        self._worker.calibration_finished.connect(self._on_worker_finished)
        self._worker.calibration_failed.connect(self._on_worker_failed)
        self._worker.start()

    def _on_worker_status(self, message: str) -> None:
        self.status_label.setText(message)
        self._append_log(message)

    def _on_worker_finished(self) -> None:
        self.auto_start_btn.setEnabled(True)
        self.status_label.setText("Calibracao automatica concluida. Equipamento em home.")
        self._append_log("Calibracao automatica concluida com sucesso. Equipamento em home.")
        QMessageBox.information(
            self,
            "Calibracao",
            "Calibracao automatica do medidor concluida. Equipamento em home.",
        )

    def _on_worker_failed(self, error_message: str) -> None:
        self.auto_start_btn.setEnabled(True)
        self.status_label.setText("Falha na calibracao automatica.")
        self._append_log(f"Falha: {error_message}")
        QMessageBox.critical(
            self,
            "Calibracao",
            f"Falha durante a calibracao automatica:\n{error_message}",
        )

    def _run_manual_command(self, coil: int, action_name: str, duration_ms: int) -> None:
        try:
            self._ensure_manual_command_ready()
            if hasattr(self.cnc, "pulse_coil"):
                self.cnc.pulse_coil(coil, duration_ms)
            else:
                self.cnc._pulse_coil(coil, duration_ms)

            message = f"Comando manual enviado: {action_name}."
            self.status_label.setText(message)
            self._append_log(message)
        except Exception as exc:
            logger.exception("Falha no comando manual do medidor: %s", action_name)
            QMessageBox.critical(
                self,
                "Calibracao manual",
                f"Falha ao executar '{action_name}':\n{exc}",
            )

    def _ensure_manual_command_ready(self) -> None:
        if self.cnc is None:
            raise RuntimeError("Controlador CNC nao disponivel.")
        if not getattr(self.cnc, "is_connected", False):
            raise RuntimeError("Conecte o CLP antes de acionar o medidor.")
        if not hasattr(self.cnc, "pulse_coil") and not hasattr(self.cnc, "_pulse_coil"):
            raise RuntimeError("O backend atual nao suporta pulso de coil.")

    def _append_log(self, message: str) -> None:
        timestamp = time.strftime("%H:%M:%S")
        self.log_output.appendPlainText(f"[{timestamp}] {message}")

    def closeEvent(self, event) -> None:
        if self._worker is not None and self._worker.isRunning():
            QMessageBox.warning(
                self,
                "Calibracao em andamento",
                "Aguarde a calibracao automatica terminar antes de fechar esta tela.",
            )
            if event:
                event.ignore()
            return

        super().closeEvent(event)
