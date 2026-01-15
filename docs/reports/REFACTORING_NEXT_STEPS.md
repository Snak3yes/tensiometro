# Próximos Passos de Refatoração - Análise 2026-01-15

## Status Atual

✅ **FASE 4 CONCLUÍDA:** Refatoração do mainwindow.py do gerber_core
- Redução de 1.421 → 735 linhas (-48.3%)
- 3 módulos extraídos: ObjectEditor, GerberFileManager, WidthHeightDialog
- Sintaxe validada, imports corrigidos

## Análise de Arquivos Grandes (>500 linhas)

### 🔴 **CRÍTICO** - Validar Refatoração Atual

**Prioridade 1 - URGENTE**
- [ ] Testar todas as funcionalidades do gerber_core/gui/mainwindow.py
- [ ] Garantir que não há regressões
- [ ] Documentar bugs encontrados

**Rationale:** Não podemos prosseguir sem validar o que já foi feito.

---

### 🟡 **ALTA PRIORIDADE** - Limpeza de Arquivos Legacy

#### 1. `aoi_lib/stencil_tension_old.py` (1.409 linhas)
**Status:** ARQUIVO LEGACY (deve ser removido/movido para archive/)

**Ação:**
```bash
# Verificar se ainda é usado
grep -r "stencil_tension_old" --include="*.py" .
# Se não for usado, mover para archive
mv aoi_lib/stencil_tension_old.py archive/
```

**Benefício:** Limpeza imediata de 1.409 linhas de código obsoleto.

---

#### 2. `aoi_lib/recipe_dialog.py` (880 linhas) vs `consumo_lib/dialogs/recipe_dialogs.py` (881 linhas)
**Status:** POSSÍVEL DUPLICATA

**Ação:**
- Verificar se `aoi_lib/recipe_dialog.py` é um legacy
- Comparar com `consumo_lib/dialogs/recipe_dialogs.py`
- Remover ou arquivar duplicata

**Benefício:** Eliminar confusão entre dois arquivos similares.

---

### 🟢 **MÉDIA PRIORIDADE** - Análise de Novos Alvos

#### 3. `aoi_lib/report_generator.py` (1.366 linhas)
**Análise Preliminar Necessária:**
- Responsabilidades atuais?
- Pode ser dividido em geradores específicos (PDF, HTML, gráficos)?
- Vocabulário de template pode ser extraído?

**Potencial:** 400-600 linhas podem ser extraídas.

---

#### 4. `aoi_lib/fiducial_alignment_widget.py` (959 linhas)
**Análise:** Pode ter responsabilidades de UI + lógica de alinhamento misturadas.

**Potencial Extração:**
- TemplateMatcherService (lógica de matching)
- AlignmentCalculator (cálculo de transformações)
- FiducialCaptureUI (apenas UI)

---

#### 5. `consumo_lib/widgets/engenharia/alignment_widget.py` (1.019 linhas)
**Status:** JÁ ANALISADO NO PHASE 3 - track: solid_refactoring_phase3

**Verificar:**
- Se a refatoração proposta foi implementada
- Se ainda há work pendente deste track

---

#### 6. `consumo_lib/dialogs/defect_judgment_dialog.py` (848 linhas)
**Análise:** Diálogo complexo para classificação de defeitos.

**Potencial Extração:**
- DefectClassifier (serviço de classificação)
- ImageAnnotationService (serviço de anotação)
- DefectJudgmentUI (apenas UI)

---

#### 7. `aoi_lib/stencil_tracker.py` (848 linhas)
**Análise:** Gerenciamento de dados de stencils (JSON + SQLite).

**Potencial Refatoração:**
- Separar camada de persistência (Repository Pattern)
- StencilRepository (interface)
- JSONStencilRepository (implementação)
- SQLiteStencilRepository (implementação)

**Benefício:** Facilitar migração completa para SQLite.

---

