# Resumo: Padrão Semântico de Dimensões de Botões

**Data:** 2026-01-20
**Versão:** 1.0.0
**Status:** Proposta
**Documento completo:** `BUTTON_DIMENSIONS_PROPOSAL.md`

---

## 🎯 Objetivo

Criar um **sistema semântico** para dimensões de botões baseado em:
- **Contexto de uso** (Onde o botão vive?)
- **Importância** (Quão crítica é a ação?)
- **Acessibilidade** (WCAG 2.5.5: mínimo 44×44px)

---

## 📊 Padrão Proposto (Resumo)

### CATEGORIAS DE BOTÕES

| Categoria | Tamanho | Dimensões | Exemplo |
|-----------|---------|-----------|---------|
| **Dialog - Primary** | XL | 48px altura × 120px largura (min) | Salvar, Confirmar |
| **Dialog - Secondary** | L | 40px altura × 100px largura (min) | Cancelar, Fechar |
| **Emergency** | XXL | 56px altura × 140px largura (min) | STOP, Emergency |
| **Directional** | Square | 50×50px | ↑, ↓, ←, → |
| **Z-Axis** | Rect | 50×35px | Z+, Z- |
| **Toolbar - Text** | M | 36px altura × 120px largura (min) | Anterior, Próximo |
| **Toolbar - Icon** | Square | 40×40px | Refresh, Clear |
| **Inline - Primary** | M | 36px altura × auto largura | Capturar, Calcular |
| **Grid Action** | S (A11y) | 44px altura × 80px largura (min) | Edit, Delete |

---

## 🔥 Problemas Atuais

1. **Inconsistência:** Login usa 45px, outros diálogos usam 48px
2. **Acessibilidade:** Botões de 32px violam WCAG 2.5.5 (mínimo 44px)
3. **Hardcoded:** Muitos valores numéricos sem tokens (`DIM.*`)
4. **Semântica ausente:** Tamanho baseado em "parece bom", não em função

---

## ✅ Benefícios da Proposta

### 1. Consistência Visual
```
Dialog Principal: 48px altura (todos)
Dialog Secundário: 40px altura (todos)
```

### 2. Acessibilidade Garantida
```
Grid Actions: 44px (WCAG 2.5.5 compliant)
Touch Targets: Mínimo 44×44px
```

### 3. Código Type-Safe
```python
# ❌ ANTES (Hardcoded)
btn.setMinimumHeight(45)  # Mágica!

# ✅ DEPOIS (Semantic)
btn.setMinimumHeight(DIM.BUTTON_DIALOG_PRIMARY_HEIGHT)  # 48px
```

### 4. Intenção Clara
```python
StandardButton(
    "Salvar",
    variant="primary-green",
    semantic_size="dialog-primary"  # Intenção óbvia
)
```

---

## 🚀 Implementação Rápida

### Passo 1: Adicionar Tokens (1 dia)

**Arquivo:** `consumo_lib/ui/design_tokens.py`

```python
@dataclass(frozen=True)
class Dimensions:
    # ... tokens existentes ...

    # =========================================================================
    # DIALOG BUTTONS (Novo)
    # =========================================================================

    BUTTON_DIALOG_PRIMARY_HEIGHT: int = 48
    BUTTON_DIALOG_PRIMARY_MIN_WIDTH: int = 120

    BUTTON_DIALOG_SECONDARY_HEIGHT: int = 40
    BUTTON_DIALOG_SECONDARY_MIN_WIDTH: int = 100

    # =========================================================================
    # MOVEMENT BUTTONS (Novo)
    # =========================================================================

    BUTTON_DIRECTIONAL_SIZE: int = 50
    BUTTON_Z_AXIS_WIDTH: int = 50
    BUTTON_Z_AXIS_HEIGHT: int = 35

    # ... outros tokens ...
```

---

### Passo 2: Atualizar StandardButton (2 dias)

**Arquivo:** `consumo_lib/ui/widget_standards.py`

```python
class StandardButton(QPushButton):
    def __init__(
        self,
        text: str,
        variant: str = "primary-green",
        size: str = "md",  # [DEPRECATED]
        semantic_size: str | None = None,  # NOVO
        parent=None
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

        # Fallback para size (sm/md/lg)
        elif size == "sm":
            height = DIM.BUTTON_HEIGHT_SM
        # ...

        self.setMinimumHeight(height)
        self.setMinimumWidth(min_width)
```

---

### Passo 3: Migrar Diálogos (3 dias)

