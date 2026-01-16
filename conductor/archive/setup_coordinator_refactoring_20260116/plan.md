# Plano da Track: Setup Coordinator Refactoring

## Visão Geral

Refatorar `consumo_lib/coordinators/setup_coordinator.py` (602 linhas, 47 instanciações) aplicando **Dependency Injection Principle (DIP)** e **Facade Pattern**.

**Track ID:** setup_coordinator_refactoring_20260116
**Type:** Refactor
**Created:** 2026-01-16
**Est. Duration:** 2-3 dias
**Priority:** Medium

---

## Fases

### Fase 1: Análise do Arquivo Atual ⏳ IN PROGRESS

**Objetivo:** Mapear todas as dependências e ordem de criação

#### Tarefas

##### 1.1. Mapear instanciações
- [x] 1.1.1. Contar todas as instanciações diretas ✅
  - **Resultado:** 47 instanciações identificadas
- [x] 1.1.2. Agrupar por categoria ✅
  - Core (2), Managers (11), Coordinators (4), Handlers (4), Controllers (11), Services (2), Utils (2)
- [x] 1.1.3. Identificar dependências entre componentes ✅
  - Managers → Core
  - Coordinators → Managers
  - Handlers → Window
  - Controllers → Managers + Core + Window
  - Services → Core + Window
- [x] 1.1.4. Documentar ordem crítica de setup ✅
  - Ordem: 1. Basic Config → 2. Core Controller → 3. Managers → 4. Coordinators → 5. Handlers → 6. Controllers → 7. Services → 8-16. Outros

##### 1.2. Criar especificação
- [x] 1.2.1. Criar spec.md com análise completa ✅
- [x] 1.2.2. Definir arquitetura proposta (7 factories + 3 facades) ✅
- [x] 1.2.3. Criar metadata.json ✅

#### Checkpoint Fase 1
- [x] Análise estrutural completa ✅
- [x] Especificação da track criada (spec.md) ✅
- [x] Metadata criado ✅
- **Status:** ✅ COMPLETE (pronto para implementação)

---

### Fase 2: Criar Factories ⏳ PENDING

**Objetivo:** Extrair criação de componentes para factories especializadas

#### Tarefas

##### 2.1. Criar diretório factories/
- [ ] 2.1.1. Criar `consumo_lib/factories/`
- [ ] 2.1.2. Criar `__init__.py` com exportações

##### 2.2. Criar CoreFactory
- [ ] 2.2.1. Criar `core_factory.py`
- [ ] 2.2.2. Implementar `create_config(window)` → AOIConfigManager
- [ ] 2.2.3. Implementar `create_controller(config)` → CNCAOIController
- [ ] 2.2.4. Adicionar type hints e docstrings
- [ ] 2.2.5. Criar testes unitários (2 testes)

##### 2.3. Criar ManagersFactory
- [ ] 2.3.1. Criar `managers_factory.py`
- [ ] 2.3.2. Implementar `create_all_managers(window, config, controller)`
- [ ] 2.3.3. Criar 11 managers (Connection, Role, Session, Recipe, Stencil, Report, Inspection)
- [ ] 2.3.4. Retornar dict com todos os managers
- [ ] 2.3.5. Criar testes unitários (5 testes)

##### 2.4. Criar CoordinatorsFactory
- [ ] 2.4.1. Criar `coordinators_factory.py`
- [ ] 2.4.2. Implementar `create_all_coordinators(window, config, controller, managers)`
- [ ] 2.4.3. Criar 4 coordinators (Connection, Inspection, Tension, OperatorInspection)
- [ ] 2.4.4. Retornar dict com todos os coordinators
- [ ] 2.4.5. Criar testes unitários (4 testes)

##### 2.5. Criar HandlersFactory
- [ ] 2.5.1. Criar `handlers_factory.py`
- [ ] 2.5.2. Implementar `create_all_handlers(window)`
- [ ] 2.5.3. Criar 4 handlers (Keyboard, Menu, GRBL, DialogRouter)
- [ ] 2.5.4. Retornar dict com todos os handlers
- [ ] 2.5.5. Criar testes unitários (4 testes)

##### 2.6. Criar ControllersFactory
- [ ] 2.6.1. Criar `controllers_factory.py`
- [ ] 2.6.2. Implementar `create_all_controllers(window, config, controller, managers)`
- [ ] 2.6.3. Criar 11 controllers
- [ ] 2.6.4. Retornar dict com todos os controllers
- [ ] 2.6.5. Criar testes unitários (8 testes)

