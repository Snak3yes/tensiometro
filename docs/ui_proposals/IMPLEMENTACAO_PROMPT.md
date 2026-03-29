# Prompt para Implementação da Nova Aba "Medição de Tensão"

**Data:** 2026-03-29
**Para:** IA de implementação (sem capacidade de visão)
**Projeto:** Tensiometro - https://github.com/RONALDBUZAGLO/tensiometro

---

## 📋 CONTEXTO DO PROJETO

Você está trabalhando no projeto **Tensiometro**, um sistema AOI industrial para inspeção de stencils de pasta de solda em manufatura SMT.

**Stack:** Python 3.x + PyQt6 + OpenCV + SQLite
**Branch atual:** `release/v0.5-tension`
**Dimensões da janela:** 1200×800 pixels (FIXO)

**Estrutura principal:**
```
tensiometro/
├── aoi_lib/              # Core business logic
│   ├── tensiometer/      # Medição de tensão
│   ├── plc/              # Controle PLC
│   ├── database/         # Persistência SQLite
│   └── utils/            # Utilitários
│
├── consumo_lib/          # GUI PyQt6
│   ├── tabs/             # Abas principais
│   ├── widgets/          # Componentes UI
│   ├── dialogs/          # Diálogos
│   ├── ui/               # Design System
│   └── utils/            # Utilitários GUI
│
└── main.py               # Entry point
```

---

## 🎯 OBJETIVO DA IMPLEMENTAÇÃO

Criar uma **NOVA ABA** chamada "Medição de Tensão" que UNIFICA as funcionalidades das abas atuais "Stencils" e "Visualização de Tensão".

**IMPORTANTE:**
- ✅ Adicionar como TERCEIRA aba (não remover as existentes ainda)
- ✅ Manter abas atuais: "Stencils", "Visualização de Tensão" + NOVA: "Medição de Tensão"
- ✅ Após testes, as abas antigas serão removidas em PR separado

---

## 📐 LAYOUT DA NOVA ABA

A aba deve ter divisão vertical **70%/30%**:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  📊 Medição de Tensão                                                            │
├─────────────────────────────────┬───────────────────────────────────────────────┤
│                                 │                                               │
│  PAINEL ESQUERDO (70%)          │   PAINEL DIREITO (30%)                        │
│  - Barra de filtros             │   - Título + Info stencil                     │
│  - Lista de stencils            │   - Critérios de aceitação                    │
│  - Painel de detalhes           │   - Heatmap 4x4                               │
│  - Botões de ação               │   - Resultado (OK/WARN/NOK)                   │
│                                 │   - Estatísticas                              │
│                                 │   - Legenda                                   │
│                                 │   - Botões de ação                            │
│                                 │                                               │
├─────────────────────────────────┴───────────────────────────────────────────────┤
│  🔴 CLP: Desconectado  |  🔴 Tensiômetro: Desconectado  |  🔴 Câmera: Desc.    │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 ARQUIVOS PARA CRIAR/MODIFICAR

### 1. CRIAR: `consumo_lib/tabs/tension_measurement_tab.py`

Esta é a aba principal unificada. Use como referência:
- `consumo_lib/tabs/tree_view_tab.py` (aba Stencils atual)
- `consumo_lib/tabs/tension_tab.py` (aba Visualização atual)
- `consumo_lib/tabs/base_tab.py` (classe base)

### 2. CRIAR: `consumo_lib/widgets/mini_tension_heatmap.py`

Widget para o heatmap compacto no painel direito (30%).
Use como referência:
- `consumo_lib/widgets/tension_viz.py` (visualização completa atual)

### 3. MODIFICAR: `main_window.py` (ou arquivo equivalente)

Adicionar a nova aba ao QTabWidget principal.

---

## 🏗️ ESTRUTURA DA CLASSE `TensionMeasurementTab`

