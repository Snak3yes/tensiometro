"""
services/resource_manager.py
----------------------------
Gerenciador de recursos da aplicação.

Encapsula lógica de limpeza e gerenciamento de recursos (threads, timers, dispositivos).
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ResourceManager:
    """
    Gerencia recursos da aplicação (threads, timers, conexões).

    Responsabilidades:
        - Parar sequências em execução
        - Parar timers
        - Parar e limpar QThreads
        - Desconectar dispositivos (câmera, CNC, GRBL)
        - Gerenciar ciclo de vida de recursos
        - Evitar limpeza duplicada
    """

    def __init__(self, controller):
        """
        Inicializa o gerenciador de recursos.

        Args:
            controller: CNCAOIController com acesso a todos os recursos
        """
        self.controller = controller
        self._already_clean = False

    def cleanup_all(self, main_window):
        """
        Para tudo que possa manter o Qt vivo após o fechamento.

        Executa limpeza completa em ordem segura:
        1. Para sequências em execução
        2. Para timers
        3. Para QThreads
        4. Para thread de status do GRBL
        5. Desconecta grbl-streamer
        6. Desconecta dispositivos (câmera, CNC)

        Args:
            main_window: Referência ao main_window para acessar widgets e recursos
        """
        # Evita executar limpeza duplicada
        if self._already_clean:
            logger.debug("Limpeza já foi executada, ignorando")
            return
        self._already_clean = True

        logger.info("Iniciando limpeza de recursos...")

        # 1) Sequências em execução
        self._stop_sequences(main_window)

        # 2) Timers
        self._stop_timers(main_window)

        # 3) QThreads
        self._stop_threads(main_window)

        # 4) Thread de status do GRBL dentro do controlador CNC
        self._stop_grbl_status_thread()

        # 5) grbl-streamer (poll thread)
        self._disconnect_grbl()

        # 6) Dispositivos
        self._disconnect_devices()

        logger.info("Limpeza de recursos concluída")

    def _stop_sequences(self, main_window):
        """
        Para sequências em execução.

        Args:
            main_window: Referência ao main_window
        """
        if getattr(main_window, "is_running_sequence", False):
            logger.debug("Parando sequência em execução...")
            try:
                self.controller.stop_sequence()
            except Exception as e:
                logger.error(f"Erro ao parar sequência: {e}")

    def _stop_timers(self, main_window):
        """
        Para timers ativos.

        Args:
            main_window: Referência ao main_window
        """
        # Para update_timer
        for tm_name in ("update_timer",):
            tm = getattr(main_window, tm_name, None)
            if tm and tm.isActive():
                logger.debug(f"Parando timer {tm_name}...")
                tm.stop()

        # Para preview da câmera
        if getattr(main_window, "camera_preview", None):
            logger.debug("Parando preview da câmera...")
            try:
                main_window.camera_preview.stop_preview()
            except Exception as e:
                logger.error(f"Erro ao parar preview: {e}")

    def _stop_threads(self, main_window):
        """
        Para e limpa QThreads.

        Args:
            main_window: Referência ao main_window
        """
        thread_names = ("run_thread", "map_thread", "_move_thread")

        for th_name in thread_names:
            th = getattr(main_window, th_name, None)
            if th and th.isRunning():
                logger.debug(f"Parando thread {th_name}...")
                try:
                    th.requestInterruption()
                    th.quit()
                    th.wait(2000)  # aguarda até 2 s
                except Exception as e:
                    logger.error(f"Erro ao parar thread {th_name}: {e}")

    def _stop_grbl_status_thread(self):
        """Para thread de status do GRBL dentro do controlador CNC."""
        if getattr(self.controller.cnc, "running", False):
            logger.debug("Parando thread de status do GRBL...")
            try:
                self.controller.cnc.running = False
                if getattr(self.controller.cnc, "status_thread", None):
                    self.controller.cnc.status_thread.join(timeout=2)
            except Exception as e:
                logger.error(f"Erro ao parar thread de status GRBL: {e}")

    def _disconnect_grbl(self):
        """Desconecta grbl-streamer (poll thread + serial)."""
        if getattr(self.controller.cnc, "grbl", None):
            logger.debug("Desconectando grbl-streamer...")
            try:
                self.controller.cnc.grbl.poll_stop()
                self.controller.cnc.grbl.disconnect()  # fecha serial + join
                logger.debug("grbl-streamer desconectado")
            except Exception as e:
                logger.warning(f"Erro ao desconectar grbl-streamer: {e}")

    def _disconnect_devices(self):
        """Desconecta dispositivos (câmera e CNC)."""
        # Desconecta câmera
        if getattr(self.controller.camera, "is_connected", False):
            logger.debug("Desconectando câmera...")
            try:
                self.controller.camera.disconnect()
                logger.debug("Câmera desconectada")
            except Exception as e:
                logger.error(f"Erro ao desconectar câmera: {e}")

        # Desconecta CNC
        if getattr(self.controller.cnc, "is_connected", False):
            logger.debug("Desconectando CNC...")
            try:
                self.controller.cnc.disconnect()
                logger.debug("CNC desconectado")
            except Exception as e:
                logger.error(f"Erro ao desconectar CNC: {e}")

    @property
    def is_cleaned(self) -> bool:
        """Retorna True se a limpeza já foi executada."""
        return self._already_clean
