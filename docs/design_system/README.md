# Design System - Tensiometro

Sistema de design unificado para garantir consistência visual e facilitar manutenção da interface do Tensiometro.

## 📋 Índice

- [O que é](#o-que-é)
- [Benefícios](#benefícios)
- [Arquitetura](#arquitetura)
- [Como Começar](#como-começar)
- [Exemplos Rápidos](#exemplos-rápidos)
- [Documentação Detalhada](#documentação-detalhada)

---

## O que é

O Design System do Tensiometro é uma coleção centralizada de:

- **Design Tokens**: Cores, fontes, espaçamentos, dimensões
- **Componentes Base**: Botões, inputs, labels padronizados
- **Stylesheet Global**: Estilos Qt consistentes (styles.qss)
- **Helpers**: Funções utilitárias para layouts

Baseado em **Material Design 3** com adaptações para o domínio industrial do Tensiometro.

---

## Benefícios

### Para Desenvolvedores

✅ **Single Source of Truth**: Cores e tamanhos definidos em um único lugar
✅ **Type-Safe**: Tokens são constantes, não strings mágicas
✅ **Fácil Refatoração**: Alterar cor primária afeta toda a aplicação
✅ **Consistência**: Componentes padronizados evitam retrabalho
✅ **Autocompletção**: IDE sugere tokens disponíveis

### Para o Projeto

✅ **Manutenibilidade**: Menos código duplicado
✅ **Escalabilidade**: Novos componentes seguem padrões estabelecidos
✅ **Qualidade**: Interface consistente em todas as telas
✅ **Professionalism**: Visual polido seguindo padrões de mercado

---

## Arquitetura

```
consumo_lib/ui/
├── __init__.py              # Exports públicos (COLORS, TYPO, etc)
├── design_tokens.py         # 9 singletons de tokens (928 linhas)
├── widget_standards.py      # 7 componentes base (226 linhas)
├── theme_manager.py         # Gerenciador de temas (206 linhas)
├── helpers.py               # 5 funções utilitárias (138 linhas)
└── styles.qss               # Stylesheet global (544 linhas)
```

### Camadas do Design System

```
┌─────────────────────────────────────┐
│   Aplicação (main.py, tabs, etc)   │  ← Usa Design System
├─────────────────────────────────────┤
│   Componentes Base                  │  ← StandardButton, etc
├─────────────────────────────────────┤
│   Design Tokens                     │  ← COLORS, TYPO, SPACE, DIM
├─────────────────────────────────────┤
│   Qt Framework                      │  ← QPushButton, QLabel, etc
└─────────────────────────────────────┘
```

---

## Como Começar

### Instalação

O Design System já está incluído no Tensiometro. Basta importar:

```python
# No topo do seu arquivo
from consumo_lib.ui import COLORS, TYPO, SPACE, DIM
from consumo_lib.ui.widget_standards import StandardButton, StandardLabel
from consumo_lib.ui.theme_manager import init_theme_manager
```

### Inicialização (main.py)

```python
from PyQt6.QtWidgets import QApplication
from consumo_lib.ui.theme_manager import init_theme_manager

def main():
    app = QApplication(sys.argv)

    # Inicializa Design System
    theme_mgr = init_theme_manager(app)
    # Stylesheet global aplicado automaticamente

    window = MinhaJanela()
    window.show()
    sys.exit(app.exec())
```

---

## Exemplos Rápidos

### 1. Usar Cores

```python
from consumo_lib.ui import COLORS

# Antes: hardcoded string
btn.setStyleSheet(f"background-color: #4CAF50;")

# Depois: design token
btn.setStyleSheet(f"background-color: {COLORS.PRIMARY};")
```

### 2. Usar Fontes

```python
from consumo_lib.ui import TYPO

# Antes: QFont manual
font = QFont()
font.setPointSize(14)
font.setBold(True)
label.setFont(font)

# Depois: token
label.setFont(TYPO.get_font(TYPO.BODY_MEDIUM, bold=True))
```

### 3. Usar Espaçamentos

```python
from consumo_lib.ui import SPACE

# Antes: hardcoded
layout.setContentsMargins(16, 16, 16, 16)
layout.setSpacing(16)

# Depois: tokens
layout.setContentsMargins(SPACE.MD, SPACE.MD, SPACE.MD, SPACE.MD)
layout.setSpacing(SPACE.MD)
```

### 4. Usar Dimensões

```python
from consumo_lib.ui import DIM

# Antes: hardcoded
btn.setMinimumHeight(40)

# Depois: token
btn.setMinimumHeight(DIM.BUTTON_HEIGHT_MD)
```

### 5. Usar Componentes Padrão

```python
from consumo_lib.ui.widget_standards import StandardButton

# Antes: QPushButton manual
btn = QPushButton("Salvar")
btn.setFont(QFont("Arial", 14, QFont.Bold))
btn.setMinimumHeight(40)
btn.setStyleSheet("...")

# Depois: componente pronto
btn = StandardButton("Salvar", variant="primary")
```

---

## Documentação Detalhada

### 🎨 [TOKENS.md](./TOKENS.md)
Referência completa de todos os design tokens:
- **Cores**: Quando usar cada cor (PRIMARY, SECONDARY, ERROR, etc)
- **Tipografia**: Escala de tipos (BODY, HEADING, LABEL)
- **Espaçamentos**: Sistema de grid 4px
- **Dimensões**: Alturas de botões, diálogos, inputs
- **Elevação**: Sombras e layering
- **Opacidade**: Estados hover, focus, disabled
- **Transições**: Durações e easing functions
- **Breakpoints**: Responsividade
- **Acessibilidade**: Padrões WCAG

### 🧩 [COMPONENTS.md](./COMPONENTS.md)
Guia de componentes base:
- **StandardButton**: 4 variantes (primary, secondary, danger, outline)
- **StandardLabel**: 4 variantes (heading, subheading, body, caption)
- **StandardInput**: Input com altura padronizada
- **StandardSpinBox**: Spinners numéricos
- **StandardComboBox**: Dropdowns
- **StandardGroupBox**: Agrupamentos
- Exemplos de uso para cada componente

### 🔄 [MIGRATION.md](./MIGRATION.md)
Guia de migração para código legado:
- Como substituir valores hardcoded
- Padrões de refatoração
- Before/After de arquivos migrados
- Checklists de validação

---

## Perguntas Frequentes

### Quando devo usar o Design System?

**Sempre** que possível para código novo. Para código legado, migre gradualmente durante refatorações.

### Posso criar minhas próprias cores?

**Sim**, mas prefira tokens existentes. Se necessário, pode adicionar cores customizadas em `design_tokens.py`.

### O Design System suporta temas dark?

**Parcialmente**. ThemeManager tem suporte para light/dark, mas dark mode ainda está em desenvolvimento (placeholder).

### Como faço override de um estilo?

Use `setStyleSheet()` localmente. O stylesheet global é aplicado primeiro, depois estilos locais sobrescrevem.

```python
# Usa design tokens + override local
btn.setStyleSheet(f"""
    QPushButton {{
        background-color: {COLORS.PRIMARY};
        border: 2px solid {COLORS.PRIMARY_DARK};
    }}
    QPushButton:hover {{
        background-color: {COLORS.PRIMARY_DARK};
    }}
""")
```

---

## Status do Projeto

- **Fase 1**: ✅ Fundação (design tokens, stylesheet, componentes)
- **Fase 2**: ✅ Theme Manager (integração com main.py)
- **Fase 3**: ✅ Migração Parcial (status_badge, movement_control)
- **Fase 4**: 🔄 Documentação (este arquivo)

### Arquivos Migrados

- ✅ `consumo_lib/widgets/status_badge.py`
- ✅ `consumo_lib/widgets/movement_control.py`

### Próximos Passos

- ⏳ Migrar 8 arquivos críticos restantes
- ⏳ Implementar dark mode completo
- ⏳ Adicionar mais componentes base (StandardCheckBox, StandardRadioButton)

---

## Contribuindo

Ao adicionar novos componentes ou tokens:

1. **Siga os padrões existentes**: Use dataclasses frozen para tokens
2. **Docstrings completas**: Explique quando usar cada token
3. **Type hints**: Use type hints em todos os métodos
4. **Testes**: Teste visualmente no contexto da aplicação
5. **Documente**: Atualize README e guias relacionados

---

## Licença

Parte do projeto Tensiometro.

---

**Última atualização**: 2026-01-19
**Versão**: 1.0.0
**Autor**: RONALDBUZAGLO
