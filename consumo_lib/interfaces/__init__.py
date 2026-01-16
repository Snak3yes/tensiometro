"""
Interfaces - Contratos para baixo acoplamento

Este pacote contém interfaces ABC (Abstract Base Classes) que definem
contratos para diferentes componentes da aplicação.

Objetivos:
- Interface Segregation Principle (ISP)
- Baixo acoplamento entre módulos
- Testabilidade via mocks
"""

from consumo_lib.interfaces.tab_manager import ITabManager
from consumo_lib.interfaces.menu_manager import IMenuManager
from consumo_lib.interfaces.hardware_manager import IHardwareManager
from consumo_lib.interfaces.dialog_manager import IDialogManager

__all__ = [
    'ITabManager',
    'IMenuManager',
    'IHardwareManager',
    'IDialogManager',
]
