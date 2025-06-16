#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AJC-10 – GUI de Configuração (PyQt6)
Permite ler/editar parâmetros via Modbus-RTU (RS-232 ±12 V)
115 200 baud  8 N 1   ID-escravo = 1
"""
from __future__ import annotations
import sys, struct, time, threading
from typing import List, Tuple, Any, Optional

import serial, serial.tools.list_ports
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QComboBox, QPushButton, QTableWidget,
                             QTableWidgetItem, QTextEdit, QMessageBox,
                             QHeaderView, QSpinBox)
from PyQt6.QtCore import Qt

# ───────────────────────────  dados fixos ────────────────────────────
BAUD      = 115_200
SLAVE_ID  = 1
SER_CFG   = dict(bytesize=serial.EIGHTBITS,
                 parity=serial.PARITY_NONE,
                 stopbits=serial.STOPBITS_ONE,
                 timeout=1.0)

# endereço, nome, escala(p/ mostrar), unidade, writable?
REGMAP: List[Tuple[int, str, float, str, bool]] = [
    (0x0040, "SHOOT MODE"     , 1   , ""     , True ),
    (0x0043, "OPEN TIME"      , 0.1 , "ms"   , True ),
    (0x0044, "CLOSE TIME"     , 0.1 , "ms"   , True ),
    (0x0045, "SHOOT NUMBER HI", 1   , ""     , True ),   # parte alta
    (0x0046, "SHOOT NUMBER LO", 1   , ""     , True ),   # parte baixa
    (0x0047, "SET TEMP"       , 0.1 , "°C"   , True ),
    (0x0048, "ACTUAL TEMP"    , 0.1 , "°C"   , False),
    (0x0049, "SUPPLY PRESS"   , 0.1 , "kPa"  , False),
    (0x004A, "VALVE PRESS"    , 0.1 , "kPa"  , False),
]

# ───────────────────────────  CRC-16 Modbus ──────────────────────────
def crc16(data: bytes) -> bytes:
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return struct.pack('<H', crc)           # low-hi

# ──────────────────────────  Telegramas Modbus ───────────────────────
def frame_fc03(addr: int, qty: int) -> bytes:
    p = struct.pack('>B B H H', SLAVE_ID, 3, addr, qty)
    return p + crc16(p)

def frame_fc06(addr: int, value: int) -> bytes:
    p = struct.pack('>B B H H', SLAVE_ID, 6, addr, value)
    return p + crc16(p)

def frame_fc10(addr: int, values: List[int]) -> bytes:
    qty = len(values)
    header = struct.pack('>B B H H B', SLAVE_ID, 16, addr, qty, qty*2)
    body   = b''.join(struct.pack('>H', v) for v in values)
    p = header + body
    return p + crc16(p)

# ────────────────────────────  GUI principal ────────────────────────
class Ajc10Gui(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AJC-10  Config Tool")
        self.ser: Optional[serial.Serial] = None
        self._build_ui()

    # -------------------  UI  ----------------------------------------
    def _build_ui(self):
        lay = QVBoxLayout(self)
        # linha de conexão
        h = QHBoxLayout()
        self.cmb_port = QComboBox()
        self._refresh_ports()
        self.btn_conn = QPushButton("Conectar")
        self.btn_conn.clicked.connect(self._toggle_conn)
        h.addWidget(QLabel("Porta:"))
        h.addWidget(self.cmb_port)
        h.addWidget(self.btn_conn)
        lay.addLayout(h)

        # tabela de registos
        self.tbl = QTableWidget(len(REGMAP), 5)
        self.tbl.setHorizontalHeaderLabels(
            ["End.", "Nome", "Valor", "Unid.", "R/W"])
        self.tbl.horizontalHeader().setSectionResizeMode(
        1, QHeaderView.ResizeMode.Stretch)
        self.tbl.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked)
        for row, (addr, name, scale, unit, w) in enumerate(REGMAP):
            self.tbl.setItem(row, 0, QTableWidgetItem(f"0x{addr:04X}"))
            self.tbl.setItem(row, 1, QTableWidgetItem(name))
            self.tbl.setItem(row, 3, QTableWidgetItem(unit))
            self.tbl.setItem(row, 4, QTableWidgetItem("W" if w else "R"))
            self.tbl.item(row, 0).setFlags(Qt.ItemFlag.ItemIsSelectable |
                                           Qt.ItemFlag.ItemIsEnabled)
            self.tbl.item(row, 1).setFlags(Qt.ItemFlag.ItemIsSelectable |
                                           Qt.ItemFlag.ItemIsEnabled)
            self.tbl.item(row, 3).setFlags(Qt.ItemFlag.ItemIsSelectable |
                                           Qt.ItemFlag.ItemIsEnabled)
            self.tbl.item(row, 4).setFlags(Qt.ItemFlag.ItemIsSelectable |
                                           Qt.ItemFlag.ItemIsEnabled)
        lay.addWidget(self.tbl)

        # botões de operação
        h2 = QHBoxLayout()
        self.btn_read  = QPushButton("Ler Tudo")
        self.btn_write = QPushButton("Gravar Selecionado(s)")
        self.btn_mode  = QPushButton("Mudar SHOOT MODE")
        self.btn_read.clicked.connect(self._read_all)
        self.btn_write.clicked.connect(self._write_sel)
        self.btn_mode.clicked.connect(self._change_mode_popup)
        for b in (self.btn_read, self.btn_write, self.btn_mode):
            b.setEnabled(False)
        h2.addWidget(self.btn_read);  h2.addWidget(self.btn_write); h2.addWidget(self.btn_mode)
        lay.addLayout(h2)

        # log
        self.log = QTextEdit(readOnly=True)
        lay.addWidget(self.log)

    # -------------------  conexão serial  ----------------------------
    def _refresh_ports(self):
        self.cmb_port.clear()
        for p in serial.tools.list_ports.comports():
            self.cmb_port.addItem(p.device)

    def _toggle_conn(self):
        if self.ser and self.ser.is_open:
            self.ser.close(); self.ser = None
            self._set_conn_state(False); return
        port = self.cmb_port.currentText()
        try:
            self.ser = serial.Serial(port, BAUD, **SER_CFG)
        except serial.SerialException as e:
            QMessageBox.critical(self, "Erro", str(e)); return
        self._set_conn_state(True)

    def _set_conn_state(self, ok: bool):
        self.cmb_port.setEnabled(not ok)
        self.btn_conn.setText("Desconectar" if ok else "Conectar")
        for b in (self.btn_read, self.btn_write, self.btn_mode):
            b.setEnabled(ok)
        self._log(">>> " + ("Conectado" if ok else "Desconectado"))

    # -------------------  leitura completa  --------------------------
    def _read_all(self):
        threading.Thread(target=self._read_all_thr, daemon=True).start()

    def _read_all_thr(self):
        # Leio bloco contínuo do 1.º ao último endereço usado
        start   = REGMAP[0][0]
        end     = REGMAP[-1][0]
        qty     = end - start + 1
        tx      = frame_fc03(start, qty)
        rx      = self._txrx(tx)
        if not rx: return
        if rx[1] & 0x80:
            self._log("Leitura: exceção 0x%02X" % rx[2]); return
        byte_cnt = rx[2]
        data = rx[3:3+byte_cnt]
        vals = list(struct.unpack(f'>{qty}H', data))
        for row, (addr, _, scale, _, _) in enumerate(REGMAP):
            raw = vals[addr-start]
            val = raw * scale
            item = QTableWidgetItem(f"{val:g}")
            self.tbl.setItem(row, 2, item)

    # -------------------  escrita dos seleccionados ------------------
    def _write_sel(self):
        rows = {idx.row() for idx in self.tbl.selectedIndexes()}
        if not rows:
            QMessageBox.information(self, "Info", "Selecione ao menos um campo editável.")
            return
        for row in rows:
            addr, _, scale, _, writable = REGMAP[row]
            if not writable: continue
            txt_item = self.tbl.item(row, 2)
            if not txt_item: continue
            try:
                fval = float(txt_item.text())
                raw  = int(round(fval / scale))
            except ValueError:
                self._log(f"Linha {row}: valor inválido.")
                continue
            tx = frame_fc06(addr, raw)
            rx = self._txrx(tx)
            if rx and not (rx[1] & 0x80):
                self._log(f"Gravado 0x{addr:04X} = {raw}")
            else:
                self._log(f"Falha gravação 0x{addr:04X}")

    # -------------------  mudar SHOOT MODE ---------------------------
    def _change_mode_popup(self):
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Selecionar SHOOT MODE")
        dlg.setText("Escolha o modo:")
        for key, txt in enumerate(("DEFINED (0)", "INFINITE (1)", "GROUP (2)", "PURGE (3)")):
            dlg.addButton(txt, QMessageBox.ButtonRole.AcceptRole)
            dlg.buttons()[-1].setProperty("MODE", key)
        dlg.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
        ret = dlg.exec()
        btn = dlg.clickedButton()
        if btn and btn.property("MODE") is not None:
            mode = int(btn.property("MODE"))
            tx = frame_fc06(0x0040, mode)
            rx = self._txrx(tx)
            if rx and not (rx[1] & 0x80):
                self._log(f"SHOOT MODE definido para {mode}")
                # refazer leitura para atualizar tabela
                self._read_all()
            else:
                self._log("Falha ao mudar SHOOT MODE")

    # -------------------  TX/RX comum --------------------------------
    def _txrx(self, frame: bytes) -> Optional[bytes]:
        if not self.ser or not self.ser.is_open: return None
        self.ser.reset_input_buffer()
        self.ser.write(frame); self.ser.flush()
        time.sleep(0.05)
        rx = self.ser.read(256)
        self._log(f"TX: {frame.hex(' ')}")
        self._log(f"RX: {rx.hex(' ') if rx else '(timeout)'}")
        return rx

    # -------------------  logger -------------------------------------
    def _log(self, msg: str): self.log.append(msg)

# ──────────────────────────────  main  ───────────────────────────────
if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = Ajc10Gui()
    gui.resize(650, 480)
    gui.show()
    sys.exit(app.exec())
