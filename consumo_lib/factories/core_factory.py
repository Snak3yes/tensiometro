# -*- coding: utf-8 -*-
"""
core_factory.py
---------------
Factory para criar componentes core da aplicação.

Responsabilidade: Criar config (AOIConfigManager) e controller (CNCAOIController).

Autor: Sistema AOI Tensiometro
Data: 2026-01-16 (SOLID Refactoring Phase 2)
"""

import logging
from typing import Dict, Any
from aoi_lib.config_manager import AOIConfigManager
from aoi_lib import CNCAOIController

logger = logging.getLogger(__name__)


class CoreFactory:
    """
    Factory para criar componentes core da aplicação.

    Responsabilidade:
    - Criar AOIConfigManager (gerenciador de configurações)
    - Criar CNCAOIController (controller CNC principal)

    Methods:
    - create_config(): Cria AOIConfigManager
    - create_controller(config): Cria CNCAOIController
    - create_all(): Cria ambos e retorna dict
    """

    def create_config(self) -> AOIConfigManager:
        """
        Cria o gerenciador de configurações.

        Returns:
            AOIConfigManager: Instância configurada
        """
        config = AOIConfigManager()
        logger.debug("AOIConfigManager criado via CoreFactory")
        return config

    def create_controller(self, config: AOIConfigManager) -> CNCAOIController:
        """
        Cria o controller CNC principal.

        Args:
            config: Instância de AOIConfigManager

        Returns:
            CNCAOIController: Instância configurada
        """
        plc_host = config.get("connections", "plc_host", default="192.168.1.5")
        plc_port = config.get("connections", "plc_port", default=502)

        controller = CNCAOIController(
            plc_host=plc_host,
            plc_port=plc_port,
            auto_connect=False
        )

        logger.debug(
            "CNCAOIController criado via CoreFactory; backend = %s",
            type(controller.cnc).__name__
        )

        return controller

    def create_all(self) -> Dict[str, Any]:
        """
        Cria todos os componentes core.

        Returns:
            Dict com 'config' e 'controller'
        """
        config = self.create_config()
        controller = self.create_controller(config)

        return {
            'config': config,
            'controller': controller,
        }
