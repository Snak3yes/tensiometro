# 🚀 Guia Prático de Refactoring - Passo a Passo

**Este documento contém instruções detalhadas para executar o refactoring.**

---

## 📋 Pré-requisitos

### Ferramentas Necessárias
```bash
# Verificar se tem tudo instalado
git --version          # Controle de versão
python --version       # Python 3.10+

# Opcional mas recomendado
mypy --version         # Type checker
pylint --version       # Linter
black --version        # Formatter
```

### Backup Seguro
```bash
# 1. Criar branch de refactoring
git checkout -b refactor/consumo_lib_modular

# 2. Commit do estado atual
git add .
git commit -m "refactor: snapshot antes do refactoring modular"

# 3. Criar tag para fácil rollback
git tag pre-refactor-v0.4.0
```

---

## FASE 1: Estrutura de Diretórios (Dia 1)

### Passo 1.1: Criar estrutura

```bash
# No diretório raiz do projeto
cd /mnt/e/PycharmProjects/Tensiometro

# Criar estrutura de pacotes
mkdir -p consumo_lib/{widgets,tabs,managers,dialogs,threads,utils}

# Criar __init__.py em cada diretório
touch consumo_lib/__init__.py
touch consumo_lib/widgets/__init__.py
touch consumo_lib/tabs/__init__.py
touch consumo_lib/managers/__init__.py
touch consumo_lib/dialogs/__init__.py
touch consumo_lib/threads/__init__.py
touch consumo_lib/utils/__init__.py

# Verificar estrutura
tree consumo_lib/ -L 2
```

**Resultado esperado:**
```
consumo_lib/
├── __init__.py
├── widgets/
│   └── __init__.py
├── tabs/
│   └── __init__.py
├── managers/
│   └── __init__.py
├── dialogs/
│   └── __init__.py
├── threads/
│   └── __init__.py
└── utils/
    └── __init__.py
```

### Passo 1.2: Renomear arquivo antigo

```bash
# Renomear consumo_lib.py para consumo_lib/main_window.py
mv consumo_lib.py consumo_lib/main_window.py

# Testar que ainda funciona (deve funcionar!)
python -m consumo_lib.main_window
```

### Passo 1.3: Mover widgets (um por vez)

```bash
# Vou criar um script para ajudar no movimento
cat > /tmp/move_widgets.py << 'EOF'
#!/usr/bin/env python3
"""
Script auxiliar para mover widgets de consumo_lib.py
"""
import re

# Arquivo de origem
source_file = "consumo_lib/main_window.py"

# Padrões de classes para mover
patterns = {
    "widgets/tension_viz.py": [
        "TensionVisualizationWidget",
        "TensionCanvas",
    ],
    "widgets/image_viewer.py": [
        "ImageViewerWidget",
    ],
    "widgets/position_list.py": [
        "PositionListWidget",
    ],
    "widgets/sequence_control.py": [
        "SequenceControlWidget",
    ],
    "widgets/position_registry.py": [
        "PositionRegistryWidget",
    ],
    "widgets/camera_preview.py": [
        "CameraPreviewWidget",
    ],
    "widgets/movement_control.py": [
        "MovementControlWidget",
    ],
    "widgets/plc_monitor.py": [
        "PLCMonitorWidget",
    ],
}

print("Este script apenas mostra o que fazer. Manual:")
print("1. Abrir consumo_lib/main_window.py")
print("2. Localizar a classe")
print("3. Cortar (todo o bloco da classe)")
print("4. Colar no arquivo novo")
print("5. Adicionar import em consumo_lib/widgets/__init__.py")
EOF

python /tmp/move_widgets.py
```

### Passo 1.4: Exemplo Prático - Movendo CameraPreviewWidget

