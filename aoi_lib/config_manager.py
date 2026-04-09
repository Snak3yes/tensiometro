#config_manager.py

import os, json, logging, copy
from pathlib import Path
from aoi_lib.runtime_paths import get_runtime_path

# ------------------------------------------------------------
#  AOIConfigManager  –  gerencia arquivo JSON de preferências
# ------------------------------------------------------------
class AOIConfigManager:
    FIXED_Z_SPEED_MM_MIN = 5000.0
    _DEFAULT_CFG = {
        "cnc": {
            "system_type": "cartesian",          # cartesian  |  corexy
            "max_feed": {"x": 2500.0, "y": 2500.0, "z": 5000.0},   # + $112
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
            "plc_host": "192.168.1.5",  # IP padrão do PLC
            "plc_port": 502,            # Porta padrão Modbus TCP
            "auto_connect_cnc": True,
            "last_camera_id": 0,
            "last_camera_id": 0,
            "auto_connect_camera": True,
            "backlight_coil": 1       # Endereço coil backlight (padrão 1 = M1)
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
            "focus": 0,
            "auto_focus": True,
            "auto_exposure": True,
            "auto_white_balance": True,
            "presets": {},                # Perfis nomeados de configuração de câmera
            "calibration_file": "",       # Arquivo de calibração de distorção
            # Configurações da cruz de centralização
            "crosshair": {
                "color_r": 0,             # Componente R (0-255)
                "color_g": 0,             # Componente G (0-255)
                "color_b": 255,           # Componente B (0-255) - padrão vermelho
                "thickness": 2,           # Espessura da linha (px)
                "length_percent": 5       # Comprimento como % da menor dimensão (1-50)
            }
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
        },
        # ---------- CONFIGURAÇÕES DE AUTENTICAÇÃO -----------
        "authentication": {
            "require_login_on_startup": True,  # Exigir login ao iniciar aplicação
            "default_role": "operator"          # Papel padrão para auto-login (operator|engineering|quality|admin)
        },
        # ---------- CONFIGURAÇÕES DO ENGINEERING WIZARD -----------
        "engineering_wizard": {
            "free_navigation_enabled": False,  # Habilitar navegação livre (testing/debug)
            "last_used_mode": "normal"          # Rastrear último modo usado (normal|free)
        },
        # ---------- CONFIGURAÇÕES DE CRITÉRIOS DE TENSÃO -----------
        "tension_criteria": {
            "min_tension": 25.0,     # N/cm² mínimo aceitável (NOK abaixo deste)
            "max_tension": 45.0,     # N/cm² máximo aceitável (NOK acima deste)
            "warning_low": 28.0,     # N/cm² limite warning inferior
            "warning_high": 42.0     # N/cm² limite warning superior
        },
        # ---------- CONFIGURAÇÕES OPERACIONAIS DE TENSÃO -----------
        "tension": {
            "delay_medidor_ms": 500  # Tempo de estabilização após atingir Z de medição
        },
        "integration": {
            "enabled": True,
            "endpoint_url": "http://147.1.0.100:3075/sfcs-print/stencil/stencil_tensiometro",
            "timeout_sec": 10.0,
            "line_name": "IMC4-LM03",
            "user_id": 1,
            "stencil_status_id": None
        }
    }

    # ---- atalhos para gravação rápida -------
    def remember_cnc_port(self, port: str):
        self.set("connections", "last_cnc_port", value=port)
    def remember_camera_id(self, cam_id: int | str):
        # Tenta converter para int se possível, senão salva como string
        try:
            val = int(cam_id)
        except ValueError:
            val = str(cam_id)
        self.set("connections", "last_camera_id", value=val)
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
                                  gain: int = 128, focus: int = 0,
                                  auto_exp: bool = True, auto_wb: bool = True,
                                  auto_focus: bool = True):
        """Grava configurações de câmera."""
        self.set("camera", "mirror_x", value=mirror_x)
        self.set("camera", "mirror_y", value=mirror_y)
        self.set("camera", "brightness", value=brightness)
        self.set("camera", "contrast", value=contrast)
        self.set("camera", "saturation", value=saturation)
        self.set("camera", "exposure", value=exposure)
        self.set("camera", "gain", value=gain)
        self.set("camera", "focus", value=focus)
        self.set("camera", "auto_exposure", value=auto_exp)
        self.set("camera", "auto_white_balance", value=auto_wb)
        self.set("camera", "auto_focus", value=auto_focus)

    # -------- presets de câmera ---------------
    def save_camera_preset(self, name: str, data: dict):
        """Grava um preset de câmera nomeado."""
        presets = self.get("camera", "presets", default={})
        presets[name] = data
        self.set("camera", "presets", value=presets)

    def get_camera_preset(self, name: str) -> dict | None:
        presets = self.get("camera", "presets", default={})
        return presets.get(name)

    def list_camera_presets(self) -> list[str]:
        presets = self.get("camera", "presets", default={})
        return list(presets.keys())

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

    # -------- atalhos para configurações de autenticação ---------------
    def get_require_login_on_startup(self) -> bool:
        """
        Retorna se login é obrigatório ao iniciar aplicação.

        Returns:
            bool: True se login é obrigatório, False caso contrário.
                  Padrão: True
        """
        return self.get("authentication", "require_login_on_startup", default=True)

    def get_default_role(self) -> str:
        """
        Retorna o papel (role) padrão para auto-login.

        Returns:
            str: Papel padrão (operator|engineering|quality|admin).
                 Padrão: "operator"
        """
        return self.get("authentication", "default_role", default="operator")

    def set_require_login_on_startup(self, value: bool):
        """
        Define se login é obrigatório ao iniciar aplicação.

        Args:
            value: True para exigir login, False para permitir auto-login.
        """
        self.set("authentication", "require_login_on_startup", value=value)

    def set_default_role(self, role: str):
        """
        Define o papel (role) padrão para auto-login.

        Args:
            role: Papel padrão (operator|engineering|quality|admin).
        """
        self.set("authentication", "default_role", value=role)

    # -------- atalhos para configurações do Engineering Wizard ---------------
    def get_free_navigation_enabled(self) -> bool:
        """
        Retorna se navegação livre está habilitada no Engineering Wizard.

        Returns:
            bool: True se navegação livre está habilitada, False caso contrário.
                  Padrão: False
        """
        return self.get("engineering_wizard", "free_navigation_enabled", default=False)

    def set_free_navigation_enabled(self, value: bool):
        """
        Define se navegação livre está habilitada no Engineering Wizard.

        Args:
            value: True para habilitar navegação livre, False para desabilitar.
        """
        self.set("engineering_wizard", "free_navigation_enabled", value=value)

    def get_delay_medidor_ms(self) -> int:
        """
        Retorna o delay global do medidor em milissegundos.

        Returns:
            int: Delay de estabilização após o movimento para altura de medição.
                 Padrão: 500 ms
        """
        try:
            return max(0, int(self.get("tension", "delay_medidor_ms", default=500)))
        except (TypeError, ValueError):
            return 500

    def set_delay_medidor_ms(self, value: int):
        """
        Define o delay global do medidor em milissegundos.

        Args:
            value: Delay em milissegundos.
        """
        self.set("tension", "delay_medidor_ms", value=max(0, int(value)))

    def __init__(self, cfg_path: str | None = None):
        self.log = logging.getLogger("AOIConfig")
        # Se o caminho não for informado, grava ao lado do executável
        # Nota: Após reorganização (2026-01-07), config está em config/aoi_config.json
        default_path = get_runtime_path("config", "aoi_config.json")
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
                self.data = copy.deepcopy(self._DEFAULT_CFG)
        else:
            self.log.info("Arquivo de config inexistente – criando padrão em %s", self.cfg_path)
            self.data = copy.deepcopy(self._DEFAULT_CFG)
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
            cnc.max_feed['z'] = self.FIXED_Z_SPEED_MM_MIN
        
        # Aplica fator de conversão pulsos/mm
        ppr = self.get("calibration", "pulses_per_rev", default=1000)
        pitch = self.get("calibration", "fuso_pitch", default=10)
        if ppr > 0 and pitch > 0 and hasattr(cnc, 'pulses_per_mm'):
            cnc.pulses_per_mm = ppr / pitch
        elif hasattr(cnc, 'pulses_per_mm'):
            cnc.pulses_per_mm = 1.0
            self.log.warning(
                "Calibracao invalida ignorada ao aplicar no PLC: pulses_per_rev=%s, fuso_pitch=%s. "
                "Usando fallback pulses_per_mm=1.0",
                ppr,
                pitch,
            )
        
        # Aplica endereço do backlight
        bl_addr = self.get("connections", "backlight_coil", default=5)
        if hasattr(cnc, 'backlight_coil_address'):
            cnc.backlight_coil_address = bl_addr

        if hasattr(cnc, '_enforce_fixed_z_speed'):
            try:
                cnc._enforce_fixed_z_speed()
            except Exception as e:
                self.log.warning("Falha ao reaplicar velocidade fixa do eixo Z: %s", e)

        ppm_info = ppr / pitch if ppr > 0 and pitch > 0 else 'N/A'
        self.log.info(f"Configurações aplicadas ao PLC: max_feed={maxf}, pulses_per_mm={ppm_info}")


