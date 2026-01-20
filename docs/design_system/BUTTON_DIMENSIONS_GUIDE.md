# Guia de Implementação - Dimensões de Botões

**Data:** 2026-01-20
**Versão:** 1.0.0
**Status:** Guia Prático
**Documento completo:** `BUTTON_DIMENSIONS_PROPOSAL.md`

---

## 🚀 Implementação Rápida (Copy-Paste)

### Passo 1: Atualizar `design_tokens.py`

Adicione os seguintes tokens à classe `Dimensions` em `consumo_lib/ui/design_tokens.py`:

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
    BUTTON_HEIGHT_MD: int = 40  # [DEPRECATED] Use BUTTON_DIALOG_SECONDARY
    BUTTON_HEIGHT_LG: int = 48  # [DEPRECATED] Use BUTTON_DIALOG_PRIMARY

    # =========================================================================
    # DIALOG BUTTONS (Novo Sistema Semântico)
    # =========================================================================

    BUTTON_DIALOG_PRIMARY_HEIGHT: int = 48
    BUTTON_DIALOG_PRIMARY_MIN_WIDTH: int = 120

    BUTTON_DIALOG_SECONDARY_HEIGHT: int = 40
    BUTTON_DIALOG_SECONDARY_MIN_WIDTH: int = 100

    BUTTON_DIALOG_TERTIARY_HEIGHT: int = 36
    BUTTON_DIALOG_TERTIARY_MIN_WIDTH: int = 90

    BUTTON_EMERGENCY_HEIGHT: int = 56
    BUTTON_EMERGENCY_MIN_WIDTH: int = 140
    BUTTON_EMERGENCY_PADDING: tuple = (15, 40)

    # =========================================================================
    # MOVEMENT CONTROL BUTTONS
    # =========================================================================

    BUTTON_DIRECTIONAL_SIZE: int = 50

    BUTTON_Z_AXIS_WIDTH: int = 50
    BUTTON_Z_AXIS_HEIGHT: int = 35

    BUTTON_FUNCTION_PRIMARY_HEIGHT: int = 40
    BUTTON_FUNCTION_PRIMARY_MIN_WIDTH: int = 100

    BUTTON_FUNCTION_SECONDARY_HEIGHT: int = 40
    BUTTON_FUNCTION_SECONDARY_MIN_WIDTH: int = 90

    BUTTON_TOGGLE_STATUS_SIZE: int = 44

    # =========================================================================
    # TOOLBAR BUTTONS
    # =========================================================================

    BUTTON_TOOLBAR_TEXT_HEIGHT: int = 36
    BUTTON_TOOLBAR_TEXT_MIN_WIDTH: int = 120

    BUTTON_TOOLBAR_ICON_SIZE: int = 40
    BUTTON_TOOLBAR_ICON_LARGE_SIZE: int = 48

    # =========================================================================
    # INLINE ACTION BUTTONS
    # =========================================================================

    BUTTON_INLINE_PRIMARY_HEIGHT: int = 36
    BUTTON_INLINE_PRIMARY_MIN_WIDTH: int = 80

    BUTTON_INLINE_SECONDARY_HEIGHT: int = 32
    BUTTON_INLINE_SECONDARY_MIN_WIDTH: int = 70

    BUTTON_INLINE_COMPACT_HEIGHT: int = 28
    BUTTON_INLINE_COMPACT_MIN_WIDTH: int = 60

    # =========================================================================
    # GRID/TABLE ACTION BUTTONS
    # =========================================================================

    BUTTON_GRID_ACTION_HEIGHT: int = 44  # WCAG 2.5.5 compliant
    BUTTON_GRID_ACTION_MIN_WIDTH: int = 80

    BUTTON_GRID_STATUS_HEIGHT: int = 24
