# 📋 Plano de Refactoring - consumo_lib.py

**Data:** 03/01/2026
**Arquivo Alvo:** consumo_lib.py (6.245 linhas)
**Objetivo:** Dividir em módulos coesos e manteníveis
**Estimativa:** 10-15 dias de trabalho

---

## 📊 Análise da Estrutura Atual

### Classes Identificadas (13 classes + 1 main)

```python
1. TensionVisualizationWidget   (58-393)   - Visualização de tensão
2. TensionCanvas                (394-616)  - Canvas de desenho
3. ImageViewerWidget            (617-659)  - Visualizador de imagens
4. PositionListWidget           (660-725)  - Lista de posições
5. SequenceControlWidget        (726-775)  - Controle de sequência
6. PositionRegistryWidget       (776-852)  - Registro de posições
7. CameraPreviewWidget          (853-1098) - Preview de câmera
8. MovementControlWidget        (1099-1743) - Controle de movimento
9. PLCMonitorWidget             (1744-1915) - Monitor PLC
10. MapParams                    (1916-1924) - DTO de parâmetros
11. _PreviewSuspender            (1925-1941) - Context manager
12. AOIControllerApp             (1942-6079) - MAIN WINDOW (4.138 linhas) 🔴
13. SequenceRunnerThread         (6080-6102) - Thread sequenciador
14. MapGeneratorThread           (6103-6127) - Thread gerador de mapa
```

### Problema Principal
**AOIControllerApp** tem **113 métodos** em **4.138 linhas** - uma classe monolítica que faz tudo.

---

## 🏗️ Estrutura Proposta

```
consumo_lib/                    # NOVO PACOTE
│
├── __init__.py                 # Exporta AOIControllerApp
├── main_window.py              # AOIControllerApp simplificada (~800 linhas)
│
├── widgets/                    # Widgets reusáveis (existentes e novos)
│   ├── __init__.py
│   ├── tension_viz.py          # TensionVisualizationWidget + TensionCanvas
│   ├── image_viewer.py         # ImageViewerWidget
│   ├── position_list.py        # PositionListWidget
│   ├── sequence_control.py     # SequenceControlWidget
│   ├── position_registry.py    # PositionRegistryWidget
│   ├── camera_preview.py       # CameraPreviewWidget
│   ├── movement_control.py     # MovementControlWidget
│   ├── plc_monitor.py          # PLCMonitorWidget
│   └── preview_suspender.py    # _PreviewSuspender
│
├── tabs/                       # Novo: Abas da aplicação
│   ├── __init__.py
│   ├── base_tab.py             # Base class para todas as abas
│   ├── cnc_control_tab.py      # Aba "Controle CNC"
│   ├── tension_tab.py          # Aba "Medição Tensão"
│   ├── inspection_tab.py       # Aba "Inspeção Visual"
│   ├── tracking_tab.py         # Aba "Rastreabilidade"
│   └── map_tab.py              # Aba "Mapa/Índice"
│
├── managers/                   # Novo: Gerenciadores de funcionalidades
│   ├── __init__.py
│   ├── connection_manager.py   # Gerencia conexões (PLC + Câmera)
│   ├── recipe_manager.py       # Wrapper para RecipeManager com UI
│   ├── stencil_manager.py      # Wrapper para StencilTracker com UI
│   ├── inspection_manager.py   # Gerencia workflow de inspeção
│   ├── report_manager.py       # Gerencia geração de relatórios
│   ├── map_manager.py          # Gerencia programas de mapa
│   └── calibration_manager.py  # Gerencia calibração de câmera
│
├── dialogs/                    # Novo: Diálogos específicos
│   ├── __init__.py
│   ├── camera_settings_dialog.py
│   ├── fov_calibration_dialog.py
│   ├── crosshair_settings_dialog.py
│   ├── fiducial_alignment_dialog.py
│   ├── inspection_settings_dialog.py
│   ├── report_settings_dialog.py
│   ├── calibration_test_dialog.py
│   ├── about_dialog.py
│   └── settings_dialog.py
│
├── threads/                    # Novo: Threads workers
│   ├── __init__.py
│   ├── sequence_runner.py      # SequenceRunnerThread
│   └── map_generator.py        # MapGeneratorThread
│
└── utils/                      # Novo: Helpers
    ├── __init__.py
    ├── position_display.py     # Formatação de posição
    ├── wcs_manager.py          # Gerenciamento de WCS
    └── keyboard_handler.py     # Filtro de eventos de teclado
```

---

## 📋 Análise Detalhada dos Métodos da AOIControllerApp

