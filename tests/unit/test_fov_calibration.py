"""
Testes para o módulo de calibração FOV (Field of View).

Testa a conversão entre pixels e milímetros para câmera fixa,
considerando diferentes alturas Z e inversão de eixo Y.
"""

import pytest
import numpy as np
from aoi_lib.fov_calibration import FOVCalibration, CameraFOVConverter


class TestFixedCameraFOV:
    """
    Testa comportamento de FOV para câmera fixa.

    Ao contrário da ADESIVADORA (câmera móvel), o Tensiometro
    possui câmera fixa, portanto o FOV deve ser constante
    independentemente da altura Z.
    """

    def test_fov_constant_across_z_heights(self):
        """
        Testa que FOV permanece constante em diferentes alturas Z.

        Para câmera fixa, get_fov_at_z() deve retornar os mesmos
        valores de largura e altura para qualquer Z.
        """
        fov = FOVCalibration(
            z0_z_pulses=0,
            z0_width_mm=50.0,
            z0_height_mm=37.5
        )

        # Verifica que z1 = z0 (forçado pela classe)
        assert fov.z0_width_mm == fov.z1_width_mm, \
            "z0_width deve ser igual a z1_width"
        assert fov.z0_height_mm == fov.z1_height_mm, \
            "z0_height deve ser igual a z1_height"

        # Testa conversor em diferentes alturas Z
        converter = CameraFOVConverter(fov)
        converter.set_frame_size(640, 480)
        converter.set_axis_calibration("X", 100.0)  # 100 pulsos/mm
        converter.set_axis_calibration("Y", 100.0)

        # FOV deve ser o mesmo em qualquer Z
        fov_z0 = converter.get_fov_at_z(0)
        fov_z100 = converter.get_fov_at_z(100)
        fov_z200 = converter.get_fov_at_z(200)

        assert fov_z0 == fov_z100 == fov_z200, \
            "FOV deve ser constante em todas as alturas Z"

    def test_fov_returns_tuple(self):
        """Testa que get_fov_at_z retorna uma tupla (width, height)."""
        fov = FOVCalibration(
            z0_z_pulses=0,
            z0_width_mm=50.0,
            z0_height_mm=37.5
        )

        converter = CameraFOVConverter(fov)
        result = converter.get_fov_at_z(0)

        assert isinstance(result, tuple), "get_fov_at_z deve retornar tuple"
        assert len(result) == 2, "get_fov_at_z deve retornar (width, height)"

    def test_fov_positive_values(self):
        """Testa que FOV sempre retorna valores positivos."""
        fov = FOVCalibration(
            z0_z_pulses=0,
            z0_width_mm=50.0,
            z0_height_mm=37.5
        )

        converter = CameraFOVConverter(fov)
        width, height = converter.get_fov_at_z(0)

        assert width > 0, "FOV width deve ser positivo"
        assert height > 0, "FOV height deve ser positivo"


