from typing import List, Dict
import math
import sys
import traceback
# GUI / imagem (PyQt6)
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QLabel,
    QFileDialog,
    QMessageBox,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, QByteArray, QBuffer, QIODevice
from PyQt6.QtGui import QPixmap

from PIL import Image, ImageDraw


class ApertureMacro:
    def __init__(self, name):
        self.name = name
        self.primitives = []  # cada item = (code, expo, params)

    def add_primitive(self, code, expo, params):
        self.primitives.append((code, expo, params))

    def render(self, scale_x=1, scale_y=1, rot_deg=0, trans=(0,0)):
        """
        Retorna lista de polígonos (listas de pontos) já transformados.
        O parâmetro `trans` permite **posicionar** a macro em coordenadas
        do mundo (útil para flashes de stencils). Antes o método só
        retornava o shape, mas não considerava rotação/escala por
        flash; agora isso está documentado.
        """
        polys = []
        theta = math.radians(rot_deg)
        cos_t, sin_t = math.cos(theta), math.sin(theta)

        def transform(pt):
            x = pt[0]*scale_x
            y = pt[1]*scale_y
            # rotaciona
            xr =  x*cos_t - y*sin_t
            yr =  x*sin_t + y*cos_t
            # translada
            return (xr + trans[0], yr + trans[1])

        for code, expo, p in self.primitives:
            if code == 4:  # outline
                N = int(p[0])
                coords = []
                for i in range(N):
                    x = float(p[1+2*i])
                    y = float(p[1+2*i+1])
                    coords.append(transform((x,y)))
                # fecha o polígono (exposição 1 → sólido)
                if expo == 1:
                    polys.append(coords + [coords[0]])   # fecha explicitamente
                # expo == 0 pode ser “hole”; deixamos para futuro
                # expo=0 poderia significar “buraco”: tratar como subtração
        return polys

def parse_macro(lines):
    """Recebe lista de linhas entre %AM…* e % e devolve ApertureMacro."""
    header = lines[0]            # ex: "%AMacap0165_180*"
    name = header[3:-1]
    mac = ApertureMacro(name)
    # junta só as linhas que NÃO são o "%" final
    body = "".join(l for l in lines[1:] if not l.strip() == '%')
    # só tokens que começam com dígito (4,1,42,...) e não "%", ou vazios
    prims = [s.strip() for s in body.split('*')
             if s.strip() and s.strip()[0].isdigit()]
    for prim in prims:
        tokens = prim.split(',')
        code = int(tokens[0])
        expo = int(tokens[1])
        params = tokens[2:]
        mac.add_primitive(code, expo, params)
    return mac

def parse_all_macros(gerber_lines: List[str]) -> Dict[str, ApertureMacro]:
    """
    Varre o arquivo Gerber linha a linha e extrai todos os blocos de macro:
      %AMnome*
        ...
      %
    ou o formato clássico:
      %AMnome*
        ...
      ...0.00000*%

    Parâmetro:
        gerber_lines: lista de linhas do arquivo Gerber (por exemplo, f.readlines()).

    Retorna:
        dicionário {nome_da_macro: ApertureMacro}.
    """
    macros: Dict[str, ApertureMacro] = {}
    i = 0
    n = len(gerber_lines)

    while i < n:
        line = gerber_lines[i].strip()
        if line.startswith("%AM"):
            block = [line]
            i += 1
            # Acumula linhas da macro até encontrar:
            #  - uma linha que seja apenas "%", como no arquivo do CAM350
            #  - OU uma linha que termine com "*%", formato Gerber clássico
            while (
                i < n
                and gerber_lines[i].strip() != "%"
                and not gerber_lines[i].strip().endswith("*%")
            ):
                block.append(gerber_lines[i].rstrip("\n"))
                i += 1

            # Adiciona também a linha de término (%, ou ...*%)
            if i < n:
                block.append(gerber_lines[i].rstrip("\n"))

            macro = parse_macro(block)
            macros[macro.name] = macro

        i += 1

    return macros

