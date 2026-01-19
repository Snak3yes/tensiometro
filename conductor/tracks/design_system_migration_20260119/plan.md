# Design System Migration - Plano de Implementação

**Track ID:** design_system_migration_20260119
**Data de Criação:** 2026-01-19
**Estimativa:** 4-6 semanas (20-25 horas Fase 1, 15-20 horas Fase 2, 5-10 horas Fase 3)
**Estratégia de Testes**: Test-After Development + Smoke Test Visual

---

## 📊 Visão Geral

Este plano detalha a migração gradual de **70 arquivos** com **2.313 problemas** de estilos inline para o Design System do Tensiometro.

### Estratégia de Migração

**Abordagem**: Incremental, arquivo por arquivo, com validação visual

**Princípios**:
1. ✅ **Zero regressões**: Smoke test após cada arquivo
2. ✅ **Commits pequenos**: 1 commit por arquivo migrado
3. ✅ **Documentação同步**: Atualizar MIGRATION.md a cada fase
4. ✅ **Validação visual**: Comparar antes/depois

### Distribuição por Fase

| Fase | Duração | Arquivos | Problemas | Redução |
|------|---------|----------|-----------|---------|
| **Fase 1** | Semanas 1-2 | 10 críticos | ~398 | 40% |
| **Fase 2** | Semanas 3-4 | 20 prioritários | ~250 | 35% |
| **Fase 3** | Mês 2+ | ~40 restantes | ~578 | 25% |
| **TOTAL** | 4-6 semanas | 70 arquivos | 2.313 | 100% |

---

## 📍 Fase 1: Migração de Arquivos Críticos

**Objetivo:** Migrar os 10 arquivos mais problemáticos (75+ problemas cada)

**Duração:** Semanas 1-2 (10 dias úteis)
**Saídas:**
- 10 arquivos migrados para Design System
- 10 commits individuais + 1 checkpoint
- MIGRATION.md atualizado
- Smoke tests validados

### Status: ⏳ TODO

---

### Tarefa 1.1: Migrar defect_judgment_dialog.py

**Descrição:** Migrar dialog com 75 problemas (45 cores + 29 estilos + 1 QFont)

**Arquivo:** `consumo_lib/dialogs/defect_judgment_dialog.py`

**Problemas identificados:**
- 45 cores hex hardcoded
- 29 blocos setStyleSheet
- 1 QFont manual

**Passos:**
1. Ler arquivo completo
2. Importar Design Tokens:
   ```python
   from consumo_lib.ui import COLORS, TYPO, SPACE, DIM
   ```
3. Substituir cores hex:
   - `#111827` → `COLORS.ON_BACKGROUND`
   - `#6B7280` → `COLORS.ON_SURFACE`
   - `#DBEAFE` → `COLORS.SECONDARY_LIGHT`
   - `#1E40AF` → `COLORS.SECONDARY_DARK`
   - `#E5E7EB` → `COLORS.OUTLINE`
4. Substituir QFont por TYPO.get_font()
5. Refatorar setStyleSheet para usar tokens
6. Executar smoke test: `python main.py`
7. Validar visualmente o dialog
8. Commit: `feat(dialogs): Migrate defect_judgment_dialog to Design System`
9. Atualizar MIGRATION.md

**Critérios de Aceite:**
- [ ] Zero cores hex hardcoded
- [ ] Zero QFont manual
- [ ] Todos os estilos usam Design Tokens
- [ ] Smoke test passando
- [ ] Visual igual ou melhor que antes
- [ ] Commit criado
- [ ] MIGRATION.md atualizado

**Estimativa:** 2-3 horas
**Prioridade:** 🔴 HIGH
**Dependências:** Nenhuma

---

### Tarefa 1.2: Migrar inspection_results_dialog.py

**Descrição:** Migrar dialog com 56 problemas (33 cores + 23 estilos)

**Arquivo:** `consumo_lib/dialogs/inspection_results_dialog.py`

**Passos:** Mesmo padrão da Tarefa 1.1

**Critérios de Aceite:**
- [ ] Zero cores hex hardcoded
- [ ] Todos os estilos usam Design Tokens
- [ ] Smoke test passando
- [ ] Visual validado
- [ ] Commit criado

**Estimativa:** 2 horas
**Prioridade:** 🔴 HIGH
**Dependências:** Tarefa 1.1

---

### Tarefa 1.3: Migrar mode_selection_dialog.py

**Descrição:** Migrar dialog com 51 problemas (35 cores + 12 estilos + 4 fontes)

**Arquivo:** `consumo_lib/dialogs/mode_selection_dialog.py`

**Passos:** Mesmo padrão da Tarefa 1.1

