# Plano de Implementação: Integrar Engineering Wizard

## Visão Geral
**Track ID:** integrate_engineering_wizard_20260113
**Status:** 📋 Not Started
**Duração Estimada:** 3-4 semanas
**Fases:** 4

---

## Fase 1: Arquitetura Base e State Manager (Semana 1)

### Objetivo
Criar a arquitetura fundamental do Engineering Wizard, incluindo o State Manager compartilhado e o Dialog principal (esqueleto).

### Tarefas

#### 1.1 Criar EngineeringWizardState (2 dias)
**Responsável:** Developer
**Prioridade:** Alta
**Dependencies:** Nenhuma

**Subtarefas:**
- [ ] Criar arquivo `consumo_lib/models/engineering/wizard_state.py`
- [ ] Implementar dataclass `EngineeringWizardState`
  - [ ] Campos para cada aba (program_data, gerber_data, fiducial_templates, etc.)
  - [ ] Campo current_tab para rastrear aba atual
  - [ ] Campo is_dirty para rastrear mudanças não salvas
- [ ] Implementar método `is_valid(tab_index)` para validação por aba
- [ ] Implementar método `validate_dependencies(tab_index)` para validação cruzada
- [ ] Implementar método `to_dict()` para serialização JSON
- [ ] Implementar classmethod `from_dict()` para desserialização
- [ ] Adicionar logging para mudanças de estado

**Critérios de Sucesso:**
- StateManager pode ser instanciado sem erros
- Serialização/desserialização funciona corretamente
- Validação de dependências funciona (ex: aba 2 depende de aba 1)

**Testes:**
- `test_wizard_state_creation()`: Criar estado vazio
- `test_wizard_state_serialization()`: Testar to_dict/from_dict
- `test_wizard_state_validation()`: Testar validação de cada aba
- `test_wizard_state_dependencies()`: Testar validação cruzada

**Arquivos:**
- Novo: `consumo_lib/models/engineering/wizard_state.py`
- Novo: `tests/unit/models/test_wizard_state.py`

---

#### 1.2 Criar EngineeringWizardDialog (Esqueleto) (2 dias)
**Responsável:** Developer
**Prioridade:** Alta
**Dependencies:** Tarefa 1.1

**Subtarefas:**
- [ ] Criar arquivo `consumo_lib/dialogs/engineering_wizard_dialog.py`
- [ ] Implementar classe `EngineeringWizardDialog(QDialog)`
  - [ ] Layout principal com QVBoxLayout
  - [ ] Barra de progresso (QProgressBar ou QLabel customizado)
  - [ ] QTabWidget com 7 tabs (placeholders por enquanto)
  - [ ] Barra de botões (Anterior, Próximo, Cancelar, Concluir)
- [ ] Instanciar EngineeringWizardState
- [ ] Conectar sinais dos botões a slots
- [ ] Implementar navegação básica (próximo/anterior)
- [ ] Implementar validação antes de avançar (não avança se aba inválida)
- [ ] Implementar closeEvent com detecção de mudanças não salvas

**Critérios de Sucesso:**
- Dialog abre sem erros
- Navegação entre tabs funciona
- Botões estão habilitados/desabilitados corretamente
- Dialog não fecha se houver mudanças não salvas (pergunta ao usuário)

**Testes:**
- `test_dialog_creation()`: Criar dialog sem erros
- `test_navigation()`: Testar botões anterior/próximo
- `test_validation_blocking()`: Não avança se aba inválida
- `test_unsaved_changes()`: Detecta mudanças ao fechar

**Arquivos:**
- Novo: `consumo_lib/dialogs/engineering_wizard_dialog.py`
- Novo: `tests/unit/dialogs/test_engineering_wizard_dialog.py`

---

#### 1.3 Implementar Auto-Save Básico (1 dia)
**Responsável:** Developer
**Prioridade:** Média
**Dependencies:** Tarefas 1.1, 1.2

**Subtarefas:**
- [ ] Adicionar QTimer em EngineeringWizardDialog
- [ ] Implementar método `auto_save()` que salva estado a cada 2 minutos
- [ ] Gerar nome de arquivo auto-save único (ex: `.autosave_20260113_153045.json`)
- [ ] Salvar em `data/inspection_programs/.autosaves/`
- [ ] Detectar auto-saves ao abrir wizard e oferecer recuperação

