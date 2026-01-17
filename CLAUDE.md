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
- Total Python files: 261
- Total lines of code: ~63,326
- aoi_lib: 65 files, ~24,287 lines (core business logic)
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

### Service Layer Architecture (NOVO - Phase 2)

**Propósito:** Separar lógica de negócio de apresentação, tornar código testável sem PyQt6.

**Camadas de Serviços Refatoradas:**

```
aoi_lib/
├── tensiometer/               # Medição de tensão (Phase 1: 96/100)
│   ├── serial_protocol.py      - Protocolo serial RS-232 (2400 baud)
│   ├── measurement_service.py   - Serviço de medição de tensão
│   └── measurement_orchestrator.py - Orquestração de medição
│
├── fiducial_alignment/        # Alinhamento Gerber (Phase 5B: 96/100)
│   ├── fiducial_models.py          - Modelos de dados (FiducialPoint, AlignmentTransform)
│   ├── fiducial_matching_service.py  - Template matching com OpenCV
│   ├── alignment_transform_service.py - Transformações geométricas (translação, rotação, escala)
│   ├── alignment_state_service.py    - Gerenciamento de estado com JSON
│   └── fiducial_alignment_adapter.py  - Adapter para compatibilidade com código legado
│
├── gerber_core/                # Parser Gerber RS-274X (Phase 1: 100/100)
│   ├── models/                    - Modelos de dados (GerberObject, GerberLayer, GerberLayerGroup)
│   ├── controllers/               - Orquestração (GerberController com Command Pattern)
│   └── commands/                  - Commands de edição (EditCircleCommand, EditRectangleCommand, etc.)
│
└── report_generator/            # Geração de relatórios PDF (Phase 5A: 96/100)
│   ├── pdf_generator.py           - Operações PDF de baixo nível
│   ├── chart_generator.py         - Geração de gráficos com Matplotlib
│   ├── statistics_calculator.py   - Cálculos estatísticos (média, desvio padrão)
│   ├── report_layout_manager.py    - Layout e formatação de relatórios
│   ├── services/                  - Serviços compartilhados entre builders
│   └── builders/                  - Builders especializados (TensionReportBuilder, etc.)
│
└── [outros módulos refatorados com Score SOLID ~96/100]
```

**Score SOLID Global:** **97/100** (Excelente)
- S (SRP): 10/10 - Cada módulo tem responsabilidade única
- O (OCP): 9/10 - Extensível via Strategy/Factory/Service patterns
- L (LSP): 10/10 - Substituição preservada em toda arquitetura
- I (ISP): 10/10 - Interfaces focadas (Protocolos com 1-2 métodos)
- D (DIP): 10/10 - Injeção de dependências via construtor

**Relatórios de Refatoração:**
- `docs/reports/SOLID_SCORE_FINAL_PHASE2.md` - Score SOLID final consolidado: 97/100
- `docs/reports/SOLID_PHASE1_VERIFICATION_REPORT.md` - Gerber Core refatorizado (100/100)
- `docs/reports/SOLID_PHASE5_COMPLETION_REPORT.md` - Report Generator refatorizado (96/100)
- `docs/reports/SOLID_REFACTORING_PHASE5B_REPORT.md` - Fiducial Alignment refatorizado (96/100)
- `docs/reports/SOLID_ANALYSIS_REPORT.md` - Análise SOLID completa antes da refatoração

### aoi_lib - Core Business Logic

**Purpose:** Hardware abstraction, business logic, data models, and services. NO GUI code.

**Key Modules:**

**Hardware Layer (External Interfaces):**
- `plc_axis_controller.py` - Modbus TCP communication with Delta PLC for 3-axis CNC control
  - Methods: `move_absolute()`, `move_relative()`, `jog_start()`, `wait_for_idle()`, `read_position()`
  - X/Y interpolation: Both axes share coil M1050 (NOT separate coils)
  - Addresses: X (M1000, D3000), Y (M500, D3200), Z (M1500, D3400)
  - **NOTA (Fase 4):** Este arquivo será refatorado na Fase 5 com Interface Segregation

