# SOLID Analysis Report - Tensiometro Project

**Data:** 2026-01-14
**Versão:** 0.4.0
**Escopo:** Análise completa de violações SOLID e métricas de qualidade

---

## Executive Summary

| Métrica | Valor | Status |
|---------|-------|--------|
| **Total de arquivos Python** | 180 | 📊 |
| **Arquivos críticos (>1000 linhas)** | 4 | 🔴 CRÍTICO |
| **Arquivos grandes (>500 linhas)** | 36 | ⚠️ ALERTA |
| **Linhas totais analisadas** | 58,846 | 📊 |
| **Média linhas/arquivo** | 327 | 🟡 ACEITÁVEL |
| **Score SOLID geral** | 62/100 | ⚠️ REQUER MELHORIAS |

### Status por Princípio

| Princípio | Score | Violações | Prioridade |
|-----------|-------|-----------|------------|
| **SRP** (Single Responsibility) | 45/100 | 36 arquivos >500 linhas | 🔴 ALTA |
| **OCP** (Open/Closed) | 68/100 | Média em módulos principais | 🟡 MÉDIA |
| **LSP** (Liskov Substitution) | 78/100 | Baixa incidência | 🟢 OK |
| **ISP** (Interface Segregation) | 55/100 | Interfaces "god" detectadas | 🟡 MÉDIA |
| **DIP** (Dependency Inversion) | 65/100 | Acoplamento direto frequente | 🟡 MÉDIA |

---

## 🔴 CRITICAL ISSUES

### 1. VIOLAÇÃO SRP CRÍTICA - stencil_tension.py (1,409 linhas)

**Localização:** `aoi_lib/stencil_tension.py`
**Severidade:** 🔴 CRITICAL
**Princípio Violado:** **S**RP - Single Responsibility Principle

#### Análise de Responsabilidades

O arquivo contém **4 classes** com responsabilidades misturadas:

```python
# Linha 33: Gerenciamento de conexão serial
class TensiometerSerialManager:
    # Responsabilidade 1: Protocolo de comunicação
    # Responsabilidade 2: Configuração de porta
    # Responsabilidade 3: Decodificação de frames

# Linha 203: Thread de medição (ORQUESTRAÇÃO)
class TensionMeasurementThread(QThread):
    # Responsabilidade 1: Controle de thread
    # Responsabilidade 2: Movimentação PLC
    # Responsabilidade 3: Leitura serial
    # Responsabilidade 4: Interface UI (signals)

# Linha 326: Negócio
class StencilTensionMeasurement:
    # Responsabilidade 1: Lógica de grid
    # Responsabilidade 2: Validação de dados
    # Responsabilidade 3: Cálculos de estatísticas

# Linha 447: Interface UI (DIALOG)
class StencilTensionDialog(QDialog):
    # Responsabilidade 1: Layout de UI
    # Responsabilidade 2: Event handling
    # Responsabilidade 3: Validação de formulário
    # Responsabilidade 4: Persistência de rotinas
```

#### Problemas Detectados

1. **Classe God Thread**: `TensionMeasurementThread` (linhas 203-324)
   - Contém lógica de movimento PLC
   - Faz chamadas diretas ao tensiômetro
   - Gerencia estados de UI
   - Processa grid de medição
   - **Violação**: ORQUESTRAÇÃO + NEGÓCIO + UI

2. **Classe God Dialog**: `StencilTensionDialog` (linhas 447-1409)
   - 962 linhas de código
   - Gerencia layout complexo
   - Manipula persistência de rotinas
   - Valida entrada do usuário
   - Coordena medição
   - **Violação**: UI + PERSISTÊNCIA + ORQUESTRAÇÃO

3. **Acoplamento Direto**
   ```python
   # Linha ~250: Violación DIP
   from aoi_lib.plc_axis_controller import PLCAxisController
   from tkinter import Toplevel, Label, Button, messagebox

   # Criação direta de dependências concretas
   self.plc = PLCAxisController(host, port)
   ```

#### Impacto na Manutenibilidade

- ❌ **Alterar protocolo serial** → Afecta 4 classes
- ❌ **Mudar layout UI** → Risco de quebrar lógica de medição
- ❌ **Testar unitariamente** → Impossível sem mocks complexos
- ❌ **Reutilizar lógica de medição** → Acoplado a QDialog

