"""
confirm_save_widget.py
-----------------------

Widget de confirmação e salvamento para o fluxo de engenharia.

Aba 7 do wizard - Exibe resumo completo do programa e permite salvar.

Autor: Claude Code (Sonnet 4.5)
Data: 2026-01-13
"""

import logging
from typing import Optional, Dict, Any
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QScrollArea, QLabel, QPushButton, QGroupBox,
    QTextEdit, QCheckBox, QSpinBox, QMessageBox,
    QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal

# Design System
from consumo_lib.ui import COLORS, TYPO, SPACE, DIM

from consumo_lib.models.engineering.program_config import ProgramConfig

logger = logging.getLogger(__name__)


class SummaryCard(QGroupBox):
    """
    Card para exibir informações resumidas do programa.
    """

    def __init__(self, title: str, parent=None):
        super().__init__(title, parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Label para conteúdo
        self.content_label = QLabel()
        self.content_label.setWordWrap(True)
        self.content_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        layout.addWidget(self.content_label)

    def set_content(self, text: str):
        """Define conteúdo do card."""
        self.content_label.setText(text)

    def set_html(self, html: str):
        """Define conteúdo HTML do card."""
        self.content_label.setText(html)
        self.content_label.setTextFormat(Qt.TextFormat.RichText)


class WarningPanel(QWidget):
    """
    Painel para exibir avisos e alertas de validação.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.warnings = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel()
        self.label.setWordWrap(True)
        self.label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(self.label)

    def set_warnings(self, warnings: list[str]):
        """Define lista de avisos."""
        self.warnings = warnings
        if not warnings:
            self.label.setText(f"""
                <div style='background-color: {COLORS.SUCCESS}; color: {COLORS.TEXT_PRIMARY};
                            padding: {SPACE.XS}px; border-radius: {DIM.RADIUS_SM}px;'>
                    ✓ Nenhum avio - Programa válido
                </div>
            """)
        else:
            html = f"<div style='background-color: {COLORS.WARNING_LIGHT}; padding: {SPACE.XS}px; border-radius: {DIM.RADIUS_SM}px;'>"
            html += "<b>⚠ Avisos:</b><ul>"
            for warning in warnings:
                html += f"<li>{warning}</li>"
            html += "</ul></div>"
            self.label.setText(html)


class ConfirmSaveWidget(QWidget):
    """
    Widget de confirmação e salvamento (Aba 7 do Wizard).

    Funcionalidades:
    - Resumo completo do programa
    - Validação de dados
    - Exibição de avisos
    - Estimativa de tempo de execução
    - Salvamento do programa
    - Opção de testar inspeção

    Signals:
        save_requested: Emitido quando usuário clica em salvar
        test_requested: Emitido quando usuário clica em testar
        back_requested: Emitido quando usuário clica em voltar
    """

    save_requested = pyqtSignal(object)  # ProgramConfig
    test_requested = pyqtSignal(object)  # ProgramConfig
    back_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.program_config: Optional[ProgramConfig] = None
        self.is_base_program = False
        self.setup_ui()

    def setup_ui(self):
        """Inicializa interface do usuário."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Título
        title = QLabel("Confirmar e Salvar Programa")
        title.setFont(TYPO.get_font(TYPO.HEADLINE_LARGE, bold=True))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # ScrollArea para conteúdo
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(12)

        # Painel de avisos
        self.warning_panel = WarningPanel()
        scroll_layout.addWidget(self.warning_panel)

        # Grid de cards de resumo
        grid_layout = QGridLayout()
        grid_layout.setSpacing(12)

        # Card 1: Dados do Programa
        self.program_card = SummaryCard("📋 Dados do Programa")
        grid_layout.addWidget(self.program_card, 0, 0)

        # Card 2: Gerber
        self.gerber_card = SummaryCard("📁 Arquivo Gerber")
        grid_layout.addWidget(self.gerber_card, 0, 1)

        # Card 3: Fiduciais
        self.fiducials_card = SummaryCard("🎯 Fiduciais")
        grid_layout.addWidget(self.fiducials_card, 1, 0)

        # Card 4: Mosaico
        self.mosaic_card = SummaryCard("📷 Mosaico Capturado")
        grid_layout.addWidget(self.mosaic_card, 1, 1)

        # Card 5: Alinhamento
        self.alignment_card = SummaryCard("🔄 Alinhamento")
        grid_layout.addWidget(self.alignment_card, 2, 0)

        # Card 6: Janelas de Inspeção
        self.inspection_card = SummaryCard("🔍 Janelas de Inspeção")
        grid_layout.addWidget(self.inspection_card, 2, 1)

        # Card 7: Estimativas
        self.estimates_card = SummaryCard("⏱️ Estimativas de Execução")
        grid_layout.addWidget(self.estimates_card, 3, 0, 1, 2)

        scroll_layout.addLayout(grid_layout)
        scroll_layout.addStretch()

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, 1)

        # Opções de salvamento
        options_group = QGroupBox("Opções de Salvamento")
        options_layout = QHBoxLayout(options_group)

        self.base_program_checkbox = QCheckBox("Salvar como Programa Base")
        self.base_program_checkbox.setToolTip(
            "Programas Base não são associados a stencil específico "
            "e podem ser reutilizados."
        )
        self.base_program_checkbox.toggled.connect(self._on_base_program_toggled)
        options_layout.addWidget(self.base_program_checkbox)

        layout.addWidget(options_group)

        # Campo de código do stencil (para programas específicos)
        stencil_code_layout = QHBoxLayout()
        stencil_code_layout.addWidget(QLabel("Código do Stencil:"))
        self.stencil_code_edit = QLabel()  # Readonly, vindo da aba 1
        self.stencil_code_edit.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.stencil_code_edit.setStyleSheet(f"font-weight: bold; color: {COLORS.PRIMARY_DARK};")
        stencil_code_layout.addWidget(self.stencil_code_edit)
        stencil_code_layout.addStretch()
        layout.addLayout(stencil_code_layout)

        # Botões de ação
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)

        self.back_button = QPushButton("← Voltar")
        self.back_button.clicked.connect(self._on_back_clicked)
        buttons_layout.addWidget(self.back_button)

        buttons_layout.addStretch()

        self.test_button = QPushButton("🧪 Testar Inspeção")
        self.test_button.setToolTip(
            "Executa uma inspeção piloto para validar o programa "
            "(opcional, requer hardware conectado)"
        )
        self.test_button.clicked.connect(self._on_test_clicked)
        buttons_layout.addWidget(self.test_button)

        self.save_button = QPushButton("💾 Salvar Programa")
        self.save_button.setMinimumHeight(DIM.BUTTON_HEIGHT_LG)
        self.save_button.setFont(TYPO.get_font(TYPO.BODY_MEDIUM, bold=True))
        self.save_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.SUCCESS};
                color: {COLORS.TEXT_PRIMARY};
                border-radius: {DIM.RADIUS_SM}px;
                padding: {SPACE.SM}px {SPACE.MD}px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.SUCCESS_DARK};
            }}
            QPushButton:disabled {{
                background-color: {COLORS.SURFACE};
                color: {COLORS.TEXT_HINT};
            }}
        """)
        self.save_button.clicked.connect(self._on_save_clicked)
        self.save_button.setEnabled(False)  # Initially disabled
        buttons_layout.addWidget(self.save_button)

        layout.addLayout(buttons_layout)

    def set_program_config(self, config: ProgramConfig):
        """
        Define configuração do programa e atualiza UI.

        Args:
            config: ProgramConfig com todos os dados das abas anteriores
        """
        self.program_config = config
        self._update_display()

    def _update_display(self):
        """Atualiza todos os cards com dados do programa."""
        if not self.program_config:
            logger.warning("ProgramConfig não definido")
            return

        config = self.program_config
        summary = config.get_summary()

        # Validação
        is_valid, errors = config.validate()
        self.warning_panel.set_warnings(errors)

        # Atualiza código do stencil
        self.stencil_code_edit.setText(config.stencil_code)

        # Card 1: Dados do Programa
        program_html = f"""
            <b>Nome:</b> {config.program_name}<br>
            <b>Versão:</b> {config.version}<br>
            <b>Descrição:</b> {config.description or "N/A"}<br>
            <b>Receita Base:</b> {config.recipe_name or "N/A"}<br>
            <b>Criado em:</b> {config.created_at[:19].replace('T', ' ')}<br>
            <b>Criado por:</b> {config.created_by or "N/A"}
        """
        self.program_card.set_html(program_html)

        # Card 2: Gerber
        gerber_name = Path(config.gerber_file).name if config.gerber_file else "N/A"
        gerber_html = f"""
            <b>Arquivo:</b> {gerber_name}<br>
            <b>Dimensões:</b> {config.gerber_dimensions.get('width', 0):.1f} ×
            {config.gerber_dimensions.get('height', 0):.1f} mm<br>
            <b>Apertures:</b> {config.aperture_count}<br>
            <b>Fiduciais detectados:</b> {config.detected_fiducials}
        """
        self.gerber_card.set_html(gerber_html)

        # Card 3: Fiduciais
        fiducials_html = f"""
            <b>Fiducial 1:</b> ({config.fiducials.fiducial1['x']:.1f},
            {config.fiducials.fiducial1['y']:.1f}) mm<br>
            <b>Fiducial 2:</b> ({config.fiducials.fiducial2['x']:.1f},
            {config.fiducials.fiducial2['y']:.1f}) mm<br>
            <b>Template 1:</b> {config.fiducials.template1_path or "N/A"}<br>
            <b>Template 2:</b> {config.fiducials.template2_path or "N/A"}
        """
        self.fiducials_card.set_html(fiducials_html)

        # Card 4: Mosaico
        mosaic = config.mosaic
        mosaic_html = f"""
            <b>Grid:</b> {mosaic.grid_rows}×{mosaic.grid_cols}<br>
            <b>Total FOVs:</b> {mosaic.total_fovs}<br>
            <b>Canto 1:</b> ({mosaic.corner1['x']:.1f}, {mosaic.corner1['y']:.1f}) mm<br>
            <b>Canto 2:</b> ({mosaic.corner2['x']:.1f}, {mosaic.corner2['y']:.1f}) mm<br>
            <b>Delay:</b> {mosaic.capture_delay_ms} ms
        """
        self.mosaic_card.set_html(mosaic_html)

        # Card 5: Alinhamento
        alignment = config.alignment
        score_color = COLORS.SUCCESS if alignment.alignment_score >= 70 else COLORS.WARNING
        alignment_html = f"""
            <b>Translação X:</b> {alignment.translation_x:.2f} mm<br>
            <b>Translação Y:</b> {alignment.translation_y:.2f} mm<br>
            <b>Rotação:</b> {alignment.rotation:.2f}°<br>
            <b>Escala:</b> {alignment.scale:.3f}<br>
            <b>Score:</b> <span style='color: {score_color}; font-weight: bold;'>
            {alignment.alignment_score:.1f}%</span>
        """
        self.alignment_card.set_html(alignment_html)

        # Card 6: Janelas de Inspeção
        inspection = summary['inspection']
        inspection_html = f"""
            <b>Total de Grupos:</b> {inspection['total_groups']}<br>
            <b>Configurados:</b> {inspection['configured_groups']}<br>
            <b>Confirmados:</b> {inspection['confirmed_groups']}<br>
            <b>Total Aberturas:</b> {inspection['total_apertures']}
        """
        self.inspection_card.set_html(inspection_html)

        # Card 7: Estimativas
        estimates = summary['execution_time']
        estimates_html = f"""
            <b>Tempo Total:</b> ~{estimates['total_minutes']:.1f} min
            ({estimates['total_seconds']:.0f} s)<br>
            <b>Captura FOVs:</b> {estimates['fov_capture_time']:.0f} s<br>
            <b>Inspeção:</b> {estimates['inspection_time']:.1f} s<br>
            <b>Alinhamento:</b> {estimates['alignment_time']:.0f} s<br>
            <b>Relatório:</b> {estimates['report_time']:.0f} s
        """
        self.estimates_card.set_html(estimates_html)

        # Habilita/desabilita botão salvar
        self.save_button.setEnabled(is_valid)

    def _on_base_program_toggled(self, checked: bool):
        """
        Usuário alterou checkbox de programa base.

        Args:
            checked: True se marcado
        """
        self.is_base_program = checked
        # Para programas base, código do stencil é N/A
        if checked:
            self.stencil_code_edit.setText("N/A (Programa Base)")

    def _on_save_clicked(self):
        """Usuário clicou em Salvar."""
        if not self.program_config:
            QMessageBox.warning(self, "Erro", "Nenhum programa configurado.")
            return

        # Valida novamente
        is_valid, errors = self.program_config.validate()
        if not is_valid:
            msg = "<b>Programa contém erros:</b><ul>"
            for error in errors:
                msg += f"<li>{error}</li>"
            msg += "</ul><br>Deseja salvar mesmo assim?"
            reply = QMessageBox.question(
                self,
                "Salvar com erros?",
                msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return

        # Se for programa base, ajusta código do stencil
        if self.is_base_program:
            self.program_config.stencil_code = "BASE"

        # Confirmação
        summary = self.program_config.get_summary()
        msg = f"""
            <h3>Confirmar Salvamento</h3>
            <p>O programa será salvo com as seguintes informações:</p>
            <ul>
                <li><b>Stencil:</b> {self.program_config.stencil_code}</li>
                <li><b>Programa:</b> {self.program_config.program_name}</li>
                <li><b>Versão:</b> {self.program_config.version}</li>
                <li><b>Aberturas:</b> {summary['inspection']['total_apertures']}</li>
                <li><b>Tempo estimado:</b> ~{summary['execution_time']['total_minutes']:.1f} min</li>
            </ul>
            <p><b>Local:</b> {self.program_config.get_file_path()}</p>
            <p>Deseja salvar?</p>
        """
        reply = QMessageBox.question(
            self,
            "Confirmar Salvamento",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )

        if reply == QMessageBox.StandardButton.Yes:
            logger.info(f"Salvando programa: {self.program_config.program_name}")
            self.save_requested.emit(self.program_config)

    def _on_test_clicked(self):
        """Usuário clicou em Testar Inspeção."""
        if not self.program_config:
            QMessageBox.warning(self, "Erro", "Nenhum programa configurado.")
            return

        # Valida antes de testar
        is_valid, errors = self.program_config.validate()
        if not is_valid:
            msg = "<b>Programa contém erros:</b><ul>"
            for error in errors:
                msg += f"<li>{error}</li>"
            msg += "</ul>Corrija os erros antes de testar."
            QMessageBox.warning(self, "Erros de Validação", msg)
            return

        # Confirmação
        reply = QMessageBox.question(
            self,
            "Testar Inspeção",
            """
            <h3>Executar Inspeção de Teste?</h3>
            <p>Isso irá executar uma inspeção completa usando este programa.</p>
            <p><b>Requisitos:</b></p>
            <ul>
                <li>PLC conectado</li>
                <li>Câmera conectada</li>
                <li>Stencil posicionado</li>
            </ul>
            <p>Deseja continuar?</p>
            """,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            logger.info(f"Testando programa: {self.program_config.program_name}")
            self.test_requested.emit(self.program_config)

    def _on_back_clicked(self):
        """Usuário clicou em Voltar."""
        self.back_requested.emit()

    def get_program_config(self) -> Optional[ProgramConfig]:
        """
        Retorna configuração do programa atual.

        Returns:
            ProgramConfig ou None se não configurado
        """
        return self.program_config

    def is_ready_to_save(self) -> bool:
        """
        Verifica se programa está pronto para salvar.

        Returns:
            True se válido
        """
        if not self.program_config:
            return False
        is_valid, _ = self.program_config.validate()
        return is_valid
