# Conductor - Tensiometro Project

**Status:** ✅ Setup Complete
**Last Updated:** 2026-01-15
**Version:** 1.0

---

## Overview

Conductor é o sistema de gerenciamento de desenvolvimento do projeto **Tensiometro** - Sistema AOI (Automated Optical Inspection) para controle de qualidade de stencils em SMT (Surface Mount Technology).

O Conductor organiza o desenvolvimento em **tracks** (funcionalidades/bug fixes), divididos em **phases** (etapas), compostas por **tasks** (tarefas), seguindo princípios **SOLID** e **TDD** (Test-Driven Development).

---

## Project Vision

**Tensiometro** é um sistema de automação industrial para:

- Medição de tensão superficial de stencils via tensiômetro AS-120N
- Inspeção visual automática (AOI) comparando imagem com arquivos Gerber
- Controle de hardware via CLP (Modbus TCP) para movimento preciso de eixos
- Rastreabilidade completa com banco de dados e relatórios PDF

**Usuários:**
- **Operadores:** Execução de inspeções/medições predefinidas
- **Qualidade:** Análise de históricos e geração de relatórios
- **Engenharia:** Criação de receitas, configuração de parâmetros, manutenção

---

## Directory Structure

```
conductor/
├── product.md                 # ✅ Visão do produto
├── product-guidelines.md      # ✅ Diretrizes (UI/UX, design)
├── tech-stack.md              # ✅ Stack tecnológica
├── workflow.md                # ✅ Protocolo de desenvolvimento (CRITICAL)
├── tracks.md                  # ✅ Registro de todos os tracks
├── setup_state.json           # ✅ Estado do setup
├── README.md                  # ✅ Este arquivo
│
├── code_styleguides/          # Guías de estilo por linguagem
│   └── python.md              # ✅ Google Python Style Guide
│
├── tracks/                    # 🔄 Tracks ativos (vazio no momento)
│   └── {track_id}/
│       ├── spec.md            # Especificação da funcionalidade
│       ├── plan.md            # Plano de implementação (fases + tasks)
│       └── metadata.json      # Metadados do track
│
└── archive/                   # ✅ Tracks completados
    ├── solid_refactoring_phase1_20260114/
    ├── solid_refactoring_phase2_20260114/  # Phase 3 complete!
    ├── engenharia_aba[1-7]*/  # Engineering Wizard (100% complete)
    └── [outros tracks]...
```

---

## Quick Start

### 1. Ver Status do Projeto

```bash
/conductor-status
```

Mostra tracks ativos, fases em progresso, e tasks pendentes.

### 2. Criar Novo Track

```bash
/conductor-newtrack
```

Cria nova funcionalidade/bug fix com:
- `spec.md` - Especificação detalhada
- `plan.md` - Plano de implementação com fases e tasks
- `metadata.json` - Metadados do track

### 3. Implementar Track Atual

```bash
/conductor-implement
```

Segue workflow.md para implementar tasks:
1. Selecionar task
2. Analisar testes existentes
3. Planejar implementação
4. TDD Red (escrever testes que falham)
5. TDD Green (implementar mínimo para passar)
6. TDD Refactor (melhorar código)
7. Documentar
8. Verificar (testes, coverage, linter)
9. Marcar task completa
10. Review
11. Próxima task

---

## Current Status

### Active Tracks

**Nenhum track ativo no momento.**

Último track completo:
- **SOLID Refactoring Phase 3** (2026-01-15)
  - AlignmentWidget refatorado (1,179 → 1,019 linhas, -13.6%)
  - 3 services criados (FiducialAlignmentService, TemplateMatchingService, AlignmentState)
  - 102 testes unitários (100% pass rate)
  - Tag: `solid_refactoring_phase3_20260115-complete`

### Completed Tracks

Veja `tracks.md` para lista completa de tracks completados, incluindo:

- ✅ **SOLID Refactoring Phase 1** (2026-01-14) - Stencil Tension refactoring
- ✅ **SOLID Refactoring Phase 2** (2026-01-14) - Database Layer (Repository Pattern)
- ✅ **SOLID Refactoring Phase 3** (2026-01-15) - Alignment Widget (Service Layer)
- ✅ **Engineering Wizard - 7 Abas** (2026-01-13) - Interface completa para engenharia
- ✅ **Integrate Engineering Wizard** (2026-01-14) - Orquestrador + state management
- ✅ **Refactor Large Files** (2026-01-14) - 3 arquivos monolíticos refatorados

