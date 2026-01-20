# Proposta de Padrão Semântico - Dimensões de Botões

**Data:** 2026-01-20
**Versão:** 1.0.0
**Status:** Proposta
**Autor:** Design System Team

---

## 1. Resumo Executivo

Esta proposta define um padrão **semântico** para as dimensões dos botões na aplicação Tensiometro, baseado em análise de 20+ arquivos da codebase. O objetivo é garantir consistência visual enquanto mantém a flexibilidade necessária para diferentes contextos de uso em uma aplicação industrial.

### Princípios Fundamentais

1. **Semântica > Estética:** Tamanhos baseados em **função** e **contexto**, não apenas aparência
2. **Hierarquia Visual:** Tamanhos devem refletir importância e frequência de uso
3. **Acessibilidade:** Mínimo de 44×44px para touch targets (WCAG 2.5.5)
4. **Consistência:** Mesmo contexto = mesmas dimensões em toda aplicação
5. **Escalabilidade:** Sistema extensível para futuros componentes

---

## 2. Análise do Estado Atual

### 2.1 Padrões Identificados

| Contexto Semântico | Dimensões Atuais | Frequência | Problemas Identificados |
|-------------------|------------------|------------|------------------------|
| **Dialog - Primary** | 45-48px altura | Alta | Inconsistente (45px em login, 48px em outros) |
| **Dialog - Secondary** | 40-48px altura | Alta | Sem padrão claro |
| **Emergency/Stop** | 100×40px | Baixa | Largura fixa inconsistente |
| **Movement - Directional** | 50×50px | Média | Bom, mas não padronizado como token |
| **Movement - Z-axis** | 50×30px | Média | Específico, sem padrão definido |
| **Toolbar - Text** | 120px largura | Alta | Consistente, mas não documentado |
| **Toolbar - Icon** | 40×40px | Média | Tamanho arbitrário |
| **Inline Actions** | Variável | Alta | Sem padrão, muito inconsistente |
| **Table/List** | 32px altura | Média | Muito pequeno (abaixo de acessibilidade) |
| **Toggle/Status** | 32px altura | Média | Mesmo problema de acessibilidade |

### 2.2 Problemas Críticos

1. **Inconsistência:** Login usa 45px, outros diálogos usam 48px
2. **Acessibilidade:** Botões de 32px violam WCAG 2.5.5 (mínimo 44px)
3. **Hardcoded:** Muitos valores numéricos sem uso de tokens (`DIM.*`)
4. **Semântica ausente:** Tamanho baseado em "parece bom", não em função
5. **Documentação:** Padrões existentes não documentados

---

## 3. Proposta de Padrão Semântico

### 3.1 Sistema de Categorização

Botões serão categorizados por **5 dimensões semânticas**:

1. **Contexto de Uso** (Onde o botão vive?)
2. **Importância** (Quão crítica é a ação?)
3. **Frequência** (Com que frequência é usado?)
4. **Tipo de Conteúdo** (Texto, ícone, ambos?)
5. **Relação Espacial** (Está agrupado com outros botões?)

### 3.2 Matriz de Tamanhos Semânticos

#### **TABELA 1: Botões de Diálogo (Dialog Buttons)**

| Semântica | Tamanho | Dimensões | Tokens | Uso |
|----------|---------|-----------|--------|-----|
| **Dialog - Primary** | Extra Large | 48px altura × 120px largura (min) | `DIM.BUTTON_DIALOG_PRIMARY` | Ações principais: Salvar, Confirmar, OK |
| **Dialog - Secondary** | Large | 40px altura × 100px largura (min) | `DIM.BUTTON_DIALOG_SECONDARY` | Ações secundárias: Cancelar, Fechar |
| **Dialog - Tertiary** | Medium | 36px altura × 90px largura (min) | `DIM.BUTTON_DIALOG_TERTIARY` | Ações terciárias: Aplicar, Reset |
| **Dialog - Emergency** | Extra Large (Prominente) | 56px altura × 140px largura (min) | `DIM.BUTTON_EMERGENCY` | Emergências físicas: STOP, Emergency Stop |

**Regras:**
- Diálogos simples (1-2 campos): Primary + Secondary
- Diálogos complexos (Engineering Wizard): Primary + Secondary + Tertiary
- Diálogos críticos (Emergência): Apenas Emergency (超大 destaque)

