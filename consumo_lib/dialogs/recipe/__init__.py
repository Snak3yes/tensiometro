# -*- coding: utf-8 -*-
"""
Recipe Dialogs - Diálogos para gerenciamento de receitas

Este pacote contém 3 diálogos PyQt6 para gerenciamento de receitas:
- RecipeListWidget: Lista e seleciona receitas
- RecipeEditorDialog: Cria/edita receitas
- RecipeManagerDialog: Gerencia receitas (CRUD completo)

Backward Compatibility:
----------------------
Importar de `consumo_lib.dialogs.recipe_dialogs` AINDA funciona
via reexportação neste arquivo.

Uso Recomendado (NOVO):
----------------------
from consumo_lib.dialogs.recipe import RecipeManagerDialog

Uso Legacy (AINDA FUNCIONA):
----------------------------
from consumo_lib.dialogs.recipe_dialogs import RecipeManagerDialog

Autor: Sistema AOI Tensiometro
Data: 2026-01-16 (Refatorado de recipe_dialogs.py)
"""

from consumo_lib.dialogs.recipe.recipe_list_widget import RecipeListWidget
from consumo_lib.dialogs.recipe.recipe_edit_dialog import RecipeEditorDialog
from consumo_lib.dialogs.recipe.recipe_manager_dialog import RecipeManagerDialog

__all__ = [
    'RecipeListWidget',
    'RecipeEditorDialog',
    'RecipeManagerDialog',
]