```bash
# 1. Abrir consumo_lib/main_window.py
# 2. Localizar linha 853 (class CameraPreviewWidget)
# 3. Copiar toda a classe até linha 1098 (inclusive)

# Conteúdo para copiar:
# ──────────────────────────────────────────────────────────────
class CameraPreviewWidget(QWidget):
    """
    Widget de preview de câmera com click-to-move.

    ...
    """
    # ... (todo o código até o final da classe)
# ──────────────────────────────────────────────────────────────

# 4. Criar arquivo consumo_lib/widgets/camera_preview.py
cat > consumo_lib/widgets/camera_preview.py << 'EOFWIDGET'
"""
widgets/camera_preview.py
-------------------------
Widget de preview de câmera com funcionalidade de click-to-move.
"""
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, ...
from aoi_lib import CNCAOIController
from aoi_lib.config_manager import AOIConfigManager
from aoi_lib.fov_calibration import CameraFOVConverter

# TODO: Colar aqui a classe CameraPreviewWidget copiada
# Passo a passo:
# 1. Copiar classe de main_window.py
# 2. Colar abaixo deste comentário
# 3. Verificar imports no topo

class CameraPreviewWidget(QWidget):
    # [COLAR CÓDIGO AQUI]
    pass
EOFWIDGET

# 5. Atualizar consumo_lib/widgets/__init__.py
cat >> consumo_lib/widgets/__init__.py << 'EOF'
from .camera_preview import CameraPreviewWidget
EOF

# 6. Remover classe de main_window.py (após verificar que funciona)
#    Substituir por import:
cat >> consumo_lib/main_window.py << 'EOF'
from consumo_lib.widgets import CameraPreviewWidget
EOF
```

### Passo 1.5: Repetir para outros widgets

**Ordem recomendada:**
1. ✅ TensionVisualizationWidget + TensionCanvas → `widgets/tension_viz.py`
2. ✅ ImageViewerWidget → `widgets/image_viewer.py`
3. ✅ PositionListWidget → `widgets/position_list.py`
4. ✅ SequenceControlWidget → `widgets/sequence_control.py`
5. ✅ PositionRegistryWidget → `widgets/position_registry.py`
6. ✅ CameraPreviewWidget → `widgets/camera_preview.py`
7. ✅ MovementControlWidget → `widgets/movement_control.py`
8. ✅ PLCMonitorWidget → `widgets/plc_monitor.py`

### Passo 1.6: Mover threads e utils

```bash
# Threads
grep -n "class SequenceRunnerThread" consumo_lib/main_window.py
# Linha 6080 - copiar para threads/sequence_runner.py

grep -n "class MapGeneratorThread" consumo_lib/main_window.py
# Linha 6103 - copiar para threads/map_generator.py

# Utils
grep -n "class MapParams" consumo_lib/main_window.py
# Linha 1916 - copiar para utils/map_params.py

grep -n "class _PreviewSuspender" consumo_lib/main_window.py
# Linha 1925 - copiar para widgets/preview_suspender.py
```

### Passo 1.7: Validação Fase 1

```bash
# 1. Testar import
python -c "from consumo_lib.main_window import AOIControllerApp; print('✅ Import OK')"

# 2. Testar execução (se possível sem hardware)
python -m consumo_lib.main_window

# 3. Commit
git add consumo_lib/
git commit -m "refactor(fase 1): estruturar diretórios e mover widgets"
```

---

## FASE 2: ConnectionManager (Dia 2)

### Passo 2.1: Criar o manager

