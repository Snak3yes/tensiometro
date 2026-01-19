# Design System - Plano de Implementação

**Track ID:** design_system_20260119
**Data de Criação:** 2026-01-19
**Estimativa:** 4-6 semanas

---

## 📊 Visão Geral

Este plano detalha a implementação do Design System do Tensiometro em 4 fases principais, totalizando 38 tarefas distribuídas em 6 semanas de desenvolvimento.

### Estrutura do Plano

- **Fase 1: Fundação do Design System** (Semanas 1-2, 13 tarefas)
- **Fase 2: Gerenciador de Temas e Integração** (Semana 3, 8 tarefas)
- **Fase 3: Migração Parcial (Prova de Conceito)** (Semanas 4-5, 12 tarefas)
- **Fase 4: Documentação e Validação** (Semana 6, 5 tarefas)

### Estratégia de Testes

**Adaptive Testing Strategy:**
- **Design Tokens:** Test-After (simples, apenas constantes)
- **Componentes Base:** Test-After (visual, validação manual)
- **Theme Manager:** TDD (lógica de carregamento de arquivos)
- **Migração:** Test-After + validação manual visual

**Cobertura Alvo:** >80% para código novo

---

## 📍 Fase 1: Fundação do Design System

**Objetivo:** Criar os blocos fundamentais do Design System (tokens, stylesheet, componentes base)

**Duração:** Semanas 1-2 (10 dias úteis)
**Saídas:**
- `consumo_lib/ui/design_tokens.py` (250+ linhas)
- `consumo_lib/ui/styles.qss` (200+ linhas)
- `consumo_lib/ui/widget_standards.py` (150+ linhas)
- `consumo_lib/ui/helpers.py` (50+ linhas)

### Status: ✅ COMPLETE (2026-01-19)

---

### Tarefa 1.1: Criar Estrutura de Diretórios ✅

**Descrição:** Criar diretório `consumo_lib/ui/` com estrutura inicial

**Arquivos:**
- `consumo_lib/ui/__init__.py`

**Critérios de Aceite:**
- [ ] Diretório `consumo_lib/ui/` criado
- [ ] Arquivo `__init__.py` criado com exports básicos
- [ ] README.md criado explicando propósito do diretório

**Estimativa:** 30 minutos
**Prioridade:** 🔴 HIGH
**Dependências:** Nenhuma

---

### Tarefa 1.2: Implementar ColorPalette

**Descrição:** Criar classe `ColorPalette` com todas as constantes de cores

**Arquivo:** `consumo_lib/ui/design_tokens.py`

**Constantes a Implementar:**
- Primary colors (PRIMARY, PRIMARY_DARK, PRIMARY_LIGHT, ON_PRIMARY)
- Secondary colors (SECONDARY, SECONDARY_DARK, SECONDARY_LIGHT, ON_SECONDARY)
- Semantic colors (SUCCESS, WARNING, ERROR, com variants)
- Status colors (STATUS_APPROVED_AUTO, STATUS_APPROVED_USER, etc.)
- Neutral colors (TEXT_PRIMARY, TEXT_SECONDARY, BACKGROUND, SURFACE)
- Border colors (BORDER, BORDER_DARK, BORDER_FOCUS)
- Engineering colors (OVERLAY_IMAGE, FIDUCIAL_FOUND, etc.)

**Critérios de Aceite:**
- [ ] 30+ constantes de cores definidas
- [ ] Valores hexadecimais seguindo Material Design 3
- [ ] Docstring em cada constante explicando propósito
- [ ] Classe como dataclass
- [ ] Instância singleton `COLORS` exportada

**Testes:**
- Verificar se todas as constantes têm formato HEX válido
- Verificar se constantes de status estão definidas

**Estimativa:** 3 horas
**Prioridade:** 🔴 HIGH
**Dependências:** Tarefa 1.1

---

### Tarefa 1.3: Implementar Typography

**Descrição:** Criar classe `Typography` com sistema de tipos

**Arquivo:** `consumo_lib/ui/design_tokens.py` (continuação)

**Atributos a Implementar:**
- Font family (FONT_FAMILY, FONT_FAMILY_MONOSPACE)
- Type scale (DISPLAY_LARGE, DISPLAY_MEDIUM, ..., LABEL_SMALL)
- Factory method `get_font(size, bold=False, italic=False)`
- Métodos convenience (display_large, headline_medium, body_medium, etc.)

**Critérios de Aceite:**
- [ ] Type scale completo (12 níveis seguindo Material Design 3)
- [ ] Método `get_font()` funcionando com parâmetros
- [ ] 5+ métodos convenience criados
- [ ] Docstrings explicando quando usar cada nível
- [ ] Instância singleton `TYPO` exportada

**Testes:**
- Testar criação de QFont com diferentes parâmetros
- Verificar se métodos convenience retornam QFont corretas

**Estimativa:** 2 horas
**Prioridade:** 🔴 HIGH
**Dependências:** Tarefa 1.2

