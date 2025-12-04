from __future__ import annotations

import traceback
from typing import List

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import (
    QGraphicsScene,
    QGraphicsView,
    QMessageBox,
)


class PreviewGraphicsView(QGraphicsView):
    """
    Área de preview com suporte a:
      - zoom com scroll do mouse;
      - pan (arrastar) com botão esquerdo pressionado;
      - reset da visão (ajustar à área disponível).
    Renderiza os polígonos diretamente como vetores (QPainterPath).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self._zoom = 1.0
        # Guarda os polígonos em mm na mesma ordem em que foram desenhados
        self._polys_mm: List[List[tuple[float, float]]] = []

        self.setRenderHints(
            QPainter.RenderHint.Antialiasing
            | QPainter.RenderHint.SmoothPixmapTransform
        )
        self.setTransformationAnchor(
            QGraphicsView.ViewportAnchor.AnchorUnderMouse
        )
        self.setResizeAnchor(
            QGraphicsView.ViewportAnchor.AnchorViewCenter
        )

        # Controle de pan
        self._panning = False
        self._last_mouse_pos = None

    def reset_view(self):
        """
        Restaura o zoom/pan para enquadrar toda a imagem
        na área visível, mantendo o aspecto.
        """
        self.resetTransform()
        self._zoom = 1.0
        if not self._scene.items():
            return
        self.fitInView(
            self._scene.sceneRect(),
            Qt.AspectRatioMode.KeepAspectRatio,
        )

    def set_polygons(
        self,
        polys_mm: List[List[tuple[float, float]]],
        aperture_color: QColor,
        bg_color: QColor,
    ):
        """
        Recebe a lista de polígonos em coordenadas de mundo (mm) e desenha
        vetorialmente na cena (QGraphicsScene) usando QPainterPath.
        Também armazena esses polígonos para permitir inspeção por clique.
        """
        self._scene.clear()
        self._zoom = 1.0
        self.resetTransform()
        self._polys_mm = polys_mm or []

        if not polys_mm:
            return

        # cor de fundo
        self._scene.setBackgroundBrush(bg_color)

        # Determina bounding box em mm
        xs = [pt[0] for poly in polys_mm for pt in poly]
        ys = [pt[1] for poly in polys_mm for pt in poly]
        minx, maxx = min(xs), max(xs)
        miny, maxy = min(ys), max(ys)
        w = maxx - minx
        h = maxy - miny
        if w == 0 or h == 0:
            return

        brush = QBrush(aperture_color)
        pen = QPen(Qt.PenStyle.NoPen)
        for idx, poly in enumerate(polys_mm):
            if len(poly) < 3:
                continue
            path = QPainterPath()
            x0, y0 = poly[0]
            path.moveTo(x0, -y0)
            for x, y in poly[1:]:
                path.lineTo(x, -y)
            item = self._scene.addPath(path, pen, brush)
            try:
                item.setData(0, idx)
            except Exception:
                traceback.print_exc()
            item.setBrush(brush)

        rect = QRectF(minx, -maxy, w, h)
        self._scene.setSceneRect(rect)
        self.reset_view()

    def wheelEvent(self, event):
        """Zoom com scroll do mouse."""
        if not self._scene.items():
            return

        angle = event.angleDelta().y()
        if angle == 0:
            return

        factor = 1.25 if angle > 0 else 0.8
        old_zoom = self._zoom
        self._zoom *= factor
        self._zoom = max(0.05, min(self._zoom, 100.0))
        factor = self._zoom / old_zoom
        self.scale(factor, factor)

    def _show_polygon_info(self, poly_index: int):
        """
        Mostra em uma MessageBox informações sobre o polígono clicado.
        """
        if not (0 <= poly_index < len(self._polys_mm)):
            return
        poly = self._polys_mm[poly_index]
        if not poly:
            return

        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        minx, maxx = min(xs), max(xs)
        miny, maxy = min(ys), max(ys)
        cx = (minx + maxx) / 2.0
        cy = (miny + maxy) / 2.0

        text = (
            f"Índice do polígono: {poly_index}\n"
            f"Número de pontos: {len(poly)}\n"
            f"Limits X: ({minx:.6f}, {maxx:.6f}) mm\n"
            f"Limits Y: ({miny:.6f}, {maxy:.6f}) mm\n"
            f"Centro aproximado: ({cx:.6f}, {cy:.6f}) mm\n"
        )
        QMessageBox.information(self, "Informações do polígono", text)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            scene_pos = self.mapToScene(event.pos())
            items = self._scene.items(scene_pos)
            if items:
                item = items[0]
                try:
                    idx = int(item.data(0))
                    self._show_polygon_info(idx)
                except Exception:
                    traceback.print_exc()
            event.accept()
            return

        if event.button() == Qt.MouseButton.LeftButton:
            self._panning = True
            self._last_mouse_pos = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._panning and self._last_mouse_pos is not None:
            delta = event.pos() - self._last_mouse_pos
            self._last_mouse_pos = event.pos()
            hbar = self.horizontalScrollBar()
            vbar = self.verticalScrollBar()
            hbar.setValue(hbar.value() - delta.x())
            vbar.setValue(vbar.value() - delta.y())
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._panning:
            self._panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)
