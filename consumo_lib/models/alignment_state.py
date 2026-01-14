"""
Alignment State Model - Estado do Alinhamento Fiducial

Este módulo contém modelos de dados para representar o estado do alinhamento
fiducial entre Gerber e mosaico capturado.

Components:
    - AlignmentState: Estado completo do alinhamento
    - FiducialMatch: Resultado de matching de um fiducial
    - AlignmentMetrics: Métricas de qualidade do alinhamento

Author: Claude Sonnet 4.5
Date: 2026-01-14
Track: solid_refactoring_phase2_20260114 (Phase 3 - Alignment Widget Refactoring)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Optional, List

logger = logging.getLogger(__name__)


@dataclass
class FiducialMatch:
    """
    Resultado do matching de um fiducial.

    Atributos:
        template_id: Identificador do template fiducial
        found: Se fiducial foi encontrado
        x: Posição X em pixels (na imagem do mosaico)
        y: Posição Y em pixels (na imagem do mosaico)
        score: Score de matching (0-100, sendo 100 perfeito)
        expected_x: Posição X esperada (do Gerber)
        expected_y: Posição Y esperada (do Gerber)
        error_x: Erro em X (found_x - expected_x)
        error_y: Erro em Y (found_y - expected_y)
    """

    template_id: int
    found: bool
    x: float = 0.0
    y: float = 0.0
    score: float = 0.0
    expected_x: float = 0.0
    expected_y: float = 0.0
    error_x: float = 0.0
    error_y: float = 0.0

    def __post_init__(self):
        """Calcula erros após inicialização."""
        if self.found:
            self.error_x = self.x - self.expected_x
            self.error_y = self.y - self.expected_y

    @property
    def error_magnitude(self) -> float:
        """Retorna magnitude do erro (distância euclidiana)."""
        return (self.error_x**2 + self.error_y**2)**0.5

    def to_dict(self) -> dict[str, Any]:
        """Converte para dicionário (serialização)."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FiducialMatch:
        """Cria FiducialMatch a partir de dicionário."""
        return cls(**data)