### Agrupamento por Responsabilidade (113 métodos identificados)

#### 1. **INICIALIZAÇÃO E CONFIGURAÇÃO** (8 métodos)
```python
__init__                        # Inicialização da aplicação
_attempt_auto_connect           # Conexão automática ao iniciar
_show_plc_connection_error      # Mostra erro de conexão PLC
_cleanup_resources              # Limpeza ao fechar
closeEvent                      # Evento de fechamento
_init_report_generator          # Inicializa gerador de relatórios
_init_inspection_system         # Inicializa sistema de inspeção
setup_ui                        # Configura interface (retorna para dividir)
```

#### 2. **CONEXÕES (PLC + CÂMERA)** (5 métodos)
```python
connect_cnc                     # Conecta/desconecta PLC
connect_camera                  # Conecta câmera
test_camera                     # Testa câmera
refresh_ports                   # Atualiza lista de portas
_apply_plc_ui_settings          # Aplica configurações PLC na UI
```

#### 3. **INTERFACE DO USUÁRIO - MENU** (35+ métodos)
```python
setup_menu                      # Configura menu principal
# Submenu: Ferramentas
open_stencil_tension_dialog     # Diálogo de medição de tensão
show_recipe_manager             # Gerenciador de receitas
show_new_recipe_dialog          # Nova receita
show_stencil_manager            # Gerenciador de stencils
show_new_stencil_dialog         # Novo stencil
show_mosaic_builder             # Builder de mosaico
show_camera_calibration_dialog  # Calibração de câmera
show_fov_calibration_dialog     # Calibração FOV
show_crosshair_settings_dialog  # Configura cruz de centralização
show_fiducial_alignment_dialog  # Alinhamento de fiduciais
show_inspection_settings        # Configurações de inspeção
show_inspection_dialog          # Executa inspeção visual
show_camera_settings_dialog     # Configurações de câmera
show_settings_dialog            # Preferências gerais
show_calibration_dialog         # Diálogo de calibração
show_calibration_test_dialog    # Teste de calibração
show_about_dialog               # Sobre o sistema
show_definir_mapa_dialog        # Definir programa de mapa
# Submenu: Relatórios
show_report_settings            # Configurações de relatório
show_tension_report_dialog      # Relatório de tensão
show_stencil_report_dialog      # Relatório de stencil
show_period_query_dialog        # Consulta por período
# Submenu: Ajuda (se houver)
```

#### 4. **GERENCIAMENTO DE RECEITAS** (4 métodos)
```python
_on_recipe_loaded              # Callback quando receita carregada
apply_recipe_to_capture        # Aplica receita à captura
apply_recipe_to_tension        # Aplica receita à tensão
_on_recipe_requested           # Callback quando receita solicitada
```

#### 5. **GERENCIAMENTO DE STENCILS** (4 métodos)
```python
_on_stencil_selected           # Callback quando stencil selecionado
_on_stencil_cleared            # Callback quando stencil limpo
_save_tension_to_history       # Salva medição no histórico
```

#### 6. **MEDIÇÃO DE TENSÃO** (1 método principal)
```python
_run_tension_measurement       # Executa medição de tensão
```

#### 7. **INSPEÇÃO VISUAL** (9 métodos)
```python
_browse_inspection_gerber      # Seleciona arquivo Gerber
_browse_inspection_mosaic      # Seleciona mosaico
_run_inspection                # Executa inspeção
_open_fiducial_alignment_from_inspection  # Abre alinhamento
_show_inspection_result        # Mostra resultado
export_pdf                     # Exporta PDF do resultado
show_last_inspection_result    # Mostra última inspeção
```

#### 8. **CONFIGURAÇÕES DE CÂMERA** (13 métodos)
```python
_gather_camera_settings        # Coleta configurações atuais
_apply_current_camera_settings # Aplica configurações
_apply_camera_prop             # Aplica propriedade específica
_apply_focus_mode              # Modo de foco
_reset_camera_props            # Reseta propriedades
_apply_mirror_settings         # Aplica espelhamento
_load_camera_presets_into_combo # Carrega presets
_save_current_camera_preset    # Salva preset
_load_selected_camera_preset   # Carrega preset
_export_current_camera_settings # Exporta configurações
# ... (diálogos internos)
```

