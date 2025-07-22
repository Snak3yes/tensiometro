# roi_window_editor.py
#
#  Uso mínimo ----------------------------------------------------
#  view = QGraphicsView(parent)
#  editor = ROIWindowEditor(view)
#
#  editor.start_drawing()    # clique-e-arrasta cria novas janelas
#  editor.stop_drawing()
#
#  j = editor.add_window(10, 10, 150, 90)   # criar por código
#  j.change_callback = lambda item: print(item.rect())   # escuta
#
#  Todas as janelas podem ser apagadas com a tecla DEL
#  (o atalho é registrado automaticamente).
#
#  ---------------------------------------------------------------

from __future__ import annotations

from typing import Callable, Dict, Optional, List
from PyQt6.QtCore import Qt, QRectF, QPointF, QObject, QEvent, pyqtSignal
from PyQt6.QtGui import QPen, QBrush, QColor, QCursor
from PyQt6.QtWidgets import (
    QGraphicsRectItem,
    QGraphicsItem,
    QGraphicsView,
    QGraphicsScene,
    QInputDialog
)

HANDLE = 6  # px


# ======================================================================
#  Item individual (janela)
# ======================================================================
class ResizableRectItem(QGraphicsRectItem):
    """
    Retângulo completo:
      • movível
      • redimensionável (8 alças)
      • selecionável
      • opcionalmente deletável com DEL (atributo .deletable)
      • dispara change_callback(self) em toda mudança geométrica
    """
    pen_normal   = QPen(Qt.GlobalColor.green, 2)
    pen_selected = QPen(Qt.GlobalColor.blue, 2, Qt.PenStyle.DashLine)
    handle_brush = QBrush(Qt.GlobalColor.white)
    handle_pen   = QPen(Qt.GlobalColor.black, 1)

    def __init__(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        pen: Optional[QPen] = None,
        change_callback: Optional[Callable[['ResizableRectItem'], None]] = None,
        deletable: bool = True,
        parent: Optional[QGraphicsItem] = None
    ):
        super().__init__(x, y, w, h, parent)
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)
        self._active_handle: Optional[str] = None
        self._pen_custom = pen
        self.change_callback = change_callback
        self.deletable = deletable
        if callable(self.change_callback):
            self.change_callback(self)

    # -------------------------- helpers --------------------------
    def _all_handles(self) -> Dict[str, QRectF]:
        r = self.rect()
        x, y, w, h = r.x(), r.y(), r.width(), r.height()
        s = HANDLE
        cx, cy = x + w / 2.0, y + h / 2.0
        return {
            'tl': QRectF(x - s / 2, y - s / 2, s, s),
            'tm': QRectF(cx - s / 2, y - s / 2, s, s),
            'tr': QRectF(x + w - s / 2, y - s / 2, s, s),
            'mr': QRectF(x + w - s / 2, cy - s / 2, s, s),
            'br': QRectF(x + w - s / 2, y + h - s / 2, s, s),
            'bm': QRectF(cx - s / 2, y + h - s / 2, s, s),
            'bl': QRectF(x - s / 2, y + h - s / 2, s, s),
            'ml': QRectF(x - s / 2, cy - s / 2, s, s),
        }

    @staticmethod
    def _cursor_for(handle: Optional[str]) -> Qt.CursorShape:
        return {
            'tl': Qt.CursorShape.SizeFDiagCursor,
            'br': Qt.CursorShape.SizeFDiagCursor,
            'tr': Qt.CursorShape.SizeBDiagCursor,
            'bl': Qt.CursorShape.SizeBDiagCursor,
            'ml': Qt.CursorShape.SizeHorCursor,
            'mr': Qt.CursorShape.SizeHorCursor,
            'tm': Qt.CursorShape.SizeVerCursor,
            'bm': Qt.CursorShape.SizeVerCursor,
        }.get(handle, Qt.CursorShape.ArrowCursor)

    def _handle_at(self, pos: QPointF) -> Optional[str]:
        for name, rect in self._all_handles().items():
            if rect.contains(pos):
                return name
        return None

    # --------------------- eventos de ponteiro --------------------
    def hoverMoveEvent(self, ev):
        self.setCursor(self._cursor_for(self._handle_at(ev.pos())))
        super().hoverMoveEvent(ev)

    def mousePressEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self._active_handle = self._handle_at(ev.pos())
        super().mousePressEvent(ev)

    def mouseMoveEvent(self, ev):
        if self._active_handle:
            self._resize(ev.pos())
            if callable(self.change_callback):
                self.change_callback(self)
        else:
            super().mouseMoveEvent(ev)

    def mouseReleaseEvent(self, ev):
        self._active_handle = None
        if callable(self.change_callback):
            self.change_callback(self)
        super().mouseReleaseEvent(ev)

    # ------------------------- mudança ----------------------------
    def itemChange(self, change, value):
        if (change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged
                and callable(self.change_callback)):
            self.change_callback(self)
        return super().itemChange(change, value)

    # ------------------------- resize -----------------------------
    def _resize(self, pos: QPointF):
        r = self.rect()
        x, y, w, h = r.x(), r.y(), r.width(), r.height()
        px, py = pos.x(), pos.y()

        if 'l' in self._active_handle:
            new_x = min(px, x + w - 1)
            w += x - new_x
            x = new_x
        if 'r' in self._active_handle:
            w = max(1, px - x)
        if 't' in self._active_handle:
            new_y = min(py, y + h - 1)
            h += y - new_y
            y = new_y
        if 'b' in self._active_handle:
            h = max(1, py - y)

        self.prepareGeometryChange()
        self.setRect(QRectF(x, y, w, h))

    # -------------------------- paint -----------------------------
    def paint(self, painter, option, widget=None):
        # borda
        pen = self._pen_custom or self.pen_normal
        if self.isSelected():
            pen = self.pen_selected
        painter.setPen(pen)
        painter.drawRect(self.rect())

        # alças
        if self.isSelected():
            painter.setBrush(self.handle_brush)
            painter.setPen(self.handle_pen)
            for rect in self._all_handles().values():
                painter.drawRect(rect)


