import sys
import serial
import serial.tools.list_ports
import struct
import time
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
class AdhesiveApplicatorController(QMainWindow): 
    def __init__(self): 
        super().__init__() 
        self.serial_connection = None 
        self.init_ui() 
        self.refresh_ports()

    def init_ui(self):
        self.setWindowTitle("Controlador Aplicadora de Adesivo AJC-10 - Diagnóstico Avançado")
        self.setGeometry(100, 100, 1000, 800)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Seção de Conexão
        conn_group = QGroupBox("Conexão Serial")
        conn_layout = QGridLayout(conn_group)
        
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(300)
        self.refresh_btn = QPushButton("🔄 Atualizar Portas")
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
        
        # Configurações de Comunicação Expandidas
        comm_group = QGroupBox("Configurações de Comunicação")
        comm_layout = QGridLayout(comm_group)
        
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.addItems(["1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200"])
        self.baudrate_combo.setCurrentText("9600")
        
        self.parity_combo = QComboBox()
        self.parity_combo.addItems(["None", "Even", "Odd"])
        self.parity_combo.setCurrentText("None")
        
        self.stopbits_combo = QComboBox()
        self.stopbits_combo.addItems(["1", "2"])
        self.stopbits_combo.setCurrentText("1")
        
        self.device_id_spin = QSpinBox()
        self.device_id_spin.setRange(1, 255)
        self.device_id_spin.setValue(1)
        
        self.timeout_spin = QDoubleSpinBox()
        self.timeout_spin.setRange(0.1, 10.0)
        self.timeout_spin.setValue(2.0)
        self.timeout_spin.setSuffix(" s")
        
        comm_layout.addWidget(QLabel("Baud Rate:"), 0, 0)
        comm_layout.addWidget(self.baudrate_combo, 0, 1)
        comm_layout.addWidget(QLabel("Paridade:"), 0, 2)
        comm_layout.addWidget(self.parity_combo, 0, 3)
        comm_layout.addWidget(QLabel("Stop Bits:"), 1, 0)
        comm_layout.addWidget(self.stopbits_combo, 1, 1)
        comm_layout.addWidget(QLabel("Device ID:"), 1, 2)
        comm_layout.addWidget(self.device_id_spin, 1, 3)
        comm_layout.addWidget(QLabel("Timeout:"), 2, 0)
        comm_layout.addWidget(self.timeout_spin, 2, 1)
        
        # Seção de Diagnóstico
        diag_group = QGroupBox("Ferramentas de Diagnóstico")
        diag_layout = QGridLayout(diag_group)
        
        self.scan_devices_btn = QPushButton("🔍 Scan Dispositivos (ID 1-10)")
        self.scan_devices_btn.clicked.connect(self.scan_devices)
        self.scan_devices_btn.setEnabled(False)
        
        self.scan_baudrates_btn = QPushButton("📡 Scan Baudrates")
        self.scan_baudrates_btn.clicked.connect(self.scan_baudrates)
        self.scan_baudrates_btn.setEnabled(False)
        
        self.test_basic_cmd_btn = QPushButton("🧪 Teste Comandos Básicos")
        self.test_basic_cmd_btn.clicked.connect(self.test_basic_commands)
        self.test_basic_cmd_btn.setEnabled(False)
        
        self.send_raw_btn = QPushButton("📝 Enviar Comando Raw")
        self.send_raw_btn.clicked.connect(self.send_raw_command)
        self.send_raw_btn.setEnabled(False)
        
        self.raw_command_input = QLineEdit()
        self.raw_command_input.setPlaceholderText("Ex: 01 03 00 48 00 01 04 1C")
        
        diag_layout.addWidget(self.scan_devices_btn, 0, 0)
        diag_layout.addWidget(self.scan_baudrates_btn, 0, 1)
        diag_layout.addWidget(self.test_basic_cmd_btn, 1, 0)
        diag_layout.addWidget(self.send_raw_btn, 1, 1)
        diag_layout.addWidget(QLabel("Comando Raw:"), 2, 0)
        diag_layout.addWidget(self.raw_command_input, 2, 1)
        
        # Seção de Monitoramento
        monitor_group = QGroupBox("Monitoramento em Tempo Real")
        monitor_layout = QGridLayout(monitor_group)
        
        self.temp_label = QLabel("Temperatura: -- °C")
        self.temp_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.fluid_label = QLabel("Pressão Fluido: -- psi")
        self.valve_label = QLabel("Pressão Válvula: -- psi")
        self.connection_status = QLabel("Status Conexão: Desconectado")
        self.last_response_label = QLabel("Última Resposta: --")
        
        monitor_layout.addWidget(self.temp_label, 0, 0)
        monitor_layout.addWidget(self.fluid_label, 0, 1)
        monitor_layout.addWidget(self.valve_label, 1, 0)
        monitor_layout.addWidget(self.connection_status, 1, 1)
        monitor_layout.addWidget(self.last_response_label, 2, 0, 1, 2)
        
        # Seção de Controle
        control_group = QGroupBox("Controle da Aplicadora")
        control_layout = QGridLayout(control_group)
        
        # Modo de Operação
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["DEFINED", "INFINITE"])
        self.set_mode_btn = QPushButton("Definir Modo")
        self.set_mode_btn.clicked.connect(self.set_mode)
        self.set_mode_btn.setEnabled(False)
        
        control_layout.addWidget(QLabel("Modo:"), 0, 0)
        control_layout.addWidget(self.mode_combo, 0, 1)
        control_layout.addWidget(self.set_mode_btn, 0, 2)
        
        # Ciclos
        self.cycles_spin = QSpinBox()
        self.cycles_spin.setRange(1, 65535)
        self.cycles_spin.setValue(50)
        self.set_cycles_btn = QPushButton("Definir Ciclos")
        self.set_cycles_btn.clicked.connect(self.set_cycles)
        self.set_cycles_btn.setEnabled(False)
        
        control_layout.addWidget(QLabel("Ciclos:"), 1, 0)
        control_layout.addWidget(self.cycles_spin, 1, 1)
        control_layout.addWidget(self.set_cycles_btn, 1, 2)
        
        # Controle Manual
        self.trigger_btn = QPushButton("🎯 Trigger Manual")
        self.trigger_btn.clicked.connect(self.manual_trigger)
        self.trigger_btn.setEnabled(False)
        self.trigger_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")
        
        control_layout.addWidget(self.trigger_btn, 2, 1)
        
        # Log de Comunicação
        log_group = QGroupBox("Log de Comunicação")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Courier", 9))
        
        log_controls = QHBoxLayout()
        self.clear_log_btn = QPushButton("Limpar Log")
        self.clear_log_btn.clicked.connect(self.clear_log)
        self.auto_scroll_check = QCheckBox("Auto Scroll")
        self.auto_scroll_check.setChecked(True)
        
        log_controls.addWidget(self.clear_log_btn)
        log_controls.addWidget(self.auto_scroll_check)
        log_controls.addStretch()
        
        log_layout.addWidget(self.log_text)
        log_layout.addLayout(log_controls)
        
        layout.addWidget(conn_group)
        layout.addWidget(comm_group)
        layout.addWidget(diag_group)
        layout.addWidget(monitor_group)
        layout.addWidget(control_group)
        layout.addWidget(log_group)
        
        # Timer para leitura periódica
        self.read_timer = QTimer()
        self.read_timer.timeout.connect(self.read_sensors)
        
    def refresh_ports(self):
        """Atualiza a lista de portas COM disponíveis"""
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        
        if not ports:
            self.port_combo.addItem("Nenhuma porta encontrada")
            self.log_message("❌ Nenhuma porta COM encontrada")
            return
            
        for port in sorted(ports):
            # Formatar informações da porta
            port_info = f"{port.device}"
            if port.description and port.description != "n/a":
                port_info += f" - {port.description}"
            if port.manufacturer and port.manufacturer != "n/a":
                port_info += f" ({port.manufacturer})"
                
            self.port_combo.addItem(port_info, port.device)
            
            # Destacar portas USB-Serial conhecidas
            if any(keyword in port.description.lower() for keyword in 
                ['cp210x', 'silicon labs', 'usb-serial', 'ch340', 'ftdi'] if port.description):
                self.log_message(f"🔌 Encontrada porta USB-Serial: {port_info}")
                
        self.log_message(f"🔍 Encontradas {len(ports)} porta(s) COM")
        
    def get_selected_port(self):
        """Retorna a porta selecionada"""
        current_data = self.port_combo.currentData()
        if current_data:
            return current_data
        else:
            # Fallback para o texto se não houver dados
            return self.port_combo.currentText().split(' - ')[0].split(' (')[0]
            
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
                
            baudrate = int(self.baudrate_combo.currentText())
            parity_map = {"None": "N", "Even": "E", "Odd": "O"}
            parity = parity_map[self.parity_combo.currentText()]
            stopbits = int(self.stopbits_combo.currentText())
            timeout = self.timeout_spin.value()
            
            self.serial_connection = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=8,
                parity=parity,
                stopbits=stopbits,
                timeout=timeout
            )
            
            self.status_label.setText("Conectado")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            self.connect_btn.setText("Desconectar")
            self.connection_status.setText("Status Conexão: Conectado")
            
            # Habilitar controles
            self.set_mode_btn.setEnabled(True)
            self.set_cycles_btn.setEnabled(True)
            self.trigger_btn.setEnabled(True)
            self.scan_devices_btn.setEnabled(True)
            self.scan_baudrates_btn.setEnabled(True)
            self.test_basic_cmd_btn.setEnabled(True)
            self.send_raw_btn.setEnabled(True)
            
            self.log_message(f"✅ Conectado em {port} @ {baudrate} bps, {parity}-{stopbits}, timeout={timeout}s")
            
            # Aguardar um momento antes do teste
            QTimer.singleShot(100, self.test_communication)
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao conectar: {e}")
            self.log_message(f"❌ Erro de conexão: {e}")
            
    def disconnect_serial(self):
        if self.serial_connection:
            self.read_timer.stop()
            self.serial_connection.close()
            self.serial_connection = None
            self.status_label.setText("Desconectado")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.connect_btn.setText("Conectar")
            self.connection_status.setText("Status Conexão: Desconectado")
            
            # Desabilitar controles
            self.set_mode_btn.setEnabled(False)
            self.set_cycles_btn.setEnabled(False)
            self.trigger_btn.setEnabled(False)
            self.scan_devices_btn.setEnabled(False)
            self.scan_baudrates_btn.setEnabled(False)
            self.test_basic_cmd_btn.setEnabled(False)
            self.send_raw_btn.setEnabled(False)
            
            self.log_message("🔌 Desconectado")
            
    def send_modbus_command(self, command_bytes, wait_response=True, delay_before=0):
        """Envia comando Modbus e retorna resposta"""
        if not self.serial_connection:
            return None
            
        try:
            if delay_before > 0:
                time.sleep(delay_before)
                
            # Limpar buffer antes de enviar
            self.serial_connection.reset_input_buffer()
            self.serial_connection.reset_output_buffer()
            
            # Log do comando enviado
            cmd_hex = ' '.join([f'{b:02X}' for b in command_bytes])
            self.log_message(f"📤 TX: {cmd_hex}")
            
            self.serial_connection.write(command_bytes)
            
            if not wait_response:
                return b''
            
            # Aguardar resposta com timeout maior
            response = self.serial_connection.read(50)  # Aumentar buffer
            
            if response:
                resp_hex = ' '.join([f'{b:02X}' for b in response])
                self.log_message(f"📥 RX: {resp_hex} ({len(response)} bytes)")
                self.last_response_label.setText(f"Última Resposta: {resp_hex}")
            else:
                self.log_message("⚠️ Sem resposta")
                self.last_response_label.setText("Última Resposta: SEM RESPOSTA")
                
            return response
        except Exception as e:
            self.log_message(f"❌ Erro na comunicação: {e}")
            return None
            
    def calculate_crc(self, data):
        """Calcula CRC16 para Modbus RTU"""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return crc.to_bytes(2, 'little')
        
    def scan_devices(self):
        """Scan para encontrar device IDs válidos"""
        self.log_message("🔍 Iniciando scan de dispositivos (ID 1-10)...")
        
        for device_id in range(1, 11):
            self.log_message(f"Testando Device ID {device_id}...")
            
            # Comando de leitura simples
            command = bytes([device_id, 0x03, 0x00, 0x48, 0x00, 0x01])
            crc = self.calculate_crc(command)
            full_command = command + crc
            
            response = self.send_modbus_command(full_command, delay_before=0.1)
            
            if response and len(response) >= 5:
                self.log_message(f"✅ DISPOSITIVO ENCONTRADO! ID: {device_id}")
                self.device_id_spin.setValue(device_id)
                return
            
            QApplication.processEvents()  # Permitir atualizações da UI
            
        self.log_message("❌ Nenhum dispositivo respondeu ao scan")
        
    def scan_baudrates(self):
        """Scan diferentes baudrates"""
        if not self.serial_connection:
            return
            
        baudrates = [1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200]
        current_port = self.get_selected_port()
        
        self.log_message("📡 Iniciando scan de baudrates...")
        
        for baudrate in baudrates:
            self.log_message(f"Testando {baudrate} bps...")
            
            try:
                # Reconectar com novo baudrate
                self.serial_connection.close()
                
                parity_map = {"None": "N", "Even": "E", "Odd": "O"}
                parity = parity_map[self.parity_combo.currentText()]
                stopbits = int(self.stopbits_combo.currentText())
                
                self.serial_connection = serial.Serial(
                    port=current_port,
                    baudrate=baudrate,
                    bytesize=8,
                    parity=parity,
                    stopbits=stopbits,
                    timeout=1.0
                )
                
                time.sleep(0.1)  # Aguardar estabilização
                
                # Testar comando
                device_id = self.device_id_spin.value()
                command = bytes([device_id, 0x03, 0x00, 0x48, 0x00, 0x01])
                crc = self.calculate_crc(command)
                full_command = command + crc
                
                response = self.send_modbus_command(full_command)
                
                if response and len(response) >= 5:
                    self.log_message(f"✅ BAUDRATE CORRETO: {baudrate} bps!")
                    self.baudrate_combo.setCurrentText(str(baudrate))
                    return
                    
            except Exception as e:
                self.log_message(f"❌ Erro em {baudrate} bps: {e}")
                
            QApplication.processEvents()
            
        self.log_message("❌ Nenhum baudrate funcionou")
        
    def test_basic_commands(self):
        """Teste comandos básicos diferentes"""
        self.log_message("🧪 Testando comandos básicos...")
        
        test_commands = [
            # Comando original do manual
            "01 03 00 48 00 01 04 1C",
            # Tentativas com endereços diferentes
            "01 03 00 00 00 01 84 0A",  # Ler registrador 0
            "01 03 00 01 00 01 D5 CA",  # Ler registrador 1
            "01 04 00 00 00 01 31 CA",  # Input register 0
            "01 04 00 48 00 01 70 1F",  # Input register 0x48
            # Comando de identificação
            "01 03 00 00 00 0A C5 CD",  # Ler múltiplos registradores
        ]
        
        for cmd_str in test_commands:
            try:
                # Converter string hex para bytes
                cmd_bytes = bytes.fromhex(cmd_str.replace(" ", ""))
                self.log_message(f"Testando: {cmd_str}")
                response = self.send_modbus_command(cmd_bytes, delay_before=0.2)
                
                if response and len(response) > 0:
                    self.log_message("✅ RESPOSTA RECEBIDA para este comando!")
                    return
                    
            except Exception as e:
                self.log_message(f"❌ Erro no comando {cmd_str}: {e}")
                
            QApplication.processEvents()
            
        self.log_message("❌ Nenhum comando básico funcionou")
        
    def send_raw_command(self):
        """Envia comando raw inserido pelo usuário"""
        cmd_text = self.raw_command_input.text().strip()
        if not cmd_text:
            QMessageBox.warning(self, "Erro", "Digite um comando em hexadecimal")
            return
            
        try:
            # Converter para bytes
            cmd_bytes = bytes.fromhex(cmd_text.replace(" ", ""))
            response = self.send_modbus_command(cmd_bytes)
            
            if response and len(response) > 0:
                QMessageBox.information(self, "Sucesso", "Comando enviado e resposta recebida!")
            else:
                QMessageBox.warning(self, "Aviso", "Comando enviado mas sem resposta")
                
        except ValueError:
            QMessageBox.critical(self, "Erro", "Formato hexadecimal inválido")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao enviar comando: {e}")
        
    def test_communication(self):
        """Teste inicial de comunicação"""
        self.log_message("🧪 Testando comunicação...")
        temp = self.read_temperature()
        if temp is not None:
            self.log_message("✅ Comunicação OK")
        else:
            self.log_message("⚠️ Falha na comunicação - Execute diagnósticos")
        
    def read_temperature(self):
        """Lê temperatura atual"""
        device_id = self.device_id_spin.value()
        command = bytes([device_id, 0x03, 0x00, 0x48, 0x00, 0x01])
        crc = self.calculate_crc(command)
        full_command = command + crc
        
        response = self.send_modbus_command(full_command)
        if response and len(response) >= 7:
            temp_raw = (response[3] << 8) | response[4]
            temperature = temp_raw / 10.0
            return temperature
        return None
        
    def set_mode(self):
        """Define modo de operação"""
        mode = self.mode_combo.currentText()
        device_id = self.device_id_spin.value()
        
        if mode == "INFINITE":
            command = bytes([device_id, 0x06, 0x00, 0x40, 0x00, 0x01])
            crc = self.calculate_crc(command)
            full_command = command + crc
            
            response = self.send_modbus_command(full_command)
            if response and len(response) >= 6:
                QMessageBox.information(self, "Sucesso", "Modo INFINITE definido")
                self.log_message("✅ Modo INFINITE configurado")
            else:
                QMessageBox.warning(self, "Erro", "Falha ao definir modo")
                self.log_message("❌ Falha ao configurar modo")
                
    def set_cycles(self):
        """Define número de ciclos"""
        cycles = self.cycles_spin.value()
        device_id = self.device_id_spin.value()
        
        command = bytes([device_id, 0x10, 0x00, 0x45, 0x00, 0x02, 0x04])
        command += bytes([0x00, 0x01, (cycles >> 8) & 0xFF, cycles & 0xFF])
        crc = self.calculate_crc(command)
        full_command = command + crc
        
        response = self.send_modbus_command(full_command)
        if response and len(response) >= 6:
            QMessageBox.information(self, "Sucesso", f"Ciclos definidos: {cycles}")
            self.log_message(f"✅ Ciclos configurados: {cycles}")
        else:
            QMessageBox.warning(self, "Erro", "Falha ao definir ciclos")
            self.log_message("❌ Falha ao configurar ciclos")
            
    def manual_trigger(self):
        """Executa trigger manual"""
        self.log_message("🎯 Trigger manual executado")
        QMessageBox.information(self, "Trigger", "Comando de trigger enviado")
        
    def read_sensors(self):
        """Lê sensores periodicamente"""
        temp = self.read_temperature()
        if temp is not None:
            self.temp_label.setText(f"Temperatura: {temp:.1f} °C")
            if temp > 100:
                self.temp_label.setStyleSheet("font-size: 14px; font-weight: bold; color: red;")
            else:
                self.temp_label.setStyleSheet("font-size: 14px; font-weight: bold; color: green;")
        else:
            self.temp_label.setText("Temperatura: -- °C (Erro)")
            self.temp_label.setStyleSheet("font-size: 14px; font-weight: bold; color: orange;")
            
    def log_message(self, message):
        """Adiciona mensagem ao log"""
        timestamp = QTime.currentTime().toString("hh:mm:ss")
        self.log_text.append(f"[{timestamp}] {message}")
        
        if self.auto_scroll_check.isChecked():
            scrollbar = self.log_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
        
    def clear_log(self):
        """Limpa o log"""
        self.log_text.clear()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AdhesiveApplicatorController()
    window.show()
    sys.exit(app.exec())