---

#### **TABELA 2: Botões de Movimento (Movement Controls)**

| Semântica | Tamanho | Dimensões | Tokens | Uso |
|----------|---------|-----------|--------|-----|
| **Directional - D-Pad** | Square Large | 50×50px | `DIM.BUTTON_DIRECTIONAL` | Controles direcionais: ↑, ↓, ←, → |
| **Directional - Z-Axis** | Rectangular | 50×35px | `DIM.BUTTON_Z_AXIS` | Controles Z: Z+, Z- |
| **Function - Primary** | Medium | 40px altura × 100px largura (min) | `DIM.BUTTON_FUNCTION_PRIMARY` | Funções críticas: Home, Zero, Go To |
| **Function - Secondary** | Medium | 40px altura × 90px largura (min) | `DIM.BUTTON_FUNCTION_SECONDARY` | Funções auxiliares: Step/Continuous, Toggle |
| **Toggle - Status** | Small (Acessível) | 44×44px | `DIM.BUTTON_TOGGLE_STATUS` | Toggle de estado: Backlight, Mode |

**Regras:**
- Botões direcionais sempre quadrados (prevenir cliques acidentais)
- Z-axis retangular (economizar espaço vertical)
- Botões de função sempre com label textual claro
- Toggles indicam estado visualmente (cor + ícone)

---

#### **TABELA 3: Botões de Toolbar (Toolbar Buttons)**

| Semântica | Tamanho | Dimensões | Tokens | Uso |
|----------|---------|-----------|--------|-----|
| **Toolbar - Text** | Medium | 36px altura × 120px largura (min) | `DIM.BUTTON_TOOLBAR_TEXT` | Texto + ícone opcional: Anterior, Próximo |
| **Toolbar - Icon** | Square Medium | 40×40px | `DIM.BUTTON_TOOLBAR_ICON` | Apenas ícone: Refresh, Clear, Add |
| **Toolbar - Icon-Large** | Square Large | 48×48px | `DIM.BUTTON_TOOLBAR_ICON_LARGE` | Ícone destaque: New, Open, Save |

**Regras:**
- Toolbar horizontal: usar 36px altura (economizar espaço vertical)
- Toolbar vertical: usar 40-48px largura (botões quadrados)
- Botões com texto: sempre mínimo 120px largura
- Botões ícone apenas: sempre quadrados (prevenir distorção)

---

#### **TABELA 4: Botões Inline (Inline Action Buttons)**

| Semântica | Tamanho | Dimensões | Tokens | Uso |
|----------|---------|-----------|--------|-----|
| **Inline - Primary** | Medium | 36px altura × auto largura | `DIM.BUTTON_INLINE_PRIMARY` | Ações em formulários: Capturar, Calcular |
| **Inline - Secondary** | Small | 32px altura × auto largura | `DIM.BUTTON_INLINE_SECONDARY` | Ações auxiliares: Limpar, Reset |
| **Inline - Compact** | Compact | 28px altura × auto largura | `DIM.BUTTON_INLINE_COMPACT` | Ações compactas: Edit, Delete (em tabelas) |

**Regras:**
- Botões inline sempre ajustam largura ao conteúdo (`auto`)
- Nunca usar botões compactos (<32px) como única ação
- Ações críticas em inline devem usar `inline-primary` (36px)
- Ações destrutivas devem terConfirmation Dialog

---

#### **TABELA 5: Botões de Grid/Table (Grid Action Buttons)**

| Semântica | Tamanho | Dimensões | Tokens | Uso |
|----------|---------|-----------|--------|-----|
| **Grid - Action** | Small (Acessível) | 44px altura × 80px largura (min) | `DIM.BUTTON_GRID_ACTION` | Ações em linhas: Edit, Delete, View |
| **Grid - Status** | Badge Clickable | 24px altura × auto largura | `DIM.BUTTON_GRID_STATUS` | Status clicável: Badges, Flags |

**Regras:**
- **CRÍTICO:** Mínimo 44px altura para WCAG 2.5.5 (touch target)
- Grid actions nunca <44px (mesmo que pareça "grande")
- Status badges são clicáveis mas visualmente distinctivos de botões
- Grid actions devem ter tooltip em hover