**Interfaces e Factories (NOVO - Fase 4):**
- `interfaces/` - Interfaces ABC para baixo acoplamento (4 interfaces)
  - `interfaces/tab_manager.py` - Contrato para gerenciamento de abas
  - `interfaces/menu_manager.py` - Contrato para gerenciamento de menus
  - `interfaces/hardware_manager.py` - Contrato para gerenciamento de hardware
  - `interfaces/dialog_manager.py` - Contrato para gerenciamento de diálogos
- `factories/` - Factories para criação de componentes desacoplados (3 factories)
  - `factories/tab_factory.py` - Factory para criar abas da aplicação
  - `factories/controller_factory.py` - Factory para criar controllers
  - `factories/hardware_factory.py` - Factory para criar componentes de hardware
- `facades/` - Interfaces simplificadas para subsistemas complexos (3 facades)
  - `facades/hardware_connection_facade.py` - Interface simplificada para conexões de hardware
  - `facades/position_manager_facade.py` - Interface simplificada para gerenciamento de posições
  - `facades/authentication_manager.py` - Interface simplificada para autenticação e permissões
- **Padrões Aplicados:** Factory Pattern, Facade Pattern, Interface Segregation, Dependency Injection
- **Commit:** `bc44e16` - conductor(phase4): Refatorar main_window com Factory Pattern + Interface Segregation

**PLC Controllers Refactoring (NOVO - Fase 5):**
- `plc/interfaces/` - Interfaces ABC para controle PLC (7 interfaces)
  - `plc/interfaces/plc_connection_interface.py` - Contrato para gerenciamento de conexão Modbus TCP
  - `plc/interfaces/plc_absolute_movement_interface.py` - Contrato para movimento absoluto
  - `plc/interfaces/plc_relative_movement_interface.py` - Contrato para movimento relativo
  - `plc/interfaces/plc_jog_movement_interface.py` - Contrato para movimento Jog contínuo
  - `plc/interfaces/plc_homing_interface.py` - Contrato para operações de homing
  - `plc/interfaces/plc_position_reader_interface.py` - Contrato para leitura de posição
  - `plc/interfaces/plc_register_interface.py` - Contrato para operações de registradores Modbus
- `plc/controllers/` - Controllers especializados implementando interfaces (7 controllers)
  - `plc/controllers/plc_connection_manager.py` - Gerencia conexão Modbus TCP (130 linhas)
  - `plc/controllers/plc_absolute_movement_controller.py` - Movimento absoluto (295 linhas)
  - `plc/controllers/plc_relative_movement_controller.py` - Movimento relativo (159 linhas)
  - `plc/controllers/plc_jog_movement_controller.py` - Movimento Jog contínuo (166 linhas)
  - `plc/controllers/plc_homing_controller.py` - Operações de homing (144 linhas)
  - `plc/controllers/plc_position_reader_controller.py` - Leitura de posição (158 linhas)
  - `plc/controllers/plc_registers_controller.py` - Operações de registradores + backlight (352 linhas)
- **Padrões Aplicados:** Interface Segregation Principle (ISP), Single Responsibility Principle (SRP), Dependency Injection
- **Metas:** Reduzir de 37 métodos → 3-8 métodos por interface, manter 100% backward compatibility via Adapter Pattern
- **Testes:** 92 testes unitários criados (100% mockado, sem dependência de hardware)
- **Commits:**
  - `f09deee` - Fase 1: Interfaces ABC
  - `34fd038` - Fase 2: Controllers especializados (1.404 linhas)
  - `f49bcfa` - Fase 3: Testes unitários (92 testes)
- `camera_controller.py` - OpenCV USB camera interface with real-time preview
- `tensiometer/` - AS-120N tension sensor serial communication (refactored 2026-01-14)
  - `models.py` - Data structures (GridPoint, TensionMeasurement, GridParameters, MeasurementSession)
  - `serial_protocol.py` - RS-232 protocol handler (2400 baud, 9-byte frame)
  - `measurement_service.py` - Business logic (100% testable without PyQt6)
  - `measurement_orchestrator.py` - Facade for complete measurement workflow

