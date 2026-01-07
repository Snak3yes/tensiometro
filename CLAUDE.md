# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Tensiometro** is an industrial Automated Optical Inspection (AOI) system for solder stencil quality control in SMT manufacturing. The system performs:
- Surface tension measurement using AS-120N tensiometer (serial RS-232)
- Visual inspection of stencil openings for cleanliness validation
- CNC movement control via Delta PLC (Modbus TCP)
- Individual stencil traceability with historical trend analysis
- PDF report generation

**Development Status:** ~99% complete - in practical validation phase with hardware

**Version:** 0.4.0 (see aoi_lib/__init__.py)

**Recent Changes (2025-12-12):**
- Simplified FOV calibration for fixed camera (removed dual-Z-height logic)
- Fixed Y-axis movement inversion bug (click-to-move now works correctly)
- Added crosshair customization dialog
- Fixed FOV calibration save bug (ConfigAdapter keyword argument)

**Latest Updates (2026-01-07):**
- **Project Reorganization:** Restructured project root, moved documentation to `docs/`, archived test files to `archive/`
- **Modular Refactoring:** `consumo_lib.py` refactored from 6,245 to 592 lines as modular package structure
- **POC Gerber:** Renamed `testes_gerber/` → `poc_gerber/` (Proof of Concept Gerber viewer)
- **Auto-Connect PLC:** Enabled `auto_connect_plc: true` in `aoi_config.json` for automatic PLC connection on startup
- **Bug Fixes:**
  - Fixed import path from `testes_gerber` to `poc_gerber` in `aoi_lib/gerber_parser.py`
  - Fixed `log` undefined error in `fiducial_alignment_widget.py`
  - Fixed duplicate movement bug in POC Gerber viewer `_move_objects()` method
  - Corrected obround geometry implementation (rectangle + semi-circles per Gerber spec)
  - Added robust validation to Gerber parser functions
  - Fixed Modbus interpolation addressing (X/Y use shared coil M1050)
  - Added extensive logging to PLC movement and wait_for_idle
- **Branch Strategy:** Migrated from `master` to `main` as primary branch
- **SSH Configuration:** SSH keys properly configured for passwordless Git operations
- **Repository Size:** Currently ~2.0 GB (needs cleanup of large .rar files from history)

## Commands

### Running the Application
```bash
# Main application (Windows Python, typically in .venv)
.venv/Scripts/python.exe main.py

# Alternative: run as module
python -m consumo_lib.main_window

# Mosaic builder utility (standalone)
python mosaic_builder.py

# Camera calibration utility
python camera_calibration.py

# FOV corrections validation test
python test_fov_corrections.py

# Continuous tensiometer reading utility
python Leitura_Continua.py [COM_PORT]
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
pip install PyQt6 opencv-python numpy pymodbus pyserial reportlab matplotlib
```

### Test Suite
**Limited Unit Testing:** `test_fov_corrections.py` for FOV calibration validation only.
Primary testing is through practical validation with real hardware (PLC, tensiometer, USB camera).

### Git Repository Status
- **Primary Branch:** `main` (migrated from `master` on 2026-01-05)
- **Active Branches:** `main`, `clp`, `clp-release`
- **Remote:** `git@github.com:RONALDBUZAGLO/tensiometro.git` (SSH configured)
- **Repository Size:** ~2.0 GB (133 Python files, 42,618 lines of code)
- **Last Major Update:** 2026-01-07 - PLC movement fixes and extensive logging

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
from aoi_lib.stencil_tension import TensiometerSerialManager
from aoi_lib.recipe_manager import RecipeManager
from aoi_lib.fiducial_alignment import FiducialAlignment
from aoi_lib.gerber_parser import GerberParser
from aoi_lib.gerber_renderer import GerberRenderer
from aoi_lib.stencil_inspector import StencilInspector
```

**From consumo_lib (Modular GUI):**
```python
# Main window (orchestrator)
from consumo_lib.main_window import MainWindow

# Tabs
from consumo_lib.tabs import CNCTab, TensionTab, InspectionTab, TrackingTab

# Controllers
from consumo_lib.controllers import MovementController, CameraController

# Managers
from consumo_lib.managers import RecipeManagerWrapper, StencilManagerWrapper

# Coordinators
from consumo_lib.coordinators import SetupCoordinator, InspectionCoordinator
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
- Tensiometer serial: `aoi_lib/stencil_tension.py` (search "read_tension_value")
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
- **TensiometerSerialManager** ([aoi_lib/stencil_tension.py](aoi_lib/stencil_tension.py)) - RS-232 serial protocol (2400 baud, 9-byte frame) for AS-120N tension sensor
- **CameraController** ([aoi_lib/camera_controller.py](aoi_lib/camera_controller.py)) - OpenCV USB camera interface with real-time preview

