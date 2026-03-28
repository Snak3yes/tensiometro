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
            "Sobre o Tensiômetro",
            "<h2>Sistema Tensiômetro</h2>"
            "<h3>Controle de Tensão, Rastreabilidade e Movimento</h3>"
            "<p><b>Versão:</b> 0.4.0</p>"
            "<p><b>Desenvolvido por:</b> Ronald Buzaglo</p>"
            "<hr>"
            "<p><b>Parceria de Desenvolvimento:</b></p>"
            "<p>CodeVision ↔ CTD (Centro de Transformação Digital)<br>"
            "Digiboard Eletrônica da Amazônia Ltda (DGB)</p>"
            "<hr>"
            "<p><b>Funcionalidades:</b></p>"
            "<ul>"
            "<li>✓ Medição de tensão superficial com AS-120N</li>"
            "<li>✓ Controle CNC 3 eixos via PLC (Modbus TCP)</li>"
            "<li>✓ Geração de relatórios PDF com tendências</li>"
            "<li>✓ Rastreabilidade completa de stencils</li>"
            "</ul>"
            "<hr>"
            "<p style='text-align:center;'><i>© 2025-2026 - Projeto desenvolvido em parceria "
            "CodeVision e DGB/CTD</i></p>"
        )
