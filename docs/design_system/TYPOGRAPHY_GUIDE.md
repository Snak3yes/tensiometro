# Guia de Tipografia - Tensiometro (Material Design 3)

**Versão:** 2.0
**Data:** 2026-01-20
**Status:** ✅ Approved (Material Design 3)
**Previous Version:** 1.0 (Semântico - Deprecated)

## Visão Geral

Este guia define a padronização de tipografia para o sistema **Tensiometro** baseado no **Material Design 3** do Google, garantindo consistência visual, legibilidade otimizada e escalabilidade para futuras necessidades.

### Princípios de Design

1. **Padrão de Mercado**: Material Design 3 (Google) - amplamente adotado e testado
2. **Escalabilidade**: 13 níveis de tipografia para flexibilidade máxima
3. **Legibilidade**: Alto contraste, fontes claras, espaçamento adequado
4. **Consistência**: Nomes padronizados reconhecidos globalmente
5. **Ênfase Moderada**: Pesos de fonte usados com critério (5 níveis)

---

## Por Que Material Design 3?

### Decisão Arquitetural

**Escolha:** Manter nomenclatura **Material Design 3 (MD3)** para tipografia.

**Justificativa:**
1. **Padrão de Mercado**: Google Material Design 3 é usado globalmente
2. **Escalabilidade**: 13 níveis (DISPLAY_LARGE a LABEL_SMALL) vs 6 níveis semânticos
3. **Implementação Existente**: Código já usa MD3 (zero breaking changes)
4. **Documentação Oficial**: Google mantém guias detalhadas e atualizadas
5. **Ferramentas**: Plugins e extensões disponíveis para VS Code, Figma, etc.
6. **Futuro-Proof**: Google continua investindo no MD3
7. **Time-to-Value**: 1 dia para atualizar guias vs 3-5 dias para refatoração

**Mais Informações:**
- Ver `conductor/tracks/design_system_alignment_20260120/DECISION_LOG.md` para análise completa
- Material Design 3 Typography: https://m3.material.io/styles/typography

---

## Sistema de Fontes

### Fonte Principal

```
Font Family: 'Segoe UI', Arial, sans-serif
```

**Justificativa:**
- **Segoe UI**: Fonte moderna do Windows, excelente legibilidade em telas
- **Arial**: Fallback universal, disponível em todos os sistemas
- **Sans-serif**: Limpa, profissional, adequada para interfaces

### Fonte Monoespaçada

```
Font Family: 'Consolas', 'Courier New', monospace
```

**Uso:** Código técnico, valores numéricos, logs de sistema

---

## Escala de Tipografia (Material Design 3)

### Display Styles (Hero/Marketing)

**Uso:** Títulos hero muito grandes, marketing, splash screens

| Estilo | Tamanho | Uso | Font Weight | Exemplo |
|--------|---------|-----|-------------|---------|
| **DISPLAY_LARGE** | 57px | Hero title (raro) | 400 (normal) | Tela inicial |
| **DISPLAY_MEDIUM** | 45px | Subtítulo hero | 400 (normal) | Seção principal |
| **DISPLAY_SMALL** | 36px | Subtítulo grande | 400 (normal) | Destaque importante |

```python
# Uso de Display Styles
from consumo_lib.ui.design_tokens import TYPO

title_hero = QLabel("Tensiometro AOI")
title_hero.setFont(TYPO.display_large())
# Result: 57px, normal
```

**Frequência de Uso:** 5% (apenas em contextos especiais)

---

### Headline Styles

**Uso:** Títulos principais de dialogs e janelas

| Estilo | Tamanho | Uso | Font Weight | Exemplo |
|--------|---------|-----|-------------|---------|
| **HEADLINE_LARGE** | 32px | Título de dialog grande | 400 (normal) | "Configurações Avançadas" |
| **HEADLINE_MEDIUM** | 28px | Título de dialog padrão | 400 (normal) | "Configurar Câmera" |
| **HEADLINE_SMALL** | 24px | Título de seção | 400 (normal) | "Parâmetros" |

