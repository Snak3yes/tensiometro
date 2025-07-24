from PyQt6.QtWidgets import (
    QGroupBox, QVBoxLayout, QFormLayout, QSpinBox, QPushButton,
    QLabel, QHBoxLayout, QSizePolicy, QDialog,
    QGraphicsView, QGraphicsScene, QWidget, QTreeWidget, QTreeWidgetItem
)
from roi_window_editor import ROIWindowEditor, ResizableRectItem
from selectable_rect_item import SelectableResizableRectItem
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui  import QGuiApplication
from PyQt6.QtGui import QPixmap, QPainter, QImage, QPen, QColor
import cv2
import os

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
                 update_callback=None,  # Função callback para atualização
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle("Auxiliar de Inspeção")
        self.setWindowModality(Qt.WindowModality.NonModal)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self._main_widget = ctrl_widget  # Referência ao widget principal
        self._update_callback = update_callback  # Callback para atualização direta

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
        self.region_editor = ROIWindowEditor(
            self.view_region, 
            ask_name=True, 
            autosave_path=os.path.join(ctrl_widget._c.prog_mgr.path, "mechanical_positions.json") if hasattr(ctrl_widget, '_c') and hasattr(ctrl_widget._c, 'prog_mgr') and ctrl_widget._c.prog_mgr else None
        )

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
            self.roi_editor = ROIWindowEditor(
                self.view_roi,
                autosave_path=os.path.join(ctrl_widget._c.prog_mgr.path, "comparison_windows.json") if hasattr(ctrl_widget, '_c') and hasattr(ctrl_widget._c, 'prog_mgr') and ctrl_widget._c.prog_mgr else None
            )

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
        self.region_editor.windowChanged.connect(self._on_window_changed)        
        
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

        # Flags para evitar loops infinitos de sinais
        self._updating_tree_selection = False
        self._updating_scene_selection = False
        self._scene_selection_blocked = False
        # NOVO SISTEMA: Armazena janelas de comparação nos dados dos componentes
        # Exatamente como no gerador de projetos
        self.inspecao_items = {}  # {nome_componente: [items]}

        # Inicializa dicionário de componentes (essencial!)
        self.componentes = {}
        # Flags de controle
        self._criando_item = False

        # Configuração da TreeView para permitir seleção individual
        self.tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        

        # ------------ NOVA SINCRONIZAÇÃO com ROIWindowEditor ------------
        self.view_region.scene().selectionChanged.connect(self._on_position_selection_changed)
        self.tree.itemSelectionChanged.connect(self._on_tree_selection_changed) 
        self.tree.itemClicked.connect(self._on_tree_item_clicked)
        
        # EVENT-FILTER para logs de clique
        self.view_region.viewport().installEventFilter(self)
        if self.view_roi:
            self.view_roi.viewport().installEventFilter(self)
            self.roi_editor.windowAdded.connect(self._on_comparison_window_added)
            self.roi_editor.windowRemoved.connect(self._on_comparison_window_removed)
        # Variável para guardar o pai das janelas de comparação
        self._comparison_parent_uid = None

        # NOVO: Carrega dados do cache ao inicializar
        self.load_cached_data()
    
    def _update_mechanical_positions_in_cache(self):
        """Atualiza as coordenadas das posições mecânicas no cache com as posições atuais"""
        for window in self.region_editor.windows:
            if isinstance(window, ResizableRectItem):
                window_name = getattr(window, 'name', None)
                if window_name and window_name in self.componentes:
                    # CORREÇÃO: Captura posição atual da janela no editor
                    pos_rect = window.sceneBoundingRect()
                    atual_x = int(pos_rect.x())
                    atual_y = int(pos_rect.y())
                    atual_w = int(pos_rect.width())
                    atual_h = int(pos_rect.height())
                    
                    # Atualiza no cache
                    self.componentes[window_name]['posicao'] = (atual_x, atual_y)
                    self.componentes[window_name]['dimensoes'] = (atual_w, atual_h)
                    
                    self.log(f"🔧 Posição '{window_name}' atualizada no cache: pos=({atual_x},{atual_y}), dims=({atual_w},{atual_h})")
 
    def _on_window_changed(self, item):
        """Callback chamado quando janela é modificada - salva automaticamente"""
        # CORREÇÃO: Atualiza dados no cache se for posição mecânica
        if isinstance(item, ResizableRectItem):
            window_name = getattr(item, 'name', None)
            if window_name and window_name in self.componentes:
                pos_rect = item.sceneBoundingRect()
                self.componentes[window_name]['posicao'] = (int(pos_rect.x()), int(pos_rect.y()))
                self.componentes[window_name]['dimensoes'] = (int(pos_rect.width()), int(pos_rect.height()))
                self.log(f"🔄 Posição mecânica '{window_name}' atualizada em tempo real: pos={self.componentes[window_name]['posicao']}, dims={self.componentes[window_name]['dimensoes']}")
        
        self.log(f"🔄 Janela modificada: {self._describe_item(item)}")

    # ------------ helpers internos ----------------------------------
    def _update_pix(self):
        """Escala novamente a partir da imagem original (evita cascata)."""
        if self._orig_pix.isNull():
            return
        if not self._orig_pix.isNull():
            self._pix_item.setPixmap(self._orig_pix)
            self.view_region.fitInView(self._pix_item,
                                       Qt.AspectRatioMode.KeepAspectRatio)            
    
    def _get_selected_mechanical_position_node(self):
        """Retorna o nó da posição mecânica atualmente selecionado na tree"""
        selected_items = self.tree.selectedItems()
        if not selected_items:
            return None
        
        return selected_items[0] if selected_items else None
    def _on_position_selection_changed(self):
        """
        Chamado quando seleção muda no visor de posições mecânicas.
        
        """
        selected_items = self.view_region.scene().selectedItems()
        if not selected_items:
            # Nenhuma seleção - mostra todas as janelas de comparação
            if self.roi_editor:
                self.roi_editor.focus_on_parent(None)
            return
        
        # Pega primeiro item selecionado (posição mecânica)
        selected_item = selected_items[0]
        if isinstance(selected_item, ResizableRectItem):
            # Foca nas janelas filhas desta posição mecânica
            # Atualiza ROI e redesenha janelas
            
            # Atualiza ROI visual
            self._update_roi_from_selection()
            
            # Seleciona na TreeView
            self._select_tree_node_for_item(selected_item)
            
            self.log(f"🎯 Posição selecionada: {getattr(selected_item, 'name', '?')}")
    
    def _update_roi_from_selection(self):
        """
        Recorta a área da Posição Mecânica selecionada e mostra
        na view_roi preservando a resolução original.
        """
        if self.view_roi is None or self._orig_bgr is None:
            return        
        sel = [it for it in self.view_region.scene().selectedItems()
               if isinstance(it, ResizableRectItem)]
        if not sel:
            return
        
        # CORREÇÃO: Evita redesenho desnecessário
        item = sel[0]
        component_name = getattr(item, 'name', None)
        if not component_name:
            return
            
        # Verifica se mudou a seleção para evitar redesenhos repetitivos
        if hasattr(self, '_last_selected_component') and self._last_selected_component == component_name:
            return
        self._last_selected_component = component_name
        
        # ... resto da função mantém igual ...
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
        
        # Atualiza o visor ROI
        roi_px = InspectionConfigWidget._bgr_to_pixmap(roi_bgr)  # qualidade máx.

        # CORREÇÃO: Remove apenas o pixmap anterior, mantém janelas de comparação
        scene = self.view_roi.scene()
        # Remove apenas o item de imagem anterior (se existir)
        if hasattr(self, '_roi_pix_item') and self._roi_pix_item:
            scene.removeItem(self._roi_pix_item)
        
        # Adiciona nova imagem
        self._roi_pix_item = scene.addPixmap(roi_px)
        self.view_roi.fitInView(self._roi_pix_item,
                                Qt.AspectRatioMode.KeepAspectRatio)
        
        # FORÇO redesenho se necessário
        if component_name and component_name in self.componentes:
            self._redesenhar_janelas_inspecao(component_name)
            
    # ===================  TREEVIEW Sync  ============================
    def _on_window_added(self, item):
        """Insere posição mecânica na árvore"""
        name = getattr(item, 'name', f'Posição {item.id}' if hasattr(item, 'id') else 'Posição mecânica')
        node = QTreeWidgetItem([name])
        node.setData(0, Qt.ItemDataRole.UserRole, item)
        self.tree.addTopLevelItem(node)
        self.log(f"➕ Posição mecânica adicionada à tree: {name}")

    def _on_comparison_window_added(self, roi_item):
        """
        NOVA ABORDAGEM: Converte janela do ROIWindowEditor em dados do componente
        e redesenha usando o sistema do gerador de projetos
        """
        # Identifica a posição mecânica pai
        parent_item = None
        if self._comparison_parent_uid is not None:
            for window in self.region_editor.windows:
                if hasattr(window, 'id') and window.id == self._comparison_parent_uid:
                    parent_item = window
                    break
        
        if parent_item is None:
            # Fallback: usa posição selecionada
            selected_items = self.view_region.scene().selectedItems()
            for scene_item in selected_items:
                if isinstance(scene_item, ResizableRectItem) and scene_item in self.region_editor.windows:
                    parent_item = scene_item
                    break
        
        if parent_item is None:
            self.log("⚠️ Janela de comparação criada sem pai definido")
            return        
            
        # Encontra nó pai na TreeView
        parent_node = None
        parent_name = getattr(parent_item, 'name', f'ID:{parent_item.id}')
        for i in range(self.tree.topLevelItemCount()):
            node = self.tree.topLevelItem(i)
            if node.data(0, Qt.ItemDataRole.UserRole) is parent_item:
                parent_node = node
                parent_name = node.text(0)
                break
                
        if parent_node is None:
            self.log("⚠️ Nó pai não encontrado na TreeView")
            return
        
        # NOVA LÓGICA: Converte para dados do componente (como no gerador)
        # Obtém coordenadas da janela ROI em relação à ROI original
        roi_rect = roi_item.rect()
            
        # Converte coordenadas da cena ROI para coordenadas absolutas da ROI
        if parent_name not in self.componentes:
            # Inicializa dados do componente se não existir
            pos_rect = parent_item.sceneBoundingRect()
            self.componentes[parent_name] = {
                'posicao': (int(pos_rect.x()), int(pos_rect.y())),
                'dimensoes': (int(pos_rect.width()), int(pos_rect.height())),
               'roi': None,  # será preenchido quando necessário
                'inspecoes': []
            }
        
        # Calcula coordenadas absolutas (simula o sistema do gerador)
        scene_rect = self.view_roi.sceneRect()
        # Para simplicidade, assume que a cena ROI tem o mesmo tamanho da ROI
        roi_w, roi_h = scene_rect.width(), scene_rect.height()
        
        if roi_w > 0 and roi_h > 0:
            # Coordenadas absolutas na ROI original
            x_orig = int(roi_rect.x())
            y_orig = int(roi_rect.y())
            w_orig = int(roi_rect.width())
            h_orig = int(roi_rect.height())
        else:
            x_orig, y_orig, w_orig, h_orig = int(roi_rect.x()), int(roi_rect.y()), int(roi_rect.width()), int(roi_rect.height())
        
        # Conta janelas existentes para gerar nome
        existing_count = len(self.componentes[parent_name]['inspecoes'])
        comp_name = f"w{existing_count + 1}"
        
        # Salva referência bidirecional
        inspecao_data = {
            'posicao': (x_orig, y_orig),
            'tamanho': (w_orig, h_orig),
            'threshold': 100,  # valor padrão
            'cor_pixel': 'branco',
            'percentual_minimo': 50.0,
            'roi_editor_item': roi_item,  # referência para sincronização
            'tree_node': None,            # será preenchido abaixo
            'blue_window': None           # será preenchido no redesenho
        }
        
        self.componentes[parent_name]['inspecoes'].append(inspecao_data)

        # CORREÇÃO: Remove janela vermelha do ROIWindowEditor após salvar dados
        if roi_item in self.roi_editor.windows:
            self.roi_editor.windows.remove(roi_item)
            if roi_item.scene():
                roi_item.scene().removeItem(roi_item)
            
        # FORÇA redesenho imediato para mostrar janela azul
        self._redesenhar_janelas_inspecao(parent_name)

        # DEBUGGING: Log detalhado da associação
        self.log(f"🔗 Dados salvos {comp_name} → pai {parent_name}")
        # Cria subnó na TreeView
        comp_node = QTreeWidgetItem([comp_name])
        # CORREÇÃO CRÍTICA: Associa imediatamente a um placeholder que será substituído
        placeholder_data = {
            'type': 'comparison_placeholder',
            'component_name': parent_name,
            'window_name': comp_name,
            'inspecao_ref': inspecao_data
        }
        comp_node.setData(0, Qt.ItemDataRole.UserRole, placeholder_data)

        # Log detalhado da associação
        self.log(f"🔗 Criando nó TreeView '{comp_name}' com placeholder")

        # Salva referência bidirecional
        inspecao_data['tree_node'] = comp_node
        parent_node.addChild(comp_node)
        parent_node.setExpanded(True)

        # NOVO: Força atualização visual da TreeView
        self.tree.update()
        self.tree.repaint()
        
        # NOVO: Torna o item explicitamente selecionável
        comp_node.setFlags(
            comp_node.flags() | 
            Qt.ItemFlag.ItemIsSelectable | 
            Qt.ItemFlag.ItemIsEnabled
        )

        
        
        self.log(f"➕ Janela de comparação adicionada: {comp_name}")

        # Limpa referência do pai após usar
        self._comparison_parent_uid = None

    def _select_tree_node_for_item(self, item):
        """Seleciona o nó da TreeView correspondente ao item"""
        for i in range(self.tree.topLevelItemCount()):
            node = self.tree.topLevelItem(i)
            if node.data(0, Qt.ItemDataRole.UserRole) is item:
                self.tree.setCurrentItem(node)
                return
    
    def log(self, message):
        """Helper para logging (usa o log do controller se disponível)"""
        if hasattr(self, '_c') and hasattr(self._c, 'log'):
            self._c.log(message)
        elif hasattr(self, 'parent') and hasattr(self.parent(), 'log'):
            self.parent().log(message)
        else:
            print(f"[AuxDialog] {message}")

    
    # ================================================================
    #  NOVO SISTEMA: CARREGAMENTO E TRANSFERÊNCIA DE DADOS
    # ================================================================
    
    def load_cached_data(self):
        """Carrega dados do cache do widget principal"""
        if not hasattr(self._main_widget, 'get_cached_auxiliary_data'):
           self.log("Widget principal não suporta cache")
           return
            
        cached_data = self._main_widget.get_cached_auxiliary_data()
        componentes_cache = cached_data.get('componentes', {})

        # DEBUGGING DETALHADO das coordenadas
        if not hasattr(self, 'componentes'):
            self.componentes = {}
            self.log("⚠️ Dicionário componentes não existia - inicializado")
            
        if not hasattr(self, 'region_editor') or self.region_editor is None:
            self.log("❌ region_editor não disponível - cancelando reconstrução")
            return
        self.log(f"📂 Tentando carregar cache: {len(componentes_cache)} componentes disponíveis")
        for nome, dados in componentes_cache.items():
            pos = dados.get('posicao', (0, 0))
            dims = dados.get('dimensoes', (100, 100))
            inspecoes = dados.get('inspecoes', [])
            self.log(f"📂 Cache '{nome}': pos={pos}, dims={dims}, {len(inspecoes)} inspeções")
            
            # ALERTA se posição for (0,0)
            if pos == (0, 0) and dims == (100, 100):
                self.log(f"⚠️ POSIÇÃO SUSPEITA para '{nome}': pode estar em posição padrão")

        # DEBUGGING: Mostra estado do widget principal
        self.log(f"📂 Widget principal - inicializando auxiliar: {getattr(self._main_widget, '_initializing_auxiliary', 'N/A')}")
        
        # NOVO: Se está inicializando e não tem dados, aguarda um pouco
        if not componentes_cache and hasattr(self._main_widget, '_initializing_auxiliary'):
            self.log("⏳ Aguardando inicialização completa...")
            QTimer.singleShot(100, self.load_cached_data)  # Tenta novamente em 100ms
            return

        # DEBUGGING: Log detalhado do que está sendo carregado
        self.log(f"📂 Tentando carregar cache: {len(componentes_cache)} componentes disponíveis")
        for nome, dados in componentes_cache.items():
            pos = dados.get('posicao', (0, 0))
            dims = dados.get('dimensoes', (100, 100))
            inspecoes = dados.get('inspecoes', [])
            self.log(f"📂 Cache '{nome}': pos={pos}, dims={dims}, {len(inspecoes)} inspeções")
       
        if not componentes_cache:
            self.log("Nenhum dado em cache para carregar")
            return
            
        # Carrega componentes do cache
        self.componentes.update(componentes_cache)
        self.log(f"📂 Carregados {len(componentes_cache)} componentes do cache")
        self.log(f"📂 Total de componentes após carregar: {len(self.componentes)}")
        
        # Reconstroi a interface baseada nos dados carregados
        self.rebuild_interface_from_cache()
        
    def rebuild_interface_from_cache(self):
        """Reconstroi TreeView e editores baseado nos componentes em cache"""
        # Limpa TreeView atual
        self.tree.clear()
        # CORREÇÃO: Limpa editor antes de recriar
        if hasattr(self.region_editor, 'windows'):
            for window in list(self.region_editor.windows):
                try:
                    if window.scene():
                        window.scene().removeItem(window)
                except RuntimeError:
                    pass
            self.region_editor.windows.clear()
        
        # Adiciona posições mecânicas ao region_editor e TreeView
        for comp_name, comp_data in self.componentes.items():
            pos = comp_data.get('posicao', (0, 0))
            dims = comp_data.get('dimensoes', (100, 100))
            
            self.log(f"📂 Recriando '{comp_name}': pos={pos}, dims={dims}")
            
            # CORREÇÃO CRÍTICA: Cria o item no region_editor usando coordenadas do cache
            item = self.region_editor.add_window(
                x=pos[0], y=pos[1], 
                w=dims[0], h=dims[1],
                name=comp_name, 
                deletable=True,
                editable=False
            )                 
            
            # Adiciona à TreeView
            node = QTreeWidgetItem([comp_name])
            node.setData(0, Qt.ItemDataRole.UserRole, item)
            self.tree.addTopLevelItem(node)
            # Adiciona janelas de inspeção como subnós
            for i, inspecao in enumerate(comp_data.get('inspecoes', []), 1):
                comp_node = QTreeWidgetItem([f"w{i}"])
                
                # Cria placeholder para a janela de comparação
                placeholder_data = {
                    'type': 'comparison_placeholder',
                    'component_name': comp_name,
                    'window_name': f"w{i}",
                    'inspecao_ref': inspecao
                }
                comp_node.setData(0, Qt.ItemDataRole.UserRole, placeholder_data)
                inspecao['tree_node'] = comp_node
                node.addChild(comp_node)
                node.setExpanded(True)
            
            self.log(f"🔄 Posição '{comp_name}' restaurada com {len(comp_data.get('inspecoes', []))} janelas")
                        
    def closeEvent(self, event):
        """Atualiza posições e chama callback direto"""
        try:
            # Atualiza posições mecânicas no cache
            self._update_mechanical_positions_in_cache()
            
            # Chama callback direto se disponível
            if self._update_callback:
                self._update_callback(self.componentes, self._orig_bgr)
                print(f"[DEBUG] ✅ Callback direto executado com sucesso")
            
        except Exception as e:
            print(f"[ERROR] Erro no closeEvent: {e}")
        super().closeEvent(event)        

