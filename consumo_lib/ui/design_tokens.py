"""
Design Tokens para o Tensiometro

Centraliza todas as constantes de design (cores, fontes, espaçamentos).
Este arquivo é a única fonte de verdade para estilos da aplicação.

Baseado no Material Design 3: https://m3.material.io/styles/color/the-color-system/tokens
"""

from dataclasses import dataclass
from PyQt6.QtGui import QFont, QColor


# =============================================================================
# PALETA DE CORES
# =============================================================================

@dataclass(frozen=True)
class ColorPalette:
    """
    Paleta de cores do Material Design 3

    Segue especificação: https://m3.material.io/styles/color/the-color-system/tokens

    Todas as cores são valores hexadecimais (ex: "#4CAF50") compatíveis com Qt.

    Atributos:
        PRIMARY: Cor primária para ações principais (verde)
        SECONDARY: Cor secundária para informações (azul)
        SUCCESS: Cor para estados de sucesso
        WARNING: Cor para avisos
        ERROR: Cor para erros
        STATUS_*: Cores específicas de status do domínio
    """

    # =========================================================================
    # PRIMARY COLORS (Verde - Success/Action)
    # =========================================================================

    PRIMARY: str = "#4CAF50"  # Green 500
    """Cor primária para ações principais e botões"""

    PRIMARY_DARK: str = "#388E3C"  # Green 700
    """Versão escura da cor primária (hover states)"""

    PRIMARY_LIGHT: str = "#81C784"  # Green 300
    """Versão clara da cor primária"""

    ON_PRIMARY: str = "#FFFFFF"  # White
    """Cor de texto/símbolos sobre cor primária"""

    # =========================================================================
    # SECONDARY COLORS (Azul - Information)
    # =========================================================================

    SECONDARY: str = "#2196F3"  # Blue 500
    """Cor secundária para informações e ações secundárias"""

    SECONDARY_DARK: str = "#1976D2"  # Blue 700
    """Versão escura da cor secundária"""

    SECONDARY_LIGHT: str = "#64B5F6"  # Blue 300
    """Versão clara da cor secundária"""

    ON_SECONDARY: str = "#FFFFFF"  # White
    """Cor de texto/símbolos sobre cor secundária"""

    # =========================================================================
    # SUCCESS COLORS
    # =========================================================================

    SUCCESS: str = "#2ecc71"  # Emerald
    """Cor para indicar sucesso (mais vibrante que PRIMARY)"""

    SUCCESS_DARK: str = "#27ae60"  # Emerald dark
    """Versão escura da cor de sucesso"""

    # =========================================================================
    # WARNING COLORS
    # =========================================================================

    WARNING: str = "#f1c40f"  # Yellow
    """Cor para avisos e atenção"""

    WARNING_DARK: str = "#f39c12"  # Orange
    """Versão escura da cor de aviso (mais urgente)"""

    WARNING_LIGHT: str = "#FFF9C4"  # Yellow light
    """Versão clara da cor de aviso (backgrounds)"""

    # =========================================================================
    # ERROR COLORS
    # =========================================================================

    ERROR: str = "#e74c3c"  # Red
    """Cor para erros e estados críticos"""

    ERROR_DARK: str = "#c0392b"  # Red dark
    """Versão escura da cor de erro"""

    ERROR_LIGHT: str = "#FFCDD2"  # Red light
    """Versão clara da cor de erro (backgrounds)"""

    # =========================================================================
    # STATUS COLORS (Domínio Específico - Inspeção)
    # =========================================================================

    STATUS_APPROVED_AUTO: str = "#4CAF50"  # Verde vibrante
    """Status: aprovado automaticamente (algoritmo)"""

    STATUS_APPROVED_USER: str = "#CDDC39"  # Verde-amarelo
    """Status: aprovado manualmente (usuário)"""

    STATUS_REJECTED: str = "#F44336"  # Vermelho
    """Status: reprovado/falha na inspeção"""

    STATUS_PENDING: str = "#9E9E9E"  # Cinza médio
    """Status: pendente (ainda não inspecionado)"""

    STATUS_IN_PROGRESS: str = "#2196F3"  # Azul
    """Status: em andamento (inspeção em curso)"""

    # =========================================================================
    # NEUTRAL COLORS (Texto, Background, Surface)
    # =========================================================================

    TEXT_PRIMARY: str = "#212121"  # Almost black
    """Cor de texto principal (alto contraste)"""

    TEXT_SECONDARY: str = "#757575"  # Medium gray
    """Cor de texto secundário (menos proeminente)"""

    TEXT_DISABLED: str = "#BDBDBD"  # Light gray
    """Cor de texto desabilitado"""

    TEXT_HINT: str = "#9E9E9E"  # Gray
    """Cor de hint/placeholder text"""

    BACKGROUND: str = "#FFFFFF"  # White
    """Cor de fundo principal da aplicação"""

    SURFACE: str = "#F5F5F5"  # Light gray
    """Cor de superfície (cards, panels)"""

    SURFACE_VARIANT: str = "#EEEEEE"  # Gray 100
    """Variante de cor de superfície"""

    # =========================================================================
    # BORDER COLORS
    # =========================================================================

    BORDER: str = "#E0E0E0"  # Gray 300
    """Cor de bordas padrão"""

    BORDER_DARK: str = "#BDBDBD"  # Gray 400
    """Cor de bordas escuras"""

    BORDER_FOCUS: str = "#2196F3"  # Blue
    """Cor de borda em estado de focus"""

    # =========================================================================
    # OVERLAY & SPECIAL COLORS
    # =========================================================================

    OVERLAY: str = "rgba(0, 0, 0, 0.5)"
    """Cor de overlay (semi-transparente)"""

    OVERLAY_DARK: str = "rgba(0, 0, 0, 0.7)"
    """Cor de overlay escura (mais opaca)"""

    SHADOW: str = "rgba(0, 0, 0, 0.1)"
    """Cor de sombra"""

    # =========================================================================
    # ENGINEERING-SPECIFIC COLORS (Visão Computacional)
    # =========================================================================

    OVERLAY_IMAGE: str = "#1e1e1e"  # Dark gray
    """Cor de overlay para imagens de visão computacional"""

    FIDUCIAL_FOUND: str = "#00ff00"  # Verde neon
    """Cor para marcar fiduciais encontrados (alta visibilidade)"""

    FIDUCIAL_NOT_FOUND: str = "#ff0000"  # Vermelho neon
    """Cor para marcar fiduciais não encontrados (alta visibilidade)"""

    GRID_LINES: str = "#E0E0E0"  # Gray 300
    """Cor de linhas de grade em visualizações"""

    # =========================================================================
    # ADDITIONAL UI COLORS
    # =========================================================================

    DIVIDER: str = "#E0E0E0"  # Gray 300
    """Cor de divisores/separadores"""

    ICON: str = "#757575"  # Medium gray
    """Cor padrão para ícones"""

    ICON_ACTIVE: str = "#212121"  # Almost black
    """Cor para ícones ativos/selecionados"""

    LINK: str = "#2196F3"  # Blue
    """Cor para links e texto clicável"""

    LINK_VISITED: str = "#9C27B0"  # Purple
    """Cor para links visitados"""

    # =========================================================================
    # MÉTODOS UTILITÁRIOS
    # =========================================================================

    def to_qcolor(self, color_hex: str) -> QColor:
        """
        Converte string hexadecimal para QColor

        Args:
            color_hex: Cor em formato hexadecimal (ex: "#4CAF50")

        Returns:
            Instância de QColor

        Raises:
            ValueError: Se formato for inválido

        Exemplo:
            >>> COLORS.to_qcolor(COLORS.PRIMARY)
            PyQt6.QtGui.QColor('#4CAF50')
        """
        if not color_hex.startswith("#"):
            raise ValueError(f"Cor deve começar com '#': {color_hex}")

        # Remover o '#' se presente
        hex_value = color_hex.lstrip("#")

        # Validar tamanho
        if len(hex_value) not in [6, 8]:
            raise ValueError(f"Cor HEX deve ter 6 ou 8 caracteres: {color_hex}")

        return QColor(f"#{hex_value}")

    def get_status_color(self, status: str) -> str:
        """
        Retorna cor para um status específico

        Args:
            status: Código do status (approved_auto, approved_user, rejected, etc.)

        Returns:
            Cor hexadecimal correspondente ao status

        Raises:
            ValueError: Se status for desconhecido

        Exemplo:
            >>> COLORS.get_status_color("approved_auto")
            '#4CAF50'
        """
        status_map = {
            "approved_auto": self.STATUS_APPROVED_AUTO,
            "approved_user": self.STATUS_APPROVED_USER,
            "rejected": self.STATUS_REJECTED,
            "pending": self.STATUS_PENDING,
            "in_progress": self.STATUS_IN_PROGRESS,
        }

        if status not in status_map:
            raise ValueError(f"Status desconhecido: {status}")

        return status_map[status]


