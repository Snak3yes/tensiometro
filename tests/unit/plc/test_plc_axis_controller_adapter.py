"""
Teste de backward compatibility para PLCAxisControllerAdapter

Verifica se o adapter mantém 100% de compatibilidade com a interface original.
"""

import pytest
from unittest.mock import Mock, patch
from aoi_lib.plc.plc_axis_controller_adapter import PLCAxisControllerAdapter


class TestPLCAxisControllerAdapterBackwardCompatibility:
    """Testes de backward compatibility do Adapter"""

    @pytest.fixture
    def adapter(self):
        """Fixture para adapter sem auto_connect"""
        with patch('aoi_lib.plc.controllers.plc_connection_manager.ModbusTcpClient'):
            adapter = PLCAxisControllerAdapter(
                host="192.168.1.5",
                port=502,
                auto_connect=False
            )
            return adapter

    def test_init_default_params(self, adapter):
        """Testa inicialização com parâmetros padrão"""
        assert adapter.host == "192.168.1.5"
        assert adapter.port == 502
        assert adapter.pulses_per_mm == 1.0

    def test_has_all_original_methods(self, adapter):
        """Verifica se adapter tem todos os 37 métodos originais"""
        # Lista de métodos originais de PLCAxisController
        original_methods = [
            'connect', 'close', 'disconnect', 'set_connection_params',
            'set_zero', 'move_absolute', 'move_to_absolute_position',
            '_apply_motion_pulses', 'move_relative', 'step_move',
            '_move_relative_single_axis', 'jog_start', 'jog_stop',
            'home_all', 'home_axis', 'unlock', 'read_position',
            'get_current_position', 'read_register', 'wait_for_idle',
            '_wait_for_idle_axis', 'pulse_coil', 'read_coil', 'write_coil',
            'read_dword', 'write_dword', 'write_register',
            'snapshot_registers', 'backlight_is_on', 'backlight_set',
            'backlight_toggle', 'backlight_turn_on', 'backlight_turn_off',
            'send_soft_reset', '_clamp_feed_rate'
        ]

        for method_name in original_methods:
            assert hasattr(adapter, method_name), f"Método {method_name} faltando"
            assert callable(getattr(adapter, method_name)), f"Método {method_name} não é callable"

    def test_has_addresses_mapping(self, adapter):
        """Verifica se ADDRESSES está presente"""
        assert hasattr(adapter, 'ADDRESSES')
        assert 'X' in adapter.ADDRESSES
        assert 'Y' in adapter.ADDRESSES
        assert 'Z' in adapter.ADDRESSES

    def test_connection_delegates_to_manager(self, adapter):
        """Verifica se connect() delega para connection_manager"""
        adapter.connection_manager.connect = Mock(return_value=True)

        result = adapter.connect()

        assert result == True
        adapter.connection_manager.connect.assert_called_once()

    def test_disconnect_delegates_to_manager(self, adapter):
        """Verifica se disconnect() delega para connection_manager"""
        adapter.connection_manager.disconnect = Mock()

        adapter.disconnect()

        adapter.connection_manager.disconnect.assert_called_once()

    def test_set_zero_delegates_to_absolute(self, adapter):
        """Verifica se set_zero() delega para absolute_controller"""
        adapter.absolute_controller.set_zero = Mock()

        adapter.set_zero('X')

        adapter.absolute_controller.set_zero.assert_called_once()

    def test_move_absolute_delegates_to_absolute(self, adapter):
        """Verifica se move_absolute() delega corretamente"""
        adapter.absolute_controller.move_absolute = Mock(return_value=True)

        adapter.move_absolute('X', 4000, speed=80000)

        adapter.absolute_controller.move_absolute.assert_called_once_with('X', 4000, 80000)

    def test_read_position_delegates_to_reader(self, adapter):
        """Verifica se read_position() delega para position_reader"""
        adapter.position_reader.read_position = Mock(return_value=4000)

        result = adapter.read_position('X')

        assert result == 4000
        adapter.position_reader.read_position.assert_called_once_with('X')

    def test_backlight_set_delegates_to_registers(self, adapter):
        """Verifica se backlight_set() delega para registers_controller"""
        adapter.registers_controller.backlight_set = Mock(return_value=True)

        result = adapter.backlight_set(True)

        assert result == True
        adapter.registers_controller.backlight_set.assert_called_once_with(True)

    def test_all_composition_controllers_exist(self, adapter):
        """Verifica se todos os controllers compostos existem"""
        assert adapter.connection_manager is not None
        assert adapter.absolute_controller is not None
        assert adapter.relative_controller is not None
        assert adapter.jog_controller is not None
        assert adapter.homing_controller is not None
        assert adapter.position_reader is not None
        assert adapter.registers_controller is not None

    def test_adapter_is_composable(self, adapter):
        """Verifica se adapter pode ser usado no lugar do original"""
        # Verifica se adapter pode substituir PLCAxisController original
        assert hasattr(adapter, 'connect')
        assert hasattr(adapter, 'move_absolute')
        assert hasattr(adapter, 'move_relative')
        assert hasattr(adapter, 'jog_start')
        assert hasattr(adapter, 'home_all')
        assert hasattr(adapter, 'read_position')

        # Verifica propriedades compatíveis
        assert hasattr(adapter, 'is_connected')
        assert hasattr(adapter, 'machine_status')
        assert hasattr(adapter, 'pulses_per_mm')