### Core Business Logic
- **AOIController** ([aoi_lib/aoi_controller.py](aoi_lib/aoi_controller.py)) - High-level orchestrator integrating CNC movement + camera capture
- **StencilTracker** ([aoi_lib/stencil_tracker.py](aoi_lib/stencil_tracker.py)) - Data models (Stencil, TensionRecord, InspectionRecord) with JSON persistence
- **StencilInspector** ([aoi_lib/stencil_inspector.py](aoi_lib/stencil_inspector.py)) - Visual inspection engine with threshold-based analysis (OK/PARTIAL/BLOCK)
- **RecipeManager** ([aoi_lib/recipe_manager.py](aoi_lib/recipe_manager.py)) - Configuration management for different stencil models with acceptance criteria

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
**consumo_lib/** package - Refactored from monolithic 6,245-line file to modular structure:
- **main_window.py** (592 lines) - PyQt6 main window orchestrator with tabs:
  - CNC Control: Manual jogging, camera preview with click-to-move
  - Tension Measurement: Grid-based sampling with heatmap visualization
  - Stencil Inspection: Fiducial alignment, Gerber overlay, visual analysis
  - Tracking & Reports: Stencil history, trend analysis, PDF generation
- **tabs/** - Tab implementations (CNCControlTab, TensionTab, InspectionTab, TrackingTab)
- **widgets/** - Reusable UI components (CameraPreviewWidget, MovementControlWidget, etc.)
- **controllers/** - Hardware control wrappers (MovementController, CameraControllerWrapper)
- **coordinators/** - Complex workflow orchestration (SetupCoordinator, InspectionCoordinator)
- **managers/** - Business logic wrappers (RecipeManagerWrapper, StencilManagerWrapper)
- **handlers/** - Event handling (KeyboardHandler, MenuHandler, DialogHandler)
- **threads/** - Worker threads (TensionMeasurementThread, MapGeneratorThread)

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
consumo_lib/main_window.py (589 lines - orchestrator only)
  ├── consumo_lib/coordinators/SetupCoordinator (initialization)
  │   ├── consumo_lib/managers/ (RecipeManagerWrapper, StencilManagerWrapper, etc.)
  │   ├── consumo_lib/controllers/ (various UI controllers)
  │   └── consumo_lib/handlers/ (keyboard, menu, dialogs)
  ├── consumo_lib/tabs/ (CNCControlTab, TensionTab, InspectionTab, etc.)
  │   └── consumo_lib/widgets/ (reusable UI components)
  └── aoi_lib/ (CORE BUSINESS LOGIC - ~15,439 lines)
      ├── plc_axis_controller.py (Modbus TCP - hardware layer)
      ├── camera_controller.py (OpenCV - hardware layer)
      ├── stencil_tension.py (Serial RS-232 - hardware layer)
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
# From aoi_config.json: "pulses_per_rev": 1000, "fuso_pitch": 10.0
pulses_per_mm = 1000 / 10.0 = 100.0

# Examples:
position_mm = 50.0
position_pulses = position_mm * pulses_per_mm  # 5000 pulses
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
- **aoi_config.json** - System-wide settings (connection, calibration, UI state)
  - **Important:** Contains `auto_connect_plc: true` (enabled 2026-01-05) for automatic PLC connection
  - Contains `auto_connect_camera: true` for automatic camera connection
  - PLC connection: `plc_host: "192.168.1.5"`, `plc_port: 502`
- **camera_calibration.json** - FOV calibration data
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
aoi_lib/         # Core AOI library
consumo_lib/     # Main GUI application (modular package, 592 lines main_window.py)
```

### Known Issues & Quirks
1. **Repository Size:** Currently ~2.0 GB due to large .rar files in Git history (needs cleanup with BFG or git-filter-repo)
2. **Refactoring Completed:** `consumo_lib.py` was successfully refactored from 6,245 to 592 lines as modular package (2026-01-05)
3. **Legacy Code:** Some references to "ADESIVADORA" project (adhesive dispenser) - code was adapted from that project
4. **Dual Persistence:** Both JSON and SQLite supported - SQLite migration is partial/optional
5. **No requirements.txt:** Project uses `.venv` but no formal dependency declaration file
6. **POC Gerber:** Located in `poc_gerber/` directory, contains experimental Gerber viewer with corrected obround geometry

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
- **Serial Protocol Decoding:** [aoi_lib/stencil_tension.py](aoi_lib/stencil_tension.py:~200-250) - 9-byte frame parsing is hardware-specific for AS-120N tensiometer (2400 baud, 8N1)
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
- [BACKLOG.md](BACKLOG.md) - Detailed task backlog with priorities
- [ROADMAP_DESENVOLVIMENTO.md](ROADMAP_DESENVOLVIMENTO.md) - Phase-by-phase development history
- [CHANGELOG_2025-12-12.md](CHANGELOG_2025-12-12.md) - Recent fixes and improvements
- [NOTAS_TECNICAS.md](NOTAS_TECNICAS.md) - Technical notes on code reuse from ADESIVADORA
- [ANALISE_PROJETO_PROXIMOS_PASSOS.txt](ANALISE_PROJETO_PROXIMOS_PASSOS.txt) - Portuguese project analysis
- [CORRECOES_FOV_CALIBRATION.md](CORRECOES_FOV_CALIBRATION.md) - FOV calibration correction details
- [CROSSHAIR_CONFIG.md](CROSSHAIR_CONFIG.md) - Crosshair configuration guide
- [GUIA_MIGRACAO_SQLITE.md](GUIA_MIGRACAO_SQLITE.md) - SQLite migration guide
