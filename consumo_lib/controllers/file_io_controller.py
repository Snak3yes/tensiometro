"""
FileIOController - Controller para Operações de Arquivo I/O

Este controller gerencia operações de entrada/saída de arquivos:
- Carregar/salvar arquivos G-CODE
- Carregar/salvar programas de mapa
- Gerenciar diálogos de arquivo
- Atualizar UI após operações

Responsabilidade:
- Gerenciar toda lógica de I/O de arquivos
- Validar pré-condições (ex: sequência existe)
- Emitir signals quando operações completam

Signals Emitidos:
- file_loaded(filename, content) - Arquivo carregado
- file_saved(filename) - Arquivo salvo
- file_operation_failed(error) - Erro na operação
"""

import logging
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QFileDialog, QMessageBox

from aoi_lib.gcode_manager import GCodeManager
from aoi_lib.position_manager import InspectionPosition

logger = logging.getLogger("consumo_lib")


class FileIOController(QObject):
    """
    Controller para operações de arquivo I/O.

    Responsável por gerenciar carregamento e salvamento de
    arquivos G-CODE e programas de mapa.
    """

    # Signals
    file_loaded = pyqtSignal(str, object)  # filename, content
    file_saved = pyqtSignal(str)  # filename
    file_operation_failed = pyqtSignal(str)  # error_message
    gcode_loaded = pyqtSignal(str, object)  # filename, sequence
    gcode_saved = pyqtSignal(str)  # filename
    program_loaded = pyqtSignal(str)  # filename
    program_saved = pyqtSignal(str)  # filename

    def __init__(self, controller, position_list_widget, sequence_widget, parent=None):
        """
        Inicializa o FileIOController.

        Args:
            controller: Instância de CNCAOIController
            position_list_widget: Widget de lista de posições
            sequence_widget: Widget de sequência
            parent: Widget pai (geralmente main_window)
        """
        super().__init__(parent)
        self.controller = controller
        self.position_list_widget = position_list_widget
        self.sequence_widget = sequence_widget
        self.parent_window = parent

        logger.debug("FileIOController inicializado")

    def load_gcode(self):
        """
        Carrega uma sequência a partir de um arquivo G-CODE.

        Emits:
            gcode_loaded se arquivo carregado
            file_operation_failed se erro
        """
        gcode_manager = GCodeManager()

        filename, _ = QFileDialog.getOpenFileName(
            self.parent_window,
            "Abrir G-CODE",
            "",
            "Arquivos G-CODE (*.gcode *.nc *.ngc)"
        )

        if filename:
            try:
                # Carrega o G-CODE
                result = gcode_manager.read_gcode_file(filename)

                if result:
                    # Limpa posições atuais
                    self.position_list_widget.clear_positions()

                    # Cria sequência a partir dos dados do G-CODE
                    positions = []
                    for pos_data in result['positions']:
                        # Cria objeto de posição
                        position = InspectionPosition(
                            pos_data['name'],
                            pos_data['x'],
                            pos_data['y'],
                            pos_data['camera_params']
                        )

                        # Adiciona à lista visual
                        self.position_list_widget.add_position(position)

                        # Adiciona à lista interna
                        positions.append(position)

                    # Cria a sequência
                    sequence = self.controller.create_sequence(
                        result['sequence_name'],
                        positions
                    )

                    # Atualiza interface
                    self.sequence_widget.sequence_name.setText(result['sequence_name'])
                    self.sequence_widget.sequence_status.setText(
                        f"Carregada do G-CODE: {len(positions)} posições"
                    )

                    self.parent_window.statusBar().showMessage(
                        f"G-CODE carregado de {filename}"
                    )
                    logger.info(f"G-CODE carregado: {filename}")

                    # Emit signal
                    self.gcode_loaded.emit(filename, sequence)
                else:
                    error_msg = "Falha ao carregar o arquivo G-CODE"
                    QMessageBox.critical(self.parent_window, "Erro", error_msg)
                    self.file_operation_failed.emit(error_msg)

            except Exception as e:
                error_msg = f"Erro ao carregar G-CODE: {e}"
                logger.exception("Erro ao carregar arquivo G-CODE")
                QMessageBox.critical(self.parent_window, "Erro", error_msg)
                self.file_operation_failed.emit(error_msg)

    def save_gcode(self, current_sequence):
        """
        Salva a sequência atual como um arquivo G-CODE.

        Args:
            current_sequence: Sequência atual (ou None)

        Emits:
            gcode_saved se arquivo salvo
            file_operation_failed se erro ou sem sequência
        """
        if not current_sequence:
            QMessageBox.warning(
                self.parent_window,
                "Aviso",
                "Crie uma sequência primeiro"
            )
            self.file_operation_failed.emit("Nenhuma sequência para salvar")
            return

        gcode_manager = GCodeManager()

        filename, _ = QFileDialog.getSaveFileName(
            self.parent_window,
            "Salvar G-CODE",
            "",
            "Arquivos G-CODE (*.gcode *.nc *.ngc)"
        )

        if filename:
            try:
                # Adiciona extensão se necessário
                if not filename.endswith('.gcode') and \
                   not filename.endswith('.nc') and \
                   not filename.endswith('.ngc'):
                    filename += '.gcode'

                # Salva usando o GCodeManager
                if gcode_manager.save_gcode_to_file(current_sequence, filename):
                    self.parent_window.statusBar().showMessage(
                        f"G-CODE salvo em {filename}"
                    )
                    logger.info(f"G-CODE salvo: {filename}")
                    self.gcode_saved.emit(filename)
                else:
                    error_msg = "Falha ao salvar o arquivo G-CODE"
                    QMessageBox.critical(self.parent_window, "Erro", error_msg)
                    self.file_operation_failed.emit(error_msg)

            except Exception as e:
                error_msg = f"Erro ao salvar G-CODE: {e}"
                logger.exception("Erro ao salvar arquivo G-CODE")
                QMessageBox.critical(self.parent_window, "Erro", error_msg)
                self.file_operation_failed.emit(error_msg)

    def save_program(self, current_sequence):
        """
        Salva o programa de inspeção atual.

        Args:
            current_sequence: Sequência atual (ou None)

        Emits:
            program_saved se salvo
            file_operation_failed se erro
        """
        if not current_sequence:
            QMessageBox.warning(
                self.parent_window,
                "Aviso",
                "Crie uma sequência primeiro"
            )
            self.file_operation_failed.emit("Nenhuma sequência para salvar")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self.parent_window,
            "Salvar Programa",
            "",
            "Arquivos JSON (*.json)"
        )

        if filename:
            try:
                if not filename.endswith('.json'):
                    filename += '.json'

                if self.controller.save_positions(filename):
                    self.parent_window.statusBar().showMessage(
                        f"Programa salvo em {filename}"
                    )
                    logger.info(f"Programa salvo: {filename}")
                    self.program_saved.emit(filename)
                else:
                    error_msg = "Falha ao salvar o programa"
                    QMessageBox.critical(self.parent_window, "Erro", error_msg)
                    self.file_operation_failed.emit(error_msg)

            except Exception as e:
                error_msg = f"Erro ao salvar programa: {e}"
                logger.exception("Erro ao salvar programa")
                QMessageBox.critical(self.parent_window, "Erro", error_msg)
                self.file_operation_failed.emit(error_msg)

    def load_program(self):
        """
        Carrega um programa de inspeção salvo.

        Emits:
            program_loaded se carregado
            file_operation_failed se erro
        """
        filename, _ = QFileDialog.getOpenFileName(
            self.parent_window,
            "Carregar Programa",
            "",
            "Arquivos JSON (*.json)"
        )

        if filename:
            try:
                if self.controller.load_positions(filename):
                    # Atualiza a interface
                    self.position_list_widget.clear_positions()

                    # Adiciona posições carregadas à lista
                    for name, position in self.controller.position_manager.positions.items():
                        self.position_list_widget.add_position(position)

                    # Se há sequências, usa a primeira como atual
                    if self.controller.position_manager.sequences:
                        sequence_name = next(iter(self.controller.position_manager.sequences))
                        sequence = self.controller.position_manager.sequences[sequence_name]
                        self.sequence_widget.sequence_name.setText(sequence_name)
                        self.sequence_widget.sequence_status.setText(
                            f"Carregada: {len(sequence.positions)} posições"
                        )

                    self.parent_window.statusBar().showMessage(
                        f"Programa carregado de {filename}"
                    )
                    logger.info(f"Programa carregado: {filename}")
                    self.program_loaded.emit(filename)
                else:
                    error_msg = "Falha ao carregar o programa"
                    QMessageBox.critical(self.parent_window, "Erro", error_msg)
                    self.file_operation_failed.emit(error_msg)

            except Exception as e:
                error_msg = f"Erro ao carregar programa: {e}"
                logger.exception("Erro ao carregar programa")
                QMessageBox.critical(self.parent_window, "Erro", error_msg)
                self.file_operation_failed.emit(error_msg)