---

### Tarefa 1.4: Implementar Spacing

**Descrição:** Criar classe `Spacing` com sistema de espaçamentos

**Arquivo:** `consumo_lib/ui/design_tokens.py` (continuação)

**Atributos a Implementar:**
- Baseline grid (BASE = 4px)
- Escala (XS=4, SM=8, MD=16, LG=24, XL=32, XXL=48)
- Paddings contextuais (PADDING_TIGHT, PADDING_NORMAL, PADDING_SPACIOUS)
- Margins contextuais (MARGIN_TIGHT, MARGIN_NORMAL, MARGIN_SPACIOUS)

**Critérios de Aceite:**
- [ ] Escala completa implementada
- [ ] Valores em múltiplos de 4px
- [ ] Tuples para paddings (vertical, horizontal)
- [ ] Docstrings explicando quando usar cada valor
- [ ] Instância singleton `SPACE` exportada

**Estimativa:** 1 hora
**Prioridade:** 🟡 MEDIUM
**Dependências:** Tarefa 1.3

---

### Tarefa 1.5: Implementar Dimensions

**Descrição:** Criar classe `Dimensions` com dimensões padronizadas

**Arquivo:** `consumo_lib/ui/design_tokens.py` (continuação)

**Atributos a Implementar:**
- Border radius (RADIUS_SM, RADIUS_MD, RADIUS_LG, RADIUS_XL, RADIUS_CIRCLE)
- Icon sizes (ICON_XS, ICON_SM, ICON_MD, ICON_LG, ICON_XL)
- Button heights (BUTTON_HEIGHT_SM, BUTTON_HEIGHT_MD, BUTTON_HEIGHT_LG)
- Input heights (INPUT_HEIGHT_SM, INPUT_HEIGHT_MD, INPUT_HEIGHT_LG)
- Dialog sizes (DIALOG_SMALL, DIALOG_MEDIUM, DIALOG_LARGE, DIALOG_XLARGE)
- Widget sizes (BADGE_HEIGHT, PROGRESS_BAR_HEIGHT, etc.)
- Thumbnail sizes (THUMBNAIL_SM, THUMBNAIL_MD, THUMBNAIL_LG)

**Critérios de Aceite:**
- [ ] 20+ constantes de dimensões
- [ ] Tuples para sizes (width, height)
- [ ] Valores baseados em Material Design 3
- [ ] Docstrings explicando cada categoria
- [ ] Instância singleton `DIM` exportada

**Estimativa:** 2 horas
**Prioridade:** 🟡 MEDIUM
**Dependências:** Tarefa 1.4

---

### Tarefa 1.6: Implementar Elevation, Opacity, Transitions

**Descrição:** Completar design tokens com elevação, opacidades e transições

**Arquivo:** `consumo_lib/ui/design_tokens.py` (continuação)

**Classes a Implementar:**
- `Elevation` - Níveis 0-5 para sombras/layering
- `Opacity` - Valores padronizados (DISABLED, HOVER, FOCUS, PRESSED, DRAG, OVERLAY)
- `Transitions` - Durações (FAST=150ms, NORMAL=250ms, SLOW=350ms) e easing functions
- `Breakpoints` - Responsive breakpoints (XS=600, SM=960, MD=1280, LG=1920, XL=2560)
- `Accessibility` - Constantes WCAG (CONTRAST_NORMAL, MINIMUM_TOUCH_SIZE, etc.)

**Critérios de Aceite:**
- [ ] 5 classes adicionais criadas
- [ ] Todos os valores seguindo Material Design 3 / WCAG
- [ ] Instâncias singleton exportadas (ELEV, OPAC, TRANS, BREAK, A11Y)
- [ ] Docstrings completas

**Estimativa:** 2 horas
**Prioridade:** 🟡 MEDIUM
**Dependências:** Tarefa 1.5

---

### Tarefa 1.7: Exportar Tokens e Testar

**Descrição:** Finalizar design_tokens.py com exports e testes básicos

**Arquivos:**
- `consumo_lib/ui/design_tokens.py` (finalização)
- `tests/unit/test_design_tokens.py`

**Atividades:**
- Criar instâncias singleton no final do arquivo
- Adicionar `__all__` com exports públicos
- Criar testes unitários básicos
- Testar imports de outros módulos

**Critérios de Aceite:**
- [ ] `from consumo_lib.ui.design_tokens import COLORS, TYPO, SPACE, DIM` funciona
- [ ] Testes unitários criados (10+ testes)
- [ ] 100% de type hints no código
- [ ] Pylint score >8.0

**Testes:**
```python
def test_color_palette_constants():
    assert COLORS.PRIMARY == "#4CAF50"
    assert COLORS.SUCCESS == "#2ecc71"

def test_typography_factory():
    font = TYPO.get_font(14, bold=True)
    assert font.pointSize() == 14
    assert font.bold() == True
```

