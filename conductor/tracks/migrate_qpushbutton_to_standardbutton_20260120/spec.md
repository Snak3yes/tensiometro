# Especificação: Migrar QPushButton para StandardButton

**Track ID:** `migrate_qpushbutton_to_standardbutton_20260120`
**Tipo:** Refatoração
**Prioridade:** Alta (Alto impacto - consistência visual em 197 botões)
**Data de Criação:** 2026-01-20

## Objetivo

Migrar todos os botões do projeto (aproximadamente 197 instâncias de `QPushButton`) para usar o componente `StandardButton` do Design System ou, quando não for apropriado, usar `setStyleSheet()` com tokens do Design System (`COLORS`, `TYPO`, `DIM`).

## Contexto

### Problema Atual

O projeto tem **~197 botões** criados como `QPushButton` que usam a aparência padrão do Qt. Embora funcionais, esses botões:

- ❌ Não usam `StandardButton` do Design System
- ❌ Não usam cores do sistema `COLORS` (PRIMARY, SECONDARY, ERROR, etc.)
- ❌ Não usam tamanhos do sistema `DIM` (BUTTON_HEIGHT_MD, etc.)
- ❌ Não têm consistência visual
- ❌ Não seguem Material Design 3

### Estado Atual

```
Total de QPushButton: ~197
Usam StandardButton: 0 (0%)
Usam COLORS tokens: 0 (0%)
Aparência padrão do Qt: ~197 (100%)
Violações críticas: 0
```

### Estado Desejado

```
Todos os botões devem usar:
✅ StandardButton ou
✅ setStyleSheet() com COLORS/DIM tokens

Consistência visual: 100%
Aderência ao Design System: 100%
```

## Requisitos Funcionais

### RF-001: Identificar Todos os Botões
- **Descrição:** Listar todos os arquivos que contêm criação de `QPushButton`
- **Prioridade:** Alta
- **Aceitação:** Lista completa de arquivos com contagem de botões

### RF-002: Categorizar Botões por Tipo
- **Descrição:** Categorizar botões em:
  - **Ação Primária:** Botões principais (Salvar, Confirmar, Aplicar)
  - **Ação Secundária:** Botões secundários (Cancelar, Fechar, Voltar)
  - **Ação Perigosa:** Botões destrutivos (Excluir, Deletar, Remover)
  - **Ação de Navegação:** Botões de navegação (Próximo, Anterior, Voltar)
  - **Botões de Ícone:** Botões com apenas ícone/símbolo
- **Prioridade:** Alta
- **Aceitação:** Todos os 197 botões categorizados

### RF-003: Migrar para StandardButton
- **Descrição:** Substituir `QPushButton` por `StandardButton` onde apropriado
- **Prioridade:** Alta
- **Critérios:**
  - Botões com texto apenas → `StandardButton(text="Texto")`
  - Botões primários → `StandardButton(text="Texto", variant="primary")`
  - Botões secundários → `StandardButton(text="Texto", variant="secondary")`
  - Botões perigosos → `StandardButton(text="Texto", variant="danger")`
  - Botões outline → `StandardButton(text="Texto", variant="outline")`
- **Aceitação:** Todos os botões migrados para StandardButton

### RF-004: Migrar para setStyleSheet com Design System
- **Descrição:** Para botões onde `StandardButton` não é apropriado, usar `setStyleSheet()` com tokens
- **Prioridade:** Média
- **Critérios:**
  - Usar `COLORS.PRIMARY` para cor principal
  - Usar `COLORS.SECONDARY` para cor secundária
  - Usar `COLORS.ERROR` para botões de erro/perigo
  - Usar `COLORS.TEXT_PRIMARY` para cor do texto
  - Usar `DIM.BUTTON_HEIGHT_MD` para altura
  - Usar `DIM.RADIUS_SM` para border-radius
- **Aceitação:** Botões estilizados com tokens do Design System

### RF-005: Remover Hardcodeds
- **Descrição:** Remover todas as cores e tamanhos hardcoded
- **Prioridade:** Alta
- **Critérios:**
  - Zero ocorrências de `background-color: #XXXXXX`
  - Zero ocorrências de `setMinimumHeight(40)` (usar `DIM.BUTTON_HEIGHT_MD`)
  - Zero ocorrências de `setFixedSize(120, 40)`
- **Aceitação:** Nenhum hardcoded remanescente

## Requisitos Não-Funcionais

### RNF-001: Consistência Visual
- **Descrição:** Todos os botões devem ter aparência consistente
- **Prioridade:** Alta
- **Métrica:** Homogeneidade visual entre botões do mesmo tipo

### RNF-002: Aderência ao Material Design 3
- **Descrição:** Botões devem seguir especificações do Material Design 3
- **Prioridade:** Média
- **Referência:** https://m3.material.io/components/buttons/

### RNF-003: Manter Funcionalidade
- **Descrição:** Migração não deve quebrar funcionalidade existente
- **Prioridade:** Crítica
- **Métrica:** 100% dos botões funcionando como antes

### RNF-004: Performance
- **Descrição:** Performance não deve degradar
- **Prioridade:** Média
- **Métrica:** Tempo de resposta inalterado

## Arquivos Principais

### Alto Impacto (> 5 botões)

1. **`consumo_lib/controllers/calibration_controller.py`** (~7 botões)
   - `apply_btn`, `test_btn`, `cancel_btn`
   - `move_x_btn`, `move_y_btn`, `reset_position_btn`, `close_btn`

