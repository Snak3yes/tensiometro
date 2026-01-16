# Spec: PLC Controller Refactoring - Interface Segregation

## Track Information

- **Track ID:** plc_refactoring_phase5_20260116
- **Name:** PLC Controller Refactoring - Interface Segregation
- **Type:** Refactor
- **Priority:** 🔴 HIGH
- **Created:** 2026-01-16
- **Est. Duration:** 3-5 days
- **Phases:** 7

## Problem Statement

O arquivo `aoi_lib/plc_axis_controller.py` tem **738 linhas** e **37 métodos públicos**, violando o **Interface Segregation Principle (ISP)** da SOLID. Isso dificulta:

1. **Testabilidade:** Classe monolítica difícil de testar em isolamento
2. **Manutenibilidade:** 37 métodos em uma classe complexa
3. **Acoplamento:** Muitas responsabilidades em uma classe
4. **Extensibilidade:** Difícil adicionar novos recursos sem modificar classe existente

### Metas de Qualidade

- **Interface Segregation:** Interfaces ABC segregadas (<15 métodos por interface)
- **Single Responsibility:** Cada classe com uma responsabilidade única
- **Dependency Inversion:** Dependências de interfaces, não de classes concretas
- **Open/Closed:** Fácil estender sem modificar código existente
- **Backward Compatibility:** Interface pública mantida via Adapter Pattern

### Current State

**Arquivo alvo:** `aoi_lib/plc_axis_controller.py`
- **Linhas:** 738 linhas 🔴 CRÍTICO
- **Métodos públicos:** 37 métodos 🔴 ALTO ISP
- **Classes:** 1 classe monolítica (PLCAxisController)
- **Imports:** 2 imports ✅ BOM (baixo acoplamento)
- **Complexidade:** Alta (múltiplas responsabilidades misturadas)

### Responsabilidades Identificadas

1. **Connection Management (4 métodos):**
   - `connect()`, `disconnect()`, `close()`, `set_connection_params()`

2. **Absolute Movement (4 métodos):**
   - `move_absolute()`, `move_to_absolute_position()`, `set_zero()`, `_apply_motion_pulses()`

3. **Relative Movement (3 métodos):**
   - `move_relative()`, `_move_relative_single_axis()`, `step_move()`

4.  **Jog Movement (3 métodos):**
   - `jog_start()`, `jog_stop()`, `jog()` (se existir)

5. **Homing (3 métodos):**
   - `home_all()`, `home_axis()`, `unlock()`

6. **Position Reading (3 métodos):**
   - `get_current_position()`, `read_position()`, `read_register()`

7. **Coil/Register Operations (8 métodos):**
   - `pulse_coil()`, `read_coil()`, `write_coil()`, `read_dword()`, `write_dword()`, `write_register()`, `snapshot_registers()`

8. **Idle/Waiting (2 métodos):**
   - `wait_for_idle()`, `_wait_for_idle_axis()`

9. **Backlight Control (5 métodos):**
   - `backlight_is_on()`, `backlight_set()`, `backlight_toggle()`, `backlight_turn_on()`, `backlight_turn_off()`

10. **Feed Rate (1 método):**
    - `_clamp_feed_rate()`

## Solution Approach

### Arquitetura Proposta

```
aoi_lib/plc/
├── interfaces/
│   ├── plc_connection_interface.py (ABC) - Connection management
│   ├── plc_absolute_movement_interface.py (ABC) - Absolute movement
│   ├── plc_relative_movement_interface.py (ABC) - Relative movement
│   ├── plc_jog_movement_interface.py (ABC) - Jog movement
│   ├── plc_homing_interface.py (ABC) - Homing operations
│   ├── plc_position_reader_interface.py (ABC) - Position reading
│   └── plc_register_interface.py (ABC) - Register operations
│
├── controllers/
│   ├── plc_connection_manager.py - Implementa IPLCConnection
│   ├── plc_absolute_movement_controller.py - Implementa IPLCAbsoluteMovement
│   ├── plc_relative_movement_controller.py - Implementa PLCRelativeMovement
│   ├── plc_jog_movement_controller.py - Implementa PLCJogMovement
│   ├── plc_homing_controller.py - Implementa IPLCHoming
│   ├── plc_position_reader_controller.py - Implementa IPLCPositionReader
│   └── plc_registers_controller.py - Implementa IPLCRegisterOperations
│
├── plc_axis_controller_adapter.py - Adapter pattern para backward compatibility
└── plc_axis_controller.py → (depreciado, mas mantido por backward compatibility)
```

### Padrões de Design

1. **Interface Segregation Principle (ISP):**
   - 7 interfaces ABC especializadas
   - Cada interface com 3-8 métodos
   - Baixo acoplamento entre componentes

2. **Adapter Pattern:**
   - `PLCAxisControllerAdapter` mantém interface pública original
   - Delega para controllers especializados
   - Zero breaking changes