# ======================================================================
#  Editor / Gerenciador
# ======================================================================
class ROIWindowEditor(QObject):
    """
    Conecta-se a um QGraphicsView fornecido e oferece:

        editor = ROIWindowEditor(view)
        editor.start_drawing()   # clique-e-arrasta cria janelas
        editor.stop_drawing()

        item = editor.add_window(10, 10, 100, 80)
        editor.windows          # lista de itens
    """

    # ---- sinais públicos -------------------------------------------
    windowAdded   = pyqtSignal(object)   # ResizableRectItem
    windowRemoved = pyqtSignal(object)   # ResizableRectItem

    def __init__(self,
                 view: QGraphicsView,
                 *,
                 ask_name: bool = False):
        super().__init__(view)
        self.view = view
        self._ask_name = ask_name         # solicita nome ao criar janela
        if self.view.scene() is None:
            self.view.setScene(QGraphicsScene(self.view))

        self._drawing = False
        self._tmp_rect: Optional[ResizableRectItem] = None
        self._start_pos: QPointF | None = None
        self.windows: List[ResizableRectItem] = []

        # instala-se como filtro para mouse/teclado
        view.viewport().installEventFilter(self)
        # atalho Delete automatizado
        self.view.scene().installEventFilter(self)

    # ---------------- interface pública --------------------------
    def start_drawing(self, pen: QPen = QPen(Qt.GlobalColor.red, 2)):
        """Entra no modo desenho (criação de novas janelas)."""
        self._drawing_pen = pen
        self._drawing = True
        self.view.setCursor(Qt.CursorShape.CrossCursor)

    def stop_drawing(self):
        """Sai do modo desenho."""
        self._drawing = False
        self.view.setCursor(Qt.CursorShape.ArrowCursor)
        if self._tmp_rect and self._tmp_rect.scene():
            self.view.scene().removeItem(self._tmp_rect)
        self._tmp_rect = None

    def add_window(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        pen: Optional[QPen] = None,
        deletable: bool = True,
        change_cb: Optional[Callable[[ResizableRectItem], None]] = None
    ) -> ResizableRectItem:
        item = ResizableRectItem(x, y, w, h, pen,
                                 change_callback=change_cb,
                                 deletable=deletable)
        self.view.scene().addItem(item)
        self.windows.append(item)
        return item

    # -------------------- event filter ----------------------------
    def eventFilter(self, obj, ev):
        # --- tecla DELETE (escopo da cena) -------------------------
        if ev.type() == QEvent.Type.KeyPress and ev.key() == Qt.Key.Key_Delete:
            self._delete_selected()
            return True

        # -------------- desenho (viewport) -------------------------
        if obj is self.view.viewport() and self._drawing:
            if ev.type() == QEvent.Type.MouseButtonPress and ev.button() == Qt.MouseButton.LeftButton:
                self._start_pos = self.view.mapToScene(ev.position().toPoint())
                self._tmp_rect = ResizableRectItem(
                    self._start_pos.x(), self._start_pos.y(), 0, 0,
                    self._drawing_pen, deletable=True
                )
                self.view.scene().addItem(self._tmp_rect)
                return True

            if ev.type() == QEvent.Type.MouseMove and self._tmp_rect and self._start_pos:
                cur = self.view.mapToScene(ev.position().toPoint())
                x = min(self._start_pos.x(), cur.x())
                y = min(self._start_pos.y(), cur.y())
                w = abs(cur.x() - self._start_pos.x())
                h = abs(cur.y() - self._start_pos.y())
                self._tmp_rect.setRect(x, y, w, h)
                return True

            if ev.type() == QEvent.Type.MouseButtonRelease and self._tmp_rect and self._start_pos:
                # fixa janela definitiva (>=3 px em ambas as direções)
                valid = (self._tmp_rect.rect().width()  > 2 and
                         self._tmp_rect.rect().height() > 2)

                if valid and self._ask_name:
                    # ----------------------------------------------------------------
                    #  Solicita NOME ▶ se usuário cancelar ou string vazia → descarta
                    # ----------------------------------------------------------------
                    name, ok = QInputDialog.getText(
                        self.view, "Nome da Posição Mecânica",
                        "Digite o nome da posição mecânica:")
                    name = name.strip()
                    if not ok or not name:
                        valid = False     # força descarte
                    else:
                        # salva no item (pode ser usado depois)
                        self._tmp_rect.name = name
                        self._tmp_rect.setToolTip(name)

                if valid:
                    self.windows.append(self._tmp_rect)
                    self.windowAdded.emit(self._tmp_rect)
                else:  # pequena ou sem nome → descarta
                    self.view.scene().removeItem(self._tmp_rect)
                self._tmp_rect = None
                self._start_pos = None
                if not self._drawing:      # pode ter sido parado externamente
                    self.view.setCursor(Qt.CursorShape.ArrowCursor)
                return True
        return False

    # --------------------- utilidades -----------------------------
    def _delete_selected(self):
        scene = self.view.scene()
        for it in scene.selectedItems():
            if isinstance(it, ResizableRectItem) and it.deletable:
                scene.removeItem(it)
                if it in self.windows:
                    self.windows.remove(it)
                    self.windowRemoved.emit(it)
        scene.clearSelection()
