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
    QLabel, QLineEdit, QPushButton, QGroupBox, QFrame, QMessageBox, QDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from aoi_lib.stencil_tracker import StencilTracker, Stencil, normalize_stencil_code
from consumo_lib.services.sfcs_stencil_lookup_service import (
    SfcsStencilLookupError,
    SfcsStencilNotFound,
)
from consumo_lib.ui import COLORS, TYPO, SPACE
from consumo_lib.ui.widget_standards import StandardButton

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
    measurement_requested = pyqtSignal()

    def __init__(self, tracker: StencilTracker, parent=None, sfcs_service=None):
        super().__init__(parent)
        self.tracker = tracker
        self.sfcs_service = sfcs_service
        self.current_stencil: Optional[Stencil] = None
        self._sfcs_lookup_error_shown = False

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # ================== ENTRADA DE CÓDIGO ==================
        input_group = QGroupBox("Identificação do Stencil")
        input_layout = QHBoxLayout(input_group)

        input_layout.addWidget(QLabel("Código:"))

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Escaneie ou digite o código de barras...")
        self.code_input.setMinimumWidth(250)
        self.code_input.setFont(TYPO.get_font(TYPO.BODY_MEDIUM))
        input_layout.addWidget(self.code_input, 1)

        self.btn_load = StandardButton("Carregar Stencil")
        self.btn_load.setDefault(True)
        input_layout.addWidget(self.btn_load)

        self.btn_clear = StandardButton("✖ Limpar")
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
        self.status_label.setFont(TYPO.get_font(16))
        info_layout.addWidget(self.status_label, 0, 0)

        # Código e descrição
        self.lbl_code = QLabel()
        self.lbl_code.setFont(TYPO.get_font(TYPO.BODY_LARGE, bold=True))
        info_layout.addWidget(self.lbl_code, 0, 1)

        self.lbl_description = QLabel()
        self.lbl_description.setStyleSheet(f"color: {COLORS.TEXT_HINT};")
        info_layout.addWidget(self.lbl_description, 0, 2)

        # Padrão de medição
        info_layout.addWidget(QLabel("Padrão de medição:"), 1, 0)
        self.lbl_recipe = QLabel()
        self.lbl_recipe.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(self.lbl_recipe, 1, 1, 1, 2)

        # Última medição
        info_layout.addWidget(QLabel("Última medição:"), 2, 0)
        self.lbl_last_inspection = QLabel()
        info_layout.addWidget(self.lbl_last_inspection, 2, 1)

        self.lbl_inspection_count = QLabel()
        self.lbl_inspection_count.setStyleSheet(f"color: {COLORS.TEXT_HINT};")
        info_layout.addWidget(self.lbl_inspection_count, 2, 2)

        # Alerta de tendência
        self.alert_frame = QFrame()
        self.alert_frame.setVisible(False)
        self.alert_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS.WARNING_LIGHT};
                border: 1px solid {COLORS.WARNING};
                border-radius: 5px;
                padding: 5px;
            }}
        """)
        alert_layout = QHBoxLayout(self.alert_frame)
        alert_layout.setContentsMargins(SPACE.MD, SPACE.SM, SPACE.MD, SPACE.SM)

        self.lbl_alert = QLabel()
        self.lbl_alert.setWordWrap(True)
        alert_layout.addWidget(self.lbl_alert, 1)

        info_layout.addWidget(self.alert_frame, 3, 0, 1, 3)

        # Botões de ação
        btn_layout = QHBoxLayout()

        self.btn_history = StandardButton("Histórico")
        self.btn_history.clicked.connect(self._show_history)
        btn_layout.addWidget(self.btn_history)

        self.btn_run_tension = StandardButton("Iniciar Medição", variant="primary-green")
        self.btn_run_tension.setEnabled(False)
        self.btn_run_tension.clicked.connect(self._request_tension_measurement)
        btn_layout.addWidget(self.btn_run_tension)

        btn_layout.addStretch()

        info_layout.addLayout(btn_layout, 4, 0, 1, 3)

        layout.addWidget(self.info_frame)

        # ================== MENSAGEM QUANDO VAZIO ==================
        self.empty_label = QLabel(
            "Nenhum stencil selecionado.\n"
            "Escaneie ou digite o código de barras para iniciar."
        )
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet(f"color: {COLORS.TEXT_HINT}; font-style: italic;")
        layout.addWidget(self.empty_label)

        layout.addStretch()

    def _connect_signals(self):
        self.code_input.textEdited.connect(self._normalize_code_input)
        self.code_input.returnPressed.connect(self._load_stencil)
        self.btn_load.clicked.connect(self._load_stencil)
        self.btn_clear.clicked.connect(self._clear_selection)

    def _normalize_code_input(self, text: str):
        """Mantem o codigo bipado/digitado em maiusculas no campo."""
        normalized = normalize_stencil_code(text)
        if text == normalized:
            return

        cursor_position = self.code_input.cursorPosition()
        self.code_input.blockSignals(True)
        self.code_input.setText(normalized)
        self.code_input.setCursorPosition(min(cursor_position, len(normalized)))
        self.code_input.blockSignals(False)

    def _load_stencil(self):
        """Carrega stencil pelo código digitado."""
        code = normalize_stencil_code(self.code_input.text())
        self.code_input.setText(code)

        if not code:
            QMessageBox.warning(
                self, "Código Vazio",
                "Digite ou escaneie o código do stencil."
            )
            return

        self._sfcs_lookup_error_shown = False
        stencil = self._load_stencil_from_sfcs(code)
        if self._sfcs_lookup_error_shown:
            return
        if stencil is None and not self._sfcs_lookup_enabled():
            stencil = self.tracker.get_stencil(code)

        if not stencil:
            QMessageBox.warning(
                self, "Falha no Cadastro SFCS",
                f"O stencil '{code}' não foi encontrado no cadastro do SFCS.\n\n"
                "Cadastre o stencil no SFCS antes de iniciar o teste de medição."
            )
            self.code_input.selectAll()
            self.code_input.setFocus()
            return

        self._select_stencil(stencil)

    def _sfcs_lookup_enabled(self) -> bool:
        return bool(self.sfcs_service and self.sfcs_service.is_enabled())

    def _load_stencil_from_sfcs(self, code: str) -> Optional[Stencil]:
        if not self._sfcs_lookup_enabled():
            return None

        try:
            record = self.sfcs_service.lookup(code)
            recipe_name = self.sfcs_service.resolve_recipe_name(record)
            return self._sync_sfcs_stencil(record.to_stencil(recipe_name=recipe_name))
        except SfcsStencilNotFound:
            return None
        except SfcsStencilLookupError as exc:
            self._sfcs_lookup_error_shown = True
            QMessageBox.critical(
                self,
                "Falha de Comunicação SFCS",
                f"Não foi possível consultar o cadastro do stencil no SFCS.\n\n{exc}"
            )
            self.code_input.selectAll()
            self.code_input.setFocus()
            return None

    def _sync_sfcs_stencil(self, sfcs_stencil: Stencil) -> Stencil:
        existing = self.tracker.get_stencil(sfcs_stencil.code)
        if existing:
            sfcs_stencil.created_at = existing.created_at
            sfcs_stencil.last_inspection = existing.last_inspection
            sfcs_stencil.inspection_count = existing.inspection_count
            self.tracker.update_stencil(sfcs_stencil)
            return self.tracker.get_stencil(sfcs_stencil.code) or sfcs_stencil

        created = self.tracker.create_stencil(
            sfcs_stencil.code,
            description=sfcs_stencil.description,
            recipe_name=sfcs_stencil.recipe_name,
        )
        created.status = sfcs_stencil.status
        created.notes = sfcs_stencil.notes
        self.tracker.update_stencil(created)
        return created

    def _select_stencil(self, stencil: Stencil):
        """Seleciona um stencil e atualiza a interface."""
        self.current_stencil = stencil

        # Atualiza UI
        self.empty_label.setVisible(False)
        self.info_frame.setVisible(True)
        self.btn_clear.setEnabled(True)
        self.btn_run_tension.setEnabled(True)

        # Status com cor
        status_colors = {
            "active": ("🟢", COLORS.SUCCESS),
            "warning": ("🟡", COLORS.WARNING),
            "retired": ("🔴", COLORS.ERROR),
        }
        icon, color = status_colors.get(stencil.status, ("⚪", COLORS.TEXT_HINT))
        self.status_label.setText(icon)

        # Informações
        self.lbl_code.setText(stencil.code)
        self.lbl_description.setText(stencil.description or "(sem descrição)")
        self.lbl_recipe.setText(stencil.recipe_name or "(nenhum padrão)")

        if stencil.last_inspection:
            try:
                dt = datetime.fromisoformat(stencil.last_inspection)
                self.lbl_last_inspection.setText(dt.strftime("%d/%m/%Y %H:%M"))
            except:
                self.lbl_last_inspection.setText(stencil.last_inspection)
        else:
            self.lbl_last_inspection.setText("Nenhuma medição registrada")

        self.lbl_inspection_count.setText(f"({stencil.inspection_count} medições)")

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

        log.info(f"Stencil selecionado: {stencil.code}")

    def _clear_selection(self):
        """Limpa a seleção atual."""
        self.reset_state(emit_signal=True)

    def reset_state(self, emit_signal: bool = True):
        """Reseta a sessão local de identificação do stencil."""
        had_selection = self.current_stencil is not None
        self.current_stencil = None
        self.code_input.clear()
        self.info_frame.setVisible(False)
        self.empty_label.setVisible(True)
        self.btn_clear.setEnabled(False)
        self.btn_run_tension.setEnabled(False)
        self.alert_frame.setVisible(False)
        self.code_input.clearFocus()
        self.code_input.setFocus()

        if emit_signal and had_selection:
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

    def _request_tension_measurement(self):
        """Solicita abertura do fluxo de medição para o stencil selecionado."""
        if not self.current_stencil:
            QMessageBox.warning(
                self,
                "Stencil",
                "Carregue um stencil antes de iniciar a medição."
            )
            return

        self.measurement_requested.emit()

    def set_stencil_code(self, code: str):
        """Define código programaticamente e carrega."""
        self.code_input.setText(normalize_stencil_code(code))
        self._load_stencil()
