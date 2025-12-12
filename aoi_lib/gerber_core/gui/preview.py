from __future__ import annotations

import traceback
from typing import List, Optional

from PyQt6.QtCore import Qt, QRectF, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import (
    QGraphicsPathItem,
    QGraphicsItem,
    QGraphicsScene,
    QGraphicsView,
    QMenu,
    QMessageBox,
)
from ..parser import GerberObject

class GerberGraphicsItem(QGraphicsPathItem):
    """
    Item gráfico para um polígono Gerber.
    Troca automaticamente de cor quando é selecionado / desmarcado.
    """

    def __init__(
        self,
        path: QPainterPath,
        index: int,
        normal_brush: QBrush,
        selection_brush: QBrush,
        pen: QPen,
    ):
        super().__init__(path)
        self._normal_brush = normal_brush
        self._selection_brush = selection_brush
        self.setBrush(self._normal_brush)
        self.setPen(pen)
        self.setData(0, index)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)

    def setSelectionBrush(self, brush: QBrush):
        self._selection_brush = brush
        if self.isSelected():
            self.setBrush(self._selection_brush)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self.setBrush(self._selection_brush if bool(value) else self._normal_brush)
        return super().itemChange(change, value)



class PreviewGraphicsView(QGraphicsView):
    """
    Área de preview com suporte a:
      - zoom com scroll do mouse;
      - pan (arrastar) com botão do meio (scroll) pressionado;
      - reset da visão (ajustar à área disponível).
    Renderiza os polígonos diretamente como vetores (QPainterPath) e
    permite seleção múltipla (Ctrl+clique) e por retângulo (RubberBand).
    """

    # Emite o índice do objeto/polígono para exclusão ou edição
    objectDeleteRequested = pyqtSignal(int)
    objectEditRequested = pyqtSignal(int)
    objectDeleteManyRequested = pyqtSignal(list)
    objectEditManyRequested = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self._zoom = 1.0
        # Cores atuais (vêm da janela principal)
        self._aperture_color = QColor(Qt.GlobalColor.black)
        self._selection_color = QColor(Qt.GlobalColor.red)
        self._bg_color = QColor(Qt.GlobalColor.white)
        # Guarda os polígonos em mm na mesma ordem em que foram desenhados
        self._polys_mm: List[List[tuple[float, float]]] = []
        # Opcional: lista de objetos Gerber associados a esses polígonos
        self._objects: Optional[List[GerberObject]] = None
        # Itens gráficos efetivos na cena
        self._items: List[GerberGraphicsItem] = []

        # Conjunto de índices atualmente selecionados (para possível uso futuro)
        self._selected_indices: set[int] = set()

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

        # Permite seleção por retângulo com o botão esquerdo
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)

        # Para receber eventos de teclado (Delete etc.)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Controle de pan
        self._panning = False
        self._last_mouse_pos = None

    # ------------------------------------------------------------------ Cores
    def set_selection_color(self, selection_color: QColor):
        """
        Define a cor usada para destacar os objetos selecionados.
        Atualiza imediatamente todos os itens já existentes.
        """
        self._selection_color = selection_color
        sel_brush = QBrush(self._selection_color)
        for it in self._items:
            it.setSelectionBrush(sel_brush)
            # brush normal permanece a cor da abertura

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

    def set_objects(
        self,
        objects: List[GerberObject],
        aperture_color: QColor,
        bg_color: QColor,
        *,
        preserve_view: bool = False,
    ):
        """
        Nova interface: recebe a lista de GerberObject e desenha seus
        polígonos (polygon_mm). A ordem dos objetos é usada como índice
        para mapear itens gráficos → objeto.

        Por compatibilidade, internamente chamamos set_polygons().
        """
        # Corrige o mapeamento índice do polígono -> objeto:
        # mantém apenas objetos com polígono válido, na mesma ordem.

        self._aperture_color = aperture_color
        self._bg_color = bg_color

        self._items = []
        self._objects = []
        polys_mm: List[List[tuple[float, float]]] = []

        for obj in objects or []:
            poly = obj.polygon_mm
            if not poly or len(poly) < 3:
                continue
            self._objects.append(obj)
            polys_mm.append(poly)

        # Limpa seleção ao recarregar
        self._selected_indices.clear()

        self.set_polygons(
            polys_mm,
            preserve_view=preserve_view,
        )

    def set_polygons(
        self,
        polys_mm: List[List[tuple[float, float]]],
        *,
        preserve_view: bool = False,
    ):
        """
        Recebe a lista de polígonos em coordenadas de mundo (mm) e desenha
        vetorialmente na cena (QGraphicsScene) usando QPainterPath.
        Também armazena esses polígonos para permitir inspeção por clique.
        """
        # Guarda transformação atual se for para preservar zoom/pan
        old_transform = self.transform() if preserve_view else None
        old_zoom = self._zoom if preserve_view else None
        self._scene.clear()
        self._items = []
        if not preserve_view:
            self._zoom = 1.0
            self.resetTransform()
        self._polys_mm = polys_mm or []
        # Limpa seleção atual
        self._selected_indices.clear()
        # Se estiver apenas usando polígonos, limpa os objetos associados
        if not polys_mm:
            self._objects = None

        if not polys_mm:
            return

        # cor de fundo
        self._scene.setBackgroundBrush(self._bg_color)

        # Determina bounding box em mm
        xs = [pt[0] for poly in polys_mm for pt in poly]
        ys = [pt[1] for poly in polys_mm for pt in poly]
        minx, maxx = min(xs), max(xs)
        miny, maxy = min(ys), max(ys)
        w = maxx - minx
        h = maxy - miny
        if w == 0 or h == 0:
            return

        normal_brush = QBrush(self._aperture_color)
        selection_brush = QBrush(self._selection_color)
        pen = QPen(Qt.PenStyle.NoPen)
        for idx, poly in enumerate(polys_mm):
            if len(poly) < 3:
                continue
            path = QPainterPath()
            x0, y0 = poly[0]
            path.moveTo(x0, -y0)
            for x, y in poly[1:]:
                path.lineTo(x, -y)
            try:
                item = GerberGraphicsItem(
                    path,
                    idx,
                    normal_brush,
                    selection_brush,
                    pen,
                )
                self._scene.addItem(item)
                self._items.append(item)
            except Exception:
                traceback.print_exc()

        rect = QRectF(minx, -maxy, w, h)
        self._scene.setSceneRect(rect)
        # Restaura transform se for para preservar visão
        if preserve_view and old_transform is not None and old_zoom is not None:
            self.setTransform(old_transform)
            self._zoom = old_zoom
        else:
            # Comportamento padrão: ajustar à tela
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
        Mostra em uma MessageBox informações sobre o polígono / objeto
        clicado. Se houver objetos Gerber associados, usa esses dados;
        caso contrário, usa apenas o polígono.
        """
        # Tenta primeiro usar a lista de objetos Gerber (se disponível)
        obj: Optional[GerberObject] = None
        if self._objects is not None and 0 <= poly_index < len(self._objects):
            obj = self._objects[poly_index]
            poly = obj.polygon_mm
        else:
            # Fallback: usa apenas a lista de polígonos
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

        lines = [
            f"Índice do polígono: {poly_index}",
            f"Número de pontos: {len(poly)}",
            f"Limits X: ({minx:.6f}, {maxx:.6f}) mm",
            f"Limits Y: ({miny:.6f}, {maxy:.6f}) mm",
            f"Centro aproximado: ({cx:.6f}, {cy:.6f}) mm",
        ]

        # Se tivermos um GerberObject, acrescenta informações semânticas
        if obj is not None:
            lines.append("")
            lines.append(f"Tipo: {obj.kind}")
            if obj.dcode is not None:
                lines.append(f"D-code: D{obj.dcode}")
            if obj.x_mm is not None and obj.y_mm is not None:
                lines.append(f"Posição do flash: ({obj.x_mm:.6f}, {obj.y_mm:.6f}) mm")

            if obj.kind.startswith("flash_"):
                # Alguns parâmetros típicos
                if "dia_mm" in obj.params:
                    lines.append(f"Diâmetro: {float(obj.params['dia_mm']):.6f} mm")
                if "width_mm" in obj.params and "height_mm" in obj.params:
                    lines.append(
                        "Largura x Altura: "
                        f"{float(obj.params['width_mm']):.6f} x "
                        f"{float(obj.params['height_mm']):.6f} mm"
                    )
                if "macro_name" in obj.params:
                    lines.append(f"Macro: {obj.params['macro_name']}")

        text = "\n".join(lines)
        QMessageBox.information(self, "Informações do polígono", text)

    def mousePressEvent(self, event):
        # Garante que a view receba eventos de teclado após clique
        self.setFocus()
        if event.button() == Qt.MouseButton.RightButton:
            scene_pos = self.mapToScene(event.pos())
            items = self._scene.items(scene_pos)
            if items:
                item = items[0]
                try:
                    idx = int(item.data(0))
                except Exception:
                    traceback.print_exc()
                    event.accept()
                    return
                
                # Conjunto atual de índices selecionados
                selected_items = self._scene.selectedItems()
                selected_indices: set[int] = set()
                for sit in selected_items:
                    try:
                        si = int(sit.data(0))
                        selected_indices.add(si)
                    except Exception:
                        traceback.print_exc()

                # Menu de contexto para o objeto clicado
                menu = QMenu(self)
                act_info = menu.addAction("Informações do objeto")
                act_edit = menu.addAction("Editar propriedades…")
                act_delete = menu.addAction("Excluir objeto")

                global_pos = self.mapToGlobal(event.pos())
                chosen = menu.exec(global_pos)

                if chosen is act_info:
                    try:
                        self._show_polygon_info(idx)
                    except Exception:
                        traceback.print_exc()
                elif chosen is act_edit:
                    # Edição em grupo se houver vários selecionados e o
                    # item clicado fizer parte da seleção; caso contrário,
                    # edição simples.
                    try:
                        if len(selected_indices) > 1 and idx in selected_indices:
                            self.objectEditManyRequested.emit(
                                sorted(selected_indices)
                            )
                        else:
                            self.objectEditRequested.emit(idx)
                    except Exception:
                        traceback.print_exc()
                elif chosen is act_delete:
                    # Exclusão em grupo se houver vários selecionados e o
                    # item clicado fizer parte da seleção; caso contrário,
                    # exclusão simples.
                    try:
                        if len(selected_indices) > 1 and idx in selected_indices:
                            self.objectDeleteManyRequested.emit(
                                sorted(selected_indices)
                            )
                        else:
                            self.objectDeleteRequested.emit(idx)
                    except Exception:
                        traceback.print_exc()

                event.accept()
                return
            else:
                # Clique direito em área vazia: nada a fazer por enquanto
                event.accept()
                return

        # Pan agora é com botão do meio (scroll)
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = True
            self._last_mouse_pos = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return

        # Clique esquerdo: deixa o QGraphicsView lidar com seleção
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
        if event.button() == Qt.MouseButton.MiddleButton and self._panning:
            self._panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    # ------------------------------------------------------------------ teclado (Delete)
    def keyPressEvent(self, event):
        """
        Permite excluir objetos selecionados com a tecla Delete/Backspace.
        A confirmação é tratada pela janela principal (on_delete_object).
        """
        key = event.key()
        if key in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            items = self._scene.selectedItems()
            if not items:
                event.accept()
                return

            indices: set[int] = set()
            for it in items:
                try:
                    idx = int(it.data(0))
                    indices.add(idx)
                except Exception:
                    traceback.print_exc()

            indices_sorted = sorted(indices)
            try:
                if len(indices_sorted) == 1:
                    # Mantém o comportamento de exclusão simples
                    self.objectDeleteRequested.emit(indices_sorted[0])
                else:
                    # Exclusão em grupo com uma única confirmação
                    self.objectDeleteManyRequested.emit(indices_sorted)
            except Exception:
                traceback.print_exc()

            event.accept()
            return

        # Teclas não tratadas: comportamento padrão
        super().keyPressEvent(event)