def render_polys_to_image(
    polys,
    img_size=(500, 500),
    margin=20,
    fill="black",
    bg="white",
):
    """
    Constrói um objeto PIL.Image a partir da lista de polígonos.
    Esta função é usada tanto pelo modo GUI (preview em memória)
    quanto pelo modo que salva PNG em disco (draw_polys).
    """
    # Extrai todos os X e Y para determinar bounds
    xs = [pt[0] for poly in polys for pt in poly]
    ys = [pt[1] for poly in polys for pt in poly]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)

    # Tamanho do “mundo”
    w_world = maxx - minx
    h_world = maxy - miny
    if w_world == 0 or h_world == 0:
        raise RuntimeError("Polígonos degenerados")

    # Fator de escala para caber na imagem (mantendo aspecto)
    scale_x = (img_size[0] - 2 * margin) / w_world
    scale_y = (img_size[1] - 2 * margin) / h_world
    scale = min(scale_x, scale_y)

    # Cria imagem
    img = Image.new("RGB", img_size, bg)
    draw = ImageDraw.Draw(img)

    # Desenha cada polígono, invertendo Y para o sistema de imagem
    for poly in polys:
        pts = []
        for x, y in poly:
            xx = (x - minx) * scale + margin
            yy = img_size[1] - ((y - miny) * scale + margin)
            pts.append((xx, yy))
        draw.polygon(pts, fill=fill)

    return img


def draw_polys(polys, filename="macro.png", img_size=(500,500), margin=20):
    """
    Desenha a lista de polígonos em um PNG.
    - polys: lista de listas de tuplas (x,y) em coordenadas reais.
    - filename: caminho de saída.
    - img_size: tupla (width, height) em pixels.
    - margin: margem em pixels.
    """
    img = render_polys_to_image(polys, img_size=img_size, margin=margin)
    img.save(filename)
    print(f"Imagem salva em: {filename}")