```python
# Uso de Headline Styles
from consumo_lib.ui.design_tokens import TYPO

title_dialog = QLabel("Configurações de Câmera")
title_dialog.setFont(TYPO.headline_medium())
# Result: 28px, normal
```

**Frequência de Uso:** 10% (títulos de dialogs)

---

### Title Styles

**Uso:** Títulos de widgets, blocos, cards

| Estilo | Tamanho | Uso | Font Weight | Exemplo |
|--------|---------|-----|-------------|---------|
| **TITLE_LARGE** | 22px | Título de bloco grande | 400 (normal) | "Status do Sistema" |
| **TITLE_MEDIUM** | 16px | Título de widget | 500 (medium) | "Câmera 1" |
| **TITLE_SMALL** | 14px | Subtítulo | 500 (medium) | "Resolução" |

```python
# Uso de Title Styles
from consumo_lib.ui.design_tokens import TYPO

title_widget = QLabel("Câmera 1")
title_widget.setFont(TYPO.title_medium())
# Result: 16px, medium (500)
```

**Frequência de Uso:** 20% (títulos de componentes)

---

### Body Styles (MAIS USADO)

**Uso:** Texto corrido, labels, botões, conteúdo geral

| Estilo | Tamanho | Uso | Font Weight | Exemplo |
|--------|---------|-----|-------------|---------|
| **BODY_LARGE** | 16px | Botões, labels importantes | 400 (normal) | Botão "Salvar" |
| **BODY_MEDIUM** | 14px | Texto padrão (DEFAULT) | 400 (normal) | "Conectado ao PLC" |
| **BODY_SMALL** | 12px | Texto secundário | 400 (normal) | "Use scroll para zoom" |

```python
# Uso de Body Styles (MAIS COMUM)
from consumo_lib.ui.design_tokens import TYPO

# Texto padrão (70% dos casos)
label_info = QLabel("Câmera conectada")
label_info.setFont(TYPO.body_medium())
# Result: 14px, normal (400)

# Botão (20% dos casos)
from consumo_lib.ui.widget_standards import StandardButton
btn = StandardButton("Salvar")
# Usa BODY_LARGE (16px) automaticamente
```

**Frequência de Uso:** 60% (maioria do texto)

---

### Label Styles

**Uso:** Labels de formulário, captions, badges, texto pequeno

| Estilo | Tamanho | Uso | Font Weight | Exemplo |
|--------|---------|-----|-------------|---------|
| **LABEL_LARGE** | 14px | Labels importantes | 400 (normal) | "Endereço IP:" |
| **LABEL_MEDIUM** | 12px | Labels padrão | 400 (normal) | "Porta:" |
| **LABEL_SMALL** | 11px | Captions, badges | 400 (normal) | "192.168.1.5" |

```python
# Uso de Label Styles
from consumo_lib.ui.design_tokens import TYPO

label_form = QLabel("Endereço IP:")
label_form.setFont(TYPO.label_large())
# Result: 14px, normal (400)

label_meta = QLabel("192.168.1.5")
label_meta.setFont(TYPO.label_small())
# Result: 11px, normal (400)
```

**Frequência de Uso:** 5% (labels e captions)

---

## Mapeamento: Uso → Estilo MD3

### Guia Rápido: Qual Estilo Usar?

**Para Títulos:**
- Dialog grande → `HEADLINE_LARGE` (32px)
- Dialog padrão → `HEADLINE_MEDIUM` (28px)
- Seção → `HEADLINE_SMALL` (24px)
- Widget → `TITLE_MEDIUM` (16px)
- Subtítulo → `TITLE_SMALL` (14px)

**Para Texto Corrido:**
- Botão → `BODY_LARGE` (16px, aplicado via StandardButton)
- Texto padrão → `BODY_MEDIUM` (14px) ← **USE ESTE 70% das vezes**
- Texto secundário → `BODY_SMALL` (12px)

