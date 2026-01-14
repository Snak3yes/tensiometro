# SOLID Refactoring Phase 1 - Implementation Plan

**Track ID:** solid_refactoring_phase1_20260114
**Type:** Refactor
**Priority:** 🔴 CRITICAL
**Est. Duration:** 2 weeks (10 working days)
**Sprint:** 1
**Start Date:** 2026-01-14

---

## Overview

Esta track implementa a **Fase 1 do Roadmap de Refatoração SOLID**, focando nos 2 arquivos mais críticos do projeto:

1. **aoi_lib/stencil_tension.py** (1,409 linhas) → Refatorar em 4 módulos
2. **consumo_lib/handlers/signal_aggregator.py** (1,192 linhas) → Implementar Event Bus

**Objetivo:** Eliminar violações CRÍTICAS de SRP, melhorar testabilidade e reduzir complexidade.

---

## Phase Structure

```
Phase 0: Preparation & Setup (1 day)
├── Task 0.1: Analyze current codebase dependencies
├── Task 0.2: Create compatibility shims
├── Task 0.3: Setup test infrastructure
└── Task 0.4: Verify checkpoint (smoke test)

Phase 1: Refactor stencil_tension.py (5 days)
├── Task 1.1: Extract data models to models.py
├── Task 1.2: Create measurement_service.py (business logic)
├── Task 1.3: Create measurement_orchestrator.py (coordination)
├── Task 1.4: Refactor measurement_thread.py (execution only)
├── Task 1.5: Move dialog to consumo_lib and refactor
├── Task 1.6: Write unit tests for service layer
├── Task 1.7: Update imports across codebase
├── Task 1.8: Verify checkpoint (all tests passing)
└── Task 1.9: Create checkpoint commit

Phase 2: Implement Event Bus (3 days)
├── Task 2.1: Create EventBus core infrastructure
├── Task 2.2: Migrate critical signals to Event Bus
├── Task 2.3: Refactor SignalAggregator to use EventBus
├── Task 2.4: Remove 120+ connect_*() methods
├── Task 2.5: Write integration tests for EventBus
├── Task 2.6: Update all signal registrations
├── Task 2.7: Verify checkpoint (smoke test + integration tests)
└── Task 2.8: Create checkpoint commit

Phase 3: Documentation & Polish (1 day)
├── Task 3.1: Update CLAUDE.md with new architecture
├── Task 3.2: Create migration guide for developers
├── Task 3.3: Run full test suite and fix issues
├── Task 3.4: Verify final checkpoint (all quality gates)
└── Task 3.5: Create final commit and documentation
```

---

## Phase 0: Preparation & Setup

**Duration:** 1 day
**Goal:** Setup infrastructure e análise de dependências

### Task 0.1: Analyze current codebase dependencies ✅

**Commit:** 96bdf27

**Description:** Mapear todas as dependências de `stencil_tension.py` e `signal_aggregator.py`

**Subtasks:**
- [x] Find all imports of `stencil_tension` module
- [x] Find all usages of `StencilTensionDialog`
- [x] Find all usages of `SignalAggregator`
- [x] Document compatibility requirements
- [x] Identify potential breaking changes

**Verification:**
```bash
# Comando para encontrar dependências
grep -r "from aoi_lib.stencil_tension import" --include="*.py" .
grep -r "from consumption_lib.handlers.signal_aggregator import" --include="*.py" .
grep -r "StencilTensionDialog" --include="*.py" .
grep -r "SignalAggregator" --include="*.py" .
```

**Acceptance:**
- [x] Lista de dependências documentada
- [x] Arquivos que necessitam atualização identificados
- [x] Plano de compatibility shims definido

**🎉 CRITICAL DISCOVERY:** SignalAggregator JÁ FOI REFACTORADO!
- Phase 2 pode ser SKIPPADA (economiza 3 dias)
- Ver DEPENDENCY_ANALYSIS.md para detalhes

---

### Task 0.2: Create compatibility shims

**Description:** Criar wrappers para manter backward compatibility durante migração

**Files to Create:**
- `aoi_lib/stencil_tension.py` (rebuild como compatibility layer)

**Code Structure:**
```python
# aoi_lib/stencil_tension.py (compatibility shim)
"""
Compatibility module for legacy imports.
Deprecated: Use aoi_lib.tensiometer.* instead.
"""

import warnings
from aoi_lib.tensiometer.serial_protocol import TensiometerSerialManager
from aoi_lib.tensiometer.measurement_service import StencilTensionMeasurement
from aoi_lib.tensiometer.measurement_orchestrator import MeasurementOrchestrator

# Show deprecation warning
warnings.warn(
    "Direct import from stencil_tension is deprecated. "
    "Use 'from aoi_lib.tensiometer import ...' instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export for compatibility
__all__ = [
    'TensiometerSerialManager',
    'StencilTensionMeasurement',
    'MeasurementOrchestrator',
]
```

**Verification:**
- [ ] Imports antigos funcionam com warning
- [ ] Testes existentes passam sem modificação
- [ ] Código novo pode usar novos módulos

