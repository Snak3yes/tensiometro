# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Project Organization:** This project follows [PROJECT_ORGANIZATION_GUIDELINES.md](PROJECT_ORGANIZATION_GUIDELINES.md) for maintaining a clean, professional structure.

## Project Overview

**Tensiometro** is an industrial Automated Optical Inspection (AOI) system for solder stencil quality control in SMT manufacturing. The system performs:
- Surface tension measurement using AS-120N tensiometer (serial RS-232)
- Visual inspection of stencil openings for cleanliness validation
- CNC movement control via Delta PLC (Modbus TCP)
- Individual stencil traceability with historical trend analysis
- PDF report generation

**Development Status:** ~99% complete - in practical validation phase with hardware

**Version:** 0.4.0 (see aoi_lib/__init__.py)

**Code Statistics (2026-01-14):**
- Total Python files: 245 (excluindo .conda/, archive/, poc_gerber/)
- Total lines of code: ~59,516
- aoi_lib: 59 files, ~21,627 lines (core business logic)
- consumo_lib: 125 files, ~37,889 lines (modular GUI)
- tests: 48 unit tests (test_tensiometer_services.py)

**Recent Changes (2025-12-12):**
- Simplified FOV calibration for fixed camera (removed dual-Z-height logic)
- Fixed Y-axis movement inversion bug (click-to-move now works correctly)
- Added crosshair customization dialog
- Fixed FOV calibration save bug (ConfigAdapter keyword argument)

**Latest Updates (2026-01-08):**
- **Project Organization:** Adopted PROJECT_ORGANIZATION_GUIDELINES.md standards
- **Clean Root:** Reduced root .md files from 7 to 3 (README.md, CLAUDE.md, PROJECT_ORGANIZATION_GUIDELINES.md)
- **Documentation Structure:** Organized docs/ with subdirectories (guides/, architecture/, meetings/, reports/)
- **Test Scripts Reorganized:** Moved run_tests.bat to tests/scripts/, created wrappers in root
- **Project Reorganization (2026-01-07):** Restructured project root, moved documentation to `docs/`, archived test files to `archive/`
- **Modular Refactoring:** `consumo_lib.py` refactored from 6,245 to 1,060 lines as modular package structure (88 files)
- **POC Gerber:** Renamed `testes_gerber/` → `poc_gerber/` (Proof of Concept Gerber viewer)
- **Auto-Connect PLC:** Enabled `auto_connect_plc: true` in `config/aoi_config.json` for automatic PLC connection on startup
- **Bug Fixes (2026-01-07):**
  - Fixed import path from `testes_gerber` to `poc_gerber` in `aoi_lib/gerber_parser.py`
  - Fixed `log` undefined error in `fiducial_alignment_widget.py`
  - Fixed duplicate movement bug in POC Gerber viewer `_move_objects()` method
  - Corrected obround geometry implementation (rectangle + semi-circles per Gerber spec)
  - Added robust validation to Gerber parser functions
  - Fixed Modbus interpolation addressing (X/Y use shared coil M1050)
  - Added extensive logging to PLC movement and wait_for_idle
- **Recent UI Updates (2026-01-08):**
  - Fixed CNC status label reference
  - Removed "Posição Atual" groupbox from left panel
  - Added CNC status display to MovementControlWidget
  - Added position display inside Movement Controls groupbox
  - Fixed AboutDialog and updated "About" text
- **Branch Strategy:** Migrated from `master` to `main` as primary branch
- **SSH Configuration:** SSH keys properly configured for passwordless Git operations
- **Repository Size:** Currently ~2.0 GB (needs cleanup of large .rar files from history)

**New Features (2026-01-13):**
- **Operator Workflow:** Guided inspection workflow with role-based access control
  - Login system with user authentication (RoleManager)
  - Step-by-step inspection process with progress tracking
  - Defect judgment dialogs with image annotation
  - Session logging for traceability (SessionLogger)
- **Services Layer:** Introduced `consumo_lib/services/` for business logic separation
  - `MovementService`: Centralized movement control logic
  - `ClickToMoveService`: Camera click-to-move functionality
  - `SequenceExecutionService`: Automated sequence execution
  - `ResourceManager`: Hardware resource lifecycle management
- **Enhanced UI Components:**
  - `OperatorInterface`: Dedicated operator workflow UI
  - `HardwareStatusBar`: Real-time hardware status display
  - `PositionList`: Position management widget
  - `SequenceControl`: Sequence execution controls
- **New Tabs:**
  - `TreeViewTab`: Hierarchical view of inspection data
  - Enhanced `MapTab`: Improved mosaic generation interface
- **Dialog System Expansion:**
  - `LoginDialog`: User authentication dialog
  - `ModeSelectionDialog`: Operation mode selection
  - `ConfirmPositioningDialog`: Position confirmation
  - `InspectionProgressDialog`: Progress tracking
  - `InspectionResultsDialog`: Results display
  - `DefectJudgmentDialog`: Defect classification
  - `FinalDecisionDialog`: Final approval/rejection
- **Data Management:**
  - `data/sessions/`: Session data storage
  - `data/users/`: User management data
- **Build Artifacts Cleanup:** Removed htmlcov/, .coverage, coverage.xml, .pytest_cache/ from Git tracking

**Latest Updates (2026-01-14):**
- **SOLID Refactoring Phase 1:** ✅ COMPLETE
  - Refatorado `stencil_tension.py` (1,409 → 5 módulos focados: 2,368 linhas)
  - Criado 48 unit tests (100% service layer coverage)
  - Dialog reduzido 50% (962 → 482 linhas)
  - Removido `SignalAggregator` (1,192 linhas obsoleto)
  - Zero breaking changes (backward compatibility maintained)
  - Tag: `solid_refactoring_phase1_20260114-complete`
  - Migration guide: `docs/guides/SOLID_PHASE1_MIGRATION_GUIDE.md`
  - SOLID analysis: `docs/reports/SOLID_ANALYSIS_REPORT.md`
- **Engineering Wizard:** ✅ 100% COMPLETE
  - Todas as 7 abas implementadas (~4,672 linhas)
  - 122 testes unitários
  - Integration complete (orchestrator, state management, hardware coordination)
- **Code Statistics Updated:**
  - Total: 245 Python files (132 → 245, +86%)
  - aoi_lib: 59 files, ~21,627 lines (44 → 59, +34%)
  - consumo_lib: 125 files, ~37,889 lines (88 → 125, +42%)

## Completed Tracks (Conductor System)

### ✅ SOLID Refactoring Phase 1 (2026-01-14)
- **Track ID:** solid_refactoring_phase1_20260114
- **Status:** Complete (archived)
- **Duration:** 2 days (80% faster than estimated 2 weeks)
- **Achievements:**
  - 5 módulos focados criados (2,368 linhas)
  - 48 unit tests (100% service layer coverage)
  - Dialog reduzido 50% (962 → 482 linhas)
  - Removido SignalAggregator (1,192 linhas)
  - Zero breaking changes (backward compatibility maintained)
- **Documentation:**
  - Migration Guide: `docs/guides/SOLID_PHASE1_MIGRATION_GUIDE.md` (521 linhas)
  - SOLID Analysis: `docs/reports/SOLID_ANALYSIS_REPORT.md`
  - Track Archive: `conductor/archive/solid_refactoring_phase1_20260114/`
- **Tag:** `solid_refactoring_phase1_20260114-complete`

### ✅ Engineering Wizard - All 7 Tabs (2026-01-13)
- **Track ID:** engenharia_abas_1-7
- **Status:** Complete (archived)
- **Duration:** ~3 weeks
- **Achievements:**
  - 7 widgets completos (~4,672 linhas)
  - 122 testes unitários
  - Full integration (orchestrator, state management, hardware coordination)
- **Documentation:**
  - Implementation Report: `conductor/RELATORIO_IMPLEMENTACAO_ABAS_1-4.md`
  - Track Archives: `conductor/archive/engenharia_aba[1-7]*/`

### ✅ Refactor Large Monolithic Files (2026-01-14)
- **Track ID:** refactor_large_files_20260113
- **Status:** Complete (archived)
- **Duration:** 2 days (estimated 4-6 weeks)
- **Achievements:**
  - 3 arquivos monolíticos refatorados (~3,817 linhas)
  - 13 novos módulos focados
  - 462 testes passing (97.7% pass rate)
  - Zero breaking changes
  - 3,114 linhas de código bem documentado
- **Documentation:**
  - Completion Report: `docs/reports/REFACTORING_COMPLETION_REPORT.md`
  - Track Archive: `conductor/archive/refactor_large_files_20260113/`

### ✅ Integrate Engineering Wizard (2026-01-14)
- **Track ID:** integrate_engineering_wizard_20260113
- **Status:** 98% Complete - Ready for validation
- **Duration:** 1 day (estimated 3-4 weeks)
- **Achievements:**
  - EngineeringWizardDialog (orchestrator das 7 abas)
  - EngineeringWizardState (estado compartilhado)
  - EngineeringHardwareCoordinator (coordenação de hardware)
  - EngineeringProgramManager (persistência de programas)
  - EngineeringRecipeCoordinator (integração com RecipeManager)
  - Menu integration + toolbar button
  - Documentação completa (620 linhas)