**Critérios de Sucesso:**
- Auto-save acontece silenciosamente em background
- Auto-saves são recuperados se wizard foi fechado inesperadamente
- Auto-saves são limpos após conclusão bem-sucedida

**Testes:**
- `test_auto_save_timer()`: Timer dispara auto-save
- `test_auto_save_recovery()`: Recupera estado de auto-save
- `test_auto_save_cleanup()`: Limpa auto-saves após conclusão

**Arquivos:**
- Modificar: `consumo_lib/dialogs/engineering_wizard_dialog.py`
- Modificar: `tests/unit/dialogs/test_engineering_wizard_dialog.py`

---

## Fase 2: Hardware Coordinator e Integração de Menu (Semana 2)

### Objetivo
Criar coordenação de hardware e integrar o Engineering Wizard ao menu principal da aplicação.

### Tarefas

#### 2.1 Criar EngineeringHardwareCoordinator (2 dias)
**Responsável:** Developer
**Prioridade:** Alta
**Dependencies:** Nenhuma

**Subtarefas:**
- [~] Criar arquivo `consumo_lib/coordinators/engineering_hardware_coordinator.py` [manual]
- [~] Implementar classe `EngineeringHardwareCoordinator` [manual]
  - [~] Construtor recebe referências para CameraController, PLCAxisController, FiducialAligner [manual]
  - [~] Método `is_hardware_ready(required)` para verificar disponibilidade [manual]
  - [~] Método `capture_fiducial_template(x, y)` para Aba 3 [manual]
  - [~] Método `capture_mosaic_grid(config)` para Aba 4 [manual]
  - [~] Método `perform_fiducial_alignment()` para Aba 5 [manual]
- [~] Adicionar tratamento de erros (hardware desconectado, timeout, etc.) [manual]
- [~] Adicionar logging extensivo (🎯, ⚠️, ❌ para operações) [manual]

**Critérios de Sucesso:**
- Coordinator pode ser instanciado com controllers do MainWindow
- Verifica disponibilidade de hardware corretamente
- Captura templates fiduciais sem erros (se hardware conectado)
- Captura mosaico sem erros (se hardware conectado)
- Retorna mensagens de erro claras se hardware indisponível

**Testes:**
- `test_hardware_check()`: Verifica disponibilidade de hardware
- `test_fiducial_capture()`: Captura template fiducial
- `test_mosaic_capture()`: Captura mosaico
- `test_hardware_unavailable()`: Trata erro quando hardware desconectado
- `test_fiducial_alignment()`: Executa alinhamento

**Arquivos:**
- Novo: `consumo_lib/coordinators/engineering_hardware_coordinator.py`
- Novo: `tests/unit/coordinators/test_engineering_hardware_coordinator.py`

---

#### 2.2 Integrar Abas 3, 4, 5 ao Hardware (2 dias)
**Responsável:** Developer
**Prioridade:** Alta
**Dependencies:** Tarefa 2.1

**Subtarefas:**
- [~] Modificar widgets das Abas 3, 4, 5 para receber EngineeringHardwareCoordinator [manual]
- [~] **Aba 3 (FiducialCaptureWidget)**: Usar `capture_fiducial_template()` [manual] [manual]
  - [~] Verificar disponibilidade de câmera antes de capturar [manual] [manual]
  - [~] Mostrar erro se câmera desconectada [manual] [manual]
  - [~] Salvar template em EngineeringWizardState [manual] [manual]
- [~] **Aba 4 (MosaicCaptureWidget)**: Usar `capture_mosaic_grid()` [manual] [manual]
  - [~] Verificar disponibilidade de PLC e câmera [manual] [manual]
  - [~] Mostrar erro se hardware desconectado [manual] [manual]
  - [~] Salvar mosaico em EngineeringWizardState [manual] [manual]
- [~] **Aba 5 (AlignmentWidget)**: Usar `perform_fiducial_alignment()` [manual] [manual]
  - [~] Receber fiducial templates do estado [manual] [manual]
  - [~] Executar template matching [manual] [manual]
  - [~] Salvar transform em EngineeringWizardState [manual] [manual]

**Critérios de Sucesso:**
- Abas 3, 4, 5 funcionam com hardware real
- Abas 3, 4, 5 mostram erros claros se hardware indisponível
- Dados capturados são salvos no estado compartilhado
- Widgets podem ser testados sem hardware (modo offline)

