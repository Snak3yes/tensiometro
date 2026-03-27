"""
Widget de Badge de Status

Exibe badge colorido para status de aprovação.
"""

from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt

from consumo_lib.ui import COLORS, TYPO, SPACE, DIM


class StatusBadge(QLabel):
    """
    Badge colorido para status de inspeção

    Cores por status (v3.0 - Paleta Neutra - Tons de Cinza):
        - approved_auto: Cinza escuro
        - approved_user: Cinza médio
        - rejected: Cinza mais escuro
        - pending: Cinza claro
        - in_progress: Cinza médio

    Note:
        Status é indicado por texto/ícones, não por cores vibrantes.
    """

    # Cores por status (usando design tokens)
    STATUS_COLORS = {
        "approved_auto": COLORS.STATUS_APPROVED_AUTO,    # Verde vibrante
        "approved_user": COLORS.STATUS_APPROVED_USER,    # Verde-amarelo
        "rejected": COLORS.STATUS_REJECTED,              # Vermelho
        "pending": COLORS.STATUS_PENDING,                # Cinza
        "in_progress": COLORS.SECONDARY,                 # Azul
    }

    # Labels por status
    LABELS = {
        "approved_auto": "A-AUTO",
        "approved_user": "A-USER",
        "rejected": "REPROV",
        "pending": "PENDENTE",
        "in_progress": "EM ANDAMENTO",
    }

    def __init__(self, status: str, parent=None):
        """
        Inicializa badge de status

        Args:
            status: Código do status (approved_auto, approved_user, rejected, etc.)
            parent: Widget pai
        """
        super().__init__(parent)
        self.set_status(status)

    def set_status(self, status: str):
        """
        Define status e atualiza aparência

        Args:
            status: Código do status
        """
        # Define texto
        text = self.LABELS.get(status, status.upper())
        self.setText(text)

        # Aplica estilo com design tokens
        color = self.STATUS_COLORS.get(status, COLORS.STATUS_PENDING)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: {COLORS.BACKGROUND};
                padding: {SPACE.XS}px {SPACE.MD}px;
                border-radius: {DIM.RADIUS_SM}px;
                font-weight: bold;
                font-size: {TYPO.LABEL_SMALL}px;
            }}
        """)

        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    @classmethod
    def from_inspection_record(cls, record, parent=None):
        """
        Cria badge a partir de registro de inspeção

        Args:
            record: Dicionário com dados de inspeção
            parent: Widget pai

        Returns:
            Instância de StatusBadge
        """
        status = record.get("status", "pending")
        return cls(status, parent)
