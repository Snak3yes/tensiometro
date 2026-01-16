# Plano da Track: Recipe Dialogs Refactoring

## Visão Geral

Refatorar `consumo_lib/dialogs/recipe_dialogs.py` (881 linhas) aplicando **Single Responsibility Principle (SRP)** para separar em 3 arquivos focados.

**Track ID:** recipe_dialogs_refactoring_20260116
**Type:** Refactor
**Created:** 2026-01-16
**Est. Duration:** 1-2 dias
**Priority:** Medium

---

## Fases

### Fase 1: Análise do Arquivo Atual ⏳ IN PROGRESS

**Objetivo:** Entender completamente a estrutura atual e dependências

#### Tarefas

##### 1.1. Análise estrutural
- [x] 1.1.1. Ler arquivo completo (881 linhas) ✅
- [x] 1.1.2. Identificar as 3 classes principais ✅
  - RecipeListWidget (70 linhas, linhas 37-107)
  - RecipeEditorDialog (474 linhas, linhas 109-583)
  - RecipeManagerDialog (272 linhas, linhas 585-857)
- [x] 1.1.3. Mapear dependências entre classes ✅
  - RecipeManagerDialog → RecipeListWidget (composição)
  - RecipeManagerDialog → RecipeEditorDialog (cria instâncias)
  - RecipeEditorDialog → independente (sem dependências)
- [x] 1.1.4. Identificar imports necessários ✅
  - PyQt6: QtWidgets, QtCore, QtGui
  - aoi_lib: Recipe, RecipeManager, StencilInfo, etc.
  - logging: logger

##### 1.2. Documentar dependências
- [x] 1.2.1. Criar documento de análise ✅
- [x] 1.2.2. Mapear signals emitidos ✅
  - RecipeListWidget: recipe_selected, recipe_double_clicked
  - RecipeManagerDialog: recipe_loaded
- [x] 1.2.3. Identificar métodos de cada classe ✅
  - RecipeListWidget: 6 métodos públicos
  - RecipeEditorDialog: 10 métodos públicos
  - RecipeManagerDialog: 8 métodos públicos

#### Checkpoint Fase 1
- [x] Análise estrutural completa ✅
- [x] Documento de dependências criado ✅
- [x] Especificação da track criada (spec.md) ✅
- [x] Metadata criado ✅
- **Status:** ✅ COMPLETE (pronto para implementação)

---

### Fase 2: Separar RecipeListWidget ⏳ PENDING

**Objetivo:** Extrair RecipeListWidget para arquivo próprio

#### Tarefas

##### 2.1. Criar estrutura de diretórios
- [ ] 2.1.1. Criar diretório `consumo_lib/dialogs/recipe/`
- [ ] 2.1.2. Criar `recipe_list_widget.py`

##### 2.2. Extrair RecipeListWidget
- [ ] 2.2.1. Copiar linhas 37-107 para `recipe_list_widget.py`
- [ ] 2.2.2. Adicionar imports necessários (PyQt6, logging, aoi_lib)
- [ ] 2.2.3. Adicionar docstring da classe
- [ ] 2.2.4. Verificar sintaxe (python -m py_compile)

##### 2.3. Testar import isolado
- [ ] 2.3.1. Testar `from consumo_lib.dialogs.recipe.recipe_list_widget import RecipeListWidget`
- [ ] 2.3.2. Verificar se classe pode ser instanciada
- [ ] 2.3.3. Verificar métodos públicos

#### Checkpoint Fase 2
- [ ] Diretório recipe/ criado
- [ ] recipe_list_widget.py criado e sintaxe OK
- [ ] Import isolado funcionando
- [ ] Commit: `git commit -m "feat(phase7-2): Extract RecipeListWidget to separate file"`

---

### Fase 3: Separar RecipeEditorDialog ⏳ PENDING

**Objetivo:** Extrair RecipeEditorDialog para arquivo próprio

#### Tarefas

