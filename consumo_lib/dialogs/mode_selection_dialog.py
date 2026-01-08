"""
Dialog de Seleção de Modo de Inspeção

Permite usuário escolher entre medição de tensão, inspeção visual,
ou modo completo (ambos).
"""

import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

logger = logging.getLogger(__name__)


class ModeCard(QWidget):
    """
    Card selecionável para modo de inspeção

    Sinais:
        selected: Emitido quando card é selecionado
                  Argumento: mode_type ("tension", "inspection", "both")
    """

    selected = pyqtSignal(str)

    def __init__(self, mode_type: str, title: str, description: str,
                 time_estimate: str, icon: str, parent=None):
        """
        Inicializa card de modo

        Args:
            mode_type: Tipo do modo ("tension", "inspection", "both")
            title: Título do modo
            description: Descrição detalhada
            time_estimate: Tempo estimado (ex: "10 min")
            icon: Emoji ou ícone
            parent: Widget pai
        """
        super().__init__(parent)
        self.mode_type = mode_type
        self.is_selected = False

        self.setup_ui(title, description, time_estimate, icon)

    def setup_ui(self, title: str, description: str,
                 time_estimate: str, icon: str):
        """Configura interface do card"""
        self.setFixedSize(200, 180)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Ícone + tempo
        header_layout = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 32px;")
        header_layout.addWidget(icon_label)

        time_label = QLabel(time_estimate)
        time_font = time_label.font()
        time_font.setBold(True)
        time_font.setPointSize(12)
        time_label.setFont(time_font)
        time_label.setStyleSheet("color: #2196F3;")
        header_layout.addWidget(time_label)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Título
        title_label = QLabel(title)
        title_font = title_label.font()
        title_font.setBold(True)
        title_font.setPointSize(13)
        title_label.setFont(title_font)
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        # Descrição
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(desc_label)

        layout.addStretch()

        # Botão de seleção
        self.select_button = QPushButton("Selecionar")
        self.select_button.setMinimumHeight(35)
        self.select_button.clicked.connect(self.on_clicked)
        layout.addWidget(self.select_button)

        # Estilo inicial
        self.update_style()

    def update_style(self):
        """Atualiza estilo visual baseado no estado de seleção"""
        if self.is_selected:
            bg_color = "#E3F2FD"
            border_color = "#2196F3"
            border_width = "3px"
            btn_text = "✓ Selecionado"
            btn_bg = "#2196F3"
            btn_color = "white"
        else:
            bg_color = "white"
            border_color = "#E0E0E0"
            border_width = "2px"
            btn_text = "Selecionar"
            btn_bg = "#F5F5F5"
            btn_color = "#333333"

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                border: {border_width} solid {border_color};
                border-radius: 8px;
            }}
            QWidget:hover {{
                background-color: {"#BBDEFB" if not self.is_selected else "#E3F2FD"};
                border: 2px solid #2196F3;
            }}
        """)

        self.select_button.setText(btn_text)
        self.select_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {btn_bg};
                color: {btn_color};
                font-size: 12px;
                font-weight: bold;
                border-radius: 4px;
                padding: 5px 15px;
            }}
            QPushButton:hover {{
                background-color: {"#1976D2" if self.is_selected else "#E0E0E0"};
            }}
        """)

    def on_clicked(self):
        """Handler: Card clicado"""
        self.select()

    def select(self):
        """Marca este card como selecionado"""
        if not self.is_selected:
            self.is_selected = True
            self.update_style()
            self.selected.emit(self.mode_type)

    def deselect(self):
        """Desmarca este card"""
        if self.is_selected:
            self.is_selected = False
            self.update_style()

    def mousePressEvent(self, event):
        """Handler: Clique no card (qualquer área)"""
        self.select()


