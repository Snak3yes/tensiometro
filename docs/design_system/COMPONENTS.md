# Componentes Base - Referência Completa

Guia completo de todos os componentes base disponíveis no Tensiometro Design System.

## 📋 Índice

- [O que são Componentes Base](#o-que-são-componentes-base)
- [Como Importar](#como-importar)
- [StandardButton](#standardbutton)
- [StandardLabel](#standardlabel)
- [StandardInput](#standardinput)
- [StandardSpinBox](#standardspinbox)
- [StandardDoubleSpinBox](#standardspinbox)
- [StandardComboBox](#standardcombobox)
- [StandardGroupBox](#standardgroupbox)
- [Exemplos Práticos](#exemplos-práticos)

---

## O que são Componentes Base

Componentes base são subclasses de widgets Qt com estilos **pré-aplicados** seguindo o Design System.

**Benefícios**:
- ✅ Estilo consistente sem código repetitivo
- ✅ Alturas e fontes padronizadas automaticamente
- ✅ Variantes pré-definidas (primary, secondary, etc)
- ✅ Menos código boilerplate

**Quando usar**:
- Sempre que possível para código novo
- Ao refatorar código legado
- Para garantir consistência visual

---

## Como Importar

```python
# Importar todos os componentes
from consumo_lib.ui.widget_standards import (
    StandardButton,
    StandardLabel,
    StandardInput,
    StandardSpinBox,
    StandardDoubleSpinBox,
    StandardComboBox,
    StandardGroupBox
)

# Importar componente específico
from consumo_lib.ui.widget_standards import StandardButton

# Importar com alias
from consumo_lib.ui.widget_standards import StandardButton as Btn
```

---

## StandardButton

Botão padrão com variantes de estilo e **tamanhos semânticos** (v1.1).

### Importar

```python
from consumo_lib.ui.widget_standards import StandardButton
```

### Variantes de Cor Disponíveis

| Variante | Cor Hex | Uso |
|----------|---------|-----|
| `primary-green` | `#43A047` (verde) | Ações principais de confirmação/início |
| `primary-blue` | `#455A64` (azul petróleo) | Ações padrão/genéricas |
| `primary-orange` | `#E65100` (laranja) | Ações de parada/atenção |
| `secondary` | Transparente + borda azul | Ações alternativas/cancelamento |
| `emergency` | `#C62828` (vermelho) | Emergências físicas (uso raro 1%) |
| `danger` | `[DEPRECATED]` | Use `emergency` instead |
| `outline` | Borda verde `[LEGADO]` | Use `secondary` no futuro |

### Tamanhos Semânticos (NOVO v1.1)

#### Quando usar cada `semantic_size`:

| semantic_size | Dimensões | Uso Típico |
|---------------|-----------|-------------|
| **Dialog Buttons** |||
| `dialog-primary` | 48×120px | Salvar, Confirmar, OK (ação principal) |
| `dialog-secondary` | 40×100px | Cancelar, Fechar (ação secundária) |
| `dialog-tertiary` | 36×90px | Apply, Reset (ação terciária) |
| `emergency` | 56×140px | STOP, Emergency (prominente) |
| **Movement Buttons** |||
| `directional` | 50×50px (quadrado) | ↑, ↓, ←, → (controles direcionais) |
| `z-axis` | 50×35px (retangular) | Z+, Z- (eixo Z) |
| `function-primary` | 40×100px | Home, Zero, Go To (funções críticas) |
| `function-secondary` | 40×90px | Step/Continuous, Toggle (funções auxiliares) |
| `toggle-status` | 44×44px (quadrado) | Backlight, Mode (toggle de estado) |
| **Toolbar Buttons** |||
| `toolbar-text` | 36×120px | Anterior, Próximo (texto + ícone opcional) |
| `toolbar-icon` | 40×40px (quadrado) | Refresh, Clear (ícone apenas) |
| `toolbar-icon-large` | 48×48px (quadrado) | New, Open, Save (ícone grande) |
| **Inline Buttons** |||
| `inline-primary` | 36px altura | Capturar, Calcular (ação em formulário) |
| `inline-secondary` | 32px altura | Limpar, Reset (ação auxiliar) |
| `inline-compact` | 28px altura `[CUIDADO]` | Edit, Delete em tabelas (uso moderado) |
| **Grid Buttons** |||
| `grid-action` | 44×80px | Edit, Delete, View (WCAG 2.5.5 compliant) |
| `grid-status` | 24px altura | Badges clicáveis de status |

### API

```python
StandardButton(
    text: str,
    variant: str = "primary-green",
    size: str = "md",                    # [DEPRECATED - Use semantic_size]
    semantic_size: str | None = None,   # [NOVO v1.1 - Recomendado]
    parent=None
)
```

**Parâmetros**:
- `text`: Texto do botão
- `variant`: `"primary-green"` | `"primary-blue"` | `"primary-orange"` | `"secondary"` | `"emergency"`
- `size`: `[DEPRECATED]` `"sm"` | `"md"` | `"lg"` (use `semantic_size` para código novo)
- `semantic_size`: `[NOVO v1.1]` Ver tabela acima (ex: `"dialog-primary"`, `"directional"`)
- `parent`: Widget pai (opcional)

### Estilo Aplicado Automaticamente

- Font: `TYPO.BODY_LARGE` (16px, weight=MEDIUM)
- Altura e largura: Baseado em `semantic_size` ou `size`
- Padding: Ajustado automaticamente para cada tamanho
- Border radius: Ajustado automaticamente (4-10px dependendo da variante)
- Cores via stylesheet global (styles.qss)

### Exemplos de Uso

#### Botão Primário de Dialog (NOVO v1.1 - Recomendado)

```python
from consumo_lib.ui.widget_standards import StandardButton

# Botão de salvar (diálogo principal)
btn_save = StandardButton(
    "Salvar",
    variant="primary-green",
    semantic_size="dialog-primary"  # 48×120px
)
btn_save.clicked.connect(self.on_save)
layout.addWidget(btn_save)

# Botão de cancelar (diálogo secundário)
btn_cancel = StandardButton(
    "Cancelar",
    variant="secondary",
    semantic_size="dialog-secondary"  # 40×100px
)
btn_cancel.clicked.connect(dialog.reject)
layout.addWidget(btn_cancel)
```

#### Botão de Movimento (NOVO v1.1)

```python
from consumo_lib.ui import DIM

# Botão direcional (50×50px - quadrado)
up_btn = QPushButton("↑")
up_btn.setMinimumSize(
    DIM.BUTTON_DIRECTIONAL_SIZE,
    DIM.BUTTON_DIRECTIONAL_SIZE
)
layout.addWidget(up_btn)

# Botão Z-axis (50×35px - retangular)
z_up_btn = QPushButton("Z+")
z_up_btn.setMinimumSize(
    DIM.BUTTON_Z_AXIS_WIDTH,
    DIM.BUTTON_Z_AXIS_HEIGHT
)
layout.addWidget(z_up_btn)
```

#### Botão de Toolbar (NOVO v1.1)

```python
# Botão com texto (36×120px)
new_btn = QPushButton("Novo")
new_btn.setMinimumHeight(DIM.BUTTON_TOOLBAR_TEXT_HEIGHT)
new_btn.setMinimumWidth(DIM.BUTTON_TOOLBAR_TEXT_MIN_WIDTH)
layout.addWidget(new_btn)

# Botão ícone (40×40px - quadrado)
refresh_btn = QPushButton("🔄")
refresh_btn.setFixedSize(
    DIM.BUTTON_TOOLBAR_ICON_SIZE,
    DIM.BUTTON_TOOLBAR_ICON_SIZE
)
layout.addWidget(refresh_btn)
```

#### Botões de Ação (Dialog) - LEGADO (Ainda funciona)

```python
# Botões de Confirmar/Cancelar (com size legado)
btn_confirm = StandardButton("Confirmar", size="lg")    # 160×48px
btn_cancel = StandardButton("Cancelar", size="md")     # 120×40px

btn_confirm.clicked.connect(dialog.accept)
btn_cancel.clicked.connect(dialog.reject)

button_layout.addWidget(btn_confirm)
button_layout.addWidget(btn_cancel)
```

### Estados Interativos

O stylesheet global (styles.qss) aplica estilos automáticos para:
- **Hover**: Cor levemente mais escura
- **Pressed**: Cor mais escura + transform scale(0.98)
- **Disabled**: Opacidade reduzida (38%)
- **Focus**: Borda de foco visível

### Antes vs Depois

```python
# ❌ ANTES - Código repetitivo
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
    QPushButton:hover {
        background-color: #388E3C;
    }
""")

# ✅ DEPOIS - Componente pronto
btn = StandardButton("Salvar", variant="primary")
```

---

## StandardLabel

Label padrão com 4 variantes de tipografia.

### Importar

```python
from consumo_lib.ui.widget_standards import StandardLabel
```

### Variantes Disponíveis

| Variante | Tamanho | Peso | Uso |
|----------|---------|------|-----|
| `heading` | 16px (TITLE_MEDIUM) | Bold | Títulos de seção |
| `subheading` | 16px (BODY_LARGE) | Bold | Subtítulos |
| `body` | 14px (BODY_MEDIUM) | Normal | Texto padrão |
| `caption` | 11px (LABEL_SMALL) | Normal | Captions, textos pequenos |

### API

```python
StandardLabel(text: str, variant: str = "body", parent=None)
```

**Parâmetros**:
- `text`: Texto da label
- `variant`: `"heading"` | `"subheading"` | `"body"` | `"caption"`
- `parent`: Widget pai (opcional)

### Estilo Aplicado Automaticamente

Cada variante aplica automaticamente:
- Font size e weight via `Typography.get_font()`
- Cor via stylesheet global (styles.qss)

### Exemplos de Uso

#### Título de Seção

```python
from consumo_lib.ui.widget_standards import StandardLabel

# Título de seção
title = StandardLabel("Configurações de Movimento", variant="heading")
layout.addWidget(title)
```

#### Subtítulo

```python
# Subtítulo descritivo
subtitle = StandardLabel("Ajuste os parâmetros abaixo", variant="subheading")
layout.addWidget(subtitle)
```

#### Texto Padrão

```python
# Texto informativo (variante padrão)
info = StandardLabel("Clique em salvar para aplicar as alterações")
layout.addWidget(info)
```

#### Caption (Texto Pequeno)

```python
# Caption ou nota
caption = StandardLabel("* Campos obrigatórios", variant="caption")
layout.addWidget(caption)
```

#### Labels com Rich Text

```python
# Labels suportam HTML
heading = StandardLabel("<b>Título em Negrito</b>", variant="heading")
body = StandardLabel("Texto com <span style='color: red'>destaque</span>")
```

### Antes vs Depois

```python
# ❌ ANTES
title = QLabel("Configurações")
font = QFont()
font.setPointSize(16)
font.setBold(True)
title.setFont(font)

# ✅ DEPOIS
title = StandardLabel("Configurações", variant="heading")
```

---

## StandardInput

Input de texto padrão com altura consistente.

### Importar

```python
from consumo_lib.ui.widget_standards import StandardInput
```

### API

```python
StandardInput(placeholder: str = "", parent=None)
```

**Parâmetros**:
- `placeholder`: Texto de placeholder (opcional)
- `parent`: Widget pai (opcional)

### Estilo Aplicado Automaticamente

- Altura mínima: `DIM.INPUT_HEIGHT_MD` (40px)
- Padding: `SPACE.SM` (8px) vertical, `SPACE.MD` (16px) horizontal
- Border radius: `DIM.RADIUS_MD` (8px)
- Font: `TYPO.BODY_MEDIUM` (14px)
- Cor de borda: `COLORS.OUTLINE` (#E0E0E0)
- Cor de foco: `COLORS.PRIMARY` (#4CAF50)

### Exemplos de Uso

#### Input Simples

```python
from consumo_lib.ui.widget_standards import StandardInput

# Input com placeholder
name_input = StandardInput(placeholder="Digite seu nome")
layout.addWidget(name_input)

# Obter valor
name = name_input.text()
```

#### Input com Validação

```python
# Input de email
email_input = StandardInput(placeholder="exemplo@email.com")
email_input.setInputMask("")  # Sem máscara
layout.addWidget(email_input)

# Validar
if "@" in email_input.text():
    print("Email válido")
```

#### Input Somente Leitura

```python
# Input read-only
code_input = StandardInput(placeholder="Código do produto")
code_input.setReadOnly(True)
code_input.setText("PROD-12345")
layout.addWidget(code_input)
```

#### Input com Validador Numérico

```python
from PyQt6.QtGui import QIntValidator

# Apenas números
age_input = StandardInput(placeholder="Idade")
age_input.setValidator(QIntValidator(0, 120, age_input))
layout.addWidget(age_input)
```

### Estados Especiais

- **Focus**: Borda verde (COLORS.PRIMARY)
- **Disabled**: Fundo cinza (COLORS.SURFACE)
- **Readonly**: Fundo cinza claro (COLORS.SURFACE_VARIANT)

### Antes vs Depois

```python
# ❌ ANTES
input = QLineEdit()
input.setPlaceholderText("Digite seu nome")
input.setMinimumHeight(40)
input.setStyleSheet("""
    QLineEdit {
        border: 1px solid #E0E0E0;
        border-radius: 8px;
        padding: 8px 16px;
        font-size: 14px;
    }
""")

# ✅ DEPOIS
input = StandardInput(placeholder="Digite seu nome")
```

---

## StandardSpinBox

SpinBox numérico padrão (inteiros).

### Importar

```python
from consumo_lib.ui.widget_standards import StandardSpinBox
```

### API

```python
StandardSpinBox(parent=None)
```

**Parâmetros**:
- `parent`: Widget pai (opcional)

### Estilo Aplicado Automaticamente

- Altura mínima: `DIM.INPUT_HEIGHT_MD` (40px)
- Mesmo estilo que StandardInput
- Setas de incremento/decremento estilizadas

### Exemplos de Uso

#### SpinBox Simples

```python
from consumo_lib.ui.widget_standards import StandardSpinBox

# SpinBox de 0 a 100
quantity = StandardSpinBox()
quantity.setRange(0, 100)
quantity.setValue(1)
layout.addWidget(quantity)

# Obter valor
qty = quantity.value()
```

#### SpinBox com Step Personalizado

```python
# SpinBox com passo de 5
step_spinbox = StandardSpinBox()
step_spinbox.setRange(0, 1000)
step_spinbox.setSingleStep(5)  # Incrementa de 5 em 5
step_spinbox.setValue(10)
layout.addWidget(step_spinbox)
```

#### SpinBox com Suffix

```python
# SpinBox com unidade
feed_rate = StandardSpinBox()
feed_rate.setRange(0, 30000)
feed_rate.setSuffix(" mm/min")  # Exibe "1000 mm/min"
feed_rate.setValue(1000)
layout.addWidget(feed_rate)
```

#### SpinBox com Prefix

```python
# SpinBox com prefixo
temperature = StandardSpinBox()
temperature.setRange(-50, 150)
temperature.setPrefix("±")  # Exibe "±25 °C"
temperature.setSuffix(" °C")
temperature.setValue(25)
layout.addWidget(temperature)
```

### Métodos Úteis

```python
spinbox = StandardSpinBox()

# Configurar range
spinbox.setMinimum(0)
spinbox.setMaximum(100)
# OU
spinbox.setRange(0, 100)

# Configurar passo
spinbox.setSingleStep(5)

# Valor atual
value = spinbox.value()  # int

# Configurar prefix/suffix
spinbox.setPrefix("R$")
spinbox.setSuffix(".00")

# Alinhamento do texto
from PyQt6.QtCore import Qt
spinbox.setAlignment(Qt.AlignmentFlag.AlignRight)
```

### Antes vs Depois

```python
# ❌ ANTES
spinbox = QSpinBox()
spinbox.setRange(0, 100)
spinbox.setMinimumHeight(40)
spinbox.setStyleSheet("...")

# ✅ DEPOIS
spinbox = StandardSpinBox()
spinbox.setRange(0, 100)
```

---

## StandardDoubleSpinBox

SpinBox numérico padrão (números decimais).

### Importar

```python
from consumo_lib.ui.widget_standards import StandardDoubleSpinBox
```

### API

```python
StandardDoubleSpinBox(parent=None)
```

**Parâmetros**:
- `parent`: Widget pai (opcional)

### Estilo Aplicado Automaticamente

- Altura mínima: `DIM.INPUT_HEIGHT_MD` (40px)
- Mesmo estilo que StandardSpinBox
- Suporte a casas decimais

### Exemplos de Uso

#### DoubleSpinBox Simples

```python
from consumo_lib.ui.widget_standards import StandardDoubleSpinBox

# DoubleSpinBox com 2 casas decimais
price = StandardDoubleSpinBox()
price.setRange(0.0, 9999.99)
price.setDecimals(2)
price.setValue(19.99)
layout.addWidget(price)

# Obter valor
value = price.value()  # float
```

#### DoubleSpinBox com Precisão

```python
# Medição de tensão (3 casas decimais)
tension = StandardDoubleSpinBox()
tension.setRange(0.0, 100.0)
tension.setDecimals(3)  # 3 casas decimais
tension.setSingleStep(0.1)  # Incrementa 0.1
tension.setSuffix(" N/cm²")
tension.setValue(12.345)
layout.addWidget(tension)
```

#### DoubleSpinBox com Step Pequeno

```python
# Medição precisa (step de 0.01)
measurement = StandardDoubleSpinBox()
measurement.setRange(0.0, 100.0)
measurement.setDecimals(2)
measurement.setSingleStep(0.01)  # Incrementa 0.01
measurement.setValue(10.50)
layout.addWidget(measurement)
```

### Diferenças para StandardSpinBox

| Característica | StandardSpinBox | StandardDoubleSpinBox |
|----------------|-----------------|----------------------|
| Tipo de dado | `int` | `float` |
| Casas decimais | Não | Sim (configurável) |
| Step padrão | 1 | 1.0 |
| Uso típico | Quantidades, contadores | Medições, preços |

### Antes vs Depois

```python
# ❌ ANTES
spinbox = QDoubleSpinBox()
spinbox.setRange(0.0, 100.0)
spinbox.setDecimals(2)
spinbox.setMinimumHeight(40)
spinbox.setStyleSheet("...")

# ✅ DEPOIS
spinbox = StandardDoubleSpinBox()
spinbox.setRange(0.0, 100.0)
spinbox.setDecimals(2)
```

---

## StandardComboBox

ComboBox (dropdown) padrão.

### Importar

```python
from consumo_lib.ui.widget_standards import StandardComboBox
```

### API

```python
StandardComboBox(parent=None)
```

**Parâmetros**:
- `parent`: Widget pai (opcional)

### Estilo Aplicado Automaticamente

- Altura mínima: `DIM.INPUT_HEIGHT_MD` (40px)
- Mesmo estilo que StandardInput
- Setas dropdown estilizadas

### Exemplos de Uso

#### ComboBox Simples

```python
from consumo_lib.ui.widget_standards import StandardComboBox

# Dropdown de opções
role_combo = StandardComboBox()
role_combo.addItem("Operador")
role_combo.addItem("Engenheiro")
role_combo.addItem("Administrador")
layout.addWidget(role_combo)

# Obter seleção
selected_role = role_combo.currentText()
```

#### ComboBox com Dados

```python
# Dropdown com dados associados
status_combo = StandardComboBox()
status_combo.addItem("Pendente", "pending")
status_combo.addItem("Em Andamento", "in_progress")
status_combo.addItem("Concluído", "completed")

layout.addWidget(status_combo)

# Obter valor associado
status_value = status_combo.currentData()  # "pending", "in_progress", etc
status_text = status_combo.currentText()   # "Pendente", "Em Andamento", etc
```

#### ComboBox com Seleção Padrão

```python
# Dropdown com seleção inicial
mode_combo = StandardComboBox()
mode_combo.addItem("Modo Passo")
mode_combo.addItem("Modo Contínuo")
mode_combo.setCurrentIndex(1)  # Seleciona "Modo Contínuo"
layout.addWidget(mode_combo)
```

#### ComboBox Editável

```python
# ComboBox editável (usuário pode digitar)
search_combo = StandardComboBox()
search_combo.setEditable(True)
search_combo.addItem("Opção 1")
search_combo.addItem("Opção 2")
search_combo.setPlaceholderText("Buscar...")
layout.addWidget(search_combo)
```

### Métodos Úteis

```python
combo = StandardComboBox()

# Adicionar itens
combo.addItem("Texto")
combo.addItem("Texto com dado", "data_value")

# Múltiplos itens
items = ["Opção 1", "Opção 2", "Opção 3"]
combo.addItems(items)

# Seleção
combo.setCurrentIndex(0)  # Por índice
combo.setCurrentText("Opção 1")  # Por texto

# Obter valores
text = combo.currentText()  # str
data = combo.currentData()  # Any
index = combo.currentIndex()  # int

# Contar itens
count = combo.count()

# Limpar
combo.clear()
```

### Signals Úteis

```python
combo = StandardComboBox()

# Detectar mudança de seleção
combo.currentTextChanged.connect(self.on_selection_changed)
combo.currentIndexChanged.connect(self.on_index_changed)

# Exemplo:
def on_selection_changed(self, text: str):
    print(f"Selecionado: {text}")
```

### Antes vs Depois

```python
# ❌ ANTES
combo = QComboBox()
combo.addItem("Opção 1")
combo.addItem("Opção 2")
combo.setMinimumHeight(40)
combo.setStyleSheet("...")

# ✅ DEPOIS
combo = StandardComboBox()
combo.addItem("Opção 1")
combo.addItem("Opção 2")
```

---

## StandardGroupBox

GroupBox padrão com espaçamento consistente.

### Importar

```python
from consumo_lib.ui.widget_standards import StandardGroupBox
```

### API

```python
StandardGroupBox(title: str, parent=None)
```

**Parâmetros**:
- `title`: Título do groupbox
- `parent`: Widget pai (opcional)

### Estilo Aplicado Automaticamente

- Espaçamento interno: `SPACE.MD` (16px)
- Borda arredondada: `DIM.RADIUS_MD` (8px)
- Font do título: `TYPO.TITLE_MEDIUM` (16px, bold)

### Exemplos de Uso

#### GroupBox Simples

```python
from consumo_lib.ui.widget_standards import StandardGroupBox
from PyQt6.QtWidgets import QVBoxLayout, QLabel

# GroupBox para agrupar controles
movement_group = StandardGroupBox("Controles de Movimento")
layout = QVBoxLayout()

label1 = QLabel("Conteúdo do grupo")
layout.addWidget(label1)

movement_group.setLayout(layout)
main_layout.addWidget(movement_group)
```

#### GroupBox com Formulário

```python
# GroupBox com formulário
config_group = StandardGroupBox("Configurações")
form_layout = QVBoxLayout()

# Adicionar campos
from consumo_lib.ui.widget_standards import StandardInput

name_input = StandardInput(placeholder="Nome")
email_input = StandardInput(placeholder="Email")

form_layout.addWidget(name_input)
form_layout.addWidget(email_input)

config_group.setLayout(form_layout)
main_layout.addWidget(config_group)
```

#### GroupBox com Grid

```python
# GroupBox com grid layout
from PyQt6.QtWidgets import QGridLayout
from consumo_lib.ui import SPACE

position_group = StandardGroupBox("Posição Atual")
grid_layout = QGridLayout()
grid_layout.setSpacing(SPACE.MD)  # 16px entre itens

# Adicionar campos
grid_layout.addWidget(QLabel("X:"), 0, 0)
grid_layout.addWidget(QLabel("Y:"), 1, 0)
grid_layout.addWidget(QLabel("Z:"), 2, 0)

position_group.setLayout(grid_layout)
main_layout.addWidget(position_group)
```

#### GroupBox Aninhado

```python
# GroupBox dentro de outro GroupBox
outer_group = StandardGroupBox("Configurações Gerais")
outer_layout = QVBoxLayout()

inner_group = StandardGroupBox("Configurações Avançadas")
inner_layout = QVBoxLayout()
inner_layout.addWidget(QLabel("Opção avançada"))
inner_group.setLayout(inner_layout)

outer_layout.addWidget(inner_group)
outer_group.setLayout(outer_layout)
main_layout.addWidget(outer_group)
```

### Personalização Avançada

```python
# GroupBox com checkbox
from PyQt6.QtWidgets import QCheckBox

group = StandardGroupBox("Opções")
layout = QVBoxLayout()

checkbox = QCheckBox("Habilitar recurso")
layout.addWidget(checkbox)

group.setLayout(layout)
main_layout.addWidget(group)

# Conectar checkbox ao estado do groupbox
checkbox.toggled.connect(group.setChecked)
```

### Diferenças para QGroupBox Padrão

| Característica | QGroupBox | StandardGroupBox |
|----------------|-----------|------------------|
| Espaçamento padrão | 9px | 16px (SPACE.MD) |
| Altura mínima | Não | 16px |
| Estilo visual | Básico | Arredondado, moderno |
| Font do título | Padrão | 16px bold |

### Antes vs Depois

```python
# ❌ ANTES
group = QGroupBox("Controles")
layout = QVBoxLayout()
layout.setSpacing(16)  # Tem que configurar manualmente
group.setLayout(layout)

# ✅ DEPOIS
group = StandardGroupBox("Controles")
# Spacing já vem configurado automaticamente
layout = group.layout()
```

---

## Exemplos Práticos

### Formulário de Login

```python
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout
from consumo_lib.ui.widget_standards import (
    StandardLabel,
    StandardInput,
    StandardButton,
    StandardGroupBox
)

# GroupBox do formulário
form_group = StandardGroupBox("Login")
form_layout = QVBoxLayout()

# Título
title = StandardLabel("Entre com suas credenciais", variant="heading")
form_layout.addWidget(title)

# Campos
username_input = StandardInput(placeholder="Usuário")
password_input = StandardInput(placeholder="Senha")
password_input.setEchoMode(QLineEdit.EchoMode.Password)

form_layout.addWidget(username_input)
form_layout.addWidget(password_input)

# Botões
button_layout = QHBoxLayout()
btn_login = StandardButton("Entrar", variant="primary")
btn_cancel = StandardButton("Cancelar", variant="secondary")

button_layout.addWidget(btn_login)
button_layout.addWidget(btn_cancel)

form_layout.addLayout(button_layout)

form_group.setLayout(form_layout)
main_layout.addWidget(form_group)
```

### Dialog com Pergunta

```python
from PyQt6.QtWidgets import QDialog, QVBoxLayout
from consumo_lib.ui.widget_standards import StandardLabel, StandardButton

class ConfirmDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)

        # Mensagem
        msg = StandardLabel(
            "Deseja realmente excluir este item?",
            variant="body"
        )
        layout.addWidget(msg)

        # Botões
        btn_layout = QHBoxLayout()
        btn_yes = StandardButton("Sim", variant="danger")
        btn_no = StandardButton("Não", variant="secondary")

        btn_yes.clicked.connect(self.accept)
        btn_no.clicked.connect(self.reject)

        btn_layout.addWidget(btn_yes)
        btn_layout.addWidget(btn_no)

        layout.addLayout(btn_layout)
```

### Painel de Controle

```python
from PyQt6.QtWidgets import QGridLayout
from consumo_lib.ui.widget_standards import (
    StandardGroupBox,
    StandardLabel,
    StandardSpinBox,
    StandardDoubleSpinBox,
    StandardButton
)

# GroupBox de controles
control_group = StandardGroupBox("Parâmetros de Movimento")
grid_layout = QGridLayout()

# Labels
grid_layout.addWidget(StandardLabel("Step Size (mm):"), 0, 0)
grid_layout.addWidget(StandardLabel("Feed Rate:"), 1, 0)

# Inputs
step_spinbox = StandardSpinBox()
step_spinbox.setRange(1, 100)
step_spinbox.setValue(10)

feed_spinbox = StandardDoubleSpinBox()
feed_spinbox.setRange(0.0, 30000.0)
feed_spinbox.setValue(1000.0)

grid_layout.addWidget(step_spinbox, 0, 1)
grid_layout.addWidget(feed_spinbox, 1, 1)

# Botão de ação
btn_apply = StandardButton("Aplicar", variant="primary")
grid_layout.addWidget(btn_apply, 2, 0, 1, 2)

control_group.setLayout(grid_layout)
main_layout.addWidget(control_group)
```

---

## Boas Práticas

### 1. Sempre Use Componentes Padrão

```python
# ❌ ERRADO - Widget Qt puro
btn = QPushButton("Salvar")

# ✅ CORRETO - Componente Design System
btn = StandardButton("Salvar", variant="primary")
```

### 2. Escolha a Variante Correta

```python
# ✅ CORRETO - Variantes semânticas
btn_primary = StandardButton("Salvar", variant="primary")
btn_secondary = StandardButton("Cancelar", variant="secondary")
btn_danger = StandardButton("Excluir", variant="danger")
```

### 3. Combine com Design Tokens

```python
from consumo_lib.ui import COLORS, SPACE

# Labels suportam HTML + tokens
label = StandardLabel(
    f"<span style='color: {COLORS.ERROR}'>Campo obrigatório</span>",
    variant="caption"
)
```

### 4. Use Layouts Consistentes

```python
from consumo_lib.ui import SPACE

# Espaçamento consistente
layout.setSpacing(SPACE.MD)  # 16px entre widgets
layout.setContentsMargins(SPACE.LG, SPACE.MD, SPACE.LG, SPACE.MD)
```

### 5. Signals e Slots

```python
# Sempre conecte signals após criar o widget
btn = StandardButton("Salvar", variant="primary")
btn.clicked.connect(self.on_save)  # ✅ CORRETO

# ❌ ERRADO - Criar widget e não conectar
btn = StandardButton("Salvar", variant="primary")
# Esqueceu de conectar o signal
```

---

## Referência Rápida

```python
# Importar tudo
from consumo_lib.ui.widget_standards import (
    StandardButton,        # Botões (4 variantes)
    StandardLabel,         # Labels (4 variantes)
    StandardInput,         # Input de texto
    StandardSpinBox,       # Números inteiros
    StandardDoubleSpinBox, # Números decimais
    StandardComboBox,      # Dropdowns
    StandardGroupBox       # Agrupamentos
)

# Variantes de botão
StandardButton("Texto", variant="primary")    # Verde (ação principal)
StandardButton("Texto", variant="secondary")  # Azul (ação secundária)
StandardButton("Texto", variant="danger")     # Vermelho (ação destrutiva)
StandardButton("Texto", variant="outline")    # Borda (ação terciária)

# Variantes de label
StandardLabel("Texto", variant="heading")     # Título (16px, bold)
StandardLabel("Texto", variant="subheading")  # Subtítulo (16px, bold)
StandardLabel("Texto")                        # Body (14px, normal)
StandardLabel("Texto", variant="caption")     # Caption (11px, gray)

# SpinBoxes
spin = StandardSpinBox()           # int: setRange(0, 100)
spin = StandardDoubleSpinBox()     # float: setRange(0.0, 100.0), setDecimals(2)
```

---

## Troubleshooting

### Componente não aparece com o estilo correto

**Problema**: StandardButton tem aparência padrão do Qt

**Causa**: ThemeManager não inicializado ou stylesheet não carregado

**Solução**:
```python
# Em main.py
from consumo_lib.ui.theme_manager import init_theme_manager

app = QApplication(sys.argv)
theme_mgr = init_theme_manager(app)  # Aplica styles.qss automaticamente
```

### Altura dos componentes está errada

**Problema**: Input com altura diferente do esperado

**Causa**: Stylesheet local sobrescrevendo altura mínima

**Solução**:
```python
# ❌ ERRADO
input = StandardInput()
input.setMinimumHeight(60)  # Sobrescreve DESIGN_TOKEN

# ✅ CORRETO
input = StandardInput()
# Altura já vem configurada via DIM.INPUT_HEIGHT_MD
```

### Fonte não está sendo aplicada

**Problema**: Label com fonte padrão do sistema

**Causa**: Font sendo sobrescrita depois de criar o componente

**Solução**:
```python
# ❌ ERRADO
label = StandardLabel("Texto", variant="heading")
label.setFont(QFont("Arial", 12))  # Sobrescreve fonte do Design System

# ✅ CORRETO
label = StandardLabel("Texto", variant="heading")
# Font já aplicada via Typography.get_font()
```

---

**Última atualização**: 2026-01-20
**Versão**: 1.1.0 - Semantic Button Sizes
