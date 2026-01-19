"""
Gerenciador de Temas - Tensiometro

Gerencia aplicação de temas e estilos globais.
"""

from typing import Optional
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, QFile
import logging

logger = logging.getLogger(__name__)


class ThemeManager(QObject):
    """
    Gerenciador central de temas e estilos

    Features:
        - Aplicar stylesheet global
        - Alternar temas (light/dark/custom)
        - Atualizar tokens de design dinamicamente
        - Carregar estilos de arquivo .qss

    Usage:
        >>> from consumo_lib.ui.theme_manager import init_theme_manager
        >>> app = QApplication(sys.argv)
        >>> theme_mgr = init_theme_manager(app)
        >>> # Stylesheet aplicado automaticamente
    """

    def __init__(self, app: QApplication):
        """
        Inicializa gerenciador de temas

        Args:
            app: Instância da QApplication
        """
        super().__init__()
        self.app = app
        self.current_theme = "light"
        self._load_stylesheet()

    def _load_stylesheet(self):
        """
        Carrega stylesheet global do arquivo styles.qss
        """
        try:
            # Tenta carregar do arquivo
            from importlib.resources import read_text
            stylesheet = read_text("consumo_lib.ui", "styles.qss")

            # Aplica stylesheet
            self.app.setStyleSheet(stylesheet)
            logger.info("✅ Stylesheet global carregado com sucesso (consumo_lib/ui/styles.qss)")

        except Exception as e:
            logger.warning(f"⚠️ Falha ao carregar stylesheet: {e}")
            logger.warning("   Usando estilos padrão do Qt")
            # Não re-raise - permitir que app rode sem stylesheet

    def set_theme(self, theme_name: str):
        """
        Altera tema atual

        Args:
            theme_name: Nome do tema (light | dark | high_contrast)

        Note:
            Apenas 'light' está implementado no momento.
            'dark' e 'high_contrast' são placeholders para futuro.
        """
        if theme_name == self.current_theme:
            logger.debug(f"Tema {theme_name} já está ativo")
            return

        logger.info(f"🎨 Alterando tema para: {theme_name}")
        self.current_theme = theme_name
        self._apply_theme(theme_name)

    def _apply_theme(self, theme_name: str):
        """
        Aplica configurações específicas do tema

        Args:
            theme_name: Nome do tema
        """
        if theme_name == "dark":
            # TODO: Implementar dark mode
            logger.warning("⚠️ Dark mode ainda não implementado (usando light)")
            self._load_stylesheet()

        elif theme_name == "high_contrast":
            # TODO: Implementar high contrast mode
            logger.warning("⚠️ High contrast mode ainda não implementado (usando light)")
            self._load_stylesheet()

        elif theme_name == "light":
            # Tema padrão (já carregado)
            self._load_stylesheet()

        else:
            logger.warning(f"⚠️ Tema desconhecido: {theme_name} (usando light)")
            self._load_stylesheet()

    @property
    def colors(self):
        """
        Retorna paleta de cores do tema atual

        Returns:
            Instância de ColorPalette (do design_tokens)
        """
        # Import local para evitar circular import
        from .design_tokens import ColorPalette
        return ColorPalette()

    @property
    def typo(self):
        """
        Retorna sistema de tipografia

        Returns:
            Instância de Typography (do design_tokens)
        """
        # Import local para evitar circular import
        from .design_tokens import Typography
        return Typography()


# =============================================================================
# SINGLETON PATTERN
# =============================================================================

_instance: Optional[ThemeManager] = None


def init_theme_manager(app: QApplication) -> ThemeManager:
    """
    Inicializa ThemeManager global

    Args:
        app: Instância da QApplication

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
    """
    global _instance

    if app is None:
        raise ValueError("app não pode ser None")

    if not isinstance(app, QApplication):
        raise TypeError(f"app deve ser QApplication, não {type(app)}")

    if _instance is None:
        logger.info("🎨 Inicializando ThemeManager global")
        _instance = ThemeManager(app)
    else:
        logger.warning("⚠️ ThemeManager já foi inicializado (retornando instância existente)")

    return _instance


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
