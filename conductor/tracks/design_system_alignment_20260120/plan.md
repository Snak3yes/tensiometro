# Design System Alignment Track - Implementation Plan

**Track ID:** design_system_alignment_20260120
**Status:** pending
**Start Date:** 2026-01-20
**Estimated Duration:** 6-13 days

---

## Overview

Este plano detalha a implementação da adequação completa do Design System aos guias estabelecidos (TYPOGRAPHY_GUIDE.md e BUTTON_GUIDE.md).

**Conformidade Atual:** 60%
**Conformidade Alvo:** 100%

---

## Development Phases

### Phase 1: Nomenclatura Decision (1-2 days)

**Objective:** Decidir e implementar nomenclatura unificada para tipografia.

**Decision Point:** MD3 vs Semântico

**Options Analysis:**

| Aspect | MD3 (Material Design 3) | Semântico (Guia Original) |
|--------|------------------------|---------------------------|
| **Padrão de mercado** | ✅ Sim (Google) | ❌ Não (custom) |
| **Escalabilidade** | ✅ 13 níveis | ⚠️ 6 níveis |
| **Legibilidade** | ✅ Maior (até 57px) | ⚠️ Menor (máx 14px) |
| **Industrial fitness** | ⚠️ Desktop/Web | ✅ Interface compacta |
| **Implementação atual** | ✅ Já existe | ❌ Requires refactoring |
| **Time de implementação** | ✅ 1 dia (atualizar guia) | ❌ 3-5 dias (refatorar código) |

**Recommendation:** **Manter MD3** (Option A)
- Justification: Padrão de mercado, mais escalável, já implementado
- Risk: Guias precisam ser atualizados (baixo risco)

**Alternative:** Migrar para Semântico (Option B)
- Justification: Guias originais, melhor para interfaces industriais
- Risk: Refactoring extenso, aliases para backward compatibility

---

#### Tasks

##### Task 1.1: Decision Meeting (4 hours)

**Description:** Reunião com stakeholders para decidir nomenclatura.

**Steps:**
1. Preparar apresentação com prós/contras
2. Agendar reunião com time técnico
3. Apresentar options analysis
4. Coletar feedback e decidir
5. Documentar decisão com justificativa

**Acceptance Criteria:**
- [ ] Decisão documentada em `conductor/tracks/design_system_alignment_20260120/DECISION_LOG.md`
- [ ] Justificativa clara registrada
- [ ] Riscos identificados e mitigados
- [ ] Time alinhado com decisão

**Deliverables:**
- DECISION_LOG.md com decisão registrada

---

##### Task 1.2: Implement Decision (Option A: MD3 - 4 hours OR Option B: Semântico - 2 days)

**Option A: Update Guide (1 day)**

**Steps:**
1. Fazer backup de TYPOGRAPHY_GUIDE.md
2. Reescrever seção "Escala de Tamanhos de Fonte" com MD3
3. Atualizar exemplos de código
4. Atualizar tabela de uso por componente
5. Adicionar seção "Por que Material Design 3?"
6. Revisar documentação completa
7. Commit com mensagem: `docs(typography): Update guide to use Material Design 3 scale`

**Acceptance Criteria:**
- [ ] TYPOGRAPHY_GUIDE.md usa nomenclatura MD3
- [ ] Todos os exemplos de código atualizados
- [ ] Justificativa para MD3 documentada
- [ ] Guia revisado e aprovado

**Option B: Refactor Code (2-3 days)**

**Steps:**
1. Adicionar constantes semânticas em Typography
2. Adicionar aliases para MD3 (compatibilidade)
3. Atualizar get_font() para aceitar ambos padrões
4. Criar métodos convenientes semânticos
5. Migrar código existente gradualmente
6. Atualizar testes unitários
7. Documentar mapeamento MD3 ↔ Semântico

**Acceptance Criteria:**
- [ ] Constantes semânticas definidas (TINY, SMALL, NORMAL, etc.)
- [ ] Aliases MD3 funcionais (DISPLAY_LARGE → XLARGE, etc.)
- [ ] get_font() aceita ambos padrões
- [ ] Testes unitários passam
- [ ] Cobertura ≥ 80%
- [ ] Documentação atualizada

**Deliverables:**
- TYPOGRAPHY_GUIDE.md atualizado (Option A) OU
- design_tokens.py refatorado (Option B)

---

##### Task 1.3: Verify Implementation (2 hours)

**Description:** Verificar conformidade da implementação.

**Steps:**
1. Criar checklist de conformidade
2. Verificar todos os usos de Typography no código
3. Confirmar que nomenclatura é consistente
4. Rodar testes unitários
5. Validar aplicação abre sem erros

**Acceptance Criteria:**
- [ ] 100% de usos de Typography usam nomenclatura correta
- [ ] 0 erros de sintaxe
- [ ] 0 erros de runtime
- [ ] Todos os testes passam
- [ ] Aplicação abre e funciona

**Deliverables:**
- Checklist de conformidade preenchido
- Logs de validação

---

### Phase 2: Button Variants (2-3 days)

**Objective:** Implementar todas as 5 variantes de botão conforme guia.

---

#### Tasks

##### Task 2.1: Implement New Variants (1 day)

**Description:** Adicionar primary-blue e primary-orange.

