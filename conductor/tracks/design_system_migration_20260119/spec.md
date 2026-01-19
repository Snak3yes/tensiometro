# Design System Migration - Especificação

**Track ID:** design_system_migration_20260119
**Data de Criação:** 2026-01-19
**Tipo:** Refatoração
**Prioridade:** 🔴 ALTA
**Estimativa:** 4-6 semanas

---

## Contexto

O Tensiometro possui um Design System robusto (v1.0) implementado, porém com adoção muito baixa (~1.6% dos arquivos). A auditoria completa identificou **2.313 problemas** de estilos inline distribuídos em aproximadamente **70 arquivos**.

### Situação Atual

- ✅ **Design System implementado**: 9 tokens, 7 componentes base, stylesheet global
- ⚠️ **Adoção parcial**: Apenas 2 arquivos migrados (status_badge.py, movement_control.py)
- ❌ **Débito técnico significativo**: 460 cores hex, 200 setStyleSheet, 20 QFont manual

---

## Problema

**Inconsistência Visual e Dificuldade de Manutenção**

1. **Cores hardcoded**: 460 ocorrências em 44 arquivos
2. **Estilos inline**: 200 blocos setStyleSheet com valores hardcoded
3. **Fontes manuais**: 20 QFont() criados manualmente
4. **Tamanhos hardcoded**: 40 setMinimumHeight, 28 setPointSize

**Impacto**:
- Alterar cor primária requer editar 44 arquivos manualmente
- Risco alto de esquecer algum arquivo
- Inconsistência visual entre telas
- Código repetitivo e difícil de manter

---

## Objetivo

**Migrar gradualmente o código legado para o Design System**

### Metas

1. **Fase 1** (Semanas 1-2): Migrar 10 arquivos críticos (75+ problemas cada)
2. **Fase 2** (Semanas 3-4): Migrar 20 arquivos prioritários (10-19 problemas cada)
3. **Fase 3** (Mês 2+): Migrar restantes durante manutenção contínua

### Critérios de Sucesso

- ✅ Reduzir 75% dos problemas totais (de 2.313 para ~578)
- ✅ Migrar 30 arquivos críticos
- ✅ Zero regressões visuais (smoke tests)
- ✅ Documentação atualizada

---

## Requisitos Funcionais

### RF1: Migração de Cores

**Substituir cores hexadecimais por Design Tokens**

```python
# Antes
setStyleSheet("color: #4CAF50;")

# Depois
from consumo_lib.ui import COLORS
setStyleSheet(f"color: {COLORS.PRIMARY};")
```

**Mapeamento principal**:
- `#4CAF50` → `COLORS.PRIMARY`
- `#2196F3` → `COLORS.SECONDARY`
- `#F44336` → `COLORS.ERROR`
- `#FFFFFF` → `COLORS.BACKGROUND`
- `#111827` → `COLORS.ON_BACKGROUND`
- `#E5E7EB` → `COLORS.OUTLINE`

### RF2: Migração de Fontes

**Substituir QFont() manual por TYPO.get_font()**

```python
# Antes
font = QFont()
font.setPointSize(14)
font.setBold(True)
label.setFont(font)

# Depois
from consumo_lib.ui import TYPO
label.setFont(TYPO.get_font(TYPO.BODY_MEDIUM, bold=True))
```

### RF3: Migração de Dimensões

**Substituir tamanhos hardcoded por DIM tokens**

```python
# Antes
button.setMinimumHeight(40)

# Depois
from consumo_lib.ui import DIM
button.setMinimumHeight(DIM.BUTTON_HEIGHT_MD)
```

### RF4: Migração de setStyleSheet

**Refatorar estilos inline para usar Design Tokens**

```python
# Antes
widget.setStyleSheet("""
    QPushButton {
        background-color: #4CAF50;
        color: white;
        border-radius: 8px;
        padding: 8px 24px;
    }
""")

# Depois
from consumo_lib.ui import COLORS, DIM, SPACE
widget.setStyleSheet(f"""
    QPushButton {{
        background-color: {COLORS.PRIMARY};
        color: {COLORS.ON_PRIMARY};
        border-radius: {DIM.RADIUS_MD}px;
        padding: {SPACE.SM}px {SPACE.LG}px;
    }}
""")
```

---

## Requisitos Não-Funcionais

### RNF1: Manutenibilidade

- Código deve ser legível e self-documenting
- Seguir padrões estabelecidos em docs/design_system/MIGRATION.md
- Usar constantes nomeadas em vez de valores hardcoded

### RNF2: Compatibilidade

- Zero breaking changes visuais
- Smoke test após cada arquivo migrado
- Validação visual comparando antes/depois

### RNF3: Consistência

- Seguir Material Design 3 (já implementado)
- Usar tokens existentes, não criar novos
- Manter consistência com arquivos já migrados

### RNF4: Documentação

- Atualizar MIGRATION.md com novos exemplos
- Registrar arquivos migrados
- Commit descritivo seguindo padrão

---

## Casos de Uso

### UC1: Migrar Dialog Crítico

**Ator**: Desenvolvedor
**Descrição**: Migrar dialog com muitos estilos inline

**Fluxo Principal**:
1. Identificar arquivo com análise (grep, script)
2. Ler arquivo e entender estrutura
3. Importar Design Tokens (COLORS, TYPO, SPACE, DIM)
4. Substituir cores hex por COLORS
5. Substituir QFont por TYPO.get_font()
6. Substituir tamanhos por DIM/SPACE
7. Executar smoke test (python main.py)
8. Validar visualmente a aplicação
9. Commit se sucesso, corrigir se erro
10. Marcar como migrado em MIGRATION.md

