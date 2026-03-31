"""
Diálogo para Salvar Padrão de Medição de Tensão

Diálogo modal para o usuário salvar configurações atuais como padrão reutilizável.

Author: Claude
Created: 2026-03-31
"""

import logging
from typing import Optional, Tuple

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPlainTextEdit, QMessageBox,
    QGroupBox
)

from consumo_lib.ui import COLORS, TYPO, SPACE, DIM
from consumo_lib.ui.widget_standards import StandardButton

logger = logging.getLogger(__name__)


class SavePatternDialog(QDialog):
    """
    Diálogo para salvar configurações de medição como padrão.

    Permite ao usuário:
    - Nomear o padrão
    - Adicionar descrição
    - Visualizar resumo das configurações
    - Salvar o padrão

    Exemplo:
        >>> dialog = SavePatternDialog(parent, start_point=(0, 0), end_point=(100, 100), ...)
        >>> if dialog.exec() == QDialog.DialogCode.Accepted:
        ...     name, description = dialog.get_pattern_data()
    """

    def __init__(
        self,
        parent=None,
        start_point: Tuple[float, float] = (0.0, 0.0),
        end_point: Tuple[float, float] = (100.0, 100.0),
        grid_size: int = 3,
        z_height: float = 5.0,
        z_move: float = 10.0,
        stabilization_time_ms: int = 500,
        feed_rate: float = 1000.0
    ):
        """
        Inicializa diálogo.

        Args:
            parent: Widget pai
            start_point: Ponto inicial (x, y) em mm
            end_point: Ponto final (x, y) em mm
            grid_size: Tamanho do grid NxN
            z_height: Altura de medição Z em mm
            z_move: Altura de movimento Z em mm
            stabilization_time_ms: Tempo de estabilização em ms
            feed_rate: Velocidade de movimento em mm/min
        """
        super().__init__(parent)
        self.setWindowTitle("Salvar Padrão de Medição")
        self.setMinimumSize(500, 400)
        self.setModal(True)

        # Parâmetros de medição
        self.start_point = start_point
        self.end_point = end_point
        self.grid_size = grid_size
        self.z_height = z_height
        self.z_move = z_move
        self.stabilization_time_ms = stabilization_time_ms
        self.feed_rate = feed_rate

        # Resultado
        self.pattern_name: Optional[str] = None
        self.pattern_description: Optional[str] = None

        self._build_ui()

    def _build_ui(self):
        """Constrói interface do usuário."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(SPACE.MD)
        main_layout.setContentsMargins(SPACE.MD, SPACE.MD, SPACE.MD, SPACE.MD)

        # ==================== IDENTIFICAÇÃO ====================
        id_group = QGroupBox("Identificação do Padrão")
        id_layout = QGridLayout(id_group)
        id_layout.setSpacing(SPACE.SM)

        # Nome
        id_layout.addWidget(QLabel("Nome:"), 0, 0)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ex: padrão 3x3, padrão pequeno, ...")
        self.name_input.setFont(TYPO.get_font(TYPO.BODY_MEDIUM))
        id_layout.addWidget(self.name_input, 0, 1)

        # Descrição
        id_layout.addWidget(QLabel("Descrição:"), 1, 0)
        self.desc_input = QPlainTextEdit()
        self.desc_input.setPlaceholderText("Descrição opcional do padrão...")
        self.desc_input.setMaximumHeight(60)
        self.desc_input.setFont(TYPO.get_font(TYPO.BODY_SMALL))
        id_layout.addWidget(self.desc_input, 1, 1)

        main_layout.addWidget(id_group)

        # ==================== RESUMO DAS CONFIGURAÇÕES ====================
        summary_group = QGroupBox("Resumo das Configurações")
        summary_layout = QGridLayout(summary_group)
        summary_layout.setSpacing(SPACE.SM)

        # Linha 1: Grid
        summary_layout.addWidget(
            QLabel(f"Grid: {self.grid_size}x{self.grid_size} ({self.grid_size ** 2} pontos)"),
            0, 0
        )

        # Linha 2: Área
        area_width = self.end_point[0] - self.start_point[0]
        area_height = self.end_point[1] - self.start_point[1]
        summary_layout.addWidget(
            QLabel(f"Área: {area_width:.1f} x {area_height:.1f} mm"),
            0, 1
        )

        # Linha 3: Ponto inicial
        summary_layout.addWidget(
            QLabel(f"Início: ({self.start_point[0]:.2f}, {self.start_point[1]:.2f}) mm"),
            1, 0
        )

        # Linha 4: Ponto final
        summary_layout.addWidget(
            QLabel(f"Fim: ({self.end_point[0]:.2f}, {self.end_point[1]:.2f}) mm"),
            1, 1
        )

        # Linha 5: Alturas Z
        summary_layout.addWidget(
            QLabel(f"Altura Medição: {self.z_height:.2f} mm | Movimento: {self.z_move:.2f} mm"),
            2, 0, 1, 2
        )

        # Linha 6: Outros
        summary_layout.addWidget(
            QLabel(f"Estabilização: {self.stabilization_time_ms}ms | Feed: {self.feed_rate:.0f} mm/min"),
            3, 0, 1, 2
        )

        # Estilo do resumo
        for i in range(summary_layout.count()):
            widget = summary_layout.itemAt(i).widget()
            if widget:
                widget.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; font-size: {TYPO.LABEL_SMALL}px;")

        main_layout.addWidget(summary_group)

        # ==================== NOTAS/INSTRUÇÕES ====================
        notes_label = QLabel(
            "ℹ️ O padrão será salvo e poderá ser reutilizado em futuras medições. "
            "Os critérios de aceitação são globais e configurados separadamente."
        )
        notes_label.setWordWrap(True)
        notes_label.setStyleSheet(
            f"color: {COLORS.TEXT_HINT}; font-size: {TYPO.LABEL_SMALL}px; "
            f"background-color: {COLORS.SURFACE_VARIANT}; padding: {SPACE.SM}px; "
            f"border-radius: {DIM.RADIUS_SM}px;"
        )
        main_layout.addWidget(notes_label)

        # ==================== BOTÕES ====================
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        # Cancelar
        self.btn_cancel = StandardButton(
            "Cancelar",
            variant="secondary",
            semantic_size="dialog-secondary"
        )
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        # Salvar
        self.btn_save = StandardButton(
            "💾 Salvar Padrão",
            variant="primary-green",
            semantic_size="dialog-primary"
        )
        self.btn_save.clicked.connect(self._on_save)
        btn_layout.addWidget(self.btn_save)

        main_layout.addLayout(btn_layout)

        # Conexão Enter para salvar
        self.name_input.returnPressed.connect(self._on_save)

    def _on_save(self):
        """Handle para botão Salvar."""
        # Valida nome
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(
                self, "Nome Obrigatório",
                "Por favor, informe um nome para o padrão."
            )
            self.name_input.setFocus()
            return

        # Valida caracteres especiais
        if any(c in name for c in '<>:"/\\|?*'):
            QMessageBox.warning(
                self, "Nome Inválido",
                "O nome não pode conter caracteres especiais: < > : \" / \\ | ? *"
            )
            self.name_input.setFocus()
            return

        # Salva dados
        self.pattern_name = name
        self.pattern_description = self.desc_input.toPlainText().strip()

        logger.info(f"Padrão salvo: '{name}' - {self.pattern_description or 'sem descrição'}")

        self.accept()

    def get_pattern_data(self) -> Tuple[str, str]:
        """
        Obtém dados do padrão salvo.

        Returns:
            Tuple (nome, descrição)
        """
        return self.pattern_name or "", self.pattern_description or ""

    def get_measurement_params(self) -> dict:
        """
        Obtém parâmetros de medição atuais.

        Returns:
            Dict com parâmetros de medição
        """
        return {
            'start_point': self.start_point,
            'end_point': self.end_point,
            'grid_size': self.grid_size,
            'z_height': self.z_height,
            'z_move': self.z_move,
            'stabilization_time_ms': self.stabilization_time_ms,
            'feed_rate': self.feed_rate
        }
