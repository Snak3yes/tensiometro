# Especificação da Track: Integrar Engineering Wizard ao Programa Principal

## Visão Geral
**Track ID:** integrate_engineering_wizard_20260113
**Tipo:** Integration
**Prioridade:** Critical
**Complexidade:** Very High (3+ semanas)
**Data de Criação:** 2026-01-13
**Estimativa:** 3-4 semanas

## Descrição Detalhada

Integrar o **Engineering Wizard** (fluxo completo de 7 abas para criação de programas de inspeção) ao programa principal Tensiometro. O código de todas as 7 abas já foi implementado (Tracks 1-7) mas ainda não está conectado à aplicação principal. Esta track deve criar a arquitetura de integração, interfaces de usuário, persistência de dados e comunicação com o sistema existente.

## Contexto e Motivação

### Código Já Implementado (Tracks 1-7)
O Engineering Wizard foi desenvolvido em 7 tracks independentes:

1. **Track 1 (Aba 1):** Dados do Programa - `consumo_lib/models/engineering/program_config.py`
2. **Track 2 (Aba 2):** Carregar Gerber - Parser e validação
3. **Track 3 (Aba 3):** Definir Fiduciais - Captura de templates
4. **Track 4 (Aba 4):** Capturar Mosaico - Grid de FOVs
5. **Track 5 (Aba 5):** Alinhamento - `consumo_lib/widgets/engenharia/alignment_widget.py` (1,036 linhas)
6. **Track 6 (Aba 6):** Janelas de Inspeção - `consumo_lib/widgets/engenharia/inspection_windows_widget.py` (886 linhas)
7. **Track 7 (Aba 7):** Confirmar e Salvar - `consumo_lib/widgets/engenharia/confirm_save_widget.py` (500 linhas)

**Status das Tracks 1-7:** ✅ TODAS COMPLETAS E TESTADAS

### Problema a Resolver
Os widgets e modelos de dados existem mas:
1. ❌ Não há um EngineeringWizardDialog/orchestrator conectando as 7 abas
2. ❌ Não há entrada no menu principal para acessar o wizard
3. ❌ Não há persistência de programas criados
4. ❌ Não há integração com RecipeManager do sistema principal
5. ❌ Não há reuse dos componentes de InspectionTab e MapTab
6. ❌ Não há coordenação com hardware (PLC, câmera, tensiômetro)

### Objetivo Final
Engenheiros devem poder criar programas de inspeção completos através de um fluxo guiado de 7 passos, salvar esses programas, e usá-los no sistema de inspeção AOI existente.

## Objetivos

### Primário
1. Criar **EngineeringWizardDialog** principal conectando todas as 7 abas
2. Adicionar entrada no **menu principal** (Ferramentas → Engineering Wizard)
3. Implementar **persistência de programas** em `data/inspection_programs/`
4. Integrar com **RecipeManager** para carregar programas salvos
5. Reutilizar componentes de **InspectionTab** e **MapTab** quando possível
6. Implementar coordenação com **hardware** (PLC, câmera)

### Secundário
1. Criar botão de "Novo Programa" na Interface principal
2. Implementar lista de programas recentes
3. Adicionar opção de editar programas existentes
4. Suportar exportação/importação de programas
5. Adicionar atalhos de teclado para fluxo rápido

## Alcance (Scope)

### INCLUÍDO
✅ **Arquitetura de Integração**
  - EngineeringWizardDialog (orchestrator das 7 abas)
  - EngineeringWizardCoordinator (coordenação com hardware)
  - EngineeringWizardController (controle de fluxo)

✅ **Interface do Usuário**
  - Menu entry: "Ferramentas → Engineering Wizard"
  - Botão na toolbar: "Novo Programa de Inspeção"
  - Dialog principal com QTabWidget ou QStackedWidget
  - Botões de navegação: Anterior, Próximo, Cancelar, Concluir

✅ **Gerenciamento de Estado**
  - StateManager para compartilhar dados entre abas
  - Validação cruzada entre abas
  - Auto-save em cada transição de aba

