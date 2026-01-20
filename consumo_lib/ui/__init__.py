"""
⚠️⚠️⚠️ REGRA CRÍTICA: PROIBIÇÃO DE ESTILOS INLINE/HARDCODED ⚠️⚠️⚠️

Design System - Fonte ÚNICA de Verdade para Estilos

❌ COMPLETAMENTE PROIBIDO em qualquer lugar da aplicação:
   - .setStyleSheet() inline em código Python (use styles.qss.template + widget_standards.py)
   - Estilo local (definir styles em arquivos Python fora deste módulo ui/)
   - Estilo hardcoded (valores mágicos como "#4CAF50", setMinimumHeight(45))
   - Estilo mágico (números sem contexto ou semântica clara)

✅ SEMPRE USE ESTE MÓDULO PARA TUDO RELACIONADO A UI:
   - from consumo_lib.ui import COLORS, TYPO, SPACE, DIM (design tokens)
   - from consumo_lib.ui.widget_standards import StandardButton, StandardLabel, etc.
   - from consumo_lib.ui.theme_manager import init_theme_manager (aplicar stylesheet global)

✅ SE PRECISA DE ESTILO NOVO:
   - Para componentes: Crie classe herdada de widget_standards.py
   - Para tokens: Adicione em design_tokens.py
   - Para estilos globais: Adicione em styles.qss.template usando {{TOKEN}}

⚠️ ESTA REGRA NÃO PODE SER BURLADA - Code review irá rejeitar violações
⚠️⚠️⚠️ FIM DA REGRA CRÍTICA ⚠️⚠️⚠️

Design System - Tensiometro

Este módulo contém o sistema de design tokens, componentes base e
gerenciador de temas para toda a aplicação Tensiometro.

Módulos:
    - design_tokens: Constantes de design (cores, fontes, espaçamentos)
    - themes: Paletas de cores para Light/Dark/System themes
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
    >>>
    >>> # Mudar tema (se ThemeManager estiver inicializado)
    >>> from consumo_lib.ui.theme_manager import get_theme_manager
    >>> mgr = get_theme_manager()
    >>> mgr.set_theme("dark")  # Cores atualizam automaticamente
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

# Componentes base (implementados na Fase 1)
from .widget_standards import (
    StandardButton,
    StandardLabel,
    StandardInput,
    StandardSpinBox,
    StandardDoubleSpinBox,
    StandardComboBox,
    StandardGroupBox,
)

# Theme manager (implementado na Fase 2)
from .theme_manager import init_theme_manager, get_theme_manager

# Themes system (implementado na Fase 3 - Multi-theme support)
from .themes import (
    ThemeType,
    LightThemePalette,
    DarkThemePalette,
    ThemePaletteFactory,
    to_qcolor,
    get_status_color,
)

# Helpers (implementados na Fase 1)
from .helpers import (
    create_h_spacer,
    create_v_spacer,
    add_spacing,
    create_separator,
    apply_standard_spacing,
)

__version__ = "1.0.0"
__author__ = "RONALDBUZAGLO"

__all__ = [
    # Design tokens
    "COLORS",
    "TYPO",
    "SPACE",
    "DIM",
    "ELEV",
    "OPAC",
    "TRANS",
    "BREAK",
    "A11Y",
    # Themes system
    "ThemeType",
    "LightThemePalette",
    "DarkThemePalette",
    "ThemePaletteFactory",
    "to_qcolor",
    "get_status_color",
    # Componentes base
    "StandardButton",
    "StandardLabel",
    "StandardInput",
    "StandardSpinBox",
    "StandardDoubleSpinBox",
    "StandardComboBox",
    "StandardGroupBox",
    # Theme manager
    "init_theme_manager",
    "get_theme_manager",
    # Helpers
    "create_h_spacer",
    "create_v_spacer",
    "add_spacing",
    "create_separator",
    "apply_standard_spacing",
]  # Será preenchido conforme módulos forem implementados
