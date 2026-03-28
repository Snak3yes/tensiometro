"""
dialogs/stencil/full_history_dialog.py
--------------------------------------
Diálogo para visualizar histórico completo de um stencil.
"""

import logging
import os
from datetime import datetime

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QGroupBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QTabWidget, QWidget, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont

from aoi_lib.stencil_tracker import StencilTracker
from consumo_lib.ui import COLORS, TYPO, SPACE, DIM
from consumo_lib.ui.widget_standards import StandardButton

log = logging.getLogger(__name__)


class StencilFullHistoryDialog(QDialog):
    """
    Diálogo para visualizar histórico de medições de tensão de um stencil.

    Mostra:
    - Resumo de tendência
    - Histórico de medições de tensão
    """

    def __init__(self, tracker: StencilTracker, code: str, parent=None):
        super().__init__(parent)
        self.tracker = tracker
        self.code = code

        self.setWindowTitle(f"Histórico Completo - {code}")
        self.setMinimumSize(850, 600)

        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # ================== INFORMAÇÕES DO STENCIL ==================
        stencil = self.tracker.get_stencil(self.code)
        if stencil:
            info_group = QGroupBox("Stencil")
            info_layout = QHBoxLayout(info_group)

            info_layout.addWidget(QLabel(f"<b>{stencil.code}</b>"))
            info_layout.addWidget(QLabel(f"| {stencil.description or '(sem descrição)'}"))
            info_layout.addWidget(QLabel(f"| Receita: {stencil.recipe_name or 'N/A'}"))
            info_layout.addWidget(QLabel(f"| Total de medições: {stencil.inspection_count}"))
            info_layout.addStretch()

            layout.addWidget(info_group)

        # ================== HISTÓRICO DE TENSÃO ==================
        self.tabs = QTabWidget()

        # Aba de tensão
        self.tension_tab = QWidget()
        self._setup_tension_tab()
        self.tabs.addTab(self.tension_tab, "Medições de Tensão")

        layout.addWidget(self.tabs, 1)

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

    def _setup_tension_tab(self):
        """Configura aba de medições de tensão."""
        layout = QVBoxLayout(self.tension_tab)

        # Resumo de tendência
        trend_group = QGroupBox("Análise de Tendência")
        trend_layout = QGridLayout(trend_group)

        self.lbl_tension_total = QLabel()
        self.lbl_tension_first = QLabel()
        self.lbl_tension_last = QLabel()
        self.lbl_tension_moving = QLabel()
        self.lbl_tension_variation = QLabel()
        self.lbl_tension_trend = QLabel()

        trend_layout.addWidget(QLabel("Total:"), 0, 0)
        trend_layout.addWidget(self.lbl_tension_total, 0, 1)
        trend_layout.addWidget(QLabel("Primeira média:"), 0, 2)
        trend_layout.addWidget(self.lbl_tension_first, 0, 3)
        trend_layout.addWidget(QLabel("Última média:"), 1, 0)
        trend_layout.addWidget(self.lbl_tension_last, 1, 1)
        trend_layout.addWidget(QLabel("Média móvel:"), 1, 2)
        trend_layout.addWidget(self.lbl_tension_moving, 1, 3)
        trend_layout.addWidget(QLabel("Variação:"), 2, 0)
        trend_layout.addWidget(self.lbl_tension_variation, 2, 1)
        trend_layout.addWidget(QLabel("Tendência:"), 2, 2)
        trend_layout.addWidget(self.lbl_tension_trend, 2, 3)

        layout.addWidget(trend_group)

        # Tabela de tensão
        self.tension_table = QTableWidget()
        self.tension_table.setColumnCount(7)
        self.tension_table.setHorizontalHeaderLabels([
            "Data/Hora", "Média", "Mín", "Máx", "OK", "WARN", "Resultado"
        ])
        self.tension_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.tension_table.setAlternatingRowColors(True)

        layout.addWidget(self.tension_table, 1)

    def _load_data(self):
        """Carrega todos os dados."""
        self._load_tension_history()

    def _load_tension_history(self):
        """Carrega histórico de tensão."""
        # Análise de tendência
        analysis = self.tracker.get_trend_analysis(self.code)

        self.lbl_tension_total.setText(str(analysis.record_count))
        self.lbl_tension_first.setText(f"{analysis.first_average:.2f} N/cm²")
        self.lbl_tension_last.setText(f"{analysis.last_average:.2f} N/cm²")
        self.lbl_tension_moving.setText(f"{analysis.moving_average:.2f} N/cm²")

        var_text = f"{analysis.variation_percent:+.1f}%"
        if analysis.variation_percent < -5:
            self.lbl_tension_variation.setStyleSheet(f"color: {COLORS.ERROR}; font-weight: bold;")
            var_text = f"📉 {var_text}"
        elif analysis.variation_percent > 5:
            self.lbl_tension_variation.setStyleSheet(f"color: {COLORS.SUCCESS}; font-weight: bold;")
            var_text = f"{var_text}"
        else:
            self.lbl_tension_variation.setStyleSheet(f"color: {COLORS.TEXT_DISABLED};")
        self.lbl_tension_variation.setText(var_text)

        trend_map = {
            "stable": ("Estável", COLORS.TEXT_DISABLED),
            "degrading": ("Em Degradação ⚠️", COLORS.ERROR),
            "improving": ("Melhorando ✓", COLORS.SUCCESS),
        }
        trend_text, trend_color = trend_map.get(analysis.trend, ("?", COLORS.TEXT_DISABLED))
        self.lbl_tension_trend.setText(trend_text)
        self.lbl_tension_trend.setStyleSheet(f"color: {trend_color}; font-weight: bold;")

        # Tabela de tensão
        history = self.tracker.get_tension_history(self.code, limit=50)
        self.tension_table.setRowCount(len(history))

        for row, record in enumerate(history):
            try:
                dt = datetime.fromisoformat(record.timestamp)
                dt_str = dt.strftime("%d/%m/%Y %H:%M")
            except:
                dt_str = record.timestamp

            self.tension_table.setItem(row, 0, QTableWidgetItem(dt_str))
            self.tension_table.setItem(row, 1, QTableWidgetItem(f"{record.average_tension:.2f}"))
            self.tension_table.setItem(row, 2, QTableWidgetItem(f"{record.min_tension:.2f}"))
            self.tension_table.setItem(row, 3, QTableWidgetItem(f"{record.max_tension:.2f}"))
            self.tension_table.setItem(row, 4, QTableWidgetItem(str(record.ok_count)))
            self.tension_table.setItem(row, 5, QTableWidgetItem(str(record.warning_count)))

            result_item = QTableWidgetItem(record.result)
            if record.result == "OK":
                result_item.setBackground(COLORS.to_qcolor(COLORS.SUCCESS))
            elif record.result == "WARNING":
                result_item.setBackground(COLORS.to_qcolor(COLORS.WARNING_LIGHT))
            else:
                result_item.setBackground(COLORS.to_qcolor(COLORS.ERROR_LIGHT))
            self.tension_table.setItem(row, 6, result_item)

    def _export_csv(self):
        """Exporta histórico de tensão para CSV."""
        from PyQt6.QtWidgets import QFileDialog

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Histórico de Tensão",
            f"historico_tensao_{self.code}.csv",
            "CSV (*.csv)"
        )

        if not filepath:
            return

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                # Header
                f.write("Data/Hora,Resultado,Media,Min,Max,OK,WARNING,NOK,Receita\n")

                for record in self.tracker.get_tension_history(self.code, limit=1000):
                    f.write(
                        f"{record.timestamp},"
                        f"{record.result},"
                        f"{record.average_tension:.2f},"
                        f"{record.min_tension:.2f},"
                        f"{record.max_tension:.2f},"
                        f"{record.ok_count},"
                        f"{record.warning_count},"
                        f"{record.nok_count},"
                        f"{record.recipe_name or ''}\n"
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