##### 3.1. Criar arquivo
- [ ] 3.1.1. Criar `recipe_edit_dialog.py`

##### 3.2. Extrair RecipeEditorDialog
- [ ] 3.2.1. Copiar linhas 109-583 para `recipe_edit_dialog.py`
- [ ] 3.2.2. Adicionar imports necessários
  - PyQt6 (todos os widgets usados)
  - aoi_lib.recipe_manager (todos os models)
  - logging
- [ ] 3.2.3. Adicionar docstring da classe
- [ ] 3.2.4. Verificar sintaxe (python -m py_compile)

##### 3.3. Testar import isolado
- [ ] 3.3.1. Testar `from consumo_lib.dialogs.recipe.recipe_edit_dialog import RecipeEditorDialog`
- [ ] 3.3.2. Verificar se diálogo pode ser aberto
- [ ] 3.3.3. Verificar se 5 tabs são criadas corretamente

#### Checkpoint Fase 3
- [ ] recipe_edit_dialog.py criado e sintaxe OK
- [ ] Import isolado funcionando
- [ ] UI renderizando corretamente
- [ ] Commit: `git commit -m "feat(phase7-3): Extract RecipeEditorDialog to separate file"`

---

### Fase 4: Separar RecipeManagerDialog ⏳ PENDING

**Objetivo:** Extrair RecipeManagerDialog para arquivo próprio

#### Tarefas

##### 4.1. Criar arquivo
- [ ] 4.1.1. Criar `recipe_manager_dialog.py`

##### 4.2. Extrair RecipeManagerDialog
- [ ] 4.2.1. Copiar linhas 585-857 para `recipe_manager_dialog.py`
- [ ] 4.2.2. Adicionar imports necessários
  - PyQt6
  - aoi_lib.recipe_manager
  - **NOVO:** `from consumo_lib.dialogs.recipe.recipe_list_widget import RecipeListWidget`
  - **NOVO:** `from consumo_lib.dialogs.recipe.recipe_edit_dialog import RecipeEditorDialog`
  - logging
- [ ] 4.2.3. Adicionar docstring da classe
- [ ] 4.2.4. Verificar sintaxe (python -m py_compile)

##### 4.3. Testar import isolado
- [ ] 4.3.1. Testar `from consumo_lib.dialogs.recipe.recipe_manager_dialog import RecipeManagerDialog`
- [ ] 4.3.2. Verificar se diálogo pode ser aberto
- [ ] 4.3.3. Verificar se RecipeListWidget é renderizado dentro do diálogo
- [ ] 4.3.4. Verificar se botão "Nova" abre RecipeEditorDialog

#### Checkpoint Fase 4
- [ ] recipe_manager_dialog.py criado e sintaxe OK
- [ ] Import isolado funcionando
- [ ] Integração RecipeListWidget + RecipeEditorDialog funcionando
- [ ] Commit: `git commit -m "feat(phase7-4): Extract RecipeManagerDialog to separate file"`

---

### Fase 5: Testes e Documentação ⏳ PENDING

**Objetivo:** Garantir qualidade e backward compatibility

#### Tarefas

##### 5.1. Criar __init__.py para backward compatibility
- [ ] 5.1.1. Criar `consumo_lib/dialogs/recipe/__init__.py`
- [ ] 5.1.2. Exportar todas as 3 classes
- [ ] 5.1.3. Manter `recipe_dialogs.py` como facade (opcional)

##### 5.2. Criar testes unitários
- [ ] 5.2.1. Criar `tests/unit/test_recipe_list_widget.py`
  - Testar setup_ui()
  - Testar refresh_list()
  - Testar signals (recipe_selected, recipe_double_clicked)
- [ ] 5.2.2. Criar `tests/unit/test_recipe_edit_dialog.py`
  - Testar criação de nova receita
  - Testar edição de receita existente
  - Testar validação
- [ ] 5.2.3. Criar `tests/unit/test_recipe_manager_dialog.py`
  - Testar listagem de receitas
  - Testar criação/edição/exclusão
  - Testar signal recipe_loaded

