import sys
import serial
import serial.tools.list_ports
import time
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

class MultiProtocolTester(QMainWindow):
    def __init__(self):
        super().__init__()
        self.serial_connection = None
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Testador Multi-Protocolo - AJC-10")
        self.setGeometry(100, 100, 1000, 700)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Header
        header = QLabel("🔧 TESTADOR MULTI-PROTOCOLO - Tentativas Alternativas")
        header.setStyleSheet("""
            background-color: #9C27B0; 
            color: white; 
            padding: 15px; 
            font-weight: bold; 
            font-size: 16px;
        """)
        layout.addWidget(header)
        
        # Configuração da porta
        port_group = QGroupBox("Configuração da Porta")
        port_layout = QGridLayout(port_group)
        
        self.port_combo = QComboBox()
        self.refresh_ports()
        
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.addItems(["1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200"])
        self.baudrate_combo.setCurrentText("115200")
        
        self.connect_btn = QPushButton("🔌 Conectar")
        self.connect_btn.clicked.connect(self.toggle_connection)
        
        port_layout.addWidget(QLabel("Porta:"), 0, 0)
        port_layout.addWidget(self.port_combo, 0, 1)
        port_layout.addWidget(QLabel("Baudrate:"), 0, 2)
        port_layout.addWidget(self.baudrate_combo, 0, 3)
        port_layout.addWidget(self.connect_btn, 1, 1)
        
        self.status_label = QLabel("📡 Status: Desconectado")
        self.status_label.setStyleSheet("font-weight: bold; color: red;")
        port_layout.addWidget(self.status_label, 1, 0, 1, 4)
        
        layout.addWidget(port_group)
        
        # Testes de protocolo
        protocol_group = QGroupBox("Testes de Protocolo Alternativos")
        protocol_layout = QGridLayout(protocol_group)
        
        # Teste 1: Modbus ASCII
        self.test_ascii_btn = QPushButton("📝 TESTE: Modbus ASCII")
        self.test_ascii_btn.clicked.connect(self.test_modbus_ascii)
        self.test_ascii_btn.setEnabled(False)
        self.test_ascii_btn.setStyleSheet("padding: 10px; font-weight: bold; background-color: #FF9800; color: white;")
        
        # Teste 2: Comandos simples
        self.test_simple_btn = QPushButton("🔤 TESTE: Comandos Texto Simples")
        self.test_simple_btn.clicked.connect(self.test_simple_commands)
        self.test_simple_btn.setEnabled(False)
        self.test_simple_btn.setStyleSheet("padding: 10px; font-weight: bold; background-color: #2196F3; color: white;")
        
        # Teste 3: Baudrates diferentes
        self.test_baudrates_btn = QPushButton("📡 TESTE: Todos os Baudrates")
        self.test_baudrates_btn.clicked.connect(self.test_all_baudrates)
        self.test_baudrates_btn.setEnabled(False)
        self.test_baudrates_btn.setStyleSheet("padding: 10px; font-weight: bold; background-color: #4CAF50; color: white;")
        
        # Teste 4: Sequências especiais
        self.test_special_btn = QPushButton("✨ TESTE: Sequências Especiais")
        self.test_special_btn.clicked.connect(self.test_special_sequences)
        self.test_special_btn.setEnabled(False)
        self.test_special_btn.setStyleSheet("padding: 10px; font-weight: bold; background-color: #E91E63; color: white;")
        
        # Teste 5: Device IDs alternativos
        self.test_devices_btn = QPushButton("🎯 TESTE: Device IDs 0-255")
        self.test_devices_btn.clicked.connect(self.test_all_device_ids)
        self.test_devices_btn.setEnabled(False)
        self.test_devices_btn.setStyleSheet("padding: 10px; font-weight: bold; background-color: #795548; color: white;")
        
        # Teste 6: Controle de fluxo
        self.test_handshake_btn = QPushButton("🤝 TESTE: Com Controle de Fluxo")
        self.test_handshake_btn.clicked.connect(self.test_handshake)
        self.test_handshake_btn.setEnabled(False)
        self.test_handshake_btn.setStyleSheet("padding: 10px; font-weight: bold; background-color: #607D8B; color: white;")
        
        protocol_layout.addWidget(self.test_ascii_btn, 0, 0)
        protocol_layout.addWidget(self.test_simple_btn, 0, 1)
        protocol_layout.addWidget(self.test_baudrates_btn, 1, 0)
        protocol_layout.addWidget(self.test_special_btn, 1, 1)
        protocol_layout.addWidget(self.test_devices_btn, 2, 0)
        protocol_layout.addWidget(self.test_handshake_btn, 2, 1)
        
        layout.addWidget(protocol_group)
        
        # Verificações de hardware
        hardware_group = QGroupBox("Verificações de Hardware")
        hardware_layout = QGridLayout(hardware_group)
        
        self.test_loopback_btn = QPushButton("🔄 TESTE: Loopback (TX→RX)")
        self.test_loopback_btn.clicked.connect(self.test_loopback)
        self.test_loopback_btn.setEnabled(False)
        
        self.test_signals_btn = QPushButton("📊 TESTE: Sinais RTS/DTR")
        self.test_signals_btn.clicked.connect(self.test_control_signals)
        self.test_signals_btn.setEnabled(False)
        
        self.test_break_btn = QPushButton("⚡ TESTE: Break Signal")
        self.test_break_btn.clicked.connect(self.test_break_signal)
        self.test_break_btn.setEnabled(False)
        
        hardware_layout.addWidget(self.test_loopback_btn, 0, 0)
        hardware_layout.addWidget(self.test_signals_btn, 0, 1)
        hardware_layout.addWidget(self.test_break_btn, 0, 2)
        
        layout.addWidget(hardware_group)
        
        # Log de resultados
        log_group = QGroupBox("Log de Testes")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(300)
        
        controls_layout = QHBoxLayout()
        self.clear_log_btn = QPushButton("🗑️ Limpar")
        self.clear_log_btn.clicked.connect(self.clear_log)
        self.save_log_btn = QPushButton("💾 Salvar")
        self.save_log_btn.clicked.connect(self.save_log)
        
        controls_layout.addWidget(self.clear_log_btn)
        controls_layout.addWidget(self.save_log_btn)
        controls_layout.addStretch()
        
        log_layout.addWidget(self.log_text)
        log_layout.addLayout(controls_layout)
        
        layout.addWidget(log_group)
        
    def refresh_ports(self):
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        
        for port in sorted(ports):
            port_text = f"{port.device}"
            if port.description:
                port_text += f" - {port.description}"
            self.port_combo.addItem(port_text, port.device)
            
    def toggle_connection(self):
        if self.serial_connection is None:
            self.connect_serial()
        else:
            self.disconnect_serial()
            
    def connect_serial(self):
        try:
            port_data = self.port_combo.currentData()
            baudrate = int(self.baudrate_combo.currentText())
            
            self.serial_connection = serial.Serial(
                port=port_data,
                baudrate=baudrate,
                bytesize=8,
                parity='N',
                stopbits=1,
                timeout=2.0
            )
            
            self.connect_btn.setText("🔌 Desconectar")
            self.status_label.setText("📡 Status: CONECTADO")
            self.status_label.setStyleSheet("font-weight: bold; color: green;")
            
            # Habilitar testes
            for btn in [self.test_ascii_btn, self.test_simple_btn, self.test_baudrates_btn,
                       self.test_special_btn, self.test_devices_btn, self.test_handshake_btn,
                       self.test_loopback_btn, self.test_signals_btn, self.test_break_btn]:
                btn.setEnabled(True)
                
            self.log_message("✅ CONECTADO!", "SUCCESS")
            self.log_message(f"📍 Porta: {port_data} @ {baudrate}", "INFO")
            
        except Exception as e:
            self.log_message(f"❌ ERRO: {e}", "ERROR")
            
    def disconnect_serial(self):
        if self.serial_connection:
            self.serial_connection.close()
            self.serial_connection = None
            
        self.connect_btn.setText("🔌 Conectar")
        self.status_label.setText("📡 Status: Desconectado")
        self.status_label.setStyleSheet("font-weight: bold; color: red;")
        
        for btn in [self.test_ascii_btn, self.test_simple_btn, self.test_baudrates_btn,
                   self.test_special_btn, self.test_devices_btn, self.test_handshake_btn,
                   self.test_loopback_btn, self.test_signals_btn, self.test_break_btn]:
            btn.setEnabled(False)
            
    def send_and_wait(self, data, description, wait_time=1.0):
        """Envia dados e aguarda resposta"""
        if not self.serial_connection:
            return None
            
        try:
            # Limpar buffers
            self.serial_connection.reset_input_buffer()
            self.serial_connection.reset_output_buffer()
            
            # Log do envio
            if isinstance(data, str):
                self.log_message(f"📤 {description}: '{data}'", "INFO")
                self.serial_connection.write(data.encode())
            else:
                hex_str = ' '.join([f'{b:02X}' for b in data])
                self.log_message(f"📤 {description}: {hex_str}", "INFO")
                self.serial_connection.write(data)
                
            # Aguardar resposta
            time.sleep(wait_time)
            response = self.serial_connection.read(100)
            
            if response:
                if all(32 <= b <= 126 for b in response):  # ASCII printável
                    self.log_message(f"📥 RESPOSTA: '{response.decode()}'", "SUCCESS")
                else:
                    hex_resp = ' '.join([f'{b:02X}' for b in response])
                    self.log_message(f"📥 RESPOSTA: {hex_resp}", "SUCCESS")
                return response
            else:
                self.log_message("⚠️ SEM RESPOSTA", "WARNING")
                return None
                
        except Exception as e:
            self.log_message(f"❌ ERRO: {e}", "ERROR")
            return None
            
    def test_modbus_ascii(self):
        """Teste Modbus ASCII ao invés de RTU"""
        self.log_message("=" * 60, "INFO")
        self.log_message("📝 TESTANDO MODBUS ASCII", "INFO")
        
        # Comandos Modbus ASCII (ao invés de RTU)
        ascii_commands = [
            ":010300480001F9\r\n",  # Leitura temperatura em ASCII
            ":010600400001B9\r\n",  # Modo INFINITE em ASCII
            ":0103004000010A\r\n"   # Leitura modo atual
        ]
        
        for cmd in ascii_commands:
            self.send_and_wait(cmd, "Modbus ASCII", 0.5)
            time.sleep(0.2)
            
    def test_simple_commands(self):
        """Teste comandos de texto simples"""
        self.log_message("=" * 60, "INFO")
        self.log_message("🔤 TESTANDO COMANDOS TEXTO SIMPLES", "INFO")
        
        simple_commands = [
            "TEMP\r\n", "temp\r\n", "STATUS\r\n", "status\r\n",
            "READ\r\n", "GET\r\n", "INFO\r\n", "VER\r\n",
            "?\r\n", "*IDN?\r\n", "HELP\r\n", "CMD\r\n",
            "START\r\n", "STOP\r\n", "SET\r\n", "GET\r\n"
        ]
        
        for cmd in simple_commands:
            self.send_and_wait(cmd, f"Texto Simples", 0.3)
            
    def test_all_baudrates(self):
        """Teste com diferentes baudrates"""
        self.log_message("=" * 60, "INFO")
        self.log_message("📡 TESTANDO TODOS OS BAUDRATES", "INFO")
        
        baudrates = [1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200]
        original_port = self.port_combo.currentData()
        
        for baudrate in baudrates:
            try:
                self.log_message(f"🔄 Testando {baudrate} bps...", "INFO")
                
                # Reconectar com novo baudrate
                if self.serial_connection:
                    self.serial_connection.close()
                    
                self.serial_connection = serial.Serial(
                    port=original_port,
                    baudrate=baudrate,
                    bytesize=8,
                    parity='N',
                    stopbits=1,
                    timeout=1.0
                )
                
                # Testar comando do manual
                cmd = bytes([0x01, 0x03, 0x00, 0x48, 0x00, 0x01, 0x04, 0x1C])
                response = self.send_and_wait(cmd, f"Modbus RTU @ {baudrate}", 0.5)
                
                if response:
                    self.log_message(f"🎉 POSSÍVEL BAUDRATE CORRETO: {baudrate}", "SUCCESS")
                    
            except Exception as e:
                self.log_message(f"❌ Erro em {baudrate}: {e}", "ERROR")
                
        # Restaurar conexão original
        try:
            if self.serial_connection:
                self.serial_connection.close()
            self.connect_serial()
        except:
            pass
            
    def test_special_sequences(self):
        """Teste sequências especiais"""
        self.log_message("=" * 60, "INFO")
        self.log_message("✨ TESTANDO SEQUÊNCIAS ESPECIAIS", "INFO")
        
        # Sequências de escape/wake-up
        special_sequences = [
            b'\x00\x00\x00',        # NULs
            b'\xFF\xFF\xFF',        # 0xFF
            b'\xAA\x55\xAA\x55',    # Alternating pattern
            b'\r\n\r\n',            # CRLF
            b'\x1B[',               # ESC sequence
            b'+++',                 # Hayes command
            b'\x05',                # ENQ
            b'\x06',                # ACK
            b'\x15',                # NAK
            b'\x04',                # EOT
        ]
        
        for seq in special_sequences:
            hex_str = ' '.join([f'{b:02X}' for b in seq])
            self.send_and_wait(seq, f"Sequência especial", 0.3)
            
    def test_all_device_ids(self):
        """Teste com diferentes Device IDs"""
        self.log_message("=" * 60, "INFO")
        self.log_message("🎯 TESTANDO DEVICE IDs 0-255", "INFO")
        
        found_devices = []
        
        for device_id in range(0, 256):
            if device_id % 50 == 0:
                self.log_message(f"🔄 Testando Device ID {device_id}...", "INFO")
                
            # Comando de leitura temperatura com Device ID variável
            cmd = bytes([device_id, 0x03, 0x00, 0x48, 0x00, 0x01])
            
            # Calcular CRC
            crc = self.calculate_crc(cmd)
            full_cmd = cmd + crc
            
            response = self.send_and_wait(full_cmd, f"Device ID {device_id}", 0.1)
            
            if response and len(response) > 0:
                self.log_message(f"🎉 DEVICE ID VÁLIDO ENCONTRADO: {device_id}", "SUCCESS")
                found_devices.append(device_id)
                
        if found_devices:
            self.log_message(f"✅ Device IDs encontrados: {found_devices}", "SUCCESS")
        else:
            self.log_message("❌ Nenhum Device ID respondeu", "WARNING")
            
    def test_handshake(self):
        """Teste com controle de fluxo"""
        self.log_message("=" * 60, "INFO")
        self.log_message("🤝 TESTANDO COM CONTROLE DE FLUXO", "INFO")
        
        try:
            # Reconectar com controle de fluxo
            port_data = self.port_combo.currentData()
            baudrate = int(self.baudrate_combo.currentText())
            
            if self.serial_connection:
                self.serial_connection.close()
                
            self.serial_connection = serial.Serial(
                port=port_data,
                baudrate=baudrate,
                bytesize=8,
                parity='N',
                stopbits=1,
                timeout=2.0,
                rtscts=True,    # Controle RTS/CTS
                dsrdtr=True     # Controle DSR/DTR
            )
            
            self.log_message("✅ Reconectado COM controle de fluxo", "INFO")
            
            # Testar comando
            cmd = bytes([0x01, 0x03, 0x00, 0x48, 0x00, 0x01, 0x04, 0x1C])
            self.send_and_wait(cmd, "Com controle de fluxo", 1.0)
            
        except Exception as e:
            self.log_message(f"❌ Erro: {e}", "ERROR")
            
    def test_loopback(self):
        """Teste de loopback"""
        self.log_message("=" * 60, "INFO")
        self.log_message("🔄 TESTANDO LOOPBACK", "INFO")
        
        test_data = b"LOOPBACK_TEST_123"
        response = self.send_and_wait(test_data, "Loopback", 0.5)
        
        if response == test_data:
            self.log_message("✅ LOOPBACK OK - Cabo funcionando", "SUCCESS")
        else:
            self.log_message("❌ LOOPBACK FALHOU - Problema no cabo ou aplicadora não faz eco", "WARNING")
            
    def test_control_signals(self):
        """Teste sinais de controle"""
        self.log_message("=" * 60, "INFO")
        self.log_message("📊 TESTANDO SINAIS RTS/DTR", "INFO")
        
        if not self.serial_connection:
            return
            
        try:
            # Testar diferentes combinações de RTS/DTR
            combinations = [
                (True, True),   # RTS=1, DTR=1
                (True, False),  # RTS=1, DTR=0
                (False, True),  # RTS=0, DTR=1
                (False, False)  # RTS=0, DTR=0
            ]
            
            for rts, dtr in combinations:
                self.serial_connection.rts = rts
                self.serial_connection.dtr = dtr
                self.log_message(f"🔧 RTS={rts}, DTR={dtr}", "INFO")
                
                # Testar comando
                cmd = bytes([0x01, 0x03, 0x00, 0x48, 0x00, 0x01, 0x04, 0x1C])
                self.send_and_wait(cmd, f"RTS={rts},DTR={dtr}", 0.5)
                
        except Exception as e:
            self.log_message(f"❌ Erro: {e}", "ERROR")
            
    def test_break_signal(self):
        """Teste break signal"""
        self.log_message("=" * 60, "INFO")
        self.log_message("⚡ TESTANDO BREAK SIGNAL", "INFO")
        
        if not self.serial_connection:
            return
            
        try:
            # Enviar break signal
            self.serial_connection.send_break(0.25)  # 250ms break
            time.sleep(0.5)
            
            # Testar comando após break
            cmd = bytes([0x01, 0x03, 0x00, 0x48, 0x00, 0x01, 0x04, 0x1C])
            self.send_and_wait(cmd, "Após Break Signal", 1.0)
            
        except Exception as e:
            self.log_message(f"❌ Erro: {e}", "ERROR")
            
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
        
    def log_message(self, message, level="INFO"):
        """Log com cores"""
        timestamp = QTime.currentTime().toString("hh:mm:ss")
        
        colors = {
            "SUCCESS": "green",
            "ERROR": "red", 
            "WARNING": "orange",
            "INFO": "black"
        }
        
        color = colors.get(level, "black")
        formatted = f'<span style="color: {color};">[{timestamp}] {message}</span>'
        self.log_text.append(formatted)
        
        # Auto-scroll
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)
        
    def clear_log(self):
        self.log_text.clear()
        
    def save_log(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Salvar Log", 
            f"multi_protocol_test.txt",
            "Text Files (*.txt)"
        )
        
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.log_text.toPlainText())
                
    def closeEvent(self, event):
        if self.serial_connection:
            self.disconnect_serial()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MultiProtocolTester()
    window.show()
    sys.exit(app.exec())
