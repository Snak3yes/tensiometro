import sys
import time
import json
import cv2
from pathlib import Path
from plate_flow import PlateFlowManager
from virtual_home_dialog import ConfigHomeDialog
from axis_calibration_dialog import AxisCalibrationDialog
from settings_manager import SettingsManager
from camera_manager   import CameraManager
from alignment_dialog import AlignmentDialog
# widgets externos importados
from table_program_tab           import TableProgramTab
from axes_control_tab            import AxesControlTab
from movement_controls_widget    import MovementControlsWidget
from position_status_widget      import PositionStatusWidget
from inspection_positions_widget import InspectionPositionsWidget
from program_io_widget           import ProgramIOWidget
from positions_backend           import InspectionPositionsBackend
from sequence_control import (
    SequenceControlWidget, InspectionPosition, MotionBackend
)

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QSpinBox, QPushButton, 
                            QGroupBox, QGridLayout, QTabWidget, QTextEdit,
                            QFrame, QSizePolicy, QCheckBox, QScrollArea,
                            QMessageBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QThread
from PyQt6.QtGui import QFont
from pymodbus.client import ModbusTcpClient

class MultiAxisMotorController(QMainWindow):
    # -----------------------------------------------------------------
    #  S I G N A L   (garante acesso aos widgets só no thread GUI)
    # -----------------------------------------------------------------
    logRequested = pyqtSignal(str)        # emitido por qualquer thread
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
            # EIXO Y1 
            'M500_Y1': 500,   # ATRIBUI ZERO A POSIÇÃO ATUAL (Y1)
            'M550_Y1': 550,   # INICIA O MOVIMENTO ABSOLUTO (Y1)
            'M600_Y1': 600,   # ACIONA LÓGICA DE COMPARAÇÃO (Y1)
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
            'M850': 850,      # GO TO HOME Y1
            'M1350': 1350,    # GO TO HOME X
            'M1850': 1850,    # GO TO HOME Z

            # HOMING REALIZADO - Status do homing
            'M300': 300,      # HOMING REALIZADO Y2
            'M800': 800,      # HOMING REALIZADO Y1
            'M1300': 1300,    # HOMING REALIZADO X
            'M1800': 1800,    # HOMING REALIZADO Z

            # SISTEMA JOG TODOS OS EIXOS (conforme nova estrutura)
            # Y2
            'M70_Y2': 70,     # JOG POSITIVO Y2
            'M80_Y2': 80,     # JOG NEGATIVO Y2
            'M10_Y2': 10,     # INTERROMPE JOG LIMITE POSITIVO Y2
            'M11_Y2': 11,     # INTERROMPE JOG LIMITE NEGATIVO Y2
            # Y1
            'M570_Y1': 570,   # JOG POSITIVO Y1
            'M580_Y1': 580,   # JOG NEGATIVO Y1
            'M510_Y1': 510,   # INTERROMPE JOG LIMITE POSITIVO Y1
            'M511_Y1': 511,   # INTERROMPE JOG LIMITE NEGATIVO Y1
            # X
            'M1070_X': 1070,  # JOG POSITIVO X
            'M1080_X': 1080,  # JOG NEGATIVO X
            'M1010_X': 1010,  # INTERROMPE JOG LIMITE POSITIVO X
            'M1011_X': 1011,  # INTERROMPE JOG LIMITE NEGATIVO X
            # Z
            'M1570_Z': 1570,  # JOG POSITIVO Z
            'M1580_Z': 1580,  # JOG NEGATIVO Z
            'M1510_Z': 1510,  # INTERROMPE JOG LIMITE POSITIVO Z
            'M1511_Z': 1511,  # INTERROMPE JOG LIMITE NEGATIVO Z

            # botões / sinal de conclusão do fluxo de placa
            'M20': 20,   # botão Mesa 1
            'M21': 21,   # done Mesa 1
            'M30': 30,   # botão Mesa 2
            'M31': 31,   # done Mesa 2

            # MEMÓRIAS AUXILIARES HOMING (conforme ladder real)
            # Y2
            'M311': 311, 'M312': 312, 'M313': 313, 'M314': 314, 'M315': 315,
            'M360': 360,
            # Y1  
            'M811': 811, 'M812': 812, 'M813': 813, 'M814': 814, 'M815': 815,
            'M860': 860,
            # X
            'M1311': 1311, 'M1312': 1312, 'M1313': 1313, 'M1314': 1314, 'M1315': 1315,
            'M1360': 1360,
            # Z
            'M1811': 1811, 'M1812': 1812, 'M1813': 1813, 'M1814': 1814, 'M1815': 1815,
            'M1860': 1860,
            
            # TEMPORIZADORES HOMING
            'T0': 0, 'T1': 1, 'T2': 2, 'T3': 3, 'T4': 4, 'T5': 5, 'T6': 6, 'T7': 7,
            
            # VELOCIDADES JOG (nova estrutura D22000 série)
            'D22000': 22000,  # VELOCIDADE JOG POSITIVO Y2
            'D22010': 22010,  # VELOCIDADE JOG POSITIVO Y1
            'D22020': 22020,  # VELOCIDADE JOG POSITIVO X
            'D22030': 22030,  # VELOCIDADE JOG POSITIVO Z
            'D22050': 22050,  # VELOCIDADE JOG NEGATIVO Y2
            'D22060': 22060,  # VELOCIDADE JOG NEGATIVO Y1
            'D22070': 22070,  # VELOCIDADE JOG NEGATIVO X
            'D22080': 22080,  # VELOCIDADE JOG NEGATIVO Z
            'D22100': 22100,  # TEMPO DE ACELERAÇÃO JOG
            'D22110': 22110,  # TEMPO DE DESACELERAÇÃO JOG

            # LIMITES SALVOS EM ROM (novos conforme planilha)
            'D23050': 23050,  # LIMITE NEGATIVO Y2 (ROM)
            'D23060': 23060,  # LIMITE NEGATIVO Y1 (ROM)
            'D23070': 23070,  # LIMITE NEGATIVO X (ROM)
            'D23080': 23080,  # LIMITE NEGATIVO Z (ROM)
            'D23090': 23090,  # LIMITE POSITIVO Y2 (ROM)
            'D23100': 23100,  # LIMITE POSITIVO Y1 (ROM)
            'D23110': 23110,  # LIMITE POSITIVO X (ROM)
            'D23120': 23120,  # LIMITE POSITIVO Z (ROM)
            
            # VELOCIDADES HOMING (conforme planilha)
            'D23000': 23000,  # VELOCIDADE HOMING Y2 (ROM)
            'D23010': 23010,  # VELOCIDADE HOMING Y1 (ROM)
            'D23020': 23020,  # VELOCIDADE HOMING X (ROM)
            'D23030': 23030,  # VELOCIDADE HOMING Z (ROM)
            'D450': 450,      # VELOCIDADE HOMING Y2 (aplicada)
            'D950': 950,      # VELOCIDADE HOMING Y1 (aplicada)
            'D1450': 1450,    # VELOCIDADE HOMING X (aplicada)
            'D1950': 1950,    # VELOCIDADE HOMING Z (aplicada)
            
            # Registradores D - Corrigidos conforme ladder real
            # EIXO Y2
            'D0_Y2': 0,         # MOVE TO ABS (Y2)
            'D50_Y2': 50,       # LIMITE NEGATIVO Y2 (trabalho)
            'D23050_Y2': 23050, # LIMITE NEGATIVO Y2 (ROM)
            'D100_Y2': 100,     # POSIÇÃO ABSOLUTA DEFINIDA PELO USUÁRIO (Y2) - ENTRADA
            'D150_Y2': 150,     # POSIÇÃO ABSOLUTA DEFINIDA (Y2)
            'D20000_Y2': 20000, # VELOCIDADE DE DESLOCAMENTO (Y2)
            # EIXO Y1 - NOVO
            'D500_Y1': 500,     # MOVE TO ABS (Y1)
            'D550_Y1': 550,     # LIMITE NEGATIVO Y1 (trabalho)
            'D23060_Y1': 23060, # LIMITE NEGATIVO Y1 (ROM)
            'D600_Y1': 600,     # POSIÇÃO ABSOLUTA DEFINIDA PELO USUÁRIO (Y1) - ENTRADA
            'D650_Y1': 650,     # POSIÇÃO ABSOLUTA DEFINIDA (Y1)
            'D20500_Y1': 20500, # VELOCIDADE DE DESLOCAMENTO (Y1)
            # EIXO Z
            'D1500_Z': 1500,    # MOVE TO ABS (Z)
            'D1550_Z': 1550,    # LIMITE NEGATIVO Z (trabalho)
            'D23080_Z': 23080,  # LIMITE NEGATIVO Z (ROM)
            'D1600_Z': 1600,    # POSIÇÃO ABSOLUTA DEFINIDA PELO USUÁRIO (Z) - ENTRADA
            'D1650_Z': 1650,    # POSIÇÃO ABSOLUTA DEFINIDA (Z)
            'D21500_Z': 21500,  # VELOCIDADE DE DESLOCAMENTO (Z)
            # EIXO X
            'D1000_X': 1000,    # MOVE TO ABS (X)
            'D1050_X': 1050,    # LIMITE NEGATIVO X (trabalho) 
            'D23070_X': 23070,  # LIMITE NEGATIVO X (ROM)
            'D1100_X': 1100,    # POSIÇÃO ABSOLUTA DEFINIDA PELO USUÁRIO (X) - ENTRADA
            'D1150_X': 1150,    # POSIÇÃO ABSOLUTA DEFINIDA (X)
            'D21000_X': 21000,  # VELOCIDADE DE DESLOCAMENTO (X)

            # ---------------- DOT CONTROL --------------------------
            # D-registradores para frequência e quantidade de aplicação
            # (mudaram de D4000 / D4100 → D24000 / D24100 no ladder)
            'D24000_FREQ': 24000,   # Frequência (Hz) dos dots
            'D24100_QTY':  24100,   # Quantidade de dots

            # Registradores de status (leitura)
            'D3100_Y2': 3100,   # POSIÇÃO ATUAL MOTOR Y2 (cópia do SR460)
            'D3400_Y1': 3400,   # POSIÇÃO ATUAL MOTOR Y1 (cópia do SR500)
            'D3200_Z': 3200,    # POSIÇÃO ATUAL MOTOR Z (cópia do SR480)
            'D3000_X': 3000,    # POSIÇÃO ATUAL MOTOR X (cópia do SR520)

            # Saídas Y (coils) – endereços Modbus oficiais (AS-Series Manual, Tabela 7-3)
            'Y00': 40960, 'Y01': 40961,     # Y0.0 / Y0.1  eixo-Y2
            'Y02': 40962, 'Y03': 40963,     # Y0.2 / Y0.3  eixo-Z
            'Y04': 40964, 'Y05': 40965,     # Y0.4 / Y0.5  eixo-Y1
            'Y06': 40966, 'Y07': 40967,     # Y0.6 / Y0.7  eixo-X
            'Y010': 40970,                 # Y0.10 (0xA00A) aplicadora de adesivo  <<< FIX

            # Entradas X (sensores)
            'X04_Y2': 8196,     # X0.4 sensor homing Y2  
            'X06_Y1': 8198,     # X0.6 sensor homing Y1
            'X08_X': 8200,      # X0.8 sensor homing X
            'X09_Z': 8201,      # X0.9 sensor homing Z
        }
        # Posição atual dos eixos
        self.current_positions = {
            'Y2': 0,
            'Y1': 0,
            'Z': 0, 
            'X': 0
        }

        # ---------------- CONTEXTO DO PROJETO -----------------
        self.prog_mgr            = None   # AdhesiveProgramManager ou None
        self.current_proj_name   = None   # string ou None

        # ------------------------------------------------------------------
        #  SPINBOX “FANTASMA” PARA CADA EIXO (necessário para o backend PLC)
        # ------------------------------------------------------------------
        from PyQt6.QtWidgets import QSpinBox
        for _axis in ('Y2', 'Y1', 'X', 'Z'):
            if not hasattr(self, f'pulsos_spin_{_axis}'):
                sb = QSpinBox()
                sb.setRange(-2_147_483_648, 2_147_483_647)
                sb.setValue(0)
                setattr(self, f'pulsos_spin_{_axis}', sb)

        # ------------------- NOVO: lista de registradores configuráveis -------------------
        # (qualquer outro pode ser acrescentado facilmente depois)
        self.configurable_registers = [
            # ---- LIMITES SALVOS EM ROM ----
            ('D23050', 'Limite-   Y2 (ROM)'), ('D23090', 'Limite+ Y2 (ROM)'),
            ('D23060', 'Limite-   Y1 (ROM)'), ('D23100', 'Limite+ Y1 (ROM)'),
            ('D23070', 'Limite-   X  (ROM)'), ('D23110', 'Limite+ X  (ROM)'),
            ('D23080', 'Limite-   Z  (ROM)'), ('D23120', 'Limite+ Z  (ROM)'),
            # ---- VELOCIDADE DE DESLOCAMENTO ----
            ('D20000_Y2', 'Vel. Desloc. Y2'),
            ('D20500_Y1', 'Vel. Desloc. Y1'),
            ('D21000_X',  'Vel. Desloc. X'),
            ('D21500_Z',  'Vel. Desloc. Z'),
            # ---- VELOCIDADE DE HOMING (ROM) ----
            ('D23000', 'Vel. Homing Y2'),
            ('D23010', 'Vel. Homing Y1'),
            ('D23020', 'Vel. Homing X'),
            ('D23030', 'Vel. Homing Z'),
            # ---- VELOCIDADE JOG ----
            ('D22000', 'Jog+ Y2'), ('D22050', 'Jog- Y2'),
            ('D22010', 'Jog+ Y1'), ('D22060', 'Jog- Y1'),
            ('D22020', 'Jog+ X'),  ('D22070', 'Jog- X'),
            ('D22030', 'Jog+ Z'),  ('D22080', 'Jog- Z'),
            ('D22100', 'Tempo Acel. Jog'),
            ('D22110', 'Tempo Desac. Jog'),
            # ---------- DOT --------------------------------------
            ('D24000_FREQ', 'Frequência dot  (Hz)'),
            ('D24100_QTY',  'Quantidade dot')
        ]

        # -------------- limites de trabalho (padrão) + persistência ---
        # --------------- carrega configurações persistentes -----------
        self.settings = SettingsManager()
        self.table_limits = self.settings.table_limits

        # -------------------------------------------------------------
        #  OFFSET CÂMERA ↔ NOZZLE deve existir ANTES do backend PLC
        # -------------------------------------------------------------
        self.camera_nozzle_offset = self.settings.cam_noz_offset

        # ------------------------------------------------------------
        #  Diretório-base dos projetos (…\Projetos\modelos\…)
        # ------------------------------------------------------------
        self.projects_dir = self.settings.projects_dir
        self.projects_dir.mkdir(parents=True, exist_ok=True)

        # --------------- câmera ------------------------------
        self.camera_manager = CameraManager(self.settings.camera_index)

        # aplica calibração se existir
        a,b = self.settings.focus_coeffs
        self.camera_manager.load_calibration(a,b)

        # backend de movimento criado uma única vez e reutilizado
        self._plc_motion_backend = PLCMotionBackend(self)
        # ---------------- STEPS/MM  -----------------------------
        self.steps_per_mm: dict[str,float] = self.settings.axis_steps
        # -------- escala da câmera (mm/pixel) -------------------
        self.mm_per_pixel: float = self.settings.camera_mm_per_pixel

        # -------- campo-de-visão (dois pontos) -------------------
        self.camera_fov: dict = self.settings.camera_fov
        # coeficientes lineares  largura = aX*z + bX   (idem altura)
        self._fov_coeffs = self._calc_fov_coeffs()

        # ---- homing virtual ---------------------------------
        self.virtual_home: dict[int,dict[str,int]] = self.settings.virtual_home

        self.init_ui()
        # Ao iniciar, criação/edição de programa fica BLOQUEADA
        QTimer.singleShot(0, lambda: self._set_creation_controls_enabled(False))
        self.connect_plc()

        # Lê velocidades salvas na ROM após conectar
        QTimer.singleShot(1500, self.read_initial_jog_velocities)
        QTimer.singleShot(2500, self.read_initial_limits)
        QTimer.singleShot(3000, self.read_current_positions)
        QTimer.singleShot(3500, self.read_initial_homing_status)

        # Controle de teclas do teclado
        self.keyboard_jog_active = {
            'X': False,
            'Y2': False,
            'Y1': False,
            'Z': False
        }  # Flags para controlar se JOG está ativo via teclado para cada eixo
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)  # Permite capturar teclas
        
        # Timer para atualização
        # ---------------------- logger seguro -------------------------
        self.logRequested.connect(self._append_log)    # slot GUI

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(500)
        
    # ===============  LOG thread-safe  =================================
    def log(self, msg: str):
        """
        Pode ser chamado de QUALQUER thread.
        No thread GUI a mensagem é escrita imediatamente;
        nos demais threads emite-se logRequested.
        """
        ts = time.strftime("%H:%M:%S")
        full = f"[{ts}] {msg}"
        print(full, flush=True)
        if QThread.currentThread() is self.thread():      # GUI?
            self._append_log(full)
        else:
            self.logRequested.emit(full)

    def _append_log(self, text: str):
        """Slot executado SEMPRE no thread GUI"""
        if not hasattr(self, "log_text"):
            return
        self.log_text.append(text)
        # mantém no máx. 100 linhas
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

        # ----------------------- MENU --------------------------------
        menubar = self.menuBar()
        # ------------ MENU “ARQUIVO” ---------------------------------
        menu_file  = menubar.addMenu("Arquivo")
        act_new    = menu_file.addAction("Novo Projeto")
        act_open   = menu_file.addAction("Abrir Projeto…")
        act_save   = menu_file.addAction("Salvar Projeto")
        act_saveas = menu_file.addAction("Salvar Como…")
        menu_file.addSeparator()
        act_exit   = menu_file.addAction("Sair")

        act_new.triggered.connect(self._new_project)
        act_open.triggered.connect(self._open_project)
        act_save.triggered.connect(self._save_project)
        act_saveas.triggered.connect(self._save_as_project)
        act_exit.triggered.connect(self.close)
        menu_cfg   = menubar.addMenu("Configurações")

        # =====================  NOVO  ▸  PREFERÊNCIAS  ===============
        menu_pref  = menubar.addMenu("Preferências")
        act_setdir = menu_pref.addAction("Definir caminho Modelos…")
        act_setdir.triggered.connect(self._set_models_path)
        menu_prog  = menubar.addMenu("Programa")
        act_limits = menu_cfg.addAction("Limites de mesa…")
        act_limits.triggered.connect(self._open_limits_dialog)

        # ---- submenu câmera ---------------------------------
        menu_cam = menu_cfg.addMenu("Câmera")
        act_select = menu_cam.addAction("Selecionar câmera…")
        act_reopen = menu_cam.addAction("Reconectar")
        act_focus  = menu_cam.addAction("Calibrar foco…")
        act_fov    = menu_cam.addAction("Calibração campo de visão…")
        act_select.triggered.connect(self._select_camera_dialog)
        act_reopen.triggered.connect(lambda: self.camera_manager.open(self.settings.camera_index))
        act_focus.triggered.connect(self._open_focus_dialog)
        act_fov.triggered.connect(self._open_fov_dialog)

        # ---------------- CALIBRAÇÃO EIXOS ----------------------
        act_calib  = menu_cfg.addAction("Calibração dos Eixos…")
        act_calib.triggered.connect(self._open_axis_calib_dialog)

        # ---------------- HOMING VIRTUAL ---------------------
        act_homecfg = menu_cfg.addAction("Homing Virtual…")
        act_homecfg.triggered.connect(self._open_virtual_home_dialog)

        # ------------- NOVO  –  ALINHAMENTO NOZZLE/CÂMERA ---------
        act_align = menu_cfg.addAction("Alinhamento Nozzle↔Câmera…")
        act_align.triggered.connect(self._open_alignment_dialog)

        # ------------------ DOT PATTERNS ---------------------------
        act_dots = menu_prog.addAction("Padrões de Dots…")
        act_dots.triggered.connect(self._open_dot_dialog)

        # ------------- NOVO  –  CONVERSOR DE MESA --------------------
        act_conv = menu_prog.addAction("Converter programa da outra mesa…")
        act_conv.triggered.connect(self._open_converter_dialog)

        # --------------------- BANNER DE CONEXÃO (rodapé) -------------
        # Usa o status-bar nativo do QMainWindow (aparece no rodapé).
        self.status_bar = self.statusBar()          # QStatusBar
        self.status_bar.setSizeGripEnabled(False)   # oculta “grip” de redimensionar
        self.status_bar.showMessage("Desconectado")
        self.status_bar.setStyleSheet(
            "QStatusBar { background-color:red; color:white; font-weight:bold; }")
        
        # Abas para organizar
        # ----------------------------------------------------------------
        #  TAB WIDGET principal fica em self.tab_widget para acesso global
        # ----------------------------------------------------------------
        self.tab_widget = QTabWidget()
                
        # === ABA 1: CONTROLE DOS EIXOS (principal) ===
        self.control_tab = AxesControlTab(self, primary=True)
        self.tab_widget.addTab(self.control_tab, "Controle de Eixos")
        
        # === ABA 2: STATUS ===
        status_tab = QWidget()
        status_layout = QVBoxLayout(status_tab)
        
        # Status das saídas
        outputs_group = self.create_outputs_status()
        status_layout.addWidget(outputs_group)
        
        # Status das memórias
        memories_group = self.create_memories_status()
        status_layout.addWidget(memories_group)

        # Sensores de HOMING (entradas X0.4 / X0.6 / X0.8 / X0.9)
        sensors_group = self.create_homing_sensors_status()
        status_layout.addWidget(sensors_group)
        
        # Status dos registradores
        registers_group = self.create_registers_status()
        status_layout.addWidget(registers_group)
        
        self.tab_widget.addTab(status_tab, "Status do Sistema")
        
        # === ABA 3: CONFIGURAÇÃO DE REGISTRADORES (NOVA) ===
        config_tab = self.create_config_tab()
        self.tab_widget.addTab(config_tab, "Config. Registradores")

        # === ABA 4: LOG ===
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
        
        self.tab_widget.addTab(log_tab, "Log")

        # === ABA 5: MESA 1 ============================================
        self.mesa_tabs = {}
        mesa1_tab = TableProgramTab(self, mesa_id=1)
        self.mesa_tabs[1] = mesa1_tab
        self.tab_widget.addTab(mesa1_tab, "Mesa 1")

        # === ABA 6: MESA 2 ============================================
        mesa2_tab = TableProgramTab(self, mesa_id=2)
        self.mesa_tabs[2] = mesa2_tab
        self.tab_widget.addTab(mesa2_tab, "Mesa 2")
        
        layout.addWidget(self.tab_widget)

        # --- gerentes de fluxo de placa --------------------------------
        
        self.flow_mesa1 = PlateFlowManager(self, 1, self.mesa_tabs[1])
        self.flow_mesa2 = PlateFlowManager(self, 2, self.mesa_tabs[2])
        # flag de execução geral
        self._global_cycle_active = False

        # ------- rastreia arquivo atual do projeto -------------------
        self._current_project_file = None
        # --------------- registra todos os ProgramIOWidgets ------------
        self._register_prog_widget(self.prog_io_widget)          # controle de eixos
        self._register_prog_widget(mesa1_tab.prog_widget)
        self._register_prog_widget(mesa2_tab.prog_widget)

    # ================================================================
    #  CONVERSOR MESA1 ⇆ MESA2
    # ================================================================
    def _open_converter_dialog(self):
        """Abre (ou traz à frente) a janela de conversão de programa."""
        w = self.tab_widget.currentWidget()
        if w not in self.mesa_tabs.values():
            QMessageBox.warning(self, "Converter",
                                "Selecione primeiro a aba Mesa 1 ou Mesa 2.")
            return
        if not hasattr(self, "_conv_dialog"):
            from program_converter_dialog import ProgramConverterDialog
            self._conv_dialog = ProgramConverterDialog(self, w)
        else:
            # actualiza referência da aba actual
            self._conv_dialog.mesa_tab = w
            self._conv_dialog.setWindowTitle(
                f"Conversor de Programa – Mesa {w.mesa}")
        self._conv_dialog.show()
        self._conv_dialog.raise_()
        self._conv_dialog.activateWindow()

    # -----------------------------------------------------------------
    # Helpers para ProgramIOWidget por aba
    # -----------------------------------------------------------------
    def _register_prog_widget(self, widget):
        """Acopla sinais de load/save para lembrar o último arquivo usado."""
        widget._last_file = None
        widget.fileSaved.connect(lambda f, w=widget: setattr(w, "_last_file", f))
        # ─── NOVO ───
        # sempre que um programa for CARREGADO por este widget
        # (botão “Carregar Programa” nas abas), ajusta estado global
        widget.fileLoaded.connect(
            lambda f, w=widget: self._on_program_loaded(f, w))
        # mantém lista para futura atualização do default_dir
        if not hasattr(self, "_prog_widgets"):
            self._prog_widgets = []
        self._prog_widgets.append(widget)

    # ================================================================
    #  handler único para qualquer ProgramIOWidget.fileLoaded
    # ================================================================
    def _on_program_loaded(self, filepath: str, widget):
        """
        • cria (ou re-usa) AdhesiveProgramManager para a pasta do arquivo;
        • grava current_proj_name;
        • habilita imediatamente todos os botões de criação/edição.
        """
        try:
            from adhesive_program_manager import AdhesiveProgramManager
            path = Path(filepath).resolve()
            prog_name = path.stem
            self.prog_mgr = AdhesiveProgramManager(path.parent)
            try:
                # tenta criar; se já existir apenas re-usa
                self.prog_mgr.create_program(prog_name, overwrite=False)
            except FileExistsError:
                # programa já existe → apenas aponta o diretório
                self.prog_mgr.model_dir = (
                    self.prog_mgr.base_dir / "modelos" / prog_name)
            self.current_proj_name = prog_name

            # memoriza no widget para futuros “Salvar”
            widget._last_file = str(path)

            # libera botões de criação/edição
            self._set_creation_controls_enabled(True)

            self.log(f"■ Projeto “{prog_name}” carregado: {path.name}")
        except Exception as exc:
            self.log(f"■ Erro ao processar programa carregado: {exc}")

    # ================================================================
    #       ALINHAMENTO NOZZLE  ↔  CÂMERA   (offset X,Y)
    # ================================================================
    def _open_alignment_dialog(self):
        
        dlg = AlignmentDialog(self, self)          # não modal
        dlg.offsetSaved.connect(self._save_nozzle_offset)
        dlg.show()

    def _save_nozzle_offset(self, off: dict[str, int]):
        """Salvo em memória e disco."""
        self.camera_nozzle_offset = off
        self.settings.cam_noz_offset = off
        self.settings.save()
        self.log(f"■ Offset câmera↔nozzle salvo: ΔX={off['x']}  ΔY={off['y']}")

        # informa backend caso já exista
        if hasattr(self, "_plc_motion_backend"):
            self._plc_motion_backend._off_x = off.get("x", 0)
            self._plc_motion_backend._off_y = off.get("y", 0)

    def _current_prog_widget(self):
        """Devolve o ProgramIOWidget associado à aba visível."""
        w = self.tab_widget.currentWidget()
        if w is self.control_tab:
            return self.prog_io_widget
        for mesa_id, tab in self.mesa_tabs.items():
            if w is tab:
                return tab.prog_widget
        # fallback
        return self.prog_io_widget
    
    # ================================================================
    #  Conversões pulsos  ←→  milímetros
    # ================================================================
    def pulses_from_mm(self, axis: str, mm: float) -> int:
        """Converte mm → pulsos utilizando a calibração do eixo."""
        return int(round(mm * self.steps_per_mm.get(axis, 1.0)))
    
    # ---------- NOVO: pixels → pulsos  -------------------------------
    def pulses_from_pixels(self, dx_pix: float, dy_pix: float, z_pos: int,
                           y_axis: str = "Y1") -> tuple[int,int]:
        """
        Converte deslocamento em pixels (no frame da câmera) em pulsos
        dos eixos X e Y dados o z_pos (pulsos Z).
        """
        # calcula mm/pixel a partir dos coef. do FOV
        c = self._calc_fov_coeffs()
        w_mm = c["aX"]*z_pos + c["bX"]
        h_mm = c["aY"]*z_pos + c["bY"]
        mmpp_x = w_mm / self.camera_manager._cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        mmpp_y = h_mm / self.camera_manager._cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        dx_mm = dx_pix * mmpp_x
        dy_mm = dy_pix * mmpp_y
        dx_p = self.pulses_from_mm("X",  dx_mm)
        dy_p = self.pulses_from_mm(y_axis, dy_mm)
        return dx_p, dy_p

    def _set_axis_steps(self, axis: str, steps: float):
        """Atualiza fator steps/mm de um eixo e persiste em settings."""
        self.steps_per_mm[axis] = float(steps)
        self.settings.axis_steps = self.steps_per_mm
        self.settings.save()
        self.log(f"■ Calibração {axis}: {steps:.3f} steps/mm salva")

    # ================================================================
    #  HOMING VIRTUAL
    # ================================================================
    def _open_virtual_home_dialog(self):
        # cria uma única instância reutilizável
        if not hasattr(self, '_vh_dialog'):
            from virtual_home_dialog import ConfigHomeDialog
            self._vh_dialog = ConfigHomeDialog(self, self)
            self._vh_dialog.acceptedAndSaved.connect(self._save_virtual_home)
        # mostra janela não modal, mantendo-a na frente
        self._vh_dialog.show()
        self._vh_dialog.raise_()
        self._vh_dialog.activateWindow()

    # ------------------ DOTS --------------------------------------
    def _open_dot_dialog(self):
        if not hasattr(self, "_dot_dialog"):
            from dot_patterns_dialog import DotPatternsDialog
            self._dot_dialog = DotPatternsDialog(self)
        self._dot_dialog.show()
        self._dot_dialog.raise_(); self._dot_dialog.activateWindow()

    def _save_virtual_home(self):
        self.virtual_home = self._vh_dialog.get_home_dict()
        self.settings.virtual_home = self.virtual_home
        self.settings.save()
        self.log("■ Homing virtual atualizado")

    def goto_virtual_home(self, mesa: int):
        """Usado pelas abas Mesa 1/Mesa 2."""
        home = self.virtual_home.get(mesa, {"x":0,"y":0})
        x_tgt = home["x"]
        y_tgt = home["y"]
        # calcula diferenças
        dx = x_tgt - self.current_positions["X"]
        y_axis = 'Y1' if mesa == 1 else 'Y2'
        dy = y_tgt - self.current_positions[y_axis]
        if abs(dx) > 0:
            self.move_relative('X', dx)
        if abs(dy) > 0:
            self.move_relative(y_axis, dy)
        self.log(f"■ Mesa {mesa}: cabeça movida para Home virtual")
            
    # =================================================================
    #  AÇÕES DO MENU “ARQUIVO”
    # =================================================================
    def _new_project(self):
        """
        Inicia um NOVO programa.
        Passos:
          1. usuário já está na aba Mesa 1 ou Mesa 2;
          2. pergunta nome do programa;
          3. cria imediatamente  modelos/<nome>/…  (estrutura base);
          4. limpa listas e libera botões de criação.
        """
        from PyQt6.QtWidgets import QInputDialog
        mesa_tab = self.tab_widget.currentWidget()
        if mesa_tab not in self.mesa_tabs.values():
            QMessageBox.warning(self, "Novo projeto",
                                "Antes de criar um projeto, selecione a aba Mesa 1 ou Mesa 2.")
            return

        proj_name, ok = QInputDialog.getText(
            self, "Novo Projeto",
            "Nome do novo programa:",
            text=""
        )
        if not ok or not proj_name.strip():
            return                          # cancelado
        proj_name = proj_name.strip()

        # Cria a pasta-raiz imediatamente
        try:
            from adhesive_program_manager import AdhesiveProgramManager
            # garante …/<Projetos>/  existente
            self.projects_dir.mkdir(parents=True, exist_ok=True)
            self.prog_mgr = AdhesiveProgramManager(self.projects_dir)
            # overwrite=True  ➜ recria estrutura completa sempre
            self.proj_root = self.prog_mgr.create_program(proj_name, overwrite=True)
            self.current_proj_name = proj_name
            self.log(f"■■ Estrutura base criada: {self.proj_root}")
        except FileExistsError:
            QMessageBox.warning(self, "Projeto existente",
                                f"O programa “{proj_name}” já existe.")
            return
        except Exception as exc:
            self.log(f"■ Erro ao criar estrutura do projeto: {exc}")
            QMessageBox.critical(self, "Erro", str(exc))
            return

        # Limpa listas das abas
        for tab in self.mesa_tabs.values():
            tab.inspect_widget.clear()

        # Libera botões de criação / ação
        self._set_creation_controls_enabled(True)
        self._current_project_file = None
        self.log(f"■■ Novo projeto “{proj_name}” iniciado")

    # =================================================================
    #  DEFINIR DIRETÓRIO BASE  (Preferências ▸ Definir caminho Modelos)
    # =================================================================
    def _set_models_path(self):
        from PyQt6.QtWidgets import QFileDialog
        sel = QFileDialog.getExistingDirectory(
            self, "Escolha a pasta onde será criado “Projetos”")
        if not sel:
            return
        base = Path(sel).resolve()
        projetos_path = base / "Projetos"
        try:
            projetos_path.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            QMessageBox.critical(self, "Erro",
                                 f"Não foi possível criar “Projetos”:\n{exc}")
            return
        # persiste
        self.projects_dir = projetos_path
        self.settings.projects_dir = projetos_path
        self.settings.save()
        # actualiza diretório-padrão nos ProgramIOWidgets já existentes
        for w in getattr(self, "_prog_widgets", []):
            if hasattr(w, "_default_dir"):
                w._default_dir = str(projetos_path)
        self.log(f"■ Diretório de projetos definido para: {projetos_path}")
        QMessageBox.information(self, "Preferências",
                                f"Caminho configurado:\n{projetos_path}")

    # --- salvar / abrir utilizando ProgramIOWidget já existente ------
    def _save_project(self):
        """Salva arquivo referente à aba ativa."""
        if not self.current_proj_name or not self.projects_dir:
            QMessageBox.warning(self, "Salvar",
                                "Nenhum projeto em edição ou pasta padrão indefinida.")
            return
        widget = self._current_prog_widget()
        # sufixo .m1 / .m2 conforme backend
        suffix = getattr(widget, "_default_suf", ".json")
        mesa_id = 1 if suffix.endswith("1") else 2
        dest = self.projects_dir / f"{self.current_proj_name}{suffix}"
        try:
            ok = widget._backend.save_to_file(str(dest))
            if ok:
                widget._last_file = str(dest)
                self.log(f"Projeto salvo em {dest}")
                QMessageBox.information(self, "Salvar",
                                        f"Projeto salvo com sucesso em:\n{dest}")
            else:
                QMessageBox.critical(self, "Erro", "Falha ao salvar o projeto.")
        except Exception as exc:
            QMessageBox.critical(self, "Erro", str(exc))

    def _save_as_project(self):
        """Abre diálogo de ‘Salvar Como…’ reaproveitando ProgramIOWidget."""
        widget = self._current_prog_widget()
        widget._on_save_clicked()

    def _open_project(self):
        """Abre projeto (diálogo de arquivo) via ProgramIOWidget oculto."""
        widget = self._current_prog_widget()
        old_enabled = widget.isEnabled()
        widget._on_load_clicked()
        # se carregou com sucesso (_last_file setado), habilita botões
        if getattr(widget, "_last_file", None):
            # garante ponteiro do gerente de programa
            try:
                from adhesive_program_manager import AdhesiveProgramManager
                proj_path = Path(widget._last_file).resolve()
                proj_name = proj_path.stem
                self.prog_mgr = AdhesiveProgramManager(proj_path.parent)
                try:
                    self.prog_mgr.create_program(proj_name, overwrite=False)
                except FileExistsError:
                    # estrutura já criada anteriormente → ok
                    self.prog_mgr.model_dir = (
                        self.prog_mgr.base_dir / "modelos" / proj_name)
                self.current_proj_name = proj_name
            except Exception:
                QMessageBox.critical(self, "Erro",
                                     "Não foi possível abrir o programa selecionado.")
                pass
            self._set_creation_controls_enabled(True)

    # -----------------------------------------------------------------
    #  Habilita / desabilita botões de criação (ActionSelector + Add)
    # -----------------------------------------------------------------
    def _set_creation_controls_enabled(self, enabled: bool):
        """
        Ativa ou bloqueia os botões que só devem ser usados quando um
        projeto está em edição (novo ou aberto).
        """
        for mesa_tab in self.mesa_tabs.values():
            # selector de ação
            mesa_tab.action_selector.setEnabled(enabled)
            # botão “Adicionar posição atual”
            mesa_tab.inspect_widget.btn_add.setEnabled(enabled)
        # movimento / salvar posição da aba principal
        if hasattr(self, 'inspect_widget'):
            self.inspect_widget.btn_add.setEnabled(enabled)
        

    def _open_focus_dialog(self):
        from focus_calibration_dialog import FocusCalibrationDialog
        dlg = FocusCalibrationDialog(self, self)
        if dlg.exec():
            # pega coeficientes
            z0,f0,z1,f1 = dlg._z_top, dlg._f_top, dlg._z_bot, dlg._f_bot
            a = (f1 - f0) / (z1 - z0)
            b = f0 - a*z0
            self.camera_manager.load_calibration(a,b)
            self.settings.focus_coeffs = (a,b)
            self.settings.save()
            self.log("Calibração de foco salva")
            # agora que existe calibração, liga auto-focus
            self.camera_manager.enable_auto_focus(True)

    # -------------- diálogo FOV ------------------------------------
    def _open_fov_dialog(self):
        from fov_calibration_dialog import FOVCalibrationDialog
        dlg = FOVCalibrationDialog(self.settings, self)
        if dlg.exec():
            # recarrega as constantes na instância
            self.camera_fov = self.settings.camera_fov
            self._fov_coeffs = self._calc_fov_coeffs()
            self.log("Calibração de campo-de-visão salva")

    # ----------------------------------------------------------------
    #  Calcula coeficientes lineares  campo_mm(z)=a*z+b
    # ----------------------------------------------------------------
    def _calc_fov_coeffs(self) -> dict[str,float]:
        f = self.camera_fov
        z0 = float(f.get("z0_z_pulses", 0))
        z1 = float(f.get("z1_z_pulses", 700))
        w0 = float(f.get("z0_width_mm", 61.0))
        w1 = float(f.get("z1_width_mm", 30.5))
        h0 = float(f.get("z0_height_mm", 45.0))
        h1 = float(f.get("z1_height_mm", 22.5))
        if z1 == z0:           # garante denom.
            z1 += 1
        aX = (w1 - w0) / (z1 - z0)
        bX = w0 - aX * z0
        aY = (h1 - h0) / (z1 - z0)
        bY = h0 - aY * z0
        return {"aX":aX, "bX":bX, "aY":aY, "bY":bY}

    # -------------------- diálogo calibração eixos -------------------
    def _open_axis_calib_dialog(self):
        
        dlg = AxisCalibrationDialog(self, self)
        dlg.exec()

    # --------------------- diálogo de limites ------------------------
    def _open_limits_dialog(self):
        from config_dialogs import WorkAreaConfigDialog
        dlg = WorkAreaConfigDialog(self.table_limits, self)
        if dlg.exec():
            self.table_limits = dlg.get_limits()
            # envia às abas
            for mesa, tab in self.mesa_tabs.items():
                tab.set_limits(self.table_limits[mesa])
            self.settings.table_limits = self.table_limits
            self.settings.save()
            self.log("Limites de mesa atualizados pelo usuário")

    # ----------------------- câmera --------------------------
    def _select_camera_dialog(self):
        from PyQt6.QtWidgets import QInputDialog
        idx, ok = QInputDialog.getInt(self, "Selecionar câmera",
                                      "Índice da câmera (0 = padrão):",
                                      value=self.settings.camera_index, min=0, max=10)
        if ok:
            self.settings.camera_index = idx
            self.settings.save()
            self.camera_manager.open(idx)
            self.log(f"Câmera {idx} selecionada")

    # ---------------- persistência em JSON ---------------------------
    def _load_limits_from_disk(self):
        try:
            if self._limits_file.exists():
                data = json.loads(self._limits_file.read_text(encoding="utf-8"))
                # valida estrutura mínima
                if all(str(k) in ("1", "2") for k in data):
                    self.table_limits = {int(k): v for k, v in data.items()}
                    self.log("Limites de mesa carregados do disco")
        except Exception as exc:
            self.log(f"Erro ao ler limites salvos: {exc}")

    def _save_limits_to_disk(self):
        try:
            self._limits_file.write_text(
                json.dumps(self.table_limits, indent=2), encoding="utf-8")
            self.log("Limites de mesa gravados em table_limits.json")
        except Exception as exc:
            self.log(f"Erro ao salvar limites: {exc}")

    def create_homing_sensors_status(self):
        """Exibe o estado ON/OFF dos sensores físicos de HOME"""
        group = QGroupBox("SENSORES DE HOME (Entradas X)")
        layout = QGridLayout()

        sensors = [
            ('X04_Y2', 'Sensor HOME Y2 (X0.4)'),
            ('X06_Y1', 'Sensor HOME Y1 (X0.6)'),
            ('X08_X',  'Sensor HOME X  (X0.8)'),
            ('X09_Z',  'Sensor HOME Z  (X0.9)')
        ]
        for i, (addr_key, desc) in enumerate(sensors):
            layout.addWidget(QLabel(f"{desc}:"), i, 0)
            lbl = QLabel("OFF")
            lbl.setStyleSheet("QLabel { background-color: gray; color: white; padding: 5px; }")
            layout.addWidget(lbl, i, 1)
            setattr(self, f'{addr_key}_status', lbl)

        group.setLayout(layout)
        return group

    def create_config_tab(self):
        """Aba que exibe TODOS os registradores configuráveis em formato editável"""
        tab = QWidget()
        vbox = QVBoxLayout(tab)

        # Scroll para caber em qualquer resolução
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        grid = QGridLayout(scroll_content)

        # Cria um spinBox 32 bits para cada registrador listado em self.configurable_registers
        for row, (reg_key, desc) in enumerate(self.configurable_registers):
            addr = self.addresses.get(reg_key)
            if addr is None:
                continue       # pula se endereço ainda não mapeado

            # Coluna 0 – label descritivo
            grid.addWidget(QLabel(f"{reg_key} ({desc})"), row, 0)

            # Coluna 1 – spinBox (-2 147 483 648 a 2 147 483 647)
            spin = QSpinBox()
            spin.setRange(-2_147_483_648, 2_147_483_647)
            spin.setObjectName(f"cfg_spin_{reg_key}")
            grid.addWidget(spin, row, 1)

            # Coluna 2 – botão “Gravar”
            btn = QPushButton("Gravar")
            btn.clicked.connect(lambda _=False, rk=reg_key: self.write_single_config(rk))
            grid.addWidget(btn, row, 2)

        scroll_content.setLayout(grid)
        scroll.setWidget(scroll_content)
        vbox.addWidget(scroll)

        # Botões globais
        h = QHBoxLayout()
        ler_btn  = QPushButton("Ler Todos")
        gravar_btn = QPushButton("Gravar Todos")
        ler_btn.clicked.connect(self.read_all_config)
        gravar_btn.clicked.connect(self.write_all_config)
        h.addStretch()
        h.addWidget(ler_btn)
        h.addWidget(gravar_btn)
        vbox.addLayout(h)

        # Leitura inicial automática quando a aba é criada
        QTimer.singleShot(200, self.read_all_config)
        return tab

    # ------------------------------------------------------------------ 
    # Funções auxiliares da aba de configuração
    # ------------------------------------------------------------------
    def read_all_config(self):
        """Lê todos os registradores configuráveis e atualiza os spinBoxes"""
        if not self.connected:
            return
        for reg_key, _ in self.configurable_registers:
            addr = self.addresses.get(reg_key)
            if addr is None:
                continue
            try:
                value = self.read_dword(addr)
                spin: QSpinBox = self.findChild(QSpinBox, f"cfg_spin_{reg_key}")
                if spin:
                    spin.blockSignals(True)
                    spin.setValue(value)
                    spin.blockSignals(False)
            except Exception as exc:
                self.log(f"‚ùå Falha ao ler {reg_key}: {exc}")
                continue
        self.log("‚úÖ Configuração – leitura concluída")

    def write_single_config(self, reg_key):
        """Grava somente o registrador indicado"""
        if not self.connected:
            self.log("‚ùå CLP não conectado")
            return
        addr = self.addresses.get(reg_key)
        if addr is None:
            return
        spin: QSpinBox = self.findChild(QSpinBox, f"cfg_spin_{reg_key}")
        if spin is None:
            return
        value = spin.value()
        try:
            res = self.write_dword(addr, value)
            if not res.isError():
                self.log(f"‚úÖ {reg_key} gravado: {value}")
            else:
                self.log(f"‚ùå Falha ao gravar {reg_key}")
        except Exception as e:
            self.log(f"‚ùå Erro ao gravar {reg_key}: {e}")

    def write_all_config(self):
        """Grava TODOS os registradores configuráveis"""
        for reg_key, _ in self.configurable_registers:
            self.write_single_config(reg_key)
        self.log("‚úÖ Configuração – gravação concluída")
                
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
            'Y1': (f'D600_{axis_name}', f'D20500_{axis_name}'),  # Entrada usuário, Velocidade
            'Z':  (f'D1600_{axis_name}', f'D21500_{axis_name}'), # Entrada usuário, Velocidade  
            'X':  (f'D1100_{axis_name}', f'D21000_{axis_name}')  # Entrada usuário, Velocidade
        }
        pulsos_addr, vel_addr = addr_map[axis_name]
        
        # Apenas posição absoluta (velocidade passou para aba de configuração)
        pulsos_label    = f"{pulsos_addr} - Posição Absoluta:"
        pulsos_tooltip  = "Coordenada absoluta de destino"
        default_pulsos  = 0
            
        # Posição absoluta – 32 bits (aceita valores negativos)
        params_layout.addWidget(QLabel(pulsos_label), 0, 0)
        pulsos_spin = QSpinBox()
        pulsos_spin.setRange(-2_000_000_000, 2_000_000_000)
        pulsos_spin.setValue(default_pulsos)
        pulsos_spin.setToolTip(pulsos_tooltip)
        params_layout.addWidget(pulsos_spin, 0, 1)
        setattr(self, f'pulsos_spin_{axis_name}', pulsos_spin)
        
        # Display da posição atual
        sr_addr_map = {'Y2': 'D3100_Y2', 'Y1': 'D3400_Y1', 'Z': 'D3200_Z', 'X': 'D3000_X'}

        params_layout.addWidget(QLabel(f"{sr_addr_map[axis_name]} - Posição Atual:"), 1, 0)
        current_pos_label = QLabel("0")
        current_pos_label.setStyleSheet("QLabel { background-color: lightblue; padding: 2px; font-weight: bold; max-height: 20px; }")
        params_layout.addWidget(current_pos_label, 1, 1)

        setattr(self, f'current_pos_label_{axis_name}', current_pos_label)

        # Indicador LED de HOMING REALIZADO
        params_layout.addWidget(QLabel("Status Homing:"), 2, 0)
        homing_led = QLabel("●")
        homing_led.setStyleSheet("QLabel { background-color: gray; color: gray; padding: 2px; font-size: 16px; font-weight: bold; max-height: 20px; border-radius: 10px; }")
        homing_led.setAlignment(Qt.AlignmentFlag.AlignCenter)
        homing_led.setToolTip("Cinza: Homing não realizado | Verde: Homing realizado")
        params_layout.addWidget(homing_led, 2, 1)
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
        
        # Controles JOG para TODOS OS EIXOS (novo sistema)
        if axis_name in ['Y2', 'Y1', 'X', 'Z']:  # Todos os eixos têm JOG agora
            # Separador visual
            separator = QFrame()
            separator.setFrameStyle(QFrame.Shape.HLine | QFrame.Shadow.Sunken)
            move_layout.addWidget(separator, 1, 0, 1, 2)
            
            # Frame JOG
            jog_frame = QFrame()
            jog_frame.setStyleSheet("QFrame { border: 2px solid #2196F3; border-radius: 5px; background-color: #E3F2FD; }")
            jog_layout = QVBoxLayout(jog_frame)
                                
            # Botões JOG com pressionar/soltar
            jog_buttons_layout = QHBoxLayout()
            
            # Botão JOG Negativo (à esquerda)
            jog_minus_btn = QPushButton(f"🔽 JOG {axis_name}-")
            jog_minus_btn.setStyleSheet("""
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
            jog_minus_btn.pressed.connect(lambda: self.jog_start(axis_name, '-'))
            jog_minus_btn.released.connect(lambda: self.jog_stop(axis_name))
            jog_buttons_layout.addWidget(jog_minus_btn)
            setattr(self, f'jog_minus_btn_{axis_name}', jog_minus_btn)
            
            # Botão JOG Positivo (à direita)
            jog_plus_btn = QPushButton(f"🔼 JOG {axis_name}+")
            jog_plus_btn.setStyleSheet("""
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
            jog_plus_btn.pressed.connect(lambda: self.jog_start(axis_name, '+'))
            jog_plus_btn.released.connect(lambda: self.jog_stop(axis_name))
            jog_buttons_layout.addWidget(jog_plus_btn)
            setattr(self, f'jog_plus_btn_{axis_name}', jog_plus_btn)
            
            jog_layout.addLayout(jog_buttons_layout)
                    
        move_layout.addWidget(jog_frame, 2, 0, 1, 2)
        
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
        
        group.setLayout(layout)
        return group

    # ===================================================================
    #               SEQUÊNCIA DE HOMING GERAL  (Z → (Y2,Y1,X))
    # ===================================================================

    def home_all_axes(self):
        """
        1) Aciona homing do eixo Z (M1850) e aguarda 3 s.
        2) Depois aciona simultaneamente os homings de Y2 (M350), Y1 (M850) e X (M1350).
        Todos os coils são soltos 200 ms após o disparo (pulso momentâneo).
        """
        if not self.connected:
            self.log(" CLP não conectado")
            return

        # Etapa 1 – homing apenas do Z
        self.log(" HOMING GERAL: acionando homing do eixo Z (M1850)…")
        self._pulse_coil('M1850')

        # Agenda etapa 2 para daqui a 3 s
        QTimer.singleShot(3000, self._home_remaining_axes)

    def _home_remaining_axes(self):
        """Dispara homing de Y2, Y1 e X em paralelo e solta todos os coils."""
        try:
            self.log(" Acionando homing simultâneo de Y2, Y1 e X…")
            for mem in ['M350', 'M850', 'M1350']:
                self._pulse_coil(mem)

        except Exception as e:
            self.log(f" Erro na etapa 2 do homing geral: {e}")

    # ---------------------------------------------------------
    # Helper interno – envia pulso de 20 ms em uma memória M
    # ---------------------------------------------------------
    def _pulse_coil(self, mem_key):
        """Liga o coil por 20 ms e depois desliga (edge-trigger)."""
        try:
            addr = self.addresses[mem_key]
            self.client.write_coil(addr, True)
            QTimer.singleShot(100, lambda a=addr: self.client.write_coil(a, False))
            self.log(f" Pulso {mem_key} enviado")
        except Exception as e:
            self.log(f" Falha ao pulsar {mem_key}: {e}")
                
    def create_outputs_status(self):
        """Cria status das saídas"""
        group = QGroupBox("STATUS DAS SAÍDAS")
        layout = QGridLayout()
        
        outputs = [
            ('Y0.0',  'Pulso Eixo 1'),
            ('Y0.1',  'Dir Eixo 1'),
            ('Y0.2',  'Pulso Eixo 2'), 
            ('Y0.3',  'Dir Eixo 2'),
            ('Y0.4',  'Pulso Eixo 3'),
            ('Y0.5',  'Dir Eixo 3'),
            ('Y0.6',  'Pulso Eixo 4'),
            ('Y0.7',  'Dir Eixo 4'),
            ('Y0.10', 'Y0.10 (SHOT)')
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
        
        memories = ['M0_Y2', 'M50_Y2', 'M100_Y2', 'M500_Y1', 'M550_Y1', 'M600_Y1',
                    'M1500_Z', 'M1550_Z', 'M1600_Z', 'M1000_X', 'M1050_X', 'M1100_X', 
                    'M5000', 'M5001', 
                    'M350', 'M850', 'M1350', 'M1850',
                    'M300', 'M800', 'M1300', 'M1800',
                    'M70_Y2', 'M570_Y1', 'M1070_X', 'M1570_Z']

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
            'D500_Y1', 'D600_Y1', 'D20500_Y1',    # Y1 (entrada usuário)
            'D1500_Z', 'D1600_Z', 'D21500_Z',     # Z (entrada usuário)
            'D1000_X', 'D1100_X', 'D21000_X',     # X (entrada usuário)
            'D3100_Y2', 'D3400_Y1', 'D3200_Z', 'D3000_X',  # Posições atuais - CORRIGIDO
            'D22000', 'D22010', 'D22020', 'D22030',         # Velocidades JOG
            'D23000', 'D23010', 'D23020', 'D23030',         # Velocidades Homing ROM
            'D23050', 'D23060', 'D23070', 'D23080',         # Limites Negativos ROM
            'D23090', 'D23100', 'D23110', 'D23120'          # Limites Positivos ROM
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
                self.status_bar.showMessage("■ CONECTADO: 192.168.1.5:502")
                self.status_bar.setStyleSheet(
                    "QStatusBar { background-color:green; color:white; font-weight:bold; }")
                self.log("✅ Conectado com sucesso!")
                self.log("🔧 Endereços corrigidos conforme ladder real")
            else:
                self.connected = False
                self.status_bar.showMessage("Desconectado")
                self.status_bar.setStyleSheet(
                    "QStatusBar { background-color:red; color:white; font-weight:bold; }")
                self.log("■ Falha na conexão")
                
        except Exception as e:
            self.connected = False
            self.status_bar.showMessage("Desconectado")
            self.status_bar.setStyleSheet(
                "QStatusBar { background-color:red; color:white; font-weight:bold; }")
            self.log(f"■ Erro na conexão: {e}")    
    
    def read_initial_jog_velocities(self):
        """Lê velocidades JOG atuais dos registradores D22000 série"""
        if not self.connected:
            return
            
        try:
            self.log("📖 Lendo velocidades JOG atuais...")
            
            # Mapeamento dos registradores JOG
            jog_velocity_map = {
                'Y2': ('D22000', 'jog_velocity_spin_Y2'),
                'Y1': ('D22010', 'jog_velocity_spin_Y1'),
                'X':  ('D22020', 'jog_velocity_spin_X'),
                'Z':  ('D22030', 'jog_velocity_spin_Z')
            }
            
            for axis, (reg_key, spin_attr) in jog_velocity_map.items():
                try:
                    jog_velocity = self.read_dword(self.addresses[reg_key])
            
            # Atualiza interface se spinbox existir
                    if hasattr(self, spin_attr):
                        jog_spin = getattr(self, spin_attr)
                        jog_spin.setValue(abs(jog_velocity))
                        self.log(f"✅ Velocidade JOG {axis}: {abs(jog_velocity)} Hz")
                
                except Exception as e:
                    self.log(f"⚠️ Erro ao ler velocidade JOG {axis}: {e}")
                    continue
        except Exception as e:
            self.log(f"❌ Erro geral na leitura das velocidades JOG: {e}")    
            
    def read_initial_limits(self):
        """Lê limites salvos na ROM"""
        if not self.connected:
            return
            
        try:
            self.log("📖 Lendo limites da ROM...")
            
            limits_map = {
                'Y2': ('D23050', 'D23090'),  # Negativo, Positivo
                'Y1': ('D23060', 'D23100'),  # Negativo, Positivo
                'X':  ('D23070', 'D23110'),  # Negativo, Positivo
                'Z':  ('D23080', 'D23120')   # Negativo, Positivo
            }
            
            for axis, (neg_reg, pos_reg) in limits_map.items():
                try:
                    neg_limit = self.read_dword(self.addresses[neg_reg])
                    pos_limit = self.read_dword(self.addresses[pos_reg])
                    self.log(f"📊 Limites {axis}: {neg_limit} a {pos_limit}")
                
                except Exception as e:
                    self.log(f"⚠️ Erro ao ler limites {axis}: {e}")
                    continue
                    
        except Exception as e:
            self.log(f"❌ Erro geral na leitura dos limites: {e}")    

    def read_initial_homing_status(self):
        """Lê status inicial das memórias de homing na inicialização"""
        if not self.connected:
            return
            
        try:
            self.log("📖 Lendo status inicial das memórias de homing...")
            
            homing_memories = {
                'M300': 'Y2',
                'M800': 'Y1', 
                'M1300': 'X',
                'M1800': 'Z'
            }
            
            for mem_name, axis in homing_memories.items():
                try:
                    addr = self.addresses[mem_name]
                    result = self.client.read_coils(addr, count=1)
                    
                    if not result.isError():
                        state = result.bits[0]
                        
                        # Atualiza LED diretamente
                        homing_led = getattr(self, f'homing_led_{axis}', None)
                        if homing_led:
                            self.update_homing_led(homing_led, state)
                            
                        # Log do status inicial
                        status_text = "REALIZADO" if state else "NÃO REALIZADO"
                        self.log(f"🏠 Status inicial Homing {axis}: {status_text}")
                        
                        # Inicializa variável de controle de mudança
                        setattr(self, f'_last_homing_status_M{mem_name[1:]}', state)

                        # FORÇA atualização do LED imediatamente
                        homing_led = getattr(self, f'homing_led_{axis}', None)
                        if homing_led:
                            self.update_homing_led(homing_led, state)
                        
                except Exception as e:
                    self.log(f"⚠️ Erro ao ler status inicial {mem_name}: {e}")
                    continue
                    
            self.log("📖 Leitura inicial de homing concluída")
            
        except Exception as e:
            self.log(f"❌ Erro geral na leitura inicial de homing: {e}")

    # ================================================================
    #  SISTEMA DE CACHE PARA PRESERVAR JANELAS DE COMPARAÇÃO
    # ================================================================
    
    def _save_current_comparison_windows(self, parent_item):
        """
        Salva o estado atual das janelas de comparação no cache
        associado à posição mecânica especificada
        """
        if parent_item is None or not self.roi_editor:
            return
            
        try:
            # Coleta todas as janelas atualmente no visor ROI
            current_windows = []
            for item in self.roi_editor.windows:
                if hasattr(item, 'comparison_name'):
                    # Salva dados essenciais da janela
                    window_data = {
                        'name': item.comparison_name,
                        'rect': {
                            'x': item.rect().x(),
                            'y': item.rect().y(), 
                            'width': item.rect().width(),
                            'height': item.rect().height()
                        },
                        'scene_pos': {
                            'x': item.scenePos().x(),
                            'y': item.scenePos().y()
                        },
                        'tooltip': item.toolTip()
                    }
                    current_windows.append(window_data)
            
            # Salva no cache
            self._comparison_windows_cache[parent_item] = current_windows
            
            if current_windows:
                self.log(f"💾 {len(current_windows)} janelas de comparação salvas no cache para posição mecânica")
                
        except Exception as e:
            self.log(f"⚠️ Erro ao salvar janelas no cache: {e}")
    
    def _load_comparison_windows_from_cache(self, parent_item):
        """
        Carrega as janelas de comparação do cache para a posição mecânica especificada
        """
        if parent_item is None or not self.roi_editor:
            return
            
        try:
            # Verifica se há janelas salvas para esta posição
            cached_windows = self._comparison_windows_cache.get(parent_item, [])
            
            if not cached_windows:
                return
                
            # Limpa janelas atuais do ROI editor (sem emitir sinais)
            self._clear_roi_editor_silently()
            
            # Recria cada janela salva
            for window_data in cached_windows:
                try:
                    # Cria nova janela com os mesmos parâmetros
                    rect_data = window_data['rect']
                    new_item = self.roi_editor.add_window(
                        x=rect_data['x'],
                        y=rect_data['y'],
                        w=rect_data['width'],
                        h=rect_data['height'],
                        deletable=True
                    )
                    
                    # Restaura propriedades
                    new_item.comparison_name = window_data['name']
                    new_item.setToolTip(window_data.get('tooltip', ''))
                    
                    # Adiciona à TreeView
                    self._add_comparison_window_to_tree(parent_item, new_item)
                    
                except Exception as e:
                    self.log(f"⚠️ Erro ao restaurar janela {window_data.get('name', '?')}: {e}")
                    continue
            
            self.log(f"📂 {len(cached_windows)} janelas de comparação restauradas do cache")
            
        except Exception as e:
            self.log(f"⚠️ Erro ao carregar janelas do cache: {e}")
    
    def _clear_roi_editor_silently(self):
        """Remove todas as janelas do ROI editor sem emitir sinais"""
        if not self.roi_editor:
            return
            
        try:
            # Remove itens da cena silenciosamente
            for item in self.roi_editor.windows[:]:  # cópia para evitar modificação durante iteração
                try:
                    if item.scene():
                        self.roi_editor.view.scene().removeItem(item)
                    self.roi_editor.windows.remove(item)
                except (RuntimeError, ValueError):
                    # Item já foi removido ou não existe mais
                    if item in self.roi_editor.windows:
                        self.roi_editor.windows.remove(item)
                    
        except Exception as e:
            self.log(f"⚠️ Erro ao limpar ROI editor: {e}")
    
    def _clear_cache_for_position(self, parent_item):
        """Remove do cache todas as janelas associadas a uma posição mecânica"""
        if parent_item in self._comparison_windows_cache:
            del self._comparison_windows_cache[parent_item]
            self.log(f"🗑️ Cache de janelas limpo para posição mecânica removida")

    def read_current_positions(self):
        """Lê posições atuais dos motores (função dedicada)"""
        if not self.connected:
            return
            
        try:
            position_registers = {
                'D3100_Y2': 'Y2',
                'D3400_Y1': 'Y1', 
                'D3200_Z': 'Z',
                'D3000_X': 'X'
            }
            
            for reg_name, axis in position_registers.items():
                try:
                    addr = self.addresses[reg_name]
                    value = self.read_dword(addr)
                    
                    # Atualiza posição e interface
                    self.current_positions[axis] = value
                    label = getattr(self, f'current_pos_label_{axis}', None)
                    if label:
                        label.setText(str(value))
                        
                except Exception as e:
                    self.log(f"⚠️ Erro ao ler posição {axis} ({reg_name}): {e}")                        
                    continue
                    
        except Exception as e:
            # Falha silenciosa para não afetar outras operações
            self.log(f"⚠️ Erro ao ler posições: {e}")
    
    def monitor_homing_status(self):
        """Função dedicada APENAS para monitorar status de homing em tempo real"""
        if not self.connected:
            return
            
        try:
            homing_memories = {
                'M300': 'Y2',
                'M800': 'Y1', 
                'M1300': 'X',
                'M1800': 'Z'
            }
            
            for mem_name, axis in homing_memories.items():
                try:
                    addr = self.addresses[mem_name]
                    result = self.client.read_coils(addr, count=1)
                    
                    if not result.isError():
                        state = result.bits[0]
                        
                        # Atualiza LED SEMPRE (sem verificação de mudança)
                        homing_led = getattr(self, f'homing_led_{axis}', None)
                        if homing_led:
                            current_led_state = "lime" in homing_led.styleSheet()
                            
                            # Só atualiza se estado for diferente do LED atual
                            if (state and not current_led_state) or (not state and current_led_state):
                                self.update_homing_led(homing_led, state)
                                self.log(f"🔄 LED Homing {axis} atualizado: {'VERDE' if state else 'CINZA'}")
                        
                except Exception as e:
                    self.log(f"⚠️ Erro ao ler status de homing {axis}: {e}")
                    continue
                    
        except Exception as e:
            self.log(f"⚠️ Erro ao monitorar status de homing: {e}")
            pass
    
    def test_homing_status(self):
        """Função de teste específica para verificar status das memórias de homing"""
        if not self.connected:
            return
            
        self.log("🔧 Testando status das memórias de homing...")
        
        homing_memories = {
            'M300': 'Y2',
            'M800': 'Y1', 
            'M1300': 'X',
            'M1800': 'Z'
        }
        
        for mem_name, axis in homing_memories.items():
            try:
                addr = self.addresses[mem_name]
                result = self.client.read_coils(addr, count=1)

                if not result.isError():
                    state = result.bits[0]
                    status_text = "REALIZADO" if state else "NÃO REALIZADO"
                    self.log(f"🏠 Homing {axis} ({mem_name}): {status_text}")

                    # Força atualização do LED
                    homing_led = getattr(self, f'homing_led_{axis}', None)
                    if homing_led:
                        self.update_homing_led(homing_led, state)
                        self.log(f"💡 LED {axis} forçado para: {'VERDE' if state else 'CINZA'}")
                else:
                    self.log(f"❌ Erro ao ler {mem_name}: {result}")

                # Força uma atualização completa dos LEDs após o teste
                QTimer.singleShot(100, self.force_homing_leds_update)

                # Também força verificação dedicada
                QTimer.singleShot(200, self.force_homing_status_check)

            except Exception as e:
                self.log(f"❌ Erro ao testar {mem_name}: {e}")

    def force_homing_leds_update(self):
        """Força atualização imediata de todos os LEDs de homing"""
        try:
            # Reset das variáveis de controle para forçar atualização
            for axis in ['Y2', 'Y1', 'X', 'Z']:
                if hasattr(self, f'_last_led_status_{axis}'):
                    delattr(self, f'_last_led_status_{axis}')
                if hasattr(self, f'_last_homing_status_M{axis}'):
                    delattr(self, f'_last_homing_status_M{axis}')

            self.log("🔄 Forçando atualização completa dos LEDs...")

            # Força leitura imediata
            QTimer.singleShot(50, self.monitor_homing_status)
            
        except Exception as e:
            self.log(f"❌ Erro ao forçar atualização: {e}")
        
    def force_update_homing_leds(self):
        """Força atualização de todos os LEDs de homing"""
        self.log("🔄 Forçando atualização dos LEDs de homing...")
        self.test_homing_status()
            
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

    # ---------------------------------------------------
    def write_axis_parameters(self, axis_name):
        """Escreve parâmetros de um eixo"""
        if not self.connected:
            self.log("❌ CLP não conectado")
            return
            
        try:
            # Obtém valores da interface
            p_spin       = getattr(self, f'pulsos_spin_{axis_name}')
            pulsos_value = p_spin.value()
            
            # Mapeamento de endereços
            addr_map = {
                'Y2': (f'D100_{axis_name}', f'D20000_{axis_name}'),
                'Y1': (f'D600_{axis_name}', f'D20500_{axis_name}'),
                'Z':  (f'D1600_{axis_name}', f'D21500_{axis_name}'),
                'X':  (f'D1100_{axis_name}', f'D21000_{axis_name}')
            }
            p_addr_key, v_addr_key = addr_map[axis_name]
            pulsos_addr = self.addresses[p_addr_key]
            vel_addr = self.addresses[v_addr_key]
                
            self.log(f"📝 Escrevendo parâmetros Eixo {axis_name}: Posição={pulsos_value}")
            
            # -----------------------------------------------------------
            # 1) POSIÇÃO ABSOLUTA  (sempre grava)
            # -----------------------------------------------------------
            if self.write_dword(pulsos_addr, pulsos_value).isError():
                self.log(f"■ Erro ao escrever posição {axis_name}")
                return

            # -----------------------------------------------------------
            # 2) VELOCIDADE         (novo) – pega do spinBox da aba
            #    Config. Registradores ou usa default 20000 Hz
            # -----------------------------------------------------------
            try:
                vel_spin = self.findChild(QSpinBox, f"cfg_spin_{v_addr_key}")
                vel_value = vel_spin.value() if vel_spin else 20000
            except Exception:
                vel_value = 20000

            if self.write_dword(vel_addr, vel_value).isError():
                self.log(f"■ Erro ao escrever velocidade {axis_name}")
                return

            # LOG
            self.log(f"■ Eixo {axis_name}: pos={pulsos_value}  vel={vel_value}")

            # Verifica se posição ficou realmente gravada
            self.verify_write(pulsos_addr, pulsos_value, p_addr_key)
            
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
                'Y1': f'M550_{axis_name}',  # INICIA MOVIMENTO ABSOLUTO
                'Z':  f'M1550_{axis_name}', # INICIA MOVIMENTO ABSOLUTO
                'X':  f'M1050_{axis_name}'  # INICIA MOVIMENTO ABSOLUTO
            }
            cmd_addr = self.addresses[cmd_map[axis_name]]
                
            target_position = getattr(self, f'pulsos_spin_{axis_name}').value()
            self.log(f"🚀 Movendo eixo {axis_name} para posição {target_position}")
            
            # envia pulso de 100 ms no coil → garante borda de subida
            self._pulse_coil(cmd_map[axis_name])
            self.log(f"🚀 Pulso {cmd_map[axis_name]} enviado – alvo {target_position}")

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
                'Y1': 'M850',    # GO TO HOME Y1
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

    # SISTEMA JOG TODOS OS EIXOS
    
    def set_jog_velocity(self, axis_name):
        """Define velocidade do JOG para qualquer eixo"""
        if not self.connected:
            self.log("❌ CLP não conectado")
            return
            
        try:
            # Obtém velocidade: se spinbox existir usa-o; caso contrário
            # lê o valor já programado no CLP (mantém UI enxuta).
            if hasattr(self, f'jog_velocity_spin_{axis_name}'):
                velocity = getattr(self, f'jog_velocity_spin_{axis_name}').value()
            else:
                pos_addr_key = {
                    'Y2':'D22000','Y1':'D22010','X':'D22020','Z':'D22030'
                }[axis_name]
                velocity = abs(self.read_dword(self.addresses[pos_addr_key]))
            
            # Mapeamento dos registradores JOG por eixo
            jog_addr_map = {
                'Y2': ('D22000', 'D22050'),  # Positivo, Negativo
                'Y1': ('D22010', 'D22060'),  # Positivo, Negativo
                'X':  ('D22020', 'D22070'),  # Positivo, Negativo
                'Z':  ('D22030', 'D22080')   # Positivo, Negativo
            }
            
            pos_addr_key, neg_addr_key = jog_addr_map[axis_name]

            # Verifica se mudou antes de escrever
            current_velocity = self.read_dword(self.addresses[pos_addr_key])
            if current_velocity == velocity:
                self.log(f"ℹ️ Velocidade JOG {axis_name} já está em {velocity} Hz - não alterada")
                return
            
            # Escreve velocidades positiva e negativa
            result1 = self.write_dword(self.addresses[pos_addr_key], velocity)     # Positiva
            result2 = self.write_dword(self.addresses[neg_addr_key], -velocity)   # Negativa
             
            # Escreve tempos de aceleração/desaceleração (comuns para todos os eixos)
            result3 = self.write_dword(self.addresses['D22100'], 1)  # Tempo aceleração
            result4 = self.write_dword(self.addresses['D22110'], 1)  # Tempo desaceleração
            
            if not result1.isError() and not result2.isError() and not result3.isError() and not result4.isError():
                self.log(f"✅ Velocidade JOG {axis_name} definida: ±{velocity} Hz")
                # Verifica se foi escrito corretamente
                QTimer.singleShot(200, lambda: self.verify_jog_velocity(axis_name, velocity))
            else:
                self.log(f"❌ Erro ao definir velocidade JOG {axis_name}")
                
        except Exception as e:
            self.log(f"❌ Erro ao configurar velocidade JOG {axis_name}: {e}")

    def verify_jog_velocity(self, axis_name, expected_velocity):
        """Verifica se a velocidade JOG foi escrita corretamente"""
        try:
            jog_addr_map = {
                'Y2': ('D22000', 'D22050'),
                'Y1': ('D22010', 'D22060'),
                'X':  ('D22020', 'D22070'),
                'Z':  ('D22030', 'D22080')
            }
            pos_addr_key, neg_addr_key = jog_addr_map[axis_name]
            actual_positive = self.read_dword(self.addresses[pos_addr_key])
            actual_negative = self.read_dword(self.addresses[neg_addr_key])
            
            if actual_positive == expected_velocity and actual_negative == -expected_velocity:
                self.log(f"✓ Velocidade JOG {axis_name} verificada: {pos_addr_key}={actual_positive}, {neg_addr_key}={actual_negative}")
            else:
                self.log(f"⚠️ Velocidade JOG {axis_name} divergente: Esperado ±{expected_velocity}, Lido {actual_positive}/{actual_negative}")
                
        except Exception as e:
            self.log(f"❌ Erro verificação velocidade JOG {axis_name}: {e}")
            
    def jog_start(self, axis_name, direction):
        """Inicia movimento JOG contínuo para qualquer eixo"""
        if not self.connected:
            self.log("❌ CLP não conectado")
            return
            
        try:            
            # Configura velocidade automaticamente
            self.set_jog_velocity(axis_name)
            
            # Mapeamento de comandos JOG por eixo (conforme ladder real)
            jog_cmd_map = {
                'Y2': ('M70_Y2', 'M80_Y2'),    # JOG+, JOG-
                'Y1': ('M570_Y1', 'M580_Y1'),  # JOG+, JOG-
                'X':  ('M1070_X', 'M1080_X'),  # JOG+, JOG-
                'Z':  ('M1570_Z', 'M1580_Z')   # JOG+, JOG-
            }
            
            pos_cmd, neg_cmd = jog_cmd_map[axis_name]
                        
            if direction == '+':
                result = self.client.write_coil(self.addresses[pos_cmd], True)
                direction_text = f"POSITIVO ({pos_cmd})"
                self.log(f"🔼 Acionando {pos_cmd} para JOG {axis_name}+")
            else:
                result = self.client.write_coil(self.addresses[neg_cmd], True)
                direction_text = f"NEGATIVO ({neg_cmd})"
                self.log(f"🔽 Acionando {neg_cmd} para JOG {axis_name}-")
                
            if not result.isError():
                self.log(f"🎮 JOG {axis_name} {direction_text} INICIADO")
                self.update_jog_status(axis_name, f"ATIVO - {direction_text}", "lime")
                # Verifica segurança apenas para informar o usuário (não bloqueia)
                self.check_jog_safety(axis_name)
            else:
                self.log(f"❌ Erro ao iniciar JOG {axis_name} {direction_text}")
                
        except Exception as e:
            self.log(f"❌ Erro JOG start {axis_name}: {e}")
            
    def jog_stop(self, axis_name):
        """Para movimento JOG de qualquer eixo"""
        if not self.connected:
            return
            
        try:
            # Mapeamento de comandos JOG por eixo
            jog_cmd_map = {
                'Y2': ('M70_Y2', 'M80_Y2'),
                'Y1': ('M570_Y1', 'M580_Y1'),
                'X':  ('M1070_X', 'M1080_X'),
                'Z':  ('M1570_Z', 'M1580_Z')
            }
            
            pos_cmd, neg_cmd = jog_cmd_map[axis_name]
            
            # Para ambos os comandos JOG do eixo
            result1 = self.client.write_coil(self.addresses[pos_cmd], False)
            result2 = self.client.write_coil(self.addresses[neg_cmd], False)
            
            self.log(f"🛑 Desligando {pos_cmd} e {neg_cmd}")
            
            self.log(f"🛑 JOG {axis_name} PARADO")
            self.update_jog_status(axis_name, "PARADO", "gray")
           
        except Exception as e:
            self.log(f"❌ Erro JOG stop {axis_name}: {e}")
            
    def check_jog_safety(self, axis_name):
        """Monitora status de segurança JOG (apenas informativo - não bloqueia)"""
        try:
            # Mapeamento de flags de segurança por eixo
            safety_map = {
                'Y2': ('M10_Y2', 'M11_Y2'),     # Limite positivo, negativo
                'Y1': ('M510_Y1', 'M511_Y1'),   # Limite positivo, negativo
                'X':  ('M1010_X', 'M1011_X'),   # Limite positivo, negativo
                'Z':  ('M1510_Z', 'M1511_Z')    # Limite positivo, negativo
            }
            
            pos_limit_mem, neg_limit_mem = safety_map[axis_name]
            result1 = self.client.read_coils(self.addresses[pos_limit_mem], count=1)
            result2 = self.client.read_coils(self.addresses[neg_limit_mem], count=1)
            
            if not result1.isError() and not result2.isError():
                positive_ok = not result1.bits[0]  # Invertido: flag ativa = bloqueado
                negative_ok = not result2.bits[0]  # Invertido: flag ativa = bloqueado
                safety_ok = positive_ok or negative_ok  # Pelo menos uma direção liberada

                safety_indicator = getattr(self, f'safety_indicator_{axis_name}', None)
                if not safety_indicator:
                    return safety_ok
                
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
                
                safety_indicator.setText(status_text)
                safety_indicator.setStyleSheet(f"QLabel {{ background-color: {color}; color: white; padding: 3px; font-size: 10px; border-radius: 3px; }}")
                # Log detalhado para debug
                status_key = f'_last_safety_status_{axis_name}'
                current_status = (positive_ok, negative_ok)
                if hasattr(self, status_key) and getattr(self, status_key) != current_status:
                    if not safety_ok:
                        self.log(f"⚠️ {axis_name} fora dos limites - {pos_limit_mem}={not positive_ok}, {neg_limit_mem}={not negative_ok}")
                    else:
                        self.log(f"✅ {axis_name} dentro dos limites - {pos_limit_mem}={not positive_ok}, {neg_limit_mem}={not negative_ok}")
                        
                setattr(self, status_key, current_status)
                
                return safety_ok
            else:
                return False
                
        except Exception as e:
            self.log(f"⚠️ Erro ao verificar segurança JOG {axis_name}: {e}")
            return False
            
    def update_jog_status(self, axis_name, status_text, color):
        """Atualiza status visual do JOG"""
        status_label = getattr(self, f'jog_status_label_{axis_name}', None)
        if status_label:
            status_label.setText(f"Status: {status_text}")
            status_label.setStyleSheet(f"QLabel {{ background-color: {color}; color: white; padding: 5px; font-weight: bold; border-radius: 3px; }}")
    
    # Funções específicas para eixo X (compatibilidade com teclado)
    def jog_start_x(self, direction): self.jog_start('X', direction)
    def jog_stop_x(self): self.jog_stop('X')
    
    # ===================================================================
    #                    CONTROLE VIA TECLADO  
    # ===================================================================
    
    def on_keyboard_jog_toggle(self, state):
        """Callback quando checkbox global de controle via teclado é alterado"""
        enabled = state == Qt.CheckState.Checked.value
        
        if enabled:
            self.log("⌨️ Controle via teclado HABILITADO para todos os eixos")
            self.log("🎮 Teclas: X(← →) | Y2(↑ ↓) | Y1(W S) | Z(Q E)")
            self.keyboard_jog_checkbox.setStyleSheet("QCheckBox { font-weight: bold; color: #4CAF50; }")
        else:
            self.log("⌨️ Controle via teclado DESABILITADO para todos os eixos")
            self.keyboard_jog_checkbox.setStyleSheet("QCheckBox { font-weight: bold; color: #E65100; }")
            # Para qualquer movimento JOG ativo se desabilitar
            for axis in self.keyboard_jog_active:
                if self.keyboard_jog_active[axis]:
                    self.jog_stop(axis)
                    self.keyboard_jog_active[axis] = False
                
    def keyPressEvent(self, event):
        """Captura teclas pressionadas"""
        # Só processa se checkbox estiver habilitado e conectado
        if not hasattr(self, 'keyboard_jog_checkbox') or not self.keyboard_jog_checkbox.isChecked() or not self.connected:
            super().keyPressEvent(event)
            return
            
        key = event.key()
        axis_to_start = None
        direction = None
        
        # Mapeamento de teclas para eixos e direções
        if key == Qt.Key.Key_Left:
            axis_to_start, direction = 'X', '-'
        elif key == Qt.Key.Key_Right:
            axis_to_start, direction = 'X', '+'
        elif key == Qt.Key.Key_Up:
            axis_to_start, direction = 'Y2', '+'
        elif key == Qt.Key.Key_Down:
            axis_to_start, direction = 'Y2', '-'
        elif key == Qt.Key.Key_W:
            axis_to_start, direction = 'Y1', '+'
        elif key == Qt.Key.Key_S:
            axis_to_start, direction = 'Y1', '-'
        elif key == Qt.Key.Key_Q:
            axis_to_start, direction = 'Z', '+'
        elif key == Qt.Key.Key_E:
            axis_to_start, direction = 'Z', '-'
        
        # Inicia JOG se tecla válida e eixo não estiver ativo
        if axis_to_start and not self.keyboard_jog_active[axis_to_start]:
            self.keyboard_jog_active[axis_to_start] = True
            self.jog_start(axis_to_start, direction)
            
            # Mapeamento de símbolos para log
            key_symbols = {
                'X': {'+':"→", '-':"←"},
                'Y2': {'+':"↑", '-':"↓"},
                'Y1': {'+':"W", '-':"S"},
                'Z': {'+':"Q", '-':"E"}
            }
            symbol = key_symbols[axis_to_start][direction]
            self.log(f"⌨️ JOG {axis_to_start}{direction} iniciado via teclado ({symbol})")
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
        axis_to_stop = None
        direction = None
        
        # Mapeamento de teclas para eixos
        if key == Qt.Key.Key_Left:
            axis_to_stop, direction = 'X', '-'
        elif key == Qt.Key.Key_Right:
            axis_to_stop, direction = 'X', '+'
        elif key == Qt.Key.Key_Up:
            axis_to_stop, direction = 'Y2', '+'
        elif key == Qt.Key.Key_Down:
            axis_to_stop, direction = 'Y2', '-'
        elif key == Qt.Key.Key_W:
            axis_to_stop, direction = 'Y1', '+'
        elif key == Qt.Key.Key_S:
            axis_to_stop, direction = 'Y1', '-'
        elif key == Qt.Key.Key_Q:
            axis_to_stop, direction = 'Z', '+'
        elif key == Qt.Key.Key_E:
            axis_to_stop, direction = 'Z', '-'
        
        # Para JOG se tecla válida e eixo estiver ativo
        if axis_to_stop and self.keyboard_jog_active[axis_to_stop]:
            self.keyboard_jog_active[axis_to_stop] = False
            self.jog_stop(axis_to_stop)
            
            # Mapeamento de símbolos para log
            key_symbols = {
                'X': {'+':"→", '-':"←"},
                'Y2': {'+':"↑", '-':"↓"},
                'Y1': {'+':"W", '-':"S"},
                'Z': {'+':"Q", '-':"E"}
            }
            symbol = key_symbols[axis_to_stop][direction]
            self.log(f"⌨️ JOG {axis_to_stop}{direction} parado via teclado ({symbol})")
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
            emergency_memories = [
                'M0_Y2', 'M50_Y2', 'M100_Y2', 'M500_Y1', 'M550_Y1', 'M600_Y1',
                'M1500_Z', 'M1550_Z', 'M1600_Z', 'M1000_X', 'M1050_X', 'M1100_X',
                'M5000', 'M350', 'M850', 'M1350', 'M1850',
                'M70_Y2', 'M80_Y2', 'M570_Y1', 'M580_Y1', 'M1070_X', 'M1080_X', 'M1570_Z', 'M1580_Z'
            ]
            for mem in emergency_memories:
                self.client.write_coil(self.addresses[mem], False)
            
            # Para JOG de todos os eixos
            for axis in ['Y2', 'Y1', 'X', 'Z']:
                self.jog_stop(axis)

            # Lê posições uma última vez antes de parar
            self.read_current_positions()

            # Para JOG via teclado se estiver ativo para qualquer eixo
            if hasattr(self, 'keyboard_jog_active'):
                for axis in self.keyboard_jog_active:
                    if self.keyboard_jog_active[axis]:
                        self.keyboard_jog_active[axis] = False
                        self.jog_stop(axis)
                self.log("⌨️ JOG via teclado interrompido por emergência")
                
            # Desliga o botão Y0.10 na interface
            self.y010_btn.setChecked(False)
                
            self.log("✅ Todos os comandos desligados")
            
        except Exception as e:
            self.log(f"❌ Erro na parada: {e}")

    # ================================================================
    # callbacks vindos do MovementControlsWidget
    # ================================================================
    def _on_step_move_requested(self, axis: str, distance: float, feed: float):
        """Step = movimento incremental curto, em milímetros."""
        pulses = self.pulses_from_mm(axis, distance)
        self.move_relative(axis, pulses)

    def _on_widget_jog_start(self, axis: str, direction: int, feed: float):
        self._active_widget_axis = axis
        self.jog_start(axis, '+' if direction > 0 else '-')

    def _on_widget_jog_stop(self):
        if hasattr(self, '_active_widget_axis'):
            self.jog_stop(self._active_widget_axis)

    def _on_go_to_zero(self):
        # usa homing (já implementado) para Z primeiro e depois Y2,Y1,X
        self.home_all_axes()

    # ================================================================
    #  S T A R T   G E R A L
    # ================================================================
    def start_global_cycle(self):
        """
        1. Verifica se existe pelo menos UM programa carregado
           (Mesa 1 e/ou Mesa 2).
        2. Para cada mesa com programa:
              – move o berço (eixo Y físico da mesa) até o limite
                POSITIVO configurado em settings.table_limits;
              – aguarda o eixo ficar idle.
        3. Exibe erro se nenhuma mesa possui programa.
        4. Deixa _global_cycle_active = True para indicar que a
           máquina está pronta e o fluxo PlateFlow pode iniciar
           quando o operador pressionar M20 / M30.
        """
        from PyQt6.QtWidgets import QMessageBox

        if self._global_cycle_active:
            self.log("■ Start Geral já está ativo – comando ignorado")
            return

        # ---------------------- 1. detecção de programas -----------------
        mesas_com_prog = []
        for mesa_id, tab in self.mesa_tabs.items():
            if self._mesa_has_program(mesa_id):
                mesas_com_prog.append(mesa_id)

        if not mesas_com_prog:
            QMessageBox.warning(
                self, "Start Geral",
                "Nenhum programa está carregado em Mesa 1 ou Mesa 2.")
            self.log("■ Start Geral cancelado – nenhuma mesa tem programa")
            return

        # ---------------------- 2. prepara mesas -------------------------
        for mesa_id in mesas_com_prog:
            try:
                self._prepare_table_for_cycle(mesa_id)
            except Exception as exc:
                self.log(f"■ Erro preparando Mesa {mesa_id}: {exc}")

        self._global_cycle_active = True
        self.log(f"■■ START GERAL – pronto. Mesas ativas: {mesas_com_prog}")

        # Aciona polling inicial dos PlateFlowManagers das mesas ativas
        for mid, mgr in ((1, getattr(self, "flow_mesa1", None)),
                         (2, getattr(self, "flow_mesa2", None))):
            if mgr and mid in mesas_com_prog:
                mgr.poll_now()

    # -----------------------------------------------------------------
    #  H E L P E R S
    # -----------------------------------------------------------------
    def _mesa_has_program(self, mesa_id: int) -> bool:
        """
        Retorna True se a aba da mesa possui pelo menos um ponto
        carregado (positions != []) OU se o ProgramIOWidget já tem
        um arquivo carregado (_last_file).
        """
        tab = self.mesa_tabs.get(mesa_id)
        if tab is None:
            return False
        if tab.inspect_widget.positions():
            return True
        return bool(getattr(tab.prog_widget, "_last_file", None))

    def _prepare_table_for_cycle(self, mesa_id: int):
        """
        Move o eixo Y físico da mesa até o limite POSITIVO configurado
        e aguarda a conclusão do movimento.
        """
        axis = 'Y1' if mesa_id == 1 else 'Y2'
        lim  = int(self.table_limits[mesa_id]['y'][1])
        self.log(f"■ Mesa {mesa_id}: levando berço ao limite +Y ({lim})")
        getattr(self, f'pulsos_spin_{axis}').setValue(lim)
        self.move_axis_absolute(axis)
        if not self._plc_motion_backend.wait_for_idle():
            raise RuntimeError("timeout aguardando eixo chegar ao limite")

    # ================================================================
    # zerar posição individual (M0/M500/…)
    # ================================================================
    def zero_axis(self, axis: str):
        """Pulsa a memória M0/M500/M1000/M1500 conforme eixo."""
        mem_map = {'Y2':'M0_Y2', 'Y1':'M500_Y1', 'X':'M1000_X', 'Z':'M1500_Z'}
        if axis in mem_map:
            self._pulse_coil(mem_map[axis])
            self.log(f"üè† Zero absoluto do eixo {axis} solicitado")
            
    def update_status(self):
        """Atualiza status em tempo real"""
        if not self.connected:
            return
        
        # Lê posições atuais e status de homing (prioridade)
        self.read_current_positions()
        # ------------ atualiza MovementControls principal --------------
        if hasattr(self, 'mov_widget'):
            self.mov_widget.update_position(
                x=self.current_positions['X'],
                y2=self.current_positions['Y2'],
                y1=self.current_positions['Y1'],
                z=self.current_positions['Z'])

        # ------------ atualiza widgets das mesas ------------------------
        for mesa_id, tab in getattr(self, 'mesa_tabs', {}).items():
            # envia posição para cada mov_widget da mesa
            if tab.y_axis == 'Y1':
                tab.mov_widget.update_position(
                    x=self.current_positions['X'],
                    y2=0,
                    y1=self.current_positions['Y1'],
                    z=self.current_positions['Z'])
            else:
                tab.mov_widget.update_position(
                    x=self.current_positions['X'],
                    y2=self.current_positions['Y2'],
                    y1=0,
                    z=self.current_positions['Z'])
        self.monitor_homing_status()
        # ------------ atualiza gráficos das mesas -----------------------
        if hasattr(self, "mesa_plot_widgets"):
            self.mesa_plot_widgets[1].update_head_position(
                self.current_positions['X'],
                self.current_positions['Y1'])
            self.mesa_plot_widgets[2].update_head_position(
                self.current_positions['X'],
                self.current_positions['Y2'])
        # ajusta foco conforme Z
        self.camera_manager.auto_focus(self.current_positions['Z'])  
            
        try:
            # Atualiza saídas
            outputs_map = {
                'Y0_0': ('Y00', self.Y0_0_status),
                'Y0_1': ('Y01', self.Y0_1_status),
                'Y0_4': ('Y04', self.Y0_4_status),
                'Y0_5': ('Y05', self.Y0_5_status),
                'Y0_2': ('Y02', self.Y0_2_status),
                'Y0_3': ('Y03', self.Y0_3_status),
                'Y0_6': ('Y06', self.Y0_6_status),
                'Y0_7': ('Y07', self.Y0_7_status),
                'Y0_10': ('Y010', self.Y0_10_status)
             }
            
            for name, (addr_key, label) in outputs_map.items():
                # Y = coils  ➜ FC01 (read_coils)
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
                'M500_Y1': (self.addresses['M500_Y1'], getattr(self, 'M500_Y1_status', None)),
                'M550_Y1': (self.addresses['M550_Y1'], getattr(self, 'M550_Y1_status', None)),
                # Disparo e status da aplicadora
                'M5000': (self.addresses['M5000'], getattr(self, 'M5000_status', None)),
                'M5001': (self.addresses['M5001'], getattr(self, 'M5001_status', None)),
                
                'M350': (self.addresses['M350'], getattr(self, 'M350_status', None)),
                'M850': (self.addresses['M850'], getattr(self, 'M850_status', None)),
                'M1350': (self.addresses['M1350'], getattr(self, 'M1350_status', None)),
                'M1850': (self.addresses['M1850'], getattr(self, 'M1850_status', None)),
                # MEMÓRIAS DE HOMING REALIZADO - PRIORITÁRIAS
                'M300': (self.addresses['M300'], getattr(self, 'M300_status', None)),
                'M800': (self.addresses['M800'], getattr(self, 'M800_status', None)),
                'M1300': (self.addresses['M1300'], getattr(self, 'M1300_status', None)),
                'M1800': (self.addresses['M1800'], getattr(self, 'M1800_status', None)),
                # Monitoramento JOG (apenas alguns principais)
                'M70_Y2': (self.addresses['M70_Y2'], getattr(self, 'M70_Y2_status', None)),
                'M570_Y1': (self.addresses['M570_Y1'], getattr(self, 'M570_Y1_status', None)),
                'M1070_X': (self.addresses['M1070_X'], getattr(self, 'M1070_X_status', None)),
                'M1570_Z': (self.addresses['M1570_Z'], getattr(self, 'M1570_Z_status', None))
            }
            
            for name, (addr, label) in memories_map.items():
                if name in ['M300', 'M800', 'M1300', 'M1800']:
                    continue  # Pula memórias de homing (tratadas em função dedicada)
                
                if label is None:
                    continue
                result = self.client.read_coils(addr, count=1)
                if not result.isError():
                    state = result.bits[0]
                    # Atualiza label se existir
                    if label is not None:
                        label.setText("ON" if state else "OFF")
                        # Para M5001 usamos cor laranja enquanto ativo
                        if name == 'M5001':
                            label.setStyleSheet(
                                "QLabel { background-color: orange; color: black; padding: 5px; }" if state
                                else "QLabel { background-color: gray; color: white; padding: 5px; }"
                            )
                        else:
                            label.setStyleSheet(
                                "QLabel { background-color: red; color: white; padding: 5px; }" if state
                                else "QLabel { background-color: gray; color: white; padding: 5px; }"
                            )
                                            
                # Atualiza status JOG ativo para todos os eixos
                if name in ['M70_Y2', 'M570_Y1', 'M1070_X', 'M1570_Z']:
                    jog_status_map = {
                        'M70_Y2': ('Y2', 'POSITIVO'),
                        'M570_Y1': ('Y1', 'POSITIVO'),
                        'M1070_X': ('X', 'POSITIVO'),
                        'M1570_Z': ('Z', 'POSITIVO')
                    }
                    
                    if name in jog_status_map and not result.isError():
                        axis, direction = jog_status_map[name]
                        status_label = getattr(self, f'jog_status_label_{axis}', None)
                        if status_label:
                            if state:
                                self.update_jog_status(axis, f"ATIVO - {direction}", "lime")
                            elif not state and direction in status_label.text():
                                self.update_jog_status(axis, "Inativo", "gray")
                                
                    # Atualiza segurança JOG em tempo real apenas quando necessário
                if name in ['M10_Y2', 'M11_Y2', 'M510_Y1', 'M511_Y1', 'M1010_X', 'M1011_X', 'M1510_Z', 'M1511_Z']:
                    axis_map = {
                        'M10_Y2': 'Y2', 'M11_Y2': 'Y2',
                        'M510_Y1': 'Y1', 'M511_Y1': 'Y1', 
                        'M1010_X': 'X', 'M1011_X': 'X',
                        'M1510_Z': 'Z', 'M1511_Z': 'Z'
                    }
                    if name in axis_map:
                        axis = axis_map[name]
                        QTimer.singleShot(50, lambda a=axis: self.check_jog_safety(a))
            
            # Atualiza registradores
            registers_map = {
                # Registradores dos eixos
                'D100_Y2': (self.addresses['D100_Y2'], getattr(self, 'D100_Y2_status', None)),
                'D20000_Y2': (self.addresses['D20000_Y2'], getattr(self, 'D20000_Y2_status', None)),
                'D1600_Z': (self.addresses['D1600_Z'], getattr(self, 'D1600_Z_status', None)),
                'D21500_Z': (self.addresses['D21500_Z'], getattr(self, 'D21500_Z_status', None)),
                'D1100_X': (self.addresses['D1100_X'], getattr(self, 'D1100_X_status', None)),
                'D21000_X': (self.addresses['D21000_X'], getattr(self, 'D21000_X_status', None))
            }

            # ------------------------- SENSORES HOME -------------------------
            sensors_map = {
                'X04_Y2': ('X04_Y2_status', self.addresses['X04_Y2']),
                'X06_Y1': ('X06_Y1_status', self.addresses['X06_Y1']),
                'X08_X':  ('X08_X_status',  self.addresses['X08_X']),
                'X09_Z':  ('X09_Z_status',  self.addresses['X09_Z'])
            }

            for sensor_key, (label_attr, addr) in sensors_map.items():
                lbl = getattr(self, label_attr, None)
                if lbl is None:
                    continue
                # X = discrete inputs ➜ FC02 (read_discrete_inputs)
                res = self.client.read_discrete_inputs(addr, count=1)
                if not res.isError():
                    state = res.bits[0]
                    lbl.setText("ON" if state else "OFF")
                    lbl.setStyleSheet(
                        "QLabel { background-color: lime; color: black; padding: 5px; }" if state
                        else "QLabel { background-color: gray; color: white; padding: 5px; }"
                    )
            
            for name, (addr, label) in registers_map.items():
                try:
                    # Todos agora são registradores D normais
                    signed = self.read_dword(addr)
                      
                    if label is not None:
                        label.setText(str(signed))
                        # cor laranja se negativo
                        label.setStyleSheet(
                            "QLabel { background-color: orange; padding: 5px; }"
                            if signed < 0 else
                            "QLabel { background-color: lightgray; padding: 5px; }"
                        )
                except Exception as e:
                    self.log(f"⚠️ Erro ao ler registrador {name}: {e}")
        except Exception as e:
            self.log(f"⚠️ Erro ao atualizar status: {e}")
    
    # ------------------------------------------------------------------
    #  Fornece posição atual para o widget de inspeção
    # ------------------------------------------------------------------
    def _get_current_position_dict(self) -> dict:
        """
        Retorna dict {x,y2,y1,z} em pulsos – usado pelo
        InspectionPositionsWidget para ‘Adicionar posição atual’.
        """
        return {
            "x":  self.current_positions.get("X",  0),
            "y2": self.current_positions.get("Y2", 0),
            "y1": self.current_positions.get("Y1", 0),
            "z":  self.current_positions.get("Z",  0),
        }
    
    # ------------------------------------------------------------------
    # converte lista do widget para InspectionPosition do sequence_control
    # ------------------------------------------------------------------
    def _positions_to_model(self):
        lst = []
        for p in self.inspect_widget.positions():
            lst.append(
                InspectionPosition(
                    name=p.name,
                    x=p.x, y2=p.y2, y1=p.y1, z=p.z
                )
            )
        return lst

    def force_homing_status_check(self):
        """Força uma verificação imediata do status de homing"""
        try:
            self.log("🔍 Verificação forçada do status de homing...")
            self.monitor_homing_status()
        except Exception as e:
            self.log(f"❌ Erro na verificação forçada: {e}")
            
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
                    
    def test_position_reading(self):
        """Função de teste para verificar leitura das posições"""
        if not self.connected:
            return
            
        self.log("🔧 Testando leitura das posições atuais...")
        
        # Usa a função dedicada e exibe resultados
        self.read_current_positions()
        
        # Log das posições lidas
        for axis, position in self.current_positions.items():
            self.log(f"📊 Posição {axis}: {position}")
        self.test_homing_status()
        
            
    def closeEvent(self, event):
        """Fecha conexão ao sair"""
        if self.client:
            self.emergency_stop()
            self.client.close()
            self.status_bar.showMessage("Desconectado")
            self.status_bar.setStyleSheet(
                "QStatusBar { background-color:red; color:white; font-weight:bold; }")
            self.log("Desconectado do CLP")
        event.accept()

