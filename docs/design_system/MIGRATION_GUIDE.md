# Guia de Migração - Design System v1.0 → v2.0

**Versão:** 2.0
**Data:** 2026-01-20
**Status:** ✅ Approved

## Visão Geral

Este guia ajuda desenvolvedores a migrar código legado para o novo Design System v2.0 do Tensiometro, garantindo consistência visual e aproveitando os novos recursos.

### O Que Mudou?

| Recurso | v1.0 (Old) | v2.0 (New) |
|---------|------------|------------|
| **API de Botões** | `StyleManager.create_button()` | `StandardButton` class |
| **Variantes** | 3 tipos (primary, secondary, danger) | 5 tipos (primary-green, primary-blue, primary-orange, secondary, emergency) |
| **Fonte Principal** | Arial | Segoe UI |
| **Font Weights** | Boolean `bold=True/False` | Enum `FontWeight` (5 níveis) |
| **Tamanhos de Botão** | Hardcoded | Parameter `size` (sm/md/lg) |

---

## Migração Rápida (Quick Reference)

### Botões

```python
# ❌ v1.0 (OLD)
from consumo_lib.ui.style_manager import StyleManager
btn = StyleManager.create_button("Salvar", 'primary')

# ✅ v2.0 (NEW)
from consumo_lib.ui.widget_standards import StandardButton
btn = StandardButton("Salvar", variant="primary-green")
```

### Font Weights

```python
# ❌ v1.0 (OLD)
font = TYPO.get_font(14, bold=True)

# ✅ v2.0 (NEW)
from consumo_lib.ui.design_tokens import FontWeight
font = TYPO.get_font(14, weight=FontWeight.MEDIUM)
# OU método conveniente:
font = TYPO.medium(14)
```

---

## Migração Detalhada por Componente

### 1. Botões (Buttons)

#### Mapeamento de Variantes

| v1.0 | v2.0 | Notas |
|------|------|-------|
| `variant="primary"` | `variant="primary-green"` | Renomeado para ser mais específico |
| `variant="secondary"` | `variant="secondary"` | Visual mudou (sólido → outline azul) |
| `variant="danger"` | `variant="emergency"` | Renomeado para ser mais específico |
| N/A | `variant="primary-blue"` | **NOVO** - Ações padrão/genéricas |
| N/A | `variant="primary-orange"` | **NOVO** - Ações de parada/atenção |

#### Exemplos de Migração

**Caso 1: Botão de Salvar (Primary)**
```python
# ❌ v1.0
btn_salvar = StyleManager.create_button("Salvar", 'primary')

# ✅ v2.0
btn_salvar = StandardButton("Salvar", variant="primary-green")
```

**Caso 2: Botão de Cancelar (Secondary)**
```python
# ❌ v1.0
btn_cancelar = StyleManager.create_button("Cancelar", 'secondary')

# ✅ v2.0
btn_cancelar = StandardButton("Cancelar", variant="secondary")
# Nota: Visual mudou de azul sólido para outline azul
```

**Caso 3: Botão de Emergência (Danger)**
```python
# ❌ v1.0
btn_emergency = StyleManager.create_button("EMERGENCY STOP", 'danger')

# ✅ v2.0
btn_emergency = StandardButton("EMERGENCY STOP", variant="emergency")
```

**Caso 4: Novo Botão de Configuração (Primary-Blue)**
```python
# ❌ v1.0 (não existia)
btn_configurar = StyleManager.create_button("Configurar", 'primary')  # Repropósito de primary

# ✅ v2.0 (nova variante específica)
btn_configurar = StandardButton("Configurar", variant="primary-blue")
```

**Caso 5: Novo Botão de Parada (Primary-Orange)**
```python
# ❌ v1.0 (não existia)
btn_parar = StyleManager.create_button("Parar", 'secondary')  # Uso incorreto

# ✅ v2.0 (nova variante específica)
btn_parar = StandardButton("Parar", variant="primary-orange")
```

#### Tamanhos de Botão

```python
# ❌ v1.0 (hardcoded)
btn = StyleManager.create_button("Salvar", 'primary')
btn.setFixedSize(120, 40)  # Tamanho definido manualmente

# ✅ v2.0 (parameter)
btn = StandardButton("Salvar", variant="primary-green", size="md")  # sm/md/lg
```

---

### 2. Font Weights

