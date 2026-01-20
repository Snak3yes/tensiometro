"""
FiducialAlignmentController - Controller para Alinhamento de Fiduciais

Este controller gerencia o diálogo de alinhamento de fiduciais, permitindo:
- Carregar arquivo Gerber e detectar fiduciais automaticamente
- Capturar templates de fiduciais da câmera ou mosaico
- Calcular transformação (translação, rotação, escala) para alinhar
- Ajuste fino manual da transformação

Responsabilidade:
- Gerenciar diálogo de alinhamento
- Carregar mosaico automaticamente
- Configurar callbacks da câmera
- Salvar transformação nas configurações

Signals Emitidos:
- alignment_completed(transform) - Alinhamento completado com sucesso
- alignment_cancelled() - Alinhamento cancelado pelo usuário
- alignment_error(error) - Erro durante o alinhamento
"""

import os
import logging
from typing import Optional, Callable

import cv2
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QMessageBox
)
from PyQt6.QtCore import QObject, pyqtSignal

from aoi_lib.fiducial_alignment_widget import FiducialAlignmentWidget

from consumo_lib.ui.widget_standards import StandardButton

logger = logging.getLogger("consumo_lib")


class FiducialAlignmentController(QObject):
    """
    Controller para alinhamento de fiduciais.

    Responsável por gerenciar todo o fluxo de UI para alinhamento
    de fiduciais, incluindo carregamento de imagens e salvamento
    da transformação calculada.
    """

    # Signals
    alignment_completed = pyqtSignal(object)  # transform
    alignment_cancelled = pyqtSignal()
    alignment_error = pyqtSignal(str)  # error

    def __init__(self, config_manager, camera_controller, parent=None):
        """
        Inicializa o FiducialAlignmentController.

        Args:
            config_manager: Instância de AOIConfigManager
            camera_controller: Instância de CameraController
            parent: Widget pai (geralmente main_window)
        """
        super().__init__(parent)
        self.config = config_manager
        self.camera_controller = camera_controller
        self.parent_window = parent

        logger.debug("FiducialAlignmentController inicializado")

    # =========================================================================
    # MÉTODOS PÚBLICOS
    # =========================================================================

    def show_dialog(self):
        """
        Exibe o diálogo de alinhamento de fiduciais.

        O diálogo permite:
        - Carregar arquivo Gerber e detectar fiduciais automaticamente
        - Capturar templates de fiduciais da câmera ou mosaico
        - Calcular transformação (translação, rotação, escala)
        - Ajuste fino manual da transformação

        Returns:
            A transformação calculada ou None se cancelado
        """
        dialog = QDialog(self.parent_window)
        dialog.setWindowTitle("🎯 Alinhamento de Fiduciais")
        dialog.setMinimumSize(1000, 700)
        dialog.resize(1200, 800)

        layout = QVBoxLayout(dialog)

        # Widget principal de alinhamento
        alignment_widget = FiducialAlignmentWidget()
        layout.addWidget(alignment_widget)

        # Carrega mosaico recente se disponível
        self._load_recent_mosaic(alignment_widget)

        # Configura callback para captura de frame da câmera
        alignment_widget.set_frame_callback(self._get_camera_frame)

        # Conecta sinais
        alignment_widget.alignmentComplete.connect(
            lambda transform: self._on_alignment_complete(dialog, transform)
        )
        alignment_widget.alignmentCancelled.connect(
            lambda: self._on_alignment_cancelled(dialog)
        )

        # Botões de arquivo para carregar imagem
        btn_layout = QHBoxLayout()

        btn_load_image = StandardButton("📷 Carregar Imagem/Mosaico")
        btn_load_image.clicked.connect(
            lambda: self._load_image(dialog, alignment_widget)
        )
        btn_layout.addWidget(btn_load_image)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Executa diálogo (modal)
        result = dialog.exec()

        # Retorna resultado
        if result == QDialog.DialogCode.Accepted:
            # Transformação foi salva no _on_alignment_complete
            return True
        else:
            self.alignment_cancelled.emit()
            return None

    # =========================================================================
    # MÉTODOS PRIVADOS
    # =========================================================================

    def _load_recent_mosaic(self, alignment_widget):
        """
        Carrega o mosaico mais recente no widget de alinhamento.

        Args:
            alignment_widget: Instância de FiducialAlignmentWidget
        """
        mosaic_path = self.config.get("mosaic", "last_output_path", default=None)

        if mosaic_path and os.path.exists(mosaic_path):
            try:
                img = cv2.imread(mosaic_path)
                if img is not None:
                    alignment_widget.set_image(img)
                    logger.info(f"Mosaico carregado para alinhamento: {mosaic_path}")
            except Exception as e:
                logger.warning(f"Erro ao carregar mosaico: {e}")

    def _get_camera_frame(self):
        """
        Obtém um frame da câmera.

        Returns:
            Frame da câmera (numpy array) ou None se não disponível
        """
        try:
            if (self.camera_controller and
                hasattr(self.camera_controller, 'is_connected') and
                self.camera_controller.is_connected):

                frame = self.camera_controller.get_frame()
                return frame
        except Exception as e:
            logger.warning(f"Erro ao obter frame da câmera: {e}")

        return None

    def _load_image(self, dialog, alignment_widget):
        """
        Carrega uma imagem de arquivo para o widget de alinhamento.

        Args:
            dialog: Diálogo pai
            alignment_widget: Instância de FiducialAlignmentWidget
        """
        filepath, _ = QFileDialog.getOpenFileName(
            dialog,
            "Carregar Imagem",
            "",
            "Imagens (*.png *.jpg *.bmp *.tiff);;All Files (*)"
        )

        if filepath:
            try:
                img = cv2.imread(filepath)
                if img is not None:
                    alignment_widget.set_image(img)
                    logger.info(f"Imagem carregada: {filepath}")
                else:
                    QMessageBox.warning(
                        dialog,
                        "Erro de Leitura",
                        f"Não foi possível ler a imagem:\n{filepath}"
                    )
            except Exception as e:
                logger.exception("Erro ao carregar imagem")
                QMessageBox.critical(
                    dialog,
                    "Erro",
                    f"Erro ao carregar imagem:\n{str(e)}"
                )

    def _on_alignment_complete(self, dialog, transform):
        """
        Handler chamado quando o alinhamento é completado.

        Args:
            dialog: Diálogo a ser fechado
            transform: Transformação calculada
        """
        try:
            # Log da transformação
            logger.info(
                f"Alinhamento calculado: tx={transform.tx:.1f}, ty={transform.ty:.1f}, "
                f"angle={transform.angle:.2f}°, scale={transform.scale_x:.4f}"
            )

            # Salvar transformação nas configurações
            self.config.set("fiducial_alignment", "last_tx", value=transform.tx)
            self.config.set("fiducial_alignment", "last_ty", value=transform.ty)
            self.config.set("fiducial_alignment", "last_angle", value=transform.angle)
            self.config.set("fiducial_alignment", "last_scale", value=transform.scale_x)
            self.config.save()

            # Mostrar mensagem de sucesso
            QMessageBox.information(
                dialog,
                "Alinhamento Aplicado",
                f"Transformação calculada:\n\n"
                f"📍 Translação: ({transform.tx:.1f}, {transform.ty:.1f}) px\n"
                f"🔄 Rotação: {transform.angle:.2f}°\n"
                f"📐 Escala: {transform.scale_x:.4f}\n\n"
                f"Os valores foram salvos nas configurações."
            )

            # Fecha diálogo
            dialog.accept()

            # Emite signal
            self.alignment_completed.emit(transform)

        except Exception as e:
            logger.exception("Erro ao salvar alinhamento")
            error_msg = f"Erro ao salvar alinhamento:\n{str(e)}"
            self.alignment_error.emit(error_msg)
            QMessageBox.critical(dialog, "Erro", error_msg)

    def _on_alignment_cancelled(self, dialog):
        """
        Handler chamado quando o alinhamento é cancelado.

        Args:
            dialog: Diálogo a ser fechado
        """
        logger.info("Alinhamento de fiduciais cancelado")
        dialog.reject()
        self.alignment_cancelled.emit()

    # =========================================================================
    # UI HANDLERS (Migrados do SignalAggregator)
    # =========================================================================

    def setup_ui_handlers(self):
        """
        Configura handlers de UI para signals de alinhamento fiducial.

        Este método conecta os signals internos do FiducialAlignmentController
        aos métodos que atualizam a UI do main_window.

        Deve ser chamado durante a inicialização do main_window.
        """
        # Conectar signals a handlers de UI
        self.alignment_completed.connect(self._on_alignment_completed_update_ui)
        self.alignment_cancelled.connect(self._on_alignment_cancelled_update_status)
        self.alignment_error.connect(self._on_alignment_error_show_message)

        logger.debug("UI handlers conectados no FiducialAlignmentController")

    def _on_alignment_completed_update_ui(self, transform):
        """
        Atualiza UI quando alinhamento de fiduciais é completado.

        Args:
            transform: Transformação calculada
        """
        logger.info(f"Alinhamento de fiduciais completado: {transform}")

        if hasattr(self.parent(), 'statusBar'):
            self.parent().statusBar().showMessage(
                f"Fiduciais alinhados - Transformação: {transform}",
                5000
            )

    def _on_alignment_cancelled_update_status(self):
        """
        Atualiza statusBar quando alinhamento é cancelado.
        """
        logger.info("Alinhamento de fiduciais cancelado")
        if hasattr(self.parent(), 'statusBar'):
            self.parent().statusBar().showMessage("Alinhamento cancelado", 3000)

    def _on_alignment_error_show_message(self, error):
        """
        Mostra mensagem de erro quando alinhamento falha.

        Args:
            error: Mensagem de erro
        """
        logger.error(f"Erro no alinhamento de fiduciais: {error}")
        if hasattr(self.parent(), 'statusBar'):
            self.parent().statusBar().showMessage(f"Erro de alinhamento: {error}", 5000)