##### 2.7. Criar ServicesFactory
- [ ] 2.7.1. Criar `services_factory.py`
- [ ] 2.7.2. Implementar `create_all_services(window, controller)`
- [ ] 2.7.3. Criar 2 services (SequenceExecution, ResourceManager)
- [ ] 2.7.4. Retornar dict com todos os services
- [ ] 2.7.5. Criar testes unitários (2 testes)

##### 2.8. Criar ApplicationComponentsFactory (Facade)
- [ ] 2.8.1. Criar `application_components_factory.py`
- [ ] 2.8.2. Implementar `create_all_components(window)` orquestrando todas as factories
- [ ] 2.8.3. Retornar dict unificado com todos os componentes
- [ ] 2.8.4. Adicionar type hints e docstrings
- [ ] 2.8.5. Criar testes unitários (3 testes)

#### Checkpoint Fase 2
- [ ] Diretório factories/ criado
- [ ] 7 factories criadas
- [ ] Testes unitários criados (28 testes)
- [ ] Commit: `git commit -m "feat(phase8-2): Create 7 factories for component creation"`

---

### Fase 3: Criar ConfigurationFacade ⏳ PENDING

**Objetivo:** Abstrair acesso a configurações

#### Tarefas

##### 3.1. Criar ConfigurationFacade
- [ ] 3.1.1. Criar `consumo_lib/facades/configuration_facade.py`
- [ ] 3.1.2. Implementar `get_plc_host()`, `get_plc_port()`
- [ ] 3.1.3. Implementar `get_camera_mirror_x()`, `get_camera_mirror_y()`
- [ ] 3.1.4. Implementar `get_inspection_thresholds()`
- [ ] 3.1.5. Adicionar type hints e docstrings
- [ ] 3.1.6. Criar testes unitários (5 testes)

##### 3.2. Integrar ConfigurationFacade
- [ ] 3.2.1. Modificar SetupCoordinator para usar ConfigurationFacade
- [ ] 3.2.2. Substituir `self.window.config.get()` por methods da facade
- [ ] 3.2.3. Testar smoke test

#### Checkpoint Fase 3
- [ ] ConfigurationFacade criado
- [ ] Integrado em SetupCoordinator
- [ ] Testes criados e passando
- [ ] Commit: `git commit -m "feat(phase8-3): Create ConfigurationFacade and integrate"`

---

### Fase 4: Refatorar SetupCoordinator ⏳ PENDING

**Objetivo:** Injetar factories via construtor e usar DI

#### Tarefas

##### 4.1. Modificar construtor
- [ ] 4.1.1. Adicionar parâmetros opcionais para factories no `__init__()`
- [ ] 4.1.2. Criar factories com defaults se não fornecidas
- [ ] 4.1.3. Armazenar factories como atributos

##### 4.2. Refatorar métodos _setup_*()
- [ ] 4.2.1. Modificar `_setup_basic_config()` para usar CoreFactory
- [ ] 4.2.2. Modificar `_setup_managers()` para usar ManagersFactory
- [ ] 4.2.3. Modificar `_setup_coordinators()` para usar CoordinatorsFactory
- [ ] 4.2.4. Modificar `_setup_handlers()` para usar HandlersFactory
- [ ] 4.2.5. Modificar `_setup_controllers()` para usar ControllersFactory
- [ ] 4.2.6. Modificar `_setup_services()` para usar ServicesFactory
- [ ] 4.2.7. Remover todas as instanciações diretas

##### 4.3. Criar SetupCoordinatorFacade (opcional)
- [ ] 4.3.1. Criar `setup_coordinator_facade.py` se necessário
- [ ] 4.3.2. Implementar facade simplificando interface

#### Checkpoint Fase 4
- [ ] SetupCoordinator refatorado com DI
- [ ] Zero instanciações diretas
- [ ] Testes de smoke test passando
- [ ] Commit: `git commit -m "feat(phase8-4): Refactor SetupCoordinator with DI"`

---

### Fase 5: Testes e Documentação ⏳ PENDING

**Objetivo:** Garantir qualidade e backward compatibility

#### Tarefas

