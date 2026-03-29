"""
Dialog de Configuração de Critérios de Tensão

Implementa interface para configurar critérios globais de aceitação de tensão:
- Tensão mínima/máxima aceitável
- Limites de warning (alerta)
- Aplicável a todos os stencils do sistema

Author: Claude
Created: 2026-03-29
"""

import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QGroupBox, QFormLayout, QDoubleSpinBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from consumo_lib.ui import COLORS, TYPO, SPACE, DIM
from consumo_lib.ui.widget_standards import StandardButton

from consumo_lib.managers.tension_criteria_manager import TensionCriteriaManager, TensionCriteriaConfig

logger = logging.getLogger(__name__)


class TensionCriteriaDialog(QDialog):
    """
    Dialog de configuração de critérios de tensão globais.

    Permite configurar:
        - Tensão mínima aceitável (NOK abaixo deste valor)
        - Tensão máxima aceitável (NOK acima deste valor)
        - Limite warning inferior
        - Limite warning superior

    Atributos:
        criteria_manager: Gerenciador de critérios de tensão
        criteria_changed: Sinal emitido quando critérios são aplicados
    """

    criteria_changed = pyqtSignal(object)  # TensionCriteriaConfig

    def __init__(
        self,
        criteria_manager: TensionCriteriaManager,
        parent=None
    ):
        """
        Inicializa dialog de critérios de tensão.

        Args:
            criteria_manager: Gerenciador de critérios
            parent: Widget pai
        """
        super().__init__(parent)
        self.criteria_manager = criteria_manager
        self.original_config: TensionCriteriaConfig = None

        self.setup_ui()
        self.load_current_config()

    def setup_ui(self):
        """Configura interface do dialog."""
        self.setWindowTitle("Critérios de Aceitação de Tensão")
        self.setModal(True)
        self.setMinimumWidth(450)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Título
        title_label = QLabel("Critérios de Aceitação de Tensão")
        title_label.setFont(TYPO.get_font(TYPO.HEADLINE_MEDIUM, bold=True))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Descrição
        desc_label = QLabel(
            "Estes critérios são aplicados a todos os stencils do sistema.\n"
            "Medições fora dos limites OK/WARNING serão classificadas como NOK."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; padding: {SPACE.SM}px;")
        layout.addWidget(desc_label)

        # Grupo: Limites de Aceitação
        acceptance_group = QGroupBox("Limites de Aceitação")
        acceptance_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: 12px;
                font-weight: bold;
                color: {COLORS.TEXT_PRIMARY};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)

        acceptance_layout = QFormLayout(acceptance_group)
        acceptance_layout.setSpacing(12)

        # Spinbox style
        spinbox_style = f"""
            QDoubleSpinBox {{
                min-height: 28px;
                max-width: 100px;
                font-size: 12px;
                padding: 4px 8px;
                border: 1px solid {COLORS.BORDER};
                border-radius: 4px;
                background-color: {COLORS.BACKGROUND};
            }}
        """

        # Mínimo (NOK abaixo)
        lbl_min = QLabel("Mínimo (NOK abaixo):")
        lbl_min.setStyleSheet(f"font-size: 11px; color: {COLORS.TEXT_PRIMARY};")
        self.spin_min = QDoubleSpinBox()
        self.spin_min.setRange(0, 100)
        self.spin_min.setDecimals(1)
        self.spin_min.setSingleStep(0.5)
        self.spin_min.setStyleSheet(spinbox_style)
        self.spin_min.setSuffix(" N/cm²")
        acceptance_layout.addRow(lbl_min, self.spin_min)

        # Máximo (NOK acima)
        lbl_max = QLabel("Máximo (NOK acima):")
        lbl_max.setStyleSheet(f"font-size: 11px; color: {COLORS.TEXT_PRIMARY};")
        self.spin_max = QDoubleSpinBox()
        self.spin_max.setRange(0, 100)
        self.spin_max.setDecimals(1)
        self.spin_max.setSingleStep(0.5)
        self.spin_max.setStyleSheet(spinbox_style)
        self.spin_max.setSuffix(" N/cm²")
        acceptance_layout.addRow(lbl_max, self.spin_max)

        layout.addWidget(acceptance_group)

        # Grupo: Limites de Warning
        warning_group = QGroupBox("Limites de Warning")
        warning_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: 12px;
                font-weight: bold;
                color: {COLORS.WARNING};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)

        warning_layout = QFormLayout(warning_group)
        warning_layout.setSpacing(12)

        # Warning inferior
        lbl_warn_low = QLabel("Warning ↓:")
        lbl_warn_low.setStyleSheet(f"font-size: 11px; color: {COLORS.WARNING};")
        self.spin_warn_low = QDoubleSpinBox()
        self.spin_warn_low.setRange(0, 100)
        self.spin_warn_low.setDecimals(1)
        self.spin_warn_low.setSingleStep(0.5)
        self.spin_warn_low.setStyleSheet(spinbox_style)
        self.spin_warn_low.setSuffix(" N/cm²")
        warning_layout.addRow(lbl_warn_low, self.spin_warn_low)

        # Warning superior
        lbl_warn_high = QLabel("Warning ↑:")
        lbl_warn_high.setStyleSheet(f"font-size: 11px; color: {COLORS.WARNING};")
        self.spin_warn_high = QDoubleSpinBox()
        self.spin_warn_high.setRange(0, 100)
        self.spin_warn_high.setDecimals(1)
        self.spin_warn_high.setSingleStep(0.5)
        self.spin_warn_high.setStyleSheet(spinbox_style)
        self.spin_warn_high.setSuffix(" N/cm²")
        warning_layout.addRow(lbl_warn_high, self.spin_warn_high)

        layout.addWidget(warning_group)

        # Nota sobre classificação
        note_label = QLabel(
            "<b>Classificação:</b><br>"
            "• <span style='color: #27AE60;'>OK</span>: Entre warning_low e warning_high<br>"
            "• <span style='color: #F1C40F;'>WARNING</span>: Entre min/warn_low ou warn_high/max<br>"
            "• <span style='color: #E74C3C;'>NOK</span>: Abaixo de min ou acima de max"
        )
        note_label.setWordWrap(True)
        note_label.setStyleSheet(f"""
            background-color: {COLORS.SURFACE_VARIANT};
            padding: {SPACE.MD}px;
            border-radius: {DIM.RADIUS_SM}px;
            font-size: 11px;
        """)
        layout.addWidget(note_label)

        layout.addSpacing(12)

        # Botões
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        self.btn_apply = StandardButton("Aplicar", variant="primary-green", semantic_size="dialog-primary")
        self.btn_apply.setMinimumWidth(100)
        self.btn_apply.clicked.connect(self.on_apply_clicked)
        buttons_layout.addWidget(self.btn_apply)

        self.btn_cancel = StandardButton("Cancelar", variant="secondary", semantic_size="dialog-secondary")
        self.btn_cancel.setMinimumWidth(100)
        self.btn_cancel.clicked.connect(self.reject)
        buttons_layout.addWidget(self.btn_cancel)

        layout.addLayout(buttons_layout)

    def load_current_config(self):
        """
        Carrega configuração atual e preenche campos.

        Também armazena configuração original para detectar mudanças.
        """
        try:
            criteria = self.criteria_manager.get_criteria()
            self.original_config = criteria

            # Bloqueia sinais para evitar múltiplas atualizações
            self.spin_min.blockSignals(True)
            self.spin_max.blockSignals(True)
            self.spin_warn_low.blockSignals(True)
            self.spin_warn_high.blockSignals(True)

            self.spin_min.setValue(criteria.min_tension)
            self.spin_max.setValue(criteria.max_tension)
            self.spin_warn_low.setValue(criteria.warning_low)
            self.spin_warn_high.setValue(criteria.warning_high)

            self.spin_min.blockSignals(False)
            self.spin_max.blockSignals(False)
            self.spin_warn_low.blockSignals(False)
            self.spin_warn_high.blockSignals(False)

            logger.debug(f"Critérios carregados: {criteria}")

        except Exception as e:
            logger.error(f"Erro ao carregar critérios: {e}")
            QMessageBox.critical(
                self,
                "Erro",
                f"Erro ao carregar critérios:\n{e}",
                QMessageBox.StandardButton.Ok
            )
            self.reject()

    def on_apply_clicked(self):
        """
        Processa clique no botão Aplicar.

        Valida e salva novos critérios.
        """
        # Captura novos valores
        min_tension = self.spin_min.value()
        max_tension = self.spin_max.value()
        warning_low = self.spin_warn_low.value()
        warning_high = self.spin_warn_high.value()

        # Validação básica
        if min_tension >= max_tension:
            QMessageBox.warning(
                self,
                "Validação",
                "O valor mínimo deve ser menor que o máximo.",
                QMessageBox.StandardButton.Ok
            )
            return

        if warning_low < min_tension:
            QMessageBox.warning(
                self,
                "Validação",
                "Warning ↓ deve ser maior ou igual ao valor mínimo.\n\n"
                f"Mínimo atual: {min_tension} N/cm²\n"
                f"Warning ↓ informado: {warning_low} N/cm²",
                QMessageBox.StandardButton.Ok
            )
            return

        if warning_high > max_tension:
            QMessageBox.warning(
                self,
                "Validação",
                "Warning ↑ deve ser menor ou igual ao valor máximo.\n\n"
                f"Máximo atual: {max_tension} N/cm²\n"
                f"Warning ↑ informado: {warning_high} N/cm²",
                QMessageBox.StandardButton.Ok
            )
            return

        if warning_low >= warning_high:
            QMessageBox.warning(
                self,
                "Validação",
                "Warning ↓ deve ser menor que Warning ↑.",
                QMessageBox.StandardButton.Ok
            )
            return

        # Cria nova configuração
        new_criteria = TensionCriteriaConfig(
            min_tension=min_tension,
            max_tension=max_tension,
            warning_low=warning_low,
            warning_high=warning_high
        )

        # Tenta salvar
        success = self.criteria_manager.update_criteria(new_criteria)

        if success:
            QMessageBox.information(
                self,
                "Sucesso",
                "Critérios atualizados com sucesso!\n\n"
                "Os novos critérios serão aplicados a todas as medições.",
                QMessageBox.StandardButton.Ok
            )

            # Emite sinal
            self.criteria_changed.emit(new_criteria)

            # Fecha dialog
            self.accept()
        else:
            QMessageBox.warning(
                self,
                "Erro",
                "Não foi possível salvar os critérios.",
                QMessageBox.StandardButton.Ok
            )