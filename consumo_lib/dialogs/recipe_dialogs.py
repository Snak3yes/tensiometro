# -*- coding: utf-8 -*-
"""
recipe_dialog.py
----------------
Diálogos PyQt6 para gerenciamento de receitas de stencil.

Inclui:
- RecipeManagerDialog: Lista e gerencia receitas
- RecipeEditorDialog: Cria/edita uma receita

Autor: Sistema AOI Tensiometro
Data: 2024-12-10
"""

import logging
from typing import Optional
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QTextEdit, QPushButton, QComboBox,
    QSpinBox, QDoubleSpinBox, QCheckBox, QGroupBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QTabWidget, QMessageBox, QFileDialog, QDialogButtonBox,
    QSplitter, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from aoi_lib.recipe_manager import (
    Recipe, RecipeManager, StencilInfo, TensionConfig, 
    TensionAcceptance, CaptureConfig, InspectionConfig,
    Point2D, create_sample_recipe, MACHINE_LIMITS
)

logger = logging.getLogger(__name__)


class RecipeListWidget(QWidget):
    """Widget para listar e selecionar receitas."""
    
    recipe_selected = pyqtSignal(str)  # Emite recipe_id
    recipe_double_clicked = pyqtSignal(str)  # Emite recipe_id
    
    def __init__(self, recipe_manager: RecipeManager, parent=None):
        super().__init__(parent)
        self.manager = recipe_manager
        self.setup_ui()
        self.refresh_list()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Tabela de receitas
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Nome", "ID", "Modificado"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.table.itemDoubleClicked.connect(self._on_double_click)
        
        layout.addWidget(self.table)
    
    def refresh_list(self):
        """Atualiza a lista de receitas."""
        self.table.setRowCount(0)
        recipes = self.manager.list_recipes()
        
        for i, r in enumerate(recipes):
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(r['name']))
            self.table.setItem(i, 1, QTableWidgetItem(r['recipe_id']))
            
            # Formata data
            modified = r.get('modified_at', '')
            if modified:
                try:
                    modified = modified[:10]  # Apenas data
                except:
                    pass
            self.table.setItem(i, 2, QTableWidgetItem(modified))
    
    def _on_selection_changed(self):
        items = self.table.selectedItems()
        if items:
            row = items[0].row()
            recipe_id = self.table.item(row, 1).text()
            self.recipe_selected.emit(recipe_id)
    
    def _on_double_click(self, item):
        row = item.row()
        recipe_id = self.table.item(row, 1).text()
        self.recipe_double_clicked.emit(recipe_id)
    
    def get_selected_recipe_id(self) -> Optional[str]:
        """Retorna o ID da receita selecionada."""
        items = self.table.selectedItems()
        if items:
            row = items[0].row()
            return self.table.item(row, 1).text()
        return None


