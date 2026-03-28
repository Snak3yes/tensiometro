# -*- coding: utf-8 -*-
"""
coordinators_factory.py
-----------------------
Factory para criar todos os coordinators da aplicação.

Responsabilidade: Criar coordinators ativos da aplicação.

Autor: Sistema AOI Tensiometro
Data: 2026-01-16 (SOLID Refactoring Phase 2)
"""

import logging
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from aoi_lib.config_manager import AOIConfigManager
    from aoi_lib import CNCAOIController
    from PyQt6.QtWidgets import QWidget

logger = logging.getLogger(__name__)


class CoordinatorsFactory:
    """
    Factory para criar todos os coordinators da aplicação.

    Responsabilidade:
    - Criar ConnectionCoordinator (gerencia estados de conexão)
    - Criar TensionCoordinator (gerencia medição de tensão)

    Methods:
    - create_all_coordinators(): Cria todos os coordinators ativos
    """

    def create_all_coordinators(
        self,
        window: 'QWidget',
        config: 'AOIConfigManager',
        controller: 'CNCAOIController',
        managers: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Cria todos os coordinators da aplicação.

        Args:
            window: Instância da janela principal
            config: Instância de AOIConfigManager
            controller: Instância de CNCAOIController
            managers: Dict com todos os managers (de ManagersFactory)

        Returns:
            Dict com todos os coordinators criados
        """
        from consumo_lib.coordinators import (
            ConnectionCoordinator,
            TensionCoordinator,
        )

        coordinators = {}

        # 1. Connection Coordinator (gerencia estados de conexão)
        coordinators['connection_coordinator'] = ConnectionCoordinator(
            controller,
            config
        )
        logger.debug("ConnectionCoordinator criado via CoordinatorsFactory")

        # 2. Tension Coordinator
        coordinators['tension_coordinator'] = TensionCoordinator(
            controller,
            config
        )
        logger.debug("TensionCoordinator criado via CoordinatorsFactory")

        logger.info("Todos os coordinators ativos criados via CoordinatorsFactory")

        return coordinators
