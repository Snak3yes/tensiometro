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

**Latest Updates (2026-01-05):**
- **Project Reorganization:** Restructured project root, moved documentation to `docs/`, archived test files to `archive/`
- **POC Gerber:** Renamed `testes_gerber/` → `poc_gerber/` (Proof of Concept Gerber viewer)
- **Auto-Connect PLC:** Enabled `auto_connect_plc: true` in `aoi_config.json` for automatic PLC connection on startup
- **Bug Fixes:**
  - Fixed import path from `testes_gerber` to `poc_gerber` in `gerber_parser.py`
  - Fixed `log` undefined error in `fiducial_alignment_widget.py`
  - Fixed duplicate movement bug in POC Gerber viewer `_move_objects()` method
  - Corrected obround geometry implementation (rectangle + semi-circles per Gerber spec)
  - Added robust validation to Gerber parser functions
- **Branch Strategy:** Migrated from `master` to `main` as primary branch
- **SSH Configuration:** SSH keys properly configured for passwordless Git operations
- **Repository Size:** Currently ~1.96 GB (needs cleanup of large .rar files from history)

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
# No requirements.txt exists - dependencies are:
# - PyQt6 (GUI)
# - opencv-python (cv2)
# - numpy
# - pymodbus (Modbus TCP)
# - pyserial (RS-232)
# - reportlab (PDF generation)
# - matplotlib (charts)
```

### No Formal Test Suite
This project does not have automated tests. Testing is done through practical validation with real hardware (PLC, tensiometer, USB camera). The `test_fov_corrections.py` file is an exception used for validating FOV calibration logic.

### Git Repository Status
- **Primary Branch:** `main` (migrated from `master` on 2026-01-05)
- **Active Branches:** `main`, `clp`, `clp-release`
- **Remote:** `git@github.com:RONALDBUZAGLO/tensiometro.git` (SSH configured)
- **Repository Size:** ~1.96 GB (contains large .rar files in history - needs cleanup)
- **Last Major Update:** 2026-01-05 - Project reorganization and bug fixes

### Module Import Pattern
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
# etc.
```

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
- **Entry Point:** `poc_gerber/aperture_macro.py`
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

### Main Application
- **consumo_lib.py** (6,245 lines) - PyQt6 main window with tabs:
  - CNC Control: Manual jogging, camera preview with click-to-move
  - Tension Measurement: Grid-based sampling with heatmap visualization
  - Stencil Inspection: Fiducial alignment, Gerber overlay, visual analysis
  - Tracking & Reports: Stencil history, trend analysis, PDF generation

## Key Technical Details

### Coordinate System & Movement
- **Pulse-to-MM Conversion:** Configured in `aoi_config.json` (`pulses_per_rev`, `fuso_pitch`)
- **Movement Modes:** Absolute positioning (G90) and relative (G91) via Modbus registers
- **Soft Limits:** Defined per axis in [aoi_lib/plc_axis_controller.py](aoi_lib/plc_axis_controller.py:~250)
- **Speed Control:** Separate speeds for jogging, inspection moves, and tension measurement

### FOV Calibration System
- **FOVCalibration** ([aoi_lib/fov_calibration.py](aoi_lib/fov_calibration.py)) - Pixel-to-millimeter conversion at different Z heights
- **Click-to-Move:** Camera preview allows clicking points to automatically center them (uses FOV conversion)
- **Calibration Data:** Stored in `camera_calibration.json`

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
consumo_lib/    # Main GUI application (refactored from 6,245 to 589 lines)
```

### Known Issues & Quirks
1. **Repository Size:** Currently ~1.96 GB due to large .rar files in Git history (needs cleanup with BFG or git-filter-repo)
2. **Refactoring Completed:** `consumo_lib.py` was successfully refactored from 6,245 to 589 lines (2026-01-05)
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
- See plc_axis_controller.py for register mapping

### Critical Sections to Preserve
- **Serial Protocol Decoding:** [aoi_lib/stencil_tension.py](aoi_lib/stencil_tension.py:~200-250) - 9-byte frame parsing is hardware-specific for AS-120N tensiometer (2400 baud, 8N1)
- **Modbus Register Mapping:** [aoi_lib/plc_axis_controller.py](aoi_lib/plc_axis_controller.py:~50-100) - PLC-specific addresses for Delta CLP series
- **FOV Conversion Logic:** [aoi_lib/fov_calibration.py](aoi_lib/fov_calibration.py:~150-250) - Pixel-to-pulse calculations for click-to-move functionality
- **Fiducial Alignment Transform:** [aoi_lib/fiducial_alignment.py](aoi_lib/fiducial_alignment.py) - Template matching for Gerber-to-image alignment

### Common Modification Patterns
When adding new features:
1. **Add to aoi_lib/** as separate module (don't extend consumo_lib.py further - it's already 6,245 lines)
2. **Update aoi_config.json schema** if adding configuration
3. **Add menu item** in consumo_lib.py setupMenuBar() method (around line 1200-1400)
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
- Refactor consumo_lib.py into smaller modules (6,245 lines is too large)
- Add error recovery and retry logic for network/hardware failures

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
