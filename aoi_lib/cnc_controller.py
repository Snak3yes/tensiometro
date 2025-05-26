import time
import serial
import serial.tools.list_ports
import threading
from grbl_streamer import GrblStreamer  # Importa a biblioteca grbl-streamer
from pathlib import Path
import json

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
        # se True, inverte lógica dos eixos Y / Z (para a visão do operador)
        self.invert_y = False
        self.invert_z = False
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

        # Limites máximos de feed  e  aceleração  (mm/min  | mm/s²)
        self.max_feed = {'x': 1000.0, 'y': 1000.0, 'z': 800.0}
        self.max_acc  = {'x':  50.0,  'y':  50.0,  'z': 30.0}

        # evita mostrar várias vezes o mesmo aviso de clamp
        self._feed_clamp_warned = False

        # ----------------- NOVO BLOCO -----------------
        # Lê a configuração para saber a cinemática desejada
        cfg_path = Path(__file__).resolve().parent.parent / "aoi_config.json"
        if cfg_path.exists():
            try:
                cfg_data = json.loads(cfg_path.read_text(encoding="utf-8"))
            except Exception:
                cfg_data = {}
        else:
            cfg_data = {}
        cnc_cfg = cfg_data.get("cnc", {})
        self.kinematics_mode = cnc_cfg.get("system_type", "cartesian").lower()
        self.corexy_cfg = cnc_cfg.get("corexy_config", {})

        # LOGA a escolha para facilitar depuração
        logger.info("Cinemática inicial: %s | corexy_cfg=%s",
                    self.kinematics_mode, self.corexy_cfg)

    # ---------- seleção dinâmica de cinemática ----------
    def set_kinematics_mode(self, mode: str):
        """
        Altera o modo de cinemática em tempo-real.
        Aceita 'cartesian' ou 'corexy'.
        """
        mode = str(mode).lower()
        assert mode in ("cartesian", "corexy"), "Modo inválido"
        self.kinematics_mode = mode

    # ---------- helpers CoreXY --------------------------
    def _convert_xy_to_ab(self, x: float, y: float) -> tuple[float, float]:
        """
        Converte deslocamentos/cartesianas (X,Y) para pulsos dos motores
        A e B de um sistema CoreXY.

            Motor A =  (+X) + (+Y)
            Motor B =  (+X) - (+Y)

        O utilizador pode inverter o sentido de cada motor nas
        Preferências.  Não aplicamos steps-per-unit aqui; o firmware já
        usa mm (ou steps) directos conforme a sua configuração.
        """
        cfg = getattr(self, "corexy_cfg", {}) or {}
        inv_a = -1 if cfg.get("motor_a_invert", False) else 1
        inv_b = -1 if cfg.get("motor_b_invert", False) else 1

        a = (x + y) * inv_a
        b = (x - y) * inv_b
        return a, b

    def set_invert_y(self, invert: bool = True):
        """Define se o eixo Y deve ser invertido (+Y vai para a frente do usuário)."""
        self.invert_y = bool(invert)
    
    def set_invert_z(self, invert: bool = True):
        """Define se o eixo Z deve ser invertido (+Z = cima)."""
        self.invert_z = bool(invert)

    def set_grbl_y_direction(self, forward_positive: bool = True):
        """
        Altera o parâmetro $3 (Step Dir Invert Mask) para inverter
        (ou não) o eixo Y diretamente no firmware GRBL.
        forward_positive=True   →  bit1 ligado  (valor 2 adicionado)
        forward_positive=False  →  bit1 desligado
        """
        if not self.is_connected or not self.grbl:
            return False
        try:
            # pede os settings com $#
            self.grbl.send_immediately("$$")
            time.sleep(0.3)  # pequena pausa para GRBL responder
            # A biblioteca expõe o dicionário de settings em grbl.settings
            current_mask = int(self.grbl.settings.get("$3", 0))
            want_bit = 0x02 if forward_positive else 0
            new_mask = (current_mask | 0x02) if forward_positive else (current_mask & ~0x02)
            if new_mask != current_mask:
                self.grbl.send_immediately(f"$3={new_mask}")
            return True
        except Exception:
            return False
        
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
            # Garante que o Y esteja invertido fisicamente (positivo = frente)
            self.set_grbl_y_direction(forward_positive=True)

            # ----------  Lê $$ para descobrir limits -----------
            # Solicitamos os settings logo após o unlock para conhecer os
            # limites máximos de feed ($110 / $111) e armazená-los em
            # self.max_feed.
            logger.debug("CONEXÃO: Solicitando $$ para obter limites de velocidade")
            self.grbl.send_immediately("$$")
            time.sleep(0.5)               # pequeno atraso p/ GRBL responder
            self._cache_settings_from_grbl()
            
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
        
    def wait_for_idle(self,
                      timeout: float = 5.0,
                      poll_interval: float = 0.1,
                      idle_grace: float = 0.4) -> bool:
        """
        Aguarda o término de qualquer movimento.
        A lógica:
           1) força consulta de status (?) a cada ‘poll_interval’
           2) aguarda ver a máquina entrar em Run ou Jog
           3) depois aguarda voltar a Idle
        Assim evitamos o “salto” observado quando a variável machine_status
        ainda está ‘Idle’ logo após o envio do comando.
        """
        if not self.is_connected or not self.grbl:
            return False

        start = time.time()
        saw_motion   = False
        idle_since   = None

        while True:
            # força GRBL a reportar um status
            try:
                self.grbl.send_immediately("?")
            except Exception:
                pass

            state = self.machine_status   # atualizado pelo callback _on_status_update

            if state in ("Run", "Jog"):
                saw_motion = True
                idle_since = None         # zera caso volte a ver Run
            elif state == "Idle":
                if saw_motion:            # cenário normal
                    return True
                # nunca vimos Run → conta um “grace time” em Idle
                idle_since = idle_since or time.time()
                if (time.time() - idle_since) >= idle_grace:
                    logger.debug("wait_for_idle: Idle estável sem movimento; liberando cedo.")
                    return True

            if time.time() - start > timeout:
                logger.warning("wait_for_idle: timeout depois de %.1fs (state=%s)", timeout, state)
                return False

            time.sleep(poll_interval)
        
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
        
    def move_to_absolute_position(self, x=None, y=None, z=None, feed_rate=1000):
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
        
        #  Ajusta feed se exceder limite configurado
        axis_limit = max(
            self.max_feed['x'] if x is not None else 0,
            self.max_feed['y'] if y is not None else 0,
            self.max_feed['z'] if z is not None else 0
        ) or min(self.max_feed.values())   # fallback
        if feed_rate > axis_limit:
            if not self._feed_clamp_warned:
                logger.warning("Feed solicitado (%s) > limite (%s). "
                               "Será enviado como %s",
                               feed_rate, axis_limit, axis_limit)
                self._feed_clamp_warned = True
            feed_rate = axis_limit

        # Constrói o comando  –  SEMPRE em X/Y
        #  (o firmware GRBL faz a cinemática CoreXY internamente)
        command = "G1"
        if x is not None:
            command += f" X{x}"
        if y is not None:
            y_send = -y if self.invert_y else y
            command += f" Y{y_send}"
        if z is not None:
            z_send = -z if self.invert_z else z
            command += f" Z{z_send}"
        command += f" F{feed_rate}"
        
        # Envia o comando
        self.send_command(command, priority=True)
        return True
    
    def step_move(self, axis: str, distance: float, feed_rate: float = 1000):
        """
        Move um único passo (distância em mm, sinal define direção) no eixo selecionado.
        Encapsula o uso de move_relative para manter a UI livre de detalhes G-code.
        """
        if axis.upper() == "X":
            return self.move_relative(x=distance, y=0, feed_rate=feed_rate)
        elif axis.upper() == "Y":
            return self.move_relative(x=0, y=distance, feed_rate=feed_rate)
        elif axis.upper() == "Z":
            return self.move_relative(x=0, y=0, z=distance, feed_rate=feed_rate)
        else:
            logger.error(f"step_move: eixo inválido '{axis}'")
            return False

    # “Aliases” para manter nomenclatura intuitiva na UI
    def jog_start(self, axis, direction, feed_rate=1000):
        """Wrapper p/ iniciar jog contínuo."""
        return self.start_continuous_jog(axis, direction, feed_rate)

    def jog_stop(self):
        """Wrapper p/ parar jog contínuo."""
        return self.stop_continuous_jog()
        
    def move_relative(self, x=0, y=0, z=0, feed_rate=1000):
        """
        Move em relação à posição atual.
        
        Args:
            x, y: Distância a mover em cada eixo
            feed_rate: Velocidade de avanço em mm/min
        """
        if not self.is_connected:
            return False
        
        # Ajuste de feed
        axis_limit = max(
            self.max_feed['x'] if abs(x) > 0 else 0,
            self.max_feed['y'] if abs(y) > 0 else 0,
            self.max_feed['z'] if abs(z) > 0 else 0
        ) or min(self.max_feed.values())
        if feed_rate > axis_limit:
            if not self._feed_clamp_warned:
                logger.warning("Feed solicitado (%s) > limite (%s). "
                               "Será enviado como %s",
                               feed_rate, axis_limit, axis_limit)
                self._feed_clamp_warned = True
            feed_rate = axis_limit
            
        # Muda para modo relativo
        self.send_command("G91", priority=True)
        
        # ------------------------------------------------------------------
        # Constrói o comando (com conversão CoreXY, se activada)
        # ------------------------------------------------------------------
        if self.kinematics_mode == "corexy":
            tgt_x = x if x is not None else 0.0
            tgt_y = y if y is not None else 0.0
            a, b = self._convert_xy_to_ab(tgt_x, tgt_y)
            command = f"G1 X{a:.3f} Y{b:.3f}"
            if z is not None:
                z_send = -z if self.invert_z else z
                command += f" Z{z_send}"
            command += f" F{feed_rate}"
        else:  # cartesiano
            y_send = -y if self.invert_y else y
            command = "G1"
            command += f" X{x} Y{y_send}"
            if z != 0:
                z_send = -z if self.invert_z else z
                command += f" Z{z_send}"
            command += f" F{feed_rate}"
        
        # Envia o comando
        self.send_command(command, priority=True)
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
        
        # ------------------------------------------------------------------
        # 1. Distância “longa” para JOG (só para ficar em movimento)
        # ------------------------------------------------------------------
        distance = 1000 * direction

        # ------------------------------------------------------------------
        # 2. Gera o comando $J=… com total segurança
        # ------------------------------------------------------------------
        jog_command = None                     # ← sempre inicializado
        axis_uc = axis.upper()

        if self.kinematics_mode == "corexy":
            # ‑- CoreXY: converter XY→AB mas enviar nos eixos X/Y
            if axis_uc == "X":
                a, b = self._convert_xy_to_ab(distance, 0)
                jog_command = f"$J=G91 X{a:.3f} Y{b:.3f} F{feed_rate}"
            elif axis_uc == "Y":
                a, b = self._convert_xy_to_ab(0, distance)
                jog_command = f"$J=G91 X{a:.3f} Y{b:.3f} F{feed_rate}"
            elif axis_uc == "Z":
                dist_z = -distance if self.invert_z else distance
                jog_command = f"$J=G91 Z{dist_z:.3f} F{feed_rate}"

        else:  # ‑- Cartesiano puro
            if axis_uc == "X":
                jog_command = f"$J=G91 X{distance:.3f} F{feed_rate}"
            elif axis_uc == "Y":
                dist_y = -distance if self.invert_y else distance
                jog_command = f"$J=G91 Y{dist_y:.3f} F{feed_rate}"
            elif axis_uc == "Z":
                dist_z = -distance if self.invert_z else distance
                jog_command = f"$J=G91 Z{dist_z:.3f} F{feed_rate}"

        # ------------------------------------------------------------------
        # 3. Segurança extra: aborta se algo ficou sem tratar
        # ------------------------------------------------------------------
        if jog_command is None:
            logger.error("start_continuous_jog: comando não gerado "
                        "(axis=%s  mode=%s)", axis_uc, self.kinematics_mode)
            return False

        # ------------------------------------------------------------------
        # 4. Atualiza estado e envia comando
        # ------------------------------------------------------------------
        self.jogging = True
        self.current_jog_command = jog_command
        return self.send_command(jog_command, priority=True)
    
    def _cache_settings_from_grbl(self):
        """
        Copia $settings do objeto GrblStreamer (se disponível) e
        atualiza self.max_feed.
        """
        if not self.grbl or not hasattr(self.grbl, "settings"):
            logger.warning("_cache_settings_from_grbl: settings não disponíveis")
            return
        try:
            s = self.grbl.settings
            self.max_feed['x'] = float(s.get("$110", self.max_feed['x']))
            self.max_feed['y'] = float(s.get("$111", self.max_feed['y']))
            self.max_acc['x']  = float(s.get("$120", self.max_acc['x']))
            self.max_acc['y']  = float(s.get("$121", self.max_acc['y']))
            self.max_feed['z'] = float(s.get("$112", self.max_feed['z']))
            self.max_acc['z']  = float(s.get("$122", self.max_acc['z']))
            logger.info("Limites de feed carregados  –  X:%s  Y:%s  (mm/min)",
                        self.max_feed['x'], self.max_acc['x'],
                        self.max_feed['y'], self.max_acc['y'])
        except Exception as e:
            logger.error("Falha ao parsear $settings: %s", e)
        
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
            # Comandos “normais” vão para fila padrão
            else:
                self.grbl.send(command)   # método normal do grbl-streamer
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
                'y': -position.get('y', 0) if self.invert_y else position.get('y', 0),
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