#### 9. **PROGRAMAÇÃO DE MAPA** (13 métodos)
```python
_select_map_folder             # Seleciona pasta
_define_map_corner             # Define canto do mapa
_update_adjusted_step_info     # Atualiza informação de passo
_refresh_map_programs          # Atualiza lista de programas
_save_map_program              # Salva programa
_on_load_map_program_clicked   # Handler de carregamento
_load_map_program              # Carrega programa
_delete_map_program            # Deleta programa
_on_generate_map               # Handler de geração
_collect_map_params            # Coleta parâmetros
_start_map_thread              # Inicia thread
_on_map_progress               # Progresso do mapa
_on_map_finished               # Mapa finalizado
_on_map_error                  # Erro no mapa
```

#### 10. **CALIBRAÇÃO** (5 métodos)
```python
apply_calibration              # Aplica calibração
test_calibration_move          # Testa movimento calibrado
_show_calibration_result       # Mostra resultado
verify_calibration_result      # Verifica resultado
```

#### 11. **MOVIMENTO E POSIÇÃO** (8 métodos)
```python
update_position_display        # Atualiza display de posição
add_current_position           # Adiciona posição atual
remove_position                # Remove posição
on_position_selected           # Handler de seleção
get_current_feed_rate          # Feed rate atual
on_image_captured             # Callback de captura
create_sequence_from_registry  # Cria sequência
```

#### 12. **SEQUÊNCIAS** (6 métodos)
```python
load_gcode                     # Carrega G-code
create_sequence                # Cria sequência manual
run_sequence                   # Executa sequência
stop_sequence                  # Para sequência
on_sequence_completed          # Sequência finalizada
on_sequence_error              # Erro na sequência
on_sequence_image_captured     # Imagem capturada na sequência
```

#### 13. **PROGRAMAÇÃO** (2 métodos)
```python
save_program                   # Salva programa
load_program                   # Carrega programa
```

#### 14. **BACKLIGHT** (1 método)
```python
_sync_backlight_button         # Sincroniza botão backlight
```

#### 15. **EVENTOS E TIMERS** (3 métodos)
```python
eventFilter                    # Filtro de eventos globais
on_update_timer                # Timer de atualização
```

---

## 🔄 Plano de Refactoring - Fase a Fase

### FASE 1: Preparação e Infraestrutura (Dia 1-2)

**Objetivo:** Criar estrutura de diretórios e mover classes existentes.

#### Tarefas:

1. **Criar estrutura de pacotes**
```bash
mkdir -p consumo_lib/{widgets,tabs,managers,dialogs,threads,utils}
touch consumo_lib/__init__.py
touch consumo_lib/widgets/__init__.py
touch consumo_lib/tabs/__init__.py
touch consumo_lib/managers/__init__.py
touch consumo_lib/dialogs/__init__.py
touch consumo_lib/threads/__init__.py
touch consumo_lib/utils/__init__.py
```

2. **Mover widgets existentes (sem alterações)**
```python
# movimento simples de código - apenas cut/paste
consumo_lib.py:TensionVisualizationWidget → widgets/tension_viz.py
consumo_lib.py:TensionCanvas → widgets/tension_viz.py
consumo_lib.py:ImageViewerWidget → widgets/image_viewer.py
consumo_lib.py:PositionListWidget → widgets/position_list.py
consumo_lib.py:SequenceControlWidget → widgets/sequence_control.py
consumo_lib.py:PositionRegistryWidget → widgets/position_registry.py
consumo_lib.py:CameraPreviewWidget → widgets/camera_preview.py
consumo_lib.py:MovementControlWidget → widgets/movement_control.py
consumo_lib.py:PLCMonitorWidget → widgets/plc_monitor.py
consumo_lib.py:_PreviewSuspender → widgets/preview_suspender.py
consumo_lib.py:MapParams → utils/map_params.py
consumo_lib.py:SequenceRunnerThread → threads/sequence_runner.py
consumo_lib.py:MapGeneratorThread → threads/map_generator.py
```

3. **Atualizar imports no arquivo principal**
```python
# Antes: (tudo no mesmo arquivo)
# Depois:
from consumo_lib.widgets import (
    TensionVisualizationWidget, CameraPreviewWidget,
    MovementControlWidget, ...
)
```

**Entregáveis:**
- ✅ Estrutura de diretórios criada
- ✅ Widgets movidos sem quebrar funcionalidade
- ✅ consumo_lib.py funciona igual ao antes

---

### FASE 2: Extrair Managers (Dia 3-5)

**Objetivo:** Criar camada de gerenciadores para desacoplar lógica de negócio da UI.

#### 2.1 ConnectionManager (Dia 3)
**Responsabilidade:** Gerenciar conexões PLC e Câmera