**Para Labels:**
- Label importante → `LABEL_LARGE` (14px)
- Label padrão → `LABEL_MEDIUM` (12px)
- Caption/metadata → `LABEL_SMALL` (11px)

**Para Hero (Raro):**
- Splash screen → `DISPLAY_LARGE` (57px)
- Destaque principal → `DISPLAY_MEDIUM` (45px)
- Subtítulo hero → `DISPLAY_SMALL` (36px)

---

## Pesos de Fonte (Font Weight)

### Tabela de Uso

| Weight | Valor | Uso | Frequência |
|--------|-------|-----|------------|
| **Light** | 300 | Raramente usado | 5% |
| **Normal** | 400 | Texto padrão, labels, instruções | 70% |
| **Medium** | 500 | Títulos de seção, botões, headings | 20% |
| **Semibold** | 600 | Títulos principais, dialogs | 4% |
| **Bold** | 700 | Apenas emergências, alertas críticos | 1% |

### Como Usar

```python
from consumo_lib.ui.design_tokens import TYPO, FontWeight

# Método novo (RECOMENDADO)
font = TYPO.get_font(14, weight=FontWeight.MEDIUM)

# Methods convenientes
TYPO.normal(10)   # 400 - texto padrão (70%)
TYPO.medium(11)   # 500 - títulos, botões (20%)
TYPO.semibold(14) # 600 - títulos principais (4%)
TYPO.bold(14)     # 700 - emergências apenas (1%)
```

### Regras de Uso

✅ **USE NORMAL (400) - 70% dos casos:**
- Texto corrido
- Labels descritivos
- Instruções
- Mensagens informativas
- Conteúdo de tabelas

✅ **USE MEDIUM (500) - 20% dos casos:**
- Títulos de seção/grupo
- Texto de botões
- Labels de formulário
- Cabeçalhos de coluna

✅ **USE SEMIBOLD (600) - 4% dos casos:**
- Título de dialogs
- Título de janelas
- Headings principais
- Alertas importantes

❌ **NÃO USE BOLD (700) EXCETO - 1% dos casos:**
- Botões de EMERGENCY STOP
- Alertas críticos de segurança
- Avisos de perigo iminente

---

## Hierarquia Visual

### Nível 1: Título Principal (HEADLINE_MEDIUM/28px)

```
┌─────────────────────────────────────────┐
│  Configurações Avançadas - Câmera 1     │  ← HEADLINE_MEDIUM
├─────────────────────────────────────────┤
│                                          │
│  Conectado • 192.168.1.5 • 25 FPS       │  ← LABEL_SMALL
│                                          │
```

### Nível 2: Título de Seção (HEADLINE_SMALL/24px)

```
┌─────────────────────────────────────────┐
│  Parâmetros de Inspeção                 │  ← HEADLINE_SMALL
├─────────────────────────────────────────┤
│  Threshold:  [██████░░░]  50%          │  ← BODY_MEDIUM
│  Sensibilidade: [████████]  80%        │
└─────────────────────────────────────────┘
```

### Nível 3: Texto Padrão (BODY_MEDIUM/14px)

```python
# Texto descritivo, labels de formulário
label = QLabel("Pressione para capturar imagem")
label.setFont(TYPO.body_medium())
# Result: 14px, normal (400)
```

### Nível 4: Texto Auxiliar (BODY_SMALL/12px)

```python
# Instruções, hints
label_hint = QLabel("Use Ctrl+Clique para múltipla seleção")
label_hint.setFont(TYPO.body_small())
# Result: 12px, normal (400)
```

### Nível 5: Metadados (LABEL_SMALL/11px)

```python
# Informações técnicas, timestamps
label_meta = QLabel("ID: PLC-001 | 192.168.1.5:502")
label_meta.setFont(TYPO.label_small())
# Result: 11px, normal (400)
```

---

## Exemplos Práticos

### Labels e Texto Informativo

