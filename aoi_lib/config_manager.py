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

    # -------- aplica limites ao GRBL -------
    def apply_to_cnc(self, cnc):
        """
        Envia $110,$111,$120,$121 e sentido de Y logo
        após a conexão da CNC.
        """
        # modo cartesiano × corexy ------------------
        try:
            sys_type = self.get("cnc", "system_type", default="cartesian")
            cnc.set_kinematics_mode(sys_type)
            # passa configurações específicas do CoreXY
            cnc.corexy_cfg = self.get("cnc", "corexy_config", default={})
            self.log.info("Modo de cinemática aplicado: %s", sys_type)
        except Exception as e:
            self.log.error("Falha ao aplicar modo de cinemática: %s", e)
        if not cnc or not cnc.is_connected:
            return
        maxf = self.get("cnc", "max_feed", default={})
        acc  = self.get("cnc", "max_acc",  default={})

        # ------------------ GARANTE EIXO Z ------------------
        # Se o usuário ainda não possui as novas chaves no JSON,
        # criamos valores seguros para evitar KeyError.
        if "z" not in maxf:
            maxf["z"] = 800.0          # mm/min   (ajuste depois em Preferências)
            self.set("cnc", "max_feed", "z", value=maxf["z"])
        if "z" not in acc:
            acc["z"] = 60.0            # mm/s²
            self.set("cnc", "max_acc",  "z", value=acc["z"])
        invert_y = self.get("cnc", "invert_y", default=True)
        invert_z = self.get("cnc", "invert_z", default=False)
        cmds = [
            f"$110={maxf['x']}", f"$111={maxf['y']}", f"$112={maxf['z']}",
            f"$120={acc['x']}",  f"$121={acc['y']}",  f"$122={acc['z']}",
        ]
        for c in cmds:
            cnc.send_command(c, priority=True)
        cnc.set_invert_y(invert=invert_y)
        cnc.set_invert_z(invert=invert_z)
        # Configuração de motor hold
        motor_hold = self.get("cnc", "motor_hold_enabled", default=True)
        cnc.set_motor_hold_enabled(motor_hold)
        self.log.info("Limites aplicados ao GRBL: feed %s  acc %s  invert_y=%s",
                      maxf, acc, invert_y, invert_z)

# ============================================================
#  SettingsDialog – UI PyQt6 para editar as preferências
# ============================================================
from PyQt6.QtWidgets import (QDialog, QFormLayout, QDoubleSpinBox, QCheckBox,
                             QPushButton, QHBoxLayout, QGroupBox, QComboBox)

