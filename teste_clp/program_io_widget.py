from __future__ import annotations
from pathlib import Path
from typing import Protocol, runtime_checkable

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QGroupBox, QVBoxLayout, QPushButton,
    QFileDialog, QMessageBox
)

# ----------------------------------------------------------------------
# 1) Protocolo (interface) para o backend que realmente salva/carrega
# ----------------------------------------------------------------------
@runtime_checkable
class ProgramStorageBackend(Protocol):
    """
    Interface mínima que o backend de persistência deve expor.
      – InspectionPositionManager do projeto antigo já satisfaz.
    """
    def save_to_file(self, filename: str) -> bool: ...
    def load_from_file(self, filename: str) -> bool: ...


# ----------------------------------------------------------------------
# 2) Widget de UI
# ----------------------------------------------------------------------
class ProgramIOWidget(QWidget):
    """
    Painel “Salvar / Carregar” pronto para ser acoplado a qualquer
    aplicação.  Usa um backend que implemente ProgramStorageBackend.
    """

    fileSaved  = pyqtSignal(str)   # Caminho salvo
    fileLoaded = pyqtSignal(str)   # Caminho carregado

    def __init__(self,
                 backend: ProgramStorageBackend,
                 *,
                 file_filter: str = "Arquivos JSON (*.json)",
                 default_suffix: str = ".json",
                 default_dir: str | Path = "",
                 parent=None) -> None:
        super().__init__(parent)
        if not isinstance(backend, ProgramStorageBackend):
            raise TypeError(
                "backend não implementa ProgramStorageBackend (save_to_file / load_from_file)"
            )
        self._backend = backend
        self._file_filter   = file_filter
        self._default_suf   = default_suffix
        self._default_dir   = str(default_dir) if default_dir else ""
        self._build_ui()

    # ------------------------------------------------------------------
    # construção da interface
    # ------------------------------------------------------------------
    def _build_ui(self):
        grp = QGroupBox("Salvar / Carregar")
        v   = QVBoxLayout(grp)

        self.btn_save = QPushButton("Salvar Programa")
        self.btn_load = QPushButton("Carregar Programa")

        v.addWidget(self.btn_save)
        v.addWidget(self.btn_load)

        main = QVBoxLayout(self)
        main.addWidget(grp)
        main.addStretch()

        # conexões
        self.btn_save.clicked.connect(self._on_save_clicked)
        self.btn_load.clicked.connect(self._on_load_clicked)

    # ------------------------------------------------------------------
    # slots privados
    # ------------------------------------------------------------------
    def _on_save_clicked(self):
        fname, _ = QFileDialog.getSaveFileName(
            self, "Salvar Programa", "", self._file_filter
        )
        if not fname:
            return
        # garante extensão correta
        if self._default_suf and not fname.lower().endswith(self._default_suf):
            fname += self._default_suf

        ok = False
        try:
            ok = self._backend.save_to_file(fname)
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Falha ao salvar:\n{exc}")
            return

        if ok:
            self.fileSaved.emit(fname)
        else:
            QMessageBox.critical(self, "Erro", "Falha ao salvar o programa")

    def _on_load_clicked(self):
        fname, _ = QFileDialog.getOpenFileName(
            self, "Carregar Programa",
            self._default_dir,
            self._file_filter
        )
        if not fname:
            return

        ok = False
        try:
            ok = self._backend.load_from_file(fname)
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Falha ao carregar:\n{exc}")
            return

        if ok:
            self.fileLoaded.emit(fname)
        else:
            QMessageBox.critical(self, "Erro", "Falha ao carregar o programa")


# ----------------------------------------------------------------------
# 3) Demonstração rápida
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import sys, json, tempfile
    from dataclasses import dataclass, asdict
    from PyQt6.QtWidgets import QApplication, QLabel

    # Backend de exemplo ----------------------------------------------
    class _DummyBackend:
        """Exemplo simples que salva/carrega um dict em JSON."""
        def __init__(self):
            self.data = {"positions": [], "sequences": []}

        def save_to_file(self, filename: str) -> bool:
            Path(filename).write_text(json.dumps(self.data, indent=2),
                                      encoding="utf-8")
            return True

        def load_from_file(self, filename: str) -> bool:
            self.data = json.loads(Path(filename).read_text(encoding="utf-8"))
            return True

    # Qt demo ----------------------------------------------------------
    app = QApplication(sys.argv)
    backend = _DummyBackend()
    widget  = ProgramIOWidget(backend)
    widget.resize(220, 120)

    # Mostra em label onde salvou/carregou
    info = QLabel()
    def _saved(f):  info.setText(f"Salvo: {Path(f).name}")
    def _loaded(f): info.setText(f"Carregado: {Path(f).name}")
    widget.fileSaved.connect(_saved)
    widget.fileLoaded.connect(_loaded)

    wrapper = QWidget()
    lay = QVBoxLayout(wrapper); lay.addWidget(widget); lay.addWidget(info)
    wrapper.show()
    sys.exit(app.exec())
