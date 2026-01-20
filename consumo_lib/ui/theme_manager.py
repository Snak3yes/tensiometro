"""
Gerenciador de Temas - Tensiometro

Gerencia aplicação de temas e estilos globais com suporte a:
- Light theme
- Dark theme
- System theme (segue OS)

Features:
        - Aplicar stylesheet global
        - Alternar temas dinamicamente (light/dark/system)
        - Atualizar tokens de design (COLORS) automaticamente
        - Carregar estilos de arquivo .qss
        - Detectar tema do sistema operacional

Usage:
        >>> from consumo_lib.ui.theme_manager import init_theme_manager
        >>> app = QApplication(sys.argv)
        >>> theme_mgr = init_theme_manager(app)
        >>> # Stylesheet aplicado automaticamente
        >>>
        >>> # Mudar tema
        >>> theme_mgr.set_theme("dark")  # COLORS atualiza automaticamente
"""

from typing import Optional
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal
import logging

logger = logging.getLogger(__name__)


class ThemeManager(QObject):
    """
    Gerenciador central de temas e estilos

    Este gerenciador coordena:
        1. Aplicação de stylesheets globais
        2. Mudança de temas (light/dark/system)
        3. Atualização dinâmica de ColorPalette (COLORS)
        4. Notificação de componentes sobre mudança de tema

    Signals:
        theme_changed: Emitido quando tema muda (str: nome do novo tema)

    Usage:
        >>> from consumo_lib.ui.theme_manager import init_theme_manager
        >>> app = QApplication(sys.argv)
        >>> theme_mgr = init_theme_manager(app)
        >>>
        >>> # Mudar tema
        >>> theme_mgr.set_theme("dark")
        >>> # COLORS.PRIMARY agora retorna cor do dark theme
    """

    # Signal emitido quando tema muda
    theme_changed = pyqtSignal(str)  # theme_name

    def __init__(self, app: QApplication, initial_theme: str = "light"):
        """
        Inicializa gerenciador de temas

        Args:
            app: Instância da QApplication
            initial_theme: Tema inicial ("light" | "dark" | "system")
        """
        super().__init__()
        self.app = app
        self.current_theme = initial_theme

        # Inicializar ColorPalette global com tema inicial
        self._init_color_palette(initial_theme)

        # Carregar stylesheet inicial
        self._load_stylesheet()

        logger.info(f"✅ ThemeManager inicializado com tema: {initial_theme}")

    def _init_color_palette(self, theme: str):
        """
        Inicializa ColorPalette global do design_tokens

        Args:
            theme: Nome do tema a ser aplicado
        """
        try:
            import consumo_lib.ui.design_tokens as dt_module
            from consumo_lib.ui.design_tokens import ColorPalette

            if dt_module._COLOR_PALETTE_INSTANCE is None:
                dt_module._COLOR_PALETTE_INSTANCE = ColorPalette(theme=theme)
                logger.info(f"ColorPalette inicializada com tema: {theme}")
            else:
                # Atualizar paleta existente
                dt_module._COLOR_PALETTE_INSTANCE._update_palette(theme)
                logger.info(f"ColorPalette atualizada para tema: {theme}")

        except ImportError as e:
            logger.error(f"❌ Falha ao importar ColorPalette: {e}")

    def _load_stylesheet(self):
        """
        Gera e aplica stylesheet global com cores do tema atual

        O stylesheet é gerado dinamicamente substituindo placeholders
        no arquivo styles.qss.template pelos valores atuais de COLORS.
        """
        try:
            # Gerar stylesheet dinamicamente
            stylesheet = self._generate_stylesheet()

            # Aplica stylesheet
            self.app.setStyleSheet(stylesheet)
            logger.info(f"✅ Stylesheet global gerado e aplicado (tema: {self.current_theme})")

        except Exception as e:
            logger.warning(f"⚠️ Falha ao gerar stylesheet: {e}")
            logger.warning("   Usando estilos padrão do Qt")
            # Não re-raise - permitir que app rode sem stylesheet

    def _generate_stylesheet(self) -> str:
        """
        Gera stylesheet dinamicamente substituindo placeholders

        Returns:
            Stylesheet com cores do tema atual

        Raises:
            FileNotFoundError: Se styles.qss.template não existir
        """
        from importlib.resources import read_text

        # Ler template
        template = read_text("consumo_lib.ui", "styles.qss.template")

        # Obter paleta de cores atual
        from consumo_lib.ui.design_tokens import get_color_palette
        colors = get_color_palette()

        # Dicionário de substituição (placeholder -> valor atual)
        replacements = {
            # Primary Colors
            '{{PRIMARY}}': colors.PRIMARY,
            '{{PRIMARY_DARK}}': colors.PRIMARY_DARK,
            '{{PRIMARY_LIGHT}}': colors.PRIMARY_LIGHT,
            '{{ON_PRIMARY}}': colors.ON_PRIMARY,

            # Secondary Colors
            '{{SECONDARY}}': colors.SECONDARY,
            '{{SECONDARY_DARK}}': colors.SECONDARY_DARK,
            '{{ON_SECONDARY}}': colors.ON_SECONDARY,

            # Success Colors
            '{{SUCCESS}}': colors.SUCCESS,
            '{{SUCCESS_DARK}}': colors.SUCCESS_DARK,

            # Warning Colors
            '{{WARNING}}': colors.WARNING,
            '{{WARNING_DARK}}': colors.WARNING_DARK,
            '{{WARNING_LIGHT}}': colors.WARNING_LIGHT,

            # Error Colors
            '{{ERROR}}': colors.ERROR,
            '{{ERROR_DARK}}': colors.ERROR_DARK,
            '{{ERROR_LIGHT}}': colors.ERROR_LIGHT,

            # Text Colors
            '{{TEXT_PRIMARY}}': colors.TEXT_PRIMARY,
            '{{TEXT_SECONDARY}}': colors.TEXT_SECONDARY,
            '{{TEXT_DISABLED}}': colors.TEXT_DISABLED,
            '{{TEXT_HINT}}': colors.TEXT_HINT,

            # Background & Surface
            '{{BACKGROUND}}': colors.BACKGROUND,
            '{{SURFACE}}': colors.SURFACE,
            '{{SURFACE_VARIANT}}': colors.SURFACE_VARIANT,

            # Border Colors
            '{{BORDER}}': colors.BORDER,
            '{{BORDER_DARK}}': colors.BORDER_DARK,
            '{{BORDER_FOCUS}}': colors.BORDER_FOCUS,

            # Divider
            '{{DIVIDER}}': colors.DIVIDER,
        }

        # Aplicar substituições
        stylesheet = template
        for placeholder, value in replacements.items():
            stylesheet = stylesheet.replace(placeholder, value)

        return stylesheet

    def set_theme(self, theme_name: str):
        """
        Altera tema atual e atualiza ColorPalette global

        Args:
            theme_name: Nome do tema ("light" | "dark" | "system")

        Note:
            - "light": Tema claro (padrão)
            - "dark": Tema escuro
            - "system": Detecta automaticamente tema do OS

        Example:
            >>> theme_mgr.set_theme("dark")  # Muda para dark theme
            >>> COLORS.PRIMARY  # Agora retorna cor do dark theme
            >>> theme_mgr.set_theme("system")  # Segue configuração do OS
        """
        # Validar tema
        valid_themes = ["light", "dark", "system"]
        if theme_name not in valid_themes:
            logger.warning(f"⚠️ Tema inválido: '{theme_name}'. Temas válidos: {valid_themes}")
            return

        if theme_name == self.current_theme:
            logger.debug(f"Tema {theme_name} já está ativo")
            return

        logger.info(f"🎨 Alterando tema de '{self.current_theme}' para '{theme_name}'")
        self.current_theme = theme_name

        # Atualizar ColorPalette global
        self._update_color_palette(theme_name)

        # Aplicar stylesheet do tema
        self._apply_theme(theme_name)

        # Emitir signal para componentes interessados
        self.theme_changed.emit(theme_name)

        logger.info(f"✅ Tema alterado para: {theme_name}")

    def _update_color_palette(self, theme_name: str):
        """
        Atualiza ColorPalette global para novo tema

        Args:
            theme_name: Nome do tema a ser aplicado
        """
        try:
            import consumo_lib.ui.design_tokens as dt_module

            if dt_module._COLOR_PALETTE_INSTANCE is not None:
                # Atualizar paleta existente
                dt_module._COLOR_PALETTE_INSTANCE._update_palette(theme_name)
            else:
                # Criar nova paleta
                from consumo_lib.ui.design_tokens import ColorPalette
                dt_module._COLOR_PALETTE_INSTANCE = ColorPalette(theme=theme_name)

            logger.info(f"✅ ColorPalette atualizada para tema: {theme_name}")

        except Exception as e:
            logger.error(f"❌ Erro ao atualizar ColorPalette: {e}")

    def _apply_theme(self, theme_name: str):
        """
        Aplica configurações específicas do tema

        Args:
            theme_name: Nome do tema
        """
        if theme_name == "light":
            # Tema claro (padrão)
            self._load_stylesheet()

        elif theme_name == "dark":
            # TODO: Criar styles_dark.qss com cores apropriadas para dark theme
            # Por enquanto, usa stylesheet padrão
            logger.info("🌙 Aplicando dark theme (usando styles.qss padrão)")
            self._load_stylesheet()

        elif theme_name == "system":
            # Detectar e aplicar tema do sistema
            detected = self._detect_system_theme()
            logger.info(f"💻 System theme detectado como: {detected}")
            self._load_stylesheet()

    def _detect_system_theme(self) -> str:
        """
        Detecta tema do sistema operacional

        Returns:
            "light" ou "dark"
        """
        try:
            from consumo_lib.ui.themes import ThemePaletteFactory
            return ThemePaletteFactory._detect_system_theme()
        except Exception as e:
            logger.warning(f"⚠️ Erro ao detectar tema do sistema: {e}")
            return "light"  # Fallback seguro

    def get_current_theme(self) -> str:
        """
        Retorna tema atual

        Returns:
            Nome do tema atual ("light" | "dark" | "system")
        """
        return self.current_theme

    @property
    def colors(self):
        """
        Retorna paleta de cores do tema atual

        Returns:
            Instância de ColorPalette (do design_tokens)

        Deprecated:
            Prefira usar COLORS diretamente:
            >>> from consumo_lib.ui import COLORS
            >>> COLORS.PRIMARY
        """
        # Import local para evitar circular import
        from consumo_lib.ui.design_tokens import get_color_palette
        return get_color_palette()

    @property
    def typo(self):
        """
        Retorna sistema de tipografia

        Returns:
            Instância de Typography (do design_tokens)

        Deprecated:
            Prefira usar TYPO diretamente:
            >>> from consumo_lib.ui import TYPO
            >>> TYPO.BODY_MEDIUM
        """
        # Import local para evitar circular import
        from consumo_lib.ui.design_tokens import Typography
        return Typography()


