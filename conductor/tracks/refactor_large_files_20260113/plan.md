# Plano da Track: Refactor large monolithic files

## Visão Geral
**Description:** Refactor 38 large Python files (>500 lines) to improve maintainability, testability, and adherence to project architecture

**User Value:** Cleaner, more maintainable codebase with better separation of concerns. Easier to test, extend, and understand.

**Priority:** Medium-High

**Type:** Refactor

**Estimated Phases:** 3

**Track ID:** refactor_large_files_20260113
**Type:** refactor
**Created:** 2026-01-13
**Est. Duration:** 4-6 weeks

---

## Fases

## Fase 1: Critical Architecture Fixes (High Priority)
**Objetivo:** Eliminate anti-patterns and architectural mismatches

### Tarefa 1.1: Split stencil_tension.py into 4 modules ✅
- [x] Create `aoi_lib/tensiometer/` package directory <!-- e741cb5 -->
- [x] Extract `TensiometerSerialManager` to `serial_protocol.py` <!-- e741cb5 -->
- [x] Extract `TensionMeasurementThread` to `measurement_thread.py` <!-- e741cb5 -->
- [x] Extract business logic to `tension_measurement.py` <!-- e741cb5 -->
- [x] Create `consumo_lib/dialogs/tension_measurement_dialog.py` with GUI code <!-- e741cb5 -->
- [x] Update imports in all files that reference old module <!-- e741cb5 -->
- [x] Run tests to validate refactoring <!-- e741cb5 -->
- [x] Update CLAUDE.md with new structure <!-- 0b31b4d -->

### Tarefa 1.2: Eliminate signal_aggregator.py anti-pattern
- [x] Analyze all 50+ signal connections in signal_aggregator.py
- [x] Create mapping of which controller owns which signals
- [x] **Phase 1.2.1:** Recipe Manager Signals → RecipeManagerController ✅ <!-- 984f080 -->
- [x] **Phase 1.2.2:** Tension Measurement Signals → TensionMeasurementController ✅ <!-- 6160fa9 -->
- [x] **Phase 1.2.3:** Inspection Signals → InspectionUIController ✅ <!-- 7ac92b3 -->
- [x] **Phase 1.2.4:** Camera & Calibration Signals → CameraController ✅ <!-- bac5f64 -->
- [x] **Phase 1.2.5:** Map & Position Signals → MapController/PositionManager ✅ <!-- 3b20bee -->
- [x] **Phase 1.2.6:** Stencil & Report Signals → StencilManager/ReportManager ✅ <!-- bbbba16 -->
- [x] **Phase 1.2.7:** PLC & Misc Signals → appropriate controllers ✅ <!-- Already migrated -->
- [x] **Phase 1.2.8:** Delete signal_aggregator.py and integration test ✅ <!-- 88164af -->
- [ ] Update CLAUDE.md to reflect distributed signal handling

### Tarefa 1.3: Move stencil_tracker_ui.py to consumo_lib ✅ <!-- 6f18408 -->
- [x] Create `consumo_lib/widgets/stencil/identification_widget.py`
- [x] Create `consumo_lib/dialogs/stencil/history_dialog.py`
- [x] Create `consumo_lib/dialogs/stencil/edit_dialog.py`
- [x] Create `consumo_lib/dialogs/stencil/create_dialog.py`
- [x] Create `consumo_lib/dialogs/stencil/manager_dialog.py`
- [x] Create `consumo_lib/dialogs/stencil/full_history_dialog.py`
- [x] Update imports across codebase (StencilManagerWrapper, TrackingTab, dialogs/__init__.py)
- [x] Delete original `aoi_lib/stencil_tracker_ui.py`
- [x] Validate syntax of all new files
- [ ] Update CLAUDE.md with GUI architecture (deferred to validation checkpoint)

### Tarefa 1.4: Validation checkpoint ✅ <!-- 3cb9514 -->
- [x] Run full test suite (unit + integration) - manual tests passed
- [x] Validate all main workflows (CNC, tension, inspection) - user validated
- [x] Code review all Phase 1 changes - 16 commits reviewed
- [x] Create checkpoint commit - 3cb9514
- [x] Add git note with validation report - full report attached

## Fase 2: Modularization (Medium Priority)
**Objetivo:** Split large files into focused, single-responsibility modules

### Tarefa 2.1: Split report_generator.py into specialized modules
- [ ] Create `aoi_lib/reports/` package directory
- [ ] Extract ReportConfig to `reports/config.py`
- [ ] Create `reports/builders/` subdirectory
- [ ] Extract TensionReportBuilder to `builders/tension_builder.py`
- [ ] Extract StencilHistoryReportBuilder to `builders/history_builder.py`
- [ ] Extract InspectionReportBuilder to `builders/inspection_builder.py`
- [ ] Extract chart generation to `reports/chart_generator.py`
- [ ] Create orchestrator in `reports/report_generator.py`
- [ ] Update imports across codebase
- [ ] Test all report generation workflows
- [ ] Update CLAUDE.md with reports structure

### Tarefa 2.2: Reduce main_window.py complexity
- [ ] Analyze 49 methods in MainWindow class
- [ ] Extract state management to `MainWindowState` class
- [ ] Extract initialization logic to `MainWindowInitializer` class
- [ ] Reduce MainWindow to pure orchestrator (200-300 lines target)
- [ ] Ensure all tabs still work correctly
- [ ] Test all menu actions and keyboard shortcuts
- [ ] Run integration tests
- [ ] Update CLAUDE.md with main_window structure

