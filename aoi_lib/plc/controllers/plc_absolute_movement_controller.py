"""
PLC Absolute Movement Controller - Movimento absoluto de eixos

Implementa IPLCAbsoluteMovement e encapsula lógica de movimento absoluto.
"""

import logging
import time
from typing import Dict, Optional
from pymodbus.client import ModbusTcpClient


logger = logging.getLogger(__name__)


class PLCAbsoluteMovementController:
    """
    Controller para movimento absoluto de eixos PLC.

    Implementa movimento para coordenadas absolutas em pulsos.
    """

    # Mapeamento de endereços para movimento absoluto
    ADDRESSES = {
        'X': {
            'zero': 1500,      # M1500 - confirmacao homing X
            'move_abs': 1050,  # M1050 - Interpolação X/Y
            'pos_input': 1100, # D1100_X
            'speed': 20500,    # D20500 - velocidade compartilhada X/Y
            'pos_reg': 3000    # D3000_X
        },
        'Y': {
            'zero': 1000,      # M1000 - confirmacao homing Y
            'move_abs': 1050,  # M1050 - Interpolação X/Y
            'pos_input': 600,  # D600_Y
            'speed': 20500,    # D20500_Y
            'pos_reg': 3200    # D3200_Y
        },
        'Z': {
            'zero': 500,       # M500 - confirmacao homing Z
            'move_abs': 1550,  # M1550_Z - inicia movimento absoluto Z
            'pos_input': 1600, # D1600_Z
            'speed': 21500,    # D21500_Z
            'pos_reg': 3400    # D3400_Z
        }
    }

    def __init__(self, connection_manager, pulses_per_mm: float = 1.0, max_feed: Optional[Dict] = None):
        """
        Inicializa o controller de movimento absoluto.

        Args:
            connection_manager: Instância de PLCConnectionManager
            pulses_per_mm: Fator de conversão pulsos → mm (padrão: 1.0)
            max_feed: Limites máximos de feed por eixo
        """
        self.connection_manager = connection_manager
        self.pulses_per_mm = pulses_per_mm
        self.max_feed = max_feed or {'x': float('inf'), 'y': float('inf'), 'z': float('inf')}
        self._targets: Dict[str, int] = {}

        logger.debug(f"PLCAbsoluteMovementController criado: pulses_per_mm={pulses_per_mm}")

    def _clamp_feed_rate(self, feed_rate: Optional[float]) -> Optional[float]:
        """
        Garante que o feed-rate esteja dentro de limites válidos.

        Args:
            feed_rate: Taxa de avanço em mm/min

        Returns:
            Feed rate validado ou None
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

    def _write_dword(self, address: int, value: int):
        """
        Escreve valor INT32 (little-endian) em dois registradores.

        Args:
            address: Endereço base do registrador
            value: Valor de 32 bits a escrever
        """
        client = self.connection_manager.client
        if not client:
            raise IOError("Cliente Modbus não inicializado")

        u32 = value & 0xFFFFFFFF
        lo = u32 & 0xFFFF
        hi = (u32 >> 16) & 0xFFFF
        return client.write_registers(address, [lo, hi])

    def _read_dword(self, address: int) -> int:
        """
        Lê INT32 assinado de dois registradores.

        Args:
            address: Endereço base do registrador

        Returns:
            Valor de 32 bits lido
        """
        client = self.connection_manager.client
        if not client:
            raise IOError("Cliente Modbus não inicializado")

        res = client.read_holding_registers(address, count=2)
        if res.isError():
            raise IOError(f"Falha na leitura DWORD em {address}")
        lo, hi = res.registers
        u32 = (hi << 16) | lo
        return u32 if u32 < 0x80000000 else u32 - 0x100000000

    def _pulse_coil(self, coil: int, duration_ms: int = 100):
        """
        Pulsa coil por duração especificada.

        Args:
            coil: Endereço do coil
            duration_ms: Duração do pulso em ms
        """
        client = self.connection_manager.client
        if not client:
            raise IOError("Cliente Modbus não inicializado")

        client.write_coil(coil, True)
        time.sleep(duration_ms / 1000.0)
        client.write_coil(coil, False)

    def apply_motion_pulses(self, targets_pulses: Dict[str, int], feed_rate: Optional[float] = None) -> bool:
        """
        Escreve alvo e velocidade para múltiplos eixos e dispara movimento.

        Args:
            targets_pulses: Dicionário {eixo: alvo em pulsos}
            feed_rate: Velocidade em mm/min

        Returns:
            True se movimento iniciado com sucesso
        """
        if not targets_pulses:
            return True

        if not self.connection_manager.is_connected():
            raise IOError("PLC não conectado")

        fr = self._clamp_feed_rate(feed_rate)
        speed_pulses = int(round(fr * self.pulses_per_mm)) if fr is not None else None

        logger.info(f"🎯 apply_motion_pulses: alvos={targets_pulses}, feed_rate={feed_rate}mm/min, speed_pulses={speed_pulses}pulsos/min")

        # Limpa alvos anteriores e registra os novos
        self._targets.clear()

        # 1) Grava alvos e velocidades
        for ax, tgt in targets_pulses.items():
            cfg = self.ADDRESSES[ax]
            logger.info(f"🎯 Eixo {ax}: escrevendo target={tgt} pulsos em pos_input (endereco {cfg['pos_input']})")
            self._write_dword(cfg['pos_input'], int(tgt))

            if speed_pulses is not None:
                logger.info(f"🎯 Eixo {ax}: escrevendo speed={speed_pulses} pulsos/min em speed (endereco {cfg['speed']})")
                self._write_dword(cfg['speed'], int(speed_pulses))

            self._targets[ax] = int(tgt)

            # Lê posição atual ANTES do movimento
            try:
                current_before = self._read_dword(cfg['pos_reg'])
                logger.info(f"🎯 Eixo {ax}: posicao atual (pos_reg) ANTES do movimento: {current_before} pulsos")
            except Exception as e:
                logger.warning(f"⚠️ Não foi possível ler posição atual antes do movimento: {e}")

        # 2) Dispara todos os eixos rapidamente
        # NOTA: X e Y usam o MESMO coil (M1050) para interpolação
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

        # Pequena pausa para deixar o PLC começar o movimento
        time.sleep(0.1)

        # Lê posição logo após iniciar movimento
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

    def move_absolute(self, axis: str, position: float, speed: float = 0.0) -> bool:
        """
        Move eixo para posição absoluta.

        Args:
            axis: Eixo a ser movido ('X', 'Y', ou 'Z')
            position: Posição absoluta em pulsos
            speed: Taxa de avanço em pulses/minuto

        Returns:
            True se movimento bem-sucedido
        """
        speed_mm = speed / self.pulses_per_mm if speed else None
        return self.apply_motion_pulses({axis: int(position)}, speed_mm)

    def move_to_absolute_position(self, x: float, y: float, z: float,
                                 speed_x: Optional[float] = None,
                                 speed_y: Optional[float] = None,
                                 speed_z: Optional[float] = None) -> bool:
        """
        Move para posição XYZ absoluta.

        Args:
            x: Posição X em pulsos
            y: Posição Y em pulsos
            z: Posição Z em pulsos
            speed_x: Velocidade X em pulsos/minuto
            speed_y: Velocidade Y em pulsos/minuto
            speed_z: Velocidade Z em pulsos/minuto

        Returns:
            True se movimento bem-sucedido
        """
        targets = {}

        if x is not None:
            targets['X'] = int(round(x))
        if y is not None:
            targets['Y'] = int(round(y))
        if z is not None:
            targets['Z'] = int(round(z))

        # Se nenhuma velocidade for informada, preserva o valor ja gravado no PLC.
        speeds = [s for s in [speed_x, speed_y, speed_z] if s is not None and s > 0]
        feed_rate = max(speeds) if speeds else None

        return self.apply_motion_pulses(targets, feed_rate)

    def _legacy_set_zero_unused(self) -> None:
        """
        Define posição atual da máquina como zero (zero absoluto).

        NOTA: Este método afeta todos os eixos.
        """
        for axis in ['X', 'Y', 'Z']:
            mem = self.ADDRESSES[axis]['zero']
            logger.info(f"🔄 Zerando eixo {axis} (coil {mem})")
            self._pulse_coil(mem)

    def set_feed_rate(self, feed_rate: float) -> None:
        """
        Configura taxa de avanço padrão.

        Args:
            feed_rate: Taxa de avanço em pulsos/minuto
        """
        # Armazena feed rate padrão para uso futuro
        self._default_feed_rate = feed_rate
        logger.debug(f"Feed rate padrão configurado: {feed_rate} pulsos/min")

    def get_targets(self) -> Dict[str, int]:
        """
        Retorna alvos ativos dos eixos.

        Returns:
            Dicionário {eixo: alvo em pulsos}
        """
        return self._targets.copy()

    def set_zero(self) -> None:
        logger.warning("set_zero() ignorado: mapa atual do PLC nao expoe comando dedicado de zero")
        return False


# Import correto para a interface
from aoi_lib.plc.interfaces.plc_absolute_movement_interface import IPLCAbsoluteMovement
IPLCAbsoluteMovement.register(PLCAbsoluteMovementController)
