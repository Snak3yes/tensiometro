# Design System Alignment Track - Specification

**Track ID:** design_system_alignment_20260120
**Title:** Design System Alignment - Conformidade com Guias TYPOGRAPHY e BUTTON
**Status:** pending
**Created:** 2026-01-20
**Type:** Refactoring
**Priority:** High

---

## Overview

Alinhar completamente a implementação atual do Design System (`design_tokens.py` e `widget_standards.py`) com os guias estabelecidos (`TYPOGRAPHY_GUIDE.md` e `BUTTON_GUIDE.md`).

Atualmente, o Design System apresenta **60% de conformidade** com os guias, com divergências críticas em nomenclatura de tipografia, variantes de botão e sistema de font weights.

---

## Contexto

### Motivação

O projeto possui dois guias de design aprovados:
1. **TYPOGRAPHY_GUIDE.md** - Define sistema de tipografia para interfaces industriais compactas
2. **BUTTON_GUIDE.md** - Define padronização completa de botões

A implementação atual do Design System (`consumo_lib/ui/`) segue padrões diferentes, criando:
- Confusão entre desenvolvedores (qual padrão seguir?)
- Violações das diretrizes estabelecidas
- Inconsistência visual na aplicação
- Dificuldade de manutenção (duas "fontes de verdade")

### Problemas Identificados

**CRÍTICOS:**
1. Nomenclatura de tipografia incompatível (MD3 vs Semântico)
2. Variantes de botão incompletas (falta primary-orange, secondary implementado errado)
3. Font weights limitados (2 pesos vs 5 requeridos)

**MÉDIOS:**
4. Font family sem Segoe UI
5. Tamanhos de botão sem larguras definidas

**BAIXOS:**
6. StyleManager vs StandardButton (diferença arquitetural)

### Análise Completa

Ver relatório detalhado: `DESIGN_SYSTEM_COMPARISON_REPORT.md`

---

## Objetivos

### Objetivo Principal

Alinhar a implementação do Design System aos guias estabelecidos, alcançando **100% de conformidade**.

### Objetivos Específicos

1. **Tipografia:** Unificar nomenclatura (escolher MD3 ou Semântico)
2. **Botões:** Implementar todas as 5 variantes conforme guia
3. **Font Weights:** Suportar 5 níveis de peso (300, 400, 500, 600, 700)
4. **Font Family:** Incluir Segoe UI como primeira opção
5. **Tamanhos:** Definir larguras e alturas para botões
6. **Documentação:** Atualizar guias para refletir implementação final

---

## Funcional Requirements

### FR1: Nomenclatura de Tipografia Unificada

**Priority:** Critical
**Description:** O sistema deve utilizar uma única nomenclatura para tamanhos de fonte.

**Acceptance Criteria:**
- [ ] Escolha feita entre MD3 (Material Design 3) ou Semântico (TINY, SMALL, etc.)
- [ ] Guia atualizado para refletir nomenclatura escolhida
- [ ] Código (`design_tokens.py`) atualizado conforme escolha
- [ ] Todos os usos de Typography atualizados (verificar com grep)
- [ ] Testes unitários atualizados para refletir nova nomenclatura

**Technical Notes:**
- Se escolher MD3: Atualizar TYPOGRAPHY_GUIDE.md com escala MD3
- Se escolher Semântico: Adicionar constantes em design_tokens.py + aliases para compatibilidade

---

### FR2: Variantes de Botão Completas

**Priority:** Critical
**Description:** StandardButton deve suportar todas as 5 variantes definidas no BUTTON_GUIDE.md.

**Acceptance Criteria:**
- [ ] `variant="primary-green"` implementado (ou mantido como "primary")
- [ ] `variant="primary-blue"` implementado
- [ ] `variant="primary-orange"` implementado
- [ ] `variant="secondary"` refatorado para **outline** (transparente com borda)
- [ ] `variant="emergency"` implementado (renomeado de "danger")
- [ ] Stylesheets aplicados corretamente para cada variante
- [ ] Hover states funcionais para todas variantes
- [ ] Disabled states funcionais para todas variantes

**Current Implementation Issues:**
```python
# ATUAL (ERRADO)
variant="secondary"  # Fundo azul sólido

# NECESSÁRIO (CORRETO)
variant="secondary"  # Transparente com borda azul (outline)
variant="primary-blue"  # Fundo azul sólido
variant="primary-orange"  # Fundo laranja sólido
variant="emergency"  # Fundo vermelho (renomear de "danger")
```

**Migration Strategy:**
1. Adicionar novos variants sem quebrar existentes
2. Manter `variant="primary"` como alias para `primary-green`
3. Marcar `variant="danger"` como deprecated, manter por 1 ciclo
4. Atualizar 197 instâncias de StandardButton gradualmente

---

### FR3: Sistema de Font Weights Completo

**Priority:** High
**Description:** Typography deve suportar 5 níveis de peso conforme guia.

