"""
Janela não-modal que converte um arquivo *.m1 ⇆ *.m2
para a mesa atualmente selecionada.

Fluxo para o operador
1. Estar na aba Mesa 1 ou Mesa 2.
2. Menu Programa ▸ Converter programa da outra mesa…
3. Clicar “Selecionar programa…”.
     – se estiver na Mesa 1 só aparecem *.m2;
       se Mesa 2, apenas *.m1.
4. Posicionar a câmera sobre o Fiducial 1 e clicar
   “Definir Fiducial 1”; fazer o mesmo para Fiducial 2.
5. “Converter” aplica translação + pequena correção
   de escala (proporcional entre os 2 fiduciais).
6. “Salvar” grava o novo arquivo com sufixo correto
   na pasta do projecto actual ou onde o utilizador escolher.
"""
from __future__ import annotations
from pathlib import Path
import json, math, typing as _t

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal


class ProgramConverterDialog(QWidget):
    """
    Dialogo perene (não modal, sempre-on-top) que converte
    programas entre as mesas.
    """

    # sinal opcional: novo programa carregado na aba
    programConverted = pyqtSignal(list)        # lista[dict] já convertida

    def __init__(self, ctrl, mesa_tab):
        """
        ctrl      = MultiAxisMotorController (janela principal)
        mesa_tab  = TableProgramTab actualmente visível
        """
        super().__init__(parent=None)   # ← sem parent → janela top-level

        # Torna-a uma janela independente sempre no topo
        flags = (Qt.WindowType.Window |
                 Qt.WindowType.WindowStaysOnTopHint |
                 Qt.WindowType.CustomizeWindowHint |
                 Qt.WindowType.WindowCloseButtonHint)
        self.setWindowFlags(flags)

        self.setWindowTitle(f"Conversor de Programa – Mesa {mesa_tab.mesa}")
        self.ctrl      = ctrl
        self.mesa_tab  = mesa_tab
        self._file_in  : Path | None = None
        self._prog_raw : list[dict] | None = None
        self._fid_old  : list[tuple[float,float]] = []   # coordenadas no arquivo
        self._fid_new  : list[tuple[int,int]]     = []   # pulsos medidos
        self._build_ui()

    # -----------------------------------------------------------------
    def _build_ui(self):
        v = QVBoxLayout(self)

        self.lbl_file = QLabel("Nenhum programa seleccionado")
        self.lbl_f1   = QLabel("Fiducial 1: —")
        self.lbl_f2   = QLabel("Fiducial 2: —")

        btn_sel  = QPushButton("Selecionar programa…")
        btn_f1   = QPushButton("Definir Fiducial 1")
        btn_f2   = QPushButton("Definir Fiducial 2")
        btn_conv = QPushButton("Converter")
        btn_save = QPushButton("Salvar")

        for b in (btn_conv, btn_save):
            b.setEnabled(False)

        self._btn_conv = btn_conv
        self._btn_save = btn_save

        v.addWidget(self.lbl_file)
        v.addSpacing(10)

        h1 = QHBoxLayout(); h1.addWidget(btn_sel); h1.addStretch()
        v.addLayout(h1)

        v.addSpacing(15)
        v.addWidget(self.lbl_f1)
        v.addWidget(self.lbl_f2)
        h2 = QHBoxLayout(); h2.addWidget(btn_f1); h2.addWidget(btn_f2)
        v.addLayout(h2)

        v.addSpacing(15)
        h3 = QHBoxLayout(); h3.addWidget(btn_conv); h3.addWidget(btn_save)
        v.addLayout(h3)
        v.addStretch()

        # conexões ----------------------------------------------------
        btn_sel.clicked.connect(self._select_program)
        btn_f1.clicked.connect(lambda: self._capture_fid(1))
        btn_f2.clicked.connect(lambda: self._capture_fid(2))
        btn_conv.clicked.connect(self._convert)
        btn_save.clicked.connect(self._save)

    # -----------------------------------------------------------------
    #  Passo 1 – escolher o arquivo da outra mesa
    # -----------------------------------------------------------------
    def _select_program(self):
        # mesa actual
        mesa_atual = self.mesa_tab.mesa          # 1 ou 2
        other_mesa = 2 if mesa_atual == 1 else 1
        filter_str = f"Programa Mesa {other_mesa} (*.m{other_mesa})"
        fname, _ = QFileDialog.getOpenFileName(self,
                                               "Escolher programa da outra mesa",
                                               str(self.ctrl.projects_dir),
                                               filter_str)
        if not fname:
            return
        self._file_in = Path(fname)
        try:
            self._prog_raw = json.loads(Path(fname).read_text(encoding="utf-8"))
        except Exception as exc:
            QMessageBox.critical(self, "Erro",
                                 f"Falha ao abrir:\n{exc}")
            return

        # procura dois fiduciais no programa
        fids = [(p["x"], p["y"]) for p in self._prog_raw
                if (p.get("meta") or {}).get("action") == "fiducial"]
        if len(fids) < 2:
            QMessageBox.warning(self, "Fiduciais insuficientes",
                                "O programa da outra mesa precisa ter "
                                "pelo menos 2 pontos de fiducial.")
            self._prog_raw = None
            return
        self._fid_old = fids[:2]       # usa os dois primeiros
        self.lbl_file.setText(f"Programa: {self._file_in.name} "
                              f"(fid1={self._fid_old[0]}, "
                              f"fid2={self._fid_old[1]})")
        self._check_ready()

    # -----------------------------------------------------------------
    #  Passo 2 – capturar coords em pulsos do ponto sob a câmera
    # -----------------------------------------------------------------
    def _capture_fid(self, idx: int):
        pos = self.ctrl._get_current_position_dict()
        x_p = pos["x"]
        y_p = pos["y1"] if self.mesa_tab.y_axis == "Y1" else pos["y2"]
        if idx == 1:
            if len(self._fid_new) >= 1:
                self._fid_new[0] = (x_p, y_p)
            else:
                self._fid_new.insert(0, (x_p, y_p))
            self.lbl_f1.setText(f"Fiducial 1: X={x_p}  Y={y_p}")
        else:
            if len(self._fid_new) == 0:
                self._fid_new.append((0, 0))      # placeholder
            if len(self._fid_new) >= 2:
                self._fid_new[1] = (x_p, y_p)
            else:
                self._fid_new.append((x_p, y_p))
            self.lbl_f2.setText(f"Fiducial 2: X={x_p}  Y={y_p}")
        self._check_ready()

    # -----------------------------------------------------------------
    def _check_ready(self):
        ready = self._prog_raw is not None and len(self._fid_new) >= 2
        self._btn_conv.setEnabled(ready)

    # -----------------------------------------------------------------
    #  Passo 3 – converter
    # -----------------------------------------------------------------
    def _convert(self):
        if not self._btn_conv.isEnabled():
            return
        f1_old, f2_old = self._fid_old
        f1_new, f2_new = self._fid_new

        # escala (pequenas variações de distância)
        dist_old = math.hypot(f2_old[0]-f1_old[0], f2_old[1]-f1_old[1])
        dist_new = math.hypot(f2_new[0]-f1_new[0], f2_new[1]-f1_new[1])
        scale = dist_new/dist_old if dist_old else 1.0

        self._prog_conv : list[dict] = []
        for p in self._prog_raw:
            dx = p["x"] - f1_old[0]
            dy = p["y"] - f1_old[1]
            new_x = f1_new[0] + dx*scale
            new_y = f1_new[1] + dy*scale
            # troca campo y1 / y2 conforme mesa destino
            if self.mesa_tab.y_axis == "Y1":
                y1, y2 = new_y, 0.0
            else:
                y1, y2 = 0.0, new_y
            self._prog_conv.append({
                "name": p["name"],
                "x": new_x,
                "y": new_y,
                "z": p["z"],
                "meta": p.get("meta", {})
            })
        QMessageBox.information(self, "Conversão",
                                "Programa convertido.\n"
                                "Clique “Salvar” para guardar.")
        self._btn_save.setEnabled(True)

        # carrega na aba actual
        self._load_into_current_tab()

    def _load_into_current_tab(self):
        """Preenche a lista de posições da mesa destino."""
        if not self._prog_conv:
            return
        w = self.mesa_tab.inspect_widget
        w.blockSignals(True)
        try:
            w.clear()
            for d in self._prog_conv:
                y1 = d["y"] if self.mesa_tab.y_axis == "Y1" else 0.0
                y2 = d["y"] if self.mesa_tab.y_axis == "Y2" else 0.0
                from sequence_control import InspectionPosition
                cam_meta = d.get("meta", {})          # mantém meta original
                pos = InspectionPosition(
                    name=d["name"],
                    x=d["x"],
                    y1=y1, y2=y2,
                    z=d["z"],
                    camera_params=cam_meta)           # <-- parâmetro correto

                # ---- compatibilidade: vários widgets ainda usam .meta
                setattr(pos, "meta", cam_meta)
                w.add_position(pos)
        finally:
            w.blockSignals(False)
        # actualiza sequence widget
        self.mesa_tab.seq_widget.set_positions(self.mesa_tab._to_model())

    # -----------------------------------------------------------------
    #  Passo 4 – salvar
    # -----------------------------------------------------------------
    def _default_save_path(self) -> Path:
        base = self.ctrl.projects_dir
        orig = self._file_in.stem if self._file_in else "programa"
        new_suffix = ".m1" if self.mesa_tab.mesa == 1 else ".m2"
        return base / f"{orig}{new_suffix}"

    def _save(self):
        if not self._prog_conv:
            return
        suggested = str(self._default_save_path())
        fname, _ = QFileDialog.getSaveFileName(self, "Salvar programa convertido",
                                               suggested,
                                               "Programas (*.m1 *.m2)")
        if not fname:
            return
        # força extensão certa
        if self.mesa_tab.mesa == 1 and not fname.endswith(".m1"):
            fname += ".m1"
        if self.mesa_tab.mesa == 2 and not fname.endswith(".m2"):
            fname += ".m2"
        try:
            Path(fname).write_text(json.dumps(self._prog_conv, indent=2),
                                   encoding="utf-8")
        except Exception as exc:
            QMessageBox.critical(self, "Erro", str(exc))
            return
        QMessageBox.information(self, "Salvar",
                                f"Programa gravado em:\n{fname}")
        # actualiza ProgramIOWidget da mesa (para permitir salvar de novo)
        self.mesa_tab.prog_widget._last_file = fname

    # -----------------------------------------------------------------
    def closeEvent(self, ev):
        """Mantém a instância viva (não destrói)"""
        ev.ignore()
        self.hide()