```python
from consumo_lib.ui.design_tokens import TYPO

# Label pequeno (instruções, dicas)
label_hint = QLabel("Use scroll para zoom")
label_hint.setFont(TYPO.body_small())  # 12px
label_hint.setStyleSheet("color: #757575;")

# Label normal (texto padrão) - MAIS COMUM
label_info = QLabel("Câmera conectada")
label_info.setFont(TYPO.body_medium())  # 14px

# Label de formulário
label_form = QLabel("Endereço IP:")
label_form.setFont(TYPO.label_large())  # 14px
```

### Títulos e Headings

```python
from consumo_lib.ui.design_tokens import TYPO

# Título de dialog (MAIS COMUM para títulos)
title_dialog = QLabel("Configurações de Câmera")
title_dialog.setFont(TYPO.headline_medium())  # 28px

# Título de seção
title_section = QLabel("Parâmetros de Inspeção")
title_section.setFont(TYPO.headline_small())  # 24px
title_section.setStyleSheet("color: #2196F3;")

# Título de widget
title_widget = QLabel("Câmera 1")
title_widget.setFont(TYPO.title_medium())  # 16px
title_widget.setStyleSheet("font-weight: 500;")
```

### Botões

```python
# Botão padrão (StandardButton aplica BODY_LARGE automaticamente)
from consumo_lib.ui.widget_standards import StandardButton

btn = StandardButton("Iniciar Ciclo", variant="primary-green")
# Usa: 16px, medium (500)

# Botão de emergência (MAIOR TAMANHO)
btn_emergency = StandardButton("EMERGENCY STOP", variant="emergency")
# Usa: Tamanho extra-large + bold (700)
```

### Tabelas

```python
from consumo_lib.ui.design_tokens import TYPO

# Cabeçalho da tabela
header_font = TYPO.title_medium()  # 16px, medium (500)
table.horizontalHeader().setFont(header_font)

# Conteúdo da tabela
content_font = TYPO.body_medium()  # 14px, normal (400)
table.setFont(content_font)
```

### Status e Mensagens

```python
# Mensagem de sucesso
msg_success = QLabel("✓ Conectado com sucesso")
msg_success.setFont(TYPO.title_medium())  # 16px, medium
msg_success.setStyleSheet("color: #388E3C;")

# Mensagem de erro
msg_error = QLabel("✗ Falha na conexão")
msg_error.setFont(TYPO.title_medium())  # 16px, medium
msg_error.setStyleSheet("color: #D32F2F;")

# Mensagem informativa
msg_info = QLabel("Aguarde enquanto o sistema carrega...")
msg_info.setFont(TYPO.body_medium())  # 14px, normal
msg_info.setStyleSheet("color: #757575;")
```

---

## Cores de Texto por Contexto

### Light Theme

| Contexto | Cor | Uso |
|----------|-----|-----|
| Texto principal | `#212121` (TEXT_PRIMARY) | Conteúdo, títulos, labels |
| Texto secundário | `#757575` (TEXT_SECONDARY) | Instruções, hints |
| Texto desabilitado | `#BDBDBD` (TEXT_DISABLED) | Labels inativos |
| Links/ativos | `#2196F3` (PRIMARY) | Abas ativas, links |
| Erro | `#D32F2F` (ERROR) | Mensagens de erro |
| Sucesso | `#388E3C` (SUCCESS) | Mensagens de sucesso |
| Aviso | `#F57C00` (WARNING) | Warnings |

### Dark Theme

| Contexto | Cor | Uso |
|----------|-----|-----|
| Texto principal | `#FFFFFF` (TEXT_PRIMARY) | Conteúdo, títulos, labels |
| Texto secundário | `#B0BEC5` (TEXT_SECONDARY) | Instruções, hints |
| Texto desabilitado | `#757575` (TEXT_DISABLED) | Labels inativos |
| Links/ativos | `#64B5F6` (PRIMARY_LIGHT) | Abas ativas, links |
| Erro | `#EF5350` (ERROR_LIGHT) | Mensagens de erro |
| Sucesso | `#66BB6A` (SUCCESS_LIGHT) | Mensagens de sucesso |
| Aviso | `#FFA726` (WARNING_LIGHT) | Warnings |

