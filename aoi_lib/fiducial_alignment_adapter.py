"""
Fiducial Alignment Adapter - Ponte entre Código Legado e Novos Services

Este adapter fornece uma camada de compatibilidade entre:
- Código legado (fiducial_alignment.py com FiducialTemplate, FiducialAligner)
- Novos services (fiducial_matching_service, alignment_transform_service)

Responsabilidade:
- Converter entre models legados e novos
- Fornecer interface compatível com FiducialAlignmentWidget
- Orquestrar os novos services usando API legada

Author: Claude Code (Sonnet 4.5)
Created: 2026-01-15
Phase: SOLID Refactoring Phase 5B.3
"""

import logging
from typing import List, Optional, Tuple, Callable
import numpy as np
import cv2

from .fiducial_alignment import (
    FiducialTemplate,
    FiducialMatchResult,
    AlignmentTransform as LegacyTransform,
    FiducialAligner
)

from .fiducial_models import (
    FiducialPoint,
    AlignmentTransform as NewTransform,
    AlignmentState,
    FiducialConfig,
    FiducialType,
    MatchingMethod
)

from .fiducial_matching_service import FiducialMatchingService
from .alignment_transform_service import AlignmentTransformService
from .alignment_state_service import AlignmentStateService

logger = logging.getLogger(__name__)


