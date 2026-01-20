"""
Dialog Final de Decisão - Descartar ou Reprovar Inspeção

Aparece quando há defeitos confirmados após análise visual humana.
Usuário escolhe entre descartar (não salva) ou reprovar (salva).
"""

import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QWidget, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from aoi_lib.audit_log import get_audit_log
from consumo_lib.ui import COLORS, TYPO, SPACE, DIM

logger = logging.getLogger(__name__)


class FinalDecisionDialog(QDialog):
    """
    Dialog final de decisão após análise de defeitos

    Aparece quando usuário confirmou defeitos reais durante análise.
    Oferece 2 opções:
    1. Descartar Inspeção - NÃO salva no histórico (apenas log de auditoria)
    2. Reprovar Sessão - Salva no histórico como REPROVADO

    Sinais:
        decision_discarded: Emitido quando usuário escolhe descartar
                            Argumento: dict com session_data
        decision_rejected: Emitido quando usuário escolhe reprovar
                           Argumento: dict com session_data
    """

    decision_discarded = pyqtSignal(dict)
    decision_rejected = pyqtSignal(dict)

    def __init__(
        self,
        session_data: dict,
        defects_confirmed: list,
        defects_approved: list,
        parent=None
    ):
        """
        Inicializa dialog final de decisão

        Args:
            session_data: Dicionário com dados da sessão
                {
                    "session_id": "XPTO-2025-12-15-001",
                    "stencil_code": "STENCIL-ABC-123",
                    "session_type": "Limpeza XPTO",
                    "operator": "João Silva",
                    "mode": "inspection" ou "both"
                }
            defects_confirmed: Lista de defeitos confirmados como reais
            defects_approved: Lista de defeitos julgados como falhas falsas
            parent: Widget pai
        """
        super().__init__(parent)
        self.session_data = session_data
        self.defects_confirmed = defects_confirmed
        self.defects_approved = defects_approved
        self.audit_log = get_audit_log()

        self.setup_ui()

    def setup_ui(self):
        """Configura interface do dialog"""
        self.setWindowTitle("Decisão Final - Análise Completa")
        self.setModal(True)
        self.setFixedSize(650, 550)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(20)

        # Título principal
        title_label = QLabel("Análise Completa")
        title_label.setFont(TYPO.get_font(TYPO.DISPLAY_SMALL, bold=True))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY};")
        layout.addWidget(title_label)

        # Resumo da análise
        summary_frame = self._create_summary_frame()
        layout.addWidget(summary_frame)

        layout.addSpacing(10)

        # Instruções
        instruction_label = QLabel(
            "Há defeitos confirmados. O que deseja fazer?"
        )
        instruction_label.setFont(TYPO.get_font(TYPO.HEADLINE_MEDIUM, bold=True))
        instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instruction_label.setStyleSheet(f"color: {COLORS.TEXT_HINT};")
        layout.addWidget(instruction_label)

        layout.addSpacing(20)

        # Opções (Cards)
        options_container = QWidget()
        options_layout = QHBoxLayout(options_container)
        options_layout.setSpacing(20)

        # Opção 1: Descartar
        discard_card = self._create_discard_card()
        options_layout.addWidget(discard_card)

        # Opção 2: Reprovar
        reject_card = self._create_reject_card()
        options_layout.addWidget(reject_card)

        layout.addWidget(options_container)

        layout.addStretch()

        # Botões inferiores
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setMinimumWidth(120)
        self.cancel_button.setMinimumHeight(DIM.BUTTON_HEIGHT_MD)
        self.cancel_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.SURFACE};
                color: {COLORS.TEXT_HINT};
                font-size: 13px;
                font-weight: 600;
                border: 2px solid {COLORS.BORDER};
                border-radius: {DIM.RADIUS_SM}px;
                padding: {SPACE.SM}px {SPACE.MD}px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.BORDER};
                border: 2px solid {COLORS.TEXT_PRIMARY};
            }}
        """)
        self.cancel_button.clicked.connect(self.on_cancel_clicked)
        buttons_layout.addWidget(self.cancel_button)

        layout.addLayout(buttons_layout)

    def _create_summary_frame(self) -> QFrame:
        """Cria frame de resumo da análise"""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS.WARNING_LIGHT};
                border: 2px solid {COLORS.WARNING};
                border-radius: {DIM.RADIUS_MD}px;
                padding: {SPACE.MD}px;
            }}
        """)

        layout = QVBoxLayout(frame)
        layout.setSpacing(10)

        # Contagem total
        total_defects = len(self.defects_confirmed) + len(self.defects_approved)
        total_label = QLabel(f"{total_defects} defeitos analisados")
        total_label.setFont(TYPO.get_font(TYPO.HEADLINE_LARGE, bold=True))
        total_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        total_label.setStyleSheet(f"color: {COLORS.WARNING_DARK};")
        layout.addWidget(total_label)

        # Estatísticas
        stats_text = f"""
        ✅ {len(self.defects_approved)} aprovados (falhas falsas)
        ❌ {len(self.defects_confirmed)} confirmados como defeitos reais
        """.strip()

        stats_label = QLabel(stats_text)
        stats_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS.WARNING_DARK};
                font-size: 13px;
                font-weight: 600;
            }}
        """)
        stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(stats_label)

        return frame

    def _create_discard_card(self) -> QFrame:
        """Cria card de opção Descartar"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS.ERROR_LIGHT};
                border: 2px solid {COLORS.ERROR_LIGHT};
                border-radius: 12px;
                padding: {SPACE.LG}px;
            }}
        """)
        card.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(card)
        layout.setSpacing(15)

        # Ícone
        icon_label = QLabel("🗑️")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 48px;")
        layout.addWidget(icon_label)

        # Título
        title_label = QLabel("Descartar Inspeção")
        title_label.setFont(TYPO.get_font(TYPO.HEADLINE_LARGE, bold=True))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(f"color: {COLORS.ERROR_DARK};")
        layout.addWidget(title_label)

        # Descrição
        desc_label = QLabel(
            "NÃO salva no histórico.\n\n"
            "Faça a correção necessária\n"
            "e inspecione novamente do zero."
        )
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setStyleSheet(f"color: {COLORS.ERROR_DARK}; {TYPO.BODY_SMALL}")
        layout.addWidget(desc_label)

        layout.addStretch()

        # Botão
        discard_btn = QPushButton("Descartar Inspeção")
        discard_btn.setMinimumHeight(DIM.BUTTON_HEIGHT_LG)
        discard_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.ERROR};
                color: white;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: {DIM.RADIUS_MD}px;
                padding: {SPACE.SM}px {SPACE.LG}px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.ERROR_DARK};
            }}
            QPushButton:pressed {{
                background-color: {COLORS.ERROR_DARK};
            }}
        """)
        discard_btn.clicked.connect(self.on_discard_clicked)
        layout.addWidget(discard_btn)

        # Click no card clica no botão
        card.mousePressEvent = lambda event: self.on_discard_clicked()

        return card

    def _create_reject_card(self) -> QFrame:
        """Cria card de opção Reprovar"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS.ERROR_LIGHT};
                border: 2px solid {COLORS.ERROR_LIGHT};
                border-radius: 12px;
                padding: {SPACE.LG}px;
            }}
        """)
        card.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(card)
        layout.setSpacing(15)

        # Ícone
        icon_label = QLabel("❌")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 48px;")
        layout.addWidget(icon_label)

        # Título
        title_label = QLabel("Reprovar Sessão")
        title_label.setFont(TYPO.get_font(TYPO.HEADLINE_LARGE, bold=True))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(f"color: {COLORS.ERROR_DARK};")
        layout.addWidget(title_label)

        # Descrição
        desc_label = QLabel(
            "Salva no histórico como REPROVADO.\n\n"
            "Registra os defeitos confirmados.\n"
            "Pode fazer nova limpeza depois."
        )
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setStyleSheet(f"color: {COLORS.ERROR_DARK}; {TYPO.BODY_SMALL}")
        layout.addWidget(desc_label)

        layout.addStretch()

        # Botão
        reject_btn = QPushButton("Reprovar Sessão")
        reject_btn.setMinimumHeight(DIM.BUTTON_HEIGHT_LG)
        reject_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.ERROR_DARK};
                color: white;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: {DIM.RADIUS_MD}px;
                padding: {SPACE.SM}px {SPACE.LG}px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.ERROR};
            }}
            QPushButton:pressed {{
                background-color: {COLORS.ERROR_DARK};
            }}
        """)
        reject_btn.clicked.connect(self.on_reject_clicked)
        layout.addWidget(reject_btn)

        # Click no card clica no botão
        card.mousePressEvent = lambda event: self.on_reject_clicked()

        return card

    def on_discard_clicked(self):
        """
        Handler: Botão Descartar clicado

        Registra no log de auditoria e emite sinal.
        """
        # Confirmação
        reply = QMessageBox.question(
            self,
            "Confirmar Descarte",
            f"Tem certeza que deseja descartar esta inspeção?\n\n"
            f"Os dados NÃO serão salvos no histórico.\n"
            f"Um log de auditoria será registrado internamente.\n\n"
            f"Stencil: {self.session_data.get('stencil_code')}\n"
            f"Defeitos confirmados: {len(self.defects_confirmed)}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Registra no log de auditoria
            self.audit_log.log_discarded_inspection(
                session_id=self.session_data.get("session_id", "UNKNOWN"),
                operator=self.session_data.get("operator", "Unknown"),
                stencil_code=self.session_data.get("stencil_code", "UNKNOWN"),
                session_type=self.session_data.get("session_type", "Unknown"),
                defects=self.defects_confirmed,
                reason=f"{len(self.defects_confirmed)} defeitos confirmados pelo operador"
            )

            logger.info(
                f"Inspeção descartada: {self.session_data.get('stencil_code')} "
                f"por {self.session_data.get('operator')}"
            )

            # Emite sinal
            self.decision_discarded.emit(self.session_data)

            # Fecha dialog
            self.accept()

    def on_reject_clicked(self):
        """
        Handler: Botão Reprovar clicado

        Registra no log de auditoria e emite sinal.
        """
        # Confirmação
        reply = QMessageBox.question(
            self,
            "Confirmar Reprovação",
            f"Tem certeza que deseja reprovar esta sessão?\n\n"
            f"Os dados serão salvos no histórico como REPROVADO.\n\n"
            f"Stencil: {self.session_data.get('stencil_code')}\n"
            f"Defeitos confirmados: {len(self.defects_confirmed)}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Registra no log de auditoria
            audit_entry = self.audit_log.log_rejected_inspection(
                session_id=self.session_data.get("session_id", "UNKNOWN"),
                operator=self.session_data.get("operator", "Unknown"),
                stencil_code=self.session_data.get("stencil_code", "UNKNOWN"),
                session_type=self.session_data.get("session_type", "Unknown"),
                defects=self.defects_confirmed
            )

            # Adiciona audit_entry ao session_data
            self.session_data["audit_entry"] = audit_entry.to_dict()

            logger.info(
                f"Inspeção reprovada: {self.session_data.get('stencil_code')} "
                f"por {self.session_data.get('operator')}"
            )

            # Emite sinal
            self.decision_rejected.emit(self.session_data)

            # Fecha dialog
            self.accept()

    def on_cancel_clicked(self):
        """Handler: Botão Cancelar clicado"""
        logger.info("Decisão final cancelada pelo usuário")
        self.reject()
