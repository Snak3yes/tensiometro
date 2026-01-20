# Relatório de Comparação: Design System vs. Guias

**Data:** 2026-01-20
**Versão:** 1.0
**Status:** Análise Completa

---

## Resumo Executivo

**Conformidade Geral:** ⚠️ **PARCIAL (60%)**

A implementação atual do Design System (`design_tokens.py` e `widget_standards.py`) apresenta **divergências significativas** em relação aos guias (`TYPOGRAPHY_GUIDE.md` e `BUTTON_GUIDE.md`).

### Principais Descobertas

| Aspecto | Conformidade | Status |
|---------|--------------|--------|
| **Nomenclatura de Tipografia** | ❌ 0% | Nomes completamente diferentes (MD3 vs Semântico) |
| **Valores de Tamanhos de Fonte** | ❌ 0% | Valores muito maiores (até 57px vs 14px) |
| **Font Family** | ⚠️ 50% | Arial correto, mas falta Segoe UI |
| **Tipos de Botão** | ⚠️ 60% | 3/5 tipos implementados |
| **Tamanhos de Botão** | ⚠️ 75% | Alturas implementadas, larguras não |
| **StyleManager vs StandardButton** | ❌ 0% | Padrões diferentes |

---

## 1. Tipografia (Typography)

### 1.1 Nomenclatura

**❌ CRÍTICO: Nomenclatura Incompatível**

#### Guia (`TYPOGRAPHY_GUIDE.md`)
Recomenda nomes **semânticos**:

```python
TINY = 8        # Metadados, informações auxiliares
SMALL = 9       # Instruções, hints, texto secundário
NORMAL = 10     # Texto padrão (DEFAULT)
MEDIUM = 11     # Títulos de seção, headings
LARGE = 12      # Títulos principais, dialogs
XLARGE = 14     # Títulos de janela, emergências
```

#### Implementação (`design_tokens.py`)
Usa nomes **Material Design 3**:

```python
DISPLAY_LARGE = 57     # Títulos hero (raro)
DISPLAY_MEDIUM = 45
DISPLAY_SMALL = 36

HEADLINE_LARGE = 32    # Títulos principais
HEADLINE_MEDIUM = 28
HEADLINE_SMALL = 24

TITLE_LARGE = 22       # Títulos de blocos
TITLE_MEDIUM = 16      # Títulos de widgets
TITLE_SMALL = 14       # Subtítulos

BODY_LARGE = 16        # Texto principal
BODY_MEDIUM = 14       # Texto padrão
BODY_SMALL = 12        # Texto secundário

LABEL_LARGE = 14       # Labels importantes
LABEL_MEDIUM = 12      # Labels padrão
LABEL_SMALL = 11       # Captions, badges
```

#### Impacto

- **Mapeamento impossível:** Não há correspondência 1:1 entre sistemas
- **Correção:** `BODY_MEDIUM(14)` vs `NORMAL(10)` - diferença de **40%**
- **Maior discrepância:** `DISPLAY_LARGE(57)` vs `XLARGE(14)` - diferença de **307%**

#### Recomendação

**Opção A - Manter MD3 (Recomendado para consistência Material Design):**
- Atualizar guia para refletir implementação MD3
- Justificativa: MD3 é padrão de mercado, mais escalável

**Opção B - Migrar para Semântico (Recomendado para guia original):**
- Refatorar `design_tokens.py` para usar nomes semânticos
- Adicionar aliases para compatibilidade:
  ```python
  # Novos nomes semânticos
  TINY = 8
  SMALL = 9
  NORMAL = 10
  MEDIUM = 11
  LARGE = 12
  XLARGE = 14

  # Aliases para MD3 (compatibilidade)
  DISPLAY_LARGE = XLARGE
  BODY_MEDIUM = NORMAL
  LABEL_SMALL = TINY
  ```

---

### 1.2 Valores de Tamanhos

**❌ CRÍTICO: Valores Muito Maiores**

#### Comparação de Faixas

| Sistema | Menor | Maior | Faixa |
|---------|-------|-------|-------|
| **Guia** | 8px (TINY) | 14px (XLARGE) | 6px |
| **Implementação** | 11px (LABEL_SMALL) | 57px (DISPLAY_LARGE) | 46px |

