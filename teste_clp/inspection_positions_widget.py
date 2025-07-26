# inspection_positions_widget.py
#
# Widget reutilizável para registrar posições de inspeção
# (c) 2025 – livre para uso sob MIT License

from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, List, Dict, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout,
    QHBoxLayout, QLabel, QMessageBox
)


# ----------------------------------------------------------------------
# Camada de modelo
# ----------------------------------------------------------------------
@dataclass
class InspectionPosition:
    name: str
    x:  float
    y2: float
    y1: float
    z:  float = 0.0
    meta: Dict[str, object] | None = None           # espaço para parâmetros extras

    def __str__(self) -> str:
        return f"{self.name} (X={self.x:.2f}, Y2={self.y2:.2f}, Y1={self.y1:.2f}, Z={self.z:.2f})"


class InspectionPositionListModel:
    """
    Classe mínima para guardar a lista de posições; não depende de Qt.
    """

    def __init__(self) -> None:
        self._positions: List[InspectionPosition] = []

    # ---- API pública -------------------------------------------------
    def add(self, pos: InspectionPosition) -> None:
        self._positions.append(pos)

    def remove(self, index: int) -> Optional[InspectionPosition]:
        if 0 <= index < len(self._positions):
            return self._positions.pop(index)
        return None

    def clear(self) -> None:
        self._positions.clear()

    def __iter__(self):
        return iter(self._positions)

    def __len__(self):
        return len(self._positions)

    def __getitem__(self, idx):
        return self._positions[idx]


# ----------------------------------------------------------------------
# Camada de interface
# ----------------------------------------------------------------------
class InspectionPositionsWidget(QWidget):
    """
    Widget que exibe e gerencia as “Posições de Inspeção”.

    Parâmetros do construtor:
        get_current_position: Callable[[], Dict[str,float]]
            Função/callable que devolve
            {'x':float,'y2':float,'y1':float,'z':float}.
            Pode ser None; nesse caso somente add_position(...) externo
            poderá alimentar a lista.

    Sinais:
        positionAdded(InspectionPosition)
        positionRemoved(InspectionPosition)
    """

    positionAdded = pyqtSignal(object)     # InspectionPosition
    positionRemoved = pyqtSignal(object)   # InspectionPosition

    def __init__(self,
                 get_current_position: Callable[[], Dict[str, float]] | None = None,
                 validate_position: Callable[[float,float,float,float], str | None] | None = None,
                 get_action_context: Callable[[], Dict[str,object] | None] | None = None,
                 parent=None) -> None:
        super().__init__(parent)
        self._get_current_position = get_current_position
        self._validate_position   = validate_position
        self._get_action_context  = get_action_context
        self._model = InspectionPositionListModel()
        self._build_ui()

    # ------------------------------------------------------------------
    # API pública para outras partes do programa
    # ------------------------------------------------------------------
    def add_position(self, pos: InspectionPosition) -> None:
        """Adiciona já com objeto pronto (útil para carregamento de arquivo)."""
        self._model.add(pos)
        self._append_item_to_list(pos)
        self.positionAdded.emit(pos)

    def remove_selected(self) -> Optional[InspectionPosition]:
        """Remove a posição atualmente destacada."""
        item = self.list_widget.currentItem()
        if not item:
            return None
        row = self.list_widget.row(item)
        removed = self._model.remove(row)
        if removed:
            self.list_widget.takeItem(row)
            self.positionRemoved.emit(removed)
        return removed

    def clear(self) -> None:
        self.list_widget.clear()
        self._model.clear()

    def positions(self) -> List[InspectionPosition]:
        """Devolve cópia da lista interna."""
        return list(self._model)

    # ------------------------------------------------------------------
    # Construção UI
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        v = QVBoxLayout(self)

        title = QLabel("Posições de Inspeção")
        title.setStyleSheet("font-weight:bold;")
        v.addWidget(title)

        # listagem
        self.list_widget = QListWidget()
        v.addWidget(self.list_widget, 1)

        # botões
        h = QHBoxLayout()
        self.btn_add = QPushButton("Adicionar posição atual")
        self.btn_remove = QPushButton("Remover posição")
        h.addWidget(self.btn_add)
        h.addWidget(self.btn_remove)
        v.addLayout(h)

        # conexões
        self.btn_add.clicked.connect(self._on_add_clicked)
        self.btn_remove.clicked.connect(self.remove_selected)

    # ------------------------------------------------------------------
    # Slots privados
    # ------------------------------------------------------------------
    def _on_add_clicked(self) -> None:
        """
        Obtém a posição atual através do callable injetado e solicita
        ao usuário um nome. Gera o objeto InspectionPosition e adiciona
        ao modelo/lista.
        """
        if not callable(self._get_current_position):
            QMessageBox.warning(self, "Indisponível",
                                "Função get_current_position não foi fornecida.")
            return

        try:
            pos_dict = self._get_current_position() or {}
            x = float(pos_dict.get("x", 0.0))
            y2 = float(pos_dict.get("y2", 0.0))
            y1 = float(pos_dict.get("y1", 0.0))
            z = float(pos_dict.get("z", 0.0))
        except Exception as exc:
            QMessageBox.critical(self, "Erro",
                                 f"Não foi possível obter a posição atual:\n{exc}")
            return

        # --- validação opcional ---------------------------------------
        if callable(self._validate_position):
            err = self._validate_position(x, y2, y1, z)
            if err:
                QMessageBox.warning(self, "Fora dos limites", err)
                return

        # Nome numérico sequencial: 1, 2, 3…
        name = str(len(self._model) + 1)

        # ---------------- anexa dados de ação -------------------------
        if callable(self._get_action_context):
            meta = self._get_action_context()
            if meta is None:
                QMessageBox.warning(self, "Ação não definida",
                                    "Selecione uma ação antes de adicionar o ponto.")
                return
        else:
            meta = None
        new_pos = InspectionPosition(name, x, y2, y1, z, meta=meta)
        self._model.add(new_pos)
        self._append_item_to_list(new_pos)
        self.positionAdded.emit(new_pos)

    def _append_item_to_list(self, pos: InspectionPosition) -> None:
        txt = (f"{pos.name}.  "
               f"X={pos.x:.2f}  Y2={pos.y2:.2f}  "
               f"Y1={pos.y1:.2f}  Z={pos.z:.2f}")
        if pos.meta and pos.meta.get("action") == "dot":
            txt += f"  [dot {pos.meta.get('dot_qty',1)}]"
        item = QListWidgetItem(txt)
        self.list_widget.addItem(item)


# ----------------------------------------------------------------------
# Test-drive rápido do widget isolado
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    import random
    from PyQt6.QtWidgets import QApplication

    # Simula um motion controller retornando coordenadas random
    def _mock_current_position():
        return {"x": random.uniform(0, 100),
                "y": random.uniform(0, 100),
                "z": random.uniform(0, 50)}

    app = QApplication(sys.argv)
    w = InspectionPositionsWidget(get_current_position=_mock_current_position)
    w.resize(400, 300)
    w.show()

    # Conecta sinais a prints
    w.positionAdded.connect(lambda p: print("ADDED:", p))
    w.positionRemoved.connect(lambda p: print("REMOVED:", p))

    sys.exit(app.exec())