**Acceptance Criteria:**
- [ ] Classe `FontWeight` definida com 5 constantes (LIGHT, NORMAL, MEDIUM, SEMIBOLD, BOLD)
- [ ] Método `get_font()` atualizado para aceitar `weight` parameter
- [ ] Valor padrão de weight = `FontWeight.NORMAL` (400)
- [ ] Methods convenientes adicionados: `light()`, `normal()`, `medium()`, `semibold()`, `bold()`
- [ ] Backward compatibility mantida ( `bold=True` ainda funciona, mas com warning)
- [ ] Testes unitários para cada peso de fonte
- [ ] Documentação atualizada com exemplos

**API Design:**
```python
# Novo enum
class FontWeight:
    LIGHT = 300
    NORMAL = 400
    MEDIUM = 500
    SEMIBOLD = 600
    BOLD = 700

# Nova assinatura
def get_font(self, size: int, weight: int = FontWeight.NORMAL,
             italic: bool = False) -> QFont:
    """Cria QFont com peso específico"""

# Methods convenientes
def light(self, size: int) -> QFont:
    """Font light (300) - raramente usado"""

def normal(self, size: int) -> QFont:
    """Font normal (400) - texto padrão (70% dos casos)"""

def medium(self, size: int) -> QFont:
    """Font medium (500) - títulos, botões (20% dos casos)"""

def semibold(self, size: int) -> QFont:
    """Font semibold (600) - títulos principais (4% dos casos)"""

def bold(self, size: int) -> QFont:
    """Font bold (700) - emergências apenas (1% dos casos)"""
```

---

### FR4: Font Family com Segoe UI

**Priority:** Medium
**Description:** Font family deve priorizar Segoe UI (fonte moderna do Windows).

**Acceptance Criteria:**
- [ ] `FONT_FAMILY` atualizado para `"Segoe UI, Arial, sans-serif"`
- [ ] `FONT_FAMILY_MONOSPACE` mantido como `"Consolas, 'Courier New', monospace"`
- [ ] Verificação de compatibilidade com Windows/Linux/Mac
- [ ] Fallback funciona se Segoe UI não disponível

**Technical Notes:**
- Segoe UI está disponível no Windows Vista+
- Arial é fallback universal (sempre disponível)
- Sem impacto em Linux/Mac (usam Arial automaticamente)

---

### FR5: Tamanhos de Botão com Larguras

**Priority:** Medium
**Description:** Sistema deve definir larguras e alturas para todos os tamanhos de botão.

**Acceptance Criteria:**
- [ ] Classe `ButtonSizes` adicionada a `Dimensions`
- [ ] 4 tamanhos definidos: SMALL, MEDIUM, LARGE, EXTRA_LARGE
- [ ] Cada tamanho tem (largura, altura) como tuple
- [ ] `StandardButton.__init__()` atualizado para aceitar `size` parameter
- [ ] Tamanho padrão = "medium"
- [ ] Largura pode ser `None` para auto-sizing

**API Design:**
```python
@dataclass(frozen=True)
class ButtonSizes:
    """Tamanhos padrão de botão (largura, altura)"""

    SMALL: tuple = (20, 20)      # Botões de ícone
    MEDIUM: tuple = (40, 24)     # Padrão
    LARGE: tuple = (60, 40)      # Ações importantes
    EXTRA_LARGE: tuple = (100, 50)  # Botões principais

# Uso em StandardButton
class StandardButton(QPushButton):
    def __init__(self, text: str, variant: str = "primary-green",
                 size: str = "medium", parent=None):
        """
        Args:
            size: small | medium | large | extra-large
        """
        # Aplicar tamanho
        width, height = ButtonSizes[size.upper()]
        if width:
            self.setFixedSize(width, height)
        else:
            self.setMinimumHeight(height)
```

---

### FR6: Atualização de Guias

**Priority:** Low
**Description:** Guias devem refletir implementação final (não vice-versa).

**Acceptance Criteria:**
- [ ] `TYPOGRAPHY_GUIDE.md` atualizado com nomenclatura final
- [ ] `BUTTON_GUIDE.md` atualizado para recomendar StandardButton
- [ ] Exemplos de código atualizados em ambos guias
- [ ] Seção "Arquitetura" adicionada explicando StandardButton vs StyleManager
- [ ] Seção "Migração" adicionada com exemplos de código legado vs novo
- [ ] Relatório de conformidade atualizado (100%)

---

## Non-Functional Requirements

### NFR1: Backward Compatibility

**Priority:** High
**Description:** Mudanças não devem quebrar código existente.

**Requirements:**
- Manter aliases para nomes antigos (ex: `danger` → `emergency`)
- Emitir deprecation warnings para código antigo
- Documentar período de transição (ex: "danger" será removido em v0.5.0)

---

### NFR2: Performance

**Priority:** Medium
**Description:** Mudanças não devem degradar performance da aplicação.

**Requirements:**
- Criação de fontes deve ser < 1ms
- Aplicação de estilos de botão deve ser < 5ms
- Startup time não deve aumentar > 5%

---

### NFR3: Testabilidade

**Priority:** High
**Description:** Todas as mudanças devem ser testáveis.

**Requirements:**
- Testes unitários para cada nova variante de botão
- Testes unitários para cada peso de fonte
- Testes de integração para StandardButton
- Cobertura de testes ≥ 80% para código modificado

