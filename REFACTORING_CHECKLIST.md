# ✅ Checklist Executivo - Refactoring consumo_lib.py

**Status:** Planejamento Completo | **Próximo Passo:** Iniciar Fase 1

---

## 📊 Visão Geral

**Objetivo:** Reduzir `consumo_lib.py` de **6.245 linhas** para estrutura modular

**Tempo Estimado:** 10-15 dias úteis
**Risco:** Médio (mitigado por migração gradual)
**Prioridade:** ALTA

---

## 🗂️ Estrutura Proposta

```
consumo_lib/          (pacote modular)
├── main_window.py    ← 350 linhas (era 4.138!)
├── widgets/          ← 9 componentes
├── tabs/             ← 6 abas semânticas
├── managers/         ← 6 gerenciadores de negócio
├── dialogs/          ← 9 diálogos
├── threads/          ← 2 workers
└── utils/            ← 3 helpers
```

---

## 📋 Pré-Refactoring (Preparação)

- [ ] Backup do projeto
  ```bash
  git tag pre-refactor-v0.4.0
  git checkout -b refactor/consumo_lib_modular
  ```

- [ ] Ler documentação
  - [ ] `REFACTORING_INDEX.md` (5 min)
  - [ ] `REFACTORING_SUMMARY.md` (10 min)
  - [ ] `REFACTORING_GUIDE.md` (deixar aberto para referência)

- [ ] Ambiente preparado
  - [ ] Python 3.10+ funcionando
  - [ ] PyQt6 instalado
  - [ ] Git configurado

---

## 🚀 Fase 1: Estrutura (Dia 1-2)

**Objetivo:** Criar diretórios e mover widgets existentes

### Passos:
- [ ] Criar estrutura de diretórios
  ```bash
  mkdir -p consumo_lib/{widgets,tabs,managers,dialogs,threads,utils}
  touch consumo_lib/__init__.py
  touch consumo_lib/*/__init__.py
  ```

- [ ] Renomear arquivo principal
  ```bash
  mv consumo_lib.py consumo_lib/main_window.py
  ```

- [ ] Mover widgets (um por vez):
  - [ ] TensionVisualizationWidget → `widgets/tension_viz.py`
  - [ ] TensionCanvas → `widgets/tension_viz.py`
  - [ ] ImageViewerWidget → `widgets/image_viewer.py`
  - [ ] PositionListWidget → `widgets/position_list.py`
  - [ ] SequenceControlWidget → `widgets/sequence_control.py`
  - [ ] PositionRegistryWidget → `widgets/position_registry.py`
  - [ ] CameraPreviewWidget → `widgets/camera_preview.py`
  - [ ] MovementControlWidget → `widgets/movement_control.py`
  - [ ] PLCMonitorWidget → `widgets/plc_monitor.py`

- [ ] Mover threads e utils:
  - [ ] SequenceRunnerThread → `threads/sequence_runner.py`
  - [ ] MapGeneratorThread → `threads/map_generator.py`
  - [ ] MapParams → `utils/map_params.py`
  - [ ] _PreviewSuspender → `widgets/preview_suspender.py`

- [ ] Atualizar imports
- [ ] Testar: `python -m consumo_lib.main_window`
- [ ] Commit: `git commit -m "refactor(fase 1): estruturar diretórios e mover widgets"`

**Entregável:** Aplicação funciona com nova estrutura

---

## 🔌 Fase 2: ConnectionManager (Dia 3)

**Objetivo:** Extrair lógica de conexões para manager dedicado

### Passos:
- [ ] Criar `managers/connection_manager.py`
  - [ ] Classe ConnectionManager
  - [ ] Signals: plc_connected, plc_disconnected, plc_error
  - [ ] Métodos: connect_plc(), disconnect_plc(), attempt_auto_connect()

- [ ] Integrar na MainWindow
  - [ ] Instanciar ConnectionManager em `__init__`
  - [ ] Conectar signals aos handlers
  - [ ] Atualizar botões da UI

- [ ] Mover código de `connect_cnc()` para manager
- [ ] Testar conexão/desconexão
- [ ] Testar auto-connect ao iniciar
- [ ] Commit: `git commit -m "refactor(fase 2): extrair ConnectionManager"`

**Entregável:** Conexões funcionando via manager

---

## 📦 Fase 3: Outros Managers (Dia 4-5)