# =============================================================================
# INSTÂNCIA SINGLETON
# =============================================================================

COLORS = ColorPalette()
"""
Instância singleton de ColorPalette

Uso:
    >>> from consumo_lib.ui.design_tokens import COLORS
    >>> COLORS.PRIMARY
    '#4CAF50'
    >>> COLORS.get_status_color("approved_auto")
    '#4CAF50'
"""


# =============================================================================
# TYPE SYSTEMS
# =============================================================================

@dataclass(frozen=True)
class Typography:
    """
    Sistema de tipografia com base no Material Design 3

    Escala de tipos: https://m3.material.io/styles/typography/type-scale-tokens

    Atributos:
        FONT_FAMILY: Fonte padrão (Arial - fallback seguro para Windows)
        FONT_FAMILY_MONOSPACE: Fonte monoespaçada (Consolas - para código)
    """

    # =========================================================================
    # FONT FAMILIES
    # =========================================================================

    FONT_FAMILY: str = "Arial"
    """Fonte padrão da aplicação (fallback seguro para Windows)"""

    FONT_FAMILY_MONOSPACE: str = "Consolas"
    """Fonte monoespaçada para código/técnicos"""

    # =========================================================================
    # TYPE SCALE (Material Design 3)
    # =========================================================================

    # Display Styles (Hero/Marketing)
    DISPLAY_LARGE: int = 57
    """Títulos hero (raro, usado em marketing)"""

    DISPLAY_MEDIUM: int = 45
    """Títulos de seção muito grandes"""

    DISPLAY_SMALL: int = 36
    """Subtítulos grandes"""

    # Headline Styles
    HEADLINE_LARGE: int = 32
    """Títulos principais (títulos de dialogs grandes)"""

    HEADLINE_MEDIUM: int = 28
    """Títulos de dialogs padrão"""

    HEADLINE_SMALL: int = 24
    """Títulos de seção"""

    # Title Styles
    TITLE_LARGE: int = 22
    """Títulos de blocos grandes"""

    TITLE_MEDIUM: int = 16
    """Títulos de widgets"""

    TITLE_SMALL: int = 14
    """Subtítulos"""

    # Body Styles
    BODY_LARGE: int = 16
    """Texto principal (botões, labels importantes)"""

    BODY_MEDIUM: int = 14
    """Texto padrão da aplicação"""

    BODY_SMALL: int = 12
    """Texto secundário"""

    # Label Styles
    LABEL_LARGE: int = 14
    """Labels de formulários importantes"""

    LABEL_MEDIUM: int = 12
    """Labels de formulários padrão"""

    LABEL_SMALL: int = 11
    """Captions, badges, texto pequeno"""

    # =========================================================================
    # FACTORY METHODS
    # =========================================================================

    def get_font(self, size: int, bold: bool = False, italic: bool = False) -> QFont:
        """
        Cria QFont com parâmetros padronizados

        Args:
            size: Tamanho da fonte em pontos
            bold: Se True, aplica negrito
            italic: Se True, aplica itálico

        Returns:
            QFont configurada

        Exemplo:
            >>> TYPO.get_font(14, bold=True)
            PyQt6.QtGui.QFont('Arial', 14, weight=75)
        """
        font = QFont(self.FONT_FAMILY, size)

        if bold:
            font.setBold(True)

        if italic:
            font.setItalic(True)

        return font

    # =========================================================================
    # CONVENIENCE METHODS
    # =========================================================================

    def display_large(self, bold: bool = True) -> QFont:
        """Font display large (57pt)"""
        return self.get_font(self.DISPLAY_LARGE, bold)

    def display_medium(self, bold: bool = True) -> QFont:
        """Font display medium (45pt)"""
        return self.get_font(self.DISPLAY_MEDIUM, bold)

    def display_small(self, bold: bool = True) -> QFont:
        """Font display small (36pt)"""
        return self.get_font(self.DISPLAY_SMALL, bold)

    def headline_large(self, bold: bool = True) -> QFont:
        """Font headline large (32pt)"""
        return self.get_font(self.HEADLINE_LARGE, bold)

    def headline_medium(self, bold: bool = True) -> QFont:
        """Font headline medium (28pt)"""
        return self.get_font(self.HEADLINE_MEDIUM, bold)

    def headline_small(self, bold: bool = True) -> QFont:
        """Font headline small (24pt)"""
        return self.get_font(self.HEADLINE_SMALL, bold)

    def title_large(self, bold: bool = True) -> QFont:
        """Font title large (22pt)"""
        return self.get_font(self.TITLE_LARGE, bold)

    def title_medium(self, bold: bool = True) -> QFont:
        """Font title medium (16pt)"""
        return self.get_font(self.TITLE_MEDIUM, bold)

    def title_small(self, bold: bool = True) -> QFont:
        """Font title small (14pt)"""
        return self.get_font(self.TITLE_SMALL, bold)

    def body_large(self, bold: bool = False) -> QFont:
        """Font body large (16pt)"""
        return self.get_font(self.BODY_LARGE, bold)

    def body_medium(self, bold: bool = False) -> QFont:
        """Font body medium (14pt) - padrão"""
        return self.get_font(self.BODY_MEDIUM, bold)

    def body_small(self, bold: bool = False) -> QFont:
        """Font body small (12pt)"""
        return self.get_font(self.BODY_SMALL, bold)

    def label_large(self, bold: bool = False) -> QFont:
        """Font label large (14pt)"""
        return self.get_font(self.LABEL_LARGE, bold)

    def label_medium(self, bold: bool = False) -> QFont:
        """Font label medium (12pt)"""
        return self.get_font(self.LABEL_MEDIUM, bold)

    def label_small(self, bold: bool = False) -> QFont:
        """Font label small (11pt)"""
        return self.get_font(self.LABEL_SMALL, bold)


