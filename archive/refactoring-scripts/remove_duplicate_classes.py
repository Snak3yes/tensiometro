#!/usr/bin/env python3
"""
Script para remover as definições de classe duplicadas de main_window.py
após movê-las para arquivos separados.
"""

from pathlib import Path
import re

# Classes para remover e suas linhas aproximadas (baseado no grep anterior)
CLASSES_TO_REMOVE = [
    ("TensionVisualizationWidget", 57, 393),      # Linhas 57-393
    ("TensionCanvas", 394, 616),                   # Linhas 394-616
    ("ImageViewerWidget", 617, 659),               # Linhas 617-659
    ("PositionListWidget", 660, 725),              # Linhas 660-725
    ("SequenceControlWidget", 726, 775),           # Linhas 726-775
    ("PositionRegistryWidget", 776, 852),          # Linhas 776-852
    ("CameraPreviewWidget", 853, 1098),            # Linhas 853-1098
    ("MovementControlWidget", 1099, 1743),         # Linhas 1099-1743
    ("PLCMonitorWidget", 1744, 1915),              # Linhas 1744-1915
    ("MapParams", 1916, 1924),                     # Linhas 1916-1924
    ("_PreviewSuspender", 1925, 1941),             # Linhas 1925-1941
    ("SequenceRunnerThread", 6080, 6102),          # Linhas 6080-6102
    ("MapGeneratorThread", 6103, 6120),            # Linhas 6103-6120 (aprox)
]

def remove_classes_from_file(file_path: Path):
    """Remove as classes especificadas do arquivo."""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Ordenar em ordem reversa para não bagunçar os índices
    classes_to_remove_sorted = sorted(CLASSES_TO_REMOVE, key=lambda x: x[1], reverse=True)

    lines_to_keep = list(range(1, len(lines) + 1))

    for class_name, start_line, end_line in classes_to_remove_sorted:
        # Converter para 0-indexed
        start_idx = start_line - 1
        end_idx = end_line - 1

        print(f"Removendo {class_name} (linhas {start_line}-{end_line})")

        # Marcar linhas para remover
        for i in range(start_idx, min(end_idx + 1, len(lines))):
            if i in lines_to_keep:
                lines_to_keep.remove(i + 1)  # +1 porque lines_to_keep é 1-indexed

    # Reconstruir o arquivo
    new_lines = []
    for i, line in enumerate(lines):
        if (i + 1) in lines_to_keep:
            new_lines.append(line)

    # Salvar
    backup_path = file_path.with_suffix('.py.bak')
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    print(f"\n✅ {len(lines) - len(new_lines)} linhas removidas")
    print(f"📁 Backup salvo em: {backup_path}")
    print(f"📊 Novo tamanho: {len(new_lines)} linhas (era {len(lines)})")

    return len(new_lines)


def main():
    file_path = Path("consumo_lib/main_window.py")

    if not file_path.exists():
        print(f"❌ Arquivo {file_path} não encontrado")
        return

    print("🔧 Removendo classes duplicadas de main_window.py")
    print("=" * 60)

    new_size = remove_classes_from_file(file_path)

    print("\n" + "=" * 60)
    print("✅ Classes removidas com sucesso!")
    print(f"📉 Redução de {6245 - new_size} linhas ({100 * (6245 - new_size) / 6245:.1f}%)")


if __name__ == "__main__":
    main()
