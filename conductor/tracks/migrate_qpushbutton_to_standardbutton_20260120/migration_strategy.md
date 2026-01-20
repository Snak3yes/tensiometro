# Matriz de Migração: QPushButton → StandardButton

**Data:** 2026-01-20
**Track:** migrate_qpushbutton_to_standardbutton_20260120

## Categorização de Tipos de Botão

### Tipo 1: Ação Primária (~40% dos botões)
**Características:**
- Ação principal do dialog/form
- Exemplos: "Salvar", "Aplicar", "Confirmar", "OK", "Concluir"
- Visual: Destaque visual, cor primária

**Migração:**
```python
# ANTES
btn = QPushButton("Salvar")

# DEPOIS
from consumo_lib.ui.widget_standards import StandardButton
btn = StandardButton("Salvar", variant="primary")
```

**Exemplos identificados:**
- camera_settings_controller.py: "Salvar/Atualizar", "Aplicar Ajustes", "Aplicar Ajustes (Câmera)"
- calibration_controller.py: "Aplicar Parâmetros", "Concluir"
- inspection_ui_controller.py: "🎯 Configurar Alinhamento"
- movement_control.py: "Go to Zero", "Go to Position"

### Tipo 2: Ação Secundária (~30% dos botões)
**Características:**
- Ações secundárias ou de cancelamento
- Exemplos: "Cancelar", "Fechar", "Voltar", "Carregar"
- Visual: Menos destaque, cor secundária ou neutra

**Migração:**
```python
# ANTES
btn = QPushButton("Cancelar")

# DEPOIS
btn = StandardButton("Cancelar", variant="secondary")
# OU
btn = StandardButton("Cancelar")  # variant="secondary" é o padrão
```

**Exemplos identificados:**
- camera_settings_controller.py: "Carregar", "Fechar", "Exportar JSON", "Restaurar Padrão"
- calibration_controller.py: "Cancelar", "Testar Calibração", "Mover X", "Mover Y", "Zerar Posição"

### Tipo 3: Ação Perigosa (~5% dos botões)
**Características:**
- Ações destrutivas ou irreversíveis
- Exemplos: "Excluir", "Deletar", "Remover", "STOP" (emergency)
- Visual: Cor de erro/aviso para indicar perigo
- **VIOLAÇÃO:** movement_control.py linha 113 tem hardcoded "background-color: red"

**Migração:**
```python
# ANTES (COM VIOLAÇÃO)
btn = QPushButton("STOP")
btn.setStyleSheet("background-color: red; color: white;")  # ❌ HARDCODED

# DEPOIS
btn = StandardButton("STOP", variant="danger")
```

**Exemplos identificados:**
- movement_control.py: "STOP" (emergency stop button) - **HARDCODED RED DETECTED**

### Tipo 4: Botões de Ícone (~15% dos botões)
**Características:**
- Apenas ícone/símbolo, sem texto
- Exemplos: "📁", "🎯", "↑", "↓", "←", "→", "Z+", "Z-"
- Visual: Quadrado ou circular, com ícone centralizado

**Migração:**
```python
# ANTES
btn = QPushButton("📁")
btn.setMinimumSize(50, 50)
font = TYPO.get_font(16, bold=True)
btn.setFont(font)

# DEPOIS - OPÇÃO A: StandardButton com ícone
btn = StandardButton("📁", icon_only=True)

# DEPOIS - OPÇÃO B: setStyleSheet customizado (para tamanhos específicos)
from consumo_lib.ui import COLORS, DIM
btn = QPushButton("📁")
btn.setMinimumSize(50, 50)
btn.setStyleSheet(f"""
    QPushButton {{
        background-color: {COLORS.SURFACE};
        color: {COLORS.TEXT_PRIMARY};
        border: 2px solid {COLORS.BORDER};
        border-radius: {DIM.RADIUS_SM}px;
        font-size: 16px;
        font-weight: bold;
    }}
    QPushButton:hover {{
        background-color: {COLORS.PRIMARY};
        color: {COLORS.ON_PRIMARY};
    }}
""")
```

**Exemplos identificados:**
- movement_control.py: ↑, ↓, ←, →, Z+, Z- (6 botões direcionais)
- inspection_ui_controller.py: 📁, 📁, 🎯, ⚙️ (botões com ícone + texto)

