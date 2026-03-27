"""
Widget Base Padrão para o Tensiometro

Fornece classes base com estilos consistentes para todos os componentes UI.

⚠️⚠️⚠️ REGRA CRÍTICA: PROIBIÇÃO DE ESTILOS INLINE/HARDCODED ⚠️⚠️⚠️

Este arquivo FORNECE COMPONENTES com estilos pré-aplicados do Design System.
❌ NUNCA use .setStyleSheet() ou valores hardcoded nestes componentes.
✅ SEMPRE use tokens: COLORS.*, TYPO.*, DIM.*, SPACE.*
✅ Se precisa de estilo novo, use widget_standards.py como modelo ou crie token em design_tokens.py.

Violations will be rejected in code review.

⚠️⚠️⚠️ FIM DA REGRA CRÍTICA ⚠️⚠️⚠️
"""

from PyQt6.QtWidgets import (
    QPushButton, QLabel, QLineEdit, QComboBox,
    QSpinBox, QDoubleSpinBox, QCheckBox, QGroupBox, QWidget
)
from PyQt6.QtCore import Qt

from .design_tokens import ColorPalette, Typography, Dimensions, Spacing, FontWeight, COLORS, TYPO, DIM, SPACE


class StandardButton(QPushButton):
    """
    Botão padrão com estilo consistente - Paleta Neutra v3.0

    Usage:
        >>> # NOVO (Recomendado - v1.1)
        >>> btn = StandardButton("Salvar", semantic_size="dialog-primary")
        >>> btn = StandardButton("Cancelar", semantic_size="dialog-secondary")
        >>> btn = StandardButton("Home", semantic_size="function-primary")
        >>>
        >>> # ANTIGO (Ainda funciona - backward compat)
        >>> btn = StandardButton("Salvar", size="lg")
        >>> btn = StandardButton("Configurar", size="md")
        >>> btn = StandardButton("OK", size="sm")

    Args:
        text: Texto do botão
        variant: primary-green | primary-blue | primary-orange | secondary | emergency | outline
        size: sm | md | lg (tamanho do botão) [DEPRECATED - Use semantic_size]
        semantic_size: Tamanho semântico baseado em contexto (NOVO v1.1)
        parent: Widget pai

    Variants (v3.0 - Paleta Neutra - Tons de Cinza):
        primary-green: Gradiente cinza escuro - ações de confirmação/início
        primary-blue: Gradiente cinza médio - ações padrão/genéricas
        primary-orange: Gradiente cinza mais escuro - ações de parada/atenção
        secondary: Outline transparente com borda cinza - ações alternativas/cancelamento
        emergency: Gradiente cinza muito escuro (uso raro 1%) - emergências físicas
        danger: [DEPRECATED] Use emergency instead
        outline: Borda cinza, fundo transparente [LEGADO - use secondary]

    Semantic Sizes (NOVO v1.1):
        Dialog Buttons:
            dialog-primary: 48×120px (Salvar, Confirmar, OK)
            dialog-secondary: 40×100px (Cancelar, Fechar)
            dialog-tertiary: 36×90px (Apply, Reset)
            emergency: 56×140px (STOP, Emergency)

        Movement Buttons:
            directional: 50×50px (↑, ↓, ←, →)
            z-axis: 50×35px (Z+, Z-)
            function-primary: 40×100px (Home, Zero, Go To)
            function-secondary: 40×90px (Step/Continuous)
            toggle-status: 44×44px (Backlight, Mode)

        Toolbar Buttons:
            toolbar-text: 36×120px (Anterior, Próximo)
            toolbar-icon: 40×40px (Refresh, Clear)
            toolbar-icon-large: 48×48px (New, Open, Save)

        Inline Buttons:
            inline-primary: 36px altura (Capturar, Calcular)
            inline-secondary: 32px altura (Limpar, Reset)
            inline-compact: 28px altura [CUIDADO: usar com moderação]

        Grid Buttons:
            grid-action: 44×80px (Edit, Delete, View) [WCAG compliant]
            grid-status: 24px altura (Badges clicáveis)

    Sizes (Legacy - mantido para backward compatibility):
        sm: (80, 32) - Botão pequeno
        md: (120, 40) - Botão médio (padrão)
        lg: (160, 48) - Botão grande

    Migration Notes (v1.0 → v1.1):
        - size="lg" → semantic_size="dialog-primary"
        - size="md" → semantic_size="dialog-secondary"
        - Use semantic_size para novos códigos (mais claro)
    """

    # Mapeamento de tamanhos semânticos para (altura, largura_min)
    # v4.0 - Microsoft Style - Compact & Clean
    SEMANTIC_SIZES = {
        # Dialog Buttons
        "dialog-primary": (28, 90),
        "dialog-secondary": (24, 80),
        "dialog-tertiary": (22, 70),
        "emergency": (32, 100),

        # Movement Buttons
        "directional": (32, 32),
        "z-axis": (24, 32),
        "function-primary": (26, 80),
        "function-secondary": (24, 70),
        "toggle-status": (28, 28),

        # Toolbar Buttons
        "toolbar-text": (24, 80),
        "toolbar-icon": (28, 28),
        "toolbar-icon-large": (32, 32),

        # Inline Buttons
        "inline-primary": (24, 60),
        "inline-secondary": (22, 55),
        "inline-compact": (20, 50),

        # Grid Buttons
        "grid-action": (28, 60),
        "grid-status": (20, 0),  # 0 = auto (largura ajusta ao conteúdo)
    }

    def __init__(self, text: str, variant: str = "primary-green", size: str = "md", semantic_size: str | None = None, parent=None):
        """
        Inicializa botão padrão

        Args:
            text: Texto do botão
            variant: Variant do botão (primary-green|primary-blue|primary-orange|secondary|emergency|outline)
            size: [DEPRECATED] Tamanho do botão (sm|md|lg)
            semantic_size: [NOVO v1.1] Tamanho semântico baseado em contexto
            parent: Widget pai
        """
        super().__init__(text, parent)

        # Emitir warning para variantes deprecated
        if variant == "primary":
            import warnings
            warnings.warn(
                'variant="primary" is deprecated. Use variant="primary-green" instead. '
                'Will be removed in v0.6.0',
                DeprecationWarning,
                stacklevel=2
            )
            variant = "primary-green"
        elif variant == "danger":
            import warnings
            warnings.warn(
                'variant="danger" is deprecated. Use variant="emergency" instead. '
                'Will be removed in v0.5.0',
                DeprecationWarning,
                stacklevel=2
            )
            variant = "emergency"

        # Aplicar fonte padrão
        font = TYPO.get_font(TYPO.BODY_LARGE, weight=FontWeight.MEDIUM)
        self.setFont(font)

        # Prioridade: semantic_size > size
        if semantic_size:
            if semantic_size not in self.SEMANTIC_SIZES:
                valid_sizes = list(self.SEMANTIC_SIZES.keys())
                raise ValueError(
                    f"semantic_size inválido: '{semantic_size}'\n"
                    f"Valores válidos: {valid_sizes}\n"
                    f"Veja documentação: docs/design_system/BUTTON_DIMENSIONS_PROPOSAL.md"
                )

            height, min_width = self.SEMANTIC_SIZES[semantic_size]

            # Aplicar dimensões
            self.setMinimumHeight(height)

            # Ajustes especiais para semantic_size específicos
            if semantic_size == "directional":
                # Botões direcionais são sempre quadrados
                self.setMaximumSize(height, height)

            elif semantic_size in ["toolbar-icon", "toolbar-icon-large", "toggle-status"]:
                # Botões quadrados
                self.setMaximumSize(height, height)

            elif semantic_size == "z-axis":
                # Z-axis tem formato retangular específico
                self.setMinimumSize(min_width, height)  # min_width=50, height=35
                self.setMaximumSize(height * 2, height)  # max_width=100, height=35

            else:
                # Largura padrão
                if min_width > 0:
                    self.setMinimumWidth(min_width)

        else:
            # Fallback para size (sm/md/lg) - BACKWARD COMPAT
            if size == "sm":
                width, height = DIM.BUTTON_SIZE_SM
            elif size == "lg":
                width, height = DIM.BUTTON_SIZE_LG
            else:  # md (default)
                width, height = DIM.BUTTON_SIZE_MD

            self.setMinimumSize(width, height)

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