```python
# consumo_lib/managers/connection_manager.py
class ConnectionManager(QObject):
    """Gerencia conexões de hardware (PLC + Câmera)."""

    # Signals
    plc_connected = pyqtSignal()
    plc_disconnected = pyqtSignal()
    plc_connection_error = pyqtSignal(str)
    camera_connected = pyqtSignal()
    camera_disconnected = pyqtSignal()

    def __init__(self, controller: CNCAOIController, config: AOIConfigManager):
        super().__init__()
        self.controller = controller
        self.config = config

    def connect_plc(self) -> bool:
        """Tenta conectar ao PLC."""
        # Implementação de connect_cnc()

    def disconnect_plc(self):
        """Desconecta PLC."""

    def connect_camera(self, camera_id) -> bool:
        """Conecta câmera."""

    def test_camera(self) -> bool:
        """Testa conexão da câmera."""

    def attempt_auto_connect(self):
        """Tenta conexões automáticas ao iniciar."""
        # Implementação de _attempt_auto_connect()
```

**Métodos extraídos de AOIControllerApp:**
- `connect_cnc()`
- `connect_camera()`
- `test_camera()`
- `refresh_ports()`
- `_attempt_auto_connect()`
- `_show_plc_connection_error()`
- `_apply_plc_ui_settings()`

#### 2.2 RecipeManagerWrapper (Dia 3)
**Responsabilidade:** Integrar RecipeManager com a UI

```python
# consumo_lib/managers/recipe_manager.py
class RecipeManagerWrapper(QObject):
    """Wrapper para RecipeManager com integração UI."""

    recipe_loaded = pyqtSignal(object)  # Recipe

    def __init__(self, recipe_manager: RecipeManager):
        super().__init__()
        self.manager = recipe_manager
        self.current_recipe = None

    def load_recipe(self, name: str) -> Recipe:
        """Carrega receita e emite signal."""

    def apply_to_capture(self, recipe):
        """Aplica parâmetros de captura."""

    def apply_to_tension(self, recipe):
        """Aplica parâmetros de tensão."""

    def show_manager_dialog(self, parent) -> None:
        """Mostra diálogo de gerenciamento."""
```

**Métodos extraídos:**
- `show_recipe_manager()`
- `show_new_recipe_dialog()`
- `_on_recipe_loaded()`
- `apply_recipe_to_capture()`
- `apply_recipe_to_tension()`
- `_on_recipe_requested()`

#### 2.3 StencilManagerWrapper (Dia 4)
**Responsabilidade:** Integrar StencilTracker com a UI

```python
# consumo_lib/managers/stencil_manager.py
class StencilManagerWrapper(QObject):
    """Wrapper para StencilTracker com integração UI."""

    stencil_selected = pyqtSignal(object)  # Stencil
    stencil_cleared = pyqtSignal()

    def __init__(self, tracker: StencilTracker):
        super().__init__()
        self.tracker = tracker
        self.current_stencil = None

    def select_stencil(self, code: str) -> Stencil:
        """Seleciona stencil por código."""

    def save_tension_measurement(self, data: dict):
        """Salva medição no histórico."""

    def show_manager_dialog(self, parent) -> None:
        """Mostra diálogo de gerenciamento."""

    def show_create_dialog(self, parent) -> None:
        """Mostra diálogo de criação."""
```

**Métodos extraídos:**
- `show_stencil_manager()`
- `show_new_stencil_dialog()`
- `_on_stencil_selected()`
- `_on_stencil_cleared()`
- `_save_tension_to_history()`

#### 2.4 InspectionManager (Dia 5)
**Responsabilidade:** Orquestrar workflow de inspeção visual

```python
# consumo_lib/managers/inspection_manager.py
class InspectionManager(QObject):
    """Gerencia workflow completo de inspeção visual."""

    inspection_completed = pyqtSignal(object, object)  # result, overlay
    inspection_error = pyqtSignal(str)

    def __init__(self, inspector: StencilInspector, fiducial_widget):
        super().__init__()
        self.inspector = inspector
        self.fiducial_widget = fiducial_widget
        self.current_result = None

    def run_inspection(self, params: InspectionParams) -> None:
        """Executa inspeção com parâmetros dados."""

    def open_fiducial_alignment(self, parent_dialog) -> None:
        """Abre diálogo de alinhamento de fiduciais."""

    def show_result(self, result: InspectionResult, overlay: np.ndarray) -> None:
        """Mostra resultado da inspeção."""

    def export_pdf(self, result, output_path: Path) -> None:
        """Exporta resultado como PDF."""

    def show_last_result(self) -> None:
        """Mostra última inspeção executada."""
```

