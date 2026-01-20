# Plano de Implementação: Migrar QPushButton para StandardButton

**Track ID:** `migrate_qpushbutton_to_standardbutton_20260120`
**Estimativa:** 14-22 horas
**Fases:** 4 fases principais

## Visão Geral

Migrar **~197 botões** em todo o códigobase para usar `StandardButton` ou `setStyleSheet()` com tokens do Design System, garantindo consistência visual e aderência ao Material Design 3.

## Fase 1: Análise e Inventário (2-4 horas)

**Objetivo:** Mapear todos os botões e categorizar por tipo.

### Tarefas

- [x] **T1.1:** Listar todos os arquivos com `QPushButton`
  - Busca: `grep -r "= QPushButton(" consumo_lib/ --include="*.py" -l`
  - Saída: Lista de arquivos
  - Estimativa: 30 min
  - **Resultado:** 50 arquivos identificados

- [x] **T1.2:** Contar botões por arquivo
  - Busca: `grep -r "= QPushButton(" arquivo.py -c`
  - Criar planilha com: arquivo, quantidade, tipo estimado
  - Estimativa: 1 hora
  - **Resultado:** 197 botões contabilizados

- [x] **T1.3:** Analisar tipos de botão
  - Categorizar cada botão por:
    - Ação Primária (Salvar, Confirmar, Aplicar)
    - Ação Secundária (Cancelar, Fechar, Voltar)
    - Ação Perigosa (Excluir, Deletar)
    - Ícone/Símbolo (📁, 🎯, etc.)
  - Estimativa: 2 horas
  - **Resultado:** 6 tipos categorizados (Primário, Secundário, Perigoso, Ícone, Toggle, Ícone+Texto)

- [x] **T1.4:** Priorizar arquivos
  - Alto impacto: >5 botões (camera_settings, calibration, etc.)
  - Médio impacto: 2-5 botões
  - Baixo impacto: 1 botão
  - Estimativa: 30 min
  - **Resultado:** 15 arquivos alta prioridade, 33 média, 2 baixa

- [x] **T1.5:** Criar matriz de migração
  - Documentar: arquivo → botão → tipo → variante StandardButton
  - Estimativa: 1 hora
  - **Resultado:** Matriz completa em migration_strategy.md

**Critérios de Sucesso da Fase 1:**
- [x] Lista completa de arquivos com botões (esperado: ~40-50 arquivos)
- [x] Contagem total de botões (esperado: ~197)
- [x] Todos os botões categorizados por tipo
- [x] Matriz de migração criada

**Checkpoint 1:**
- Commit: "docs(conductor): Complete button inventory - 197 QPushButton mapped"

---

## Fase 2: Migração por Arquivo (8-12 horas)

**Objetivo:** Migrar arquivo por arquivo para `StandardButton` ou `setStyleSheet` com Design System.

### Tarefas

#### Lote 1: Controllers (Alta Prioridade)

- [ ] **T2.1:** Migrar `calibration_controller.py`
  - 7 botões identificados
  - Botões a migrar:
    - `apply_btn` → StandardButton("Aplicar Parâmetros", variant="primary")
    - `test_btn` → StandardButton("Testar Calibração")
    - `cancel_btn` → StandardButton("Cancelar")
    - `move_x_btn` → StandardButton("Mover X")
    - `move_y_btn` → StandardButton("Mover Y")
    - `reset_position_btn` → StandardButton("Zerar Posição")
    - `close_btn` → StandardButton("Concluir")
  - Testar funcionalidade
  - Estimativa: 1 hora
  - **Responsável:** Dev

- [ ] **T2.2:** Migrar `camera_settings_controller.py`
  - 10+ botões identificados
  - Botões a migrar:
    - `btn_load_preset` → StandardButton("Carregar")
    - `btn_save_preset` → StandardButton("Salvar/Atualizar", variant="primary")
    - `btn_apply_now` → StandardButton("Aplicar Ajustes")
    - `btn_export_preset` → StandardButton("Exportar JSON")
    - `btn_reset` → StandardButton("Restaurar Padrão")
    - `btn_apply` → StandardButton("Aplicar Espelhamento")
    - `btn_apply_all` → StandardButton("Aplicar Ajustes (Câmera)")
    - `btn_close` → StandardButton("Fechar")
  - Testar funcionalidade
  - Estimativa: 1.5 horas
  - **Responsável:** Dev

