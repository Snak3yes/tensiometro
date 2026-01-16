# Especificação da Track: Recipe Dialogs Refactoring

## Visão Geral

**Track ID:** recipe_dialogs_refactoring_20260116
**Nome:** Recipe Dialogs Refactoring - Single Responsibility Principle
**Tipo:** Refactor
**Prioridade:** MEDIUM
**Data de Criação:** 2026-01-16
**Estimativa:** 1-2 dias

---

## Objetivo

Refatorar `consumo_lib/dialogs/recipe_dialogs.py` (881 linhas) aplicando **Single Responsibility Principle (SRP)** para separar em 3 arquivos focados, mantendo 100% backward compatibility.

**Motivação:**
- Arquivo monolítico com 3 classes misturadas (viola SRP)
- Dificuldade de manutenção e teste
- Arquivo muito grande (881 linhas)
- Baixa coesão entre as classes

---

## Critérios de Aceite

### Funcional
- [ ] RecipeListWidget separado em arquivo próprio
- [ ] RecipeEditorDialog separado em arquivo próprio
- [ ] RecipeManagerDialog separado em arquivo próprio
- [ ] Todos os 3 diálogos funcionando corretamente
- [ ] Backward compatibility mantida (imports funcionam)

### Não-Funcional
- [ ] Zero breaking changes
- [ ] Testes unitários criados
- [ ] Documentação atualizada
- [ ] Linting sem erros

---

## Arquitetura Atual

### Arquivo: `consumo_lib/dialogs/recipe_dialogs.py`

```
recipe_dialogs.py (881 linhas)
├── RecipeListWidget (70 linhas)
│   ├── setup_ui()
│   ├── refresh_list()
│   ├── _on_selection_changed()
│   ├── _on_double_click()
│   └── get_selected_recipe_id()
│
├── RecipeEditorDialog (474 linhas)
│   ├── setup_ui()
│   ├── _create_info_tab()
│   ├── _create_stencil_tab()
│   ├── _create_tension_tab()
│   ├── _create_capture_tab()
│   ├── _create_inspection_tab()
│   ├── load_recipe_data()
│   ├── save_recipe_data()
│   └── accept()
│
└── RecipeManagerDialog (272 linhas)
    ├── setup_ui()
    ├── _on_recipe_selected()
    ├── _on_new_recipe()
    ├── _on_edit_recipe()
    ├── _on_delete_recipe()
    ├── _on_duplicate_recipe()
    └── _on_load_recipe()
```

### Problemas Identificados

1. **Violação de SRP:** 3 responsabilidades diferentes em 1 arquivo
2. **Arquivo muito grande:** 881 linhas (difícil navegação)
3. **Baixa testabilidade:** Difícil testar classes individualmente
4. **Baixa manutenibilidade:** Mudanças em um diálogo afetam arquivo inteiro

---

## Arquitetura Proposta

### Nova Estrutura

```
consumo_lib/dialogs/recipe/
├── __init__.py                     # Exporta todas as classes (backward compat)
├── recipe_list_widget.py           # RecipeListWidget (~100 linhas)
├── recipe_edit_dialog.py           # RecipeEditorDialog (~500 linhas)
└── recipe_manager_dialog.py        # RecipeManagerDialog (~300 linhas)
```

### Responsabilidades

#### 1. RecipeListWidget
**Responsabilidade:** Listar e selecionar receitas
- Exibir tabela de receitas
- Emitir sinais de seleção
- Permitir duplo clique para edição rápida

#### 2. RecipeEditorDialog
**Responsabilidade:** Editar uma receita
- Formulário com 5 tabs (Info, Stencil, Tensão, Captura, Inspeção)
- Validação de dados
- Salvar/carregar dados da receita

#### 3. RecipeManagerDialog
**Responsabilidade:** Gerenciar receitas
- Listar receitas (usa RecipeListWidget)
- Criar/editar/excluir/duplicar receitas
- Preview de receita selecionada
- Carregar receita para uso

---

## Implementação

### Fase 1: Análise do Arquivo Atual
**Objetivo:** Entender completamente a estrutura atual

**Tarefas:**
1. Mapear todas as dependências entre as 3 classes
2. Identificar imports necessários para cada arquivo
3. Documentar signals usados por cada classe

**Saída:**
- Documento de análise com dependências mapeadas

### Fase 2: Separar RecipeListWidget
**Objetivo:** Extrair RecipeListWidget para arquivo próprio

**Tarefas:**
1. Criar `consumo_lib/dialogs/recipe/recipe_list_widget.py`
2. Mover RecipeListWidget (linhas 37-107)
3. Adicionar imports necessários
4. Testar import isolado

