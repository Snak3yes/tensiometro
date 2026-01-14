# Guia de Uso: Gerber Core Commands

**Última atualização:** 2026-01-14
**Versão:** 1.0.0
**Status:** SOLID Refactoring Phase 2 - Task 1.1.6 (Completo)

## Visão Geral

Este guia documenta como usar o novo sistema de **Command Pattern** implementado no módulo `aoi_lib.gerber_core` para manipulação de arquivos Gerber RS-274X.

**Objetivo:** Reduzir complexidade ciclomática e melhorar aderência aos princípios SOLID.

### Arquitetura

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

## Quando Usar Cada Tipo de Comando

### 1. `models.GerberObject` + `EditCommands` (Recomendado para novo código)

**Quando usar:**
- Novo código que não depende de `parser.GerberObject`
- Código que precisa de estrutura de dados limpa (dataclass)
- Testes unitários (sem dependência de PyQt6)
- Integração com `GerberController`

**Vantagens:**
- ✅ Type safety completo
- ✅ Estrutura de dados limpa (dataclass)
- ✅ 100% testável sem GUI
- ✅ MVC pattern completo

**Exemplo:**
```python
from aoi_lib.gerber_core.models import GerberObject, GerberModel
from aoi_lib.gerber_core.controllers import GerberController

# Setup
model = GerberModel()
controller = GerberController(model)

# Importar arquivo
with open("design.gbr", "r") as f:
    lines = f.readlines()
controller.import_gerber(lines, cfg)

# Selecionar e editar
controller.select_object(0, "copper")
controller.edit_selected_object({"diameter": 10.0})

# Batch edit
controller.select_objects([0, 1, 2])
controller.edit_selected_objects(scale_factor=1.5, dx=5.0, dy=0.0)
```

### 2. `parser.GerberObject` + `ParserEditCommands` (Solução temporária)

**Quando usar:**
- Código legado que já usa `parser.GerberObject`
- POC Gerber Viewer (`poc_gerber/`)
- Código que depende de `kind`, `params`, `polygon_mm`
- Migração gradual sem breaking changes

**Vantagens:**
- ✅ Zero breaking changes
- ✅ Backward compatibility
- ✅ Reduz complexidade imediatamente
- ✅ Fácil migração futura

**Exemplo:**
```python
from aoi_lib.gerber_core.parser import GerberObject
from aoi_lib.gerber_core.commands.parser_edit_commands import create_parser_edit_command

# Objeto existente do parser
obj = GerberObject(
    id=0,
    kind="flash_circle",
    dcode=10,
    x_mm=5.0,
    y_mm=3.0,
    params={"dia_mm": 2.5},
    polygon_mm=[...]  # calculado
)

# Criar comando usando Factory Function
command = create_parser_edit_command(obj)

# Executar edição
try:
    modified = command.execute(new_dia_mm=5.0)
    # modified é uma NOVA instância (imutabilidade)
    print(f"Diâmetro atualizado: {modified.params['dia_mm']}")
except ValueError as e:
    print(f"Erro: {e}")
```

## Command Pattern: Conceitos Chave

### Factory Function

A Factory Function `create_parser_edit_command(obj)` elimina cadeias if/elif/else:

**Antes (complexidade alta):**
```python
def edit_object(obj):
    if obj.kind == "flash_circle":
        # 20 linhas de código...
    elif obj.kind == "flash_rect":
        # 30 linhas de código...
    elif obj.kind == "flash_oval":
        # 30 linhas de código...
    elif obj.kind == "region":
        # 40 linhas de código...
```

**Depois (complexidade <5):**
```python
def edit_object(obj):
    command = create_parser_edit_command(obj)
    if command is None:
        raise ValueError(f"Tipo não suportado: {obj.kind}")

    modified = command.execute(appropriate_params)
```

### Template Method Pattern

Todos os comandos compartilham a mesma estrutura via Template Method:

```python
class ParserEditObjectCommand(ABC):
    def execute(self, **changes) -> GerberObject:
        """Template Method - define algoritmo, delega detalhes"""
        modified = copy.copy(self.original)
        modified.polygon_mm = copy.copy(modified.polygon_mm)

        # Passo 1: Aplicar mudanças específicas (definido em subclasses)
        self._apply_changes(modified, **changes)

        # Passo 2: Recalcular polígono
        self._recalculate_polygon(modified)

        return modified

    @abstractmethod
    def _apply_changes(self, obj, **changes):
        """Hook method - subclasses implementam detalhes"""
        pass
```

### Imutabilidade

Comandos retornam **NOVAS instâncias** em vez de modificar o original:

