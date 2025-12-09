# Exporta as classes principais para facilitar importação
from .aoi_controller import CNCAOIController
from .plc_axis_controller import PLCAxisController
from .camera_controller import CameraController
from .position_manager import InspectionPosition, InspectionSequence

__version__ = '0.2.0'  # Versão atualizada - apenas CLP (removido GRBL/Arduino)