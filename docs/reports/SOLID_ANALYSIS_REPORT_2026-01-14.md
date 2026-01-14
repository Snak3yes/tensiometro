# SOLID Analysis Report - Tensiometro Project

**Data:** 2026-01-14
**Versão:** 0.4.0
**Analista:** Claude Code (SOLID Analyzer Skill)
**Escopo:** Análise completa de violações SOLID e métricas de qualidade

---

## Executive Summary

### 📊 Métricas Gerais

| Métrica | Valor | Status |
|---------|-------|--------|
| **Total de Arquivos Python** | 184 | ✅ |
| **Linhas de Código** | 59,516 | ✅ |
| **Módulos Analisados** | 171 | ✅ |
| **Classes Analisadas** | 220 | ✅ |
| **Classes com Herança** | 143 | ✅ |

### 🎯 Score SOLID Global: **72/100** (BOM)

| Princípio | Score | Peso | Status |
|-----------|-------|------|--------|
| **SRP** (Single Responsibility) | 65/100 | 5 | ⚠️ Atenção Necessária |
| **OCP** (Open/Closed) | 78/100 | 4 | ✅ Bom |
| **LSP** (Liskov Substitution) | 85/100 | 3 | ✅ Excelente |
| **ISP** (Interface Segregation) | 70/100 | 3 | ⚠️ Aceitável |
| **DIP** (Dependency Inversion) | 55/100 | 4 | 🔴 Crítico |

### 📈 Resumo de Violações

| Severidade | Quantidade | Ações Imediatas |
|------------|-----------|-----------------|
| 🔴 **CRITICAL** | 3 | Refatoração urgente |
| 🟠 **HIGH** | 12 | Planejar refatoração |
| 🟡 **MEDIUM** | 28 | Melhorias contínuas |
| 🟢 **LOW** | 45 | Technical debt |

---

## 1. SRP - Single Responsibility Principle (Score: 65/100)

### 📋 Regra
Cada classe/módulo deve ter uma única razão para mudar.

### 🔴 Violações CRÍTICAS (>1000 linhas)

#### 1.1 `aoi_lib/stencil_tension_old.py` - **1,409 linhas**
**Status:** 🔴 CRITICAL (JÁ ARQUIVADO - Refatorado em 2026-01-14)

**Responsabilidades Identificadas:**
- ❌ Gerenciamento de medição de tensão
- ❌ Interface de usuário (dialog)
- ❌ Lógica de negócio (validação, cálculos)
- ❌ Comunicação serial (tensíometro)
- ❌ Controle de movimento CNC
- ❌ Persistência de dados
- ❌ Geração de relatórios

**Ação Tomada:** ✅ **REFATORADO** em `aoi_lib/tensiometer/`
- 5 módulos focados criados (2,368 linhas)
- 48 unit tests (100% service layer coverage)
- Zero breaking changes

**Referência:** `conductor/archive/solid_refactoring_phase1_20260114/`

---

#### 1.2 `aoi_lib/gerber_core/gui/mainwindow.py` - **1,384 linhas**
**Status:** 🔴 CRITICAL

**Responsabilidades Identificadas:**
- ❌ Interface principal do viewer Gerber
- ❌ Manipulação de objetos (criação, edição, deleção)
- ❌ Controles de zoom e pan
- ❌ Exportação de arquivos
- ❌ Gerenciamento de camadas
- ❌ Edição em lote (múltiplos objetos)

**Funções Complexas:**
- `on_edit_many_objects()` (linha 924) - complexidade 46
- `on_edit_object()` (linha 733) - complexidade 27

**Recomendação:**
```python
# ✅ REFACTORING SUGERIDO:

# gerber_core/gui/mainwindow.py (UI apenas)
class GerberMainWindow(QMainWindow):
    def __init__(self, viewer: GerberViewer, controller: GerberController):
        self.viewer = viewer
        self.controller = controller

# gerber_core/controllers/gerber_controller.py (lógica de negócio)
class GerberController:
    def __init__(self, model: GerberModel):
        self.model = model

    def edit_object(self, obj_id, changes):
        # Valida e aplica mudanças
        pass

    def edit_many_objects(self, obj_ids, changes):
        # Edição em lote
        pass

# gerber_core/models/gerber_model.py (dados)
class GerberModel:
    def __init__(self):
        self.layers = []
        self.objects = []

# gerber_core/commands/edit_commands.py (padrão Command)
class EditObjectCommand:
    def execute(self): pass
    def undo(self): pass
```

**Prioridade:** 🔴 HIGH
**Estimativa:** 3-5 dias

---

#### 1.3 `aoi_lib/report_generator.py` - **1,366 linhas**
**Status:** ⚠️ MEDIUM (Parcialmente OK)

**Responsabilidades Identificadas:**
- ✅ Geração de PDF (Reportlab)
- ⚠️ Criação de gráficos (Matplotlib)
- ⚠️ Layout de páginas (múltiplos builders)
- ⚠️ Configuração de relatórios
- ⚠️ Serialização/deserialização

**Análise:**
- **Boa:** Separado em builders (`TensionReportBuilder`, `StencilHistoryReportBuilder`, `InspectionReportBuilder`)
- **Ruim:** Cada builder tem ~400 linhas (muito grande)
- **Ruim:** Mistura layout + gráficos + dados

**Recomendação:**
```python
# ✅ REFACTORING SUGERIDO:

# report_generator/builders/tension_builder.py (~150 linhas)
class TensionReportBuilder:
    def __init__(self, layout: ReportLayout, chart_gen: ChartGenerator):
        self.layout = layout
        self.chart_gen = chart_gen

# report_generator/layout/report_layout.py
class ReportLayout:
    def create_header(self): pass
    def create_footer(self): pass
    def create_table(self): pass

# report_generator/charts/chart_generator.py
class ChartGenerator:
    def create_heatmap(self, data): pass
    def create_trend_chart(self, data): pass

# report_generator/config/report_config.py
class ReportConfig:
    # Já existe e está bom
    pass
```

**Prioridade:** 🟡 MEDIUM
**Estimativa:** 2-3 dias
**Nota:** Arquitetura já está parcialmente correta, apenas extrair gráficos e layout.

