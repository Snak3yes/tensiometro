# Design Tokens - Referência Completa

Guia completo de todos os design tokens disponíveis no Tensiometro Design System.

## 📋 Índice

- [O que são Design Tokens](#o-que-são-design-tokens)
- [Como Importar](#como-importar)
- [Cores (ColorPalette)](#cores-colorpalette)
- [Tipografia (Typography)](#tipografia-typography)
- [Espaçamentos (Spacing)](#espaçamentos-spacing)
- [Dimensões (Dimensions)](#dimensões-dimensions)
- [Elevação (Elevation)](#elevação-elevation)
- [Opacidade (Opacity)](#opacidade-opacity)
- [Transições (Transitions)](#transições-transitions)
- [Breakpoints (Breakpoints)](#breakpoints-breakpoints)
- [Acessibilidade (Accessibility)](#acessibilidade-accessibility)

---

## O que são Design Tokens

Design tokens são variáveis que armazenam valores visuais (cores, tamanhos, espaçamentos) como **constantes nomeadas**.

**Benefícios**:
- ✅ Single source of truth
- ✅ Type-safe (não são strings mágicas)
- ✅ Fácil refatoração
- ✅ Autocompletção no IDE

---

## Como Importar

```python
# Importar todos os tokens
from consumo_lib.ui import COLORS, TYPO, SPACE, DIM, ELEV, OPAC, TRANS, BREAK, A11Y

# Importar tokens específicos
from consumo_lib.ui import COLORS, TYPO, SPACE

# Importar do módulo diretamente
from consumo_lib.ui.design_tokens import ColorPalette, Typography
```

---

## Cores (ColorPalette)

Baseado em **Material Design 3** com cores específicas do domínio.

### Importar

```python
from consumo_lib.ui import COLORS
```

### Cores Primárias (Verde - Success/Action)

| Token | Hex | Uso |
|-------|-----|-----|
| `COLORS.PRIMARY` | `#4CAF50` | Ações principais, botões primários |
| `COLORS.PRIMARY_DARK` | `#388E3C` | Hover states, bordas |
| `COLORS.PRIMARY_LIGHT` | `#81C784` | Backgrounds, overlays |
| `COLORS.ON_PRIMARY` | `#FFFFFF` | Texto/símbolos sobre PRIMARY |

**Exemplo**:
```python
btn.setStyleSheet(f"background-color: {COLORS.PRIMARY};")
btn.setStyleSheet(f"color: {COLORS.ON_PRIMARY};")
```

### Cores Secundárias (Azul - Information)

| Token | Hex | Uso |
|-------|-----|-----|
| `COLORS.SECONDARY` | `#2196F3` | Informações, ações secundárias |
| `COLORS.SECONDARY_DARK` | `#1976D2` | Hover states |
| `COLORS.SECONDARY_LIGHT` | `#64B5F6` | Backgrounds |
| `COLORS.ON_SECONDARY` | `#FFFFFF` | Texto sobre SECONDARY |

### Cores de Status (Semânticas)

| Token | Hex | Uso |
|-------|-----|-----|
| `COLORS.SUCCESS` | `#2ecc71` | Sucesso, confirmações |
| `COLORS.WARNING` | `#f1c40f` | Avisos, atenção |
| `COLORS.WARNING_DARK` | `#f39c12` | Avisos urgentes |
| `COLORS.ERROR` | `#e74c3c` | Erros, falhas críticas |
| `COLORS.ERROR_DARK` | `#c0392b` | Borda de erros |

### Cores de Status do Domínio (Inspeção)

| Token | Hex | Uso |
|-------|-----|-----|
| `COLORS.STATUS_APPROVED_AUTO` | `#4CAF50` | Aprovado automaticamente |
| `COLORS.STATUS_APPROVED_USER` | `#CDDC39` | Aprovado manualmente |
| `COLORS.STATUS_REJECTED` | `#F44336` | Reprovado na inspeção |
| `COLORS.STATUS_PENDING` | `#9E9E9E` | Pendente de inspeção |
| `COLORS.STATUS_IN_PROGRESS` | `#2196F3` | Em andamento |

**Exemplo**:
```python
# Em StatusBadge
STATUS_COLORS = {
    "approved_auto": COLORS.STATUS_APPROVED_AUTO,
    "approved_user": COLORS.STATUS_APPROVED_USER,
    "rejected": COLORS.STATUS_REJECTED,
    "pending": COLORS.STATUS_PENDING,
    "in_progress": COLORS.SECONDARY,
}
```

### Cores Neutras

| Token | Hex | Uso |
|-------|-----|-----|
| `COLORS.BACKGROUND` | `#FFFFFF` | Background principal |
| `COLORS.SURFACE` | `#F5F5F5` | Superfícies secundárias |
| `COLORS.SURFACE_VARIANT` | `#EEEEEE` | Cards, containers |
| `COLORS.ON_BACKGROUND` | `#212121` | Texto sobre background |
| `COLORS.ON_SURFACE` | `#424242` | Texto sobre superfícies |
| `COLORS.OUTLINE` | `#E0E0E0` | Bordas, divisores |
| `COLORS.DISABLED` | `#9E9E9E` | Estados desabilitados |

### Métodos Úteis

```python
# Converter para QColor do Qt
qcolor = COLORS.to_qcolor(COLORS.PRIMARY)

# Obter cor de status
status_color = COLORS.get_status_color("approved_auto")  # Retorna COLORS.STATUS_APPROVED_AUTO
```

---

## Tipografia (Typography)

Sistema de tipos baseado em **Material Design 3** type scale.

### Importar

```python
from consumo_lib.ui import TYPO
```

### Font Families

| Token | Valor | Uso |
|-------|-------|-----|
| `TYPO.FONT_FAMILY` | `"Arial"` | Fonte padrão |
| `TYPO.FONT_FAMILY_MONOSPACE` | `"Consolas"` | Código, técnicos |

### Type Scale (Tamanhos)

#### Display Styles (Hero/Marketing)

| Token | Tamanho | Uso |
|-------|---------|-----|
| `TYPO.DISPLAY_LARGE` | 57px | Títulos hero (raro) |
| `TYPO.DISPLAY_MEDIUM` | 45px | Títulos de seção muito grandes |
| `TYPO.DISPLAY_SMALL` | 36px | Subtítulos grandes |

#### Headline Styles

| Token | Tamanho | Uso |
|-------|---------|-----|
| `TYPO.HEADLINE_LARGE` | 32px | Títulos de dialogs grandes |
| `TYPO.HEADLINE_MEDIUM` | 28px | Títulos de dialogs padrão |
| `TYPO.HEADLINE_SMALL` | 24px | Títulos de seção |

#### Title Styles

| Token | Tamanho | Uso |
|-------|---------|-----|
| `TYPO.TITLE_LARGE` | 22px | Títulos de blocos grandes |
| `TYPO.TITLE_MEDIUM` | 16px | Títulos de widgets |
| `TYPO.TITLE_SMALL` | 14px | Subtítulos |

#### Body Styles

| Token | Tamanho | Uso |
|-------|---------|-----|
| `TYPO.BODY_LARGE` | 16px | Botões, labels importantes |
| `TYPO.BODY_MEDIUM` | 14px | Texto padrão da aplicação |
| `TYPO.BODY_SMALL` | 12px | Texto secundário |

#### Label Styles

| Token | Tamanho | Uso |
|-------|---------|-----|
| `TYPO.LABEL_LARGE` | 14px | Labels de formulários importantes |
| `TYPO.LABEL_MEDIUM` | 12px | Labels de formulários padrão |
| `TYPO.LABEL_SMALL` | 11px | Captions, badges |

### Métodos Úteis

```python
# Criar QFont com tamanho e estilo
font = TYPO.get_font(14)  # Tamanho 14, regular
font = TYPO.get_font(TYPO.BODY_MEDIUM, bold=True)  # 14px, bold
font = TYPO.get_font(16, bold=True, italic=True)  # 16px, bold + italic

# Aplicar a widget
label.setFont(TYPO.get_font(TYPO.HEADLINE_SMALL, bold=True))
```

---

## Espaçamentos (Spacing)

Sistema de espaçamento baseado em **grid de 4px** (baseline grid).

### Importar

```python
from consumo_lib.ui import SPACE
```

### Escala de Espaçamentos

| Token | Pixels | Multiplicador | Uso |
|-------|--------|---------------|-----|
| `SPACE.BASE` | 4px | 1× | Unidade base |
| `SPACE.XS` | 4px | 1× | Espaçamento mínimo |
| `SPACE.SM` | 8px | 2× | Elementos relacionados próximos |
| `SPACE.MD` | 16px | 4× | Padrão de espaçamento |
| `SPACE.LG` | 24px | 6× | Seções distintas |
| `SPACE.XL` | 32px | 8× | Grandes seções |
| `SPACE.XXL` | 48px | 12× | Separações muito grandes |

### Paddings Contextuais

| Token | Vertical | Horizontal | Uso |
|-------|----------|------------|-----|
| `SPACE.PADDING_TIGHT` | 8px | 12px | Elementos compactos |
| `SPACE.PADDING_NORMAL` | 12px | 16px | Padrão |
| `SPACE.PADDING_SPACIOUS` | 16px | 24px | Elementos arejados |

### Margins Contextuais

| Token | Valor | Uso |
|-------|-------|-----|
| `SPACE.MARGIN_TIGHT` | 8px | Margens compactas |
| `SPACE.MARGIN_NORMAL` | 16px | Margens padrão |
| `SPACE.MARGIN_SPACIOUS` | 24px | Margens largas |

**Exemplos**:

```python
# Em layouts
layout.setSpacing(SPACE.MD)  # 16px entre widgets
layout.setContentsMargins(SPACE.LG, SPACE.MD, SPACE.LG, SPACE.MD)

# Em stylesheets
widget.setStyleSheet(f"padding: {SPACE.SM}px {SPACE.MD}px;")

# Com helpers
from consumo_lib.ui.helpers import add_spacing
add_spacing(layout, SPACE.LG)  # Adiciona espaçamento
```

---

## Dimensões (Dimensions)

Dimensões padronizadas para componentes.

### Importar

```python
from consumo_lib.ui import DIM
```

### Border Radius

| Token | Pixels | Uso |
|-------|--------|-----|
| `DIM.RADIUS_SM` | 4px | Borda suave |
| `DIM.RADIUS_MD` | 8px | Borda padrão |
| `DIM.RADIUS_LG` | 12px | Borda arredondada |
| `DIM.RADIUS_XL` | 16px | Borda muito arredondada |
| `DIM.RADIUS_CIRCLE` | 50% | Círculo completo |

### Icon Sizes

| Token | Pixels | Uso |
|-------|--------|-----|
| `DIM.ICON_XS` | 16px | Ícones muito pequenos |
| `DIM.ICON_SM` | 20px | Ícones pequenos |
| `DIM.ICON_MD` | 24px | Ícones padrão |
| `DIM.ICON_LG` | 32px | Ícones grandes |
| `DIM.ICON_XL` | 48px | Ícones muito grandes |

### Button Heights

| Token | Pixels | Uso |
|-------|--------|-----|
| `DIM.BUTTON_HEIGHT_SM` | 32px | Botões pequenos |
| `DIM.BUTTON_HEIGHT_MD` | 40px | Botões padrão |
| `DIM.BUTTON_HEIGHT_LG` | 48px | Botões grandes |

### Input Heights

| Token | Pixels | Uso |
|-------|--------|-----|
| `DIM.INPUT_HEIGHT_SM` | 32px | Inputs pequenos |
| `DIM.INPUT_HEIGHT_MD` | 40px | Inputs padrão |
| `DIM.INPUT_HEIGHT_LG` | 48px | Inputs grandes |

### Dialog Sizes

| Token | Width × Height | Uso |
|-------|----------------|-----|
| `DIM.DIALOG_SMALL` | 500 × 400 | Diálogos compactos |
| `DIM.DIALOG_MEDIUM` | 700 × 600 | Diálogos padrão |
| `DIM.DIALOG_LARGE` | 900 × 700 | Diálogos grandes |
| `DIM.DIALOG_XLARGE` | 1200 × 800 | Diálogos muito grandes |

### Widget Sizes

| Token | Pixels | Uso |
|-------|--------|-----|
| `DIM.BADGE_HEIGHT` | 24px | Altura de badges |
| `DIM.PROGRESS_BAR_HEIGHT` | 8px | Altura de barras de progresso |

### Thumbnail Sizes

| Token | Pixels | Uso |
|-------|--------|-----|
| `DIM.THUMBNAIL_SM` | 48×48 | Thumbnails pequenos |
| `DIM.THUMBNAIL_MD` | 80×80 | Thumbnails padrão |
| `DIM.THUMBNAIL_LG` | 120×120 | Thumbnails grandes |

**Exemplos**:

```python
# Botões
btn.setMinimumHeight(DIM.BUTTON_HEIGHT_MD)

# Diálogos
dialog.resize(*DIM.DIALOG_MEDIUM)

# Estilos
widget.setStyleSheet(f"border-radius: {DIM.RADIUS_MD}px;")
```

---

## Elevação (Elevation)

Sistema de sombras para layering (profundidade visual).

### Importar

```python
from consumo_lib.ui import ELEV
```

### Níveis de Elevação

| Token | Uso |
|-------|-----|
| `ELEV.LEVEL_0` | Sem sombra (plano) |
| `ELEV.LEVEL_1` | Cards, botões elevados |
| `ELEV.LEVEL_2` | Menus dropdowns |
| `ELEV.LEVEL_3` | Popups, tooltips |
| `ELEV.LEVEL_4` | Dialogs |
| `ELEV.LEVEL_5` | Modais, overlays máximos |

---

## Opacidade (Opacity)

Níveis de opacidade padronizados para estados visuais.

### Importar

```python
from consumo_lib.ui import OPAC
```

### Valores de Opacidade

| Token | Opacidade | Uso |
|-------|-----------|-----|
| `OPAC.DISABLED` | 38% (0.38) | Estados desabilitados |
| `OPAC.HOVER` | 8% (0.08) | Hover states |
| `OPAC.FOCUS` | 12% (0.12) | Focus states |
| `OPAC.PRESSED` | 16% (0.16) | Pressed/active states |
| `OPAC.DRAG` | 24% (0.24) | Drag states |
| `OPAC.OVERLAY` | 60% (0.60) | Overlays de fundo |

---

## Transições (Transitions)

Durações e funções de easing para animações.

### Importar

```python
from consumo_lib.ui import TRANS
```

### Durações

| Token | ms | Uso |
|-------|----|-----|
| `TRANS.FAST` | 150ms | Micro-interações |
| `TRANS.NORMAL` | 250ms | Padrão |
| `TRANS.SLOW` | 350ms | Transições complexas |

### Easing Functions

| Token | Curva | Uso |
|-------|-------|-----|
| `TRANS.EASING_STANDARD` | ease-in-out | Padrão |
| `TRANS.EASING_DECELERATE` | ease-out | Entrada |
| `TRANS.EASING_ACCELERATE` | ease-in | Saída |

---

## Breakpoints (Breakpoints)

Pontos de corte para responsividade.

### Importar

```python
from consumo_lib.ui import BREAK
```

### Breakpoints

| Token | Pixels | Uso |
|-------|--------|-----|
| `BREAK.XS` | 600px | Telas muito pequenas |
| `BREAK.SM` | 960px | Telas pequenas |
| `BREAK.MD` | 1280px | Telas médias (padrão) |
| `BREAK.LG` | 1920px | Telas grandes |
| `BREAK.XL` | 2560px | Telas muito grandes |

---

## Acessibilidade (Accessibility)

Constantes WCAG para acessibilidade.

### Importar

```python
from consumo_lib.ui import A11Y
```

### Padrões

| Token | Valor | Uso |
|-------|-------|-----|
| `A11Y.CONTRAST_NORMAL` | 7.0:1 | Contraste WCAG AA |
| `A11Y.CONTRAST_LARGE` | 4.5:1 | Contraste WCAG AA (texto grande) |
| `A11Y.MINIMUM_TOUCH_SIZE` | 44×44px | Tamanho mínimo de toque (mobile) |

---

## Boas Práticas

### 1. Use Sempre Tokens

```python
# ❌ ERRADO - Hardcoded
btn.setStyleSheet("background-color: #4CAF50; padding: 4px 12px;")

# ✅ CORRETO - Tokens
btn.setStyleSheet(f"background-color: {COLORS.PRIMARY}; padding: {SPACE.XS}px {SPACE.MD}px;")
```

### 2. Prefira Constantes Semânticas

```python
# ❌ ERRADO - Genérico
btn.setStyleSheet(f"background-color: {COLORS.PRIMARY};")

# ✅ CORRETO - Semântico (se houver um token específico)
status_badge.setStyleSheet(f"background-color: {COLORS.STATUS_APPROVED_AUTO};")
```

### 3. Combine Tokens

```python
# Combinação de múltiplos tokens
label.setStyleSheet(f"""
    color: {COLORS.ON_BACKGROUND};
    font-size: {TYPO.BODY_MEDIUM}px;
    padding: {SPACE.SM}px;
    border-radius: {DIM.RADIUS_SM}px;
""")
```

---

## Referência Rápida

```python
# Cores mais usadas
COLORS.PRIMARY              # Ações principais (#4CAF50)
COLORS.SUCCESS              # Sucesso (#2ecc71)
COLORS.ERROR                # Erros (#e74c3c)
COLORS.WARNING              # Avisos (#f1c40f)
COLORS.BACKGROUND           # Fundo branco (#FFFFFF)
COLORS.ON_BACKGROUND        # Texto preto (#212121)

# Fontes mais usadas
TYPO.BODY_MEDIUM            # Texto padrão (14px)
TYPO.BODY_LARGE             # Botões (16px)
TYPO.HEADLINE_SMALL         # Títulos (24px)
TYPO.LABEL_SMALL            # Badges (11px)

# Espaçamentos mais usados
SPACE.SM                    # 8px
SPACE.MD                    # 16px (padrão)
SPACE.LG                    # 24px

# Dimensões mais usadas
DIM.BUTTON_HEIGHT_MD        # 40px
DIM.INPUT_HEIGHT_MD         # 40px
DIM.RADIUS_MD               # 8px
```

---

**Última atualização**: 2026-01-19
**Versão**: 1.0.0
