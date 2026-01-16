"""
Controller Factory - Factory para criar controllers

Responsável por criar todos os controllers da aplicação de forma desacoplada.
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aoi_lib import CNCAOIController
    from aoi_lib.config_manager import AOIConfigManager
    from consumo_lib.controllers import (
        MapController,
        SequenceController,
        ConnectionManagerController,
        TensionMeasurementController,
        PositionManagerController
    )

logger = logging.getLogger(__name__)


class ControllerFactory:
    """
    Factory para criar controllers da aplicação.

    Responsabilidades:
    - Criar todos os controllers (Map, Sequence, Connection, etc.)
    - Injetar dependências necessárias
    - Configurar cada controller adequadamente
    """

    def __init__(self,
                 controller: 'CNCAOIController',
                 config: 'AOIConfigManager',
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

        logger.debug("ControllerFactory inicializada")

    def create_sequence_controller(self) -> 'SequenceController':
        """
        Cria controller de sequência.

        Returns:
            Instância de SequenceController configurada
        """
        from consumo_lib.controllers import SequenceController

        seq_controller = SequenceController(
            self.controller,
            self.config
        )

        logger.debug("SequenceController criado")
        return seq_controller

    def create_connection_manager_controller(self, camera_preview) -> 'ConnectionManagerController':
        """
        Cria controller de gerenciador de conexões.

        Args:
            camera_preview: Widget de preview da câmera

        Returns:
            Instância de ConnectionManagerController configurada
        """
        from consumo_lib.controllers import ConnectionManagerController

        conn_controller = ConnectionManagerController(
            self.controller,
            self.config,
            camera_preview,
            self.main_window
        )

        logger.debug("ConnectionManagerController criado")
        return conn_controller

    def create_tension_measurement_controller(self) -> 'TensionMeasurementController':
        """
        Cria controller de medição de tensão.

        Returns:
            Instância de TensionMeasurementController configurada
        """
        from consumo_lib.controllers import TensionMeasurementController

        tension_controller = TensionMeasurementController(
            self.controller,
            self.config,
            self.main_window
        )

        logger.debug("TensionMeasurementController criado")
        return tension_controller

    def create_position_manager_controller(self) -> 'PositionManagerController':
        """
        Cria controller de gerenciador de posições.

        Returns:
            Instância de PositionManagerController configurada
        """
        from consumo_lib.controllers import PositionManagerController

        pos_controller = PositionManagerController(
            self.controller,
            self.config
        )

        logger.debug("PositionManagerController criado")
        return pos_controller