**Steps:**
1. Fazer backup de widget_standards.py
2. Adicionar variant="primary-blue"
3. Adicionar variant="primary-orange"
4. Criar estilos QSS para cada variante
5. Implementar hover states
6. Implementar disabled states
7. Testar visualmente cada variante

**Code Changes:**

```python
# widget_standards.py
class StandardButton(QPushButton):
    def __init__(self, text: str, variant: str = "primary-green", parent=None):
        """
        Args:
            variant: primary-green | primary-blue | primary-orange |
                     secondary | emergency | outline
        """
```

**QSS Styles:**

```python
# primary-blue (novo)
if variant == "primary-blue":
    self.setStyleSheet("""
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #2196F3, stop:1 #1976D2);
            color: white;
            border: 2px solid #1565C0;
            border-radius: 10px;
            font-weight: 500;
            padding: 8px 16px;
        }
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #1E88E5, stop:1 #1565C0);
        }
        QPushButton:disabled {
            background: #9E9E9E;
            border: 2px solid #757575;
        }
    """)

# primary-orange (novo)
elif variant == "primary-orange":
    self.setStyleSheet("""
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #FF9800, stop:1 #F57C00);
            color: white;
            border: 2px solid #EF6C00;
            border-radius: 10px;
            font-weight: 500;
            padding: 8px 16px;
        }
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #FFB74D, stop:1 #FF9800);
        }
        QPushButton:disabled {
            background: #9E9E9E;
            border: 2px solid #757575;
        }
    """)
```

**Acceptance Criteria:**
- [ ] variant="primary-blue" funciona
- [ ] variant="primary-orange" funciona
- [ ] Hover states funcionam
- [ ] Disabled states funcionam
- [ ] Gradientes visuais corretos
- [ ] Bordas corretas
- [ ] Testes unitários passam

**Deliverables:**
- widget_standards.py com novas variantes
- Screenshots de cada variante

---

##### Task 2.2: Refactor Secondary Variant (4 hours)

**Description:** Refatorar secondary para outline (transparente com borda).

**Problem:** Atualmente secondary é fundo azul sólido (ERRADO).

**Solution:** Mudar para transparente com borda azul.

**Steps:**
1. Analisar implementação atual de secondary
2. Criar novo estilo outline (transparente)
3. Manter backward compatibility (secondary-old → deprecated)
4. Atualizar documentação
5. Testar visualmente

**Code Changes:**

```python
# Antes (ERRADO)
if variant == "secondary":
    self.setStyleSheet("""
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #2196F3, stop:1 #1976D2);
            color: white;
            ...
        }
    """)

# Depois (CORRETO)
if variant == "secondary":
    self.setStyleSheet("""
        QPushButton {
            background: transparent;
            color: #2196F3;
            border: 2px solid #2196F3;
            border-radius: 5px;
            font-weight: 500;
            padding: 8px 16px;
        }
        QPushButton:hover {
            background: #E3F2FD;
        }
        QPushButton:disabled {
            background: transparent;
            color: #BDBDBD;
            border: 2px solid #BDBDBD;
        }
    """)
```

**Acceptance Criteria:**
- [ ] secondary é outline (transparente com borda)
- [ ] Hover state funciona (fundo azul claro)
- [ ] Disabled state funciona
- [ ] Visual conforme BUTTON_GUIDE.md
- [ ] Testes unitários passam

**Deliverables:**
- widget_standards.py com secondary refatorado
- Screenshot comparando antes/depois

---

##### Task 2.3: Rename danger to emergency (2 hours)

**Description:** Renomear variant="danger" para variant="emergency".

**Rationale:** Guia define "emergency" para emergências físicas, "danger" é muito genérico.

**Steps:**
1. Adicionar variant="emergency" (cópia de danger)
2. Marcar danger como deprecated (emitir warning)
3. Documentar período de transição
4. Atualizar testes
5. Criar guia de migração

**Code Changes:**

```python
class StandardButton(QPushButton):
    def __init__(self, text: str, variant: str = "primary-green", parent=None):
        """
        Args:
            variant: primary-green | primary-blue | primary-orange |
                     secondary | emergency | outline
        DEPRECATED:
            variant="danger" - Use "emergency" instead. Will be removed in v0.5.0.
        """
        # Emit warning se danger usado
        if variant == "danger":
            import warnings
            warnings.warn(
                'variant="danger" is deprecated. Use variant="emergency" instead. '
                'Will be removed in v0.5.0',
                DeprecationWarning,
                stacklevel=2
            )
            variant = "emergency"  # Auto-migrate

        if variant == "emergency":
            # ... estilo emergency
```

**Acceptance Criteria:**
- [ ] variant="emergency" funciona
- [ ] variant="danger" ainda funciona (com warning)
- [ ] Warning emitido quando danger usado
- [ ] Documentação atualizada
- [ ] Testes unitários passam

**Deliverables:**
- widget_standards.py com emergency
- Guia de migração (MIGRATION_V0.4_to_v0.5.md)

---

##### Task 2.4: Add Outline Variant (optional, 2 hours)

**Description:** Adicionar variant="outline" (caso seja necessário).

**Note:** Verificar se secondary outline é suficiente ou se precisa de outline em outras cores.

**Steps:**
1. Verificar requisitos com time
2. Se necessário, adicionar variant="outline"
3. Implementar estilo
4. Testar