**Testes:**
- `test_aba3_hardware_integration()`: Testar captura de fiducial
- `test_aba4_hardware_integration()`: Testar captura de mosaico
- `test_aba5_hardware_integration()`: Testar alinhamento
- `test_offline_mode()`: Testar modo sem hardware

**Arquivos:**
- Modificar: `consumo_lib/widgets/engenharia/fiducial_capture_widget.py` (se existir, senão criar)
- Modificar: `consumo_lib/widgets/engenharia/mosaic_capture_widget.py` (se existir, senão criar)
- Modificar: `consumo_lib/widgets/engenharia/alignment_widget.py`
- Novo: `tests/integration/test_engineering_hardware_integration.py`

---

#### 2.3 Adicionar Menu Entry e Toolbar Button (1 dia)
**Responsível:** Developer
**Prioridade:** Alta
**Dependencies:** Tarefa 1.2

**Subtarefas:**
- [~] Modificar `consumo_lib/handlers/menu_handler.py` [manual] [manual]
  - [~] Adicionar método `setup_engineering_menu()` [manual] [manual]
  - [~] Criar menu "Ferramentas" (se não existir) [manual] [manual]
  - [~] Adicionar ação "Engineering Wizard..." com atalho Ctrl+Shift+E [manual] [manual]
  - [~] Criar menu "Programas" (novo) [manual] [manual]
    - [~] Ação "Listar Programas Salvos..." [manual] [manual]
    - [~] Ação "Carregar Programa..." [manual] [manual]
- [~] Modificar `consumo_lib/main_window.py` [manual]
  - [~] Chamar `menu_handler.setup_engineering_menu()` na inicialização [manual]
  - [~] Adicionar botão na toolbar: "Novo Programa de Inspeção" [manual]
  - [~] Conectar ação a slot que abre EngineeringWizardDialog [manual]
- [~] Implementar slot `open_engineering_wizard()` em MainWindow [manual]
  - [~] Instanciar EngineeringWizardDialog [manual]
  - [~] Passar referências de hardware (controllers) [manual]
  - [~] Executar dialog com `dialog.exec()` [manual]
  - [~] Se Accepted, salvar programa via EngineeringProgramManager [manual]

**Critérios de Sucesso:**
- Menu "Ferramentas → Engineering Wizard" abre dialog
- Atalho Ctrl+Shift+E abre dialog
- Botão da toolbar abre dialog
- Menu "Programas" existe (mesmo que ações ainda não funcionem)

**Testes:**
- `test_menu_entry_exists()`: Verificar se menu foi criado
- `test_menu_opens_dialog()`: Clicar no menu abre dialog
- `test_toolbar_button_opens_dialog()`: Clicar no botão abre dialog
- `test_keyboard_shortcut()`: Ctrl+Shift+E abre dialog

**Arquivos:**
- Modificar: `consumo_lib/handlers/menu_handler.py`
- Modificar: `consumo_lib/main_window.py`
- Novo: `tests/integration/test_menu_integration.py`

---

## Fase 3: Persistência e Integração com RecipeManager (Semana 3)

### Objetivo
Implementar salvamento/carregamento de programas e integração com o RecipeManager existente.

### Tarefas

#### 3.1 Criar EngineeringProgramManager (2 dias)
**Responsável:** Developer
**Prioridade:** Alta
**Dependencies:** Nenhuma

**Subtarefas:**
- [ ] Criar arquivo `consumo_lib/managers/engineering_program_manager.py`
- [ ] Implementar classe `EngineeringProgramManager`
  - [ ] Constante `PROGRAMS_DIR = Path("data/inspection_programs")`
  - [ ] Método `save_program(program: ProgramConfig) -> Path`
    - [ ] Criar diretório se não existir
    - [ ] Gerar filename: `{program_name}.json`
    - [ ] Converter ProgramConfig para dict via `to_dict()`
    - [ ] Salvar como JSON indentado
  - [ ] Método `load_program(program_name: str) -> ProgramConfig`
    - [ ] Ler arquivo JSON
    - [ ] Converter dict para ProgramConfig via `from_dict()`
    - [ ] Tratar erros (arquivo não existe, JSON inválido)
  - [ ] Método `list_programs() -> List[Dict]`
    - [ ] Escanear diretório de programas
    - [ ] Retornar metadados (nome, data criação, stencil_code)
  - [ ] Método `delete_program(program_name: str) -> bool`
    - [ ] Remover arquivo com confirmação
  - [ ] Método `program_exists(program_name: str) -> bool`