```python
obj = GerberObject(kind="flash_circle", params={"dia_mm": 2.5})
command = create_parser_edit_command(obj)

modified = command.execute(new_dia_mm=5.0)

# Original NÃO é modificado
assert obj.params["dia_mm"] == 2.5  # Ainda 2.5

# Nova instância com mudanças
assert modified.params["dia_mm"] == 5.0  # Nova instância
assert obj is not modified  # Objetos diferentes
```

## API Reference: ParserEditCommands

### `ParserEditCircleCommand`

Edita objetos circulares (`kind="flash_circle"`).

**Parâmetros do método `execute()`:**
- `new_dia_mm` (float, opcional): Novo diâmetro em mm
- `dx` (float, padrão 0.0): Translação em X
- `dy` (float, padrão 0.0): Translação em Y

**Validações:**
- `new_dia_mm` deve ser > 0 (senão levanta `ValueError`)

**Exemplo:**
```python
obj = GerberObject(kind="flash_circle", params={"dia_mm": 2.5}, ...)
command = ParserEditCircleCommand(obj)

# Editar apenas diâmetro
modified = command.execute(new_dia_mm=5.0)

# Editar diâmetro + posição
modified = command.execute(new_dia_mm=5.0, dx=10.0, dy=3.0)

# Apenas translação
modified = command.execute(dx=5.0, dy=0.0)
```

### `ParserEditRectangleCommand`

Edita objetos retangulares (`kind="flash_rect"`).

**Parâmetros do método `execute()`:**
- `new_width_mm` (float, opcional): Nova largura em mm
- `new_height_mm` (float, opcional): Nova altura em mm
- `scale_x` (float, padrão 1.0): Fator de escala em X
- `scale_y` (float, padrão 1.0): Fator de escala em Y
- `dx` (float, padrão 0.0): Translação em X
- `dy` (float, padrão 0.0): Translação em Y

**Validações:**
- `new_width_mm` e `new_height_mm` devem ser > 0
- `scale_x` e `scale_y` devem ser > 0

**Exemplo:**
```python
obj = GerberObject(
    kind="flash_rect",
    params={"width_mm": 5.0, "height_mm": 3.0},
    ...
)
command = ParserEditRectangleCommand(obj)

# Editar dimensões absolutas
modified = command.execute(new_width_mm=10.0, new_height_mm=6.0)

# Editar por escala (2x)
modified = command.execute(scale_x=2.0, scale_y=2.0)

# Combinar escala + translação
modified = command.execute(scale_x=1.5, scale_y=1.5, dx=5.0, dy=0.0)
```

### `ParserEditObroundCommand`

Edita objetos obround (`kind="flash_oval"`).

**Parâmetros:** Idênticos a `ParserEditRectangleCommand`

**Exemplo:**
```python
obj = GerberObject(
    kind="flash_oval",
    params={"width_mm": 8.0, "height_mm": 4.0},
    ...
)
command = ParserEditObroundCommand(obj)

modified = command.execute(new_width_mm=12.0, new_height_mm=6.0)
```

### `ParserEditRegionCommand`

Edita regiões poligonais (`kind="region"`).

**Parâmetros do método `execute()`:**
- `scale_x` (float, padrão 1.0): Fator de escala em X
- `scale_y` (float, padrão 1.0): Fator de escala em Y
- `dx` (float, padrão 0.0): Translação em X
- `dy` (float, padrão 0.0): Translação em Y

**Validações:**
- `polygon_mm` deve ter pelo menos 3 vértices
- Escala é aplicada em relação ao centro geométrico

**Exemplo:**
```python
polygon = [(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)]
obj = GerberObject(kind="region", polygon_mm=polygon, ...)
command = ParserEditRegionCommand(obj)

# Escala 2x (maintém centro em (5, 5))
modified = command.execute(scale_x=2.0, scale_y=2.0)

# Escala + translação
modified = command.execute(scale_x=1.5, scale_y=1.5, dx=10.0, dy=5.0)
```

### `create_parser_edit_command(obj)`

Factory Function que cria o comando apropriado baseado no tipo de objeto.

**Parâmetros:**
- `obj` (GerberObject): Objeto do parser a ser editado

**Retorna:**
- `ParserEditObjectCommand` ou `None` se tipo não suportado

**Tipos suportados:**
- `"flash_circle"` → `ParserEditCircleCommand`
- `"flash_rect"` → `ParserEditRectangleCommand`
- `"flash_oval"` → `ParserEditObroundCommand`
- `"region"` → `ParserEditRegionCommand`

**Exemplo:**
```python
obj = GerberObject(kind="flash_circle", ...)
command = create_parser_edit_command(obj)

if command is None:
    print(f"Tipo {obj.kind} não suportado para edição")
else:
    modified = command.execute(new_dia_mm=5.0)
```