---

### 🟠 Violações HIGH (>500 linhas)

#### 1.4 `consumo_lib/widgets/engenharia/alignment_widget.py` - **1,179 linhas**
**Status:** 🟠 HIGH

**Responsabilidades Identificadas:**
- ❌ Interface de alinhamento Gerber ↔ Imagem
- ❌ Captura de templates fiduciais
- ❌ Template matching (OpenCV)
- ❌ Cálculo de transformação (matriz)
- ❌ Renderização de overlay
- ❌ Gerenciamento de estado
- ❌ Validação de dependências

**Recomendação:**
```python
# ✅ Extrair para:

# consumo_lib/services/fiducial_alignment_service.py
class FiducialAlignmentService:
    def detect_templates(self, image, templates): pass
    def calculate_transform(self, matches): pass

# consumo_lib/services/template_matching_service.py
class TemplateMatchingService:
    def match_template(self, image, template): pass

# consumo_lib/models/alignment_state.py
class AlignmentState:
    # Já existe em wizard_state.py, extrair para módulo dedicado
    pass

# consumo_lib/widgets/engenharia/alignment_widget.py (UI apenas)
class AlignmentWidget(QWidget):
    def __init__(self, alignment_service: FiducialAlignmentService):
        self.service = alignment_service
```

**Prioridade:** 🟠 MEDIUM-HIGH
**Estimativa:** 2-3 dias

---

#### 1.5 `aoi_lib/fiducial_alignment_widget.py` - **959 linhas**
**Status:** 🟠 HIGH

**Responsabilidades Identificadas:**
- ❌ Interface de captura de fiduciais
- ❌ Controle de câmera
- ❌ Seleção de regiões (click-to-select)
- ❌ Template matching
- ❌ Gerenciamento de configuração

**Nota:** Este arquivo parece ser legado. Verificar se ainda está em uso após refatoração.

**Ação:** Verificar se foi substituído por `fiducial_alignment.py` e `alignment_widget.py`

---

#### 1.6 `aoi_lib/stencil_database.py` - **914 linhas**
**Status:** 🟠 HIGH

**Responsabilidades Identificadas:**
- ❌ Gerenciamento de banco SQLite
- ❌ Migração JSON → SQLite
- ❌ Queries de tensão
- ❌ Queries de inspeção
- ❌ Queries de stencil
- ❌ Transações e rollback
- ❌ Validação de dados

**Análise:**
- 21 métodos públicos (violação ISP também)
- Muitas responsabilidades em uma única classe

**Recomendação:**
```python
# ✅ REFACTORING SUGERIDO:

# aoi_lib/database/connection.py
class DatabaseConnection:
    def connect(self): pass
    def close(self): pass

# aoi_lib/database/repositories/stencil_repository.py
class StencilRepository:
    def save(self, stencil): pass
    def find_by_code(self, code): pass

# aoi_lib/database/repositories/tension_repository.py
class TensionRepository:
    def save_measurements(self, measurements): pass
    def get_history(self, stencil_code): pass

# aoi_lib/database/repositories/inspection_repository.py
class InspectionRepository:
    def save_inspection(self, inspection): pass
    def get_history(self, stencil_code): pass

# aoi_lib/database/migrators/json_to_sqlite_migrator.py
class JsonToSqliteMigrator:
    def migrate(self, json_path): pass
```

**Prioridade:** 🟠 MEDIUM-HIGH
**Estimativa:** 3-4 dias

---

#### 1.7 `consumo_lib/dialogs/recipe_dialogs.py` - **881 linhas**
**Status:** 🟠 HIGH

**Responsabilidades Identificadas:**
- ❌ RecipeListWidget (UI)
- ❌ RecipeEditorDialog (UI + validação)
- ❌ RecipeManagerDialog (UI + persistência)
- ❌ Validação de receitas
- ❌ Gerenciamento de arquivos JSON

**Nota:** Este arquivo contém 3 diálogos em um único arquivo. Já existe `aoi_lib/recipe_manager.py` com lógica de negócio.

**Recomendação:**
```python
# ✅ Separar em:

# consumo_lib/dialogs/recipe/recipe_list_dialog.py
class RecipeListDialog(QDialog):
    # Apenas lista e seleção
    pass

# consumo_lib/dialogs/recipe/recipe_edit_dialog.py
class RecipeEditDialog(QDialog):
    # Apenas edição
    pass

# consumo_lib/dialogs/recipe/recipe_manager_dialog.py
class RecipeManagerDialog(QDialog):
    # Apenas gerenciamento
    pass
```

**Prioridade:** 🟡 MEDIUM
**Estimativa:** 1 dia

---

### 📊 Classes com Muitos Métodos Públicos (SRP + ISP)

| Classe | Métodos Públicos | Arquivo | Status |
|--------|-----------------|---------|--------|
| `AOIControllerApp` | 46 | `consumo_lib/main_window.py` | 🔴 Crítico |
| `PLCAxisController` | 29 | `aoi_lib/plc_axis_controller.py` | 🟠 Alto |
| `StencilDatabase` | 21 | `aoi_lib/stencil_database.py` | 🟠 Alto |
| `DialogRouter` | 20 | `consumo_lib/handlers/dialog_router.py` | 🟠 Alto |
| `AOIConfigManager` | 18 | `aoi_lib/config_manager.py` | 🟡 Médio |

---

## 2. OCP - Open/Closed Principle (Score: 78/100)

### 📋 Regra
Entidades devem estar abertas para extensão, mas fechadas para modificação.

### 🔴 Violações CRÍTICAS

#### 2.1 `aoi_lib/gerber_core/parser.py` - Função `_build_layer_core_mm()`
**Linha:** 200
**Complexidade:** 47
**Status:** 🔴 CRITICAL

```python
# ❌ VIOLAÇÃO: Longo if/elif/else chain
def _build_layer_core_mm(self):
    # ... 47 níveis de complexidade
    if type == "circle":
        # ...
    elif type == "rectangle":
        # ...
    elif type == "obround":
        # ...
    elif type == "polygon":
        # ...
    # + 40 linhas de condicionais
```