```

---

### Passo 2: Atualizar `widget_standards.py`

Modifique `StandardButton` para suportar tamanhos semânticos:

```python
class StandardButton(QPushButton):
    """
    Botão padrão com estilo consistente

    NOVO v1.1: Suporte a semantic_size para tamanhos baseados em contexto

    Usage:
        # NOVO (Recomendado)
        btn = StandardButton("Salvar", semantic_size="dialog-primary")

        # ANTIGO (Ainda funciona)
        btn = StandardButton("Salvar", size="lg")
    """

    # Mapeamento de tamanhos semânticos
    SEMANTIC_SIZES = {
        "dialog-primary": (48, 120),
        "dialog-secondary": (40, 100),
        "dialog-tertiary": (36, 90),
        "emergency": (56, 140),
        "directional": (50, 50),
        "z-axis": (50, 35),
        "function-primary": (40, 100),
        "function-secondary": (40, 90),
        "toggle-status": (44, 44),
        "toolbar-text": (36, 120),
        "toolbar-icon": (40, 40),
        "toolbar-icon-large": (48, 48),
        "inline-primary": (36, 80),
        "inline-secondary": (32, 70),
        "inline-compact": (28, 60),
        "grid-action": (44, 80),
        "grid-status": (24, 0),  # 0 = auto
    }

    def __init__(
        self,
        text: str,
        variant: str = "primary-green",
        size: str = "md",
        semantic_size: str | None = None,
        parent=None
    ):
        """
        Inicializa botão padrão

        Args:
            text: Texto do botão
            variant: Variant do botão (primary-green|primary-blue|primary-orange|secondary|emergency)
            size: [DEPRECATED] Tamanho (sm|md|lg)
            semantic_size: [NOVO] Tamanho semântico (dialog-primary|directional|etc)
            parent: Widget pai
        """
        super().__init__(text, parent)

        # Emitir warning para variantes deprecated
        if variant == "primary":
            import warnings
            warnings.warn(
                'variant="primary" is deprecated. Use variant="primary-green" instead.',
                DeprecationWarning,
                stacklevel=2
            )
            variant = "primary-green"
        elif variant == "danger":
            import warnings
            warnings.warn(
                'variant="danger" is deprecated. Use variant="emergency" instead.',
                DeprecationWarning,
                stacklevel=2
            )
            variant = "emergency"

        # Aplicar fonte padrão
        font = TYPO.get_font(TYPO.BODY_LARGE, weight=FontWeight.MEDIUM)
        self.setFont(font)

        # Prioridade: semantic_size > size
        if semantic_size:
            if semantic_size not in self.SEMANTIC_SIZES:
                raise ValueError(
                    f"semantic_size deve ser um de: {list(self.SEMANTIC_SIZES.keys())}\n"
                    f"Recebido: '{semantic_size}'"
                )

            height, min_width = self.SEMANTIC_SIZES[semantic_size]

            # Aplicar dimensões
            self.setMinimumHeight(height)
            if min_width > 0:
                self.setMinimumWidth(min_width)

            # Ajustes especiais para alguns semantic_size
            if semantic_size == "directional":
                # Botões direcionais são sempre quadrados
                self.setMaximumSize(height, height)

            elif semantic_size == "toolbar-icon":
                # Botões de toolbar com ícone são quadrados
                self.setMaximumSize(height, height)

        else:
            # Fallback para size (sm/md/lg) - BACKWARD COMPAT
            if size == "sm":
                width, height = DIM.BUTTON_SIZE_SM
            elif size == "lg":
                width, height = DIM.BUTTON_SIZE_LG
            else:  # md (default)
                width, height = DIM.BUTTON_SIZE_MD

            self.setMinimumSize(width, height)

        # Aplicar variante via property (para stylesheet)
        self.setProperty("variant", variant)
```

---

### Passo 3: Exemplos de Migração

#### Exemplo 1: Dialog Padrão

```python
# ❌ ANTES (Hardcoded)
from PyQt6.QtWidgets import QDialog, QHBoxLayout, QPushButton

class MyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Botões
        ok_btn = QPushButton("OK")
        ok_btn.setMinimumHeight(45)
        ok_btn.setMinimumWidth(120)

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setMinimumHeight(45)
        cancel_btn.setMinimumWidth(120)

        button_layout = QHBoxLayout()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(ok_btn)

# ✅ DEPOIS (Semantic)
from PyQt6.QtWidgets import QDialog, QHBoxLayout
from consumo_lib.ui.widget_standards import StandardButton

class MyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Botões
        ok_btn = StandardButton(
            "OK",
            variant="primary-green",
            semantic_size="dialog-primary"  # 48×120px
        )

        cancel_btn = StandardButton(
            "Cancelar",
            variant="secondary",
            semantic_size="dialog-secondary"  # 40×100px
        )

        button_layout = QHBoxLayout()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(ok_btn)
