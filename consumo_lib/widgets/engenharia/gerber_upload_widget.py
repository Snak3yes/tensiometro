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
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QPixmap, QImage
import numpy as np

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


class GerberPreviewWidget(QWidget):
    """
    Widget de preview do Gerber com zoom/pan.

    Features:
        - Renderização vetorial simplificada
        - Zoom com scroll do mouse
        - Pan com clique do meio ou arrasto
        - Seleção de aperturas por clique
    """

    aperture_selected = pyqtSignal(dict)  # Emitido ao clicar em uma aperture

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 500)

        # Estado
        self._apertures = []
        self._fiducials = []
        self._removed_apertures = []

        # Visualização
        self._zoom = 1.0
        self._offset = QPoint(0, 0)
        self._panning = False
        self._last_pan_pos = QPoint()

        # Estilo
        self.setStyleSheet("""
            GerberPreviewWidget {
                background-color: #1e1e1e;
                border: 2px solid #444;
                border-radius: 4px;
            }
        """)

    def set_apertures(self, apertures: List[Dict]):
        """Define lista de aperturas para renderizar."""
        self._apertures = apertures
        self._removed_apertures = []
        self.update()

    def set_fiducials(self, fiducials: List[Dict]):
        """Define lista de fiduciais."""
        self._fiducials = fiducials
        self.update()

    def remove_aperture(self, aperture: Dict):
        """Remove uma aperture da renderização."""
        if aperture in self._apertures and aperture not in self._removed_apertures:
            self._removed_apertures.append(aperture)
            self.update()

    def undo_remove(self):
        """Desfaz última remoção."""
        if self._removed_apertures:
            self._removed_apertures.pop()
            self.update()

    def fit_to_view(self):
        """Ajusta zoom para mostrar todo o conteúdo."""
        if not self._apertures:
            return

        # Calcular bounding box
        min_x = min(a['x'] - a.get('width', 1)/2 for a in self._apertures)
        max_x = max(a['x'] + a.get('width', 1)/2 for a in self._apertures)
        min_y = min(a['y'] - a.get('height', 1)/2 for a in self._apertures)
        max_y = max(a['y'] + a.get('height', 1)/2 for a in self._apertures)

        width = max_x - min_x
        height = max_y - min_y

        # Calcular zoom
        margin = 20
        zoom_x = (self.width() - 2*margin) / width if width > 0 else 1.0
        zoom_y = (self.height() - 2*margin) / height if height > 0 else 1.0
        self._zoom = min(zoom_x, zoom_y) * 0.9  # 90% para dar margem

        # Centralizar
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        self._offset = QPoint(
            int(self.width()/2 - center_x * self._zoom),
            int(self.height()/2 - center_y * self._zoom)
        )

        self.update()

    def paintEvent(self, event):
        """Renderiza aperturas e fiduciais."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background
        painter.fillRect(self.rect(), QColor("#1e1e1e"))

        # Aplicar transformações
        painter.translate(self._offset)
        painter.scale(self._zoom, self._zoom)

        # Renderizar aperturas (não removidas)
        for aperture in self._apertures:
            if aperture in self._removed_apertures:
                continue

            # Cores baseadas em tipo
            if aperture.get('type') == 'circle':
                color = QColor("#4CAF50")  # Verde
                self._draw_circle(painter, aperture, color)
            elif aperture.get('type') == 'rect':
                color = QColor("#2196F3")  # Azul
                self._draw_rect(painter, aperture, color)
            elif aperture.get('type') == 'obround':
                color = QColor("#FF9800")  # Laranja
                self._draw_obround(painter, aperture, color)
            else:
                color = QColor("#9C27B0")  # Roxo (outros)
                self._draw_circle(painter, aperture, color)

        # Renderizar fiduciais (destacados)
        for fid in self._fiducials:
            color = QColor("#F44336")  # Vermelho
            self._draw_circle(painter, fid, color, highlight=True)

        painter.end()

    def _draw_circle(self, painter, aperture, color, highlight=False):
        """Desenha aperture circular."""
        x = aperture['x']
        y = aperture['y']
        r = aperture.get('d', 1) / 2

        if highlight:
            # Círculo destacado com borda grossa
            painter.setPen(QPen(color, 0.1))
            painter.setBrush(QBrush(color.lighter(150)))
        else:
            painter.setPen(QPen(color, 0.01))
            painter.setBrush(QBrush(color.lighter(180)))

        painter.drawEllipse(QRectF(x - r, y - r, r*2, r*2))

    def _draw_rect(self, painter, aperture, color):
        """Desenha aperture retangular."""
        x = aperture['x']
        y = aperture['y']
        w = aperture.get('width', 1)
        h = aperture.get('height', 1)

        painter.setPen(QPen(color, 0.01))
        painter.setBrush(QBrush(color.lighter(180)))
        painter.drawRect(QRectF(x - w/2, y - h/2, w, h))

    def _draw_obround(self, painter, aperture, color):
        """Desenha aperture obround (racetrack)."""
        # Simplificação: desenhar como retângulo por enquanto
        self._draw_rect(painter, aperture, color)

    def wheelEvent(self, event):
        """Zoom com scroll do mouse."""
        angle = event.angleDelta().y()
        if angle > 0:
            self._zoom *= 1.1
        else:
            self._zoom /= 1.1

        self._zoom = max(0.1, min(self._zoom, 10.0))
        self.update()

    def mousePressEvent(self, event):
        """Inicia pan ou detecta clique."""
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = True
            self._last_pan_pos = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        elif event.button() == Qt.MouseButton.LeftButton:
            # Detectar clique em aperture
            self._detect_aperture_click(event.pos())

    def mouseMoveEvent(self, event):
        """Pan com arrasto."""
        if self._panning:
            delta = event.pos() - self._last_pan_pos
            self._offset += delta
            self._last_pan_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        """Finaliza pan."""
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def _detect_aperture_click(self, pos: QPoint):
        """Detecta se clique foi em uma aperture."""
        # Converter posição de tela para coordenadas mundo
        world_x = (pos.x() - self._offset.x()) / self._zoom
        world_y = (pos.y() - self._offset.y()) / self._zoom

        # Buscar aperture próxima (tolerância de 5 pixels)
        tolerance = 5.0 / self._zoom
        for aperture in self._apertures:
            if aperture in self._removed_apertures:
                continue

            ax = aperture['x']
            ay = aperture['y']
            dist = ((world_x - ax)**2 + (world_y - ay)**2)**0.5

            if dist <= tolerance:
                self.aperture_selected.emit(aperture)
                break


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
        logger.info("🎨 Inicializando GerberUploadWidget")

        # Estado
        self._gerber_metadata: Optional[GerberMetadata] = None
        self._apertures = []
        self._fiducials = []
        self._is_valid = False

        # Setup UI
        self._setup_ui()

        # Conectar signals
        self._connect_signals()

        logger.info("✅ GerberUploadWidget inicializado")

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
        """Carrega e processa arquivo Gerber."""
        try:
            logger.info(f"📥 Carregando Gerber: {file_path}")

            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

            # TODO: Parse real do Gerber usando aoi_lib.gerber_parser
            # Por enquanto, criar dados mock para desenvolvimento
            self._create_mock_gerber_data(file_path)

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
                f"{self._gerber_metadata.aperture_count} aperturas, "
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

            logger.info("✅ Gerber carregado com sucesso")

        except Exception as e:
            logger.error(f"❌ Erro ao carregar Gerber: {e}")
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
            self._apertures.append({
                'id': i,
                'type': 'circle' if i % 3 == 0 else 'rect',
                'x': i * 2.0,
                'y': (i % 5) * 2.0,
                'd': 0.5 if i % 3 == 0 else None,
                'width': 0.5 if i % 3 != 0 else None,
                'height': 0.5 if i % 3 != 0 else None
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
        """Handler quando aperture é selecionada."""
        self.btn_remove.setEnabled(True)

    def _on_remove_clicked(self):
        """Handler do botão remover."""
        # TODO: Implementar remoção da última aperture selecionada
        self.preview_widget.undo_remove()  # Simplificado por enquanto

    def _on_undo_clicked(self):
        """Handler do botão desfazer."""
        self.preview_widget.undo_remove()

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