**Métodos extraídos:**
- `_init_inspection_system()`
- `show_inspection_settings()`
- `show_inspection_dialog()`
- `_browse_inspection_gerber()`
- `_browse_inspection_mosaic()`
- `_run_inspection()`
- `_open_fiducial_alignment_from_inspection()`
- `_show_inspection_result()`
- `export_pdf()`
- `show_last_inspection_result()`

#### 2.5 ReportManagerWrapper (Dia 5)
**Responsabilidade:** Gerenciar geração de relatórios

```python
# consumo_lib/managers/report_manager.py
class ReportManagerWrapper(QObject):
    """Wrapper para ReportGenerator com diálogos."""

    def __init__(self, generator: ReportGenerator):
        super().__init__()
        self.generator = generator

    def show_tension_report_dialog(self, parent, tension_data) -> None:
        """Mostra diálogo para relatório de tensão."""

    def show_stencil_report_dialog(self, parent, stencil: Stencil) -> None:
        """Mostra diálogo para relatório de stencil."""

    def show_period_query_dialog(self, parent) -> None:
        """Mostra diálogo de consulta por período."""

    def show_settings_dialog(self, parent) -> None:
        """Mostra configurações de relatório."""
```

**Métodos extraídos:**
- `_init_report_generator()`
- `show_report_settings()`
- `show_tension_report_dialog()`
- `show_stencil_report_dialog()`
- `show_period_query_dialog()`

---

### FASE 3: Extrair Diálogos (Dia 6-7)

**Objetivo:** Mover cada diálogo para arquivo próprio.

#### 3.1 Diálogos de Configuração
```python
# consumo_lib/dialogs/camera_settings_dialog.py
class CameraSettingsDialog(QDialog):
    """Diálogo de configurações de câmera."""
    # TODO: Extrair lógica de show_camera_settings_dialog()

# consumo_lib/dialogs/fov_calibration_dialog.py
# (wrapper existente, apenas mover)

# consumo_lib/dialogs/crosshair_settings_dialog.py
# (wrapper existente, apenas mover)

# consumo_lib/dialogs/fiducial_alignment_dialog.py
# (wrapper existente, apenas mover)

# consumo_lib/dialogs/inspection_settings_dialog.py
# (wrapper existente, apenas mover)

# consumo_lib/dialogs/report_settings_dialog.py
# (wrapper existente, apenas mover)

# consumo_lib/dialogs/calibration_test_dialog.py
class CalibrationTestDialog(QDialog):
    """Diálogo para teste de calibração."""
    # TODO: Extrair de show_calibration_test_dialog()

# consumo_lib/dialogs/about_dialog.py
class AboutDialog(QDialog):
    """Diálogo Sobre."""
    # TODO: Extrair de show_about_dialog()
```

#### 3.2 Diálogo de Mapa
```python
# consumo_lib/dialogs/map_definition_dialog.py
class MapDefinitionDialog(QDialog):
    """Diálogo para definir programa de mapa."""
    # TODO: Extrair de show_definir_mapa_dialog()
    # Inclui:
    # - _select_map_folder()
    # - _define_map_corner()
    # - _update_adjusted_step_info()
    # - _refresh_map_programs()
    # - _save_map_program()
```

---

### FASE 4: Criar Abas (Dia 8-9)

**Objetivo:** Divir setup_ui() em abas semânticas.

#### 4.1 Base Tab
```python
# consumo_lib/tabs/base_tab.py
class BaseTab(QWidget):
    """Classe base para todas as abas."""

    def __init__(self, name: str, controller, config, parent=None):
        super().__init__(parent)
        self.tab_name = name
        self.controller = controller
        self.config = config
        self.setup_ui()

    def setup_ui(self):
        """Override nas subclasses."""

    def on_tab_activated(self):
        """Chamado quando a aba é ativada."""

    def on_tab_deactivated(self):
        """Chamado quando a aba é desativada."""
```

#### 4.2 CNC Control Tab
```python
# consumo_lib/tabs/cnc_control_tab.py
class CNCControlTab(BaseTab):
    """Aba de controle CNC manual."""

    def setup_ui(self):
        # Layout existente de CNC (position display, movement, etc)

    def create_widgets(self):
        self.preview_widget = CameraPreviewWidget(...)
        self.movement_widget = MovementControlWidget(...)
        self.plc_monitor_widget = PLCMonitorWidget(...)

    # Métodos movidos de AOIControllerApp:
    # - update_position_display()
    # - add_current_position()
    # - remove_position()
    # - on_position_selected()
    # - get_current_feed_rate()
    # - _sync_backlight_button()
```

