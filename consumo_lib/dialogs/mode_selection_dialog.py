"""
Dialog de Seleção de Modo de Inspeção

Permite usuário escolher entre medição de tensão, inspeção visual,
ou modo completo (ambos).
"""

import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QWidget, QGroupBox, QButtonGroup
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
        self.icon_text = icon
        self.icon_label = None  # Será definido no setup_ui

        self.setup_ui(title, description, time_estimate, icon)

    def setup_ui(self, title: str, description: str,
                 time_estimate: str, icon: str):
        """Configura interface do card"""
        self.setFixedSize(220, 140)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Container esquerdo (ícone)
        icon_container = QWidget()
        icon_container.setFixedSize(56, 56)
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)

        self.icon_label = QLabel(icon)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet("font-size: 32px; background-color: #F9FAFB; border-radius: 28px; padding: 12px;")
        self.icon_label.setFixedSize(56, 56)
        icon_layout.addWidget(self.icon_label)

        layout.addWidget(icon_container)

        # Container direito (conteúdo)
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setSpacing(4)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # Título
        title_label = QLabel(title)
        title_font = title_label.font()
        title_font.setBold(True)
        title_font.setPointSize(13)
        title_label.setFont(title_font)
        title_label.setWordWrap(True)
        title_label.setStyleSheet("color: #1F2937;")
        content_layout.addWidget(title_label)

        # Descrição
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #6B7280; font-size: 11px;")
        content_layout.addWidget(desc_label)

        # Tempo estimado
        time_label = QLabel(time_estimate.replace("⏱️ ", ""))
        time_font = time_label.font()
        time_font.setPointSize(10)
        time_label.setFont(time_font)
        time_label.setStyleSheet("""
            color: #059669;
            background-color: #ECFDF5;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: 600;
        """)
        content_layout.addWidget(time_label)

        content_layout.addStretch()
        layout.addWidget(content_container, 1)

        # Estilo inicial
        self.update_style()

    def update_style(self):
        """Atualiza estilo visual baseado no estado de seleção"""
        if self.is_selected:
            # Card selecionado: estilo destacado
            bg_color = "#EFF6FF"
            border_color = "#3B82F6"
            border_width = "2px"
            icon_bg = "#DBEAFE"
        else:
            # Card normal: estilo neutro
            bg_color = "#FFFFFF"
            border_color = "#E5E7EB"
            border_width = "1px"
            icon_bg = "#F9FAFB"

        # Atualiza fundo do ícone
        if self.icon_label:
            self.icon_label.setStyleSheet(f"font-size: 32px; background-color: {icon_bg}; border-radius: 28px; padding: 12px;")

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                border: {border_width} solid {border_color};
                border-radius: 12px;
            }}
            QWidget:hover {{
                background-color: {"#F9FAFB" if not self.is_selected else "#EFF6FF"};
                border: 2px solid {"#D1D5DB" if not self.is_selected else "#3B82F6"};
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
        self.setFixedSize(800, 480)

        # Layout principal com fundo suave
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        header_widget = QWidget()
        header_widget.setStyleSheet("background-color: #F9FAFB; border-bottom: 1px solid #E5E7EB;")
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(40, 30, 40, 30)
        header_layout.setSpacing(12)

        # Título principal
        title_label = QLabel("Escolha o Modo de Inspeção")
        title_font = QFont()
        title_font.setPointSize(22)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #111827;")
        header_layout.addWidget(title_label)

        # Subtítulo com código do stencil
        subtitle_label = QLabel(f"Stencil: {self.stencil_code}")
        subtitle_font = subtitle_label.font()
        subtitle_font.setPointSize(13)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setStyleSheet("color: #6B7280;")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(subtitle_label)

        main_layout.addWidget(header_widget)

        # Container principal (fundo branco)
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: #FFFFFF;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(40, 40, 40, 40)
        content_layout.setSpacing(30)

        # Grupo de seleção de modo
        mode_group = QGroupBox("Modo de Inspeção")
        mode_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: 600;
                color: #374151;
                border: 2px solid #E5E7EB;
                border-radius: 12px;
                margin-top: 12px;
                padding-top: 20px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 8px 0 8px;
                background-color: #FFFFFF;
            }
        """)
        mode_group_layout = QVBoxLayout(mode_group)
        mode_group_layout.setSpacing(20)
        mode_group_layout.setContentsMargins(20, 20, 20, 20)

        # Cards container (dentro do grupo)
        cards_container = QWidget()
        cards_layout = QHBoxLayout(cards_container)
        cards_layout.setSpacing(20)
        cards_layout.setContentsMargins(0, 0, 0, 0)

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

        mode_group_layout.addWidget(cards_container)
        content_layout.addWidget(mode_group)

        # Botões
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)
        buttons_layout.addStretch()

        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setMinimumWidth(140)
        self.cancel_button.setMinimumHeight(44)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #6B7280;
                font-size: 13px;
                font-weight: 600;
                border: 2px solid #D1D5DB;
                border-radius: 8px;
                padding: 12px 24px;
            }
            QPushButton:hover {
                background-color: #F9FAFB;
                border: 2px solid #9CA3AF;
                color: #374151;
            }
            QPushButton:pressed {
                background-color: #F3F4F6;
            }
        """)
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)

        self.confirm_button = QPushButton("Confirmar Seleção")
        self.confirm_button.setMinimumWidth(160)
        self.confirm_button.setMinimumHeight(44)
        self.confirm_button.setEnabled(False)  # Desabilitado até selecionar
        self.confirm_button.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                font-size: 13px;
                font-weight: 600;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
            QPushButton:pressed {
                background-color: #1D4ED8;
            }
            QPushButton:disabled {
                background-color: #E5E7EB;
                color: #9CA3AF;
            }
        """)
        self.confirm_button.clicked.connect(self.on_confirm_clicked)
        buttons_layout.addWidget(self.confirm_button)

        content_layout.addLayout(buttons_layout)

        main_layout.addWidget(content_widget)

        # Layout final
        final_layout = QVBoxLayout(self)
        final_layout.setContentsMargins(0, 0, 0, 0)
        final_layout.addWidget(main_widget)

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