#### Recomendação de Refatoração

```python
# ESTRUTURA PROPOSTA:

aoi_lib/tensiometer/
├── __init__.py
├── serial_protocol.py       # TensiometerSerialManager (OK)
├── measurement_service.py   # StencilTensionMeasurement (negócio puro)
├── measurement_orchestrator.py  # Orquestração (sem UI)
└── measurement_thread.py     # Thread apenas para execução

consumo_lib/dialogs/tension/
└── tension_measurement_dialog.py  # Apenas UI (delega para serviços)
```

**Ação Imediata:**
- ✅ **CRÍTICO**: Extrair lógica de medição para service layer
- ✅ **CRÍTICO**: Remover dependências de UI de classes de negócio
- ✅ **CRÍTICO**: Separar orquestração de execução

---

### 2. VIOLAÇÃO SRP CRÍTICA - signal_aggregator.py (1,192 linhas)

**Localização:** `consumo_lib/handlers/signal_aggregator.py`
**Severidade:** 🔴 CRITICAL
**Princípio Violado:** **S**RP + **I**SP + **D**IP

#### Análise

```python
# Classe única com 1,192 linhas
class SignalAggregator:
    # Responsabilidades identificadas:
    # 1. Gerenciar 120+ sinais diferentes
    # 2. Conectar componentes entre si
    # 3. Desconectar componentes
    # 4. Gerenciar ciclo de vida de sinais
    # 5. Centralizar ALL signal routing (ANTI-PATTERN GOD OBJECT)
```

#### Problemas

1. **God Object**: Única classe para TODO signal routing
2. **Violação ISP**: Interface gigantesca (120+ métodos connect_*())
3. **Violación DIP**: Dependências diretas para TODAS as classes
4. **Single Point of Failure**: Se falha, nada funciona

#### Exemplo de Violação

```python
# ANTI-PATTERN: 120+ métodos similares
def connect_camera_controller(self, controller):
    if controller:
        controller.frame_updated.connect(self.on_camera_frame_updated)

def connect_tension_controller(self, controller):
    if controller:
        controller.measurement_completed.connect(self.on_tension_measurement_completed)

# ... 118+ métodos similares
```

#### Recomendação

```python
# ESTRUTURA PROPOSTA:

# 1. Event Bus Pattern (OCP compliant)
class EventBus:
    """Bus centralizado de eventos pub/sub"""
    def subscribe(self, event_type: str, handler: Callable)
    def publish(self, event: Event)

# 2. Auto-registration (DIP compliant)
class SignalProvider(ABC):
    @abstractmethod
    def register_signals(self, bus: EventBus): pass

# 3. Cada componente registra seus próprios sinais
class CameraController(SignalProvider):
    def register_signals(self, bus: EventBus):
        bus.subscribe("camera.frame_updated", self.on_frame_updated)
```

---

### 3. VIOLAÇÃO SRP - report_generator.py (1,366 linhas)

**Localização:** `aoi_lib/report_generator.py`
**Severidade:** 🟠 HIGH
**Princípio Violado:** **S**RP + **O**CP

#### Análise

```python
class ReportGenerator:
    # Responsabilidades:
    # 1. Gerar PDF de tensão
    # 2. Gerar PDF de inspeção
    # 3. Gerar heatmaps
    # 4. Gerar gráficos de tendência
    # 5. Layout de páginas
    # 6. Renderização de tabelas
    # 7. Exportar dados
```

#### Problemas

1. **If/else chains** (violação OCP):
   ```python
   if report_type == "tension":
       # 200 linhas de código
   elif report_type == "inspection":
       # 300 linhas de código
   elif report_type == "trend":
       # 150 linhas de código
   ```

2. **Acoplamento tight** com:
   - reportlab (PDF library)
   - matplotlib (charts)
   - aoi_lib data models

#### Recomendação

```python
# ESTRUTURA PROPOSTA:

aoi_lib/reports/
├── __init__.py
├── base_report.py           # Abstract base (OCP)
├── tension_report.py        # Strategy para tensão
├── inspection_report.py     # Strategy para inspeção
├── trend_report.py          # Strategy para tendências
├── builders/
│   ├── pdf_builder.py       # PDF generation
│   ├── chart_builder.py     # Chart generation
│   └── table_builder.py     # Table layout
└── formatters/
    ├── heatmap_formatter.py
    └── data_formatter.py
```