class ModeSelectionDialog(QDialog):
    """
    Dialog de seleção de modo de inspeção

    Sinais:
        mode_selected: Emitido quando usuário seleciona modo
                      Argumento: dict com mode_type e dados do stencil
    """

    mode_selected = pyqtSignal(dict)

    # Configurações dos modos
    MODES = [
        {
            "mode": "tension",
            "title": "Apenas Tensão",
            "description": "Medir tensão superficial em múltiplos pontos",
            "time_estimate": "⏱️ 10 min",
            "icon": "⏱️"
        },
        {
            "mode": "inspection",
            "title": "Apenas Inspeção",
            "description": "Análise visual das aberturas do stencil",
            "time_estimate": "⏱️ 15 min",
            "icon": "🔍"
        },
        {
            "mode": "both",
            "title": "Ambos (Completo)",
            "description": "Tensão + Inspeção Visual completa",
            "time_estimate": "⏱️ 25 min",
            "icon": "✅"
        }
    ]

    def __init__(self, stencil_code: str, parent=None):
        """
        Inicializa dialog de seleção de modo

        Args:
            stencil_code: Código do stencil selecionado
            parent: Widget pai
        """
        super().__init__(parent)
        self.stencil_code = stencil_code
        self.selected_mode = None
        self.mode_cards = []

        self.setup_ui()

    def setup_ui(self):
        """Configura interface do dialog"""
        self.setWindowTitle("Escolha o Modo de Inspeção")
        self.setModal(True)
        self.setFixedSize(700, 450)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Título principal
        title_label = QLabel("Escolha o Modo de Inspeção")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Subtítulo com código do stencil
        subtitle_label = QLabel(f"Stencil: {self.stencil_code}")
        subtitle_font = subtitle_label.font()
        subtitle_font.setPointSize(12)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setStyleSheet("color: #666;")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label)

        layout.addSpacing(10)

        # Container dos cards
        cards_container = QWidget()
        cards_layout = QHBoxLayout(cards_container)
        cards_layout.setSpacing(20)

        # Criar cards
        for mode_config in self.MODES:
            card = ModeCard(
                mode_type=mode_config["mode"],
                title=mode_config["title"],
                description=mode_config["description"],
                time_estimate=mode_config["time_estimate"],
                icon=mode_config["icon"],
                parent=self
            )
            card.selected.connect(self.on_mode_selected)
            cards_layout.addWidget(card)
            self.mode_cards.append(card)

        layout.addWidget(cards_container, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addSpacing(20)

        # Botões
        buttons_layout = QHBoxLayout()

        self.confirm_button = QPushButton("✓ Confirmar Seleção")
        self.confirm_button.setMinimumHeight(45)
        self.confirm_button.setEnabled(False)  # Desabilitado até selecionar
        self.confirm_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 4px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #45A049;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
                color: #757575;
            }
        """)
        self.confirm_button.clicked.connect(self.on_confirm_clicked)
        buttons_layout.addWidget(self.confirm_button)

        self.cancel_button = QPushButton("✗ Cancelar")
        self.cancel_button.setMinimumHeight(45)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #F5F5F5;
                color: #424242;
                font-size: 14px;
                font-weight: bold;
                border-radius: 4px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #E0E0E0;
            }
        """)
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)

        layout.addLayout(buttons_layout)

    def on_mode_selected(self, mode_type: str):
        """
        Handler: Modo selecionado

        Args:
            mode_type: Tipo do modo selecionado
        """
        # Atualiza seleção (radio button behavior)
        self.selected_mode = mode_type

        for card in self.mode_cards:
            if card.mode_type == mode_type:
                # Garante que está selecionado
                if not card.is_selected:
                    card.select()
            else:
                # Desmarca outros cards
                card.deselect()

        # Habilita botão confirmar
        self.confirm_button.setEnabled(True)

        logger.info(f"Modo selecionado: {mode_type}")

    def on_confirm_clicked(self):
        """Handler: Botão Confirmar clicado"""
        if self.selected_mode:
            logger.info(f"Confirmação de modo: {self.selected_mode}")

            # Emite sinal com dados
            self.mode_selected.emit({
                "mode": self.selected_mode,
                "stencil_code": self.stencil_code
            })

            self.accept()

    def get_selected_mode(self) -> str:
        """
        Retorna modo selecionado

        Returns:
            Mode type ("tension", "inspection", "both") ou None
        """
        return self.selected_mode
