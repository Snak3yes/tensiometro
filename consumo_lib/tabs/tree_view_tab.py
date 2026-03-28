"""Aba de listagem de stencils cadastrados."""

import logging
from datetime import datetime, timedelta

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from consumo_lib.ui import COLORS, SPACE, TYPO
from consumo_lib.ui.widget_standards import StandardButton
from consumo_lib.widgets.hardware_status_bar import HardwareStatusBar
from consumo_lib.widgets.search_line_edit import SearchLineEdit
from consumo_lib.widgets.status_badge import StatusBadge

logger = logging.getLogger(__name__)


class TreeViewTab(QWidget):
    """
    Aba principal com lista de stencils.

    Sinais:
        program_selected: Emitido ao selecionar um stencil
        inspect_requested: Sinal legado de compatibilidade
    """

    program_selected = pyqtSignal(dict)
    inspect_requested = pyqtSignal(dict)

    def __init__(self, stencil_manager=None, parent=None):
        super().__init__(parent)
        self.stencil_manager = stencil_manager
        self.current_stencils = []
        self.selected_stencil = None

        self.setup_ui()
        self.load_stencils()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        top_bar = self.create_top_bar()
        layout.addWidget(top_bar)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["Código", "Descrição", "Status", "Última Medição"])
        self.tree_widget.setColumnWidth(0, 170)
        self.tree_widget.setColumnWidth(1, 260)
        self.tree_widget.setColumnWidth(2, 110)
        self.tree_widget.setColumnWidth(3, 170)
        self.tree_widget.itemClicked.connect(self.on_item_clicked)
        splitter.addWidget(self.tree_widget)

        details_panel = self.create_details_panel()
        splitter.addWidget(details_panel)

        splitter.setStretchFactor(0, 6)
        splitter.setStretchFactor(1, 4)
        layout.addWidget(splitter, 1)

        self.hw_status_bar = HardwareStatusBar()
        self.hw_status_bar.status_clicked.connect(self.on_hardware_status_clicked)
        layout.addWidget(self.hw_status_bar)

    def create_top_bar(self) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(QLabel("Buscar:"))
        self.search_input = SearchLineEdit()
        self.search_input.searchPerformed.connect(self.filter_stencils)
        layout.addWidget(self.search_input)

        layout.addWidget(QLabel("Período:"))
        self.period_combo = QComboBox()
        self.period_combo.addItems([
            "Últimas 10",
            "7 dias",
            "30 dias",
            "60 dias",
            "90 dias",
            "180 dias",
            "365 dias",
        ])
        self.period_combo.setMinimumWidth(120)
        self.period_combo.currentTextChanged.connect(self.on_filter_changed)
        layout.addWidget(self.period_combo)

        layout.addWidget(QLabel("Status:"))
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Todos", "Ativos", "Alerta", "Retirados"])
        self.status_combo.setMinimumWidth(120)
        self.status_combo.currentTextChanged.connect(self.on_filter_changed)
        layout.addWidget(self.status_combo)

        layout.addStretch()
        return widget

    def create_details_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)

        title_label = QLabel("Detalhes do Stencil")
        title_label.setFont(TYPO.get_font(TYPO.HEADLINE_SMALL, bold=True))
        layout.addWidget(title_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        self.details_content = QWidget()
        details_layout = QVBoxLayout(self.details_content)

        self.details_placeholder = QLabel(
            "Selecione um stencil para ver detalhes\n\n"
            "Clique em um item na lista para exibir informações completas."
        )
        self.details_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.details_placeholder.setStyleSheet(
            f"color: {COLORS.TEXT_HINT}; padding: {SPACE.XL * 2}px; font-size: {TYPO.BODY_SMALL}px;"
        )
        details_layout.addWidget(self.details_placeholder)

        scroll.setWidget(self.details_content)
        layout.addWidget(scroll, 1)

        self.history_button = StandardButton("Histórico")
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

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(SPACE.MD)
        buttons_layout.addWidget(self.history_button)
        layout.addLayout(buttons_layout)

        return panel

    def load_stencils(self):
        """Carrega lista real de stencils cadastrados."""
        self.current_stencils = []

        if self.stencil_manager is None:
            self.populate_tree([])
            return

        try:
            for stencil in self.stencil_manager.list_stencils():
                history = self.stencil_manager.get_tension_history(stencil.code, limit=1)
                latest_record = history[0] if history else None

                self.current_stencils.append({
                    "code": stencil.code,
                    "description": stencil.description or "",
                    "status": stencil.status,
                    "last_measurement": stencil.last_inspection or "-",
                    "recipe": stencil.recipe_name or "",
                    "tension_avg": latest_record.average_tension if latest_record else None,
                    "measurements_count": stencil.inspection_count,
                    "created_at": stencil.created_at,
                    "notes": stencil.notes or "",
                })
        except Exception as exc:
            logger.error("Erro ao carregar stencils na TreeView: %s", exc)
            self.current_stencils = []

        self.apply_filters()

    def populate_tree(self, filtered_stencils=None):
        self.tree_widget.clear()
        stencils = filtered_stencils if filtered_stencils is not None else self.current_stencils

        for stencil in stencils:
            item = QTreeWidgetItem()
            item.setText(0, stencil["code"])
            item.setText(1, stencil["description"])
            item.setText(3, self._format_datetime(stencil.get("last_measurement")))

            status_badge = StatusBadge(stencil.get("status", "pending"))
            self.tree_widget.setItemWidget(item, 2, status_badge)

            item.setData(0, Qt.ItemDataRole.UserRole, stencil)
            self.tree_widget.addTopLevelItem(item)

    def on_item_clicked(self, item: QTreeWidgetItem, column: int):
        stencil_data = item.data(0, Qt.ItemDataRole.UserRole)
        self.selected_stencil = stencil_data
        self.show_details(stencil_data)
        self.program_selected.emit(stencil_data)
        self.history_button.setEnabled(True)

    def show_details(self, stencil: dict):
        layout = self.details_content.layout()
        while layout.count():
            child = layout.takeAt(0)
            widget = child.widget()
            if widget is not None:
                widget.deleteLater()

        code_label = QLabel(f"Código: {stencil['code']}")
        code_label.setFont(TYPO.get_font(TYPO.BODY_LARGE, bold=True))
        layout.addWidget(code_label)

        desc_label = QLabel(stencil["description"] or "(sem descrição)")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(
            f"color: {COLORS.TEXT_HINT}; margin-bottom: {SPACE.SM}px;"
        )
        layout.addWidget(desc_label)

        line = QLabel()
        line.setFrameStyle(QLabel.Shape.HLine | QLabel.Shadow.Sunken)
        layout.addWidget(line)

        notes = stencil.get("notes", "").strip() or "-"
        created_at = self._format_datetime(stencil.get("created_at"))
        last_measurement = self._format_datetime(stencil.get("last_measurement"))
        tension_avg = stencil.get("tension_avg")

        details_html = f"""
        <style>
            .label {{ color: {COLORS.TEXT_HINT}; font-weight: bold; }}
            .value {{ color: {COLORS.TEXT_PRIMARY}; }}
        </style>
        <table cellpadding="5" cellspacing="0">
            <tr><td class="label">Status:</td><td class="value">{self._get_status_label(stencil['status'])}</td></tr>
            <tr><td class="label">Receita:</td><td class="value">{stencil.get('recipe', '-') or '-'}</td></tr>
            <tr><td class="label">Última Medição:</td><td class="value">{last_measurement}</td></tr>
        """

        if tension_avg is not None:
            details_html += f"""
            <tr><td class="label">Tensão Média:</td><td class="value">{tension_avg:.1f} N/cm</td></tr>
            """

        details_html += f"""
            <tr><td class="label">Total de Medições:</td><td class="value">{stencil.get('measurements_count', 0)}</td></tr>
            <tr><td colspan="2"><hr style="border: 0; border-top: 1px solid {COLORS.BORDER}; margin: {SPACE.SM}px 0;"></td></tr>
            <tr><td class="label">Criado em:</td><td class="value">{created_at}</td></tr>
            <tr><td class="label">Observações:</td><td class="value">{notes}</td></tr>
        </table>
        """

        details_label = QLabel(details_html)
        details_label.setTextFormat(Qt.TextFormat.RichText)
        details_label.setWordWrap(True)
        layout.addWidget(details_label)
        layout.addStretch()

    def _get_status_label(self, status: str) -> str:
        labels = {
            "active": "🟢 Ativo",
            "warning": "🟡 Alerta",
            "retired": "🔴 Retirado",
            "pending": "⏳ Pendente",
        }
        return labels.get(status, status.upper())

    def filter_stencils(self, search_term=""):
        self.apply_filters(search_term=search_term)

    def on_filter_changed(self):
        self.apply_filters()

    def apply_filters(self, search_term: str | None = None):
        if search_term is None:
            search_term = self.search_input.text().strip()

        filtered = list(self.current_stencils)

        if search_term:
            term = search_term.lower()
            filtered = [
                stencil for stencil in filtered
                if term in stencil["code"].lower()
                or term in stencil["description"].lower()
            ]

        status_map = {
            "Todos": None,
            "Ativos": "active",
            "Alerta": "warning",
            "Retirados": "retired",
        }
        status_filter = status_map.get(self.status_combo.currentText())
        if status_filter:
            filtered = [s for s in filtered if s.get("status") == status_filter]

        period_text = self.period_combo.currentText()
        if period_text == "Últimas 10":
            filtered = filtered[:10]
        else:
            days = {
                "7 dias": 7,
                "30 dias": 30,
                "60 dias": 60,
                "90 dias": 90,
                "180 dias": 180,
                "365 dias": 365,
            }.get(period_text)
            if days:
                cutoff = datetime.now() - timedelta(days=days)
                filtered = [
                    stencil for stencil in filtered
                    if (dt := self._parse_datetime(stencil.get("last_measurement"))) is not None
                    and dt >= cutoff
                ]

        self.populate_tree(filtered)

    def show_history(self):
        if self.selected_stencil:
            from consumo_lib.dialogs.stencil import StencilFullHistoryDialog

            dialog = StencilFullHistoryDialog(
                self.stencil_manager,
                self.selected_stencil["code"],
                self,
            )
            dialog.exec()
        else:
            logger.warning("Tentativa de abrir histórico sem stencil selecionado")

    def on_hardware_status_clicked(self, hardware: str):
        logger.info("Status %s clicado - abrir configuração", hardware)

    def _parse_datetime(self, value):
        if not value or value == "-":
            return None
        try:
            return datetime.fromisoformat(value)
        except (TypeError, ValueError):
            return None

    def _format_datetime(self, value):
        parsed = self._parse_datetime(value)
        if parsed is None:
            return value or "-"
        return parsed.strftime("%d/%m/%Y %H:%M")
