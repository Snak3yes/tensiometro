"""
ReportDialogController - Controller para Diálogos de Relatório

Este controller gerencia os diálogos para geração e consulta de relatórios,
incluindo relatórios de tensão, histórico de stencil e consultas por período.

Responsabilidade:
- Gerar relatório de tensão da última medição
- Gerar relatório de histórico do stencil selecionado
- Consultar medições por período com exportação CSV

Signals Emitidos:
- tension_report_generated(output_path: str) - Relatório de tensão gerado
- stencil_report_generated(output_path: str) - Relatório de stencil gerado
- period_query_executed(record_count: int) - Consulta por período executada
- report_error(error: str) - Erro na geração de relatório
"""

import json
import logging
import subprocess
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QGroupBox, QFormLayout, QCheckBox,
    QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem, QDateEdit
)
from PyQt6.QtCore import QObject, pyqtSignal, QDate

logger = logging.getLogger("consumo_lib")


class ReportDialogController(QObject):
    """
    Controller para diálogos de relatório.

    Responsável por gerenciar geração de relatórios de tensão, histórico
    de stencil e consultas por período.
    """

    # Signals
    tension_report_generated = pyqtSignal(str)  # output_path
    stencil_report_generated = pyqtSignal(str)  # output_path
    period_query_executed = pyqtSignal(int)  # record_count
    report_error = pyqtSignal(str)  # error

    def __init__(self, report_manager_wrapper, stencil_manager_wrapper,
                 stencil_tracker, parent=None):
        """
        Inicializa o ReportDialogController.

        Args:
            report_manager_wrapper: Instância de ReportManagerWrapper
            stencil_manager_wrapper: Instância de StencilManagerWrapper
            stencil_tracker: Instância de StencilTracker
            parent: Widget pai (geralmente main_window)
        """
        super().__init__(parent)
        self.report_manager = report_manager_wrapper
        self.stencil_manager = stencil_manager_wrapper
        self.stencil_tracker = stencil_tracker
        self.parent_window = parent

        logger.debug("ReportDialogController inicializado")

    # =========================================================================
    # MÉTODOS PÚBLICOS
    # =========================================================================

    def show_tension_report_dialog(self):
        """Gera relatório de tensão da última medição."""
        # Tentar carregar última medição
        tension_file = Path("stencil_tension_measurements.json")

        if not tension_file.exists():
            QMessageBox.warning(
                self.parent_window, "Sem Dados",
                "Nenhuma medição de tensão disponível.\n\n"
                "Execute uma medição de tensão primeiro."
            )
            return

        try:
            with open(tension_file, 'r', encoding='utf-8') as f:
                tension_data = json.load(f)

            # Obter informações do stencil atual
            # Nota: O parent_window deve fornecer current_stencil
            stencil_code = None
            if hasattr(self.parent_window, 'current_stencil') and self.parent_window.current_stencil:
                stencil_code = self.parent_window.current_stencil.code

            # Gerar relatório via manager
            output_path = self.report_manager.generate_tension_report(
                tension_data=tension_data,
                stencil_code=stencil_code,
                operator=None  # TODO: Implementar campo de operador
            )

            if output_path:
                self.tension_report_generated.emit(output_path)

                # Perguntar se quer abrir o PDF
                reply = QMessageBox.question(
                    self.parent_window, "Relatório Gerado",
                    f"Relatório gerado com sucesso:\n{output_path}\n\n"
                    f"Deseja abrir o arquivo?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.Yes:
                    subprocess.Popen([output_path], shell=True)

        except Exception as e:
            logger.exception("Erro ao gerar relatório de tensão")
            error_msg = f"Erro ao gerar relatório:\n{str(e)}"
            self.report_error.emit(error_msg)
            QMessageBox.critical(
                self.parent_window, "Erro",
                error_msg
            )

    def show_stencil_report_dialog(self):
        """Gera relatório de histórico do stencil selecionado."""
        if not hasattr(self.parent_window, 'current_stencil') or not self.parent_window.current_stencil:
            QMessageBox.warning(
                self.parent_window, "Stencil Não Selecionado",
                "Selecione um stencil primeiro usando a aba de Rastreabilidade."
            )
            return

        # Obter histórico do stencil via manager
        current_stencil = self.parent_window.current_stencil
        history = self.stencil_manager.get_tension_history(current_stencil.code)

        if not history:
            QMessageBox.warning(
                self.parent_window, "Sem Histórico",
                f"O stencil {current_stencil.code} não possui histórico de medições."
            )
            return

        try:
            # Gerar relatório via manager
            output_path = self.report_manager.generate_stencil_history_report(
                stencil_code=current_stencil.code,
                include_tension=True,
                include_inspections=True
            )

            if output_path:
                self.stencil_report_generated.emit(output_path)

                # Perguntar se quer abrir
                reply = QMessageBox.question(
                    self.parent_window, "Relatório Gerado",
                    f"Relatório de histórico gerado:\n{output_path}\n\n"
                    f"Deseja abrir o arquivo?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.Yes:
                    subprocess.Popen([output_path], shell=True)

        except Exception as e:
            logger.exception("Erro ao gerar relatório de stencil")
            error_msg = f"Erro ao gerar relatório:\n{str(e)}"
            self.report_error.emit(error_msg)
            QMessageBox.critical(
                self.parent_window, "Erro",
                error_msg
            )

    def show_period_query_dialog(self):
        """Abre diálogo para consultar medições por período."""
        dialog = QDialog(self.parent_window)
        dialog.setWindowTitle("📅 Consultar por Período")
        dialog.setMinimumWidth(400)

        layout = QVBoxLayout(dialog)

        # Seleção de período
        period_group = QGroupBox("Período de Consulta")
        period_layout = QFormLayout(period_group)

        date_start = QDateEdit()
        date_start.setDate(QDate.currentDate().addMonths(-1))
        date_start.setCalendarPopup(True)
        period_layout.addRow("Data Inicial:", date_start)

        date_end = QDateEdit()
        date_end.setDate(QDate.currentDate())
        date_end.setCalendarPopup(True)
        period_layout.addRow("Data Final:", date_end)

        layout.addWidget(period_group)

        # Opções
        options_group = QGroupBox("Opções")
        options_layout = QVBoxLayout(options_group)

        chk_all_stencils = QCheckBox("Todos os stencils")
        chk_all_stencils.setChecked(True)
        options_layout.addWidget(chk_all_stencils)

        layout.addWidget(options_group)

        # Lista de resultados
        result_table = QTableWidget()
        result_table.setColumnCount(5)
        result_table.setHorizontalHeaderLabels(["Data", "Stencil", "Média", "Resultado", "Operador"])
        result_table.setMinimumHeight(200)
        layout.addWidget(result_table)

        # Botões
        btn_layout = QHBoxLayout()

        btn_search = QPushButton("🔍 Buscar")

        def do_search():
            # Converter datas
            start = date_start.date().toPyDate()
            end = date_end.date().toPyDate()

            # Buscar em todos os stencils
            all_records = []
            stencils = self.stencil_tracker.list_stencils()

            for stencil in stencils:
                history = self.stencil_tracker.get_tension_history(stencil.code)
                for record in history:
                    try:
                        ts = record.timestamp if hasattr(record, 'timestamp') else record.get('timestamp', '')
                        from datetime import datetime
                        dt = datetime.fromisoformat(ts).date()
                        if start <= dt <= end:
                            all_records.append((stencil.code, record))
                    except:
                        pass

            # Preencher tabela
            result_table.setRowCount(len(all_records))
            for i, (code, record) in enumerate(all_records):
                ts = record.timestamp if hasattr(record, 'timestamp') else record.get('timestamp', '')
                avg = record.average_tension if hasattr(record, 'average_tension') else record.get('average_tension', 0)
                result_field = record.result if hasattr(record, 'result') else record.get('result', 'OK')
                op = record.operator if hasattr(record, 'operator') else record.get('operator', '-')

                result_table.setItem(i, 0, QTableWidgetItem(ts[:16]))
                result_table.setItem(i, 1, QTableWidgetItem(code))
                result_table.setItem(i, 2, QTableWidgetItem(f"{avg:.2f}"))
                result_table.setItem(i, 3, QTableWidgetItem(result_field))
                result_table.setItem(i, 4, QTableWidgetItem(op or "-"))

            self.period_query_executed.emit(len(all_records))
            if hasattr(self.parent_window, 'statusBar'):
                self.parent_window.statusBar().showMessage(f"{len(all_records)} registros encontrados", 3000)

        btn_search.clicked.connect(do_search)
        btn_layout.addWidget(btn_search)

        btn_export = QPushButton("📄 Exportar CSV")

        def do_export():
            if result_table.rowCount() == 0:
                QMessageBox.warning(dialog, "Sem Dados", "Execute uma busca primeiro.")
                return

            filepath, _ = QFileDialog.getSaveFileName(
                dialog, "Exportar CSV", "", "CSV (*.csv)"
            )
            if filepath:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write("Data,Stencil,Média,Resultado,Operador\n")
                    for row in range(result_table.rowCount()):
                        cols = [result_table.item(row, c).text() for c in range(5)]
                        f.write(",".join(cols) + "\n")
                QMessageBox.information(dialog, "Exportado", f"Dados exportados para:\n{filepath}")

        btn_export.clicked.connect(do_export)
        btn_layout.addWidget(btn_export)

        btn_layout.addStretch()

        btn_close = QPushButton("Fechar")
        btn_close.clicked.connect(dialog.accept)
        btn_layout.addWidget(btn_close)

        layout.addLayout(btn_layout)

        dialog.exec()

    # =========================================================================
    # UI HANDLERS (Migrados do SignalAggregator)
    # =========================================================================

    def setup_ui_handlers(self):
        """
        Configura handlers de UI para signals de relatório.

        Este método conecta os signals internos do ReportDialogController
        aos métodos que atualizam a UI do main_window.

        Deve ser chamado durante a inicialização do main_window.
        """
        # Conectar signals a handlers de UI
        self.tension_report_generated.connect(self._on_tension_report_generated_update_status)
        self.stencil_report_generated.connect(self._on_stencil_report_generated_update_status)
        self.period_query_executed.connect(self._on_period_query_executed_log)
        self.report_error.connect(self._on_report_error_log)

        logger.debug("UI handlers conectados no ReportDialogController")

    def _on_tension_report_generated_update_status(self, output_path: str):
        """
        Atualiza statusBar quando relatório de tensão é gerado.

        Args:
            output_path: Caminho do relatório gerado
        """
        logger.info(f"Relatório de tensão gerado: {output_path}")

        if hasattr(self.parent(), 'statusBar'):
            self.parent().statusBar().showMessage(f"Relatório salvo: {output_path}", 5000)

    def _on_stencil_report_generated_update_status(self, output_path: str):
        """
        Atualiza statusBar quando relatório de stencil é gerado.

        Args:
            output_path: Caminho do relatório gerado
        """
        logger.info(f"Relatório de stencil gerado: {output_path}")

        if hasattr(self.parent(), 'statusBar'):
            self.parent().statusBar().showMessage(f"Relatório salvo: {output_path}", 5000)

    def _on_period_query_executed_log(self, record_count: int):
        """
        Log quando consulta por período é executada.

        Args:
            record_count: Número de registros encontrados
        """
        logger.info(f"Consulta por período executada: {record_count} registros")

    def _on_report_error_log(self, error: str):
        """
        Log erro quando geração de relatório falha.

        Args:
            error: Mensagem de erro
        """
        logger.error(f"Erro na geração de relatório: {error}")
