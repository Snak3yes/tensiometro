import time
import serial
import serial.tools.list_ports
from threading import Thread
from queue import Queue, PriorityQueue
import threading

class GRBLCommunicationThread(Thread):
    """
    Thread para comunicação com o controlador GRBL.
    """
    
    def __init__(self):
        super().__init__()
        self.daemon = True
        self.serial_port = None
        self.running = False
        self.command_queue = PriorityQueue()
        self.lock = threading.Lock()
        
        # Eventos simulados
        self.response_received = EventEmitter()
        self.status_update = EventEmitter()
        self.position_update = EventEmitter()
        self.error_message = EventEmitter()
    
    def set_serial_port(self, serial_port):
        """Define a porta serial para comunicação."""
        self.serial_port = serial_port
        self.running = True
    
    def run(self):
        """Método principal da thread."""
        while True:
            if not self.running or not self.serial_port:
                time.sleep(0.1)
                continue
            
            # Processar comandos na fila
            try:
                if not self.command_queue.empty():
                    priority, command = self.command_queue.get(block=False)
                    with self.lock:
                        self.serial_port.write((command + "\n").encode())
                    self.command_queue.task_done()
                
                # Ler respostas
                if self.serial_port.in_waiting:
                    with self.lock:
                        response = self.serial_port.readline().decode().strip()
                    
                    if response:
                        self.response_received.emit(response)
                        
                        # Processar atualizações de status e posição
                        if response.startswith('<'):
                            self.status_update.emit(response)
                            self._parse_position(response)
                        elif response.startswith('error:'):
                            self.error_message.emit(response)
            except Exception as e:
                self.error_message.emit(str(e))
            
            time.sleep(0.01)
    
    def _parse_position(self, status_string):
        """Analisa a string de status para extrair a posição."""
        try:
            parts = status_string.split('|')
            for part in parts:
                if part.startswith('MPos:') or part.startswith('WPos:'):
                    coords = part.split(':')[1].split(',')
                    position = {'x': float(coords[0]), 'y': float(coords[1]), 'z': float(coords[2])}
                    self.position_update.emit(position)
                    break
        except Exception:
            pass
    
    def send_command(self, command, priority=False):
        """
        Envia um comando para a fila.
        
        Args:
            command: O comando GCODE
            priority: Se True, o comando tem prioridade
        """
        priority_level = 0 if priority else 1
        self.command_queue.put((priority_level, command))
    
    def disconnect(self):
        """Desconecta a thread."""
        self.running = False
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.serial_port = None


class EventEmitter:
    """
    Sistema de eventos para comunicação assíncrona.
    Permite registrar múltiplos callbacks para diferentes eventos.
    """
    def __init__(self):
        self.callbacks = {}
        self.default_callbacks = []
    
    def connect(self, callback, event_name=None):
        """
        Conecta um callback a um evento específico ou como callback padrão.
        
        Args:
            callback: Função a ser chamada quando o evento ocorrer
            event_name: Nome do evento (se None, será adicionado aos callbacks padrão)
        """
        if event_name is None:
            self.default_callbacks.append(callback)
        else:
            if event_name not in self.callbacks:
                self.callbacks[event_name] = []
            self.callbacks[event_name].append(callback)
        
        # Retorna uma função que pode ser usada para desconectar este callback
        return lambda: self.disconnect(callback, event_name)
    
    def disconnect(self, callback, event_name=None):
        """
        Desconecta um callback específico.
        
        Args:
            callback: Callback a ser removido
            event_name: Nome do evento do qual remover (se None, remove dos callbacks padrão)
        """
        if event_name is None:
            if callback in self.default_callbacks:
                self.default_callbacks.remove(callback)
        else:
            if event_name in self.callbacks and callback in self.callbacks[event_name]:
                self.callbacks[event_name].remove(callback)
    
    def disconnect_all(self, event_name=None):
        """
        Desconecta todos os callbacks de um evento específico ou todos os eventos.
        
        Args:
            event_name: Nome do evento para limpar (se None, limpa todos os eventos)
        """
        if event_name is None:
            self.callbacks.clear()
            self.default_callbacks.clear()
        else:
            if event_name in self.callbacks:
                self.callbacks[event_name].clear()
    
    def emit(self, *args, event_name=None, **kwargs):
        """
        Emite um evento, chamando todos os callbacks registrados.
        
        Args:
            *args: Argumentos posicionais para passar aos callbacks
            event_name: Nome do evento a ser emitido (se None, apenas callbacks padrão são chamados)
            **kwargs: Argumentos nomeados para passar aos callbacks
        """
        # Chama todos os callbacks padrão
        for callback in self.default_callbacks:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                print(f"Erro em callback para evento: {e}")
        
        # Se um nome de evento for especificado, chama esses callbacks também
        if event_name is not None and event_name in self.callbacks:
            for callback in self.callbacks[event_name]:
                try:
                    callback(*args, **kwargs)
                except Exception as e:
                    print(f"Erro em callback para evento '{event_name}': {e}")
    
    def has_listeners(self, event_name=None):
        """
        Verifica se há callbacks registrados para um evento específico ou para qualquer evento.
        
        Args:
            event_name: Nome do evento a verificar (se None, verifica todos)
            
        Returns:
            bool: True se houver callbacks registrados, False caso contrário
        """
        if event_name is None:
            return bool(self.default_callbacks) or any(bool(callbacks) for callbacks in self.callbacks.values())
        else:
            return event_name in self.callbacks and bool(self.callbacks[event_name])


