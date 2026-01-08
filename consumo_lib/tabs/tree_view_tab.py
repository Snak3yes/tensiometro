"""
Aba TreeView - Lista de Programas

Exibe lista de stencils com busca, filtros e detalhes.
"""

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTreeWidget, QTreeWidgetItem, QLabel, QPushButton,
    QComboBox, QGroupBox, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal

from consumo_lib.widgets.search_line_edit import SearchLineEdit
from consumo_lib.widgets.status_badge import StatusBadge
from consumo_lib.widgets.hardware_status_bar import HardwareStatusBar

logger = logging.getLogger(__name__)


class TreeViewTab(QWidget):
    """
    Aba principal com lista de programas (stencils)

    Sinais:
        program_selected: Emitido ao selecionar programa
                         Argumento: dict com dados do stencil
        inspect_requested: Emitido ao clicar "Inspecionar Stencil"
                          Argumento: dict com dados do stencil
    """

    program_selected = pyqtSignal(dict)
    inspect_requested = pyqtSignal(dict)

    def __init__(self, stencil_manager=None, parent=None):
        """
        Inicializa aba TreeView

        Args:
            stencil_manager: Instância de StencilTracker (opcional)
            parent: Widget pai
        """
        super().__init__(parent)
        self.stencil_manager = stencil_manager
        self.current_stencils = []
        self.selected_stencil = None

        self.setup_ui()
        self.load_stencils()  # Carrega dados de exemplo

    def setup_ui(self):
        """Configura interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Barra superior (busca + filtros + botões)
        top_bar = self.create_top_bar()
        layout.addWidget(top_bar)

        # Splitter horizontal (lista | detalhes)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # TreeView (esquerda)
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["Código", "Descrição", "Status", "Última Medição"])
        self.tree_widget.setColumnWidth(0, 150)
        self.tree_widget.setColumnWidth(1, 250)
        self.tree_widget.setColumnWidth(2, 100)
        self.tree_widget.setColumnWidth(3, 150)
        self.tree_widget.itemClicked.connect(self.on_item_clicked)
        splitter.addWidget(self.tree_widget)

        # Painel de detalhes (direita)
        details_panel = self.create_details_panel()
        splitter.addWidget(details_panel)

        # Proporção do splitter (60% | 40%)
        splitter.setStretchFactor(0, 6)
        splitter.setStretchFactor(1, 4)

        layout.addWidget(splitter, 1)  # Ocupa todo espaço restante

        # Barra de status do hardware
        self.hw_status_bar = HardwareStatusBar()
        self.hw_status_bar.status_clicked.connect(self.on_hardware_status_clicked)
        layout.addWidget(self.hw_status_bar)

    def create_top_bar(self) -> QWidget:
        """Cria barra superior com filtros e botões"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Busca
        layout.addWidget(QLabel("Buscar:"))
        self.search_input = SearchLineEdit()
        self.search_input.searchPerformed.connect(self.filter_stencils)
        layout.addWidget(self.search_input)

        # Filtro de período
        layout.addWidget(QLabel("Período:"))
        self.period_combo = QComboBox()
        self.period_combo.addItems([
            "Últimas 10",
            "7 dias",
            "30 dias",
            "60 dias",
            "90 dias",
            "180 dias",
            "365 dias"
        ])
        self.period_combo.setMinimumWidth(120)
        self.period_combo.currentTextChanged.connect(self.on_filter_changed)
        layout.addWidget(self.period_combo)

        # Filtro de status
        layout.addWidget(QLabel("Status:"))
        self.status_combo = QComboBox()
        self.status_combo.addItems([
            "Todos",
            "A-AUTO",
            "A-USER",
            "REPROV",
            "Pendentes"
        ])
        self.status_combo.setMinimumWidth(120)
        self.status_combo.currentTextChanged.connect(self.on_filter_changed)
        layout.addWidget(self.status_combo)

        layout.addStretch()

        # Botão código de barras
        self.barcode_button = QPushButton("📷 Escanear Código")
        self.barcode_button.setMinimumHeight(35)
        self.barcode_button.clicked.connect(self.on_scan_barcode_clicked)
        layout.addWidget(self.barcode_button)

        return widget

    def create_details_panel(self) -> QWidget:
        """Cria painel de detalhes do stencil"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)

        # Título
        title_label = QLabel("Detalhes do Stencil")
        title_font = title_label.font()
        title_font.setBold(True)
        title_font.setPointSize(14)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # Scroll area para detalhes
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        self.details_content = QWidget()
        details_layout = QVBoxLayout(self.details_content)

        # Placeholder (será preenchido ao selecionar item)
        self.details_placeholder = QLabel(
            "📋 Selecione um stencil para ver detalhes\n\n"
            "Clique em um item na lista para exibir informações completas."
        )
        self.details_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.details_placeholder.setStyleSheet("color: #888; padding: 40px; font-size: 12px;")
        details_layout.addWidget(self.details_placeholder)

        scroll.setWidget(self.details_content)
        layout.addWidget(scroll, 1)

        # Botão inspecionar
        self.inspect_button = QPushButton("🔍 Inspecionar Stencil")
        self.inspect_button.setMinimumHeight(45)
        self.inspect_button.setEnabled(False)
        self.inspect_button.clicked.connect(self.on_inspect_clicked)
        layout.addWidget(self.inspect_button)

        return panel

    def load_stencils(self):
        """Carrega lista de stencils (dados de exemplo)"""
        # TODO: Carregar do stencil_manager
        # Por enquanto, dados de exemplo para testes
        self.current_stencils = [
            {
                "code": "STENCIL-ABC-123",
                "description": "Stencil Principal - Linha 1",
                "status": "approved_auto",
                "last_measurement": "15/12/2025 14:30",
                "recipe": "Limpeza Padrão",
                "tension_avg": 32.5,
                "measurements_count": 5
            },
            {
                "code": "STENCIL-XYZ-456",
                "description": "Stencil Secundário - Linha 2",
                "status": "approved_user",
                "last_measurement": "14/12/2025 09:15",
                "recipe": "Limpeza Reforçada",
                "tension_avg": 30.2,
                "measurements_count": 3
            },
            {
                "code": "STENCIL-DEF-789",
                "description": "Stencil Defeito - Protótipo",
                "status": "rejected",
                "last_measurement": "13/12/2025 16:45",
                "recipe": "Protótipo",
                "tension_avg": 28.7,
                "measurements_count": 2
            },
            {
                "code": "STENCIL-GHI-012",
                "description": "Stencil Teste - Novo Design",
                "status": "pending",
                "last_measurement": "-",
                "recipe": "Teste",
                "tension_avg": None,
                "measurements_count": 0
            }
        ]

        self.populate_tree()

    def populate_tree(self, filtered_stencils=None):
        """Popula TreeView com stencils"""
        self.tree_widget.clear()

        stencils = filtered_stencils or self.current_stencils

        for stencil in stencils:
            item = QTreeWidgetItem()
            item.setText(0, stencil["code"])
            item.setText(1, stencil["description"])
            item.setText(3, stencil.get("last_measurement", "-"))

            # Badge de status
            status_badge = StatusBadge(stencil["status"])
            self.tree_widget.setItemWidget(item, 2, status_badge)

            # Armazena dados completos no item
            item.setData(0, Qt.ItemDataRole.UserRole, stencil)

            self.tree_widget.addTopLevelItem(item)

    def on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Handler: Item clicado na TreeView"""
        stencil_data = item.data(0, Qt.ItemDataRole.UserRole)
        self.selected_stencil = stencil_data
        self.show_details(stencil_data)
        self.program_selected.emit(stencil_data)
        self.inspect_button.setEnabled(True)

    def show_details(self, stencil: dict):
        """Exibe detalhes do stencil no painel lateral"""
        # Limpa conteúdo anterior
        for i in reversed(range(self.details_content.layout().count())):
            self.details_content.layout().itemAt(i).widget().setParent(None)

        # Cria layout novo
        layout = QVBoxLayout(self.details_content)

        # Código
        code_label = QLabel(f"Código: {stencil['code']}")
        code_font = code_label.font()
        code_font.setBold(True)
        code_font.setPointSize(12)
        code_label.setFont(code_font)
        layout.addWidget(code_label)

        # Descrição
        desc_label = QLabel(stencil['description'])
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(desc_label)

        # Linha separadora
        line = QLabel()
        line.setFrameStyle(QLabel.Shape.HLine | QLabel.Shadow.Sunken)
        layout.addWidget(line)

        # Detalhes
        details_html = f"""
        <table cellpadding="5">
            <tr><td><b>Status:</b></td><td>{self._get_status_label(stencil['status'])}</td></tr>
            <tr><td><b>Receita:</b></td><td>{stencil.get('recipe', '-')}</td></tr>
            <tr><td><b>Última Medição:</b></td><td>{stencil.get('last_measurement', '-')}</td></tr>
        """

        if stencil.get('tension_avg'):
            details_html += f"""
            <tr><td><b>Tensão Média:</b></td><td>{stencil['tension_avg']:.1f} N/cm</td></tr>
            <tr><td><b>Medições:</b></td><td>{stencil['measurements_count']}</td></tr>
            """

        details_html += "</table>"

        details_label = QLabel(details_html)
        details_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(details_label)

        layout.addStretch()

    def _get_status_label(self, status: str) -> str:
        """Retorna label legível do status"""
        labels = {
            "approved_auto": "✅ Aprovado Automático",
            "approved_user": "✅ Aprovado (c/ Julgamento)",
            "rejected": "❌ Reprovado",
            "pending": "⏳ Pendente"
        }
        return labels.get(status, status.upper())

    def filter_stencils(self, search_term=""):
        """Filtra stencils por termo de busca"""
        if not search_term:
            self.populate_tree(self.current_stencils)
            return

        search_lower = search_term.lower()
        filtered = [
            s for s in self.current_stencils
            if search_lower in s["code"].lower() or
               search_lower in s["description"].lower()
        ]

        self.populate_tree(filtered)

    def on_filter_changed(self):
        """Handler: Filtro mudou (período ou status)"""
        # TODO: Implementar filtros de período e status
        # Por enquanto, apenas log
        period = self.period_combo.currentText()
        status = self.status_combo.currentText()
        logger.debug(f"Filtros: Período={period}, Status={status}")

    def on_scan_barcode_clicked(self):
        """Handler: Botão Escanear Código clicado"""
        # TODO: Implementar leitura de código de barras
        logger.info("Escanear código de barras - não implementado ainda")

    def on_inspect_clicked(self):
        """Handler: Botão Inspecionar clicado"""
        if self.selected_stencil:
            self.inspect_requested.emit(self.selected_stencil)
            logger.info(f"Solicitar inspeção: {self.selected_stencil['code']}")

    def on_hardware_status_clicked(self, hardware: str):
        """Handler: Status de hardware clicado"""
        logger.info(f"Status {hardware} clicado - abrir configuração")
        # TODO: Abrir dialog de configuração de conexões
