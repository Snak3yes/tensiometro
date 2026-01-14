"""
widgets/stencil/identification_widget.py
----------------------------------------
Widget para identificação e seleção de stencil.
"""

import logging
from datetime import datetime
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QGroupBox, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from aoi_lib.stencil_tracker import StencilTracker, Stencil

log = logging.getLogger(__name__)


class StencilIdentificationWidget(QWidget):
    """
    Widget para identificação e seleção de stencil.

    Permite:
    - Entrada de código de barras (manual ou leitor USB)
    - Visualização de informações do stencil selecionado
    - Acesso rápido ao histórico

    Signals:
        stencil_selected: Emitido quando um stencil é selecionado/carregado
        stencil_cleared: Emitido quando a seleção é limpa
    """

    stencil_selected = pyqtSignal(object)  # Stencil
    stencil_cleared = pyqtSignal()
    recipe_requested = pyqtSignal(str)  # Nome da receita para carregar

    def __init__(self, tracker: StencilTracker, parent=None):
        super().__init__(parent)
        self.tracker = tracker
        self.current_stencil: Optional[Stencil] = None

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # ================== ENTRADA DE CÓDIGO ==================
        input_group = QGroupBox("🏷️ Identificação do Stencil")
        input_layout = QHBoxLayout(input_group)

        input_layout.addWidget(QLabel("Código:"))

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Escaneie ou digite o código de barras...")
        self.code_input.setMinimumWidth(250)
        self.code_input.setFont(QFont("Consolas", 12))
        input_layout.addWidget(self.code_input, 1)

        self.btn_load = QPushButton("🔍 Carregar")
        self.btn_load.setDefault(True)
        input_layout.addWidget(self.btn_load)

        self.btn_clear = QPushButton("✖ Limpar")
        self.btn_clear.setEnabled(False)
        input_layout.addWidget(self.btn_clear)

        layout.addWidget(input_group)

        # ================== INFORMAÇÕES DO STENCIL ==================
        self.info_frame = QFrame()
        self.info_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.info_frame.setVisible(False)
        info_layout = QGridLayout(self.info_frame)

        # Status indicator
        self.status_label = QLabel("●")
        self.status_label.setFont(QFont("Arial", 16))
        info_layout.addWidget(self.status_label, 0, 0)

        # Código e descrição
        self.lbl_code = QLabel()
        self.lbl_code.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        info_layout.addWidget(self.lbl_code, 0, 1)

        self.lbl_description = QLabel()
        self.lbl_description.setStyleSheet("color: #666;")
        info_layout.addWidget(self.lbl_description, 0, 2)

        # Receita
        info_layout.addWidget(QLabel("Receita:"), 1, 0)
        self.lbl_recipe = QLabel()
        self.lbl_recipe.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(self.lbl_recipe, 1, 1, 1, 2)

        # Última inspeção
        info_layout.addWidget(QLabel("Última inspeção:"), 2, 0)
        self.lbl_last_inspection = QLabel()
        info_layout.addWidget(self.lbl_last_inspection, 2, 1)

        self.lbl_inspection_count = QLabel()
        self.lbl_inspection_count.setStyleSheet("color: #888;")
        info_layout.addWidget(self.lbl_inspection_count, 2, 2)

        # Alerta de tendência
        self.alert_frame = QFrame()
        self.alert_frame.setVisible(False)
        self.alert_frame.setStyleSheet("""
            QFrame {
                background-color: #FFF3CD;
                border: 1px solid #FFECB5;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        alert_layout = QHBoxLayout(self.alert_frame)
        alert_layout.setContentsMargins(10, 5, 10, 5)

        self.lbl_alert = QLabel()
        self.lbl_alert.setWordWrap(True)
        alert_layout.addWidget(self.lbl_alert, 1)

        info_layout.addWidget(self.alert_frame, 3, 0, 1, 3)

        # Botões de ação
        btn_layout = QHBoxLayout()

        self.btn_history = QPushButton("📊 Histórico")
        self.btn_history.clicked.connect(self._show_history)
        btn_layout.addWidget(self.btn_history)

        self.btn_edit = QPushButton("✏️ Editar")
        self.btn_edit.clicked.connect(self._edit_stencil)
        btn_layout.addWidget(self.btn_edit)

        btn_layout.addStretch()

        info_layout.addLayout(btn_layout, 4, 0, 1, 3)

        layout.addWidget(self.info_frame)

        # ================== MENSAGEM QUANDO VAZIO ==================
        self.empty_label = QLabel(
            "Nenhum stencil selecionado.\n"
            "Escaneie ou digite o código de barras para iniciar."
        )
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: #888; font-style: italic;")
        layout.addWidget(self.empty_label)

        layout.addStretch()

    def _connect_signals(self):
        self.code_input.returnPressed.connect(self._load_stencil)
        self.btn_load.clicked.connect(self._load_stencil)
        self.btn_clear.clicked.connect(self._clear_selection)

    def _load_stencil(self):
        """Carrega stencil pelo código digitado."""
        code = self.code_input.text().strip()

        if not code:
            QMessageBox.warning(
                self, "Código Vazio",
                "Digite ou escaneie o código do stencil."
            )
            return

        # Verifica se stencil existe
        stencil = self.tracker.get_stencil(code)

        if not stencil:
            QMessageBox.warning(
                self, "Programa Não Existe",
                f"O programa '{code}' não existe no sistema.\n\n"
                "Verifique o código ou solicite à engenharia para cadastrar."
            )
            self.code_input.selectAll()
            self.code_input.setFocus()
            return

        self._select_stencil(stencil)

    def _select_stencil(self, stencil: Stencil):
        """Seleciona um stencil e atualiza a interface."""
        self.current_stencil = stencil

        # Atualiza UI
        self.empty_label.setVisible(False)
        self.info_frame.setVisible(True)
        self.btn_clear.setEnabled(True)

        # Status com cor
        status_colors = {
            "active": ("🟢", "#28a745"),
            "warning": ("🟡", "#ffc107"),
            "retired": ("🔴", "#dc3545"),
        }
        icon, color = status_colors.get(stencil.status, ("⚪", "#888"))
        self.status_label.setText(icon)

        # Informações
        self.lbl_code.setText(stencil.code)
        self.lbl_description.setText(stencil.description or "(sem descrição)")
        self.lbl_recipe.setText(stencil.recipe_name or "(nenhuma receita)")

        if stencil.last_inspection:
            try:
                dt = datetime.fromisoformat(stencil.last_inspection)
                self.lbl_last_inspection.setText(dt.strftime("%d/%m/%Y %H:%M"))
            except:
                self.lbl_last_inspection.setText(stencil.last_inspection)
        else:
            self.lbl_last_inspection.setText("Nunca inspecionado")

        self.lbl_inspection_count.setText(f"({stencil.inspection_count} inspeções)")

        # Verifica alertas de tendência
        if stencil.recipe_name:
            # TODO: Obter warning_low da receita
            alert = self.tracker.check_degradation_alert(stencil.code)
            if alert:
                self.alert_frame.setVisible(True)
                self.lbl_alert.setText(alert)
            else:
                self.alert_frame.setVisible(False)
        else:
            self.alert_frame.setVisible(False)

        # Emite sinal
        self.stencil_selected.emit(stencil)

        # Solicita carregamento da receita
        if stencil.recipe_name:
            self.recipe_requested.emit(stencil.recipe_name)

        log.info(f"Stencil selecionado: {stencil.code}")

    def _clear_selection(self):
        """Limpa a seleção atual."""
        self.current_stencil = None
        self.code_input.clear()
        self.info_frame.setVisible(False)
        self.empty_label.setVisible(True)
        self.btn_clear.setEnabled(False)
        self.alert_frame.setVisible(False)

        self.stencil_cleared.emit()
        log.info("Seleção de stencil limpa")

    def _show_history(self):
        """Abre diálogo de histórico."""
        if not self.current_stencil:
            return

        from consumo_lib.dialogs.stencil import StencilHistoryDialog

        dialog = StencilHistoryDialog(
            self.tracker,
            self.current_stencil.code,
            self
        )
        dialog.exec()

    def _edit_stencil(self):
        """Abre diálogo para editar stencil."""
        if not self.current_stencil:
            return

        from consumo_lib.dialogs.stencil import StencilEditDialog

        dialog = StencilEditDialog(
            self.tracker,
            self.current_stencil,
            self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Recarrega stencil atualizado
            stencil = self.tracker.get_stencil(self.current_stencil.code)
            if stencil:
                self._select_stencil(stencil)

    def get_current_stencil(self) -> Optional[Stencil]:
        """Retorna stencil atualmente selecionado."""
        return self.current_stencil

    def set_stencil_code(self, code: str):
        """Define código programaticamente e carrega."""
        self.code_input.setText(code)
        self._load_stencil()
