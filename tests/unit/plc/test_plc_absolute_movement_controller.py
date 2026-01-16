"""
Testes unitários para PLCAbsoluteMovementController

Testa movimento absoluto de eixos PLC.
"""

import pytest
from unittest.mock import Mock, MagicMock
from aoi_lib.plc.controllers.plc_absolute_movement_controller import PLCAbsoluteMovementController


class TestPLCAbsoluteMovementController:
    """Testes para PLCAbsoluteMovementController"""

    @pytest.fixture
    def connection_manager(self):
        """Fixture para connection manager mockado"""
        manager = Mock()
        manager.is_connected.return_value = True
        manager.client = Mock()
        return manager

    @pytest.fixture
    def controller(self, connection_manager):
        """Fixture para controller com parâmetros padrão"""
        return PLCAbsoluteMovementController(
            connection_manager=connection_manager,
            pulses_per_mm=80.0,
            max_feed={'x': 3000.0, 'y': 3000.0, 'z': 1000.0}
        )

    def test_init_default_params(self, connection_manager):
        """Testa inicialização com parâmetros padrão"""
        controller = PLCAbsoluteMovementController(connection_manager)

        assert controller.connection_manager == connection_manager
        assert controller.pulses_per_mm == 1.0
        assert controller._targets == {}

    def test_init_custom_params(self, connection_manager):
        """Testa inicialização com parâmetros customizados"""
        max_feed = {'x': 3000.0, 'y': 3000.0, 'z': 1000.0}
        controller = PLCAbsoluteMovementController(
            connection_manager=connection_manager,
            pulses_per_mm=80.0,
            max_feed=max_feed
        )

        assert controller.pulses_per_mm == 80.0
        assert controller.max_feed == max_feed

    def test_clamp_feed_rate_none(self, controller):
        """Testa _clamp_feed_rate com None"""
        result = controller._clamp_feed_rate(None)
        assert result is None

    def test_clamp_feed_rate_valid(self, controller):
        """Testa _clamp_feed_rate com valor válido"""
        result = controller._clamp_feed_rate(1000.0)
        assert result == 1000.0

    def test_clamp_feed_rate_below_minimum(self, controller):
        """Testa _clamp_feed_rate com valor abaixo do mínimo"""
        result = controller._clamp_feed_rate(0.5)
        assert result == 1.0

    def test_clamp_feed_rate_above_maximum(self, controller):
        """Testa _clamp_feed_rate com valor acima do máximo"""
        result = controller._clamp_feed_rate(5000.0)
        assert result == 1000.0  # min(max_feed) = 1000.0

    def test_apply_motion_pulses_empty(self, controller):
        """Testa apply_motion_pulses com dicionário vazio"""
        result = controller.apply_motion_pulses({})
        assert result == True

    def test_apply_motion_pulses_disconnected(self, controller):
        """Testa apply_motion_pulses quando desconectado"""
        controller.connection_manager.is_connected.return_value = False

        with pytest.raises(IOError, match="PLC não conectado"):
            controller.apply_motion_pulses({'X': 1000})

    def test_apply_motion_pulses_single_axis(self, controller):
        """Testa apply_motion_pulses para eixo único"""
        # Mock dos métodos de escrita
        controller._write_dword = Mock()
        controller._pulse_coil = Mock()

        result = controller.apply_motion_pulses({'X': 4000}, feed_rate=1000.0)

        assert result == True
        assert controller._targets['X'] == 4000
        # Verifica se _write_dword foi chamado para pos_input e speed
        assert controller._write_dword.call_count >= 1
        # Verifica se _pulse_coil foi chamado
        controller._pulse_coil.assert_called_once()

    def test_apply_motion_pulses_multiple_axes(self, controller):
        """Testa apply_motion_pulses para múltiplos eixos"""
        controller._write_dword = Mock()
        controller._pulse_coil = Mock()

        result = controller.apply_motion_pulses(
            {'X': 4000, 'Y': 3200},
            feed_rate=800.0
        )

        assert result == True
        assert controller._targets['X'] == 4000
        assert controller._targets['Y'] == 3200
        # X e Y compartilham o mesmo coil M1050, então _pulse_coil deve ser chamado 1 vez
        controller._pulse_coil.assert_called_once()

    def test_move_absolute(self, controller):
        """Testa movimento absoluto de eixo único"""
        controller.apply_motion_pulses = Mock(return_value=True)

        result = controller.move_absolute('X', 4000, speed=80000)

        assert result == True
        controller.apply_motion_pulses.assert_called_once_with(
            {'X': 4000},
            1000.0  # 80000 / 80.0 = 1000 mm/min
        )

    def test_move_to_absolute_position_single_axis(self, controller):
        """Testa movimento para posição XYZ com apenas um eixo"""
        controller.apply_motion_pulses = Mock(return_value=True)

        result = controller.move_to_absolute_position(x=4000, y=None, z=None)

        assert result == True
        controller.apply_motion_pulses.assert_called_once()

    def test_move_to_absolute_position_all_axes(self, controller):
        """Testa movimento para posição XYZ com todos os eixos"""
        controller.apply_motion_pulses = Mock(return_value=True)

        result = controller.move_to_absolute_position(
            x=4000,
            y=3200,
            z=800,
            speed_x=80000,
            speed_y=64000,
            speed_z=40000
        )

        assert result == True
        # Usa a maior velocidade (80000)
        call_args = controller.apply_motion_pulses.call_args
        assert call_args[0][0] == {'X': 4000, 'Y': 3200, 'Z': 800}

    def test_set_zero(self, controller):
        """Testa definição de zero da máquina"""
        controller._pulse_coil = Mock()

        controller.set_zero()

        # Deve pulsar coil de zero para todos os eixos
        assert controller._pulse_coil.call_count == 3

    def test_set_feed_rate(self, controller):
        """Testa configuração de feed rate padrão"""
        controller.set_feed_rate(120000.0)

        assert controller._default_feed_rate == 120000.0

    def test_get_targets(self, controller):
        """Testa obtenção de alvos ativos"""
        controller._targets = {'X': 4000, 'Y': 3200}

        targets = controller.get_targets()

        assert targets == {'X': 4000, 'Y': 3200}
        # Retorna cópia, não referência
        assert targets is not controller._targets

    def test_write_dword(self, controller):
        """Testa escrita de DWORD em dois registradores"""
        controller.connection_manager.client.write_registers = Mock()

        controller._write_dword(1100, 4000)

        # Verifica se write_registers foi chamado com [lo, hi]
        # 4000 = 0x0FA0 → lo=0x0FA0, hi=0x0000
        controller.connection_manager.client.write_registers.assert_called_once()
        call_args = controller.connection_manager.client.write_registers.call_args
        assert call_args[0][0] == 1100
        assert call_args[0][1] == [0x0FA0, 0x0000]

    def test_read_dword(self, controller):
        """Testa leitura de DWORD de dois registradores"""
        mock_response = Mock()
        mock_response.isError.return_value = False
        mock_response.registers = [0x0FA0, 0x0000]  # 4000

        controller.connection_manager.client.read_holding_registers = Mock(
            return_value=mock_response
        )

        result = controller._read_dword(3000)

        assert result == 4000
        controller.connection_manager.client.read_holding_registers.assert_called_once_with(
            3000, count=2
        )

    def test_read_dword_signed_negative(self, controller):
        """Testa leitura de DWORD com valor negativo (signed)"""
        mock_response = Mock()
        mock_response.isError.return_value = False
        mock_response.registers = [0x0000, 0xFFFF]  # -1 em complemento de 2

        controller.connection_manager.client.read_holding_registers = Mock(
            return_value=mock_response
        )

        result = controller._read_dword(3000)

        assert result == -1
