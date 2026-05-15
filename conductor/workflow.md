# Development Workflow (Tensiometro)

**Project:** Tensiometro - Sistema AOI para Controle de Qualidade de Stencils
**Last Updated:** 2026-01-15
**Version:** 1.0

---

## Overview

Este documento define o protocolo de desenvolvimento para o projeto Tensiometro, seguindo princípios SOLID, TDD (Test-Driven Development), e desenvolvimento incremental com checkpoints.

## Philosophy

- **Documentation as Source of Truth**: Todo contexto em arquivos markdown
- **Test-Driven Development**: Escrever testes antes da implementação
- **SOLID Principles**: Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion
- **Incremental Progress**: Uma tarefa por vez, verificar frequentemente
- **Human-in-the-Loop**: Claude propõe, humano aprova
- **Checkpoint-Based**: Commits marcam fronteiras de fase

---

## Task Workflow (11 Passos)

### 1. Task Selection
```
1. Ler plan.md do track atual
2. Identificar próxima tarefa pendente
3. Verificar dependências (tasks anteriores devem estar completas)
4. Confirmar entendimento dos objetivos
```

### 2. Test Analysis
```
1. Identificar testes existentes relacionados à tarefa
2. Ler testes para entender comportamento esperado
3. Verificar se há gaps de cobertura
4. Documentar testes que precisam ser criados/atualizados
```

### 3. Implementation Planning
```
1. Listar arquivos que serão modificados/criados
2. Definir estrutura de classes/funções
3. Aplicar princípios SOLID (SRP, OCP, DIP, ISP, LSP)
4. Verificar compatibilidade com código existente (backward compatibility)
```

### 4. Test-First (TDD Red)
```
1. Escrever testes ANTES da implementação
2. Testes devem falhar inicialmente (RED)
3. Usar padrões: pytest, fixtures, mocks
4. Testar casos normais, edge cases e erros
```

### 5. Implementation (TDD Green)
```
1. Implementar código MÍNIMO para passar nos testes
2. Rodar testes frequentemente
3. Não adicionar funcionalidades extras (YAGNI)
4. Aplicar code styleguides (Python: Google Python Style Guide)
```

### 6. Refactoring (TDD Refactor)
```
1. Melhorar código mantendo testes verdes
2. Extrair métodos, renomear variáveis, aplicar padrões
3. Verificar SOLID principles
4. Remover código duplicado
5. Manter backward compatibility
```

### 7. Documentation
```
1. Adicionar docstrings (Google style)
2. Atualizar CLAUDE.md se necessário
3. Atualizar README.md se adicionou novo módulo
4. Documentar breaking changes (se inevitáveis)
```

### 8. Verification
```
1. Rodar suite completa de testes (pytest)
2. Verificar覆盖率 (coverage.py >80%)
3. Rodar linter (pylint, flake8)
4. Testar manualmente se aplicável
```

### 9. Mark Task Complete
```
1. Atualizar plan.md marcando tarefa como [x]
2. Registrar observações/decisões tomadas
3. Atualizar metadata.json (timestamp)
4. Commit com mensagem descritiva
```

### 10. Review
```
1. Revisar mudanças com foco em:
   - SOLID principles
   - Backward compatibility
   - Test coverage
   - Code style
2. Verificar se objetivos da tarefa foram atingidos
3. Confirmar que não há regressões
```

### 11. Next Task
```
1. Retornar ao passo 1 para próxima tarefa
2. OU marcar fase completa se todas tasks completas
```

---

## Phase Completion Protocol

### Quality Gates

Uma fase só é considerada completa quando:

1. **✅ Todas as Tasks Completas**
   - Todas as tasks da fase marcadas como [x] no plan.md
   - Nenhuma task pendente ou bloqueada

2. **✅ Testes Passando (100%)**
   ```bash
   pytest tests/ -v
   # Expected: 100% pass rate
   ```

3. **✅ Cobertura Adequada (>80%)**
   ```bash
   coverage run -m pytest tests/
   coverage report
   # Expected: >80% coverage
   ```

4. **✅ Linter Clean**
   ```bash
   pylint consumo_lib/ aoi_lib/
   # Expected: No errors, warnings minimizadas
   ```

5. **✅ Documentação Atualizada**
   - CLAUDE.md atualizado se mudou arquitetura
   - Docstrings em todos os métodos públicos
   - README.md atualizado se adicionou novos módulos