**Estimativa:** 2 horas
**Prioridade:** 🔴 HIGH
**Dependências:** Tarefa 1.6

---

### Tarefa 1.8: Criar Qt Style Sheet (Base)

**Descrição:** Criar arquivo styles.qss com reset e estilos base

**Arquivo:** `consumo_lib/ui/styles.qss`

**Seções a Implementar:**
- Reset & Base (outline, font family, cores globais)
- Buttons (estilo base, estados hover/pressed/disabled)
- Text & Labels (base, heading, subheading, caption)

**Critérios de Aceite:**
- [ ] Arquivo .qss criado com sintaxe correta
- [ ] Comentários por seção
- [ ] Estilos usando cores hexadecimais
- [ ] 50+ linhas de CSS

**Estimativa:** 2 horas
**Prioridade:** 🔴 HIGH
**Dependências:** Tarefa 1.7

---

### Tarefa 1.9: Completar Qt Style Sheet (Componentes)

**Descrição:** Adicionar estilos para todos componentes Qt restantes

**Arquivo:** `consumo_lib/ui/styles.qss` (continuação)

**Componentes a Adicionar:**
- Inputs (QLineEdit, QTextEdit, QPlainTextEdit)
- Combobox (QComboBox)
- SpinBox (QSpinBox, QDoubleSpinBox)
- Checkbox & Radio (QCheckBox, QRadioButton)
- GroupBox (QGroupBox)
- ScrollBar (QScrollBar)
- ProgressBar (QProgressBar)
- TabWidget (QTabWidget)
- Table (QTableView, QTableWidget)
- Dialog (QDialog)
- Menu (QMenu)

**Critérios de Aceite:**
- [ ] Todos os 13 componentes estilizados
- [ ] Estados interativos implementados (hover, focus, disabled)
- [ ] 150+ linhas totais no arquivo
- [ ] Comentários explicativos por seção

**Estimativa:** 4 horas
**Prioridade:** 🟡 MEDIUM
**Dependências:** Tarefa 1.8

---

### Tarefa 1.10: Implementar StandardButton

**Descrição:** Criar classe StandardButton com variantes

**Arquivo:** `consumo_lib/ui/widget_standards.py`

**Funcionalidades:**
- Herdar de QPushButton
- Aceitar parâmetros: text, variant (primary|secondary|danger|outline)
- Aplicar fonte automaticamente (TYPO.BODY_LARGE, bold)
- Aplicar tamanho mínimo (DIM.BUTTON_HEIGHT_MD)
- Usar property "variant" para stylesheet

**Critérios de Aceite:**
- [ ] Classe StandardButton criada
- [ ] 4 variantes implementadas
- [ ] Docstring completa
- [ ] Type hints
- [ ] Exemplo de uso em docstring

**Testes:**
- Testar criação com diferentes variantes
- Verificar se property "variant" está definida

**Estimativa:** 1.5 horas
**Prioridade:** 🔴 HIGH
**Dependências:** Tarefa 1.7

---

### Tarefa 1.11: Implementar StandardLabel

**Descrição:** Criar classe StandardLabel com variantes

**Arquivo:** `consumo_lib/ui/widget_standards.py` (continuação)

**Funcionalidades:**
- Herdar de QLabel
- Aceitar parâmetros: text, variant (heading|subheading|body|caption)
- Selecionar fonte automaticamente
- Usar property para stylesheet

**Critérios de Aceite:**
- [ ] Classe StandardLabel criada
- [ ] 4 variantes implementadas
- [ ] Docstring completa
- [ ] Exemplo de uso

**Estimativa:** 1 hora
**Prioridade:** 🔴 HIGH
**Dependências:** Tarefa 1.10

---

### Tarefa 1.12: Implementar Inputs e Outros Componentes

**Descrição:** Criar classes restantes de componentes padrão

**Arquivo:** `consumo_lib/ui/widget_standards.py` (continuação)

**Componentes a Implementar:**
- `StandardInput` (QLineEdit)
- `StandardSpinBox` (QSpinBox)
- `StandardDoubleSpinBox` (QDoubleSpinBox)
- `StandardComboBox` (QComboBox)
- `StandardGroupBox` (QGroupBox)

**Critérios de Aceite:**
- [ ] 5 classes criadas
- [ ] Todas com altura mínima aplicada
- [ ] Docstrings completas
- [ ] StandardGroupBox com espaçamento interno

**Estimativa:** 2 horas
**Prioridade:** 🟡 MEDIUM
**Dependências:** Tarefa 1.11

---

### Tarefa 1.13: Criar Funções Helper

**Descrição:** Criar funções utilitárias para tarefas comuns de UI

**Arquivo:** `consumo_lib/ui/helpers.py`

**Funções a Implementar:**
- `create_h_spacer()` - Espaço horizontal expansível
- `create_v_spacer()` - Espaço vertical expansível
- `add_spacing(layout, space)` - Adiciona espaçamento
- `create_separator(orientation)` - Linha separadora
- `apply_standard_spacing(layout)` - Aplica spacing e margins

