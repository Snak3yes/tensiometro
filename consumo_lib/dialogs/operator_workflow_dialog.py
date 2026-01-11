"""
Dialog de Workflow Simplificado para Operadores

Interface one-click para execução de inspeções:
- Seleção de stencil (dropdown)
- Seleção de programa (dropdown)
- Botão "Iniciar Inspeção"
- Display de resultado (OK/NOK)
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from consumo_lib.widgets import (
    StencilSelector, ProgramSelector, InspectionResultsWidget
)
from consumo_lib.coordinators import OperatorInspectionCoordinator

logger = logging.getLogger(__name__)


class OperatorWorkflowDialog(QDialog):
    """
    Dialog simplificado para operadores executarem inspeções.

    Fluxo one-click:
    1. Operador seleciona stencil
    2. Operador seleciona programa
    3. Operador clica "Iniciar Inspeção"
    4. Resultado é exibido (OK/NOK)
    """

    # Signals
    inspection_completed = pyqtSignal(dict)  # Resultados da inspeção

    def __init__(
        self,
        coordinator: OperatorInspectionCoordinator,
        stencils: Optional[List[Dict]] = None,
        operator_id: Optional[str] = None,
        parent=None
    ):
        """
        Inicializa dialog de workflow.

        Args:
            coordinator: OperatorInspectionCoordinator
            stencils: Lista de stencils disponíveis
            operator_id: ID do operador (para logging)
            parent: Widget pai
        """
        super().__init__(parent)

        self.coordinator = coordinator
        self.stencils = stencils if stencils is not None else []
        self.operator_id = operator_id or "OPERADOR"
        self._is_inspecting = False

        self._setup_ui()
        self._connect_signals()

        # Inicia sessão do operador
        session_id = self.coordinator.start_session(self.operator_id)
        logger.info(f"Sessão iniciada: {session_id}")

    def _setup_ui(self):
        """Configura interface do dialog."""
        self.setWindowTitle("Inspeção de Stencil - Operador")
        self.setModal(True)
        self.setFixedSize(600, 700)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Header
        self._setup_header(layout)

        # Seção de seleção
        self._setup_selection_section(layout)

        # Botão de ação
        self._setup_action_button(layout)

        # Seção de resultado
        self._setup_result_section(layout)

        # Footer
        self._setup_footer(layout)

    def _setup_header(self, layout: QVBoxLayout):
        """Configura header do dialog."""
        title = QLabel("Workflow de Inspeção")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #111827;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel(f"Operador: {self.operator_id}")
        subtitle_font = QFont()
        subtitle_font.setPointSize(11)
        subtitle.setFont(subtitle_font)
        subtitle.setStyleSheet("color: #6B7280;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        layout.addSpacing(10)

    def _setup_selection_section(self, layout: QVBoxLayout):
        """Configura seção de seleção (stencil + programa)."""
        selection_group = QGroupBox("1. Selecione os Parâmetros")
        selection_group.setStyleSheet("""
            QGroupBox {
                font-size: 13px;
                font-weight: 600;
                color: #374151;
                border: 2px solid #E5E7EB;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
            }
        """)
        selection_layout = QVBoxLayout()
        selection_layout.setSpacing(15)

        # Stencil Selector
        self.stencil_selector = StencilSelector(stencils=self.stencils)
        selection_layout.addWidget(self.stencil_selector)

        # Program Selector
        available_programs = self.coordinator.get_available_programs()
        program_list = [
            {
                "program_id": prog.program_id,
                "name": prog.name,
                "description": prog.description
            }
            for prog in available_programs
        ]
        self.program_selector = ProgramSelector(programs=program_list)
        selection_layout.addWidget(self.program_selector)

        selection_group.setLayout(selection_layout)
        layout.addWidget(selection_group)

    def _setup_action_button(self, layout: QVBoxLayout):
        """Configura botão de ação."""
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.start_button = QPushButton("▶ Iniciar Inspeção")
        self.start_button.setMinimumHeight(50)
        self.start_button.setMinimumWidth(200)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                font-size: 14px;
                font-weight: 700;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
            QPushButton:disabled {
                background-color: #D1D5DB;
                color: #9CA3AF;
            }
        """)
        self.start_button.clicked.connect(self._on_start_inspection)
        button_layout.addWidget(self.start_button)
        button_layout.addStretch()

        layout.addLayout(button_layout)

    def _setup_result_section(self, layout: QVBoxLayout):
        """Configura seção de resultado."""
        result_group = QGroupBox("2. Resultado da Inspeção")
        result_group.setStyleSheet("""
            QGroupBox {
                font-size: 13px;
                font-weight: 600;
                color: #374151;
                border: 2px solid #E5E7EB;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
            }
        """)
        result_layout = QVBoxLayout()

        self.results_widget = InspectionResultsWidget()
        result_layout.addWidget(self.results_widget)

        result_group.setLayout(result_layout)
        layout.addWidget(result_group)

    def _setup_footer(self, layout: QVBoxLayout):
        """Configura footer do dialog."""
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()

        close_button = QPushButton("Fechar")
        close_button.setMinimumWidth(120)
        close_button.setMinimumHeight(40)
        close_button.setStyleSheet("""
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
        close_button.clicked.connect(self.accept)
        footer_layout.addWidget(close_button)

        layout.addLayout(footer_layout)

    def _connect_signals(self):
        """Conecta sinais dos widgets."""
        self.stencil_selector.stencil_selected.connect(self._on_stencil_selected)
        self.program_selector.program_selected.connect(self._on_program_selected)

        # Conecta sinais do coordinator
        self.coordinator.inspection_completed.connect(self._on_inspection_completed)
        self.coordinator.inspection_failed.connect(self._on_inspection_failed)

    def _on_stencil_selected(self, stencil_code: str):
        """
        Handler: Stencil selecionado.

        Args:
            stencil_code: Código do stencil selecionado
        """
        logger.info(f"Stencil selecionado: {stencil_code}")
        self.coordinator.select_stencil(stencil_code)

    def _on_program_selected(self, program_id: str):
        """
        Handler: Programa selecionado.

        Args:
            program_id: ID do programa selecionado
        """
        logger.info(f"Programa selecionado: {program_id}")
        self.coordinator.select_program(program_id)

    def _on_start_inspection(self):
        """Handler: Botão Iniciar Inspeção clicado."""
        if self._is_inspecting:
            logger.warning("Inspeção já em andamento")
            return

        # Valida seleções
        if not self.coordinator._selected_stencil_code:
            QMessageBox.warning(
                self,
                "Seleção Incompleta",
                "Por favor, selecione um stencil antes de iniciar a inspeção."
            )
            return

        if not self.coordinator._selected_program:
            QMessageBox.warning(
                self,
                "Seleção Incompleta",
                "Por favor, selecione um programa antes de iniciar a inspeção."
            )
            return

        # Inicia inspeção
        self._is_inspecting = True
        self.start_button.setEnabled(False)
        self.start_button.setText("Executando...")

        logger.info("Iniciando inspeção one-click...")

        # Executa inspeção (síncrono por enquanto)
        result = self.coordinator.start_inspection()

        if result.get("status") == "completed":
            self._on_inspection_completed(result)
        else:
            self._on_inspection_failed(result.get("message", "Erro desconhecido"))

    def _on_inspection_completed(self, result: Dict[str, Any]):
        """
        Handler: Inspeção completada com sucesso.

        Args:
            result: Resultado da inspeção
        """
        self._is_inspecting = False
        self.start_button.setEnabled(True)
        self.start_button.setText("▶ Iniciar Inspeção")

        # Exibe resultado
        self.results_widget.display_results(result)

        # Log da conclusão
        classification = result.get("classification", "UNKNOWN")
        logger.info(f"Inspeção completada: {classification}")

        # Emite sinal
        self.inspection_completed.emit(result)

        # Feedback visual
        if classification == "OK":
            QMessageBox.information(
                self,
                "Inspeção Concluída",
                f"Stencil APROVADO!\n\nClassificação: {classification}\n\nResultado: Todos os critérios atendidos."
            )
        elif classification == "NOK":
            QMessageBox.warning(
                self,
                "Inspeção Concluída",
                f"Stencil REPROVADO!\n\nClassificação: {classification}\n\nResultado: Critérios NÃO atendidos."
            )
        else:
            QMessageBox.information(
                self,
                "Inspeção Concluída",
                f"Inspeção finalizada.\n\nClassificação: {classification}"
            )

    def _on_inspection_failed(self, error_message: str):
        """
        Handler: Inspeção falhou.

        Args:
            error_message: Mensagem de erro
        """
        self._is_inspecting = False
        self.start_button.setEnabled(True)
        self.start_button.setText("▶ Iniciar Inspeção")

        logger.error(f"Inspeção falhou: {error_message}")

        # Exibe erro no widget de resultados
        error_result = {
            "status": "error",
            "classification": "ERROR",
            "message": error_message,
            "timestamp": datetime.now().isoformat()
        }
        self.results_widget.display_results(error_result)

        # Mensagem ao usuário
        QMessageBox.critical(
            self,
            "Erro na Inspeção",
            f"A inspeção não pôde ser completada:\n\n{error_message}"
        )

    def get_last_result(self) -> Optional[Dict[str, Any]]:
        """
        Retorna último resultado de inspeção.

        Returns:
            Dict com resultado ou None se nenhum resultado
        """
        return self.results_widget.get_last_result()