- [ ] **T2.3:** Migrar `fiducial_alignment_controller.py`
  - Vários botões identificados
  - Testar funcionalidade
  - Estimativa: 1 hora
  - **Responsável:** Dev

- [ ] **T2.4:** Migrar `inspection_ui_controller.py`
  - Vários botões identificados
  - Testar funcionalidade
  - Estimativa: 1 hora
  - **Responsável:** Dev

#### Lote 2: Dialogs (Média Prioridade)

- [ ] **T2.5 - T2.20:** Migrar dialogs em `consumo_lib/dialogs/`
  - ~40 arquivos de dialogs
  - Cada dialog tipicamente tem 2-5 botões
  - Botões comuns em dialogs:
    - OK/Confirmar → StandardButton("OK", variant="primary")
    - Cancel/Close → StandardButton("Cancelar")
    - Yes/No → StandardButton("Sim"/"Não")
    - Apply → StandardButton("Aplicar", variant="primary")
  - Testar cada dialog após migração
  - Estimativa: 6 horas (18min/dialog)
  - **Responsável:** Dev

#### Lote 3: Widgets e Outros (Baixa Prioridade)

- [ ] **T2.21 - T2.30:** Migrar widgets e outros arquivos
  - Arquivos restantes com 1-3 botões
  - Estimativa: 2 horas
  - **Responsável:** Dev

**Critérios de Sucesso da Fase 2:**
- [ ] Todos os 197 botões migrados
- [ ] 100% dos botões usam StandardButton ou setStyleSheet com Design System
- [ ] Zero hardcoded colors
- [ ] Zero hardcoded sizes
- [ ] Todos os testes passando
- [ ] Validação visual aprovada

**Checkpoint 2:**
- Commit: "refactor(ui): Migrate buttons to StandardButton - Phase 2 complete (197 buttons)"

---

## Fase 3: Validação e Testes (4-6 horas)

**Objetivo:** Garantir que migração está correta e funcional.

### Tarefas

- [ ] **T3.1:** Testes Automatizados
  - Testar que todos os botões criados podem ser instanciados
  - Testar que botões aceitam clique
  - Testar que botões respondem a enabled/disabled
  - Estimativa: 2 horas

- [ ] **T3.2:** Validação Visual
  - Abrir aplicação principal
  - Navegar por todas as janelas/dialogs
  - Verificar aparência dos botões
  - Verificar consistência de cores
  - Verificar hover states
  - Estimativa: 2 horas

- [ ] **T3.3:** Testes de Integração
  - Testar fluxos completos que usam botões
  - Ex: Engenharia Wizard (7 abas, ~30 botões)
  - Ex: Diálogo de Calibração
  - Ex: Diálogo de Configurações de Câmera
  - Estimativa: 2 horas

- [ ] **T3.4:** Correção de Problemas
  - Corrigir qualquer problema encontrado
  - Re-testar após correções
  - Estimativa: 1-2 horas

**Critérios de Sucesso da Fase 3:**
- [ ] 100% dos testes automatizados passando
- [ ] Validação visual aprovada
- [ ] Zero bugs reportados
- [ ] Performance mantida

**Checkpoint 3:**
- Commit: "test(ui): Add button validation tests - 100% passing"

---

## Fase 4: Limpeza e Documentação (1-2 horas)

**Objetivo:** Finalizar migração com código limpo e documentado.

### Tarefas

- [ ] **T4.1:** Remover imports não utilizados
  - Buscar: `from PyQt6.QtGui import QFont`
  - Remover se não usado após migração
  - Estimativa: 30 min

- [ ] **T4.2:** Atualizar documentação
  - Atualizar guias de uso de StandardButton
  - Adicionar exemplos nos docs
  - Estimativa: 30 min

- [ ] **T4.3:** Validação Final
  - Verificar zero hardcodeds remanescentes
  - Verificar todos os botões usam Design System
  - Teste final da aplicação
  - Estimativa: 1 hora

**Critérios de Sucesso da Fase 4:**
- [ ] Nenhum import não utilizado
- [ ] Documentação atualizada
- [ ] Validação final aprovada
- [ ] Zero problemas pendentes

**Checkpoint 4:**
- Commit: "refactor(ui): Complete QPushButton to StandardButton migration - 197 buttons migrated"

---

## Detalhes de Implementação

### Padrão de Migração por Tipo de Botão

