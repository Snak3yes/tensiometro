# plc_axis_controller.py
"""
Módulo independente para controle de eixos X, Y e Z via CLP (Modbus TCP).
Fornece movimentos absolutos, relativos, jog e homing para cada eixo.
"""
import time
import logging
from pymodbus.client import ModbusTcpClient

logger = logging.getLogger(__name__)

class PLCAxisController:
    """
    Controller para 3 eixos (X, Y, Z) usando Modbus TCP.
    Métodos principais:
        connect()/close()
        set_zero(axis)
        move_absolute(axis, position, speed=None)
        move_relative(axis, offset, speed=None)
        jog_start(axis, direction, speed=None)
        jog_stop(axis)
        wait_for_idle(axis, tolerance=1, timeout=10)
        read_position(axis)
        home_axis(axis)
        home_all()
    """
    # Mapeamento de memórias (coils) e registradores (holding)
    HOME_ALL_COIL = 1350
    ADDRESSES = {
        'X': {
            'zero':           1500,    # M1500 - confirmacao homing X
            'move_abs':       1050,    # M1050 - Interpolação X/Y (corrige ERRO: era 1100)
            'pos_input':      1100,    # D1100_X
            'speed':          20500,   # D20500 - velocidade compartilhada X/Y
            'jog_plus':       570,     # M570_X
            'jog_minus':      580,     # M580_X
            'jog_stop_plus':  1010,    # M1010_X
            'jog_stop_minus': 1011,    # M1011_X
            'pos_reg':        3000     # D3000_X (feedback posição atual)
        },
        'Y': {
            'zero':           1000,    # M1000 - confirmacao homing Y
            'move_abs':       1050,    # M1050 - Interpolação X/Y (corrige ERRO: era 600)
            'pos_input':      600,     # D600_Y
            'speed':          20500,   # D20500_Y
            'jog_plus':       670,     # M670_Y
            'jog_minus':      680,     # M680_Y
            'jog_stop_plus':  1020,    # M1020_Y
            'jog_stop_minus': 1021,    # M1021_Y
            'pos_reg':        3200     # D3200_Y (feedback posição atual)
        },
        'Z': {
            'zero':           500,     # M500 - confirmacao homing Z
            'move_abs':       1550,    # M1550_Z - inicia movimento absoluto Z (M1600 eh execucao)
            'pos_input':      1600,    # D1600_Z
            'speed':          21500,   # D21500_Z
            'jog_plus':       770,     # M770_Z
            'jog_minus':      780,     # M780_Z
            'jog_stop_plus':  1030,    # M1030_Z
            'jog_stop_minus': 1031,    # M1031_Z
            'pos_reg':        3400     # D3400_Z (feedback posição atual)
        }
    }
    FIXED_Z_SPEED_MM_MIN = 5000.0
    FIXED_Z_SPEED_REGISTER = ADDRESSES['Z']['speed']
    
    def __init__(self, host: str='192.168.1.5', port: int=502, auto_connect: bool=True):
        """
        Inicializa o controlador do CLP via Modbus TCP.
        
        Args:
            host: Endereço IP do CLP
            port: Porta Modbus TCP (padrão 502)
            auto_connect: Se True, tenta conectar imediatamente. Se False, a conexão
                          deve ser feita manualmente via connect().
        """
        # guarda os parâmetros de conexão
        self.host = host
        self.port = port
        # flag para indicar se está online
        self.is_connected = False
        # estado inicial da máquina
        self.machine_status = "Disconnected"
        # cria o cliente Modbus (sem conectar ainda)
        self.client = ModbusTcpClient(host, port=port)
        # limites de feed (compatível com MovementControlWidget)
        self.max_feed = {'x': float('inf'),
                         'y': float('inf'),
                         'z': float('inf')}
        # fator de conversão pulses → mm
        self.pulses_per_mm = 1.0
        # estado do backlight (iluminação inferior)
        self.backlight_on = False
        # Endereço da saída Y0.7 para controle do backlight (padrão 1 = M1 -> Y0.7)
        self.backlight_coil_address = 5
        # destinos ativos (usado para wait_for_idle inspirado na adesivadora)
        self._targets: dict[str, int] = {}
        
        # Conecta automaticamente se solicitado
        if auto_connect:
            self.connect()

    def _fixed_z_speed_pulses(self) -> int:
        """Retorna a velocidade fixa do eixo Z em pulsos/min."""
        return int(round(self.FIXED_Z_SPEED_MM_MIN * self.pulses_per_mm))

    def _normalize_register_write(self, address: int, value: int) -> int:
        """
        Normaliza escritas em registradores protegidos.

        O registrador D21500 deve permanecer fixo para o eixo Z.
        """
        if address == self.FIXED_Z_SPEED_REGISTER:
            fixed_value = self._fixed_z_speed_pulses()
            if int(value) != fixed_value:
                logger.info(
                    "Ignorando tentativa de sobrescrever D%d com %s; mantendo Z fixo em %s pulsos/min",
                    address,
                    value,
                    fixed_value,
                )
            return fixed_value
        return int(value)

    def _enforce_fixed_z_speed(self):
        """Regrava no PLC a velocidade fixa do eixo Z."""
        self._write_dword(self.FIXED_Z_SPEED_REGISTER, self._fixed_z_speed_pulses())

    # =========================================================================
    # Helpers internos de movimento
    # =========================================================================
    def _clamp_feed_rate(self, feed_rate: float | None) -> float | None:
        """
        Garante que o feed-rate esteja dentro de limites válidos.
        """
        if feed_rate is None:
            return None
        try:
            fr = float(feed_rate)
        except (TypeError, ValueError):
            return None
        fr = max(fr, 1.0)
        finite_limits = [v for v in self.max_feed.values() if v != float("inf")]
        if finite_limits:
            fr = min(fr, min(finite_limits))
        return fr

    def _apply_motion_pulses(self, targets_pulses: dict[str, int], feed_rate: float | None = None) -> bool:
        """
        Escreve alvo e velocidade para múltiplos eixos e dispara o movimento
        quase simultaneamente, evitando jitter entre eixos.
        """
        if not targets_pulses:
            return True
        if not self.client or not self.is_connected:
            raise IOError("PLC não conectado")

        fr = self._clamp_feed_rate(feed_rate)
        speed_pulses = int(round(fr * self.pulses_per_mm)) if fr is not None else None

        logger.info(f"🎯 _apply_motion_pulses: alvos={targets_pulses}, feed_rate={feed_rate}mm/min, speed_pulses={speed_pulses}pulsos/min")

        # limpa alvos anteriores e registra os novos para wait_for_idle
        self._targets.clear()

        # 1) Grava alvos e velocidades
        for ax, tgt in targets_pulses.items():
            cfg = self.ADDRESSES[ax]
            logger.info(f"🎯 Eixo {ax}: escrevendo target={tgt} pulsos em pos_input (endereco {cfg['pos_input']})")
            self._write_dword(cfg['pos_input'], int(tgt))
            axis_speed_pulses = self._fixed_z_speed_pulses() if ax == 'Z' else speed_pulses
            if axis_speed_pulses is not None:
                logger.info(f"🎯 Eixo {ax}: escrevendo speed={axis_speed_pulses} pulsos/min em speed (endereco {cfg['speed']})")
                self._write_dword(cfg['speed'], int(axis_speed_pulses))
            self._targets[ax] = int(tgt)

            # Lê posicao atual ANTES do movimento para verificar
            try:
                current_before = self._read_dword(cfg['pos_reg'])
                logger.info(f"🎯 Eixo {ax}: posicao atual (pos_reg) ANTES do movimento: {current_before} pulsos")
            except Exception as e:
                logger.warning(f"⚠️ Não foi possível ler posição atual antes do movimento: {e}")

        # 2) Dispara todos os eixos rapidamente
        # NOTA: X e Y usam o MESMO coil (M1050) para interpolação
        # Então precisamos pulsar cada coil único apenas uma vez
        unique_coils = {}
        for ax in targets_pulses.keys():
            cfg = self.ADDRESSES[ax]
            coil = cfg['move_abs']
            if coil not in unique_coils:
                unique_coils[coil] = []
            unique_coils[coil].append(ax)

        # Pulsa cada coil único apenas uma vez
        for coil, axes in unique_coils.items():
            axes_str = "+".join(axes)
            logger.info(f"⚡ Eixo(s) {axes_str}: pulsando coil move_abs (endereco {coil}) para iniciar movimento")
            self._pulse_coil(coil)

        self.machine_status = "Run"
        logger.info(f"✅ Status alterado para 'Run', movimento iniciado")

        # Pequena pausa para deixar o PLC começar o movimento
        time.sleep(0.1)

        # Lê posição logo após iniciar movimento para verificar se começou a mudar
        for ax in targets_pulses.keys():
            cfg = self.ADDRESSES[ax]
            try:
                current_after = self._read_dword(cfg['pos_reg'])
                target = self._targets[ax]
                diff = current_after - target
                logger.info(f"📊 Eixo {ax}: posicao APÓS inicio={current_after} pulsos, target={target} pulsos, diferença={diff} pulsos ({diff/self.pulses_per_mm:.3f}mm)")
            except Exception as e:
                logger.warning(f"⚠️ Não foi possível ler posição após inicio do movimento: {e}")

        return True

    def set_connection_params(self, host: str, port: int):
        """
        Atualiza host/porta do CLP e recria o cliente Modbus.
        Fecha a conexão atual, se existir.
        """
        if self.is_connected:
            self.close()
        self.host = host
        self.port = int(port)
        self.client = ModbusTcpClient(host, port=int(port))
        self.machine_status = "Disconnected"

    def connect(self) -> bool:
        """
        Tenta conectar ao CLP via Modbus TCP.
        
        Returns:
            True se a conexão foi bem-sucedida, False caso contrário.
            
        Raises:
            ConnectionError: Se a conexão falhar.
        """
        if self.is_connected:
            return True
            
        try:
            connected = self.client.connect()
            if not connected:
                raise ConnectionError(f"Falha ao conectar ao CLP em {self.host}:{self.port}")
            self.is_connected = True
            self.machine_status = "Idle"
            try:
                self._enforce_fixed_z_speed()
            except Exception as e:
                logger.warning("Nao foi possivel aplicar a velocidade fixa do eixo Z na conexao: %s", e)
            return True
        except Exception as e:
            self.is_connected = False
            self.machine_status = "Disconnected"
            raise ConnectionError(f"Falha ao conectar ao CLP em {self.host}:{self.port}: {e}")
    
    

    def close(self):
        """Fecha a conexão Modbus."""
        if self.client:
            self.client.close()
        # sinaliza para a aplicação que não está mais conectado
        self.is_connected = False

    def disconnect(self):
        """
        Alias para fechar a conexão (compatibilidade com AOIControllerApp).
        """
        self.close()

    def _write_dword(self, address: int, value: int):
        """
        Escreve valor INT32 (little-endian) em dois registradores
        de retenção (holding registers).
        """
        if not self.client or not self.is_connected:
            raise IOError("PLC não conectado")
        u32 = value & 0xFFFFFFFF
        lo = u32 & 0xFFFF
        hi = (u32 >> 16) & 0xFFFF
        return self.client.write_registers(address, [lo, hi])

    def _read_dword(self, address: int) -> int:
        """
        Lê INT32 assinado de dois registradores de retenção.
        """
        if not self.client or not self.is_connected:
            raise IOError("PLC não conectado")
        res = self.client.read_holding_registers(address, count=2)
        if res.isError():
            raise IOError(f"Falha na leitura DWORD em {address}")
        lo, hi = res.registers
        u32 = (hi << 16) | lo
        return u32 if u32 < 0x80000000 else u32 - 0x100000000

    def _pulse_coil(self, coil: int, duration_ms: int=100):
        """
        Aciona um coil por `duration_ms` milissegundos (borda de subida).

        Aumentado de 20ms para 100ms para garantir que o PLC reconheça
        o comando de movimento absoluto.
        """
        if not self.client or not self.is_connected:
            raise IOError("PLC não conectado")
        self.client.write_coil(coil, True)
        time.sleep(duration_ms/1000.0)
        self.client.write_coil(coil, False)

    def _legacy_set_zero_unused(self, axis: str):
        """Zera a posição atual do eixo (memória de zero)."""
        mem = self.ADDRESSES[axis]['zero']
        self._pulse_coil(mem)

    def move_absolute(self, axis: str, position: int, speed: int=None):
        """
        Move o eixo `axis` para posição absoluta (pulsos).
        Se `speed` for fornecido, grava no registrador de velocidade.
        """
        return self._apply_motion_pulses({axis: position}, speed / self.pulses_per_mm if speed else None)

    def move_relative(self, x=None, y=None, z=None, feed_rate=None):
        """
        Move de forma relativa em múltiplos eixos.
        Compatível com GRBLCNCController para uso em threads de medição.
        
        Args:
            x, y, z: Deslocamento relativo em mm (None para não mover o eixo)
            feed_rate: Velocidade em mm/min (opcional)
        """
        targets = {}
        if x is not None:
            current_x = self._read_dword(self.ADDRESSES['X']['pos_reg'])
            targets['X'] = current_x + int(round(x * self.pulses_per_mm))

        if y is not None:
            current_y = self._read_dword(self.ADDRESSES['Y']['pos_reg'])
            targets['Y'] = current_y + int(round(y * self.pulses_per_mm))

        if z is not None:
            current_z = self._read_dword(self.ADDRESSES['Z']['pos_reg'])
            targets['Z'] = current_z + int(round(z * self.pulses_per_mm))

        return self._apply_motion_pulses(targets, feed_rate)

    def step_move(self, axis: str, distance_mm: float, feed_rate: float = None) -> bool:
        """
        Move um passo no eixo especificado:
          - distance_mm: deslocamento em mm (positivo ou negativo)
          - feed_rate: velocidade em mm/min (opcional)
        Converte mm → pulsos usando pulses_per_mm, faz move_relative + wait_for_idle.
        Retorna True se o eixo atingir o destino, False em timeout.
        """
        # 1) converte milímetros em pulsos
        pulses = int(round(distance_mm * self.pulses_per_mm))
        # 2) converte feed_rate (mm/min) em pulsos/min, se fornecido
        speed = int(round(feed_rate * self.pulses_per_mm)) if feed_rate is not None else None

        # 3) Calcula timeout apropriado baseado no tempo esperado do movimento
        # Tempo esperado (segundos) = (distância / velocidade) * 60 + margem de segurança
        if feed_rate and feed_rate > 0:
            distance_abs = abs(distance_mm)
            expected_time_sec = (distance_abs / feed_rate) * 60  # converter min para seg
            # Timeout = tempo esperado + margem de 50% + mínimo de 5 segundos
            timeout = max(5, int(expected_time_sec * 1.5))
            logger.info(f"⏱️ Timeout calculado: {timeout}s (distância={distance_abs}mm, velocidade={feed_rate}mm/min, tempo esperado≈{expected_time_sec:.1f}s)")
        else:
            timeout = 30  # Timeout padrão se não tiver feed_rate
            logger.info(f"⏱️ Timeout padrão: {timeout}s (feed_rate não fornecido)")

        # 4) executa movimento relativo usando o método antigo interno
        self._move_relative_single_axis(axis, pulses, speed)
        # 5) aguarda até o eixo estar idle com timeout calculado
        return self.wait_for_idle(axis, timeout=timeout)
    
    def _move_relative_single_axis(self, axis: str, offset: int, speed: int=None):
        """
        Move um único eixo de forma relativa (método interno).
        """
        current = self._read_dword(self.ADDRESSES[axis]['pos_reg'])
        return self._apply_motion_pulses({axis: current + offset}, speed / self.pulses_per_mm if speed else None)

    def jog_start(self, axis: str, direction: int, feed_rate: float = None):
        """
        Inicia jog contínuo no eixo.
        Args:
            axis: Nome do eixo ('X', 'Y' ou 'Z')
            direction: Direção do movimento (+1 ou -1)
            feed_rate: Velocidade em mm/min (será convertida para pulsos/min)
        """
        # Normaliza nome do eixo para maiúscula
        axis = axis.upper()
        if axis not in self.ADDRESSES:
            raise ValueError(f"Eixo inválido: {axis}")
        cfg = self.ADDRESSES[axis]
        # Converte feed_rate (mm/min) para pulsos/min se fornecido
        if axis == 'Z':
            self._write_dword(cfg['speed'], self._fixed_z_speed_pulses())
        elif feed_rate is not None:
            fr = self._clamp_feed_rate(feed_rate)
            speed_pulses = int(round(fr * self.pulses_per_mm))
            self._write_dword(cfg['speed'], speed_pulses)

        # Aciona o coil apropriado baseado na direção
        coil = cfg['jog_plus'] if direction > 0 else cfg['jog_minus']
        self.client.write_coil(coil, True)
        self.machine_status = "Jog"

    def jog_stop(self, axis: str = None):
        """
        Para o jog contínuo de todos os eixos.
        O parâmetro axis é ignorado para manter compatibilidade com a UI.
        """
        # Para todos os eixos (a UI não especifica qual)
        alvos = [axis] if axis else list(self.ADDRESSES.keys())
        for ax in alvos:
            cfg = self.ADDRESSES[ax]
            self.client.write_coil(cfg['jog_plus'], False)
            self.client.write_coil(cfg['jog_minus'], False)
        self.machine_status = "Idle"

    def move_to_absolute_position(self, x=None, y=None, z=None, feed_rate=None):
        """
        Move para uma posição absoluta em coordenadas.
        Compatível com GRBLCNCController para uso em threads de medição.
        
        Args:
            x, y, z: Coordenadas de destino em mm (None para não mover o eixo)
            feed_rate: Velocidade em mm/min (opcional)
        """
        if self.pulses_per_mm <= 0:
            raise ValueError(
                f"Calibracao invalida do PLC: pulses_per_mm={self.pulses_per_mm}. "
                "O fator deve ser maior que zero."
            )

        targets = {}
        if x is not None:
            targets['X'] = int(round(x * self.pulses_per_mm))

        if y is not None:
            targets['Y'] = int(round(y * self.pulses_per_mm))

        if z is not None:
            targets['Z'] = int(round(z * self.pulses_per_mm))
            logger.info(
                "Movimento absoluto Z solicitado: z_mm=%s, pulses_per_mm=%s, target_pulses=%s",
                z,
                self.pulses_per_mm,
                targets['Z'],
            )

        return self._apply_motion_pulses(targets, feed_rate)
    
    def wait_for_idle(self, axis=None, tolerance: int=1, timeout: int=10):
        """
        Aguarda até que os eixos fiquem idle.
        - Se axis for string, usa apenas aquele alvo; senão usa _targets ativos.
        """
        # Se status atual é "Alarm", tenta resetar automaticamente
        if self.machine_status == "Alarm":
            logger.info("🔄 Status é 'Alarm', verificando se máquina pode ser resetada")
            # Verifica se todos os eixos estão idle (sem movimento ativo)
            all_idle = True
            for ax, cfg in self.ADDRESSES.items():
                # Lê status de movimento do eixo (coil jog_plus/jog_minus)
                try:
                    jog_plus = self.client.read_coils(cfg['jog_plus'], count=1).bits[0]
                    jog_minus = self.client.read_coils(cfg['jog_minus'], count=1).bits[0]
                    if jog_plus or jog_minus:
                        all_idle = False
                        break
                except:
                    pass

            if all_idle:
                logger.info("🔄 Todos os eixos estão idle, resetando status de 'Alarm' para 'Idle'")
                self.machine_status = "Idle"
            else:
                logger.warning("⚠️ Status é 'Alarm' e máquina ainda está em movimento, impossível resetar automaticamente")

        # fallback para compatibilidade: se nada em _targets, usa axis único ou todos
        targets = {}
        if isinstance(axis, str):
            # se pediram eixo específico, tenta alvo registrado; senão lê pos_input
            if self._targets:
                if axis in self._targets:
                    targets = {axis: self._targets[axis]}
            else:
                targets = {axis: self._read_dword(self.ADDRESSES[axis]['pos_input'])}
        else:
            targets = self._targets.copy() if self._targets else {
                ax: self._read_dword(cfg['pos_input'])
                for ax, cfg in self.ADDRESSES.items()
            }

        logger.info(f"⏳ wait_for_idle iniciado: targets={targets}, tolerance={tolerance} pulsos, timeout={timeout}s")

        t0 = time.time()
        ok_axes = set()
        last_log_time = -1.0  # Para forçar primeiro log
        log_interval = 1.0  # Log a cada 1 segundo para não encher o terminal

        while time.time() - t0 < timeout:
            all_reached = True
            elapsed = time.time() - t0

            # Log progresso periodicamente
            should_log = (elapsed - last_log_time >= log_interval)

            for ax, tgt in list(targets.items()):
                if ax in ok_axes:
                    continue
                pos = self._read_dword(self.ADDRESSES[ax]['pos_reg'])
                diff = pos - tgt

                # Log periodicamente
                if should_log:
                    logger.info(f"📊 Eixo {ax}: pos={pos} pulsos, target={tgt} pulsos, diff={diff} pulsos ({diff/self.pulses_per_mm:.3f}mm), elapsed={elapsed:.1f}s")

                if abs(pos - tgt) <= tolerance:
                    logger.info(f"✅ Eixo {ax} atingiu target! pos={pos}, target={tgt}, diff={diff} pulsos (tolerancia={tolerance})")
                    ok_axes.add(ax)
                else:
                    all_reached = False

            if all_reached:
                self._targets.clear()
                self.machine_status = "Idle"
                logger.info(f"✅ Todos os eixos atingiram targets após {elapsed:.1f}s")
                return True

            if should_log:
                last_log_time = elapsed

            time.sleep(0.05)

        # timeout - mostra situação final antes de retornar
        elapsed = time.time() - t0
        logger.warning(f"⏱️ TIMEOUT em wait_for_idle após {elapsed:.1f}s")
        for ax, tgt in targets.items():
            pos = self._read_dword(self.ADDRESSES[ax]['pos_reg'])
            diff = pos - tgt
            logger.warning(f"⏱️ Eixo {ax}: FINAL pos={pos} pulsos, target={tgt} pulsos, diff={diff} pulsos ({diff/self.pulses_per_mm:.3f}mm), tolerance={tolerance}")

        # NÃO mudar status para "Alarm" automaticamente!
        # Isso permite que o usuário possa tentar novamente sem precisar resetar
        logger.warning(f"⏱️ Status mantido como '{self.machine_status}' (não mudou para Alarm)")
        # REMOVIDO: self.machine_status = "Alarm" if self.machine_status == "Run" else self.machine_status
        return False
    
    def _wait_for_idle_axis(self, axis: str, tolerance: int=1, timeout: int=10) -> bool:
        """
        Aguarda até um eixo específico atingir o alvo.
        (Renomeado do antigo wait_for_idle para evitar conflito)
        """
        target = self._read_dword(self.ADDRESSES[axis]['pos_input'])
        t0 = time.time()
        while time.time() - t0 < timeout:
            cur = self._read_dword(self.ADDRESSES[axis]['pos_reg'])
            if abs(cur - target) <= tolerance:
                return True
            time.sleep(0.05)
        return False

    def read_position(self, axis: str) -> int:
        """Lê a posição atual do eixo em pulsos."""
        return self._read_dword(self.ADDRESSES[axis]['pos_reg'])
    
    def get_current_position(self) -> dict:
        """
        Retorna a posição atual de X, Y e Z em milímetros.
        Assume 1 pulso = 1 mm por padrão; se necessário ajuste em pulses_per_mm.
        """
        try:
            xp = self.read_position('X')
            yp = self.read_position('Y')
            zp = self.read_position('Z')
            return {
                'x': xp / self.pulses_per_mm,
                'y': yp / self.pulses_per_mm,
                'z': zp / self.pulses_per_mm
            }
        except Exception as e:
            raise IOError(f"Falha ao obter posição atual via PLC: {e}")

    def home_axis(self, axis: str):
        """
        Executa homing do eixo individual (usa mesma memória de zero).
        """
        self._pulse_coil(self.ADDRESSES[axis]['zero'])

    def home_all(self):
        """
        Sequência de homing completa: Z primeiro, depois X e Y.
        """
        # homing Z
        self._pulse_coil(self.ADDRESSES['Z']['zero'])
        time.sleep(3.0)
        # homing X e Y em paralelo
        self._pulse_coil(self.ADDRESSES['X']['zero'])
        self._pulse_coil(self.ADDRESSES['Y']['zero'])

    # =========================================================================
    # PARADA DE EMERGÊNCIA / RESET
    # =========================================================================
    def send_soft_reset(self) -> bool:
        """
        Interrompe movimentos e sinaliza estado de alarme.

        Retorna True quando o pedido foi aceito; False em caso de falha ou PLC
        desconectado.
        """
        if not self.is_connected or not self.client:
            logging.warning("Soft reset ignorado: PLC não conectado")
            return False

        try:
            # Garante que qualquer jog contínuo seja interrompido
            self.jog_stop()
            # Marca estado interno para bloquear novos comandos na UI
            self.machine_status = "Alarm"
            logging.info("PLC em estado de ALARM (soft reset solicitado)")
            return True
        except Exception as e:
            logging.error(f"Falha ao executar soft reset no PLC: {e}")
            return False

    def unlock(self) -> bool:
        """
        Libera a máquina após um soft reset, voltando ao estado Idle.
        """
        if not self.is_connected:
            logging.warning("Unlock ignorado: PLC não conectado")
            return False

        self.machine_status = "Idle"
        logging.info("PLC liberado após soft reset")
        return True

    # =========================================================================
    # MONITORAMENTO / EDIÇÃO DE REGISTROS
    # =========================================================================
    def read_coil(self, coil: int) -> bool:
        """Lê o estado de um coil (bit)."""
        if not self.client or not self.is_connected:
            raise IOError("PLC não conectado")
        res = self.client.read_coils(coil, count=1)
        if res.isError():
            raise IOError(f"Falha na leitura do coil {coil}: {res}")
        return bool(res.bits[0])

    def write_coil(self, coil: int, value: bool) -> bool:
        """Escreve um coil (bool)."""
        if not self.client or not self.is_connected:
            raise IOError("PLC não conectado")
        res = self.client.write_coil(coil, bool(value))
        if res.isError():
            raise IOError(f"Falha na escrita do coil {coil}: {res}")
        return True

    def pulse_coil(self, coil: int, duration_ms: int = 20) -> bool:
        """Pulsa um coil por `duration_ms` ms."""
        if not self.client or not self.is_connected:
            raise IOError("PLC não conectado")
        self._pulse_coil(coil, duration_ms)
        return True

    def read_register(self, address: int) -> int:
        """Lê um registrador double-word (32 bits)."""
        if not self.client or not self.is_connected:
            raise IOError("PLC não conectado")
        return self._read_dword(address)

    def write_register(self, address: int, value: int) -> bool:
        """Escreve um registrador double-word (32 bits)."""
        if not self.client or not self.is_connected:
            raise IOError("PLC não conectado")
        self._write_dword(address, self._normalize_register_write(address, value))
        return True

    def snapshot_registers(self) -> dict:
        """
        Retorna um snapshot dos principais registradores e coils por eixo.
        Usado para depuração/monitoramento na UI.
        """
        if not self.is_connected:
            raise IOError("PLC não conectado")

        snap = {
            "machine_status": self.machine_status,
            "pulses_per_mm": self.pulses_per_mm,
            "backlight_on": self.backlight_on,
            "axes": {}
        }

        for axis, cfg in self.ADDRESSES.items():
            axis_data = {}
            # registradores
            axis_data["pos_input"] = self._read_dword(cfg["pos_input"])
            axis_data["pos_reg"] = self._read_dword(cfg["pos_reg"])
            axis_data["speed"] = self._read_dword(cfg["speed"])
            # coils
            axis_data["zero"] = self.read_coil(cfg["zero"])
            axis_data["move_abs"] = self.read_coil(cfg["move_abs"])
            axis_data["jog_plus"] = self.read_coil(cfg["jog_plus"])
            axis_data["jog_minus"] = self.read_coil(cfg["jog_minus"])
            axis_data["jog_stop_plus"] = self.read_coil(cfg["jog_stop_plus"])
            axis_data["jog_stop_minus"] = self.read_coil(cfg["jog_stop_minus"])

            snap["axes"][axis] = axis_data

        return snap

    # =========================================================================
    # CONTROLE DE ILUMINAÇÃO (BACKLIGHT)
    # =========================================================================

    def backlight_set(self, on: bool) -> bool:
        """
        Liga ou desliga o backlight (iluminação inferior do stencil).
        
        Args:
            on: True para ligar, False para desligar
            
        Returns:
            True se o comando foi executado com sucesso
        """
        logging.debug(f"🔍 DEBUG PLC: backlight_set chamado com on={on}, address={self.backlight_coil_address}")
        
        if not self.client or not self.is_connected:
            logging.warning("PLC não conectado - não é possível controlar backlight")
            return False
        
        try:
            logging.debug(f"🔍 DEBUG PLC: Executando write_coil(address={self.backlight_coil_address}, value={on})")
            result = self.client.write_coil(self.backlight_coil_address, on)
            logging.debug(f"🔍 DEBUG PLC: write_coil retornou result={result}, isError={result.isError() if hasattr(result, 'isError') else 'N/A'}")
            
            if result.isError():
                logging.error(f"Erro ao {'ligar' if on else 'desligar'} backlight: {result}")
                return False
            
            self.backlight_on = on
            logging.info(f"Backlight {'LIGADO' if on else 'DESLIGADO'} (Y0.7)")
            logging.debug(f"🔍 DEBUG PLC: backlight_set retornando True")
            return True
        except Exception as e:
            logging.error(f"Exceção ao controlar backlight: {e}")
            logging.debug(f"🔍 DEBUG PLC: backlight_set retornando False devido a exceção")
            return False
    
    def backlight_turn_on(self) -> bool:
        """Liga o backlight."""
        return self.backlight_set(True)
    
    def backlight_turn_off(self) -> bool:
        """Desliga o backlight."""
        return self.backlight_set(False)
    
    def backlight_toggle(self) -> bool:
        """Alterna o estado do backlight."""
        return self.backlight_set(not self.backlight_on)
    
    def backlight_is_on(self) -> bool:
        """Retorna o estado atual do backlight."""
        return self.backlight_on

    def set_zero(self, axis: str):
        logger.warning("set_zero(%s) ignorado: mapa atual do PLC nao expoe comando dedicado de zero por eixo", axis)
        return False

    def home_axis(self, axis: str):
        logger.info("home_axis(%s): usando homing global via M%d", axis, self.HOME_ALL_COIL)
        self._pulse_coil(self.HOME_ALL_COIL)

    def home_all(self):
        self._pulse_coil(self.HOME_ALL_COIL)


if __name__ == "__main__":
    # Exemplo de uso rápido
    plc = PLCAxisController("192.168.1.5", 502)
    try:
        plc.home_all()
        plc.move_absolute("X", 10000)
        if plc.wait_for_idle("X"):
            print("X chegou ao destino")
        plc.jog_start("Y", +1, speed=1500)
        time.sleep(1.0)
        plc.jog_stop("Y")
    finally:
        plc.close()
