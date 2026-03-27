"""
⚠️⚠️⚠️ REGRA CRÍTICA: PROIBIÇÃO DE ESTILOS INLINE/HARDCODED ⚠️⚠️⚠️

Este arquivo DEFINE as paletas de cores (LIGHT, DARK, SYSTEM).

❌ COMPLETAMENTE PROIBIDO em qualquer lugar da aplicação:
   - Usar valores hexadecimais hardcoded (#4CAF50, #e74c3c, etc.)
   - Definir cores em outros arquivos
   - Criar "cores mágicas" sem documentação

✅ SEMPRE USE:
   - COLORS.* do design_tokens.py (que aponta para estas paletas)
   - Este arquivo para ADICIONAR novas cores ao sistema

✅ SE PRECISA DE UMA NOVA COR:
   - Adicione AQUI em LightThemePalette e DarkThemePalette
   - Documente o propósito da cor (usando /**/ docstrings)
   - Use ColorPalette para acessar dinamicamente com base no tema

⚠️ ESTA REGRA NÃO PODE SER BURLADA - Code review irá rejeitar violações
⚠️⚠️⚠️ FIM DA REGRA CRÍTICA ⚠️⚠️⚠️

Sistema de Temas - Tensiometro
Paleta NEUTRA - Tons de Cinza Industrial

Baseado no projeto ADESIVADORA_DOUBLE_TABLE para interface industrial limpa.
Foco em: clareza, legibilidade, baixo contraste visual, profissionalismo.

Este arquivo fornece:
- LightThemePalette: Cores neutras para tema claro
- DarkThemePalette: Cores neutras para tema escuro
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
    Paleta de cores NEUTRAS para o tema Light (claro)

    v3.0 - Paleta Neutra Industrial:
    - Todos os botões e elementos em tons de cinza
    - Alto contraste para texto, baixo contraste para elementos
    - Aparência limpa e profissional
    - Status indicados por ícones/texto, não por cores vibrantes

    Referência: ADESIVADORA_DOUBLE_TABLE
    """

    # =========================================================================
    # PRIMARY COLORS (Cinza Escuro - Ações Principais)
    # =========================================================================

    PRIMARY: str = "#37474F"
    """Cinza escuro para botões primários e ações principais"""

    PRIMARY_DARK: str = "#263238"
    """Versão mais escura para hover"""

    PRIMARY_LIGHT: str = "#455A64"
    """Versão clara para elementos secundários"""

    ON_PRIMARY: str = "#FFFFFF"
    """Texto branco sobre cinza escuro"""

    ON_PRIMARY_DARK: str = "#E0E0E0"
    """Texto cinza claro sobre muito escuro"""

    # =========================================================================
    # SECONDARY COLORS (Cinza Médio - Ações Secundárias)
    # =========================================================================

    SECONDARY: str = "#607D8B"
    """Cinza médio para informações e ações secundárias"""

    SECONDARY_DARK: str = "#455A64"
    """Versão escura para hover"""

    SECONDARY_LIGHT: str = "#78909C"
    """Versão clara"""

    ON_SECONDARY: str = "#FFFFFF"
    """Texto branco sobre cinza médio"""

    # =========================================================================
    # SUCCESS COLORS (Cinza Esverdeado Sutil - Sucesso)
    # =========================================================================

    SUCCESS: str = "#546E7A"
    """Cinza azulado para sucesso (sutil, não verde vibrante)"""

    SUCCESS_DARK: str = "#37474F"
    """Versão escura"""

    # =========================================================================
    # WARNING COLORS (Cinza Amarelado Sutil - Atenção)
    # =========================================================================

    WARNING: str = "#78909C"
    """Cinza médio para avisos (sutil)"""

    WARNING_DARK: str = "#607D8B"
    """Versão escura"""

    WARNING_LIGHT: str = "#90A4AE"
    """Versão clara para backgrounds"""

    # =========================================================================
    # ERROR COLORS (Cinza Avermelhado Sutil - Erro)
    # =========================================================================

    ERROR: str = "#546E7A"
    """Cinza para erros (sutil, indicado por ícone/texto)"""

    ERROR_DARK: str = "#37474F"
    """Versão escura"""

    ERROR_LIGHT: str = "#78909C"
    """Versão clara"""

    # =========================================================================
    # STATUS COLORS (Domínio Específico - Tons Neutros)
    # =========================================================================

    STATUS_APPROVED_AUTO: str = "#546E7A"
    """Status: aprovado automaticamente"""

    STATUS_APPROVED_USER: str = "#607D8B"
    """Status: aprovado manualmente"""

    STATUS_REJECTED: str = "#455A64"
    """Status: reprovado/falha"""

    STATUS_PENDING: str = "#90A4AE"
    """Status: pendente"""

    STATUS_IN_PROGRESS: str = "#78909C"
    """Status: em andamento"""

    # =========================================================================
    # NEUTRAL COLORS (Texto, Background, Surface)
    # =========================================================================

    TEXT_PRIMARY: str = "#111827"
    """Texto principal - quase preto para máxima legibilidade"""

    TEXT_PRIMARY_DARK: str = "#1F2937"
    """Variação escura"""

    TEXT_PRIMARY_VARIANT: str = "#374151"
    """Variação de texto"""

    TEXT_SECONDARY: str = "#6B7280"
    """Texto secundário - cinza médio"""

    TEXT_DISABLED: str = "#9CA3AF"
    """Texto desabilitado"""

    TEXT_HINT: str = "#9CA3AF"
    """Hint/placeholder"""

    BACKGROUND: str = "#F2F4F7"
    """Fundo principal - cinza muito claro"""

    SURFACE: str = "#FFFFFF"
    """Superfície (cards, panels) - branco"""

    SURFACE_VARIANT: str = "#E6EAEE"
    """Variante de superfície - cinza claro"""

    # =========================================================================
    # BORDER COLORS
    # =========================================================================

    BORDER: str = "#D1D5DB"
    """Bordas padrão"""

    BORDER_DARK: str = "#9CA3AF"
    """Bordas escuras"""

    BORDER_VARIANT: str = "#E5E7EB"
    """Variante de borda"""

    BORDER_FOCUS: str = "#607D8B"
    """Borda em focus"""

    # =========================================================================
    # OVERLAY & SPECIAL COLORS
    # =========================================================================

    OVERLAY: str = "rgba(0, 0, 0, 0.4)"
    """Overlay semi-transparente"""

    OVERLAY_DARK: str = "rgba(0, 0, 0, 0.6)"
    """Overlay mais opaco"""

    SHADOW: str = "rgba(0, 0, 0, 0.08)"
    """Sombra suave"""

    # =========================================================================
    # ENGINEERING-SPECIFIC COLORS (Visão Computacional)
    # Mantidas cores vivas para alta visibilidade em imagens
    # =========================================================================

    OVERLAY_IMAGE: str = "#1e1e1e"
    """Overlay para imagens"""

    FIDUCIAL_FOUND: str = "#22C55E"
    """Fiducial encontrado - verde para visibilidade"""

    FIDUCIAL_NOT_FOUND: str = "#EF4444"
    """Fiducial não encontrado - vermelho para visibilidade"""

    GRID_LINES: str = "#D1D5DB"
    """Linhas de grade"""

    # =========================================================================
    # ADDITIONAL UI COLORS
    # =========================================================================

    DIVIDER: str = "#E5E7EB"
    """Divisores/separadores"""

    ICON: str = "#6B7280"
    """Ícones padrão"""

    ICON_ACTIVE: str = "#374151"
    """Ícones ativos"""

    LINK: str = "#4B5563"
    """Links - cinza escuro"""

    LINK_VISITED: str = "#6B7280"
    """Links visitados"""

    # =========================================================================
    # BUTTON STATES (Neutros)
    # =========================================================================

    BUTTON_DEFAULT: str = "#F2F4F7"
    """Botão padrão - cinza claro"""

    BUTTON_DEFAULT_HOVER: str = "#E6EAEE"
    """Botão padrão hover"""

    BUTTON_DEFAULT_PRESSED: str = "#D9DEE3"
    """Botão padrão pressionado"""

    BUTTON_PRIMARY: str = "#455A64"
    """Botão primário - cinza escuro"""

    BUTTON_PRIMARY_HOVER: str = "#37474F"
    """Botão primário hover"""

    BUTTON_PRIMARY_PRESSED: str = "#263238"
    """Botão primário pressionado"""

    BUTTON_DANGER: str = "#78909C"
    """Botão de perigo - cinza"""

    BUTTON_DANGER_HOVER: str = "#607D8B"
    """Botão de perigo hover"""


