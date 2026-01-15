#!/usr/bin/env python3
"""
Script para remover métodos privados duplicados do mainwindow.py
"""

import re
from pathlib import Path


def cleanup_duplicate_methods():
    """Remove métodos privados que agora estão no ObjectEditor."""

    project_root = Path(__file__).parent
    mainwindow_path = project_root / "aoi_lib" / "gerber_core" / "gui" / "mainwindow.py"

    # Read file
    with open(mainwindow_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # ========================================================================
    # 1. Remove _edit_rectangle_or_oval_group method
    # ========================================================================

    # This method is now in ObjectEditor
    edit_oval_pattern = r'    def _edit_rectangle_or_oval_group\(self.*?(?=\n    def |\n\nclass|\Z)'

    # Need to be careful - find the exact method
    lines = content.split('\n')
    new_lines = []
    skip = False
    indent_level = None

    for i, line in enumerate(lines):
        if '    def _edit_rectangle_or_oval_group(' in line:
            skip = True
            indent_level = len(line) - len(line.lstrip())
            continue
        elif skip:
            # Check if we've exited the method
            current_indent = len(line) - len(line.lstrip()) if line.strip() else indent_level + 4
            if line.strip() and current_indent <= indent_level:
                skip = False
                new_lines.append(line)
            # else: skip this line (it's part of the method being removed)
        else:
            new_lines.append(line)

    content = '\n'.join(new_lines)

    # ========================================================================
    # 2. Remove _edit_region_group method
    # ========================================================================

    lines = content.split('\n')
    new_lines = []
    skip = False

    for i, line in enumerate(lines):
        if '    def _edit_region_group(' in line:
            skip = True
            indent_level = len(line) - len(line.lstrip())
            continue
        elif skip:
            current_indent = len(line) - len(line.lstrip()) if line.strip() else indent_level + 4
            if line.strip() and current_indent <= indent_level:
                skip = False
                new_lines.append(line)
        else:
            new_lines.append(line)

    content = '\n'.join(new_lines)

    # ========================================================================
    # 3. Remove _move_object and _move_objects methods
    # ========================================================================

    lines = content.split('\n')
    new_lines = []
    skip = False

    for i, line in enumerate(lines):
        if '    def _move_object(' in line or '    def _move_objects(' in line:
            skip = True
            indent_level = len(line) - len(line.lstrip())
            continue
        elif skip:
            current_indent = len(line) - len(line.lstrip()) if line.strip() else indent_level + 4
            if line.strip() and current_indent <= indent_level:
                skip = False
                new_lines.append(line)
        else:
            new_lines.append(line)

    content = '\n'.join(new_lines)

    # ========================================================================
    # 4. Update callbacks to use object_editor instead of self
    # ========================================================================

    # Replace lambda callbacks that reference self._move_objects
    content = re.sub(
        r'move_callback=lambda dx, dy, objs=objs: self\._move_objects\(',
        r'move_callback=lambda dx, dy, objs=objs: self.object_editor._move_objects(',
        content
    )

    # ========================================================================
    # Write modified file
    # ========================================================================

    if content != original_content:
        with open(mainwindow_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # Count lines
        original_lines = original_content.count('\n')
        new_lines = content.count('\n')
        reduction = original_lines - new_lines
        percentage = (reduction / original_lines) * 100

        print(f"[OK] Arquivo modificado: {mainwindow_path.name}")
        print(f"     Linhas originais: {original_lines}")
        print(f"     Linhas apos: {new_lines}")
        print(f"     Reducao: -{reduction} linhas ({percentage:.1f}%)")

        return True
    else:
        print("[INFO] Nenhuma modificacao necessaria.")
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("Limpando metodos duplicados do mainwindow.py")
    print("=" * 70)
    print()

    try:
        cleanup_duplicate_methods()
        print("\n[OK] Limpeza concluida!")
    except Exception as e:
        print(f"\n[ERRO] {e}")
        import traceback
        traceback.print_exc()