✅ **Persistência de Dados**
  - Salvamento em JSON (`data/inspection_programs/{program_name}.json`)
  - Carregamento de programas existentes
  - Listagem de programas disponíveis
  - Versionamento simples (v1, v2, ...)

✅ **Integração com RecipeManager**
  - Converter ProgramConfig → Recipe
  - Carregar Recipe no InspectionTab
  - Editar Recipe via Engineering Wizard

✅ **Coordenação de Hardware**
  - Acesso a CameraController (abas 3, 4)
  - Acesso a PLCAxisController (aba 4)
  - Acesso a FiducialAligner (aba 5)

✅ **Testes**
  - Testes de unidade para novos componentes
  - Testes de integração do fluxo completo
  - Testes manuais com hardware real

✅ **Documentação**
  - Comentários no código explicando integrações
  - Atualização de CLAUDE.md com nova arquitetura
  - Guia de uso do Engineering Wizard

### EXCLUÍDO
❌ Modificações em widgets existentes das Tracks 1-7 (considerados estáveis)
❌ Implementação de novas funcionalidades de inspeção (runtime)
❌ Automação completa de testes de hardware
❌ Interface web ou API REST
❌ Versionamento avançado de programas (branches, merge)
❌ Permissões complexas por usuário

## Requisitos Funcionais

### RF1. Dialog Principal do Engineering Wizard
**Prioridade:** Alta
**Descrição:** Criar dialog principal conectando todas as 7 abas

**Critérios:**
- [ ] Janela QDialog com tamanho mínimo 1200x800
- [ ] QTabWidget com 7 tabs (ou QStackedWidget com navegação linear)
- [ ] Barra de título: "Engineering Wizard - Novo Programa de Inspeção"
- [ ] Barra de progresso mostrando etapa atual (1/7, 2/7, ...)
- [ ] Botões: Anterior, Próximo, Cancelar, Concluir
- [ ] Validação: não permite avançar se aba atual inválida
- [ ] Auto-save: salva estado parcial ao mudar de aba

**Especificações Técnicas:**
```python
# consumo_lib/dialogs/engineering_wizard_dialog.py
class EngineeringWizardDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Engineering Wizard - Novo Programa de Inspeção")
        self.setMinimumSize(1200, 800)

        # State manager (compartilhado entre abas)
        self.state = EngineeringWizardState()

        # 7 tabs
        self.tabs = QTabWidget()
        self.tab1 = ProgramDataWidget(self.state)
        self.tab2 = GerberUploadWidget(self.state)
        self.tab3 = FiducialCaptureWidget(self.state)
        self.tab4 = MosaicCaptureWidget(self.state)
        self.tab5 = AlignmentWidget(self.state)
        self.tab6 = InspectionWindowsWidget(self.state)
        self.tab7 = ConfirmSaveWidget(self.state)

        # Connect signals
        self.tab1.validationChanged.connect(self.on_validation_changed)
        # ... (todas as 7 abas)

        # Navigation buttons
        self.btn_back = QPushButton("← Anterior")
        self.btn_next = QPushButton("Próximo →")
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_finish = QPushButton("Concluir")  # só visível na aba 7
```

### RF2. State Manager Compartilhado
**Prioridade:** Alta
**Descrição:** Gerenciar estado compartilhado entre as 7 abas

**Critérios:**
- [ ] Instância única de EngineeringWizardState compartilhada
- [ ] Getter/setter para cada dado de aba (aba1_data, aba2_data, etc.)
- [ ] Validação cruzada (ex: aba 2 depende de aba 1)
- [ ] Auto-save em cada mudança de estado
- [ ] Load de estado parcial (retomar programa em andamento)

