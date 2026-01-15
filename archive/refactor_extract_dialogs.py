#!/usr/bin/env python3
"""
Script para extrair WidthHeightDialog de mainwindow.py
"""

import re
from pathlib import Path


def extract_dialogs():
    """Extrai WidthHeightDialog para módulo separado."""

    project_root = Path(__file__).parent
    mainwindow_path = project_root / "aoi_lib" / "gerber_core" / "gui" / "mainwindow.py"

    # Read file
    with open(mainwindow_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # ========================================================================
    # 1. Remove WidthHeightDialog class (lines 41-262)
    # ========================================================================

    # Pattern to match the entire WidthHeightDialog class
    dialog_pattern = r'class WidthHeightDialog\(QDialog\):.*?(?=\nclass GerberMacroViewer)'

    # Remove the class
    content = re.sub(dialog_pattern, '', content, flags=re.DOTALL)

    # ========================================================================
    # 2. Add import for dialogs
    # ========================================================================

    import_pattern = r'(from \.preview import PreviewGraphicsView)'

    import_replacement = r'''from .dialogs import WidthHeightDialog
\\1'''

    if "from .dialogs import WidthHeightDialog" not in content:
        content = re.sub(import_pattern, import_replacement, content)

    # ========================================================================
    # 3. Remove unused imports (now in dialogs.py)
    # ========================================================================

    # Remove QDoubleSpinBox, QCheckBox, QHBoxLayout, QPushButton from imports
    # if they are only used in WidthHeightDialog
    unused_imports_pattern = r'(    QDoubleSpinBox,\n    QCheckBox,\n    QHBoxLayout,)\n    (QPushButton,)'

    # Check if these are used elsewhere (besides WidthHeightDialog)
    # If not, remove them
    qdialog_import = r'    QDialog,\n    QDialogButtonBox,\n    QFormLayout,'

    # We need to be careful here - QDialog, QDialogButtonBox, QFormLayout might be used elsewhere
    # Let's keep them in mainwindow.py for now, as they might be needed

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
    print("Extraindo WidthHeightDialog de mainwindow.py")
    print("=" * 70)
    print()

    try:
        extract_dialogs()
        print("\n[OK] Extracao concluida!")
    except Exception as e:
        print(f"\n[ERRO] {e}")
        import traceback
        traceback.print_exc()