# ------------------------------------------------------------------
#  BACK-END DE MOVIMENTO para o SequenceControlWidget
# ------------------------------------------------------------------

class PLCMotionBackend(MotionBackend):
    """
    Adaptador simples que converte as chamadas do SequenceControlWidget
    para os métodos já existentes do MultiAxisMotorController.
    """
    def __init__(self, ctrl: MultiAxisMotorController):
        self._c = ctrl
        self._off_x = ctrl.camera_nozzle_offset.get("x", 0)
        self._off_y = ctrl.camera_nozzle_offset.get("y", 0)
        self._feed = 1000
        self._apply_offset = True      # default = APPLY
        # ---------- deslocamento dinâmico calculado por fiducial -----
        self._dx_dyn = 0          # em pulsos
        self._dy_dyn = 0
        # guarda último ΔX/ΔY ≠ 0 para leitura pós-runner
        self._last_offset: tuple[int,int] = (0, 0)
        self._targets: dict[str,int] = {}   # destino mais recente por eixo
        # registrador de QUANTIDADE de dots
        self._addr_qty = ctrl.addresses.get('D24100_QTY')
        # coils para dot
        self._addr_trig = ctrl.addresses.get('M5000')
        self._addr_stat = ctrl.addresses.get('M5001')

    # --------------------------------------------------------------
    def move_to_absolute_position(self,
                                  x:  float | None,
                                  y2: float | None,
                                  y1: float | None,
                                  z:  float | None,
                                  feed_rate: float = 1000) -> bool:
        self._feed = feed_rate
        # ----------------------------------------------------------------
        # LIMPA destinos da execução anterior  ← BUG FIX travamento 2ª run
        # ----------------------------------------------------------------
        self._targets.clear()
        try:
            # Escreve apenas eixos cujo valor não é None
            dx = self._off_x if self._apply_offset else 0
            dy = self._off_y if self._apply_offset else 0
            if x  is not None:  self._move_axis('X',  int(x)  - dx)
            if y2 is not None:  self._move_axis('Y2', int(y2) - dy)
            if y1 is not None:  self._move_axis('Y1', int(y1) - dy)
            if z  is not None:  self._move_axis('Z',  int(z))
            return True
        except Exception as exc:
            print(f"Erro move_to_absolute_position: {exc}")
            self._c.log(f"Erro move_to_abs: {exc}")
            return False
    
    # --------------------------------------------------------------
    #  NOVO: muda modo de offset  (True = APPLY, False = VIEW)
    # --------------------------------------------------------------
    def set_offset_mode(self, apply_offset: bool):
        self._apply_offset = bool(apply_offset)

    # ===============================================================
    #  recebe ΔX / ΔY (pulsos) calculado pelo fiducial
    # ===============================================================
    def apply_dynamic_offset(self, dx_pulses: int, dy_pulses: int):
        self._dx_dyn = dx_pulses
        self._dy_dyn = dy_pulses
        if dx_pulses or dy_pulses:
            self._last_offset = (dx_pulses, dy_pulses)
        self._c.log(f"■ Offset dinâmico aplicado: ΔX={dx_pulses}  ΔY={dy_pulses}")

    def _move_axis(self, axis: str, pulses: int):
        # acrescenta deslocamento dinâmico a X/Y apenas
        if axis == "X":
            pulses += self._dx_dyn
        elif axis in ("Y1", "Y2"):
            pulses += self._dy_dyn

        spin = getattr(self._c, f"pulsos_spin_{axis}")
        spin.setValue(int(pulses))
        self._c.move_axis_absolute(axis)
        self._targets[axis] = pulses
        # Não bloqueia aqui – wait_for_idle fará polling

    # --------------------------------------------------------------
    def wait_for_idle(self) -> bool:
        """Bloqueia até que cada eixo alcance o pulso alvo ±1."""
        t0 = time.time()
        timeout = 120          # s – eixo pode percorrer longas distâncias
        ok_axes = set()

        pos_regs = {           # registradores D que espelham SR
            'Y2': self._c.addresses['D3100_Y2'],
            'Y1': self._c.addresses['D3400_Y1'],
            'X' : self._c.addresses['D3000_X'],
            'Z' : self._c.addresses['D3200_Z'],
        }

        while time.time() - t0 < timeout:
            all_reached = True
            # copia para evitar “dictionary changed size”
            for axis, target in list(self._targets.items()):
                if axis in ok_axes:
                    continue

                try:
                    pos = self._c.read_dword(pos_regs[axis])
                except Exception as exc:
                    self._c.log(f"Erro ao ler posição do eixo {axis}: {exc}")
                    pos = None

                if pos is None or abs(pos - target) > 1:
                    all_reached = False
                else:
                    ok_axes.add(axis)

            if all_reached:
                return True
            time.sleep(0.05)

        self._c.log("wait_for_idle: timeout atingido")
        return False

    # --------------------------------------------------------------
    def set_feed_rate(self, fr: float):
        self._feed = fr

    # --------------------------------------------------------------
    #  DOT – grava SOMENTE a quantidade (D24100)
    # --------------------------------------------------------------
    def apply_dot_qty(self, qty: int):
        if not self._c.connected:
            return
        try:
            if self._addr_qty is not None:
                self._c.write_dword(self._addr_qty, int(qty))
                self._c.log(f"■ DOT qty → D24100={qty}")
        except Exception as exc:
            self._c.log(f"■ Erro ao escrever DOT cfg: {exc}")

    # --------------------------------------------------------------
    #  DISPARO DO DOT (pulso M5000)  + espera M5001
    # --------------------------------------------------------------
    def trigger_dot(self, pulse_ms: int = 100) -> bool:
        """
        Gera um pulso no coil M5000.  Retorna True se escrito com sucesso.
        """
        if not self._c.connected or self._addr_trig is None:
            return False
        try:
            self._c.client.write_coil(self._addr_trig, True)
            time.sleep(pulse_ms / 1000.0)
            self._c.client.write_coil(self._addr_trig, False)
            self._c.log("■ Pulso M5000 enviado")
            return True
        except Exception as exc:
            self._c.log(f"■ Erro no pulso M5000: {exc}")
            return False

    def wait_dot_complete(self, timeout: float = 10.0) -> bool:
        """
        Aguarda M5001 ligar (start) e desligar (fim) dentro do timeout.
        """
        if not self._c.connected or self._addr_stat is None:
            return True          # nada a esperar – não bloqueia
        t0 = time.time()
        # espera LIGAR
        while time.time() - t0 < timeout:
            try:
                r = self._c.client.read_coils(self._addr_stat, count=1)
                if not r.isError() and r.bits[0]:
                    break
            except Exception as exc:
                self._c.log(f"Erro ao esperar M5001=ON: {exc}")
                pass
            time.sleep(0.05)
        else:
            self._c.log("■ Timeout esperando M5001=ON")
            return False

        # espera DESLIGAR
        while time.time() - t0 < timeout:
            try:
                r = self._c.client.read_coils(self._addr_stat, count=1)
                if not r.isError() and not r.bits[0]:
                    self._c.log("■ Dot concluído (M5001=OFF)")
                    return True
            except Exception as exc:
                self._c.log(f"Erro ao esperar M5001=OFF: {exc}")
            time.sleep(0.05)
        self._c.log("■ Timeout esperando M5001=OFF")
        return False

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = MultiAxisMotorController()
    window.showMaximized()   # abre já maximizado
    
    print("="*60)
    print("CONTROLE MULTI-EIXOS - DELTA AS (ENDEREÇOS LADDER REAIS)")
    print("="*60)
    print("✅ MELHORIAS IMPLEMENTADAS:")
    print("• Endereços corrigidos conforme planilha do ladder real")
    print("• Controle de 4 eixos: Y2, Y1, Z, X")
    print("• Botões HOME corrigidos: M350, M1350, M1850")
    print("• Posições atuais via D3000, D3100, D3200")
    print("• Indicadores LED de homing e leitura automática de velocidades")
    print("• Sistema JOG integrado para TODOS os eixos com segurança")
    print("✓ Controle via teclado para TODOS os eixos:")
    print("  • X: ← →  • Y2: ↑ ↓  • Y1: W S  • Z: Q E")
    print("• Movimentos absolutos com verificação de limites")
    print("• Configurações de homing e limites salvos em ROM")
    print("• Interface redesenhada para melhor usabilidade")
    print("• Leitura em tempo real das posições dos motores corrigida")
    print("• Status inicial e atualização automática dos LEDs de homing")
    print("="*60)
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