**Recomendação:**
```python
# ✅ Strategy Pattern

from abc import ABC, abstractmethod

class ApertureRenderer(ABC):
    @abstractmethod
    def render(self, params): pass

class CircleApertureRenderer(ApertureRenderer):
    def render(self, params):
        # Render circle
        pass

class RectangleApertureRenderer(ApertureRenderer):
    def render(self, params):
        # Render rectangle
        pass

class ObroundApertureRenderer(ApertureRenderer):
    def render(self, params):
        # Render obround
        pass

# Registry de renderers
RENDERERS = {
    'circle': CircleApertureRenderer(),
    'rectangle': RectangleApertureRenderer(),
    'obround': ObroundApertureRenderer(),
}

def _build_layer_core_mm(self, aperture_type, params):
    renderer = RENDERERS.get(aperture_type)
    if renderer:
        return renderer.render(params)
    raise ValueError(f"Unknown aperture type: {aperture_type}")
```

**Prioridade:** 🔴 HIGH
**Estimativa:** 2-3 dias

---

#### 2.2 `aoi_lib/gerber_core/gui/mainwindow.py` - Função `on_edit_many_objects()`
**Linha:** 924
**Complexidade:** 46
**Status:** 🔴 CRITICAL

```python
# ❌ VIOLAÇÃO: if/elif chain por tipo de objeto
def on_edit_many_objects(self):
    if obj_type == "circle":
        # Edita círculo
    elif obj_type == "rectangle":
        # Edita retângulo
    elif obj_type == "obround":
        # Edita obround
    # ... + 40 linhas
```

**Recomendação:**
```python
# ✅ Command Pattern + Strategy

class EditObjectCommand(ABC):
    @abstractmethod
    def execute(self, obj): pass

class EditCircleCommand(EditObjectCommand):
    def execute(self, circle): pass

class EditRectangleCommand(EditObjectCommand):
    def execute(self, rectangle): pass

# Factory
EDIT_COMMANDS = {
    'circle': EditCircleCommand(),
    'rectangle': EditRectangleCommand(),
}

def on_edit_many_objects(self, obj_type, changes):
    command = EDIT_COMMANDS.get(obj_type)
    if command:
        for obj in self.selected_objects:
            command.execute(obj)
```

**Prioridade:** 🔴 HIGH
**Estimativa:** 1-2 dias

---

### 🟠 Violações HIGH

#### 2.3 `aoi_lib/recipe_manager.py` - Função `validate()`
**Linha:** 321
**Complexidade:** 23
**Status:** 🟠 HIGH

```python
# ❌ VIOLAÇÃO: Validação com if/elif chain
def validate(self):
    if self.tension_config.ok_min < 0:
        raise ValidationError("ok_min must be positive")
    elif self.tension_config.ok_max > 50:
        raise ValidationError("ok_max too high")
    # ... + 20 linhas
```

**Recomendação:**
```python
# ✅ Chain of Responsibility

class ValidationRule(ABC):
    @abstractmethod
    def validate(self, config): pass

class TensionRangeRule(ValidationRule):
    def validate(self, config):
        if config.ok_min < 0:
            raise ValidationError("ok_min must be positive")

class TensionMaxRule(ValidationRule):
    def validate(self, config):
        if config.ok_max > 50:
            raise ValidationError("ok_max too high")

# Validator com regras encadeadas
class RecipeValidator:
    def __init__(self):
        self.rules = [
            TensionRangeRule(),
            TensionMaxRule(),
            # ... mais regras
        ]

    def validate(self, recipe):
        for rule in self.rules:
            rule.validate(recipe)
```

**Prioridade:** 🟡 MEDIUM
**Estimativa:** 1 dia

---

### 📊 Resumo de if/elif/else Chains

| Arquivo | Linha | Condicionais | Status |
|---------|-------|--------------|--------|
| `connection_coordinator.py` | 347 | 6 | 🟡 Médio |
| `wizard_state.py` | 95 | 6 | 🟡 Médio |
| `gerber_parser.py` | 276 | 5 | 🟡 Médio |
| `engineering_hardware_coordinator.py` | 78 | 5 | 🟡 Médio |
| `inspection_history_dialog.py` | 422 | 5 | 🟡 Médio |

---

## 3. LSP - Liskov Substitution Principle (Score: 85/100)

### 📋 Regra
Subtipos devem ser substituíveis por seus tipos base.

### ✅ Análise

**Total de Classes com Herança:** 143

**Boas Práticas Identificadas:**
- ✅ A maioria herda de classes PyQt6 (QDialog, QWidget, QThread)
- ✅ Enums herdam de `Enum` (padrão correto)
- ✅ Exceções customizadas herdam de `Exception` (padrão correto)

**Exemplos de Herança Adequada:**
```python
# ✅ BOM: Herança de widgets PyQt6
class FiducialAlignmentWidget(QWidget):
    # Estende QWidget corretamente

class TensionMeasurementThread(QThread):
    # Estende QThread corretamente

# ✅ BOM: Herança de exceções
class ValidationError(Exception):
    # Estende Exception corretamente

# ✅ BOM: Enums
class DefectType(Enum):
    OK = "OK"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"
```

### ⚠️ Possíveis Problemas

**Nota:** Não foram encontradas violações óbvias de LSP. A maioria das heranças segue os padrões corretos de PyQt6 e Python.

**Recomendação:**
- Revisar classes que herdam de outras classes customizadas (não PyQt6/built-in)
- Documentar contratos das classes base (métodos que devem ser sobrescritos)
- Adicionar testes de substituição (LSP tests)

**Prioridade:** 🟢 LOW
**Estimativa:** 1 dia (revisão + testes)

---

## 4. ISP - Interface Segregation Principle (Score: 70/100)

### 📋 Regra
Clients não devem depender de interfaces que não usam.

### 🔴 Violações CRÍTICAS (>20 métodos públicos)

#### 4.1 `AOIControllerApp` (MainWindow) - **46 métodos públicos**
**Status:** 🔴 CRITICAL