```python
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QGroupBox, QLabel, QLineEdit, QComboBox,
    QTreeWidget, QTreeWidgetItem, QScrollArea,
    QDoubleSpinBox, QPushButton, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from consumo_lib.ui import COLORS, TYPO, SPACE, DIM
from consumo_lib.ui.widget_standards import StandardButton
from consumo_lib.widgets.mini_tension_heatmap import MiniTensionHeatmapWidget
from consumo_lib.widgets.hardware_status_bar import HardwareStatusBar


class TensionMeasurementTab(QWidget):
    """
    Aba unificada de Medição de Tensão.

    Combina lista de stencils e visualização de tensão em layout 70%/30%.
    """

    program_selected = pyqtSignal(dict)

    def __init__(self, stencil_manager=None, parent=None):
        super().__init__(parent)
        self.stencil_manager = stencil_manager
        self.current_stencils = []
        self.selected_stencil = None
        self.setup_ui()
        self.load_stencils()

    def setup_ui(self):
        """Configura a interface da aba."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Título da aba
        title = QLabel("📊 Medição de Tensão")
        title.setFont(TYPO.get_font(TYPO.HEADLINE_MEDIUM, bold=True))
        layout.addWidget(title)

        # Splitter 70%/30%
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Painel esquerdo (70%)
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)

        # Painel direito (30%)
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)

        splitter.setStretchFactor(0, 7)
        splitter.setStretchFactor(1, 3)
        splitter.setHandleWidth(4)

        layout.addWidget(splitter, 1)

        # Hardware status bar
        self.hw_status_bar = HardwareStatusBar()
        layout.addWidget(self.hw_status_bar)

    def create_left_panel(self) -> QWidget:
        """Cria painel esquerdo com lista de stencils."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Barra de filtros
        filter_bar = self.create_filter_bar()
        layout.addWidget(filter_bar)

        # Lista de stencils
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels([
            "Código", "Descrição", "Status", "Tensão Média", "Última Medição", "Ações"
        ])
        self.tree_widget.setColumnWidth(0, 100)  # Código
        self.tree_widget.setColumnWidth(1, 200)  # Descrição
        self.tree_widget.setColumnWidth(2, 80)   # Status
        self.tree_widget.setColumnWidth(3, 100)  # Tensão
        self.tree_widget.setColumnWidth(4, 150)  # Última
        self.tree_widget.setColumnWidth(5, 80)   # Ações
        self.tree_widget.itemClicked.connect(self.on_stencil_selected)
        layout.addWidget(self.tree_widget, 1)

        # Painel de detalhes
        details_panel = self.create_details_panel()
        layout.addWidget(details_panel)

        return widget

    def create_filter_bar(self) -> QWidget:
        """Cria barra de filtros."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Buscar
        layout.addWidget(QLabel("Buscar:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar programas...")
        self.search_input.textChanged.connect(self.filter_stencils)
        layout.addWidget(self.search_input)

        # Período
        layout.addWidget(QLabel("Período:"))
        self.period_combo = QComboBox()
        self.period_combo.addItems([
            "Últimas 10", "7 dias", "30 dias",
            "60 dias", "90 dias", "180 dias", "365 dias"
        ])
        self.period_combo.currentTextChanged.connect(self.apply_filters)
        layout.addWidget(self.period_combo)

        # Status
        layout.addWidget(QLabel("Status:"))
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Todos", "Ativos", "Alerta", "Retirados"])
        self.status_combo.currentTextChanged.connect(self.apply_filters)
        layout.addWidget(self.status_combo)

        layout.addStretch()
        return widget

    def create_details_panel(self) -> QWidget:
        """Cria painel de detalhes do stencil selecionado."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        title = QLabel("📋 Detalhes do Stencil Selecionado")
        title.setFont(TYPO.get_font(TYPO.BODY_LARGE, bold=True))
        layout.addWidget(title)

        # Conteúdo dos detalhes (preencher quando selecionar)
        self.details_label = QLabel(
            "Selecione um stencil para ver detalhes"
        )
        self.details_label.setStyleSheet(f"color: {COLORS.TEXT_HINT};")
        layout.addWidget(self.details_label)

        # Botões
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_history = StandardButton("📜 Histórico")
        self.btn_history.setEnabled(False)
        self.btn_history.clicked.connect(self.show_history)
        btn_layout.addWidget(self.btn_history)

        self.btn_view = StandardButton("📈 Ver", variant="primary-green")
        self.btn_view.setEnabled(False)
        btn_layout.addWidget(self.btn_view)

        layout.addLayout(btn_layout)
        return widget

    def create_right_panel(self) -> QWidget:
        """Cria painel direito com visualização de tensão."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)

        # Título
        self.viz_title = QLabel("📊 Visualização")
        self.viz_title.setFont(TYPO.get_font(TYPO.BODY_LARGE, bold=True))
        layout.addWidget(self.viz_title)

        self.viz_subtitle = QLabel("Selecione um stencil")
        self.viz_subtitle.setStyleSheet(f"color: {COLORS.TEXT_HINT}; font-size: {TYPO.BODY_SMALL}px;")
        layout.addWidget(self.viz_subtitle)

        # Botões superiores
        btn_layout = QHBoxLayout()

        self.btn_load = StandardButton("📁 Carregar JSON")
        self.btn_load.clicked.connect(self.load_tension_file)
        btn_layout.addWidget(self.btn_load)

        self.btn_reload = StandardButton("↻ Recarregar")
        self.btn_reload.setEnabled(False)
        self.btn_reload.clicked.connect(self.reload_tension)
        btn_layout.addWidget(self.btn_reload)

        layout.addLayout(btn_layout)

        # Critérios de aceitação
        criteria_group = self.create_criteria_group()
        layout.addWidget(criteria_group)

        # Heatmap
        self.heatmap = MiniTensionHeatmapWidget()
        layout.addWidget(self.heatmap, 1)

        # Resultado
        self.result_label = QLabel("---")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_label.setStyleSheet(f"""
            font-size: {TYPO.BODY_LARGE}px;
            font-weight: bold;
            padding: {SPACE.SM}px;
            border-radius: {DIM.RADIUS_SM}px;
            background-color: {COLORS.TEXT_DISABLED};
        """)
        layout.addWidget(self.result_label)

        # Estatísticas
        self.stats_label = QLabel("Carregue um arquivo para ver estatísticas")
        self.stats_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        layout.addWidget(self.stats_label)

        # Legenda
        self.legend_label = QLabel("")
        layout.addWidget(self.legend_label)

        # Botão Histórico
        self.btn_full_history = StandardButton("📜 Ver Histórico Completo")
        self.btn_full_history.clicked.connect(self.show_full_history)
        layout.addWidget(self.btn_full_history)

        return widget

    def create_criteria_group(self) -> QGroupBox:
        """Cria grupo de critérios de aceitação."""
        group = QGroupBox("Critérios de Aceitação (N/cm²)")
        layout = QHBoxLayout(group)

        # Mínimo
        layout.addWidget(QLabel("Mín:"))
        self.spin_min = QDoubleSpinBox()
        self.spin_min.setRange(0, 100)
        self.spin_min.setValue(25.0)
        self.spin_min.valueChanged.connect(self.on_criteria_changed)
        layout.addWidget(self.spin_min)

        # Warning baixo
        layout.addWidget(QLabel("Warn↓:"))
        self.spin_warn_low = QDoubleSpinBox()
        self.spin_warn_low.setRange(0, 100)
        self.spin_warn_low.setValue(28.0)
        self.spin_warn_low.valueChanged.connect(self.on_criteria_changed)
        layout.addWidget(self.spin_warn_low)

        # Warning alto
        layout.addWidget(QLabel("Warn↑:"))
        self.spin_warn_high = QDoubleSpinBox()
        self.spin_warn_high.setRange(0, 100)
        self.spin_warn_high.setValue(42.0)
        self.spin_warn_high.valueChanged.connect(self.on_criteria_changed)
        layout.addWidget(self.spin_warn_high)

        # Máximo
        layout.addWidget(QLabel("Máx:"))
        self.spin_max = QDoubleSpinBox()
        self.spin_max.setRange(0, 100)
        self.spin_max.setValue(45.0)
        self.spin_max.valueChanged.connect(self.on_criteria_changed)
        layout.addWidget(self.spin_max)

        # Usar Receita
        self.btn_recipe = StandardButton("Usar Receita", variant="primary-blue")
        self.btn_recipe.clicked.connect(self.load_criteria_from_recipe)
        layout.addWidget(self.btn_recipe)

        return group

    # ============ MÉTODOS DE LÓGICA ============

    def load_stencils(self):
        """Carrega lista de stencils do manager."""
        # Implementar lógica similar à TreeViewTab
        pass

    def filter_stencils(self, search_term: str):
        """Filtra stencils por termo de busca."""
        self.apply_filters()

    def apply_filters(self):
        """Aplica filtros de período e status."""
        # Implementar filtragem
        pass

    def on_stencil_selected(self, item: QTreeWidgetItem, column: int):
        """Handle quando stencil é selecionado."""
        # Atualizar painel direito
        # Carregar dados de tensão se disponíveis
        pass

    def load_tension_file(self):
        """Carrega arquivo JSON de tensão."""
        # Implementar loading de arquivo
        pass

    def reload_tension(self):
        """Recarrega último arquivo de tensão."""
        pass

    def on_criteria_changed(self):
        """Handle quando critérios mudam."""
        # Atualizar visualização
        pass

    def load_criteria_from_recipe(self):
        """Carrega critérios da receita atual."""
        pass

    def show_history(self):
        """Mostra histórico do stencil selecionado."""
        pass

    def show_full_history(self):
        """Mostra histórico completo em diálogo."""
        pass
```

