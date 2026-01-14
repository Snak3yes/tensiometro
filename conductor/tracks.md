# Project Tracks

This file tracks all major tracks for the project. Each track has its own detailed plan in its respective folder.

---

## 📦 Engineering Wizard - Todas as 7 Abas COMPLETAS (archived) <!-- 2026-01-13 -->

### [x] Aba 1: Dados do Programa (archived)
*Link: [./conductor/archive/engenharia_aba1_dados_programa/](./conductor/archive/engenharia_aba1_dados_programa/)*
- **Track ID:** engenharia_aba1_dados_programa
- **Status:** ✅ Complete
- **Código:** `consumo_lib/widgets/engenharia/program_data_widget.py` (448 linhas)
- **Testes:** 8 testes unitários
- **Entregável:** Widget de coleta de dados do programa (nome, stencil, versão, etc.)

### [x] Aba 2: Carregar Gerber (archived)
*Link: [./conductor/archive/engenharia_aba2_carregar_gerber/](./conductor/archive/engenharia_aba2_carregar_gerber/)*
- **Track ID:** engenharia_aba2_carregar_gerber
- **Status:** ✅ Complete
- **Código:** `consumo_lib/widgets/engenharia/gerber_upload_widget.py` (591 linhas)
- **Testes:** 5 testes unitários
- **Entregável:** Widget de upload e preview de arquivo Gerber

### [x] Aba 3: Definir Fiduciais (archived)
*Link: [./conductor/archive/engenharia_aba3_definir_fiduciais/](./conductor/archive/engenharia_aba3_definir_fiduciais/)*
- **Track ID:** engenharia_aba3_definir_fiduciais
- **Status:** ✅ Complete
- **Código:** `consumo_lib/widgets/engenharia/fiducial_capture_widget.py` (564 linhas)
- **Testes:** 6 testes unitários
- **Entregável:** Widget de captura de templates fiduciais

### [x] Aba 4: Capturar Mosaico (archived)
*Link: [./conductor/archive/engenharia_aba4_capturar_mosaico/](./conductor/archive/engenharia_aba4_capturar_mosaico/)*
- **Track ID:** engenharia_aba4_capturar_mosaico
- **Status:** ✅ Complete
- **Código:** `consumo_lib/widgets/engenharia/mosaic_capture_widget.py` (647 linhas)
- **Testes:** 5 testes unitários
- **Entregável:** Widget de captura de mosaico via grid

### [x] Aba 5: Alinhamento (archived)
*Link: [./conductor/archive/engenharia_aba5_alinhamento/](./conductor/archive/engenharia_aba5_alinhamento/)*
- **Track ID:** engenharia_aba5_alinhamento
- **Status:** ✅ Complete (implementado anteriormente)
- **Código:** `consumo_lib/widgets/engenharia/alignment_widget.py` (1,036 linhas)
- **Testes:** 34 testes unitários
- **Entregável:** Widget de alinhamento Gerber ↔ imagem

### [x] Aba 6: Janelas de Inspeção (archived)
*Link: [./conductor/archive/engenharia_aba6_janelas_inspecao/](./conductor/archive/engenharia_aba6_janelas_inspecao/)*
- **Track ID:** engenharia_aba6_janelas_inspecao
- **Status:** ✅ Complete (implementado anteriormente)
- **Código:** `consumo_lib/widgets/engenharia/inspection_windows_widget.py` (886 linhas)
- **Testes:** 34 testes unitários
- **Entregável:** Widget de configuração de janelas de inspeção

### [x] Aba 7: Confirmar e Salvar (archived)
*Link: [./conductor/archive/engenharia_aba7_confirmar_salvar/](./conductor/archive/engenharia_aba7_confirmar_salvar/)*
- **Track ID:** engenharia_aba7_confirmar_salvar
- **Status:** ✅ Complete (implementado anteriormente)
- **Código:** `consumo_lib/widgets/engenharia/confirm_save_widget.py` (500 linhas)
- **Testes:** 30 testes unitários
- **Entregável:** Widget de resumo e salvamento

**📊 Resumo Engineering Wizard:**
- Total de código implementado: ~4,672 linhas
- Total de testes: 122 testes unitários
- Status: **100% COMPLETO** ✅
- Relatório: `conductor/RELATORIO_IMPLEMENTACAO_ABAS_1-4.md`

---

## [x] Track: Refatoração da Gestão de Receitas (archived) <!-- 2026-01-11 -->
*Link: [./conductor/archive/refactor_recipe_manager_20260110/](./conductor/archive/refactor_recipe_manager_20260110/)*

## [x] Track: Implement operator workflow (archived) <!-- 2026-01-13 -->
*Link: [./conductor/archive/feature_implement_operator_workflow_20260111/](./conductor/archive/feature_implement_operator_workflow_20260111/)*
- **Track ID:** feature_implement_operator_workflow_20260111
- **Status:** Complete
- **Created:** 2026-01-11
- **Completed:** 2026-01-13
- **Plan:** ./archive/feature_implement_operator_workflow_20260111/plan.md
- **Spec:** ./archive/feature_implement_operator_workflow_20260111/spec.md

## [ ] Track: Refactor large monolithic files (Refactor)
- **Track ID:** refactor_large_files_20260113
- **Status:** New
- **Priority:** Medium-High
- **Created:** 2026-01-13
- **Est. Duration:** 4-6 weeks
- **Phases:** 3 (High/Medium/Low priority)
- **Plan:** ./tracks/refactor_large_files_20260113/plan.md
- **Spec:** ./tracks/refactor_large_files_20260113/spec.md
- **Target:** Refactor 38 files >500 lines, eliminate anti-patterns

---

## [x] Track: Integrar Engineering Wizard (archived) <!-- 2026-01-14 -->
*Link: [./conductor/archive/integrate_engineering_wizard_20260113/](./conductor/archive/integrate_engineering_wizard_20260113/)*
- **Track ID:** integrate_engineering_wizard_20260113
- **Status:** ✅ 98% Complete - Ready for validation
- **Priority:** Critical
- **Created:** 2026-01-13
- **Completed:** 2026-01-14
- **Est. Duration:** 3-4 weeks
- **Actual Duration:** 1 day
- **Phases:** 4/4 complete
- **Final Commit:** d687ba3
- **Plan:** ./archive/integrate_engineering_wizard_20260113/plan.md
- **Spec:** ./archive/integrate_engineering_wizard_20260113/spec.md
- **Metadata:** ./archive/integrate_engineering_wizard_20260113/metadata.json
- **Dependencies:** Tracks 1-7 do Engineering Wizard (TODAS COMPLETAS)
- **Deliverables:**
  - ✅ EngineeringWizardDialog (orchestrator das 7 abas)
  - ✅ EngineeringWizardState (estado compartilhado)
  - ✅ EngineeringHardwareCoordinator (coordenação de hardware)
  - ✅ EngineeringProgramManager (persistência de programas)
  - ✅ EngineeringRecipeCoordinator (integração com RecipeManager)
  - ✅ Menu integration + toolbar button
  - ✅ Documentação completa (620 linhas)

---
*Last updated: 2026-01-14*