**Acceptance Criteria:**
- [ ] Decisão tomada (precisa ou não)
- [ ] Se sim: variant="outline" implementado
- [ ] Testes unitários passam

---

##### Task 2.5: Update All 197 Button Instances (1 day)

**Description:** Atualizar todas as instâncias de StandardButton para usar variants corretos.

**Steps:**
1. Usar grep para encontrar todos StandardButton(..., variant=...)
2. Analisar contexto de cada uso
3. Mapear para nova variante correta
4. Criar script de migração automatizada
5. Executar migração
6. Revisar manualmente mudanças
7. Testar cada arquivo

**Migration Mapping:**

| Uso Atual | Deve Ser | Justificativa |
|-----------|----------|---------------|
| `variant="primary"` | `variant="primary-green"` | Manter, mas usar nome completo |
| `variant="secondary"` (ações genéricas) | `variant="primary-blue"` | Secondary é outline |
| `variant="danger"` | `variant="emergency"` | Renomear |
| `variant="secondary"` (cancelar) | `variant="secondary"` | Mantém (mas agora é outline) |

**Script de Migração:**

```python
# migrate_button_variants.py
import re
import os

MAPPING = {
    'variant="primary"': 'variant="primary-green"',
    # Adicionar outros mapeamentos conforme necessário
}

def migrate_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content
    for old, new in MAPPING.items():
        content = content.replace(old, new)

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Migrated: {filepath}")
        return True
    return False

# Encontrar todos os arquivos .py
for root, dirs, files in os.walk('consumo_lib'):
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            migrate_file(filepath)
```

**Acceptance Criteria:**
- [ ] 197 instâncias de StandardButton revisadas
- [ ] 100% usam variants corretos
- [ ] 0 warnings de deprecation em código novo
- [ ] Aplicação abre sem erros
- [ ] Testes funcionais passam

**Deliverables:**
- Script de migração executado
- Lista de arquivos modificados
- Logs de revisão manual

---

### Phase 3: Font Weights System (1-2 days)

**Objective:** Implementar sistema completo de 5 níveis de peso de fonte.

---

#### Tasks

##### Task 3.1: Add FontWeight Enum (2 hours)

**Description:** Adicionar enum com 5 níveis de peso.

**Steps:**
1. Criar classe FontWeight em design_tokens.py
2. Definir 5 constantes (LIGHT, NORMAL, MEDIUM, SEMIBOLD, BOLD)
3. Adicionar docstrings documentando uso (% de casos)
4. Adicionar type hints
5. Testar import

**Code Changes:**

```python
# design_tokens.py
from enum import IntEnum

class FontWeight(IntEnum):
    """
    Pesos de fonte conforme TYPOGRAPHY_GUIDE.md

    Usage Frequencies:
    - LIGHT (300): 5% - Raramente usado
    - NORMAL (400): 70% - Texto padrão, labels, instruções
    - MEDIUM (500): 20% - Títulos de seção, botões, headings
    - SEMIBOLD (600): 4% - Títulos principais, dialogs
    - BOLD (700): 1% - Emergências, alertas críticos
    """

    LIGHT = 300
    NORMAL = 400
    MEDIUM = 500
    SEMIBOLD = 600
    BOLD = 700
```

**Acceptance Criteria:**
- [ ] FontWeight definido
- [ ] 5 constantes com valores corretos
- [ ] Docstrings documentando uso
- [ ] Type hints funcionam
- [ ] Import funciona sem erros

**Deliverables:**
- design_tokens.py com FontWeight

---

##### Task 3.2: Update get_font() Method (2 hours)

**Description:** Atualizar get_font() para aceitar weight parameter.

**Steps:**
1. Modificar assinatura de get_font()
2. Adicionar weight parameter com default FontWeight.NORMAL
3. Implementar lógica de peso
4. Manter backward compatibility (bold boolean)
5. Adicionar warning se deprecated bold=True usado
6. Testar

**Code Changes:**

```python
class Typography:
    def get_font(self, size: int, weight: int = FontWeight.NORMAL,
                 italic: bool = False, bold: bool = None) -> QFont:
        """
        Cria QFont com parâmetros padronizados

        Args:
            size: Tamanho da fonte em pontos
            weight: Peso da fonte (FontWeight)
            italic: Aplica itálico
            bold: [DEPRECATED] Use weight=FontWeight.BOLD instead

        Returns:
            QFont configurada

        Examples:
            >>> # Novo (recomendado)
            >>> TYPO.get_font(14, weight=FontWeight.MEDIUM)
            >>>
            >>> # Legado (deprecated)
            >>> TYPO.get_font(14, bold=True)
        """
        # Emit warning se deprecated parâmetro usado
        if bold is not None:
            import warnings
            warnings.warn(
                'bold parameter is deprecated. Use weight=FontWeight.BOLD instead.',
                DeprecationWarning,
                stacklevel=2
            )
            if bold:
                weight = FontWeight.BOLD

        font = QFont(self.FONT_FAMILY, size)
        font.setWeight(weight)

        if italic:
            font.setItalic(True)

        return font
```

**Acceptance Criteria:**
- [ ] get_font() aceita weight parameter
- [ ] Default = FontWeight.NORMAL (400)
- [ ] bold=True ainda funciona (com warning)
- [ ] Warning emitido para código legado
- [ ] Testes unitários passam
- [ ] Backward compatibility mantida