**Objetivo:** Extrair lógica de negócio para managers especializados

### Passos:
- [ ] **RecipeManagerWrapper** (`managers/recipe_manager.py`)
  - [ ] Gerencia RecipeManager
  - [ ] Dialog de gerenciamento
  - [ ] Aplicar receita à UI
  - [ ] Commit separado

- [ ] **StencilManagerWrapper** (`managers/stencil_manager.py`)
  - [ ] Gerencia StencilTracker
  - [ ] Seleção de stencil
  - [ ] Salvamento automático
  - [ ] Commit separado

- [ ] **InspectionManager** (`managers/inspection_manager.py`)
  - [ ] Workflow de inspeção
  - [ ] Fiducial alignment
  - [ ] Exportação PDF
  - [ ] Commit separado

- [ ] **ReportManagerWrapper** (`managers/report_manager.py`)
  - [ ] Geração de relatórios
  - [ ] Dialogs de consulta
  - [ ] Configurações
  - [ ] Commit separado

**Entregável:** 5 managers funcionando, código testável sem UI

---

## 💬 Fase 4: Diálogos (Dia 6-7)

**Objetivo:** Mover diálogos para arquivos próprios

### Passos:
- [ ] Criar estrutura em `dialogs/`
- [ ] Mover um diálogo por vez:
  - [ ] CameraSettingsDialog
  - [ ] FOVCalibrationDialog (já existe, apenas mover)
  - [ ] CrosshairSettingsDialog (já existe)
  - [ ] FiducialAlignmentDialog (já existe)
  - [ ] InspectionSettingsDialog (já existe)
  - [ ] ReportSettingsDialog (já existe)
  - [ ] CalibrationTestDialog
  - [ ] AboutDialog
  - [ ] MapDefinitionDialog
- [ ] Testar cada diálogo
- [ ] Commits pequenos

**Entregável:** Todos diálogos isolados

---

## 📑 Fase 5: Abas (Dia 8-9)

**Objetivo:** Divir UI em abas semânticas

### Passos:
- [ ] Criar `BaseTab` (`tabs/base_tab.py`)
- [ ] Criar abas:
  - [ ] **CNControlTab** (`tabs/cnc_control_tab.py`)
    - Preview de câmera
    - Movimentação
    - Monitor PLC
  - [ ] **TensionTab** (`tabs/tension_tab.py`)
    - Visualização de tensão
    - Diálogo de medição
  - [ ] **InspectionTab** (`tabs/inspection_tab.py`)
    - Config parâmetros
    - Executa inspeção
  - [ ] **TrackingTab** (`tabs/tracking_tab.py`)
    - Seleção stencil
    - Histórico
  - [ ] **MapTab** (`tabs/map_tab.py`)
    - Programação de mapa

- [ ] Mover código de `setup_ui()` para as abas
- [ ] Testar navegação entre abas
- [ ] Testar funcionalidades em cada aba
- [ ] Commit por aba

**Entregável:** UI modularizada em 6 abas

---

## 🧹 Fase 6: Simplificação (Dia 10-11)

**Objetivo:** Reduzir AOIControllerApp de 4.138 para ~350 linhas

### Passos:
- [ ] Remover código movido
- [ ] Simplificar `__init__()` (chamar managers)
- [ ] Simplificar `setup_ui()` (criar tabs)
- [ ] Simplificar `setup_menu()` (delegar)
- [ ] Manter apenas orquestração

### Resultado esperado:
```python
class AOIControllerApp(QMainWindow):
    def __init__(self):
        # 1. Config (5 linhas)
        self._init_config()
        # 2. Controller (5 linhas)
        self._init_controller()
        # 3. Managers (10 linhas)
        self._init_managers()
        # 4. Tabs (20 linhas)
        self._init_tabs()
        # 5. Menu (10 linhas)
        self._init_menu()
        # 6. Connections (10 linhas)
        self._init_connections()
        # Total: ~60 linhas
```

**Entregável:** MainWindow com ~350 linhas totais

---

## ✅ Fase 7: Validação (Dia 12-13)

**Objetivo:** Testar tudo e garantir zero regressões

### Checklist Funcional:
- [ ] **Conexões**
  - [ ] Conectar PLC
  - [ ] Desconectar PLC
  - [ ] Conectar Câmera
  - [ ] Testar Câmera