- [ ] Adicionar logging para todas as operações

**Critérios de Sucesso:**
- Programas são salvos em JSON corretamente
- Programas salvos podem ser carregados sem perda de dados
- Listagem mostra todos os programas salvos
- Arquivos JSON são legíveis (indentados)

**Testes:**
- `test_save_program()`: Salvar programa
- `test_load_program()`: Carregar programa salvo
- `test_list_programs()`: Listar programas
- `test_delete_program()`: Deletar programa
- `test_roundtrip()`: Salvar e carregar preserva dados

**Arquivos:**
- Novo: `consumo_lib/managers/engineering_program_manager.py`
- Novo: `tests/unit/managers/test_engineering_program_manager.py`

---

#### 3.2 Criar EngineeringRecipeCoordinator (2 dias)
**Responsável:** Developer
**Prioridade:** Alta
**Dependencies:** Tarefa 3.1

**Subtarefas:**
- [ ] Criar arquivo `consumo_lib/coordinators/engineering_recipe_coordinator.py`
- [ ] Analisar schema de Recipe (existente em `aoi_lib/recipe_manager.py`)
- [ ] Analisar schema de ProgramConfig (existente em `consumo_lib/models/engineering/program_config.py`)
- [ ] Implementar classe `EngineeringRecipeCoordinator`
  - [ ] Método `program_to_recipe(program: ProgramConfig) -> Recipe`
    - [ ] Mapear campos: program_name → name
    - [ ] Mapear campos: stencil_code → stencil_code
    - [ ] Mapear campos: gerber_file → gerber_path
    - [ ] Mapear campos: fiducial_positions → fiducials
    - [ ] Mapear campos: alignment_transform → transform
    - [ ] Mapear campos: inspection_groups → inspection_windows
    - [ ] Tratar campos sem correspondência (usar defaults)
  - [ ] Método `recipe_to_program(recipe: Recipe) -> ProgramConfig`
    - [ ] Mapeamento inverso (Recipe → ProgramConfig)
    - [ ] Tratar campos faltantes (usar defaults)
  - [ ] Método `can_convert_to_recipe(program) -> Tuple[bool, str]`
    - [ ] Validar se ProgramConfig pode ser convertido
    - [ ] Retornar mensagem de erro se não puder
- [ ] Adicionar testes de conversão bidirecional

**Critérios de Sucesso:**
- ProgramConfig pode ser convertido para Recipe sem perda de dados críticos
- Recipe pode ser convertido para ProgramConfig (edição)
- Conversão inversa (Recipe → ProgramConfig → Recipe) é idempotente
- Mensagens de erro claras se conversão falhar

**Testes:**
- `test_program_to_recipe()`: Converter ProgramConfig para Recipe
- `test_recipe_to_program()`: Converter Recipe para ProgramConfig
- `test_roundtrip_conversion()`: Conversão bidirecional preserva dados
- `test_conversion_validation()`: Validar antes de converter

**Arquivos:**
- Novo: `consumo_lib/coordinators/engineering_recipe_coordinator.py`
- Novo: `tests/unit/coordinators/test_engineering_recipe_coordinator.py`

---

#### 3.3 Integrar com RecipeManager (1 dia)
**Responsível:** Developer
**Prioridade:** Média
**Dependencies:** Tarefas 3.1, 3.2

**Subtarefas:**
- [ ] Modificar `consumo_lib/managers/recipe_manager_wrapper.py` (se necessário)
  - [ ] Adicionar método `load_from_engineering_program(program_name)`
  - [ ] Adicionar método `create_recipe_from_program(program: ProgramConfig)`
- [ ] Modificar EngineeringWizardDialog
  - [ ] Após concluir (botão "Concluir" clicado), converter para Recipe
  - [ ] Chamar RecipeManager para salvar Recipe
  - [ ] Opcionalmente abrir InspectionTab com Recipe carregado
- [ ] Modificar MenuHandler
  - [~] Ação "Carregar Programa..." [manual] [manual] abre diálogo de seleção
  - [ ] Programa selecionado é convertido para Recipe
  - [ ] Recipe é carregado no sistema

**Critérios de Sucesso:**
- Programa concluído no wizard é convertido para Recipe
- Recipe aparece no RecipeManager
- Recipe pode ser usado no InspectionTab
- Programa salvo pode ser recarregado via menu