**Problema:** Interface muito grande, clients dependem de métodos que não usam.

**Análise dos Métodos:**
- Gerenciamento de abas (~10 métodos)
- Gerenciamento de menus (~8 métodos)
- Gerenciamento de hardware (~12 métodos)
- Gerenciamento de diálogos (~10 métodos)
- Utilitários diversos (~6 métodos)

**Recomendação:**
```python
# ✅ Separar em interfaces específicas:

class TabManager(ABC):
    @abstractmethod
    def add_tab(self, tab): pass

class MenuManager(ABC):
    @abstractmethod
    def add_menu_item(self, menu, action): pass

class HardwareManager(ABC):
    @abstractmethod
    def connect_plc(self): pass
    @abstractmethod
    def connect_camera(self): pass

class DialogManager(ABC):
    @abstractmethod
    def show_dialog(self, dialog_type): pass

# MainWindow implementa apenas interfaces necessárias
class MainWindow(TabManager, MenuManager, HardwareManager, DialogManager):
    # ...
```

**Prioridade:** 🟠 MEDIUM-HIGH
**Estimativa:** 3-4 dias
**Nota:** Esta é uma refatoração grande e pode quebrar muito código. Considerar fazer incrementalmente.

---

#### 4.2 `PLCAxisController` - **29 métodos públicos**
**Status:** 🟠 HIGH

**Problema:** Interface grande com responsabilidades misturadas.

**Categorização dos Métodos:**
- Conexão (2 métodos): `connect()`, `close()`
- Movimento absoluto (1 método): `move_absolute()`
- Movimento relativo (1 método): `move_relative()`
- Jog (4 métodos): `jog_start()`, `jog_stop()`, etc.
- Homing (2 métodos): `home_axis()`, `home_all()`
- Leitura (3 métodos): `read_position()`, `read_all_positions()`, etc.
- Configuração (5 métodos): `set_feed_limits()`, `set_pulses_per_mm()`, etc.
- Backlight (3 métodos): `backlight_on`, `backlight_off`, etc.
- Utilitários (8 métodos): `wait_for_idle()`, `is_axis_moving()`, etc.

**Recomendação:**
```python
# ✅ Separar em interfaces específicas:

class PLCConnection(ABC):
    @abstractmethod
    def connect(self): pass
    @abstractmethod
    def close(self): pass

class PLCAbsoluteMovement(ABC):
    @abstractmethod
    def move_absolute(self, axis, position, speed): pass

class PLCRelativeMovement(ABC):
    @abstractmethod
    def move_relative(self, axis, offset, speed): pass

class PLCJogMovement(ABC):
    @abstractmethod
    def jog_start(self, axis, direction, speed): pass
    @abstractmethod
    def jog_stop(self, axis): pass

class PLCHoming(ABC):
    @abstractmethod
    def home_axis(self, axis): pass
    @abstractmethod
    def home_all(self): pass

class PLCPositionReader(ABC):
    @abstractmethod
    def read_position(self, axis): pass

# PLCAxisController implementa todas
class PLCAxisController(PLCConnection, PLCAbsoluteMovement, ...):
    # ...

# Clients usam apenas interfaces necessárias
def move_to_position(movement: PLCAbsoluteMovement, x, y):
    movement.move_absolute('X', x)
    movement.move_absolute('Y', y)
```

**Prioridade:** 🟡 MEDIUM
**Estimativa:** 2-3 dias

---

#### 4.3 `StencilDatabase` - **21 métodos públicos**
**Status:** 🟠 HIGH

**Problema:** Interface mistura queries de diferentes domínios.

**Análise:**
- Queries de Stencil (5 métodos)
- Queries de Tensão (8 métodos)
- Queries de Inspeção (6 métodos)
- Utilitários (2 métodos)

**Recomendação:**
```python
# ✅ Interfaces segregadas por domínio:

class StencilRepository(ABC):
    @abstractmethod
    def save_stencil(self, stencil): pass
    @abstractmethod
    def find_stencil(self, code): pass

class TensionRepository(ABC):
    @abstractmethod
    def save_tension_record(self, record): pass
    @abstractmethod
    def get_tension_history(self, stencil_code): pass

class InspectionRepository(ABC):
    @abstractmethod
    def save_inspection(self, inspection): pass
    @abstractmethod
    def get_inspection_history(self, stencil_code): pass

# Implementação concreta implementa todas
class StencilDatabase(StencilRepository, TensionRepository, InspectionRepository):
    # ...

# Clients usam apenas repositórios necessários
class TensionService:
    def __init__(self, tension_repo: TensionRepository):
        self.tension_repo = tension_repo
```

**Nota:** Esta recomendação é a mesma da seção SRP. Resolver SRP aqui também resolve ISP.

**Prioridade:** 🟠 MEDIUM-HIGH
**Estimativa:** 3-4 dias

---

### 📊 Top 7 Classes com Mais Métodos Públicos

| Classe | Métodos | Arquivo | Prioridade |
|--------|---------|---------|------------|
| `AOIControllerApp` | 46 | `main_window.py` | 🔴 Critical |
| `PLCAxisController` | 29 | `plc_axis_controller.py` | 🟠 High |
| `StencilDatabase` | 21 | `stencil_database.py` | 🟠 High |
| `DialogRouter` | 20 | `dialog_router.py` | 🟡 Medium |
| `AOIConfigManager` | 18 | `config_manager.py` | 🟡 Medium |
| `GerberMacroViewer` | 17 | `mainwindow.py` (gerber_core) | 🟡 Medium |
| `ConnectionState` | 16 | `connection_coordinator.py` | 🟢 Low |

---

## 5. DIP - Dependency Inversion Principle (Score: 55/100)

### 📋 Regra
Dependa de abstrações, não de implementações concretas.

### 🔴 Violações CRÍTICAS

#### 5.1 `main_window.py` - **43 imports, todos concretos**
**Status:** 🔴 CRITICAL

**Problema:** MainWindow depende de 43 implementações concretas.