# =============================================================================
# SINGLETON PATTERN
# =============================================================================

_instance: Optional[ThemeManager] = None


def init_theme_manager(app: QApplication, theme: Optional[str] = None) -> ThemeManager:
    """
    Inicializa ThemeManager global

    Args:
        app: Instância da QApplication
        theme: Tema inicial ("light" | "dark" | "system").
               Se None, lê do config/aoi_config.json ou usa "light" como padrão.

    Returns:
        ThemeManager inicializado

    Raises:
        ValueError: Se app for None
        TypeError: Se app não for QApplication

    Note:
        Esta função deve ser chamada apenas uma vez no startup da aplicação.
        Chamadas subsequentes retornarão a mesma instância.

    Example:
        >>> import sys
        >>> from PyQt6.QtWidgets import QApplication
        >>> from consumo_lib.ui.theme_manager import init_theme_manager
        >>>
        >>> app = QApplication(sys.argv)
        >>> theme_mgr = init_theme_manager(app)
        >>> print(f"Tema atual: {theme_mgr.current_theme}")
        >>>
        >>> # Ou especificar tema explicitamente
        >>> theme_mgr = init_theme_manager(app, theme="dark")
    """
    global _instance

    if app is None:
        raise ValueError("app não pode ser None")

    if not isinstance(app, QApplication):
        raise TypeError(f"app deve ser QApplication, não {type(app)}")

    if _instance is None:
        # Determinar tema inicial
        if theme is None:
            # Tentar ler do config
            theme = _load_theme_from_config()
            if theme is None:
                theme = "light"  # Padrão

        logger.info(f"🎨 Inicializando ThemeManager global com tema: {theme}")
        _instance = ThemeManager(app, initial_theme=theme)
    else:
        logger.warning("⚠️ ThemeManager já foi inicializado (retornando instância existente)")

    return _instance


