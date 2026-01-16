"""
Testes unitários para PLCHomingController

Testa operações de homing de eixos PLC.
"""

import pytest
import time
from unittest.mock import Mock, patch
from aoi_lib.plc.controllers.plc_homing_controller import PLCHomingController


class TestPLCHomingController:
    """Testes para PLCHomingController"""

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
        controller.get_targets = Mock(return_value={})
        return controller

    @pytest.fixture
    def controller(self, connection_manager, absolute_controller):
        """Fixture para controller"""
        return PLCHomingController(
            connection_manager=connection_manager,
            absolute_controller=absolute_controller
        )

    def test_init(self, connection_manager, absolute_controller):
        """Testa inicialização"""
        controller = PLCHomingController(
            connection_manager=connection_manager,
            absolute_controller=absolute_controller
        )

        assert controller.connection_manager == connection_manager
        assert controller.absolute_controller == absolute_controller

    def test_home_all_success(self, controller):
        """Testa homing de todos os eixos com sucesso"""
        controller._pulse_coil = Mock()

        with patch('time.sleep'):  # Mock sleep para acelerar teste
            result = controller.home_all()

        assert result == True
        # Deve chamar _pulse_coil 3 vezes: Z, X, Y
        assert controller._pulse_coil.call_count == 3

    def test_home_all_disconnected(self, controller):
        """Testa home_all quando desconectado"""
        controller.connection_manager.is_connected.return_value = False

        with pytest.raises(IOError, match="PLC não conectado"):
            controller.home_all()

    def test_home_all_failure(self, controller):
        """Testa home_all com erro durante execução"""
        controller._pulse_coil = Mock(side_effect=Exception("Erro Modbus"))

        with patch('time.sleep'):
            result = controller.home_all()

        assert result == False

    def test_home_axis_x(self, controller):
        """Testa homing do eixo X"""
        controller._pulse_coil = Mock()

        result = controller.home_axis('X')

        assert result == True
        controller._pulse_coil.assert_called_once_with(
            controller.ADDRESSES['X']['zero']
        )

    def test_home_axis_y(self, controller):
        """Testa homing do eixo Y"""
        controller._pulse_coil = Mock()

        result = controller.home_axis('Y')

        assert result == True
        controller._pulse_coil.assert_called_once_with(
            controller.ADDRESSES['Y']['zero']
        )

    def test_home_axis_z(self, controller):
        """Testa homing do eixo Z"""
        controller._pulse_coil = Mock()

        result = controller.home_axis('Z')

        assert result == True
        controller._pulse_coil.assert_called_once_with(
            controller.ADDRESSES['Z']['zero']
        )

    def test_home_axis_lowercase(self, controller):
        """Testa home_axis com eixo minúsculo (deve converter)"""
        controller._pulse_coil = Mock()

        result = controller.home_axis('x')

        assert result == True
        controller._pulse_coil.assert_called_once()

    def test_home_axis_invalid(self, controller):
        """Testa home_axis com eixo inválido"""
        with pytest.raises(ValueError, match="Eixo inválido"):
            controller.home_axis('W')

    def test_home_axis_disconnected(self, controller):
        """Testa home_axis quando desconectado"""
        controller.connection_manager.is_connected.return_value = False

        with pytest.raises(IOError, match="PLC não conectado"):
            controller.home_axis('X')

    def test_home_axis_failure(self, controller):
        """Testa home_axis com erro durante execução"""
        controller._pulse_coil = Mock(side_effect=Exception("Erro"))

        result = controller.home_axis('X')

        assert result == False

    def test_unlock(self, controller):
        """Testa desbloqueio de eixos"""
        controller.unlock()

        # Deve limpar alvos do absolute controller
        controller.absolute_controller.get_targets.return_value = {}
        controller.absolute_controller.get_targets.assert_called()

    def test_pulse_coil(self, controller):
        """Testa pulso de coil"""
        controller.connection_manager.client.write_coil = Mock()

        with patch('time.sleep'):
            controller._pulse_coil(1000, duration_ms=100)

        # Deve ligar e desligar o coil
        assert controller.connection_manager.client.write_coil.call_count == 2
        calls = controller.connection_manager.client.write_coil.call_args_list
        assert calls[0][0] == (1000, True)  # Liga
        assert calls[1][0] == (1000, False)  # Desliga
