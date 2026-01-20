# -*- coding: utf-8 -*-
"""
recipe_dialog.py
-----------------
Diálogos PyQt6 para gerenciamento de receitas de stencil.

⚠️  DEPRECATED (2026-01-16) ⚠️
-------------------------------
Este arquivo foi refatorado aplicando Single Responsibility Principle (SRP).
O conteúdo foi movido para `consumo_lib/dialogs/recipe/`.

NOVA ESTRUTURA:
- consumo_lib/dialogs/recipe/recipe_list_widget.py
- consumo_lib/dialogs/recipe/recipe_edit_dialog.py
- consumo_lib/dialogs/recipe/recipe_manager_dialog.py

BACKWARD COMPATIBILITY:
----------------------
Este arquivo ainda funciona IMPORTANDO do novo local.
Use o novo import para código futuro:

  NOVO (recomendado):
    from consumo_lib.dialogs.recipe import RecipeManagerDialog

  ANTIGO (ainda funciona):
    from consumo_lib.dialogs.recipe_dialogs import RecipeManagerDialog

Autor: Sistema AOI Tensiometro
Data: 2024-12-10 (Refatorado: 2026-01-16)
"""

# Reexportar do novo local para backward compatibility
from consumo_lib.dialogs.recipe import (
    RecipeListWidget,
    RecipeEditorDialog,
    RecipeManagerDialog
)

__all__ = [
    'RecipeListWidget',
    'RecipeEditorDialog',
    'RecipeManagerDialog',
]