##### 5.1. Criar testes unitários para SetupCoordinator
- [ ] 5.1.1. Criar `tests/unit/test_setup_coordinator.py`
- [ ] 5.1.2. Testar setup completo com mocks
- [ ] 5.1.3. Testar ordem de criação
- [ ] 5.1.4. Testar tratamento de erros

##### 5.2. Criar testes de integração
- [ ] 5.2.1. Criar `tests/integration/test_setup_coordinator_e2e.py`
- [ ] 5.2.2. Testar setup completo da aplicação
- [ ] 5.2.3. Testar backward compatibility

##### 5.3. Atualizar documentação
- [ ] 5.3.1. Atualizar CLAUDE.md
  - Adicionar seção "Factories" em consumo_lib/
  - Documentar ApplicationComponentsFactory
  - Atualizar diagrama de arquitetura
- [ ] 5.3.2. Criar CHANGELOG
  - Documentar mudança de arquitetura
  - Explicar benefícios (testabilidade, manutenibilidade)
  - Adicionar exemplos de uso

##### 5.4. Verificação final
- [ ] 5.4.1. Smoke test completo
  - Inicializar aplicação
  - Verificar todos os componentes criados
  - Verificar conectores de signals
- [ ] 5.4.2. Validar backward compatibility
  - Testar código cliente existente
  - Verificar se interface pública inalterada
- [ ] 5.4.3. Linting
  - pylint em todos os factories
  - pylint em SetupCoordinator refatorado
  - flake8 em todos os arquivos

#### Checkpoint Fase 5
- [ ] Testes criados e passando (30+ testes)
- [ ] CLAUDE.md atualizado
- [ ] CHANGELOG criado
- [ ] Smoke test passando
- [ ] Linting sem erros
- [ ] Commit: `git commit -m "feat(phase8-5): Complete tests and documentation"`

---

## Definição de Done

### Uma tarefa está completa quando:
- [ ] Código implementado conforme especificação
- [ ] Sintaxe verificada (python -m py_compile)
- [ ] Testes criados e passando
- [ ] Commit com mensagem convencional
- [ ] plan.md atualizado com status

### Uma fase está completa quando:
- [ ] Todas as tarefas da fase concluídas
- [ ] Testes da fase passando
- [ ] Checkpoint commit criado
- [ ] plan.md atualizado com checkpoint SHA

### A track está completa quando:
- [ ] Todas as 5 fases completadas
- [ ] Backward compatibility mantida
- [ ] Testes criados e passando (30+ testes)
- [ ] Documentação atualizada
- [ ] Linting sem erros
- [ ] Metadata atualizado com status "complete"
- [ ] Track movida para archive/ (opcional - parte de SOLID Phase 2)

---

## Recursos e Referências

### Documentos do Projeto
- **Spec:** `conductor/tracks/setup_coordinator_refactoring_20260116/spec.md`
- **Metadata:** `conductor/tracks/setup_coordinator_refactoring_20260116/metadata.json`
- **Product Context:** `conductor/product.md`
- **Tech Stack:** `conductor/tech-stack.md`
- **Workflow:** `conductor/workflow.md`
- **Code Guidelines:** `conductor/code_styleguides/python.md`

### Documentação Externa
- **CLAUDE.md:** Contexto completo do projeto
- **SOLID Refactoring Phase 2:** `conductor/tracks/solid_refactoring_phase2_20260114/plan.md`

### Referências Técnicas
- [Dependency Injection Principle](https://en.wikipedia.org/wiki/Dependency_inversion_principle)
- [Facade Pattern](https://en.wikipedia.org/wiki/Facade_pattern)
- [Factory Pattern](https://en.wikipedia.org/wiki/Factory_method_pattern)
- [Clean Code by Robert C. Martin](https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/dp/0132350882)

---

## Métricas de Sucesso

### Métricas Quantitativas (Antes → Depois)
- **Instanciações diretas:** 47 → 0 (100% em factories)
- **Linhas setup_coordinator.py:** 602 → ~400 (33% redução)
- **Arquivos de factories:** 0 → 7
- **Testes unitários:** 0 → 30+

### Métricas Qualitativas
- ✅ Baixo acoplamento (Dependency Injection)
- ✅ Alta coesão (cada factory focada)
- ✅ Fácil testar (mock de factories)
- ✅ Fácil manter (mudanças isoladas)
- ✅ Backward compatibility mantida

---

*Generated by Conductor. Created: 2026-01-16*
*Last updated: 2026-01-16*
*Track ID: setup_coordinator_refactoring_20260116*
