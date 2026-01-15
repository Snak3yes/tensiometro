"""
Suite Completa de Testes Unitários - Phase 5B.2

Este script executa todos os testes unitários criados na Phase 5B.2
para validar os services de fiducial alignment.

Author: Claude Code (Sonnet 4.5)
Created: 2026-01-15
Phase: SOLID Refactoring Phase 5B.2
"""

import sys
from pathlib import Path

# Adiciona diretório raiz ao sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import subprocess


def run_test_file(test_file):
    """Executa um arquivo de testes e retorna o resultado"""
    print(f"\n{'='*70}")
    print(f"Executando: {test_file}")
    print('='*70)

    result = subprocess.run(
        [sys.executable, '-m', 'pytest', test_file, '-v', '--tb=short'],
        capture_output=True,
        text=True
    )

    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    return result.returncode == 0


def main():
    """Executa todos os testes unitários"""
    print("\n" + "="*70)
    print("PHASE 5B.2 - SUITE COMPLETA DE TESTES UNITÁRIOS")
    print("="*70)

    test_files = [
        'tests/unit/test_fiducial_matching_service.py',
        'tests/unit/test_alignment_transform_service.py',
        'tests/unit/test_alignment_state_service.py'
    ]

    results = {}

    for test_file in test_files:
        success = run_test_file(test_file)
        results[test_file] = success

    # Resumo final
    print("\n" + "="*70)
    print("RESUMO FINAL DOS TESTES")
    print("="*70)

    total = len(results)
    passed = sum(1 for v in results.values() if v)

    for test_file, success in results.items():
        status = "[PASSOU]" if success else "[FALHOU]"
        print(f"{status} {test_file}")

    print("\n" + "="*70)
    print(f"Total: {passed}/{total} arquivos de teste passaram")

    if passed == total:
        print("\n[SUCCESS] TODOS OS TESTES UNITÁRIOS PASSARAM!")
        print("Phase 5B.2 validada com sucesso!")
        return 0
    else:
        print(f"\n[FAILURE] {total - passed} arquivos de teste falharam")
        return 1


if __name__ == '__main__':
    exit(main())
