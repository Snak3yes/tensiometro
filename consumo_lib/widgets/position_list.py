from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QInputDialog, QMessageBox, QLabel
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from aoi_lib import InspectionPosition
import logging

logger = logging.getLogger(__name__)
class PositionListWidget(QWidget):
    """Widget para gerenciar lista de posições"""
    position_selected = pyqtSignal(object)  # Emite a posição selecionada
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        
        # Título
        title_label = QLabel("Posições de Inspeção")
        title_font = QFont()
        title_font.setBold(True)
        title_label.setFont(title_font)
        
        # Lista de posições
        self.positions_list = QListWidget()
        self.positions_list.currentItemChanged.connect(self.on_position_selected)
        
        # Botões
        buttons_layout = QHBoxLayout()
        self.add_position_btn = QPushButton("Adicionar Posição Atual")
        self.remove_position_btn = QPushButton("Remover")
        buttons_layout.addWidget(self.add_position_btn)
        buttons_layout.addWidget(self.remove_position_btn)
        
        self.layout.addWidget(title_label)
        self.layout.addWidget(self.positions_list)
        self.layout.addLayout(buttons_layout)
        
        # Mapeia id(QListWidgetItem) ➜ InspectionPosition.
        # QListWidgetItem NÃO é hashable, portanto usamos id(item).
        self.positions: dict[int, InspectionPosition] = {}
        
    def add_position(self, position: InspectionPosition):
        """Adiciona uma posição à lista"""
        item_text = f"{position.name} ({position.x:.2f}, {position.y:.2f}, {getattr(position,'z',0.0):.2f})"
        item = QListWidgetItem(item_text)
        self.positions_list.addItem(item)
        self.positions[id(item)] = position
        
    def remove_selected_position(self):
        """Remove a posição selecionada"""
        current_item = self.positions_list.currentItem()
        if current_item:
            position = self.positions.pop(id(current_item))
            row = self.positions_list.row(current_item)
            self.positions_list.takeItem(row)
            return position
        return None
        
    def clear_positions(self):
        """Limpa todas as posições"""
        self.positions_list.clear()
        self.positions = {}
        
    def get_all_positions(self):
        """Retorna todas as posições"""
        return list(self.positions.values())
        
    def on_position_selected(self, current, previous):
        """Manipula evento de seleção de posição"""
        if current:
            pos = self.positions.get(id(current))
            if pos:
                self.position_selected.emit(pos)



