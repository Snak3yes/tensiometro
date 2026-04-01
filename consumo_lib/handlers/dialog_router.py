"""
DialogRouter - Centraliza abertura de diálogos do main_window.

Este módulo contém o DialogRouter, que centraliza todos os métodos de abertura
de diálogos que antes estavam espalhados pelo main_window.

Responsabilidade:
- Abrir todos os diálogos da aplicação
- Delegar para controllers apropriados quando disponível
- Fallback para comportamento original se controller não existir
"""

import logging
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QMessageBox, QInputDialog
)

# Design System
from consumo_lib.ui.widget_standards import StandardButton
import cv2

logger = logging.getLogger(__name__)


class DialogRouter:
    """
    Centraliza todos os métodos de abertura de diálogos do main_window.

    Responsabilidade:
    - Gerenciar abertura de ~17 diálogos diferentes
    - Delegar para controllers quando disponível
    - Fallback para código original se controller não existir
    """

    def __init__(self, main_window):
        """
        Inicializa o DialogRouter.

        Args:
            main_window: Instância do AOIControllerApp
        """
        self.main_window = main_window
        self.window = main_window  # Alias para facilitar acesso

    # =========================================================================
    # SISTEMA DE RECEITAS
    # =========================================================================

    def show_recipe_manager(self):
        """
        Abre o diálogo de gerenciamento de receitas.

        Delega para RecipeManagerWrapper.
        """
        self.main_window.recipe_manager_wrapper.show_manager(self.window)

    def show_new_recipe_dialog(self):
        """
        Abre o diálogo para criar uma nova receita.

        Delega para RecipeManagerController.
        """
        if self.main_window.recipe_manager_controller is not None:
            self.main_window.recipe_manager_controller.show_new_recipe_dialog()
        else:
            logger.error("RecipeManagerController não está disponível")
            # Fallback: código original
            from consumo_lib.recipe_dialog import RecipeDialog
            success = self.main_window.recipe_manager_wrapper.create_new(self.window)
            if success:
                QMessageBox.information(
                    self.window, "Sucesso",
                    "Receita criada com sucesso!\n\n"
                    "Acesse Receitas > Gerenciar Receitas para carregar."
                )

    # =========================================================================
    # SISTEMA DE RASTREABILIDADE (STENCILS)
    # =========================================================================

    def show_stencil_manager(self):
        """
        Abre o diálogo de gerenciamento de stencils.

        Delega para DialogManagerController.
        """
        if self.main_window.dialog_manager_controller is not None:
            self.main_window.dialog_manager_controller.show_stencil_manager()
        else:
            logger.error("DialogManagerController não está disponível")
            self.main_window.stencil_manager_wrapper.show_manager(self.window)

    def show_new_stencil_dialog(self):
        """
        Abre diálogo para criar novo stencil.

        Delega para DialogManagerController.
        """
        if self.main_window.dialog_manager_controller is not None:
            self.main_window.dialog_manager_controller.show_new_stencil_dialog()
        else:
            logger.error("DialogManagerController não está disponível")
            from consumo_lib.recipe_dialog import NewStencilDialog
            dialog = NewStencilDialog(
                self.main_window.stencil_tracker,
                self.main_window.recipe_manager_wrapper,
                self.window
            )
            if dialog.exec() == QDialog.DialogCode.Accepted:
                stencil = dialog.get_stencil()
                if stencil:
                    self.main_window.stencil_manager_wrapper.add_stencil(stencil)
                    logger.info(f"Novo stencil criado: {stencil.code}")

    # =========================================================================
    # FERRAMENTAS DE CALIBRAÇÃO
    # =========================================================================

    def show_camera_calibration_dialog(self):
        """Abre diálogo para calibração de câmera (correção de distorção)"""
        if not hasattr(self.main_window.controller.camera, 'is_connected') or \
           not self.main_window.controller.camera.is_connected:
            QMessageBox.warning(self.window, "Aviso", "Conecte a câmera antes de calibrar.")
            return

        from camera_calibration import CameraCalibrationDialog
        self.main_window.camera_calib_dialog = CameraCalibrationDialog(
            self.main_window.controller.camera, self.window
        )
        self.main_window.camera_calib_dialog.resize(900, 750)
        self.main_window.camera_calib_dialog.show()

    def show_fov_calibration_dialog(self):
        """
        Abre diálogo para calibração de Campo de Visão (FOV).

        Esta calibração define a relação entre pixels da câmera e dimensões físicas (mm)
        em diferentes alturas Z, permitindo conversão precisa de clique no vídeo para
        movimento da head.
        """
        # Cria adaptador para o ConfigManager para usar o formato esperado pelo diálogo
        class ConfigAdapter:
            def __init__(self, cfg):
                self._cfg = cfg

            def get_config(self, key, default=None):
                if key == "camera_fov":
                    return self._cfg.get("camera", "fov_calibration", default=default or {})
                return default

            def set_config(self, key, value):
                if key == "camera_fov":
                    self._cfg.set("camera", "fov_calibration", value=value)
                    self._cfg.save()

        from aoi_lib.fov_calibration import FOVCalibrationDialog

        adapter = ConfigAdapter(self.main_window.config)

        dialog = FOVCalibrationDialog(adapter, self.window)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Atualiza o conversor FOV do CameraPreviewWidget
            if hasattr(self.main_window, 'camera_preview') and \
               hasattr(self.main_window.camera_preview, 'fov_converter'):
                fov = dialog.get_calibration()
                self.main_window.camera_preview.fov_converter.set_fov_calibration(fov)
                logger.info(f"Calibração de FOV atualizada: {fov}")

            QMessageBox.information(
                self.window, "Calibração Salva",
                "A calibração de campo de visão foi salva.\n\n"
                "Agora você pode usar o clique no vídeo para mover a head\n"
                "com precisão baseada na altura Z atual."
            )

    def show_crosshair_settings_dialog(self):
        """
        Abre diálogo para configurar a cruz de centralização da câmera.

        Permite ajustar:
        - Cor da linha (seletor de cor visual)
        - Espessura da linha (1-10 pixels)
        - Comprimento da linha (1-50% da menor dimensão)
        """
        from aoi_lib.crosshair_settings import CrosshairSettingsDialog

        dialog = CrosshairSettingsDialog(self.main_window.config, self.window)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(
                self.window, "Configurações Salvas",
                "As configurações da cruz foram salvas.\n\n"
                "As mudanças serão aplicadas na próxima atualização do preview."
            )

    # =========================================================================
    # SISTEMA DE RELATÓRIOS
    # =========================================================================

    def show_report_settings(self):
        """
        Abre diálogo de configurações de relatório.

        Delega para DialogManagerController.
        """
        if self.main_window.dialog_manager_controller is not None:
            self.main_window.dialog_manager_controller.show_report_settings()
        else:
            logger.error("DialogManagerController não está disponível")
            from consumo_lib.recipe_dialog import ReportSettingsDialog
            dialog = ReportSettingsDialog(self.main_window.report_config, self.window)

            if dialog.exec() == QDialog.DialogCode.Accepted:
                new_config = dialog.get_config()
                self.main_window.report_manager_wrapper.update_config(new_config, save=True)
                self.main_window.report_config = new_config  # Atualiza referência local

                logger.info("Configuração de relatórios atualizada e salva")
                self.window.statusBar().showMessage("Configurações de relatório salvas", 3000)

    def show_tension_report_dialog(self):
        """Gera relatório de tensão da última medição."""
        if self.main_window.report_dialog_controller is not None:
            self.main_window.report_dialog_controller.show_tension_report_dialog()
        else:
            logger.error("ReportDialogController não está disponível")
            QMessageBox.warning(self.window, "Erro", "ReportDialogController não está disponível")

    def show_stencil_report_dialog(self):
        """Gera relatório de histórico do stencil selecionado."""
        if self.main_window.report_dialog_controller is not None:
            self.main_window.report_dialog_controller.show_stencil_report_dialog()
        else:
            logger.error("ReportDialogController não está disponível")
            QMessageBox.warning(self.window, "Erro", "ReportDialogController não está disponível")

    def show_period_query_dialog(self):
        """Abre diálogo para consultar medições por período."""
        if self.main_window.report_dialog_controller is not None:
            self.main_window.report_dialog_controller.show_period_query_dialog()
        else:
            logger.error("ReportDialogController não está disponível")
            QMessageBox.warning(self.window, "Erro", "ReportDialogController não está disponível")

    # =========================================================================
    # DIÁLOGOS GERAIS
    # =========================================================================

    def show_settings_dialog(self):
        """Abre diálogo de configurações gerais da aplicação."""
        from consumo_lib.main_window import SettingsDialog

        dlg = SettingsDialog(self.main_window.config, self.window)
        if dlg.exec():
            # Se o usuário modificou algo, re-aplica (se a CNC já estiver conectada)
            if self.main_window.controller.cnc.is_connected:
                self.main_window.config.apply_to_cnc(self.main_window.controller.cnc)
            # Atualiza campos rápidos de conexão do PLC
            if hasattr(self.window, "plc_host_input"):
                self.window.plc_host_input.setText(
                    self.main_window.config.get("connections", "plc_host", default="192.168.1.5")
                )
            if hasattr(self.window, "plc_port_input"):
                self.window.plc_port_input.setValue(
                    self.main_window.config.get("connections", "plc_port", default=502)
                )

    def show_about_dialog(self):
        """
        Exibe o diálogo Sobre.

        Delega para DialogManagerController.
        """
        if self.main_window.dialog_manager_controller is not None:
            self.main_window.dialog_manager_controller.show_about_dialog()
        else:
            logger.error("DialogManagerController não está disponível")
            from consumo_lib.dialogs import AboutDialog
            dialog = AboutDialog(self.window)
            dialog.exec()

    def show_permissions_info(self):
        """
        Exibe informações sobre as permissões do usuário atual.
        """
        from consumo_lib.managers import UserRole

        user = self.main_window.auth_service.get_current_user()
        if not user:
            QMessageBox.warning(
                self.window, "Usuário Não Logado",
                "Nenhum usuário está logado no momento."
            )
            return

        # Obtém role atual
        current_role = self.main_window.role_manager.get_current_role()

        # Mapeia role para nome legível
        role_names = {
            UserRole.OPERATOR: "Operador",
            UserRole.ENGINEERING: "Engenharia",
            UserRole.QUALITY: "Qualidade",
            UserRole.ADMIN: "Administrador"
        }

        # Handle both enum and string cases
        if isinstance(current_role, UserRole):
            role_name = role_names.get(current_role, current_role.value)
        else:
            # current_role is a string
            role_name = current_role if current_role else "Desconhecido"

        # Obtém lista de permissões
        permissions = self.main_window.role_manager.get_all_permissions_for_role(current_role if isinstance(current_role, str) else current_role.value)

        # Cria mensagem
        message = f"Usuário: {user.username}\n"
        message += f"Role: {role_name}\n\n"
        message += "Permissões:\n"
        for perm in permissions:
            message += f"  • {perm}\n"

        QMessageBox.information(
            self.window, "Permissões do Usuário",
            message
        )
