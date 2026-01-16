"""
Testes unitários para PLCJogMovementController

Testa movimento Jog (contínuo) de eixos PLC.
"""

import pytest
from unittest.mock import Mock
from aoi_lib.plc.controllers.plc_jog_movement_controller import PLCJogMovementController


class TestPLCJogMovementController:
    """Testes para PLCJogMovementController"""

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
        controller._clamp_feed_rate = Mock(return_value=1000.0)
        return controller

    @pytest.fixture
    def controller(self, connection_manager, absolute_controller):
        """Fixture para controller"""
        return PLCJogMovementController(
            connection_manager=connection_manager,
            absolute_controller=absolute_controller,
            pulses_per_mm=80.0,
            max_feed={'x': 3000.0, 'y': 3000.0, 'z': 1000.0}
        )

    def test_init(self, connection_manager, absolute_controller):
        """Testa inicialização"""
        controller = PLCJogMovementController(
            connection_manager=connection_manager,
            absolute_controller=absolute_controller,
            pulses_per_mm=80.0
        )

        assert controller.connection_manager == connection_manager
        assert controller.absolute_controller == absolute_controller
        assert controller._jog_state == {'X': 'stopped', 'Y': 'stopped', 'Z': 'stopped'}

    def test_jog_start_lowercase_axis(self, controller):
        """Testa início de jog com eixo minúsculo (deve converter)"""
        controller._write_dword = Mock()
        controller.connection_manager.client.write_coil = Mock()

        controller.jog_start('x', 80000)

        # Deve converter para maiúscula
        assert controller._jog_state['X'] == 'forward'
        controller.connection_manager.client.write_coil.assert_called_once()

    def test_jog_start_uppercase_axis(self, controller):
        """Testa início de jog com eixo maiúsculo"""
        controller._write_dword = Mock()
        controller.connection_manager.client.write_coil = Mock()

        controller.jog_start('Y', 64000)

        assert controller._jog_state['Y'] == 'forward'
        controller.connection_manager.client.write_coil.assert_called_once()

    def test_jog_start_invalid_axis(self, controller):
        """Testa início de jog com eixo inválido"""
        with pytest.raises(ValueError, match="Eixo inválido"):
            controller.jog_start('W', 80000)

    def test_jog_start_disconnected(self, controller):
        """Testa início de jog quando desconectado"""
        controller.connection_manager.is_connected.return_value = False

        with pytest.raises(IOError, match="PLC não conectado"):
            controller.jog_start('X', 80000)

    def test_jog_stop(self, controller):
        """Testa parada de jog"""
        controller.connection_manager.client.write_coil = Mock()
        controller._jog_state['X'] = 'forward'

        controller.jog_stop('X')

        assert controller._jog_state['X'] == 'stopped'
        # Deve desligar ambos os coils (jog_plus e jog_minus)
        assert controller.connection_manager.client.write_coil.call_count == 2

    def test_jog_stop_lowercase_axis(self, controller):
        """Testa parada de jog com eixo minúsculo"""
        controller.connection_manager.client.write_coil = Mock()
        controller._jog_state['Y'] = 'forward'

        controller.jog_stop('y')

        assert controller._jog_state['Y'] == 'stopped'

    def test_jog_stop_disconnected(self, controller):
        """Testa parada de jog quando desconectado (não deve raise)"""
        controller.connection_manager.is_connected.return_value = False
        controller.connection_manager.client.write_coil = Mock()
        controller._jog_state['X'] = 'forward'

        # Não deve raise, apenas log warning
        controller.jog_stop('X')

        # Estado não deve mudar
        assert controller._jog_state['X'] == 'forward'

    def test_is_jogging_true(self, controller):
        """Testa verificação se está em jog (retorna True)"""
        controller._jog_state['X'] = 'forward'

        result = controller.is_jogging('X')

        assert result == True

    def test_is_jogging_false(self, controller):
        """Testa verificação se está em jog (retorna False)"""
        controller._jog_state['Y'] = 'stopped'

        result = controller.is_jogging('Y')

        assert result == False

    def test_is_jogging_invalid_axis(self, controller):
        """Testa is_jogging com eixo inválido"""
        with pytest.raises(ValueError, match="Eixo inválido"):
            controller.is_jogging('W')

    def test_stop_all_jog(self, controller):
        """Testa parada de todos os eixos"""
        controller.jog_stop = Mock()

        controller.stop_all_jog()

        # Deve chamar jog_stop para cada eixo
        assert controller.jog_stop.call_count == 3

    def test_write_dword(self, controller):
        """Testa escrita de DWORD"""
        controller.connection_manager.client.write_registers = Mock()

        controller._write_dword(21000, 80000)

        controller.connection_manager.client.write_registers.assert_called_once()
        call_args = controller.connection_manager.client.write_registers.call_args
        assert call_args[0][0] == 21000