---

## Espaçamento e Line Height

### Line Height (Altura de Linha)

```
Tamanho da Fonte    Line Height    Uso
57px (DISPLAY_L)    1.2 (68.4px)   Hero title
45px (DISPLAY_M)    1.2 (54px)     Subtítulo hero
36px (DISPLAY_S)    1.3 (46.8px)   Subtítulo grande
32px (HEADLINE_L)   1.3 (41.6px)   Título muito grande
28px (HEADLINE_M)   1.3 (36.4px)   Título de dialog
24px (HEADLINE_S)   1.3 (31.2px)   Título de seção
22px (TITLE_L)      1.4 (30.8px)   Título de bloco
16px (TITLE_M/BODY_L) 1.5 (24px)   Título widget / Botão
14px (TITLE_S/BODY_M) 1.5 (21px)   Subtítulo / Texto padrão
12px (TITLE_L/BODY_S) 1.5 (18px)   Label / Texto secundário
11px (LABEL_M)     1.5 (16.5px)   Label padrão
```

### Letter Spacing (Espaçamento entre letras)

```python
# Normal (padrão)
letter-spacing: 0px

# Títulos (opcional, para maiúsculas)
letter-spacing: 0.5px  # Apenas para títulos em ALL-CAPS
```

---

## Casos de Uso Específicos

### 1. Dialog Típico

```
┌──────────────────────────────────────────────┐
│  Configurações Avançadas - Câmera 1    [X]  │  ← HEADLINE_MEDIUM/28px
├──────────────────────────────────────────────┤
│                                              │
│  Conectado • 192.168.1.5 • 25 FPS           │  ← LABEL_SMALL/11px
│                                              │
│  Parâmetros de Imagem                        │  ← HEADLINE_SMALL/24px
│  ─────────────────────────────               │
│                                              │
│  Resolução:        [1920x1080 ▼]             │  ← BODY_MEDIUM/14px
│  Exposição:         [████████░░]  80%        │
│  Ganho:            [━━━━●━━━]  50%           │
│                                              │
│  Dica: Use arraste para ajustar a ROI        │  ← BODY_SMALL/12px
│                                              │
│           [Cancelar]  [Aplicar]              │  ← BODY_LARGE/16px
└──────────────────────────────────────────────┘
```

### 2. Aba com Títulos

```
┌──────────────────────────────────────────────┐
│ Inspeção │ Câmeras │ Projeto │ Cadastros │ HW │
│══════════════════                                            │
│                                                             │
│  Status de Inspeção                            │  ← HEADLINE_SMALL/24px
│  ────────────────────                          │
│                                                             │
│  Ciclo:        Em andamento                    │  ← BODY_MEDIUM/14px
│  Posição:      X:150 Y:200 Z:50                │
│  Resultado:    Aguardando...                    │
│                                                             │
│  info: O ciclo pode levar até 30 segundos    │  ← BODY_SMALL/12px
└─────────────────────────────────────────────────────────────┘
```

---

## Padrões de Código

### Padrão 1: Import Design Tokens

```python
# Importar instâncias globais
from consumo_lib.ui.design_tokens import TYPO, COLORS, SPACE, DIM

# OU importar classes específicas
from consumo_lib.ui.design_tokens import Typography, FontWeight
```

### Padrão 2: Criar Font com get_font()

```python
# Novo método (RECOMENDADO)
from consumo_lib.ui.design_tokens import TYPO, FontWeight

font = TYPO.get_font(14, weight=FontWeight.MEDIUM)
label.setFont(font)
```

### Padrão 3: Usar Methods Convenientes

```python
from consumo_lib.ui.design_tokens import TYPO

# Texto padrão (70% dos casos)
font = TYPO.body_medium()  # 14px, normal
label.setFont(font)

# Título de seção (20% dos casos)
font = TYPO.title_medium()  # 16px, medium
label.setFont(font)

# Título de dialog (4% dos casos)
font = TYPO.headline_medium()  # 28px, normal
label.setFont(font)
```

