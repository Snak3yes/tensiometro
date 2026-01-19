"""
Design System - Tensiometro

Este módulo contém o sistema de design tokens, componentes base e
gerenciador de temas para toda a aplicação Tensiometro.

Módulos:
    - design_tokens: Constantes de design (cores, fontes, espaçamentos)
    - widget_standards: Componentes base padronizados
    - theme_manager: Gerenciador de temas
    - helpers: Funções utilitárias para UI

Uso básico:
    >>> from consumo_lib.ui import COLORS, TYPO, SPACE, DIM
    >>> from consumo_lib.ui.widget_standards import StandardButton
    >>> from consumo_lib.ui.theme_manager import init_theme_manager
    >>>
    >>> # Inicializar tema
    >>> init_theme_manager(app)
    >>>
    >>> # Usar tokens
    >>> btn.setStyleSheet(f"background-color: {COLORS.PRIMARY};")
    >>>
    >>> # Usar componentes padrão
    >>> btn = StandardButton("Salvar", variant="primary")
"""

# Design tokens (implementados na Fase 1)
from .design_tokens import (
    COLORS,
    TYPO,
    SPACE,
    DIM,
    ELEV,
    OPAC,
    TRANS,
    BREAK,
    A11Y,
)

# Componentes base serão exportados aqui quando implementados
# from .widget_standards import (
#     StandardButton,
#     StandardLabel,
#     StandardInput,
#     StandardComboBox,
#     StandardGroupBox
# )

# Theme manager será exportado aqui quando implementado
# from .theme_manager import init_theme_manager, get_theme_manager

# Helpers serão exportados aqui quando implementados
# from .helpers import (
#     create_h_spacer,
#     create_v_spacer,
#     add_spacing,
#     create_separator,
#     apply_standard_spacing
# )

__version__ = "1.0.0"
__author__ = "RONALDBUZAGLO"

__all__ = [
    "COLORS",
    "TYPO",
    "SPACE",
    "DIM",
    "ELEV",
    "OPAC",
    "TRANS",
    "BREAK",
    "A11Y",
]  # Será preenchido conforme módulos forem implementados
