# -*- coding: utf-8 -*-
"""
coordinators_factory.py
-----------------------
Factory para criar todos os coordinators da aplicação.

Responsabilidade: Criar 4 coordinators (Connection, Inspection, Tension,
OperatorInspection).

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
    - Criar InspectionCoordinator (gerencia inspeção visual)
    - Criar TensionCoordinator (gerencia medição de tensão)
    - Criar OperatorInspectionCoordinator (gerencia workflow de operador)

    Methods:
    - create_all_coordinators(): Cria todos os 4 coordinators
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
            InspectionCoordinator,
            TensionCoordinator,
            OperatorInspectionCoordinator,
        )

        coordinators = {}

        # 1. Connection Coordinator (gerencia estados de conexão)
        coordinators['connection_coordinator'] = ConnectionCoordinator(
            controller,
            config
        )
        logger.debug("ConnectionCoordinator criado via CoordinatorsFactory")

        # 2. Inspection Coordinator
        # Nota: inspection_manager está em managers
        coordinators['inspection_coordinator'] = InspectionCoordinator(
            controller,
            config,
            managers['inspection_manager']
        )
        logger.debug("InspectionCoordinator criado via CoordinatorsFactory")

        # 3. Tension Coordinator
        coordinators['tension_coordinator'] = TensionCoordinator(
            controller,
            config
        )
        logger.debug("TensionCoordinator criado via CoordinatorsFactory")

        # 4. Operator Inspection Coordinator (NOVO - Operator Workflow Fase 2)
        # Nota: role_manager e session_logger estão em managers
        coordinators['operator_inspection_coordinator'] = OperatorInspectionCoordinator(
            inspection_coordinator=coordinators['inspection_coordinator'],
            role_manager=managers['role_manager'],
            session_logger=managers['session_logger']
        )
        logger.debug("OperatorInspectionCoordinator criado via CoordinatorsFactory")

        logger.info("Todos os 4 coordinators criados via CoordinatorsFactory")

        return coordinators