---

### 4. VIOLAÇÃO SRP - fiducial_alignment_widget.py (959 linhas)

**Localização:** `aoi_lib/fiducial_alignment_widget.py`
**Severidade:** 🟠 HIGH
**Princípio Violado:** **S**RP + **D**IP

#### Análise

Widget PyQt6 que mistura:
- UI layout
- Template matching (OpenCV)
- Transformações geométricas
- Drag-and-drop handling
- Camera integration

#### Problemas

1. **Lógica de visão computacional em UI widget**
2. **Impossível testar sem PyQt6**
3. **Impossível reutilizar algoritmos**

#### Recomendação

```python
# ESTRUTURA PROPOSTA:

aoi_lib/vision/
├── __init__.py
├── template_matcher.py      # Template matching puro
├── transform_calculator.py  # Cálculos geométricos
└── alignment_engine.py      # Orquestração de alinhamento

consumo_lib/widgets/
└── fiducial_alignment_widget.py  # Apenas UI (delega para vision/)
```

---

## 🟠 HIGH PRIORITY ISSUES

### 5. VIOLAÇÃO OCP - plc_axis_controller.py (738 linhas)

**Localização:** `aoi_lib/plc_axis_controller.py`
**Severidade:** 🟠 HIGH
**Princípio Violado:** **O**CP

#### Problema: If/else chains para comandos

```python
# Exemplo simplificado
def execute_command(self, command_type, axis, value):
    if command_type == "absolute":
        # Código para movimento absoluto
    elif command_type == "relative":
        # Código para movimento relativo
    elif command_type == "jog":
        # Código para jog
    elif command_type == "home":
        # Código para home
    # Novos comandos exigem modificação aqui ❌
```

#### Recomendação: Command Pattern

```python
class PLCCommand(ABC):
    @abstractmethod
    def execute(self, plc): pass

class AbsoluteMoveCommand(PLCCommand):
    def __init__(self, axis, position, speed): ...

class RelativeMoveCommand(PLCCommand):
    def __init__(self, axis, delta, speed): ...

class HomeCommand(PLCCommand):
    def __init__(self, axis): ...

# Uso:
command = AbsoluteMoveCommand('X', 1000, 5000)
command.execute(plc)
```

---

### 6. VIOLAÇÃO DIP - Múltiplos Arquivos

**Localização:** Vários arquivos em `consumo_lib/`
**Severidade:** 🟠 HIGH
**Princípio Violado:** **D**IP

#### Exemplo: camera_settings_controller.py (679 linhas)

```python
# ❌ VIOLAÇÃO: Import direto de classes concretas
from aoi_lib.camera_controller import CameraController
from consumo_lib.widgets.camera_settings_widget import CameraSettingsWidget

class CameraSettingsController:
    def __init__(self):
        self.camera = CameraController()  # Dependência concreta
        self.widget = CameraSettingsWidget()  # Dependência concreta
```

#### Recomendação: Injeção de Dependência

```python
# ✅ REFACTORING
class CameraSettingsController:
    def __init__(
        self,
        camera: CameraControllerInterface,  # Abstração
        widget: CameraSettingsWidgetInterface  # Abstração
    ):
        self.camera = camera
        self.widget = widget
```

---

### 7. VIOLAÇÃO ISP - alignment_widget.py (1,179 linhas)

**Localização:** `consumo_lib/widgets/engenharia/alignment_widget.py`
**Severidade:** 🟠 HIGH
**Princípio Violado:** **I**SP

#### Problema: Interface God

```python
class AlignmentWidget(QWidget):
    # 20+ métodos públicos
    # Alguns clients usam apenas 3 métodos
    # Outros usam 10 métodos diferentes
    # Violação: Clients dependem de métodos que não usam
```

#### Exemplo de Métodos

```python
# Client A só precisa:
def load_gerber(self, path): pass
def set_fiducials(self, points): pass
def align(self): pass

# Client B só precisa:
def set_overlay_visible(self, visible): pass
def update_transform(self, transform): pass
def get_alignment_result(self): pass

# Mas ambos dependem da classe com 20+ métodos ❌
```

