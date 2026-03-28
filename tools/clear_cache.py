#!/usr/bin/env python3
"""
Script de Limpeza de Cache Python

Remove todos os caches __pycache__ e arquivos .pyc do projeto
(excluindo .venv para nao afetar pacotes instalados).

Use quando:
- Primeira execucao falha com KeyboardInterrupt
- Mudanca de versao Python
- Problemas de importacao estranhos

Uso:
    python tools/clear_cache.py
"""

import shutil
from pathlib import Path


def clear_cache():
    """Remove todos os caches Python do projeto."""
    project_root = Path(__file__).resolve().parent.parent

    print(f"Limpando cache em: {project_root}")

    # Contadores
    dirs_removed = 0
    files_removed = 0

    # Remover __pycache__ directories (exceto .venv)
    for dirpath in project_root.rglob("__pycache__"):
        # Ignorar .venv
        if ".venv" in str(dirpath) or "venv" in str(dirpath):
            continue

        try:
            shutil.rmtree(dirpath)
            dirs_removed += 1
            print(f"  Removido: {dirpath.relative_to(project_root)}")
        except Exception as e:
            print(f"  Erro: {dirpath} - {e}")

    # Remover arquivos .pyc (exceto .venv)
    for filepath in project_root.rglob("*.pyc"):
        # Ignorar .venv
        if ".venv" in str(filepath) or "venv" in str(filepath):
            continue

        try:
            filepath.unlink()
            files_removed += 1
        except Exception as e:
            print(f"  Erro: {filepath} - {e}")

    print(f"\n[OK] Limpeza concluida:")
    print(f"   Diretorios __pycache__ removidos: {dirs_removed}")
    print(f"   Arquivos .pyc removidos: {files_removed}")

    return dirs_removed + files_removed


if __name__ == "__main__":
    total = clear_cache()
    if total == 0:
        print("\nNenhum cache encontrado para limpar.")