# ======================================================================
#  EVENT-FILTER  (cliques nos visores)  +  logs auxiliares
# ======================================================================
    def eventFilter(self, obj, ev):
        from PyQt6.QtCore import QEvent
        if ev.type() == QEvent.Type.MouseButtonPress:
            if obj is self.view_region.viewport():
                pos = self.view_region.mapToScene(int(ev.position().x()),
                                                  int(ev.position().y()))
                it  = self.view_region.scene().itemAt(pos, self.view_region.transform())
                self._log_click("vis. ESQ", it, pos)
            elif self.view_roi and obj is self.view_roi.viewport():
                pos = self.view_roi.mapToScene(int(ev.position().x()),
                                               int(ev.position().y()))
                it  = self.view_roi.scene().itemAt(pos, self.view_roi.transform())
                self._log_click("vis. DIR", it, pos)
                # NOVA FUNCIONALIDADE: Detecta clique em janela azul para sincronizar TreeView
                if (hasattr(it, 'item_type') and it.item_type == 'inspection'):
                    self._handle_blue_window_click(it)
                    # NOVO: Força seleção visual da janela clicada
                    try:
                        self.view_roi.scene().clearSelection()
                        it.setSelected(True)
                        self.view_roi.scene().update()
                        self.view_roi.viewport().update()
                    except RuntimeError:
                        self.log("⚠️ Erro ao selecionar janela azul clicada")
                        pass
        return super().eventFilter(obj, ev)
    
    def _handle_blue_window_click(self, blue_window):
        """Manipula clique em janela azul para sincronizar com TreeView"""
        self.log(f"🖱️ Clique na janela azul: {getattr(blue_window, 'inspecao_name', '?')}")

        # NOVO: Força seleção visual imediata
        try:
            self.view_roi.scene().clearSelection()
            blue_window.setSelected(True)
            self.view_roi.scene().update()
            self.view_roi.viewport().update()
        except RuntimeError:
            self.log("⚠️ Erro ao selecionar janela azul clicada")
            pass
        
        # Encontra o nó correspondente na TreeView
        tree_node = getattr(blue_window, 'tree_node', None)
        if tree_node:
            # Evita loops infinitos
            self._updating_tree_selection = True
            try:
                self.tree.setCurrentItem(tree_node)
                # NOVO: Força expansão do nó pai para visibilidade
                if tree_node.parent():
                    tree_node.parent().setExpanded(True)
                self.log(f"✅ TreeView sincronizada: {tree_node.text(0)} selecionado")
                
                # Também garante que a posição mecânica pai seja selecionada
                self._sync_parent_selection_from_comparison(blue_window)
                
            finally:
                self._updating_tree_selection = False
        else:
            self.log("⚠️ Nó da TreeView não encontrado para janela azul")
    
    def _sync_parent_selection_from_comparison(self, blue_window):
        """Garante que a posição mecânica pai seja selecionada quando janela azul é clicada"""
        # Usa método centralizado
        self._ensure_parent_position_selected(blue_window)

    # ------------------------  helpers interno ------------------------
    def _describe_item(self, it) -> str:
        if it is None:
            return "área vazia"
        if hasattr(it, "comparison_name"):
            return f"Cmp “{it.comparison_name}”"
        if isinstance(it, ResizableRectItem):
            nm = getattr(it, "name", "")
            return f"Posição “{nm or '?'}”"
        return str(it)

    def _log_click(self, visor, item, pos):
        desc = self._describe_item(item)
        self.log(f"🖱️ Click {visor}: {desc}  @({pos.x():.0f},{pos.y():.0f})")

    # ------------------------------------------------------------------
    #           LOG para clique na TREEVIEW
    # ------------------------------------------------------------------
    def _on_tree_item_clicked(self, item: QTreeWidgetItem, col: int):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(data, dict) and data.get('type') == 'comparison_placeholder':
            kind = f"Placeholder w* ({data.get('window_name')})"
        elif hasattr(data, 'item_type') and data.item_type == 'inspection':
            kind = f"Janela azul ({getattr(data, 'inspecao_name', '?')})"
        elif isinstance(data, ResizableRectItem):
            kind = "Posição mecânica"
        else:
            kind = f"Desconhecido ({type(data)})"
        self.log(f"🖱️ Click Tree → {kind}: {item.text(0)}")

    def _on_window_removed(self, item):
        """Remove posição mecânica da tree"""
        for i in range(self.tree.topLevelItemCount()):
            n = self.tree.topLevelItem(i)
            if n.data(0, Qt.ItemDataRole.UserRole) is item:                
                self.tree.takeTopLevelItem(i)
                self.log(f"➖ Posição mecânica removida da tree")
                return
    def _on_comparison_window_removed(self, item):
        """Remove janela de comparação da tree"""
        # Remove subitens (janelas de comparação)
        for i in range(self.tree.topLevelItemCount()):
            parent_node = self.tree.topLevelItem(i)
            # Procura subitens que correspondam ao item
            for j in range(parent_node.childCount()):
                child_node = parent_node.child(j)
                if child_node.data(0, Qt.ItemDataRole.UserRole) is item:
                    parent_node.removeChild(child_node)
                    self.log(f"➖ Janela de comparação removida da tree")
                    return
    
    def _is_item_valid(self, item):
        """Verifica se um item Qt ainda é válido"""
        if item is None:
            return False
        try:
            # Tenta acessar uma propriedade básica - se falhar, objeto foi deletado
            _ = item.scene()
            return True
        except RuntimeError:
            # Objeto C++ foi deletado
            return False
        
    def _find_and_select_tree_node(self, item):
        """Encontra e seleciona o nó correspondente na TreeView"""
        if not self._is_item_valid(item):
            return
            
        # Procura em itens de primeiro nível
        for i in range(self.tree.topLevelItemCount()):
            n = self.tree.topLevelItem(i)
            if n and n.data(0, Qt.ItemDataRole.UserRole) is item:
                self.tree.setCurrentItem(n)
                return
    
    def _safe_clear_tree_selection(self):
        """Limpa seleção da TreeView de forma segura"""
        try:
            self._updating_tree_selection = True
            self.tree.clearSelection()
        finally:
            self._updating_tree_selection = False
    
    def _safe_select_tree_node(self, node):
        """Seleciona nó na TreeView de forma segura"""
        if node is None:
            return
        try:
            self._updating_tree_selection = True
            if not node.isSelected():
                self.tree.setCurrentItem(node)
        finally:
            self._updating_tree_selection = False
    
    def _select_tree_node(self, node):
        """Helper para selecionar um nó na tree"""
        self._safe_select_tree_node(node)
                    

    def _on_tree_selection_changed(self):
        """Seleciona retângulo na cena ao clicar na tree"""
        # Evita loops infinitos
        if self._updating_tree_selection:
            return
        nodes = self.tree.selectedItems()
        if not nodes:
            # Limpa seleção das cenas de forma segura
            try:
                self.view_region.scene().clearSelection()
                if self.view_roi:
                    self.view_roi.scene().clearSelection()
            except RuntimeError:
                pass
            # Mostra todas as janelas
            if self.roi_editor:
                self.roi_editor.focus_on_parent(None)
            return
        node = nodes[0]
        item = node.data(0, Qt.ItemDataRole.UserRole)

        if item is None:
            return
            
        # CORREÇÃO: Distingue entre posição mecânica e janela de comparação
        is_mechanical_position = False
        is_comparison_window = False
        comparison_placeholder = False
        
        if isinstance(item, ResizableRectItem):
            # Verifica se é posição mecânica (está na cena esquerda)
            if item in self.region_editor.windows:
                is_mechanical_position = True
        elif isinstance(item, dict) and item.get('type') == 'comparison_placeholder':
            # NOVO: Placeholder para janelas de comparação (antes do redesenho)
            comparison_placeholder = True
            self.log(f"🔍 Detectado placeholder para: {item.get('window_name')}")
        elif hasattr(item, 'item_type') and item.item_type == 'inspection':
            # Janela azul já redesenhada
            is_comparison_window = True
        
        # NOVA LÓGICA: Trata placeholder como janela de comparação
        if comparison_placeholder:
            # CORREÇÃO: Converte placeholder MAS MANTÉM seleção no item w*
            self._handle_comparison_placeholder_selection(node, item, keep_selection=True)
            return
            # CORREÇÃO: Janela azul de comparação (SelectableResizableRectItem)
            is_comparison_window = True
        elif isinstance(item, ResizableRectItem) and hasattr(item, 'parent_uid'):
            is_comparison_window = True            
        
        if is_mechanical_position:
            # Seleciona na cena principal
            try:
                self.view_region.scene().clearSelection()
            except RuntimeError:
                pass
            item.setSelected(True)
            self.view_region.centerOn(item)
            
            # SEMPRE chama redesenho, mesmo se componente não tem janelas
            if self.roi_editor:
                # Mostra todas as janelas, não apenas as filhas
                self.roi_editor.focus_on_parent(None)
                
            # Atualiza ROI visual  
            self._update_roi_from_selection()
            
            self.log(f"🏭 Seleção tree → posição: {node.text(0)}")

        elif is_comparison_window:
            # NOVO: Selecionou janela de comparação (w*) - sincronização completa
            self.log(f"🎯 Seleção tree → janela comparação: {node.text(0)}")

            # 1. CRÍTICO: Seleciona a janela azul no visor direito e centraliza
            try:
                if self.view_roi:
                    self.view_roi.scene().clearSelection()
                    item.setSelected(True)
                    self.view_roi.centerOn(item)
                    # Força atualização visual da seleção
                    self.view_roi.scene().update()
                    self.view_roi.viewport().update()
                    self.log(f"✅ Janela azul selecionada e centralizada")
            except RuntimeError:
                self.log("⚠️ Erro ao selecionar janela azul")
            
            # 2. Garante que posição mecânica pai seja selecionada no visor esquerdo
            self._ensure_parent_position_selected(item)
                                    
        else:
            self.log(f"⚠️ Tipo de item desconhecido selecionado: {type(item)}")
    def _ensure_parent_position_selected(self, comparison_item):
        """Garante que a posição mecânica pai esteja selecionada no visor esquerdo"""
        component_name = getattr(comparison_item, 'componente', None)
        if not component_name:
            return
            
        # Encontra a posição mecânica pai
        for window in self.region_editor.windows:
            if getattr(window, 'name', None) == component_name:
                try:
                    # Seleciona no visor esquerdo apenas se necessário
                    current_selection = self.view_region.scene().selectedItems()
                    if not current_selection or current_selection[0] != window:
                        self.view_region.scene().clearSelection()
                        window.setSelected(True)
                        self.view_region.centerOn(window)
                        # Força atualização do ROI
                        self._update_roi_from_selection()
                        self.log(f"✅ Posição pai '{component_name}' selecionada automaticamente")
                    break
                except RuntimeError:
                    self.log("⚠️ Erro ao selecionar posição mecânica pai")
                    break

    def _handle_comparison_placeholder_selection(self, node, placeholder_data, keep_selection=False):
        """Manipula seleção de placeholder de janela de comparação"""
        component_name = placeholder_data.get('component_name')
        window_name = placeholder_data.get('window_name')
        
        self.log(f"🎯 Seleção tree → janela comparação: {window_name} (via placeholder)")
        
        # 1. Força redesenho para criar as janelas azuis se necessário
        if component_name and component_name in self.componentes:
            self._redesenhar_janelas_inspecao(component_name)
            
        # 2. Encontra a janela azul correspondente após redesenho
        target_window = None
        if component_name in self.inspecao_items:
            for blue_window in self.inspecao_items[component_name]:
                if hasattr(blue_window, 'inspecao_name') and blue_window.inspecao_name == window_name:
                    target_window = blue_window
                    break
        
        # 3. CRÍTICO: Seleciona e centraliza a janela azul com feedback visual
        if target_window:
            try:
                if self.view_roi:
                    self.view_roi.scene().clearSelection()
                    target_window.setSelected(True)
                    self.view_roi.centerOn(target_window)
                    # NOVO: Força feedback visual da seleção
                    self.view_roi.scene().update()
                    self.view_roi.viewport().update()
                    self.log(f"✅ Janela azul {window_name} selecionada via placeholder")
            except RuntimeError:
                self.log("⚠️ Erro ao selecionar janela azul via placeholder")
        
        # 4. Garante posição pai selecionada
        if target_window:
            self._ensure_parent_position_selected(target_window)
            
            # NOVO: Se keep_selection=True, volta seleção TreeView para o item w*
            if keep_selection:
                QTimer.singleShot(100, lambda: self._force_tree_selection(node))
                
    def _force_tree_selection(self, node):
        """Força seleção de um nó específico na TreeView"""
        try:
            self._updating_tree_selection = True
            self.tree.setCurrentItem(node)
            self.log(f"🔄 TreeView forçada para: {node.text(0)}")
        finally:
            self._updating_tree_selection = False
    
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
        
        # Atualiza o visor ROI

        roi_px = InspectionConfigWidget._bgr_to_pixmap(roi_bgr)  # qualidade máx.

        # CORREÇÃO: Remove apenas o pixmap anterior, mantém janelas de comparação
        scene = self.view_roi.scene()
        # Remove apenas o item de imagem anterior (se existir)
        if hasattr(self, '_roi_pix_item') and self._roi_pix_item:
            scene.removeItem(self._roi_pix_item)
        
        # Adiciona nova imagem
        self._roi_pix_item = scene.addPixmap(roi_px)
        self.view_roi.fitInView(self._roi_pix_item,
                                Qt.AspectRatioMode.KeepAspectRatio)
        # CORREÇÃO: Mantém todas as janelas sempre visíveis
        if self.roi_editor and isinstance(item, ResizableRectItem):
            # Encontra o nome do componente
            component_name = getattr(item, 'name', None)
            # DEBUGGING: Log da operação
            self.log(f"🔄 Atualizando ROI para componente: {component_name}")
            # FORÇA redesenho mesmo se componente não tem janelas (para limpar cena)
            if component_name:
                # Garante que componente existe no dicionário
                if component_name not in self.componentes:
                    self.componentes[component_name] = {
                        'posicao': (0, 0),
                        'dimensoes': (100, 100),
                        'roi': None,
                        'inspecoes': []  # Lista vazia
                    }
                inspecoes_count = len(self.componentes[component_name].get('inspecoes', []))
                self.log(f"📊 Componente {component_name} tem {inspecoes_count} janelas salvas")
                # SEMPRE chama redesenho (vai limpar cena se não há janelas)
                self._redesenhar_janelas_inspecao(component_name)

    def _redesenhar_janelas_inspecao(self, componente):
        """
        NOVA IMPLEMENTAÇÃO: Identica ao gerador de projetos
        Redesenha todas as janelas de comparação para o componente especificado
        """
        
        # Verifica se componentes foi inicializado
        if not hasattr(self, 'componentes'):
            self.componentes = {}
            
            return
        if componente not in self.componentes:
            return
        
        # DEBUGGING: Log do componente sendo redesenhado
        inspecoes_count = len(self.componentes[componente].get('inspecoes', []))
        self.log(f"🔄 Iniciando redesenho para '{componente}' ({inspecoes_count} janelas)")
            
        if not self.view_roi or not self.view_roi.scene():
            self.log(f"⚠️ Não foi possível redesenhar - visor ROI não disponível")
            return
        
            
        scene = self.view_roi.scene()
        
        # CORREÇÃO: Remove TODAS as janelas de inspeção da cena (de todos os componentes)
        # Isso garante que apenas as janelas do componente atual sejam exibidas
        for comp_name in list(self.inspecao_items.keys()):
            for item in self.inspecao_items[comp_name]:
                if item.scene():
                    scene.removeItem(item)
            self.inspecao_items[comp_name] = []

        self.log(f"🧹 Cena ROI limpa - todas as janelas antigas removidas")
        
        # Garante que o componente atual existe no dicionário  
        if componente not in self.inspecao_items:
            self.inspecao_items[componente] = []
        
        # Obtém dimensões da cena para escala
        scene_rect = scene.sceneRect()
        scene_width = scene_rect.width()
        scene_height = scene_rect.height()
        
        if scene_width == 0 or scene_height == 0:
            return
        
        # Redesenha cada janela de inspeção salva
        # Usa apenas cor azul para todas as janelas de comparação
        cor_azul = Qt.GlobalColor.blue

        for i, inspecao in enumerate(self.componentes[componente].get('inspecoes', [])):
            # CORREÇÃO CRÍTICA: Usa coordenadas ATUAIS (que incluem modificações do usuário)
            x_orig, y_orig = inspecao['posicao']
            w_orig, h_orig = inspecao['tamanho']

            # DEBUGGING: Log das coordenadas que serão usadas
            self.log(f"🔧 Redesenhando w{i+1}: pos=({x_orig},{y_orig}), tam=({w_orig},{h_orig})")

            # Para simplicidade, usa coordenadas diretas (pode ser ajustado se necessário)
            # No gerador original, há conversão de escala aqui
            graphicsView_x = x_orig
            graphicsView_y = y_orig
            graphicsView_w = w_orig
            graphicsView_h = h_orig

            # CORREÇÃO CRÍTICA: Callback que salva alterações do usuário
            def _on_insp_change(item, d=inspecao, comp=componente):
                """Atualiza dados quando item é modificado"""
                # CORREÇÃO: Permite salvar alterações do usuário mesmo durante redesenho
                # Só bloqueia durante a criação inicial do item
                if hasattr(self, '_criando_item') and self._criando_item:
                    return
                br = item.sceneBoundingRect()
                # CORREÇÃO CRÍTICA: Atualiza coordenadas principais (que são usadas no redesenho)
                new_pos = (int(br.x()), int(br.y()))
                new_tam = (int(br.width()), int(br.height()))
                d['posicao'] = new_pos
                d['tamanho'] = new_tam
                # NOVO: Também atualiza originais para manter consistência
                d['original_posicao'] = new_pos
                d['original_tamanho'] = new_tam
                self.log(f"🔄 Janela {comp} atualizada: pos={d['posicao']}, tam={d['tamanho']}")
            # Marca que está criando item (evita callback durante criação)
            self._criando_item = True

            # Cria item visual
            
            rect_item = SelectableResizableRectItem(
                graphicsView_x, graphicsView_y,
                graphicsView_w, graphicsView_h,
                pen=QPen(cor_azul, 2),
                change_callback=_on_insp_change
            )

            # Item criado - libera callbacks
            self._criando_item = False

            # Metadados para identificação
            rect_item.item_type = 'inspection'
            rect_item.componente = componente
            rect_item.inspecao_ref = inspecao
            rect_item.deletavel = True

            # NOVO: Estabelece associação bidirecional TreeView ↔ Janela Azul
            inspecao['blue_window'] = rect_item
            if inspecao.get('tree_node'):
                # CORREÇÃO: Substitui placeholder pela janela azul real
                inspecao['tree_node'].setData(0, Qt.ItemDataRole.UserRole, rect_item)
                self.log(f"🔗 Nó '{inspecao['tree_node'].text(0)}' associado à janela azul (substitui placeholder)")
                # CRÍTICO: Associação bidirecional completa
                rect_item.tree_node = inspecao['tree_node']
                rect_item.inspecao_name = f"w{i+1}"

                rect_item.component_name = componente

                # NOVO: Metadados extras para debugging
                rect_item.original_inspecao_data = inspecao                                
                
                # DEBUGGING: Confirma associação bidirecional
                self.log(f"🔗 Associação bidirecional completa: TreeView({inspecao['tree_node'].text(0)}) ↔ Janela({rect_item.inspecao_name})")
            
            scene.addItem(rect_item)
            self.inspecao_items[componente].append(rect_item)

        # Força atualização da visualização
        self.view_roi.viewport().update()

        # DEBUGGING: Log do resultado final
        total_items_scene = len([item for item in scene.items() 
                               if hasattr(item, 'item_type') and item.item_type == 'inspection'])
        self.log(f"🎯 Cena ROI agora tem {total_items_scene} janelas de inspeção visíveis")
        
        self.log(f"🔄 Redesenhadas {len(self.componentes[componente].get('inspecoes', []))} janelas para {componente}")    

    # ============== NOVO: SCENE EVENT FILTER PARA JANELAS AZUIS ==============
    def sceneEventFilter(self, watched, event):
        """Event filter específico para janelas azuis"""
        try:
            from PyQt6.QtCore import QEvent
            
            # Só processa cliques do mouse em janelas azuis
            if (hasattr(watched, 'item_type') and 
                watched.item_type == 'inspection' and
                event.type() == QEvent.Type.GraphicsSceneMousePress):
                
                self.log(f"🎯 Scene Event Filter: clique em {getattr(watched, 'inspecao_name', '?')}")
                
                # Chama handler específico
                self._handle_blue_window_click(watched)
                
                # Propaga o evento normalmente
                return False
                
        except Exception as e:
            self.log(f"⚠️ Erro no scene event filter: {e}")
            
        # Propaga evento para handlers normais
        return False

    # mantém proporção 4:3 na imagem grande
    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        self._fit_views()

    # NOVO MÉTODO: Remove janela dos dados do componente
    def _on_comparison_window_removed(self, roi_item):
        """Remove janela de comparação dos dados e da TreeView"""
        # Encontra o componente e remove a janela dos dados
        if not hasattr(self, 'componentes'):
            self.componentes = {}
            return
        # DEBUGGING: Log antes da busca
        self.log(f"🔍 Procurando janela removida entre {len(self.componentes)} componentes")

        removed = False
        for comp_name, comp_data in self.componentes.items():
            inspecoes = comp_data.get('inspecoes', [])
            for i, insp in enumerate(inspecoes):
                if insp.get('roi_editor_item') is roi_item:
                    # Remove dos dados
                    inspecoes.pop(i)
                    self.log(f"➖ Janela removida dos dados de {comp_name}")
                    # Redesenha as janelas restantes
                    self._redesenhar_janelas_inspecao(comp_name)
                    break
            if removed:
                break

        # Remove também janela do ROIWindowEditor se ainda estiver lá
        if roi_item in self.roi_editor.windows:
            self.roi_editor.windows.remove(roi_item)

        # Remove da TreeView
        for i in range(self.tree.topLevelItemCount()):
            parent_node = self.tree.topLevelItem(i)
            for j in range(parent_node.childCount()):
                child_node = parent_node.child(j)
                if child_node.data(0, Qt.ItemDataRole.UserRole) is roi_item:
                    parent_node.removeChild(child_node)
                    self.log(f"➖ Janela removida da TreeView")
                    return

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
                # Determina o item pai baseado na seleção atual
                parent_item = None
                parent_uid = None
                selected_items = self.view_region.scene().selectedItems()
                if selected_items:
                    for item in selected_items:
                        if isinstance(item, ResizableRectItem):
                            parent_item = item
                            parent_uid = item.id
                            break
                
                # Inicia desenho SEM pai Qt Graphics (evita problemas entre cenas)
                # Mas salva o parent_uid para associação lógica
                self._comparison_parent_uid = parent_uid
                # CORREÇÃO: Garante que desenho acontece APENAS no visor direito
                if self.roi_editor and self.view_roi:
                    # Define pen azul para ROIWindowEditor (evita janelas vermelhas)
                    from PyQt6.QtGui import QPen
                    blue_pen = QPen(Qt.GlobalColor.blue, 2)
                    # Força foco no visor direito antes de iniciar desenho
                    self.view_roi.setFocus()
                    self.roi_editor.start_drawing(pen=blue_pen)
                else:
                    self.log("⚠️ Visor direito não disponível para desenho")
                
                self.btn_mech.setChecked(False)
            else:
                self.roi_editor.stop_drawing()
                

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
        # Cache simples para dados da janela auxiliar
        self._cached_auxiliary_data = {
            'componentes': {},           # posições mecânicas + janelas
            'region_image': None         # imagem da região (BGR)
        }
        # Flag para controlar limpeza de cache durante inicialização
        self._initializing_auxiliary = False

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

        # ----------------------------------------------------------
        #  NOVO VISOR PRINCIPAL  (QGraphicsView  +  ROIWindowEditor)
        # ----------------------------------------------------------
        self.view_region = QGraphicsView()
        self.view_region.setRenderHints(
            QPainter.RenderHint.SmoothPixmapTransform |
            QPainter.RenderHint.Antialiasing
        )
        self.view_region.setSizePolicy(QSizePolicy.Policy.Expanding,
                                       QSizePolicy.Policy.Expanding)
        scene = QGraphicsScene(self.view_region)
        self.view_region.setScene(scene)
        # item que exibirá o QPixmap da região
        self._region_pix_item = scene.addPixmap(QPixmap())
        # editor que torna as janelas vermelhas clicáveis
        self.region_editor = ROIWindowEditor(self.view_region)

        # Mantém o mesmo nome (“lbl_region”) para compatibilidade externa
        self.lbl_region = self.view_region

        # --------------------------------------------------------------
        #  Sempre que o usuário selecionar uma Posição Mecânica
        #  no visor “Região”, recortamos a área correspondente
        #  e a exibimos no pequeno visor ‘ROI’ aqui do painel
        # --------------------------------------------------------------
        self.view_region.scene().selectionChanged.connect(
            self._update_roi_from_selection_main)

        if self._show_region:
            v.addWidget(self.view_region)
        else:
            self.view_region.setVisible(False)

        # garante 4:3 e largura ≤ 15 % da tela já na criação
        self._adjust_region_size()

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
        # Ajusta aspecto inicial do visor ROI
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

    # --------------------------------------------------------------
    #  NOVO: coloca imagem na cena principal
    # --------------------------------------------------------------
    def _set_main_pixmap(self, img_bgr):
        """Actualiza o QGraphicsPixmapItem da região principal."""
        if img_bgr is None:
            self._region_pix_item.setPixmap(QPixmap())
            return
        h, w = img_bgr.shape[:2]
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        qimg = QImage(img_rgb.data, w, h, 3 * w, QImage.Format.Format_RGB888)
        self._region_pix_item.setPixmap(QPixmap.fromImage(qimg))
        # mantém 4:3
        self.view_region.fitInView(self._region_pix_item,
                                   Qt.AspectRatioMode.KeepAspectRatio)
        
    # --------------------------------------------------------------
    #  AJUSTE 4:3  (imagem “Região”)  +  limite 15 % largura da tela
    # --------------------------------------------------------------
    def _adjust_region_size(self):
        """
        Mantém o visor 'Região' com proporção 4:3, limitando sua largura
        a, no máximo, 15 % da largura do monitor principal.
        """
        if not hasattr(self, "view_region"):
            return

        # Largura máxima baseada em 15 % da largura da tela
        scr   = QGuiApplication.primaryScreen()
        if scr is None:
            return
        max_w = int(scr.size().width() * 0.18)

        # Largura realmente disponível no layout da coluna
        col_w = max(10, self.width())
        tgt_w = min(col_w, max_w)
        tgt_h = int(tgt_w * 3 / 4)   # 4:3

        # Define dimensões fixas
        self.view_region.setFixedWidth(tgt_w)
        self.view_region.setFixedHeight(tgt_h)

        # Re-ajusta a imagem para caber
        if hasattr(self, "_region_pix_item") and self._region_pix_item:
            self.view_region.fitInView(self._region_pix_item,
                                       Qt.AspectRatioMode.KeepAspectRatio)

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
        self._set_main_pixmap(img_bgr)

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
        self._set_main_pixmap(roi)
        self.regionCaptured.emit(roi)
        # Limpa cache quando nova região é definida
        self.clear_auxiliary_cache()    

    def _show_pixmap(self, label: QLabel, img_bgr, *, draw_border=False):
        print(f"[DEBUG] === _SHOW_PIXMAP INICIADO ===")
        print(f"[DEBUG] Label: {label.objectName() if hasattr(label, 'objectName') else 'unnamed'}")
        print(f"[DEBUG] Imagem: {img_bgr.shape if img_bgr is not None else 'None'}")
        print(f"[DEBUG] Draw border: {draw_border}")
        if img_bgr is None: 
            print(f"[DEBUG] ❌ Imagem é None - abortando")
            return
        h,w,_ = img_bgr.shape
        print(f"[DEBUG] Dimensões da imagem: {w}x{h}")
        if draw_border:
            print(f"[DEBUG] Desenhando borda amarela...")
            img_bgr = cv2.rectangle(img_bgr.copy(), (0,0), (w-1,h-1),
                                    (0,255,255), 2)
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        print(f"[DEBUG] Imagem convertida para RGB")
        from PyQt6.QtGui import QImage, QPixmap
        qimg = QImage(img_rgb.data, w, h, 3*w, QImage.Format.Format_RGB888)
        print(f"[DEBUG] QImage criada: {qimg.width()}x{qimg.height()}")
        px = QPixmap.fromImage(qimg).scaled(
            label.width(), label.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation)
        print(f"[DEBUG] QPixmap escalado para: {px.width()}x{px.height()}")
        print(f"[DEBUG] Label size: {label.width()}x{label.height()}")

        label.setPixmap(px)
        print(f"[DEBUG] ✅ Pixmap definido no label")
        
        # NOVO: Força atualização visual
        label.update()
        label.repaint()
        print(f"[DEBUG] ✅ Update e repaint forçados")

    def _open_aux(self):
        # NOVA ABORDAGEM: Callback direto
        def update_callback(componentes, region_image):
            """Callback que é chamado diretamente quando auxiliar fecha"""
            print(f"[DEBUG] 🔄 Callback direto recebido: {len(componentes)} componentes")
            self._update_main_with_data(componentes, region_image)
        # 1) widget de controle (lado direito)
        # no painel à direita omitimos o visor da região E o botão auxiliar
        ctrl_w = InspectionConfigWidget(
            self._c,
            show_region=False,
            show_aux_button=False,
            show_size_controls=False,      # ‼ remove Largura / Altura
            show_region_button=False       # ‼ remove “Definir região”
        )
        # CORREÇÃO CRÍTICA: Bloqueia limpeza de cache durante inicialização da auxiliar
        self._initializing_auxiliary = True
        ctrl_w.spin_w.setValue(self.spin_w.value())
        ctrl_w.spin_h.setValue(self.spin_h.value())
        ctrl_w.spin_sim.setValue(self.spin_sim.value())
        # Passa referência do cache para o widget de controle
        ctrl_w._cached_auxiliary_data = self._cached_auxiliary_data
        ctrl_w._last_roi_bgr = self._last_roi_bgr
        # 2) obtém ROI em resolução total, se disponível
        if self._last_roi_bgr is not None:
            pix = self._bgr_to_pixmap(self._last_roi_bgr)
            # CORREÇÃO: Não sobrescreve cache existente durante inicialização
            if self._cached_auxiliary_data.get('region_image') is None:
                self._cached_auxiliary_data['region_image'] = self._last_roi_bgr.copy()
        else:
            pix = self._bgr_to_pixmap(self._last_roi_bgr) if self._last_roi_bgr is not None else QPixmap()
            # Não força None se já há dados em cache
            if self._cached_auxiliary_data.get('region_image') is None:
                self._cached_auxiliary_data['region_image'] = None
        # 3) cria diálogo e mostra
        dlg = _AuxDialog(pix, ctrl_w, update_callback, self)   # <-- callback direto

        # CORREÇÃO: Libera bloqueio após auxiliar estar totalmente inicializada
        self._initializing_auxiliary = False

        dlg.resize(900, 600)
        dlg.show()

    def _update_main_with_data(self, componentes, region_image):
        """Método simplificado para atualizar visor principal com dados da auxiliar"""
        print(f"[DEBUG] 🔄 Atualizando visor principal diretamente: {len(componentes)} componentes")
        
        # Atualiza cache interno
        self._cached_auxiliary_data['componentes'] = componentes.copy() if componentes else {}
        if region_image is not None:
            self._cached_auxiliary_data['region_image'] = region_image.copy()
            self._last_roi_bgr = region_image.copy()
            print(f"[DEBUG] Imagem atualizada: {region_image.shape}")
        
        # Chama atualização imediata - SEM delay
        try:
            self.update_main_viewer()
            print(f"[DEBUG] ✅ Visor principal atualizado com sucesso")
        except Exception as e:
            print(f"[DEBUG] ❌ Erro na atualização: {e}")

    # ================================================================
    #  NOVO SISTEMA: CACHE SIMPLES PARA DADOS AUXILIARES
    # ================================================================
    
    def clear_auxiliary_cache(self):
        """Limpa o cache de dados auxiliares"""
        # CORREÇÃO: Não limpa cache se estiver inicializando auxiliar
        if hasattr(self, '_initializing_auxiliary') and self._initializing_auxiliary:
            print(f"[DEBUG] Limpeza de cache bloqueada - inicializando auxiliar")
            return
        old_count = len(self._cached_auxiliary_data.get('componentes', {}))
        self._cached_auxiliary_data = {
            'componentes': {},
            'region_image': None
        }
        print(f"[DEBUG] Cache auxiliar limpo - {old_count} componentes removidos")
        
        # CORREÇÃO: Também limpa o visor principal se necessário
        if hasattr(self, 'lbl_region') and hasattr(self, '_last_roi_bgr') and self._last_roi_bgr is not None:
            # Reexibe apenas a imagem-base
            self._set_main_pixmap(self._last_roi_bgr)
            print(f"[DEBUG] Visor principal limpo")

    def debug_cache_status(self):
        """Método para debug - mostra status atual do cache"""
        componentes = self._cached_auxiliary_data.get('componentes', {})
        # DEBUG DETALHADO
        print(f"[DEBUG] === UPDATE_MAIN_VIEWER INICIADO ===")
        print(f"[DEBUG] Componentes no cache: {len(componentes)}")
        print(f"[DEBUG] Widget tem _last_roi_bgr: {hasattr(self, '_last_roi_bgr')}")
        print(f"[DEBUG] _last_roi_bgr é None: {getattr(self, '_last_roi_bgr', None) is None}")
        print(f"\n=== DEBUG CACHE STATUS ===")
        print(f"Componentes em cache: {len(componentes)}")
        print(f"Imagem em cache: {'Sim' if self._cached_auxiliary_data.get('region_image') is not None else 'Não'}")
        print(f"_last_roi_bgr: {'Sim' if self._last_roi_bgr is not None else 'Não'}")
        for nome, dados in componentes.items():
            pos = dados.get('posicao', (0, 0))
            dims = dados.get('dimensoes', (100, 100))
            insp_count = len(dados.get('inspecoes', []))
            print(f"  '{nome}': pos={pos}, dims={dims}, {insp_count} inspeções")
        print("========================\n")
        
    def receive_auxiliary_data(self, componentes, region_image):
        """MÉTODO LEGACY - usar _update_main_with_data"""
        print(f"[DEBUG] ⚠️ receive_auxiliary_data chamado - redirecionando para novo método")
        self._update_main_with_data(componentes, region_image)
        
    def get_cached_auxiliary_data(self):
        """Retorna dados em cache para a auxiliar"""
        return self._cached_auxiliary_data.copy()
    
    def debug_update_viewer(self):
        """Função de debug para testar atualização do visor"""
        print(f"\n[DEBUG] === FUNÇÃO DEBUG CHAMADA ===")
        
        # Debug do cache
        self.debug_cache_status()
        
        # Força atualização
        try:
            self.update_main_viewer()
            print(f"[DEBUG] ✅ update_main_viewer() chamado com sucesso")
        except Exception as e:
            print(f"[DEBUG] ❌ Erro em update_main_viewer(): {e}")
            import traceback
            traceback.print_exc()
            
        print(f"[DEBUG] === FUNÇÃO DEBUG CONCLUÍDA ===")
        
    def update_main_viewer(self):
        """Atualiza o visor principal com as posições mecânicas do cache"""
        print(f"[DEBUG] 🎯 UPDATE_MAIN_VIEWER chamado automaticamente")
        componentes = self._cached_auxiliary_data.get('componentes', {})
        
        if not componentes:
            print(f"[DEBUG] ⚠️ Nenhum componente no cache para exibir")
            return
            
        print(f"[DEBUG] Atualizando visor principal com {len(componentes)} posições")

        # DEBUG: Log detalhado dos componentes
        for nome, dados in componentes.items():
            pos = dados.get('posicao', (0, 0))
            dims = dados.get('dimensoes', (100, 100))
            insp_count = len(dados.get('inspecoes', []))
            print(f"[DEBUG] Componente '{nome}': pos={pos}, dims={dims}, {insp_count} inspeções")
            for i, insp in enumerate(dados.get('inspecoes', [])):
                print(f"[DEBUG]   Inspeção {i+1}: pos={insp.get('posicao', (0,0))}, tam={insp.get('tamanho', (0,0))}")
        
        # CORREÇÃO: Verifica se há imagem base disponível
        if not hasattr(self, '_last_roi_bgr') or self._last_roi_bgr is None:
            print(f"[DEBUG] ⚠️ Nenhuma imagem base disponível (_last_roi_bgr é None)")
            # Tenta usar imagem do cache se existir
            cached_image = self._cached_auxiliary_data.get('region_image')
            if cached_image is not None:
                self._last_roi_bgr = cached_image.copy()
                print(f"[DEBUG] ✅ Imagem restaurada do cache: {self._last_roi_bgr.shape}")
            
            elif hasattr(self, 'lbl_region') and self.lbl_region.pixmap():
                # Fallback: usa imagem do label se existir
                print(f"[DEBUG] Tentando usar imagem do label como base")
                try:
                    # Converte pixmap para BGR
                    pixmap = self.lbl_region.pixmap()
                    self._last_roi_bgr = self._qpixmap_to_bgr(pixmap)
                    if self._last_roi_bgr is None:
                        print(f"[DEBUG] ❌ Falha ao converter pixmap para BGR")
                        return
                    print(f"[DEBUG] ✅ Imagem convertida: {self._last_roi_bgr.shape}")
                except Exception as e:
                    print(f"[DEBUG] ❌ Erro ao converter pixmap: {e}")
                    return
            else:
                # NOVO: Tenta criar imagem padrão se não houver nenhuma
                print(f"[DEBUG] 🔧 Criando imagem padrão para desenho...")
                try:
                    import numpy as np
                    # Cria imagem padrão 400x300 (cinza escuro)
                    default_image = np.full((300, 400, 3), (64, 64, 64), dtype=np.uint8)
                    self._last_roi_bgr = default_image
                    self._cached_auxiliary_data['region_image'] = default_image.copy()
                    print(f"[DEBUG] ✅ Imagem padrão criada: {default_image.shape}")
                except Exception as e:
                    print(f"[DEBUG] ❌ Erro ao criar imagem padrão: {e}")
                    return
        
        # Garante que o cache tem a imagem atual
        if self._cached_auxiliary_data.get('region_image') is None and self._last_roi_bgr is not None:
            self._cached_auxiliary_data['region_image'] = self._last_roi_bgr.copy()
            print(f"[DEBUG] ✅ Cache atualizado com imagem atual")
        
        # Log das dimensões da imagem base
        h, w = self._last_roi_bgr.shape[:2]
        print(f"[DEBUG] Imagem base: {w}x{h} pixels")
        
        # Log dos dados dos componentes
        for nome, dados in componentes.items():
            pos = dados.get('posicao', (0, 0))
            dims = dados.get('dimensoes', (100, 100))

            inspecoes = dados.get('inspecoes', [])
            print(f"[DEBUG] Componente '{nome}': pos={pos}, dims={dims}, {len(inspecoes)} inspeções")
        
        # Exibe APENAS a imagem, sem desenhar retângulos nela
        # (os retângulos agora serão itens clicáveis sobrepostos na cena)
        self._set_main_pixmap(self._last_roi_bgr)

        # -----------------------------------------------------------------
        #  NOVO: cria/actualiza retângulos clicáveis para cada posição
        # -----------------------------------------------------------------
        self._refresh_clickable_position_items(componentes)
        print(f"[DEBUG] ‚úÖ Visor principal atualizado com itens clicáveis")
 
    # -----------------------------------------------------------------
    #  NOVO  –  retângulos vermelhos clicáveis no visor principal
    # -----------------------------------------------------------------
    def _refresh_clickable_position_items(self, componentes):
        """
        Remove janelas antigas e cria novas janelas vermelhas clicáveis
        correspondentes às posições mecânicas do cache.
        """
        # 1) remove janelas existentes
        for win in list(self.region_editor.windows):
            try:
                if win.scene():
                    win.scene().removeItem(win)
            except RuntimeError:
                pass
        self.region_editor.windows.clear()

        # 2) recria uma janela para cada componente
        red_pen = QPen(Qt.GlobalColor.red, 2)
        for nome, dados in componentes.items():
            pos_x, pos_y = dados.get('posicao', (0, 0))
            dim_w, dim_h = dados.get('dimensoes', (100, 100))
            self.region_editor.add_window(
                x=pos_x, y=pos_y,
                w=dim_w, h=dim_h,
                pen=red_pen,
                name=nome,
                deletable=False,         # protegidas de deleção acidental
                editable=False          # protegidas de deleção acidental
            )

    def _qpixmap_to_bgr(self, pixmap):
        """Converte QPixmap para numpy BGR"""
        try:
            if pixmap.isNull():
                return None
            image = pixmap.toImage().convertToFormat(QImage.Format.Format_RGB888)
            w, h = image.width(), image.height()
            ptr = image.bits().asstring(w * h * 3)
            import numpy as np
            arr = np.frombuffer(ptr, np.uint8).reshape((h, w, 3))
            return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
        except Exception as e:
            print(f"[DEBUG] Erro na conversão QPixmap->BGR: {e}")
            return None
            
    def _draw_positions_on_image(self, img_bgr, componentes):
        """Desenha retângulos das posições mecânicas sobre a imagem"""            
        h_img, w_img = img_bgr.shape[:2]
        print(f"[DEBUG] Desenhando {len(componentes)} posições em imagem {w_img}x{h_img}")
        
        posicoes_desenhadas = 0
        inspecoes_desenhadas = 0
        
        for nome, dados in componentes.items():
            pos = dados.get('posicao', (0, 0))
            dims = dados.get('dimensoes', (100, 100))
            
            # Usa coordenadas da posição mecânica
            pos_x, pos_y = pos
            pos_w, pos_h = dims
                                            
            # CORREÇÃO: Verifica se coordenadas estão dentro da imagem
            if pos_x < 0 or pos_y < 0 or pos_x + pos_w > w_img or pos_y + pos_h > h_img:
    
                # Ajusta coordenadas para ficar dentro da imagem
                pos_x = max(0, min(pos_x, w_img - 1))
                pos_y = max(0, min(pos_y, h_img - 1))
                pos_w = min(pos_w, w_img - pos_x)
                pos_h = min(pos_h, h_img - pos_y)                
             
            # Verifica se dimensões são válidas após ajuste
            if pos_w <= 0 or pos_h <= 0:
                print(f"[DEBUG] ❌ Dimensões inválidas após ajuste: {pos_w}x{pos_h} - pulando")
                continue
            
            # Desenha retângulo VERMELHO para a posição mecânica (como solicitado)
            try:
                cv2.rectangle(img_bgr, (pos_x, pos_y), (pos_x + pos_w, pos_y + pos_h), (0, 0, 255), 3)  # Vermelho, espessura 3
                
            except Exception as e:
                print(f"[DEBUG] ❌ Erro ao desenhar retângulo vermelho: {e}")
                continue
            posicoes_desenhadas += 1
            
            # Adiciona texto com o nome
            try:
                cv2.putText(img_bgr, nome, (pos_x, pos_y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)  # Texto vermelho
                print(f"[DEBUG] ✅ Texto '{nome}' adicionado")
            except Exception as e:
                print(f"[DEBUG] ⚠️ Erro ao adicionar texto: {e}")
            print(f"[DEBUG] ✅ Posição '{nome}' processada completamente")

            # REMOVIDO: Desenho das janelas azuis (não necessário no visor principal)
            print(f"[DEBUG] ✅ Posição '{nome}' concluída - janelas de inspeção serão exibidas apenas no visor ROI")

        print(f"[DEBUG] Resultado: {posicoes_desenhadas} posições e {inspecoes_desenhadas} inspeções desenhadas")
        
        return img_bgr
    
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
        # Visor ROI (pequeno) continua com ajuste já existente
        self._update_roi_aspect()

        # Novo: mantém visor 'Região' em 4:3 e ≤ 15 % da tela
        self._adjust_region_size()

        # Re-encaixa a imagem na área disponível
        if hasattr(self, "view_region"):
            self.view_region.fitInView(self._region_pix_item,
                                       Qt.AspectRatioMode.KeepAspectRatio)
            
    # --------------------------------------------------------------
    #  NOVO MÉTODO – mostra ROI da posição mecânica selecionada
    # --------------------------------------------------------------
    def _update_roi_from_selection_main(self):
        """
        Exibe, no visor ‘ROI’ deste painel, o conteúdo da
        Posição Mecânica (ResizableRectItem) atualmente selecionada
        no visor principal (‘Região’).
        """
        # É necessário ter imagem de referência
        if self._last_roi_bgr is None:
            return

        # Há item selecionado?
        sel_items = [it for it in self.view_region.scene().selectedItems()
                     if isinstance(it, ResizableRectItem)]
        if not sel_items:
            return

        item = sel_items[0]

        # Converte retângulo do item para coordenadas de cena
        r_scene = item.mapRectToScene(item.rect())
        x, y, w, h = map(int, [r_scene.x(), r_scene.y(),
                               r_scene.width(), r_scene.height()])

        h_img, w_img, _ = self._last_roi_bgr.shape

        # Garante que o recorte está dentro da imagem
        x = max(0, min(x, w_img - 1))
        y = max(0, min(y, h_img - 1))
        w = max(1, min(w, w_img - x))
        h = max(1, min(h, h_img - y))

        roi_bgr = self._last_roi_bgr[y:y + h, x:x + w].copy()
        if roi_bgr.size == 0:
            return

        # Mostra no visor ‘ROI’
        self._show_pixmap(self.lbl_roi, roi_bgr)