**Arquivos:** Login, Engineering Wizard, Auth Settings, etc.

```python
# ❌ ANTES
ok_btn = QPushButton("OK")
ok_btn.setMinimumHeight(45)
ok_btn.setMinimumWidth(120)

# ✅ DEPOIS
ok_btn = StandardButton(
    "OK",
    variant="primary-green",
    semantic_size="dialog-primary"  # 48×120px
)
```

---

## 📈 Plano de Migração

| Fase | Descrição | Timeline | Prioridade |
|------|-----------|----------|------------|
| **Fase 1** | Adicionar tokens | 1 dia | HIGH |
| **Fase 2** | Atualizar StandardButton | 2 dias | HIGH |
| **Fase 3** | Migrar diálogos críticos | 3 dias | HIGH |
| **Fase 4** | Migrar controles de movimento | 2 dias | MEDIUM |
| **Fase 5** | Migrar toolbars/inline | 5 dias | LOW |
| **Fase 6** | Atualizar documentação | 2 dias | MEDIUM |
| **Fase 7** | Remover tokens legados | Futuro | LOW |

**Total estimado:** 15 dias (3 semanas)

---

## 🎓 Exemplos de Uso

### Dialog Padrão

```python
from consumo_lib.ui.widget_standards import StandardButton

# Botão primário (Salvar)
save_btn = StandardButton(
    "Salvar",
    variant="primary-green",
    semantic_size="dialog-primary"  # 48×120px
)

# Botão secundário (Cancelar)
cancel_btn = StandardButton(
    "Cancelar",
    variant="secondary",
    semantic_size="dialog-secondary"  # 40×100px
)
```

### Movement Controls

```python
from consumo_lib.ui import DIM

# Botão direcional (50×50px)
up_btn = QPushButton("↑")
up_btn.setMinimumSize(
    DIM.BUTTON_DIRECTIONAL_SIZE,
    DIM.BUTTON_DIRECTIONAL_SIZE
)

# Botão Z-axis (50×35px)
z_up_btn = QPushButton("Z+")
z_up_btn.setMinimumSize(
    DIM.BUTTON_Z_AXIS_WIDTH,
    DIM.BUTTON_Z_AXIS_HEIGHT
)
```

---

## ✅ Checklist de Validação

Para cada botão na aplicação:

- [ ] Tem **contexto semântico claro**?
- [ ] Tamanho definido por **token** (`DIM.BUTTON_*`)?
- [ ] Respeita **hierarquia visual**?
- [ ] É **acessível** (≥44px para touch targets)?
- [ ] É **consistente** com outros botões do mesmo contexto?
- [ ] Está **documentado**?

---

## 📚 Referências

- **Documento completo:** `BUTTON_DIMENSIONS_PROPOSAL.md`
- **Material Design 3:** https://m3.material.io/components/buttons
- **WCAG 2.5.5:** https://www.w3.org/WAI/WCAG21/Understanding/target-size.html
- **Design System README:** `docs/design_system/README.md`

---

## 🤔 Decisão: Qual Tamanho Usar?

```
Botão em DIALOG?
├─ Sim → Ação PRIMÁRIA?
│   ├─ Sim → dialog-primary (48×120px)
│   └─ Não → dialog-secondary (40×100px)
│
└─ Não → Botão de MOVIMENTO?
    ├─ Sim → DIRECIONAL?
    │   ├─ Sim → directional (50×50px)
    │   └─ Z-AXIS → z-axis (50×35px)
    │
    └─ Não → Botão em TOOLBAR?
        ├─ Sim → Com TEXTO?
        │   ├─ Sim → toolbar-text (36×120px)
        │   └─ Ícone → toolbar-icon (40×40px)
        │
        └─ Não → INLINE?
            ├─ Sim → inline-primary (36px altura)
            └─ GRID → grid-action (44×80px)
```

---

## 🎯 Conclusão

Esta proposta estabelece um **sistema semântico** que garante:

✅ **Consistência visual** em toda aplicação
✅ **Acessibilidade** WCAG 2.1 compliant
✅ **Flexibilidade** para diferentes contextos
✅ **Escalabilidade** para futuros componentes
✅ **Clareza** na escolha do tamanho certo

**Próximos passos:**
1. Review com equipe
2. Implementar Fase 1 (tokens)
3. Piloto em 2-3 diálogos
4. Validar visualmente
5. Migrar gradualmente

---

**Para detalhes completos, veja:** `BUTTON_DIMENSIONS_PROPOSAL.md`