**Critérios de Aceite:**
- [ ] Zero cores hex hardcoded
- [ ] Zero setPointSize hardcoded
- [ ] Todos os estilos usam Design Tokens
- [ ] Smoke test passando
- [ ] Visual validado
- [ ] Commit criado

**Estimativa:** 2 horas
**Prioridade:** 🔴 HIGH
**Dependências:** Tarefa 1.2

---

### Tarefa 1.4: Migrar final_decision_dialog.py

**Descrição:** Migrar dialog com 44 problemas (25 cores + 14 estilos + 3 fontes + 5 tamanhos)

**Arquivo:** `consumo_lib/dialogs/final_decision_dialog.py`

**Passos:** Mesmo padrão da Tarefa 1.1

**Critérios de Aceite:**
- [ ] Zero cores hex hardcoded
- [ ] Zero QFont manual
- [ ] Zero setPointSize hardcoded
- [ ] Todos os estilos usam Design Tokens
- [ ] Smoke test passando
- [ ] Visual validado
- [ ] Commit criado

**Estimativa:** 2.5 horas
**Prioridade:** 🔴 HIGH
**Dependências:** Tarefa 1.3

---

### Tarefa 1.5: Migrar mosaic_capture_widget.py

**Descrição:** Migrar widget com 30 problemas (19 cores + 11 estilos)

**Arquivo:** `consumo_lib/widgets/engenharia/mosaic_capture_widget.py`

**Passos:** Mesmo padrão da Tarefa 1.1

**Critérios de Aceite:**
- [ ] Zero cores hex hardcoded
- [ ] Todos os estilos usam Design Tokens
- [ ] Smoke test passando
- [ ] Visual validado
- [ ] Commit criado

**Estimativa:** 2 horas
**Prioridade:** 🔴 HIGH
**Dependências:** Tarefa 1.4

---

### Tarefa 1.6: Migrar program_data_widget.py

**Descrição:** Migrar widget com 30 problemas (21 cores + 9 estilos)

**Arquivo:** `consumo_lib/widgets/engenharia/program_data_widget.py`

**Passos:** Mesmo padrão da Tarefa 1.1

**Critérios de Aceite:**
- [ ] Zero cores hex hardcoded
- [ ] Todos os estilos usam Design Tokens
- [ ] Smoke test passando
- [ ] Visual validado
- [ ] Commit criado

**Estimativa:** 2 horas
**Prioridade:** 🔴 HIGH
**Dependências:** Tarefa 1.5

---

### Tarefa 1.7: Migrar inspection_windows_widget.py

**Descrição:** Migrar widget com 31 problemas (19 cores + 11 estilos + 1 tamanho)

**Arquivo:** `consumo_lib/widgets/engenharia/inspection_windows_widget.py`

**Passos:** Mesmo padrão da Tarefa 1.1

**Critérios de Aceite:**
- [ ] Zero cores hex hardcoded
- [ ] Zero tamanhos hardcoded
- [ ] Todos os estilos usam Design Tokens
- [ ] Smoke test passando
- [ ] Visual validado
- [ ] Commit criado

**Estimativa:** 2 horas
**Prioridade:** 🔴 HIGH
**Dependências:** Tarefa 1.6

---

### Tarefa 1.8: Migrar alignment_widget.py

**Descrição:** Migrar widget com 35 problemas (25 cores + 10 estilos)

**Arquivo:** `consumo_lib/widgets/engenharia/alignment_widget.py`

**Passos:** Mesmo padrão da Tarefa 1.1

**Critérios de Aceite:**
- [ ] Zero cores hex hardcoded
- [ ] Todos os estilos usam Design Tokens
- [ ] Smoke test passando
- [ ] Visual validado
- [ ] Commit criado

**Estimativa:** 2 horas
**Prioridade:** 🔴 HIGH
**Dependências:** Tarefa 1.7

---

### Tarefa 1.9: Migrar inspection_history_dialog.py

**Descrição:** Migrar dialog com 25 problemas (23 cores + 2 tamanhos)

**Arquivo:** `consumo_lib/dialogs/inspection_history_dialog.py`

**Passos:** Mesmo padrão da Tarefa 1.1

**Critérios de Aceite:**
- [ ] Zero cores hex hardcoded
- [ ] Zero tamanhos hardcoded
- [ ] Todos os estilos usam Design Tokens
- [ ] Smoke test passando
- [ ] Visual validado
- [ ] Commit criado

**Estimativa:** 1.5 horas
**Prioridade:** 🔴 HIGH
**Dependências:** Tarefa 1.8

---

### Tarefa 1.10: Migrar full_history_dialog.py

