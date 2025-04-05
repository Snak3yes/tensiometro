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
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon

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
                
                # Emite atualização apenas se a posição mudou significativamente (> 0.001mm)
                if (abs(position['x'] - self.last_position['x']) > 0.001 or
                    abs(position['y'] - self.last_position['y']) > 0.001 or
                    abs(position['z'] - self.last_position['z']) > 0.001):
                    
                    self.position_update.emit(position)
                    self.last_position = position
        
        except Exception as e:
            logger.error(f"Erro ao analisar status: {e}", exc_info=True)

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
        
        # Configuração para repetição automática - ajustada para ser mais lenta e estável
        self.setAutoRepeat(True)
        self.setAutoRepeatDelay(500)   # Aumentado para 500ms - espera mais antes de começar a repetir
        self.setAutoRepeatInterval(150)  # Aumentado para 150ms - repete mais lentamente

class JogButton(QPushButton):
    """Botão personalizado para movimentos jog"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setAutoRepeat(True)
        self.setAutoRepeatDelay(500)    # Aumentado para 500ms
        self.setAutoRepeatInterval(150)  # Aumentado para 150ms
        
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
        self.setGeometry(100, 100, 1000, 700)  # Janela maior para acomodar os controles adicionais
        
        # Criar thread de comunicação
        self.comm_thread = GRBLCommunicationThread()

        self.jog_controller = JogController(self.comm_thread)
        
        # Conectar os sinais da thread
        self.comm_thread.response_received.connect(self.on_response_received)
        self.comm_thread.status_update.connect(self.on_status_update)
        self.comm_thread.position_update.connect(self.on_position_update)
        self.comm_thread.error_message.connect(self.on_error_message)
        
        # Iniciar a thread
        self.comm_thread.start()
        
        # Configuração da interface
        self.init_ui()
        
        # Estado da máquina
        self.machine_status = "Desconectado"
        
        # Flag para indicar se estamos em modo de jog
        self.jog_mode_active = False
        
        # Timer para atualizar o status da interface
        self.ui_timer = QTimer(self)
        self.ui_timer.timeout.connect(self.update_ui_state)
        self.ui_timer.start(300)  # Atualiza a cada 300ms (mais frequente)
        
        # Configura a máquina em modo relativo no início
        # Isso ajuda a evitar mudanças de modo durante operações de jog
        self.current_motion_mode = "G91"
        
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
        
        self.x_distance = QLineEdit("1")  # Distância reduzida para movimentos mais precisos
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
        
        self.y_distance = QLineEdit("1")  # Distância reduzida para movimentos mais precisos
        self.y_distance.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        y_control_layout.addWidget(self.y_minus_button)
        y_control_layout.addWidget(self.y_distance)
        y_control_layout.addWidget(self.y_plus_button)
        
        axis_layout.addLayout(y_control_layout, 1, 1)
        
        # NOVO: Controle direcional em formato de teclado numérico (8, 4, 6, 2)
        directional_group = QGroupBox("Controle Direcional")
        directional_layout = QGridLayout()
        
        self.dir_up_button = DirectionalButton("up")  # 8 no numpad (Y+)
        self.dir_left_button = DirectionalButton("left")  # 4 no numpad (X-)
        self.dir_right_button = DirectionalButton("right")  # 6 no numpad (X+)
        self.dir_down_button = DirectionalButton("down")  # 2 no numpad (Y-)
        
        # Conectar eventos de pressionar/soltar para movimentos imediatos
        self.dir_up_button.pressed.connect(lambda: self.start_jog("Y", 1, priority=True))
        self.dir_up_button.released.connect(self.stop_jog)
        
        self.dir_down_button.pressed.connect(lambda: self.start_jog("Y", -1, priority=True))
        self.dir_down_button.released.connect(self.stop_jog)
        
        self.dir_left_button.pressed.connect(lambda: self.start_jog("X", -1, priority=True))
        self.dir_left_button.released.connect(self.stop_jog)
        
        self.dir_right_button.pressed.connect(lambda: self.start_jog("X", 1, priority=True))
        self.dir_right_button.released.connect(self.stop_jog)
        
        # Organização em grade para parecer com teclado numérico
        directional_layout.addWidget(self.dir_up_button, 0, 1)  # Cima (8)
        directional_layout.addWidget(self.dir_left_button, 1, 0)  # Esquerda (4)
        directional_layout.addWidget(self.dir_right_button, 1, 2)  # Direita (6)
        directional_layout.addWidget(self.dir_down_button, 2, 1)  # Baixo (2)
        
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
        self.feed_rate = QLineEdit("1000")  # Valor maior para movimentos mais rápidos
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
        self.mode_absolute = QPushButton("Absoluto (G90)")
        self.mode_absolute.setCheckable(True)
        self.mode_absolute.clicked.connect(lambda: self.set_motion_mode("G90"))
        
        self.mode_relative = QPushButton("Relativo (G91)")
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
        
        self.stop_button = QPushButton("PARAR (!")
        self.stop_button.setStyleSheet("background-color: red; color: white; font-weight: bold;")
        self.stop_button.clicked.connect(self.emergency_stop)
        
        control_buttons_layout.addWidget(self.home_button, 0, 0)
        control_buttons_layout.addWidget(self.unlock_button, 0, 1)
        control_buttons_layout.addWidget(self.zero_button, 1, 0)
        control_buttons_layout.addWidget(self.stop_button, 1, 1)
        
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
        control_status_layout.setStretch(0, 3)  # Controle
        control_status_layout.setStretch(1, 2)  # Status
        
        main_layout.addLayout(control_status_layout)
        
        # Barra de status
        self.statusBar = self.statusBar()
        self.statusBar.showMessage("Pronto para conexão")
        
        # Desabilitar controles até que a conexão seja estabelecida
        self.toggle_controls(False)
        
        # Atualizar portas
        self.refresh_ports()

    def _resume_after_stop(self):
        """Método auxiliar para enviar comando de retomada após parada"""
        try:
            # Verifica se a máquina está em estado Hold e envia comando para retomar
            if "Hold" in self.comm_thread.machine_state:
                logger.debug("Enviando comando de retomada após parada")
                self.comm_thread.send_command("~", priority=True)
                
            # Solicita status para atualizar interface
            self.comm_thread.send_command("?", priority=True)
        except Exception as e:
            logger.error(f"Erro ao retomar após parada: {e}", exc_info=True)
        
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
        if not self.comm_thread.is_connected:
            try:
                port = self.port_combo.currentText()
                if not port:
                    self.statusBar.showMessage("Nenhuma porta selecionada")
                    return
                
                # Mensagem de status
                self.statusBar.showMessage(f"Conectando à porta {port}...")
                
                # Configuração de porta similar ao consumo_lib.py
                serial_port = serial.Serial(port, 115200, timeout=0.5)
                time.sleep(0.5)  # Aguarda a inicialização básica
                
                # Inicializar GRBL - similar ao consumo_lib.py
                logger.info("Enviando comando de inicialização")
                serial_port.write(b"\r\n\r\n")
                time.sleep(0.5)
                
                # Limpar buffer
                logger.info("Limpando buffer de entrada")
                serial_port.flushInput()  # Usa flushInput como em consumo_lib
                
                # Configurar a thread
                logger.info("Configurando thread de comunicação")
                self.comm_thread.set_serial_port(serial_port)
                
                # Enviar comandos de configuração
                logger.info("Enviando comando de desbloqueio")
                self.comm_thread.send_command("$X", priority=True)
                time.sleep(0.1)  # Pequeno delay para processamento do comando
                
                # Iniciar em modo relativo para jog
                logger.info("Configurando modo relativo")
                self.comm_thread.send_command("G91", priority=True)
                self.mode_relative.setChecked(True)
                self.mode_absolute.setChecked(False)
                
                # Confirmar conexão bem-sucedida
                logger.info("Conexão estabelecida com sucesso")
                self.connect_button.setText("Desconectar")
                self.machine_state_label.setText("Conectado")
                self.statusBar.showMessage(f"Conectado ao GRBL na porta {port}")
                self.toggle_controls(True)
                
            except Exception as e:
                logger.error(f"Erro ao conectar: {str(e)}", exc_info=True)
                self.statusBar.showMessage(f"Erro: {str(e)}")
        else:
            # Desconectar
            logger.info("Desconectando")
            self.comm_thread.disconnect()
            
            self.connect_button.setText("Conectar")
            self.machine_state_label.setText("Desconectado")
            self.statusBar.showMessage("Desconectado")
            self.toggle_controls(False)
    
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
        # Colorir o status da máquina
        if self.machine_status == "Idle":
            self.machine_state_label.setStyleSheet("color: green;")
        elif self.machine_status == "Run":
            self.machine_state_label.setStyleSheet("color: blue;")
        elif self.machine_status == "Alarm":
            self.machine_state_label.setStyleSheet("color: red;")
        elif self.machine_status == "Hold":
            self.machine_state_label.setStyleSheet("color: orange;")
        else:
            self.machine_state_label.setStyleSheet("")
            
    def toggle_fast_mode(self):
        """Ativa/desativa o modo rápido (desabilita verificação de porta)"""
        if self.fast_mode_check.isChecked():
            # Desativar verificação de porta para movimentos mais rápidos
            self.comm_thread.send_command("$10=0", priority=True)
            self.statusBar.showMessage("Modo rápido ativado (verificação de porta desativada)")
        else:
            # Reativar verificação de porta
            self.comm_thread.send_command("$10=1", priority=True)
            self.statusBar.showMessage("Modo rápido desativado (verificação de porta ativada)")
            
    def set_motion_mode(self, mode):
        """Define o modo de movimento (absoluto ou relativo)"""
        if mode == "G90":
            self.mode_absolute.setChecked(True)
            self.mode_relative.setChecked(False)
        else:
            self.mode_absolute.setChecked(False)
            self.mode_relative.setChecked(True)
            
        # Atualiza o modo atual
        self.current_motion_mode = mode
            
        # Enviar comando para a máquina
        self.comm_thread.send_command(mode)
        self.last_command_label.setText(mode)
        
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
        
    def start_jog(self, axis, direction, priority=False):
        """Inicia movimento jog para um eixo"""
        try:
            logger.debug(f"Iniciando jog: eixo={axis}, direção={direction}")
            
            # Delega o jogging para o controlador dedicado
            self.jog_controller.start_jog(axis, direction)
            
        except Exception as e:
            logger.error(f"Erro ao iniciar movimento: {e}", exc_info=True)
            self.statusBar.showMessage(f"Erro ao iniciar movimento: {str(e)}")
        
    def _continue_jog(self, axis, direction, priority):
        """Continua o processo de jog após verificações iniciais"""
        try:
            # Determina a distância de movimento
            if axis == "X":
                distance = float(self.x_distance.text())
            elif axis == "Y":
                distance = float(self.y_distance.text())
            else:
                # Para outros casos, usa o jog_step
                distance = float(self.jog_step.text())
                
            # Aplica direção
            if direction < 0:
                distance = -distance
                
            # Obtém a velocidade
            feed_rate = float(self.feed_rate.text())
            
            logger.debug(f"Parâmetros de jog: distância={distance}, velocidade={feed_rate}")
            
            # Garante que estamos em modo relativo para jog - sem bloquear a UI
            if self.current_motion_mode != "G91":
                logger.debug("Mudando para modo relativo (G91)")
                self.comm_thread.send_command("G91", priority=True)
                self.current_motion_mode = "G91"
                self.mode_relative.setChecked(True)
                self.mode_absolute.setChecked(False)
            
            # Monta o comando G-code
            g_command = "G0" if priority else "G1"
            
            if axis == "X":
                gcode = f"{g_command} X{distance} F{feed_rate}"
            else:
                gcode = f"{g_command} Y{distance} F{feed_rate}"
                
            logger.info(f"Enviando comando jog: {gcode}")
            
            # Envia o comando
            self.comm_thread.send_command(gcode, priority=priority)
            self.last_command_label.setText(gcode)
        except Exception as e:
            logger.error(f"Erro ao continuar movimento: {e}", exc_info=True)
            self.statusBar.showMessage(f"Erro ao continuar movimento: {str(e)}")
            
    def stop_jog(self):
        """Para o movimento jog quando o botão é liberado"""
        try:
            logger.debug("Parando movimento jog")
            
            # Delega para o controlador
            self.jog_controller.stop_jog()
            
        except Exception as e:
            logger.error(f"Erro ao parar movimento: {e}", exc_info=True)
            self.statusBar.showMessage(f"Erro ao parar movimento: {str(e)}")
        
    def home(self):
        """Envia comando para ir para home"""
        self.comm_thread.send_command("$H")
        self.last_command_label.setText("$H (Home)")
        
    def unlock(self):
        """Desbloqueia a máquina após um alarme"""
        self.comm_thread.send_command("$X", priority=True)
        self.last_command_label.setText("$X (Unlock)")
        
    def set_zero(self):
        """Define a posição atual como zero para todos os eixos"""
        self.comm_thread.send_command("G92 X0 Y0")
        self.last_command_label.setText("G92 X0 Y0 (Set Zero)")
        
    def emergency_stop(self):
        """Para todos os movimentos imediatamente"""
        self.comm_thread.send_command("!", priority=True)
        self.statusBar.showMessage("PARADA DE EMERGÊNCIA acionada!")
        self.last_command_label.setText("! (Parada de Emergência)")
        
    def send_command(self):
        """Envia um comando G-code personalizado"""
        command = self.command_input.text()
        if command:
            self.comm_thread.send_command(command)
            self.last_command_label.setText(command)
            self.command_input.clear()
            
    def on_response_received(self, response):
        """Manipula a resposta recebida da thread de comunicação"""
        self.last_response_label.setText(response)
        self.comm_log.setText(response)
        
    def on_status_update(self, status):
        """Atualiza o status da máquina na interface"""
        # Extrai o estado da máquina (ex: <Idle|...> => "Idle")
        if status.startswith('<') and '|' in status:
            state = status[1:status.find('|')]
            self.machine_status = state
            self.machine_state_label.setText(state)
        
    def on_position_update(self, position):
        """Atualiza a exibição de posição na interface"""
        self.position_display.update_position(position)
        
    def on_error_message(self, error):
        """Exibe mensagem de erro na barra de status"""
        self.statusBar.showMessage(error)
        
    def closeEvent(self, event):
        """Manipula o evento de fechamento da janela"""
        self.comm_thread.running = False  # Sinaliza que a thread deve terminar
        self.comm_thread.wait(1000)       # Espera até 1 segundo pela thread
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GRBLController()
    window.show()
    sys.exit(app.exec())