```bash
# Criar arquivo do manager
cat > consumo_lib/managers/connection_manager.py << 'EOFMANAGER"""
managers/connection_manager.py
-------------------------
Gerencia conexões de hardware (PLC + Câmera).
"""
import logging
from PyQt6.QtCore import QObject, pyqtSignal
from aoi_lib import PLCAxisController

logger = logging.getLogger(__name__)

class ConnectionManager(QObject):
    """
    Gerencia conexões com hardware (PLC via Modbus + Câmera).

    Responsabilidades:
        - Conectar/desconectar PLC
        - Conectar/desconectar câmera
        - Auto-connection ao iniciar
        - Emitir signals de status
    """

    # Signals
    plc_connected = pyqtSignal()
    plc_disconnected = pyqtSignal()
    plc_connection_error = pyqtSignal(str)
    camera_connected = pyqtSignal()
    camera_disconnected = pyqtSignal()
    camera_error = pyqtSignal(str)

    def __init__(self, controller, config):
        super().__init__()
        self.controller = controller
        self.config = config
        self._plc_connecting = False

    def connect_plc(self) -> bool:
        """
        Tenta conectar ao PLC.

        Returns:
            True se conectado, False caso contrário
        """
        if not isinstance(self.controller.cnc, PLCAxisController):
            logger.warning("Backend não é PLC")
            return False

        plc = self.controller.cnc

        try:
            logger.info(f"Conectando ao PLC em {plc.host}:{plc.port}")
            plc.connect()

            if plc.is_connected:
                logger.info("PLC conectado com sucesso")
                self.plc_connected.emit()
                return True
            else:
                logger.error("Falha na conexão PLC")
                self.plc_connection_error.emit("Falha ao conectar")
                return False

        except Exception as e:
            logger.error(f"Exceção na conexão PLC: {e}")
            self.plc_connection_error.emit(str(e))
            return False

    def disconnect_plc(self):
        """Desconecta o PLC."""
        if not isinstance(self.controller.cnc, PLCAxisController):
            return

        self.controller.cnc.close()
        self.plc_disconnected.emit()
        logger.info("PLC desconectado")

    def attempt_auto_connect(self):
        """
        Tenta conexão automática ao iniciar aplicação.

        Usa configurações salvas para decidir se deve conectar.
        """
        # Auto-connect PLC?
        if self.config.get("connections", "auto_connect_cnc", default=False):
            if isinstance(self.controller.cnc, PLCAxisController):
                self.connect_plc()

        # Auto-connect câmera?
        if self.config.get("connections", "auto_connect_camera", default=False):
            # Implementação similar para câmera
            pass

    # TODO: Implementar métodos de câmera (connect_camera, test_camera, etc)
EOFMANAGER
```

### Passo 2.2: Integrar na MainWindow

```python
# Em consumo_lib/main_window.py

# No __init__ de AOIControllerApp, substituir:

# ANTIGO:
# self.connect_cnc_btn.clicked.connect(self.connect_cnc)

# NOVO:
from consumo_lib.managers import ConnectionManager

# Em __init__:
self.connection_mgr = ConnectionManager(self.controller, self.config)
self.connection_mgr.plc_connected.connect(self._on_plc_connected)
self.connection_mgr.plc_disconnected.connect(self._on_plc_disconnected)
self.connection_mgr.plc_connection_error.connect(self._on_plc_error)

# Conectar botão
self.connect_cnc_btn.clicked.connect(self._on_connect_btn_clicked)

# Novos handlers:
def _on_connect_btn_clicked(self):
    """Botão conectar/desconectar clicado."""
    if self.controller.cnc.is_connected:
        self.connection_mgr.disconnect_plc()
    else:
        self.connection_mgr.connect_plc()

def _on_plc_connected(self):
    """PLC conectado."""
    self.connect_cnc_btn.setText("Desconectar PLC")
    self.cnc_status.setText("Conectado")
    self.statusBar().showMessage("✅ PLC Conectado")

def _on_plc_disconnected(self):
    """PLC desconectado."""
    self.connect_cnc_btn.setText("Conectar PLC")
    self.cnc_status.setText("Desconectado")

def _on_plc_error(self, error: str):
    """Erro na conexão PLC."""
    self.cnc_status.setText("Erro")
    QMessageBox.warning(self, "Erro de Conexão",
                       f"Não foi possível conectar ao PLC:\n{error}")
```

### Passo 2.3: Mover código antigo

