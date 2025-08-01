# roi_window_editor.py  –  v3  (22/Jul/2025)
#
#  Novidades v3 – Janelas-dependentes (“filhos”)
#  --------------------------------------------
#  • Qualquer janela pode ser marcada como PAI  (tipicamente a posição mecânica)
#  • add_window(…, parent=item_pai)            → cria filho
#  • editor.focus_on_parent(item|uid|None)     → mostra só os filhos do pai ativo
#  • serialização inclui:
#        { "id": <int>, "parent": <int|null>, … }
#  • Métodos utilitários:
#        editor.current_parent()        → item ou None
#        editor.all_children(parent)    → lista[ResizableRectItem]
#
#  Compatível com v2 – APIs antigas não mudaram.
# ----------------------------------------------------------------------

from __future__ import annotations
import json, os, itertools
from typing import Callable, Dict, Optional, List, Any, Union
from PyQt6.QtCore import Qt, QRectF, QPointF, QPoint, QObject, QEvent, pyqtSignal
from PyQt6.QtGui import QPen, QBrush
from PyQt6.QtWidgets import (
    QGraphicsRectItem, QGraphicsItem, QGraphicsView, QGraphicsScene,
    QInputDialog
)

HANDLE = 6  # px


# ======================================================================
#  Item individual (janela)
# ======================================================================
class ResizableRectItem(QGraphicsRectItem):
    """
    Retângulo arrastável/redimensionável.

    Novo v3:
      – id            → identificador único inteiro
      – parent_uid    → id do item-pai (ou None)
      – is_child()    → True se pertence a um pai
    """
    _id_counter = itertools.count(1)      # gerador global

    pen_normal   = QPen(Qt.GlobalColor.green, 2)
    pen_selected = QPen(Qt.GlobalColor.blue, 2, Qt.PenStyle.DashLine)
    handle_brush = QBrush(Qt.GlobalColor.white)
    handle_pen   = QPen(Qt.GlobalColor.black, 1)

    def __init__(
        self,
        x: float, y: float, w: float, h: float,
        *,
        pen: Optional[QPen] = None,
        change_callback: Optional[Callable[['ResizableRectItem'], None]] = None,
        deletable: bool = True,
        name: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
        parent_uid: Optional[int] = None,
        parent: Optional[QGraphicsItem] = None,
        editable: bool = True            # NOVO: janelas “somente-seleção” no visor principal
    ):
        super().__init__(x, y, w, h, parent)
        self.editable: bool = editable
        self.id: int = next(self._id_counter)
        self.parent_uid: Optional[int] = parent_uid
        # --------------------------------------------------------
        # ItemIsMovable + redimensionamento só se editable=True
        flags = (
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        if self.editable:
            flags |= QGraphicsItem.GraphicsItemFlag.ItemIsMovable
        self.setFlags(flags)
        self.setAcceptHoverEvents(self.editable)
        self._active_handle: Optional[str] = None
        self._pen_custom = pen
        self.change_callback = change_callback
        self.deletable = deletable
        # ----------- metadados livres ----------------------------
        self.name: Optional[str] = name
        self.meta: Dict[str, Any] = meta or {}
        if self.name:
            self.setToolTip(self.name)
        # callback inicial
        if callable(self.change_callback):
            self.change_callback(self)

    # ------------------------------------------------------------
    #  Conveniências
    # ------------------------------------------------------------
    def is_child(self) -> bool:
        return self.parent_uid is not None

    # ------------------------------------------------------------
    #  Helpers internos (redimensionamento)
    # ------------------------------------------------------------
    def _all_handles(self) -> Dict[str, QRectF]:
        r = self.rect()
        x, y, w, h = r.x(), r.y(), r.width(), r.height()
        s = HANDLE
        cx, cy = x + w/2.0, y + h/2.0
        return {
            'tl': QRectF(x - s/2,   y - s/2,   s, s),
            'tm': QRectF(cx - s/2,  y - s/2,   s, s),
            'tr': QRectF(x + w - s/2, y - s/2, s, s),
            'mr': QRectF(x + w - s/2, cy - s/2, s, s),
            'br': QRectF(x + w - s/2, y + h - s/2, s, s),
            'bm': QRectF(cx - s/2,  y + h - s/2, s, s),
            'bl': QRectF(x - s/2,   y + h - s/2, s, s),
            'ml': QRectF(x - s/2,   cy - s/2,  s, s),
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

    # ---------------- eventos  -------------------------------
    def hoverMoveEvent(self, ev):
        if self.editable:
            self.setCursor(self._cursor_for(self._handle_at(ev.pos())))
        super().hoverMoveEvent(ev)

    def mousePressEvent(self, ev):
        if self.editable and ev.button() == Qt.MouseButton.LeftButton:
            self._active_handle = self._handle_at(ev.pos())
        super().mousePressEvent(ev)

    def mouseMoveEvent(self, ev):
        if self.editable and self._active_handle:
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

    # ---------------- mudanças de posição ---------------------
    def itemChange(self, change, value):
        if (change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged
                and callable(self.change_callback)):
            self.change_callback(self)
        return super().itemChange(change, value)

    # ---------------- redimensionamento -----------------------
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

    # ---------------- desenho ------------------------------
    def paint(self, painter, option, widget=None):
        pen = self._pen_custom or self.pen_normal
        if self.isSelected():
            pen = self.pen_selected
        painter.setPen(pen)
        painter.drawRect(self.rect())
        # Alças de redimensionamento apenas se editável
        if self.isSelected() and self.editable:
            painter.setBrush(self.handle_brush)
            painter.setPen(self.handle_pen)
            for rect in self._all_handles().values():
                painter.drawRect(rect)

    # ---------------- serialização --------------------------
    def to_dict(self) -> Dict[str, Any]:
        r = self.rect()
        return dict(
            id=self.id,
            parent=self.parent_uid,
            x=r.x(), y=r.y(), w=r.width(), h=r.height(),
            name=self.name,
            meta=self.meta
        )


# ======================================================================
#  Editor / Gerenciador
# ======================================================================
class ROIWindowEditor(QObject):
    """
    Gerenciador universal de janelas redimensionáveis.

    Novidades v3 (janelas-filhas):
    --------------------------------
    • add_window(…, parent=None) → cria dependência hierárquica.
    • focus_on_parent(pai|uid|None)
        – None           → mostra todas as janelas
        – ResizableItem  → mostra apenas seus filhos
    • current_parent()          → retorna pai ativo
    • all_children(pai)         → lista de filhos
    """
    windowAdded   = pyqtSignal(object)   # ResizableRectItem
    windowRemoved = pyqtSignal(object)
    windowChanged = pyqtSignal(object)

    # --------------- init -------------------------------------
    def __init__(self,
                 view: QGraphicsView,
                 *,
                 ask_name: bool = False,
                 autosave_path: Optional[str] = None):

        super().__init__(view)
        self.view = view
        self._ask_name = ask_name
        self.autosave_path = autosave_path
        if self.view.scene() is None:
            self.view.setScene(QGraphicsScene(self.view))

        self._drawing = False
        self._drawing_parent: Optional[ResizableRectItem] = None
        self._tmp_rect: Optional[ResizableRectItem] = None
        self._start_pos: QPointF | None = None
        self.windows: List[ResizableRectItem] = []

        # parent currently focused (None = todos visíveis)
        self._parent_focus_uid: Optional[int] = None

        # event‐filter (viewport para mouse, scene para teclado)
        view.viewport().installEventFilter(self)
        self.view.scene().installEventFilter(self)

        # ------------------------------------------------------------------
        #  PREVENÇÃO DE ACESSO APÓS DESTRUIÇÃO DO QGraphicsView
        # ------------------------------------------------------------------
        # Quando a janela é encerrada o QGraphicsView é destruído antes
        # do ROIWindowEditor.  Mantemos uma flag para ignorar eventos
        # subsequentes e evitar  “wrapped C/C++ object … has been deleted”.
        self._view_deleted = False
        self.view.destroyed.connect(self._on_view_destroyed)

    # --------------- API PÚBLICA ------------------------------
    #  ----- modo desenho --------------------------------------
    def start_drawing(self, *,
                      pen: QPen = QPen(Qt.GlobalColor.red, 2),
                      parent: Optional[ResizableRectItem] = None):
        """Habilita desenho; janelas receberão `parent` (opcional)."""
        self._drawing_pen = pen
        self._drawing_parent = parent
        self._drawing = True
        self.view.setCursor(Qt.CursorShape.CrossCursor)

    def stop_drawing(self):
        self._drawing = False
        self._drawing_parent = None
        self.view.setCursor(Qt.CursorShape.ArrowCursor)
        if self._tmp_rect and self._tmp_rect.scene():
            self.view.scene().removeItem(self._tmp_rect)
        self._tmp_rect = None

    # ---- criação programática --------------------------------
    def add_window(self,
                   x: float, y: float, w: float, h: float,
                   *,
                   pen: Optional[QPen] = None,
                   deletable: bool = True,
                   name: Optional[str] = None,
                   meta: Optional[Dict[str, Any]] = None,
                   change_cb: Optional[Callable[[ResizableRectItem], None]] = None,
                   parent: Optional[ResizableRectItem] = None,
                   editable: bool = True          # NOVO
                   ) -> ResizableRectItem:

        item_parent_uid = parent.id if parent else None
        item = ResizableRectItem(
            x, y, w, h,
            pen=pen,
            deletable=deletable,
            name=name,
            meta=meta,
            parent_uid=item_parent_uid,
            parent=parent,                       # hierarquia Qt
            change_callback=self._wrap_change_cb(change_cb),
            editable=editable
        )
        # CORREÇÃO: Sempre adiciona à cena se não há pai Qt Graphics
        # (mesmo que tenha parent_uid para associação lógica)
        if parent is None:
            self.view.scene().addItem(item)
        # Se tem pai Qt Graphics, não precisa addItem (já vinculado automaticamente)
        self.windows.append(item)
        self.windowAdded.emit(item)
        self._autosave()
        return item

    # ------------ foco / filtragem ----------------------------
    def focus_on_parent(self,
                        parent: Optional[Union[ResizableRectItem, int]]):
        """
        Define a janela-pai “ativa”.
        • None → todas as janelas visíveis
        • item / id → exibe APENAS os filhos desse pai
        Janelas sem pai (top-level) permanecem sempre visíveis.
        """
        if isinstance(parent, ResizableRectItem):
            uid = parent.id
        else:
            uid = parent
        self._parent_focus_uid = uid
        # PROTEÇÃO: Remove itens inválidos da lista antes de usar
        valid_windows = []
        # DEBUGGING: Log da operação de foco
        if uid is None:
            print(f"🔍 Focando em: TODOS os itens")
        else:
            print(f"🔍 Focando em pai UID: {uid}")
        for w in self.windows:
            try:
                # Testa se objeto Qt ainda existe
                _ = w.scene()
                valid_windows.append(w)
                # Se chegou aqui, objeto é válido - aplica visibilidade
                if w.parent_uid is None:
                    w.setVisible(True)          # sempre visível
                    print(f"  ✅ Item sem pai sempre visível: {getattr(w, 'name', w.id)}")
                else:
                    should_be_visible = (w.parent_uid == uid)
                    w.setVisible(should_be_visible)
                    visibility_status = "VISÍVEL" if should_be_visible else "OCULTO"
                    print(f"  {'✅' if should_be_visible else '❌'} Item {getattr(w, 'name', w.id)} (pai: {w.parent_uid}): {visibility_status}")
            except RuntimeError:
                print(f"  🗑️ Item inválido removido da lista")
                # Objeto foi deletado - ignora silenciosamente
                pass
        self.windows = valid_windows

    def show_all_comparison_windows(self):
        """
        Mostra todas as janelas de comparação (que têm parent_uid),
        mantendo posições mecânicas (sem parent_uid) sempre visíveis.
        """
        for w in self.windows:
            # Posições mecânicas (sem pai) sempre visíveis
            # Janelas de comparação (com pai) sempre visíveis também  
            w.setVisible(True)

    def current_parent(self) -> Optional[ResizableRectItem]:
        """Retorna o item-pai atualmente em foco (ou None)."""
        if self._parent_focus_uid is None:
            return None
        for w in self.windows:
            if w.id == self._parent_focus_uid:
                return w
        return None

    def all_children(self, parent: ResizableRectItem) -> List[ResizableRectItem]:
        """Lista todos os filhos imediatos do item informado."""
        return [w for w in self.windows if w.parent_uid == parent.id]
    
    def get_window_by_id(self, window_id: int) -> Optional[ResizableRectItem]:
        """Retorna janela pelo ID"""
        for w in self.windows:
            if hasattr(w, 'id') and w.id == window_id:
                return w
        return None

    # --------------- EVENT FILTER -----------------------------
    def eventFilter(self, obj, ev):
        # ---- tecla Delete (escopo da cena) --------------------
        # ----------------------------------------------------------
        # Evita acessar self.view depois que o objeto C++ foi
        # destruído (fase de shutdown da aplicação).
        # ----------------------------------------------------------
        if self._view_deleted:
            return False

        # viewport pode não existir mais nestas alturas; tenta acessar
        # com proteção.
        try:
            viewport = self.view.viewport()
        except RuntimeError:
            return False
        if ev.type() == QEvent.Type.KeyPress and ev.key() == Qt.Key.Key_Delete:
            self._delete_selected()
            return True

        # ---- desenho (viewport) ------------------------------
        if obj is viewport and self._drawing:
            if ev.type() == QEvent.Type.MouseButtonPress and ev.button() == Qt.MouseButton.LeftButton:
                self._start_pos = self.view.mapToScene(QPoint(int(ev.position().x()),
                                                              int(ev.position().y())))
                self._tmp_rect = ResizableRectItem(
                    self._start_pos.x(), self._start_pos.y(), 0, 0,
                    pen=self._drawing_pen, deletable=True,
                    parent=self._drawing_parent,  # pai Qt Graphics (pode ser None)
                    parent_uid=self._drawing_parent.id if self._drawing_parent else None
                )
                # CORREÇÃO: Sempre adiciona à cena durante desenho
                if self._drawing_parent is None:
                    self.view.scene().addItem(self._tmp_rect)
                else:
                    # Mesmo com pai lógico, se pai Qt Graphics for de outra cena, adiciona à cena atual
                    if self._drawing_parent.scene() != self.view.scene():
                        self.view.scene().addItem(self._tmp_rect)
                        self._tmp_rect.parent = None  # Remove pai Qt Graphics para evitar conflitos
                self.windows.append(self._tmp_rect)
                return True

            if ev.type() == QEvent.Type.MouseMove and self._tmp_rect and self._start_pos:
                cur = self.view.mapToScene(QPoint(int(ev.position().x()),
                                                  int(ev.position().y())))
                x = min(self._start_pos.x(), cur.x())
                y = min(self._start_pos.y(), cur.y())
                w = abs(cur.x() - self._start_pos.x())
                h = abs(cur.y() - self._start_pos.y())
                self._tmp_rect.setRect(x, y, w, h)
                return True

            if ev.type() == QEvent.Type.MouseButtonRelease and self._tmp_rect and self._start_pos:
                valid = (self._tmp_rect.rect().width() > 2
                         and self._tmp_rect.rect().height() > 2)

                # nome opcional somente para janelas TOP-LEVEL
                if valid and self._ask_name and self._drawing_parent is None:
                    name, ok = QInputDialog.getText(
                        self.view, "Nome da Janela", "Digite um nome (opcional):"
                    )
                    if ok:
                        name = name.strip()
                        if name:
                            self._tmp_rect.name = name
                            self._tmp_rect.setToolTip(name)

                if not valid:
                    # descarta
                    if self._tmp_rect in self.windows:
                        self.windows.remove(self._tmp_rect)
                    if self._tmp_rect.scene():
                        self._tmp_rect.scene().removeItem(self._tmp_rect)
                else:
                    # finaliza
                    self._tmp_rect.change_callback = self._wrap_change_cb(
                        self._tmp_rect.change_callback)
                    self.windowAdded.emit(self._tmp_rect)
                    self._autosave()
                self._tmp_rect = None
                self._start_pos = None
                if not self._drawing:
                    self.view.setCursor(Qt.CursorShape.ArrowCursor)
                return True
        return False
    
    # ------------------------------------------------------------------
    #  Callback disparado quando o QGraphicsView for destruído
    # ------------------------------------------------------------------
    def _on_view_destroyed(self, *_):
        """
        Marca flag para que o eventFilter ignore qualquer evento
        pendente após a destruição do QGraphicsView.
        """
        self._view_deleted = True

    # --------------- SERIALIZAÇÃO -----------------------------
    def to_dict_list(self) -> List[Dict[str, Any]]:
        return [w.to_dict() for w in self.windows]

    def from_dict_list(self, data: List[Dict[str, Any]], *, clear=True):
        """
        Restaura hierarquia em 2 passagens para garantir que
        itens-pai existam antes dos filhos.
        """
        if clear:
            self._clear_all()
        # 1ª passagem – cria todos os TOP LEVEL
        id_map: Dict[int, ResizableRectItem] = {}
        for d in data:
            if d.get("parent") is not None:
                continue
            it = self.add_window(
                d["x"], d["y"], d["w"], d["h"],
                name=d.get("name"), meta=d.get("meta", {}),
                parent=None
            )
            it.id = d["id"]               # preserva UID
            id_map[it.id] = it

        # 2ª passagem – cria filhos
        for d in data:
            if d.get("parent") is None:
                continue
            parent_it = id_map.get(d["parent"])
            if parent_it is None:         # órfão → ignora
                continue
            it = self.add_window(
                d["x"], d["y"], d["w"], d["h"],
                name=d.get("name"), meta=d.get("meta", {}),
                parent=parent_it
            )
            it.id = d["id"]
            id_map[it.id] = it

        self.view.viewport().update()
        self._autosave()

    def save_json(self, path: str):
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict_list(), f, indent=2)

    def load_json(self, path: str, *, clear=True):
        if not os.path.isfile(path):
            return False
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                self.from_dict_list(data, clear=clear)
                return True
        except Exception:
            pass
        return False

    # --------------- INTERNOS ---------------------------------
    def _wrap_change_cb(self, user_cb):
        """
        Garante callback + autosave + sinal.
        """
        def _cb(item):
            if callable(user_cb):
                user_cb(item)
            self.windowChanged.emit(item)
            self._autosave()
        return _cb

    def _autosave(self):
        if self.autosave_path:
            try:
                self.save_json(self.autosave_path)
            except Exception:
                pass

    def _delete_selected(self):
        scene = self.view.scene()
        for it in scene.selectedItems():
            if isinstance(it, ResizableRectItem) and it.deletable:
                # remove também os FILHOS ligados a este item
                for child in list(self.all_children(it)):
                    if child.scene():
                        child.scene().removeItem(child)
                    if child in self.windows:
                        self.windows.remove(child)
                    self.windowRemoved.emit(child)
                scene.removeItem(it)
                if it in self.windows:
                    self.windows.remove(it)
                self.windowRemoved.emit(it)
        scene.clearSelection()
        self._autosave()

    def _clear_all(self):
        scene = self.view.scene()
        for w in list(self.windows):
            if w.scene() is scene:
                scene.removeItem(w)
        self.windows.clear()