class RecipeEditorDialog(QDialog):
    """
    Diálogo para criar ou editar uma receita.
    """
    
    def __init__(self, recipe: Recipe = None, parent=None):
        super().__init__(parent)
        self.recipe = recipe or Recipe(name="Nova Receita")
        self.is_new = recipe is None
        
        self.setWindowTitle("Nova Receita" if self.is_new else f"Editar: {self.recipe.name}")
        self.setMinimumSize(700, 600)
        
        self.setup_ui()
        self.load_recipe_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Tabs para organizar seções
        self.tabs = QTabWidget()
        
        # Tab 1: Informações Básicas
        self.tabs.addTab(self._create_info_tab(), "📋 Informações")
        
        # Tab 2: Stencil
        self.tabs.addTab(self._create_stencil_tab(), "📐 Stencil")
        
        # Tab 3: Tensão
        self.tabs.addTab(self._create_tension_tab(), "🎯 Tensão")
        
        # Tab 4: Captura
        self.tabs.addTab(self._create_capture_tab(), "📷 Captura")
        
        # Tab 5: Inspeção (placeholder)
        self.tabs.addTab(self._create_inspection_tab(), "🔍 Inspeção")
        
        layout.addWidget(self.tabs)
        
        # Botões
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
    
    def _create_info_tab(self) -> QWidget:
        """Cria tab de informações básicas."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Grupo de identificação
        group = QGroupBox("Identificação da Receita")
        grid = QGridLayout(group)
        
        grid.addWidget(QLabel("Nome:"), 0, 0)
        self.edit_name = QLineEdit()
        self.edit_name.setPlaceholderText("Ex: Stencil PCB Principal")
        grid.addWidget(self.edit_name, 0, 1)
        
        grid.addWidget(QLabel("ID:"), 1, 0)
        self.edit_id = QLineEdit()
        self.edit_id.setPlaceholderText("Gerado automaticamente")
        self.edit_id.setEnabled(False)  # ID é somente leitura
        grid.addWidget(self.edit_id, 1, 1)
        
        grid.addWidget(QLabel("Criado por:"), 2, 0)
        self.edit_author = QLineEdit()
        self.edit_author.setPlaceholderText("Nome do operador")
        grid.addWidget(self.edit_author, 2, 1)
        
        grid.addWidget(QLabel("Notas:"), 3, 0, Qt.AlignmentFlag.AlignTop)
        self.edit_notes = QTextEdit()
        self.edit_notes.setPlaceholderText("Observações sobre esta receita...")
        self.edit_notes.setMaximumHeight(100)
        grid.addWidget(self.edit_notes, 3, 1)
        
        layout.addWidget(group)
        layout.addStretch()
        
        return widget
    
    def _create_stencil_tab(self) -> QWidget:
        """Cria tab de informações do stencil."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Dimensões
        dim_group = QGroupBox("Dimensões do Stencil")
        dim_grid = QGridLayout(dim_group)

        # Largura
        dim_grid.addWidget(QLabel("Largura (mm):"), 0, 0)
        self.spin_width = QDoubleSpinBox()
        self.spin_width.setRange(1, MACHINE_LIMITS["max_width_mm"])
        self.spin_width.setValue(400)
        dim_grid.addWidget(self.spin_width, 0, 1)

        # Altura
        dim_grid.addWidget(QLabel("Altura (mm):"), 0, 2)
        self.spin_height = QDoubleSpinBox()
        self.spin_height.setRange(1, MACHINE_LIMITS["max_height_mm"])
        self.spin_height.setValue(300)
        dim_grid.addWidget(self.spin_height, 0, 3)

        # Espessura
        dim_grid.addWidget(QLabel("Espessura (mm):"), 1, 0)
        self.spin_thickness = QDoubleSpinBox()
        self.spin_thickness.setRange(0.01, 1.0)
        self.spin_thickness.setValue(0.12)
        self.spin_thickness.setDecimals(3)
        self.spin_thickness.setSingleStep(0.01)
        dim_grid.addWidget(self.spin_thickness, 1, 1)

        layout.addWidget(dim_group)
        
        # Material
        mat_group = QGroupBox("Material")
        mat_layout = QHBoxLayout(mat_group)
        
        mat_layout.addWidget(QLabel("Material:"))
        self.combo_material = QComboBox()
        self.combo_material.addItems([
            "Inox 304", "Inox 316", "Níquel", "Latão", "Outro"
        ])
        self.combo_material.setEditable(True)
        mat_layout.addWidget(self.combo_material)
        mat_layout.addStretch()
        
        layout.addWidget(mat_group)
        layout.addStretch()
        
        return widget
    
    def _create_tension_tab(self) -> QWidget:
        """Cria tab de configuração de tensão."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Enable
        self.chk_tension_enabled = QCheckBox("Habilitar medição de tensão")
        self.chk_tension_enabled.setChecked(True)
        layout.addWidget(self.chk_tension_enabled)
        
        # Grid
        grid_group = QGroupBox("Grid de Medição")
        grid_layout = QGridLayout(grid_group)
        
        grid_layout.addWidget(QLabel("Linhas:"), 0, 0)
        self.spin_grid_rows = QSpinBox()
        self.spin_grid_rows.setRange(1, 20)
        self.spin_grid_rows.setValue(5)
        grid_layout.addWidget(self.spin_grid_rows, 0, 1)
        
        grid_layout.addWidget(QLabel("Colunas:"), 0, 2)
        self.spin_grid_cols = QSpinBox()
        self.spin_grid_cols.setRange(1, 20)
        self.spin_grid_cols.setValue(5)
        grid_layout.addWidget(self.spin_grid_cols, 0, 3)
        
        grid_layout.addWidget(QLabel("Ponto Inicial X:"), 1, 0)
        self.spin_tension_start_x = QDoubleSpinBox()
        self.spin_tension_start_x.setRange(0, MACHINE_LIMITS["max_width_mm"])
        self.spin_tension_start_x.setValue(50)
        grid_layout.addWidget(self.spin_tension_start_x, 1, 1)
        
        grid_layout.addWidget(QLabel("Y:"), 1, 2)
        self.spin_tension_start_y = QDoubleSpinBox()
        self.spin_tension_start_y.setRange(0, MACHINE_LIMITS["max_height_mm"])
        self.spin_tension_start_y.setValue(50)
        grid_layout.addWidget(self.spin_tension_start_y, 1, 3)
        
        grid_layout.addWidget(QLabel("Ponto Final X:"), 2, 0)
        self.spin_tension_end_x = QDoubleSpinBox()
        self.spin_tension_end_x.setRange(0, MACHINE_LIMITS["max_width_mm"])
        self.spin_tension_end_x.setValue(350)
        grid_layout.addWidget(self.spin_tension_end_x, 2, 1)
        
        grid_layout.addWidget(QLabel("Y:"), 2, 2)
        self.spin_tension_end_y = QDoubleSpinBox()
        self.spin_tension_end_y.setRange(0, MACHINE_LIMITS["max_height_mm"])
        self.spin_tension_end_y.setValue(250)
        grid_layout.addWidget(self.spin_tension_end_y, 2, 3)
        
        layout.addWidget(grid_group)
        
        # Critérios de aceitação
        acc_group = QGroupBox("Critérios de Aceitação (N/cm²)")
        acc_layout = QGridLayout(acc_group)
        
        acc_layout.addWidget(QLabel("Tensão Mínima:"), 0, 0)
        self.spin_tension_min = QDoubleSpinBox()
        self.spin_tension_min.setRange(0, MACHINE_LIMITS["max_tension"])
        self.spin_tension_min.setValue(25)
        acc_layout.addWidget(self.spin_tension_min, 0, 1)
        
        acc_layout.addWidget(QLabel("Tensão Máxima:"), 0, 2)
        self.spin_tension_max = QDoubleSpinBox()
        self.spin_tension_max.setRange(0, MACHINE_LIMITS["max_tension"])
        self.spin_tension_max.setValue(45)
        acc_layout.addWidget(self.spin_tension_max, 0, 3)
        
        acc_layout.addWidget(QLabel("Warning Baixo:"), 1, 0)
        self.spin_warning_low = QDoubleSpinBox()
        self.spin_warning_low.setRange(0, MACHINE_LIMITS["max_tension"])
        self.spin_warning_low.setValue(28)
        acc_layout.addWidget(self.spin_warning_low, 1, 1)
        
        acc_layout.addWidget(QLabel("Warning Alto:"), 1, 2)
        self.spin_warning_high = QDoubleSpinBox()
        self.spin_warning_high.setRange(0, MACHINE_LIMITS["max_tension"])
        self.spin_warning_high.setValue(42)
        acc_layout.addWidget(self.spin_warning_high, 1, 3)
        
        # Legenda
        legend = QLabel(
            "💚 OK: Entre Warning Baixo e Warning Alto\n"
            "⚠️ WARNING: Fora do range de warning mas dentro do aceitável\n"
            "❌ NOK: Fora do range mín/máx"
        )
        legend.setStyleSheet("color: #666; font-size: 10px;")
        acc_layout.addWidget(legend, 2, 0, 1, 4)
        
        layout.addWidget(acc_group)
        layout.addStretch()
        
        return widget
    
    def _create_capture_tab(self) -> QWidget:
        """Cria tab de configuração de captura."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Área de captura
        area_group = QGroupBox("Área de Captura")
        area_layout = QGridLayout(area_group)
        
        area_layout.addWidget(QLabel("Origem X:"), 0, 0)
        self.spin_capture_origin_x = QDoubleSpinBox()
        self.spin_capture_origin_x.setRange(0, MACHINE_LIMITS["max_width_mm"])
        self.spin_capture_origin_x.setValue(0)
        area_layout.addWidget(self.spin_capture_origin_x, 0, 1)
        
        area_layout.addWidget(QLabel("Y:"), 0, 2)
        self.spin_capture_origin_y = QDoubleSpinBox()
        self.spin_capture_origin_y.setRange(0, MACHINE_LIMITS["max_height_mm"])
        self.spin_capture_origin_y.setValue(0)
        area_layout.addWidget(self.spin_capture_origin_y, 0, 3)
        
        area_layout.addWidget(QLabel("Final X:"), 1, 0)
        self.spin_capture_end_x = QDoubleSpinBox()
        self.spin_capture_end_x.setRange(0, MACHINE_LIMITS["max_width_mm"])
        self.spin_capture_end_x.setValue(300)
        area_layout.addWidget(self.spin_capture_end_x, 1, 1)
        
        area_layout.addWidget(QLabel("Y:"), 1, 2)
        self.spin_capture_end_y = QDoubleSpinBox()
        self.spin_capture_end_y.setRange(0, MACHINE_LIMITS["max_height_mm"])
        self.spin_capture_end_y.setValue(200)
        area_layout.addWidget(self.spin_capture_end_y, 1, 3)
        
        layout.addWidget(area_group)
        
        # Parâmetros de captura
        params_group = QGroupBox("Parâmetros de Captura")
        params_layout = QGridLayout(params_group)
        
        params_layout.addWidget(QLabel("Step X (mm):"), 0, 0)
        self.spin_step_x = QDoubleSpinBox()
        self.spin_step_x.setRange(1, 500)
        self.spin_step_x.setValue(50)
        params_layout.addWidget(self.spin_step_x, 0, 1)
        
        params_layout.addWidget(QLabel("Step Y (mm):"), 0, 2)
        self.spin_step_y = QDoubleSpinBox()
        self.spin_step_y.setRange(1, 500)
        self.spin_step_y.setValue(50)
        params_layout.addWidget(self.spin_step_y, 0, 3)
        
        params_layout.addWidget(QLabel("Velocidade (mm/min):"), 1, 0)
        self.spin_feed_rate = QDoubleSpinBox()
        self.spin_feed_rate.setRange(100, 10000)
        self.spin_feed_rate.setValue(2000)
        params_layout.addWidget(self.spin_feed_rate, 1, 1)
        
        params_layout.addWidget(QLabel("Delay (ms):"), 1, 2)
        self.spin_delay = QSpinBox()
        self.spin_delay.setRange(50, 2000)
        self.spin_delay.setValue(200)
        params_layout.addWidget(self.spin_delay, 1, 3)
        
        self.chk_backlight = QCheckBox("Usar backlight durante captura")
        self.chk_backlight.setChecked(True)
        params_layout.addWidget(self.chk_backlight, 2, 0, 1, 4)
        
        layout.addWidget(params_group)
        layout.addStretch()
        
        return widget
    
    def _create_inspection_tab(self) -> QWidget:
        """Cria tab de configuração de inspeção (placeholder)."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Placeholder para integração futura
        info_label = QLabel(
            "🔍 Inspeção Visual de Aberturas\n\n"
            "Esta funcionalidade requer integração com arquivo Gerber.\n\n"
            "📌 Próximos passos:\n"
            "• Importar arquivo Gerber do stencil\n"
            "• Gerar máscaras de inspeção\n"
            "• Configurar threshold e critérios\n"
        )
        info_label.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 20px;
                color: #666;
            }
        """)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Parâmetros básicos (para uso futuro)
        params_group = QGroupBox("Parâmetros Padrão (para uso futuro)")
        params_layout = QGridLayout(params_group)
        
        params_layout.addWidget(QLabel("Threshold:"), 0, 0)
        self.spin_threshold = QSpinBox()
        self.spin_threshold.setRange(0, 255)
        self.spin_threshold.setValue(128)
        params_layout.addWidget(self.spin_threshold, 0, 1)
        
        params_layout.addWidget(QLabel("% Mínimo:"), 0, 2)
        self.spin_min_percent = QDoubleSpinBox()
        self.spin_min_percent.setRange(0, 100)
        self.spin_min_percent.setValue(95)
        params_layout.addWidget(self.spin_min_percent, 0, 3)
        
        params_layout.addWidget(QLabel("Cor alvo:"), 1, 0)
        self.combo_target_color = QComboBox()
        self.combo_target_color.addItems(["Branco", "Preto"])
        params_layout.addWidget(self.combo_target_color, 1, 1)
        
        layout.addWidget(params_group)
        layout.addStretch()
        
        return widget
    
    def load_recipe_data(self):
        """Carrega dados da receita nos widgets."""
        r = self.recipe
        
        # Info
        self.edit_name.setText(r.name)
        self.edit_id.setText(r.recipe_id)
        self.edit_author.setText(r.created_by)
        self.edit_notes.setPlainText(r.stencil.notes)
        
        # Stencil
        self.spin_width.setValue(r.stencil.width_mm)
        self.spin_height.setValue(r.stencil.height_mm)
        self.spin_thickness.setValue(r.stencil.thickness_mm)
        self.combo_material.setCurrentText(r.stencil.material)
        
        # Tensão
        self.chk_tension_enabled.setChecked(r.tension.enabled)
        self.spin_grid_rows.setValue(r.tension.grid_rows)
        self.spin_grid_cols.setValue(r.tension.grid_cols)
        self.spin_tension_start_x.setValue(r.tension.start_point.x)
        self.spin_tension_start_y.setValue(r.tension.start_point.y)
        self.spin_tension_end_x.setValue(r.tension.end_point.x)
        self.spin_tension_end_y.setValue(r.tension.end_point.y)
        self.spin_tension_min.setValue(r.tension.acceptance.min_tension)
        self.spin_tension_max.setValue(r.tension.acceptance.max_tension)
        self.spin_warning_low.setValue(r.tension.acceptance.warning_low)
        self.spin_warning_high.setValue(r.tension.acceptance.warning_high)
        
        # Captura
        self.spin_capture_origin_x.setValue(r.capture.origin.x)
        self.spin_capture_origin_y.setValue(r.capture.origin.y)
        self.spin_capture_end_x.setValue(r.capture.end.x)
        self.spin_capture_end_y.setValue(r.capture.end.y)
        self.spin_step_x.setValue(r.capture.step_x)
        self.spin_step_y.setValue(r.capture.step_y)
        self.spin_feed_rate.setValue(r.capture.feed_rate)
        self.spin_delay.setValue(r.capture.capture_delay_ms)
        self.chk_backlight.setChecked(r.capture.backlight_enabled)
        
        # Inspeção
        self.spin_threshold.setValue(r.inspection.default_threshold)
        self.spin_min_percent.setValue(r.inspection.default_min_percent)
        self.combo_target_color.setCurrentIndex(
            0 if r.inspection.target_color == "white" else 1
        )
    
    def save_recipe_data(self) -> Recipe:
        """Salva dados dos widgets na receita."""
        r = self.recipe
        
        # Info
        r.name = self.edit_name.text().strip()
        r.created_by = self.edit_author.text().strip()
        
        # Stencil
        r.stencil.width_mm = self.spin_width.value()
        r.stencil.height_mm = self.spin_height.value()
        r.stencil.thickness_mm = self.spin_thickness.value()
        r.stencil.material = self.combo_material.currentText()
        r.stencil.notes = self.edit_notes.toPlainText()
        
        # Tensão
        r.tension.enabled = self.chk_tension_enabled.isChecked()
        r.tension.grid_rows = self.spin_grid_rows.value()
        r.tension.grid_cols = self.spin_grid_cols.value()
        r.tension.start_point = Point2D(
            self.spin_tension_start_x.value(),
            self.spin_tension_start_y.value()
        )
        r.tension.end_point = Point2D(
            self.spin_tension_end_x.value(),
            self.spin_tension_end_y.value()
        )
        r.tension.acceptance = TensionAcceptance(
            min_tension=self.spin_tension_min.value(),
            max_tension=self.spin_tension_max.value(),
            warning_low=self.spin_warning_low.value(),
            warning_high=self.spin_warning_high.value()
        )
        
        # Captura
        r.capture.origin = Point2D(
            self.spin_capture_origin_x.value(),
            self.spin_capture_origin_y.value()
        )
        r.capture.end = Point2D(
            self.spin_capture_end_x.value(),
            self.spin_capture_end_y.value()
        )
        r.capture.step_x = self.spin_step_x.value()
        r.capture.step_y = self.spin_step_y.value()
        r.capture.feed_rate = self.spin_feed_rate.value()
        r.capture.capture_delay_ms = self.spin_delay.value()
        r.capture.backlight_enabled = self.chk_backlight.isChecked()
        
        # Inspeção
        r.inspection.default_threshold = self.spin_threshold.value()
        r.inspection.default_min_percent = self.spin_min_percent.value()
        r.inspection.target_color = (
            "white" if self.combo_target_color.currentIndex() == 0 else "black"
        )
        
        return r
    
    def accept(self):
        """Valida e aceita o diálogo."""
        recipe = self.save_recipe_data()
        errors = recipe.validate()
        
        if errors:
            QMessageBox.warning(
                self, "Validação",
                "Erros encontrados:\n\n• " + "\n• ".join(errors)
            )
            return
        
        self.recipe = recipe
        super().accept()