##### 5.3. Atualizar documentação
- [ ] 5.3.1. Atualizar CLAUDE.md
  - Adicionar seção "Recipe Dialogs" em consumo_lib/dialogs/
  - Atualizar Module Import Patterns
- [ ] 5.3.2. Criar CHANGELOG
  - Documentar mudança de estrutura
  - Explicar backward compatibility
  - Adicionar exemplos de migração

##### 5.4. Verificação final
- [ ] 5.4.1. Smoke test completo
  - Importar de `consumo_lib.dialogs.recipe` (novo)
  - Importar de `consumo_lib.dialogs.recipe_dialogs` (antigo - se mantido)
  - Testar criação de receita
  - Testar edição de receita
  - Testar exclusão de receita
- [ ] 5.4.2. Validar backward compatibility
  - Verificar se imports antigos ainda funcionam
  - Testar integração com main_window.py
- [ ] 5.4.3. Linting
  - pylint nos 3 arquivos novos
  - flake8 nos 3 arquivos novos

#### Checkpoint Fase 5
- [ ] __init__.py criado com exportações
- [ ] Testes unitários criados e passando
- [ ] CLAUDE.md atualizado
- [ ] CHANGELOG criado
- [ ] Smoke test passando
- [ ] Linting sem erros
- [ ] Commit: `git commit -m "feat(phase7-5): Complete Recipe Dialogs refactoring with tests and docs"`

---

## Definição de Done

### Uma tarefa está completa quando:
- [ ] Código implementado conforme especificação
- [ ] Sintaxe verificada (python -m py_compile)
- [ ] Import isolado testado
- [ ] Commit com mensagem convencional
- [ ] plan.md atualizado com status

### Uma fase está completa quando:
- [ ] Todas as tarefas da fase concluídas
- [ ] Checkpoint commit criado
- [ ] plan.md atualizado com checkpoint SHA

### A track está completa quando:
- [ ] Todas as 5 fases completadas
- [ ] Backward compatibility mantida
- [ ] Testes criados e passando
- [ ] Documentação atualizada
- [ ] Linting sem erros
- [ ] Metadata atualizado com status "complete"
- [ ] Track movida para archive/ (opcional - parte de SOLID Phase 2)

---

## Recursos e Referências

### Documentos do Projeto
- **Spec:** `conductor/tracks/recipe_dialogs_refactoring_20260116/spec.md`
- **Metadata:** `conductor/tracks/recipe_dialogs_refactoring_20260116/metadata.json`
- **Product Context:** `conductor/product.md`
- **Tech Stack:** `conductor/tech-stack.md`
- **Workflow:** `conductor/workflow.md`
- **Code Guidelines:** `conductor/code_styleguides/python.md`

### Documentação Externa
- **CLAUDE.md:** Contexto completo do projeto
- **SOLID Refactoring Phase 2:** `conductor/tracks/solid_refactoring_phase2_20260114/plan.md`

### Referências Técnicas
- [Single Responsibility Principle](https://en.wikipedia.org/wiki/Single-responsibility_principle)
- [Clean Code by Robert C. Martin](https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/dp/0132350882)

---

## Métricas de Sucesso

### Métricas Quantitativas (Antes → Depois)
- **Arquivo principal:** 881 linhas → ~300 linhas (cada)
- **Arquivos:** 1 → 3 (separação por responsabilidade)
- **Classes por arquivo:** 3 → 1 (SRP)
- **Linhas por arquivo:** 881 → 70/474/272 (média ~272)

### Métricas Qualitativas
- ✅ Alta coesão dentro de cada arquivo
- ✅ Fácil navegação e manutenção
- ✅ Testabilidade melhorada
- ✅ Backward compatibility mantida
- ✅ Código limpo e organizado

---

*Generated by Conductor. Created: 2026-01-16*
*Last updated: 2026-01-16*
*Track ID: recipe_dialogs_refactoring_20260116*
