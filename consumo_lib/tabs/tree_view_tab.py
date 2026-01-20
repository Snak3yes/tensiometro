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
from PyQt6.QtGui import QFont

from consumo_lib.widgets.search_line_edit import SearchLineEdit
from consumo_lib.widgets.status_badge import StatusBadge
from consumo_lib.widgets.hardware_status_bar import HardwareStatusBar
from consumo_lib.ui import COLORS, TYPO, SPACE

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

        return widget

    def create_details_panel(self) -> QWidget:
        """Cria painel de detalhes do stencil"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)

        # Título
        title_label = QLabel("Detalhes do Stencil")
        title_label.setFont(TYPO.get_font(TYPO.HEADLINE_SMALL, bold=True))
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
        self.details_placeholder.setStyleSheet(f"color: {COLORS.TEXT_HINT}; padding: {SPACE.XL * 2}px; font-size: {TYPO.BODY_SMALL}px;")
        details_layout.addWidget(self.details_placeholder)

        scroll.setWidget(self.details_content)
        layout.addWidget(scroll, 1)

        # Botão inspecionar
        self.inspect_button = QPushButton("🔍 Inspecionar Stencil")
        self.inspect_button.setMinimumHeight(45)
        self.inspect_button.setEnabled(False)
        self.inspect_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.PRIMARY};
                color: {COLORS.ON_PRIMARY};
                font-size: {TYPO.BODY_LARGE}px;
                font-weight: bold;
                border-radius: 4px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.PRIMARY_DARK};
            }}
            QPushButton:pressed {{
                background-color: {COLORS.PRIMARY_DARK};
            }}
            QPushButton:disabled {{
                background-color: {COLORS.SURFACE};
                color: {COLORS.TEXT_HINT};
            }}
        """)
        self.inspect_button.clicked.connect(self.on_inspect_clicked)

        # Botão histórico (NOVO - FASE 7)
        self.history_button = QPushButton("📋 Histórico")
        self.history_button.setMinimumHeight(45)
        self.history_button.setEnabled(False)
        self.history_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.SECONDARY};
                color: {COLORS.ON_SECONDARY};
                font-size: {TYPO.BODY_LARGE}px;
                font-weight: bold;
                border-radius: 4px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.SECONDARY_DARK};
            }}
            QPushButton:pressed {{
                background-color: {COLORS.SECONDARY_DARK};
            }}
            QPushButton:disabled {{
                background-color: {COLORS.SURFACE};
                color: {COLORS.TEXT_HINT};
            }}
        """)
        self.history_button.clicked.connect(self.show_history)

        # Layout horizontal para os botões
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(SPACE.MD)
        buttons_layout.addWidget(self.inspect_button)
        buttons_layout.addWidget(self.history_button)

        layout.addLayout(buttons_layout)

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
                "measurements_count": 5,
                # Dados adicionais hipotéticos
                "dimensions": "520mm x 480mm",
                "thickness": "120 µm (5 mil)",
                "manufacturer": "Stencils International Ltda",
                "manufacture_date": "2023-08-15",
                "aperture_count": 2847,
                "area_total": "0.145 m²",
                "alloy_type": "AISI 304",
                "frame_type": "Cast Aluminum H-frame",
                "last_cleaning": "10/12/2025",
                "inspection_cycle": "1000 impressões"
            },
            {
                "code": "STENCIL-XYZ-456",
                "description": "Stencil Secundário - Linha 2",
                "status": "approved_user",
                "last_measurement": "14/12/2025 09:15",
                "recipe": "Limpeza Reforçada",
                "tension_avg": 30.2,
                "measurements_count": 3,
                # Dados adicionais hipotéticos
                "dimensions": "480mm x 420mm",
                "thickness": "100 µm (4 mil)",
                "manufacturer": "Precision Stencils Inc",
                "manufacture_date": "2024-01-20",
                "aperture_count": 1523,
                "area_total": "0.098 m²",
                "alloy_type": "AISI 304L",
                "frame_type": "Cast Aluminum H-frame",
                "last_cleaning": "12/12/2025",
                "inspection_cycle": "800 impressões"
            },
            {
                "code": "STENCIL-DEF-789",
                "description": "Stencil Defeito - Protótipo",
                "status": "rejected",
                "last_measurement": "13/12/2025 16:45",
                "recipe": "Protótipo",
                "tension_avg": 28.7,
                "measurements_count": 2,
                # Dados adicionais hipotéticos
                "dimensions": "600mm x 550mm",
                "thickness": "150 µm (6 mil)",
                "manufacturer": "ProtoStencils SA",
                "manufacture_date": "2022-11-05",
                "aperture_count": 4521,
                "area_total": "0.220 m²",
                "alloy_type": "AISI 316",
                "frame_type": "Tubular Stainless Steel",
                "last_cleaning": "08/12/2025",
                "inspection_cycle": "1500 impressões"
            },
            {
                "code": "STENCIL-GHI-012",
                "description": "Stencil Teste - Novo Design",
                "status": "pending",
                "last_measurement": "-",
                "recipe": "Teste",
                "tension_avg": None,
                "measurements_count": 0,
                # Dados adicionais hipotéticos
                "dimensions": "380mm x 320mm",
                "thickness": "127 µm (5 mil)",
                "manufacturer": "Stencils International Ltda",
                "manufacture_date": "2025-01-10",
                "aperture_count": 856,
                "area_total": "0.058 m²",
                "alloy_type": "AISI 304",
                "frame_type": "Cast Aluminum H-frame",
                "last_cleaning": "Nova",
                "inspection_cycle": "500 impressões"
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
        self.history_button.setEnabled(True)

    def show_details(self, stencil: dict):
        """Exibe detalhes do stencil no painel lateral"""
        # Limpa conteúdo anterior
        for i in reversed(range(self.details_content.layout().count())):
            self.details_content.layout().itemAt(i).widget().setParent(None)

        # Cria layout novo
        layout = QVBoxLayout(self.details_content)

        # Código
        code_label = QLabel(f"Código: {stencil['code']}")
        code_label.setFont(TYPO.get_font(TYPO.BODY_LARGE, bold=True))
        layout.addWidget(code_label)

        # Descrição
        desc_label = QLabel(stencil['description'])
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"color: {COLORS.TEXT_HINT}; margin-bottom: {SPACE.SM}px;")
        layout.addWidget(desc_label)

        # Linha separadora
        line = QLabel()
        line.setFrameStyle(QLabel.Shape.HLine | QLabel.Shadow.Sunken)
        layout.addWidget(line)

        # Detalhes principais
        details_html = f"""
        <style>
            .label {{ color: {COLORS.TEXT_HINT}; font-weight: bold; }}
            .value {{ color: {COLORS.TEXT_PRIMARY}; }}
        </style>
        <table cellpadding="5" cellspacing="0">
        """

        # Status
        details_html += f"""
            <tr><td class="label">Status:</td><td class="value">{self._get_status_label(stencil['status'])}</td></tr>
            <tr><td class="label">Receita:</td><td class="value">{stencil.get('recipe', '-')}</td></tr>
            <tr><td class="label">Última Medição:</td><td class="value">{stencil.get('last_measurement', '-')}</td></tr>
        """

        # Dados de tensão (se disponível)
        if stencil.get('tension_avg'):
            details_html += f"""
            <tr><td class="label">Tensão Média:</td><td class="value">{stencil['tension_avg']:.1f} N/cm</td></tr>
            <tr><td class="label">Medições:</td><td class="value">{stencil['measurements_count']}</td></tr>
            """

        # Linha separadora
        details_html += f"""
            <tr><td colspan="2"><hr style="border: 0; border-top: 1px solid {COLORS.OUTLINE}; margin: {SPACE.SM}px 0;"></td></tr>
        """

        # Dados físicos
        details_html += f"""
            <tr><td class="label">Dimensões:</td><td class="value">{stencil.get('dimensions', '-')}</td></tr>
            <tr><td class="label">Espessura:</td><td class="value">{stencil.get('thickness', '-')}</td></tr>
            <tr><td class="label">Fabricante:</td><td class="value">{stencil.get('manufacturer', '-')}</td></tr>
            <tr><td class="label">Data Fabricação:</td><td class="value">{stencil.get('manufacture_date', '-')}</td></tr>
            <tr><td class="label">Aberturas:</td><td class="value">{stencil.get('aperture_count', 0):,}</td></tr>
            <tr><td class="label">Área Total:</td><td class="value">{stencil.get('area_total', '-')}</td></tr>
            <tr><td class="label">Liga Metálica:</td><td class="value">{stencil.get('alloy_type', '-')}</td></tr>
            <tr><td class="label">Tipo Frame:</td><td class="value">{stencil.get('frame_type', '-')}</td></tr>
        """

        # Dados de manutenção
        details_html += f"""
            <tr><td colspan="2"><hr style="border: 0; border-top: 1px solid {COLORS.OUTLINE}; margin: {SPACE.SM}px 0;"></td></tr>
        """
        details_html += f"""
            <tr><td class="label">Última Limpeza:</td><td class="value">{stencil.get('last_cleaning', '-')}</td></tr>
            <tr><td class="label">Ciclo Inspeção:</td><td class="value">{stencil.get('inspection_cycle', '-')}</td></tr>
        """

        details_html += "</table>"

        details_label = QLabel(details_html)
        details_label.setTextFormat(Qt.TextFormat.RichText)
        details_label.setWordWrap(True)
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

    def on_inspect_clicked(self):
        """Handler: Botão Inspecionar clicado"""
        if self.selected_stencil:
            self.inspect_requested.emit(self.selected_stencil)
            logger.info(f"Solicitar inspeção: {self.selected_stencil['code']}")

    def show_history(self):
        """Handler: Botão Histórico clicado"""
        if self.selected_stencil:
            # Chama método do MainWindow para exibir histórico
            main_window = self.parent()
            while main_window and not hasattr(main_window, 'show_inspection_history'):
                main_window = main_window.parent()

            if main_window and hasattr(main_window, 'show_inspection_history'):
                main_window.show_inspection_history(self.selected_stencil['code'])
            else:
                logger.error("Não foi possível encontrar MainWindow para exibir histórico")
                QMessageBox.warning(
                    self,
                    "Erro",
                    "Não foi possível abrir o histórico.\nContacte o suporte técnico."
                )
        else:
            logger.warning("Tentativa de abrir histórico sem stencil selecionado")

    def on_hardware_status_clicked(self, hardware: str):
        """Handler: Status de hardware clicado"""
        logger.info(f"Status {hardware} clicado - abrir configuração")
        # TODO: Abrir dialog de configuração de conexões
