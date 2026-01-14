# Dependency Analysis - SOLID Phase 1

**Date:** 2026-01-14
**Track:** solid_refactoring_phase1_20260114
**Task:** 0.1 - Analyze current codebase dependencies

---

## Executive Summary

Análise completa de dependências para os 2 arquivos críticos:
- **aoi_lib/stencil_tension.py** (1,409 linhas)
- **consumo_lib/handlers/signal_aggregator.py** (1,192 linhas)

**FINDING CRÍTICO:** SignalAggregator JÁ FOI REFACTORADO em refatoração anterior (2026-01-14)!

---

## 1. stencil_tension.py Dependencies

### 1.1 Files that import from stencil_tension

**Primary Import:**
```python
# consumo_lib/dialogs/tension_measurement_dialog.py
from aoi_lib.stencil_tension import StencilTensionDialog
```

**Re-exports:**
```python
# consumo_lib/dialogs/__init__.py
from consumo_lib.dialogs.tension_measurement_dialog import StencilTensionDialog
__all__ = ['StencilTensionDialog', ...]
```

**Usage Locations:**
1. **consumo_lib/main_window.py** (linha ~800+)
   ```python
   from consumo_lib.dialogs.tension_measurement_dialog import StencilTensionDialog
   dlg = StencilTensionDialog(self, self.controller.cnc)
   ```

2. **consumo_lib/controllers/dialog_manager_controller.py**
   ```python
   from consumo_lib.dialogs.tension_measurement_dialog import StencilTensionDialog
   dlg = StencilTensionDialog(self.parent_window, self.controller.cnc)
   ```

3. **consumo_lib/controllers/tension_measurement_controller.py** (2 locais)
   ```python
   from consumo_lib.dialogs.tension_measurement_dialog import StencilTensionDialog
   dlg = StencilTensionDialog(self.parent_window, self.controller.cnc)
   ```

### 1.2 Class Hierarchy

```
aoi_lib/stencil_tension.py (1,409 lines)
├── TensiometerSerialManager        (lines 33-201)  ✅ OK
├── TensionMeasurementThread        (lines 203-324) ⚠️ VIOLA SRP
├── StencilTensionMeasurement       (lines 326-445) ⚠️ VIOLA SRP
└── StencilTensionDialog            (lines 447-1409) 🔴 GOD DIALOG
```

### 1.3 Breaking Changes Assessment

**HIGH RISK:**
- ❌ `StencilTensionDialog` é usado em 3 locais diferentes
- ❌ Dialog contém 962 linhas (lógica UI + negócio + coordenação)
- ❌ Nenhum test exists for this dialog

**MEDIUM RISK:**
- ⚠️ `TensiometerSerialManager` é exportado (mas provavelmente não usado externamente)
- ⚠️ `TensionMeasurementThread` pode ter dependências externas desconhecidas

**LOW RISK:**
- ✅ `StencilTensionMeasurement` provavelmente é usado apenas internamente

### 1.4 Compatibility Requirements

**Must Maintain:**
1. Import path: `from aoi_lib.stencil_tension import StencilTensionDialog`
2. Dialog constructor: `StencilTensionDialog(parent, cnc_controller)`
3. Dialog interface: Todos os métodos públicos
4. PyQt6 signals: Todos os signals emitidos pelo dialog

**Can Change (Internal):**
1. Implementação interna do dialog
2. Organização de métodos privados
3. Lógica de negócio (pode mover para service layer)

---

## 2. signal_aggregator.py Dependencies

### 2.1 CRITICAL FINDING: Already Refactored!

**Status:** ✅ **JÁ REFACTORADO** (2026-01-14)

**Evidence from file header:**
```python
"""
⚠️  AVISO: ESTE ARQUIVO ESTÁ OBSOLETO! ⚠️

Refatoração Fases 1.2.1 a 1.2.8 (2026-01-14):
- TODOS os handlers de signals foram migrados para seus respectivos controllers
- Cada controller agora gerencia seus próprios handlers via setup_ui_handlers()
- Este arquivo é mantido APENAS para referência histórica
- SignalAggregator NÃO é mais instanciado no SetupCoordinator

Histórico:
- Autor: Refatoração Session 20
- Data: 2026-01-05
- Obsoleto: 2026-01-14 (Fase 1.2.8)
"""
```

