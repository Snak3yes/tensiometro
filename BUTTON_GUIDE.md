# Guia de Padronização de Botões - Inspetor Periférico

**Versão:** 1.0
**Data:** 2026-01-20
**Status:** Proposta para aprovação

## Visão Geral

Este guia define a padronização completa de botões para o sistema de inspeção industrial **Inspetor Periférico**, garantindo consistência visual, hierarquia clara e usabilidade otimizada.

### Princípios de Design

1. **Consistência Visual**: Mesmo estilo para mesma ação em diferentes contextos
2. **Hierarquia Clara**: Tamanho e cor indicam importância da ação
3. **Feedback Imediato**: Hover, pressed e disabled bem definidos
4. **Acessibilidade**: Tamanhos adequados para toque/clique em ambiente industrial
5. **Sobriedade**: Cores e efeitos moderados, adequados para ambiente profissional

---

## Tipos de Botões

### 1. Botões Primários (Primary Buttons)

**Uso:** Ações principais, mais frequentes ou mais importantes do contexto atual.

| Subtipo | Cor | Tamanho Padrão | Quando Usar |
|---------|-----|----------------|-------------|
| **primary-blue** | Azul | Medium (40×24) | Ações padrão, genéricas |
| **primary-green** | Verde | Large (60×40) | Ações de confirmação, início |
| **primary-orange** | Laranja | Large (60×40) | Ações de parada, alerta, atenção |

#### Exemplos de Uso

```python
# ✓ CORRETO - Ação principal do contexto
btn_inspecionar = StyleManager.create_button("Inspecionar", 'primary-blue')

# ✓ CORRETO - Ação de confirmação/início
btn_iniciar = StyleManager.create_button("Iniciar Ciclo", 'primary-green', size='large')

# ✓ CORRETO - Ação de parada
btn_parar = StyleManager.create_button("Parar", 'primary-orange', size='large')

# ✗ ERRADO - Usar primary para ação secundária
btn_cancelar = StyleManager.create_button("Cancelar", 'primary-blue')  # Deveria ser 'secondary'
```

#### Especificação Visual

