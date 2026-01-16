# Especificação da Track: Setup Coordinator Refactoring

## Visão Geral

**Track ID:** setup_coordinator_refactoring_20260116
**Nome:** Setup Coordinator Refactoring - Dependency Injection
**Tipo:** Refactor
**Prioridade:** MEDIUM
**Data de Criação:** 2026-01-16
**Estimativa:** 2-3 dias

---

## Objetivo

Refatorar `consumo_lib/coordinators/setup_coordinator.py` (602 linhas, 47 instanciações diretas) aplicando **Dependency Injection Principle (DIP)** e **Facade Pattern** para reduzir acoplamento e melhorar testabilidade.

**Motivação:**
- 47 instanciações diretas dentro de SetupCoordinator (viola DIP)
- Alto acoplamento - difícil testar em isolamento
- Difícil substituir implementações (mock para testes)
- Orquestração complexa espalhada em 17 métodos privados

---

## Critérios de Aceite

### Funcional
- [ ] Criar 5 factories (Core, Managers, Coordinators, Handlers, Controllers, Services)
- [ ] Criar 3 facades (ApplicationComponentsFactory, SetupCoordinatorFacade, ConfigurationFacade)
- [ ] Refatorar SetupCoordinator para usar factories
- [ ] Injetar dependências via construtor
- [ ] Manter 100% backward compatibility

### Não-Funcional
- [ ] Zero breaking changes
- [ ] Testes unitários criados
- [ ] Documentação atualizada
- [ ] Linting sem erros

---

## Arquitetura Atual

### Arquivo: `consumo_lib/coordinators/setup_coordinator.py`

```
setup_coordinator.py (602 linhas)
└── SetupCoordinator
    ├── __init__(main_window_class)
    ├── setup(window)
    ├── _setup_basic_config()              # 1 instanciação
    ├── _setup_core_controller()            # 1 instanciação
    ├── _setup_managers()                  # 11 instanciações
    ├── _setup_coordinators()              # 4 instanciações
    ├── _setup_handlers()                  # 4 instanciações
    ├── _setup_controllers()               # 11 instanciações
    ├── _setup_services()                  # 2 instanciações
    ├── _setup_camera_config()             # configs
    ├── _setup_ui()                        # UI setup
    ├── _setup_dependent_controllers()     # 2 instanciações
    ├── _setup_keyboard_handler()          # configuração
    ├── _setup_menu()                      # menu setup
    ├── _setup_signals()                   # signal connection
    ├── _setup_ui_state()                  # estado inicial
    ├── _setup_auto_connect()              # auto-connect
    └── _setup_timers()                    # 1 instanciação
```

### Problemas Identificados

1. **Violação de DIP:** 47 instanciações diretas (alto acoplamento)
2. **Difícil testar:** Impossível mock de dependências
3. **Baixa coesão:** SetupCoordinator faz tudo (criação + orquestração)
4. **Difícil manter:** Mudar uma instanciação afeta todo o setup

---

## Análise das 47 Instanciações

### Por Categoria:

1. **Core (2 instanciações)**
   - `AOIConfigManager` → self.window.config
   - `CNCAOIController` → self.window.controller

2. **Managers (11 instanciações)**
   - `ConnectionManager` → self.window.connection_mgr
   - `RoleManager` → self.window.role_manager
   - `SessionLogger` → self.window.session_logger
   - `RecipeManagerWrapper` → self.window.recipe_manager_wrapper
   - `StencilManagerWrapper` → self.window.stencil_manager_wrapper
   - `ReportManagerWrapper` → self.window.report_manager_wrapper
   - `InspectionManager` → self.window.inspection_manager
   - + configs e trackers derivados

3. **Coordinators (4 instanciações)**
   - `ConnectionCoordinator` → self.window.connection_coordinator
   - `InspectionCoordinator` → self.window.inspection_coordinator
   - `TensionCoordinator` → self.window.tension_coordinator
   - `OperatorInspectionCoordinator` → self.window.operator_inspection_coordinator

4. **Handlers (4 instanciações)**
   - `KeyboardEventHandler` → self.window.keyboard_handler
   - `MenuHandler` → self.window.menu_handler
   - `GRBLCallbackHandler` → self.window.grbl_callback_handler
   - `DialogRouter` → self.window.dialog_router