class SettingsDialog(QDialog):
    def __init__(self, cfg: AOIConfigManager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preferências da AOI / CNC")
        self.cfg = cfg
        form = QFormLayout(self)

        # ------ widgets para feed / acel -------
        self.spin_f_x = QDoubleSpinBox(); self.spin_f_x.setRange(1, 30000)
        self.spin_f_y = QDoubleSpinBox(); self.spin_f_y.setRange(1, 30000)
        self.spin_f_z = QDoubleSpinBox(); self.spin_f_z.setRange(1, 30000)
        self.spin_a_x = QDoubleSpinBox(); self.spin_a_x.setRange(1, 1000)
        self.spin_a_y = QDoubleSpinBox(); self.spin_a_y.setRange(1, 1000)
        self.spin_a_z = QDoubleSpinBox(); self.spin_a_z.setRange(1, 1000)
        self.chk_invert_y = QCheckBox("Inverter lógica do eixo Y (+Y frente)")
        self.chk_invert_z = QCheckBox("Inverter lógica do eixo Z (+Z cima)")

        # Configuração de motor hold
        self.chk_motor_hold = QCheckBox("Manter motores energizados quando parados")
        self.chk_motor_hold.setToolTip("Evita que motores fiquem 'soltos' e possam ser girados manualmente")

        # valores atuais
        self.spin_f_x.setValue(cfg.get("cnc", "max_feed", "x"))
        self.spin_f_y.setValue(cfg.get("cnc", "max_feed", "y"))
        self.spin_a_x.setValue(cfg.get("cnc", "max_acc", "x"))
        self.spin_a_y.setValue(cfg.get("cnc", "max_acc", "y"))
        # Usa False como valor-padrão caso a chave ainda não exista no JSON
        self.chk_invert_y.setChecked(cfg.get("cnc", "invert_y", default=False))
        self.chk_invert_z.setChecked(cfg.get("cnc", "invert_z", default=False))
        self.spin_f_z.setValue(cfg.get("cnc", "max_feed", "z"))
        self.spin_a_z.setValue(cfg.get("cnc", "max_acc",  "z"))
        self.chk_motor_hold.setChecked(cfg.get("cnc", "motor_hold_enabled", default=True))

        form.addRow("Feed máx X (mm/min):", self.spin_f_x)
        form.addRow("Feed máx Y (mm/min):", self.spin_f_y)
        form.addRow("Feed máx Z (mm/min):", self.spin_f_z)
        form.addRow("Acel máx X (mm/s²):",  self.spin_a_x)
        form.addRow("Acel máx Y (mm/s²):",  self.spin_a_y)
        form.addRow("Acel máx Z (mm/s²):",  self.spin_a_z)
        form.addRow(self.chk_invert_y)
        form.addRow(self.chk_invert_z)
        form.addRow(self.chk_motor_hold)

        # --- NOVO BLOCO: seleção do tipo de sistema -----------------------
        self.combo_sys = QComboBox()
        self.combo_sys.addItems(["cartesian", "corexy"])
        self.combo_sys.setCurrentText(cfg.get("cnc", "system_type",
                                              default="cartesian"))
        form.addRow("Tipo de sistema:", self.combo_sys)

        # Grupo CoreXY (visível apenas quando selecionado)
        self.grp_corexy = QGroupBox("Opções CoreXY")
        g_core = QFormLayout(self.grp_corexy)
        self.chk_inv_a = QCheckBox("Inverter Motor A")
        self.chk_inv_b = QCheckBox("Inverter Motor B")
        core_cfg = cfg.get("cnc", "corexy_config", default={})
        self.chk_inv_a.setChecked(core_cfg.get("motor_a_invert", False))
        self.chk_inv_b.setChecked(core_cfg.get("motor_b_invert", False))
        g_core.addRow(self.chk_inv_a)
        g_core.addRow(self.chk_inv_b)
        form.addRow(self.grp_corexy)

        # Mostrar/esconder grupo conforme seleção inicial
        self.grp_corexy.setVisible(self.combo_sys.currentText() == "corexy")
        self.combo_sys.currentTextChanged.connect(
            lambda txt: self.grp_corexy.setVisible(txt == "corexy")
        )

        # ------ botões ----------
        btn_box = QHBoxLayout()
        btn_ok  = QPushButton("Salvar")
        btn_can = QPushButton("Cancelar")
        btn_ok.clicked.connect(self._on_save)
        btn_can.clicked.connect(self.reject)
        btn_box.addWidget(btn_ok); btn_box.addWidget(btn_can)
        form.addRow(btn_box)

    def _on_save(self):
        self.cfg.set("cnc", "max_feed", "x", value=self.spin_f_x.value())
        self.cfg.set("cnc", "max_feed", "y", value=self.spin_f_y.value())
        self.cfg.set("cnc", "max_acc",  "x", value=self.spin_a_x.value())
        self.cfg.set("cnc", "max_acc",  "y", value=self.spin_a_y.value())
        self.cfg.set("cnc", "max_feed", "z", value=self.spin_f_z.value())
        self.cfg.set("cnc", "max_acc",  "z", value=self.spin_a_z.value())
        self.cfg.set("cnc", "invert_y", value=self.chk_invert_y.isChecked())
        self.cfg.set("cnc", "invert_z", value=self.chk_invert_z.isChecked())
        self.cfg.set("cnc", "motor_hold_enabled", value=self.chk_motor_hold.isChecked())

        # -------- grava modo cartesiano/corexy ---------------------------
        sys_type = self.combo_sys.currentText()
        self.cfg.remember_system_type(sys_type)

        # -------- grava parâmetros CoreXY se aplicável -------------------
        if sys_type == "corexy":
            self.cfg.set("cnc", "corexy_config", "motor_a_invert",
                         value=self.chk_inv_a.isChecked())
            self.cfg.set("cnc", "corexy_config", "motor_b_invert",
                         value=self.chk_inv_b.isChecked())
        self.accept()
