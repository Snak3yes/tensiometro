"""
PLC Registers Controller - Operações de registradores Modbus

Implementa IPLCRegisterOperations e encapsula lógica de registradores.
"""

import logging
import time
from typing import Dict


logger = logging.getLogger(__name__)


class PLCRegistersController:
    """
    Controller para operações de registradores do PLC.

    Implementa leitura e escrita de coils e registradores Modbus.
    """

    # Mapeamento de endereços para monitoramento
    ADDRESSES = {
        'X': {
            'zero': 1000,
            'move_abs': 1050,
            'pos_input': 1100,
            'speed': 21000,
            'pos_reg': 3000,
            'jog_plus': 1070,
            'jog_minus': 1080,
            'jog_stop_plus': 1010,
            'jog_stop_minus': 1011
        },
        'Y': {
            'zero': 500,
            'move_abs': 1050,
            'pos_input': 600,
            'speed': 20500,
            'pos_reg': 3200,
            'jog_plus': 570,
            'jog_minus': 580,
            'jog_stop_plus': 510,
            'jog_stop_minus': 511
        },
        'Z': {
            'zero': 1500,
            'move_abs': 1600,
            'pos_input': 1600,
            'speed': 21500,
            'pos_reg': 3400,
            'jog_plus': 1570,
            'jog_minus': 1580,
            'jog_stop_plus': 1510,
            'jog_stop_minus': 1511
        }
    }

    def __init__(self, connection_manager, position_reader, pulses_per_mm: float = 1.0):
        """
        Inicializa o controller de registradores.

        Args:
            connection_manager: Instância de PLCConnectionManager
            position_reader: Instância de PLCPositionReaderController
            pulses_per_mm: Fator de conversão pulsos → mm (padrão: 1.0)
        """
        self.connection_manager = connection_manager
        self.position_reader = position_reader
        self.pulses_per_mm = pulses_per_mm

        # Estado do backlight
        self.backlight_on = False
        self.backlight_coil_address = 1  # Y0.7

        logger.debug(f"PLCRegistersController criado: pulses_per_mm={pulses_per_mm}")

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

    def pulse_coil(self, coil_address: int, pulse_time_ms: int = 100) -> bool:
        """
        Pulsa coil digital por tempo especificado.

        Args:
            coil_address: Endereço da coil
            pulse_time_ms: Tempo do pulso em milissegundos (padrão: 100)

        Returns:
            True se pulso bem-sucedido, False caso contrário
        """
        if not self.connection_manager.is_connected():
            raise IOError("PLC não conectado")

        try:
            client = self.connection_manager.client
            client.write_coil(coil_address, True)
            time.sleep(pulse_time_ms / 1000.0)
            client.write_coil(coil_address, False)
            return True
        except Exception as e:
            logger.error(f"Erro ao pulsar coil {coil_address}: {e}")
            return False

    def read_coil(self, coil_address: int) -> bool:
        """
        Lê estado de coil digital.

        Args:
            coil_address: Endereço da coil

        Returns:
            True se coil ativo, False se inativo
        """
        if not self.connection_manager.is_connected():
            raise IOError("PLC não conectado")

        client = self.connection_manager.client
        res = client.read_coils(coil_address, count=1)
        if res.isError():
            raise IOError(f"Falha na leitura do coil {coil_address}: {res}")
        return bool(res.bits[0])

    def write_coil(self, coil_address: int, value: bool) -> bool:
        """
        Escreve valor em coil digital.

        Args:
            coil_address: Endereço da coil
            value: Valor a escrever (True/False)

        Returns:
            True se escrita bem-sucedida, False caso contrário
        """
        if not self.connection_manager.is_connected():
            raise IOError("PLC não conectado")

        client = self.connection_manager.client
        res = client.write_coil(coil_address, bool(value))
        if res.isError():
            raise IOError(f"Falha na escrita do coil {coil_address}: {res}")
        return True

    def write_dword(self, register: int, value: int) -> bool:
        """
        Escreve word (32 bits) em registro Modbus.

        Args:
            register: Número do registro
            value: Valor de 32 bits

        Returns:
            True se escrita bem-sucedida, False caso contrário
        """
        if not self.connection_manager.is_connected():
            raise IOError("PLC não conectado")

        try:
            self._write_dword(register, value)
            return True
        except Exception as e:
            logger.error(f"Erro ao escrever dword no registro {register}: {e}")
            return False

    def read_dword(self, register: int) -> int:
        """
        Lê word (32 bits) de registro Modbus.

        Args:
            register: Número do registro

        Returns:
            Valor de 32 bits
        """
        if not self.connection_manager.is_connected():
            raise IOError("PLC não conectado")

        return self._read_dword(register)

    def write_register(self, register: int, value: int) -> bool:
        """
        Escreve valor em registro Modbus.

        Args:
            register: Número do registro
            value: Valor a ser escrito

        Returns:
            True se escrita bem-sucedida, False caso contrário
        """
        return self.write_dword(register, value)

    def read_register(self, register: int) -> int:
        """
        Lê valor de registro Modbus.

        Args:
            register: Número do registro

        Returns:
            Valor do registro
        """
        return self.read_dword(register)

    def snapshot_registers(self) -> dict:
        """
        Cria snapshot de todos os registradores críticos.

        Returns:
            Dicionário com valores dos registradores
        """
        if not self.connection_manager.is_connected():
            raise IOError("PLC não conectado")

        snap = {
            "pulses_per_mm": self.pulses_per_mm,
            "backlight_on": self.backlight_on,
            "axes": {}
        }

        for axis, cfg in self.ADDRESSES.items():
            axis_data = {}

            # Registradores
            try:
                axis_data["pos_input"] = self._read_dword(cfg["pos_input"])
            except:
                axis_data["pos_input"] = 0

            try:
                axis_data["pos_reg"] = self._read_dword(cfg["pos_reg"])
            except:
                axis_data["pos_reg"] = 0

            try:
                axis_data["speed"] = self._read_dword(cfg["speed"])
            except:
                axis_data["speed"] = 0

            # Coils
            try:
                axis_data["zero"] = self.read_coil(cfg["zero"])
            except:
                axis_data["zero"] = False

            try:
                axis_data["move_abs"] = self.read_coil(cfg["move_abs"])
            except:
                axis_data["move_abs"] = False

            try:
                axis_data["jog_plus"] = self.read_coil(cfg["jog_plus"])
            except:
                axis_data["jog_plus"] = False

            try:
                axis_data["jog_minus"] = self.read_coil(cfg["jog_minus"])
            except:
                axis_data["jog_minus"] = False

            snap["axes"][axis] = axis_data

        return snap

    # =========================================================================
    # CONTROLE DE ILUMINAÇÃO (BACKLIGHT)
    # =========================================================================

    def backlight_set(self, on: bool) -> bool:
        """
        Liga ou desliga o backlight (iluminação inferior).

        Args:
            on: True para ligar, False para desligar

        Returns:
            True se o comando foi executado com sucesso
        """
        if not self.connection_manager.is_connected():
            logger.warning("PLC não conectado - não é possível controlar backlight")
            return False

        try:
            client = self.connection_manager.client
            result = client.write_coil(self.backlight_coil_address, on)

            if result.isError():
                logger.error(f"Erro ao {'ligar' if on else 'desligar'} backlight: {result}")
                return False

            self.backlight_on = on
            logger.info(f"Backlight {'LIGADO' if on else 'DESLIGADO'} (Y0.7)")
            return True

        except Exception as e:
            logger.error(f"Exceção ao controlar backlight: {e}")
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


# Import correto para a interface
from aoi_lib.plc.interfaces.plc_register_interface import IPLCRegisterOperations
IPLCRegisterOperations.register(PLCRegistersController)
