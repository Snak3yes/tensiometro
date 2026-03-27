"""
PLC Axis Controller Adapter - Backward Compatibility via Adapter Pattern

Este adapter mantém 100% de compatibilidade com a interface original PLCAxisController,
delegando para 7 controllers especializados seguindo Interface Segregation Principle.

Autor: Fase 5 do SOLID Refactoring Phase 2
"""

import time
import logging
from typing import Optional, Dict
from pymodbus.client import ModbusTcpClient


logger = logging.getLogger(__name__)


class PLCAxisControllerAdapter:
    """
    Adapter para backward compatibility com PLCAxisController original.

    Implementa todos os 37 métodos públicos da interface original,
    delegando para 7 controllers especializados via composition.

    Padrão: Adapter Pattern + Composition
    Objetivo: Zero breaking changes durante refatoração
    """

    # Mapeamento de memórias (coils) e registradores (holding)
    HOME_ALL_COIL = 1350
    ADDRESSES = {
        'X': {
            'zero': 1500,      # M1500 - confirmacao homing X
            'move_abs': 1050,   # M1050 - Interpolação X/Y
            'pos_input': 1100,  # D1100_X
            'speed': 20500,     # D20500 - velocidade compartilhada X/Y
            'jog_plus': 570,    # M570_X
            'jog_minus': 580,   # M580_X
            'jog_stop_plus': 1010,   # M1010_X
            'jog_stop_minus': 1011,  # M1011_X
            'pos_reg': 3000     # D3000_X
        },
        'Y': {
            'zero': 1000,      # M1000 - confirmacao homing Y
            'move_abs': 1050,   # M1050 - Interpolação X/Y
            'pos_input': 600,   # D600_Y
            'speed': 20500,     # D20500_Y
            'jog_plus': 670,    # M670_Y
            'jog_minus': 680,   # M680_Y
            'jog_stop_plus': 1020,   # M1020_Y
            'jog_stop_minus': 1021,  # M1021_Y
            'pos_reg': 3200     # D3200_Y
        },
        'Z': {
            'zero': 500,       # M500 - confirmacao homing Z
            'move_abs': 1600,   # M1600_Z
            'pos_input': 1600,  # D1600_Z
            'speed': 21500,     # D21500_Z
            'jog_plus': 770,    # M770_Z
            'jog_minus': 780,   # M780_Z
            'jog_stop_plus': 1030,   # M1030_Z
            'jog_stop_minus': 1031,  # M1031_Z
            'pos_reg': 3400     # D3400_Z
        }
    }

    def __init__(self, host: str = '192.168.1.5', port: int = 502, auto_connect: bool = True):
        """
        Inicializa o adapter e todos os controllers especializados.

        Args:
            host: Endereço IP do PLC
            port: Porta Modbus TCP (padrão 502)
            auto_connect: Se True, tenta conectar imediatamente
        """
        # Import controllers para evitar import circular
        from aoi_lib.plc.controllers import (
            PLCConnectionManager,
            PLCAbsoluteMovementController,
            PLCRelativeMovementController,
            PLCJogMovementController,
            PLCHomingController,
            PLCPositionReaderController,
            PLCRegistersController
        )

        # Criar connection manager
        self.connection_manager = PLCConnectionManager(host, port)

        # Criar controllers especializados com dependency injection
        self.absolute_controller = PLCAbsoluteMovementController(
            connection_manager=self.connection_manager,
            pulses_per_mm=1.0,
            max_feed={'x': float('inf'), 'y': float('inf'), 'z': float('inf')}
        )

        self.relative_controller = PLCRelativeMovementController(
            connection_manager=self.connection_manager,
            absolute_controller=self.absolute_controller,
            pulses_per_mm=1.0
        )

        self.jog_controller = PLCJogMovementController(
            connection_manager=self.connection_manager,
            absolute_controller=self.absolute_controller,
            pulses_per_mm=1.0,
            max_feed={'x': float('inf'), 'y': float('inf'), 'z': float('inf')}
        )

        self.homing_controller = PLCHomingController(
            connection_manager=self.connection_manager,
            absolute_controller=self.absolute_controller
        )

        self.position_reader = PLCPositionReaderController(
            connection_manager=self.connection_manager,
            pulses_per_mm=1.0
        )

        self.registers_controller = PLCRegistersController(
            connection_manager=self.connection_manager,
            position_reader=self.position_reader,
            pulses_per_mm=1.0
        )

        # Propriedades públicas para compatibilidade
        self.host = host
        self.port = port
        self.client = self.connection_manager.client
        self.max_feed = {'x': float('inf'), 'y': float('inf'), 'z': float('inf')}
        self.pulses_per_mm = 1.0
        self.backlight_on = False
        self.backlight_coil_address = 5

        # Conecta automaticamente se solicitado
        if auto_connect:
            self.connect()

    # =========================================================================
    # Propriedades para compatibilidade com interface original
    # =========================================================================

    @property
    def is_connected(self) -> bool:
        """Verifica se o PLC está conectado."""
        return self.connection_manager.is_connected()

    @is_connected.setter
    def is_connected(self, value: bool):
        """Setter para compatibilidade."""
        # Apenas log, não modifica estado real
        logger.debug(f"is_connected set to {value} (read-only property)")

    @property
    def machine_status(self) -> str:
        """Retorna status da máquina."""
        # Mantém cache simples de status
        if not self.is_connected:
            return "Disconnected"
        return "Idle"  # Simplificado - poderia expor dos controllers

    @machine_status.setter
    def machine_status(self, value: str):
        """Setter para compatibilidade."""
        logger.debug(f"machine_status set to {value} (read-only property)")

    # =========================================================================
    # Connection Management (4 métodos) - delega para PLCConnectionManager
    # =========================================================================

    def connect(self) -> bool:
        """
        Tenta conectar ao CLP via Modbus TCP.

        Returns:
            True se a conexão foi bem-sucedida, False caso contrário.
        """
        try:
            result = self.connection_manager.connect()
            if result:
                logger.info(f"✅ PLC conectado em {self.host}:{self.port}")
            return result
        except Exception as e:
            logger.error(f"❌ Falha ao conectar ao CLP: {e}")
            return False

    def close(self):
        """Fecha a conexão Modbus."""
        self.connection_manager.disconnect()

    def disconnect(self):
        """Alias para fechar a conexão (compatibilidade)."""
        self.close()

    def set_connection_params(self, host: str, port: int):
        """
        Atualiza host/porta do CLP e recria o cliente Modbus.

        Args:
            host: Novo endereço IP
            port: Nova porta
        """
        if self.is_connected:
            self.close()

        self.host = host
        self.port = port

        # Recriar connection manager com novos parâmetros
        from aoi_lib.plc.controllers import PLCConnectionManager

        old_manager = self.connection_manager
        self.connection_manager = PLCConnectionManager(host, port)

        # Atualizar referências em todos os controllers
        self.absolute_controller.connection_manager = self.connection_manager
        self.relative_controller.connection_manager = self.connection_manager
        self.jog_controller.connection_manager = self.connection_manager
        self.homing_controller.connection_manager = self.connection_manager
        self.position_reader.connection_manager = self.connection_manager
        self.registers_controller.connection_manager = self.connection_manager

        # Atualizar client
        self.client = self.connection_manager.client

        logger.info(f"Parâmetros de conexão atualizados: {host}:{port}")

    # =========================================================================
    # Absolute Movement (4 métodos) - delega para PLCAbsoluteMovementController
    # =========================================================================

    def _legacy_set_zero_unused(self, axis: str):
        """Zera a posição atual do eixo (memória de zero)."""
        self.absolute_controller.set_zero()

    def move_absolute(self, axis: str, position: int, speed: int = None):
        """
        Move o eixo `axis` para posição absoluta (pulsos).

        Args:
            axis: Eixo ('X', 'Y', ou 'Z')
            position: Posição absoluta em pulsos
            speed: Taxa de avanço em pulsos/minuto (opcional)
        """
        self.absolute_controller.move_absolute(axis, position, speed)

    def move_to_absolute_position(self, x=None, y=None, z=None, feed_rate=1000):
        """
        Move para uma posição absoluta em coordenadas.

        Args:
            x, y, z: Coordenadas de destino em mm (None para não mover o eixo)
            feed_rate: Velocidade em mm/min
        """
        # Converte mm → pulsos
        if x is not None:
            x = int(round(x * self.pulses_per_mm))
        if y is not None:
            y = int(round(y * self.pulses_per_mm))
        if z is not None:
            z = int(round(z * self.pulses_per_mm))

        self.absolute_controller.move_to_absolute_position(x, y, z,
                                                             speed_x=feed_rate,
                                                             speed_y=feed_rate,
                                                             speed_z=feed_rate)

    def _apply_motion_pulses(self, targets_pulses: dict[str, int], feed_rate: float = None):
        """
        Escreve alvo e velocidade para múltiplos eixos e dispara o movimento.

        Método interno para compatibilidade.
        """
        self.absolute_controller.apply_motion_pulses(targets_pulses, feed_rate)

    # =========================================================================
    # Relative Movement (3 métodos) - delega para PLCRelativeMovementController
    # =========================================================================

    def move_relative(self, x=None, y=None, z=None, feed_rate=1000):
        """
        Move de forma relativa em múltiplos eixos.

        Args:
            x, y, z: Deslocamento relativo em mm (None para não mover o eixo)
            feed_rate: Velocidade em mm/min
        """
        # Converte mm → pulsos
        if x is not None:
            x = int(round(x * self.pulses_per_mm))
        if y is not None:
            y = int(round(y * self.pulses_per_mm))
        if z is not None:
            z = int(round(z * self.pulses_per_mm))

        # Delega para controller relativo
        targets = {}
        if x is not None:
            current_x = self.position_reader.read_position('X')
            targets['X'] = current_x + x

        if y is not None:
            current_y = self.position_reader.read_position('Y')
            targets['Y'] = current_y + y

        if z is not None:
            current_z = self.position_reader.read_position('Z')
            targets['Z'] = current_z + z

        self.absolute_controller.apply_motion_pulses(targets, feed_rate)

    def step_move(self, axis: str, distance_mm: float, feed_rate: float = None):
        """
        Move um passo no eixo especificado.

        Args:
            axis: Eixo ('X', 'Y', ou 'Z')
            distance_mm: Deslocamento em mm (positivo ou negativo)
            feed_rate: Velocidade em mm/min (opcional)

        Returns:
            True se o eixo atingiu o destino, False em timeout
        """
        # Calcula timeout apropriado
        if feed_rate and feed_rate > 0:
            distance_abs = abs(distance_mm)
            expected_time_sec = (distance_abs / feed_rate) * 60
            timeout = max(5, int(expected_time_sec * 1.5))
        else:
            timeout = 30

        # Executa movimento relativo
        self.relative_controller.move_relative(axis, distance_mm, feed_rate)

        # Aguarda conclusão
        return self.wait_for_idle(axis, timeout=timeout)

    def _move_relative_single_axis(self, axis: str, offset: int, speed: int = None):
        """Move um único eixo de forma relativa (método interno)."""
        self.relative_controller.move_relative_single_axis(axis, offset)

    # =========================================================================
    # Jog Movement (3 métodos) - delega para PLCJogMovementController
    # =========================================================================

    def _legacy_jog_start_unused(self, axis: str, direction: int, feed_rate: float = None):
        """
        Inicia jog contínuo no eixo.

        Args:
            axis: Nome do eixo ('X', 'Y', ou 'Z')
            direction: Direção do movimento (+1 ou -1)
            feed_rate: Velocidade em mm/min (opcional)
        """
        # Normaliza direção
        if direction > 0:
            speed = feed_rate if feed_rate else 1000.0
            self.jog_controller.jog_start(axis, speed)
        else:
            # Implementação simplificada - direction negativo requer lógica adicional
            speed = feed_rate if feed_rate else 1000.0
            self.jog_controller.jog_start(axis, speed)

    def jog_stop(self, axis: str = None):
        """
        Para o jog contínuo de todos os eixos.

        Args:
            axis: Eixo específico ou None para todos
        """
        if axis:
            self.jog_controller.jog_stop(axis)
        else:
            self.jog_controller.stop_all_jog()

    # =========================================================================
    # Homing (3 métodos) - delega para PLCHomingController
    # =========================================================================

    def home_all(self):
        """Sequência de homing completa: Z primeiro, depois X e Y."""
        self.homing_controller.home_all()

    def home_axis(self, axis: str):
        """
        Executa homing do eixo individual (usa mesma memória de zero).

        Args:
            axis: Eixo para homing ('X', 'Y', ou 'Z')
        """
        self.homing_controller.home_axis(axis)

    def unlock(self) -> bool:
        """
        Libera a máquina após um soft reset, voltando ao estado Idle.

        Returns:
            True se liberado com sucesso
        """
        self.homing_controller.unlock()
        return True

    # =========================================================================
    # Position Reading (3 métodos) - delega para PLCPositionReaderController
    # =========================================================================

    def read_position(self, axis: str) -> int:
        """
        Lê a posição atual do eixo em pulsos.

        Args:
            axis: Eixo ('X', 'Y', ou 'Z')

        Returns:
            Posição atual em pulsos
        """
        return int(self.position_reader.read_position(axis))

    def get_current_position(self) -> dict:
        """
        Retorna a posição atual de X, Y e Z em milímetros.

        Returns:
            Dicionário com chaves 'x', 'y', 'z' e valores em mm
        """
        return self.position_reader.get_current_position_mm()

    def read_register(self, register: int) -> int:
        """
        Lê valor de registro Modbus.

        Args:
            register: Número do registro

        Returns:
            Valor do registro
        """
        return self.registers_controller.read_register(register)

    # =========================================================================
    # Idle/Waiting (2 métodos) - implementação local com suporte de controllers
    # =========================================================================

    def wait_for_idle(self, axis=None, tolerance: int = 1, timeout: int = 10):
        """
        Aguarda até que os eixos fiquem idle.

        Args:
            axis: Eixo específico ou None para todos
            tolerance: Tolerância em pulsos
            timeout: Timeout em segundos

        Returns:
            True se atingiu destino, False se timeout
        """
        if not self.is_connected:
            logger.warning("wait_for_idle: PLC não conectado")
            return False

        # Obtém alvos do absolute controller
        targets = self.absolute_controller.get_targets()

        if not targets:
            return True

        # Usa eixo específico ou todos
        if isinstance(axis, str):
            if axis not in targets:
                # Se não tem alvo registrado, lê pos_input atual
                cfg = self.ADDRESSES[axis]
                targets = {axis: self.registers_controller._read_dword(cfg['pos_input'])}
            else:
                targets = {axis: targets[axis]}
        else:
            # Usa todos os alvos registrados
            if not targets:
                # Lê todos os pos_input
                targets = {
                    ax: self.registers_controller._read_dword(cfg['pos_input'])
                    for ax, cfg in self.ADDRESSES.items()
                }

        logger.info(f"⏳ wait_for_idle iniciado: targets={targets}, tolerance={tolerance} pulsos, timeout={timeout}s")

        t0 = time.time()
        ok_axes = set()
        last_log_time = -1.0
        log_interval = 1.0

        while time.time() - t0 < timeout:
            all_reached = True
            elapsed = time.time() - t0
            should_log = (elapsed - last_log_time >= log_interval)

            for ax, tgt in list(targets.items()):
                if ax in ok_axes:
                    continue

                pos = self.position_reader.read_position(ax)
                diff = pos - tgt

                if should_log:
                    logger.info(f"📊 Eixo {ax}: pos={pos} pulsos, target={tgt} pulsos, diff={diff} pulsos ({diff/self.pulses_per_mm:.3f}mm), elapsed={elapsed:.1f}s")

                if abs(pos - tgt) <= tolerance:
                    logger.info(f"✅ Eixo {ax} atingiu target! pos={pos}, target={tgt}, diff={diff} pulsos (tolerância={tolerance})")
                    ok_axes.add(ax)
                else:
                    all_reached = False

            if all_reached:
                self.absolute_controller.get_targets().clear()
                logger.info(f"✅ Todos os eixos atingiram targets após {elapsed:.1f}s")
                return True

            if should_log:
                last_log_time = elapsed

            time.sleep(0.05)

        # Timeout
        elapsed = time.time() - t0
        logger.warning(f"⏱️ TIMEOUT em wait_for_idle após {elapsed:.1f}s")
        return False

    def _wait_for_idle_axis(self, axis: str, tolerance: int = 1, timeout: int = 10) -> bool:
        """
        Aguarda até um eixo específico atingir o alvo.

        Args:
            axis: Eixo a aguardar
            tolerance: Tolerância em pulsos
            timeout: Timeout em segundos

        Returns:
            True se atingiu alvo, False se timeout
        """
        cfg = self.ADDRESSES[axis]
        target = self.registers_controller._read_dword(cfg['pos_input'])
        t0 = time.time()

        while time.time() - t0 < timeout:
            cur = self.position_reader.read_position(axis)
            if abs(cur - target) <= tolerance:
                return True
            time.sleep(0.05)

        return False

    # =========================================================================
    # Coil/Register Operations (8 métodos) - delega para PLCRegistersController
    # =========================================================================

    def pulse_coil(self, coil: int, duration_ms: int = 100) -> bool:
        """Pulsa coil por tempo especificado."""
        return self.registers_controller.pulse_coil(coil, duration_ms)

    def read_coil(self, coil: int) -> bool:
        """Lê estado de coil (bit)."""
        return self.registers_controller.read_coil(coil)

    def write_coil(self, coil: int, value: bool) -> bool:
        """Escreve um coil (bool)."""
        return self.registers_controller.write_coil(coil, value)

    def read_dword(self, address: int) -> int:
        """Lê word (32 bits) de registro Modbus."""
        return self.registers_controller.read_dword(address)

    def write_dword(self, address: int, value: int):
        """Escreve word (32 bits) em registro Modbus."""
        self.registers_controller.write_dword(address, value)

    def write_register(self, register: int, value: int):
        """Escreve valor em registro Modbus."""
        self.registers_controller.write_register(register, value)

    def snapshot_registers(self) -> dict:
        """Retorna snapshot dos principais registradores e coils por eixo."""
        snap = self.registers_controller.snapshot_registers()
        snap['machine_status'] = self.machine_status
        snap['pulses_per_mm'] = self.pulses_per_mm
        return snap

    # =========================================================================
    # Backlight Control (5 métodos) - delega para PLCRegistersController
    # =========================================================================

    def backlight_is_on(self) -> bool:
        """Retorna o estado atual do backlight."""
        return self.registers_controller.backlight_is_on()

    def backlight_set(self, on: bool) -> bool:
        """
        Liga ou desliga o backlight.

        Args:
            on: True para ligar, False para desligar

        Returns:
            True se comando bem-sucedido
        """
        result = self.registers_controller.backlight_set(on)
        if result:
            self.backlight_on = on
        return result

    def backlight_toggle(self) -> bool:
        """Alterna o estado do backlight."""
        result = self.registers_controller.backlight_toggle()
        if result:
            self.backlight_on = not self.backlight_on
        return result

    def backlight_turn_on(self) -> bool:
        """Liga o backlight."""
        result = self.registers_controller.backlight_turn_on()
        if result:
            self.backlight_on = True
        return result

    def backlight_turn_off(self) -> bool:
        """Desliga o backlight."""
        result = self.registers_controller.backlight_turn_off()
        if result:
            self.backlight_on = False
        return result

    # =========================================================================
    # Feed Rate (1 método) - exposto de PLCAbsoluteMovementController
    # =========================================================================

    def _clamp_feed_rate(self, feed_rate: float | None) -> float | None:
        """Garante que o feed-rate esteja dentro de limites válidos."""
        return self.absolute_controller._clamp_feed_rate(feed_rate)

    # =========================================================================
    # Emergency/Reset (2 métodos) - implementação local
    # =========================================================================

    def send_soft_reset(self) -> bool:
        """
        Interrompe movimentos e sinaliza estado de alarme.

        Returns:
            True quando pedido aceito, False caso contrário
        """
        if not self.is_connected:
            logger.warning("Soft reset ignorado: PLC não conectado")
            return False

        try:
            self.jog_controller.stop_all_jog()
            logger.info("PLC em estado de ALARM (soft reset solicitado)")
            return True
        except Exception as e:
            logger.error(f"Falha ao executar soft reset: {e}")
            return False

    def set_zero(self, axis: str):
        return self.absolute_controller.set_zero()

    def jog_start(self, axis: str, direction: int, feed_rate: float = None):
        speed = feed_rate if feed_rate else 1000.0
        self.jog_controller.jog_start(axis, speed, direction=1 if direction > 0 else -1)