```python
# Em consumo_lib/main_window.py, método connect_cnc():
# ANTIGO: Toda a implementação de conexão (linhas 3535-3590)
# NOVO: Delegar para ConnectionManager

def connect_cnc(self):
    """MÉTODO OBSOLETO - Usar ConnectionManager"""
    # Mantido temporariamente por compatibilidade
    # TODO: Remover após verificar que tudo funciona
    return self.connection_mgr.connect_plc()
```

### Passo 2.4: Testar

```bash
# Testar manualmente:
python -m consumo_lib.main_window

# 1. Clicar em "Conectar PLC"
# 2. Verificar se conecta
# 3. Verificar se UI atualiza

# Se funcionou, commit:
git add consumo_lib/managers/connection_manager.py
git add consumo_lib/main_window.py
git commit -m "refactor(fase 2): extrair ConnectionManager"
```

---

## FASE 3: Outros Managers (Dia 3-5)

### Padronão para todos os managers:

```python
# 1. Criar arquivo em managers/
# 2. Criar classe Manager herdando de QObject
# 3. Definir signals para eventos importantes
# 4. Mover lógica de AOIControllerApp para o manager
# 5. Conectar signals na MainWindow
# 6. Testar
# 7. Commit
```

### Exemplo: RecipeManagerWrapper

```bash
# Criar
cat > consumo_lib/managers/recipe_manager.py << 'EOF'
"""
Wrapper para RecipeManager com integração UI.
"""
from PyQt6.QtCore import QObject, pyqtSignal
from aoi_lib.recipe_manager import RecipeManager

class RecipeManagerWrapper(QObject):
    """Gerencia receitas com integração à UI."""

    recipe_loaded = pyqtSignal(object)

    def __init__(self, recipe_manager: RecipeManager):
        super().__init__()
        self.manager = recipe_manager
        self.current_recipe = None

    def load_recipe(self, name: str):
        """Carrega receita e emite signal."""
        recipe = self.manager.load_recipe(name)
        self.current_recipe = recipe
        self.recipe_loaded.emit(recipe)
        return recipe

    def show_manager_dialog(self, parent):
        """Mostra diálogo de gerenciamento."""
        from aoi_lib.recipe_dialog import RecipeManagerDialog
        dlg = RecipeManagerDialog(self.manager, parent)
        if dlg.exec():
            # Recipe selecionado/carregado
            pass
EOF
```

---

## FASE 4: Criar Abas (Dia 8-9)

### Passo 4.1: Base Tab

```bash
cat > consumo_lib/tabs/base_tab.py << 'EOFTAB"""
tabs/base_tab.py
---------------
Classe base para todas as abas da aplicação.
"""
from PyQt6.QtWidgets import QWidget
from aoi_lib import CNCAOIController
from aoi_lib.config_manager import AOIConfigManager

class BaseTab(QWidget):
    """
    Classe base para abas da aplicação.

    Todas as abas devem herdar desta classe para garantir
    interface consistente.
    """

    def __init__(self, name: str, controller: CNCAOIController,
                 config: AOIConfigManager, parent=None):
        super().__init__(parent)
        self.tab_name = name
        self.controller = controller
        self.config = config
        self.setup_ui()

    def setup_ui(self):
        """
        Configura a UI da aba.

        Override nas subclasses.
        """
        raise NotImplementedError("Subclasses devem implementar setup_ui()")

    def on_tab_activated(self):
        """
        Chamado quando a aba é ativada pelo usuário.

        Override opcional nas subclasses.
        """
        pass

    def on_tab_deactivated(self):
        """
        Chamado quando a aba é desativada.

        Override opcional nas subclasses.
        """
        pass
EOFTAB
```

### Passo 4.2: CNC Control Tab

