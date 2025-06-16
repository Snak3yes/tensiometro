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
        self.setWindowTitle("Controlador Aplicadora AJC-10 - Configuração Correta")
        self.setGeometry(100, 100, 1000, 800)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Aviso sobre configurações
        warning_label = QLabel("⚠️ USANDO CONFIGURAÇÕES DO MANUAL: 115200 bps, 8-N-1, Device ID=1")
        warning_label.setStyleSheet("background-color: yellow; padding: 10px; font-weight: bold;")
        layout.addWidget(warning_label)
        
        # Seção de Conexão
        conn_group = QGroupBox("Conexão Serial")
        conn_layout = QGridLayout(conn_group)
        
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(350)
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
        
        # Testes rápidos
        test_group = QGroupBox("Testes Rápidos")
        test_layout = QGridLayout(test_group)
        
        self.test_temp_btn = QPushButton("🌡️ Testar Leitura Temperatura")
        self.test_temp_btn.clicked.connect(self.test_temperature_read)
        self.test_temp_btn.setEnabled(False)
        
        self.test_mode_btn = QPushButton("🔄 Testar Modo INFINITE")
        self.test_mode_btn.clicked.connect(self.test_infinite_mode)
        self.test_mode_btn.setEnabled(False)
        
        self.manual_commands_btn = QPushButton("📋 Comandos do Manual")
        self.manual_commands_btn.clicked.connect(self.test_manual_commands)
        self.manual_commands_btn.setEnabled(False)
        
        test_layout.addWidget(self.test_temp_btn, 0, 0)
        test_layout.addWidget(self.test_mode_btn, 0, 1)
        test_layout.addWidget(self.manual_commands_btn, 1, 0, 1, 2)
        
        # Monitoramento
        monitor_group = QGroupBox("Monitoramento em Tempo Real")
        monitor_layout = QGridLayout(monitor_group)
        
        self.temp_label = QLabel("Temperatura: -- °C")
        self.temp_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.mode_label = QLabel("Modo: --")
        self.cycle_label = QLabel("Ciclos: --")
        self.last_command_label = QLabel("Último Comando: --")
        
        monitor_layout.addWidget(self.temp_label, 0, 0)
        monitor_layout.addWidget(self.mode_label, 0, 1)
        monitor_layout.addWidget(self.cycle_label, 1, 0)
        monitor_layout.addWidget(self.last_command_label, 1, 1)
        
        # Controles operacionais
        control_group = QGroupBox("Controles Operacionais")
        control_layout = QGridLayout(control_group)
        
        # Modo
        self.set_infinite_btn = QPushButton("Definir Modo INFINITE")
        self.set_infinite_btn.clicked.connect(self.set_infinite_mode)
        self.set_infinite_btn.setEnabled(False)
        self.set_infinite_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        
        # Ciclos
        self.cycles_spin = QSpinBox()
        self.cycles_spin.setRange(1, 65535)
        self.cycles_spin.setValue(99)  # Valor do exemplo do manual
        self.set_cycles_btn = QPushButton("Definir Ciclos")
        self.set_cycles_btn.clicked.connect(self.set_cycles)
        self.set_cycles_btn.setEnabled(False)
        
        # Comando raw
        self.raw_cmd_input = QLineEdit()
        self.raw_cmd_input.setPlaceholderText("Ex: 01 03 00 48 00 01 04 1C")
        self.send_raw_btn = QPushButton("Enviar Comando Raw")
        self.send_raw_btn.clicked.connect(self.send_raw_command)
        self.send_raw_btn.setEnabled(False)
        
        control_layout.addWidget(self.set_infinite_btn, 0, 0, 1, 2)
        control_layout.addWidget(QLabel("Ciclos:"), 1, 0)
        control_layout.addWidget(self.cycles_spin, 1, 1)
        control_layout.addWidget(self.set_cycles_btn, 1, 2)
        control_layout.addWidget(QLabel("Comando Raw:"), 2, 0)
        control_layout.addWidget(self.raw_cmd_input, 2, 1)
        control_layout.addWidget(self.send_raw_btn, 2, 2)
        
        # Log melhorado
        log_group = QGroupBox("Log de Comunicação Detalhado")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(250)
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Courier", 9))
        
        log_controls = QHBoxLayout()
        self.clear_log_btn = QPushButton("Limpar Log")
        self.clear_log_btn.clicked.connect(self.clear_log)
        self.save_log_btn = QPushButton("Salvar Log")
        self.save_log_btn.clicked.connect(self.save_log)
        
        log_controls.addWidget(self.clear_log_btn)
        log_controls.addWidget(self.save_log_btn)
        log_controls.addStretch()
        
        log_layout.addWidget(self.log_text)
        log_layout.addLayout(log_controls)
        
        # Adicionar todos os grupos
        layout.addWidget(conn_group)
        layout.addWidget(config_group)
        layout.addWidget(test_group)
        layout.addWidget(monitor_group)
        layout.addWidget(control_group)
        layout.addWidget(log_group)
        
        # Timer para monitoramento
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.monitor_device)
        
    def refresh_ports(self):
        """Atualiza portas COM"""
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        
        if not ports:
            self.port_combo.addItem("Nenhuma porta encontrada")
            self.log_message("❌ Nenhuma porta COM encontrada")
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
                self.log_message(f"🔌 Porta USB-Serial encontrada: {port_info}")
                
        self.log_message(f"🔍 Total: {len(ports)} porta(s) COM")
        
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
                
            # Configurações EXATAS do manual
            self.serial_connection = serial.Serial(
                port=port,
                baudrate=115200,  # FIXO conforme manual
                bytesize=8,       # FIXO conforme manual
                parity='N',       # FIXO conforme manual (sem paridade)
                stopbits=1,       # FIXO conforme manual
                timeout=3.0,      # Timeout aumentado
                rtscts=False,     # Sem controle de fluxo
                dsrdtr=False      # Sem controle de fluxo
            )
            
            # Aguardar estabilização
            time.sleep(0.2)
            
            self.status_label.setText("Conectado")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            self.connect_btn.setText("Desconectar")
            
            # Habilitar controles
            self.test_temp_btn.setEnabled(True)
            self.test_mode_btn.setEnabled(True)
            self.manual_commands_btn.setEnabled(True)
            self.set_infinite_btn.setEnabled(True)
            self.set_cycles_btn.setEnabled(True)
            self.send_raw_btn.setEnabled(True)
            
            self.log_message(f"✅ CONECTADO: {port} @ 115200-8-N-1")
            self.log_message("📡 Configurações conforme manual AJC-10")
            
            # Teste automático após conexão
            QTimer.singleShot(500, self.auto_test_connection)
            
        except Exception as e:
            QMessageBox.critical(self, "Erro de Conexão", f"Erro: {e}")
            self.log_message(f"❌ ERRO: {e}")
            
    def disconnect_serial(self):
        if self.serial_connection:
            self.monitor_timer.stop()
            self.serial_connection.close()
            self.serial_connection = None
            
            self.status_label.setText("Desconectado")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.connect_btn.setText("Conectar")
            
            # Desabilitar controles
            self.test_temp_btn.setEnabled(False)
            self.test_mode_btn.setEnabled(False)
            self.manual_commands_btn.setEnabled(False)
            self.set_infinite_btn.setEnabled(False)
            self.set_cycles_btn.setEnabled(False)
            self.send_raw_btn.setEnabled(False)
            
            self.log_message("🔌 Desconectado")
            
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
            self.log_message(f"📤 TX {description}: {cmd_hex_string}")
            
            # Enviar comando
            self.serial_connection.write(cmd_bytes)
            
            # Aguardar resposta
            time.sleep(0.1)  # Pequena pausa
            response = self.serial_connection.read(50)
            
            if response:
                resp_hex = ' '.join([f'{b:02X}' for b in response])
                self.log_message(f"📥 RX ({len(response)} bytes): {resp_hex}")
                self.last_command_label.setText(f"Último: {description} - OK")
                return response
            else:
                self.log_message("⚠️ SEM RESPOSTA")
                self.last_command_label.setText(f"Último: {description} - SEM RESPOSTA")
                return None
                
        except Exception as e:
            self.log_message(f"❌ ERRO: {e}")
            return None
            
    def auto_test_connection(self):
        """Teste automático ao conectar"""
        self.log_message("🧪 TESTE AUTOMÁTICO DE CONEXÃO...")
        
        # Teste 1: Leitura de temperatura (comando do manual)
        response = self.send_command("01 03 00 48 00 01 04 1C", "Leitura Temperatura")
        
        if response and len(response) >= 7:
            self.log_message("🎉 COMUNICAÇÃO ESTABELECIDA COM SUCESSO!")
            self.parse_temperature_response(response)
            self.monitor_timer.start(3000)  # Monitorar a cada 3 segundos
        else:
            self.log_message("❌ FALHA NA COMUNICAÇÃO")
            QMessageBox.warning(self, "Falha", "Não foi possível estabelecer comunicação.\nVerifique:\n• Equipamento ligado\n• Cabo conectado\n• Porta correta")
            
    def test_temperature_read(self):
        """Teste manual de leitura de temperatura"""
        response = self.send_command("01 03 00 48 00 01 04 1C", "Teste Temperatura")
        if response:
            self.parse_temperature_response(response)
            
    def test_infinite_mode(self):
        """Teste do modo INFINITE"""
        response = self.send_command("01 06 00 40 00 01 49 00", "Teste Modo INFINITE")
        if response and len(response) >= 8:
            # Verificar se resposta confere
            expected = bytes.fromhex("01 06 00 40 00 01 49 00")
            if response[:8] == expected:
                self.log_message("✅ MODO INFINITE CONFIGURADO!")
                self.mode_label.setText("Modo: INFINITE")
                QMessageBox.information(self, "Sucesso", "Modo INFINITE definido com sucesso!")
            else:
                self.log_message("⚠️ Resposta inesperada")
        else:
            self.log_message("❌ Falha ao definir modo")
            
    def test_manual_commands(self):
        """Testa todos os comandos do manual"""
        self.log_message("📋 TESTANDO COMANDOS DO MANUAL...")
        
        commands = [
            ("01 03 00 48 00 01 04 1C", "Leitura Temperatura"),
            ("01 06 00 40 00 01 49 00", "Modo INFINITE"),
            ("01 10 00 45 00 02 04 00 01 00 99 86 0A", "Definir 99 Ciclos")
        ]
        
        success_count = 0
        for cmd, desc in commands:
            response = self.send_command(cmd, desc)
            if response and len(response) > 0:
                success_count += 1
                time.sleep(0.3)  # Pausa entre comandos
                
        self.log_message(f"📊 RESULTADO: {success_count}/{len(commands)} comandos funcionaram")
        
    def set_infinite_mode(self):
        """Define modo INFINITE"""
        response = self.send_command("01 06 00 40 00 01 49 00", "Configurar INFINITE")
        if response:
            expected = bytes.fromhex("01 06 00 40 00 01 49 00")
            if len(response) >= 8 and response[:8] == expected:
                QMessageBox.information(self, "Sucesso", "Modo INFINITE definido!\nVerifique o display da aplicadora.")
                self.mode_label.setText("Modo: INFINITE")
            else:
                QMessageBox.warning(self, "Aviso", "Comando enviado mas resposta inesperada")
                
    def set_cycles(self):
        """Define número de ciclos"""
        cycles = self.cycles_spin.value()
        
        # Construir comando conforme manual
        # Formato: 01 10 00 45 00 02 04 00 01 [HIGH] [LOW] [CRC]
        high_byte = (cycles >> 8) & 0xFF
        low_byte = cycles & 0xFF
        
        cmd_base = f"01 10 00 45 00 02 04 00 01 {high_byte:02X} {low_byte:02X}"
        
        # Calcular CRC
        cmd_bytes = bytes.fromhex(cmd_base.replace(" ", ""))
        crc = self.calculate_crc(cmd_bytes)
        crc_hex = f"{crc[0]:02X} {crc[1]:02X}"
        
        full_cmd = f"{cmd_base} {crc_hex}"
        
        response = self.send_command(full_cmd, f"Definir {cycles} Ciclos")
        if response and len(response) >= 6:
            QMessageBox.information(self, "Sucesso", f"Ciclos definidos: {cycles}")
            self.cycle_label.setText(f"Ciclos: {cycles}")
        else:
            QMessageBox.warning(self, "Erro", "Falha ao definir ciclos")
            
    def send_raw_command(self):
        """Envia comando raw"""
        cmd = self.raw_cmd_input.text().strip()
        if not cmd:
            QMessageBox.warning(self, "Erro", "Digite um comando")
            return
            
        response = self.send_command(cmd, "Comando Raw")
        if response:
            QMessageBox.information(self, "Enviado", f"Comando enviado. Resposta: {len(response)} bytes")
        else:
            QMessageBox.warning(self, "Sem Resposta", "Comando enviado mas sem resposta")
            
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
                
            self.log_message(f"🌡️ Temperatura atual: {temperature:.1f}°C")
            
    def monitor_device(self):
        """Monitoramento contínuo"""
        response = self.send_command("01 03 00 48 00 01 04 1C", "Monitor")
        if response:
            self.parse_temperature_response(response)
            
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
        """Log com timestamp"""
        timestamp = QTime.currentTime().toString("hh:mm:ss")
        self.log_text.append(f"[{timestamp}] {message}")
        
        # Auto scroll
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def clear_log(self):
        """Limpa log"""
        self.log_text.clear()
        
    def save_log(self):
        """Salva log"""
        filename, _ = QFileDialog.getSaveFileName(self, "Salvar Log", "log_aplicadora.txt", "Text Files (*.txt)")
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.log_text.toPlainText())
            QMessageBox.information(self, "Salvo", f"Log salvo em: {filename}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AdhesiveApplicatorController()
    window.show()
    sys.exit(app.exec())