# Instância singleton
TYPO = Typography()
"""
Instância singleton de Typography

Uso:
    >>> from consumo_lib.ui.design_tokens import TYPO
    >>> TYPO.BODY_MEDIUM
    14
    >>> TYPO.get_font(14, bold=True)
    PyQt6.QtGui.QFont('Arial', 14, weight=75)
"""


__all__ = [
    "ColorPalette",
    "COLORS",
    "Typography",
    "TYPO",
    "Spacing",
    "SPACE",
    "Dimensions",
    "DIM",
    "Elevation",
    "ELEV",
    "Opacity",
    "OPAC",
    "Transitions",
    "TRANS",
    "Breakpoints",
    "BREAK",
    "Accessibility",
    "A11Y",
]


# =============================================================================
# SPACING SYSTEM
# =============================================================================

@dataclass(frozen=True)
class Spacing:
    """
    Sistema de espaçamento em múltiplos de 4px (baseline grid)

    Baseado no sistema de grid de 4px do Material Design

    Todos os valores são múltiplos de 4px para manter consistência.
    """

    # Baseline
    ZERO: int = 0
    """Zero spacing (sem espaço)"""

    BASE: int = 4
    """Base da grid (4px) - unidade fundamental"""

    # Escala
    XS: int = 4
    """Extra Small (1x base) - Espaçamento mínimo"""

    SM: int = 8
    """Small (2x base) - Elements densamente relacionados"""

    MD: int = 16
    """Medium (4x base) - Espaçamento padrão"""

    LG: int = 24
    """Large (6x base) - Seções relacionadas"""

    XL: int = 32
    """Extra Large (8x base) - Seções distintas"""

    XXL: int = 48
    """Extra Extra Large (12x base) - Maior separação"""

    # Context-specific (tuples)
    PADDING_TIGHT: tuple = (XS, SM)
    """Padding apertado (vertical, horizontal) - (4px, 8px)"""

    PADDING_NORMAL: tuple = (SM, MD)
    """Padding normal (vertical, horizontal) - (8px, 16px)"""

    PADDING_SPACIOUS: tuple = (MD, LG)
    """Padding espaçoso (vertical, horizontal) - (16px, 24px)"""

    MARGIN_TIGHT: int = SM
    """Margin apertado - 8px"""

    MARGIN_NORMAL: int = MD
    """Margin normal - 16px"""

    MARGIN_SPACIOUS: int = LG
    """Margin espaçoso - 24px"""


