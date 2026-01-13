"""
Testes unitários para EngineeringHardwareCoordinator

Testa o coordenador de hardware do Engineering Wizard.
"""

import pytest
import numpy as np
from unittest.mock import Mock, MagicMock

from consumo_lib.coordinators.engineering_hardware_coordinator import (
    EngineeringHardwareCoordinator,
    HardwareType
)


class TestEngineeringHardwareCoordinatorCreation:
    """Testes para criação do coordenador."""

    def test_create_without_hardware(self):
        """Testa criação sem hardware (modo offline)."""
        coordinator = EngineeringHardwareCoordinator()

        assert coordinator.camera_controller is None
        assert coordinator.plc_controller is None
        assert coordinator.fiducial_aligner is None

    def test_create_with_camera(self):
        """Testa criação com câmera."""
        mock_camera = Mock()
        coordinator = EngineeringHardwareCoordinator(camera_controller=mock_camera)

        assert coordinator.camera_controller is mock_camera
        assert coordinator.plc_controller is None

    def test_create_with_plc(self):
        """Testa criação com PLC."""
        mock_plc = Mock()
        coordinator = EngineeringHardwareCoordinator(plc_controller=mock_plc)

        assert coordinator.plc_controller is mock_plc
        assert coordinator.camera_controller is None

    def test_create_with_all_hardware(self):
        """Testa criação com todo hardware."""
        mock_camera = Mock()
        mock_plc = Mock()
        mock_aligner = Mock()

        coordinator = EngineeringHardwareCoordinator(
            camera_controller=mock_camera,
            plc_controller=mock_plc,
            fiducial_aligner=mock_aligner
        )

        assert coordinator.camera_controller is mock_camera
        assert coordinator.plc_controller is mock_plc
        assert coordinator.fiducial_aligner is mock_aligner


class TestHardwareType:
    """Testes para enum HardwareType."""

    def test_hardware_type_values(self):
        """Testa valores do enum."""
        assert HardwareType.CAMERA.value == "camera"
        assert HardwareType.PLC.value == "plc"
        assert HardwareType.FIDUCIAL_ALIGNER.value == "fiducial_aligner"


class TestIsHardwareReady:
    """Testes para método is_hardware_ready()."""

    def test_no_hardware_required(self):
        """Testa sem requisitar hardware."""
        coordinator = EngineeringHardwareCoordinator()
        ready, message = coordinator.is_hardware_ready([])

        assert ready
        assert message == ""

    def test_camera_not_available(self):
        """Testa quando câmera não está disponível."""
        coordinator = EngineeringHardwareCoordinator()
        ready, message = coordinator.is_hardware_ready([HardwareType.CAMERA])

        assert not ready
        assert "Câmera" in message

    def test_camera_available(self):
        """Testa quando câmera está disponível."""
        mock_camera = Mock()
        mock_camera.is_connected = True

        coordinator = EngineeringHardwareCoordinator(camera_controller=mock_camera)
        ready, message = coordinator.is_hardware_ready([HardwareType.CAMERA])

        assert ready
        assert message == ""

    def test_camera_disconnected(self):
        """Testa quando câmera disponível mas desconectada."""
        mock_camera = Mock()
        mock_camera.is_connected = False

        coordinator = EngineeringHardwareCoordinator(camera_controller=mock_camera)
        ready, message = coordinator.is_hardware_ready([HardwareType.CAMERA])

        assert not ready
        assert "não conectada" in message

    def test_plc_not_available(self):
        """Testa quando PLC não está disponível."""
        coordinator = EngineeringHardwareCoordinator()
        ready, message = coordinator.is_hardware_ready([HardwareType.PLC])

        assert not ready
        assert "PLC" in message

    def test_plc_available(self):
        """Testa quando PLC está disponível."""
        mock_plc = Mock()
        mock_plc.is_connected = True

        coordinator = EngineeringHardwareCoordinator(plc_controller=mock_plc)
        ready, message = coordinator.is_hardware_ready([HardwareType.PLC])

        assert ready
        assert message == ""

    def test_multiple_hardware_requirements(self):
        """Testa com múltiplos requisitos de hardware."""
        mock_camera = Mock()
        mock_camera.is_connected = True

        coordinator = EngineeringHardwareCoordinator(camera_controller=mock_camera)
        ready, message = coordinator.is_hardware_ready([
            HardwareType.CAMERA,
            HardwareType.PLC
        ])

        assert not ready
        assert "PLC" in message

    def test_all_hardware_ready(self):
        """Testa quando todo hardware está pronto."""
        mock_camera = Mock()
        mock_camera.is_connected = True
        mock_plc = Mock()
        mock_plc.is_connected = True

        coordinator = EngineeringHardwareCoordinator(
            camera_controller=mock_camera,
            plc_controller=mock_plc
        )
        ready, message = coordinator.is_hardware_ready([
            HardwareType.CAMERA,
            HardwareType.PLC
        ])

        assert ready
        assert message == ""