#### Mapeamento de Weights

| v1.0 | v2.0 | Valor Numérico |
|------|------|----------------|
| `bold=False` | `weight=None` ou `weight=FontWeight.NORMAL` | 400 |
| `bold=True` | `weight=FontWeight.MEDIUM` (botões) | 500 |
| `bold=True` | `weight=FontWeight.BOLD` (emergências) | 700 |

#### Exemplos de Migração

**Caso 1: Texto Normal**
```python
# ❌ v1.0
font = TYPO.get_font(14, bold=False)

# ✅ v2.0 (opção 1 - weight parameter)
from consumo_lib.ui.design_tokens import FontWeight
font = TYPO.get_font(14, weight=FontWeight.NORMAL)

# ✅ v2.0 (opção 2 - método conveniente)
font = TYPO.normal(14)

# ✅ v2.0 (opção 3 - default)
font = TYPO.get_font(14)  # default é NORMAL (400)
```

**Caso 2: Texto de Botão**
```python
# ❌ v1.0
font = TYPO.get_font(16, bold=True)

# ✅ v2.0 (recomendado para botões)
font = TYPO.medium(16)  # MEDIUM (500) ao invés de BOLD (700)

# ✅ v2.0 (weight parameter)
font = TYPO.get_font(16, weight=FontWeight.MEDIUM)
```

**Caso 3: Título de Dialog**
```python
# ❌ v1.0
font = TYPO.get_font(28, bold=True)

# ✅ v2.0 (recomendado para títulos)
font = TYPO.semibold(28)  # SEMIBOLD (600)

# ✅ v2.0 (weight parameter)
font = TYPO.get_font(28, weight=FontWeight.SEMIBOLD)
```

**Caso 4: Alerta de Emergência**
```python
# ❌ v1.0
font = TYPO.get_font(16, bold=True)

# ✅ v2.0 (use BOLD apenas para emergências)
font = TYPO.bold(16)  # BOLD (700)
```

#### Métodos Convenientes (NOVO)

```python
# NOVO v2.0 - Métodos convenientes
TYPO.light(size)    # 300 - Uso raro (5%)
TYPO.normal(size)   # 400 - Texto padrão (70%)
TYPO.medium(size)   # 500 - Títulos, botões (20%)
TYPO.semibold(size) # 600 - Títulos principais (4%)
TYPO.bold(size)     # 700 - Emergências apenas (1%)
```

---

### 3. Font Family

#### Mudança de Fonte

| v1.0 | v2.0 |
|------|------|
| Arial | Segoe UI |

#### Impacto

**Nenhuma ação necessária!** A fonte é aplicada automaticamente via `TYPO.get_font()`.

```python
# v1.0 e v2.0 - Mesmo código
font = TYPO.get_font(14)
# v1.0: Arial, 14pt
# v2.0: Segoe UI, 14pt (automático)
```

Se você criava QFont manualmente:

```python
# ❌ v1.0
from PyQt6.QtGui import QFont
font = QFont("Arial", 14)

# ✅ v2.0 (use design tokens)
font = TYPO.get_font(14)  # Segoe UI aplicada automaticamente
```

---

## Backward Compatibility

### Aviso de Deprecation

O código legado ainda funciona, mas emite warnings:

```python
# Ainda funciona, mas gera warning
btn = StandardButton("Salvar", variant="primary")
# DeprecationWarning: variant="primary" is deprecated.
# Use variant="primary-green" instead. Will be removed in v0.5.0

font = TYPO.get_font(14, bold=True)
# DeprecationWarning: bold parameter is deprecated.
# Use weight=FontWeight.BOLD instead. Will be removed in v0.6.0
```

### Timeline de Remoção

| Versão | Status |
|---------|--------|
| v0.4.0 (atual) | Warnings emitidos, código legado funciona |
| v0.5.0 | Variantes "primary" e "danger" removidas |
| v0.6.0 | Parâmetro `bold` removido |

---

## Checklist de Migração

### Passo 1: Botões

- [ ] Substituir `StyleManager.create_button()` por `StandardButton`
- [ ] Mapear `variant="primary"` → `variant="primary-green"`
- [ ] Mapear `variant="danger"` → `variant="emergency"`
- [ ] Revisar botões "secondary" (visual mudou)
- [ ] Adicionar `size="sm/md/lg"` se necessário