**Especificações Técnicas:**
```python
# consumo_lib/models/engineering/wizard_state.py
@dataclass
class EngineeringWizardState:
    """Estado compartilhado entre as 7 abas do Engineering Wizard."""

    # Aba 1: Dados do Programa
    program_data: Optional[ProgramData] = None

    # Aba 2: Arquivo Gerber
    gerber_file: Optional[str] = None
    gerber_data: Optional[GerberData] = None

    # Aba 3: Fiduciais
    fiducial_templates: List[FiducialTemplate] = field(default_factory=list)

    # Aba 4: Mosaico
    mosaic_image: Optional[np.ndarray] = None
    mosaic_config: Optional[MosaicConfig] = None

    # Aba 5: Alinhamento
    alignment_transform: Optional[AlignmentTransform] = None

    # Aba 6: Janelas de Inspeção
    inspection_groups: List[WindowGroup] = field(default_factory=list)

    # Metadados
    current_tab: int = 0
    is_dirty: bool = False
    auto_save_path: Optional[str] = None

    def is_valid(self, tab_index: int) -> bool:
        """Valida se a aba específica tem dados completos."""
        if tab_index == 0:
            return self.program_data is not None
        elif tab_index == 1:
            return self.gerber_data is not None
        # ... (validação para cada aba)

    def to_dict(self) -> Dict:
        """Serializa estado para JSON (auto-save)."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'EngineeringWizardState':
        """Desserializa estado do JSON."""
        return cls(**data)
```

### RF3. Menu Integration
**Prioridade:** Alta
**Descrição:** Adicionar entrada no menu principal

**Critérios:**
- [ ] Menu "Ferramentas" → "Engineering Wizard"
- [ ] Toolbar button: ícone + tooltip "Novo Programa de Inspeção"
- [ ] Atalho de teclado: Ctrl+Shift+E
- [ ] Menu "Programas" → "Listar Programas Salvos"
- [ ] Menu "Programas" → "Carregar Programa..."

**Especificações Técnicas:**
```python
# consumo_lib/handlers/menu_handler.py (extensão)
class MenuHandler:
    def setup_engineering_menu(self):
        # Menu Ferramentas
        tools_menu = self.main_menu.addMenu("&Ferramentas")
        tools_menu.addAction("Engineering Wizard...", self.open_engineering_wizard, QKeySequence("Ctrl+Shift+E"))

        # Menu Programas (novo)
        programs_menu = self.main_menu.addMenu("&Programas")
        programs_menu.addAction("Listar Programas Salvos...", self.list_saved_programs)
        programs_menu.addAction("Carregar Programa...", self.load_program)

    def open_engineering_wizard(self):
        dialog = EngineeringWizardDialog(self.main_window)
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            program = dialog.get_final_program()
            self.save_program(program)
```

### RF4. Persistência de Programas
**Prioridade:** Alta
**Descrição:** Salvar e carregar programas de inspeção

**Critérios:**
- [ ] Salvar em `data/inspection_programs/{program_name}.json`
- [ ] Converter ProgramConfig → JSON schema
- [ ] Listar todos os programas salvos
- [ ] Carregar programa existente (modo edição)
- [ ] Sobrescrever com confirmação
- [ ] Metadata: data de criação, última modificação, versão

**Especificações Técnicas:**
```python
# consumo_lib/managers/engineering_program_manager.py
class EngineeringProgramManager:
    """Gerencia persistência de programas de inspeção."""

    PROGRAMS_DIR = Path("data/inspection_programs")

    def save_program(self, program: ProgramConfig) -> Path:
        """Salva programa em JSON."""
        self.PROGRAMS_DIR.mkdir(parents=True, exist_ok=True)
        filename = f"{program.program_name}.json"
        filepath = self.PROGRAMS_DIR / filename

        data = program.to_dict()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return filepath

    def load_program(self, program_name: str) -> ProgramConfig:
        """Carrega programa do JSON."""
        filepath = self.PROGRAMS_DIR / f"{program_name}.json"
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return ProgramConfig.from_dict(data)

    def list_programs(self) -> List[Dict]:
        """Lista metadados de todos os programas."""
        programs = []
        for filepath in self.PROGRAMS_DIR.glob("*.json"):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            programs.append({
                'name': data.get('program_name'),
                'created_at': data.get('created_at'),
                'stencil_code': data.get('stencil_code'),
            })
        return programs
```

### RF5. Integração com RecipeManager
**Prioridade:** Alta
**Descrição:** Converter ProgramConfig para Recipe do sistema

