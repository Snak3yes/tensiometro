#!/usr/bin/env python
"""Análise completa de estilos inline na aplicação"""

import os
import re
from pathlib import Path
from collections import defaultdict

# Padrões para buscar
PATTERNS = {
    'cores_hex': r'#([0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})',
    'qfont_manual': r'QFont\(\)',
    'set_minimum_height': r'setMinimumHeight\((\d+)\)',
    'set_maximum_height': r'setMaximumHeight\((\d+)\)',
    'set_minimum_size': r'setMinimumSize\((\d+),\s*(\d+)\)',
    'set_maximum_size': r'setMaximumSize\((\d+),\s*(\d+)\)',
    'set_point_size': r'setPointSize\((\d+)\)',
    'set_pixel_size': r'setPixelSize\((\d+)\)',
    'setStyleSheet': r'setStyleSheet\([^)]*#[0-9A-Fa-f]{6}',
}

# Arquivos que devem ser ignorados (parte do Design System)
IGNORE_FILES = {
    'design_tokens.py',
    'styles.qss',
    'widget_standards.py',
}

# Diretórios para analisar
DIRS_TO_ANALYZE = [
    'consumo_lib/tabs',
    'consumo_lib/widgets',
    'consumo_lib/dialogs',
    'consumo_lib/controllers',
]

def analyze_file(filepath):
    """Analisa um arquivo buscando padrões hardcoded"""
    results = defaultdict(list)

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')

        # Ignorar arquivos do Design System
        if any(ignore_file in str(filepath) for ignore_file in IGNORE_FILES):
            return results

        # Buscar cada padrão
        for pattern_name, pattern in PATTERNS.items():
            for match in re.finditer(pattern, content):
                # Encontrar linha número
                line_num = content[:match.start()].count('\n') + 1
                line_content = lines[line_num - 1].strip()

                # Pular comentários
                if line_content.startswith('#'):
                    continue

                results[pattern_name].append({
                    'line': line_num,
                    'content': line_content,
                    'match': match.group(0)
                })

    except Exception as e:
        print(f"Erro ao ler {filepath}: {e}")

    return results

def main():
    """Função principal"""
    print("=" * 80)
    print("ANÁLISE COMPLETA DE ESTILOS INLINE - TENSIOEMETRO")
    print("=" * 80)
    print()

    all_results = defaultdict(lambda: defaultdict(list))

    # Analisar todos os arquivos Python
    for base_dir in DIRS_TO_ANALYZE:
        if not os.path.exists(base_dir):
            continue

        for root, dirs, files in os.walk(base_dir):
            # Ignorar diretórios __pycache__
            dirs[:] = [d for d in dirs if d != '__pycache__']

            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    results = analyze_file(filepath)

                    if results:
                        rel_path = os.path.relpath(filepath)
                        for pattern_name, matches in results.items():
                            all_results[pattern_name][rel_path] = matches

    # Gerar relatório
    total_issues = sum(len(matches) for matches in all_results.values()
                      for files_matches in matches.values()
                      for matches in files_matches)

    print(f"\n[RELATORIO] RESUMO GERAL")
    print(f"-" * 80)
    print(f"Total de problemas encontrados: {total_issues}")
    print()

    # Relatório por categoria
    for pattern_name, files in sorted(all_results.items()):
        pattern_total = sum(len(matches) for matches in files.values())
        print(f"\n{'=' * 80}")
        print(f"[ANALISE] {pattern_name.upper().replace('_', ' ')}: {pattern_total} ocorrências em {len(files)} arquivos")
        print(f"{'=' * 80}")

        # Arquivos mais problemáticos primeiro
        sorted_files = sorted(files.items(), key=lambda x: len(x[1]), reverse=True)

        for filepath, matches in sorted_files[:10]:  # Top 10 arquivos
            print(f"\n[ARQUIVO] {filepath} ({len(matches)} ocorrências)")
            for match in matches[:5]:  # Mostrar primeiras 5
                print(f"   Linha {match['line']}: {match['content'][:80]}")
            if len(matches) > 5:
                print(f"   ... e mais {len(matches) - 5} ocorrências")

    # Recomendações
    print(f"\n\n{'=' * 80}")
    print("[RECOMENDACOES]")
    print(f"{'=' * 80}")

    print("""
1. PRIORIDADE ALTA - Arquivos com QFont() manual:
   - Migrar para TYPO.get_font()
   - Substituir: font = QFont() → font = TYPO.get_font(TYPO.BODY_MEDIUM)

2. PRIORIDADE ALTA - Arquivos com cores hex inline:
   - Migrar para COLORS tokens
   - Substituir: "#4CAF50" → COLORS.PRIMARY

3. PRIORIDADE MÉDIA - Arquivos com setMinimumHeight hardcoded:
   - Migrar para DIM tokens
   - Substituir: setMinimumHeight(40) → setMinimumHeight(DIM.BUTTON_HEIGHT_MD)

4. Consulte documentação completa em: docs/design_system/MIGRATION.md
5. Padrões de migração em: docs/design_system/README.md
""")

    # Arquivos críticos não migrados
    print(f"\n{'=' * 80}")
    print("[ALERTA] ARQUIVOS CRITICOS NAO MIGRADOS")
    print(f"{'=' * 80}")

    critical_files = []
    for pattern_name, files in all_results.items():
        for filepath, matches in files.items():
            if len(matches) >= 5:  # 5 ou mais problemas
                if filepath not in [f[0] for f in critical_files]:
                    critical_files.append((filepath, sum(len(m) for m in all_results.values()
                                                        if filepath in all_results.get(pattern_name, {}))))

    critical_files.sort(key=lambda x: x[1], reverse=True)

    for filepath, total in critical_files[:15]:
        print(f"   {filepath}: {total} problemas totais")

    print(f"\n{'=' * 80}")
    print("[CONCLUIDO] Analise finalizada!")
    print(f"{'=' * 80}\n")

if __name__ == '__main__':
    main()