**Descrição:** Migrar dialog com 21 problemas (todas QColor inline)

**Arquivo:** `consumo_lib/dialogs/stencil/full_history_dialog.py`

**Problema específico:** Cores usadas em `setBackground(QColor("#hex"))`

**Solução:**
```python
# Antes
type_item.setBackground(QColor("#e3f2fd"))

# Depois
from consumo_lib.ui import COLORS
type_item.setBackground(COLORS.to_qcolor(COLORS.SECONDARY_LIGHT))
```

**Critérios de Aceite:**
- [ ] Zero cores hex hardcoded
- [ ] Zero QColor inline
- [ ] Todos os estilos usam Design Tokens
- [ ] Smoke test passando
- [ ] Visual validado
- [ ] Commit criado

**Estimativa:** 1.5 horas
**Prioridade:** 🔴 HIGH
**Dependências:** Tarefa 1.9

---

### Checkpoint 1: Fase 1 Completa

**Descrição:** Validar conclusão da Fase 1 e criar checkpoint

**Atividades:**
1. Executar smoke test completo da aplicação
2. Validar visualmente os 10 dialogs/widgets migrados
3. Atualizar MIGRATION.md com todos os arquivos da Fase 1
4. Criar commit checkpoint: `feat(design-system): Phase 1 complete - 10 critical files migrated`
5. Gerar relatório de progresso
6. Atualizar plan.md marcando Fase 1 como completa

**Critérios de Aceite:**
- [ ] 10/10 arquivos migrados
- [ ] Smoke test completo passando
- [ ] Zero regressões visuais
- [ ] MIGRATION.md atualizado
- [ ] Checkpoint commit criado
- [ ] Fase 1 marcada como completa
- [ ] ~40% dos problemas totais resolvidos

**Estimativa:** 2 horas
**Prioridade:** 🔴 HIGH
**Dependências:** Todas as tarefas da Fase 1

---

## 📍 Fase 2: Migração de Arquivos Prioritários

**Objetivo:** Migrar 20 arquivos com 10-19 problemas cada

**Duração:** Semanas 3-4 (10 dias úteis)
**Saídas:**
- 20 arquivos migrados
- 20 commits + 1 checkpoint
- Padrão de migração refinado
- Documentação consolidada

### Status: ⏳ TODO

---

### Tarefa 2.1: Migrar fiducial_capture_widget.py

**Descrição:** Migrar widget com 20 problemas

**Arquivo:** `consumo_lib/widgets/engenharia/fiducial_capture_widget.py`

**Passos:** Padrão estabelecido na Fase 1

**Estimativa:** 1.5 horas
**Prioridade:** 🟡 MEDIUM
**Dependências:** Checkpoint 1

---

### Tarefa 2.2: Migrar confirm_save_widget.py

**Descrição:** Migrar widget com 15 problemas

**Arquivo:** `consumo_lib/widgets/engenharia/confirm_save_widget.py`

**Passos:** Padrão estabelecido na Fase 1

**Estimativa:** 1 hora
**Prioridade:** 🟡 MEDIUM
**Dependências:** Tarefa 2.1

---

### Tarefa 2.3-2.20: Migrar 18 Arquivos Restantes

**Arquivos-alvo** (em ordem de prioridade):
1. inspection_progress_dialog.py (18 problemas)
2. operator_workflow_dialog.py (14 problemas)
3. confirm_positioning_dialog.py (14 problemas)
4. auth_settings_dialog.py (12 problemas)
5. engineering_wizard_dialog.py (11 problemas)
6. map_settings_dialog.py (12 problemas)
7. recipe_manager_dialog.py (11 problemas)
8. tree_view_tab.py (? problemas)
9. position_list.py (? problemas)
10. position_registry.py (? problemas)
11. tension_viz.py (? problemas)
12. zoomable_image_view.py (? problemas)
13. operator_interface.py (? problemas)
14. hardware_status_bar.py (? problemas)
15. camera_preview.py (? problemas)
16. camera_capture.py (? problemas)
17. image_viewer.py (? problemas)
18. gerber_upload_widget.py (15 problemas)

**Padrão:** Mesmo da Fase 1, mas com velocidade aumentada (aprendizado)

**Estimativa total:** 12-15 horas
**Prioridade:** 🟡 MEDIUM
**Dependências:** Progressivo (cada tarefa depende da anterior)

---

### Checkpoint 2: Fase 2 Completa

**Descrição:** Validar conclusão da Fase 2 e consolidar aprendizado

