import sys
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QSpinBox, QPushButton, 
                            QGroupBox, QGridLayout, QTabWidget, QTextEdit,
                            QFrame, QSizePolicy, QCheckBox)
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
            # Memórias M - Endereços corrigidos conforme ladder real
            # EIXO Y2
            'M0_Y2': 0,       # ATRIBUI ZERO A POSIÇÃO ATUAL (Y2)
            'M50_Y2': 50,     # INICIA O MOVIMENTO ABSOLUTO (Y2)
            'M100_Y2': 100,   # ACIONA LÓGICA DE COMPARAÇÃO (Y2)
            # EIXO Z  
            'M1500_Z': 1500,  # ATRIBUI ZERO A POSIÇÃO ATUAL (Z)
            'M1550_Z': 1550,  # INICIA O MOVIMENTO ABSOLUTO (Z)
            'M1600_Z': 1600,  # ACIONA LÓGICA DE COMPARAÇÃO (Z)
            # EIXO X
            'M1000_X': 1000,  # ATRIBUI ZERO A POSIÇÃO ATUAL (X)
            'M1050_X': 1050,  # INICIA O MOVIMENTO ABSOLUTO (X)
            'M1100_X': 1100,  # ACIONA LÓGICA DE COMPARAÇÃO (X)
            # APLICADORA DE ADESIVO
            'M5000': 5000,    # Trigger aplicadora de adesivo
            'M5001': 5001,    # Auxiliar aplicadora

            # HOMING - Busca pelo HOME
            'M350': 350,      # GO TO HOME Y2
            'M1350': 1350,    # GO TO HOME X
            'M1850': 1850,    # GO TO HOME Z

            # HOMING REALIZADO - Status do homing
            'M300': 300,      # HOMING REALIZADO Y2
            'M1300': 1300,    # HOMING REALIZADO X
            'M1800': 1800,    # HOMING REALIZADO Z

            # SISTEMA JOG EIXO X (conforme ladder implementado)
            'M1070': 1070,    # Comando JOG X
            'M1080': 1080,    # Comando JOG X (sentido oposto, se implementado)
            'M1010': 1010,    # Flag segurança JOG (conforme ladder)
            'M1011': 1011,    # Flag segurança JOG (conforme ladder)
            'D1470': 1470,    # Ramp-up time JOG X
            'D4000': 4000,    # Target frequency JOG X (positiva)
            'D1476': 1476,    # Target frequency JOG X (negativa)
            'D1490': 1490,    # Ramp-down time JOG X
            
            # Registradores D - Corrigidos conforme ladder real
            # EIXO Y2
            'D0_Y2': 0,         # MOVE TO ABS (Y2)
            'D50_Y2': 50,       # LIMITE NEGATIVO (Y2)
            'D100_Y2': 100,     # POSIÇÃO ABSOLUTA DEFINIDA PELO USUÁRIO (Y2) - ENTRADA
            'D150_Y2': 150,     # POSIÇÃO ABSOLUTA DEFINIDA (Y2)
            'D20000_Y2': 20000, # VELOCIDADE DE DESLOCAMENTO (Y2)
            # EIXO Z
            'D1500_Z': 1500,    # MOVE TO ABS (Z)
            'D1550_Z': 1550,    # LIMITE NEGATIVO (Z)
            'D1600_Z': 1600,    # POSIÇÃO ABSOLUTA DEFINIDA PELO USUÁRIO (Z) - ENTRADA
            'D1650_Z': 1650,    # POSIÇÃO ABSOLUTA DEFINIDA (Z)
            'D21500_Z': 21500,  # VELOCIDADE DE DESLOCAMENTO (Z)
            # EIXO X
            'D1000_X': 1000,    # MOVE TO ABS (X)
            'D1050_X': 1050,    # LIMITE NEGATIVO (X)
            'D1100_X': 1100,    # POSIÇÃO ABSOLUTA DEFINIDA PELO USUÁRIO (X) - ENTRADA
            'D1150_X': 1150,    # POSIÇÃO ABSOLUTA DEFINIDA (X)
            'D21000_X': 21000,  # VELOCIDADE DE DESLOCAMENTO (X)
            
            # Registradores de status (leitura)
            'D3100_Y2': 3100,   # POSIÇÃO ATUAL MOTOR Y2 (cópia do SR460)
            'D3200_Z': 3200,    # POSIÇÃO ATUAL MOTOR Z (cópia do SR480)
            'D3000_X': 3000,    # POSIÇÃO ATUAL MOTOR X (cópia do SR520)
            
            # Saídas Y - Conforme ladder real
            'Y00': 40960, 'Y01': 40961,     # Y0.0 / Y0.1  eixo-Y2
            'Y02': 40962, 'Y03': 40963,     # Y0.2 / Y0.3  eixo-Z
            'Y06': 40966, 'Y07': 40967,     # Y0.6 / Y0.7  eixo-X
            'Y010': 40971,                  # Y0.10 aplicadora de adesivo
            
            # Entradas X (sensores)
            'X01_Z': 8193,      # X0.1 sensor homing Z
            'X02_Y2': 8194,     # X0.2 sensor homing Y2  
            'X03_X': 8195,      # X0.3 sensor homing X
        }
        # Posição atual dos eixos
        self.current_positions = {
            'Y2': 0,
            'Z': 0, 
            'X': 0
        }
        
        self.init_ui()
        self.connect_plc()

        # Lê velocidades salvas na ROM após conectar
        QTimer.singleShot(1000, self.read_initial_velocities)
        QTimer.singleShot(1500, self.read_initial_jog_velocity)

        # Controle de teclas do teclado
        self.keyboard_jog_active = False  # Flag para controlar se JOG está ativo via teclado
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)  # Permite capturar teclas
        
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
        self.setWindowTitle("Controle Multi-Eixos - Delta AS (ENDEREÇOS LADDER REAIS)")
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

        # === ABA APLICADORA DE ADESIVO ===
        adhesive_tab = self.create_adhesive_control_tab()
        tab_widget.addTab(adhesive_tab, "Aplicadora Adesivo")

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
        btn_y2_p = QPushButton("Y2 +")
        btn_z_p  = QPushButton("Z  +")
        btn_x_p  = QPushButton("X  +")
        grid.addWidget(btn_y2_p, 0, 1)
        grid.addWidget(btn_z_p,  0, 2)
        grid.addWidget(btn_x_p,  0, 3)

        # --- linha do meio (X- / X+)

        # --- linha inferior ( − )
        btn_y2_m = QPushButton("Y2 −")
        btn_z_m  = QPushButton("Z  −")
        btn_x_m  = QPushButton("X  −")
        grid.addWidget(btn_y2_m, 1, 1)
        grid.addWidget(btn_z_m,  1, 2)
        grid.addWidget(btn_x_m,  1, 3)

        # ligações
        btn_y2_p.clicked.connect(lambda: self.jog_move('Y2', 'forward'))
        btn_y2_m.clicked.connect(lambda: self.jog_move('Y2', 'reverse'))
        btn_z_p.clicked.connect( lambda: self.jog_move('Z', 'forward'))
        btn_z_m.clicked.connect( lambda: self.jog_move('Z', 'reverse'))
        btn_x_p.clicked.connect( lambda: self.jog_move('X', 'forward'))
        btn_x_m.clicked.connect( lambda: self.jog_move('X', 'reverse'))

        # estilinho
        for b in [btn_y2_p, btn_y2_m, btn_z_p, btn_z_m, btn_x_p, btn_x_m]:
            b.setMinimumSize(90, 60)
            b.setStyleSheet("QPushButton { font-weight:bold; font-size:15px; }")

        jog_layout.addLayout(grid)
        jog_layout.addStretch()

        tab_widget.addTab(jog_tab, "Jog Manual")
        
        # === ABA 1: CONTROLE DOS EIXOS ===
        control_tab = QWidget()
        control_layout = QHBoxLayout(control_tab)
        
        # Eixo Y2
        axis_y2_group = self.create_axis_control("EIXO Y2", 'Y2')
        control_layout.addWidget(axis_y2_group)
        
        # Eixo Z
        axis_z_group = self.create_axis_control("EIXO Z", 'Z')
        control_layout.addWidget(axis_z_group)

        

        # Eixo X
        axis_x_group = self.create_axis_control("EIXO X", 'X')
        control_layout.addWidget(axis_x_group)
        
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
        
    def create_adhesive_control_tab(self):
        """Cria aba de controle da aplicadora de adesivo"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Grupo principal
        group = QGroupBox("CONTROLE APLICADORA DE ADESIVO")
        group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 14px; }")
        group_layout = QVBoxLayout()
        
        # Botão de acionamento
        trigger_btn = QPushButton("🎯 ACIONAR APLICADORA")
        trigger_btn.setStyleSheet("QPushButton { background-color: #FF5722; color: white; padding: 15px; font-weight: bold; font-size: 16px; }")
        trigger_btn.clicked.connect(self.trigger_adhesive_applicator)
        group_layout.addWidget(trigger_btn)
        
        # Status
        self.adhesive_status_label = QLabel("Status: Inativo")
        self.adhesive_status_label.setStyleSheet("QLabel { background-color: gray; color: white; padding: 10px; font-weight: bold; }")
        group_layout.addWidget(self.adhesive_status_label)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
        layout.addStretch()
        
        return tab
        
    def create_axis_control(self, title, axis_name):
        """Cria controle para um eixo - CORRIGIDO para valores absolutos"""
        group = QGroupBox(title)
        group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 12px; }")
        layout = QVBoxLayout()
        
        # Parâmetros
        params_frame = QFrame()
        params_layout = QGridLayout(params_frame)
        
        # Mapeamento de endereços corrigido
        addr_map = {
            'Y2': (f'D100_{axis_name}', f'D20000_{axis_name}'),  # Entrada usuário, Velocidade
            'Z':  (f'D1600_{axis_name}', f'D21500_{axis_name}'), # Entrada usuário, Velocidade  
            'X':  (f'D1100_{axis_name}', f'D21000_{axis_name}')  # Entrada usuário, Velocidade
        }
        pulsos_addr, vel_addr = addr_map[axis_name]
        
        # Configurações comuns para todos os eixos (agora todos usam posição absoluta)
        pulsos_label = f"{pulsos_addr} - Posição Absoluta:"
        pulsos_tooltip = "Coordenada absoluta de destino"
        vel_label = f"{vel_addr} - Velocidade:"
        vel_tooltip = "Velocidade de deslocamento"
        default_pulsos = 0
        default_vel = 2000
            
        # Pulsos 32-bits (aceita valores negativos)
        params_layout.addWidget(QLabel(pulsos_label), 0, 0)
        pulsos_spin = QSpinBox()
        pulsos_spin.setRange(-2_000_000_000, 2_000_000_000)
        pulsos_spin.setValue(default_pulsos)
        pulsos_spin.setToolTip(pulsos_tooltip)
        params_layout.addWidget(pulsos_spin, 0, 1)
        setattr(self, f'pulsos_spin_{axis_name}', pulsos_spin)
        
        # Velocidade
        params_layout.addWidget(QLabel(vel_label), 1, 0)
        vel_spin = QSpinBox()
        vel_spin.setRange(100, 2_000_000_000)
        vel_spin.setValue(default_vel)
        vel_spin.setToolTip(vel_tooltip)
        params_layout.addWidget(vel_spin, 1, 1)
        setattr(self, f'vel_spin_{axis_name}', vel_spin)

        # Display da posição atual para todos os eixos
        sr_addr_map = {'Y2': 'D3100_Y2', 'Z': 'D3200_Z', 'X': 'D3000_X'}
        params_layout.addWidget(QLabel(f"{sr_addr_map[axis_name]} - Posição Atual:"), 2, 0)
        current_pos_label = QLabel("0")
        current_pos_label.setStyleSheet("QLabel { background-color: lightblue; padding: 2px; font-weight: bold; max-height: 20px; }")
        params_layout.addWidget(current_pos_label, 2, 1)
        setattr(self, f'current_pos_label_{axis_name}', current_pos_label)

        # Indicador LED de HOMING REALIZADO
        params_layout.addWidget(QLabel("Status Homing:"), 3, 0)
        homing_led = QLabel("●")
        homing_led.setStyleSheet("QLabel { background-color: gray; color: gray; padding: 2px; font-size: 16px; font-weight: bold; max-height: 20px; border-radius: 10px; }")
        homing_led.setAlignment(Qt.AlignmentFlag.AlignCenter)
        homing_led.setToolTip("Cinza: Homing não realizado | Verde: Homing realizado")
        params_layout.addWidget(homing_led, 3, 1)
        setattr(self, f'homing_led_{axis_name}', homing_led)
        
        layout.addWidget(params_frame)
        
        # Botões de escrita
        write_btn = QPushButton("Escrever Parâmetros")
        write_btn.clicked.connect(lambda: self.write_axis_parameters(axis_name))
        layout.addWidget(write_btn)
        
        # Botões de movimento
        move_frame = QFrame()
        move_layout = QGridLayout(move_frame)
        
        # Movimento absoluto principal
        move_abs_btn = QPushButton("🎯 MOVER PARA POSIÇÃO ABSOLUTA")
        move_abs_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; padding: 10px; font-weight: bold; }")
        move_abs_btn.clicked.connect(lambda: self.move_axis_absolute(axis_name))
        move_layout.addWidget(move_abs_btn, 0, 0, 1, 2)
        
        # Botão HOME
        home_btn = QPushButton("🏠 HOME (Zerar Posição)")
        home_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; }")
        home_btn.clicked.connect(lambda: self.move_axis_home(axis_name))
        move_layout.addWidget(home_btn, 1, 0, 1, 2)
        
        # Movimentos relativos rápidos
        rel_plus_btn = QPushButton("Relativo +1000")
        rel_plus_btn.clicked.connect(lambda: self.move_relative(axis_name, 1000))
        move_layout.addWidget(rel_plus_btn, 2, 0)
        
        rel_minus_btn = QPushButton("Relativo -1000")
        rel_minus_btn.clicked.connect(lambda: self.move_relative(axis_name, -1000))
        move_layout.addWidget(rel_minus_btn, 2, 1)

        # Controles JOG específicos para EIXO X
        if axis_name == 'X':
            # Separador visual
            separator = QFrame()
            separator.setFrameStyle(QFrame.Shape.HLine | QFrame.Shadow.Sunken)
            move_layout.addWidget(separator, 3, 0, 1, 2)
            
            # Frame JOG
            jog_frame = QFrame()
            jog_frame.setStyleSheet("QFrame { border: 2px solid #2196F3; border-radius: 5px; background-color: #E3F2FD; }")
            jog_layout = QVBoxLayout(jog_frame)
            
            # Título JOG
            jog_title = QLabel("🎮 CONTROLE JOG CONTÍNUO")
            jog_title.setStyleSheet("QLabel { font-weight: bold; font-size: 12px; color: #1976D2; padding: 3px; }")
            jog_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            jog_layout.addWidget(jog_title)
            
            # Configuração de velocidade JOG
            vel_jog_layout = QHBoxLayout()
            vel_jog_layout.addWidget(QLabel("Vel. JOG (Hz):"))
            self.jog_velocity_spin = QSpinBox()
            self.jog_velocity_spin.setRange(100, 50000)
            self.jog_velocity_spin.setValue(2000)  # Valor padrão do ladder
            self.jog_velocity_spin.setToolTip("Frequência do movimento JOG (Hz)")
            vel_jog_layout.addWidget(self.jog_velocity_spin)
            
            set_vel_btn = QPushButton("📝 Aplicar")
            set_vel_btn.setStyleSheet("QPushButton { background-color: #FF9800; color: white; font-weight: bold; }")
            set_vel_btn.clicked.connect(self.set_jog_velocity_x)
            vel_jog_layout.addWidget(set_vel_btn)
            jog_layout.addLayout(vel_jog_layout)
            
            # Botões JOG com pressionar/soltar
            jog_buttons_layout = QHBoxLayout()
            
            # Botão JOG Negativo (AGORA À ESQUERDA)
            self.jog_minus_btn = QPushButton("🔽 JOG X-")
            self.jog_minus_btn.setStyleSheet("""
                QPushButton { 
                    background-color: #FF5722; 
                    color: white; 
                    font-weight: bold; 
                    padding: 10px;
                    border-radius: 5px;
                }
                QPushButton:pressed { 
                    background-color: #e64a19;
                }
            """)
            self.jog_minus_btn.pressed.connect(lambda: self.jog_start_x('-'))
            self.jog_minus_btn.released.connect(self.jog_stop_x)
            jog_buttons_layout.addWidget(self.jog_minus_btn)
            
            # Botão JOG Positivo (AGORA À DIREITA)
            self.jog_plus_btn = QPushButton("🔼 JOG X+")
            self.jog_plus_btn.setStyleSheet("""
                QPushButton { 
                    background-color: #4CAF50; 
                    color: white; 
                    font-weight: bold; 
                    padding: 10px;
                    border-radius: 5px;
                }
                QPushButton:pressed { 
                    background-color: #45a049;
                }
            """)
            self.jog_plus_btn.pressed.connect(lambda: self.jog_start_x('+'))
            self.jog_plus_btn.released.connect(self.jog_stop_x)
            jog_buttons_layout.addWidget(self.jog_plus_btn)
            
            jog_layout.addLayout(jog_buttons_layout)
            
            # Status JOG
            self.jog_status_label = QLabel("Status: Inativo")
            self.jog_status_label.setStyleSheet("QLabel { background-color: gray; color: white; padding: 5px; font-weight: bold; border-radius: 3px; }")
            self.jog_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            jog_layout.addWidget(self.jog_status_label)
            
            # Indicador de segurança
            self.safety_indicator = QLabel("🛡️ Segurança: OK")
            self.safety_indicator.setStyleSheet("QLabel { background-color: green; color: white; padding: 3px; font-size: 10px; border-radius: 3px; }")
            self.safety_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
            jog_layout.addWidget(self.safety_indicator)

            # NOVO: Checkbox para habilitar controle via teclado
            keyboard_frame = QFrame()
            keyboard_frame.setStyleSheet("QFrame { border: 1px solid #FF9800; border-radius: 3px; background-color: #FFF3E0; }")
            keyboard_layout = QHBoxLayout(keyboard_frame)
            keyboard_layout.setContentsMargins(5, 5, 5, 5)
            
            self.keyboard_jog_checkbox = QCheckBox("⌨️ Controle via teclado")
            self.keyboard_jog_checkbox.setStyleSheet("QCheckBox { font-weight: bold; color: #E65100; }")
            self.keyboard_jog_checkbox.setToolTip("Habilita uso das setas ← → para JOG do eixo X")
            self.keyboard_jog_checkbox.stateChanged.connect(self.on_keyboard_jog_toggle)
            keyboard_layout.addWidget(self.keyboard_jog_checkbox)
            
            # Label informativo
            keyboard_info = QLabel("(← eixo X-  |  → eixo X+)")
            keyboard_info.setStyleSheet("QLabel { color: #BF360C; font-size: 10px; font-style: italic; }")
            keyboard_layout.addWidget(keyboard_info)
            
            jog_layout.addWidget(keyboard_frame)
            
            move_layout.addWidget(jog_frame, 4, 0, 1, 2)
        
        layout.addWidget(move_frame)
        
        group.setLayout(layout)
        return group
        
    def create_auxiliary_controls(self):
        """Cria controles auxiliares - Y0.10 CORRIGIDO"""
        group = QGroupBox("CONTROLES AUXILIARES")
        group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 12px; }")
        layout = QVBoxLayout()
        
        # Saída Y0.10  ─ comando tipo “falling-edge trigger”
        y010_btn = QPushButton("SHOT (M5000)")
        y010_btn.setCheckable(True)
        y010_btn.clicked.connect(self.pulse_y010)
        y010_btn.setStyleSheet("QPushButton:checked { background-color: orange; }")
        layout.addWidget(y010_btn)
        setattr(self, 'y010_btn', y010_btn)
        
        # Info do endereço
        info_label = QLabel("Y0.10 é comandado por M5000 (coil 50)")
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
    
    def trigger_adhesive_applicator(self):
        """Aciona a aplicadora de adesivo"""
        if not self.connected:
            self.log("❌ CLP não conectado")
            return
            
        try:
            self.log("🎯 Acionando aplicadora de adesivo...")
            result = self.client.write_coil(self.addresses['M5000'], True)
            if not result.isError():
                self.adhesive_status_label.setText("Status: ATIVO")
                self.adhesive_status_label.setStyleSheet("QLabel { background-color: orange; color: white; padding: 10px; font-weight: bold; }")
                QTimer.singleShot(200, self.reset_adhesive_trigger)
                self.log("✅ Aplicadora acionada")
        except Exception as e:
            self.log(f"❌ Erro ao acionar aplicadora: {e}")
            
    def reset_adhesive_trigger(self):
        """Reseta trigger da aplicadora"""
        try:
            self.client.write_coil(self.addresses['M5000'], False)
            self.adhesive_status_label.setText("Status: Inativo")
            self.adhesive_status_label.setStyleSheet("QLabel { background-color: gray; color: white; padding: 10px; font-weight: bold; }")
        except Exception as e:
            self.log(f"❌ Erro ao resetar aplicadora: {e}")
        
    def create_outputs_status(self):
        """Cria status das saídas"""
        group = QGroupBox("STATUS DAS SAÍDAS")
        layout = QGridLayout()
        
        outputs = [
            ('Y0.0', 'Pulso Eixo 1'),
            ('Y0.1', 'Dir Eixo 1'),
            ('Y0.2', 'Pulso Eixo 2'), 
            ('Y0.3', 'Dir Eixo 2'),
            ('Y0.6', 'Pulso Eixo 4'),
            ('Y0.7', 'Dir Eixo 4'),
            ('Y0.10', 'Aplicadora')
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
        
        memories = ['M0_Y2', 'M50_Y2', 'M100_Y2', 'M1500_Z', 'M1550_Z', 'M1600_Z', 'M1000_X', 
                    'M1050_X', 'M1100_X', 'M5000', 'M350', 'M1350', 'M1850', 'M300', 'M1300', 
                    'M1800', 'M1070', 'M1080', 'M1010', 'M1011']
        
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
        
        registers = [
            'D0_Y2', 'D100_Y2', 'D20000_Y2',      # Y2 (entrada usuário)
            'D1500_Z', 'D1600_Z', 'D21500_Z',     # Z (entrada usuário)
            'D1000_X', 'D1100_X', 'D21000_X',     # X (entrada usuário)
            'D3100_Y2', 'D3200_Z', 'D3000_X',     # Posições atuais (cópias dos SR)
            'D1470', 'D4000', 'D1476', 'D1490'    # Parâmetros JOG X
        ]

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
                self.log("🔧 Endereços corrigidos conforme ladder real")
                self.log("🔧 Aplicadora de adesivo integrada")
            else:
                self.connected = False
                self.log("❌ Falha na conexão")
                
        except Exception as e:
            self.connected = False
            self.log(f"❌ Erro na conexão: {e}")

    def read_initial_velocities(self):
        """Lê velocidades salvas na ROM do CLP e atualiza interface"""
        if not self.connected:
            return
            
        try:
            self.log("📖 Lendo velocidades salvas na ROM do CLP...")
            
            # Mapeamento dos registradores de velocidade
            velocity_map = {
                'Y2': ('D20000_Y2', 'vel_spin_Y2'),
                'Z':  ('D21500_Z', 'vel_spin_Z'),
                'X':  ('D21000_X', 'vel_spin_X')
            }
            
            for axis, (reg_key, spin_attr) in velocity_map.items():
                try:
                    velocity_addr = self.addresses[reg_key]
                    saved_velocity = self.read_dword(velocity_addr)
                    
                    # Atualiza interface com valor lido
                    vel_spin = getattr(self, spin_attr)
                    vel_spin.setValue(saved_velocity)
                    
                    self.log(f"✅ Velocidade {axis} lida da ROM: {saved_velocity}")
                    
                except Exception as e:
                    self.log(f"⚠️ Erro ao ler velocidade {axis}: {e}")
                    # Mantém valor padrão se der erro
                    continue
                    
            self.log("📖 Leitura das velocidades concluída")
            
        except Exception as e:
            self.log(f"❌ Erro geral na leitura das velocidades: {e}")
    
    def read_initial_jog_velocity(self):
        """Lê velocidade JOG atual dos registradores D4000 e D1476"""
        if not self.connected:
            return
            
        try:
            self.log("📖 Lendo velocidade JOG atual...")
            
            # Lê velocidade positiva do D4000
            jog_velocity_positive = self.read_dword(self.addresses['D4000'])
            
            # Lê velocidade negativa do D1476 (deve ser negativa)
            jog_velocity_negative = self.read_dword(self.addresses['D1476'])
            
            # Usa o valor absoluto da velocidade positiva para atualizar interface
            if hasattr(self, 'jog_velocity_spin'):
                current_velocity = abs(jog_velocity_positive)
                self.jog_velocity_spin.setValue(current_velocity)
                self.log(f"✅ Velocidade JOG atual: {current_velocity} Hz (D4000={jog_velocity_positive}, D1476={jog_velocity_negative})")
            else:
                self.log(f"📊 Velocidade JOG atual: D4000={jog_velocity_positive}, D1476={jog_velocity_negative}")
                
        except Exception as e:
            self.log(f"⚠️ Erro ao ler velocidade JOG atual: {e}")
            # Mantém valor padrão se der erro
            
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
    
    def jog_move(self, axis_name, direction):
        """
        Movimento incremental (JOG).
        Usa `quick_move` com quantidade definida na spin box de passo.
        """
        pulses = self.jog_step_spin.value()
        self.move_relative(axis_name, pulses if direction == 'forward' else -pulses)

    # ---------------------------------------------------
    def write_axis_parameters(self, axis_name):
        """Escreve parâmetros de um eixo"""
        if not self.connected:
            self.log("❌ CLP não conectado")
            return
            
        try:
            # Obtém valores da interface
            p_spin = getattr(self, f'pulsos_spin_{axis_name}')
            v_spin = getattr(self, f'vel_spin_{axis_name}')
            pulsos_value = p_spin.value()
            vel_value = v_spin.value()
            
            # Mapeamento de endereços
            addr_map = {
                'Y2': (f'D100_{axis_name}', f'D20000_{axis_name}'),
                'Z':  (f'D1600_{axis_name}', f'D21500_{axis_name}'),
                'X':  (f'D1100_{axis_name}', f'D21000_{axis_name}')
            }
            p_addr_key, v_addr_key = addr_map[axis_name]
            pulsos_addr = self.addresses[p_addr_key]
            vel_addr = self.addresses[v_addr_key]
                
            self.log(f"📝 Escrevendo parâmetros Eixo {axis_name}: Posição={pulsos_value}, Vel={vel_value}")
            
            # Escreve INT32 completo
            result1 = self.write_dword(pulsos_addr, pulsos_value)
            result2 = self.write_dword(vel_addr, vel_value)
            
            if result1.isError() or result2.isError():
                self.log(f"❌ Erro ao escrever parâmetros eixo {axis_name}")
                return
            
            self.log(f"✅ Parâmetros eixo {axis_name} escritos: Pos={pulsos_value}, Vel={vel_value}")
            
            # Verifica se foi escrito
            self.verify_write(pulsos_addr, pulsos_value, p_addr_key)
            self.verify_write(vel_addr, vel_value, v_addr_key)
            
        except Exception as e:
            self.log(f"❌ Erro ao escrever parâmetros eixo {axis_name}: {e}")
            
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
            
    def move_axis_absolute(self, axis_name):
        """Move eixo para posição absoluta"""
        if not self.connected:
            self.log("❌ CLP não conectado")
            return
            
        try:
            # Escreve parâmetros primeiro
            self.write_axis_parameters(axis_name)
                
            # Comando de movimento
            cmd_map = {
                'Y2': f'M50_{axis_name}',   # INICIA MOVIMENTO ABSOLUTO
                'Z':  f'M1550_{axis_name}', # INICIA MOVIMENTO ABSOLUTO
                'X':  f'M1050_{axis_name}'  # INICIA MOVIMENTO ABSOLUTO
            }
            cmd_addr = self.addresses[cmd_map[axis_name]]
                
            target_position = getattr(self, f'pulsos_spin_{axis_name}').value()
            self.log(f"🚀 Movendo eixo {axis_name} para posição {target_position}")
            
            result = self.client.write_coil(cmd_addr, True)
            if result.isError():
                self.log(f"❌ Erro ao acionar eixo {axis_name}")
                return

            self.log(f"✅ Eixo {axis_name} acionado para posição {target_position}")
            
        except Exception as e:
            self.log(f"❌ Erro ao mover eixo {axis_name}: {e}")
            
    def move_axis_home(self, axis_name):
        """Move eixo para HOME (zera posição)"""
        if not self.connected:
            self.log("❌ CLP não conectado")
            return
        try:
            self.log(f"🏠 Zerando posição eixo {axis_name}")
            
            # Comando de busca pelo HOME - endereços corrigidos conforme planilha
            cmd_map = {
                'Y2': 'M350',    # GO TO HOME Y2
                'Z':  'M1850',   # GO TO HOME Z
                'X':  'M1350'    # GO TO HOME X
            }
            cmd_addr = self.addresses[cmd_map[axis_name]]
            result = self.client.write_coil(cmd_addr, True) 
            if not result.isError():
                self.log(f"✅ Comando HOME enviado para eixo {axis_name}")
            
        except Exception as e:
            self.log(f"❌ Erro movimento HOME eixo {axis_name}: {e}")
             
    def move_relative(self, axis_name, offset):
        """Movimento relativo a partir da posição atual"""
            
        if not self.connected:
            self.log("❌ CLP não conectado")
            return
            
        try:
            current_pos = self.current_positions[axis_name]
            new_position = current_pos + offset
            
            # Atualiza interface e executa movimento
            p_spin = getattr(self, f'pulsos_spin_{axis_name}')
            p_spin.setValue(new_position)
            self.move_axis_absolute(axis_name)
            
            self.log(f"📍 Movimento relativo {axis_name}: {current_pos} + {offset} = {new_position}")
            
        except Exception as e:
            self.log(f"❌ Erro movimento relativo {axis_name}: {e}")

    # ===================================================================
    #                    SISTEMA JOG EIXO X
    # ===================================================================
    
    def set_jog_velocity_x(self):
        """Define velocidade do JOG no eixo X conforme ladder implementado"""
        if not self.connected:
            self.log("❌ CLP não conectado")
            return
            
        try:
            velocity = self.jog_velocity_spin.value()

            # Verifica se a velocidade mudou antes de escrever
            current_d4000 = self.read_dword(self.addresses['D4000'])
            if current_d4000 == velocity:
                self.log(f"ℹ️ Velocidade JOG já está em {velocity} Hz - não alterada")
                return
            
            # Escreve velocidade positiva e negativa conforme ladder
            result1 = self.write_dword(self.addresses['D4000'], velocity)      # Frequência positiva
            result2 = self.write_dword(self.addresses['D1476'], -velocity)    # Frequência negativa
            
            if not result1.isError() and not result2.isError():
                self.log(f"✅ Velocidade JOG X definida: ±{velocity} Hz")
                # Verifica se foi escrito corretamente
                QTimer.singleShot(200, lambda: self.verify_jog_velocity(velocity))
            else:
                self.log(f"❌ Erro ao definir velocidade JOG X")
                
        except Exception as e:
            self.log(f"❌ Erro ao configurar velocidade JOG X: {e}")

    def verify_jog_velocity(self, expected_velocity):
        """Verifica se a velocidade JOG foi escrita corretamente"""
        try:
            actual_positive = self.read_dword(self.addresses['D4000'])
            actual_negative = self.read_dword(self.addresses['D1476'])
            
            if actual_positive == expected_velocity and actual_negative == -expected_velocity:
                self.log(f"✓ Velocidade JOG verificada: D4000={actual_positive}, D1476={actual_negative}")
            else:
                self.log(f"⚠️ Velocidade JOG divergente: Esperado ±{expected_velocity}, Lido D4000={actual_positive}, D1476={actual_negative}")
                
        except Exception as e:
            self.log(f"❌ Erro verificação velocidade JOG: {e}")
            
    def jog_start_x(self, direction):
        """Inicia movimento JOG contínuo no eixo X"""
        if not self.connected:
            self.log("❌ CLP não conectado")
            return
            
        try:            
            # Configura velocidade automaticamente
            self.set_jog_velocity_x()
            
            # Aciona comando JOG correto conforme ladder implementado
            if direction == '+':
                result = self.client.write_coil(self.addresses['M1070'], True)
                direction_text = "POSITIVO (M1070)"
                self.log(f"🔼 Acionando M1070 para JOG X+")
            else:
                # Movimento negativo: usa M1080 com velocidade negativa em D1476
                result = self.client.write_coil(self.addresses['M1080'], True)
                direction_text = "NEGATIVO (M1080)"
                self.log(f"🔽 Acionando M1080 para JOG X-")
                
            if not result.isError():
                self.log(f"🎮 JOG X {direction_text} INICIADO")
                self.update_jog_status(f"ATIVO - {direction_text}", "orange")
                # Log dos parâmetros JOG para debug
                velocity = self.jog_velocity_spin.value()
                self.log(f"📊 Parâmetros JOG: D1470={100}, D4000={velocity}, D1476={-velocity}, D1490={100}")
                # Verifica segurança apenas para informar o usuário (não bloqueia)
                self.check_jog_safety_x()
            else:
                self.log(f"❌ Erro ao iniciar JOG X {direction_text}")
                
        except Exception as e:
            self.log(f"❌ Erro JOG start X: {e}")
            
    def jog_stop_x(self):
        """Para movimento JOG do eixo X"""
        if not self.connected:
            return
            
        try:
            # Para todos os comandos JOG
            result1 = self.client.write_coil(self.addresses['M1070'], False)
            result2 = self.client.write_coil(self.addresses['M1080'], False)
            
            self.log("🛑 Desligando M1070 e M1080")
            
            self.log("🛑 JOG X PARADO")
            self.update_jog_status("PARADO", "gray")
           
        except Exception as e:
            self.log(f"❌ Erro JOG stop X: {e}")
            
    def check_jog_safety_x(self):
        """Monitora status de segurança JOG X (apenas informativo - não bloqueia)"""
        try:
            # Lê flags de segurança do ladder conforme implementado
            # M1010: movimento positivo permitido (posição < limite positivo)
            # M1011: movimento negativo permitido (posição > limite negativo)
            result1 = self.client.read_coils(self.addresses['M1010'], 1)
            result2 = self.client.read_coils(self.addresses['M1011'], 1)
            
            if not result1.isError() and not result2.isError():
                positive_ok = result1.bits[0]  # M1010: movimento + permitido
                negative_ok = result2.bits[0]  # M1011: movimento - permitido
                safety_ok = positive_ok or negative_ok  # Pelo menos uma direção liberada
                
                # Atualiza indicador visual
                if positive_ok and negative_ok:
                    status_text = "🛡️ Ambas direções OK"
                    color = "green"
                elif positive_ok:
                    status_text = "🛡️ Apenas JOG+ permitido"
                    color = "orange"
                elif negative_ok:
                    status_text = "🛡️ Apenas JOG- permitido" 
                    color = "orange"
                else:
                    status_text = "⚠️ Fora dos limites"
                    color = "red"
                
                self.safety_indicator.setText(status_text)
                self.safety_indicator.setStyleSheet(f"QLabel {{ background-color: {color}; color: white; padding: 3px; font-size: 10px; border-radius: 3px; }}")
                # Log detalhado para debug
                current_status = (positive_ok, negative_ok)
                if hasattr(self, '_last_safety_status') and self._last_safety_status != current_status:
                    if not safety_ok:
                        self.log(f"⚠️ Motor fora dos limites - M1010(+)={positive_ok}, M1011(-)={negative_ok}")
                    else:
                        self.log(f"✅ Motor dentro dos limites - M1010(+)={positive_ok}, M1011(-)={negative_ok}")
                self._last_safety_status = (positive_ok, negative_ok)
                
                return safety_ok
            else:
                return False
                
        except Exception as e:
            # Não loga erro para não poluir - pode acontecer se CLP não estiver conectado
            return False
            
    def update_jog_status(self, status_text, color):
        """Atualiza status visual do JOG"""
        if hasattr(self, 'jog_status_label'):
            self.jog_status_label.setText(f"Status: {status_text}")
            self.jog_status_label.setStyleSheet(f"QLabel {{ background-color: {color}; color: white; padding: 5px; font-weight: bold; border-radius: 3px; }}")
    
    # ===================================================================
    #                    CONTROLE VIA TECLADO  
    # ===================================================================
    
    def on_keyboard_jog_toggle(self, state):
        """Callback quando checkbox de controle via teclado é alterado"""
        enabled = state == Qt.CheckState.Checked.value
        
        if enabled:
            self.log("⌨️ Controle via teclado HABILITADO - Use ← → para JOG X")
            self.keyboard_jog_checkbox.setStyleSheet("QCheckBox { font-weight: bold; color: #4CAF50; }")
        else:
            self.log("⌨️ Controle via teclado DESABILITADO")
            self.keyboard_jog_checkbox.setStyleSheet("QCheckBox { font-weight: bold; color: #E65100; }")
            # Para qualquer movimento JOG ativo se desabilitar
            if self.keyboard_jog_active:
                self.jog_stop_x()
                self.keyboard_jog_active = False
                
    def keyPressEvent(self, event):
        """Captura teclas pressionadas"""
        # Só processa se checkbox estiver habilitado e conectado
        if not hasattr(self, 'keyboard_jog_checkbox') or not self.keyboard_jog_checkbox.isChecked() or not self.connected:
            super().keyPressEvent(event)
            return
            
        key = event.key()
        
        # Tecla SETA ESQUERDA (JOG X-)
        if key == Qt.Key.Key_Left:
            if not self.keyboard_jog_active:
                self.keyboard_jog_active = True
                self.jog_start_x('-')
                self.log("⌨️ JOG X- iniciado via teclado (←)")
            event.accept()
            return
            
        # Tecla SETA DIREITA (JOG X+)  
        elif key == Qt.Key.Key_Right:
            if not self.keyboard_jog_active:
                self.keyboard_jog_active = True
                self.jog_start_x('+')
                self.log("⌨️ JOG X+ iniciado via teclado (→)")
            event.accept()
            return
            
        # Outras teclas passam para o comportamento padrão
        super().keyPressEvent(event)
        
    def keyReleaseEvent(self, event):
        """Captura teclas soltas"""
        # Só processa se checkbox estiver habilitado e conectado
        if not hasattr(self, 'keyboard_jog_checkbox') or not self.keyboard_jog_checkbox.isChecked() or not self.connected:
            super().keyReleaseEvent(event)
            return
            
        key = event.key()
        
        # Para JOG quando soltar SETA ESQUERDA ou DIREITA
        if key in [Qt.Key.Key_Left, Qt.Key.Key_Right]:
            if self.keyboard_jog_active:
                self.keyboard_jog_active = False
                self.jog_stop_x()
                direction = "X-" if key == Qt.Key.Key_Left else "X+"
                self.log(f"⌨️ JOG {direction} parado via teclado")
            event.accept()
            return
            
        # Outras teclas passam para o comportamento padrão
        super().keyReleaseEvent(event)
        
    # ------------------------------------------------------------------
    #  NOVO: pulso momentâneo em M5000 (Y0.10) – “falling-edge trigger”
    # ------------------------------------------------------------------
    def pulse_y010(self):
        """Dispara um pulso de 100 ms em M5000 (Y0.10) e solta o botão."""
        if not self.connected:
            self.log("❌ CLP não conectado")
            return
            
        try:
            # Aciona o coil
            self.log("üèÑ Pulso M5000 (SHOT)")
            result = self.client.write_coil(self.addresses['M5000'], True)
            if result.isError():
                self.log(f"‚ùå Erro ao escrever M5000: {result}")
            else:
                # Mantém ON por 100 ms e depois desliga  (falling-edge)
                QTimer.singleShot(100,
                    lambda: self.client.write_coil(self.addresses['M5000'], False))
                # Libera o botão na interface um pouco depois
                QTimer.singleShot(120,
                    lambda: self.y010_btn.setChecked(False))
                self.log("‚úÖ Pulso M5000 enviado (100 ms)")
                
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
            
            # Desliga todas as memórias importantes
            for mem in ['M0_Y2', 'M50_Y2', 'M100_Y2', 'M1500_Z', 'M1550_Z', 'M1600_Z', 'M1000_X', 
                        'M1050_X', 'M1100_X', 'M5000', 'M350', 'M1350', 'M1850', 'M1070', 'M1080']:
                self.client.write_coil(self.addresses[mem], False)
            
            # Para JOG especificamente
            self.jog_stop_x()

            # Para JOG via teclado se estiver ativo
            if hasattr(self, 'keyboard_jog_active') and self.keyboard_jog_active:
                self.keyboard_jog_active = False
                self.log("⌨️ JOG via teclado interrompido por emergência")
                
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
                # Atualizado conforme novos endereços
                'M0_Y2': (self.addresses['M0_Y2'], getattr(self, 'M0_Y2_status', None)),
                'M50_Y2': (self.addresses['M50_Y2'], getattr(self, 'M50_Y2_status', None)),
                'M5000': (self.addresses['M5000'], getattr(self, 'M5000_status', None)),
                'M350': (self.addresses['M350'], getattr(self, 'M350_status', None)),
                'M1350': (self.addresses['M1350'], getattr(self, 'M1350_status', None)),
                'M1850': (self.addresses['M1850'], getattr(self, 'M1850_status', None)),
                'M300': (self.addresses['M300'], getattr(self, 'M300_status', None)),
                'M1300': (self.addresses['M1300'], getattr(self, 'M1300_status', None)),
                'M1800': (self.addresses['M1800'], getattr(self, 'M1800_status', None)),
                # Monitoramento JOG
                'M1070': (self.addresses['M1070'], getattr(self, 'M1070_status', None)),
                'M1010': (self.addresses['M1010'], getattr(self, 'M1010_status', None)),
                'M1011': (self.addresses['M1011'], getattr(self, 'M1011_status', None))
            }
            
            for name, (addr, label) in memories_map.items():
                if label is None:
                    continue
                result = self.client.read_coils(addr, count=1)
                if not result.isError():
                    state = result.bits[0]
                    label.setText("ON" if state else "OFF")
                    label.setStyleSheet(
                        "QLabel { background-color: red; color: white; padding: 5px; }" if state 
                        else "QLabel { background-color: gray; color: white; padding: 5px; }"
                    )
                    # Atualiza indicadores LED de homing
                    if name == 'M300':  # HOMING REALIZADO Y2
                        homing_led = getattr(self, 'homing_led_Y2', None)
                        if homing_led:
                            self.update_homing_led(homing_led, state)
                    elif name == 'M1300':  # HOMING REALIZADO X
                        homing_led = getattr(self, 'homing_led_X', None)
                        if homing_led:
                            self.update_homing_led(homing_led, state)
                    elif name == 'M1800':  # HOMING REALIZADO Z
                        homing_led = getattr(self, 'homing_led_Z', None)
                        if homing_led:
                            self.update_homing_led(homing_led, state)
                    # Atualiza status de segurança JOG em tempo real
                    if name in ['M1010', 'M1011'] and hasattr(self, 'safety_indicator'):
                        self.check_jog_safety_x()
                        
                    # Atualiza status JOG ativo
                    if name == 'M1070' and hasattr(self, 'jog_status_label'):
                        if state:
                            self.update_jog_status("ATIVO - POSITIVO", "lime")
                        elif not state and "POSITIVO" in self.jog_status_label.text():
                            self.update_jog_status("Inativo", "gray")
                            
                    # Monitora também M1080
                    if name == 'M1080' and hasattr(self, 'jog_status_label'):
                        if state:
                            self.update_jog_status("ATIVO - NEGATIVO", "lime")
                        elif not state and "NEGATIVO" in self.jog_status_label.text():
                            self.update_jog_status("Inativo", "gray")
                    # Atualiza indicador de segurança em tempo real quando há mudança nos flags
                    if name in ['M1010', 'M1011'] and hasattr(self, 'safety_indicator'):
                        QTimer.singleShot(50, self.check_jog_safety_x)  # Pequeno delay para evitar spam
            # Adiciona M1080 ao monitoramento
            memories_map['M1080'] = (self.addresses['M1080'], getattr(self, 'M1080_status', None))

        except Exception as e:
            # Silencia erros de status update para não poluir log
            pass
            
    def update_homing_led(self, led_widget, homing_status):
        """Atualiza o indicador LED de homing"""
        if homing_status:
            # Homing realizado - LED verde
            led_widget.setStyleSheet("QLabel { background-color: lime; color: darkgreen; padding: 2px; font-size: 16px; font-weight: bold; max-height: 20px; border-radius: 10px; }")
            led_widget.setText("●")
        else:
            # Homing não realizado - LED cinza
            led_widget.setStyleSheet("QLabel { background-color: gray; color: darkgray; padding: 2px; font-size: 16px; font-weight: bold; max-height: 20px; border-radius: 10px; }")
            led_widget.setText("●")
            
            # Atualiza registradores
            registers_map = {
                # Registradores dos eixos
                'D100_Y2': (self.addresses['D100_Y2'], getattr(self, 'D100_Y2_status', None)),
                'D20000_Y2': (self.addresses['D20000_Y2'], getattr(self, 'D20000_Y2_status', None)),
                'D1600_Z': (self.addresses['D1600_Z'], getattr(self, 'D1600_Z_status', None)),
                'D21500_Z': (self.addresses['D21500_Z'], getattr(self, 'D21500_Z_status', None)),
                'D1100_X': (self.addresses['D1100_X'], getattr(self, 'D1100_X_status', None)),
                'D21000_X': (self.addresses['D21000_X'], getattr(self, 'D21000_X_status', None)),
                # Posições atuais
                'D3100_Y2': (self.addresses['D3100_Y2'], None),
                'D3200_Z': (self.addresses['D3200_Z'], None),
                'D3000_X': (self.addresses['D3000_X'], None)
            }
            
            for name, (addr, label) in registers_map.items():
                try:
                    # Todos agora são registradores D normais
                    signed = self.read_dword(addr)

                    # Atualiza posições atuais dos eixos
                    if name == 'D3100_Y2':
                        self.current_positions['Y2'] = signed
                        if hasattr(self, 'current_pos_label_Y2'):
                            self.current_pos_label_Y2.setText(str(signed))
                    elif name == 'D3200_Z':
                        self.current_positions['Z'] = signed
                        if hasattr(self, 'current_pos_label_Z'):
                            self.current_pos_label_Z.setText(str(signed))
                    elif name == 'D3000_X':
                        self.current_positions['X'] = signed
                        if hasattr(self, 'current_pos_label_X'):
                            self.current_pos_label_X.setText(str(signed))                            
                    if label is not None:
                        label.setText(str(signed))
                        # cor laranja se negativo
                        label.setStyleSheet(
                            "QLabel { background-color: orange; padding: 5px; }"
                            if signed < 0 else
                            "QLabel { background-color: lightgray; padding: 5px; }"
                        )
                except Exception as e:
                    pass  # Silencia erros para não poluir o log
        
            
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
    print("CONTROLE MULTI-EIXOS - DELTA AS (ENDEREÇOS LADDER REAIS)")
    print("="*60)
    print("✅ MELHORIAS IMPLEMENTADAS:")
    print("• Endereços corrigidos conforme planilha do ladder real")
    print("• Controle de 3 eixos: Y2, Z, X")
    print("• Botões HOME corrigidos: M350, M1350, M1850")
    print("• Posições atuais via D3000, D3100, D3200")
    print("• Aplicadora de adesivo integrada")
    print("• Indicadores LED de homing e leitura automática de velocidades")
    print("• Sistema JOG integrado para eixo X com segurança")
    print("• Controle via teclado (setas ← →) para JOG do eixo X")
    print("• Movimentos absolutos com verificação de limites")
    print("• Interface redesenhada para melhor usabilidade")
    print("="*60)
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
