# settings_manager.py
import json, typing as _t
from pathlib import Path

class SettingsManager:
    _FILE = Path(__file__).with_name("settings.json")

    def __init__(self):
        self.data = {                       # defaults
            "table_limits": {
                "1": {"x": [0, 25000], "y": [0, 18000]},
                "2": {"x": [0, 25000], "y": [0, 18000]}
            },
            "camera_index": 0,
            "focus_calibration": {"a": 0.0, "b": 0.0},
            # ---------- steps/mm por eixo -----------------
            "axis_calibration": {
                "X":  1.0,
                "Y2": 1.0,
                "Y1": 1.0,
                "Z":  1.0
            },
            # ----------- homing virtual de cada mesa -----------
            "virtual_home": {
                "1": {"x": 0, "y": 0},
                "2": {"x": 0, "y": 0}
            },
            # ------- escala câmera (mm por pixel @ Z-ref = 0) --------
            "camera_mm_per_pixel": 0.05,
            "camera_fov": {               # NOVO – campo de visão
                "z0_z_pulses": 0,
                "z0_width_mm": 61.0,
                "z0_height_mm": 45.0,
                "z1_z_pulses": 700,
                "z1_width_mm": 30.5,
                "z1_height_mm": 22.5
            },
            # ------------   OFFSET CÂMERA  →  NOZZLE    ---------------
            # Guardado em PULSOS (mesma unidade dos motores).
            "camera_nozzle_offset": {"x": 0, "y": 0},

            # ------- NOVO: pasta-raiz dos projetos -----------------
            # será algo como  C:\QualquerLugar\Projetos
            "projects_dir": str((Path.home() / "Projetos").resolve())
        }
        self.load()

    # ----------------------------------------------------------
    def load(self):
        if self._FILE.exists():
            try:
                self.data.update(json.loads(self._FILE.read_text("utf-8")))
            except Exception:
                pass                       # mantém defaults

    def save(self):
        try:
            self._FILE.write_text(json.dumps(self.data, indent=2), encoding="utf-8")
        except Exception:
            pass

    # conveniência
    @property
    def table_limits(self) -> dict[int, dict[str, _t.Any]]:
        return {int(k): v for k, v in self.data["table_limits"].items()}

    @table_limits.setter
    def table_limits(self, v):
        self.data["table_limits"] = {str(k): v[k] for k in v}

    @property
    def camera_index(self) -> int:
        return int(self.data.get("camera_index", 0))

    @camera_index.setter
    def camera_index(self, idx: int):
        self.data["camera_index"] = int(idx)

    # ---------- foco ----------------------------------------------
    @property
    def focus_coeffs(self):
        d = self.data.get("focus_calibration", {"a":0.0,"b":0.0})
        return d.get("a",0.0), d.get("b",0.0)

    @focus_coeffs.setter
    def focus_coeffs(self, ab):
        self.data["focus_calibration"] = {"a":ab[0], "b":ab[1]}

    # ---------- steps/mm --------------------------------------------
    @property
    def axis_steps(self) -> dict[str,float]:
        return {k: float(v) for k,v in self.data.get("axis_calibration", {}).items()}
    @axis_steps.setter
    def axis_steps(self, d: dict[str,float]):
        self.data["axis_calibration"] = {k: float(v) for k,v in d.items()}

    # ----------- homing virtual -------------------------------------
    @property
    def virtual_home(self) -> dict[int, dict[str,int]]:
        vh = self.data.get("virtual_home", {"1":{"x":0,"y":0},"2":{"x":0,"y":0}})
        return {int(k): {"x":int(v["x"]), "y":int(v["y"])} for k,v in vh.items()}
    @virtual_home.setter
    def virtual_home(self, d: dict[int,dict[str,int]]):
        self.data["virtual_home"] = {str(k): {"x":int(v["x"]), "y":int(v["y"])}
                                     for k,v in d.items()}
        
    # ------------ câmera --------------------------------------------
    @property
    def camera_mm_per_pixel(self) -> float:
        return float(self.data.get("camera_mm_per_pixel", 0.05))
    @camera_mm_per_pixel.setter
    def camera_mm_per_pixel(self, v: float):
        self.data["camera_mm_per_pixel"] = float(v)
    # ---------- campo-de-visão --------------------------------------
    @property
    def camera_fov(self) -> dict:
        return self.data.get("camera_fov", {})
    @camera_fov.setter
    def camera_fov(self, d: dict):
        self.data["camera_fov"] = d

    # ------------ OFFSET CÂMERA↔NOZZLE ------------------------------
    @property
    def cam_noz_offset(self) -> dict[str, int]:
        off = self.data.get("camera_nozzle_offset", {"x": 0, "y": 0})
        return {"x": int(off.get("x", 0)), "y": int(off.get("y", 0))}

    @cam_noz_offset.setter
    def cam_noz_offset(self, off: dict[str, int]):
        self.data["camera_nozzle_offset"] = {"x": int(off["x"]), "y": int(off["y"])}

    # ------------ PASTA «PROJETOS» ----------------------------------
    @property
    def projects_dir(self) -> Path:
        return Path(self.data.get("projects_dir",
                                  str(Path.home() / "Projetos"))).resolve()

    @projects_dir.setter
    def projects_dir(self, p: Path | str):
        self.data["projects_dir"] = str(Path(p).resolve())