**Testes:**
- `test_save_to_recipe_manager()`: Salvar programa como Recipe
- `test_load_from_recipe_manager()`: Carregar Recipe como programa
- `test_inspection_tab_integration()`: Abrir InspectionTab com Recipe

**Arquivos:**
- Modificar: `consumo_lib/managers/recipe_manager_wrapper.py`
- Modificar: `consumo_lib/dialogs/engineering_wizard_dialog.py`
- Modificar: `consumo_lib/handlers/menu_handler.py`
- Novo: `tests/integration/test_recipe_manager_integration.py`

---

## Fase 4: Validação, Polimento e Documentação (Semana 4)

### Objetivo
Completar validações, melhorar UX, adicionar tratamento de erros robusto e documentar código.

### Tarefas

#### 4.1 Implementar Validação Cruzada entre Abas (2 dias)
**Responsável:** Developer
**Prioridade:** Alta
**Dependencies:** Tarefas 1.1, 1.2

**Subtarefas:**
- [ ] Modificar `EngineeringWizardState.validate_dependencies()`
  - [ ] Aba 1 (Dados): Sem dependências
  - [ ] Aba 2 (Gerber): Requer Aba 1 preenchida
  - [ ] Aba 3 (Fiduciais): Requer Aba 2 carregada
  - [ ] Aba 4 (Mosaico): Requer Aba 3 completada
  - [ ] Aba 5 (Alinhamento): Requer Aba 4 capturada
  - [ ] Aba 6 (Janelas): Requer Aba 5 alinhada
  - [ ] Aba 7 (Salvar): Requer todas as anteriores
- [ ] Modificar EngineeringWizardDialog
  - [ ] Chamar `validate_dependencies()` antes de mudar de aba
  - [ ] Mostrar QMessageBox com erro se dependências não atendidas
  - [ ] Bloquear abas subsequentes (desabilitar tabs)
  - [ ] Mostrar indicador visual (✅) quando aba válida
- [ ] Adicionar validações específicas por aba
  - [ ] Aba 1: stencil_code válido, program_name único
  - [ ] Aba 2: arquivo Gerber válido, aperturas detectadas
  - [ ] Aba 3: 2 fiduciais capturados
  - [ ] Aba 4: mosaico completo (todos os FOVs)
  - [ ] Aba 5: score de matching ≥ 70%
  - [ ] Aba 6: pelo menos 1 grupo configurado

**Critérios de Sucesso:**
- Usuário não pode avançar se aba atual inválida
- Usuário não pode pular abas (navegação linear)
- Mensagens de erro específicas e acionáveis
- Indicadores visuais de progresso claros

**Testes:**
- `test_cross_validation_aba2()`: Aba 2 bloqueada sem Aba 1
- `test_cross_validation_aba3()`: Aba 3 bloqueada sem Aba 2
- `test_cross_validation_all()`: Testar todas as dependências
- `test_error_messages()`: Mensagens de erro são específicas

**Arquivos:**
- Modificar: `consumo_lib/models/engineering/wizard_state.py`
- Modificar: `consumo_lib/dialogs/engineering_wizard_dialog.py`
- Novo: `tests/unit/test_cross_validation.py`

---

#### 4.2 Adicionar Tratamento de Erros Robusto (2 dias)
**Responsável:** Developer
**Prioridade:** Alta
**Dependencies:** Todas as tarefas anteriores

**Subtarefas:**
- [ ] Adicionar try/except em todas as operações críticas
  - [ ] Captura de imagem (camera desconectada, timeout)
  - [ ] Movimento PLC (PLC desconectado, erro de comunicação)
  - [ ] Salvamento de arquivo (sem permissão, disco cheio)
  - [ ] Carregamento de Gerber (arquivo inválido, corrompido)
- [ ] Criar exceções customizadas
  - [ ] `EngineeringWizardError` (base)
  - [ ] `HardwareUnavailableError`
  - [ ] `ProgramSaveError`
  - [ ] `GerberLoadError`
- [ ] Adicionar QMessageBox para erros fatais
  - [ ] Botão "OK" fecha dialog
  - [ ] Botão "Retry" tenta operação novamente
  - [ ] Botão "Ignore" continua (se possível)
- [ ] Adicionar logging de erros com stack trace
  - [ ] Usar `logger.exception()` para capturar stack trace
  - [ ] Incluir contexto (aba atual, operação, parâmetros)