### Tarefa 2.3: Refactor map_controller.py
- [ ] Extract JSON CRUD logic to `services/map_program_manager.py`
- [ ] Extract dialog UI to `dialogs/map_settings_dialog.py`
- [ ] Keep orchestration in `controllers/map_controller.py`
- [ ] Update imports in map-related code
- [ ] Test map generation workflow
- [ ] Test map program save/load
- [ ] Update CLAUDE.md

### Tarefa 2.4: Validation checkpoint
- [ ] Run full test suite
- [ ] Validate report generation (tension, history, inspection)
- [ ] Validate main window functionality
- [ ] Validate map generation workflow
- [ ] Code review all Phase 2 changes
- [ ] Create checkpoint commit
- [ ] Add git note with validation report

## Fase 3: Code Cleanup and Final Polish (Low Priority)
**Objetivo:** Extract reusable components and finalize documentation

### Tarefa 3.1: Extract reusable widgets
- [ ] Extract ImagePreviewWidget from defect_judgment_dialog.py
- [ ] Create `widgets/zoomable_image_view.py`
- [ ] Update defect_judgment_dialog.py to use new widget
- [ ] Identify other reusable components
- [ ] Extract to appropriate widget files
- [ ] Test widget reuse scenarios

### Tarefa 3.2: Evaluate Repository pattern for stencil_database.py
- [ ] Analyze stencil_database.py structure (914 lines)
- [ ] Assess value of Repository pattern for this use case
- [ ] If beneficial: create repositories for stencil, tension, inspection
- [ ] If not beneficial: document rationale for keeping as-is
- [ ] Update CLAUDE.md with database architecture

### Tarefa 3.3: Evaluate tools/mosaic_builder.py
- [ ] Determine if mosaic_builder should move to aoi_lib
- [ ] If used by main app: move to `aoi_lib/mosaic.py`
- [ ] If tool only: keep in tools/ with better documentation
- [ ] Update imports if moved
- [ ] Test mosaic generation

### Tarefa 3.4: Final validation and documentation
- [ ] Run complete test suite (unit + integration + hardware)
- [ ] Validate all main workflows end-to-end
- [ ] Update CLAUDE.md with final structure
- [ ] Update code statistics (file counts, line counts)
- [ ] Create architecture diagrams if needed
- [ ] Update CHANGELOG with breaking changes
- [ ] Code review all Phase 3 changes
- [ ] Create final checkpoint commit
- [ ] Add git note with completion report

---

## Definição de Done

Uma tarefa está completa quando:
- [ ] Código refatorado conforme especificação
- [ ] Testes escritos/atualizados e passando
- [ ] Smoke test executado e passando
- [ ] Cobertura de código mantida (>80%)
- [ ] Imports atualizados em todos arquivos afetados
- [ ] CLAUDE.md atualizado com nova estrutura
- [ ] Linting sem erros (pylint, mypy)
- [ ] Commit com mensagem convencional
- [ ] Git note anexada com resumo detalhado
- [ ] plan.md atualizado com commit SHA

Uma fase está completa quando:
- [ ] Todas as tarefas da fase concluídas
- [ ] Testes da fase passando
- [ ] Validação manual aprovada
- [ ] Checkpoint commit criado
- [ ] Git note com relatório de validação anexada
- [ ] plan.md atualizado com checkpoint SHA
- [ ] CLAUDE.md atualizado com mudanças da fase

A track está completa quando:
- [ ] Todas as 3 fases completadas
- [ ] Zero arquivos >500 linhas em aoi_lib/ core
- [ ] Zero arquivos >1,000 linhas no projeto
- [ ] >90% dos arquivos <400 linhas
- [ ] Test coverage mantida (>80%)
- [ ] Documentação atualizada (CLAUDE.md, diagrams)
- [ ] Track movida para archive/
- [ ] tracks.md atualizada

---

## Checkpoints Planejados

**Checkpoint 1:** Final da Fase 1 - Critical fixes
- stencil_tension.py split into 4 modules
- signal_aggregator.py eliminated
- stencil_tracker_ui.py moved to consumo_lib

**Checkpoint 2:** Final da Fase 2 - Modularization
- report_generator.py split into 6 modules
- main_window.py reduced to 200-300 lines
- map_controller.py split into 3 modules

**Checkpoint 3:** Final da Fase 3 - Polish
- Reusable widgets extracted
- Repository pattern evaluated
- Documentation complete

---

## Recursos e Referências

- **Spec:** ../spec.md
- **Refactoring Analysis:** Ver relatório detalhado gerado anteriormente
- **Product Context:** ../../product.md
- **Tech Stack:** ../../tech-stack.md
- **Workflow:** ../../workflow.md
- **Code Guidelines:** ../../code_styleguides/

---

## Métricas de Sucesso

### Antes da Refatoração
- 38 arquivos >500 linhas
- 7 arquivos >1,000 linhas
- stencil_tension.py: 1,409 linhas (anti-pattern)
- signal_aggregator.py: 1,098 linhas (anti-pattern)
- stencil_tracker_ui.py: 1,301 linhas (wrong location)

### Depois da Refatoração (Alvo)
- 0 arquivos >1,000 linhas
- <10 arquivos >500 linhas (apenas testes)
- >90% dos arquivos <400 linhas
- GUI code 100% in consumo_lib/
- Business logic 100% in aoi_lib/
- Zero anti-patterns arquiteturais

---
*Generated by Conductor. Last updated: 2026-01-13*
