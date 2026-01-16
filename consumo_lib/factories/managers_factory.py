# -*- coding: utf-8 -*-
"""
managers_factory.py
-------------------
Factory para criar todos os managers da aplicação.

Responsabilidade: Criar 11 managers (Connection, Role, Session, Recipe, Stencil,
Report, Inspection e derivados).

Autor: Sistema AOI Tensiometro
Data: 2026-01-16 (SOLID Refactoring Phase 2)
"""

import logging
from pathlib import Path
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from aoi_lib.config_manager import AOIConfigManager
    from aoi_lib import CNCAOIController
    from PyQt6.QtWidgets import QWidget

logger = logging.getLogger(__name__)


class ManagersFactory:
    """
    Factory para criar todos os managers da aplicação.

    Responsabilidade:
    - Criar ConnectionManager (gerencia PLC, GRBL, serial ports)
    - Criar RoleManager (gerencia roles de usuários)
    - Criar SessionLogger (gerencia logs de sessão)
    - Criar RecipeManagerWrapper e RecipeManager
    - Criar StencilManagerWrapper e StencilTracker
    - Criar ReportManagerWrapper e derivados
    - Criar InspectionManager e derivados

    Methods:
    - create_all_managers(): Cria todos os 11 managers
    """

    def create_all_managers(
        self,
        window: 'QWidget',
        config: 'AOIConfigManager',
        controller: 'CNCAOIController'
    ) -> Dict[str, Any]:
        """
        Cria todos os managers da aplicação.

        Ordem de criação é crítica! Alguns managers dependem de outros.

        Args:
            window: Instância da janela principal
            config: Instância de AOIConfigManager
            controller: Instância de CNCAOIController

        Returns:
            Dict com todos os managers criados
        """
        from consumo_lib.managers import (
            ConnectionManager,
            RoleManager,
            SessionLogger,
            RecipeManagerWrapper,
            StencilManagerWrapper,
            ReportManagerWrapper,
            InspectionManager,
        )

        managers = {}

        # 1. Estado interno
        managers['current_sequence'] = None
        managers['is_running_sequence'] = False

        # 2. Role Manager (NOVO - Operator Workflow Fase 2)
        managers['role_manager'] = RoleManager()
        logger.debug("RoleManager criado via ManagersFactory")

        # 3. Session Logger (NOVO - Operator Workflow Fase 2)
        log_dir = Path(config.cfg_path).parent / "data" / "sessions"
        managers['session_logger'] = SessionLogger(log_dir=str(log_dir))
        logger.debug(f"SessionLogger criado via ManagersFactory com log_dir={log_dir}")

        # 4. Connection Manager (gerencia PLC, GRBL, serial ports)
        managers['connection_mgr'] = ConnectionManager(
            controller,
            config
        )
        logger.debug("ConnectionManager criado via ManagersFactory")

        # 5. Recipe Manager
        managers['recipe_manager_wrapper'] = RecipeManagerWrapper(parent=window)
        managers['recipe_manager'] = managers['recipe_manager_wrapper'].recipe_manager
        managers['current_recipe'] = None
        logger.debug("RecipeManagerWrapper e RecipeManager criados via ManagersFactory")

        # 6. RecipeManagerController (depende de recipe_manager)
        from consumo_lib.controllers import RecipeManagerController
        try:
            managers['recipe_manager_controller'] = RecipeManagerController(
                managers['recipe_manager'],
                managers['recipe_manager_wrapper'],
                window
            )
            # Configura handlers de UI no próprio controller
            managers['recipe_manager_controller'].setup_ui_handlers()
            logger.debug("RecipeManagerController criado via ManagersFactory")
        except Exception as e:
            logger.error(f"Erro ao criar RecipeManagerController via ManagersFactory: {e}")
            managers['recipe_manager_controller'] = None

        # 7. Stencil Manager
        managers['stencil_manager_wrapper'] = StencilManagerWrapper(parent=window)
        managers['stencil_tracker'] = managers['stencil_manager_wrapper'].stencil_tracker
        managers['current_stencil'] = None
        logger.debug("StencilManagerWrapper e StencilTracker criados via ManagersFactory")

        # Configura handlers de UI do StencilManagerWrapper
        managers['stencil_manager_wrapper'].setup_ui_handlers(window)
        logger.debug("StencilManagerWrapper UI handlers configurados via ManagersFactory")

        # 8. Report Manager
        managers['report_manager_wrapper'] = ReportManagerWrapper(
            config,
            parent=window
        )
        managers['report_config'] = managers['report_manager_wrapper'].get_config()
        managers['report_generator'] = managers['report_manager_wrapper'].get_generator()
        logger.debug("ReportManagerWrapper criado via ManagersFactory")

        # 9. Inspection Manager
        managers['inspection_manager'] = InspectionManager(
            config,
            parent=window
        )
        managers['inspection_thresholds'] = managers['inspection_manager'].get_thresholds()
        managers['stencil_inspector'] = managers['inspection_manager'].get_inspector()
        managers['_last_inspection_result'] = None
        managers['_last_inspection_overlay'] = None
        logger.debug("InspectionManager criado via ManagersFactory")

        logger.info("Todos os 11 managers criados via ManagersFactory")

        return managers