**Saída:**
- `recipe_list_widget.py` criado e testado

### Fase 3: Separar RecipeEditorDialog
**Objetivo:** Extrair RecipeEditorDialog para arquivo próprio

**Tarefas:**
1. Criar `consumo_lib/dialogs/recipe/recipe_edit_dialog.py`
2. Mover RecipeEditorDialog (linhas 109-583)
3. Adicionar imports necessários
4. Testar import isolado

**Saída:**
- `recipe_edit_dialog.py` criado e testado

### Fase 4: Separar RecipeManagerDialog
**Objetivo:** Extrair RecipeManagerDialog para arquivo próprio

**Tarefas:**
1. Criar `consumo_lib/dialogs/recipe/recipe_manager_dialog.py`
2. Mover RecipeManagerDialog (linhas 585-857)
3. Adicionar imports de RecipeListWidget e RecipeEditorDialog
4. Testar import isolado

**Saída:**
- `recipe_manager_dialog.py` criado e testado

### Fase 5: Testes e Documentação
**Objetivo:** Garantir qualidade e backward compatibility

**Tarefas:**
1. Criar `__init__.py` com exportações (backward compat)
2. Criar testes unitários para cada classe
3. Atualizar CLAUDE.md com nova estrutura
4. Criar CHANGELOG
5. Executar smoke test completo

**Saída:**
- Testes criados e passando
- Documentação atualizada
- Backward compatibility verificada

---

## Backward Compatibility

### Estratégia: Facade Pattern via __init__.py

**Arquivo:** `consumo_lib/dialogs/recipe/__init__.py`

```python
"""
Recipe Dialogs - Diálogos para gerenciamento de receitas

Backward compatibility: Importar de consumo_lib.dialogs.recipe_dialogs
ainda funciona via este __init__.py.
"""

from consumo_lib.dialogs.recipe.recipe_list_widget import RecipeListWidget
from consumo_lib.dialogs.recipe.recipe_edit_dialog import RecipeEditorDialog
from consumo_lib.dialogs.recipe.recipe_manager_dialog import RecipeManagerDialog

__all__ = [
    'RecipeListWidget',
    'RecipeEditorDialog',
    'RecipeManagerDialog',
]
```

**Resultado:**
```python
# ANTIGO (ainda funciona)
from consumo_lib.dialogs.recipe_dialogs import RecipeManagerDialog

# NOVO (agora também funciona)
from consumo_lib.dialogs.recipe import RecipeManagerDialog
from consumo_lib.dialogs.recipe.recipe_manager_dialog import RecipeManagerDialog
```

---

## Riscos e Mitigações

### Risco 1: Quebra de Backward Compatibility
**Nível:** LOW
**Descrição:** Imports existentes podem parar de funcionar
**Mitigação:**
- Manter `recipe_dialogs.py` como facade que importa do novo local
- Documentar novos imports no CLAUDE.md
- Testar todos os imports existentes

### Risco 2: Referências Circulares
**Nível:** LOW
**Descrição:** RecipeManagerDialog depende de RecipeEditorDialog
**Mitigação:**
- Imports locais dentro de métodos quando necessário
- Usar type hints com TYPE_CHECKING

---

## Métricas de Sucesso

### Quantitativas (Antes → Depois)
- **Arquivo principal:** 881 linhas → ~300 linhas (cada)
- **Arquivos:** 1 → 3 (separação por responsabilidade)
- **Classes por arquivo:** 3 → 1 (SRP)

### Qualitativas
- ✅ Alta coesão dentro de cada arquivo
- ✅ Fácil navegação e manutenção
- ✅ Testabilidade melhorada
- ✅ Backward compatibility mantida

---

## Dependencies

### Internas
- `aoi_lib/recipe_manager.py` - Recipe, RecipeManager, etc.
- `PyQt6` - Qt widgets

### Externas
- Nenhuma

---

## Definição de Done

A track está completa quando:
- [ ] 3 arquivos separados criados
- [ ] __init__.py com exportações (backward compat)
- [ ] Testes unitários criados e passando
- [ ] Smoke test executado e passando
- [ ] Documentação atualizada (CLAUDE.md, CHANGELOG)
- [ ] Linting sem erros
- [ ] Backward compatibility verificada
- [ ] Checkpoint commit criado
- [ ] Metadata atualizado com status "complete"

---

*Generated by Conductor. Created: 2026-01-16*
*Track ID: recipe_dialogs_refactoring_20260116*