**Deliverables:**
- design_tokens.py com get_font() atualizado

---

##### Task 3.3: Add Convenience Methods (2 hours)

**Description:** Adicionar methods convenientes para cada peso.

**Steps:**
1. Implementar light()
2. Implementar normal()
3. Implementar medium()
4. Implementar semibold()
5. Implementar bold()
6. Adicionar docstrings para cada método
7. Testar

**Code Changes:**

```python
class Typography:
    # ... existing code ...

    def light(self, size: int, italic: bool = False) -> QFont:
        """
        Font light (300) - raramente usado (5% dos casos)

        Args:
            size: Tamanho da fonte em pontos
            italic: Aplica itálico

        Returns:
            QFont com peso 300

        Example:
            >>> TYPO.light(11)  # Título muito sutil
        """
        return self.get_font(size, weight=FontWeight.LIGHT, italic=italic)

    def normal(self, size: int, italic: bool = False) -> QFont:
        """
        Font normal (400) - texto padrão (70% dos casos)

        Use para:
        - Texto corrido
        - Labels descritivos
        - Instruções
        - Mensagens informativas

        Args:
            size: Tamanho da fonte em pontos
            italic: Aplica itálico

        Returns:
            QFont com peso 400

        Example:
            >>> TYPO.normal(10)  # Texto padrão
        """
        return self.get_font(size, weight=FontWeight.NORMAL, italic=italic)

    def medium(self, size: int, italic: bool = False) -> QFont:
        """
        Font medium (500) - títulos, botões (20% dos casos)

        Use para:
        - Títulos de seção/grupo
        - Texto de botões
        - Labels de formulário
        - Cabeçalhos de coluna

        Args:
            size: Tamanho da fonte em pontos
            italic: Aplica itálico

        Returns:
            QFont com peso 500

        Example:
            >>> TYPO.medium(11)  # Título de seção
        """
        return self.get_font(size, weight=FontWeight.MEDIUM, italic=italic)

    def semibold(self, size: int, italic: bool = False) -> QFont:
        """
        Font semibold (600) - títulos principais (4% dos casos)

        Use para:
        - Título de dialogs
        - Título de janelas
        - Headings principais
        - Alertas importantes

        Args:
            size: Tamanho da fonte em pontos
            italic: Aplica itálico

        Returns:
            QFont com peso 600

        Example:
            >>> TYPO.semibold(14)  # Título de dialog
        """
        return self.get_font(size, weight=FontWeight.SEMIBOLD, italic=italic)

    def bold(self, size: int, italic: bool = False) -> QFont:
        """
        Font bold (700) - emergências apenas (1% dos casos)

        Use APENAS para:
        - Botões de EMERGENCY STOP
        - Alertas críticos de segurança
        - Avisos de perigo iminente

        ❌ NÃO USE para:
        - Títulos comuns (use semibold)
        - Botões normais (use medium)
        - Destaques gerais (use medium)

        Args:
            size: Tamanho da fonte em pontos
            italic: Aplica itálico

        Returns:
            QFont com peso 700

        Example:
            >>> TYPO.bold(14)  # EMERGENCY STOP
        """
        return self.get_font(size, weight=FontWeight.BOLD, italic=italic)
```

**Acceptance Criteria:**
- [ ] 5 methods implementados
- [ ] Docstrings detalhadas com exemplos
- [ ] Docstrings documentam quando usar (frequência)
- [ ] Docstrings documentam quando NÃO usar
- [ ] Testes unitários passam

**Deliverables:**
- design_tokens.py com 5 methods convenientes

---

##### Task 3.4: Write Unit Tests (4 hours)

**Description:** Escrever testes unitários para sistema de font weights.

**Steps:**
1. Criar test_font_weight.py
2. Testar cada nível de peso
3. Testar backward compatibility (bold=True)
4. Testar deprecation warning
5. Testar methods convenientes
6. Testar edge cases

**Test Cases:**

```python
# tests/unit/test_font_weight.py
import pytest
from PyQt6.QtGui import QFont
from consumo_lib.ui.design_tokens import TYPO, FontWeight

class TestFontWeight:
    """Testes para sistema de font weights"""

    def test_font_weight_enum_values(self):
        """Verifica valores do enum"""
        assert FontWeight.LIGHT == 300
        assert FontWeight.NORMAL == 400
        assert FontWeight.MEDIUM == 500
        assert FontWeight.SEMIBOLD == 600
        assert FontWeight.BOLD == 700

    def test_get_font_with_weight_parameter(self):
        """Testa get_font() com weight parameter"""
        font = TYPO.get_font(14, weight=FontWeight.MEDIUM)
        assert font.family() == "Arial"
        assert font.pointSize() == 14
        assert font.weight() == 500

    def test_get_font_default_weight(self):
        """Testa get_font() com peso padrão"""
        font = TYPO.get_font(14)
        assert font.weight() == 400  # FontWeight.NORMAL

    def test_get_font_deprecated_bold_parameter(self):
        """Testa backward compatibility com bold=True"""
        with pytest.warns(DeprecationWarning):
            font = TYPO.get_font(14, bold=True)
        assert font.weight() == 700

    def test_light_method(self):
        """Testa método light()"""
        font = TYPO.light(11)
        assert font.weight() == 300

    def test_normal_method(self):
        """Testa método normal()"""
        font = TYPO.normal(10)
        assert font.weight() == 400

    def test_medium_method(self):
        """Testa método medium()"""
        font = TYPO.medium(11)
        assert font.weight() == 500

    def test_semibold_method(self):
        """Testa método semibold()"""
        font = TYPO.semibold(14)
        assert font.weight() == 600

    def test_bold_method(self):
        """Testa método bold()"""
        font = TYPO.bold(14)
        assert font.weight() == 700

    def test_italic_parameter(self):
        """Testa parâmetro italic"""
        font = TYPO.get_font(14, italic=True)
        assert font.italic()

    def test_method_combinations(self):
        """Testa combinações de peso e itálico"""
        font = TYPO.medium(11, italic=True)
        assert font.weight() == 500
        assert font.italic()
```