### Passo 2: Font Weights

- [ ] Substituir `bold=False` → `weight=FontWeight.NORMAL` ou remover
- [ ] Substituir `bold=True` em botões → `weight=FontWeight.MEDIUM`
- [ ] Substituir `bold=True` em títulos → `weight=FontWeight.SEMIBOLD`
- [ ] Usar métodos convenientes onde apropriado: `TYPO.normal/medium/semibold/bold()`

### Passo 3: Validação

- [ ] Executar aplicação e verificar visualmente
- [ ] Verificar se não há warnings no console
- [ ] Testar interações de hover/pressed/disabled

---

## Exemplos Práticos de Migração

### Exemplo 1: Dialog de Confirmação

**Antes (v1.0):**
```python
from consumo_lib.ui.style_manager import StyleManager

class ConfirmDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout()

        # Título
        title = QLabel("Confirmar Ação")
        title.setFont(TYPO.get_font(28, bold=True))

        # Botões
        btn_confirm = StyleManager.create_button("Confirmar", 'primary')
        btn_cancel = StyleManager.create_button("Cancelar", 'secondary')

        layout.addWidget(title)
        layout.addWidget(btn_confirm)
        layout.addWidget(btn_cancel)
```

**Depois (v2.0):**
```python
from consumo_lib.ui.widget_standards import StandardButton
from consumo_lib.ui.design_tokens import FontWeight, TYPO

class ConfirmDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout()

        # Título (usa SEMIBOLD para dialogs)
        title = QLabel("Confirmar Ação")
        title.setFont(TYPO.semibold(28))  # 600

        # Botões (primary-green para confirmar, secondary para cancelar)
        btn_confirm = StandardButton("Confirmar", variant="primary-green", size="lg")
        btn_cancel = StandardButton("Cancelar", variant="secondary")

        layout.addWidget(title)
        layout.addWidget(btn_confirm)
        layout.addWidget(btn_cancel)
```

### Exemplo 2: Botões de Toolbar

**Antes (v1.0):**
```python
from consumo_lib.ui.style_manager import StyleManager

# Toolbar com botões pequenos
btn_zoom_in = StyleManager.create_button("+", 'primary')
btn_zoom_in.setFixedSize(60, 32)

btn_zoom_out = StyleManager.create_button("-", 'primary')
btn_zoom_out.setFixedSize(60, 32)
```

**Depois (v2.0):**
```python
from consumo_lib.ui.widget_standards import StandardButton

# Toolbar com botões pequenos (size="sm")
btn_zoom_in = StandardButton("+", variant="secondary", size="sm")
btn_zoom_out = StandardButton("-", variant="secondary", size="sm")
```

---

## Perguntas Frequentes (FAQ)

### Q1: Preciso migrar todo o código imediatamente?

**R:** Não. O código legado ainda funciona com warnings. Você pode migrar gradualmente, mas recomendamos migrar o código novo imediatamente.

### Q2: Posso continuar usando `bold=True`?

**R:** Você pode, mas será removido em v0.6.0. Recomendamos migrar para `weight=FontWeight` o quanto antes.

### Q3: Qual variante devo usar para botões genéricos?

**R:** Use `variant="primary-blue"` para ações padrão que não sejam confirmação/início (primary-green) ou parada/atenção (primary-orange).

### Q4: O visual do botão "secondary" mudou?

**R:** Sim. De azul sólido para outline azul com fundo transparente. Isso segue Material Design 3 e fornece melhor hierarquia visual.

### Q5: Como sei se devo usar NORMAL, MEDIUM, SEMIBOLD ou BOLD?

**R:** Siga a frequência de uso:
- **NORMAL (400)**: 70% dos casos - Texto padrão, labels
- **MEDIUM (500)**: 20% dos casos - Títulos de seção, botões
- **SEMIBOLD (600)**: 4% dos casos - Títulos de dialogs
- **BOLD (700)**: 1% dos casos - Emergências apenas

---

## Recursos Adicionais

- **BUTTON_GUIDE.md**: Guia completo de botões
- **TYPOGRAPHY_GUIDE.md**: Guia completo de tipografia
- **Design Tokens**: `consumo_lib/ui/design_tokens.py`
- **Widget Standards**: `consumo_lib/ui/widget_standards.py`

---

**Última Atualização:** 2026-01-20
**Versão do Design System:** 2.0
