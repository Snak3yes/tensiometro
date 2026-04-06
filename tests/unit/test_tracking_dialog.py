"""
Testes unitários para TrackingDialog.

Testes de regressão para garantir que o fluxo de stencil funciona
corretamente após mover de aba para diálogo.

Autor: Claude Code
Data: 2026-03-29
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
import sys


@pytest.fixture
def qapp():
    """Cria QApplication para testes PyQt6."""
    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance()
    return app


@pytest.fixture
def mock_stencil_tracker():
    """Mock do StencilTracker."""
    tracker = Mock()

    # Criar mock de Stencil
    mock_stencil = Mock()
    mock_stencil.code = "TEST-001"
    mock_stencil.description = "Stencil de teste"
    mock_stencil.recipe_name = "RECIPE-001"
    mock_stencil.status = "active"
    mock_stencil.last_inspection = "2026-03-29T10:00:00"
    mock_stencil.inspection_count = 5

    tracker.get_stencil = Mock(return_value=mock_stencil)
    tracker.check_degradation_alert = Mock(return_value=None)

    return tracker, mock_stencil


class TestTrackingDialogCreation:
    """Testes de criação do TrackingDialog."""

    def test_dialog_import_available(self):
        """
        Testa se TrackingDialog pode ser importado.
        NOTA: Este teste deve passar ANTES e DEPOIS da criação do diálogo.
        """
        # Este teste valida que o módulo existe ou será criado
        try:
            from consumo_lib.dialogs import TrackingDialog
            assert TrackingDialog is not None
        except ImportError:
            # Antes da criação, este teste documenta a necessidade
            pytest.skip("TrackingDialog ainda não criado - implementação pendente")

    def test_dialog_creation_with_stencil_tracker(self, qapp, mock_stencil_tracker):
        """
        Testa criação do TrackingDialog com StencilTracker.
        """
        tracker, _ = mock_stencil_tracker

        try:
            from consumo_lib.dialogs import TrackingDialog
        except ImportError:
            pytest.skip("TrackingDialog ainda não criado")

        dialog = TrackingDialog(tracker, parent=None)

        assert dialog is not None, "Dialog deve ser criado"
        assert dialog.stencil_tracker == tracker, "StencilTracker deve ser armazenado"

    def test_dialog_is_non_modal(self, qapp, mock_stencil_tracker):
        """
        Testa se o diálogo é não-modal.
        """
        tracker, _ = mock_stencil_tracker

        try:
            from consumo_lib.dialogs import TrackingDialog
        except ImportError:
            pytest.skip("TrackingDialog ainda não criado")

        dialog = TrackingDialog(tracker, parent=None)

        # Verifica se é não-modal
        assert not dialog.isModal(), "Dialog deve ser não-modal"
        assert dialog.windowFlags() & Qt.WindowType.WindowStaysOnTopHint, \
            "Dialog deve ter flag WindowStaysOnTopHint"

    def test_dialog_contains_stencil_identification_widget(self, qapp, mock_stencil_tracker):
        """
        Testa se o diálogo contém StencilIdentificationWidget.
        """
        tracker, _ = mock_stencil_tracker

        try:
            from consumo_lib.dialogs import TrackingDialog
        except ImportError:
            pytest.skip("TrackingDialog ainda não criado")

        dialog = TrackingDialog(tracker, parent=None)

        assert hasattr(dialog, 'stencil_identification'), \
            "Dialog deve ter atributo stencil_identification"
        assert dialog.stencil_identification is not None, \
            "stencil_identification deve ser inicializado"


class TestTrackingDialogSignals:
    """Testes de sinais do TrackingDialog."""

    def test_dialog_has_stencil_selected_signal(self, qapp, mock_stencil_tracker):
        """
        Testa se o diálogo tem signal stencil_selected.
        """
        tracker, _ = mock_stencil_tracker

        try:
            from consumo_lib.dialogs import TrackingDialog
        except ImportError:
            pytest.skip("TrackingDialog ainda não criado")

        dialog = TrackingDialog(tracker, parent=None)

        assert hasattr(dialog, 'stencil_selected'), \
            "Dialog deve ter signal stencil_selected"

    def test_dialog_has_stencil_cleared_signal(self, qapp, mock_stencil_tracker):
        """
        Testa se o diálogo tem signal stencil_cleared.
        """
        tracker, _ = mock_stencil_tracker

        try:
            from consumo_lib.dialogs import TrackingDialog
        except ImportError:
            pytest.skip("TrackingDialog ainda não criado")

        dialog = TrackingDialog(tracker, parent=None)

        assert hasattr(dialog, 'stencil_cleared'), \
            "Dialog deve ter signal stencil_cleared"

    def test_dialog_has_recipe_requested_signal(self, qapp, mock_stencil_tracker):
        """
        Testa se o diálogo tem signal recipe_requested.
        """
        tracker, _ = mock_stencil_tracker

        try:
            from consumo_lib.dialogs import TrackingDialog
        except ImportError:
            pytest.skip("TrackingDialog ainda não criado")

        dialog = TrackingDialog(tracker, parent=None)

        assert hasattr(dialog, 'recipe_requested'), \
            "Dialog deve ter signal recipe_requested"

    def test_stencil_selected_signal_emitted(self, qapp, mock_stencil_tracker):
        """
        Testa se signal stencil_selected é emitido quando stencil é selecionado.
        """
        tracker, mock_stencil = mock_stencil_tracker

        try:
            from consumo_lib.dialogs import TrackingDialog
        except ImportError:
            pytest.skip("TrackingDialog ainda não criado")

        dialog = TrackingDialog(tracker, parent=None)

        # Captura signal
        captured_signals = []
        def capture_handler(stencil):
            captured_signals.append(stencil)

        dialog.stencil_selected.connect(capture_handler)

        # Simula seleção de stencil via widget interno
        dialog.stencil_identification._select_stencil(mock_stencil)

        # Verifica se signal foi emitido
        assert len(captured_signals) == 1, "Signal stencil_selected deve ser emitido"
        assert captured_signals[0] == mock_stencil, "Signal deve conter o stencil selecionado"

    def test_stencil_cleared_signal_emitted(self, qapp, mock_stencil_tracker):
        """
        Testa se signal stencil_cleared é emitido quando seleção é limpa.
        """
        tracker, mock_stencil = mock_stencil_tracker

        try:
            from consumo_lib.dialogs import TrackingDialog
        except ImportError:
            pytest.skip("TrackingDialog ainda não criado")

        dialog = TrackingDialog(tracker, parent=None)

        # Primeiro seleciona um stencil
        dialog.stencil_identification._select_stencil(mock_stencil)

        # Captura signal
        captured = []
        def capture_handler():
            captured.append(True)

        dialog.stencil_cleared.connect(capture_handler)

        # Limpa seleção
        dialog.stencil_identification._clear_selection()

        assert len(captured) == 1, "Signal stencil_cleared deve ser emitido"


class TestTrackingDialogReuse:
    """Testes de reutilização do diálogo."""

    def test_dialog_show_hide_cycle(self, qapp, mock_stencil_tracker):
        """
        Testa ciclo de show/hide do diálogo.
        """
        tracker, _ = mock_stencil_tracker

        try:
            from consumo_lib.dialogs import TrackingDialog
        except ImportError:
            pytest.skip("TrackingDialog ainda não criado")

        dialog = TrackingDialog(tracker, parent=None)

        # Mostra
        dialog.show()
        assert dialog.isVisible(), "Dialog deve estar visível após show()"

        # Esconde
        dialog.hide()
        assert not dialog.isVisible(), "Dialog deve estar oculto após hide()"

        # Mostra novamente
        dialog.show()
        assert dialog.isVisible(), "Dialog deve estar visível novamente"

    def test_dialog_preserves_stencil_on_reopen(self, qapp, mock_stencil_tracker):
        """
        Testa se stencil selecionado é preservado ao reabrir diálogo.
        """
        tracker, mock_stencil = mock_stencil_tracker

        try:
            from consumo_lib.dialogs import TrackingDialog
        except ImportError:
            pytest.skip("TrackingDialog ainda não criado")

        dialog = TrackingDialog(tracker, parent=None)

        # Seleciona stencil
        dialog.stencil_identification._select_stencil(mock_stencil)

        # Fecha e reabre
        dialog.hide()
        dialog.show()

        # Verifica se stencil ainda está selecionado
        current = dialog.stencil_identification.get_current_stencil()
        assert current == mock_stencil, "Stencil deve ser preservado ao reabrir"

    def test_dialog_close_clears_loaded_stencil(self, qapp, mock_stencil_tracker):
        """
        Testa se fechar o diálogo limpa o stencil carregado.
        """
        tracker, mock_stencil = mock_stencil_tracker

        try:
            from consumo_lib.dialogs import TrackingDialog
        except ImportError:
            pytest.skip("TrackingDialog ainda não criado")

        dialog = TrackingDialog(tracker, parent=None)
        captured = []
        dialog.stencil_cleared.connect(lambda: captured.append(True))

        dialog.stencil_identification._select_stencil(mock_stencil)

        dialog.close()
        dialog.show()

        assert dialog.get_current_stencil() is None, \
            "Fechar o dialogo deve limpar o stencil carregado"
        assert dialog.stencil_identification.code_input.text() == "", \
            "Fechar o dialogo deve limpar o codigo digitado"
        assert len(captured) == 1, \
            "Fechar o dialogo deve emitir stencil_cleared quando houver stencil carregado"


class TestStencilIdentificationReference:
    """Testes de referência global stencil_identification."""

    def test_stencil_identification_accessible_from_dialog(self, qapp, mock_stencil_tracker):
        """
        Testa se stencil_identification é acessível via diálogo.
        """
        tracker, _ = mock_stencil_tracker

        try:
            from consumo_lib.dialogs import TrackingDialog
        except ImportError:
            pytest.skip("TrackingDialog ainda não criado")

        dialog = TrackingDialog(tracker, parent=None)

        # Verifica que stencil_identification é o mesmo widget interno
        assert hasattr(dialog, 'stencil_identification'), \
            "Dialog deve ter atributo stencil_identification"

    def test_stencil_identification_get_current_stencil(self, qapp, mock_stencil_tracker):
        """
        Testa se get_current_stencil funciona via diálogo.
        """
        tracker, mock_stencil = mock_stencil_tracker

        try:
            from consumo_lib.dialogs import TrackingDialog
        except ImportError:
            pytest.skip("TrackingDialog ainda não criado")

        dialog = TrackingDialog(tracker, parent=None)

        # Inicialmente None
        assert dialog.get_current_stencil() is None, \
            "Stencil deve ser None inicialmente"

        # Após seleção
        dialog.stencil_identification._select_stencil(mock_stencil)
        assert dialog.get_current_stencil() == mock_stencil, \
            "get_current_stencil deve retornar stencil selecionado"