```

---

#### Exemplo 2: Movement Controls

```python
# ❌ ANTES (Hardcoded)
from PyQt6.QtWidgets import QPushButton

class MovementControls(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.up_button = QPushButton("↑")
        self.up_button.setMinimumSize(50, 50)

        self.z_up_button = QPushButton("Z+")
        self.z_up_button.setMinimumSize(50, 30)

# ✅ DEPOIS (Semantic)
from PyQt6.QtWidgets import QPushButton
from consumo_lib.ui import DIM

class MovementControls(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Botão direcional (50×50px)
        self.up_button = QPushButton("↑")
        self.up_button.setMinimumSize(
            DIM.BUTTON_DIRECTIONAL_SIZE,
            DIM.BUTTON_DIRECTIONAL_SIZE
        )

        # Botão Z-axis (50×35px)
        self.z_up_button = QPushButton("Z+")
        self.z_up_button.setMinimumSize(
            DIM.BUTTON_Z_AXIS_WIDTH,
            DIM.BUTTON_Z_AXIS_HEIGHT
        )
```

---

#### Exemplo 3: Toolbar

```python
# ❌ ANTES (Hardcoded)
from PyQt6.QtWidgets import QHBoxLayout, QPushButton

class Toolbar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)

        # Botão com texto
        new_btn = QPushButton("Novo")
        new_btn.setMinimumHeight(36)
        new_btn.setMinimumWidth(120)

        # Botão ícone
        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedSize(40, 40)

        layout.addWidget(new_btn)
        layout.addWidget(refresh_btn)

# ✅ DEPOIS (Semantic)
from PyQt6.QtWidgets import QHBoxLayout, QPushButton
from consumo_lib.ui import DIM

class Toolbar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)

        # Botão com texto
        new_btn = QPushButton("Novo")
        new_btn.setMinimumHeight(DIM.BUTTON_TOOLBAR_TEXT_HEIGHT)
        new_btn.setMinimumWidth(DIM.BUTTON_TOOLBAR_TEXT_MIN_WIDTH)

        # Botão ícone
        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedSize(
            DIM.BUTTON_TOOLBAR_ICON_SIZE,
            DIM.BUTTON_TOOLBAR_ICON_SIZE
        )

        layout.addWidget(new_btn)
        layout.addWidget(refresh_btn)
```

---

## 📋 Checklist de Migração

### Para cada arquivo com botões:

- [ ] Identificar o **contexto semântico** de cada botão
- [ ] Escolher o `semantic_size` apropriado (veja tabela abaixo)
- [ ] Substituir `setMinimumHeight(hardcoded)` por `DIM.BUTTON_*`
- [ ] Substituir `QPushButton` por `StandardButton` quando apropriado
- [ ] Testar visualmente o resultado
- [ ] Verificar acessibilidade (≥44px para touch targets)

---

## 🎯 Tabela de Decisão Rápida

| Contexto | semantic_size | Dimensões |
|----------|---------------|-----------|
| Dialog - Salvar/Confirmar/OK | `dialog-primary` | 48×120px |
| Dialog - Cancelar/Fechar | `dialog-secondary` | 40×100px |
| Dialog - Apply/Reset | `dialog-tertiary` | 36×90px |
| Emergency - STOP | `emergency` | 56×140px |
| Movement - ↑↓←→ | `directional` | 50×50px |
| Movement - Z+/Z- | `z-axis` | 50×35px |
| Movement - Home/Zero | `function-primary` | 40×100px |
| Movement - Toggle | `toggle-status` | 44×44px |
| Toolbar - Texto | `toolbar-text` | 36×120px |
| Toolbar - Ícone | `toolbar-icon` | 40×40px |
| Inline - Principal | `inline-primary` | 36px altura |
| Inline - Secundário | `inline-secondary` | 32px altura |
| Table - Edit/Delete | `grid-action` | 44×80px |

---

## 🧪 Validação

### Teste 1: Verificar Tokens

```python
# Testar se os tokens estão definidos
from consumo_lib.ui import DIM

assert DIM.BUTTON_DIALOG_PRIMARY_HEIGHT == 48
assert DIM.BUTTON_DIALOG_PRIMARY_MIN_WIDTH == 120
assert DIM.BUTTON_DIRECTIONAL_SIZE == 50
assert DIM.BUTTON_Z_AXIS_WIDTH == 50
assert DIM.BUTTON_Z_AXIS_HEIGHT == 35
```

### Teste 2: Verificar StandardButton

```python
# Testar se StandardButton aceita semantic_size
from consumo_lib.ui.widget_standards import StandardButton

