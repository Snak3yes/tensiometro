"""
Hardware Connection Facade - Interface simplificada para conexões de hardware

Facade que proporciona uma interface simplificada para gerenciar
conexões de hardware (PLC, CNC, Câmera).
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class HardwareConnectionFacade:
    """
    Facade para gerenciar conexões de hardware.

    Esta classe encapsula a complexidade de gerenciar conexões com
    diferentes tipos de hardware (PLC, CNC, Câmera), proporcionando
    uma interface unificada e simplificada.

    Responsabilidades:
    - Conectar/desconectar PLC (Modbus TCP)
    - Conectar/desconectar CNC (Serial)
    - Conectar/desconectar Câmera (USB/IP)
    - Testar hardware
    - Atualizar lista de portas
    - Aplicar configurações de UI

    A facade delega para ConnectionManager, mas proporciona
    métodos com nomes mais simples e adequados para a MainWindow.
    """

    def __init__(self, connection_manager, main_window):
        """
        Inicializa a facade.

        Args:
            connection_manager: Gerenciador de conexões existente
            main_window: Janela principal (para atualizar UI)
        """
        self.connection_manager = connection_manager
        self.main_window = main_window

        logger.debug("HardwareConnectionFacade inicializada")

    def connect_plc(self, host: str, port: int) -> bool:
        """
        Conecta ao PLC via Modbus TCP.

        Args:
            host: Endereço IP do PLC
            port: Porta Modbus

        Returns:
            True se conectado com sucesso, False caso contrário
        """
        try:
            success = self.connection_manager.connect_plc(host, port)

            if success:
                logger.info(f"PLC conectado em {host}:{port}")
                self.main_window.statusBar().showMessage(
                    f"PLC conectado em {host}:{port}", 3000
                )
            else:
                logger.warning(f"Falha ao conectar PLC em {host}:{port}")
                self.main_window.statusBar().showMessage(
                    f"Falha ao conectar PLC", 3000
                )

            return success
        except Exception as e:
            logger.error(f"Erro ao conectar PLC: {e}")
            self.main_window.statusBar().showMessage(
                f"Erro ao conectar PLC: {e}", 3000
            )
            return False

    def connect_cnc(self, port: str) -> bool:
        """
        Conecta ao CNC via serial.

        Args:
            port: Porta serial (ex: "COM3")

        Returns:
            True se conectado com sucesso, False caso contrário
        """
        try:
            success = self.connection_manager.connect_cnc(port)

            if success:
                logger.info(f"CNC conectado na porta {port}")
                self.main_window.statusBar().showMessage(
                    f"CNC conectado na porta {port}", 3000
                )
            else:
                logger.warning(f"Falha ao conectar CNC na porta {port}")
                self.main_window.statusBar().showMessage(
                    f"Falha ao conectar CNC", 3000
                )

            return success
        except Exception as e:
            logger.error(f"Erro ao conectar CNC: {e}")
            self.main_window.statusBar().showMessage(
                f"Erro ao conectar CNC: {e}", 3000
            )
            return False

    def connect_camera(self, camera_id: str) -> bool:
        """
        Conecta à câmera.

        Args:
            camera_id: ID da câmera (0, 1, 2...) ou URL

        Returns:
            True se conectado com sucesso, False caso contrário
        """
        try:
            success = self.connection_manager.connect_camera(camera_id)

            if success:
                logger.info(f"Câmera conectada: {camera_id}")
                self.main_window.statusBar().showMessage(
                    f"Câmera conectada: {camera_id}", 3000
                )
            else:
                logger.warning(f"Falha ao conectar câmera: {camera_id}")
                self.main_window.statusBar().showMessage(
                    f"Falha ao conectar câmera", 3000
                )

            return success
        except Exception as e:
            logger.error(f"Erro ao conectar câmera: {e}")
            self.main_window.statusBar().showMessage(
                f"Erro ao conectar câmera: {e}", 3000
            )
            return False

    def test_camera(self) -> bool:
        """
        Testa a conexão da câmera.

        Returns:
            True se teste bem-sucedido, False caso contrário
        """
        try:
            success = self.connection_manager.test_camera()

            if success:
                logger.info("Teste de câmera bem-sucedido")
                self.main_window.statusBar().showMessage(
                    "Teste de câmera OK", 3000
                )
            else:
                logger.warning("Teste de câmera falhou")
                self.main_window.statusBar().showMessage(
                    "Teste de câmera falhou", 3000
                )

            return success
        except Exception as e:
            logger.error(f"Erro ao testar câmera: {e}")
            self.main_window.statusBar().showMessage(
                f"Erro ao testar câmera: {e}", 3000
            )
            return False

    def refresh_ports(self) -> list[str]:
        """
        Atualiza lista de portas seriais disponíveis.

        Returns:
            Lista de portas disponíveis
        """
        try:
            ports = self.connection_manager.refresh_serial_ports()
            logger.debug(f"Portas disponíveis: {ports}")
            return ports
        except Exception as e:
            logger.error(f"Erro ao atualizar portas: {e}")
            return []

    def apply_plc_ui_settings(self):
        """
        Aplica configurações de UI baseadas no tipo de PLC.

        Atualiza labels e textos baseados no tipo de controller
        (PLCAxisController vs GrblStreamer).
        """
        try:
            from aoi_lib.plc_axis_controller import PLCAxisController

            if isinstance(self.connection_manager.cnc, PLCAxisController):
                # Modo PLC
                self.main_window.connect_cnc_btn.setText("Conectar PLC")
                logger.debug("UI configurada para modo PLC")
            else:
                # Modo GRBL
                self.main_window.connect_cnc_btn.setText("Conectar CNC")
                logger.debug("UI configurada para modo GRBL")
        except Exception as e:
            logger.error(f"Erro ao aplicar configurações UI: {e}")

    def is_plc_connected(self) -> bool:
        """
        Verifica se o PLC está conectado.

        Returns:
            True se conectado, False caso contrário
        """
        return self.connection_manager.is_plc_connected()

    def is_cnc_connected(self) -> bool:
        """
        Verifica se o CNC está conectado.

        Returns:
            True se conectado, False caso contrário
        """
        return self.connection_manager.is_cnc_connected()

    def is_camera_connected(self) -> bool:
        """
        Verifica se a câmera está conectada.

        Returns:
            True se conectada, False caso contrário
        """
        return self.connection_manager.is_camera_connected()
