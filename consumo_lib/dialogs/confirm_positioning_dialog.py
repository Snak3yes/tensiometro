"""
Dialog de Confirmação de Posicionamento do Stencil

Exibe checklist de segurança antes de iniciar medição/inspeção.
"""

import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal

# Design System
from consumo_lib.ui import COLORS, TYPO, SPACE, DIM

logger = logging.getLogger(__name__)


class ConfirmPositioningDialog(QDialog):
    """
    Dialog de confirmação de posicionamento do stencil

    Sinais:
        position_confirmed: Emitido quando usuário confirma posicionamento
    """

    position_confirmed = pyqtSignal()

    # Checklist items
    CHECKLIST_ITEMS = [
        "Stencil fixado na mesa",
        "Área de trabalho limpa",
        "CNC zerada (posição 0,0)",
        "Emergency Stop acessível",
        "Backlight ligado (se inspeção visual)"
    ]

    def __init__(self, stencil_code: str, parent=None):
        """
        Inicializa dialog de confirmação

        Args:
            stencil_code: Código do stencil selecionado
            parent: Widget pai
        """
        super().__init__(parent)
        self.stencil_code = stencil_code
        self.checklist_states = [False] * len(self.CHECKLIST_ITEMS)
        self.setup_ui()

    def setup_ui(self):
        """Configura interface do dialog"""
        self.setWindowTitle("Confirmação de Posicionamento")
        self.setModal(True)
        self.setFixedSize(550, 650)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(40, 40, 40, 40)

        # Título
        title_label = QLabel("Confirmação de Posicionamento")
        title_label.setFont(TYPO.get_font(TYPO.HEADING_LARGE, bold=True))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        layout.addSpacing(10)

        # Ícone do stencil (placeholder)
        icon_container = QLabel()
        icon_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_container.setFixedSize(100, 100)
        icon_container.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS.SECONDARY_LIGHT};
                border: 2px solid {COLORS.PRIMARY_DARK};
                border-radius: 50px;
                font-size: 40px;
            }}
        """)
        icon_container.setText("📋")
        layout.addWidget(icon_container, alignment=Qt.AlignmentFlag.AlignCenter)

        # Código do stencil
        code_label = QLabel(self.stencil_code)
        code_label.setFont(TYPO.get_font(TYPO.HEADING_MEDIUM, bold=True))
        code_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(code_label)

        layout.addSpacing(15)

        # Instruções
        instruction_label = QLabel("Verifique antes de continuar:")
        instruction_label.setFont(TYPO.get_font(TYPO.BODY_LARGE, bold=True))
        layout.addWidget(instruction_label)

        # Checklist
        self.checkboxes = []
        for i, item_text in enumerate(self.CHECKLIST_ITEMS):
            checkbox = QCheckBox(item_text)
            checkbox.stateChanged.connect(
                lambda state, index=i: self._on_checkbox_changed(index, state)
            )
            self.checkboxes.append(checkbox)
            layout.addWidget(checkbox)

        layout.addSpacing(15)

        # Aviso Emergency Stop
        warning_label = QLabel(
            "⚠️  Emergency Stop deve estar acessível em caso de emergência!"
        )
        warning_label.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS.WARNING_LIGHT};
                color: {COLORS.ON_WARNING_LIGHT};
                padding: {SPACE.SM}px;
                border-radius: {DIM.RADIUS_SM}px;
                font-weight: bold;
            }}
        """)
        warning_label.setWordWrap(True)
        warning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(warning_label)

        layout.addStretch()

        # Botões
        buttons_layout = QHBoxLayout()

        self.confirm_button = QPushButton("✓ Confirmar")
        self.confirm_button.setMinimumHeight(DIM.BUTTON_HEIGHT_LG)
        self.confirm_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.SUCCESS};
                color: {COLORS.ON_SUCCESS};
                font-size: 14px;
                font-weight: bold;
                border-radius: {DIM.RADIUS_SM}px;
                padding: {SPACE.XS}px {SPACE.MD}px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.SUCCESS_DARK};
            }}
        """)
        self.confirm_button.clicked.connect(self.on_confirm_clicked)
        buttons_layout.addWidget(self.confirm_button)

        self.cancel_button = QPushButton("✗ Cancelar")
        self.cancel_button.setMinimumHeight(DIM.BUTTON_HEIGHT_LG)
        self.cancel_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.SURFACE};
                color: {COLORS.TEXT_HINT};
                font-size: 14px;
                font-weight: bold;
                border-radius: {DIM.RADIUS_SM}px;
                padding: {SPACE.XS}px {SPACE.MD}px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.OUTLINE};
            }}
        """)
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)

        layout.addLayout(buttons_layout)

    def _on_checkbox_changed(self, index: int, state):
        """
        Handler: Checkbox mudou de estado

        Args:
            index: Índice do checkbox
            state: Novo estado (Qt.CheckState)
        """
        self.checklist_states[index] = (state == Qt.CheckState.Checked.value)

    def on_confirm_clicked(self):
        """Handler: Botão Confirmar clicado"""
        # Log dos itens marcados
        marked_items = [
            self.CHECKLIST_ITEMS[i]
            for i, checked in enumerate(self.checklist_states)
            if checked
        ]

        logger.info(f"Checklist marcados: {marked_items}")

        # Não bloqueia mesmo se não marcaram tudo
        # Sistema confia no operador
        self.position_confirmed.emit()
        self.accept()

    def get_checklist_state(self) -> dict:
        """
        Retorna estado atual do checklist

        Returns:
            Dicionário com itens e seus estados (True/False)
        """
        return {
            item: checked
            for item, checked in zip(self.CHECKLIST_ITEMS, self.checklist_states)
        }