```python
# ❌ VIOLAÇÃO: Imports diretos de classes concretas
from consumo_lib.tabs.cnc_control_tab import CNCControlTab
from consumo_lib.tabs.tension_tab import TensionTab
from consumo_lib.tabs.inspection_tab import InspectionTab
from consumo_lib.coordinators.setup_coordinator import SetupCoordinator
from consumo_lib.managers.recipe_manager import RecipeManager
from consumo_lib.managers.stencil_manager import StencilManager
# ... + 36 imports
```

**Recomendação:**
```python
# ✅ Injeção de dependências + Factory Pattern

from abc import ABC

class TabFactory(ABC):
    @abstractmethod
    def create_cnc_tab(self, hardware) -> 'CNCControlTab': pass
    @abstractmethod
    def create_tension_tab(self, hardware) -> 'TensionTab': pass

class ManagerFactory(ABC):
    @abstractmethod
    def create_recipe_manager(self) -> 'RecipeManager': pass
    @abstractmethod
    def create_stencil_manager(self) -> 'StencilManager': pass

class MainWindow(QMainWindow):
    def __init__(self, tab_factory: TabFactory, manager_factory: ManagerFactory):
        self.tab_factory = tab_factory
        self.manager_factory = manager_factory

        # Usa factories em vez de criar diretamente
        self.cnc_tab = self.tab_factory.create_cnc_tab(self.hardware)
        self.recipe_manager = self.manager_factory.create_recipe_manager()
```

**Prioridade:** 🔴 HIGH
**Estimativa:** 5-7 dias
**Nota:** Esta é uma refatoração MUITO grande. Considerar fazer incrementalmente.

---

#### 5.2 `setup_coordinator.py` - **15 imports concretos**
**Status:** 🟠 HIGH

**Problema:** SetupCoordinator cria diretamente 47 instâncias de classes concretas.

```python
# ❌ VIOLAÇÃO: Criação direta de classes concretas
class SetupCoordinator:
    def __init__(self):
        self.recipe_manager = RecipeManager()  # Dependência concreta
        self.stencil_manager = StencilManager()  # Dependência concreta
        self.plc_controller = PLCAxisController()  # Dependência concreta
        self.camera_controller = CameraController()  # Dependência concreta
        # ... + 43 instanciações
```

**Recomendação:**
```python
# ✅ Injeção de dependências via construtor

class SetupCoordinator:
    def __init__(
        self,
        recipe_manager: RecipeManager,
        stencil_manager: StencilManager,
        plc_controller: PLCAxisController,
        camera_controller: CameraController,
        # ... outras dependências
    ):
        self.recipe_manager = recipe_manager
        self.stencil_manager = stencil_manager
        self.plc_controller = plc_controller
        self.camera_controller = camera_controller

# Factory para criar SetupCoordinator com todas as dependências
class CoordinatorFactory:
    def create_setup_coordinator(self) -> SetupCoordinator:
        return SetupCoordinator(
            recipe_manager=self.create_recipe_manager(),
            stencil_manager=self.create_stencil_manager(),
            plc_controller=self.create_plc_controller(),
            camera_controller=self.create_camera_controller(),
        )
```

**Prioridade:** 🟠 MEDIUM-HIGH
**Estimativa:** 3-4 dias

---

#### 5.3 `plc_axis_controller.py` - **67 instanciações diretas**
**Status:** 🟡 MEDIUM

**Problema:** PLCAxisController depende diretamente de `ModbusTcpClient` (classe concreta).

```python
# ❌ VIOLAÇÃO: Import direto de classe concreta
from pymodbus.client import ModbusTcpClient

class PLCAxisController:
    def __init__(self, host: str, port: int):
        self.client = ModbusTcpClient(host, port=port)  # Dependência concreta
```

**Recomendação:**
```python
# ✅ Abstração para cliente Modbus

from abc import ABC, abstractmethod

class ModbusClient(ABC):
    @abstractmethod
    def connect(self) -> bool: pass
    @abstractmethod
    def close(self): pass
    @abstractmethod
    def read_coils(self, address, count): pass
    @abstractmethod
    def write_coil(self, address, value): pass

class PymodbusTcpClient(ModbusClient):
    def __init__(self, host, port):
        self.client = pymodbus.client.ModbusTcpClient(host, port=port)

    def connect(self) -> bool:
        return self.client.connect()

    # ... delega para self.client

class PLCAxisController:
    def __init__(self, modbus_client: ModbusClient):
        self.modbus_client = modbus_client  # Dependência abstrata

# Factory para criar PLCAxisController
class PLCFactory:
    def create_plc_controller(self, host, port) -> PLCAxisController:
        modbus_client = PymodbusTcpClient(host, port)
        return PLCAxisController(modbus_client)
```

**Prioridade:** 🟡 MEDIUM
**Estimativa:** 2 dias

---

### 📊 Top 3 Arquivos com Maior Acoplamento

| Arquivo | Imports Concretos | Instanciações | Prioridade |
|---------|------------------|---------------|------------|
| `main_window.py` | 43 | 26 | 🔴 Critical |
| `setup_coordinator.py` | 15 | 47 | 🟠 High |
| `plc_axis_controller.py` | 3 | 67 | 🟡 Medium |

---

## 6. Métricas de Qualidade

### 6.1 Complexidade Ciclomática

| Faixa | Quantidade | Status |
|-------|-----------|--------|
| **1-10** (Baixa) | ~95% | ✅ Excelente |
| **11-20** (Média) | ~4% | ⚠️ Aceitável |
| **21-50** (Alta) | ~1% | 🟠 Preocupante |
| **50+** (Muito Alta) | 0 | ✅ Bom |

**Top 10 Funções Mais Complexas:**

1. `_build_layer_core_mm()` (gerber_core/parser.py) - **47** 🔴
2. `on_edit_many_objects()` (gerber_core/gui/mainwindow.py) - **46** 🔴
3. `on_edit_object()` (gerber_core/gui/mainwindow.py) - **27** 🟠
4. `validate()` (recipe_manager.py) - **23** 🟠
5. `validate_dependencies()` (wizard_state.py) - **20** 🟡
6. `get_validation_message()` (wizard_state.py) - **18** 🟡
7. `parse_gcode()` (gcode_manager.py) - **19** 🟡
8. `apply_filters()` (inspection_history_dialog.py) - **19** 🟡
9. `wait_for_idle()` (plc_axis_controller.py) - **18** 🟡
10. `compare()` (stencil_inspection.py) - **18** 🟡

