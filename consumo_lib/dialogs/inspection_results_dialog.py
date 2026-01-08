"""
Dialog de Resultados de Inspeção

Exibe resultados coletados, estatísticas e classificação final.
"""

import logging
from datetime import datetime
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QWidget, QScrollArea, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

logger = logging.getLogger(__name__)


class InspectionResultsDialog(QDialog):
    """
    Dialog de resultados da inspeção

    Mostra dados coletados, métricas e classificação.
    """

    def __init__(self, stencil_code: str, mode: str,
                 results: dict, parent=None):
        """
        Inicializa dialog de resultados

        Args:
            stencil_code: Código do stencil
            mode: Modo de inspeção executado
            results: Dicionário com resultados da execução
            parent: Widget pai
        """
        super().__init__(parent)
        self.stencil_code = stencil_code
        self.mode = mode
        self.results = results

        self.setup_ui()

    def setup_ui(self):
        """Configura interface do dialog"""
        self.setWindowTitle("Resultados da Inspeção")
        self.setModal(True)
        self.setFixedSize(700, 700)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(20)

        # Header
        header = self._create_header()
        layout.addWidget(header)

        # Área de conteúdo scrollável
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(20)

        # Resumo
        resumo = self._create_resumo()
        content_layout.addWidget(resumo)

        # Detalhes (específicos do modo)
        if self.mode == "tension":
            detalhes = self._create_detalhes_tensao()
        elif self.mode == "inspection":
            detalhes = self._create_detalhes_inspecao()
        else:  # both
            detalhes = self._create_detalhes_ambos()

        content_layout.addWidget(detalhes)
        content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

        # Botões
        buttons = self._create_buttons()
        layout.addWidget(buttons)

    def _create_header(self) -> QWidget:
        """Cria header com informações básicas"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(5)

        # Título
        title = QLabel("Resultados da Inspeção")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #111827;")
        layout.addWidget(title)

        # Info line
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        info_label = QLabel(
            f"Stencil: {self.stencil_code}   |   "
            f"Modo: {self._get_mode_title()}   |   "
            f"Data: {timestamp}"
        )
        info_label.setStyleSheet("color: #6B7280; font-size: 12px;")
        layout.addWidget(info_label)

        return widget

    def _create_resumo(self) -> QFrame:
        """Cria card de resumo com classificação"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                border: 2px solid #E5E7EB;
                border-radius: 8px;
                background-color: #F9FAFB;
                padding: 20px;
            }
        """)

        layout = QVBoxLayout(frame)
        layout.setSpacing(15)

        # Título do resumo
        resumo_title = QLabel("RESUMO")
        resumo_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        resumo_title.setStyleSheet("color: #374151;")
        layout.addWidget(resumo_title)

        # Conteúdo baseado no modo
        content = self._get_resumo_content()
        layout.addWidget(content)

        return frame

    def _get_resumo_content(self) -> QWidget:
        """Retorna conteúdo do resumo baseado no modo"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)

        if self.mode == "tension":
            # Tensão Média
            tension_avg = self.results.get("tension_avg", 0)
            avg_label = QLabel(f"Tensão Média: {tension_avg} N/cm")
            avg_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #111827;")
            layout.addWidget(avg_label)

            # Pontos medidos
            points = self.results.get("points_measured", 0)
            points_label = QLabel(f"Pontos Medidos: {points}")
            points_label.setStyleSheet("font-size: 14px; color: #374151;")
            layout.addWidget(points_label)

            # Classificação
            classification = self.results.get("classification", "UNKNOWN")
            class_label = QLabel(f"Classificação: {self._get_classification_label(classification)}")
            class_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {self._get_classification_color(classification)};")
            layout.addWidget(class_label)

        elif self.mode == "inspection":
            # Aperturas analisadas
            total = self.results.get("apertures_analyzed", 0)
            total_label = QLabel(f"Aberturas Analisadas: {total}")
            total_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #111827;")
            layout.addWidget(total_label)

            # Distribuição
            ok = self.results.get("ok_count", 0)
            partial = self.results.get("partial_count", 0)
            blocked = self.results.get("blocked_count", 0)

            dist_label = QLabel(f"OK: {ok}  |  Parciais: {partial}  |  Bloqueadas: {blocked}")
            dist_label.setStyleSheet("font-size: 13px; color: #374151;")
            layout.addWidget(dist_label)

            # Classificação
            classification = self.results.get("classification", "UNKNOWN")
            class_label = QLabel(f"Classificação: {self._get_classification_label(classification)}")
            class_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {self._get_classification_color(classification)};")
            layout.addWidget(class_label)

        return widget

    def _create_detalhes_tensao(self) -> QFrame:
        """Cria seção de detalhes para medição de tensão"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                border: 2px solid #E5E7EB;
                border-radius: 8px;
                padding: 20px;
            }
        """)

        layout = QVBoxLayout(frame)
        layout.setSpacing(15)

        # Título
        title = QLabel("DADOS DETALHADOS")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title.setStyleSheet("color: #374151;")
        layout.addWidget(title)

        # Estatísticas
        stats_text = f"""
Grid de Medição: {self.results.get('grid_size', 'N/A')}
Menor Valor: {self.results.get('tension_min', 'N/A')} N/cm
Maior Valor: {self.results.get('tension_max', 'N/A')} N/cm
Desvio Padrão: {self.results.get('tension_std', 'N/A')} N/cm
        """.strip()

        stats_label = QLabel(stats_text)
        stats_label.setStyleSheet("font-family: 'Consolas', monospace; font-size: 12px; color: #374151;")
        layout.addWidget(stats_label)

        # Placeholder para heatmap (FUTURO)
        heatmap_label = QLabel("[Heatmap de medições será implementado em fase futura]")
        heatmap_label.setStyleSheet("color: #9CA3AF; font-style: italic; padding: 20px; border: 1px dashed #D1D5DB;")
        heatmap_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(heatmap_label)

        return frame

    def _create_detalhes_inspecao(self) -> QFrame:
        """Cria seção de detalhes para inspeção visual"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                border: 2px solid #E5E7EB;
                border-radius: 8px;
                padding: 20px;
            }
        """)

        layout = QVBoxLayout(frame)
        layout.setSpacing(15)

        # Título
        title = QLabel("DADOS DETALHADOS")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title.setStyleSheet("color: #374151;")
        layout.addWidget(title)

        # Lista de aberturas parciais/bloqueadas
        partial = self.results.get("partial_apertures", [])
        blocked = self.results.get("blocked_apertures", [])

        if partial:
            partial_text = f"Aberturas Parciais: {', '.join(map(str, partial[:5]))}"
            if len(partial) > 5:
                partial_text += f" ... (+{len(partial)-5} mais)"
            partial_label = QLabel(partial_text)
            partial_label.setStyleSheet("color: #F59E0B; font-size: 12px;")
            layout.addWidget(partial_label)

        if blocked:
            blocked_text = f"Aberturas Bloqueadas: {', '.join(map(str, blocked[:5]))}"
            if len(blocked) > 5:
                blocked_text += f" ... (+{len(blocked)-5} mais)"
            blocked_label = QLabel(blocked_text)
            blocked_label.setStyleSheet("color: #EF4444; font-size: 12px;")
            layout.addWidget(blocked_label)

        if not partial and not blocked:
            ok_label = QLabel("✅ Todas as aberturas aprovadas!")
            ok_label.setStyleSheet("color: #10B981; font-size: 13px; font-weight: bold;")
            layout.addWidget(ok_label)

        return frame

    def _create_detalhes_ambos(self) -> QFrame:
        """Cria seção de detalhes para modo completo"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                border: 2px solid #E5E7EB;
                border-radius: 8px;
                padding: 20px;
            }
        """)

        layout = QVBoxLayout(frame)
        layout.setSpacing(10)

        # Título
        title = QLabel("MODO COMPLETO: TENSÃO + INSPEÇÃO")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title.setStyleSheet("color: #374151;")
        layout.addWidget(title)

        # Resumo dos dois modos
        tension_results = self.results.get('tension_results', {})
        inspection_results = self.results.get('inspection_results', {})

        resumo_text = f"""
✓ Tensão Média: {tension_results.get('tension_avg', 'N/A')} N/cm
✓ Aberturas Analisadas: {inspection_results.get('apertures_analyzed', 'N/A')}
✓ Classificação Final: {self._get_classification_label(self.results.get('combined_classification', 'UNKNOWN'))}
        """.strip()

        resumo_label = QLabel(resumo_text)
        resumo_label.setStyleSheet("font-size: 13px; color: #374151;")
        layout.addWidget(resumo_label)

        return frame

    def _create_buttons(self) -> QWidget:
        """Cria botões de ação"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setSpacing(12)
        layout.addStretch()

        # Salvar no histórico
        save_btn = QPushButton("Salvar no Histórico")
        save_btn.setMinimumHeight(40)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                font-size: 13px;
                font-weight: 600;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        save_btn.clicked.connect(self.on_save_clicked)
        layout.addWidget(save_btn)

        # Gerar PDF
        pdf_btn = QPushButton("Gerar PDF")
        pdf_btn.setMinimumHeight(40)
        pdf_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                font-size: 13px;
                font-weight: 600;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
        """)
        pdf_btn.clicked.connect(self.on_pdf_clicked)
        layout.addWidget(pdf_btn)

        # Fechar
        close_btn = QPushButton("Fechar")
        close_btn.setMinimumHeight(40)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #6B7280;
                color: white;
                font-size: 13px;
                font-weight: 600;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #4B5563;
            }
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        return widget

    def on_save_clicked(self):
        """Handler: Botão Salvar clicado"""
        # TODO: Implementar salvamento no StencilTracker
        logger.info(f"Salvar inspeção no histórico: {self.stencil_code}")
        QMessageBox.information(
            self,
            "Salvar no Histórico",
            "Funcionalidade de salvamento será implementada na FASE 7."
        )

    def on_pdf_clicked(self):
        """Handler: Botão PDF clicado"""
        # TODO: Implementar geração de PDF
        logger.info(f"Gerar PDF: {self.stencil_code}")
        QMessageBox.information(
            self,
            "Gerar PDF",
            "Funcionalidade de geração de PDF será implementada na FASE 7."
        )

    def _get_mode_title(self) -> str:
        """Retorna título legível do modo"""
        titles = {
            "tension": "Medição de Tensão",
            "inspection": "Inspeção Visual",
            "both": "Completo (Tensão + Visual)"
        }
        return titles.get(self.mode, "Inspeção")

    def _get_classification_label(self, classification: str) -> str:
        """Retorna label legível da classificação"""
        labels = {
            "OK": "✅ APROVADO",
            "WARNING": "⚠️ ATENÇÃO",
            "NOK": "❌ REPROVADO",
            "UNKNOWN": "⏳ PENDENTE"
        }
        return labels.get(classification, classification)

    def _get_classification_color(self, classification: str) -> str:
        """Retorna cor da classificação"""
        colors = {
            "OK": "#10B981",      # Verde
            "WARNING": "#F59E0B",  # Amarelo
            "NOK": "#EF4444",     # Vermelho
            "UNKNOWN": "#9CA3AF"  # Cinza
        }
        return colors.get(classification, "#9CA3AF")
