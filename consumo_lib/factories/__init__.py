"""
Factories - Criação de Componentes

Este pacote contém factories para criar objetos de forma desacoplada.

Objetivos:
- Factory Pattern para criação de objetos
- Baixo acoplamento entre componentes
- Testabilidade via injeção de dependências
"""

from consumo_lib.factories.tab_factory import TabFactory
from consumo_lib.factories.controller_factory import ControllerFactory
from consumo_lib.factories.hardware_factory import HardwareFactory

__all__ = [
    'TabFactory',
    'ControllerFactory',
    'HardwareFactory',
]