# ============================================================
#  SettingsDialog – UI PyQt6 para editar as preferências
# ============================================================
from PyQt6.QtWidgets import (QDialog, QFormLayout, QDoubleSpinBox,
                             QPushButton, QHBoxLayout, QVBoxLayout, QGroupBox,
                             QLabel, QTabWidget, QWidget)

class SettingsDialog(QDialog):
    def __init__(self, cfg: AOIConfigManager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preferências do Sistema")
        self.cfg = cfg
        self.setMinimumWidth(450)
        
        main_layout = QVBoxLayout(self)
        
        # Cria abas para organizar as configurações
        tabs = QTabWidget()
        main_layout.addWidget(tabs)

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
        self.spin_f_z.setValue(AOIConfigManager.FIXED_Z_SPEED_MM_MIN)
        self.spin_f_z.setEnabled(False)
        self.spin_f_z.setToolTip("Eixo Z fixo em 5000 mm/min.")
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
        self.spin_step.setRange(0.01, 1000)  # Permite passos desde 0.01mm
        self.spin_step.setDecimals(2)  # 2 casas decimais para precisão
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
        # Velocidades
        self.cfg.set("cnc", "max_feed", "x", value=self.spin_f_x.value())
        self.cfg.set("cnc", "max_feed", "y", value=self.spin_f_y.value())
        self.cfg.set("cnc", "max_feed", "z", value=AOIConfigManager.FIXED_Z_SPEED_MM_MIN)
        
        # Calibração
        self.cfg.set("calibration", "pulses_per_rev", value=self.spin_pulses_rev.value())
        self.cfg.set("calibration", "fuso_pitch", value=self.spin_fuso.value())
        
        # Interface
        self.cfg.set("movement", "step_size", value=self.spin_step.value())
        self.cfg.set("movement", "feed_rate", value=self.spin_feed.value())
        
        self.accept()
