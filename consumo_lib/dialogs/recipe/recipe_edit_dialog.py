# -*- coding: utf-8 -*-
"""
recipe_edit_dialog.py
----------------------
Diálogo para criar ou editar uma receita.

Responsabilidade: Formulário com 4 tabs (Info, Stencil, Tensão, Captura)
para edição completa de uma receita.

Autor: Sistema AOI Tensiometro
Data: 2026-01-16 (Refatorado de recipe_dialogs.py)
"""

import logging
from typing import Optional
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QTextEdit, QComboBox,
    QSpinBox, QDoubleSpinBox, QCheckBox, QGroupBox,
    QTabWidget, QMessageBox, QDialogButtonBox
)
from PyQt6.QtCore import Qt
from aoi_lib.recipe_manager import (
    Recipe, StencilInfo, TensionConfig,
    TensionAcceptance, CaptureConfig,
    Point2D, MACHINE_LIMITS
)
from consumo_lib.ui import COLORS, SPACE

logger = logging.getLogger(__name__)


class RecipeEditorDialog(QDialog):
    """
    Diálogo para criar ou editar uma receita.

    Responsabilidade:
    - Formulário com 5 tabs para edição de receita
    - Validação de dados antes de salvar
    - Carregar/salvar dados da receita

    Tabs:
    1. Informações (nome, ID, autor, notas)
    2. Stencil (dimensões, material)
    3. Tensão (grid, critérios de aceitação)
    4. Captura (área, parâmetros)
    """

    def __init__(self, recipe: Recipe = None, parent=None):
        """
        Inicializa diálogo de edição de receita.

        Args:
            recipe: Receita para editar (None = nova receita)
            parent: Widget pai (opcional)
        """
        super().__init__(parent)
        self.recipe = recipe or Recipe(name="Nova Receita")
        self.is_new = recipe is None

        self.setWindowTitle("Nova Receita" if self.is_new else f"Editar: {self.recipe.name}")
        self.setMinimumSize(700, 600)

        self.setup_ui()
        self.load_recipe_data()

    def setup_ui(self):
        """Configura interface do diálogo com 5 tabs."""
        layout = QVBoxLayout(self)

        # Tabs para organizar seções
        self.tabs = QTabWidget()

        # Tab 1: Informações Básicas
        self.tabs.addTab(self._create_info_tab(), "Informações")

        # Tab 2: Stencil
        self.tabs.addTab(self._create_stencil_tab(), "Stencil")

        # Tab 3: Tensão
        self.tabs.addTab(self._create_tension_tab(), "Tensão")

        # Tab 4: Captura
        self.tabs.addTab(self._create_capture_tab(), "Captura")

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
        legend.setStyleSheet(f"color: {COLORS.TEXT_HINT}; font-size: 10px;")
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
