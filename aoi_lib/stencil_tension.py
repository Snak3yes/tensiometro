"""
Módulo: stencil_tension.py
Descrição: mede a tensão do stencil em um grid NxN e salva em JSON.
"""

import json
import serial
import serial.tools.list_ports
import numpy as np
import logging
import os
from pathlib import Path
from datetime import datetime
from PyQt6.QtCore import QThread, pyqtSignal, QTimer, Qt
from tkinter import Toplevel, Label, Entry, Button, messagebox
from PyQt6.QtWidgets import (
    QDialog, QGridLayout, QLabel, QLineEdit, QPushButton, QMessageBox,
    QComboBox, QGroupBox, QFrame, QHBoxLayout, QVBoxLayout, QProgressBar,
    QTreeWidget, QTreeWidgetItem, QSplitter, QInputDialog, QMenu, QWidget
)
from PyQt6.QtGui import QAction
from aoi_lib.plc_axis_controller import PLCAxisController
from PyQt6.QtCore import QThread, pyqtSignal
import time, logging

# Pasta para salvar rotinas de medição
ROUTINES_FOLDER = Path(__file__).parent.parent / "tension_routines"         

# Configure logging
log = logging.getLogger(__name__)

# ======== Gerenciador de Conexão Serial para Tensiômetro =========
class TensiometerSerialManager:
    """
    Gerencia conexão serial dedicada para o tensiômetro.
    Permite configurar porta, baudrate e parâmetros de comunicação.
    """
    
    def __init__(self):
        self.serial_connection = None
        self.is_connected = False
        self.port = None
        self.baudrate = 2400  # Padrão para tensiômetros AS-120N
        self.timeout = 1.0
        self.last_error = ""
        # Parâmetros específicos do AS-120N
        self.REQ_COMMAND = b'\x20'  # Comando de requisição
        self.FRAME_LEN = 9          # Tamanho do frame de resposta
        self.UNIT_MAP = {0x05: "N/cm²", 0x04: "kg/cm²", 0x06: "lb/cm²"}
        
    def _real_dig(self, b: int) -> int:
        """Converte nibble baixo deslocado (+0x0A) em dígito 0–9."""
        return ((b & 0x0F) + 10) % 10
    
    def _decode_frame(self, frame: bytes) -> float | None:
        """
        Decodifica um frame de 9 bytes do AS-120N.
        Retorna o valor em float (N/cm²).
        """
        if len(frame) < self.FRAME_LEN or frame[0] != 0x10 or frame[2] != 0x19:
            return None
        casas = (frame[3] >> 4) & 0x07
        d3 = self._real_dig(frame[6])
        d2 = self._real_dig(frame[7])
        d1 = self._real_dig(frame[8])
        raw = d3 * 100 + d2 * 10 + d1
        return raw / (10 ** casas)
        
    def get_available_ports(self):
        """Retorna lista de portas seriais disponíveis"""
        try:
            ports = [port.device for port in serial.tools.list_ports.comports()]
            return ports
        except Exception as e:
            log.error(f"Erro ao listar portas: {e}")
            return []
    
    def connect(self, port, baudrate=2400, timeout=1.0):
        """
        Conecta ao tensiômetro em uma porta específica
        
        Args:
            port: Porta COM (ex: 'COM3', '/dev/ttyUSB0')
            baudrate: Taxa de transmissão (padrão: 2400)
            timeout: Timeout para leitura em segundos
        """
        try:
            # Desconecta se já estiver conectado
            if self.is_connected:
                self.disconnect()
                
            # Cria nova conexão
            self.serial_connection = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=timeout
            )

            # Configuração específica para AS-120N
            self.serial_connection.dtr = False
            self.serial_connection.rts = False
            
            self.port = port
            self.baudrate = baudrate
            self.timeout = timeout
            self.is_connected = True
            self.last_error = ""
            
            log.info(f"Tensiômetro conectado em {port} @ {baudrate} baud")
            return True
            
        except Exception as e:
            self.last_error = str(e)
            log.error(f"Erro ao conectar tensiômetro: {e}")
            return False
    
    def disconnect(self):
        """Desconecta do tensiômetro"""
        try:
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.close()
                log.info("Tensiômetro desconectado")
        except Exception as e:
            log.error(f"Erro ao desconectar tensiômetro: {e}")
        finally:
            self.serial_connection = None
            self.is_connected = False
            self.port = None
    
    def read_tension_value(self):
        """
        Lê valor do tensiômetro AS-120N usando protocolo binário
        
        Returns:
            str: Valor formatado ou "0" em caso de erro
        """
        if not self.is_connected or not self.serial_connection:
            self.last_error = "Tensiômetro não conectado"
            return "0"
            
        try:
            # Limpa buffer de entrada
            self.serial_connection.reset_input_buffer()
            
            # Envia comando de requisição
            self.serial_connection.write(self.REQ_COMMAND)
            self.serial_connection.flush()
            
            # Aguarda resposta
            import time
            time.sleep(0.05)  # 50ms conforme exemplo
            
            # Lê frame de resposta (9 bytes exatos)
            raw_data = self.serial_connection.read(self.FRAME_LEN)
            
            if not raw_data:
                self.last_error = "Sem resposta do tensiômetro"
                return "0"
                
            if len(raw_data) != self.FRAME_LEN:
                self.last_error = f"Frame incompleto: {len(raw_data)} bytes (esperado: {self.FRAME_LEN})"
                return "0"
            
            # Decodifica o frame binário
            value = self._decode_frame(raw_data)
            
            if value is None:
                self.last_error = f"Frame inválido: {raw_data.hex(' ')}"
                return "0"
                
            # Retorna valor formatado
            return f"{value:.2f}"
            
        except Exception as e:
            self.last_error = str(e)
            log.error(f"Erro ao ler tensiômetro: {e}")
            return "0"
    
    def send_command(self, command):
        """
        Envia comando para o tensiômetro (se suportado)
        
        Args:
            command: Comando a ser enviado
        """
        if not self.is_connected or not self.serial_connection:
            return False
            
        try:
            cmd_bytes = (command + '\r\n').encode('ascii')
            self.serial_connection.write(cmd_bytes)
            self.serial_connection.flush()
            return True
        except Exception as e:
            self.last_error = str(e)
            log.error(f"Erro ao enviar comando: {e}")
            return False

