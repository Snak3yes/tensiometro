# Guia de Migração - Design System

Guia prático para migrar código legado para o Tensiometro Design System.

## 📋 Índice

- [Por que Migrar](#por-que-migrar)
- [Quando Migrar](#quando-migrar)
- [Identificando Código Legado](#identificando-código-legado)
- [Padrões de Refatoração](#padrões-de-refatoração)
- [Exemplos Reais](#exemplos-reais)
- [Erros Comuns](#erros-comuns)
- [Checklist de Validação](#checklist-de-validação)
- [Arquivos Migrados](#arquivos-migrados)

---

## Por que Migrar

**Benefícios da migração**:

✅ **Manutenibilidade**: Cores e tamanhos centralizados
✅ **Consistência**: Interface uniforme em toda a aplicação
✅ **Type Safety**: Tokens são constantes, não strings mágicas
✅ **Fácil Refatoração**: Alterar cor primária afeta toda a aplicação
✅ **Professionalism**: Visual polido seguindo Material Design 3

**Custo da não migração**:

❌ Código duplicado em toda a aplicação
❌ Inconsistências visuais (tons de verde diferentes, etc)
❌ Difícil manutenção (mudar cor requer alterar múltiplos arquivos)
❌ Valores hardcoded sem documentação

---

## Quando Migrar

### Código Novo

**Sempre** use Design System para código novo. Não há exceções.

### Código Legado

Migre gradualmente durante refatorações ou quando:

1. **Bug Fix**: Ao corrigir um bug no widget
2. **Feature Add**: Ao adicionar nova funcionalidade
3. **Code Review**: Quando revisando código com muitos valores hardcoded
4. **Cleanup**: Quando fazendo limpeza técnica

**Regra prática**: Se você está editando um arquivo com valores hardcoded (cores, fontes, espaçamentos), migre para Design System durante a edição.

---

## Identificando Código Legado

### Sinais de Código Legado

**1. Cores Hardcoded**

```python
# ❌ CÓDIGO LEGADO
setStyleSheet(f"background-color: #4CAF50;")
setStyleSheet(f"color: white;")
setStyleSheet(f"border: 1px solid #E0E0E0;")
```

**2. QFont Manual**

```python
# ❌ CÓDIGO LEGADO
font = QFont()
font.setPointSize(14)
font.setBold(True)
label.setFont(font)
```

**3. Tamanhos Hardcoded**

```python
# ❌ CÓDIGO LEGADO
btn.setMinimumHeight(40)
setContentsMargins(16, 16, 16, 16)
setSpacing(8)
```

**4. Estilos Repetitivos**

```python
# ❌ CÓDIGO LEGADO
btn.setStyleSheet("""
    QPushButton {
        background-color: #4CAF50;
        color: white;
        border-radius: 8px;
        padding: 8px 24px;
    }
""")
```

### Busca Global

Use grep para encontrar código legado:

```bash
# Encontrar cores hex hardcoded
grep -r "#[0-9A-Fa-f]\{6\}" --include="*.py" consumo_lib/

# Encontrar QFont manual
grep -r "QFont()" --include="*.py" consumo_lib/

# Encontrar setMinimumHeight hardcoded
grep -r "setMinimumHeight([0-9]" --include="*.py" consumo_lib/
```

---

## Padrões de Refatoração

### Padrão 1: Cores Hex → Design Tokens

**Antes**:
```python
setStyleSheet(f"background-color: #4CAF50;")
setStyleSheet(f"color: white;")
setStyleSheet(f"border: 1px solid #E0E0E0;")
```

**Depois**:
```python
from consumo_lib.ui import COLORS

setStyleSheet(f"background-color: {COLORS.PRIMARY};")
setStyleSheet(f"color: {COLORS.BACKGROUND};")
setStyleSheet(f"border: 1px solid {COLORS.OUTLINE};")
```

**Mapeamento de cores comuns**:

| Cor Hex | Token | Uso |
|---------|-------|-----|
| `#4CAF50` | `COLORS.PRIMARY` | Ações principais |
| `#2196F3` | `COLORS.SECONDARY` | Ações secundárias |
| `#F44336` | `COLORS.ERROR` | Erros |
| `#f1c40f` | `COLORS.WARNING` | Avisos |
| `#2ecc71` | `COLORS.SUCCESS` | Sucesso |
| `#FFFFFF` / `white` | `COLORS.BACKGROUND` | Fundo branco |
| `#212121` | `COLORS.ON_BACKGROUND` | Texto sobre fundo |
| `#E0E0E0` | `COLORS.OUTLINE` | Bordas |
| `#9E9E9E` | `COLORS.STATUS_PENDING` | Pendente |
| `#4CAF50` | `COLORS.STATUS_APPROVED_AUTO` | Aprovado auto |
| `#CDDC39` | `COLORS.STATUS_APPROVED_USER` | Aprovado manual |
| `#F44336` | `COLORS.STATUS_REJECTED` | Reprovado |

### Padrão 2: QFont Manual → Typography

**Antes**:
```python
font = QFont()
font.setPointSize(14)
font.setBold(True)
label.setFont(font)
```

**Depois**:
```python
from consumo_lib.ui import TYPO

label.setFont(TYPO.get_font(14, bold=True))

# OU usar tokens pré-definidos
label.setFont(TYPO.get_font(TYPO.BODY_LARGE, bold=True))
```

**Mapeamento de tamanhos comuns**:

| Tamanho | Token | Uso |
|---------|-------|-----|
| 11px | `TYPO.LABEL_SMALL` | Captions, badges |
| 12px | `TYPO.LABEL_MEDIUM` | Labels de formulário |
| 14px | `TYPO.BODY_MEDIUM` | Texto padrão |
| 16px | `TYPO.BODY_LARGE` | Botões, labels importantes |
| 24px | `TYPO.HEADLINE_SMALL` | Títulos de seção |

### Padrão 3: Tamanhos Hardcoded → Dimensions

**Antes**:
```python
btn.setMinimumHeight(40)
setContentsMargins(16, 16, 16, 16)
setSpacing(8)
```

**Depois**:
```python
from consumo_lib.ui import DIM, SPACE

btn.setMinimumHeight(DIM.BUTTON_HEIGHT_MD)
setContentsMargins(SPACE.MD, SPACE.MD, SPACE.MD, SPACE.MD)
setSpacing(SPACE.SM)
```

**Mapeamento de tamanhos comuns**:

| Valor Hardcoded | Token | Uso |
|-----------------|-------|-----|
| 4px | `SPACE.BASE` ou `SPACE.XS` | Espaçamento mínimo |
| 8px | `SPACE.SM` | Elementos próximos |
| 16px | `SPACE.MD` | Espaçamento padrão |
| 24px | `SPACE.LG` | Seções distintas |
| 32px | `SPACE.XL` | Grandes seções |
| 40px | `DIM.BUTTON_HEIGHT_MD`, `DIM.INPUT_HEIGHT_MD` | Botões e inputs |
| 32px | `DIM.BUTTON_HEIGHT_SM` | Botões pequenos |
| 8px | `DIM.RADIUS_MD` | Border radius padrão |

### Padrão 4: Component Qt → Componente Padrão

**Antes**:
```python
btn = QPushButton("Salvar")
font = QFont()
font.setPointSize(16)
font.setBold(True)
btn.setFont(font)
btn.setMinimumHeight(40)
btn.setStyleSheet("""
    QPushButton {
        background-color: #4CAF50;
        color: white;
        border-radius: 8px;
        padding: 8px 24px;
    }
""")
```

**Depois**:
```python
from consumo_lib.ui.widget_standards import StandardButton

btn = StandardButton("Salvar", variant="primary")
```

---

## Exemplos Reais

### Exemplo 1: StatusBadge

**Arquivo**: `consumo_lib/widgets/status_badge.py`

#### Passo 1: Importar Design Tokens

```python
# Adicionar no topo do arquivo
from consumo_lib.ui import COLORS, TYPO, SPACE, DIM
```

#### Passo 2: Migrar Cores

**Antes**:
```python
STATUS_COLORS = {
    "approved_auto": "#4CAF50",
    "approved_user": "#CDDC39",
    "rejected": "#F44336",
    "pending": "#9E9E9E",
    "in_progress": "#2196F3",
}
```

**Depois**:
```python
STATUS_COLORS = {
    "approved_auto": COLORS.STATUS_APPROVED_AUTO,
    "approved_user": COLORS.STATUS_APPROVED_USER,
    "rejected": COLORS.STATUS_REJECTED,
    "pending": COLORS.STATUS_PENDING,
    "in_progress": COLORS.SECONDARY,
}
```

#### Passo 3: Migrar setStyleSheet()

**Antes**:
```python
self.setStyleSheet(f"""
    QLabel {{
        background-color: {color};
        color: white;
        padding: 4px 12px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 11px;
    }}
""")
```

**Depois**:
```python
self.setStyleSheet(f"""
    QLabel {{
        background-color: {color};
        color: {COLORS.BACKGROUND};
        padding: {SPACE.XS}px {SPACE.MD}px;
        border-radius: {DIM.RADIUS_SM}px;
        font-weight: bold;
        font-size: {TYPO.LABEL_SMALL}px;
    }}
""")
```

#### Resultado

- ✅ Cores centralizadas
- ✅ Espaçamentos consistentes
- ✅ Type-safe (não são strings)
- ✅ Fácil manutenção

**Commit**: `1f34c30` - feat(widgets): Migrate StatusBadge to Design System

### Exemplo 2: MovementControlWidget

**Arquivo**: `consumo_lib/widgets/movement_control.py`

#### Passo 1: Importar Design Tokens

```python
# Adicionar no topo do arquivo
from consumo_lib.ui import TYPO, DIM
```

#### Passo 2: Migrar QFont()

**Antes**:
```python
# Directional buttons
for btn in [self.up_button, self.down_button, ...]:
    font = QFont()
    font.setBold(True)
    font.setPointSize(16)
    btn.setFont(font)

# Emergency stop
font_stop = QFont()
font_stop.setBold(True)
self.emergency_stop_button.setFont(font_stop)

# Go to Zero
font = QFont()
font.setBold(True)
self.go_to_zero_btn.setFont(font)
```

**Depois**:
```python
# Directional buttons
for btn in [self.up_button, self.down_button, ...]:
    font = TYPO.get_font(16, bold=True)
    btn.setFont(font)

# Emergency stop
font_stop = TYPO.get_font(TYPO.BODY_LARGE, bold=True)
self.emergency_stop_button.setFont(font_stop)

# Go to Zero
font = TYPO.get_font(TYPO.BODY_LARGE, bold=True)
self.go_to_zero_btn.setFont(font)
```

#### Passo 3: Migrar setMinimumHeight()

**Antes**:
```python
self.emergency_stop_button.setMinimumSize(100, 40)
self.go_to_zero_btn.setMinimumHeight(40)
self.backlight_button.setMinimumHeight(35)
```

**Depois**:
```python
self.emergency_stop_button.setMinimumSize(100, DIM.BUTTON_HEIGHT_MD)
self.go_to_zero_btn.setMinimumHeight(DIM.BUTTON_HEIGHT_MD)
self.backlight_button.setMinimumHeight(DIM.BUTTON_HEIGHT_SM)
```

#### Resultado

- ✅ Alturas consistentes
- ✅ Fontes padronizadas
- ✅ Menos código repetitivo

**Commit**: `122ed8d` - feat(widgets): Migrate MovementControl to Design System

---

## Erros Comuns

### Erro 1: Token Inexistente

**Erro**:
```
AttributeError: 'ColorPalette' object has no attribute 'DISABLED'
```

**Causa**: Usar nome de token errado

**Solução**: Verificar token correto em `consumo_lib/ui/design_tokens.py`

```python
# ❌ ERRADO
"pending": COLORS.DISABLED,  # Token não existe

# ✅ CORRETO
"pending": COLORS.STATUS_PENDING,  # Token correto
```

### Erro 2: Confundir WHITE com BACKGROUND

**Erro**:
```
AttributeError: 'ColorPalette' object has no attribute 'WHITE'
```

**Solução**: Usar `COLORS.BACKGROUND` para branco

```python
# ❌ ERRADO
color: {COLORS.WHITE};

# ✅ CORRETO
color: {COLORS.BACKGROUND};
```

### Erro 3: Confundir CAPTION com LABEL_SMALL

**Erro**:
```
AttributeError: 'Typography' object has no attribute 'CAPTION'
```

**Solução**: Usar `TYPO.LABEL_SMALL` (11px)

```python
# ❌ ERRADO
font-size: {TYPO.CAPTION}px;

# ✅ CORRETO
font-size: {TYPO.LABEL_SMALL}px;
```

### Erro 4: Esquecer de Importar

**Erro**:
```
NameError: name 'COLORS' is not defined
```

**Solução**: Sempre importar tokens no topo do arquivo

```python
# Adicionar no topo do arquivo
from consumo_lib.ui import COLORS, TYPO, SPACE, DIM
```

### Erro 5: Fazer Override do Estilo Padrão

**Problema**: Componente StandardButton com estilo incorreto

```python
# ❌ ERRADO - Sobrescreve estilo do Design System
btn = StandardButton("Salvar", variant="primary")
btn.setMinimumHeight(60)  # Sobrescreve DIM.BUTTON_HEIGHT_MD
btn.setStyleSheet("...")  # Remove estilos do stylesheet global
```

**Solução**: Não fazer override desnecessário

```python
# ✅ CORRETO - Usa estilo padrão
btn = StandardButton("Salvar", variant="primary")
# Altura e estilo já aplicados automaticamente
```

---

## Checklist de Validação

### Antes de Commitar

- [ ] **Imports**: Adicionei `from consumo_lib.ui import COLORS, TYPO, SPACE, DIM`?
- [ ] **Cores**: Substituí todas as cores hex por tokens?
- [ ] **Fontes**: Substituí todos os `QFont()` por `TYPO.get_font()`?
- [ ] **Tamanhos**: Substituí tamanhos hardcoded por tokens DIM/SPACE?
- [ ] **Teste Visual**: Executei a aplicação para validar a aparência?
- [ ] **Smoke Test**: A aplicação abre sem erros?

### Smoke Test

```bash
# Executar aplicação
python main.py

# Validar:
# 1. Tela abre sem erros
# 2. Widget migrado tem aparência correta
# 3. Não há erros no console
```

### Validação Visual

**O que verificar**:

1. **Cores**: Tons estão corretos? (não muito claros/escuros)
2. **Fontes**: Tamanhos proporcionais? (não muito grandes/pequenos)
3. **Espaçamentos**: Layout está balanceado? (não muito apertado/espaçoso)
4. **Alinhamento**: Elementos estão alinhados corretamente?
5. **Responsividade**: Widget se comporta bem ao redimensionar?

---

## Processo de Migração Passo a Passo

### 1. Planejamento

```bash
# Identificar arquivos para migrar
grep -r "#[0-9A-Fa-f]\{6\}" --include="*.py" consumo_lib/widgets/

# Priorizar:
# - Widgets mais usados
# - Arquivos sendo modificados para bug fixes/features
# - Arquivos com muitos valores hardcoded
```

### 2. Migração

```python
# Passo 1: Adicionar imports
from consumo_lib.ui import COLORS, TYPO, SPACE, DIM

# Passo 2: Substituir cores
# - Usar grep para encontrar todas as cores hex
# - Consultar TOKENS.md para encontrar token correto
# - Substituir gradualmente

# Passo 3: Substituir QFont
# - Encontrar todos os QFont()
# - Substituir por TYPO.get_font()

# Passo 4: Substituir tamanhos
# - Encontrar setMinimumHeight(), setSpacing(), etc
# - Substituir por DIM/SPACE tokens

# Passo 5: Considerar componentes padrão
# - Substituir QPushButton por StandardButton
# - Substituir QLabel por StandardLabel
# - Quando fizer sentido
```

### 3. Testes

```bash
# Smoke test
python main.py

# Validar visualmente
# - Abrir widget migrado
# - Verificar cores, fontes, tamanhos
# - Testar interações (hover, click)

# Commit se tudo OK
git add .
git commit -m "feat(widgets): Migrate WidgetName to Design System"
```

### 4. Documentação

```bash
# Atualizar este arquivo (MIGRATION.md)
# Adicionar ao final de "Arquivos Migrados"
```

---

## Arquivos Migrados

### Status Atual: 2 arquivos migrados (2026-01-19)

### ✅ consumption_lib/widgets/status_badge.py

- **Data**: 2026-01-19
- **Commit**: `1f34c30`
- **Migrações**:
  - Cores hardcoded → COLORS tokens
  - Tamanhos hardcoded → SPACE/DIM tokens
  - Fontes hardcoded → TYPO tokens
- **Linhas alteradas**: ~30 linhas
- **Antes**: 5 cores hex hardcoded
- **Depois**: 5 COLORS tokens
- **Benefícios**: Cores centralizadas, type-safe

### ✅ consumo_lib/widgets/movement_control.py

- **Data**: 2026-01-19
- **Commit**: `122ed8d`
- **Migrações**:
  - QFont() → TYPO.get_font()
  - setMinimumHeight() hardcoded → DIM.BUTTON_HEIGHT_*
- **Linhas alteradas**: ~10 linhas
- **Antes**: 3 QFont() manuais, 3 alturas hardcoded
- **Depois**: 3 TYPO.get_font(), 3 DIM tokens
- **Benefícios**: Fontes consistentes, menos código

### 🔄 Próximos Arquivos Prioritários

- [ ] `consumo_lib/widgets/camera_capture.py`
- [ ] `consumo_lib/tabs/cnc_control_tab.py`
- [ ] `consumo_lib/tabs/tension_tab.py`
- [ ] `consumo_lib/dialogs/tension/tension_measurement_dialog.py`
- [ ] `consumo_lib/dialogs/engineering_wizard_dialog.py`

**Critério de prioridade**:
1. Widgets visíveis (tabs, dialogs)
2. Widgets com muitos valores hardcoded
3. Arquivos sendo modificados para bug fixes/features
4. Widgets críticos (main_window.py)

---

## Dicas Avançadas

### 1. Migrar Gradualmente

Não tente migrar tudo de uma vez. Migrar arquivo por arquivo durante edições naturais.

**Exemplo**:
```python
# Você está corrigindo um bug no widget
def fix_bug_in_widget(self):
    # Corrige bug
    self.value += 1

    # Enquanto está aqui, migra valores hardcoded
    # Antes: setStyleSheet(f"color: #4CAF50;")
    # Depois: from consumo_lib.ui import COLORS
    #         setStyleSheet(f"color: {COLORS.PRIMARY};")
```

### 2. Usar Search and Replace

Use a função de search and replace do IDE para acelerar:

```python
# Search: setMinimumHeight(40)
# Replace: setMinimumHeight(DIM.BUTTON_HEIGHT_MD)

# Search: setPointSize(14)
# Replace: TYPO.BODY_MEDIUM
```

**Cuidado**: Sempre revisar manualmente cada substituição.

### 3. Validação Incremental

Migrar uma função/classe por vez e testar:

```python
# Passo 1: Migrar função A
# Passo 2: Testar smoke test
# Passo 3: Commit
# Passo 4: Migrar função B
# Passo 5: Testar smoke test
# Passo 6: Commit
```

### 4. Documentar Decisões

Se precisar usar um valor customizado (não token), documente porquê:

```python
# Layout customizado (não usa SPACE.MD porque precisa ser mais compacto)
layout.setSpacing(10)
```

---

## Referências

- **[TOKENS.md](./TOKENS.md)** - Referência completa de design tokens
- **[COMPONENTS.md](./COMPONENTS.md)** - Componentes base disponíveis
- **[README.md](./README.md)** - Visão geral do Design System
- **CLAUDE.md** - Documentação do projeto (seção Design System)

---

**Última atualização**: 2026-01-19
**Versão**: 1.0.0
**Status**: 2/10 arquivos críticos migrados (20%)
