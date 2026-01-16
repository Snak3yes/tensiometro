"""
PLC Package - Controle de hardware PLC via Modbus TCP

Este pacote contém:
- Interfaces ABC para controle PLC (Interface Segregation Principle)
- Controllers especializados implementando as interfaces
- Adapter para backward compatibility com código legado

Arquitetura:
- 7 interfaces ABC (<15 métodos cada)
- 7 controllers especializados (3-8 métodos cada)
- 1 adapter mantém compatibilidade 100% com código existente

Autor: Fase 5 do SOLID Refactoring Phase 2
"""

# Interfaces ABC
from aoi_lib.plc.interfaces.plc_connection_interface import IPLCConnection
from aoi_lib.plc.interfaces.plc_absolute_movement_interface import IPLCAbsoluteMovement
from aoi_lib.plc.interfaces.plc_relative_movement_interface import PLCRelativeMovement
from aoi_lib.plc.interfaces.plc_jog_movement_interface import PLCJogMovement
from aoi_lib.plc.interfaces.plc_homing_interface import IPLCHoming
from aoi_lib.plc.interfaces.plc_position_reader_interface import IPLCPositionReader
from aoi_lib.plc.interfaces.plc_register_interface import IPLCRegisterOperations

# Controllers especializados
from aoi_lib.plc.controllers.plc_connection_manager import PLCConnectionManager
from aoi_lib.plc.controllers.plc_absolute_movement_controller import PLCAbsoluteMovementController
from aoi_lib.plc.controllers.plc_relative_movement_controller import PLCRelativeMovementController
from aoi_lib.plc.controllers.plc_jog_movement_controller import PLCJogMovementController
from aoi_lib.plc.controllers.plc_homing_controller import PLCHomingController
from aoi_lib.plc.controllers.plc_position_reader_controller import PLCPositionReaderController
from aoi_lib.plc.controllers.plc_registers_controller import PLCRegistersController

# Adapter para backward compatibility
from aoi_lib.plc.plc_axis_controller_adapter import PLCAxisControllerAdapter

__all__ = [
    # Interfaces
    'IPLCConnection',
    'IPLCAbsoluteMovement',
    'PLCRelativeMovement',
    'PLCJogMovement',
    'IPLCHoming',
    'IPLCPositionReader',
    'IPLCRegisterOperations',
    # Controllers
    'PLCConnectionManager',
    'PLCAbsoluteMovementController',
    'PLCRelativeMovementController',
    'PLCJogMovementController',
    'PLCHomingController',
    'PLCPositionReaderController',
    'PLCRegistersController',
    # Adapter
    'PLCAxisControllerAdapter',
]
