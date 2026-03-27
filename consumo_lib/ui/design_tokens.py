"""
Design Tokens para o Tensiometro

Centraliza todas as constantes de design (cores, fontes, espaçamentos).
Este arquivo é a única fonte de verdade para estilos da aplicação.

Baseado no Material Design 3: https://m3.material.io/styles/color/the-color-system/tokens

Theme Support:
    - Este arquivo agora suporta múltiplos temas (light, dark, system)
    - Use COLORS dinâmico que carrega a paleta do tema atual
    - Para mudar tema: use ThemeManager.set_theme("dark")

⚠️⚠️⚠️ REGRA CRÍTICA: PROIBIÇÃO DE ESTILOS INLINE/HARDCODED ⚠️⚠️⚠️

ESTE ARQUIVO É A ÚNICA FONTE DE VERDADE PARA ESTILOS.

❌ COMPLETAMENTE PROIBIDO em qualquer lugar da aplicação:
   - Estilo inline (.setStyleSheet)
   - Estilo local (definir styles em arquivos Python)
   - Estilo hardcoded (valores mágicos como "#4CAF50", setMinimumHeight(45))
   - Estilo mágico (números sem contexto ou semântica clara)

✅ SEMPRE USE TOKENS DESTE ARQUIVO:
   - COLORS.* (cores)
   - TYPO.* (fontes e pesos)
   - DIM.* (dimensões)
   - SPACE.* (espaçamentos)

Se precisa de estilo novo, adicione AQUI e documente.
Violations will be rejected in code review.

⚠️⚠️⚠️ FIM DA REGRA CRÍTICA ⚠️⚠️⚠️
"""

from dataclasses import dataclass
from typing import Optional
from PyQt6.QtGui import QFont, QColor
import logging

logger = logging.getLogger(__name__)

# Importar sistema de temas
from consumo_lib.ui.themes import (
    ThemeType,
    LightThemePalette,
    DarkThemePalette,
    ThemePaletteFactory
)


# =============================================================================
# PALETA DE CORES DINÂMICA (Theme-Aware)
# =============================================================================

