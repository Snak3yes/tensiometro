"""
Widget de Badge de Status

Exibe badge colorido para status operacional.
"""

from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt

from consumo_lib.ui import COLORS, TYPO, SPACE, DIM


class StatusBadge(QLabel):
    """
    Badge colorido para status do stencil.
    """

    # Cores por status (usando design tokens)
    STATUS_COLORS = {
        "active": COLORS.SUCCESS,
        "warning": COLORS.WARNING,
        "retired": COLORS.ERROR,
        "pending": COLORS.STATUS_PENDING,
        "in_progress": COLORS.SECONDARY,
        "approved_auto": COLORS.SUCCESS,
        "approved_user": COLORS.SUCCESS,
        "rejected": COLORS.ERROR,
    }

    # Labels por status
    LABELS = {
        "active": "ATIVO",
        "warning": "ALERTA",
        "retired": "RETIRADO",
        "pending": "PENDENTE",
        "in_progress": "EM ANDAMENTO",
        "approved_auto": "ATIVO",
        "approved_user": "ATIVO",
        "rejected": "RETIRADO",
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
        Método legado de compatibilidade.

        Args:
            record: Dicionário com dados de inspeção
            parent: Widget pai

        Returns:
            Instância de StatusBadge
        """
        status = record.get("status", "pending")
        return cls(status, parent)