5. **Controllers (11 instanciações)**
   - `RecipeManagerController` → self.window.recipe_manager_controller
   - `MapController` → self.window.map_controller
   - `CameraSettingsController` → self.window.camera_settings_controller
   - `CalibrationController` → self.window.calibration_controller
   - `InspectionUIController` → self.window.inspection_ui_controller
   - `ReportDialogController` → self.window.report_dialog_controller
   - `SequenceController` → self.window.sequence_controller
   - `FiducialAlignmentController` → self.window.fiducial_alignment_controller
   - `TensionMeasurementController` → self.window.tension_measurement_controller
   - `DialogManagerController` → self.window.dialog_manager_controller
   - `FileIOController` → self.window.file_io_controller
   - `PositionManagerController` → self.window.position_manager_controller

6. **Services (2 instanciações)**
   - `SequenceExecutionService` → self.window.sequence_execution_service
   - `ResourceManager` → self.window.resource_manager

7. **Utils/Other (2 instanciações)**
   - `QTimer` → self.window.update_timer
   - Configs (camera mirrors)

**Total: 36 instanciações diretas (excluindo configs e None assignments)**

---

## Arquitetura Proposta

### Nova Estrutura

```
consumo_lib/factories/
├── __init__.py
├── core_factory.py                    # CoreFactory (2 componentes)
├── managers_factory.py                # ManagersFactory (11 componentes)
├── coordinators_factory.py            # CoordinatorsFactory (4 componentes)
├── handlers_factory.py                # HandlersFactory (4 componentes)
├── controllers_factory.py             # ControllersFactory (11 componentes)
├── services_factory.py                # ServicesFactory (2 componentes)
└── application_components_factory.py  # ApplicationComponentsFactory (Facade)

consumo_lib/coordinators/
├── setup_coordinator.py               # Refatorado com DI
└── setup_coordinator_facade.py        # SetupCoordinatorFacade (opcional)

consumo_lib/facades/
└── configuration_facade.py            # ConfigurationFacade (nova)
```

### Responsabilidades

#### 1. Factories (Criação de Componentes)

**CoreFactory**
- Criar `AOIConfigManager`
- Criar `CNCAOIController`

**ManagersFactory**
- Criar todos os managers (11 componentes)
- Recebe config, controller, window como dependências

**CoordinatorsFactory**
- Criar todos os coordinators (4 componentes)
- Recebe managers como dependências

**HandlersFactory**
- Criar todos os handlers (4 componentes)
- Recebe window como dependência

**ControllersFactory**
- Criar todos os controllers (11 componentes)
- Recebe managers, config, controller, window como dependências

**ServicesFactory**
- Criar todos os services (2 componentes)
- Recebe controller, window como dependências

#### 2. Facades (Simplificação)

**ApplicationComponentsFactory**
- Facade que orquestra todas as factories
- Método `create_all_components(window)` retorna dict com todos os componentes
- Simplifica SetupCoordinator

**SetupCoordinatorFacade** (opcional)
- Facade que simplifica interface de SetupCoordinator
- Método simplificado `setup(window)` sem necessidade de conhecer detalhes

**ConfigurationFacade** (nova)
- Abstrai acesso a configurações
- Centraliza get() de config
- Facilita testes

---

## Implementação

### Fase 1: Análise do Arquivo Atual
**Objetivo:** Mapear todas as dependências

**Tarefas:**
1. ✅ Contar todas as instanciações (47 identificadas)
2. ✅ Agrupar por categoria (7 categorias)
3. ✅ Identificar dependências entre componentes
4. ✅ Documentar ordem de criação crítica

**Saída:**
- Documento de análise completo (nesta spec)

### Fase 2: Criar Factories
**Objetivo:** Extrair criação de componentes para factories

**Tarefas:**
1. Criar `CoreFactory` (2 componentes)
2. Criar `ManagersFactory` (11 componentes)
3. Criar `CoordinatorsFactory` (4 componentes)
4. Criar `HandlersFactory` (4 componentes)
5. Criar `ControllersFactory` (11 componentes)
6. Criar `ServicesFactory` (2 componentes)
7. Criar `ApplicationComponentsFactory` (Facade)

**Saída:**
- 7 arquivos de factory criados
- Cada factory com testes unitários

### Fase 3: Criar ConfigurationFacade
**Objetivo:** Abstrair acesso a configurações

