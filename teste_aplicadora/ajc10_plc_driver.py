#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
1) Configura parâmetros da AJC-10 via RS-232 (COM-local)
2) Dispara o CLP Delta (Ethernet) para enviar 24 V a IN1
Autor: você – 2025-06-05
"""

import struct, time, sys, threading
from typing import Optional

# ---------- RS-232 (AJP-10) -----------------------------------------
import serial

AJC_PORT   = "COM23"
AJC_BAUD   = 115_200
SER_CFG    = dict(bytesize=serial.EIGHTBITS,
                  parity=serial.PARITY_NONE,
                  stopbits=serial.STOPBITS_ONE,
                  timeout=1)

def crc16(data: bytes) -> bytes:
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = ((crc >> 1) ^ 0xA001) if (crc & 1) else crc >> 1
    return struct.pack('<H', crc)

def fc06(addr: int, val: int) -> bytes:
    p = struct.pack('>B B H H', 1, 6, addr, val)
    return p + crc16(p)

def send_ajc(frame: bytes) -> bytes:
    with serial.Serial(AJC_PORT, AJC_BAUD, **SER_CFG) as s:
        s.reset_input_buffer()
        s.write(frame); s.flush()
        time.sleep(0.05)
        return s.read(256)

# ----------- Modbus-TCP (PLC) ---------------------------------------
from pyModbusTCP.client import ModbusClient

PLC_IP   = "192.168.0.10"
PLC_PORT = 502
Y0_ADDR  = 20480          # coil Y0

plc = ModbusClient(host=PLC_IP, port=PLC_PORT, unit_id=1, auto_open=True,
                   auto_close=True, timeout=1)

def plc_pulse_ms(addr: int, width_ms: int = 30):
    """Liga bobina, espera, desliga."""
    if not plc.write_single_coil(addr, True):
        print("Erro ao ligar bobina")
        return
    time.sleep(width_ms/1000.0)
    plc.write_single_coil(addr, False)

# ----------- Demonstração -------------------------------------------
def main():
    # 1) Colocar SHOOT MODE = INFINITE (exemplo)
    print("Configurando AJC-10 …")
    tx = fc06(0x0040, 1)
    rx = send_ajc(tx)
    print("TX:", tx.hex(' '), "\nRX:", rx.hex(' '))
    
    # 2) Ajustar OPEN/CLOSE TIME (4 ms)
    send_ajc(fc06(0x0043, 40))   # 40 *0,1 ms = 4,0 ms
    send_ajc(fc06(0x0044, 40))
    
    # 3) Disparar dois shots via CLP
    print("Pulso 1")
    plc_pulse_ms(Y0_ADDR, 30)
    time.sleep(0.3)
    print("Pulso 2")
    plc_pulse_ms(Y0_ADDR, 30)

if __name__ == "__main__":
    main()
