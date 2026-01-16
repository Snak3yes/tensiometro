"""
PLC Controllers - Implementações de interfaces para controle de hardware

Este pacote contém controllers especializados que implementam as interfaces PLC.
Cada controller foca em uma responsabilidade específica.

Objetivos:
- Interface Segregation Principle (ISP) - cada controller com 3-15 métodos
- Single Responsibility Principle (SRP) - cada controller com uma responsabilidade única
- Testabilidade - 100% testável sem PyQt6
- Baixo acoplamento - controllers podem ter mocks para testes

Autor: Fase 5 do SOLID Refactoring Phase 2
"""

from aoi_lib.plc.controllers.plc_connection_manager import PLCConnectionManager
from aoi_lib.plc.controllers.plc_absolute_movement_controller import PLCAbsoluteMovementController
from aoi_lib.plc.controllers.plc_relative_movement_controller import PLCRelativeMovementController
from aoi_lib.plc.controllers.plc_jog_movement_controller import PLCJogMovementController
from aoi_lib.plc.controllers.plc_homing_controller import PLCHomingController
from aoi_lib.plc.controllers.plc_position_reader_controller import PLCPositionReaderController
from aoi_lib.plc.controllers.plc_registers_controller import PLCRegistersController

__all__ = [
    'PLCConnectionManager',
    'PLCAbsoluteMovementController',
    'PLCRelativeMovementController',
    'PLCJogMovementController',
    'PLCHomingController',
    'PLCPositionReaderController',
    'PLCRegistersController',
]