- [ ] **Movimentação**
  - [ ] Jog X/Y/Z
  - [ ] Go to position
  - [ ] Stop/Emergency stop
  - [ ] Display de posição

- [ ] **Medição Tensão**
  - [ ] Abrir diálogo
  - [ ] Executar medição completa
  - [ ] Salvar no histórico
  - [ ] Gerar relatório

- [ ] **Inspeção Visual**
  - [ ] Carregar Gerber
  - [ ] Alinhar fiduciais
  - [ ] Executar inspeção
  - [ ] Exportar PDF

- [ ] **Rastreabilidade**
  - [ ] Selecionar stencil
  - [ ] Ver histórico
  - [ ] Criar novo stencil

- [ ] **Mapa**
  - [ ] Definir programa
  - [ ] Salvar programa
  - [ ] Carregar programa
  - [ ] Gerar mapa

### Checklist Técnico:
- [ ] mypy sem erros
- [ ] pylint < 5.0/10
- [ ] Zero warnings em execução
- [ ] Todos os widgets funcionam
- [ ] Sem regressões visuais

**Entregável:** Sistema validado e pronto para merge

---

## 📊 Métricas de Sucesso

### Durante Processo
- [ ] Cada fase testada antes de avançar
- [ ] Commits pequenos e frequentes
- [ ] Zero regressões detectadas

### Ao Final
- [ ] Arquivo principal < 400 linhas
- [ ] Maior arquivo < 700 linhas
- [ ] Todas funcionalidades originais funcionando
- [ ] Código mais legível e organizado

---

## 🎯 Pontos de Decisão

### Após Fase 1
- **Se funcionou:** Continuar para Fase 2
- **Se quebrou:** Usar `git reset --hard HEAD~1` e revisar

### Após Fase 3
- **Se managers funcionam:** Continuar extrair diálogos
- **Se muito complexo:** Revisar abordagem, considerar ajuste

### Após Fase 7
- **Se tudo validado:** Merge para main
- **Se há problemas:** Corrigir e re-testar

---

## 🚨 Riscos e Mitigações

| Risco | Probabilidade | Mitigação |
|-------|---------------|------------|
| Quebrar funcionalidade | Média | Testes após cada fase |
| Demorar mais tempo | Média | Commits pequenos, progresso visível |
| Dificuldade técnica | Baixa | Seguir REFACTORING_GUIDE.md detalhado |
| Regressões sutis | Baixa | Checklist completo de validação |

---

## 📝 Commits Sugeridos

```bash
# Padrão de mensagens
git commit -m "refactor(fase X): descrição

- Mudança 1
- Mudança 2
- Testes: ✅ funcionando"

# Exemplos
git commit -m "refactor(fase 1): criar estrutura de diretórios

- Criado consumo_lib/ com 6 subpacotes
- Movido consumo_lib.py → main_window.py
- Movidos 9 widgets para widgets/
- Movidos 2 threads para threads/
- Atualizados imports
- Testes: ✅ aplicação inicia e funciona"

git commit -m "refactor(fase 2): extrair ConnectionManager

- Criado managers/connection_manager.py
- Movido connect_cnc() para manager
- Implementados signals plc_connected/disconnected
- Atualizado MainWindow para usar manager
- Testes: ✅ conecta/desconecta PLC funcionando"
```

---

## 🎓 Referências Rápidas

### Para Dúvidas Técnicas
- **Detalhes:** `REFACTORING_CONSUMO_LIB_PLAN.md`
- **Diagramas:** `REFACTORING_DIAGRAM.txt`
- **Passo a passo:** `REFACTORING_GUIDE.md`

### Para Visão Geral
- **Resumo:** `REFACTORING_SUMMARY.md`
- **Índice:** `REFACTORING_INDEX.md` (este arquivo)

### Para Contexto
- **Qualidade:** `CODE_QUALITY_IMPROVEMENTS.md`
- **Projeto:** `CLAUDE.md`

---

## ✨ Sucesso!

Ao completar este checklist:

✅ Código modular e organizado
✅ Fácil de manter e evoluir
✅ Testável sem UI completa
✅ Preparado para melhorias futuras
✅ 6.245 linhas → estrutura coerente

---

**Checklist elaborado:** 03/01/2026
**Status:** Pronto para uso
**Versão:** 1.0