**Critérios de Sucesso:**
- Nenhum erro não tratado resulta em crash
- Usuário recebe mensagens de erro claras
- Logs contêm informações suficientes para debugging
- Operações podem ser repetidas após erro

**Testes:**
- `test_camera_disconnected_error()`: Trata erro de câmera desconectada
- `test_plc_disconnected_error()`: Trata erro de PLC desconectado
- `test_save_error()`: Trata erro ao salvar programa
- `test_gerber_load_error()`: Trata erro ao carregar Gerber inválido

**Arquivos:**
- Novo: `consumo_lib/exceptions/engineering_errors.py`
- Modificar: Todos os arquivos do Engineering Wizard
- Novo: `tests/integration/test_error_handling.py`

---

#### 4.3 Melhorar UX e Polimento (1 dia)
**Responsável:** Developer
**Prioridade:** Média
**Dependencies:** Todas as tarefas anteriores

**Subtarefas:**
- [ ] Adicionar barra de progresso no topo do dialog
  - [ ] Mostrar etapa atual (ex: "Etapa 3 de 7: Definir Fiduciais")
  - [ ] Barra visual preenchida proporcionalmente
- [ ] Adicionar tooltips informativos
  - [ ] Botões com explicações do que fazem
  - [ ] Campos com exemplos de formato esperado
- [ ] Adicionar atalhos de teclado
  - [ ] Ctrl+Enter: Avançar para próxima aba
    - [ ] Esc: Cancelar (com confirmação se mudanças não salvas)
- [ ] Melhorar responsividade
  - [ ] Mostrar cursor "ocupado" durante operações longas
  - [ ] Desabilitar botões durante operações assíncronas
  - [ ] Adicionar QProgressDialog para operações > 1s
- [ ] Adicionar confirmações críticas
  - [ ] Confirmar cancelamento se houver mudanças não salvas
  - [ ] Confirmar sobrescrita se programa já existe
  - [ ] Confirmar exclusão de programa

**Critérios de Sucesso:**
- Interface é intuitiva para engenheiros
- Feedback visual claro para todas as ações
- Operações longas mostram progresso
- Usuário não perde trabalho acidentalmente

**Testes:**
- `test_progress_bar()`: Barra de progresso mostra etapa correta
- `test_keyboard_shortcuts()`: Atalhos funcionam
- `test_cancel_confirmation()`: Confirma antes de cancelar
- `test_overwrite_confirmation()`: Confirma antes de sobrescrever

**Arquivos:**
- Modificar: `consumo_lib/dialogs/engineering_wizard_dialog.py`
- Modificar: Todos os widgets das abas (tooltips)
- Novo: `tests/integration/test_ux_improvements.py`

---

#### 4.4 Documentação e Comentários no Código (2 dias)
**Responsável:** Developer
**Prioridade:** Média
**Dependencies:** Todas as tarefas anteriores

**Subtarefas:**
- [ ] Adicionar docstrings Google style em todas as classes
  - [ ] EngineeringWizardDialog
  - [ ] EngineeringWizardState
  - [ ] EngineeringHardwareCoordinator
  - [ ] EngineeringProgramManager
  - [ ] EngineeringRecipeCoordinator
- [ ] Adicionar comentários em código complexo
  - [ ] Explicar lógica de validação cruzada
  - [ ] Explicar mapeamento ProgramConfig ↔ Recipe
  - [ ] Explicar tratamento de erros de hardware
  - [ ] Explicar auto-save e recuperação
- [ ] Atualizar CLAUDE.md
  - [ ] Adicionar seção "Engineering Wizard Integration"
  - [ ] Documentar novos arquivos criados
  - [ ] Atualizar diagrama de dependências
  - [ ] Adicionar exemplo de uso
- [ ] Criar guia de uso rápido
  - [ ] Arquivo: `docs/guides/engineering_wizard_usage.md`
  - [ ] Passo a passo das 7 abas
  - [ ] Screenshots (se possível)
  - [ ] Troubleshooting comum

**Critérios de Sucesso:**
- Todo código novo tem docstrings
- Lógica complexa tem comentários explicativos
- CLAUDE.md está atualizado
- Guia de uso é claro e completo

**Testes:**
- N/A (documentação)

