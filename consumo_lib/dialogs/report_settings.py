"""
dialogs/report_settings.py
--------------------------
Diálogo de configuração de relatórios do sistema.

Permite ao usuário configurar:
- Logo e nome da empresa
- Diretório de saída
- Opções de geração automática
- Cores do tema
"""

from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QPushButton, QLabel, QLineEdit, QCheckBox, QComboBox,
    QFileDialog, QMessageBox, QSpinBox, QTabWidget, QWidget,
    QColorDialog, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QColor, QPalette

from aoi_lib.reports import ReportConfig
from consumo_lib.ui import COLORS, SPACE
from consumo_lib.ui.widget_standards import StandardButton

log = logging.getLogger(__name__)


class ColorButton(QPushButton):
    """Botão para seleção de cor."""

    colorChanged = pyqtSignal(tuple)

    def __init__(self, color: tuple = (41, 128, 185), parent=None):
        super().__init__(parent)
        self._color = color
        self.setFixedSize(60, 30)
        self._update_style()
        self.clicked.connect(self._pick_color)

    def _update_style(self):
        r, g, b = self._color
        # Determinar cor do texto (branco ou preto) baseado na luminosidade
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        text_color = "white" if luminance < 0.5 else "black"
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: rgb({r}, {g}, {b});
                color: {text_color};
                border: 1px solid {COLORS.BORDER};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                border: 2px solid {COLORS.TEXT_PRIMARY};
            }}
        """)
        self.setText(f"#{r:02X}{g:02X}{b:02X}")

    def _pick_color(self):
        current = QColor(*self._color)
        color = QColorDialog.getColor(current, self, "Selecionar Cor")
        if color.isValid():
            self._color = (color.red(), color.green(), color.blue())
            self._update_style()
            self.colorChanged.emit(self._color)

    def get_color(self) -> tuple:
        return self._color

    def set_color(self, color: tuple):
        self._color = color
        self._update_style()


class ReportSettingsDialog(QDialog):
    """
    Diálogo de configuração de relatórios.

    Permite configurar:
    - Identidade visual (logo, nome da empresa)
    - Diretório de saída
    - Opções de geração
    - Cores do tema
    """

    settingsSaved = pyqtSignal(ReportConfig)

    def __init__(self, config: Optional[ReportConfig] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Configurações de Relatórios")
        self.setMinimumWidth(500)

        self.config = config or ReportConfig()
        self._build_ui()
        self._load_config()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Tabs
        tabs = QTabWidget()

        # Tab 1: Identidade Visual
        tab_identity = QWidget()
        identity_layout = QVBoxLayout(tab_identity)

        # Grupo: Empresa
        company_group = QGroupBox("Informações da Empresa")
        company_layout = QFormLayout(company_group)

        self.edit_company_name = QLineEdit()
        self.edit_company_name.setPlaceholderText("Ex: MinhaEmpresa Ltda")
        company_layout.addRow("Nome da Empresa:", self.edit_company_name)

        self.edit_subtitle = QLineEdit()
        self.edit_subtitle.setPlaceholderText("Ex: Sistema de Tensão e Rastreabilidade")
        company_layout.addRow("Subtítulo:", self.edit_subtitle)

        identity_layout.addWidget(company_group)

        # Grupo: Logo
        logo_group = QGroupBox("Logo da Empresa")
        logo_layout = QVBoxLayout(logo_group)

        # Preview do logo
        self.lbl_logo_preview = QLabel()
        self.lbl_logo_preview.setFixedSize(150, 150)
        self.lbl_logo_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_logo_preview.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS.SURFACE};
                border: 2px dashed {COLORS.BORDER};
                border-radius: 8px;
            }}
        """)
        self.lbl_logo_preview.setText("Nenhum logo\nselecionado")

        logo_preview_layout = QHBoxLayout()
        logo_preview_layout.addStretch()
        logo_preview_layout.addWidget(self.lbl_logo_preview)
        logo_preview_layout.addStretch()
        logo_layout.addLayout(logo_preview_layout)

        # Caminho do logo
        logo_path_layout = QHBoxLayout()
        self.edit_logo_path = QLineEdit()
        self.edit_logo_path.setReadOnly(True)
        self.edit_logo_path.setPlaceholderText("Caminho para o arquivo de imagem...")
        logo_path_layout.addWidget(self.edit_logo_path)

        btn_browse_logo = StandardButton("📁 Procurar")
        btn_browse_logo.clicked.connect(self._browse_logo)
        logo_path_layout.addWidget(btn_browse_logo)

        btn_clear_logo = StandardButton("🗑️ Limpar")
        btn_clear_logo.clicked.connect(self._clear_logo)
        logo_path_layout.addWidget(btn_clear_logo)

        logo_layout.addLayout(logo_path_layout)
        identity_layout.addWidget(logo_group)

        identity_layout.addStretch()
        tabs.addTab(tab_identity, "🏢 Identidade Visual")

        # Tab 2: Opções
        tab_options = QWidget()
        options_layout = QVBoxLayout(tab_options)

        # Grupo: Saída
        output_group = QGroupBox("Diretório de Saída")
        output_layout = QHBoxLayout(output_group)

        self.edit_output_dir = QLineEdit()
        self.edit_output_dir.setPlaceholderText("Ex: reports")
        output_layout.addWidget(self.edit_output_dir)

        btn_browse_output = StandardButton("📁 Procurar")
        btn_browse_output.clicked.connect(self._browse_output_dir)
        output_layout.addWidget(btn_browse_output)

        options_layout.addWidget(output_group)

        # Grupo: Opções de Geração
        gen_group = QGroupBox("Opções de Geração")
        gen_layout = QVBoxLayout(gen_group)

        self.chk_auto_generate = QCheckBox("Gerar relatório automaticamente após cada medição")
        self.chk_auto_generate.setToolTip(
            "Se marcado, um PDF será gerado automaticamente após cada medição de tensão.\n"
            "Caso contrário, o usuário pode gerar manualmente quando precisar."
        )
        gen_layout.addWidget(self.chk_auto_generate)

        self.chk_include_charts = QCheckBox("Incluir gráficos nos relatórios")
        self.chk_include_charts.setChecked(True)
        gen_layout.addWidget(self.chk_include_charts)

        self.chk_include_details = QCheckBox("Incluir tabela detalhada de pontos")
        self.chk_include_details.setChecked(True)
        gen_layout.addWidget(self.chk_include_details)

        options_layout.addWidget(gen_group)

        # Grupo: Formato
        format_group = QGroupBox("Formato")
        format_layout = QFormLayout(format_group)

        self.combo_page_size = QComboBox()
        self.combo_page_size.addItems(["A4", "Letter"])
        format_layout.addRow("Tamanho da Página:", self.combo_page_size)

        self.combo_language = QComboBox()
        self.combo_language.addItems(["Português (pt-BR)", "English (en-US)"])
        format_layout.addRow("Idioma:", self.combo_language)

        options_layout.addWidget(format_group)

        options_layout.addStretch()
        tabs.addTab(tab_options, "⚙️ Opções")

        # Tab 3: Cores
        tab_colors = QWidget()
        colors_layout = QVBoxLayout(tab_colors)

        colors_group = QGroupBox("Cores do Tema")
        colors_form = QFormLayout(colors_group)

        self.btn_primary_color = ColorButton((41, 128, 185))
        colors_form.addRow("Cor Primária:", self.btn_primary_color)

        self.btn_success_color = ColorButton((46, 204, 113))
        colors_form.addRow("Cor de Sucesso (OK):", self.btn_success_color)

        self.btn_warning_color = ColorButton((241, 196, 15))
        colors_form.addRow("Cor de Alerta (WARNING):", self.btn_warning_color)

        self.btn_danger_color = ColorButton((231, 76, 60))
        colors_form.addRow("Cor de Erro (NOK):", self.btn_danger_color)

        colors_layout.addWidget(colors_group)

        # Botão para restaurar cores padrão
        btn_reset_colors = StandardButton("🔄 Restaurar Cores Padrão")
        btn_reset_colors.clicked.connect(self._reset_colors)
        colors_layout.addWidget(btn_reset_colors)

        colors_layout.addStretch()
        tabs.addTab(tab_colors, "🎨 Cores")

        layout.addWidget(tabs)

        # Botões de ação
        btn_layout = QHBoxLayout()

        btn_preview = StandardButton("👁️ Visualizar Exemplo")
        btn_preview.clicked.connect(self._preview_report)
        btn_layout.addWidget(btn_preview)

        btn_layout.addStretch()

        btn_cancel = StandardButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_save = StandardButton("💾 Salvar", variant="primary")
        btn_save.setStyleSheet(f"background-color: {COLORS.SUCCESS}; color: white; font-weight: bold;")
        btn_save.clicked.connect(self._save_config)
        btn_layout.addWidget(btn_save)

        layout.addLayout(btn_layout)

    def _load_config(self):
        """Carrega configuração atual nos campos."""
        self.edit_company_name.setText(self.config.company_name)
        self.edit_subtitle.setText(self.config.company_subtitle)
        self.edit_output_dir.setText(self.config.output_dir)

        if self.config.logo_path:
            self.edit_logo_path.setText(self.config.logo_path)
            self._update_logo_preview(self.config.logo_path)

        self.chk_auto_generate.setChecked(self.config.auto_generate_after_measurement)
        self.chk_include_charts.setChecked(self.config.include_charts)
        self.chk_include_details.setChecked(self.config.include_details_table)

        self.combo_page_size.setCurrentText(self.config.page_size)
        lang_text = "Português (pt-BR)" if self.config.language == "pt-BR" else "English (en-US)"
        self.combo_language.setCurrentText(lang_text)

        self.btn_primary_color.set_color(self.config.primary_color)
        self.btn_success_color.set_color(self.config.success_color)
        self.btn_warning_color.set_color(self.config.warning_color)
        self.btn_danger_color.set_color(self.config.danger_color)

    def _browse_logo(self):
        """Abre diálogo para selecionar logo."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Logo",
            "", "Imagens (*.png *.jpg *.jpeg *.bmp *.gif);;Todos (*)"
        )
        if filepath:
            self.edit_logo_path.setText(filepath)
            self._update_logo_preview(filepath)

    def _clear_logo(self):
        """Limpa logo selecionado."""
        self.edit_logo_path.clear()
        self.lbl_logo_preview.setPixmap(QPixmap())
        self.lbl_logo_preview.setText("Nenhum logo\nselecionado")

    def _update_logo_preview(self, filepath: str):
        """Atualiza preview do logo."""
        if filepath and os.path.exists(filepath):
            pixmap = QPixmap(filepath)
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    140, 140,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.lbl_logo_preview.setPixmap(scaled)
                self.lbl_logo_preview.setText("")

    def _browse_output_dir(self):
        """Abre diálogo para selecionar diretório de saída."""
        folder = QFileDialog.getExistingDirectory(
            self, "Selecionar Diretório de Saída",
            self.edit_output_dir.text() or ""
        )
        if folder:
            self.edit_output_dir.setText(folder)

    def _reset_colors(self):
        """Restaura cores padrão."""
        self.btn_primary_color.set_color((41, 128, 185))
        self.btn_success_color.set_color((46, 204, 113))
        self.btn_warning_color.set_color((241, 196, 15))
        self.btn_danger_color.set_color((231, 76, 60))

    def _preview_report(self):
        """Gera relatório de exemplo para preview."""
        from aoi_lib.reports import ReportGenerator

        config = self.get_config()
        generator = ReportGenerator(config)

        # Dados de exemplo
        tension_data = {
            "measurements": [
                {"x": -50, "y": -40, "tension": 28.3, "status": "OK"},
                {"x": 0, "y": 0, "tension": 24.1, "status": "WARNING"},
                {"x": 50, "y": 40, "tension": 22.5, "status": "NOK"},
            ],
            "acceptance_criteria": {
                "ok_min": 26.0, "ok_max": 32.0,
                "warning_low": 24.0, "warning_high": 35.0,
            }
        }

        try:
            path = generator.generate_tension_report(
                tension_data=tension_data,
                stencil_code="EXEMPLO-001",
                stencil_description="Relatório de Exemplo",
                recipe_name="Receita Padrão",
                operator="Operador Teste"
            )

            # Abrir o PDF
            import subprocess
            subprocess.Popen([path], shell=True)

            QMessageBox.information(
                self, "Preview Gerado",
                f"Relatório de exemplo gerado em:\n{path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Erro",
                f"Erro ao gerar preview:\n{str(e)}"
            )

    def _save_config(self):
        """Salva configuração."""
        # Validar
        if not self.edit_company_name.text().strip():
            QMessageBox.warning(
                self, "Aviso",
                "Informe o nome da empresa."
            )
            return

        config = self.get_config()
        self.config = config
        self.settingsSaved.emit(config)
        self.accept()

    def get_config(self) -> ReportConfig:
        """Retorna configuração atual baseada nos campos."""
        lang = "pt-BR" if "Português" in self.combo_language.currentText() else "en-US"

        logo_path = self.edit_logo_path.text().strip()
        if logo_path and not os.path.exists(logo_path):
            logo_path = None

        return ReportConfig(
            company_name=self.edit_company_name.text().strip() or "SeuStencil",
            company_subtitle=self.edit_subtitle.text().strip() or "Sistema de Tensão e Rastreabilidade",
            logo_path=logo_path,
            output_dir=self.edit_output_dir.text().strip() or "reports",
            include_charts=self.chk_include_charts.isChecked(),
            include_details_table=self.chk_include_details.isChecked(),
            auto_generate_after_measurement=self.chk_auto_generate.isChecked(),
            page_size=self.combo_page_size.currentText(),
            language=lang,
            primary_color=self.btn_primary_color.get_color(),
            success_color=self.btn_success_color.get_color(),
            warning_color=self.btn_warning_color.get_color(),
            danger_color=self.btn_danger_color.get_color(),
        )


# ============================================================================
#  EXEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    dialog = ReportSettingsDialog()
    if dialog.exec() == QDialog.DialogCode.Accepted:
        config = dialog.get_config()
        print(f"Configuração salva: {config.company_name}")

    sys.exit(0)
