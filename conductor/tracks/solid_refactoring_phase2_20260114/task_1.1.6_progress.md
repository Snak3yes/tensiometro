# Progresso: Task 1.1.6 - Refatorar mainwindow.py

## Status: INCOMPLETO (50% completo)

**Data:** 2026-01-14
**Commit:** `2e7caae`

## Resumo do Progresso

### ✅ Completado

1. **Testes de Integração Criados** (Task 1.1.7 parcial)
   - Arquivo: `tests/integration/gerber_core/test_mainwindow_refactoring.py`
   - 10/13 testes passando (3 skipped - MainWindow não refatorado ainda)
   - Testam integração Model-Controller-Commands
   - Garantem backward compatibility

2. **Command Pattern para Parser GerberObject** (Sub-tarefa de 1.1.6)
   - Arquivo: `aoi_lib/gerber_core/commands/parser_edit_commands.py`
   - 5 classes de comando implementadas
   - Factory Function para seleção de comando
   - 17 testes unitários (100% passing)
   - 96% de cobertura

3. **Análise e Estratégia Documentada**
   - Arquivo: `conductor/.../mainwindow_refactoring_analysis.md`
   - Análise completa de estruturas de dados
   - Estratégia de refatoração conservadora definida
   - Plano de implementação detalhado

### ⏳ Pendente

1. **Refatoração de mainwindow.py** (Task 1.1.6 - CORE)
   - [ ] Modificar `on_edit_object()` para usar Command Pattern
   - [ ] Modificar `on_edit_many_objects()` para usar Command Pattern
   - [ ] Adicionar Factory Function em MainWindow
   - [ ] Testar refatoração completa
   - [ ] Reduzir complexidade ciclomática (27→<5, 46→<5)
   - [ ] Reduzir tamanho do arquivo (1384→~1100 linhas)

2. **Atualização de Documentação** (Task 1.1.8)
   - [ ] Atualizar CLAUDE.md com nova estrutura
   - [ ] Documentar migração de Parser Commands
   - [ ] Criar guia de uso para novos comandos

3. **Verificação Final** (Task 1.1.9)
   - [ ] Smoke test completo com GUI
   - [ ] Validação manual com usuário
   - [ ] Code review

## Blocos de Construção Criados

```
┌─────────────────────────────────────────────┐
│          CAMADA DE COMANDOS                 │
├─────────────────────────────────────────────┤
│ models.GerberObject (dataclass)             │
│   ├─ EditCircleCommand                     │
│   ├─ EditRectangleCommand                  │
│   ├─ EditObroundCommand                    │
│   └─ EditRegionCommand                     │
├─────────────────────────────────────────────┤
│ parser.GerberObject (kind, params, polygon)│
│   ├─ ParserEditCircleCommand               │
│   ├─ ParserEditRectangleCommand            │
│   ├─ ParserEditObroundCommand              │
│   └─ ParserEditRegionCommand               │
│      └─ create_parser_edit_command()       │
└─────────────────────────────────────────────┘
```

## Próximos Passos (Ordem de Implementação)

### Passo 1: Adicionar import em MainWindow

```python
# mainwindow.py
from ..commands.parser_edit_commands import create_parser_edit_command
```

### Passo 2: Refatorar `on_edit_object()`

**Antes** (complexidade 27):
```python
def on_edit_object(self, index: int):
    obj = self._full_layer_objects[index]

    if obj.kind == "flash_circle":
        # 20 linhas de código...
    elif obj.kind == "flash_rect":
        # 30 linhas de código...
    elif obj.kind == "flash_oval":
        # 30 linhas de código...
    # ... cadeia if/elif
```

**Depois** (complexidade <5):
```python
def on_edit_object(self, index: int):
    """Edita objeto usando Command Pattern."""
    obj = self._full_layer_objects[index]

    # Factory para criar comando apropriado
    command = create_parser_edit_command(obj)
    if command is None:
        QMessageBox.information(self, "Não editável",
                                "Este tipo não pode ser editado.")
        return

    # Executar diálogo específico (circle = QInputDialog, etc.)
    if obj.kind == "flash_circle":
        new_dia, ok = QInputDialog.getDouble(...)
        if not ok:
            return
        modified = command.execute(new_dia_mm=new_dia)
    elif obj.kind in ("flash_rect", "flash_oval"):
        dlg = WidthHeightDialog(...)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        new_w, new_h = dlg.values()
        modified = command.execute(new_width_mm=new_w, new_height_mm=new_h)

    # Atualizar objeto
    self._full_layer_objects[index] = modified
    self._refresh_view()
```

### Passo 3: Refatorar `on_edit_many_objects()`

**Antes** (complexidade 46):
```python
def on_edit_many_objects(self, indices: list[int]):
    # Validações...

    kind = next(iter(kinds))

    if kind == "flash_rect":
        # 40 linhas de código...
    elif kind == "flash_oval":
        # 40 linhas de código...
    elif kind == "region":
        # 60 linhas de código...
```

**Depois** (complexidade <5):
```python
def on_edit_many_objects(self, indices: list[int]):
    """Edita múltiplos objetos usando Command Pattern."""
    # Validações (mesma lógica)...

    # Criar comando para primeiro objeto (todos são do mesmo tipo)
    first_obj = objs[0]
    command = create_parser_edit_command(first_obj)

    # Executar diálogo de edição em grupo
    dlg = WidthHeightDialog(...)
    if dlg.exec() != QDialog.DialogCode.Accepted:
        return

    new_w, new_h = dlg.values()

    # Aplicar a todos objetos
    for obj in objs:
        cmd = create_parser_edit_command(obj)
        modified = cmd.execute(new_width_mm=new_w, new_height_mm=new_h)
        # Atualizar na lista...
```

## Métricas Esperadas (completude)

### Antes (atual)
- `on_edit_object()`: 190 linhas, complexidade 27
- `on_edit_many_objects()`: 280+ linhas, complexidade 46
- Total mainwindow.py: 1,384 linhas

### Depois (estimado)
- `on_edit_object()`: ~50 linhas, complexidade <5
- `on_edit_many_objects()`: ~60 linhas, complexidade <5
- Total mainwindow.py: ~1,100 linhas (-284 linhas, -20%)

## Decisão Arquitetural

**Por que refatoração conservadora?**

1. **Zero breaking changes**: Código existente continua funcionando
2. **Baixo risco**: Mudanças isoladas em métodos específicos
3. **Fácil reversão**: Pode reverter se necessário
4. **Preparação para futuro**: Padrão Command facilita migração completa futura

**Por que não migrar para GerberModel agora?**

1. **Estruturas incompatíveis**: parser.GerberObject ≠ models.GerberObject
2. **Alto acoplamento**: MainWindow depende de parser.GerberObject
3. **Muitas dependências**: parser, render, geometry todos usam parser.GerberObject
4. **Risco alto**: Requer reescrever metade do código gerber_core

**Quando migrar para GerberModel?**

- **Fase 2** (Task 1.2): Refatorar parser.py com Strategy Pattern
- **Fase 3** (Future): Criar adapters entre parser e model
- **Fase 4** (Future): Migrar MainWindow completamente

## Conclusão

Blocos de construção criados com sucesso. Restando apenas implementar
a refatoração de mainwindow.py usando os comandos criados.

**Próxima ação**: Implementar Passo 2 (refatorar on_edit_object)

**Estimativa**: 2-3 horas para completar refatoração de mainwindow.py

**Risco**: Baixo (testes de integração já criados, estratégia clara)
