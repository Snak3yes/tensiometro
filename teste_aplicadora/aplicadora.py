import sys
import serial
import serial.tools.list_ports
import struct
import time
from typing import Callable
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *


# Constantes de configuração Modbus/Serial
COM_SETTINGS = dict(
    baudrate=115200,  # FIXO conforme manual
    bytesize=8,       # FIXO conforme manual
    parity='N',       # Sem paridade
    stopbits=1,       # FIXO conforme manual
    timeout=0.5,      # 500 ms
    rtscts=False,
    dsrdtr=False
)
# Temporizações (ms)
MONITOR_INTERVAL_MS = 3000
AUTO_TEST_DELAY_MS  = 500

# Novas constantes Modbus
DEVICE_ID         = 0x01
FUNC_READ         = 0x03
FUNC_WRITE_SINGLE = 0x06
FUNC_WRITE_MULTI  = 0x10

class AdhesiveApplicatorController(QMainWindow):
    def __init__(self):
        super().__init__()
        self.serial_connection = None
        self._extended_controls = []
        self.init_ui()
        self.refresh_ports()
        
    def init_ui(self):
        self.setWindowTitle("Controlador Aplicadora AJC-10 - Configuração Correta")
        self.setGeometry(100, 100, 800, 450)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Seção de Conexão
        conn_group = QGroupBox("Conexão Serial")
        conn_layout = QGridLayout(conn_group)
        
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(350)
        self.refresh_btn = QPushButton("Atualizar Portas")
        self.refresh_btn.clicked.connect(self.refresh_ports)
        self.connect_btn = QPushButton("Conectar")
        self.connect_btn.clicked.connect(self.toggle_connection)
        self.status_label = QLabel("Desconectado")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        
        conn_layout.addWidget(QLabel("Porta COM:"), 0, 0)
        conn_layout.addWidget(self.port_combo, 0, 1)
        conn_layout.addWidget(self.refresh_btn, 0, 2)
        conn_layout.addWidget(self.connect_btn, 1, 1)
        conn_layout.addWidget(QLabel("Status:"), 1, 0)
        conn_layout.addWidget(self.status_label, 1, 2)
        
        # Configurações fixas conforme manual
        config_group = QGroupBox("Configurações (Conforme Manual AJC-10)")
        config_layout = QGridLayout(config_group)
        
        config_layout.addWidget(QLabel("Baudrate:"), 0, 0)
        config_layout.addWidget(QLabel("115200 bps (FIXO)"), 0, 1)
        config_layout.addWidget(QLabel("Dados/Paridade/Stop:"), 0, 2)
        config_layout.addWidget(QLabel("8-N-1 (FIXO)"), 0, 3)
        config_layout.addWidget(QLabel("Device ID:"), 1, 0)
        config_layout.addWidget(QLabel("1 (FIXO)"), 1, 1)
        config_layout.addWidget(QLabel("Protocolo:"), 1, 2)
        config_layout.addWidget(QLabel("Modbus RTU"), 1, 3)
        
        # Monitoramento
        monitor_group = QGroupBox("Monitoramento em Tempo Real")
        monitor_layout = QGridLayout(monitor_group)
        
        self.temp_label = QLabel("Temperatura: -- °C")
        self.temp_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        monitor_layout.addWidget(self.temp_label, 0, 0)
        # Pressões Pneumáticas
        self.supply_pressure_label = QLabel("Supply Pressure: --")
        self.supply_pressure_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.open_pressure_label = QLabel("Open-Valve Pressure: --")
        self.open_pressure_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        monitor_layout.addWidget(self.supply_pressure_label, 2, 0)
        monitor_layout.addWidget(self.open_pressure_label, 2, 1)

        # Controles operacionais
        control_group = QGroupBox("Controles Operacionais")
        control_layout = QGridLayout(control_group)
        # Controles Operacionais – Botão Carregar Informações
        self.load_info_btn = QPushButton("Carregar Informações")
        control_layout.addWidget(self.load_info_btn, 0, 0, 1, 4)
        self.load_info_btn.setEnabled(False)
        self.load_info_btn.clicked.connect(self.read_initial_parameters)
        # Modo de Disparo (DEFINIDO, INFINITE, GROUP, PURGE)
        control_layout.addWidget(QLabel("Modo:"), 1, 0)
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Defined","Infinite","Group","Purge"])
        self.mode_combo.setEnabled(False)
        control_layout.addWidget(self.mode_combo, 1, 1)
        self.set_mode_btn = QPushButton("Definir Modo")
        self.set_mode_btn.setEnabled(False)
        self.set_mode_btn.clicked.connect(self.set_mode)
        control_layout.addWidget(self.set_mode_btn, 1, 2)
        # --- Parâmetros Estendidos ---
        # Unidade de Pressão (0x41)
        control_layout.addWidget(QLabel("Unidade Pressão:"), 4, 0)
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["PSI","KPA"])
        self.unit_combo.setEnabled(False)
        control_layout.addWidget(self.unit_combo, 4, 1)
        self.set_unit_btn = QPushButton("Definir Unidade")
        self.set_unit_btn.setEnabled(False)
        self.set_unit_btn.clicked.connect(self.set_unit)
        control_layout.addWidget(self.set_unit_btn, 4, 2)

        # Canal1 On/Off (0x42)
        control_layout.addWidget(QLabel("Canal1 Aquec.:"), 5, 0)
        self.heat1_combo = QComboBox()
        self.heat1_combo.addItems(["ON","OFF"])
        self.heat1_combo.setEnabled(False)
        control_layout.addWidget(self.heat1_combo, 5, 1)
        self.set_heat1_btn = QPushButton("Definir Canal1")
        self.set_heat1_btn.setEnabled(False)
        self.set_heat1_btn.clicked.connect(self.set_heat1)
        control_layout.addWidget(self.set_heat1_btn, 5, 2)

        # Open/Close Time (0x43,0x44)
        control_layout.addWidget(QLabel("Open Time (0.1ms):"), 6, 0)
        self.open_time_spin = QSpinBox()
        self.open_time_spin.setRange(0,9999)
        self.open_time_spin.setEnabled(False)
        control_layout.addWidget(self.open_time_spin, 6, 1)
        self.set_open_btn = QPushButton("Definir Open")
        self.set_open_btn.setEnabled(False)
        self.set_open_btn.clicked.connect(self.set_open_time)
        control_layout.addWidget(self.set_open_btn, 6, 2)

        control_layout.addWidget(QLabel("Close Time (0.1ms):"), 7, 0)
        self.close_time_spin = QSpinBox()
        self.close_time_spin.setRange(0,9999)
        self.close_time_spin.setEnabled(False)
        control_layout.addWidget(self.close_time_spin, 7, 1)
        self.set_close_btn = QPushButton("Definir Close")
        self.set_close_btn.setEnabled(False)
        self.set_close_btn.clicked.connect(self.set_close_time)
        control_layout.addWidget(self.set_close_btn, 7, 2)

        

        # Temperatura de Set (0x47)
        control_layout.addWidget(QLabel("Temp1 Set (0.1°C):"), 8, 0)
        self.temp1_spin = QSpinBox()
        self.temp1_spin.setRange(200,800)
        self.temp1_spin.setEnabled(False)
        control_layout.addWidget(self.temp1_spin, 8, 1)
        self.set_temp1_btn = QPushButton("Definir T1")
        self.set_temp1_btn.setEnabled(False)
        self.set_temp1_btn.clicked.connect(self.set_temp1)
        control_layout.addWidget(self.set_temp1_btn, 8, 2)

        # Adicionar todos os grupos
        layout.addWidget(conn_group)
        # Painel com Monitoramento e Configurações lado a lado
        hbox = QHBoxLayout()
        hbox.addWidget(monitor_group)
        hbox.addWidget(config_group)
        layout.addLayout(hbox)
        layout.addWidget(control_group)
        
        # Timer para monitoramento
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.monitor_device)

        # Registra os controles operacionais para DRY nas chamadas de setEnabled
        self._extended_controls.extend([
            self.load_info_btn, self.mode_combo, self.set_mode_btn,
            self.unit_combo, self.set_unit_btn, self.heat1_combo,
            self.set_heat1_btn, self.open_time_spin, self.set_open_btn,
            self.close_time_spin, self.set_close_btn, self.temp1_spin,
            self.set_temp1_btn
        ])
    def write_register(self, func: int, reg: int, val: int, desc: str):
        """Helper genérico de escrita Modbus RTU (função 0x10, 1 registrador)."""
        hi, lo = (val >> 8) & 0xFF, val & 0xFF
        base = f"01 {func:02X} {reg:04X} 00 01 02 {hi:02X} {lo:02X}"
        return self.send_command(self.build_modbus_command(base), desc)
    
    def write_single_register(self, reg: int, val: int, desc: str):
        """Escreve 1 registrador via função 0x06."""
        base = f"{DEVICE_ID:02X} {FUNC_WRITE_SINGLE:02X} {reg:04X} 00 {val:02X}"
        return self.send_command(self.build_modbus_command(base), desc)

    def read_register(self, reg: int, parser: Callable, desc: str):
        """Lê 1 registrador via função 0x03 e dispara o parser."""
        base = f"{DEVICE_ID:02X} {FUNC_READ:02X} {reg:04X} 00 01"
        return self.send_and_parse(base, parser, desc)
        
    def refresh_ports(self):
        """Atualiza portas COM"""
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        
        if not ports:
            self.port_combo.addItem("Nenhuma porta encontrada")
            self.log_message(" Nenhuma porta COM encontrada")
            return
            
        for port in sorted(ports):
            port_info = f"{port.device}"
            if port.description and port.description != "n/a":
                port_info += f" - {port.description}"
            if port.manufacturer:
                port_info += f" ({port.manufacturer})"
                
            self.port_combo.addItem(port_info, port.device)
            
            # Destacar portas conhecidas
            if any(keyword in str(port.description).lower() for keyword in 
                   ['cp210x', 'silicon labs', 'usb-serial', 'ch340', 'ftdi']):
                self.log_message(f" Porta USB-Serial encontrada: {port_info}")
                
        self.log_message(f" Total: {len(ports)} porta(s) COM")
        
    def get_selected_port(self):
        """Retorna porta selecionada"""
        current_data = self.port_combo.currentData()
        return current_data if current_data else self.port_combo.currentText().split(' - ')[0]
        
    def toggle_connection(self):
        if self.serial_connection is None:
            self.connect_serial()
        else:
            self.disconnect_serial()
            
    def connect_serial(self):
        try:
            port = self.get_selected_port()
            if not port or "Nenhuma porta" in port:
                QMessageBox.warning(self, "Erro", "Selecione uma porta COM válida")
                return
                
            self.serial_connection = serial.Serial(port=port, **COM_SETTINGS)
            
            # Aguardar estabilização
            time.sleep(0.2)
            
            self.status_label.setText("Conectado")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            self.connect_btn.setText("Desconectar")
            
            # Habilita todos os controles operacionais de uma vez
            self._set_controls_enabled(True)
            
            self.log_message(f" CONECTADO: {port} @ 115200-8-N-1")
            self.log_message(" Configurações conforme manual AJC-10")
            
            # Teste automático após conexão
            QTimer.singleShot(AUTO_TEST_DELAY_MS, self.auto_test_connection)
            
        except Exception as e:
            QMessageBox.critical(self, "Erro de Conexão", f"Erro: {e}")
            self.log_message(f" ERRO: {e}")
            
    def disconnect_serial(self):
        if self.serial_connection:
            self.monitor_timer.stop()
            self.serial_connection.close()
            self.serial_connection = None
            
            self.status_label.setText("Desconectado")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.connect_btn.setText("Conectar")
                        
            # Desabilita todos os controles operacionais de uma vez
            self._set_controls_enabled(False)
            
            self.log_message(" Desconectado")
            
    def send_command(self, cmd_hex_string, description=""):
        """Envia comando e retorna resposta"""
        if not self.serial_connection:
            return None
            
        try:
            # Converter string hex para bytes
            cmd_bytes = bytes.fromhex(cmd_hex_string.replace(" ", ""))
            
            # Limpar buffers
            self.serial_connection.reset_input_buffer()
            self.serial_connection.reset_output_buffer()
            
            # Log do envio
            self.log_message(f" TX {description}: {cmd_hex_string}")
            
            # Enviar comando
            self.serial_connection.write(cmd_bytes)
            
            # Aguardar resposta de forma não bloqueante
            response = b""
            start = time.time()
            while time.time() - start < self.serial_connection.timeout:
                waiting = self.serial_connection.in_waiting
                if waiting > 0:
                    response += self.serial_connection.read(waiting)
                else:
                    # permite que a UI continue responsiva
                    QCoreApplication.processEvents()
                    time.sleep(0.01)
                # se já vier um frame mínimo (unitário), pode quebrar antes
                if len(response) >= 5:
                    break

            # para compatibilidade, renomeia a variável
            raw = response
            
            if response:
                resp_hex = ' '.join(f"{b:02X}" for b in raw)
                self.log_message(f"📥 RX ({len(response)} bytes): {resp_hex}")
                
                return raw
            else:
                self.log_message("⚠️ SEM RESPOSTA")
                
                return None
                
        except Exception as e:
            self.log_message(f" ERRO: {e}")
            return None
            
    def auto_test_connection(self):
        """Teste automático ao conectar"""
        self.log_message(" TESTE AUTOMÁTICO DE CONEXÃO...")
        
        # Teste 1: Leitura de temperatura (com CRC calculado)
        base_cmd = "01 03 00 48 00 01"
        full_cmd = self.build_modbus_command(base_cmd)
        response = self.send_command(full_cmd, "Leitura Temperatura")

        if response and len(response) >= 7:
            self.log_message("🎉 COMUNICAÇÃO ESTABELECIDA COM SUCESSO!")
            # Atualiza leitura de temperatura
            self.parse_temperature_response(response)
            # Lê todos os parâmetros visíveis e preenche campos na UI
            self.read_initial_parameters()
            # Inicia monitoramento periódico
            self.monitor_timer.start(MONITOR_INTERVAL_MS)
        else:
            self.log_message(" FALHA NA COMUNICAÇÃO")
            QMessageBox.warning(self, "Falha", "Não foi possível estabelecer comunicação.\nVerifique:\n• Equipamento ligado\n• Cabo conectado\n• Porta correta")
    def build_modbus_command(self, base_hex):
        """Gera comando Modbus RTU com CRC16"""
        data = bytes.fromhex(base_hex.replace(" ", ""))
        crc = self.calculate_crc(data)
        # Retorna string hex com CRC em ordem little-endian (low byte, high byte)
        return base_hex + f" {crc[0]:02X} {crc[1]:02X}"    
            
    def parse_temperature_response(self, response):
        """Interpreta resposta de temperatura"""
        if len(response) >= 7:
            # Conforme manual: bytes 3-4 contêm temperatura
            temp_raw = (response[3] << 8) | response[4]
            temperature = temp_raw / 10.0  # Dividir por 10 conforme manual
            
            self.temp_label.setText(f"Temperatura: {temperature:.1f} °C")
            
            if temperature > 100:
                self.temp_label.setStyleSheet("font-size: 16px; font-weight: bold; color: red;")
            else:
                self.temp_label.setStyleSheet("font-size: 16px; font-weight: bold; color: green;")
                
            self.log_message(f"Temperatura atual: {temperature:.1f}°C")

    def _set_controls_enabled(self, enable: bool):
        """Ativa ou desativa todos os controles operacionais registrados."""
        for w in self._extended_controls:
            w.setEnabled(enable)
    def send_and_parse(self, base_hex: str, parser, description: str):
        """Envia comando Modbus RTU (via build_modbus_command) e dispara parser em caso de resposta."""
        cmd = self.build_modbus_command(base_hex)
        resp = self.send_command(cmd, description)
        if resp:
            try:
                parser(resp)
            except Exception as e:
                self.log_message(f" Erro no parser para '{description}': {e}")
        return resp
            
    def monitor_device(self):
        """Monitoramento em loop apenas de temperatura e pressões."""
        # leitura periódica parametrizada
        for reg, parser, desc in [
            (0x0048, self.parse_temperature_response, "Monitor Temperatura"),
            (0x0049, self.parse_supply_pressure,     "Monitor Supply-Pressure"),
            (0x004A, self.parse_open_pressure,        "Monitor Open-Pressure"),
        ]:
            self.read_register(reg, parser, desc)
              
    def calculate_crc(self, data):
        """Calcula CRC16 Modbus"""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return crc.to_bytes(2, 'little')
        
    def log_message(self, message):
        """Log com timestamp (usa saída padrão após remoção do widget de log)"""
        timestamp = QTime.currentTime().toString("hh:mm:ss")
        print(f"[{timestamp}] {message}")
        
    
        
    
    def set_mode(self):
        """Define modo de disparo (Finite ou Infinite)"""
        # indice corresponde ao código de modo 0=Defined,1=Infinite,2=Group,3=Purge
        idx = self.mode_combo.currentIndex()
        if self.write_single_register(0x0040, idx, "Configurar Modo"):
            text = self.mode_combo.currentText()
            QMessageBox.information(self, "Sucesso", f"Modo definido: {text}")
        else:
            QMessageBox.critical(self, "Erro", "Falha ao definir modo")
    # --- Setters para extensão ---
    def set_unit(self):
        # currentIndex já retorna 0 para PSI, 1 para KPA
        if self.write_single_register(0x0041,
                                      self.unit_combo.currentIndex(),
                                      "Definir Unidade"):
            QMessageBox.information(self, "OK", "Unidade definida")

    def set_heat1(self):
        # currentIndex: 0=ON, 1=OFF
        if self.write_single_register(0x0042,
                                      self.heat1_combo.currentIndex(),
                                      "Definir Canal1"):
            QMessageBox.information(self, "OK", "Canal1 definido")

    def set_open_time(self):
        valor = self.open_time_spin.value()
        if self.write_register(0x10, 0x0043, valor, "Definir Open"):
            QMessageBox.information(self, "OK", "Open time definido")

    def set_close_time(self):
        valor = self.close_time_spin.value()
        if self.write_register(0x10, 0x0044, valor, "Definir Close"):
            QMessageBox.information(self, "OK", "Close time definido")

    def set_temp1(self):
        valor = self.temp1_spin.value()
        if self.write_register(0x10, 0x0047, valor, "Definir T1"):
            QMessageBox.information(self, "OK", "T1 set definido")

    # --- Parsers para extensão ---
    def parse_unit_response(self, r):
        # Monta valor completo do registrador (hi+lo)
        raw = (r[3] << 8) | r[4]
        # Esperado 0 -> PSI, 1 -> KPA
        idx = 0 if raw not in (0, 1) else raw
        self.unit_combo.setCurrentIndex(idx)
        self.log_message(f" Unidade de Pressão: {self.unit_combo.currentText()}")

    def parse_heat1_response(self, r):
        v = r[3]
        self.heat1_combo.setCurrentIndex(0 if v==0 else 1)
        self.log_message(f" Heat1: {self.heat1_combo.currentText()}")

    def parse_time_response(self,r,kind):
        ms = (r[3]<<8)|r[4]
        if kind=='open':
            self.open_time_spin.setValue(ms)
        else:
            self.close_time_spin.setValue(ms)
        self.log_message(f" {kind.capitalize()} Time: {ms*0.1}ms")

    def parse_tempset_response(self, r, ch):
        """Interpreta resposta de set-point de T1"""
        v = (r[3] << 8) | r[4]
        self.temp1_spin.setValue(v)
        self.log_message(f" T1 Set: {v/10:.1f}°C")

    def parse_mode_response(self, response):
        """Interpreta resposta de leitura de modo de disparo"""
        if len(response) >= 7:
            raw = (response[3] << 8) | response[4]
            modes = {0:"Defined",1:"Infinite",2:"Group",3:"Purge"}
            # atualiza combo se valor válido
            if raw in modes:
                self.mode_combo.setCurrentIndex(raw)
            # apenas logar o modo atual, sem tentar usar mode_label
            self.log_message(f" Modo atual: {modes.get(raw, f'Unknown({raw})')}")
    
    def parse_supply_pressure(self, response):
        """Interpreta resposta de supply pressure (0x49)"""
        if len(response) >= 5:
            raw = (response[3] << 8) | response[4]
            pressure = raw / 10.0
            unit = self.unit_combo.currentText()
            self.supply_pressure_label.setText(f"Supply Pressure: {pressure:.1f} {unit}")
            self.log_message(f" Supply Pressure: {pressure:.1f} {unit}")

    def parse_open_pressure(self, response):
        """Interpreta resposta de open-valve pressure (0x4A)"""
        if len(response) >= 5:
            raw = (response[3] << 8) | response[4]
            pressure = raw / 10.0
            unit = self.unit_combo.currentText()
            self.open_pressure_label.setText(f"Open-Valve Pressure: {pressure:.1f} {unit}")
            self.log_message(f" Open-Valve Pressure: {pressure:.1f} {unit}")

    def read_initial_parameters(self):
        """
        Lê registradores após a conexão e preenche os campos da UI:
        modo, unidade de pressão, canal1, tempos e temperaturas set.
        """
        # inicialização em lote dos parâmetros
        for reg, parser in [
            (0x0040, self.parse_mode_response),
            (0x0041, self.parse_unit_response),
            (0x0042, self.parse_heat1_response),
            (0x0043, lambda r: self.parse_time_response(r, 'open')),
            (0x0044, lambda r: self.parse_time_response(r, 'close')),
            (0x0047, lambda r: self.parse_tempset_response(r, 1)),
            (0x0049, self.parse_supply_pressure),
            (0x004A, self.parse_open_pressure),
        ]:
            self.read_register(reg, parser, "Leitura Inicial")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AdhesiveApplicatorController()
    window.show()
    sys.exit(app.exec())
