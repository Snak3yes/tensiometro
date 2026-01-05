"""
InspectionUIController - Controller para UI de Inspeção Visual

Este controller gerencia a interface de usuário para execução de inspeção visual,
incluindo diálogo de configuração e exibição de resultados.

Responsabilidade:
- Criar e gerenciar diálogo de inspeção
- Coletar parâmetros de entrada (Gerber, mosaico, alinhamento)
- Executar inspeção via InspectionManager
- Exibir resultados em janela dedicada
- Gerenciar exportação de PDF

Signals Emitidos:
- inspection_requested(gerber_file: str) - Inspeção solicitada
- inspection_completed(result: InspectionResult, overlay: np.ndarray) - Inspeção completada
- inspection_failed(error: str) - Inspeção falhou
- settings_updated(thresholds: InspectionThresholds) - Configurações atualizadas
"""

import os
import logging
from typing import Optional
from pathlib import Path

import cv2
import numpy as np
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QGroupBox, QFormLayout, QLineEdit,
    QCheckBox, QFileDialog, QMessageBox, QApplication,
    QProgressBar
)
from PyQt6.QtCore import QObject, pyqtSignal

from aoi_lib.stencil_inspector import InspectionResult, InspectionThresholds
from aoi_lib.inspection_result_viewer import InspectionResultWidget
from consumo_lib.dialogs import InspectionSettingsDialog

logger = logging.getLogger("consumo_lib")