## Exemplos de Uso Avançado

### Edição em Grupo com Factory Function

```python
from aoi_lib.gerber_core.parser import GerberObject
from aoi_lib.gerber_core.commands.parser_edit_commands import create_parser_edit_command

# Lista de objetos do mesmo tipo
objs = [
    GerberObject(kind="flash_rect", params={"width_mm": 5.0, "height_mm": 3.0}, ...),
    GerberObject(kind="flash_rect", params={"width_mm": 5.0, "height_mm": 3.0}, ...),
    GerberObject(kind="flash_rect", params={"width_mm": 5.0, "height_mm": 3.0}, ...),
]

# Editar todos com escala 2x
modified_objs = []
for obj in objs:
    command = create_parser_edit_command(obj)
    if command:
        modified = command.execute(scale_x=2.0, scale_y=2.0)
        modified_objs.append(modified)

# Atualizar lista original
objs[:] = modified_objs
```

### Tratamento de Erros

```python
command = create_parser_edit_command(obj)

if command is None:
    QMessageBox.warning(None, "Erro", f"Tipo {obj.kind} não pode ser editado")
    return

try:
    modified = command.execute(new_dia_mm=-5.0)  # Inválido!
except ValueError as e:
    QMessageBox.warning(None, "Erro ao modificar", str(e))
    # Log: "Diâmetro deve ser > 0, recebido: -5.0"
```

### Integração com UI (PyQt6)

```python
from PyQt6.QtWidgets import QInputDialog
from aoi_lib.gerber_core.commands.parser_edit_commands import create_parser_edit_command

def on_edit_circle(obj):
    """Edita círculo com diálogo."""
    command = create_parser_edit_command(obj)
    if command is None:
        return

    # Diálogo para input
    new_dia, ok = QInputDialog.getDouble(
        None,
        "Editar Círculo",
        "Diâmetro (mm):",
        value=obj.params.get("dia_mm", 0.0),
        min=0.1,
        max=100.0,
        decimals=3
    )

    if not ok:
        return  # Usuário cancelou

    try:
        modified = command.execute(new_dia_mm=new_dia)
        # Atualizar objeto na lista
        objects[idx] = modified
        refresh_preview()
    except ValueError as e:
        QMessageBox.warning(None, "Erro", str(e))
```

## Boas Práticas

### ✅ DO

1. **Sempre usar Factory Function** em vez de instanciar comandos diretamente:
   ```python
   # Bom
   command = create_parser_edit_command(obj)

   # Evitar (mas funciona se necessário)
   command = ParserEditCircleCommand(obj)
   ```

2. **Verificar `None`** da Factory Function:
   ```python
   command = create_parser_edit_command(obj)
   if command is None:
       # Tratar tipo não suportado
       return
   ```

3. **Usar try/except** para `ValueError`:
   ```python
   try:
       modified = command.execute(new_dia_mm=...)
   except ValueError as e:
       # Tratar erro de validação
       logger.error(f"Erro ao editar: {e}")
   ```

4. **Aproveitar imutabilidade** - comando não modifica original:
   ```python
   modified = command.execute(...)
   # Original ainda intacto
   backup_list.append(original)  # Ainda válido
   work_list[idx] = modified  # Usar modificada
   ```

### ❌ DON'T

1. **Não assuma que Factory Function retorna comando não-None:**
   ```python
   # RUIM - pode crashar
   command = create_parser_edit_command(obj)
   modified = command.execute(...)  # Se command=None, crash!

   # BOM
   command = create_parser_edit_command(obj)
   if command is None:
       return  # Ou raise erro apropriado
   modified = command.execute(...)
   ```

2. **Não modifique o objeto original diretamente** se usar Command Pattern:
   ```python
   # RUIM - mistura padrões
   command = create_parser_edit_command(obj)
   obj.params["dia_mm"] = 5.0  # Não faça isso!
   modified = command.execute(...)

   # BOM - use o retorno do comando
   modified = command.execute(new_dia_mm=5.0)
   objs[idx] = modified  # Substituir na lista
   ```

3. **Não ignore validações:**
   ```python
   # RUIM - pode passar valor inválido
   modified = command.execute(new_dia_mm=user_input_sem_validacao)

   # BOM - valida antes ou trata erro
   try:
       modified = command.execute(new_dia_mm=user_input)
   except ValueError as e:
       show_error_to_user(str(e))
   ```

## Migração de Código Legado

### Antes (manipulação direta)