### 2.2 Current State

**File Size:** 1,192 lines (mostly commented code + warnings)

**Content Analysis:**
- Lines 1-80: Deprecation warnings and documentation
- Lines 80-1192: **COMMENTED CODE** showing old implementation

**Actual Usage:**
- **ZERO active usages** found in codebase
- `consumo_lib/main_window.py` imports it but likely doesn't instantiate
- All controllers now use `setup_ui_handlers()` pattern

### 2.3 Migration Pattern (Already Applied)

**BEFORE (old SignalAggregator):**
```python
class SignalAggregator:
    def _setup_all_connections(self):
        # Connect recipe manager
        self.main_window.recipe_manager_wrapper.recipe_loaded.connect(
            self._on_recipe_loaded
        )
        # ... 100+ more connections
```

**AFTER (current architecture):**
```python
# Each controller manages its own handlers
class RecipeManagerController:
    def setup_ui_handlers(self):
        self.recipe_loaded.connect(self._on_recipe_loaded)

class TensionMeasurementController:
    def setup_ui_handlers(self):
        self.measurement_completed.connect(self._on_measurement_completed)
```

### 2.4 Breaking Changes Assessment

**NO RISK:** ✅
- SignalAggregator is **already obsolete**
- File can be **safely deleted** or moved to archive
- No active code depends on it

**Recommendation:**
- **DELETE** `consumo_lib/handlers/signal_aggregator.py` entirely
- **REMOVE** from `consumo_lib/handlers/__init__.py`
- **UPDATE** documentation to reflect completed refactoring

---

## 3. Updated Track Plan

### 3.1 Impact on Phase 2 (Event Bus)

**ORIGINAL PLAN:**
- Phase 2: Implement Event Bus (3 days)
  - Create EventBus infrastructure
  - Migrate signals to Event Bus
  - Refactor SignalAggregator
  - Remove 120+ connect_*() methods

**NEW PLAN:**
- ✅ **SKIP Phase 2 entirely!**
  - Event Bus pattern already implemented via `setup_ui_handlers()`
  - SignalAggregator already refactored
  - 120+ methods already removed

**Time Savings:** 3 days

### 3.2 Revised Track Timeline

**ORIGINAL:**
- Phase 0: Setup (1 day)
- Phase 1: Refactor stencil_tension.py (5 days)
- Phase 2: Implement Event Bus (3 days) ← **SKIP THIS**
- Phase 3: Documentation (1 day)
- **Total: 10 days**

**REVISED:**
- Phase 0: Setup (1 day)
- Phase 1: Refactor stencil_tension.py (5 days)
- ~~Phase 2: Implement Event Bus~~ ✅ **ALREADY DONE**
- Phase 3: Documentation & Cleanup (1 day) ← Updated to remove obsolete files
- **Total: 7 days** (3 days faster!)

---

## 4. Compatibility Shim Strategy

### 4.1 For stencil_tension.py

**Approach:** Rebuild as compatibility layer

```python
# aoi_lib/stencil_tension.py (NEW - compatibility shim)
"""
Compatibility module for legacy imports.
Deprecated: Use aoi_lib.tensiometer.* instead.
"""

import warnings
from aoi_lib.tensiometer.serial_protocol import TensiometerSerialManager
from aoi_lib.tensiometer.measurement_service import StencilTensionMeasurement
from aoi_lib.tensiometer.measurement_orchestrator import MeasurementOrchestrator

# Dialog will remain here temporarily
from aoi_lib.tensiometer.tension_dialog import StencilTensionDialog

warnings.warn(
    "Direct import from stencil_tension is deprecated. "
    "Use 'from aoi_lib.tensiometer import ...' instead.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = [
    'TensiometerSerialManager',
    'StencilTensionMeasurement',
    'MeasurementOrchestrator',
    'StencilTensionDialog',  # Still exported for compatibility
]
```