---

### 3.3 Sistema de Tokens Proposto

#### **Adições ao `design_tokens.py` (Dimensions class)**

```python
@dataclass(frozen=True)
class Dimensions:
    """
    Dimensões padrão para componentes e layouts

    Atualizado v1.1: Sistema semântico de botões
    """

    # =========================================================================
    # BUTTON HEIGHTS (Genéricos - BACKWARD COMPAT)
    # =========================================================================

    BUTTON_HEIGHT_SM: int = 32  # [DEPRECATED] Use BUTTON_INLINE_COMPACT
    """Altura de botão pequeno - [LEGADO] será removido em v0.6.0"""

    BUTTON_HEIGHT_MD: int = 40  # [DEPRECATED] Use BUTTON_DIALOG_SECONDARY
    """Altura de botão médio (padrão) - [LEGADO] use específico"""

    BUTTON_HEIGHT_LG: int = 48  # [DEPRECATED] Use BUTTON_DIALOG_PRIMARY
    """Altura de botão grande - [LEGADO] use específico"""

    # =========================================================================
    # DIALOG BUTTONS (Novo Sistema Semântico)
    # =========================================================================

    # Botão Primário de Dialog
    BUTTON_DIALOG_PRIMARY_HEIGHT: int = 48
    """Altura de botão primário em dialogs"""
    BUTTON_DIALOG_PRIMARY_MIN_WIDTH: int = 120
    """Largura mínima de botão primário em dialogs"""

    # Botão Secundário de Dialog
    BUTTON_DIALOG_SECONDARY_HEIGHT: int = 40
    """Altura de botão secundário em dialogs"""
    BUTTON_DIALOG_SECONDARY_MIN_WIDTH: int = 100
    """Largura mínima de botão secundário em dialogs"""

    # Botão Terciário de Dialog
    BUTTON_DIALOG_TERTIARY_HEIGHT: int = 36
    """Altura de botão terciário em dialogs"""
    BUTTON_DIALOG_TERTIARY_MIN_WIDTH: int = 90
    """Largura mínima de botão terciário em dialogs"""

    # Botão de Emergência
    BUTTON_EMERGENCY_HEIGHT: int = 56
    """Altura de botão de emergência (prominente)"""
    BUTTON_EMERGENCY_MIN_WIDTH: int = 140
    """Largura mínima de botão de emergência"""
    BUTTON_EMERGENCY_PADDING: tuple = (15, 40)
    """Padding vertical/horizontal de botão de emergência"""

    # =========================================================================
    # MOVEMENT CONTROL BUTTONS
    # =========================================================================

    # Controles Direcionais (D-Pad)
    BUTTON_DIRECTIONAL_SIZE: int = 50
    """Tamanho de botão direcional (quadrado)"""

    # Controles de Eixo Z
    BUTTON_Z_AXIS_WIDTH: int = 50
    """Largura de botão de eixo Z"""
    BUTTON_Z_AXIS_HEIGHT: int = 35
    """Altura de botão de eixo Z"""

    # Botões de Função
    BUTTON_FUNCTION_PRIMARY_HEIGHT: int = 40
    """Altura de botão de função primária"""
    BUTTON_FUNCTION_PRIMARY_MIN_WIDTH: int = 100
    """Largura mínima de botão de função primária"""

    BUTTON_FUNCTION_SECONDARY_HEIGHT: int = 40
    """Altura de botão de função secundária"""
    BUTTON_FUNCTION_SECONDARY_MIN_WIDTH: int = 90
    """Largura mínima de botão de função secundária"""

    # Botões Toggle de Status
    BUTTON_TOGGLE_STATUS_SIZE: int = 44
    """Tamanho de botão toggle de status (quadrado, acessível)"""

    # =========================================================================
    # TOOLBAR BUTTONS
    # =========================================================================

    # Toolbar com Texto
    BUTTON_TOOLBAR_TEXT_HEIGHT: int = 36
    """Altura de botão de toolbar com texto"""
    BUTTON_TOOLBAR_TEXT_MIN_WIDTH: int = 120
    """Largura mínima de botão de toolbar com texto"""

    # Toolbar com Ícone
    BUTTON_TOOLBAR_ICON_SIZE: int = 40
    """Tamanho de botão de toolbar com ícone (quadrado)"""
    BUTTON_TOOLBAR_ICON_LARGE_SIZE: int = 48
    """Tamanho de botão de toolbar com ícone grande (quadrado)"""

    # =========================================================================
    # INLINE ACTION BUTTONS
    # =========================================================================

    # Inline Primário
    BUTTON_INLINE_PRIMARY_HEIGHT: int = 36
    """Altura de botão inline primário"""
    BUTTON_INLINE_PRIMARY_MIN_WIDTH: int = 80
    """Largura mínima de botão inline primário"""

    # Inline Secundário
    BUTTON_INLINE_SECONDARY_HEIGHT: int = 32
    """Altura de botão inline secundário"""
    BUTTON_INLINE_SECONDARY_MIN_WIDTH: int = 70
    """Largura mínima de botão inline secundário"""

    # Inline Compacto
    BUTTON_INLINE_COMPACT_HEIGHT: int = 28
    """Altura de botão inline compacto [CUIDADO: usar com moderação]"""
    BUTTON_INLINE_COMPACT_MIN_WIDTH: int = 60
    """Largura mínima de botão inline compacto"""

    # =========================================================================
    # GRID/TABLE ACTION BUTTONS
    # =========================================================================

    # Grid Actions (Edit, Delete, View)
    BUTTON_GRID_ACTION_HEIGHT: int = 44  # WCAG 2.5.5 compliant
    """Altura de botão de ação em grid (mínimo acessível)"""
    BUTTON_GRID_ACTION_MIN_WIDTH: int = 80
    """Largura mínima de botão de ação em grid"""

    # Grid Status (Clickable Badges)
    BUTTON_GRID_STATUS_HEIGHT: int = 24
    """Altura de badge clicável de status"""
```

