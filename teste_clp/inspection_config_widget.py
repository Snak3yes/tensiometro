from PyQt6.QtWidgets import (
    QGroupBox, QVBoxLayout, QFormLayout, QSpinBox, QPushButton,
    QLabel, QHBoxLayout, QSizePolicy, QDialog,
    QGraphicsView, QGraphicsScene, QWidget, QTreeWidget, QTreeWidgetItem
)
from roi_window_editor import ROIWindowEditor, ResizableRectItem
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QImage
import cv2

# ================================================================
#  CONFIGURAÇÃO – larguras mínimas dos visores da janela auxiliar
#  • altere aqui se desejar outros valores
# ================================================================
MIN_REGION_WIDTH = 800     # visor principal (esquerda)
MIN_REGION_HEIGHT = 600    # altura do visor principal (4:3)
MIN_ROI_WIDTH    = 350     # visor ROI        (direita)
MIN_ROI_HEIGHT   = 262     # altura do ROI (4:3)
# MIN_REGION_WIDTH = 480     # visor principal (esquerda)
# MIN_REGION_HEIGHT = 360    # altura do visor principal (4:3)
# MIN_ROI_WIDTH    = 240     # visor ROI        (direita)
# MIN_ROI_HEIGHT   = 180     # altura do ROI (4:3)