class TestCaptureFiducialTemplate:
    """Testes para método capture_fiducial_template()."""

    def test_capture_without_hardware_raises_error(self):
        """Testa captura sem hardware levanta erro."""
        coordinator = EngineeringHardwareCoordinator()

        with pytest.raises(RuntimeError, match="Hardware indisponível"):
            coordinator.capture_fiducial_template(10.0, 20.0, 5.0)

    def test_capture_with_mock_hardware(self):
        """Testa captura com hardware mockado."""
        # Mock camera
        mock_camera = Mock()
        mock_camera.is_connected = True
        test_image = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_camera.capture_frame.return_value = test_image

        # Mock PLC
        mock_plc = Mock()
        mock_plc.is_connected = True
        mock_plc.move_absolute.return_value = None
        mock_plc.wait_for_idle.return_value = None

        coordinator = EngineeringHardwareCoordinator(
            camera_controller=mock_camera,
            plc_controller=mock_plc
        )

        result = coordinator.capture_fiducial_template(10.0, 20.0, 5.0, window_size=50)

        assert result['x'] == 10.0
        assert result['y'] == 20.0
        assert result['z'] == 5.0
        assert result['window_size'] == 50
        assert result['image'].shape == (50, 50, 3)
        assert 'captured_at' in result

        # Verificar se PLC foi movido
        assert mock_plc.move_absolute.call_count == 3  # X, Y, Z
        assert mock_plc.wait_for_idle.call_count == 3

        # Verificar se câmera capturou
        mock_camera.capture_frame.assert_called_once()


class TestCaptureMosaicGrid:
    """Testes para método capture_mosaic_grid()."""

    def test_capture_without_hardware_raises_error(self):
        """Testa captura sem hardware levanta erro."""
        coordinator = EngineeringHardwareCoordinator()
        config = {
            'x1': 0.0, 'y1': 0.0,
            'x2': 100.0, 'y2': 50.0,
            'rows': 2, 'cols': 2
        }

        with pytest.raises(RuntimeError, match="Hardware indisponível"):
            coordinator.capture_mosaic_grid(config)

    def test_capture_small_grid(self):
        """Testa captura de grid pequeno (2x2)."""
        # Mock hardware
        mock_camera = Mock()
        mock_camera.is_connected = True
        test_image = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_camera.capture_frame.return_value = test_image

        mock_plc = Mock()
        mock_plc.is_connected = True
        mock_plc.move_absolute.return_value = None
        mock_plc.wait_for_idle.return_value = None

        coordinator = EngineeringHardwareCoordinator(
            camera_controller=mock_camera,
            plc_controller=mock_plc
        )

        config = {
            'x1': 0.0, 'y1': 0.0,
            'x2': 50.0, 'y2': 50.0,
            'rows': 2,
            'cols': 2,
            'delay_ms': 0,
            'z_height': 0.0
        }

        result = coordinator.capture_mosaic_grid(config)

        assert result['total_points'] == 4
        assert result['captured_count'] == 4
        assert len(result['images']) == 4
        assert len(result['grid_points']) == 4
        assert 'config' in result
        assert 'captured_at' in result

        # Verificar movimentos do PLC (4 pontos * 3 eixos)
        assert mock_plc.move_absolute.call_count == 12


