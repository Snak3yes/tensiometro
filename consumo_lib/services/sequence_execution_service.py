"""
services/sequence_execution_service.py
---------------------------------------
Serviço de execução de sequências de inspeção.

Encapsula toda lógica de execução de sequências, validação e callbacks.
"""
import logging
import time
from typing import Optional, Callable
from PyQt6.QtWidgets import QMessageBox, QTableWidget, QTableWidgetItem
from PyQt6.QtCore import QObject, pyqtSignal
from aoi_lib import InspectionPosition

logger = logging.getLogger(__name__)


class SequenceExecutionService(QObject):
    """
    Serviço para executar sequências de inspeção.

    Responsabilidades:
        - Validar pré-condições (sequência existe, CNC conectado, câmera conectada)
        - Executar sequência via SequenceRunnerThread
        - Gerenciar callbacks (imagem capturada, conclusão, erro)
        - Atualizar UI durante execução
        - Parar execução
        - Criar sequências a partir de registro de posições
    """

    # Signals para notificar UI sobre eventos de sequência
    image_captured = pyqtSignal(dict)  # result: {position, image, timestamp}
    sequence_completed = pyqtSignal()
    sequence_error = pyqtSignal(str)

    def __init__(self, controller, main_window):
        """
        Inicializa o serviço de execução de sequências.

        Args:
            controller: CNCAOIController com lógica de execução
            main_window: Referência à MainWindow para acessar UI widgets
        """
        super().__init__()
        self.controller = controller
        self.window = main_window
        self._is_running = False
        self._run_thread: Optional['SequenceRunnerThread'] = None

    def create_sequence_from_registry(
        self,
        position_registry,
        sequence_widget,
        position_list_widget
    ):
        """
        Cria uma sequência a partir de posições registradas.

        Args:
            position_registry: PositionRegistryWidget com posições
            sequence_widget: SequenceControlWidget para atualizar status
            position_list_widget: PositionListWidget para exibir posições

        Returns:
            InspectionSequence ou None se falhou
        """
        if not position_registry.positions:
            QMessageBox.warning(self.window, "Aviso", "Nenhuma posição registrada")
            return None

        # Get sequence name
        sequence_name = sequence_widget.sequence_name.text()
        if not sequence_name:
            QMessageBox.warning(self.window, "Aviso", "Digite um nome para a sequência")
            return None

        # Clear existing positions
        position_list_widget.clear_positions()

        # Create positions for the sequence
        positions = []
        for pos in position_registry.positions:
            # Create position object with camera parameters
            camera_params = {"has_image": pos['image'] is not None}

            inspection_pos = InspectionPosition(
                pos['name'],
                pos['x'],
                pos['y'],
                pos.get('z', 0.0),
                camera_params
            )
            positions.append(inspection_pos)

            # Also add to the position list widget
            position_list_widget.add_position(inspection_pos)

        # Create the sequence
        sequence = self.controller.create_sequence(sequence_name, positions)

        # Update UI
        sequence_widget.sequence_status.setText(f"Criada: {len(positions)} posições")
        self.window.statusBar().showMessage(
            f"Sequência '{sequence_name}' criada com {len(positions)} posições"
        )

        # Ask if user wants to save as G-CODE
        reply = QMessageBox.question(
            self.window,
            "Salvar G-CODE",
            "Deseja salvar esta sequência como G-CODE?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Delegate to main_window's save_gcode method
            self.window.save_gcode()

        return sequence

    def run_sequence(
        self,
        current_sequence,
        movement_widget,
        sequence_widget,
        results_table: QTableWidget
    ) -> bool:
        """
        Executa a sequência atual.

        Args:
            current_sequence: InspectionSequence para executar
            movement_widget: MovementControlWidget para obter feed rate
            sequence_widget: SequenceControlWidget para atualizar botões
            results_table: QTableWidget para exibir resultados

        Returns:
            bool: True se iniciou com sucesso, False caso contrário
        """
        # Validations
        if not current_sequence:
            QMessageBox.warning(self.window, "Aviso", "Crie uma sequência primeiro")
            return False

        if not self.controller.cnc.is_connected:
            QMessageBox.warning(self.window, "Aviso", "CNC não conectado")
            return False

        if not hasattr(self.controller.camera, 'is_connected') or not self.controller.camera.is_connected:
            QMessageBox.warning(self.window, "Aviso", "Câmera não conectada")
            return False

        # Clear previous results
        results_table.setRowCount(0)

        # Configure UI for execution
        self._is_running = True
        sequence_widget.run_sequence_btn.setEnabled(False)
        sequence_widget.stop_sequence_btn.setEnabled(True)
        sequence_widget.sequence_status.setText("Executando...")

        # Start execution
        try:
            self.window.statusBar().showMessage(
                f"Executando sequência '{current_sequence.name}'..."
            )
            # Configura velocidade no controlador baseada na interface
            self.controller.set_feed_rate(movement_widget.get_current_feed_rate())

            # Import here to avoid circular dependency
            from consumo_lib.threads.sequence_runner import SequenceRunnerThread

            # Use a thread to run the sequence
            self._run_thread = SequenceRunnerThread(self.controller, current_sequence.name)

            # Connect signals
            self._run_thread.image_captured.connect(self._on_image_captured)
            self._run_thread.sequence_completed.connect(self._on_completed)
            self._run_thread.sequence_error.connect(self._on_error)

            # Forward signals to UI
            self._run_thread.image_captured.connect(self.image_captured)
            self._run_thread.sequence_completed.connect(self.sequence_completed)
            self._run_thread.sequence_error.connect(self.sequence_error)

            self._run_thread.start()

            return True

        except Exception as e:
            error_msg = f"Erro ao executar sequência: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.window.statusBar().showMessage(error_msg)
            sequence_widget.sequence_status.setText("Erro")
            self._on_completed()
            return False

    def stop_sequence(self, sequence_widget):
        """
        Para a execução da sequência atual.

        Args:
            sequence_widget: SequenceControlWidget para atualizar botões
        """
        if self._is_running:
            self.controller.stop_sequence()
            self.window.statusBar().showMessage("Execução de sequência interrompida")
            self._on_completed()

    def _on_image_captured(self, result: dict):
        """
        Callback interno quando uma imagem é capturada.

        Args:
            result: Dict com {position, image, timestamp}
        """
        position = result["position"]
        timestamp = result["timestamp"]

        # Update status bar
        self.window.statusBar().showMessage(
            f"Posição capturada: {position.name} ({position.x:.3f}, {position.y:.3f})"
        )

    def _on_completed(self):
        """
        Callback interno quando a execução é concluída.

        Atualiza UI para estado de repouso.
        """
        self._is_running = False
        self.sequence_widget.run_sequence_btn.setEnabled(True)
        self.sequence_widget.stop_sequence_btn.setEnabled(False)
        self.sequence_widget.sequence_status.setText("Concluída")
        self.window.statusBar().showMessage("Execução de sequência concluída")
        self._run_thread = None

    def _on_error(self, error_message: str):
        """
        Callback interno quando ocorre um erro.

        Args:
            error_message: Mensagem de erro
        """
        QMessageBox.critical(self.window, "Erro na Sequência", error_message)
        self._on_completed()

    @property
    def is_running(self) -> bool:
        """Retorna True se uma sequência está em execução."""
        return self._is_running

    @property
    def sequence_widget(self):
        """Conveniência para acessar sequence_widget da janela."""
        return self.window.sequence_widget