**Critérios de Aceite:**
- [ ] 5 funções criadas
- [ ] Docstrings completas
- [ ] Type hints
- [ ] Usando design tokens (SPACE)

**Testes:**
- Testar criação de spacers
- Testar separadores

**Estimativa:** 1.5 horas
**Prioridade:** 🟡 MEDIUM
**Dependências:** Tarefa 1.12

---

## 📍 Fase 2: Gerenciador de Temas e Integração

**Objetivo:** Criar ThemeManager e integrar com aplicação principal

**Duração:** Semana 3 (5 dias úteis)
**Saídas:**
- `consumo_lib/ui/theme_manager.py` (100+ linhas)
- Integração em `consumo_lib/main_window.py`
- Testes de tema funcionando

### Status: ⏳ TODO

---

### Tarefa 2.1: Implementar ThemeManager (Básico)

**Descrição:** Criar classe ThemeManager com carregamento de stylesheet

**Arquivo:** `consumo_lib/ui/theme_manager.py`

**Funcionalidades:**
- Herdar de QObject
- Construtor recebendo QApplication
- Método `_load_stylesheet()` para ler styles.qss
- Aplicar stylesheet globalmente
- Logging de sucesso/erro

**Critérios de Aceite:**
- [ ] Classe ThemeManager criada
- [ ] Stylesheet carregado de styles.qss
- [ ] Fallback para estilos padrão do Qt se falhar
- [ ] Logs informativos (success/warning)

**Testes:**
- Testar inicialização com QApplication válida
- Testar fallback quando styles.qss não existe
- Verificar se stylesheet foi aplicado

**Estimativa:** 3 horas
**Prioridade:** 🔴 HIGH
**Dependências:** Tarefa 1.9

---

### Tarefa 2.2: Adicionar Gerenciamento de Temas

**Descrição:** Adicionar métodos para alternar temas

**Arquivo:** `consumo_lib/ui/theme_manager.py` (continuação)

**Funcionalidades:**
- Método `set_theme(theme_name)` para alternar temas
- Método `_apply_theme(theme_name)` para aplicar configurações
- Propriedades `colors` e `typo` para acessar tokens
- Placeholder para dark mode (TODOs com comentários)

**Critérios de Aceite:**
- [ ] Método set_theme funcionando
- [ ] Tema padrão "light" ativo no startup
- [ ] Propriedades colors/typo retornando instâncias corretas
- [ ] TODOs documentados para dark mode

**Testes:**
- Testar set_theme com tema válido
- Testar set_theme com mesmo tema (não deve fazer nada)
- Verificar propriedades colors/typo

**Estimativa:** 2 horas
**Prioridade:** 🟡 MEDIUM
**Dependências:** Tarefa 2.1

---

### Tarefa 2.3: Implementar Singleton Pattern

**Descrição:** Adicionar instância global do ThemeManager

**Arquivo:** `consumo_lib/ui/theme_manager.py` (continuação)

**Funcionalidades:**
- Variável global `_instance: Optional[ThemeManager] = None`
- Função `init_theme_manager(app: QApplication)` para criar instância
- Função `get_theme_manager()` para acessar instância
- Verificar se instância já existe antes de criar

**Critérios de Aceite:**
- [ ] Singleton pattern implementado
- [ ] init_theme_manager cria instância se não existe
- [ ] get_theme_manager retorna None se não inicializado
- [ ] get_theme_manager retorna instância se inicializado
- [ ] Thread-safe (opcional, mas recomendado)

**Testes:**
- Testar chamadas múltiplas de init_theme_manager
- Testar get_theme_manager antes e depois de init

**Estimativa:** 1 hora
**Prioridade:** 🔴 HIGH
**Dependências:** Tarefa 2.2

---

### Tarefa 2.4: Testar ThemeManager

**Descrição:** Criar testes unitários completos para ThemeManager

**Arquivo:** `tests/unit/test_theme_manager.py`

**Testes a Implementar:**
- Teste de inicialização bem-sucedida
- Teste de fallback quando styles.qss não existe
- Teste de set_theme
- Teste de propriedades colors/typo
- Teste de singleton pattern
- Teste de chamadas múltiplas de init_theme_manager

**Critérios de Aceite:**
- [ ] 10+ testes criados
- [ ] 100% passing
- [ ] Coverage >80%
- [ ] Mock de QApplication usado

**Estimativa:** 2 horas
**Prioridade:** 🟡 MEDIUM
**Dependências:** Tarefa 2.3

---

### Tarefa 2.5: Atualizar __init__.py do ui/

**Descrição:** Exportar classes públicas do módulo ui

**Arquivo:** `consumo_lib/ui/__init__.py`

