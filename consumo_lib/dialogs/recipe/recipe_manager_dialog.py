# -*- coding: utf-8 -*-
"""
recipe_manager_dialog.py
-----------------------
Diálogo principal para gerenciar receitas.

Responsabilidade: Listar, criar, editar, excluir e carregar receitas.

Autor: Sistema AOI Tensiometro
Data: 2026-01-16 (Refatorado de recipe_dialogs.py)
"""

import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QSplitter, QFrame, QWidget,
    QInputDialog, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from aoi_lib.recipe_manager import RecipeManager
from consumo_lib.ui import COLORS, TYPO, SPACE
from consumo_lib.ui.widget_standards import StandardButton
from consumo_lib.dialogs.recipe.recipe_list_widget import RecipeListWidget
from consumo_lib.dialogs.recipe.recipe_edit_dialog import RecipeEditorDialog

logger = logging.getLogger(__name__)


class RecipeManagerDialog(QDialog):
    """
    Diálogo principal para gerenciar receitas.

    Responsabilidade:
    - Listar receitas (usando RecipeListWidget)
    - Criar novas receitas
    - Editar receitas existentes
    - Excluir receitas
    - Duplicar receitas
    - Carregar receita para uso
    - Mostrar preview da receita selecionada

    Signals:
    - recipe_loaded(object): Emitido quando receita é carregada (Recipe)
    """

    recipe_loaded = pyqtSignal(object)  # Emite Recipe quando carregada

    def __init__(self, recipe_manager: RecipeManager, parent=None):
        """
        Inicializa diálogo gerenciador de receitas.

        Args:
            recipe_manager: Instância de RecipeManager
            parent: Widget pai (opcional)
        """
        super().__init__(parent)
        self.manager = recipe_manager

        self.setWindowTitle("Gerenciador de Receitas")
        self.setMinimumSize(800, 500)

        self.setup_ui()

    def setup_ui(self):
        """Configura interface do diálogo com splitter (lista + preview)."""
        layout = QVBoxLayout(self)

        # Splitter: lista à esquerda, preview à direita
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Painel esquerdo: lista de receitas
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # Título
        title = QLabel("📋 Receitas Disponíveis")
        title.setFont(TYPO.get_font(TYPO.BODY_LARGE, bold=True))
        left_layout.addWidget(title)

        # Lista de receitas
        self.recipe_list = RecipeListWidget(self.manager, self)
        self.recipe_list.recipe_selected.connect(self._on_recipe_selected)
        self.recipe_list.recipe_double_clicked.connect(self._on_edit_recipe)
        left_layout.addWidget(self.recipe_list)

        # Botões de ação
        btn_layout = QHBoxLayout()

        self.btn_new = StandardButton("➕ Nova")
        self.btn_new.clicked.connect(self._on_new_recipe)
        btn_layout.addWidget(self.btn_new)

        self.btn_edit = StandardButton("✏️ Editar")
        self.btn_edit.clicked.connect(self._on_edit_recipe)
        self.btn_edit.setEnabled(False)
        btn_layout.addWidget(self.btn_edit)

        self.btn_delete = StandardButton("🗑️ Excluir", variant="danger")
        self.btn_delete.clicked.connect(self._on_delete_recipe)
        self.btn_delete.setEnabled(False)
        btn_layout.addWidget(self.btn_delete)

        self.btn_duplicate = StandardButton("📄 Duplicar")
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
        preview_title.setFont(TYPO.get_font(TYPO.BODY_LARGE, bold=True))
        right_layout.addWidget(preview_title)

        self.preview_label = QLabel("Selecione uma receita para ver os detalhes.")
        self.preview_label.setWordWrap(True)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.preview_label.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS.SURFACE};
                border: 1px solid {COLORS.BORDER};
                border-radius: 5px;
                padding: {SPACE.MD}px;
            }}
        """)
        right_layout.addWidget(self.preview_label, 1)

        # Botão de carregar
        self.btn_load = StandardButton("🚀 Carregar Receita")
        self.btn_load.setMinimumHeight(40)
        self.btn_load.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.SUCCESS};
                color: white;
                font-weight: bold;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.SUCCESS};
            }}
            QPushButton:disabled {{
                background-color: {COLORS.TEXT_DISABLED};
            }}
        """)
        self.btn_load.clicked.connect(self._on_load_recipe)
        self.btn_load.setEnabled(False)
        right_layout.addWidget(self.btn_load)

        splitter.addWidget(right_panel)

        # Define proporções do splitter
        splitter.setSizes([400, 400])

        layout.addWidget(splitter)

        # Botão fechar
        close_btn = StandardButton("Fechar")
        close_btn.clicked.connect(self.reject)
        layout.addWidget(close_btn)

    def _on_recipe_selected(self, recipe_id: str):
        """
        Atualiza o preview quando uma receita é selecionada.

        Args:
            recipe_id: ID da receita selecionada
        """
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
        """
        Edita a receita selecionada.

        Args:
            recipe_id: ID da receita (None = usar seleção atual)
        """
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