### Padrão 4: StandardButton (Aplica Font Automaticamente)

```python
from consumo_lib.ui.widget_standards import StandardButton

# Font aplicada automaticamente
btn = StandardButton("Salvar", variant="primary-green")
# Usa: BODY_LARGE (16px), MEDIUM (500)
```

---

## Migration Guide (v1.0 → v2.0)

### Mudanças

**Antes (v1.0 - Semântico):**
- Nomes: TINY, SMALL, NORMAL, MEDIUM, LARGE, XLARGE
- Valores: 8px a 14px
- 6 níveis apenas

**Depois (v2.0 - Material Design 3):**
- Nomes: DISPLAY_*, HEADLINE_*, TITLE_*, BODY_*, LABEL_*
- Valores: 11px a 57px
- 13 níveis (mais escalável)

### Mapeamento

| v1.0 (Semântico) | v2.0 (MD3) | Uso |
|------------------|-------------|-----|
| TINY (8px) | LABEL_SMALL (11px) | Metadados |
| SMALL (9px) | BODY_SMALL (12px) | Instruções |
| NORMAL (10px) | BODY_MEDIUM (14px) | Texto padrão |
| MEDIUM (11px) | TITLE_MEDIUM (16px) | Títulos |
| LARGE (12px) | HEADLINE_SMALL (24px) | Títulos grandes |
| XLARGE (14px) | HEADLINE_MEDIUM (28px) | Título de dialog |

**Note:** Valores são ligeiramente maiores em MD3 (melhor legibilidade).

---

## Checklist de Uso

Antes de aplicar um estilo de texto, pergunte:

1. ✅ **Este é o tamanho correto?**
   - Dialog grande → HEADLINE_LARGE (32px)
   - Dialog padrão → HEADLINE_MEDIUM (28px)
   - Seção → HEADLINE_SMALL (24px)
   - Widget → TITLE_MEDIUM (16px)
   - Texto padrão → BODY_MEDIUM (14px) ← **MAIS COMUM**
   - Caption → BODY_SMALL (12px)
   - Metadata → LABEL_SMALL (11px)

2. ✅ **Este é o peso correto?**
   - Texto corrido → Normal (400) ← 70% dos casos
   - Título de seção → Medium (500) ← 20% dos casos
   - Título principal → Semibold (600) ← 4% dos casos
   - Emergência → Bold (700) ← 1% dos casos

3. ✅ **A cor está correta?**
   - Texto principal → TEXT_PRIMARY
   - Texto secundário → TEXT_SECONDARY
   - Links/ativos → PRIMARY
   - Erro → ERROR
   - Sucesso → SUCCESS
   - Aviso → WARNING

4. ✅ **O espaçamento está adequado?**
   - Line height = 1.3-1.5x para texto
   - Letter spacing = 0px (padrão)
   - Margens/padding consistentes (use SPACE.MD, etc.)

---

## Referências

- Material Design 3 Typography: https://m3.material.io/styles/typography
- Atlassian Design Guidelines: https://atlassian.design/guidelines/product/typography
- Apple Human Interface Guidelines: Typography
- DECISION_LOG.md: Decisão arquitetural (MD3 vs Semântico)

---

## Changelog

### v2.0 (2026-01-20)
- ✅ **BREAKING CHANGE**: Nomenclatura alterada de Semântico para Material Design 3
- ✅ Escala expandida de 6 para 13 níveis
- ✅ Adicionada seção "Por Que Material Design 3?"
- ✅ Atualizados todos os exemplos de código
- ✅ Adicionado guia de migração (v1.0 → v2.0)
- ✅ Adicionado mapeamento Semântico → MD3

### v1.0 (2026-01-20)
- Versão inicial com nomenclatura semântica
- 6 níveis de tipografia
- Guias de uso por componente

---

**Documento mantido pelo Design System Team**
**Última atualização:** 2026-01-20
**Próxima revisão:** 2026-02-20 (se necessário)