btn = StandardButton("Test", semantic_size="dialog-primary")
assert btn.minimumHeight() == 48
assert btn.minimumWidth() == 120
```

### Teste 3: Validação Visual

1. Abrir aplicação
2. Verificar se botões de diálogos têm tamanhos consistentes
3. Verificar se botões de movimento são quadrados (50×50px)
4. Verificar se não há botões <44px (exceto em grupos)

---

## 🐛 Troubleshooting

### Erro: `ValueError: semantic_size deve ser um de: [...]`

**Causa:** Você passou um `semantic_size` inválido.

**Solução:** Verifique a lista de valores válidos:
```python
from consumo_lib.ui.widget_standards import StandardButton
print(StandardButton.SEMANTIC_SIZES.keys())
```

---

### Erro: Botão muito pequeno (<44px)

**Causa:** Usou `inline-compact` ou `size="sm"` sozinho.

**Solução:** Use `inline-primary` (36px) ou `grid-action` (44px) para acessibilidade.

---

### Erro: Botão distorcido (não quadrado)

**Causa:** Usou `semantic_size="directional"` mas não configurou corretamente.

**Solução:** Use `setMaximumSize()` para garantir quadrado:
```python
btn.setMinimumSize(DIM.BUTTON_DIRECTIONAL_SIZE, DIM.BUTTON_DIRECTIONAL_SIZE)
btn.setMaximumSize(DIM.BUTTON_DIRECTIONAL_SIZE, DIM.BUTTON_DIRECTIONAL_SIZE)
```

---

## 📚 Referências Rápidas

- **Tokens disponíveis:** `consumo_lib/ui/design_tokens.py` (classe `Dimensions`)
- **Componente padrão:** `consumo_lib/ui/widget_standards.py` (classe `StandardButton`)
- **Documentação completa:** `docs/design_system/BUTTON_DIMENSIONS_PROPOSAL.md`
- **Resumo executivo:** `docs/design_system/BUTTON_DIMENSIONS_SUMMARY.md`

---

## ✅ Exemplo Completo: Dialog com Tudo

```python
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout
from consumo_lib.ui.widget_standards import StandardButton
from consumo_lib.ui import DIM, SPACE

class ExampleDialog(QDialog):
    """
    Dialog exemplo usando sistema semântico de botões

    Layout:
    - Botão primário (Salvar): 48×120px
    - Botão secundário (Cancelar): 40×100px
    - Botão terciário (Apply): 36×90px
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Dialog Exemplo")
        self.setMinimumSize(400, 300)

        layout = QVBoxLayout(self)
        layout.setSpacing(SPACE.MD)

        # Conteúdo
        content = QLabel("Este dialog demonstra o uso de botões semânticos.")
        layout.addWidget(content)

        layout.addStretch()

        # Botões (BOTTOM-RIGHT ALIGNMENT)
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # Apply (Terciário - 36×90px)
        apply_btn = StandardButton(
            "Apply",
            variant="primary-blue",
            semantic_size="dialog-tertiary"
        )
        button_layout.addWidget(apply_btn)

        # Cancelar (Secundário - 40×100px)
        cancel_btn = StandardButton(
            "Cancelar",
            variant="secondary",
            semantic_size="dialog-secondary"
        )
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        # Salvar (Primário - 48×120px)
        save_btn = StandardButton(
            "Salvar",
            variant="primary-green",
            semantic_size="dialog-primary"
        )
        save_btn.clicked.connect(self.accept)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    dialog = ExampleDialog()
    dialog.exec()
```

---

## 🎓 Próximos Passos

1. **Implementar Passo 1:** Adicionar tokens ao `design_tokens.py`
2. **Implementar Passo 2:** Atualizar `StandardButton`
3. **Testar:** Executar aplicação e validar visualmente
4. **Migrar:** Usar exemplos acima para migrar diálogos críticos
5. **Documentar:** Atualizar `COMPONENTS.md` com novos padrões

---

**Para dúvidas, consulte:** `BUTTON_DIMENSIONS_PROPOSAL.md`