---

### 6.2 Acoplamento de Módulos

**Total de Módulos Analisados:** 171
**Módulos com Alto Acoplamento (>15 dependências):** 1

**Top 15 Módulos Mais Acoplados:**

1. `consumo_lib.dialogs.__init__` - **17 dependências** 🟠

**Análise:**
- ✅ **Excelente:** Apenas 1 módulo com alto acoplamento
- ✅ **Muito bom:** Baixo acoplamento geral entre módulos
- ✅ **Arquitetura limpa:** Separação adequada de responsabilidades

**Nota:** O alto acoplamento em `consumo_lib.dialogs.__init__` é esperado (arquivo de exportação/importação de todos os diálogos).

---

### 6.3 Tamanho de Arquivos

**Total de Arquivos Python:** 184

| Faixa de Tamanho | Quantidade | Percentual | Status |
|-----------------|-----------|------------|--------|
| **<300 linhas** | 145 | 78.8% | ✅ Excelente |
| **300-500 linhas** | 13 | 7.1% | ✅ Bom |
| **500-1000 linhas** | 23 | 12.5% | ⚠️ Aceitável |
| **>1000 linhas** | 3 | 1.6% | 🔴 Crítico |

**Arquivos >1000 linhas:**
1. `aoi_lib/stencil_tension_old.py` - 1,409 linhas (JÁ ARQUIVADO)
2. `aoi_lib/gerber_core/gui/mainwindow.py` - 1,384 linhas
3. `aoi_lib/report_generator.py` - 1,366 linhas

**Arquivos 500-1000 linhas (32 arquivos):**
- `consumo_lib/widgets/engenharia/alignment_widget.py` - 1,179
- `aoi_lib/fiducial_alignment_widget.py` - 959
- `aoi_lib/stencil_database.py` - 914
- `consumo_lib/widgets/engenharia/inspection_windows_widget.py` - 886
- `consumo_lib/dialogs/recipe_dialogs.py` - 881
- `aoi_lib/recipe_dialog.py` - 880
- `consumo_lib/dialogs/defect_judgment_dialog.py` - 848
- `aoi_lib/stencil_tracker.py` - 848
- `consumo_lib/widgets/engenharia/mosaic_capture_widget.py` - 790
- `aoi_lib/stencil_inspection.py` - 784
- `aoi_lib/plc_axis_controller.py` - 738
- `consumo_lib/widgets/engenharia/fiducial_capture_widget.py` - 696
- `aoi_lib/fiducial_alignment.py` - 692
- `consumo_lib/controllers/camera_settings_controller.py` - 679
- `consumo_lib/dialogs/engineering_wizard_dialog.py` - 654
- `consumo_lib/controllers/inspection_ui_controller.py` - 651
- `consumo_lib/main_window.py` - 650
- `aoi_lib/recipe_manager.py` - 642
- `aoi_lib/gerber_parser.py` - 616
- `consumo_lib/controllers/map_controller.py` - 602
- `consumo_lib/coordinators/setup_coordinator.py` - 601
- `consumo_lib/widgets/engenharia/gerber_upload_widget.py` - 591
- `consumo_lib/coordinators/tension_coordinator.py` - 579
- `consumo_lib/widgets/tension_viz.py` - 577
- `consumo_lib/coordinators/engineering_hardware_coordinator.py` - 559
- `consumo_lib/controllers/sequence_controller.py` - 558
- `consumo_lib/services/movement_service.py` - 542
- `aoi_lib/stencil_inspector.py` - 540
- `consumo_lib/models/engineering/program_config.py` - 521
- `consumo_lib/handlers/dialog_router.py` - 515
- `consumo_lib/handlers/menu_handler.py` - 501
- `consumo_lib/controllers/calibration_controller.py` - 501

**Análise:**
- ✅ **78.8%** dos arquivos estão abaixo de 300 linhas (Excelente)
- ⚠️ **14.1%** dos arquivos estão acima de 500 linhas (Atenção necessária)
- 🔴 **1.6%** dos arquivos estão acima de 1000 linhas (Crítico)

---

### 6.4 Duplicação de Código

**Nota:** Análise de duplicação requer ferramentas especializadas (ex: `pycode_similarity`, `jscpd`). Não foi realizada nesta análise manual.

**Recomendação:** Executar análise de duplicação com:
```bash
pip install pycode_similarity
pycode_similarity aoi_lib/ consumo_lib/
```

---

## 7. Roadmap de Refatoração

### Fase 1: Críticos (Semana 1-2) 🔴

#### 1.1 Refatorar `gerber_core/gui/mainwindow.py` (1,384 linhas)
**Prioridade:** 🔴 CRITICAL
**Violações:** SRP, OCP, ISP
**Estimativa:** 5-7 dias
**Ações:**
- [ ] Extrair `GerberController` para lógica de negócio
- [ ] Extrair `GerberModel` para dados
- [ ] Extrair `GerberCommand` para ações (padrão Command)
- [ ] Reduzir complexidade de `on_edit_many_objects()` (46 → <15)
- [ ] Reduzir complexidade de `on_edit_object()` (27 → <15)

**Entregáveis:**
- `gerber_core/controllers/gerber_controller.py`
- `gerber_core/models/gerber_model.py`
- `gerber_core/commands/edit_commands.py`
- `gerber_core/gui/mainwindow.py` (<500 linhas)

---

#### 1.2 Refatorar `gerber_core/parser.py` - Função `_build_layer_core_mm()`
**Prioridade:** 🔴 CRITICAL
**Violações:** OCP
**Estimativa:** 2-3 dias
**Ações:**
- [ ] Implementar Strategy Pattern para renderizadores de aperture
- [ ] Criar `ApertureRenderer` (ABC)
- [ ] Criar renderizadores concretos (Circle, Rectangle, Obround, etc.)
- [ ] Reduzir complexidade de 47 → <15