# ======== Thread para Medição de Tensão =========
class TensionMeasurementThread(QThread):
    """
    Thread responsável por executar a medição de tensão em background,
    permitindo que a interface continue responsiva.
    """
    
    # Sinais para comunicação com a interface
    progress_updated = pyqtSignal(int, int, str)  # ponto_atual, total_pontos, status_msg
    measurement_completed = pyqtSignal(dict)      # ponto medido com dados
    finished = pyqtSignal(list)                   # lista completa de medições
    error_occurred = pyqtSignal(str)              # mensagem de erro
    
    def __init__(self, cnc_controller, tensiometer, points, z_down, z_move, 
                 user_feed, stabilization_time, parameters):
        super().__init__()
        self.cnc = cnc_controller
        self.tensiometer = tensiometer
        self.points = points
        self.z_down        = z_down
        self.z_move        = z_move
        self.user_feed = user_feed
        self.stabilization_time = stabilization_time
        self.parameters = parameters
        self.measurements = []
        self._stop_requested = False
        
    def request_stop(self):
        """Solicita parada da medição"""
        self._stop_requested = True
        
    def run(self):
        """Executa o processo de medição"""
        try:
            log = logging.getLogger("TensionMeasurementThread")
            log.info("Iniciando medição de tensão em thread separada")
            
            # Garante modo absoluto
            if hasattr(self.cnc, "set_absolute_mode"):
                self.cnc.set_absolute_mode()
            else:
                if hasattr(self.cnc, "send_raw_gcode"):
                    self.cnc.send_raw_gcode("G90")
            
            # Move para altura de movimentação (safe height)
            self._move_abs(z=self.z_move, feed=self.user_feed)
            
            total_points = len(self.points)
            
            for idx, (x, y) in enumerate(self.points, 1):
                # Verifica se foi solicitada a parada
                if self._stop_requested:
                    log.info("Medição interrompida pelo usuário")
                    self.error_occurred.emit("Medição interrompida pelo usuário")
                    return
                
                log.debug("Ponto %d de %d -> X%.3f Y%.3f", idx, total_points, x, y)
                
                # Emite progresso
                self.progress_updated.emit(idx, total_points, f"Medindo ponto {idx}/{total_points}")
                
                # 1) Move XY mantendo a safe height
                self._move_abs(x=x, y=y, z=self.z_move, feed=self.user_feed)
                
                # 2) Desce até a altura de medição
                self._move_abs(z=self.z_down, feed=self.user_feed)
                
                # 3) Aguarda estabilização
                stabilization_sec = self.stabilization_time / 1000.0
                log.debug("Aguardando estabilização por %.1fs...", stabilization_sec)
                time.sleep(stabilization_sec)
                
                # 4) Lê tensão
                tension = self.tensiometer.read_tension_value()
                log.debug("Tensão medida no ponto %d: %s", idx, tension)
                
                # 5) Salva medição
                measurement = {"x": x, "y": y, "z": self.z_down, "tension": tension}
                self.measurements.append(measurement)
                
                # Emite medição individual
                self.measurement_completed.emit(measurement)
                
                # 6) Retorna para a safe height
                self._move_abs(z=self.z_move, feed=self.user_feed)
                
                # 7) Pequena pausa entre pontos
                time.sleep(0.1)
            
            # Emite resultado final
            log.info("Medição de tensão concluída com sucesso")
            # Desliga o sensor de tensão (pulso de 3000 ms na memória M0)
            try:
                if hasattr(self.cnc, "_pulse_coil"):
                    self.cnc._pulse_coil(0, 3000)
            except Exception as e:
                log.error(f"Falha ao desligar sensor: {e}")
            # Emite sinal de finalização
            self.finished.emit(self.measurements)
            
        except Exception as e:
            log.error(f"Erro durante medição: {e}", exc_info=True)
            self.error_occurred.emit(f"Erro durante medição: {str(e)}")
    
    def _move_abs(self, *, x=None, y=None, z=None, feed=None):
        """Move em coordenadas absolutas"""
        if feed is not None:
            self.cnc.move_to_absolute_position(x=x, y=y, z=z, feed_rate=feed)
        else:
            self.cnc.move_to_absolute_position(x=x, y=y, z=z)
        self.cnc.wait_for_idle()
    
    def _move_rel(self, *, x=None, y=None, z=None, feed=None):
        """Move em coordenadas relativas"""
        kwargs = {}
        if x is not None: kwargs['x'] = x
        if y is not None: kwargs['y'] = y
        if z is not None: kwargs['z'] = z
        if feed is not None: kwargs['feed_rate'] = feed
        self.cnc.move_relative(**kwargs)
        self.cnc.wait_for_idle()