---

## 4. Diretrizes de Uso

### 4.1 Quando Usar Cada Tamanho

#### **Dialog - Primary (48×120px)**

**Usar para:**
- ✅ Ação principal de um dialog (Salvar, Confirmar, OK)
- ✅ Último passo de um wizard (Concluir, Finish)
- ✅ Ações irreversíveis (Delete, Remove)

**NÃO usar para:**
- ❌ Ações secundárias (Cancelar, Fechar)
- ❌ Ações destrutivas sem confirmação
- ❌ Botões inline em formulários

---

#### **Dialog - Secondary (40×100px)**

**Usar para:**
- ✅ Ações de cancelamento (Cancelar, Close)
- ✅ Ações alternativas (Apply, Reset)
- ✅ Navegação em wizards (Anterior, Próximo)

**NÃO usar para:**
- ❌ Ação principal do dialog
- ❌ Ações críticas ou irreversíveis

---

#### **Movement - Directional (50×50px)**

**Usar para:**
- ✅ Controles direcionais (↑, ↓, ←, →)
- ✅ Controles de jog precisos
- ✅ Interfaces onde erro é caro (movimento de CNC)

**NÃO usar para:**
- ❌ Botões com texto (não cabe)
- ❌ Botões de função (Home, Zero)
- ❌ Interfaces touch-oriented (precisam ser maiores)

---

#### **Movement - Z-Axis (50×35px)**

**Usar para:**
- ✅ Controles específicos de eixo Z (Z+, Z-)
- ✅ Onde economia de vertical é crítica

**NÃO usar para:**
- ❌ Controles X/Y (devem ser quadrados)
- ❌ Botões com texto longo

---

#### **Toolbar - Text (36×120px)**

**Usar para:**
- ✅ Botões de navegação (Anterior, Próximo)
- ✅ Ações principais em toolbar (Novo, Abrir, Salvar)
- ✅ Onde espaço vertical é limitado

**NÃO usar para:**
- ❌ Botões com ícone apenas (use toolbar-icon)
- ❌ Botões de diálogo principal (use dialog-primary)

---

#### **Toolbar - Icon (40×40px)**

**Usar para:**
- ✅ Ações com ícone reconhecível (Refresh, Clear)
- ✅ Toolbars densas com muitos botões
- ✅ Ações secundárias de rápida execução