class RecipeManagerDialog(QDialog):
    """
    Diálogo principal para gerenciar receitas.
    """
    
    recipe_loaded = pyqtSignal(object)  # Emite Recipe quando carregada
    
    def __init__(self, recipe_manager: RecipeManager, parent=None):
        super().__init__(parent)
        self.manager = recipe_manager
        
        self.setWindowTitle("Gerenciador de Receitas")
        self.setMinimumSize(800, 500)
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Splitter: lista à esquerda, preview à direita
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Painel esquerdo: lista de receitas
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Título
        title = QLabel("📋 Receitas Disponíveis")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title.setFont(title_font)
        left_layout.addWidget(title)
        
        # Lista de receitas
        self.recipe_list = RecipeListWidget(self.manager, self)
        self.recipe_list.recipe_selected.connect(self._on_recipe_selected)
        self.recipe_list.recipe_double_clicked.connect(self._on_edit_recipe)
        left_layout.addWidget(self.recipe_list)
        
        # Botões de ação
        btn_layout = QHBoxLayout()
        
        self.btn_new = QPushButton("➕ Nova")
        self.btn_new.clicked.connect(self._on_new_recipe)
        btn_layout.addWidget(self.btn_new)
        
        self.btn_edit = QPushButton("✏️ Editar")
        self.btn_edit.clicked.connect(self._on_edit_recipe)
        self.btn_edit.setEnabled(False)
        btn_layout.addWidget(self.btn_edit)
        
        self.btn_delete = QPushButton("🗑️ Excluir")
        self.btn_delete.clicked.connect(self._on_delete_recipe)
        self.btn_delete.setEnabled(False)
        btn_layout.addWidget(self.btn_delete)
        
        self.btn_duplicate = QPushButton("📄 Duplicar")
        self.btn_duplicate.clicked.connect(self._on_duplicate_recipe)
        self.btn_duplicate.setEnabled(False)
        btn_layout.addWidget(self.btn_duplicate)
        
        left_layout.addLayout(btn_layout)
        
        splitter.addWidget(left_panel)
        
        # Painel direito: preview
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 0, 0, 0)
        
        preview_title = QLabel("📄 Detalhes da Receita")
        preview_title.setFont(title_font)
        right_layout.addWidget(preview_title)
        
        self.preview_label = QLabel("Selecione uma receita para ver os detalhes.")
        self.preview_label.setWordWrap(True)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #f9f9f9;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 15px;
            }
        """)
        right_layout.addWidget(self.preview_label, 1)
        
        # Botão de carregar
        self.btn_load = QPushButton("🚀 Carregar Receita")
        self.btn_load.setMinimumHeight(40)
        self.btn_load.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        self.btn_load.clicked.connect(self._on_load_recipe)
        self.btn_load.setEnabled(False)
        right_layout.addWidget(self.btn_load)
        
        splitter.addWidget(right_panel)
        
        # Define proporções do splitter
        splitter.setSizes([400, 400])
        
        layout.addWidget(splitter)
        
        # Botão fechar
        close_btn = QPushButton("Fechar")
        close_btn.clicked.connect(self.reject)
        layout.addWidget(close_btn)
    
    def _on_recipe_selected(self, recipe_id: str):
        """Atualiza o preview quando uma receita é selecionada."""
        recipe = self.manager.load_recipe(recipe_id)
        
        if recipe:
            preview_text = f"""