- **Documentation:**
  - Track Archive: `conductor/archive/integrate_engineering_wizard_20260113/`

## Commands

### Running the Application
```bash
# Main application (Windows Python, typically in .venv)
.venv/Scripts/python.exe main.py

# Alternative: run as module
python -m consumo_lib.main_window

# Utilities in tools/
python tools/mosaic_builder.py
python tools/camera_calibration.py
python tools/Leitura_Continua.py [COM_PORT]

# FOV corrections validation test
python tests/unit/test_fov_corrections.py
```

### Environment Setup
```bash
# The project uses .venv virtual environment
# Core dependencies:
# - PyQt6 (GUI)
# - opencv-python (cv2)
# - numpy
# - pymodbus (Modbus TCP)
# - pyserial (RS-232)
# - reportlab (PDF generation)
# - matplotlib (charts)

# Install all at once:
pip install -r requirements.txt
```

### Test Suite
**Unit Tests:** 48 tests in `test_tensiometer_services.py` (100% service layer coverage, testable without PyQt6) + `test_fov_corrections.py` for FOV calibration validation.
Primary testing is through practical validation with real hardware (PLC, tensiometer, USB camera).

### Git Repository Status
- **Primary Branch:** `main` (migrated from `master` on 2026-01-05)
- **Active Branches:** `main`, `clp`, `clp-release`
- **Remote:** `git@github.com:RONALDBUZAGLO/tensiometro.git` (SSH configured)
- **Repository Size:** ~2.0 GB (245 Python files, ~59,516 lines of code)
- **Last Major Update:** 2026-01-14 - SOLID Refactoring Phase 1 complete + Engineering Wizard integration

### Module Import Patterns

**From aoi_lib (Core Business Logic):**
```python
# Recommended imports from aoi_lib
from aoi_lib import (
    CNCAOIController,
    PLCAxisController,
    CameraController,
    StencilTracker, Stencil, TensionRecord, InspectionRecord,
    StencilDatabase, migrate_json_to_sqlite
)

# Individual modules can be imported directly
from aoi_lib.fov_calibration import FOVCalibration, CameraFOVConverter

# Tensiometer module (NEW - 2026-01-14)
from aoi_lib.tensiometer import (
    MeasurementOrchestrator,
    TensiometerSerialManager,
    TensionMeasurementThread,
    GridCalculationService,
    MeasurementAnalysisService,
    GridPoint,
    TensionMeasurement,
    GridParameters,
    MeasurementSession,
    ValidationError
)

# Other modules
from aoi_lib.recipe_manager import RecipeManager
from aoi_lib.fiducial_alignment import FiducialAlignment
from aoi_lib.gerber_parser import GerberParser
from aoi_lib.gerber_renderer import GerberRenderer
from aoi_lib.stencil_inspector import StencilInspector

# Gerber Core (NEW - 2026-01-14)
from aoi_lib.gerber_core.models import GerberObject, GerberModel
from aoi_lib.gerber_core.controllers import GerberController
from aoi_lib.gerber_core.commands import (
    EditCircleCommand,
    EditRectangleCommand,
    EditObroundCommand,
    EditRegionCommand,
    create_edit_command
)
from aoi_lib.gerber_core.commands.parser_edit_commands import (
    ParserEditCircleCommand,
    ParserEditRectangleCommand,
    ParserEditObroundCommand,
    ParserEditRegionCommand,
    create_parser_edit_command
)
```

**From consumo_lib (Modular GUI):**
```python
# Main window (orchestrator)
from consumo_lib.main_window import MainWindow

# Tabs
from consumo_lib.tabs import CNCControlTab, TensionTab, InspectionTab, MapTab, TrackingTab, TreeViewTab

# Controllers
from consumo_lib.controllers import (
    MovementController, CameraController, TensionMeasurementController,
    FiducialAlignmentController, InspectionUIController
)

# Dialogs (NEW - 2026-01-14)
from consumo_lib.dialogs.tension import TensionMeasurementDialog
# Legacy import still works (with deprecation warning):
# from aoi_lib.stencil_tension import StencilTensionDialog

# Engineering Wizard (NEW - 2026-01-14)
from consumo_lib.dialogs import EngineeringWizardDialog
from consumo_lib.widgets.engenharia import (
    ProgramDataWidget,           # Aba 1
    GerberUploadWidget,          # Aba 2
    FiducialCaptureWidget,       # Aba 3
    MosaicCaptureWidget,         # Aba 4
    AlignmentWidget,             # Aba 5
    InspectionWindowsWidget,     # Aba 6
    ConfirmSaveWidget,           # Aba 7
)

# Stencil Management (NEW - 2026-01-13)
from consumo_lib.widgets.stencil import IdentificationWidget
from consumo_lib.dialogs.stencil import (
    StencilManagerDialog,
    StencilCreateDialog,
    StencilEditDialog,
    StencilHistoryDialog,
    StencilFullHistoryDialog,
)

# Managers
from consumo_lib.managers import (
    RecipeManager, StencilManager, InspectionManager,
    ReportManager, RoleManager, SessionLogger,
    EngineeringProgramManager, ConnectionManager
)

# Services
from consumo_lib.services import (
    MovementService, ClickToMoveService,
    SequenceExecutionService, ResourceManager
)

# Coordinators
from consumo_lib.coordinators import (
    SetupCoordinator, InspectionCoordinator,
    OperatorWorkflow, ConnectionCoordinator,
    EngineeringHardwareCoordinator, EngineeringRecipeCoordinator,
    TensionCoordinator
)
```

## Development Workflow

### Adding a New Feature: Step-by-Step

**1. Planning Phase**
- Read relevant CLAUDE.md sections (Hardware Integration, Data Models, Data Flows)
- Check BACKLOG.md for existing related tasks
- Identify which aoi_lib modules will be affected
- Check if new configuration needed in aoi_config.json

**2. Implementation Phase**
- Create new module in `aoi_lib/` (NEVER extend consumo_lib modules directly)
- Follow existing patterns: dataclass models + manager/controller class
- Use logging: `logger = logging.getLogger(__name__)`
- Add type hints consistently
- For new UI: create widget in `consumo_lib/widgets/` or tab in `consumo_lib/tabs/`

**3. Integration Phase**
- Import from aoi_lib in consumo_lib if needed
- Add menu item via MenuHandler (consumo_lib/handlers/menu_handler.py)
- Connect signals using existing pattern (QThread + pyqtSignals)
- Test with hardware if applicable

**4. Documentation Phase**
- Update CLAUDE.md if adding new concepts
- Add inline docstrings to new classes (Google style)
- Update CHANGELOG if behavior changes

