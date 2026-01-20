# Guia de Botões - Design System Tensiometro

**Versão:** 2.0
**Data:** 2026-01-20
**Status:** ✅ Approved (Design System v2.0)
**Previous Version:** 1.0 (StyleManager - Deprecated)

## Visão Geral

Este guia define a padronização de botões para o sistema **Tensiometro** baseado no Design System, garantindo consistência visual, hierarquia clara e usabilidade otimizada.

### Princípios de Design

1. **Consistência Visual**: Mesmo estilo para mesma ação em diferentes contextos
2. **Hierarquia Clara**: Tamanho e cor indicam importância da ação
3. **Feedback Imediato**: Hover, pressed e disabled bem definidos
4. **Acessibilidade**: Tamanhos adequados para toque/clique em ambiente industrial
5. **Sobriedade**: Cores e efeitos moderados, adequados para ambiente profissional

---

## Tipos de Botões (Variants)

### 1. Botões Primários (Primary Buttons)

**Uso:** Ações principais, mais frequentes ou mais importantes do contexto atual.

| Subtipo | Cor | Tamanho Padrão | Quando Usar |
|---------|-----|----------------|-------------|
| **primary-green** | Verde | Medium (120×40) | Ações de confirmação, início |
| **primary-blue** | Azul | Medium (120×40) | Ações padrão, genéricas |
| **primary-orange** | Laranja | Medium (120×40) | Ações de parada, alerta, atenção |

#### Exemplos de Uso

```python
from consumo_lib.ui.widget_standards import StandardButton

# ✓ CORRETO - Ação de confirmação/início
btn_iniciar = StandardButton("Iniciar Ciclo", variant="primary-green")

# ✓ CORRETO - Ação padrão genérica
btn_configurar = StandardButton("Configurar", variant="primary-blue")

# ✓ CORRETO - Ação de parada
btn_parar = StandardButton("Parar", variant="primary-orange")

# ✗ ERRADO - Usar primary para ação secundária
btn_cancelar = StandardButton("Cancelar", variant="primary-blue")  # Deveria ser 'secondary'
```

#### Especificação Visual

