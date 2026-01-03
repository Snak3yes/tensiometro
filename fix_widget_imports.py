#!/usr/bin/env python3
"""
Script para corrigir os imports dos widgets movidos.
"""

import re
from pathlib import Path

# Mapeamento de arquivo para imports adicionais necessários
EXTRA_IMPORTS = {
    "consumo_lib/widgets/position_list.py": [
        "from aoi_lib import InspectionPosition",
    ],
    "consumo_lib/widgets/position_registry.py": [
        "from aoi_lib.config_manager import AOIConfigManager",
    ],
    "consumo_lib/widgets/sequence_control.py": [
        "from aoi_lib.config_manager import AOIConfigManager",
    ],
    "consumo_lib/widgets/tension_viz.py": [
        "from aoi_lib.config_manager import AOIConfigManager",
    ],
    "consumo_lib/threads/map_generator.py": [
        "from aoi_lib.config_manager import AOIConfigManager",
    ],
}


def fix_file_imports(file_path: Path, extra_imports: list):
    """Adiciona imports extras ao arquivo."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Encontrar a última linha de imports (antes da primeira classe ou função)
    lines = content.split('\n')

    insert_pos = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Se encontramos uma definição de classe/função, parar antes dela
        if stripped.startswith('class ') or stripped.startswith('def '):
            insert_pos = i
            break
        # Se encontramos uma linha que não é import nem comment nem blank, parar
        if stripped and not stripped.startswith('#') and not stripped.startswith('import') and not stripped.startswith('from'):
            insert_pos = i
            break

    # Verificar quais imports já existem
    existing_imports = set()
    for line in lines[:insert_pos]:
        if line.strip().startswith('import ') or line.strip().startswith('from '):
            existing_imports.add(line.strip())

    # Adicionar imports que não existem
    new_imports = []
    for imp in extra_imports:
        if imp not in existing_imports:
            new_imports.append(imp)

    if new_imports:
        # Inserir imports
        lines[insert_pos:insert_pos] = new_imports

        # Salvar
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        print(f"✅ {file_path.name}: adicionados {len(new_imports)} imports")
        for imp in new_imports:
            print(f"   + {imp}")
    else:
        print(f"✅ {file_path.name}: imports já OK")


def main():
    print("🔧 Corrigindo imports dos widgets...\n")

    for file_path_str, extra_imports in EXTRA_IMPORTS.items():
        file_path = Path(file_path_str)
        if file_path.exists():
            fix_file_imports(file_path, extra_imports)
        else:
            print(f"⚠️  Arquivo não encontrado: {file_path}")

    print("\n✅ Correção de imports concluída!")


if __name__ == "__main__":
    main()
