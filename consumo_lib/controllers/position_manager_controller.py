"""
PositionManagerController - Controller para Gerenciamento de Posições

Este controller gerencia operações relacionadas a posições CNC:
- Adicionar/remover posições da lista
- Atualizar display de posição atual
- Selecionar posições
- Criar sequências
- Capturar posições

Responsabilidade:
- Gerenciar toda lógica de manipulação de posições
- Validar pré-condições (ex: CNC conectada)
- Emitir signals quando eventos ocorrem

Signals Emitidos:
- position_updated(position) - Posição CNC atualizada
- position_added(position) - Posição adicionada
- position_removed(position_name) - Posição removida
- position_selected(position) - Posição selecionada
- sequence_created(sequence) - Sequência criada
- position_captured(position, image, timestamp) - Posição capturada
"""

import logging
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QInputDialog, QMessageBox

logger = logging.getLogger("consumo_lib")


class PositionManagerController(QObject):
    """
    Controller para gerenciamento de posições CNC.

    Responsável por gerenciar adição, remoção, seleção e
    atualização de posições no sistema.
    """

    # Signals
    position_updated = pyqtSignal(dict)  # position dict com x,y,z
    position_added = pyqtSignal(object)  # InspectionPosition
    position_removed = pyqtSignal(str)  # position_name
    position_selected = pyqtSignal(object)  # InspectionPosition
    sequence_created = pyqtSignal(object)  # Sequence
    position_captured = pyqtSignal(object, object, float)  # position, image, timestamp

    def __init__(self, controller, position_list_widget, parent=None):
        """
        Inicializa o PositionManagerController.

        Args:
            controller: Instância de CNCAOIController
            position_list_widget: Widget de lista de posições
            parent: Widget pai (geralmente main_window)
        """
        super().__init__(parent)
        self.controller = controller
        self.position_list_widget = position_list_widget
        self.parent_window = parent

        # Estado para rastreamento de posição
        self.last_logged_position = None

        logger.debug("PositionManagerController inicializado")

    def update_position_display(self, x_position_label, y_position_label,
                                z_position_label=None, cnc_status_label=None):
        """
        Atualiza a exibição da posição atual CNC (WPos calculada).

        Args:
            x_position_label: QLabel para coordenada X
            y_position_label: QLabel para coordenada Y
            z_position_label: QLabel opcional para coordenada Z
            cnc_status_label: QLabel opcional para status CNC

        Emits:
            position_updated se posição obtida com sucesso
        """
        if not self.controller.cnc.is_connected:
            return

        try:
            # get_current_position retorna a WPos calculada
            position = self.controller.cnc.get_current_position()
        except Exception as e:
            logger.error("update_position_display: erro ao obter posição: %s", e)
            return

        # Rastreamento de mudanças de posição
        if self.last_logged_position is not None:
            if position != self.last_logged_position:
                logger.debug("Posição mudou de %s para %s",
                           self.last_logged_position, position)

        self.last_logged_position = position.copy()

        # Atualiza os labels da interface com a WPos calculada
        x_position_label.setText(f"{position['x']:.3f} mm")
        y_position_label.setText(f"{position['y']:.3f} mm")

        # Z axis (opcional)
        if z_position_label is not None:
            z_position_label.setText(f"{position['z']:.3f} mm")

        # CNC status (opcional)
        if cnc_status_label is not None:
            cnc_status_label.setText(self.controller.cnc.machine_status)

        # Emit signal
        self.position_updated.emit(position)

    def add_current_position(self):
        """
        Adiciona a posição atual à lista de posições.

        Solicita nome da posição ao usuário e adiciona à lista.

        Emits:
            position_added se posição adicionada
        """
        if not self.controller.cnc.is_connected:
            QMessageBox.warning(
                self.parent_window,
                "Aviso",
                "CNC não conectada"
            )
            return

        position_name, ok = QInputDialog.getText(
            self.parent_window,
            "Nova Posição",
            "Nome da posição:"
        )

        if ok and position_name:
            position = self.controller.add_current_position(position_name)
            self.position_list_widget.add_position(position)

            self.parent_window.statusBar().showMessage(
                f"Posição '{position_name}' adicionada"
            )
            logger.info(f"Posição '{position_name}' adicionada em "
                       f"({position.x:.3f}, {position.y:.3f})")

            # Emit signal
            self.position_added.emit(position)

    def remove_position(self):
        """
        Remove a posição selecionada da lista.

        Emits:
            position_removed se posição removida
        """
        position = self.position_list_widget.remove_selected_position()

        if position:
            self.controller.position_manager.remove_position(position.name)

            self.parent_window.statusBar().showMessage(
                f"Posição '{position.name}' removida"
            )
            logger.info(f"Posição '{position.name}' removida")

            # Emit signal
            self.position_removed.emit(position.name)

    def on_position_selected(self, position):
        """
        Handler chamado quando uma posição é selecionada na lista.

        Args:
            position: Instância de InspectionPosition

        Emits:
            position_selected
        """
        message = (f"Posição selecionada: {position.name} "
                  f"({position.x:.3f}, {position.y:.3f})")

        self.parent_window.statusBar().showMessage(message)
        logger.debug(message)

        # Emit signal
        self.position_selected.emit(position)

    def create_sequence(self, sequence_name_widget, sequence_status_widget,
                       current_sequence_ref):
        """
        Cria uma nova sequência com as posições atuais.

        Args:
            sequence_name_widget: Widget com nome da sequência
            sequence_status_widget: Widget para status da sequência
            current_sequence_ref: Referência para armazenar sequência atual

        Emits:
            sequence_created se sequência criada
        """
        positions = self.position_list_widget.get_all_positions()

        if not positions:
            QMessageBox.warning(
                self.parent_window,
                "Aviso",
                "Adicione pelo menos uma posição"
            )
            return

        sequence_name = sequence_name_widget.text()
        if not sequence_name:
            QMessageBox.warning(
                self.parent_window,
                "Aviso",
                "Digite um nome para a sequência"
            )
            return

        # Cria sequência via controller
        sequence = self.controller.create_sequence(sequence_name, positions)

        # Atualiza referência da sequência atual
        current_sequence_ref[0] = sequence

        self.parent_window.statusBar().showMessage(
            f"Sequência '{sequence_name}' criada com {len(positions)} posições"
        )
        sequence_status_widget.setText(f"Criada: {len(positions)} posições")

        logger.info(f"Sequência '{sequence_name}' criada com {len(positions)} posições")

        # Emit signal
        self.sequence_created.emit(sequence)

    def on_position_captured(self, position, image, timestamp):
        """
        Handler chamado quando uma posição é capturada.

        Args:
            position: Instância de InspectionPosition
            image: Imagem capturada (numpy array)
            timestamp: Timestamp da captura

        Emits:
            position_captured
        """
        message = (f"Posição capturada: {position.name} "
                  f"({position.x:.3f}, {position.y:.3f})")

        self.parent_window.statusBar().showMessage(message, 3000)
        logger.info(message)

        # Emit signal
        self.position_captured.emit(position, image, timestamp)

    # =========================================================================
    # UI HANDLERS (Migrados do SignalAggregator)
    # =========================================================================

    def setup_ui_handlers(self):
        """
        Configura handlers de UI para signals de posição.

        Este método conecta os signals internos do PositionManagerController
        aos métodos que atualizam a UI do main_window.

        Deve ser chamado durante a inicialização do main_window.
        """
        # Conectar signals a handlers de UI
        self.position_updated.connect(self._on_position_updated_log)
        self.position_added.connect(self._on_position_added_log)
        self.position_removed.connect(self._on_position_removed_log)
        self.position_selected.connect(self._on_position_selected_log)
        self.sequence_created.connect(self._on_sequence_created_update_ui)
        self.position_captured.connect(self._on_position_captured_update_status)

        logger.debug("UI handlers conectados no PositionManagerController")

    def _on_position_updated_log(self, position):
        """
        Log quando posição CNC é atualizada.

        Args:
            position: Dict com posição {x, y, z}
        """
        logger.debug(f"Posição atualizada: {position}")

    def _on_position_added_log(self, position):
        """
        Log quando posição é adicionada.

        Args:
            position: InspectionPosition adicionada
        """
        logger.info(f"Posição adicionada: {position.name}")

    def _on_position_removed_log(self, position_name):
        """
        Log quando posição é removida.

        Args:
            position_name: Nome da posição removida
        """
        logger.info(f"Posição removida: {position_name}")

    def _on_position_selected_log(self, position):
        """
        Log quando posição é selecionada.

        Args:
            position: InspectionPosition selecionada
        """
        logger.debug(f"Posição selecionada: {position.name}")

    def _on_sequence_created_update_ui(self, sequence):
        """
        Atualiza UI quando sequência é criada.

        Args:
            sequence: Sequence criada
        """
        self.parent_window.current_sequence = sequence
        logger.info(f"Sequência '{sequence.name}' criada com {len(sequence.positions)} posições")

        if hasattr(self.parent_window, 'statusBar'):
            self.parent_window.statusBar().showMessage(
                f"Sequência '{sequence.name}' criada com {len(sequence.positions)} posições",
                5000
            )

    def _on_position_captured_update_status(self, position, image, timestamp):
        """
        Atualiza statusBar quando posição é capturada.

        Args:
            position: InspectionPosition capturada
            image: Imagem capturada
            timestamp: Timestamp da captura
        """
        logger.info(
            f"Posição capturada: {position.name} "
            f"({position.x:.3f}, {position.y:.3f})"
        )

        if hasattr(self.parent_window, 'statusBar'):
            self.parent_window.statusBar().showMessage(
                f"Posição capturada: {position.name} ({position.x:.3f}, {position.y:.3f})",
                3000
            )