**Acceptance Criteria:**
- [ ] 15+ test cases escritos
- [ ] Todos os testes passam
- [ ] Cobertura ≥ 80% para código novo
- [ ] Testes de edge cases cobertos
- [ ] Testes de backward compliance cobertos

**Deliverables:**
- test_font_weight.py com 15+ testes

---

### Phase 4: Small Corrections (1 day)

**Objective:** Implementar correções menores (Font Family e Button Sizes).

---

#### Tasks

##### Task 4.1: Update Font Family (1 hour)

**Description:** Atualizar FONT_FAMILY para incluir Segoe UI.

**Steps:**
1. Modificar constante FONT_FAMILY em Typography
2. Verificar compatibilidade Windows/Linux/Mac
3. Testar em Windows (Segoe UI disponível)
4. Testar em Linux (fallback Arial)
5. Documentar comportamento

**Code Changes:**

```python
# Antes
FONT_FAMILY: str = "Arial"

# Depois
FONT_FAMILY: str = "Segoe UI, Arial, sans-serif"
```

**Acceptance Criteria:**
- [ ] Segoe UI é primeira opção
- [ ] Arial é fallback
- [ ] Funciona em Windows (Segoe UI carregada)
- [ ] Funciona em Linux (Arial carregada como fallback)
- [ ] Testes unitários passam

**Deliverables:**
- design_tokens.py atualizado

---

##### Task 4.2: Add ButtonSizes Class (2 hours)

**Description:** Adicionar classe ButtonSizes com dimensões completas.

**Steps:**
1. Adicionar dataclass ButtonSizes em Dimensions
2. Definir 4 tamanhos (SMALL, MEDIUM, LARGE, EXTRA_LARGE)
3. Cada tamanho tem (largura, altura) como tuple
4. Adicionar docstrings
5. Testar

**Code Changes:**

```python
# design_tokens.py
from dataclasses import dataclass

@dataclass(frozen=True)
class ButtonSizes:
    """
    Tamanhos padrão de botão (largura, altura)

    Tamanhos disponíveis:
    - SMALL (20×20px): Botões de ícone, JOG, toggle
    - MEDIUM (40×24px): Botões padrão, DEFAULT
    - LARGE (60×40px): Botões de ação importante
    - EXTRA_LARGE (100×50px): Botões principais, calibração

    Usage:
        >>> from consumo_lib.ui.design_tokens import DIM
        >>> width, height = DIM.BUTTON_SIZES.MEDIUM
        >>> btn.setFixedSize(width, height)
    """

    SMALL: tuple = (20, 20)
    """Botões de ícone (20×20px)"""

    MEDIUM: tuple = (40, 24)
    """Botões padrão (40×24px) - DEFAULT"""

    LARGE: tuple = (60, 40)
    """Botões de ação importante (60×40px)"""

    EXTRA_LARGE: tuple = (100, 50)
    """Botões principais (100×50px)"""

# Adicionar a Dimensions
@dataclass(frozen=True)
class Dimensions:
    # ... existing code ...

    # BUTTON SIZES
    BUTTON_SIZES: ButtonSizes = ButtonSizes()
```

**Acceptance Criteria:**
- [ ] ButtonSizes definida
- [ ] 4 tamanhos com (largura, altura)
- [ ] Docstrings documentando uso
- [ ] Integrado com Dimensions
- [ ] Testes unitários passam

**Deliverables:**
- design_tokens.py com ButtonSizes

---

##### Task 4.3: Update StandardButton for Size Parameter (3 hours)

**Description:** Atualizar StandardButton para aceitar size parameter.

**Steps:**
1. Modificar __init__ para aceitar size parameter
2. Implementar lógica de tamanho
3. Aplicar dimensões corretamente
4. Suportar largura auto (None)
5. Testar todos os tamanhos

**Code Changes:**

