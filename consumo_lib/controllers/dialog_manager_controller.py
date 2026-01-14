"""
DialogManagerController - Controller para Gerenciamento de Diálogos

Este controller gerencia a abertura de diálogos simples do sistema:
- Diálogo de gerenciamento de stencils
- Diálogo de novo stencil
- Diálogo de configurações de relatório
- Diálogo Sobre (About)
- Diálogo simples de medição de tensão

Responsabilidade:
- Abrir diálogos simples
- Validar pré-condições quando necessário
- Emitir signals quando diálogos são fechados

Signals Emitidos:
- dialog_closed(dialog_name) - Diálogo foi fechado
- stencil_created(stencil) - Novo stencil criado
- report_settings_updated(config) - Configurações de relatório atualizadas
"""

import logging
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QDialog, QMessageBox

logger = logging.getLogger("consumo_lib")


class DialogManagerController(QObject):
    """
    Controller para gerenciamento de diálogos simples.

    Responsável por abrir diálogos e notificar quando são fechados,
    centralizando a lógica de criação de diálogos simples.
    """

    # Signals
    dialog_closed = pyqtSignal(str)  # dialog_name
    stencil_created = pyqtSignal(object)  # stencil
    report_settings_updated = pyqtSignal(object)  # config

    def __init__(self, stencil_manager_wrapper, report_manager_wrapper,
                 report_config, controller, parent=None):
        """
        Inicializa o DialogManagerController.

        Args:
            stencil_manager_wrapper: Wrapper para gerenciar stencils
            report_manager_wrapper: Wrapper para gerenciar relatórios
            report_config: Configurações de relatório
            controller: Instância de CNCAOIController
            parent: Widget pai (geralmente main_window)
        """
        super().__init__(parent)
        self.stencil_manager_wrapper = stencil_manager_wrapper
        self.report_manager_wrapper = report_manager_wrapper
        self.report_config = report_config
        self.controller = controller
        self.parent_window = parent

        logger.debug("DialogManagerController inicializado")

    # =========================================================================
    # MÉTODOS PÚBLICOS
    # =========================================================================

    def show_stencil_manager(self):
        """
        Abre o diálogo de gerenciamento de stencils.

        Emits:
            dialog_closed signal quando diálogo fechar
        """
        self.stencil_manager_wrapper.show_manager(self.parent_window)
        logger.debug("Diálogo de gerenciamento de stencils aberto")
        self.dialog_closed.emit("stencil_manager")

    def show_new_stencil_dialog(self):
        """
        Abre o diálogo para criar um novo stencil.

        Emits:
            stencil_created signal se stencil criado
            dialog_closed signal quando diálogo fechar
        """
        stencil = self.stencil_manager_wrapper.create_new(self.parent_window)
        if stencil:
            QMessageBox.information(
                self.parent_window,
                "Sucesso",
                f"Stencil '{stencil.code}' cadastrado com sucesso!\n\n"
                "Escaneie ou digite o código para selecioná-lo."
            )
            logger.info(f"Novo stencil criado: {stencil.code}")
            self.stencil_created.emit(stencil)
        else:
            logger.debug("Criação de stencil cancelada")

        self.dialog_closed.emit("new_stencil")

    def show_report_settings(self):
        """
        Abre diálogo de configurações de relatório.

        Emits:
            report_settings_updated signal se config alterada
            dialog_closed signal quando diálogo fechar
        """
        from consumo_lib.dialogs import ReportSettingsDialog

        dialog = ReportSettingsDialog(self.report_config, self.parent_window)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_config = dialog.get_config()
            self.report_manager_wrapper.update_config(new_config, save=True)
            self.report_config = new_config  # Atualiza referência local

            logger.info("Configuração de relatórios atualizada e salva")
            self.parent_window.statusBar().showMessage(
                "Configurações de relatório salvas",
                3000
            )
            self.report_settings_updated.emit(new_config)
        else:
            logger.debug("Configurações de relatório canceladas")

        self.dialog_closed.emit("report_settings")

    def show_about_dialog(self):
        """
        Exibe o diálogo Sobre.

        Emits:
            dialog_closed signal quando diálogo fechar
        """
        from consumo_lib.dialogs.about import AboutDialog

        AboutDialog.show_about(self.parent_window)
        logger.debug("Diálogo Sobre exibido")
        self.dialog_closed.emit("about")

    def open_simple_tension_dialog(self):
        """
        Abre diálogo simples de medição de tensão (sem salvar no histórico).

        Valida pré-condições:
        - CNC deve estar conectada

        Emits:
            dialog_closed signal quando diálogo fechar
        """
        # Validar conexão CNC
        if not self.controller.cnc.is_connected:
            QMessageBox.warning(
                self.parent_window,
                "Aviso",
                "Conecte a CNC antes de medir a tensão do stencil."
            )
            logger.warning("Tentativa de abrir diálogo de tensão sem CNC conectada")
            self.dialog_closed.emit("tension_dialog")
            return

        # Importar diálogo aqui para evitar import circular
        from consumo_lib.dialogs.tension_measurement_dialog import StencilTensionDialog

        dlg = StencilTensionDialog(self.parent_window, self.controller.cnc)
        dlg.exec()
        logger.debug("Diálogo simples de tensão aberto")
        self.dialog_closed.emit("tension_dialog")
