# SOLID Refactoring Phase 1 - Specification

**Track ID:** solid_refactoring_phase1_20260114
**Type:** Refactor
**Priority:** 🔴 CRITICAL
**Created:** 2026-01-14
**Est. Duration:** 2 weeks
**Sprint:** 1

---

## Executive Summary

Esta track foca na refatoração dos **2 arquivos mais críticos** do projeto Tensiometro, identificados no SOLID Analysis Report (2026-01-14). Ambos os arquivos violam massivamente o princípio SRP (Single Responsibility Principle) e apresentam complexidade extrema.

**Objetivo:** Reduzir complexidade, melhorar testabilidade e eliminar violações CRÍTICAS dos princípios SOLID.

**Meta de Melhoria:** Score SOLID 62/100 → 75/100

---

## Problem Statement

### Arquivo 1: `aoi_lib/stencil_tension.py` (1,409 linhas)

**Violações Detectadas:**
- 🔴 **SRP**: 4 classes com responsabilidades misturadas
- 🔴 **DIP**: Dependências diretas de classes concretas
- 🔴 **OCP**: If/else chains para configurações

**Classes Problemáticas:**

1. **TensiometerSerialManager** (linhas 33-201)
   - Gerencia conexão serial
   - Decodifica frames do protocolo AS-120N
   - Lista portas disponíveis
   - ✅ **Status:** Aceitável (única responsabilidade clara)

2. **TensionMeasurementThread** (linhas 203-324)
   - ❌ ORQUESTRAÇÃO: Controla fluxo de medição
   - ❌ NEGÓCIO: Calcula grid de medição
   - ❌ HARDWARE: Move PLC, lê tensiômetro
   - ❌ UI: Emite signals para PyQt6
   - **Problema:** Impossível testar sem mocks complexos

3. **StencilTensionMeasurement** (linhas 326-445)
   - ❌ NEGÓCIO: Lógica de grid NxN
   - ❌ VALIDAÇÃO: Valida dados de medição
   - ❌ CÁLCULO: Estatísticas (média, desvio padrão)
   - ❌ PERSISTÊNCIA: Salva/carrega rotinas JSON
   - **Problema:** Múltiplas razões para mudar

4. **StencilTensionDialog** (linhas 447-1409)
   - ❌ UI: Layout complexo (962 linhas!)
   - ❌ PERSISTÊNCIA: Gerencia rotinas de medição
   - ❌ COORDENAÇÃO: Controla medição
   - ❌ VALIDAÇÃO: Valida formulários
   - **Problema:** God Dialog - faz de tudo

**Impacto:**
- Alterar protocolo serial → Afeta 4 classes
- Mudar layout UI → Risco de quebrar lógica de medição
- Testar unitariamente → Impossível sem PyQt6
- Reutilizar lógica → Acoplado a QDialog

---

### Arquivo 2: `consumo_lib/handlers/signal_aggregator.py` (1,192 linhas)

**Violações Detectadas:**
- 🔴 **SRP**: God Object anti-pattern
- 🔴 **ISP**: Interface gigantesca (120+ métodos)
- 🔴 **DIP**: Dependências para TODAS as classes do projeto

**Problemas:**

1. **God Object**: Única classe para TODO signal routing
   - 120+ métodos `connect_*()` repetitivos
   - Gerencia TODOS os sinais do projeto
   - Single Point of Failure

2. **Anti-Pattern:** Repetição massiva
   ```python
   def connect_camera_controller(self, controller):
       if controller:
           controller.frame_updated.connect(self.on_camera_frame_updated)

   def connect_tension_controller(self, controller):
       if controller:
           controller.measurement_completed.connect(self.on_tension_measurement_completed)

   # ... 118+ métodos similares
   ```

3. **Acoplamento Excessivo:**
   - Conhece TODAS as classes do projeto
   - Qualquer mudança em um controller → afeta SignalAggregator
   - Impossível testar em isolação

**Impacto:**
- Manter sinal novo → Adicionar método em SignalAggregator
- Testar componente → Mockar SignalAggregator
- Remover controller → Risco de quebrar SignalAggregator

---

## Solution Approach

### Refatoração 1: stencil_tension.py

**Estrutura Proposta:**

