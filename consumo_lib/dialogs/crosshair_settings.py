"""
dialogs/crosshair_settings.py
-----------------------------
Diálogo para configurar a aparência da cruz de centralização da câmera.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
    QSpinBox, QPushButton, QLabel, QColorDialog
)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt


class CrosshairSettingsDialog(QDialog):
    """Diálogo para configurar a cruz de centralização da câmera."""

    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.cfg = config_manager
        self.setWindowTitle("Configurações da Cruz de Centralização")
        self.setMinimumWidth(400)

        self._build_ui()
        self._load_current_values()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Instruções
        info = QLabel(
            "Configure a aparência da cruz de centralização exibida no preview da câmera.\n"
            "Use uma linha mais longa para facilitar as calibrações."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(info)

        # Grupo de configurações
        group = QGroupBox("Aparência da Cruz")
        form = QFormLayout(group)

        # Cor
        color_layout = QHBoxLayout()
        self.color_preview = QLabel("      ")
        self.color_preview.setStyleSheet("background-color: red; border: 1px solid black;")
        self.color_preview.setFixedSize(50, 25)
        color_layout.addWidget(self.color_preview)

        self.btn_choose_color = QPushButton("Escolher Cor...")
        self.btn_choose_color.clicked.connect(self._choose_color)
        color_layout.addWidget(self.btn_choose_color)
        color_layout.addStretch()

        form.addRow("Cor da linha:", color_layout)

        # Espessura
        self.spin_thickness = QSpinBox()
        self.spin_thickness.setRange(1, 10)
        self.spin_thickness.setSuffix(" px")
        self.spin_thickness.setToolTip("Espessura da linha em pixels (1-10)")
        form.addRow("Espessura:", self.spin_thickness)

        # Comprimento (percentual da menor dimensão)
        self.spin_length = QSpinBox()
        self.spin_length.setRange(1, 50)
        self.spin_length.setSuffix(" %")
        self.spin_length.setToolTip("Comprimento da linha como percentual da menor dimensão da imagem (1-50%)")
        form.addRow("Comprimento:", self.spin_length)

        layout.addWidget(group)

        # Dica
        tip = QLabel(
            "💡 Dica: Use linhas mais longas (15-25%) e mais espessas (3-5px) "
            "para facilitar a calibração FOV com régua."
        )
        tip.setWordWrap(True)
        tip.setStyleSheet("color: #888; font-size: 11px; margin-top: 10px;")
        layout.addWidget(tip)

        # Botões
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_reset = QPushButton("Restaurar Padrão")
        btn_reset.clicked.connect(self._reset_to_default)
        btn_layout.addWidget(btn_reset)

        btn_save = QPushButton("Salvar")
        btn_save.clicked.connect(self._save)
        btn_layout.addWidget(btn_save)

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        layout.addLayout(btn_layout)

        # Armazena valores RGB atuais
        self.current_r = 0
        self.current_g = 0
        self.current_b = 255

    def _load_current_values(self):
        """Carrega valores atuais do config."""
        crosshair = self.cfg.get("camera", "crosshair", default={})

        self.current_r = crosshair.get("color_r", 0)
        self.current_g = crosshair.get("color_g", 0)
        self.current_b = crosshair.get("color_b", 255)

        self.spin_thickness.setValue(crosshair.get("thickness", 2))
        self.spin_length.setValue(crosshair.get("length_percent", 5))

        self._update_color_preview()

    def _update_color_preview(self):
        """Atualiza a preview da cor."""
        color = QColor(self.current_r, self.current_g, self.current_b)
        self.color_preview.setStyleSheet(
            f"background-color: {color.name()}; border: 1px solid black;"
        )

    def _choose_color(self):
        """Abre diálogo de seleção de cor."""
        initial = QColor(self.current_r, self.current_g, self.current_b)
        color = QColorDialog.getColor(initial, self, "Escolher Cor da Cruz")

        if color.isValid():
            self.current_r = color.red()
            self.current_g = color.green()
            self.current_b = color.blue()
            self._update_color_preview()

    def _reset_to_default(self):
        """Restaura valores padrão."""
        self.current_r = 0
        self.current_g = 0
        self.current_b = 255
        self.spin_thickness.setValue(2)
        self.spin_length.setValue(5)
        self._update_color_preview()

    def _save(self):
        """Salva configurações."""
        self.cfg.set("camera", "crosshair", "color_r", value=self.current_r)
        self.cfg.set("camera", "crosshair", "color_g", value=self.current_g)
        self.cfg.set("camera", "crosshair", "color_b", value=self.current_b)
        self.cfg.set("camera", "crosshair", "thickness", value=self.spin_thickness.value())
        self.cfg.set("camera", "crosshair", "length_percent", value=self.spin_length.value())

        self.accept()