class InspectionUIController(QObject):
    """
    Controller para UI de inspeção visual.

    Responsável por gerenciar todo o fluxo de UI para inspeção visual,
    desde a seleção de arquivos até a exibição de resultados.
    """

    # Signals
    inspection_requested = pyqtSignal(str)  # gerber_file
    inspection_completed = pyqtSignal(object, object)  # result, overlay
    inspection_failed = pyqtSignal(str)  # error
    settings_updated = pyqtSignal(object)  # thresholds

    def __init__(self, inspection_manager, config_manager, parent=None):
        """
        Inicializa o InspectionUIController.

        Args:
            inspection_manager: Instância de InspectionManager
            config_manager: Instância de AOIConfigManager
            parent: Widget pai (geralmente main_window)
        """
        super().__init__(parent)
        self.inspection_manager = inspection_manager
        self.config = config_manager
        self.parent_window = parent

        # Estado interno
        self._last_result: Optional[InspectionResult] = None
        self._last_overlay: Optional[np.ndarray] = None

        # Componentes de UI (preenchidos durante show_dialog)
        self._dialog: Optional[QDialog] = None
        self._gerber_path_input: Optional[QLineEdit] = None
        self._mosaic_path_input: Optional[QLineEdit] = None
        self._use_alignment_checkbox: Optional[QCheckBox] = None
        self._status_label: Optional[QLabel] = None
        self._progress_bar: Optional[QProgressBar] = None

        logger.debug("InspectionUIController inicializado")

    # =========================================================================
    # MÉTODOS PÚBLICOS
    # =========================================================================

    def show_dialog(self, current_stencil=None, inspection_thresholds=None):
        """
        Exibe o diálogo de inspeção visual.

        Args:
            current_stencil: Stencil atual (opcional)
            inspection_thresholds: Thresholds de inspeção (opcional)
        """
        self._create_inspection_dialog(current_stencil, inspection_thresholds)

    def show_settings_dialog(self, inspection_thresholds):
        """
        Exibe o diálogo de configuração de parâmetros de inspeção.

        Args:
            inspection_thresholds: Thresholds atuais de inspeção
        """
        dialog = InspectionSettingsDialog(inspection_thresholds, self.parent_window)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_thresholds = dialog.get_thresholds()
            self.inspection_manager.update_thresholds(new_thresholds, save=True)

            logger.info("Parâmetros de inspeção atualizados e salvos")
            self.settings_updated.emit(new_thresholds)

    def show_last_result(self):
        """Exibe o último resultado de inspeção."""
        if self._last_result is None:
            QMessageBox.information(
                self.parent_window, "Sem Resultado",
                "Nenhuma inspeção foi executada ainda.\n\n"
                "Use 'Inspeção Visual' → 'Executar Inspeção' para realizar uma inspeção."
            )
            return

        self._show_result_dialog(self._last_result, self._last_overlay)

    def run_inspection(self):
        """Executa a inspeção com os parâmetros configurados."""
        if self._dialog is None:
            logger.warning("Tentativa de executar inspeção sem diálogo aberto")
            return

        gerber_path = self._gerber_path_input.text()
        mosaic_path = self._mosaic_path_input.text()

        # Validar entradas
        if not gerber_path or not os.path.exists(gerber_path):
            QMessageBox.warning(self._dialog, "Erro", "Selecione um arquivo Gerber válido.")
            return

        if not mosaic_path or not os.path.exists(mosaic_path):
            QMessageBox.warning(self._dialog, "Erro", "Selecione uma imagem de mosaico válida.")
            return

        self._execute_inspection(gerber_path, mosaic_path)

    # =========================================================================
    # MÉTODOS PRIVADOS - CRIAÇÃO DE UI
    # =========================================================================

    def _create_inspection_dialog(self, current_stencil, inspection_thresholds):
        """Cria o diálogo de inspeção."""
        self._dialog = QDialog(self.parent_window)
        self._dialog.setWindowTitle("🔬 Inspeção Visual de Stencil")
        self._dialog.setMinimumWidth(600)

        layout = QVBoxLayout(self._dialog)

        # Grupo: Arquivos
        files_group = QGroupBox("📁 Arquivos de Entrada")
        files_layout = QFormLayout(files_group)

        # Gerber
        gerber_layout = QHBoxLayout()
        self._gerber_path_input = QLineEdit()
        self._gerber_path_input.setPlaceholderText("Selecione o arquivo Gerber...")
        gerber_layout.addWidget(self._gerber_path_input)
        btn_browse_gerber = QPushButton("📁")
        btn_browse_gerber.clicked.connect(self._browse_gerber)
        gerber_layout.addWidget(btn_browse_gerber)
        files_layout.addRow("Arquivo Gerber:", gerber_layout)

        # Mosaico
        mosaic_layout = QHBoxLayout()
        self._mosaic_path_input = QLineEdit()
        self._mosaic_path_input.setPlaceholderText("Selecione a imagem do mosaico...")

        # Auto-preencher com último mosaico
        last_mosaic = self.config.get("mosaic", "last_output_path", default="")
        if last_mosaic and os.path.exists(last_mosaic):
            self._mosaic_path_input.setText(last_mosaic)

        mosaic_layout.addWidget(self._mosaic_path_input)
        btn_browse_mosaic = QPushButton("📁")
        btn_browse_mosaic.clicked.connect(self._browse_mosaic)
        mosaic_layout.addWidget(btn_browse_mosaic)
        files_layout.addRow("Imagem Mosaico:", mosaic_layout)

        layout.addWidget(files_group)

        # Grupo: Informações
        info_group = QGroupBox("ℹ️ Informações")
        info_layout = QFormLayout(info_group)

        stencil_label = QLabel(
            current_stencil.code if current_stencil else "(nenhum stencil selecionado)"
        )
        info_layout.addRow("Stencil:", stencil_label)

        if inspection_thresholds:
            thresholds_text = (
                f"OK ≥ {inspection_thresholds.ok_threshold}%, "
                f"PARTIAL ≥ {inspection_thresholds.partial_threshold}%"
            )
            info_layout.addRow("Thresholds:", QLabel(thresholds_text))

        layout.addWidget(info_group)

        # Grupo: Alinhamento
        align_group = QGroupBox("🎯 Alinhamento Gerber ↔ Imagem")
        align_layout = QVBoxLayout(align_group)

        # Checkbox para usar alinhamento existente
        self._use_alignment_checkbox = QCheckBox("Usar transformação de alinhamento (fiduciais)")

        # Verificar se existe transformação salva
        saved_tx = self.config.get("fiducial_alignment", "last_tx", default=None)
        has_alignment = saved_tx is not None

        self._use_alignment_checkbox.setChecked(has_alignment)
        self._use_alignment_checkbox.setEnabled(has_alignment)

        if has_alignment:
            tx = self.config.get("fiducial_alignment", "last_tx", default=0)
            ty = self.config.get("fiducial_alignment", "last_ty", default=0)
            angle = self.config.get("fiducial_alignment", "last_angle", default=0)
            scale = self.config.get("fiducial_alignment", "last_scale", default=1)
            self._use_alignment_checkbox.setText(
                f"Usar transformação de alinhamento "
                f"(tx={tx:.0f}, ty={ty:.0f}, rot={angle:.1f}°, escala={scale:.3f})"
            )
        else:
            self._use_alignment_checkbox.setText(
                "Usar transformação de alinhamento (nenhuma configurada)"
            )

        align_layout.addWidget(self._use_alignment_checkbox)

        # Botão para configurar alinhamento
        btn_align = QPushButton("🎯 Configurar Alinhamento de Fiduciais...")
        btn_align.clicked.connect(self._open_fiducial_alignment)
        align_layout.addWidget(btn_align)

        layout.addWidget(align_group)

        # Status
        self._status_label = QLabel("")
        layout.addWidget(self._status_label)

        # Barra de progresso
        self._progress_bar = QProgressBar()
        self._progress_bar.setVisible(False)
        layout.addWidget(self._progress_bar)

        layout.addStretch()

        # Botões
        btn_layout = QHBoxLayout()

        btn_settings = QPushButton("⚙️ Parâmetros")
        btn_settings.clicked.connect(lambda: self.show_settings_dialog(inspection_thresholds))
        btn_layout.addWidget(btn_settings)

        btn_layout.addStretch()

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self._dialog.reject)
        btn_layout.addWidget(btn_cancel)

        btn_run = QPushButton("▶️ Executar Inspeção")
        btn_run.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        btn_run.clicked.connect(self.run_inspection)
        btn_layout.addWidget(btn_run)

        layout.addLayout(btn_layout)

        self._dialog.exec()

    def _show_result_dialog(self, result: InspectionResult, overlay: np.ndarray):
        """
        Exibe diálogo com resultado da inspeção.

        Args:
            result: Resultado da inspeção
            overlay: Imagem com overlay
        """
        dialog = QDialog(self.parent_window)
        dialog.setWindowTitle(f"📊 Resultado da Inspeção - {result.overall_status}")
        dialog.resize(1200, 800)

        layout = QVBoxLayout(dialog)

        # Widget de resultado
        result_widget = InspectionResultWidget()
        result_widget.set_result(result, overlay)

        # Conectar exportação
        def export_pdf():
            try:
                import tempfile

                # Salvar overlay em arquivo temporário
                temp_dir = Path(tempfile.gettempdir())
                overlay_path = str(temp_dir / "inspection_overlay_temp.png")
                cv2.imwrite(overlay_path, overlay)

                # Preparar dados da inspeção
                result_dict = result.to_dict() if hasattr(result, 'to_dict') else {
                    'total_apertures': result.total_apertures,
                    'ok_count': result.ok_count,
                    'partial_count': result.partial_count,
                    'blocked_count': result.blocked_count,
                    'overall_status': result.overall_status,
                    'approval_rate': result.approval_rate,
                    'defects': [d.to_dict() if hasattr(d, 'to_dict') else d for d in result.defects]
                }

                # Gerar PDF (via signal para main_window)
                self.inspection_completed.emit(result_dict, overlay_path)

                QMessageBox.information(
                    dialog, "Relatório Gerado",
                    "Relatório de inspeção visual gerado com sucesso!"
                )

            except Exception as e:
                logger.exception("Erro ao gerar relatório de inspeção")
                QMessageBox.critical(
                    dialog, "Erro",
                    f"Erro ao gerar relatório:\n{str(e)}"
                )

        result_widget.exportRequested.connect(export_pdf)

        layout.addWidget(result_widget)

        # Botões
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_close = QPushButton("Fechar")
        btn_close.clicked.connect(dialog.accept)
        btn_layout.addWidget(btn_close)

        layout.addLayout(btn_layout)

        dialog.exec()

    # =========================================================================
    # MÉTODOS PRIVADOS - AÇÕES
    # =========================================================================

    def _browse_gerber(self):
        """Abre diálogo para selecionar arquivo Gerber."""
        filepath, _ = QFileDialog.getOpenFileName(
            self._dialog, "Selecionar Arquivo Gerber",
            "", "Gerber (*.gbr *.ger);;Todos (*)"
        )
        if filepath:
            self._gerber_path_input.setText(filepath)

    def _browse_mosaic(self):
        """Abre diálogo para selecionar imagem de mosaico."""
        filepath, _ = QFileDialog.getOpenFileName(
            self._dialog, "Selecionar Imagem do Mosaico",
            "", "Imagens (*.png *.jpg *.bmp *.tiff);;Todos (*)"
        )
        if filepath:
            self._mosaic_path_input.setText(filepath)

    def _open_fiducial_alignment(self):
        """Abre diálogo de alinhamento de fiduciais."""
        # Este método emite um signal para o main_window abrir o diálogo
        # O main_window é responsável por chamar show_fiducial_alignment_dialog
        self._dialog.hide()

        # Emitir signal solicitando abertura do diálogo de alinhamento
        # O main_window deve conectar a este signal
        if hasattr(self.parent_window, 'show_fiducial_alignment_dialog'):
            self.parent_window.show_fiducial_alignment_dialog()

            # Verificar se agora temos alinhamento
            saved_tx = self.config.get("fiducial_alignment", "last_tx", default=None)
            has_alignment = saved_tx is not None

            if has_alignment:
                tx = self.config.get("fiducial_alignment", "last_tx", default=0)
                ty = self.config.get("fiducial_alignment", "last_ty", default=0)
                angle = self.config.get("fiducial_alignment", "last_angle", default=0)
                scale = self.config.get("fiducial_alignment", "last_scale", default=1)
                self._use_alignment_checkbox.setText(
                    f"Usar transformação de alinhamento "
                    f"(tx={tx:.0f}, ty={ty:.0f}, rot={angle:.1f}°, escala={scale:.3f})"
                )
                self._use_alignment_checkbox.setChecked(True)
                self._use_alignment_checkbox.setEnabled(True)

        self._dialog.show()

    def _execute_inspection(self, gerber_path: str, mosaic_path: str):
        """
        Executa a inspeção com os parâmetros fornecidos.

        Args:
            gerber_path: Caminho do arquivo Gerber
            mosaic_path: Caminho da imagem de mosaico
        """
        try:
            self._status_label.setText("🔄 Carregando Gerber...")
            self._progress_bar.setVisible(True)
            self._progress_bar.setValue(10)
            QApplication.processEvents()

            # Emitir signal de inspeção solicitada
            self.inspection_requested.emit(gerber_path)

            # Carregar Gerber
            if not self.inspection_manager.load_gerber(gerber_path):
                self.inspection_failed.emit("Falha ao carregar arquivo Gerber")
                return

            self._status_label.setText("🔄 Carregando mosaico...")
            self._progress_bar.setValue(30)
            QApplication.processEvents()

            # Carregar mosaico
            mosaic = cv2.imread(mosaic_path)
            if mosaic is None:
                raise ValueError(f"Não foi possível carregar: {mosaic_path}")

            self.inspection_manager.set_mosaic(mosaic)

            # Carregar transformação de alinhamento se selecionada
            if self._use_alignment_checkbox.isChecked():
                from aoi_lib.gerber_renderer import AlignmentTransform
                tx = self.config.get("fiducial_alignment", "last_tx", default=0)
                ty = self.config.get("fiducial_alignment", "last_ty", default=0)
                angle = self.config.get("fiducial_alignment", "last_angle", default=0)
                scale = self.config.get("fiducial_alignment", "last_scale", default=1)

                transform = AlignmentTransform(
                    tx=tx, ty=ty, angle=angle,
                    scale_x=scale, scale_y=scale
                )
                self.inspection_manager.set_alignment(transform)
                self._status_label.setText("🔄 Aplicando alinhamento...")
                QApplication.processEvents()

            self._status_label.setText("🔄 Executando inspeção...")
            self._progress_bar.setValue(50)
            QApplication.processEvents()

            # Executar inspeção via manager
            result, overlay = self.inspection_manager.run_inspection()

            if result is None:
                # Erro já tratado pelo signal inspection_failed
                return

            self._progress_bar.setValue(100)

            # Salvar referências
            self._last_result = result
            self._last_overlay = overlay
            result.gerber_file = gerber_path
            result.mosaic_file = mosaic_path

            # Fechar diálogo e mostrar resultado
            self._dialog.accept()

            # Emitir signal de completion
            self.inspection_completed.emit(result, overlay)

            # Mostrar resultado
            self._show_result_dialog(result, overlay)

        except Exception as e:
            logger.exception("Erro na inspeção visual")
            self._progress_bar.setVisible(False)
            error_msg = f"Erro ao executar inspeção:\n{str(e)}"
            self.inspection_failed.emit(error_msg)
            QMessageBox.critical(self._dialog, "Erro", error_msg)