#### 4.3 Tension Tab
```python
# consumo_lib/tabs/tension_tab.py
class TensionTab(BaseTab):
    """Aba de medição de tensão."""

    def setup_ui(self):
        self.viz_widget = TensionVisualizationWidget(...)
        # Layout de medição de tensão

    # Métodos movidos:
    # - open_stencil_tension_dialog()
    # - _run_tension_measurement()
    # - _save_tension_to_history()
```

#### 4.4 Inspection Tab
```python
# consumo_lib/tabs/inspection_tab.py
class InspectionTab(BaseTab):
    """Aba de inspeção visual."""

    def setup_ui(self):
        # Layout de inspeção visual

    # Métodos movidos (delegam ao InspectionManager):
    # - show_inspection_settings()
    # - show_inspection_dialog()
    # - show_fiducial_alignment_dialog()
```

#### 4.5 Tracking Tab
```python
# consumo_lib/tabs/tracking_tab.py
class TrackingTab(BaseTab):
    """Aba de rastreabilidade de stencils."""

    def setup_ui(self):
        self.identification_widget = StencilIdentificationWidget(...)
        # Layout de histórico

    # Métodos movidos:
    # - show_stencil_manager()
    # - show_new_stencil_dialog()
    # - _on_stencil_selected()
```

#### 4.6 Map Tab
```python
# consumo_lib/tabs/map_tab.py
class MapTab(BaseTab):
    """Aba de programas de mapa."""

    def setup_ui(self):
        # Layout de programação de mapa

    # Métodos movidos:
    # - show_definir_mapa_dialog()
    # - _on_load_map_program_clicked()
    # - _on_generate_map()
    # - save_gcode()
    # - load_gcode()
```

---

### FASE 5: Simplificar MainWindow (Dia 10)

**Objetivo:** Reduzir AOIControllerApp para orquestração simples.

```python
# consumo_lib/main_window.py
class AOIControllerApp(QMainWindow):
    """
    Janela principal do sistema AOI.

    Responsabilidade: Orquestrar abas, menus e gerenciadores.
    Lógica de negócio específica fica nos gerenciadores.
    """

    def __init__(self):
        super().__init__()
        self._init_config()
        self._init_controller()
        self._init_managers()
        self._init_tabs()
        self._init_menu()
        self._init_connections()
        self._attempt_auto_connect()

    # ===== INICIALIZAÇÃO =====
    def _init_config(self):
        """Carrega configurações."""
        self.config = AOIConfigManager()

    def _init_controller(self):
        """Inicializa controller CNC."""
        self.controller = CNCAOIController(...)

    def _init_managers(self):
        """Inicializa gerenciadores de negócio."""
        self.connection_mgr = ConnectionManager(self.controller, self.config)
        self.recipe_mgr = RecipeManagerWrapper(RecipeManager())
        self.stencil_mgr = StencilManagerWrapper(StencilTracker())
        self.inspection_mgr = InspectionManager(...)
        self.report_mgr = ReportManagerWrapper(...)

    def _init_tabs(self):
        """Inicializa abas da aplicação."""
        self.tabs = QTabWidget()

        self.cnc_tab = CNCControlTab("Controle CNC", ...)
        self.tension_tab = TensionTab("Medição Tensão", ...)
        self.inspection_tab = InspectionTab("Inspeção Visual", ...)
        self.tracking_tab = TrackingTab("Rastreabilidade", ...)
        self.map_tab = MapTab("Mapa", ...)

        self.tabs.addTab(self.cnc_tab, "🎮 Controle CNC")
        self.tabs.addTab(self.tension_tab, "📏 Medição Tensão")
        self.tabs.addTab(self.inspection_tab, "🔍 Inspeção Visual")
        self.tabs.addTab(self.tracking_tab, "🏷️ Rastreabilidade")
        self.tabs.addTab(self.map_tab, "🗺️ Mapa")

    def _init_menu(self):
        """Configura menu - apenas delega para gerenciadores."""
        menubar = self.menuBar()

        # Menu Ferramentas
        tools_menu = menubar.addMenu("Ferramentas")
        tools_menu.addAction("Medição de Tensão", self.tension_tab.open_dialog)
        tools_menu.addAction("Gerenciar Receitas", self.recipe_mgr.show_manager_dialog)
        tools_menu.addAction("Gerenciar Stencils", self.stencil_mgr.show_manager_dialog)
        tools_menu.addSeparator()
        tools_menu.addAction("Preferências", self.show_settings)

        # Menu Relatórios
        reports_menu = menubar.addMenu("Relatórios")
        reports_menu.addAction("Relatório de Tensão", self.report_mgr.show_tension_dialog)
        reports_menu.addAction("Histórico de Stencil", self.report_mgr.show_stencil_dialog)

        # Menu Ajuda
        help_menu = menubar.addMenu("Ajuda")
        help_menu.addAction("Sobre", self.show_about)

    def _init_connections(self):
        """Conecta signals e slots."""
        self.connection_mgr.plc_connected.connect(self._on_plc_connected)
        self.connection_mgr.plc_connection_error.connect(self._on_plc_error)
        self.recipe_mgr.recipe_loaded.connect(self._on_recipe_loaded)
        self.stencil_mgr.stencil_selected.connect(self._on_stencil_selected)

    # ===== HANDLERS =====
    def _on_plc_connected(self):
        """PLC conectado."""
        self.statusBar().showMessage("✅ PLC Conectado")

    def _on_plc_error(self, error: str):
        """Erro na conexão PLC."""
        QMessageBox.warning(self, "Erro PLC", error)

    def _on_recipe_loaded(self, recipe):
        """Receita carregada."""
        self.current_recipe = recipe
        # Aplica às abas pertinentes
        self.tension_tab.apply_recipe(recipe)
        self.inspection_tab.apply_recipe(recipe)

    def _on_stencil_selected(self, stencil):
        """Stencil selecionado."""
        self.current_stencil = stencil
        self.tracking_tab.update_display(stencil)

    # ===== UTILITÁRIOS =====
    def show_settings(self):
        """Mostra diálogo de configurações."""
        dlg = SettingsDialog(self.config, self)
        dlg.exec()

    def show_about(self):
        """Mostra diálogo Sobre."""
        AboutDialog(self).exec()

    # ===== EVENTOS =====
    def eventFilter(self, source, event):
        """Filtro global de eventos (teclado)."""
        # Delega para aba ativa
        current_tab = self.tabs.currentWidget()
        if hasattr(current_tab, 'handle_key_event'):
            return current_tab.handle_key_event(source, event)
        return super().eventFilter(source, event)

    def closeEvent(self, event):
        """Limpeza ao fechar."""
        self.connection_mgr.disconnect_all()
        super().closeEvent(event)
```

