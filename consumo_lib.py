import sys
import cv2
import time
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QLabel, QGroupBox, QGridLayout, QLineEdit, 
                            QComboBox, QListWidget, QListWidgetItem, QFileDialog, QMessageBox, QTabWidget,
                            QSplitter, QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QDialog)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QImage, QFont, QAction

from aoi_lib import CNCAOIController, InspectionPosition
from grbl_streamer import GrblStreamer

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
        
        # Dicionário para mapear itens da lista para objetos de posição
        self.positions = {}
        
    def add_position(self, position):
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
        if current and current in self.positions:
            self.position_selected.emit(self.positions[current])

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
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.positions = []  # List of registered positions
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
    
    def __init__(self, controller, parent=None):
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
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
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
        self.up_button.pressed.connect(lambda: self.start_movement("Y", 1))
        self.up_button.released.connect(self.stop_movement)
        self.down_button.pressed.connect(lambda: self.start_movement("Y", -1))
        self.down_button.released.connect(self.stop_movement)
        self.left_button.pressed.connect(lambda: self.start_movement("X", -1))
        self.left_button.released.connect(self.stop_movement)
        self.right_button.pressed.connect(lambda: self.start_movement("X", 1))
        self.right_button.released.connect(self.stop_movement)
        
        # Add buttons to grid
        movement_layout.addWidget(self.up_button, 0, 1)
        movement_layout.addWidget(self.left_button, 1, 0)
        movement_layout.addWidget(self.right_button, 1, 2)
        movement_layout.addWidget(self.down_button, 2, 1)
        
        # Step size and feed rate controls
        step_layout = QHBoxLayout()
        step_layout.addWidget(QLabel("Step Size:"))
        self.step_size = QLineEdit("1.0")
        step_layout.addWidget(self.step_size)
        step_layout.addWidget(QLabel("mm"))
        
        feed_layout = QHBoxLayout()
        feed_layout.addWidget(QLabel("Feed Rate:"))
        self.feed_rate = QLineEdit("1000")
        feed_layout.addWidget(self.feed_rate)
        feed_layout.addWidget(QLabel("mm/min"))
        
        # Add step and feed rate controls
        movement_layout.addLayout(step_layout, 3, 0, 1, 3)
        movement_layout.addLayout(feed_layout, 4, 0, 1, 3)
        
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
        
    def start_movement(self, axis, direction):
        """Inicia movimento no eixo e direção especificados"""
        logger.debug(f"MOVIMENTO: Iniciando movimento: eixo={axis}, direção={direction}")
        
        if not hasattr(self.controller.cnc, 'grbl') or not self.controller.cnc.is_connected:
            logger.warning("MOVIMENTO: CNC não conectado")
            QMessageBox.warning(self, "Error", "CNC not connected")
            return
            
        try:
            # Captura posição antes do movimento para verificação posterior
            original_position = self.controller.cnc.get_current_position()
            logger.info(f"MOVIMENTO: Posição antes do movimento: {original_position}")
            
            step_size = float(self.step_size.text())
            feed_rate = float(self.feed_rate.text())
            
            # Verifica o modo atual
            is_absolute_mode = self.mode_absolute.isChecked()
            logger.debug(f"MOVIMENTO: Modo atual: {'Absoluto (G90)' if is_absolute_mode else 'Relativo (G91)'}")
            
            if is_absolute_mode:
                # CORREÇÃO: Implementação melhorada para modo absoluto (passo a passo)
                # Enviamos uma sequência atômica de comandos para evitar problemas de sincronização
                
                # 1. Calculamos o tamanho do passo com a direção
                distance = step_size * direction
                
                # 2. Definimos a sequência completa de comandos
                commands = [
                    "G91",  # Modo relativo
                    f"G1 {axis.upper()}{distance} F{feed_rate}",  # Movimento com G1
                    "G90"   # Volta ao modo absoluto
                ]
                
                # 3. Enviamos os comandos com intervalos controlados
                logger.debug(f"MOVIMENTO: Enviando sequência de comandos para movimento absoluto")
                for i, cmd in enumerate(commands):
                    QTimer.singleShot(50 * i, lambda c=cmd: self.controller.cnc.grbl.send_immediately(c))
                    logger.debug(f"MOVIMENTO: Programado envio de comando: {cmd}")
                
            else:
                # Modo contínuo - usa comando $J= para jog
                distance = 100 * direction  # Distância grande para movimento contínuo
                
                if axis.upper() == 'X':
                    command = f"$J=G91 X{distance} F{feed_rate}"
                else:  # Y
                    command = f"$J=G91 Y{distance} F{feed_rate}"
                    
                logger.debug(f"MOVIMENTO: Enviando comando contínuo: {command}")
                self.controller.cnc.grbl.send_immediately(command)
                
            # Agenda verificação após intervalo adequado para permitir que o movimento ocorra
            # Usar intervalo maior (500ms) para dar tempo suficiente ao movimento físico
            QTimer.singleShot(500, lambda: self.verify_position_changed(axis, direction, original_position))
                    
        except Exception as e:
            logger.error(f"MOVIMENTO: Erro ao iniciar movimento: {str(e)}")
            QMessageBox.warning(self, "Error", f"Error starting movement: {str(e)}")

    def verify_position_changed(self, axis, direction, original_position):
        """Verifica se a posição realmente mudou após comando de movimento"""
        try:
            current_position = self.controller.cnc.get_current_position()
            expected_axis = 'x' if axis.upper() == 'X' else 'y'
            
            logger.info(f"VERIFICAÇÃO: Movimento {axis}{'+' if direction > 0 else '-'}: "
                    f"Original={original_position[expected_axis]}, "
                    f"Atual={current_position[expected_axis]}")
            
            if original_position[expected_axis] == current_position[expected_axis]:
                logger.warning(f"VERIFICAÇÃO: Posição {expected_axis} NÃO MUDOU após comando!")
                
                # Forçar atualização de status para tentar obter a posição atual
                if hasattr(self.controller.cnc, 'grbl') and self.controller.cnc.grbl:
                    logger.debug("VERIFICAÇÃO: Enviando comando de status ? para atualizar posição")
                    self.controller.cnc.grbl.send_immediately("?")
        except Exception as e:
            logger.error(f"VERIFICAÇÃO: Erro ao verificar posição: {e}")
            
    def stop_movement(self): 
        """Para o movimento""" 
        logger.debug("MOVIMENTO: Parando movimento")     
        if not hasattr(self.controller.cnc, 'grbl') or not self.controller.cnc.is_connected:
            return
            
        try:
            # Verifica o modo atual
            is_absolute_mode = self.mode_absolute.isChecked()
            
            if is_absolute_mode:
                # No modo absoluto (passo a passo), não precisamos parar o movimento
                # porque ele já deve ter sido concluído quando o botão é liberado
                logger.debug("MOVIMENTO: Modo absoluto, ignorando comando de parada")
                return
            else:
                # Apenas no modo contínuo enviamos os comandos de parada
                # Envia comando de feed hold para parar movimento
                logger.debug("MOVIMENTO: Enviando comando de parada (!)")
                self.controller.cnc.grbl.send_immediately("!")
                
                # Após uma breve pausa, envia comando resume para liberar o estado hold
                logger.debug("MOVIMENTO: Agendando comando de retomada (~) após pausa")
                QTimer.singleShot(100, lambda: self._execute_resume_and_update())
            
        except Exception as e:
            logger.error(f"MOVIMENTO: Erro ao parar movimento: {e}")

    def _execute_resume_and_update(self):
        """Executa o resumo após parada e força atualização de posição em sequência"""
        try:
            # Primeiro envia o comando para retomar após hold
            self.controller.cnc.grbl.send_immediately("~")
            logger.debug("MOVIMENTO: Enviado comando de retomada (~)")
            
            # Agenda uma série de comandos de status para garantir obtenção da posição atualizada
            # Primeira verificação após 150ms
            QTimer.singleShot(150, lambda: self._force_position_update(1))
            
        except Exception as e:
            logger.error(f"MOVIMENTO: Erro ao executar sequência de retomada: {e}")
            
    def _force_position_update(self, attempt=1):
        """Força múltiplas atualizações de posição para garantir precisão
        
        Args:
            attempt: Número da tentativa atual (para limitar tentativas)
        """
        if not hasattr(self.controller.cnc, 'grbl') or not self.controller.cnc.is_connected:
            return
            
        try:
            # Envia comando de status para obter posição atualizada
            logger.debug(f"MOVIMENTO: Forçando atualização de posição - tentativa {attempt}")
            self.controller.cnc.grbl.send_immediately("?")
            
            # Se ainda estamos dentro do limite de tentativas, agenda outra verificação
            if attempt < 3:
                # Aumento progressivo do tempo entre tentativas
                delay = 150 + (attempt * 50)
                QTimer.singleShot(delay, lambda: self._force_position_update(attempt + 1))
                
        except Exception as e:
            logger.error(f"MOVIMENTO: Erro ao forçar atualização de posição: {e}")
            
    def _force_position_update(self, attempt=1):
        """Força múltiplas atualizações de posição para garantir precisão
        
        Args:
            attempt: Número da tentativa atual (para limitar tentativas)
        """
        if not hasattr(self.controller.cnc, 'grbl') or not self.controller.cnc.is_connected:
            return
            
        try:
            # Envia comando de status para obter posição atualizada
            logger.debug(f"MOVIMENTO: Forçando atualização de posição - tentativa {attempt}")
            self.controller.cnc.grbl.send_immediately("?")
            
            # Se ainda estamos dentro do limite de tentativas, agenda outra verificação
            if attempt < 3:
                # Aumento progressivo do tempo entre tentativas (150ms, 200ms, 250ms)
                delay = 150 + (attempt * 50)
                QTimer.singleShot(delay, lambda: self._force_position_update(attempt + 1))
                
        except Exception as e:
            logger.error(f"MOVIMENTO: Erro ao forçar atualização de posição: {e}")
            
    def set_motion_mode(self, mode):
        """Set the motion mode (G90/G91)"""
        if not self.controller.cnc.is_connected:
            return
            
        if mode == "G90":
            self.mode_absolute.setChecked(True)
            self.mode_relative.setChecked(False)
        else:
            self.mode_absolute.setChecked(False)
            self.mode_relative.setChecked(True)
            
        try:
            self.controller.cnc.send_command(mode)
        except Exception as e:
            print(f"Error setting motion mode: {e}")

class AOIControllerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Controle de Inspeção Óptica Automatizada")
        self.setGeometry(100, 100, 1200, 800)
        
        # Inicializa o controlador AOI
        self.controller = CNCAOIController()
        self.current_sequence = None
        self.is_running_sequence = False
        
        # Variável para armazenar o último valor de posição (para comparação)
        self.last_logged_position = None
        
        # Configuração da interface
        self.setup_ui()
        # Configuração do menu
        self.setup_menu()
        # Timer para atualizar a posição – agora conectamos a um método que loga a ação 
        self.update_timer = QTimer(self) 
        self.update_timer.timeout.connect(self.on_update_timer) 
        self.update_timer.start(500) # Atualiza a cada 500ms
        # Variável para armazenar o último valor de posição (para comparação)
        self.last_logged_position = None

    def on_update_timer(self):
        logger.debug("Timer fired: atualizando tela de posição da head.")
        self.update_position_display()
        
    def setup_ui(self):
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        
        # Grupo de conexão
        connection_group = QGroupBox("Conexão")
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
        
        connection_group.setLayout(connection_layout)
        main_layout.addWidget(connection_group)

        # Grupo de Calibração de Movimento 
        calibration_group = QGroupBox("Calibração de Movimento")
        calibration_layout = QHBoxLayout()
        
        calibration_layout.addWidget(QLabel("Pulsos/Revolução:"))
        self.pulses_input = QLineEdit("400")
        calibration_layout.addWidget(self.pulses_input)
        
        calibration_layout.addWidget(QLabel("Passo do Fuso (mm):"))
        self.fuso_input = QLineEdit("5")
        calibration_layout.addWidget(self.fuso_input)
        
        self.apply_calibration_btn = QPushButton("Aplicar Calibração")
        self.apply_calibration_btn.clicked.connect(self.apply_calibration)
        calibration_layout.addWidget(self.apply_calibration_btn)
        
        calibration_group.setLayout(calibration_layout)
        main_layout.addWidget(calibration_group)
        
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

        position_layout.addWidget(QLabel("Y:"), 1, 0)
        self.y_position = QLabel("0.000 mm")
        position_layout.addWidget(self.y_position, 1, 1)

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
        self.movement_widget = MovementControlWidget(self.controller)
        cm_left_layout.addWidget(self.movement_widget)
        
        # Position registry
        self.position_registry = PositionRegistryWidget(self.controller)
        self.position_registry.create_sequence_btn.clicked.connect(self.create_sequence_from_registry)
        cm_left_layout.addWidget(self.position_registry)
        
        # Right side: camera preview
        self.camera_preview = CameraPreviewWidget(self.controller)
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
        
        calibration_action = QAction('Calibração CNC', self)
        calibration_action.triggered.connect(self.show_calibration_dialog)
        tools_menu.addAction(calibration_action)
        
        # Menu de Ajuda
        help_menu = menubar.addMenu('&Ajuda')
        
        about_action = QAction('Sobre', self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

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
            cmd = f"G1 {axis_name}{target_position[axis_name.lower()]} F500"
            logger.info(f"CALIBRAÇÃO: Enviando comando de teste: {cmd}")
            self.controller.cnc.grbl.send_immediately(cmd)
            
            # Aguarda um pouco para o movimento ser concluído
            QTimer.singleShot(1500, lambda: self.verify_calibration_result(axis, initial_position, distance))
            
        except Exception as e:
            logger.error(f"CALIBRAÇÃO: Erro no teste de calibração: {e}")
            QMessageBox.warning(self, "Erro", f"Erro no teste: {str(e)}")

    def verify_calibration_result(self, axis, initial_position, expected_distance):
        """
        Verifica o resultado do teste de calibração.
        
        Args:
            axis: 0 para X, 1 para Y
            initial_position: Posição antes do movimento
            expected_distance: Distância esperada do movimento
        """
        try:
            # Força atualização da posição
            self.controller.cnc.grbl.send_immediately("?")
            
            # Aguarda um pouco para receber a atualização
            time.sleep(0.2)
            
            # Obtem posição atual
            current_position = self.controller.cnc.get_current_position()
            
            # Calcula o deslocamento real
            axis_name = "x" if axis == 0 else "y"
            actual_distance = current_position[axis_name] - initial_position[axis_name]
            
            # Calcula o erro
            error = actual_distance - expected_distance
            error_percent = (error / expected_distance) * 100
            
            # Atualiza o resultado do teste
            result_text = (
                f"Eixo: {axis_name.upper()}\n"
                f"Movimento comandado: {expected_distance:.3f} mm\n"
                f"Movimento real: {actual_distance:.3f} mm\n"
                f"Erro: {error:.3f} mm ({error_percent:.2f}%)\n\n"
            )
            
            if abs(error_percent) < 1:
                result_text += "✅ Calibração excelente (erro < 1%)"
            elif abs(error_percent) < 5:
                result_text += "✓ Calibração aceitável (erro < 5%)"
            else:
                result_text += "❌ Calibração insatisfatória - Ajuste os parâmetros"
            
            if hasattr(self, 'calibration_test_result'):
                self.calibration_test_result.setText(result_text)
                
            logger.info(f"CALIBRAÇÃO: Resultado do teste - {result_text}")
            
        except Exception as e:
            logger.error(f"CALIBRAÇÃO: Erro ao verificar resultado: {e}")

    def set_zero_position(self):
        """Define a posição atual como zero."""
        if not self.controller.cnc.is_connected:
            QMessageBox.warning(self, "Aviso", "CNC não conectada")
            return
        if self.controller.cnc.set_zero():
            self.statusBar().showMessage("Posição zero setada.")
            self.update_position_display()
        else:
            QMessageBox.warning(self, "Erro", "Falha ao setar posição zero.")

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

    def get_current_position(self):
        """
        Retorna a posição atual do CNC.
        Certifica-se de retornar uma cópia do dicionário para evitar alteração acidental.
        """
        logger.debug(f"get_current_position chamado, retornando: {self.current_position}")
        return self.current_position.copy() if hasattr(self, 'current_position') else {'x': 0, 'y': 0, 'z': 0}
            
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
                    
                    if eventstring == "on_stateupdate":
                        if len(data) >= 3:
                            state = data[0]
                            mpos = data[1]  # Tupla de coordenadas da máquina (x, y, z)
                            wpos = data[2]  # Tupla de coordenadas de trabalho (x, y, z)
                            
                            # Log detalhado para depuração
                            logger.debug(f"CALLBACK DETALHADO: state={state}, mpos={mpos}, wpos={wpos}")
                            
                            # Atualiza estado da máquina
                            old_state = self.controller.cnc.machine_status if hasattr(self.controller.cnc, 'machine_status') else None
                            self.controller.cnc.machine_status = state
                            
                            if old_state != state:
                                logger.debug(f"CALLBACK: Estado da máquina mudou de '{old_state}' para '{state}'")
                            
                            # CORREÇÃO CRÍTICA: Verifica tipo e estrutura dos dados antes de usar
                            if isinstance(wpos, (list, tuple)) and len(wpos) >= 2:
                                try:
                                    # CORREÇÃO: Verifica se posição recebida está em formato de tupla ou lista
                                    old_position = None
                                    if hasattr(self.controller.cnc, 'current_position'):
                                        old_position = self.controller.cnc.current_position.copy()
                                    
                                    # Copia informação para evitar referência compartilhada
                                    new_position = {
                                        'x': float(wpos[0]),
                                        'y': float(wpos[1]),
                                        'z': float(wpos[2]) if len(wpos) > 2 else 0
                                    }
                                    
                                    # Registra TODA mudança de posição, mesmo pequena
                                    if old_position != new_position:
                                        logger.info(f"POSIÇÃO ALTERADA: {old_position} → {new_position}")
                                        
                                        # Atualiza a posição no controlador apenas se mudou
                                        self.controller.cnc.current_position = new_position
                                    
                                except (ValueError, TypeError, IndexError) as e:
                                    logger.error(f"CALLBACK: Erro ao processar posição: {e}, wpos={wpos}")
                            elif isinstance(wpos, dict):
                                # Se já for um dicionário, o que pode ocorrer em algumas versões
                                logger.debug("CALLBACK: wpos já é um dicionário")
                                self.controller.cnc.current_position = wpos.copy()
                            else:
                                logger.error(f"CALLBACK: Formato inválido para wpos: {type(wpos)}, valor: {wpos}")
                    
                    # Adiciona mais log para outros eventos importantes
                    elif eventstring == "on_write":
                        logger.debug(f"CALLBACK: Comando enviado: {data[0] if data else 'vazio'}")
                    elif eventstring == "on_read":
                        # Depuração de respostas do GRBL, especialmente status <...>
                        response = data[0] if data else "vazio"
                        if response.startswith("<") and "MPos" in response:
                            logger.debug(f"CALLBACK: Resposta status raw do GRBL: {response}")
                
                # CORREÇÃO: Inicializa o GrblStreamer com callback, SEM passar 'port' ao construtor
                self.controller.cnc.grbl = GrblStreamer(grbl_callback)
                
                # Configura logging (opcional)
                self.controller.cnc.grbl.setup_logging()
                
                # Conecta à porta usando o método correto cnect() (não connect)
                logger.debug(f"CONEXÃO: Conectando à porta {port}")
                self.controller.cnc.grbl.cnect(port, 115200)
                
                # Desbloqueia a máquina
                logger.debug("CONEXÃO: Enviando comando de desbloqueio $X")
                self.controller.cnc.grbl.send_immediately("$X")
                
                # Inicia em modo relativo para jog
                logger.debug("CONEXÃO: Configurando modo relativo G91")
                self.controller.cnc.grbl.send_immediately("G91")
                
                # Inicia verificação de status
                logger.debug("CONEXÃO: Iniciando polling de status")
                self.controller.cnc.grbl.poll_start()
                
                # Atualiza o estado da conexão
                self.controller.cnc.is_connected = True
                self.controller.cnc.machine_status = "Idle"  # Estado inicial presumido
                
                # Atualiza UI
                self.connect_cnc_btn.setText("Desconectar CNC")
                self.cnc_status.setText("Conectado")
                self.statusBar().showMessage(f"CNC conectada na porta {port}")
                
            except Exception as e:
                logger.error(f"CONEXÃO: Falha ao conectar: {str(e)}")
                QMessageBox.critical(self, "Erro", f"Falha ao conectar a CNC: {str(e)}")
                
    def connect_camera(self):
        """Conecta à câmera"""
        if hasattr(self.controller.camera, 'is_connected') and self.controller.camera.is_connected:
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
        """Atualiza a exibição da posição atual""" 
        if not self.controller.cnc.is_connected: 
            logger.debug("update_position_display: CNC não conectada.") 
            return 
        try: 
            position = self.controller.cnc.get_current_position() 
            logger.debug("update_position_display: posição obtida do CNC: %s", position) 
        except Exception as e: 
            logger.error("update_position_display: erro ao obter posição: %s", e) 
            return
        # Verificação para detectar se a posição não mudou (mesmo após movimento)
        if self.last_logged_position is not None:
            if position == self.last_logged_position:
                logger.warning("update_position_display: posição inalterada: %s", position)
            else:
                logger.debug("update_position_display: posição mudou de %s para %s", 
                            self.last_logged_position, position)
        else:
            logger.debug("update_position_display: nenhuma posição anterior registrada.")

        self.last_logged_position = position.copy()

        # Atualiza os labels da interface
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
                
    def closeEvent(self, event):
        """Manipula o evento de fechamento da janela"""
        # Para a execução da sequência, se houver
        if self.is_running_sequence:
            self.controller.stop_sequence()
            
        # Desconecta da câmera e CNC
        if hasattr(self.controller.camera, 'is_connected') and self.controller.camera.is_connected:
            self.controller.camera.disconnect()
            
        if self.controller.cnc.is_connected:
            self.controller.cnc.disconnect()
            
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

# Classe QInputDialog que estava faltando
from PyQt6.QtWidgets import QInputDialog

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AOIControllerApp()
    window.show()
    sys.exit(app.exec())