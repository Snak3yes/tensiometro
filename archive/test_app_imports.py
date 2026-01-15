#!/usr/bin/env python3
"""
Script simples para testar se o aplicativo pode ser importado
após a correção dos imports de TensionMeasurementDialog.
"""

import sys

def test_main_imports():
    """Testa se os módulos principais podem ser importados."""
    print("=" * 70)
    print("Testando imports do aplicativo principal...")
    print("=" * 70)
    print()

    # Test 1: TensionMeasurementDialog (novo caminho)
    try:
        from consumo_lib.dialogs.tension import TensionMeasurementDialog
        print("✅ TensionMeasurementDialog (NOVO) import OK")
    except Exception as e:
        print(f"❌ TensionMeasurementDialog import FAILED: {e}")
        return False

    # Test 2: StencilTensionDialog (alias - compatibilidade)
    try:
        from consumo_lib.dialogs import StencilTensionDialog
        print("✅ StencilTensionDialog (ALIAS) import OK")
    except Exception as e:
        print(f"❌ StencilTensionDialog import FAILED: {e}")
        return False

    # Test 3: MainWindow (se conseguir importar, todos os outros imports estão OK)
    try:
        from consumo_lib.main_window import AOIControllerApp
        print("✅ AOIControllerApp import OK")
    except Exception as e:
        print(f"❌ AOIControllerApp import FAILED: {e}")
        return False

    print()
    print("=" * 70)
    print("🎉 Todos os imports principais estão OK!")
    print("=" * 70)
    print()
    print("Você pode agora executar: python main.py")
    return True


if __name__ == "__main__":
    success = test_main_imports()
    sys.exit(0 if success else 1)
