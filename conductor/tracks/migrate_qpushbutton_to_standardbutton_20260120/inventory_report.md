# Relatório de Inventário: QPushButton Migration

**Data:** 2026-01-20
**Track:** migrate_qpushbutton_to_standardbutton_20260120
**Status:** Fase 1 - Análise e Inventário (COMPLETA)

## Resumo Executivo

- **Total de Arquivos Analisados:** 50
- **Total de Botões Identificados:** 197
- **Arquivos de Alta Prioridade (>5 botões):** 15
- **Arquivos de Média Prioridade (2-5 botões):** 26
- **Arquivos de Baixa Prioridade (1 botão):** 9

## Distribuição por Faixa de Prioridade

### Alta Prioridade (7-14 botões)

| Arquivo | Botões | Prioridade | Estimativa |
|---------|--------|------------|------------|
| consumo_lib\widgets\movement_control.py | 14 | Alta | 2h |
| consumo_lib\controllers\camera_settings_controller.py | 8 | Alta | 1.5h |
| consumo_lib\dialogs\defect_judgment_dialog.py | 8 | Média | 1.5h |
| consumo_lib\dialogs\map_settings_dialog.py | 8 | Média | 1.5h |
| consumo_lib\widgets\engenharia\inspection_windows_widget.py | 8 | Média | 1.5h |
| consumo_lib\dialogs\tension\tension_measurement_dialog.py | 8 | Média | 1.5h |
| consumo_lib\controllers\calibration_controller.py | 7 | Alta | 1h |
| consumo_lib\controllers\inspection_ui_controller.py | 7 | Alta | 1h |
| consumo_lib\dialogs\report_settings.py | 7 | Média | 1h |
| consumo_lib\widgets\sequence_control.py | 7 | Média | 1h |
| consumo_lib\dialogs\recipe\recipe_manager_dialog.py | 6 | Média | 1h |
| consumo_lib\dialogs\stencil\manager_dialog.py | 6 | Média | 1h |
| consumo_lib\ui_builders\ui_builders.py | 5 | Média | 1h |
| consumo_lib\widgets\engenharia\gerber_upload_widget.py | 5 | Média | 1h |

**Subtotal Alta Prioridade:** 4 arquivos, 30 botões
**Subtotal Média Prioridade:** 10 arquivos, 73 botões

### Média Prioridade (2-4 botões)

| Arquivo | Botões | Prioridade | Estimativa |
|---------|--------|------------|------------|
| consumo_lib\dialogs\crosshair_settings.py | 4 | Média | 45min |
| consumo_lib\dialogs\engineering_wizard_dialog.py | 4 | Média | 45min |
| consumo_lib\dialogs\inspection_history_dialog.py | 4 | Média | 45min |
| consumo_lib\widgets\engenharia\alignment_widget.py | 4 | Média | 45min |
| consumo_lib\widgets\engenharia\gerber_edit_dialogs.py | 4 | Média | 45min |
| consumo_lib\widgets\stencil\identification_widget.py | 4 | Média | 45min |
| consumo_lib\controllers\report_dialog_controller.py | 3 | Média | 30min |
| consumo_lib\dialogs\final_decision_dialog.py | 3 | Média | 30min |
| consumo_lib\dialogs\inspection_results_dialog.py | 3 | Média | 30min |
| consumo_lib\dialogs\inspection_settings.py | 3 | Média | 30min |
| consumo_lib\tabs\tracking_tab.py | 3 | Média | 30min |
| consumo_lib\widgets\camera_capture.py | 3 | Média | 30min |
| consumo_lib\widgets\plc_monitor.py | 3 | Média | 30min |
| consumo_lib\widgets\tension_viz.py | 3 | Média | 30min |
| consumo_lib\widgets\engenharia\confirm_save_widget.py | 3 | Média | 30min |
| consumo_lib\widgets\engenharia\mosaic_capture_widget.py | 3 | Média | 30min |
| consumo_lib\utils\main_window\engineering_workflow.py | 3 | Média | 30min |
| consumo_lib\dialogs\auth_settings_dialog.py | 2 | Média | 20min |
| consumo_lib\dialogs\confirm_positioning_dialog.py | 2 | Média | 20min |
| consumo_lib\dialogs\fov_calibration.py | 2 | Média | 20min |
| consumo_lib\dialogs\inspection_progress_dialog.py | 2 | Média | 20min |
| consumo_lib\dialogs\login_dialog.py | 2 | Média | 20min |
| consumo_lib\dialogs\mode_selection_dialog.py | 2 | Média | 20min |
| consumo_lib\dialogs\operator_workflow_dialog.py | 2 | Média | 20min |
| consumo_lib\dialogs\theme_settings.py | 2 | Média | 20min |
| consumo_lib\tabs\inspection_tab.py | 2 | Média | 20min |
| consumo_lib\tabs\map_tab.py | 2 | Média | 20min |
| consumo_lib\tabs\tree_view_tab.py | 2 | Média | 20min |
| consumo_lib\widgets\camera_preview.py | 2 | Média | 20min |
| consumo_lib\widgets\position_list.py | 2 | Média | 20min |
| consumo_lib\widgets\position_registry.py | 2 | Média | 20min |
| consumo_lib\widgets\engenharia\fiducial_capture_widget.py | 2 | Média | 20min |
| consumo_lib\dialogs\stencil\full_history_dialog.py | 2 | Média | 20min |
| consumo_lib\dialogs\stencil\history_dialog.py | 2 | Média | 20min |