**CRITICAL: Code Organization Rules**
- ✅ Business logic → `aoi_lib/`
- ✅ UI components → `consumo_lib/tabs/` or `consumo_lib/widgets/`
- ✅ Hardware control → `aoi_lib/*_controller.py`
- ❌ NEVER add business logic to `consumo_lib/main_window.py` (it's an orchestrator only)

### Debugging Workflow

**Enable Debug Logs:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or add to aoi_config.json:
# "logging": {
#   "level": "DEBUG",
#   "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
# }
```

**Key Log Locations:**
- PLC connection/movement: `aoi_lib/plc_axis_controller.py` (search for "🎯" or "DEBUG PLC")
- Tensiometer serial: `aoi_lib/tensiometer/serial_protocol.py` (search "read_tension_value")
- FOV conversion: `aoi_lib/fov_calibration.py` (search "Coeficientes FOV")
- Fiducial alignment: `aoi_lib/fiducial_alignment.py` (search "Template matching")
- Inspection: `aoi_lib/stencil_inspector.py` (search "Inspecting aperture")

**Common Debugging Commands:**
```python
# Check PLC connection status
plc.is_connected  # Returns bool
plc.read_position('X')  # Returns position in pulses
plc.machine_status  # Returns "Idle", "Run", or "Alarm"

# Check camera
camera.is_connected
camera.frame_width, camera.frame_height
camera.last_error

# Check tensiometer
tensio.is_connected
tensio.last_error

# Check FOV calibration
from aoi_lib.fov_calibration import CameraFOVConverter
converter = CameraFOVConverter(calibration_data)
converter.get_fov_at_z(0)  # Returns (width_mm, height_mm)
```

**Testing Without Hardware:**
- **PLC:** Cannot mock easily - use real PLC or skip PLC-dependent tests
- **Tensiometer:** Use `Leitura_Continua.py` for standalone serial testing
- **Camera:** Test with video file or image sequence
- **Gerber:** Use files in `poc_gerber/` with standalone viewer

## Architecture Overview

### Hardware Integration Layer
- **PLCAxisController** ([aoi_lib/plc_axis_controller.py](aoi_lib/plc_axis_controller.py)) - Modbus TCP communication with Delta CLP for 3-axis (X,Y,Z) movement control
- **TensiometerSerialManager** ([aoi_lib/tensiometer/serial_protocol.py](aoi_lib/tensiometer/serial_protocol.py)) - RS-232 serial protocol (2400 baud, 9-byte frame) for AS-120N tension sensor
- **CameraController** ([aoi_lib/camera_controller.py](aoi_lib/camera_controller.py)) - OpenCV USB camera interface with real-time preview

### Tensiometer Module (NEW - 2026-01-14)
Location: `aoi_lib/tensiometer/` - Refactored from `aoi_lib/stencil_tension.py` (1,409 → 2,368 lines across 5 modules)

**Purpose:** Tension measurement of stencils with SOLID principles, separation of concerns, and 100% testable business logic

**Components:**
- **models.py** (267 lines) - Data structures with dataclasses:
  - `GridPoint` - Single measurement point (x, y, index, grid_position)
  - `TensionMeasurement` - Measurement with value, unit, timestamp, validation
  - `GridParameters` - Configuration (start_point, end_point, grid_size, z_height, z_move)
  - `MeasurementSession` - Complete session with measurements, statistics, duration
  - `TensiometerConfig` - Serial port configuration
  - `TensionUnit` - Unit enum (N_CM2, KG_CM2, LB_CM2)

- **serial_protocol.py** - AS-120N tensiometer serial communication:
  - `TensiometerSerialManager` - RS-232 protocol handler (2400 baud, 9-byte frame)
  - `read_tension_value()` - Read tension value with automatic decoding
  - Context manager support (`with` statement)
  - Error handling and last_error tracking

- **measurement_thread.py** (238 lines) - Background measurement execution:
  - `TensionMeasurementThread` - PyQt6 QThread for non-blocking measurements
  - Signals: `progress_updated`, `measurement_completed`, `finished`, `error_occurred`
  - Graceful stop support with `request_stop()`

- **measurement_service.py** (467 lines) - Business logic (100% testable without PyQt6):
  - `GridCalculationService` - Calculate grid points in zig-zag pattern
    - `calculate_grid_points()` - Generate NxN grid with validation
    - `validate_parameters()` - Check grid constraints (size, Z heights)
    - `get_grid_statistics()` - Calculate total distance, bounds
  - `MeasurementAnalysisService` - Statistical analysis and classification
    - `analyze_session()` - Complete analysis (statistics, classification, outliers)
    - `_classify_tension()` - Classify as OK/WARNING/CRITICAL based on mean and CV
    - `generate_report()` - Human-readable text report
  - `ValidationError` - Custom exception for validation failures

- **measurement_orchestrator.py** (415 lines) - Facade for complete workflow:
  - `MeasurementOrchestrator` - Coordinates entire measurement process
  - `prepare_measurement()` - Validate and prepare measurement session
  - `start_measurement()` - Start background thread with callbacks
  - `stop_measurement()` - Request graceful stop
  - `save_results()` - Save session to JSON file
  - `get_report()` - Generate formatted report

**Usage Example:**
```python
from aoi_lib.tensiometer import (
    MeasurementOrchestrator,
    TensiometerSerialManager,
    GridCalculationService,
    MeasurementAnalysisService
)
from consumo_lib.dialogs.tension import TensionMeasurementDialog

# Setup
tensiometer = TensiometerSerialManager()
tensiometer.connect("COM3")

# Orchestrator handles everything
orchestrator = MeasurementOrchestrator(cnc, tensiometer)

# Prepare
result = orchestrator.prepare_measurement(
    start_point=(0, 0),
    end_point=(100, 100),
    grid_size=3,
    z_height=5.0,
    z_move=10.0
)

# Start with callbacks
orchestrator.start_measurement(
    points=result['points'],
    on_progress=lambda cur, total, msg: print(f"{cur}/{total}: {msg}"),
    on_complete=lambda results: print(f"Done: {results['analysis']}")
)
```

**Benefits of Refactoring:**
- ✅ Separation of concerns (SRP compliant)
- ✅ Service layer 100% testable without PyQt6
- ✅ Dialog reduced from 962 to 482 lines (50% reduction)
- ✅ 48 unit tests for business logic
- ✅ Zero breaking changes (backward compatibility maintained)
- ✅ Type hints and docstrings throughout

**UI Dialog:**
- **TensionMeasurementDialog** ([consumo_lib/dialogs/tension/tension_measurement_dialog.py](consumo_lib/dialogs/tension/tension_measurement_dialog.py)) - Refactored PyQt6 dialog (482 lines, UI-only responsibilities)
- Uses `MeasurementOrchestrator` for all business logic
- Progress display, status updates, error messages
- Available via `from consumo_lib.dialogs.tension import TensionMeasurementDialog`

**Legacy Compatibility:**
- Old import still works with deprecation warning: `from aoi_lib.stencil_tension import StencilTensionDialog`
- Compatibility layer re-exports from new locations
- See `docs/guides/SOLID_PHASE1_MIGRATION_GUIDE.md` for migration guide

### Core Business Logic
- **AOIController** ([aoi_lib/aoi_controller.py](aoi_lib/aoi_controller.py)) - High-level orchestrator integrating CNC movement + camera capture
- **StencilTracker** ([aoi_lib/stencil_tracker.py](aoi_lib/stencil_tracker.py)) - Data models (Stencil, TensionRecord, InspectionRecord) with JSON persistence
- **StencilInspector** ([aoi_lib/stencil_inspector.py](aoi_lib/stencil_inspector.py)) - Visual inspection engine with threshold-based analysis (OK/PARTIAL/BLOCK)
- **RecipeManager** ([aoi_lib/recipe_manager.py](aoi_lib/recipe_manager.py)) - Configuration management for different stencil models with acceptance criteria

### Gerber Core (NEW - 2026-01-14)
Location: `aoi_lib/gerber_core/` - Refactored Gerber file handling with MVC architecture and Command Pattern

**Purpose:** Provide SOLID-compliant architecture for Gerber RS-274X file manipulation with separation of concerns

**Components:**

- **models/gerber_model.py** (269 lines) - Model layer for MVC pattern:
  - `GerberObject` - Dataclass representing Gerber apertures (circles, rectangles, obrounds, regions)
  - `GerberModel` - Main model for Gerber data management
  - `transform_object()` - Apply transformations (scale, translate) to objects
  - `get_statistics()` - Query object counts by type
  - 23 unit tests, 97% coverage

- **controllers/gerber_controller.py** (316 lines) - Controller layer for MVC coordination:
  - `import_gerber()` - Load Gerber files into model
  - `select_object()` - Manage selection state
  - `edit_selected_object()` - Edit single object using Command Pattern
  - `edit_selected_objects()` - Batch edit multiple objects
  - `delete_selected_objects()` - Remove objects from model
  - 18 unit tests, 88% coverage

- **commands/edit_commands.py** (276 lines) - Command Pattern for models.GerberObject:
  - `EditObjectCommand` (ABC) - Base command with Template Method pattern
  - `EditCircleCommand` - Edit circular apertures
  - `EditRectangleCommand` - Edit rectangular apertures
  - `EditObroundCommand` - Edit obround (racetrack) apertures
  - `EditRegionCommand` - Edit polygonal regions
  - 20 unit tests, 74% coverage

- **commands/parser_edit_commands.py** (344 lines) - Command Pattern for parser.GerberObject (conservative refactoring):
  - `ParserEditObjectCommand` (ABC) - Base command for parser objects
  - `ParserEditCircleCommand` - Edit circles (kind="flash_circle")
  - `ParserEditRectangleCommand` - Edit rectangles (kind="flash_rect")
  - `ParserEditObroundCommand` - Edit obrounds (kind="flash_oval")
  - `ParserEditRegionCommand` - Edit regions (kind="region")
  - `create_parser_edit_command()` - Factory Function for command creation
  - 17 unit tests, 96% coverage

- **gui/mainwindow.py** (1,421 lines) - POC Gerber Viewer with refactored edit methods:
  - `on_edit_object()` - Single object edit (complexity: 27 → <5) ✅
  - `on_edit_many_objects()` - Batch edit (complexity: 46 → <5) ✅
  - `_edit_rectangle_or_oval_group()` - Helper for rectangle/oval group editing
  - `_edit_region_group()` - Helper for region group editing
  - `_refresh_preview()` - Helper for view updates
  - Integration tests: 10/13 passing (3 skipped pending full MVC implementation)

**Usage Example:**
```python
from aoi_lib.gerber_core.models import GerberObject, GerberModel
from aoi_lib.gerber_core.controllers import GerberController
from aoi_lib.gerber_core.commands import create_parser_edit_command

# Option 1: Using Controller (recommended for new code)
model = GerberModel()
controller = GerberController(model)
controller.import_gerber(lines, cfg)
controller.select_object(0, "layer1")
controller.edit_selected_object({"diameter": 10.0})  # Edit via Command Pattern

# Option 2: Using Commands directly (for parser.GerberObject)
from aoi_lib.gerber_core.parser import GerberObject
obj = GerberObject(kind="flash_circle", ...)
command = create_parser_edit_command(obj)
modified = command.execute(new_dia_mm=10.0)
```

**Benefits of Refactoring:**
- ✅ **SOLID Principles**: SRP (separation of concerns), OCP (open for extension, closed for modification), DIP (depend on abstractions)
- ✅ **Testability**: Service layer 100% testable without PyQt6
- ✅ **Reduced Complexity**: Cyclomatic complexity from 27,46 → <5 (70% reduction)
- ✅ **Zero Breaking Changes**: Backward compatibility maintained
- ✅ **Type Safety**: Full type hints throughout

**Migration Notes:**
- Parser.GerberObject commands are a **temporary solution** during migration
- Future phases will migrate to GerberModel completely
- See `conductor/tracks/solid_refactoring_phase2_20260114/` for detailed implementation plan

### Computer Vision Pipeline
1. **FiducialAlignment** ([aoi_lib/fiducial_alignment.py](aoi_lib/fiducial_alignment.py)) - Template matching for reference mark detection and transformation calculation
2. **GerberParser** ([aoi_lib/gerber_parser.py](aoi_lib/gerber_parser.py)) - RS-274X Gerber file parsing with automatic fiducial candidate detection
3. **GerberRenderer** ([aoi_lib/gerber_renderer.py](aoi_lib/gerber_renderer.py)) - Converts Gerber vector data to OpenCV masks for inspection
4. **MosaicBuilder** ([mosaic_builder.py](mosaic_builder.py)) - Image stitching from grid captures with multiband blending

### POC Gerber Viewer
Located in `poc_gerber/` (formerly `testes_gerber/`) - Proof of Concept for standalone Gerber file viewer:
- **Entry Point:** `poc_gerber/gerber_viewer/gui/mainwindow.py` (1,384 lines)
- **Features:** Visualize, edit, and export Gerber RS-274X files with PyQt6 GUI
- **Bug Fixes (2026-01-05):**
  - Fixed duplicate movement bug in `_move_objects()` method (was applying dx/dy twice)
  - Corrected obround geometry to match Gerber spec (rectangle + semi-circles, not ellipse)
  - Added robust validation to parser functions
- **Status:** Functional POC with improved accuracy for obround apertures

### Configuration & Persistence
- **AOIConfigManager** ([aoi_lib/config_manager.py](aoi_lib/config_manager.py)) - Manages [aoi_config.json](aoi_config.json) (CNC params, connection settings, FOV calibration)
- **StencilDatabase** ([aoi_lib/stencil_database.py](aoi_lib/stencil_database.py)) - SQLite layer (partial migration from JSON)
- **ReportGenerator** ([aoi_lib/report_generator.py](aoi_lib/report_generator.py)) - PDF generation using reportlab with heatmaps and trend analysis

### Main Application (Modular Architecture)
**consumo_lib/** package - Evolved from monolithic 6,245-line file to modular structure (125 files, ~37,889 lines):
- **main_window.py** (1,060 lines) - PyQt6 main window orchestrator with tabs:
  - CNC Control: Manual jogging, camera preview with click-to-move
  - Tension Measurement: Grid-based sampling with heatmap visualization
  - Stencil Inspection: Fiducial alignment, Gerber overlay, visual analysis
  - Map Generation: Image mosaic creation from grid captures
  - Tracking & Reports: Stencil history, trend analysis, PDF generation
  - Operator Workflow: Guided inspection workflow with role-based access
- **tabs/** (8 files) - Tab implementations (CNCControlTab, TensionTab, InspectionTab, MapTab, TrackingTab, TreeViewTab)
- **widgets/** (25 files) - Reusable UI components:
  - **engenharia/** (7 files) - Engineering Wizard widgets (ProgramDataWidget, GerberUploadWidget, FiducialCaptureWidget, MosaicCaptureWidget, AlignmentWidget, InspectionWindowsWidget, ConfirmSaveWidget)
  - **stencil/** (3 files) - Stencil management widgets (IdentificationWidget, etc.)
  - Others: CameraPreviewWidget, MovementControlWidget, OperatorInterface, HardwareStatusBar, etc.
- **dialogs/** (26 files) - Dialog windows:
  - **tension/** - TensionMeasurementDialog (refatorado 2026-01-14)
  - **stencil/** (5 dialogs) - StencilManagerDialog, CreateDialog, EditDialog, HistoryDialog, FullHistoryDialog
  - Others: InspectionSettings, CrosshairSettings, LoginDialog, EngineeringWizardDialog, etc.
- **controllers/** (14 files) - Hardware control wrappers (MovementController, CameraController, TensionMeasurementController, etc.)
- **coordinators/** (8 files) - Complex workflow orchestration (SetupCoordinator, InspectionCoordinator, OperatorWorkflow, ConnectionCoordinator, EngineeringHardwareCoordinator, EngineeringRecipeCoordinator, TensionCoordinator, etc.)
- **managers/** (9 files) - Business logic wrappers (RecipeManager, StencilManager, EngineeringProgramManager, RoleManager, SessionLogger, ConnectionManager, InspectionManager, ReportManager, etc.)
- **handlers/** (5 files) - Event handling (KeyboardHandler, MenuHandler, DialogRouter, GRBLCallbackHandler - SignalAggregator removido)
- **services/** (6 files) - Business services (MovementService, ClickToMoveService, SequenceExecutionService, ResourceManager, etc.)
- **threads/** (5 files) - Worker threads (MapGenerator, SequenceRunner, InspectionWorker, OperatorInspectionThread)
- **ui_builders/** (2 files) - UI construction helpers
- **utils/** (10 files) - Utility functions (error_handler, ux_helpers, etc.)
- **models/** (5 files) - Data models:
  - **engineering/** - Engineering program models (ProgramConfig, WizardState, etc.)
  - InspectionWindow model

**Entry Point:**
- **main.py** (34 lines) - Application entry point that initializes and launches MainWindow

## Critical Data Flows

### Tension Measurement Flow
```
User selects stencil → RecipeManager.load_recipe(stencil.recipe_name)
                         ↓
TensionTab reads recipe grid config (rows, cols, bounds)
                         ↓
TensiometerSerialManager.connect(port)
                         ↓
PLCAxisController moves to start_position (X, Y)
                         ↓
Loop for each grid point:
  1. PLCAxisController.move_absolute(axis, position, speed)
  2. Wait for idle (wait_for_idle with tolerance)
  3. Z-axis descends for contact
  4. TensiometerSerialManager.read_tension_value()
     → Serial write(0x20) → Read 9 bytes → Decode value
  5. Z-axis retracts
  6. Store measurement in TensionMeasurementThread
  7. Emit progress_updated signal
                         ↓
All points complete → TensionMeasurementThread.finished signal
                         ↓
StencilTracker.add_tension_record(stencil_code, TensionRecord)
                         ↓
Classification: OK/WARNING/NOK based on recipe.tension_config.acceptance
                         ↓
Optional: ReportGenerator.generate_pdf()
```

### Visual Inspection Flow
```
User loads Gerber file → GerberParser.parse() → Detect fiducial candidates
                           ↓
User captures fiducial templates → Click on camera preview (N points)
                                     ↓
FiducialAlignment.capture_template(x, y, window_size)
                                     ↓
Generate mosaic → MapGeneratorThread runs CNC grid
                   → Capture images at each point
                   → MosaicBuilder.stitch_images() (multiband blending)
                                     ↓
User aligns Gerber → FiducialAlignmentWidget.drag_overlay()
                      → Auto-search fiducials (template_matching)
                      → Calculate AlignmentTransform (tx, ty, angle, scale)
                                     ↓
Render masks → GerberRenderer.render_to_image(transform)
                → OpenCV masks for each aperture
                                     ↓
Inspect → StencilInspector.inspect(image, masks, thresholds)
            → Binarize image (Otsu/Adaptive)
            → Compare expected vs observed area
            → Classify: OK (≥90%), PARTIAL (70-90%), BLOCKED (<70%)
                                     ↓
Results → InspectionResultWidget.show(results)
           → Optional PDF report with overlay
```

### Click-to-Move Flow
```
User clicks camera preview → ClickableVideoLabel.mousePressEvent()
                              → Get pixel coordinates (x_px, y_px)
                              ↓
video_click_to_movement(x_px, y_px)
  1. CameraFOVConverter.get_fov_at_z(current_z)
     → Returns (width_mm, height_mm)
  2. Convert pixel offset to mm offset
     → dx_mm = (x_px - center_x) * (width_mm / frame_width)
     → dy_mm = (y_px - center_y) * (height_mm / frame_height)
  3. Apply Y-axis inversion (if needed)
     → if not invert_y: dy_mm = -dy_mm
  4. Convert mm to pulses
     → dx_pulses = dx_mm * pulses_per_mm[X]
     → dy_pulses = dy_mm * pulses_per_mm[Y]
  ↓
PLCAxisController.move_absolute('X', current_x + dx_pulses)
PLCAxisController.move_absolute('Y', current_y + dy_pulses)
  → wait_for_idle() until movement completes
```

### Dependency Graph
```
consumo_lib/main_window.py (1,060 lines - orchestrator only)
  ├── consumo_lib/coordinators/SetupCoordinator (initialization)
  │   ├── consumo_lib/managers/ (9 files: RecipeManager, StencilManager, EngineeringProgramManager, RoleManager, SessionLogger, ConnectionManager, etc.)
  │   ├── consumo_lib/controllers/ (14 files: MovementController, CameraController, TensionMeasurementController, etc.)
  │   ├── consumo_lib/services/ (6 files: MovementService, ClickToMoveService, SequenceExecutionService, ResourceManager, etc.)
  │   └── consumo_lib/handlers/ (5 files: KeyboardHandler, MenuHandler, DialogRouter, GRBLCallbackHandler - SignalAggregator removido)
  ├── consumo_lib/tabs/ (8 files: CNCControlTab, TensionTab, InspectionTab, MapTab, TrackingTab, TreeViewTab)
  │   ├── consumo_lib/widgets/ (25 files)
  │   │   ├── widgets/engenharia/ (7 files - Engineering Wizard)
  │   │   └── widgets/stencil/ (3 files)
  │   ├── consumo_lib/dialogs/ (26 files)
  │   │   ├── dialogs/tension/ (TensionMeasurementDialog - refatorado)
  │   │   └── dialogs/stencil/ (5 dialogs)
  │   └── consumo_lib/threads/ (5 files: MapGenerator, SequenceRunner, InspectionWorker, OperatorInspectionThread)
  └── aoi_lib/ (CORE BUSINESS LOGIC - 59 files, ~21,627 lines)
      ├── tensiometer/ (7 files - NOVO 2026-01-14)
      │   ├── models.py (data structures)
      │   ├── serial_protocol.py (AS-120N protocol)
      │   ├── measurement_thread.py (QThread)
      │   ├── measurement_service.py (business logic)
      │   ├── measurement_orchestrator.py (facade)
      │   └── tension_measurement.py (legacy compatibility)
      ├── plc_axis_controller.py (Modbus TCP - hardware layer)
      ├── camera_controller.py (OpenCV - hardware layer)
      ├── fov_calibration.py (pixel↔mm conversion)
      ├── fiducial_alignment.py (template matching)
      ├── gerber_parser.py (RS-274X parsing)
      ├── gerber_renderer.py (mask generation)
      ├── stencil_inspector.py (visual inspection engine)
      ├── stencil_tracker.py (data models + persistence)
      ├── recipe_manager.py (recipe configuration)
      ├── report_generator.py (PDF generation)
      └── config_manager.py (JSON settings)
```

## Key Technical Details

### Coordinate System & Movement
- **Pulse-to-MM Conversion:** Configured in `aoi_config.json` (`pulses_per_rev`, `fuso_pitch`)
  - Default: 1000 pulses/rev ÷ 10mm/rev = 100 pulses/mm
- **Movement Modes:** Absolute positioning (G90) and relative (G91) via Modbus registers
- **Speed Control:** Separate speeds for jogging, inspection moves, and tension measurement
- **Interpolation:** X and Y axes share coil M1050 for coordinated movement (NOT separate coils)

### FOV Calibration System
- **FOVCalibration** ([aoi_lib/fov_calibration.py](aoi_lib/fov_calibration.py)) - Pixel-to-millimeter conversion
- **Fixed Camera:** Unlike ADESIVADORA, Tensiometro has fixed camera (FOV constant regardless of Z)
- **Click-to-Move:** Camera preview allows clicking points to automatically center them (uses FOV conversion)
- **Calibration Data:** Stored in `camera_calibration.json`

### Unit Conversions Reference

**Pulse ↔ Millimeter (CNC Positioning):**
```python
# From aoi_config.json: "pulses_per_rev": 800, "fuso_pitch": 10.0
pulses_per_mm = 800 / 10.0 = 80.0

# Examples:
position_mm = 50.0
position_pulses = position_mm * pulses_per_mm  # 4000 pulses
```

**Pixel ↔ Millimeter (Camera FOV):**
```python
# From camera_calibration.json: FOV at Z=0 is 34.0mm x 34.0mm
# Frame size: 640px x 480px
mm_per_pixel_x = 34.0 / 640  # 0.0531 mm/px
mm_per_pixel_y = 34.0 / 480  # 0.0708 mm/px
```

**Tensiometer Value Decoding (AS-120N Protocol):**
```python
# 9-byte frame: byte[6]=d3, byte[7]=d2, byte[8]=d1 (nibbles shifted by +0x0A)
# Byte[3] bits 4-6 = decimal places (casas)
def _decode_frame(frame):
    casas = (frame[3] >> 4) & 0x07
    d3, d2, d1 = _real_dig(frame[6]), _real_dig(frame[7]), _real_dig(frame[8])
    raw = d3 * 100 + d2 * 10 + d1
    value = raw / (10 ** casas)  # Apply decimal places
    return value  # In N/cm²
```

### Tension Measurement Protocol
- **Serial Frame Format:** 9 bytes @ 2400 baud, 8N1
- **Grid Calculation:** Zig-zag pattern with configurable NxN points
- **Z-Axis Contact:** Controlled descent for sensor contact without damaging stencil
- **Threading:** Measurement runs in separate thread to prevent UI blocking

### Visual Inspection Workflow
1. Load Gerber file (RS-274X format) for stencil design
2. Capture fiducial templates via click on camera preview
3. Auto-detect fiducials using template matching
4. Calculate transformation matrix (translation, rotation, scale)
5. Capture inspection image with backlight
6. Render Gerber masks aligned to image
7. Analyze each opening (binarization + pixel count)
8. Classify as OK (>threshold), PARTIAL (middle range), or BLOCKED (<threshold)
9. Generate PDF report with overlay and defect table

### Data Models (Dataclasses)
```python
# aoi_lib/stencil_tracker.py
Stencil              # code, description, recipe_name, status, creation_date
TensionRecord        # timestamp, grid_size, measurements, classification
InspectionRecord     # timestamp, gerber_file, image_path, results

# aoi_lib/recipe_manager.py
Recipe               # name, dimensions, tension_acceptance, inspection_thresholds
TensionAcceptance    # ok_min, warning_min, nok_max (in N/cm)
InspectionThresholds # ok_threshold, partial_threshold (pixel percentages)
```

## Error Handling Patterns

### Hardware Connection Errors
**Pattern: Graceful degradation + user notification**

Hardware disconnection is an **expected state**, not exception:
- UI continues to work without hardware
- Movement controls disabled when PLC disconnected
- User can retry connection via menu
- Log errors but don't raise (return safe defaults)

Example from `plc_axis_controller.py`:
```python
def connect(self) -> bool:
    try:
        self.client = ModbusTcpClient(self.host, port=self.port, timeout=1.0)
        if not self.client.connect():
            raise ConnectionError(f"PLC em {self.host}:{self.port} não responde")
        self.is_connected = True
        return True
    except Exception as e:
        self.is_connected = False
        logger.error(f"Falha ao conectar PLC: {e}")
        return False  # DON'T raise - allow app to run without PLC
```

### Serial Communication Errors
**Pattern: Retry + timeout + specific error messages**

Always return safe default ("0") on error, never raise:
```python
def read_tension_value(self) -> str:
    if not self.is_connected:
        self.last_error = "Tensiômetro não conectado"
        return "0"  # Safe default

    try:
        frame = self.serial_connection.read(self.FRAME_LEN)
        if len(frame) != self.FRAME_LEN:
            self.last_error = f"Frame incompleto: {len(frame)}/{self.FRAME_LEN} bytes"
            return "0"
        # ... decode and return value
    except Exception as e:
        self.last_error = f"Erro de leitura: {e}"
        return "0"
```

### Thread Safety (PyQt6)
**CRITICAL RULE:** Never update UI widgets from worker thread. Always use signals.

```python
class TensionMeasurementThread(QThread):
    progress_updated = pyqtSignal(int, int, str)  # point, total, message
    measurement_completed = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def run(self):
        try:
            for i, point in enumerate(self.grid_points):
                self.progress_updated.emit(i, total, f"Medindo ponto {i+1}/{total}")
        except Exception as e:
            self.error_occurred.emit(f"Erro na medição: {e}")

# In UI class (thread-safe):
self.thread.error_occurred.connect(self.on_measurement_error)
```

### Logging Best Practices
```python
logger = logging.getLogger(__name__)

# Use structured logging for key events:
logger.info("🎯 Movimento iniciado", extra={
    'axis': axis,
    'target': target,
    'feed_rate': feed_rate
})

# Include context in errors:
logger.error(f"Falha ao conectar PLC em {host}:{port}: {e}")

# Use emoji prefixes for easy scanning:
logger.info("✅ PLC conectado")
logger.warning("⚠️ Timeout aguardando eixo X")
logger.error("❌ Falha na leitura do tensiômetro")
```

## Domain Glossary - SMT Stencil Inspection

### SMT (Surface Mount Technology) Terms
- **Stencil**: Thin metal sheet (typically stainless steel, 0.12mm thick) with apertures for solder paste deposition
- **Aperture**: Opening in stencil (circle, rectangle, obround) through which solder paste is printed
- **Fiducial**: Reference mark (typically circular, 1-2mm diameter) used for visual alignment. Global fiducials are at stencil corners; local fiducials are near fine-pitch components
- **Backlight**: Illumination from below stencil to visualize apertures (light = open, dark = blocked)
- **Tension**: Surface tension of stencil mesh, measured in N/cm. Adequate tension ensures consistent paste release

### Units and Conversions
- **Pulses**: PLC internal units (integer). Converted to mm using `pulses_per_mm = pulses_per_rev / fuso_pitch`
  - Default: 1000 pulses/rev ÷ 10mm/rev = 100 pulses/mm
- **N/cm**: Tension measurement unit (Newtons per centimeter). Typical range: 25-45 N/cm
- **Mil**: Imperial unit for stencil thickness (1 mil = 0.001 inch = 0.0254mm). Common: 5 mil (0.127mm)
- **Obround**: Racetrack-shaped aperture (rectangle with semicircular ends). Gerber spec: rectangle + 2 semicircles (NOT ellipse) - **CRITICAL**: Already caused bug when implemented as ellipse
- **RS-274X**: Extended Gerber format (vector-based aperture definitions)

### Quality Standards
- **OK**: Aperture ≥90% clear (free from solder paste residue)
- **PARTIAL**: Aperture 70-90% clear (requires cleaning attention)
- **BLOCKED**: Aperture <70% clear (must clean before next print)
- Classification based on recipe's `InspectionThresholds.ok_threshold` and `partial_threshold`

### Hardware-Specific Terms
- **AS-120N**: Tensiometer model (tension measurement device). Serial protocol: 2400 baud, 9-byte binary frame
- **Delta PLC**: Programmable Logic Controller (Delta AS series). Modbus TCP @ 192.168.1.5:502
- **Modbus TCP**: Industrial communication protocol over Ethernet. Read/write coils (bits) and holding registers (16-bit integers)
- **FOV (Field of View)**: Area visible in camera frame, measured in mm. Constant for fixed camera (Tensiometro)

## Important Development Notes

### Hardware Dependencies
- **PLC:** Delta CLP series (Modbus TCP, default 192.168.1.5:502)
- **Tensiometer:** AS-120N (Serial RS-232, COM port varies)
- **Camera:** USB camera compatible with OpenCV (or HTTP stream support)

### Configuration Files
- **config/aoi_config.json** - System-wide settings (connection, calibration, UI state)
  - **Important:** Contains `auto_connect_plc: true` (enabled 2026-01-05) for automatic PLC connection
  - Contains `auto_connect_camera: true` for automatic camera connection
  - PLC connection: `plc_host: "192.168.1.5"`, `plc_port: 502`
  - Calibration: `pulses_per_rev: 800.0`, `fuso_pitch: 0.0`
  - CNC: `system_type: "corexy"`, `steps_per_unit: 80.0`
- **config/camera_calibration.json** - FOV calibration data
- **recipes/*.json** - Recipe definitions per stencil model
- **data/stencils/*.json** - Individual stencil history files

### Directory Structure Convention
```
reports/
  tension/       # Tension measurement PDFs
  stencil/       # Stencil history PDFs
data/
  stencils/      # JSON files per stencil code
recipes/         # Recipe JSON files
map_programs/    # Mosaic capture configuration
Projetos/        # Test projects with captured images
archive/         # Archived refactoring scripts and test files (2026-01-05)
docs/            # Documentation and manuals
  history/       # Development history and session notes
  manuals/       # Technical PDF manuals
assets/          # Project assets
  calibration/    # Calibration checkerboard images
poc_gerber/      # POC Gerber viewer (renamed from testes_gerber/)
aoi_lib/         # Core AOI library (59 files, ~21,627 lines)
consumo_lib/     # Main GUI application (125 files, ~37,889 lines, modular package, 1,060 lines main_window.py)
```

### Known Issues & Quirks
1. **Repository Size:** Currently ~2.0 GB due to large .rar files in Git history (needs cleanup with BFG or git-filter-repo)
2. **Refactoring Completed:** `consumo_lib.py` refactored to modular package with 125 files, ~37,889 lines (2026-01-05 to 2026-01-14)
3. **Legacy Code:** Some references to "ADESIVADORA" project (adhesive dispenser) - code was adapted from that project
4. **Dual Persistence:** Both JSON and SQLite supported - SQLite migration is partial/optional
5. **POC Gerber:** Located in `poc_gerber/` directory, contains experimental Gerber viewer with corrected obround geometry
6. **Build Artifacts in Root:** `coverage.xml`, `.coverage`, `htmlcov/` visible during development (properly in .gitignore)
7. **SignalAggregator Removed:** `consumo_lib/handlers/signal_aggregator.py` (1,192 lines) removed in 2026-01-14 - already refactored to `setup_ui_handlers()` pattern

### Coordinate Systems and Important Gotchas

**Image Coordinates vs CNC Coordinates:**
- Image coordinates: (0,0) at top-left, Y increases downward
- CNC coordinates: Y typically increases upward (toward operator)
- `video_click_to_movement()` in fov_calibration.py handles the conversion
- **Critical:** Y-axis inversion is handled with `invert_y` parameter - see CHANGELOG_2025-12-12.md for bug fix history

**Camera FOV is Fixed:**
- Unlike ADESIVADORA (movable camera), Tensiometro has fixed camera
- FOV calibration only needs one measurement (not two at different Z heights)
- `CameraFOVConverter.get_fov_at_z()` returns constant FOV regardless of Z

**Tensiometer Serial Protocol (AS-120N):**
- Request: Single byte `0x20`
- Response: 9 bytes starting with `0x10`, byte[2] = `0x19`
- Frame format is custom - see `Leitura_Continua.py` for standalone test utility
- Baud: 2400, 8N1, DTR=0, RTS=0

**Modbus TCP Addressing:**
- Default PLC: 192.168.1.5:502 (Delta AS series)
- Pulse-to-mm conversion: `pulses_per_rev` / `fuso_pitch` (from aoi_config.json)
- Movement uses absolute positioning (G90) or relative (G91)
- **X/Y Interpolation:** Axes X and Y share coil M1050 for coordinated movement (NOT separate coils M1050/M1050)
- See plc_axis_controller.py for register mapping

### Critical Sections to Preserve
- **Serial Protocol Decoding:** [aoi_lib/tensiometer/serial_protocol.py](aoi_lib/tensiometer/serial_protocol.py:~200-250) - 9-byte frame parsing is hardware-specific for AS-120N tensiometer (2400 baud, 8N1)
- **Modbus Register Mapping:** [aoi_lib/plc_axis_controller.py](aoi_lib/plc_axis_controller.py:~50-100) - PLC-specific addresses for Delta CLP series
- **FOV Conversion Logic:** [aoi_lib/fov_calibration.py](aoi_lib/fov_calibration.py:~150-250) - Pixel-to-pulse calculations for click-to-move functionality
- **Fiducial Alignment Transform:** [aoi_lib/fiducial_alignment.py](aoi_lib/fiducial_alignment.py) - Template matching for Gerber-to-image alignment

### Common Modification Patterns
When adding new features:
1. **Add to aoi_lib/** as separate module (don't extend consumo_lib modules)
2. **Update aoi_config.json schema** if adding configuration
3. **Add menu item** via MenuHandler (consumo_lib/handlers/menu_handler.py)
4. **Follow dataclass pattern** for new data models (see Stencil, TensionRecord, InspectionRecord)
5. **Use threading** for blocking operations (serial, Modbus, long computations)
6. **Use QThread/Signals** for PyQt6 UI updates from worker threads

### Gerber File Handling
- **Supported Format:** RS-274X only (Extended Gerber)
- **Fiducial Detection:** Looks for circular apertures (D-codes) in specific regions
- **Coordinate System:** Gerber units converted to mm for alignment
- **Rendering:** Uses QPainterPath for vector display, OpenCV masks for inspection

### Report Generation
- **Library:** reportlab (not matplotlib for PDF, matplotlib for embedded charts)
- **Templates:** Hard-coded layouts in [aoi_lib/report_generator.py](aoi_lib/report_generator.py)
- **Customization:** Logo, company name, colors via ReportConfig dialog
- **Output:** Always PDF, never HTML/Excel

## Performance Characteristics

### Known Bottlenecks

**Mosaic Generation (O(n) where n = number of images)**
- Location: `mosaic_builder.py` → `compose_mosaic_from_folder()`
- Typical grid: 8x8 = 64 images
- Capture delay: 200ms per image (configurable in `aoi_config.json`)
- Stitching: ~2-5 seconds using multiband blending
- **Optimization:** Reduce grid size, disable multiband blend, increase capture delay

**Gerber Rendering (O(m) where m = number of apertures)**
- Location: `aoi_lib/gerber_renderer.py` → `render_to_image()`
- Typical stencil: 500-2000 apertures
- Rendering time: ~1-3 seconds
- **Optimization:** Cache rendered masks, render only visible region

**Template Matching (O(p * w * h) where p = templates, w*h = search area)**
- Location: `aoi_lib/fiducial_alignment.py` → `locate_fiducials()`
- Search radius: 100px (default)
- Template size: 50px x 50px
- Time per fiducial: ~50-200ms depending on image size
- **Optimization:** Reduce `search_radius`, increase `threshold`, use fewer fiducials

### Latency Budget

| Operation | Typical Time | Notes |
|-----------|--------------|-------|
| PLC connect | 0.5-1s | One-time at startup |
| Camera connect | 1-2s | One-time, depends on USB |
| PLC move X/Y | 0.1-0.5s | Depends on distance + feed rate |
| Tensiometer read | 50-100ms | Serial protocol @ 2400 baud |
| Camera capture | 30-50ms | USB transfer |
| Mosaic capture (8x8) | 15-20s | Includes movement + capture |
| Fiducial alignment | 0.5-2s | Template matching |
| Full inspection (1000 apertures) | 5-10s | Includes rendering + analysis |
| PDF report generation | 2-5s | Includes charts + heatmap |

### Memory Usage

| Component | Typical Usage | Peak |
|-----------|---------------|------|
| Camera frame | 0.9 MB (640x480x3) | 3.6 MB (4K) |
| Mosaic (8x8) | 70-100 MB | Depends on blend |
| Gerber masks (1000 apertures) | 5-10 MB | Depends on complexity |
| Tensiometer grid (5x5) | <1 MB | Only data, no images |

## Troubleshooting Guide

### Hardware Issues

**PLC Not Connecting**
```
Symptoms:
  - "CLP Não Conectado" message at startup
  - Movement controls disabled
  - plc.is_connected returns False

Diagnosis:
  1. Ping PLC: ping 192.168.1.5
  2. Check aoi_config.json: "plc_host" and "plc_port"
  3. Check PLC power and network cable

Solutions:
  - Verify PLC is powered on (LED indicators)
  - Check network cable (use known-good cable)
  - Try different IP: Tools → Preferences → Connections → PLC Host
  - Restart PLC (power cycle)
  - Check Windows Firewall (allow Python.exe on port 502)
```

**Tensiometer Returns "0" or Inconsistent Values**
```
Symptoms:
  - All tension measurements show "0.00"
  - Values fluctuate wildly
  - Error: "Frame incompleto" or "Frame inválido"

Diagnosis:
  1. Check COM port in Tools → Connections
  2. Use Leitura_Continua.py for standalone testing
  3. Check TensiometerSerialManager.last_error

Solutions:
  - Verify correct COM port (use dropdown, don't type manually)
  - Check serial cable (use null-modem cable if needed)
  - Ensure tensiometer is powered on
  - Reset tensiometer (power cycle)
  - Try different baudrate (default 2400, some models use 9600)
```

**Camera Shows Black Screen**
```
Symptoms:
  - Camera preview is black
  - "Camera disconnected" status
  - Error: "Could not open camera"

Solutions:
  - Try different camera ID from dropdown
  - Use external powered USB hub
  - Replug USB cable
  - Check camera privacy settings in Windows
```

### Calibration Issues

**FOV Calibration Inaccurate**
```
Symptoms:
  - Click-to-move targets wrong position
  - Measurements don't match real dimensions

Solutions:
  - Recalibrate using physical ruler (50mm recommended)
  - Ensure ruler is in focal plane
  - Check camera mirror settings (aoi_config.json → camera → mirror_x/y)
  - Verify invert_y setting (see CHANGELOG_2025-12-12.md)
```

**Fiducial Alignment Fails**
```
Symptoms:
  - "Fiducial not found" error
  - Overlay doesn't match image

Solutions:
  - Recapture templates with better lighting (backlight ON)
  - Increase search_radius (default 100px, try 150-200px)
  - Decrease threshold (default 70%, try 60%)
  - Ensure fiducials are clean (no solder residue)
```

### Performance Issues

**Mosaic Generation Slow**
```
Solutions:
  - Reduce grid size (8x8 → 5x5)
  - Disable multiband blend (aoi_config.json → mosaic → use_multiband: false)
  - Reduce blend_size (20 → 10)
  - Increase capture_delay_ms (allow motion to settle)
```

**Inspection Takes Too Long**
```
Solutions:
  - Inspect only critical areas
  - Increase min_aperture_area_px to skip small pads
  - Use simpler binarization (method: "fixed" instead of "otsu")
```

## Project Organization Standards

**Last Updated:** 2026-01-08
**Status:** Enforced - Follow PROJECT_ORGANIZATION_GUIDELINES.md for all new code

### Directory Structure Principles

This project follows a **clean root** philosophy with clear separation of concerns:

```
tensiometro/
├── main.py                     # Single entry point (ACCEPTED in root)
├── README.md                   # Project overview (ACCEPTED in root)
├── CLAUDE.md                   # Claude Code context (ACCEPTED in root)
├── PROJECT_ORGANIZATION_GUIDELINES.md  # Organization standards (ACCEPTED in root)
│
├── aoi_lib/                    # Core AOI library (59 files, ~21,627 lines)
├── consumo_lib/                # Main GUI application (125 files, ~37,889 lines, modular package)
│   ├── main_window.py          # Main orchestrator (1,060 lines)
│   ├── tabs/                   # Tab implementations (8 files)
│   ├── widgets/                # Reusable UI components (25 files)
│   │   ├── engenharia/         # Engineering Wizard (7 files)
│   │   └── stencil/            # Stencil management (3 files)
│   ├── dialogs/                # Dialog windows (26 files)
│   │   ├── tension/            # Tension measurement dialog
│   │   └── stencil/            # Stencil CRUD dialogs (5 files)
│   ├── controllers/            # Hardware control wrappers (14 files)
│   ├── coordinators/           # Complex workflow orchestration (8 files)
│   ├── managers/               # Business logic wrappers (9 files)
│   ├── handlers/               # Event handling (5 files)
│   ├── services/               # Business services (6 files)
│   ├── threads/                # Worker threads (5 files)
│   ├── ui_builders/            # UI construction helpers (2 files)
│   ├── utils/                  # Utility functions (10 files)
│   └── models/                 # Data models (5 files)
│
├── tests/                      # Test suite
│   ├── unit/                   # Fast unit tests
│   ├── integration/            # Integration tests with mocks
│   └── fixtures/               # Test data and assets
│
├── tools/                      # Development utilities (camera calibration, mosaic builder, etc.)
│
├── config/                     # Configuration files
│   ├── aoi_config.json         # Main application configuration
│   ├── camera_calibration.json # FOV calibration data
│   └── map_programs/           # Mosaic capture configurations
│
├── docs/                       # Documentation (organized by purpose)
│   ├── guides/                 # How-to guides and tutorials
│   │   ├── testing_guide.md
│   │   ├── test_implementation_plan.md
│   │   └── fluxo_usuario_questionario.md
│   ├── architecture/           # System design documents
│   │   ├── ANALISE_INTEGRACAO_MOVEMENT_CONTROLS.md
│   │   └── TENSION_COORDINATOR.md
│   ├── meetings/               # Meeting notes and client reports
│   │   └── RELATORIO_CLIENTE_3_SEMANAS.md
│   ├── reports/                # Technical reports
│   │   └── RELATORIO_IMPLEMENTACAO_3_SEMANAS.md
│   ├── history/                # Development history
│   │   ├── BACKLOG.md
│   │   ├── CHANGELOG_2025-12-12.md
│   │   └── REFACTORING_*.md
│   └── manuals/                # Technical PDF manuals
│
├── data/                       # Application data
│   ├── stencils/               # Individual stencil JSON files
│   └── projects/               # User test projects (was Projetos/)
│
├── recipes/                    # Recipe definitions
├── reports/                    # Generated PDF reports
├── assets/                     # Static assets
│   └── calibration/            # Checkerboard images
│
├── archive/                    # Archived refactoring code
├── poc_gerber/                 # POC Gerber viewer
├── tension_routines/           # Domain-specific tension measurement utilities
├── programas_teste/            # Test programs for PLC
└── map_programs/               # Legacy map programs (consider moving to config/)
```

### Root Directory Rules

**✅ ALLOWED in root:**
- Entry points: `main.py`
- Essential guides: `README.md`, `CLAUDE.md`, `PROJECT_ORGANIZATION_GUIDELINES.md`
- Build configs: `pytest.ini`, `requirements.txt`
- Test runner wrappers: `run_tests.bat`, `run_tests.sh` (delegates to `tests/scripts/`)
- Virtual env: `.venv/`, `.conda/`
- Git: `.git/`, `.gitignore`
- Tool configs: `.vscode/`, `.claude/`

**❌ FORBIDDEN in root:**
- Utility scripts → `tools/`
- Test files → `tests/`
- Config files → `config/`
- Documentation (except essential guides) → `docs/`
- Data files → `data/`
- Build artifacts → `.gitignore`

### Build Artifacts Policy

**All build artifacts MUST be in .gitignore:**

```gitignore
# Coverage reports
htmlcov/
.coverage
coverage.xml
*.cover

# Pytest
.pytest_cache/

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python

# Virtual environments
.venv/
.conda/
venv/
ENV/
```

**Never commit:**
- Coverage reports (`htmlcov/`, `coverage.xml`)
- Test cache (`.pytest_cache/`)
- Python bytecode (`__pycache__/`, `*.pyc`)
- Virtual environment (`.venv/`, `.conda/`)
- User data (`data/projects/`, `Projetos/`)
- Generated reports (`reports/`)

### Configuration Management

**All configuration files MUST be in `config/`:**

- Application config: `config/aoi_config.json`
- Calibration data: `config/camera_calibration.json`
- Recipe definitions: `recipes/*.json` (exception: recipes stay in recipes/)
- Map programs: `config/map_programs/*.json`

**Loading config in code:**
```python
from pathlib import Path

# aoi_lib/config_manager.py
CONFIG_DIR = Path(__file__).parent.parent / "config"
AOI_CONFIG_PATH = CONFIG_DIR / "aoi_config.json"
```

### Documentation Organization

**Root level (essential guides only):**
- `README.md` - Project overview, quick start, installation
- `CLAUDE.md` - Claude Code context (this file)

**docs/ directory (detailed documentation):**
- `docs/guides/` - How-to guides (testing, development, deployment)
- `docs/history/` - Development history, session notes
- `docs/manuals/` - Technical PDF manuals, hardware specs

**Creating new documentation:**
```bash
# Guides go in docs/guides/
docs/guides/your_topic_guide.md

# Manuals go in docs/manuals/
docs/manuals/hardware_specification.pdf
```

### Tools and Utilities

**All standalone scripts MUST be in `tools/`:**

```bash
tools/
├── camera_calibration.py    # Camera calibration utility
├── mosaic_builder.py        # Image stitching tool
├── Leitura_Continua.py      # Tensiometer serial reader
└── tension/                 # Domain-specific tools
    ├── routine_1.py
    └── routine_2.py
```

**Running tools:**
```bash
# From project root
python tools/camera_calibration.py

# Or from tools/ directory
cd tools/
python camera_calibration.py
```

### Test Organization

**Test structure (enforced):**
```
tests/
├── unit/                   # Fast, no dependencies
│   ├── test_fov_calibration.py
│   └── test_gerber_parser.py
├── integration/            # With mocks, external deps
│   ├── test_plc_controller.py
│   └── test_tensiometer.py
├── fixtures/               # Test data
│   ├── gerber/
│   └── images/
├── scripts/                # Test runner utilities
│   ├── run_tests.bat       # Main test runner (Windows)
│   ├── run_tests.sh        # Main test runner (Unix/Linux)
│   └── README.md           # Test scripts documentation
└── conftest.py             # Global fixtures
```

**Test markers (use in test files):**
```python
@pytest.mark.unit           # Fast, isolated
@pytest.mark.integration    # With mocks
@pytest.mark.slow           # >1 second
@pytest.mark.hardware       # Requires physical hardware
```

### Migration Path (Current → Ideal)

**Phase 1: Clean Root (COMPLETED 2026-01-08)**
- ✅ Move test_fov_corrections.py → tests/unit/
- ✅ Update .gitignore
- ✅ Remove build artifacts from Git
- ✅ Move documentation files from root to docs/ subdirectories
- ✅ Organize docs/ with subdirectories (guides/, architecture/, meetings/, reports/)

**Phase 2: Organize Scripts (COMPLETED 2026-01-08)**
- ✅ Move `camera_calibration.py` → tools/
- ✅ Move `mosaic_builder.py` → tools/
- ✅ Move `Leitura_Continua.py` → tools/
- ✅ Create `tools/tension/` for tension routines

**Phase 3: Organize Configs (COMPLETED 2026-01-08)**
- ✅ Create `config/` directory
- ✅ Move `aoi_config.json` → config/
- ✅ Move `camera_calibration.json` → config/
- ✅ Update config_manager.py paths

**Phase 4: Organize Documentation (COMPLETED 2026-01-08)**
- ✅ Move `PLANO_TESTES.md` → docs/guides/test_implementation_plan.md
- ✅ Move `TESTING.md` → docs/guides/testing_guide.md
- ✅ Move `RELATORIO_CLIENTE_3_SEMANAS.md` → docs/meetings/
- ✅ Move `RELATORIO_IMPLEMENTACAO_3_SEMANAS.md` → docs/reports/
- ✅ Organize docs/ with purpose-based subdirectories

**Phase 5: Optional src/ Restructure (DEFERRED)**
- Consider moving to `src/` layout for better packaging
- Requires updating all imports across codebase
- Use if project becomes distributable package

### Enforcement Guidelines

**When adding new files:**
1. **Ask yourself:** "Is this a utility script?" → Put in `tools/`
2. **Ask yourself:** "Is this configuration?" → Put in `config/`
3. **Ask yourself:** "Is this documentation?" → Put in `docs/`
4. **Ask yourself:** "Is this a test?" → Put in `tests/`

**Code review checklist:**
- [ ] No .py files in root (except main.py)
- [ ] No .json configs in root (except build configs)
- [ ] No documentation in root (except README.md, CLAUDE.md)
- [ ] Build artifacts in .gitignore
- [ ] Tests properly marked (unit/integration/slow/hardware)
- [ ] All imports use absolute paths from project root

### References

- **Python Project Structure:** https://docs.python-guide.org/writing/structure/
- **Testing Best Practices:** docs/guides/testing_guide.md
- **Git Ignore Patterns:** .gitignore
- **Current Analysis:** See session 2026-01-08 in docs/history/
- **Organization Standards:** PROJECT_ORGANIZATION_GUIDELINES.md

---

## Domain-Specific Directories

This project contains several domain-specific directories that deviate from generic standards due to the industrial nature of the application:

### `tension_routines/`
**Purpose:** Domain-specific utilities for tension measurement workflows
**Contains:** Custom routines for specific tension testing scenarios
**Status:** Accepted (domain-specific exception to standards)

### `programas_teste/`
**Purpose:** PLC test programs for hardware validation
**Contains:** Test programs for Delta PLC movement validation
**Status:** Accepted (hardware-specific exception)
**Note:** Could be moved to `tests/fixtures/` if purely for testing, or `config/plc_programs/` if production programs

### `map_programs/`
**Purpose:** Mosaic capture configurations for image stitching
**Contains:** Grid layout configurations for mosaic generation
**Status:** Legacy (consider moving to `config/map_programs/`)
**Recommendation:** Move to `config/map_programs/` for consistency

### `recipes/`
**Purpose:** Stencil recipe definitions with acceptance criteria
**Contains:** JSON files with tension and inspection thresholds
**Status:** Accepted (domain data - stays in root per project convention)

### `Projetos/` (Portuguese)
**Purpose:** User test projects with captured images
**Contains:** Test data from practical validation sessions
**Status:** Temporary user data (should be in .gitignore or moved to `data/projects/`)

### `poc_gerber/`
**Purpose:** Proof of Concept for standalone Gerber file viewer
**Contains:** Experimental Gerber viewer with PyQt6 GUI
**Status:** Accepted (POC/experimental code - separate from main codebase)
**Note:** May evolve into separate product or be integrated later

---

## Next Steps (From Project Documentation)

**Priority: CRITICAL - Practical Validation**
- Test complete workflow with real stencil hardware
- Validate fiducial alignment accuracy in production conditions
- Optimize thresholds based on real-world inspection results
- Create operator manual and training materials

**Priority: HIGH - Production Readiness**
- Implement automated backup system (SQLite + configs)
- Create comprehensive operator documentation
- Validate FOV calibration with physical standard

**Priority: MEDIUM - Infrastructure**
- Complete SQLite migration for better performance at scale
- Add error recovery and retry logic for network/hardware failures
- Create requirements.txt for dependency management

**Priority: LOW - Future Enhancements**
- REST API for MES/ERP integration
- Dashboard with statistics and trend analysis
- ML-based failure prediction

**See Also:**
- [docs/history/BACKLOG.md](docs/history/BACKLOG.md) - Detailed task backlog with priorities
- [docs/history/ROADMAP_DESENVOLVIMENTO.md](docs/history/ROADMAP_DESENVOLVIMENTO.md) - Phase-by-phase development history
- [docs/history/CHANGELOG_2025-12-12.md](docs/history/CHANGELOG_2025-12-12.md) - Recent fixes and improvements
- [docs/history/NOTAS_TECNICAS.md](docs/history/NOTAS_TECNICAS.md) - Technical notes on code reuse from ADESIVADORA
- [docs/history/CORRECOES_FOV_CALIBRATION.md](docs/history/CORRECOES_FOV_CALIBRATION.md) - FOV calibration correction details
- [docs/history/CROSSHAIR_CONFIG.md](docs/history/CROSSHAIR_CONFIG.md) - Crosshair configuration guide
- [docs/history/GUIA_MIGRACAO_SQLITE.md](docs/history/GUIA_MIGRACAO_SQLITE.md) - SQLite migration guide
- [docs/guides/testing_guide.md](docs/guides/testing_guide.md) - Testing best practices
- [docs/guides/test_implementation_plan.md](docs/guides/test_implementation_plan.md) - Test implementation roadmap
- [docs/architecture/ANALISE_INTEGRACAO_MOVEMENT_CONTROLS.md](docs/architecture/ANALISE_INTEGRACAO_MOVEMENT_CONTROLS.md) - Movement controls integration analysis
- [docs/reports/RELATORIO_IMPLEMENTACAO_3_SEMANAS.md](docs/reports/RELATORIO_IMPLEMENTACAO_3_SEMANAS.md) - 3-week implementation report
- [docs/meetings/RELATORIO_CLIENTE_3_SEMANAS.md](docs/meetings/RELATORIO_CLIENTE_3_SEMANAS.md) - 3-week client report
