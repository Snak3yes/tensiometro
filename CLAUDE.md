# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Tensiometro** is an industrial Automated Optical Inspection (AOI) system for solder paste stencil quality control in SMT manufacturing. The system performs:
- Surface tension measurement using AS-120N tensiometer (serial RS-232)
- Visual inspection of stencil openings for cleanliness validation
- CNC movement control via Delta PLC (Modbus TCP)
- Individual stencil traceability with SQLite persistence and historical trend analysis
- PDF report generation with charts and statistics

**Development Status:** ~99% complete - in practical validation phase with hardware

**Version:** 0.4.0 (see aoi_lib/__init__.py)

**Technology:** Python 3.x + PyQt6 GUI + OpenCV + Modbus TCP + SQLite

**Key Statistics (2026-01-15):**
- Total Python files: 245
- Total lines of code: ~59,516
- aoi_lib: 59 files, ~21,627 lines (core business logic)
- consumo_lib: 125 files, ~37,889 lines (modular GUI)

**Development Philosophy:** SOLID principles, TDD, incremental progress with checkpoints, documentation as source of truth. See `conductor/workflow.md` for complete development protocol.

---

## Running the Application

### Main Application Entry Point
```bash
# Using virtual environment (recommended)
.venv/Scripts/python.exe main.py

# Or using module
python -m consumo_lib.main_window
```

### Hardware Dependencies
The application requires hardware for full functionality:
- **PLC:** Delta CLP series (Modbus TCP at 192.168.1.5:502)
- **Tensiometer:** AS-120N (Serial RS-232, COM port varies, 2400 baud)
- **Camera:** USB camera compatible with OpenCV

The application degrades gracefully without hardware - UI continues to work but hardware-dependent features are disabled.

### Testing

**Run all tests:**
```bash
# Windows
tests\scripts\run_tests.bat

# Or using pytest directly
pytest tests/ -v

# Fast mode (excludes slow/hardware tests)
pytest tests/ -v -m "not slow and not hardware"

# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v
```

**Test coverage:**
```bash
# Run with coverage
pytest tests/ --cov=aoi_lib --cov=consumo_lib --cov-report=html:htmlcov --cov-report=term-missing

# Open coverage report (Windows)
start htmlcov\index.html
```

**Single test:**
```bash
# Run specific test file
pytest tests/unit/test_fov_calibration.py -v

# Run specific test
pytest tests/unit/test_fov_calibration.py::TestFOVCalibration::test_get_fov_at_z -v
```

