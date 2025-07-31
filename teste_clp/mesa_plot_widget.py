"""
mesa_plot_widget.py
-------------------
Widget (QGraphicsView) que desenha a área de trabalho de uma mesa,
os pontos carregados no programa e a posição atual da cabeça.
Usa apenas Qt (sem dependências externas).
"""
from typing import List, Tuple, Optional
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, \
                           QGraphicsRectItem, QGraphicsSimpleTextItem
from PyQt6.QtGui import QPen, QBrush, QColor, QPainter
from PyQt6.QtCore import QRectF, Qt, QSizeF

class MesaPlotWidget(QGraphicsView):
    def __init__(self,
                 limits_xy: dict[str, Tuple[int, int]],
                 *,
                 title: str = "",
                 parent=None):
        super().__init__(parent)
        self._lim = limits_xy             # {'x':(min,max),'y':(min,max)}
        # -----------------------------------------------------------------
        #  Guardamos limites “brutos” em pulsos e calculamos  1:1  na tela
        #  • x_range : pulses_x_max – pulses_x_min
        #  • y_range : pulses_y_max – pulses_y_min
        #    Se forem diferentes o gráfico ficava “esticado”.
        #  • Aplicamos factor  _scale_y  para traçar
        #        y_plot = y_raw * _scale_y
        #    tornando 1 pulsos→1 px  equivalente em X e Y.
        # -----------------------------------------------------------------
        self._lim_raw = limits_xy        # {'x':(..),(..), 'y':(..),(..)}
        x0, x1 = limits_xy['x']
        y0, y1 = limits_xy['y']
        x_range = x1 - x0
        y_range = y1 - y0 if (y1 - y0) != 0 else 1
        self._scale_y = x_range / y_range
        # lim com Y já escalonado
        self._lim = {
            'x': (x0, x1),
            'y': (y0 * self._scale_y, y1 * self._scale_y)
        }
        self._scene  = QGraphicsScene(self)
        self.setScene(self._scene)
        # Qt 6 ⇒ enum está em QPainter.RenderHint
        self.setRenderHints(
            self.renderHints()
            | QPainter.RenderHint.Antialiasing
            | QPainter.RenderHint.TextAntialiasing
        )
        # elementos estáticos
        self._build_static(title)

        # barras de rolagem sempre ocultas
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # dinâmicos
        self._point_items: List[QGraphicsEllipseItem] = []
        self._head_item: Optional[QGraphicsEllipseItem] = None

    # -----------------------------------------------------------------
    #  Construção do retângulo e título
    # -----------------------------------------------------------------
    def _build_static(self, title:str):
        self._scene.clear()
        # Atenção: usamos limites COM y já escalonado
        x0,x1 = self._lim['x']; y0,y1 = self._lim['y']
        w  = x1-x0;   h  = y1-y0
        # retângulo origem (0,0).  Deixamos margem 5 %
        margin = 0.05*max(w,h)
        rect = QRectF(x0-margin, y0-margin, w+2*margin, h+2*margin)
        self._work_rect = rect
        self.setSceneRect(rect)
        pen = QPen(QColor("#455A64")); pen.setWidth(2)
        brush = QBrush(Qt.BrushStyle.NoBrush)
        self._scene.addRect(QRectF(x0, y0, w, h), pen, brush)
        # título
        tit = QGraphicsSimpleTextItem(title)
        tit.setPos(x0, y0-h*0.07)
        self._scene.addItem(tit)        

        # invert-Y para ficar origem em baixo-esquerda
        self.scale(1, -1)
        # força ajuste inicial
        self._fit()

    # -----------------------------------------------------------------
    #  Interface pública
    # -----------------------------------------------------------------
    def update_points(self, points: List[Tuple[float,float]]):
        """Lista [(x,y), …] em pulsos."""
        # remove antigos
        for it in self._point_items:
            self._scene.removeItem(it)
        self._point_items.clear()
        # ----------------------------------------------------------
        #  1) Corrige ESPELHAMENTO X  (imagem tipo “página virada”)
        #  2) Aplica factor _scale_y  para manter proporção 1:1
        # ----------------------------------------------------------
        x_min, x_max = self._lim['x']
        # adiciona
        pen = QPen(Qt.GlobalColor.darkBlue); pen.setWidth(0)
        brush = QBrush(Qt.GlobalColor.blue)
        r_pix = 6   # diâmetro em pixels (fixo)
        for (x, y) in points:
            x = x_min + x_max - x
            y = y * self._scale_y
            e = self._scene.addEllipse(
                x, y, 0, 0, pen, brush)  # placeholder
            # tamanho fixo  – ignora transformações (pixels na tela)
            e.setRect(-r_pix/2, -r_pix/2, r_pix, r_pix)
            e.setPos(x, y)
            e.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIgnoresTransformations)
            self._point_items.append(e)

    def update_head_position(self, x: int, y: int):
        """Atualiza / cria círculo vermelho da cabeça."""
        r_pix = 10
        # aplica correção de espelhamento X
        x_min, x_max = self._lim['x']
        x = x_min + x_max - x
        y = y * self._scale_y
        if self._head_item is None:
            pen = QPen(Qt.GlobalColor.red); pen.setWidth(0)
            brush = QBrush(Qt.GlobalColor.red)
            self._head_item = self._scene.addEllipse(
                -r_pix/2, -r_pix/2, r_pix, r_pix, pen, brush)
            self._head_item.setFlag(
                QGraphicsEllipseItem.GraphicsItemFlag.ItemIgnoresTransformations)
        else:
            pass
        self._head_item.setPos(x, y)
    
    # -----------------------------------------------------------------
    #  Ajusta automaticamente o zoom
    # -----------------------------------------------------------------
    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        self._fit()

    def _fit(self):
        """Ajusta o retângulo de trabalho para caber na view."""
        if hasattr(self, "_work_rect"):
            self.fitInView(self._work_rect, Qt.AspectRatioMode.KeepAspectRatio)