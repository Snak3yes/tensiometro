"""
Serial Protocol Handler for AS-120N Tensiometer
Created: 2026-01-14 (Phase 1 - SOLID Refactoring)
"""

import serial
import serial.tools.list_ports
import logging
import time
from typing import Optional, List
from .models import TensiometerConfig, TensionUnit

logger = logging.getLogger(__name__)


class TensiometerSerialManager:
    """Gerencia conexao serial para o tensiometro AS-120N."""
    
    REQ_COMMAND = b' '
    FRAME_LEN = 9
    DEFAULT_BAUDRATE = 2400
    
    UNIT_MAP = {
        0x05: TensionUnit.N_CM2,
        0x04: TensionUnit.KG_CM2,
        0x06: TensionUnit.LB_CM2
    }
    
    def __init__(self, config: Optional[TensiometerConfig] = None):
        self.serial_connection: Optional[serial.Serial] = None
        self.is_connected = False
        self.port: Optional[str] = None
        self.baudrate = self.DEFAULT_BAUDRATE
        self.timeout = 1.0
        self.last_error = ""
        self.config = config or TensiometerConfig()
    
    def _real_dig(self, b: int) -> int:
        return ((b & 0x0F) + 10) % 10
    
    def _decode_frame(self, frame: bytes) -> Optional[float]:
        if len(frame) < self.FRAME_LEN:
            return None
        if frame[0] != 0x10 or frame[2] != 0x19:
            return None
        
        param_byte = frame[3]
        casas = (param_byte >> 4) & 0x07
        d3 = self._real_dig(frame[6])
        d2 = self._real_dig(frame[7])
        d1 = self._real_dig(frame[8])
        raw_value = d3 * 100 + d2 * 10 + d1
        return raw_value / (10 ** casas)
    
    def get_available_ports(self) -> List[str]:
        try:
            ports = [port.device for port in serial.tools.list_ports.comports()]
            return ports
        except Exception as e:
            logger.error(f"Erro ao listar portas: {e}")
            return []
    
    def connect(self, port: str, baudrate: int = DEFAULT_BAUDRATE, timeout: float = 1.0) -> bool:
        try:
            if self.is_connected:
                self.disconnect()
            
            self.serial_connection = serial.Serial(
                port=port, baudrate=baudrate,
                bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE, timeout=timeout
            )
            self.serial_connection.dtr = False
            self.serial_connection.rts = False
            
            self.port = port
            self.baudrate = baudrate
            self.timeout = timeout
            self.is_connected = True
            self.last_error = ""
            logger.info(f"Tensiometro conectado em {port} @ {baudrate} baud")
            return True
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Erro ao conectar: {e}")
            return False
    
    def disconnect(self) -> None:
        try:
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.close()
        except Exception as e:
            logger.error(f"Erro ao desconectar: {e}")
        finally:
            self.serial_connection = None
            self.is_connected = False
            self.port = None
    
    def read_tension_value(self) -> str:
        if not self.is_connected or not self.serial_connection:
            self.last_error = "Nao conectado"
            return "0"
        
        try:
            self.serial_connection.reset_input_buffer()
            self.serial_connection.write(self.REQ_COMMAND)
            self.serial_connection.flush()
            time.sleep(0.05)
            
            raw_data = self.serial_connection.read(self.FRAME_LEN)
            
            if not raw_data or len(raw_data) != self.FRAME_LEN:
                self.last_error = "Frame incompleto"
                return "0"
            
            value = self._decode_frame(raw_data)
            if value is None:
                self.last_error = "Frame invalido"
                return "0"
            
            return f"{value:.2f}"
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Erro na leitura: {e}")
            return "0"
    
