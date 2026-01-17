"""
GerberUploadWidget - Widget de Carregamento de Gerber (Aba 2 do Engineering Wizard)

Este widget permite carregar um arquivo Gerber RS-274X, visualizar o preview,
limpar aperturas indesejadas e extrair informações.

Funcionalidades:
- Upload de arquivo .gbr/.ger/.txt
- Preview vetorial com zoom/pan
- Limpeza interativa de aperturas
- Detecção automática de fiduciais
- Extração de métricas (dimensões, contagem)

Autor: Claude Code (Sonnet 4.5)
Data: 2026-01-13
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QGroupBox, QFileDialog,
    QListWidget, QListWidgetItem, QMessageBox, QSplitter
)
from PyQt6.QtCore import pyqtSignal, Qt, QPoint, QRectF
from PyQt6.QtGui import QColor

# Importar NOVO widget baseado em QGraphicsView
from .gerber_preview_widget_new import GerberPreviewWidget

logger = logging.getLogger(__name__)


@dataclass
class GerberMetadata:
    """Metadados extraídos do arquivo Gerber."""
    file_path: str
    file_name: str
    file_size: int
    dimensions: Tuple[float, float]  # (width_mm, height_mm)
    aperture_count: int
    fiducial_count: int
    fiducial_positions: List[Dict]  # [{'x': float, 'y': float, 'd': float}, ...]
    unit: str = 'mm'

    def to_dict(self) -> Dict:
        """Converte para dicionário."""
        return {
            'file_path': self.file_path,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'dimensions': {
                'width_mm': self.dimensions[0],
                'height_mm': self.dimensions[1]
            },
            'aperture_count': self.aperture_count,
            'fiducial_count': self.fiducial_count,
            'fiducial_positions': self.fiducial_positions,
            'unit': self.unit
        }


class GerberUploadWidget(QWidget):
    """
    Widget para carregar e processar arquivo Gerber.

    Signals:
        gerber_loaded(dict): Emitido quando Gerber é carregado com sucesso
        validation_changed(bool): Emitido quando validação muda
    """

    gerber_loaded = pyqtSignal(dict)
    validation_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info("Inicializando GerberUploadWidget")

        # Estado
        self._gerber_metadata: Optional[GerberMetadata] = None
        self._apertures = []
        self._fiducials = []
        self._is_valid = False
        self._selected_aperture_index: Optional[int] = None  # Armazena índice da última seleção

        # Setup UI
        self._setup_ui()

        # Conectar signals
        self._connect_signals()

        logger.info("GerberUploadWidget inicializado")

    def _setup_ui(self):
        """Configura interface do usuário."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Título
        title = QLabel("📁 Carregar Arquivo Gerber")
        title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2196F3;
                padding: 10px;
            }
        """)
        layout.addWidget(title)

        # Botão de upload
        upload_layout = QHBoxLayout()
        self.btn_upload = QPushButton("📤 Carregar Gerber")
        self.btn_upload.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45A049;
            }
            QPushButton:pressed {
                background-color: #3D8B40;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
                color: #757575;
            }
        """)
        upload_layout.addWidget(self.btn_upload)
        upload_layout.addStretch()
        layout.addLayout(upload_layout)

        # Splitter (preview | info)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Lado esquerdo: Preview
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout(preview_group)

        self.preview_widget = GerberPreviewWidget()
        preview_layout.addWidget(self.preview_widget)

        # Controles de preview
        preview_controls = QHBoxLayout()
        btn_fit = QPushButton("🔍 Ajustar")
        btn_fit.clicked.connect(self.preview_widget.fit_to_view)
        preview_controls.addWidget(btn_fit)
        preview_controls.addStretch()
        preview_layout.addLayout(preview_controls)

        splitter.addWidget(preview_group)

        # Lado direito: Informações
        info_group = QGroupBox("Informações")
        info_layout = QVBoxLayout(info_group)

        # Labels de informações
        self.lbl_filename = QLabel("📄 Arquivo: Nenhum")
        self.lbl_size = QLabel("💾 Tamanho: -")
        self.lbl_dimensions = QLabel("📐 Dimensões: -")
        self.lbl_apertures = QLabel("🔳 Aperturas: 0")
        self.lbl_fiducials = QLabel("🎯 Fiduciais: 0")

        for lbl in [self.lbl_filename, self.lbl_size, self.lbl_dimensions,
                    self.lbl_apertures, self.lbl_fiducials]:
            lbl.setStyleSheet("padding: 5px;")
            info_layout.addWidget(lbl)

        # Lista de fiduciais detectados
        info_layout.addWidget(QLabel("Fiduciais Detectados:"))
        self.list_fiducials = QListWidget()
        self.list_fiducials.setMaximumHeight(150)
        info_layout.addWidget(self.list_fiducials)

        # Controles de limpeza
        cleanup_group = QGroupBox("Limpeza")
        cleanup_layout = QGridLayout(cleanup_group)

        self.btn_remove = QPushButton("🗑️ Remover Selecionado")
        self.btn_remove.setEnabled(False)
        self.btn_undo = QPushButton("↩️ Desfazer")
        self.btn_undo.setEnabled(False)

        cleanup_layout.addWidget(self.btn_remove, 0, 0)
        cleanup_layout.addWidget(self.btn_undo, 0, 1)

        info_layout.addWidget(cleanup_group)
        info_layout.addStretch()

        splitter.addWidget(info_group)

        # Proporção do splitter (60% preview, 40% info)
        splitter.setSizes([600, 400])

        layout.addWidget(splitter, 1)

        # Status label
        self.status_label = QLabel("⚠️ Carregue um arquivo Gerber (.gbr)")
        self.status_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #FFF3CD;
                border: 1px solid #FFC107;
                border-radius: 4px;
                color: #856404;
            }
        """)
        layout.addWidget(self.status_label)

    def _connect_signals(self):
        """Conecta signals."""
        self.btn_upload.clicked.connect(self._on_upload_clicked)
        self.preview_widget.aperture_selected.connect(self._on_aperture_selected)
        self.preview_widget.objectDeleteRequested.connect(self._on_object_delete_requested)
        self.preview_widget.objectDeleteManyRequested.connect(self._on_objects_delete_many_requested)
        self.preview_widget.undo_available.connect(self._on_undo_available)
        self.preview_widget.redo_available.connect(self._on_redo_available)
        self.btn_remove.clicked.connect(self._on_remove_clicked)
        self.btn_undo.clicked.connect(self._on_undo_clicked)

    def _on_upload_clicked(self):
        """Handler do botão de upload."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Arquivo Gerber",
            "",
            "Gerber Files (*.gbr *.ger *.txt);;All Files (*)"
        )

        if file_path:
            self._load_gerber(file_path)

    def _load_gerber(self, file_path: str):
        """Carrega e processa arquivo Gerber usando o novo widget baseado no POC."""
        try:
            print("[INFO] Carregando Gerber...")
            logger.info(f"Carregando Gerber: {file_path}")

            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

            # Usar parser de Gerber
            from aoi_lib.gerber_parser import GerberParser

            parser = GerberParser()
            result = parser.parse_file(file_path)

            if result.error:
                raise ValueError(f"Erro no parsing: {result.error}")

            print(f"[INFO] Parser retornou {len(result.objects)} objetos")

            # USAR NOVO MÉTODO set_objects() direto do parser!
            # Isso usa QGraphicsView e renderiza regions corretamente
            self.preview_widget.set_objects(result.objects)

            # Criar metadados simplificados
            self._gerber_metadata = GerberMetadata(
                file_path=file_path,
                file_name=path.name,
                file_size=0,  # TODO: Obter tamanho real
                dimensions=(result.stats.bounds.width if result.stats.bounds else 0.0,
                          result.stats.bounds.height if result.stats.bounds else 0.0),
                aperture_count=len(result.objects),
                fiducial_count=len(result.fiducial_candidates),
                fiducial_positions=[
                    {'x': f.x_mm, 'y': f.y_mm, 'd': f.diameter_mm if f.diameter_mm else 1.5}
                    for f in result.fiducial_candidates
                ],
                unit='mm'
            )

            # Atualizar UI
            self._update_info_display()

            # Atualizar validação
            self._is_valid = True
            self.validation_changed.emit(True)

            # Emitir signal
            data = self.get_gerber_data()
            self.gerber_loaded.emit(data)

            # Atualizar status
            self.status_label.setText(
                f"✅ Gerber carregado: {path.name} - "
                f"{self._gerber_metadata.aperture_count} objetos, "
                f"{self._gerber_metadata.fiducial_count} fiduciais"
            )
            self.status_label.setStyleSheet("""
                QLabel {
                    padding: 10px;
                    background-color: #D4EDDA;
                    border: 1px solid #28A745;
                    border-radius: 4px;
                    color: #155724;
                }
            """)

            logger.info("Gerber carregado com sucesso")

        except Exception as e:
            logger.error(f"Erro ao carregar Gerber: {e}")
            QMessageBox.critical(
                self,
                "Erro ao Carregar Gerber",
                f"Não foi possível carregar o arquivo Gerber:\n{e}"
            )
            self.status_label.setText(f"❌ Erro: {e}")


    def _create_mock_gerber_data(self, file_path: str):
        """Cria dados mock de Gerber para desenvolvimento."""
        path = Path(file_path)

        # Criar aperturas mock
        self._apertures = []
        for i in range(50):
            if i % 3 == 0:
                # Círculo: tem 'd' (diâmetro), não tem width/height
                self._apertures.append({
                    'id': i,
                    'type': 'circle',
                    'x': i * 2.0,
                    'y': (i % 5) * 2.0,
                    'd': 0.5
                })
            else:
                # Retângulo: tem width/height, não tem 'd'
                self._apertures.append({
                    'id': i,
                    'type': 'rect',
                    'x': i * 2.0,
                    'y': (i % 5) * 2.0,
                    'width': 0.5,
                    'height': 0.5
                })

        # Detectar fiduciais mock
        self._fiducials = [
            {'x': 0.0, 'y': 0.0, 'd': 1.5},
            {'x': 100.0, 'y': 0.0, 'd': 1.5},
            {'x': 0.0, 'y': 50.0, 'd': 1.5},
            {'x': 100.0, 'y': 50.0, 'd': 1.5}
        ]

        # Criar metadados
        self._gerber_metadata = GerberMetadata(
            file_path=file_path,
            file_name=path.name,
            file_size=path.stat().st_size,
            dimensions=(100.0, 50.0),
            aperture_count=len(self._apertures),
            fiducial_count=len(self._fiducials),
            fiducial_positions=self._fiducials
        )

        # Atualizar preview
        self.preview_widget.set_apertures(self._apertures)
        self.preview_widget.set_fiducials(self._fiducials)
        self.preview_widget.fit_to_view()

    def _update_info_display(self):
        """Atualiza display de informações."""
        if not self._gerber_metadata:
            return

        self.lbl_filename.setText(f"📄 Arquivo: {self._gerber_metadata.file_name}")
        self.lbl_size.setText(f"💾 Tamanho: {self._gerber_metadata.file_size} bytes")
        w, h = self._gerber_metadata.dimensions
        self.lbl_dimensions.setText(f"📐 Dimensões: {w:.1f} x {h:.1f} mm")
        self.lbl_apertures.setText(f"🔳 Aperturas: {self._gerber_metadata.aperture_count}")
        self.lbl_fiducials.setText(f"🎯 Fiduciais: {self._gerber_metadata.fiducial_count}")

        # Atualizar lista de fiduciais
        self.list_fiducials.clear()
        for i, fid in enumerate(self._fiducials):
            item = QListWidgetItem(
                f"Fiducial {i+1}: X={fid['x']:.1f}, Y={fid['y']:.1f}"
            )
            self.list_fiducials.addItem(item)

    def _on_aperture_selected(self, aperture: Dict):
        """
        Handler quando aperture é selecionada.

        Args:
            aperture: Dict com dados da aperture selecionada
        """
        # Armazenar índice da última seleção
        self._selected_aperture_index = aperture.get('id')
        # Habilitar botão remover quando há seleção
        self.btn_remove.setEnabled(True)
        logger.debug(f"Botão remover habilitado (aperture {self._selected_aperture_index} selecionada)")

    def _on_undo_available(self, available: bool):
        """
        Handler quando disponibilidade de undo muda.

        Args:
            available: True se undo está disponível
        """
        self.btn_undo.setEnabled(available)
        logger.debug(f"Undo disponível: {available}")

    def _on_redo_available(self, available: bool):
        """
        Handler quando disponibilidade de redo muda.

        Args:
            available: True se redo está disponível
        """
        # TODO: Poderíamos adicionar botão de redo se necessário
        logger.debug(f"Redo disponível: {available}")

    def _on_remove_clicked(self):
        """Handler do botão remover - remove todos os itens selecionados."""
        try:
            # Obter todos os itens selecionados da cena
            selected_items = self.preview_widget._scene.selectedItems()

            if not selected_items:
                logger.warning("Nenhuma aperture selecionada para remoção")
                return

            # Coletar índices de todos os itens selecionados
            indices: set[int] = set()
            for item in selected_items:
                try:
                    idx = int(item.data(0))
                    indices.add(idx)
                except Exception:
                    logger.exception("Erro ao obter índice do item selecionado")

            if not indices:
                logger.warning("Nenhum índice válido encontrado nos itens selecionados")
                return

            indices_sorted = sorted(indices)

            # Confirmar exclusão (mensagem diferente para singular/plural)
            if len(indices_sorted) == 1:
                message = f"Deseja realmente excluir a abertura selecionada (índice {indices_sorted[0]})?"
            else:
                message = f"Deseja realmente excluir {len(indices_sorted)} aberturas selecionadas?"

            reply = QMessageBox.question(
                self,
                "Confirmar Exclusão",
                message,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                # Remover usando o handler apropriado
                if len(indices_sorted) == 1:
                    self._on_object_delete_requested(indices_sorted[0])
                else:
                    self._on_objects_delete_many_requested(indices_sorted)

                # Limpar seleção
                self._selected_aperture_index = None
                self.btn_remove.setEnabled(False)

        except Exception as e:
            logger.error(f"Erro ao excluir aberturas selecionadas: {e}")
            QMessageBox.critical(
                self,
                "Erro na Exclusão",
                f"Erro ao excluir aberturas:\n{e}"
            )

    def _on_undo_clicked(self):
        """Handler do botão desfazer."""
        self.preview_widget.undo_remove()

    def _on_object_delete_requested(self, index: int):
        """
        Handler quando usuário solicita exclusão de um objeto (Delete/Backspace).

        Args:
            index: Índice do objeto a ser excluído
        """
        try:
            # Confirmar exclusão
            reply = QMessageBox.question(
                self,
                "Confirmar Exclusão",
                f"Deseja realmente excluir o objeto no índice {index}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                # Remover objeto da cena
                success = self.preview_widget.remove_object_at_index(index)

                if success:
                    logger.info(f"Objeto {index} excluído com sucesso")
                    # TODO: Atualizar metadados e contadores
                else:
                    QMessageBox.warning(
                        self,
                        "Erro na Exclusão",
                        f"Não foi possível excluir o objeto {index}"
                    )

        except Exception as e:
            logger.error(f"Erro ao excluir objeto {index}: {e}")
            QMessageBox.critical(
                self,
                "Erro na Exclusão",
                f"Erro ao excluir objeto:\n{e}"
            )

    def _on_objects_delete_many_requested(self, indices: list[int]):
        """
        Handler quando usuário solicita exclusão de múltiplos objetos.

        Args:
            indices: Lista de índices dos objetos a serem excluídos
        """
        try:
            # Confirmar exclusão
            reply = QMessageBox.question(
                self,
                "Confirmar Exclusão em Lote",
                f"Deseja realmente excluir {len(indices)} objeto(s)?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                # Remover objetos da cena
                removed_count = self.preview_widget.remove_objects_at_indices(indices)

                if removed_count > 0:
                    logger.info(f"{removed_count} objetos excluídos com sucesso")
                    QMessageBox.information(
                        self,
                        "Exclusão Concluída",
                        f"{removed_count} de {len(indices)} objetos excluídos com sucesso"
                    )
                    # TODO: Atualizar metadados e contadores
                else:
                    QMessageBox.warning(
                        self,
                        "Erro na Exclusão",
                        "Nenhum objeto foi excluído"
                    )

        except Exception as e:
            logger.error(f"Erro ao excluir objetos: {e}")
            QMessageBox.critical(
                self,
                "Erro na Exclusão",
                f"Erro ao excluir objetos:\n{e}"
            )

    def get_gerber_data(self) -> Dict:
        """
        Retorna dados do Gerber como dicionário.

        Returns:
            Dict com metadados e dados do arquivo Gerber
        """
        if not self._gerber_metadata:
            return {}

        return self._gerber_metadata.to_dict()

    def is_valid(self) -> bool:
        """Verifica se Gerber foi carregado e é válido."""
        return self._is_valid
