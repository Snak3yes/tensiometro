"""
MapController - Orchestrator for map generation and program management.

Refactored to use MapProgramManager (CRUD) and MapSettingsDialog (UI).
Now acts as a pure orchestrator, delegating to specialized components.
"""

import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal, Qt
from PyQt6.QtWidgets import QMessageBox, QProgressDialog

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
from consumo_lib.services.map_program_manager import MapProgramManager, MAP_PROGRAMS_FOLDER
from consumo_lib.dialogs.map_settings_dialog import MapSettingsDialog
from consumo_lib.utils.error_handler import show_motion_interlock_dialog

# Import compose_mosaic_from_folder with fallback
try:
    from tools.mosaic_builder import compose_mosaic_from_folder
except ImportError:
    try:
        from mosaic_builder import compose_mosaic_from_folder
    except ImportError:
        compose_mosaic_from_folder = None

logger = logging.getLogger("consumo_lib")


class MapController(QObject):
    """
    Orchestrator controller for map generation and program management.

    Delegates CRUD operations to MapProgramManager and UI to MapSettingsDialog.
    Manages map generation thread and high-level workflow.

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

        # Components
        self.program_manager = MapProgramManager()

        # Runtime state
        self.map_origin = None
        self.map_end = None
        self.map_thread = None
        self.map_progress_dialog = None

        # Dialog reference (lazy loaded)
        self.dialog = None

    def show_dialog(self, parent_widget, camera_preview):
        """
        Show the map definition dialog (modeless, always on top).

        Args:
            parent_widget: Parent QWidget (usually MainWindow)
            camera_preview: CameraPreviewWidget instance

        Returns:
            MapSettingsDialog instance
        """
        # Create dialog if not exists
        if self.dialog is None:
            self.dialog = MapSettingsDialog(parent_widget)

            # Connect signals
            self.dialog.program_load_requested.connect(self._on_load_program_requested)
            self.dialog.program_delete_requested.connect(self._on_delete_program_requested)
            self.dialog.save_requested.connect(self._on_save_requested)
            self.dialog.step_changed.connect(self._on_step_changed)
            self.dialog.corner_define_requested.connect(lambda corner: self._define_map_corner(corner, parent_widget))
            self.dialog.generate_requested.connect(lambda: self._on_generate_map(self.dialog, camera_preview))

        # Load last settings
        self._load_last_settings()

        # Refresh programs list
        self._refresh_programs_list()

        # Show dialog
        self.dialog.show()

        return self.dialog

    # ==================== PROGRAM MANAGEMENT ====================

    def _refresh_programs_list(self):
        """Refresh programs list in dialog."""
        if self.dialog:
            programs = self.program_manager.list_programs()
            self.dialog.update_programs_list(programs)

    def _on_load_program_requested(self, program_path: Path):
        """
        Handle program load request from dialog.

        Args:
            program_path: Path to program directory
        """
        program = self.program_manager.load_program(program_path)
        if not program:
            QMessageBox.warning(self.dialog, "Erro", f"Falha ao carregar programa:\n{program_path}")
            return

        # Update dialog fields
        capture = program.capture_params
        mosaic = program.mosaic_params

        self.dialog.update_field_values(
            program_name=program.name,
            base_folder=str(program.path.parent),
            step_x=capture.get('step_x', 10.0),
            step_y=capture.get('step_y', 10.0),
            auto_build=mosaic.get('auto_build', True),
            margin=mosaic.get('margin', 50),
            blend_size=mosaic.get('blend_size', 20),
            capture_delay_ms=mosaic.get('capture_delay_ms', 200)
        )

        # Update internal state
        origin = capture.get('origin', {})
        end = capture.get('end', {})
        if origin.get('x') is not None:
            self.map_origin = origin
        if end.get('x') is not None:
            self.map_end = end

        # Update calculated info
        self._on_step_changed()

        logger.info(f"Programa carregado: {program_path}")
        self.program_loaded.emit(program.name, program.to_dict())

    def _on_delete_program_requested(self, program_path: Path):
        """
        Handle program delete request from dialog.

        Args:
            program_path: Path to program directory
        """
        program_name = program_path.name

        # Confirm deletion
        reply = QMessageBox.question(
            self.dialog, "Confirmar Exclusão",
            f"Deseja excluir o programa '{program_name}'?\n\n"
            f"Pasta: {program_path}\n\n"
            "Esta ação removerá a pasta e todo seu conteúdo (imagens, mosaico, etc.)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Delete program
        success, error_msg = self.program_manager.delete_program(program_path)
        if not success:
            QMessageBox.critical(self.dialog, "Erro", error_msg)
            return

        # Refresh list
        self._refresh_programs_list()
        self.program_deleted.emit(program_name)

    def _on_save_requested(self):
        """Handle save button click from dialog."""
        if not self.dialog:
            return

        # Get field values
        values = self.dialog.get_field_values()

        # Validate and save
        success, program_path, error_msg = self.program_manager.save_program(
            program_name=values['program_name'],
            base_folder=values['base_folder'],
            origin=self.map_origin or {'x': 0, 'y': 0},
            end=self.map_end or {'x': 0, 'y': 0},
            step_x=values['step_x'],
            step_y=values['step_y'],
            auto_build=values['auto_build'],
            margin=values['margin'],
            blend_size=values['blend_size'],
            capture_delay_ms=values['capture_delay_ms']
        )

        if not success:
            QMessageBox.warning(self.dialog, "Erro", error_msg)
            return

        # Refresh list
        self._refresh_programs_list()
        self.program_saved.emit(values['program_name'], program_path)

        logger.info(f"Programa salvo: {program_path}")

    # ==================== CORNER DEFINITION ====================

    def _define_map_corner(self, which: str, status_target):
        """
        Define map corner (origin or end) from current CNC position.

        Args:
            which: 'origin' or 'end'
            status_target: Widget with statusBar() method (usually MainWindow)
        """
        pos = self.controller.cnc.get_current_position()
        if which == 'origin':
            self.map_origin = {'x': pos['x'], 'y': pos['y']}
            status_target.statusBar().showMessage(
                f"✅ Origem definida: X={pos['x']:.3f}, Y={pos['y']:.3f}"
            )
        else:
            self.map_end = {'x': pos['x'], 'y': pos['y']}
            status_target.statusBar().showMessage(
                f"✅ Limite definido: X={pos['x']:.3f}, Y={pos['y']:.3f}"
            )

        # Update calculated info panel
        self._on_step_changed()

    # ==================== CALCULATED INFO ====================

    def _on_step_changed(self):
        """Handle step value change - update calculated info panel."""
        if not self.dialog or not self.map_origin or not self.map_end:
            return

        try:
            step_x = float(self.dialog.map_step_x_edit.text() or "10.0")
            step_y = float(self.dialog.map_step_y_edit.text() or "10.0")
        except ValueError:
            return

        try:
            adjusted = CNCAOIController.calculate_adjusted_steps(
                self.map_origin, self.map_end, step_x, step_y
            )
            self.dialog.update_calculated_info(adjusted)
        except ValueError as e:
            logger.warning(f"Erro ao calcular passos ajustados: {e}")
        except Exception as e:
            logger.warning(f"Erro ao calcular passos ajustados: {e}")

    # ==================== MAP GENERATION ====================

    def _on_generate_map(self, dialog, camera_preview):
        """
        Start map generation process.

        Args:
            dialog: Map definition dialog
            camera_preview: CameraPreviewWidget instance
        """
        # Check CNC connection
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

        # Collect and validate parameters
        params = self._collect_map_params(dialog)
        if params is None:
            return

        # Start generation thread
        self._start_map_thread(params, dialog, camera_preview)

    def _collect_map_params(self, parent_dialog) -> Optional[MapParams]:
        """
        Validate UI inputs and return MapParams object or None on error.

        Args:
            parent_dialog: Dialog for showing messages

        Returns:
            MapParams object or None if validation fails
        """
        if not self.dialog:
            return None

        # Get field values
        values = self.dialog.get_field_values()

        origin = self.map_origin
        end = self.map_end
        if not origin or not end:
            QMessageBox.warning(parent_dialog, "Erro", "Defina ambos os cantos antes de gerar o mapa.")
            return None

        step_x = values['step_x']
        step_y = values['step_y']
        dx, dy = end['x'] - origin['x'], end['y'] - origin['y']

        if step_x <= 0 or step_y <= 0:
            QMessageBox.warning(parent_dialog, "Erro", "Os passos devem ser maiores que zero.")
            return None

        # Optional adjustment if step exceeds dimension
        if step_x > dx or step_y > dy:
            if QMessageBox.question(
                    parent_dialog,
                    "Passo maior que dimensão",
                    ("Algum passo é maior que a dimensão da placa. "
                     "Deseja ajustar automaticamente?"),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            ) == QMessageBox.StandardButton.No:
                return None
            step_x = min(step_x, dx)
            step_y = min(step_y, dy)
            self.dialog.map_step_x_edit.setText(f"{step_x:.3f}")
            self.dialog.map_step_y_edit.setText(f"{step_y:.3f}")

        base_folder = values['base_folder']
        prog = values['program_name']
        if not base_folder or not prog:
            QMessageBox.warning(parent_dialog, "Erro", "Informe o nome do programa e a pasta de salvamento.")
            return None

        # Create folder structure
        success, program_folder, error_msg = self.program_manager.create_program_structure(
            base_folder, prog
        )
        if not success:
            QMessageBox.critical(parent_dialog, "Erro", error_msg)
            return None

        # Images folder
        final_folder = str(program_folder / "Imagens")

        # Save configurations for next time
        try:
            self.config.remember_map_params(step_x, step_y, base_folder, prog)
            self.config.remember_mosaic_settings(
                auto_build=values['auto_build'],
                margin=values['margin'],
                blend_size=values['blend_size'],
                capture_delay_ms=values['capture_delay_ms']
            )
            logger.debug("Configurações de mapa/mosaico salvas")
        except Exception as e:
            logger.warning(f"Erro ao salvar configurações de mapa: {e}")

        return MapParams(origin, end, step_x, step_y, final_folder, prog)

    def _start_map_thread(self, p: MapParams, dialog, camera_preview):
        """
        Configure and start map generation thread.

        Args:
            p: MapParams with map generation parameters
            dialog: Map definition dialog
            camera_preview: CameraPreviewWidget instance
        """
        # Get configured wait time
        delay_ms = self.dialog.spin_capture_delay.value() if self.dialog else 200

        # Context manager ensures preview is restored
        with _PreviewSuspender(camera_preview):
            self.map_thread = MapGeneratorThread(
                self.controller, p.origin, p.end,
                p.step_x, p.step_y, p.folder, p.program_name,
                feed_rate=None,  # Use speed already in PLC
                capture_delay_ms=delay_ms
            )

            # Simple progress dialog
            self.map_progress_dialog = QProgressDialog("Gerando mapa…", "Cancelar", 0, 0, None)
            self.map_progress_dialog.setWindowTitle("Progresso do Mapa")
            self.map_progress_dialog.setWindowModality(Qt.WindowModality.NonModal)
            self.map_progress_dialog.show()

            # Signal connections
            self.map_thread.progress.connect(self._on_map_progress)
            self.map_thread.image_captured.connect(camera_preview.display_image)
            self.map_thread.finished.connect(lambda: self._on_map_finished(dialog))
            self.map_thread.error.connect(self._on_map_error)

            self.map_progress_dialog.canceled.connect(self.map_thread.requestInterruption)
            self.map_thread.start()

    def _on_map_progress(self, done: int, total: int):
        """
        Update progress during map generation.

        Args:
            done: Number of images captured
            total: Total number of images
        """
        if self.map_progress_dialog:
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
        if self.map_progress_dialog:
            self.map_progress_dialog.close()

        # Close dialog BEFORE showing messages
        dialog.accept()

        if not self.dialog:
            return

        # Get folder parameters and mosaic options
        folder_path = self.dialog.map_folder_edit.text().strip()
        should_build_mosaic = self.dialog.chk_auto_mosaic.isChecked()

        image_count = 0
        if should_build_mosaic and folder_path and Path(folder_path).is_dir():
            margin = self.dialog.spin_mosaic_margin.value()
            blend_value = self.dialog.spin_mosaic_blend.value()

            # Build mosaic
            try:
                if compose_mosaic_from_folder is None:
                    logger.warning("Funcionalidade de mosaico não disponível - pulando montagem automática")
                else:
                    mosaic_path = compose_mosaic_from_folder(
                        folder_path,
                        invert_rows=True,
                        margin=margin,
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
        if self.map_progress_dialog:
            self.map_progress_dialog.close()
        self.map_error.emit(msg)

    # ==================== SETTINGS PERSISTENCE ====================

    def _load_last_settings(self):
        """Load last used settings from config."""
        if not self.dialog:
            return

        # Load last program name
        last_program = self.config.get("mosaic", "last_program_name", default="")
        self.dialog.map_program_name_edit.setText(last_program)

        # Load last folder
        last_folder = self.config.get("mosaic", "last_folder", default=str(MAP_PROGRAMS_FOLDER))
        self.dialog.map_folder_edit.setText(last_folder)

        # Load step values
        saved_step_x = self.config.get("map", "step_x", default=10.0)
        saved_step_y = self.config.get("map", "step_y", default=10.0)
        self.dialog.map_step_x_edit.setText(str(saved_step_x))
        self.dialog.map_step_y_edit.setText(str(saved_step_y))

        # Load mosaic settings
        saved_auto_build = self.config.get("mosaic", "auto_build", default=True)
        saved_margin = self.config.get("mosaic", "margin", default=50)
        saved_blend = self.config.get("mosaic", "blend_size", default=20)
        saved_delay = self.config.get("mosaic", "capture_delay_ms", default=200)

        self.dialog.chk_auto_mosaic.setChecked(saved_auto_build)
        self.dialog.spin_mosaic_margin.setValue(saved_margin)
        self.dialog.spin_mosaic_blend.setValue(saved_blend)
        self.dialog.spin_capture_delay.setValue(saved_delay)

    # ==================== UI HANDLERS ====================

    def setup_ui_handlers(self):
        """
        Configure UI handlers for map signals.

        Connects internal MapController signals to UI update methods.
        Should be called during main_window initialization.
        """
        self.program_saved.connect(self._on_program_saved_update_status)
        self.program_loaded.connect(self._on_program_loaded_update_status)
        self.program_deleted.connect(self._on_program_deleted_update_status)
        self.map_generated.connect(self._on_map_generated_show_message)
        self.map_progress.connect(self._on_map_progress_log)
        self.map_error.connect(self._on_map_error_show_message)

        logger.debug("UI handlers conectados no MapController")

    def _on_program_saved_update_status(self, name, path):
        """Update statusBar when program is saved."""
        logger.info(f"Programa de mapa salvo: {name} -> {path}")
        if hasattr(self.parent(), 'statusBar'):
            self.parent().statusBar().showMessage(f"Programa '{name}' salvo com sucesso", 3000)

    def _on_program_loaded_update_status(self, name, params):
        """Update statusBar when program is loaded."""
        logger.info(f"Programa de mapa carregado: {name}")
        if hasattr(self.parent(), 'statusBar'):
            self.parent().statusBar().showMessage(f"Programa '{name}' carregado", 3000)

    def _on_program_deleted_update_status(self, name):
        """Update statusBar when program is deleted."""
        logger.info(f"Programa de mapa excluído: {name}")
        if hasattr(self.parent(), 'statusBar'):
            self.parent().statusBar().showMessage(f"Programa '{name}' excluído", 3000)

    def _on_map_generated_show_message(self, image_count, mosaic_path):
        """Show message when mosaic is generated."""
        logger.info(f"Mosaico gerado: {mosaic_path} ({image_count} imagens)")

        if hasattr(self.parent(), 'statusBar'):
            self.parent().statusBar().showMessage(f"Mosaico gerado com sucesso", 5000)

        QMessageBox.information(
            self.parent(),
            "Mosaico Gerado",
            f"O mosaico foi gerado com sucesso!\n\n"
            f"Arquivo: {mosaic_path}"
        )

    def _on_map_progress_log(self, current, total):
        """Log map generation progress."""
        logger.debug(f"Progresso do mapa: {current}/{total}")

    def _on_map_error_show_message(self, error_message):
        """Show error message when map generation fails."""
        logger.error(f"Erro no mapa: {error_message}")
        if show_motion_interlock_dialog(self.parent(), error_message, operation="geracao de mapa"):
            return
        QMessageBox.critical(self.parent(), "Erro na Geração do Mapa", error_message)
