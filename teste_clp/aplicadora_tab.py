import time
import serial
import serial.tools.list_ports
from typing import Callable
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QGridLayout, QLabel, QComboBox,
    QPushButton, QSpinBox, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal

# Configurações seriais e Modbus
COM_SETTINGS = dict(
    baudrate=115200, bytesize=8, parity='N',
    stopbits=1, timeout=0.5, rtscts=False, dsrdtr=False
)
MONITOR_INTERVAL_MS = 3000
AUTO_TEST_DELAY_MS  = 500

DEVICE_ID         = 0x01
FUNC_READ         = 0x03
FUNC_WRITE_SINGLE = 0x06
FUNC_WRITE_MULTI  = 0x10


class AdhesiveApplicatorTab(QWidget):
    """
    Aba de controle da aplicadora de adesivo em Modbus RTU via serial.
    main_ctrl: instância de MultiAxisMotorController (para log e settings).
    """
    # sinaliza quando a temperatura real é atualizada (°C)
    temperatureUpdated = pyqtSignal(float)
    # sinaliza quando a temperatura configurada (spin_t1) é atualizada (°C)
    configTempUpdated  = pyqtSignal(float)

    def __init__(self, main_ctrl):
        super().__init__()
        self.ctrl = main_ctrl
        self.serial_connection = None
        self._extended_controls = []
        self._build_ui()
        # 1) Preenche combo com portas e seleciona a última porta salva (se existir)
        self.refresh_ports()
        last = self.ctrl.settings.data.get('applicator_last_port')
        if last:
            idx = self.port_combo.findData(last)
            if idx >= 0:
                self.port_combo.setCurrentIndex(idx)
                # 2) Conecta automaticamente na última porta
                self.connect_serial()

    def _build_ui(self):
        self.setLayout(QVBoxLayout())
        # — Conexão Serial —
        conn_box = QGroupBox("Conexão Serial")
        g = QGridLayout(conn_box)
        self.port_combo = QComboBox(); self.port_combo.setMinimumWidth(300)
        self.btn_refresh = QPushButton("Atualizar Portas")
        self.btn_connect = QPushButton("Conectar")
        self.lbl_status = QLabel("Desconectado")
        self.lbl_status.setStyleSheet("color:red; font-weight:bold;")
        g.addWidget(QLabel("Porta:"), 0,0); g.addWidget(self.port_combo,0,1)
        g.addWidget(self.btn_refresh,0,2)
        g.addWidget(QLabel("Status:"),1,0); g.addWidget(self.lbl_status,1,1)
        g.addWidget(self.btn_connect,1,2)
        self.layout().addWidget(conn_box)

        # — Monitoramento —
        mon_box = QGroupBox("Monitoramento")
        mg = QGridLayout(mon_box)
        self.lbl_temp   = QLabel("Temp: --°C")
        self.lbl_press1 = QLabel("Supply: --")
        self.lbl_press2 = QLabel("Open: --")
        for w in (self.lbl_temp, self.lbl_press1, self.lbl_press2):
            w.setStyleSheet("font-weight:bold;")
        mg.addWidget(self.lbl_temp,0,0)
        mg.addWidget(self.lbl_press1,1,0)
        mg.addWidget(self.lbl_press2,1,1)
        self.layout().addWidget(mon_box)

        # — Configurações Operacionais —
        op_box = QGroupBox("Configurações")
        og = QGridLayout(op_box)
        # Modo
        og.addWidget(QLabel("Modo:"),0,0)
        self.cmb_mode = QComboBox(); self.cmb_mode.addItems(
            ["Defined","Infinite","Group","Purge"])
        self.btn_set_mode = QPushButton("Definir")
        og.addWidget(self.cmb_mode,0,1); og.addWidget(self.btn_set_mode,0,2)
        # Unidade
        og.addWidget(QLabel("Unidade:"),1,0)
        self.cmb_unit = QComboBox(); self.cmb_unit.addItems(["PSI","KPA"])
        self.btn_set_unit = QPushButton("Definir")
        og.addWidget(self.cmb_unit,1,1); og.addWidget(self.btn_set_unit,1,2)
        # Heat1
        og.addWidget(QLabel("Canal1:"),2,0)
        self.cmb_heat1 = QComboBox(); self.cmb_heat1.addItems(["ON","OFF"])
        self.btn_set_heat1 = QPushButton("Definir")
        og.addWidget(self.cmb_heat1,2,1); og.addWidget(self.btn_set_heat1,2,2)
        # Tempos Open/Close
        og.addWidget(QLabel("Open time (0.1ms):"),3,0)
        self.spin_open = QSpinBox(); self.spin_open.setRange(0,9999)
        self.btn_set_open = QPushButton("Definir")
        og.addWidget(self.spin_open,3,1); og.addWidget(self.btn_set_open,3,2)
        og.addWidget(QLabel("Close time (0.1ms):"),4,0)
        self.spin_close = QSpinBox(); self.spin_close.setRange(0,9999)
        self.btn_set_close = QPushButton("Definir")
        og.addWidget(self.spin_close,4,1); og.addWidget(self.btn_set_close,4,2)
        # Temp1
        og.addWidget(QLabel("Temp1 (0.1°C):"),5,0)
        self.spin_t1 = QSpinBox(); self.spin_t1.setRange(200,800)
        self.btn_set_t1 = QPushButton("Definir")
        og.addWidget(self.spin_t1,5,1); og.addWidget(self.btn_set_t1,5,2)

        self.layout().addWidget(op_box)

        # Timer de monitoramento
        self.monitor_timer = QTimer(self)
        self.monitor_timer.timeout.connect(self.monitor_device)

        # Conecta sinais
        self.btn_refresh.clicked.connect(self.refresh_ports)
        self.btn_connect.clicked.connect(self.toggle_connection)
        self.btn_set_mode.clicked.connect(self.set_mode)
        self.btn_set_unit.clicked.connect(self.set_unit)
        self.btn_set_heat1.clicked.connect(self.set_heat1)
        self.btn_set_open.clicked.connect(self.set_open_time)
        self.btn_set_close.clicked.connect(self.set_close_time)
        self.btn_set_t1.clicked.connect(self.set_temp1)

        # Registra controles para habilitar/desabilitar
        self._extended_controls += [
            self.cmb_mode, self.btn_set_mode,
            self.cmb_unit, self.btn_set_unit,
            self.cmb_heat1, self.btn_set_heat1,
            self.spin_open, self.btn_set_open,
            self.spin_close, self.btn_set_close,
            self.spin_t1, self.btn_set_t1
        ]

    def log(self, msg: str):
        # redireciona para o log geral
        if hasattr(self.ctrl, "log"):
            self.ctrl.log(f"[Applicadora] {msg}")
        else:
            print(f"[Applicadora] {msg}")

    def refresh_ports(self):
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        if not ports:
            self.port_combo.addItem("— nenhuma —")
            self.log("nenhuma porta serial encontrada")
            return
        for p in ports:
            txt = f"{p.device} ({p.description})"
            self.port_combo.addItem(txt, p.device)
        self.log(f"{len(ports)} porta(s) detectada(s)")
        # Se existir porta salva, tenta selecioná-la
        last = self.ctrl.settings.data.get('applicator_last_port')
        if last:
            idx = self.port_combo.findData(last)
            if idx >= 0:
                self.port_combo.setCurrentIndex(idx)

    def get_selected_port(self):
        d = self.port_combo.currentData()
        if d: return d
        txt = self.port_combo.currentText()
        return txt.split(' ')[0]

    def toggle_connection(self):
        if not self.serial_connection:
            self.connect_serial()
        else:
            self.disconnect_serial()

    def connect_serial(self):
        # evita reconectar na mesma porta se já estiver conectado
        if self.serial_connection:
            self.log("porta serial já conectada, pulando reconnect")
            return
        port = self.get_selected_port()
        if "nenhuma" in port.lower():
            QMessageBox.warning(self, "Erro", "Selecione uma porta válida")
            return
        try:
            self.serial_connection = serial.Serial(port=port, **COM_SETTINGS)
            time.sleep(0.2)
            self.lbl_status.setText("Conectado")
            self.lbl_status.setStyleSheet("color:green;")
            self.btn_connect.setText("Desconectar")
            self._set_controls_enabled(True)
            self.log(f"conectado em {port}")
            # Persiste porta usada
            try:
                self.ctrl.settings.data['applicator_last_port'] = port
                self.ctrl.settings.save()
            except Exception:
                print("Erro ao salvar porta no settings")
            QTimer.singleShot(AUTO_TEST_DELAY_MS, self.auto_test_connection)
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))
            self.log(f"falha na conexão: {e}")

    def disconnect_serial(self):
        if self.serial_connection:
            self.monitor_timer.stop()
            self.serial_connection.close()
            self.serial_connection = None
            self.lbl_status.setText("Desconectado")
            self.lbl_status.setStyleSheet("color:red;")
            self.btn_connect.setText("Conectar")
            self._set_controls_enabled(False)
            self.log("desconectado")

    def _set_controls_enabled(self, en: bool):
        for w in self._extended_controls:
            w.setEnabled(en)

    def auto_test_connection(self):
        self.log("teste comunicação...")
        # comando de leitura temperatura
        base = f"{DEVICE_ID:02X} {FUNC_READ:02X} 0048 00 01"
        cmd = self.build_modbus_command(base)
        r = self.send_command(cmd, "Teste Temp")
        if r and len(r)>=7:
            self.log("comunicação OK")
            self.parse_temperature_response(r)
            self.read_initial_parameters()
            self.monitor_timer.start(MONITOR_INTERVAL_MS)
        else:
            QMessageBox.warning(self, "Falha", "não foi possível comunicar")

    def send_command(self, hexstr: str, desc: str="") -> bytes | None:
        if not self.serial_connection:
            return None
        try:
            data = bytes.fromhex(hexstr.replace(" ", ""))
            self.serial_connection.reset_input_buffer()
            self.serial_connection.reset_output_buffer()
            self.log(f"TX {desc}: {hexstr}")
            self.serial_connection.write(data)
            resp = b""
            start = time.time()
            while time.time()-start < self.serial_connection.timeout:
                n = self.serial_connection.in_waiting
                if n:
                    resp += self.serial_connection.read(n)
                else:
                    QTimer.singleShot(1, lambda: None)
                    time.sleep(0.01)
                if len(resp)>=5: break
            if resp:
                self.log(f"RX ({len(resp)}): " +
                         ' '.join(f"{b:02X}" for b in resp))
                return resp
            self.log("sem resposta")
            return None
        except Exception as e:
            self.log(f"erro: {e}")
            return None

    def build_modbus_command(self, base_hex: str) -> str:
        data = bytes.fromhex(base_hex.replace(" ", ""))
        crc = self.calculate_crc(data)
        return base_hex + f" {crc[0]:02X} {crc[1]:02X}"

    @staticmethod
    def calculate_crc(data: bytes) -> bytes:
        crc = 0xFFFF
        for b in data:
            crc ^= b
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return crc.to_bytes(2, 'little')

    def send_and_parse(self, base_hex: str,
                       parser: Callable[[bytes], None],
                       desc: str):
        cmd = self.build_modbus_command(base_hex)
        r = self.send_command(cmd, desc)
        if r:
            try: parser(r)
            except Exception as e: self.log(f"parser '{desc}' erro: {e}")
        return r

    # — Helpers Modbus —
    def write_register(self, func: int, reg: int,
                       val: int, desc: str) -> bool:
        hi, lo = (val>>8)&0xFF, val&0xFF
        base = f"{DEVICE_ID:02X} {func:02X} {reg:04X} 00 01 02 {hi:02X} {lo:02X}"
        return bool(self.send_command(self.build_modbus_command(base), desc))

    def write_single_register(self, reg: int, val: int, desc: str) -> bool:
        base = f"{DEVICE_ID:02X} {FUNC_WRITE_SINGLE:02X} {reg:04X} 00 {val:02X}"
        return bool(self.send_command(self.build_modbus_command(base), desc))

    def read_register(self, reg: int, parser: Callable, desc: str):
        base = f"{DEVICE_ID:02X} {FUNC_READ:02X} {reg:04X} 00 01"
        return self.send_and_parse(base, parser, desc)

    # — Setters e Parsers —
    def set_mode(self):
        idx = self.cmb_mode.currentIndex()
        if self.write_single_register(0x0040, idx, "Modo"):
            QMessageBox.information(self, "OK", "Modo definido")

    def set_unit(self):
        idx = self.cmb_unit.currentIndex()
        if self.write_single_register(0x0041, idx, "Unidade"):
            QMessageBox.information(self, "OK", "Unidade definida")

    def set_heat1(self):
        idx = self.cmb_heat1.currentIndex()
        if self.write_single_register(0x0042, idx, "Heat1"):
            QMessageBox.information(self, "OK", "Canal1 definido")

    def set_open_time(self):
        v = self.spin_open.value()
        if self.write_register(FUNC_WRITE_MULTI, 0x0043, v, "Open"):
            QMessageBox.information(self, "OK", "Open time definido")

    def set_close_time(self):
        v = self.spin_close.value()
        if self.write_register(FUNC_WRITE_MULTI, 0x0044, v, "Close"):
            QMessageBox.information(self, "OK", "Close time definido")

    def set_temp1(self):
        v = self.spin_t1.value()
        if self.write_register(FUNC_WRITE_MULTI, 0x0047, v, "Temp1"):
            QMessageBox.information(self, "OK", "T1 definido")

    def parse_temperature_response(self, r: bytes):
        if len(r)>=7:
            raw = (r[3]<<8)|r[4]
            t = raw/10
            self.lbl_temp.setText(f"Temp: {t:.1f}°C")
            color = "red" if t>100 else "green"
            self.lbl_temp.setStyleSheet(f"color:{color};")
            # emite sinal de temperatura atual
            try:
                self.temperatureUpdated.emit(t)
            except Exception as e:
                print(f"Erro ao emitir sinal de temperatura: {e}")

    def parse_supply_pressure(self, r: bytes):
        if len(r)>=5:
            raw = (r[3]<<8)|r[4]
            p = raw/10
            self.lbl_press1.setText(f"Supply: {p:.1f}")

    def parse_open_pressure(self, r: bytes):
        if len(r)>=5:
            raw = (r[3]<<8)|r[4]
            p = raw/10
            self.lbl_press2.setText(f"Open: {p:.1f}")

    def read_initial_parameters(self):
        """
        Lê os registradores de configuração e popula:
          – modo (0x0040)
          – unidade (0x0041)
          – heat1  (0x0042)
          – open   (0x0043)
          – close  (0x0044)
          – temp1  (0x0047)
        """
        for reg, parser in [
            (0x0040, self.parse_mode_response),
            (0x0041, self.parse_unit_response),
            (0x0042, self.parse_heat1_response),
            (0x0043, lambda r: self.parse_time_response(r, 'open')),
            (0x0044, lambda r: self.parse_time_response(r, 'close')),
            (0x0047, lambda r: self.parse_tempset_response(r, 1)),
        ]:
            self.read_register(reg, parser, "Leitura Config")

    def monitor_device(self):
        for reg, parser, desc in [
            (0x0048, self.parse_temperature_response, "Temp"),
            (0x0049, self.parse_supply_pressure,     "Supply"),
            (0x004A, self.parse_open_pressure,       "Open"),
        ]:
            self.read_register(reg, parser, desc)
    
    # --------------------------------------------------
    # Parsers para atualização dos campos de configuração
    # --------------------------------------------------
    def parse_mode_response(self, r: bytes):
        if len(r) >= 5:
            val = (r[3] << 8) | r[4]
            if 0 <= val < self.cmb_mode.count():
                self.cmb_mode.setCurrentIndex(val)

    def parse_unit_response(self, r: bytes):
        if len(r) >= 5:
            val = (r[3] << 8) | r[4]
            if 0 <= val < self.cmb_unit.count():
                self.cmb_unit.setCurrentIndex(val)

    def parse_heat1_response(self, r: bytes):
        if len(r) >= 5:
            val = (r[3] << 8) | r[4]
            if 0 <= val < self.cmb_heat1.count():
                self.cmb_heat1.setCurrentIndex(val)

    def parse_time_response(self, r: bytes, which: str):
        if len(r) >= 5:
            val = (r[3] << 8) | r[4]
            if which == 'open':
                self.spin_open.setValue(val)
            elif which == 'close':
                self.spin_close.setValue(val)

    def parse_tempset_response(self, r: bytes, idx: int):
        if len(r) >= 5:
            val = (r[3] << 8) | r[4]
            self.spin_t1.setValue(val)
            # emite sinal de temperatura configurada (°C)
            try:
                self.configTempUpdated.emit(val/10)
            except Exception as e:
                print(f"Erro ao emitir sinal de temperatura configurada: {e}")

    # --------------------------------------------------
    # Sempre que a janela for exibida, relê configurações
    # --------------------------------------------------
    def showEvent(self, event):
        super().showEvent(event)
        if self.serial_connection:
            self.read_initial_parameters()