**Fluxos Alternativos**:
- **Erro no token**: Consultar TOKENS.md para encontrar token correto
- **Erro no smoke test**: Debugar e corrigir até passar
- **Visual diferente**: Revisar migração e ajustar

### UC2: Validação Visual

**Ator**: Desenvolvedor
**Descrição**: Validar que migração não quebrou visual

**Pré-condições**: Arquivo migrado, smoke test passou
**Fluxo Principal**:
1. Executar aplicação (python main.py)
2. Navegar até tela/feature migrada
3. Comparar visualmente com expectativa
4. Testar estados interativos (hover, focus)
5. Validar cores, fontes, espaçamentos
6. Fechar aplicação
7. Aprovar se OK, corrigir se problema

---

## Critérios de Aceite

### Fase 1 (Semanas 1-2)

- [ ] Migrar 10 arquivos críticos selecionados
- [ ] Reduzir ~40% dos problemas totais
- [ ] Zero regressões visuais
- [ ] Smoke tests passando para todos os arquivos
- [ ] Commits descritivos criados
- [ ] MIGRATION.md atualizado

### Fase 2 (Semanas 3-4)

- [ ] Migrar 20 arquivos prioritários
- [ ] Reduzir ~35% adicional dos problemas
- [ ] Padrão de migração refinado
- [ ] Documentação atualizada
- [ ] Checkpoint da fase criado

### Fase 3 (Mês 2+)

- [ ] Migrar restantes durante manutenção
- [ ] Reduzir ~25% final dos problemas
- [ ] Design System 90%+ adotado
- [ ] Guia de migração consolidado

---

## Arquivos Alvo

### Fase 1: 10 Arquivos Críticos (75+ problemas)

1. **consumo_lib/dialogs/defect_judgment_dialog.py** (75 problemas)
2. **consumo_lib/dialogs/inspection_results_dialog.py** (56 problemas)
3. **consumo_lib/dialogs/mode_selection_dialog.py** (51 problemas)
4. **consumo_lib/dialogs/final_decision_dialog.py** (44 problemas)
5. **consumo_lib/widgets/engenharia/mosaic_capture_widget.py** (30 problemas)
6. **consumo_lib/widgets/engenharia/program_data_widget.py** (30 problemas)
7. **consumo_lib/widgets/engenharia/inspection_windows_widget.py** (31 problemas)
8. **consumo_lib/widgets/engenharia/alignment_widget.py** (35 problemas)
9. **consumo_lib/dialogs/inspection_history_dialog.py** (25 problemas)
10. **consumo_lib/dialogs/stencil/full_history_dialog.py** (21 problemas)

**Total estimado**: 398 problemas (17% do total)
**Tempo estimado**: 20-25 horas
**Impacto**: Reduz ~40% dos problemas totais das fases 1 e 2

### Fase 2: 20 Arquivos Prioritários (10-19 problemas)

**Dialogs**:
- inspection_progress_dialog.py (18)
- operator_workflow_dialog.py (14)
- confirm_positioning_dialog.py (14)
- auth_settings_dialog.py (12)
- engineering_wizard_dialog.py (11)
- map_settings_dialog.py (12)
- recipe_manager_dialog.py (11)
- E outros...

**Widgets**:
- fiducial_capture_widget.py (20)
- confirm_save_widget.py (15)
- E outros...

**Total estimado**: ~250 problemas
**Tempo estimado**: 15-20 horas

### Fase 3: Manutenção Contínua

- Restante dos ~40 arquivos
- Migrar durante bug fixes/features
- Temporiz undefined: 5-10 horas spread ao longo de meses

---

## Riscos e Mitigações

### Risco 1: Regressões Visuais

**Probabilidade**: Média
**Impacto**: Alto
**Mitigação**:
- Smoke test obrigatório após cada migração
- Validação visual comparando antes/depois
- Commit descritivo para fácil revert

### Risco 2: Token Não Existe

**Probabilidade**: Baixa
**Impacto**: Médio
**Mitigação**:
- Consultar TOKENS.md antes de usar
- Se necessário, adicionar token em design_tokens.py
- Documentar token adicionado

### Risco 3: Tempo Subestimado

**Probabilidade**: Média
**Impacto**: Médio
**Mitigação**:
- Fases curtas (2 semanas cada)
- Avaliação ao final de cada fase
- Ajuste de escopo se necessário

---

## Dependências

### Dependências Técnicas

- ✅ Design System v1.0 implementado
- ✅ Documentação completa (TOKENS.md, COMPONENTS.md, MIGRATION.md)
- ✅ Script de análise funcionando

### Dependências Externas

- Nenhuma

---

## Deliverables

### Fase 1

- 10 arquivos migrados
- Commits: 10 commits (1 por arquivo)
- Checkpoint commit ao final
- MIGRATION.md atualizado
- Smoke tests validados

### Fase 2

- 20 arquivos migrados adicionais
- Commits: 20 commits
- Checkpoint commit ao final
- Documentação refinada

### Fase 3

- Restante dos arquivos migrados gradualmente
- Design System 90%+ adotado
- Guia definitivo de migração

---

## Referências

- **docs/design_system/README.md** - Visão geral do Design System
- **docs/design_system/TOKENS.md** - Referência completa de tokens
- **docs/design_system/COMPONENTS.md** - Componentes base
- **docs/design_system/MIGRATION.md** - Guia de migração
- **DESIGN_SYSTEM_AUDIT_REPORT.md** - Relatório de auditoria completo
- **conductor/archive/design_system_20260119/** - Track de implementação original

---

**Última atualização**: 2026-01-19
**Versão**: 1.0.0
**Status**: 📝 Especificação Completa - Aguardando Implementação