@dataclass
class AlignmentMetrics:
    """
    Métricas de qualidade do alinhamento.

    Atributos:
        overall_score: Score geral (0-100)
        mean_error: Erro médio em pixels
        max_error: Erro máximo em pixels
        std_error: Desvio padrão do erro em pixels
        fiducials_found: Número de fiduciais encontrados
        fiducials_total: Número total de fiduciais
        is_acceptable: Se alinhamento é aceitável (score >= threshold)
    """

    overall_score: float = 0.0
    mean_error: float = 0.0
    max_error: float = 0.0
    std_error: float = 0.0
    fiducials_found: int = 0
    fiducials_total: int = 0
    is_acceptable: bool = False

    @property
    def success_rate(self) -> float:
        """Taxa de sucesso (fiduciais encontrados / total)."""
        if self.fiducials_total == 0:
            return 0.0
        return self.fiducials_found / self.fiducials_total

    def to_dict(self) -> dict[str, Any]:
        """Converte para dicionário (serialização)."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AlignmentMetrics:
        """Cria AlignmentMetrics a partir de dicionário."""
        return cls(**data)

    @classmethod
    def from_matches(
        cls,
        matches: List[FiducialMatch],
        min_score_threshold: float = 70.0
    ) -> AlignmentMetrics:
        """
        Calcula métricas a partir de lista de matches.

        Args:
            matches: Lista de resultados de matching
            min_score_threshold: Score mínimo para considerar aceitável

        Returns:
            AlignmentMetrics calculado
        """
        if not matches:
            return cls()

        # Filtra apenas fiduciais encontrados
        found_matches = [m for m in matches if m.found]

        # Conta fiduciais
        fiducials_found = len(found_matches)
        fiducials_total = len(matches)

        # Calcula erros
        errors = [(m.error_x**2 + m.error_y**2)**0.5 for m in found_matches]

        if errors:
            mean_error = sum(errors) / len(errors)
            max_error = max(errors)
            variance = sum((e - mean_error)**2 for e in errors) / len(errors)
            std_error = variance**0.5
        else:
            mean_error = 0.0
            max_error = 0.0
            std_error = 0.0

        # Calcula score geral
        if found_matches:
            avg_score = sum(m.score for m in found_matches) / len(found_matches)
            success_penalty = (fiducials_total - fiducials_found) * 10
            overall_score = max(0, avg_score - success_penalty)
        else:
            overall_score = 0.0

        # Determina se é aceitável
        # Critério: pelo menos 1 fiducial encontrado (se total >= 2)
        # ou todos encontrados (se total < 2)
        if fiducials_total == 0:
            min_required = 0
        elif fiducials_total == 1:
            min_required = 1
        elif fiducials_total == 2:
            min_required = 1  # Permite 50% para 2 fiduciais
        else:
            min_required = 2  # Para 3+, exige pelo menos 2

        is_acceptable = (
            overall_score >= min_score_threshold and
            fiducials_found >= min_required
        )

        return cls(
            overall_score=overall_score,
            mean_error=mean_error,
            max_error=max_error,
            std_error=std_error,
            fiducials_found=fiducials_found,
            fiducials_total=fiducials_total,
            is_acceptable=is_acceptable
        )


@dataclass
class AlignmentState:
    """
    Estado completo do alinhamento fiducial.

    Este modelo armazena todo o estado necessário para o alinhamento,
    incluindo transformação, visualização e resultados.

    Atributos:
        # Transformação
        tx: Translação em X (pixels)
        ty: Translação em Y (pixels)
        angle: Rotação em graus
        scale: Fator de escala

        # Visualização
        opacity: Opacidade do overlay (0-1)
        zoom: Nível de zoom (1.0 = 100%)

        # Resultados
        score: Score de alinhamento (0-100)
        fiducials_found: Se fiduciais foram encontrados
        fiducial_matches: Lista de matches de fiduciais

        # Métricas detalhadas
        metrics: Métricas calculadas do alinhamento

        # Metadados
        is_valid: Se estado é válido (para avançar no wizard)
        timestamp: Timestamp da última modificação
    """

    # Transformação
    tx: float = 0.0
    ty: float = 0.0
    angle: float = 0.0
    scale: float = 1.0

    # Visualização
    opacity: float = 0.5
    zoom: float = 1.0

    # Resultados
    score: float = 0.0
    fiducials_found: bool = False
    fiducial_matches: List[FiducialMatch] = field(default_factory=list)
    metrics: Optional[AlignmentMetrics] = None

    # Metadados
    is_valid: bool = False
    timestamp: Optional[str] = None

    def __post_init__(self):
        """Inicializa timestamp se não fornecido."""
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

        # Calcula métricas se não fornecidas
        if self.metrics is None and self.fiducial_matches:
            self.metrics = AlignmentMetrics.from_matches(self.fiducial_matches)
            self.score = self.metrics.overall_score
            self.fiducials_found = self.metrics.fiducials_found > 0

    def reset_transform(self) -> None:
        """Reseta transformação para valores padrão."""
        self.tx = 0.0
        self.ty = 0.0
        self.angle = 0.0
        self.scale = 1.0
        self.timestamp = datetime.now().isoformat()

    def update_from_transform(
        self,
        tx: Optional[float] = None,
        ty: Optional[float] = None,
        angle: Optional[float] = None,
        scale: Optional[float] = None
    ) -> None:
        """
        Atualiza transformação parcialmente.

        Args:
            tx: Nova translação X (ou None para manter atual)
            ty: Nova translação Y (ou None para manter atual)
            angle: Nova rotação (ou None para manter atual)
            scale: Nova escala (ou None para manter atual)
        """
        if tx is not None:
            self.tx = tx
        if ty is not None:
            self.ty = ty
        if angle is not None:
            self.angle = angle
        if scale is not None:
            self.scale = scale

        self.timestamp = datetime.now().isoformat()

    def update_matches(self, matches: List[FiducialMatch]) -> None:
        """
        Atualiza matches e recalcula métricas.

        Args:
            matches: Nova lista de matches
        """
        self.fiducial_matches = matches
        self.metrics = AlignmentMetrics.from_matches(matches)
        self.score = self.metrics.overall_score
        self.fiducials_found = self.metrics.fiducials_found > 0
        self.is_valid = self.metrics.is_acceptable
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict[str, Any]:
        """
        Converte estado para dicionário (serialização).

        Returns:
            Dicionário com todos os campos (incluindo aninhados)
        """
        data = asdict(self)
        # Converte lista de FiducialMatch
        if self.fiducial_matches:
            data['fiducial_matches'] = [m.to_dict() for m in self.fiducial_matches]
        # Converte metrics
        if self.metrics:
            data['metrics'] = self.metrics.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AlignmentState:
        """
        Cria AlignmentState a partir de dicionário (deserialização).

        Args:
            data: Dicionário com dados do estado

        Returns:
            Instância de AlignmentState
        """
        # Deserializa lista de matches
        if 'fiducial_matches' in data and data['fiducial_matches']:
            data['fiducial_matches'] = [
                FiducialMatch.from_dict(m) if isinstance(m, dict) else m
                for m in data['fiducial_matches']
            ]

        # Deserializa metrics
        if 'metrics' in data and data['metrics']:
            data['metrics'] = (
                AlignmentMetrics.from_dict(data['metrics'])
                if isinstance(data['metrics'], dict)
                else data['metrics']
            )

        return cls(**data)

    def to_aoi_lib_format(self) -> dict[str, float]:
        """
        Converte para formato compatível com aoi_lib.fiducial_alignment.AlignmentTransform.

        Returns:
            Dicionário com campos tx, ty, angle, scale
        """
        return {
            'tx': self.tx,
            'ty': self.ty,
            'angle': self.angle,
            'scale': self.scale
        }

    @classmethod
    def from_aoi_lib_format(
        cls,
        transform: dict[str, float],
        opacity: float = 0.5,
        zoom: float = 1.0
    ) -> AlignmentState:
        """
        Cria AlignmentState a partir de formato aoi_lib.

        Args:
            transform: Dicionário com tx, ty, angle, scale
            opacity: Opacidade do overlay
            zoom: Nível de zoom

        Returns:
            Instância de AlignmentState
        """
        return cls(
            tx=transform.get('tx', 0.0),
            ty=transform.get('ty', 0.0),
            angle=transform.get('angle', 0.0),
            scale=transform.get('scale', 1.0),
            opacity=opacity,
            zoom=zoom
        )

    def copy(self) -> AlignmentState:
        """
        Cria uma cópia profunda do estado.

        Returns:
            Nova instância com mesmos valores
        """
        return AlignmentState.from_dict(self.to_dict())

    @property
    def has_transformation(self) -> bool:
        """Retorna True se há alguma transformação aplicada."""
        return (
            self.tx != 0.0 or
            self.ty != 0.0 or
            self.angle != 0.0 or
            self.scale != 1.0
        )

    @property
    def transform_summary(self) -> str:
        """Retorna resumo legível da transformação."""
        if not self.has_transformation:
            return "Sem transformação"

        parts = []
        if self.tx != 0.0 or self.ty != 0.0:
            parts.append(f"Translação: ({self.tx:.1f}, {self.ty:.1f}) px")
        if self.angle != 0.0:
            parts.append(f"Rotação: {self.angle:.2f}°")
        if self.scale != 1.0:
            parts.append(f"Escala: {self.scale:.4f}x")

        return " | ".join(parts) if parts else "Sem transformação"
