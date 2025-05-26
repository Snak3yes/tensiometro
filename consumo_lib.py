import sys
import cv2
import os
import time
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QLabel, QGroupBox, QGridLayout, QLineEdit, 
                            QComboBox, QListWidget, QCheckBox, QListWidgetItem, QFileDialog, QMessageBox, QTabWidget,
                            QSplitter, QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QInputDialog,
                            QProgressDialog)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QEvent
from PyQt6.QtGui import QPixmap, QImage, QFont, QAction, QDoubleValidator

from aoi_lib import CNCAOIController, InspectionPosition
from grbl_streamer import GrblStreamer
from aoi_lib.utils.move_task import MoveTaskThread
from aoi_lib.config_manager import AOIConfigManager, SettingsDialog
from dataclasses import dataclass

import logging



logger = logging.getLogger("consumo_lib")
logger.setLevel(logging.DEBUG)
# Se necessário, adicione um handler:
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

class ImageViewerWidget(QWidget):
    """Widget para exibir imagens capturadas pela câmera"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        
        # Label para exibir a imagemgit
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setText("Nenhuma imagem capturada")
        self.image_label.setStyleSheet("border: 1px solid gray; background-color: #f0f0f0;")
        self.image_label.setMinimumSize(400, 300)
        
        # Informações da imagem
        self.info_label = QLabel("Informações da imagem:")
        
        self.layout.addWidget(self.image_label)
        self.layout.addWidget(self.info_label)
        
    def display_image(self, image, info_text=None):
        """Mostra uma imagem no widget"""
        if image is None:
            self.image_label.setText("Imagem inválida")
            return
            
        # Converte imagem OpenCV para QPixmap
        h, w, c = image.shape
        bytes_per_line = 3 * w
        q_img = QImage(image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(q_img)
        
        # Redimensiona se for muito grande
        if pixmap.width() > 800 or pixmap.height() > 600:
            pixmap = pixmap.scaled(800, 600, Qt.AspectRatioMode.KeepAspectRatio)
            
        self.image_label.setPixmap(pixmap)
        
        # Atualiza informações
        if info_text:
            self.info_label.setText(info_text)
        else:
            self.info_label.setText(f"Imagem: {w}x{h}px")

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
        item_text = f"{position.name} ({position.x:.2f}, {position.y:.2f})"
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
        self.create_sequence_btn = QPushButton("Criar Sequência")
        self.run_sequence_btn = QPushButton("Executar Sequência")
        self.stop_sequence_btn = QPushButton("Parar")
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
        self.save_btn = QPushButton("Salvar Programa (JSON)")
        self.load_btn = QPushButton("Carregar Programa (JSON)")
        self.save_gcode_btn = QPushButton("Exportar para G-CODE")
        self.load_gcode_btn = QPushButton("Importar de G-CODE")
        file_layout.addWidget(self.save_btn)
        file_layout.addWidget(self.load_btn)
        file_layout.addWidget(self.save_gcode_btn)
        file_layout.addWidget(self.load_gcode_btn)
        
        file_group.setLayout(file_layout)
        
        self.layout.addWidget(sequence_group)
        self.layout.addWidget(file_group)
        self.layout.addStretch()

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
        
    def add_position(self, name, x, y, image=None):
        """Add a position to the registry"""
        # Create position object
        position = {
            'name': name,
            'x': x,
            'y': y,
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

class CameraPreviewWidget(QWidget):
    """Widget for displaying camera preview and capturing images"""
    image_captured = pyqtSignal(object, str)  # Emits the captured image and position name
    
    def __init__(self, controller, cfg: AOIConfigManager, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.current_image = None
        self.preview_timer = QTimer(self)
        self.preview_timer.timeout.connect(self.update_preview)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Preview area - Ajustar para usar mais espaço
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setText("Camera Preview")
        self.image_label.setStyleSheet("border: 1px solid gray; background-color: #f0f0f0;")
        self.image_label.setMinimumSize(600, 450)  # Aumentar tamanho mínimo
        
        # Camera controls
        controls_layout = QHBoxLayout()
        self.start_preview_btn = QPushButton("Start Preview")
        self.start_preview_btn.clicked.connect(self.start_preview)
        self.stop_preview_btn = QPushButton("Stop Preview")
        self.stop_preview_btn.clicked.connect(self.stop_preview)
        self.stop_preview_btn.setEnabled(False)
        controls_layout.addWidget(self.start_preview_btn)
        controls_layout.addWidget(self.stop_preview_btn)
        
        # Position capture layout
        capture_layout = QHBoxLayout()
        self.position_name = QLineEdit()
        self.position_name.setPlaceholderText("Position Name")
        self.capture_button = QPushButton("Capture Image & Register Position")
        self.capture_button.clicked.connect(self.capture_image)
        capture_layout.addWidget(self.position_name)
        capture_layout.addWidget(self.capture_button)
        
        # Adicionar elementos ao layout principal
        layout.addWidget(self.image_label, 1)  # Proporção 1 para permitir expansão
        layout.addLayout(controls_layout)
        layout.addLayout(capture_layout)
        
    def start_preview(self):
        """Start camera preview"""
        if not hasattr(self.controller.camera, 'is_connected') or not self.controller.camera.is_connected:
            QMessageBox.warning(self, "Error", "Camera not connected")
            return
        self.preview_timer.start(100)  # Update every 100ms
        self.start_preview_btn.setEnabled(False)
        self.stop_preview_btn.setEnabled(True)
        
    def stop_preview(self):
        """Stop camera preview"""
        self.preview_timer.stop()
        self.start_preview_btn.setEnabled(True)
        self.stop_preview_btn.setEnabled(False)
        
    def update_preview(self):
        """Update the camera preview"""
        try:
            image = self.controller.camera.capture()
            if image is not None:
                self.display_image(image)
                self.current_image = image
        except Exception as e:
            print(f"Error updating preview: {e}")
            self.stop_preview()
            
    def capture_image(self):
        """Capture an image and emit signal with position name"""
        if not hasattr(self.controller.camera, 'is_connected') or not self.controller.camera.is_connected:
            QMessageBox.warning(self, "Error", "Camera not connected")
            return
        position_name = self.position_name.text()
        if not position_name:
            QMessageBox.warning(self, "Error", "Please enter a position name")
            return
        try:
            image = self.controller.camera.capture()
            if image is not None:
                self.display_image(image)
                self.current_image = image
                self.image_captured.emit(image, position_name)
                self.position_name.clear()
            else:
                QMessageBox.warning(self, "Error", "Failed to capture image")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Capture error: {e}")
            
    def display_image(self, image):
        """Display an image in the preview area with a crosshair in the center"""
        if image is None:
            return
            
        # Criar uma cópia da imagem para não modificar a original
        display_img = image.copy()
        
        # Desenhar a cruz vermelha no centro
        h, w, _ = display_img.shape
        center_x, center_y = w // 2, h // 2
        
        # Parâmetros da cruz
        color = (0, 0, 255)  # Vermelho em BGR
        thickness = 2
        length = min(w, h) // 20  # 5% do tamanho da dimensão menor
        
        # Desenhar a cruz
        # Linha horizontal
        cv2.line(display_img, 
                (center_x - length, center_y), 
                (center_x + length, center_y), 
                color, thickness)
        # Linha vertical
        cv2.line(display_img, 
                (center_x, center_y - length), 
                (center_x, center_y + length), 
                color, thickness)
                
        # Converter a imagem OpenCV para QPixmap
        h, w, c = display_img.shape
        bytes_per_line = 3 * w
        q_img = QImage(display_img.data, w, h, bytes_per_line, QImage.Format.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(q_img)
        
        # Obter tamanho do widget de exibição
        label_width = self.image_label.width()
        label_height = self.image_label.height()
        
        # Redimensionar a imagem para caber no espaço disponível mantendo proporções
        pixmap = pixmap.scaled(label_width, label_height, 
                           Qt.AspectRatioMode.KeepAspectRatio, 
                           Qt.TransformationMode.SmoothTransformation)
                           
        self.image_label.setPixmap(pixmap)
        
    def resizeEvent(self, event):
        """Override do evento de redimensionamento para ajustar a imagem quando o widget for redimensionado"""
        super().resizeEvent(event)
        if self.current_image is not None:
            self.display_image(self.current_image)

class MovementControlWidget(QWidget):
    """Widget for controlling CNC movement (jog)"""
    def __init__(self, controller, cfg: AOIConfigManager, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.cfg        = cfg 
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Group box for movement controls
        movement_group = QGroupBox("Movement Controls")
        movement_layout = QGridLayout()
        
        # Directional control buttons
        self.up_button = QPushButton("↑")
        self.down_button = QPushButton("↓")
        self.left_button = QPushButton("←")
        self.right_button = QPushButton("→")
        
        # Style the buttons
        for btn in [self.up_button, self.down_button, self.left_button, self.right_button]:
            btn.setMinimumSize(50, 50)
            font = QFont()
            font.setBold(True)
            font.setPointSize(16)
            btn.setFont(font)
        
        # Connect press/release events for continuous movement
        self.up_button.pressed.connect(lambda: self._on_direction_press("Y",  1))
        self.up_button.released.connect(self._on_direction_release)
        self.down_button.pressed.connect(lambda: self._on_direction_press("Y", -1))
        self.down_button.released.connect(self._on_direction_release)
        self.left_button.pressed.connect(lambda: self._on_direction_press("X", -1))
        self.left_button.released.connect(self._on_direction_release)
        self.right_button.pressed.connect(lambda: self._on_direction_press("X", 1))
        self.right_button.released.connect(self._on_direction_release)

        # --------- NOVOS BOTÕES Z -----------------
        self.z_up_button   = QPushButton("Z+")
        self.z_down_button = QPushButton("Z-")
        for zbtn in (self.z_up_button, self.z_down_button):
            zbtn.setMinimumSize(50, 30)
        self.z_up_button.pressed.connect(  lambda: self._on_direction_press("Z",  1))
        self.z_up_button.released.connect(self._on_direction_release)
        self.z_down_button.pressed.connect(lambda: self._on_direction_press("Z", -1))
        self.z_down_button.released.connect(self._on_direction_release)
        
        # Add buttons to grid
        movement_layout.addWidget(self.up_button, 0, 1)
        movement_layout.addWidget(self.left_button, 1, 0)
        movement_layout.addWidget(self.right_button, 1, 2)
        movement_layout.addWidget(self.down_button, 2, 1)

        # Coloca Z+ acima de STOP e Z- abaixo
        movement_layout.addWidget(self.z_up_button,   0, 3)
        movement_layout.addWidget(self.z_down_button, 2, 3)

        # Botão de Emergency Stop / Reset
        self.emergency_stop_button = QPushButton("STOP")
        self.emergency_stop_button.setCheckable(True) # Torna o botão toggle
        self.emergency_stop_button.setMinimumSize(100, 40)
        font_stop = QFont()
        font_stop.setBold(True)
        self.emergency_stop_button.setFont(font_stop)
        # Estilo inicial (vermelho)
        self.emergency_stop_button.setStyleSheet("background-color: red; color: white;")
        self.emergency_stop_button.toggled.connect(self.on_emergency_stop_toggle) # Conecta ao handler

        # Adiciona o botão ao layout, centralizado abaixo dos direcionais
        movement_layout.addWidget(self.emergency_stop_button, 1, 1, Qt.AlignmentFlag.AlignCenter) # Coloca no centro (linha 1, coluna 1)
        
        # Step size and feed rate controls
        step_layout = QHBoxLayout()
        step_layout.addWidget(QLabel("Step Size:"))
        # ---------- STEP SIZE ---------------
        default_step = self.cfg.get("movement", "step_size", default=10.0)
        self.step_size = QLineEdit(f"{default_step}")
        # ▸ VALIDAÇÃO numérica (>=0)
        self.step_size.setValidator(QDoubleValidator(0.0001, 100000.0, 4, self))
        step_layout.addWidget(self.step_size)
        step_layout.addWidget(QLabel("mm"))
        
        feed_layout = QHBoxLayout()
        feed_layout.addWidget(QLabel("Feed Rate:"))

        # ---------- FEED RATE ---------------
        default_feed = self.cfg.get("movement", "feed_rate", default=1000.0)
        self.feed_rate = QLineEdit(f"{default_feed}")
        # ▸ feed entre 1 e 30000 mm/min
        self.feed_rate.setValidator(QDoubleValidator(1.0, 30000.0, 0, self))
        feed_layout.addWidget(self.feed_rate)
        feed_layout.addWidget(QLabel("mm/min"))
        
        # Add step and feed rate controls
        movement_layout.addLayout(step_layout, 3, 0, 1, 3)
        movement_layout.addLayout(feed_layout, 4, 0, 1, 3)

        # ---- grava no JSON quando o usuário termina de editar -----
        self.step_size.editingFinished.connect(self._save_step_feed)
        self.feed_rate.editingFinished.connect(self._save_step_feed)

        self.go_to_zero_btn = QPushButton("Go to Zero")
        self.go_to_zero_btn.clicked.connect(self.go_to_zero)
        self.go_to_zero_btn.setMinimumHeight(40)  # Altura mínima para facilitar o clique
        font = QFont()
        font.setBold(True)
        self.go_to_zero_btn.setFont(font)
        movement_layout.addWidget(self.go_to_zero_btn, 6, 0, 1, 3)  # Posiciona abaixo dos controles existentes

        # Botão para deslocar a head para posição de trabalho definida pelo usuário (WPos)
        self.go_to_position_btn = QPushButton("Go to Position")
        self.go_to_position_btn.setToolTip("Ir para posição de trabalho específica (WPos)")
        self.go_to_position_btn.clicked.connect(self.show_go_to_dialog)
        movement_layout.addWidget(self.go_to_position_btn, 7, 0, 1, 3)

        # Checkbox para habilitar/desabilitar controle via teclado
        self.keyboard_control_checkbox = QCheckBox("Enable Keyboard Control")
        self.keyboard_control_checkbox.setChecked(False)
        movement_layout.addWidget(self.keyboard_control_checkbox, 8, 0, 1, 3)
        
        # Movement mode (G90/G91)
        mode_layout = QHBoxLayout()
        self.mode_absolute = QPushButton("Passo a Passo (G90)")
        self.mode_absolute.setCheckable(True)
        self.mode_absolute.clicked.connect(lambda: self.set_motion_mode("G90"))
        
        self.mode_relative = QPushButton("Contínuo (G91)")
        self.mode_relative.setCheckable(True)
        self.mode_relative.setChecked(True)  # Default to relative mode
        self.mode_relative.clicked.connect(lambda: self.set_motion_mode("G91"))
        
        mode_layout.addWidget(self.mode_absolute)
        mode_layout.addWidget(self.mode_relative)
        movement_layout.addLayout(mode_layout, 5, 0, 1, 3)
        
        movement_group.setLayout(movement_layout)
        layout.addWidget(movement_group)

    def _save_step_feed(self):
        try:
            step = float(self.step_size.text())
            feed = float(self.feed_rate.text())
            self.cfg.remember_step_feed(step, feed)
        except ValueError:
            # silencioso – validação já existe
            return
        
    def _on_direction_press(self, axis: str, direction: int):
        """
        Chamada quando o usuário pressiona um botão (ou tecla).
        Decide entre STEP ou JOG e delega ao GRBLCNCController.
        """
        if not self._precheck_connected():
            return

        feed = self._get_feed_rate()
        step = self._get_step_size()
        if feed is None or step is None:
            return
        
        # --- grava imediatamente no JSON ---
        self.cfg.remember_step_feed(step, feed)

        # “Passo-a-passo” = botão G90 selecionado  ➜  usa step_move
        if self.mode_absolute.isChecked():
            self.controller.cnc.step_move(axis, step * direction, feed)
        # “Contínuo” = G91 selecionado  ➜  jog
        else:
            self.controller.cnc.jog_start(axis, direction, feed)

    def _on_direction_release(self):
        """Interrompe jog se estivermos em modo contínuo."""
        if not self._precheck_connected():
            return
        if self.mode_relative.isChecked():      # só há jog se G91
            self.controller.cnc.jog_stop()

    def start_movement(self, axis: str, direction: int):
        """
        Mantido apenas para chamadas vindas de eventFilter (atalhos de
        teclado). Encaminha para _on_direction_press.
        """
        self._on_direction_press(axis, direction)

    def _get_feed_rate(self) -> float | None:
        """Lê o feed-rate; devolve None e avisa em caso de erro."""
        try:
            val = float(self.feed_rate.text())

            if self.controller.cnc.is_connected:
                max_lim = max(self.controller.cnc.max_feed.values())
                if val > max_lim + 1e-3:
                    resp = QMessageBox.question(
                        self, "Feed acima do limite",
                        (f"O valor F={val:.0f} mm/min excede o limite atual "
                         f"(≤ {max_lim:.0f}).\n\n"
                         "Deseja atualizar $110 e $111 para permitir essa "
                         "velocidade em X e Y?"),
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    if resp == QMessageBox.StandardButton.Yes:
                        # novo limite com folga de 10 %
                        new_lim = int(val * 1.1)                 # 10 % de folga
                        new_acc = int((new_lim / 60) * 5)        # ≈5 s para atingir Vmáx

                        cmds = [
                            f"$110={new_lim}", f"$111={new_lim}",
                            f"$120={new_acc}", f"$121={new_acc}"
                        ]
                        for c in cmds:
                            self.controller.cnc.send_command(c, priority=True)

                        # actualiza cache interno
                        self.controller.cnc.max_feed['x'] = new_lim
                        self.controller.cnc.max_feed['y'] = new_lim
                        self.controller.cnc.max_acc ['x'] = new_acc
                        self.controller.cnc.max_acc ['y'] = new_acc
                        # desabilita avisos futuros de clamp
                        self.controller.cnc._feed_clamp_warned = True
                        QMessageBox.information(
                            self, "Limites actualizados",
                            (f"Feed-máx X/Y = {new_lim} mm/min\n"
                             f"Aceleração X/Y = {new_acc} mm/s²")
                        )
                    else:
                        # clampará ao valor máximo existente
                        QMessageBox.information(self, "Feed ajustado",
                                                f"A velocidade será limitada a {max_lim} mm/min.")
                        val = max_lim
            return val
        except ValueError:
            QMessageBox.warning(self, "Erro", "Feed-rate inválido")
            return None

    def _get_step_size(self) -> float | None:
        """Lê o step-size; devolve None e avisa em caso de erro."""
        try:
            return float(self.step_size.text())
        except ValueError:
            QMessageBox.warning(self, "Erro", "Step size inválido")
            return None

    def _precheck_connected(self) -> bool:
        if not self.controller.cnc.is_connected:
            QMessageBox.warning(self, "Erro", "CNC não conectada")
            return False
        return True

    def go_to_zero(self):
        """
        Move a cabeça para WPos (0, 0) reaproveitando a API de
        alto-nível do GRBLCNCController; UI não envia mais G-code cru.
        """
        if not self._precheck_connected():
            return

        # evita travamentos se a máquina já estiver ocupada
        if self.controller.cnc.machine_status in ("Run", "Jog", "Alarm"):
            QMessageBox.warning(self, "Aviso", f"Máquina ocupada ({self.controller.cnc.machine_status})")
            return

        feed = self._get_feed_rate()
        if feed is None:
            return

        self._start_move_thread(x=0, y=0, feed=feed,
                                status_msg="Movendo para posição zero")

    def stop_movement(self):
        self._on_direction_release()

    def show_go_to_dialog(self):
        """Exibe diálogo para coletar coordenadas de destino (WPos)."""
        from PyQt6.QtWidgets import QDialog, QLabel, QLineEdit, QHBoxLayout, QPushButton, QMessageBox
        from PyQt6.QtGui import QDoubleValidator

        dialog = QDialog(self)
        dialog.setWindowTitle("Go to Position")
        dialog.setModal(True)
        layout = QGridLayout(dialog)

        # Captura a posição de trabalho atual (WPos) para pré‑preencher os campos
        try:
            current = self.controller.cnc.get_current_position()
        except Exception:
            current = {'x': 0.0, 'y': 0.0}

        layout.addWidget(QLabel("X (mm):"), 0, 0)
        x_input = QLineEdit()
        x_input.setValidator(QDoubleValidator(-10000.0, 10000.0, 4, x_input))
        x_input.setText(f"{current.get('x', 0.0):.3f}")
        layout.addWidget(x_input, 0, 1)

        layout.addWidget(QLabel("Y (mm):"), 1, 0)
        y_input = QLineEdit()
        y_input.setValidator(QDoubleValidator(-10000.0, 10000.0, 4, y_input))
        y_input.setText(f"{current.get('y', 0.0):.3f}")
        layout.addWidget(y_input, 1, 1)

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout, 2, 0, 1, 2)

        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                x = float(x_input.text())
                y = float(y_input.text())
                self.go_to_position(x, y)
            except ValueError:
                QMessageBox.warning(self, "Erro", "Valores inválidos para X ou Y")

    def go_to_position(self, x, y):
        """Realiza movimento para a posição absoluta de trabalho (WPos)."""
        from PyQt6.QtWidgets import QMessageBox
        from PyQt6.QtCore import QTimer

        # 1. Verifica se há conexão
        if not self.controller.cnc.is_connected:
            QMessageBox.warning(self, "Erro", "CNC não conectada")
            return

        # 2. Verifica se a máquina está livre
        status = self.controller.cnc.machine_status
        if status in ("Alarm", "Run", "Jog"):
            QMessageBox.warning(self, "Aviso", f"Máquina ocupada ({status})")
            return

        # 3. Guarda modo de distância atual (G90 ou G91)
        prev_mode = "G90" if self.mode_absolute.isChecked() else "G91"

        # 4. Obtém feed rate
        try:
            feed_rate = float(self.feed_rate.text())
        except:
            feed_rate = 1000

        # 5. Deslocamento assíncrono
        self._start_move_thread(x, y, feed_rate,
                                status_msg=f"Movendo para X:{x:.3f}, Y:{y:.3f}")

    def _start_move_thread(self, x, y, feed, status_msg="Movendo…"):
        stbar = self.window().statusBar()
        stbar.showMessage(status_msg)

        self._move_thread = MoveTaskThread(self.controller.cnc, x, y, feed)

        def _on_done(xx, yy):
            stbar.showMessage(f"Head em X:{xx:.3f}, Y:{yy:.3f}")
            # força atualização UI
            QTimer.singleShot(50, self.window().update_position_display)

        def _on_err(msg):
            QMessageBox.critical(self, "Erro", msg)
            stbar.showMessage("Falha no deslocamento")

        self._move_thread.finished.connect(_on_done)
        self._move_thread.error.connect(_on_err)
        self._move_thread.start()

    def _execute_resume_and_update(self):
        """Executa o resumo após parada e força atualização de posição em sequência"""
        try:
            # Primeiro envia o comando para retomar após hold
            self.controller.cnc.grbl.send_immediately("~")
            logger.debug("MOVIMENTO: Enviado comando de retomada (~)")

            # --- INÍCIO DA MODIFICAÇÃO ---
            # REMOVIDO: Chamada para _force_position_update. A atualização agora
            # dependerá do polling regular iniciado em connect_cnc.
            # QTimer.singleShot(150, lambda: self._force_position_update(1))
            logger.debug("MOVIMENTO: Atualização de posição dependerá do polling regular.")
            # --- FIM DA MODIFICAÇÃO ---

        except Exception as e:
            logger.error(f"MOVIMENTO: Erro ao executar sequência de retomada: {e}")
            
    # A função _force_position_update pode ser mantida, mas não será mais chamada
    # a partir de _execute_resume_and_update.
    def _force_position_update(self, attempt=1):
        """Força múltiplas atualizações de posição para garantir precisão

        Args:
            attempt: Número da tentativa atual (para limitar tentativas)
        """
        if not hasattr(self.controller.cnc, 'grbl') or not self.controller.cnc.is_connected:
            return

        try:
            # Envia comando de status para obter posição atualizada
            # --- INÍCIO DA MODIFICAÇÃO ---
            # logger.debug(f"MOVIMENTO: Forçando atualização de posição - tentativa {attempt}") # REMOVIDO/COMENTADO
            # --- FIM DA MODIFICAÇÃO ---
            self.controller.cnc.grbl.send_immediately("?")

            # Se ainda estamos dentro do limite de tentativas, agenda outra verificação
            if attempt < 3:
                # Aumento progressivo do tempo entre tentativas (150ms, 200ms, 250ms)
                delay = 150 + (attempt * 50)
                # A chamada recursiva ainda existe, mas o log dentro dela foi removido
                QTimer.singleShot(delay, lambda: self._force_position_update(attempt + 1))

        except Exception as e:
            # Manter o log de erro
            logger.error(f"MOVIMENTO: Erro ao forçar atualização de posição: {e}")
            
    def set_motion_mode(self, mode):
        """Set the motion mode (G90/G91)"""
        if not self.controller.cnc.is_connected:
             # Se não estiver conectado, apenas atualiza a UI
            if mode == "G90":
                self.mode_absolute.setChecked(True)
                self.mode_relative.setChecked(False)
            else:
                self.mode_absolute.setChecked(False)
                self.mode_relative.setChecked(True)
            logger.warning(f"MOVIMENTO: CNC não conectada, modo {mode} definido apenas na UI.")
            return

        # Atualiza a UI
        if mode == "G90":
            self.mode_absolute.setChecked(True)
            self.mode_relative.setChecked(False)
        else: # G91
            self.mode_absolute.setChecked(False)
            self.mode_relative.setChecked(True)

        # Envia o comando para o GRBL
        try:
            # --- INÍCIO DA MODIFICAÇÃO ---
            # Armazena o modo internamente para referência futura, se necessário
            # self.controller.cnc.current_motion_mode = mode # Supondo que exista essa variável no controller
            # --- FIM DA MODIFICAÇÃO ---
            logger.debug(f"MOVIMENTO: Definindo modo de movimento para {mode}")
            self.controller.cnc.grbl.send_immediately(mode)
        except Exception as e:
            logger.error(f"MOVIMENTO: Erro ao definir modo de movimento: {e}")
            QMessageBox.warning(self, "Error", f"Error setting motion mode: {e}")

    def on_emergency_stop_toggle(self, checked):
        """
        Manipula o clique no botão Emergency Stop/Reset.
        """
        if not hasattr(self.controller.cnc, 'is_connected') or not self.controller.cnc.is_connected:
            QMessageBox.warning(self, "Erro", "CNC não conectada")
            self.emergency_stop_button.setChecked(not checked)
            return
            
        if checked:
            # Botão foi pressionado para entrar no modo RESET
            logger.info("EMERGENCY STOP: Botão pressionado. Enviando Soft Reset.")
            if self.controller.cnc.send_soft_reset():
                # Configura visual do botão para Reset
                self.emergency_stop_button.setText("Reset")
                self.emergency_stop_button.setStyleSheet("background-color: orange; color: black;")
                
                # Atualiza status
                main_window = self.window()
                if hasattr(main_window, 'statusBar'):
                    main_window.statusBar().showMessage("Máquina parada. Clique em Reset para desbloquear.")
            else:
                # Soft reset falhou, reverte o botão
                logger.error("EMERGENCY STOP: Falha ao enviar Soft Reset")
                QMessageBox.critical(self, "Erro", "Falha ao enviar comando de parada")
                self.emergency_stop_button.setChecked(False)
        else:
            # Botão foi pressionado para sair do modo RESET
            logger.info("RESET: Botão pressionado para desbloquear. Enviando $X.")
            if self.controller.cnc.unlock():
                # Configura visual do botão para STOP
                self.emergency_stop_button.setText("STOP")
                self.emergency_stop_button.setStyleSheet("background-color: red; color: white;")
                
                # Atualiza status
                main_window = self.window()
                if hasattr(main_window, 'statusBar'):
                    main_window.statusBar().showMessage("Máquina desbloqueada e pronta.")
                    
                # Solicita atualização de status para verificar nova condição
                QTimer.singleShot(200, lambda: self.controller.cnc.grbl.send_immediately("?"))
            else:
                # Desbloqueio falhou, reverte o botão
                logger.error("RESET: Falha ao enviar comando de desbloqueio")
                QMessageBox.critical(self, "Erro", "Falha ao desbloquear a máquina")
                self.emergency_stop_button.setChecked(True)


    def _auto_unlock_after_reset(self):
        """Executa sequência automática de desbloqueio após reset de emergência"""
        logger.info("AUTO UNLOCK: Iniciando sequência de desbloqueio automático após reset")
        
        try:
            # 1. Envia comando de desbloqueio
            self.controller.cnc.grbl.send_immediately("$X")
            logger.info("AUTO UNLOCK: Comando $X enviado")
            
            # 2. Pequena pausa
            QTimer.singleShot(200, lambda: self._check_if_unlocked())
        except Exception as e:
            logger.error(f"AUTO UNLOCK: Erro ao enviar comando de desbloqueio: {e}")
            main_window = self.window()
            if hasattr(main_window, 'statusBar'):
                main_window.statusBar().showMessage(f"Erro no desbloqueio automático: {e}")

    def _check_if_unlocked(self):
        """Verifica se o desbloqueio foi bem-sucedido e restaura configurações se necessário"""
        try:
            # Solicita status para conferir se saiu do alarme
            self.controller.cnc.grbl.send_immediately("?")
            
            # Exibe mensagem de sucesso
            main_window = self.window()
            if hasattr(main_window, 'statusBar'):
                main_window.statusBar().showMessage("Sistema parado e desbloqueado automaticamente.")
                
            logger.info("AUTO UNLOCK: Sequência de desbloqueio automático concluída")
        except Exception as e:
            logger.error(f"AUTO UNLOCK: Erro ao verificar status após desbloqueio: {e}")

@dataclass
class MapParams:
    origin: dict
    end: dict
    step_x: float
    step_y: float
    folder: str
    program_name: str


class _PreviewSuspender:
    """
    Context-manager que pausa o preview da câmera e garante reativação
    mesmo em caso de exceções.
    """
    def __init__(self, preview_widget):
        self.preview_widget = preview_widget
        self.was_running   = preview_widget and preview_widget.preview_timer.isActive()

    def __enter__(self):
        if self.was_running:
            self.preview_widget.stop_preview()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.was_running:
            self.preview_widget.start_preview()

class AOIControllerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Controle de Inspeção Óptica Automatizada")
        self.setGeometry(100, 100, 1200, 800)
        
        # Inicializa o controlador AOI
        self.controller = CNCAOIController()
        self.config = AOIConfigManager()
        self.current_sequence = None
        self.is_running_sequence = False
        
        # Variável para armazenar o último valor de posição (para comparação)
        self.last_logged_position = None

        # Armazenar o offset do sistema de coordenadas de trabalho (WCS) ativo (ex: G54)
        self.current_wcs_offset = {'x': 0.0, 'y': 0.0, 'z': 0.0} # Inicializa o offset WCS padrão (G54)

        # Armazenar a última Posição da Máquina (MPos) conhecida
        self.current_mpos = {'x': 0.0, 'y': 0.0, 'z': 0.0} 
        # Armazenar o Sistema de Coordenadas de Trabalho (WCS) ativo (ex: "G54")
        self.active_wcs = "G54" # Assume G54 como padrão inicial
        # Mapeamento de WCS para número P do G10
        self.wcs_to_p = {"G54": 1, "G55": 2, "G56": 3, "G57": 4, "G58": 5, "G59": 6}
        
        # Configuração da interface
        self.setup_ui()
        # Configuração do menu
        self.setup_menu()

        # -------- Painel de conexão inicialmente oculto -------
        self.connection_group.setVisible(False)

        # -------- Auto-connect se preferido --------------------
        self._attempt_auto_connect()

        # Timer para atualizar a posição – agora conectamos a um método que loga a ação 
        self.update_timer = QTimer(self) 
        self.update_timer.timeout.connect(self.on_update_timer) 
        self.update_timer.start(1000) # Atualiza a cada 1000ms

        # Capturar eventos de teclado para movimentação de qualquer widget:
        # instala o filter globalmente apenas UMA vez
        QApplication.instance().installEventFilter(self)

        # chama cleanup se o Qt encerrar por outros caminhos
        QApplication.instance().aboutToQuit.connect(self._cleanup_resources)


    #   Auto-connect com base no JSON de prefs
    def _attempt_auto_connect(self):
        # CNC
        if self.config.get("connections", "auto_connect_cnc", default=False):
            port = self.config.get("connections", "last_cnc_port", default="")
            if port:
                idx = self.cnc_port_combo.findText(port)
                if idx >= 0:
                    self.cnc_port_combo.setCurrentIndex(idx)
                QTimer.singleShot(100, self.connect_cnc)
        # Câmera
        if self.config.get("connections", "auto_connect_camera", default=False):
            cam_id = int(self.config.get("connections", "last_camera_id", default=0))
            idx = self.camera_id_combo.findText(str(cam_id))
            if idx >= 0:
                self.camera_id_combo.setCurrentIndex(idx)
            QTimer.singleShot(200, self.connect_camera)

    def eventFilter(self, source, event):
        """
        Intercepta eventos de teclado e dispara start/stop de movimento
        se a opção estiver habilitada.
        """
        # KeyPress
        if event.type() == QEvent.Type.KeyPress and self.movement_widget.keyboard_control_checkbox.isChecked():
            if hasattr(event, 'isAutoRepeat') and event.isAutoRepeat():
                return True
            key = event.key()
            if key == Qt.Key.Key_Up:
                self.movement_widget.start_movement("Y", 1)
                return True
            elif key == Qt.Key.Key_Down:
                self.movement_widget.start_movement("Y", -1)
                return True
            elif key == Qt.Key.Key_Left:
                self.movement_widget.start_movement("X", -1)
                return True
            elif key == Qt.Key.Key_Right:
                self.movement_widget.start_movement("X", 1)
                return True
            elif key == Qt.Key.Key_PageUp:
                 self.movement_widget.start_movement("Z", 1)
                 return True
            elif key == Qt.Key.Key_PageDown:
                 self.movement_widget.start_movement("Z", -1)
                 return True
        # KeyRelease
        elif event.type() == QEvent.Type.KeyRelease and self.movement_widget.keyboard_control_checkbox.isChecked():
            if hasattr(event, 'isAutoRepeat') and event.isAutoRepeat():
                return True
            key = event.key()
            if key in (
                Qt.Key.Key_Up, 
                Qt.Key.Key_Down, 
                Qt.Key.Key_Left, 
                Qt.Key.Key_Right,
                Qt.Key.Key_PageUp,
                Qt.Key.Key_PageDown
            ):
                self.movement_widget.stop_movement()
                return True
        return super().eventFilter(source, event)

    def on_update_timer(self):
        #logger.debug("Timer fired: atualizando tela de posição da head.")
        self.update_position_display()
        
    def setup_ui(self):
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        
        # Grupo de conexão (oculto por padrão; mostrado via menu)
        self.connection_group = QGroupBox("Conexão")
        connection_layout = QGridLayout()
        
        # CNC Connection
        connection_layout.addWidget(QLabel("Porta CNC:"), 0, 0)
        self.cnc_port_combo = QComboBox()
        self.refresh_ports()
        connection_layout.addWidget(self.cnc_port_combo, 0, 1)
        
        self.connect_cnc_btn = QPushButton("Conectar CNC")
        self.connect_cnc_btn.clicked.connect(self.connect_cnc)
        connection_layout.addWidget(self.connect_cnc_btn, 0, 2)
        
        # Camera connection
        connection_layout.addWidget(QLabel("Câmera ID:"), 1, 0)
        self.camera_id_combo = QComboBox()
        self.camera_id_combo.addItems(["0", "1", "2", "3"])
        connection_layout.addWidget(self.camera_id_combo, 1, 1)
        
        self.connect_camera_btn = QPushButton("Conectar Câmera")
        self.connect_camera_btn.clicked.connect(self.connect_camera)
        connection_layout.addWidget(self.connect_camera_btn, 1, 2)
        
        # Refresh ports button
        self.refresh_ports_btn = QPushButton("Atualizar Portas")
        self.refresh_ports_btn.clicked.connect(self.refresh_ports)
        connection_layout.addWidget(self.refresh_ports_btn, 0, 3)
        
        # Test camera button
        self.test_camera_btn = QPushButton("Testar Câmera")
        self.test_camera_btn.clicked.connect(self.test_camera)
        connection_layout.addWidget(self.test_camera_btn, 1, 3)
        
        self.connection_group.setLayout(connection_layout)
        main_layout.addWidget(self.connection_group)

        # Grupo de Calibração de Movimento ------
        calibration_group = QGroupBox("Calibração de Movimento")
        calibration_layout = QHBoxLayout()

        # Campos permanecem criados porque são usados pela
        # lógica de calibração, porém o grupo ficará oculto.
        self.pulses_input = QLineEdit(str(
            self.config.get("calibration", "pulses_per_rev", default=400)
        ))
        self.fuso_input = QLineEdit(str(
            self.config.get("calibration", "fuso_pitch", default=5)
        ))
        self.apply_calibration_btn = QPushButton("Aplicar Calibração")
        self.apply_calibration_btn.clicked.connect(self.apply_calibration)

        # (os widgets não são adicionados ao layout visual)
        calibration_group.setLayout(calibration_layout)
        calibration_group.setVisible(False)       # ← esconde
        main_layout.addWidget(calibration_group)  # mantém no DOM para uso interno
        
        # Splitter para dividir a interface em painéis
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Painel esquerdo: controles e lista de posições
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Informações de posição
        position_group = QGroupBox("Posição Atual")
        position_layout = QGridLayout()

        # Exibe os valores X, Y e status
        position_layout.addWidget(QLabel("X:"), 0, 0)
        self.x_position = QLabel("0.000 mm")
        position_layout.addWidget(self.x_position, 0, 1)

        # Botão para zerar apenas o eixo X
        self.zero_x_btn = QPushButton("Zero X")
        self.zero_x_btn.setToolTip("Zerar apenas o eixo X")
        self.zero_x_btn.clicked.connect(self.set_zero_x_position)
        position_layout.addWidget(self.zero_x_btn, 0, 2)

        position_layout.addWidget(QLabel("Y:"), 1, 0)
        self.y_position = QLabel("0.000 mm")
        position_layout.addWidget(self.y_position, 1, 1)

        # Botão para zerar apenas o eixo Y
        self.zero_y_btn = QPushButton("Zero Y")
        self.zero_y_btn.setToolTip("Zerar apenas o eixo Y")
        self.zero_y_btn.clicked.connect(self.set_zero_y_position)
        position_layout.addWidget(self.zero_y_btn, 1, 2)

        position_layout.addWidget(QLabel("Status:"), 2, 0)
        self.cnc_status = QLabel("Desconectado")
        position_layout.addWidget(self.cnc_status, 2, 1)

        # NOVO: Botão para setar a posição atual como zero
        self.set_zero_btn = QPushButton("Setar Posição Zero")
        self.set_zero_btn.clicked.connect(self.set_zero_position)
        position_layout.addWidget(self.set_zero_btn, 3, 0, 1, 2)

        position_group.setLayout(position_layout)
        left_layout.addWidget(position_group)
        
        # Widget de lista de posições
        self.position_list_widget = PositionListWidget()
        self.position_list_widget.add_position_btn.clicked.connect(self.add_current_position)
        self.position_list_widget.remove_position_btn.clicked.connect(self.remove_position)
        self.position_list_widget.position_selected.connect(self.on_position_selected)
        
        left_layout.addWidget(self.position_list_widget)
        
        # Controle de sequência
        self.sequence_widget = SequenceControlWidget()
        self.sequence_widget.create_sequence_btn.clicked.connect(self.create_sequence)
        self.sequence_widget.run_sequence_btn.clicked.connect(self.run_sequence)
        self.sequence_widget.stop_sequence_btn.clicked.connect(self.stop_sequence)
        self.sequence_widget.save_btn.clicked.connect(self.save_program)
        self.sequence_widget.load_btn.clicked.connect(self.load_program)
        self.sequence_widget.save_gcode_btn.clicked.connect(self.save_gcode)
        self.sequence_widget.load_gcode_btn.clicked.connect(self.load_gcode)
        
        left_layout.addWidget(self.sequence_widget)
        
        # Painel direito: visualizador de imagem e resultados
        right_panel = QTabWidget()
        
        # Aba de visualização de imagem
        self.image_viewer = ImageViewerWidget()
        right_panel.addTab(self.image_viewer, "Visualizador de Imagem")
        
        # Aba de resultados
        results_widget = QWidget()
        results_layout = QVBoxLayout(results_widget)
        
        self.results_table = QTableWidget(0, 3)
        self.results_table.setHorizontalHeaderLabels(["Posição", "Timestamp", "Status"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        results_layout.addWidget(QLabel("Resultados da Inspeção:"))
        results_layout.addWidget(self.results_table)
        
        right_panel.addTab(results_widget, "Resultados")
        
        # MOVER PARA AQUI: Adicionar a aba de Câmera & Movimento (após definir right_panel)
        # Tab para Camera & Movement
        camera_movement_tab = QWidget()
        camera_movement_layout = QHBoxLayout(camera_movement_tab)
        
        # Left side: controls and position registry
        cm_left_panel = QWidget()
        cm_left_layout = QVBoxLayout(cm_left_panel)
        
        # Movement controls 
        self.movement_widget = MovementControlWidget(self.controller, self.config)
        cm_left_layout.addWidget(self.movement_widget)
        
        # Position registry
        self.position_registry = PositionRegistryWidget(self.controller, self.config)
        self.position_registry.create_sequence_btn.clicked.connect(self.create_sequence_from_registry)
        cm_left_layout.addWidget(self.position_registry)
        
        # Right side: camera preview
        self.camera_preview = CameraPreviewWidget(self.controller, self.config)
        self.camera_preview.image_captured.connect(self.on_image_captured)
        
        # Define proporções para os painéis - dar mais espaço para a visualização da câmera
        camera_movement_layout.addWidget(cm_left_panel, 1)  # Proporção 1
        camera_movement_layout.addWidget(self.camera_preview, 3)  # Proporção 3 (mais espaço)
        
        # Agora é seguro adicionar a nova aba ao right_panel que já foi definido
        right_panel.addTab(camera_movement_tab, "Câmera & Movimento")
        
        # Adiciona painéis ao splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 800])
        
        main_layout.addWidget(splitter)
        
        # Barra de status
        self.statusBar().showMessage("Pronto para conectar")

    def setup_menu(self):
        """Configura o menu da aplicação"""
        menubar = self.menuBar()
        
        # Menu de Arquivo
        file_menu = menubar.addMenu('&Arquivo')
        
        exit_action = QAction('Sair', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Menu de Ferramentas
        tools_menu = menubar.addMenu('&Ferramentas')

        # ação para definir mapa
        definir_mapa_action = QAction('Definir Mapa', self)
        definir_mapa_action.triggered.connect(self.show_definir_mapa_dialog)
        tools_menu.addAction(definir_mapa_action)

        
        calibration_action = QAction('Calibração CNC', self)
        calibration_action.triggered.connect(self.show_calibration_dialog)
        tools_menu.addAction(calibration_action)

        # Preferências
        pref_action = QAction('Preferências', self)
        pref_action.setShortcut('Ctrl+,')
        pref_action.triggered.connect(self.show_settings_dialog)
        tools_menu.addAction(pref_action)

        # --------  painel de conexões -----------------
        conn_panel = QAction('Conexões…', self)
        conn_panel.setCheckable(True)
        conn_panel.setChecked(False)
        conn_panel.triggered.connect(
            lambda checked: self.connection_group.setVisible(checked)
        )
        tools_menu.addAction(conn_panel)
        
        # Menu de Ajuda
        help_menu = menubar.addMenu('&Ajuda')
        
        about_action = QAction('Sobre', self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

    def show_settings_dialog(self):
        dlg = SettingsDialog(self.config, self)
        if dlg.exec():
            # Se o usuário modificou algo, re-aplica (se a CNC já estiver conectada)
            if self.controller.cnc.is_connected:
                self.config.apply_to_cnc(self.controller.cnc)
            self.statusBar().showMessage("Preferências salvas")

    def show_calibration_dialog(self):
        """Mostra um diálogo para configuração de calibração"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Calibração do Sistema CNC")
        dialog.setMinimumWidth(500)
        
        layout = QVBoxLayout(dialog)
        
        # Grupo de parâmetros físicos
        param_group = QGroupBox("Parâmetros da Máquina")
        param_layout = QGridLayout(param_group)
        
        param_layout.addWidget(QLabel("Pulsos por Revolução:"), 0, 0)
        pulses_input = QLineEdit(self.pulses_input.text())
        param_layout.addWidget(pulses_input, 0, 1)
        
        param_layout.addWidget(QLabel("Passo do Fuso (mm):"), 1, 0)
        fuso_input = QLineEdit(self.fuso_input.text())
        param_layout.addWidget(fuso_input, 1, 1)
        
        param_layout.addWidget(QLabel("Steps/mm calculado:"), 2, 0)
        steps_mm_result = QLabel("Calculando...")
        param_layout.addWidget(steps_mm_result, 2, 1)
        
        # Atualiza o cálculo quando os valores mudam
        def update_calculation():
            try:
                pulses = float(pulses_input.text())
                fuso = float(fuso_input.text())
                steps_mm = pulses / fuso
                steps_mm_result.setText(f"{steps_mm:.3f} steps/mm")
            except:
                steps_mm_result.setText("Erro no cálculo")
        
        pulses_input.textChanged.connect(update_calculation)
        fuso_input.textChanged.connect(update_calculation)
        update_calculation()  # Executa o cálculo inicial
        
        layout.addWidget(param_group)
        
        # Botões de ação
        buttons_layout = QHBoxLayout()
        
        apply_btn = QPushButton("Aplicar Parâmetros")
        def apply_and_close():
            self.pulses_input.setText(pulses_input.text())
            self.fuso_input.setText(fuso_input.text())
            dialog.accept()
            self.apply_calibration()
        apply_btn.clicked.connect(apply_and_close)
        
        test_btn = QPushButton("Testar Calibração")
        test_btn.clicked.connect(lambda: [dialog.accept(), self.show_calibration_test_dialog()])
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(dialog.reject)
        
        buttons_layout.addWidget(apply_btn)
        buttons_layout.addWidget(test_btn)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
        
        dialog.exec()

    def show_about_dialog(self):
        """Mostra informações sobre o aplicativo"""
        QMessageBox.about(self, "Sobre HesaiVision", 
                        "HesaiVision v1.0\n\n"
                        "Sistema de Inspeção Óptica Automatizada\n"
                        "Desenvolvido para controle de CNC com GRBL\n\n"
                        "© 2025 HesaiVision")
        
    def show_definir_mapa_dialog(self):
        """Abre diálogo para definir cantos e gerar mapa (modeless, sempre no topo)."""
        # 1) Cria sem flags inválidas
        dialog = QDialog(self)
        dialog.setWindowTitle("Definir Mapa")

        # 2) Non‐modal: permite operar a janela principal
        dialog.setWindowModality(Qt.WindowModality.NonModal)

        # 3) Sempre no topo, com título e botão de fechar
        dialog.setWindowFlags(
            dialog.windowFlags()
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowStaysOnTopHint
        )

        layout = QVBoxLayout(dialog)

        # Nome do programa
        h1 = QHBoxLayout()
        h1.addWidget(QLabel("Nome do Programa:"))
        self.map_program_name_edit = QLineEdit()
        h1.addWidget(self.map_program_name_edit)
        layout.addLayout(h1)

        # Pasta de salvamento
        h2 = QHBoxLayout()
        h2.addWidget(QLabel("Pasta de Salvamento:"))
        self.map_folder_edit = QLineEdit()
        h2.addWidget(self.map_folder_edit)
        btn_browse = QPushButton("Buscar…")
        btn_browse.clicked.connect(self._select_map_folder)
        h2.addWidget(btn_browse)
        layout.addLayout(h2)

        # Passos X/Y
        h3 = QHBoxLayout()
        h3.addWidget(QLabel("Passo X (mm):"))
        self.map_step_x_edit = QLineEdit("10")
        h3.addWidget(self.map_step_x_edit)
        h3.addWidget(QLabel("Passo Y (mm):"))
        self.map_step_y_edit = QLineEdit("10")
        h3.addWidget(self.map_step_y_edit)
        layout.addLayout(h3)

        # Botões de definição de canto
        btn_origin = QPushButton("Definir canto inferior esquerdo")
        btn_origin.clicked.connect(lambda: self._define_map_corner('origin'))
        layout.addWidget(btn_origin)

        btn_end = QPushButton("Definir canto superior direito")
        btn_end.clicked.connect(lambda: self._define_map_corner('end'))
        layout.addWidget(btn_end)

        # Botão gerar mapa
        btn_generate = QPushButton("Gerar Mapa")
        btn_generate.clicked.connect(lambda: self._on_generate_map(dialog))
        layout.addWidget(btn_generate)

        dialog.show()  # modeless, não bloqueia a janela principal

    def _select_map_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Selecione pasta para salvar imagens")
        if folder:
            self.map_folder_edit.setText(folder)

    def _define_map_corner(self, which):
        pos = self.controller.cnc.get_current_position()
        if which == 'origin':
            self.map_origin = {'x': pos['x'], 'y': pos['y']}
            QMessageBox.information(self, "Origem", f"Canto inferior esquerdo: X={pos['x']:.3f}, Y={pos['y']:.3f}")
        else:
            self.map_end = {'x': pos['x'], 'y': pos['y']}
            QMessageBox.information(self, "Limite", f"Canto superior direito: X={pos['x']:.3f}, Y={pos['y']:.3f}")

    def _on_generate_map(self, dialog):
                
        # Passo 1 – coletar e validar parâmetros ---------------------
        params = self._collect_map_params()
        if params is None:      # validação falhou ⇒ aborta
            return

        # Passo 2 – iniciar thread de geração -----------------------
        self._start_map_thread(params, dialog)

    def _collect_map_params(self) -> MapParams | None:
        """
        Valida inputs da UI e devolve objeto MapParams ou None em caso de erro.
        Toda mensagem ao usuário é tratada aqui.
        """
        origin = getattr(self, 'map_origin', None)
        end    = getattr(self, 'map_end',    None)
        if not origin or not end:
            QMessageBox.warning(self, "Erro", "Defina ambos os cantos antes de gerar o mapa.")
            return None

        try:
            step_x = float(self.map_step_x_edit.text())
            step_y = float(self.map_step_y_edit.text())
        except ValueError:
            QMessageBox.warning(self, "Erro", "Passos X/Y inválidos.")
            return None

        dx, dy = end['x'] - origin['x'], end['y'] - origin['y']
        if step_x <= 0 or step_y <= 0:
            QMessageBox.warning(self, "Erro", "Os passos devem ser maiores que zero.")
            return None

        # Ajuste opcional se o passo superar dimensão
        if step_x > dx or step_y > dy:
            if QMessageBox.question(
                    self,
                    "Passo maior que dimensão",
                    ("Algum passo é maior que a dimensão da placa. "
                     "Deseja ajustar automaticamente?"),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            ) == QMessageBox.StandardButton.No:
                return None
            step_x = min(step_x, dx)
            step_y = min(step_y, dy)
            self.map_step_x_edit.setText(f"{step_x:.3f}")
            self.map_step_y_edit.setText(f"{step_y:.3f}")

        folder = self.map_folder_edit.text().strip()
        prog   = self.map_program_name_edit.text().strip()
        if not folder or not prog:
            QMessageBox.warning(self, "Erro", "Informe o nome do programa e a pasta de salvamento.")
            return None

        return MapParams(origin, end, step_x, step_y, folder, prog)

    def _start_map_thread(self, p: MapParams, dialog):
        """
        Separa a configuração da thread e da UI/ProgressBar.
        """
        # Context manager garante preview restaurado
        with _PreviewSuspender(self.camera_preview):
            self.map_thread = MapGeneratorThread(
                self.controller, p.origin, p.end,
                p.step_x, p.step_y, p.folder, p.program_name
            )

            # Progress dialog simples
            self.map_progress = QProgressDialog("Gerando mapa…", "Cancelar", 0, 0, self)
            self.map_progress.setWindowTitle("Progresso do Mapa")
            self.map_progress.setWindowModality(Qt.WindowModality.NonModal)
            self.map_progress.show()

            # Conexões de sinal ⇄ slots
            self.map_thread.progress.connect(self._on_map_progress)
            self.map_thread.image_captured.connect(self.camera_preview.display_image)
            self.map_thread.finished.connect(lambda: self._on_map_finished(dialog))
            self.map_thread.error.connect(self._on_map_error)

            self.map_progress.canceled.connect(self.map_thread.requestInterruption)
            self.map_thread.start()

    # ---------- slots da geração de mapa ----------------------------

    def _on_map_progress(self, done: int, total: int):
        self.map_progress.setMaximum(total)
        self.map_progress.setValue(done)
        pct = int(done / total * 100) if total else 0
        self.map_progress.setLabelText(f"Capturadas {done}/{total} imagens ({pct}%)")

    def _on_map_finished(self, dialog):
        self.map_progress.close()
        QMessageBox.information(self, "Concluído", "Mapa gerado com sucesso.")
        dialog.accept()

    def _on_map_error(self, msg: str):
        self.map_progress.close()
        QMessageBox.critical(self, "Erro", msg)

    def save_gcode(self):
        """Salva a sequência atual como arquivo G-CODE"""
        if not self.current_sequence:
            QMessageBox.warning(self, "Aviso", "Crie uma sequência primeiro")
            return
            
        from aoi_lib.gcode_manager import GCodeManager
        gcode_manager = GCodeManager()
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Salvar como G-CODE", "", "Arquivos G-CODE (*.gcode *.nc *.ngc)"
        )
        
        if filename:
            if not filename.lower().endswith(('.gcode', '.nc', '.ngc')):
                filename += '.gcode'
                
            if gcode_manager.save_gcode_to_file(self.current_sequence, filename):
                self.statusBar().showMessage(f"G-CODE salvo em {filename}")
            else:
                QMessageBox.critical(self, "Erro", "Falha ao salvar o arquivo G-CODE")

    def apply_calibration(self):
        """
        Aplica a calibração de movimento com base nos valores informados pelo usuário.
        Envia comandos diretos para o GRBL para configurar os steps/mm.
        """
        if not self.controller.cnc.is_connected or not self.controller.cnc.grbl:
            QMessageBox.warning(self, "Erro", "CNC não conectada. Conecte primeiro.")
            return
            
        try:
            pulses = float(self.pulses_input.text())
            fuso_pass = float(self.fuso_input.text())
            
            # Calcula steps/mm: (pulsos por revolução) / (passo do fuso em mm)
            steps_per_mm = pulses / fuso_pass
            
            # Armazena o valor calculado
            self.controller.cnc.steps_to_mm_factor = fuso_pass / pulses
            
            # Envia comandos para configurar o GRBL
            logger.info(f"CALIBRAÇÃO: Configurando steps/mm para {steps_per_mm}")
            
            # Verifica se o usuário deseja realmente enviar estes valores
            reply = QMessageBox.question(
                self, 
                "Confirmar Calibração", 
                f"Deseja enviar os seguintes parâmetros para o GRBL?\n\n"
                f"Steps/mm eixo X: {steps_per_mm:.3f}\n"
                f"Steps/mm eixo Y: {steps_per_mm:.3f}\n\n"
                f"Isso irá alterar a configuração do controlador.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Comandos para configurar os eixos X e Y
                self.controller.cnc.grbl.send_immediately(f"$100={steps_per_mm:.3f}")
                QTimer.singleShot(100, lambda: self.controller.cnc.grbl.send_immediately(f"$101={steps_per_mm:.3f}"))
                
                # Solicita ao usuário que faça um teste de calibração
                QTimer.singleShot(500, self.show_calibration_test_dialog)
                
                self.statusBar().showMessage(f"Calibração aplicada: {steps_per_mm:.3f} steps/mm")

                # --------- salva no JSON ----------
                self.config.remember_calibration(pulses, fuso_pass)

            else:
                self.statusBar().showMessage("Calibração cancelada pelo usuário")
                
        except ValueError:
            QMessageBox.warning(self, "Erro", "Valores de calibração inválidos.")

    def show_calibration_test_dialog(self):
        """
        Exibe um diálogo para testar a calibração atual.
        """
        dialog = QDialog(self)
        dialog.setWindowTitle("Teste de Calibração")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Instruções
        instructions = QLabel(
            "Para testar a calibração:\n\n"
            "1. Coloque um papel milimetrado ou uma régua sob a cabeça da máquina\n"
            "2. Escolha uma distância de teste\n"
            "3. Clique em 'Mover X' ou 'Mover Y' para testar cada eixo\n"
            "4. Verifique se o deslocamento físico corresponde ao valor escolhido\n"
            "5. Se necessário, ajuste os valores de calibração e aplique novamente"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Distância de teste
        test_layout = QHBoxLayout()
        test_layout.addWidget(QLabel("Distância de teste:"))
        distance_input = QLineEdit("10")
        test_layout.addWidget(distance_input)
        test_layout.addWidget(QLabel("mm"))
        layout.addLayout(test_layout)
        
        # Botões de teste
        buttons_layout = QHBoxLayout()
        
        move_x_btn = QPushButton("Mover X")
        move_x_btn.clicked.connect(lambda: self.test_calibration_move(0, float(distance_input.text())))
        
        move_y_btn = QPushButton("Mover Y")
        move_y_btn.clicked.connect(lambda: self.test_calibration_move(1, float(distance_input.text())))
        
        reset_position_btn = QPushButton("Zerar Posição")
        reset_position_btn.clicked.connect(self.set_zero_position)
        
        buttons_layout.addWidget(move_x_btn)
        buttons_layout.addWidget(move_y_btn)
        buttons_layout.addWidget(reset_position_btn)
        
        layout.addLayout(buttons_layout)
        
        # Resultados
        result_group = QGroupBox("Resultados")
        result_layout = QVBoxLayout(result_group)
        
        self.calibration_test_result = QLabel("Execute um teste para ver os resultados")
        result_layout.addWidget(self.calibration_test_result)
        
        layout.addWidget(result_group)
        
        # Botões de controle
        control_layout = QHBoxLayout()
        close_btn = QPushButton("Concluir")
        close_btn.clicked.connect(dialog.accept)
        control_layout.addWidget(close_btn)
        
        layout.addLayout(control_layout)
        
        dialog.exec()

    def test_calibration_move(self, axis, distance):
        """
        Realiza um movimento de teste para calibração.
        
        Args:
            axis: 0 para X, 1 para Y
            distance: Distância em mm para mover
        """
        if not self.controller.cnc.is_connected:
            QMessageBox.warning(self, "Erro", "CNC não conectada")
            return
        
        try:
            # Captura posição inicial
            initial_position = self.controller.cnc.get_current_position()
            
            # Prepara o comando
            axis_name = "X" if axis == 0 else "Y"
            
            # Define o modo absoluto para garantir precisão
            self.controller.cnc.grbl.send_immediately("G90")
            
            # Calcula a posição absoluta a ser atingida
            target_position = {}
            target_position['x'] = initial_position['x'] + distance if axis == 0 else initial_position['x']
            target_position['y'] = initial_position['y'] + distance if axis == 1 else initial_position['y']
            
            # Envia o movimento como coordenada absoluta
            if axis == 0:
                self.controller.cnc.move_to_absolute_position(target_position['x'], None, 500)
            else:
                self.controller.cnc.move_to_absolute_position(None, target_position['y'], 500)
            self.controller.cnc.wait_for_idle()
            
            # Aguarda um pouco para o movimento ser concluído
            QTimer.singleShot(1500, lambda: self.verify_calibration_result(axis, initial_position, distance))
            
        except Exception as e:
            logger.error(f"CALIBRAÇÃO: Erro no teste de calibração: {e}")
            QMessageBox.warning(self, "Erro", f"Erro no teste: {str(e)}")

    def _show_calibration_result(self, axis, initial_position, expected_distance):
        """
        Calcula deslocamento real, erro e atualiza o QLabel de resultados.
        Executado de forma assíncrona pelo QTimer.
        """
        try:
            current_position = self.controller.cnc.get_current_position()

            axis_name = "x" if axis == 0 else "y"
            actual_distance = current_position[axis_name] - initial_position[axis_name]

            error = actual_distance - expected_distance
            error_percent = (error / expected_distance * 100) if expected_distance else 0

            result_text = (
                f"Eixo: {axis_name.upper()}\n"
                f"Movimento comandado: {expected_distance:.3f} mm\n"
                f"Movimento real: {actual_distance:.3f} mm\n"
                f"Erro: {error:.3f} mm ({error_percent:.2f}%)\n\n"
            )

            if abs(error_percent) < 1:
                result_text += "■ Calibração excelente (erro < 1%)"
            elif abs(error_percent) < 5:
                result_text += "✓ Calibração aceitável (erro < 5%)"
            else:
                result_text += "■ Calibração insatisfatória – ajuste os parâmetros"

            if hasattr(self, "calibration_test_result"):
                self.calibration_test_result.setText(result_text)

            logger.info(
                "CALIBRAÇÃO: Resultado – %s",
                result_text.replace("\n", " | ")
            )
        except Exception as e:
            logger.error(f"CALIBRAÇÃO: Erro ao calcular resultado: {e}")

    def verify_calibration_result(self, axis, initial_position, expected_distance):
        """
        Verifica o resultado do teste de calibração.
        
        Args:
            axis: 0 para X, 1 para Y
            initial_position: Posição antes do movimento
            expected_distance: Distância esperada do movimento
        """
        try:
            # 1) força a atualização de status
            self.controller.cnc.grbl.send_immediately("?")

            # 2) Agenda o cálculo daqui a 250 ms para NÃO travar a GUI
            QTimer.singleShot(
                250,
                lambda: self._show_calibration_result(
                    axis, initial_position, expected_distance
                )
            )
            return
            
        except Exception as e:
            logger.error(f"CALIBRAÇÃO: Erro ao verificar resultado: {e}")

    def set_zero_position(self):
        """Define a posição de trabalho atual como zero usando G10 L20."""
        if not self.controller.cnc.is_connected or not self.controller.cnc.grbl:
            QMessageBox.warning(self, "Aviso", "CNC não conectada")
            return
        try:
            # 1. Captura a MPos MAIS RECENTE armazenada ANTES de enviar o G10
            #    Garante que estamos usando a posição correta para calcular o novo offset.
            #    Usamos self.current_mpos que é atualizado pelo callback on_stateupdate.
            mpos_correcta_no_zeramento = self.current_mpos.copy() # Captura a MPos atual armazenada
            logger.info(f"SET ZERO: MPos capturada para zeramento: {mpos_correcta_no_zeramento}")

            # Verifica se a MPos capturada parece válida (não apenas zeros se esperamos algo diferente)
            # Este é um check adicional, pode ser ajustado ou removido se causar problemas.
            if mpos_correcta_no_zeramento['x'] == 0.0 and mpos_correcta_no_zeramento['y'] == 0.0 and (self.last_logged_position and (self.last_logged_position['x'] != 0.0 or self.last_logged_position['y'] != 0.0)):
                 logger.warning(f"SET ZERO: MPos capturada ({mpos_correcta_no_zeramento}) parece zerada, mas a última posição exibida era {self.last_logged_position}. Verifique a atualização de self.current_mpos.")
                 # Poderia até abortar aqui ou pedir confirmação, mas vamos prosseguir por enquanto.

            # 2. Obter o número P correspondente ao WCS ativo (Ex: G54 -> P1)
            p_number = self.wcs_to_p.get(self.active_wcs)
            if p_number is None:
                logger.error(f"SET ZERO: WCS ativo '{self.active_wcs}' não reconhecido para G10 L20. Usando P1 (G54).")
                p_number = 1 # Usa G54 como fallback

            # 3. Construir o comando G10 L20
            # Zerando apenas X e Y por enquanto. Adicione Z se necessário: Z{mpos_correcta_no_zeramento['z']:.4f}
            # O comando G10 L20 Pn X0 Y0 diz ao GRBL: "Ajuste o offset do WCS 'n' para que a MPos *atual* corresponda a WPos X0 Y0"
            command = f"G10 L20 P{p_number} X0 Y0"
            logger.info(f"SET ZERO: Enviando comando: {command} para zerar {self.active_wcs}")

            # 4. Enviar o comando G10 L20 para o GRBL
            self.controller.cnc.grbl.send_immediately(command)

            # 5. Atualizar o offset interno da APLICAÇÃO
            # O novo offset que a aplicação deve usar para calcular WPos = MPos - Offset
            # é exatamente a MPos que a máquina tinha no momento do comando G10.
            logger.info(f"SET ZERO: Atualizando offset interno de {self.current_wcs_offset} para {mpos_correcta_no_zeramento}")
            self.current_wcs_offset = mpos_correcta_no_zeramento # ATUALIZAÇÃO CORRETA DO OFFSET INTERNO

            # 6. Atualizar a posição interna da APLICAÇÃO (WPos) para zero
            # Isso força a exibição a mostrar (0,0) imediatamente.
            new_wpos = {'x': 0.0, 'y': 0.0, 'z': 0.0} # A WPos deve ser zero agora
            logger.info(f"SET ZERO: Forçando posição interna (WPos) para {new_wpos}")
            self.controller.cnc.current_position = new_wpos

            # 7. Atualizar a interface gráfica imediatamente com a WPos zerada
            self.update_position_display() # Chama a função que atualiza os labels X e Y

            self.statusBar().showMessage(f"Posição zero definida para {self.active_wcs} na localização atual.")

            # 8. (Opcional) Solicitar $# ou $G após um tempo para verificar se o GRBL processou
            QTimer.singleShot(500, lambda: self.controller.cnc.grbl.send_immediately("$#"))
            QTimer.singleShot(600, lambda: self.controller.cnc.grbl.send_immediately("$G"))

        except Exception as e:
            logger.error(f"SET ZERO: Erro ao definir posição zero: {e}", exc_info=True)
            QMessageBox.warning(self, "Erro", f"Falha ao setar posição zero: {str(e)}")

    def set_zero_x_position(self):
        """Zera apenas o eixo X (WPos.x = 0), mantendo Y."""
        from PyQt6.QtWidgets import QMessageBox
        if not self.controller.cnc.is_connected:
            QMessageBox.warning(self, "Aviso", "CNC não conectada")
            return
        try:
            # Captura a MPos atual
            mpos = self.current_mpos.copy()
            # Número do WCS (G54…G59)
            p_number = self.wcs_to_p.get(self.active_wcs, 1)
            # Comando para zerar X no offset ativo
            cmd = f"G10 L20 P{p_number} X0"
            self.controller.cnc.grbl.send_immediately(cmd)
            # Atualiza o offset interno de X
            self.current_wcs_offset['x'] = mpos['x']
            # Ajusta a posição interna (WPos) para refletir X=0
            new_wpos = {
                'x': 0.0,
                'y': self.controller.cnc.current_position.get('y', 0.0),
                'z': self.controller.cnc.current_position.get('z', 0.0)
            }
            self.controller.cnc.current_position = new_wpos
            self.update_position_display()
            self.statusBar().showMessage("Eixo X zerado")
        except Exception as e:
            logger.error(f"Erro ao zerar eixo X: {e}", exc_info=True)
            QMessageBox.critical(self, "Erro", f"Falha ao zerar eixo X:\n{e}")

    def set_zero_y_position(self):
        """Zera apenas o eixo Y (WPos.y = 0), mantendo X."""
        from PyQt6.QtWidgets import QMessageBox
        if not self.controller.cnc.is_connected:
            QMessageBox.warning(self, "Aviso", "CNC não conectada")
            return
        try:
            mpos = self.current_mpos.copy()
            p_number = self.wcs_to_p.get(self.active_wcs, 1)
            cmd = f"G10 L20 P{p_number} Y0"
            self.controller.cnc.grbl.send_immediately(cmd)
            self.current_wcs_offset['y'] = mpos['y']
            new_wpos = {
                'x': self.controller.cnc.current_position.get('x', 0.0),
                'y': 0.0,
                'z': self.controller.cnc.current_position.get('z', 0.0)
            }
            self.controller.cnc.current_position = new_wpos
            self.update_position_display()
            self.statusBar().showMessage("Eixo Y zerado")
        except Exception as e:
            logger.error(f"Erro ao zerar eixo Y: {e}", exc_info=True)
            QMessageBox.critical(self, "Erro", f"Falha ao zerar eixo Y:\n{e}")

    def on_image_captured(self, image, position_name):
        """Handle captured image and register position"""
        # Display in image viewer
        self.image_viewer.display_image(image, f"Image: {position_name}")
        
        # Get current position
        if not self.controller.cnc.is_connected:
            QMessageBox.warning(self, "Error", "CNC not connected")
            return
            
        current_pos = self.controller.cnc.get_current_position()
        
        # Register position with image
        self.position_registry.add_position(
            position_name, 
            current_pos['x'], 
            current_pos['y'], 
            image
        )
        
        self.statusBar().showMessage(f"Position '{position_name}' registered at X:{current_pos['x']:.3f}, Y:{current_pos['y']:.3f}")

    def create_sequence_from_registry(self):
        """Create a sequence from registered positions"""
        if not self.position_registry.positions:
            QMessageBox.warning(self, "Warning", "No positions registered")
            return
            
        # Get sequence name
        sequence_name = self.sequence_widget.sequence_name.text()
        if not sequence_name:
            QMessageBox.warning(self, "Warning", "Please enter a sequence name")
            return
            
        # Clear existing positions in the position list widget
        self.position_list_widget.clear_positions()
        
        # Create positions for the sequence
        positions = []
        for pos in self.position_registry.positions:
            # Create position object with camera parameters
            camera_params = {"has_image": pos['image'] is not None}
            
            inspection_pos = InspectionPosition(
                pos['name'], 
                pos['x'], 
                pos['y'],
                camera_params
            )
            positions.append(inspection_pos)
            
            # Also add to the position list widget
            self.position_list_widget.add_position(inspection_pos)
            
        # Create the sequence
        self.current_sequence = self.controller.create_sequence(sequence_name, positions)
        
        # Update UI
        self.sequence_widget.sequence_status.setText(f"Created: {len(positions)} positions")
        self.statusBar().showMessage(f"Sequence '{sequence_name}' created with {len(positions)} positions")
        
        # Ask if user wants to save as G-CODE
        reply = QMessageBox.question(
            self, 
            "Save G-CODE", 
            "Do you want to save this sequence as G-CODE?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.save_gcode()

    def load_gcode(self):
        """Carrega uma sequência a partir de um arquivo G-CODE"""
        from aoi_lib.gcode_manager import GCodeManager
        gcode_manager = GCodeManager()
        
        filename, _ = QFileDialog.getOpenFileName(
            self, "Abrir G-CODE", "", "Arquivos G-CODE (*.gcode *.nc *.ngc)"
        )
        
        if filename:
            # Carrega o G-CODE
            result = gcode_manager.read_gcode_file(filename)
            
            if result:
                # Limpa posições atuais
                self.position_list_widget.clear_positions()
                
                # Cria sequência a partir dos dados do G-CODE
                positions = []
                for pos_data in result['positions']:
                    # Cria objeto de posição
                    position = InspectionPosition(
                        pos_data['name'], 
                        pos_data['x'], 
                        pos_data['y'],
                        pos_data['camera_params']
                    )
                    
                    # Adiciona à lista visual
                    self.position_list_widget.add_position(position)
                    
                    # Adiciona à lista interna
                    positions.append(position)
                
                # Cria a sequência
                self.current_sequence = self.controller.create_sequence(
                    result['sequence_name'], positions
                )
                
                # Atualiza interface
                self.sequence_widget.sequence_name.setText(result['sequence_name'])
                self.sequence_widget.sequence_status.setText(
                    f"Carregada do G-CODE: {len(positions)} posições"
                )
                
                self.statusBar().showMessage(f"G-CODE carregado de {filename}")
            else:
                QMessageBox.critical(self, "Erro", "Falha ao carregar o arquivo G-CODE")
        
    def refresh_ports(self):
        """Atualiza a lista de portas seriais disponíveis"""
        import serial.tools.list_ports
        
        self.cnc_port_combo.clear()
        ports = [port.device for port in serial.tools.list_ports.comports()]
        
        if ports:
            self.cnc_port_combo.addItems(ports)
            
            # Verificar se COM9 está na lista e selecionar
            com9_index = self.cnc_port_combo.findText("COM9")
            if com9_index >= 0:
                self.cnc_port_combo.setCurrentIndex(com9_index)
                self.statusBar().showMessage("Porta COM9 detectada")
        else:
            self.statusBar().showMessage("Nenhuma porta serial encontrada")
            
    def connect_cnc(self): 
        """Conecta à máquina CNC usando a biblioteca grbl-streamer""" 
        if hasattr(self.controller.cnc, 'is_connected') and self.controller.cnc.is_connected: 
            # Desconectar 
            try: 
                if hasattr(self.controller.cnc, 'grbl') and self.controller.cnc.grbl: 
                    self.controller.cnc.grbl.poll_stop() 
                    self.controller.cnc.grbl.disconnect() 
                    self.controller.cnc.grbl = None
                    self.controller.cnc.is_connected = False
                    self.connect_cnc_btn.setText("Conectar CNC")
                    self.cnc_status.setText("Desconectado")
                    self.statusBar().showMessage("CNC desconectada")
            except Exception as e:
                self.statusBar().showMessage(f"Erro ao desconectar: {str(e)}")
        else:
            # Conectar
            port = self.cnc_port_combo.currentText()
            if not port:
                QMessageBox.warning(self, "Erro", "Selecione uma porta serial")
                return
                
            self.statusBar().showMessage(f"Conectando à CNC na porta {port}...")
            
            try:
                # Define função de callback para eventos do GrblStreamer
                def grbl_callback(eventstring, *data):
                    logger.debug(f"CALLBACK: Evento '{eventstring}' recebido com data: {data}") 

                    # Capturar offsets do sistema de coordenadas (G54, G55, etc.)
                    if eventstring == "on_hash_stateupdate":
                        if data and isinstance(data[0], dict):
                            hash_state = data[0]

                            # Processar G54 APENAS se o WCS ativo for G54
                            # Isso evita que a resposta tardia do $# sobrescreva um offset
                            # que foi definido manualmente via G10 L20 para G54.
                            if self.active_wcs == "G54": 
                                g54_offset_data = hash_state.get('G54') 
                                if isinstance(g54_offset_data, (list, tuple)) and len(g54_offset_data) >= 2:
                                    try:
                                        new_offset_x_phys = float(g54_offset_data[0])
                                        new_offset_y_phys = float(g54_offset_data[1])
                                        new_offset_z_phys = float(g54_offset_data[2]) if len(g54_offset_data) > 2 else 0.0

                                        # Converte Y físico → lógico (depende de invert_y)
                                        if self.controller.cnc.invert_y:
                                            new_offset_y_log = -new_offset_y_phys
                                        else:
                                            new_offset_y_log = new_offset_y_phys

                                        self.current_wcs_offset = {
                                            # X e Z permanecem iguais
                                            'x': new_offset_x_phys,
                                            # guardamos FÍSICO para operar com G10 L20.
                                            'y': new_offset_y_phys,
                                            'z': new_offset_z_phys
                                        }

                                        logger.info(
                                            "CALLBACK: Offset G54 atualizado "
                                            f"(físico): {{x:{new_offset_x_phys:.3f}, y:{new_offset_y_phys:.3f}, z:{new_offset_z_phys:.3f}}}; "
                                            f"(lógico Y={new_offset_y_log:.3f})"
                                        )
                                    except (ValueError, TypeError):
                                         logger.error(f"CALLBACK: Erro ao converter offset G54 de $#: {g54_offset_data}")
                                else:
                                    logger.warning(f"CALLBACK: Offset G54 não encontrado ou inválido nos dados hash para WCS ativo G54: {hash_state}")
                            else:
                                logger.debug(f"CALLBACK: Ignorando atualização de offset G54 de $# porque WCS ativo é {self.active_wcs}")
                            # TODO: Se precisar suportar outros WCS (G55-G59), adicionar lógica similar aqui
                
                    # Capturar estado do parser para saber o WCS ativo
                    elif eventstring == "on_gcode_parser_stateupdate":
                        # ... (código existente para atualizar self.active_wcs) ...
                        if data and isinstance(data[0], list) and len(data[0]) > 1:
                            parser_state = data[0]
                            # O índice 1 contém o WCS ativo (ex: "54", "55", etc.)
                            # O índice 0 contém o modo de movimento (ex: "1" para G1)
                            # O índice 4 contém o modo de distância (ex: "90" para G90)
                            new_active_wcs = f"G{parser_state[1]}" 
                            new_motion_mode = f"G{parser_state[0]}"
                            new_distance_mode = f"G{parser_state[4]}"

                            if new_active_wcs != self.active_wcs:
                                logger.info(f"CALLBACK: WCS Ativo mudou de {self.active_wcs} para {new_active_wcs}")
                                self.active_wcs = new_active_wcs
                                # Ao mudar o WCS, seria ideal buscar o offset correspondente via $#
                                # ou ter todos os offsets armazenados. Por enquanto, apenas logamos.
                                # self.controller.cnc.grbl.send_immediately("$#") # Cuidado com loops

                            # Atualiza estado interno da aplicação sobre modos G90/G91
                            # Isso garante que a UI e a lógica de movimento estejam sincronizadas
                            # com o estado real do GRBL reportado por $G.
                            if hasattr(self, 'movement_widget'): # Verifica se o widget existe
                                if new_distance_mode == "G90":
                                    if not self.movement_widget.mode_absolute.isChecked():
                                        logger.info("CALLBACK ($G): Sincronizando UI para G90 (Absoluto)")
                                        self.movement_widget.mode_absolute.setChecked(True)
                                        self.movement_widget.mode_relative.setChecked(False)
                                elif new_distance_mode == "G91":
                                     if not self.movement_widget.mode_relative.isChecked():
                                        logger.info("CALLBACK ($G): Sincronizando UI para G91 (Relativo)")
                                        self.movement_widget.mode_absolute.setChecked(False)
                                        self.movement_widget.mode_relative.setChecked(True)
                    
                    elif eventstring == "on_stateupdate":
                        logger.info(f"CALLBACK: Processando 'on_stateupdate'. Dados brutos: {data}") 

                        if len(data) >= 3:
                            state = data[0]
                            mpos_tuple = data[1]  # Posição da Máquina (MPos)
                            # wpos_tuple = data[2] # Posição de Trabalho (WPos) - Ignorando pois está vindo zerado

                            logger.debug(f"CALLBACK DETALHADO: state={state}, mpos={mpos_tuple}") # Removido wpos do log detalhado
                            
                            # Atualiza estado da máquina
                            old_state = self.controller.cnc.machine_status if hasattr(self.controller.cnc, 'machine_status') else None
                            self.controller.cnc.machine_status = state
                            
                            if old_state != state:
                                logger.debug(f"CALLBACK: Estado da máquina mudou de '{old_state}' para '{state}'")
                            
                            # Calcular WPOS a partir de MPOS e do offset armazenado
                            if isinstance(mpos_tuple, (list, tuple)) and len(mpos_tuple) >= 2: 
                                try:
                                    # 1) valores FÍSICOS reportados pelo GRBL
                                    mpos_x_phys = float(mpos_tuple[0])
                                    mpos_y_phys = float(mpos_tuple[1])
                                    mpos_z_phys = float(mpos_tuple[2]) if len(mpos_tuple) > 2 else 0.0

                                    # 2) guarda MPos física para rotinas G10
                                    self.current_mpos = {
                                        'x': mpos_x_phys,
                                        'y': mpos_y_phys,
                                        'z': mpos_z_phys
                                    }

                                    # 3) converte para sistema LÓGICO (visão do usuário)
                                    mpos_y_log = -mpos_y_phys if self.controller.cnc.invert_y else mpos_y_phys
                                    off_y_log  = (-self.current_wcs_offset['y']
                                                if self.controller.cnc.invert_y
                                                else self.current_wcs_offset['y'])

                                    calculated_wpos_x = mpos_x_phys - self.current_wcs_offset['x']
                                    calculated_wpos_y = mpos_y_log  - off_y_log
                                    calculated_wpos_z = mpos_z_phys - self.current_wcs_offset['z']

                                    new_position = {
                                        'x': calculated_wpos_x,
                                        'y': calculated_wpos_y,
                                        'z': calculated_wpos_z
                                    }

                                    old_position = None
                                    if hasattr(self.controller.cnc, 'current_position'):
                                        old_position = self.controller.cnc.current_position.copy() 
                                        # logger.debug(f"CALLBACK: Posição interna ANTES da atualização: {old_position}") # Log opcional

                                    logger.debug(f"CALLBACK: MPos={mpos_tuple}, Offset={self.current_wcs_offset}, WPos Calculada={new_position}")
                                    logger.debug(f"CALLBACK: Tentando atualizar posição interna (usando WPOS CALCULADA) para: {new_position}")

                                    # Compara new_position (WPos calculada) com old_position
                                    position_changed = (old_position is None) or \
                                                       (abs(old_position['x'] - new_position['x']) > 1e-4) or \
                                                       (abs(old_position['y'] - new_position['y']) > 1e-4) or \
                                                       (abs(old_position.get('z', 0.0) - new_position.get('z', 0.0)) > 1e-4)

                                    if position_changed:
                                        logger.info(f"CALLBACK: POSIÇÃO INTERNA ATUALIZADA (usando WPOS CALCULADA): {old_position} -> {new_position}")
                                        # Atualiza a posição no controlador com a WPos calculada
                                        self.controller.cnc.current_position = new_position 
                                    
                                except (ValueError, TypeError, IndexError) as e:
                                    logger.error(f"CALLBACK: Erro ao processar MPOS ou calcular WPOS: {e}, mpos={mpos_tuple}")
                            else:
                                logger.error(f"CALLBACK: Formato inválido para MPOS: {type(mpos_tuple)}, valor: {mpos_tuple}")

                        else:
                            logger.error(f"CALLBACK: 'on_stateupdate' recebido com dados insuficientes (len={len(data)}). Dados: {data}")

                    # ... (restante do código do callback para outros eventos: on_write, on_read, etc.) ...
                    elif eventstring == "on_write":
                        logger.debug(f"CALLBACK: Comando enviado para GRBL: {data[0] if data else 'vazio'}")
                    # ... (etc.) ...

                # --- INÍCIO DA MODIFICAÇÃO ---
                # Inicializa o GrblStreamer APENAS com o callback
                self.controller.cnc.grbl = GrblStreamer(grbl_callback) 
                # --- FIM DA MODIFICAÇÃO ---

                logger.debug(f"CONEXÃO: Tentando conectar à porta {port} com baudrate 115200")
                # Conecta usando o método cnect()
                self.controller.cnc.grbl.cnect(port, 115200) 
                time.sleep(2.0) 

                if not self.controller.cnc.grbl.connected:
                     logger.error("CONEXÃO: Falha ao estabelecer conexão serial (grbl.connected é False).")
                     raise ConnectionError("Falha ao conectar à porta serial após inicialização.")

                logger.debug("CONEXÃO: Enviando comando de desbloqueio $X")
                self.controller.cnc.grbl.send_immediately("$X")
                time.sleep(0.1) 

                logger.debug("CONEXÃO: Configurando $10=3 para relatório completo de posição")
                self.controller.cnc.grbl.send_immediately("$10=3") # Mantém $10=3 para receber MPos
                time.sleep(0.1)

                # --- INÍCIO DA MODIFICAÇÃO ---
                # Solicitar estado hash logo após conectar para obter offsets
                logger.debug("CONEXÃO: Solicitando estado hash ($#) para obter offsets")
                self.controller.cnc.grbl.send_immediately("$#") 
                time.sleep(0.1)
                # --- FIM DA MODIFICAÇÃO ---

                logger.debug("CONEXÃO: Configurando modo relativo G91")
                self.controller.cnc.grbl.send_immediately("G91")
                time.sleep(0.1)

                logger.debug("CONEXÃO: Iniciando polling de status")
                self.controller.cnc.grbl.poll_start()

                self.controller.cnc.is_connected = True
                self.config.apply_to_cnc(self.controller.cnc)
                self.config.remember_cnc_port(port)
                self.controller.cnc.machine_status = "Idle"  
                self.connect_cnc_btn.setText("Desconectar CNC")
                self.cnc_status.setText("Conectado")
                self.statusBar().showMessage(f"CNC conectada na porta {port}")
                
            except Exception as e:
                # ... (código de tratamento de erro de conexão) ...
                logger.error(f"CONEXÃO: Falha ao conectar ou configurar: {str(e)}", exc_info=True) 
                QMessageBox.critical(self, "Erro", f"Falha ao conectar a CNC: {str(e)}")
                if hasattr(self.controller.cnc, 'grbl') and self.controller.cnc.grbl:
                    try:
                        self.controller.cnc.grbl.disconnect()
                    except: pass
                self.controller.cnc.grbl = None
                self.controller.cnc.is_connected = False
                self.controller.cnc.machine_status = "Erro Conexão"
                self.connect_cnc_btn.setText("Conectar CNC")
                self.cnc_status.setText("Erro Conexão")
                
    def connect_camera(self):
        """Conecta à câmera"""
        if hasattr(self.controller.camera, 'is_connected') and self.controller.camera.is_connected:
            # Interrompe preview antes de liberar a câmera
            self.camera_preview.stop_preview()

            # Desconectar
            self.controller.camera.disconnect()
            self.connect_camera_btn.setText("Conectar Câmera")
            self.statusBar().showMessage("Câmera desconectada")
        else:
            # Conectar
            try:
                camera_id = int(self.camera_id_combo.currentText())
                
                self.statusBar().showMessage(f"Conectando à câmera ID {camera_id}...")
                
                if self.controller.connect_camera(camera_id):
                    self.connect_camera_btn.setText("Desconectar Câmera")
                    self.statusBar().showMessage(f"Câmera ID {camera_id} conectada")
                    self.config.remember_camera_id(camera_id)
                else:
                    QMessageBox.critical(self, "Erro", f"Falha ao conectar à câmera: {self.controller.camera.last_error}")
            except ValueError:
                QMessageBox.warning(self, "Erro", "ID de câmera inválido")
                
    def test_camera(self):
        """Testa a captura de imagem da câmera"""
        if not hasattr(self.controller.camera, 'is_connected') or not self.controller.camera.is_connected:
            QMessageBox.warning(self, "Aviso", "Câmera não conectada")
            return
            
        image = self.controller.camera.capture()
        
        if image is not None:
            self.image_viewer.display_image(image, "Imagem de teste da câmera")
            self.statusBar().showMessage("Imagem capturada com sucesso")
        else:
            QMessageBox.warning(self, "Erro", f"Falha ao capturar imagem: {self.controller.camera.last_error}")
            
    def update_position_display(self): 
        """Atualiza a exibição da posição atual (agora exibindo WPos calculada)""" 
        if not self.controller.cnc.is_connected: 
            # logger.debug("update_position_display: CNC não conectada.") # Log já existente
            return 
        try: 
            # get_current_position agora retorna a WPos calculada
            position = self.controller.cnc.get_current_position() 
            logger.debug("update_position_display: posição (WPos calculada) obtida do CNC: %s", position) 
        except Exception as e: 
            logger.error("update_position_display: erro ao obter posição: %s", e) 
            return

        # Comparação para log (opcional, pode ser removido se poluir muito)
        if self.last_logged_position is not None:
            if position == self.last_logged_position:
                pass
                # logger.warning("update_position_display: posição (WPos calculada) inalterada: %s", position)
            else:
                logger.debug("update_position_display: posição (WPos calculada) mudou de %s para %s", 
                            self.last_logged_position, position)
        else:
            logger.debug("update_position_display: nenhuma posição (WPos calculada) anterior registrada.")
        
        self.last_logged_position = position.copy()

        # Atualiza os labels da interface com a WPos calculada
        self.x_position.setText(f"{position['x']:.3f} mm")
        self.y_position.setText(f"{position['y']:.3f} mm")
        self.cnc_status.setText(self.controller.cnc.machine_status)
        
    def add_current_position(self):
        """Adiciona a posição atual à lista"""
        if not self.controller.cnc.is_connected:
            QMessageBox.warning(self, "Aviso", "CNC não conectada")
            return
            
        position_name, ok = QInputDialog.getText(self, "Nova Posição", "Nome da posição:")
        
        if ok and position_name:
            position = self.controller.add_current_position(position_name)
            self.position_list_widget.add_position(position)
            self.statusBar().showMessage(f"Posição '{position_name}' adicionada")
            
    def remove_position(self):
        """Remove a posição selecionada"""
        position = self.position_list_widget.remove_selected_position()
        
        if position:
            self.controller.position_manager.remove_position(position.name)
            self.statusBar().showMessage(f"Posição '{position.name}' removida")
            
    def on_position_selected(self, position):
        """Manipula a seleção de uma posição"""
        # Poderia mover para esta posição, mostrar detalhes, etc.
        self.statusBar().showMessage(f"Posição selecionada: {position.name} ({position.x:.3f}, {position.y:.3f})")
        
    def create_sequence(self):
        """Cria uma nova sequência com as posições atuais"""
        positions = self.position_list_widget.get_all_positions()
        
        if not positions:
            QMessageBox.warning(self, "Aviso", "Adicione pelo menos uma posição")
            return
            
        sequence_name = self.sequence_widget.sequence_name.text()
        if not sequence_name:
            QMessageBox.warning(self, "Aviso", "Digite um nome para a sequência")
            return
            
        self.current_sequence = self.controller.create_sequence(sequence_name, positions)
        self.statusBar().showMessage(f"Sequência '{sequence_name}' criada com {len(positions)} posições")
        self.sequence_widget.sequence_status.setText(f"Criada: {len(positions)} posições")
        
    def run_sequence(self):
        """Executes the current sequence"""
        if not self.current_sequence:
            QMessageBox.warning(self, "Warning", "Create a sequence first")
            return
            
        if not self.controller.cnc.is_connected:
            QMessageBox.warning(self, "Warning", "CNC not connected")
            return
            
        if not hasattr(self.controller.camera, 'is_connected') or not self.controller.camera.is_connected:
            QMessageBox.warning(self, "Warning", "Camera not connected")
            return
            
        # Clear previous results
        self.results_table.setRowCount(0)
        
        # Configure UI for execution
        self.is_running_sequence = True
        self.sequence_widget.run_sequence_btn.setEnabled(False)
        self.sequence_widget.stop_sequence_btn.setEnabled(True)
        self.sequence_widget.sequence_status.setText("Executing...")
        
        # Start execution
        try:
            self.statusBar().showMessage(f"Executing sequence '{self.current_sequence.name}'...")
            
            # Use a thread to run the sequence
            self.run_thread = SequenceRunnerThread(self.controller, self.current_sequence.name)
            self.run_thread.image_captured.connect(self.on_sequence_image_captured)
            self.run_thread.sequence_completed.connect(self.on_sequence_completed)
            self.run_thread.sequence_error.connect(self.on_sequence_error)
            self.run_thread.start()
            
        except Exception as e:
            self.statusBar().showMessage(f"Error executing sequence: {str(e)}")
            self.sequence_widget.sequence_status.setText("Error")
            self.on_sequence_completed()

    def on_sequence_image_captured(self, result):
        """Called when an image is captured during sequence execution"""
        position = result["position"]
        image = result["image"]
        timestamp = result["timestamp"]
        
        # Display the image
        self.image_viewer.display_image(image, f"Position: {position.name} ({position.x:.3f}, {position.y:.3f})")
        
        # Add to results table
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        self.results_table.setItem(row, 0, QTableWidgetItem(position.name))
        self.results_table.setItem(row, 1, QTableWidgetItem(time.strftime("%H:%M:%S", time.localtime(timestamp))))
        self.results_table.setItem(row, 2, QTableWidgetItem("Captured"))
            
    def stop_sequence(self):
        """Para a execução da sequência atual"""
        if self.is_running_sequence:
            self.controller.stop_sequence()
            self.statusBar().showMessage("Execução de sequência interrompida")
            self.on_sequence_completed()
        
    def on_sequence_completed(self):
        """Chamado quando a execução da sequência é concluída"""
        self.is_running_sequence = False
        self.sequence_widget.run_sequence_btn.setEnabled(True)
        self.sequence_widget.stop_sequence_btn.setEnabled(False)
        self.sequence_widget.sequence_status.setText("Concluída")
        self.statusBar().showMessage("Execução de sequência concluída")
        
    def on_sequence_error(self, error_message):
        """Chamado quando ocorre um erro durante a execução da sequência"""
        QMessageBox.critical(self, "Erro na Sequência", error_message)
        self.on_sequence_completed()
        
    def save_program(self):
        """Salva o programa de inspeção atual"""
        if not self.current_sequence:
            QMessageBox.warning(self, "Aviso", "Crie uma sequência primeiro")
            return
            
        filename, _ = QFileDialog.getSaveFileName(self, "Salvar Programa", "", "Arquivos JSON (*.json)")
        
        if filename:
            if not filename.endswith('.json'):
                filename += '.json'
                
            if self.controller.save_positions(filename):
                self.statusBar().showMessage(f"Programa salvo em {filename}")
            else:
                QMessageBox.critical(self, "Erro", "Falha ao salvar o programa")
                
    def load_program(self):
        """Carrega um programa de inspeção salvo"""
        filename, _ = QFileDialog.getOpenFileName(self, "Carregar Programa", "", "Arquivos JSON (*.json)")
        
        if filename:
            if self.controller.load_positions(filename):
                # Atualiza a interface
                self.position_list_widget.clear_positions()
                
                # Adiciona posições carregadas à lista
                for name, position in self.controller.position_manager.positions.items():
                    self.position_list_widget.add_position(position)
                    
                # Se há sequências, usa a primeira como atual
                if self.controller.position_manager.sequences:
                    sequence_name = next(iter(self.controller.position_manager.sequences))
                    self.current_sequence = self.controller.position_manager.sequences[sequence_name]
                    self.sequence_widget.sequence_name.setText(sequence_name)
                    self.sequence_widget.sequence_status.setText(f"Carregada: {len(self.current_sequence.positions)} posições")
                    
                self.statusBar().showMessage(f"Programa carregado de {filename}")
            else:
                QMessageBox.critical(self, "Erro", "Falha ao carregar o programa")
                
    #  LIMPEZA GERAL  (Threads, Timers, Dispositivos)
    def _cleanup_resources(self):
        """Para tudo que possa manter o Qt vivo após o fechamento."""
        if getattr(self, "_already_clean", False):
            return                         # evita executar 2×
        self._already_clean = True

        # 1) Sequências em execução
        if getattr(self, "is_running_sequence", False):
            self.controller.stop_sequence()

        # 2) Timers ------------------------------------------------
        for tm_name in ("update_timer",):
            tm = getattr(self, tm_name, None)
            if tm and tm.isActive():
                tm.stop()
        if getattr(self, "camera_preview", None):
            self.camera_preview.stop_preview()

        # 3) QThreads ---------------------------------------------
        for th_name in ("run_thread", "map_thread", "_move_thread"):
            th = getattr(self, th_name, None)
            if th and th.isRunning():
                th.requestInterruption()
                th.quit()
                th.wait(2000)             # aguarda até 2 s

        # 4) Thread de status do GRBL dentro do controlador CNC
        if getattr(self.controller.cnc, "running", False):
            self.controller.cnc.running = False
            if getattr(self.controller.cnc, "status_thread", None):
                self.controller.cnc.status_thread.join(timeout=2)

        # 5) grbl-streamer (poll thread) --------------------------
        if getattr(self.controller.cnc, "grbl", None):
            try:
                self.controller.cnc.grbl.poll_stop()
                self.controller.cnc.grbl.disconnect()   # fecha serial + join
            except Exception:
                pass

        # 6) Dispositivos -----------------------------------------
        if getattr(self.controller.camera, "is_connected", False):
            self.controller.camera.disconnect()
        if getattr(self.controller.cnc, "is_connected", False):
            self.controller.cnc.disconnect()

    # closeEvent agora só dispara a limpeza
    def closeEvent(self, event):
        self._cleanup_resources()
        event.accept()

class SequenceRunnerThread(QThread):
    """Thread para executar uma sequência de inspeção"""
    image_captured = pyqtSignal(dict)  # Emite resultados da captura
    sequence_completed = pyqtSignal()  # Emite quando a sequência é concluída
    sequence_error = pyqtSignal(str)   # Emite quando ocorre um erro
    
    def __init__(self, controller, sequence_name):
        super().__init__()
        self.controller = controller
        self.sequence_name = sequence_name
        
    def run(self):
        try:
            # Execute a sequência e processe os resultados
            def process_result(result):
                self.image_captured.emit(result)
                
            self.controller.run_sequence(self.sequence_name, process_result)
            self.sequence_completed.emit()
            
        except Exception as e:
            self.sequence_error.emit(str(e))

class MapGeneratorThread(QThread):
    """
    Thread responsável por percorrer a grade, movimentar a CNC e capturar
    as imagens sem travar a GUI.
    """
    progress = pyqtSignal(int, int)       # imagens_capturadas, total
    image_captured = pyqtSignal(object)   # cv2 image (opcional para preview)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, controller, origin, end, sx, sy, folder, prog_name):
        super().__init__()
        self.ctrl = controller
        self.origin = origin
        self.end = end
        self.sx = sx
        self.sy = sy
        self.folder = folder
        self.prog_name = prog_name

    def run(self):        
        log = logging.getLogger("MapGeneratorThread")
        try:
            points = list(self.ctrl._grid_points(self.origin, self.end,
                                             self.sx, self.sy))
            total = len(points)
            os.makedirs(self.folder, exist_ok=True)

            # -- Vai para a origem (somente se não estivermos nela) ----------
            cur = self.ctrl.cnc.get_current_position()
            if (abs(cur['x'] - self.origin['x']) > 1e-3 or
                abs(cur['y'] - self.origin['y']) > 1e-3):
                self.ctrl.cnc.move_to_absolute_position(self.origin['x'],
                                                        self.origin['y'])
                self.ctrl.cnc.wait_for_idle()
            else:
                log.debug("MapGeneratorThread: Já estamos na origem; iniciando varredura sem espera extra.")

            captured = 0
            for r, col, x, y in points:
                if self.isInterruptionRequested():
                    log.warning("Mapa cancelado pelo usuário")
                    self.error.emit("Operação cancelada")
                    return
                self.ctrl.cnc.move_to_absolute_position(x, y)
                self.ctrl.cnc.wait_for_idle()

                img = self.ctrl.camera.capture()
                if img is not None:
                    fname = f"{self.prog_name}_r{r:03d}_c{col:03d}.png"
                    cv2.imwrite(os.path.join(self.folder, fname), img)
                    self.image_captured.emit(img)
                captured += 1
                self.progress.emit(captured, total)
                time.sleep(0.05)

            self.finished.emit()
        except Exception as exc:
            log.exception("Erro na geração do mapa")
            self.error.emit(str(exc))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AOIControllerApp()
    window.show()
    sys.exit(app.exec())