**Atividades:**
1. Executar smoke test completo
2. Validar visualmente os 20 arquivos migrados
3. Atualizar MIGRATION.md
4. Refinar guia de migração com lições aprendidas
5. Commit checkpoint: `feat(design-system): Phase 2 complete - 20 priority files migrated`
6. Atualizar plan.md

**Critérios de Aceite:**
- [ ] 20/20 arquivos migrados
- [ ] ~75% dos problemas totais resolvidos
- [ ] Guia de migração refinado
- [ ] Checkpoint commit criado
- [ ] Fase 2 marcada como completa

**Estimativa:** 2 horas
**Prioridade:** 🟡 MEDIUM
**Dependências:** Todas as tarefas da Fase 2

---

## 📍 Fase 3: Migração Contínua (Maintenance-Driven)

**Objetivo:** Migrar restante dos arquivos durante manutenção normal

**Duração:** Mês 2+ (spread ao longo do tempo)
**Saídas:**
- ~40 arquivos migrados gradualmente
- Design System 90%+ adotado
- Guia definitivo de migração

### Status: ⏳ TODO

---

### Estratégia Fase 3

**Princípio**: Migrar ao fazer outras modificações

**Quando migrar:**
- Ao corrigir bug no arquivo
- Ao adicionar feature no arquivo
- Durante refatoração
- Ao revisar código legado

**Padrão:**
1. Abrir arquivo para outra tarefa
2. Verificar se tem estilos inline
3. Se sim, migrar antes de fazer outra modificação
4. Commit separado para migração
5. Commit para a tarefa original

**Arquivos restantes (~40):**
- dialogs/restantes/*.py
- widgets/restantes/*.py
- controllers/*.py
- outros/

**Estimativa:** 5-10 horas spread ao longo de 2-3 meses

---

## 📋 Resumo de Métricas

### Estimativa Geral
- **Total de Fases:** 3
- **Total de Arquivos:** 70
- **Total de Problemas:** 2.313
- **Estimativa Total:** 40-55 horas
- **Duração:** 4-6 semanas (Fases 1 e 2) + contínuo (Fase 3)

### Distribuição por Fase
- **Fase 1 (Críticos):** 10 arquivos, ~398 problemas, 20-25 horas
- **Fase 2 (Prioritários):** 20 arquivos, ~250 problemas, 15-20 horas
- **Fase 3 (Contínuo):** ~40 arquivos, ~578 problemas, 5-10 horas

### Critérios de Sucesso da Track

A track será considerada um sucesso quando:

1. ✅ Fase 1 completa (10 arquivos críticos)
2. ✅ Fase 2 completa (20 arquivos prioritários)
3. ✅ Fase 3 em progresso (manutenção contínua)
4. ✅ 75% dos problemas totais resolvidos
5. ✅ Zero regressões visuais
6. ✅ Design System 90%+ adotado

---

## 🎯 Checklists

### Checklist de Migração de Arquivo

- [ ] Ler arquivo completo
- [ ] Importar Design Tokens: `from consumo_lib.ui import COLORS, TYPO, SPACE, DIM`
- [ ] Substituir cores hex por COLORS
- [ ] Substituir QFont por TYPO.get_font()
- [ ] Substituir tamanhos por DIM/SPACE
- [ ] Refatorar setStyleSheet para usar tokens
- [ ] Executar smoke test: `python main.py`
- [ ] Validar visualmente a aplicação
- [ ] Commit: `feat(modulo): Migrate file to Design System`
- [ ] Atualizar MIGRATION.md

### Checklist de Validação Visual

- [ ] Aplicação abre sem erros
- [ ] Cores estão corretas (não muito claras/escuros)
- [ ] Fontes proporcionais (não muito grandes/pequenas)
- [ ] Espaçamentos balanceados (não muito apertado/espaçoso)
- [ ] Elementos alinhados corretamente
- [ ] Estados interativos funcionam (hover, focus)
- [ ] Layout responsivo (redimensionamento)

### Checklist de Final de Fase

- [ ] Todos os arquivos da fase migrados
- [ ] Smoke test completo passando
- [ ] Zero regressões visuais
- [ ] MIGRATION.md atualizado
- [ ] Checkpoint commit criado
- [ ] plan.md marcado como completo
- [ ] Relatório de progresso gerado

---

## 📚 Referências

- **spec.md** - Especificação completa da track
- **docs/design_system/MIGRATION.md** - Guia de migração detalhado
- **docs/design_system/TOKENS.md** - Referência de tokens
- **DESIGN_SYSTEM_AUDIT_REPORT.md** - Relatório de auditoria
- **conductor/archive/design_system_20260119/** - Track de implementação original

---

**Última atualização**: 2026-01-19
**Versão**: 1.0.0
**Próxima atualização**: Ao completar Fase 1