**Computer Vision Pipeline:**
- `fiducial_alignment.py` - Legacy template matching (still in use)
- `fiducial_models.py` (NEW 2026-01-15) - Data structures (FiducialPoint, AlignmentTransform, AlignmentState)
- `fiducial_matching_service.py` (NEW 2026-01-15) - Template matching service (100% testable without PyQt6)
- `alignment_transform_service.py` (NEW 2026-01-15) - Geometric transformations (translation, rotation, scale)
- `alignment_state_service.py` (NEW 2026-01-15) - State management with JSON persistence
- `fiducial_alignment_adapter.py` (NEW 2026-01-15) - Adapter pattern for backward compatibility
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

**Fiducial Alignment (REFACTORED 2026-01-15):**
- `fiducial_models.py` (372 lines) - Data structures with dataclasses
  - `FiducialPoint` - Single fiducial mark with template, match data
  - `AlignmentTransform` - Transformation parameters (tx, ty, angle, scale)
  - `AlignmentState` - Complete alignment state with fiducials list
  - `FiducialConfig` - Configuration (thresholds, search_radius, window_size)
- `fiducial_matching_service.py` (330 lines) - Template matching using OpenCV
  - `match_template()` - ROI-based template matching with validation
  - `locate_fiducials()` - Batch processing multiple fiducials
  - 100% testable without PyQt6
- `alignment_transform_service.py` (413 lines) - Geometric calculations
  - `calculate_transform()` - Translation, rotation, scale via least squares
  - `apply_transform()` - Apply transformation to points
  - `inverse_transform()` - Reverse transformation (image → gerber)
- `alignment_state_service.py` (381 lines) - State management with JSON persistence
  - `add_fiducial()` - CRUD operations for fiducials
  - `update_match()` - Update match results
  - `save_state()` / `load_state()` - JSON persistence
- `fiducial_alignment_adapter.py` (488 lines) - Adapter pattern for backward compatibility
  - Converts between legacy (FiducialTemplate) and new (FiducialPoint) models
  - Provides API compatible with FiducialAlignmentWidget
  - Orchestrates new services using legacy interface
  - 100% backward compatibility maintained
- **SOLID Score: 96/100** (S:10, O:8, L:10, I:10, D:10)
- **Widget Reduced:** 959 → 547 lines (-43%)
- **Test Coverage:** 81 unit tests, 100% service layer coverage

### consumo_lib - Modular GUI Application

**Purpose:** PyQt6 GUI, presentation logic, user workflows. NO business logic (delegates to aoi_lib).

**Entry Point:**
- `main_window.py` (1,060 lines) - Main orchestrator that coordinates all tabs and modules

**UI Layout Structure (Refactored 2026-01-16):**
- **Main Layout:** QHBoxLayout com QTabWidget ocupando todo o espaço central
- **NO left panel** - Painel esquerdo removido, controles movidos para aba dedicada
- **Abas Principais:**
  - 📷 Câmera & Movimento (CNCControlTab + MovementControlWidget integrado)
  - 📋 Programas (TreeViewTab)
  - 🖥️ Monitor CLP (PLCMonitorWidget)
  - 📊 Visualização de Tensão (TensionTab)
  - 🏷️ Rastreabilidade (TrackingTab)
  - 🔍 Inspeção (InspectionTab)
  - 🗺️ Mapa (MapTab)
  - 📦 **Backup de Controles** ⭐ **NOVA** (2026-01-16)
    - Contém: PositionListWidget, SequenceControlWidget, ResultsTable
    - Acessa: Menu → Clicar na aba "Backup de Controles"
    - Propósito: Agrupar controles legacy que estavam no painel esquerdo

**UI Builder:**
- `consumo_lib/ui_builders/ui_builders.py` - MainUIBuilder
- `build_ui()` - Simplificado (removeu splitter, usa QHBoxLayout)
- `_build_backup_controls_tab()` - NOVO método (cria aba com controles legacy)

**Migration Notes (2026-01-16):**
- **Breaking Changes:** None
- **User Action:** None - controles automaticamente movidos para nova aba
- **Access:** Clicar na aba "📦 Backup de Controles" para acessar controles legacy
- **Preservado:** Todas as conexões signal/slot, toda funcionalidade mantida
- **Benefícios:** Interface mais limpa, maior espaço para conteúdo das abas

