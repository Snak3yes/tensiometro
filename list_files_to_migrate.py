#!/usr/bin/env python
"""Análise consolidada de arquivos que precisam de migração"""

import os
import re
from collections import defaultdict

def find_files_with_problems():
    """Encontra todos os arquivos com qualquer tipo de problema"""

    # Padrões para buscar
    patterns = {
        'cores': r'#([0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})',
        'qfont': r'QFont\(\)',
        'tamanhos': r'set(Minimum|Maximum)?Height\((\d+)\)',
        'pointsize': r'setPointSize\((\d+)\)',
    }

    # Arquivos a ignorar (parte do Design System ou já migrados)
    ignore_files = {
        'design_tokens.py',
        'styles.qss',
        'widget_standards.py',
        'theme_manager.py',
        'helpers.py',
        '__init__.py',
    }

    # Arquivos já migrados
    migrated_files = {
        'status_badge.py',
        'movement_control.py',
    }

    files_with_issues = set()

    # Buscar em consumo_lib
    for root, dirs, files in os.walk('consumo_lib'):
        # Ignorar __pycache__
        dirs[:] = [d for d in dirs if d != '__pycache__']

        for file in files:
            if not file.endswith('.py'):
                continue

            filepath = os.path.join(root, file)
            rel_path = os.path.relpath(filepath)

            # Ignorar arquivos do Design System
            if any(ignore in rel_path for ignore in ignore_files):
                continue

            # Ignorar arquivos já migrados
            if any(migrated in rel_path for migrated in migrated_files):
                continue

            # Verificar se tem algum problema
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Buscar cada padrão
                for pattern_name, pattern in patterns.items():
                    if re.search(pattern, content):
                        # Verificar se não é apenas comentário
                        lines = content.split('\n')
                        has_real_issue = False

                        for line in lines:
                            if re.search(pattern, line) and not line.strip().startswith('#'):
                                # Excluir falsos positivos
                                if 'import' not in line and '"""' not in line and "'''" not in line:
                                    has_real_issue = True
                                    break

                        if has_real_issue:
                            files_with_issues.add(rel_path)
                            break

            except Exception as e:
                print(f"Erro ao ler {filepath}: {e}")

    return sorted(files_with_issues)

def main():
    print("=" * 80)
    print("ANALISE CONSOLIDADA - ARQUIVOS PARA MIGRAR")
    print("=" * 80)
    print()

    files = find_files_with_problems()

    print(f"\nTotal de arquivos para migrar: {len(files)}")
    print()

    print("=" * 80)
    print("ARQUIVOS ORDENADOS POR DIRETORIO")
    print("=" * 80)
    print()

    # Agrupar por diretório
    by_dir = defaultdict(list)
    for filepath in files:
        dirname = os.path.dirname(filepath)
        by_dir[dirname].append(filepath)

    # Ordenar alfabeticamente
    for dirname in sorted(by_dir.keys()):
        dir_files = sorted(by_dir[dirname])
        print(f"\n{dirname}/ ({len(dir_files)} arquivos):")
        for filepath in dir_files:
            print(f"  - {filepath}")

    print()
    print("=" * 80)
    print("RESUMO")
    print("=" * 80)
    print(f"\nTotal de arquivos: {len(files)}")
    print(f"\nPor diretório:")
    for dirname in sorted(by_dir.keys()):
        print(f"  {dirname}: {len(by_dir[dirname])} arquivos")

    print()
    print("=" * 80)
    print("[STATUS] Analise concluida!")
    print("=" * 80)
    print()

if __name__ == '__main__':
    main()