```bash
cat > consumo_lib/tabs/cnc_control_tab.py << 'EOFTAB"""
tabs/cnc_control_tab.py
----------------------
Aba de controle CNC manual.
"""
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QGroupBox
from .base_tab import BaseTab
from consumo_lib.widgets import (
    CameraPreviewWidget,
    MovementControlWidget,
    PLCMonitorWidget
)

class CNCControlTab(BaseTab):
    """Aba de controle CNC com preview e movimento."""

    def __init__(self, controller, config, parent=None):
        super().__init__("Controle CNC", controller, config, parent)

    def setup_ui(self):
        """Configura layout da aba CNC."""
        layout = QVBoxLayout(self)

        # Preview de câmera
        self.preview_widget = CameraPreviewWidget(
            self.controller, self.config, self
        )
        layout.addWidget(self.preview_widget, stretch=2)

        # Controles de movimento
        self.movement_widget = MovementControlWidget(
            self.controller, self.config, self
        )
        layout.addWidget(self.movement_widget, stretch=1)

        # Monitor PLC (opcional, pode estar em accordion)
        self.plc_monitor_widget = PLCMonitorWidget(
            self.controller, self
        )
        # ... adiciona ao layout se desejado

    def on_tab_activated(self):
        """Ao ativar aba, iniciar preview."""
        self.preview_widget.start_preview()

    def on_tab_deactivated(self):
        """Ao desativar, parar preview."""
        self.preview_widget.stop_preview()

    # TODO: Mover métodos update_position_display, etc da MainWindow
EOFTAB
```

---

## FASE 5: Simplificar MainWindow (Dia 10-11)

### Meta: Reduzir de 4.138 para ~350 linhas

```python
# Estrutura da nova AOIControllerApp:

class AOIControllerApp(QMainWindow):
    """Janela principal - ORQUESTRADOR apenas."""

    def __init__(self):
        super().__init__()
        # 1. Config
        self._init_config()

        # 2. Controller
        self._init_controller()

        # 3. Managers (~30 linhas)
        self._init_managers()

        # 4. Tabs (~50 linhas)
        self._init_tabs()

        # 5. Menu (~40 linhas)
        self._init_menu()

        # 6. Connections (~30 linhas)
        self._init_connections()

        # 7. Auto-connect (~10 linhas)
        self._attempt_auto_connect()

    # ===== INICIALIZAÇÃO =====
    def _init_config(self):
        """Inicializa configurações."""
        self.config = AOIConfigManager()

    def _init_controller(self):
        """Inicializa controller CNC."""
        self.controller = CNCAOIController(...)

    def _init_managers(self):
        """Inicializa gerenciadores."""
        self.connection_mgr = ConnectionManager(...)
        self.recipe_mgr = RecipeManagerWrapper(...)
        self.stencil_mgr = StencilManagerWrapper(...)
        self.inspection_mgr = InspectionManager(...)
        self.report_mgr = ReportManagerWrapper(...)

    def _init_tabs(self):
        """Inicializa abas."""
        self.tabs = QTabWidget()
        self.cnc_tab = CNCControlTab(...)
        self.tension_tab = TensionTab(...)
        # ...
        self.setCentralWidget(self.tabs)

    def _init_menu(self):
        """Configura menu - delega para managers/tabs."""
        menubar = self.menuBar()
        # ... menu simples

    def _init_connections(self):
        """Conecta signals."""
        self.connection_mgr.plc_connected.connect(self._on_plc_connected)
        # ...

    # ===== HANDLERS SIMPLES =====
    def _on_plc_connected(self):
        """PLC conectado."""
        self.statusBar().showMessage("✅ PLC Conectado")

    def _on_plc_error(self, error):
        """Erro PLC."""
        QMessageBox.warning(self, "Erro", error)

    # ===== EVENTOS =====
    def closeEvent(self, event):
        """Limpeza."""
        self.connection_mgr.disconnect_all()
        super().closeEvent(event)
```

---

## ✅ Checklist de Validação por Fase

