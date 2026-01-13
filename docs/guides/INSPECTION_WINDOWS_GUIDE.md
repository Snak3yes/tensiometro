# Inspection Windows Widget - Guia de Integração

**Track 6 do Engineering Wizard**
**Data:** 2026-01-13
**Status:** ✅ COMPLETO

---

## 🎯 Visão Geral

O `InspectionWindowsWidget` é o componente responsável pela configuração de janelas de inspeção (apertures) no fluxo de engenharia. Ele permite agrupar automaticamente aberturas do Gerber por dimensões e configurar parâmetros de inspeção (thresholds, binarização, etc.) por grupo.

### Localização

- **Widget:** `consumo_lib/widgets/engenharia/inspection_windows_widget.py`
- **Modelos:** `consumo_lib/models/inspection_window.py`
- **Testes:** `tests/unit/widgets/engenharia/test_inspection_windows_widget.py`

---

## 🚀 Quick Start

### 1. Importar e Inicializar

```python
from PyQt6.QtWidgets import QApplication, QDialog, QVBoxLayout
from consumo_lib.widgets.engenharia import InspectionWindowsWidget
from aoi_lib.gerber_parser import GerberParser

# Criar widget
widget = InspectionWindowsWidget()

# Carregar janelas do Gerber
parser = GerberParser()
result = parser.parse_file("stencil.gbr")
widget.load_from_gerber(result.objects)

# Exibir
layout = QVBoxLayout()
layout.addWidget(widget)
```

### 2. Obter Configurações

```python
# Validar
if widget.validate():
    print("Todos os grupos estão configurados")

# Obter configurações finais
configs = widget.get_configurations()  # Dict[window_id, WindowConfig]
groups = widget.get_groups()  # List[WindowGroup]

print(f"Grupos criados: {len(groups)}")
print(f"Janelas configuradas: {len(configs)}")
```

### 3. Sinais para Integração

```python
# Conectar sinais para validação em tempo real
widget.validation_changed.connect(lambda is_valid: update_next_button(is_valid))
widget.group_count_changed.connect(lambda count: update_summary(count))
```

---

## 📐 API Reference

### InspectionWindowsWidget

#### Métodos Públicos

```python
load_from_gerber(gerber_objects: List[Any]) -> None
```
Carrega janelas de inspeção a partir de objetos Gerber.

**Parâmetros:**
- `gerber_objects`: Lista de objetos `GerberObject` do `gerber_parser.py`

**Exemplo:**
```python
widget.load_from_gerber(parser_result.objects)
```

---

```python
validate() -> bool
```
Valida se todos os grupos têm configuração válida.

**Retorna:**
- `True` se todos os grupos configurados
- `False` se algum grupo sem configuração

---

```python
get_configurations() -> Dict[int, WindowConfig]
```
Retorna todas as configurações de janelas.

**Retorna:**
- Dicionário `{window_id: WindowConfig}`

---

```python
get_groups() -> List[WindowGroup]
```
Retorna todos os grupos criados.

**Retorna:**
- Lista de objetos `WindowGroup`

---

```python
set_read_only(read_only: bool) -> None
```
Define modo read-only (para programas Base).

**Parâmetros:**
- `read_only`: `True` para bloquear edições

---

#### Sinais

```python
validation_changed(bool)  # Emitido quando validação muda
group_count_changed(int)  # Emitido quando número de grupos muda
```

---

## 🗂️ Modelos de Dados

### WindowConfig

Configuração de inspeção para uma janela ou grupo.

```python
from consumo_lib.models.inspection_window import WindowConfig, BinarizationMethod, PreprocessMethod

config = WindowConfig(
    ok_threshold=90.0,              # % mínima para OK
    partial_threshold=70.0,         # % mínima para PARTIAL
    binarization_method=BinarizationMethod.OTSU,
    preprocess_method=PreprocessMethod.BLUR
)

# Validar
if config.validate():
    print("Configuração válida")

# Serializar
data = config.to_dict()  # Dict para JSON
loaded = WindowConfig.from_dict(data)  # Carregar de Dict
```

### InspectionWindow

Representa uma abertura individual do Gerber.

```python
from consumo_lib.models.inspection_window import InspectionWindow

window = InspectionWindow(
    id=1,
    x_mm=10.0,
    y_mm=20.0,
    kind="circle",  # ou "rect", "oval", "macro"
    dimensions={"diameter_mm": 0.5},
    config=None,  # WindowConfig ou None (usa do grupo)
    status=WindowStatus.NOT_CONFIGURED,
    is_exception=False
)

# Chave de agrupamento automática
print(window.group_key)  # "circle_0.50mm"
```

### WindowGroup

