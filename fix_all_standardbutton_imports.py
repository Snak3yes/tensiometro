"""
Script robusto para adicionar import StandardButton em todos os arquivos necessários.
"""

import re
from pathlib import Path

def fix_import_in_file(file_path: Path) -> bool:
    """Adiciona import de StandardButton se necessário, retornando True se modificou"""
    try:
        content = file_path.read_text(encoding="utf-8")
    except:
        return False

    # Verificar se usa StandardButton
    if "StandardButton(" not in content:
        return False

    # Verificar se já tem o import correto
    if "from consumo_lib.ui.widget_standards import StandardButton" in content:
        return False

    # Encontrar a posição do primeiro import
    lines = content.split('\n')

    # Encontrar última linha de imports (PyQt6 ou consumo_lib)
    last_import_line = -1
    for i, line in enumerate(lines):
        if line.strip().startswith(("from PyQt6", "from consumo_lib", "from aoi_lib", "import logging", "import sys")):
            last_import_line = i

    if last_import_line == -1:
        # Não encontrou imports, adicionar após shebang ou docstring
        insert_pos = 0
        # Pular shebang
        if len(lines) > 0 and lines[0].startswith("#!"):
            insert_pos = 1
        # Pular docstring
        if insert_pos < len(lines) and lines[insert_pos].startswith('"""'):
            insert_pos += 1
            while insert_pos < len(lines) and '"""' not in lines[insert_pos]:
                insert_pos += 1
            if insert_pos < len(lines):
                insert_pos += 1
    else:
        insert_pos = last_import_line + 1

    # Criar linha de import
    import_line = "from consumo_lib.ui.widget_standards import StandardButton"

    # Adicionar linha em branco antes se necessário
    if insert_pos > 0 and lines[insert_pos - 1].strip() != "":
        lines.insert(insert_pos, "")
        insert_pos += 1

    # Inserir import
    lines.insert(insert_pos, import_line)

    # Adicionar linha em branco depois se necessário
    if insert_pos + 1 < len(lines) and lines[insert_pos + 1].strip() != "":
        lines.insert(insert_pos + 1, "")

    # Escrever de volta
    new_content = '\n'.join(lines)
    file_path.write_text(new_content, encoding="utf-8")

    return True

def main():
    """Função principal"""
    projeto = Path("consumo_lib")
    fixed = []
    errors = []

    for py_file in projeto.rglob("*.py"):
        try:
            content = py_file.read_text(encoding="utf-8")

            if "StandardButton(" in content:
                if fix_import_in_file(py_file):
                    fixed.append(str(py_file))
        except Exception as e:
            errors.append((str(py_file), str(e)))

    print(f"Arquivos corrigidos: {len(fixed)}")
    for f in fixed:
        print(f"  [FIXED] {f}")

    if errors:
        print(f"\nErros: {len(errors)}")
        for f, e in errors:
            print(f"  [ERROR] {f}: {e}")

if __name__ == "__main__":
    main()
