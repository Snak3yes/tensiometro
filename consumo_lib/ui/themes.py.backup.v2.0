"""
Sistema de Temas - Tensiometro

Define paletas de cores para diferentes temas (Light, Dark, System).
Baseado no Material Design 3: https://m3.material.io/styles/color/the-color-system/tokens

Este arquivo fornece:
- LightThemePalette: Cores para tema claro
- DarkThemePalette: Cores para tema escuro
- ThemePaletteFactory: Factory pattern para criar paletas dinamicamente
"""

from dataclasses import dataclass
from typing import Literal
from PyQt6.QtGui import QColor
import logging

logger = logging.getLogger(__name__)

# Type alias para temas suportados
ThemeType = Literal["light", "dark", "system"]


@dataclass(frozen=True)
class LightThemePalette:
    """
    Paleta de cores para o tema Light (claro)

    Segue especificação Material Design 3 para tema claro.
    Todas as cores são valores hexadecimais compatíveis com Qt.
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

    ON_PRIMARY_DARK: str = "#E0E0E0"  # Gray 200
    """Variação escura de ON_PRIMARY"""

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

    TEXT_PRIMARY_DARK: str = "#424242"  # Gray 800
    """Variação escura de TEXT_PRIMARY"""

    TEXT_PRIMARY_VARIANT: str = "#757575"  # Gray 600
    """Variação de TEXT_PRIMARY"""

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

    BORDER_VARIANT: str = "#EEEEEE"  # Gray 200
    """Variação de borda (mais clara que BORDER)"""

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


@dataclass(frozen=True)
class DarkThemePalette:
    """
    Paleta de cores para o tema Dark (escuro)

    Segue especificação Material Design 3 para tema escuro.
    Cores otimizadas para reduzir fadiga visual em ambientes escuros.
    """

    # =========================================================================
    # PRIMARY COLORS (Verde - Success/Action)
    # =========================================================================
    # No dark mode, cores primárias são levemente mais suaves para evitar glare

    PRIMARY: str = "#66BB6A"  # Green 400 (mais suave que light theme)
    """Cor primária para ações principais e botões"""

    PRIMARY_DARK: str = "#43A047"  # Green 600
    """Versão escura da cor primária (hover states)"""

    PRIMARY_LIGHT: str = "#81C784"  # Green 300
    """Versão clara da cor primária"""

    ON_PRIMARY: str = "#121212"  # Almost black
    """Cor de texto/símbolos sobre cor primária (invertido no dark)"""

    ON_PRIMARY_DARK: str = "#000000"  # Black
    """Variação escura de ON_PRIMARY (no dark theme)"""

    # =========================================================================
    # SECONDARY COLORS (Azul - Information)
    # =========================================================================

    SECONDARY: str = "#42A5F5"  # Blue 400 (mais suave)
    """Cor secundária para informações e ações secundárias"""

    SECONDARY_DARK: str = "#1E88E5"  # Blue 600
    """Versão escura da cor secundária"""

    SECONDARY_LIGHT: str = "#64B5F6"  # Blue 300
    """Versão clara da cor secundária"""

    ON_SECONDARY: str = "#121212"  # Almost black
    """Cor de texto/símbolos sobre cor secundária (invertido no dark)"""

    # =========================================================================
    # SUCCESS COLORS
    # =========================================================================

    SUCCESS: str = "#4CAF50"  # Green 500 (mais vibrante no dark)
    """Cor para indicar sucesso"""

    SUCCESS_DARK: str = "#388E3C"  # Green 700
    """Versão escura da cor de sucesso"""

    # =========================================================================
    # WARNING COLORS
    # =========================================================================

    WARNING: str = "#FFD54F"  # Amber 300 (mais visível em fundo escuro)
    """Cor para avisos e atenção"""

    WARNING_DARK: str = "#FFB300"  # Amber 600
    """Versão escura da cor de aviso"""

    WARNING_LIGHT: str = "#FFE082"  # Amber 200
    """Versão clara da cor de aviso (backgrounds)"""

    # =========================================================================
    # ERROR COLORS
    # =========================================================================

    ERROR: str = "#EF5350"  # Red 400 (mais suave que light)
    """Cor para erros e estados críticos"""

    ERROR_DARK: str = "#E53935"  # Red 700
    """Versão escura da cor de erro"""

    ERROR_LIGHT: str = "#EF9A9A"  # Red 200
    """Versão clara da cor de erro (backgrounds)"""

    # =========================================================================
    # STATUS COLORS (Domínio Específico - Inspeção)
    # =========================================================================

    STATUS_APPROVED_AUTO: str = "#66BB6A"  # Verde suave
    """Status: aprovado automaticamente (algoritmo)"""

    STATUS_APPROVED_USER: str = "#D4E157"  # Verde-amarelo ajustado
    """Status: aprovado manualmente (usuário)"""

    STATUS_REJECTED: str = "#EF5350"  # Vermelho suave
    """Status: reprovado/falha na inspeção"""

    STATUS_PENDING: str = "#757575"  # Cinza médio
    """Status: pendente (ainda não inspecionado)"""

    STATUS_IN_PROGRESS: str = "#42A5F5"  # Azul suave
    """Status: em andamento (inspeção em curso)"""

    # =========================================================================
    # NEUTRAL COLORS (Texto, Background, Surface)
    # =========================================================================
    # No dark mode, invertemos: background escuro, texto claro

    TEXT_PRIMARY: str = "#E0E0E0"  # Gray 300 (quase branco)
    """Cor de texto principal (alto contraste em fundo escuro)"""

    TEXT_PRIMARY_DARK: str = "#BDBDBD"  # Gray 200
    """Variação escura de TEXT_PRIMARY (no dark theme)"""

    TEXT_PRIMARY_VARIANT: str = "#9E9E9E"  # Gray 500
    """Variação de TEXT_PRIMARY"""

    TEXT_SECONDARY: str = "#B0BEC5"  # Blue Gray 200
    """Cor de texto secundário (menos proeminente)"""

    TEXT_DISABLED: str = "#616161"  # Gray 700
    """Cor de texto desabilitado"""

    TEXT_HINT: str = "#757575"  # Gray 600
    """Cor de hint/placeholder text"""

    BACKGROUND: str = "#121212"  # Almost black (Material Design dark baseline)
    """Cor de fundo principal da aplicação"""

    SURFACE: str = "#1E1E1E"  # Dark gray (elevated surface)
    """Cor de superfície (cards, panels)"""

    SURFACE_VARIANT: str = "#2C2C2C"  # Gray 800
    """Variante de cor de superfície"""

    # =========================================================================
    # BORDER COLORS
    # =========================================================================

    BORDER: str = "#424242"  # Gray 800
    """Cor de bordas padrão (mais visível em fundo escuro)"""

    BORDER_DARK: str = "#616161"  # Gray 700
    """Cor de bordas escuras"""

    BORDER_VARIANT: str = "#616161"  # Gray 700
    """Variação de borda (igual ao BORDER_DARK no dark theme)"""

    BORDER_FOCUS: str = "#42A5F5"  # Blue 400
    """Cor de borda em estado de focus"""

    # =========================================================================
    # OVERLAY & SPECIAL COLORS
    # =========================================================================

    OVERLAY: str = "rgba(0, 0, 0, 0.7)"
    """Cor de overlay (mais opaca no dark mode)"""

    OVERLAY_DARK: str = "rgba(0, 0, 0, 0.85)"
    """Cor de overlay escura (mais opaca)"""

    SHADOW: str = "rgba(0, 0, 0, 0.3)"
    """Cor de sombra (mais opaca no dark)"""

    # =========================================================================
    # ENGINEERING-SPECIFIC COLORS (Visão Computacional)
    # =========================================================================

    OVERLAY_IMAGE: str = "#2C2C2C"  # Dark gray ajustado
    """Cor de overlay para imagens de visão computacional"""

    FIDUCIAL_FOUND: str = "#00FF00"  # Verde neon (mesmo, alta visibilidade)
    """Cor para marcar fiduciais encontrados (alta visibilidade)"""

    FIDUCIAL_NOT_FOUND: str = "#FF0000"  # Vermelho neon (mesmo)
    """Cor para marcar fiduciais não encontrados (alta visibilidade)"""

    GRID_LINES: str = "#424242"  # Gray 800 (mais visível em fundo escuro)
    """Cor de linhas de grade em visualizações"""

    # =========================================================================
    # ADDITIONAL UI COLORS
    # =========================================================================

    DIVIDER: str = "#424242"  # Gray 800
    """Cor de divisores/separadores"""

    ICON: str = "#B0BEC5"  # Blue Gray 200
    """Cor padrão para ícones"""

    ICON_ACTIVE: str = "#E0E0E0"  # Gray 300
    """Cor para ícones ativos/selecionados"""

    LINK: str = "#42A5F5"  # Blue 400
    """Cor para links e texto clicável"""

    LINK_VISITED: str = "#AB47BC"  # Purple 400
    """Cor para links visitados"""


class ThemePaletteFactory:
    """
    Factory para criar paletas de cores baseadas no tema

    Este factory permite alternar dinamicamente entre temas
    sem alterar o código que consome as cores.

    Usage:
        >>> from consumo_lib.ui.themes import ThemePaletteFactory
        >>> palette = ThemePaletteFactory.create_palette("light")
        >>> palette.PRIMARY
        '#4CAF50'
        >>>
        >>> # Mudar para dark
        >>> palette_dark = ThemePaletteFactory.create_palette("dark")
        >>> palette_dark.BACKGROUND
        '#121212'
    """

    @staticmethod
    def create_palette(theme: ThemeType = "light") -> "LightThemePalette | DarkThemePalette":
        """
        Cria paleta de cores para o tema especificado

        Args:
            theme: Nome do tema ("light" | "dark" | "system")

        Returns:
            Instância de LightThemePalette ou DarkThemePalette

        Raises:
            ValueError: Se tema for desconhecido

        Note:
            Para "system", detecta automaticamente o tema do OS.
            Se detecção falhar, fallback para "light".
        """
        if theme == "system":
            # Detectar tema do sistema operacional
            detected_theme = ThemePaletteFactory._detect_system_theme()
            logger.debug(f"Tema 'system' detectado como: {detected_theme}")
            theme = detected_theme

        if theme == "light":
            logger.debug("Criando paleta LightTheme")
            return LightThemePalette()

        elif theme == "dark":
            logger.debug("Criando paleta DarkTheme")
            return DarkThemePalette()

        else:
            logger.warning(f"Tema desconhecido: '{theme}', usando light theme")
            return LightThemePalette()

    @staticmethod
    def _detect_system_theme() -> ThemeType:
        """
        Detecta tema do sistema operacional (light/dark)

        Returns:
            "light" ou "dark" baseado na configuração do OS

        Note:
            - Windows: Lê registro do Windows
            - macOS: Lê defaults do sistema
            - Linux: Lê settings do Desktop Environment
            - Fallback: "light" se não conseguir detectar
        """
        import platform

        system = platform.system()

        try:
            if system == "Windows":
                return ThemePaletteFactory._detect_windows_theme()

            elif system == "Darwin":  # macOS
                return ThemePaletteFactory._detect_macos_theme()

            elif system == "Linux":
                return ThemePaletteFactory._detect_linux_theme()

            else:
                logger.warning(f"Sistema não suportado: {system}, usando light theme")
                return "light"

        except Exception as e:
            logger.warning(f"Erro ao detectar tema do sistema: {e}, usando light theme")
            return "light"

    @staticmethod
    def _detect_windows_theme() -> ThemeType:
        """
        Detecta tema do Windows via registro

        Returns:
            "light" ou "dark"
        """
        try:
            import winreg

            # Windows 10+: AppsUseLightTheme
            # 0 = Dark, 1 = Light
            registry_key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            )

            # AppsUseLightTheme: 0=dark, 1=light
            value, _ = winreg.QueryValueEx(registry_key, "AppsUseLightTheme")
            winreg.CloseKey(registry_key)

            # 0 = dark mode, 1 = light mode
            if value == 0:
                logger.debug("Windows: Dark theme detectado")
                return "dark"
            else:
                logger.debug("Windows: Light theme detectado")
                return "light"

        except FileNotFoundError:
            # Registro não existe (Windows < 10), fallback para light
            logger.debug("Windows < 10 não suporta dark theme nativo, usando light")
            return "light"

        except Exception as e:
            logger.warning(f"Erro ao ler registro Windows: {e}")
            return "light"

    @staticmethod
    def _detect_macos_theme() -> ThemeType:
        """
        Detecta tema do macOS via defaults

        Returns:
            "light" ou "dark"
        """
        import subprocess

        try:
            # macOS: defaults read -g AppleInterfaceStyle
            # Retorna "Dark" se dark mode, senão vazio (light)
            result = subprocess.run(
                ["defaults", "read", "-g", "AppleInterfaceStyle"],
                capture_output=True,
                text=True,
                timeout=1
            )

            if "Dark" in result.stdout:
                logger.debug("macOS: Dark theme detectado")
                return "dark"
            else:
                logger.debug("macOS: Light theme detectado")
                return "light"

        except (FileNotFoundError, subprocess.TimeoutExpired):
            logger.warning("macOS: comando defaults falhou, usando light theme")
            return "light"

        except Exception as e:
            logger.warning(f"Erro ao detectar tema macOS: {e}")
            return "light"

    @staticmethod
    def _detect_linux_theme() -> ThemeType:
        """
        Detecta tema do Linux via Desktop Environment

        Returns:
            "light" ou "dark"
        """
        import subprocess

        try:
            # Tentar várias maneiras de detectar no Linux
            # GNOME: gsettings get org.gnome.desktop.interface gtk-theme
            # KDE: смотрит на configurações do Plasma

            # GNOME via gsettings
            result = subprocess.run(
                ["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"],
                capture_output=True,
                text=True,
                timeout=1
            )

            theme_name = result.stdout.strip().lower()

            # Hint: "-dark" no nome do tema geralmente indica dark theme
            if "dark" in theme_name:
                logger.debug(f"Linux GNOME: Dark theme detectado ({theme_name})")
                return "dark"
            else:
                logger.debug(f"Linux GNOME: Light theme detectado ({theme_name})")
                return "light"

        except FileNotFoundError:
            # gsettings não existe, tentar outros métodos
            # Fallback para light
            logger.debug("Linux: gsettings não disponível, usando light theme")
            return "light"

        except Exception as e:
            logger.warning(f"Erro ao detectar tema Linux: {e}")
            return "light"


# =============================================================================
# MÉTODOS UTILITÁRIOS (compatibilidade com código legado)
# =============================================================================

def to_qcolor(color_hex: str) -> QColor:
    """
    Converte string hexadecimal para QColor

    Args:
        color_hex: Cor em formato hexadecimal (ex: "#4CAF50")

    Returns:
        Instância de QColor

    Raises:
        ValueError: Se formato for inválido

    Exemplo:
        >>> to_qcolor("#4CAF50")
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


def get_status_color(palette: "LightThemePalette | DarkThemePalette", status: str) -> str:
    """
    Retorna cor para um status específico da paleta

    Args:
        palette: Instância de paleta (LightThemePalette ou DarkThemePalette)
        status: Código do status (approved_auto, approved_user, rejected, etc.)

    Returns:
        Cor hexadecimal correspondente ao status

    Raises:
        ValueError: Se status for desconhecido

    Exemplo:
        >>> palette = ThemePaletteFactory.create_palette("light")
        >>> get_status_color(palette, "approved_auto")
        '#4CAF50'
    """
    status_map = {
        "approved_auto": palette.STATUS_APPROVED_AUTO,
        "approved_user": palette.STATUS_APPROVED_USER,
        "rejected": palette.STATUS_REJECTED,
        "pending": palette.STATUS_PENDING,
        "in_progress": palette.STATUS_IN_PROGRESS,
    }

    if status not in status_map:
        raise ValueError(f"Status desconhecido: {status}")

    return status_map[status]


__all__ = [
    "ThemeType",
    "LightThemePalette",
    "DarkThemePalette",
    "ThemePaletteFactory",
    "to_qcolor",
    "get_status_color",
]