#### Botão Primário (Ação principal)
```python
# ANTES
button = QPushButton("Salvar")
button.clicked.connect(self.save)

# DEPOIS
from consumo_lib.ui.widget_standards import StandardButton
button = StandardButton("Salvar", variant="primary")
button.clicked.connect(self.save)
```

#### Botão Secundário (Cancelar, Fechar)
```python
# ANTES
button = QPushButton("Cancelar")
button.clicked.connect(self.cancel)

# DEPOIS
button = StandardButton("Cancelar", variant="secondary")
button.clicked.connect(self.cancel)
```

#### Botão Perigoso (Excluir, Deletar)
```python
# ANTES
button = QPushButton("Excluir")
button.setStyleSheet("background-color: #F44336; color: white;")
button.clicked.connect(self.delete)

# DEPOIS
button = StandardButton("Excluir", variant="danger")
button.clicked.connect(self.delete)
```

#### Botão Outline (Borda colorida, fundo transparente)
```python
# ANTES
button = QPushButton("Cancelar")
button.setStyleSheet("border: 2px solid #4CAF50; color: #4CAF50;")

# DEPOIS
button = StandardButton("Cancelar", variant="outline")
```

#### Botão com Ícone
```python
# ANTES
button = QPushButton("📁")
button.setToolTip("Abrir arquivo")

# DEPOIS
button = StandardButton("📁", icon_only=True)
button.setToolTip("Abrir arquivo")
```

#### Botão com setStyleSheet (casos especiais)
```python
# Quando StandardButton não se aplica (ex: botão customizado complexo)
from consumo_lib.ui import COLORS, TYPO, SPACE, DIM

button.setStyleSheet(f"""
    QPushButton {{
        background-color: {COLORS.PRIMARY};
        color: {COLORS.ON_PRIMARY};
        border: none;
        border-radius: {DIM.RADIUS_SM}px;
        padding: {SPACE.SM}px {SPACE.MD}px;
        font-size: {TYPO.BODY_LARGE}px;
        font-weight: bold;
        min-height: {DIM.BUTTON_HEIGHT_MD}px;
    }}
    QPushButton:hover {{
        background-color: {COLORS.PRIMARY_DARK};
    }}
""")
```

### Arquivos de Prioridade Alta

#### 1. calibration_controller.py
**Localização:** `consumo_lib/controllers/calibration_controller.py`

**Botões (7):**
- Linha ~117: `apply_btn = QPushButton("Aplicar Parâmetros")`
- Linha ~125: `test_btn = QPushButton("Testar Calibração")`
- Linha ~128: `cancel_btn = QPushButton("Cancelar")`
- Linha ~286: `move_x_btn = QPushButton("Mover X")`
- Linha ~289: `move_y_btn = QPushButton("Mover Y")`
- Line ~292: `reset_position_btn = QPushButton("Zerar Posição")`
- Line ~312: `close_btn = QPushButton("Concluir")`

**Migração:**
```python
# Adicionar import
from consumo_lib.ui.widget_standards import StandardButton

# Substituir
apply_btn = StandardButton("Aplicar Parâmetros", variant="primary")
test_btn = StandardButton("Testar Calibração")
cancel_btn = StandardButton("Cancelar")
move_x_btn = StandardButton("Mover X")
move_y_btn = StandardButton("Mover Y")
reset_position_btn = StandardButton("Zerar Posição")
close_btn = StandardButton("Concluir", variant="primary")
```

#### 2. camera_settings_controller.py
**Localização:** `consumo_lib/controllers/camera_settings_controller.py`

**Botões (10+):**
- Linha ~265: `btn_load_preset = QPushButton("Carregar")`
- Linha ~275: `btn_save_preset = QPushButton("Salvar/Atualizar")`
- Linha ~282: `btn_apply_now = QPushButton("Aplicar Ajustes")`
- Linha ~285: `btn_export_preset = QPushButton("Exportar JSON")`
- Linha ~295: `btn_reset = QPushButton("Restaurar Padrão")`
- Linha ~299: `btn_apply = QPushButton("Aplicar Espelhamento")`
- Linha ~303: `btn_apply_all = QPushButton("Aplicar Ajustes (Câmera)")`
- Linha ~307: `btn_close = QPushButton("Fechar")`