---

### Task 0.3: Setup test infrastructure

**Description:** Configurar infraestrutura de testes para novos módulos

**Subtasks:**
- [ ] Create `tests/unit/aoi_lib/tensiometer/` directory
- [ ] Create `tests/integration/event_bus/` directory
- [ ] Add pytest fixtures for PLC, Serial, EventBus mocks
- [ ] Configure test coverage for new modules
- [ ] Create test templates for service layer

**Files to Create:**
```
tests/unit/aoi_lib/tensiometer/
├── __init__.py
├── conftest.py                    # Fixtures compartilhadas
├── test_serial_protocol.py
├── test_measurement_service.py
├── test_measurement_orchestrator.py
└── test_measurement_thread.py

tests/integration/
├── __init__.py
└── test_event_bus.py
```

**Verification:**
- [ ] `pytest tests/unit/aoi_lib/tensiometer/` runs successfully
- [ ] `pytest tests/integration/test_event_bus.py` runs successfully
- [ ] Coverage configured for new directories

---

### Task 0.4: Verify checkpoint (smoke test)

**Description:** Garantir que aplicação inicia sem erros antes de começar refatoração

**Subtasks:**
- [ ] Run application: `python main.py`
- [ ] Verify no import errors
- [ ] Verify UI loads correctly
- [ ] Run full test suite: `pytest`
- [ ] Check all tests pass (462 tests)

**Verification Commands:**
```bash
# Smoke test
python main.py &
sleep 5
kill %1

# Full test suite
pytest --cov=aoi_lib --cov=consumo_lib
```

**Acceptance:**
- [ ] Application starts without errors
- [ ] All 462 tests pass
- [ ] Coverage ≥ 25.81%

**Checkpoint Commit:**
```bash
git add -A
git commit -m "feat(conductor): Phase 0 checkpoint - Setup complete

- Analyzed dependencies for stencil_tension.py
- Created compatibility shims for backward compatibility
- Setup test infrastructure for new modules
- Smoke test verified: 462 tests passing

Co-Authored-By: RONALDBUZAGLO <senseironald@gmail.com>"
```

---

## Phase 1: Refactor stencil_tension.py

**Duration:** 5 days
**Goal:** Refatorar 1,409 linhas em 4 módulos focados

### Task 1.1: Extract data models to models.py

**Description:** Extrair estruturas de dados para módulo separado

**File to Create:** `aoi_lib/tensiometer/models.py`

**Classes to Extract:**
```python
@dataclass
class TensionPoint:
    """Ponto de medição de tensão"""
    x: int
    y: int
    value: float
    unit: str = "N/cm²"
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class GridConfig:
    """Configuração do grid de medição"""
    rows: int
    cols: int
    start_x: float
    start_y: float
    spacing_x: float
    spacing_y: float

@dataclass
class TensionGrid:
    """Grid completo de medições"""
    config: GridConfig
    points: List[TensionPoint]
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class MeasurementStats:
    """Estatísticas das medições"""
    mean: float
    std_dev: float
    min_value: float
    max_value: float
    classification: str  # "OK", "WARNING", "NOK"
```

**Acceptance:**
- [ ] `aoi_lib/tensiometer/models.py` criado
- [ ] Todas as classes são dataclasses
- [ ] Type hints em todos os campos
- [ ] Docstrings Google style
- [ ] Import test: `from aoi_lib.tensiometer.models import TensionPoint`

---

### Task 1.2: Create measurement_service.py (business logic)

**Description:** Extrair lógica de negócio PURA (sem UI, sem hardware)

**File to Create:** `aoi_lib/tensiometer/measurement_service.py`

**Class Structure:**
```python
class TensionMeasurementService:
    """
    Service para lógica de negócio de medição de tensão.

    Responsabilidades:
    - Calcular grid de pontos (NxN)
    - Validar medições (range checking)
    - Calcular estatísticas (média, desvio padrão)
    - Classificar resultados (OK/WARNING/NOK)

    SEM dependências de:
    - PyQt6 (UI)
    - PLC (hardware)
    - Serial (hardware)
    """

    def __init__(self, config: GridConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)

    def calculate_grid_points(self) -> List[TensionPoint]:
        """Calcula coordenadas do grid NxN"""

    def validate_measurement(self, value: float) -> bool:
        """Valida se valor está dentro do range aceitável"""

    def calculate_statistics(self, grid: TensionGrid) -> MeasurementStats:
        """Calcula estatísticas descritivas"""

    def classify_result(self, stats: MeasurementStats) -> str:
        """Classifica resultado baseado em critérios de aceitação"""
```

**Acceptance:**
- [ ] Service não depende de PyQt6
- [ ] Service não depende de PLC/Serial
- [ ] Service 100% testável com mocks
- [ ] Complexidade < 15 por método
- [ ] Docstrings completas

---

### Task 1.3: Create measurement_orchestrator.py (coordination)

**Description:** Criar orquestrador que coordena PLC + Tensiômetro

**File to Create:** `aoi_lib/tensiometer/measurement_orchestrator.py`

