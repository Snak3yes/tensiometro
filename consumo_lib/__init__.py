"""
consumo_lib - Pacote da interface principal do Tensiometro

Este pacote contém a interface PyQt6 principal e todos os componentes
de UI organizados em módulos:
- main_window.py: Janela principal da aplicação
- widgets/: Componentes de UI reutilizáveis
- tabs/: Abas semânticas organizadas por funcionalidade
- managers/: Gerenciadores de domínio
- dialogs/: Diálogos configuráveis
- threads/: Threads para operações assíncronas
- utils/: Utilitários diversos
"""

import sys
from pathlib import Path

# Fix de sys.path para garantir imports funcionem
# Quando consumo_lib é executado como pacote, precisamos garantir
# que o diretório raiz do projeto esteja no path
_current_file = Path(__file__).resolve()
_root_dir = _current_file.parent.parent

if str(_root_dir) not in sys.path:
    sys.path.insert(0, str(_root_dir))

__version__ = "0.4.0"

# Barrier package: Exporta classes principais para simplificar imports
from .main_window import AOIControllerApp

__all__ = [
    'AOIControllerApp',
    '__version__',
]
