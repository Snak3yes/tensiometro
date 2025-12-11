"""
stencil_tracker_ui.py
----------------------
Widgets PyQt6 para interface de rastreabilidade de stencils.

Componentes:
- StencilIdentificationWidget: Painel para identificar/selecionar stencil
- StencilHistoryDialog: Diálogo para visualizar histórico e tendência
- StencilManagerDialog: Diálogo para gerenciar cadastro de stencils
"""

import logging
from datetime import datetime
from typing import Optional, List, Callable

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QGroupBox, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QDialogButtonBox, QMessageBox, QTextEdit,
    QComboBox, QSplitter, QTabWidget, QFormLayout,
    QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor

from .stencil_tracker import (
    StencilTracker, Stencil, TensionRecord, TrendAnalysis
)

log = logging.getLogger(__name__)


# ============================================================================
#  WIDGET DE IDENTIFICAÇÃO DE STENCIL
# ============================================================================

class StencilIdentificationWidget(QWidget):
    """
    Widget para identificação e seleção de stencil.
    
    Permite:
    - Entrada de código de barras (manual ou leitor USB)
    - Visualização de informações do stencil selecionado
    - Acesso rápido ao histórico
    
    Signals:
        stencil_selected: Emitido quando um stencil é selecionado/carregado
        stencil_cleared: Emitido quando a seleção é limpa
    """
    
    stencil_selected = pyqtSignal(object)  # Stencil
    stencil_cleared = pyqtSignal()
    recipe_requested = pyqtSignal(str)  # Nome da receita para carregar
    
    def __init__(self, tracker: StencilTracker, parent=None):
        super().__init__(parent)
        self.tracker = tracker
        self.current_stencil: Optional[Stencil] = None
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # ================== ENTRADA DE CÓDIGO ==================
        input_group = QGroupBox("🏷️ Identificação do Stencil")
        input_layout = QHBoxLayout(input_group)
        
        input_layout.addWidget(QLabel("Código:"))
        
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Escaneie ou digite o código de barras...")
        self.code_input.setMinimumWidth(250)
        self.code_input.setFont(QFont("Consolas", 12))
        input_layout.addWidget(self.code_input, 1)
        
        self.btn_load = QPushButton("🔍 Carregar")
        self.btn_load.setDefault(True)
        input_layout.addWidget(self.btn_load)
        
        self.btn_clear = QPushButton("✖ Limpar")
        self.btn_clear.setEnabled(False)
        input_layout.addWidget(self.btn_clear)
        
        layout.addWidget(input_group)
        
        # ================== INFORMAÇÕES DO STENCIL ==================
        self.info_frame = QFrame()
        self.info_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.info_frame.setVisible(False)
        info_layout = QGridLayout(self.info_frame)
        
        # Status indicator
        self.status_label = QLabel("●")
        self.status_label.setFont(QFont("Arial", 16))
        info_layout.addWidget(self.status_label, 0, 0)
        
        # Código e descrição
        self.lbl_code = QLabel()
        self.lbl_code.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        info_layout.addWidget(self.lbl_code, 0, 1)
        
        self.lbl_description = QLabel()
        self.lbl_description.setStyleSheet("color: #666;")
        info_layout.addWidget(self.lbl_description, 0, 2)
        
        # Receita
        info_layout.addWidget(QLabel("Receita:"), 1, 0)
        self.lbl_recipe = QLabel()
        self.lbl_recipe.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(self.lbl_recipe, 1, 1, 1, 2)
        
        # Última inspeção
        info_layout.addWidget(QLabel("Última inspeção:"), 2, 0)
        self.lbl_last_inspection = QLabel()
        info_layout.addWidget(self.lbl_last_inspection, 2, 1)
        
        self.lbl_inspection_count = QLabel()
        self.lbl_inspection_count.setStyleSheet("color: #888;")
        info_layout.addWidget(self.lbl_inspection_count, 2, 2)
        
        # Alerta de tendência
        self.alert_frame = QFrame()
        self.alert_frame.setVisible(False)
        self.alert_frame.setStyleSheet("""
            QFrame {
                background-color: #FFF3CD;
                border: 1px solid #FFECB5;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        alert_layout = QHBoxLayout(self.alert_frame)
        alert_layout.setContentsMargins(10, 5, 10, 5)
        
        self.lbl_alert = QLabel()
        self.lbl_alert.setWordWrap(True)
        alert_layout.addWidget(self.lbl_alert, 1)
        
        info_layout.addWidget(self.alert_frame, 3, 0, 1, 3)
        
        # Botões de ação
        btn_layout = QHBoxLayout()
        
        self.btn_history = QPushButton("📊 Histórico")
        self.btn_history.clicked.connect(self._show_history)
        btn_layout.addWidget(self.btn_history)
        
        self.btn_edit = QPushButton("✏️ Editar")
        self.btn_edit.clicked.connect(self._edit_stencil)
        btn_layout.addWidget(self.btn_edit)
        
        btn_layout.addStretch()
        
        info_layout.addLayout(btn_layout, 4, 0, 1, 3)
        
        layout.addWidget(self.info_frame)
        
        # ================== MENSAGEM QUANDO VAZIO ==================
        self.empty_label = QLabel(
            "Nenhum stencil selecionado.\n"
            "Escaneie ou digite o código de barras para iniciar."
        )
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: #888; font-style: italic;")
        layout.addWidget(self.empty_label)
        
        layout.addStretch()
    
    def _connect_signals(self):
        self.code_input.returnPressed.connect(self._load_stencil)
        self.btn_load.clicked.connect(self._load_stencil)
        self.btn_clear.clicked.connect(self._clear_selection)
    
    def _load_stencil(self):
        """Carrega stencil pelo código digitado."""
        code = self.code_input.text().strip()
        
        if not code:
            QMessageBox.warning(
                self, "Código Vazio",
                "Digite ou escaneie o código do stencil."
            )
            return
        
        # Verifica se stencil existe
        stencil = self.tracker.get_stencil(code)
        
        if not stencil:
            QMessageBox.warning(
                self, "Programa Não Existe",
                f"O programa '{code}' não existe no sistema.\n\n"
                "Verifique o código ou solicite à engenharia para cadastrar."
            )
            self.code_input.selectAll()
            self.code_input.setFocus()
            return
        
        self._select_stencil(stencil)
    
    def _select_stencil(self, stencil: Stencil):
        """Seleciona um stencil e atualiza a interface."""
        self.current_stencil = stencil
        
        # Atualiza UI
        self.empty_label.setVisible(False)
        self.info_frame.setVisible(True)
        self.btn_clear.setEnabled(True)
        
        # Status com cor
        status_colors = {
            "active": ("🟢", "#28a745"),
            "warning": ("🟡", "#ffc107"),
            "retired": ("🔴", "#dc3545"),
        }
        icon, color = status_colors.get(stencil.status, ("⚪", "#888"))
        self.status_label.setText(icon)
        
        # Informações
        self.lbl_code.setText(stencil.code)
        self.lbl_description.setText(stencil.description or "(sem descrição)")
        self.lbl_recipe.setText(stencil.recipe_name or "(nenhuma receita)")
        
        if stencil.last_inspection:
            try:
                dt = datetime.fromisoformat(stencil.last_inspection)
                self.lbl_last_inspection.setText(dt.strftime("%d/%m/%Y %H:%M"))
            except:
                self.lbl_last_inspection.setText(stencil.last_inspection)
        else:
            self.lbl_last_inspection.setText("Nunca inspecionado")
        
        self.lbl_inspection_count.setText(f"({stencil.inspection_count} inspeções)")
        
        # Verifica alertas de tendência
        if stencil.recipe_name:
            # TODO: Obter warning_low da receita
            alert = self.tracker.check_degradation_alert(stencil.code)
            if alert:
                self.alert_frame.setVisible(True)
                self.lbl_alert.setText(alert)
            else:
                self.alert_frame.setVisible(False)
        else:
            self.alert_frame.setVisible(False)
        
        # Emite sinal
        self.stencil_selected.emit(stencil)
        
        # Solicita carregamento da receita
        if stencil.recipe_name:
            self.recipe_requested.emit(stencil.recipe_name)
        
        log.info(f"Stencil selecionado: {stencil.code}")
    
    def _clear_selection(self):
        """Limpa a seleção atual."""
        self.current_stencil = None
        self.code_input.clear()
        self.info_frame.setVisible(False)
        self.empty_label.setVisible(True)
        self.btn_clear.setEnabled(False)
        self.alert_frame.setVisible(False)
        
        self.stencil_cleared.emit()
        log.info("Seleção de stencil limpa")
    
    def _show_history(self):
        """Abre diálogo de histórico."""
        if not self.current_stencil:
            return
        
        dialog = StencilHistoryDialog(
            self.tracker, 
            self.current_stencil.code, 
            self
        )
        dialog.exec()
    
    def _edit_stencil(self):
        """Abre diálogo para editar stencil."""
        if not self.current_stencil:
            return
        
        dialog = StencilEditDialog(
            self.tracker,
            self.current_stencil,
            self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Recarrega stencil atualizado
            stencil = self.tracker.get_stencil(self.current_stencil.code)
            if stencil:
                self._select_stencil(stencil)
    
    def get_current_stencil(self) -> Optional[Stencil]:
        """Retorna stencil atualmente selecionado."""
        return self.current_stencil
    
    def set_stencil_code(self, code: str):
        """Define código programaticamente e carrega."""
        self.code_input.setText(code)
        self._load_stencil()


# ============================================================================
#  DIÁLOGO DE HISTÓRICO
# ============================================================================

class StencilHistoryDialog(QDialog):
    """
    Diálogo para visualizar histórico de inspeções de um stencil.
    
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
        
        trend_layout.addWidget(QLabel("Total de inspeções:"), 0, 0)
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
        self.lbl_trend.setFont(QFont("Arial", 10, QFont.Weight.Bold))
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
        
        btn_export = QPushButton("📥 Exportar CSV")
        btn_export.clicked.connect(self._export_csv)
        btn_layout.addWidget(btn_export)
        
        btn_layout.addStretch()
        
        btn_close = QPushButton("Fechar")
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
            self.lbl_variation.setStyleSheet("color: #dc3545;")
        elif analysis.variation_percent > 5:
            var_text = f"📈 {var_text}"
            self.lbl_variation.setStyleSheet("color: #28a745;")
        else:
            self.lbl_variation.setStyleSheet("color: #888;")
        self.lbl_variation.setText(var_text)
        
        # Tendência com cor
        trend_map = {
            "stable": ("Estável", "#888"),
            "degrading": ("Em Degradação ⚠️", "#dc3545"),
            "improving": ("Melhorando ✓", "#28a745"),
        }
        trend_text, trend_color = trend_map.get(
            analysis.trend, ("Desconhecida", "#888")
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
                result_item.setBackground(QColor("#d4edda"))
            elif record.result == "WARNING":
                result_item.setBackground(QColor("#fff3cd"))
            else:
                result_item.setBackground(QColor("#f8d7da"))
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


# ============================================================================
#  DIÁLOGO DE EDIÇÃO
# ============================================================================

class StencilEditDialog(QDialog):
    """Diálogo para editar informações de um stencil."""
    
    def __init__(self, tracker: StencilTracker, stencil: Stencil, parent=None):
        super().__init__(parent)
        self.tracker = tracker
        self.stencil = stencil
        
        self.setWindowTitle(f"Editar Stencil - {stencil.code}")
        self.setMinimumWidth(400)
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        form = QFormLayout()
        
        # Código (somente leitura)
        self.lbl_code = QLabel(self.stencil.code)
        self.lbl_code.setFont(QFont("Consolas", 11))
        form.addRow("Código:", self.lbl_code)
        
        # Descrição
        self.txt_description = QLineEdit(self.stencil.description)
        form.addRow("Descrição:", self.txt_description)
        
        # Receita
        self.txt_recipe = QLineEdit(self.stencil.recipe_name or "")
        self.txt_recipe.setPlaceholderText("Nome da receita associada")
        form.addRow("Receita:", self.txt_recipe)
        
        # Status
        self.cmb_status = QComboBox()
        self.cmb_status.addItems(["active", "warning", "retired"])
        self.cmb_status.setCurrentText(self.stencil.status)
        form.addRow("Status:", self.cmb_status)
        
        # Notas
        self.txt_notes = QTextEdit()
        self.txt_notes.setPlainText(self.stencil.notes)
        self.txt_notes.setMaximumHeight(100)
        form.addRow("Observações:", self.txt_notes)
        
        layout.addLayout(form)
        
        # Botões
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _save(self):
        """Salva alterações."""
        self.stencil.description = self.txt_description.text().strip()
        self.stencil.recipe_name = self.txt_recipe.text().strip() or None
        self.stencil.status = self.cmb_status.currentText()
        self.stencil.notes = self.txt_notes.toPlainText().strip()
        
        try:
            self.tracker.update_stencil(self.stencil)
            self.accept()
        except Exception as e:
            QMessageBox.critical(
                self, "Erro ao Salvar",
                f"Erro: {str(e)}"
            )


# ============================================================================
#  DIÁLOGO DE CADASTRO
# ============================================================================

class StencilCreateDialog(QDialog):
    """Diálogo para cadastrar novo stencil."""
    
    def __init__(self, tracker: StencilTracker, 
                 initial_code: str = "",
                 parent=None):
        super().__init__(parent)
        self.tracker = tracker
        self.created_stencil: Optional[Stencil] = None
        
        self.setWindowTitle("Cadastrar Novo Stencil")
        self.setMinimumWidth(400)
        
        self._setup_ui()
        
        if initial_code:
            self.txt_code.setText(initial_code)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        info = QLabel(
            "ℹ️ Cadastre um novo programa de stencil.\n"
            "O código é o identificador único (código de barras)."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(info)
        
        form = QFormLayout()
        
        # Código (obrigatório)
        self.txt_code = QLineEdit()
        self.txt_code.setFont(QFont("Consolas", 11))
        self.txt_code.setPlaceholderText("Código de barras (obrigatório)")
        form.addRow("Código*:", self.txt_code)
        
        # Descrição
        self.txt_description = QLineEdit()
        self.txt_description.setPlaceholderText("Descrição auxiliar")
        form.addRow("Descrição:", self.txt_description)
        
        # Receita
        self.txt_recipe = QLineEdit()
        self.txt_recipe.setPlaceholderText("Nome exato da receita")
        form.addRow("Receita:", self.txt_recipe)
        
        layout.addLayout(form)
        
        # Botões
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._create)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _create(self):
        """Cria o stencil."""
        code = self.txt_code.text().strip()
        
        if not code:
            QMessageBox.warning(
                self, "Código Obrigatório",
                "Digite o código do stencil."
            )
            self.txt_code.setFocus()
            return
        
        if self.tracker.stencil_exists(code):
            QMessageBox.warning(
                self, "Código Já Existe",
                f"O código '{code}' já está cadastrado."
            )
            return
        
        try:
            self.created_stencil = self.tracker.create_stencil(
                code=code,
                description=self.txt_description.text().strip(),
                recipe_name=self.txt_recipe.text().strip() or None,
            )
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self, "Erro ao Cadastrar",
                f"Erro: {str(e)}"
            )
    
    def get_created_stencil(self) -> Optional[Stencil]:
        return self.created_stencil


# ============================================================================
#  DIÁLOGO DE GERENCIAMENTO
# ============================================================================

class StencilManagerDialog(QDialog):
    """
    Diálogo para gerenciamento de stencils cadastrados.
    
    Permite:
    - Listar todos os stencils
    - Criar novos
    - Editar existentes
    - Filtrar por status
    """
    
    def __init__(self, tracker: StencilTracker, parent=None):
        super().__init__(parent)
        self.tracker = tracker
        
        self.setWindowTitle("Gerenciar Stencils")
        self.setMinimumSize(800, 500)
        
        self._setup_ui()
        self._load_stencils()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # ================== FILTROS ==================
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("Filtrar por status:"))
        
        self.cmb_filter = QComboBox()
        self.cmb_filter.addItems(["Todos", "Ativos", "Alerta", "Retirados"])
        self.cmb_filter.currentIndexChanged.connect(self._load_stencils)
        filter_layout.addWidget(self.cmb_filter)
        
        filter_layout.addStretch()
        
        self.btn_new = QPushButton("➕ Novo Stencil")
        self.btn_new.clicked.connect(self._create_new)
        filter_layout.addWidget(self.btn_new)
        
        self.btn_refresh = QPushButton("🔄 Atualizar")
        self.btn_refresh.clicked.connect(self._load_stencils)
        filter_layout.addWidget(self.btn_refresh)
        
        layout.addLayout(filter_layout)
        
        # ================== TABELA ==================
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Código", "Descrição", "Receita", "Última Inspeção", "Inspeções", "Status"
        ])
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self._edit_selected)
        
        layout.addWidget(self.table, 1)
        
        # ================== BOTÕES ==================
        btn_layout = QHBoxLayout()
        
        self.btn_edit = QPushButton("✏️ Editar")
        self.btn_edit.clicked.connect(self._edit_selected)
        btn_layout.addWidget(self.btn_edit)
        
        self.btn_history = QPushButton("📊 Histórico")
        self.btn_history.clicked.connect(self._show_history)
        btn_layout.addWidget(self.btn_history)
        
        self.btn_delete = QPushButton("🗑️ Excluir")
        self.btn_delete.clicked.connect(self._delete_selected)
        self.btn_delete.setStyleSheet("color: #dc3545;")
        btn_layout.addWidget(self.btn_delete)
        
        btn_layout.addStretch()
        
        btn_close = QPushButton("Fechar")
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)
        
        layout.addLayout(btn_layout)
    
    def _load_stencils(self):
        """Carrega lista de stencils."""
        filter_map = {
            0: None,  # Todos
            1: "active",
            2: "warning",
            3: "retired",
        }
        status_filter = filter_map.get(self.cmb_filter.currentIndex())
        
        stencils = self.tracker.list_stencils(status=status_filter)
        
        self.table.setRowCount(len(stencils))
        
        status_display = {
            "active": ("🟢 Ativo", "#d4edda"),
            "warning": ("🟡 Alerta", "#fff3cd"),
            "retired": ("🔴 Retirado", "#f8d7da"),
        }
        
        for row, stencil in enumerate(stencils):
            self.table.setItem(row, 0, QTableWidgetItem(stencil.code))
            self.table.setItem(row, 1, QTableWidgetItem(stencil.description))
            self.table.setItem(row, 2, QTableWidgetItem(stencil.recipe_name or ""))
            
            # Última inspeção
            if stencil.last_inspection:
                try:
                    dt = datetime.fromisoformat(stencil.last_inspection)
                    dt_str = dt.strftime("%d/%m/%Y %H:%M")
                except:
                    dt_str = stencil.last_inspection
            else:
                dt_str = "-"
            self.table.setItem(row, 3, QTableWidgetItem(dt_str))
            
            self.table.setItem(row, 4, QTableWidgetItem(str(stencil.inspection_count)))
            
            # Status com cor
            status_text, status_color = status_display.get(
                stencil.status, ("?", "#f0f0f0")
            )
            status_item = QTableWidgetItem(status_text)
            status_item.setBackground(QColor(status_color))
            self.table.setItem(row, 5, status_item)
    
    def _get_selected_code(self) -> Optional[str]:
        """Retorna código do stencil selecionado."""
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        return item.text() if item else None
    
    def _create_new(self):
        """Abre diálogo para criar novo stencil."""
        dialog = StencilCreateDialog(self.tracker, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._load_stencils()
    
    def _edit_selected(self):
        """Edita stencil selecionado."""
        code = self._get_selected_code()
        if not code:
            QMessageBox.warning(self, "Seleção", "Selecione um stencil.")
            return
        
        stencil = self.tracker.get_stencil(code)
        if stencil:
            dialog = StencilEditDialog(self.tracker, stencil, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self._load_stencils()
    
    def _show_history(self):
        """Mostra histórico do stencil selecionado."""
        code = self._get_selected_code()
        if not code:
            QMessageBox.warning(self, "Seleção", "Selecione um stencil.")
            return
        
        dialog = StencilHistoryDialog(self.tracker, code, self)
        dialog.exec()
    
    def _delete_selected(self):
        """Exclui stencil selecionado."""
        code = self._get_selected_code()
        if not code:
            QMessageBox.warning(self, "Seleção", "Selecione um stencil.")
            return
        
        reply = QMessageBox.question(
            self, "Confirmar Exclusão",
            f"Tem certeza que deseja excluir o stencil '{code}'?\n\n"
            "⚠️ Esta ação é irreversível e removerá todo o histórico!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.tracker.delete_stencil(code):
                self._load_stencils()
            else:
                QMessageBox.critical(
                    self, "Erro",
                    "Não foi possível excluir o stencil."
                )