class TestYInversion:
    """
    Testa inversão de eixo Y para conversão de coordenadas.

    O sistema de coordenadas da imagem tem Y aumentando para baixo,
    enquanto o CNC tem Y aumentando para cima (em direção ao operador).
    Portanto, é necessário inverter Y ao converter de imagem para CNC.
    """

    @pytest.fixture
    def fov_converter(self):
        """Fixture com configuração padrão de FOV."""
        fov = FOVCalibration(
            z0_z_pulses=0,
            z0_width_mm=50.0,
            z0_height_mm=37.5
        )
        converter = CameraFOVConverter(fov)
        converter.set_frame_size(640, 480)
        converter.set_axis_calibration("X", 100.0)
        converter.set_axis_calibration("Y", 100.0)
        return converter

    def test_y_inversion_move_down(self, fov_converter):
        """
        Testa movimento para baixo (aumentar pixel Y).

        Ao clicar na parte inferior da imagem (maior pixel Y),
        o CNC deve se mover para baixo (menor Y em coordenadas CNC).
        """
        display_w, display_h = 640, 480

        # Clicar 100 pixels abaixo do centro
        click_x, click_y = 320, 340  # Centro Y + 100

        dx_pulses, dy_pulses = fov_converter.video_click_to_movement(
            click_x, click_y,
            display_w, display_h,
            z_pulses=0,
            invert_y=False  # Comportamento padrão
        )

        # dx deve ser ~0 (clicou no centro X)
        assert abs(dx_pulses) < 10, f"dx deveria ser ~0, mas é {dx_pulses}"
        # dy deve ser NEGATIVO (mover para baixo no CNC)
        assert dy_pulses < 0, \
            f"dy deveria ser negativo (câmera para baixo), mas é {dy_pulses}"

    def test_y_inversion_move_up(self, fov_converter):
        """
        Testa movimento para cima (diminuir pixel Y).

        Ao clicar na parte superior da imagem (menor pixel Y),
        o CNC deve se mover para cima (maior Y em coordenadas CNC).
        """
        display_w, display_h = 640, 480

        # Clicar 100 pixels acima do centro
        click_x, click_y = 320, 140  # Centro Y - 100

        dx_pulses, dy_pulses = fov_converter.video_click_to_movement(
            click_x, click_y,
            display_w, display_h,
            z_pulses=0,
            invert_y=False  # Comportamento padrão
        )

        # dx deve ser ~0
        assert abs(dx_pulses) < 10, f"dx deveria ser ~0, mas é {dx_pulses}"
        # dy deve ser POSITIVO (mover para cima no CNC)
        assert dy_pulses > 0, \
            f"dy deveria ser positivo (câmera para cima), mas é {dy_pulses}"

    def test_x_no_inversion_right(self, fov_converter):
        """
        Testa que eixo X NÃO é invertido (direita).

        X aumenta da esquerda para a direita tanto na imagem quanto no CNC.
        """
        display_w, display_h = 640, 480

        # Clicar 100 pixels à direita do centro
        click_x, click_y = 420, 240  # Centro X + 100

        dx_pulses, dy_pulses = fov_converter.video_click_to_movement(
            click_x, click_y,
            display_w, display_h,
            z_pulses=0,
            invert_y=False
        )

        # dx deve ser POSITIVO (mover para direita)
        assert dx_pulses > 0, \
            f"dx deveria ser positivo (mover para direita), mas é {dx_pulses}"
        # dy deve ser ~0 (clicou no centro Y)
        assert abs(dy_pulses) < 10, f"dy deveria ser ~0, mas é {dy_pulses}"

    def test_x_no_inversion_left(self, fov_converter):
        """
        Testa que eixo X NÃO é invertido (esquerda).
        """
        display_w, display_h = 640, 480

        # Clicar 100 pixels à esquerda do centro
        click_x, click_y = 220, 240  # Centro X - 100

        dx_pulses, dy_pulses = fov_converter.video_click_to_movement(
            click_x, click_y,
            display_w, display_h,
            z_pulses=0,
            invert_y=False
        )

        # dx deve ser NEGATIVO (mover para esquerda)
        assert dx_pulses < 0, \
            f"dx deveria ser negativo (mover para esquerda), mas é {dx_pulses}"
        # dy deve ser ~0
        assert abs(dy_pulses) < 10, f"dy deveria ser ~0, mas é {dy_pulses}"

    def test_click_center_no_movement(self, fov_converter):
        """
        Testa que clicar no centro não resulta em movimento.

        Clicar exatamente no centro da imagem deve resultar em
        dx=0 e dy=0 (sem movimento).
        """
        display_w, display_h = 640, 480
        center_x, center_y = display_w // 2, display_h // 2

        dx_pulses, dy_pulses = fov_converter.video_click_to_movement(
            center_x, center_y,
            display_w, display_h,
            z_pulses=0,
            invert_y=False
        )

        # Sem movimento (tolerância pequena para erros de ponto flutuante)
        assert abs(dx_pulses) < 1, "Clicar no centro X não deve gerar movimento em X"
        assert abs(dy_pulses) < 1, "Clicar no centro Y não deve gerar movimento em Y"


class TestFOVEdgeCases:
    """Testa casos extremos e borda."""

    def test_negative_fov_values(self):
        """Testa que valores negativos de FOV são aceitos (embora inválidos)."""
        # FOV com valores negativos (inválido, mas pode acontecer por bug)
        fov = FOVCalibration(
            z0_z_pulses=0,
            z0_width_mm=-50.0,
            z0_height_mm=-37.5
        )

        # Valores devem ser negativos (testa que não há erro)
        assert fov.z0_width_mm < 0
        assert fov.z0_height_mm < 0

    def test_extreme_z_heights(self):
        """Testa FOV em alturas Z extremas."""
        fov = FOVCalibration(
            z0_z_pulses=0,
            z0_width_mm=50.0,
            z0_height_mm=37.5
        )

        converter = CameraFOVConverter(fov)
        converter.set_frame_size(640, 480)

        # Z muito alto
        fov_z_high = converter.get_fov_at_z(z_pulses=100000)
        assert fov_z_high == (50.0, 37.5), "FOV deve ser constante mesmo em Z extremo"

        # Z negativo (pode acontecer em homing)
        fov_z_neg = converter.get_fov_at_z(z_pulses=-100)
        assert fov_z_neg == (50.0, 37.5), "FOV deve ser constante mesmo em Z negativo"
