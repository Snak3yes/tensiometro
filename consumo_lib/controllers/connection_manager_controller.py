"""
ConnectionManagerController - Controller para Gerenciamento de Conexões

Este controller gerencia as conexões de hardware do sistema:
- Conexão de câmera (USB/HTTP)
- Gerenciamento de portas seriais
- Configurações de PLC (IP/porta)
- Teste de captura de câmera

Responsabilidade:
- Gerenciar conexões de câmera
- Atualizar lista de portas seriais
- Aplicar configurações de PLC
- Notificar estado de conexões via signals

Signals Emitidos:
- camera_connected(camera_id) - Câmera conectada com sucesso
- camera_disconnected() - Câmera desconectada
- camera_connection_error(error) - Erro na conexão da câmera
- plc_settings_changed(host, port) - Configurações de PLC alteradas
- ports_refreshed(ports_list) - Lista de portas atualizada
"""

import logging
from typing import List, Optional, Union

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QMessageBox

from aoi_lib.plc_axis_controller import PLCAxisController

logger = logging.getLogger("consumo_lib")


class ConnectionManagerController(QObject):
    """
    Controller para gerenciamento de conexões de hardware.

    Responsável por gerenciar conexões de câmera, portas seriais
    e configurações de PLC, emitindo signals apropriados para
    notificar mudanças de estado.
    """

    # Signals
    camera_connected = pyqtSignal(object)  # camera_id (int ou str)
    camera_disconnected = pyqtSignal()
    camera_connection_error = pyqtSignal(str)  # error_message
    plc_settings_changed = pyqtSignal(str, int)  # host, port
    ports_refreshed = pyqtSignal(list)  # ports_list

    def __init__(self, controller, config_manager, camera_preview_widget, parent=None):
        """
        Inicializa o ConnectionManagerController.

        Args:
            controller: Instância de CNCAOIController
            config_manager: Instância de AOIConfigManager
            camera_preview_widget: Widget de preview da câmera
            parent: Widget pai (geralmente main_window)
        """
        super().__init__(parent)
        self.controller = controller
        self.config = config_manager
        self.camera_preview = camera_preview_widget
        self.parent_window = parent

        logger.debug("ConnectionManagerController inicializado")

    # =========================================================================
    # MÉTODOS PÚBLICOS
    # =========================================================================

    def refresh_ports(self, port_combo_widget):
        """
        Atualiza a lista de portas seriais disponíveis.

        Args:
            port_combo_widget: QComboBox para preencher com as portas

        Emits:
            ports_refreshed signal com lista de portas encontradas
        """
        import serial.tools.list_ports

        port_combo_widget.clear()
        ports = [port.device for port in serial.tools.list_ports.comports()]

        if ports:
            port_combo_widget.addItems(ports)

            # Verificar se COM9 está na lista e selecionar
            com9_index = port_combo_widget.findText("COM9")
            if com9_index >= 0:
                port_combo_widget.setCurrentIndex(com9_index)
                self.parent_window.statusBar().showMessage("Porta COM9 detectada")
                logger.info("Porta COM9 detectada e selecionada")
        else:
            self.parent_window.statusBar().showMessage("Nenhuma porta serial encontrada")
            logger.warning("Nenhuma porta serial encontrada")

        # Emit signal
        self.ports_refreshed.emit(ports)

    def apply_plc_ui_settings(self, plc_host_input, plc_port_input):
        """
        Atualiza IP/porta do PLC vindos da UI e persiste no config.

        Args:
            plc_host_input: QLineEdit com host do PLC
            plc_port_input: QSpinBox com porta do PLC

        Emits:
            plc_settings_changed signal com host e porta
        """
        if not isinstance(self.controller.cnc, PLCAxisController):
            logger.debug("CNC não é PLCAxisController, ignorando configurações de PLC")
            return

        host = (plc_host_input.text() or "").strip() or "192.168.1.5"
        port = int(plc_port_input.value())
        current_host = getattr(self.controller.cnc, "host", None)
        current_port = getattr(self.controller.cnc, "port", None)
        current_port_int = int(current_port) if current_port is not None else None

        # Persistência no arquivo de config
        self.config.set("connections", "plc_host", value=host)
        self.config.set("connections", "plc_port", value=port)
        self.config.save()

        # Verifica se houve mudança
        if host == current_host and current_port_int == port:
            logger.debug(f"Configurações do PLC inalteradas: {host}:{port}")
            return

        # Aplica mudanças
        try:
            self.controller.cnc.set_connection_params(host, port)
            self.parent_window.statusBar().showMessage(
                f"Configurações do PLC atualizadas para {host}:{port}"
            )
            logger.info(f"Configurações do PLC atualizadas: {host}:{port}")
        except Exception as e:
            logger.error(f"Falha ao aplicar IP/porta do PLC: {e}")
            self.camera_connection_error.emit(f"Falha ao aplicar configurações: {e}")
            return

        # Emit signal
        self.plc_settings_changed.emit(host, port)

    def connect_camera(self, camera_id_combo, connect_button):
        """
        Conecta ou desconecta a câmera.

        Args:
            camera_id_combo: QComboBox com ID da câmera
            connect_button: QPushButton de conectar/desconectar

        Emits:
            camera_connected signal com ID da câmera
            camera_disconnected signal
            camera_connection_error signal com mensagem de erro
        """
        camera = self.controller.camera

        if hasattr(camera, 'is_connected') and camera.is_connected:
            # Desconectar
            self._disconnect_camera(connect_button)
        else:
            # Conectar
            self._connect_camera(camera_id_combo, connect_button)

    def test_camera(self):
        """
        Testa a captura de imagem da câmera.

        Exibe a imagem capturada no widget de preview.

        Returns:
            bool: True se captura bem-sucedida, False caso contrário
        """
        camera = self.controller.camera

        if not hasattr(camera, 'is_connected') or not camera.is_connected:
            logger.warning("Tentativa de testar câmera desconectada")
            return False

        try:
            image = camera.capture()

            if image is not None:
                # Exibe imagem no preview
                self.camera_preview.display_image(image)
                self.parent_window.statusBar().showMessage(
                    "Imagem de teste capturada com sucesso"
                )
                logger.info("Teste de câmera executado com sucesso")
                return True
            else:
                error_msg = "Falha ao capturar imagem (retornou None)"
                self.parent_window.statusBar().showMessage(error_msg)
                logger.warning(error_msg)
                return False

        except Exception as e:
            error_msg = f"Erro ao testar câmera: {e}"
            logger.exception("Erro ao testar câmera")
            self.camera_connection_error.emit(error_msg)
            return False

    # =========================================================================
    # MÉTODOS PRIVADOS
    # =========================================================================

    def _connect_camera(self, camera_id_combo, connect_button):
        """
        Conecta à câmera.

        Args:
            camera_id_combo: QComboBox com ID da câmera
            connect_button: QPushButton para atualizar texto
        """
        try:
            # Obtém texto do combo (pode ser número ou URL)
            id_text = camera_id_combo.currentText().strip()

            # Tenta converter para int se for numérico
            if id_text.isdigit():
                camera_id = int(id_text)
            else:
                camera_id = id_text

            self.parent_window.statusBar().showMessage(
                f"Conectando à câmera {camera_id}..."
            )
            logger.info(f"Tentando conectar à câmera {camera_id}")

            if self.controller.connect_camera(camera_id):
                connect_button.setText("Desconectar Câmera")
                self.parent_window.statusBar().showMessage(
                    f"Câmera {camera_id} conectada"
                )
                logger.info(f"Câmera {camera_id} conectada com sucesso")

                # Salva no config
                self.config.remember_camera_id(camera_id)

                # Emit signal
                self.camera_connected.emit(camera_id)
            else:
                error_msg = f"Falha ao conectar à câmera: {self.controller.camera.last_error}"
                logger.error(error_msg)
                QMessageBox.warning(
                    self.parent_window,
                    "Erro",
                    error_msg
                )
                self.camera_connection_error.emit(error_msg)

        except Exception as e:
            error_msg = f"Erro ao conectar câmera: {e}"
            logger.exception("Exceção ao conectar câmera")
            QMessageBox.warning(
                self.parent_window,
                "Erro",
                error_msg
            )
            self.camera_connection_error.emit(error_msg)

    def _disconnect_camera(self, connect_button):
        """
        Desconecta a câmera.

        Args:
            connect_button: QPushButton para atualizar texto
        """
        # Interrompe preview antes de liberar a câmera
        self.camera_preview.stop_preview()

        # Desconectar
        self.controller.camera.disconnect()
        connect_button.setText("Conectar Câmera")
        self.parent_window.statusBar().showMessage("Câmera desconectada")
        logger.info("Câmera desconectada")

        # Emit signal
        self.camera_disconnected.emit()