# ------------------------------------------------------------------
#  Diálogo auxiliar em 2 colunas  (80 % região | 20 % controles)
# ------------------------------------------------------------------
class _AuxDialog(QDialog):
    def __init__(self,
                 pix_region,            # QPixmap da região capturada
                 ctrl_widget,           # InspectionConfigWidget (controles)
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle("Auxiliar de Inspeção")
        self.setWindowModality(Qt.WindowModality.NonModal)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)

        # ---------- COLUNA ESQUERDA  (imagem + editor ROI) -----------
        # Usa QGraphicsView para poder desenhar janelas via ROIWindowEditor
        # ----------------------------------------------------------------
        #  Imagem original (alta resolução) recebida do widget principal
        # ----------------------------------------------------------------
        self._orig_pix = pix_region or QPixmap()   # cache como QPixmap

        self.view_region = QGraphicsView()
        self.view_region.setMinimumWidth(MIN_REGION_WIDTH)
        self.view_region.setMinimumHeight(MIN_REGION_HEIGHT)
        self.view_region.setScene(QGraphicsScene(self.view_region))
        self.view_region.setRenderHints(
            QPainter.RenderHint.SmoothPixmapTransform |
            QPainter.RenderHint.Antialiasing
        )
        self._pix_item = self.view_region.scene().addPixmap(self._orig_pix)
        # Posições mecânicas — pede nome ao concluir
        self.region_editor = ROIWindowEditor(self.view_region, ask_name=True)

        # ---------- mantém cópia BGR da imagem para recortes ----------
        # numpy BGR correspondente – usado para recortes exatos
        self._orig_bgr = None
        if not self._orig_pix.isNull():
            self._orig_bgr = self._qpix_to_bgr(self._orig_pix)
        # caso o widget principal possua buffer original, usa-o (mais fiel)
        if getattr(parent, "_last_roi_bgr", None) is not None:
            self._orig_bgr = parent._last_roi_bgr.copy()

        # ---------- layout principal ---------------------------------
        h = QHBoxLayout(self)
        h.addWidget(self.view_region, 4)   # 80 %

        # ------------- coluna direita (controles + botões extras) ----
        right_box = QWidget()
        vright = QVBoxLayout(right_box); vright.setContentsMargins(0, 0, 0, 0)
        vright.addWidget(ctrl_widget, 1)

        # NOVOS BOTÕES – exclusivos desta janela
        self.btn_mech = QPushButton("Posição mecanica")
        self.btn_mech.setCheckable(True)
        self.btn_cmp  = QPushButton("Comparação de imagem")
        self.btn_cmp.setCheckable(True)
        # ---------- TREEVIEW – lista de posições mecânicas ------------
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        vright.addWidget(self.tree, 2)

        vright.addWidget(self.btn_mech)
        vright.addWidget(self.btn_cmp)
        vright.addStretch()

        h.addWidget(right_box, 1)          # 20 %

        # Garante que o preview interno e o botão auxiliar não apareçam
        for attr in ("lbl_region", "btn_aux"):
            if hasattr(ctrl_widget, attr) and getattr(ctrl_widget, attr):
                getattr(ctrl_widget, attr).setVisible(False)

        # --------------- ROI (thumbnail) – substitui QLabel por View ---
        roi_label = getattr(ctrl_widget, "lbl_roi", None)
        if roi_label:
            roi_pix = roi_label.pixmap() or QPixmap()
            self.view_roi = QGraphicsView()
            self.view_roi.setMinimumWidth(MIN_ROI_WIDTH)
            self.view_roi.setMinimumHeight(MIN_ROI_HEIGHT)
            self.view_roi.setScene(QGraphicsScene(self.view_roi))
            self.view_roi.setRenderHints(
                QPainter.RenderHint.SmoothPixmapTransform |
                QPainter.RenderHint.Antialiasing
            )
            self.view_roi.scene().addPixmap(roi_pix)
            self.roi_editor = ROIWindowEditor(self.view_roi)   # comparação

            parent_lay = roi_label.parentWidget().layout()
            idx = parent_lay.indexOf(roi_label)
            parent_lay.removeWidget(roi_label)
            roi_label.setParent(None)
            parent_lay.insertWidget(idx, self.view_roi)
        else:
            self.view_roi = None
            self.roi_editor = None
            self._roi_pix_item = None

        # -------------------------- sinais botões ---------------------
        self.btn_mech.toggled.connect(
            lambda st: self._toggle_editor("mech", st))
        self.btn_cmp.toggled.connect(
            lambda st: self._toggle_editor("cmp", st))
        
        # ---------------- sincronização Tree ⇄ Scene -----------------
        self.region_editor.windowAdded.connect(self._on_window_added)
        self.region_editor.windowRemoved.connect(self._on_window_removed)
        self.view_region.scene().selectionChanged.connect(
            self._on_scene_selection_changed)
        self.tree.itemSelectionChanged.connect(
            self._on_tree_selection_changed)
        
        # --------------------------------------------------------------
        #  Quando o usuário seleciona um retângulo (posição mecânica),
        #  o conteúdo interno é recortado da imagem original e exibido
        #  no visor “Região ROI” à direita, mantendo resolução e escala.
        # --------------------------------------------------------------
        self.view_region.scene().selectionChanged.connect(
            self._update_roi_from_selection)

        # ------------------------------------------------------------------
        #  Sempre que o usuário clicar em “Definir região” no painel direito,
        #  o sinal regionCaptured(img_bgr) será emitido.  Conectamos para que
        #  o novo ROI substitua imediatamente a imagem exibida na coluna
        #  esquerda (“Região de Inspeção”).
        # ------------------------------------------------------------------
        if hasattr(ctrl_widget, "regionCaptured"):
            ctrl_widget.regionCaptured.connect(self._on_region_captured)
            # Actualiza também o visor da JANELA PRINCIPAL
            if parent is not None and hasattr(parent, "_apply_external_roi"):
                ctrl_widget.regionCaptured.connect(parent._apply_external_roi)

        # ROI capturado na janela PRINCIPAL deve reflectir aqui
        if parent is not None and hasattr(parent, "regionCaptured"):
            parent.regionCaptured.connect(self._on_region_captured)

        # Contador para janelas de comparação de imagem (por posição mecânica)
        self._comparison_window_counters = {}  # {posicao_mecanica_item: contador}

    # ------------ helpers internos ----------------------------------
    def _update_pix(self):
        """Escala novamente a partir da imagem original (evita cascata)."""
        if self._orig_pix.isNull():
            return
        if not self._orig_pix.isNull():
            self._pix_item.setPixmap(self._orig_pix)
            self.view_region.fitInView(self._pix_item,
                                       Qt.AspectRatioMode.KeepAspectRatio)
            
    def _get_next_comparison_name(self, parent_item):
        """
        Gera o próximo nome automático para janela de comparação específico 
        para cada posição mecânica (w1, w2, w3, etc.)
        """
        if parent_item is None:
            # Se não há posição mecânica, usa contador global de fallback
            fallback_counter = getattr(self, '_fallback_counter', 0) + 1
            self._fallback_counter = fallback_counter
            return f"w{fallback_counter}"
        
        # Obtém ou inicializa o contador específico desta posição mecânica
        current_count = self._comparison_window_counters.get(parent_item, 0)
        current_count += 1
        self._comparison_window_counters[parent_item] = current_count
        return f"w{current_count}"
    
    def _get_selected_mechanical_position_node(self):
        """Retorna o nó da posição mecânica atualmente selecionado na tree"""
        selected_items = self.tree.selectedItems()
        if not selected_items:
            return None
        
        node = selected_items[0]
        # Se é um subitem (janela de comparação), pega o pai (posição mecânica)
        if node.parent() is not None:
            return node.parent()
        
        # Se é um item de primeiro nível, verifica se é uma posição mecânica
        item_data = node.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(item_data, ResizableRectItem):
            return node
        
        return None
            
    # ===================  TREEVIEW Sync  ============================
    def _on_window_added(self, item):
        """Insere item na árvore"""
        name = getattr(item, 'name', 'Posição mecânica')
        node = QTreeWidgetItem([name])
        node.setData(0, Qt.ItemDataRole.UserRole, item)
        self.tree.addTopLevelItem(node)

    def _on_comparison_window_added(self, item):
        """Adiciona janela de comparação como subitem da posição mecânica selecionada"""
        # Primeiro identifica a posição mecânica pai
        parent_item = None
        
        # PRIORIDADE 1: Verifica qual posição mecânica está selecionada na cena principal
        # (esta determina o que é exibido no visor ROI)
        parent_node = None
        
        
        # Primeiro verifica se há uma posição mecânica selecionada na cena principal
        selected_scene_items = self.view_region.scene().selectedItems()
        for scene_item in selected_scene_items:
            if isinstance(scene_item, ResizableRectItem):
                # Encontra o nó correspondente na TreeView
                for i in range(self.tree.topLevelItemCount()):
                    tree_node = self.tree.topLevelItem(i)
                    if tree_node.data(0, Qt.ItemDataRole.UserRole) is scene_item:
                        parent_node = tree_node
                        parent_item = scene_item
                        self.log(f"✓ Usando posição mecânica selecionada na cena: {tree_node.text(0)}")
                        break
                if parent_node:
                    break
        
        # PRIORIDADE 2: Se não há seleção na cena, verifica a TreeView
        if parent_node is None:
            selected_tree_items = self.tree.selectedItems()
            if selected_tree_items:
                selected_node = selected_tree_items[0]
                # Se selecionou uma posição mecânica (item de primeiro nível)
                if selected_node.parent() is None:
                    item_data = selected_node.data(0, Qt.ItemDataRole.UserRole)
                    if isinstance(item_data, ResizableRectItem):
                        parent_node = selected_node
                        parent_item = item_data
                        self.log(f"✓ Usando posição mecânica selecionada na TreeView: {selected_node.text(0)}")
                # Se selecionou uma janela de comparação (filho), pega o pai
                else:
                    parent_node = selected_node.parent()
                    if parent_node:
                        parent_item = parent_node.data(0, Qt.ItemDataRole.UserRole)
                        self.log(f"✓ Usando posição mecânica pai da seleção: {parent_node.text(0)}")
        
        # PRIORIDADE 3: Se ainda não encontrou, procura a posição mecânica mais recente que está sendo exibida no ROI
        if parent_node is None:
            # Verifica se há alguma posição mecânica que foi usada recentemente para atualizar o ROI
            if hasattr(self, '_last_roi_parent_item') and self._last_roi_parent_item:
                # Procura o nó correspondente na tree
                for i in range(self.tree.topLevelItemCount()):
                    tree_node = self.tree.topLevelItem(i)
                    if tree_node.data(0, Qt.ItemDataRole.UserRole) is self._last_roi_parent_item:
                        parent_node = tree_node
                        parent_item = self._last_roi_parent_item
                        self.log(f"✓ Usando última posição mecânica que gerou o ROI: {tree_node.text(0)}")
                        break
        
        # PRIORIDADE 4: Como último recurso, cria um item raiz temporário
        if parent_node is None:
            parent_node = QTreeWidgetItem(["⚠️ Sem posição mecânica definida"])
            parent_node.setData(0, Qt.ItemDataRole.UserRole, None)
            self.tree.addTopLevelItem(parent_node)
            self.log("⚠️ Criado nó temporário - nenhuma posição mecânica encontrada")

        # Gera nome automático baseado no contador específico da posição mecânica
        comp_name = self._get_next_comparison_name(parent_item)
        
        # Cria subitem para a janela de comparação
        comp_node = QTreeWidgetItem([comp_name])
        comp_node.setData(0, Qt.ItemDataRole.UserRole, item)
        parent_node.addChild(comp_node)
        
        # Expande o nó pai para mostrar o subitem
        parent_node.setExpanded(True)
        
        # Limpa seleção anterior e seleciona apenas o novo subitem
        self.tree.setCurrentItem(comp_node)
        
        # Salva referência do nome gerado no item
        item.comparison_name = comp_name

        # Atualiza registro da posição mecânica pai para próximas janelas
        if parent_item and isinstance(parent_item, ResizableRectItem):
            self._last_roi_parent_item = parent_item
    
    def log(self, message):
        """Helper para logging (usa o log do controller se disponível)"""
        if hasattr(self, '_c') and hasattr(self._c, 'log'):
            self._c.log(message)
        elif hasattr(self, 'parent') and hasattr(self.parent(), 'log'):
            self.parent().log(message)
        else:
            print(f"[AuxDialog] {message}")

    def _on_window_removed(self, item):
        """Remove linha correspondente na tree"""
        # Remove de itens de primeiro nível (posições mecânicas)
        for i in range(self.tree.topLevelItemCount()):
            n = self.tree.topLevelItem(i)
            if n.data(0, Qt.ItemDataRole.UserRole) is item:
                # Limpa contador desta posição mecânica quando ela for removida
                if item in self._comparison_window_counters:
                    del self._comparison_window_counters[item]
                    self.log(f"✓ Contador de comparação resetado para posição removida")
                self.tree.takeTopLevelItem(i)
                return
        # Remove subitens (janelas de comparação) e ajusta contadores
        for i in range(self.tree.topLevelItemCount()):
            parent_node = self.tree.topLevelItem(i)
            parent_item = parent_node.data(0, Qt.ItemDataRole.UserRole)
            for j in range(parent_node.childCount()):
                child_node = parent_node.child(j)
                if child_node.data(0, Qt.ItemDataRole.UserRole) is item:
                    # Obtém o nome da janela antes de remover para reajustar contador
                    removed_name = child_node.text(0)
                    parent_node.removeChild(child_node)
                    # Reajusta o contador da posição mecânica se necessário
                    if parent_item and parent_item in self._comparison_window_counters:
                        # Se removeu a última janela criada, decrementa o contador
                        current_max = self._comparison_window_counters[parent_item]
                        if removed_name == f"w{current_max}":
                            self._comparison_window_counters[parent_item] = max(0, current_max - 1)
                            self.log(f"✓ Contador ajustado para posição mecânica: w{self._comparison_window_counters[parent_item]}")
                    # Se o pai não tem mais filhos e era "Posição não definida", remove também
                    if (parent_node.childCount() == 0 and 
                        ("Posição não definida" in parent_node.text(0) or 
                         "Sem posição mecânica" in parent_node.text(0))):
                        parent_index = self.tree.indexOfTopLevelItem(parent_node)
                        if parent_index >= 0:
                            self.tree.takeTopLevelItem(parent_index)
                    return
                
    def _reset_comparison_counter(self, parent_item):
        """Reseta o contador de comparação para uma posição mecânica específica"""
        if parent_item in self._comparison_window_counters:
            self._comparison_window_counters[parent_item] = 0
            self.log(f"✓ Contador de comparação resetado para posição mecânica")

    def _on_scene_selection_changed(self):
        """Seleciona linha da tree conforme retângulo"""
        sel_items = self.view_region.scene().selectedItems()
        # Se nada selecionado, limpa seleção da tree
        if not sel_items:
            self.tree.clearSelection()
            return
        item = sel_items[0]
        # Garante seleção única - remove seleção de outros itens
        for other_item in sel_items[1:]:
            other_item.setSelected(False)
        # procura nó correspondente
        for i in range(self.tree.topLevelItemCount()):
            n = self.tree.topLevelItem(i)
            if n.data(0, Qt.ItemDataRole.UserRole) is item:
                self._select_tree_node(n)
                return
            
            # Verifica subitens também
            for j in range(n.childCount()):
                child = n.child(j)
                if child.data(0, Qt.ItemDataRole.UserRole) is item:
                    self._select_tree_node(child)
                    return
        # Também verifica itens na cena ROI
        if self.view_roi and item.scene() == self.view_roi.scene():
            # Se é item da cena ROI, mantém seleção mas não interfere na tree
            pass
        else:
            # Se não encontrou correspondente, limpa seleção da tree
            self.tree.clearSelection()
    
    def _select_tree_node(self, node):
        """Helper para selecionar um nó na tree"""
        if node and not node.isSelected():
            self.tree.blockSignals(True)
            self.tree.setCurrentItem(node)
            self.tree.blockSignals(False)
                    

    def _on_tree_selection_changed(self):
        """Seleciona retângulo na cena ao clicar na tree"""
        nodes = self.tree.selectedItems()
        if not nodes:
            return
        node = nodes[0]
        item = node.data(0, Qt.ItemDataRole.UserRole)

        if item is None:
            return
            
        # Verifica se o objeto ainda é válido
        try:
            if hasattr(item, 'scene') and item.scene():
                # Limpa seleção de ambas as cenas primeiro
                self.view_region.scene().clearSelection()
                if self.view_roi:
                    self.view_roi.scene().clearSelection()
                    
                # Seleciona apenas o item correto na cena correta
                if item.scene() == self.view_region.scene():
                    item.setSelected(True)
                    self.view_region.centerOn(item)
                elif self.view_roi and item.scene() == self.view_roi.scene():
                    item.setSelected(True)
                    self.view_roi.centerOn(item)
        except RuntimeError:
            # Objeto foi deletado, remove da tree
            if node.parent():
                node.parent().removeChild(node)
            else:
                index = self.tree.indexOfTopLevelItem(node)
                if index >= 0:
                    self.tree.takeTopLevelItem(index)

        # Se é uma janela de comparação, também atualiza o ROI
        if hasattr(item, 'comparison_name'):
            self._update_roi_from_selection()
    
    # ------------ slot: novo ROI vindo do painel --------------------
    def _on_region_captured(self, img_bgr):
        """
        Recebe numpy BGR do widget de controle e actualiza o visor grande
        sem efeito “cascata”.
        """
        # troca cache original (pix + bgr) e reajusta view
        self._orig_bgr = img_bgr.copy() if img_bgr is not None else None
        self._orig_pix = InspectionConfigWidget._bgr_to_pixmap(img_bgr)
        self._update_pix()

    # ------------ novo: recorte da posição mecânica ------------------
    def _update_roi_from_selection(self):
        """
        Recorta a área da Posição Mecânica selecionada e mostra
        na view_roi preservando a resolução original.
        """
        if self.view_roi is None or self._orig_bgr is None:
            return
        # seleciona apenas retângulos do editor
        sel = [it for it in self.view_region.scene().selectedItems()
               if isinstance(it, ResizableRectItem)]
        if not sel:
            return
        item = sel[0]
        # usa retângulo do item já mapeado p/ cena (inclui posição)
        r_scene = item.mapRectToScene(item.rect())
        x, y, w, h = map(int, [r_scene.x(), r_scene.y(),
                               r_scene.width(), r_scene.height()])
        h_img, w_img, _ = self._orig_bgr.shape
        # limita dentro da imagem
        x = max(0, min(x, w_img - 1))
        y = max(0, min(y, h_img - 1))
        w = max(1, min(w, w_img - x))
        h = max(1, min(h, h_img - y))
        roi_bgr = self._orig_bgr[y:y + h, x:x + w].copy()
        if roi_bgr.size == 0:
            return
        # -------------------- mostra ROI no visor direito -------------------

        # Registra qual posição mecânica gerou este ROI (para janelas de comparação futuras)
        self._last_roi_parent_item = item
        
        # Atualiza o visor ROI

        roi_px = InspectionConfigWidget._bgr_to_pixmap(roi_bgr)  # qualidade máx.

        # atualiza visor ROI preservando proporção e resolução
        scene = self.view_roi.scene()
        scene.clear()
        self._roi_pix_item = scene.addPixmap(roi_px)
        self.view_roi.fitInView(self._roi_pix_item,
                                Qt.AspectRatioMode.KeepAspectRatio)

    # mantém proporção 4:3 na imagem grande
    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        self._fit_views()

    # ------------ ajuste automático das views -----------------------
    def _fit_views(self):
        if hasattr(self, "_pix_item") and self._pix_item:
            self.view_region.fitInView(self._pix_item,
                                       Qt.AspectRatioMode.KeepAspectRatio)
        if hasattr(self, "view_roi") and self.view_roi:
            self.view_roi.fitInView(
                self.view_roi.scene().itemsBoundingRect(),
                Qt.AspectRatioMode.KeepAspectRatio)

    # --------------------------------------------------------------
    #  Conversões utilitárias
    # --------------------------------------------------------------
    @staticmethod
    def _qpix_to_bgr(px: QPixmap):
        """Converte QPixmap → numpy BGR preservando resolução."""
        if px.isNull():
            return None
        img = px.toImage().convertToFormat(QImage.Format.Format_RGB888)
        w, h = img.width(), img.height()
        ptr = img.bits().asstring(w * h * 3)
        import numpy as np
        arr = np.frombuffer(ptr, np.uint8).reshape((h, w, 3))
        return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)

    # ------------ habilita / desabilita editores --------------------
    def _toggle_editor(self, which: str, enabled: bool):
        if which == "mech":
            if enabled:
                self.region_editor.start_drawing()
                self.btn_cmp.setChecked(False)
            else:
                self.region_editor.stop_drawing()
        elif which == "cmp" and self.roi_editor is not None:
            if enabled:
                self.roi_editor.start_drawing()
                # Configura para não pedir nome (será gerado automaticamente)
                self.roi_editor._ask_name = False
                # Conecta o sinal de janela adicionada ao ROI editor
                if not hasattr(self.roi_editor, '_comparison_connected'):
                    self.roi_editor.windowAdded.connect(self._on_comparison_window_added)
                    self.roi_editor.windowRemoved.connect(self._on_comparison_window_removed)
                    self.roi_editor._comparison_connected = True
                self.btn_mech.setChecked(False)
            else:
                self.roi_editor.stop_drawing()
                # Restaura comportamento padrão
                self.roi_editor._ask_name = False
    def _on_comparison_window_removed(self, item):
        """Handler para remoção de janela de comparação"""
        self._on_window_removed(item)

