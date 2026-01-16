"""
Testes unitários para PLCRelativeMovementController

Testa movimento relativo de eixos PLC.
"""

import pytest
from unittest.mock import Mock
from aoi_lib.plc.controllers.plc_relative_movement_controller import PLCRelativeMovementController


class TestPLCRelativeMovementController:
    """Testes para PLCRelativeMovementController"""

    @pytest.fixture
    def connection_manager(self):
        """Fixture para connection manager mockado"""
        manager = Mock()
        manager.is_connected.return_value = True
        manager.client = Mock()
        return manager

    @pytest.fixture
    def absolute_controller(self):
        """Fixture para absolute controller mockado"""
        controller = Mock()
        controller.apply_motion_pulses = Mock(return_value=True)
        controller._clamp_feed_rate = Mock(return_value=1000.0)
        return controller

    @pytest.fixture
    def controller(self, connection_manager, absolute_controller):
        """Fixture para controller"""
        return PLCRelativeMovementController(
            connection_manager=connection_manager,
            absolute_controller=absolute_controller,
            pulses_per_mm=80.0
        )

    def test_init(self, connection_manager, absolute_controller):
        """Testa inicialização"""
        controller = PLCRelativeMovementController(
            connection_manager=connection_manager,
            absolute_controller=absolute_controller,
            pulses_per_mm=80.0
        )

        assert controller.connection_manager == connection_manager
        assert controller.absolute_controller == absolute_controller
        assert controller.pulses_per_mm == 80.0

    def test_move_relative_forward(self, controller):
        """Testa movimento relativo para frente"""
        # Mock _read_dword para retornar posição atual
        controller._read_dword = Mock(return_value=4000)

        result = controller.move_relative('X', 800, speed=80000)

        assert result == True
        # 4000 (atual) + 800 (distância) = 4800
        controller.absolute_controller.apply_motion_pulses.assert_called_once()
        call_args = controller.absolute_controller.apply_motion_pulses.call_args
        assert call_args[0][0] == {'X': 4800}

    def test_move_relative_backward(self, controller):
        """Testa movimento relativo para trás"""
        controller._read_dword = Mock(return_value=4000)

        result = controller.move_relative('X', -800, speed=80000)

        assert result == True
        # 4000 (atual) + (-800) (distância) = 3200
        call_args = controller.absolute_controller.apply_motion_pulses.call_args
        assert call_args[0][0] == {'X': 3200}

    def test_move_relative_invalid_axis(self, controller):
        """Testa movimento relativo com eixo inválido"""
        with pytest.raises(ValueError, match="Eixo inválido"):
            controller.move_relative('W', 800)

    def test_move_relative_single_axis(self, controller):
        """Testa movimento relativo de eixo único sem velocidade"""
        controller._read_dword = Mock(return_value=4000)

        result = controller.move_relative_single_axis('X', 800)

        assert result == True
        # Deve chamar move_relative com speed=0.0
        call_args = controller.absolute_controller.apply_motion_pulses.call_args
        assert call_args[0][0] == {'X': 4800}

    def test_step_move_forward(self, controller):
        """Testa movimento passo a passo para frente"""
        controller.move_relative_single_axis = Mock(return_value=True)

        result = controller.step_move('X', 100, 'forward')

        assert result == True
        controller.move_relative_single_axis.assert_called_once_with('X', 100)

    def test_step_move_backward(self, controller):
        """Testa movimento passo a passo para trás"""
        controller.move_relative_single_axis = Mock(return_value=True)

        result = controller.step_move('Y', 50, 'backward')

        assert result == True
        controller.move_relative_single_axis.assert_called_once_with('Y', -50)

    def test_step_move_invalid_direction(self, controller):
        """Testa step_move com direção inválida"""
        with pytest.raises(ValueError, match="Direção inválida"):
            controller.step_move('X', 100, 'left')

    def test_step_move_invalid_axis(self, controller):
        """Testa step_move com eixo inválido"""
        with pytest.raises(ValueError, match="Eixo inválido"):
            controller.step_move('W', 100, 'forward')

    def test_get_position(self, controller):
        """Testa leitura de posição de eixo"""
        controller._read_dword = Mock(return_value=4000)

        result = controller.get_position('X')

        assert result == 4000
        controller._read_dword.assert_called_once_with(
            controller.ADDRESSES['X']['pos_reg']
        )

    def test_get_position_invalid_axis(self, controller):
        """Testa get_position com eixo inválido"""
        with pytest.raises(ValueError, match="Eixo inválido"):
            controller.get_position('W')
