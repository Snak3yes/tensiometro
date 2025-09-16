# plc_axis_controller.py
"""
Módulo independente para controle de eixos X, Y e Z via CLP (Modbus TCP).
Fornece movimentos absolutos, relativos, jog e homing para cada eixo.
"""
import time
from pymodbus.client import ModbusTcpClient

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
    ADDRESSES = {
        'X': {
            'zero':           1000,    # M1000_X
            'move_abs':       1050,    # M1050_X
            'pos_input':      1100,    # D1100_X
            'speed':          21000,   # D21000_X
            'jog_plus':       1070,    # M1070_X
            'jog_minus':      1080,    # M1080_X
            'jog_stop_plus':  1010,    # M1010_X
            'jog_stop_minus': 1011,    # M1011_X
            'pos_reg':        3000     # D3000_X
        },
        'Y': {
            'zero':           500,     # M500_Y1
            'move_abs':       550,     # M550_Y1
            'pos_input':      600,     # D600_Y1
            'speed':          20500,   # D20500_Y1
            'jog_plus':       570,     # M570_Y1
            'jog_minus':      580,     # M580_Y1
            'jog_stop_plus':  510,     # M510_Y1
            'jog_stop_minus': 511,     # M511_Y1
            'pos_reg':        3400     # D3400_Y1
        },
        'Z': {
            'zero':           1500,    # M1500_Z
            'move_abs':       1550,    # M1550_Z
            'pos_input':      1600,    # D1600_Z
            'speed':          21500,   # D21500_Z
            'jog_plus':       1570,    # M1570_Z
            'jog_minus':      1580,    # M1580_Z
            'jog_stop_plus':  1510,    # M1510_Z
            'jog_stop_minus': 1511,    # M1511_Z
            'pos_reg':        3200     # D3200_Z
        }
    }

    def __init__(self, host: str='192.168.1.5', port: int=502):
        """Conecta ao CLP via Modbus TCP."""
        self.client = ModbusTcpClient(host, port=port)
        if not self.client.connect():
            raise ConnectionError(f"Falha ao conectar ao CLP em {host}:{port}")

    def close(self):
        """Fecha a conexão Modbus."""
        self.client.close()

    def _write_dword(self, address: int, value: int):
        """
        Escreve valor INT32 (little-endian) em dois registradores
        de retenção (holding registers).
        """
        u32 = value & 0xFFFFFFFF
        lo = u32 & 0xFFFF
        hi = (u32 >> 16) & 0xFFFF
        return self.client.write_registers(address, [lo, hi])

    def _read_dword(self, address: int) -> int:
        """
        Lê INT32 assinado de dois registradores de retenção.
        """
        res = self.client.read_holding_registers(address, count=2)
        if res.isError():
            raise IOError(f"Falha na leitura DWORD em {address}")
        lo, hi = res.registers
        u32 = (hi << 16) | lo
        return u32 if u32 < 0x80000000 else u32 - 0x100000000

    def _pulse_coil(self, coil: int, duration_ms: int=20):
        """
        Aciona um coil por `duration_ms` milissegundos (borda de subida).
        """
        self.client.write_coil(coil, True)
        time.sleep(duration_ms/1000.0)
        self.client.write_coil(coil, False)

    def set_zero(self, axis: str):
        """Zera a posição atual do eixo (memória de zero)."""
        mem = self.ADDRESSES[axis]['zero']
        self._pulse_coil(mem)

    def move_absolute(self, axis: str, position: int, speed: int=None):
        """
        Move o eixo `axis` para posição absoluta (pulsos).
        Se `speed` for fornecido, grava no registrador de velocidade.
        """
        cfg = self.ADDRESSES[axis]
        self._write_dword(cfg['pos_input'], int(position))
        if speed is not None:
            self._write_dword(cfg['speed'], int(speed))
        self._pulse_coil(cfg['move_abs'])

    def move_relative(self, axis: str, offset: int, speed: int=None):
        """
        Move o eixo `axis` de forma relativa ao valor atual.
        """
        current = self._read_dword(self.ADDRESSES[axis]['pos_reg'])
        self.move_absolute(axis, current + offset, speed)

    def wait_for_idle(self, axis: str, tolerance: int=1, timeout: int=10) -> bool:
        """
        Aguarda até o eixo atingir o alvo ±`tolerance` pulsos,
        retornando True se dentro de `timeout` segundos.
        """
        target = self._read_dword(self.ADDRESSES[axis]['pos_input'])
        t0 = time.time()
        while time.time() - t0 < timeout:
            cur = self._read_dword(self.ADDRESSES[axis]['pos_reg'])
            if abs(cur - target) <= tolerance:
                return True
            time.sleep(0.05)
        return False

    def jog_start(self, axis: str, direction: int, speed: int=None):
        """
        Inicia jog contínuo no eixo: `direction` = +1 ou -1.
        Se `speed` for dado, atualiza registrador de velocidade.
        """
        cfg = self.ADDRESSES[axis]
        if speed is not None:
            self._write_dword(cfg['speed'], int(speed))
        coil = cfg['jog_plus'] if direction > 0 else cfg['jog_minus']
        self.client.write_coil(coil, True)

    def jog_stop(self, axis: str):
        """Para o jog contínuo do eixo."""
        cfg = self.ADDRESSES[axis]
        self.client.write_coil(cfg['jog_plus'], False)
        self.client.write_coil(cfg['jog_minus'], False)

    def read_position(self, axis: str) -> int:
        """Lê a posição atual do eixo em pulsos."""
        return self._read_dword(self.ADDRESSES[axis]['pos_reg'])

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
