#config_manager.py

import os, json, logging
from pathlib import Path

# ------------------------------------------------------------
#  AOIConfigManager  –  gerencia arquivo JSON de preferências
# ------------------------------------------------------------
class AOIConfigManager:
    _DEFAULT_CFG = {
        "cnc": {
            "system_type": "cartesian",          # cartesian  |  corexy
            "max_feed": {"x": 2500.0, "y": 2500.0, "z": 800.0},   # + $112
            "max_acc":  {"x": 120.0,  "y": 120.0,  "z": 60.0},   # + $122
            "invert_y": True,                         # sentido lógico (+Y frente)
            "invert_z": False,                        # novo – (+Z = cima)
            "motor_hold_enabled": True,  # Manter motores energizados quando parados
            # apenas se corexy estiver selecionado
            "corexy_config": {
                "motor_a_invert": False,
                "motor_b_invert": False,
                "steps_per_unit": 80.0
            }
        },
        "connections": {
            "last_cnc_port": "",
            "plc_host": "192.168.0.5",  # IP padrão do PLC
            "plc_port": 502,            # Porta padrão Modbus TCP
            "auto_connect_cnc": True,
            "last_camera_id": 0,
            "auto_connect_camera": True
        },
        "ui": {
            "theme": "light"
        },
        # ---------- CONFIGURAÇÕES DE MOVIMENTO -----------
        "movement": {                     # controles manuais
            "step_size": 10.0,            # mm
            "feed_rate": 1000.0           # mm/min
        },
        "calibration": {                  # parâmetros mecânicos
            "pulses_per_rev": 400.0,
            "fuso_pitch": 5.0             # mm / volta
        },
        # ---------- CONFIGURAÇÕES DE CÂMERA -----------
        "camera": {
            "mirror_x": False,            # Espelhar horizontalmente
            "mirror_y": False,            # Espelhar verticalmente
            "brightness": 128,
            "contrast": 128,
            "saturation": 128,
            "exposure": -6,
            "gain": 128,
            "auto_exposure": True,
            "auto_white_balance": True,
            "calibration_file": ""        # Arquivo de calibração de distorção
        },
        # ---------- CONFIGURAÇÕES DE MOSAICO -----------
        "mosaic": {
            "auto_build": True,           # Montar mosaico automaticamente
            "margin": 50,                 # Margem de corte (px)
            "blend_size": 20,             # Tamanho do blending (px)
            "use_multiband": False,       # Usar blending multiband
            "capture_delay_ms": 200,      # Tempo de espera antes da captura
            "delta_x": 0,                 # Ajuste horizontal entre tiles
            "delta_y": 0,                 # Ajuste vertical entre tiles
            "invert_rows": True,          # Origem no canto inferior-esquerdo
            "last_folder": "",            # Última pasta usada
            "last_program_name": ""       # Último nome de programa
        },
        # ---------- CONFIGURAÇÕES DE MAPA -----------
        "map": {
            "step_x": 50.0,               # Passo X (mm)
            "step_y": 50.0                # Passo Y (mm)
        }
    }

    # ---- atalhos para gravação rápida -------
    def remember_cnc_port(self, port: str):
        self.set("connections", "last_cnc_port", value=port)
    def remember_camera_id(self, cam_id: int | str):
        self.set("connections", "last_camera_id", value=int(cam_id))
    def remember_step_feed(self, step: float, feed: float):
        self.set("movement", "step_size",  value=step)
        self.set("movement", "feed_rate",  value=feed)
    def remember_calibration(self, pulses: float, fuso: float):
        self.set("calibration", "pulses_per_rev", value=pulses)
        self.set("calibration", "fuso_pitch",     value=fuso)

    # -------- novo atalho para lembrar o sistema de eixos ---------------
    def remember_system_type(self, sys_type: str):
        """Grava cartesian|corexy escolhido pelo usuário."""
        self.set("cnc", "system_type", value=sys_type.lower())

    # -------- atalhos para configurações de câmera ---------------
    def remember_camera_settings(self, mirror_x: bool, mirror_y: bool, 
                                  brightness: int = 128, contrast: int = 128,
                                  saturation: int = 128, exposure: int = -6,
                                  gain: int = 128, auto_exp: bool = True,
                                  auto_wb: bool = True):
        """Grava configurações de câmera."""
        self.set("camera", "mirror_x", value=mirror_x)
        self.set("camera", "mirror_y", value=mirror_y)
        self.set("camera", "brightness", value=brightness)
        self.set("camera", "contrast", value=contrast)
        self.set("camera", "saturation", value=saturation)
        self.set("camera", "exposure", value=exposure)
        self.set("camera", "gain", value=gain)
        self.set("camera", "auto_exposure", value=auto_exp)
        self.set("camera", "auto_white_balance", value=auto_wb)

    def remember_camera_calibration(self, filepath: str):
        """Grava caminho do arquivo de calibração de câmera."""
        self.set("camera", "calibration_file", value=filepath)

    # -------- atalhos para configurações de mosaico ---------------
    def remember_mosaic_settings(self, auto_build: bool, margin: int, 
                                  blend_size: int, capture_delay_ms: int,
                                  use_multiband: bool = False):
        """Grava configurações de mosaico."""
        self.set("mosaic", "auto_build", value=auto_build)
        self.set("mosaic", "margin", value=margin)
        self.set("mosaic", "blend_size", value=blend_size)
        self.set("mosaic", "capture_delay_ms", value=capture_delay_ms)
        self.set("mosaic", "use_multiband", value=use_multiband)

    def remember_mosaic_adjustments(self, delta_x: int, delta_y: int, invert_rows: bool):
        """Grava ajustes de sobreposição do mosaico."""
        self.set("mosaic", "delta_x", value=delta_x)
        self.set("mosaic", "delta_y", value=delta_y)
        self.set("mosaic", "invert_rows", value=invert_rows)

    def remember_map_params(self, step_x: float, step_y: float, 
                            folder: str = "", program_name: str = ""):
        """Grava configurações de mapa."""
        self.set("map", "step_x", value=step_x)
        self.set("map", "step_y", value=step_y)
        if folder:
            self.set("mosaic", "last_folder", value=folder)
        if program_name:
            self.set("mosaic", "last_program_name", value=program_name)

    def __init__(self, cfg_path: str | None = None):
        self.log = logging.getLogger("AOIConfig")
        # Se o caminho não for informado, grava ao lado do executável
        default_path = Path(__file__).resolve().parent.parent / "aoi_config.json"
        self.cfg_path = Path(cfg_path) if cfg_path else default_path
        self.data = {}
        self.load()

    # ---------------- json  -----------------
    def load(self):
        if self.cfg_path.exists():
            try:
                with open(self.cfg_path, "r", encoding="utf-8") as fp:
                    self.data = json.load(fp)
                self.log.info("Config carregada de %s", self.cfg_path)
            except Exception as e:
                self.log.error("Falha ao ler config, usando padrão: %s", e)
                self.data = self._DEFAULT_CFG.copy()
        else:
            self.log.info("Arquivo de config inexistente – criando padrão em %s", self.cfg_path)
            self.data = self._DEFAULT_CFG.copy()
            self.save()

    def save(self):
        try:
            with open(self.cfg_path, "w", encoding="utf-8") as fp:
                json.dump(self.data, fp, indent=2)
            self.log.debug("Config salva em %s", self.cfg_path)
        except Exception as e:
            self.log.error("Erro salvando config: %s", e)

    # ------------- API simples -------------
    def get(self, *path, default=None):
        ref = self.data
        for p in path:
            if p not in ref:
                return default
            ref = ref[p]
        return ref

    def set(self, *path, value):
        ref = self.data
        for p in path[:-1]:
            ref = ref.setdefault(p, {})
        ref[path[-1]] = value
        self.save()

    # -------- aplica configurações ao controlador de eixos -------
    def apply_to_cnc(self, cnc):
        """
        Aplica configurações salvas ao controlador de eixos (PLC).
        Atualiza velocidades máximas e fator de calibração.
        """
        if not cnc or not cnc.is_connected:
            return
        
        # Aplica velocidades máximas (limites de segurança)
        maxf = self.get("cnc", "max_feed", default={})
        if hasattr(cnc, 'max_feed'):
            cnc.max_feed['x'] = maxf.get('x', 5000)
            cnc.max_feed['y'] = maxf.get('y', 5000)
            cnc.max_feed['z'] = maxf.get('z', 800)
        
        # Aplica fator de conversão pulsos/mm
        ppr = self.get("calibration", "pulses_per_rev", default=1000)
        pitch = self.get("calibration", "fuso_pitch", default=10)
        if pitch > 0 and hasattr(cnc, 'pulses_per_mm'):
            cnc.pulses_per_mm = ppr / pitch
        
        self.log.info(f"Configurações aplicadas ao PLC: max_feed={maxf}, pulses_per_mm={ppr/pitch if pitch > 0 else 'N/A'}")


