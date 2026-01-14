"""
MapController - Handles map generation and program management.

Extracted from MainWindow.show_definir_mapa_dialog() and related methods.
Manages map program JSON files in MAP_PROGRAMS_FOLDER.
"""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QTreeWidget, QTreeWidgetItem,
    QFileDialog, QMessageBox, QProgressDialog, QApplication,
    QCheckBox, QSpinBox, QSplitter
)

# Add project root to path for imports
import sys
from pathlib import Path as _Path
_current_file = _Path(__file__).resolve()
_root_dir = _current_file.parent.parent.parent
if str(_root_dir) not in sys.path:
    sys.path.insert(0, str(_root_dir))

from aoi_lib import CNCAOIController
from consumo_lib.utils.map_params import MapParams
from consumo_lib.threads.map_generator import MapGeneratorThread
from consumo_lib.widgets.preview_suspender import _PreviewSuspender

logger = logging.getLogger("consumo_lib")

# Import compose_mosaic_from_folder com fallback
try:
    from tools.mosaic_builder import compose_mosaic_from_folder
except ImportError:
    # Fallback para importação legada (já que root está no sys.path)
    try:
        from mosaic_builder import compose_mosaic_from_folder
    except ImportError:
        compose_mosaic_from_folder = None
        logger.warning("mosaic_builder.py não encontrado - funcionalidade de mosaico desabilitada")

# Default folder for map programs
MAP_PROGRAMS_FOLDER = Path(__file__).parent.parent / "map_programs"


