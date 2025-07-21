from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLineEdit, QSpinBox, QMessageBox
)
from PyQt6.QtCore import Qt
from dot_patterns import DotPatternManager


class DotPatternsDialog(QDialog):
    """
    Diálogo não-modal (always-on-top) para gerir padrões de Dot.
    """
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Window)
        self.setWindowModality(Qt.WindowModality.NonModal)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.setWindowTitle("Padrões de Dot")
        self.man = DotPatternManager()
        self._build_ui()
        self.man.patternsChanged.connect(self._refresh)
        self._refresh()

    def _build_ui(self):
        v = QVBoxLayout(self)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["ID", "Nome", "Qtd. gotas"])
        self.tree.setColumnWidth(1, 160)
        v.addWidget(self.tree, 1)
        # ---- formulário adicionar ---------------------------------
        h = QHBoxLayout()
        self.ed_name = QLineEdit(); self.ed_name.setPlaceholderText("Nome")
        self.sp_qty  = QSpinBox(); self.sp_qty.setRange(1, 1000)
        btn_add = QPushButton("Adicionar")
        btn_del = QPushButton("Excluir")
        h.addWidget(self.ed_name); h.addWidget(self.sp_qty)
        h.addWidget(btn_add); h.addWidget(btn_del)
        v.addLayout(h)
        btn_close = QPushButton("Fechar"); btn_close.clicked.connect(self.hide)
        v.addWidget(btn_close, 0, Qt.AlignmentFlag.AlignRight)
        # ---- sinais -------------------------------------------------
        btn_add.clicked.connect(self._add)
        btn_del.clicked.connect(self._delete)

    # ----------------------------- slots ----------------------------
    def _refresh(self):
        self.tree.clear()
        for p in self.man.patterns():
            QTreeWidgetItem(self.tree,
                            [str(p.id), p.name, str(p.qty)])

    def _add(self):
        name = self.ed_name.text().strip()
        qty  = self.sp_qty.value()
        if not name:
            QMessageBox.warning(self, "Nome vazio", "Digite um nome.")
            return
        self.man.add(name, qty)
        self.ed_name.clear(); self.sp_qty.setValue(1)

    def _delete(self):
        item = self.tree.currentItem()
        if not item: return
        dot_id = int(item.text(0))
        if QMessageBox.question(self, "Confirma",
                f"Excluir dot #{dot_id} ({item.text(1)})?",
                QMessageBox.StandardButton.Yes |
                QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No) \
           != QMessageBox.StandardButton.Yes:
            return
        self.man.remove(dot_id)