---

## 🎨 WIDGET `MiniTensionHeatmapWidget`

Crie em `consumo_lib/widgets/mini_tension_heatmap.py`:

```python
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont
from PyQt6.QtCore import Qt
from typing import List, Dict, Optional

from consumo_lib.ui import COLORS, TYPO


class MiniTensionHeatmapWidget(QWidget):
    """
    Widget para visualização compacta de heatmap de tensão.

    Grid 4x4 otimizado para painel de 340px de largura.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.measurements: List[Dict] = []
        self.acceptance_criteria = None
        self.setMinimumSize(280, 280)

    def set_measurements(self, data: Dict):
        """Define dados de medição para visualização."""
        self.measurements = data.get('measurements', [])
        self.parameters = data.get('parameters', {})
        self.update()

    def set_acceptance_criteria(self, criteria):
        """Define critérios para colorização."""
        self.acceptance_criteria = criteria
        self.update()

    def paintEvent(self, event):
        """Desenha o heatmap."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Fundo
        painter.fillRect(self.rect(), COLORS.to_qcolor(COLORS.BACKGROUND))

        if not self.measurements:
            # Mensagem de placeholder
            painter.setPen(COLORS.to_qcolor(COLORS.TEXT_HINT))
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "Carregue um arquivo JSON para visualizar"
            )
            return

        # Desenha grid 4x4
        self._draw_grid(painter)

        # Desenha pontos
        self._draw_measurement_points(painter)

    def _draw_grid(self, painter: QPainter):
        """Desenha grid 4x4."""
        margin = 10
        size = min(self.width(), self.height()) - 2 * margin

        painter.setPen(QPen(COLORS.to_qcolor(COLORS.BORDER), 1))

        # Retângulo externo
        painter.drawRect(margin, margin, size, size)

        # Linhas verticais
        for i in range(1, 4):
            x = margin + (size * i / 4)
            painter.drawLine(x, margin, x, margin + size)

        # Linhas horizontais
        for i in range(1, 4):
            y = margin + (size * i / 4)
            painter.drawLine(margin, y, margin + size, y)

    def _draw_measurement_points(self, painter: QPainter):
        """Desenha pontos de medição."""
        # Implementar lógica de desenho similar ao TensionCanvas
        # mas otimizada para grid 4x4 compacto
        pass

    def clear(self):
        """Limpa o heatmap."""
        self.measurements = []
        self.update()
```