**Critérios:**
- [ ] Converter ProgramConfig → Recipe (schema existente)
- [ ] Carregar Recipe no InspectionTab após salvar
- [ ] Editar Recipe existente via Engineering Wizard
- [ ] Sincronizar metadados (stencil_code, program_name)

**Especificações Técnicas:**
```python
# consumo_lib/coordinators/engineering_recipe_coordinator.py
class EngineeringRecipeCoordinator:
    """Coordena conversão entre ProgramConfig e Recipe."""

    def program_to_recipe(self, program: ProgramConfig) -> Recipe:
        """Converte ProgramConfig para Recipe do sistema."""
        recipe = Recipe(
            name=program.program_name,
            stencil_code=program.stencil_code,
            description=program.description,
            # Mapear campos do ProgramConfig para Recipe
            gerber_file=program.gerber_file,
            fiducial_positions=program.fiducial_positions,
            alignment_transform=program.alignment_transform,
            inspection_windows=program.inspection_groups,
            # ...
        )
        return recipe

    def recipe_to_program(self, recipe: Recipe) -> ProgramConfig:
        """Converte Recipe existente para ProgramConfig (edição)."""
        return ProgramConfig(
            program_name=recipe.name,
            stencil_code=recipe.stencil_code,
            # ... (mapeamento inverso)
        )
```

### RF6. Coordenação de Hardware
**Prioridade:** Média
**Descrição:** Fornecer acesso a hardware para as abas do wizard

**Critérios:**
- [ ] Aba 3 (Fiduciais): acessar CameraController
- [ ] Aba 4 (Mosaico): acessar PLCAxisController + CameraController
- [ ] Aba 5 (Alinhamento): acessar FiducialAligner
- [ ] Verificar conexão antes de permitir operações
- [ ] Mostrar mensagens de erro claras se hardware indisponível

**Especificações Técnicas:**
```python
# consumo_lib/coordinators/engineering_hardware_coordinator.py
class EngineeringHardwareCoordinator:
    """Coordena acesso a hardware durante Engineering Wizard."""

    def __init__(self, main_window):
        self.main_window = main_window
        self.camera = main_window.camera_controller
        self.plc = main_window.plc_controller
        self.fiducial_aligner = main_window.fiducial_aligner

    def is_hardware_ready(self, required: List[str]) -> Tuple[bool, str]:
        """Verifica se hardware necessário está conectado."""
        if 'camera' in required and not self.camera.is_connected:
            return False, "Câmera não conectada"
        if 'plc' in required and not self.plc.is_connected:
            return False, "PLC não conectado"
        return True, ""

    def capture_fiducial_template(self, x: float, y: float) -> np.ndarray:
        """Captura template de fiducial (Aba 3)."""
        # Mover para posição
        self.plc.move_absolute('X', x)
        self.plc.move_absolute('Y', y)
        self.plc.wait_for_idle()

        # Capturar imagem
        frame = self.camera.capture_frame()
        return frame

    def capture_mosaic_grid(self, grid_config: MosaicConfig) -> np.ndarray:
        """Captura mosaico (Aba 4)."""
        # Reutilizar MapGeneratorThread existente
        pass
```

### RF7. Validação Cruzada entre Abas
**Prioridade:** Média
**Descrição:** Validar dependências entre abas

**Critérios:**
- [ ] Aba 2 só válida se Aba 1 preenchida
- [ ] Aba 3 só válida se Aba 2 carregou Gerber
- [ ] Aba 4 só válida se Aba 3 capturou fiduciais
- [ ] Aba 5 só válida se Aba 4 capturou mosaico
- [ ] Aba 6 só válida se Aba 5 aplicou alinhamento
- [ ] Aba 7 só válida se todas as anteriores completas

**Especificações Técnicas:**
```python
# consumo_lib/models/engineering/wizard_state.py (continuação)
class EngineeringWizardState:
    def validate_dependencies(self, tab_index: int) -> Tuple[bool, str]:
        """Valida dependências de outras abas."""
        if tab_index == 1:  # Aba 2 (Gerber)
            if self.program_data is None:
                return False, "Preencha os dados do programa primeiro (Aba 1)"
        elif tab_index == 2:  # Aba 3 (Fiduciais)
            if self.gerber_data is None:
                return False, "Carregue o arquivo Gerber primeiro (Aba 2)"
        # ... (validação para cada aba)
        return True, ""
```

