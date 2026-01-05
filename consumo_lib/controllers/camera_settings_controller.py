"""
CameraSettingsController - Handles camera configuration and presets.

Extracted from MainWindow.show_camera_settings_dialog() and related methods.
Manages camera properties (brightness, contrast, exposure, etc.) and presets.
"""

import json
import logging
from typing import Dict, Optional

import cv2
from PyQt6.QtCore import QObject, pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QSlider, QLineEdit, QCheckBox, QComboBox,
    QSpinBox, QPushButton, QMessageBox, QFileDialog
)

# Add project root to path for imports
import sys
from pathlib import Path as _Path
_current_file = _Path(__file__).resolve()
_root_dir = _current_file.parent.parent.parent
if str(_root_dir) not in sys.path:
    sys.path.insert(0, str(_root_dir))

logger = logging.getLogger("consumo_lib")


class CameraSettingsController(QObject):
    """
    Controller for camera settings management.

    Signals:
        settings_changed: Emitted when any setting is changed (setting_name, value)
        settings_applied: Emitted when settings are applied to camera (settings_dict)
        settings_saved: Emitted when settings are saved to preset (preset_name)
        settings_loaded: Emitted when preset is loaded (preset_name, settings_dict)
    """

    settings_changed = pyqtSignal(str, object)  # setting_name, value
    settings_applied = pyqtSignal(dict)  # settings_dict
    settings_saved = pyqtSignal(str)  # preset_name
    settings_loaded = pyqtSignal(str, dict)  # preset_name, settings_dict

    def __init__(self, controller, config_manager, parent=None):
        """
        Initialize CameraSettingsController.

        Args:
            controller: CNCAOIController instance (with camera)
            config_manager: AOIConfigManager instance
            parent: Optional parent QObject
        """
        super().__init__(parent)
        self.controller = controller
        self.config = config_manager

        # Runtime camera reference
        self._camera_cap_ref = None

        # Mirror settings (runtime state)
        self._camera_mirror_x = False
        self._camera_mirror_y = False

        # UI widgets (filled by show_dialog)
        self.chk_mirror_x = None
        self.chk_mirror_y = None
        self.slider_brightness = None
        self.slider_contrast = None
        self.slider_saturation = None
        self.slider_exposure = None
        self.lbl_exposure = None
        self.slider_gain = None
        self.slider_focus = None
        self.chk_auto_exp = None
        self.chk_auto_wb = None
        self.chk_auto_focus = None
        self.combo_cam_presets = None
        self.edit_preset_name = None

    def show_dialog(self, parent_widget=None):
        """
        Show camera settings dialog.

        Args:
            parent_widget: Parent QWidget (usually MainWindow)

        Returns:
            QDialog instance
        """
        if not hasattr(self.controller.camera, 'is_connected') or not self.controller.camera.is_connected:
            QMessageBox.warning(parent_widget, "Aviso", "Conecte a câmera antes de ajustar as configurações.")
            return None

        # Get VideoCapture object
        cap = self.controller.camera.camera
        if cap is None:
            QMessageBox.warning(parent_widget, "Erro", "Câmera não disponível.")
            return None

        # Store reference for batch operations
        self._camera_cap_ref = cap

        dialog = QDialog(parent_widget)
        dialog.setWindowTitle("Configurações de Câmera")
        dialog.setMinimumWidth(500)

        layout = QVBoxLayout(dialog)

        # Load saved focus values
        saved_focus = self.config.get("camera", "focus", default=0)
        saved_auto_focus = self.config.get("camera", "auto_focus", default=True)

        # ============== MIRRORING ==============
        mirror_group = QGroupBox("Espelhamento da Imagem")
        mirror_layout = QHBoxLayout(mirror_group)

        self.chk_mirror_x = QCheckBox("Espelhar Horizontalmente (X)")
        saved_mirror_x = self.config.get("camera", "mirror_x", default=False)
        self._camera_mirror_x = saved_mirror_x
        self.chk_mirror_x.setChecked(self._camera_mirror_x)
        mirror_layout.addWidget(self.chk_mirror_x)

        self.chk_mirror_y = QCheckBox("Espelhar Verticalmente (Y)")
        saved_mirror_y = self.config.get("camera", "mirror_y", default=False)
        self._camera_mirror_y = saved_mirror_y
        self.chk_mirror_y.setChecked(self._camera_mirror_y)
        mirror_layout.addWidget(self.chk_mirror_y)

        layout.addWidget(mirror_group)

        # ============== IMAGE ADJUSTMENTS ==============
        settings_group = QGroupBox("Ajustes de Imagem")
        settings_layout = QVBoxLayout(settings_group)

        # Function to create slider row with label
        def create_slider_row(label, prop_id, min_val, max_val, default, scale=1.0):
            row = QHBoxLayout()
            row.addWidget(QLabel(f"{label}:"))

            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(min_val, max_val)

            # Try to read current value
            try:
                current = cap.get(prop_id)
                if current != -1 and current != 0:
                    slider.setValue(int(current * scale))
                else:
                    slider.setValue(default)
            except:
                slider.setValue(default)

            lbl = QLabel(str(slider.value()))
            slider.valueChanged.connect(lambda v: lbl.setText(str(v)))
            slider.valueChanged.connect(lambda v: self._apply_camera_prop(cap, prop_id, v / scale))

            row.addWidget(slider)
            row.addWidget(lbl)
            return slider, row

        # Brightness (0-255 on most cameras)
        self.slider_brightness, brightness_row = create_slider_row("Brilho", cv2.CAP_PROP_BRIGHTNESS, 0, 255, 128, 1.0)
        settings_layout.addLayout(brightness_row)

        # Contrast (0-255)
        self.slider_contrast, contrast_row = create_slider_row("Contraste", cv2.CAP_PROP_CONTRAST, 0, 255, 128, 1.0)
        settings_layout.addLayout(contrast_row)

        # Saturation (0-255)
        self.slider_saturation, saturation_row = create_slider_row("Saturação", cv2.CAP_PROP_SATURATION, 0, 255, 128, 1.0)
        settings_layout.addLayout(saturation_row)

        # Exposure (-13 to 0 for typical USB cameras)
        exposure_row = QHBoxLayout()
        exposure_row.addWidget(QLabel("Exposição:"))
        self.slider_exposure = QSlider(Qt.Orientation.Horizontal)
        self.slider_exposure.setRange(-13, 0)
        try:
            exp = int(cap.get(cv2.CAP_PROP_EXPOSURE))
            self.slider_exposure.setValue(exp if -13 <= exp <= 0 else -6)
        except:
            self.slider_exposure.setValue(-6)
        self.lbl_exposure = QLabel(str(self.slider_exposure.value()))
        self.slider_exposure.valueChanged.connect(lambda v: self.lbl_exposure.setText(str(v)))
        self.slider_exposure.valueChanged.connect(lambda v: self._apply_camera_prop(cap, cv2.CAP_PROP_EXPOSURE, v))
        exposure_row.addWidget(self.slider_exposure)
        exposure_row.addWidget(self.lbl_exposure)
        settings_layout.addLayout(exposure_row)

        # Gain (0-255)
        self.slider_gain, gain_row = create_slider_row("Ganho", cv2.CAP_PROP_GAIN, 0, 255, 128, 1.0)
        settings_layout.addLayout(gain_row)

        # Focus (0-255)
        self.slider_focus, focus_row = create_slider_row("Foco", cv2.CAP_PROP_FOCUS, 0, 255, saved_focus, 1.0)

        def _on_focus_change(v):
            # If user moved focus, turn off auto-focus and fix value
            if hasattr(self, "chk_auto_focus") and self.chk_auto_focus.isChecked():
                self.chk_auto_focus.blockSignals(True)
                self.chk_auto_focus.setChecked(False)
                self.chk_auto_focus.blockSignals(False)
                self._apply_focus_mode(cap, False)
            self._apply_camera_prop(cap, cv2.CAP_PROP_FOCUS, v)

        self.slider_focus.valueChanged.connect(_on_focus_change)
        settings_layout.addLayout(focus_row)

        layout.addWidget(settings_group)

        # ============== AUTOMATIC EXPOSURE ==============
        auto_group = QGroupBox("Controle Automático")
        auto_layout = QHBoxLayout(auto_group)

        self.chk_auto_exp = QCheckBox("Exposição Automática")
        try:
            auto_val = cap.get(cv2.CAP_PROP_AUTO_EXPOSURE)
            self.chk_auto_exp.setChecked(auto_val == 3 or auto_val == 1)
        except:
            self.chk_auto_exp.setChecked(True)
        self.chk_auto_exp.toggled.connect(
            lambda on: self._apply_camera_prop(cap, cv2.CAP_PROP_AUTO_EXPOSURE, 3 if on else 1)
        )
        auto_layout.addWidget(self.chk_auto_exp)

        self.chk_auto_wb = QCheckBox("Balanço de Branco Automático")
        try:
            wb_val = cap.get(cv2.CAP_PROP_AUTO_WB)
            self.chk_auto_wb.setChecked(wb_val == 1)
        except:
            self.chk_auto_wb.setChecked(True)
        self.chk_auto_wb.toggled.connect(
            lambda on: self._apply_camera_prop(cap, cv2.CAP_PROP_AUTO_WB, 1 if on else 0)
        )
        auto_layout.addWidget(self.chk_auto_wb)

        # Auto focus
        self.chk_auto_focus = QCheckBox("Foco Automático")
        try:
            af_val = cap.get(cv2.CAP_PROP_AUTOFOCUS)
            auto_focus_on = (af_val == 1)
        except Exception:
            auto_focus_on = saved_auto_focus
        self.chk_auto_focus.setChecked(auto_focus_on)
        self.chk_auto_focus.toggled.connect(lambda on: self._apply_focus_mode(cap, on))
        auto_layout.addWidget(self.chk_auto_focus)
        # Adjust initial state (enable/disable slider)
        self._apply_focus_mode(cap, auto_focus_on)

        layout.addWidget(auto_group)

        # ============== CAMERA PROFILES ==============
        presets_grp = QGroupBox("Perfis de Câmera")
        presets_layout = QVBoxLayout(presets_grp)

        # Preset selection
        sel_row = QHBoxLayout()
        sel_row.addWidget(QLabel("Perfil:"))
        self.combo_cam_presets = QComboBox()
        self._load_camera_presets_into_combo()
        sel_row.addWidget(self.combo_cam_presets, 1)
        btn_load_preset = QPushButton("Carregar")
        btn_load_preset.clicked.connect(self._load_selected_camera_preset)
        sel_row.addWidget(btn_load_preset)
        presets_layout.addLayout(sel_row)

        # Save/update preset
        save_row = QHBoxLayout()
        save_row.addWidget(QLabel("Nome:"))
        self.edit_preset_name = QLineEdit()
        save_row.addWidget(self.edit_preset_name, 1)
        btn_save_preset = QPushButton("Salvar/Atualizar")
        btn_save_preset.clicked.connect(self._save_current_camera_preset)
        save_row.addWidget(btn_save_preset)
        presets_layout.addLayout(save_row)

        # Apply and export
        action_row = QHBoxLayout()
        btn_apply_now = QPushButton("Aplicar Ajustes")
        btn_apply_now.clicked.connect(lambda: self._apply_current_camera_settings(cap))
        action_row.addWidget(btn_apply_now)
        btn_export_preset = QPushButton("Exportar JSON")
        btn_export_preset.clicked.connect(self._export_current_camera_settings)
        action_row.addWidget(btn_export_preset)
        presets_layout.addLayout(action_row)

        layout.addWidget(presets_grp)

        # ============== BUTTONS ==============
        btn_layout = QHBoxLayout()

        btn_reset = QPushButton("Restaurar Padrão")
        btn_reset.clicked.connect(lambda: self._reset_camera_props(cap))
        btn_layout.addWidget(btn_reset)

        btn_apply = QPushButton("Aplicar Espelhamento")
        btn_apply.clicked.connect(self._apply_mirror_settings)
        btn_layout.addWidget(btn_apply)

        btn_apply_all = QPushButton("Aplicar Ajustes (Câmera)")
        btn_apply_all.clicked.connect(lambda: self._apply_current_camera_settings(cap))
        btn_layout.addWidget(btn_apply_all)

        btn_close = QPushButton("Fechar")
        btn_close.clicked.connect(dialog.accept)
        btn_layout.addWidget(btn_close)

        layout.addLayout(btn_layout)

        # Information note
        note = QLabel("<i>Nota: Algumas configurações podem não funcionar com todas as câmeras.</i>")
        note.setWordWrap(True)
        layout.addWidget(note)

        dialog.exec()

        # Save mirroring settings
        self._camera_mirror_x = self.chk_mirror_x.isChecked()
        self._camera_mirror_y = self.chk_mirror_y.isChecked()

        return dialog

    def _apply_camera_prop(self, cap, prop_id, value):
        """
        Apply a property to OpenCV camera.

        Args:
            cap: VideoCapture object
            prop_id: OpenCV property constant (cv2.CAP_PROP_*)
            value: Value to set
        """
        try:
            result = cap.set(prop_id, value)
            if result:
                logger.debug(f"Câmera: Propriedade {prop_id} = {value}")
            else:
                logger.warning(f"Câmera: Falha ao definir propriedade {prop_id} = {value}")
        except Exception as e:
            logger.warning(f"Erro ao aplicar configuração de câmera: {e}")

    def _gather_camera_settings(self) -> dict:
        """
        Collect current UI camera values into a dictionary.

        Returns:
            Dictionary with all camera settings
        """
        return {
            "mirror_x": self.chk_mirror_x.isChecked() if self.chk_mirror_x else False,
            "mirror_y": self.chk_mirror_y.isChecked() if self.chk_mirror_y else False,
            "brightness": self.slider_brightness.value() if self.slider_brightness else 128,
            "contrast": self.slider_contrast.value() if self.slider_contrast else 128,
            "saturation": self.slider_saturation.value() if self.slider_saturation else 128,
            "exposure": self.slider_exposure.value() if self.slider_exposure else -6,
            "gain": self.slider_gain.value() if self.slider_gain else 128,
            "focus": self.slider_focus.value() if hasattr(self, "slider_focus") and self.slider_focus else 0,
            "auto_exposure": self.chk_auto_exp.isChecked() if self.chk_auto_exp else True,
            "auto_white_balance": self.chk_auto_wb.isChecked() if self.chk_auto_wb else True,
            "auto_focus": self.chk_auto_focus.isChecked() if hasattr(self, "chk_auto_focus") and self.chk_auto_focus else True,
        }

    def _apply_current_camera_settings(self, cap):
        """
        Apply all current UI adjustments to camera device.

        Args:
            cap: VideoCapture object
        """
        try:
            settings = self._gather_camera_settings()
            # Automatic settings
            self._apply_camera_prop(cap, cv2.CAP_PROP_AUTO_EXPOSURE, 3 if settings["auto_exposure"] else 1)
            self._apply_camera_prop(cap, cv2.CAP_PROP_AUTO_WB, 1 if settings["auto_white_balance"] else 0)
            self._apply_focus_mode(cap, settings["auto_focus"])
            # Manual values
            self._apply_camera_prop(cap, cv2.CAP_PROP_BRIGHTNESS, settings["brightness"])
            self._apply_camera_prop(cap, cv2.CAP_PROP_CONTRAST, settings["contrast"])
            self._apply_camera_prop(cap, cv2.CAP_PROP_SATURATION, settings["saturation"])
            self._apply_camera_prop(cap, cv2.CAP_PROP_EXPOSURE, settings["exposure"])
            self._apply_camera_prop(cap, cv2.CAP_PROP_GAIN, settings["gain"])
            if not settings["auto_focus"]:
                self._apply_camera_prop(cap, cv2.CAP_PROP_FOCUS, settings["focus"])

            # Emit signal
            self.settings_applied.emit(settings)

        except Exception as e:
            logger.warning(f"Falha ao aplicar ajustes de câmera: {e}")

    def _apply_focus_mode(self, cap, auto_on: bool):
        """
        Turn auto-focus on/off and adjust focus UI.

        Args:
            cap: VideoCapture object
            auto_on: True for auto-focus, False for manual
        """
        try:
            self._apply_camera_prop(cap, cv2.CAP_PROP_AUTOFOCUS, 1 if auto_on else 0)
        except Exception:
            pass

        if hasattr(self, "slider_focus"):
            self.slider_focus.setEnabled(not auto_on)

        # When auto-focus is off, reapply current manual value
        if not auto_on and hasattr(self, "slider_focus"):
            try:
                self._apply_camera_prop(cap, cv2.CAP_PROP_FOCUS, self.slider_focus.value())
            except Exception:
                pass

    def _reset_camera_props(self, cap):
        """
        Restore default camera settings.

        Args:
            cap: VideoCapture object
        """
        if self.slider_brightness:
            self.slider_brightness.setValue(128)
        if self.slider_contrast:
            self.slider_contrast.setValue(128)
        if self.slider_saturation:
            self.slider_saturation.setValue(128)
        if self.slider_exposure:
            self.slider_exposure.setValue(-6)
        if self.slider_gain:
            self.slider_gain.setValue(128)
        if self.chk_auto_exp:
            self.chk_auto_exp.setChecked(True)
        if self.chk_auto_wb:
            self.chk_auto_wb.setChecked(True)
        if hasattr(self, "slider_focus") and self.slider_focus:
            self.slider_focus.blockSignals(True)
            self.slider_focus.setValue(self.config.get("camera", "focus", default=0))
            self.slider_focus.blockSignals(False)
        if hasattr(self, "chk_auto_focus") and self.chk_auto_focus:
            self.chk_auto_focus.setChecked(True)
            self._apply_focus_mode(cap, True)
        if self.chk_mirror_x:
            self.chk_mirror_x.setChecked(False)
        if self.chk_mirror_y:
            self.chk_mirror_y.setChecked(False)

    def _apply_mirror_settings(self):
        """Save mirroring settings to config"""
        self._camera_mirror_x = self.chk_mirror_x.isChecked() if self.chk_mirror_x else False
        self._camera_mirror_y = self.chk_mirror_y.isChecked() if self.chk_mirror_y else False

        # Save all camera settings to file
        try:
            self.config.remember_camera_settings(
                mirror_x=self._camera_mirror_x,
                mirror_y=self._camera_mirror_y,
                brightness=self.slider_brightness.value() if self.slider_brightness else 128,
                contrast=self.slider_contrast.value() if self.slider_contrast else 128,
                saturation=self.slider_saturation.value() if self.slider_saturation else 128,
                exposure=self.slider_exposure.value() if self.slider_exposure else -6,
                gain=self.slider_gain.value() if self.slider_gain else 128,
                focus=self.slider_focus.value() if hasattr(self, "slider_focus") and self.slider_focus else 0,
                auto_exp=self.chk_auto_exp.isChecked() if self.chk_auto_exp else True,
                auto_wb=self.chk_auto_wb.isChecked() if self.chk_auto_wb else True,
                auto_focus=self.chk_auto_focus.isChecked() if hasattr(self, "chk_auto_focus") and self.chk_auto_focus else True
            )
            logger.info("Configurações de câmera salvas")
        except Exception as e:
            logger.warning(f"Erro ao salvar configurações de câmera: {e}")

    # ========= CAMERA PRESETS =========

    def _load_camera_presets_into_combo(self):
        """Update combo with saved presets."""
        if not self.combo_cam_presets:
            return

        presets = self.config.list_camera_presets()
        self.combo_cam_presets.clear()
        self.combo_cam_presets.addItem("Selecione…", userData=None)
        for name in presets:
            self.combo_cam_presets.addItem(name, userData=name)

    def _save_current_camera_preset(self):
        """Save current settings as a preset."""
        if not self.edit_preset_name:
            return

        name = self.edit_preset_name.text().strip()
        if not name:
            QMessageBox.warning(None, "Nome obrigatório", "Informe um nome para salvar o perfil.")
            return

        data = self._gather_camera_settings()
        try:
            self.config.save_camera_preset(name, data)
            self._load_camera_presets_into_combo()
            logger.info(f"Perfil '{name}' salvo.")

            # Emit signal
            self.settings_saved.emit(name)

        except Exception as e:
            QMessageBox.warning(None, "Erro", f"Falha ao salvar perfil: {e}")

    def _load_selected_camera_preset(self):
        """Load selected preset and apply to camera."""
        if not self.combo_cam_presets or not self._camera_cap_ref:
            return

        name = self.combo_cam_presets.currentData()
        if not name:
            QMessageBox.information(None, "Selecione", "Escolha um perfil para carregar.")
            return

        preset = self.config.get_camera_preset(name)
        if not preset:
            QMessageBox.warning(None, "Erro", f"Perfil '{name}' não encontrado.")
            return

        try:
            from PyQt6.QtCore import QSignalBlocker

            with QSignalBlocker(self.slider_brightness):
                self.slider_brightness.setValue(int(preset.get("brightness", 128)))
            with QSignalBlocker(self.slider_contrast):
                self.slider_contrast.setValue(int(preset.get("contrast", 128)))
            with QSignalBlocker(self.slider_saturation):
                self.slider_saturation.setValue(int(preset.get("saturation", 128)))
            with QSignalBlocker(self.slider_exposure):
                self.slider_exposure.setValue(int(preset.get("exposure", -6)))
            with QSignalBlocker(self.slider_gain):
                self.slider_gain.setValue(int(preset.get("gain", 128)))
            if hasattr(self, "slider_focus") and self.slider_focus:
                with QSignalBlocker(self.slider_focus):
                    self.slider_focus.setValue(int(preset.get("focus", 0)))
            if self.chk_mirror_x:
                self.chk_mirror_x.setChecked(bool(preset.get("mirror_x", False)))
            if self.chk_mirror_y:
                self.chk_mirror_y.setChecked(bool(preset.get("mirror_y", False)))
            if self.chk_auto_exp:
                self.chk_auto_exp.setChecked(bool(preset.get("auto_exposure", True)))
            if self.chk_auto_wb:
                self.chk_auto_wb.setChecked(bool(preset.get("auto_white_balance", True)))
            if hasattr(self, "chk_auto_focus") and self.chk_auto_focus:
                self.chk_auto_focus.setChecked(bool(preset.get("auto_focus", True)))
                self._apply_focus_mode(self._camera_cap_ref, self.chk_auto_focus.isChecked())

            # Apply to device
            self._apply_current_camera_settings(self._camera_cap_ref)
            logger.info(f"Perfil '{name}' carregado e aplicado.")

            # Emit signal
            self.settings_loaded.emit(name, preset)

        except Exception as e:
            QMessageBox.warning(None, "Erro", f"Falha ao carregar perfil: {e}")

    def _export_current_camera_settings(self):
        """Export current camera settings to JSON file."""
        settings = self._gather_camera_settings()
        filepath, _ = QFileDialog.getSaveFileName(None, "Exportar Configuração de Câmera", "", "JSON (*.json)")
        if not filepath:
            return

        try:
            with open(filepath, "w", encoding="utf-8") as fp:
                json.dump(settings, fp, indent=2, ensure_ascii=False)
            logger.info(f"Configuração exportada para {filepath}")
        except Exception as e:
            QMessageBox.warning(None, "Erro", f"Falha ao exportar: {e}")

    def get_mirror_settings(self) -> tuple:
        """
        Get current mirror settings.

        Returns:
            Tuple (mirror_x, mirror_y)
        """
        return self._camera_mirror_x, self._camera_mirror_y
