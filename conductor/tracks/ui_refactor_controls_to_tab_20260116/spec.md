# Specification: UI Refactor - Move Controls to Backup Tab

**Track ID:** ui_refactor_controls_to_tab_20260116
**Type:** Refactoring
**Priority:** 🟡 MEDIUM
**Created:** 2026-01-16

---

## Overview

Reorganizar a interface principal da aplicação para remover todos os controles do painel esquerdo que estão fora das abas e movê-los para uma nova aba chamada "Backup de Controles". O objetivo é ter apenas o menu superior e as abas ocupando todo o espaço disponível, simplificando a interface.

## Current State (BEFORE)

Based on screenshot analysis (2026-01-16 07:54:43), the current layout has:

**Left Panel Controls (OUTSIDE tabs):**
1. **Posições de Inspeção** (PositionRegistryWidget)
   - Lista de posições
   - Botão "Adicionar Posição Atual"
   - Botão "Remover"

2. **Controle de Sequência** (SequenceControlWidget)
   - Campo "Nome:" (default: "Sequência PCB")
   - Botão "Criar Sequência"
   - Botão "Executar Sequência"
   - Botão "Parar"
   - Campo "Status:" (default: "Pronto")

3. **Salvar/Carregar** (inside SequenceControlWidget)
   - Botão "Salvar Programa (JSON)"
   - Botão "Carregar Programa (JSON)"
   - Botão "Exportar para G-CODE"
   - Botão "Importar de G-CODE"

4. **Tabela de Histórico**
   - Colunas: "Posição", "Horário", "Status"
   - TableWidget com log de execuções

**Right Panel Controls (MovementControlsWidget - OUTSIDE tabs):**
- Botões de direção (↑ ↓ ← →)
- Botão "STOP" (vermelho)
- Botões "Z+" e "Z-"
- Campo "Step Size"
- Campo "Feed Rate"
- Seção "Posição Atual (mm)" (X, Y, Z)
- Botões "Passo" e "Continuo"
- Botão "Go to Zero"
- Botão "Go to Position"
- Checkbox "Enable Keyboard Control"
- Status "Idle"
- Indicador "Backlight OFF"

**Central Area (WITHIN tabs):**
- QTabWidget with multiple tabs:
  - "Câmera Movimento" (active)
  - "Programas"
  - "Monitor CLP"
  - "Visualização de Tensão"
  - "Rastreabilidade"
  - "Inspeção"
  - "Mapa"
  - "TreeView"

**Top Menu:**
- Menu bar with: Arquivo, Posições, Stencils, Relatórios, Ferramentas, Tensão do Stencil, Inspeção Visual, Engenharia, Operador, Ajuda

## Desired State (AFTER)

**Layout Simplificado:**
1. **Top:** Menu bar (unchanged)
2. **Central Area:** QTabWidget occupying ALL available space
3. **New Tab:** "Backup de Controles" containing all widgets from left panel

**Specific Changes:**
- ✅ Remove left panel completely from main layout
- ✅ Create new tab "Backup de Controles" in QTabWidget
- ✅ Move PositionRegistryWidget to the new tab
- ✅ Move SequenceControlWidget to the new tab
- ✅ Move history table to the new tab
- ❌ Keep MovementControlsWidget in right panel (NOT moved to tab)
  - **RATIONALE:** Movement controls are frequently used during camera preview and machine operation. They need to remain visible and accessible at all times, especially when "Câmera Movimento" tab is active.

**New Tab Structure:**
The "Backup de Controles" tab will organize widgets vertically:
```
┌─────────────────────────────────────┐
│ Posições de Inspeção                │
│ [Lista] [Adicionar] [Remover]       │
├─────────────────────────────────────┤
│ Controle de Sequência               │
│ [Nome: Sequência PCB]               │
│ [Criar] [Executar] [Parar]          │
│ Status: Pronto                      │
├─────────────────────────────────────┤
│ Salvar/Carregar                     │
│ [Salvar JSON] [Carregar JSON]       │
│ [Exportar G-CODE] [Importar G-CODE] │
├─────────────────────────────────────┤
│ Histórico de Execuções             │
│ [Tabela: Posição | Horário | Status]│
└─────────────────────────────────────┘
```

## Functional Requirements

### FR1: Remove Left Panel from Main Layout
- The left panel container must be completely removed from the main window layout
- All widgets currently in left panel must be moved to the new tab
- The main layout must use only QHBoxLayout: [QTabWidget (expanding) | MovementControlsWidget (fixed width)]

### FR2: Create "Backup de Controles" Tab
- New tab must be added to existing QTabWidget
- Tab name: "Backup de Controles"
- Tab index: After "Câmera Movimento" (or at the end)
- Tab must contain QVBoxLayout to organize widgets vertically

### FR3: Move Widgets to New Tab
- PositionRegistryWidget must be moved to new tab
- SequenceControlWidget must be moved to new tab
- History table (QTableWidget) must be moved to new tab
- All signal/slot connections must be preserved
- All functionality must remain working

### FR4: Preserve Movement Controls in Right Panel
- MovementControlsWidget must REMAIN in right panel
- NOT moved to any tab
- Must stay visible at all times for machine operation
- Must maintain all current functionality

### FR5: Adjust Tab Widget Layout
- QTabWidget must expand to fill all available space (left panel area + current tab area)
- No empty spaces in layout
- Proper resizing behavior when window is resized

## Non-Functional Requirements

### NFR1: Backward Compatibility
- All existing functionality must work exactly as before
- No breaking changes to user workflows
- All keyboard shortcuts must continue to work
- All signals/slots must remain connected

### NFR2: Code Quality
- Follow SOLID principles
- Maintain code organization in consumo_lib/
- Add type hints to new code
- Add docstrings (Portuguese) to new methods

