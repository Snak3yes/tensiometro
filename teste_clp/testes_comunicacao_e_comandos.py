import sys
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QSpinBox, QPushButton, 
                            QGroupBox, QGridLayout, QTabWidget, QTextEdit,
                            QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from pymodbus.client import ModbusTcpClient

class MultiAxisMotorController(QMainWindow):
    def __init__(self):
        super().__init__()
        self.client = None
        self.connected = False
        
        # Endereços Modbus CORRIGIDOS
        self.addresses = {
            # Memórias M
            'M300': 300,      # eixo-Y2
            'M200': 200,      # eixo-Z
            'M400': 400,      # eixo-Y1   
            'M500': 500,      # eixo-X    
            'M30': 30,        # M30
            'M50': 50,        # M50  ← usado para acionar Y0.10
            
            # Registradores D
            'D110': 110, 'D120': 120,       # eixo-Y2
            'D200': 200, 'D210': 210,       # eixo-Z
            'D400': 400, 'D410': 410,       # eixo-Y1  
            'D500': 500, 'D510': 510,       # eixo-X   
            
            # Saídas Y - CORRIGIDAS
            'Y00': 40960, 'Y01': 40961,     # Y0.0 / Y0.1  eixo-Y2
            'Y02': 40962, 'Y03': 40963,     # Y0.2 / Y0.3  eixo-Z
            'Y04': 40964, 'Y05': 40965,     # Y0.4 / Y0.5  eixo-Y1 (novo)
            'Y06': 40966, 'Y07': 40967,     # Y0.6 / Y0.7  eixo-X  (novo)
            'Y010': 40971                   # Y0.10 = 040972-1 = 40971
        }
        
        self.init_ui()
        self.connect_plc()
        
        # Timer para atualização
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(300)
        
    def log(self, msg):
        """Log no terminal e na interface"""
        timestamp = time.strftime('%H:%M:%S')
        log_msg = f"[{timestamp}] {msg}"
        print(log_msg)
        
        if hasattr(self, 'log_text'):
            self.log_text.append(log_msg)
            if self.log_text.document().lineCount() > 100:
                cursor = self.log_text.textCursor()
                cursor.movePosition(cursor.MoveOperation.Start)
                cursor.select(cursor.SelectionType.LineUnderCursor)
                cursor.removeSelectedText()
        
    def init_ui(self):
        self.setWindowTitle("Controle Multi-Eixos - Delta AS (FINAL CORRIGIDO)")
        self.setMinimumSize(900, 700)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Status de conexão
        self.status_label = QLabel("Desconectado")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("QLabel { background-color: red; color: white; padding: 10px; font-weight: bold; }")
        layout.addWidget(self.status_label)
        
        # Abas para organizar
        tab_widget = QTabWidget()

        # === ABA 0: JOG MANUAL  (fica à ESQUERDA) ===
        jog_tab = QWidget()
        jog_layout = QVBoxLayout(jog_tab)

        # valor de passo do JOG
        step_frame = QHBoxLayout()
        step_frame.addWidget(QLabel("Passo (pulsos):"))
        self.jog_step_spin = QSpinBox()
        self.jog_step_spin.setRange(1, 100_000)
        self.jog_step_spin.setValue(500)
        step_frame.addWidget(self.jog_step_spin)
        step_frame.addStretch()
        jog_layout.addLayout(step_frame)

        grid = QGridLayout()
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(20)

        # --- linha superior ( + )
        btn_y1_p = QPushButton("Y1 +")
        btn_y2_p = QPushButton("Y2 +")
        btn_z_p  = QPushButton("Z  +")
        grid.addWidget(btn_y1_p, 0, 1)
        grid.addWidget(btn_y2_p, 0, 2)
        grid.addWidget(btn_z_p,  0, 3)

        # --- linha do meio (X- / X+)
        btn_x_m  = QPushButton("X  −")
        btn_x_p  = QPushButton("X  +")
        grid.addWidget(btn_x_m, 1, 0)
        grid.addWidget(btn_x_p, 1, 4)

        # --- linha inferior ( − )
        btn_y1_m = QPushButton("Y1 −")
        btn_y2_m = QPushButton("Y2 −")
        btn_z_m  = QPushButton("Z  −")
        grid.addWidget(btn_y1_m, 2, 1)
        grid.addWidget(btn_y2_m, 2, 2)
        grid.addWidget(btn_z_m,  2, 3)

        # ligações
        btn_y1_p.clicked.connect(lambda: self.jog_move(3, 'forward'))
        btn_y1_m.clicked.connect(lambda: self.jog_move(3, 'reverse'))
        btn_y2_p.clicked.connect(lambda: self.jog_move(1, 'forward'))
        btn_y2_m.clicked.connect(lambda: self.jog_move(1, 'reverse'))
        btn_z_p.clicked.connect( lambda: self.jog_move(2, 'forward'))
        btn_z_m.clicked.connect( lambda: self.jog_move(2, 'reverse'))
        btn_x_p.clicked.connect( lambda: self.jog_move(4, 'forward'))
        btn_x_m.clicked.connect( lambda: self.jog_move(4, 'reverse'))

        # estilinho
        for b in [btn_y1_p, btn_y1_m, btn_y2_p, btn_y2_m,
                  btn_z_p,  btn_z_m,  btn_x_p, btn_x_m]:
            b.setMinimumSize(90, 60)
            b.setStyleSheet("QPushButton { font-weight:bold; font-size:15px; }")

        jog_layout.addLayout(grid)
        jog_layout.addStretch()

        tab_widget.addTab(jog_tab, "Jog Manual")
        
        # === ABA 1: CONTROLE DOS EIXOS ===
        control_tab = QWidget()
        control_layout = QHBoxLayout(control_tab)
        
        # Eixo 1 (Y2)
        axis1_group = self.create_axis_control("EIXO 1 (Y2)", 1)
        control_layout.addWidget(axis1_group)
        
        # Eixo 2 (Z)
        axis2_group = self.create_axis_control("EIXO 2 (Z)", 2)
        control_layout.addWidget(axis2_group)

        # Eixo 3 (Y1)
        axis3_group = self.create_axis_control("EIXO 3 (Y1)", 3)
        control_layout.addWidget(axis3_group)

        # Eixo 4 (X)
        axis4_group = self.create_axis_control("EIXO 4 (X)", 4)
        control_layout.addWidget(axis4_group)
        
        # Controles auxiliares
        aux_group = self.create_auxiliary_controls()
        control_layout.addWidget(aux_group)
        
        tab_widget.addTab(control_tab, "Controle de Eixos")
        
        # === ABA 2: STATUS ===
        status_tab = QWidget()
        status_layout = QVBoxLayout(status_tab)
        
        # Status das saídas
        outputs_group = self.create_outputs_status()
        status_layout.addWidget(outputs_group)
        
        # Status das memórias
        memories_group = self.create_memories_status()
        status_layout.addWidget(memories_group)
        
        # Status dos registradores
        registers_group = self.create_registers_status()
        status_layout.addWidget(registers_group)
        
        tab_widget.addTab(status_tab, "Status do Sistema")
        
        # === ABA 3: LOG ===
        log_tab = QWidget()
        log_layout = QVBoxLayout(log_tab)
        
        log_label = QLabel("Log de Eventos:")
        log_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        log_layout.addWidget(log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        log_layout.addWidget(self.log_text)
        
        clear_log_btn = QPushButton("Limpar Log")
        clear_log_btn.clicked.connect(self.log_text.clear)
        log_layout.addWidget(clear_log_btn)
        
        tab_widget.addTab(log_tab, "Log")
        
        layout.addWidget(tab_widget)
        
    def create_axis_control(self, title, axis_num):
        """Cria controle para um eixo - CORRIGIDO para valores absolutos"""
        group = QGroupBox(title)
        group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 12px; }")
        layout = QVBoxLayout()
        
        # Parâmetros
        params_frame = QFrame()
        params_layout = QGridLayout(params_frame)
        
        addr_map = {
            1: ('D110', 'D120'),   # Y2
            2: ('D200', 'D210'),   # Z
            3: ('D400', 'D410'),   # Y1
            4: ('D500', 'D510')    # X
        }
        pulsos_addr, vel_addr = addr_map[axis_num]
        default_pulsos = 1000
            
        # Pulsos 32-bits (aceita valores negativos)
        params_layout.addWidget(QLabel(f"{pulsos_addr} - Pulsos:"), 0, 0)
        pulsos_spin = QSpinBox()
        pulsos_spin.setRange(-2_000_000_000, 2_000_000_000)
        pulsos_spin.setValue(default_pulsos)
        pulsos_spin.setToolTip("Valor INT32 (negativo → sentido inverso)")
        params_layout.addWidget(pulsos_spin, 0, 1)
        setattr(self, f'pulsos_spin_{axis_num}', pulsos_spin)
        
        # Velocidade
        params_layout.addWidget(QLabel(f"{vel_addr} - Velocidade:"), 1, 0)
        vel_spin = QSpinBox()
        vel_spin.setRange(100, 2_000_000_000)
        vel_spin.setValue(1000)
        params_layout.addWidget(vel_spin, 1, 1)
        setattr(self, f'vel_spin_{axis_num}', vel_spin)
        
        layout.addWidget(params_frame)
        
        # Botões de escrita
        write_btn = QPushButton("Escrever Parâmetros")
        write_btn.clicked.connect(lambda: self.write_axis_parameters(axis_num))
        layout.addWidget(write_btn)
        
        # Botões de movimento com DIREÇÃO
        move_frame = QFrame()
        move_layout = QGridLayout(move_frame)
        
        # Movimento FORWARD
        move_fwd_btn = QPushButton(f"MOVER FORWARD →")
        move_fwd_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 10px; font-weight: bold; }")
        move_fwd_btn.clicked.connect(lambda: self.move_axis(axis_num, direction='forward'))
        move_layout.addWidget(move_fwd_btn, 0, 0)
        
        # Movimento REVERSE
        move_rev_btn = QPushButton(f"MOVER REVERSE ←")
        move_rev_btn.setStyleSheet("QPushButton { background-color: #FF9800; color: white; padding: 10px; font-weight: bold; }")
        move_rev_btn.clicked.connect(lambda: self.move_axis(axis_num, direction='reverse'))
        move_layout.addWidget(move_rev_btn, 0, 1)
        
        # Botões de movimento rápido
        quick_fwd_btn = QPushButton("Quick 1000 →")
        quick_fwd_btn.clicked.connect(lambda: self.quick_move(axis_num, 1000, 'forward'))
        move_layout.addWidget(quick_fwd_btn, 1, 0)
        
        quick_rev_btn = QPushButton("Quick 1000 ←")
        quick_rev_btn.clicked.connect(lambda: self.quick_move(axis_num, 1000, 'reverse'))
        move_layout.addWidget(quick_rev_btn, 1, 1)
        
        layout.addWidget(move_frame)
        
        group.setLayout(layout)
        return group
        
    def create_auxiliary_controls(self):
        """Cria controles auxiliares - Y0.10 CORRIGIDO"""
        group = QGroupBox("CONTROLES AUXILIARES")
        group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 12px; }")
        layout = QVBoxLayout()
        
        # Saída Y0.10  ─ comando tipo “falling-edge trigger”
        y010_btn = QPushButton("SHOT (M50)")
        y010_btn.setCheckable(True)                     # mantém o efeito “afundar”
        y010_btn.clicked.connect(self.pulse_y010)       # novo handler momentâneo
        y010_btn.setStyleSheet("QPushButton:checked { background-color: orange; }")
        layout.addWidget(y010_btn)
        setattr(self, 'y010_btn', y010_btn)
        
        # Info do endereço
        info_label = QLabel("Y0.10 é comandado por M50 (coil 50)")
        info_label.setStyleSheet("QLabel { color: gray; font-size: 9px; }")
        layout.addWidget(info_label)
        
        # M100 auxiliar
        m100_btn = QPushButton("M100 - Auxiliar")
        m100_btn.clicked.connect(self.pulse_m100)
        layout.addWidget(m100_btn)
        
        # Parada de emergência
        stop_btn = QPushButton("PARADA DE EMERGÊNCIA")
        stop_btn.setStyleSheet("QPushButton { background-color: red; color: white; padding: 15px; font-weight: bold; }")
        stop_btn.clicked.connect(self.emergency_stop)
        layout.addWidget(stop_btn)
        
        group.setLayout(layout)
        return group
        
    def create_outputs_status(self):
        """Cria status das saídas"""
        group = QGroupBox("STATUS DAS SAÍDAS")
        layout = QGridLayout()
        
        outputs = [
            ('Y0.0', 'Pulso Eixo 1'),
            ('Y0.1', 'Dir Eixo 1'),
            ('Y0.2', 'Pulso Eixo 2'), 
            ('Y0.3', 'Dir Eixo 2'),
            ('Y0.4', 'Pulso Eixo 3'),
            ('Y0.5', 'Dir Eixo 3'),
            ('Y0.6', 'Pulso Eixo 4'),
            ('Y0.7', 'Dir Eixo 4'),
            ('Y0.10', 'Auxiliar')
        ]
        
        for i, (name, desc) in enumerate(outputs):
            layout.addWidget(QLabel(f"{name}:"), i//2, (i%2)*2)
            status_label = QLabel("OFF")
            status_label.setStyleSheet("QLabel { background-color: gray; color: white; padding: 5px; }")
            layout.addWidget(status_label, i//2, (i%2)*2 + 1)
            setattr(self, f'{name.replace(".", "_")}_status', status_label)
            
        layout.addWidget(QLabel(f"{desc}"), i//2, (i%2)*2 + 2)
        
        group.setLayout(layout)
        return group
        
    def create_memories_status(self):
        """Cria status das memórias"""
        group = QGroupBox("STATUS DAS MEMÓRIAS")
        layout = QGridLayout()
        
        memories = ['M100', 'M200', 'M300', 'M400', 'M500', 'M30']
        
        for i, mem in enumerate(memories):
            layout.addWidget(QLabel(f"{mem}:"), i//4, (i%4)*2)
            status_label = QLabel("OFF")
            status_label.setStyleSheet("QLabel { background-color: gray; color: white; padding: 5px; }")
            layout.addWidget(status_label, i//4, (i%4)*2 + 1)
            setattr(self, f'{mem}_status', status_label)
            
        group.setLayout(layout)
        return group
        
    def create_registers_status(self):
        """Cria status dos registradores"""
        group = QGroupBox("STATUS DOS REGISTRADORES")
        layout = QGridLayout()
        
        registers = ['D110', 'D120', 'D200', 'D210', 'D400', 'D410', 'D500', 'D510']
        
        for i, reg in enumerate(registers):
            layout.addWidget(QLabel(f"{reg}:"), i//4, (i%4)*2)
            status_label = QLabel("0")
            status_label.setStyleSheet("QLabel { background-color: lightgray; padding: 5px; }")
            layout.addWidget(status_label, i//4, (i%4)*2 + 1)
            setattr(self, f'{reg}_status', status_label)
            
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
                self.log("🔧 Y0.10 corrigido para endereço 40971")
                self.log("🔧 Valores apenas positivos - direção via botões")
            else:
                self.connected = False
                self.log("❌ Falha na conexão")
                
        except Exception as e:
            self.connected = False
            self.log(f"❌ Erro na conexão: {e}")
            
    # ------------- helpers de 32 bits -----------------
    def write_dword(self, address, value):
        """Escreve INT32 em dois registradores Modbus (little-endian)."""
        u32 = value & 0xFFFFFFFF
        lo = u32 & 0xFFFF
        hi = (u32 >> 16) & 0xFFFF
        return self.client.write_registers(address, [lo, hi])

    def read_dword(self, address):
        """Lê INT32 assinado de dois registradores."""
        res = self.client.read_holding_registers(address, count=2)
        if res.isError():
            raise ValueError(res)
        lo, hi = res.registers
        u32 = (hi << 16) | lo
        return u32 if u32 < 0x8000_0000 else u32 - 0x1_0000_0000
    
    def jog_move(self, axis_num, direction):
        """
        Movimento incremental (JOG).
        Usa `quick_move` com quantidade definida na spin box de passo.
        """
        pulses = self.jog_step_spin.value()
        self.quick_move(axis_num, pulses, direction)

    # ---------------------------------------------------
    def write_axis_parameters(self, axis_num):
        """Escreve parâmetros de um eixo - APENAS VALORES POSITIVOS"""
        if not self.connected:
            self.log("❌ CLP não conectado")
            return
            
        try:
            spins_map = {
            1: (self.pulsos_spin_1, self.vel_spin_1, 'D110', 'D120'),
            2: (self.pulsos_spin_2, self.vel_spin_2, 'D200', 'D210'),
            3: (self.pulsos_spin_3, self.vel_spin_3, 'D400', 'D410'),
            4: (self.pulsos_spin_4, self.vel_spin_4, 'D500', 'D510')
            }
            p_spin, v_spin, p_addr_key, v_addr_key = spins_map[axis_num]
            pulsos_value = p_spin.value()
            vel_value    = v_spin.value()
            pulsos_addr  = self.addresses[p_addr_key]
            vel_addr     = self.addresses[v_addr_key]
                
            self.log(f"📝 Escrevendo parâmetros Eixo {axis_num}: Pulsos={pulsos_value}, Vel={vel_value}")
            
            # Escreve INT32 completo
            result1 = self.write_dword(pulsos_addr, pulsos_value)
            result2 = self.write_dword(vel_addr, vel_value)
            
            if result1.isError() or result2.isError():
                self.log(f"❌ Erro ao escrever parâmetros eixo {axis_num}")
                return
                
            self.log(f"✅ Parâmetros eixo {axis_num} escritos: D={pulsos_value}, V={vel_value}")
            
            # Verifica se foi escrito
            self.verify_write(pulsos_addr, pulsos_value, f"D{pulsos_addr}")
            self.verify_write(vel_addr, vel_value, f"D{vel_addr}")
            
        except Exception as e:
            self.log(f"❌ Erro ao escrever parâmetros eixo {axis_num}: {e}")
            
    def verify_write(self, address, expected_value, name):
        """Verifica DWORD"""
        try:
            actual_value = self.read_dword(address)
            if actual_value == expected_value:
                self.log(f"✓ {name} verificado: {actual_value}")
            else:
                self.log(f"⚠ {name} divergente: esperado {expected_value}, lido {actual_value}")
        except Exception as e:
            self.log(f"❌ Erro verificação {name}: {e}")
            
    def move_axis(self, axis_num, direction='forward'):
        """Move um eixo com direção especificada"""
        if not self.connected:
            self.log("❌ CLP não conectado")
            return
            
        try:
            # Para movimento reverso, escreve valor negativo no registrador antes do movimento
            if direction == 'reverse':
                # valor negativo INT32
                pulse_spin_map = {
                1: (self.pulsos_spin_1, 'D110'),
                2: (self.pulsos_spin_2, 'D200'),
                3: (self.pulsos_spin_3, 'D400'),
                4: (self.pulsos_spin_4, 'D500')
                }
                spin, p_addr_key = pulse_spin_map[axis_num]
                current_pulses = spin.value()
                pulsos_addr = self.addresses[p_addr_key]
                neg_val = -abs(current_pulses)
                self.log(f"↔ Movimento REVERSE: {neg_val}")
                self.write_dword(pulsos_addr, neg_val)
                
            # Comando de movimento
            cmd_map = {1: 'M300', 2: 'M200', 3: 'M400', 4: 'M500'}
            cmd_addr = self.addresses[cmd_map[axis_num]]
                
            self.log(f"🚀 Movendo eixo {axis_num} - {direction.upper()}")
            
            # Liga o comando ‑ permanece ON; o ladder irá resetar (R) quando o DDRVI terminar
            result = self.client.write_coil(cmd_addr, True)
            if result.isError():
                self.log(f"❌ Erro ao acionar eixo {axis_num}")
                return

            self.log(f"✅ Eixo {axis_num} acionado - {direction} (PLC controla a duração)")
            
            # Se foi reverse, restaura valor positivo
            if direction == 'reverse':
                QTimer.singleShot(200, lambda: self.restore_positive_value(axis_num))
            
        except Exception as e:
            self.log(f"❌ Erro ao mover eixo {axis_num}: {e}")
            
    def restore_positive_value(self, axis_num):
        """Restaura valor positivo após REVERSE"""
        try:
            pulse_spin_map = {
                1: (self.pulsos_spin_1, 'D110'),
                2: (self.pulsos_spin_2, 'D200'),
                3: (self.pulsos_spin_3, 'D400'),
                4: (self.pulsos_spin_4, 'D500')
            }
            spin, p_addr_key = pulse_spin_map[axis_num]
            current_pulses = abs(spin.value())
            pulsos_addr    = self.addresses[p_addr_key]

            self.write_dword(pulsos_addr, current_pulses)
            self.log(f"↔ Valor positivo restaurado: {current_pulses}")
            
        except Exception as e:
            self.log(f"❌ Erro ao restaurar valor: {e}")
            
    def quick_move(self, axis_num, pulses, direction):
        """Movimento rápido com direção"""
        spin_map = {
            1: (self.pulsos_spin_1, self.vel_spin_1),
            2: (self.pulsos_spin_2, self.vel_spin_2),
            3: (self.pulsos_spin_3, self.vel_spin_3),
            4: (self.pulsos_spin_4, self.vel_spin_4)
        }
        p_spin, v_spin = spin_map[axis_num]
        p_spin.setValue(pulses)
        v_spin.setValue(2000)
            
        self.write_axis_parameters(axis_num)
        QTimer.singleShot(200, lambda: self.move_axis(axis_num, direction))
        
    # ------------------------------------------------------------------
    #  NOVO: pulso momentâneo em M50 (Y0.10) – “falling-edge trigger”
    # ------------------------------------------------------------------
    def pulse_y010(self):
        """Dispara um pulso de 100 ms em M50 (Y0.10) e solta o botão."""
        if not self.connected:
            self.log("❌ CLP não conectado")
            return
            
        try:
            # Aciona o coil
            self.log("üèÑ Pulso M50 (SHOT)")
            result = self.client.write_coil(self.addresses['M50'], True)
            if result.isError():
                self.log(f"‚ùå Erro ao escrever M50: {result}")
            else:
                # Mantém ON por 100 ms e depois desliga  (falling-edge)
                QTimer.singleShot(100,
                    lambda: self.client.write_coil(self.addresses['M50'], False))
                # Libera o botão na interface um pouco depois
                QTimer.singleShot(120,
                    lambda: self.y010_btn.setChecked(False))
                self.log("‚úÖ Pulso M50 enviado (100 ms)")
                
        except Exception as e:
            self.log(f"❌ Erro Y0.10: {e}")
            
    def pulse_m100(self):
        """Pulso em M100"""
        if not self.connected:
            return
            
        try:
            self.client.write_coil(self.addresses['M100'], True)
            QTimer.singleShot(100, lambda: self.client.write_coil(self.addresses['M100'], False))
            self.log("M100 pulsado")
        except Exception as e:
            self.log(f"❌ Erro M100: {e}")
            
    def emergency_stop(self):
        """Parada de emergência"""
        if not self.connected:
            return
            
        try:
            self.log("🛑 PARADA DE EMERGÊNCIA!")
            
            # Desliga todas as memórias
            for mem in ['M100', 'M200', 'M300', 'M30', 'M50']:
                self.client.write_coil(self.addresses[mem], False)
                
            # Desliga o botão Y0.10 na interface
            self.y010_btn.setChecked(False)
                
            self.log("✅ Todos os comandos desligados")
            
        except Exception as e:
            self.log(f"❌ Erro na parada: {e}")
            
    def update_status(self):
        """Atualiza status em tempo real"""
        if not self.connected:
            return
            
        try:
            # Atualiza saídas
            outputs_map = {
                'Y0_0': ('Y00', self.Y0_0_status),
                'Y0_1': ('Y01', self.Y0_1_status), 
                'Y0_2': ('Y02', self.Y0_2_status),
                'Y0_3': ('Y03', self.Y0_3_status),
                'Y0_4': ('Y04', self.Y0_4_status),
                'Y0_5': ('Y05', self.Y0_5_status),
                'Y0_6': ('Y06', self.Y0_6_status),
                'Y0_7': ('Y07', self.Y0_7_status),
                'Y0_10': ('Y010', self.Y0_10_status)
             }
            
            for name, (addr_key, label) in outputs_map.items():
                result = self.client.read_coils(self.addresses[addr_key], count=1)
                if not result.isError():
                    state = result.bits[0]
                    label.setText("ON" if state else "OFF")
                    label.setStyleSheet(
                        "QLabel { background-color: lime; color: black; padding: 5px; }" if state 
                        else "QLabel { background-color: gray; color: white; padding: 5px; }"
                    )
                    
                    # Sincroniza botão Y0.10 com o estado real
                    if name == 'Y0_10':
                        if self.y010_btn.isChecked() != state:
                            self.y010_btn.setChecked(state)
            
            # Atualiza memórias
            memories_map = {
                'M100': (self.addresses['M100'], self.M100_status),
                'M200': (self.addresses['M200'], self.M200_status),
                'M300': (self.addresses['M300'], self.M300_status),
                'M400': (self.addresses['M400'], self.M400_status),
                'M500': (self.addresses['M500'], self.M500_status),
                'M30':  (self.addresses['M30'],  self.M30_status)
            }
            
            for name, (addr, label) in memories_map.items():
                result = self.client.read_coils(addr, count=1)
                if not result.isError():
                    state = result.bits[0]
                    label.setText("ON" if state else "OFF")
                    label.setStyleSheet(
                        "QLabel { background-color: red; color: white; padding: 5px; }" if state 
                        else "QLabel { background-color: gray; color: white; padding: 5px; }"
                    )
            
            # Atualiza registradores
            registers_map = {
                'D110': (self.addresses['D110'], self.D110_status),
                'D120': (self.addresses['D120'], self.D120_status),
                'D200': (self.addresses['D200'], self.D200_status),
                'D210': (self.addresses['D210'], self.D210_status),
                'D400': (self.addresses['D400'], self.D400_status),
                'D410': (self.addresses['D410'], self.D410_status),
                'D500': (self.addresses['D500'], self.D500_status),
                'D510': (self.addresses['D510'], self.D510_status)
            }
            
            for name, (addr, label) in registers_map.items():
                try:
                    signed = self.read_dword(addr)
                    label.setText(str(signed))
                    # cor laranja se negativo
                    label.setStyleSheet(
                        "QLabel { background-color: orange; padding: 5px; }"
                        if signed < 0 else
                        "QLabel { background-color: lightgray; padding: 5px; }"
                    )
                except Exception as e:
                    pass  # Silencia erros para não poluir o log
        except Exception as e:
            self.log(f"❌ Erro ao atualizar status: {e}")
            
    def closeEvent(self, event):
        """Fecha conexão ao sair"""
        if self.client:
            self.emergency_stop()
            self.client.close()
            self.log("Desconectado do CLP")
        event.accept()

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = MultiAxisMotorController()
    window.show()
    
    print("="*60)
    print("CONTROLE MULTI-EIXOS - DELTA AS (FINAL)")
    print("="*60)
    print("✅ PROBLEMAS RESOLVIDOS:")
    print("• Y0.10: Endereço corrigido para 40971")
    print("• Valores negativos: Botões de direção FORWARD/REVERSE")
    print("• Agora com 4 eixos (Y2, Z, Y1, X)")
    print("• Direção via botões específicos")
    print("="*60)
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
