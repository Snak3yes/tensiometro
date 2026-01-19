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
from pathlib import Path

# Adiciona diretório raiz ao sys.path para garantir imports funcionem
# Isso é necessário porque consumo_lib/ agora é um pacote
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# Importa e executa a aplicação principal
from consumo_lib.main_window import AOIControllerApp
from PyQt6.QtWidgets import QApplication

def main():
    """Função principal de inicialização"""
    app = QApplication(sys.argv)

    # Inicializa ThemeManager do Design System
    # Isso carrega o stylesheet global (styles.qss) automaticamente
    try:
        from consumo_lib.ui.theme_manager import init_theme_manager
        theme_mgr = init_theme_manager(app)
        print(f"[OK] Design System inicializado - Tema: {theme_mgr.current_theme}")
    except Exception as e:
        print(f"[WARN] Falha ao inicializar Design System: {e}")
        print("   Continuando sem Design System...")

    window = AOIControllerApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