```python
# widget_standards.py
from consumo_lib.ui.design_tokens import DIM, ButtonSizes

class StandardButton(QPushButton):
    def __init__(self, text: str, variant: str = "primary-green",
                 size: str = "medium", parent=None):
        """
        Botão padrão com estilo consistente

        Args:
            text: Texto do botão
            variant: primary-green | primary-blue | primary-orange |
                     secondary | emergency | outline
            size: small | medium | large | extra-large
            parent: Widget pai

        Variants:
            primary-green: Cor verde - ações principais/confirmação
            primary-blue: Cor azul - ações padrão/genéricas
            primary-orange: Cor laranja - ações de parada/atenção
            secondary: Outline - ações alternativas/cancelamento
            emergency: Vermelho - emergências físicas (1% dos casos)

        Sizes:
            small (20×20px): Botões de ícone
            medium (40×24px): Padrão, DEFAULT
            large (60×40px): Ações importantes
            extra-large (100×50px): Botões principais
        """
        super().__init__(text, parent)

        # Aplicar fonte padrão
        font = TYPO.get_font(TYPO.BODY_LARGE, bold=True)
        self.setFont(font)

        # Aplicar variante
        self._apply_variant(variant)

        # Aplicar tamanho
        self._apply_size(size)

    def _apply_size(self, size: str):
        """
        Aplica tamanho ao botão

        Args:
            size: small | medium | large | extra-large
        """
        size_map = {
            'small': DIM.BUTTON_SIZES.SMALL,
            'medium': DIM.BUTTON_SIZES.MEDIUM,
            'large': DIM.BUTTON_SIZES.LARGE,
            'extra-large': DIM.BUTTON_SIZES.EXTRA_LARGE,
        }

        if size not in size_map:
            raise ValueError(f"Invalid size: {size}. Must be one of: {list(size_map.keys())}")

        width, height = size_map[size]

        if width:
            self.setFixedSize(width, height)
        else:
            self.setMinimumHeight(height)
```

**Acceptance Criteria:**
- [ ] size parameter funciona
- [ ] Default = "medium"
- [ ] ValueError se size inválido
- [ ] Todos os 4 tamanhos funcionam
- [ ] Testes unitários passam
- [ ] Aplicação valida sem erros

**Deliverables:**
- widget_standards.py com size parameter
- Testes para cada tamanho

---

### Phase 5: Documentation Update (1 day)

**Objective:** Atualizar guias para refletir implementação final.

---

#### Tasks

##### Task 5.1: Update TYPOGRAPHY_GUIDE.md (2 hours)

**Description:** Atualizar guia com nomenclatura final.

**Steps:**
1. Revisar TYPOGRAPHY_GUIDE.md completo
2. Atualizar seção de escala de tamanhos
3. Atualizar exemplos de código
4. Atualizar tabela de uso por componente
5. Adicionar seção "Por que Material Design 3?" (se MD3 escolhido)
6. Revisar seção de font weights
7. Atualizar checklists

**Acceptance Criteria:**
- [ ] Guia usa nomenclatura final (MD3 ou Semântico)
- [ ] Todos os exemplos atualizados
- [ ] Seção de font weights atualizada (5 níveis)
- [ ] Font family atualizada (Segoe UI)
- [ ] Checklists funcionais

**Deliverables:**
- TYPOGRAPHY_GUIDE.md atualizado

---

##### Task 5.2: Update BUTTON_GUIDE.md (2 hours)

**Description:** Atualizar guia com StandardButton.

**Steps:**
1. Revisar BUTTON_GUIDE.md completo
2. Substituir StyleManager por StandardButton em exemplos
3. Adicionar seção "Arquitetura: Por que StandardButton?"
4. Atualizar tabela de tipos de botão (5 variantes)
5. Atualizar exemplos de código
6. Adicionar seção "Migração de Código Legado"
7. Remover referências a StyleManager (se aplicável)

**Acceptance Criteria:**
- [ ] Guia recomenda StandardButton
- [ ] 5 variantes documentadas
- [ ] Exemplos usam sintaxe correta
- [ ] Seção de arquitetura explica escolha
- [ ] Guia de migração incluído

**Deliverables:**
- BUTTON_GUIDE.md atualizado

---

##### Task 5.3: Create Migration Guide (2 hours)

**Description:** Criar guia de migração de código legado.

**Steps:**
1. Criar MIGRATION_GUIDE.md
2. Documentar mudanças breaking
3. Fornecer exemplos de antes/depois
4. Documentar período de transição
5. Adicionar FAQ

**Structure:**

```markdown
# Design System Migration Guide

## Overview
Mudanças no Design System v0.4 → v0.5

## Breaking Changes

### 1. Nomenclatura de Tipografia

**Antes:**
```python
TYPO.get_font(TYPO.NORMAL, bold=True)
```

**Depois:**
```python
TYPO.get_font(14, weight=FontWeight.MEDIUM)
```

### 2. Variantes de Botão

**Antes:**
```python
StandardButton("Salvar", variant="primary")
StandardButton("Cancelar", variant="secondary")  # Fundo azul
StandardButton("Excluir", variant="danger")
```

**Depois:**
```python
StandardButton("Salvar", variant="primary-green")
StandardButton("Cancelar", variant="secondary")  # Outline
StandardButton("Excluir", variant="emergency")
```

### 3. Font Family

**Antes:**
```python
FONT_FAMILY = "Arial"
```

**Depois:**
```python
FONT_FAMILY = "Segoe UI, Arial, sans-serif"
```

## Migration Steps

1. Atualizar variantes de botão
2. Substituir bold=True por weight=FontWeight.MEDIUM
3. Testar cada módulo modificado
4. Validar aplicação abre sem erros

## Timeline

- v0.4.0: Código legado ainda funciona (com warnings)
- v0.5.0: Código legado é removido
- v0.6.0: Warnings se tornam erros

## FAQ

**Q: Preciso atualizar todo o código de uma vez?**
A: Não, você pode migrar gradualmente. Código legado ainda funciona com warnings.

**Q: Posso manter usando bold=True?**
A: Sim, mas será removido em v0.5.0. Recomendamos migrar para weight parameter.
```