---

## Development Workflow

### Task Workflow (11 Passos)

1. **Task Selection** - Selecionar próxima task pendente
2. **Test Analysis** - Analisar testes existentes
3. **Implementation Planning** - Planejar estrutura
4. **Test-First (TDD Red)** - Escrever testes que falham
5. **Implementation (TDD Green)** - Implementar mínimo para passar
6. **Refactoring (TDD Refactor)** - Melhorar código mantendo testes verdes
7. **Documentation** - Adicionar docstrings, atualizar docs
8. **Verification** - Rodar testes, coverage, linter
9. **Mark Task Complete** - Atualizar plan.md, commit
10. **Review** - Verificar SOLID, compatibilidade, qualidade
11. **Next Task** - Repetir ou completar fase

### Quality Gates

Uma fase só é completa quando:

- ✅ Todas as tasks marcadas como [x]
- ✅ 100% dos testes passando
- ✅ >80% cobertura de testes
- ✅ Linter clean (pylint, flake8)
- ✅ Documentação atualizada
- ✅ Zero breaking changes

### Commit Guidelines

```bash
git commit -m "feat(scope): Subject

- Achievement 1
- Achievement 2

SOLID principles applied:
- SRP: Single Responsibility
- DIP: Dependency Inversion
- OCP: Open/Closed

Breaking changes: None
Backward compatibility: Maintained"

Refs: #123
Co-Authored-By: Claude Sonnet <noreply@anthropic.com>
```

---

## Code Style

### Python (Google Python Style Guide)

- **Linting:** `pylint`, `flake8`
- **Line length:** Máximo 80 caracteres
- **Indentation:** 4 espaços (nunca tabs)
- **Docstrings:** Google style (`"""triple double quotes"""`)
- **Type hints:** Fortemente recomendado para APIs públicas
- **Naming:**
  - Modules/functions/variables: `snake_case`
  - Classes: `PascalCase`
  - Constants: `ALL_CAPS_WITH_UNDERSCORES`
  - Internal: `_leading_underscore`

Veja `code_styleguides/python.md` para detalhes completos.

---

## SOLID Principles

O projeto segue rigorosamente os princípios SOLID:

1. **SRP (Single Responsibility Principle)**
   - Cada classe/módulo tem uma única responsabilidade
   - Exemplo: Widget = UI, Service = Business Logic, Model = Data

2. **OCP (Open/Closed Principle)**
   - Aberto para extensão, fechado para modificação
   - Exemplo: Injeção de dependência, strategy pattern

3. **LSP (Liskov Substitution Principle)**
   - Subclasses podem substituir classes base sem quebrar código
   - Exemplo: Interfaces implementadas corretamente

4. **ISP (Interface Segregation Principle)**
   - Interfaces específicas, não genéricas
   - Exemplo: ITemplateMatchingStrategy (método único)

5. **DIP (Dependency Inversion Principle)**
   - Depender de abstrações, não de implementações concretas
   - Exemplo: Service injection via constructor

---

## Testing Strategy

### Test Organization

```
tests/
├── unit/                   # Testes rápidos, sem dependências externas
│   ├── test_services/      # Lógica de negócio
│   ├── test_models/        # Modelos de dados
│   └── test_widgets/       # Lógica de widgets (sem renderizar PyQt6)
├── integration/            # Testes de integração
│   ├── test_hardware/      # Integração com hardware
│   └── test_workflows/     # Fluxos completos
└── fixtures/               # Dados de teste e mocks
```

### Coverage Goals

- **Business Logic (Services):** >90% coverage
- **Models:** >90% coverage
- **UI (Widgets):** >70% coverage (difícil devido ao PyQt6)
- **Overall:** >80% coverage

### Running Tests

```bash
# All tests
pytest tests/ -v

# Unit tests only
pytest tests/unit/ -v

# With coverage
coverage run -m pytest tests/
coverage report
coverage html  # Generate HTML report

# Specific test file
pytest tests/unit/services/test_fiducial_alignment_service.py -v
```

---

## Key Documents

### Conductor Configuration

- **product.md** - Visão do produto, usuários, objetivos
- **product-guidelines.md** - Diretrizes de UI/UX e design
- **tech-stack.md** - Stack tecnológica (Python, PyQt6, OpenCV, etc)
- **workflow.md** - Protocolo de desenvolvimento (CRITICAL)
- **tracks.md** - Registro de todos os tracks