**Exports:**
- from .design_tokens import COLORS, TYPO, SPACE, DIM, ELEV, OPAC, TRANS, BREAK, A11Y
- from .widget_standards import StandardButton, StandardLabel, StandardInput, etc.
- from .theme_manager import init_theme_manager, get_theme_manager
- from .helpers import create_h_spacer, create_v_spacer, etc.

**Critérios de Aceite:**
- [ ] __all__ definido com exports públicos
- [ ] Imports funcionando de consumo_lib.ui
- [ ] Docstrings no __init__.py explicando módulo

**Estimativa:** 30 minutos
**Prioridade:** 🟡 MEDIUM
**Dependências:** Tarefa 2.4

---

### Tarefa 2.6: Integrar ThemeManager em main_window.py

**Descrição:** Inicializar ThemeManager no startup da aplicação

**Arquivo:** `consumo_lib/main_window.py`

**Modificações:**
- Importar init_theme_manager no topo
- Chamar init_theme_manager(app) no __init__ de AOIControllerApp
- Adicionar logging de sucesso/erro
- Verificar se ThemeManager foi inicializado corretamente

**Critérios de Aceite:**
- [ ] ThemeManager inicializado no startup
- [ ] Stylesheet global carregado automaticamente
- [ ] Log de sucesso no console
- [ ] Aplicação continua funcionando normalmente

**Testes:**
- Testar startup da aplicação
- Verificar se stylesheet foi aplicado (inspecionar visualmente)

**Estimativa:** 1 hora
**Prioridade:** 🔴 HIGH
**Dependências:** Tarefa 2.5

---

### Tarefa 2.7: Validar Stylesheet Global

**Descrição:** Testar visualmente se stylesheet está funcionando