**NÃO usar para:**
- ❌ Ações críticas (precisam de texto)
- ❌ Botões sem ícone (use toolbar-text)

---

#### **Inline - Primary (36px altura × auto largura)**

**Usar para:**
- ✅ Ações principais em formulários (Capturar, Calcular)
- ✅ Botões ao lado de inputs
- ✅ Onde contexto local já é claro

**NÃO usar para:**
- ❌ Única ação de uma seção (use button maior)
- ❌ Ações destrutivas sem confirmação

---

#### **Grid - Action (44×80px)**

**Usar para:**
- ✅ Ações em linhas de tabela (Edit, Delete, View)
- ✅ Onde many actions aparecem juntas
- ✅ Criticamente: nunca <44px (WCAG 2.5.5)

**NÃO usar para:**
- ❌ Status badges (use grid-status)
- ❌ Botões fora de grid/table

---

### 4.2 Regras de Composição

#### **Regra 1: Hierarquia Visual**

Botões maiores = mais importantes. Sempre.

```
[Emergência 56px] > [Dialog Primary 48px] > [Dialog Secondary 40px] > [Inline 36px] > [Compact 28px]
```

#### **Regra 2: Consistência de Contexto**

Mesmo contexto = mesmo tamanho.

```python
# ❌ ERRADO - Inconsistente
dialog = QDialog()
save_btn = QPushButton("Salvar")
save_btn.setMinimumHeight(48)  # 48px

cancel_btn = QPushButton("Cancelar")
cancel_btn.setMinimumHeight(40)  # 40px - inconsistente!

# ✅ CORRETO - Consistente
from consumo_lib.ui.widget_standards import StandardButton
from consumo_lib.ui import DIM

dialog = QDialog()
save_btn = StandardButton("Salvar", variant="primary-green")
save_btn.setMinimumHeight(DIM.BUTTON_DIALOG_PRIMARY_HEIGHT)  # 48px

cancel_btn = StandardButton("Cancelar", variant="secondary")
cancel_btn.setMinimumHeight(DIM.BUTTON_DIALOG_SECONDARY_HEIGHT)  # 40px
```

#### **Regra 3: Acessibilidade Primeiro**

Nunca usar botões <44px como única ação.

```python
# ❌ ERRADO - Acessibilidade violada
edit_btn = QPushButton("✏️")
edit_btn.setFixedSize(32, 32)  # 32×32px - viola WCAG 2.5.5!

# ✅ CORRETO - Acessível
edit_btn = QPushButton("✏️ Editar")
edit_btn.setMinimumSize(80, 44)  # 80×44px - WCAG compliant
```

#### **Regra 4: Largura Auto para Inline**

Botões inline sempre ajustam ao conteúdo.

```python
# ✅ CORRETO - Largura auto
capture_btn = StandardButton("📍 Capturar", variant="primary")
capture_btn.setMinimumHeight(DIM.BUTTON_INLINE_PRIMARY_HEIGHT)  # 36px
# Largura = auto (ajusta ao texto + ícone + padding)
```

---

## 5. Plano de Migração

### 5.1 Fase 1: Atualizar Tokens (Priority: HIGH)

**Arquivo:** `consumo_lib/ui/design_tokens.py`

**Ações:**
1. Adicionar novos tokens semânticos (seção 3.3)
2. Marcar tokens legados como `[DEPRECATED]`
3. Adicionar docstrings explicando semântica

**Timeline:** 1 dia
**Risco:** Baixo (aditivo, backward compatible)

---

### 5.2 Fase 2: Atualizar StandardButton (Priority: HIGH)

**Arquivo:** `consumo_lib/ui/widget_standards.py`

**Ações:**
1. Adicionar parâmetro `semantic_size` ao `StandardButton`
2. Mapear `semantic_size` para tokens apropriados
3. Manter `size` (sm/md/lg) como backward compatible

**Exemplo:**

