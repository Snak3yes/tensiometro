#!/usr/bin/env python3
"""
Remove blocos de fallback do main_window.py.

Estratégia:
- Substitui blocos else com código de fallback por apenas logger.error + return
- Remove código duplicado que só existe como fallback
- Mantém segurança mas simplifica o código
"""

import re

def process_fallback_block(lines, start_idx):
    """
    Processa um bloco de fallback começando em start_idx.

    Retorna: (output_lines, lines_skipped, new_start_idx)
    """
    output = []
    i = start_idx

    # Volta para encontrar o else:
    j = i - 1
    while j >= 0 and 'else:' not in lines[j]:
        j -= 1

    if j < 0 or 'else:' not in lines[j]:
        # Não encontrou else, retorna linhas originais
        return lines[:start_idx], 0, start_idx

    # Adiciona linhas até o else (exclusive)
    output.extend(lines[:j])

    # Pega indentação do else
    else_indent = len(lines[j]) - len(lines[j].lstrip())

    # Encontra nome do controller no logger.error
    controller_name = "Controller"
    for k in range(j, min(j + 5, len(lines))):
        match = re.search(r"(\w+)Controller não está disponível", lines[k])
        if match:
            controller_name = match.group(1)
            break

    # Substitui por logger.error + return simplificados
    simplified_else = f"{' ' * else_indent}else:\n"
    simplified_else += f"{' ' * (else_indent + 4)}logger.error(\"{controller_name} não está disponível\")\n"
    simplified_else += f"{' ' * (else_indent + 4)}return\n"

    output.append(simplified_else)

    # Pula bloco de fallback
    i += 1
    fallback_indent = len(lines[start_idx]) - len(lines[start_idx].lstrip())
    lines_skipped = 0

    while i < len(lines):
        next_line = lines[i]

        # Se chegou em um método/classe com mesma ou menor indentação, parou
        if next_line.strip() and not next_line.strip().startswith('#'):
            next_indent = len(next_line) - len(next_line.lstrip())
            if next_indent <= fallback_indent and re.match(r'^\s*(def |class )', next_line):
                break

        lines_skipped += 1
        i += 1

    # Adiciona o restante das linhas (a partir de i)
    output.extend(lines[i:])

    return output, lines_skipped, i

def remove_fallback_blocks(input_file, output_file):
    """Remove blocos de fallback do arquivo."""

    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    current_lines = lines
    total_removed = 0
    replaced_blocks = 0
    max_iterations = 20  # Limite de segurança

    for iteration in range(max_iterations):
        # Procura próximo bloco de fallback
        fallback_idx = -1
        for i, line in enumerate(current_lines):
            if '# Fallback:' in line or '# Fallback para' in line:
                fallback_idx = i
                break

        if fallback_idx == -1:
            # Não encontrou mais blocos
            break

        # Processa o bloco
        current_lines, removed, _ = process_fallback_block(current_lines, fallback_idx)
        total_removed += removed
        replaced_blocks += 1

    # Escreve o arquivo modificado
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(current_lines)

    return total_removed, replaced_blocks

if __name__ == '__main__':
    input_file = 'consumo_lib/main_window.py'
    output_file = 'consumo_lib/main_window.py'

    print("Removendo blocos de fallback...")
    removed, replaced = remove_fallback_blocks(input_file, output_file)

    print(f"\nResultado:")
    print(f"- Blocos substituídos: {replaced}")
    print(f"- Linhas removidas: {removed}")
    print(f"- Arquivo atualizado: {output_file}")