```
aoi_lib/tensiometer/
├── __init__.py
├── serial_protocol.py           # TensiometerSerialManager (OK como está)
├── models.py                    # Dataclasses (TensionPoint, GridConfig, etc.)
├── measurement_service.py       # Lógica de negócio PURA
├── measurement_orchestrator.py  # Orquestração (sem UI)
└── measurement_thread.py        # Thread apenas para execução

consumo_lib/dialogs/tension/
└── tension_measurement_dialog.py  # Apenas UI (delega para serviços)
```

**Separação de Responsabilidades:**

| Componente | Responsabilidade | Depende de | Testável sem PyQt6? |
|------------|------------------|------------|---------------------|
| **serial_protocol.py** | Protocolo AS-120N | Nenhum | ✅ Sim |
| **models.py** | Data structures | Nenhum | ✅ Sim |
| **measurement_service.py** | Lógica de grid, cálculos | Models | ✅ Sim |
| **measurement_orchestrator.py** | Coordena PLC + Tensiômetro | Service, PLC, Serial | ✅ Sim |
| **measurement_thread.py** | Execução em background | Orchestrator | ✅ Sim |
| **tension_measurement_dialog.py** | UI apenas | Orchestrator, Thread | ❌ Não (esperado) |

---

### Refatoração 2: signal_aggregator.py

**Padrão Proposto:** Event Bus (Publish/Subscribe)

**Estrutura:**

```python
# Novo arquivo: consumo_lib/event_bus.py

class EventBus:
    """Bus centralizado de eventos pub/sub"""

    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, handler: Callable):
        """Inscreve handler para tipo de evento"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def publish(self, event: Event):
        """Publica evento para todos subscribers"""
        handlers = self._subscribers.get(event.type_, [])
        for handler in handlers:
            handler(event)

    def unsubscribe(self, event_type: str, handler: Callable):
        """Remove inscrição de handler"""
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(handler)
```

**Uso:**

```python
# Cada componente registra seus próprios eventos
class CameraController:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        # Auto-registration
        self.event_bus.subscribe("camera.capture_requested", self.on_capture)

    def capture_frame(self):
        frame = self._do_capture()
        # Publica evento
        self.event_bus.publish(Event("camera.frame_captured", frame=frame))
```

**Benefícios:**
- ✅ Desacoplamento: Componentes não se conhecem
- ✅ Extensibilidade: Adicionar eventos sem modificar EventBus
- ✅ Testabilidade: Mockar EventBus é simples
- ✅ Remoção de 120+ métodos repetitivos

---

## Acceptance Criteria

### Critérios Gerais

- [ ] **Zero breaking changes** em APIs públicas
- [ ] **100% de testes passando** (atual: 462 tests)
- [ ] **Coverage ≥ 25%** (atual: 25.81%)
- [ ] **Smoke test:** Aplicação inicia sem erros

### Critérios Específicos - stencil_tension.py

- [ ] **4 módulos criados** em `aoi_lib/tensiometer/`
- [ ] **Módulo service** testável sem PyQt6
- [ ] **Módulo orchestrator** sem dependências de UI
- [ ] **Dialog** reduzido para <400 linhas
- [ ] **Testes unitários** para service layer (≥10 testes)

### Critérios Específicos - signal_aggregator.py

- [ ] **EventBus implementado** (~100 linhas)
- [ ] **Auto-registration** para componentes
- [ ] **120+ métodos connect_*() removidos**
- [ ] **SignalAggregator reduzido** para <200 linhas
- [ ] **Testes de integração** para EventBus (≥5 testes)

### Critérios de Qualidade

- [ ] **Complexidade ciclomática < 15** por método
- [ ] **Cada arquivo < 500 linhas**
- [ ] **Type hints** em todo código novo
- [ ] **Docstrings** em formato Google
- [ ] **Logging** estruturado com contexto

---

## Non-Functional Requirements

### Performance
- ⚱️ **Overhead de EventBus < 1ms** por evento publish
- ⚱️ **Thread de medição** sem degradação de performance
- ⚱️ **Startup time** sem aumento significativo

### Maintainability
- 📖 **Código autodocumentado** (nomes descritivos)
- 📖 **Separação clara** de camadas (UI → Orchestration → Business → Hardware)
- 📖 **Fácil de estender** (aberto/fechado)

