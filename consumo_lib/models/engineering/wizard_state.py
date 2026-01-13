"""
EngineeringWizardState - Estado compartilhado entre as 7 abas do Engineering Wizard

Este módulo define o estado centralizado que é compartilhado entre todas as abas
do Engineering Wizard, permitindo comunicação de dados e validação cruzada.

Autor: Claude Code (Sonnet 4.5)
Data: 2026-01-13
"""

import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class EngineeringWizardState:
    """
    Estado compartilhado entre as 7 abas do Engineering Wizard.

    Gerencia todos os dados coletados nas abas e fornece métodos para
    validação cruzada e serialização para auto-save.

    Attributes:
        program_data: Dados da Aba 1 (nome, stencil, versão, etc.)
        gerber_data: Dados da Aba 2 (arquivo, dimensões, aperturas)
        fiducial_templates: Templates da Aba 3 (2 fiduciais)
        mosaic_config: Configuração da Aba 4 (grid, FOVs)
        alignment_transform: Transformação da Aba 5 (tx, ty, angle, scale)
        inspection_groups: Grupos da Aba 6 (configurações de janelas)
        program_config: Configuração completa da Aba 7 (todos os dados agregados)
        current_tab: Índice da aba atual (0-6)
        is_dirty: Flag indicando se há mudanças não salvas
        auto_save_path: Caminho do arquivo de auto-save
        created_at: Timestamp de criação do wizard
        updated_at: Timestamp da última modificação
    """

    # Aba 1: Dados do Programa
    program_data: Optional[Dict[str, Any]] = None

    # Aba 2: Arquivo Gerber
    gerber_file: Optional[str] = None
    gerber_data: Optional[Dict[str, Any]] = None

    # Aba 3: Fiduciais
    fiducial_templates: List[Dict[str, Any]] = field(default_factory=list)

    # Aba 4: Mosaico
    mosaic_image_path: Optional[str] = None
    mosaic_config: Optional[Dict[str, Any]] = None

    # Aba 5: Alinhamento
    alignment_transform: Optional[Dict[str, float]] = None

    # Aba 6: Janelas de Inspeção
    inspection_groups: List[Dict[str, Any]] = field(default_factory=list)

    # Aba 7: Configuração Completa
    program_config: Optional[Dict[str, Any]] = None

    # Metadados de controle
    current_tab: int = 0
    is_dirty: bool = False
    auto_save_path: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self):
        """Inicializa timestamp após criação."""
        logger.info("📦 EngineeringWizardState criado")

    def update_timestamp(self):
        """Atualiza timestamp de modificação."""
        self.updated_at = datetime.now().isoformat()
        self.is_dirty = True

    def is_valid(self, tab_index: int) -> bool:
        """
        Valida se a aba específica tem dados completos.

        Args:
            tab_index: Índice da aba (0-6)

        Returns:
            bool: True se a aba está válida, False caso contrário
        """
        logger.debug(f"🔍 Validando aba {tab_index}")

        if tab_index == 0:  # Aba 1: Dados do Programa
            if self.program_data is None:
                return False
            # Validar campos obrigatórios
            required_fields = ['program_name', 'stencil_code', 'version', 'created_by']
            return all(
                self.program_data.get(field) for field in required_fields
            )

        elif tab_index == 1:  # Aba 2: Carregar Gerber
            return self.gerber_data is not None and self.gerber_file is not None

        elif tab_index == 2:  # Aba 3: Definir Fiduciais
            return len(self.fiducial_templates) >= 2  # Pelo menos 2 fiduciais

        elif tab_index == 3:  # Aba 4: Capturar Mosaico
            return self.mosaic_config is not None

        elif tab_index == 4:  # Aba 5: Alinhamento
            return self.alignment_transform is not None

        elif tab_index == 5:  # Aba 6: Janelas de Inspeção
            return len(self.inspection_groups) > 0

        elif tab_index == 6:  # Aba 7: Confirmar e Salvar
            # Última aba só válida se todas as anteriores estiverem completas
            return all(self.is_valid(i) for i in range(6))

        return False

    def validate_dependencies(self, tab_index: int) -> Tuple[bool, str]:
        """
        Valida dependências de outras abas.

        Args:
            tab_index: Índice da aba a validar

        Returns:
            Tuple[bool, str]: (True, "") se válido, (False, mensagem) se inválido
        """
        logger.debug(f"🔍 Validando dependências da aba {tab_index}")

        if tab_index == 0:  # Aba 1: Sem dependências
            return True, ""

        elif tab_index == 1:  # Aba 2: Depende da Aba 1
            if self.program_data is None:
                return False, "Preencha os dados do programa primeiro (Aba 1)"
            return True, ""

        elif tab_index == 2:  # Aba 3: Depende da Aba 2
            if self.gerber_data is None:
                return False, "Carregue o arquivo Gerber primeiro (Aba 2)"
            return True, ""

        elif tab_index == 3:  # Aba 4: Depende da Aba 3
            if len(self.fiducial_templates) < 2:
                return False, "Capture pelo menos 2 fiduciais primeiro (Aba 3)"
            return True, ""

        elif tab_index == 4:  # Aba 5: Depende da Aba 4
            if self.mosaic_config is None:
                return False, "Capture o mosaico primeiro (Aba 4)"
            return True, ""

        elif tab_index == 5:  # Aba 6: Depende da Aba 5
            if self.alignment_transform is None:
                return False, "Execute o alinhamento primeiro (Aba 5)"
            return True, ""

        elif tab_index == 6:  # Aba 7: Depende de todas as anteriores
            missing = []
            if not self.is_valid(0):
                missing.append("Dados do Programa")
            if not self.is_valid(1):
                missing.append("Arquivo Gerber")
            if not self.is_valid(2):
                missing.append("Fiduciais")
            if not self.is_valid(3):
                missing.append("Mosaico")
            if not self.is_valid(4):
                missing.append("Alinhamento")
            if not self.is_valid(5):
                missing.append("Janelas de Inspeção")

            if missing:
                return False, f"Complete as abas anteriores: {', '.join(missing)}"
            return True, ""

        return True, ""

    def to_dict(self) -> Dict:
        """
        Serializa estado para JSON (auto-save).

        Returns:
            Dict com todos os dados do estado
        """
        data = asdict(self)
        logger.debug(f"💾 Estado serializado: {len(data)} campos")
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'EngineeringWizardState':
        """
        Desserializa estado do JSON.

        Args:
            data: Dicionário com dados do estado

        Returns:
            EngineeringWizardState: Estado restaurado
        """
        state = cls(**data)
        logger.info(f"📥 Estado restaurado de {data.get('created_at', 'unknown')}")
        return state

    def can_proceed_to_tab(self, target_tab: int) -> Tuple[bool, str]:
        """
        Verifica se é possível avançar para a aba alvo.

        Args:
            target_tab: Índice da aba de destino (0-6)

        Returns:
            Tuple[bool, str]: (True, "") se pode avançar, (False, motivo) se não
        """
        logger.debug(f"🔍 Verificando se pode avançar para aba {target_tab}")

        # Não pode pular abas
        if target_tab > self.current_tab + 1:
            return False, f"Complete a aba {self.current_tab + 1} primeiro"

        # Validar dependências
        valid, message = self.validate_dependencies(target_tab)
        if not valid:
            return False, message

        return True, ""

    def get_summary(self) -> Dict[str, Any]:
        """
        Retorna resumo do estado atual.

        Returns:
            Dict com resumo de cada aba
        """
        return {
            'aba_1': {
                'valid': self.is_valid(0),
                'data': self.program_data
            },
            'aba_2': {
                'valid': self.is_valid(1),
                'file': self.gerber_file,
                'data': self.gerber_data
            },
            'aba_3': {
                'valid': self.is_valid(2),
                'fiducials_count': len(self.fiducial_templates)
            },
            'aba_4': {
                'valid': self.is_valid(3),
                'has_mosaic': self.mosaic_config is not None
            },
            'aba_5': {
                'valid': self.is_valid(4),
                'has_alignment': self.alignment_transform is not None
            },
            'aba_6': {
                'valid': self.is_valid(5),
                'groups_count': len(self.inspection_groups)
            },
            'aba_7': {
                'valid': self.is_valid(6),
                'ready_to_save': self.program_config is not None
            },
            'current_tab': self.current_tab,
            'is_dirty': self.is_dirty,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    def clear(self):
        """Limpa todos os dados do estado (reset)."""
        logger.warning("🗑️ Limpando EngineeringWizardState")

        self.program_data = None
        self.gerber_file = None
        self.gerber_data = None
        self.fiducial_templates = []
        self.mosaic_image_path = None
        self.mosaic_config = None
        self.alignment_transform = None
        self.inspection_groups = []
        self.program_config = None
        self.current_tab = 0
        self.is_dirty = False
        self.auto_save_path = None
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
