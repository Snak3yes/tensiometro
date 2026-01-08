"""
Dialog de Progresso de Inspeção

Exibe progresso em tempo real da execução de inspeção,
com barra de progresso, logs detalhados e controle de cancelamento.
"""

import logging
from datetime import datetime
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QTextCursor

logger = logging.getLogger(__name__)


class InspectionProgressDialog(QDialog):
    """
    Dialog de progresso de inspeção

    Sinais:
        execution_cancelled: Emitido quando usuário cancela
        execution_completed: Emitido quando execução termina
    """

    execution_cancelled = pyqtSignal()
    execution_completed = pyqtSignal(dict)

    def __init__(self, stencil_code: str, mode: str, parent=None):
        """
        Inicializa dialog de progresso

        Args:
            stencil_code: Código do stencil
            mode: Modo de inspeção ("tension", "inspection", "both")
            parent: Widget pai
        """
        super().__init__(parent)
        self.stencil_code = stencil_code
        self.mode = mode
        self.is_running = False
        self.is_complete = False

        self.setup_ui()

    def setup_ui(self):
        """Configura interface do dialog"""
        self.setWindowTitle("Execução de Inspeção")
        self.setModal(True)
        self.setFixedSize(700, 600)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(20)

        # Título
        mode_title = self._get_mode_title()
        title_label = QLabel(f"Execução: {mode_title}")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #111827;")
        layout.addWidget(title_label)

        # Subtítulo
        subtitle_label = QLabel(f"Stencil: {self.stencil_code}")
        subtitle_font = subtitle_label.font()
        subtitle_font.setPointSize(12)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setStyleSheet("color: #6B7280;")
        layout.addWidget(subtitle_label)

        layout.addSpacing(10)

        # Barra de progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(25)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #E5E7EB;
                border-radius: 6px;
                text-align: center;
                font-size: 12px;
                font-weight: 600;
            }
            QProgressBar::chunk {
                background-color: #3B82F6;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.progress_bar)

        # Label de status
        self.status_label = QLabel("Preparando execução...")
        self.status_label.setStyleSheet("color: #374151; font-size: 13px; font-weight: 500;")
        layout.addWidget(self.status_label)

        layout.addSpacing(10)

        # Área de log
        log_group = QLabel("Log de Operações")
        log_group.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        log_group.setStyleSheet("color: #374151;")
        layout.addWidget(log_group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(250)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #F9FAFB;
                border: 1px solid #E5E7EB;
                border-radius: 6px;
                padding: 12px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
                color: #1F2937;
            }
        """)
        layout.addWidget(self.log_text)

        layout.addSpacing(10)

        # Botões
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        self.cancel_button = QPushButton("Cancelar Execução")
        self.cancel_button.setMinimumWidth(160)
        self.cancel_button.setMinimumHeight(40)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #EF4444;
                color: white;
                font-size: 13px;
                font-weight: 600;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #DC2626;
            }
            QPushButton:disabled {
                background-color: #E5E7EB;
                color: #9CA3AF;
            }
        """)
        self.cancel_button.clicked.connect(self.on_cancel_clicked)
        buttons_layout.addWidget(self.cancel_button)

        self.close_button = QPushButton("Fechar")
        self.close_button.setMinimumWidth(120)
        self.close_button.setMinimumHeight(40)
        self.close_button.hide()  # Inicialmente oculto
        self.close_button.setStyleSheet("""
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
        self.close_button.clicked.connect(self.accept)
        buttons_layout.addWidget(self.close_button)

        layout.addLayout(buttons_layout)

    def _get_mode_title(self) -> str:
        """Retorna título legível do modo"""
        titles = {
            "tension": "Medição de Tensão",
            "inspection": "Inspeção Visual",
            "both": "Inspeção Completa (Tensão + Visual)"
        }
        return titles.get(self.mode, "Inspeção")

    def start_execution(self, worker: QThread):
        """
        Inicia execução com worker thread

        Args:
            worker: QThread com lógica de execução
        """
        self.is_running = True
        self.worker = worker

        # Conecta sinais
        self.worker.progress_updated.connect(self.on_progress_updated)
        self.worker.step_changed.connect(self.on_step_changed)
        self.worker.log_message.connect(self.add_log)
        self.worker.execution_complete.connect(self.on_execution_complete)

        # Inicia worker
        self.worker.start()

        self.add_log("✓ Iniciando execução...")

    def on_progress_updated(self, current: int, total: int, message: str):
        """
        Handler: Progresso atualizado

        Args:
            current: Valor atual
            total: Valor total
            message: Mensagem de progresso
        """
        percentage = int((current / total) * 100) if total > 0 else 0
        self.progress_bar.setValue(percentage)
        self.status_label.setText(f"{message} ({current}/{total})")

    def on_step_changed(self, step_description: str):
        """
        Handler: Etapa mudou

        Args:
            step_description: Descrição da etapa atual
        """
        self.add_log(f"→ {step_description}")

    def add_log(self, message: str):
        """
        Adiciona mensagem ao log

        Args:
            message: Mensagem para adicionar
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_line = f"[{timestamp}] {message}"

        self.log_text.append(log_line)
        self.log_text.moveCursor(QTextCursor.End)

        logger.info(f"Progress: {message}")

    def on_execution_complete(self, success: bool, message: str):
        """
        Handler: Execução completada

        Args:
            success: True se sucesso, False se erro
            message: Mensagem de resultado
        """
        self.is_running = False
        self.is_complete = True

        # Desabilita botão cancelar
        self.cancel_button.setEnabled(False)
        self.cancel_button.hide()

        # Mostra botão fechar
        self.close_button.show()

        if success:
            self.progress_bar.setValue(100)
            self.status_label.setText("Execução concluída com sucesso!")
            self.add_log(f"✅ {message}")
        else:
            self.status_label.setText("Execução concluída com erros")
            self.add_log(f"✗ {message}")

    def on_cancel_clicked(self):
        """Handler: Botão Cancelar clicado"""
        if self.is_running and hasattr(self, 'worker'):
            self.add_log("⚠ Cancelando execução...")
            self.worker.cancel()

            # Aguarda thread terminar (até 3 segundos)
            if not self.worker.wait(3000):
                self.add_log("✗ Worker não respondeu, forçando término")
                self.worker.terminate()

            self.is_running = False
            self.execution_cancelled.emit()
            self.reject()

    def get_results(self) -> dict:
        """
        Retorna resultados da execução

        Returns:
            Dict com resultados (se disponível)
        """
        if hasattr(self, 'worker') and hasattr(self.worker, 'results'):
            return self.worker.results
        return {}
