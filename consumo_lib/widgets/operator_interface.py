"""
widgets/operator_interface.py
-------------------------------

Widgets de interface simplificada para operadores:
- StencilSelector: Dropdown para seleção de stencil
- ProgramSelector: Dropdown para seleção de programa
- InspectionResultsWidget: Display simples de resultados (OK/NOK)
"""

import logging
from typing import Optional, List, Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QGroupBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal

from consumo_lib.ui import COLORS, TYPO, SPACE

logger = logging.getLogger(__name__)


class StencilSelector(QWidget):
    """
    Widget para seleção de stencil.

    Permite operador selecionar um stencil de uma lista dropdown.
    """

    # Signals
    stencil_selected = pyqtSignal(str)  # stencil_code

    def __init__(self, stencils: Optional[List[Dict]] = None, parent=None):
        super().__init__(parent)

        self._stencils = stencils if stencils is not None else []
        self._selected_code: Optional[str] = None

        self._setup_ui()
        self._populate_stencils()

        logger.info(f"StencilSelector criado com {len(self._stencils)} stencils")

    def _setup_ui(self):
        """Configura interface do widget."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Label
        label = QLabel("Stencil:")
        label.setFont(TYPO.get_font(TYPO.BODY_MEDIUM))

        # Dropdown
        self._combo = QComboBox()
        self._combo.setFont(TYPO.get_font(TYPO.BODY_MEDIUM))
        self._combo.currentTextChanged.connect(self._on_selection_changed)

        # Layout
        layout.addWidget(label)
        layout.addWidget(self._combo)

        self.setLayout(layout)

    def _populate_stencils(self):
        """Popula dropdown com lista de stencils."""
        self._combo.clear()

        if not self._stencils:
            self._combo.addItem("Nenhum stencil disponível", None)
            return

        # Adiciona opção padrão
        self._combo.addItem("Selecione um stencil...", None)

        # Adiciona stencils
        for stencil in self._stencils:
            code = stencil.get("code", "")
            description = stencil.get("description", code)
            display_text = f"{code} - {description}" if description != code else code

            self._combo.addItem(display_text, code)

    def _on_selection_changed(self, text: str):
        """Handler quando seleção muda."""
        current_data = self._combo.currentData()

        if current_data:
            self._selected_code = current_data
            self.stencil_selected.emit(current_data)
            logger.debug(f"Stencil selecionado: {current_data}")

    def select_stencil(self, stencil_code: str) -> bool:
        """
        Seleciona um stencil pelo código.

        Args:
            stencil_code: Código do stencil

        Returns:
            True se encontrado e selecionado
        """
        for i in range(self._combo.count()):
            if self._combo.itemData(i) == stencil_code:
                self._combo.setCurrentIndex(i)
                return True

        logger.warning(f"Stencil não encontrado: {stencil_code}")
        return False

    def get_selected_stencil(self) -> Optional[Dict]:
        """
        Retorna o stencil selecionado.

        Returns:
            Dicionário do stencil ou None
        """
        if not self._selected_code:
            return None

        for stencil in self._stencils:
            if stencil.get("code") == self._selected_code:
                return stencil

        return None

    def get_available_stencils(self) -> List[Dict]:
        """Retorna lista de stencils disponíveis."""
        return self._stencils.copy()

    def is_empty(self) -> bool:
        """Verifica se lista está vazia."""
        return len(self._stencils) == 0

    def get_warning_message(self) -> str:
        """Retorna mensagem de aviso se lista vazia."""
        if self.is_empty():
            return "Nenhum stencil disponível. Configure stencils no sistema primeiro."
        return ""


class ProgramSelector(QWidget):
    """
    Widget para seleção de programa de inspeção.

    Permite operador selecionar um programa predefinido.
    """

    # Signals
    program_selected = pyqtSignal(str)  # program_id

    def __init__(self, programs: Optional[List[Dict]] = None, parent=None):
        super().__init__(parent)

        self._programs = programs if programs is not None else []
        self._selected_id: Optional[str] = None

        self._setup_ui()
        self._populate_programs()

        logger.info(f"ProgramSelector criado com {len(self._programs)} programas")

    def _setup_ui(self):
        """Configura interface do widget."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Label
        label = QLabel("Programa de Inspeção:")
        label.setFont(TYPO.get_font(TYPO.BODY_MEDIUM))

        # Dropdown
        self._combo = QComboBox()
        self._combo.setFont(TYPO.get_font(TYPO.BODY_MEDIUM))
        self._combo.currentTextChanged.connect(self._on_selection_changed)

        # Layout
        layout.addWidget(label)
        layout.addWidget(self._combo)

        self.setLayout(layout)

    def _populate_programs(self):
        """Popula dropdown com programas."""
        self._combo.clear()

        if not self._programs:
            self._combo.addItem("Nenhum programa disponível", None)
            return

        # Adiciona programas
        for program in self._programs:
            prog_id = program.get("id", program.get("program_id", ""))
            name = program.get("name", prog_id)
            description = program.get("description", "")

            # Texto com nome + descrição
            if description:
                display_text = f"{name} - {description}"
            else:
                display_text = name

            self._combo.addItem(display_text, prog_id)

    def _on_selection_changed(self, text: str):
        """Handler quando seleção muda."""
        current_data = self._combo.currentData()

        if current_data:
            self._selected_id = current_data
            self.program_selected.emit(current_data)
            logger.debug(f"Programa selecionado: {current_data}")

    def select_program(self, program_id: str) -> bool:
        """
        Seleciona um programa pelo ID.

        Args:
            program_id: ID do programa

        Returns:
            True se encontrado e selecionado
        """
        for i in range(self._combo.count()):
            if self._combo.itemData(i) == program_id:
                self._combo.setCurrentIndex(i)
                return True

        logger.warning(f"Programo não encontrado: {program_id}")
        return False

    def get_selected_program(self) -> Optional[Dict]:
        """
        Retorna o programa selecionado.

        Returns:
            Dicionário do programa ou None
        """
        if not self._selected_id:
            return None

        for program in self._programs:
            prog_id = program.get("id", program.get("program_id", ""))
            if prog_id == self._selected_id:
                return program

        return None

    def get_available_programs(self) -> List[Dict]:
        """Retorna lista de programas disponíveis."""
        return self._programs.copy()

    def get_program_info(self, program_id: str) -> Optional[Dict]:
        """
        Retorna informações de um programa.

        Args:
            program_id: ID do programa

        Returns:
            Dicionário com info do programa ou None
        """
        for program in self._programs:
            prog_id = program.get("id", program.get("program_id", ""))
            if prog_id == program_id:
                return program

        return None