class MapController(QObject):
    """
    Controller for map generation and program management.

    Signals:
        program_saved: Emitted when a program is saved (program_name, program_path)
        program_loaded: Emitted when a program is loaded (program_name, params)
        program_deleted: Emitted when a program is deleted (program_name)
        map_generated: Emitted when map generation completes (image_count, folder)
        map_progress: Emitted during map generation (done, total)
        map_error: Emitted on map generation error (error_message)
    """

    program_saved = pyqtSignal(str, Path)  # program_name, program_path
    program_loaded = pyqtSignal(str, dict)  # program_name, params
    program_deleted = pyqtSignal(str)  # program_name
    map_generated = pyqtSignal(int, str)  # image_count, folder
    map_progress = pyqtSignal(int, int)  # done, total
    map_error = pyqtSignal(str)  # error_message

    def __init__(self, controller, config_manager, parent=None):
        """
        Initialize MapController.

        Args:
            controller: CNCAOIController instance
            config_manager: AOIConfigManager instance
            parent: Optional parent QObject
        """
        super().__init__(parent)
        self.controller = controller
        self.config = config_manager

        # Runtime state
        self.map_origin = None
        self.map_end = None
        self.map_thread = None
        self.map_progress_dialog = None  # QProgressDialog (não confundir com signal map_progress)

        # UI widgets (filled by show_dialog)
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

    def show_dialog(self, parent_widget, camera_preview):
        """
        Show the map definition dialog (modeless, always on top).

        Args:
            parent_widget: Parent QWidget (usually MainWindow)
            camera_preview: CameraPreviewWidget instance

        Returns:
            QDialog instance
        """
        # 1) Create dialog without invalid flags
        dialog = QDialog(parent_widget)
        dialog.setWindowTitle("Definir Mapa")
        dialog.setMinimumWidth(900)
        dialog.setMinimumHeight(600)

        # 2) Non-modal: allows operating main window
        dialog.setWindowModality(Qt.WindowModality.NonModal)

        # 3) Always on top, with title and close button
        dialog.setWindowFlags(
            dialog.windowFlags()
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowStaysOnTopHint
        )

        # Main layout with splitter
        main_layout = QHBoxLayout(dialog)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ================== LEFT PANEL: SAVED PROGRAMS ==================
        programs_widget = QWidget()
        programs_layout = QVBoxLayout(programs_widget)
        programs_layout.setContentsMargins(0, 0, 0, 0)

        programs_group = QGroupBox("📁 Programas Salvos")
        programs_group_layout = QVBoxLayout(programs_group)

        # TreeView of programs
        self.map_programs_tree = QTreeWidget()
        self.map_programs_tree.setHeaderLabels(["Nome", "Dimensão", "Data"])
        self.map_programs_tree.setColumnWidth(0, 150)
        self.map_programs_tree.setColumnWidth(1, 100)
        self.map_programs_tree.itemDoubleClicked.connect(
            lambda item: self._load_map_program(Path(item.data(0, Qt.ItemDataRole.UserRole))) if item else None
        )
        programs_group_layout.addWidget(self.map_programs_tree)

        # Management buttons
        btn_programs_layout = QHBoxLayout()

        btn_load_program = QPushButton("📂 Carregar")
        btn_load_program.clicked.connect(lambda: self._on_load_map_program_clicked())
        btn_programs_layout.addWidget(btn_load_program)

        btn_delete_program = QPushButton("🗑️ Excluir")
        btn_delete_program.clicked.connect(lambda: self._delete_map_program())
        btn_programs_layout.addWidget(btn_delete_program)

        btn_refresh_programs = QPushButton("🔄")
        btn_refresh_programs.setMaximumWidth(40)
        btn_refresh_programs.clicked.connect(lambda: self._refresh_map_programs())
        btn_programs_layout.addWidget(btn_refresh_programs)

        programs_group_layout.addLayout(btn_programs_layout)
        programs_layout.addWidget(programs_group)

        # ================== RIGHT PANEL: CONFIGURATION ==================
        config_widget = QWidget()
        layout = QVBoxLayout(config_widget)
        layout.setContentsMargins(10, 0, 0, 0)

        # Program name
        h1 = QHBoxLayout()
        h1.addWidget(QLabel("Nome do Programa:"))
        self.map_program_name_edit = QLineEdit()
        # Load last used program name
        last_program = self.config.get("mosaic", "last_program_name", default="")
        self.map_program_name_edit.setText(last_program)
        h1.addWidget(self.map_program_name_edit)

        # Save program button
        btn_save_program = QPushButton("💾 Salvar")
        btn_save_program.clicked.connect(lambda: self._save_map_program())
        h1.addWidget(btn_save_program)
        layout.addLayout(h1)

        # Save folder (base for projects) - now uses MAP_PROGRAMS_FOLDER
        h2 = QHBoxLayout()
        h2.addWidget(QLabel("Pasta de Salvamento:"))
        self.map_folder_edit = QLineEdit()
        # Uses map_programs as default folder
        default_folder = str(MAP_PROGRAMS_FOLDER)
        last_folder = self.config.get("mosaic", "last_folder", default=default_folder)
        self.map_folder_edit.setText(last_folder)
        self.map_folder_edit.setToolTip(
            "Pasta base onde serão criadas as subpastas dos programas.\n"
            "Estrutura: [Pasta]/[Nome do Programa]/Imagens/"
        )
        h2.addWidget(self.map_folder_edit)
        btn_browse = QPushButton("Buscar…")
        btn_browse.clicked.connect(self._select_map_folder)
        h2.addWidget(btn_browse)
        layout.addLayout(h2)

        # X/Y steps
        h3 = QHBoxLayout()
        h3.addWidget(QLabel("Passo X (mm):"))
        self.map_step_x_edit = QLineEdit()
        # Load saved values
        saved_step_x = self.config.get("map", "step_x", default=10.0)
        self.map_step_x_edit.setText(str(saved_step_x))
        h3.addWidget(self.map_step_x_edit)
        h3.addWidget(QLabel("Passo Y (mm):"))
        self.map_step_y_edit = QLineEdit()
        saved_step_y = self.config.get("map", "step_y", default=10.0)
        self.map_step_y_edit.setText(str(saved_step_y))
        h3.addWidget(self.map_step_y_edit)
        layout.addLayout(h3)

        # ============== CALCULATED INFO PANEL ==============
        info_group = QGroupBox("📊 Cálculo da Grade (ajuste automático)")
        info_layout = QVBoxLayout()
        info_layout.setProperty("layout", "grid")  # Mark for grid layout conversion

        info_grid = QHBoxLayout()  # Simplified - using horizontal layout
        info_grid.addWidget(QLabel("Passo X ajustado:"))
        self.lbl_adjusted_step_x = QLabel("--")
        self.lbl_adjusted_step_x.setStyleSheet("font-weight: bold; color: #2196F3;")
        info_grid.addWidget(self.lbl_adjusted_step_x)
        info_grid.addWidget(QLabel("Passo Y ajustado:"))
        self.lbl_adjusted_step_y = QLabel("--")
        self.lbl_adjusted_step_y.setStyleSheet("font-weight: bold; color: #2196F3;")
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
        self.lbl_total_images.setStyleSheet("font-weight: bold; font-size: 14px; color: #4CAF50;")
        info_grid3.addWidget(self.lbl_total_images)
        info_grid3.addWidget(QLabel("Área (mm):"))
        self.lbl_area = QLabel("--")
        self.lbl_area.setStyleSheet("font-weight: bold;")
        info_grid3.addWidget(self.lbl_area)
        info_layout.addLayout(info_grid3)

        # Status message
        self.lbl_adjustment_status = QLabel("")
        self.lbl_adjustment_status.setWordWrap(True)
        self.lbl_adjustment_status.setStyleSheet("color: #666; font-style: italic;")
        info_layout.addWidget(self.lbl_adjustment_status)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # Connect events for dynamic update
        self.map_step_x_edit.textChanged.connect(lambda: self._update_adjusted_step_info())
        self.map_step_y_edit.textChanged.connect(lambda: self._update_adjusted_step_info())

        # Update initial info
        self._update_adjusted_step_info()

        # ============== MOSAIC OPTIONS ==============
        mosaic_group = QGroupBox("Montagem de Mosaico")
        mosaic_layout = QVBoxLayout()

        # Checkbox for automatic assembly
        self.chk_auto_mosaic = QCheckBox("Montar mosaico automaticamente após captura")
        saved_auto_build = self.config.get("mosaic", "auto_build", default=True)
        self.chk_auto_mosaic.setChecked(saved_auto_build)
        mosaic_layout.addWidget(self.chk_auto_mosaic)

        # Crop margin (to remove lens distortion)
        margin_row = QHBoxLayout()
        margin_row.addWidget(QLabel("Margem de corte (px):"))
        self.spin_mosaic_margin = QSpinBox()
        self.spin_mosaic_margin.setRange(0, 500)
        saved_margin = self.config.get("mosaic", "margin", default=50)
        self.spin_mosaic_margin.setValue(saved_margin)
        self.spin_mosaic_margin.setToolTip("Pixels a remover de cada borda para eliminar distorção de lente")
        margin_row.addWidget(self.spin_mosaic_margin)
        mosaic_layout.addLayout(margin_row)

        # Blending at joints
        blend_row = QHBoxLayout()
        blend_row.addWidget(QLabel("Blending (px):"))
        self.spin_mosaic_blend = QSpinBox()
        self.spin_mosaic_blend.setRange(0, 100)
        saved_blend = self.config.get("mosaic", "blend_size", default=20)
        self.spin_mosaic_blend.setValue(saved_blend)
        self.spin_mosaic_blend.setToolTip("Tamanho da zona de transição gradual entre tiles")
        blend_row.addWidget(self.spin_mosaic_blend)
        mosaic_layout.addLayout(blend_row)

        mosaic_group.setLayout(mosaic_layout)
        layout.addWidget(mosaic_group)
        # ============== END MOSAIC OPTIONS ==============

        # ============== CAPTURE DELAY ==============
        capture_group = QGroupBox("Configurações de Captura")
        capture_layout = QHBoxLayout(capture_group)

        capture_layout.addWidget(QLabel("Tempo de espera antes da captura (ms):"))
        self.spin_capture_delay = QSpinBox()
        self.spin_capture_delay.setRange(50, 5000)
        saved_delay = self.config.get("mosaic", "capture_delay_ms", default=200)
        self.spin_capture_delay.setValue(saved_delay)
        self.spin_capture_delay.setSingleStep(50)
        self.spin_capture_delay.setToolTip(
            "Tempo de estabilização após movimento antes de capturar a imagem.\n"
            "Aumente se a câmera for lenta ou a imagem sair tremida."
        )
        capture_layout.addWidget(self.spin_capture_delay)
        capture_layout.addWidget(QLabel("ms"))
        capture_layout.addStretch()

        layout.addWidget(capture_group)
        # ============== END CAPTURE SETTINGS ==============

        # Corner definition buttons
        btn_origin = QPushButton("Definir canto inferior esquerdo")
        btn_origin.clicked.connect(lambda: self._define_map_corner('origin', parent_widget))
        layout.addWidget(btn_origin)

        btn_end = QPushButton("Definir canto superior direito")
        btn_end.clicked.connect(lambda: self._define_map_corner('end', parent_widget))
        layout.addWidget(btn_end)

        # Generate map button
        btn_generate = QPushButton("🔧 Gerar Mapa de Imagens")
        btn_generate.setMinimumHeight(40)
        btn_generate.clicked.connect(lambda: self._on_generate_map(dialog, camera_preview))
        layout.addWidget(btn_generate)

        # ================== ASSEMBLE SPLITTER ==================
        splitter.addWidget(programs_widget)
        splitter.addWidget(config_widget)
        splitter.setSizes([250, 650])  # Initial proportion
        main_layout.addWidget(splitter)

        # Update program list
        self._refresh_map_programs()

        dialog.show()  # modeless, doesn't block main window

        return dialog

    def _select_map_folder(self):
        """Open folder selection dialog"""
        folder = QFileDialog.getExistingDirectory(None, "Selecione pasta para salvar imagens")
        if folder:
            self.map_folder_edit.setText(folder)

    def _define_map_corner(self, which, status_target):
        """
        Define map corner (origin or end) from current CNC position.

        Args:
            which: 'origin' or 'end'
            status_target: Widget with statusBar() method (usually MainWindow)
        """
        pos = self.controller.cnc.get_current_position()
        if which == 'origin':
            self.map_origin = {'x': pos['x'], 'y': pos['y']}
            # Uses statusBar instead of MessageBox to avoid blocking
            # (dialog is WindowStaysOnTopHint)
            status_target.statusBar().showMessage(
                f"✅ Origem definida: X={pos['x']:.3f}, Y={pos['y']:.3f}"
            )
        else:
            self.map_end = {'x': pos['x'], 'y': pos['y']}
            status_target.statusBar().showMessage(
                f"✅ Limite definido: X={pos['x']:.3f}, Y={pos['y']:.3f}"
            )

        # Update calculated info panel
        self._update_adjusted_step_info()

    def _update_adjusted_step_info(self):
        """
        Update info panel with calculated adjusted steps.
        Called when user changes steps or defines corners.
        """
        # Check if labels exist
        if not hasattr(self, 'lbl_adjusted_step_x'):
            return

        # Get origin and end
        origin = getattr(self, 'map_origin', None)
        end = getattr(self, 'map_end', None)

        if not origin or not end:
            self.lbl_adjusted_step_x.setText("--")
            self.lbl_adjusted_step_y.setText("--")
            self.lbl_cols.setText("--")
            self.lbl_rows.setText("--")
            self.lbl_total_images.setText("--")
            self.lbl_area.setText("--")
            self.lbl_adjustment_status.setText("⚠️ Defina os cantos (origem e limite) para calcular a grade.")
            return

        # Try to read steps
        try:
            step_x = float(self.map_step_x_edit.text())
            step_y = float(self.map_step_y_edit.text())
        except ValueError:
            self.lbl_adjustment_status.setText("⚠️ Passos X/Y inválidos.")
            return

        if step_x <= 0 or step_y <= 0:
            self.lbl_adjustment_status.setText("⚠️ Os passos devem ser maiores que zero.")
            return

        # Calculate adjustments
        try:
            adjusted = CNCAOIController.calculate_adjusted_steps(origin, end, step_x, step_y)

            # Update labels
            self.lbl_adjusted_step_x.setText(f"{adjusted['step_x']:.3f} mm")
            self.lbl_adjusted_step_y.setText(f"{adjusted['step_y']:.3f} mm")
            self.lbl_cols.setText(str(adjusted['cols']))
            self.lbl_rows.setText(str(adjusted['rows']))
            self.lbl_total_images.setText(str(adjusted['total_images']))
            self.lbl_area.setText(f"{adjusted['dx']:.1f} x {adjusted['dy']:.1f}")

            # Build status message
            messages = []
            if adjusted['adjusted_x']:
                delta_x = adjusted['step_x'] - step_x
                messages.append(f"Passo X ajustado de {step_x:.3f} → {adjusted['step_x']:.3f} mm ({'+' if delta_x > 0 else ''}{delta_x:.3f})")
            if adjusted['adjusted_y']:
                delta_y = adjusted['step_y'] - step_y
                messages.append(f"Passo Y ajustado de {step_y:.3f} → {adjusted['step_y']:.3f} mm ({'+' if delta_y > 0 else ''}{delta_y:.3f})")

            if messages:
                self.lbl_adjustment_status.setText("ℹ️ " + " | ".join(messages))
                self.lbl_adjustment_status.setStyleSheet("color: #FF9800; font-style: italic;")
            else:
                self.lbl_adjustment_status.setText("✅ Os passos dividem a área uniformemente.")
                self.lbl_adjustment_status.setStyleSheet("color: #4CAF50; font-style: italic;")

        except ValueError as e:
            self.lbl_adjustment_status.setText(f"⚠️ {str(e)}")
            self.lbl_adjustment_status.setStyleSheet("color: #F44336; font-style: italic;")
        except Exception as e:
            logger.warning(f"Erro ao calcular passos ajustados: {e}")
            self.lbl_adjustment_status.setText(f"⚠️ Erro no cálculo: {e}")

    # ================== MAP PROGRAM MANAGEMENT ==================

    def _refresh_map_programs(self, base_folder: Optional[Path] = None):
        """
        Update saved programs list in TreeView without blocking UI.

        Args:
            base_folder: Optional base folder path (defaults to map_folder_edit)
        """
        if not hasattr(self, 'map_programs_tree'):
            return

        base_dir = Path(base_folder) if base_folder else Path(self.map_folder_edit.text() or MAP_PROGRAMS_FOLDER)

        self.map_programs_tree.clear()

        # Ensure folder exists
        base_dir.mkdir(parents=True, exist_ok=True)

        # List all subfolders containing config.json
        for idx, prog_dir in enumerate(sorted(base_dir.iterdir())):
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

                # Add to tree
                item = QTreeWidgetItem([name, dimension, date_str])
                item.setData(0, Qt.ItemDataRole.UserRole, str(prog_dir))
                self.map_programs_tree.addTopLevelItem(item)

                # Process events periodically to keep UI responsive
                if idx % 20 == 0:
                    QApplication.processEvents()

            except Exception as e:
                logger.warning(f"Erro ao carregar programa {prog_dir}: {e}")

    def _save_map_program(self):
        """Save current program with its configurations"""
        prog_name = self.map_program_name_edit.text().strip()
        if not prog_name:
            QMessageBox.warning(None, "Erro", "Informe um nome para o programa.")
            return

        # Sanitize name
        safe_name = "".join(c for c in prog_name if c.isalnum() or c in "._- ").strip()
        if not safe_name:
            QMessageBox.warning(None, "Erro", "Nome de programa inválido.")
            return

        # Create program folder
        base_folder = Path(self.map_folder_edit.text().strip() or str(MAP_PROGRAMS_FOLDER))
        program_folder = base_folder / safe_name
        images_folder = program_folder / "Imagens"

        try:
            images_folder.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            QMessageBox.critical(None, "Erro", f"Falha ao criar pasta:\n{e}")
            return

        # Collect data
        origin = getattr(self, 'map_origin', None)
        end = getattr(self, 'map_end', None)

        try:
            step_x = float(self.map_step_x_edit.text())
            step_y = float(self.map_step_y_edit.text())
        except ValueError:
            step_x, step_y = 10.0, 10.0

        config_data = {
            "version": "1.0",
            "name": prog_name,
            "created_at": datetime.now().isoformat(),
            "modified_at": datetime.now().isoformat(),
            "capture_params": {
                "origin": origin if origin else {"x": 0, "y": 0},
                "end": end if end else {"x": 0, "y": 0},
                "step_x": step_x,
                "step_y": step_y
            },
            "mosaic_params": {
                "auto_build": self.chk_auto_mosaic.isChecked(),
                "margin": self.spin_mosaic_margin.value(),
                "blend_size": self.spin_mosaic_blend.value(),
                "capture_delay_ms": self.spin_capture_delay.value()
            },
            "status": {
                "images_captured": len(list(images_folder.glob("*.png"))),
                "mosaic_generated": (program_folder / "mosaic.png").exists(),
                "last_capture_date": None
            }
        }

        # Save config.json
        config_file = program_folder / "config.json"
        try:
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Programa salvo: {config_file}")

            # Update TreeView using saved program's folder
            self._refresh_map_programs(base_folder=program_folder.parent)

            # Emit signal
            self.program_saved.emit(prog_name, program_folder)

        except Exception as e:
            QMessageBox.critical(None, "Erro", f"Falha ao salvar programa:\n{e}")

    def _on_load_map_program_clicked(self):
        """Callback for Load button - loads program selected in TreeView"""
        if not hasattr(self, 'map_programs_tree'):
            return

        current = self.map_programs_tree.currentItem()
        if not current:
            QMessageBox.warning(None, "Seleção", "Selecione um programa na lista.")
            return

        program_path = Path(current.data(0, Qt.ItemDataRole.UserRole))
        self._load_map_program(program_path)

    def _load_map_program(self, program_path: Path):
        """
        Load a program from its directory.

        Args:
            program_path: Path to program directory
        """
        config_file = program_path / "config.json"

        if not config_file.exists():
            QMessageBox.warning(None, "Erro", f"Arquivo de configuração não encontrado:\n{config_file}")
            return

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Fill fields
            name = data.get("name", program_path.name)
            self.map_program_name_edit.setText(name)

            # Base folder
            self.map_folder_edit.setText(str(program_path.parent))

            # Capture parameters
            capture = data.get("capture_params", {})
            self.map_step_x_edit.setText(str(capture.get("step_x", 10.0)))
            self.map_step_y_edit.setText(str(capture.get("step_y", 10.0)))

            # Define origin/end
            origin = capture.get("origin", {})
            end = capture.get("end", {})
            if origin.get("x") is not None and origin.get("y") is not None:
                self.map_origin = origin
            if end.get("x") is not None and end.get("y") is not None:
                self.map_end = end

            # Mosaic parameters
            mosaic = data.get("mosaic_params", {})
            self.chk_auto_mosaic.setChecked(mosaic.get("auto_build", True))
            self.spin_mosaic_margin.setValue(mosaic.get("margin", 50))
            self.spin_mosaic_blend.setValue(mosaic.get("blend_size", 20))
            self.spin_capture_delay.setValue(mosaic.get("capture_delay_ms", 200))

            # Update calculated info panel
            self._update_adjusted_step_info()

            logger.info(f"Programa carregado: {program_path}")

            # Emit signal with params
            self.program_loaded.emit(name, data)

        except Exception as e:
            QMessageBox.critical(None, "Erro", f"Falha ao carregar programa:\n{e}")

    def _delete_map_program(self):
        """Delete selected program"""
        if not hasattr(self, 'map_programs_tree'):
            return

        current = self.map_programs_tree.currentItem()
        if not current:
            QMessageBox.warning(None, "Seleção", "Selecione um programa para excluir.")
            return

        program_path = Path(current.data(0, Qt.ItemDataRole.UserRole))
        program_name = current.text(0)

        # Confirm deletion
        reply = QMessageBox.question(
            None, "Confirmar Exclusão",
            f"Deseja excluir o programa '{program_name}'?\n\n"
            f"Pasta: {program_path}\n\n"
            "Esta ação removerá a pasta e todo seu conteúdo (imagens, mosaico, etc.)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            shutil.rmtree(program_path)

            logger.info(f"Programa excluído: {program_path}")

            # Update TreeView in same folder
            self._refresh_map_programs(base_folder=program_path.parent)

            # Emit signal
            self.program_deleted.emit(program_name)

        except Exception as e:
            QMessageBox.critical(None, "Erro", f"Falha ao excluir programa:\n{e}")

    def _on_generate_map(self, dialog, camera_preview):
        """
        Start map generation process.

        Args:
            dialog: Map definition dialog
            camera_preview: CameraPreviewWidget instance
        """
        # Check CNC connection - blocks ONLY generation, not dialog
        if not self.controller.cnc.is_connected:
            QMessageBox.warning(
                dialog, "CNC Não Conectado",
                "A geração do mapa requer conexão com o CLP para movimentar a máquina.\n\n"
                "Você pode:\n"
                "• Conectar o CLP e tentar novamente\n"
                "• Configurar e salvar os parâmetros na receita para uso posterior\n\n"
                "As demais funcionalidades (câmera, receitas) continuam disponíveis."
            )
            return

        # Step 1 – collect and validate parameters
        params = self._collect_map_params(dialog)
        if params is None:  # validation failed ⇒ abort
            return

        # Step 2 – start generation thread
        self._start_map_thread(params, dialog, camera_preview)

    def _collect_map_params(self, parent_dialog=None) -> Optional[MapParams]:
        """
        Validate UI inputs and return MapParams object or None on error.

        Args:
            parent_dialog: Dialog for showing messages (avoids conflict with WindowStaysOnTopHint)

        Returns:
            MapParams object or None if validation fails
        """
        # Uses dialog as parent for MessageBox to avoid conflict
        # with WindowStaysOnTopHint
        msg_parent = parent_dialog if parent_dialog else None

        origin = getattr(self, 'map_origin', None)
        end = getattr(self, 'map_end', None)
        if not origin or not end:
            QMessageBox.warning(msg_parent, "Erro", "Defina ambos os cantos antes de gerar o mapa.")
            return None

        try:
            step_x = float(self.map_step_x_edit.text())
            step_y = float(self.map_step_y_edit.text())
        except ValueError:
            QMessageBox.warning(msg_parent, "Erro", "Passos X/Y inválidos.")
            return None

        dx, dy = end['x'] - origin['x'], end['y'] - origin['y']
        if step_x <= 0 or step_y <= 0:
            QMessageBox.warning(msg_parent, "Erro", "Os passos devem ser maiores que zero.")
            return None

        # Optional adjustment if step exceeds dimension
        if step_x > dx or step_y > dy:
            if QMessageBox.question(
                    msg_parent,
                    "Passo maior que dimensão",
                    ("Algum passo é maior que a dimensão da placa. "
                     "Deseja ajustar automaticamente?"),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            ) == QMessageBox.StandardButton.No:
                return None
            step_x = min(step_x, dx)
            step_y = min(step_y, dy)
            self.map_step_x_edit.setText(f"{step_x:.3f}")
            self.map_step_y_edit.setText(f"{step_y:.3f}")

        base_folder = self.map_folder_edit.text().strip()
        prog = self.map_program_name_edit.text().strip()
        if not base_folder or not prog:
            QMessageBox.warning(msg_parent, "Erro", "Informe o nome do programa e a pasta de salvamento.")
            return None

        # ========== CREATE FOLDER STRUCTURE ==========
        # Structure: [Base Folder]/[Program Name]/Imagens/
        # Sanitize program name for folder usage
        safe_prog_name = "".join(c for c in prog if c.isalnum() or c in "._- ").strip()
        if not safe_prog_name:
            QMessageBox.warning(msg_parent, "Erro", "Nome do programa inválido para criar pasta.")
            return None

        # Create folder structure
        program_folder = Path(base_folder) / safe_prog_name
        images_folder = program_folder / "Imagens"

        try:
            images_folder.mkdir(parents=True, exist_ok=True)
            logger.info(f"Estrutura de pastas criada: {images_folder}")
        except Exception as e:
            QMessageBox.critical(msg_parent, "Erro", f"Falha ao criar pasta:\n{images_folder}\n\nErro: {e}")
            return None

        # Images folder is where captures will be saved
        final_folder = str(images_folder)

        # ========== SAVE CONFIGURATIONS FOR NEXT TIME ==========
        try:
            # Save BASE folder (not images folder) so user can reuse
            self.config.remember_map_params(step_x, step_y, base_folder, prog)
            self.config.remember_mosaic_settings(
                auto_build=self.chk_auto_mosaic.isChecked(),
                margin=self.spin_mosaic_margin.value(),
                blend_size=self.spin_mosaic_blend.value(),
                capture_delay_ms=self.spin_capture_delay.value()
            )
            logger.debug("Configurações de mapa/mosaico salvas")
        except Exception as e:
            logger.warning(f"Erro ao salvar configurações de mapa: {e}")
        # ==========================================================

        # Use images folder as final destination
        return MapParams(origin, end, step_x, step_y, final_folder, prog)

    def _start_map_thread(self, p: MapParams, dialog, camera_preview):
        """
        Separate thread configuration from UI/ProgressBar.

        Args:
            p: MapParams with map generation parameters
            dialog: Map definition dialog
            camera_preview: CameraPreviewWidget instance
        """
        # Get configured wait time
        capture_delay = getattr(self, 'spin_capture_delay', None)
        delay_ms = capture_delay.value() if capture_delay else 200

        # Context manager ensures preview is restored
        with _PreviewSuspender(camera_preview):
            self.map_thread = MapGeneratorThread(
                self.controller, p.origin, p.end,
                p.step_x, p.step_y, p.folder, p.program_name,
                feed_rate=None,  # Use speed already in PLC (don't override)
                capture_delay_ms=delay_ms  # Wait time before capture
            )

            # Simple progress dialog
            self.map_progress = QProgressDialog("Gerando mapa…", "Cancelar", 0, 0, None)
            self.map_progress_dialog.setWindowTitle("Progresso do Mapa")
            self.map_progress_dialog.setWindowModality(Qt.WindowModality.NonModal)
            self.map_progress_dialog.show()

            # Signal ⇄ slot connections
            self.map_thread.progress.connect(self._on_map_progress)
            self.map_thread.image_captured.connect(camera_preview.display_image)
            self.map_thread.finished.connect(lambda: self._on_map_finished(dialog))
            self.map_thread.error.connect(self._on_map_error)

            self.map_progress_dialog.canceled.connect(self.map_thread.requestInterruption)
            self.map_thread.start()

    # ---------- map generation slots ------------

    def _on_map_progress(self, done: int, total: int):
        """
        Update progress during map generation.

        Args:
            done: Number of images captured
            total: Total number of images
        """
        self.map_progress_dialog.setMaximum(total)
        self.map_progress_dialog.setValue(done)
        pct = int(done / total * 100) if total else 0
        self.map_progress_dialog.setLabelText(f"Capturadas {done}/{total} imagens ({pct}%)")

        # Emit signal for external listeners
        self.map_progress.emit(done, total)

    def _on_map_finished(self, dialog):
        """
        Handle map generation completion.

        Args:
            dialog: Map definition dialog to close
        """
        self.map_progress_dialog.close()

        # IMPORTANT: Close dialog BEFORE showing messages
        # This avoids conflict with WindowStaysOnTopHint
        dialog.accept()

        # Get folder parameters and mosaic options
        folder = getattr(self, 'map_folder_edit', None)
        folder_path = folder.text().strip() if folder else ""

        # Check if automatic assembly is enabled
        auto_mosaic = getattr(self, 'chk_auto_mosaic', None)
        should_build_mosaic = auto_mosaic.isChecked() if auto_mosaic else True

        image_count = 0
        if should_build_mosaic and folder_path and Path(folder_path).is_dir():
            # Get margin and blending parameters
            margin = getattr(self, 'spin_mosaic_margin', None)
            margin_value = margin.value() if margin else 50

            blend = getattr(self, 'spin_mosaic_blend', None)
            blend_value = blend.value() if blend else 20

            # Build mosaic
            try:
                if compose_mosaic_from_folder is None:
                    logger.warning("Funcionalidade de mosaico não disponível - pulando montagem automática")
                    should_build_mosaic = False
                else:
                    mosaic_path = compose_mosaic_from_folder(
                        folder_path,
                        invert_rows=True,  # Origin at bottom-left corner
                        margin=margin_value,
                        blend_size=blend_value,
                    )

                    # Count images
                    images_folder = Path(folder_path) / "Imagens"
                    if images_folder.exists():
                        image_count = len(list(images_folder.glob("*.png")))

                    if mosaic_path:
                        self.map_generated.emit(image_count, str(mosaic_path))
                    else:
                        self.map_generated.emit(image_count, folder_path)
            except Exception as e:
                logger.error(f"Erro ao montar mosaico: {e}")
                self.map_error.emit(f"Erro ao montar mosaico: {e}")
        else:
            # Count images without mosaic
            images_folder = Path(folder_path) / "Imagens"
            if images_folder.exists():
                image_count = len(list(images_folder.glob("*.png")))
            self.map_generated.emit(image_count, folder_path)

    def _on_map_error(self, msg: str):
        """
        Handle map generation error.

        Args:
            msg: Error message
        """
        self.map_progress_dialog.close()
        self.map_error.emit(msg)

    # =========================================================================
    # UI HANDLERS (Migrados do SignalAggregator)
    # =========================================================================

    def setup_ui_handlers(self):
        """
        Configura handlers de UI para signals de mapa.

        Este método conecta os signals internos do MapController
        aos métodos que atualizam a UI do main_window.

        Deve ser chamado durante a inicialização do main_window.
        """
        # Conectar signals a handlers de UI
        self.program_saved.connect(self._on_program_saved_update_status)
        self.program_loaded.connect(self._on_program_loaded_update_status)
        self.program_deleted.connect(self._on_program_deleted_update_status)
        self.map_generated.connect(self._on_map_generated_show_message)
        self.map_progress.connect(self._on_map_progress_log)
        self.map_error.connect(self._on_map_error_show_message)

        logger.debug("UI handlers conectados no MapController")

    def _on_program_saved_update_status(self, name, path):
        """
        Atualiza statusBar quando programa de mapa é salvo.

        Args:
            name: Nome do programa
            path: Caminho do arquivo
        """
        logger.info(f"Programa de mapa salvo: {name} -> {path}")
        if hasattr(self.parent(), 'statusBar'):
            self.parent().statusBar().showMessage(f"Programa '{name}' salvo com sucesso", 3000)

    def _on_program_loaded_update_status(self, name, params):
        """
        Atualiza statusBar quando programa de mapa é carregado.

        Args:
            name: Nome do programa
            params: Parâmetros do programa
        """
        logger.info(f"Programa de mapa carregado: {name}")
        if hasattr(self.parent(), 'statusBar'):
            self.parent().statusBar().showMessage(f"Programa '{name}' carregado", 3000)

    def _on_program_deleted_update_status(self, name):
        """
        Atualiza statusBar quando programa de mapa é excluído.

        Args:
            name: Nome do programa
        """
        logger.info(f"Programa de mapa excluído: {name}")
        if hasattr(self.parent(), 'statusBar'):
            self.parent().statusBar().showMessage(f"Programa '{name}' excluído", 3000)

    def _on_map_generated_show_message(self, image_count, mosaic_path):
        """
        Mostra mensagem quando mosaico é gerado.

        Args:
            image_count: Número de imagens capturadas
            mosaic_path: Caminho do mosaico gerado
        """
        logger.info(f"Mosaico gerado: {mosaic_path} ({image_count} imagens)")

        if hasattr(self.parent(), 'statusBar'):
            self.parent().statusBar().showMessage(f"Mosaico gerado com sucesso", 5000)

        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(
            self.parent(),
            "Mosaico Gerado",
            f"O mosaico foi gerado com sucesso!\n\n"
            f"Arquivo: {mosaic_path}"
        )

    def _on_map_progress_log(self, current, total):
        """
        Log progresso da geração do mapa.

        Args:
            current: Número atual de imagens capturadas
            total: Total de imagens a capturar
        """
        logger.debug(f"Progresso do mapa: {current}/{total}")

    def _on_map_error_show_message(self, error_message):
        """
        Mostra mensagem de erro quando geração de mapa falha.

        Args:
            error_message: Mensagem de erro
        """
        logger.error(f"Erro no mapa: {error_message}")

        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(self.parent(), "Erro na Geração do Mapa", error_message)
