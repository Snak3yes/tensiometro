"""
dot_action_selector_widget.py
-----------------------------
Widget compacto contendo quatro botões toggle que representam
as ações disponíveis para cada ponto do programa:
    • Fiducial           • Aplicar Dot
    • Leitura Barcode    • Inspeção Visual
Somente um pode ficar selecionado de cada vez.
"""
from PyQt6.QtWidgets import (
    QGroupBox, QHBoxLayout, QPushButton, QButtonGroup
)
from PyQt6.QtCore import pyqtSignal

class DotActionSelectorWidget(QGroupBox):
    """
    Grupo exclusivo de seleção de ação.
    Sinal:
        actionChanged(str)  – id interno: 'fiducial' | 'dot' | 'barcode' | 'inspect'
    """
    actionChanged = pyqtSignal(str)
    _ACTIONS = [
        ("fiducial", "Fiducial"),
        ("dot",      "Dot"),
        ("barcode",  "Barcode"),
        ("inspect",  "Inspeção")
    ]
    # ================================================================
    #  NOVO  –  permite selecionar programaticamente a ação
    # ================================================================
    def select_action(self, key: str) -> None:
        """
        Marca o botão correspondente a `key`
        e emite actionChanged(key).
        """
        for btn in self._group.buttons():
            # propriedade foi gravada no __init__ como "actionKey"
            if btn.property("actionKey") == key:
                btn.setChecked(True)
                # garante que o sinal seja disparado mesmo
                # quando a seleção veio de fora (duplo-clique)
                self.actionChanged.emit(key)
                break

    def __init__(self, parent=None):
        super().__init__("Ação Selecionada", parent)
        h = QHBoxLayout(self)
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        for idx,(key, label) in enumerate(self._ACTIONS):
            btn = QPushButton(label)
            btn.setCheckable(True)
            self._group.addButton(btn, idx)
            btn.setProperty("actionKey", key)
            h.addWidget(btn)
        # conecta
        self._group.idToggled.connect(self._on_toggled)
        # seleção inicial – nenhum
    # --------------------------------------------------------------
    def _on_toggled(self, _id:int, checked:bool):
        if not checked:
            return
        btn = self._group.button(_id)
        key = btn.property("actionKey")
        self.actionChanged.emit(key)
    # --------------------------------------------------------------
    def current_action(self) -> str | None:
        """Devolve a string da ação selecionada ou None."""
        btn = self._group.checkedButton()
        return btn.property("actionKey") if btn else None