class ColorPalette:
    """
    Wrapper dinâmico para paleta de cores do tema atual

    Esta classe atua como um proxy para a paleta do tema ativo.
    Quando o tema muda, todas as cores são atualizadas automaticamente.

    A paleta atual é gerenciada por ThemeManager.
    Esta classe fornece acesso compatível com código legado.

    Usage:
        >>> from consumo_lib.ui.design_tokens import COLORS
        >>> COLORS.PRIMARY  # Retorna cor do tema atual
        '#4CAF50'  # ou '#66BB6A' no dark mode

    Theme Management:
        >>> from consumo_lib.ui.theme_manager import get_theme_manager
        >>> mgr = get_theme_manager()
        >>> mgr.set_theme("dark")  # COLORS atualiza automaticamente
    """

    def __init__(self, theme: ThemeType = "light"):
        """
        Inicializa paleta com tema específico

        Args:
            theme: Nome do tema ("light" | "dark" | "system")
        """
        self._theme = theme
        self._palette = ThemePaletteFactory.create_palette(theme)

    def _update_palette(self, theme: ThemeType):
        """
        Atualiza paleta para novo tema (chamado pelo ThemeManager)

        Args:
            theme: Novo tema a ser aplicado
        """
        self._theme = theme
        self._palette = ThemePaletteFactory.create_palette(theme)
        logger.info(f"ColorPalette atualizada para tema: {theme}")

    # =========================================================================
    # PRIMARY COLORS (Verde - Success/Action)
    # =========================================================================

    @property
    def PRIMARY(self) -> str:
        """Cor primária para ações principais e botões"""
        return self._palette.PRIMARY

    @property
    def PRIMARY_DARK(self) -> str:
        """Versão escura da cor primária (hover states)"""
        return self._palette.PRIMARY_DARK

    @property
    def PRIMARY_LIGHT(self) -> str:
        """Versão clara da cor primária"""
        return self._palette.PRIMARY_LIGHT

    @property
    def ON_PRIMARY(self) -> str:
        """Cor de texto/símbolos sobre cor primária"""
        return self._palette.ON_PRIMARY

    @property
    def ON_PRIMARY_DARK(self) -> str:
        """Variação escura de ON_PRIMARY"""
        return self._palette.ON_PRIMARY_DARK

    # =========================================================================
    # SECONDARY COLORS (Azul - Information)
    # =========================================================================

    @property
    def SECONDARY(self) -> str:
        """Cor secundária para informações e ações secundárias"""
        return self._palette.SECONDARY

    @property
    def SECONDARY_DARK(self) -> str:
        """Versão escura da cor secundária"""
        return self._palette.SECONDARY_DARK

    @property
    def SECONDARY_LIGHT(self) -> str:
        """Versão clara da cor secundária"""
        return self._palette.SECONDARY_LIGHT

    @property
    def ON_SECONDARY(self) -> str:
        """Cor de texto/símbolos sobre cor secundária"""
        return self._palette.ON_SECONDARY

    # =========================================================================
    # SUCCESS COLORS
    # =========================================================================

    @property
    def SUCCESS(self) -> str:
        """Cor para indicar sucesso (mais vibrante que PRIMARY)"""
        return self._palette.SUCCESS

    @property
    def SUCCESS_DARK(self) -> str:
        """Versão escura da cor de sucesso"""
        return self._palette.SUCCESS_DARK

    # =========================================================================
    # WARNING COLORS
    # =========================================================================

    @property
    def WARNING(self) -> str:
        """Cor para avisos e atenção"""
        return self._palette.WARNING

    @property
    def WARNING_DARK(self) -> str:
        """Versão escura da cor de aviso (mais urgente)"""
        return self._palette.WARNING_DARK

    @property
    def WARNING_LIGHT(self) -> str:
        """Versão clara da cor de aviso (backgrounds)"""
        return self._palette.WARNING_LIGHT

    # =========================================================================
    # ERROR COLORS
    # =========================================================================

    @property
    def ERROR(self) -> str:
        """Cor para erros e estados críticos"""
        return self._palette.ERROR

    @property
    def ERROR_DARK(self) -> str:
        """Versão escura da cor de erro"""
        return self._palette.ERROR_DARK

    @property
    def ERROR_LIGHT(self) -> str:
        """Versão clara da cor de erro (backgrounds)"""
        return self._palette.ERROR_LIGHT

    # =========================================================================
    # STATUS COLORS (Domínio Específico - Inspeção)
    # =========================================================================

    @property
    def STATUS_APPROVED_AUTO(self) -> str:
        """Status: aprovado automaticamente (algoritmo)"""
        return self._palette.STATUS_APPROVED_AUTO

    @property
    def STATUS_APPROVED_USER(self) -> str:
        """Status: aprovado manualmente (usuário)"""
        return self._palette.STATUS_APPROVED_USER

    @property
    def STATUS_REJECTED(self) -> str:
        """Status: reprovado/falha na inspeção"""
        return self._palette.STATUS_REJECTED

    @property
    def STATUS_PENDING(self) -> str:
        """Status: pendente (ainda não inspecionado)"""
        return self._palette.STATUS_PENDING

    @property
    def STATUS_IN_PROGRESS(self) -> str:
        """Status: em andamento (inspeção em curso)"""
        return self._palette.STATUS_IN_PROGRESS

    # =========================================================================
    # NEUTRAL COLORS (Texto, Background, Surface)
    # =========================================================================

    @property
    def TEXT_PRIMARY(self) -> str:
        """Cor de texto principal (alto contraste)"""
        return self._palette.TEXT_PRIMARY

    @property
    def TEXT_PRIMARY_DARK(self) -> str:
        """Variação escura de TEXT_PRIMARY"""
        return self._palette.TEXT_PRIMARY_DARK

    @property
    def TEXT_PRIMARY_VARIANT(self) -> str:
        """Variação de TEXT_PRIMARY"""
        return self._palette.TEXT_PRIMARY_VARIANT

    @property
    def TEXT_SECONDARY(self) -> str:
        """Cor de texto secundário (menos proeminente)"""
        return self._palette.TEXT_SECONDARY

    @property
    def TEXT_DISABLED(self) -> str:
        """Cor de texto desabilitado"""
        return self._palette.TEXT_DISABLED

    @property
    def TEXT_HINT(self) -> str:
        """Cor de hint/placeholder text"""
        return self._palette.TEXT_HINT

    @property
    def BACKGROUND(self) -> str:
        """Cor de fundo principal da aplicação"""
        return self._palette.BACKGROUND

    @property
    def SURFACE(self) -> str:
        """Cor de superfície (cards, panels)"""
        return self._palette.SURFACE

    @property
    def SURFACE_VARIANT(self) -> str:
        """Variante de cor de superfície"""
        return self._palette.SURFACE_VARIANT

    # =========================================================================
    # BORDER COLORS
    # =========================================================================

    @property
    def BORDER(self) -> str:
        """Cor de bordas padrão"""
        return self._palette.BORDER

    @property
    def BORDER_DARK(self) -> str:
        """Cor de bordas escuras"""
        return self._palette.BORDER_DARK

    @property
    def BORDER_VARIANT(self) -> str:
        """Variação de cor de borda"""
        return self._palette.BORDER_VARIANT

    @property
    def BORDER_FOCUS(self) -> str:
        """Cor de borda em estado de focus"""
        return self._palette.BORDER_FOCUS

    # =========================================================================
    # OVERLAY & SPECIAL COLORS
    # =========================================================================

    @property
    def OVERLAY(self) -> str:
        """Cor de overlay (semi-transparente)"""
        return self._palette.OVERLAY

    @property
    def OVERLAY_DARK(self) -> str:
        """Cor de overlay escura (mais opaca)"""
        return self._palette.OVERLAY_DARK

    @property
    def SHADOW(self) -> str:
        """Cor de sombra"""
        return self._palette.SHADOW

    # =========================================================================
    # ENGINEERING-SPECIFIC COLORS (Visão Computacional)
    # =========================================================================

    @property
    def OVERLAY_IMAGE(self) -> str:
        """Cor de overlay para imagens de visão computacional"""
        return self._palette.OVERLAY_IMAGE

    @property
    def FIDUCIAL_FOUND(self) -> str:
        """Cor para marcar fiduciais encontrados (alta visibilidade)"""
        return self._palette.FIDUCIAL_FOUND

    @property
    def FIDUCIAL_NOT_FOUND(self) -> str:
        """Cor para marcar fiduciais não encontrados (alta visibilidade)"""
        return self._palette.FIDUCIAL_NOT_FOUND

    @property
    def GRID_LINES(self) -> str:
        """Cor de linhas de grade em visualizações"""
        return self._palette.GRID_LINES

    # =========================================================================
    # ADDITIONAL UI COLORS
    # =========================================================================

    @property
    def DIVIDER(self) -> str:
        """Cor de divisores/separadores"""
        return self._palette.DIVIDER

    @property
    def ICON(self) -> str:
        """Cor padrão para ícones"""
        return self._palette.ICON

    @property
    def ICON_ACTIVE(self) -> str:
        """Cor para ícones ativos/selecionados"""
        return self._palette.ICON_ACTIVE

    @property
    def LINK(self) -> str:
        """Cor para links e texto clicável"""
        return self._palette.LINK

    @property
    def LINK_VISITED(self) -> str:
        """Cor para links visitados"""
        return self._palette.LINK_VISITED

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
            '#4CAF50'  # light
            '#66BB6A'  # dark
        """
        from consumo_lib.ui.themes import get_status_color
        return get_status_color(self._palette, status)


# =============================================================================
# INSTÂNCIA SINGLETON (Compatibilidade com código legado)
# =============================================================================

# Instância global de ColorPalette (será gerenciada pelo ThemeManager)
_COLOR_PALETTE_INSTANCE: Optional[ColorPalette] = None


def get_color_palette() -> ColorPalette:
    """
    Retorna instância singleton de ColorPalette

    Returns:
        Instância de ColorPalette do tema atual

    Raises:
        RuntimeError: Se ColorPalette não foi inicializada

    Note:
        A paleta é inicializada pelo ThemeManager em init_theme_manager().
        Aplicações devem usar get_theme_manager() para obter o gerenciador.

    Example:
        >>> from consumo_lib.ui.design_tokens import get_color_palette
        >>> colors = get_color_palette()
        >>> colors.PRIMARY
        '#4CAF50'
    """
    global _COLOR_PALETTE_INSTANCE

    if _COLOR_PALETTE_INSTANCE is None:
        # Fallback: criar instância padrão com tema light
        logger.warning("ColorPalette não foi inicializada pelo ThemeManager, usando light theme")
        _COLOR_PALETTE_INSTANCE = ColorPalette(theme="light")

    return _COLOR_PALETTE_INSTANCE


# Criar wrapper para compatibilidade com código existente
class _ColorPaletteProxy:
    """
    Proxy para compatibilidade com código legado que importa COLORS diretamente

    Este proxy permite que código existente continue funcionando:
        from consumo_lib.ui.design_tokens import COLORS
        btn.setStyleSheet(f"background-color: {COLORS.PRIMARY}")

    Quando o tema muda via ThemeManager.set_theme(), COLORS atualiza automaticamente.
    """

    def __getattr__(self, name: str):
        """
        Proxy para atributos da paleta atual

        Args:
            name: Nome do atributo (PRIMARY, BACKGROUND, etc.)

        Returns:
            Valor do atributo da paleta do tema atual
        """
        palette = get_color_palette()
        return getattr(palette, name)

    def __setattr__(self, name: str, _value):
        """
        Previne atribuições diretas (paleta é read-only via ThemeManager)

        Args:
            name: Nome do atributo
            _value: Valor a ser atribuído (ignorado)

        Raises:
            AttributeError: Sempre previne atribuição direta
        """
        raise AttributeError(
            f"Cannot assign to COLORS.{name}. "
            f"Use ThemeManager.set_theme() to change theme."
        )


COLORS = _ColorPaletteProxy()
"""
Instância proxy de ColorPalette para compatibilidade com código legado

