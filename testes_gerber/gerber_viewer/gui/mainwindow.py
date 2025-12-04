from __future__ import annotations

import sys
import traceback
from typing import Dict, List

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QAction
from PyQt6.QtWidgets import (
    QApplication,
    QColorDialog,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..apertures import ApertureInstance, parse_add, parse_all_macros
from ..config import GerberConfig, parse_gerber_config
from ..parser import build_layer_polys_mm
from ..render import render_polys_to_image
from .preview import PreviewGraphicsView


class GerberMacroViewer(QMainWindow):
    """
    Janela principal da aplicação (PyQt6):
      - Menu para criar projeto e importar arquivo Gerber.
      - Renderização da camada completa em mm logo após a importação.
      - Área de preview com zoom/pan para visualizar a camada completa.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gerber Macro Viewer")

        # Dimensões da imagem base (alta resolução para zoom)
        self.preview_width = 2000
        self.preview_height = 2000

        # Armazena dados do Gerber carregado
        self.gerber_lines: List[str] | None = None
        self.gerber_cfg: GerberConfig | None = None

        # Armazena macros carregadas (%AM...) e aperturas (%ADD...)
        self.macros = {}
        self.apertures_by_dcode: Dict[int, ApertureInstance] = {}

        # Cores configuráveis pelo usuário
        self.aperture_color = QColor(Qt.GlobalColor.black)
        self.background_color = QColor(Qt.GlobalColor.white)

        # Guarda polígonos da camada para exportar
        self._full_layer_polys_mm: List[List[tuple[float, float]]] | None = None
        self._current_pixmap = None  # mantido apenas para compatibilidade
        self.current_project_name: str | None = None
        self._build_ui()

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        menubar = self.menuBar()

        # ------------------------- Menu Arquivo -------------------------
        arquivo_menu: QMenu = menubar.addMenu("Arquivo")

        # Novo projeto
        act_new_project: QAction = arquivo_menu.addAction("Novo projeto")
        act_new_project.triggered.connect(self.on_new_project)

        # Importar arquivo .gbr
        act_import_gbr: QAction = arquivo_menu.addAction("Importar arquivo .gbr")
        act_import_gbr.triggered.connect(self.on_import_gbr)

        arquivo_menu.addSeparator()

        # Salvar / Salvar como
        act_save: QAction = arquivo_menu.addAction("Salvar")
        act_save.triggered.connect(self.on_save)
        act_save_as: QAction = arquivo_menu.addAction("Salvar como")
        act_save_as.triggered.connect(self.on_save_as)

        arquivo_menu.addSeparator()

        # Exportar
        export_menu: QMenu = arquivo_menu.addMenu("Exportar")
        act_export_gbr: QAction = export_menu.addAction(".gbr")
        act_export_gbr.triggered.connect(self.on_export_gbr)
        act_export_dxf: QAction = export_menu.addAction(".dxf")
        act_export_dxf.triggered.connect(self.on_export_dxf)

        # ---------------------- Menu Configurações ----------------------
        config_menu = menubar.addMenu("Configurações")

        act_aperture_color = config_menu.addAction("Cor da abertura")
        act_aperture_color.triggered.connect(self.on_choose_aperture_color)

        act_bg_color = config_menu.addAction("Cor do fundo")
        act_bg_color.triggered.connect(self.on_choose_background_color)

        central = QWidget(self)
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # Barra superior
        top_layout = QHBoxLayout()

        self.reset_view_btn = QPushButton("Ajustar visão")
        self.reset_view_btn.clicked.connect(self.on_reset_view)
        self.reset_view_btn.setEnabled(False)
        top_layout.addWidget(self.reset_view_btn)

        self.export_btn = QPushButton("Exportar PNG...")
        self.export_btn.clicked.connect(self.on_export_png)
        self.export_btn.setEnabled(False)
        top_layout.addWidget(self.export_btn)

        top_layout.addStretch(1)
        main_layout.addLayout(top_layout)

        # Área de preview
        right_layout = QVBoxLayout()
        main_layout.addLayout(right_layout, 1)

        lbl_preview = QLabel("Pré-visualização da camada completa:")
        right_layout.addWidget(lbl_preview)

        self.preview_view = PreviewGraphicsView()
        self.preview_view.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self.preview_view.setMinimumSize(600, 400)
        right_layout.addWidget(self.preview_view, 1)
        # Barra de status (rodapé) para exibir o nome do projeto
        self.statusBar().showMessage("Nenhum projeto")

    # ------------------------------------------------------------------ Menu Arquivo
    def _feature_not_implemented(self, name: str):
        QMessageBox.information(
            self,
            "Não implementado",
            f"A funcionalidade '{name}' ainda não foi implementada.",
        )

    def on_new_project(self):
        """
        Cria um novo projeto:
          - limpa a visualização/estado atual;
          - solicita o nome do projeto (obrigatório);
          - exibe o nome no rodapé no formato 'Projeto: <nome>'.
        """
        # 1) Limpa visualização e estado atual de arquivo/projeto
        self.gerber_lines = None
        self.gerber_cfg = None
        self.apertures_by_dcode = {}
        self.macros = {}
        self._full_layer_polys_mm = None
        self._clear_preview()

        # 2) Solicita o nome do novo projeto (obrigatório)
        name, ok = QInputDialog.getText(
            self,
            "Novo projeto",
            "Informe o nome do novo projeto:",
        )
        if not ok:
            # Usuário cancelou: não altera o projeto atual
            return

        name = name.strip()
        if not name:
            QMessageBox.warning(self, "Nome obrigatório",
                                "É necessário informar um nome para o projeto.")
            return

        # 3) Atualiza estado e barra de status
        self.current_project_name = name
        self.statusBar().showMessage(f"Projeto: {name}")

        # 4) Inicia fluxo de importação de arquivo Gerber para este projeto
        #    (abre o diálogo de seleção e, se o arquivo for carregado,
        #     já renderiza automaticamente a camada completa)
        self.on_import_gbr()

    def on_import_gbr(self):
        """
        Importa um arquivo Gerber (.gbr):
          - reutiliza a rotina de abertura de arquivo;
          - se houver arquivo selecionado e carregado com sucesso,
            já gera e exibe a camada completa (mm).
        """
        loaded = self.on_open_file()
        if not loaded:
            return
        self.on_render_full_layer()

    def on_save(self):
        self._feature_not_implemented("Salvar")

    def on_save_as(self):
        self._feature_not_implemented("Salvar como")

    def on_export_gbr(self):
        self._feature_not_implemented("Exportar .gbr")

    def on_export_dxf(self):
        self._feature_not_implemented("Exportar .dxf")

    # ------------------------------------------------------------------ Abrir arquivo (.gbr)
    # (rotina de abertura/reimportação de arquivo Gerber)
    def on_open_file(self) -> bool:
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
            return False

        self.gerber_lines = None
        self.gerber_cfg = None
        self.apertures_by_dcode = {}
        self._full_layer_polys_mm = None
        self.macros = {}

        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except OSError as e:
            QMessageBox.critical(
                self,
                "Erro ao abrir arquivo",
                f"Não foi possível abrir:\n{path}\n\n{e}",
            )
            return False

        self.gerber_lines = lines
        self.gerber_cfg = parse_gerber_config(lines)
        self.apertures_by_dcode = parse_add(lines, self.gerber_cfg)
        self.macros = parse_all_macros(lines)

        self._clear_preview()
        return True

    # ------------------------------------------------------------------ Camada completa
    def on_render_full_layer(self):
        if self.gerber_lines is None or self.gerber_cfg is None:
            QMessageBox.information(
                self,
                "Nenhum arquivo",
                "Abra um arquivo Gerber antes de gerar a camada completa.",
            )
            return

        try:
            polys_mm = build_layer_polys_mm(
                self.gerber_lines,
                self.macros,
                self.apertures_by_dcode,
                self.gerber_cfg,
            )
            self._full_layer_polys_mm = polys_mm
        except Exception:
            traceback.print_exc()
            QMessageBox.critical(
                self,
                "Erro ao gerar camada completa",
                "Ocorreu um erro ao processar a camada completa.\n"
                "Veja o terminal para detalhes.",
            )
            return

        if not polys_mm:
            QMessageBox.information(
                self,
                "Nada para exibir",
                "Nenhuma entidade geométrica foi encontrada para a camada completa.",
            )
            return

        try:
            # Apenas para validar rasterização; preview será vetorial
            _ = render_polys_to_image(
                polys_mm,
                img_size=(self.preview_width, self.preview_height),
                margin=20,
            )
        except Exception:
            traceback.print_exc()
            QMessageBox.critical(
                self,
                "Erro ao renderizar imagem",
                "Falha ao rasterizar a camada completa.",
            )
            return

        try:
            self._current_pixmap = None
            self.preview_view.set_polygons(
                polys_mm,
                aperture_color=self.aperture_color,
                bg_color=self.background_color,
            )
            self.export_btn.setEnabled(True)
            self.reset_view_btn.setEnabled(True)
        except Exception:
            traceback.print_exc()
            QMessageBox.critical(
                self,
                "Erro ao converter imagem",
                "Não foi possível converter a imagem da camada completa para exibição.",
            )

    # ------------------------------------------------------------------ Export PNG
    def on_export_png(self):
        if not self._full_layer_polys_mm:
            QMessageBox.information(
                self,
                "Nada para exportar",
                "Não há nenhum dado de camada completa para exportar.\n"
                "Gere a camada completa primeiro.",
            )
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar imagem em PNG",
            "",
            "Imagem PNG (*.png)",
        )
        if not path:
            return

        factor, ok = QInputDialog.getInt(
            self,
            "Escala da imagem",
            "Fator de escala (1 = igual ao preview, 2 = 2x, ...):",
            4,   # padrão
            1,   # mínimo
            20,  # máximo
            1,   # step
        )
        if not ok:
            return

        from ..render import render_polys_to_image  # local import para evitar dependências cíclicas

        try:
            ac = self.aperture_color
            bc = self.background_color
            fill_rgb = (ac.red(), ac.green(), ac.blue())
            bg_rgb = (bc.red(), bc.green(), bc.blue())

            img = render_polys_to_image(
                self._full_layer_polys_mm,
                img_size=(
                    self.preview_width * factor,
                    self.preview_height * factor,
                ),
                margin=20 * factor,
                fill=fill_rgb,
                bg=bg_rgb,
            )
            img.save(path, format="PNG")
        except Exception:
            traceback.print_exc()
            QMessageBox.critical(
                self,
                "Erro ao exportar PNG",
                "Ocorreu um erro ao gerar o PNG de alta resolução.\n"
                "Veja o terminal para detalhes.",
            )

    def on_reset_view(self):
        self.preview_view.reset_view()

    # ------------------------------------------------------------------ Cores
    def on_choose_aperture_color(self):
        color = QColorDialog.getColor(
            self.aperture_color,
            self,
            "Selecionar cor da abertura",
        )
        if not color.isValid():
            return
        self.aperture_color = color
        if self._full_layer_polys_mm:
            self.preview_view.set_polygons(
                self._full_layer_polys_mm,
                aperture_color=self.aperture_color,
                bg_color=self.background_color,
            )

    def on_choose_background_color(self):
        color = QColorDialog.getColor(
            self.background_color,
            self,
            "Selecionar cor do fundo",
        )
        if not color.isValid():
            return
        self.background_color = color
        if self._full_layer_polys_mm:
            self.preview_view.set_polygons(
                self._full_layer_polys_mm,
                aperture_color=self.aperture_color,
                bg_color=self.background_color,
            )

    # ------------------------------------------------------------------ Utilitários
    def _clear_preview(self):
        self.preview_view._scene.clear()
        self.preview_view._polys_mm = []
        self._current_pixmap = None
        self.export_btn.setEnabled(False)
        self.reset_view_btn.setEnabled(False)


def run():
    app = QApplication(sys.argv)
    window = GerberMacroViewer()
    window.resize(900, 700)
    window.show()
    sys.exit(app.exec())
