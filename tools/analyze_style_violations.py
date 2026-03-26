"""
Análise completa de violações do Design System no projeto Tensiometro.
"""
import os
import re
import sys
from collections import defaultdict

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Define patterns
patterns = {
    'hex_colors': r'#[0-9A-Fa-f]{6}',
    'hex_colors_3': r'#[0-9A-Fa-f]{3}',
    'hex_colors_8': r'#[0-9A-Fa-f]{8}',
    'qfont': r'QFont\(',
    'setstylesheet': r'setStyleSheet\(',
    'qcolor': r'QColor\(',
    'design_system_import': r'from consumo_lib\.ui import'
}

# Directory to scan
base_dir = 'consumo_lib'

# Store results
file_stats = {}

# Walk through all Python files
for root, dirs, files in os.walk(base_dir):
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            rel_path = filepath.replace('\\', '/')

            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                stats = {}
                has_design_system = False

                for pattern_name, pattern in patterns.items():
                    matches = re.findall(pattern, content)
                    count = len(matches)
                    stats[pattern_name] = count

                    if pattern_name == 'design_system_import' and count > 0:
                        has_design_system = True

                # Calculate total issues (excluding design_system_import)
                total_issues = (stats.get('hex_colors', 0) +
                              stats.get('hex_colors_3', 0) +
                              stats.get('hex_colors_8', 0) +
                              stats.get('qfont', 0) +
                              stats.get('setstylesheet', 0) +
                              stats.get('qcolor', 0))

                file_stats[rel_path] = {
                    'has_design_system': has_design_system,
                    'total_issues': total_issues,
                    **stats
                }
            except Exception as e:
                print(f'Error reading {filepath}: {e}')

# Sort by total issues (descending)
sorted_files = sorted(file_stats.items(), key=lambda x: x[1]['total_issues'], reverse=True)

# Categorize files
critical = []
high = []
medium = []
low = []
no_issues = []
migrated_with_issues = []

for filepath, stats in sorted_files:
    if stats['has_design_system']:
        if stats['total_issues'] > 0:
            migrated_with_issues.append((filepath, stats))
    else:
        if stats['total_issues'] >= 50:
            critical.append((filepath, stats))
        elif stats['total_issues'] >= 20:
            high.append((filepath, stats))
        elif stats['total_issues'] >= 10:
            medium.append((filepath, stats))
        elif stats['total_issues'] > 0:
            low.append((filepath, stats))
        else:
            no_issues.append((filepath, stats))

# Generate report
print("=" * 80)
print("RELATÓRIO DE ANÁLISE DO DESIGN SYSTEM - TENSIOMETRO")
print("=" * 80)
print()

print("📊 RESUMO GERAL")
print("-" * 80)
print(f"Total de arquivos analisados: {len(file_stats)}")
print(f"Arquivos SEM problemas: {len(no_issues)}")
print(f"Arquivos COM problemas (sem Design System): {len(critical) + len(high) + len(medium) + len(low)}")
print(f"Arquivos JÁ MIGRADOS (com Design System + problemas residuais): {len(migrated_with_issues)}")
print()

print("📈 DISTRIBUIÇÃO POR CATEGORIA")
print("-" * 80)
print(f"CRÍTICA (50+ problemas):     {len(critical)} arquivos")
print(f"ALTA (20-49 problemas):       {len(high)} arquivos")
print(f"MÉDIA (10-19 problemas):      {len(medium)} arquivos")
print(f"BAIXA (1-9 problemas):        {len(low)} arquivos")
print(f"SEM PROBLEMAS:                {len(no_issues)} arquivos")
print(f"MIGRADOS COM PROBLEMAS:       {len(migrated_with_issues)} arquivos")
print()

print("🔥 TOP 20 ARQUIVOS MAIS PROBLEMÁTICOS")
print("-" * 80)
for i, (filepath, stats) in enumerate(sorted_files[:20], 1):
    ds_status = "✓" if stats['has_design_system'] else "✗"
    print(f"{i:2d}. [{ds_status}] {stats['total_issues']:3d} probs - {filepath}")
    if stats['total_issues'] > 0:
        print(f"     Hex6:{stats['hex_colors']:2d} Hex3:{stats['hex_colors_3']:2d} "
              f"Hex8:{stats['hex_colors_8']:2d} QFont:{stats['qfont']:2d} "
              f"Style:{stats['setstylesheet']:2d} QColor:{stats['qcolor']:2d}")

print()
print("=" * 80)
print("📋 LISTA COMPLETA POR CATEGORIA")
print("=" * 80)
print()

if critical:
    print("🚨 CATEGORIA: CRÍTICA (50+ problemas)")
    print("-" * 80)
    for i, (filepath, stats) in enumerate(critical, 1):
        print(f"{i:2d}. {stats['total_issues']:3d} probs - {filepath}")
    print()

if high:
    print("⚠️  CATEGORIA: ALTA (20-49 problemas)")
    print("-" * 80)
    for i, (filepath, stats) in enumerate(high, 1):
        print(f"{i:2d}. {stats['total_issues']:3d} probs - {filepath}")
    print()

if medium:
    print("📝 CATEGORIA: MÉDIA (10-19 problemas)")
    print("-" * 80)
    for i, (filepath, stats) in enumerate(medium, 1):
        print(f"{i:2d}. {stats['total_issues']:3d} probs - {filepath}")
    print()

if low:
    print("📄 CATEGORIA: BAIXA (1-9 problemas)")
    print("-" * 80)
    for i, (filepath, stats) in enumerate(low[:50], 1):  # Limit to 50 for brevity
        print(f"{i:2d}. {stats['total_issues']:3d} probs - {filepath}")
    if len(low) > 50:
        print(f"     ... e mais {len(low) - 50} arquivos")
    print()

if migrated_with_issues:
    print("✅ ARQUIVOS JÁ MIGRADOS (com problemas residuais)")
    print("-" * 80)
    for i, (filepath, stats) in enumerate(migrated_with_issues, 1):
        print(f"{i:2d}. {stats['total_issues']:3d} probs - {filepath}")
    print()

print("=" * 80)
print("📊 ESTATÍSTICAS TOTAIS DE OCORRÊNCIAS")
print("=" * 80)

total_hex6 = sum(s['hex_colors'] for s in file_stats.values())
total_hex3 = sum(s['hex_colors_3'] for s in file_stats.values())
total_hex8 = sum(s['hex_colors_8'] for s in file_stats.values())
total_qfont = sum(s['qfont'] for s in file_stats.values())
total_style = sum(s['setstylesheet'] for s in file_stats.values())
total_qcolor = sum(s['qcolor'] for s in file_stats.values())

print(f"Cores hexadecimais (6 dígitos): {total_hex6}")
print(f"Cores hexadecimais (3 dígitos): {total_hex3}")
print(f"Cores hexadecimais (8 dígitos): {total_hex8}")
print(f"TOTAL de cores hardcoded:      {total_hex6 + total_hex3 + total_hex8}")
print()
print(f"Criação manual de QFont:       {total_qfont}")
print(f"Chamadas setStyleSheet:        {total_style}")
print(f"Criação de QColor:             {total_qcolor}")
print()
print(f"TOTAL GERAL DE VIOLAÇÕES:     {total_hex6 + total_hex3 + total_hex8 + total_qfont + total_style + total_qcolor}")
print()