# ------------------------------------------------------------------
#  QLabel com proporção fixa (default = 4:3)
# ------------------------------------------------------------------
class AspectRatioLabel(QLabel):
    """
    QLabel que mantém width : height = 4 : 3
    (ou outro aspecto definido no construtor).
    Usa o mecanismo height-for-width do Qt ‑ sem precisar de
    resizeEvent personalizado no widget contêiner.
    """
    def __init__(self, *args, aspect_ratio: float = 4/3, **kwargs):
        super().__init__(*args, **kwargs)
        self._aspect_ratio = aspect_ratio        # width / height
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Expanding)

    # ---- height-for-width ----------------------------------------
    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, w: int) -> int:
        return int(w / self._aspect_ratio)

    # sizeHint garante 4:3 quando o layout consulta o widget
    def sizeHint(self):
        hint = super().sizeHint()
        hint.setHeight(self.heightForWidth(hint.width()))
        return hint

# ------------------------------------------------------------------
#  InspectionConfigWidget
#  • show_region         → exibe/omite o visor grande na própria coluna
#  • show_aux_button     → exibe/omite o botão “Aux. de inspeção”
#  • show_size_controls  → exibe/omite campos Largura / Altura
#  • show_region_button  → exibe/omite o botão “Definir região”
# ------------------------------------------------------------------
class InspectionConfigWidget(QGroupBox):
    """
    UI da Ação 'Inspeção'.
    """
    parametersChanged = pyqtSignal(int, int)       # width, height
    regionCaptured    = pyqtSignal(object)         # img_bgr

    def __init__(self, controller,
                 parent=None,
                 *,
                 show_region: bool = True,
                 show_aux_button: bool = True,
                 show_size_controls: bool = True,
                 show_region_button: bool = True):
        super().__init__("Config. Inspeção", parent)
        self._c = controller
        self._show_region = show_region
        self._show_aux_button = show_aux_button
        self._template = None
        self._last_roi_bgr = None
        self._show_size_controls = show_size_controls
        self._show_region_button = show_region_button
        self._build_ui()

    # ---------------- construção ----------------------------
    def _build_ui(self):
        v = QVBoxLayout(self)

        form = QFormLayout()
        self._ratio = 4/3
        self._internal = False   # evita recursão ao sincronizar
        self.spin_w = QSpinBox(); self.spin_w.setRange(12, 4000); self.spin_w.setValue(400)
        self.spin_h = QSpinBox(); self.spin_h.setRange(9, 3000);  self.spin_h.setValue(int(400/ self._ratio))
        if self._show_size_controls:
            form.addRow("Largura (px):", self.spin_w)
            form.addRow("Altura  (px):", self.spin_h)
        v.addLayout(form)

        # botão capturar região
        self.btn_region = QPushButton("Definir região")
        if self._show_region_button:
            v.addWidget(self.btn_region)

        # visor grande (4:3) – largura elástica, altura controlada
        self.lbl_region = AspectRatioLabel("Região")
        self._style_label(self.lbl_region)
        # já possui SizePolicy.Expanding|Expanding no construtor
        # exibe apenas se solicitado
        if self._show_region:
            v.addWidget(self.lbl_region)
        else:
            self.lbl_region.setVisible(False)

        # visor pequeno (ROI mecânico)
        # visor ROI menor (metade da largura, 4:3, centrado)
        self.lbl_roi = QLabel("ROI")
        self._style_label(self.lbl_roi)
        self.lbl_roi.setAlignment(
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        # largura controlada manualmente → Policy.Fixed evita “esticar”
        self.lbl_roi.setSizePolicy(QSizePolicy.Policy.Fixed,
                                   QSizePolicy.Policy.Fixed)
        v.addWidget(self.lbl_roi)
        # Garante que ambos os visores começam com a geometria correta
        self._update_roi_aspect()

        # similaridade + salvar
        hsim = QHBoxLayout()
        self.spin_sim = QSpinBox(); self.spin_sim.setRange(50, 100); self.spin_sim.setValue(95)
        hsim.addWidget(QLabel("Similaridade mínima %:"))
        hsim.addWidget(self.spin_sim)
        self.btn_save = QPushButton("Salvar")
        hsim.addWidget(self.btn_save)
        hsim.addStretch()
        v.addLayout(hsim)

        # linha de botões
        h = QHBoxLayout()
        self.btn_inspect = QPushButton("Inspecionar")
        self.btn_addimg  = QPushButton("Add imagem")
        h.addWidget(self.btn_inspect); h.addWidget(self.btn_addimg)
        v.addLayout(h)

        # botão auxiliar (opcional)
        if self._show_aux_button:
            self.btn_aux = QPushButton("Aux. de inspeção")
            v.addWidget(self.btn_aux)            
        else:
            self.btn_aux = None     # atributo presente para checagem externa
        v.addStretch()

        # sinais
        if self._show_size_controls:
            self.spin_w.valueChanged.connect(self._emit_params)
            self.spin_h.valueChanged.connect(self._emit_params)
            # mantém 4:3
            self.spin_w.valueChanged.connect(lambda w: self._sync_hw('w', w))
            self.spin_h.valueChanged.connect(lambda h: self._sync_hw('h', h))
        if self._show_region_button:
            self.btn_region.clicked.connect(self._capture_region)
        # botão “Aux. de inspeção” só existe se show_aux_button=True
        if self.btn_aux is not None:
            self.btn_aux.clicked.connect(self._open_aux)

    # -------------------- tamanho fixo 4:3 ---------------------------
    def _update_region_aspect(self):
        """
        Agora é responsabilidade do próprio AspectRatioLabel via
        height-for-width.  Esta função existe apenas por compatibilidade
        e pode ser chamada livremente sem causar efeitos colaterais.
        """
        pass   # nada a fazer – proporção garantida pelo widget

    def _update_roi_aspect(self):
        """
        Ajusta SOMENTE o visor ROI.
        Passa a ser completamente independente do visor 'Região'.
        """
        col_w = self.width() or 1                  # largura real da coluna
        roi_w = max(10, int(col_w * 0.5))          # 50 % da coluna
        self.lbl_roi.setFixedWidth(roi_w)          # largura fixa
        self.lbl_roi.setFixedHeight(int(roi_w * 3 / 4))  # mantém 4:3

    def _style_label(self, lab: QLabel):
        lab.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lab.setStyleSheet("QLabel { background:#263238; color:#CFD8DC; }")

    # ---------------- ratio keeper ---------------------------------
    def _sync_hw(self, changed, val):
        if self._internal: return
        self._internal = True
        if changed == 'w':
            self.spin_h.setValue(int(val / self._ratio))
        else:
            self.spin_w.setValue(int(val * self._ratio))
        self._internal = False

    # ---------------- -- slots ------------------------------
    def _emit_params(self):
        self.parametersChanged.emit(self.spin_w.value(), self.spin_h.value())

    def _grab_frame(self):
        cm = getattr(self._c, "camera_manager", None)
        if not cm or not getattr(cm, "_cap", None): return None
        ok, frame = cm._cap.read()
        return frame if ok else None
    
    # ================================================================
    #  Sincronização com outras janelas
    # ================================================================
    def _apply_external_roi(self, img_bgr):
        """
        Recebe um ROI capturado em OUTRO InspectionConfigWidget
        (ex.: o widget embutido na janela Auxiliar) e apenas actualiza
        o visor + buffer interno, SEM re-emitir regionCaptured
        (assim evitamos loops infinitos de sinal).
        """
        if img_bgr is None:
            return
        self._last_roi_bgr = img_bgr
        self._show_pixmap(self.lbl_region, img_bgr, draw_border=True)

    def _capture_region(self):
        frame = self._grab_frame()
        if frame is None:
            return
        h_img, w_img, _ = frame.shape
        ww = self.spin_w.value(); hh = self.spin_h.value()
        cx, cy = w_img//2, h_img//2
        x0 = max(0, cx-ww//2); y0 = max(0, cy-hh//2)
        roi = frame[y0:y0 + hh, x0:x0 + ww].copy()
        self._last_roi_bgr = roi          # guarda original p/ alta qualidade
        self._show_pixmap(self.lbl_region, roi, draw_border=True)
        self.regionCaptured.emit(roi)

    def _show_pixmap(self, label: QLabel, img_bgr, *, draw_border=False):
        if img_bgr is None: return
        h,w,_ = img_bgr.shape
        if draw_border:
            img_bgr = cv2.rectangle(img_bgr.copy(), (0,0), (w-1,h-1),
                                    (0,255,255), 2)
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        from PyQt6.QtGui import QImage, QPixmap
        qimg = QImage(img_rgb.data, w, h, 3*w, QImage.Format.Format_RGB888)
        px = QPixmap.fromImage(qimg).scaled(
            label.width(), label.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation)
        label.setPixmap(px)

    def _open_aux(self):
        # 1) widget de controle (lado direito)
        # no painel à direita omitimos o visor da região E o botão auxiliar
        ctrl_w = InspectionConfigWidget(
            self._c,
            show_region=False,
            show_aux_button=False,
            show_size_controls=False,      # ‼ remove Largura / Altura
            show_region_button=False       # ‼ remove “Definir região”
        )
        ctrl_w.spin_w.setValue(self.spin_w.value())
        ctrl_w.spin_h.setValue(self.spin_h.value())
        ctrl_w.spin_sim.setValue(self.spin_sim.value())
        # 2) obtém ROI em resolução total, se disponível
        if self._last_roi_bgr is not None:
            pix = self._bgr_to_pixmap(self._last_roi_bgr)
        else:
            pix = self.lbl_region.pixmap()

        # 3) cria diálogo e mostra
        dlg = _AuxDialog(pix, ctrl_w, self)   # <-- 'self' = widget principal
        dlg.resize(900, 600)
        dlg.show()
    
    # ------------------------------------------------------------------
    #  Utilitário estático – converte numpy BGR → QPixmap sem downscale
    # ------------------------------------------------------------------
    @staticmethod
    def _bgr_to_pixmap(img_bgr):
        if img_bgr is None:
            return QPixmap()
        h, w, _ = img_bgr.shape
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        from PyQt6.QtGui import QImage, QPixmap
        qimg = QImage(img_rgb.data, w, h, 3 * w, QImage.Format.Format_RGB888)
        return QPixmap.fromImage(qimg)

    # exportação
    def roi_size(self):
        return self.spin_w.value(), self.spin_h.value()
    
    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        # region já é automático; apenas ROI necessita ajuste
        self._update_roi_aspect()
