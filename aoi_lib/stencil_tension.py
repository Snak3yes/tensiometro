"""
Compatibility Module for Legacy stencil_tension.py Imports

⚠️  DEPRECATED ⚠️
This module is maintained ONLY for backward compatibility.
All functionality has been refactored into aoi_lib/tensiometer/ package.

Refactoring Date: 2026-01-14
Track: solid_refactoring_phase1_20260114

Migration Path:
  OLD: from aoi_lib.stencil_tension import StencilTensionDialog
  NEW: from consumo_lib.dialogs.tension import TensionMeasurementDialog

For new code, use the refactored modules:
  from aoi_lib.tensiometer import (
      TensiometerSerialManager,
      MeasurementOrchestrator,
      GridCalculationService,
      MeasurementAnalysisService
  )
  from consumo_lib.dialogs.tension import TensionMeasurementDialog
"""

import warnings
import sys
import logging
from pathlib import Path

# Show deprecation warning on module import
warnings.warn(
    "O módulo 'aoi_lib.stencil_tension' está OBSOLETO e será removido em versão futura.\n"
    "Use 'from aoi_lib.tensiometer import ...' para lógica de negócio.\n"
    "Use 'from consumo_lib.dialogs.tension import TensionMeasurementDialog' para UI.\n"
    "Track: solid_refactoring_phase1_20260114 - Phase 1",
    DeprecationWarning,
    stacklevel=2
)

logger = logging.getLogger(__name__)
logger.info("Using deprecated aoi_lib.stencil_tension module - "
           "please migrate to aoi_lib.tensiometer and consumo_lib.dialogs.tension")

# ============================================================================
# REFLECTED IMPORTS - Re-export from new locations
# ============================================================================

# Core business logic (from aoi_lib.tensiometer)
from aoi_lib.tensiometer import (
    # Models
    GridPoint,
    TensionMeasurement,
    GridParameters,
    MeasurementSession,
    TensiometerConfig,
    TensionUnit,

    # Serial communication
    TensiometerSerialManager,

    # Thread
    TensionMeasurementThread,

    # Services
    GridCalculationService,
    MeasurementAnalysisService,
    ValidationError,

    # Orchestrator
    MeasurementOrchestrator
)

# Dialog (from consumo_lib.dialogs.tension)
try:
    from consumo_lib.dialogs.tension import TensionMeasurementDialog

    # Create alias for backward compatibility
    StencilTensionDialog = TensionMeasurementDialog

    # Show specific warning for dialog usage
    _original_import = StencilTensionDialog.__init__

    def _deprecated_init(self, *args, **kwargs):
        warnings.warn(
            "StencilTensionDialog está obsoleto. "
            "Use 'from consumo_lib.dialogs.tension import TensionMeasurementDialog' "
            "para evitar warnings no futuro.",
            DeprecationWarning,
            stacklevel=2
        )
        return _original_import(self, *args, **kwargs)

    # Monkey-patch to show warning on instantiation
    StencilTensionDialog.__init__ = _deprecated_init

except ImportError as e:
    # Fallback if new module not found
    logger.warning(f"Could not import refactored dialog: {e}")
    StencilTensionDialog = None


# ============================================================================
# BACKWARD COMPATIBILITY ALIASES
# ============================================================================

# Aliases for old class names (if they differ)
# Currently: StencilTensionDialog → TensionMeasurementDialog
# No aliases needed as we're using the same name