@dataclass(frozen=True)
class DarkThemePalette:
    """
    Paleta de cores NEUTRAS para o tema Dark (escuro)

    v3.0 - Paleta Neutra Industrial (Dark):
    - Tons de cinza escuro para fundos
    - Texto claro para contraste
    - Mesma filosofia neutra do light theme
    """

    # =========================================================================
    # PRIMARY COLORS (Cinza Claro - Ações Principais)
    # =========================================================================

    PRIMARY: str = "#90A4AE"
    """Cinza claro para botões primários"""

    PRIMARY_DARK: str = "#78909C"
    """Versão mais escura para hover"""

    PRIMARY_LIGHT: str = "#B0BEC5"
    """Versão clara"""

    ON_PRIMARY: str = "#111827"
    """Texto escuro sobre cinza claro"""

    ON_PRIMARY_DARK: str = "#1F2937"
    """Texto escuro"""

    # =========================================================================
    # SECONDARY COLORS (Cinza Médio)
    # =========================================================================

    SECONDARY: str = "#78909C"
    """Cinza médio"""

    SECONDARY_DARK: str = "#607D8B"
    """Versão escura"""

    SECONDARY_LIGHT: str = "#90A4AE"
    """Versão clara"""

    ON_SECONDARY: str = "#111827"
    """Texto escuro"""

    # =========================================================================
    # SUCCESS COLORS (Cinza Esverdeado Sutil)
    # =========================================================================

    SUCCESS: str = "#90A4AE"
    """Cinza para sucesso"""

    SUCCESS_DARK: str = "#78909C"
    """Versão escura"""

    # =========================================================================
    # WARNING COLORS (Cinza Amarelado Sutil)
    # =========================================================================

    WARNING: str = "#B0BEC5"
    """Cinza para avisos"""

    WARNING_DARK: str = "#90A4AE"
    """Versão escura"""

    WARNING_LIGHT: str = "#CFD8DC"
    """Versão clara"""

    # =========================================================================
    # ERROR COLORS (Cinza Avermelhado Sutil)
    # =========================================================================

    ERROR: str = "#90A4AE"
    """Cinza para erros"""

    ERROR_DARK: str = "#78909C"
    """Versão escura"""

    ERROR_LIGHT: str = "#B0BEC5"
    """Versão clara"""

    # =========================================================================
    # STATUS COLORS
    # =========================================================================

    STATUS_APPROVED_AUTO: str = "#90A4AE"
    """Status: aprovado automaticamente"""

    STATUS_APPROVED_USER: str = "#A3B8C6"
    """Status: aprovado manualmente"""

    STATUS_REJECTED: str = "#78909C"
    """Status: reprovado"""

    STATUS_PENDING: str = "#607D8B"
    """Status: pendente"""

    STATUS_IN_PROGRESS: str = "#90A4AE"
    """Status: em andamento"""

    # =========================================================================
    # NEUTRAL COLORS (Texto, Background, Surface)
    # =========================================================================

    TEXT_PRIMARY: str = "#F2F4F7"
    """Texto principal - cinza claro"""

    TEXT_PRIMARY_DARK: str = "#E6EAEE"
    """Variação"""

    TEXT_PRIMARY_VARIANT: str = "#D1D5DB"
    """Variação"""

    TEXT_SECONDARY: str = "#9CA3AF"
    """Texto secundário"""

    TEXT_DISABLED: str = "#6B7280"
    """Texto desabilitado"""

    TEXT_HINT: str = "#6B7280"
    """Hint/placeholder"""

    BACKGROUND: str = "#1F2937"
    """Fundo principal - cinza escuro"""

    SURFACE: str = "#374151"
    """Superfície"""

    SURFACE_VARIANT: str = "#4B5563"
    """Variante de superfície"""

    # =========================================================================
    # BORDER COLORS
    # =========================================================================

    BORDER: str = "#4B5563"
    """Bordas padrão"""

    BORDER_DARK: str = "#6B7280"
    """Bordas escuras"""

    BORDER_VARIANT: str = "#374151"
    """Variante de borda"""

    BORDER_FOCUS: str = "#90A4AE"
    """Borda em focus"""

    # =========================================================================
    # OVERLAY & SPECIAL COLORS
    # =========================================================================

    OVERLAY: str = "rgba(0, 0, 0, 0.6)"
    """Overlay"""

    OVERLAY_DARK: str = "rgba(0, 0, 0, 0.8)"
    """Overlay opaco"""

    SHADOW: str = "rgba(0, 0, 0, 0.3)"
    """Sombra"""

    # =========================================================================
    # ENGINEERING-SPECIFIC COLORS
    # =========================================================================

    OVERLAY_IMAGE: str = "#2C2C2C"
    """Overlay para imagens"""

    FIDUCIAL_FOUND: str = "#22C55E"
    """Fiducial encontrado"""

    FIDUCIAL_NOT_FOUND: str = "#EF4444"
    """Fiducial não encontrado"""

    GRID_LINES: str = "#4B5563"
    """Linhas de grade"""

    # =========================================================================
    # ADDITIONAL UI COLORS
    # =========================================================================

    DIVIDER: str = "#374151"
    """Divisores"""

    ICON: str = "#9CA3AF"
    """Ícones padrão"""

    ICON_ACTIVE: str = "#F2F4F7"
    """Ícones ativos"""

    LINK: str = "#D1D5DB"
    """Links"""

    LINK_VISITED: str = "#9CA3AF"
    """Links visitados"""

    # =========================================================================
    # BUTTON STATES (Neutros)
    # =========================================================================

    BUTTON_DEFAULT: str = "#374151"
    """Botão padrão"""

    BUTTON_DEFAULT_HOVER: str = "#4B5563"
    """Botão padrão hover"""

    BUTTON_DEFAULT_PRESSED: str = "#6B7280"
    """Botão padrão pressionado"""

    BUTTON_PRIMARY: str = "#607D8B"
    """Botão primário"""

    BUTTON_PRIMARY_HOVER: str = "#78909C"
    """Botão primário hover"""

    BUTTON_PRIMARY_PRESSED: str = "#90A4AE"
    """Botão primário pressionado"""

    BUTTON_DANGER: str = "#6B7280"
    """Botão de perigo"""

    BUTTON_DANGER_HOVER: str = "#78909C"
    """Botão de perigo hover"""