def _load_theme_from_config() -> Optional[str]:
    """
    Lê configuração de tema do aoi_config.json

    Returns:
        "light", "dark", "system" ou None se não configurado/erro
    """
    try:
        from aoi_lib.config_manager import AOIConfigManager

        config_mgr = AOIConfigManager()
        theme = config_mgr.get("ui", "theme", default=None)

        if theme is not None:
            valid_themes = ["light", "dark", "system"]

            if theme in valid_themes:
                logger.info(f"✅ Tema carregado do config: {theme}")
                return theme
            else:
                logger.warning(f"⚠️ Tema inválido no config: '{theme}'. Usando 'light'")
                return "light"
        else:
            logger.debug("Chave ui.theme não encontrada no config")
            return None

    except Exception as e:
        logger.warning(f"⚠️ Erro ao ler tema do config: {e}")
        return None


def get_theme_manager() -> Optional[ThemeManager]:
    """
    Retorna instância singleton do ThemeManager

    Returns:
        ThemeManager se inicializado, None caso contrário

    Example:
        >>> from consumo_lib.ui.theme_manager import get_theme_manager
        >>>
        >>> theme_mgr = get_theme_manager()
        >>> if theme_mgr:
        >>>     print(f"Tema atual: {theme_mgr.current_theme}")
        >>> else:
        >>>     print("ThemeManager não foi inicializado")
    """
    return _instance


__all__ = [
    "ThemeManager",
    "init_theme_manager",
    "get_theme_manager",
]