### Project Documentation

- **CLAUDE.md** - Contexto completo do projeto para Claude Code
- **README.md** (root) - Visão geral do projeto Tensiometro
- **docs/** - Documentação técnica, guias, relatórios

### Track Documentation

Cada track tem:
- **spec.md** - O que será implementado
- **plan.md** - Como será implementado (fases + tasks)
- **metadata.json** - Metadados (status, timestamps)

---

## Tools and Commands

### Development

```bash
# Run tests
pytest tests/ -v

# Coverage
coverage run -m pytest tests/
coverage report

# Linting
pylint consumo_lib/ aoi_lib/
flake8 consumo_lib/ aoi_lib/

# Format code
black consumo_lib/ aoi_lib/
```

### Git

```bash
# Status
git status
git log --oneline -10

# Create branch
git checkout -b feature/xyz

# Commit
git add .
git commit -m "type(scope): subject"

# Tag
git tag -a tag_name -m "Description"
git push origin tag_name
```

---

## Best Practices

### DO ✅

- Escrever testes ANTES da implementação (TDD)
- Aplicar SOLID principles consistentemente
- Manter backward compatibility (ZERO breaking changes sem migração)
- Commit frequentemente com mensagens descritivas
- Documentar decisões arquiteturais em docstrings
- Usar type hints em APIs públicas
- Seguir Google Python Style Guide

### DON'T ❌

- Não adicionar funcionalidades extras (YAGNI)
- Não criar breaking changes sem migração documentada
- Não commit código com testes falhando
- Não ignorar linter warnings
- Não duplicar código (DRY principle)
- Não commit com mensagem genérica ("update files")

---

## Definition of Done

Uma task/fase/track é **DONE** quando:

1. ✅ Código implementado
2. ✅ Testes criados e passando (100%)
3. ✅ Cobertura >80%
4. ✅ Linter clean
5. ✅ Docstrings completas
6. ✅ CLAUDE.md atualizado
7. ✅ Backward compatibility mantida
8. ✅ Code review aprovado
9. ✅ Commit criado
10. ✅ plan.md atualizado

---

## Success Metrics

### Phase 3 Achievements (2026-01-15)

- ✅ Widget reduzido: 1,179 → 1,019 linhas (-13.6%)
- ✅ Complexidade reduzida: 5 → 1 responsabilidades (-80%)
- ✅ Testabilidade aumentada: 10% → 90% (+800%)
- ✅ Services criados: 3 (1,226 linhas totais)
- ✅ Testes: 34 → 102 (+200%)
- ✅ 100% pass rate (102/102 testes passing)
- ✅ SOLID principles aplicados (todos 5)
- ✅ Zero breaking changes

### Overall Project Metrics

- **Total Python Files:** 245
- **Total Lines of Code:** ~59,516
- **aoi_lib (Core):** 59 files, ~21,627 lines
- **consumo_lib (GUI):** 125 files, ~37,889 lines
- **Test Files:** 48 test files
- **Test Coverage:** >80% (business logic >90%)

---

## References

### Internal Documentation

- **SOLID Analysis:** `docs/reports/SOLID_ANALYSIS_REPORT_2026-01-14.md`
- **Phase 3 Summary:** `conductor/archive/solid_refactoring_phase2_20260114/phase3_executive_summary.md`
- **Migration Guides:** `docs/guides/SOLID_PHASE1_MIGRATION_GUIDE.md`
- **Testing:** `docs/guides/testing_guide.md`

### External Resources

- **Google Python Style Guide:** https://google.github.io/styleguide/pyguide.html
- **PyTest Documentation:** https://docs.pytest.org/
- **SOLID Principles:** https://en.wikipedia.org/wiki/SOLID
- **TDD:** https://en.wikipedia.org/wiki/Test-driven_development

---

## Support and Maintenance

### Maintainers

- **Development Team:** RONALDBUZAGLO <senseironald@gmail.com>
- **AI Assistant:** Claude Code (Sonnet 4.5)

### Getting Help

1. Read `workflow.md` for development protocols
2. Read `CLAUDE.md` for project context
3. Check `tracks.md` for current status
4. Review completed tracks in `archive/` for examples

---

*Last Updated: 2026-01-15*
*Version: 1.0*
*Conductor System for Tensiometro Project*
