"""
managers/connection_manager.py
------------------------------
Gerencia conexões de hardware (PLC + Câmera + GRBL).
"""
import logging
import time
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QMessageBox, QComboBox
from aoi_lib import PLCAxisController
from grbl_streamer import GrblStreamer

logger = logging.getLogger(__name__)


class ConnectionManager(QObject):
    """
    Gerencia conexões com hardware (PLC via Modbus + Câmera).

    Responsabilidades:
        - Conectar/desconectar PLC
        - Conectar/desconectar câmera
        - Auto-connection ao iniciar
        - Emitir signals de status
    """

    # Signals PLC
    plc_connected = pyqtSignal()
    plc_disconnected = pyqtSignal()
    plc_connection_error = pyqtSignal(str)

    # Signals Câmera (para implementação futura)
    camera_connected = pyqtSignal()
    camera_disconnected = pyqtSignal()
    camera_error = pyqtSignal(str)

    def __init__(self, controller, config):
        super().__init__()
        self.controller = controller
        self.config = config
        self._plc_ui_settings_applied = False

    def connect_plc(self):
        """
        Conecta ao PLC usando o controlador existente.

        Emite signals:
            - plc_connected: em caso de sucesso
            - plc_connection_error: em caso de falha
        """
        # Verificar se é PLCAxisController
        if not isinstance(self.controller.cnc, PLCAxisController):
            logger.warning("CNC não é PLCAxisController, ignorando conexão PLC")
            return

        plc = self.controller.cnc

        # Se já está conectado, ignora
        if plc.is_connected:
            logger.info("PLC já está conectado")
            self.plc_connected.emit()
            return

        # Aplica configurações da UI antes de conectar
        self._apply_plc_ui_settings()

        logger.info(f"Tentando conectar ao PLC em {plc.host}:{plc.port}")
        try:
            plc.connect()
            logger.info(f"PLC conectado com sucesso em {plc.host}:{plc.port}")
            self.plc_connected.emit()
        except Exception as e:
            error_msg = f"Falha ao conectar ao PLC em {plc.host}:{plc.port}: {e}"
            logger.error(error_msg)
            self.plc_connection_error.emit(error_msg)

    def disconnect_plc(self):
        """
        Desconecta do PLC.

        Emite signal plc_disconnected.
        """
        # Verificar se é PLCAxisController
        if not isinstance(self.controller.cnc, PLCAxisController):
            logger.warning("CNC não é PLCAxisController, ignorando desconexão")
            return

        plc = self.controller.cnc

        # Se não está conectado, ignora
        if not plc.is_connected:
            logger.info("PLC já está desconectado")
            self.plc_disconnected.emit()
            return

        try:
            plc.close()
            logger.info("PLC desconectado pelo usuário")
            self.plc_disconnected.emit()
        except Exception as e:
            logger.error(f"Erro ao desconectar PLC: {e}")
            # Emite mesmo com erro, pois estado final é "desconectado"
            self.plc_disconnected.emit()

    def toggle_plc(self):
        """
        Alterna estado de conexão do PLC (connect/disconnect).
        """
        plc = self.controller.cnc

        # Verificar se é PLCAxisController
        if not isinstance(plc, PLCAxisController):
            logger.warning("CNC não é PLCAxisController")
            return

        if plc.is_connected:
            self.disconnect_plc()
        else:
            self.connect_plc()

    def attempt_auto_connect(self):
        """
        Tenta conectar automaticamente ao PLC se configurado.

        Lê a configuração 'auto_connect_plc' e tenta conectar se True.
        """
        if not isinstance(self.controller.cnc, PLCAxisController):
            logger.debug("CNC não é PLCAxisController, pulando auto-connect")
            return

        if self.config.get("connections", "auto_connect_plc", default=False):
            logger.info("Auto-connect PLC habilitado, tentando conectar...")
            self.connect_plc()
        else:
            logger.info("Auto-connect PLC desabilitado")

    def _apply_plc_ui_settings(self):
        """
        Aplica configurações de UI ao PLC.

        Este método lê configurações e as aplica ao controlador.
        Pode ser sobrescrito para aplicar configurações específicas da UI.
        """
        # Placeholder: implementar se necessário aplicar configurações específicas
        logger.debug("Aplicando configurações da UI ao PLC")
        self._plc_ui_settings_applied = True

    def connect_grbl(self, port, connect_btn, status_label, status_bar,
                     grbl_callback_handler, main_window):
        """
        Conecta ao CNC GRBL via serial.

        Args:
            port: Porta serial para conexão
            connect_btn: Botão de conectar (para atualizar texto)
            status_label: Label de status (para atualizar)
            status_bar: Barra de status (para mostrar mensagens)
            grbl_callback_handler: Handler de callbacks GRBL
            main_window: Referência ao main_window (para acessar controller/config)

        Returns:
            bool: True se conectou com sucesso, False caso contrário
        """
        if not port:
            QMessageBox.warning(main_window, "Erro", "Selecione uma porta serial")
            return False

        status_bar.showMessage(f"Conectando à CNC na porta {port}...")

        try:
            # Usa GRBLCallbackHandler para gerenciar callbacks complexos
            grbl_callback = grbl_callback_handler.create_callback()

            # Inicializa o GrblStreamer com o callback
            main_window.controller.cnc.grbl = GrblStreamer(grbl_callback)

            logger.debug(f"CONEXÃO: Tentando conectar à porta {port} com baudrate 115200")
            # Conecta usando o método cnect()
            main_window.controller.cnc.grbl.cnect(port, 115200)
            time.sleep(2.0)

            if not main_window.controller.cnc.grbl.connected:
                logger.error("CONEXÃO: Falha ao estabelecer conexão serial (grbl.connected é False).")
                raise ConnectionError("Falha ao conectar à porta serial após inicialização.")

            logger.debug("CONEXÃO: Enviando comando de desbloqueio $X")
            main_window.controller.cnc.grbl.send_immediately("$X")
            time.sleep(0.1)

            logger.debug("CONEXÃO: Configurando $10=3 para relatório completo de posição")
            main_window.controller.cnc.grbl.send_immediately("$10=3") # Mantém $10=3 para receber MPos
            time.sleep(0.1)

            # Solicitar estado hash logo após conectar para obter offsets
            logger.debug("CONEXÃO: Solicitando estado hash ($#) para obter offsets")
            main_window.controller.cnc.grbl.send_immediately("$#")
            time.sleep(0.1)

            logger.debug("CONEXÃO: Configurando modo relativo G91")
            main_window.controller.cnc.grbl.send_immediately("G91")
            time.sleep(0.1)

            logger.debug("CONEXÃO: Iniciando polling de status")
            main_window.controller.cnc.grbl.poll_start()

            main_window.controller.cnc.is_connected = True
            main_window.config.apply_to_cnc(main_window.controller.cnc)
            main_window.config.remember_cnc_port(port)
            main_window.controller.cnc.machine_status = "Idle"
            connect_btn.setText("Desconectar CNC")
            status_label.setText("Conectado")
            status_bar.showMessage(f"CNC conectada na porta {port}")

            return True

        except Exception as e:
            # Tratamento de erro de conexão
            logger.error(f"CONEXÃO: Falha ao conectar ou configurar: {str(e)}", exc_info=True)
            QMessageBox.critical(main_window, "Erro", f"Falha ao conectar a CNC: {str(e)}")

            if hasattr(main_window.controller.cnc, 'grbl') and main_window.controller.cnc.grbl:
                try:
                    main_window.controller.cnc.grbl.disconnect()
                except:
                    pass

            main_window.controller.cnc.grbl = None
            main_window.controller.cnc.is_connected = False
            main_window.controller.cnc.machine_status = "Erro Conexão"
            connect_btn.setText("Conectar CNC")
            status_label.setText("Erro Conexão")

            return False

    def disconnect_grbl(self, connect_btn, status_label, status_bar, main_window):
        """
        Desconecta do CNC GRBL.

        Args:
            connect_btn: Botão de conectar (para atualizar texto)
            status_label: Label de status (para atualizar)
            status_bar: Barra de status (para mostrar mensagens)
            main_window: Referência ao main_window
        """
        if hasattr(main_window.controller.cnc, 'grbl') and main_window.controller.cnc.grbl:
            main_window.controller.cnc.grbl.poll_stop()
            main_window.controller.cnc.grbl.disconnect()
            main_window.controller.cnc.grbl = None
            main_window.controller.cnc.is_connected = False
            connect_btn.setText("Conectar CNC")
            status_label.setText("Desconectado")
            status_bar.showMessage("CNC desconectada")

    def refresh_serial_ports(self, port_combo):
        """
        Atualiza a lista de portas seriais disponíveis.

        Args:
            port_combo: QComboBox para preencher com portas
        """
        import serial.tools.list_ports

        port_combo.clear()
        ports = serial.tools.list_ports.comports()

        if ports:
            for port in ports:
                port_combo.addItem(port.device)
            logger.info(f"Portas seriais encontradas: {[p.device for p in ports]}")
        else:
            port_combo.addItem("Nenhuma porta encontrada")
            logger.warning("Nenhuma porta serial encontrada")

    # TODO: Implementar métodos de câmera (connect_camera, test_camera, etc)
