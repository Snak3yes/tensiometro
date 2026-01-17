"""
Testes para validação do botão Concluir em ambos os modos de navegação.

Autor: Claude Code (Sonnet 4.5)
Data: 2026-01-17
"""

import pytest
from unittest.mock import Mock, patch


class TestFinishValidation:
    """Testes para validação do botão Concluir."""

    def test_finish_validates_all_tabs_in_free_navigation_mode(self):
        """
        Testa se _on_finish valida todas as abas mesmo em modo livre.
        """
        # Arrange: Mock config manager retornando free_navigation=True
        with patch('consumo_lib.dialogs.engineering_wizard_dialog.AOIConfigManager') as mock_config_cls:
            mock_config_mgr = Mock()
            mock_config_mgr.get_free_navigation_enabled = Mock(return_value=True)
            mock_config_cls.return_value = mock_config_mgr

            from consumo_lib.dialogs.engineering_wizard_dialog import EngineeringWizardDialog

            with patch.object(EngineeringWizardDialog, '_setup_ui'):
                with patch.object(EngineeringWizardDialog, '_connect_signals'):
                    with patch.object(EngineeringWizardDialog, '_update_ui_state'):
                        with patch.object(EngineeringWizardDialog, '_setup_keyboard_shortcuts'):
                            with patch.object(EngineeringWizardDialog, '_setup_tooltips'):
                                wizard = EngineeringWizardDialog()

            # Configurar estado: algumas abas inválidas
            wizard.current_tab = 6  # Última aba
            wizard.state = Mock()
            wizard.state.is_valid = Mock(side_effect=lambda i: i in [0, 1, 2])  # Apenas 3 abas válidas
            wizard.state.is_dirty = False

            # Act: Chamar _on_finish
            with patch('consumo_lib.dialogs.engineering_wizard_dialog.QMessageBox') as mock_msgbox:
                wizard._on_finish()

                # Assert: QMessageBox.warning deve ser chamado (algumas abas inválidas)
                mock_msgbox.warning.assert_called_once()
                call_args = mock_msgbox.warning.call_args[0]
                assert "Complete todas as abas" in call_args[1]

    def test_finish_validates_all_tabs_in_normal_mode(self):
        """
        Testa se _on_finish valida todas as abas em modo normal.
        """
        # Arrange: Mock config manager retornando free_navigation=False
        with patch('consumo_lib.dialogs.engineering_wizard_dialog.AOIConfigManager') as mock_config_cls:
            mock_config_mgr = Mock()
            mock_config_mgr.get_free_navigation_enabled = Mock(return_value=False)
            mock_config_cls.return_value = mock_config_mgr

            from consumo_lib.dialogs.engineering_wizard_dialog import EngineeringWizardDialog

            with patch.object(EngineeringWizardDialog, '_setup_ui'):
                with patch.object(EngineeringWizardDialog, '_connect_signals'):
                    with patch.object(EngineeringWizardDialog, '_update_ui_state'):
                        with patch.object(EngineeringWizardDialog, '_setup_keyboard_shortcuts'):
                            with patch.object(EngineeringWizardDialog, '_setup_tooltips'):
                                wizard = EngineeringWizardDialog()

            # Configurar estado: algumas abas inválidas
            wizard.current_tab = 6  # Última aba
            wizard.state = Mock()
            wizard.state.is_valid = Mock(side_effect=lambda i: i in [0, 1, 2, 3, 4])  # 5 abas válidas
            wizard.state.is_dirty = False

            # Act: Chamar _on_finish
            with patch('consumo_lib.dialogs.engineering_wizard_dialog.QMessageBox') as mock_msgbox:
                wizard._on_finish()

                # Assert: QMessageBox.warning deve ser chamado (algumas abas inválidas)
                mock_msgbox.warning.assert_called_once()

    def test_finish_saves_when_all_valid_free_mode(self):
        """
        Testa se _on_finish salva programa quando todas abas válidas (modo livre).
        """
        # Arrange: Mock config manager e wizard com todas abas válidas
        with patch('consumo_lib.dialogs.engineering_wizard_dialog.AOIConfigManager') as mock_config_cls:
            mock_config_mgr = Mock()
            mock_config_mgr.get_free_navigation_enabled = Mock(return_value=True)
            mock_config_cls.return_value = mock_config_mgr

            from consumo_lib.dialogs.engineering_wizard_dialog import EngineeringWizardDialog

            with patch.object(EngineeringWizardDialog, '_setup_ui'):
                with patch.object(EngineeringWizardDialog, '_connect_signals'):
                    with patch.object(EngineeringWizardDialog, '_update_ui_state'):
                        with patch.object(EngineeringWizardDialog, '_setup_keyboard_shortcuts'):
                            with patch.object(EngineeringWizardDialog, '_setup_tooltips'):
                                wizard = EngineeringWizardDialog()

            # Configurar estado: todas abas válidas
            wizard.current_tab = 6
            wizard.state = Mock()
            wizard.state.is_valid = Mock(return_value=True)  # Todas válidas
            wizard.state.is_dirty = False
            wizard.state.update_timestamp = Mock()
            wizard._compile_program_config = Mock(return_value={'test': 'config'})

            # Act: Chamar _on_finish
            with patch('consumo_lib.dialogs.engineering_wizard_dialog.QMessageBox') as mock_msgbox:
                mock_msgbox.question = Mock(return_value=mock_msgbox.StandardButton.Yes)

                with patch.object(wizard, 'program_completed') as mock_signal:
                    with patch.object(wizard, '_cleanup_auto_saves'):
                        with patch.object(wizard, 'accept') as mock_accept:
                            wizard._on_finish()

                            # Assert: program_completed.emit deve ser chamado
                            mock_signal.emit.assert_called_once()

    def test_finish_saves_when_all_valid_normal_mode(self):
        """
        Testa se _on_finish salva programa quando todas abas válidas (modo normal).
        """
        # Arrange: Mock config manager retornando free_navigation=False
        with patch('consumo_lib.dialogs.engineering_wizard_dialog.AOIConfigManager') as mock_config_cls:
            mock_config_mgr = Mock()
            mock_config_mgr.get_free_navigation_enabled = Mock(return_value=False)
            mock_config_cls.return_value = mock_config_mgr

            from consumo_lib.dialogs.engineering_wizard_dialog import EngineeringWizardDialog

            with patch.object(EngineeringWizardDialog, '_setup_ui'):
                with patch.object(EngineeringWizardDialog, '_connect_signals'):
                    with patch.object(EngineeringWizardDialog, '_update_ui_state'):
                        with patch.object(EngineeringWizardDialog, '_setup_keyboard_shortcuts'):
                            with patch.object(EngineeringWizardDialog, '_setup_tooltips'):
                                wizard = EngineeringWizardDialog()

            # Configurar estado: todas abas válidas
            wizard.current_tab = 6
            wizard.state = Mock()
            wizard.state.is_valid = Mock(return_value=True)
            wizard.state.is_dirty = False
            wizard.state.update_timestamp = Mock()
            wizard._compile_program_config = Mock(return_value={'test': 'config'})

            # Act: Chamar _on_finish
            with patch('consumo_lib.dialogs.engineering_wizard_dialog.QMessageBox') as mock_msgbox:
                mock_msgbox.question = Mock(return_value=mock_msgbox.StandardButton.Yes)

                with patch.object(wizard, 'program_completed') as mock_signal:
                    with patch.object(wizard, '_cleanup_auto_saves'):
                        with patch.object(wizard, 'accept') as mock_accept:
                            wizard._on_finish()

                            # Assert: program_completed.emit deve ser chamado
                            mock_signal.emit.assert_called_once()