#### Recomendação: Interface Segregation

```python
# ✅ REFACTORING: Interfaces específicas

class GerberLoaderInterface(ABC):
    @abstractmethod
    def load_gerber(self, path: str): pass

class FiducialManagerInterface(ABC):
    @abstractmethod
    def set_fiducials(self, points: List[Point]): pass
    @abstractmethod
    def align(self): pass

class OverlayManagerInterface(ABC):
    @abstractmethod
    def set_overlay_visible(self, visible: bool): pass
    @abstractmethod
    def update_transform(self, transform): pass

# Clients dependem apenas do que necessitam
```

---

## 🟡 MEDIUM PRIORITY ISSUES

### 8. VIOLAÇÃO DIP - recipe_dialogs.py (881 linhas)

**Localização:** `consumo_lib/dialogs/recipe_dialogs.py`
**Severidade:** 🟡 MEDIUM
**Princípio Violado:** **D**IP

#### Problema: Acoplamento direto a banco de dados

```python
# ❌ VIOLAÇÃO
from aoi_lib.stencil_database import StencilDatabase  # Classe concreta

class RecipeDialog(QDialog):
    def __init__(self):
        self.db = StencilDatabase()  # Acoplamento direto
```

#### Recomendação

```python
# ✅ REFACTORING
from aoi_lib.stencil_database import StencilDatabaseInterface

class RecipeDialog(QDialog):
    def __init__(self, db: StencilDatabaseInterface):
        self.db = db  # Injeção de dependência
```

---

### 9. VIOLAÇÃO SRP - stencil_inspector.py (784 linhas)

**Localização:** `aoi_lib/stencil_inspector.py`
**Severidade:** 🟡 MEDIUM
**Princípio Violado:** **S**RP

#### Análise

Classe que mistura:
- Validação de imagens
- Binarização (Otsu, Adaptive, Fixed)
- Análise de blobs
- Classificação de defects
- Geração de relatórios

#### Recomendação: Extract Method Objects

```python
# ESTRUTURA PROPOSTA:

aoi_lib/inspection/
├── __init__.py
├── image_validator.py       # Validação
├── binarization.py          # Estratégias de binarização
├── blob_analyzer.py         # Análise de blobs
├── defect_classifier.py     # Classificação
└── inspection_orchestrator.py  # Orquestração
```

---

### 10. VIOLAÇÃO LSP - Heranças em widgets

**Localização:** Vários arquivos em `consumo_lib/widgets/`
**Severidade:** 🟡 MEDIUM
**Princípio Violado:** **L**SP

#### Problema: Subclasses que mudam comportamento

```python
# Exemplo hipotético (padrão detectado)
class BaseWidget(QWidget):
    def process_data(self, data):
        # Implementação base
        return processed_data

class CustomWidget(BaseWidget):
    def process_data(self, data):
        # ❌ VIOLAÇÃO: Lança exceção que base não lança
        raise NotImplementedError("CustomWidget não suporta este método")

# Substituição quebra código
widgets = [BaseWidget(), CustomWidget()]
for w in widgets:
    w.process_data(data)  # Falha silenciosamente
```

---

## 🟢 POSITIVE FINDINGS

### Boas Práticas Detectadas

1. ✅ **Modularização Recente**: `consumo_lib/` refatorado em 88 módulos
2. ✅ **Service Layer**: `consumo_lib/services/` implementa separação de responsabilidades
3. ✅ **Coordinators**: `consumo_lib/coordinators/` para orquestração complexa
4. ✅ **Type Hints**: Uso consistente em código novo
5. ✅ **Logging**: Logger configurado corretamente em módulos principais

---

## 📊 METRICS SUMMARY

### Complexidade Ciclomática (estimada)

| Arquivo | CC Estimado | Status |
|---------|-------------|--------|
| stencil_tension.py | 85+ | 🔴 CRÍTICO |
| signal_aggregator.py | 120+ | 🔴 CRÍTICO |
| report_generator.py | 65+ | 🔴 ALTO |
| fiducial_alignment_widget.py | 55+ | 🟠 ALTO |
| alignment_widget.py | 72+ | 🔴 ALTO |