# ======== Classe principal =========
class StencilTensionMeasurement:
    """
    Abre uma janela para o usuário inserir:
        • ponto inicial  (X,Y)
        • ponto final    (X,Y)
        • quantidade N   (grid NxN)
        • altura Z
    Movimenta o CNC, lê o tensiômetro e grava JSON.
    """

    def __init__(self, master, serial_handler):
        self.master = master
        self.serial_handler = serial_handler     # já existente na aplicação
        self.window = None

    # ---------- GUI ----------
    def show_window(self):
        self.window = Toplevel(self.master)
        self.window.title("Tensão do Stencil")
        self.window.resizable(False, False)

        # ---- Entradas ----
        Label(self.window, text="Ponto Inicial").grid(row=0, column=0, columnspan=4, pady=(5, 0))
        Label(self.window, text="X:").grid(row=1, column=0)
        self.start_x = Entry(self.window, width=8); self.start_x.grid(row=1, column=1)
        Label(self.window, text="Y:").grid(row=1, column=2)
        self.start_y = Entry(self.window, width=8); self.start_y.grid(row=1, column=3)

        Label(self.window, text="Ponto Final").grid(row=2, column=0, columnspan=4, pady=(10, 0))
        Label(self.window, text="X:").grid(row=3, column=0)
        self.end_x = Entry(self.window, width=8); self.end_x.grid(row=3, column=1)
        Label(self.window, text="Y:").grid(row=3, column=2)
        self.end_y = Entry(self.window, width=8); self.end_y.grid(row=3, column=3)

        Label(self.window, text="Quantidade (N):").grid(row=4, column=0, pady=(10, 0))
        self.quantity = Entry(self.window, width=8); self.quantity.grid(row=4, column=1)

        Label(self.window, text="Altura Z:").grid(row=4, column=2, pady=(10, 0))
        self.height = Entry(self.window, width=8); self.height.grid(row=4, column=3)

        Button(self.window, text="Iniciar Medição", command=self.start_measurement)\
            .grid(row=5, column=0, columnspan=4, pady=15)

    # ---------- Cálculo do grid ----------
    def calculate_grid_points(self):
        try:
            sx, sy = float(self.start_x.get()), float(self.start_y.get())
            ex, ey = float(self.end_x.get()), float(self.end_y.get())
            n = int(self.quantity.get())

            if n < 2:
                raise ValueError

            x_points = np.linspace(sx, ex, n)
            y_points = np.linspace(sy, ey, n)
            return [(float(x), float(y)) for x in x_points for y in y_points]
        except ValueError:
            messagebox.showerror("Erro", "Preencha todos os campos corretamente.\n"
                                         "Quantidade deve ser um inteiro >= 2.")
            return None

    # ---------- Loop de medição ----------
    def start_measurement(self):
        points = self.calculate_grid_points()
        if points is None:
            return

        try:
            z = float(self.height.get())
        except ValueError:
            messagebox.showerror("Erro", "Altura Z inválida.")
            return

        measurements = []
        for x, y in points:
            # Move XY
            self.serial_handler.send_command(f"G0 X{x:.3f} Y{y:.3f}")
            # Baixa Z
            self.serial_handler.send_command(f"G1 Z{z:.3f}")

            # ---- Lê tensiômetro ----
            tension = self.read_tensiometer_value()
            measurements.append({"x": x, "y": y, "z": z, "tension": tension})

            # Sobe Z (evita arrastar o sensor)
            self.serial_handler.send_command("G1 Z0")

        self.save_json(measurements)
        messagebox.showinfo("Concluído", "Medições finalizadas e arquivo salvo.")
        self.window.destroy()

    # ---------- Leitura do tensiômetro ----------
    def read_tensiometer_value(self):
        """
        Exemplo de leitura (AS-120N a 2400 baud, 8N1).
        Adapte se seu serial_handler já contiver método apropriado.
        """
        ser: serial.Serial = self.serial_handler.serial  # porta já aberta pelo app
        raw = ser.readline().decode(errors="ignore").strip()
        return raw or "0"

    # ---------- Salva resultado ----------
    def save_json(self, measurements):
        data = {
            "type": "stencil_tension",
            "parameters": {
                "start": {"x": float(self.start_x.get()), "y": float(self.start_y.get())},
                "end":   {"x": float(self.end_x.get()),   "y": float(self.end_y.get())},
                "quantity": int(self.quantity.get()),
                "height":   float(self.height.get())
            },
            "measurements": measurements
        }
        with open("stencil_tension_measurements.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)


# --------------------------------------------------------------------
#  NOVA VERSÃO PyQt6  – compatível com AOIControllerApp (consumo_lib.py)
# --------------------------------------------------------------------

class StencilTensionDialog(QDialog):
    """
    Diálogo PyQt6 para medir tensão do stencil em um grid NxN.
    Usa cntrl_cnc (GRBLCNCController) para movimentação.
    """
    def __init__(self, parent, cntrl_cnc):
        super().__init__(parent)
        self.setWindowTitle("Tensão do Stencil")
        self.setMinimumWidth(900)
        self.setMinimumHeight(600)
        self.cnc = cntrl_cnc
        # Inicializa gerenciador do tensiômetro
        self.tensiometer = TensiometerSerialManager()
        self.measurement_thread = None
        # Cria pasta de rotinas se não existir
        ROUTINES_FOLDER.mkdir(parents=True, exist_ok=True)
        self._current_routine_path = None  # Caminho da rotina carregada
        self._build_ui()
        # Popula lista de portas disponíveis
        self._refresh_ports()
        # Carrega lista de rotinas
        self._refresh_routines()

    # --------------------------- UI ---------------------------------
    def _build_ui(self):
        # Layout principal com splitter
        main_layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # ================== PAINEL ESQUERDO: ROTINAS ==================
        routines_widget = QWidget()
        routines_layout = QVBoxLayout(routines_widget)
        routines_layout.setContentsMargins(0, 0, 0, 0)
        
        routines_group = QGroupBox("Rotinas Salvas")
        routines_group_layout = QVBoxLayout(routines_group)
        
        # TreeView de rotinas
        self.routines_tree = QTreeWidget()
        self.routines_tree.setHeaderLabels(["Nome", "Pontos", "Data"])
        self.routines_tree.setColumnWidth(0, 150)
        self.routines_tree.setColumnWidth(1, 50)
        self.routines_tree.setColumnWidth(2, 100)
        self.routines_tree.itemDoubleClicked.connect(self._on_routine_double_clicked)
        self.routines_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.routines_tree.customContextMenuRequested.connect(self._on_routine_context_menu)
        routines_group_layout.addWidget(self.routines_tree)
        
        # Botões de gestão de rotinas
        routines_btn_layout = QHBoxLayout()
        self.btn_load_routine = QPushButton("▶ Carregar")
        self.btn_load_routine.clicked.connect(self._load_selected_routine)
        routines_btn_layout.addWidget(self.btn_load_routine)
        
        self.btn_save_routine = QPushButton("💾 Salvar Como...")
        self.btn_save_routine.clicked.connect(self._save_routine_as)
        routines_btn_layout.addWidget(self.btn_save_routine)
        
        self.btn_delete_routine = QPushButton("🗑 Excluir")
        self.btn_delete_routine.clicked.connect(self._delete_selected_routine)
        routines_btn_layout.addWidget(self.btn_delete_routine)
        
        routines_group_layout.addLayout(routines_btn_layout)
        
        self.btn_refresh_routines = QPushButton("🔄 Atualizar Lista")
        self.btn_refresh_routines.clicked.connect(self._refresh_routines)
        routines_group_layout.addWidget(self.btn_refresh_routines)
        
        routines_layout.addWidget(routines_group)
        splitter.addWidget(routines_widget)
        
        # ================== PAINEL DIREITO: CONFIGURAÇÕES ==================
        config_widget = QWidget()
        lay = QGridLayout(config_widget)
        r = 0
        # Grupo de Conexão do Tensiômetro
        conn_group = QGroupBox("Conexão do Tensiômetro")
        conn_layout = QGridLayout(conn_group)
        
        # Porta Serial
        conn_layout.addWidget(QLabel("Porta:"), 0, 0)
        self.port_combo = QComboBox()
        conn_layout.addWidget(self.port_combo, 0, 1)
        
        # Baudrate
        conn_layout.addWidget(QLabel("Baudrate:"), 0, 2)
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.addItems(["2400", "9600", "19200", "38400", "57600", "115200"])
        self.baudrate_combo.setCurrentText("2400")
        conn_layout.addWidget(self.baudrate_combo, 0, 3)
        
        # Botões de conexão
        self.refresh_ports_btn = QPushButton("Atualizar")
        self.refresh_ports_btn.clicked.connect(self._refresh_ports)
        conn_layout.addWidget(self.refresh_ports_btn, 1, 0)
        
        self.connect_btn = QPushButton("Conectar")
        self.connect_btn.clicked.connect(self._toggle_connection)
        conn_layout.addWidget(self.connect_btn, 1, 1)
        
        self.test_btn = QPushButton("Testar Leitura")
        self.test_btn.clicked.connect(self._test_reading)
        self.test_btn.setEnabled(False)
        conn_layout.addWidget(self.test_btn, 1, 2)
        
        # Status da conexão
        self.connection_status = QLabel("Desconectado")
        self.connection_status.setStyleSheet("color: red; font-weight: bold;")
        conn_layout.addWidget(self.connection_status, 1, 3)
        
        lay.addWidget(conn_group, r, 0, 1, 5); r += 1

        # -------------------------------------------------------------------
        # botão liga/desliga (toggle) para enviar pulso a M0
        # -------------------------------------------------------------------
        self.power_btn = QPushButton("Ligar")
        self.power_btn.setCheckable(True)
        self.power_btn.toggled.connect(self._on_power_toggle)
        conn_layout.addWidget(self.power_btn, 2, 0, 1, 4)
        
        # Separador
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        lay.addWidget(line, r, 0, 1, 5); r += 1

        # Grupo de Configurações Avançadas
        adv_group = QGroupBox("Configurações de Medição")
        adv_layout = QGridLayout(adv_group)
        
        adv_layout.addWidget(QLabel("Tempo de estabilização (ms):"), 0, 0)
        self.stabilization_time = QLineEdit("500")
        self.stabilization_time.setToolTip("Tempo de espera após descida do Z antes da leitura")
        adv_layout.addWidget(self.stabilization_time, 0, 1)

        # Velocidade de movimentação configurável
        adv_layout.addWidget(QLabel("Velocidade de movimentação (mm/min):"), 1, 0)
        self.movement_feed = QLineEdit("30")
        self.movement_feed.setToolTip("Velocidade para todas as movimentações durante a medição")
        adv_layout.addWidget(self.movement_feed, 1, 1)
        
        adv_group.setLayout(adv_layout)
        lay.addWidget(adv_group, r, 0, 1, 5); r += 1

        # Campos reorganizados: Quantidade → Inicial → Final → Altura de Movimentação → Altura de Medição
        # 1) Quantidade
        lay.addWidget(QLabel("Quantidade (N):"), r, 0)
        self.ed_n       = QLineEdit("3");       lay.addWidget(self.ed_n, r, 1)
        r += 1

        # 2) Ponto Inicial
        lay.addWidget(QLabel("<b>Ponto Inicial</b>"), r, 0, 1, 5)
        r += 1
        lay.addWidget(QLabel("X:"), r, 0)
        self.ed_sx      = QLineEdit();          lay.addWidget(self.ed_sx, r, 1)
        lay.addWidget(QLabel("Y:"), r, 2)
        self.ed_sy      = QLineEdit();          lay.addWidget(self.ed_sy, r, 3)
        btn_cap_start  = QPushButton("Capturar"); lay.addWidget(btn_cap_start, r, 4)
        r += 1

        # 3) Ponto Final
        lay.addWidget(QLabel("<b>Ponto Final</b>"), r, 0, 1, 5)
        r += 1
        lay.addWidget(QLabel("X:"), r, 0)
        self.ed_ex      = QLineEdit();          lay.addWidget(self.ed_ex, r, 1)
        lay.addWidget(QLabel("Y:"), r, 2)
        self.ed_ey      = QLineEdit();          lay.addWidget(self.ed_ey, r, 3)
        btn_cap_end    = QPushButton("Capturar"); lay.addWidget(btn_cap_end, r, 4)
        r += 1

        # 4) Altura de Movimentação (safe height)
        lay.addWidget(QLabel("Altura de Movimentação (mm):"), r, 2)
        self.ed_move_z  = QLineEdit("0");       lay.addWidget(self.ed_move_z, r, 3)
        btn_cap_move_z = QPushButton("Capturar"); lay.addWidget(btn_cap_move_z, r, 4)
        r += 1

        # 5) Altura de Medição
        lay.addWidget(QLabel("Altura de Medição (mm):"), r, 2)
        self.ed_z       = QLineEdit("2");       lay.addWidget(self.ed_z, r, 3)
        btn_cap_z      = QPushButton("Capturar"); lay.addWidget(btn_cap_z, r, 4)
        r += 1
        measurement_buttons_layout = QHBoxLayout()
        self.start_measurement_btn = QPushButton("Iniciar Medição")
        self.stop_measurement_btn = QPushButton("Parar Medição")
        self.stop_measurement_btn.setEnabled(False)
        measurement_buttons_layout.addWidget(self.start_measurement_btn)
        measurement_buttons_layout.addWidget(self.stop_measurement_btn)
        lay.addLayout(measurement_buttons_layout, r, 0, 1, 5); r += 1
        
        # Barra de progresso
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        lay.addWidget(self.progress_bar, r, 0, 1, 5); r += 1
        
        # Labels de status
        self.status_label = QLabel("")
        lay.addWidget(self.status_label, r, 0, 1, 5); r += 1

        # Conexões ------------------------------------------------------
        self.start_measurement_btn.clicked.connect(self._on_start)
        self.stop_measurement_btn.clicked.connect(self._on_stop)
        btn_cap_start.clicked.connect(self._capture_start_xy)
        btn_cap_end.clicked.connect(self._capture_end_xy)
        btn_cap_z.clicked.connect(self._capture_z_height)
        btn_cap_move_z.clicked.connect(self._capture_move_z_height)
        
        # Finaliza splitter e layout principal
        splitter.addWidget(config_widget)
        splitter.setSizes([250, 650])  # Tamanhos iniciais dos painéis
        main_layout.addWidget(splitter)

    def _on_power_toggle(self, checked: bool):
        """
        Liga/desliga o tensiômetro enviando um pulso para a memória M0:
          - ao ligar (checked=True): pulso de 100 ms
          - ao desligar (checked=False): pulso de 3000 ms
        """
        coil_addr = 0      # M0
        duration = 100 if checked else 3000
        # Atualiza texto do botão
        self.power_btn.setText("Desligar" if checked else "Ligar")
        try:
            # Aciona o coil
            self.cnc.client.write_coil(coil_addr, True)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao acionar M0: {e}")
            # desfaz toggle se houver erro
            self.power_btn.setChecked(not checked)
            return
        # Programa desligamento após a duração
        QTimer.singleShot(duration,
            lambda: self.cnc.client.write_coil(coil_addr, False)
        )

    # ---------------------- Conexão do Tensiômetro ----------------------
    def _refresh_ports(self):
        """Atualiza lista de portas disponíveis"""
        self.port_combo.clear()
        ports = self.tensiometer.get_available_ports()
        
        if ports:
            self.port_combo.addItems(ports)
        else:
            self.port_combo.addItem("Nenhuma porta encontrada")
    
    def _toggle_connection(self):
        """Conecta/desconecta do tensiômetro"""
        if self.tensiometer.is_connected:
            # Desconectar
            self.tensiometer.disconnect()
            self.connect_btn.setText("Conectar")
            self.test_btn.setEnabled(False)
            self.connection_status.setText("Desconectado")
            self.connection_status.setStyleSheet("color: red; font-weight: bold;")
            
        else:
            # Conectar
            port = self.port_combo.currentText()
            if port == "Nenhuma porta encontrada":
                QMessageBox.warning(self, "Erro", "Nenhuma porta disponível")
                return
                
            baudrate = int(self.baudrate_combo.currentText())
            
            if self.tensiometer.connect(port, baudrate):
                self.connect_btn.setText("Desconectar")
                self.test_btn.setEnabled(True)
                self.connection_status.setText(f"Conectado - {port}")
                self.connection_status.setStyleSheet("color: green; font-weight: bold;")
            else:
                QMessageBox.critical(
                    self, "Erro de Conexão", 
                    f"Falha ao conectar:\n{self.tensiometer.last_error}"
                )
    
    def _test_reading(self):
        """Testa leitura do tensiômetro"""
        if not self.tensiometer.is_connected:
            QMessageBox.warning(self, "Erro", "Tensiômetro não conectado")
            return
            
        value = self.tensiometer.read_tension_value()
        
        if value != "0" or not self.tensiometer.last_error:
            QMessageBox.information(
                self, "Teste de Leitura", 
                f"Valor lido: {value}"
            )
        else:
            QMessageBox.warning(
                self, "Erro de Leitura",
                f"Falha na leitura:\n{self.tensiometer.last_error}"
            )
    
    def _get_user_feed_rate(self):
        """
        Obtém a velocidade de movimentação configurada pelo usuário.
        Retorna valor padrão se inválido.
        """
        try:
            feed = float(self.movement_feed.text())
            if feed <= 0:
                return 1000.0  # fallback
            return feed
        except ValueError:
            return 1000.0  # fallback se valor inválido

    # ---------------------- helpers --------------------------------
    # ------------- wrappers de movimentação com espera -------------
    def _move_abs(self, *, x=None, y=None, z=None, feed=None):
        """
        Move em coordenadas absolutas.
        feed → mapeado para feed_rate exigido pelo GRBLCNCController.
        """
        if feed is None:
            feed = self._get_user_feed_rate()
        if feed is not None:
            self.cnc.move_to_absolute_position(
                x=x, y=y, z=z, feed_rate=feed
            )
        else:
            self.cnc.move_to_absolute_position(
                x=x, y=y, z=z
            )
        self.cnc.wait_for_idle()

    def _move_rel(self, *, x=None, y=None, z=None, feed=None):
        """
        Move em coordenadas relativas.
        feed → feed_rate.
        """
        if feed is None:
            feed = self._get_user_feed_rate()
        kwargs = {}
        if x is not None: kwargs['x'] = x
        if y is not None: kwargs['y'] = y
        if z is not None: kwargs['z'] = z
        if feed is not None: kwargs['feed_rate'] = feed
        self.cnc.move_relative(**kwargs)
        self.cnc.wait_for_idle()

    def _grid_points(self):
        try:
            sx, sy = float(self.ed_sx.text()), float(self.ed_sy.text())
            ex, ey = float(self.ed_ex.text()), float(self.ed_ey.text())
            n = int(self.ed_n.text())
            if n < 2:
                raise ValueError
            xs = np.linspace(sx, ex, n)
            ys = np.linspace(sy, ey, n)
            points = []
            for idx_row, y in enumerate(ys):
                row_xs = xs if idx_row % 2 == 0 else xs[::-1]   # zig-zag
                for x in row_xs:
                    points.append((float(x), float(y)))
            return points
        except ValueError:
            QMessageBox.warning(self, "Erro", "Preencha todos os valores corretamente (N ≥ 2).")
            return None
    
    # --------------- captura automática de posições -----------------
    def _require_connection(self) -> bool:
        if not self.cnc.is_connected:
            QMessageBox.warning(self, "Erro", "CNC não conectada")
            return False
        return True

    def _capture_start_xy(self):
        if not self._require_connection():
            return
        pos = self.cnc.get_current_position()
        self.ed_sx.setText(f"{pos['x']:.3f}")
        self.ed_sy.setText(f"{pos['y']:.3f}")

    def _capture_end_xy(self):
        if not self._require_connection():
            return
        pos = self.cnc.get_current_position()
        self.ed_ex.setText(f"{pos['x']:.3f}")
        self.ed_ey.setText(f"{pos['y']:.3f}")

    def _capture_z_height(self):
        if not self._require_connection():
            return
        pos = self.cnc.get_current_position()
        # Usa valor absoluto para sempre baixar – usuário pode ajustar depois
        self.ed_z.setText(f"{abs(pos['z']):.3f}")
    
    def _capture_move_z_height(self):
        """Captura a altura de movimentação (safe height) atual."""
        if not self._require_connection():
            return
        pos = self.cnc.get_current_position()
        self.ed_move_z.setText(f"{abs(pos['z']):.3f}")

    def _read_tension(self):
        """
        Lê valor do tensiômetro usando a conexão dedicada
        """
        if not self.tensiometer.is_connected:
            log.warning("Tentativa de leitura com tensiômetro desconectado")
            return "0"
        return self.tensiometer.read_tension_value()

    # --------------------- ciclo principal --------------------------
    def _on_start(self):
        """Inicia o processo de medição em thread separada"""
        pts = self._grid_points()
        if pts is None:
            return

        # 1) Parse das alturas
        try:
            z_measure = float(self.ed_z.text())
            z_move    = float(self.ed_move_z.text())
        except ValueError:
            QMessageBox.warning(self, "Erro", "Alturas inválidas.")
            return
        z_down = z_measure

        # --- Rotina automática de checagem do sensor ---
        try:
            # a) Liga o sensor via pulso de 100 ms em M0 (somente CLP)
            if not hasattr(self.cnc, '_pulse_coil'):
                QMessageBox.warning(
                    self, "Erro",
                    "Controle de sensor não disponível neste backend"
                )
                return
            try:
                # Dispara o pulso de 100 ms
                self.cnc._pulse_coil(0, 100)
            except Exception as e:
                QMessageBox.critical(
                    self, "Erro",
                    f"Falha ao acionar sensor: {e}"
                )
                return
            # Atualiza visual do botão para 'Desligar', sem disparar _on_power_toggle
            self.power_btn.blockSignals(True)
            self.power_btn.setChecked(True)
            self.power_btn.setText("Desligar")
            self.power_btn.blockSignals(False)
            # b) Aguarda 1 s para estabilização antes de conectar o serial
            time.sleep(1.0)
            # c) Conecta ao tensiômetro (porta + baud da UI)
            port = self.port_combo.currentText()
            baud = int(self.baudrate_combo.currentText())
            if not self.tensiometer.connect(port, baud):
                QMessageBox.critical(
                    self, "Erro", 
                    f"Falha ao conectar tensiômetro:\n{self.tensiometer.last_error}"
                )
                return
            # d) Aguarda 1 s
            time.sleep(1.0)
            # e) Testa leitura inicial (deve ser zero)
            raw = self.tensiometer.read_tension_value()
            try:
                val = float(raw)
            except ValueError:
                QMessageBox.critical(
                    self, "Erro", 
                    f"Leitura inválida do sensor: '{raw}'"
                )
                return
            if abs(val) > 1e-6:
                QMessageBox.critical(
                    self, "Erro", 
                    f"Leitura inicial deve ser 0.0, obtido {val:.2f}"
                )
                return
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro na checagem do sensor:\n{e}")
            return

        # Verifica conexão com CNC
        if not self.cnc.is_connected:
            QMessageBox.warning(self, "Erro", "CNC não conectada")
            return
        
        # Obtém parâmetros de configuração
        user_feed = self._get_user_feed_rate()
        try:
            stabilization_ms = int(self.stabilization_time.text())
        except ValueError:
            stabilization_ms = 500  # fallback
        
        # Parâmetros para salvar no JSON
        parameters = {
            "start": {"x": float(self.ed_sx.text()), "y": float(self.ed_sy.text())},
            "end":   {"x": float(self.ed_ex.text()), "y": float(self.ed_ey.text())},
            "quantity": int(self.ed_n.text()),
            "measurement_height": float(self.ed_z.text()),
            "movement_height":    float(self.ed_move_z.text())
        }
        
        # Configura interface para medição
        self._setup_measurement_ui(len(pts))
        
        # Cria e inicia thread de medição
        self.measurement_thread = TensionMeasurementThread(
            self.cnc, self.tensiometer, pts,
            z_down, z_move,
            user_feed, stabilization_ms, parameters
        )
        
        # Conecta sinais
        self.measurement_thread.progress_updated.connect(self._on_progress_updated)
        self.measurement_thread.measurement_completed.connect(self._on_measurement_completed)
        self.measurement_thread.finished.connect(self._on_measurement_finished)
        self.measurement_thread.error_occurred.connect(self._on_measurement_error)
        
        # Inicia medição
        self.measurement_thread.start()
    
    def _on_stop(self):
        """Para o processo de medição"""
        if self.measurement_thread and self.measurement_thread.isRunning():
            self.measurement_thread.request_stop()
            self.status_label.setText("Parando medição...")
            self.stop_measurement_btn.setEnabled(False)
    
    def _setup_measurement_ui(self, total_points):
        """Configura interface para medição"""
        self.start_measurement_btn.setEnabled(False)
        self.stop_measurement_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, total_points)
        self.progress_bar.setValue(0)
        self.status_label.setText("Iniciando medição...")
    
    def _reset_measurement_ui(self):
        """Reseta interface após medição"""
        self.start_measurement_btn.setEnabled(True)
        self.stop_measurement_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_label.setText("")
    
    def _on_progress_updated(self, current, total, status_msg):
        """Atualiza progresso da medição"""
        self.progress_bar.setValue(current)
        self.status_label.setText(status_msg)
        
        # Atualiza título da janela com progresso
        self.setWindowTitle(f"Tensão do Stencil - {current}/{total}")
    
    def _on_measurement_completed(self, measurement):
        """Chamado quando uma medição individual é completada"""
        # Aqui pode adicionar lógica para processar cada medição individual
        # Por exemplo, mostrar em uma tabela em tempo real
        log.debug(f"Medição completada: {measurement}")
    
    def _on_measurement_finished(self, measurements):
        """Chamado quando todas as medições são completadas"""
        self._reset_measurement_ui()
        self.setWindowTitle("Tensão do Stencil")
        
        # Salva resultados (agora incluindo both heights)
        try:
            parameters = {
                "start": {"x": float(self.ed_sx.text()), "y": float(self.ed_sy.text())},
                "end":   {"x": float(self.ed_ex.text()), "y": float(self.ed_ey.text())},
                "quantity": int(self.ed_n.text()),
                "measurement_height": float(self.ed_z.text()),
                "movement_height":    float(self.ed_move_z.text())
            }
            
            data = {
                "type": "stencil_tension",
                "parameters": parameters,
                "measurements": measurements
            }
            
            with open("stencil_tension_measurements.json", "w", encoding="utf-8") as fp:
                json.dump(data, fp, indent=4, ensure_ascii=False)
                
            QMessageBox.information(
            self, "Concluído", 
            f"Medição concluída!\n"
            f"Total de pontos: {len(measurements)}\n"
            f"Arquivo salvo: stencil_tension_measurements.json"
        )
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao salvar resultados: {e}")
    
    def _on_measurement_error(self, error_msg):
        """Chamado quando ocorre erro na medição"""
        self._reset_measurement_ui()
        self.setWindowTitle("Tensão do Stencil")
        QMessageBox.critical(self, "Erro na Medição", error_msg)
    
    def closeEvent(self, event):
        """Garante desconexão e parada da thread ao fechar o diálogo"""
        # Para thread se estiver rodando
        if self.measurement_thread and self.measurement_thread.isRunning():
            self.measurement_thread.request_stop()
            self.measurement_thread.wait(3000)  # Aguarda até 3 segundos
        
        # Desconecta tensiômetro
        if self.tensiometer.is_connected:
            self.tensiometer.disconnect()
            
        super().closeEvent(event)

    # ====================== GESTÃO DE ROTINAS ======================
    
    def _refresh_routines(self):
        """Atualiza a lista de rotinas salvas na TreeView"""
        self.routines_tree.clear()
        
        if not ROUTINES_FOLDER.exists():
            return
        
        for filepath in sorted(ROUTINES_FOLDER.glob("*.json")):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Extrai informações
                name = filepath.stem
                params = data.get("parameters", {})
                qty = params.get("quantity", "?")
                points = f"{qty}x{qty}"
                
                # Data de modificação
                mod_time = datetime.fromtimestamp(filepath.stat().st_mtime)
                date_str = mod_time.strftime("%Y-%m-%d %H:%M")
                
                # Adiciona à tree
                item = QTreeWidgetItem([name, points, date_str])
                item.setData(0, Qt.ItemDataRole.UserRole, str(filepath))
                self.routines_tree.addTopLevelItem(item)
                
            except Exception as e:
                log.warning(f"Erro ao carregar rotina {filepath}: {e}")
    
    def _save_routine_as(self):
        """Salva a configuração atual como uma nova rotina"""
        # Pede nome para a rotina
        name, ok = QInputDialog.getText(
            self, "Salvar Rotina", 
            "Nome da rotina:",
            text=datetime.now().strftime("Rotina_%Y%m%d_%H%M%S")
        )
        
        if not ok or not name.strip():
            return
        
        # Sanitiza o nome
        safe_name = "".join(c for c in name if c.isalnum() or c in "._- ").strip()
        if not safe_name:
            QMessageBox.warning(self, "Erro", "Nome inválido para a rotina.")
            return
        
        filepath = ROUTINES_FOLDER / f"{safe_name}.json"
        
        # Verifica se já existe
        if filepath.exists():
            result = QMessageBox.question(
                self, "Confirmar Sobrescrita",
                f"A rotina '{safe_name}' já existe. Deseja sobrescrever?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if result != QMessageBox.StandardButton.Yes:
                return
        
        # Coleta os parâmetros atuais
        try:
            routine_data = {
                "type": "stencil_tension_routine",
                "name": safe_name,
                "created_at": datetime.now().isoformat(),
                "parameters": {
                    "start": {
                        "x": float(self.ed_sx.text() or 0),
                        "y": float(self.ed_sy.text() or 0)
                    },
                    "end": {
                        "x": float(self.ed_ex.text() or 0),
                        "y": float(self.ed_ey.text() or 0)
                    },
                    "quantity": int(self.ed_n.text() or 3),
                    "measurement_height": float(self.ed_z.text() or 2),
                    "movement_height": float(self.ed_move_z.text() or 0),
                    "stabilization_time": int(self.stabilization_time.text() or 500),
                    "movement_feed": float(self.movement_feed.text() or 30)
                },
                "tensiometer": {
                    "baudrate": self.baudrate_combo.currentText()
                }
            }
            
            # Salva o arquivo
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(routine_data, f, indent=4, ensure_ascii=False)
            
            self._current_routine_path = filepath
            self.setWindowTitle(f"Tensão do Stencil - {safe_name}")
            
            QMessageBox.information(
                self, "Sucesso", 
                f"Rotina '{safe_name}' salva com sucesso!"
            )
            
            # Atualiza a lista
            self._refresh_routines()
            
        except ValueError as e:
            QMessageBox.warning(self, "Erro", f"Valores inválidos nos campos: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao salvar rotina: {e}")
    
    def _load_selected_routine(self):
        """Carrega a rotina selecionada na TreeView"""
        item = self.routines_tree.currentItem()
        if not item:
            QMessageBox.warning(self, "Aviso", "Selecione uma rotina para carregar.")
            return
        
        filepath = Path(item.data(0, Qt.ItemDataRole.UserRole))
        self._load_routine(filepath)
    
    def _load_routine(self, filepath: Path):
        """Carrega uma rotina de um arquivo"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            params = data.get("parameters", {})
            
            # Preenche os campos
            start = params.get("start", {})
            end = params.get("end", {})
            
            self.ed_sx.setText(str(start.get("x", "")))
            self.ed_sy.setText(str(start.get("y", "")))
            self.ed_ex.setText(str(end.get("x", "")))
            self.ed_ey.setText(str(end.get("y", "")))
            self.ed_n.setText(str(params.get("quantity", 3)))
            self.ed_z.setText(str(params.get("measurement_height", 2)))
            self.ed_move_z.setText(str(params.get("movement_height", 0)))
            self.stabilization_time.setText(str(params.get("stabilization_time", 500)))
            self.movement_feed.setText(str(params.get("movement_feed", 30)))
            
            # Tensiometer config
            tensio = data.get("tensiometer", {})
            baudrate = tensio.get("baudrate", "2400")
            idx = self.baudrate_combo.findText(baudrate)
            if idx >= 0:
                self.baudrate_combo.setCurrentIndex(idx)
            
            # Atualiza estado
            self._current_routine_path = filepath
            name = data.get("name", filepath.stem)
            self.setWindowTitle(f"Tensão do Stencil - {name}")
            
            self.status_label.setText(f"✅ Rotina '{name}' carregada")
            log.info(f"Rotina carregada: {filepath}")
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao carregar rotina: {e}")
    
    def _on_routine_double_clicked(self, item, column):
        """Carrega rotina ao dar duplo-clique"""
        filepath = Path(item.data(0, Qt.ItemDataRole.UserRole))
        self._load_routine(filepath)
    
    def _on_routine_context_menu(self, position):
        """Menu de contexto para rotinas (botão direito)"""
        item = self.routines_tree.itemAt(position)
        if not item:
            return
        
        menu = QMenu(self)
        
        action_load = menu.addAction("▶ Carregar")
        action_load.triggered.connect(self._load_selected_routine)
        
        action_run = menu.addAction("▶▶ Carregar e Executar")
        action_run.triggered.connect(self._load_and_run_routine)
        
        menu.addSeparator()
        
        action_rename = menu.addAction("✏ Renomear")
        action_rename.triggered.connect(self._rename_selected_routine)
        
        action_delete = menu.addAction("🗑 Excluir")
        action_delete.triggered.connect(self._delete_selected_routine)
        
        menu.exec(self.routines_tree.viewport().mapToGlobal(position))
    
    def _delete_selected_routine(self):
        """Exclui a rotina selecionada"""
        item = self.routines_tree.currentItem()
        if not item:
            QMessageBox.warning(self, "Aviso", "Selecione uma rotina para excluir.")
            return
        
        name = item.text(0)
        filepath = Path(item.data(0, Qt.ItemDataRole.UserRole))
        
        result = QMessageBox.question(
            self, "Confirmar Exclusão",
            f"Deseja realmente excluir a rotina '{name}'?\n\nEsta ação não pode ser desfeita.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if result == QMessageBox.StandardButton.Yes:
            try:
                filepath.unlink()
                self._refresh_routines()
                
                # Se era a rotina atual, limpa o título
                if self._current_routine_path == filepath:
                    self._current_routine_path = None
                    self.setWindowTitle("Tensão do Stencil")
                
                self.status_label.setText(f"🗑 Rotina '{name}' excluída")
                
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Falha ao excluir rotina: {e}")
    
    def _rename_selected_routine(self):
        """Renomeia a rotina selecionada"""
        item = self.routines_tree.currentItem()
        if not item:
            return
        
        old_name = item.text(0)
        filepath = Path(item.data(0, Qt.ItemDataRole.UserRole))
        
        new_name, ok = QInputDialog.getText(
            self, "Renomear Rotina",
            "Novo nome:",
            text=old_name
        )
        
        if not ok or not new_name.strip() or new_name == old_name:
            return
        
        safe_name = "".join(c for c in new_name if c.isalnum() or c in "._- ").strip()
        new_filepath = ROUTINES_FOLDER / f"{safe_name}.json"
        
        if new_filepath.exists():
            QMessageBox.warning(self, "Erro", f"Já existe uma rotina com o nome '{safe_name}'.")
            return
        
        try:
            # Atualiza o nome dentro do JSON também
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            data["name"] = safe_name
            
            with open(new_filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            
            filepath.unlink()  # Remove o arquivo antigo
            
            self._refresh_routines()
            self.status_label.setText(f"✏ Rotina renomeada: {old_name} → {safe_name}")
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao renomear rotina: {e}")
    
    def _load_and_run_routine(self):
        """Carrega a rotina selecionada e inicia execução automaticamente"""
        item = self.routines_tree.currentItem()
        if not item:
            QMessageBox.warning(self, "Aviso", "Selecione uma rotina para executar.")
            return
        
        filepath = Path(item.data(0, Qt.ItemDataRole.UserRole))
        self._load_routine(filepath)
        
        # Aguarda um pouco e inicia a medição
        QTimer.singleShot(500, self._on_start)