Grupo de janelas com mesma configuração.

```python
from consumo_lib.models.inspection_window import WindowGroup

group = WindowGroup(
    name="0.5mm Círculo",
    key="circle_0.50mm"
)

# Adicionar janelas
group.add_window(window1)
group.add_window(window2)

# Aplicar configuração
config = WindowConfig(ok_threshold=90.0, partial_threshold=70.0)
group.apply_config_to_group(config, confirm=True)

# Propriedades
print(group.count)  # Total de janelas
print(group.standard_count)  # Janelas com config do grupo
print(group.exception_count)  # Janelas com config individual
```

### WindowLibrary

Biblioteca global de configurações.

```python
from consumo_lib.models.inspection_window import WindowLibrary
from pathlib import Path

# Criar biblioteca
library = WindowLibrary()

# Adicionar configuração
config = WindowConfig(ok_threshold=90.0, partial_threshold=70.0)
library.add_config("circle_0.50mm", config)

# Salvar/carregar
library_path = Path("data/inspection_config_library.json")
library.save(library_path)
loaded_library = WindowLibrary.load(library_path)

# Sugerir configuração
suggested = library.suggest_config("circle_0.51mm")  # Fuzzy matching
```

---

## 🎨 Layout da Interface

```
┌─────────────────────────────────────────────────────────────┐
│  InspectionWindowsWidget                                    │
├───────────────────────────┬─────────────────────────────────┤
│  LEFT PANEL (40%)         │  RIGHT PANEL (60%)             │
│                           │                                 │
│  ┌─────────────────────┐  │  ┌───────────────────────────┐ │
│  │ 📦 Groups Tree      │  │  │ GroupConfigPanel          │ │
│  │                     │  │  │                           │ │
│  │ 📦 0.5mm (145) ✅   │  │  │ Grupo: 0.5mm Círculo     │ │
│  │  ├─ Padrão          │  │  │ Qtd: 145 aberturas        │ │
│  │  └─ Exceções (3)    │  │  │                           │ │
│  │                     │  │  │ Thresholds:               │ │
│  │ 📦 0.8mm (82) 🟢    │  │  │  ✅ OK ≥ [90%]           │ │
│  │  └─ Padrão          │  │  │  ⚠️ PARTIAL ≥ [70%]      │ │
│  │                     │  │  │                           │ │
│  │ [Expandir Todos]     │  │  │ Binarização:              │ │
│  │ [Recolher Todos]    │  │  │  Método: [Otsu ▼]        │ │
│  │ [Auto-Agrupar]      │  │  │  Pré: [Blur ▼]           │ │
│  └─────────────────────┘  │  │                           │ │
│                           │  │ Preview (3 exemplos):      │ │
│  ┌─────────────────────┐  │  │  [┌───┐ ┌───┐ ┌───┐]    │ │
│  │ 📚 LibraryPanel     │  │  │  [│ ✅ │ │ ✅ │ │ ✅ │]    │ │
│  │                     │  │  │  [└───┘ └───┘ └───┘]    │ │
│  │ ⚙️ 0.5mm Padrão    │  │  │                           │ │
│  │ ⚙️ 0.8mm Padrão    │  │  │ [☑ Aplicar a todas]      │ │
│  │ [Carregar]          │  │  │                           │ │
│  └─────────────────────┘  │  │ [Confirmar ✅]            │ │
│                           │  │ [Exceção ⚙️]             │ │
│                           │  │ [Salvar 💾]               │ │
│                           │  └───────────────────────────┘ │
└───────────────────────────┴─────────────────────────────────┘
```

---

## 🔄 Fluxo de Trabalho Típico

### 1. Carregar Gerber (Aba 2 → Aba 6)

```python
# Na Aba 2, usuário carregou Gerber
parser_result = gerber_tab.get_parse_result()

# Ao entrar na Aba 6:
inspection_widget.load_from_gerber(parser_result.objects)

# Widget automaticamente:
# 1. Cria InspectionWindow para cada objeto
# 2. Agrupa por dimensões (auto-group)
# 3. Aplica sugestões da biblioteca
# 4. Atualiza árvore visual
```

### 2. Configurar Grupos

```python
# Usuário seleciona grupo na árvore
# Widget mostra configuração no painel direito

# Usuário ajusta thresholds e clique "Confirmar"
# Widget:
# 1. Aplica config a todas janelas do grupo
# 2. Marca grupo como ✅ confirmado
# 3. Emite validation_changed(True)
# 4. Habilita botão "Próximo" no wizard
```

### 3. Salvar na Biblioteca

```python
# Usuário configura grupo e clica "Salvar na Biblioteca"
# Widget:
# 1. Salva config com chave do grupo
# 2. Persiste em JSON
# 3. Disponível para próximos programas
```