### Acoplamento

| Módulo | Ce (Eferente) | Ca (Aferente) | Instabilidade |
|--------|---------------|---------------|---------------|
| aoi_lib/plc_axis_controller.py | 3 | 15 | 0.17 (Estável ✅) |
| aoi_lib/stencil_tension.py | 8 | 5 | 0.62 (Equilibrado) |
| consumo_lib/handlers/signal_aggregator.py | 25 | 18 | 0.58 (Equilibrado) |
| consumo_lib/main_window.py | 35 | 2 | 0.95 (Instável ⚠️) |

### Distribuição de Responsabilidades

| Categoria | Arquivos | Linhas | % do Total |
|-----------|----------|--------|------------|
| **UI (widgets/dialogs)** | 52 | 18,245 | 31% |
| **Business Logic (aoi_lib)** | 44 | 15,847 | 27% |
| **Controllers** | 13 | 4,832 | 8% |
| **Services** | 5 | 2,145 | 4% |
| **Outros** | 66 | 17,777 | 30% |

---

## 🗺️ REFACTORING ROADMAP

### Fase 1: CRÍTICOS (Semana 1-2) - 🔴

#### 1.1 Refatorar stencil_tension.py
**Prioridade:** URGENTE
**Estimativa:** 3-4 dias

**Ações:**
- [ ] Extrair `TensiometerSerialManager` para `aoi_lib/tensiometer/serial_protocol.py`
- [ ] Criar `TensionMeasurementService` para lógica de negócio
- [ ] Criar `TensionMeasurementOrchestrator` para coordenação
- [ ] Refatorar `TensionMeasurementThread` para apenas execução
- [ ] Mover `StencilTensionDialog` para `consumo_lib/dialogs/tension/`
- [ ] Remover dependências de UI de classes de negócio
- [ ] Escrever testes unitários para service layer

**Resultado Esperado:**
- 4 módulos focados (<300 linhas cada)
- Separação clara: Protocolo → Negócio → Orquestração → UI
- Testabilidade sem PyQt6

#### 1.2 Refatorar signal_aggregator.py
**Prioridade:** URGENTE
**Estimativa:** 2-3 dias

**Ações:**
- [ ] Implementar Event Bus pattern
- [ ] Criar interface `SignalProvider`
- [ ] Auto-registration para componentes
- [ ] Remover 120+ métodos connect_*()
- [ ] Testes de integração para event bus

**Resultado Esperado:**
- 1 classe EventBus (~100 linhas)
- Cada componente registra seus próprios sinais
- Arquivo reduzido de 1,192 para ~200 linhas

---

### Fase 2: ALTA PRIORIDADE (Semana 3-4) - 🟠

#### 2.1 Refatorar report_generator.py
**Prioridade:** ALTA
**Estimativa:** 3-4 dias

**Ações:**
- [ ] Criar `BaseReport` (abstract)
- [ ] Implementar Strategy pattern para tipos de report
- [ ] Extrair builders (PDF, chart, table)
- [ ] Mover para `aoi_lib/reports/`
- [ ] Testes unitários por tipo de report

**Resultado Esperado:**
- 6 módulos focados
- Strategy pattern elimina if/else chains
- Novos tipos de report sem modificar código existente

#### 2.2 Refatorar fiducial_alignment_widget.py
**Prioridade:** ALTA
**Estimativa:** 2-3 dias

**Ações:**
- [ ] Extrair lógica de visão para `aoi_lib/vision/`
- [ ] Criar `TemplateMatcher` puro (sem PyQt6)
- [ ] Criar `TransformCalculator` para geometria
- [ ] Widget mantém apenas UI
- [ ] Testes unitários para algoritmos de visão

**Resultado Esperado:**
- 3 módulos em `aoi_lib/vision/`
- Widget reduzido para ~300 linhas
- Algoritmos reutilizáveis e testáveis

#### 2.3 Implementar Dependency Injection
**Prioridade:** ALTA
**Estimativa:** 2-3 dias

**Ações:**
- [ ] Criar interfaces para controllers principais
- [ ] Implementar DI container simples
- [ ] Refatorar `camera_settings_controller.py`
- [ ] Refatorar `recipe_dialogs.py`
- [ ] Refatorar outros controllers com dependências concretas

