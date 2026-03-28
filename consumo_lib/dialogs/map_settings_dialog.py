"""
Map Settings Dialog - Dialog for map generation configuration.

Provides UI for:
- Saved programs list (left panel)
- Capture and mosaic settings (right panel)
- Corner definition and grid calculation
- Program save/load/delete operations

Extracted from map_controller.py for better separation of concerns.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, Callable

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QTreeWidget, QTreeWidgetItem,
    QFileDialog, QCheckBox, QSpinBox, QSplitter, QWidget
)

# Design System
from consumo_lib.ui import COLORS, TYPO
from consumo_lib.ui.widget_standards import StandardButton

# Add project root to path for imports
import sys
from pathlib import Path as _Path
_current_file = _Path(__file__).resolve()
_root_dir = _current_file.parent.parent.parent
if str(_root_dir) not in sys.path:
    sys.path.insert(0, str(_root_dir))

from aoi_lib import CNCAOIController

logger = logging.getLogger(__name__)

# Default folder for map programs
MAP_PROGRAMS_FOLDER = Path(__file__).parent.parent.parent / "map_programs"


class MapSettingsDialog(QDialog):
    """
    Dialog for map generation settings and program management.

    Signals:
        program_load_requested: Emitted when user clicks Load button (program_path: Path)
        program_delete_requested: Emitted when user clicks Delete button (program_path: Path)
        save_requested: Emitted when user clicks Save button
        folder_selected: Emitted when user selects folder (folder_path: str)
        step_changed: Emitted when step values change
        corner_define_requested: Emitted when user clicks corner definition (corner_type: str)
        generate_requested: Emitted when user clicks Generate button
    """

    program_load_requested = pyqtSignal(Path)
    program_delete_requested = pyqtSignal(Path)
    save_requested = pyqtSignal()
    folder_selected = pyqtSignal(str)
    step_changed = pyqtSignal()
    corner_define_requested = pyqtSignal(str)  # 'origin' or 'end'
    generate_requested = pyqtSignal()

    def __init__(self, parent=None):
        """
        Initialize MapSettingsDialog.

        Args:
            parent: Optional parent QWidget
        """
        super().__init__(parent)

        self.setWindowTitle("Definir Mapa")
        self.setMinimumWidth(900)
        self.setMinimumHeight(600)

        # Non-modal: allows operating main window
        self.setWindowModality(Qt.WindowModality.NonModal)

        # Always on top, with title and close button
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowStaysOnTopHint
        )

        # UI widgets
        self.map_programs_tree = None
        self.map_program_name_edit = None
        self.map_folder_edit = None
        self.map_step_x_edit = None
        self.map_step_y_edit = None
        self.chk_auto_mosaic = None
        self.spin_mosaic_margin = None
        self.spin_mosaic_blend = None
        self.spin_capture_delay = None

        # Info labels
        self.lbl_adjusted_step_x = None
        self.lbl_adjusted_step_y = None
        self.lbl_cols = None
        self.lbl_rows = None
        self.lbl_total_images = None
        self.lbl_area = None
        self.lbl_adjustment_status = None

        # Create UI
        self._create_dialog()

    def _create_dialog(self):
        """Create dialog layout and widgets."""
        # Main layout with splitter
        main_layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Create panels
        left_panel = self._create_left_panel()
        right_panel = self._create_right_panel()

        # Add to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([250, 650])  # Initial proportion

        main_layout.addWidget(splitter)

    def _create_left_panel(self) -> QWidget:
        """
        Create left panel with saved programs list.

        Returns:
            QWidget with programs list
        """
        programs_widget = QWidget()
        programs_layout = QVBoxLayout(programs_widget)
        programs_layout.setContentsMargins(0, 0, 0, 0)

        programs_group = QGroupBox("📁 Mapas Salvos")
        programs_group_layout = QVBoxLayout(programs_group)

        # TreeView of programs
        self.map_programs_tree = QTreeWidget()
        self.map_programs_tree.setHeaderLabels(["Nome", "Dimensão", "Data"])
        self.map_programs_tree.setColumnWidth(0, 150)
        self.map_programs_tree.setColumnWidth(1, 100)
        programs_group_layout.addWidget(self.map_programs_tree)

        # Management buttons
        btn_programs_layout = QHBoxLayout()

        btn_load_program = StandardButton("📂 Carregar")
        btn_load_program.clicked.connect(self._on_load_clicked)
        btn_programs_layout.addWidget(btn_load_program)

        btn_delete_program = StandardButton("🗑️ Excluir", variant="danger")
        btn_delete_program.clicked.connect(self._on_delete_clicked)
        btn_programs_layout.addWidget(btn_delete_program)

        btn_refresh_programs = StandardButton("🔄")
        btn_refresh_programs.setMaximumWidth(40)
        btn_refresh_programs.clicked.connect(self._on_refresh_clicked)
        btn_programs_layout.addWidget(btn_refresh_programs)

        programs_group_layout.addLayout(btn_programs_layout)
        programs_layout.addWidget(programs_group)

        return programs_widget

    def _create_right_panel(self) -> QWidget:
        """
        Create right panel with configuration options.

        Returns:
            QWidget with configuration controls
        """
        config_widget = QWidget()
        layout = QVBoxLayout(config_widget)
        layout.setContentsMargins(10, 0, 0, 0)

        # Program name
        h1 = QHBoxLayout()
        h1.addWidget(QLabel("Nome do Programa:"))
        self.map_program_name_edit = QLineEdit()
        h1.addWidget(self.map_program_name_edit)

        # Save program button
        btn_save_program = StandardButton("💾 Salvar", variant="primary")
        btn_save_program.clicked.connect(self.save_requested.emit)
        h1.addWidget(btn_save_program)
        layout.addLayout(h1)

        # Save folder (base for projects)
        h2 = QHBoxLayout()
        h2.addWidget(QLabel("Pasta de Salvamento:"))
        self.map_folder_edit = QLineEdit()
        self.map_folder_edit.setToolTip(
            "Pasta base onde serão criadas as subpastas dos programas.\n"
            "Estrutura: [Pasta]/[Nome do Programa]/Imagens/"
        )
        h2.addWidget(self.map_folder_edit)
        btn_browse = StandardButton("Buscar…")
        btn_browse.clicked.connect(self._on_folder_browse)
        h2.addWidget(btn_browse)
        layout.addLayout(h2)

        # X/Y steps
        h3 = QHBoxLayout()
        h3.addWidget(QLabel("Passo X (mm):"))
        self.map_step_x_edit = QLineEdit()
        self.map_step_x_edit.setText("10.0")
        h3.addWidget(self.map_step_x_edit)
        h3.addWidget(QLabel("Passo Y (mm):"))
        self.map_step_y_edit = QLineEdit()
        self.map_step_y_edit.setText("10.0")
        h3.addWidget(self.map_step_y_edit)
        layout.addLayout(h3)

        # Connect step changes
        self.map_step_x_edit.textChanged.connect(self.step_changed.emit)
        self.map_step_y_edit.textChanged.connect(self.step_changed.emit)

        # Add calculated info panel
        layout.addWidget(self._create_info_panel())

        # Add mosaic options
        layout.addWidget(self._create_mosaic_group())

        # Add capture settings
        layout.addWidget(self._create_capture_group())

        # Corner definition buttons
        btn_origin = StandardButton("Definir canto inferior esquerdo")
        btn_origin.clicked.connect(lambda: self.corner_define_requested.emit('origin'))
        layout.addWidget(btn_origin)

        btn_end = StandardButton("Definir canto superior direito")
        btn_end.clicked.connect(lambda: self.corner_define_requested.emit('end'))
        layout.addWidget(btn_end)

        # Generate map button
        btn_generate = StandardButton("🔧 Gerar Mapa de Imagens")
        btn_generate.setMinimumHeight(40)
        btn_generate.clicked.connect(self.generate_requested.emit)
        layout.addWidget(btn_generate)

        return config_widget

    def _create_info_panel(self) -> QGroupBox:
        """
        Create calculated info panel.

        Returns:
            QGroupBox with grid calculation info
        """
        info_group = QGroupBox("📊 Cálculo da Grade (ajuste automático)")
        info_layout = QVBoxLayout()

        info_grid = QHBoxLayout()
        info_grid.addWidget(QLabel("Passo X ajustado:"))
        self.lbl_adjusted_step_x = QLabel("--")
        self.lbl_adjusted_step_x.setStyleSheet(f"font-weight: bold; color: {COLORS.SECONDARY};")
        info_grid.addWidget(self.lbl_adjusted_step_x)
        info_grid.addWidget(QLabel("Passo Y ajustado:"))
        self.lbl_adjusted_step_y = QLabel("--")
        self.lbl_adjusted_step_y.setStyleSheet(f"font-weight: bold; color: {COLORS.SECONDARY};")
        info_grid.addWidget(self.lbl_adjusted_step_y)
        info_layout.addLayout(info_grid)

        info_grid2 = QHBoxLayout()
        info_grid2.addWidget(QLabel("Colunas:"))
        self.lbl_cols = QLabel("--")
        self.lbl_cols.setStyleSheet("font-weight: bold;")
        info_grid2.addWidget(self.lbl_cols)
        info_grid2.addWidget(QLabel("Linhas:"))
        self.lbl_rows = QLabel("--")
        self.lbl_rows.setStyleSheet("font-weight: bold;")
        info_grid2.addWidget(self.lbl_rows)
        info_layout.addLayout(info_grid2)

        info_grid3 = QHBoxLayout()
        info_grid3.addWidget(QLabel("Total de imagens:"))
        self.lbl_total_images = QLabel("--")
        self.lbl_total_images.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {COLORS.SUCCESS};")
        info_grid3.addWidget(self.lbl_total_images)
        info_grid3.addWidget(QLabel("Área (mm):"))
        self.lbl_area = QLabel("--")
        self.lbl_area.setStyleSheet("font-weight: bold;")
        info_grid3.addWidget(self.lbl_area)
        info_layout.addLayout(info_grid3)

        # Status message
        self.lbl_adjustment_status = QLabel("")
        self.lbl_adjustment_status.setWordWrap(True)
        self.lbl_adjustment_status.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; font-style: italic;")
        info_layout.addWidget(self.lbl_adjustment_status)

        info_group.setLayout(info_layout)
        return info_group

    def _create_mosaic_group(self) -> QGroupBox:
        """
        Create mosaic options group.

        Returns:
            QGroupBox with mosaic settings
        """
        mosaic_group = QGroupBox("Montagem de Mosaico")
        mosaic_layout = QVBoxLayout()

        # Checkbox for automatic assembly
        self.chk_auto_mosaic = QCheckBox("Montar mosaico automaticamente após captura")
        self.chk_auto_mosaic.setChecked(True)
        mosaic_layout.addWidget(self.chk_auto_mosaic)

        # Crop margin (to remove lens distortion)
        margin_row = QHBoxLayout()
        margin_row.addWidget(QLabel("Margem de corte (px):"))
        self.spin_mosaic_margin = QSpinBox()
        self.spin_mosaic_margin.setRange(0, 500)
        self.spin_mosaic_margin.setValue(50)
        self.spin_mosaic_margin.setToolTip("Pixels a remover de cada borda para eliminar distorção de lente")
        margin_row.addWidget(self.spin_mosaic_margin)
        mosaic_layout.addLayout(margin_row)

        # Blending at joints
        blend_row = QHBoxLayout()
        blend_row.addWidget(QLabel("Blending (px):"))
        self.spin_mosaic_blend = QSpinBox()
        self.spin_mosaic_blend.setRange(0, 100)
        self.spin_mosaic_blend.setValue(20)
        self.spin_mosaic_blend.setToolTip("Tamanho da zona de transição gradual entre tiles")
        blend_row.addWidget(self.spin_mosaic_blend)
        mosaic_layout.addLayout(blend_row)

        mosaic_group.setLayout(mosaic_layout)
        return mosaic_group

    def _create_capture_group(self) -> QGroupBox:
        """
        Create capture settings group.

        Returns:
            QGroupBox with capture settings
        """
        capture_group = QGroupBox("Configurações de Captura")
        capture_layout = QHBoxLayout(capture_group)

        capture_layout.addWidget(QLabel("Tempo de espera antes da captura (ms):"))
        self.spin_capture_delay = QSpinBox()
        self.spin_capture_delay.setRange(50, 5000)
        self.spin_capture_delay.setValue(200)
        self.spin_capture_delay.setSingleStep(50)
        self.spin_capture_delay.setToolTip(
            "Tempo de estabilização após movimento antes de capturar a imagem.\n"
            "Aumente se a câmera for lenta ou a imagem sair tremida."
        )
        capture_layout.addWidget(self.spin_capture_delay)
        capture_layout.addWidget(QLabel("ms"))
        capture_layout.addStretch()

        return capture_group

    def update_programs_list(self, programs: list):
        """
        Update programs list in TreeView.

        Args:
            programs: List of program info dicts with keys: name, dimension, date, path
        """
        self.map_programs_tree.clear()

        for prog in programs:
            item = QTreeWidgetItem([prog['name'], prog['dimension'], prog['date']])
            item.setData(0, Qt.ItemDataRole.UserRole, prog['path'])
            self.map_programs_tree.addTopLevelItem(item)

    def update_calculated_info(self, adjusted: Dict[str, Any]):
        """
        Update calculated info panel with adjusted step data.

        Args:
            adjusted: Dict with keys: step_x, step_y, cols, rows, total_images,
                     dx, dy, adjusted_x, adjusted_y
        """
        self.lbl_adjusted_step_x.setText(f"{adjusted['step_x']:.3f} mm")
        self.lbl_adjusted_step_y.setText(f"{adjusted['step_y']:.3f} mm")
        self.lbl_cols.setText(str(adjusted['cols']))
        self.lbl_rows.setText(str(adjusted['rows']))
        self.lbl_total_images.setText(str(adjusted['total_images']))
        self.lbl_area.setText(f"{adjusted['dx']:.1f} x {adjusted['dy']:.1f}")

        # Build status message
        messages = []
        step_x = float(self.map_step_x_edit.text() or "10.0")
        step_y = float(self.map_step_y_edit.text() or "10.0")

        if adjusted['adjusted_x']:
            delta_x = adjusted['step_x'] - step_x
            messages.append(f"Passo X ajustado de {step_x:.3f} → {adjusted['step_x']:.3f} mm ({'+' if delta_x > 0 else ''}{delta_x:.3f})")
        if adjusted['adjusted_y']:
            delta_y = adjusted['step_y'] - step_y
            messages.append(f"Passo Y ajustado de {step_y:.3f} → {adjusted['step_y']:.3f} mm ({'+' if delta_y > 0 else ''}{delta_y:.3f})")

        if messages:
            self.lbl_adjustment_status.setText("ℹ️ " + " | ".join(messages))
            self.lbl_adjustment_status.setStyleSheet(f"color: {COLORS.WARNING}; font-style: italic;")
        else:
            self.lbl_adjustment_status.setText("✅ Os passos dividem a área uniformemente.")
            self.lbl_adjustment_status.setStyleSheet(f"color: {COLORS.SUCCESS}; font-style: italic;")

    def update_field_values(self, program_name: str, base_folder: str,
                           step_x: float, step_y: float,
                           auto_build: bool, margin: int, blend_size: int,
                           capture_delay_ms: int):
        """
        Update field values from loaded program.

        Args:
            program_name: Program name
            base_folder: Base folder path
            step_x: X step in mm
            step_y: Y step in mm
            auto_build: Auto-build mosaic flag
            margin: Mosaic margin in pixels
            blend_size: Mosaic blend size in pixels
            capture_delay_ms: Capture delay in milliseconds
        """
        self.map_program_name_edit.setText(program_name)
        self.map_folder_edit.setText(base_folder)
        self.map_step_x_edit.setText(str(step_x))
        self.map_step_y_edit.setText(str(step_y))
        self.chk_auto_mosaic.setChecked(auto_build)
        self.spin_mosaic_margin.setValue(margin)
        self.spin_mosaic_blend.setValue(blend_size)
        self.spin_capture_delay.setValue(capture_delay_ms)

    def get_field_values(self) -> Dict[str, Any]:
        """
        Get current field values.

        Returns:
            Dict with current values: program_name, base_folder, step_x, step_y,
            auto_build, margin, blend_size, capture_delay_ms
        """
        try:
            step_x = float(self.map_step_x_edit.text() or "10.0")
            step_y = float(self.map_step_y_edit.text() or "10.0")
        except ValueError:
            step_x, step_y = 10.0, 10.0

        return {
            'program_name': self.map_program_name_edit.text().strip(),
            'base_folder': self.map_folder_edit.text().strip(),
            'step_x': step_x,
            'step_y': step_y,
            'auto_build': self.chk_auto_mosaic.isChecked(),
            'margin': self.spin_mosaic_margin.value(),
            'blend_size': self.spin_mosaic_blend.value(),
            'capture_delay_ms': self.spin_capture_delay.value()
        }

    def get_selected_program_path(self) -> Optional[Path]:
        """
        Get path of currently selected program.

        Returns:
            Path to selected program or None if no selection
        """
        current = self.map_programs_tree.currentItem()
        if not current:
            return None

        return Path(current.data(0, Qt.ItemDataRole.UserRole))

    def _on_load_clicked(self):
        """Handle Load button click."""
        path = self.get_selected_program_path()
        if path:
            self.program_load_requested.emit(path)

    def _on_delete_clicked(self):
        """Handle Delete button click."""
        path = self.get_selected_program_path()
        if path:
            self.program_delete_requested.emit(path)

    def _on_refresh_clicked(self):
        """Handle Refresh button click."""
        # Signal to parent to refresh list
        # Parent will call update_programs_list()
        pass

    def _on_folder_browse(self):
        """Handle folder browse button click."""
        folder = QFileDialog.getExistingDirectory(
            self, "Selecione pasta para salvar imagens"
        )
        if folder:
            self.map_folder_edit.setText(folder)
            self.folder_selected.emit(folder)