<h3>{recipe.name}</h3>
<p><b>ID:</b> {recipe.recipe_id}</p>
<p><b>Criado:</b> {recipe.created_at[:10] if recipe.created_at else 'N/A'}</p>
<p><b>Modificado:</b> {recipe.modified_at[:10] if recipe.modified_at else 'N/A'}</p>

<hr>

<h4>📐 Stencil</h4>
<p>
Dimensões: {recipe.stencil.width_mm} x {recipe.stencil.height_mm} mm<br>
Espessura: {recipe.stencil.thickness_mm} mm<br>
Material: {recipe.stencil.material}
</p>

<h4>🎯 Tensão</h4>
<p>
Status: {'Habilitado' if recipe.tension.enabled else 'Desabilitado'}<br>
Grid: {recipe.tension.grid_rows} x {recipe.tension.grid_cols}<br>
Aceitação: {recipe.tension.acceptance.min_tension} - {recipe.tension.acceptance.max_tension} N/cm²
</p>

<h4>📷 Captura</h4>
<p>
Área: ({recipe.capture.origin.x}, {recipe.capture.origin.y}) até ({recipe.capture.end.x}, {recipe.capture.end.y})<br>
Steps: {recipe.capture.step_x} x {recipe.capture.step_y} mm<br>
Backlight: {'Sim' if recipe.capture.backlight_enabled else 'Não'}
</p>