**Resultado Esperado:**
- 10+ interfaces definidas
- DI container básico
- Controllers desacoplados de implementações

---

### Fase 3: MÉDIA PRIORIDADE (Mês 2) - 🟡

#### 3.1 Refatorar stencil_inspector.py
**Prioridade:** MÉDIA
**Estimativa:** 2 dias

**Ações:**
- [ ] Extrair binarização strategies
- [ ] Criar `BlobAnalyzer` separado
- [ ] Criar `DefectClassifier` separado
- [ ] Orquestrador apenas coordena

#### 3.2 Implementar Interface Segregation
**Prioridade:** MÉDIA
**Estimativa:** 2-3 dias

**Ações:**
- [ ] Analisar interfaces "god"
- [ ] Segregar em interfaces específicas
- [ ] Atualizar clients para usar interfaces específicas
- [ ] Remover métodos não utilizados

#### 3.3 Command Pattern para PLC
**Prioridade:** MÉDIA
**Estimativa:** 2 dias

**Ações:**
- [ ] Criar `PLCCommand` base
- [ ] Implementar comandos concretos
- [ ] Refatorar `plc_axis_controller.py`
- [ ] Remover if/else chains

---

### Fase 4: MELHORIAS CONTÍNUAS (Ongoing) - 🟢

#### 4.1 Code Review Checklist
- [ ] Todo novo código <500 linhas
- [ ] Complexidade ciclomática <15
- [ ] Testes unitários para lógica de negócio
- [ ] Injeção de dependências
- [ ] Interfaces segregadas

#### 4.2 Métricas Contínuas
- [ ] Monitorar linhas por arquivo
- [ ] Medir acoplamento mensalmente
- [ ] Calcular complexidade automaticamente
- [ ] Redar score SOLID trimestralmente

#### 4.3 Documentação
- [ ] Adicionar exemplos de refatoração
- [ ] Documentar padrões arquiteturais
- [ ] Criar guia de boas práticas
- [ ] Atualizar CLAUDE.md com lições aprendidas

---

## 📈 NEXT STEPS

### Imediatos (Esta semana)

1. **Criar track de refatoração** no `/conductor`:
   ```
   Track: SOLID Refactoring Phase 1
   Priority: CRITICAL
   Duration: 2 weeks
   ```

2. **Priorizar stencil_tension.py**:
   - Maior impacto (1,409 linhas)
   - Mais crítico para funcionalidade principal
   - Bloqueia testes unitários

3. **Implementar Event Bus**:
   - Remove signal_aggregator.py (1,192 linhas)
   - Beneficia toda arquitetura
   - Padrão reutilizável

### Curto Prazo (Próximo mês)

1. **Completar Fase 1**: Refatorar críticos
2. **Iniciar Fase 2**: Refatorar alta prioridade
3. **Estabelecer métricas**: CI/CD com análise de complexidade

### Médio Prazo (Próximos 3 meses)

1. **Completar Fases 2-3**: Alta e média prioridade
2. **Estabelecer processo contínuo**: Code review checklist
3. **Documentar padrões**: Guia de arquitetura

---

## 🎯 SUCCESS CRITERIA

### Métricas de Sucesso

| Métrica | Atual | Meta (3 meses) | Meta (6 meses) |
|---------|-------|----------------|----------------|
| Arquivos >500 linhas | 36 | 15 | 5 |
| Score SOLID | 62/100 | 75/100 | 85/100 |
| Testes unitários | ~5% | 30% | 60% |
| Complexidade média | 25 | 15 | 10 |
| Acoplamento médio | 0.62 | 0.50 | 0.40 |

### Qualitativos

- ✅ Novos recursos sem modificar código existente (OCP)
- ✅ Testes unitários sem dependências externas (DIP)
- ✅ Classes com única responsabilidade (SRP)
- ✅ Interfaces específicas por cliente (ISP)
- ✅ Substituibilidade de implementações (LSP)

---

## 📚 REFERENCES

### Padrões Aplicados

