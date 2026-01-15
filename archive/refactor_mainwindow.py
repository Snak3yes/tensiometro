#!/usr/bin/env python3
"""
Script para refatorar mainwindow.py usando ObjectEditor.

Este script modifica o mainwindow.py para delegar as operações
de edição de objetos para a classe ObjectEditor.
"""

import re
from pathlib import Path


def refactor_mainwindow():
    """Refatora mainwindow.py para usar ObjectEditor."""

    project_root = Path(__file__).parent
    mainwindow_path = project_root / "aoi_lib" / "gerber_core" / "gui" / "mainwindow.py"

    # Backup
    backup_path = mainwindow_path.with_suffix(".py.backup2")
    if not backup_path.exists():
        import shutil
        shutil.copy2(mainwindow_path, backup_path)
        print(f"✅ Backup criado: {backup_path}")

    # Read file
    with open(mainwindow_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # ========================================================================
    # 1. Replace on_edit_object method
    # ========================================================================

    on_edit_object_pattern = r'(    def on_edit_object\(self, index: int\):.*?)(        # Atualizar objeto na lista se modificação foi bem-sucedida\s+if modified_obj is not None:\s+self\._full_layer_objects\[index\] = modified_obj\s+self\._refresh_preview\(\))'

    on_edit_object_replacement = r'''    def on_edit_object(self, index: int):
        """
        Edita propriedades geométricas de um objeto simples.

        REFATORADO: Usa ObjectEditor para separar responsabilidades.
        """
        if self._full_layer_objects is None:
            print("[DEBUG edit] _full_layer_objects is None")
            return
        if not (0 <= index < len(self._full_layer_objects)):
            print(
                f"[DEBUG edit] index fora do intervalo: "
                f"idx={index}, n={len(self._full_layer_objects)}"
            )
            return

        obj = self._full_layer_objects[index]

        # Delegate to ObjectEditor
        modified_obj = self.object_editor.edit_object(
            obj=obj,
            index=index,
            objects_list=self._full_layer_objects,
        )

        # Update object in list if modification was successful
        if modified_obj is not None:
            self._full_layer_objects[index] = modified_obj
            self._refresh_preview()'''

    content = re.sub(
        on_edit_object_pattern,
        on_edit_object_replacement,
        content,
        flags=re.DOTALL,
    )

    # ========================================================================
    # 2. Replace on_edit_many_objects method
    # ========================================================================

    on_edit_many_pattern = r'(    def on_edit_many_objects\(self, indices: list\[int\]\):.*?)(        # Atualiza preview\s+self\._refresh_preview\(\))'

    on_edit_many_replacement = r'''    def on_edit_many_objects(self, indices: list[int]):
        """
        Edição em grupo usando ObjectEditor.

        REFATORADO: Usa ObjectEditor para separar responsabilidades.
        """
        if self._full_layer_objects is None:
            return
        if not indices:
            return

        # Delegate to ObjectEditor
        success = self.object_editor.edit_many_objects(
            indices=indices,
            objects_list=self._full_layer_objects,
        )

        if success:
            self._refresh_preview()'''

    content = re.sub(
        on_edit_many_pattern,
        on_edit_many_replacement,
        content,
        flags=re.DOTALL,
    )

    # ========================================================================
    # 3. Replace on_delete_object method
    # ========================================================================

    on_delete_pattern = r'(    def on_delete_object\(self, index: int\):.*?)(        # Se não sobrou nada, limpa a tela\s+if not self\._full_layer_objects:\s+self\._clear_preview\(\)\s+return\s+\s+# Caso contrário, re-renderiza a partir da lista atualizada\s+self\.preview_view\.set_objects\()'

    on_delete_replacement = r'''    def on_delete_object(self, index: int):
        """
        Remove um objeto Gerber da camada atual.

        REFATORADO: Usa ObjectEditor para separar responsabilidades.
        """
        if self._full_layer_objects is None:
            return

        if not (0 <= index < len(self._full_layer_objects)):
            return

        # Delegate to ObjectEditor
        deleted = self.object_editor.delete_object(
            index=index,
            objects_list=self._full_layer_objects,
        )

        if not deleted:
            return

        # Update polygon list
        self._full_layer_polys_mm = [
            o.polygon_mm
            for o in self._full_layer_objects
            if o.polygon_mm and len(o.polygon_mm) >= 3
        ]

        # If nothing left, clear screen
        if not self._full_layer_objects:
            self._clear_preview()
            return

        # Otherwise, re-render from updated list
        self.preview_view.set_objects('''

    content = re.sub(
        on_delete_pattern,
        on_delete_replacement,
        content,
        flags=re.DOTALL,
    )

    # ========================================================================
    # 4. Replace on_delete_many_objects method
    # ========================================================================

    on_delete_many_pattern = r'(    def on_delete_many_objects\(self, indices: list\[int\]\):.*?)(        self\.preview_view\.set_objects\()'

    on_delete_many_replacement = r'''    def on_delete_many_objects(self, indices: list[int]):
        """
        Remove vários objetos Gerber de uma vez.

        REFATORADO: Usa ObjectEditor para separar responsabilidades.
        """
        if self._full_layer_objects is None:
            return
        if not indices:
            return

        # Delegate to ObjectEditor
        deleted = self.object_editor.delete_many_objects(
            indices=indices,
            objects_list=self._full_layer_objects,
        )

        if not deleted:
            return

        # Update polygon list
        if not self._full_layer_objects:
            self._clear_preview()
            return

        self._full_layer_polys_mm = [
            o.polygon_mm
            for o in self._full_layer_objects
            if o.polygon_mm and len(o.polygon_mm) >= 3
        ]

        self.preview_view.set_objects('''

    content = re.sub(
        on_delete_many_pattern,
        on_delete_many_replacement,
        content,
        flags=re.DOTALL,
    )

    # ========================================================================
    # 5. Remove private methods that are now in ObjectEditor
    # ========================================================================

    # Methods to remove completely (now in ObjectEditor):
    methods_to_remove = [
        r'    def _edit_rectangle_or_oval_group\(self.*?\n.*?(?=\n    def |\n    # |\nclass |\Z)',
        r'    def _edit_region_group\(self.*?\n.*?(?=\n    def |\n    # |\nclass |\Z)',
        r'    def _move_object\(self.*?\n.*?(?=\n    def |\n    # |\nclass |\Z)',
        r'    def _move_objects\(self.*?\n.*?(?=\n    def |\n    # |\nclass |\Z)',
    ]

    # Note: We'll keep _refresh_preview and _clear_preview as they're UI-related

    # ========================================================================
    # 6. Write modified file
    # ========================================================================

    if content != original_content:
        with open(mainwindow_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Arquivo modificado: {mainwindow_path}")

        # Count lines
        original_lines = original_content.count('\n')
        new_lines = content.count('\n')
        reduction = original_lines - new_lines
        percentage = (reduction / original_lines) * 100

        print(f"\n📊 Estatísticas:")
        print(f"   Linhas originais: {original_lines}")
        print(f"   Linhas após refatoração: {new_lines}")
        print(f"   Redução: -{reduction} linhas ({percentage:.1f}%)")

        return True
    else:
        print("⚠️ Nenhuma modificação necessária.")
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("Refatorando mainwindow.py para usar ObjectEditor")
    print("=" * 70)
    print()

    try:
        success = refactor_mainwindow()

        if success:
            print("\n✅ Refatoração concluída com sucesso!")
            print("\n📝 Próximos passos:")
            print("   1. Testar a aplicação para verificar funcionalidade")
            print("   2. Commit das mudanças")
            print("   3. Continuar com extração do GerberFileManager")
        else:
            print("\nℹ️ Refatoração não foi necessária.")

    except Exception as e:
        print(f"\n❌ Erro durante refatoração: {e}")
        import traceback
        traceback.print_exc()
        print("\n💡 Dica: Restaure o backup manualmente se necessário:")
        print("   cp aoi_lib/gerber_core/gui/mainwindow.py.backup aoi_lib/gerber_core/gui/mainwindow.py")
