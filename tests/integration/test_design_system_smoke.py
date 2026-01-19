"""
Smoke Test - Design System (Simplificado)

Teste rápido para validar que o Design System está funcionando corretamente.
Executado ao final de cada fase para detectar regressões precocemente.

Versão simplificada que não requer consumo_lib instalado como pacote.
"""

import sys
from pathlib import Path

# Adiciona diretório raiz ao sys.path
# Arquivo está em tests/integration/, então precisamos subir 3 níveis
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# Adiciona consumo_lib/ui ao path
ui_dir = root_dir / "consumo_lib" / "ui"
if str(ui_dir) not in sys.path:
    sys.path.insert(0, str(ui_dir))


def test_design_tokens_import():
    """Testa se todos os design tokens podem ser importados"""
    print("\n[TEST] Test 1: Import Design Tokens...")
    try:
        from design_tokens import (
            ColorPalette,
            COLORS,
            Typography,
            TYPO,
            Spacing,
            SPACE,
            Dimensions,
            DIM,
            Elevation,
            ELEV,
            Opacity,
            OPAC,
            Transitions,
            TRANS,
            Breakpoints,
            BREAK,
            Accessibility,
            A11Y,
        )
        print("   [OK] Todos os tokens importados com sucesso")
        return True
    except Exception as e:
        print(f"   [FAIL] Falha ao importar tokens: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_design_tokens_values():
    """Testa se os tokens têm valores corretos"""
    print("\n[TEST] Test 2: Validar valores dos tokens...")
    try:
        from design_tokens import COLORS, TYPO, SPACE, DIM

        # Testar cores
        assert COLORS.PRIMARY == "#4CAF50", "PRIMARY color incorreta"
        assert COLORS.SUCCESS == "#2ecc71", "SUCCESS color incorreta"
        assert COLORS.ERROR == "#e74c3c", "ERROR color incorreta"

        # Testar tipografia
        assert TYPO.BODY_MEDIUM == 14, "BODY tamanho incorreto"
        font = TYPO.get_font(14, bold=True)
        assert font.pointSize() == 14, "Font size incorreto"
        assert font.bold() is True, "Font bold incorreto"

        # Testar espaçamentos
        assert SPACE.MD == 16, "MD spacing incorreto"

        # Testar dimensões
        assert DIM.BUTTON_HEIGHT_MD == 40, "BUTTON_HEIGHT_MD incorreto"

        print("   [OK] Todos os tokens validados")
        return True
    except AssertionError as e:
        print(f"   [FAIL] Validacao falhou: {e}")
        return False
    except Exception as e:
        print(f"   [FAIL] Erro ao validar: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_stylesheet_exists():
    """Testa se o arquivo styles.qss existe"""
    print("\n[TEST] Test 3: Arquivo styles.qss...")
    try:
        styles_path = root_dir / "consumo_lib" / "ui" / "styles.qss"
        if not styles_path.exists():
            print(f"   [FAIL] Arquivo não encontrado: {styles_path}")
            return False

        # Verificar tamanho mínimo
        content = styles_path.read_text(encoding='utf-8')
        if len(content) < 500:
            print(f"   [FAIL] Arquivo muito pequeno: {len(content)} bytes")
            return False

        print(f"   [OK] Arquivo encontrado ({len(content)} bytes)")
        return True
    except Exception as e:
        print(f"   [FAIL] Erro ao verificar arquivo: {e}")
        return False


def test_theme_manager_import():
    """Testa se ThemeManager pode ser importado"""
    print("\n[TEST] Test 4: Import Theme Manager...")
    try:
        from theme_manager import (
            ThemeManager,
            init_theme_manager,
            get_theme_manager,
        )
        print("   [OK] ThemeManager importado com sucesso")
        return True
    except Exception as e:
        print(f"   [FAIL] Falha ao importar ThemeManager: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Executa todos os smoke tests"""
    print("=" * 60)
    print("DESIGN SYSTEM - SMOKE TEST")
    print("=" * 60)
    print(f"Diretorio: {Path.cwd()}")
    print(f"Python: {sys.version.split()[0]}")

    tests = [
        ("Import Design Tokens", test_design_tokens_import),
        ("Validar Valores dos Tokens", test_design_tokens_values),
        ("Arquivo styles.qss", test_stylesheet_exists),
        ("Import Theme Manager", test_theme_manager_import),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        if test_func():
            passed += 1
        else:
            failed += 1

    print("\n" + "=" * 60)
    print(f"[RESULT] RESULTADOS: {passed} passaram, {failed} falharam")
    print("=" * 60)

    if failed == 0:
        print("\n[OK] TODOS OS TESTES PASSARAM! Design System está funcionando corretamente.")
        return 0
    else:
        print(f"\n[FAIL] {failed} TESTE(S) FALHARAM! Revise os erros acima.")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