### RF8. Auto-Save e Recuperação
**Prioridade:** Média
**Descrição:** Salvar estado parcial automaticamente

**Critérios:**
- [ ] Salvar estado ao mudar de aba
- [ ] Salvar estado a cada 2 minutos
- [ ] Detectar programas não salvos ao fechar
- [ ] Recuperar programa interrompido
- [ ] Limpar autosaves após conclusão

**Especificações Técnicas:**
```python
# consumo_lib/dialogs/engineering_wizard_dialog.py (continuação)
class EngineeringWizardDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # ...
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save)
        self.auto_save_timer.start(120000)  # 2 minutos

    def on_tab_changed(self, index: int):
        """Salva estado ao mudar de aba."""
        self.auto_save()
        self.current_tab = index

    def auto_save(self):
        """Salva estado parcial."""
        if self.state.is_dirty:
            filepath = self.state.auto_save_path or self._generate_autosave_path()
            self.save_state(filepath)
            self.state.is_dirty = False

    def closeEvent(self, event):
        """Detecta programa não salvo ao fechar."""
        if self.state.is_dirty:
            reply = QMessageBox.question(
                self, "Programa Não Salvo",
                "Deseja salvar o programa antes de fechar?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
            )
            if reply == QMessageBox.StandardButton.Save:
                self.save_program()
            elif reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
        event.accept()
```

## Requisitos Não-Funcionais

### RNF1. Performance
- Tempo de carregamento do wizard: < 1 segundo
- Transição entre abas: < 200ms
- Salvamento de programa: < 500ms
- Auto-save não deve bloquear UI (async/thread)

### RNF2. Usabilidade
- Interface intuitiva com progresso claro
- Mensagens de erro específicas e acionáveis
- Atalhos de teclado para usuários avançados
- Undo/Undo limitado (última ação em cada aba)

### RNF3. Confiabilidade
- Auto-save preventivo contra perda de dados
- Validação robusta de dados de entrada
- Recuperação graceful de erros de hardware
- Logging extensivo para debugging

### RNF4. Compatibilidade
- Não deve quebrar funcionalidades existentes
- Deve funcionar sem hardware (modo offline)
- Deve ser compatível com RecipeManager atual

## Arquitetura Proposta

### Componentes Principais

```
consumo_lib/
├── dialogs/
│   └── engineering_wizard_dialog.py          (NOVO - orchestrator)
├── coordinators/
│   ├── engineering_hardware_coordinator.py   (NOVO - hardware access)
│   ├── engineering_recipe_coordinator.py     (NOVO - recipe conversion)
│   └── engineering_flow_coordinator.py       (NOVO - workflow orchestration)
├── managers/
│   └── engineering_program_manager.py        (NOVO - persistence)
├── models/
│   └── engineering/
│       ├── wizard_state.py                   (NOVO - shared state)
│       └── program_config.py                 (JÁ EXISTE - Track 7)
├── widgets/
│   └── engenharia/                           (JÁ EXISTE - Tracks 5,6,7)
│       ├── alignment_widget.py
│       ├── inspection_windows_widget.py
│       └── confirm_save_widget.py
└── handlers/
    └── menu_handler.py                       (MODIFICAR - add menu entry)
```

### Fluxo de Dados

```
User Action (Menu "Engineering Wizard")
    ↓
MenuHandler.open_engineering_wizard()
    ↓
EngineeringWizardDialog.__init__()
    ↓
EngineeringWizardState (compartilhado)
    ↓
7 Tabs (Widgets já existentes)
    ├── Tab 1: ProgramDataWidget
    ├── Tab 2: GerberUploadWidget
    ├── Tab 3: FiducialCaptureWidget
    ├── Tab 4: MosaicCaptureWidget
    ├── Tab 5: AlignmentWidget
    ├── Tab 6: InspectionWindowsWidget
    └── Tab 7: ConfirmSaveWidget
    ↓
EngineeringProgramManager.save_program()
    ↓
data/inspection_programs/{program_name}.json
    ↓
EngineeringRecipeCoordinator.program_to_recipe()
    ↓
RecipeManager (sistema existente)
```