**Entregáveis:**
- `gerber_core/renderers/aperture_renderer.py` (ABC)
- `gerber_core/renderers/circle_renderer.py`
- `gerber_core/renderers/rectangle_renderer.py`
- `gerber_core/renderers/obround_renderer.py`
- `gerber_core/parser.py` (refatorado)

---

#### 1.3 Refatorar `stencil_database.py` (914 linhas)
**Prioridade:** 🟠 HIGH
**Violações:** SRP, ISP, DIP
**Estimativa:** 3-4 dias
**Ações:**
- [ ] Extrair interfaces de repositórios (ABC)
- [ ] Criar `StencilRepository`, `TensionRepository`, `InspectionRepository`
- [ ] Criar `JsonToSqliteMigrator` (separado)
- [ ] Reduzir métodos públicos de 21 → <10 por classe

**Entregáveis:**
- `aoi_lib/database/repositories/stencil_repository.py`
- `aoi_lib/database/repositories/tension_repository.py`
- `aoi_lib/database/repositories/inspection_repository.py`
- `aoi_lib/database/migrators/json_to_sqlite_migrator.py`

---

### Fase 2: Alta Prioridade (Semana 3-4) 🟠

#### 2.1 Refatorar `alignment_widget.py` (1,179 linhas)
**Prioridade:** 🟠 HIGH
**Violações:** SRP
**Estimativa:** 2-3 dias
**Ações:**
- [ ] Extrair `FiducialAlignmentService`
- [ ] Extrair `TemplateMatchingService`
- [ ] Extrair `AlignmentState` (separado de wizard_state.py)

**Entregáveis:**
- `consumo_lib/services/fiducial_alignment_service.py`
- `consumo_lib/services/template_matching_service.py`
- `consumo_lib/models/alignment_state.py`

---

#### 2.2 Refatorar `main_window.py` (650 linhas, 46 métodos)
**Prioridade:** 🟠 HIGH
**Violações:** SRP, ISP, DIP
**Estimativa:** 5-7 dias
**Ações:**
- [ ] Extrair interfaces (`TabManager`, `MenuManager`, etc.)
- [ ] Implementar Factory Pattern para criação de componentes
- [ ] Reduzir métodos públicos de 46 → <20
- [ ] Injetar dependências via construtor

**Entregáveis:**
- `consumo_lib/factories/tab_factory.py`
- `consumo_lib/factories/manager_factory.py`
- `consumo_lib/interfaces/tab_manager.py` (ABC)
- `consumo_lib/interfaces/menu_manager.py` (ABC)
- `consumo_lib/main_window.py` (refatorado)

---

#### 2.3 Refatorar `plc_axis_controller.py` (738 linhas, 29 métodos)
**Prioridade:** 🟡 MEDIUM
**Violações:** SRP, ISP, DIP
**Estimativa:** 2-3 dias
**Ações:**
- [ ] Criar abstração `ModbusClient` (ABC)
- [ ] Implementar `PymodbusTcpClient` (adaptação)
- [ ] Segregar interfaces (`PLCAbsoluteMovement`, `PLCJogMovement`, etc.)
- [ ] Reduzir métodos públicos de 29 → <15

**Entregáveis:**
- `aoi_lib/modbus/modbus_client.py` (ABC)
- `aoi_lib/modbus/pymodbus_tcp_client.py`
- `aoi_lib/plc/interfaces/plc_absolute_movement.py` (ABC)
- `aoi_lib/plc/interfaces/plc_jog_movement.py` (ABC)
- `aoi_lib/plc_axis_controller.py` (refatorado)

---

### Fase 3: Média Prioridade (Mês 2) 🟡

#### 3.1 Refatorar `report_generator.py` (1,366 linhas)
**Prioridade:** 🟡 MEDIUM
**Violações:** SRP (parcial)
**Estimativa:** 2-3 dias
**Ações:**
- [ ] Extrair `ReportLayout` (layout de páginas)
- [ ] Extrair `ChartGenerator` (gráficos Matplotlib)
- [ ] Reduzir tamanho dos builders (~400 → ~200 linhas cada)

**Entregáveis:**
- `report_generator/layout/report_layout.py`
- `report_generator/charts/chart_generator.py`
- `report_generator/builders/tension_builder.py` (refatorado)
- `report_generator/builders/stencil_history_builder.py` (refatorado)

---

#### 3.2 Refatorar `recipe_dialogs.py` (881 linhas)
**Prioridade:** 🟡 MEDIUM
**Violações:** SRP
**Estimativa:** 1 dia
**Ações:**
- [ ] Separar 3 diálogos em arquivos distintos

**Entregáveis:**
- `consumo_lib/dialogs/recipe/recipe_list_dialog.py`
- `consumo_lib/dialogs/recipe/recipe_edit_dialog.py`
- `consumo_lib/dialogs/recipe/recipe_manager_dialog.py`

---

#### 3.3 Refatorar `setup_coordinator.py` (601 linhas)
**Prioridade:** 🟡 MEDIUM
**Violações:** DIP
**Estimativa:** 3-4 dias
**Ações:**
- [ ] Injetar dependências via construtor
- [ ] Criar `CoordinatorFactory`

**Entregáveis:**
- `consumo_lib/factories/coordinator_factory.py`
- `consumo_lib/coordinators/setup_coordinator.py` (refatorado)

---

### Fase 4: Melhorias Contínuas (Ongoing) 🟢

#### 4.1 Reduzir Complexidade de Funções
**Prioridade:** 🟡 MEDIUM
**Estimativa:** 1-2 dias
**Ações:**
- [ ] `validate()` (recipe_manager.py) - 23 → <15
- [ ] `validate_dependencies()` (wizard_state.py) - 20 → <15
- [ ] `parse_gcode()` (gcode_manager.py) - 19 → <15
- [ ] `apply_filters()` (inspection_history_dialog.py) - 19 → <15
- [ ] `wait_for_idle()` (plc_axis_controller.py) - 18 → <15
- [ ] `compare()` (stencil_inspection.py) - 18 → <15

---

