"""
Smoke Test - Aplicação Principal

Teste simples que valida que a aplicação principal abre sem erros.

Este é o ÚNICO teste que pode abrir janelas PyQt6.
"""
import pytest
import sys
from pathlib import Path

# Adiciona diretório raiz ao sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))


@pytest.mark.slow
def test_main_application_opens_without_errors():
    """
    Smoke Test: Valida que a aplicação principal abre sem erros.

    Este é o único teste que abre a janela principal.
    """
    from PyQt6.QtWidgets import QApplication
    from consumo_lib.main_window import AOIControllerApp

    # Criar QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    # Criar janela principal
    window = AOIControllerApp()

    # Validar que foi criada
    assert window is not None
    assert window.windowTitle() != ""

    # Limpeza
    window.close()
    window.deleteLater()

    # Sucesso
    assert True
