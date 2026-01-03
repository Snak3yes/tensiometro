"""
dialogs/inspection_settings.py
-------------------------------
Diálogo de configuração dos parâmetros de inspeção visual.

Permite que a engenharia ajuste:
- Thresholds de classificação (OK, PARTIAL, BLOCKED)
- Métodos de binarização
- Parâmetros de pré-processamento
"""

from __future__ import annotations

import logging
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QPushButton, QLabel, QDoubleSpinBox, QSpinBox, QComboBox,
    QCheckBox, QMessageBox, QSlider, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal

from aoi_lib.stencil_inspector import InspectionThresholds

log = logging.getLogger(__name__)


class InspectionSettingsDialog(QDialog):
    """
    Diálogo para configuração dos parâmetros de inspeção visual.

    Permite ajustar thresholds e parâmetros de binarização.
    """

    settingsSaved = pyqtSignal(InspectionThresholds)

    def __init__(
        self,
        thresholds: Optional[InspectionThresholds] = None,
        parent=None
    ):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Parâmetros de Inspeção Visual")
        self.setMinimumWidth(450)

        self.thresholds = thresholds or InspectionThresholds()
        self._build_ui()
        self._load_values()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # =====================================================
        # Grupo: Classificação de Aberturas
        # =====================================================
        class_group = QGroupBox("🎯 Classificação de Aberturas")
        class_layout = QFormLayout(class_group)

        # Threshold OK
        self.spin_ok = QDoubleSpinBox()
        self.spin_ok.setRange(50, 100)
        self.spin_ok.setSuffix(" %")
        self.spin_ok.setDecimals(1)
        self.spin_ok.setToolTip(
            "Porcentagem mínima de área livre para considerar abertura OK.\n"
            "Valor padrão: 90%"
        )
        class_layout.addRow("✅ Threshold OK (≥):", self.spin_ok)

        # Threshold PARTIAL
        self.spin_partial = QDoubleSpinBox()
        self.spin_partial.setRange(0, 99)
        self.spin_partial.setSuffix(" %")
        self.spin_partial.setDecimals(1)
        self.spin_partial.setToolTip(
            "Porcentagem mínima para considerar obstrução PARCIAL.\n"
            "Abaixo deste valor = BLOQUEADA.\n"
            "Valor padrão: 70%"
        )
        class_layout.addRow("⚠️ Threshold PARTIAL (≥):", self.spin_partial)

        # Info
        info_label = QLabel(
            "<small><i>Aberturas com área livre abaixo do threshold PARTIAL "
            "são consideradas BLOQUEADAS.</i></small>"
        )
        info_label.setWordWrap(True)
        class_layout.addRow(info_label)

        layout.addWidget(class_group)

        # =====================================================
        # Grupo: Binarização de Imagem
        # =====================================================
        bin_group = QGroupBox("🔲 Binarização de Imagem")
        bin_layout = QFormLayout(bin_group)

        # Método
        self.combo_method = QComboBox()
        self.combo_method.addItems(["Otsu (Automático)", "Adaptativo", "Fixo"])
        self.combo_method.setToolTip(
            "Método de binarização:\n"
            "- Otsu: Calcula threshold automaticamente (recomendado)\n"
            "- Adaptativo: Calcula por região (bom para iluminação desigual)\n"
            "- Fixo: Usa valor fixo definido abaixo"
        )
        self.combo_method.currentIndexChanged.connect(self._on_method_changed)
        bin_layout.addRow("Método:", self.combo_method)

        # Threshold fixo
        self.spin_fixed = QSpinBox()
        self.spin_fixed.setRange(0, 255)
        self.spin_fixed.setToolTip("Valor de threshold para binarização fixa (0-255)")
        bin_layout.addRow("Threshold Fixo:", self.spin_fixed)

        # Bloco adaptativo
        self.spin_block = QSpinBox()
        self.spin_block.setRange(3, 51)
        self.spin_block.setSingleStep(2)
        self.spin_block.setToolTip("Tamanho do bloco para binarização adaptativa (ímpar)")
        bin_layout.addRow("Tamanho do Bloco:", self.spin_block)

        # Constante C
        self.spin_c = QSpinBox()
        self.spin_c.setRange(-20, 20)
        self.spin_c.setToolTip("Constante subtraída do threshold adaptativo")
        bin_layout.addRow("Constante (C):", self.spin_c)

        layout.addWidget(bin_group)

        # =====================================================
        # Grupo: Pré-processamento
        # =====================================================
        pre_group = QGroupBox("🔧 Pré-processamento")
        pre_layout = QFormLayout(pre_group)

        # Blur
        self.spin_blur = QSpinBox()
        self.spin_blur.setRange(1, 15)
        self.spin_blur.setSingleStep(2)
        self.spin_blur.setToolTip(
            "Tamanho do kernel Gaussian Blur para reduzir ruído.\n"
            "Use 1 para desabilitar."
        )
        pre_layout.addRow("Kernel de Blur:", self.spin_blur)

        # Morphology
        self.chk_morphology = QCheckBox("Aplicar operações morfológicas")
        self.chk_morphology.setToolTip(
            "Aplica abertura/fechamento morfológico para limpar a máscara."
        )
        pre_layout.addRow(self.chk_morphology)

        self.spin_morph = QSpinBox()
        self.spin_morph.setRange(1, 11)
        self.spin_morph.setSingleStep(2)
        self.spin_morph.setToolTip("Tamanho do kernel morfológico")
        pre_layout.addRow("Kernel Morfológico:", self.spin_morph)

        layout.addWidget(pre_group)

        # =====================================================
        # Grupo: Filtros
        # =====================================================
        filter_group = QGroupBox("📐 Filtros")
        filter_layout = QFormLayout(filter_group)

        self.spin_min_area = QSpinBox()
        self.spin_min_area.setRange(1, 1000)
        self.spin_min_area.setSuffix(" px²")
        self.spin_min_area.setToolTip(
            "Aberturas menores que esta área (em pixels) são ignoradas."
        )
        filter_layout.addRow("Área mínima de abertura:", self.spin_min_area)

        layout.addWidget(filter_group)

        # =====================================================
        # Botões
        # =====================================================
        layout.addStretch()

        btn_layout = QHBoxLayout()

        btn_default = QPushButton("🔄 Restaurar Padrão")
        btn_default.clicked.connect(self._restore_defaults)
        btn_layout.addWidget(btn_default)

        btn_layout.addStretch()

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_save = QPushButton("💾 Salvar")
        btn_save.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        btn_save.clicked.connect(self._save)
        btn_layout.addWidget(btn_save)

        layout.addLayout(btn_layout)

    def _load_values(self):
        """Carrega valores do objeto thresholds nos campos."""
        self.spin_ok.setValue(self.thresholds.ok_threshold)
        self.spin_partial.setValue(self.thresholds.partial_threshold)

        # Método de binarização
        method_map = {"otsu": 0, "adaptive": 1, "fixed": 2}
        self.combo_method.setCurrentIndex(method_map.get(self.thresholds.bin_method, 0))

        self.spin_fixed.setValue(self.thresholds.bin_fixed_threshold)
        self.spin_block.setValue(self.thresholds.bin_adaptive_block)
        self.spin_c.setValue(self.thresholds.bin_adaptive_c)

        self.spin_blur.setValue(self.thresholds.blur_kernel_size)
        self.chk_morphology.setChecked(self.thresholds.apply_morphology)
        self.spin_morph.setValue(self.thresholds.morphology_kernel_size)

        self.spin_min_area.setValue(self.thresholds.min_aperture_area_px)

        self._on_method_changed()

    def _on_method_changed(self):
        """Habilita/desabilita campos baseado no método selecionado."""
        method = self.combo_method.currentIndex()

        self.spin_fixed.setEnabled(method == 2)  # Fixo
        self.spin_block.setEnabled(method == 1)  # Adaptativo
        self.spin_c.setEnabled(method == 1)

    def _restore_defaults(self):
        """Restaura valores padrão."""
        self.thresholds = InspectionThresholds()
        self._load_values()
        QMessageBox.information(
            self, "Padrão Restaurado",
            "Os valores padrão foram restaurados.\n"
            "Clique em Salvar para confirmar."
        )

    def _save(self):
        """Valida e salva configurações."""
        # Validar
        if self.spin_ok.value() <= self.spin_partial.value():
            QMessageBox.warning(
                self, "Validação",
                "O threshold OK deve ser maior que o threshold PARTIAL."
            )
            return

        # Criar objeto
        method_map = {0: "otsu", 1: "adaptive", 2: "fixed"}

        self.thresholds = InspectionThresholds(
            ok_threshold=self.spin_ok.value(),
            partial_threshold=self.spin_partial.value(),
            bin_method=method_map[self.combo_method.currentIndex()],
            bin_fixed_threshold=self.spin_fixed.value(),
            bin_adaptive_block=self.spin_block.value(),
            bin_adaptive_c=self.spin_c.value(),
            blur_kernel_size=self.spin_blur.value(),
            apply_morphology=self.chk_morphology.isChecked(),
            morphology_kernel_size=self.spin_morph.value(),
            min_aperture_area_px=self.spin_min_area.value()
        )

        self.settingsSaved.emit(self.thresholds)
        self.accept()

    def get_thresholds(self) -> InspectionThresholds:
        """Retorna os thresholds configurados."""
        return self.thresholds


# ============================================================================
#  EXEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    dialog = InspectionSettingsDialog()
    if dialog.exec() == QDialog.DialogCode.Accepted:
        thresholds = dialog.get_thresholds()
        print(f"OK threshold: {thresholds.ok_threshold}%")
        print(f"PARTIAL threshold: {thresholds.partial_threshold}%")
        print(f"Method: {thresholds.bin_method}")

    sys.exit(0)
