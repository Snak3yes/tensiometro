"""
SequenceController - Controller para Gerenciamento de Sequências

Este controller gerencia a criação, execução e persistência de sequências
de inspeção, incluindo importação/exportação de G-CODE.

Responsabilidade:
- Criar sequências a partir de posições registradas
- Carregar/salvar sequências em G-CODE
- Executar sequências de inspeção
- Gerenciar estados de execução

Signals Emitidos:
- sequence_created(sequence) - Sequência criada
- sequence_loaded(sequence, source) - Sequência carregada
- sequence_saved(filepath) - Sequência salva
- sequence_execution_started(sequence_name) - Execução iniciada
- sequence_execution_stopped() - Execução parada
- sequence_execution_finished() - Execução finalizada
- sequence_error(error_message) - Erro na execução
- position_captured(position, image, timestamp) - Posição capturada
"""

import logging
from typing import Optional, List

from PyQt6.QtWidgets import (
    QFileDialog, QMessageBox
)
from PyQt6.QtCore import QObject, pyqtSignal

from aoi_lib import InspectionPosition

logger = logging.getLogger("consumo_lib")


class SequenceController(QObject):
    """
    Controller para gerenciamento de sequências.

    Responsável por criar, carregar, salvar e executar sequências
    de inspeção com suporte a G-CODE.
    """

    # Signals
    sequence_created = pyqtSignal(object)  # sequence
    sequence_loaded = pyqtSignal(object, str)  # sequence, source
    sequence_saved = pyqtSignal(str)  # filepath
    sequence_execution_started = pyqtSignal(str)  # sequence_name
    sequence_execution_stopped = pyqtSignal()
    sequence_execution_finished = pyqtSignal()
    sequence_error = pyqtSignal(str)  # error_message
    position_captured = pyqtSignal(object, object, float)  # position, image, timestamp

    def __init__(self, controller, parent=None):
        """
        Inicializa o SequenceController.

        Args:
            controller: Instância de CNCAOIController
            parent: Widget pai (geralmente main_window)
        """
        super().__init__(parent)
        self.controller = controller
        self.parent_window = parent

        # Estado de execução
        self._is_running = False
        self._current_sequence = None
        self._run_thread = None

        logger.debug("SequenceController inicializado")

    # =========================================================================
    # MÉTODOS PÚBLICOS
    # =========================================================================

    def create_sequence_from_registry(
        self,
        position_registry,
        sequence_name: str,
        position_list_widget=None,
        sequence_widget=None
    ):
        """
        Cria uma sequência a partir de posições registradas.

        Args:
            position_registry: PositionRegistryWidget com posições
            sequence_name: Nome da sequência
            position_list_widget: Widget de lista de posições (opcional)
            sequence_widget: Widget de controle de sequência (opcional)

        Returns:
            A sequência criada ou None em caso de erro
        """
        if not position_registry.positions:
            self.sequence_error.emit("Nenhuma posição registrada")
            if self.parent_window:
                QMessageBox.warning(
                    self.parent_window,
                    "Aviso",
                    "Nenhuma posição registrada"
                )
            return None

        if not sequence_name:
            self.sequence_error.emit("Nome da sequência não fornecido")
            if self.parent_window:
                QMessageBox.warning(
                    self.parent_window,
                    "Aviso",
                    "Por favor, insira um nome para a sequência"
                )
            return None

        try:
            # Limpa posições existentes no widget
            if position_list_widget:
                position_list_widget.clear_positions()

            # Cria posições para a sequência
            positions = []
            for pos in position_registry.positions:
                # Cria objeto de posição com parâmetros de câmera
                camera_params = {"has_image": pos['image'] is not None}

                inspection_pos = InspectionPosition(
                    pos['name'],
                    pos['x'],
                    pos['y'],
                    pos.get('z', 0.0),
                    camera_params
                )
                positions.append(inspection_pos)

                # Adiciona ao widget de lista
                if position_list_widget:
                    position_list_widget.add_position(inspection_pos)

            # Cria a sequência via controller
            sequence = self.controller.create_sequence(sequence_name, positions)
            self._current_sequence = sequence

            # Atualiza UI
            if sequence_widget:
                sequence_widget.sequence_status.setText(
                    f"Criada: {len(positions)} posições"
                )

            # Emite signal
            self.sequence_created.emit(sequence)

            logger.info(
                f"Sequência '{sequence_name}' criada com {len(positions)} posições"
            )

            return sequence

        except Exception as e:
            logger.exception("Erro ao criar sequência")
            error_msg = f"Erro ao criar sequência: {str(e)}"
            self.sequence_error.emit(error_msg)
            if self.parent_window:
                QMessageBox.critical(self.parent_window, "Erro", error_msg)
            return None

    def load_gcode(
        self,
        position_list_widget=None,
        sequence_widget=None
    ):
        """
        Carrega uma sequência a partir de um arquivo G-CODE.

        Args:
            position_list_widget: Widget de lista de posições (opcional)
            sequence_widget: Widget de controle de sequência (opcional)

        Returns:
            A sequência carregada ou None em caso de erro
        """
        from aoi_lib.gcode_manager import GCodeManager

        gcode_manager = GCodeManager()

        filename, _ = QFileDialog.getOpenFileName(
            self.parent_window if self.parent_window else None,
            "Abrir G-CODE",
            "",
            "Arquivos G-CODE (*.gcode *.nc *.ngc)"
        )

        if not filename:
            return None

        try:
            # Carrega o G-CODE
            result = gcode_manager.read_gcode_file(filename)

            if not result:
                raise ValueError("Falha ao ler arquivo G-CODE")

            # Limpa posições atuais
            if position_list_widget:
                position_list_widget.clear_positions()

            # Cria sequência a partir dos dados do G-CODE
            positions = []
            for pos_data in result['positions']:
                # Cria objeto de posição
                position = InspectionPosition(
                    pos_data['name'],
                    pos_data['x'],
                    pos_data['y'],
                    pos_data.get('z', 0.0),
                    pos_data.get('camera_params', {})
                )

                # Adiciona à lista visual
                if position_list_widget:
                    position_list_widget.add_position(position)

                # Adiciona à lista interna
                positions.append(position)

            # Cria a sequência
            sequence = self.controller.create_sequence(
                result['sequence_name'],
                positions
            )
            self._current_sequence = sequence

            # Atualiza interface
            if sequence_widget:
                sequence_widget.sequence_name.setText(result['sequence_name'])
                sequence_widget.sequence_status.setText(
                    f"Carregada do G-CODE: {len(positions)} posições"
                )

            # Emite signal
            self.sequence_loaded.emit(sequence, filename)

            logger.info(f"G-CODE carregado de {filename}: {len(positions)} posições")

            return sequence

        except Exception as e:
            logger.exception("Erro ao carregar G-CODE")
            error_msg = f"Erro ao carregar G-CODE:\n{str(e)}"
            self.sequence_error.emit(error_msg)
            if self.parent_window:
                QMessageBox.critical(
                    self.parent_window,
                    "Erro",
                    error_msg
                )
            return None

    def save_gcode(self, sequence):
        """
        Salva a sequência atual como um arquivo G-CODE.

        Args:
            sequence: Sequência a ser salva

        Returns:
            Caminho do arquivo salvo ou None em caso de erro
        """
        from aoi_lib.gcode_manager import GCodeManager

        if not sequence:
            self.sequence_error.emit("Nenhuma sequência para salvar")
            if self.parent_window:
                QMessageBox.warning(
                    self.parent_window,
                    "Aviso",
                    "Crie uma sequência primeiro"
                )
            return None

        gcode_manager = GCodeManager()

        filename, _ = QFileDialog.getSaveFileName(
            self.parent_window if self.parent_window else None,
            "Salvar G-CODE",
            "",
            "Arquivos G-CODE (*.gcode *.nc *.ngc)"
        )

        if not filename:
            return None

        try:
            # Adiciona extensão se necessário
            if not filename.endswith('.gcode') and not filename.endswith('.nc') and not filename.endswith('.ngc'):
                filename += '.gcode'

            # Salva usando o GCodeManager
            if gcode_manager.save_gcode_to_file(sequence, filename):
                self.sequence_saved.emit(filename)
                logger.info(f"G-CODE salvo em {filename}")
                return filename
            else:
                raise ValueError("Falha ao salvar arquivo G-CODE")

        except Exception as e:
            logger.exception("Erro ao salvar G-CODE")
            error_msg = f"Erro ao salvar G-CODE:\n{str(e)}"
            self.sequence_error.emit(error_msg)
            if self.parent_window:
                QMessageBox.critical(
                    self.parent_window,
                    "Erro",
                    error_msg
                )
            return None

    def run_sequence(
        self,
        sequence,
        results_table=None,
        sequence_widget=None,
        movement_widget=None,
        camera_preview=None
    ):
        """
        Executa a sequência de inspeção.

        Args:
            sequence: Sequência a ser executada
            results_table: Tabela de resultados (opcional)
            sequence_widget: Widget de controle de sequência (opcional)
            movement_widget: Widget de movimento (opcional)
            camera_preview: Widget de preview de câmera (opcional)

        Returns:
            True se iniciou com sucesso, False caso contrário
        """
        if not sequence:
            self.sequence_error.emit("Nenhuma sequência para executar")
            if self.parent_window:
                QMessageBox.warning(
                    self.parent_window,
                    "Aviso",
                    "Crie uma sequência primeiro"
                )
            return False

        if not self.controller.cnc.is_connected:
            self.sequence_error.emit("CNC não conectado")
            if self.parent_window:
                QMessageBox.warning(
                    self.parent_window,
                    "Aviso",
                    "CNC não conectado"
                )
            return False

        if not hasattr(self.controller.camera, 'is_connected') or not self.controller.camera.is_connected:
            self.sequence_error.emit("Câmera não conectada")
            if self.parent_window:
                QMessageBox.warning(
                    self.parent_window,
                    "Aviso",
                    "Câmera não conectada"
                )
            return False

        try:
            # Limpa resultados anteriores
            if results_table:
                results_table.setRowCount(0)

            # Configura UI para execução
            self._is_running = True

            if sequence_widget:
                sequence_widget.run_sequence_btn.setEnabled(False)
                sequence_widget.stop_sequence_btn.setEnabled(True)
                sequence_widget.sequence_status.setText("Executando...")

            # Configura velocidade no controlador
            if movement_widget:
                self.controller.set_feed_rate(movement_widget.get_current_feed_rate())

            # Inicia execução em thread
            from consumo_lib.threads.sequence_runner import SequenceRunnerThread
            import time

            self._run_thread = SequenceRunnerThread(
                self.controller,
                sequence.name
            )

            # Conecta signals
            self._run_thread.image_captured.connect(self._on_image_captured)
            self._run_thread.sequence_completed.connect(self._on_sequence_completed)
            self._run_thread.sequence_error.connect(self._on_sequence_error)

            # Armazena referências para handlers
            self._results_table = results_table
            self._sequence_widget = sequence_widget
            self._camera_preview = camera_preview

            self._run_thread.start()

            # Emite signal
            self.sequence_execution_started.emit(sequence.name)

            logger.info(f"Execução da sequência '{sequence.name}' iniciada")

            return True

        except Exception as e:
            logger.exception("Erro ao iniciar sequência")
            error_msg = f"Erro ao executar sequência:\n{str(e)}"
            self.sequence_error.emit(error_msg)

            # Reseta estado
            self._is_running = False
            if sequence_widget:
                sequence_widget.run_sequence_btn.setEnabled(True)
                sequence_widget.stop_sequence_btn.setEnabled(False)
                sequence_widget.sequence_status.setText("Erro")

            if self.parent_window:
                QMessageBox.critical(self.parent_window, "Erro", error_msg)

            return False

    def stop_sequence(self):
        """
        Para a execução da sequência atual.

        Returns:
            True se parou com sucesso, False caso contrário
        """
        if not self._is_running:
            return False

        try:
            self.controller.stop_sequence()
            self._is_running = False

            # Reseta UI
            if hasattr(self, '_sequence_widget') and self._sequence_widget:
                self._sequence_widget.run_sequence_btn.setEnabled(True)
                self._sequence_widget.stop_sequence_btn.setEnabled(False)
                self._sequence_widget.sequence_status.setText("Parada")

            # Emite signal
            self.sequence_execution_stopped.emit()

            logger.info("Execução de sequência interrompida")

            return True

        except Exception as e:
            logger.exception("Erro ao parar sequência")
            error_msg = f"Erro ao parar sequência:\n{str(e)}"
            self.sequence_error.emit(error_msg)
            return False

    # =========================================================================
    # MÉTODOS PRIVADOS - HANDLERS
    # =========================================================================

    def _on_image_captured(self, result):
        """
        Handler chamado quando uma imagem é capturada durante a execução.

        Args:
            result: Dicionário com 'position', 'image', 'timestamp'
        """
        position = result["position"]
        image = result["image"]
        timestamp = result["timestamp"]

        # Exibe a imagem no preview
        if hasattr(self, '_camera_preview') and self._camera_preview:
            self._camera_preview.display_image(image)

        # Adiciona à tabela de resultados
        if hasattr(self, '_results_table') and self._results_table:
            import time
            row = self._results_table.rowCount()
            from PyQt6.QtWidgets import QTableWidgetItem
            self._results_table.insertRow(row)
            self._results_table.setItem(row, 0, QTableWidgetItem(position.name))
            self._results_table.setItem(
                row, 1,
                QTableWidgetItem(time.strftime("%H:%M:%S", time.localtime(timestamp)))
            )
            self._results_table.setItem(row, 2, QTableWidgetItem("Capturado"))

        # Emite signal
        self.position_captured.emit(position, image, timestamp)

        logger.debug(f"Posição capturada: {position.name}")

    def _on_sequence_completed(self):
        """Handler chamado quando a execução da sequência é concluída."""
        self._is_running = False
        self._run_thread = None

        # Reseta UI
        if hasattr(self, '_sequence_widget') and self._sequence_widget:
            self._sequence_widget.run_sequence_btn.setEnabled(True)
            self._sequence_widget.stop_sequence_btn.setEnabled(False)
            self._sequence_widget.sequence_status.setText("Concluída")

        # Emite signal
        self.sequence_execution_finished.emit()

        logger.info("Execução de sequência concluída")

    def _on_sequence_error(self, error_message):
        """
        Handler chamado quando ocorre um erro durante a execução.

        Args:
            error_message: Mensagem de erro
        """
        # Emite signal
        self.sequence_error.emit(error_message)

        # Reseta estado
        self._on_sequence_completed()

        # Exibe mensagem
        if self.parent_window:
            QMessageBox.critical(
                self.parent_window,
                "Erro na Sequência",
                error_message
            )

        logger.error(f"Erro na execução da sequência: {error_message}")

    # =========================================================================
    # PROPRIEDADES
    # =========================================================================

    @property
    def is_running(self) -> bool:
        """Retorna True se uma sequência está em execução."""
        return self._is_running

    @property
    def current_sequence(self):
        """Retorna a sequência atual."""
        return self._current_sequence

    @current_sequence.setter
    def current_sequence(self, value):
        """Define a sequência atual."""
        self._current_sequence = value
