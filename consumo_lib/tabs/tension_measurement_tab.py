"""
Aba Unificada de Medição de Tensão

Combina lista de stencils e visualização de tensão em layout 70%/30%.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QGroupBox, QLabel, QLineEdit, QComboBox,
    QTreeWidget, QTreeWidgetItem,
    QDoubleSpinBox,
    QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from consumo_lib.ui import COLORS, TYPO, SPACE, DIM
from consumo_lib.ui.widget_standards import StandardButton
from consumo_lib.widgets.mini_tension_heatmap import MiniTensionHeatmapWidget
from consumo_lib.widgets.hardware_status_bar import HardwareStatusBar
from consumo_lib.widgets.status_badge import StatusBadge

from aoi_lib.recipe_manager import TensionAcceptance

logger = logging.getLogger(__name__)


class TensionMeasurementTab(QWidget):
    """
    Aba unificada de Medição de Tensão.

    Combina lista de stencils e visualização de tensão em layout 70%/30%.
    """

    program_selected = pyqtSignal(dict)

    def __init__(self, stencil_manager=None, parent=None):
        super().__init__(parent)
        self.stencil_manager = stencil_manager
        self.current_stencils: List[Dict] = []
        self.selected_stencil: Optional[Dict] = None
        self.last_file_path: Optional[str] = None
        self.measurements_data: Optional[Dict] = None
        self.acceptance_criteria: Optional[TensionAcceptance] = None

        self.setup_ui()
        self.load_stencils()

    def setup_ui(self):
        """Configura a interface da aba."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Título da aba
        title = QLabel("Medição de Tensão")
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

        # Customizar altura dos items (45px) e selected background
        self.tree_widget.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {COLORS.BACKGROUND};
                border: 1px solid {COLORS.BORDER};
                border-radius: {DIM.RADIUS_SM}px;
            }}
            QTreeWidget::item {{
                min-height: 45px;
                padding: {SPACE.SM}px;
            }}
            QTreeWidget::item:selected {{
                background-color: {COLORS.PRIMARY};
                color: {COLORS.BACKGROUND};
            }}
            QTreeWidget::item:hover {{
                background-color: {COLORS.SURFACE};
            }}
        """)

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
        layout.setSpacing(8)

        # Buscar
        layout.addWidget(QLabel("Buscar:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar programas...")
        self.search_input.textChanged.connect(self.filter_stencils)
        layout.addWidget(self.search_input, 1)

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

        # Ordenar (NOVO)
        layout.addWidget(QLabel("Ordenar:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            "Mais recentes", "Mais antigos",
            "Código (A-Z)", "Código (Z-A)",
            "Tensão (maior)", "Tensão (menor)"
        ])
        self.sort_combo.currentTextChanged.connect(self.apply_filters)
        layout.addWidget(self.sort_combo)

        layout.addStretch()
        return widget

    def create_details_panel(self) -> QWidget:
        """Cria painel de detalhes do stencil selecionado."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        title = QLabel("Detalhes do Stencil Selecionado")
        title.setFont(TYPO.get_font(TYPO.BODY_LARGE, bold=True))
        layout.addWidget(title)

        # Conteúdo dos detalhes (preenchido quando seleciona)
        self.details_label = QLabel(
            "Selecione um stencil para ver detalhes"
        )
        self.details_label.setStyleSheet(f"color: {COLORS.TEXT_HINT};")
        layout.addWidget(self.details_label)

        # Botões
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_history = StandardButton(
            "Histórico",
            variant="secondary",
            semantic_size="inline-secondary"
        )
        self.btn_history.setEnabled(False)
        self.btn_history.clicked.connect(self.show_history)
        btn_layout.addWidget(self.btn_history)

        self.btn_view = StandardButton(
            "Ver",
            variant="primary-green",
            semantic_size="inline-primary"
        )
        self.btn_view.setEnabled(False)
        self.btn_view.clicked.connect(self.view_stencil_details)
        btn_layout.addWidget(self.btn_view)

        layout.addLayout(btn_layout)
        return widget

    def create_right_panel(self) -> QWidget:
        """Cria painel direito com visualização de tensão (30% - 340px largura)."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # HEADER: Título + Botões (lado a lado)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        # Títulos (esquerda)
        titles_layout = QVBoxLayout()
        titles_layout.setSpacing(0)
        self.viz_title = QLabel("Visualização")
        self.viz_title.setFont(TYPO.get_font(TYPO.TITLE_SMALL, bold=True))  # 13px bold
        titles_layout.addWidget(self.viz_title)

        self.viz_subtitle = QLabel("Selecione um stencil")
        self.viz_subtitle.setStyleSheet(
            f"color: {COLORS.TEXT_HINT}; font-size: 9px;"
        )
        titles_layout.addWidget(self.viz_subtitle)
        header_layout.addLayout(titles_layout)

        # Botões (direita) - 75x28px e 65x28px conforme proposta
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.btn_load = StandardButton(
            "Carregar",
            variant="primary-green",
            semantic_size="inline-primary"  # 24x60px
        )
        self.btn_load.setFixedHeight(28)
        self.btn_load.setMinimumWidth(75)
        self.btn_load.clicked.connect(self.load_tension_file)
        btn_layout.addWidget(self.btn_load)

        self.btn_reload = StandardButton(
            "Recarregar",
            variant="secondary",
            semantic_size="inline-compact"  # 20x50px
        )
        self.btn_reload.setFixedHeight(28)
        self.btn_reload.setMinimumWidth(65)
        self.btn_reload.setEnabled(False)
        self.btn_reload.clicked.connect(self.reload_tension)
        btn_layout.addWidget(self.btn_reload)

        header_layout.addLayout(btn_layout)
        layout.addLayout(header_layout)

        # CRITÉRIOS: Layout horizontal compacto (spinboxes 45x18px, labels 9px)
        criteria_group = self.create_criteria_group()
        layout.addWidget(criteria_group)

        # HEATMAP: 310x280px fixo
        self.heatmap = MiniTensionHeatmapWidget()
        self.heatmap.setMinimumSize(310, 280)
        self.heatmap.setMaximumSize(310, 280)
        self.heatmap.setSizePolicy(
            self.heatmap.sizePolicy().horizontalPolicy(),
            self.heatmap.sizePolicy().verticalPolicy()
        )
        layout.addWidget(self.heatmap)

        # RESULTADO: Badge 310x40px
        self.result_badge = QLabel("---")
        self.result_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_badge.setFixedHeight(40)
        self.result_badge.setFixedWidth(310)
        self.result_badge.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
                background-color: {COLORS.TEXT_DISABLED};
                color: {COLORS.TEXT_PRIMARY};
            }}
        """)
        layout.addWidget(self.result_badge)

        # ESTATÍSTICAS: GroupBox 310x90px - 3 linhas organizadas
        stats_group = QGroupBox("Estatísticas")
        stats_group.setMinimumWidth(310)
        stats_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: 10px;
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        stats_layout = QVBoxLayout(stats_group)
        stats_layout.setContentsMargins(10, 20, 10, 10)
        stats_layout.setSpacing(4)

        # Linha 1: OK/WARN/NOK com porcentagens
        self.stats_counts_label = QLabel("🟢 OK: 0 (0%) | 🟡 WARN: 0 (0%) | 🔴 NOK: 0 (0%)")
        self.stats_counts_label.setStyleSheet(f"font-size: 9px; color: {COLORS.TEXT_PRIMARY};")
        stats_layout.addWidget(self.stats_counts_label)

        # Linha 2: Min/Máx/Média
        self.stats_values_label = QLabel("Mín: -- | Máx: -- | Média: --")
        self.stats_values_label.setStyleSheet(f"font-size: 9px; color: {COLORS.TEXT_SECONDARY};")
        stats_layout.addWidget(self.stats_values_label)

        # Linha 3: Total
        self.stats_total_label = QLabel("Total: 0 pontos")
        self.stats_total_label.setStyleSheet(f"font-size: 9px; color: {COLORS.TEXT_HINT};")
        stats_layout.addWidget(self.stats_total_label)

        layout.addWidget(stats_group)

        # LEGENDA: Box horizontal 310x50px
        self.legend_widget = self.create_legend_widget()
        self.legend_widget.setMinimumWidth(310)
        layout.addWidget(self.legend_widget)

        # BOTÃO HISTÓRICO: 310x35px
        self.btn_full_history = StandardButton(
            "Ver Histórico Completo",
            variant="primary-blue",
            semantic_size="inline-primary"
        )
        self.btn_full_history.setFixedHeight(35)
        self.btn_full_history.setMinimumWidth(310)
        self.btn_full_history.clicked.connect(self.show_full_history)
        layout.addWidget(self.btn_full_history)

        # INFO ARQUIVO: GroupBox 310x60px
        self.file_info_group = self.create_file_info_group()
        self.file_info_group.setMinimumWidth(310)
        layout.addWidget(self.file_info_group)

        layout.addStretch()
        return widget

    def create_criteria_group(self) -> QGroupBox:
        """
        Cria grupo de critérios de aceitação (layout compacto horizontal).

        Dimensões da proposta:
        - Container: 310x55px
        - Spinboxes: 45x18px
        - Labels: 9px
        - Botão 'Usar Receita': 100x22px
        """
        group = QGroupBox("Critérios")
        group.setFixedHeight(60)
        group.setFixedWidth(310)
        group.setStyleSheet(f"""
            QGroupBox {{
                font-size: 9px;
                font-weight: bold;
                background-color: {COLORS.SURFACE};
                border-radius: 6px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: {COLORS.TEXT_HINT};
            }}
        """)

        layout = QHBoxLayout(group)
        layout.setContentsMargins(8, 18, 8, 8)
        layout.setSpacing(4)

        # Spinbox stylesheet
        spinbox_style = f"""
            QDoubleSpinBox {{
                background-color: {COLORS.BACKGROUND};
                color: {COLORS.TEXT_PRIMARY};
                border: 1px solid {COLORS.BORDER};
                border-radius: 3px;
                padding: 2px;
                font-size: 9px;
            }}
        """

        # Mín: spinbox 45x18px
        layout.addWidget(QLabel("Mín:"))
        self.spin_min = QDoubleSpinBox()
        self.spin_min.setRange(0, 100)
        self.spin_min.setValue(25.0)
        self.spin_min.setFixedWidth(45)
        self.spin_min.setFixedHeight(18)
        self.spin_min.setStyleSheet(spinbox_style)
        self.spin_min.valueChanged.connect(self.on_criteria_changed)
        layout.addWidget(self.spin_min)

        # Warn↓: spinbox 45x18px
        layout.addWidget(QLabel("Warn↓:"))
        self.spin_warn_low = QDoubleSpinBox()
        self.spin_warn_low.setRange(0, 100)
        self.spin_warn_low.setValue(28.0)
        self.spin_warn_low.setFixedWidth(45)
        self.spin_warn_low.setFixedHeight(18)
        self.spin_warn_low.setStyleSheet(spinbox_style)
        self.spin_warn_low.valueChanged.connect(self.on_criteria_changed)
        layout.addWidget(self.spin_warn_low)

        # Warn↑: spinbox 45x18px
        layout.addWidget(QLabel("Warn↑:"))
        self.spin_warn_high = QDoubleSpinBox()
        self.spin_warn_high.setRange(0, 100)
        self.spin_warn_high.setValue(42.0)
        self.spin_warn_high.setFixedWidth(45)
        self.spin_warn_high.setFixedHeight(18)
        self.spin_warn_high.setStyleSheet(spinbox_style)
        self.spin_warn_high.valueChanged.connect(self.on_criteria_changed)
        layout.addWidget(self.spin_warn_high)

        # Máx: spinbox 45x18px
        layout.addWidget(QLabel("Máx:"))
        self.spin_max = QDoubleSpinBox()
        self.spin_max.setRange(0, 100)
        self.spin_max.setValue(45.0)
        self.spin_max.setFixedWidth(45)
        self.spin_max.setFixedHeight(18)
        self.spin_max.setStyleSheet(spinbox_style)
        self.spin_max.valueChanged.connect(self.on_criteria_changed)
        layout.addWidget(self.spin_max)

        # Botão "Usar Receita": 100x22px
        self.btn_recipe = StandardButton(
            "Receita",
            variant="primary-blue",
            semantic_size="inline-compact"
        )
        self.btn_recipe.setFixedHeight(22)
        self.btn_recipe.setMinimumWidth(70)
        self.btn_recipe.clicked.connect(self.load_criteria_from_recipe)
        layout.addWidget(self.btn_recipe)

        layout.addStretch()
        return group

    def create_legend_widget(self) -> QWidget:
        """Cria widget de legenda horizontal."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        widget.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS.SURFACE};
                border-radius: {DIM.RADIUS_SM}px;
            }}
        """)

        # Item OK
        ok_layout = QHBoxLayout()
        self.ok_indicator = QLabel("●")
        self.ok_indicator.setStyleSheet(f"color: {COLORS.SUCCESS}; font-size: 14px; font-weight: bold;")
        self.ok_label = QLabel(f"OK ({self.spin_warn_low.value()}-{self.spin_warn_high.value()})")
        self.ok_label.setStyleSheet(f"color: {COLORS.SUCCESS}; font-size: {TYPO.LABEL_SMALL}px;")
        ok_layout.addWidget(self.ok_indicator)
        ok_layout.addWidget(self.ok_label)
        ok_layout.addStretch()
        layout.addLayout(ok_layout)

        # Item WARN
        warn_layout = QHBoxLayout()
        self.warn_indicator = QLabel("●")
        self.warn_indicator.setStyleSheet(f"color: {COLORS.WARNING}; font-size: 14px; font-weight: bold;")
        self.warn_label = QLabel("WARN")
        self.warn_label.setStyleSheet(f"color: {COLORS.WARNING}; font-size: {TYPO.LABEL_SMALL}px;")
        warn_layout.addWidget(self.warn_indicator)
        warn_layout.addWidget(self.warn_label)
        warn_layout.addStretch()
        layout.addLayout(warn_layout)

        # Item NOK
        nok_layout = QHBoxLayout()
        self.nok_indicator = QLabel("●")
        self.nok_indicator.setStyleSheet(f"color: {COLORS.ERROR}; font-size: 14px; font-weight: bold;")
        self.nok_label = QLabel("NOK")
        self.nok_label.setStyleSheet(f"color: {COLORS.ERROR}; font-size: {TYPO.LABEL_SMALL}px;")
        nok_layout.addWidget(self.nok_indicator)
        nok_layout.addWidget(self.nok_label)
        nok_layout.addStretch()
        layout.addLayout(nok_layout)

        return widget

    def _update_legend(self):
        """Atualiza textos da legenda com valores dos critérios."""
        self.ok_label.setText(f"OK ({self.spin_warn_low.value()}-{self.spin_warn_high.value()})")

    def create_file_info_group(self) -> QGroupBox:
        """Cria grupo de informações do arquivo."""
        group = QGroupBox("Arquivo")
        group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {TYPO.LABEL_SMALL}px;
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)

        layout = QVBoxLayout(group)
        layout.setContentsMargins(10, 15, 10, 10)
        layout.setSpacing(4)

        self.file_name_label = QLabel("Nenhum arquivo carregado")
        self.file_name_label.setStyleSheet(f"font-size: {TYPO.LABEL_SMALL}px; color: {COLORS.TEXT_PRIMARY};")
        layout.addWidget(self.file_name_label)

        self.file_details_label = QLabel("Grid: -- | Área: --")
        self.file_details_label.setStyleSheet(f"font-size: {TYPO.LABEL_SMALL}px; color: {COLORS.TEXT_HINT};")
        layout.addWidget(self.file_details_label)

        return group

    # ============ MÉTODOS DE LÓGICA ============

    def load_stencils(self):
        """Carrega lista de stencils do manager."""
        self.current_stencils = []

        if self.stencil_manager is None:
            self.populate_tree([])
            return

        try:
            for stencil in self.stencil_manager.list_stencils():
                # Busca histórico de tensão para obter tensão média
                tension_avg = None
                try:
                    history = self.stencil_manager.get_tension_history(
                        stencil.code, limit=1
                    )
                    if history and len(history) > 0:
                        tension_avg = history[0].average_tension
                except Exception:
                    pass

                self.current_stencils.append({
                    "code": stencil.code,
                    "description": stencil.description or "",
                    "status": stencil.status,
                    "last_measurement": stencil.last_inspection or "-",
                    "recipe": stencil.recipe_name or "",
                    "tension_avg": tension_avg,
                    "measurements_count": stencil.inspection_count,
                    "created_at": stencil.created_at,
                    "notes": stencil.notes or "",
                })
        except Exception as exc:
            logger.error("Erro ao carregar stencils: %s", exc)
            self.current_stencils = []

        self.apply_filters()

    def populate_tree(self, filtered_stencils: List[Dict]):
        """Preenche a tree widget com stencils filtrados."""
        self.tree_widget.clear()

        for stencil in filtered_stencils:
            item = QTreeWidgetItem()
            item.setText(0, stencil["code"])
            item.setText(1, stencil["description"])

            # Status badge
            status_badge = StatusBadge(stencil.get("status", "pending"))
            self.tree_widget.setItemWidget(item, 2, status_badge)

            # Tensão média
            tension_avg = stencil.get("tension_avg")
            if tension_avg is not None:
                item.setText(3, f"{tension_avg:.1f} N/cm²")
            else:
                item.setText(3, "--")

            # Última medição
            last_meas = self._format_datetime(stencil.get("last_measurement"))
            item.setText(4, last_meas)

            # Botão Ver
            btn_view = StandardButton(
                "Ver",
                variant="primary-green",
                semantic_size="inline-compact"
            )
            btn_view.clicked.connect(
                lambda checked, s=stencil: self.on_view_clicked(s)
            )

            # Container para o botão
            btn_container = QWidget()
            btn_layout = QHBoxLayout(btn_container)
            btn_layout.setContentsMargins(2, 2, 2, 2)
            btn_layout.addWidget(btn_view)

            self.tree_widget.setItemWidget(item, 5, btn_container)

            # Dados do stencil
            item.setData(0, Qt.ItemDataRole.UserRole, stencil)
            self.tree_widget.addTopLevelItem(item)

    def on_view_clicked(self, stencil: Dict):
        """Handle para clique no botão Ver."""
        # Seleciona o item na tree
        for i in range(self.tree_widget.topLevelItemCount()):
            item = self.tree_widget.topLevelItem(i)
            if item.data(0, Qt.ItemDataRole.UserRole) == stencil:
                self.tree_widget.setCurrentItem(item)
                break

        # Carrega dados de tensão se disponíveis
        self.view_stencil_details()

    def on_stencil_selected(self, item: QTreeWidgetItem, column: int):
        """Handle quando stencil é selecionado."""
        stencil_data = item.data(0, Qt.ItemDataRole.UserRole)
        self.selected_stencil = stencil_data

        # Atualiza painel de detalhes
        self.show_details(stencil_data)

        # Atualiza painel direito
        self.viz_subtitle.setText(f"{stencil_data['code']} Selecionado")

        # Habilita botões
        self.btn_history.setEnabled(True)
        self.btn_view.setEnabled(True)

        # Emite sinal
        self.program_selected.emit(stencil_data)

    def show_details(self, stencil: Dict):
        """Mostra detalhes do stencil no painel esquerdo."""
        # Remove conteúdo atual
        parent_widget = self.details_label.parent()
        if not parent_widget:
            return
        layout = parent_widget.layout()
        if not layout:
            return
        while layout.count() > 1:  # Mantém o título
            child = layout.takeAt(1)
            if child.widget():
                child.widget().deleteLater()

        # Cria novos detalhes
        details_text = f"""
        <style>
            .label {{ color: {COLORS.TEXT_HINT}; font-weight: bold; }}
            .value {{ color: {COLORS.TEXT_PRIMARY}; }}
        </style>
        <table cellpadding="3" cellspacing="0">
            <tr>
                <td class="label">Código:</td>
                <td class="value">{stencil.get('code', '-')}</td>
            </tr>
            <tr>
                <td class="label">Descrição:</td>
                <td class="value">{stencil.get('description', '-') or '-'}</td>
            </tr>
            <tr>
                <td class="label">Receita:</td>
                <td class="value">{stencil.get('recipe', '-') or '-'}</td>
            </tr>
            <tr>
                <td class="label">Status:</td>
                <td class="value">{self._get_status_label(stencil.get('status', ''))}</td>
            </tr>
        </table>
        """

        details_label = QLabel(details_text)
        details_label.setTextFormat(Qt.TextFormat.RichText)
        details_label.setWordWrap(True)
        details_label.setStyleSheet(f"padding: {SPACE.SM}px;")
        layout.insertWidget(1, details_label)

        self.details_label.setText("")

    def _get_status_label(self, status: str) -> str:
        """Retorna label formatada do status."""
        labels = {
            "active": "Ativo",
            "warning": "Alerta",
            "retired": "Retirado",
            "pending": "Pendente",
        }
        return labels.get(status, status.upper())

    def load_tension_file(self):
        """Carrega arquivo JSON de tensão."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Carregar Dados de Tensão",
            "",
            "Arquivos JSON (*.json);;Todos os arquivos (*)"
        )

        if file_path:
            self.load_file(file_path)

    def load_file(self, file_path: str):
        """Carrega arquivo específico de tensão."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Valida se é arquivo de tensão válido
            if data.get('type') != 'stencil_tension':
                QMessageBox.warning(
                    self, "Arquivo Inválido",
                    "Este não é um arquivo de medição de tensão válido."
                )
                return

            self.measurements_data = data
            self.last_file_path = file_path
            self.btn_reload.setEnabled(True)

            # Atualiza heatmap
            self.heatmap.set_measurements(data)

            # Atualiza critérios se disponíveis
            if 'parameters' in data and 'acceptance' in data['parameters']:
                acc = data['parameters']['acceptance']
                self.spin_min.blockSignals(True)
                self.spin_max.blockSignals(True)
                self.spin_warn_low.blockSignals(True)
                self.spin_warn_high.blockSignals(True)

                self.spin_min.setValue(acc.get('min_tension', 25.0))
                self.spin_max.setValue(acc.get('max_tension', 45.0))
                self.spin_warn_low.setValue(acc.get('warning_low', 28.0))
                self.spin_warn_high.setValue(acc.get('warning_high', 42.0))

                self.spin_min.blockSignals(False)
                self.spin_max.blockSignals(False)
                self.spin_warn_low.blockSignals(False)
                self.spin_warn_high.blockSignals(False)

            # Atualiza visualização
            self.on_criteria_changed()

        except Exception as e:
            QMessageBox.critical(
                self, "Erro",
                f"Erro ao carregar arquivo:\n{str(e)}"
            )

    def reload_tension(self):
        """Recarrega último arquivo de tensão."""
        if self.last_file_path:
            self.load_file(self.last_file_path)

    def on_criteria_changed(self, value=None):
        """Handle quando critérios mudam."""
        self.acceptance_criteria = TensionAcceptance(
            min_tension=self.spin_min.value(),
            max_tension=self.spin_max.value(),
            warning_low=self.spin_warn_low.value(),
            warning_high=self.spin_warn_high.value()
        )

        # Atualiza heatmap
        self.heatmap.set_acceptance_criteria(self.acceptance_criteria)

        # Atualiza estatísticas se houver dados
        if self.measurements_data:
            self.update_statistics()

    def update_statistics(self):
        """Atualiza estatísticas e resultado."""
        if not self.measurements_data:
            # Reset labels
            self.stats_counts_label.setText("🟢 OK: 0 | 🟡 WARN: 0 | 🔴 NOK: 0")
            self.stats_values_label.setText("Mín: -- | Máx: -- | Média: --")
            self.stats_total_label.setText("Total: 0 pontos")
            self.result_badge.setText("---")
            self.file_name_label.setText("Nenhum arquivo carregado")
            self.file_details_label.setText("Grid: -- | Área: --")
            return

        measurements = self.measurements_data.get('measurements', [])
        if not measurements:
            return

        tensions = [float(m.get('tension', 0)) for m in measurements]

        # Calcula estatísticas
        min_tension = min(tensions)
        max_tension = max(tensions)
        avg_tension = sum(tensions) / len(tensions)

        # Classifica medições
        counts = {'OK': 0, 'WARNING': 0, 'NOK': 0}
        if self.acceptance_criteria:
            for t in tensions:
                result = self.acceptance_criteria.classify(t)
                counts[result] = counts.get(result, 0) + 1

        total = len(tensions)
        ok_pct = (counts['OK'] / total * 100) if total > 0 else 0
        warn_pct = (counts['WARNING'] / total * 100) if total > 0 else 0
        nok_pct = (counts['NOK'] / total * 100) if total > 0 else 0

        # Atualiza estatísticas (linha 1: counts)
        self.stats_counts_label.setText(
            f"🟢 OK: {counts['OK']} ({ok_pct:.1f}%) | "
            f"🟡 WARN: {counts['WARNING']} ({warn_pct:.1f}%) | "
            f"🔴 NOK: {counts['NOK']} ({nok_pct:.1f}%)"
        )

        # Atualiza estatísticas (linha 2: valores)
        self.stats_values_label.setText(
            f"Mín: {min_tension:.1f} | Máx: {max_tension:.1f} | Média: {avg_tension:.1f} N/cm²"
        )

        # Atualiza estatísticas (linha 3: total)
        self.stats_total_label.setText(f"Total: {total} pontos medidos")

        # Atualiza resultado (badge)
        if nok_pct > 0:
            self.result_badge.setText("REPROVADO")
            self.result_badge.setStyleSheet(f"""
                QLabel {{
                    font-size: {TYPO.TITLE_SMALL}px;
                    font-weight: bold;
                    padding: {SPACE.SM}px;
                    border-radius: {DIM.RADIUS_MD}px;
                    background-color: {COLORS.ERROR};
                    color: {COLORS.BACKGROUND};
                    min-height: 40px;
                }}
            """)
        elif warn_pct > 20:
            self.result_badge.setText("ATENÇÃO")
            self.result_badge.setStyleSheet(f"""
                QLabel {{
                    font-size: {TYPO.TITLE_SMALL}px;
                    font-weight: bold;
                    padding: {SPACE.SM}px;
                    border-radius: {DIM.RADIUS_MD}px;
                    background-color: {COLORS.WARNING};
                    color: {COLORS.TEXT_PRIMARY};
                    min-height: 40px;
                }}
            """)
        else:
            self.result_badge.setText("APROVADO")
            self.result_badge.setStyleSheet(f"""
                QLabel {{
                    font-size: {TYPO.TITLE_SMALL}px;
                    font-weight: bold;
                    padding: {SPACE.SM}px;
                    border-radius: {DIM.RADIUS_MD}px;
                    background-color: {COLORS.SUCCESS};
                    color: {COLORS.BACKGROUND};
                    min-height: 40px;
                }}
            """)

        # Atualiza legenda
        self._update_legend()

        # Atualiza info do arquivo
        if self.last_file_path:
            import os
            file_name = os.path.basename(self.last_file_path)
            self.file_name_label.setText(file_name)

            # Tenta obter informações do grid
            params = self.measurements_data.get('parameters', {})
            start = params.get('start', {})
            end = params.get('end', {})
            if start and end:
                area_w = end.get('x', 0) - start.get('x', 0)
                area_h = end.get('y', 0) - start.get('y', 0)
                self.file_details_label.setText(f"Grid: 4x4 | Área: {area_w}x{area_h}mm")
            else:
                self.file_details_label.setText("Grid: 4x4")

    def load_criteria_from_recipe(self):
        """Carrega critérios da receita atual."""
        # Tenta obter a receita do pai (AOIControllerApp)
        parent = self.parent()
        while parent and not hasattr(parent, 'current_recipe'):
            parent = parent.parent()

        if parent and hasattr(parent, 'current_recipe') and parent.current_recipe:
            recipe = parent.current_recipe
            acc = recipe.tension.acceptance

            # Bloqueia sinais para evitar múltiplas atualizações
            self.spin_min.blockSignals(True)
            self.spin_max.blockSignals(True)
            self.spin_warn_low.blockSignals(True)
            self.spin_warn_high.blockSignals(True)

            self.spin_min.setValue(acc.min_tension)
            self.spin_max.setValue(acc.max_tension)
            self.spin_warn_low.setValue(acc.warning_low)
            self.spin_warn_high.setValue(acc.warning_high)

            self.spin_min.blockSignals(False)
            self.spin_max.blockSignals(False)
            self.spin_warn_low.blockSignals(False)
            self.spin_warn_high.blockSignals(False)

            # Atualiza manualmente
            self.on_criteria_changed()

            QMessageBox.information(
                self, "Critérios Carregados",
                f"Critérios da receita '{recipe.name}' aplicados:\n\n"
                f"Mínimo: {acc.min_tension} N/cm²\n"
                f"Máximo: {acc.max_tension} N/cm²\n"
                f"Warning ↓: {acc.warning_low} N/cm²\n"
                f"Warning ↑: {acc.warning_high} N/cm²"
            )
        else:
            QMessageBox.warning(
                self, "Receita Não Encontrada",
                "Nenhuma receita está carregada.\n\n"
                "Acesse o menu para carregar uma receita."
            )

    def filter_stencils(self, search_term: str = ""):
        """Filtra stencils por termo de busca."""
        self.apply_filters(search_term=search_term)

    def apply_filters(self, search_term: str = ""):
        """Aplica filtros de período e status."""
        if not search_term:
            search_term = self.search_input.text().strip()

        filtered = list(self.current_stencils)

        # Filtro por busca
        if search_term:
            term = search_term.lower()
            filtered = [
                s for s in filtered
                if term in s["code"].lower()
                or term in s["description"].lower()
            ]

        # Filtro por status
        status_map = {
            "Todos": None,
            "Ativos": "active",
            "Alerta": "warning",
            "Retirados": "retired",
        }
        status_filter = status_map.get(self.status_combo.currentText())
        if status_filter:
            filtered = [s for s in filtered if s.get("status") == status_filter]

        # Filtro por período
        period_text = self.period_combo.currentText()
        if period_text == "Últimas 10":
            filtered = filtered[:10]
        else:
            days_map = {
                "7 dias": 7,
                "30 dias": 30,
                "60 dias": 60,
                "90 dias": 90,
                "180 dias": 180,
                "365 dias": 365,
            }
            days = days_map.get(period_text)
            if days:
                cutoff = datetime.now() - timedelta(days=days)
                filtered = [
                    s for s in filtered
                    if (dt := self._parse_datetime(s.get("last_measurement"))) is not None
                    and dt >= cutoff
                ]

        # Ordenar (NOVO)
        sort_text = self.sort_combo.currentText()
        if sort_text == "Mais recentes":
            filtered.sort(
                key=lambda s: self._parse_datetime(s.get("last_measurement")) or datetime.min,
                reverse=True
            )
        elif sort_text == "Mais antigos":
            filtered.sort(
                key=lambda s: self._parse_datetime(s.get("last_measurement")) or datetime.min,
            )
        elif sort_text == "Código (A-Z)":
            filtered.sort(key=lambda s: s.get("code", ""))
        elif sort_text == "Código (Z-A)":
            filtered.sort(key=lambda s: s.get("code", ""), reverse=True)
        elif sort_text == "Tensão (maior)":
            filtered.sort(key=lambda s: s.get("tension_avg") or 0, reverse=True)
        elif sort_text == "Tensão (menor)":
            filtered.sort(key=lambda s: s.get("tension_avg") or 0)

        self.populate_tree(filtered)

    def show_history(self):
        """Mostra histórico do stencil selecionado."""
        if self.selected_stencil and self.stencil_manager:
            from consumo_lib.dialogs.stencil import StencilFullHistoryDialog

            dialog = StencilFullHistoryDialog(
                self.stencil_manager,
                self.selected_stencil["code"],
                self,
            )
            dialog.exec()
        else:
            logger.warning("Tentativa de abrir histórico sem stencil selecionado")

    def show_full_history(self):
        """Mostra histórico completo em diálogo."""
        self.show_history()

    def view_stencil_details(self):
        """Abre detalhes completos do stencil."""
        if self.selected_stencil:
            # Aqui pode abrir um diálogo com detalhes completos se necessário
            logger.info("Visualizando detalhes de %s", self.selected_stencil["code"])
        else:
            logger.warning("Tentativa de ver detalhes sem stencil selecionado")

    def _parse_datetime(self, value) -> Optional[datetime]:
        """Parse de datetime."""
        if not value or value == "-":
            return None
        try:
            return datetime.fromisoformat(value)
        except (TypeError, ValueError):
            return None

    def _format_datetime(self, value) -> str:
        """Formata datetime para exibição."""
        parsed = self._parse_datetime(value)
        if parsed is None:
            return value or "-"
        return parsed.strftime("%d/%m/%Y %H:%M")