**primary-blue:**
- Background: Gradiente azul (#2196F3 → #1976D2)
- Texto: Branco
- Borda: 2px solid #1565C0
- Font-size: 10px (Typography.NORMAL)
- Font-weight: 500 (Typography.WEIGHT_MEDIUM)
- Border-radius: 10px
- Hover: Gradiente mais claro (#1E88E5 → #1565C0)
- Disabled: Cinza (#9E9E9E)

**primary-green:**
- Background: Gradiente verde (#4CAF50 → #388E3C)
- Texto: Branco
- Borda: 2px solid #2E7D32
- Font-size: 10px (Typography.NORMAL)
- Font-weight: 500 (Typography.WEIGHT_MEDIUM)
- Border-radius: 10px
- Hover: Gradiente mais claro (#66BB6A → #4CAF50)
- Disabled: Cinza (#9E9E9E)

**primary-orange:**
- Background: Gradiente laranja (#FF9800 → #F57C00)
- Texto: Branco
- Borda: 2px solid #EF6C00
- Font-size: 10px (Typography.NORMAL)
- Font-weight: 500 (Typography.WEIGHT_MEDIUM)
- Border-radius: 10px
- Hover: Gradiente mais claro (#FFB74D → #FF9800)
- Disabled: Cinza (#9E9E9E)

---

### 2. Botão Secundário (Secondary Button)

**Uso:** Ações alternativas, cancelamento, fechamento, ou ações de menor importância.

#### Especificação Visual

- Background: Transparente
- Texto: Azul (#2196F3)
- Borda: 2px solid #2196F3 (outline)
- Font-size: 10px (Typography.NORMAL)
- Font-weight: 500 (Typography.WEIGHT_MEDIUM)
- Border-radius: 5px
- Padding: 8px 16px
- Hover: Background azul claro (#E3F2FD)
- Disabled: Cinza claro, text cinza

#### Exemplos de Uso

```python
# ✓ CORRETO - Ação de cancelamento
btn_cancelar = StyleManager.create_button("Cancelar", 'secondary')

# ✓ CORRETO - Ação de fechamento
btn_fechar = StyleManager.create_button("Fechar", 'secondary')

# ✓ CORRETO - Ação alternativa
btn_outra_opcao = StyleManager.create_button("Voltar", 'secondary')
```

---

### 3. Botão de Emergência (Emergency Button)

**Uso:** Ações críticas de segurança, paradas de emergência física. **MUITO RARO (1% dos casos)**.

#### Especificação Visual

- Background: Gradiente vermelho (#F44336 → #D32F2F)
- Texto: Branco
- Borda: 3px solid #B71C1C (borda mais grossa para destaque)
- Font-size: 12px (Typography.LARGE)
- Font-weight: 700 (Typography.WEIGHT_BOLD)
- Border-radius: 25px (borda mais arredondada)
- Padding: 15px 40px (mais espaçoso)
- Hover: Gradiente mais claro (#EF5350 → #F44336)
- Disabled: Cinza (#9E9E9E)

#### Regras de Uso

**✅ USE 'emergency' PARA:**
- Botão físico de parada de emergência (E-STOP)
- Situações de risco à segurança humana
- Alertas críticos de segurança

**✗ NÃO USE 'emergency' PARA:**
- Botões de "Parar" comuns (ciclos, processos)
- Botões de cancelamento
- Ações reversíveis
- Feedback visual de erro

#### Exemplos de Uso

```python
# ✓ CORRETO - Emergência física real
btn_emergency_stop = StyleManager.create_emergency_button("EMERGENCY STOP")

# ✗ ERRADO - Parar ciclo comum
btn_parar = StyleManager.create_button("Parar", 'emergency')  # Deveria ser 'primary-orange'

# ✗ ERRADO - Cancelar operação
btn_cancelar = StyleManager.create_button("Cancelar", 'emergency')  # Deveria ser 'secondary'
```

---

### 4. Botões Especializados

#### 4.1 Botão JOG (JOG_DIRECTION)

**Uso:** Controles direcionais de movimento manual (X+, Y-, Z+, etc.).

**Especificações:**
- Background: Azul claro (#E3F2FD)
- Borda: 2px solid #90CAF9
- Font-size: 9px (Typography.SMALL)
- Font-weight: 500 (Typography.WEIGHT_MEDIUM)
- Min-width: 50px
- Min-height: 50px
- Border-radius: 8px
- Hover: Azul médio (#BBDEFB)
- Pressed: Azul escuro (#2196F3) com texto branco

**Criação:**
```python
btn_jog = StyleManager.create_jog_button('up', axis='Z')
```

#### 4.2 Botão de Vídeo (VIDEO_BUTTON)

**Uso:** Controle de preview de câmera (iniciar/parar vídeo).

**Especificações:**
- Ativo: Gradiente verde
- Inativo: Cinza escuro
- Font-size: 9px (Typography.SMALL)
- Tamanho: Small (20×20) ou Medium (40×24)

**Criação:**
```python
btn_video = StyleManager.create_video_button(camera_id=1, active=False)
```

#### 4.3 Botão de Calibração (CALIBRATION_BUTTON)

**Uso:** Ações de calibração (CNC, Foco, FOV).

**Especificações:**
- CNC: primary-blue
- Foco: primary-orange
- FOV: primary-green
- Font-size: 10px (Typography.NORMAL)
- Font-weight: 500 (Typography.WEIGHT_MEDIUM)
- Tamanho: Extra-large (100×50)

**Criação:**
```python
btn_calib_cnc = StyleManager.create_calibrated_button("Calibrar CNC", 'cnc')
btn_calib_focus = StyleManager.create_calibrated_button("Calibrar Foco", 'focus')
btn_calib_fov = StyleManager.create_calibrated_button("Calibrar FOV", 'fov')
```

---

## Tamanhos de Botão

### Tabela de Tamanhos (ButtonSizes)

| Tamanho | Largura × Altura | Uso Recomendado |
|---------|------------------|-----------------|
| **small** | 20×20px | Botões de ícone, JOG, toggle |
| **medium** | 40×24px | Botões padrão, mais comum |
| **large** | 60×40px | Botões de ação importante |
| **extra-large** | 100×50px | Botões principais, calibração |

### Guia de Escolha de Tamanho

**Use SMALL (20×20):**
- Botões de ícone (voltar, fechar, expandir)
- Botões JOG direcionais
- Botões em tabelas/listas

**Use MEDIUM (40×24):**
- Botões em formulários
- Botões em barras de ferramentas
- Botões em diálogos modais
- **DEFAULT para a maioria dos casos**

**Use LARGE (60×40):**
- Botões de ação principal em uma seção
- Botões de confirmação importante
- Botões em destaque

**Use EXTRA-LARGE (100×50):**
- Botão principal de uma tela/aba
- Botões de calibração
- Botões de ciclo crítico

---

## Matriz de Decisão

### Quando usar cada tipo de botão?

```
┌─────────────────────────────────────────────────────────────────┐
│ QUAL A IMPORTÂNCIA DA AÇÃO?                                    │
└─────────────────────────────────────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
       CRÍTICA        IMPORTANTE        SECUNDÁRIA
       (Segurança)    (Principal)       (Alternativa)
            │               │               │
            ▼               ▼               ▼
      emergency     primary-color    secondary
                      │
          ┌─────────┼─────────┐
          ▼         ▼         ▼
      Confirma  Inicia   Para/Atenção
        (green)  (blue)     (orange)
```

### Fluxograma de Decisão

```
AÇÃO DO BOTÃO
    │
    ├─ É emergência física de segurança?
    │  └─ SIM → use 'emergency' (extra-large, 12px/bold)
    │
    ├─ É ação principal do contexto atual?
    │  └─ SIM → use 'primary-green' (large, 10px/medium)
    │
    ├─ É ação de início/ativação?
    │  └─ SIM → use 'primary-blue' (medium, 10px/medium)
    │
    ├─ É ação de parada/atenção?
    │  └─ SIM → use 'primary-orange' (large, 10px/medium)
    │
    └─ É ação alternativa/cancelamento?
       └─ SIM → use 'secondary' (medium, 10px/medium)
```

---

## Padrões de Uso por Contexto

### 1. Aba de Inspeção (InspectionTab)

| Botão | Tipo | Tamanho | Justificativa |
|-------|------|---------|---------------|
| **Iniciar Ciclo** | primary-green | extra-large | Ação principal da aba |
| **Parar** | primary-orange | extra-large | Ação de parada (não é emergência física) |
| **Inspecionar** | primary-blue | medium | Ação de início/ativação |

### 2. Aba Hardware Test (HardwareTestTab)

| Botão | Tipo | Tamanho | Justificativa |
|-------|------|---------|---------------|
| **Conectar** | primary-blue | medium | Ação de início/ativação |
| **Desconectar** | secondary | medium | Ação alternativa |
| **Calibrar CNC** | primary-blue (calibrated) | extra-large | Calibração |
| **Calibrar Foco** | primary-orange (calibrated) | extra-large | Calibração |
| **Calibrar FOV** | primary-green (calibrated) | extra-large | Calibração |
| **E-STOP** | emergency | extra-large | Emergência física |

### 3. Diálogos Modais

| Botão | Tipo | Tamanho | Justificativa |
|-------|------|---------|---------------|
| **OK/Salvar** | primary-green | medium | Confirmação |
| **Sim/Confirmar** | primary-blue | medium | Ação principal |
| **Não/Cancelar** | secondary | medium | Ação alternativa |
| **Fechar** | secondary | medium | Ação de fechamento |

### 4. Botões JOG

| Botão | Tipo | Tamanho | Justificativa |
|-------|------|---------|---------------|
| **X+, X-, Y+, Y-, Z+, Z-** | jog | small (50×50) | Controles direcionais |

### 5. Botões de Vídeo

| Botão | Tipo | Tamanho | Justificativa |
|-------|------|---------|---------------|
| **Iniciar Vídeo** | video (active) | medium | Toggle de estado |
| **Parar Vídeo** | video (inactive) | medium | Toggle de estado |

---

## Violações Atuais e Correções Necessárias

### Violação 1: Uso Indevido de 'emergency'

**Arquivo:** `widgets/cycle_monitor_widget.py:339`
```python
# ✗ ATUAL - Violação
StyleManager.apply_button_style(self.btn_parar, 'emergency')

# ✓ CORREÇÃO
StyleManager.apply_button_style(self.btn_parar, 'primary-orange')
```

**Justificativa:** Botão "Parar" de ciclo não é emergência física de segurança.

---

### Violação 2: Uso Indevido de 'emergency'

**Arquivo:** `widgets/camera_preview_widget.py:251`
```python
# ✗ ATUAL - Violação
StyleManager.apply_button_style(self.btn_stop_all, 'emergency')

# ✓ CORREÇÃO
StyleManager.apply_button_style(self.btn_stop_all, 'primary-orange')
```

**Justificativa:** "Parar Todas Câmeras" não é emergência física de segurança.

---

### Violação 3: Falta de Tamanho

**Arquivo:** `widgets/inspection_tab.py:285`
```python
# ✗ ATUAL - Sem tamanho definido
StyleManager.apply_button_style(self.btn_inspect, 'primary-blue')
# Sem setFixedSize()

# ✓ CORREÇÃO
self.btn_inspect = StyleManager.create_button("🔍 Inspecionar", 'primary-blue', size='medium')
# OU
StyleManager.apply_button_style(self.btn_inspect, 'primary-blue')
self.btn_inspect.setFixedSize(*ButtonSizes.MEDIUM)
```

**Justificativa:** Todos os botões devem ter tamanho explícito para consistência.

---

## Implementação

### Padrão Recomendado de Código

```python
# ✓ PADRÃO 1 - Usar create_button() (RECOMENDADO)
btn = StyleManager.create_button(
    text="Salvar",
    button_type='primary-green',
    size='medium'  # 'small', 'medium', 'large', 'extra-large'
)

# ✓ PADRÃO 2 - Usar apply_button_style() + setFixedSize()
btn = QPushButton("Salvar")
StyleManager.apply_button_style(btn, 'primary-green')
btn.setFixedSize(*ButtonSizes.MEDIUM)
btn.clicked.connect(self._on_save)

# ✓ PADRÃO 3 - Usar factory methods especializados
btn_emergency = StyleManager.create_emergency_button("EMERGENCY STOP")
btn_jog = StyleManager.create_jog_button('up', axis='Z')
btn_video = StyleManager.create_video_button(camera_id=1)
btn_calib = StyleManager.create_calibrated_button("Calibrar CNC", 'cnc')
```

### Ordem de Operações

```python
# ✓ ORDEM CORRETA
btn = QPushButton("Texto")              # 1. Criar botão
StyleManager.apply_button_style(btn, 'primary-green')  # 2. Aplicar estilo
btn.setFixedSize(*ButtonSizes.LARGE)    # 3. Definir tamanho
btn.clicked.connect(self._handler)     # 4. Conectar signal
btn.setEnabled(False)                   # 5. Definir estado inicial (opcional)
layout.addWidget(btn)                   # 6. Adicionar ao layout
```

---

## Regras de Ouro

1. **SEMPRE** use `StyleManager` para botões
2. **NUNCA** use `setStyleSheet()` direto em botões
3. **TODOS** os botões devem ter tamanho explícito (via `create_button()` ou `setFixedSize()`)
4. **'emergency'** é apenas para emergências físicas de segurança (1% dos casos)
5. **'primary-green'** é para ações de confirmação/início
6. **'primary-blue'** é para ações padrão/genéricas
7. **'primary-orange'** é para ações de parada/atenção
8. **'secondary'** é para ações alternativas/cancelamento
9. Botões da **MESMA categoria** devem usar o **MESMO tamanho**
10. Botões em **barras/grupos** devem ter **alturas iguais**

---

## Exemplos Práticos

### Exemplo 1: Grupo de Ações Principais

```python
# ✓ CORRETO - Botões principais, mesmo tamanho
group = QGroupBox("Ações Principais")
layout = QHBoxLayout(group)

btn_start = StyleManager.create_button("▶ Iniciar", 'primary-green', size='large')
btn_stop = StyleManager.create_button("⏹ Parar", 'primary-orange', size='large')
btn_inspect = StyleManager.create_button("🔍 Inspecionar", 'primary-blue', size='large')

layout.addWidget(btn_start)
layout.addWidget(btn_stop)
layout.addWidget(btn_inspect)
```

### Exemplo 2: Diálogo Modal

```python
# ✓ CORRETO - Diálogo com botões OK/Cancelar
dialog = QDialog()

btn_ok = StyleManager.create_button("OK", 'primary-green', size='medium')
btn_cancel = StyleManager.create_button("Cancelar", 'secondary', size='medium')

btn_ok.clicked.connect(dialog.accept)
btn_cancel.clicked.connect(dialog.reject)

# Layout
button_layout = QHBoxLayout()
button_layout.addStretch()
button_layout.addWidget(btn_ok)
button_layout.addWidget(btn_cancel)
```

### Exemplo 3: Barra de Ferramentas

```python
# ✓ CORRETO - Barra com botões pequenos/ícones
toolbar = QHBoxLayout()

btn_new = StyleManager.create_button("Novo", 'primary-blue', size='small')
btn_open = StyleManager.create_button("Abrir", 'primary-blue', size='small')
btn_save = StyleManager.create_button("Salvar", 'primary-green', size='small')
btn_delete = StyleManager.create_button("Excluir", 'secondary', size='small')

toolbar.addWidget(btn_new)
toolbar.addWidget(btn_open)
toolbar.addWidget(btn_save)
toolbar.addWidget(btn_delete)
```

---

## Checklist de Validação

Antes de finalizar um botão, verifique:

- [ ] Usa `StyleManager` (nunca `setStyleSheet()` direto)
- [ ] Tipo apropriado para a ação (primary/emergency/secondary)
- [ ] Tamanho explícito definido
- [ ] Cor semântica correta (green=ok, orange=alerta, blue=padrão)
- [ ] Conectado ao handler apropriado
- [ ] Estado inicial correto (enabled/disabled)
- [ ] Tamanho consistente com botões adjacentes
- [ ] Tooltip adicionado (se necessário)
- [ ] Acessível (atalho de teclado se aplicável)

---

## Métricas de Sucesso

- **100%** dos botões usam `StyleManager`
- **0%** uso de `setStyleSheet()` direto em botões
- **100%** dos botões têm tamanho explícito
- **<1%** dos botões usam 'emergency'
- **Zero** botões sem hover definido
- **100%** de consistência visual em grupos de botões

---

## Referências

- `TYPOGRAPHY_GUIDE.md` - Guia de tipografia
- `widgets/style_manager.py` - Implementação de StyleManager
- `widgets/widget_styles.py` - Definições de cores e estilos
- `BUTTON_GUIDE.md` (este documento) - Guia completo de botões

---

**Histórico de Revisões:**

| Versão | Data | Autor | Mudanças |
|--------|------|-------|----------|
| 1.0 | 2026-01-20 | Claude | Criação inicial do guia |