**Acceptance Criteria:**
- [ ] Guia de migração criado
- [ ] Exemplos de antes/depois claros
- [ ] Timeline definida
- [ ] FAQ útil

**Deliverables:**
- MIGRATION_GUIDE.md

---

##### Task 5.4: Update CLAUDE.md (1 hour)

**Description:** Atualizar CLAUDE.md com referências ao Design System alinhado.

**Steps:**
1. Procurar seções sobre Design System
2. Atualizar exemplos de código
3. Adicionar referência a MIGRATION_GUIDE.md
4. Atualizar seção de best practices

**Acceptance Criteria:**
- [ ] CLAUDE.md atualizado
- [ ] Exemplos de código corretos
- [ ] Referências funcionais

**Deliverables:**
- CLAUDE.md atualizado

---

##### Task 5.5: Update CHANGELOG (1 hour)

**Description:** Documentar mudanças no CHANGELOG.md.

**Steps:**
1. Adicionar entrada para v0.5.0
2. Listar todas as mudanças breaking
3. Listar novas features
4. Listar deprecations
5. Listar bugfixes

**Structure:**

```markdown
# Changelog

## [0.5.0] - 2026-01-20

### Added
- Sistema completo de font weights (5 níveis: LIGHT, NORMAL, MEDIUM, SEMIBOLD, BOLD)
- Variantes de botão: primary-blue, primary-orange
- Classe ButtonSizes com dimensões completas
- Suporte a Segoe UI como font family primária
- Methods convenientes: TYPO.light(), normal(), medium(), semibold(), bold()

### Changed
- Nomenclatura de tipografia unificada (Material Design 3)
- StandardButton agora aceita size parameter
- variant="secondary" agora é outline (transparente com borda)
- variant="danger" renomeado para variant="emergency"

### Deprecated
- get_font(bold=True) - Use get_font(weight=FontWeight.BOLD) instead
- variant="danger" - Use variant="emergency" instead
- variant="primary" - Use variant="primary-green" instead (alias ainda funciona)

### Fixed
- Font family agora inclui Segoe UI (Windows)
- Button sizes agora têm larguras definidas

### Migration Guide
See MIGRATION_GUIDE.md for detailed migration instructions.
```

**Acceptance Criteria:**
- [ ] CHANGELOG.md atualizado
- [ ] Todas as mudanças documentadas
- [ ] Versão e data corretas

**Deliverables:**
- CHANGELOG.md atualizado

---

## Quality Gates

### Gate 1: Phase 1 Complete (Nomenclatura)

- [ ] Decisão documentada e aprovada
- [ ] Implementação completa (guia OU código)
- [ ] 100% de conformidade na nomenclatura
- [ ] 0 erros de validação
- [ ] Aplicação abre sem erros

### Gate 2: Phase 2 Complete (Button Variants)

- [ ] 5 variantes implementadas
- [ ] 197 instâncias atualizadas
- [ ] 0 warnings de deprecation em código novo
- [ ] Testes visuais passam
- [ ] Aplicação funciona sem erros

### Gate 3: Phase 3 Complete (Font Weights)

- [ ] 5 níveis de peso implementados
- [ ] 15+ testes unitários passando
- [ ] Cobertura ≥ 80%
- [ ] Backward compatibility mantida
- [ ] 0 breaking changes não documentados

### Gate 4: Phase 4 Complete (Small Corrections)

- [ ] Segoe UI funcionando em Windows
- [ ] ButtonSizes implementada
- [ ] size parameter funcionando
- [ ] Testes passando
- [ ] Aplicação valida sem erros

### Gate 5: Phase 5 Complete (Documentation)

- [ ] Todos os guias atualizados
- [ ] Guia de migração criado
- [ ] CLAUDE.md atualizado
- [ ] CHANGELOG.md atualizado
- [ ] 0 inconsistências entre guia e código

---

## Test Strategy

### Unit Tests

**Cobertura Alvo:** ≥ 80% para código modificado

**Testes necessários:**
- test_font_weight.py (15+ testes)
- test_button_variants.py (20+ testes)
- test_button_sizes.py (10+ testes)
- test_standardbutton.py (30+ testes)

**Total:** 75+ testes unitários

### Integration Tests

**Cenários:**
1. Criar botão com cada variante
2. Criar botão com cada tamanho
3. Criar fonte com cada peso
4. Aplicar estilo e verificar resultado
5. Validar hover states
6. Validar disabled states

**Total:** 20+ testes de integração

### Visual Tests

**Cenários:**
1. Capturar screenshot de cada variante de botão
2. Verificar cores corretas
3. Verificar gradientes
4. Verificar bordas
5. Verificar estados (hover, disabled, pressed)

**Total:** 30+ screenshots

### E2E Tests

**Cenários:**
1. Abrir aplicação
2. Navegar por cada aba
3. Verificar que todos os botões aparecem corretos
4. Verificar que fontes estão corretas
5. Verificar não há warnings no console