**Class Structure:**
```python
class MeasurementOrchestrator:
    """
    Orquestra medição de tensão usando PLC e Tensiômetro.

    Responsabilidades:
    - Coordenar movimento PLC
    - Coordenar leitura do tensiômetro
    - Delegar cálculos para Service
    - Gerenciar estado da medição

    Depende de:
    - TensionMeasurementService (negócio)
    - PLCAxisController (hardware abstraction)
    - TensiometerSerialManager (hardware abstraction)

    NÃO depende de:
    - PyQt6 (UI)
    """

    def __init__(
        self,
        service: TensionMeasurementService,
        plc: PLCAxisController,
        tensiometer: TensiometerSerialManager
    ):
        self.service = service
        self.plc = plc
        self.tensiometer = tensiometer
        self.logger = logging.getLogger(__name__)

    def execute_measurement_sequence(
        self,
        grid: TensionGrid
    ) -> TensionGrid:
        """Executa sequência completa de medição"""

    def _move_to_position(self, x: float, y: float):
        """Move PLC para posição"""

    def _read_tension(self) -> float:
        """Lê valor do tensiômetro"""

    def _wait_for_movement_complete(self):
        """Aguarda movimento PLC completar"""
```

**Acceptance:**
- [ ] Orchestrator não depende de PyQt6
- [ ] Orchestrator usa injeção de dependências
- [ ] Orchestrator delega cálculos para Service
- [ ] Orchestrator testável com mocks de PLC/Serial
- [ ] Complexidade < 15 por método

---

### Task 1.4: Refactor measurement_thread.py (execution only)

**Description:** Refatorar thread para apenas execução em background

**File to Refactor:** `aoi_lib/tensiometer/measurement_thread.py`

**Changes:**
- Remover lógica de negócio (delegar para Orchestrator)
- Remover lógica de UI (delegar para Dialog via signals)
- Manter apenas execução assíncrona

**Class Structure:**
```python
class TensionMeasurementThread(QThread):
    """
    Thread para execução assíncrona de medição.

    Responsabilidades:
    - Executar Orchestrator em background
    - Emitir signals de progresso
    - Emitir signals de conclusão

    SEM lógica de negócio (delega para Orchestrator)
    """

    progress_updated = pyqtSignal(int, int, str)  # current, total, message
    measurement_completed = pyqtSignal(TensionGrid)
    error_occurred = pyqtSignal(str)

    def __init__(self, orchestrator: MeasurementOrchestrator, grid: TensionGrid):
        super().__init__()
        self.orchestrator = orchestrator
        self.grid = grid

    def run(self):
        """Executa medição em background"""
        try:
            result = self.orchestrator.execute_measurement_sequence(self.grid)
            self.measurement_completed.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))
```

**Acceptance:**
- [ ] Thread tem <100 linhas
- [ ] Thread não tem lógica de negócio
- [ ] Thread apenas delega para Orchestrator
- [ ] Signals emitidos corretamente
- [ ] Testável com mocks de Orchestrator

---

### Task 1.5: Move dialog to consumo_lib and refactor

**Description:** Mover dialog para `consumo_lib/dialogs/tension/` e refatorar

**New Location:** `consumo_lib/dialogs/tension/tension_measurement_dialog.py`

**Changes:**
- Remover lógica de negócio (delegar para Service)
- Remover lógica de coordenação (delegar para Orchestrator)
- Manter apenas UI (layout, eventos, validação de formulário)
- Reduzir de 962 para <400 linhas

**Class Structure:**
```python
class TensionMeasurementDialog(QDialog):
    """
    Dialog de medição de tensão (UI apenas).

    Responsabilidades:
    - Layout de UI
    - Event handling (botões, inputs)
    - Validação de formulário
    - Persistência de rotinas (JSON)
    - Coordenação com Orchestrator/Thread

    SEM lógica de negócio (delega para Service/Orchestrator)
    """

    def __init__(
        self,
        orchestrator: MeasurementOrchestrator,
        parent=None
    ):
        super().__init__(parent)
        self.orchestrator = orchestrator
        self.setup_ui()

    def setup_ui(self):
        """Setup UI layout (≈200 linhas)"""

    def on_start_measurement(self):
        """Handler para botão Iniciar"""

    def on_save_routine(self):
        """Handler para botão Salvar Rotina"""
```

**Acceptance:**
- [ ] Dialog em `consumo_lib/dialogs/tension/`
- [ ] Dialog tem <400 linhas
- [ ] Dialog não tem lógica de negócio
- [ ] Dialog usa Orchestrator (não Service diretamente)
- [ ] Persistência de rotinas isolada em método próprio
- [ ] UI funcional (smoke test)

---

### Task 1.6: Write unit tests for service layer

**Description:** Escrever testes unitários para service layer

**Files to Create:**
- `tests/unit/aoi_lib/tensiometer/test_measurement_service.py`
- `tests/unit/aoi_lib/tensiometer/test_measurement_orchestrator.py`

**Test Coverage:**

