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
    QFileDialog, QMessageBox, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal

from consumo_lib.ui import COLORS, TYPO, SPACE, DIM
from consumo_lib.ui.widget_standards import StandardButton
from consumo_lib.widgets.mini_tension_heatmap import MiniTensionHeatmapWidget

from aoi_lib.recipe_manager import TensionAcceptance

logger = logging.getLogger(__name__)


class TensionMeasurementTab(QWidget):
    """
    Aba unificada de Medição de Tensão.

    Combina lista de stencils e visualização de tensão em layout 70%/30%.
    """

    program_selected = pyqtSignal(dict)
    measure_stencil_requested = pyqtSignal()

    def __init__(self, stencil_manager=None, config_manager=None, parent=None):
        super().__init__(parent)
        self.stencil_manager = stencil_manager
        self.config_manager = config_manager
        self.current_stencils: List[Dict] = []
        self.selected_stencil: Optional[Dict] = None
        self.last_file_path: Optional[str] = None
        self.measurements_data: Optional[Dict] = None
        self.acceptance_criteria: Optional[TensionAcceptance] = None

        # Critérios globais (valores padrão, serão atualizados pelo manager)
        self.criteria_min = 25.0
        self.criteria_max = 45.0
        self.criteria_warn_low = 28.0
        self.criteria_warn_high = 42.0

        self.setup_ui()
        self._load_saved_criteria()
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

        header_actions = QHBoxLayout()
        header_actions.addStretch()

        self.btn_measure_stencil = StandardButton(
            "Medir stencil",
            variant="primary-green",
            semantic_size="inline-primary"
        )
        self.btn_measure_stencil.clicked.connect(self.measure_stencil_requested.emit)
        header_actions.addWidget(self.btn_measure_stencil)

        layout.addLayout(header_actions)

        # Splitter 70%/30%
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # Painel esquerdo (70%)
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)

        # Painel direito (30%)
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)

        splitter.setStretchFactor(0, 7)
        splitter.setStretchFactor(1, 3)
        splitter.setHandleWidth(4)
        splitter.setSizes([760, 340])

        layout.addWidget(splitter, 1)

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
        self.tree_widget.currentItemChanged.connect(self._on_current_item_changed)

        # Compact header and items (conforme proposta SVG)
        self.tree_widget.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {COLORS.BACKGROUND};
                border: 1px solid {COLORS.BORDER};
                border-radius: {DIM.RADIUS_SM}px;
                font-size: 11px;
            }}
            QHeaderView::section {{
                padding: 4px 8px;
                font-size: 11px;
                min-height: 24px;
                background-color: {COLORS.SURFACE_VARIANT};
                border: none;
                border-right: 1px solid {COLORS.BORDER};
                border-bottom: 1px solid {COLORS.BORDER};
                font-weight: bold;
            }}
            QTreeWidget::item {{
                min-height: 20px;
                padding: 4px 2px;
                border-bottom: 1px solid {COLORS.BORDER};
            }}
            QTreeWidget::item:selected {{
                background-color: #05966915;
                border: 1px solid #059669;
                color: {COLORS.TEXT_PRIMARY};
            }}
            QTreeWidget::item:hover:!selected {{
                background-color: {COLORS.SURFACE_VARIANT};
            }}
        """)

        layout.addWidget(self.tree_widget, 1)

        # Painel de detalhes
        details_panel = self.create_details_panel()
        layout.addWidget(details_panel)

        return widget

    def create_filter_bar(self) -> QWidget:
        """Cria barra de filtros compacta."""
        widget = QWidget()
        widget.setMinimumHeight(36)
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)

        # Estilo compacto para campos
        field_style = f"""
            QLineEdit, QComboBox {{
                min-height: 20px;
                max-height: 20px;
                font-size: 9px;
                padding: 1px 4px;
                border-radius: 3px;
            }}
            QLabel {{
                font-size: 9px;
                color: {COLORS.TEXT_SECONDARY};
            }}
        """
        widget.setStyleSheet(field_style)

        # Buscar
        layout.addWidget(QLabel("Buscar:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar programas...")
        self.search_input.setMinimumWidth(140)
        self.search_input.textChanged.connect(self.filter_stencils)
        layout.addWidget(self.search_input, 1)

        # Período
        layout.addWidget(QLabel("Período:"))
        self.period_combo = QComboBox()
        self.period_combo.setMinimumWidth(70)
        self.period_combo.addItems([
            "Últimas 10", "7 dias", "30 dias",
            "60 dias", "90 dias", "180 dias", "365 dias"
        ])
        self.period_combo.currentTextChanged.connect(self.apply_filters)
        layout.addWidget(self.period_combo)

        # Status
        layout.addWidget(QLabel("Status:"))
        self.status_combo = QComboBox()
        self.status_combo.setMinimumWidth(70)
        self.status_combo.addItems(["Todos", "Ativos", "Alerta", "Retirados"])
        self.status_combo.currentTextChanged.connect(self.apply_filters)
        layout.addWidget(self.status_combo)

        # Ordenar
        layout.addWidget(QLabel("Ordenar:"))
        self.sort_combo = QComboBox()
        self.sort_combo.setMinimumWidth(90)
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
        """
        Cria painel de detalhes do stencil selecionado.

        Proposta SVG: Layout horizontal grid 3 colunas, 7 campos + 2 botões (75x30px, 55x30px)
        Altura fixa: 155px
        """
        widget = QWidget()
        widget.setMinimumHeight(155)
        widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        title = QLabel("Detalhes do Stencil Selecionado")
        title.setFont(TYPO.get_font(TYPO.TITLE_SMALL, bold=True))  # 13px bold
        layout.addWidget(title)

        # Grid de detalhes (3 colunas)
        self.details_grid_widget = QWidget()
        self.details_grid = QVBoxLayout(self.details_grid_widget)
        self.details_grid.setContentsMargins(0, 0, 0, 0)
        self.details_grid.setSpacing(8)

        # Placeholder quando nada está selecionado
        self.details_placeholder = QLabel("Selecione um stencil para ver detalhes")
        self.details_placeholder.setStyleSheet(f"color: {COLORS.TEXT_HINT}; font-size: {TYPO.LABEL_SMALL}px;")
        self.details_grid.addWidget(self.details_placeholder)

        # Campos (inicialmente ocultos)
        self.details_fields_widget = QWidget()
        self.details_fields_widget.hide()
        fields_layout = QVBoxLayout(self.details_fields_widget)
        fields_layout.setContentsMargins(0, 0, 0, 0)
        fields_layout.setSpacing(6)

        # Linha 1: Código, Descrição, Status
        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(10)
        self.field_code_label = QLabel("")
        self.field_code_label.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {COLORS.TEXT_PRIMARY};")
        self.field_desc_label = QLabel("")
        self.field_desc_label.setStyleSheet(f"font-size: 12px; color: {COLORS.TEXT_SECONDARY};")
        self.field_status_badge = QLabel("")
        self.field_status_badge.setStyleSheet(f"font-size: 11px; font-weight: bold;")
        row1_layout.addWidget(QLabel("Código:"))
        row1_layout.addWidget(self.field_code_label, 1)
        row1_layout.addWidget(QLabel("Descrição:"))
        row1_layout.addWidget(self.field_desc_label, 2)
        row1_layout.addWidget(QLabel("Status:"))
        row1_layout.addWidget(self.field_status_badge)
        fields_layout.addLayout(row1_layout)

        # Linha 2: Receita, Tensão Média, Total Medições
        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(10)
        self.field_recipe_label = QLabel("")
        self.field_recipe_label.setStyleSheet(f"font-size: 11px; color: {COLORS.TEXT_SECONDARY};")
        self.field_tension_label = QLabel("")
        self.field_tension_label.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {COLORS.SUCCESS};")
        self.field_count_label = QLabel("")
        self.field_count_label.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {COLORS.TEXT_PRIMARY};")
        row2_layout.addWidget(QLabel("Receita:"))
        row2_layout.addWidget(self.field_recipe_label, 1)
        row2_layout.addWidget(QLabel("Tensão Média:"))
        row2_layout.addWidget(self.field_tension_label)
        row2_layout.addWidget(QLabel("Total Medições:"))
        row2_layout.addWidget(self.field_count_label)
        fields_layout.addLayout(row2_layout)

        # Linha 3: Criado em, Última, Observações
        row3_layout = QHBoxLayout()
        row3_layout.setSpacing(10)
        self.field_created_label = QLabel("")
        self.field_created_label.setStyleSheet(f"font-size: 11px; color: {COLORS.TEXT_SECONDARY};")
        self.field_last_label = QLabel("")
        self.field_last_label.setStyleSheet(f"font-size: 11px; color: {COLORS.TEXT_SECONDARY};")
        self.field_notes_label = QLabel("")
        self.field_notes_label.setStyleSheet(f"font-size: 11px; color: {COLORS.TEXT_HINT}; font-style: italic;")
        row3_layout.addWidget(QLabel("Criado em:"))
        row3_layout.addWidget(self.field_created_label)
        row3_layout.addWidget(QLabel("Última:"))
        row3_layout.addWidget(self.field_last_label)
        row3_layout.addWidget(QLabel("Obs:"))
        row3_layout.addWidget(self.field_notes_label, 1)
        fields_layout.addLayout(row3_layout)

        self.details_grid.addWidget(self.details_fields_widget)
        layout.addWidget(self.details_grid_widget)

        # Botões (75x30px e 55x30px)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_history = StandardButton(
            "Histórico",
            variant="secondary",
            semantic_size="grid-action"  # 28x60px
        )
        self.btn_history.setFixedHeight(30)
        self.btn_history.setMinimumWidth(75)
        self.btn_history.setEnabled(False)
        self.btn_history.clicked.connect(self.show_history)
        btn_layout.addWidget(self.btn_history)

        self.btn_view = StandardButton(
            "Ver",
            variant="primary-green",
            semantic_size="grid-action"  # 28x60px
        )
        self.btn_view.setFixedHeight(30)
        self.btn_view.setMinimumWidth(55)
        self.btn_view.setEnabled(False)
        self.btn_view.clicked.connect(self.view_stencil_details)
        btn_layout.addWidget(self.btn_view)

        layout.addLayout(btn_layout)
        return widget

    def create_right_panel(self) -> QWidget:
        """Cria painel direito com visualização de tensão (30% - 340px largura).

        Espaço real disponível: ~677px de altura (1200x740px útil menos menus/status bar)
        """
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # HEADER: Título + Botões (lado a lado) - ~45px
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

        # HEATMAP: 310x220px fixo (ajustado para caber em ~677px)
        self.heatmap = MiniTensionHeatmapWidget()
        self.heatmap.setMinimumSize(260, 190)
        self.heatmap.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.heatmap)

        # RESULTADO: Badge 310x40px
        self.result_badge = QLabel("---")
        self.result_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_badge.setMinimumHeight(40)
        self.result_badge.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
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

        # ESTATÍSTICAS: GroupBox 310x85px - 3 linhas organizadas (reduzido de 90px)
        stats_group = QGroupBox("Estatísticas")
        stats_group.setMinimumWidth(260)
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
        stats_layout.setContentsMargins(10, 18, 10, 8)
        stats_layout.setSpacing(3)

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
        self.legend_widget.setMinimumWidth(260)
        layout.addWidget(self.legend_widget)

        # BOTÃO HISTÓRICO: 310x35px
        self.btn_full_history = StandardButton(
            "Ver Histórico Completo",
            variant="primary-blue",
            semantic_size="inline-primary"
        )
        self.btn_full_history.setMinimumHeight(35)
        self.btn_full_history.setMinimumWidth(260)
        self.btn_full_history.setEnabled(False)
        self.btn_full_history.clicked.connect(self.show_full_history)
        layout.addWidget(self.btn_full_history)

        # INFO ARQUIVO: GroupBox 310x60px
        self.file_info_group = self.create_file_info_group()
        self.file_info_group.setMinimumWidth(260)
        layout.addWidget(self.file_info_group)

        layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setWidget(content)
        return scroll

    def create_legend_widget(self) -> QWidget:
        """
        Cria widget de legenda horizontal (310x50px).

        Proposta SVG:
        - Título 'Legenda' 10px bold
        - 3 items horizontais: OK (28-42), WARNING, NOK
        - Círculos r=6px
        """
        widget = QWidget()
        widget.setMinimumHeight(50)
        widget.setMinimumWidth(260)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)

        widget.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS.BACKGROUND};
                border-radius: 6px;
            }}
        """)

        # Título
        title_label = QLabel("Legenda")
        title_label.setStyleSheet(f"font-size: 10px; font-weight: bold; color: {COLORS.TEXT_PRIMARY};")
        layout.addWidget(title_label)

        # Items horizontais
        items_layout = QHBoxLayout()
        items_layout.setSpacing(10)

        # Item OK - círculo + texto
        ok_indicator = QLabel("●")
        ok_indicator.setStyleSheet(f"color: {COLORS.SUCCESS}; font-size: 12px; font-weight: bold;")
        self.ok_label = self._create_status_badge("Aprovado", "#2E7D32", "#FFFFFF")
        items_layout.addWidget(self.ok_label)

        # Item WARN - círculo + texto
        warn_indicator = QLabel("●")
        warn_indicator.setStyleSheet(f"color: {COLORS.WARNING}; font-size: 12px; font-weight: bold;")
        self.warn_label = self._create_status_badge("Warning", "#F9A825", "#1F2937")
        items_layout.addWidget(self.warn_label)

        # Item NOK - círculo + texto
        nok_indicator = QLabel("●")
        nok_indicator.setStyleSheet(f"color: {COLORS.ERROR}; font-size: 12px; font-weight: bold;")
        self.nok_label = self._create_status_badge("Reprovado", "#C62828", "#FFFFFF")
        items_layout.addWidget(self.nok_label)

        items_layout.addStretch()
        layout.addLayout(items_layout)

        return widget

    def _update_legend(self):
        """Atualiza textos da legenda com valores dos critérios."""
        self.ok_label.setText("Aprovado")
        self.warn_label.setText("Warning")
        self.nok_label.setText("Reprovado")

    def _create_status_badge(self, text: str, background_color: str, text_color: str) -> QLabel:
        """Cria um badge compacto para status."""
        badge = QLabel(text)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(
            self._status_badge_stylesheet(
                background_color=background_color,
                text_color=text_color,
            )
        )
        return badge

    def _status_badge_stylesheet(
        self,
        background_color: str,
        text_color: str,
        min_width: int = 96,
    ) -> str:
        return f"""
            font-size: 11px;
            font-weight: bold;
            color: {text_color};
            background-color: {background_color};
            padding: 4px 10px;
            border-radius: 6px;
            min-width: {min_width}px;
        """

    def _status_display_config(self, status: str) -> tuple[str, str, str]:
        """Mapeia status interno para badge visivel ao operador."""
        status_config = {
            "active": ("Aprovado", "#2E7D32", "#FFFFFF"),
            "warning": ("Warning", "#F9A825", "#1F2937"),
            "retired": ("Reprovado", "#C62828", "#FFFFFF"),
            "pending": ("Pendente", COLORS.SURFACE_VARIANT, COLORS.TEXT_PRIMARY),
        }
        return status_config.get(status, status_config["pending"])

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
        self.file_name_label.setWordWrap(True)
        layout.addWidget(self.file_name_label)

        self.file_details_label = QLabel("Grid: -- | Área: --")
        self.file_details_label.setStyleSheet(f"font-size: {TYPO.LABEL_SMALL}px; color: {COLORS.TEXT_HINT};")
        self.file_details_label.setWordWrap(True)
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
                latest_result = None
                latest_timestamp = stencil.last_inspection or "-"
                try:
                    history = self.stencil_manager.get_tension_history(
                        stencil.code, limit=1
                    )
                    if history and len(history) > 0:
                        latest_record = history[0]
                        tension_avg = latest_record.average_tension
                        latest_result = latest_record.result
                        latest_timestamp = latest_record.timestamp
                except Exception:
                    pass

                self.current_stencils.append({
                    "code": stencil.code,
                    "description": stencil.description or "",
                    "status": stencil.status,
                    "latest_result": latest_result,
                    "last_measurement": latest_timestamp,
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
        selected_code = (self.selected_stencil or {}).get("code")
        item_to_select = None

        for stencil in filtered_stencils:
            item = QTreeWidgetItem()
            item.setText(0, stencil["code"])
            item.setText(1, stencil["description"])
            item.setData(0, Qt.ItemDataRole.UserRole, stencil)
            self.tree_widget.addTopLevelItem(item)

            status_text, status_bg, status_fg = self._approval_display_config(stencil)
            status_label = self._create_status_badge(status_text, status_bg, status_fg)
            self.tree_widget.setItemWidget(item, 2, status_label)

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

            if selected_code and stencil.get("code") == selected_code:
                item_to_select = item

        if item_to_select is not None:
            self.tree_widget.setCurrentItem(item_to_select)
        else:
            self._clear_visualization()

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
        """Mostra detalhes do stencil no painel esquerdo (layout horizontal grid 3 colunas)."""
        # Esconde placeholder e mostra campos
        self.details_placeholder.hide()
        self.details_fields_widget.show()

        # Preenche campos da Linha 1: Código, Descrição, Status
        code = stencil.get('code', '-')
        desc = stencil.get('description', '-') or '-'
        self.field_code_label.setText(code)
        self.field_desc_label.setText(desc)

        # Badge com o resultado da ultima medicao.
        status_text, status_bg, status_fg = self._approval_display_config(stencil)
        self.field_status_badge.setText(status_text)
        self.field_status_badge.setStyleSheet(
            self._status_badge_stylesheet(
                background_color=status_bg,
                text_color=status_fg,
                min_width=110,
            )
        )

        # Preenche campos da Linha 2: Receita, Tensão Média, Total Medições
        recipe = stencil.get('recipe', '-') or '-'
        tension_avg = stencil.get('tension_avg')
        tension_count = stencil.get('measurements_count', stencil.get('measurement_count', 0))

        self.field_recipe_label.setText(recipe)

        if tension_avg is not None:
            self.field_tension_label.setText(f"{tension_avg:.1f} N/cm²")
            # Cor baseada na tensão
            if self._is_tension_ok(tension_avg):
                self.field_tension_label.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {COLORS.SUCCESS};")
            else:
                self.field_tension_label.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {COLORS.ERROR};")
        else:
            self.field_tension_label.setText("--")

        self.field_count_label.setText(str(tension_count))

        # Preenche campos da Linha 3: Criado em, Última, Observações
        created = self._format_datetime(stencil.get('created_at'))
        last_meas = self._format_datetime(stencil.get('last_measurement'))
        notes = stencil.get('notes', '-') or '-'

        self.field_created_label.setText(created)
        self.field_last_label.setText(last_meas)
        self.field_notes_label.setText(notes)

    def _get_status_label(self, status: str) -> str:
        """Retorna label formatada do status."""
        labels = {
            "active": "Aprovado",
            "warning": "Warning",
            "retired": "Reprovado",
            "pending": "Pendente",
        }
        return labels.get(status, status.upper())

    def _approval_display_config(self, stencil: Dict) -> tuple[str, str, str]:
        """Mapeia a ultima medicao do stencil para o badge visivel ao operador."""
        latest_result = (stencil.get("latest_result") or "").upper()
        if latest_result == "OK":
            return "Aprovado", "#2E7D32", "#FFFFFF"
        if latest_result == "WARNING":
            return "Warning", "#F9A825", "#1F2937"
        if latest_result == "NOK":
            return "Reprovado", "#C62828", "#FFFFFF"

        return "Sem medicao", COLORS.SURFACE_VARIANT, COLORS.TEXT_PRIMARY

    def _is_tension_ok(self, tension: float) -> bool:
        """Verifica se tensão está dentro dos critérios OK."""
        if not self.acceptance_criteria:
            self.on_criteria_changed()
        return self.acceptance_criteria.classify(tension) == "OK"

    def _load_saved_criteria(self) -> None:
        """Carrega os criterios persistidos antes de calcular a visualizacao."""
        if self.config_manager is None:
            self.on_criteria_changed()
            return

        try:
            from consumo_lib.managers.tension_criteria_manager import TensionCriteriaManager

            criteria = TensionCriteriaManager(self.config_manager).get_criteria()
            self.update_criteria(criteria)
        except Exception as exc:
            logger.warning("Falha ao carregar criterios de tensao salvos: %s", exc)
            self.on_criteria_changed()

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
            measurement_type = data.get('type')
            if measurement_type not in {'stencil_tension', 'stencil_tension_session'} and 'measurements' not in data:
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

            # Nota: Critérios agora são globais, não carregados do arquivo

            # Atualiza visualização com critérios globais
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
        elif self.selected_stencil:
            self._load_latest_measurement_for_stencil(self.selected_stencil)

    def on_criteria_changed(self):
        """Handle quando critérios mudam."""
        self.acceptance_criteria = TensionAcceptance(
            min_tension=self.criteria_min,
            max_tension=self.criteria_max,
            warning_low=self.criteria_warn_low,
            warning_high=self.criteria_warn_high
        )

        # Atualiza heatmap
        self.heatmap.set_acceptance_criteria(self.acceptance_criteria)

        # Atualiza estatísticas se houver dados
        if self.measurements_data:
            self.update_statistics()

    def update_criteria(self, criteria):
        """
        Atualiza critérios globais recebidos do manager.

        Args:
            criteria: TensionCriteriaConfig com novos valores
        """
        self.criteria_min = criteria.min_tension
        self.criteria_max = criteria.max_tension
        self.criteria_warn_low = criteria.warning_low
        self.criteria_warn_high = criteria.warning_high

        logger.info(f"Critérios atualizados: min={self.criteria_min}, max={self.criteria_max}, "
                    f"warn_low={self.criteria_warn_low}, warn_high={self.criteria_warn_high}")

        # Atualiza legenda
        self._update_legend()

        # Atualiza critérios
        self.on_criteria_changed()

    def update_statistics(self):
        """Atualiza estatísticas e resultado."""
        if not self.measurements_data:
            # Reset labels
            self.stats_counts_label.setText("OK: 0 (0%) | WARN: 0 (0%) | NOK: 0 (0%)")
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
        for measurement, tension in zip(measurements, tensions):
            result = self._measurement_status(measurement, tension)
            counts[result] = counts.get(result, 0) + 1

        total = len(tensions)
        ok_pct = (counts['OK'] / total * 100) if total > 0 else 0
        warn_pct = (counts['WARNING'] / total * 100) if total > 0 else 0
        nok_pct = (counts['NOK'] / total * 100) if total > 0 else 0

        # Atualiza estatísticas (linha 1: counts) - sem emojis
        self.stats_counts_label.setText(
            f"OK: {counts['OK']} ({ok_pct:.1f}%) | "
            f"WARN: {counts['WARNING']} ({warn_pct:.1f}%) | "
            f"NOK: {counts['NOK']} ({nok_pct:.1f}%)"
        )

        # Atualiza estatísticas (linha 2: valores)
        self.stats_values_label.setText(
            f"Mín: {min_tension:.1f} | Máx: {max_tension:.1f} | Média: {avg_tension:.1f} N/cm²"
        )

        # Atualiza estatísticas (linha 3: total) - sem emoji
        self.stats_total_label.setText(f"Total: {total} pontos medidos")

        # Atualiza resultado (badge)
        overall_result = self._overall_result_from_measurements(counts, total)
        if overall_result == "NOK":
            self.result_badge.setText("REPROVADO")
            self.result_badge.setStyleSheet(f"""
                QLabel {{
                    font-size: {TYPO.TITLE_SMALL}px;
                    font-weight: bold;
                    padding: {SPACE.SM}px;
                    border-radius: {DIM.RADIUS_MD}px;
                    background-color: #C62828;
                    color: #FFFFFF;
                    min-height: 40px;
                }}
            """)
        elif overall_result == "WARNING":
            self.result_badge.setText("WARNING")
            self.result_badge.setStyleSheet(f"""
                QLabel {{
                    font-size: {TYPO.TITLE_SMALL}px;
                    font-weight: bold;
                    padding: {SPACE.SM}px;
                    border-radius: {DIM.RADIUS_MD}px;
                    background-color: #F9A825;
                    color: #1F2937;
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
                    background-color: #2E7D32;
                    color: #FFFFFF;
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
            grid_size = params.get('grid_size', '--')

            if isinstance(start, (list, tuple)) and len(start) >= 2:
                start = {'x': start[0], 'y': start[1]}
            if isinstance(end, (list, tuple)) and len(end) >= 2:
                end = {'x': end[0], 'y': end[1]}
            if start and end:
                area_w = float(end.get('x', 0)) - float(start.get('x', 0))
                area_h = float(end.get('y', 0)) - float(start.get('y', 0))
                self.file_details_label.setText(
                    f"Grid: {grid_size}x{grid_size} | Área: {area_w:.1f}x{area_h:.1f}mm"
                )
            else:
                self.file_details_label.setText(f"Grid: {grid_size}x{grid_size}")

    def _measurement_status(self, measurement: Dict, tension: float) -> str:
        """Retorna o status do ponto, preservando o valor salvo quando existir."""
        saved_status = str(measurement.get("status") or "").upper()
        if saved_status in {"OK", "WARNING", "NOK"}:
            return saved_status

        if not self.acceptance_criteria:
            self.on_criteria_changed()
        return self.acceptance_criteria.classify(tension)

    def _overall_result_from_measurements(self, counts: Dict[str, int], total: int) -> str:
        """Calcula o resultado agregado com a mesma regra do historico."""
        saved_result = str((self.measurements_data or {}).get("result") or "").upper()
        if saved_result in {"OK", "WARNING", "NOK"}:
            return saved_result

        if counts.get("NOK", 0) > 0:
            return "NOK"
        if total and counts.get("WARNING", 0) > total * 0.2:
            return "WARNING"
        return "OK"

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

    def _on_current_item_changed(self, current: QTreeWidgetItem, previous: QTreeWidgetItem):
        """Atualiza a visualizacao quando a selecao atual muda."""
        del previous
        self._apply_selected_stencil(current)

    def _apply_selected_stencil(self, item: Optional[QTreeWidgetItem]):
        """Aplica o stencil selecionado aos paineis da aba."""
        if item is None:
            self.selected_stencil = None
            self.btn_history.setEnabled(False)
            self.btn_view.setEnabled(False)
            self.btn_full_history.setEnabled(False)
            self._clear_visualization()
            return

        stencil_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not stencil_data:
            self.selected_stencil = None
            self.btn_history.setEnabled(False)
            self.btn_view.setEnabled(False)
            self.btn_full_history.setEnabled(False)
            self._clear_visualization()
            return

        self.selected_stencil = stencil_data
        self.show_details(stencil_data)
        self.btn_history.setEnabled(True)
        self.btn_view.setEnabled(True)
        self.btn_full_history.setEnabled(True)
        self._load_latest_measurement_for_stencil(stencil_data)
        self.program_selected.emit(stencil_data)

    def _load_latest_measurement_for_stencil(self, stencil: Optional[Dict]):
        """Carrega a ultima medicao registrada do stencil selecionado."""
        if not stencil or self.stencil_manager is None:
            self._clear_visualization()
            return

        stencil_code = stencil.get("code")
        if not stencil_code:
            self._clear_visualization()
            return

        try:
            history = self.stencil_manager.get_tension_history(stencil_code) or []
        except Exception as exc:
            logger.error("Erro ao carregar historico de tensao de %s: %s", stencil_code, exc)
            self._clear_visualization(
                subtitle=f"{stencil_code} sem visualizacao",
                file_name="Erro ao carregar historico",
            )
            return

        if not history:
            self._clear_visualization(
                subtitle=f"{stencil_code} sem medicao",
                file_name="Nenhuma medicao registrada",
            )
            return

        latest_record = history[0]
        stencil["latest_result"] = latest_record.result
        stencil["last_measurement"] = latest_record.timestamp
        stencil["tension_avg"] = latest_record.average_tension
        self.show_details(stencil)

        self.measurements_data = self._build_visualization_payload(latest_record.to_dict())
        self.last_file_path = None
        self.btn_reload.setEnabled(True)

        self.heatmap.set_measurements(self.measurements_data)
        self.on_criteria_changed()

        self.viz_subtitle.setText(f"{stencil_code} | ultima medicao")
        self.file_name_label.setText(
            f"Ultima medicao: {self._format_datetime(latest_record.timestamp)}"
        )

        measurements = self.measurements_data.get("measurements", [])
        if measurements:
            xs = [float(m.get("x", 0)) for m in measurements]
            ys = [float(m.get("y", 0)) for m in measurements]
            self.file_details_label.setText(
                f"Pontos: {len(measurements)} | Area: {max(xs) - min(xs):.1f}x{max(ys) - min(ys):.1f}mm"
            )
        else:
            self.file_details_label.setText("Pontos: 0 | Area: --")

    def _build_visualization_payload(self, data: Dict) -> Dict:
        """Garante parametros suficientes para desenhar o heatmap do historico."""
        payload = dict(data)
        measurements = list(payload.get("measurements", []) or [])
        parameters = dict(payload.get("parameters", {}) or {})

        if not measurements:
            payload["parameters"] = parameters
            return payload

        start = parameters.get("start")
        end = parameters.get("end")
        if not isinstance(start, dict):
            start = None
        if not isinstance(end, dict):
            end = None

        if start is None or end is None:
            xs = [float(m.get("x", 0.0)) for m in measurements]
            ys = [float(m.get("y", 0.0)) for m in measurements]
            start = {"x": min(xs), "y": min(ys)}
            end = {"x": max(xs), "y": max(ys)}

        if not parameters.get("grid_size"):
            rows = set()
            cols = set()
            for measurement in measurements:
                grid_position = measurement.get("grid_position", {}) or {}
                row = grid_position.get("row")
                col = grid_position.get("col")
                if row is not None:
                    rows.add(int(row))
                if col is not None:
                    cols.add(int(col))

            inferred_grid = max(len(rows), len(cols))
            if inferred_grid <= 1:
                inferred_grid = max(2, round(len(measurements) ** 0.5))
            parameters["grid_size"] = inferred_grid

        parameters["start"] = start
        parameters["end"] = end
        payload["parameters"] = parameters
        return payload

    def _clear_visualization(
        self,
        subtitle: str = "Selecione um stencil",
        file_name: str = "Nenhuma medicao carregada",
    ):
        """Limpa a visualizacao quando nao ha dados para exibir."""
        self.measurements_data = None
        self.last_file_path = None
        self.viz_subtitle.setText(subtitle)
        self.btn_reload.setEnabled(False)
        self.heatmap.set_measurements({"measurements": [], "parameters": {}})
        self.on_criteria_changed()
        self.file_name_label.setText(file_name)
        self.file_details_label.setText("Grid: -- | Area: --")

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

    def _format_date(self, value) -> str:
        """Formata datetime para exibição (apenas data)."""
        parsed = self._parse_datetime(value)
        if parsed is None:
            return value or "-"
        return parsed.strftime("%d/%m/%Y")
