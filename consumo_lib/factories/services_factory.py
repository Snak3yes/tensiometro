# -*- coding: utf-8 -*-
"""
services_factory.py
------------------
Factory para criar todos os services da aplicação.

Responsabilidade: Criar 2 services (SequenceExecution, ResourceManager).

Autor: Sistema AOI Tensiometro
Data: 2026-01-16 (SOLID Refactoring Phase 2)
"""

import logging
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from aoi_lib import CNCAOIController
    from PyQt6.QtWidgets import QWidget

logger = logging.getLogger(__name__)


class ServicesFactory:
    """
    Factory para criar todos os services da aplicação.

    Responsabilidade:
    - Criar SequenceExecutionService (gerencia execução de sequências)
    - Criar ResourceManager (gerencia recursos da aplicação)

    Methods:
    - create_all_services(): Cria todos os 2 services
    """

    def create_all_services(
        self,
        window: 'QWidget',
        controller: 'CNCAOIController'
    ) -> Dict[str, Any]:
        """
        Cria todos os services da aplicação.

        Args:
            window: Instância da janela principal
            controller: Instância de CNCAOIController

        Returns:
            Dict com todos os services criados
        """
        from consumo_lib.services import SequenceExecutionService, ResourceManager

        services = {}

        # 1. Sequence Execution Service
        try:
            services['sequence_execution_service'] = SequenceExecutionService(
                controller,
                window
            )
            logger.debug("SequenceExecutionService criado via ServicesFactory")

            # Connect signals from SequenceExecutionService
            if services['sequence_execution_service'] is not None:
                services['sequence_execution_service'].image_captured.connect(
                    window.on_sequence_image_captured
                )
                services['sequence_execution_service'].sequence_completed.connect(
                    window.on_sequence_completed
                )
                services['sequence_execution_service'].sequence_error.connect(
                    window.on_sequence_error
                )
                logger.debug("Signals de SequenceExecutionService conectados via ServicesFactory")
        except Exception as e:
            logger.error(f"Erro ao criar SequenceExecutionService via ServicesFactory: {e}")
            services['sequence_execution_service'] = None

        # 2. Resource Manager
        try:
            services['resource_manager'] = ResourceManager(controller)
            logger.debug("ResourceManager criado via ServicesFactory")
        except Exception as e:
            logger.error(f"Erro ao criar ResourceManager via ServicesFactory: {e}")
            services['resource_manager'] = None

        logger.info("Todos os 2 services criados via ServicesFactory")

        return services