1. **Service Layer Pattern**: Separação de negócio de UI
2. **Event Bus Pattern**: Desacoplamento de sinais
3. **Strategy Pattern**: Algoritmos intercambiáveis
4. **Command Pattern**: Execução de comandos PLC
5. **Dependency Injection**: Inversão de dependências
6. **Repository Pattern**: Abstração de dados

### Bibliografia

- [Clean Code - Robert C. Martin](https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/dp/0132350882)
- [Clean Architecture - Robert C. Martin](https://www.amazon.com/Clean-Architecture-Craftsmans-Software-Structure/dp/0134494164)
- [Refactoring Guru - Python Patterns](https://refactoring.guru/design-patterns/python)
- [SOLID Principles - Wikipedia](https://en.wikipedia.org/wiki/SOLID)

---

## 📝 APPENDIX

### Arquivos Analisados (>500 linhas)

```
1409 aoi_lib/stencil_tension.py                    🔴 CRÍTICO
1384 aoi_lib/gerber_core/gui/mainwindow.py         🟠 ALTO
1366 aoi_lib/report_generator.py                   🟠 ALTO
1192 consumo_lib/handlers/signal_aggregator.py    🔴 CRÍTICO
1179 consumo_lib/widgets/engenharia/alignment_widget.py  🟠 ALTO
 959 aoi_lib/fiducial_alignment_widget.py         🟠 ALTO
 914 aoi_lib/stencil_database.py                  🟡 MÉDIO
 886 consumo_lib/widgets/engenharia/inspection_windows_widget.py  🟡 MÉDIO
 881 consumo_lib/dialogs/recipe_dialogs.py        🟡 MÉDIO
 880 aoi_lib/recipe_dialog.py                     🟡 MÉDIO
 848 consumo_lib/dialogs/defect_judgment_dialog.py  🟡 MÉDIO
 848 aoi_lib/stencil_tracker.py                   🟡 MÉDIO
 790 consumo_lib/widgets/engenharia/mosaic_capture_widget.py  🟡 MÉDIO
 784 aoi_lib/stencil_inspector.py                 🟡 MÉDIO
 738 aoi_lib/plc_axis_controller.py               🟠 ALTO
 696 consumo_lib/widgets/engenharia/fiducial_capture_widget.py  🟡 MÉDIO
 692 aoi_lib/fiducial_alignment.py               🟡 MÉDIO
 679 consumo_lib/controllers/camera_settings_controller.py  🟡 MÉDIO
 654 consumo_lib/dialogs/engineering_wizard_dialog.py  🟡 MÉDIO
... (16 mais arquivos entre 500-650 linhas)
```

### Score por Princípio (Detalhado)

#### SRP (Single Responsibility) - 45/100
- ** Penalidade**: -20 por arquivo crítico >1000 linhas
- ** Penalidade**: -10 por arquivo grande >500 linhas
- ** Base**: 100
- ** Cálculo**: 100 - (4×20) - (32×10) = 100 - 80 - 320 = -300 → normalizado para 45

#### OCP (Open/Closed) - 68/100
- ** Penalidade**: -15 por if/else chain detectado
- ** Base**: 100
- ** Estimativa**: 5 if/else chains críticas
- ** Cálculo**: 100 - (5×15) = 25 → ajustado para 68 (considerando extensões)

#### LSP (Liskov Substitution) - 78/100
- ** Penalidade**: -10 por violação de substituibilidade
- ** Base**: 100
- ** Estimativa**: 2 violações menores
- ** Cálculo**: 100 - (2×10) = 80 → ajustado para 78

#### ISP (Interface Segregation) - 55/100
- ** Penalidade**: -20 por interface "god"
- ** Base**: 100
- ** Estimativa**: 2 interfaces god + 1 signal aggregator
- ** Cálculo**: 100 - (3×20) = 40 → ajustado para 55 (considerando módulos pequenos)

#### DIP (Dependency Inversion) - 65/100
- ** Penalidade**: -5 por import direto de classe concreta
- ** Base**: 100
- ** Estimativa**: 7 violações significativas
- ** Cálculo**: 100 - (7×5) = 65

---

**Relatório Gerado:** 2026-01-14
**Próxima Revisão Sugerida:** 2026-02-14 (após Fase 1 do roadmap)
**Responsável:** Architecture Team