**primary-green:**
- Background: Gradiente verde (#4CAF50 → #388E3C)
- Texto: Branco
- Borda: 2px solid #2E7D32
- Font-size: 16px (BODY_LARGE)
- Font-weight: 500 (MEDIUM)
- Border-radius: 10px
- Tamanho: (120, 40) - Medium
- Hover: Gradiente mais claro (#66BB6A → #4CAF50)
- Disabled: Cinza (#BDBDBD)

**primary-blue:**
- Background: Gradiente azul (#2196F3 → #1976D2)
- Texto: Branco
- Borda: 2px solid #1565C0
- Font-size: 16px (BODY_LARGE)
- Font-weight: 500 (MEDIUM)
- Border-radius: 10px
- Tamanho: (120, 40) - Medium
- Hover: Gradiente mais claro (#42A5F5 → #2196F3)
- Disabled: Cinza (#BDBDBD)

**primary-orange:**
- Background: Gradiente laranja (#FF9800 → #F57C00)
- Texto: Branco
- Borda: 2px solid #EF6C00
- Font-size: 16px (BODY_LARGE)
- Font-weight: 500 (MEDIUM)
- Border-radius: 10px
- Tamanho: (120, 40) - Medium
- Hover: Gradiente mais claro (#FFB74D → #FF9800)
- Disabled: Cinza (#BDBDBD)

---

### 2. Botão Secundário (Secondary Button)

**Uso:** Ações alternativas, cancelamento, fechamento, ou ações de menor importância.

#### Especificação Visual

- Background: Transparente
- Texto: Azul (#2196F3)
- Borda: 2px solid #2196F3 (outline)
- Font-size: 16px (BODY_LARGE)
- Font-weight: 500 (MEDIUM)
- Border-radius: 5px
- Tamanho: (120, 40) - Medium
- Hover: Gradiente azul claro (#90CAF9 → #64B5F6)
- Disabled: Borda cinza, texto cinza

#### Exemplos de Uso

```python
# ✓ CORRETO - Ação de cancelamento
btn_cancelar = StandardButton("Cancelar", variant="secondary")

# ✓ CORRETO - Ação de fechamento
btn_fechar = StandardButton("Fechar", variant="secondary")

# ✓ CORRETO - Ação alternativa
btn_voltar = StandardButton("Voltar", variant="secondary")
```

---

### 3. Botão de Emergência (Emergency Button)

**Uso:** Ações críticas de segurança, paradas de emergência física. **MUITO RARO (1% dos casos)**.

#### Especificação Visual

- Background: Gradiente vermelho (#F44336 → #D32F2F)
- Texto: Branco
- Borda: 3px solid #B71C1C (borda mais grossa para destaque)
- Font-size: 16px (BODY_LARGE)
- Font-weight: 700 (BOLD)
- Border-radius: 25px (borda muito arredondada)
- Tamanho: (120, 40) - Medium
- Padding: 15px 40px (mais espaçoso via QSS)
- Hover: Gradiente mais claro (#EF5350 → #F44336)
- Disabled: Cinza (#BDBDBD)

#### Regras de Uso

**✅ USE 'emergency' PARA:**
- Botão físico de parada de emergência (E-STOP)
- Situações de risco à segurança humana
- Alertas críticos de segurança

**✗ NÃO USE 'emergency' PARA:**
- Botões de "Parar" comuns (ciclos, processos) → use 'primary-orange'
- Botões de cancelamento → use 'secondary'
- Ações reversíveis → use 'primary-blue' ou 'secondary'
- Feedback visual de erro → use labels coloridas

#### Exemplos de Uso

```python
# ✓ CORRETO - Emergência física real
btn_emergency_stop = StandardButton("EMERGENCY STOP", variant="emergency")

# ✗ ERRADO - Parar ciclo comum
btn_parar = StandardButton("Parar", variant="emergency")  # Deveria ser 'primary-orange'

# ✗ ERRADO - Cancelamento
btn_cancelar = StandardButton("Cancelar", variant="emergency")  # Deveria ser 'secondary'
```

---

## Tamanhos de Botão (Sizes)

### Tabela de Tamanhos

| Tamanho | Dimensões (W×H) | Uso |
|---------|----------------|-----|
| **sm** (small) | 80×32 | Botões compactos, barras de ferramentas |
| **md** (medium) | 120×40 | Tamanho padrão (DEFAULT) |
| **lg** (large) | 160×48 | Botões de destaque, dialogs importantes |

### Exemplos de Uso

```python
# Botão pequeno (toolbar)
btn_zoom_in = StandardButton("+", variant="secondary", size="sm")

# Botão médio (padrão)
btn_salvar = StandardButton("Salvar", variant="primary-green")  # size="md" é default

# Botão grande (destaque)
btn_confirmar = StandardButton("Confirmar Ação", variant="primary-green", size="lg")
```

---

## API Reference

### StandardButton

```python
class StandardButton(QPushButton):
    """
    Botão padrão com estilo consistente

    Args:
        text: Texto do botão
        variant: primary-green | primary-blue | primary-orange | secondary | emergency
        size: sm | md | lg (default: md)
        parent: Widget pai
    """
```

#### Exemplos Completos

```python
from consumo_lib.ui.widget_standards import StandardButton

# Botão padrão (primary-green, medium)
btn1 = StandardButton("Salvar")

# Botão de configuração (primary-blue, medium)
btn2 = StandardButton("Configurar", variant="primary-blue")

# Botão de parada (primary-orange, medium)
btn3 = StandardButton("Parar", variant="primary-orange")

# Botão de cancelamento (secondary, medium)
btn4 = StandardButton("Cancelar", variant="secondary")

# Botão pequeno (secondary, small)
btn5 = StandardButton("Fechar", variant="secondary", size="sm")

# Botão de emergência (emergency, medium)
btn6 = StandardButton("EMERGENCY STOP", variant="emergency")
```

---

## Boas Práticas

### 1. Hierarquia Visual

**✅ CERTO:**
```python
# Dialog de confirmação
layout = QVBoxLayout()

# Ação principal (destaque)
btn_confirmar = StandardButton("Confirmar", variant="primary-green", size="lg")

# Ação secundária
btn_cancelar = StandardButton("Cancelar", variant="secondary")

layout.addWidget(btn_confirmar)
layout.addWidget(btn_cancelar)
```

**❌ ERRADO:**
```python
# Ambos os botões têm mesmo destaque visual
btn_confirmar = StandardButton("Confirmar", variant="primary-green")
btn_cancelar = StandardButton("Cancelar", variant="primary-green")
```

### 2. Nomenclatura de Texto

**✅ USE:**
- Verbos no infinitivo: "Salvar", "Configurar", "Cancelar"
- Caixa alta apenas para emergências: "EMERGENCY STOP"
- Texto curto e direto: "Sim", "Não", "Fechar"

**❌ EVITE:**
- Frases longas: "Deseja realmente confirmar esta ação?"
- Pontuação: "Salvar.", "Cancelar?"
- Caixa alta exagerada: "SALVAR", "CONFIGURAR"

### 3. Posicionamento em Dialogs

**✅ CERTO (Padrão):**
```
┌─────────────────────────────────────┐
│  Configurar Câmera                  │
│  ┌───────────────────────────────┐  │
│  │                               │  │
│  └───────────────────────────────┘  │
│  [Cancelar]      [Configurar]       │  ← secondary à esquerda
│                                      ← primary à direita
└─────────────────────────────────────┘
```

**❌ ERRADO:**
```
┌─────────────────────────────────────┐
│  [Configurar]    [Cancelar]         │  ← Ordem inversa
└─────────────────────────────────────┘
```

### 4. Estados Disabled

**✅ CERTO:**
```python
# Desabilitar botão quando ação não disponível
btn_salvar.setEnabled(False)  # Estado desabilitado visualmente correto
```

---

## Migration Guide (v1.0 → v2.0)

### API Antiga (StyleManager)

```python
# ❌ OLD WAY (v1.0 - DEPRECATED)
from consumo_lib.ui.style_manager import StyleManager

btn = StyleManager.create_button("Salvar", 'primary')
```

### API Nova (StandardButton)

```python
# ✅ NEW WAY (v2.0 - RECOMMENDED)
from consumo_lib.ui.widget_standards import StandardButton

btn = StandardButton("Salvar", variant="primary-green")
```

### Mapeamento de Variants

| v1.0 (Old) | v2.0 (New) | Nota |
|------------|------------|------|
| `variant="primary"` | `variant="primary-green"` | Novo nome |
| `variant="secondary"` (azul sólido) | `variant="secondary"` (outline azul) | Novo visual |
| `variant="danger"` | `variant="emergency"` | Novo nome |
| N/A | `variant="primary-blue"` | Nova variante |
| N/A | `variant="primary-orange"` | Nova variante |

### Aviso de Deprecation

```python
# Ainda funciona, mas emite warning
btn = StandardButton("Salvar", variant="primary")
# DeprecationWarning: variant="primary" is deprecated.
# Use variant="primary-green" instead. Will be removed in v0.5.0
```

---

## Referências

- **Design Tokens:** `consumo_lib/ui/design_tokens.py`
- **Widget Standards:** `consumo_lib/ui/widget_standards.py`
- **Typography Guide:** `TYPOGRAPHY_GUIDE.md`
- **Material Design 3:** https://m3.material.io/components/buttons

---

**Última Atualização:** 2026-01-20
**Versão do Design System:** 2.0