**Resultado esperado:**
- AOIControllerApp reduzida de ~4.138 linhas para **~300-400 linhas**
- Apenas orquestração, sem lógica de negócio
- Código limpo e fácil de entender

---

### FASE 6: Threads e Utils (Dia 11)

#### 6.1 Mover Threads
```python
# consumo_lib/threads/sequence_runner.py
class SequenceRunnerThread(QThread):
    """Thread para execução de sequência de movimentos."""
    # Já existe, apenas mover

# consumo_lib/threads/map_generator.py
class MapGeneratorThread(QThread):
    """Thread para geração de mapa/índice."""
    # Já existe, apenas mover
```

#### 6.2 Criar Utils
```python
# consumo_lib/utils/position_display.py
class PositionFormatter:
    """Formata posição para exibição."""

    @staticmethod
    def format_wpos(wpos: dict, wcs: str = "G54") -> str:
        """Formata WCS Position."""

    @staticmethod
    def format_mpos(mpos: dict) -> str:
        """Formata Machine Position."""

# consumo_lib/utils/wcs_manager.py
class WCSManager:
    """Gerencia sistemas de coordenadas."""

    def __init__(self):
        self.active_wcs = "G54"
        self.offsets = {"G54": {"x": 0, "y": 0, "z": 0}}

    def set_active(self, wcs: str):
        """Define WCS ativo."""

    def get_offset(self, wcs: str) -> dict:
        """Retorna offset do WCS."""

# consumo_lib/utils/keyboard_handler.py
class KeyboardEventHandler:
    """Manipula eventos de teclado para movimentação."""

    def __init__(self, movement_widget):
        self.movement_widget = movement_widget

    def handle_event(self, event) -> bool:
        """Processa evento de teclado."""
        # Lógica de eventFilter() movida para cá
```

---

### FASE 7: Limpeza Final (Dia 12-13)

#### Tarefas:

1. **Atualizar todos os imports**
```python
# consumo_lib/__init__.py
from .main_window import AOIControllerApp

__all__ = ['AOIControllerApp']
```

2. **Verificar funcionalidade**
```bash
# Teste manual de todas as funcionalidades:
- Conexão PLC
- Conexão Câmera
- Movimentação
- Medição de tensão
- Inspeção visual
- Rastreabilidade
- Geração de mapa
- Relatórios
```

3. **Rodar mypy e pylint**
```bash
mypy consumo_lib/
pylint consumo_lib/
```

