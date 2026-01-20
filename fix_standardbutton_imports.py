"""
Script para adicionar import StandardButton em arquivos que usam mas não importam.
"""

import re
from pathlib import Path

def fix_import(file_path: Path) -> bool:
    """Adiciona import de StandardButton se necessário"""
    content = file_path.read_text(encoding="utf-8")

    # Verificar se usa StandardButton
    if "StandardButton(" not in content:
        return False

    # Verificar se já tem o import
    if "from consumo_lib.ui.widget_standards import StandardButton" in content:
        return False

    # Adicionar import
    if "from consumo_lib.ui import" in content:
        # Adicionar após imports existentes de consumo_lib.ui
        content = re.sub(
            r'(from consumo_lib\.ui import [^\n]+)',
            r'\1\nfrom consumo_lib.ui.widget_standards import StandardButton',
            content,
            count=1
        )
    elif "from PyQt6.QtWidgets import" in content:
        # Adicionar após imports PyQt6
        content = re.sub(
            r'(from PyQt6\.QtWidgets import[^\n]+\))',
            r'\1\n\nfrom consumo_lib.ui.widget_standards import StandardButton',
            content,
            count=1
        )
    else:
        # Adicionar no topo do arquivo
        content = "from consumo_lib.ui.widget_standards import StandardButton\n\n" + content

    file_path.write_text(content, encoding="utf-8")
    return True

def main():
    """Função principal"""
    # Buscar todos os arquivos Python que usam StandardButton
    projeto = Path("consumo_lib")
    fixed = 0

    for py_file in projeto.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8")

        if "StandardButton(" in content:
            if fix_import(py_file):
                print(f"[FIXED] {py_file}")
                fixed += 1

    print(f"\nTotal de arquivos corrigidos: {fixed}")

if __name__ == "__main__":
    main()