**test_measurement_service.py:**
```python
def test_calculate_grid_points_3x3():
    """Testa cálculo de grid 3x3"""

def test_calculate_grid_points_5x5():
    """Testa cálculo de grid 5x5"""

def test_validate_measurement_ok_range():
    """Testa validação de valor OK"""

def test_validate_measurement_out_of_range():
    """Testa validação de valor fora do range"""

def test_calculate_statistics_normal():
    """Testa cálculo de estatísticas normais"""

def test_classify_result_ok():
    """Testa classificação OK"""

def test_classify_result_warning():
    """Testa classificação WARNING"""

def test_classify_result_nok():
    """Testa classificação NOK"
```

**test_measurement_orchestrator.py:**
```python
@pytest.fixture
def mock_plc():
    """Mock de PLC controller"""

@pytest.fixture
def mock_tensiometer():
    """Mock de tensiometer"""

def test_execute_measurement_sequence_success():
    """Testa sequência completa com sucesso"""

def test_execute_measurement_sequence_plc_error():
    """Testa tratamento de erro de PLC"""

def test_execute_measurement_sequence_tensiometer_error():
    """Testa tratamento de erro de tensiômetro"""

def test_move_to_position():
    """Testa movimento para posição"""

def test_read_tension():
    """Testa leitura de tensão"
```

**Acceptance:**
- [ ] ≥10 testes para MeasurementService
- [ ] ≥5 testes para MeasurementOrchestrator
- [ ] Coverage ≥ 80% para service layer
- [ ] Todos os testes passam
- [ ] Testes rodam sem PyQt6

---

### Task 1.7: Update imports across codebase

**Description:** Atualizar todos os imports para usar novos módulos

**Files to Update:**
```bash
# Encontrar todos os arquivos que importam stencil_tension
grep -r "from aoi_lib.stencil_tension import" --include="*.py" .
grep -r "import aoi_lib.stencil_tension" --include="*.py" .
```

**Migration Pattern:**
```python
# ANTIGO
from aoi_lib.stencil_tension import StencilTensionMeasurement, StencilTensionDialog

# NOVO (com deprecation warning automático via compatibility shim)
from aoi_lib.tensiometer import StencilTensionMeasurement
from consumo_lib.dialogs.tension import TensionMeasurementDialog
```

**Acceptance:**
- [ ] Todos os imports atualizados
- [ ] Código novo usa novos módulos
- [ ] Código legado usa compatibility shim
- [ ] Nenhum import error

---

### Task 1.8: Verify checkpoint (all tests passing)

**Description:** Garantir que tudo funciona após refatoração

**Verification Commands:**
```bash
# Testes unitários novos
pytest tests/unit/aoi_lib/tensiometer/ -v

# Testes de integração
pytest tests/integration/ -v

# Test suite completo
pytest --cov=aoi_lib --cov=consumo_lib --cov-report=html

# Smoke test
python main.py
```

**Acceptance:**
- [ ] Todos os testes novos passam (≥15 testes)
- [ ] Todos os testes existentes passam (462 tests)
- [ ] Coverage ≥ 30% (meta: +4.2%)
- [ ] Application inicia sem erros
- [ ] Dialog de tensão funcional (manual test)

---

### Task 1.9: Create checkpoint commit

**Description:** Commit do checkpoint da Phase 1

**Commit Message:**
```bash
git add -A
git commit -m "feat(conductor): Phase 1 checkpoint - stencil_tension refactored

Refactored aoi_lib/stencil_tension.py (1,409 lines → 4 modules):

Created:
- aoi_lib/tensiometer/models.py (data structures)
- aoi_lib/tensiometer/measurement_service.py (business logic)
- aoi_lib/tensiometer/measurement_orchestrator.py (coordination)
- aoi_lib/tensiometer/measurement_thread.py (execution)
- consumo_lib/dialogs/tension/tension_measurement_dialog.py (UI only)

Benefits:
- Separation of concerns (SRP compliant)
- Service layer 100% testable without PyQt6
- Dialog reduced from 962 to <400 lines
- 15 new unit tests (80%+ coverage)
- Zero breaking changes (compatibility shims)

Metrics:
- Complexity: 85+ → <15 per method
- Testability: 0% → 80% (without PyQt6)
- Lines: 1,409 → ~600 total (4 modules)
- Files >1000 lines: 2 → 1

Co-Authored-By: RONALDBUZAGLO <senseironald@gmail.com>"
```

---

## Phase 2: Implement Event Bus

**Duration:** 3 days
**Goal:** Substituir SignalAggregator por Event Bus pattern

### Task 2.1: Create EventBus core infrastructure

**Description:** Implementar EventBus centralizado (Publish/Subscribe)

**File to Create:** `consumo_lib/event_bus.py`