4. **Documentar** (se aplicável)
```python
# Adicionar docstrings nas novas classes/métodos críticos
```

---

## 📊 Comparação Antes vs Depois

### Estrutura de Arquivos

**Antes:**
```
consumo_lib.py                6.245 linhas  🔴
```

**Depois:**
```
consumo_lib/                  TOTAL: ~6.500 linhas
├── __init__.py               10 linhas
├── main_window.py            350 linhas     ✅ (era 4.138)
├── widgets/                  ~2.500 linhas
│   ├── tension_viz.py        400
│   ├── image_viewer.py       60
│   ├── position_list.py      80
│   ├── sequence_control.py   60
│   ├── position_registry.py  100
│   ├── camera_preview.py     280
│   ├── movement_control.py   680
│   ├── plc_monitor.py        200
│   └── preview_suspender.py  30
├── tabs/                     ~1.200 linhas
│   ├── base_tab.py           50
│   ├── cnc_control_tab.py    350
│   ├── tension_tab.py        200
│   ├── inspection_tab.py     250
│   ├── tracking_tab.py       200
│   └── map_tab.py            150
├── managers/                 ~800 linhas
│   ├── connection_manager.py 180
│   ├── recipe_manager.py     120
│   ├── stencil_manager.py    150
│   ├── inspection_manager.py 200
│   ├── report_manager.py     100
│   └── calibration_manager.py 50
├── dialogs/                  ~1.200 linhas
│   ├── camera_settings.py    350
│   ├── fov_calibration.py    150
│   ├── crosshair_settings.py 100
│   ├── fiducial_alignment.py 150
│   ├── inspection_settings.py 100
│   ├── report_settings.py    120
│   ├── calibration_test.py   100
│   ├── about.py              50
│   └── map_definition.py     80
├── threads/                  100 linhas
│   ├── sequence_runner.py    50
│   └── map_generator.py      50
└── utils/                    200 linhas
    ├── position_display.py   80
    ├── wcs_manager.py        70
    ├── keyboard_handler.py   50
```

### Métricas de Melhoria

| Métrica | Antes | Depois | Melhoria |
|---------|-------|--------|----------|
| Linhas do arquivo principal | 6.245 | 350 | **94% ↓** |
| Número de arquivos | 1 | 30+ | **Modular** |
| Maior classe | 4.138 linhas | 680 linhas | **84% ↓** |
| Métodos por classe | 113 (média) | ~20 (média) | **82% ↓** |
| Acoplamento | Alto | Baixo | **✅** |
| Coesão | Baixa | Alta | **✅** |
| Testabilidade | Difícil | Fácil | **✅** |

---

## 🎯 Estratégia de Migração Segura

### Técnica: "Strangler Fig Pattern"

1. **Criar nova estrutura em paralelo**
   - Não apagar código antigo imediatamente
   - Criar novos módulos com código refatorado

2. **Migrar gradualmente**
   - Substituir um componente por vez
   - Testar após cada migração
   - Manter código antigo como fallback

3. **Validação contínua**
   - Testes manuais após cada fase
   - Não passar para próxima fase sem validar
   - Commits pequenos e frequentes

### Controle de Versão

```bash
# Branch de refactoring
git checkout -b refactor/consumo_lib_modular

# Commits por fase
git commit -m "refactor: fase 1 - estrutura de diretórios"
git commit -m "refactor: fase 2 - extrair connection_manager"
git commit -m "refactor: fase 2 - extrair recipe_manager"
# ... etc

# Merge após validação completa
git checkout main
git merge refactor/consumo_lib_modular
```

---

## ✅ Checklist de Validação

### Após cada fase:
- [ ] Aplicação inicia sem erros
- [ ] Todas as abas funcionam
- [ ] Conexões funcionam
- [ ] Movimentação funciona
- [ ] Medição de tensão funciona
- [ ] Inspeção visual funciona
- [ ] Relatórios geram corretamente
- [ ] Não há regressões visuais

### Validação final:
- [ ] mypy sem erros
- [ ] pylint < 5.0/10.0
- [ ] Sem warnings em tempo de execução
- [ ] Teste manual completo (1 hora)
- [ ] Documentação atualizada

---

## 📝 Próximos Passos

Após conclusão deste refactoring:

1. **Adicionar testes unitários** para managers
2. **Adicionar type hints** completos
3. **Melhorar documentação** (docstrings)
4. **Considerar split adicional** se necessário

---

**Plano elaborado em:** 03/01/2026
**Estimativa de conclusão:** 10-15 dias úteis
**Risco:** Médio (mitigado por migração gradual)
**Prioridade:** ALTA