```python
class StandardButton(QPushButton):
    def __init__(
        self,
        text: str,
        variant: str = "primary-green",
        size: str = "md",  # [DEPRECATED] Use semantic_size
        semantic_size: str | None = None,  # NOVO
        parent: None
    ):
        super().__init__(text, parent)

        # Mapeamento semântico
        if semantic_size == "dialog-primary":
            height = DIM.BUTTON_DIALOG_PRIMARY_HEIGHT
            min_width = DIM.BUTTON_DIALOG_PRIMARY_MIN_WIDTH
        elif semantic_size == "dialog-secondary":
            height = DIM.BUTTON_DIALOG_SECONDARY_HEIGHT
            min_width = DIM.BUTTON_DIALOG_SECONDARY_MIN_WIDTH
        # ... etc

        # Fallback para size (sm/md/lg) se semantic_size não fornecido
        elif size == "sm":
            height = DIM.BUTTON_HEIGHT_SM
            # ...
```

**Timeline:** 2 dias
**Risco:** Baixo (aditivo, backward compatible)

---

### 5.3 Fase 3: Migrar Diálogos Críticos (Priority: HIGH)

**Arquivos:**
- `consumo_lib/dialogs/login_dialog.py`
- `consumo_lib/dialogs/engineering_wizard_dialog.py`
- `consumo_lib/dialogs/auth_settings_dialog.py`
- `consumo_lib/dialogs/confirm_positioning_dialog.py`

**Ações:**
1. Substituir `setMinimumHeight(45)` por `DIM.BUTTON_DIALOG_PRIMARY_HEIGHT`
2. Usar `StandardButton` com `semantic_size="dialog-primary"`
3. Garantir consistência em todos os diálogos

**Exemplo de migração:**

```python
# ❌ ANTES (Hardcoded)
ok_btn = QPushButton("OK")
ok_btn.setMinimumHeight(45)
ok_btn.setMinimumWidth(120)

# ✅ DEPOIS (Semantic)
ok_btn = StandardButton("OK", variant="primary-green", semantic_size="dialog-primary")
```

**Timeline:** 3 dias
**Risco:** Médio (mudança visual, mas melhora consistência)

---

### 5.4 Fase 4: Migrar Controles de Movimento (Priority: MEDIUM)

**Arquivos:**
- `consumo_lib/widgets/movement_control.py`
- `consumo_lib/tabs/cnc_control_tab.py`

**Ações:**
1. Padronizar botões direcionais com `DIM.BUTTON_DIRECTIONAL_SIZE`
2. Padronizar botões Z-axis com `DIM.BUTTON_Z_AXIS_WIDTH/HEIGHT`
3. Usar `semantic_size="function-primary"` para botões de função

**Exemplo de migração:**

```python
# ❌ ANTES
self.up_button = QPushButton("↑")
self.up_button.setMinimumSize(50, 50)  # Hardcoded

# ✅ DEPOIS
from consumo_lib.ui import DIM

self.up_button = QPushButton("↑")
self.up_button.setMinimumSize(
    DIM.BUTTON_DIRECTIONAL_SIZE,
    DIM.BUTTON_DIRECTIONAL_SIZE
)
```

**Timeline:** 2 dias
**Risco:** Baixo (melhoria de consistência)

---

### 5.5 Fase 5: Migrar Toolbars e Inline Actions (Priority: LOW)

**Arquivos:** Múltiplos (10+ arquivos)

**Ações:**
1. Identificar todos os botões de toolbar
2. Migrar para `semantic_size="toolbar-text"` ou `"toolbar-icon"`
3. Migrar botões inline para `semantic_size="inline-primary"`

**Timeline:** 5 dias
**Risco:** Baixo (mudanças localizadas)

---

### 5.6 Fase 6: Atualizar Documentação (Priority: MEDIUM)

**Arquivos:**
- `docs/design_system/README.md`
- `docs/design_system/COMPONENTS.md`
- `docs/design_system/TOKENS.md`

**Ações:**
1. Adicionar seção "Button Sizes - Semantic System"
2. Documentar quando usar cada `semantic_size`
3. Adicionar exemplos visuais (screenshots)
4. Criar guia de migração para developers

**Timeline:** 2 dias
**Risco:** Nenhum (documentação apenas)

---

### 5.7 Fase 7: Remover Tokens Legados (Priority: LOW)

**Arquivo:** `consumo_lib/ui/design_tokens.py`

**Ações:**
1. Remover `BUTTON_HEIGHT_SM/MD/LG` (marcar como obsoletos)
2. Forçar uso de `semantic_size` em `StandardButton`
3. Atualizar todos os exemplos de código

