"""
Diálogo de Seleção de Padrões de Medição de Tensão

Diálogo modal com TreeView para selecionar padrões de medição salvos.

Author: Claude
Created: 2026-03-31
"""

import logging
from typing import Optional, Dict, List

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QTreeWidget, QTreeWidgetItem, QMessageBox,
    QGroupBox, QLineEdit, QComboBox, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal

from consumo_lib.ui import COLORS, TYPO, SPACE, DIM
from consumo_lib.ui.widget_standards import StandardButton
from consumo_lib.managers.measurement_pattern_manager import MeasurementPatternManager

logger = logging.getLogger(__name__)


class SelectPatternDialog(QDialog):
    """
    Diálogo para selecionar padrão de medição salvo.

    Exibe lista de padrões disponíveis em TreeView e permite:
    - Visualizar detalhes do padrão selecionado
    - Filtrar padrões
    - Selecionar padrão para aplicar
    - Excluir padrão (com confirmação)

    Signals:
        pattern_selected: Emitido quando padrão é selecionado (pattern_name)

    Exemplo:
        >>> dialog = SelectPatternDialog(pattern_manager, parent)
        >>> if dialog.exec() == QDialog.DialogCode.Accepted:
        ...     pattern_name = dialog.get_selected_pattern()
    """

    pattern_selected = pyqtSignal(str)  # pattern_name

    def __init__(self, pattern_manager: MeasurementPatternManager, parent=None):
        """
        Inicializa diálogo.

        Args:
            pattern_manager: Gerenciador de padrões
            parent: Widget pai
        """
        super().__init__(parent)
        self.setWindowTitle("Selecionar Padrão de Medição")
        self.setMinimumSize(600, 450)
        self.setModal(True)

        self.pattern_manager = pattern_manager
        self.selected_pattern_name: Optional[str] = None
        self.patterns: List[Dict] = []

        self._build_ui()
        self._load_patterns()

    def _build_ui(self):
        """Constrói interface do usuário."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(SPACE.MD)
        main_layout.setContentsMargins(SPACE.MD, SPACE.MD, SPACE.MD, SPACE.MD)

        # ==================== HEADER ====================
        header_label = QLabel("Selecione um padrão de medição para aplicar")
        header_label.setFont(TYPO.get_font(TYPO.TITLE_SMALL, bold=True))
        main_layout.addWidget(header_label)

        # ==================== FILTROS ====================
        filter_widget = QWidget()
        filter_layout = QHBoxLayout(filter_widget)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(SPACE.SM)

        # Busca
        filter_layout.addWidget(QLabel("Buscar:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar padrão...")
        self.search_input.textChanged.connect(self._filter_patterns)
        filter_layout.addWidget(self.search_input, 1)

        # Ordenar
        filter_layout.addWidget(QLabel("Ordenar:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            "Mais recentes",
            "Mais antigos",
            "Nome (A-Z)",
            "Nome (Z-A)",
            "Grid (maior)",
            "Grid (menor)"
        ])
        self.sort_combo.currentTextChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.sort_combo)

        main_layout.addWidget(filter_widget)

        # ==================== TREEVIEW ====================
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels([
            "Nome", "Grid", "Pontos", "Criado", "Modificado", "Autor"
        ])
        self.tree_widget.setColumnWidth(0, 180)  # Nome
        self.tree_widget.setColumnWidth(1, 50)   # Grid
        self.tree_widget.setColumnWidth(2, 50)   # Pontos
        self.tree_widget.setColumnWidth(3, 100)  # Criado
        self.tree_widget.setColumnWidth(4, 100)  # Modificado
        self.tree_widget.setColumnWidth(5, 80)   # Autor
        self.tree_widget.itemClicked.connect(self._on_pattern_selected)
        self.tree_widget.itemDoubleClicked.connect(self._on_pattern_double_clicked)

        # Estilo
        self.tree_widget.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {COLORS.BACKGROUND};
                border: 1px solid {COLORS.BORDER};
                border-radius: {DIM.RADIUS_SM}px;
                font-size: {TYPO.BODY_SMALL}px;
            }}
            QHeaderView::section {{
                padding: 4px 8px;
                font-size: {TYPO.LABEL_SMALL}px;
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

        main_layout.addWidget(self.tree_widget, 1)

        # ==================== DETALHES ====================
        details_group = QGroupBox("Detalhes do Padrão")
        details_layout = QGridLayout(details_group)
        details_layout.setSpacing(SPACE.SM)

        # Campos de detalhes
        self.details_name = QLabel("-")
        self.details_name.setStyleSheet(f"font-weight: bold; color: {COLORS.TEXT_PRIMARY};")
        details_layout.addWidget(QLabel("Nome:"), 0, 0)
        details_layout.addWidget(self.details_name, 0, 1)

        self.description_label = QLabel("Descrição:")
        self.description_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        details_layout.addWidget(self.description_label, 1, 0)

        self.details_description = QLabel("-")
        self.details_description.setWordWrap(True)
        self.details_description.setStyleSheet(f"color: {COLORS.TEXT_HINT}; font-style: italic;")
        details_layout.addWidget(self.details_description, 1, 1)

        self.details_grid = QLabel("-")
        self.details_grid.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        details_layout.addWidget(QLabel("Grid:"), 2, 0)
        details_layout.addWidget(self.details_grid, 2, 1)

        self.details_area = QLabel("-")
        self.details_area.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        details_layout.addWidget(QLabel("Área:"), 3, 0)
        details_layout.addWidget(self.details_area, 3, 1)

        self.details_heights = QLabel("-")
        self.details_heights.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        details_layout.addWidget(QLabel("Alturas:"), 4, 0)
        details_layout.addWidget(self.details_heights, 4, 1)

        self.details_created = QLabel("-")
        self.details_created.setStyleSheet(f"color: {COLORS.TEXT_HINT};")
        details_layout.addWidget(QLabel("Criado:"), 5, 0)
        details_layout.addWidget(self.details_created, 5, 1)

        # Estilo dos labels
        for i in range(details_layout.count()):
            widget = details_layout.itemAt(i).widget()
            if widget and isinstance(widget, QLabel):
                widget.setStyleSheet(f"font-size: {TYPO.LABEL_SMALL}px;")

        main_layout.addWidget(details_group)

        # ==================== BOTÕES ====================
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        # Excluir
        self.btn_delete = StandardButton(
            "Excluir",
            variant="secondary",
            semantic_size="dialog-secondary"
        )
        self.btn_delete.clicked.connect(self._on_delete)
        self.btn_delete.setEnabled(False)
        btn_layout.addWidget(self.btn_delete)

        # Cancelar
        self.btn_cancel = StandardButton(
            "Cancelar",
            variant="secondary",
            semantic_size="dialog-secondary"
        )
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        # Selecionar
        self.btn_select = StandardButton(
            "Aplicar",
            variant="primary-green",
            semantic_size="dialog-primary"
        )
        self.btn_select.clicked.connect(self._on_select)
        self.btn_select.setEnabled(False)
        btn_layout.addWidget(self.btn_select)

        main_layout.addLayout(btn_layout)

    def _load_patterns(self):
        """Carrega padrões do gerenciador."""
        self.patterns = self.pattern_manager.list_patterns()
        self._populate_tree(self.patterns)

    def _populate_tree(self, patterns: List[Dict]):
        """Preenche tree com padrões."""
        self.tree_widget.clear()

        for pattern in patterns:
            item = QTreeWidgetItem()

            name = pattern.get('name', 'Sem Nome')
            grid_size = pattern.get('grid_size', 0)
            points = grid_size * grid_size if grid_size > 0 else 0
            created = self._format_date(pattern.get('created_at', ''))
            modified = self._format_date(pattern.get('modified_at', ''))
            author = pattern.get('created_by', '-') or '-'

            item.setText(0, name)
            item.setText(1, f"{grid_size}x{grid_size}")
            item.setText(2, str(points))
            item.setText(3, created)
            item.setText(4, modified)
            item.setText(5, author)

            # Armazena dados completos
            item.setData(0, Qt.ItemDataRole.UserRole, pattern)

            self.tree_widget.addTopLevelItem(item)

        # Seleciona primeiro item se existir
        if self.tree_widget.topLevelItemCount() > 0:
            self.tree_widget.setCurrentItem(self.tree_widget.topLevelItem(0))

    def _filter_patterns(self, search_term: str = ""):
        """Filtra padrões por termo de busca."""
        self._apply_filters()

    def _apply_filters(self, sort_by: str = ""):
        """Aplica filtros e ordenação."""
        search_term = self.search_input.text().strip().lower()

        # Filtra por busca
        filtered = list(self.patterns)
        if search_term:
            filtered = [
                p for p in filtered
                if search_term in p.get('name', '').lower()
                or search_term in p.get('description', '').lower()
            ]

        # Ordena
        sort_text = sort_by or self.sort_combo.currentText()
        if sort_text == "Mais recentes":
            filtered.sort(key=lambda x: x.get('modified_at', ''), reverse=True)
        elif sort_text == "Mais antigos":
            filtered.sort(key=lambda x: x.get('modified_at', ''))
        elif sort_text == "Nome (A-Z)":
            filtered.sort(key=lambda x: x.get('name', ''))
        elif sort_text == "Nome (Z-A)":
            filtered.sort(key=lambda x: x.get('name', ''), reverse=True)
        elif sort_text == "Grid (maior)":
            filtered.sort(key=lambda x: x.get('grid_size', 0), reverse=True)
        elif sort_text == "Grid (menor)":
            filtered.sort(key=lambda x: x.get('grid_size', 0))

        self._populate_tree(filtered)

    def _on_pattern_selected(self, item: QTreeWidgetItem, column: int):
        """Handle quando padrão é selecionado."""
        pattern_data = item.data(0, Qt.ItemDataRole.UserRole)
        self.selected_pattern_name = pattern_data.get('name')
        self.btn_select.setEnabled(True)
        self.btn_delete.setEnabled(True)

        # Atualiza detalhes
        self._show_details(pattern_data)

    def _on_pattern_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle para double-click - seleciona e fecha."""
        self._on_pattern_selected(item, column)
        self._on_select()

    def _show_details(self, pattern: Dict):
        """Mostra detalhes do padrão selecionado."""
        name = pattern.get('name', '-')
        description = pattern.get('description', '-') or 'Sem descrição'
        grid_size = pattern.get('grid_size', 0)
        points = grid_size * grid_size if grid_size > 0 else 0
        created = self._format_date(pattern.get('created_at', ''))
        author = pattern.get('created_by', '-') or '-'

        params = pattern.get('parameters', {})
        start = params.get('start', {})
        end = params.get('end', {})
        area_width = end.get('x', 0) - start.get('x', 0)
        area_height = end.get('y', 0) - start.get('y', 0)
        z_height = params.get('measurement_height', 0)
        z_move = params.get('movement_height', 0)
        stab_time = params.get('stabilization_time', 0)

        self.details_name.setText(name)
        self.details_description.setText(description)
        self.details_grid.setText(f"{grid_size}x{grid_size} ({points} pontos)")
        self.details_area.setText(f"{area_width:.1f} x {area_height:.1f} mm")
        self.details_heights.setText(
            f"Medição: {z_height:.2f}mm | Movimento: {z_move:.2f}mm | Estab: {stab_time}ms"
        )
        self.details_created.setText(f"{created} por {author}")

    def _on_select(self):
        """Handle para botão Selecionar."""
        if not self.selected_pattern_name:
            return

        logger.info(f"Padrão selecionado: {self.selected_pattern_name}")
        self.pattern_selected.emit(self.selected_pattern_name)
        self.accept()

    def _on_delete(self):
        """Handle para botão Excluir."""
        if not self.selected_pattern_name:
            return

        reply = QMessageBox.question(
            self,
            "Confirmar Exclusão",
            f"Deseja realmente excluir o padrão '{self.selected_pattern_name}'?\n\n"
            "Esta ação não pode ser desfeita.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            success = self.pattern_manager.delete_pattern(self.selected_pattern_name)
            if success:
                QMessageBox.information(
                    self, "Padrão Excluído",
                    f"Padrão '{self.selected_pattern_name}' excluído com sucesso."
                )
                self._load_patterns()
                self.selected_pattern_name = None
                self.btn_select.setEnabled(False)
                self.btn_delete.setEnabled(False)
            else:
                QMessageBox.critical(
                    self, "Erro",
                    "Erro ao excluir padrão."
                )

    def _format_date(self, date_str: str) -> str:
        """Formata string de data para exibição."""
        if not date_str:
            return "-"
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(date_str)
            return dt.strftime("%d/%m/%Y %H:%M")
        except:
            return date_str

    def get_selected_pattern(self) -> Optional[str]:
        """
        Obtém nome do padrão selecionado.

        Returns:
            Nome do padrão ou None
        """
        return self.selected_pattern_name