class ThemePaletteFactory:
    """
    Factory para criar paletas de cores baseadas no tema
    """

    @staticmethod
    def create_palette(theme: ThemeType = "light") -> "LightThemePalette | DarkThemePalette":
        """
        Cria paleta de cores para o tema especificado
        """
        if theme == "system":
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
        """Detecta tema do sistema operacional"""
        import platform

        system = platform.system()

        try:
            if system == "Windows":
                return ThemePaletteFactory._detect_windows_theme()

            elif system == "Darwin":
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
        """Detecta tema do Windows via registro"""
        try:
            import winreg

            registry_key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            )

            value, _ = winreg.QueryValueEx(registry_key, "AppsUseLightTheme")
            winreg.CloseKey(registry_key)

            if value == 0:
                logger.debug("Windows: Dark theme detectado")
                return "dark"
            else:
                logger.debug("Windows: Light theme detectado")
                return "light"

        except FileNotFoundError:
            logger.debug("Windows < 10 não suporta dark theme nativo, usando light")
            return "light"

        except Exception as e:
            logger.warning(f"Erro ao ler registro Windows: {e}")
            return "light"

    @staticmethod
    def _detect_macos_theme() -> ThemeType:
        """Detecta tema do macOS"""
        import subprocess

        try:
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
        """Detecta tema do Linux"""
        import subprocess

        try:
            result = subprocess.run(
                ["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"],
                capture_output=True,
                text=True,
                timeout=1
            )

            theme_name = result.stdout.strip().lower()

            if "dark" in theme_name:
                logger.debug(f"Linux GNOME: Dark theme detectado ({theme_name})")
                return "dark"
            else:
                logger.debug(f"Linux GNOME: Light theme detectado ({theme_name})")
                return "light"

        except FileNotFoundError:
            logger.debug("Linux: gsettings não disponível, usando light theme")
            return "light"

        except Exception as e:
            logger.warning(f"Erro ao detectar tema Linux: {e}")
            return "light"


# =============================================================================
# MÉTODOS UTILITÁRIOS
# =============================================================================

def to_qcolor(color_hex: str) -> QColor:
    """Converte string hexadecimal para QColor"""
    if not color_hex.startswith("#"):
        raise ValueError(f"Cor deve começar com '#': {color_hex}")

    hex_value = color_hex.lstrip("#")

    if len(hex_value) not in [6, 8]:
        raise ValueError(f"Cor HEX deve ter 6 ou 8 caracteres: {color_hex}")

    return QColor(f"#{hex_value}")


def get_status_color(palette: "LightThemePalette | DarkThemePalette", status: str) -> str:
    """Retorna cor para um status específico"""
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