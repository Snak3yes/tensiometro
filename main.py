#!/usr/bin/env python3
"""
Tensiometro - Ponto de entrada principal da aplicação AOI

Este script inicializa a aplicação de Inspeção Óptica Automatizada
para medição de tensão de stencil e controle de qualidade.

Uso:
    python main.py
    .venv/Scripts/python.exe main.py
"""

import sys
import importlib
from pathlib import Path

# Adiciona diretório raiz ao sys.path para garantir imports funcionem
# Isso é necessário porque consumo_lib/ agora é um pacote
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))


def warmup_imports():
    """
    Pre-carrega módulos críticos antes de iniciar QApplication.

    Isso resolve problema do Windows Defender bloqueando arquivos .pyc
    na primeira execução, causando KeyboardInterrupt.

    O warmup permite que o antivírus escaneie os arquivos antes
    da execução crítica da aplicação.
    """
    print("[WARMUP] Pre-carregando módulos...")

    # Lista de módulos críticos que causaram problemas
    warmup_modules = [
        # PyQt6 core
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
        # Design system (COLORS precisa ser carregado)
        "consumo_lib.ui.design_tokens",
        "consumo_lib.ui.theme_manager",
        "consumo_lib.ui.widget_standards",
        # Handlers (keyboard_handler causou KeyboardInterrupt)
        "consumo_lib.handlers.keyboard_handler",
        "consumo_lib.handlers.menu_handler",
        "consumo_lib.handlers.dialog_router",
        # Core business logic
        "aoi_lib.config_manager",
        "aoi_lib.auth",
        "aoi_lib.plc_axis_controller",
        "aoi_lib.tensiometer",
        # Main window dependencies
        "consumo_lib.main_window",
        "consumo_lib.tabs",
        "consumo_lib.widgets",
        "consumo_lib.dialogs",
        "consumo_lib.controllers",
        "consumo_lib.coordinators",
        "consumo_lib.handlers",
        "consumo_lib.services",
        "consumo_lib.managers",
        "consumo_lib.facades",
        "consumo_lib.factories",
        "consumo_lib.ui_builders",
        "consumo_lib.utils",
        "consumo_lib.threads",
        # ReportLab (causou problemas no pdf_generator)
        "reportlab.lib",
        "reportlab.platypus",
        "reportlab.graphics.shapes",
    ]

    loaded_count = 0
    for module_name in warmup_modules:
        try:
            importlib.import_module(module_name)
            loaded_count += 1
        except ImportError as e:
            # Módulo não existe ou depende de hardware - ignorar
            pass
        except Exception as e:
            # Outros erros - log mas não crash
            print(f"[WARMUP] Warning: {module_name} - {type(e).__name__}")

    print(f"[WARMUP] {loaded_count} módulos pre-carregados")


def main():
    """Função principal de inicialização"""

    # WARMUP: Pre-carregar módulos ANTES de QApplication
    # Isso resolve o problema do Windows Defender na primeira execução
    warmup_imports()

    # Importa QApplication DEPOIS do warmup
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # Inicializa ThemeManager do Design System PRIMEIRO
    # Isso inicializa COLORS antes que qualquer widget seja importado
    try:
        from consumo_lib.ui.theme_manager import init_theme_manager
        theme_mgr = init_theme_manager(app)
        print(f"[OK] Design System inicializado - Tema: {theme_mgr.current_theme}")
    except Exception as e:
        print(f"[WARN] Falha ao inicializar Design System: {e}")
        print("   Continuando sem Design System...")

    # Importa main_window DEPOIS que ThemeManager está inicializado
    # Isso garante que COLORS esteja disponível quando widgets são criados
    from consumo_lib.main_window import AOIControllerApp

    window = AOIControllerApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