# Legacy Tkinter class (kept for extreme backward compatibility)
# Note: This is NOT recommended for new code
try:
    from tkinter import Toplevel, Label, Entry, Button, messagebox

    class StencilTensionMeasurement:
        """
        ⚠️  DEPRECATED - Legacy Tkinter-based measurement class.

        This class is maintained ONLY for extreme backward compatibility.
        It uses the old Tkinter UI which is not integrated with the main PyQt6 application.

        For new code, use TensionMeasurementDialog (PyQt6-based).
        """

        def __init__(self, master, serial_handler):
            warnings.warn(
                "StencilTensionMeasurement (Tkinter) está OBSOLETO.\n"
                "Use TensionMeasurementDialog (PyQt6) do pacote "
                "consumo_lib.dialogs.tension.",
                DeprecationWarning,
                stacklevel=2
            )
            self.master = master
            self.serial_handler = serial_handler
            self.window = None

        def show_window(self):
            """Show legacy Tkinter window (NOT RECOMMENDED)."""
            warnings.warn(
                "Usando interface Tkinter legada. "
                "Migre para TensionMeasurementDialog (PyQt6).",
                DeprecationWarning,
                stacklevel=2
            )
            # Would implement old Tkinter UI here if absolutely needed
            # For now, raise error to force migration
            raise NotImplementedError(
                "Interface Tkinter legada não está mais disponível.\n"
                "Por favor, migre para TensionMeasurementDialog (PyQt6)\n"
                "em consumo_lib.dialogs.tension."
            )

        def calculate_grid_points(self):
            """Not implemented - use GridCalculationService instead."""
            raise NotImplementedError(
                "calculate_grid_points() movido para GridCalculationService.\n"
                "Use: from aoi_lib.tensiometer import GridCalculationService"
            )

        def start_measurement(self):
            """Not implemented - use MeasurementOrchestrator instead."""
            raise NotImplementedError(
                "start_measurement() movido para MeasurementOrchestrator.\n"
                "Use: from aoi_lib.tensiometer import MeasurementOrchestrator"
            )

        def read_tensiometer_value(self):
            """Not implemented - use TensiometerSerialManager instead."""
            raise NotImplementedError(
                "read_tensiometer_value() movido para TensiometerSerialManager.\n"
                "Use: from aoi_lib.tensiometer import TensiometerSerialManager"
            )

        def save_json(self, measurements):
            """Not implemented - use MeasurementOrchestrator.save_results() instead."""
            raise NotImplementedError(
                "save_json() movido para MeasurementOrchestrator.save_results().\n"
                "Use: from aoi_lib.tensiometer import MeasurementOrchestrator"
            )

except ImportError:
    # Tkinter not available on all systems
    StencilTensionMeasurement = None


# ============================================================================
# CONSTANTS
# ============================================================================

# Legacy constant for routines folder location
ROUTINES_FOLDER = Path(__file__).parent.parent / "tension_routines"
# Ensure directory exists
ROUTINES_FOLDER.mkdir(parents=True, exist_ok=True)


# ============================================================================
# PUBLIC API (Re-exports)
# ============================================================================

__all__ = [
    # Core Classes (with deprecation warnings)
    'TensiometerSerialManager',
    'TensionMeasurementThread',
    'StencilTensionDialog',  # Alias to TensionMeasurementDialog
    'MeasurementOrchestrator',
    'GridCalculationService',
    'MeasurementAnalysisService',

    # Data Models
    'GridPoint',
    'TensionMeasurement',
    'GridParameters',
    'MeasurementSession',
    'TensiometerConfig',
    'TensionUnit',

    # Exceptions
    'ValidationError',

    # Legacy (NOT RECOMMENDED)
    'StencilTensionMeasurement',  # Tkinter version

    # Constants
    'ROUTINES_FOLDER',
]


# ============================================================================
# MODULE DOCSTRING UPDATE
# ============================================================================

__doc__ += """


MIGRATION GUIDE
===============

This module has been REFACTORED. Here's how to migrate your code:

1. IMPORTING THE DIALOG:
   OLD: from aoi_lib.stencil_tension import StencilTensionDialog
   NEW: from consumo_lib.dialogs.tension import TensionMeasurementDialog

2. USING BUSINESS LOGIC:
   OLD: from aoi_lib.stencil_tension import TensiometerSerialManager
   NEW: from aoi_lib.tensiometer import TensiometerSerialManager

3. CALCULATING GRID:
   OLD: from aoi_lib.stencil_tension import StencilTensionMeasurement
        measurement.calculate_grid_points()
   NEW: from aoi_lib.tensiometer import GridCalculationService, GridParameters
        params = GridParameters(start_point=(0,0), end_point=(100,100), grid_size=3, z_height=5.0)
        points = GridCalculationService.calculate_grid_points(params)

4. COORDINATING MEASUREMENT:
   OLD: Manual thread management and signal handling
   NEW: from aoi_lib.tensiometer import MeasurementOrchestrator
        orchestrator = MeasurementOrchestrator(cnc, tensiometer)
        result = orchestrator.prepare_measurement(...)
        orchestrator.start_measurement(points, on_progress=..., on_complete=...)

5. ANALYZING RESULTS:
   OLD: Manual calculation
   NEW: from aoi_lib.tensiometer import MeasurementAnalysisService
        analysis = MeasurementAnalysisService.analyze_session(session)

BENEFITS OF REFACTORING:
  ✅ Better separation of concerns (UI vs Business Logic)
  ✅ Improved testability (service layer 100% testable without PyQt6)
  ✅ Type hints throughout (better IDE support)
  ✅遵循 SOLID principles (Single Responsibility, etc.)
  ✅ Reduced complexity (962-line dialog → 482 lines)
  ✅ Cleaner architecture (6 focused modules instead of 1 monolithic file)

For detailed migration examples, see the track documentation:
  conductor/tracks/solid_refactoring_phase1_20260114/plan.md
"""