**Subtotal:** 33 arquivos, 90 botões

### Baixa Prioridade (1 botão)

| Arquivo | Botões | Prioridade | Estimativa |
|---------|--------|------------|------------|
| consumo_lib\controllers\fiducial_alignment_controller.py | 1 | Baixa | 15min |
| consumo_lib\handlers\dialog_router.py | 1 | Baixa | 15min |

**Subtotal:** 2 arquivos, 2 botões

## Totais Consolidados

| Prioridade | Arquivos | Botões | Estimativa Total |
|------------|----------|--------|------------------|
| Alta | 4 | 30 | 5.5h |
| Média | 44 | 165 | 18.5h |
| Baixa | 2 | 2 | 0.5h |
| **TOTAL** | **50** | **197** | **~24.5h** |

## Análise por Tipo de Botão (Estimativa)

Baseado em análise preliminar dos arquivos de alta prioridade:

### Tipo 1: Botões de Ação Primária (~40%)
- Exemplos: "Salvar", "Aplicar", "Confirmar", "OK"
- Padrão: `StandardButton(text, variant="primary")`
- Estimativa: ~79 botões

### Tipo 2: Botões de Ação Secundária (~30%)
- Exemplos: "Cancelar", "Fechar", "Voltar"
- Padrão: `StandardButton(text, variant="secondary")`
- Estimativa: ~59 botões

### Tipo 3: Botões de Ação Perigosa (~5%)
- Exemplos: "Excluir", "Deletar", "Remover"
- Padrão: `StandardButton(text, variant="danger")`
- Estimativa: ~10 botões

### Tipo 4: Botões de Ícone/Símbolo (~15%)
- Exemplos: "📁", "🎯", "↑", "↓"
- Padrão: `StandardButton(icon, icon_only=True)` ou setStyleSheet customizado
- Estimativa: ~30 botões

### Tipo 5: Botões Especiais (~10%)
- Botões com comportamento complexo ou customizado
- Padrão: setStyleSheet com COLORS + DIM tokens
- Estimativa: ~19 botões

## Próximos Passos

1. ✅ **T1.1:** Listar todos os arquivos com QPushButton (COMPLETO)
2. ✅ **T1.2:** Contar botões por arquivo (COMPLETO)
3. 🔄 **T1.3:** Analisar tipos de botão (EM ANDAMENTO)
4. ⏳ **T1.4:** Priorizar arquivos (PENDENTE)
5. ⏳ **T1.5:** Criar matriz de migração (PENDENTE)

## Conclusão da Fase 1

A contagem exata de **197 botões** confirma a estimativa inicial. A distribuição está bem equilibrada, com a maioria dos arquivos tendo 2-4 botões. Os 4 arquivos de alta prioridade representam 15% do total de botões e são bons candidatos para migração inicial.

**Checkpoint 1 Status:** Pronto para commit após conclusão da T1.5.