### 4. Avançar para Aba 7

```python
# Wizard valida antes de avançar
if inspection_widget.validate():
    # Obter configurações
    configs = inspection_widget.get_configurations()
    groups = inspection_widget.get_groups()

    # Salvar no programa
    program_data = {
        "window_configs": {wid: cfg.to_dict() for wid, cfg in configs.items()},
        "groups": [g.to_dict() for g in groups]
    }

    # Avançar para Aba 7
    wizard.next_step()
```

---

## 🧪 Testando

### Executar Testes Unitários

```bash
# Com venv
.venv/Scripts/python.exe -m pytest tests/unit/widgets/engenharia/test_inspection_windows_widget.py -v

# Com cobertura
.venv/Scripts/python.exe -m pytest tests/unit/widgets/engenharia/test_inspection_windows_widget.py --cov=consumo_lib/models/inspection_window --cov=consumo_lib/widgets/engenharia/inspection_windows_widget
```

### Demo Interativo

```bash
python tools/demo_inspection_windows.py
```

---

## 📊 Exemplos de Uso

### Exemplo 1: Configuração Básica

```python
from consumo_lib.models.inspection_window import (
    create_groups_from_windows,
    create_default_config,
    GroupingCriteria
)

# Criar grupos
windows = [...]  # Lista de InspectionWindow
groups = create_groups_from_windows(windows)

# Configurar primeiro grupo
config = create_default_config()
groups[0].apply_config_to_group(config, confirm=True)

# Verificar
print(f"Grupo: {groups[0].name}")
print(f"Status: {groups[0].status.value}")
print(f"Janelas: {groups[0].count}")
```

### Exemplo 2: Biblioteca de Configs

```python
from consumo_lib.models.inspection_window import WindowLibrary, WindowConfig
from pathlib import Path

# Criar biblioteca
library = WindowLibrary()

# Adicionar configs
library.add_config("circle_0.50mm", WindowConfig(ok_threshold=90.0))
library.add_config("circle_0.80mm", WindowConfig(ok_threshold=85.0))
library.add_config("rect_1.00x0.50mm", WindowConfig(ok_threshold=88.0))

# Salvar
library.save(Path("data/inspection_config_library.json"))

# Carregar e sugerir
loaded = WindowLibrary.load(Path("data/inspection_config_library.json"))
suggested = loaded.suggest_config("circle_0.52mm")  # Retorna config do 0.50mm
```

### Exemplo 3: Exceções

```python
from consumo_lib.models.inspection_window import WindowGroup, WindowConfig

# Criar grupo
group = WindowGroup(name="Test", key="test")
group.add_window(window1)
group.add_window(window2)
group.add_window(window3)

# Aplicar config padrão
config = WindowConfig(ok_threshold=90.0)
group.apply_config_to_group(config)

# Criar exceção para window2
exception_config = WindowConfig(ok_threshold=95.0, partial_threshold=80.0)
window2.is_exception = True
window2.config = exception_config
window2.status = WindowStatus.CONFIGURED
group.exceptions = [window2.id]

# Verificar
print(f"Total: {group.count}")
print(f"Padrão: {group.standard_count}")  # 2
print(f"Exceções: {group.exception_count}")  # 1
```

---

## 🔧 Troubleshooting

### Problema: Agrupamento não funciona

**Causa:** Objetos Gerber sem dimensões.

**Solução:**
```python
# Verificar se objetos têm parâmetros
for obj in gerber_objects:
    if hasattr(obj, 'params'):
        print(f"ID {obj.id}: {obj.params}")
```

### Problema: Biblioteca não salva

**Causa:** Diretório `data/` não existe.

**Solução:**
```python
from pathlib import Path
Path("data").mkdir(exist_ok=True)
```

### Problema: Validação sempre retorna False

**Causa:** Alguns grupos sem configuração.

**Solução:**
```python
# Verificar grupos
for group in widget.get_groups():
    print(f"{group.name}: config={group.config is not None}")
```

---

## 📚 Referências

- **Implementação:** `docs/reports/TRACK6_IMPLEMENTACAO_JANELAS_INPECAO.md`
- **Especificação:** `docs/guides/QUESTIONARIO_FLUXO_ENGENHARIA_FASE2.md` (GAP 7)
- **Plano Visual:** `docs/guides/PLANO_PROPOSTAS_ABAS_ENGENHARIA.md` (Aba 6)
- **Gerber Parser:** `aoi_lib/gerber_parser.py`

---

**Autor:** Claude Code (Sonnet 4.5)
**Data:** 2026-01-13
**Versão:** 1.0
