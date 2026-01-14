# Análise: Refatoração de mainwindow.py

## Contexto

**Arquivo**: `aoi_lib/gerber_core/gui/mainwindow.py` (1,384 linhas)
**Objetivo**: Reduzir complexidade ciclomática e violações SOLID
**Métodos críticos**:
- `on_edit_object()` - complexidade 27 (linhas 733-922)
- `on_edit_many_objects()` - complexidade 46 (linhas 924-1200+)

## Problema Identificado: Estruturas de Dados Diferentes

### Estrutura Atual (Parser - GerberObject)

```python
# Usado por mainwindow.py atualmente
class GerberObject:
    kind: str              # "flash_circle", "flash_rect", etc.
    dcode: int             # D-code (aperture number)
    x_mm: float | None
    y_mm: float | None
    params: dict           # {"dia_mm": 5.0, "width_mm": 10.0, etc.}
    polygon_mm: list       # [(x1, y1), (x2, y2), ...]
```

### Nova Estrutura (Model - GerberObject)

```python
# Nova estrutura criada na Task 1.1.3
@dataclass
class GerberObject:
    obj_type: str           # "flash_circle", "flash_rect", etc.
    x: float
    y: float
    diameter: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
```

## Estratégia de Refatoração

### Opção 1: Adapter Pattern (Recomendado para esta fase)

Criar adapters para converter entre as estruturas:

```python
# aoi_lib/gerber_core/adapters/parser_adapter.py
class GerberObjectAdapter:
    """Adapter entre Parser GerberObject e Model GerberObject."""

    @staticmethod
    def parser_to_model(parser_obj) -> GerberModel:
        """Converte parser.GerberObject → models.GerberObject"""
        ...

    @staticmethod
    def model_to_parser(model_obj) -> ParserGerberObject:
        """Converte models.GerberObject → parser.GerberObject"""
        ...
```

**Vantagens**:
- ✅ Zero breaking changes (código existente continua funcionando)
- ✅ Migração gradual (possível testar em etapas)
- ✅ Reversível (pode reverter se necessário)

**Desvantagens**:
- ❌ Código adicional (adapter)
- ❌ Dupla estrutura temporária

### Opção 2: Refatoração Completa (Agressiva)

Substituir completamente parser.GerberObject por models.GerberObject.

**Vantagens**:
- ✅ Estrutura única (sem duplicidade)
- ✅ Mais limpo a longo prazo

**Desvantagens**:
- ❌ Muitas mudanças necessárias (parser, render, etc.)
- ❌ Alto risco de breaking changes
- ❌ Difícil de testar gradualmente

### Opção 3: Híbrida - Refatoração Conservadora (Escolhida)

Manter parser.GerberObject mas usar Command Pattern para reduzir complexidade:

```python
# MainWindow refatorado mantém parser.GerberObject
# mas usa EditCommands para operações de edição

class MainWindow:
    def __init__(self):
        # Não usa GerberModel ainda
        self._full_layer_objects: list[ParserGerberObject] = []

    def on_edit_object(self, index: int):
        """Edita objeto usando Command Pattern (complexidade 27 → <5)"""
        obj = self._full_layer_objects[index]

        # Factory para criar comando apropriado
        command = self._create_edit_command(obj)

        # Executar comando
        if command:
            modified = command.execute()
            self._full_layer_objects[index] = modified

    def _create_edit_command(self, obj):
        """Factory Method - elimina if/elif chain"""
        # ... lógica simples de seleção
```

**Vantagens**:
- ✅ Reduz complexidade imediatamente (46 → <5)
- ✅ Padrão Command aplicado (SOLID OCP)
- ✅ Sem breaking changes
- ✅ Fácil de testar

**Desvantagens**:
- ❌ Não usa GerberModel/GerberController ainda
- ❌ Migração incompleta

## Decisão: Opção 3 (Refatoração Conservadora)

**Rationale**:
1. **Reduz complexidade imediatamente**: Obj. principal atingido
2. **Baixo risco**: Sem breaking changes
3. **Fácil de testar**: Testes de integração já criados
4. **Preparação para futuro**: Padrão Command facilita migração futura

## Plano de Implementação

### Fase 1: Criar Command wrappers para Parser GerberObject

```python
# aoi_lib/gerber_core/commands/parser_edit_commands.py
class ParserEditObjectCommand(ABC):
    """Comando para editar parser.GerberObject"""

    @abstractmethod
    def execute(self) -> ParserGerberObject:
        pass

class ParserEditCircleCommand(ParserEditObjectCommand):
    def __init__(self, obj: ParserGerberObject, changes: dict):
        self.obj = obj
        self.changes = changes

    def execute(self) -> ParserGerberObject:
        # Edita params["dia_mm"] e recalcula polygon_mm
        ...

class ParserEditRectangleCommand(ParserEditObjectCommand):
    # Edita params["width_mm"], params["height_mm"]
    ...
```

### Fase 2: Refatorar on_edit_object()

```python
def on_edit_object(self, index: int):
    """Edita objeto (complexidade 27 → <5)"""
    obj = self._full_layer_objects[index]

    # Usar Command Pattern
    command = self._create_edit_command(obj)
    if command is None:
        QMessageBox.information(...)
        return

    # Executar edição através de diálogo
    if self._execute_edit_dialog(command):
        modified = command.execute()
        self._full_layer_objects[index] = modified
        self._refresh_view()
```

### Fase 3: Refatorar on_edit_many_objects()

```python
def on_edit_many_objects(self, indices: list[int]):
    """Edita múltiplos objetos (complexidade 46 → <5)"""
    # Validações
    objs = [self._full_layer_objects[i] for i in indices]
    kinds = {o.kind for o in objs}

    if len(kinds) != 1:
        QMessageBox.information(...)
        return

    # Usar Command Pattern para edição em grupo
    command = self._create_batch_edit_command(objs)
    if command is None:
        return

    # Executar edição em grupo
    if self._execute_batch_edit_dialog(command):
        modified_objs = command.execute()
        # Atualizar objetos na lista
        ...
```

## Métricas Esperadas

### Antes
- `on_edit_object()`: 190 linhas, complexidade 27
- `on_edit_many_objects()`: 280+ linhas, complexidade 46
- Total mainwindow.py: 1,384 linhas

### Depois
- `on_edit_object()`: ~30 linhas, complexidade <5
- `on_edit_many_objects()`: ~40 linhas, complexidade <5
- Total mainwindow.py: ~1,100 linhas (-284 linhas)

## Próximos Passos

1. ✅ Testes de integração criados (10 tests passing)
2. ⏳ Criar `parser_edit_commands.py`
3. ⏳ Refatorar `on_edit_object()`
4. ⏳ Refatorar `on_edit_many_objects()`
5. ⏳ Testes completos
6. ⏳ Documentação

## Notas

- **Migração futura**: Em fase futura (Phase 2), migrar completamente para GerberModel/GerberController
- **Backward compatibility**: Mantida 100% (nada muda na interface pública)
- **Testabilidade**: Melhorada (Command Pattern facilita mocking)

## Conclusão

Refatoração conservadora atinge objetivo principal (reduzir complexidade)
com risco mínimo e prepara arquitetura para migração futura mais completa.
