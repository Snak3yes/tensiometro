# Design System - Especificação

**Track ID:** design_system_20260119
**Tipo:** Feature
**Prioridade:** 🟡 MEDIUM-HIGH
**Data de Criação:** 2026-01-19
**Estimativa:** 4-6 semanas

---

## 📋 Resumo

Esta track estabelecerá o **Design System oficial** do projeto Tensiometro, criando uma padronização completa de interface que será usada em toda a aplicação. O sistema incluirá tokens de design, componentes base, gerenciador de temas e documentação abrangente.

### Problema Atual

O projeto Tensiometro possui inconsistências significativas na padronização de interface:

- **412 ocorrências** de estilos hardcoded em 39 arquivos
- **145 ocorrências** de cores hexadecimais hardcoded em 20 arquivos
- **40+ ocorrências** de tamanhos de fonte inconsistentes
- **80+ ocorrências** de dimensões hardcoded
- Nenhum sistema de design centralizado
- Mesma cor definida de 3 formas diferentes (#4CAF50, #2ecc71, #00ff00)

### Proposta de Solução

Criar um Design System completo inspirado no **Material Design 3** com:

1. **Design Tokens** - Constantes centralizadas (cores, fontes, espaçamentos)
2. **Qt Style Sheets** - Stylesheet global (.qss) para estilos consistentes
3. **Componentes Base** - Widgets padrão reutilizáveis
4. **Theme Manager** - Gerenciador de temas (light/dark/futuro)
5. **Documentação** - Guias de uso e exemplos

### Benefícios Esperados

- **Manutenibilidade:** Alterar cor = modificar 1 linha (ao invés de 15+ arquivos)
- **Consistência:** Interface uniforme em toda aplicação
- **Produtividade:** Autocomplete e padrões claros para desenvolvedores
- **Escalabilidade:** Facilita implementação de dark mode e temas customizados
- **Redução de código:** 30-40% de redução em código de styling

---

## 🎯 Objetivos

### Objetivo Principal

Estabelecer um Design System unificado que sirva como **única fonte de verdade** para todos os aspectos visuais da aplicação Tensiometro.

### Objetivos Específicos

1. **Criar Sistema de Design Tokens**
   - Paleta de cores completa (30+ constantes)
   - Sistema de tipografia (Material Design 3)
   - Espaçamentos (baseline grid de 4px)
   - Dimensões padronizadas (botões, inputs, dialogs)
   - Opacidades, transições, breakpoints

2. **Criar Stylesheet Global**
   - Arquivo .qss com estilos para todos componentes Qt
   - Estilos para botões, inputs, labels, dialogs, etc.
   - Estados interativos (hover, pressed, disabled)
   - Variants de componentes (primary, secondary, danger, outline)

3. **Criar Componentes Base**
   - StandardButton (com variantes)
   - StandardLabel (heading, subheading, body, caption)
   - StandardInput, StandardComboBox, StandardSpinBox
   - StandardGroupBox com espaçamento consistente

4. **Criar Gerenciador de Temas**
   - ThemeManager para aplicar estilos globais
   - Suporte para temas (light inicialmente, dark futuro)
   - Interface para acessar tokens de design

5. **Migrar Arquivos Críticos (Prova de Conceito)**
   - Migrar 10 arquivos mais críticos
   - Validar funcionamento do Design System
   - Documentar padrões de migração

6. **Documentar Design System**
   - Guia de uso dos tokens
   - Exemplos de componentes
   - Padrões de migração
   - Integração com main_window.py

---

## ✅ Critérios de Aceite

### Funcionais

- [ ] **Design Tokens Criados**
  - [ ] Arquivo `design_tokens.py` com todas as categorias (cores, fontes, espaçamentos, dimensões)
  - [ ] Constantes seguindo Material Design 3
  - [ ] Docstrings completas em todas as classes
  - [ ] Type hints em todos os métodos
  - [ ] Instâncias singleton exportadas (COLORS, TYPO, SPACE, DIM)

- [ ] **Stylesheet Global Criado**
  - [ ] Arquivo `styles.qss` com estilos para todos componentes Qt padrão
  - [ ] Estilos para QPushButton, QLabel, QLineEdit, QComboBox, etc.
  - [ ] Estados interativos (hover, pressed, disabled, focus)
  - [ ] Variants de componentes (primary, secondary, danger, outline)
  - [ ] Comentários explicativos por seção

- [ ] **Componentes Base Criados**
  - [ ] `StandardButton` com variantes (primary, secondary, danger, outline)
  - [ ] `StandardLabel` com variantes (heading, subheading, body, caption)
  - [ ] `StandardInput`, `StandardSpinBox`, `StandardDoubleSpinBox`
  - [ ] `StandardComboBox`, `StandardGroupBox`
  - [ ] Todos os componentes usando design tokens

- [ ] **Theme Manager Criado**
  - [ ] Classe `ThemeManager` para gerenciar temas
  - [ ] Método `init_theme_manager()` para inicialização
  - [ ] Função `get_theme_manager()` para acessar instância
  - [ ] Carregamento automático de styles.qss
  - [ ] Placeholder para dark mode (comentários TODO)

- [ ] **Helpers Criados**
  - [ ] Funções helper para layouts (spacers, separators)
  - [ ] Funções para aplicar espaçamento padrão
  - [ ] Utilitários para tarefas comuns de UI

- [ ] **Integração com Aplicação**
  - [ ] ThemeManager inicializado em `main_window.py`
  - [ ] Stylesheet global carregado no startup
  - [ ] Design tokens importáveis de qualquer módulo

- [ ] **Migração de Arquivos Críticos**
  - [ ] Top 5 widgets migrados (movement_control, operator_interface, hardware_status_bar, tension_viz, status_badge)
  - [ ] Top 3 dialogs migrados (login, inspection_results, defect_judgment)
  - [ ] Top 2 engineering widgets migrados (alignment_widget, fiducial_capture_widget)
  - [ ] Zero hardcoded values nos arquivos migrados
  - [ ] Testes visuais manuais passando

- [ ] **Documentação Completa**
  - [ ] README do Design System (`docs/design_system/README.md`)
  - [ ] Guia de uso dos tokens (`docs/design_system/TOKENS.md`)
  - [ ] Guia de componentes (`docs/design_system/COMPONENTS.md`)
  - [ ] Guia de migração (`docs/design_system/MIGRATION.md`)
  - [ ] Exemplos de código em cada guia
  - [ ] CLAUDE.md atualizado com seção de Design System

### Não-Funcionais

- [ ] **Performance**
  - [ ] Stylesheet carrega em <100ms
  - [ ] Overhead de renderização insignificante (<5%)
  - [ ] Tema alternado em <50ms

- [ ] **Manutenibilidade**
  - [ ] Alterar cor primária afeta 100% dos componentes
  - [ ] Adicionar novo componente base segue padrão estabelecido
  - [ ] Documentação atualizada simultaneamente ao código

- [ ] **Compatibilidade**
  - [ ] Zero breaking changes na API pública
  - [ ] Componentes legados continuam funcionando
  - [ ] Backward compatibility mantida (100%)

- [ ] **Qualidade de Código**
  - [ ] Type hints em 100% do código público
  - [ ] Docstrings Google style em todas classes públicas
  - [ ] Linter clean (pylint score >8.0)
  - [ ] Coverage >80% para código novo

- [ ] **Acessibilidade**
  - [ ] Contraste ratios WCAG 2.1 AA atendidos
  - [ ] Tamanhos de toque mínimos (44px)
  - [ ] Focus indicators visíveis (2px)

---

## 📐 Requisitos Funcionais

### RF-001: Design Tokens

**O sistema DEVE prover tokens centralizados para:**

1. **Cores (ColorPalette)**
   - Primary colors (verde para ações primárias)
   - Secondary colors (azul para informações)
   - Semantic colors (success, warning, error)
   - Status colors (approved_auto, approved_user, rejected, pending, in_progress)
   - Neutral colors (text, background, border)
   - Engineering-specific colors (overlay, fiducial, grid)

2. **Tipografia (Typography)**
   - Font family (Arial, Consolas para monospace)
   - Type scale (Material Design 3: display, headline, title, body, label)
   - Factory methods para criar QFont (get_font)
   - Métodos convenience (headline_medium, body_medium, etc.)

3. **Espaçamentos (Spacing)**
   - Baseline grid de 4px
   - Escala: XS=4, SM=8, MD=16, LG=24, XL=32, XXL=48
   - Paddings e margins contextuais

4. **Dimensões (Dimensions)**
   - Border radius (4, 8, 12, 16px)
   - Icon sizes (16, 24, 32, 48, 64px)
   - Button/input heights (32, 40, 48px)
   - Dialog sizes (small, medium, large, xlarge)
   - Thumbnail sizes

5. **Elevação (Elevation)**
   - Níveis 0-5 para sombras/layering

6. **Opacidades (Opacity)**
   - Valores padronizados (disabled=0.38, hover=0.08, etc.)

7. **Transições (Transitions)**
   - Durações (instant, fast=150ms, normal=250ms, slow=350ms)
   - Easing functions (cubic-bezier)

**Tokens DEVEM ser:**
- Acessíveis via instâncias singleton (COLORS, TYPO, SPACE, DIM)
- Type-hinted
- Documentados com docstrings
- Imutáveis (dataclasses)

### RF-002: Qt Style Sheet

**O stylesheet global DEVE conter estilos para:**

1. **Reset & Base**
   - Reset de outline
   - Font family e size padrão
   - Cores de background e texto

2. **Botões (QPushButton)**
   - Estilo base (primary)
   - Variantes (secondary, danger, outline)
   - Estados (hover, pressed, disabled, focus)
   - Tamanhos (SM, MD, LG)

3. **Text & Labels (QLabel)**
   - Base
   - Heading
   - Subheading
   - Caption

4. **Inputs (QLineEdit, QTextEdit, QPlainTextEdit)**
   - Base
   - Estados (focus, disabled)
   - Bordas e padding

5. **Combobox (QComboBox)**
   - Base e hover
   - Dropdown arrow
   - Lista dropdown

6. **SpinBox (QSpinBox, QDoubleSpinBox)**
   - Similar aos inputs

7. **Checkbox & Radio (QCheckBox, QRadioButton)**
   - Indicator personalizado
   - Estados checked/unchecked

8. **GroupBox (QGroupBox)**
   - Borda e título
   - Padding interno

9. **ProgressBar (QProgressBar)**
   - Background e chunk
   - Altura e border-radius

10. **TabWidget (QTabWidget)**
    - Pane e tabs
    - Estados (selected, hover)

11. **Table (QTableView, QTableWidget)**
    - Grid e cells
    - Header
    - Estados (selected, hover)

12. **Dialog (QDialog)**
    - Background padrão

13. **Menu (QMenu)**
    - Background e bordas
    - Items e separators
    - Estado selected

**Stylesheet DEVE:**
- Seguir Material Design 3
- Usar cores hexadecimais (compatíveis com Qt)
- Ter comentários por seção
- Ser carregado automaticamente no startup

### RF-003: Componentes Base

**Cada componente base DEVE:**

1. **StandardButton**
   - Aceitar parâmetros: text, variant (primary|secondary|danger|outline)
   - Aplicar fonte automaticamente (BODY_LARGE, bold)
   - Aplicar tamanho mínimo (BUTTON_HEIGHT_MD)
   - Usar property "variant" para stylesheet

2. **StandardLabel**
   - Aceitar parâmetros: text, variant (heading|subheading|body|caption)
   - Selecionar fonte automaticamente baseado na variante
   - Usar property para stylesheet (heading, subheading, caption)

3. **StandardInput/SpinBox/ComboBox**
   - Aplicar altura mínima (INPUT_HEIGHT_MD)
   - Aceitar placeholder (inputs)

4. **StandardGroupBox**
   - Aplicar espaçamento interno (layoutSpacing)

**Componentes DEVEM:**
- Herdar de classes Qt correspondentes
- Usar design tokens internamente
- Ser fáceis de usar (1-2 linhas de código)
- Ter docstrings completas

### RF-004: Theme Manager

**ThemeManager DEVE:**

1. **Inicialização**
   - Receber QApplication no construtor
   - Carregar stylesheet de styles.qss
   - Aplicar stylesheet globalmente
   - Log status (sucesso/erro)

2. **Gerenciamento de Temas**
   - Método `set_theme(theme_name)` para alternar temas
   - Tema padrão: "light"
   - Placeholder para "dark" e "high_contrast"

3. **Acesso a Tokens**
   - Propriedade `colors` retornando ColorPalette
   - Propriedade `typo` retornando Typography

4. **Instância Global**
   - Singleton pattern
   - Função `init_theme_manager(app)` para criar instância
   - Função `get_theme_manager()` para acessar instância

### RF-005: Funções Helper

**Helpers DEVEM incluir:**

1. **Layout Helpers**
   - `create_h_spacer()` - Espaço horizontal expansível
   - `create_v_spacer()` - Espaço vertical expansível
   - `add_spacing(layout, space)` - Adiciona espaçamento ao layout

2. **Separadores Visuais**
   - `create_separator(orientation)` - Linha separadora

3. **Espaçamento Padrão**
   - `apply_standard_spacing(layout)` - Aplica spacing e margins

### RF-006: Integração com Aplicação

**main_window.py DEVE:**

1. **Inicializar ThemeManager**
   - Chamar `init_theme_manager(app)` no startup
   - Verificar sucesso da inicialização

2. **Carregar Stylesheet**
   - Stylesheet aplicado automaticamente pelo ThemeManager
   - Fallback para estilos padrão do Qt se falhar

### RF-007: Migração de Arquivos

**Arquivos a migrar DEVEM:**

1. **Remover Hardcoded Colors**
   - Substituir cores hexadecimais por `COLORS.*`
   - Substituir `QColor("#...")` por tokens
   - Substituir estilos inline com cores por tokens

2. **Remover Hardcoded Fonts**
   - Substituir `QFont() + setPointSize()` por `TYPO.get_font()`
   - Substituir font-size em CSS por tokens

3. **Remover Hardcoded Sizes**
   - Substituir `setFixedSize(w, h)` por `DIM.*`
   - Substituir `setMinimumSize(w, h)` por constantes

4. **Usar Componentes Base**
   - Substituir `QPushButton` por `StandardButton`
   - Substituir `QLabel` por `StandardLabel`
   - Substituir inputs por classes Standard*

**Padrão de migração:**
```python
# ANTES
from PyQt6.QtWidgets import QPushButton
from PyQt6.QtGui import QFont

btn = QPushButton("Salvar")
font = QFont()
font.setPointSize(14)
font.setBold(True)
btn.setFont(font)

# DEPOIS
from consumo_lib.ui.widget_standards import StandardButton

btn = StandardButton("Salvar", variant="primary")
```

### RF-008: Documentação

**Documentação DEVE incluir:**

1. **README do Design System**
   - Visão geral
   - Benefícios
   - Como usar
   - Arquitetura

2. **Guia de Tokens**
   - Lista completa de tokens
   - Quando usar cada token
   - Exemplos de código
   - Boas práticas

3. **Guia de Componentes**
   - Cada componente base documentado
   - Parâmetros e variantes
   - Exemplos de uso
   - Screenshots (opcional)

4. **Guia de Migração**
   - Passo a passo de migração
   - Before/After examples
   - Checklist de validação
   - Troubleshooting

5. **CLAUDE.md Atualizado**
   - Seção "Design System" adicionada
   - Como importar tokens
   - Como usar componentes base
   - Exemplos rápidos

---

## 📐 Requisitos Não-Funcionais

### RNF-001: Performance

- Stylesheet deve carregar em <100ms
- Overhead de renderização <5%
- Troca de tema <50ms
- Memory overhead <10MB

### RNF-002: Manutenibilidade

- Alterar cor primária deve afetar 100% dos componentes automaticamente
- Adicionar novo token deve seguir padrão estabelecido
- Documentação deve ser atualizada simultaneamente ao código
- Code review deve validar uso de tokens (sem hardcoded values)

### RNF-003: Compatibilidade

- Zero breaking changes na API pública existente
- Componentes legados continuam funcionando sem modificação
- Novo código deve usar Design System
- Migração é opcional para código legado (gradual)

### RNF-004: Qualidade de Código

- Type hints em 100% do código público
- Docstrings Google style em todas classes públicas
- Pylint score >8.0
- Coverage >80% para código novo
- Zero linter warnings

### RNF-005: Acessibilidade

- Contraste ratios WCAG 2.1 AA (4.5:1 para texto normal, 3:1 para texto grande)
- Tamanhos de toque mínimos 44×44px (WCAG 2.5.5)
- Focus indicators visíveis (2px, offset 2px)
- Texto escalável (respeita configurações do sistema)

### RNF-006: Internacionalização

- Tokens são invariantes (não dependem de idioma)
- Textos de UI continuam usando sistema de tradução existente
- Cores e fontes são universais

---

## 🎨 Casos de Uso

### UC-001: Desenvolvedor Criando Novo Widget

**Ator Principal:** Desenvolvedor
**Pré-condições:** Design System implementado
**Fluxo Principal:**

1. Desenvolvedor cria novo widget
2. Importa componentes base: `from consumo_lib.ui.widget_standards import StandardButton, StandardLabel`
3. Importa tokens: `from consumo_lib.ui.design_tokens import COLORS, TYPO, SPACE`
4. Usa componentes base em vez de classes Qt raw
5. Usa tokens para customizações específicas
6. Widget tem aparência consistente automaticamente

**Pós-condições:** Widget segue Design System automaticamente

### UC-002: Desenvolvedor Migra Widget Legado

**Ator Principal:** Desenvolvedor
**Pré-condições:** Widget legado com hardcoded values
**Fluxo Principal:**

1. Desenvolvedor lê Guia de Migração
2. Identifica hardcoded colors/fonts/sizes
3. Substitui por tokens/design system components
4. Testa visualmente
5. Commit com mensagem padrão
6. Valida com checklist

**Pós-condições:** Widget migrado sem breaking changes

### UC-003: Designer Altera Cor Primária

**Ator Principal:** Designer/Desenvolvedor
**Pré-condições:** Design System implementado
**Fluxo Principal:**

1. Designer solicita mudança de cor primária
2. Desenvolvedor altera `ColorPalette.PRIMARY` em design_tokens.py
3. Alteração reflete automaticamente em toda aplicação
4. Teste visual para validar

**Pós-condições:** Nova cor aplicada em 100% dos componentes

### UC-004: Alternar Tema (Futuro)

**Ator Principal:** Usuário
**Pré-condições:** Dark mode implementado
**Fluxo Principal:**

1. Usuário abre configurações
2. Seleciona tema "Dark"
3. Sistema chama `theme_manager.set_theme("dark")`
4. Todos componentes atualizados automaticamente

**Pós-condições:** Interface completamente em dark mode

---

## 🚫 Restrições e Limitações

### Restrições Técnicas

1. **Qt 6 Limitations**
   - Stylesheet não suporta todas as funcionalidades CSS3
   - Variáveis CSS não são suportadas (usar Qt properties)
   - Pseudo-elementos limitados

2. **PyQt6 Constraints**
   - Estilos devem usar sintaxe específica do Qt
   - Cores devem ser hexadecimais ou nomes Qt
   - Algumas propriedades CSS não funcionam

### Limitações Conhecidas

1. **Dark Mode**
   - Não será implementado nesta track (placeholder apenas)
   - Requer trabalho adicional de design

2. **Migração Completa**
   - Apenas 10 arquivos serão migrados nesta track
   - 29 arquivos restantes serão migrados gradualmente

3. **Componentes Customizados**
   - Alguns widgets muito específicos podem não usar componentes base
   - Devem usar tokens mesmo assim

### Exclusões (Out of Scope)

- Dark mode completo (apenas placeholder)
- Temas customizados além de light/dark
- Animações complexas
- Web components (aplicação é desktop)
- Testes E2E de UI (apenas validação manual)

---

## 📊 Dependências

### Dependências Internas

- `consumo_lib/main_window.py` - Integração de ThemeManager
- `consumo_lib/widgets/*` - Migração de widgets
- `consumo_lib/dialogs/*` - Migração de dialogs
- `aoi_lib/config_manager.py` - Configurações existentes

### Dependências Externas

- **PyQt6** (^6.0) - Framework UI
- **Python** (^3.10) - Linguagem

### Tracks Pré-requisitos

- Nenhum (pode ser feito independentemente)

### Tracks Dependentes

- `ui_standardization_migration_202601XX` - Track futura para migração completa

---

## 📅 Cronograma Estimado

- **Fase 1: Fundação** (Semanas 1-2) - Criar design_tokens.py, styles.qss, widget_standards.py
- **Fase 2: Temas e Integração** (Semana 3) - Criar ThemeManager, integrar com main_window.py
- **Fase 3: Migração Parcial** (Semanas 4-5) - Migrar 10 arquivos críticos
- **Fase 4: Documentação e Validação** (Semana 6) - Documentar, testar, finalizar

**Total:** 4-6 semanas

---

## 🎯 Sucesso da Track

A track será considerada um sucesso quando:

1. ✅ Design System está implementado e documentado
2. ✅ 10 arquivos críticos foram migrados sem breaking changes
3. ✅ Desenvolvedores conseguem usar Design System em <5 minutos
4. ✅ Alterar cor primária afeta 100% dos componentes migrados
5. ✅ Documentação está completa e exemplos funcionam
6. ✅ CLAUDE.md atualizado com seção de Design System
7. ✅ Zero regressões visuais na aplicação
8. ✅ Código segue padrões SOLID (score >90/100)

---

**Especificação v1.0 - 2026-01-19**