2. **`consumo_lib/controllers/camera_settings_controller.py`** (~10 botões)
   - `btn_load_preset`, `btn_save_preset`, `btn_apply_now`
   - `btn_export_preset`, `btn_reset`, `btn_apply`, `btn_apply_all`, `btn_close`

3. **`consumo_lib/controllers/fiducial_alignment_controller.py`** (vários botões)
   - Botões de carregar imagem, configurar alinhamento, etc.

4. **`consumo_lib/controllers/inspection_ui_controller.py`** (vários botões)
   - Botões de navegação, configuração, etc.

### Outros Arquivos

- Dialogs em `consumo_lib/dialogs/` (~40+ arquivos)
- Widgets em `consumo_lib/widgets/` (~30+ arquivos)
- Controllers em `consumo_lib/controllers/` (~10+ arquivos)

## Critérios de Sucesso

### Geral
- [ ] Todos os 197 botões migrados para StandardButton ou estilizados com Design System
- [ ] Zero hardcoded colors em botões
- [ ] Zero hardcoded sizes em botões
- [ ] Consistência visual em toda aplicação
- [ ] 100% dos testes passando
- [ ] Zero warnings de execução

### Específico
- [ ] `StandardButton` importado e usado em todos os lugares apropriados
- [ ] Tokens `COLORS.*` usados em todos os setStyleSheet()
- [ ] Tokens `DIM.*` usados para tamanhos de botões
- [ ] Nenhum botão com `QFont` direto
- [ ] Nenhum botão com `background-color: #XXXXXX` hardcoded

## Dependências

- `consumo_lib/ui/widget_standards.py` - `StandardButton`
- `consumo_lib/ui/design_tokens.py` - `COLORS`, `TYPO`, `DIM`

## Riscos

### Risco 1: Quebra de Funcionalidade
- **Probabilidade:** Baixa
- **Impacto:** Alto
- **Mitigação:** Testes abrangentes após cada arquivo migrado

### Risco 2: Regressão Visual
- **Probabilidade:** Média
- **Impacto:** Médio
- **Mitigação:** Validação visual em ambiente de teste

### Risco 3: Performance
- **Probabilidade:** Baixa
- **Impacto:** Baixo
- **Mitigação:** Benchmarks antes/depois

## Notas de Implementação

### Abordagem Sugerida

1. **Fase 1:** Análise e Planejamento
   - Listar todos os arquivos com botões
   - Categorizar botões por tipo
   - Criar matriz de migração

2. **Fase 2:** Migração em Lotes
   - Migrar arquivo por arquivo
   - Testar após cada migração
   - Commit em checkpoints

3. **Fase 3:** Validação
   - Validação visual completa
   - Testes automatizados
   - Correção de problemas

4. **Fase 4:** Limpeza
   - Remover imports não utilizados (QFont se aplicável)
   - Atualizar documentação
   - Commit final

### Padrões de Migração

**Botão Primário Padrão:**
```python
# ANTES
btn = QPushButton("Salvar")

# DEPOIS
from consumo_lib.ui.widget_standards import StandardButton
btn = StandardButton("Salvar", variant="primary")
```

**Botão com Ação Perigosa:**
```python
# ANTES
btn = QPushButton("Excluir")

# DEPOIS
btn = StandardButton("Excluir", variant="danger")
```

**Botão com Ícone:**
```python
# ANTES
btn = QPushButton("📁")

# DEPOIS
btn = StandardButton("📁", icon_only=True)
```

**Botão em setStyleSheet (quando StandardButton não se aplica):**
```python
# ANTES
btn = QPushButton("Cancelar")
btn.setStyleSheet("background-color: #2196F3; color: white;")

# DEPOIS
from consumo_lib.ui import COLORS, DIM
btn.setStyleSheet(f"""
    QPushButton {{
        background-color: {COLORS.SECONDARY};
        color: {COLORS.ON_SECONDARY};
        border-radius: {DIM.RADIUS_SM}px;
        padding: {SPACE.SM}px {SPACE.MD}px;
        min-height: {DIM.BUTTON_HEIGHT_MD}px;
    }}
""")
```

## Exemplos de Uso

### Exemplo 1: Botão Simples
```python
# ANTES
save_button = QPushButton("Salvar")
layout.addWidget(save_button)

# DEPOIS
from consumo_lib.ui.widget_standards import StandardButton
save_button = StandardButton("Salvar", variant="primary")
layout.addWidget(save_button)
```

### Exemplo 2: Botão com Callback
```python
# ANTES
button = QPushButton("Fechar")
button.clicked.connect(self.close)

# DEPOIS
button = StandardButton("Fechar")
button.clicked.connect(self.close)
```

### Exemplo 3: Botão com Estado
```python
# ANTES
self.delete_button = QPushButton("Excluir")
self.delete_button.setEnabled(False)

# DEPOIS
self.delete_button = StandardButton("Excluir", variant="danger")
self.delete_button.setEnabled(False)
```

## Testes

### Testes Automatizados
- Verificar que todos os botões existem
- Verificar que todos usam Design System
- Verificar que não há hardcodeds

### Testes Manuais
- Abrir aplicação e verificar aparência dos botões
- Verificar consistência visual entre botões
- Verificar hover states funcionam

## Timeline Estimada

- **Análise:** 2-4 horas
- **Migração:** 8-12 horas (197 botões / ~15-20 botões/hora)
- **Testes:** 4-6 horas
- **Total:** 14-22 horas

## Referências

- `consumo_lib/ui/widget_standards.py` - Implementação de StandardButton
- `consumo_lib/ui/design_tokens.py` - Tokens do Design System
- `docs/design_system/COMPONENTS.md` - Documentação de componentes
- Material Design 3 Button specifications