class GerberMacroViewer(QMainWindow):
    """
    Janela principal da aplicação (PyQt6):
      - Botão para selecionar arquivo Gerber.
      - Tree (QTreeWidget) à esquerda listando todas as macros (%AM...%).
      - Área de preview à direita mostrando a forma da macro selecionada.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gerber Macro Viewer")

        # Dimensões do preview
        self.preview_width = 600
        self.preview_height = 600

        # Armazena macros carregadas
        self.macros: Dict[str, ApertureMacro] = {}

        # Guarda referência para a imagem exibida (evita GC)
        self._current_image = None   # PIL.Image
        self._current_pixmap = None  # QPixmap

        self._build_ui()

    def _build_ui(self):
        # Widget central + layout principal vertical
        central = QWidget(self)
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)

        # --- Barra superior com botão de abrir arquivo ---
        top_layout = QHBoxLayout()
        self.open_btn = QPushButton("Abrir arquivo Gerber...")
        self.open_btn.clicked.connect(self.on_open_file)
        top_layout.addWidget(self.open_btn)
        top_layout.addStretch(1)
        main_layout.addLayout(top_layout)

        # --- Área principal: esquerda (tree) e direita (preview) ---
        content_layout = QHBoxLayout()
        main_layout.addLayout(content_layout, 1)

        # ---- Esquerda: Tree de macros ----
        left_layout = QVBoxLayout()
        content_layout.addLayout(left_layout, 1)

        lbl_macros = QLabel("Macros encontradas:")
        left_layout.addWidget(lbl_macros)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.itemSelectionChanged.connect(self.on_tree_select)
        left_layout.addWidget(self.tree, 1)

        # ---- Direita: Preview ----
        right_layout = QVBoxLayout()
        content_layout.addLayout(right_layout, 2)

        lbl_preview = QLabel("Pré-visualização da macro selecionada:")
        right_layout.addWidget(lbl_preview)

        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self.preview_label.setMinimumSize(self.preview_width, self.preview_height)
        right_layout.addWidget(self.preview_label, 1)

    # ------------------------------------------------------------------
    # Lógica de carregamento de arquivo / macros
    # ------------------------------------------------------------------
    def on_open_file(self):
        """
        Handler do botão 'Abrir arquivo Gerber...':
          - Abre diálogo de arquivo.
          - Lê e parseia macros.
          - Preenche a tree.
        """
        filters = (
            "Arquivos Gerber (*.gbr *.ger *.pho *.art *.gb* *.gt* *.g*);;"
            "Todos os arquivos (*.*)"
        )
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar arquivo Gerber",
            "",
            filters,
        )
        if not path:
            return

        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except OSError as e:
            QMessageBox.critical(
                self,
                "Erro ao abrir arquivo",
                f"Não foi possível abrir:\n{path}\n\n{e}",
            )
            return

        macros = parse_all_macros(lines)
        if not macros:
            QMessageBox.information(
                self,
                "Nenhuma macro encontrada",
                "Nenhuma macro (%AM...%) foi encontrada neste arquivo.",
            )
            self.tree.clear()
            self._clear_preview()
            self.macros = {}
            return

        self.macros = macros
        self._populate_tree()
        self._clear_preview()

    def _populate_tree(self):
        """Preenche a tree com os nomes das macros carregadas."""
        self.tree.clear()

        names = sorted(self.macros.keys())
        first_item = None
        for name in names:
            item = QTreeWidgetItem([name])
            self.tree.addTopLevelItem(item)
            if first_item is None:
                first_item = item

        # Seleciona automaticamente a primeira macro, se existir
        if first_item is not None:
            self.tree.setCurrentItem(first_item)
            self._update_preview(first_item.text(0))

    def _clear_preview(self):
        """Limpa o preview (remove imagem e referências)."""
        self.preview_label.clear()
        self._current_image = None
        self._current_pixmap = None

    # ------------------------------------------------------------------
    # Interação com a tree / preview
    # ------------------------------------------------------------------
    def on_tree_select(self):
        """Callback quando a seleção na tree é alterada."""
        try:
            selected_items = self.tree.selectedItems()
            if not selected_items:
                return
            name = selected_items[0].text(0)
            self._update_preview(name)
        except Exception:
            # Garante que qualquer exceção apareça no terminal
            traceback.print_exc()
            QMessageBox.critical(
                self,
                "Erro na seleção",
                "Ocorreu um erro ao atualizar o preview. Veja o terminal para detalhes.",
            )
    def _update_preview(self, macro_name: str):
        """Gera e mostra o preview da macro com nome 'macro_name'."""
        macro = self.macros.get(macro_name)
        if macro is None:
            return

        try:
            polys = macro.render()
            img = render_polys_to_image(
                polys,
                img_size=(self.preview_width, self.preview_height),
                margin=30,
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro ao renderizar macro",
                f"Macro: {macro_name}\n\n{e}",
            )
            return

        # Guarda referências para evitar coleta de lixo
        self._current_image = img

        # Converte PIL.Image -> QPixmap via buffer em memória (evita problemas
        # de compatibilidade entre Pillow e PyQt6)
        try:
            ba = QByteArray()
            buffer = QBuffer(ba)
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            # salva a imagem em formato PNG no buffer
            img.save(buffer, format="PNG")
            buffer.close()

            pixmap = QPixmap()
            pixmap.loadFromData(ba, "PNG")

            self._current_pixmap = pixmap
            self.preview_label.setPixmap(pixmap)
        except Exception:
            traceback.print_exc()
            QMessageBox.critical(
                self,
                "Erro ao converter imagem",
                f"Não foi possível converter a macro '{macro_name}' para exibição.",
            )


if __name__ == "__main__":
    # Inicia a aplicação PyQt6
    app = QApplication(sys.argv)
    window = GerberMacroViewer()
    window.resize(900, 700)
    window.show()
    sys.exit(app.exec())
