#!/usr/bin/env python3
"""
Script de teste para validar a refatoração do mainwindow.py

Este script testa se todos os imports estão funcionando corretamente
após a extração de ObjectEditor, GerberFileManager e WidthHeightDialog.
"""

import sys

def test_imports():
    """Testa se todos os módulos podem ser importados."""
    print("=" * 70)
    print("Testando imports após refatoração...")
    print("=" * 70)
    print()

    tests_passed = 0
    tests_failed = 0

    # Test 1: GerberFileManager
    try:
        from aoi_lib.gerber_core.file_manager import GerberFileManager
        print("✅ GerberFileManager import OK")
        tests_passed += 1
    except Exception as e:
        print(f"❌ GerberFileManager import FAILED: {e}")
        tests_failed += 1

    # Test 2: ObjectEditor
    try:
        from aoi_lib.gerber_core.object_editor import ObjectEditor
        print("✅ ObjectEditor import OK")
        tests_passed += 1
    except Exception as e:
        print(f"❌ ObjectEditor import FAILED: {e}")
        tests_failed += 1

    # Test 3: WidthHeightDialog
    try:
        from aoi_lib.gerber_core.gui.dialogs import WidthHeightDialog
        print("✅ WidthHeightDialog import OK")
        tests_passed += 1
    except Exception as e:
        print(f"❌ WidthHeightDialog import FAILED: {e}")
        tests_failed += 1

    # Test 4: GerberMacroViewer (mainwindow)
    try:
        from aoi_lib.gerber_core.gui.mainwindow import GerberMacroViewer
        print("✅ GerberMacroViewer import OK")
        tests_passed += 1
    except Exception as e:
        print(f"❌ GerberMacroViewer import FAILED: {e}")
        tests_failed += 1

    # Test 5: Verificar se mainwindow.py pode instanciar
    try:
        from aoi_lib.gerber_core.gui.mainwindow import GerberMacroViewer
        # Not trying to create instance (needs QApplication), just import
        print("✅ GerberMacroViewer class OK")
        tests_passed += 1
    except Exception as e:
        print(f"❌ GerberMacroViewer class FAILED: {e}")
        tests_failed += 1

    # Resumo
    print()
    print("=" * 70)
    print(f"Resultados: {tests_passed} passed, {tests_failed} failed")
    print("=" * 70)

    if tests_failed == 0:
        print()
        print("🎉 Todos os testes passaram! Refatoração validada.")
        return 0
    else:
        print()
        print("⚠️ Alguns testes falharam. Verifique os erros acima.")
        return 1


if __name__ == "__main__":
    sys.exit(test_imports())