**Total:** 5 testes E2E

---

## Rollback Plan

### Se Phase 1 Falhar (Nomenclatura)

**Reverter:**
- Restaurar TYPOPHONY_GUIDE.md do backup
- Reverter mudanças em design_tokens.py (se aplicável)

**Impacto:** Baixo (apenas documentação)

### Se Phase 2 Falhar (Button Variants)

**Reverter:**
- Restaurar widget_standards.py do backup
- Reverter mudanças nas 197 instâncias

**Impacto:** Médio (vários arquivos afetados)

**Comando:**
```bash
git revert <commit-hash>
```

### Se Phase 3 Falhar (Font Weights)

**Reverter:**
- Restaurar design_tokens.py do backup
- Remover test_font_weight.py

**Impacto:** Baixo (código isolado)

### Se Phase 4 Falhar (Small Corrections)

**Reverter:**
- Restaurar design_tokens.py e widget_standards.py

**Impacto:** Baixo (mudanças isoladas)

### Se Phase 5 Falhar (Documentation)

**Reverter:**
- Restaurar guias do backup

**Impacto:** Muito Baixo (apenas documentação)

---

## Success Criteria

### Quantitative

- [ ] Conformidade com guias: 100%
- [ ] Cobertura de testes: ≥ 80%
- [ ] Número de testes unitários: ≥ 75
- [ ] Número de testes de integração: ≥ 20
- [ ] Aplicação abre sem erros: ✓
- [ ] 0 warnings de PyQt6
- [ ] Startup time aumentou < 5%

### Qualitative

- [ ] Desenvolvedores entendem Design System
- [ ] Guias são claros e sem ambiguidade
- [ ] Código é consistente em toda aplicação
- [ ] Manutenção é facilitada
- [ ] Single source of truth estabelecido

---

## Timeline

### Sprint 1 (Days 1-2): Phase 1 - Nomenclatura
- Day 1: Task 1.1 (Decision Meeting) + Task 1.2 (Implement Decision)
- Day 2: Task 1.3 (Verify)

### Sprint 2 (Days 3-5): Phase 2 - Button Variants
- Day 3: Task 2.1 (New Variants) + Task 2.2 (Refactor Secondary)
- Day 4: Task 2.3 (Rename danger) + Task 2.4 (Outline optional)
- Day 5: Task 2.5 (Update 197 Instances)

### Sprint 3 (Days 6-7): Phase 3 - Font Weights
- Day 6: Task 3.1 (FontWeight Enum) + Task 3.2 (Update get_font)
- Day 7: Task 3.3 (Convenience Methods) + Task 3.4 (Unit Tests)

### Sprint 4 (Day 8): Phase 4 - Small Corrections
- Day 8: Task 4.1 (Font Family) + Task 4.2 (ButtonSizes) + Task 4.3 (Size Parameter)

### Sprint 5 (Day 9): Phase 5 - Documentation
- Day 9: Task 5.1-5.5 (Update all guides)

### Buffer (Days 10-13): Contingency
- Dias extras para imprevistos, testes adicionais, revisão

**Total Estimado:** 9-13 dias

---

## Dependencies

### Externas

- PyQt6 ≥ 6.0.0
- Python ≥ 3.10

### Internas

- design_tokens.py (modificar)
- widget_standards.py (modificar)
- 197 arquivos com StandardButton (atualizar)

### Bloqueios

- Nenhum (trabalho pode iniciar imediatamente)

---

## Risks & Mitigation

### Risk 1: Choice Between MD3 vs Semantic is Wrong

**Probability:** Medium (30%)
**Impact:** High (rework required)
**Mitigation:**
- Protótipo rápido (1 dia) antes de decisão final
- Reversão fácil se necessário
- Fase 1 isolada (baixo custo de reversão)

### Risk 2: Button Variant Migration Breaks Application

**Probability:** Low (10%)
**Impact:** High (application won't start)
**Mitigation:**
- Backward compatibility mantida
- Testes exhaustivos antes de commit
- Rollback plan documentado
- Feature flags se necessário

### Risk 3: Performance Degradation

**Probability:** Very Low (5%)
**Impact:** Medium (slower application)
**Mitigation:**
- Benchmarks antes/depois
- Profile de hotspot
- Cache de QFont objects

### Risk 4: Team Rejects Changes

**Probability:** Low (10%)
**Impact:** High (rework required)
**Mitigation:**
- Early involvement in decision meetings
- Protótipos visuais para aprovação
- Documentação clara de benefícios

---

## Notes

### Important Considerations

1. **Backward Compatibility é Crítico**
   - Manter aliases para nomes antigos
   - Emitir deprecation warnings
   - Período de transição de 2 meses

2. **Testes São Obrigatórios**
   - Não mudar sem testes
   - Cobertura ≥ 80%
   - Testes visuais para UI

3. **Documentação é Parte da Implementação**
   - Guia não é separado do código
   - Atualizar docstrings
   - Manter CHANGELOG

4. **Fases Podem Ser Paralelas**
   - Phase 2 e 3 podem ser feitas em paralelo
   - Phase 4 depende de Phase 2
   - Phase 5 depende de todas as anteriores

---

**Plan Version:** 1.0
**Last Updated:** 2026-01-20
**Author:** Claude Code (Conductor2)