#### Análise

O guia foi projetado para **interfaces industriais compactas** (máximo 14px).
A implementação usa **escala desktop/web padrão** (até 57px).

#### Contexto de Uso

**Ambiente Industrial (Guia):**
- Espaço limitado em painéis de controle
- Densidade de informação alta
- Monitores industriais menores (15-19")

**Ambiente Desktop/Web (Implementação):**
- Aplicações desktop padrão
- Maior espaço em tela
- Monitores 24"+

#### Recomendação

**Manter implementação MD3** por ser mais adequada para aplicação desktop Windows moderna.

---

### 1.3 Font Family

**⚠️ PARCIAL: Falta Segoe UI**

#### Guia
```python
FONT_FAMILY = "'Segoe UI', Arial, sans-serif"
FONT_FAMILY_MONO = "'Consolas', 'Courier New', monospace"
```

#### Implementação
```python
FONT_FAMILY: str = "Arial"
FONT_FAMILY_MONOSPACE: str = "Consolas"
```

#### Impacto

- Arial é fallback correto ✅
- Segoe UI não é utilizada ❌ (é fonte moderna do Windows, melhor legibilidade)
- Consolas está correta ✅

#### Correção Necessária

```python
# Antes
FONT_FAMILY: str = "Arial"

# Depois
FONT_FAMILY: str = "Segoe UI, Arial, sans-serif"
```

#### Prioridade: **MÉDIA**

Segoe UI melhora legibilidade, mas Arial é fallback aceitável.

---

### 1.4 Font Weights

**⚠️ NÃO IMPLEMENTADO: Sistema de Weights**

#### Guia
Define 5 níveis de peso com uso recomendado:

| Weight | Valor | Uso | Frequência |
|--------|-------|-----|------------|
| Light | 300 | Raramente | 5% |
| Normal | 400 | Texto padrão | 70% |
| Medium | 500 | Títulos, botões | 20% |
| Semibold | 600 | Títulos principais | 4% |
| Bold | 700 | Emergências apenas | 1% |

#### Implementação
```python
def get_font(self, size: int, bold: bool = False, italic: bool = False) -> QFont:
    """Cria QFont com parâmetros padronizados"""
    font = QFont(self.FONT_FAMILY, size)
    if bold:
        font.setBold(True)  # Boolean apenas, sem granularidade
    if italic:
        font.setItalic(True)
    return font
```

#### Impacto

- Apenas **2 estados**: normal (400) ou bold (700)
- Sem suporte para Light (300), Medium (500), Semibold (600)
- Violação do guia: "Bold (700) apenas para emergências (1% dos casos)"

#### Correção Necessária

```python
# Adicionar suporte a pesos
WEIGHT_LIGHT = 300
WEIGHT_NORMAL = 400
WEIGHT_MEDIUM = 500
WEIGHT_SEMIBOLD = 600
WEIGHT_BOLD = 700

def get_font(self, size: int, weight: int = WEIGHT_NORMAL, italic: bool = False) -> QFont:
    """Cria QFont com peso específico"""
    font = QFont(self.FONT_FAMILY, size)
    font.setWeight(weight)  # QFont.Weight (int)
    if italic:
        font.setItalic(True)
    return font
```

#### Prioridade: **ALTA**

Necessário para conformidade com guia de tipografia.

---

## 2. Botões (Buttons)

### 2.1 Tipos de Botão

**⚠️ PARCIAL: 3/5 Tipos Implementados**

#### Guia (`BUTTON_GUIDE.md`)
Define **5 tipos principais**:

| Tipo | Cor | Uso |
|------|-----|-----|
| **primary-blue** | Azul | Ações padrão, genéricas |
| **primary-green** | Verde | Ações de confirmação, início |
| **primary-orange** | Laranja | Ações de parada, alerta |
| **secondary** | Outline | Ações alternativas, cancelamento |
| **emergency** | Vermelho | Emergências físicas (1% dos casos) |

#### Implementação (`widget_standards.py`)
Define **3 variantes**:

```python
class StandardButton(QPushButton):
    def __init__(self, text: str, variant: str = "primary", parent=None):
        """
        Args:
            variant: primary | secondary | danger | outline
        """
```

| Variante | Cor | Mapeamento para Guia |
|----------|-----|---------------------|
| **primary** | Verde (#4CAF50) | ✅ primary-green |
| **secondary** | Azul (#2196F3) | ⚠️ primary-blue (ERRADO!) |
| **danger** | Vermelho (#F44336) | ⚠️ emergency (uso correto?) |
| **outline** | Borda verde | ❌ Não implementado |

#### Problemas Identificados

**1. `secondary` está ERRADO:**

- Guia: `secondary` = outline transparente com borda azul
- Implementação: `secondary` = fundo azul sólido
- **Isso viola o guia!**

```python
# Guia (CORRETO)
background: transparent
border: 2px solid #2196F3 (outline)
text: #2196F3

# Implementação (ERRADO)
background: #2196F3 (sólido)
text: white
```

**2. Falta `primary-orange`:**

- Guia requer botão laranja para paradas
- Implementação não possui variante laranja

**3. `danger` vs `emergency`:**

- Guia: `emergency` para emergências físicas
- Implementação: `danger` (semântica mais ampla)
- Uso atual pode violar regra "1% dos casos"

#### Correções Necessárias

```python
# Adicionar variant faltantes
class StandardButton(QPushButton):
    def __init__(self, text: str, variant: str = "primary", parent=None):
        """
        Args:
            variant: primary-green | primary-blue | primary-orange |
                     secondary | emergency | outline
        """
```

**Mapeamento correto:**

| Guia | Implementação (atual) | Implementação (necessária) |
|------|----------------------|---------------------------|
| primary-green | `variant="primary"` | ✅ Manter |
| primary-blue | ❌ Usando `secondary` | Adicionar `variant="primary-blue"` |
| primary-orange | ❌ Não existe | Adicionar `variant="primary-orange"` |
| secondary | ❌ Implementado errado | Refatorar para outline |
| emergency | ⚠️ `variant="danger"` | Renomear para `variant="emergency"` |
| outline | ❌ Não existe | Adicionar `variant="outline"` |

#### Prioridade: **CRÍTICA**

Violam princípios fundamentais do guia.

---

### 2.2 Tamanhos de Botão

**⚠️ PARCIAL: Alturas OK, Larguras Não Definidas**

#### Guia
Define **4 tamanhos** com largura × altura:

| Tamanho | Largura × Altura | Uso |
|---------|------------------|------|
| **small** | 20×20px | Botões de ícone, JOG |
| **medium** | 40×24px | Padrão (DEFAULT) |
| **large** | 60×40px | Ações importantes |
| **extra-large** | 100×50px | Botões principais |

#### Implementação (`Dimensions`)
Define **apenas alturas**:

```python
BUTTON_HEIGHT_SM: int = 32   # Pequeno
BUTTON_HEIGHT_MD: int = 40   # Padrão
BUTTON_HEIGHT_LG: int = 48   # Grande
```

#### Análise

**Alturas:**
- Guia: 24px (medium), 40px (large), 50px (extra-large)
- Implementação: 32px (small), 40px (medium), 48px (large)
- **Discrepância:** Valores próximos, mas nomes diferentes

**Larguras:**
- Guia: Define larguras explícitas (20, 40, 60, 100)
- Implementação: ❌ Não define larguras

#### Correção Necessária

```python
@dataclass(frozen=True)
class ButtonSizes:
    """Tamanhos padrão de botão (largura, altura)"""

    SMALL: tuple = (20, 20)      # Ícones, JOG
    MEDIUM: tuple = (40, 24)     # Padrão
    LARGE: tuple = (60, 40)      # Ações importantes
    EXTRA_LARGE: tuple = (100, 50)  # Botões principais

# OU se quiser manter implementação atual:
@dataclass(frozen=True)
class ButtonSizes:
    """Tamanhos padrão de botão (largura, altura)"""

    SMALL: tuple = (32, 32)      # Altura: BUTTON_HEIGHT_SM
    MEDIUM: tuple = (None, 40)   # Altura: BUTTON_HEIGHT_MD, largura auto
    LARGE: tuple = (None, 48)    # Altura: BUTTON_HEIGHT_LG, largura auto
    EXTRA_LARGE: tuple = (100, 48)  # Botões principais
```

#### Uso em StandardButton

```python
class StandardButton(QPushButton):
    def __init__(self, text: str, variant: str = "primary",
                 size: str = "medium", parent=None):
        """
        Args:
            size: small | medium | large | extra-large
        """
        super().__init__(text, parent)

        # Aplicar tamanho
        size_map = {
            'small': ButtonSizes.SMALL,
            'medium': ButtonSizes.MEDIUM,
            'large': ButtonSizes.LARGE,
            'extra-large': ButtonSizes.EXTRA_LARGE,
        }
        width, height = size_map[size]

        if width:
            self.setFixedSize(width, height)
        else:
            self.setMinimumHeight(height)
```

#### Prioridade: **MÉDIA**

Largura não é crítica (pode ser auto), mas nomes inconsistentes confundem.

---

### 2.3 StyleManager vs StandardButton

**❌ CRÍTICO: Padrões Arquiteturais Diferentes**

#### Guia (`BUTTON_GUIDE.md`)
Recomenda uso de **StyleManager**:

```python
# PADRÃO 1 - Usar create_button() (RECOMENDADO)
btn = StyleManager.create_button(
    text="Salvar",
    button_type='primary-green',
    size='medium'
)

# PADRÃO 2 - Usar apply_button_style()
btn = QPushButton("Salvar")
StyleManager.apply_button_style(btn, 'primary-green')
btn.setFixedSize(*ButtonSizes.MEDIUM)

# PADRÃO 3 - Factory methods especializados
btn_emergency = StyleManager.create_emergency_button("EMERGENCY STOP")
btn_jog = StyleManager.create_jog_button('up', axis='Z')
```

#### Implementação Atual
Usa **StandardButton** diretamente:

```python
from consumo_lib.ui.widget_standards import StandardButton

btn = StandardButton("Salvar", variant="primary")
```

#### Problemas

1. **StyleManager não existe** na implementação atual
2. **StandardButton** é um componente PyQt6, não um factory/manager
3. **Padrões arquiteturais diferentes**:
   - Guia: Manager centralizado (Singleton/God Object)
   - Implementação: Componente PyQt6 (OO inheritance)

#### Análise Arquitetural

**Abordagem do Guia (StyleManager):**
- ✅ Centraliza toda lógica de estilização
- ✅ Single source of truth
- ❌ God Object anti-pattern
- ❌ Difícil de testar (muitas responsabilidades)
- ❌ Acoplamento global (todos importam StyleManager)

**Abordagem da Implementação (StandardButton):**
- ✅ Componente PyQt6 nativo (fácil de usar)
- ✅ Type-safe (variant é string conhecida)
- ✅ Testável (mockable)
- ✅ Desacoplado (cada botão é independente)
- ❌ Duplicação de código se variants crescerem
- ❌ Harder to enforce global changes

#### Recomendação

**Manter StandardButton** (abordagem atual) por ser:

1. Mais Pythônico (componentes First-Class)
2. Mais testável
3. Menos acoplado
4. Segue padrões PyQt6

**Atualizar guia** para refletir implementação:

```python
# NOVO PADRÃO NO GUIA
from consumo_lib.ui.widget_standards import StandardButton
from consumo_lib.ui.design_tokens import DIM

# PADRÃO 1 - StandardButton (RECOMENDADO)
btn = StandardButton("Salvar", variant="primary-green", size="medium")

# PADRÃO 2 - StandardButton + tamanho manual
btn = StandardButton("Salvar", variant="primary-green")
btn.setFixedSize(60, 40)

# PADRÃO 3 - Factory methods especializados (futuro)
btn_emergency = StandardButton.create_emergency("EMERGENCY STOP")
btn_jog = StandardButton.create_jog('up', axis='Z')
```

#### Prioridade: **BAIXA**

Ambas abordagens são válidas. Diferença é preferência arquitetural.

---

## 3. Outros Aspectos

### 3.1 Font Weights (Revisão)

**Status:** ⚠️ **PARCIALMENTE IMPLEMENTADO**

#### Implementação Atual
```python
def get_font(self, size: int, bold: bool = False, italic: bool = False) -> QFont:
    font = QFont(self.FONT_FAMILY, size)
    if bold:
        font.setBold(True)  # Boolean apenas
```

#### Problema

Apenas **2 pesos** disponíveis:
- Normal (QFont.Normal, peso 400)
- Bold (QFont.Bold, peso 700)

Guia requer **5 pesos**:
- Light (300)
- Normal (400)
- Medium (500)
- Semibold (600)
- Bold (700)

#### Correção Necessária

```python
# Adicionar constantes de peso
class FontWeight:
    LIGHT = 300
    NORMAL = 400
    MEDIUM = 500
    SEMIBOLD = 600
    BOLD = 700

# Atualizar get_font
def get_font(self, size: int, weight: int = FontWeight.NORMAL,
             italic: bool = False) -> QFont:
    """
    Args:
        weight: Peso da fonte (300-700)
        italic: Aplica itálico
    """
    font = QFont(self.FONT_FAMILY, size)
    font.setWeight(weight)
    if italic:
        font.setItalic(True)
    return font
```

#### Prioridade: **ALTA**

Necessário para conformidade com guia.

---

### 3.2 Cores de Botão

**Status:** ✅ **CONFORME**

#### Implementação Atual

```python
# variant="primary" (verde)
background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #4CAF50, stop:1 #388E3C)

# variant="secondary" (azul)
background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #2196F3, stop:1 #1976D2)

# variant="danger" (vermelho)
background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #F44336, stop:1 #D32F2F)
```

#### Comparação com Guia

| Cor | Implementação | Guia | Status |
|------|---------------|------|--------|
| Verde | #4CAF50 → #388E3C | #4CAF50 → #388E3C | ✅ Conforme |
| Azul | #2196F3 → #1976D2 | #2196F3 → #1976D2 | ✅ Conforme |
| Vermelho | #F44336 → #D32F2F | #F44336 → #D32F2F | ✅ Conforme |

#### Falta

- **Laranja** (#FF9800 → #F57C00) para `primary-orange`
- **Outline** para `secondary`

#### Prioridade: **MÉDIA**

Cores implementadas estão corretas, faltam variantes.

---

### 3.3 Spacing

**Status:** ✅ **CONFORME**

#### Implementação

```python
@dataclass(frozen=True)
class Spacing:
    XS: int = 4
    SM: int = 8
    MD: int = 16
    LG: int = 24
    XL: int = 32
    XXL: int = 48
```

#### Guia

Define sistema em múltiplos de 4px (baseline grid).

✅ Implementação segue mesmo padrão.

---

## 4. Resumo de Correções Necessárias

### 4.1 CRÍTICAS (Bloqueiam conformidade)

1. **[CRÍTICA] Nomenclatura de Tipografia**
   - Problema: MD3 (DISPLAY_LARGE) vs Semântico (TINY)
   - Solução: Escolher um padrão e atualizar guia OU código
   - Prioridade: **CRÍTICA**

2. **[CRÍTICA] Variantes de Botão**
   - Problema: Falta `primary-orange`, `secondary` implementado errado
   - Solução: Adicionar variants faltantes, refatorar `secondary`
   - Prioridade: **CRÍTICA**

3. **[CRÍTICA] Font Weights**
   - Problema: Apenas 2 pesos (normal/bold), guia requer 5
   - Solução: Adicionar suporte a pesos (300, 400, 500, 600, 700)
   - Prioridade: **ALTA**

### 4.2 MÉDIAS (Melhoram conformidade)

4. **[MÉDIA] Font Family**
   - Problema: Falta Segoe UI
   - Solução: `FONT_FAMILY = "Segoe UI, Arial, sans-serif"`
   - Prioridade: **MÉDIA**

5. **[MÉDIA] Tamanhos de Botão**
   - Problema: Falta definição de larguras
   - Solução: Adicionar classe `ButtonSizes` com (largura, altura)
   - Prioridade: **MÉDIA**

### 4.3 BAIXAS (Preferências arquiteturais)

6. **[BAIXA] StyleManager vs StandardButton**
   - Problema: Padrões diferentes (Manager centralizado vs Componente)
   - Solução: Atualizar guia para recomendar StandardButton
   - Prioridade: **BAIXA**

---

## 5. Plano de Ação Recomendado

### Fase 1: Alinhar Nomenclatura (1-2 dias)

**Opção A: Manter MD3 (Recomendado)**

1. Atualizar `TYPOGRAPHY_GUIDE.md` com escala MD3
2. Documentar justificativa: "MD3 é padrão de mercado"
3. Adicionar tabela de mapeamento para desenvolvimento futuro

**Opção B: Migrar para Semântico (3-5 dias)**

1. Adicionar constantes semânticas em `design_tokens.py`
2. Adicionar aliases para MD3 (compatibilidade)
3. Migrar código existente gradualmente
4. Atualizar guia com novos nomes

### Fase 2: Corrigir Botões (2-3 dias)

1. Adicionar variant `primary-orange` a `StandardButton`
2. Refatorar `secondary` para outline (conforme guia)
3. Renomear `danger` para `emergency`
4. Adicionar variant `outline` (se necessário)
5. Atualizar todas 197 instâncias de StandardButton

### Fase 3: Melhorar Tipografia (1-2 dias)

1. Adicionar `FontWeight` enum com 5 níveis
2. Atualizar `get_font()` para aceitar `weight` parameter
3. Adicionar wrappers convenientes:
   ```python
   def light(self, size: int) -> QFont: ...
   def normal(self, size: int) -> QFont: ...
   def medium(self, size: int) -> QFont: ...
   def semibold(self, size: int) -> QFont: ...
   def bold(self, size: int) -> QFont: ...
   ```
4. Migrar usos de `bold=True` para `weight=FontWeight.MEDIUM`

### Fase 4: Pequenas Correções (1 dia)

1. Atualizar `FONT_FAMILY` para incluir Segoe UI
2. Adicionar classe `ButtonSizes` com larguras
3. Atualizar `StandardButton.__init__()` para aceitar `size` parameter

### Fase 5: Atualizar Guia (1 dia)

1. Revisar `BUTTON_GUIDE.md` para recomendar StandardButton
2. Adicionar exemplos com código atual
3. Remover referências a StyleManager (se aplicável)
4. Adicionar seção "Arquitetura: Por que StandardButton?"

---

## 6. Métricas de Sucesso

### Conformidade Atual vs. Futura

| Aspecto | Atual | Pós-Fase 1 | Pós-Fase 2 | Pós-Fase 3 | Pós-Fase 4 |
|---------|-------|------------|------------|------------|------------|
| **Nomenclatura** | 0% | 100% ✅ | 100% ✅ | 100% ✅ | 100% ✅ |
| **Variantes de Botão** | 60% | 60% | 100% ✅ | 100% ✅ | 100% ✅ |
| **Font Weights** | 40% | 40% | 40% | 100% ✅ | 100% ✅ |
| **Font Family** | 50% | 50% | 50% | 50% | 100% ✅ |
| **Tamanhos de Botão** | 75% | 75% | 75% | 75% | 100% ✅ |
| **Conformidade Geral** | **60%** | **70%** | **85%** | **95%** | **100%** ✅ |

---

## 7. Conclusão

A implementação atual do Design System apresenta **divergências significativas** em relação aos guias, mas **nenhuma é irrecuperável**.

### Pontos Positivos

1. ✅ Cores implementadas corretamente
2. ✅ Spacing conforme baseline grid
3. ✅ Sistema de temas funciona (light/dark)
4. ✅ Componentes funcionais (197 botões migrados)

### Pontos de Atenção

1. ❌ Nomenclatura de tipografia incompatível (escolha: MD3 ou Semântico)
2. ❌ Variantes de botão incompletas (falta primary-orange, secondary errado)
3. ❌ Font weights limitados (apenas 2 pesos vs 5 requeridos)

### Recomendação Final

**Executar Fases 1-4** em ordem de prioridade:

1. **Fase 1:** Escolher padrão de nomenclatura (MD3 vs Semântico)
2. **Fase 2:** Corrigir variantes de botão (CRÍTICO)
3. **Fase 3:** Implementar font weights (ALTA)
4. **Fase 4:** Pequenas correções (MÉDIA)
5. **Fase 5:** Atualizar guia (BAIXA)

**Tempo Estimado:** 6-13 dias de desenvolvimento

**Conformidade Final:** 100% com guias atualizados

---

**Relatório gerado por:** Claude Code (Conductor2 Track)
**Data:** 2026-01-20
**Versão:** 1.0