Uso:
    >>> from consumo_lib.ui.design_tokens import COLORS
    >>> COLORS.PRIMARY
    '#4CAF50'  # light theme
    >>>
    >>> # Quando tema muda para dark:
    >>> COLORS.PRIMARY
    '#66BB6A'  # dark theme (atualizado automaticamente)

Theme Management:
    >>> from consumo_lib.ui.theme_manager import get_theme_manager
    >>> mgr = get_theme_manager()
    >>> mgr.set_theme("dark")  # COLORS atualiza automaticamente
"""


# =============================================================================
# TYPE SYSTEMS
# =============================================================================

class FontWeight(int):
    """
    Pesos de fonte conforme TYPOGRAPHY_GUIDE.md

    Segue especificação Material Design 3 para pesos de fonte.

    Usage Frequencies:
        LIGHT (300): 5% - Raramente usado
        NORMAL (400): 70% - Texto padrão, labels, instruções
        MEDIUM (500): 20% - Títulos de seção, botões, headings
        SEMIBOLD (600): 4% - Títulos principais, dialogs
        BOLD (700): 1% - Emergências, alertas críticos

    Usage:
        >>> from consumo_lib.ui.design_tokens import FontWeight
        >>> TYPO.get_font(14, weight=FontWeight.MEDIUM)
        PyQt6.QtGui.QFont('Arial', 14, weight=500)

    Migration from bold boolean:
        >>> # Old way (deprecated but still works)
        >>> TYPO.get_font(14, bold=True)  # weight=700
        >>> # New way (recommended)
        >>> TYPO.get_font(14, weight=FontWeight.BOLD)
    """

    LIGHT: int = 300
    """Light (300) - Uso raro (5%)"""

    NORMAL: int = 400
    """Normal (400) - Texto padrão (70%)"""

    MEDIUM: int = 500
    """Medium (500) - Títulos de seção, botões (20%)"""

    SEMIBOLD: int = 600
    """Semibold (600) - Títulos principais (4%)"""

    BOLD: int = 700
    """Bold (700) - Emergências, alertas críticos (1%)"""


@dataclass(frozen=True)
class Typography:
    """
    Sistema de tipografia com base no Material Design 3

    Escala de tipos: https://m3.material.io/styles/typography/type-scale-tokens

    Atributos:
        FONT_FAMILY: Fonte padrão (Segoe UI - moderna do Windows)
        FONT_FAMILY_MONOSPACE: Fonte monoespaçada (Consolas - para código)
    """

    # =========================================================================
    # FONT FAMILIES
    # =========================================================================

    FONT_FAMILY: str = "Segoe UI"
    """Fonte padrão da aplicação (moderna do Windows, fallback: Arial, Helvetica)"""

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

    def get_font(
        self,
        size: int,
        weight: int | None = None,
        bold: bool | None = None,
        italic: bool = False
    ) -> QFont:
        """
        Cria QFont com parâmetros padronizados

        Args:
            size: Tamanho da fonte em pontos
            weight: Peso da fonte (FontWeight.LIGHT=300, NORMAL=400, MEDIUM=500, SEMIBOLD=600, BOLD=700)
            bold: [DEPRECATED] Se True, aplica negrito (weight=700). Use weight parameter instead.
            italic: Se True, aplica itálico

        Returns:
            QFont configurada

        Examples:
            >>> # New way (recommended)
            >>> from consumo_lib.ui.design_tokens import FontWeight
            >>> TYPO.get_font(14, weight=FontWeight.MEDIUM)
            PyQt6.QtGui.QFont('Arial', 14, weight=500)

            >>> # Old way (deprecated but still works)
            >>> TYPO.get_font(14, bold=True)  # weight=700

            >>> # With italic
            >>> TYPO.get_font(14, weight=FontWeight.SEMIBOLD, italic=True)

        Migration Notes:
            - bold=True → weight=FontWeight.BOLD (700)
            - bold=False → weight=None (usa default 400)
        """
        # Backward compatibility: migrar bold → weight
        if bold is not None:
            import warnings
            warnings.warn(
                'bold parameter is deprecated. Use weight=FontWeight.BOLD instead. '
                'Will be removed in v0.6.0',
                DeprecationWarning,
                stacklevel=2
            )
            if bold and weight is None:
                weight = FontWeight.BOLD

        # Default weight se não especificado
        if weight is None:
            weight = FontWeight.NORMAL

        font = QFont(self.FONT_FAMILY, size)
        font.setWeight(weight)

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

    # =========================================================================
    # FONT WEIGHT CONVENIENCE METHODS
    # =========================================================================

    def light(self, size: int) -> QFont:
        """
        Font com peso LIGHT (300)

        Args:
            size: Tamanho da fonte em pontos

        Returns:
            QFont com peso 300

        Usage:
            >>> TYPO.light(14)
            PyQt6.QtGui.QFont('Arial', 14, weight=300)
        """
        return self.get_font(size, weight=FontWeight.LIGHT)

    def normal(self, size: int) -> QFont:
        """
        Font com peso NORMAL (400) - peso padrão

        Args:
            size: Tamanho da fonte em pontos

        Returns:
            QFont com peso 400

        Usage:
            >>> TYPO.normal(14)
            PyQt6.QtGui.QFont('Arial', 14, weight=400)
        """
        return self.get_font(size, weight=FontWeight.NORMAL)

    def medium(self, size: int) -> QFont:
        """
        Font com peso MEDIUM (500) - para títulos de seção, botões

        Args:
            size: Tamanho da fonte em pontos

        Returns:
            QFont com peso 500

        Usage:
            >>> TYPO.medium(14)
            PyQt6.QtGui.QFont('Arial', 14, weight=500)
        """
        return self.get_font(size, weight=FontWeight.MEDIUM)

    def semibold(self, size: int) -> QFont:
        """
        Font com peso SEMIBOLD (600) - para títulos principais, dialogs

        Args:
            size: Tamanho da fonte em pontos

        Returns:
            QFont com peso 600

        Usage:
            >>> TYPO.semibold(14)
            PyQt6.QtGui.QFont('Arial', 14, weight=600)
        """
        return self.get_font(size, weight=FontWeight.SEMIBOLD)

    def bold(self, size: int) -> QFont:
        """
        Font com peso BOLD (700) - para emergências, alertas críticos

        Args:
            size: Tamanho da fonte em pontos

        Returns:
            QFont com peso 700

        Usage:
            >>> TYPO.bold(14)
            PyQt6.QtGui.QFont('Arial', 14, weight=700)
        """
        return self.get_font(size, weight=FontWeight.BOLD)


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
    "FontWeight",
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
    # BUTTON HEIGHTS (Genéricos - BACKWARD COMPAT)
    # =========================================================================

    BUTTON_HEIGHT_SM: int = 22
    """Altura de botão pequeno"""

    BUTTON_HEIGHT_MD: int = 26
    """Altura de botão médio (padrão)"""

    BUTTON_HEIGHT_LG: int = 32
    """Altura de botão grande"""

    # =========================================================================
    # BUTTON SIZES (width, height tuples)
    # =========================================================================

    BUTTON_SIZE_SM: tuple = (60, 22)
    """Tamanho de botão pequeno (largura, altura)"""

    BUTTON_SIZE_MD: tuple = (80, 26)
    """Tamanho de botão médio (largura, altura) - padrão"""

    BUTTON_SIZE_LG: tuple = (100, 32)
    """Tamanho de botão grande (largura, altura)"""

    # =========================================================================
    # SEMANTIC BUTTON SIZES (v4.0 - Microsoft Style - Compact & Clean)
    # =========================================================================
    # Nota: Dimensões otimizadas para visual profissional estilo Microsoft.
    # Abandona WCAG 44px mínimo em favor de estética mais limpa.

    # --------------------------------------------------------------------------
    # DIALOG BUTTONS (Botões de caixas de diálogo)
    # --------------------------------------------------------------------------

    BUTTON_DIALOG_PRIMARY_HEIGHT: int = 28
    """Altura de botão primário em dialogs (Salvar, Confirmar, OK)"""
    BUTTON_DIALOG_PRIMARY_MIN_WIDTH: int = 90
    """Largura mínima de botão primário em dialogs"""

    BUTTON_DIALOG_SECONDARY_HEIGHT: int = 24
    """Altura de botão secundário em dialogs (Cancelar, Fechar)"""
    BUTTON_DIALOG_SECONDARY_MIN_WIDTH: int = 80
    """Largura mínima de botão secundário em dialogs"""

    BUTTON_DIALOG_TERTIARY_HEIGHT: int = 22
    """Altura de botão terciário em dialogs (Apply, Reset)"""
    BUTTON_DIALOG_TERTIARY_MIN_WIDTH: int = 70
    """Largura mínima de botão terciário em dialogs"""

    BUTTON_EMERGENCY_HEIGHT: int = 32
    """Altura de botão de emergência (prominente)"""
    BUTTON_EMERGENCY_MIN_WIDTH: int = 100
    """Largura mínima de botão de emergência"""
    BUTTON_EMERGENCY_PADDING: tuple = (8, 24)
    """Padding vertical/horizontal de botão de emergência"""

    # --------------------------------------------------------------------------
    # MOVEMENT CONTROL BUTTONS (Botões de controle de movimento CNC)
    # --------------------------------------------------------------------------

    BUTTON_DIRECTIONAL_SIZE: int = 32
    """Tamanho de botão direcional (quadrado - ↑↓←→)"""

    BUTTON_Z_AXIS_WIDTH: int = 32
    """Largura de botão de eixo Z"""
    BUTTON_Z_AXIS_HEIGHT: int = 24
    """Altura de botão de eixo Z"""

    BUTTON_FUNCTION_PRIMARY_HEIGHT: int = 26
    """Altura de botão de função primária (Home, Zero, Go To)"""
    BUTTON_FUNCTION_PRIMARY_MIN_WIDTH: int = 80
    """Largura mínima de botão de função primária"""

    BUTTON_FUNCTION_SECONDARY_HEIGHT: int = 24
    """Altura de botão de função secundária (Step/Continuous, Toggle)"""
    BUTTON_FUNCTION_SECONDARY_MIN_WIDTH: int = 70
    """Largura mínima de botão de função secundária"""

    BUTTON_TOGGLE_STATUS_SIZE: int = 28
    """Tamanho de botão toggle de status (quadrado)"""

    # --------------------------------------------------------------------------
    # TOOLBAR BUTTONS (Botões de barras de ferramentas)
    # --------------------------------------------------------------------------

    BUTTON_TOOLBAR_TEXT_HEIGHT: int = 24
    """Altura de botão de toolbar com texto (Anterior, Próximo)"""
    BUTTON_TOOLBAR_TEXT_MIN_WIDTH: int = 80
    """Largura mínima de botão de toolbar com texto"""

    BUTTON_TOOLBAR_ICON_SIZE: int = 28
    """Tamanho de botão de toolbar com ícone (quadrado - Refresh, Clear)"""
    BUTTON_TOOLBAR_ICON_LARGE_SIZE: int = 32
    """Tamanho de botão de toolbar com ícone grande (quadrado)"""

    # --------------------------------------------------------------------------
    # INLINE ACTION BUTTONS (Botões de ação em linha/formulário)
    # --------------------------------------------------------------------------

    BUTTON_INLINE_PRIMARY_HEIGHT: int = 24
    """Altura de botão inline primário (Capturar, Calcular)"""
    BUTTON_INLINE_PRIMARY_MIN_WIDTH: int = 60

    BUTTON_INLINE_SECONDARY_HEIGHT: int = 22
    """Altura de botão inline secundário (Limpar, Reset)"""
    BUTTON_INLINE_SECONDARY_MIN_WIDTH: int = 55
    """Largura mínima de botão inline secundário"""

    BUTTON_INLINE_COMPACT_HEIGHT: int = 20
    """Altura de botão inline compacto [CUIDADO: usar com moderação]"""
    BUTTON_INLINE_COMPACT_MIN_WIDTH: int = 50
    """Largura mínima de botão inline compacto"""

    # --------------------------------------------------------------------------
    # GRID/TABLE ACTION BUTTONS (Botões de ação em tabelas)
    # --------------------------------------------------------------------------

    BUTTON_GRID_ACTION_HEIGHT: int = 28
    """Altura de botão de ação em grid"""
    BUTTON_GRID_ACTION_MIN_WIDTH: int = 60
    """Largura mínima de botão de ação em grid"""

    BUTTON_GRID_STATUS_HEIGHT: int = 20
    """Altura de badge clicável de status"""

    # =========================================================================
    # INPUT HEIGHTS (Microsoft Style)
    # =========================================================================

    INPUT_HEIGHT_SM: int = 22
    """Altura de input pequeno"""

    INPUT_HEIGHT_MD: int = 26
    """Altura de input médio (padrão)"""

    INPUT_HEIGHT_LG: int = 32
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