<h4>🔍 Inspeção</h4>
<p>
Status: {'Habilitado' if recipe.inspection.enabled else 'Pendente (Gerber não carregado)'}<br>
Threshold: {recipe.inspection.default_threshold}<br>
% Mínimo: {recipe.inspection.default_min_percent}%
</p>
"""
            self.preview_label.setText(preview_text)
            self.btn_edit.setEnabled(True)
            self.btn_delete.setEnabled(True)
            self.btn_duplicate.setEnabled(True)
            self.btn_load.setEnabled(True)
        else:
            self.preview_label.setText("Erro ao carregar receita.")
            self.btn_edit.setEnabled(False)
            self.btn_delete.setEnabled(False)
            self.btn_duplicate.setEnabled(False)
            self.btn_load.setEnabled(False)
    
    def _on_new_recipe(self):
        """Cria uma nova receita."""
        dialog = RecipeEditorDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            recipe = dialog.recipe
            if self.manager.save_recipe(recipe):
                self.recipe_list.refresh_list()
                QMessageBox.information(
                    self, "Sucesso", 
                    f"Receita '{recipe.name}' criada com sucesso!"
                )
    
    def _on_edit_recipe(self, recipe_id: str = None):
        """Edita a receita selecionada."""
        if recipe_id is None:
            recipe_id = self.recipe_list.get_selected_recipe_id()
        
        if not recipe_id:
            return
        
        recipe = self.manager.load_recipe(recipe_id)
        if not recipe:
            QMessageBox.warning(self, "Erro", "Não foi possível carregar a receita.")
            return
        
        dialog = RecipeEditorDialog(recipe, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            recipe = dialog.recipe
            if self.manager.save_recipe(recipe):
                self.recipe_list.refresh_list()
                self._on_recipe_selected(recipe.recipe_id)
                QMessageBox.information(
                    self, "Sucesso", 
                    f"Receita '{recipe.name}' atualizada!"
                )
    
    def _on_delete_recipe(self):
        """Exclui a receita selecionada."""
        recipe_id = self.recipe_list.get_selected_recipe_id()
        if not recipe_id:
            return
        
        reply = QMessageBox.question(
            self, "Confirmar Exclusão",
            f"Deseja realmente excluir a receita '{recipe_id}'?\n\n"
            "Esta ação não pode ser desfeita.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.manager.delete_recipe(recipe_id):
                self.recipe_list.refresh_list()
                self.preview_label.setText("Selecione uma receita.")
                self.btn_edit.setEnabled(False)
                self.btn_delete.setEnabled(False)
                self.btn_duplicate.setEnabled(False)
                self.btn_load.setEnabled(False)
                QMessageBox.information(self, "Sucesso", "Receita excluída.")
    
    def _on_duplicate_recipe(self):
        """Duplica a receita selecionada."""
        recipe_id = self.recipe_list.get_selected_recipe_id()
        if not recipe_id:
            return
        
        # Pede novo nome
        from PyQt6.QtWidgets import QInputDialog
        new_name, ok = QInputDialog.getText(
            self, "Duplicar Receita",
            "Nome para a nova receita:"
        )
        
        if ok and new_name.strip():
            new_recipe = self.manager.duplicate_recipe(recipe_id, new_name.strip())
            if new_recipe and self.manager.save_recipe(new_recipe):
                self.recipe_list.refresh_list()
                QMessageBox.information(
                    self, "Sucesso", 
                    f"Receita duplicada como '{new_name}'!"
                )
    
    def _on_load_recipe(self):
        """Carrega a receita selecionada para uso."""
        recipe_id = self.recipe_list.get_selected_recipe_id()
        if not recipe_id:
            return
        
        recipe = self.manager.load_recipe(recipe_id)
        if recipe:
            self.manager.set_current_recipe(recipe)
            self.recipe_loaded.emit(recipe)
            QMessageBox.information(
                self, "Receita Carregada",
                f"Receita '{recipe.name}' carregada com sucesso!\n\n"
                "As configurações serão aplicadas às próximas operações."
            )
            self.accept()


# =============================================================================
# TESTE
# =============================================================================

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Cria manager e exemplo
    manager = RecipeManager()
    
    # Cria receita de exemplo se não existir
    if not manager.list_recipes():
        sample = create_sample_recipe()
        manager.save_recipe(sample)
    
    # Abre diálogo
    dialog = RecipeManagerDialog(manager)
    dialog.show()
    
    sys.exit(app.exec())