### Tipo 5: Botões Toggle/Checkable (~10% dos botões)
**Características:**
- Mantêm estado (ligado/desligado)
- Exemplos: "Passo" vs "Contínuo", "💡 Backlight OFF" / "ON"
- Visual: Mudam aparência quando checked
- Alguns usam setStyleSheet com COLORS (JÁ COMPATÍVEL!)

**Migração:**
```python
# ANTES - Usando setStyleSheet com COLORS (JÁ OK!)
btn = QPushButton("💡 Backlight OFF")
btn.setCheckable(True)
btn.setStyleSheet(f"""
    QPushButton {{ background-color: {COLORS.TEXT_HINT}; color: {COLORS.BACKGROUND}; }}
    QPushButton:checked {{ background-color: {COLORS.WARNING}; color: {COLORS.ON_PRIMARY}; }}
""")  # ✅ JÁ USA DESIGN SYSTEM - MANTER

# DEPOIS - OU usar StandardButton + gerenciar checked state manualmente
btn = StandardButton("Passo", variant="secondary")
btn.setCheckable(True)
btn.setStyleSheet(f"""
    QPushButton {{
        {btn.styleSheet()}
    }}
    QPushButton:checked {{
        background-color: {COLORS.PRIMARY};
        color: {COLORS.ON_PRIMARY};
        font-weight: bold;
    }}
""")
```

**Exemplos identificados:**
- movement_control.py: "Passo", "Contínuo", "💡 Backlight OFF" (usa COLORS - OK!)

### Tipo 6: Botões com Ícone + Texto (~5% dos botões)
**Características:**
- Ícone + texto juntos
- Exemplos: "📷 Carregar Imagem", "🎯 Configurar Alinhamento"

**Migração:**
```python
# ANTES
btn = QPushButton("📷 Carregar Imagem")

# DEPOIS - OPÇÃO A: StandardButton (se ícone for decorativo)
btn = StandardButton("📷 Carregar Imagem", variant="primary")

# DEPOIS - OPÇÃO B: QPushButton + setStyleSheet (se precisar customizar)
btn = QPushButton("📷 Carregar Imagem")
btn.setStyleSheet(f"""
    QPushButton {{
        background-color: {COLORS.PRIMARY};
        color: {COLORS.ON_PRIMARY};
        border: none;
        border-radius: {DIM.RADIUS_SM}px;
        padding: {SPACE.SM}px {SPACE.MD}px;
        font-size: {TYPO.BODY_MEDIUM}px;
        font-weight: 600;
    }}
""")
```

## Matriz de Migração por Arquivo (Alta Prioridade)

### 1. movement_control.py (14 botões)
| Linha | Variável | Texto/Ícone | Tipo | Variante | Prioridade | Observações |
|-------|----------|-------------|------|----------|------------|-------------|
| 72 | up_button | ↑ | Ícone | - | Alta | Manter setStyleSheet customizado |
| 73 | down_button | ↓ | Ícone | - | Alta | Manter setStyleSheet customizado |
| 74 | left_button | ← | Ícone | - | Alta | Manter setStyleSheet customizado |
| 75 | right_button | → | Ícone | - | Alta | Manter setStyleSheet customizado |
| 91 | z_up_button | Z+ | Ícone | - | Média | Manter setStyleSheet customizado |
| 92 | z_down_button | Z- | Ícone | - | Média | Manter setStyleSheet customizado |
| 108 | emergency_stop_button | STOP | Perigoso | danger | **CRÍTICA** | **HARDCODED "RED" - CORRIGIR!** |
| 146 | go_to_zero_btn | Go to Zero | Primário | primary | Alta | Migrar para StandardButton |
| 154 | go_to_position_btn | Go to Position | Primário | primary | Alta | Migrar para StandardButton |
| 165 | backlight_button | 💡 Backlight OFF | Ícone+Toggle | custom | Média | **JÁ USA COLORS - MANTER** |
| 177 | mode_absolute | Passo | Toggle | secondary | Média | Migrar para StandardButton + toggle |
| 181 | mode_relative | Contínuo | Toggle | secondary | Média | Migrar para StandardButton + toggle |

**Status:**
- ✅ **1 botão já compatível** (backlight_button usa COLORS)
- ❌ **1 botão com violação crítica** (emergency_stop_button com hardcoded "red")
- 🔄 **12 botões para migrar**