**Timeline:** Futuro (v0.6.0+)
**Risco:** Alto (breaking change)

---

## 6. Exemplos de Uso

### 6.1 Dialog Padrão

```python
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout
from consumo_lib.ui.widget_standards import StandardButton
from consumo_lib.ui import DIM, SPACE

class ConfirmDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setSpacing(SPACE.MD)

        # ... adicionar conteúdo do dialog ...

        # Botões (usando StandardButton com semantic_size)
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # Botão primário (Salvar)
        save_btn = StandardButton(
            "Salvar",
            variant="primary-green",
            semantic_size="dialog-primary"  # 48×120px
        )
        save_btn.clicked.connect(self.accept)

        # Botão secundário (Cancelar)
        cancel_btn = StandardButton(
            "Cancelar",
            variant="secondary",
            semantic_size="dialog-secondary"  # 40×100px
        )
        cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)
```

---

### 6.2 Movement Control Widget

```python
from PyQt6.QtWidgets import QPushButton, QGridLayout
from consumo_lib.ui import DIM, TYPO

class MovementControls(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QGridLayout(self)

        # Botões direcionais (50×50px)
        self.up_button = QPushButton("↑")
        self._setup_directional_button(self.up_button)
        self.up_button.pressed.connect(lambda: self._move("Y", -1))

        self.down_button = QPushButton("↓")
        self._setup_directional_button(self.down_button)
        self.down_button.pressed.connect(lambda: self._move("Y", 1))

        # Layout em D-Pad
        layout.addWidget(self.up_button, 0, 1)
        layout.addWidget(self.down_button, 2, 1)

    def _setup_directional_button(self, btn: QPushButton):
        """Configura botão direcional com tamanho padrão"""
        btn.setMinimumSize(
            DIM.BUTTON_DIRECTIONAL_SIZE,  # 50px
            DIM.BUTTON_DIRECTIONAL_SIZE   # 50px
        )
        font = TYPO.get_font(16, weight=TYPO.BOLD)
        btn.setFont(font)
```

---

### 6.3 Toolbar com Botões

```python
from PyQt6.QtWidgets import QHBoxLayout
from consumo_lib.ui.widget_standards import StandardButton
from consumo_lib.ui import DIM, SPACE

class Toolbar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setSpacing(SPACE.SM)
        layout.setContentsMargins(SPACE.SM, SPACE.SM, SPACE.SM, SPACE.SM)

        # Botão com texto (36×120px)
        new_btn = StandardButton(
            "Novo",
            variant="primary-blue",
            semantic_size="toolbar-text"
        )
        layout.addWidget(new_btn)

        # Botão ícone (40×40px)
        refresh_btn = QPushButton("🔄")
        refresh_btn.setMinimumSize(
            DIM.BUTTON_TOOLBAR_ICON_SIZE,
            DIM.BUTTON_TOOLBAR_ICON_SIZE
        )
        layout.addWidget(refresh_btn)

        layout.addStretch()
```

---

## 7. Validação

### 7.1 Checklist de Implementação

Para cada botão na aplicação, verificar:

- [ ] O botão tem um **contexto semântico claro**?
- [ ] O tamanho está **definido por token** (`DIM.BUTTON_*`), não hardcoded?
- [ ] O tamanho **respeita a hierarquia visual** (mais importante = maior)?
- [ ] O botão é **acessível** (≥44px para touch targets)?
- [ ] O botão é **consistente** com outros botões do mesmo contexto?
- [ ] O tamanho está **documentado** em `COMPONENTS.md`?

---

### 7.2 Testes de Aceitação

**Teste 1: Consistência de Diálogos**
- Abrir todos os diálogos principais
- Verificar se botões OK/Save têm mesmo tamanho (48px altura)
- Verificar se botões Cancel têm mesmo tamanho (40px altura)

**Teste 2: Acessibilidade**
- Medir todos os botões <44px
- Confirmar que são usados apenas em grupos (nunca sozinhos)
- Verificar se há tooltip para botões ícone-only

**Teste 3: Movimento**
- Verificar botões direcionais são 50×50px
- Verificar botões Z-axis são 50×35px
- Verificar botões de função têm largura mínima adequada

---