# ============================================================
#  SettingsDialog – UI PyQt6 para editar as preferências
# ============================================================
from PyQt6.QtWidgets import (QDialog, QFormLayout, QDoubleSpinBox, QCheckBox,
                             QPushButton, QHBoxLayout, QVBoxLayout, QGroupBox, 
                             QComboBox, QLineEdit, QSpinBox, QLabel, QTabWidget,
                             QWidget)

class SettingsDialog(QDialog):
    def __init__(self, cfg: AOIConfigManager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preferências do Sistema AOI")
        self.cfg = cfg
        self.setMinimumWidth(450)
        
        main_layout = QVBoxLayout(self)
        
        # Cria abas para organizar as configurações
        tabs = QTabWidget()
        main_layout.addWidget(tabs)
        
        # ================== ABA: CONEXÕES ==================
        conn_tab = QWidget()
        conn_layout = QFormLayout(conn_tab)
        
        # Grupo PLC
        plc_group = QGroupBox("Conexão PLC (Modbus TCP)")
        plc_layout = QFormLayout(plc_group)
        
        self.edit_plc_host = QLineEdit()
        self.edit_plc_host.setText(cfg.get("connections", "plc_host", default="192.168.0.5"))
        plc_layout.addRow("Endereço IP:", self.edit_plc_host)
        
        self.spin_plc_port = QSpinBox()
        self.spin_plc_port.setRange(1, 65535)
        self.spin_plc_port.setValue(cfg.get("connections", "plc_port", default=502))
        plc_layout.addRow("Porta Modbus:", self.spin_plc_port)
        
        conn_layout.addRow(plc_group)
        
        # Grupo Câmera
        cam_group = QGroupBox("Câmera")
        cam_layout = QFormLayout(cam_group)
        
        self.spin_camera_id = QSpinBox()
        self.spin_camera_id.setRange(0, 10)
        self.spin_camera_id.setValue(cfg.get("connections", "last_camera_id", default=0))
        cam_layout.addRow("ID da Câmera:", self.spin_camera_id)
        
        self.chk_auto_camera = QCheckBox("Conectar câmera automaticamente")
        self.chk_auto_camera.setChecked(cfg.get("connections", "auto_connect_camera", default=False))
        cam_layout.addRow(self.chk_auto_camera)
        
        conn_layout.addRow(cam_group)
        
        tabs.addTab(conn_tab, "Conexões")
        
        # ================== ABA: MOVIMENTO ==================
        mov_tab = QWidget()
        mov_layout = QFormLayout(mov_tab)
        
        # Velocidades máximas (limites de segurança na UI)
        speed_group = QGroupBox("Velocidades Máximas (mm/min)")
        speed_layout = QFormLayout(speed_group)
        
        self.spin_f_x = QDoubleSpinBox()
        self.spin_f_x.setRange(1, 30000)
        self.spin_f_x.setValue(cfg.get("cnc", "max_feed", "x", default=5000))
        speed_layout.addRow("Eixo X:", self.spin_f_x)
        
        self.spin_f_y = QDoubleSpinBox()
        self.spin_f_y.setRange(1, 30000)
        self.spin_f_y.setValue(cfg.get("cnc", "max_feed", "y", default=5000))
        speed_layout.addRow("Eixo Y:", self.spin_f_y)
        
        self.spin_f_z = QDoubleSpinBox()
        self.spin_f_z.setRange(1, 30000)
        self.spin_f_z.setValue(cfg.get("cnc", "max_feed", "z", default=800))
        speed_layout.addRow("Eixo Z:", self.spin_f_z)
        
        mov_layout.addRow(speed_group)
        
        # Calibração mecânica
        calib_group = QGroupBox("Calibração Mecânica")
        calib_layout = QFormLayout(calib_group)
        
        self.spin_pulses_rev = QDoubleSpinBox()
        self.spin_pulses_rev.setRange(1, 100000)
        self.spin_pulses_rev.setValue(cfg.get("calibration", "pulses_per_rev", default=1000))
        calib_layout.addRow("Pulsos por revolução:", self.spin_pulses_rev)
        
        self.spin_fuso = QDoubleSpinBox()
        self.spin_fuso.setRange(0.1, 100)
        self.spin_fuso.setValue(cfg.get("calibration", "fuso_pitch", default=10))
        calib_layout.addRow("Passo do fuso (mm):", self.spin_fuso)
        
        # Mostra o valor calculado
        self.lbl_pulses_mm = QLabel()
        self._update_pulses_mm_label()
        self.spin_pulses_rev.valueChanged.connect(self._update_pulses_mm_label)
        self.spin_fuso.valueChanged.connect(self._update_pulses_mm_label)
        calib_layout.addRow("Pulsos/mm:", self.lbl_pulses_mm)
        
        mov_layout.addRow(calib_group)
        
        tabs.addTab(mov_tab, "Movimento")
        
        # ================== ABA: INTERFACE ==================
        ui_tab = QWidget()
        ui_layout = QFormLayout(ui_tab)
        
        # Controles padrão
        default_group = QGroupBox("Valores Padrão")
        default_layout = QFormLayout(default_group)
        
        self.spin_step = QDoubleSpinBox()
        self.spin_step.setRange(0.1, 1000)
        self.spin_step.setValue(cfg.get("movement", "step_size", default=10))
        default_layout.addRow("Tamanho do passo (mm):", self.spin_step)
        
        self.spin_feed = QDoubleSpinBox()
        self.spin_feed.setRange(1, 10000)
        self.spin_feed.setValue(cfg.get("movement", "feed_rate", default=1000))
        default_layout.addRow("Feed Rate padrão (mm/min):", self.spin_feed)
        
        ui_layout.addRow(default_group)
        
        tabs.addTab(ui_tab, "Interface")
        
        # ------ botões ----------
        btn_box = QHBoxLayout()
        btn_ok = QPushButton("Salvar")
        btn_can = QPushButton("Cancelar")
        btn_ok.clicked.connect(self._on_save)
        btn_can.clicked.connect(self.reject)
        btn_box.addStretch()
        btn_box.addWidget(btn_ok)
        btn_box.addWidget(btn_can)
        main_layout.addLayout(btn_box)

    def _update_pulses_mm_label(self):
        """Atualiza o label de pulsos/mm calculado."""
        try:
            pulses = self.spin_pulses_rev.value()
            pitch = self.spin_fuso.value()
            if pitch > 0:
                pulses_mm = pulses / pitch
                self.lbl_pulses_mm.setText(f"<b>{pulses_mm:.2f}</b> pulsos/mm")
            else:
                self.lbl_pulses_mm.setText("Erro: passo = 0")
        except:
            self.lbl_pulses_mm.setText("--")

    def _on_save(self):
        # Conexões
        self.cfg.set("connections", "plc_host", value=self.edit_plc_host.text().strip())
        self.cfg.set("connections", "plc_port", value=self.spin_plc_port.value())
        self.cfg.set("connections", "last_camera_id", value=self.spin_camera_id.value())
        self.cfg.set("connections", "auto_connect_camera", value=self.chk_auto_camera.isChecked())
        
        # Velocidades
        self.cfg.set("cnc", "max_feed", "x", value=self.spin_f_x.value())
        self.cfg.set("cnc", "max_feed", "y", value=self.spin_f_y.value())
        self.cfg.set("cnc", "max_feed", "z", value=self.spin_f_z.value())
        
        # Calibração
        self.cfg.set("calibration", "pulses_per_rev", value=self.spin_pulses_rev.value())
        self.cfg.set("calibration", "fuso_pitch", value=self.spin_fuso.value())
        
        # Interface
        self.cfg.set("movement", "step_size", value=self.spin_step.value())
        self.cfg.set("movement", "feed_rate", value=self.spin_feed.value())
        
        self.accept()

