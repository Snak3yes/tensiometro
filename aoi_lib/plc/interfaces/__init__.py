"""
PLC Interfaces - Contratos para baixo acoplamento de hardware

Este pacote contém interfaces ABC (Abstract Base Classes) que definem
contratos para diferentes componentes de controle PLC.

Objetivos:
- Interface Segregation Principle (ISP)
- Baixo acoplamento entre componentes
- Testabilidade via mocks
"""

from aoi_lib.plc.interfaces.plc_connection_interface import IPLCConnection
from aoi_lib.plc.interfaces.plc_absolute_movement_interface import IPLCAbsoluteMovement
from aoi_lib.plc.interfaces.plc_relative_movement_interface import PLCRelativeMovement
from aoi_lib.plc.interfaces.plc_jog_movement_interface import PLCJogMovement
from aoi_lib.plc.interfaces.plc_homing_interface import IPLCHoming

__all__ = [
    'IPLCConnection',
    'IPLCAbsoluteMovement',
    'PLCRelativeMovement',
    'PLCJogMovement',
    'IPLCHoming',
]