**Class Structure:**
```python
from dataclasses import dataclass
from typing import Callable, Dict, List, Any
from datetime import datetime
import logging

@dataclass
class Event:
    """Evento genérico do sistema"""
    type_: str
    data: Any
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = None


class EventBus:
    """
    Bus centralizado de eventos (Publish/Subscribe pattern).

    Responsabilidades:
    - Registrar subscribers para tipos de eventos
    - Publicar eventos para subscribers
    - Gerenciar lifecycle de subscriptions

    Benefícios:
    - Desacoplamento: Componentes não se conhecem
    - Extensibilidade: Adicionar eventos sem modificar EventBus
    - Testabilidade: Mock simples para testes
    """

    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self.logger = logging.getLogger(__name__)

    def subscribe(self, event_type: str, handler: Callable[[Event], None]):
        """Inscreve handler para tipo de evento"""

    def unsubscribe(self, event_type: str, handler: Callable):
        """Remove inscrição de handler"""

    def publish(self, event: Event):
        """Publica evento para todos subscribers"""

    def subscribe_async(self, event_type: str, handler: Callable):
        """Inscreve handler com execução assíncrona (Qt signals)"
```

**Acceptance:**
- [ ] `consumo_lib/event_bus.py` criado
- [ ] Event e EventBus implementados
- [ ] Type hints em todos os métodos
- [ ] Docstrings Google style
- [ ] Logging estruturado
- [ ] <150 linhas de código

---

### Task 2.2: Migrate critical signals to Event Bus

**Description:** Migrar sinais críticos para usar EventBus

**Signals to Migrate (Priority 1):**
```python
# Camera events
"camera.frame_captured"
"camera.connection_changed"

# Tension events
"tension.measurement_started"
"tension.measurement_progress"
"tension.measurement_completed"
"tension.measurement_error"

# PLC events
"plc.movement_started"
"plc.movement_completed"
"plc.connection_changed"

# Inspection events
"inspection.started"
"inspection.progress_updated"
"inspection.completed"
"inspection.defect_found"
```

**Migration Pattern:**
```python
# ANTIGO (PyQt6 signals directly)
class CameraController:
    frame_captured = pyqtSignal(np.ndarray)

    def capture_frame(self):
        frame = self._do_capture()
        self.frame_captured.emit(frame)

# NOVO (Event Bus + PyQt6 signals for UI)
class CameraController:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        # Keep signal for UI compatibility
        self.frame_captured = pyqtSignal(np.ndarray)

    def capture_frame(self):
        frame = self._do_capture()
        # Publish to event bus
        event = Event("camera.frame_captured", data=frame)
        self.event_bus.publish(event)
        # Still emit signal for UI components
        self.frame_captured.emit(frame)
```

**Acceptance:**
- [ ] 15+ eventos críticos migrados
- [ ] Cada componente publica seus eventos
- [ ] PyQt6 signals mantidos para UI (compatibilidade)
- [ ] Event types documentados

---

### Task 2.3: Refactor SignalAggregator to use EventBus

**Description:** Refatorar SignalAggregator para usar EventBus internamente

**File to Refactor:** `consumo_lib/handlers/signal_aggregator.py`

**New Structure:**
```python
class SignalAggregator:
    """
    Agregador de sinais (compatibilidade layer).

    Responsabilidade:
    - Adaptar PyQt6 signals ↔ Event Bus
    - Manter compatibilidade com código existente

    Event Bus é a nova verdade. SignalAggregator é um adaptador.
    """

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus

    # Remover 120+ métodos connect_*()
    # Substituir por auto-registration via Event Bus

    def register_controller(self, controller: Any, controller_name: str):
        """
        Registra controller no Event Bus.

        Controller deve implementar método register_events().
        """
        if hasattr(controller, 'register_events'):
            controller.register_events(self.event_bus)
```

**Acceptance:**
- [ ] SignalAggregator usa EventBus internamente
- [ ] 120+ métodos connect_*() removidos
- [ ] Auto-registration implementado
- [ ] SignalAggregator reduzido para <200 linhas

---

### Task 2.4: Remove 120+ connect_*() methods

**Description:** Remover métodos repetitivos de conexão de sinais

**Before (1,192 lines):**
```python
def connect_camera_controller(self, controller):
    if controller:
        controller.frame_updated.connect(self.on_camera_frame_updated)

def connect_tension_controller(self, controller):
    if controller:
        controller.measurement_completed.connect(self.on_tension_measurement_completed)

# ... 118+ methods
```

**After (<200 lines):**
```python
def register_controller(self, controller: Any, name: str):
    """Generic controller registration"""
    if hasattr(controller, 'register_events'):
        controller.register_events(self.event_bus)
```

**Acceptance:**
- [ ] Todos os métodos connect_*() removidos
- [ ] Código reduzido em ~900 linhas
- [ ] Auto-registration funcional
- [ ] Backward compatibility mantida

---

### Task 2.5: Write integration tests for EventBus

**Description:** Escrever testes de integração para EventBus

**File to Create:** `tests/integration/test_event_bus.py`

**Test Cases:**
```python
def test_event_subscription():
    """Testa subscrição de evento"""

def test_event_publishing():
    """Testa publicação de evento"""

def test_multiple_subscribers():
    """Testa múltiplos subscribers para mesmo evento"""

def test_event_unsubscription():
    """Testa cancelamento de subscrição"""

def test_event_with_camera_controller():
    """Testa integração com CameraController (mock)"""

def test_event_with_plc_controller():
    """Testa integração com PLCController (mock)"

def test_async_event_execution():
    """Testa execução assíncrona de eventos"
```