**Migração:**
```python
btn_load_preset = StandardButton("Carregar")
btn_save_preset = StandardButton("Salvar/Atualizar", variant="primary")
btn_apply_now = StandardButton("Aplicar Ajustes", variant="primary")
btn_export_preset = StandardButton("Exportar JSON")
btn_reset = StandardButton("Restaurar Padrão")
btn_apply = StandardButton("Aplicar Espelhamento")
btn_apply_all = StandardButton("Aplicar Ajustes (Câmera)", variant="primary")
btn_close = StandardButton("Fechar")
```

#### 3. fiducial_alignment_controller.py
**Localização:** `consumo_lib/controllers/fiducial_alignment_controller.py`

**Botões principais:**
- Linha ~113: `btn_load_image = QPushButton("📷 Carregar Imagem/Mosaico")`
- Linha ~???: Botão de configurar alinhamento
- Linha ~???: Botões de ação

**Migração:**
```python
btn_load_image = StandardButton("📷 Carregar Imagem/Mosaico")
# Outros botões seguem padrão similar
```

#### 4. inspection_ui_controller.py
**Localização:** `consumo_lib/controllers/inspection_ui_controller.py`

**Botões principais:**
- Linha ~173: `btn_browse_gerber = QPushButton("📁")`
- Linha ~189: `btn_browse_mosaic = QPushButton("📁")`
- Linha ~245: `btn_align = QPushButton("🎯 Configurar Alinhamento de Fiduciais...")`
- Linha ~265: `btn_settings = QPushButton("⚙️ Parâmetros")`

**Migração:**
```python
btn_browse_gerber = StandardButton("📁", icon_only=True)
btn_browse_mosaic = StandardButton("📁", icon_only=True)
btn_align = StandardButton("🎯 Configurar Alinhamento", variant="primary")
btn_settings = StandardButton("⚙️ Parâmetros")
```

---

## Estratégia de Testes

### Testes Unitários

Para cada arquivo migrado, testar:

```python
def test_button_creation():
    """Testa que botão pode ser criado sem erros"""
    widget = MyWidget()
    widget.setup_ui()

    # Verificar que botão existe
    assert hasattr(widget, 'save_button')
    assert isinstance(widget.save_button, (QPushButton, StandardButton))

    # Verificar que botão aceita clique
    widget.save_button.click()
    # Verificar resultado esperado

def test_button_styling():
    """Testa que botão usa Design System"""
    widget = MyWidget()
    widget.setup_ui()

    # Verificar stylesheet usa COLORS
    stylesheet = widget.save_button.styleSheet()
    assert 'COLORS.PRIMARY' in stylesheet or 'StandardButton' in str(type(widget.save_button))
```

### Testes Visuais

- [ ] Criar script de screenshots
- [ ] Capturar tela de cada dialog/janela
- ] ] Comparar antes/depois para garantir consistência
- [ ] Verificar hover states funcionam

### Testes de Integração

Fluxos importantes para testar:
1. Engenharia Wizard (7 abas, ~30 botões)
2. Diálogo de Calibração
3. Diálogo de Configurações de Câmera
4. Diálogo de Autenticação
5. Diálogo de Tema

---

## Matriz de Migração (Resumo)

| Arquivo | Botões | Variante Padrão | Prioridade | Estimativa |
|--------|--------|----------------|------------|------------|
| calibration_controller.py | 7 | primary/secondary | Alta | 1h |
| camera_settings_controller.py | 10 | primary/secondary | Alta | 1.5h |
| fiducial_alignment_controller.py | 5+ | primary/secondary | Alta | 1h |
| inspection_ui_controller.py | 4+ | primary/secondary/icon | Alta | 1h |
| dialogs/* (40 arquivos) | ~80 | various | Média | 6h |
| widgets/* (30 arquivos) | ~90 | various | Média | 4h |
| controllers/* (restantes) | ~1 | various | Baixa | 2h |
| **TOTAL** | **~197** | | | **~14h** |

---

## Conclusão

Esta migration garante consistência visual completa em todos os botões da aplicação, seguindo Material Design 3 e aproveitando os tokens do Design System.

**Benefícios:**
- ✅ Consistência visual em 197 botões
- ✅ Manutenção simplificada (mudar cor em um lugar = muda em todos)
- ✅ Aderência ao Material Design 3
- ✅ Código mais limpo e semântico
- ✅ Melhor experiência do usuário

**Riscos Mitigados:**
- ✅ Testes abrangentes previnem quebras
- ✅ Migração em lotes facilita rollback
- ✅ Validação visual garante qualidade