### NFR3: Testing
- Unit tests for new tab widget (if applicable)
- Integration tests for UI layout
- Manual testing checklist for all moved widgets
- Verify no regressions in existing functionality

### NFR4: Performance
- No performance degradation
- Layout rendering must be fast (<100ms for window resize)
- No memory leaks from widget reparenting

### NFR5: User Experience
- Intuitive tab name in Portuguese
- Familiar layout for existing users
- Clear visual separation between widgets in new tab
- Proper widget spacing and sizing

## Acceptance Criteria

### AC1: Layout Correctness
- [ ] Left panel is completely removed from main window
- [ ] QTabWidget occupies full central area (expands to fill space)
- [ ] MovementControlsWidget remains in right panel
- [ ] No empty spaces or gaps in layout

### AC2: Tab Created
- [ ] New tab "Backup de Controles" exists in QTabWidget
- [ ] Tab is accessible via mouse click
- [ ] Tab can be switched to/from without errors

### AC3: Widgets Moved
- [ ] PositionRegistryWidget is visible in new tab
- [ ] SequenceControlWidget is visible in new tab
- [ ] History table is visible in new tab
- [ ] All widgets are properly arranged vertically

### AC4: Functionality Preserved
- [ ] All buttons in moved widgets work correctly
- [ ] All signals/slots are connected
- [ ] Position registry operations work
- [ ] Sequence control operations work
- [ ] Save/load operations work
- [ ] History table updates correctly

### AC5: Movement Controls Unchanged
- [ ] MovementControlsWidget is still in right panel
- [ ] All movement control buttons work
- [ ] Position display updates correctly
- [ ] Keyboard control works (if enabled)

### AC6: Code Quality
- [ ] Code follows project style guidelines
- [ ] No pylint warnings
- [ ] No flake8 errors
- [ ] Docstrings added to new code
- [ ] Type hints added to new code

## Use Cases

### UC1: Operator Opens Application
**Actor:** Operator
**Precondition:** Application is starting
**Main Flow:**
1. Operator launches application
2. Login screen appears (if enabled)
3. Main window opens with simplified layout
4. Only menu bar and tabs are visible at top
5. Movement controls visible on right
6. Central area shows tab content (default: "Câmera Movimento")
**Postcondition:** Application ready for use with clean interface

### UC2: Operator Accesses Legacy Controls
**Actor:** Operator
**Precondition:** Application is running, any tab is active
**Main Flow:**
1. Operator clicks on "Backup de Controles" tab
2. Tab content displays with all legacy controls
3. Operator can access position registry
4. Operator can use sequence control
5. Operator can save/load programs
6. Operator can view history table
**Postcondition:** All legacy controls accessible and functional

### UC3: Operator Uses Movement Controls
**Actor:** Operator
**Precondition:** Application is running, "Câmera Movimento" tab is active
**Main Flow:**
1. Operator views camera preview in central tab
2. Movement controls are visible on right panel
3. Operator clicks movement buttons (↑ ↓ ← →)
4. Machine moves accordingly
5. Position display updates
**Postcondition:** Machine operation works seamlessly without switching tabs

## Implementation Notes

### Files to Modify
1. **consumo_lib/main_window.py**
   - Remove left panel from main layout
   - Update layout structure (HBoxLayout: QTabWidget | MovementControlsWidget)
   - Create new tab in QTabWidget
   - Move widgets to new tab

2. **consumo_lib/tabs/** (possibly create new tab widget)
   - Create `backup_controls_tab.py` (optional, can be inline)
   - Organize moved widgets in vertical layout

### Files to Analyze
- `consumo_lib/widgets/position_registry.py` - PositionRegistryWidget
- `consumo_lib/widgets/sequence_control.py` - SequenceControlWidget
- `consumo_lib/widgets/movement_control.py` - MovementControlWidget (NOT moved)

### Dependencies
- PyQt6 (already in use)
- Existing widget structure in consumo_lib/widgets/
- Existing tabs in consumo_lib/tabs/

### Migration Strategy
1. Create new tab widget (BackupControlsTab)
2. Move widgets from left panel to new tab
3. Remove left panel from main layout
4. Update main window layout to expand tab widget
5. Test all functionality
6. Update documentation

## Risks and Mitigations

### Risk 1: Breaking Signal/Slot Connections
**Impact:** HIGH - Buttons may stop working
**Mitigation:** Carefully trace all connections before moving widgets; test thoroughly after refactoring

### Risk 2: Layout Resizing Issues
**Impact:** MEDIUM - UI may look broken on different screen sizes
**Mitigation:** Test on multiple screen resolutions; use proper size policies

### Risk 3: User Confusion
**Impact:** LOW - Users may not find moved controls
**Mitigation:** Clear tab name; consider adding tooltip or help text

### Risk 4: Performance Regression
**Impact:** LOW - Layout rendering may slow down
**Mitigation:** Profile rendering time; optimize if necessary

## Success Metrics

- ✅ All acceptance criteria met
- ✅ Zero regressions in functionality
- ✅ Code coverage maintained (>80%)
- ✅ No linter warnings
- ✅ Manual testing checklist complete
- ✅ User acceptance (if applicable)

## Out of Scope

The following are explicitly OUT OF SCOPE for this track:
- ❌ Refactoring MovementControlsWidget (stays in right panel)
- ❌ Redesigning individual widgets
- ❌ Changing widget functionality
- ❌ Adding new features
- ❌ Refactoring right panel
- ❌ Changing menu structure
- ❌ Internationalization (i18n)

---

**Prepared by:** Claude Sonnet 4.5
**Date:** 2026-01-16
**Version:** 1.0
