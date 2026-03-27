# Guia de Implementação - Dimensões de Botões

**Data:** 2026-03-27
**Versão:** 4.0.0 - Microsoft Style
**Status:** Guia Prático

---

## Visão Geral

Dimensões de botões otimizadas para visual profissional estilo Microsoft:
- **Compacto e limpo** - botões menores e mais elegantes
- **Hierarquia visual clara** - tamanhos distintos por contexto
- **Abandona WCAG 44px** - estética priorizada sobre acessibilidade extrema

---

## Comparação de Dimensões (v3.0 vs v4.0)

| Tipo | v3.0 (WCAG) | v4.0 (Microsoft) | Redução |
|------|-------------|------------------|---------|
| Dialog Primary | 48×120px | 28×90px | -42% |
| Dialog Secondary | 40×100px | 24×80px | -40% |
| Directional | 50×50px | 32×32px | -36% |
| Toolbar Icon | 40×40px | 28×28px | -30% |
| Inline Primary | 36×80px | 24×60px | -33% |

---

## Tabela de Dimensões v4.0

### Dialog Buttons

| Semantic Size | Altura | Largura Mín | Uso |
|---------------|--------|-------------|-----|
| `dialog-primary` | 28px | 90px | Salvar, Confirmar, OK |
| `dialog-secondary` | 24px | 80px | Cancelar, Fechar |
| `dialog-tertiary` | 22px | 70px | Apply, Reset |
| `emergency` | 32px | 100px | STOP, Emergency |

### Movement Buttons

| Semantic Size | Altura | Largura Mín | Uso |
|---------------|--------|-------------|-----|
| `directional` | 32px | 32px | ↑, ↓, ←, → (quadrado) |
| `z-axis` | 24px | 32px | Z+, Z- |
| `function-primary` | 26px | 80px | Home, Zero, Go To |
| `function-secondary` | 24px | 70px | Step/Continuous |
| `toggle-status` | 28px | 28px | Backlight, Mode (quadrado) |

### Toolbar Buttons

| Semantic Size | Altura | Largura Mín | Uso |
|---------------|--------|-------------|-----|
| `toolbar-text` | 24px | 80px | Anterior, Próximo |
| `toolbar-icon` | 28px | 28px | Refresh, Clear (quadrado) |
| `toolbar-icon-large` | 32px | 32px | New, Open, Save (quadrado) |

### Inline Buttons

| Semantic Size | Altura | Largura Mín | Uso |
|---------------|--------|-------------|-----|
| `inline-primary` | 24px | 60px | Capturar, Calcular |
| `inline-secondary` | 22px | 55px | Limpar, Reset |
| `inline-compact` | 20px | 50px | [CUIDADO: uso raro] |

### Grid Buttons

| Semantic Size | Altura | Largura Mín | Uso |
|---------------|--------|-------------|-----|
| `grid-action` | 28px | 60px | Edit, Delete, View |
| `grid-status` | 20px | auto | Badges clicáveis |

---

## Implementação

### Usando StandardButton

```python
from consumo_lib.ui.widget_standards import StandardButton

# Diálogo - botão primário
btn_save = StandardButton("Salvar", semantic_size="dialog-primary")

# Diálogo - botão secundário
btn_cancel = StandardButton("Cancelar", semantic_size="dialog-secondary")

# Controle de movimento - direcional
btn_up = StandardButton("↑", semantic_size="directional")

# Toolbar com ícone
btn_refresh = StandardButton("⟳", semantic_size="toolbar-icon")

# Ação inline
btn_calc = StandardButton("Calcular", semantic_size="inline-primary")
```

### Usando Tokens Diretamente

```python
from consumo_lib.ui import DIM

# Altura e largura mínima
btn.setMinimumHeight(DIM.BUTTON_DIALOG_PRIMARY_HEIGHT)
btn.setMinimumWidth(DIM.BUTTON_DIALOG_PRIMARY_MIN_WIDTH)

# Botão quadrado
btn.setFixedSize(DIM.BUTTON_DIRECTIONAL_SIZE, DIM.BUTTON_DIRECTIONAL_SIZE)
```

---

## Tamanhos Legados (Backward Compatible)

| Size | Altura | Largura | Equivalente v4.0 |
|------|--------|---------|------------------|
| `sm` | 22px | 60px | inline-secondary |
| `md` | 26px | 80px | inline-primary |
| `lg` | 32px | 100px | dialog-primary |

```python
# Ainda funciona (deprecated)
btn = StandardButton("OK", size="lg")  # 32×100px

# Preferido (v4.0)
btn = StandardButton("OK", semantic_size="dialog-primary")  # 28×90px
```

---

## Input Heights (Microsoft Style)

| Size | Altura | Uso |
|------|--------|-----|
| `INPUT_HEIGHT_SM` | 22px | Campos compactos |
| `INPUT_HEIGHT_MD` | 26px | Padrão |
| `INPUT_HEIGHT_LG` | 32px | Campos proeminentes |

---

## Notas de Design

- **Border radius**: 3-4px (estilo Microsoft, não 10px)
- **Border width**: 1px (não 2px)
- **Padding**: 4-8px (não 16px)
- **Font size**: 12px para UI padrão

---

**Última atualização:** 2026-03-27
**Versão:** 4.0.0 - Microsoft Style