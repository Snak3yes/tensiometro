"""
Hardware Factory - Factory para criar componentes de hardware

Responsável por criar managers e facades para gerenciar hardware.
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aoi_lib import CNCAOIController
    from consumo_lib.managers import ConnectionManager

logger = logging.getLogger(__name__)


class HardwareFactory:
    """
    Factory para criar componentes de hardware.

    Responsabilidades:
    - Criar ConnectionManager
    - Criar facades de hardware (HardwareConnectionFacade)
    - Injetar dependências necessárias
    """

    def __init__(self,
                 controller: 'CNCAOIController',
                 config,
                 main_window):
        """
        Inicializa a factory com dependências necessárias.

        Args:
            controller: Controller principal CNC
            config: Gerenciador de configuração
            main_window: Janela principal
        """
        self.controller = controller
        self.config = config
        self.main_window = main_window

        logger.debug("HardwareFactory inicializada")

    def create_connection_manager(self) -> 'ConnectionManager':
        """
        Cria gerenciador de conexões de hardware.

        Returns:
            Instância de ConnectionManager configurada
        """
        from consumo_lib.managers import ConnectionManager

        conn_manager = ConnectionManager(
            self.controller,
            self.config
        )

        logger.debug("ConnectionManager criado")
        return conn_manager

    def create_hardware_connection_facade(self, connection_manager: 'ConnectionManager'):
        """
        Cria facade para gerenciar conexões de hardware.

        Args:
            connection_manager: Gerenciador de conexões existente

        Returns:
            Instância de HardwareConnectionFacade
        """
        from consumo_lib.facades import HardwareConnectionFacade

        facade = HardwareConnectionFacade(
            connection_manager,
            self.main_window
        )

        logger.debug("HardwareConnectionFacade criada")
        return facade
