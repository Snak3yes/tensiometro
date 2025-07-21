import sys
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QSpinBox, QPushButton, 
                            QGroupBox, QGridLayout, QTextEdit)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from pymodbus.client import ModbusTcpClient

class AbsoluteXYController(QMainWindow):
    def __init__(self):
        super().__init__()
        self.client = None
        self.connected = False
        
        # Endereços Modbus para controle absoluto X e Y
        self.addresses = {
            # Memórias de comando
            'M_X_MOVE': 600,    # Comando movimento absoluto X
            'M_Y_MOVE': 700,    # Comando movimento absoluto Y
            'M_X_HOME': 601,    # Comando HOME X
            'M_Y_HOME': 701,    # Comando HOME Y
            
            # Registradores X
            'D_X_POS': 600,     # Posição desejada X
            'D_X_FREQ': 610,    # Frequência X
            'D_X_CURRENT': 620, # Posição atual X
            
            # Registradores Y  
            'D_Y_POS': 700,     # Posição desejada Y
            'D_Y_FREQ': 710,    # Frequência Y
            'D_Y_CURRENT': 720, # Posição atual Y
            
            # Saídas físicas
            'Y_X_PULSE': 40960,  # Y0.0 - Pulso X
            'Y_X_DIR': 40961,    # Y0.1 - Direção X
            'Y_Y_PULSE': 40962,  # Y0.2 - Pulso Y
            'Y_Y_DIR': 40963,    # Y0.3 - Direção Y
        }
        
        # Posições atuais dos eixos
        self.current_positions = {'X': 0, 'Y': 0}
        
        self.init_ui()
        self.connect_plc()
        
        # Timer para atualização de status
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(500)  # Atualiza a cada 500ms
        
    def init_ui(self):
        self.setWindowTitle("Controle Absoluto X-Y - Exemplo Mínimo")
        self.setFixedSize(800, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Status de conexão
        self.status_label = QLabel("❌ Desconectado")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("QLabel { background-color: red; color: white; padding: 10px; font-weight: bold; }")
        main_layout.addWidget(self.status_label)
        
        # Layout dos eixos
        axes_layout = QHBoxLayout()
        
        # Controle do Eixo X
        x_group = self.create_axis_control("EIXO X", "X")
        axes_layout.addWidget(x_group)
        
        # Controle do Eixo Y
        y_group = self.create_axis_control("EIXO Y", "Y")
        axes_layout.addWidget(y_group)
        
        main_layout.addLayout(axes_layout)
        
        # Botão de emergência
        emergency_btn = QPushButton("PARADA DE EMERGÊNCIA")
        emergency_btn.setStyleSheet("QPushButton { background-color: red; color: white; padding: 15px; font-weight: bold; font-size: 14px; }")
        emergency_btn.clicked.connect(self.emergency_stop)
        main_layout.addWidget(emergency_btn)
        
        # Log
        log_label = QLabel("Log de Eventos:")
        log_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        main_layout.addWidget(log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setFont(QFont("Consolas", 9))
        main_layout.addWidget(self.log_text)
        
    def create_axis_control(self, title, axis):
        """Cria controle para um eixo (X ou Y)"""
        group = QGroupBox(title)
        group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 14px; }")
        layout = QVBoxLayout()
        
        # Parâmetros
        params_layout = QGridLayout()
        
        # Posição desejada
        params_layout.addWidget(QLabel("Posição Desejada:"), 0, 0)
        pos_spin = QSpinBox()
        pos_spin.setRange(-1_000_000, 1_000_000)
        pos_spin.setValue(0)
        pos_spin.setToolTip("Coordenada absoluta de destino")
        params_layout.addWidget(pos_spin, 0, 1)
        setattr(self, f'{axis.lower()}_pos_spin', pos_spin)
        
        # Frequência
        params_layout.addWidget(QLabel("Frequência (Hz):"), 1, 0)
        freq_spin = QSpinBox()
        freq_spin.setRange(100, 50000)
        freq_spin.setValue(2000)
        freq_spin.setToolTip("Frequência de pulsos (Hz)")
        params_layout.addWidget(freq_spin, 1, 1)
        setattr(self, f'{axis.lower()}_freq_spin', freq_spin)
        
        # Posição atual (display)
        params_layout.addWidget(QLabel("Posição Atual:"), 2, 0)
        current_label = QLabel("0")
        current_label.setStyleSheet("QLabel { background-color: lightblue; padding: 8px; font-weight: bold; font-size: 12px; }")
        params_layout.addWidget(current_label, 2, 1)
        setattr(self, f'{axis.lower()}_current_label', current_label)
        
        layout.addLayout(params_layout)
        
        # Botões de movimento
        move_btn = QPushButton(f"MOVER {axis} PARA POSIÇÃO")
        move_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; padding: 10px; font-weight: bold; }")
        move_btn.clicked.connect(lambda: self.move_to_position(axis))
        layout.addWidget(move_btn)
        
        # Botão HOME
        home_btn = QPushButton(f"HOME {axis} (Pos 0)")
        home_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 8px; }")
        home_btn.clicked.connect(lambda: self.move_to_home(axis))
        layout.addWidget(home_btn)
        
        # Botões de posições pré-definidas
        presets_layout = QHBoxLayout()
        
        pos_1000_btn = QPushButton("→ 1000")
        pos_1000_btn.clicked.connect(lambda: self.move_to_preset(axis, 1000))
        presets_layout.addWidget(pos_1000_btn)
        
        pos_5000_btn = QPushButton("→ 5000")
        pos_5000_btn.clicked.connect(lambda: self.move_to_preset(axis, 5000))
        presets_layout.addWidget(pos_5000_btn)
        
        layout.addLayout(presets_layout)
        
        group.setLayout(layout)
        return group
        
    def connect_plc(self):
        """Conecta ao CLP"""
        try:
            self.log("Conectando ao CLP...")
            self.client = ModbusTcpClient('192.168.1.5', port=502)
            
            if self.client.connect():
                self.connected = True
                self.status_label.setText("✅ CONECTADO: 192.168.1.5:502")
                self.status_label.setStyleSheet("QLabel { background-color: green; color: white; padding: 10px; font-weight: bold; }")
                self.log("✅ Conectado com sucesso!")
            else:
                self.connected = False
                self.status_label.setText("❌ FALHA NA CONEXÃO")
                self.log("❌ Falha na conexão")
                
        except Exception as e:
            self.connected = False
            self.log(f"❌ Erro de conexão: {e}")
            
    def write_dword(self, address, value):
        """Escreve valor 32-bit em dois registradores consecutivos"""
        u32 = value & 0xFFFFFFFF
        lo = u32 & 0xFFFF
        hi = (u32 >> 16) & 0xFFFF
        return self.client.write_registers(address, [lo, hi])

    def read_dword(self, address):
        """Lê valor 32-bit de dois registradores consecutivos"""
        result = self.client.read_holding_registers(address, count=2)
        if result.isError():
            return 0
        lo, hi = result.registers
        u32 = (hi << 16) | lo
        return u32 if u32 < 0x80000000 else u32 - 0x100000000
        
    def move_to_position(self, axis):
        """Move eixo para posição absoluta especificada"""
        if not self.connected:
            self.log("❌ CLP não conectado")
            return
            
        try:
            if axis == 'X':
                position = self.x_pos_spin.value()
                frequency = self.x_freq_spin.value()
                pos_addr = self.addresses['D_X_POS']
                freq_addr = self.addresses['D_X_FREQ']
                cmd_addr = self.addresses['M_X_MOVE']
            else:  # axis == 'Y'
                position = self.y_pos_spin.value()
                frequency = self.y_freq_spin.value()
                pos_addr = self.addresses['D_Y_POS']
                freq_addr = self.addresses['D_Y_FREQ']
                cmd_addr = self.addresses['M_Y_MOVE']
                
            self.log(f"🎯 Movendo {axis} para posição {position} a {frequency}Hz")
            
            # Escreve parâmetros
            self.write_dword(pos_addr, position)
            self.write_dword(freq_addr, frequency)
            
            # Envia comando
            result = self.client.write_coil(cmd_addr, True)
            if not result.isError():
                self.log(f"✅ Comando enviado para eixo {axis}")
            else:
                self.log(f"❌ Erro ao enviar comando para eixo {axis}")
                
        except Exception as e:
            self.log(f"❌ Erro ao mover eixo {axis}: {e}")
            
    def move_to_home(self, axis):
        """Move eixo para posição HOME (0)"""
        if not self.connected:
            self.log("❌ CLP não conectado")
            return
            
        try:
            cmd_addr = self.addresses['M_X_HOME'] if axis == 'X' else self.addresses['M_Y_HOME']
            
            self.log(f"🏠 Movendo {axis} para HOME (posição 0)")
            result = self.client.write_coil(cmd_addr, True)
            
            if not result.isError():
                self.log(f"✅ Comando HOME enviado para eixo {axis}")
            else:
                self.log(f"❌ Erro ao enviar HOME para eixo {axis}")
                
        except Exception as e:
            self.log(f"❌ Erro HOME eixo {axis}: {e}")
            
    def move_to_preset(self, axis, position):
        """Move eixo para posição pré-definida"""
        if axis == 'X':
            self.x_pos_spin.setValue(position)
        else:
            self.y_pos_spin.setValue(position)
        self.move_to_position(axis)
        
    def emergency_stop(self):
        """Parada de emergência - desliga todos os comandos"""
        if not self.connected:
            return
            
        try:
            self.log("🛑 PARADA DE EMERGÊNCIA!")
            
            # Desliga todos os comandos
            commands = ['M_X_MOVE', 'M_Y_MOVE', 'M_X_HOME', 'M_Y_HOME']
            for cmd in commands:
                self.client.write_coil(self.addresses[cmd], False)
                
            self.log("✅ Todos os comandos foram desligados")
            
        except Exception as e:
            self.log(f"❌ Erro na parada de emergência: {e}")
            
    def update_status(self):
        """Atualiza status em tempo real"""
        if not self.connected:
            return
            
        try:
            # Lê posições atuais
            x_current = self.read_dword(self.addresses['D_X_CURRENT'])
            y_current = self.read_dword(self.addresses['D_Y_CURRENT'])
            
            # Atualiza cache e interface
            self.current_positions['X'] = x_current
            self.current_positions['Y'] = y_current
            
            self.x_current_label.setText(str(x_current))
            self.y_current_label.setText(str(y_current))
            
            # Muda cor se posição é zero (referência)
            x_color = "lightgreen" if x_current == 0 else "lightblue"
            y_color = "lightgreen" if y_current == 0 else "lightblue"
            
            self.x_current_label.setStyleSheet(f"QLabel {{ background-color: {x_color}; padding: 8px; font-weight: bold; font-size: 12px; }}")
            self.y_current_label.setStyleSheet(f"QLabel {{ background-color: {y_color}; padding: 8px; font-weight: bold; font-size: 12px; }}")
            
        except Exception as e:
            pass  # Silencia erros para não poluir o log
            
    def log(self, message):
        """Adiciona mensagem ao log"""
        timestamp = time.strftime('%H:%M:%S')
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        
        if hasattr(self, 'log_text'):
            self.log_text.append(log_message)
            # Limita linhas do log
            if self.log_text.document().lineCount() > 50:
                cursor = self.log_text.textCursor()
                cursor.movePosition(cursor.MoveOperation.Start)
                cursor.select(cursor.SelectionType.LineUnderCursor)
                cursor.removeSelectedText()
                
    def closeEvent(self, event):
        """Executa parada de emergência ao fechar"""
        if self.connected:
            self.emergency_stop()
            self.client.close()
        event.accept()

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = AbsoluteXYController()
    window.show()
    
    print("="*50)
    print("CONTROLE ABSOLUTO X-Y - EXEMPLO MÍNIMO")
    print("="*50)
    print("✅ Interface PyQt6 para controle absoluto")
    print("✅ Eixos X e Y com DDRVA")
    print("✅ Posicionamento absoluto")
    print("✅ Comandos HOME")
    print("✅ Comunicação Modbus TCP")
    print("="*50)
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