**Acceptance:**
- [ ] ≥5 testes de integração
- [ ] Coverage ≥ 80% para EventBus
- [ ] Todos os testes passam
- [ ] Testes rodam rapidamente (<5s)

---

### Task 2.6: Update all signal registrations

**Description:** Atualizar todos os controllers para usar auto-registration

**Pattern:**
```python
# Adicionar método em cada controller
class CameraController:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.frame_captured = pyqtSignal(np.ndarray)

    def register_events(self, event_bus: EventBus):
        """Registra eventos no Event Bus"""
        event_bus.subscribe("camera.capture_requested", self.on_capture_request)

    def capture_frame(self):
        frame = self._do_capture()
        event = Event("camera.frame_captured", data=frame)
        self.event_bus.publish(event)
        self.frame_captured.emit(frame)  # For UI compatibility
```

**Controllers to Update:**
- [ ] CameraController
- [ ] TensionMeasurementController
- [ ] MovementController
- [ ] InspectionController
- [ ] FiducialAlignmentController
- [ ] Outros controllers com sinais

**Acceptance:**
- [ ] Todos os controllers têm register_events()
- [ ] Todos os eventos publicados no EventBus
- [ ] PyQt6 signals mantidos para UI
- [ ] Nenhum comportamento quebrado

---

### Task 2.7: Verify checkpoint (smoke test + integration tests)

**Description:** Garantir que tudo funciona após migração para EventBus

**Verification Commands:**
```bash
# Testes de integração do EventBus
pytest tests/integration/test_event_bus.py -v

# Test suite completo
pytest --cov=consumo_lib.event_bus --cov=consumo_lib.handlers -v

# Smoke test
python main.py
```

**Manual Verification:**
- [ ] Camera preview funciona
- [ ] Medição de tensão funciona
- [ ] Movimento CNC funciona
- [ ] Inspeção visual funciona
- [ ] Sinais UI são atualizados corretamente

**Acceptance:**
- [ ] Todos os testes de integração passam
- [ ] Todos os testes existentes passam (462 tests)
- [ ] Application inicia sem erros
- [ ] Funcionalidades críticas funcionam (manual test)

---

### Task 2.8: Create checkpoint commit

**Description:** Commit do checkpoint da Phase 2

**Commit Message:**
```bash
git add -A
git commit -m "feat(conductor): Phase 2 checkpoint - EventBus implemented

Implemented EventBus pattern to replace SignalAggregator God Object:

Created:
- consumo_lib/event_bus.py (Event, EventBus)
- tests/integration/test_event_bus.py (integration tests)

Refactored:
- consumption_lib/handlers/signal_aggregator.py (1,192 → <200 lines)
- Removed 120+ connect_*() methods
- Implemented auto-registration pattern

Benefits:
- Desacoplamento: Componentes não se conhecem
- Extensibilidade: Adicionar eventos sem modificar código
- Testabilidade: Mock simples para testes
- Single Point of Failure removido

Metrics:
- SignalAggregator: 1,192 → <200 lines (-83%)
- Files >1000 lines: 1 → 0 ✅
- Complexity: 120+ → <15
- Test coverage: +5 integration tests

Co-Authored-By: RONALDBUZAGLO <senseironald@gmail.com>"
```

---

## Phase 3: Documentation & Polish

**Duration:** 1 day
**Goal:** Documentar mudanças e garantir qualidade

### Task 3.1: Update CLAUDE.md with new architecture

**Description:** Atualizar CLAUDE.md com nova arquitetura

**Sections to Update:**

```markdown
## Architecture Overview

### Tensiometer Module (NEW)
Location: aoi_lib/tensiometer/

Purpose: Medição de tensão de stencil com separação de responsabilidades

Components:
- serial_protocol.py: Protocolo AS-120N (2400 baud, 9-byte frame)
- models.py: Data structures (TensionPoint, GridConfig, etc.)
- measurement_service.py: Lógica de negócio (grid, stats, classification)
- measurement_orchestrator.py: Coordenação (PLC + Tensiômetro)
- measurement_thread.py: Execução assíncrona

Usage:
from aoi_lib.tensiometer import (
    TensiometerSerialManager,
    TensionMeasurementService,
    MeasurementOrchestrator
)

### Event Bus System (NEW)
Location: consumo_lib/event_bus.py

Purpose: Desacoplamento de componentes via Publish/Subscribe pattern

Usage:
from consumo_lib.event_bus import EventBus, Event

event_bus = EventBus()
event_bus.subscribe("camera.frame_captured", handler)
event_bus.publish(Event("camera.frame_captured", data=frame))
```

**Acceptance:**
- [ ] CLAUDE.md atualizado com seção "Tensiometer Module"
- [ ] CLAUDE.md atualizado com seção "Event Bus System"
- [ ] Exemplos de uso incluídos
- [ ] Diagramas atualizados (se houver)

---

### Task 3.2: Create migration guide for developers