### Fase 1: Estrutura
- [ ] Diretórios criados
- [ ] consumo_lib.py → main_window.py
- [ ] 9 widgets movidos
- [ ] 2 threads movidas
- [ ] Aplicação inicia e funciona
- [ ] Commit feito

### Fase 2: ConnectionManager
- [ ] Arquivo criado
- [ ] Conecta PLC
- [ ] Desconecta PLC
- [ ] Auto-connect funciona
- [ ] Signals emitidos
- [ ] UI atualiza
- [ ] Commit feito

### Fase 3: Demais Managers
- [ ] RecipeManagerWrapper funciona
- [ ] StencilManagerWrapper funciona
- [ ] InspectionManager funciona
- [ ] ReportManagerWrapper funciona
- [ ] Todos managers testados
- [ ] Commits por manager

### Fase 4: Tabs
- [ ] BaseTab criada
- [ ] CNControlTab funciona
- [ ] TensionTab funciona
- [ ] InspectionTab funciona
- [ ] TrackingTab funciona
- [ ] MapTab funciona
- [ ] Todas abas testadas
- [ ] Commits por tab

### Fase 5: Simplificação
- [ ] AOIControllerApp < 400 linhas
- [ ] Todas funcionalidades testadas
- [ ] Sem regressões
- [ ] mypy sem erros
- [ ] Commit final

---

## 🚨 Recuperação de Desastres

### Se algo quebrar:

```bash
# Opção 1: Reset para commit anterior
git reset --hard HEAD~1

# Opção 2: Voltar para tag
git checkout pre-refactor-v0.4.0
git checkout -b refactor/tentativa-2

# Opção 3: Ver diff do que mudou
git diff HEAD~1 consumo_lib/main_window.py
```

### Se estiver perdido:

```bash
# Ver log do que foi feito
git log --oneline --graph

# Ver arquivo em commit específico
git show HEAD~1:consumo_lib.py | head -50

# Restaurar arquivo específico
git checkout HEAD~1 -- consumo_lib/main_window.py
```

---

## 📝 Template de Commit

```bash
# Padrão de mensagem de commit
git commit -m "refactor(fase X): descrição breve

- Mudança 1
- Mudança 2
- Mudança 3

Refs: #issue (se aplicável)"

# Exemplo:
git commit -m "refactor(fase 2): extrair ConnectionManager

- Criado managers/connection_manager.py
- Movido connect_cnc() para manager
- Implementado signals plc_connected/disconnected
- Atualizado AOIControllerApp para usar manager
- Mantido método antigo por compatibilidade (deprecated)

Testes manuais:
- ✅ Conecta PLC
- ✅ Desconecta PLC
- ✅ Auto-connect ao iniciar
- ✅ UI atualiza corretamente"
```

---

## 🎓 Dicas e Truques

### 1. Trabalhe em pequenos incrementos
```bash
# ✅ BOM
git commit -m "refactor: mover CameraPreviewWidget"
git commit -m "refactor: mover MovementControlWidget"

# ❌ RUIM
git commit -m "refactor: mover todos os widgets de uma vez"
```

### 2. Teste após cada mudança
```bash
# Teste rápido
python -c "from consumo_lib.main_window import AOIControllerApp; print('OK')"

# Teste completo
python -m consumo_lib.main_window
```

### 3. Use branches para experimentos
```bash
# Branch para tentar algo
git checkout -b experiment/nova-ideia

# Se deu certo, merge
git checkout refactor/consumo_lib_modular
git merge experiment/nova-ideia

# Se deu ruim, apenas deleta
git branch -D experiment/nova-ideia
```

### 4. Documente código complexo
```python
def _on_plc_connected(self):
    """
    Handler para quando PLC conecta.

    Atualiza:
        - Botão de conexão
        - Label de status
        - Status bar

    Signal origin:
        ConnectionManager.plc_connected
    """
    # código...
```

---

**Documento gerado em:** 03/01/2026
**Status:** Pronto para uso
**Próximo passo:** Iniciar Fase 1
