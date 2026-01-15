"""
Alignment State Service - Gerenciamento de Estado de Alinhamento

Este serviço encapsula toda a lógica de gerenciamento de estado
para o processo de alinhamento de fiduciais.

Responsabilidade única:
- Criar e validar estados de alinhamento
- Gerenciar lista de fiduciais
- Serializar/desserializar estado
- Validar pré-condições para cálculo de transformação

Author: Claude Code (Sonnet 4.5)
Created: 2026-01-15
Phase: SOLID Refactoring Phase 5B
"""

import logging
from typing import List, Optional, Tuple, Dict, Any
import json

from .fiducial_models import (
    FiducialPoint,
    AlignmentState,
    FiducialConfig,
    FiducialType
)

logger = logging.getLogger(__name__)


class StateError(Exception):
    """Exceção para erros de gerenciamento de estado"""
    pass


class AlignmentStateService:
    """
    Serviço para gerenciamento de estado de alinhamento.

    Este serviço é responsável por:
    - Criar estados de alinhamento
    - Adicionar/remover/atualizar fiduciais
    - Validar estados (pré-condições para transformação)
    - Serializar/desserializar estados para JSON
    - Verificar consistência de dados

    NOTA: Este serviço NÃO depende de PyQt6 ou OpenCV, sendo 100% testável.
    """

    def __init__(self):
        """Inicializa o serviço de estado"""
        logger.debug("AlignmentStateService inicializado")

    def create_state(
        self,
        fiducials: Optional[List[FiducialPoint]] = None,
        config: Optional[FiducialConfig] = None
    ) -> AlignmentState:
        """
        Cria um novo estado de alinhamento.

        Args:
            fiducials: Lista inicial de fiduciais (opcional)
            config: Configuração (opcional, usa default se não fornecida)

        Returns:
            AlignmentState: Novo estado
        """
        state = AlignmentState(
            fiducials=fiducials or [],
            config=config or FiducialConfig()
        )
        logger.debug(f"Estado criado com {len(state.fiducials)} fiduciais")
        return state

    def add_fiducial(
        self,
        state: AlignmentState,
        gerber_x: float,
        gerber_y: float,
        fiducial_type: str = "gerber",
        **kwargs
    ) -> FiducialPoint:
        """
        Adiciona um novo fiducial ao estado.

        Args:
            state: Estado a modificar
            gerber_x: Coordenada X no Gerber
            gerber_y: Coordenada Y no Gerber
            fiducial_type: Tipo do fiducial ("gerber" ou "template")
            **kwargs: Parâmetros adicionais (window_size, search_radius, etc.)

        Returns:
            FiducialPoint: Fiducial criado
        """
        # Converter string para enum se necessário
        if isinstance(fiducial_type, str):
            fiducial_type = FiducialType(fiducial_type)

        fiducial = FiducialPoint(
            gerber_x=gerber_x,
            gerber_y=gerber_y,
            fiducial_type=fiducial_type,
            **kwargs
        )

        state.add_fiducial(fiducial)
        logger.info(
            f"Fiducial adicionado: ({gerber_x:.1f}, {gerber_y:.1f}) "
            f"- Total: {len(state.fiducials)}"
        )

        return fiducial

    def remove_fiducial(
        self,
        state: AlignmentState,
        index: int
    ) -> None:
        """
        Remove um fiducial do estado.

        Args:
            state: Estado a modificar
            index: Índice do fiducial a remover

        Raises:
            StateError: Se índice inválido
        """
        if index < 0 or index >= len(state.fiducials):
            raise StateError(
                f"Índice {index} inválido, deve estar entre 0 e {len(state.fiducials) - 1}"
            )

        removed = state.fiducials[index]
        state.remove_fiducial(index)
        logger.info(
            f"Fiducial removido: ({removed.gerber_x:.1f}, {removed.gerber_y:.1f}) "
            f"- Restam: {len(state.fiducials)}"
        )

    def update_fiducial(
        self,
        state: AlignmentState,
        index: int,
        **kwargs
    ) -> None:
        """
        Atualiza um fiducial existente.

        Args:
            state: Estado a modificar
            index: Índice do fiducial a atualizar
            **kwargs: Campos a atualizar (template_x, template_y, etc.)

        Raises:
            StateError: Se índice inválido
        """
        if index < 0 or index >= len(state.fiducials):
            raise StateError(
                f"Índice {index} inválido, deve estar entre 0 e {len(state.fiducials) - 1}"
            )

        fiducial = state.fiducials[index]

        # Atualizar campos fornecidos
        for key, value in kwargs.items():
            if hasattr(fiducial, key):
                setattr(fiducial, key, value)
                logger.debug(f"Fiducial {index}: {key} atualizado para {value}")
            else:
                logger.warning(f"Fiducial não tem campo '{key}'")

        state.update_fiducial(index, fiducial)
        logger.info(f"Fiducial {index} atualizado")

    def validate_state(self, state: AlignmentState) -> Tuple[bool, str]:
        """
        Valida se o estado está pronto para calcular transformação.

        Pré-condições:
        - Pelo menos min_fiducials fiduciais configurados
        - Todos os fiduciais têm template capturado
        - Pelo menos min_fiducials fiduciais com match

        Args:
            state: Estado a validar

        Returns:
            (is_valid, message): Tupla com validação e mensagem descritiva
        """
        # 1. Verificar número mínimo de fiduciais
        if len(state.fiducials) < state.config.min_fiducials:
            return False, (
                f"Pelo menos {state.config.min_fiducials} fiduciais são necessários, "
                f"got {len(state.fiducials)}"
            )

        # 2. Verificar se todos têm template
        without_template = [
            i for i, f in enumerate(state.fiducials)
            if not f.has_template()
        ]

        if without_template:
            return False, (
                f"Fiduciais sem template: {without_template}. "
                "Capture templates antes de calcular transformação."
            )

        # 3. Verificar fiduciais com match
        matched = state.get_matched_count()

        if matched < state.config.min_fiducials:
            return False, (
                f"Pelo menos {state.config.min_fiducials} fiduciais com match são necessários, "
                f"got {matched}/{len(state.fiducials)}"
            )

        # 4. Validar configuração
        config_valid, config_msg = state.config.validate()
        if not config_valid:
            return False, f"Configuração inválida: {config_msg}"

        # 5. Validar consistência (coordenadas não nulas)
        for i, f in enumerate(state.fiducials):
            if f.has_match() and (f.matched_x is None or f.matched_y is None):
                return False, f"Fiducial {i} tem marcador de match mas coordenadas são None"

        return True, "Estado válido para calcular transformação"

    def serialize_state(self, state: AlignmentState) -> str:
        """
        Serializa estado para JSON string.

        Args:
            state: Estado a serializar

        Returns:
            JSON string com o estado

        Raises:
            StateError: Se erro na serialização
        """
        try:
            data = state.to_dict()
            json_str = json.dumps(data, indent=2)
            logger.debug(f"Estado serializado: {len(json_str)} bytes")
            return json_str
        except Exception as e:
            raise StateError(f"Erro ao serializar estado: {e}")

    def deserialize_state(self, json_str: str) -> AlignmentState:
        """
        Desserializa estado de JSON string.

        Args:
            json_str: JSON string com o estado

        Returns:
            AlignmentState: Estado desserializado

        Raises:
            StateError: Se erro na desserialização
        """
        try:
            data = json.loads(json_str)
            state = AlignmentState.from_dict(data)
            logger.debug(f"Estado desserializado: {len(state.fiducials)} fiduciais")
            return state
        except json.JSONDecodeError as e:
            raise StateError(f"Erro ao fazer parse do JSON: {e}")
        except Exception as e:
            raise StateError(f"Erro ao desserializar estado: {e}")

    def save_state(self, state: AlignmentState, filepath: str) -> None:
        """
        Salva estado em arquivo JSON.

        Args:
            state: Estado a salvar
            filepath: Caminho do arquivo

        Raises:
            StateError: Se erro ao salvar
        """
        try:
            with open(filepath, 'w') as f:
                f.write(self.serialize_state(state))
            logger.info(f"Estado salvo em {filepath}")
        except IOError as e:
            raise StateError(f"Erro ao salvar arquivo {filepath}: {e}")

    def load_state(self, filepath: str) -> AlignmentState:
        """
        Carrega estado de arquivo JSON.

        Args:
            filepath: Caminho do arquivo

        Returns:
            AlignmentState: Estado carregado

        Raises:
            StateError: Se erro ao carregar
        """
        try:
            with open(filepath, 'r') as f:
                json_str = f.read()
            state = self.deserialize_state(json_str)
            logger.info(f"Estado carregado de {filepath}: {len(state.fiducials)} fiduciais")
            return state
        except IOError as e:
            raise StateError(f"Erro ao carregar arquivo {filepath}: {e}")

    def get_state_summary(self, state: AlignmentState) -> Dict[str, Any]:
        """
        Retorna resumo do estado.

        Args:
            state: Estado a resumir

        Returns:
            Dicionário com informações do estado
        """
        matched = state.get_matched_fiducials()
        correlations = [f.correlation for f in matched if f.correlation is not None]

        summary = {
            'total_fiducials': len(state.fiducials),
            'matched_fiducials': len(matched),
            'match_rate': len(matched) / len(state.fiducials) if state.fiducials else 0.0,
            'has_transform': state.transform is not None,
            'is_valid': state.is_valid
        }

        if correlations:
            summary.update({
                'min_correlation': min(correlations),
                'max_correlation': max(correlations),
                'mean_correlation': sum(correlations) / len(correlations)
            })

        if state.transform:
            summary['transform'] = {
                'tx': state.transform.tx,
                'ty': state.transform.ty,
                'angle': state.transform.angle,
                'scale_x': state.transform.scale_x,
                'scale_y': state.transform.scale_y
            }

        return summary

    def clone_state(self, state: AlignmentState) -> AlignmentState:
        """
        Cria uma cópia profunda do estado.

        Útil para experimentar com transformações sem modificar o original.

        Args:
            state: Estado a clonar

        Returns:
            AlignmentState: Cópia do estado
        """
        import copy

        cloned = AlignmentState(
            fiducials=copy.deepcopy(state.fiducials),
            transform=copy.deepcopy(state.transform) if state.transform else None,
            config=copy.deepcopy(state.config),
            is_valid=state.is_valid,
            validation_message=state.validation_message
        )

        logger.debug(f"Estado clonado: {len(cloned.fiducials)} fiduciais")
        return cloned