class GRBLCNCController:
    """
    Classe para controlar uma máquina CNC usando GRBL.
    Adaptada do código existente para ser usada como biblioteca.
    """
    
    def __init__(self):
        """Inicializa o controlador CNC."""
        self.comm_thread = GRBLCommunicationThread()
        self.comm_thread.response_received.connect(self._on_response_received)
        self.comm_thread.status_update.connect(self._on_status_update)
        self.comm_thread.position_update.connect(self._on_position_update)
        self.comm_thread.error_message.connect(self._on_error_message)
        
        self.is_connected = False
        self.current_position = {'x': 0, 'y': 0, 'z': 0}
        self.machine_status = "Disconnected"
        self.last_response = ""
        self.last_error = ""
        
        # Inicia a thread de comunicação
        self.comm_thread.start()
        
    def connect(self, port=None, baudrate=115200):
        """
        Conecta à máquina CNC.
        
        Args:
            port: Porta serial (None para autodetecção)
            baudrate: Taxa de transmissão
            
        Returns:
            bool: True se conectado com sucesso
        """
        try:
            # Autodetectar porta se não especificada
            if port is None:
                ports = [p.device for p in serial.tools.list_ports.comports()]
                if not ports:
                    return False
                port = ports[0]
                
            serial_port = serial.Serial(port, baudrate, timeout=0.5)
            time.sleep(0.5)
            
            # Inicializar GRBL
            serial_port.write(b"\r\n\r\n")
            time.sleep(0.5)
            serial_port.flushInput()
            
            # Configurar thread
            self.comm_thread.set_serial_port(serial_port)
            
            # Desbloquear e configurar
            self.comm_thread.send_command("$X", priority=True)
            
            self.is_connected = True
            return True
            
        except Exception as e:
            self.last_error = str(e)
            return False
            
    def disconnect(self):
        """Desconecta da máquina CNC."""
        self.comm_thread.disconnect()
        self.is_connected = False
        
    def is_moving(self):
        """Verifica se a máquina está em movimento."""
        return self.machine_status == "Run"
        
    def wait_for_idle(self, timeout=30):
        """
        Aguarda até que a máquina esteja ociosa.
        
        Args:
            timeout: Tempo máximo de espera em segundos
            
        Returns:
            bool: True se ficou ocioso, False se atingiu timeout
        """
        start_time = time.time()
        while self.is_moving():
            if time.time() - start_time > timeout:
                return False
            time.sleep(0.1)
        return True
        
    def get_current_position(self):
        """Retorna a posição atual da máquina."""
        return self.current_position.copy()
        
    def move_to_absolute_position(self, x=None, y=None, feed_rate=1000):
        """
        Move para uma posição absoluta.
        
        Args:
            x, y: Coordenadas de destino (None para não mover esse eixo)
            feed_rate: Velocidade de avanço em mm/min
        """
        if not self.is_connected:
            return False
            
        # Muda para modo absoluto
        self.comm_thread.send_command("G90", priority=True)
        
        # Constrói o comando
        command = "G1"
        if x is not None:
            command += f" X{x}"
        if y is not None:
            command += f" Y{y}"
        command += f" F{feed_rate}"
        
        # Envia o comando
        self.comm_thread.send_command(command)
        return True
        
    def move_relative(self, x=0, y=0, feed_rate=1000):
        """
        Move em relação à posição atual.
        
        Args:
            x, y: Distância a mover em cada eixo
            feed_rate: Velocidade de avanço em mm/min
        """
        if not self.is_connected:
            return False
            
        # Muda para modo relativo
        self.comm_thread.send_command("G91", priority=True)
        
        # Constrói o comando
        command = f"G1 X{x} Y{y} F{feed_rate}"
        
        # Envia o comando
        self.comm_thread.send_command(command)
        return True
        
    def home(self):
        """Envia a máquina para a posição home."""
        if not self.is_connected:
            return False
            
        self.comm_thread.send_command("$H")
        return True
        
    def set_zero(self):
        """Define a posição atual como zero."""
        if not self.is_connected:
            return False
            
        self.comm_thread.send_command("G92 X0 Y0")
        return True
        
    def unlock(self):
        """Desbloqueia a máquina."""
        if not self.is_connected:
            return False
            
        self.comm_thread.send_command("$X", priority=True)
        return True
        
    def emergency_stop(self):
        """Para todos os movimentos imediatamente."""
        if not self.is_connected:
            return False
            
        self.comm_thread.send_command("!", priority=True)
        return True
        
    def send_command(self, command, priority=False):
        """
        Envia um comando personalizado ao GRBL.
        
        Args:
            command: Comando G-code
            priority: True para enviar com prioridade
        """
        if not self.is_connected:
            return False
            
        self.comm_thread.send_command(command, priority)
        return True
        
    def _on_response_received(self, response):
        """Callback quando uma resposta é recebida."""
        self.last_response = response
        
    def _on_status_update(self, status):
        """Callback quando o status é atualizado."""
        if status.startswith('<') and '|' in status:
            self.machine_status = status[1:status.find('|')]
        
    def _on_position_update(self, position):
        """Callback quando a posição é atualizada."""
        self.current_position = position
        
    def _on_error_message(self, error):
        """Callback quando ocorre um erro."""
        self.last_error = error