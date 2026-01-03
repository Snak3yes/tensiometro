from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QInputDialog, QMessageBox
)
from PyQt6.QtCore import Qt
from aoi_lib.config_manager import AOIConfigManager
import logging

logger = logging.getLogger(__name__)
class PositionRegistryWidget(QWidget):
    """Widget for showing registered positions"""
    def __init__(self, controller, cfg: AOIConfigManager, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.cfg        = cfg
        self.cfg        = cfg
        self.positions  = []
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Registered Positions")
        title_font = QFont()
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Registered positions table
        self.positions_table = QTableWidget(0, 3)
        self.positions_table.setHorizontalHeaderLabels(["Name", "X (mm)", "Y (mm)"])
        self.positions_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.positions_table)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.delete_button = QPushButton("Delete Selected")
        self.delete_button.clicked.connect(self.delete_position)
        
        self.create_sequence_btn = QPushButton("Create Sequence")
        
        buttons_layout.addWidget(self.delete_button)
        buttons_layout.addWidget(self.create_sequence_btn)
        
        layout.addLayout(buttons_layout)
        
    def add_position(self, name, x, y, z=0.0, image=None):
        """Add a position to the registry"""
        # Create position object
        position = {
            'name': name,
            'x': x,
            'y': y,
            'z': z,
            'image': image,
        }
        
        # Add to internal list
        self.positions.append(position)
        
        # Add to table
        row = self.positions_table.rowCount()
        self.positions_table.insertRow(row)
        self.positions_table.setItem(row, 0, QTableWidgetItem(name))
        self.positions_table.setItem(row, 1, QTableWidgetItem(f"{x:.3f}"))
        self.positions_table.setItem(row, 2, QTableWidgetItem(f"{y:.3f}"))
        
    def delete_position(self):
        """Delete selected position"""
        selected_rows = self.positions_table.selectedItems()
        if not selected_rows:
            return
            
        row = selected_rows[0].row()
        if row >= 0 and row < len(self.positions):
            del self.positions[row]
            self.positions_table.removeRow(row)
            
    def clear_positions(self):
        """Clear all positions"""
        self.positions.clear()
        while self.positions_table.rowCount() > 0:
            self.positions_table.removeRow(0)