### Diagrama de Interação

```
┌─────────────────────────────────────────────────────────────┐
│                    MainWindow                                │
│  ┌────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │MenuHandler│  │ResourceManager│  │  SetupCoordinator  │  │
│  └─────┬──────┘  └──────┬───────┘  └─────────┬──────────┘  │
│        │                 │                    │              │
│        ▼                 ▼                    ▼              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         EngineeringWizardDialog (NEW)                │  │
│  │  ┌──────────────────────────────────────────────┐   │  │
│  │  │      EngineeringWizardState (shared)         │   │  │
│  │  └──────────────────────────────────────────────┘   │  │
│  │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐│  │
│  │  │Tab 1│ │Tab 2│ │Tab 3│ │Tab 4│ │Tab 5│ │Tab 6│ │Tab 7││  │
│  │  └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘│  │
│  │     │       │       │       │       │       │       │    │  │
│  └─────┼───────┼───────┼───────┼───────┼───────┼───────┼────┘
│        │       │       │       │       │       │       │
│  ┌─────┼───────┼───────┼───────┼───────┼───────┼───────┼────┐
│  │     │       │       │       │       │       │       │    │
│  ▼     ▼       ▼       ▼       ▼       ▼       ▼       ▼    │
│ ┌────────────────────────────────────────────────────────┐ │
│ │         EngineeringHardwareCoordinator                 │ │
│ │  (CameraController, PLCController, FiducialAligner)    │ │
│ └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              EngineeringProgramManager (NEW)                │
│  save_program() → data/inspection_programs/*.json           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│           EngineeringRecipeCoordinator (NEW)                │
│  program_to_recipe() → Recipe (sistema existente)           │
└─────────────────────────────────────────────────────────────┘
```

## Backward Compatibility

### Impacto no Código Existente
**Mudanças Aditivas (não quebram código existente):**
- ✅ Novo menu em MenuHandler (aditivo)
- ✅ Nova classe EngineeringWizardDialog (aditivo)
- ✅ Novos coordinators (aditivo)
- ✅ Nova pasta `data/inspection_programs/` (aditivo)

**Mudanças Modificativas (requerem cuidado):**
- ⚠️ RecipeManager: pode precisar de novos métodos
- ⚠️ MainWindow: inicialização de novos coordinators

**Mudanças Não Quebradoras:**
- ✅ Widgets existentes (InspectionTab, MapTab) não são modificados
- ✅ aoi_lib permanece inalterado
- ✅ Controllers existentes não são modificados

### Estratégia de Migração
1. Fase 1: Criar novos componentes isoladamente
2. Fase 2: Conectar ao menu principal (ponto de entrada único)
3. Fase 3: Testar integração com RecipeManager
4. Fase 4: Atualizar documentação

### Rollback Plan
Se necessário, rollback é simples:
```bash
# Revert commit da integração
git revert <commit-hash>

# Remove arquivos criados
rm -rf consumo_lib/dialogs/engineering_wizard_dialog.py
rm -rf consumo_lib/coordinators/engineering_*
rm -rf consumo_lib/managers/engineering_program_manager.py
rm -rf consumo_lib/models/engineering/wizard_state.py
rm -rf data/inspection_programs/
```

## Riscos e Mitigações

### Risco 1: Complexidade de Coordenação
**Probabilidade:** Alta
**Impacto:** Alto
**Descrição:** Coordenar 7 abas com estado compartilhado é complexo

**Mitigação:**
- StateManager centralizado e bem testado
- Validação rigorosa em cada transição
- Logging extensivo para debugging
- Testes de integração exaustivos

### Risco 2: Conflitos com RecipeManager
**Probabilidade:** Média
**Impacto:** Médio
**Descrição:** Schema de ProgramConfig pode não mapear perfeitamente para Recipe

**Mitigação:**
- EngineeringRecipeCoordinator isolado
- Mapeamento flexível com defaults
- Testes de conversão bidirecional
- Documentação de diferenças de schema

