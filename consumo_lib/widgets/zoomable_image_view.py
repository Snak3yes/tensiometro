"""
Zoomable Image View Widget

Widget reutilizável para visualização de imagem com zoom.
Suporta zoom in/out, reset de zoom e carregamento de imagens.
"""

import logging
from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

# Design System
from consumo_lib.ui import COLORS, DIM

logger = logging.getLogger(__name__)


class ZoomableImageView(QLabel):
    """
    Widget de visualização de imagem com zoom.

    Permite zoom in/out e reset para visualização detalhada de imagens.

    Features:
        - Carregamento de imagens from file path
        - Zoom in/out com limites configuráveis
        - Reset de zoom para 100%
        - Display centralizado com stylesheet

    Example:
        >>> widget = ZoomableImageView()
        >>> widget.set_image("/path/to/image.png")
        >>> widget.zoom_in()
        >>> widget.zoom_out()
        >>> widget.reset_zoom()
    """

    def __init__(
        self,
        min_zoom: float = 0.5,
        max_zoom: float = 3.0,
        zoom_step: float = 0.25,
        parent=None
    ):
        """
        Inicializa widget de imagem com zoom.

        Args:
            min_zoom: Fator mínimo de zoom (default: 0.5 = 50%)
            max_zoom: Fator máximo de zoom (default: 3.0 = 300%)
            zoom_step: Incremento de zoom por step (default: 0.25 = 25%)
            parent: Widget pai
        """
        super().__init__(parent)

        self.pixmap = None
        self.zoom_factor = 1.0
        self.min_zoom = min_zoom
        self.max_zoom = max_zoom
        self.zoom_step = zoom_step

        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS.SURFACE};
                border: 2px solid {COLORS.BORDER};
                border-radius: {DIM.RADIUS_MD}px;
                min-height: 300px;
            }}
        """)
        self.setText("Nenhuma imagem selecionada")

        logger.debug(
            f"ZoomableImageView criado: min_zoom={min_zoom}, "
            f"max_zoom={max_zoom}, zoom_step={zoom_step}"
        )

    def set_image(self, image_path: str) -> bool:
        """
        Define imagem a ser exibida.

        Args:
            image_path: Caminho do arquivo de imagem

        Returns:
            True se imagem carregada com sucesso, False caso contrário
        """
        try:
            self.pixmap = QPixmap(image_path)

            if not self.pixmap.isNull():
                self._update_display()
                logger.debug(f"Imagem carregada: {image_path}")
                return True
            else:
                self.setText("Erro ao carregar imagem")
                logger.warning(f"Imagem não pode ser carregada: {image_path}")
                return False

        except Exception as e:
            self.setText("Erro ao carregar imagem")
            logger.error(f"Erro ao carregar imagem {image_path}: {e}")
            return False

    def set_pixmap_direct(self, pixmap: QPixmap):
        """
        Define QPixmap diretamente (sem carregar de arquivo).

        Útil para imagens em memória ou processadas.

        Args:
            pixmap: QPixmap para exibir
        """
        self.pixmap = pixmap
        if not self.pixmap.isNull():
            self._update_display()
            logger.debug("Pixmap definido diretamente")

    def zoom_in(self):
        """Aumenta zoom em um step."""
        if self.zoom_factor < self.max_zoom:
            self.zoom_factor = min(
                self.zoom_factor + self.zoom_step,
                self.max_zoom
            )
            self._update_display()
            logger.debug(f"Zoom in: {self.zoom_factor:.2f}")

    def zoom_out(self):
        """Diminui zoom em um step."""
        if self.zoom_factor > self.min_zoom:
            self.zoom_factor = max(
                self.zoom_factor - self.zoom_step,
                self.min_zoom
            )
            self._update_display()
            logger.debug(f"Zoom out: {self.zoom_factor:.2f}")

    def reset_zoom(self):
        """Reseta zoom para 100% (fator 1.0)."""
        self.zoom_factor = 1.0
        self._update_display()
        logger.debug("Zoom resetado para 1.0")

    def set_zoom(self, factor: float):
        """
        Define fator de zoom diretamente.

        Args:
            factor: Fator de zoom (entre min_zoom e max_zoom)
        """
        self.zoom_factor = max(self.min_zoom, min(self.max_zoom, factor))
        self._update_display()
        logger.debug(f"Zoom definido para: {self.zoom_factor:.2f}")

    def get_zoom(self) -> float:
        """
        Retorna fator de zoom atual.

        Returns:
            Fator de zoom atual (1.0 = 100%)
        """
        return self.zoom_factor

    def clear_image(self):
        """Limpa imagem atual e reseta zoom."""
        self.pixmap = None
        self.zoom_factor = 1.0
        self.setText("Nenhuma imagem selecionada")
        logger.debug("Imagem limpa")

    def _update_display(self):
        """
        Atualiza display com zoom atual.

        Método interno chamado após mudança de zoom ou carregamento de imagem.
        """
        if self.pixmap and not self.pixmap.isNull():
            # Aplica zoom
            scaled_pixmap = self.pixmap.scaled(
                int(self.pixmap.width() * self.zoom_factor),
                int(self.pixmap.height() * self.zoom_factor),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.setPixmap(scaled_pixmap)
