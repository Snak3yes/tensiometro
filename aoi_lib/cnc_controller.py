import time
import serial
import serial.tools.list_ports
import threading
from grbl_streamer import GrblStreamer  # Importa a biblioteca grbl-streamer

import logging
# Se ainda não existir, defina um logger para esta classe:
logger = logging.getLogger("GRBLCNCController")
logger.setLevel(logging.DEBUG)

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
    Implementada usando a biblioteca grbl-streamer.
    """
    
    def __init__(self):
        """Inicializa o controlador CNC."""
        self.grbl = None
        self.lock = threading.Lock()
        self.is_connected = False
        self.current_position = {'x': 0, 'y': 0, 'z': 0}
        self.machine_status = "Disconnected"
        self.last_response = ""
        self.last_error = ""
        
        # Eventos para comunicação assíncrona
        self.response_received = EventEmitter()
        self.status_update = EventEmitter()
        self.position_update = EventEmitter()
        self.error_message = EventEmitter()
        
        # Thread para consulta periódica de status
        self.status_thread = None
        self.running = False
        
        # Controle de jog contínuo
        self.jogging = False
        self.current_jog_command = None
        self.steps_to_mm_factor = 1.0
        
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
                    self.last_error = "Nenhuma porta serial encontrada"
                    return False
                port = ports[0]
                
            # Inicializa e configura o GrblStreamer
            self.grbl = GrblStreamer(port=port, baud=baudrate)
            
            # Configura callbacks para eventos do GrblStreamer
            self._setup_callbacks()
            
            # Desbloqueia a máquina
            self.send_command("$X", priority=True)
            
            # Inicia thread de consulta de status
            self.running = True
            self.status_thread = threading.Thread(target=self._status_polling_thread, daemon=True)
            self.status_thread.start()
            
            self.is_connected = True
            self.machine_status = "Idle"  # Estado inicial presumido
            return True
            
        except Exception as e:
            self.last_error = str(e)
            return False
    
    def _setup_callbacks(self):
        """
        Configura callbacks para eventos do GrblStreamer.
        Esta função deve ser adaptada com base na API real da biblioteca.
        """
        # Configuração para receber atualizações de status da máquina
        self.grbl.register_status_callback(self._on_status_update)
        
        # Configuração para receber respostas de comandos
        self.grbl.register_response_callback(self._on_response_received)
        
        # Configuração para receber notificações de erro
        self.grbl.register_error_callback(self._on_error_message)
            
    def _status_polling_thread(self):
        """Thread para consulta periódica de status."""
        while self.running and self.is_connected:
            try:
                # Requisição de status ao GRBL a cada 200ms
                if self.grbl:
                    self.grbl.get_status()
                time.sleep(0.2)
            except Exception:
                time.sleep(0.5)  # Maior intervalo em caso de erro
                
    def disconnect(self):
        """Desconecta da máquina CNC."""
        # Garante que o jog é parado antes de desconectar
        if self.jogging:
            self.stop_continuous_jog()
            
        self.running = False
        if self.status_thread:
            self.status_thread.join(1.0)  # Espera até 1 segundo pela thread
            
        if self.grbl:
            try:
                self.grbl.close()
                self.grbl = None
            except Exception as e:
                self.last_error = str(e)
                
        self.is_connected = False
        self.machine_status = "Disconnected"
        
    def is_moving(self):
        """Verifica se a máquina está em movimento."""
        return self.machine_status == "Run" or self.machine_status == "Jog"
        
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
        """
        Retorna a posição atual do CNC.
        Certifica-se de retornar uma cópia do dicionário para evitar alteração acidental.
        """
        logger.debug(f"get_current_position: Retornando posição atual: {self.current_position if hasattr(self, 'current_position') else 'desconhecida'}")
        if hasattr(self, 'current_position'):
            # current_position é um dicionário com chaves 'x', 'y' e 'z'
            # Retorna uma cópia para evitar alterações acidentais
            return self.current_position.copy()
        return {'x': 0, 'y': 0, 'z': 0}
        
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
        self.send_command("G90", priority=True)
        
        # Constrói o comando
        command = "G1"
        if x is not None:
            command += f" X{x}"
        if y is not None:
            command += f" Y{y}"
        command += f" F{feed_rate}"
        
        # Envia o comando
        self.send_command(command)
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
        self.send_command("G91", priority=True)
        
        # Constrói o comando
        command = f"G1 X{x} Y{y} F{feed_rate}"
        
        # Envia o comando
        self.send_command(command)
        return True

    def start_continuous_jog(self, axis, direction, feed_rate=1000):
        """
        Inicia um movimento jog contínuo em um eixo específico.
        O movimento continua até que stop_continuous_jog seja chamado.
        
        Args:
            axis: Eixo a mover ('X' ou 'Y')
            direction: Direção do movimento (1 ou -1)
            feed_rate: Velocidade em mm/min
            
        Returns:
            bool: True se o comando foi iniciado com sucesso
        """
        if not self.is_connected or self.jogging:
            return False
            
        # Para qualquer movimento anterior e garante modo relativo
        self.emergency_stop()
        time.sleep(0.1)  # Pequena pausa para garantir que o GRBL processou o comando de parada
        self.send_command("~", priority=True)  # Retoma após parada
        self.send_command("G91", priority=True)  # Modo relativo
        
        # Em GRBL 1.1, podemos usar o comando de jog para movimento contínuo
        # A sintaxe é: $J=G91 X[dist] Y[dist] F[feed]
        distance = 1000 * direction  # Distância grande para simular movimento contínuo
        
        if axis.upper() == 'X':
            jog_command = f"$J=G91 X{distance} F{feed_rate}"
        else:  # assume Y
            jog_command = f"$J=G91 Y{distance} F{feed_rate}"
            
        self.jogging = True
        self.current_jog_command = jog_command
        
        # Envia comando de jog com máxima prioridade
        success = self.send_command(jog_command, priority=True)
        
        return success
        
    def stop_continuous_jog(self):
        """
        Para o movimento jog contínuo atual.
        
        Returns:
            bool: True se o comando foi enviado com sucesso
        """
        if not self.is_connected or not self.jogging:
            return False
            
        # Cancela o jog enviando Feed Hold (!).
        # NÃO enviamos '~' para não reiniciar o jog.
        success = self.send_command("!", priority=True)

        # Atualiza o estado interno: jog deve estar parado
        self.jogging = False
        self.current_jog_command = None
        return success
        
    def home(self):
        """Envia a máquina para a posição home."""
        if not self.is_connected:
            return False
            
        self.send_command("$H")
        return True
        
    def set_zero(self):
        """Define a posição atual como zero."""
        if not self.is_connected:
            return False
            
        self.send_command("G92 X0 Y0")
        return True
        
    def unlock(self):
        """Envia o comando de desbloqueio ($X) para o GRBL."""
        if not self.is_connected or not self.grbl:
            logger.warning("UNLOCK: CNC não conectada.")
            return False
        try:
            logger.info("UNLOCK: Enviando comando de desbloqueio ($X)")
            
            # A biblioteca tem um método dedicado para killalarm
            self.grbl.killalarm()
            
            logger.info("UNLOCK: Comando de desbloqueio enviado.")
            return True
        except Exception as e:
            logger.error(f"UNLOCK: Erro ao enviar comando de desbloqueio: {e}", exc_info=True)
            return False
        
    def emergency_stop(self):
        """Para todos os movimentos imediatamente (Feed Hold)."""
        if not self.is_connected or not self.grbl:
            logger.warning("EMERGENCY STOP: CNC não conectada.")
            return False
        try:
            logger.info("EMERGENCY STOP: Enviando comando Feed Hold (!)")

            # CORREÇÃO: Usar send_immediately() em vez de send_realtime_command()
            self.grbl.send_immediately("!")            

            self.jogging = False  # Atualiza o estado de jog, pois o movimento parou
            self.machine_status = "Hold" # Estado esperado após '!' é Hold
            logger.info("EMERGENCY STOP: Comando Feed Hold (!) enviado. Estado esperado: Hold.")
            return True
        except Exception as e:
            logger.error(f"EMERGENCY STOP: Erro ao enviar comando Feed Hold (!): {e}", exc_info=True)
            return False
    
    def send_soft_reset(self):
        """Envia um comando de Soft Reset (Ctrl+X) para o GRBL."""
        if not self.is_connected or not self.grbl:
            logger.warning("SOFT RESET: CNC não conectada.")
            return False
        try:
            # O Soft Reset no GRBL é o caractere Ctrl+X (código ASCII 0x18 ou 24 em decimal)
            logger.info("SOFT RESET: Enviando comando Soft Reset (Ctrl+X)")
            
            # Utiliza o método send_immediately() com o caractere adequado
            self.grbl.send_immediately("\x18")
            
            self.jogging = False # Assume que o reset também para o jog
            self.machine_status = "Alarm" # O estado esperado após reset é Alarme
            logger.info("SOFT RESET: Comando enviado. Estado esperado: Alarm.")
            return True
        except Exception as e:
            # Loga o erro se ocorrer
            logger.error(f"SOFT RESET: Erro ao enviar comando Soft Reset: {e}", exc_info=True)
            return False

        
    def send_command(self, command, priority=False):
        """
        Envia um comando personalizado ao GRBL.
        
        Args:
            command: Comando G-code
            priority: True para enviar com prioridade
        """
        if not self.is_connected or not self.grbl:
            return False
            
        try:
            # Comandos de controle realtime (!, ~, ?) são tratados especialmente
            if command in ["!", "~", "?"]:
                self.grbl.send_immediately(command)
            # Comandos prioritários são enviados com prioridade
            elif priority:
                self.grbl.send_immediately(command)
            return True
        except Exception as e:
            self.last_error = str(e)
            self.error_message.emit(str(e))
            return False
            
    def _on_response_received(self, response):
        """Callback quando uma resposta é recebida."""
        self.last_response = response
        self.response_received.emit(response)
        
    def _on_status_update(self, status_data):
        """Callback quando o status da máquina é atualizado."""
        logger.debug(">> _on_status_update chamado com status_data: %s", status_data)
        
        # Extrai o estado da máquina
        state = status_data.get('state', 'Unknown')
        self.machine_status = state
        logger.debug("Estado da máquina extraído: %s", state)
        
        # Extrai a posição (espera-se um dicionário com chaves 'x', 'y' e 'z')
        position = status_data.get('position', None)
        if position:
            new_position = {
                'x': position.get('x', 0),
                'y': position.get('y', 0),
                'z': position.get('z', 0)
            }
            logger.debug("Posição extraída: %s", new_position)
            if new_position['x'] == 0 and new_position['y'] == 0:
                logger.warning("As coordenadas X e Y continuam 0 mesmo após movimento. status_data recebido: %s", status_data)
            self.current_position = new_position
            self.position_update.emit(self.current_position)
        else:
            logger.warning("status_data não contém a chave 'position': %s", status_data)
        
        status_string = f"<{state}|MPos:{self.current_position['x']:.3f},{self.current_position['y']:.3f},{self.current_position['z']:.3f}>"
        logger.debug("String de status formada: %s", status_string)
        self.status_update.emit(status_string)
        
    def _on_error_message(self, error):
        """Callback quando ocorre um erro."""
        self.last_error = error
        self.error_message.emit(error)