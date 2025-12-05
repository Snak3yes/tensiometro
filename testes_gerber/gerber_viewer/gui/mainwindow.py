from __future__ import annotations

import sys
import traceback
from typing import Dict, List, Callable

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QAction
from PyQt6.QtWidgets import (
    QApplication,
    QColorDialog,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QDoubleSpinBox,
    QCheckBox,
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

from ..geometry import circle_to_polys_mm, rect_to_polys_mm, oval_to_polys_mm
from ..apertures import ApertureInstance, parse_add, parse_all_macros
from ..config import GerberConfig, parse_gerber_config
from ..parser import build_layer_objects_mm, GerberObject
from ..exporter import objects_to_gerber
from ..render import render_polys_to_image
from .preview import PreviewGraphicsView

class WidthHeightDialog(QDialog):
    """
    Diálogo para edição simultânea de largura e altura, em mm e em %.
    Padrão inspirado em Corel/Illustrator:
      - campos absolutos (mm),
      - campos de escala (% da dimensão original),
      - opção "Manter proporção".
    Usado para:
      - flash_rect / flash_oval
      - regiões (kind == "region")
    """

    def __init__(
        self,
        title: str,
        label_width: str,
        label_height: str,
        cur_w: float,
        cur_h: float,
        parent: QWidget | None = None,
        move_callback: Callable[[float, float], None] | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self._move_cb = move_callback

        layout = QFormLayout(self)

        # Guarda dimensões originais (para cálculo de % e manter proporção)
        self._orig_w = cur_w
        self._orig_h = cur_h
        self._updating = False  # evita loops de sinal

        # --------------------- Campos absolutos (mm) ---------------------
        self._w_mm_spin = QDoubleSpinBox(self)
        self._w_mm_spin.setRange(0.001, 1000.0)
        self._w_mm_spin.setDecimals(3)
        self._w_mm_spin.setValue(cur_w)

        self._h_mm_spin = QDoubleSpinBox(self)
        self._h_mm_spin.setRange(0.001, 1000.0)
        self._h_mm_spin.setDecimals(3)
        self._h_mm_spin.setValue(cur_h)

        layout.addRow(label_width, self._w_mm_spin)
        layout.addRow(label_height, self._h_mm_spin)

        # ------------------------ Campos em % ----------------------------
        self._w_pct_spin = QDoubleSpinBox(self)
        self._w_pct_spin.setRange(0.01, 10000.0)  # 0,01% a 100x
        self._w_pct_spin.setDecimals(2)
        self._w_pct_spin.setSuffix(" %")
        self._w_pct_spin.setValue(100.0)

        self._h_pct_spin = QDoubleSpinBox(self)
        self._h_pct_spin.setRange(0.01, 10000.0)
        self._h_pct_spin.setDecimals(2)
        self._h_pct_spin.setSuffix(" %")
        self._h_pct_spin.setValue(100.0)

        layout.addRow("Largura (%):", self._w_pct_spin)
        layout.addRow("Altura (%):", self._h_pct_spin)

        # -------------------- Manter proporção ---------------------------
        self._lock_aspect_chk = QCheckBox("Manter proporção", self)
        self._lock_aspect_chk.setChecked(True)
        layout.addRow("", self._lock_aspect_chk)

        # --------------------- Movimento (X/Y) ---------------------------
        # Passo de movimento
        self._move_step_spin = QDoubleSpinBox(self)
        self._move_step_spin.setRange(0.001, 1000.0)
        self._move_step_spin.setDecimals(3)
        self._move_step_spin.setValue(0.050)  # passo padrão: 0,05 mm
        layout.addRow("Passo mov. (mm):", self._move_step_spin)

        # Botões de seta (← ↑ ↓ →)
        move_widget = QWidget(self)
        move_layout = QHBoxLayout(move_widget)
        move_layout.setContentsMargins(0, 0, 0, 0)

        self._btn_left = QPushButton("←", self)
        self._btn_up = QPushButton("↑", self)
        self._btn_down = QPushButton("↓", self)
        self._btn_right = QPushButton("→", self)

        for b in (self._btn_left, self._btn_up, self._btn_down, self._btn_right):
            b.setFixedWidth(32)

        move_layout.addWidget(self._btn_left)
        move_layout.addWidget(self._btn_up)
        move_layout.addWidget(self._btn_down)
        move_layout.addWidget(self._btn_right)

        layout.addRow("Mover:", move_widget)

        # Conexão de sinais (mm <-> %)
        self._w_mm_spin.valueChanged.connect(self._on_mm_changed)
        self._h_mm_spin.valueChanged.connect(self._on_mm_changed)
        self._w_pct_spin.valueChanged.connect(self._on_pct_changed)
        self._h_pct_spin.valueChanged.connect(self._on_pct_changed)

        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addRow(btn_box)

        # Conexão das setas de movimento
        self._btn_left.clicked.connect(lambda: self._on_move_clicked(-1, 0))
        self._btn_right.clicked.connect(lambda: self._on_move_clicked(1, 0))
        self._btn_up.clicked.connect(lambda: self._on_move_clicked(0, 1))
        self._btn_down.clicked.connect(lambda: self._on_move_clicked(0, -1))

    # ---------------------------- Lógica ----------------------------
    def _on_mm_changed(self, _value: float):
        """Atualiza % a partir dos campos em mm, e aplica 'manter proporção'."""
        if self._updating:
            return
        self._updating = True
        try:
            sender = self.sender()
            # Manter proporção: altera a outra dimensão com base na escala
            if self._lock_aspect_chk.isChecked():
                if sender is self._w_mm_spin and self._orig_w > 0:
                    scale = self._w_mm_spin.value() / self._orig_w
                    new_h = self._orig_h * scale
                    self._h_mm_spin.setValue(new_h)
                elif sender is self._h_mm_spin and self._orig_h > 0:
                    scale = self._h_mm_spin.value() / self._orig_h
                    new_w = self._orig_w * scale
                    self._w_mm_spin.setValue(new_w)

            # Atualiza % com base nos valores atuais em mm
            if self._orig_w > 0:
                self._w_pct_spin.setValue(
                    self._w_mm_spin.value() / self._orig_w * 100.0
                )
            if self._orig_h > 0:
                self._h_pct_spin.setValue(
                    self._h_mm_spin.value() / self._orig_h * 100.0
                )
        finally:
            self._updating = False

    

    def _on_pct_changed(self, _value: float):
        """Atualiza mm a partir dos campos em %, e aplica 'manter proporção'."""
        if self._updating:
            return
        self._updating = True
        try:
            sender = self.sender()
            if sender is self._w_pct_spin and self._orig_w > 0:
                scale = self._w_pct_spin.value() / 100.0
                new_w = self._orig_w * scale
                self._w_mm_spin.setValue(new_w)
                if self._lock_aspect_chk.isChecked():
                    # mesma % na outra dimensão
                    self._h_pct_spin.setValue(self._w_pct_spin.value())
                    # e mesmo fator de escala aplicado em mm
                    if self._orig_h > 0:
                        new_h = self._orig_h * scale
                        self._h_mm_spin.setValue(new_h)
            elif sender is self._h_pct_spin and self._orig_h > 0:
                scale = self._h_pct_spin.value() / 100.0
                new_h = self._orig_h * scale
                self._h_mm_spin.setValue(new_h)
                if self._lock_aspect_chk.isChecked():
                    self._w_pct_spin.setValue(self._h_pct_spin.value())
                    if self._orig_w > 0:
                        new_w = self._orig_w * scale
                        self._w_mm_spin.setValue(new_w)
        finally:
            self._updating = False

    def _on_move_clicked(self, dx_sign: int, dy_sign: int):
        """
        Move o objeto imediatamente, usando o passo configurado e
        chamando o callback fornecido pela janela principal.
        """
        if self._move_cb is None:
            return
        step = self._move_step_spin.value()
        dx = dx_sign * step
        dy = dy_sign * step
        self._move_cb(dx, dy)

    def values(self) -> tuple[float, float]:
        """
        Retorna as dimensões finais em mm.
        (Os campos em % já atualizam automaticamente os campos em mm.)
        """
        return self._w_mm_spin.value(), self._h_mm_spin.value()




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
        # Cor usada para destacar o objeto selecionado
        self.selection_color = QColor(Qt.GlobalColor.red)

        # Guarda polígonos da camada para exportar (PNG) e objetos para edição
        self._full_layer_polys_mm: List[List[tuple[float, float]]] | None = None
        self._full_layer_objects: List[GerberObject] | None = None
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
        act_sel_color = config_menu.addAction("Cor da seleção")
        act_sel_color.triggered.connect(self.on_choose_selection_color)
        

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
        # Cor inicial da seleção no preview
        self.preview_view.set_selection_color(self.selection_color)
        # Conecta sinal de exclusão de objeto vindo do preview
        self.preview_view.objectDeleteRequested.connect(self.on_delete_object)
        self.preview_view.objectEditRequested.connect(self.on_edit_object)
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
        self._full_layer_objects = None
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
        """
        Exporta a camada atual (objetos em mm) para um novo arquivo Gerber,
        em um formato RS-274X simplificado:

          - Unidade: milímetros (%MOMM*%)
          - Formato: FSLAX33Y33 (3 inteiros, 3 decimais)
          - Todos os objetos são convertidos em regiões sólidas (G36/G37).
        """
        if not self._full_layer_objects:
            QMessageBox.information(
                self,
                "Nada para exportar",
                "Não há nenhum objeto carregado/gerado para exportar.\n"
                "Crie um projeto, importe um Gerber e gere a camada completa.",
            )
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar como Gerber",
            "",
            "Arquivos Gerber (*.gbr *.ger *.pho *.art *.gb* *.gt* *.g*)",
        )
        if not path:
            return

        try:
            lines = objects_to_gerber(self._full_layer_objects)
            with open(path, "w", encoding="utf-8") as f:
                f.writelines(lines)
        except Exception:
            traceback.print_exc()
            QMessageBox.critical(
                self,
                "Erro ao exportar Gerber",
                "Ocorreu um erro ao gerar o arquivo Gerber exportado.\n"
                "Veja o terminal para detalhes.",
            )

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
        self._full_layer_objects = None
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
            # Gera lista de objetos Gerber (flash/região) em mm
            objects = build_layer_objects_mm(
                self.gerber_lines,
                self.macros,
                self.apertures_by_dcode,
                self.gerber_cfg,
            )
            self._full_layer_objects = objects

            # Deriva a lista de polígonos a partir dos objetos (para PNG, etc.)
            polys_mm: List[List[tuple[float, float]]] = [
                obj.polygon_mm for obj in objects
                if obj.polygon_mm and len(obj.polygon_mm) >= 3
            ]
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
            # Usa a nova interface baseada em objetos, se disponível
            if self._full_layer_objects:
                self.preview_view.set_objects(
                    self._full_layer_objects,
                    aperture_color=self.aperture_color,
                    bg_color=self.background_color,
                    preserve_view=False,  # primeira renderização: ajusta visão
                )
            else:
                # fallback (não deve ocorrer nesse fluxo normal)
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
        """
        Define a cor padrão das aberturas (objetos não selecionados).
        """
        color = QColorDialog.getColor(
            self.aperture_color,
            self,
            "Selecionar cor da abertura",
        )
        if not color.isValid():
            return
        self.aperture_color = color
        # Re-renderiza baseado em objetos se possível (mantém mapeamento)
        if self._full_layer_objects:
            self.preview_view.set_objects(
                self._full_layer_objects,
                aperture_color=self.aperture_color,
                bg_color=self.background_color,
                preserve_view=True,  # manter zoom/pan ao trocar cor
            )
        elif self._full_layer_polys_mm:
            self.preview_view.set_polygons(
                self._full_layer_polys_mm,
                preserve_view=True,
            )
    
    def on_choose_selection_color(self):
        """
        Define a cor usada para destacar o objeto selecionado.
        """
        color = QColorDialog.getColor(
            self.selection_color,
            self,
            "Selecionar cor da seleção",
        )
        if not color.isValid():
            return
        self.selection_color = color
        # Atualiza diretamente o preview (não é necessário re-render completo)
        self.preview_view.set_selection_color(self.selection_color)

    # ------------------------------------------------------------------ Edição: alterar propriedades do objeto
    def on_edit_object(self, index: int):
        """
        Edita propriedades geométricas de um objeto simples:
          - flash_circle  -> diâmetro
          - flash_rect    -> largura x altura
          - flash_oval    -> largura x altura

        Regiões (kind="region") também podem ser redimensionadas
        (largura x altura) por escala do polígono.
        """
        if self._full_layer_objects is None:
            print("[DEBUG edit] _full_layer_objects is None")
            return
        if not (0 <= index < len(self._full_layer_objects)):
            print(
                f"[DEBUG edit] index fora do intervalo: "
                f"idx={index}, n={len(self._full_layer_objects)}"
            )
            return

        obj = self._full_layer_objects[index]

        print(
            "[DEBUG edit] objeto selecionado:",
            f"idx={index}, kind={obj.kind}, dcode={obj.dcode}, "
            f"x={obj.x_mm}, y={obj.y_mm}, params={obj.params}",
        )

        # Diálogo específico por tipo
        if obj.kind == "flash_circle":
            cur_dia = float(obj.params.get("dia_mm", 0.0))
            new_dia, ok = QInputDialog.getDouble(
                self,
                "Editar diâmetro",
                "Novo diâmetro (mm):",
                cur_dia,
                0.001,
                1000.0,
                3,  # casas decimais
            )
            if not ok:
                return
            if new_dia <= 0:
                QMessageBox.warning(self, "Valor inválido",
                                    "O diâmetro deve ser maior que zero.")
                return

            obj.params["dia_mm"] = new_dia

            # Recalcula o polígono do círculo
            if obj.x_mm is None or obj.y_mm is None:
                return
            polys = circle_to_polys_mm(obj.x_mm, obj.y_mm, new_dia)
            obj.polygon_mm = polys[0]

        elif obj.kind in ("flash_rect", "flash_oval"):
            cur_w = float(obj.params.get("width_mm", 0.0))
            cur_h = float(obj.params.get("height_mm", 0.0))

            # Pergunta largura e altura na MESMA janela
            title = (
                "Editar abertura retangular"
                if obj.kind == "flash_rect"
                else "Editar abertura oval"
            )
            dlg = WidthHeightDialog(
                title=title,
                label_width="Largura (mm):",
                label_height="Altura (mm):",
                cur_w=cur_w,
                cur_h=cur_h,
                parent=self,
                move_callback=lambda dx, dy, o=obj: self._move_object(
                    o, dx, dy
                ),
            )
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return

            new_w, new_h = dlg.values()

            if new_w <= 0 or new_h <= 0:
                QMessageBox.warning(self, "Valores inválidos",
                                    "Largura e altura devem ser maiores que zero.")
                return

            obj.params["width_mm"] = new_w
            obj.params["height_mm"] = new_h

            if obj.x_mm is None or obj.y_mm is None:
                return
            if obj.kind == "flash_rect":
                polys = rect_to_polys_mm(obj.x_mm, obj.y_mm, new_w, new_h)
            else:  # flash_oval
                polys = oval_to_polys_mm(obj.x_mm, obj.y_mm, new_w, new_h)
            obj.polygon_mm = polys[0]
        elif obj.kind == "region":
            # Edição genérica de região: redimensiona largura x altura
            if not obj.polygon_mm or len(obj.polygon_mm) < 3:
                QMessageBox.information(
                    self,
                    "Não editável",
                    "Esta região não possui polígono válido para edição.",
                )
                return

            xs = [p[0] for p in obj.polygon_mm]
            ys = [p[1] for p in obj.polygon_mm]
            minx, maxx = min(xs), max(xs)
            miny, maxy = min(ys), max(ys)
            cur_w = maxx - minx
            cur_h = maxy - miny

            if cur_w <= 0 or cur_h <= 0:
                QMessageBox.information(
                    self,
                    "Não editável",
                    "Não foi possível determinar largura/altura da região.",
                )
                return

            # Centro geométrico aproximado (igual ao usado no parser)
            cx = (minx + maxx) / 2.0
            cy = (miny + maxy) / 2.0

            # Pergunta nova largura/altura na MESMA janela
            dlg = WidthHeightDialog(
                title="Editar tamanho da região",
                label_width="Largura (mm):",
                label_height="Altura (mm):",
                cur_w=cur_w,
                cur_h=cur_h,
                parent=self,
                # Habilita também o movimento para regiões
                move_callback=lambda dx, dy, o=obj: self._move_object(
                    o, dx, dy
                ),
            )
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return

            new_w, new_h = dlg.values()

            if new_w <= 0 or new_h <= 0:
                QMessageBox.warning(
                    self,
                    "Valores inválidos",
                    "Largura e altura devem ser maiores que zero.",
                )
                return

            sx = new_w / cur_w
            sy = new_h / cur_h

            new_poly = []
            for x, y in obj.polygon_mm:
                nx = cx + (x - cx) * sx
                ny = cy + (y - cy) * sy
                new_poly.append((nx, ny))

            # Garante fechamento explícito
            if new_poly and new_poly[0] != new_poly[-1]:
                new_poly.append(new_poly[0])

            obj.polygon_mm = new_poly

        else:
            # Por enquanto não editamos macros ou outros tipos
            QMessageBox.information(
                self,
                "Não editável",
                "Este tipo de objeto ainda não pode ser editado.",
            )
            return

        # Atualiza lista de polígonos a partir dos objetos
        self._full_layer_polys_mm = [
            o.polygon_mm
            for o in self._full_layer_objects
            if o.polygon_mm and len(o.polygon_mm) >= 3
        ]

        # Re-renderiza
        self.preview_view.set_objects(
            self._full_layer_objects,
            aperture_color=self.aperture_color,
            bg_color=self.background_color,
            preserve_view=True,  # manter zoom/pan após edição
        )
    # ------------------------------------------------------------------ Edição: exclusão de objeto
    def on_delete_object(self, index: int):
        """
        Remove um objeto Gerber (flash/região) da camada atual e
        re-renderiza o preview.

        Chamado quando o usuário escolhe "Excluir objeto" no menu de
        contexto da área de preview.
        """
        if self._full_layer_objects is None:
            return

        if not (0 <= index < len(self._full_layer_objects)):
            return

        obj = self._full_layer_objects[index]

        # Confirmação com o usuário
        desc = obj.kind
        if obj.dcode is not None:
            desc += f" (D{obj.dcode})"
        msg = (
            "Tem certeza que deseja excluir este objeto?\n\n"
            f"Tipo: {obj.kind}\n"
        )
        if obj.dcode is not None:
            msg += f"D-code: D{obj.dcode}\n"
        if obj.x_mm is not None and obj.y_mm is not None:
            msg += f"Posição: ({obj.x_mm:.6f}, {obj.y_mm:.6f}) mm\n"

        reply = QMessageBox.question(
            self,
            "Confirmar exclusão",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        # Remove o objeto da lista
        del self._full_layer_objects[index]

        # Reconstrói a lista de polígonos
        self._full_layer_polys_mm = [
            o.polygon_mm
            for o in self._full_layer_objects
            if o.polygon_mm and len(o.polygon_mm) >= 3
        ]

        # Se não sobrou nada, limpa a tela
        if not self._full_layer_objects:
            self._clear_preview()
            return

        # Caso contrário, re-renderiza a partir da lista atualizada
        self.preview_view.set_objects(
            self._full_layer_objects,
            aperture_color=self.aperture_color,
            bg_color=self.background_color,
            preserve_view=True,  # manter zoom/pan após exclusão
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
        if self._full_layer_objects:
            self.preview_view.set_objects(
                self._full_layer_objects,
                aperture_color=self.aperture_color,
                bg_color=self.background_color,
                preserve_view=True,  # manter zoom/pan ao trocar fundo
            )
        elif self._full_layer_polys_mm:
            self.preview_view.set_polygons(
                self._full_layer_polys_mm,
                preserve_view=True,
            )
        
    # ------------------------------------------------------------------ Utilitários de edição
    def _move_object(self, obj: GerberObject, dx: float, dy: float):
        """
        Aplica uma translação (dx, dy) em mm ao objeto e re-renderiza
        imediatamente o preview.
        Chamado pelos botões de seta do diálogo de edição.
        """
        # Atualiza posição do flash/centro, se existir
        if obj.x_mm is not None:
            obj.x_mm += dx
        if obj.y_mm is not None:
            obj.y_mm += dy

        # Translada o polígono associado
        if obj.polygon_mm:
            obj.polygon_mm = [
                (x + dx, y + dy) for (x, y) in obj.polygon_mm
            ]

        # Atualiza lista de polígonos a partir dos objetos atuais
        if self._full_layer_objects is not None:
            self._full_layer_polys_mm = [
                o.polygon_mm
                for o in self._full_layer_objects
                if o.polygon_mm and len(o.polygon_mm) >= 3
            ]
            # Re-renderiza preservando zoom/pan
            self.preview_view.set_objects(
                self._full_layer_objects,
                aperture_color=self.aperture_color,
                bg_color=self.background_color,
                preserve_view=True,
            )

    # ------------------------------------------------------------------ Utilitários
    def _clear_preview(self):
        self.preview_view._scene.clear()
        self.preview_view._polys_mm = []
        self.preview_view._objects = None
        self._current_pixmap = None
        self._full_layer_objects = None
        self.export_btn.setEnabled(False)
        self.reset_view_btn.setEnabled(False)


def run():
    app = QApplication(sys.argv)
    window = GerberMacroViewer()
    window.resize(900, 700)
    window.show()
    sys.exit(app.exec())
