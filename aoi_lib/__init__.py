# Exporta as classes principais para facilitar importação
from .aoi_controller import CNCAOIController
from .plc_axis_controller import PLCAxisController
from .camera_controller import CameraController
from .position_manager import InspectionPosition, InspectionSequence
from .stencil_tracker import (
    StencilTracker, Stencil, TensionRecord, TrendAnalysis
)
from .stencil_database import StencilDatabase, migrate_json_to_sqlite
from .audit_log import AuditLog, get_audit_log, AuditEntry

__version__ = '0.4.0'
