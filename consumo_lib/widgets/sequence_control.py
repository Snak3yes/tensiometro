from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QSpinBox, QCheckBox, QMessageBox,
    QGroupBox, QGridLayout, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from aoi_lib.config_manager import AOIConfigManager
import logging

# Design System
from consumo_lib.ui.widget_standards import StandardButton

logger = logging.getLogger(__name__)
class SequenceControlWidget(QWidget):
    """Widget para controlar a execução da sequência"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        
        # Grupo de sequência
        sequence_group = QGroupBox("Controle de Sequência")
        sequence_layout = QGridLayout()
        
        # Nome da sequência
        sequence_layout.addWidget(QLabel("Nome:"), 0, 0)
        self.sequence_name = QLineEdit("Sequência PCB")
        sequence_layout.addWidget(self.sequence_name, 0, 1)
        
        # Botões de controle
        self.create_sequence_btn = StandardButton("Criar Sequência")
        self.run_sequence_btn = StandardButton("Executar Sequência", variant="primary")
        self.stop_sequence_btn = StandardButton("Parar")
        self.stop_sequence_btn.setEnabled(False)
        
        sequence_layout.addWidget(self.create_sequence_btn, 1, 0)
        sequence_layout.addWidget(self.run_sequence_btn, 1, 1)
        sequence_layout.addWidget(self.stop_sequence_btn, 2, 0, 1, 2)
        
        # Status
        sequence_layout.addWidget(QLabel("Status:"), 3, 0)
        self.sequence_status = QLabel("Pronto")
        sequence_layout.addWidget(self.sequence_status, 3, 1)
        
        sequence_group.setLayout(sequence_layout)
        
        # Grupo de arquivo
        file_group = QGroupBox("Salvar/Carregar")
        file_layout = QVBoxLayout()
        self.save_btn = StandardButton("Salvar Programa (JSON)", variant="primary")
        self.load_btn = StandardButton("Carregar Programa (JSON)")
        self.save_gcode_btn = StandardButton("Exportar para G-CODE")
        self.load_gcode_btn = StandardButton("Importar de G-CODE")
        file_layout.addWidget(self.save_btn)
        file_layout.addWidget(self.load_btn)
        file_layout.addWidget(self.save_gcode_btn)
        file_layout.addWidget(self.load_gcode_btn)
        
        file_group.setLayout(file_layout)
        
        self.layout.addWidget(sequence_group)
        self.layout.addWidget(file_group)
        self.layout.addStretch()