3. **Dependency Inversion:**
   - Controllers dependem de interfaces, não de classes concretas
   - Baixo acoplamento entre módulos

4. **Strategy Pattern (já aplicado em fases anteriores):**
   - Cada controller implementa uma estratégia de movimento
   - Fácil adicionar novos tipos de movimento no futuro

## Implementation Strategy

### Fase 1: Interfaces ABC (JÁ CRIADO) ✅

✅ **Concluído:**
- Interfaces ABC criadas em `aoi_lib/plc/interfaces/`
- 7 interfaces definidas:
  - `IPLCConnection` - Connection management
  - `IPLCAbsoluteMovement` - Absolute movement
  - - `PLCRelativeMovement` - Relative movement
  - - `PLCJogMovement` - Jog movement
  - - `IPLCHoming` - Homing operations
  - `IPLCPositionReader` - Position reading
  - `IPLCRegisterOperations` - Register operations

### Fase 2: Controllers Especializados (7 controllers)

**Meta:**
- Criar 7 controllers, cada um implementando uma interface
- Cada controller com 3-8 métodos
- 100% testável sem PyQt6

**Controllers a criar:**
1. `PLCConnectionManager` (JÁ CRIADO ✅)
2. `PLCAbsoluteMovementController`
3. `PLCRelativeMovementController`
4. `PLCJogMovementController`
5. `PLCHomingController`
6. `PLCPositionReaderController`
7. `PLCRegistersController`

### Fase 3: Testes Unitários

**Meta:**
- Testes isolados para cada controller
- 100% cobertura do código novo
- Zero dependência de hardware real

### Fase 4: Adapter Pattern

**Meta:**
- `PLCAxisControllerAdapter` mantém interface pública compatível
- Delega para controllers especializados
- Zero breaking changes

### Fase 5: Atualização de main_window.py

**Meta:**
- Substituir `PLCAxisController` por `PLCAxisControllerAdapter`
- Testar smoke test
- Validação manual de todas as features

### Fase 6: Documentação

- Atualizar CLAUDE.md
- Criar CHANGELOG
- Atualizar plan.md com status final

### Fase 7: Checkpoint Final

- Commit de checkpoint
- Atualizar metadata.json
- Arquivar documentação
- Tag: `plc_refactoring_phase5_20260116-complete`

## Acceptance Criteria

### Métricas Quantitativas

**Antes:**
- 738 linhas em 1 arquivo
- 37 métodos públicos em 1 classe
- 1 responsabilidade misturada

**Depois:**
- 7 interfaces ABC (<15 métodos cada)
- 7 controllers especializados (3-8 métodos cada)
- 1 adapter para compatibilidade
- Testes: >80% coverage

### Métricas Qualitativas

- ✅ **Interface Segregation:** Interfaces segregadas implementadas
- ✅ **Single Responsibility:** Cada classe com uma responsabilidade única
- ✅ **Testabilidade:** 100% testável sem PyQt6
- ✅ **Backward Compatibility:** Interface pública mantida via Adapter
- ✅ **Zero Breaking Changes:** Funcionalidade preservada

## Dependencies

- **Documentos:**
  - `conductor/product.md`
  - `conductor/product-guidelines.md`
  - `conductor/tech-stack.md`
  - `conductor/workflow.md`

- **Tracks Relacionados:**
  - `conductor/archive/solid_refactoring_phase2_20260114/` - Track principal

- **Análise SOLID:**
  - `docs/reports/SOLID_ANALYSIS_REPORT_2026-01-14.md`

## Risk Assessment

**Risco BAIXO:** ✅
- Zero breaking changes planejados
- Adapter Pattern garante compatibilidade
- Interfaces bem definidas

**Risco MÉDIO:** ⚠️
- Complexidade de adaptador para gerenciar 7 componentes
- Necessário garantir sincronização de estado entre controllers

**Risco ALTO:** ❌
- Múltiplos components podem introduzir bugs sutis
- Testes precisam cobrir todas as combinações

**Mitigação:**
- Testes abrangentes em todas as interfaces
- Adapter com logging extensivo
- Validação manual cuidadosa com hardware real

## Timeline Estimada

- **Dia 1:** Fase 1 (Interfaces) + Fase 2 (Controllers)
- **Dia 2:** Fase 3 (Testes) + Fase 4 (Adapter)
- **Dia 3:** Fase 5 (Atualização MainWindow) + Fase 6 (Documentação)
- **Dia 4:** Fase 7 (Checkpoint)

## Notes

- **Backward Compatibility CRÍTICA:** Interface pública `PLCAxisController` deve ser mantida via Adapter
- **Zero breaking changes:** Todos os métodos existentes devem funcionar como antes
- **Hardware Dependencies:** Requer PLC real para testes de integração
- **Rollback Strategy:** Git tags para cada fase fácil de reverter

---

**Track Owner:** RONALDBUZAGLO
**Created:** 2026-01-16
**Status:** ✅ Pronto para implementação
