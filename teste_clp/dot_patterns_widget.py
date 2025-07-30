from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem, QGroupBox, QVBoxLayout
from PyQt6.QtCore import Qt
from dot_patterns import DotPatternManager


class DotPatternsWidget(QGroupBox):
    """
    Widget compacto somente-leitura para mostrar os dots existentes.
    """
    def __init__(self, parent=None):
        super().__init__("Padrões de Dot", parent)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["ID", "Nome", "Qtd"])
        self.tree.setColumnWidth(1, 120)
        v = QVBoxLayout(self); v.addWidget(self.tree)
        self.man = DotPatternManager()
        self.man.patternsChanged.connect(self._refresh)
        self._refresh()

    # --------------------------------------------------------------
    #  API pública: padrão selecionado
    # --------------------------------------------------------------
    def current_pattern(self):
        """
        Devolve o DotPattern selecionado ou None.
        """
        item = self.tree.currentItem()
        if not item:
            return None
        try:
            dot_id = int(item.text(0))
        except ValueError:
            return None
        for p in self.man.patterns():
            if p.id == dot_id:
                return p
        return None

    def _refresh(self):
        self.tree.clear()
        for p in self.man.patterns():
            QTreeWidgetItem(self.tree, [str(p.id), p.name, str(p.qty)])

    # =============================================================
    #  Seleciona o padrão cujo `pat_id` coincide com o informado.
    #  Percorre o QTreeWidget e marca o item correspondente.
    # =============================================================
    def select_pattern_by_id(self, pat_id: int | str) -> None:
        try:
            pat_id = int(pat_id)
        except Exception:
            return

        tree = self.tree
        for i in range(tree.topLevelItemCount()):
            it = tree.topLevelItem(i)
            if int(it.text(0)) == pat_id:
                tree.setCurrentItem(it)
                tree.scrollToItem(it)
                break