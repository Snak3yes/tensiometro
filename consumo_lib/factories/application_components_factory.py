# -*- coding: utf-8 -*-
"""
application_components_factory.py
---------------------------------
Facade principal que orquestra todas as factories para criar componentes.

Responsabilidade: Simplificar criação de todos os componentes da aplicação
orquestrando CoreFactory, ManagersFactory, CoordinatorsFactory, HandlersFactory,
ControllersFactory e ServicesFactory.

Autor: Sistema AOI Tensiometro
Data: 2026-01-16 (SOLID Refactoring Phase 2)
"""

import logging
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QWidget

logger = logging.getLogger(__name__)


class ApplicationComponentsFactory:
    """
    Facade principal que orquestra todas as factories.

    Responsabilidade:
    - Orquestrar criação de todos os componentes
    - Manter ordem crítica de criação (Core → Managers → Coordinators → Handlers → Controllers → Services)
    - Retornar dict unificado com todos os componentes

    Ordem de criação é CRÍTICA! Alguns componentes dependem de outros.
    """

    def __init__(self):
        """Inicializa a factory com as factories especializadas."""
        from consumo_lib.factories import (
            CoreFactory,
            ManagersFactory,
            CoordinatorsFactory,
            HandlersFactory,
            ControllersFactory,
            ServicesFactory,
        )

        self.core_factory = CoreFactory()
        self.managers_factory = ManagersFactory()
        self.coordinators_factory = CoordinatorsFactory()
        self.handlers_factory = HandlersFactory()
        self.controllers_factory = ControllersFactory()
        self.services_factory = ServicesFactory()

        logger.debug("ApplicationComponentsFactory inicializada com todas as factories")

    def create_all_components(self, window: 'QWidget') -> Dict[str, Any]:
        """
        Cria todos os componentes da aplicação.

        Ordem de criação é CRÍTICA:
        1. Core (config, controller)
        2. Managers (dependem de Core)
        3. Coordinators (dependem de Managers)
        4. Handlers (dependem de Window)
        5. Controllers (dependem de Core, Managers, Window)
        6. Services (dependem de Core, Window)

        Args:
            window: Instância da janela principal (AOIControllerApp)

        Returns:
            Dict unificado com todos os componentes organizados por categoria
        """
        logger.info("🏭 ApplicationComponentsFactory: Iniciando criação de todos os componentes...")

        components = {}

        # 1. Core (config, controller) - CRÍTICO: Copiar para window IMEDIATAMENTE
        logger.info("1️⃣ Criando componentes core...")
        core_components = self.core_factory.create_all()
        components['core'] = core_components
        # COPIAR PARA WINDOW IMEDIATAMENTE para que handlers possam acessar controller
        self._copy_to_window(window, core_components)
        logger.info("✅ Core criado e copiado para window: config, controller")

        # 2. Managers (dependem de core)
        logger.info("2️⃣ Criando managers...")
        managers = self.managers_factory.create_all_managers(
            window,
            core_components['config'],
            core_components['controller']
        )
        components['managers'] = managers
        # COPIAR PARA WINDOW IMEDIATAMENTE
        self._copy_to_window(window, managers)
        logger.info(f"✅ Managers criados e copiados para window: {len(managers)} componentes")

        # 3. Coordinators (dependem de managers)
        logger.info("3️⃣ Criando coordinators...")
        coordinators = self.coordinators_factory.create_all_coordinators(
            window,
            core_components['config'],
            core_components['controller'],
            managers
        )
        components['coordinators'] = coordinators
        # COPIAR PARA WINDOW IMEDIATAMENTE
        self._copy_to_window(window, coordinators)
        logger.info(f"✅ Coordinators criados e copiados para window: {len(coordinators)} componentes")

        # 4. Handlers (dependem de window) - agora pode acessar window.controller
        logger.info("4️⃣ Criando handlers...")
        handlers = self.handlers_factory.create_all_handlers(window)
        components['handlers'] = handlers
        # COPIAR PARA WINDOW IMEDIATAMENTE
        self._copy_to_window(window, handlers)
        logger.info(f"✅ Handlers criados e copiados para window: {len(handlers)} componentes")

        # 5. Controllers (dependem de core, managers, window)
        logger.info("5️⃣ Criando controllers independentes de UI...")
        controllers = self.controllers_factory.create_all_controllers(
            window,
            core_components['config'],
            core_components['controller'],
            managers
        )
        components['controllers'] = controllers
        # COPIAR PARA WINDOW IMEDIATAMENTE
        self._copy_to_window(window, controllers)
        logger.info(f"✅ Controllers criados e copiados para window: {len(controllers)} componentes")

        # 6. Services (dependem de core, window)
        logger.info("6️⃣ Criando services...")
        services = self.services_factory.create_all_services(
            window,
            core_components['controller']
        )
        components['services'] = services
        # COPIAR PARA WINDOW IMEDIATAMENTE
        self._copy_to_window(window, services)
        logger.info(f"✅ Services criados e copiados para window: {len(services)} componentes")

        logger.info("🎉 ApplicationComponentsFactory: Todos os componentes criados e copiados para window!")

        return components

    def _copy_to_window(self, window: 'QWidget', components: Dict[str, Any]):
        """
        Copia componentes para a window usando setattr().

        Args:
            window: Instância da janela principal
            components: Dict com componentes a serem copiados
        """
        for key, value in components.items():
            setattr(window, key, value)

    def create_dependent_controllers(
        self,
        window: 'QWidget'
    ) -> Dict[str, Any]:
        """
        Cria controllers que dependem de UI (FileIO, PositionManager).

        NOTA: Este método deve ser chamado APÓS setup_ui() em SetupCoordinator,
        pois estes controllers dependem de widgets da interface.

        Args:
            window: Instância da janela principal (UI já criada)

        Returns:
            Dict com controllers dependentes de UI
        """
        logger.info("🔧 Criando controllers dependentes de UI (FileIO, PositionManager)...")

        # Usa core controller já criado
        controller = window.controller

        dependent_controllers = self.controllers_factory.create_controllers_dependent_on_ui(
            window,
            controller
        )

        logger.info(f"✅ Controllers dependentes de UI criados: {len(dependent_controllers)} componentes")

        return dependent_controllers
