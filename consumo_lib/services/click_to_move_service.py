"""
services/click_to_move_service.py
---------------------------------

Service para conversão de cliques em imagem para movimentos CNC.

Responsável por converter coordenadas de pixel em coordenadas de máquina
e executar o movimento, usando FOV calibration.
"""

import logging
from typing import Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ClickMoveResult:
    """Resultado de uma operação de click-to-move."""
    success: bool
    error_message: Optional[str] = None
    movement_made: bool = False
    distance_moved: Optional[Tuple[float, float]] = None  # (dx_mm, dy_mm)


class ClickToMoveService:
    """
    Service para conversão de cliques em movimentos CNC.

    Responsabilidades:
        - Converter coordenadas de pixel para offset de centro
        - Converter offset para mm usando FOV calibration
        - Converter mm para pulsos se necessário
        - Executar movimento relativo
        - Aplicar correção de espelhamento Y

    Este service NÃO tem dependência de PyQt.
    """

    def __init__(self, movement_service, fov_converter):
        """
        Inicializa o service.

        Args:
            movement_service: Instância de MovementService
            fov_converter: Instância de CameraFOVConverter
        """
        self.movement = movement_service
        self.fov = fov_converter

    def move_to_pixel(self, pixel_x: int, pixel_y: int,
                      image_size: Tuple[int, int],
                      z_current: float = 0.0,
                      feed_rate: float = 1000.0,
                      invert_y: bool = False) -> ClickMoveResult:
        """
        Converte clique em pixel e executa movimento CNC.

        Fluxo:
        1. Calcular offset do centro da imagem (pixel)
        2. Converter para mm usando FOV calibration
        3. Converter para pulsos (se necessário)
        4. Executar movimento relativo

        Args:
            pixel_x: Coordenada X do clique na imagem (pixel)
            pixel_y: Coordenada Y do clique na imagem (pixel)
            image_size: Tamanho da imagem (width, height) em pixels
            z_current: Posição Z atual (mm) - usado para calcular FOV
            feed_rate: Feed rate para movimento (mm/min)
            invert_y: Se True, inverte eixo Y (espelhamento vertical)

        Returns:
            ClickMoveResult com detalhes da operação
        """
        # 1. Validar conexão
        conn_result = self.movement.validate_connection()
        if not conn_result.success:
            return ClickMoveResult(
                success=False,
                error_message=conn_result.error_message
            )

        # 2. Calcular offset do centro em pixels
        center_x = image_size[0] // 2
        center_y = image_size[1] // 2

        offset_x_pixels = pixel_x - center_x
        offset_y_pixels = pixel_y - center_y

        logger.debug(f"Offset do centro: ({offset_x_pixels}, {offset_y_pixels}) pixels")

        # 3. Atualizar tamanho do frame no FOV converter
        self.fov.set_frame_size(*image_size)

        # 4. Converter para pulsos usando FOV calibration
        try:
            dx_pulses, dy_pulses = self.fov.video_click_to_movement(
                offset_x_pixels,
                offset_y_pixels,
                invert_y=invert_y
            )

            logger.debug(f"Offset em pulsos: ({dx_pulses}, {dy_pulses})")

        except Exception as e:
            logger.error(f"Erro ao converter pixels para pulsos: {e}")
            return ClickMoveResult(
                success=False,
                error_message=f"Erro na conversão FOV: {e}"
            )

        # 5. Verificar se movimento é significativo
        if abs(dx_pulses) < 5 and abs(dy_pulses) < 5:
            logger.debug("Movimento muito pequeno, ignorando")
            return ClickMoveResult(
                success=True,
                movement_made=False,
                error_message=None
            )

        # 6. Converter pulsos para mm
        try:
            pulses_per_mm = self.movement.cnc.pulses_per_mm
            dx_mm = dx_pulses / pulses_per_mm
            dy_mm = dy_pulses / pulses_per_mm

            logger.debug(f"Offset em mm: ({dx_mm:.3f}, {dy_mm:.3f})")

        except Exception as e:
            logger.error(f"Erro ao converter pulsos para mm: {e}")
            return ClickMoveResult(
                success=False,
                error_message=f"Erro na conversão mm: {e}"
            )

        # 7. Executar movimento relativo
        try:
            self.movement.cnc.move_relative(x=dx_mm, y=dy_mm, feed_rate=feed_rate)

            logger.info(f"Click-to-move executado: Δ({dx_mm:.3f}, {dy_mm:.3f}) mm @ {feed_rate} mm/min")

            return ClickMoveResult(
                success=True,
                movement_made=True,
                distance_moved=(dx_mm, dy_mm)
            )

        except Exception as e:
            logger.error(f"Erro ao executar movimento: {e}")
            return ClickMoveResult(
                success=False,
                error_message=f"Erro ao mover: {e}"
            )

    def calculate_offset_from_center(self, pixel_x: int, pixel_y: int,
                                     image_size: Tuple[int, int],
                                     invert_y: bool = False) -> Tuple[float, float]:
        """
        Calcula offset em mm a partir do centro da imagem.

        Args:
            pixel_x: Coordenada X do clique
            pixel_y: Coordenada Y do clique
            image_size: Tamanho da imagem (width, height)
            invert_y: Se True, inverte eixo Y

        Returns:
            Tuple (dx_mm, dy_mm) com offset em mm
        """
        # Calcular offset do centro em pixels
        center_x = image_size[0] // 2
        center_y = image_size[1] // 2

        offset_x_pixels = pixel_x - center_x
        offset_y_pixels = pixel_y - center_y

        # Atualizar frame size
        self.fov.set_frame_size(*image_size)

        # Converter para pulsos
        dx_pulses, dy_pulses = self.fov.video_click_to_movement(
            offset_x_pixels,
            offset_y_pixels,
            invert_y=invert_y
        )

        # Converter para mm
        pulses_per_mm = self.movement.cnc.pulses_per_mm
        dx_mm = dx_pulses / pulses_per_mm
        dy_mm = dy_pulses / pulses_per_mm

        return (dx_mm, dy_mm)