### Environment Setup
```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Core dependencies:**
- PyQt6 (GUI)
- opencv-python (cv2)
- numpy
- pymodbus (Modbus TCP)
- pyserial (RS-232)
- reportlab (PDF generation)
- matplotlib (charts)
- pytest (testing)

---

## High-Level Architecture

### Two-Package Architecture

The codebase is split into two complementary packages:

```
tensiometro/
├── aoi_lib/              # Core business logic (hardware layer)
│   └── 59 files, ~21,627 lines
│
├── consumo_lib/          # Modular GUI application (presentation layer)
│   └── 125 files, ~37,889 lines
│
└── main.py               # Entry point (34 lines)
```

### aoi_lib - Core Business Logic

**Purpose:** Hardware abstraction, business logic, data models, and services. NO GUI code.

**Key Modules:**

**Hardware Layer (External Interfaces):**
- `plc_axis_controller.py` - Modbus TCP communication with Delta PLC for 3-axis CNC control
  - Methods: `move_absolute()`, `move_relative()`, `jog_start()`, `wait_for_idle()`, `read_position()`
  - X/Y interpolation: Both axes share coil M1050 (NOT separate coils)
  - Addresses: X (M1000, D3000), Y (M500, D3200), Z (M1500, D3400)
- `camera_controller.py` - OpenCV USB camera interface with real-time preview
- `tensiometer/` - AS-120N tension sensor serial communication (refactored 2026-01-14)
  - `models.py` - Data structures (GridPoint, TensionMeasurement, GridParameters, MeasurementSession)
  - `serial_protocol.py` - RS-232 protocol handler (2400 baud, 9-byte frame)
  - `measurement_service.py` - Business logic (100% testable without PyQt6)
  - `measurement_orchestrator.py` - Facade for complete measurement workflow

**Computer Vision Pipeline:**
- `fiducial_alignment.py` - Template matching for reference mark detection and transformation calculation
- `gerber_parser.py` - RS-274X Gerber file parsing with automatic fiducial candidate detection
- `gerber_renderer.py` - Converts Gerber vector data to OpenCV masks for inspection
- `stencil_inspector.py` - Visual inspection engine with threshold-based analysis (OK/PARTIAL/BLOCK)

**Data & Configuration:**
- `stencil_tracker.py` - Data models (Stencil, TensionRecord, InspectionRecord) with JSON persistence
- `stencil_database.py` - SQLite layer (partial migration from JSON)
- `recipe_manager.py` - Configuration management for different stencil models with acceptance criteria
- `config_manager.py` - Manages `config/aoi_config.json` (CNC params, connection settings, FOV calibration)

**Gerber Core (MVC Architecture):**
- `gerber_core/models/gerber_model.py` - Model layer for Gerber data management
- `gerber_core/controllers/gerber_controller.py` - Controller layer with Command Pattern
- `gerber_core/commands/edit_commands.py` - Commands for GerberObject editing
- `gerber_core/parser.py` - Legacy Gerber parser (being migrated)

**Report Generation:**
- `report_generator.py` (REFACTORED 2026-01-15) - PDF generation with SOLID architecture
  - Services: PDFGenerator, ChartGenerator, StatisticsCalculator, ReportLayoutManager
  - Builders: TensionReportBuilder, StencilHistoryReportBuilder, InspectionReportBuilder
  - Facade: ReportGenerator with shared services pattern
  - SOLID Score: 96/100 (from 45/100 before refactoring)

### consumo_lib - Modular GUI Application

**Purpose:** PyQt6 GUI, presentation logic, user workflows. NO business logic (delegates to aoi_lib).

**Entry Point:**
- `main_window.py` (1,060 lines) - Main orchestrator that coordinates all tabs and modules

**Modular Structure (125 files):**

```
consumo_lib/
├── tabs/              # Tab implementations (8 files)
│   ├── CNCControlTab
│   ├── TensionTab
│   ├── InspectionTab
│   ├── MapTab
│   ├── TrackingTab
│   └── TreeViewTab
│
├── widgets/           # Reusable UI components (25 files)
│   ├── engenharia/    # Engineering Wizard (7 widgets)
│   ├── stencil/       # Stencil management (3 widgets)
│   └── [other widgets]
│
├── dialogs/           # Dialog windows (26 files)
│   ├── tension/       # TensionMeasurementDialog (refactored 2026-01-14)
│   ├── stencil/       # 5 CRUD dialogs
│   └── [other dialogs]
│
├── controllers/       # Hardware control wrappers (14 files)
│   ├── MovementController
│   ├── CameraController
│   └── [other controllers]
│
├── coordinators/      # Complex workflow orchestration (8 files)
│   ├── SetupCoordinator
│   ├── InspectionCoordinator
│   ├── OperatorWorkflow
│   └── [other coordinators]
│
├── managers/          # Business logic wrappers (9 files)
│   ├── RecipeManager
│   ├── StencilManager
│   └── [other managers]
│
├── services/          # Business services (6 files)
│   ├── MovementService
│   ├── ClickToMoveService
│   └── [other services]
│
├── handlers/          # Event handling (5 files)
│   ├── KeyboardHandler
│   ├── MenuHandler
│   └── [other handlers]
│
├── threads/           # Worker threads (5 files)
│   ├── MapGenerator
│   ├── SequenceRunner
│   └── [other threads]
│
├── ui_builders/       # UI construction helpers (2 files)
│   └── utils/         # Utility functions (10 files)
│
└── models/            # Data models (5 files)
    └── engineering/   # Engineering program models
