# selectable_rect_item.py
from PyQt6.QtWidgets import QGraphicsRectItem, QGraphicsItem
from PyQt6.QtGui      import QPen, QBrush, QColor, QCursor
from PyQt6.QtCore     import Qt, QRectF, QPointF

HANDLE_SIZE = 6          # px
HANDLE_BRUSH = QBrush(QColor(255, 255, 255))
HANDLE_PEN   = QPen(Qt.GlobalColor.black, 1)

class SelectableResizableRectItem(QGraphicsRectItem):
    """
    • Selecionável (clique)  –  borda fica tracejada
    • Arrastável             –  ItemIsMovable
    • Redimensionável        –  8 alças nos cantos/lados
    """
    def __init__(self, x, y, w, h, pen=None, parent=None,
                 change_callback=None, deletavel: bool = True):
        super().__init__(x, y, w, h, parent)
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable    |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)
        self.pen_default = pen or QPen(Qt.GlobalColor.green, 2)
        self.pen_selected = QPen(Qt.GlobalColor.blue, 2, Qt.PenStyle.DashLine)
        self.setPen(self.pen_default)
        self.change_callback = change_callback
        # --- nova propriedade comum --------------------------------
        #  True  → pode ser removido com a tecla Delete
        #  False → protegido contra deleção pelo atalho
        self.deletavel = deletavel

        # alça atualmente ativa (None se não está redimensionando)
        if callable(self.change_callback):
            self.change_callback(self)

    # --------------------------------------------------------------
    # HELPERS DE ALÇAS
    # --------------------------------------------------------------
    def _handles(self):
        """
        Retorna dicionário {nome: QRectF} em coordenadas da cena
        nomes = 'tl','tm','tr','mr','br','bm','bl','ml'  (top-left etc.)
        """
        r = self.rect()
        x, y, w, h = r.x(), r.y(), r.width(), r.height()
        s = HANDLE_SIZE
        cx, cy = x + w/2, y + h/2
        return {
            'tl': QRectF(x-s/2,     y-s/2,     s, s),
            'tm': QRectF(cx-s/2,    y-s/2,     s, s),
            'tr': QRectF(x+w-s/2,   y-s/2,     s, s),
            'mr': QRectF(x+w-s/2,   cy-s/2,    s, s),
            'br': QRectF(x+w-s/2,   y+h-s/2,   s, s),
            'bm': QRectF(cx-s/2,    y+h-s/2,   s, s),
            'bl': QRectF(x-s/2,     y+h-s/2,   s, s),
            'ml': QRectF(x-s/2,     cy-s/2,    s, s)
        }

    def _handle_at(self, pos: QPointF):
        for name, rect in self._handles().items():
            if rect.contains(pos):
                return name
        return None

    # --------------------------------------------------------------
    # EVENTOS  mouse / hover
    # --------------------------------------------------------------
    def hoverMoveEvent(self, ev):
        handle = self._handle_at(ev.pos())
        cursors = {
            'tl': Qt.CursorShape.SizeFDiagCursor, 'br': Qt.CursorShape.SizeFDiagCursor,
            'tr': Qt.CursorShape.SizeBDiagCursor, 'bl': Qt.CursorShape.SizeBDiagCursor,
            'ml': Qt.CursorShape.SizeHorCursor,   'mr': Qt.CursorShape.SizeHorCursor,
            'tm': Qt.CursorShape.SizeVerCursor,   'bm': Qt.CursorShape.SizeVerCursor,
        }
        self.setCursor(QCursor(cursors.get(handle, Qt.CursorShape.ArrowCursor)))
        super().hoverMoveEvent(ev)

    def mousePressEvent(self, ev):
        self._active_handle = self._handle_at(ev.pos())
        super().mousePressEvent(ev)

    def mouseMoveEvent(self, ev):
        if self._active_handle:
            self._resize(ev.pos())
        else:
            super().mouseMoveEvent(ev)

    def mouseReleaseEvent(self, ev):
        self._active_handle = None
        super().mouseReleaseEvent(ev)

    def itemChange(self, change, value):
        if (change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged and
                callable(self.change_callback)):
            self.change_callback(self)
        return super().itemChange(change, value)

    # --------------------------------------------------------------
    def _resize(self, pos: QPointF):
        rect = self.rect()
        x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
        px, py = pos.x(), pos.y()

        if 'l' in self._active_handle:
            new_x = min(px, x+w-1)
            w += x - new_x
            x = new_x
        if 'r' in self._active_handle:
            w = max(1, px - x)
        if 't' in self._active_handle:
            new_y = min(py, y+h-1)
            h += y - new_y
            y = new_y
        if 'b' in self._active_handle:
            h = max(1, py - y)

        self.prepareGeometryChange()
        self.setRect(QRectF(x, y, w, h))
        # notifica alteração durante o redimensionamento
        if callable(self.change_callback):
            self.change_callback(self)

    # --------------------------------------------------------------
    # DESENHO
    # --------------------------------------------------------------
    def paint(self, painter, option, widget=None):
        # borda
        painter.setPen(self.pen_selected if self.isSelected() else self.pen_default)
        super().paint(painter, option, widget)
        # alças
        if self.isSelected():
            painter.setBrush(HANDLE_BRUSH)
            painter.setPen(HANDLE_PEN)
            for rect in self._handles().values():
                painter.drawRect(rect)
