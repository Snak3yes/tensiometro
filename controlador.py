import sys
import serial
import serial.tools.list_ports
import time
import re
import threading
import logging
from queue import Queue, Empty, PriorityQueue
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QSlider, QGroupBox,
                            QGridLayout, QLineEdit, QComboBox, QProgressBar,
                            QFrame, QPushButton)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QObject
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon

# Importa a biblioteca grbl-streamer
from grbl_streamer import GrblStreamer

# Configuração de logging para diagnóstico
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("grbl_comm.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("GRBLComm")

class GRBLCommunicationThread(QThread):
    """Thread para lidar com a comunicação com GRBL sem bloquear a interface"""
    response_received = pyqtSignal(str)
    status_update = pyqtSignal(str)
    position_update = pyqtSignal(dict)
    error_message = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.serial_port = None
        self.is_connected = False
        self.running = True
        # Usando PriorityQueue como em consumo_lib.py
        self.command_queue = PriorityQueue()
        # Usando um único lock para simplicidade
        self.lock = threading.Lock()
        self.is_moving = False
        self.last_status_check = 0
        self.last_position = {'x': 0, 'y': 0, 'z': 0}
        self.machine_state = "Unknown"
        
        logger.info("GRBLCommunicationThread inicializada")
        
    def set_serial_port(self, serial_port):
        """Define a porta serial para comunicação."""
        logger.info(f"Definindo porta serial: {serial_port}")
        self.serial_port = serial_port
        self.is_connected = True
        
    def disconnect(self):
        """Desconecta a porta serial."""
        logger.info("Desconectando porta serial")
        self.is_connected = False
        if self.serial_port and self.serial_port.is_open:
            try:
                with self.lock:
                    logger.debug("Fechando porta serial")
                    self.serial_port.close()
                    logger.info("Porta serial fechada com sucesso")
            except Exception as e:
                logger.error(f"Erro ao fechar porta serial: {e}")
            
    def send_command(self, command, priority=False):
        """
        Adiciona um comando à fila de execução, com opção de prioridade.
        
        Args:
            command: O comando GCODE
            priority: Se True, o comando tem prioridade
        """
        # Comandos de controle imediato (!, ~, ?) são sempre processados imediatamente
        if command in ['!', '~', '?']:
            priority_level = -1  # Prioridade máxima
        else:
            priority_level = 0 if priority else 1
            
        logger.debug(f"Enviando comando: '{command}' (priority={priority_level})")
        self.command_queue.put((priority_level, command))
    
    def run(self):
        """Método principal da thread - processa os comandos e monitora o status"""
        logger.info("Thread de comunicação iniciada")
        last_diagnostic_time = 0
        last_command_time = 0
        
        while self.running:
            try:
                # Diagnóstico periódico
                current_time = time.time()
                if current_time - last_diagnostic_time > 10:
                    if self.is_connected and self.serial_port and self.serial_port.is_open:
                        buffer_size = self.serial_port.in_waiting if hasattr(self.serial_port, 'in_waiting') else 0
                        logger.info(f"Diagnóstico de comunicação: Conectado, buffer_in={buffer_size}, is_moving={self.is_moving}, estado={self.machine_state}")
                        
                        # Limpar buffer se estiver muito grande
                        if buffer_size > 200:
                            logger.warning(f"Buffer muito grande ({buffer_size} bytes), limpando...")
                            with self.lock:
                                self.serial_port.reset_input_buffer()
                    else:
                        logger.info(f"Diagnóstico de comunicação: Desconectado, is_moving={self.is_moving}, estado={self.machine_state}")
                    last_diagnostic_time = current_time
                
                # Verificar conexão
                if not self.is_connected or not self.serial_port or not self.serial_port.is_open:
                    logger.debug("Não conectado, aguardando...")
                    time.sleep(0.1)
                    continue
                
                # Verificar e processar dados recebidos mesmo sem enviar comando
                if self.serial_port.in_waiting > 0:
                    with self.lock:
                        data = self.serial_port.readline().decode('utf-8', errors='replace').strip()
                        
                    if data:
                        logger.debug(f"Dados recebidos: '{data}'")
                        
                        # Processar dados recebidos
                        if data.startswith('<') and '|' in data:
                            self._parse_status(data)
                        elif "ok" in data or "error" in data:
                            self.response_received.emit(data)
                
                # Limita a taxa de envio de comandos
                can_send_command = True
                if current_time - last_command_time < 0.1:  # Máximo 10 comandos por segundo
                    can_send_command = False
                
                # Processa comandos na fila
                if can_send_command and not self.command_queue.empty():
                    priority, command = self.command_queue.get(block=False)
                    
                    # Comandos prioritários ou de controle podem sempre ser enviados
                    if priority <= 0 or command in ['!', '~', '?']:
                        pass  # Sempre permite
                    # Comandos regulares verificam o estado da máquina
                    elif self.is_moving and "Hold" not in self.machine_state:
                        logger.debug(f"Máquina em movimento, enfileirando comando: {command}")
                        self.command_queue.put((priority, command))
                        self.command_queue.task_done()
                        time.sleep(0.05)
                        continue
                    
                    # Preparar comando
                    if not command.endswith('\n'):
                        command += '\n'
                    
                    # Identificar tipo de comando
                    is_movement_cmd = any(cmd in command for cmd in ['G0', 'G1', 'G2', 'G3'])
                    
                    # Enviar comando
                    with self.lock:
                        logger.debug(f"Enviando bytes: {command.encode()}")
                        self.serial_port.write(command.encode())
                        self.serial_port.flush()
                        
                        # Se for comando de movimento, atualiza estado
                        if is_movement_cmd:
                            logger.info("Atualizando flag is_moving para True")
                            self.is_moving = True
                        
                        # Atualiza timestamp
                        last_command_time = current_time
                        
                        # Para comandos rápidos (controle), não espera resposta
                        if command.strip() in ['!', '~', '?']:
                            self.command_queue.task_done()
                            continue
                        
                        # Para outros comandos, espera resposta
                        start_time = time.time()
                        response = ""
                        
                        # Lê respostas com timeout curto (200ms)
                        while (time.time() - start_time) < 0.2:
                            if self.serial_port.in_waiting > 0:
                                line = self.serial_port.readline().decode('utf-8', errors='replace').strip()
                                if line:
                                    if not line.startswith('<'):
                                        response += line + " "
                                        # Se recebeu ok ou error, finaliza
                                        if "ok" in line or "error" in line:
                                            break
                                    # Status atualiza estado mas não é considerado resposta final
                                    elif line.startswith('<') and '|' in line:
                                        self._parse_status(line)
                            else:
                                time.sleep(0.01)
                    
                    # Finaliza comando
                    self.command_queue.task_done()
                    
                    # Processa resposta
                    if response:
                        self.response_received.emit(response.strip())
                        if is_movement_cmd and "error" in response.lower():
                            logger.warning(f"Erro GRBL em comando de movimento: {response}")
                            self.error_message.emit(f"Erro GRBL: {response}")
                            self.is_moving = False
                
                # Verificação periódica de status
                if (current_time - self.last_status_check) > 0.2:
                    self._check_status_simple()
                    self.last_status_check = current_time
                
                # Pausa pequena para não consumir CPU
                time.sleep(0.01)
                
            except Exception as e:
                logger.error(f"Erro na thread de comunicação: {e}", exc_info=True)
                self.error_message.emit(f"Erro na thread de comunicação: {str(e)}")
                time.sleep(0.1)
    
    def _check_status_simple(self):
        """Verifica o status atual do GRBL (implementação simplificada)"""
        try:
            if not self.is_connected or not self.serial_port or not self.serial_port.is_open:
                return
                
            # Apenas envia o comando de status
            with self.lock:
                logger.debug("Enviando comando de status '?'")
                self.serial_port.write(b"?")
                self.serial_port.flush()
                # Não aguardamos resposta aqui, ela será processada no próximo ciclo
                
        except Exception as e:
            logger.error(f"Erro ao verificar status: {e}")
    
    # Modifique o método _parse_status na classe GRBLCommunicationThread
    def _parse_status(self, status_line):
        """
        Analisa a linha de status do GRBL.
        
        Formato típico: <Idle|MPos:0.000,0.000,0.000|FS:0,0|WCO:0.000,0.000,0.000>
        """
        try:
            logger.debug(f"Analisando status: '{status_line}'")
            
            # Extrai o estado da máquina
            if status_line.startswith('<') and '|' in status_line:
                state = status_line[1:status_line.find('|')]
                old_state = self.machine_state
                self.machine_state = state
                logger.debug(f"Estado da máquina: {old_state} -> {state}")
                
                # Atualiza a flag de movimento com base no estado
                old_moving = self.is_moving
                
                # Estados onde a máquina está definitivamente parada
                if state in ["Idle", "Alarm", "Error", "Door", "Check", "Home"]:
                    self.is_moving = False
                # Estados onde a máquina está definitivamente em movimento
                elif state in ["Run", "Jog"]:
                    self.is_moving = True
                # Estado Hold - a máquina está temporariamente parada, mas não completamente Idle
                elif state.startswith("Hold"):
                    # Para os nossos propósitos, consideramos Hold como "não está em movimento"
                    # Isso permite que novos comandos sejam enviados após liberar o Hold
                    self.is_moving = False
                
                if old_moving != self.is_moving:
                    logger.info(f"Flag is_moving atualizada: {old_moving} -> {self.is_moving}")
                
                # Emite estado para atualizar UI quando o estado muda
                if old_state != state:
                    self.status_update.emit(status_line)
            
            # Extrai a posição
            match = re.search(r'(?:MPos|WPos):(-?\d+\.\d+),(-?\d+\.\d+),(-?\d+\.\d+)', status_line)
            if match:
                x, y, z = match.groups()
                position = {
                    'x': float(x),
                    'y': float(y),
                    'z': float(z)
                }
                
                # Verifica se houve mudança significativa na posição para log
                position_changed = (
                    abs(position['x'] - self.last_position['x']) > 0.001 or
                    abs(position['y'] - self.last_position['y']) > 0.001 or
                    abs(position['z'] - self.last_position['z']) > 0.001
                )
                
                # Se houve mudança significativa, registra no log
                if position_changed:
                    logger.info(f"POSIÇÃO ALTERADA: {self.last_position} → {position}")
                
                # Sempre emite a atualização e atualiza a última posição
                self.position_update.emit(position)
                self.last_position = position
        
        except Exception as e:
            logger.error(f"Erro ao analisar status: {e}", exc_info=True)

class SignalEmitter(QObject):
    """Classe para emitir sinais Qt de dentro da biblioteca grbl-streamer"""
    response_received = pyqtSignal(str)
    status_update = pyqtSignal(dict)
    error_message = pyqtSignal(str)

class DirectionalButton(QPushButton):
    """Botão direcional com setas para controle intuitivo de movimento"""
    def __init__(self, direction, parent=None):
        super().__init__(parent)
        self.direction = direction
        
        # Configura a aparência do botão
        self.setMinimumSize(60, 60)
        self.setMaximumSize(60, 60)
        
        # Define texto/símbolo com base na direção
        if direction == "up":
            self.setText("↑")
        elif direction == "down":
            self.setText("↓")
        elif direction == "left":
            self.setText("←")
        elif direction == "right":
            self.setText("→")
        
        # Estiliza o botão para parecer com botão de jog
        font = QFont()
        font.setBold(True)
        font.setPointSize(20)
        self.setFont(font)

class JogButton(QPushButton):
    """Botão personalizado para movimentos jog"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        
        # Estilização
        self.setMinimumSize(60, 60)
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        self.setFont(font)

class PositionDisplay(QFrame):
    """Widget para exibir a posição atual da máquina"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        
        layout = QGridLayout(self)
        
        # Rótulos para cabeçalhos
        title_font = QFont()
        title_font.setBold(True)
        
        title_label = QLabel("Posição Atual:")
        title_label.setFont(title_font)
        layout.addWidget(title_label, 0, 0, 1, 2)
        
        layout.addWidget(QLabel("X:"), 1, 0)
        layout.addWidget(QLabel("Y:"), 2, 0)
        
        # Valores de posição
        self.x_pos = QLabel("0.000")
        self.y_pos = QLabel("0.000")
        
        pos_font = QFont("Monospace")
        pos_font.setPointSize(12)
        pos_font.setBold(True)
        
        self.x_pos.setFont(pos_font)
        self.y_pos.setFont(pos_font)
        
        self.x_pos.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.y_pos.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        layout.addWidget(self.x_pos, 1, 1)
        layout.addWidget(self.y_pos, 2, 1)
        
    def update_position(self, position):
        """Atualiza os valores de posição exibidos"""
        self.x_pos.setText(f"{position.get('x', 0):.3f} mm")
        self.y_pos.setText(f"{position.get('y', 0):.3f} mm")

class JogController:
    """Controlador dedicado para operações de jogging"""
    
    def __init__(self, comm_thread):
        self.comm_thread = comm_thread
        self.is_jogging = False
        self.current_direction = None
        self.current_axis = None
        self.jog_timer = QTimer()
        self.jog_timer.timeout.connect(self._execute_jog_step)
        self.jog_step_size = 1.0  # Aumentado para 1mm por passo para movimento mais visível
        self.jog_speed = 1000     # mm/min
        self.last_command_time = 0
        self.command_sent = False
        
    def start_jog(self, axis, direction):
        """Inicia o modo de jogging contínuo"""
        logger.debug(f"JogController: iniciando jog {axis}{'+' if direction > 0 else '-'}")
        
        # Se já estiver em jog com os mesmos parâmetros, não reinicia
        if self.is_jogging and self.current_axis == axis and self.current_direction == direction:
            return
            
        # Para qualquer jog anterior antes de iniciar um novo
        self.stop_jog()
        
        # Configura o novo movimento
        self.is_jogging = True
        self.current_axis = axis
        self.current_direction = direction
        self.command_sent = False
        
        # Inicia o processo de jog com base no estado atual da máquina
        if "Hold" in self.comm_thread.machine_state:
            logger.debug("JogController: máquina em Hold, enviando comando de retomada")
            self.comm_thread.send_command("~", priority=True)
            # Aguarda para dar tempo ao comando de retomada ser processado
            QTimer.singleShot(100, self._prepare_for_jog)
        else:
            self._prepare_for_jog()
    
    def _prepare_for_jog(self):
        """Prepara a máquina para realizar um movimento de jog"""
        # Garante modo relativo
        self.comm_thread.send_command("G91", priority=True)
        
        # Espera um curto período para garantir que o comando seja processado
        QTimer.singleShot(50, self._start_jog_timer)
    
    def _start_jog_timer(self):
        """Inicia o timer que controla o movimento de jog"""
        if not self.is_jogging:
            return  # Verifica se o jog ainda está ativo
            
        # Executa o primeiro movimento imediatamente
        self._execute_jog_step()
        
        # Configura o timer para repetir o movimento periodicamente
        # Intervalo maior para melhor estabilidade
        self.jog_timer.start(300)  # 300ms entre passos
    
    def _execute_jog_step(self):
        """Executa um único passo de jog"""
        if not self.is_jogging:
            return
        
        # Impede o envio de comandos muito frequentes
        current_time = time.time()
        if current_time - self.last_command_time < 0.2:
            return
            
        # Verifica condições de estado da máquina
        if "Hold" in self.comm_thread.machine_state:
            logger.debug("JogController: detectado estado Hold durante movimento, enviando retomada")
            self.comm_thread.send_command("~", priority=True)
            return
            
        # Calcula a distância do movimento
        distance = self.current_direction * self.jog_step_size
        
        # Cria o comando de movimento
        if self.current_axis == "X":
            command = f"G0 X{distance} F{self.jog_speed}"
        else:  # assume "Y"
            command = f"G0 Y{distance} F{self.jog_speed}"
            
        logger.debug(f"JogController: enviando comando {command}")
        
        # Envia o comando com alta prioridade
        self.comm_thread.send_command(command, priority=True)
        self.last_command_time = current_time
        self.command_sent = True
    
    def stop_jog(self):
        """Para o movimento jog"""
        if not self.is_jogging:
            return
            
        logger.debug("JogController: parando jog")
        
        # Interrompe o timer
        self.jog_timer.stop()
        self.is_jogging = False
        
        # Envia comando de parada apenas se um comando foi enviado antes
        if self.command_sent:
            # Envia feed hold para parar movimento
            self.comm_thread.send_command("!", priority=True)
            
            # Após uma pequena pausa, envia comando de retomada para liberar máquina
            QTimer.singleShot(150, self._send_resume_after_stop)
            
    def _send_resume_after_stop(self):
        """Envia comando de retomada após parada para liberar a máquina"""
        # Envio do comando "~" para liberar máquina do estado Hold
        self.comm_thread.send_command("~", priority=True)
        
        # Solicita status atualizado
        QTimer.singleShot(50, lambda: self.comm_thread.send_command("?", priority=True))


class GRBLController(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Controle CNC GRBL Avançado")
        self.setGeometry(100, 100, 1000, 700)
        
        # Inicialização do sistema de comunicação
        self.signals = SignalEmitter()
        self.grbl = None
        self.is_connected = False
        self.current_position = {'x': 0, 'y': 0, 'z': 0}
        self.machine_status = "Desconectado"
        self.last_command = ""
        self.last_response = ""
        self.last_error = ""
        
        # Controle de jog contínuo
        self.jogging = False
        self.current_jog_axis = None
        self.current_jog_direction = None
        
        # Estado da máquina
        self.current_motion_mode = "G91"  # Começa em modo relativo
        
        # Conectar os sinais
        self.signals.response_received.connect(self.on_response_received)
        self.signals.status_update.connect(self.on_status_update)
        self.signals.error_message.connect(self.on_error_message)
        
        # Configuração da interface
        self.init_ui()
        
        # Timer para atualizar o status da interface
        self.ui_timer = QTimer(self)
        self.ui_timer.timeout.connect(self.update_ui_state)
        self.ui_timer.start(300)  # Atualiza a cada 300ms
        
    def init_ui(self):
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        
        # Grupo de conexão
        connection_group = QGroupBox("Conexão Arduino")
        connection_layout = QHBoxLayout()
        
        self.port_combo = QComboBox()
        
        self.connect_button = QPushButton("Conectar")
        self.connect_button.clicked.connect(self.toggle_connection)
        
        self.refresh_button = QPushButton("Atualizar Portas")
        self.refresh_button.clicked.connect(self.refresh_ports)
        
        connection_layout.addWidget(QLabel("Porta:"))
        connection_layout.addWidget(self.port_combo)
        connection_layout.addWidget(self.connect_button)
        connection_layout.addWidget(self.refresh_button)
        connection_group.setLayout(connection_layout)
        
        main_layout.addWidget(connection_group)
        
        # Layout horizontal para controles e status
        control_status_layout = QHBoxLayout()
        
        # Grupo de controle dos eixos (lado esquerdo)
        axis_group = QGroupBox("Controle de Eixos")
        axis_layout = QGridLayout()
        
        # Controles do eixo X
        axis_layout.addWidget(QLabel("Eixo X:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        
        x_control_layout = QHBoxLayout()
        self.x_minus_button = JogButton("X-")
        self.x_minus_button.pressed.connect(lambda: self.start_jog("X", -1))
        self.x_minus_button.released.connect(self.stop_jog)
        
        self.x_plus_button = JogButton("X+")
        self.x_plus_button.pressed.connect(lambda: self.start_jog("X", 1))
        self.x_plus_button.released.connect(self.stop_jog)
        
        self.x_distance = QLineEdit("1")
        self.x_distance.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        x_control_layout.addWidget(self.x_minus_button)
        x_control_layout.addWidget(self.x_distance)
        x_control_layout.addWidget(self.x_plus_button)
        
        axis_layout.addLayout(x_control_layout, 0, 1)
        
        # Controles do eixo Y
        axis_layout.addWidget(QLabel("Eixo Y:"), 1, 0, Qt.AlignmentFlag.AlignRight)
        
        y_control_layout = QHBoxLayout()
        self.y_minus_button = JogButton("Y-")
        self.y_minus_button.pressed.connect(lambda: self.start_jog("Y", -1))
        self.y_minus_button.released.connect(self.stop_jog)
        
        self.y_plus_button = JogButton("Y+")
        self.y_plus_button.pressed.connect(lambda: self.start_jog("Y", 1))
        self.y_plus_button.released.connect(self.stop_jog)
        
        self.y_distance = QLineEdit("1")
        self.y_distance.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        y_control_layout.addWidget(self.y_minus_button)
        y_control_layout.addWidget(self.y_distance)
        y_control_layout.addWidget(self.y_plus_button)
        
        axis_layout.addLayout(y_control_layout, 1, 1)
        
        # Controle direcional em formato de teclado numérico (8, 4, 6, 2)
        directional_group = QGroupBox("Controle Direcional")
        directional_layout = QGridLayout()
        
        self.dir_up_button = DirectionalButton("up")
        self.dir_left_button = DirectionalButton("left")
        self.dir_right_button = DirectionalButton("right")
        self.dir_down_button = DirectionalButton("down")
        
        # Conectar eventos de pressionar/soltar para movimentos contínuos
        self.dir_up_button.pressed.connect(lambda: self.start_continuous_jog("Y", 1))
        self.dir_up_button.released.connect(self.stop_continuous_jog)
        
        self.dir_down_button.pressed.connect(lambda: self.start_continuous_jog("Y", -1))
        self.dir_down_button.released.connect(self.stop_continuous_jog)
        
        self.dir_left_button.pressed.connect(lambda: self.start_continuous_jog("X", -1))
        self.dir_left_button.released.connect(self.stop_continuous_jog)
        
        self.dir_right_button.pressed.connect(lambda: self.start_continuous_jog("X", 1))
        self.dir_right_button.released.connect(self.stop_continuous_jog)
        
        # Organização em grade para parecer com teclado numérico
        directional_layout.addWidget(self.dir_up_button, 0, 1)
        directional_layout.addWidget(self.dir_left_button, 1, 0)
        directional_layout.addWidget(self.dir_right_button, 1, 2)
        directional_layout.addWidget(self.dir_down_button, 2, 1)
        
        # Jog step - valor incremental para os botões direcionais
        step_layout = QHBoxLayout()
        step_layout.addWidget(QLabel("Passo:"))
        self.jog_step = QLineEdit("1")
        self.jog_step.setAlignment(Qt.AlignmentFlag.AlignCenter)
        step_layout.addWidget(self.jog_step)
        step_layout.addWidget(QLabel("mm"))
        
        directional_layout.addLayout(step_layout, 3, 0, 1, 3)
        directional_group.setLayout(directional_layout)
        
        # Adiciona o grupo direcional ao layout principal
        axis_layout.addWidget(directional_group, 2, 0, 2, 2)
        
        # Velocidade de movimento (feed rate)
        axis_layout.addWidget(QLabel("Velocidade:"), 4, 0, Qt.AlignmentFlag.AlignRight)
        
        feed_layout = QHBoxLayout()
        self.feed_rate = QLineEdit("1000")
        self.feed_rate.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Slider para controle de velocidade
        self.feed_slider = QSlider(Qt.Orientation.Horizontal)
        self.feed_slider.setMinimum(100)
        self.feed_slider.setMaximum(5000)
        self.feed_slider.setValue(1000)
        self.feed_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.feed_slider.setTickInterval(500)
        
        # Conectar slider e campo de texto
        self.feed_slider.valueChanged.connect(self.update_feed_rate)
        self.feed_rate.textChanged.connect(self.update_feed_slider)
        
        feed_layout.addWidget(self.feed_rate)
        feed_layout.addWidget(QLabel("mm/min"))
        feed_layout.addWidget(self.feed_slider)
        
        axis_layout.addLayout(feed_layout, 4, 1)
        
        # Modos de movimento
        axis_layout.addWidget(QLabel("Modo:"), 5, 0, Qt.AlignmentFlag.AlignRight)
        
        mode_layout = QHBoxLayout()
        self.mode_absolute = QPushButton("Passo a Passo (G90)")
        self.mode_absolute.setCheckable(True)
        self.mode_absolute.clicked.connect(lambda: self.set_motion_mode("G90"))

        self.mode_relative = QPushButton("Contínuo (G91)")
        self.mode_relative.setCheckable(True)
        self.mode_relative.setChecked(True)  # Começa em modo relativo
        self.mode_relative.clicked.connect(lambda: self.set_motion_mode("G91"))

        mode_layout.addWidget(self.mode_absolute)
        mode_layout.addWidget(self.mode_relative)
        
        axis_layout.addLayout(mode_layout, 5, 1)
        
        # Botões de controle da máquina
        control_buttons_layout = QGridLayout()
        
        self.home_button = QPushButton("Home ($H)")
        self.home_button.clicked.connect(self.home)
        
        self.unlock_button = QPushButton("Desbloquear ($X)")
        self.unlock_button.clicked.connect(self.unlock)
        
        self.zero_button = QPushButton("Zerar Posição (G92)")
        self.zero_button.clicked.connect(self.set_zero)

        self.reset_button = QPushButton("Reset Alarme")
        self.reset_button.setStyleSheet("background-color: orange; color: white; font-weight: bold;")
        self.reset_button.clicked.connect(self.reset_alarm)
        
        self.stop_button = QPushButton("PARAR (!)")
        self.stop_button.setStyleSheet("background-color: red; color: white; font-weight: bold;")
        self.stop_button.clicked.connect(self.emergency_stop)
        
        control_buttons_layout.addWidget(self.home_button, 0, 0)
        control_buttons_layout.addWidget(self.unlock_button, 0, 1)
        control_buttons_layout.addWidget(self.zero_button, 1, 0)
        control_buttons_layout.addWidget(self.reset_button, 1, 1)  # Novo botão de reset
        control_buttons_layout.addWidget(self.stop_button, 2, 0, 1, 2)  # Ocupa duas colunas
        
        axis_layout.addLayout(control_buttons_layout, 6, 0, 1, 2)
        
        # Console de comandos
        axis_layout.addWidget(QLabel("Comando GCODE:"), 7, 0, 1, 2)
        
        command_layout = QHBoxLayout()
        self.command_input = QLineEdit()
        self.command_input.returnPressed.connect(self.send_command)
        
        self.send_button = QPushButton("Enviar")
        self.send_button.clicked.connect(self.send_command)
        
        command_layout.addWidget(self.command_input)
        command_layout.addWidget(self.send_button)
        
        axis_layout.addLayout(command_layout, 8, 0, 1, 2)
        
        axis_group.setLayout(axis_layout)
        control_status_layout.addWidget(axis_group)
        
        # Painel de status (lado direito)
        status_group = QGroupBox("Status da Máquina")
        status_layout = QVBoxLayout()
        
        # Widget de exibição de posição
        self.position_display = PositionDisplay()
        status_layout.addWidget(self.position_display)
        
        # Status da máquina
        status_layout.addWidget(QLabel("Estado:"))
        self.machine_state_label = QLabel("Desconectado")
        self.machine_state_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        status_layout.addWidget(self.machine_state_label)
        
        # Últimos comandos e respostas
        status_layout.addWidget(QLabel("Último Comando:"))
        self.last_command_label = QLabel("-")
        status_layout.addWidget(self.last_command_label)
        
        status_layout.addWidget(QLabel("Última Resposta:"))
        self.last_response_label = QLabel("-")
        status_layout.addWidget(self.last_response_label)
        
        # Log de comunicação
        status_layout.addWidget(QLabel("Log de Comunicação:"))
        self.comm_log = QLineEdit()
        self.comm_log.setReadOnly(True)
        status_layout.addWidget(self.comm_log)
        
        # Otimizações de comunicação
        optimization_group = QGroupBox("Otimizações")
        optimization_layout = QVBoxLayout()
        
        self.fast_mode_check = QPushButton("Modo Rápido (Sem Door Check)")
        self.fast_mode_check.setCheckable(True)
        self.fast_mode_check.clicked.connect(self.toggle_fast_mode)
        self.fast_mode_check.setToolTip("Desativa verificação de porta para movimentos mais rápidos")
        
        optimization_layout.addWidget(self.fast_mode_check)
        optimization_group.setLayout(optimization_layout)
        status_layout.addWidget(optimization_group)
        
        status_layout.addStretch()
        status_group.setLayout(status_layout)
        control_status_layout.addWidget(status_group)
        
        # Proporção entre painéis de controle e status
        control_status_layout.setStretch(0, 3)
        control_status_layout.setStretch(1, 2)
        
        main_layout.addLayout(control_status_layout)
        
        # Barra de status
        self.statusBar = self.statusBar()
        self.statusBar.showMessage("Pronto para conexão")
        
        # Desabilitar controles até que a conexão seja estabelecida
        self.toggle_controls(False)
        
        # Atualizar portas
        self.refresh_ports()

    def reset_alarm(self):
        """Reset o estado de alarme e libera a máquina para movimento"""
        if not self.is_connected or not self.grbl:
            return
            
        try:
            logger.debug("Resetando alarme")
            
            # Sequência completa de reset para garantir que o alarme seja cancelado
            # 1. Envia comando kill alarm
            self.grbl.send_immediately("$X")
            
            # 2. Pausa breve e mais comandos para garantir a recuperação
            QTimer.singleShot(150, lambda: self.grbl.send_immediately("~"))  # Resume
            
            # 3. Restaura o modo de movimento atual
            QTimer.singleShot(300, lambda: self.grbl.send_immediately(self.current_motion_mode))
            
            # 4. Soft reset para caso de falha dos comandos acima
            QTimer.singleShot(400, lambda: self.grbl.send_immediately("\x18"))  # Ctrl+X (soft reset)
            
            # 5. Restaura novamente o modo após soft reset
            QTimer.singleShot(600, lambda: self.grbl.send_immediately(self.current_motion_mode))
            
            self.statusBar.showMessage("Reset de alarme enviado, máquina deve estar pronta em breve")
        except Exception as e:
            logger.error(f"Erro ao resetar alarme: {str(e)}", exc_info=True)
            self.statusBar.showMessage(f"Erro: {str(e)}")
        
    def refresh_ports(self):
        """Detecta automaticamente as portas seriais disponíveis"""
        self.port_combo.clear()
        
        available_ports = [port.device for port in serial.tools.list_ports.comports()]
        
        if not available_ports:
            self.statusBar.showMessage("Nenhuma porta serial encontrada")
            return
            
        self.port_combo.addItems(available_ports)
        
        # Verificar se COM9 está na lista e selecioná-la
        com9_index = self.port_combo.findText("COM9")
        if com9_index >= 0:
            self.port_combo.setCurrentIndex(com9_index)
            self.statusBar.showMessage("Arduino detectado na porta COM9")
        else:
            self.statusBar.showMessage(f"Portas encontradas: {', '.join(available_ports)}")
    
    def toggle_connection(self):
        """Conecta/desconecta da máquina CNC"""
        if not self.is_connected:
            try:
                port = self.port_combo.currentText()
                if not port:
                    self.statusBar.showMessage("Nenhuma porta selecionada")
                    return
                
                # Mensagem de status
                self.statusBar.showMessage(f"Conectando à porta {port}...")
                
                # CORREÇÃO: Inicializar a comunicação com o GRBL usando a API correta da biblioteca
                def grbl_callback(eventstring, *data):
                    """Callback para eventos do GrblStreamer"""
                    logger.debug(f"GRBL evento: {eventstring}, dados: {data}")
                    
                    # Processar eventos específicos
                    if eventstring == "on_stateupdate":
                        # Formato: on_stateupdate(state, mpos, wpos)
                        if len(data) >= 3:
                            state = data[0]
                            machine_pos = data[1]  # (x, y, z)
                            
                            # Atualiza estado da máquina
                            self.machine_status = state
                            
                            # Atualiza posição
                            if len(machine_pos) >= 3:
                                self.current_position = {
                                    'x': machine_pos[0],
                                    'y': machine_pos[1],
                                    'z': machine_pos[2] if len(machine_pos) > 2 else 0
                                }
                                self.signals.status_update.emit(self.current_position)
                    
                    elif eventstring == "on_processed_command":
                        # Respostas a comandos
                        if len(data) >= 2:
                            response = data[1]
                            self.signals.response_received.emit(str(response))
                    
                    elif eventstring == "on_error":
                        # Mensagens de erro
                        if data:
                            error_msg = str(data[0])
                            self.signals.error_message.emit(error_msg)
                
                # Inicializa com o callback
                self.grbl = GrblStreamer(grbl_callback)
                
                # Configura logging (opcional)
                self.grbl.setup_logging()
                
                # Conecta usando o método correto
                self.grbl.cnect(port, 115200)
                
                # Desbloqueia a máquina
                self.grbl.send_immediately("$X")
                
                # Iniciar em modo relativo para jog
                self.grbl.send_immediately("G91")
                self.mode_relative.setChecked(True)
                self.mode_absolute.setChecked(False)
                
                # Inicia verificação de status
                self.grbl.poll_start()
                
                # Atualizar o estado da interface
                self.is_connected = True
                self.machine_status = "Idle"  # Estado inicial presumido
                self.connect_button.setText("Desconectar")
                self.machine_state_label.setText("Conectado")
                self.statusBar.showMessage(f"Conectado ao GRBL na porta {port}")
                self.toggle_controls(True)
                    
            except Exception as e:
                logger.error(f"Erro ao conectar: {str(e)}", exc_info=True)
                self.statusBar.showMessage(f"Erro: {str(e)}")
        else:
            # Desconectar
            self._stop_jog_and_movements()
            
            if self.grbl:
                try:
                    # Parar verificação de status
                    self.grbl.poll_stop()
                    
                    # Desconectar
                    self.grbl.disconnect()
                    self.grbl = None
                except Exception as e:
                    logger.error(f"Erro ao desconectar: {str(e)}", exc_info=True)
            
            self.is_connected = False
            self.machine_status = "Desconectado"
            self.connect_button.setText("Conectar")
            self.machine_state_label.setText("Desconectado")
            self.statusBar.showMessage("Desconectado")
            self.toggle_controls(False)
    
    def _setup_callbacks(self):
        """Configura callbacks para eventos do GrblStreamer"""
        if not self.grbl:
            return
            
        # Configurar callbacks para o grbl-streamer
        # (A API exata pode variar com base na implementação da biblioteca)
        self.grbl.register_status_callback(self._on_status_update)
        self.grbl.register_response_callback(self._on_response_received)
        self.grbl.register_error_callback(self._on_error_message)
    
    def _start_status_polling(self):
        """Inicia polling periódico de status"""
        if not self.is_connected or not self.grbl:
            return
            
        # Criar thread de consulta de status (se a lib não fizer isso automaticamente)
        self.status_thread = threading.Thread(target=self._status_polling_thread, daemon=True)
        self.status_thread.start()
    
    def _status_polling_thread(self):
        """Thread para consulta periódica de status"""
        while self.is_connected and self.grbl:
            try:
                # Requisição de status ao GRBL a cada 200ms
                self.grbl.get_status()
                time.sleep(0.2)
            except Exception as e:
                logger.error(f"Erro na consulta de status: {str(e)}", exc_info=True)
                time.sleep(0.5)  # Maior intervalo em caso de erro
    
    def _on_status_update(self, status_data):
        """Callback quando o status é atualizado pelo grbl-streamer"""
        try:
            # Interpretar os dados de status recebidos do grbl-streamer
            # (O formato exato pode variar com base na implementação da biblioteca)
            
            # Obtém o estado da máquina
            state = status_data.get('state', 'Unknown')
            
            # Obtém a posição
            position = status_data.get('position', {})
            if position:
                self.current_position = {
                    'x': position.get('x', 0),
                    'y': position.get('y', 0),
                    'z': position.get('z', 0)
                }
            
            # Emite sinais para atualizar a interface
            self.machine_status = state
            self.signals.status_update.emit(self.current_position)
            
        except Exception as e:
            logger.error(f"Erro ao processar status: {str(e)}", exc_info=True)
    
    def _on_response_received(self, response):
        """Callback quando uma resposta é recebida pelo grbl-streamer"""
        try:
            self.last_response = response
            self.signals.response_received.emit(response)
        except Exception as e:
            logger.error(f"Erro ao processar resposta: {str(e)}", exc_info=True)
    
    def _on_error_message(self, error):
        """Callback quando um erro é recebido pelo grbl-streamer"""
        try:
            self.last_error = error
            self.signals.error_message.emit(error)
        except Exception as e:
            logger.error(f"Erro ao processar mensagem de erro: {str(e)}", exc_info=True)
    
    def toggle_controls(self, enabled):
        """Habilita/desabilita os controles com base no estado de conexão"""
        # Controles de eixos e botões de movimento
        self.x_minus_button.setEnabled(enabled)
        self.x_plus_button.setEnabled(enabled)
        self.y_minus_button.setEnabled(enabled)
        self.y_plus_button.setEnabled(enabled)
        
        # Botões direcionais
        self.dir_up_button.setEnabled(enabled)
        self.dir_down_button.setEnabled(enabled)
        self.dir_left_button.setEnabled(enabled)
        self.dir_right_button.setEnabled(enabled)
        self.jog_step.setEnabled(enabled)
        
        # Campos de entrada
        self.x_distance.setEnabled(enabled)
        self.y_distance.setEnabled(enabled)
        self.feed_rate.setEnabled(enabled)
        self.feed_slider.setEnabled(enabled)
        
        # Botões de controle
        self.home_button.setEnabled(enabled)
        self.unlock_button.setEnabled(enabled)
        self.zero_button.setEnabled(enabled)
        self.stop_button.setEnabled(enabled)
        self.fast_mode_check.setEnabled(enabled)
        
        # Modos de movimento
        self.mode_absolute.setEnabled(enabled)
        self.mode_relative.setEnabled(enabled)
        
        # Console de comandos
        self.command_input.setEnabled(enabled)
        self.send_button.setEnabled(enabled)
    
    def update_ui_state(self):
        """Atualiza o estado da interface com base no status da máquina"""
        # Atualizar texto de status
        self.machine_state_label.setText(self.machine_status)
        
        # Habilitar/desabilitar botão de reset com base no estado
        is_alarm = self.machine_status == "Alarm"
        self.reset_button.setEnabled(is_alarm)
        
        # Colorir o status da máquina e aplicar estilo ao botão de reset
        if self.machine_status == "Idle":
            self.machine_state_label.setStyleSheet("color: green;")
            self.reset_button.setStyleSheet("background-color: #E0E0E0; color: black;")
        elif self.machine_status == "Run" or self.machine_status == "Jog":
            self.machine_state_label.setStyleSheet("color: blue;")
            self.reset_button.setStyleSheet("background-color: #E0E0E0; color: black;")
        elif self.machine_status == "Alarm":
            self.machine_state_label.setStyleSheet("color: red;")
            self.reset_button.setStyleSheet("background-color: orange; color: white; font-weight: bold;")
        elif self.machine_status == "Hold":
            self.machine_state_label.setStyleSheet("color: orange;")
            self.reset_button.setStyleSheet("background-color: #E0E0E0; color: black;")
        else:
            self.machine_state_label.setStyleSheet("")
            self.reset_button.setStyleSheet("background-color: #E0E0E0; color: black;")
            
        # Atualizar display de posição
        self.position_display.update_position(self.current_position)
    
    def update_feed_rate(self, value):
        """Atualiza o campo de texto quando o slider muda"""
        self.feed_rate.setText(str(value))
    
    def update_feed_slider(self):
        """Atualiza o slider quando o campo de texto muda"""
        try:
            value = int(self.feed_rate.text())
            # Limitar ao intervalo do slider
            value = max(100, min(5000, value))
            self.feed_slider.setValue(value)
        except ValueError:
            pass
    
    def toggle_fast_mode(self):
        """Ativa/desativa o modo rápido (desabilita verificação de porta)"""
        if not self.is_connected or not self.grbl:
            return
            
        try:
            if self.fast_mode_check.isChecked():
                # Desativar verificação de porta para movimentos mais rápidos
                self.grbl.send_immediately("$10=0")
                self.statusBar.showMessage("Modo rápido ativado (verificação de porta desativada)")
            else:
                # Reativar verificação de porta
                self.grbl.send_immediately("$10=1")
                self.statusBar.showMessage("Modo rápido desativado (verificação de porta ativada)")
        except Exception as e:
            logger.error(f"Erro ao alternar modo rápido: {str(e)}", exc_info=True)
            self.statusBar.showMessage(f"Erro: {str(e)}")
    
    def set_motion_mode(self, mode):
        """Define o modo de movimento (absoluto/passo a passo ou relativo/contínuo)"""
        if not self.is_connected or not self.grbl:
            return
            
        if mode == "G90":
            self.mode_absolute.setChecked(True)
            self.mode_relative.setChecked(False)
            self.mode_absolute.setText("Passo a Passo (G90)")
            self.mode_relative.setText("Contínuo (G91)")
        else:
            self.mode_absolute.setChecked(False)
            self.mode_relative.setChecked(True)
            self.mode_absolute.setText("Passo a Passo (G90)")
            self.mode_relative.setText("Contínuo (G91)")
            
        # Atualiza o modo atual
        self.current_motion_mode = mode
            
        # Envia o comando para a máquina
        self.grbl.send_immediately(mode)
        self.last_command = mode
        self.last_command_label.setText(mode)
        
        # Atualiza a mensagem de status com o novo modo
        self.statusBar.showMessage(f"Modo de movimento alterado para {mode}")
    
    def start_jog(self, axis, direction):
        """Inicia movimento jog para um eixo (movimento discreto)"""
        if not self.is_connected or not self.grbl:
            return
            
        try:
            logger.debug(f"Iniciando jog discreto: eixo={axis}, direção={direction}")
            
            # Determina a distância de movimento
            if axis == "X":
                distance = float(self.x_distance.text()) * direction
                command = f"G91\nG0 X{distance} F{self.feed_rate.text()}"
            else:  # Y
                distance = float(self.y_distance.text()) * direction
                command = f"G91\nG0 Y{distance} F{self.feed_rate.text()}"
                
            # Envia o comando
            self.grbl.send_gcode(command)
            self.last_command = command
            self.last_command_label.setText(command)
            
        except Exception as e:
            logger.error(f"Erro ao iniciar jog: {str(e)}", exc_info=True)
            self.statusBar.showMessage(f"Erro ao iniciar movimento: {str(e)}")
    
    def stop_jog(self):
        """Para o movimento jog quando o botão é liberado"""
        # Para movimento discreto, não precisamos fazer nada especial
        pass

    def _continue_jog_movement(self, axis, direction, distance, feed_rate):
        """Continua o movimento jog enviando comandos incrementais pequenos"""
        if not self.is_connected or not self.grbl or not self.jogging:
            if hasattr(self, 'jog_timer') and self.jog_timer.isActive():
                self.jog_timer.stop()
            return
            
        # Cria o comando para continuar o movimento
        if axis.upper() == 'X':
            jog_command = f"G00 X{distance} F{feed_rate}"
        else:  # Y
            jog_command = f"G00 Y{distance} F{feed_rate}"
            
        # Envia o comando usando o método disponível
        try:
            self.grbl.send_immediately(jog_command)
        except Exception as e:
            logger.error(f"Erro ao continuar jog: {str(e)}", exc_info=True)
            if hasattr(self, 'jog_timer') and self.jog_timer.isActive():
                self.jog_timer.stop()

    def _continue_jog(self):
        """Envia comandos contínuos de movimento enquanto o botão está pressionado"""
        if not self.is_connected or not self.grbl:
            return
            
        try:
            # Cria um novo comando usando G1 (movimento linear) em vez de G0
            # G1 é mais suave para movimentos contínuos
            if self.jog_axis.upper() == 'X':
                command = f"G1 X{self.jog_direction * self.jog_step_size} F{self.jog_feed_rate}"
            else:  # Y
                command = f"G1 Y{self.jog_direction * self.jog_step_size} F{self.jog_feed_rate}"
                
            # Envia o comando sem interromper fluxos anteriores
            self.grbl.send_immediately(command)
                
        except Exception as e:
            logger.error(f"Erro ao continuar jog: {str(e)}", exc_info=True)
            self.jog_timer.stop()
    
    def start_continuous_jog(self, axis, direction):
        """
        Inicia movimento passo a passo (G90) ou contínuo (G91), dependendo do modo atual.
        """
        if not self.is_connected or not self.grbl:
            return
        
        # Para qualquer jog anterior antes de iniciar o novo
        self.stop_continuous_jog()
        time.sleep(0.05)  # Pequena pausa para garantir que o GRBL processe o comando de parada
        
        try:
            # Obtém o modo atual (G90 = Absoluto, G91 = Relativo)
            is_absolute_mode = (self.current_motion_mode == "G90")
            
            logger.debug(f"Iniciando jog: eixo={axis}, direção={direction}, modo={'G90 (Absoluto/Passo a Passo)' if is_absolute_mode else 'G91 (Relativo/Contínuo)'}")
            
            # Obtém a velocidade e o tamanho do passo
            try:
                feed_rate = int(self.feed_rate.text())
                feed_rate = max(100, min(feed_rate, 5000))  # Limita a velocidade para segurança
            except ValueError:
                feed_rate = 500  # Valor seguro padrão
            
            try:
                step_size = float(self.jog_step.text())
                step_size = max(0.1, min(step_size, 10))  # Limita o tamanho do passo entre 0.1 e 10mm
            except ValueError:
                step_size = 1.0  # Valor padrão seguro
                
            # Movimento com base no modo atual
            if is_absolute_mode:
                # G90 MODO ABSOLUTO/PASSO A PASSO: Movimento incremental relativo à posição atual
                # CORREÇÃO: Primeiro garantimos que estamos em modo relativo para o movimento
                self.grbl.send_immediately("G91")
                
                # Calcula a distância de movimento baseada no passo configurado
                distance = step_size * direction
                
                # Cria um comando de movimento incremental apesar de estar em modo G90 na interface
                if axis.upper() == 'X':
                    jog_command = f"G0 X{distance} F{feed_rate}"
                else:  # Y
                    jog_command = f"G0 Y{distance} F{feed_rate}"
                    
                # Envia o comando de movimento incremental
                self.grbl.send_immediately(jog_command)
                self.last_command = jog_command
                self.last_command_label.setText(jog_command)
                
                # Restaura o modo absoluto ao final do movimento
                QTimer.singleShot(100, lambda: self.grbl.send_immediately("G90"))
                
                # Não define estado de jogging, pois é uma operação única
                self.jogging = False
                
            else:
                # G91 MODO RELATIVO/CONTÍNUO: Movimento contínuo enquanto o botão é pressionado
                # Usar o comando $J= para jog contínuo
                distance_continuous = 50 * direction  # Distância grande o suficiente para movimento contínuo
                
                if axis.upper() == 'X':
                    jog_command = f"$J=G91 X{distance_continuous} F{feed_rate}"
                else:  # Y
                    jog_command = f"$J=G91 Y{distance_continuous} F{feed_rate}"
                    
                # Imediatamente envia o comando de jog
                self.grbl.send_immediately(jog_command)
                self.last_command = jog_command
                self.last_command_label.setText(jog_command)
                
                # Define flags de controle apenas para modo contínuo
                self.jogging = True
                self.current_jog_axis = axis
                self.current_jog_direction = direction
                        
        except Exception as e:
            logger.error(f"Erro ao iniciar jog: {str(e)}", exc_info=True)
            self.statusBar.showMessage(f"Erro ao iniciar movimento: {str(e)}")

    def stop_continuous_jog(self):
        """
        Para o movimento jog contínuo quando o botão é liberado.
        No modo G90, esta função não faz nada pois o movimento é único.
        """
        if not self.is_connected or not self.grbl or not self.jogging:
            return
            
        logger.debug("Parando jog contínuo")
        
        try:
            # Comando de feed hold para parar imediatamente
            self.grbl.send_immediately("!")
            
            # Imediatamente após, envia comando de ciclo contínuo para liberar o hold
            QTimer.singleShot(50, lambda: self.grbl.send_immediately("~"))
            
            # Limpa o estado de jog
            self.jogging = False
            self.current_jog_axis = None
            self.current_jog_direction = None
            
        except Exception as e:
            logger.error(f"Erro ao parar jog contínuo: {str(e)}", exc_info=True)


    def _stop_jog_and_movements(self):
        """Para todos os movimentos ativos"""
        if hasattr(self, 'jog_timer') and self.jog_timer.isActive():
            self.jog_timer.stop()
            
        if not self.is_connected or not self.grbl:
            return
            
        try:
            # Envia comando de parada
            self.grbl.send_immediately("!")
        except Exception as e:
            logger.error(f"Erro ao parar movimentos: {str(e)}", exc_info=True)

    def _send_resume_after_stop(self):
        """Envia comando de retomada após parada"""
        if not self.is_connected or not self.grbl:
            return
            
        try:
            # Enviar comando de retomada usando o método correto
            self.grbl.send_realtime("~")
            
        except Exception as e:
            logger.error(f"Erro ao enviar comando de retomada: {str(e)}", exc_info=True)
    
    def home(self):
        """Envia comando para ir para home"""
        if not self.is_connected or not self.grbl:
            return
            
        try:
            # Usar send_immediately
            self.grbl.send_immediately("$H")
            self.last_command = "$H"
            self.last_command_label.setText("$H (Home)")
        except Exception as e:
            logger.error(f"Erro ao enviar comando home: {str(e)}", exc_info=True)

    def unlock(self):
        """Desbloqueia a máquina após um alarme"""
        if not self.is_connected or not self.grbl:
            return
            
        try:
            # Usar send_immediately
            self.grbl.send_immediately("$X")
            self.last_command = "$X"
            self.last_command_label.setText("$X (Unlock)")
        except Exception as e:
            logger.error(f"Erro ao enviar comando de desbloqueio: {str(e)}", exc_info=True)
    
    def set_zero(self):
        """Define a posição atual como zero para todos os eixos"""
        if not self.is_connected or not self.grbl:
            return
            
        try:
            # Usar send_immediately
            self.grbl.send_immediately("G92 X0 Y0")
            self.last_command = "G92 X0 Y0"
            self.last_command_label.setText("G92 X0 Y0 (Set Zero)")
        except Exception as e:
            logger.error(f"Erro ao definir posição zero: {str(e)}", exc_info=True)
    
    def emergency_stop(self):
        """Para todos os movimentos imediatamente e coloca a máquina em estado seguro"""
        if not self.is_connected or not self.grbl:
            return
        
        try:
            logger.debug("Executando parada de emergência")
            
            # Para qualquer timer ativo
            if hasattr(self, 'jog_timer') and self.jog_timer.isActive():
                self.jog_timer.stop()
            
            # Sequência robusta de parada
            # 1. Feed hold imediato (!)
            self.grbl.send_immediately("!")
            
            # 2. Soft reset para garantir parada completa
            QTimer.singleShot(100, lambda: self.grbl.send_immediately("\x18"))  # Ctrl+X
            
            # Reset completo de estado
            self.jogging = False
            self.current_jog_axis = None
            self.current_jog_direction = None
            
            self.last_command = "! (Parada de Emergência)"
            self.last_command_label.setText("! (Parada de Emergência)")
            self.statusBar.showMessage("PARADA DE EMERGÊNCIA acionada! Use o botão 'Reset Alarme' para continuar.")
            
            # Destaca o botão de reset para orientar o usuário
            self.reset_button.setStyleSheet("background-color: orange; color: white; font-weight: bold; font-size: 14px; border: 2px solid red;")
            
        except Exception as e:
            logger.error(f"Erro na parada de emergência: {str(e)}", exc_info=True)
            self.statusBar.showMessage(f"Erro: {str(e)}")
    
    def send_command(self):
        """Envia um comando G-code personalizado"""
        if not self.is_connected or not self.grbl:
            return
            
        command = self.command_input.text()
        if not command:
            return
            
        try:
            # Usar send_immediately em vez de send_gcode
            self.grbl.send_immediately(command)
            self.last_command = command
            self.last_command_label.setText(command)
            self.command_input.clear()
        except Exception as e:
            logger.error(f"Erro ao enviar comando: {str(e)}", exc_info=True)
            self.statusBar.showMessage(f"Erro ao enviar comando: {str(e)}")
    
    def on_response_received(self, response):
        """Manipula a resposta recebida"""
        self.last_response_label.setText(response)
        self.comm_log.setText(response)
    
    def on_status_update(self, position):
        """Atualiza a exibição de posição na interface"""
        # Esta função é chamada pelo sinal emitido no _on_status_update
        self.position_display.update_position(position)
    
    def on_error_message(self, error):
        """Exibe mensagem de erro na barra de status"""
        self.statusBar.showMessage(error)
    
    def closeEvent(self, event):
        """Manipula o evento de fechamento da janela"""
        # Para todos os movimentos e desconecta
        if self.is_connected and self.grbl:
            self._stop_jog_and_movements()
            try:
                self.grbl.close()
            except Exception:
                pass
                
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GRBLController()
    window.show()
    sys.exit(app.exec())