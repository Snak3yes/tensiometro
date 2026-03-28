"""Diálogo para visualizar histórico de medições de um stencil."""

import logging
from datetime import datetime

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QGroupBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from aoi_lib.stencil_tracker import StencilTracker
from consumo_lib.ui import COLORS, TYPO, SPACE
from consumo_lib.ui.widget_standards import StandardButton

log = logging.getLogger(__name__)


class StencilHistoryDialog(QDialog):
    """
    Diálogo para visualizar histórico de medições de um stencil.

    Mostra:
    - Tabela com histórico de medições
    - Análise de tendência
    - Gráfico de evolução (simplificado)
    """

    def __init__(self, tracker: StencilTracker, code: str, parent=None):
        super().__init__(parent)
        self.tracker = tracker
        self.code = code

        self.setWindowTitle(f"Histórico - Stencil {code}")
        self.setMinimumSize(700, 500)

        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # ================== RESUMO DE TENDÊNCIA ==================
        trend_group = QGroupBox("📈 Análise de Tendência")
        trend_layout = QGridLayout(trend_group)

        trend_layout.addWidget(QLabel("Total de medições:"), 0, 0)
        self.lbl_total = QLabel()
        trend_layout.addWidget(self.lbl_total, 0, 1)

        trend_layout.addWidget(QLabel("Primeira média:"), 0, 2)
        self.lbl_first_avg = QLabel()
        trend_layout.addWidget(self.lbl_first_avg, 0, 3)

        trend_layout.addWidget(QLabel("Última média:"), 1, 0)
        self.lbl_last_avg = QLabel()
        trend_layout.addWidget(self.lbl_last_avg, 1, 1)

        trend_layout.addWidget(QLabel("Média móvel (5):"), 1, 2)
        self.lbl_moving_avg = QLabel()
        trend_layout.addWidget(self.lbl_moving_avg, 1, 3)

        trend_layout.addWidget(QLabel("Variação:"), 2, 0)
        self.lbl_variation = QLabel()
        trend_layout.addWidget(self.lbl_variation, 2, 1)

        trend_layout.addWidget(QLabel("Tendência:"), 2, 2)
        self.lbl_trend = QLabel()
        self.lbl_trend.setFont(TYPO.get_font(TYPO.BODY_MEDIUM, bold=True))
        trend_layout.addWidget(self.lbl_trend, 2, 3)

        layout.addWidget(trend_group)

        # ================== TABELA DE HISTÓRICO ==================
        table_group = QGroupBox("📋 Histórico de Medições")
        table_layout = QVBoxLayout(table_group)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Data/Hora", "Média", "Mín", "Máx", "OK", "WARN", "Resultado"
        ])
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.table.setAlternatingRowColors(True)

        table_layout.addWidget(self.table)

        layout.addWidget(table_group, 1)

        # ================== BOTÕES ==================
        btn_layout = QHBoxLayout()

        btn_export = StandardButton("📥 Exportar CSV")
        btn_export.clicked.connect(self._export_csv)
        btn_layout.addWidget(btn_export)

        btn_layout.addStretch()

        btn_close = StandardButton("Fechar")
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)

        layout.addLayout(btn_layout)

    def _load_data(self):
        """Carrega dados do histórico."""
        # Análise de tendência
        analysis = self.tracker.get_trend_analysis(self.code)

        self.lbl_total.setText(str(analysis.record_count))
        self.lbl_first_avg.setText(f"{analysis.first_average:.2f} N/cm²")
        self.lbl_last_avg.setText(f"{analysis.last_average:.2f} N/cm²")
        self.lbl_moving_avg.setText(f"{analysis.moving_average:.2f} N/cm²")

        # Variação com cor
        var_text = f"{analysis.variation_percent:+.1f}%"
        if analysis.variation_percent < -5:
            var_text = f"📉 {var_text}"
            self.lbl_variation.setStyleSheet(f"color: {COLORS.ERROR};")
        elif analysis.variation_percent > 5:
            var_text = f"📈 {var_text}"
            self.lbl_variation.setStyleSheet(f"color: {COLORS.SUCCESS};")
        else:
            self.lbl_variation.setStyleSheet(f"color: {COLORS.TEXT_HINT};")
        self.lbl_variation.setText(var_text)

        # Tendência com cor
        trend_map = {
            "stable": ("Estável", COLORS.TEXT_HINT),
            "degrading": ("Em Degradação ⚠️", COLORS.ERROR),
            "improving": ("Melhorando ✓", COLORS.SUCCESS),
        }
        trend_text, trend_color = trend_map.get(
            analysis.trend, ("Desconhecida", COLORS.TEXT_HINT)
        )
        self.lbl_trend.setText(trend_text)
        self.lbl_trend.setStyleSheet(f"color: {trend_color};")

        # Tabela de histórico
        history = self.tracker.get_tension_history(self.code, limit=50)

        self.table.setRowCount(len(history))

        for row, record in enumerate(history):
            # Data/hora
            try:
                dt = datetime.fromisoformat(record.timestamp)
                dt_str = dt.strftime("%d/%m/%Y %H:%M")
            except:
                dt_str = record.timestamp

            self.table.setItem(row, 0, QTableWidgetItem(dt_str))
            self.table.setItem(row, 1, QTableWidgetItem(f"{record.average_tension:.2f}"))
            self.table.setItem(row, 2, QTableWidgetItem(f"{record.min_tension:.2f}"))
            self.table.setItem(row, 3, QTableWidgetItem(f"{record.max_tension:.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(str(record.ok_count)))
            self.table.setItem(row, 5, QTableWidgetItem(str(record.warning_count)))

            # Resultado com cor
            result_item = QTableWidgetItem(record.result)
            if record.result == "OK":
                result_item.setBackground(COLORS.to_qcolor(COLORS.SUCCESS))
            elif record.result == "WARNING":
                result_item.setBackground(COLORS.to_qcolor(COLORS.WARNING_LIGHT))
            else:
                result_item.setBackground(COLORS.to_qcolor(COLORS.ERROR))
            self.table.setItem(row, 6, result_item)

    def _export_csv(self):
        """Exporta histórico para CSV."""
        from PyQt6.QtWidgets import QFileDialog

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Histórico",
            f"historico_{self.code}.csv",
            "CSV (*.csv)"
        )

        if not filepath:
            return

        try:
            history = self.tracker.get_tension_history(self.code, limit=1000)

            with open(filepath, "w", encoding="utf-8") as f:
                # Header
                f.write("Data/Hora,Média,Mínimo,Máximo,OK,Warning,NOK,Resultado\n")

                for record in history:
                    f.write(
                        f"{record.timestamp},"
                        f"{record.average_tension:.2f},"
                        f"{record.min_tension:.2f},"
                        f"{record.max_tension:.2f},"
                        f"{record.ok_count},"
                        f"{record.warning_count},"
                        f"{record.nok_count},"
                        f"{record.result}\n"
                    )

            QMessageBox.information(
                self, "Exportação Concluída",
                f"Histórico exportado para:\n{filepath}"
            )

        except Exception as e:
            QMessageBox.critical(
                self, "Erro ao Exportar",
                f"Erro: {str(e)}"
            )
