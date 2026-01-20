"""
Widget Base Padrão para o Tensiometro

Fornece classes base com estilos consistentes para todos os componentes UI.
"""

from PyQt6.QtWidgets import (
    QPushButton, QLabel, QLineEdit, QComboBox,
    QSpinBox, QDoubleSpinBox, QCheckBox, QGroupBox, QWidget
)
from PyQt6.QtCore import Qt
from .design_tokens import ColorPalette, Typography, Dimensions, Spacing, COLORS, TYPO, DIM, SPACE


class StandardButton(QPushButton):
    """
    Botão padrão com estilo consistente

    Usage:
        >>> btn = StandardButton("Salvar", variant="primary")
        >>> btn = StandardButton("Cancelar", variant="secondary")
        >>> btn = StandardButton("Excluir", variant="danger")

    Args:
        text: Texto do botão
        variant: primary | secondary | danger | outline
        parent: Widget pai

    Variants:
        primary: Cor verde (#4CAF50) - ações principais
        secondary: Cor azul (#2196F3) - ações secundárias
        danger: Cor vermelha (#F44336) - ações destrutivas
        outline: Borda verde, fundo transparente - ações terciárias
    """

    def __init__(self, text: str, variant: str = "primary", parent=None):
        """
        Inicializa botão padrão

        Args:
            text: Texto do botão
            variant: Variant do botão (primary|secondary|danger|outline)
            parent: Widget pai
        """
        super().__init__(text, parent)

        # Aplicar fonte padrão
        font = TYPO.get_font(TYPO.BODY_LARGE, bold=True)
        self.setFont(font)

        # Aplicar tamanho padrão
        self.setMinimumHeight(DIM.BUTTON_HEIGHT_MD)

        # Aplicar variante via property (para stylesheet)
        self.setProperty("variant", variant)


class StandardLabel(QLabel):
    """
    Label padrão com variantes

    Usage:
        >>> lbl_title = StandardLabel("Título", variant="heading")
        >>> lbl_body = StandardLabel("Texto normal")
        >>> lbl_caption = StandardLabel("Caption", variant="caption")

    Args:
        text: Texto da label
        variant: heading | subheading | body | caption
        parent: Widget pai

    Variants:
        heading: Título de seção (16pt, bold)
        subheading: Subtítulo (14pt, bold, gray)
        body: Texto padrão (14pt, normal)
        caption: Caption/pequeno (11pt, gray)
    """

    def __init__(self, text: str, variant: str = "body", parent=None):
        """
        Inicializa label padrão

        Args:
            text: Texto da label
            variant: Variant da label
            parent: Widget pai
        """
        super().__init__(text, parent)

        if variant == "heading":
            font = TYPO.get_font(TYPO.TITLE_MEDIUM, bold=True)
            self.setProperty("heading", True)
        elif variant == "subheading":
            font = TYPO.get_font(TYPO.BODY_LARGE, bold=True)
            self.setProperty("subheading", True)
        elif variant == "caption":
            font = TYPO.get_font(TYPO.LABEL_SMALL)
            self.setProperty("caption", True)
        else:  # body (default)
            font = TYPO.get_font(TYPO.BODY_MEDIUM)

        self.setFont(font)


class StandardInput(QLineEdit):
    """
    Input padrão com estilo consistente

    Usage:
        >>> input = StandardInput(placeholder="Digite seu nome")

    Args:
        placeholder: Texto de placeholder
        parent: Widget pai
    """

    def __init__(self, placeholder: str = "", parent=None):
        """
        Inicializa input padrão

        Args:
            placeholder: Texto de placeholder
            parent: Widget pai
        """
        super().__init__(parent)
        if placeholder:
            self.setPlaceholderText(placeholder)
        self.setMinimumHeight(Dimensions.INPUT_HEIGHT_MD)


class StandardSpinBox(QSpinBox):
    """
    SpinBox padrão com estilo consistente

    Usage:
        >>> spinbox = StandardSpinBox()
        >>> spinbox.setRange(0, 100)

    Args:
        parent: Widget pai
    """

    def __init__(self, parent=None):
        """
        Inicializa spinbox padrão

        Args:
            parent: Widget pai
        """
        super().__init__(parent)
        self.setMinimumHeight(Dimensions.INPUT_HEIGHT_MD)


class StandardDoubleSpinBox(QDoubleSpinBox):
    """
    DoubleSpinBox padrão com estilo consistente

    Usage:
        >>> spinbox = StandardDoubleSpinBox()
        >>> spinbox.setRange(0.0, 100.0)
        >>> spinbox.setDecimals(2)

    Args:
        parent: Widget pai
    """

    def __init__(self, parent=None):
        """
        Inicializa double spinbox padrão

        Args:
            parent: Widget pai
        """
        super().__init__(parent)
        self.setMinimumHeight(Dimensions.INPUT_HEIGHT_MD)


class StandardComboBox(QComboBox):
    """
    ComboBox padrão com estilo consistente

    Usage:
        >>> combobox = StandardComboBox()
        >>> combobox.addItem("Opção 1")
        >>> combobox.addItem("Opção 2")

    Args:
        parent: Widget pai
    """

    def __init__(self, parent=None):
        """
        Inicializa combobox padrão

        Args:
            parent: Widget pai
        """
        super().__init__(parent)
        self.setMinimumHeight(Dimensions.INPUT_HEIGHT_MD)


class StandardGroupBox(QGroupBox):
    """
    GroupBox padrão com espaçamento consistente

    Usage:
        >>> groupbox = StandardGroupBox("Título")
        >>> layout = groupbox.layout()
        >>> layout.setSpacing(Spacing.MD)

    Args:
        title: Título do groupbox
        parent: Widget pai
    """

    def __init__(self, title: str, parent=None):
        """
        Inicializa groupbox padrão

        Args:
            title: Título do groupbox
            parent: Widget pai
        """
        super().__init__(title, parent)
        # Espaçamento interno padronizado
        self.layout().setSpacing(Spacing.MD)


__all__ = [
    "StandardButton",
    "StandardLabel",
    "StandardInput",
    "StandardSpinBox",
    "StandardDoubleSpinBox",
    "StandardComboBox",
    "StandardGroupBox",
]