#### 8. `aoi_lib/stencil_inspection.py` (784 linhas)
**Análise:** Motor de inspeção visual com thresholds.

**Potencial Extração:**
- ImageAnalyzer (análise de imagem)
- AreaCalculator (cálculo de áreas)
- InspectionClassifier (classificação OK/PARTIAL/BLOCKED)

---

### 🔵 **BAIXA PRIORIDADE** - Widgets de Engenharia

#### 9. Widgets do Engineering Wizard (>600 linhas cada)
- `fiducial_capture_widget.py` (696 linhas)
- `mosaic_capture_widget.py` (790 linhas)
- `inspection_windows_widget.py` (886 linhas)

**Status:** Estes widgets já foram recentemente implementados (Phase 3).

**Recomendação:** Aguardar validação prática antes de refatorar.

---

## Plano de Ação - FASE 5

### Semana 1: Validação e Limpeza

**Dia 1-2: Validação da FASE 4**
- [ ] Testes manuais completos do gerber_core
- [ ] Correção de bugs encontrados
- [ ] Documentação de regressões

**Dia 3-4: Limpeza de Legacy**
- [ ] Remover/arquivar `stencil_tension_old.py`
- [ ] Resolver duplicata `recipe_dialog.py` vs `recipe_dialogs.py`
- [ ] Limpeza de arquivos backup antigos

**Dia 5: Planejamento FASE 5**
- [ ] Escolher próximo alvo (report_generator ou fiducial_alignment)
- [ ] Criar track no conductor
- [ ] Escrever spec.md e plan.md

---

### Semana 2-3: Refatoração do Próximo Alvo

**Opção A: `aoi_lib/report_generator.py` (1.366 linhas)**
- Benefício imediato: Mais fácil manutenção de relatórios
- Complexidade: Média (dependências: reportlab, matplotlib)

**Opção B: `aoi_lib/fiducial_alignment_widget.py` (959 linhas)**
- Benefício imediato: Separação UI/lógica de alinhamento
- Complexidade: Média (OpenCV, cálculos geométricos)

---

## Critérios de Priorização

### Alta Prioridade (Fazer agora)
1. ✅ Validação da refatoração atual
2. ✅ Limpeza de código legacy
3. ✅ Arquivos com bugs conhecidos

### Média Prioridade (Fazer em seguida)
1. 📊 Arquivos críticos de negócio >800 linhas
2. 📊 Arquivos com alta taxa de modificação
3. 📊 Arquivos com múltiplas responsabilidades claras

### Baixa Prioridade (Deixar para depois)
1. 🔵 Código recentemente implementado (<3 meses)
2. 🔵 Código estável sem bugs
3. 🔵 Widgets com responsabilidade única apesar do tamanho

---

## Recomendação Final

**Fase Imediata (Próximos 2 dias):**
1. Validar completamente a FASE 4 (mainwindow.py refatorado)
2. Executar testes manuais das funcionalidades do gerber viewer
3. Limpar código legacy (`stencil_tension_old.py`, duplicatas de recipe)

**Fase Seguinte (Próximas 2 semanas):**
- Escolher UM alvo: `report_generator.py` OU `fiducial_alignment_widget.py`
- Criar track no conductor com spec/plan detalhados
- Executar refatoração seguindo SOLID principles

**Fase Futura (Após validação prática):**
- Avaliar widgets do Engineering Wizard
- Refatorar `stencil_tracker.py` (se migração SQLite for prioridade)
- Refatorar diálogos complexos (defect_judgment)

---

## Conclusão

**O que fazer AGORA:**
1. ✅ Validar FASE 4 (mainwindow.py)
2. ✅ Limpar legacy code
3. ✅ Planejar FASE 5

**O que fazer DEPOIS:**
- Escolher próximo alvo baseado em prioridade de negócio
- Seguir padrão estabelecido na FASE 4
- Documentar tudo com reports e testes

---

**Relatório gerado:** 2026-01-15
**Próxima revisão:** Após validação completa da FASE 4