# Instância singleton
SPACE = Spacing()
"""
Instância singleton de Spacing

Uso:
    >>> from consumo_lib.ui.design_tokens import SPACE
    >>> SPACE.MD
    16
    >>> widget.setContentsMargins(SPACE.MD, SPACE.MD, SPACE.MD, SPACE.MD)
"""


# =============================================================================
# DIMENSIONS SYSTEM
# =============================================================================

@dataclass(frozen=True)
class Dimensions:
    """
    Dimensões padrão para componentes e layouts

    Todos os valores seguem Material Design 3.
    """

    # =========================================================================
    # BORDER RADIUS
    # =========================================================================

    RADIUS_NONE: int = 0
    """Sem borda arredondada"""

    RADIUS_SM: int = 4
    """Border radius pequeno - Botões, cards pequenos"""

    RADIUS_MD: int = 8
    """Border radius médio - Cards, dialogs padrão"""

    RADIUS_LG: int = 12
    """Border radius grande - Cards grandes"""

    RADIUS_XL: int = 16
    """Border radius extra grande - Modals"""

    RADIUS_CIRCLE: int = 9999
    """Border radius circular - Para criar círculos"""

    # =========================================================================
    # ICON SIZES
    # =========================================================================

    ICON_XS: int = 16
    """Icone extra pequeno (16px)"""

    ICON_SM: int = 24
    """Icone pequeno (24px) - Tamanho padrão"""

    ICON_MD: int = 32
    """Icone médio (32px)"""

    ICON_LG: int = 48
    """Icone grande (48px)"""

    ICON_XL: int = 64
    """Icone extra grande (64px)"""

    # =========================================================================
    # BUTTON HEIGHTS
    # =========================================================================

    BUTTON_HEIGHT_SM: int = 32
    """Altura de botão pequeno"""

    BUTTON_HEIGHT_MD: int = 40
    """Altura de botão médio (padrão)"""

    BUTTON_HEIGHT_LG: int = 48
    """Altura de botão grande"""

    # =========================================================================
    # INPUT HEIGHTS
    # =========================================================================

    INPUT_HEIGHT_SM: int = 32
    """Altura de input pequeno"""

    INPUT_HEIGHT_MD: int = 40
    """Altura de input médio (padrão)"""

    INPUT_HEIGHT_LG: int = 48
    """Altura de input grande"""

    # =========================================================================
    # DIALOG SIZES
    # =========================================================================

    DIALOG_SMALL: tuple = (500, 400)
    """Tamanho de diálogo pequeno (largura, altura)"""

    DIALOG_MEDIUM: tuple = (700, 600)
    """Tamanho de diálogo médio (padrão)"""

    DIALOG_LARGE: tuple = (1000, 750)
    """Tamanho de diálogo grande"""

    DIALOG_XLARGE: tuple = (1400, 900)
    """Tamanho de diálogo extra grande (Engineering Wizard)"""

    # =========================================================================
    # WIDGET SIZES
    # =========================================================================

    BADGE_HEIGHT: int = 24
    """Altura de badge"""

    PROGRESS_BAR_HEIGHT: int = 8
    """Altura de barra de progresso"""

    SLIDER_THICKNESS: int = 4
    """Espessura de slider"""

    # =========================================================================
    # IMAGE PREVIEW SIZES
    # =========================================================================

    THUMBNAIL_SM: tuple = (100, 100)
    """Thumbnail pequeno"""

    THUMBNAIL_MD: tuple = (150, 150)
    """Thumbnail médio (padrão)"""

    THUMBNAIL_LG: tuple = (200, 200)
    """Thumbnail grande"""


