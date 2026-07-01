"""
dialogs/stencil/full_history_dialog.py
--------------------------------------
Diálogo para visualizar histórico completo de um stencil.
"""

import logging
from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QGridLayout,
    QGroupBox,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from aoi_lib.recipe_manager import TensionAcceptance
from aoi_lib.stencil_tracker import StencilTracker
from consumo_lib.managers.tension_criteria_manager import TensionCriteriaManager
from consumo_lib.services.tension_reclassification_service import reclassify_tension_history
from consumo_lib.ui import COLORS
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
        self.acceptance_criteria = self._load_acceptance_criteria()

        self.setWindowTitle(f"Histórico Completo - {code}")
        self.setMinimumSize(850, 600)

        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        stencil = self.tracker.get_stencil(self.code)
        if stencil:
            info_group = QGroupBox("Stencil")
            info_layout = QHBoxLayout(info_group)

            info_layout.addWidget(QLabel(f"<b>{stencil.code}</b>"))
            info_layout.addWidget(QLabel(f"| {stencil.description or '(sem descrição)'}"))
            info_layout.addWidget(QLabel(f"| Receita: {stencil.recipe_name or 'N/A'}"))
            self.lbl_stencil_total = QLabel(f"| Total de medições: {stencil.inspection_count}")
            info_layout.addWidget(self.lbl_stencil_total)
            info_layout.addStretch()

            layout.addWidget(info_group)

        self.tabs = QTabWidget()

        self.tension_tab = QWidget()
        self._setup_tension_tab()
        self.tabs.addTab(self.tension_tab, "Medições de Tensão")

        layout.addWidget(self.tabs, 1)

        btn_layout = QHBoxLayout()

        btn_export = StandardButton("Exportar CSV")
        btn_export.clicked.connect(self._export_csv)
        btn_layout.addWidget(btn_export)

        self.btn_delete = StandardButton("Excluir medição", variant="emergency")
        self.btn_delete.clicked.connect(self._delete_selected_measurement)
        self.btn_delete.setEnabled(self._is_admin_user())
        self.btn_delete.setToolTip("Disponível apenas para usuários admin.")
        btn_layout.addWidget(self.btn_delete)

        btn_layout.addStretch()

        btn_close = StandardButton("Fechar")
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)

        layout.addLayout(btn_layout)

    def _setup_tension_tab(self):
        """Configura aba de medições de tensão."""
        layout = QVBoxLayout(self.tension_tab)

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

        self.tension_table = QTableWidget()
        self.tension_table.setColumnCount(7)
        self.tension_table.setHorizontalHeaderLabels([
            "Data/Hora", "Média", "Mín", "Máx", "OK", "WARN", "Resultado"
        ])
        self.tension_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tension_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tension_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tension_table.setAlternatingRowColors(True)

        layout.addWidget(self.tension_table, 1)

    def _load_data(self):
        """Carrega todos os dados."""
        stencil = self.tracker.get_stencil(self.code)
        if stencil is not None and hasattr(self, "lbl_stencil_total"):
            self.lbl_stencil_total.setText(f"| Total de medições: {stencil.inspection_count}")
        self._load_tension_history()

    def _load_tension_history(self):
        """Carrega histórico de tensão."""
        analysis = self.tracker.get_trend_analysis(self.code)

        self.lbl_tension_total.setText(str(analysis.record_count))
        self.lbl_tension_first.setText(f"{analysis.first_average:.2f} N/cm²")
        self.lbl_tension_last.setText(f"{analysis.last_average:.2f} N/cm²")
        self.lbl_tension_moving.setText(f"{analysis.moving_average:.2f} N/cm²")

        var_text = f"{analysis.variation_percent:+.1f}%"
        if analysis.variation_percent < -5:
            self.lbl_tension_variation.setStyleSheet(f"color: {COLORS.ERROR}; font-weight: bold;")
        elif analysis.variation_percent > 5:
            self.lbl_tension_variation.setStyleSheet(f"color: {COLORS.SUCCESS}; font-weight: bold;")
        else:
            self.lbl_tension_variation.setStyleSheet(f"color: {COLORS.TEXT_DISABLED};")
        self.lbl_tension_variation.setText(var_text)

        trend_map = {
            "stable": ("Estável", COLORS.TEXT_DISABLED),
            "degrading": ("Em Degradação", COLORS.ERROR),
            "improving": ("Melhorando", COLORS.SUCCESS),
        }
        trend_text, trend_color = trend_map.get(analysis.trend, ("?", COLORS.TEXT_DISABLED))
        self.lbl_tension_trend.setText(trend_text)
        self.lbl_tension_trend.setStyleSheet(f"color: {trend_color}; font-weight: bold;")

        history = self._reclassified_history(limit=50)
        self.tension_table.setRowCount(len(history))

        for row, record in enumerate(history):
            try:
                dt = datetime.fromisoformat(record.timestamp)
                dt_str = dt.strftime("%d/%m/%Y %H:%M")
            except Exception:
                dt_str = record.timestamp

            timestamp_item = QTableWidgetItem(dt_str)
            timestamp_item.setData(Qt.ItemDataRole.UserRole, record.timestamp)
            self.tension_table.setItem(row, 0, timestamp_item)
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
            "CSV (*.csv)",
        )

        if not filepath:
            return

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("Data/Hora,Resultado,Media,Min,Max,OK,WARNING,NOK,Receita\n")

                for record in self._reclassified_history(limit=1000):
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
                self,
                "Exportação Concluída",
                f"Histórico exportado para:\n{filepath}",
            )

        except Exception as e:
            QMessageBox.critical(self, "Erro ao Exportar", f"Erro: {str(e)}")

    def _delete_selected_measurement(self):
        if not self._is_admin_user():
            QMessageBox.warning(
                self,
                "Permissão negada",
                "Apenas usuários admin podem excluir medições.",
            )
            return

        row = self.tension_table.currentRow()
        timestamp_item = self.tension_table.item(row, 0) if row >= 0 else None
        if timestamp_item is None:
            QMessageBox.warning(self, "Seleção", "Selecione uma medição para excluir.")
            return

        timestamp = timestamp_item.data(Qt.ItemDataRole.UserRole)
        if not timestamp:
            QMessageBox.critical(self, "Erro", "Não foi possível identificar a medição selecionada.")
            return

        average = self.tension_table.item(row, 1).text() if self.tension_table.item(row, 1) else "-"
        result = self.tension_table.item(row, 6).text() if self.tension_table.item(row, 6) else "-"
        reply = QMessageBox.question(
            self,
            "Confirmar exclusão",
            "Excluir esta medição do histórico?\n\n"
            f"Stencil: {self.code}\n"
            f"Data/Hora: {timestamp_item.text()}\n"
            f"Média: {average} N/cm²\n"
            f"Resultado: {result}\n\n"
            "Esta ação não pode ser desfeita.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            deleted = self.tracker.delete_tension_record(self.code, timestamp)
        except Exception as exc:
            log.exception("Erro ao excluir medição de tensão")
            QMessageBox.critical(self, "Erro", f"Erro ao excluir medição:\n{exc}")
            return

        if not deleted:
            QMessageBox.warning(self, "Medição não encontrada", "A medição selecionada não foi encontrada.")
            return

        self._notify_history_changed()
        self._load_data()
        QMessageBox.information(self, "Medição excluída", "A medição foi removida do histórico.")

    def _reclassified_history(self, limit: int):
        history = self.tracker.get_tension_history(self.code, limit=limit)
        return reclassify_tension_history(history, self.acceptance_criteria)

    def _load_acceptance_criteria(self):
        config_manager = self._find_parent_attribute("config_manager")
        if config_manager is None:
            return None

        criteria = TensionCriteriaManager(config_manager).get_criteria()
        return TensionAcceptance(
            min_tension=criteria.min_tension,
            max_tension=criteria.max_tension,
            warning_low=criteria.warning_low,
            warning_high=criteria.warning_high,
        )

    def _is_admin_user(self) -> bool:
        role_manager = self._find_parent_attribute("role_manager")
        if role_manager is not None and hasattr(role_manager, "get_current_role"):
            try:
                return role_manager.get_current_role() == "admin"
            except Exception:
                log.debug("Falha ao verificar RoleManager", exc_info=True)

        auth_service = self._find_parent_attribute("auth_service")
        if auth_service is not None and hasattr(auth_service, "get_current_user"):
            user = auth_service.get_current_user()
            role = getattr(getattr(user, "role", None), "value", None)
            return role == "admin"

        return False

    def _find_parent_attribute(self, name: str):
        widget = self
        while widget is not None:
            if hasattr(widget, name):
                return getattr(widget, name)
            widget = widget.parentWidget()
        return None

    def _notify_history_changed(self):
        wrapper = self._find_parent_attribute("stencil_manager_wrapper")
        if wrapper is not None and hasattr(wrapper, "refresh_stencil_views"):
            wrapper.refresh_stencil_views(stencil_code=self.code, select_stencil=True)
