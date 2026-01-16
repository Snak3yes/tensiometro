"""
Testes unitários para PLCPositionReaderController

Testa leitura de posição de eixos PLC.
"""

import pytest
from unittest.mock import Mock
from aoi_lib.plc.controllers.plc_position_reader_controller import PLCPositionReaderController


class TestPLCPositionReaderController:
    """Testes para PLCPositionReaderController"""

    @pytest.fixture
    def connection_manager(self):
        """Fixture para connection manager mockado"""
        manager = Mock()
        manager.is_connected.return_value = True
        manager.client = Mock()
        return manager

    @pytest.fixture
    def controller(self, connection_manager):
        """Fixture para controller"""
        return PLCPositionReaderController(
            connection_manager=connection_manager,
            pulses_per_mm=80.0
        )

    def test_init(self, connection_manager):
        """Testa inicialização"""
        controller = PLCPositionReaderController(
            connection_manager=connection_manager,
            pulses_per_mm=80.0
        )

        assert controller.connection_manager == connection_manager
        assert controller.pulses_per_mm == 80.0

    def test_get_current_position_all_axes(self, controller):
        """Testa leitura de posição de todos os eixos"""
        # Mock _read_dword para retornar valores diferentes
        def mock_read_dword(address):
            if address == 3000:  # X
                return 4000
            elif address == 3200:  # Y
                return 3200
            elif address == 3400:  # Z
                return 800
            return 0

        controller._read_dword = Mock(side_effect=mock_read_dword)

        result = controller.get_current_position()

        assert result['X'] == 4000
        assert result['Y'] == 3200
        assert result['Z'] == 800

    def test_get_current_position_disconnected(self, controller):
        """Testa get_current_position quando desconectado"""
        controller.connection_manager.is_connected.return_value = False

        with pytest.raises(IOError, match="PLC não conectado"):
            controller.get_current_position()

    def test_get_current_position_with_error(self, controller):
        """Testa get_current_position com erro em um eixo"""
        def mock_read_dword(address):
            if address == 3000:  # X - erro
                raise Exception("Erro Modbus")
            elif address == 3200:  # Y - OK
                return 3200
            elif address == 3400:  # Z - OK
                return 800
            return 0

        controller._read_dword = Mock(side_effect=mock_read_dword)

        result = controller.get_current_position()

        # X deve ser 0.0 (erro), Y e Z devem ter valores
        assert result['X'] == 0.0
        assert result['Y'] == 3200
        assert result['Z'] == 800

    def test_read_position_x(self, controller):
        """Testa leitura de posição do eixo X"""
        controller._read_dword = Mock(return_value=4000)

        result = controller.read_position('X')

        assert result == 4000
        controller._read_dword.assert_called_once_with(
            controller.ADDRESSES['X']['pos_reg']
        )

    def test_read_position_y(self, controller):
        """Testa leitura de posição do eixo Y"""
        controller._read_dword = Mock(return_value=3200)

        result = controller.read_position('Y')

        assert result == 3200

    def test_read_position_z(self, controller):
        """Testa leitura de posição do eixo Z"""
        controller._read_dword = Mock(return_value=800)

        result = controller.read_position('Z')

        assert result == 800

    def test_read_position_lowercase(self, controller):
        """Testa read_position com eixo minúsculo"""
        controller._read_dword = Mock(return_value=4000)

        result = controller.read_position('x')

        assert result == 4000

    def test_read_position_invalid_axis(self, controller):
        """Testa read_position com eixo inválido"""
        with pytest.raises(ValueError, match="Eixo inválido"):
            controller.read_position('W')

    def test_read_position_disconnected(self, controller):
        """Testa read_position quando desconectado"""
        controller.connection_manager.is_connected.return_value = False

        with pytest.raises(IOError, match="PLC não conectado"):
            controller.read_position('X')

    def test_read_register(self, controller):
        """Testa leitura de registro Modbus"""
        controller._read_dword = Mock(return_value=12345)

        result = controller.read_register(5000)

        assert result == 12345
        controller._read_dword.assert_called_once_with(5000)

    def test_read_register_disconnected(self, controller):
        """Testa read_register quando desconectado"""
        controller.connection_manager.is_connected.return_value = False

        with pytest.raises(IOError, match="PLC não conectado"):
            controller.read_register(5000)

    def test_get_xyz_position(self, controller):
        """Testa obtenção de posição XYZ como tupla"""
        controller.get_current_position = Mock(
            return_value={'X': 4000, 'Y': 3200, 'Z': 800}
        )

        result = controller.get_xyz_position()

        assert result == (4000, 3200, 800)

    def test_get_xyz_position_with_defaults(self, controller):
        """Testa get_xyz_position com valores padrão"""
        controller.get_current_position = Mock(
            return_value={'X': 0, 'Y': 0}
        )

        result = controller.get_xyz_position()

        # Z deve ser 0.0 (valor padrão)
        assert result == (0, 0, 0.0)

    def test_get_current_position_mm(self, controller):
        """Testa obtenção de posição em milímetros"""
        controller.get_current_position = Mock(
            return_value={'X': 4000, 'Y': 3200, 'Z': 800}
        )

        result = controller.get_current_position_mm()

        # 4000 pulsos / 80 pulsos/mm = 50 mm
        # 3200 pulsos / 80 pulsos/mm = 40 mm
        # 800 pulsos / 80 pulsos/mm = 10 mm
        assert result['x'] == 50.0
        assert result['y'] == 40.0
        assert result['z'] == 10.0

    def test_get_current_position_mm_disconnected(self, controller):
        """Testa get_current_position_mm quando desconectado"""
        controller.connection_manager.is_connected.return_value = False

        with pytest.raises(IOError, match="PLC não conectado"):
            controller.get_current_position_mm()

    def test_read_dword_success(self, controller):
        """Testa leitura de DWORD com sucesso"""
        mock_response = Mock()
        mock_response.isError.return_value = False
        mock_response.registers = [0x0FA0, 0x0000]  # 4000

        controller.connection_manager.client.read_holding_registers = Mock(
            return_value=mock_response
        )

        result = controller._read_dword(3000)

        assert result == 4000

    def test_read_dword_error(self, controller):
        """Testa leitura de DWORD com erro"""
        mock_response = Mock()
        mock_response.isError.return_value = True

        controller.connection_manager.client.read_holding_registers = Mock(
            return_value=mock_response
        )

        with pytest.raises(IOError, match="Falha na leitura DWORD"):
            controller._read_dword(3000)