**Arquivos:**
- Modificar: Todos os arquivos novos do Engineering Wizard
- Modificar: `CLAUDE.md`
- Novo: `docs/guides/engineering_wizard_usage.md`

---

#### 4.5 Testes End-to-End Manuais (2 dias)
**Responsível:** Developer + QA
**Prioridade:** Alta
**Dependencies:** Todas as tarefas anteriores

**Subtarefas:**
- [ ] Criar checklist de testes manuais
  - [ ] Teste 1: Fluxo completo sem hardware (modo offline)
  - [ ] Teste 2: Fluxo completo com hardware real
  - [ ] Teste 3: Salvamento e carregamento de programa
  - [ ] Teste 4: Edição de programa existente
  - [ ] Teste 5: Conversão para Recipe e uso no InspectionTab
  - [ ] Teste 6: Recuperação de auto-save após crash
  - [ ] Teste 7: Tratamento de erros de hardware
  - [ ] Teste 8: Validação cruzada entre abas
- [ ] Executar todos os testes com hardware real
  - [ ] PLC conectado
  - [ ] Câmera conectada
  - [ ] Stencil real para capturar
- [ ] Documentar bugs encontrados
- [ ] Corrigir bugs críticos imediatamente
- [ ] Criar issues para bugs não críticos

**Critérios de Sucesso:**
- Todos os testes passam sem erros críticos
- Bugs não críticos documentados
- Engenheiro pode criar programa completo sem assistência
- Programa criado funciona no InspectionTab

**Testes:**
- Manuais (checklist)

**Arquivos:**
- Novo: `docs/testing/engineering_wizard_manual_test_checklist.md`
- Modificar: Bugs encontrados (issues no GitHub ou backlog)

---

## Critérios de Conclusão da Track

### Funcional
- [ ] Engineering Wizard acessível via menu principal
- [ ] Fluxo completo de 7 abas funcional
- [ ] Programas podem ser salvos e carregados
- [ ] Integração com RecipeManager funcional
- [ ] Hardware coordination funcionando (PLC, câmera)

### Qualidade
- [ ] Testes unitários passando (≥80% cobertura)
- [ ] Testes de integração passando
- [ ] Testes manuais completados sem erros críticos
- [ ] Código documentado com docstrings e comentários
- [ ] CLAUDE.md atualizado

### Performance
- [ ] Tempo de carregamento do wizard < 1s
- [ ] Transição entre abas < 200ms
- [ ] Salvamento de programa < 500ms
- [ ] Auto-save não bloqueia UI

### Usabilidade
- [ ] Interface intuitiva
- [ ] Mensagens de erro claras
- [ ] Validação robusta
- [ ] Confirmações para ações críticas

## Riscos e Planos de Contingência

### Risco 1: Schema Incompatível com RecipeManager
**Probabilidade:** Média
**Plano de Contingência:**
- Estender schema de Recipe se necessário
- Criar campos customizados em Recipe para dados específicos do Engineering Wizard
- Documentar diferenças de schema claramente

### Risco 2: Hardware Instável Durante Testes
**Probabilidade:** Alta
**Plano de Contingência:**
- Priorizar modo offline (sem hardware)
- Criar mocks de hardware para testes automatizados
- Documentar limitações do modo offline

### Risco 3: Complexidade de Coordenação Entre Abas
**Probabilidade:** Média
**Plano de Contingência:**
- Simplificar validação cruzada se necessário
- Remover validações não críticas
- Adicionar logging extensivo para debugging

### Risco 4: Tempo Insuficiente para Testes Completos
**Probabilidade:** Média
**Plano de Contingência:**
- Priorizar testes de integração sobre testes unitários
- Focar em caminhos críticos (fluxo principal)
- Deixar testes de edge cases para fase posterior

## Próximos Passos Após Conclusão

1. **Validação com Engenheiros Reais**
   - Observar engenheiros usando o wizard
   - Coletar feedback e melhorias
   - Ajustar UX baseado em uso real

2. **Melhorias Baseadas em Feedback**
   - Adicionar recursos solicitados
   - Corrigir problemas de usabilidade
   - Otimizar fluxos baseados em comportamento real

3. **Automação de Testes**
   - Criar testes E2E automatizados
   - Integrar ao CI/CD
   - Monitorar qualidade ao longo do tempo

4. **Documentação de Usuário Final**
   - Criar manual do usuário
   - Gravar vídeos tutoriais
   - Criar FAQ de problemas comuns
