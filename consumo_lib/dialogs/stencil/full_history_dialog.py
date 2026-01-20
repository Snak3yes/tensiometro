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
    Diálogo para visualizar histórico completo de um stencil.

    Mostra:
    - Aba de medições de tensão
    - Aba de inspeções visuais
    - Histórico combinado (timeline)
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
            info_group = QGroupBox("🏷️ Stencil")
            info_layout = QHBoxLayout(info_group)

            info_layout.addWidget(QLabel(f"<b>{stencil.code}</b>"))
            info_layout.addWidget(QLabel(f"| {stencil.description or '(sem descrição)'}"))
            info_layout.addWidget(QLabel(f"| Receita: {stencil.recipe_name or 'N/A'}"))
            info_layout.addWidget(QLabel(f"| Total de inspeções: {stencil.inspection_count}"))
            info_layout.addStretch()

            layout.addWidget(info_group)

        # ================== ABAS DE HISTÓRICO ==================
        self.tabs = QTabWidget()

        # Aba de histórico combinado
        self.combined_tab = QWidget()
        self._setup_combined_tab()
        self.tabs.addTab(self.combined_tab, "📊 Timeline")

        # Aba de tensão
        self.tension_tab = QWidget()
        self._setup_tension_tab()
        self.tabs.addTab(self.tension_tab, "📐 Medições de Tensão")

        # Aba de inspeção visual
        self.inspection_tab = QWidget()
        self._setup_inspection_tab()
        self.tabs.addTab(self.inspection_tab, "🔍 Inspeções Visuais")

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

    def _setup_combined_tab(self):
        """Configura aba de histórico combinado."""
        layout = QVBoxLayout(self.combined_tab)

        self.combined_table = QTableWidget()
        self.combined_table.setColumnCount(5)
        self.combined_table.setHorizontalHeaderLabels([
            "Data/Hora", "Tipo", "Resultado", "Detalhes", "Receita"
        ])
        self.combined_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.combined_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.combined_table.setAlternatingRowColors(True)

        layout.addWidget(self.combined_table)

    def _setup_tension_tab(self):
        """Configura aba de medições de tensão."""
        layout = QVBoxLayout(self.tension_tab)

        # Resumo de tendência
        trend_group = QGroupBox("📈 Análise de Tendência")
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

    def _setup_inspection_tab(self):
        """Configura aba de inspeções visuais."""
        layout = QVBoxLayout(self.inspection_tab)

        # Resumo de inspeção
        stats_group = QGroupBox("📊 Estatísticas de Inspeção Visual")
        stats_layout = QGridLayout(stats_group)

        self.lbl_insp_total = QLabel()
        self.lbl_insp_pass = QLabel()
        self.lbl_insp_fail = QLabel()
        self.lbl_insp_rate = QLabel()
        self.lbl_insp_avg_rate = QLabel()
        self.lbl_insp_last = QLabel()

        stats_layout.addWidget(QLabel("Total de inspeções:"), 0, 0)
        stats_layout.addWidget(self.lbl_insp_total, 0, 1)
        stats_layout.addWidget(QLabel("Aprovadas:"), 0, 2)
        stats_layout.addWidget(self.lbl_insp_pass, 0, 3)
        stats_layout.addWidget(QLabel("Reprovadas:"), 1, 0)
        stats_layout.addWidget(self.lbl_insp_fail, 1, 1)
        stats_layout.addWidget(QLabel("Taxa de aprovação:"), 1, 2)
        stats_layout.addWidget(self.lbl_insp_rate, 1, 3)
        stats_layout.addWidget(QLabel("Média de fill %:"), 2, 0)
        stats_layout.addWidget(self.lbl_insp_avg_rate, 2, 1)
        stats_layout.addWidget(QLabel("Última inspeção:"), 2, 2)
        stats_layout.addWidget(self.lbl_insp_last, 2, 3)

        layout.addWidget(stats_group)

        # Tabela de inspeção
        self.inspection_table = QTableWidget()
        self.inspection_table.setColumnCount(8)
        self.inspection_table.setHorizontalHeaderLabels([
            "Data/Hora", "Total", "OK", "Parcial", "Bloqueado", "Fill %", "Resultado", "Relatório"
        ])
        self.inspection_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.inspection_table.setAlternatingRowColors(True)
        self.inspection_table.cellDoubleClicked.connect(self._open_report)

        layout.addWidget(self.inspection_table, 1)

    def _load_data(self):
        """Carrega todos os dados."""
        self._load_combined_history()
        self._load_tension_history()
        self._load_inspection_history()

    def _load_combined_history(self):
        """Carrega histórico combinado na timeline."""
        combined = self.tracker.get_combined_history(self.code, limit=100)

        self.combined_table.setRowCount(len(combined))

        for row, item in enumerate(combined):
            record = item["record"]
            record_type = item["type"]

            # Data/hora
            try:
                dt = datetime.fromisoformat(item["timestamp"])
                dt_str = dt.strftime("%d/%m/%Y %H:%M")
            except:
                dt_str = item["timestamp"]

            self.combined_table.setItem(row, 0, QTableWidgetItem(dt_str))

            # Tipo
            if record_type == "tension":
                type_item = QTableWidgetItem("📐 Tensão")
                type_item.setBackground(COLORS.to_qcolor(COLORS.SECONDARY_LIGHT))
            else:
                type_item = QTableWidgetItem("🔍 Inspeção")
                type_item.setBackground(COLORS.to_qcolor(COLORS.SECONDARY_LIGHT))
            self.combined_table.setItem(row, 1, type_item)

            # Resultado
            result = record.result
            result_item = QTableWidgetItem(result)
            if result in ["OK", "PASS"]:
                result_item.setBackground(COLORS.to_qcolor(COLORS.SUCCESS))
            elif result in ["WARNING"]:
                result_item.setBackground(COLORS.to_qcolor(COLORS.WARNING_LIGHT))
            else:
                result_item.setBackground(COLORS.to_qcolor(COLORS.ERROR_LIGHT))
            self.combined_table.setItem(row, 2, result_item)

            # Detalhes
            if record_type == "tension":
                details = f"Média: {record.average_tension:.2f} N/cm²"
            else:
                details = f"OK: {record.ok_count} | Parcial: {record.partial_count} | Bloqueado: {record.blocked_count}"
            self.combined_table.setItem(row, 3, QTableWidgetItem(details))

            # Receita
            self.combined_table.setItem(row, 4, QTableWidgetItem(record.recipe_name or ""))

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
            var_text = f"📈 {var_text}"
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

    def _load_inspection_history(self):
        """Carrega histórico de inspeções visuais."""
        # Estatísticas
        stats = self.tracker.get_inspection_stats(self.code)

        self.lbl_insp_total.setText(str(stats["total_inspections"]))
        self.lbl_insp_pass.setText(f"{stats['pass_count']} ✓")
        self.lbl_insp_pass.setStyleSheet(f"color: {COLORS.SUCCESS}; font-weight: bold;")
        self.lbl_insp_fail.setText(f"{stats['fail_count']} ✗")
        self.lbl_insp_fail.setStyleSheet(f"color: {COLORS.ERROR}; font-weight: bold;")
        self.lbl_insp_rate.setText(f"{stats['pass_rate']:.1f}%")
        self.lbl_insp_avg_rate.setText(f"{stats['avg_pass_rate']:.1f}%")

        last_result = stats["last_result"]
        if last_result:
            if last_result == "PASS":
                self.lbl_insp_last.setText("✓ PASS")
                self.lbl_insp_last.setStyleSheet(f"color: {COLORS.SUCCESS}; font-weight: bold;")
            else:
                self.lbl_insp_last.setText("✗ FAIL")
                self.lbl_insp_last.setStyleSheet(f"color: {COLORS.ERROR}; font-weight: bold;")
        else:
            self.lbl_insp_last.setText("-")

        # Tabela de inspeção
        history = self.tracker.get_inspection_history(self.code, limit=50)
        self.inspection_table.setRowCount(len(history))

        self._inspection_records = history  # Guarda para abrir relatório

        for row, record in enumerate(history):
            try:
                dt = datetime.fromisoformat(record.timestamp)
                dt_str = dt.strftime("%d/%m/%Y %H:%M")
            except:
                dt_str = record.timestamp

            self.inspection_table.setItem(row, 0, QTableWidgetItem(dt_str))
            self.inspection_table.setItem(row, 1, QTableWidgetItem(str(record.total_apertures)))
            self.inspection_table.setItem(row, 2, QTableWidgetItem(str(record.ok_count)))
            self.inspection_table.setItem(row, 3, QTableWidgetItem(str(record.partial_count)))
            self.inspection_table.setItem(row, 4, QTableWidgetItem(str(record.blocked_count)))
            self.inspection_table.setItem(row, 5, QTableWidgetItem(f"{record.pass_rate:.1f}%"))

            result_item = QTableWidgetItem(record.result)
            if record.result == "PASS":
                result_item.setBackground(COLORS.to_qcolor(COLORS.SUCCESS))
            else:
                result_item.setBackground(COLORS.to_qcolor(COLORS.ERROR_LIGHT))
            self.inspection_table.setItem(row, 6, result_item)

            # Botão para abrir relatório
            report_text = "📄 Abrir" if record.report_path else "-"
            self.inspection_table.setItem(row, 7, QTableWidgetItem(report_text))

    def _open_report(self, row: int, col: int):
        """Abre relatório PDF ao clicar duas vezes."""
        if col != 7:  # Só na coluna de relatório
            return

        if row < len(self._inspection_records):
            record = self._inspection_records[row]
            if record.report_path:
                try:
                    os.startfile(record.report_path)
                except Exception as e:
                    QMessageBox.warning(
                        self, "Erro",
                        f"Não foi possível abrir o relatório:\n{e}"
                    )

    def _export_csv(self):
        """Exporta histórico para CSV."""
        from PyQt6.QtWidgets import QFileDialog

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Histórico Completo",
            f"historico_completo_{self.code}.csv",
            "CSV (*.csv)"
        )

        if not filepath:
            return

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                # Header
                f.write("Tipo,Data/Hora,Resultado,Detalhes,Receita\n")

                combined = self.tracker.get_combined_history(self.code, limit=1000)
                for item in combined:
                    record = item["record"]
                    record_type = item["type"]

                    if record_type == "tension":
                        details = f"Média: {record.average_tension:.2f}"
                    else:
                        details = f"OK: {record.ok_count} Parcial: {record.partial_count} Bloqueado: {record.blocked_count}"

                    f.write(
                        f"{record_type},"
                        f"{item['timestamp']},"
                        f"{record.result},"
                        f"\"{details}\","
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
