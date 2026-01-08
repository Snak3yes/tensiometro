"""
Barra de Status do Hardware

Exibe status de conexão dos dispositivos (PLC, Tensiômetro, Câmera).
"""

import logging
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal, QPoint

logger = logging.getLogger(__name__)


class HardwareStatusBar(QWidget):
    """
    Barra de status do hardware na parte inferior da tela

    Mostra status de conexão de:
        - PLC (Controlador Lógico Programável)
        - Tensiômetro (Sensor de tensão)
        - Câmera (Câmera de inspeção)

    Sinais:
        status_clicked: Emitido ao clicar em um status de hardware
                        Argumento: "PLC", "TENSIO", ou "CAMERA"
    """

    status_clicked = pyqtSignal(str)  # Emitido ao clicar em status

    def __init__(self, parent=None):
        """Inicializa barra de status"""
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Configura interface"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(30)

        # Status PLC
        self.plc_label = QLabel("🔴 CLP: Desconectado")
        self.plc_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.plc_label.mousePressEvent = self._make_click_handler("PLC")
        layout.addWidget(self.plc_label)

        # Status Tensiômetro
        self.tensio_label = QLabel("🔴 Tensiômetro: Desconectado")
        self.tensio_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.tensio_label.mousePressEvent = self._make_click_handler("TENSIO")
        layout.addWidget(self.tensio_label)

        # Status Câmera
        self.camera_label = QLabel("🔴 Câmera: Desconectada")
        self.camera_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.camera_label.mousePressEvent = self._make_click_handler("CAMERA")
        layout.addWidget(self.camera_label)

        layout.addStretch()

        # Linha separadora
        self.setStyleSheet("""
            QWidget {
                border-top: 1px solid #E0E0E0;
                background-color: #F5F5F5;
            }
            QLabel {
                font-size: 12px;
                padding: 2px;
                color: #333333;
                background-color: #F5F5F5;
            }
            QLabel:hover {
                background-color: #E8E8E8;
                color: #000000;
            }
        """)

    def _make_click_handler(self, hardware: str):
        """
        Cria handler de clique para status

        Args:
            hardware: "PLC", "TENSIO", ou "CAMERA"

        Returns:
            Função handler
        """
        def handler(event):
            self.status_clicked.emit(hardware)
        return handler

    def update_plc_status(self, connected: bool):
        """
        Atualiza status PLC

        Args:
            connected: True se conectado
        """
        if connected:
            self.plc_label.setText("✅ CLP: Conectado")
        else:
            self.plc_label.setText("🔴 CLP: Desconectado")

    def update_tensio_status(self, connected: bool):
        """
        Atualiza status Tensiômetro

        Args:
            connected: True se conectado
        """
        if connected:
            self.tensio_label.setText("✅ Tensiômetro: Conectado")
        else:
            self.tensio_label.setText("🔴 Tensiômetro: Desconectado")

    def update_camera_status(self, connected: bool):
        """
        Atualiza status Câmera

        Args:
            connected: True se conectada
        """
        if connected:
            self.camera_label.setText("✅ Câmera: Conectada")
        else:
            self.camera_label.setText("🔴 Câmera: Desconectada")

    def update_all_status(self, plc: bool, tensio: bool, camera: bool):
        """
        Atualiza todos os status de uma vez

        Args:
            plc: Status PLC
            tensio: Status Tensiômetro
            camera: Status Câmera
        """
        self.update_plc_status(plc)
        self.update_tensio_status(tensio)
        self.update_camera_status(camera)
