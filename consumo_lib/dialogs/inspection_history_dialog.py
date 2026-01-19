"""
Dialog de Histórico de Inspeções

Exibe lista de inspeções anteriores com filtros e exportação.
"""

import logging
import csv
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QComboBox, QDateEdit, QLineEdit, QHeaderView,
    QFileDialog, QMessageBox, QFrame, QWidget
)
from PyQt6.QtCore import Qt, QDate

from consumo_lib.ui import COLORS, TYPO, SPACE, DIM

logger = logging.getLogger(__name__)


class InspectionHistoryDialog(QDialog):
    """
    Dialog de histórico de inspeções

    Mostra todas as inspeções de um stencil com filtros.
    """

    def __init__(self, stencil_code: str, parent=None):
        """
        Inicializa dialog de histórico

        Args:
            stencil_code: Código do stencil
            parent: Widget pai
        """
        super().__init__(parent)
        self.stencil_code = stencil_code
        self.all_records = []  # Todos os registros carregados

        self.setup_ui()
        self.load_history()

    def setup_ui(self):
        """Configura interface do dialog"""
        self.setWindowTitle("Histórico de Inspeções")
        self.setModal(True)
        self.setFixedSize(1000, 700)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(15)

        # Título
        title_label = QLabel(f"Histórico: {self.stencil_code}")
        title_label.setFont(TYPO.get_font(TYPO.DISPLAY_SMALL, bold=True))
        title_label.setStyleSheet(f"color: {COLORS.ON_BACKGROUND};")
        layout.addWidget(title_label)

        # Filtros
        filters_frame = self._create_filters_frame()
        layout.addWidget(filters_frame)

        # Tabela
        table_label = QLabel("Inspeções")
        table_label.setFont(TYPO.get_font(TYPO.HEADING_MEDIUM, bold=True))
        table_label.setStyleSheet(f"color: {COLORS.ON_SURFACE};")
        layout.addWidget(table_label)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Data/Hora", "Tipo", "Classificação", "Operador", "Arquivo"])
        self.table.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid {COLORS.OUTLINE};
                border-radius: {DIM.RADIUS_SM}px;
                background-color: white;
                selection-background-color: {COLORS.PRIMARY};
            }}
            QTableWidget::item {{
                padding: {SPACE.SM}px;
                border-bottom: 1px solid {COLORS.SURFACE};
            }}
            QHeaderView::section {{
                background-color: {COLORS.SURFACE};
                color: {COLORS.ON_SURFACE};
                font-weight: bold;
                border: none;
                border-bottom: 2px solid {COLORS.OUTLINE};
                padding: {SPACE.SM}px;
            }}
        """)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        # Botões
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        self.export_button = QPushButton("📄 Exportar CSV")
        self.export_button.setMinimumHeight(DIM.BUTTON_HEIGHT_MD)
        self.export_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.SECONDARY};
                color: white;
                font-size: 13px;
                font-weight: 600;
                border: none;
                border-radius: {DIM.RADIUS_SM}px;
                padding: {SPACE.SM}px {SPACE.MD}px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.SECONDARY_DARK};
            }}
        """)
        self.export_button.clicked.connect(self.export_to_csv)
        buttons_layout.addWidget(self.export_button)

        close_button = QPushButton("Fechar")
        close_button.setMinimumHeight(DIM.BUTTON_HEIGHT_MD)
        close_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.ON_SURFACE};
                color: white;
                font-size: 13px;
                font-weight: 600;
                border: none;
                border-radius: {DIM.RADIUS_SM}px;
                padding: {SPACE.SM}px {SPACE.MD}px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.OUTLINE};
            }}
        """)
        close_button.clicked.connect(self.accept)
        buttons_layout.addWidget(close_button)

        layout.addLayout(buttons_layout)

    def _create_filters_frame(self) -> QFrame:
        """Cria frame de filtros"""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                border: 2px solid {COLORS.OUTLINE};
                border-radius: {DIM.RADIUS_MD}px;
                background-color: {COLORS.SURFACE};
                padding: {SPACE.MD}px;
            }}
        """)

        layout = QVBoxLayout(frame)
        layout.setSpacing(10)

        # Título
        filters_title = QLabel("FILTROS")
        filters_title.setFont(TYPO.get_font(TYPO.BODY_LARGE, bold=True))
        filters_title.setStyleSheet(f"color: {COLORS.ON_SURFACE};")
        layout.addWidget(filters_title)

        # Linha 1: Tipo e Classificação
        line1 = QHBoxLayout()
        line1.setSpacing(15)

        # Tipo
        line1.addWidget(QLabel("Tipo:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Todos", "Tensão", "Inspeção Visual", "Ambos"])
        self.type_combo.currentTextChanged.connect(self.apply_filters)
        self.type_combo.setMinimumWidth(150)
        line1.addWidget(self.type_combo)

        line1.addStretch()

        # Classificação
        line1.addWidget(QLabel("Classificação:"))
        self.class_combo = QComboBox()
        self.class_combo.addItems(["Todas", "Aprovado", "Atenção", "Reprovado"])
        self.class_combo.currentTextChanged.connect(self.apply_filters)
        self.class_combo.setMinimumWidth(150)
        line1.addWidget(self.class_combo)

        layout.addLayout(line1)

        # Linha 2: Período
        line2 = QHBoxLayout()
        line2.setSpacing(15)

        line2.addWidget(QLabel("Período:"))
        line2.addWidget(QLabel("De:"))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_from.dateChanged.connect(self.apply_filters)
        line2.addWidget(self.date_from)

        line2.addWidget(QLabel("Até:"))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.dateChanged.connect(self.apply_filters)
        line2.addWidget(self.date_to)

        line2.addStretch()

        # Operador
        line2.addWidget(QLabel("Operador:"))
        self.operator_search = QLineEdit()
        self.operator_search.setPlaceholderText("Digite para filtrar...")
        self.operator_search.textChanged.connect(self.apply_filters)
        self.operator_search.setMinimumWidth(200)
        line2.addWidget(self.operator_search)

        layout.addLayout(line2)

        # Botões
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        apply_button = QPushButton("Aplicar Filtros")
        apply_button.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                font-size: 12px;
                font-weight: 600;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
        """)
        apply_button.clicked.connect(self.apply_filters)
        buttons_layout.addWidget(apply_button)

        clear_button = QPushButton("Limpar Filtros")
        clear_button.setStyleSheet("""
            QPushButton {
                background-color: #6B7280;
                color: white;
                font-size: 12px;
                font-weight: 600;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #4B5563;
            }
        """)
        clear_button.clicked.connect(self.clear_filters)
        buttons_layout.addWidget(clear_button)

        layout.addLayout(buttons_layout)

        return frame

    def load_history(self):
        """Carrega histórico do stencil"""
        from aoi_lib import StencilTracker

        try:
            tracker = StencilTracker()
            stencil = tracker.get_stencil(self.stencil_code)

            if not stencil:
                QMessageBox.warning(
                    self,
                    "Stencil Não Encontrado",
                    f"Stencil {self.stencil_code} não possui histórico ainda.\n\n"
                    "Execute algumas inspeções primeiro."
                )
                return

            # Carrega registros de tensão
            tension_records = tracker.get_tension_history(self.stencil_code)

            # Carrega registros de inspeção
            inspection_records = tracker.get_inspection_history(self.stencil_code)

            # Combina e formata para exibição
            self.all_records = []

            for record in tension_records:
                self.all_records.append({
                    'type': 'Tensão',
                    'timestamp': record.timestamp,
                    'classification': record.result,
                    'operator': record.operator or 'N/A',
                    'file': Path(record.timestamp).strftime("%Y%m%d_%H%M%S_tension.json"),
                    'raw': record
                })

            for record in inspection_records:
                self.all_records.append({
                    'type': 'Inspeção Visual',
                    'timestamp': record.timestamp,
                    'classification': record.result,
                    'operator': record.operator or 'N/A',
                    'file': Path(record.timestamp).strftime("%Y%m%d_%H%M%S_inspection.json"),
                    'raw': record
                })

            # Ordena por timestamp (mais recente primeiro)
            self.all_records.sort(key=lambda x: x['timestamp'], reverse=True)

            # Aplica filtros iniciais e popula tabela
            self.apply_filters()

        except Exception as e:
            logger.error(f"Erro ao carregar histórico: {e}")
            QMessageBox.critical(
                self,
                "Erro ao Carregar",
                f"Não foi possível carregar o histórico:\n\n{str(e)}"
            )

    def apply_filters(self):
        """Aplica filtros e atualiza tabela"""
        # Obtém valores dos filtros
        type_filter = self.type_combo.currentText()
        class_filter = self.class_combo.currentText()
        date_from = self.date_from.date().toString("yyyy-MM-dd")
        date_to = self.date_to.date().toString("yyyy-MM-dd")
        operator_filter = self.operator_search.text().lower()

        # Filtra registros
        filtered = []

        for record in self.all_records:
            # Filtro de tipo
            if type_filter != "Todos":
                if type_filter == "Tensão" and record['type'] != "Tensão":
                    continue
                if type_filter == "Inspeção Visual" and record['type'] != "Inspeção Visual":
                    continue
                if type_filter == "Ambos":
                    # "Ambos" não se aplica a filtros de histórico individual
                    continue

            # Filtro de classificação
            if class_filter != "Todas":
                rec_class = record['classification']
                if class_filter == "Aprovado" and rec_class not in ["OK", "PASS"]:
                    continue
                if class_filter == "Atenção" and rec_class not in ["WARNING"]:
                    continue
                if class_filter == "Reprovado" and rec_class not in ["NOK", "FAIL"]:
                    continue

            # Filtro de período
            rec_date = record['timestamp'][:10]  # YYYY-MM-DD
            if rec_date < date_from or rec_date > date_to:
                continue

            # Filtro de operador
            if operator_filter and operator_filter not in record['operator'].lower():
                continue

            filtered.append(record)

        # Atualiza tabela
        self.populate_table(filtered)

    def clear_filters(self):
        """Limpa todos os filtros"""
        self.type_combo.setCurrentText("Todos")
        self.class_combo.setCurrentText("Todas")
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_to.setDate(QDate.currentDate())
        self.operator_search.clear()
        self.apply_filters()

    def populate_table(self, records):
        """Popula tabela com registros filtrados"""
        self.table.setRowCount(len(records))

        for row, record in enumerate(records):
            # Data/Hora
            dt = datetime.fromisoformat(record['timestamp'])
            dt_str = dt.strftime("%d/%m/%Y %H:%M")
            item = QTableWidgetItem(dt_str)
            item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 0, item)

            # Tipo
            type_item = QTableWidgetItem(record['type'])
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 1, type_item)

            # Classificação (com cor)
            class_text = self._get_classification_label(record['classification'])
            class_item = QTableWidgetItem(class_text)
            class_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            class_item.setForeground(self._get_classification_color(record['classification']))
            self.table.setItem(row, 2, class_item)

            # Operador
            op_item = QTableWidgetItem(record['operator'])
            op_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 3, op_item)

            # Arquivo
            file_item = QTableWidgetItem(record['file'])
            file_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 4, file_item)

        # Atualiza label com contador
        # (O label está fora do método, então não atualizamos aqui)

    def _get_classification_label(self, classification: str) -> str:
        """Retorna label legível da classificação"""
        if classification in ["OK", "PASS"]:
            return "✅ Aprovado"
        elif classification == "WARNING":
            return "⚠️ Atenção"
        elif classification in ["NOK", "FAIL"]:
            return "❌ Reprovado"
        return classification

    def _get_classification_color(self, classification: str):
        """Retorna cor da classificação"""
        from PyQt6.QtGui import QColor
        if classification in ["OK", "PASS"]:
            return QColor("#10B981")
        elif classification == "WARNING":
            return QColor("#F59E0B")
        elif classification in ["NOK", "FAIL"]:
            return QColor("#EF4444")
        return QColor("#374151")

    def export_to_csv(self):
        """Exporta tabela para CSV"""
        if self.table.rowCount() == 0:
            QMessageBox.warning(self, "Exportar", "Não há dados para exportar.")
            return

        # Dialog para selecionar arquivo
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar CSV",
            f"{self.stencil_code}_historico.csv",
            "Arquivos CSV (*.csv)"
        )

        if not filename:
            return

        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                # Header
                headers = []
                for col in range(self.table.columnCount()):
                    headers.append(self.table.horizontalHeaderItem(col).text())
                writer.writerow(headers)

                # Data
                for row in range(self.table.rowCount()):
                    data = []
                    for col in range(self.table.columnCount()):
                        item = self.table.item(row, col)
                        data.append(item.text() if item else "")
                    writer.writerow(data)

            QMessageBox.information(
                self,
                "Exportar Concluído",
                f"Dados exportados com sucesso para:\n\n{filename}"
            )
            logger.info(f"Histórico exportado para {filename}")

        except Exception as e:
            logger.error(f"Erro ao exportar CSV: {e}")
            QMessageBox.critical(
                self,
                "Erro ao Exportar",
                f"Não foi possível exportar os dados:\n\n{str(e)}"
            )