**Migration Path:**
```python
# OLD (still works with warning)
from aoi_lib.stencil_tension import StencilTensionDialog

# NEW (recommended)
from aoi_lib.tensiometer import StencilTensionDialog
# or
from consumo_lib.dialogs.tension import TensionMeasurementDialog
```

### 4.2 For signal_aggregator.py

**Approach:** Complete deletion (no shim needed)

```bash
# Remove obsolete file
rm consumo_lib/handlers/signal_aggregator.py

# Remove from __init__.py
# consumo_lib/handlers/__init__.py
- from .signal_aggregator import SignalAggregator
- __all__ = [..., 'SignalAggregator']

# Update main_window.py (if it still imports)
- from consumo_lib.handlers import ..., SignalAggregator
```

---

## 5. Risk Matrix

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Breaking StencilTensionDialog imports | HIGH | HIGH | Compatibility shim + deprecation warnings |
| Breaking SignalAggregator imports | LOW | NONE | Already obsolete, safe to delete |
| Tests failing after refactoring | MEDIUM | MEDIUM | Comprehensive testing before/after |
| Performance regression | LOW | LOW | Benchmark critical paths |

---

## 6. Next Steps

### Immediate (Task 0.2):
1. Create compatibility shims for `stencil_tension.py`
2. **SKIP** creating shims for `signal_aggregator.py` (will delete)
3. Update plan.md to reflect Phase 2 skip

### Phase 1 (Refactor stencil_tension.py):
1. Extract `models.py` (data structures)
2. Create `measurement_service.py` (business logic)
3. Create `measurement_orchestrator.py` (coordination)
4. Refactor `measurement_thread.py` (execution only)
5. Move `StencilTensionDialog` to new location
6. Update all imports
7. Write comprehensive tests

### Phase 3 (Updated - Cleanup):
1. **DELETE** `signal_aggregator.py` (1,192 lines removed!)
2. Remove from `__init__.py`
3. Update documentation
4. Remove references from `main_window.py`
5. Final testing

---

## 7. Files Requiring Updates

### stencil_tension.py refactoring:
- ✅ `aoi_lib/tensiometer/models.py` (NEW)
- ✅ `aoi_lib/tensiometer/measurement_service.py` (NEW)
- ✅ `aoi_lib/tensiometer/measurement_orchestrator.py` (NEW)
- ✅ `aoi_lib/tensiometer/measurement_thread.py` (NEW)
- ✅ `consumo_lib/dialogs/tension/tension_measurement_dialog.py` (NEW)
- ⚠️ `aoi_lib/stencil_tension.py` (REBUILD as shim)
- ⚠️ `consumo_lib/dialogs/tension_measurement_dialog.py` (UPDATE)
- ⚠️ `consumo_lib/dialogs/__init__.py` (UPDATE)
- ⚠️ `consumo_lib/main_window.py` (UPDATE imports)
- ⚠️ `consumo_lib/controllers/dialog_manager_controller.py` (UPDATE)
- ⚠️ `consumo_lib/controllers/tension_measurement_controller.py` (UPDATE)

### signal_aggregator.py cleanup:
- ✅ `consumo_lib/handlers/signal_aggregator.py` (DELETE)
- ⚠️ `consumo_lib/handlers/__init__.py` (REMOVE export)
- ⚠️ `consumo_lib/main_window.py` (REMOVE import if present)

---

## 8. Success Criteria

### For stencil_tension.py:
- [ ] All 3 usage locations updated without breaking
- [ ] Compatibility shim shows deprecation warnings
- [ ] Dialog reduced from 962 to <400 lines
- [ ] Service layer 100% testable without PyQt6
- [ ] ≥15 unit tests for new modules

### For signal_aggregator.py:
- [ ] File completely deleted (1,192 lines removed)
- [ ] No import errors in codebase
- [ ] All tests still passing
- [ ] Documentation updated

---

**Analysis Complete:** 2026-01-14
**Next Task:** 0.2 - Create compatibility shims