**Fiducial Alignment Widget (REFACTORED 2026-01-15):**
- `fiducial_alignment_widget.py` (547 lines, reduced from 959 lines, -43%)
- Now uses `FiducialAlignmentAdapter` for all business logic
- Widget is a thin orchestrator (UI-only responsibilities)
- Dependency injection pattern for testability

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
      ├── fiducial_models.py (data structures)
      ├── fiducial_matching_service.py (template matching)
      ├── alignment_transform_service.py (geometric transforms)
      ├── alignment_state_service.py (state management)
      ├── fiducial_alignment_adapter.py (adapter pattern)
      ├── fiducial_alignment.py (legacy template matching)
      ├── plc_axis_controller.py (hardware layer)
      ├── camera_controller.py (hardware layer)
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
- Phase 5B (2026-01-15): fiducial_alignment_widget.py → 5 services + adapter, 81 tests, SOLID 96/100

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

## Authentication Configuration

### Auto-Login Feature (2026-01-15)

O sistema suporta configuração de autenticação com auto-login opcional:

**Location:** Menu Engenharia → Configurações de Autenticação

**Configuration file:** `config/aoi_config.json`
```json
{
  "authentication": {
    "require_login_on_startup": true,
    "default_role": "operator"
  }
}
```

**Fields:**
- `require_login_on_startup`: If `true`, shows login dialog on startup. If `false`, auto-logins with `default_role`.
- `default_role`: Role for auto-login (operator|engineering|quality|admin)

**Access Control:**
- Only engineering+ users can modify authentication settings
- Requires password confirmation to change settings
- All configuration changes are audited in logs

**Auto-Login Behavior:**
- When `require_login_on_startup=false`, application auto-logins on startup
- Default user mapping:
  - operator → user "operator" (password: operator123)
  - engineering → user "eng" (password: eng123)
  - quality → user "quality" (password: quality123)
  - admin → user "admin" (password: admin123)
- If auto-login fails, falls back to login dialog

**Implementation:**
- `aoi_lib/config_manager.py`: `get_require_login_on_startup()`, `get_default_role()`, setters
- `consumo_lib/managers/auth_config_manager.py`: Business logic for auth config management
- `consumo_lib/dialogs/auth_settings_dialog.py`: UI for engineering+ users
- `consumo_lib/main_window.py`: `_perform_auto_login()` method

**Testing:**
- Unit tests: `tests/unit/test_auth_config_manager.py` (22 tests)
- Integration tests: `tests/unit/test_auth_settings_dialog.py` (15 tests)
- E2E tests: `tests/integration/test_auth_config_e2e.py` (11 tests)
- Total: 48 tests, 100% passing

---

### Engineering Wizard Free Navigation Mode (2026-01-17)

O Engineering Wizard suporta modo de navegação livre para testes e debug:

**Location:** Menu Engenharia → Configurações de Autenticação → Configurações do Engineering Wizard

**Configuration file:** `config/aoi_config.json`
```json
{
  "engineering_wizard": {
    "free_navigation_enabled": false,
    "last_used_mode": "normal"
  }
}
```

**Fields:**
- `free_navigation_enabled`: If `true`, habilita navegação livre entre todas as abas. Default: `false`
- `last_used_mode`: Rastreia último modo usado (normal|free)

**Feature Description:**
Quando habilitado, o modo de navegação livre remove as travas sequenciais do Engineering Wizard, permitindo:
- Acessar qualquer aba diretamente (1-7)
- Navegar para frente e trás sem validações
- Testar abas específicas sem completar workflow completo
- Demonstrar funcionalidades para stakeholders

**Behavior Comparison:**

| Aspect | Normal Mode | Free Navigation Mode |
|--------|--------------|----------------------|
| **Abas habilitadas** | Apenas aba atual | Todas as 7 abas |
| **Botão Próximo** | Valida aba atual | Pula validações |
| **Clique em aba** | Valida dependências | Permite navegação livre |
| **Título do dialog** | "Engineering Wizard - ..." | "🔓 Engineering Wizard - ... [Navegação Livre]" |
| **Botão Concluir** | Valida todas as abas | Valida todas as abas (igual) |