```python
def edit_circle(obj, new_dia):
    # Manipulação direta de params
    obj.params["dia_mm"] = new_dia

    # Recalcular polígono manualmente
    if obj.x_mm is not None and obj.y_mm is not None:
        from aoi_lib.gerber_core.geometry import circle_to_polys_mm
        polys = circle_to_polys_mm(obj.x_mm, obj.y_mm, new_dia)
        obj.polygon_mm = polys[0]
```

### Depois (Command Pattern)

```python
from aoi_lib.gerber_core.commands.parser_edit_commands import create_parser_edit_command

def edit_circle(obj, new_dia):
    command = create_parser_edit_command(obj)
    if command is None:
        raise ValueError(f"Tipo não suportado: {obj.kind}")

    # Command encapsula lógica de modificação + recálculo
    modified = command.execute(new_dia_mm=new_dia)
    return modified
```

## Testes

### Exemplo de Teste Unitário

```python
import pytest
from aoi_lib.gerber_core.parser import GerberObject
from aoi_lib.gerber_core.commands.parser_edit_commands import (
    ParserEditCircleCommand,
    create_parser_edit_command
)

def test_edit_circle_diameter():
    """Testa edição de diâmetro de círculo."""
    obj = GerberObject(
        id=0,
        kind="flash_circle",
        dcode=10,
        x_mm=0.0,
        y_mm=0.0,
        params={"dia_mm": 5.0},
        polygon_mm=[]
    )

    command = ParserEditCircleCommand(obj)
    modified = command.execute(new_dia_mm=10.0)

    assert modified.params["dia_mm"] == 10.0
    assert modified.x_mm == 0.0  # Posição inalterada
    assert modified.polygon_mm is not None  # Polígono recalculado

def test_factory_function_circle():
    """Testa Factory Function para círculo."""
    obj = GerberObject(kind="flash_circle", ...)
    cmd = create_parser_edit_command(obj)

    assert isinstance(cmd, ParserEditCircleCommand)

def test_invalid_diameter_raises_error():
    """Testa que diâmetro inválido levanta ValueError."""
    obj = GerberObject(kind="flash_circle", params={"dia_mm": 5.0}, ...)
    command = ParserEditCircleCommand(obj)

    with pytest.raises(ValueError) as exc_info:
        command.execute(new_dia_mm=-5.0)

    assert "Diâmetro deve ser > 0" in str(exc_info.value)
```

## Solução de Problemas

### Problema: Command é `None`

**Sintoma:** `command = create_parser_edit_command(obj)` retorna `None`

**Causa:** Tipo de objeto não suportado

**Solução:**
```python
command = create_parser_edit_command(obj)
if command is None:
    logger.warning(f"Tipo {obj.kind} não suportado para edição")
    QMessageBox.information(None, "Não Editável",
                            f"Objetos do tipo {obj.kind} não podem ser editados.")
    return
```

### Problema: `ValueError` ao executar comando

**Sintoma:** `command.execute(...)` levanta `ValueError`

**Causa:** Parâmetros inválidos (ex: diâmetro negativo)

**Solução:**
```python
try:
    modified = command.execute(new_dia_mm=user_input)
except ValueError as e:
    logger.error(f"Erro de validação: {e}")
    QMessageBox.warning(None, "Erro", str(e))
```

### Problema: Polígono não atualizado

**Sintoma:** `modified.polygon_mm` está vazio ou desatualizado

**Causa:** Comando não recalcula polígono corretamente

**Solução:** Verificar se `x_mm` e `y_mm` não são `None`:
```python
# Comandos recalcularão polígono apenas se x_mm e y_mm definidos
if obj.x_mm is not None and obj.y_mm is not None:
    modified = command.execute(new_dia_mm=5.0)
    # modified.polygon_mm será recalculado
else:
    logger.warning("Objeto sem posição - polígono não recalculado")
```

## Referências

- **Código Fonte:** `aoi_lib/gerber_core/commands/`
- **Testes:** `tests/unit/gerber_core/commands/`
- **Integração:** `tests/integration/gerber_core/test_mainwindow_refactoring.py`
- **Plano de Refatoração:** `conductor/tracks/solid_refactoring_phase2_20260114/`
- **Análise SOLID:** `docs/reports/SOLID_ANALYSIS_REPORT.md`

## Changelog

### 2026-01-14 - v1.0.0
- ✅ Implementação inicial de Command Pattern
- ✅ 4 comandos concretos (Circle, Rectangle, Obround, Region)
- ✅ Factory Function para seleção de comando
- ✅ 17 testes unitários (96% cobertura)
- ✅ Refatoração de mainwindow.py (complexidade 27,46 → <5)
- ✅ Zero breaking changes

---

**Próximos Passos:**
- Fase 2: Migrar parser.py com Strategy Pattern
- Fase 3: Criar adapters entre parser e model
- Fase 4: Migrar completamente para GerberModel
