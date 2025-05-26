#!/usr/bin/env python3
"""
le_tensio.py – lê continuamente medições do AS-120N
usando os parâmetros detectados (2400 8‑N‑1, DTR=0, RTS=0).
"""

import sys, time, serial, contextlib

PORT      = sys.argv[1] if len(sys.argv) >= 2 else "COM23"
BAUD      = 2400
BYTESIZE  = serial.EIGHTBITS
PARITY    = serial.PARITY_NONE
STOPBITS  = serial.STOPBITS_ONE
REQ       = b'\x20'
FRAME_LEN = 9    # 0x10 + 0x## + ... até o último dígito

UNIT_MAP = {0x05: "N/cm²", 0x04: "kg/cm²", 0x06: "lb/cm²"}

def _real_dig(b: int) -> int:
    """Converte nibble baixo deslocado (+0x0A) em dígito 0–9."""
    return ((b & 0x0F) + 10) % 10

def decode_frame(frame: bytes) -> float | None:
    """
    Espera um frame de 9 bytes começando com 0x10, com byte2=0x19. 
    Retorna o valor em float (N/cm²).
    """
    if len(frame) < FRAME_LEN or frame[0] != 0x10 or frame[2] != 0x19:
        return None
    casas = (frame[3] >> 4) & 0x07
    d3 = _real_dig(frame[6])
    d2 = _real_dig(frame[7])
    d1 = _real_dig(frame[8])
    raw = d3 * 100 + d2 * 10 + d1
    return raw / (10 ** casas)

def main():
    print(f"Abrindo {PORT} @ {BAUD}, 8‑N‑1, DTR=0, RTS=0")
    with contextlib.closing(serial.Serial(
            PORT, BAUD,
            bytesize=BYTESIZE, parity=PARITY, stopbits=STOPBITS,
            timeout=1, write_timeout=1)) as ser:

        # Garante DTR=0, RTS=0
        ser.dtr = False
        ser.rts = False

        try:
            while True:
                ser.reset_input_buffer()
                ser.write(REQ)
                time.sleep(0.05)
                data = ser.read(FRAME_LEN)
                if not data:
                    print("Sem resposta, re-tentando…")
                    continue

                val = decode_frame(data)
                if val is None:
                    print(f"Quadro inválido: {data.hex(' ')}")
                else:
                    print(f"{val:.2f} N/cm²")

                time.sleep(0.5)

        except KeyboardInterrupt:
            print("\nEncerrando…")

if __name__ == "__main__":
    main()
