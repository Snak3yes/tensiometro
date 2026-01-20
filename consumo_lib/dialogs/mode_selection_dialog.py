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

from consumo_lib.ui import COLORS, TYPO, SPACE, DIM

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
        self.icon_label.setStyleSheet(f"font-size: 32px; background-color: {COLORS.SURFACE}; border-radius: 28px; padding: {SPACE.SM}px;")
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
        title_label.setFont(TYPO.get_font(TYPO.HEADLINE_MEDIUM, bold=True))
        title_label.setWordWrap(True)
        title_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY};")
        content_layout.addWidget(title_label)

        # Descrição
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"color: {COLORS.TEXT_HINT}; {TYPO.BODY_SMALL}")
        content_layout.addWidget(desc_label)

        # Tempo estimado
        time_label = QLabel(time_estimate.replace("⏱️ ", ""))
        time_label.setFont(TYPO.get_font(TYPO.BODY_SMALL))
        time_label.setStyleSheet(f"""
            color: {COLORS.SUCCESS_DARK};
            background-color: {COLORS.SUCCESS_LIGHT};
            padding: {SPACE.XXS}px {SPACE.SM}px;
            border-radius: {DIM.RADIUS_SM}px;
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
            bg_color = COLORS.PRIMARY_LIGHT
            border_color = COLORS.PRIMARY
            border_width = "2px"
            icon_bg = COLORS.SECONDARY_LIGHT
        else:
            # Card normal: estilo neutro
            bg_color = COLORS.BACKGROUND
            border_color = COLORS.OUTLINE
            border_width = "1px"
            icon_bg = COLORS.SURFACE

        # Atualiza fundo do ícone
        if self.icon_label:
            self.icon_label.setStyleSheet(f"font-size: 32px; background-color: {icon_bg}; border-radius: 28px; padding: {SPACE.SM}px;")

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                border: {border_width} solid {border_color};
                border-radius: 12px;
            }}
            QWidget:hover {{
                background-color: {COLORS.SURFACE if not self.is_selected else COLORS.PRIMARY_LIGHT};
                border: 2px solid {COLORS.OUTLINE if not self.is_selected else COLORS.PRIMARY};
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
        header_widget.setStyleSheet(f"background-color: {COLORS.SURFACE}; border-bottom: 1px solid {COLORS.OUTLINE};")
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(40, 30, 40, 30)
        header_layout.setSpacing(12)

        # Título principal
        title_label = QLabel("Escolha o Modo de Inspeção")
        title_label.setFont(TYPO.get_font(TYPO.DISPLAY_SMALL, bold=True))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY};")
        header_layout.addWidget(title_label)

        # Subtítulo com código do stencil
        subtitle_label = QLabel(f"Stencil: {self.stencil_code}")
        subtitle_label.setFont(TYPO.get_font(TYPO.HEADLINE_MEDIUM))
        subtitle_label.setStyleSheet(f"color: {COLORS.TEXT_HINT};")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(subtitle_label)

        main_layout.addWidget(header_widget)

        # Container principal (fundo branco)
        content_widget = QWidget()
        content_widget.setStyleSheet(f"background-color: {COLORS.BACKGROUND};")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(40, 40, 40, 40)
        content_layout.setSpacing(30)

        # Grupo de seleção de modo
        mode_group = QGroupBox("Modo de Inspeção")
        mode_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: 14px;
                font-weight: 600;
                color: {COLORS.TEXT_HINT};
                border: 2px solid {COLORS.OUTLINE};
                border-radius: 12px;
                margin-top: 12px;
                padding-top: 20px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 {SPACE.SM}px 0 {SPACE.SM}px;
                background-color: {COLORS.BACKGROUND};
            }}
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
        self.cancel_button.setMinimumHeight(DIM.BUTTON_HEIGHT_LG)
        self.cancel_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.BACKGROUND};
                color: {COLORS.TEXT_HINT};
                font-size: 13px;
                font-weight: 600;
                border: 2px solid {COLORS.OUTLINE};
                border-radius: {DIM.RADIUS_MD}px;
                padding: {SPACE.SM}px {SPACE.LG}px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.SURFACE};
                border: 2px solid {COLORS.ON_OUTLINE};
                color: {COLORS.TEXT_HINT};
            }}
            QPushButton:pressed {{
                background-color: {COLORS.SURFACE_DARK};
            }}
        """)
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)

        self.confirm_button = QPushButton("Confirmar Seleção")
        self.confirm_button.setMinimumWidth(160)
        self.confirm_button.setMinimumHeight(DIM.BUTTON_HEIGHT_LG)
        self.confirm_button.setEnabled(False)  # Desabilitado até selecionar
        self.confirm_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.PRIMARY};
                color: white;
                font-size: 13px;
                font-weight: 600;
                border: none;
                border-radius: {DIM.RADIUS_MD}px;
                padding: {SPACE.SM}px {SPACE.LG}px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.PRIMARY_DARK};
            }}
            QPushButton:pressed {{
                background-color: {COLORS.PRIMARY_DARKER};
            }}
            QPushButton:disabled {{
                background-color: {COLORS.OUTLINE};
                color: {COLORS.ON_OUTLINE};
            }}
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