# Instância singleton
DIM = Dimensions()
"""
Instância singleton de Dimensions

Uso:
    >>> from consumo_lib.ui.design_tokens import DIM
    >>> DIM.BUTTON_HEIGHT_MD
    40
    >>> btn.setMinimumHeight(DIM.BUTTON_HEIGHT_MD)
    >>> dialog.setFixedSize(*DIM.DIALOG_MEDIUM)
"""


# =============================================================================
# ELEVATION SYSTEM
# =============================================================================

@dataclass(frozen=True)
class Elevation:
    """
    Níveis de elevação (sombras/layering)

    Material Design 3 Elevation System
    """

    LEVEL_0: int = 0
    """Nível 0 - Superfície base (background)"""

    LEVEL_1: int = 1
    """Nível 1 - Componentes nivelados (botões, cards)"""

    LEVEL_2: int = 2
    """Nível 2 - Hover states"""

    LEVEL_3: int = 3
    """Nível 3 - Dropdowns, menus"""

    LEVEL_4: int = 4
    """Nível 4 - Dialogs, bottom sheets"""

    LEVEL_5: int = 5
    """Nível 5 - Modals, overlays"""


# Instância singleton
ELEV = Elevation()
"""
Instância singleton de Elevation

Uso:
    >>> from consumo_lib.ui.design_tokens import ELEV
    >>> ELEV.LEVEL_2
    2
"""


