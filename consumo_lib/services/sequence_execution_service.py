"""
services/sequence_execution_service.py
---------------------------------------
Servico de execucao de sequencias de inspecao.

Encapsula toda logica de execucao de sequencias, validacao e callbacks.
"""
import logging
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QMessageBox, QTableWidget

from aoi_lib import InspectionPosition
from consumo_lib.utils.error_handler import show_motion_interlock_dialog

logger = logging.getLogger(__name__)


class SequenceExecutionService(QObject):
    """
    Servico para executar sequencias de inspecao.

    Responsabilidades:
        - Validar pre-condicoes (sequencia existe, CNC conectada, camera conectada)
        - Executar sequencia via SequenceRunnerThread
        - Gerenciar callbacks (imagem capturada, conclusao, erro)
        - Atualizar UI durante execucao
        - Parar execucao
        - Criar sequencias a partir de registro de posicoes
    """

    image_captured = pyqtSignal(dict)
    sequence_completed = pyqtSignal()
    sequence_error = pyqtSignal(str)

    def __init__(self, controller, main_window):
        super().__init__()
        self.controller = controller
        self.window = main_window
        self._is_running = False
        self._run_thread: Optional["SequenceRunnerThread"] = None

    def create_sequence_from_registry(
        self,
        position_registry,
        sequence_widget,
        position_list_widget,
    ):
        if not position_registry.positions:
            QMessageBox.warning(self.window, "Aviso", "Nenhuma posicao registrada")
            return None

        sequence_name = sequence_widget.sequence_name.text()
        if not sequence_name:
            QMessageBox.warning(self.window, "Aviso", "Digite um nome para a sequencia")
            return None

        position_list_widget.clear_positions()

        positions = []
        for pos in position_registry.positions:
            camera_params = {"has_image": pos["image"] is not None}
            inspection_pos = InspectionPosition(
                pos["name"],
                pos["x"],
                pos["y"],
                pos.get("z", 0.0),
                camera_params,
            )
            positions.append(inspection_pos)
            position_list_widget.add_position(inspection_pos)

        sequence = self.controller.create_sequence(sequence_name, positions)

        sequence_widget.sequence_status.setText(f"Criada: {len(positions)} posicoes")
        self.window.statusBar().showMessage(
            f"Sequencia '{sequence_name}' criada com {len(positions)} posicoes"
        )

        reply = QMessageBox.question(
            self.window,
            "Salvar G-CODE",
            "Deseja salvar esta sequencia como G-CODE?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.window.save_gcode()

        return sequence

    def run_sequence(
        self,
        current_sequence,
        movement_widget,
        sequence_widget,
        results_table: QTableWidget,
    ) -> bool:
        if not current_sequence:
            QMessageBox.warning(self.window, "Aviso", "Crie uma sequencia primeiro")
            return False

        if not self.controller.cnc.is_connected:
            QMessageBox.warning(self.window, "Aviso", "CNC nao conectada")
            return False

        if not hasattr(self.controller.camera, "is_connected") or not self.controller.camera.is_connected:
            QMessageBox.warning(self.window, "Aviso", "Camera nao conectada")
            return False

        results_table.setRowCount(0)

        self._is_running = True
        sequence_widget.run_sequence_btn.setEnabled(False)
        sequence_widget.stop_sequence_btn.setEnabled(True)
        sequence_widget.sequence_status.setText("Executando...")

        try:
            self.window.statusBar().showMessage(
                f"Executando sequencia '{current_sequence.name}'..."
            )
            self.controller.set_feed_rate(movement_widget.get_current_feed_rate())

            from consumo_lib.threads.sequence_runner import SequenceRunnerThread

            self._run_thread = SequenceRunnerThread(self.controller, current_sequence.name)
            self._run_thread.image_captured.connect(self._on_image_captured)
            self._run_thread.sequence_completed.connect(self._on_completed)
            self._run_thread.sequence_error.connect(self._on_error)

            self._run_thread.image_captured.connect(self.image_captured)
            self._run_thread.sequence_completed.connect(self.sequence_completed)
            self._run_thread.sequence_error.connect(self.sequence_error)
            self._run_thread.start()
            return True

        except Exception as e:
            error_msg = f"Erro ao executar sequencia: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.window.statusBar().showMessage(error_msg)
            sequence_widget.sequence_status.setText("Erro")
            self._on_completed()
            return False

    def stop_sequence(self, sequence_widget):
        if self._is_running:
            self.controller.stop_sequence()
            self.window.statusBar().showMessage("Execucao de sequencia interrompida")
            self._on_completed()

    def _on_image_captured(self, result: dict):
        position = result["position"]
        self.window.statusBar().showMessage(
            f"Posicao capturada: {position.name} ({position.x:.3f}, {position.y:.3f})"
        )

    def _on_completed(self):
        self._is_running = False
        self.sequence_widget.run_sequence_btn.setEnabled(True)
        self.sequence_widget.stop_sequence_btn.setEnabled(False)
        self.sequence_widget.sequence_status.setText("Concluida")
        self.window.statusBar().showMessage("Execucao de sequencia concluida")
        self._run_thread = None

    def _on_error(self, error_message: str):
        if not show_motion_interlock_dialog(self.window, error_message, operation="sequencia automatica"):
            QMessageBox.critical(self.window, "Erro na Sequencia", error_message)
        self._on_completed()

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def sequence_widget(self):
        return self.window.sequence_widget
