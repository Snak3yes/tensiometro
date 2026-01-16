"""
Smoke Test - Aplicação Principal

Teste simples que valida que a aplicação principal abre sem erros.

Este é o ÚNICO teste que pode abrir janelas PyQt6.
Roda em modo offscreen (sem exibir janelas) graças ao pytest-qt.
"""
import pytest
import sys
from pathlib import Path

# Adiciona diretório raiz ao sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))


@pytest.mark.slow
def test_main_application_opens_without_errors(qtbot):
    """
    Smoke Test: Valida que a aplicação principal abre sem erros.

    Este é o único teste que abre a janela principal.
    Usa qtbot do pytest-qt para rodar em modo offscreen (sem exibir janelas).

    Args:
        qtbot: Fixture do pytest-qt para testes PyQt6
    """
    from PyQt6.QtWidgets import QApplication, QMainWindow
    from consumo_lib.main_window import AOIControllerApp

    # Criar QApplication (pytest-qt já configura modo offscreen)
    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    # Criar janela principal
    window = AOIControllerApp()

    # Validar que é uma QMainWindow
    assert isinstance(window, QMainWindow)

    # Validar que foi criada
    assert window is not None
    assert window.windowTitle() != ""

    # Limpeza manual (não usamos qtbot.addWidget para evitar problemas de tipo)
    window.close()

    # Processar eventos pendentes com qtbot
    qtbot.wait(100)  # Aguarda 100ms para processar eventos

    # Sucesso
    assert True
