#config_manager.py

import os, json, logging
from pathlib import Path

# ------------------------------------------------------------
#  AOIConfigManager  –  gerencia arquivo JSON de preferências
# ------------------------------------------------------------
class AOIConfigManager:
    _DEFAULT_CFG = {
        "cnc": {
            "max_feed": {"x": 2500.0, "y": 2500.0},   # $110 / $111   (mm/min)
            "max_acc":  {"x": 120.0,  "y": 120.0},    # $120 / $121   (mm/s²)
            "invert_y": True                          # sentido lógico (+Y frente)
        },
        "connections": {
            "last_cnc_port": "",
            "auto_connect_cnc": True,
            "last_camera_id": 0,
            "auto_connect_camera": True
        },
        "ui": {
            "theme": "light"
        },
        # ---------- NOVOS GRUPOS -----------
        "movement": {                     # controles manuais
            "step_size": 10.0,            # mm
            "feed_rate": 1000.0           # mm/min
        },
        "calibration": {                  # parâmetros mecânicos
            "pulses_per_rev": 400.0,
            "fuso_pitch": 5.0             # mm / volta
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
        if not cnc or not cnc.is_connected:
            return
        maxf = self.get("cnc", "max_feed")
        acc  = self.get("cnc", "max_acc")
        invert_y = self.get("cnc", "invert_y", default=True)
        cmds = [
            f"$110={maxf['x']}", f"$111={maxf['y']}",
            f"$120={acc['x']}",  f"$121={acc['y']}",
        ]
        for c in cmds:
            cnc.send_command(c, priority=True)
        cnc.set_invert_y(invert=invert_y)
        self.log.info("Limites aplicados ao GRBL: feed %s  acc %s  invert_y=%s",
                      maxf, acc, invert_y)

# ============================================================
#  SettingsDialog – UI PyQt6 para editar as preferências
# ============================================================
from PyQt6.QtWidgets import (QDialog, QFormLayout, QDoubleSpinBox, QCheckBox,
                             QPushButton, QHBoxLayout)

class SettingsDialog(QDialog):
    def __init__(self, cfg: AOIConfigManager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preferências da AOI / CNC")
        self.cfg = cfg
        form = QFormLayout(self)

        # ------ widgets para feed / acel -------
        self.spin_f_x = QDoubleSpinBox(); self.spin_f_x.setRange(1, 30000)
        self.spin_f_y = QDoubleSpinBox(); self.spin_f_y.setRange(1, 30000)
        self.spin_a_x = QDoubleSpinBox(); self.spin_a_x.setRange(1, 1000)
        self.spin_a_y = QDoubleSpinBox(); self.spin_a_y.setRange(1, 1000)
        self.chk_invert_y = QCheckBox("Inverter lógica do eixo Y (+Y frente)")

        # valores atuais
        self.spin_f_x.setValue(cfg.get("cnc", "max_feed", "x"))
        self.spin_f_y.setValue(cfg.get("cnc", "max_feed", "y"))
        self.spin_a_x.setValue(cfg.get("cnc", "max_acc", "x"))
        self.spin_a_y.setValue(cfg.get("cnc", "max_acc", "y"))
        self.chk_invert_y.setChecked(cfg.get("cnc", "invert_y"))

        form.addRow("Feed máx X (mm/min):", self.spin_f_x)
        form.addRow("Feed máx Y (mm/min):", self.spin_f_y)
        form.addRow("Acel máx X (mm/s²):",  self.spin_a_x)
        form.addRow("Acel máx Y (mm/s²):",  self.spin_a_y)
        form.addRow(self.chk_invert_y)

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
        self.cfg.set("cnc", "invert_y", value=self.chk_invert_y.isChecked())
        self.accept()