# =============================================================================
# OPACITY SYSTEM
# =============================================================================

@dataclass(frozen=True)
class Opacity:
    """
    Níveis de opacidade padronizados

    Valores de 0.0 a 1.0 (transparente a opaco)
    """

    DISABLED: float = 0.38
    """Componentes desabilitados (38%)"""

    HOVER: float = 0.08
    """Hover states (8%)"""

    FOCUS: float = 0.12
    """Focus states (12%)"""

    PRESSED: float = 0.20
    """Pressed states (20%)"""

    DRAG: float = 0.16
    """Drag states (16%)"""

    OVERLAY: float = 0.50
    """Overlays (50%)"""


# Instância singleton
OPAC = Opacity()
"""
Instância singleton de Opacity

Uso:
    >>> from consumo_lib.ui.design_tokens import OPAC
    >>> OPAC.DISABLED
    0.38
"""


# =============================================================================
# TRANSITIONS SYSTEM
# =============================================================================

@dataclass(frozen=True)
class Transitions:
    """
    Durações de transições padronizadas (em milissegundos)

    Baseado no Material Design Motion
    """

    INSTANT: int = 0
    """Transição instantânea"""

    FAST: int = 150
    """Transição rápida (150ms) - Hover states"""

    NORMAL: int = 250
    """Transição normal (250ms) - Diálogos, panels"""

    SLOW: int = 350
    """Transição lenta (350ms) - Complex animations"""

    VERY_SLOW: int = 500
    """Transição muito lenta (500ms) - Page transitions"""

    # Easing functions (para CSS)
    EASING_STANDARD: str = "cubic-bezier(0.4, 0.0, 0.2, 1)"
    """Easing padrão"""

    EASING_DECELERATE: str = "cubic-bezier(0.0, 0.0, 0.2, 1)"
    """Easing de desaceleração"""

    EASING_ACCELERATE: str = "cubic-bezier(0.4, 0.0, 1, 1)"
    """Easing de aceleração"""


# Instância singleton
TRANS = Transitions()
"""
Instância singleton de Transitions

Uso:
    >>> from consumo_lib.ui.design_tokens import TRANS
    >>> TRANS.NORMAL
    250
"""


# =============================================================================
# BREAKPOINTS SYSTEM
# =============================================================================

@dataclass(frozen=True)
class Breakpoints:
    """
    Breakpoints para layouts responsivos (em pixels)

    Para design responsivo futuro
    """

    XS: int = 600
    """Extra small devices (phones)"""

    SM: int = 960
    """Small devices (tablets)"""

    MD: int = 1280
    """Medium devices (laptops)"""

    LG: int = 1920
    """Large devices (desktops)"""

    XL: int = 2560
    """Extra large devices (4K monitors)"""


# Instância singleton
BREAK = Breakpoints()
"""
Instância singleton de Breakpoints

Uso:
    >>> from consumo_lib.ui.design_tokens import BREAK
    >>> BREAK.MD
    1280
"""


# =============================================================================
# ACCESSIBILITY SYSTEM
# =============================================================================

@dataclass(frozen=True)
class Accessibility:
    """
    Padrões de acessibilidade (WCAG 2.1 AA)
    """

    # Minimum contrast ratios
    CONTRAST_NORMAL: float = 4.5
    """Contraste mínimo para texto normal (WCAG 2.1 AA)"""

    CONTRAST_LARGE: float = 3.0
    """Contraste mínimo para texto grande (18pt+)"""

    CONTRAST_GRAPHICS: float = 3.0
    """Contraste mínimo para componentes gráficos"""

    # Focus indicators
    FOCUS_WIDTH: int = 2
    """Largura de indicador de focus (2px)"""

    FOCUS_OFFSET: int = 2
    """Offset de indicador de focus (2px)"""

    # Touch targets
    MINIMUM_TOUCH_SIZE: int = 44
    """Tamanho mínimo de toque (44×44px) - WCAG 2.5.5"""


# Instância singleton
A11Y = Accessibility()
"""
Instância singleton de Accessibility

Uso:
    >>> from consumo_lib.ui.design_tokens import A11Y
    >>> A11Y.MINIMUM_TOUCH_SIZE
    44
"""
