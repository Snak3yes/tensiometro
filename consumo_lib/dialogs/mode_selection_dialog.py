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
        self.setFixedSize(200, 160)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Ícone (centralizado)
        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 48px;")
        layout.addWidget(icon_label)

        # Título (centralizado)
        title_label = QLabel(title)
        title_font = title_label.font()
        title_font.setBold(True)
        title_font.setPointSize(14)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setWordWrap(True)
        title_label.setStyleSheet("color: #212121;")
        layout.addWidget(title_label)

        # Tempo estimado (centralizado, destaque)
        time_label = QLabel(time_estimate)
        time_font = time_label.font()
        time_font.setPointSize(11)
        time_label.setFont(time_font)
        time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        time_label.setStyleSheet("color: #2196F3; font-weight: 600;")
        layout.addWidget(time_label)

        # Descrição (centralizada)
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setStyleSheet("color: #616161; font-size: 11px; line-height: 1.4;")
        layout.addWidget(desc_label)

        layout.addStretch()

        # Estilo inicial
        self.update_style()

    def update_style(self):
        """Atualiza estilo visual baseado no estado de seleção"""
        if self.is_selected:
            # Card selecionado: fundo azul muito suave, borda azul
            bg_color = "#E3F2FD"
            border_color = "#2196F3"
            border_width = "2px"
            shadow = "0 4px 12px rgba(33, 150, 243, 0.3)"
        else:
            # Card normal: fundo branco, borda cinza clara
            bg_color = "#FFFFFF"
            border_color = "#E0E0E0"
            border_width = "1px"
            shadow = "0 2px 8px rgba(0, 0, 0, 0.08)"

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                border: {border_width} solid {border_color};
                border-radius: 12px;
            }}
            QWidget:hover {{
                background-color: {"#F5F5F5" if not self.is_selected else "#E3F2FD"};
                border: 2px solid #2196F3;
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
        self.setFixedSize(750, 420)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 40, 50, 40)
        layout.setSpacing(25)

        # Título principal
        title_label = QLabel("Escolha o Modo de Inspeção")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #212121;")
        layout.addWidget(title_label)

        # Subtítulo com código do stencil
        subtitle_label = QLabel(f"Stencil: {self.stencil_code}")
        subtitle_font = subtitle_label.font()
        subtitle_font.setPointSize(12)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setStyleSheet("color: #616161;")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label)

        layout.addSpacing(20)

        # Container dos cards
        cards_container = QWidget()
        cards_layout = QHBoxLayout(cards_container)
        cards_layout.setSpacing(25)
        cards_layout.setContentsMargins(10, 0, 10, 0)

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

        layout.addSpacing(25)

        # Botões
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)

        self.confirm_button = QPushButton("Confirmar")
        self.confirm_button.setMinimumWidth(160)
        self.confirm_button.setMinimumHeight(40)
        self.confirm_button.setEnabled(False)  # Desabilitado até selecionar
        self.confirm_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-size: 13px;
                font-weight: 600;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
                color: #757575;
            }
        """)
        self.confirm_button.clicked.connect(self.on_confirm_clicked)
        buttons_layout.addWidget(self.confirm_button)

        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setMinimumWidth(160)
        self.cancel_button.setMinimumHeight(40)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #616161;
                font-size: 13px;
                font-weight: 600;
                border: 2px solid #E0E0E0;
                border-radius: 6px;
                padding: 10px 24px;
            }
            QPushButton:hover {
                background-color: #F5F5F5;
                border: 2px solid #BDBDBD;
                color: #212121;
            }
            QPushButton:pressed {
                background-color: #E0E0E0;
            }
        """)
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)

        buttons_layout.addStretch()
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
