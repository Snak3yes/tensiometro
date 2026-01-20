"""
ProgramDataWidget - Widget de Dados do Programa (Aba 1 do Engineering Wizard)

Este widget coleta informações básicas sobre o programa de inspeção:
- Nome do programa (obrigatório)
- Código do stencil (obrigatório, validado)
- Descrição (opcional)
- Versão (obrigatório, padrão v1.0)
- Criador (obrigatório, padrão do usuário logado)

Autor: Claude Code (Sonnet 4.5)
Data: 2026-01-13
"""

import logging
from datetime import datetime
from typing import Dict, Optional
from dataclasses import dataclass

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit, QLabel, QGroupBox
)
from PyQt6.QtCore import pyqtSignal, Qt, QRegularExpression
from PyQt6.QtGui import QRegularExpressionValidator

from consumo_lib.ui import COLORS, TYPO, SPACE, DIM

logger = logging.getLogger(__name__)


@dataclass
class ProgramData:
    """Dados do programa coletados na Aba 1."""
    program_name: str
    stencil_code: str
    description: str
    version: str
    created_by: str
    created_at: str

    def to_dict(self) -> Dict:
        """Converte para dicionário."""
        return {
            'program_name': self.program_name,
            'stencil_code': self.stencil_code,
            'description': self.description,
            'version': self.version,
            'created_by': self.created_by,
            'created_at': self.created_at
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ProgramData':
        """Cria a partir de dicionário."""
        return cls(
            program_name=data.get('program_name', ''),
            stencil_code=data.get('stencil_code', ''),
            description=data.get('description', ''),
            version=data.get('version', 'v1.0'),
            created_by=data.get('created_by', ''),
            created_at=data.get('created_at', datetime.now().isoformat())
        )


class ValidatedLineEdit(QLineEdit):
    """QLineEdit com indicador visual de validação."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_valid = False
        self._placeholder = ""

    def set_validation(self, is_valid: bool, message: str = ""):
        """Define estado de validação com indicador visual."""
        self._is_valid = is_valid

        # Indicador visual via stylesheet (com cor de texto explicita para legibilidade)
        if is_valid:
            self.setStyleSheet(f"""
                QLineEdit {{
                    border: 1px solid {COLORS.SUCCESS};
                    background-color: {COLORS.SURFACE};
                    color: {COLORS.TEXT_PRIMARY};
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QLineEdit {{
                    border: 1px solid {COLORS.ERROR};
                    background-color: {COLORS.SURFACE};
                    color: {COLORS.TEXT_PRIMARY};
                }}
            """)

        # Tooltip com mensagem
        if message:
            self.setToolTip(message)

    def is_valid(self) -> bool:
        """Retorna estado de validação."""
        return self._is_valid


class ProgramDataWidget(QWidget):
    """
    Widget para coletar dados básicos do programa de inspeção.

    Signals:
        data_changed(dict): Emitido quando qualquer campo é modificado
        validation_changed(bool): Emitido quando validação do widget muda
    """

    data_changed = pyqtSignal(dict)
    validation_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info("🎨 Inicializando ProgramDataWidget")

        # Estado interno
        self._is_valid = False

        # Setup UI
        self._setup_ui()

        # Conectar signals
        self._connect_signals()

        # Validar estado inicial
        self._validate_all()

        logger.info("✅ ProgramDataWidget inicializado")

    def _setup_ui(self):
        """Configura interface do usuário."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Título
        title = QLabel("📋 Dados do Programa")
        title.setStyleSheet(f"""
            QLabel {{
                {TYPO.HEADLINE_LARGE}
                font-weight: bold;
                color: {COLORS.PRIMARY};
                padding: {SPACE.SM}px;
            }}
        """)
        layout.addWidget(title)

        # Grupo principal
        group = QGroupBox("Informações do Programa")
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {COLORS.OUTLINE};
                border-radius: {DIM.RADIUS_SM}px;
                margin-top: {SPACE.SM}px;
                padding-top: {SPACE.SM}px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: {SPACE.SM}px;
                padding: 0 {SPACE.XXS}px;
            }}
        """)

        form_layout = QFormLayout(group)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        form_layout.setHorizontalSpacing(20)
        form_layout.setVerticalSpacing(12)

        # Campo 1: Nome do Programa (obrigatório)
        self.field_name = ValidatedLineEdit()
        self.field_name.setPlaceholderText("Ex: Inspeção STENCIL-ABC-123")
        self.field_name.setMaxLength(100)
        self.field_name.setToolTip(
            "Nome descritivo do programa de inspeção.\n"
            "Mínimo: 3 caracteres, Máximo: 100 caracteres"
        )
        form_layout.addRow("Nome do Programa*:", self.field_name)

        # Campo 2: Código Stencil (obrigatório, validado)
        self.field_stencil = ValidatedLineEdit()
        self.field_stencil.setPlaceholderText("Ex: STENCIL-ABC-123")
        self.field_stencil.setMaxLength(50)

        # Validador: maiúsculas, hífens, algarismos
        stencil_validator = QRegularExpressionValidator(
            QRegularExpression("[A-Z0-9\\-]+")
        )
        self.field_stencil.setValidator(stencil_validator)
        self.field_stencil.setToolTip(
            "Código do stencil associado ao programa.\n"
            "Formato: maiúsculas, números e hífens apenas.\n"
            "Exemplo: STENCIL-ABC-123"
        )
        form_layout.addRow("Código do Stencil*:", self.field_stencil)

        # Campo 3: Descrição (opcional)
        self.field_description = QTextEdit()
        self.field_description.setPlaceholderText(
            "Descreva o propósito deste programa...\n\n"
            "Exemplo: Programa de inspeção visual para verificar\n"
            "limpeza de aberturas após processo de impressão."
        )
        self.field_description.setMaximumHeight(100)
        self.field_description.setToolTip(
            "Descrição detalhada do programa (opcional).\n"
            "Máximo: 500 caracteres"
        )
        # Aplicar estilo consistente com os demais campos (fundo cinza escuro, texto branco)
        self.field_description.setStyleSheet(f"""
            QTextEdit {{
                border: 1px solid {COLORS.TEXT_DISABLED};
                background-color: {COLORS.SURFACE};
                color: {COLORS.TEXT_PRIMARY};
                padding: {SPACE.XXS}px;
                border-radius: {DIM.RADIUS_XS}px;
            }}
        """)
        form_layout.addRow("Descrição:", self.field_description)

        # Campo 4: Versão (obrigatório, padrão v1.0)
        self.field_version = ValidatedLineEdit()
        self.field_version.setText("v1.0")
        self.field_version.setPlaceholderText("Ex: v1.0, v2.1")
        self.field_version.setMaxLength(20)
        self.field_version.setToolTip(
            "Versão do programa no formato 'vX.Y'.\n"
            "Exemplo: v1.0, v1.1, v2.0"
        )
        form_layout.addRow("Versão*:", self.field_version)

        # Campo 5: Criador (obrigatório, padrão do usuário logado)
        self.field_creator = ValidatedLineEdit()
        self.field_creator.setPlaceholderText("Ex: engenheiro@empresa.com")
        self.field_creator.setMaxLength(100)

        # TODO: Obter usuário logado do sistema de autenticação
        # Por enquanto, usar um placeholder genérico
        self.field_creator.setText("engineer")
        self.field_creator.setToolTip(
            "Identificação do criador do programa.\n"
            "Exemplo: nome@empresa.com ou usuário do sistema"
        )
        form_layout.addRow("Criado por*:", self.field_creator)

        # Labels informativos
        info_label = QLabel(
            "<i>Campos marcados com * são obrigatórios</i>"
        )
        info_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; {TYPO.BODY_SMALL}")
        form_layout.addRow("", info_label)

        layout.addWidget(group)

        # Espaçador para empurrar conteúdo para cima
        layout.addStretch()

        # Status label (feedback visual)
        self.status_label = QLabel("⚠️ Preencha os campos obrigatórios")
        self.status_label.setStyleSheet(f"""
            QLabel {{
                padding: {SPACE.SM}px;
                background-color: {COLORS.WARNING_LIGHT};
                border: 1px solid {COLORS.WARNING};
                border-radius: {DIM.RADIUS_SM}px;
                color: {COLORS.WARNING_DARK};
            }}
        """)
        layout.addWidget(self.status_label)

    def _connect_signals(self):
        """Conecta signals dos campos."""
        self.field_name.textChanged.connect(self._on_field_changed)
        self.field_stencil.textChanged.connect(self._on_field_changed)
        self.field_description.textChanged.connect(self._on_field_changed)
        self.field_version.textChanged.connect(self._on_field_changed)
        self.field_creator.textChanged.connect(self._on_field_changed)

    def _on_field_changed(self):
        """Handler chamado quando qualquer campo é modificado."""
        logger.debug("📝 Campo modificado, validando...")

        # Validar todos os campos
        self._validate_all()

        # Emitir signal com dados atuais
        data = self.get_data()
        self.data_changed.emit(data)

    def _validate_all(self):
        """Valida todos os campos e atualiza estado."""
        # Validar campo nome
        name = self.field_name.text().strip()
        name_valid = len(name) >= 3
        if name:
            self.field_name.set_validation(
                name_valid,
                "✓ Válido" if name_valid else "✗ Mínimo 3 caracteres"
            )
        else:
            self.field_name.set_validation(False, "")

        # Validar campo stencil
        stencil = self.field_stencil.text().strip()
        stencil_valid = len(stencil) >= 3
        if stencil:
            self.field_stencil.set_validation(
                stencil_valid,
                "✓ Válido" if stencil_valid else "✗ Mínimo 3 caracteres"
            )
        else:
            self.field_stencil.set_validation(False, "")

        # Validar campo versão
        version = self.field_version.text().strip()
        version_valid = version.startswith("v") and len(version) >= 3
        if version:
            self.field_version.set_validation(
                version_valid,
                "✓ Válido" if version_valid else "✗ Formato: v1.0"
            )
        else:
            self.field_version.set_validation(False, "")

        # Validar campo criador
        creator = self.field_creator.text().strip()
        creator_valid = len(creator) > 0
        if creator:
            self.field_creator.set_validation(
                creator_valid,
                "✓ Válido" if creator_valid else "✗ Obrigatório"
            )
        else:
            self.field_creator.set_validation(False, "")

        # Validar widget completo
        is_valid = all([
            name_valid,
            stencil_valid,
            version_valid,
            creator_valid
        ])

        # Atualizar estado interno
        was_valid = self._is_valid
        self._is_valid = is_valid

        # Atualizar status label
        if is_valid:
            self.status_label.setText(
                "✅ Todos os campos estão válidos - "
                f"Criado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            )
            self.status_label.setStyleSheet(f"""
                QLabel {{
                    padding: {SPACE.SM}px;
                    background-color: {COLORS.SUCCESS_LIGHT};
                    border: 1px solid {COLORS.SUCCESS};
                    border-radius: {DIM.RADIUS_SM}px;
                    color: {COLORS.SUCCESS_DARK};
                }}
            """)
        else:
            missing = []
            if not name_valid:
                missing.append("nome")
            if not stencil_valid:
                missing.append("código stencil")
            if not version_valid:
                missing.append("versão")
            if not creator_valid:
                missing.append("criador")

            self.status_label.setText(
                f"⚠️ Preencha os campos obrigatórios: {', '.join(missing)}"
            )
            self.status_label.setStyleSheet(f"""
                QLabel {{
                    padding: {SPACE.SM}px;
                    background-color: {COLORS.WARNING_LIGHT};
                    border: 1px solid {COLORS.WARNING};
                    border-radius: {DIM.RADIUS_SM}px;
                    color: {COLORS.WARNING_DARK};
                }}
            """)

        # Emitir signal se validação mudou
        if was_valid != is_valid:
            logger.info(f"✅ Validação mudou: {was_valid} → {is_valid}")
            self.validation_changed.emit(is_valid)

    def get_data(self) -> Dict:
        """
        Retorna todos os dados coletados como dicionário.

        Returns:
            Dict com campos:
                - program_name: str
                - stencil_code: str
                - description: str
                - version: str
                - created_by: str
                - created_at: str (timestamp ISO 8601)
        """
        data = {
            'program_name': self.field_name.text().strip(),
            'stencil_code': self.field_stencil.text().strip(),
            'description': self.field_description.toPlainText().strip(),
            'version': self.field_version.text().strip(),
            'created_by': self.field_creator.text().strip(),
            'created_at': datetime.now().isoformat()
        }

        logger.debug(f"📊 Dados coletados: {data}")
        return data

    def set_data(self, data: Dict):
        """
        Define os campos a partir de um dicionário.

        Args:
            data: Dict com campos do programa
        """
        logger.info(f"📥 Carregando dados: {data}")

        self.field_name.setText(data.get('program_name', ''))
        self.field_stencil.setText(data.get('stencil_code', ''))
        self.field_description.setPlainText(data.get('description', ''))
        self.field_version.setText(data.get('version', 'v1.0'))
        self.field_creator.setText(data.get('created_by', 'engineer'))

        # Revalidar
        self._validate_all()

    def is_valid(self) -> bool:
        """
        Verifica se todos os campos obrigatórios estão válidos.

        Returns:
            bool: True se válido, False caso contrário
        """
        return self._is_valid

    def clear(self):
        """Limpa todos os campos."""
        logger.info("🗑️ Limpando campos")

        self.field_name.clear()
        self.field_stencil.clear()
        self.field_description.clear()
        self.field_version.setText("v1.0")
        self.field_creator.setText("engineer")

        # Revalidar
        self._validate_all()
