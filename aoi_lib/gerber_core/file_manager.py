"""
Gerber File Manager

Module responsible for file I/O operations for Gerber files.
Extracted from mainwindow.py to follow Single Responsibility Principle.

Classes:
    GerberFileManager: Handles all file operations (import/export/render)
"""

import traceback
from typing import TYPE_CHECKING, Dict, List, Tuple
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QMessageBox, QInputDialog

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QWidget, QFileDialog
    from .parser import GerberObject
    from .config import GerberConfig
    from .apertures import ApertureInstance

from .config import parse_gerber_config
from .apertures import parse_add, parse_all_macros
from .parser import build_layer_objects_mm
from .exporter import objects_to_gerber
from .render import render_polys_to_image


class GerberFileManager(QObject):
    """
    Handles file I/O operations for Gerber files.

    Responsibilities:
    - Create new project
    - Import Gerber files
    - Export to Gerber/PNG/DXF formats
    - Render full layer
    - Manage file dialogs

    This class was extracted from GerberMacroViewer to follow SRP.
    """

    # Signals to notify main window of changes
    project_created = pyqtSignal(str)  # project_name
    file_loaded = pyqtSignal()
    layer_rendered = pyqtSignal()

    def __init__(
        self,
        preview_width: int = 2000,
        preview_height: int = 2000,
        parent: "QWidget" = None,
    ):
        """
        Initialize GerberFileManager.

        Args:
            preview_width: Width of preview image
            preview_height: Height of preview image
            parent: Parent window (for dialogs)
        """
        super().__init__(parent)
        self._preview_width = preview_width
        self._preview_height = preview_height
        self._parent_window = parent

        # Gerber data
        self.gerber_lines: List[str] | None = None
        self.gerber_cfg: "GerberConfig" | None = None
        self.macros = {}
        self.apertures_by_dcode: Dict[int, "ApertureInstance"] = {}

        # Layer data
        self._full_layer_polys_mm: List[List[tuple[float, float]]] | None = None
        self._full_layer_objects: List["GerberObject"] | None = None

    # ====================================================================== #
    # PROJECT MANAGEMENT
    # ====================================================================== #

    def new_project(self) -> str | None:
        """
        Create a new project.

        Returns:
            Project name if created, None otherwise

        Process:
            1. Clear current visualization/state
            2. Ask user for project name (required)
            3. Update status bar
        """
        # Clear current state
        self.clear_state()

        # Ask for project name
        name, ok = QInputDialog.getText(
            self._parent_window,
            "Novo projeto",
            "Informe o nome do novo projeto:",
        )
        if not ok:
            return None

        name = name.strip()
        if not name:
            QMessageBox.warning(
                self._parent_window,
                "Nome obrigatório",
                "É necessário informar um nome para o projeto.",
            )
            return None

        # Emit signal
        self.project_created.emit(name)
        return name

    def clear_state(self):
        """Clear all Gerber data."""
        self.gerber_lines = None
        self.gerber_cfg = None
        self.apertures_by_dcode = {}
        self.macros = {}
        self._full_layer_polys_mm = None
        self._full_layer_objects = None

    # ====================================================================== #
    # FILE IMPORT
    # ====================================================================== #

    def open_file(self, file_dialog_callback) -> bool:
        """
        Open a Gerber file.

        Args:
            file_dialog_callback: Function that returns (path, filter) from QFileDialog

        Returns:
            True if file was loaded successfully, False otherwise
        """
        path, _ = file_dialog_callback()
        if not path:
            return False

        # Clear state before loading
        self.clear_state()

        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except OSError as e:
            QMessageBox.critical(
                self._parent_window,
                "Erro ao abrir arquivo",
                f"Não foi possível abrir:\n{path}\n\n{e}",
            )
            return False

        # Parse Gerber file
        self.gerber_lines = lines
        self.gerber_cfg = parse_gerber_config(lines)
        self.apertures_by_dcode = parse_add(lines, self.gerber_cfg)
        self.macros = parse_all_macros(lines)

        # Emit signal
        self.file_loaded.emit()
        return True

    def import_gbr(self, file_dialog_callback) -> bool:
        """
        Import a Gerber file and render full layer.

        Args:
            file_dialog_callback: Function that returns (path, filter) from QFileDialog

        Returns:
            True if imported and rendered successfully, False otherwise
        """
        loaded = self.open_file(file_dialog_callback)
        if not loaded:
            return False

        return self.render_full_layer()

    # ====================================================================== #
    # LAYER RENDERING
    # ====================================================================== #

    def render_full_layer(self) -> bool:
        """
        Render the full Gerber layer.

        Returns:
            True if rendered successfully, False otherwise

        Process:
            1. Generate Gerber objects (flash/region) in mm
            2. Derive polygon list from objects
            3. Render preview
        """
        if self.gerber_lines is None or self.gerber_cfg is None:
            QMessageBox.information(
                self._parent_window,
                "Nenhum arquivo",
                "Abra um arquivo Gerber antes de gerar a camada completa.",
            )
            return False

        # Verificar se gerber_cfg tem os campos necessários
        print(f"[DEBUG] gerber_cfg: {self.gerber_cfg}")
        print(f"[DEBUG] gerber_cfg.format: {getattr(self.gerber_cfg, 'format', 'NOT_SET')}")

        if not hasattr(self.gerber_cfg, 'format') or self.gerber_cfg.format is None:
            QMessageBox.critical(
                self._parent_window,
                "Erro de configuração",
                "O arquivo Gerber não possui informações de formato (FS/FSA).\n"
                "Não é possível interpretar as coordenadas.",
            )
            return False

        try:
            # Generate Gerber objects (flash/region) in mm
            objects = build_layer_objects_mm(
                self.gerber_lines,
                self.macros,
                self.apertures_by_dcode,
                self.gerber_cfg,
            )
            self._full_layer_objects = objects

            # Derive polygon list from objects (for PNG, etc.)
            polys_mm: List[List[tuple[float, float]]] = [
                obj.polygon_mm for obj in objects
                if obj.polygon_mm and len(obj.polygon_mm) >= 3
            ]
            self._full_layer_polys_mm = polys_mm
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(
                self._parent_window,
                "Erro ao gerar camada completa",
                f"Ocorreu um erro ao processar a camada completa.\n\n"
                f"Erro: {e}\n\n"
                f"Veja o terminal para detalhes.",
            )
            return False

        if not polys_mm:
            QMessageBox.information(
                self._parent_window,
                "Nada para exibir",
                "Nenhuma entidade geométrica foi encontrada para a camada completa.",
            )
            return False

        # Validate rasterization
        try:
            _ = render_polys_to_image(
                polys_mm,
                img_size=(self._preview_width, self._preview_height),
                margin=20,
            )
        except Exception:
            traceback.print_exc()
            QMessageBox.critical(
                self._parent_window,
                "Erro ao renderizar imagem",
                "Falha ao rasterizar a camada completa.",
            )
            return False

        # Emit signal
        self.layer_rendered.emit()
        return True

    # ====================================================================== #
    # FILE EXPORT
    # ====================================================================== #

    def export_gbr(self, file_dialog_callback) -> bool:
        """
        Export current layer to Gerber file format.

        Args:
            file_dialog_callback: Function that returns (path, filter) from QFileDialog

        Returns:
            True if exported successfully, False otherwise

        Format: RS-274X simplified
          - Unit: millimeters (%MOMM*%)
          - Format: FSLAX33Y33 (3 integers, 3 decimals)
          - All objects converted to solid regions (G36/G37)
        """
        if not self._full_layer_objects:
            QMessageBox.information(
                self._parent_window,
                "Nada para exportar",
                "Não há nenhum objeto carregado/gerado para exportar.\n"
                "Crie um projeto, importe um Gerber e gere a camada completa.",
            )
            return False

        path, _ = file_dialog_callback()
        if not path:
            return False

        try:
            lines = objects_to_gerber(self._full_layer_objects)
            with open(path, "w", encoding="utf-8") as f:
                f.writelines(lines)
        except Exception:
            traceback.print_exc()
            QMessageBox.critical(
                self._parent_window,
                "Erro ao exportar Gerber",
                "Ocorreu um erro ao gerar o arquivo Gerber exportado.\n"
                "Veja o terminal para detalhes.",
            )
            return False

        return True

    def export_png(
        self,
        file_dialog_callback,
        aperture_color: QColor,
        background_color: QColor,
    ) -> bool:
        """
        Export current layer to PNG image.

        Args:
            file_dialog_callback: Function that returns (path, filter) from QFileDialog
            aperture_color: Color for apertures
            background_color: Background color

        Returns:
            True if exported successfully, False otherwise
        """
        if not self._full_layer_polys_mm:
            QMessageBox.information(
                self._parent_window,
                "Nada para exportar",
                "Não há nenhum dado de camada completa para exportar.\n"
                "Gere a camada completa primeiro.",
            )
            return False

        path, _ = file_dialog_callback()
        if not path:
            return False

        # Ask for scale factor
        factor, ok = QInputDialog.getInt(
            self._parent_window,
            "Escala da imagem",
            "Fator de escala (1 = igual ao preview, 2 = 2x, ...):",
            4,  # default
            1,  # minimum
            20,  # maximum
            1,  # step
        )
        if not ok:
            return False

        try:
            ac = aperture_color
            bc = background_color
            fill_rgb = (ac.red(), ac.green(), ac.blue())
            bg_rgb = (bc.red(), bc.green(), bc.blue())

            img = render_polys_to_image(
                self._full_layer_polys_mm,
                img_size=(
                    self._preview_width * factor,
                    self._preview_height * factor,
                ),
                margin=20 * factor,
                fill=fill_rgb,
                bg=bg_rgb,
            )
            img.save(path, format="PNG")
        except Exception:
            traceback.print_exc()
            QMessageBox.critical(
                self._parent_window,
                "Erro ao exportar PNG",
                "Ocorreu um erro ao gerar o PNG de alta resolução.\n"
                "Veja o terminal para detalhes.",
            )
            return False

        return True

    # ====================================================================== #
    # DATA ACCESS
    # ====================================================================== #

    @property
    def full_layer_objects(self) -> List["GerberObject"] | None:
        """Get full layer objects."""
        return self._full_layer_objects

    @property
    def full_layer_polys_mm(self) -> List[List[tuple[float, float]]] | None:
        """Get full layer polygons."""
        return self._full_layer_polys_mm

    @property
    def has_data(self) -> bool:
        """Check if any Gerber data is loaded."""
        return (
            self.gerber_lines is not None
            and self._full_layer_objects is not None
        )