---

### NFR4: Documentation

**Priority:** Medium
**Description:** Todas as mudanças devem ser documentadas.

**Requirements:**
- Docstrings atualizadas para métodos modificados
- Exemplos de uso em docstrings
- CHANGELOG.md atualizado com mudanças
- CLAUDE.md atualizado se necessário

---

## Use Cases

### UC1: Desenvolvedor Cria Botão com Nova Variante

**Actor:** Desenvolvedor
**Precondition:** Design System alinhado
**Main Flow:**
1. Desenvolvedor importa StandardButton
2. Cria botão com `variant="primary-orange"`
3. Botão aparece com gradiente laranja correto
4. Hover state funciona
5. Disabled state funciona

**Postcondition:** Botão funciona conforme BUTTON_GUIDE.md

---

### UC2: Desenvolvedor Usa Font Weight Semibold

**Actor:** Desenvolvedor
**Precondition:** Sistema de font weights implementado
**Main Flow:**
1. Desenvolvedor chama `TYPO.semibold(14)` para título de seção
2. QFont retornado com peso 600
3. Texto renderizado corretamente
4. Consistente com guia (semibold para títulos de seção)

**Postcondition:** Título de seção com peso correto

---

### UC3: Desenvolvedor Migra Código Legado

**Actor:** Desenvolvedor
**Precondition:** Código legado usa variant antiga
**Main Flow:**
1. Desenvolvedor vê warning de deprecation
2. Consulta documentação para nova sintaxe
3. Atualiza código para nova variante
4. Warning desaparece
5. Funcionalidade mantida

**Postcondition:** Código migrado sem quebras

---

## Technical Constraints

### TC1: PyQt6 Compatibility

Todas as mudanças devem ser compatíveis com PyQt6.
- QFont.setWeight() aceita int (300-700)
- QSS (Qt Style Sheets) suporta gradientes

### TC2: Python 3.10+

Código deve ser compatível com Python 3.10+.
- Type hints usando `str | None` require Python 3.10+
- Usar `Optional[str]` para Python 3.9 compatibility

### TC3: Windows, Linux, Mac

Design System deve funcionar em todos os 3 SOs.
- Segoe UI disponível apenas Windows (fallback Arial)
- Consolas pode não existir em Linux (fallback monospace)

---

## Dependencies

### Internas

- `consumo_lib/ui/design_tokens.py` - Modificar Typography, Dimensions
- `consumo_lib/ui/widget_standards.py` - Modificar StandardButton
- `TYPOGRAPHY_GUIDE.md` - Atualizar nomenclatura
- `BUTTON_GUIDE.md` - Atualizar exemplos

### Externas

- PyQt6 >= 6.0.0
- Python >= 3.10

---

## Risk Assessment

### Risco 1: Breaking Change em StandardButton

**Probabilidade:** Alta
**Impacto:** Alto
**Mitigation:**
- Manter backward compatibility com aliases
- Emitir deprecation warnings
- Documentar migração passo-a-passo
- Período de transição de 2 meses

### Risco 2: Escolha Errada de Nomenclatura (MD3 vs Semântico)

**Probabilidade:** Média
**Impacto:** Alto
**Mitigation:**
- Discussão com time antes de implementar
- Análise de prós/contras documentada
- Protótipo rápido antes de decisão final
- Reversão fácil se escolha errada

### Risco 3: Performance Degradation

**Probabilidade:** Baixa
**Impacto:** Médio
**Mitigation:**
- Benchmark antes/depois
- Cache de QFont objects
- Lazy loading de estilos

---

## Success Metrics

### Quantitativas

- [ ] 100% de conformidade com guias (medido por checklist)
- [ ] 0 erros de validação em StyleManager (se implementado)
- [ ] ≥ 80% cobertura de testes para código modificado
- [ ] 0 warnings de PyQt6 em runtime
- [ ] Startup time aumentou < 5%

### Qualitativas

- [ ] Desenvolvedores entendem qual padrão seguir
- [ ] Guias são claros e sem ambiguidade
- [ ] Código é consistente em toda aplicação
- [ ] Manutenção é facilitada (single source of truth)

---

## Out of Scope

### Não será implementado nesta track:

1. **StyleManager centralizado** (manter StandardButton)
2. **Novos componentes** (focus em alinhar existentes)
3. **Migração completa de código legado** (após conformidade 100%)
4. **Anim/Motion design** (futuro)
5. **Dark theme refinements** (já funciona)

---

## References

- `DESIGN_SYSTEM_COMPARISON_REPORT.md` - Análise completa de discrepâncias
- `TYPOGRAPHY_GUIDE.md` - Guia de tipografia
- `BUTTON_GUIDE.md` - Guia de botões
- `consumo_lib/ui/design_tokens.py` - Implementação atual
- `consumo_lib/ui/widget_standards.py` - StandardButton
- Material Design 3: https://m3.material.io/styles

---

**Spec Version:** 1.0
**Last Updated:** 2026-01-20
**Author:** Claude Code (Conductor2)
