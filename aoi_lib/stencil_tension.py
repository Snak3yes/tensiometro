"""
Módulo: stencil_tension.py
Descrição: mede a tensão do stencil em um grid NxN e salva em JSON.
"""

import json
import serial
import serial.tools.list_ports
import numpy as np
import logging
from tkinter import Toplevel, Label, Entry, Button, messagebox
from PyQt6.QtWidgets import (
    QDialog, QGridLayout, QLabel, QLineEdit, QPushButton, QMessageBox,
    QComboBox, QGroupBox, QFrame, QHBoxLayout, QProgressBar
)
from PyQt6.QtCore import QThread, pyqtSignal
import time, logging         

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
    
    def __init__(self, cnc_controller, tensiometer, points, z_down, 
                 user_feed, stabilization_time, parameters):
        super().__init__()
        self.cnc = cnc_controller
        self.tensiometer = tensiometer
        self.points = points
        self.z_down = z_down
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
            
            # Move para altura segura
            self._move_abs(z=0, feed=self.user_feed)
            
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
                
                # 1) Move XY
                self._move_abs(x=x, y=y, feed=self.user_feed)
                
                # 2) Desce Z
                self._move_rel(z=self.z_down, feed=self.user_feed)
                
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
                
                # 6) Sobe Z
                self._move_rel(z=-self.z_down, feed=self.user_feed)
                
                # 7) Pequena pausa entre pontos
                time.sleep(0.1)
            
            # Emite resultado final
            log.info("Medição de tensão concluída com sucesso")
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
        self.cnc = cntrl_cnc
        # Inicializa gerenciador do tensiômetro
        self.tensiometer = TensiometerSerialManager()
        self.measurement_thread = None
        self._build_ui()
        # Popula lista de portas disponíveis
        self._refresh_ports()

    # --------------------------- UI ---------------------------------
    def _build_ui(self):
        lay = QGridLayout(self)
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
        self.movement_feed = QLineEdit("1000")
        self.movement_feed.setToolTip("Velocidade para todas as movimentações durante a medição")
        adv_layout.addWidget(self.movement_feed, 1, 1)
        
        adv_group.setLayout(adv_layout)
        lay.addWidget(adv_group, r, 0, 1, 5); r += 1

        lay.addWidget(QLabel("<b>Ponto Inicial</b>"), r, 0, 1, 5);  r += 1

        lay.addWidget(QLabel("X:"), r, 0)
        self.ed_sx = QLineEdit(); lay.addWidget(self.ed_sx, r, 1)
        lay.addWidget(QLabel("Y:"), r, 2)
        self.ed_sy = QLineEdit(); lay.addWidget(self.ed_sy, r, 3)
        btn_cap_start = QPushButton("Capturar"); lay.addWidget(btn_cap_start, r, 4); r += 1

        lay.addWidget(QLabel("<b>Ponto Final</b>"), r, 0, 1, 5);    r += 1

        lay.addWidget(QLabel("X:"), r, 0)
        self.ed_ex = QLineEdit(); lay.addWidget(self.ed_ex, r, 1)
        lay.addWidget(QLabel("Y:"), r, 2)
        self.ed_ey = QLineEdit(); lay.addWidget(self.ed_ey, r, 3)
        btn_cap_end = QPushButton("Capturar"); lay.addWidget(btn_cap_end, r, 4); r += 1

        lay.addWidget(QLabel("Quantidade (N):"), r, 0)
        self.ed_n = QLineEdit("3"); lay.addWidget(self.ed_n, r, 1)
        lay.addWidget(QLabel("Altura Z (mm):"), r, 2)
        self.ed_z = QLineEdit("2"); lay.addWidget(self.ed_z, r, 3)
        btn_cap_z = QPushButton("Capturar"); lay.addWidget(btn_cap_z, r, 4); r += 1

        # Botões de controle da medição
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

        try:
            z_down = float(self.ed_z.text()) * -1   # negativo para descer
        except ValueError:
            QMessageBox.warning(self, "Erro", "Altura Z inválida.")
            return
        # Verifica se tensiômetro está conectado
        if not self.tensiometer.is_connected:
            QMessageBox.warning(self, "Erro", "Conecte o tensiômetro antes de iniciar")
            return

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
            "height":   float(self.ed_z.text())
        }
        
        # Configura interface para medição
        self._setup_measurement_ui(len(pts))
        
        # Cria e inicia thread de medição
        self.measurement_thread = TensionMeasurementThread(
            self.cnc, self.tensiometer, pts, z_down, 
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
        
        # Salva resultados
        try:
            parameters = {
                "start": {"x": float(self.ed_sx.text()), "y": float(self.ed_sy.text())},
                "end":   {"x": float(self.ed_ex.text()), "y": float(self.ed_ey.text())},
                "quantity": int(self.ed_n.text()),
                "height":   float(self.ed_z.text())
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
            self.accept()
            
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

        