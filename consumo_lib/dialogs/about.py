"""
dialogs/about.py
----------------
Diálogo Sobre o aplicativo.
"""

from PyQt6.QtWidgets import QMessageBox


class AboutDialog:
    """Diálogo 'Sobre' estático para exibir informações do aplicativo."""

    @staticmethod
    def show_about(parent):
        """
        Mostra diálogo sobre o aplicativo.

        Args:
            parent: Widget pai para o diálogo
        """
        QMessageBox.about(
            parent,
            "Sobre HesaiVision",
            "HesaiVision v1.0\n\n"
            "Sistema de Inspeção Óptica Automatizada\n"
            "Desenvolvido para controle de CNC com GRBL\n\n"
            "© 2025 HesaiVision"
        )
