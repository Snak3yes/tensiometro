# Exporta as classes principais para facilitar importação
from .aoi_controller import CNCAOIController
from .plc_axis_controller import PLCAxisController
from .camera_controller import CameraController
from .position_manager import InspectionPosition, InspectionSequence
from .stencil_tracker import (
    StencilTracker, Stencil, TensionRecord, InspectionRecord, TrendAnalysis
)
from .stencil_database import StencilDatabase, migrate_json_to_sqlite

__version__ = '0.4.0'  # Versão atualizada - SQLite + histórico de inspeção visual