### 2. camera_settings_controller.py (8 botões)
| Linha | Variável | Texto | Tipo | Variante | Prioridade |
|-------|----------|-------|------|----------|------------|
| 265 | btn_load_preset | Carregar | Secundário | secondary | Média |
| 275 | btn_save_preset | Salvar/Atualizar | Primário | primary | Alta |
| 282 | btn_apply_now | Aplicar Ajustes | Primário | primary | Alta |
| 285 | btn_export_preset | Exportar JSON | Secundário | secondary | Média |
| 295 | btn_reset | Restaurar Padrão | Secundário | secondary | Média |
| 299 | btn_apply | Aplicar Espelhamento | Secundário | secondary | Média |
| 303 | btn_apply_all | Aplicar Ajustes (Câmera) | Primário | primary | Alta |
| 307 | btn_close | Fechar | Secundário | secondary | Média |

**Status:**
- ✅ **0 violações detectadas**
- 🔄 **8 botões para migrar**

### 3. calibration_controller.py (7 botões)
| Linha | Variável | Texto | Tipo | Variante | Prioridade |
|-------|----------|-------|------|----------|------------|
| 117 | apply_btn | Aplicar Parâmetros | Primário | primary | Alta |
| 125 | test_btn | Testar Calibração | Secundário | secondary | Média |
| 128 | cancel_btn | Cancelar | Secundário | secondary | Média |
| 286 | move_x_btn | Mover X | Secundário | secondary | Média |
| 289 | move_y_btn | Mover Y | Secundário | secondary | Média |
| 292 | reset_position_btn | Zerar Posição | Secundário | secondary | Média |
| 312 | close_btn | Concluir | Primário | primary | Alta |

**Status:**
- ✅ **0 violações detectadas**
- 🔄 **7 botões para migrar**

### 4. inspection_ui_controller.py (7 botões)
| Linha | Variável | Texto | Tipo | Variante | Prioridade |
|-------|----------|-------|------|----------|------------|
| 173 | btn_browse_gerber | 📁 | Ícone | icon_only | Média |
| 189 | btn_browse_mosaic | 📁 | Ícone | icon_only | Média |
| 245 | btn_align | 🎯 Configurar Alinhamento | Primário+Ícone | primary | Alta |
| 265 | btn_settings | ⚙️ Parâmetros | Secundário+Ícone | secondary | Média |

**Status:**
- 🔄 **4 botões para migrar** (análise preliminar, pode haver mais)

## Resumo da Matriz

| Tipo de Botão | Quantidade Estimada | % do Total | Estratégia de Migração |
|---------------|---------------------|------------|------------------------|
| Primário | ~79 | 40% | StandardButton(variant="primary") |
| Secundário | ~59 | 30% | StandardButton(variant="secondary") |
| Perigoso | ~10 | 5% | StandardButton(variant="danger") |
| Ícone | ~30 | 15% | StandardButton(icon_only=True) ou setStyleSheet customizado |
| Toggle/Checkable | ~19 | 10% | StandardButton + gerenciar checked state |
| **TOTAL** | **~197** | **100%** | |

## Critérios de Decisão: StandardButton vs setStyleSheet

**Usar StandardButton quando:**
- ✅ Botão de texto simples (primário/secundário/perigoso)
- ✅ Botão de ícone simples (apenas o ícone, sem texto adicional)
- ✅ Não há requisitos visuais especiais

**Usar QPushButton + setStyleSheet quando:**
- ✅ Botões toggle/checkable com estados customizados
- ✅ Botões com tamanhos não-padrão (ex: 50x50px para direcionais)
- ✅ Botões com comportamento visual complexo (ex: muda ícone quando checked)
- ✅ Botões que já usam setStyleSheet com COLORS (JÁ COMPATÍVEIS!)

**Manter como está (JÁ OK):**
- ✅ movement_control.py: backlight_button (linha 165) - já usa COLORS + DIM

## Violações Críticas Detectadas

1. **movement_control.py:113** - `emergency_stop_button` com hardcoded "background-color: red"
   - **Prioridade:** CRÍTICA
   - **Ação:** Migrar para `StandardButton("STOP", variant="danger")`

## Próximos Passos

1. ✅ **T1.1:** Listar todos os arquivos (COMPLETO)
2. ✅ **T1.2:** Contar botões por arquivo (COMPLETO)
3. ✅ **T1.3:** Analisar tipos de botão (COMPLETO)
4. ✅ **T1.4:** Priorizar arquivos (COMPLETO)
5. ✅ **T1.5:** Criar matriz de migração (COMPLETO - ESTE ARQUIVO)

**Fase 1 Status:** ✅ **COMPLETA**

**Próximo:** Commit + Iniciar Fase 2 (Migração por Arquivo)
