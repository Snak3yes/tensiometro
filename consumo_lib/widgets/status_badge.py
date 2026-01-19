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

    Cores por status:
        - approved_auto: Verde vibrante (#4CAF50)
        - approved_user: Verde-amarelo (#CDDC39)
        - rejected: Vermelho (#F44336)
        - pending: Cinza (#9E9E9E)
        - in_progress: Azul (#2196F3)
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