class InspectionResultsWidget(QWidget):
    """
    Widget para exibir resultados de inspeção em formato simples.

    Mostra classificação OK/NOK de forma clara e visual para operadores.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self._current_result: Optional[Dict] = None

        self._setup_ui()

        logger.info("InspectionResultsWidget criado")

    def _setup_ui(self):
        """Configura interface do widget."""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        # GroupBox
        self._group = QGroupBox("Resultado da Inspeção")
        self._group.setFont(TYPO.get_font(TYPO.LABEL_LARGE, bold=True))

        group_layout = QVBoxLayout()

        # Label de classificação (OK/NOK)
        self._classification_label = QLabel("---")
        self._classification_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._classification_label.setFont(TYPO.get_font(TYPO.DISPLAY_LARGE, bold=True))
        self._classification_label.setAutoFillBackground(True)

        # Label de métricas
        self._metrics_label = QLabel("Aguardando inspeção...")
        self._metrics_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._metrics_label.setFont(TYPO.get_font(TYPO.BODY_MEDIUM))

        # Layout
        group_layout.addWidget(self._classification_label)
        group_layout.addWidget(self._metrics_label)

        self._group.setLayout(group_layout)
        layout.addWidget(self._group)

        self.setLayout(layout)

        # Estado inicial: cinza
        self._set_neutral_style()

    def _set_neutral_style(self):
        """Define estilo neutro (sem resultado)."""
        self._classification_label.setText("---")
        self._classification_label.setStyleSheet(
            f"background-color: {COLORS.SURFACE}; color: {COLORS.TEXT_HINT}; padding: {SPACE.LG}px; border-radius: {SPACE.SM}px;"
        )
        self._metrics_label.setText("Aguardando inspeção...")

    def _set_pass_style(self):
        """Define estilo para resultado APROVADO."""
        self._classification_label.setText("APROVADO")
        self._classification_label.setStyleSheet(
            f"background-color: {COLORS.SUCCESS}; color: {COLORS.TEXT_PRIMARY}; padding: {SPACE.LG}px; border-radius: {SPACE.SM}px;"
        )

    def _set_fail_style(self):
        """Define estilo para resultado REPROVADO."""
        self._classification_label.setText("REPROVADO")
        self._classification_label.setStyleSheet(
            f"background-color: {COLORS.ERROR}; color: {COLORS.TEXT_PRIMARY}; padding: {SPACE.LG}px; border-radius: {SPACE.SM}px;"
        )

    def display_results(self, result: Dict[str, Any]):
        """
        Exibe resultados da inspeção.

        Args:
            result: Dicionário com resultados
                - classification: "OK" | "NOK"
                - total_apertures: Número total de aberturas
                - ok: Número de aberturas OK
                - partial: Número de aberturas PARCIAIS
                - blocked: Número de aberturas BLOQUEADAS
                - overall_percentage: Porcentagem geral
        """
        self._current_result = result

        classification = result.get("classification", "UNKNOWN")

        # Atualiza classificação
        if classification == "OK":
            self._set_pass_style()
        elif classification == "NOK":
            self._set_fail_style()
        else:
            self._set_neutral_style()
            return

        # Atualiza métricas
        total = result.get("total_apertures", 0)
        ok = result.get("ok", 0)
        partial = result.get("partial", 0)
        blocked = result.get("blocked", 0)
        percentage = result.get("overall_percentage", 0.0)

        metrics_text = (
            f"Total: {total} | OK: {ok} | Parcial: {partial} | "
            f"Bloqueado: {blocked} | Aproveitamento: {percentage:.1f}%"
        )

        self._metrics_label.setText(metrics_text)

        logger.info(f"Resultados exibidos: {classification} ({percentage:.1f}%)")

    def get_classification(self) -> str:
        """Retorna classificação atual (OK/NOK/---)."""
        text = self._classification_label.text()

        if text == "APROVADO":
            return "OK"
        elif text == "REPROVADO":
            return "NOK"
        else:
            return "UNKNOWN"

    def is_passing(self) -> bool:
        """Verifica se resultado é APROVADO."""
        return self.get_classification() == "OK"

    def get_main_metrics(self) -> Dict[str, Any]:
        """Retorna métricas principais."""
        if not self._current_result:
            return {
                "total": 0,
                "ok": 0,
                "partial": 0,
                "blocked": 0,
                "overall_percentage": 0.0
            }

        return {
            "total": self._current_result.get("total_apertures", 0),
            "ok": self._current_result.get("ok", 0),
            "partial": self._current_result.get("partial", 0),
            "blocked": self._current_result.get("blocked", 0),
            "overall_percentage": self._current_result.get("overall_percentage", 0.0)
        }

    def get_blocked_count(self) -> int:
        """Retorna número de aberturas bloqueadas."""
        return self._current_result.get("blocked", 0) if self._current_result else 0

    def clear(self):
        """Limpa resultados (reseta para estado neutro)."""
        self._current_result = None
        self._set_neutral_style()

    def get_last_result(self) -> Optional[Dict[str, Any]]:
        """
        Retorna o último resultado de inspeção exibido.

        Returns:
            Dicionário com o último resultado ou None se nenhum resultado foi definido
        """
        return self._current_result