### Risco 3: Performance com Mosaicos Grandes
**Probabilidade:** Média
**Impacto:** Médio
**Descrição:** Mosaicos de alta resolução podem consumir muita memória

**Mitigação:**
- Limitar tamanho do mosaico (ex: 8x8 FOVs)
- Compressão de imagens no auto-save
- Liberar memória ao fechar wizard
- Modo "preview" com resolução reduzida

### Risco 4: Hardware Não Disponível
**Probabilidade:** Alta
**Impacto:** Baixo
**Descrição:** Usuário pode abrir wizard sem PLC/câmera conectados

**Mitigação:**
- Validação de hardware antes de operações críticas
- Modo offline para abas que não dependem de hardware
- Mensagens de erro claras e acionáveis
- Desabilitar controles quando hardware indisponível

## Critérios de Sucesso

### Medíveis
- [ ] Engineering Wizard acessível via menu principal
- [ ] Fluxo completo de 7 abas funcional sem erros
- [ ] Programas salvos em JSON carregáveis
- [ ] Integração com RecipeManager funcional
- [ ] Testes de integração passando (≥80% cobertura)
- [ ] Tempo de resposta < 1s em todas as operações

### Qualitativos
- [ ] Interface intuitiva para engenheiros
- [ ] Documentação clara de uso
- [ ] Código bem estruturado e manutenível
- [ ] Logging adequado para troubleshooting
- [ ] Retrocompatibilidade preservada

## Dependencies

### Internas (Projeto)
- ✅ Tracks 1-7 completadas (widgets + modelos)
- ✅ MainWindow funcional
- ✅ RecipeManager implementado
- ✅ CameraController, PLCAxisController funcionais
- ✅ FiducialAligner implementado

### Externas (Bibliotecas)
- PyQt6 (já usado)
- Python 3.10+ (já usado)
- OpenCV (já usado)
- pathlib (já usado)

### Recursos
- Desenvolvedor senior (3-4 semanas)
- Acesso a hardware para testes (PLC, câmera)
- Tempo para validação com engenheiros

## Timeline Estimada

### Fase 1: Arquitetura e State Manager (Semana 1)
- Criar EngineeringWizardState
- Criar EngineeringWizardDialog (esqueleto)
- Implementar navegação entre abas
- Testes unitários do state manager

### Fase 2: Hardware Coordinator e Menu (Semana 2)
- Criar EngineeringHardwareCoordinator
- Adicionar menu entry e toolbar button
- Conectar abas 3, 4, 5 ao hardware
- Testes de integração com hardware

### Fase 3: Persistência e Recipe Integration (Semana 3)
- Criar EngineeringProgramManager
- Criar EngineeringRecipeCoordinator
- Implementar salvamento/carregamento
- Testes de conversão ProgramConfig ↔ Recipe

### Fase 4: Validação, Polimento e Documentação (Semana 4)
- Validação cruzada entre abas
- Auto-save e recuperação
- Tratamento de erros e edge cases
- Documentação e código comments
- Testes end-to-end manuais

## Referências

### Documentos Relacionados
- `CLAUDE.md` - Documentação principal do projeto
- `consumo_lib/models/engineering/program_config.py` - Modelo de dados (Track 7)
- `consumo_lib/widgets/engenharia/*` - Widgets das Tracks 5,6,7
- `conductor/tracks/engenharia_aba*_*/spec.md` - Especificações das Tracks 1-7
- `docs/reports/TRACK6_SUMMARY.md` - Resumo da implementação das abas

### Padrões de Projeto
- State Pattern para gerenciar estado do wizard
- Coordinator Pattern para orquestrar componentes
- Repository Pattern para persistência
- Observer Pattern (signals/slots) para comunicação

### Decisões Arquiteturais
1. **QTabWidget vs QStackedWidget**: QTabWidget permite acesso direto a qualquer aba (melhor para debugging)
2. **Centralized State**: StateManager único em vez de passar dados entre abas
3. **Auto-save Async**: Salvamento em thread separado para não bloquear UI
4. **Hardware Abstraction**: HardwareCoordinator isola dependências de hardware
