"""
GerberPreviewWidget - Widget de Preview baseado no POC (QGraphicsView)

Baseado em: poc_gerber/gerber_viewer/gui/preview.py
"""

import logging
from typing import List, Optional

from PyQt6.QtCore import Qt, QRectF, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPathItem, QGraphicsItem

logger = logging.getLogger(__name__)


class GerberGraphicsItem(QGraphicsPathItem):
    """
    Item gráfico para um polígono Gerber (baseado no POC).
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
        self.setData(0, index)  # Guarda índice do objeto
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)

    def setSelectionBrush(self, brush: QBrush):
        """Define cor de seleção."""
        self._selection_brush = brush
        if self.isSelected():
            self.setBrush(self._selection_brush)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value):
        """Troca cor quando seleção muda."""
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self.setBrush(self._selection_brush if bool(value) else self._normal_brush)
        return super().itemChange(change, value)


class GerberPreviewWidget(QGraphicsView):
    """
    Widget de preview do Gerber baseado em QGraphicsView (POC).

    Features:
        - Renderização vetorial com QGraphicsScene
        - Zoom com scroll do mouse
        - Pan com botão do meio
        - Seleção de objetos (clique e RubberBand)
        - Exibe regions/polígonos corretamente
    """

    # Signals para compatibilidade com código existente
    aperture_selected = pyqtSignal(dict)  # Emitido ao clicar em uma aperture
    objectDeleteRequested = pyqtSignal(int)  # Índice do objeto para excluir (único)
    objectDeleteManyRequested = pyqtSignal(list)  # Lista de índices para excluir (múltiplos)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 500)

        # Cena gráfica
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        # Para receber eventos de teclado (Delete etc.)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Estado
        self._zoom = 1.0
        self._objects: Optional[List] = None  # Lista de GerberObject
        self._polys_mm: List[List[tuple[float, float]]] = []  # Polígonos em mm
        self._items: List[GerberGraphicsItem] = []  # Itens gráficos

        # Cores
        self._aperture_color = QColor("#00BCD4")  # Ciano (regions)
        self._selection_color = QColor("#FF5722")  # Laranja avermelhado
        self._bg_color = QColor("#1e1e1e")  # Fundo escuro

        # Configurações da view
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

        # Permite seleção por retângulo
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)

        # Cor de fundo
        self._scene.setBackgroundBrush(self._bg_color)

        logger.info("GerberPreviewWidget (QGraphicsView) inicializado")

    def set_objects(self, objects: List) -> None:
        """
        Recebe lista de GerberObject do parser e renderiza.

        Args:
            objects: Lista de GerberObject do parser
        """
        print(f"[INFO] set_objects() chamado com {len(objects)} objetos")

        self._objects = []
        polys_mm = []

        # Extrair polígonos dos objetos
        for obj in objects or []:
            poly = obj.polygon_mm
            if not poly or len(poly) < 3:
                continue
            self._objects.append(obj)
            polys_mm.append(poly)

        print(f"[INFO] {len(polys_mm)} polígonos válidos extraídos")

        # Limpar cena
        self._scene.clear()
        self._items = []
        self._polys_mm = polys_mm

        if not polys_mm:
            print("[WARN] Nenhum polígono para renderizar")
            return

        # Calcular bounding box
        xs = [pt[0] for poly in polys_mm for pt in poly]
        ys = [pt[1] for poly in polys_mm for pt in poly]
        minx, maxx = min(xs), max(xs)
        miny, maxy = min(ys), max(ys)
        w = maxx - minx
        h = maxy - miny

        print(f"[INFO] Bounding box: X[{minx:.1f}, {maxx:.1f}], Y[{miny:.1f}, {maxy:.1f}]")

        if w == 0 or h == 0:
            print("[WARN] Bounding box inválido")
            return

        # Criar itens gráficos
        normal_brush = QBrush(self._aperture_color)
        selection_brush = QBrush(self._selection_color)
        pen = QPen(Qt.PenStyle.NoPen)

        for idx, poly in enumerate(polys_mm):
            if len(poly) < 3:
                continue

            # Criar QPainterPath (NEGAR Y - Gerber Y aumenta para cima, Qt Y aumenta para baixo)
            path = QPainterPath()
            x0, y0 = poly[0]
            path.moveTo(x0, -y0)
            for x, y in poly[1:]:
                path.lineTo(x, -y)

            # Criar item gráfico
            item = GerberGraphicsItem(
                path,
                idx,
                normal_brush,
                selection_brush,
                pen,
            )
            self._scene.addItem(item)
            self._items.append(item)

        print(f"[INFO] {len(self._items)} itens gráficos criados")

        # Definir scene rect (Y negado)
        rect = QRectF(minx, -maxy, w, h)
        self._scene.setSceneRect(rect)

        # Ajustar view
        self.reset_view()

    def reset_view(self):
        """Ajusta zoom para mostrar todo o conteúdo."""
        self.resetTransform()
        self._zoom = 1.0
        if not self._scene.items():
            return
        self.fitInView(
            self._scene.sceneRect(),
            Qt.AspectRatioMode.KeepAspectRatio,
        )
        # Atualizar zoom
        transform = self.transform()
        self._zoom = transform.m11()  # fator de escala X (= Y)

    def remove_object_at_index(self, index: int) -> bool:
        """
        Remove um objeto da cena pelo índice.

        Args:
            index: Índice do objeto a ser removido

        Returns:
            True se removido com sucesso, False caso contrário
        """
        # Validar índice
        if not (0 <= index < len(self._items)):
            logger.warning(f"Índice inválido para remoção: {index}")
            return False

        try:
            # Remover item gráfico da cena
            item = self._items[index]
            self._scene.removeItem(item)

            # Remover das listas internas
            # NOTA: Não podemos remover da lista diretamente porque isso
            # desalinharia todos os índices subsequentes. Por ora, apenas
            # removemos da cena visual e marcamos como None.

            # Na implementação atual, removemos apenas da cena visual
            # e mantemos a lista intacta (índices não mudam)
            # TODO: Implementar sistema de undo/redo com reconstrução de índices

            logger.info(f"Objeto no índice {index} removido da cena")
            return True

        except Exception as e:
            logger.error(f"Erro ao remover objeto no índice {index}: {e}")
            return False

    def remove_objects_at_indices(self, indices: list[int]) -> int:
        """
        Remove múltiplos objetos da cena pelos índices.

        Args:
            indices: Lista de índices para remover

        Returns:
            Número de objetos removidos com sucesso
        """
        removed_count = 0
        for idx in sorted(indices, reverse=True):  # Reverse order para preservar índices
            if self.remove_object_at_index(idx):
                removed_count += 1

        logger.info(f"{removed_count} objetos removidos (solicitados: {len(indices)})")
        return removed_count

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

    def mousePressEvent(self, event):
        """Lida com cliques do mouse."""
        # Garante que a view receba eventos de teclado após clique
        self.setFocus()

        if event.button() == Qt.MouseButton.MiddleButton:
            # Inicia pan
            self._panning = True
            self._last_pan_pos = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return

        if event.button() == Qt.MouseButton.RightButton:
            # Menu de contexto (excluir)
            scene_pos = self.mapToScene(event.pos())
            items = self._scene.items(scene_pos)
            if items:
                item = items[0]
                idx = int(item.data(0))
                # TODO: Mostrar menu de contexto
                # Por ora, apenas emitir signal
                self.objectDeleteRequested.emit(idx)
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Pan com arrasto."""
        if hasattr(self, '_panning') and self._panning:
            delta = event.pos() - self._last_pan_pos
            self._last_pan_pos = event.pos()
            hbar = self.horizontalScrollBar()
            vbar = self.verticalScrollBar()
            hbar.setValue(hbar.value() - delta.x())
            vbar.setValue(vbar.value() - delta.y())
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def keyPressEvent(self, event):
        """
        Permite excluir objetos selecionados com a tecla Delete/Backspace.
        A confirmação é tratada pelo GerberUploadWidget.
        """
        key = event.key()
        if key in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            items = self._scene.selectedItems()
            if not items:
                event.accept()
                return

            # Coletar índices dos itens selecionados
            indices: set[int] = set()
            for it in items:
                try:
                    idx = int(it.data(0))
                    indices.add(idx)
                except Exception:
                    logger.exception("Erro ao obter índice do item")

            indices_sorted = sorted(indices)
            try:
                if len(indices_sorted) == 1:
                    # Exclusão simples
                    self.objectDeleteRequested.emit(indices_sorted[0])
                else:
                    # Exclusão em grupo
                    self.objectDeleteManyRequested.emit(indices_sorted)
            except Exception:
                logger.exception("Erro ao emitir signal de exclusão")

            event.accept()
            return

        # Teclas não tratadas: comportamento padrão
        super().keyPressEvent(event)

    def mouseReleaseEvent(self, event):
        """Finaliza pan e verifica seleção."""
        if event.button() == Qt.MouseButton.MiddleButton and hasattr(self, '_panning'):
            self._panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return

        # Chamar super() primeiro para processar seleção
        super().mouseReleaseEvent(event)

        # Após processar seleção, verificar se há itens selecionados
        # e emitir signal para habilitar botões
        self._emit_selection_changed()

    def _emit_selection_changed(self):
        """
        Emite signal aperture_selected quando há itens selecionados.

        Este método é chamado após mudanças de seleção para notificar
        o GerberUploadWidget que deve habilitar/desabilitar botões.
        """
        selected_items = self._scene.selectedItems()

        if selected_items and self._objects:
            # Pega o primeiro item selecionado
            item = selected_items[0]
            try:
                idx = int(item.data(0))

                # Verifica se índice é válido
                if 0 <= idx < len(self._objects):
                    obj = self._objects[idx]

                    # Converter GerberObject para dict (compatibilidade)
                    aperture_dict = self._gerber_object_to_dict(obj, idx)
                    self.aperture_selected.emit(aperture_dict)
                    logger.debug(f"aperture_selected emitido para índice {idx}")
            except Exception as e:
                logger.exception(f"Erro ao emitir aperture_selected: {e}")

    def _gerber_object_to_dict(self, obj, index: int) -> dict:
        """
        Converte GerberObject para dict (compatibilidade com código legado).

        Args:
            obj: GerberObject
            index: Índice do objeto

        Returns:
            Dict com dados da aperture
        """
        # Extrair atributos do GerberObject
        data = {
            'id': index,
            'type': getattr(obj, 'obj_type', 'unknown'),
            'x': getattr(obj, 'x', 0.0),
            'y': getattr(obj, 'y', 0.0),
        }

        # Adicionar dimensões específicas
        if hasattr(obj, 'diameter') and obj.diameter is not None:
            data['d'] = obj.diameter
        if hasattr(obj, 'width') and obj.width is not None:
            data['width'] = obj.width
        if hasattr(obj, 'height') and obj.height is not None:
            data['height'] = obj.height

        return data

    # Métodos de compatibilidade com código antigo
    def set_apertures(self, apertures: List[dict]) -> None:
        """Método de compatibilidade (não usado na nova versão)."""
        pass  # Ignorado, usamos set_objects() agora

    def set_fiducials(self, fiducials: List[dict]) -> None:
        """Método de compatibilidade (fiduciais não implementados ainda)."""
        pass

    def fit_to_view(self) -> None:
        """Método de compatibilidade - chama reset_view()."""
        self.reset_view()

    def remove_aperture(self, aperture: dict) -> None:
        """Método de compatibilidade (não implementado)."""
        pass

    def undo_remove(self) -> None:
        """Método de compatibilidade (não implementado)."""
        pass