**Description:** Criar guia de migração para desenvolvedores

**File to Create:** `docs/guides/SOLID_PHASE1_MIGRATION_GUIDE.md`

**Content:**
```markdown
# SOLID Phase 1 Migration Guide

## Overview
Phase 1 refactoring completed (2026-01-14).
This guide helps you migrate your code.

## Breaking Changes

### stencil_tension Module
**OLD:**
```python
from aoi_lib.stencil_tension import StencilTensionMeasurement, StencilTensionDialog
```

**NEW:**
```python
from aoi_lib.tensiometer import TensionMeasurementService
from consumo_lib.dialogs.tension import TensionMeasurementDialog
```

### SignalAggregator
**OLD:**
```python
signal_aggregator.connect_camera_controller(camera)
signal_aggregator.connect_tension_controller(tension)
```

**NEW:**
```python
# Auto-registration via EventBus
camera.register_events(event_bus)
tension.register_events(event_bus)
```

## New Features

### EventBus
```python
from consumo_lib.event_bus import EventBus, Event

# Create event bus
event_bus = EventBus()

# Subscribe to events
event_bus.subscribe("camera.frame_captured", my_handler)

# Publish events
event = Event("camera.frame_captured", data=frame)
event_bus.publish(event)
```

## Compatibility
- Old imports still work (with deprecation warnings)
- PyQt6 signals still emitted (for UI compatibility)
- No breaking changes for end users

## Testing
Service layer is now 100% testable without PyQt6:

```python
# Can test business logic without UI framework
def test_measurement_service():
    service = TensionMeasurementService(config)
    stats = service.calculate_statistics(grid)
    assert stats.classification == "OK"
```
```

**Acceptance:**
- [ ] Guia de migração criado
- [ ] Exemplos de código incluídos
- [ ] Breaking changes documentados
- [ ] Novas features explicadas

---

### Task 3.3: Run full test suite and fix issues

**Description:** Executar test suite completo e corrigir problemas

**Commands:**
```bash
# Full test suite
pytest --cov=aoi_lib --cov=consumo_lib --cov-report=html --cov-report=term

# Run specific test categories
pytest tests/unit/ -v
pytest tests/integration/ -v

# Check coverage
pytest --cov-report=html
open htmlcov/index.html
```

**Acceptance:**
- [ ] Todos os testes passam (462 + novos)
- [ ] Coverage ≥ 30% (meta: +4.2%)
- [ ] Nenhum teste marcado como xfail
- [ ] Nenhum warning de pytest

---

### Task 3.4: Verify final checkpoint (all quality gates)

**Description:** Verificar todos os quality gates

**Quality Gates Checklist:**

**Code Quality:**
- [ ] Zero arquivos >1000 linhas ✅
- [ ] Zero arquivos >500 linhas (exceto exceções documentadas)
- [ ] Complexidade <15 por método
- [ ] Type hints em todo código novo
- [ ] Docstrings Google style

**Testing:**
- [ ] 100% dos testes passando
- [ ] Coverage ≥ 30%
- [ ] ≥20 novos testes criados
- [ ] Testes de integração para EventBus

**Performance:**
- [ ] Application startup time sem degradação significativa
- [ ] EventBus overhead <1ms por evento
- [ ] Thread de medição sem degradação

**Documentation:**
- [ ] CLAUDE.md atualizado
- [ ] Migration guide criado
- [ ] Spec completo
- [ ] Plan completo

**Compatibility:**
- [ ] Zero breaking changes em APIs públicas
- [ ] Imports antigos funcionam (deprecation warnings)
- [ ] Configuração JSON compatível
- [ ] Dados existentes funcionam

**Manual Testing:**
- [ ] Smoke test: Aplicação inicia sem erros
- [ ] Camera preview funcional
- [ ] Medição de tensão funcional
- [ ] Movement CNC funcional
- [ ] Inspeção visual funcional

---

### Task 3.5: Create final commit and documentation

**Description:** Commit final e documentação de conclusão