6. **✅ Backward Compatibility**
   - Zero breaking changes sem migração documentada
   - Interface pública mantida
   - Testes existentes ainda passando

### Phase Checkpoint Tasks

Ao completar uma fase:

1. **Atualizar plan.md**
   ```markdown
   ## Phase X: [Nome da Fase]
   Status: ✅ COMPLETE (2026-01-15)
   - [x] Task X.1: ...
   - [x] Task X.2: ...
   ```

2. **Criar Checkpoint Commit**
   ```bash
   git add .
   git commit -m "Feat: conclui [Nome da Fase]

   - Achievement 1
   - Achievement 2
   - SOLID principles applied
   - Test coverage: N%
   - Zero breaking changes"
   ```

3. **Criar Git Tag (opcional)**
   ```bash
   git tag -a phaseX_complete -m "Phase X: [Description]"
   ```

4. **Atualizar tracks.md**
   - Marcar fase como complete
   - Registrar achievements e métricas

5. **Resumo Executivo (opcional)**
   - Criar resumo da fase no diretório do track
   - Documentar lições aprendidas
   - Métricas de sucesso

---

## Track Completion Protocol

### Completion Criteria

Um track só é considerado completo quando:

1. **✅ Todas as Fases Completas**
   - Todas as fases marcadas como ✅ COMPLETE
   - Todos os quality gates atendidos

2. **✅ Acceptance Criteria Atendidos**
   - Todos os critérios do spec.md atendidos
   - Funcionalidade testada e validada

3. **✅ Documentação Completa**
   - spec.md preenchido
   - plan.md com todas as tasks marcadas [x]
   - metadata.json atualizado
   - Resumo executivo criado

4. **✅ Artefatos Criados**
   - Código implementado
   - Testes criados (100% pass rate)
   - Documentação atualizada
   - Commits e tags criados

### Track Archive

Ao completar um track:

1. **Mover para archive/**
   ```bash
   mv conductor/tracks/{track_id} conductor/archive/{track_id}
   ```

2. **Atualizar tracks.md**
   - Mover track de "Active Tracks" para "Completed Tracks"
   - Registrar data de conclusão

3. **Criar Release Notes (opcional)**
   - Documentar funcionalidades implementadas
   - Breaking changes (se houver)
   - Migrações necessárias

---

## Quality Gates

### Test Coverage
- **Mínimo:** 80% de cobertura
- **Ideal:** >90% para business logic
- **Exceção:** Código de UI (PyQt6) pode ter menor cobertura

### Linting
- **pylint:** Score >8.0
- **flake8:** Zero erros, warnings minimizadas
- **mypy:** Type hints for public APIs

### Documentation
- Todo módulo público tem docstring
- Classes e funções públicas têm Args/Returns/Raises
- CLAUDE.md atualizado com arquitetura

### Code Review
- SOLID principles aplicados
- Backward compatibility mantida
- Test coverage adequado
- Code style consistente

---

## Test Requirements

### Unit Tests
- Testar lógica de negócio sem dependências externas
- Usar mocks para hardware, database, network
- Testar casos normais, edge cases, erros

### Integration Tests
- Testar integração entre componentes
- Usar fixtures para configurar ambiente
- Testar fluxos completos

### UI Tests (PyQt6)
- Testar lógica de UI sem renderizar widgets
- Usar QTest para simular interação do usuário
- Testar signals/slots

### Test Organization
```
tests/
├── unit/                   # Fast tests, no external deps
│   ├── test_services/      # Business logic tests
│   ├── test_models/        # Model tests
│   └── test_widgets/       # Widget logic tests
├── integration/            # Integration tests
│   ├── test_hardware/      # Hardware integration
│   └── test_workflows/     # Workflow tests
└── fixtures/               # Test data and mocks
```

---

## Code Review Process

### Review Checklist

- [ ] **SOLID Principles**
  - [ ] Single Responsibility (SRP)
  - [ ] Open/Closed (OCP)
  - [ ] Liskov Substitution (LSP)
  - [ ] Interface Segregation (ISP)
  - [ ] Dependency Inversion (DIP)

- [ ] **Code Quality**
  - [ ] Test coverage >80%
  - [ ] No linter errors
  - [ ] Docstrings completas
  - [ ] Type hints em APIs públicas

- [ ] **Compatibility**
  - [ ] Zero breaking changes sem migração
  - [ ] Interface pública mantida
  - [ ] Testes existentes passando

- [ ] **Documentation**
  - [ ] CLAUDE.md atualizado
  - [ ] README.md atualizado se necessário
  - [ ] Migrations documentadas se houver breaking changes

### Review Approval

- **Auto-Approve:** Mudanças triviais (docs, testes, refactors seguros)
- **Manual Review:** Mudanças na arquitetura, APIs públicas, ou com breaking changes
- **Reject:** Linter errors, testes falhando, violação de SOLID principles

---

## Commit Guidelines

### Commit Message Format

```
<Tipo>: <assunto descritivo>

<corpo opcional>

<rodapé opcional>
```

### Rule
- Sempre iniciar a primeira linha com um prefixo como `Feat:`, `Fix:`, `Refactor:`, `Docs:`, `Test:`, `Style:` ou `Chore:`
- Após o prefixo, descrever a mudança de forma objetiva em linguagem natural
- Não usar o formato `type(scope):`
- O corpo é opcional e pode listar contexto, impacto, compatibilidade e referências

### Example

```bash
git commit -m "Feat: adiciona serviço de alinhamento por fiducial

- Created FiducialAlignmentService for business logic
- Created TemplateMatchingService for OpenCV operations
- Created AlignmentState model for state management
- Refactored AlignmentWidget to use services (SRP)
- Added 64 unit tests (100% coverage for services)

SOLID principles applied:
- SRP: Widget now only handles UI
- DIP: Service injection via constructor
- OCP: Extensible via strategy pattern

Breaking changes: None
Backward compatibility: Maintained"

Refs: #123
Co-Authored-By: Claude Sonnet <noreply@anthropic.com>
```

---

## Definition of Done

Uma task/fase/track é considerada **DONE** quando:

1. ✅ Código implementado
2. ✅ Testes criados e passando (100%)
3. ✅ Cobertura >80%
4. ✅ Linter clean
5. ✅ Docstrings completas
6. ✅ CLAUDE.md atualizado
7. ✅ Backward compatibility mantida
8. ✅ Code review aprovado
9. ✅ Commit criado com mensagem descritiva
10. ✅ plan.md atualizado

---

## Best Practices

### DO ✅
- Escrever testes antes da implementação (TDD)
- Aplicar SOLID principles consistentemente
- Manter backward compatibility
- Commit frequentemente com mensagens descritivas
- Documentar decisões arquiteturais
- Usar type hints em APIs públicas

### DON'T ❌
- Não adicionar funcionalidades extras (YAGNI)
- Não criar breaking changes sem migração documentada
- Não commit código com testes falhando
- Não ignorar linter warnings
- Não duplicar código (DRY)
- Não commit com mensagem genérica ("update files")

---

## Tools and Commands

### Development
```bash
# Run tests
pytest tests/ -v

# Coverage
coverage run -m pytest tests/
coverage report
coverage html  # Generate HTML report

# Linting
pylint consumo_lib/ aoi_lib/
flake8 consumo_lib/ aoi_lib/
mypy consumo_lib/ aoi_lib/

# Format code (black)
black consumption_lib/ aoi_lib/

# Type check
mypy --strict consumo_lib/ aoi_lib/
```

### Git
```bash
# Status
git status
git log --oneline -10

# Branches
git branch -a
git checkout -b feature/xyz

# Commits
git add .
git commit -m "Feat: descreve a mudança realizada"
git push origin main

# Tags
git tag -a tag_name -m "Description"
git push origin tag_name
```

---

## Emergency Procedures

### Revert Task
```bash
git revert HEAD
git push origin main
```

### Rollback Phase
```bash
git reset --hard <phase_checkpoint_tag>
git push --force origin main
```

### Fix Broken Build
1. Identificar causa (testes, linter, build)
2. Criar branch hotfix
3. Implementar fix
4. Testar completamente
5. Merge e commit
6. Atualizar plan.md

---

## References

- **SOLID Principles:** `docs/reports/SOLID_ANALYSIS_REPORT_2026-01-14.md`
- **Code Style:** `conductor/code_styleguides/python.md`
- **Product Guidelines:** `conductor/product-guidelines.md`
- **Tech Stack:** `conductor/tech-stack.md`
- **Project Documentation:** `CLAUDE.md`
- **README:** `README.md`

---

*Last Updated: 2026-01-15*
*Version: 1.0*
*Maintained by: Development Team*
