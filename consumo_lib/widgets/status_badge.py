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

    @staticmethod
    def _get_status_colors():
        """
        Retorna dict de cores por status (lazy initialization).

        Isso evita acessar COLORS durante o import do módulo.
        """
        return {
            "active": COLORS.SUCCESS,
            "warning": COLORS.WARNING,
            "retired": COLORS.ERROR,
            "approved_auto": COLORS.STATUS_APPROVED_AUTO,
            "approved_user": COLORS.STATUS_APPROVED_USER,
            "rejected": COLORS.STATUS_REJECTED,
            "pending": COLORS.STATUS_PENDING,
            "in_progress": COLORS.SECONDARY,
        }

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
        status_colors = self._get_status_colors()
        color = status_colors.get(status, COLORS.STATUS_PENDING)
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