### Testability
- 🧪 **Service layer 100% testável** sem PyQt6
- 🧪 **EventBus mockável** em testes unitários
- 🧪 **Orchestrator testável** com mocks de PLC/Serial

### Backward Compatibility
- ✅ **APIs públicas mantidas**
- ✅ **Import paths funcionam** (deprecation warnings se necessário)
- ✅ **Configuração JSON compatível**
- ✅ **Dados existentes** (rotinas de medição) funcionam

---

## Dependencies

### Dependências Internas

- `aoi_lib/plc_axis_controller.py` - Movimento CNC
- `aoi_lib/camera_controller.py` - Captura de imagens (se necessário)
- `consumo_lib/main_window.py` - Integração com UI principal

### Dependências Externas

- **PyQt6** - UI components
- **pyserial** - Comunicação serial
- **pymodbus** - Comunicação Modbus TCP

### Blocks

- ❌ **Não bloqueia** outras tracks
- ⚠️ **Pode afetar** testes que usam `stencil_tension.py` diretamente
- ⚠️ **Pode afetar** integrações com SignalAggregator

---

## Risks & Mitigation

### Risk 1: Breaking Changes em Imports

**Probabilidade:** ALTA
**Impacto:** ALTO

**Mitigação:**
- Manter compatibility shims em `aoi_lib/stencil_tension.py`
- Deprecation warnings para imports antigos
- Testes de regressão antes/depois

### Risk 2: Performance Degradation com EventBus

**Probabilidade:** MÉDIA
**Impacto:** MÉDIO

**Mitigação:**
- Benchmark de publish/subscribe
- Usar tipo hints otimizados
- Lazy loading de subscribers

### Risk 3: Complexidade de Migração de Sinais PyQt6

**Probabilidade:** ALTA
**Impacto:** ALTO

**Mitigação:**
- Migração gradual (fase 1: críticos, fase 2: resto)
- Adaptador PyQt6 ↔ EventBus durante transição
- Testes manuais de UI após migração

---

## Success Metrics

### Métricas Quantitativas

| Métrica | Antes | Depois | Meta |
|---------|-------|--------|------|
| **Arquivos >1000 linhas** | 2 | 0 | ✅ 0 |
| **Arquivos >500 linhas** | 36 | 34 | -2 |
| **Score SOLID** | 62/100 | 75/100 | +13 |
| **Complexidade stencil_tension** | 85+ | <15 | -70 |
| **Complexidade signal_aggregator** | 120+ | <15 | -105 |
| **Testability (sem PyQt6)** | 0% | 80% | +80% |
| **Cobertura de testes** | 25.81% | ≥30% | +4.2% |

### Métricas Qualitativas

- ✅ **Separação clara** de responsabilidades
- ✅ **Código testável** sem dependências de UI
- ✅ **Fácil de estender** (aberto para extensão)
- ✅ **Fácil de manter** (fechado para modificação)
- ✅ **Zero God Objects** (objetos com >1000 linhas)

---

## Out of Scope

### Não incluído nesta fase:

- ❌ Refatoração de `report_generator.py` (Fase 2)
- ❌ Refatoração de `fiducial_alignment_widget.py` (Fase 2)
- ❌ Implementação de DI container global (Fase 2)
- ❌ Refatoração de `stencil_inspector.py` (Fase 3)
- ❌ Interface Segregation (Fase 3)
- ❌ Command Pattern para PLC (Fase 3)

### Rationale

Focar nos **2 arquivos mais críticos** com maior ROI (Return on Investment) em 2 semanas. Demais violações serão tratadas nas fases subsequentes (ver roadmap em `docs/reports/SOLID_ANALYSIS_REPORT.md`).

---

## References

- [SOLID Analysis Report](../../../docs/reports/SOLID_ANALYSIS_REPORT.md) - Análise completa
- [Refactoring Completion Report](../../../docs/reports/REFACTORING_COMPLETION_REPORT.md) - Refatoração anterior
- [CLAUDE.md](../../../CLAUDE.md) - Guidelines do projeto
- [workflow.md](../../workflow.md) - Workflow de desenvolvimento

---

**Spec Version:** 1.0
**Last Updated:** 2026-01-14
**Author:** Architecture Team via SOLID Analysis
