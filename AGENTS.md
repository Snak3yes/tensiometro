# AGENTS.md

## Purpose

This file gives a fast operational map of the `tensiometro` repository for coding agents and maintainers.
It does not replace `CLAUDE.md` or the material under `conductor/`; it is the shortest reliable guide based on the current workspace state.

## Project Snapshot

- Stack: Python 3.13, PyQt6, OpenCV, numpy, pymodbus, pyserial, matplotlib, reportlab
- Entry point: `main.py`
- App type: desktop industrial application for stencil tension measurement and visual inspection
- Hardware involved:
  - Delta PLC over Modbus TCP
  - USB/OpenCV camera
  - AS-120N tensiometer over serial

## Current Top-Level Structure

- `main.py`
  - Starts `QApplication`, initializes the theme manager, and opens `AOIControllerApp`.
- `aoi_lib/`
  - Core domain and hardware-facing layer.
  - Contains PLC control, camera control, Gerber parsing/rendering, stencil tracking, persistence, fiducial alignment, and tensiometer logic.
- `consumo_lib/`
  - GUI and application orchestration layer.
  - Contains main window, tabs, dialogs, widgets, controllers, coordinators, managers, services, factories, and facades.
- `config/`
  - Runtime JSON configuration such as `aoi_config.json` and camera calibration data.
- `assets/`
  - Static assets, currently calibration checkerboards.
- `tools/`
  - Standalone utilities for calibration, mosaic generation, and hardware tests.
- `conductor/`
  - Development-process documentation, tracks, style guidance, and workflow notes.
- `CLAUDE.md`
  - Existing long-form repository guidance.

## Architecture Map

### Application boot

1. `main.py`
2. `consumo_lib.main_window.AOIControllerApp`
3. `consumo_lib.coordinators.setup_coordinator.SetupCoordinator`
4. `consumo_lib.factories.application_components_factory.ApplicationComponentsFactory`
5. Factories create and attach core objects, managers, coordinators, handlers, controllers, and services to the main window

### Core split

- `aoi_lib` should hold business logic and hardware integration.
- `consumo_lib` should hold UI, presentation flow, orchestration, and application wiring.

### Main window status

`consumo_lib/main_window.py` is still the highest-coupling file in the repo, even after refactoring. It acts as a top-level orchestrator and compatibility surface. Prefer adding behavior to the existing controller/coordinator/service layers instead of expanding the main window further unless the change is strictly UI composition.

## Important Modules By Responsibility

### Hardware and domain

- `aoi_lib/aoi_controller.py`
  - Main controller combining PLC motion, camera capture, position management, sequences, and map generation.
- `aoi_lib/plc_axis_controller.py`
  - PLC motion backend.
- `aoi_lib/camera_controller.py`
  - Camera abstraction used by the app.
- `aoi_lib/config_manager.py`
  - JSON-backed configuration manager and settings dialog.
- `aoi_lib/stencil_tracker.py`, `aoi_lib/stencil_database.py`
  - Stencil traceability and historical records.
- `aoi_lib/tensiometer/`
  - Serial protocol, measurement service, thread, and models for tension measurement.
- `aoi_lib/gerber_core/`, `aoi_lib/gerber_parser.py`, `aoi_lib/gerber_renderer.py`
  - Gerber parsing/rendering pipeline.
- `aoi_lib/fiducial_*`
  - Alignment and fiducial matching workflow.

### UI and orchestration

- `consumo_lib/main_window.py`
  - Main application shell.
- `consumo_lib/coordinators/setup_coordinator.py`
  - Bootstraps the application in a strict order.
- `consumo_lib/factories/`
  - Dependency creation and composition.
- `consumo_lib/controllers/`
  - UI-facing workflow controllers.
- `consumo_lib/coordinators/`
  - Cross-component workflows such as inspection and tension measurement.
- `consumo_lib/services/`
  - Reusable application services.
- `consumo_lib/widgets/`, `consumo_lib/dialogs/`, `consumo_lib/tabs/`
  - Presentation layer.
- `consumo_lib/ui/`
  - Theme system, design tokens, and style helpers.

## Key Workflows

### Tension measurement

Primary files:

- `consumo_lib/controllers/tension_measurement_controller.py`
- `consumo_lib/coordinators/tension_coordinator.py`
- `consumo_lib/dialogs/tension/`
- `aoi_lib/tensiometer/`

Notes:

- There is both a dialog-driven workflow and a coordinator abstraction.
- Be careful to confirm which path is actually used by the current UI before refactoring.
- The current dialog/orchestrator flow persists JSON results under `tension_routines/tension_measurement_*.json`.
- Some legacy code paths historically expected `stencil_tension_measurements.json`; treat that filename as compatibility legacy, not the primary storage format.

### Visual inspection

Primary files:

- `consumo_lib/coordinators/inspection_coordinator.py`
- `consumo_lib/utils/main_window/inspection_workflow.py`
- `aoi_lib/stencil_inspector.py`
- `aoi_lib/fiducial_alignment.py`
- `aoi_lib/gerber_*`

Notes:

- Inspection combines Gerber loading, fiducial capture/alignment, image capture, result analysis, and report generation.

### Engineering/setup flows

Primary files:

- `consumo_lib/utils/main_window/engineering_workflow.py`
- `consumo_lib/widgets/engenharia/`
- `consumo_lib/dialogs/engineering_wizard_dialog.py`

## Configuration and Runtime Data

- Main runtime config file: `config/aoi_config.json`
- Calibration file: `config/camera_calibration.json`
- `AOIConfigManager` reads and writes these files directly.

Treat configuration as machine-specific runtime data, not just source code defaults. Do not casually overwrite values such as PLC IP, calibration factors, camera IDs, or authentication defaults unless the task explicitly requires it.

## Testing Reality Check

- `pytest.ini` is present and expects a `tests/` tree.
- In the current workspace snapshot, `tests/` is not present.
- `CLAUDE.md` and `conductor/` describe a broader test suite, but that suite is not currently available in this checkout.

Implication:

- Do not assume tests exist locally.
- If you add or modify behavior, state clearly whether verification was done by static review, targeted manual run, or actual automated tests.

## Practical Rules For Future Changes

1. Prefer changing the smallest layer that owns the behavior.
2. Put business logic in `aoi_lib` or `consumo_lib/services`, not directly in widgets.
3. Use controllers/coordinators/factories that already exist before creating new architectural patterns.
4. Avoid growing `consumo_lib/main_window.py` unless the change is glue code that truly belongs there.
5. Preserve graceful degradation when hardware is unavailable.
6. Keep UI styling aligned with `consumo_lib/ui/` instead of hardcoding ad hoc styles.
7. Treat `tools/` as standalone utilities; production behavior should live in `aoi_lib/` or `consumo_lib/`.
8. Check `CLAUDE.md` and `conductor/workflow.md` when the task touches process, architecture history, or coding conventions.

## Recommended First Files To Read

- `main.py`
- `consumo_lib/main_window.py`
- `consumo_lib/coordinators/setup_coordinator.py`
- `consumo_lib/factories/application_components_factory.py`
- `aoi_lib/aoi_controller.py`
- `aoi_lib/config_manager.py`

## Notes On Repository State

- The repository already contains substantial refactoring scaffolding: factories, facades, services, and coordinators.
- Documentation suggests a more mature test/documentation ecosystem than what is currently visible in the working tree.
- When in doubt, trust the live code in this checkout over historical metrics written in docs.
