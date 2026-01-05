#!/usr/bin/env python3
"""
Remove métodos _on_* duplicados do main_window.py.

Mantém apenas _on_connect_btn_clicked (handler de botão UI)
Remove todos os outros métodos _on_* que estão duplicados no SignalAggregator.
"""

import re

def remove_duplicate_handlers(input_file, output_file):
    """Remove métodos _on_* duplicados mantendo _on_connect_btn_clicked."""

    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    output_lines = []
    skip_mode = False
    removed_count = 0
    kept_connect_btn = False

    i = 0
    while i < len(lines):
        line = lines[i]

        # Detecta início de método _on_*
        if re.match(r'^\s*def _on_', line):
            method_name = re.search(r'def (_on_\w+)', line).group(1)

            # Mantém _on_connect_btn_clicked
            if method_name == '_on_connect_btn_clicked':
                output_lines.append(line)
                kept_connect_btn = True
                i += 1
                continue

            # Remove outros métodos _on_*
            skip_mode = True
            removed_count += 1

            # Encontra o fim do método (próximo método ou classe com mesma indentação)
            i += 1
            current_indent = len(line) - len(line.lstrip())

            while i < len(lines):
                next_line = lines[i]

                # Se chegou em um método/classe com mesma ou menor indentação, parou
                if next_line.strip() and not next_line.strip().startswith('#'):
                    next_indent = len(next_line) - len(next_line.lstrip())
                    if next_indent <= current_indent and re.match(r'^\s*(def |class )', next_line):
                        break

                i += 1

            skip_mode = False
            continue

        # Se não está em modo skip, adiciona a linha
        if not skip_mode:
            output_lines.append(line)

        i += 1

    # Escreve o arquivo modificado
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(output_lines)

    return removed_count, kept_connect_btn

if __name__ == '__main__':
    input_file = 'consumo_lib/main_window.py'
    output_file = 'consumo_lib/main_window.py'

    print("Removendo métodos _on_* duplicados...")
    removed, kept = remove_duplicate_handlers(input_file, output_file)

    print(f"\nResultado:")
    print(f"- Métodos removidos: {removed}")
    print(f"- _on_connect_btn_clicked mantido: {'SIM' if kept else 'NAO'}")
    print(f"\nArquivo atualizado: {output_file}")