class TestPerformFiducialAlignment:
    """Testes para método perform_fiducial_alignment()."""

    def test_alignment_without_templates_raises_error(self):
        """Testa alinhamento sem templates levanta erro."""
        coordinator = EngineeringHardwareCoordinator()
        mosaic = np.zeros((480, 640), dtype=np.uint8)

        with pytest.raises(RuntimeError, match="Mínimo de 2 fiduciais"):
            coordinator.perform_fiducial_alignment([], mosaic)

    def test_alignment_with_insufficient_templates(self):
        """Testa alinhamento com apenas 1 template levanta erro."""
        coordinator = EngineeringHardwareCoordinator()
        mosaic = np.zeros((480, 640), dtype=np.uint8)
        templates = [
            {'image': np.zeros((50, 50), dtype=np.uint8), 'x': 0, 'y': 0, 'z': 0}
        ]

        with pytest.raises(RuntimeError, match="Mínimo de 2 fiduciais"):
            coordinator.perform_fiducial_alignment(templates, mosaic)

    def test_alignment_with_two_templates(self):
        """Testa alinhamento com 2 templates."""
        coordinator = EngineeringHardwareCoordinator()

        # Criar templates simples
        template1 = np.ones((50, 50), dtype=np.uint8) * 255
        template2 = np.ones((50, 50), dtype=np.uint8) * 200

        # Criar mosaico com regiões claras onde os templates estão
        mosaic = np.zeros((480, 640), dtype=np.uint8)
        mosaic[100:150, 100:150] = 255  # Local do template 1
        mosaic[300:350, 400:450] = 200  # Local do template 2

        templates = [
            {'image': template1, 'x': 100, 'y': 100, 'z': 0, 'window_size': 50},
            {'image': template2, 'x': 300, 'y': 400, 'z': 0, 'window_size': 50}
        ]

        result = coordinator.perform_fiducial_alignment(templates, mosaic)

        assert 'tx' in result
        assert 'ty' in result
        assert 'angle' in result
        assert 'scale' in result
        assert 'scores' in result
        assert 'matched_positions' in result
        assert len(result['scores']) == 2
        assert len(result['matched_positions']) == 2


class TestMoveToPosition:
    """Testes para método move_to_position()."""

    def test_move_without_hardware(self):
        """Testa movimento sem hardware retorna False."""
        coordinator = EngineeringHardwareCoordinator()
        result = coordinator.move_to_position(10.0, 20.0, 5.0)

        assert result is False

    def test_move_with_mock_plc(self):
        """Testa movimento com PLC mockado."""
        mock_plc = Mock()
        mock_plc.is_connected = True
        mock_plc.move_absolute.return_value = None
        mock_plc.wait_for_idle.return_value = None

        coordinator = EngineeringHardwareCoordinator(plc_controller=mock_plc)
        result = coordinator.move_to_position(10.0, 20.0, 5.0)

        assert result is True
        assert mock_plc.move_absolute.call_count == 3


class TestCaptureCurrentFrame:
    """Testes para método capture_current_frame()."""

    def test_capture_without_camera(self):
        """Testa captura sem câmera retorna None."""
        coordinator = EngineeringHardwareCoordinator()
        result = coordinator.capture_current_frame()

        assert result is None

    def test_capture_with_mock_camera(self):
        """Testa captura com câmera mockada."""
        mock_camera = Mock()
        mock_camera.is_connected = True
        test_image = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_camera.capture_frame.return_value = test_image

        coordinator = EngineeringHardwareCoordinator(camera_controller=mock_camera)
        result = coordinator.capture_current_frame()

        assert result is not None
        assert result.shape == (480, 640, 3)


class TestGetCurrentPosition:
    """Testes para método get_current_position()."""

    def test_position_without_plc(self):
        """Testa posição sem PLC retorna zeros."""
        coordinator = EngineeringHardwareCoordinator()
        position = coordinator.get_current_position()

        assert position == {'x': 0.0, 'y': 0.0, 'z': 0.0}

    def test_position_with_mock_plc(self):
        """Testa posição com PLC mockado."""
        mock_plc = Mock()
        mock_plc.is_connected = True
        mock_plc.read_position.side_effect = [10.0, 20.0, 5.0]

        coordinator = EngineeringHardwareCoordinator(plc_controller=mock_plc)
        position = coordinator.get_current_position()

        assert position['x'] == 10.0
        assert position['y'] == 20.0
        assert position['z'] == 5.0