**Tarefas:**
1. Criar `ConfigurationFacade` em `consumo_lib/facades/`
2. Methods: `get_plc_config()`, `get_camera_config()`, `get_inspection_config()`
3. Substituir `self.window.config.get()` em SetupCoordinator

**Saída:**
- `configuration_facade.py` criado
- SetupCoordinator simplificado

### Fase 4: Refatorar SetupCoordinator
**Objetivo:** Injetar factories via construtor

**Tarefas:**
1. Modificar `__init__()` para receber factories
2. Modificar métodos `_setup_*()` para usar factories
3. Remover instanciações diretas
4. Manter ordem crítica de setup

**Saída:**
- SetupCoordinator refatorado com DI
- Zero instanciações diretas

### Fase 5: Testes e Documentação
**Objetivo:** Garantir qualidade

**Tarefas:**
1. Criar testes unitários para cada factory
2. Criar testes para SetupCoordinator com mocks
3. Criar testes de integração (setup completo)
4. Atualizar CLAUDE.md
5. Criar CHANGELOG
6. Executar smoke test completo

**Saída:**
- Testes criados e passando
- Documentação atualizada
- Backward compatibility verificada

---

## Backward Compatibility

### Estratégia: Manter Interface Pública Inalterada

**ANTES (código existente):**
```python
from consumo_lib.coordinators import SetupCoordinator

coordinator = SetupCoordinator(AOIControllerApp)
coordinator.setup(window)
```

**DEPOIS (usa factories internamente):**
```python
from consumo_lib.coordinators import SetupCoordinator

coordinator = SetupCoordinator(AOIControllerApp)
coordinator.setup(window)  # Interface inalterada!
```

**Implementation:**
- Factories criadas com defaults internos
- SetupCoordinator cria factories se não fornecidas
- Interface pública mantida (setup(window))
- Código cliente não precisa mudar

---

## Riscos e Mitigações

### Risco 1: Ordem Crítica de Setup
**Nível:** MEDIUM
**Descrição:** Componentes dependem de outros (ordem é crítica)
**Mitigação:**
- Manter ordem exata de criação em factories
- Documentar dependências explicitamente
- Testar ordem de setup

### Risco 2: Quebra de Backward Compatibility
**Nível:** LOW
**Descrição:** Mudança interna pode afetar código cliente
**Mitigação:**
- Manter interface pública inalterada
- Criar factories com defaults
- Testar código existente

### Risco 3: Aumento de Complexidade
**Nível:** LOW
**Descrição:** Muitas factories podem aumentar complexidade
**Mitigação:**
- ApplicationComponentsFactory (Facade) simplifica uso
- Documentar claramente responsabilidade de cada factory
- Manter factories simples e focadas

---

## Métricas de Sucesso

### Quantitativas (Antes → Depois)
- **Instanciações diretas:** 47 → 0 (100% em factories)
- **Linhas setup_coordinator.py:** 602 → ~400 (33% redução)
- **Testabilidade:** 0% → 100% (fácil mock de factories)
- **Acoplamento:** Alto → Baixo (via DI)

### Qualitativas
- ✅ Baixo acoplamento (Dependency Injection)
- ✅ Alta coesão (cada factory focada)
- ✅ Fácil testar (mock de factories)
- ✅ Fácil manter (mudanças isoladas)
- ✅ Backward compatibility mantida

---

## Dependencies

### Internas
- `consumo_lib/coordinators/setup_coordinator.py`
- `consumo_lib/managers/*` (todos os managers)
- `consumo_lib/coordinators/*` (todos os coordinators)
- `consumo_lib/handlers/*` (todos os handlers)
- `consumo_lib/controllers/*` (todos os controllers)
- `consumo_lib/services/*` (todos os services)

### Externas
- PyQt6
- logging

---

## Definição de Done

A track está completa quando:
- [ ] 7 factories criadas (Core, Managers, Coordinators, Handlers, Controllers, Services, ApplicationComponents)
- [ ] ConfigurationFacade criado
- [ ] SetupCoordinator refatorado com DI
- [ ] Testes unitários criados e passando (mínimo 30 testes)
- [ ] Smoke test executado e passando
- [ ] Documentação atualizada (CLAUDE.md, CHANGELOG)
- [ ] Linting sem erros
- [ ] Backward compatibility verificada
- [ ] Metadata atualizado com status "complete"

---

*Generated by Conductor. Created: 2026-01-16*
*Track ID: setup_coordinator_refactoring_20260116*
