"""
Map Program Manager - Manages map program CRUD operations.

Handles program persistence, validation, and folder structure management
for map generation programs. Extracted from map_controller.py.
"""

import json
import logging
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from aoi_lib.runtime_paths import get_runtime_path

logger = logging.getLogger(__name__)

# Default folder for map programs
MAP_PROGRAMS_FOLDER = get_runtime_path("map_programs")


@dataclass
class MapProgram:
    """
    Map program data model.

    Attributes:
        name: Program name
        path: Path to program directory
        created_at: Creation timestamp (ISO format)
        modified_at: Last modification timestamp (ISO format)
        capture_params: Capture parameters (origin, end, step_x, step_y)
        mosaic_params: Mosaic parameters (auto_build, margin, blend_size, capture_delay_ms)
        status: Status information (images_captured, mosaic_generated, last_capture_date)
    """
    name: str
    path: Path
    created_at: str
    modified_at: str
    capture_params: Dict[str, Any] = field(default_factory=dict)
    mosaic_params: Dict[str, Any] = field(default_factory=dict)
    status: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any], program_path: Path) -> 'MapProgram':
        """Create MapProgram from dictionary data."""
        return cls(
            name=data.get("name", program_path.name),
            path=program_path,
            created_at=data.get("created_at", ""),
            modified_at=data.get("modified_at", ""),
            capture_params=data.get("capture_params", {}),
            mosaic_params=data.get("mosaic_params", {}),
            status=data.get("status", {})
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert MapProgram to dictionary for JSON serialization."""
        return {
            "version": "1.0",
            "name": self.name,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
            "capture_params": self.capture_params,
            "mosaic_params": self.mosaic_params,
            "status": self.status
        }


class MapProgramManager:
    """
    Manager for map program CRUD operations.

    Handles program validation, folder structure, and persistence.
    """

    def __init__(self, base_folder: Optional[Path] = None):
        """
        Initialize MapProgramManager.

        Args:
            base_folder: Base folder for map programs (defaults to MAP_PROGRAMS_FOLDER)
        """
        self.base_folder = base_folder or MAP_PROGRAMS_FOLDER
        self.base_folder.mkdir(parents=True, exist_ok=True)

    def validate_program_data(self, program_name: str, base_folder: str,
                             origin: Optional[Dict], end: Optional[Dict],
                             step_x: float, step_y: float) -> tuple[bool, str]:
        """
        Validate program data before saving.

        Args:
            program_name: Name of the program
            base_folder: Base folder path
            origin: Origin coordinates dict {'x': float, 'y': float}
            end: End coordinates dict {'x': float, 'y': float}
            step_x: X step in mm
            step_y: Y step in mm

        Returns:
            Tuple of (is_valid: bool, error_message: str)
        """
        if not program_name:
            return False, "Informe um nome para o programa."

        if not base_folder:
            return False, "Informe a pasta de salvamento."

        if not origin or not end:
            return False, "Defina ambos os cantos (origem e limite)."

        if step_x <= 0 or step_y <= 0:
            return False, "Os passos devem ser maiores que zero."

        return True, ""

    def sanitize_program_name(self, program_name: str) -> Optional[str]:
        """
        Sanitize program name for safe folder usage.

        Args:
            program_name: Raw program name

        Returns:
            Sanitized name or None if invalid
        """
        safe_name = "".join(c for c in program_name if c.isalnum() or c in "._- ").strip()
        if not safe_name:
            return None
        return safe_name

    def create_program_structure(self, base_folder: str, program_name: str) -> tuple[bool, Path, Optional[str]]:
        """
        Create program folder structure.

        Args:
            base_folder: Base folder path
            program_name: Name of the program

        Returns:
            Tuple of (success: bool, program_folder: Path, error_message: Optional[str])
        """
        safe_name = self.sanitize_program_name(program_name)
        if not safe_name:
            return False, Path(""), "Nome do programa inválido para criar pasta."

        base_path = Path(base_folder)
        program_folder = base_path / safe_name
        images_folder = program_folder / "Imagens"

        try:
            images_folder.mkdir(parents=True, exist_ok=True)
            logger.info(f"Estrutura de pastas criada: {images_folder}")
            return True, program_folder, None
        except Exception as e:
            error_msg = f"Falha ao criar pasta: {e}"
            logger.error(error_msg)
            return False, Path(""), error_msg

    def save_config_file(self, program_folder: Path, config_data: Dict[str, Any]) -> bool:
        """
        Save configuration file to program folder.

        Args:
            program_folder: Path to program directory
            config_data: Configuration dictionary

        Returns:
            True if successful, False otherwise
        """
        config_file = program_folder / "config.json"

        try:
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Configuração salva: {config_file}")
            return True

        except Exception as e:
            logger.error(f"Falha ao salvar configuração: {e}")
            return False

    def load_config_file(self, program_path: Path) -> Optional[Dict[str, Any]]:
        """
        Load configuration file from program folder.

        Args:
            program_path: Path to program directory

        Returns:
            Configuration dictionary or None if error
        """
        config_file = program_path / "config.json"

        if not config_file.exists():
            logger.warning(f"Arquivo de configuração não encontrado: {config_file}")
            return None

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            return data

        except Exception as e:
            logger.error(f"Falha ao carregar configuração: {e}")
            return None

    def save_program(self, program_name: str, base_folder: str,
                    origin: Dict, end: Dict,
                    step_x: float, step_y: float,
                    auto_build: bool, margin: int, blend_size: int,
                    capture_delay_ms: int) -> tuple[bool, Optional[Path], Optional[str]]:
        """
        Save complete map program.

        Args:
            program_name: Name of the program
            base_folder: Base folder path
            origin: Origin coordinates {'x': float, 'y': float}
            end: End coordinates {'x': float, 'y': float}
            step_x: X step in mm
            step_y: Y step in mm
            auto_build: Auto-build mosaic flag
            margin: Mosaic margin in pixels
            blend_size: Mosaic blend size in pixels
            capture_delay_ms: Capture delay in milliseconds

        Returns:
            Tuple of (success: bool, program_path: Optional[Path], error_message: Optional[str])
        """
        # Validate
        is_valid, error_msg = self.validate_program_data(
            program_name, base_folder, origin, end, step_x, step_y
        )
        if not is_valid:
            return False, None, error_msg

        # Sanitize name
        safe_name = self.sanitize_program_name(program_name)
        if not safe_name:
            return False, None, "Nome de programa inválido."

        # Create folder structure
        success, program_folder, error_msg = self.create_program_structure(base_folder, program_name)
        if not success:
            return False, None, error_msg

        # Count existing images
        images_folder = program_folder / "Imagens"
        images_count = len(list(images_folder.glob("*.png")))

        # Build config data
        config_data = {
            "version": "1.0",
            "name": program_name,
            "created_at": datetime.now().isoformat(),
            "modified_at": datetime.now().isoformat(),
            "capture_params": {
                "origin": origin,
                "end": end,
                "step_x": step_x,
                "step_y": step_y
            },
            "mosaic_params": {
                "auto_build": auto_build,
                "margin": margin,
                "blend_size": blend_size,
                "capture_delay_ms": capture_delay_ms
            },
            "status": {
                "images_captured": images_count,
                "mosaic_generated": (program_folder / "mosaic.png").exists(),
                "last_capture_date": None
            }
        }

        # Save config
        if not self.save_config_file(program_folder, config_data):
            return False, None, "Falha ao salvar arquivo de configuração."

        logger.info(f"Programa salvo: {program_folder}")
        return True, program_folder, None

    def load_program(self, program_path: Path) -> Optional[MapProgram]:
        """
        Load map program from folder.

        Args:
            program_path: Path to program directory

        Returns:
            MapProgram object or None if error
        """
        config_data = self.load_config_file(program_path)
        if not config_data:
            return None

        try:
            return MapProgram.from_dict(config_data, program_path)
        except Exception as e:
            logger.error(f"Falha ao carregar programa: {e}")
            return None

    def delete_program(self, program_path: Path) -> tuple[bool, Optional[str]]:
        """
        Delete map program folder.

        Args:
            program_path: Path to program directory

        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        try:
            shutil.rmtree(program_path)
            logger.info(f"Programa excluído: {program_path}")
            return True, None
        except Exception as e:
            error_msg = f"Falha ao excluir programa: {e}"
            logger.error(error_msg)
            return False, error_msg

    def list_programs(self, base_folder: Optional[Path] = None) -> List[Dict[str, Any]]:
        """
        List all available programs in base folder.

        Args:
            base_folder: Optional base folder (defaults to self.base_folder)

        Returns:
            List of program info dicts with keys: name, path, dimension, date
        """
        base_dir = base_folder or self.base_folder
        programs = []

        # Ensure folder exists
        base_dir.mkdir(parents=True, exist_ok=True)

        # List all subfolders containing config.json
        for prog_dir in sorted(base_dir.iterdir()):
            if not prog_dir.is_dir():
                continue

            config_file = prog_dir / "config.json"
            if not config_file.exists():
                continue

            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Extract information
                name = data.get("name", prog_dir.name)
                capture = data.get("capture_params", {})
                origin = capture.get("origin", {})
                end = capture.get("end", {})

                # Calculate dimension
                if origin and end:
                    dx = abs(end.get("x", 0) - origin.get("x", 0))
                    dy = abs(end.get("y", 0) - origin.get("y", 0))
                    dimension = f"{dx:.0f}x{dy:.0f}mm"
                else:
                    dimension = "-"

                # Modification date
                mod_time = datetime.fromtimestamp(config_file.stat().st_mtime)
                date_str = mod_time.strftime("%Y-%m-%d %H:%M")

                programs.append({
                    "name": name,
                    "path": str(prog_dir),
                    "dimension": dimension,
                    "date": date_str
                })

            except Exception as e:
                logger.warning(f"Erro ao carregar programa {prog_dir}: {e}")

        return programs

    def refresh_programs(self, base_folder: Optional[Path] = None) -> List[Dict[str, Any]]:
        """
        Refresh and return list of available programs.

        Args:
            base_folder: Optional base folder (defaults to self.base_folder)

        Returns:
            List of program info dicts
        """
        return self.list_programs(base_folder)