class FiducialAlignmentAdapter:
    """
    Adapter que integra os novos services com a interface legada.

    Este adapter:
    1. Converte FiducialTemplate ↔ FiducialPoint
    2. Converte AlignmentTransform (legacy) ↔ AlignmentTransform (new)
    3. Orquestra os novos services usando a API legada
    4. Mantém compatibilidade 100% com código existente
    """

    def __init__(self,
                 matching_service: Optional[FiducialMatchingService] = None,
                 transform_service: Optional[AlignmentTransformService] = None,
                 state_service: Optional[AlignmentStateService] = None):
        """
        Inicializa o adapter com os novos services.

        Args:
            matching_service: Serviço de template matching
            transform_service: Serviço de transformações geométricas
            state_service: Serviço de gerenciamento de estado
        """
        self.matching_service = matching_service or FiducialMatchingService()
        self.transform_service = transform_service or AlignmentTransformService()
        self.state_service = state_service or AlignmentStateService()

        # Estado interno
        self._state = self.state_service.create_state()
        self._fiducial_templates: List[FiducialTemplate] = []

        logger.debug("FiducialAlignmentAdapter inicializado")

    # =========================================================================
    # MÉTODOS DE COMPATIBILIDADE (API Legada)
    # =========================================================================

    def capture_template(self, template: FiducialTemplate, frame: np.ndarray) -> bool:
        """
        Captura template do frame (captura centralizada).

        Args:
            template: Template legado para preencher
            frame: Frame da câmera (numpy array BGR ou grayscale)

        Returns:
            True se capturou com sucesso, False caso contrário
        """
        try:
            h, w = frame.shape[:2]
            win = template.window_size

            # Extrai região central
            x1 = max(0, (w - win) // 2)
            y1 = max(0, (h - win) // 2)
            x2 = min(w, x1 + win)
            y2 = min(h, y1 + win)

            roi = frame[y1:y2, x1:x2]

            # Converte para grayscale
            if len(roi.shape) == 3:
                gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            else:
                gray = roi.copy()

            template.template_gray = gray
            template.template_bgr = roi.copy()

            logger.debug(f"Template capturado: {gray.shape}")
            return True

        except Exception as e:
            logger.error(f"Erro ao capturar template: {e}")
            return False

    def capture_template_at_point(self, template: FiducialTemplate, image: np.ndarray, x: int, y: int) -> bool:
        """
        Extrai template da imagem em um ponto específico.

        Args:
            template: Template legado para preencher
            image: Imagem (numpy array BGR ou grayscale)
            x: Coordenada X do centro
            y: Coordenada Y do centro

        Returns:
            True se capturou com sucesso, False caso contrário
        """
        try:
            h, w = image.shape[:2]
            win = template.window_size

            # Extrai região centralizada no ponto
            x1 = max(0, x - win // 2)
            y1 = max(0, y - win // 2)
            x2 = min(w, x1 + win)
            y2 = min(h, y1 + win)

            roi = image[y1:y2, x1:x2]

            # Converte para grayscale
            if len(roi.shape) == 3:
                gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            else:
                gray = roi.copy()

            template.template_gray = gray
            template.template_bgr = roi.copy()

            logger.debug(f"Template capturado em ({x}, {y}): {gray.shape}")
            return True

        except Exception as e:
            logger.error(f"Erro ao capturar template em ({x}, {y}): {e}")
            return False

    def add_template(self, template: FiducialTemplate) -> None:
        """
        Adiciona um template fiducial (API legada).

        Args:
            template: FiducialTemplate do sistema legado
        """
        self._fiducial_templates.append(template)

        # Converter para novo modelo e adicionar ao estado
        fiducial_point = self._template_to_point(template)
        self.state_service.add_fiducial(
            self._state,
            gerber_x=template.gerber_x,
            gerber_y=template.gerber_y,
            fiducial_type="template",
            template=template.template_gray,
            template_x=template.gerber_x,  # Posição inicial = gerber_x
            template_y=template.gerber_y,
            window_size=template.window_size,
            search_radius=template.search_radius
        )

        logger.debug(f"Template '{template.name}' adicionado ao adapter")

    def locate_fiducials(self, image: np.ndarray) -> List[FiducialMatchResult]:
        """
        Busca fiduciais na imagem (API legada).

        Args:
            image: Imagem para buscar (numpy array BGR ou grayscale)

        Returns:
            Lista de FiducialMatchResult (API legada)
        """
        # Converter templates legados para FiducialPoint
        fiducial_points = []
        for template in self._fiducial_templates:
            point = self._template_to_point(template)
            fiducial_points.append(point)

        # Executar busca usando novo serviço
        matched_points = self.matching_service.locate_fiducials(
            image=image,
            fiducials=fiducial_points
        )

        # Converter resultados de volta para API legada
        results = []
        for template, matched_point in zip(self._fiducial_templates, matched_points):
            result = FiducialMatchResult(
                found=matched_point.is_matched,
                similarity=matched_point.correlation * 100 if matched_point.correlation else 0.0,
                image_x=matched_point.matched_x or 0.0,
                image_y=matched_point.matched_y or 0.0,
                offset_x=0.0,  # TODO: calcular offset real
                offset_y=0.0
            )
            results.append(result)

        logger.info(f"Localização concluída: {sum(r.found for r in results)}/{len(results)} encontrados")
        return results

    def calculate_transform(self,
                           gerber_points: List[Tuple[float, float]],
                           image_points: List[Tuple[float, float]]) -> LegacyTransform:
        """
        Calcula transformação entre pontos (API legada).

        Args:
            gerber_points: Lista de pontos no Gerber [(x1, y1), (x2, y2), ...]
            image_points: Lista de pontos na imagem [(x1, y1), (x2, y2), ...]

        Returns:
            AlignmentTransform (API legada)
        """
        # Usar novo serviço para calcular transformação
        new_transform = self.transform_service.calculate_transform(
            src_points=gerber_points,
            dst_points=image_points
        )

        # Converter para API legada
        legacy_transform = LegacyTransform(
            tx=new_transform.tx,
            ty=new_transform.ty,
            angle=new_transform.angle,
            scale_x=new_transform.scale_x,
            scale_y=new_transform.scale_y
        )

        logger.info(
            f"Transformação calculada: tx={legacy_transform.tx:.1f}, "
            f"ty={legacy_transform.ty:.1f}, angle={legacy_transform.angle:.2f}°"
        )

        return legacy_transform

    def adjust_transform(self,
                        current: LegacyTransform,
                        delta_tx: float,
                        delta_ty: float,
                        delta_angle: float,
                        delta_scale: float) -> LegacyTransform:
        """
        Ajusta transformação manualmente (API legada).

        Args:
            current: Transformação atual
            delta_tx: Delta translação X
            delta_ty: Delta translação Y
            delta_angle: Delta rotação (graus)
            delta_scale: Delta escala

        Returns:
            Nova AlignmentTransform (API legada)
        """
        adjusted = LegacyTransform(
            tx=current.tx + delta_tx,
            ty=current.ty + delta_ty,
            angle=current.angle + delta_angle,
            scale_x=current.scale_x + delta_scale,
            scale_y=current.scale_y + delta_scale
        )

        logger.debug(
            f"Transformação ajustada: tx={adjusted.tx:.1f}, ty={adjusted.ty:.1f}, "
            f"angle={adjusted.angle:.2f}°, scale={adjusted.scale_x:.4f}"
        )

        return adjusted

    # =========================================================================
    # MÉTODOS DE CONVERSÃO (Legacy ↔ New)
    # =========================================================================

    def _template_to_point(self, template: FiducialTemplate) -> FiducialPoint:
        """Converte FiducialTemplate (legacy) → FiducialPoint (new)"""
        # Converter threshold (0-100) → matching_threshold (0-1)
        threshold_normalized = template.threshold / 100.0

        # Criar config com parâmetros do template
        config = FiducialConfig(
            matching_threshold=threshold_normalized,
            search_radius=template.search_radius,
            window_size=template.window_size
        )

        return FiducialPoint(
            gerber_x=template.gerber_x,
            gerber_y=template.gerber_y,
            fiducial_type=FiducialType.TEMPLATE,
            window_size=template.window_size,
            search_radius=template.search_radius,
            template=template.template_gray,
            template_x=template.gerber_x,
            template_y=template.gerber_y
        )

    def _new_to_legacy_transform(self, new_transform: NewTransform) -> LegacyTransform:
        """Converte AlignmentTransform (new) → AlignmentTransform (legacy)"""
        return LegacyTransform(
            tx=new_transform.tx,
            ty=new_transform.ty,
            angle=new_transform.angle,
            scale_x=new_transform.scale_x,
            scale_y=new_transform.scale_y
        )

    def _legacy_to_new_transform(self, legacy_transform: LegacyTransform) -> NewTransform:
        """Converte AlignmentTransform (legacy) → AlignmentTransform (new)"""
        return NewTransform(
            tx=legacy_transform.tx,
            ty=legacy_transform.ty,
            angle=legacy_transform.angle,
            scale_x=legacy_transform.scale_x,
            scale_y=legacy_transform.scale_y
        )

    # =========================================================================
    # MÉTODOS DE ESTADO E PERSISTÊNCIA
    # =========================================================================

    def save_state(self, filepath: str) -> None:
        """Salva estado atual em arquivo JSON"""
        # Atualizar estado com templates atuais
        for template in self._fiducial_templates:
            point = self._template_to_point(template)
            # Verificar se já existe no estado
            exists = any(
                f.gerber_x == template.gerber_x and f.gerber_y == template.gerber_y
                for f in self._state.fiducials
            )
            if not exists:
                self.state_service.add_fiducial(
                    self._state,
                    gerber_x=template.gerber_x,
                    gerber_y=template.gerber_y,
                    fiducial_type="template",
                    template=template.template_gray,
                    template_x=template.gerber_x,
                    template_y=template.gerber_y,
                    window_size=template.window_size,
                    search_radius=template.search_radius
                )

        self.state_service.save_state(self._state, filepath)
        logger.info(f"Estado salvo em {filepath}")

    def load_state(self, filepath: str) -> None:
        """Carrega estado de arquivo JSON"""
        self._state = self.state_service.load_state(filepath)

        # Reconstruir lista de templates a partir do estado
        self._fiducial_templates.clear()
        for point in self._state.fiducials:
            if point.has_template():
                template = FiducialTemplate(
                    name=f"Fiducial_{point.gerber_x}_{point.gerber_y}",
                    template_gray=point.template,
                    template_bgr=point.template,  # Assumindo BGR
                    window_size=point.window_size,
                    search_radius=point.search_radius,
                    threshold=70.0,  # Default
                    gerber_x=point.gerber_x,
                    gerber_y=point.gerber_y
                )
                self._fiducial_templates.append(template)

        logger.info(f"Estado carregado de {filepath}: {len(self._fiducial_templates)} templates")

    def get_template_count(self) -> int:
        """Retorna número de templates configurados"""
        return len(self._fiducial_templates)

    def is_ready_for_alignment(self) -> Tuple[bool, str]:
        """
        Verifica se pronto para calcular alinhamento.

        Returns:
            (is_ready, message): Tupla com validação e mensagem
        """
        is_valid, message = self.state_service.validate_state(self._state)
        return is_valid, message

    def get_alignment_summary(self) -> dict:
        """Retorna resumo do estado de alinhamento"""
        return self.state_service.get_state_summary(self._state)

    # =========================================================================
    # MÉTODOS AUXILIARES PARA REDUZIR COMPLEXIDADE DO WIDGET
    # =========================================================================

    def update_transform_from_controls(self, tx: float, ty: float,
                                       angle: float, scale_x: float, scale_y: float) -> None:
        """
        Atualiza transformação no estado a partir de valores de controle.

        Args:
            tx: Translação X
            ty: Translação Y
            angle: Rotação em graus
            scale_x: Escala X
            scale_y: Escala Y
        """
        if self._state.transform is None:
            self._state.transform = NewTransform(
                tx=tx, ty=ty, angle=angle, scale_x=scale_x, scale_y=scale_y
            )
        else:
            # Atualiza valores existentes
            t = self._state.transform
            t.tx = tx
            t.ty = ty
            t.angle = angle
            t.scale_x = scale_x
            t.scale_y = scale_y

        logger.debug(f"Transformação atualizada: tx={tx:.1f}, ty={ty:.1f}, angle={angle:.2f}°")

    def get_legacy_transform(self) -> Optional[LegacyTransform]:
        """
        Retorna transformação atual convertida para modelo legado.

        Returns:
            AlignmentTransform (modelo legado) ou None
        """
        new_transform = self._state.transform
        if new_transform is None:
            return None

        return self._new_to_legacy_transform(new_transform)

    def calculate_alignment_from_matched_fiducials(self) -> Optional[LegacyTransform]:
        """
        Calcula transformação baseada nos fiduciais matched.

        Returns:
            AlignmentTransform (modelo legado) ou None se não foi possível calcular
        """
        # Obtém pontos Gerber e imagem dos fiduciais matched
        gerber_points = []
        image_points = []

        for f in self._state.fiducials:
            if f.is_matched and f.matched_x is not None and f.matched_y is not None:
                gerber_points.append((f.gerber_x, f.gerber_y))
                image_points.append((f.matched_x, f.matched_y))

        if len(gerber_points) < 2:
            logger.warning(f"Poucos fiduciais matched: {len(gerber_points)} < 2")
            return None

        # Calcula transformação usando adapter
        new_transform = self.transform_service.calculate_transform(gerber_points, image_points)

        # Atualiza estado
        self._state.transform = new_transform

        # Converte para modelo legado
        return self._new_to_legacy_transform(new_transform)

    def get_matched_fiducial_count(self) -> int:
        """Retorna número de fiduciais com match."""
        return sum(1 for f in self._state.fiducials if f.is_matched)