## 8. Referências

### 8.1 Padrões Externos

- **Material Design 3: Buttons**
  - URL: https://m3.material.io/components/buttons/overview
  - Referência para estados, variantes, hierarchy

- **WCAG 2.1: 2.5.5 Target Size**
  - URL: https://www.w3.org/WAI/WCAG21/Understanding/target-size.html
  - Referência para touch targets (44×44px mínimo)

- **Apple HIG: Buttons**
  - URL: https://developer.apple.com/design/human-interface-guidelines/components/buttons-and-controls/buttons
  - Referência para semântica de tamanhos

### 8.2 Documentação Interna

- `docs/design_system/README.md` - Visão geral do Design System
- `docs/design_system/TOKENS.md` - Referência completa de tokens
- `docs/design_system/COMPONENTS.md` - Componentes base
- `docs/design_system/COLOR_PROPOSAL.md` - Proposta de cores v2.1

---

## 9. Apêndice: Mapeamento Completo

### A. Tabela de Mapeamento: Legado → Semântico

| Legado | Semântico Proposto | Tokens |
|--------|-------------------|--------|
| `setMinimumHeight(45)` | `semantic_size="dialog-primary"` | `DIM.BUTTON_DIALOG_PRIMARY_HEIGHT` (48px) |
| `setMinimumHeight(40)` | `semantic_size="dialog-secondary"` | `DIM.BUTTON_DIALOG_SECONDARY_HEIGHT` (40px) |
| `setMinimumSize(50, 50)` | `semantic_size="directional"` | `DIM.BUTTON_DIRECTIONAL_SIZE` (50px) |
| `setMinimumSize(50, 30)` | `semantic_size="z-axis"` | `DIM.BUTTON_Z_AXIS_*` (50×35px) |
| `setMinimumWidth(120)` | `semantic_size="toolbar-text"` | `DIM.BUTTON_TOOLBAR_TEXT_*` (36×120px) |
| `setMaximumWidth(40)` | `semantic_size="toolbar-icon"` | `DIM.BUTTON_TOOLBAR_ICON_SIZE` (40px) |

### B. Tabela de Decisão: Qual Tamanho Usar?

```
START
│
├─ Botão está em DIALOG?
│   ├─ Sim → Ação é PRIMÁRIA?
│   │   ├─ Sim → dialog-primary (48×120px)
│   │   └─ Não → dialog-secondary (40×100px)
│   │
│   └─ Não → Continua...
│
├─ Botão é de MOVIMENTO?
│   ├─ Sim → É DIRECIONAL (↑↓←→)?
│   │   ├─ Sim → directional (50×50px)
│   │   └─ Não → É Z-AXIS?
│   │       ├─ Sim → z-axis (50×35px)
│   │       └─ Não → function-primary (40×100px)
│   │
│   └─ Não → Continua...
│
├─ Botão está em TOOLBAR?
│   ├─ Sim → Tem TEXTO?
│   │   ├─ Sim → toolbar-text (36×120px)
│   │   └─ Não → toolbar-icon (40×40px)
│   │
│   └─ Não → Continua...
│
├─ Botão é INLINE (em formulário)?
│   ├─ Sim → Ação é PRINCIPAL?
│   │   ├─ Sim → inline-primary (36px altura)
│   │   └─ Não → inline-secondary (32px altura)
│   │
│   └─ Não → Continua...
│
└─ Botão está em GRID/TABLE?
    └─ Sim → grid-action (44×80px) [WCAG compliant]
```

---

## 10. Conclusão

Esta proposta estabelece um **sistema semântico** para dimensões de botões que garante:

✅ **Consistência visual** em toda aplicação
✅ **Acessibilidade** WCAG 2.1 compliant
✅ **Flexibilidade** para diferentes contextos
✅ **Escalabilidade** para futuros componentes
✅ **Clareza** na escolha do tamanho certo

**Próximos passos:**
1. Review com equipe de desenvolvimento
2. Implementação Fase 1 (tokens)
3. Piloto em 2-3 diálogos críticos
4. Validação visual e de acessibilidade
5. Migração gradual restante da aplicação

---

**Documento aprovado por:** Design System Team
**Data de aprovação:** Pendente
**Versão final:** 1.0.0