**Atividades:**
- Abrir aplicação
- Verificar cores de botões (devem ser verde #4CAF50)
- Verificar fontes (devem ser Arial, tamanho correto)
- Verificar estados hover/pressed de botões
- Verificar inputs (bordas, focus states)
- Tirar screenshots antes/depois

**Critérios de Aceite:**
- [ ] Botões com cor verde (#4CAF50)
- [ ] Hover state funcionando
- [ ] Inputs com bordas e focus states
- [ ] Fontes consistentes (Arial)
- [ ] Zero erros no console

**Artefatos:**
- Screenshots de validação

**Estimativa:** 1 hora
**Prioridade:** 🔴 HIGH
**Dependências:** Tarefa 2.6

---

### Tarefa 2.8: Checkpoint Fase 2

**Descrição:** Validar conclusão da Fase 2 e preparar para próxima

**Atividades:**
- Verificar todos os critérios de aceite da fase
- Criar commit: "feat(design-system): Phase 2 complete - Theme Manager integration"
- Atualizar plan.md marcando fase como completa
- Testar regression (aplicação funciona normalmente)

**Critérios de Aceite:**
- [ ] Todas as tarefas da fase marcadas como [x]
- [ ] Commit criado com mensagem descritiva
- [ ] Aplicação rodando sem erros
- [ ] Stylesheet global aplicado e funcionando

**Estimativa:** 30 minutos
**Prioridade:** 🔴 HIGH
**Dependências:** Todas as tarefas da Fase 2

---

## 📍 Fase 3: Migração Parcial (Prova de Conceito)

**Objetivo:** Migrar 10 arquivos críticos para validar Design System

**Duração:** Semanas 4-5 (10 dias úteis)
**Saídas:**
- 10 arquivos migrados sem hardcoded values
- Exemplos de before/after
- Validação visual

### Status: ⏳ TODO

---

### Tarefa 3.1: Migrar status_badge.py

**Descrição:** Refatorar StatusBadge para usar design tokens

**Arquivo:** `consumo_lib/widgets/status_badge.py`

**Mudanças:**
- Importar COLORS do design_tokens
- Substituir cores hardcoded por COLORS.*
- Mantendo lógica existente (já é bem estruturada)

**Antes:**
```python
COLORS = {
    "approved_auto": "#4CAF50",
    "approved_user": "#CDDC39",
    # ...
}
```

**Depois:**
```python
from consumo_lib.ui.design_tokens import COLORS

STATUS_COLORS = {
    "approved_auto": COLORS.STATUS_APPROVED_AUTO,
    "approved_user": COLORS.STATUS_APPROVED_USER,
    # ...
}
```

**Critérios de Aceite:**
- [ ] Zero hardcoded colors no arquivo
- [ ] Cores importadas de COLORS
- [ ] Testes existentes continuam passando
- [ ] Visual idêntico ao original

**Estimativa:** 1 hora
**Prioridade:** 🔴 HIGH
**Dependências:** Fase 2 completa

---

### Tarefa 3.2: Migrar movement_control.py

**Descrição:** Refatorar MovementControlWidget para usar design tokens e componentes padrão

**Arquivo:** `consumo_lib/widgets/movement_control.py`

**Mudanças:**
- Importar TYPO, DIM do design_tokens
- Importar StandardButton do widget_standards
- Substituir `QFont()` por `TYPO.get_font()`
- Substituir tamanhos hardcoded por `DIM.*`
- Substituir `QPushButton` por `StandardButton`

**Critérios de Aceite:**
- [ ] Zero hardcoded fonts
- [ ] Zero hardcoded sizes
- [ ] StandardButton usado para botões de movimento
- [ ] Testes existentes passando
- [ ] Funcionalidade mantida

**Estimativa:** 2 horas
**Prioridade:** 🔴 HIGH
**Dependências:** Tarefa 3.1

---

### Tarefa 3.3: Migrar operator_interface.py

**Descrição:** Refatorar OperatorInterface para usar design tokens

**Arquivo:** `consumo_lib/widgets/operator_interface.py`

**Mudanças:**
- Substituir cores hardcoded em setStyleSheet
- Usar COLORS para cores de background/text
- Usar SPACE para paddings
- Substituir fontes hardcoded por TYPO

**Critérios de Aceite:**
- [ ] Zero hardcoded colors
- [ ] Cores usando COLORS.*
- [ ] Paddings usando SPACE.*
- [ ] Visual mantido

**Estimativa:** 2 horas
**Prioridade:** 🔴 HIGH
**Dependências:** Tarefa 3.2

---

### Tarefa 3.4: Migrar hardware_status_bar.py

**Descrição:** Refatorar HardwareStatusBar para usar design tokens

**Arquivo:** `consumo_lib/widgets/hardware_status_bar.py`

**Mudanças:**
- Substituir cores hardcoded por COLORS
- Substituir bordas hardcoded por dimensões
- Usar espaçamentos de SPACE

**Critérios de Aceite:**
- [ ] Zero hardcoded colors
- [ ] Tamanhos usando DIM
- [ ] Funcionalidade mantida

**Estimativa:** 1.5 horas
**Prioridade:** 🟡 MEDIUM
**Dependências:** Tarefa 3.3

---

### Tarefa 3.5: Migrar tension_viz.py

**Descrição:** Refatorar TensionVisualizationWidget para usar design tokens

**Arquivo:** `consumo_lib/widgets/tension_viz.py`

**Mudanças:**
- Substituir cores hardcoded por COLORS
- Substituir fontes por TYPO
- Simplificar setStyleSheet usando tokens

**Critérios de Aceite:**
- [ ] Zero hardcoded values
- [ ] Visual mantido
- [ ] Funcionalidade mantida

**Estimativa:** 2 horas
**Prioridade:** 🟡 MEDIUM
**Dependências:** Tarefa 3.4

---

### Tarefa 3.6: Migrar login_dialog.py

**Descrição:** Refatorar LoginDialog para usar design tokens

**Arquivo:** `consumo_lib/dialogs/login_dialog.py`

**Mudanças:**
- Substituir setFixedSize(450, 480) por DIM.DIALOG_MEDIUM
- Substituir fontes hardcoded por TYPO
- Usar StandardButton para botões
- Usar StandardLabel para títulos

**Critérios de Aceite:**
- [ ] Tamanho usando DIM.DIALOG_MEDIUM
- [ ] Fontes usando TYPO
- [ ] StandardButton usado
- [ ] Visual profissional mantido

**Estimativa:** 2 horas
**Prioridade:** 🟡 MEDIUM
**Dependências:** Tarefa 3.5

---

### Tarefa 3.7: Migrar inspection_results_dialog.py

**Descrição:** Refatorar InspectionResultsDialog para usar design tokens

**Arquivo:** `consumo_lib/dialogs/inspection_results_dialog.py`

**Mudanças:**
- Substituir setFixedSize(700, 700) por DIM.DIALOG_LARGE
- Substituir cores hardcoded por COLORS
- Substituir fontes por TYPO
- Usar componentes padrão onde possível

**Critérios de Aceite:**
- [ ] Tamanho usando DIM
- [ ] Cores usando COLORS
- [ ] Visual mantido

**Estimativa:** 3 horas
**Prioridade:** 🟡 MEDIUM
**Dependências:** Tarefa 3.6

---

### Tarefa 3.8: Migrar defect_judgment_dialog.py

**Descrição:** Refatorar DefectJudgmentDialog para usar design tokens

**Arquivo:** `consumo_lib/dialogs/defect_judgment_dialog.py`

**Mudanças:**
- Substituir setFixedSize(1000, 750) por DIM.DIALOG_LARGE
- Substituir cores por COLORS
- Substituir fontes por TYPO
- Simplificar setStyleSheet

**Critérios de Aceite:**
- [ ] Zero hardcoded colors/fonts
- [ ] Dimensões usando DIM
- [ ] Visual mantido

**Estimativa:** 3 horas
**Prioridade:** 🟡 MEDIUM
**Dependências:** Tarefa 3.7

---

### Tarefa 3.9: Migrar alignment_widget.py

**Descrição:** Refatorar AlignmentWidget para usar design tokens

**Arquivo:** `consumo_lib/widgets/engenharia/alignment_widget.py`

**Mudanças:**
- Substituir cores hardcoded por COLORS (muitas ocorrências)
- Substituir fontes por TYPO
- Substituir dimensões por DIM
- Simplificar setStyleSheet

**Desafio:** Arquivo grande (959 linhas) com 18 ocorrências de hardcoded colors

**Critérios de Aceite:**
- [ ] Zero hardcoded colors
- [ ] Zero hardcoded fonts
- [ ] Visual mantido
- [ ] Funcionalidade de alinhamento mantida

**Estimativa:** 4 horas
**Prioridade:** 🟡 MEDIUM
**Dependências:** Tarefa 3.8

---

### Tarefa 3.10: Migrar fiducial_capture_widget.py

**Descrição:** Refatorar FiducialCaptureWidget para usar design tokens

**Arquivo:** `consumo_lib/widgets/engenharia/fiducial_capture_widget.py`

**Mudanças:**
- Substituir cores por COLORS
- Substituir fontes por TYPO
- Substituir tamanhos por DIM

**Critérios de Aceite:**
- [ ] Zero hardcoded values
- [ ] Visual mantido

**Estimativa:** 2 horas
**Prioridade:** 🟡 MEDIUM
**Dependências:** Tarefa 3.9

---

### Tarefa 3.11: Validação Visual dos Arquivos Migrados

**Descrição:** Testar visualmente todos os arquivos migrados

**Atividades:**
- Abrir aplicação
- Navegar por todos os componentes migrados
- Verificar cores, fontes, tamanhos
- Comparar com screenshots antes (se disponíveis)
- Testar estados interativos (hover, pressed)
- Documentar diferenças (se houver)

**Critérios de Aceite:**
- [ ] Todos os 10 arquivos testados visualmente
- [ ] Zero regressões visuais
- [ ] Cores consistentes
- [ ] Fontes consistentes
- [ ] Estados interativos funcionando

**Artefatos:**
- Relatório de validação visual (screenshots)

**Estimativa:** 2 horas
**Prioridade:** 🔴 HIGH
**Dependências:** Tarefa 3.10

---

### Tarefa 3.12: Checkpoint Fase 3

**Descrição:** Validar conclusão da Fase 3

**Atividades:**
- Verificar todos os critérios de aceite da fase
- Criar commit: "feat(design-system): Phase 3 complete - Migration of 10 critical files"
- Atualizar plan.md
- Documentar padrões de migração observados

**Critérios de Aceite:**
- [ ] Todas as tarefas marcadas como [x]
- [ ] 10 arquivos migrados
- [ ] Commit criado
- [ ] Validação visual completa
- [ ] Zero regressões

**Estimativa:** 30 minutos
**Prioridade:** 🔴 HIGH
**Dependências:** Todas as tarefas da Fase 3

---

## 📍 Fase 4: Documentação e Validação

**Objetivo:** Documentar Design System completamente e validar uso

**Duração:** Semana 6 (5 dias úteis)
**Saídas:**
- Documentação completa em `docs/design_system/`
- CLAUDE.md atualizado
- Exemplos funcionando
- Track finalizada

### Status: ⏳ TODO

---

### Tarefa 4.1: Criar README do Design System

**Descrição:** Criar documentação principal do Design System

**Arquivo:** `docs/design_system/README.md`

**Seções:**
- O que é e por que usar
- Benefícios
- Arquitetura (tokens, componentes, temas)
- Como começar a usar
- Exemplos rápidos
- Links para documentação detalhada

**Critérios de Aceite:**
- [ ] README criado com 500+ linhas
- [ ] Explicação clara de todos os conceitos
- [ ] Exemplos de código funcionando
- [ ] Links para guias detalhados
- [ ] Screenshot (opcional)

**Estimativa:** 3 horas
**Prioridade:** 🔴 HIGH
**Dependências:** Fase 3 completa

---

### Tarefa 4.2: Criar Guia de Tokens

**Descrição:** Documentar todos os tokens de design

**Arquivo:** `docs/design_system/TOKENS.md`

**Seções:**
- Cores (ColorPalette) - quando usar cada cor
- Tipografia (Typography) - escala de tipos
- Espaçamentos (Spacing) - baseline grid
- Dimensões (Dimensions) - tamanhos padronizados
- Elevation, Opacity, Transitions
- Exemplos de uso para cada categoria

**Critérios de Aceite:**
- [ ] Todas as categorias documentadas
- [ ] Exemplos de código para cada token
- [ ] Tabela de cores (visual)
- [ ] Tabela de tamanhos de fonte
- [ ] Quando usar cada um

**Estimativa:** 4 horas
**Prioridade:** 🔴 HIGH
**Dependências:** Tarefa 4.1

---

### Tarefa 4.3: Criar Guia de Componentes

**Descrição:** Documentar todos os componentes base

**Arquivo:** `docs/design_system/COMPONENTS.md`

**Seções:**
- StandardButton (variantes, parâmetros, exemplos)
- StandardLabel (variantes, exemplos)
- StandardInput, StandardSpinBox, etc.
- StandardGroupBox
- Screenshots de cada componente (opcional)
- Exemplos de código

**Critérios de Aceite:**
- [ ] Todos os componentes documentados
- [ ] Parâmetros explicados
- [ ] Variantes documentadas
- [ ] Exemplos de uso funcionando
- [ ] Referência cruzada com guia de tokens

**Estimativa:** 3 horas
**Prioridade:** 🔴 HIGH
**Dependências:** Tarefa 4.2

---

### Tarefa 4.4: Criar Guia de Migração

**Descrição:** Documentar processo de migração de código legado

**Arquivo:** `docs/design_system/MIGRATION.md`

**Seções:**
- Por que migrar
- Quando migrar (estratégia incremental)
- Passo a passo de migração
- Exemplos Before/After
- Checklist de validação
- Troubleshooting
- Padrões observados na migração dos 10 arquivos

**Critérios de Aceite:**
- [ ] Guia passo a passo claro
- [ ] 5+ exemplos Before/After
- [ ] Checklist de validação
- [ ] Seção de troubleshooting
- [ ] Padrões documentados

**Estimativa:** 3 horas
**Prioridade:** 🟡 MEDIUM
**Dependências:** Tarefa 4.3

---

### Tarefa 4.5: Atualizar CLAUDE.md e Finalizar

**Descrição:** Atualizar documentação principal e finalizar track

**Arquivos:**
- `CLAUDE.md` (adicionar seção "Design System")
- `conductor/tracks/design_system_20260119/plan.md` (marcar fase completa)
- `conductor/tracks.md` (registrar track completa)

**Atividades:**
- Adicionar seção "Design System" no CLAUDE.md
- Documentar como importar tokens
- Documentar como usar componentes base
- Adicionar exemplos rápidos
- Marcar Fase 4 como completa no plan.md
- Criar commit final: "feat(design-system): Complete - Design System v1.0 implemented"
- Atualizar tracks.md com status completo

**Critérios de Aceite:**
- [ ] CLAUDE.md atualizado com seção Design System
- [ ] Exemplos de uso funcionando
- [ ] Fase 4 marcada como completa
- [ ] Commit final criado
- [ ] tracks.md atualizado
- [ ] Zero tarefas pendentes

**Estimativa:** 2 horas
**Prioridade:** 🔴 HIGH
**Dependências:** Tarefa 4.4

---

## 📊 Resumo de Métricas

### Estimativa Geral
- **Total de Fases:** 4
- **Total de Tarefas:** 38
- **Estimativa Total:** 4-6 semanas (20-30 dias úteis)
- **Horas Estimadas:** ~100 horas

### Distribuição por Fase
- **Fase 1 (Fundação):** 13 tarefas, ~30 horas, Semanas 1-2
- **Fase 2 (Temas):** 8 tarefas, ~12.5 horas, Semana 3
- **Fase 3 (Migração):** 12 tarefas, ~24.5 horas, Semanas 4-5
- **Fase 4 (Documentação):** 5 tarefas, ~15 horas, Semana 6

### Critérios de Sucesso da Track

A track será considerada um sucesso quando:

1. ✅ Todas as 4 fases completadas (38/38 tarefas)
2. ✅ Design System implementado e funcional
3. ✅ 10 arquivos críticos migrados sem regressões
4. ✅ Documentação completa (4 guias + CLAUDE.md)
5. ✅ Zero hardcoded values nos arquivos migrados
6. ✅ Validação visual completa
7. ✅ Código seguindo SOLID (score >90/100)
8. ✅ Coverage >80% para código novo
9. ✅ Desenvolvedores conseguem usar em <5 minutos
10. ✅ Alterar cor primária afeta 100% dos componentes migrados

---

## 🎯 Checkpoints de Validação

### Checkpoint 1: Fase 1 Completa
- [ ] Design tokens implementados
- [ ] Stylesheet criado
- [ ] Componentes base criados
- [ ] Testes de tokens passando
- [ ] Commit criado

### Checkpoint 2: Fase 2 Completa
- [ ] ThemeManager funcionando
- [ ] Integrado com main_window.py
- [ ] Stylesheet global aplicado
- [ ] Validação visual OK
- [ ] Commit criado

### Checkpoint 3: Fase 3 Completa
- [ ] 10 arquivos migrados
- [ ] Validação visual OK
- [ ] Zero regressões
- [ ] Commit criado

### Checkpoint 4: Fase 4 Completa (Track Finalizada)
- [ ] Documentação completa
- [ ] CLAUDE.md atualizado
- [ ] Exemplos funcionando
- [ ] Commit final criado
- [ ] Track pronta para arquivo

---

**Plano v1.0 - 2026-01-19**
**Status:** ⏳ pronto para implementação
