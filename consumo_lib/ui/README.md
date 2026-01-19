# Design System - Tensiometro

## 📋 Visão Geral

Este diretório contém o **Design System oficial** do projeto Tensiometro, estabelecendo uma padronização completa de interface usada em toda a aplicação.

## 🎯 Objetivos

- **Centralizar constantes de design** (cores, fontes, espaçamentos, dimensões)
- **Fornecer componentes base reutilizáveis** (botões, labels, inputs padronizados)
- **Gerenciar temas** (light/dark mode)
- **Garantir consistência visual** em toda aplicação
- **Facilitar manutenção** (alterar em 1 lugar = refletir em toda app)

## 📂 Estrutura do Diretório

```
consumo_lib/ui/
├── __init__.py              # Exports públicos do módulo
├── README.md                # Este arquivo
├── design_tokens.py         # Constantes de design (COLORS, TYPO, SPACE, DIM)
├── widget_standards.py      # Componentes base (StandardButton, StandardLabel, etc.)
├── theme_manager.py         # Gerenciador de temas
├── helpers.py               # Funções utilitárias para UI
└── styles.qss               # Qt Style Sheet global
```

## 🚀 Como Usar

### Importar Tokens de Design

```python
from consumo_lib.ui import COLORS, TYPO, SPACE, DIM

# Cores
btn.setStyleSheet(f"background-color: {COLORS.PRIMARY};")
label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY};")

# Tipografia
font = TYPO.get_font(TYPO.BODY_LARGE, bold=True)
label.setFont(font)

# Espaçamentos
layout.addSpacing(SPACE.MD)
widget.setContentsMargins(SPACE.MD, SPACE.MD, SPACE.MD, SPACE.MD)

# Dimensões
btn.setMinimumHeight(DIM.BUTTON_HEIGHT_MD)
dialog.setFixedSize(*DIM.DIALOG_MEDIUM)
```

### Usar Componentes Padrão

```python
from consumo_lib.ui.widget_standards import StandardButton, StandardLabel

# Botão com variantes
btn_save = StandardButton("Salvar", variant="primary")
btn_cancel = StandardButton("Cancelar", variant="secondary")
btn_delete = StandardButton("Excluir", variant="danger")

# Label com variantes
title = StandardLabel("Título", variant="heading")
body = StandardLabel("Texto normal")
caption = StandardLabel("Caption", variant="caption")
```

### Inicializar Theme Manager

```python
from consumo_lib.main_window import AOIControllerApp
from consumo_lib.ui.theme_manager import init_theme_manager

app = QApplication(sys.argv)
window = AOIControllerApp(...)

# Inicializar tema (carrega styles.qss)
init_theme_manager(app)

window.show()
sys.exit(app.exec())
```

## 🎨 Conceitos Principes

### Design Tokens

Tokens são constantes centralizadas que definem aspectos visuais da aplicação:

- **ColorPalette:** 30+ cores seguindo Material Design 3
- **Typography:** Type scale completo (display, headline, title, body, label)
- **Spacing:** Baseline grid de 4px
- **Dimensions:** Tamanhos padronizados (botões, inputs, dialogs)

### Componentes Base

Classes PyQt6 estendidas com estilos consistentes:

- **StandardButton:** Botões com variantes (primary, secondary, danger, outline)
- **StandardLabel:** Labels com variantes (heading, subheading, body, caption)
- **StandardInput/SpinBox/ComboBox:** Inputs com altura padronizada
- **StandardGroupBox:** GroupBox com espaçamento consistente

### Theme Manager

Gerencia estilos globais e temas:

- Carrega `styles.qss` automaticamente
- Aplica stylesheet globalmente
- Suporta alternância de temas (light/dark futuramente)
- Singleton pattern para acesso global

## 📐 Princípios de Design

### Material Design 3

O Design System segue o **Material Design 3** do Google:

- Cores vibrantess e acessíveis
- Type scale consistente
- Elevation system para layering
- Componentes com estados interativos claros

### Consistência

- **Uma fonte de verdade:** Tokens são os únicos valores válidos
- **Sem valores hardcoded:** Código não deve ter cores/fontes/tamanhos hardcoded
- **Autocomplete:** Desenvolvedores usam `COLORS.`, `TYPO.`, `DIM.` com autocomplete

### Manutenibilidade

- **Alteração centralizada:** Mudar 1 token = refletir em toda app
- **Zero breaking changes:** Componentes legados continuam funcionando
- **Migração incremental:** Arquivos migrados gradualmente

## 🔄 Status de Implementação

### Fase 1: Fundação (EM PROGRESSO)

- [x] Estrutura de diretórios criada
- [ ] design_tokens.py implementado
- [ ] styles.qss criado
- [ ] widget_standards.py implementado
- [ ] helpers.py criado

### Fase 2: Temas (PENDENTE)

- [ ] theme_manager.py implementado
- [ ] Integração com main_window.py

### Fase 3: Migração (PENDENTE)

- [ ] 10 arquivos críticos migrados

### Fase 4: Documentação (PENDENTE)

- [ ] Guias de uso criados
- [ ] CLAUDE.md atualizado

## 📚 Documentação Adicional

- **Especificação:** `conductor/tracks/design_system_20260119/spec.md`
- **Plano:** `conductor/tracks/design_system_20260119/plan.md`
- **Análise:** `docs/reports/UI_STANDARDIZATION_ANALYSIS_2026-01-19.md`

## 💡 Dicas

### Para Desenvolvedores

1. **Sempre use tokens** em vez de valores hardcoded
2. **Use componentes base** sempre que possível
3. **Consulte este README** para exemplos de uso
4. **Leia guias detalhados** quando disponíveis

### Para Designers

1. **Alterar cor primária:** Modificar `ColorPalette.PRIMARY` em `design_tokens.py`
2. **Adicionar nova variante:** Criar em `widget_standards.py`
3. **Ajustar espaçamentos:** Modificar constantes em `Spacing`

## 🐛 Troubleshooting

### Stylesheet não carregou

- Verifique se `init_theme_manager(app)` foi chamado
- Verifique se `styles.qss` existe no diretório `ui/`
- Consulte logs do console para warnings

### Componentes não aparecem estilizados

- Verifique se `widget_standards.py` foi importado
- Verifique se propriedades (variant, heading, etc.) estão definidas
- Teste com stylesheet inline: `widget.setStyleSheet("...")`

### Tokens não funcionam

- Verifique se imports estão corretos: `from consumo_lib.ui import COLORS`
- Verifique se `__init__.py` tem exports
- Recarregue a aplicação após mudanças

---

**Versão:** 1.0.0
**Última Atualização:** 2026-01-19
**Status:** 🚧 Em Implementação (Fase 1)
