"""
Factories - Criação de Componentes

Este pacote contém factories para criar objetos de forma desacoplada.

Objetivos:
- Factory Pattern para criação de objetos
- Baixo acoplamento entre componentes
- Testabilidade via injeção de dependências

Factories da Fase 4 (UI Components):
- TabFactory: Cria abas da aplicação
- ControllerFactory: Cria controllers de hardware
- HardwareFactory: Cria componentes de hardware

Factories da Fase 8 (Application Components):
- CoreFactory: Cria config e controller
- ManagersFactory: Cria todos os managers
- CoordinatorsFactory: Cria todos os coordinators
- HandlersFactory: Cria todos os handlers
- ControllersFactory: Cria todos os controllers
- ServicesFactory: Cria todos os services
- ApplicationComponentsFactory: Facade que orquestra todas as factories
"""

# Factories da Fase 4
from consumo_lib.factories.tab_factory import TabFactory
from consumo_lib.factories.controller_factory import ControllerFactory
from consumo_lib.factories.hardware_factory import HardwareFactory

# Factories da Fase 8 (SOLID Refactoring Phase 2)
from consumo_lib.factories.core_factory import CoreFactory
from consumo_lib.factories.managers_factory import ManagersFactory
from consumo_lib.factories.coordinators_factory import CoordinatorsFactory
from consumo_lib.factories.handlers_factory import HandlersFactory
from consumo_lib.factories.controllers_factory import ControllersFactory
from consumo_lib.factories.services_factory import ServicesFactory
from consumo_lib.factories.application_components_factory import ApplicationComponentsFactory

__all__ = [
    # Fase 4
    'TabFactory',
    'ControllerFactory',
    'HardwareFactory',
    # Fase 8
    'CoreFactory',
    'ManagersFactory',
    'CoordinatorsFactory',
    'HandlersFactory',
    'ControllersFactory',
    'ServicesFactory',
    'ApplicationComponentsFactory',
]
