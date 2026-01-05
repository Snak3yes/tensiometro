#!/usr/bin/env python3
"""
Script para remover classes de main_window.py usando regex para encontrar os limites exatos.
"""

import re
from pathlib import Path

# Classes para remover (ordem não importa)
CLASSES_TO_REMOVE = [
    "TensionVisualizationWidget",
    "TensionCanvas",
    "ImageViewerWidget",
    "PositionListWidget",
    "SequenceControlWidget",
    "PositionRegistryWidget",
    "CameraPreviewWidget",
    "MovementControlWidget",
    "PLCMonitorWidget",
    "MapParams",
    "_PreviewSuspender",
    "SequenceRunnerThread",
    "MapGeneratorThread",
]


def find_class_boundaries(lines: list, class_name: str):
    """
    Encontra os limites exatos de uma classe usando análise de indentação.
    Retorna (start_line, end_line) 1-indexed ou None.
    """
    # Pattern para encontrar a linha onde a classe começa
    class_pattern = re.compile(rf'^class {re.escape(class_name)}\(')

    start_line = None
    for i, line in enumerate(lines):
        if class_pattern.match(line):
            start_line = i
            break

    if start_line is None:
        return None

    # Encontrar onde a classe termina (próxima linha com indentação 0 que não seja comment/blank)
    # A classe termina quando encontramos uma linha no mesmo nível de indentação que 'class'
    for i in range(start_line + 1, len(lines)):
        line = lines[i]
        # Ignorar linhas em branco e comentários
        if line.strip() == '' or line.strip().startswith('#'):
            continue

        # Se a linha não tem indentação (começa com não-espaço), é o fim da classe
        if not line[0].isspace():
            return (start_line + 1, i + 1)  # 1-indexed

    # Se chegamos ao fim do arquivo
    return (start_line + 1, len(lines))  # 1-indexed


def remove_classes_from_file(file_path: Path):
    """Remove as classes especificadas do arquivo."""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print(f"Arquivo original: {len(lines)} linhas\n")

    # Encontrar limites de cada classe
    class_ranges = []
    for class_name in CLASSES_TO_REMOVE:
        result = find_class_boundaries(lines, class_name)
        if result:
            start, end = result
            class_ranges.append((class_name, start, end))
            print(f"✅ Encontrado: {class_name} (linhas {start}-{end}, {end-start+1} linhas)")
        else:
            print(f"⚠️  NÃO encontrado: {class_name}")

    if not class_ranges:
        print("\n❌ Nenhuma classe encontrada para remover")
        return

    # Ordenar por posição (do fim para o início para não bagunçar índices)
    class_ranges.sort(key=lambda x: x[1], reverse=True)

    # Marcar linhas para manter
    lines_to_remove = set()
    for class_name, start, end in class_ranges:
        for i in range(start - 1, end):  # Converter para 0-indexed
            lines_to_remove.add(i)

    # Reconstruir arquivo
    new_lines = [lines[i] for i in range(len(lines)) if i not in lines_to_remove]

    # Backup
    backup_path = file_path.with_suffix('.py.bak2')
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    # Salvar novo arquivo
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    print(f"\n{'='*60}")
    print(f"✅ Removidas {len(lines) - len(new_lines)} linhas")
    print(f"📊 Novo tamanho: {len(new_lines)} linhas")
    print(f"📉 Redução: {100 * (len(lines) - len(new_lines)) / len(lines):.1f}%")
    print(f"📁 Backup: {backup_path}")


def main():
    file_path = Path("consumo_lib/main_window.py")

    if not file_path.exists():
        print(f"❌ Arquivo não encontrado: {file_path}")
        return

    print("🔧 Removendo classes de main_window.py\n")
    print("="*60)

    remove_classes_from_file(file_path)


if __name__ == "__main__":
    main()
