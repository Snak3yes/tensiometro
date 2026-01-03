#!/usr/bin/env python3
"""
Script para extrair classes de consumo_lib/main_window.py para arquivos separados.
Fase 1 do refactoring: Mover widgets, threads e utils para arquivos próprios.
"""

import re
from pathlib import Path

# Mapeamento de classes para seus arquivos de destino
CLASSES_TO_EXTRACT = {
    # Widgets
    "TensionVisualizationWidget": "consumo_lib/widgets/tension_viz.py",
    "TensionCanvas": "consumo_lib/widgets/tension_viz.py",  # Mesmo arquivo
    "ImageViewerWidget": "consumo_lib/widgets/image_viewer.py",
    "PositionListWidget": "consumo_lib/widgets/position_list.py",
    "SequenceControlWidget": "consumo_lib/widgets/sequence_control.py",
    "PositionRegistryWidget": "consumo_lib/widgets/position_registry.py",
    "CameraPreviewWidget": "consumo_lib/widgets/camera_preview.py",
    "MovementControlWidget": "consumo_lib/widgets/movement_control.py",
    "PLCMonitorWidget": "consumo_lib/widgets/plc_monitor.py",
    "_PreviewSuspender": "consumo_lib/widgets/preview_suspender.py",

    # Threads
    "SequenceRunnerThread": "consumo_lib/threads/sequence_runner.py",
    "MapGeneratorThread": "consumo_lib/threads/map_generator.py",

    # Utils
    "MapParams": "consumo_lib/utils/map_params.py",
}

# Imports necessários para cada arquivo
FILE_IMPORTS = {
    "consumo_lib/widgets/tension_viz.py": """import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QLabel
from PyQt6.QtCore import Qt
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)
""",

    "consumo_lib/widgets/image_viewer.py": """from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGroupBox
from PyQt6.QtGui import QPixmap
import logging

logger = logging.getLogger(__name__)
""",

    "consumo_lib/widgets/position_list.py": """from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QInputDialog, QMessageBox
)
from PyQt6.QtCore import Qt
import logging

logger = logging.getLogger(__name__)
""",

    "consumo_lib/widgets/sequence_control.py": """from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QSpinBox, QCheckBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
import logging

logger = logging.getLogger(__name__)
""",

    "consumo_lib/widgets/position_registry.py": """from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QInputDialog, QMessageBox
)
from PyQt6.QtCore import Qt
import logging

logger = logging.getLogger(__name__)
""",

    "consumo_lib/widgets/camera_preview.py": """import cv2
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QHBoxLayout,
    QPushButton, QCheckBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QImage

from aoi_lib.config_manager import AOIConfigManager
from aoi_lib.fov_calibration import (
    FOVCalibration, CameraFOVConverter, ClickableVideoLabel
)

logger = logging.getLogger(__name__)
""",

    "consumo_lib/widgets/movement_control.py": """from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QGridLayout,
    QPushButton, QLabel, QDoubleSpinBox, QSpinBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from aoi_lib.config_manager import AOIConfigManager
import logging

logger = logging.getLogger(__name__)
""",

    "consumo_lib/widgets/plc_monitor.py": """from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
import logging

logger = logging.getLogger(__name__)
""",

    "consumo_lib/widgets/preview_suspender.py": """from contextlib import contextmanager
from PyQt6.QtCore import QSignalBlocker
""",

    "consumo_lib/threads/sequence_runner.py": """from PyQt6.QtCore import QThread, pyqtSignal
import logging

logger = logging.getLogger(__name__)
""",

    "consumo_lib/threads/map_generator.py": """from PyQt6.QtCore import QThread, pyqtSignal
from pathlib import Path
import logging

logger = logging.getLogger(__name__)
""",

    "consumo_lib/utils/map_params.py": """from dataclasses import dataclass, field
from typing import List, Dict
from pathlib import Path
""",
}


def extract_class_from_file(source_file: Path, class_name: str):
    """Extrai uma classe completa do arquivo de origem."""
    with open(source_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Encontrar a linha onde a classe começa
    start_line = None
    for i, line in enumerate(lines):
        if line.strip().startswith(f'class {class_name}'):
            start_line = i
            break

    if start_line is None:
        print(f"⚠️  Classe {class_name} não encontrada")
        return None

    # Encontrar onde a classe termina (próxima classe ou fim do arquivo)
    end_line = len(lines)
    for i in range(start_line + 1, len(lines)):
        line = lines[i]
        # Verifica se é uma definição de classe no nível superior (não indentado)
        if line.strip() and not line[0].isspace() and line.strip().startswith('class '):
            end_line = i
            break

    # Extrair o código da classe
    class_lines = lines[start_line:end_line]

    return ''.join(class_lines), start_line, end_line


def save_class_to_file(class_code: str, target_file: Path, class_name: str):
    """Salva a classe no arquivo de destino com imports apropriados."""
    target_file.parent.mkdir(parents=True, exist_ok=True)

    # Se o arquivo já existe, apenas adiciona a classe
    if target_file.exists():
        with open(target_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Adiciona a classe ao final
        with open(target_file, 'a', encoding='utf-8') as f:
            f.write('\n\n' + class_code)
    else:
        # Cria o arquivo com imports
        imports = FILE_IMPORTS.get(str(target_file), "# Imports\n\n")
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(imports)
            f.write(class_code)

    print(f"✅ {class_name} → {target_file}")


def main():
    source_file = Path("consumo_lib/main_window.py")

    if not source_file.exists():
        print(f"❌ Arquivo {source_file} não encontrado")
        return

    print("🚀 Iniciando extração de classes...")
    print("=" * 60)

    # Agrupar classes por arquivo de destino
    classes_by_file = {}
    for class_name, target_file in CLASSES_TO_EXTRACT.items():
        target_path = Path(target_file)
        if target_path not in classes_by_file:
            classes_by_file[target_path] = []
        classes_by_file[target_path].append(class_name)

    # Processar cada arquivo de destino
    for target_file, class_names in classes_by_file.items():
        print(f"\n📁 Processando {target_file}:")

        # Ordenar classes por linha de origem
        class_info_list = []
        for class_name in class_names:
            result = extract_class_from_file(source_file, class_name)
            if result:
                class_code, start, end = result
                class_info_list.append((start, class_name, class_code))

        # Ordenar por posição original
        class_info_list.sort(key=lambda x: x[0])

        # Criar arquivo com imports e classes
        target_file.parent.mkdir(parents=True, exist_ok=True)
        imports = FILE_IMPORTS.get(str(target_file), "# Imports\n\n")

        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(imports)
            for _, class_name, class_code in class_info_list:
                f.write(class_code)
                f.write('\n\n')
                print(f"  ✅ {class_name}")

    print("\n" + "=" * 60)
    print("✅ Extração concluída!")
    print(f"📊 {len(CLASSES_TO_EXTRACT)} classes extraídas para {len(classes_by_file)} arquivos")


if __name__ == "__main__":
    main()