```

### Key Architectural Patterns

**Dependency Flow:**
```
main_window.py (orchestrator only)
  ├── consumo_lib/coordinators/ (workflow orchestration)
  │   ├── consumo_lib/managers/ (business logic wrappers)
  │   ├── consumo_lib/controllers/ (hardware control wrappers)
  │   ├── consumo_lib/services/ (business services)
  │   └── consumo_lib/handlers/ (event handling)
  ├── consumo_lib/tabs/ (UI tabs)
  │   ├── consumo_lib/widgets/ (UI components)
  │   ├── consumo_lib/dialogs/ (dialogs)
  │   └── consumo_lib/threads/ (worker threads)
  └── aoi_lib/ (CORE BUSINESS LOGIC)
      ├── tensiometer/ (measurement services)
      ├── plc_axis_controller.py (hardware layer)
      ├── camera_controller.py (hardware layer)
      ├── fiducial_alignment.py (template matching)
      ├── gerber_parser.py (RS-274X parsing)
      ├── stencil_inspector.py (inspection engine)
      └── [other core modules]
```

**CRITICAL RULE:**
- ✅ Business logic → `aoi_lib/`
- ✅ UI components → `consumo_lib/tabs/` or `consumo_lib/widgets/`
- ✅ Hardware control → `aoi_lib/*_controller.py`
- ❌ NEVER add business logic to `consumo_lib/main_window.py` (it's an orchestrator only)

**SOLID Refactoring History:**
- Phase 1 (2026-01-14): stencil_tension.py → 5 modules, 48 tests, SOLID 96/100
- Phase 2 (2026-01-14): stencil_database.py → 3 repositories (Repository Pattern)
- Phase 3 (2026-01-15): alignment_widget.py → services + DI, 102 tests
- Phase 4 (2026-01-15): mainwindow.py → 735 lines, modularized
- Phase 5A (2026-01-15): report_generator.py → 10 modules, SOLID 96/100

---

## Configuration Files

### Main Configuration
**Location:** `config/aoi_config.json`

**Key sections:**
- `cnc` - CNC parameters (system_type: "corexy", steps_per_unit: 80.0, max_feed rates)
- `connections` - Hardware connections (plc_host, plc_port, auto_connect flags)
- `calibration` - FOV calibration data (pulses_per_rev: 800.0, fuso_pitch: 0.0)
- `movement` - Default movement parameters (step_size: 5.0, feed_rate: 800.0)
- `mosaic` - Mosaic generation settings

**Loading in code:**
```python
from aoi_lib.config_manager import AOIConfigManager
config_mgr = AOIConfigManager()
config = config_mgr.load_config()
```

### Camera Calibration
**Location:** `config/camera_calibration.json`

Stores FOV calibration data for pixel-to-millimeter conversion.

### Recipe Definitions
**Location:** `recipes/*.json`

Configuration files for different stencil models with acceptance criteria.

---

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
  2. wait_for_idle (with tolerance)
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

---

## Domain-Specific Technical Details

### Coordinate Systems

**CNC Coordinates (Pulse-based):**
- Pulse-to-mm conversion: `pulses_per_mm = pulses_per_rev / fuso_pitch`
- Default: 800 pulses/rev ÷ 10mm/rev (from aoi_config.json) = 80 pulses/mm
- Movement uses absolute positioning (G90) or relative (G91)
- **CRITICAL:** X and Y share coil M1050 for interpolation (NOT separate coils)

**Image Coordinates vs CNC Coordinates:**
- Image: (0,0) at top-left, Y increases downward
- CNC: Y typically increases upward (toward operator)
- `video_click_to_movement()` in fov_calibration.py handles the conversion
- **CRITICAL:** Y-axis inversion is handled with `invert_y` parameter

**Camera FOV (Fixed):**
- Unlike ADESIVADORA (movable camera), Tensiometro has fixed camera
- FOV calibration only needs one measurement (not two at different Z heights)
- `CameraFOVConverter.get_fov_at_z()` returns constant FOV regardless of Z

### Hardware Communication Protocols

**Tensiometer Serial Protocol (AS-120N):**
- Request: Single byte `0x20`
- Response: 9 bytes starting with `0x10`, byte[2] = `0x19`
- Baud: 2400, 8N1, DTR=0, RTS=0
- Frame format: Custom (see `aoi_lib/tensiometer/serial_protocol.py`)

**Modbus TCP Addressing:**
- Default PLC: 192.168.1.5:502 (Delta AS series)
- Movement uses absolute positioning (G90) or relative (G91)
- **X/Y Interpolation:** Axes X and Y share coil M1050 (NOT separate coils)
- See `plc_axis_controller.py` for complete register mapping

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

### Quality Standards

**Aperture Classification (Stencil Inspection):**
- **OK:** Aperture ≥90% clear (free from solder paste residue)
- **PARTIAL:** Aperture 70-90% clear (requires cleaning attention)
- **BLOCKED:** Aperture <70% clear (must clean before next print)
- Based on recipe's `InspectionThresholds.ok_threshold` and `partial_threshold`

---

## Common Development Patterns

### Adding New Features

**1. Planning Phase:**
- Read relevant CLAUDE.md sections (Hardware Integration, Data Models, Data Flows)
- Check BACKLOG.md or `conductor/tracks.md` for existing related tasks
- Identify which aoi_lib modules will be affected
- Check if new configuration needed in aoi_config.json

**2. Implementation Phase:**
- Create new module in `aoi_lib/` (NEVER extend consumo_lib modules directly)
- Follow existing patterns: dataclass models + manager/controller class
- Use logging: `logger = logging.getLogger(__name__)`
- Add type hints consistently
- For new UI: create widget in `consumo_lib/widgets/` or tab in `consumo_lib/tabs/`

**3. Integration Phase:**
- Import from aoi_lib in consumo_lib if needed
- Add menu item via MenuHandler (consumo_lib/handlers/menu_handler.py)
- Connect signals using existing pattern (QThread + pyqtSignals)
- Test with hardware if applicable

**4. Documentation Phase:**
- Update CLAUDE.md if adding new concepts
- Add inline docstrings to new classes (Google style)
- Update CHANGELOG if behavior changes

**CRITICAL: Code Organization Rules**
- ✅ Business logic → `aoi_lib/`
- ✅ UI components → `consumo_lib/tabs/` or `consumo_lib/widgets/`
- ✅ Hardware control → `aoi_lib/*_controller.py`
- ❌ NEVER add business logic to `consumo_lib/main_window.py` (it's an orchestrator only)

### Error Handling Patterns

**Hardware Connection Errors - Pattern: Graceful Degradation**
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

**Serial Communication Errors - Pattern: Retry + Timeout**
Always return safe default ("0") on error, never raise:
```python
def read_tension_value(self) -> str:
    if not self.is_connected:
        self.last_error = "Tensiômetro não conectado"
        return "0"  # Safe default
    # ... decode and return value
```

**Thread Safety (PyQt6) - Pattern: Signals, Not Direct UI Updates**
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

---

## Module Import Patterns

### From aoi_lib (Core Business Logic)

**Recommended imports:**
```python
# Main controllers
from aoi_lib import (
    CNCAOIController,
    PLCAxisController,
    CameraController,
    StencilTracker, Stencil, TensionRecord, InspectionRecord,
    StencilDatabase, migrate_json_to_sqlite
)

# Individual modules
from aoi_lib.fov_calibration import FOVCalibration, CameraFOVConverter
from aoi_lib.recipe_manager import RecipeManager
from aoi_lib.fiducial_alignment import FiducialAlignment
from aoi_lib.gerber_parser import GerberParser
from aoi_lib.stencil_inspector import StencilInspector

# Tensiometer module (refactored 2026-01-14)
from aoi_lib.tensiometer import (
    MeasurementOrchestrator,
    TensiometerSerialManager,
    GridCalculationService,
    MeasurementAnalysisService,
    GridPoint,
    TensionMeasurement,
    GridParameters
)

# Gerber Core (refactored 2026-01-14)
from aoi_lib.gerber_core.models import GerberObject, GerberModel
from aoi_lib.gerber_core.controllers import GerberController
from aoi_lib.gerber_core.commands import create_edit_command
```

### From consumo_lib (Modular GUI)

**Main window (orchestrator):**
```python
from consumo_lib.main_window import AOIControllerApp
```

**Tabs:**
```python
from consumo_lib.tabs import (
    CNCControlTab, TensionTab, InspectionTab, MapTab,
    TrackingTab, TreeViewTab
)
```

**Dialogs:**
```python
# Tension measurement dialog (refactored 2026-01-14)
from consumo_lib.dialogs.tension import TensionMeasurementDialog

# Stencil management
from consumo_lib.dialogs.stencil import (
    StencilManagerDialog,
    StencilCreateDialog,
    StencilEditDialog
)

# Engineering Wizard (2026-01-13)
from consumo_lib.dialogs import EngineeringWizardDialog
```

**Services, Coordinators, Managers:**
```python
from consumo_lib.services import (
    MovementService, ClickToMoveService,
    SequenceExecutionService, ResourceManager
)

from consumo_lib.coordinators import (
    SetupCoordinator, InspectionCoordinator,
    OperatorWorkflow, EngineeringHardwareCoordinator
)

from consumo_lib.managers import (
    RecipeManager, StencilManager, InspectionManager,
    ReportManager, RoleManager, SessionLogger
)
```

---

## Important Development Notes

### SOLID Refactoring Status

**Completed Tracks (2026-01-14 to 2026-01-15):**
- ✅ Phase 1: stencil_tension.py → 5 modules (2,368 lines), 48 tests
- ✅ Phase 2: stencil_database.py → 3 repositories (Repository Pattern)
- ✅ Phase 3: alignment_widget.py → services + DI, 102 tests
- ✅ Phase 4: mainwindow.py → 735 lines, modularized
- ✅ Phase 5A: report_generator.py → 10 modules, SOLID 96/100

**Active Track:**
- 🔄 Phase 2: SOLID Refactoring (9 files, 4-6 weeks)
  - Target files: mainwindow.py, plc_axis_controller.py, report_generator.py, recipe_dialogs.py, etc.
  - Goals: SOLID score 72/100 → 85+/100, eliminate files >1000 lines
  - See `conductor/tracks/solid_refactoring_phase2_20260114/`

### Legacy Code and Known Issues

**SignalAggregator Removed (2026-01-14):**
- `consumo_lib/handlers/signal_aggregator.py` (1,192 lines) removed
- Replaced by `setup_ui_handlers()` pattern in main_window.py

**POC Gerber Viewer:**
- Located in `poc_gerber/` (formerly `testes_gerber/`)
- Experimental standalone Gerber file viewer
- NOT part of main application (separate product candidate)

**Repository Size:**
- Currently ~2.0 GB due to large .rar files in Git history
- Needs cleanup with BFG or git-filter-repo

### Configuration Management

**Auto-Connect Features (enabled 2026-01-05):**
- `auto_connect_plc: true` in aoi_config.json
- `auto_connect_camera: true` in aoi_config.json
- Hardware connects automatically on application startup

**Default Hardware Settings:**
- PLC: 192.168.1.5:502 (Delta AS series)
- Steps per unit: 80.0 (from 800 pulses/rev ÷ 10mm/rev)
- System type: "corexy"

---

## Testing Without Hardware

### PLC Testing
Cannot easily mock - use real PLC or skip PLC-dependent tests.

### Tensiometer Testing
Use `tools/Leitura_Continua.py` for standalone serial testing:
```bash
python tools/Leitura_Continua.py COM3
```

### Camera Testing
Test with video file or image sequence instead of real camera.

### Gerber Testing
Use files in `poc_gerber/` with standalone viewer.

---

## Project Organization Standards

**Reference:** `PROJECT_ORGANIZATION_GUIDELINES.md` (if exists)

**Directory Structure Principles:**
- Root: Only entry point (main.py), essential guides (README.md, CLAUDE.md)
- `aoi_lib/`: Core business logic
- `consumo_lib/`: Modular GUI application
- `tests/`: Test suite (unit/, integration/, fixtures/)
- `tools/`: Development utilities
- `config/`: Configuration files
- `docs/`: Documentation (guides/, architecture/, reports/)
- `conductor/`: Development workflow and tracks
- `archive/`: Archived code and completed tracks

**Build Artifacts in .gitignore:**
- htmlcov/, .coverage, coverage.xml
- .pytest_cache/
- __pycache__/, *.pyc

**Never Commit:**
- User data (data/projects/)
- Generated reports (reports/)
- Build artifacts
- Virtual environment (.venv/)

---

## Debugging Workflow

### Enable Debug Logs
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or add to aoi_config.json:
# "logging": {
#   "level": "DEBUG",
#   "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
# }
```

### Key Log Locations
- PLC connection/movement: `aoi_lib/plc_axis_controller.py` (search "🎯" or "DEBUG PLC")
- Tensiometer serial: `aoi_lib/tensiometer/serial_protocol.py` (search "read_tension_value")
- FOV conversion: `aoi_lib/fov_calibration.py` (search "Coeficientes FOV")
- Fiducial alignment: `aoi_lib/fiducial_alignment.py` (search "Template matching")
- Inspection: `aoi_lib/stencil_inspector.py` (search "Inspecting aperture")

### Common Debugging Commands

**Check PLC connection:**
```python
plc.is_connected  # Returns bool
plc.read_position('X')  # Returns position in pulses
plc.machine_status  # Returns "Idle", "Run", or "Alarm"
```

**Check camera:**
```python
camera.is_connected
camera.frame_width, camera.frame_height
camera.last_error
```

**Check tensiometer:**
```python
tensio.is_connected
tensio.last_error
```

**Check FOV calibration:**
```python
from aoi_lib.fov_calibration import CameraFOVConverter
converter = CameraFOVConverter(calibration_data)
converter.get_fov_at_z(0)  # Returns (width_mm, height_mm)
```

---

## References

**Development Workflow:**
- `conductor/workflow.md` - Complete TDD and development protocol
- `conductor/product-guidelines.md` - Product guidelines
- `conductor/tech-stack.md` - Technology stack details

**Documentation:**
- `README.md` - Project overview
- `docs/history/BACKLOG.md` - Detailed task backlog
- `docs/history/CHANGELOG_2025-12-12.md` - Recent fixes and improvements
- `docs/architecture/` - System design documents
- `docs/reports/` - Technical reports

**SOLID Refactoring:**
- `conductor/tracks/solid_refactoring_phase2_20260114/` - Active refactoring track
- `docs/reports/SOLID_ANALYSIS_REPORT.md` - SOLID principles analysis
- `docs/guides/SOLID_PHASE1_MIGRATION_GUIDE.md` - Migration guide for Phase 1

**Completed Tracks:**
- `conductor/archive/solid_refactoring_phase1_20260114/`
- `conductor/archive/solid_refactoring_phase5_20260115/`
- `conductor/archive/refactor_large_files_20260113/`

---

**Last Updated:** 2026-01-15
**Version:** 0.4.0
**Development Philosophy:** SOLID principles, TDD, incremental progress with checkpoints