---

## 🎯 DESIGN SYSTEM - TOKENS PARA USAR

Importe de `consumo_lib.ui`:

```python
from consumo_lib.ui import COLORS, TYPO, SPACE, DIM
```

**Cores principais:**
- `COLORS.PRIMARY` - Cor primária
- `COLORS.SUCCESS` - Verde (#10B981)
- `COLORS.WARNING` - Amarelo (#F59E0B)
- `COLORS.ERROR` - Vermelho (#EF4444)
- `COLORS.BACKGROUND` - Fundo principal
- `COLORS.SURFACE` - Superfícies
- `COLORS.BORDER` - Bordas

**Tipografia:**
- `TYPO.HEADLINE_MEDIUM` - Títulos
- `TYPO.BODY_LARGE` - Corpo grande
- `TYPO.BODY_SMALL` - Corpo pequeno

**Spacing:**
- `SPACE.XS`, `SPACE.SM`, `SPACE.MD`, `SPACE.LG`, `SPACE.XL`

---

## ✅ CHECKLIST DE IMPLEMENTAÇÃO

- [ ] Criar `consumo_lib/tabs/tension_measurement_tab.py`
- [ ] Criar `consumo_lib/widgets/mini_tension_heatmap.py`
- [ ] Registrar nova aba em `consumo_lib/tabs/__init__.py`
- [ ] Adicionar aba ao MainWindow (como TERCEIRA aba)
- [ ] Testar carregamento de stencils
- [ ] Testar seleção de stencil
- [ ] Testar carregamento de arquivo JSON
- [ ] Testar critérios de aceitação
- [ ] Testar heatmap
- [ ] Verificar integração com HardwareStatusBar

---

## 🧪 TESTES

Execute:
```bash
# Testes unitários existentes
pytest tests/ -v

# Executar aplicação
.venv/Scripts/python.exe main.py
```

**Validação manual:**
1. Abrir aplicação
2. Verificar se aba "Medição de Tensão" aparece como terceira aba
3. Selecionar stencil na lista
4. Verificar painel de detalhes atualiza
5. Verificar painel direito mostra informações
6. Carregar arquivo JSON de tensão
7. Verificar heatmap renderiza corretamente

---

## 📝 OBSERVAÇÕES IMPORTANTES

1. **NÃO remover abas existentes** - Esta é uma implementação incremental
2. **Usar Design System** - Seguir tokens de `consumo_lib/ui/`
3. **Manter consistência** - Seguir padrões das abas existentes
4. **Hardware StatusBar** - Reutilizar widget existente
5. **Splitter** - Usar QSplitter com proporção 70/30
6. **Heatmap** - Widget dedicado para versão compacta

---

## 📁 ARQUIVOS DE REFERÊNCIA (EXISTENTES)

Leia estes arquivos para entender os padrões:

1. `consumo_lib/tabs/tree_view_tab.py` - Lista de stencils
2. `consumo_lib/tabs/tension_tab.py` - Visualização de tensão
3. `consumo_lib/widgets/tension_viz.py` - Canvas de tensão completo
4. `consumo_lib/ui/widget_standards.py` - StandardButton
5. `consumo_lib/ui/design_tokens.py` - Tokens de design
6. `consumo_lib/widgets/hardware_status_bar.py` - Status bar

---

## 🚀 PRÓXIMOS PASSOS (APÓS IMPLEMENTAÇÃO)

1. Testar funcionalidade completa
2. Validar com usuário
3. Preparar remoção das abas antigas (PR separado)
4. Atualizar documentação