**Security:**
- ✅ Botão Concluir SEMPRE valida todas as 7 abas (ambos os modos)
- ✅ Não é possível salvar programas incompletos em nenhum modo
- ✅ Indicador visual (🔓) mostra quando modo livre está ativo
- ✅ Aviso visual no dialog: "⚠️ Modo de desenvolvimento - permite ignorar validações"

**Access Control:**
- Only engineering+ users can modify free navigation setting
- Requires password confirmation to change setting
- All setting changes are audited in logs

**Enabling Free Navigation:**
1. Login as engineering+ user
2. Menu: Engenharia → Configurações de Autenticação
3. Section: "Configurações do Engineering Wizard"
4. Checkbox: "Habilitar Navegação Livre (Testing/Debug)"
5. Click "Aplicar" and confirm password
6. Reopen Engineering Wizard to see effect

**Use Cases:**
- **Testing:** Testar aba específica sem completar workflow completo
- **Debug:** Investigar problema na aba 5 sem completar abas 1-4
- **Demo:** Mostrar funcionalidade de alinhamento para stakeholders
- **Development:** Acelerar desenvolvimento iterativo de features

**Implementation:**
- `aoi_lib/config_manager.py`: `get_free_navigation_enabled()`, `set_free_navigation_enabled()`
- `consumo_lib/managers/auth_config_manager.py`: Wrapper methods with password confirmation
- `consumo_lib/dialogs/auth_settings_dialog.py`: UI checkbox and controls
- `consumo_lib/dialogs/engineering_wizard_dialog.py`: Navigation logic respects mode
  - `_create_tabs()`: Skips setTabEnabled() when free navigation enabled
  - `_on_next()`: Skips validation in free navigation mode
  - `_on_tab_changed()`: Allows any navigation in free navigation mode
  - `_on_finish()`: Validates all tabs in BOTH modes (security preserved)

**Testing:**
- Unit tests: `tests/unit/test_free_navigation_config.py` (5 tests)
- Unit tests: `tests/unit/test_free_navigation_auth_config.py` (5 tests)
- Unit tests: `tests/unit/test_free_navigation_dialog.py` (5 tests)
- Unit tests: `tests/unit/test_free_navigation_wizard.py` (6 tests)
- Unit tests: `tests/unit/test_free_navigation_finish.py` (4 tests)
- Total: 25 tests, 100% passing

**Important Notes:**
- ⚠️ Free navigation mode is for DEVELOPMENT/TESTING only
- ⚠️ Production use should ALWAYS use normal mode
- ⚠️ Finish button validation CANNOT be bypassed in any mode
- ⚠️ Configuration persists across application restarts

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

# Fiducial Alignment Services (refactored 2026-01-15)
from aoi_lib.fiducial_models import (
    FiducialPoint,
    AlignmentTransform,
    AlignmentState,
    FiducialConfig,
    FiducialType,
    MatchingMethod
)
from aoi_lib.fiducial_matching_service import FiducialMatchingService
from aoi_lib.alignment_transform_service import AlignmentTransformService
from aoi_lib.alignment_state_service import AlignmentStateService
from aoi_lib.fiducial_alignment_adapter import FiducialAlignmentAdapter

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
- ✅ Phase 5B: fiducial_alignment_widget.py → 5 services + adapter, 81 tests, SOLID 96/100

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
- `docs/reports/SOLID_REFACTORING_PHASE5B_REPORT.md` - Phase 5B fiducial alignment refactoring
- `docs/guides/SOLID_PHASE1_MIGRATION_GUIDE.md` - Migration guide for Phase 1

**Completed Tracks:**
- `conductor/archive/solid_refactoring_phase1_20260114/`
- `conductor/archive/solid_refactoring_phase5_20260115/`
- `conductor/archive/refactor_large_files_20260113/`
- Git tags: `solid_refactoring_phase5b_20260115-complete`

---

**Last Updated:** 2026-01-15
**Version:** 0.4.0
**Development Philosophy:** SOLID principles, TDD, incremental progress with checkpoints