**Commit Message:**
```bash
git add -A
git commit -m "feat(conductor): SOLID Refactoring Phase 1 COMPLETE ✅

Track: solid_refactoring_phase1_20260114
Duration: 2 weeks (10 working days)
Status: ✅ COMPLETE

Achievements:
===============
Refactored 2 CRITICAL files (2,601 lines total):

1. aoi_lib/stencil_tension.py (1,409 lines → 4 modules)
   - aoi_lib/tensiometer/models.py (data structures)
   - aoi_lib/tensiometer/measurement_service.py (business logic)
   - aoi_lib/tensiometer/measurement_orchestrator.py (coordination)
   - aoi_lib/tensiometer/measurement_thread.py (execution)
   - consumo_lib/dialogs/tension/tension_measurement_dialog.py (UI)

2. consumo_lib/handlers/signal_aggregator.py (1,192 lines → <200 lines)
   - consumo_lib/event_bus.py (Event Bus infrastructure)
   - Auto-registration pattern
   - Removed 120+ connect_*() methods

Metrics:
========
Before → After
- Files >1000 lines: 2 → 0 ✅
- Score SOLID: 62/100 → 75/100 (+13)
- Complexity (stencil_tension): 85+ → <15 (-70)
- Complexity (signal_aggregator): 120+ → <15 (-105)
- Testability (without PyQt6): 0% → 80% (+80%)
- Test coverage: 25.81% → 30% (+4.2%)
- New unit tests: +20
- New integration tests: +5

Quality Gates:
=============
✅ Zero breaking changes in public APIs
✅ All tests passing (462 + 20 new = 482 tests)
✅ Coverage ≥ 30%
✅ Zero files >1000 lines
✅ Complexity <15 per method
✅ Smoke test verified (application starts without errors)
✅ Manual testing passed (all features functional)

Documentation:
=============
✅ CLAUDE.md updated with new architecture
✅ Migration guide created (docs/guides/SOLID_PHASE1_MIGRATION_GUIDE.md)
✅ Spec complete (spec.md)
✅ Plan complete (plan.md)

Next Steps:
===========
Phase 2: Refactor report_generator.py, fiducial_alignment_widget.py
Phase 3: Refactor stencil_inspector.py, implement Interface Segregation
See: docs/reports/SOLID_ANALYSIS_REPORT.md (Section: Refactoring Roadmap)

Co-Authored-By: RONALDBUZAGLO <senseironald@gmail.com>"
```

**Git Note:**
```bash
git notes add 9934e09 -m "SOLID Phase 1 Completion Summary
========================================

Track: solid_refactoring_phase1_20260114
Duration: 2 weeks
Status: ✅ COMPLETE

Key Commits:
- Phase 0: Setup & Analysis
- Phase 1: stencil_tension.py refactored (1,409 → 4 modules)
- Phase 2: EventBus implemented (SignalAggregator 1,192 → <200)
- Phase 3: Documentation & Polish

Highlights:
- Eliminated all CRITICAL SRP violations
- Improved testability from 0% to 80% (without PyQt6)
- Reduced complexity by 85+ points (stencil_tension)
- Implemented Event Bus pattern for decoupling
- Added 20 new unit tests, 5 integration tests

Metrics Before → After:
- Files >1000 lines: 2 → 0 ✅
- SOLID Score: 62/100 → 75/100
- Test Coverage: 25.81% → 30%
- Testability: 0% → 80%

Documentation:
- Migration guide: docs/guides/SOLID_PHASE1_MIGRATION_GUIDE.md
- CLAUDE.md: Updated with new architecture
- Spec: conductor/tracks/solid_refactoring_phase1_20260114/spec.md
- Plan: conductor/tracks/solid_refactoring_phase1_20260114/plan.md"
```

---

## Success Criteria

### General Criteria

- [ ] **Zero breaking changes** em APIs públicas
- [ ] **100% de testes passando** (462 + 20 novos = 482 tests)
- [ ] **Coverage ≥ 30%** (atual: 25.81%, meta: +4.2%)
- [ ] **Smoke test:** Aplicação inicia sem erros
- [ ] **Manual testing:** Features críticas funcionais

### Specific Criteria - stencil_tension.py

- [ ] **4 módulos criados** em `aoi_lib/tensiometer/`
- [ ] **Service layer 100% testável** sem PyQt6
- [ ] **Dialog reduzido** para <400 linhas
- [ ] **≥15 unit tests** para service layer
- [ ] **Complexidade < 15** por método

### Specific Criteria - signal_aggregator.py

- [ ] **EventBus implementado** (~150 linhas)
- [ ] **120+ métodos removidos**
- [ ] **SignalAggregator reduzido** para <200 linhas
- [ ] **≥5 integration tests** para EventBus
- [ ] **Auto-registration** implementado

### Quality Criteria

- [ ] **Zero arquivos >1000 linhas** ✅
- [ ] **Complexidade <15** por método
- [ ] **Type hints** em todo código novo
- [ ] **Docstrings** Google style
- [ ] **Logging** estruturado

---

## Definition of Done

Uma fase é considerada **DONE** quando:

1. ✅ Todas as tarefas da fase estão completas
2. ✅ Todos os testes passam (unit + integration)
3. ✅ Code review aprovado (auto-review via checklist)
4. ✅ Documentation atualizada
5. ✅ Checkpoint commit criado
6. ✅ Smoke test verificado

Uma track é considerada **DONE** quando:

1. ✅ Todas as fases estão completas
2. ✅ Todos os critérios de sucesso atendidos
3. ✅ Quality gates aprovados
4. ✅ Documentação completa (spec + plan + migration guide)
5. ✅ Final commit criado com resumo completo

---

## References

- [SOLID Analysis Report](../../../docs/reports/SOLID_ANALYSIS_REPORT.md)
- [Refactoring Completion Report](../../../docs/reports/REFACTORING_COMPLETION_REPORT.md)
- [CLAUDE.md](../../../CLAUDE.md)
- [workflow.md](../../workflow.md)

---

**Plan Version:** 1.0
**Last Updated:** 2026-01-14
**Next Review:** After Phase 0 completion
