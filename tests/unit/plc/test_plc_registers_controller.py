"""
Testes unitários para PLCRegistersController

Testa operações de registradores Modbus e controle de backlight.
"""

import pytest
import time
from unittest.mock import Mock, patch
from aoi_lib.plc.controllers.plc_registers_controller import PLCRegistersController


class TestPLCRegistersController:
    """Testes para PLCRegistersController"""

    @pytest.fixture
    def connection_manager(self):
        """Fixture para connection manager mockado"""
        manager = Mock()
        manager.is_connected.return_value = True
        manager.client = Mock()
        return manager

    @pytest.fixture
    def position_reader(self):
        """Fixture para position reader mockado"""
        reader = Mock()
        return reader

    @pytest.fixture
    def controller(self, connection_manager, position_reader):
        """Fixture para controller"""
        return PLCRegistersController(
            connection_manager=connection_manager,
            position_reader=position_reader,
            pulses_per_mm=80.0
        )

    def test_init(self, connection_manager, position_reader):
        """Testa inicialização"""
        controller = PLCRegistersController(
            connection_manager=connection_manager,
            position_reader=position_reader,
            pulses_per_mm=80.0
        )

        assert controller.connection_manager == connection_manager
        assert controller.position_reader == position_reader
        assert controller.pulses_per_mm == 80.0
        assert controller.backlight_on == False
        assert controller.backlight_coil_address == 1

    def test_pulse_coil_success(self, controller):
        """Testa pulso de coil com sucesso"""
        controller.connection_manager.client.write_coil = Mock()

        with patch('time.sleep'):
            result = controller.pulse_coil(1050, 100)

        assert result == True
        # Deve ligar e desligar o coil
        assert controller.connection_manager.client.write_coil.call_count == 2

    def test_pulse_coil_disconnected(self, controller):
        """Testa pulso de coil quando desconectado"""
        controller.connection_manager.is_connected.return_value = False

        with pytest.raises(IOError, match="PLC não conectado"):
            controller.pulse_coil(1050)

    def test_read_coil_true(self, controller):
        """Testa leitura de coil com valor True"""
        mock_response = Mock()
        mock_response.bits = [True]
        mock_response.isError.return_value = False

        controller.connection_manager.client.read_coils = Mock(
            return_value=mock_response
        )

        result = controller.read_coil(1050)

        assert result == True

    def test_read_coil_false(self, controller):
        """Testa leitura de coil com valor False"""
        mock_response = Mock()
        mock_response.bits = [False]
        mock_response.isError.return_value = False

        controller.connection_manager.client.read_coils = Mock(
            return_value=mock_response
        )

        result = controller.read_coil(1050)

        assert result == False

    def test_read_coil_disconnected(self, controller):
        """Testa leitura de coil quando desconectado"""
        controller.connection_manager.is_connected.return_value = False

        with pytest.raises(IOError, match="PLC não conectado"):
            controller.read_coil(1050)

    def test_write_coil_true(self, controller):
        """Testa escrita de coil com valor True"""
        mock_response = Mock()
        mock_response.isError.return_value = False

        controller.connection_manager.client.write_coil = Mock(
            return_value=mock_response
        )

        result = controller.write_coil(1050, True)

        assert result == True

    def test_write_coil_false(self, controller):
        """Testa escrita de coil com valor False"""
        mock_response = Mock()
        mock_response.isError.return_value = False

        controller.connection_manager.client.write_coil = Mock(
            return_value=mock_response
        )

        result = controller.write_coil(1050, False)

        assert result == True

    def test_write_dword_success(self, controller):
        """Testa escrita de DWORD com sucesso"""
        controller._write_dword = Mock()

        result = controller.write_dword(1100, 4000)

        assert result == True
        controller._write_dword.assert_called_once_with(1100, 4000)

    def test_write_dword_disconnected(self, controller):
        """Testa escrita de DWORD quando desconectado"""
        controller.connection_manager.is_connected.return_value = False

        result = controller.write_dword(1100, 4000)

        assert result == False

    def test_write_dword_error(self, controller):
        """Testa escrita de DWORD com erro"""
        controller._write_dword = Mock(side_effect=Exception("Erro"))

        result = controller.write_dword(1100, 4000)

        assert result == False

    def test_read_dword_success(self, controller):
        """Testa leitura de DWORD com sucesso"""
        controller._read_dword = Mock(return_value=4000)

        result = controller.read_dword(3000)

        assert result == 4000
        controller._read_dword.assert_called_once_with(3000)

    def test_read_dword_disconnected(self, controller):
        """Testa leitura de DWORD quando desconectado"""
        controller.connection_manager.is_connected.return_value = False

        with pytest.raises(IOError, match="PLC não conectado"):
            controller.read_dword(3000)

    def test_write_register_alias(self, controller):
        """Testa write_register como alias para write_dword"""
        controller.write_dword = Mock(return_value=True)

        result = controller.write_register(1100, 4000)

        assert result == True
        controller.write_dword.assert_called_once_with(1100, 4000)

    def test_read_register_alias(self, controller):
        """Testa read_register como alias para read_dword"""
        controller.read_dword = Mock(return_value=4000)

        result = controller.read_register(3000)

        assert result == 4000
        controller.read_dword.assert_called_once_with(3000)

    def test_snapshot_registers(self, controller):
        """Testa snapshot de todos os registradores"""
        # Mock dos métodos de leitura
        controller._read_dword = Mock(return_value=1000)
        controller.read_coil = Mock(return_value=True)

        result = controller.snapshot_registers()

        assert 'pulses_per_mm' in result
        assert 'backlight_on' in result
        assert 'axes' in result
        assert 'X' in result['axes']
        assert 'Y' in result['axes']
        assert 'Z' in result['axes']

    def test_snapshot_registers_disconnected(self, controller):
        """Testa snapshot quando desconectado"""
        controller.connection_manager.is_connected.return_value = False

        with pytest.raises(IOError, match="PLC não conectado"):
            controller.snapshot_registers()

    def test_backlight_set_on(self, controller):
        """Testa ligar backlight"""
        mock_response = Mock()
        mock_response.isError.return_value = False

        controller.connection_manager.client.write_coil = Mock(
            return_value=mock_response
        )

        result = controller.backlight_set(True)

        assert result == True
        assert controller.backlight_on == True
        controller.connection_manager.client.write_coil.assert_called_once_with(
            controller.backlight_coil_address, True
        )

    def test_backlight_set_off(self, controller):
        """Testa desligar backlight"""
        mock_response = Mock()
        mock_response.isError.return_value = False

        controller.connection_manager.client.write_coil = Mock(
            return_value=mock_response
        )

        result = controller.backlight_set(False)

        assert result == True
        assert controller.backlight_on == False

    def test_backlight_set_disconnected(self, controller):
        """Testa backlight_set quando desconectado"""
        controller.connection_manager.is_connected.return_value = False

        result = controller.backlight_set(True)

        assert result == False

    def test_backlight_set_error(self, controller):
        """Testa backlight_set com erro no PLC"""
        mock_response = Mock()
        mock_response.isError.return_value = True

        controller.connection_manager.client.write_coil = Mock(
            return_value=mock_response
        )

        result = controller.backlight_set(True)

        assert result == False

    def test_backlight_turn_on(self, controller):
        """Testa método backlight_turn_on"""
        controller.backlight_set = Mock(return_value=True)

        result = controller.backlight_turn_on()

        assert result == True
        controller.backlight_set.assert_called_once_with(True)

    def test_backlight_turn_off(self, controller):
        """Testa método backlight_turn_off"""
        controller.backlight_set = Mock(return_value=True)

        result = controller.backlight_turn_off()

        assert result == True
        controller.backlight_set.assert_called_once_with(False)

    def test_backlight_toggle_off_to_on(self, controller):
        """Testa toggle de desligado para ligado"""
        controller.backlight_on = False
        controller.backlight_set = Mock(return_value=True)

        result = controller.backlight_toggle()

        assert result == True
        controller.backlight_set.assert_called_once_with(True)

    def test_backlight_toggle_on_to_off(self, controller):
        """Testa toggle de ligado para desligado"""
        controller.backlight_on = True
        controller.backlight_set = Mock(return_value=True)

        result = controller.backlight_toggle()

        assert result == True
        controller.backlight_set.assert_called_once_with(False)

    def test_backlight_is_on(self, controller):
        """Testa verificação se backlight está ligado"""
        controller.backlight_on = True

        result = controller.backlight_is_on()

        assert result == True

    def test_backlight_is_off(self, controller):
        """Testa verificação se backlight está desligado"""
        controller.backlight_on = False

        result = controller.backlight_is_on()

        assert result == False

    def test_write_dword_internal(self, controller):
        """Testa escrita interna de DWORD"""
        controller.connection_manager.client.write_registers = Mock()

        controller._write_dword(1100, 4000)

        # Verifica conversão correta: 4000 = 0x0FA0
        call_args = controller.connection_manager.client.write_registers.call_args
        assert call_args[0][0] == 1100
        assert call_args[0][1] == [0x0FA0, 0x0000]

    def test_read_dword_internal(self, controller):
        """Testa leitura interna de DWORD"""
        mock_response = Mock()
        mock_response.isError.return_value = False
        mock_response.registers = [0x0FA0, 0x0000]  # 4000

        controller.connection_manager.client.read_holding_registers = Mock(
            return_value=mock_response
        )

        result = controller._read_dword(3000)

        assert result == 4000