#### 4.2 Implementar Testes LSP
**Prioridade:** 🟢 LOW
**Estimativa:** 1 dia
**Ações:**
- [ ] Criar testes de substituição para classes com herança
- [ ] Documentar contratos de classes base

---

#### 4.3 Análise de Duplicação de Código
**Prioridade:** 🟢 LOW
**Estimativa:** 1 dia
**Ações:**
- [ ] Executar `pycode_similarity`
- [ ] Extrair código duplicado para funções/módulos compartilhados

---

## 8. Próximos Passos Imediatos

### Hoje / Amanhã

1. ✅ **COMPLETO:** Análise SOLID completa
2. 🔄 **EM PROGRESSO:** Revisão deste relatório
3. 📋 **PRÓXIMO:** Priorizar tarefas com o time

### Esta Semana

1. 🔴 Iniciar Fase 1: Refatoração de `gerber_core/gui/mainwindow.py`
2. 🔴 Iniciar refatoração de `gerber_core/parser.py`
3. 📊 Apresentar este relatório ao time

### Próximas 2 Semanas

1. 🔴 Completar Fase 1 (Críticos)
2. 🟠 Iniciar Fase 2 (Alta Prioridade)
3. ✅ Criar testes unitários para código refatorado

---

## 9. Recomendações Gerais

### 9.1 Boas Práticas Identificadas

✅ **Arquitetura Modular:**
- Separação clara entre `aoi_lib` (business logic) e `consumo_lib` (UI)
- Estrutura de pacotes bem organizada (tabs, widgets, dialogs, services)

✅ **SOLID Phase 1:**
- Refatoração bem-sucedida de `stencil_tension.py` (1,409 → 5 módulos)
- 48 unit tests criados (100% service layer coverage)
- Zero breaking changes

✅ **Testes Unitários:**
- 48 testes para tensiometro
- 122 testes para Engineering Wizard
- 462 testes passing (97.7% pass rate)

✅ **Baixo Acoplamento:**
- Apenas 1 módulo com >15 dependências
- Arquitetura limpa entre módulos

---

### 9.2 Áreas de Melhoria

⚠️ **SRP (Single Responsibility):**
- 3 arquivos >1000 linhas (1 já arquivado)
- 32 arquivos >500 linhas
- Muitas classes com múltiplas responsabilidades

⚠️ **OCP (Open/Closed):**
- Longas chains if/elif/else (6 condicionais em alguns casos)
- Complexidade ciclomática alta em algumas funções (47)

⚠️ **ISP (Interface Segregation):**
- 7 classes com >15 métodos públicos
- Interfaces muito grandes (ex: `AOIControllerApp` com 46 métodos)

⚠️ **DIP (Dependency Inversion):**
- Alto acoplamento a classes concretas
- `main_window.py` com 43 imports concretos
- `setup_coordinator.py` com 47 instanciações diretas

---

### 9.3 Metas de Qualidade

**Curto Prazo (1 mês):**
- [ ] Eliminar todos os arquivos >1000 linhas
- [ ] Reduzir complexidade ciclomática >20 para <15
- [ ] Implementar interfaces segregadas para classes com >20 métodos

**Médio Prazo (3 meses):**
- [ ] Manter todos os arquivos <500 linhas
- [ ] Reduzir complexidade ciclomática >15 para <10
- [ ] Implementar injeção de dependências em módulos principais

**Longo Prazo (6 meses):**
- [ ] Score SOLID global >85/100
- [ ] 100% de cobertura de testes
- [ ] Zero violações CRÍTICAS

---

## 10. Referências

### Documentação do Projeto
- `CLAUDE.md` - Contexto do projeto para Claude Code
- `PROJECT_ORGANIZATION_GUIDELINES.md` - Padrões de organização
- `docs/guides/SOLID_PHASE1_MIGRATION_GUIDE.md` - Guia de migração fase 1
- `docs/reports/SOLID_ANALYSIS_REPORT.md` - Análise SOLID anterior (2026-01-14)
- `conductor/RELATORIO_IMPLEMENTACAO_ABAS_1-4.md` - Implementação Engineering Wizard

### Tracks do Conductor
- `solid_refactoring_phase1_20260114` (COMPLETO)
- `refactor_large_files_20260113` (COMPLETO)
- `integrate_engineering_wizard_20260113` (COMPLETO)

### Literatura
- [Clean Code by Robert C. Martin](https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/dp/0132350882)
- [Clean Architecture by Robert C. Martin](https://www.amazon.com/Clean-Architecture-Craftsmans-Software-Structure/dp/0134494164)
- [SOLID Principles Wikipedia](https://en.wikipedia.org/wiki/SOLID)
- [Python Design Patterns](https://refactoring.guru/design-patterns/python)

---

## 11. Apêndice

### 11.1 Metodologia de Análise

**Ferramentas Utilizadas:**
- AST (Abstract Syntax Tree) do Python para análise estática
- Contagem de linhas de código (LOC)
- Análise de complexidade ciclomática (McCabe)
- Inspeção manual de violações SOLID

**Limitações:**
- Análise estática (sem execução de código)
- Não inclui análise de duplicação de código (requer ferramenta especializada)
- Não inclui análise de coverage de testes

**Cobertura:**
- 171 módulos Python analisados
- 220 classes analisadas
- 184 arquivos Python totais

---

### 11.2 Glossário

- **SRP:** Single Responsibility Principle (Princípio da Responsabilidade Única)
- **OCP:** Open/Closed Principle (Princípio Aberto/Fechado)
- **LSP:** Liskov Substitution Principle (Princípio da Substituição de Liskov)
- **ISP:** Interface Segregation Principle (Princípio da Segregação de Interface)
- **DIP:** Dependency Inversion Principle (Princípio da Inversão de Dependência)
- **AST:** Abstract Syntax Tree (Árvore Sintática Abstrata)
- **LOC:** Lines of Code (Linhas de Código)
- **ABC:** Abstract Base Class (Classe Base Abstrata)

---

**Fim do Relatório**

**Gerado:** 2026-01-14
**Próxima Revisão:** 2026-02-14 (após Fase 1 do roadmap)
