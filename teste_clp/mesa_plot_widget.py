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
                 steps_per_mm: dict[str, float],
                 y_axis: str,
                 title: str = "",
                 parent=None):
        super().__init__(parent)
        # -------------------- NOVO: unidades em milímetros --------------------
        self._steps = steps_per_mm           # {'X':…, 'Y1':…, 'Y2':…, 'Z':…}
        self._y_axis = y_axis                # 'Y1'  ou  'Y2'

        # Converte limites de pulsos → milímetros
        x0_mm = limits_xy['x'][0] / self._steps['X']
        x1_mm = limits_xy['x'][1] / self._steps['X']
        y0_mm = limits_xy['y'][0] / self._steps[self._y_axis]
        y1_mm = limits_xy['y'][1] / self._steps[self._y_axis]

        # ------------------------------------------------------------
        # Mantemos a proporção REAL da área de trabalho
        # (sem forçar o retângulo a virar um quadrado).
        # ------------------------------------------------------------
        self._scale_y = 1.0          # compatibilidade interna
        self._lim = {
            'x': (x0_mm, x1_mm),
            'y': (y0_mm, y1_mm)
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
        # ----------------  T Í T U L O  -----------------------------
        tit = QGraphicsSimpleTextItem(title)
        # Não sofre espelhamento / zoom
        tit.setFlag(
            QGraphicsSimpleTextItem.GraphicsItemFlag.ItemIgnoresTransformations)
        # 20 mm (aprox.) abaixo da borda inferior
        tit.setPos(x0, y0 - 20)
        self._scene.addItem(tit)        

        # invert-Y para ficar origem em baixo-esquerda
        self.scale(1, -1)
        # força ajuste inicial
        self._fit()

    # -----------------------------------------------------------------
    #  Interface pública
    # -----------------------------------------------------------------
    # ---------------- helper pulsos → mm -------------------------------
    def _p2mm(self, axis: str, pulses: float) -> float:
        return pulses / self._steps.get(axis, 1.0)

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
        for (x_raw, y_raw) in points:
            # ---------- conversão pulsos → mm  + ajustes ---------------
            x_mm = self._p2mm('X', x_raw)
            y_mm = self._p2mm(self._y_axis, y_raw)

            # espelhamento X
            x_plot = x_min + x_max - x_mm
            y_plot = y_mm
            e = self._scene.addEllipse(
                x_plot, y_plot, 0, 0, pen, brush)  # placeholder
            # tamanho fixo  – ignora transformações (pixels na tela)
            e.setRect(-r_pix/2, -r_pix/2, r_pix, r_pix)
            e.setPos(x_plot, y_plot)
            e.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIgnoresTransformations)
            self._point_items.append(e)

    def update_head_position(self, x: int, y: int):
        """Atualiza / cria círculo vermelho da cabeça."""
        r_pix = 10
        # conversões para mm
        x_mm = self._p2mm('X', x)
        y_mm = self._p2mm(self._y_axis, y)

        # espelhamento X
        x_min, x_max = self._lim['x']
        x_plot = x_min + x_max - x_mm
        y_plot = y_mm

        # ------------- visibilidade só dentro da área útil -------------
        in_x = self._lim['x'][0] <= x_mm <= self._lim['x'][1]
        in_y = self._lim['y'][0] <= y_mm <= self._lim['y'][1]
        if not (in_x and in_y):
            if self._head_item is not None:
                self._head_item.setVisible(False)
            return                     # ignora pontos fora da área

        if self._head_item is None:
            pen = QPen(Qt.GlobalColor.red); pen.setWidth(0)
            brush = QBrush(Qt.GlobalColor.red)
            self._head_item = self._scene.addEllipse(
                -r_pix/2, -r_pix/2, r_pix, r_pix, pen, brush)
            self._head_item.setFlag(
                QGraphicsEllipseItem.GraphicsItemFlag.ItemIgnoresTransformations)
        self._head_item.setPos(x_plot, y_plot)
        # caso estivesse oculto e volte para a área útil
        self._head_item.setVisible(True)
        self._head_item.setPos(x_plot, y_plot)

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