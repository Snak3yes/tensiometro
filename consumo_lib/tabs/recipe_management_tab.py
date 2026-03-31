"""
Aba de gerenciamento de receitas.

Disponibiliza criação, edição, exclusão e carregamento de receitas
diretamente na interface principal.
"""

import logging
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QMessageBox, QSplitter, QDialog
)

from consumo_lib.dialogs.recipe.recipe_edit_dialog import RecipeEditorDialog
from consumo_lib.dialogs.recipe.recipe_list_widget import RecipeListWidget
from consumo_lib.ui import TYPO, SPACE, COLORS
from consumo_lib.ui.widget_standards import StandardButton

logger = logging.getLogger(__name__)


class RecipeManagementTab(QWidget):
    """Aba visível para gerenciamento de receitas."""

    def __init__(self, recipe_manager, recipe_controller=None, parent=None):
        super().__init__(parent)
        self.recipe_manager = recipe_manager
        self.recipe_controller = recipe_controller
        self.current_recipe_id: Optional[str] = None

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        title = QLabel("Receitas")
        title.setFont(TYPO.get_font(TYPO.HEADLINE_MEDIUM, bold=True))
        layout.addWidget(title)

        subtitle = QLabel(
            "Crie, edite e carregue receitas vinculáveis aos stencils e à medição de tensão."
        )
        subtitle.setStyleSheet(f"color: {COLORS.TEXT_HINT};")
        layout.addWidget(subtitle)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        layout.addWidget(splitter, 1)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(SPACE.SM)

        self.recipe_list = RecipeListWidget(self.recipe_manager, self)
        left_layout.addWidget(self.recipe_list, 1)

        actions = QHBoxLayout()
        actions.setSpacing(SPACE.SM)

        self.btn_new = StandardButton("Nova Receita", variant="primary-green")
        self.btn_new.clicked.connect(self._on_new_recipe)
        actions.addWidget(self.btn_new)

        self.btn_edit = StandardButton("Editar", variant="secondary")
        self.btn_edit.clicked.connect(self._on_edit_recipe)
        self.btn_edit.setEnabled(False)
        actions.addWidget(self.btn_edit)

        self.btn_delete = StandardButton("Excluir", variant="secondary")
        self.btn_delete.clicked.connect(self._on_delete_recipe)
        self.btn_delete.setEnabled(False)
        actions.addWidget(self.btn_delete)

        self.btn_refresh = StandardButton("Atualizar", variant="secondary")
        self.btn_refresh.clicked.connect(self.recipe_list.refresh_list)
        actions.addWidget(self.btn_refresh)

        left_layout.addLayout(actions)
        splitter.addWidget(left_panel)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 0, 0, 0)
        right_layout.setSpacing(SPACE.MD)

        self.current_recipe_label = QLabel("Receita atual: nenhuma")
        self.current_recipe_label.setStyleSheet(f"font-weight: bold; color: {COLORS.TEXT_PRIMARY};")
        right_layout.addWidget(self.current_recipe_label)

        self.preview_label = QLabel("Selecione uma receita para ver os detalhes.")
        self.preview_label.setWordWrap(True)
        self.preview_label.setTextFormat(Qt.TextFormat.RichText)
        self.preview_label.setStyleSheet(
            f"background-color: {COLORS.SURFACE_VARIANT};"
            f"border-radius: 6px; padding: 12px;"
        )
        right_layout.addWidget(self.preview_label, 1)

        load_actions = QHBoxLayout()
        load_actions.addStretch()

        self.btn_load = StandardButton("Carregar Receita", variant="primary-blue")
        self.btn_load.clicked.connect(self._on_load_recipe)
        self.btn_load.setEnabled(False)
        load_actions.addWidget(self.btn_load)

        right_layout.addLayout(load_actions)
        splitter.addWidget(right_panel)
        splitter.setSizes([420, 560])

    def _connect_signals(self):
        self.recipe_list.recipe_selected.connect(self._on_recipe_selected)
        self.recipe_list.recipe_double_clicked.connect(self._on_edit_recipe)
        if self.recipe_controller is not None:
            self.recipe_controller.recipe_loaded.connect(self._on_recipe_loaded)

    def _on_recipe_selected(self, recipe_id: str):
        self.current_recipe_id = recipe_id
        self.btn_edit.setEnabled(True)
        self.btn_delete.setEnabled(True)
        self.btn_load.setEnabled(True)
        self._update_preview(recipe_id)

    def _update_preview(self, recipe_id: str):
        recipe = self.recipe_manager.load_recipe(recipe_id)
        if recipe is None:
            self.preview_label.setText("Erro ao carregar receita.")
            return

        self.preview_label.setText(
            f"""
            <h3>{recipe.name}</h3>
            <p><b>ID:</b> {recipe.recipe_id}</p>
            <p><b>Criado:</b> {recipe.created_at[:10] if recipe.created_at else 'N/A'}</p>
            <p><b>Modificado:</b> {recipe.modified_at[:10] if recipe.modified_at else 'N/A'}</p>
            <hr>
            <h4>Stencil</h4>
            <p>
            Dimensões: {recipe.stencil.width_mm} x {recipe.stencil.height_mm} mm<br>
            Espessura: {recipe.stencil.thickness_mm} mm<br>
            Material: {recipe.stencil.material}
            </p>
            <h4>Tensão</h4>
            <p>
            Status: {'Habilitado' if recipe.tension.enabled else 'Desabilitado'}<br>
            Padrão: {recipe.tension.measurement_pattern_name or 'Manual'}<br>
            Grid: {recipe.tension.grid_rows} x {recipe.tension.grid_cols}<br>
            Alturas Z: mov={recipe.tension.movement_height} / med={recipe.tension.measurement_height}<br>
            Aceitação: {recipe.tension.acceptance.min_tension} - {recipe.tension.acceptance.max_tension} N/cm²
            </p>
            <h4>Captura</h4>
            <p>
            Área: ({recipe.capture.origin.x}, {recipe.capture.origin.y}) até ({recipe.capture.end.x}, {recipe.capture.end.y})<br>
            Steps: {recipe.capture.step_x} x {recipe.capture.step_y} mm<br>
            Backlight: {'Sim' if recipe.capture.backlight_enabled else 'Não'}
            </p>
            """
        )

    def _on_new_recipe(self):
        dialog = RecipeEditorDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            recipe = dialog.recipe
            if self.recipe_manager.save_recipe(recipe):
                self.recipe_list.refresh_list()
                self._select_recipe_by_id(recipe.recipe_id)
            else:
                QMessageBox.warning(self, "Erro", f"Falha ao salvar receita '{recipe.name}'.")

    def _on_edit_recipe(self, recipe_id: str = None):
        target_id = recipe_id or self.current_recipe_id
        if not target_id:
            QMessageBox.warning(self, "Receita", "Selecione uma receita para editar.")
            return

        recipe = self.recipe_manager.load_recipe(target_id)
        if recipe is None:
            QMessageBox.warning(self, "Receita", "Não foi possível carregar a receita selecionada.")
            return

        dialog = RecipeEditorDialog(recipe, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated = dialog.recipe
            if self.recipe_manager.save_recipe(updated):
                self.recipe_list.refresh_list()
                self._select_recipe_by_id(updated.recipe_id)
            else:
                QMessageBox.warning(self, "Erro", f"Falha ao salvar receita '{updated.name}'.")

    def _on_delete_recipe(self):
        if not self.current_recipe_id:
            return

        recipe = self.recipe_manager.load_recipe(self.current_recipe_id)
        recipe_label = recipe.name if recipe else self.current_recipe_id
        reply = QMessageBox.question(
            self,
            "Excluir Receita",
            f"Deseja realmente excluir a receita '{recipe_label}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        if self.recipe_manager.delete_recipe(self.current_recipe_id):
            self.current_recipe_id = None
            self.recipe_list.refresh_list()
            self.preview_label.setText("Selecione uma receita para ver os detalhes.")
            self.btn_edit.setEnabled(False)
            self.btn_delete.setEnabled(False)
            self.btn_load.setEnabled(False)
        else:
            QMessageBox.warning(self, "Erro", "Não foi possível excluir a receita.")

    def _on_load_recipe(self):
        if not self.current_recipe_id:
            QMessageBox.warning(self, "Receita", "Selecione uma receita para carregar.")
            return

        if self.recipe_controller is not None:
            self.recipe_controller.load_recipe(self.current_recipe_id)
        else:
            recipe = self.recipe_manager.load_recipe(self.current_recipe_id)
            if recipe is not None:
                self._on_recipe_loaded(recipe)

    def _on_recipe_loaded(self, recipe):
        self.current_recipe_label.setText(f"Receita atual: {recipe.name}")
        logger.info("Receita carregada pela aba: %s", recipe.name)

    def _select_recipe_by_id(self, recipe_id: str):
        table = self.recipe_list.table
        for row in range(table.rowCount()):
            item = table.item(row, 1)
            if item and item.text() == recipe_id:
                table.selectRow(row)
                self._on_recipe_selected(recipe_id)
                break
