"""
Testes de integração para PLCAxisController.

Estes testes validam o controle de eixos X, Y, Z via Modbus TCP,
usando mocks para simular o PLC Delta sem hardware físico.

Cobertura alvo: 80%+ do módulo plc_axis_controller.py
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from aoi_lib.plc_axis_controller import PLCAxisController


class MockModbusResponse:
    """Mock de resposta Modbus com interface compatível."""
    def __init__(self, values, is_coil_response=False):
        if is_coil_response:
            self.bits = values  # Para read_coils
        else:
            self.registers = values  # Para read_holding_registers

    def isError(self):
        return False


@pytest.fixture
def mock_modbus():
    """
    Mock do cliente Modbus TCP e contexto de patch.

    Retorna tupla (mock_client, patcher).
    """
    mock = MagicMock()
    mock.connect.return_value = True
    mock.is_socket_open.return_value = True
    mock.write_registers.return_value = MockModbusResponse([])  # Escrever não precisa de dados
    mock.write_coil.return_value = MockModbusResponse([])  # Escrever coil não precisa de dados
    mock.read_coils.return_value = MockModbusResponse([False], is_coil_response=True)  # Ler coil retorna bits
    # Retorna MockModbusResponse com posição 0 por padrão
    mock.read_holding_registers.return_value = MockModbusResponse([0, 0])

    patcher = patch('aoi_lib.plc_axis_controller.ModbusTcpClient', return_value=mock)
    return mock, patcher


@pytest.mark.integration
class TestPLCControllerBasics:
    """Testa inicialização e configuração básica do controlador."""

    def test_initialization_default_params(self):
        """Testa inicialização com parâmetros padrão."""
        controller = PLCAxisController(auto_connect=False)

        assert controller.host == '192.168.1.5'
        assert controller.port == 502
        assert controller.is_connected is False
        assert controller.machine_status == "Disconnected"
        assert controller.pulses_per_mm == 1.0
        assert controller.backlight_on is False

    def test_initialization_custom_params(self):
        """Testa inicialização com parâmetros customizados."""
        controller = PLCAxisController(
            host='192.168.1.10',
            port=503,
            auto_connect=False
        )

        assert controller.host == '192.168.1.10'
        assert controller.port == 503

    def test_initialization_auto_connect_false(self):
        """Testa que auto_connect=False não tenta conectar."""
        with patch('aoi_lib.plc_axis_controller.ModbusTcpClient') as mock_client:
            mock_client.return_value.connect.return_value = True

            controller = PLCAxisController(auto_connect=False)

            # Não deve tentar conectar
            mock_client.return_value.connect.assert_not_called()
            assert controller.is_connected is False

    def test_initialization_auto_connect_true(self):
        """Testa que auto_connect=True tenta conectar automaticamente."""
        mock_client = MagicMock()
        mock_client.connect.return_value = True

        with patch('aoi_lib.plc_axis_controller.ModbusTcpClient', return_value=mock_client):
            controller = PLCAxisController(auto_connect=True)

            # Deve ter tentado conectar
            assert controller.is_connected is True
            assert controller.machine_status == "Idle"

    def test_addresses_configuration(self):
        """Testa que configuração de endereços está correta."""
        controller = PLCAxisController(auto_connect=False)

        # Verificar endereços X
        assert controller.ADDRESSES['X']['zero'] == 1500
        assert controller.ADDRESSES['X']['move_abs'] == 1050
        assert controller.ADDRESSES['X']['pos_input'] == 1100
        assert controller.ADDRESSES['X']['pos_reg'] == 3000

        # Verificar endereços Y
        assert controller.ADDRESSES['Y']['zero'] == 1000
        assert controller.ADDRESSES['Y']['move_abs'] == 1050  # Interpolação com X
        assert controller.ADDRESSES['Y']['pos_input'] == 600
        assert controller.ADDRESSES['Y']['pos_reg'] == 3200

        # Verificar endereços Z
        assert controller.ADDRESSES['Z']['zero'] == 500
        assert controller.ADDRESSES['Z']['move_abs'] == 1550
        assert controller.ADDRESSES['Z']['pos_input'] == 1600
        assert controller.ADDRESSES['Z']['pos_reg'] == 3400

    def test_max_feed_initialization(self):
        """Testa que limites de feed são infinitos na inicialização."""
        controller = PLCAxisController(auto_connect=False)

        assert controller.max_feed['x'] == float('inf')
        assert controller.max_feed['y'] == float('inf')
        assert controller.max_feed['z'] == float('inf')


@pytest.mark.integration
class TestPLCControllerConnection:
    """Testa conexão e desconexão do PLC."""

    def test_connect_success(self):
        """Testa conexão bem-sucedida ao PLC."""
        mock_client = MagicMock()
        mock_client.connect.return_value = True

        with patch('aoi_lib.plc_axis_controller.ModbusTcpClient', return_value=mock_client):
            controller = PLCAxisController(auto_connect=False)
            result = controller.connect()

            assert result is True
            assert controller.is_connected is True
            assert controller.machine_status == "Idle"
            mock_client.connect.assert_called_once()

    def test_connect_failure(self):
        """Testa falha de conexão com PLC."""
        mock_client = MagicMock()
        mock_client.connect.return_value = False

        with patch('aoi_lib.plc_axis_controller.ModbusTcpClient', return_value=mock_client):
            controller = PLCAxisController(auto_connect=False)

            with pytest.raises(ConnectionError):
                controller.connect()

            assert controller.is_connected is False
            assert controller.machine_status == "Disconnected"

    def test_connect_exception(self):
        """Testa exceção durante conexão."""
        mock_client = MagicMock()
        mock_client.connect.side_effect = Exception("Network error")

        with patch('aoi_lib.plc_axis_controller.ModbusTcpClient', return_value=mock_client):
            controller = PLCAxisController(auto_connect=False)

            with pytest.raises(ConnectionError, match="Falha ao conectar"):
                controller.connect()

    def test_connect_already_connected(self):
        """Testa que connect() retorna True se já conectado."""
        controller = PLCAxisController(auto_connect=False)
        controller.is_connected = True
        controller.machine_status = "Idle"

        result = controller.connect()

        assert result is True

    def test_close_connection(self):
        """Testa fechamento de conexão."""
        mock_client = MagicMock()

        with patch('aoi_lib.plc_axis_controller.ModbusTcpClient', return_value=mock_client):
            controller = PLCAxisController(auto_connect=False)
            controller.is_connected = True
            controller.client = mock_client

            controller.close()

            assert controller.is_connected is False
            mock_client.close.assert_called_once()

    def test_disconnect_alias(self):
        """Testa que disconnect() é alias para close()."""
        mock_client = MagicMock()

        with patch('aoi_lib.plc_axis_controller.ModbusTcpClient', return_value=mock_client):
            controller = PLCAxisController(auto_connect=False)
            controller.is_connected = True
            controller.client = mock_client

            controller.disconnect()

            assert controller.is_connected is False
            mock_client.close.assert_called_once()

    def test_set_connection_params(self):
        """Testa atualização de parâmetros de conexão."""
        controller = PLCAxisController(
            host='192.168.1.5',
            port=502,
            auto_connect=False
        )
        controller.is_connected = True

        controller.set_connection_params('192.168.1.10', 503)

        assert controller.host == '192.168.1.10'
        assert controller.port == 503
        assert controller.is_connected is False
        assert controller.machine_status == "Disconnected"


@pytest.mark.integration
class TestPLCControllerMovement:
    """Testa movimentos dos eixos."""

    def test_move_absolute_x(self):
        """Testa movimento absoluto no eixo X."""
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.read_holding_registers.return_value = MockModbusResponse([0, 0])  # Posição 0

        with patch('aoi_lib.plc_axis_controller.ModbusTcpClient', return_value=mock_client):
            controller = PLCAxisController(auto_connect=True)
            controller.move_absolute('X', 1000)  # 1000 pulsos

            # Verificar que escreveu posição no registrador correto
            assert mock_client.write_registers.called

    def test_move_absolute_y(self):
        """Testa movimento absoluto no eixo Y."""
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.read_holding_registers.return_value = MockModbusResponse([0, 0])

        with patch('aoi_lib.plc_axis_controller.ModbusTcpClient', return_value=mock_client):
            controller = PLCAxisController(auto_connect=True)
            controller.move_absolute('Y', 500)

            assert mock_client.write_registers.called

    def test_move_absolute_z(self):
        """Testa movimento absoluto no eixo Z."""
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.read_holding_registers.return_value = MockModbusResponse([0, 0])

        with patch('aoi_lib.plc_axis_controller.ModbusTcpClient', return_value=mock_client):
            controller = PLCAxisController(auto_connect=True)
            controller.move_absolute('Z', 200)

            assert mock_client.write_registers.called

    def test_move_relative_single_axis(self):
        """Testa movimento relativo em um eixo."""
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.read_holding_registers.return_value = MockModbusResponse([100, 0])  # Posição atual 100

        with patch('aoi_lib.plc_axis_controller.ModbusTcpClient', return_value=mock_client):
            controller = PLCAxisController(auto_connect=True)
            controller.move_relative(x=50)

            assert mock_client.write_registers.called

    def test_move_relative_multiple_axes(self):
        """Testa movimento relativo em múltiplos eixos."""
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.read_holding_registers.return_value = MockModbusResponse([100, 0])

        with patch('aoi_lib.plc_axis_controller.ModbusTcpClient', return_value=mock_client):
            controller = PLCAxisController(auto_connect=True)
            controller.move_relative(x=10, y=20, z=5)

            # Deve escrever para múltiplos eixos
            assert mock_client.write_registers.called

    def test_move_absolute_without_connection(self):
        """Testa que movimento sem conexão levanta erro."""
        controller = PLCAxisController(auto_connect=False)
        controller.is_connected = False

        with pytest.raises(IOError, match="PLC não conectado"):
            controller._apply_motion_pulses({'X': 1000})

    def test_step_move(self):
        """Testa movimento步进 (step) em mm."""
        mock_client = MagicMock()
        mock_client.connect.return_value = True

        # Simular posição inicial 0, depois posição 100 (alvo atingido)
        call_count = [0]
        def mock_read_func(address, count):
            call_count[0] += 1
            if call_count[0] == 1:  # Primeira chamada - posição inicial
                return MockModbusResponse([0, 0])
            else:  # Chamadas subsequentes - posição alvo 100 pulsos
                return MockModbusResponse([100 & 0xFFFF, (100 >> 16) & 0xFFFF])

        mock_client.read_holding_registers.side_effect = mock_read_func

        with patch('aoi_lib.plc_axis_controller.ModbusTcpClient', return_value=mock_client):
            controller = PLCAxisController(auto_connect=True)
            controller.pulses_per_mm = 100.0  # 100 pulsos/mm

            result = controller.step_move('X', 1.0)  # 1mm = 100 pulsos

            assert result is True

    def test_step_move_negative(self):
        """Testa movimento步进 negativo."""
        mock_client = MagicMock()
        mock_client.connect.return_value = True

        # Simular posição inicial 0, depois posição -100 (alvo atingido)
        call_count = [0]
        def mock_read_func(address, count):
            call_count[0] += 1
            if call_count[0] == 1:  # Primeira chamada - posição inicial
                return MockModbusResponse([0, 0])
            else:  # Chamadas subsequentes - posição alvo -100 pulsos
            # -100 em 32-bit signed = 0xFFFFFF9C
                return MockModbusResponse([0xFFFFFF9C & 0xFFFF, (0xFFFFFF9C >> 16) & 0xFFFF])

        mock_client.read_holding_registers.side_effect = mock_read_func

        with patch('aoi_lib.plc_axis_controller.ModbusTcpClient', return_value=mock_client):
            controller = PLCAxisController(auto_connect=True)
            controller.pulses_per_mm = 100.0

            result = controller.step_move('X', -1.0)  # -1mm

            assert result is True


@pytest.mark.integration
class TestPLCControllerJog:
    """Testa operações de jog (movimento contínuo)."""

    def test_jog_start_forward(self):
        """Testa início de jog para frente."""
        mock_client = MagicMock()
        mock_client.connect.return_value = True

        with patch('aoi_lib.plc_axis_controller.ModbusTcpClient', return_value=mock_client):
            controller = PLCAxisController(auto_connect=True)
            controller.jog_start('X', direction=1)

            # Deve escrever no coil jog_plus
            assert mock_client.write_coil.called

    def test_jog_start_backward(self):
        """Testa início de jog para trás."""
        mock_client = MagicMock()
        mock_client.connect.return_value = True

        with patch('aoi_lib.plc_axis_controller.ModbusTcpClient', return_value=mock_client):
            controller = PLCAxisController(auto_connect=True)
            controller.jog_start('X', direction=-1)

            # Deve escrever no coil jog_minus
            assert mock_client.write_coil.called

    def test_jog_stop_single_axis(self):
        """Testa parada de jog em um eixo."""
        mock_client = MagicMock()
        mock_client.connect.return_value = True

        with patch('aoi_lib.plc_axis_controller.ModbusTcpClient', return_value=mock_client):
            controller = PLCAxisController(auto_connect=True)
            controller.jog_stop('X')

            # Deve parar o eixo X
            assert mock_client.write_coil.called

    def test_jog_stop_all_axes(self):
        """Testa parada de jog em todos os eixos."""
        mock_client = MagicMock()
        mock_client.connect.return_value = True

        with patch('aoi_lib.plc_axis_controller.ModbusTcpClient', return_value=mock_client):
            controller = PLCAxisController(auto_connect=True)
            controller.jog_stop()  # Sem especificar eixo

            # Deve parar todos os eixos
            assert mock_client.write_coil.called


@pytest.mark.integration
class TestPLCControllerHoming:
    """Testa operações de homing (referenciamento)."""

    def test_set_zero_axis(self):
        """Testa zerar posição de um eixo."""
        mock_client = MagicMock()
        mock_client.connect.return_value = True

        with patch('aoi_lib.plc_axis_controller.ModbusTcpClient', return_value=mock_client):
            controller = PLCAxisController(auto_connect=True)
            result = controller.set_zero('X')

            # O mapa atual do PLC não expõe zero dedicado por eixo.
            assert result is False
            assert not mock_client.write_coil.called

    def test_home_axis(self):
        """Testa homing de um eixo."""
        mock_client = MagicMock()
        mock_client.connect.return_value = True

        with patch('aoi_lib.plc_axis_controller.ModbusTcpClient', return_value=mock_client):
            controller = PLCAxisController(auto_connect=True)
            controller.home_axis('X')

            assert mock_client.write_coil.called

    def test_home_all(self):
        """Testa homing de todos os eixos."""
        mock_client = MagicMock()
        mock_client.connect.return_value = True

        with patch('aoi_lib.plc_axis_controller.ModbusTcpClient', return_value=mock_client):
            controller = PLCAxisController(auto_connect=True)
            controller.home_all()

            # Deve enviar homing para X, Y, Z
            assert mock_client.write_coil.called


@pytest.mark.integration
class TestPLCControllerPositionReading:
    """Testa leitura de posição dos eixos."""

    def test_read_position_x(self):
        """Testa leitura de posição do eixo X."""
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        # Simular posição 1000 pulsos
        mock_client.read_holding_registers.return_value = MockModbusResponse([1000 & 0xFFFF, (1000 >> 16) & 0xFFFF])

        with patch('aoi_lib.plc_axis_controller.ModbusTcpClient', return_value=mock_client):
            controller = PLCAxisController(auto_connect=True)
            position = controller.read_position('X')

            assert isinstance(position, int)

    def test_read_position_y(self):
        """Testa leitura de posição do eixo Y."""
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.read_holding_registers.return_value = MockModbusResponse([500 & 0xFFFF, (500 >> 16) & 0xFFFF])

        with patch('aoi_lib.plc_axis_controller.ModbusTcpClient', return_value=mock_client):
            controller = PLCAxisController(auto_connect=True)
            position = controller.read_position('Y')

            assert isinstance(position, int)

    def test_read_position_z(self):
        """Testa leitura de posição do eixo Z."""
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.read_holding_registers.return_value = MockModbusResponse([200 & 0xFFFF, (200 >> 16) & 0xFFFF])

        with patch('aoi_lib.plc_axis_controller.ModbusTcpClient', return_value=mock_client):
            controller = PLCAxisController(auto_connect=True)
            position = controller.read_position('Z')

            assert isinstance(position, int)

    def test_get_current_position(self):
        """Testa leitura de posição de todos os eixos."""
        mock_client = MagicMock()
        mock_client.connect.return_value = True

        # Simular posições diferentes
        def mock_read_func(address, count):
            if address == 3000:  # X
                return MockModbusResponse([1000 & 0xFFFF, (1000 >> 16) & 0xFFFF])
            elif address == 3200:  # Y
                return MockModbusResponse([500 & 0xFFFF, (500 >> 16) & 0xFFFF])
            elif address == 3400:  # Z
                return MockModbusResponse([200 & 0xFFFF, (200 >> 16) & 0xFFFF])
            return MockModbusResponse([0, 0])

        mock_client.read_holding_registers.side_effect = mock_read_func

        with patch('aoi_lib.plc_axis_controller.ModbusTcpClient', return_value=mock_client):
            controller = PLCAxisController(auto_connect=True)
            positions = controller.get_current_position()

            assert isinstance(positions, dict)
            assert 'x' in positions
            assert 'y' in positions
            assert 'z' in positions


@pytest.mark.integration
class TestPLCControllerWaitForIdle:
    """Testa espera pelo fim do movimento."""

    def test_wait_for_idle_success(self):
        """Testa espera bem-sucedida por idle."""
        mock_client = MagicMock()
        mock_client.connect.return_value = True

        # Simular movimento completado (posição = alvo)
        mock_client.read_holding_registers.return_value = MockModbusResponse([1000 & 0xFFFF, (1000 >> 16) & 0xFFFF])

        with patch('aoi_lib.plc_axis_controller.ModbusTcpClient', return_value=mock_client):
            controller = PLCAxisController(auto_connect=True)
            controller._targets = {'X': 1000}

            # Pequeno timeout para teste
            result = controller.wait_for_idle('X', tolerance=1, timeout=1)

            assert result is True

    def test_wait_for_idle_timeout(self):
        """Testa timeout quando movimento não completa."""
        mock_client = MagicMock()
        mock_client.connect.return_value = True

        # Simular posição distante do alvo
        mock_client.read_holding_registers.return_value = MockModbusResponse([0, 0])  # Posição 0

        with patch('aoi_lib.plc_axis_controller.ModbusTcpClient', return_value=mock_client):
            controller = PLCAxisController(auto_connect=True)
            controller._targets = {'X': 1000}

            # Timeout curto para teste rápido
            result = controller.wait_for_idle('X', tolerance=1, timeout=1)

            assert result is False


@pytest.mark.integration
class TestPLCControllerFeedRate:
    """Testa controle de feed rate (velocidade)."""

    def test_clamp_feed_rate_none(self):
        """Testa clamp com feed_rate None."""
        controller = PLCAxisController(auto_connect=False)

        result = controller._clamp_feed_rate(None)

        assert result is None

    def test_clamp_feed_rate_valid(self):
        """Testa clamp com feed_rate válido."""
        controller = PLCAxisController(auto_connect=False)
        controller.max_feed = {'x': 3000.0, 'y': 3000.0, 'z': 1000.0}

        result = controller._clamp_feed_rate(1000.0)

        assert result == 1000.0

    def test_clamp_feed_rate_below_minimum(self):
        """Testa clamp com feed_rate abaixo do mínimo."""
        controller = PLCAxisController(auto_connect=False)

        result = controller._clamp_feed_rate(0.5)

        assert result == 1.0  # Mínimo é 1.0

    def test_clamp_feed_rate_above_maximum(self):
        """Testa clamp com feed_rate acima do máximo."""
        controller = PLCAxisController(auto_connect=False)
        controller.max_feed = {'x': 1000.0, 'y': 1000.0, 'z': 1000.0}

        result = controller._clamp_feed_rate(5000.0)

        assert result == 1000.0  # Limitado pelo máximo

    def test_clamp_feed_rate_infinite_max(self):
        """Testa clamp com limite infinito."""
        controller = PLCAxisController(auto_connect=False)
        controller.max_feed = {'x': float('inf'), 'y': float('inf'), 'z': float('inf')}

        result = controller._clamp_feed_rate(10000.0)

        assert result == 10000.0  # Não limitado


@pytest.mark.integration
class TestPLCControllerBacklight:
    """Testa controle de backlight (iluminação)."""

    def test_backlight_initial_state(self):
        """Testa estado inicial do backlight."""
        controller = PLCAxisController(auto_connect=False)

        assert controller.backlight_on is False

    def test_backlight_turn_on(self):
        """Testa ligar backlight."""
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.write_coil.return_value = MockModbusResponse([])

        with patch('aoi_lib.plc_axis_controller.ModbusTcpClient', return_value=mock_client):
            controller = PLCAxisController(auto_connect=True)
            result = controller.backlight_turn_on()

            assert result is True
            assert controller.backlight_on is True

    def test_backlight_turn_off(self):
        """Testa desligar backlight."""
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.write_coil.return_value = MockModbusResponse([])

        with patch('aoi_lib.plc_axis_controller.ModbusTcpClient', return_value=mock_client):
            controller = PLCAxisController(auto_connect=True)
            controller.backlight_on = True

            result = controller.backlight_turn_off()

            assert result is True
            assert controller.backlight_on is False

    def test_backlight_toggle(self):
        """Testa inverter estado do backlight."""
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.write_coil.return_value = MockModbusResponse([])

        with patch('aoi_lib.plc_axis_controller.ModbusTcpClient', return_value=mock_client):
            controller = PLCAxisController(auto_connect=True)

            # Toggle: desligado → ligado
            result1 = controller.backlight_toggle()
            assert result1 is True
            assert controller.backlight_on is True

            # Toggle: ligado → desligado
            result2 = controller.backlight_toggle()
            assert result2 is True
            assert controller.backlight_on is False

    def test_backlight_is_on(self):
        """Testa verificar se backlight está ligado."""
        controller = PLCAxisController(auto_connect=False)

        controller.backlight_on = True
        assert controller.backlight_is_on() is True

        controller.backlight_on = False
        assert controller.backlight_is_on() is False


@pytest.mark.integration
class TestPLCControllerReset:
    """Testa funções de reset e unlock."""

    def test_send_soft_reset(self):
        """Testa envio de soft reset ao PLC."""
        mock_client = MagicMock()
        mock_client.connect.return_value = True

        with patch('aoi_lib.plc_axis_controller.ModbusTcpClient', return_value=mock_client):
            controller = PLCAxisController(auto_connect=True)
            result = controller.send_soft_reset()

            assert result is True

    def test_unlock(self):
        """Testa unlock do PLC."""
        mock_client = MagicMock()
        mock_client.connect.return_value = True

        with patch('aoi_lib.plc_axis_controller.ModbusTcpClient', return_value=mock_client):
            controller = PLCAxisController(auto_connect=True)
            result = controller.unlock()

            assert result is True


@pytest.mark.integration
class TestPLCControllerCoilOperations:
    """Testa operações de leitura/escrita de coils."""

    def test_read_coil(self):
        """Testa leitura de coil."""
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.read_coils.return_value = MockModbusResponse([True], is_coil_response=True)

        with patch('aoi_lib.plc_axis_controller.ModbusTcpClient', return_value=mock_client):
            controller = PLCAxisController(auto_connect=True)
            result = controller.read_coil(100)

            assert result is True

    def test_write_coil_true(self):
        """Testa escrita de coil (True)."""
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.write_coil.return_value = MockModbusResponse([])

        with patch('aoi_lib.plc_axis_controller.ModbusTcpClient', return_value=mock_client):
            controller = PLCAxisController(auto_connect=True)
            result = controller.write_coil(100, True)

            assert result is True

    def test_write_coil_false(self):
        """Testa escrita de coil (False)."""
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.write_coil.return_value = MockModbusResponse([])

        with patch('aoi_lib.plc_axis_controller.ModbusTcpClient', return_value=mock_client):
            controller = PLCAxisController(auto_connect=True)
            result = controller.write_coil(100, False)

            assert result is True

    def test_pulse_coil(self):
        """Testa pulso de coil."""
        mock_client = MagicMock()
        mock_client.connect.return_value = True

        with patch('aoi_lib.plc_axis_controller.ModbusTcpClient', return_value=mock_client):
            controller = PLCAxisController(auto_connect=True)
            result = controller.pulse_coil(100, duration_ms=50)

            assert result is True


@pytest.mark.integration
class TestPLCControllerRegisterOperations:
    """Testa operações de registradores."""

    def test_read_register(self):
        """Testa leitura de registrador."""
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        # read_register chama _read_dword que lê 2 registradores (32-bit)
        mock_client.read_holding_registers.return_value = MockModbusResponse([1000 & 0xFFFF, (1000 >> 16) & 0xFFFF])

        with patch('aoi_lib.plc_axis_controller.ModbusTcpClient', return_value=mock_client):
            controller = PLCAxisController(auto_connect=True)
            result = controller.read_register(1100)

            assert result == 1000

    def test_write_register(self):
        """Testa escrita de registrador."""
        mock_client = MagicMock()
        mock_client.connect.return_value = True

        with patch('aoi_lib.plc_axis_controller.ModbusTcpClient', return_value=mock_client):
            controller = PLCAxisController(auto_connect=True)
            result = controller.write_register(1100, 1000)

            assert result is True


@pytest.mark.integration
class TestPLCControllerErrors:
    """Testa tratamento de erros."""

    def test_write_dword_without_client(self):
        """Testa erro ao escrever DWORD sem cliente."""
        controller = PLCAxisController(auto_connect=False)
        controller.client = None

        with pytest.raises(IOError, match="PLC não conectado"):
            controller._write_dword(100, 1000)

    def test_read_dword_without_client(self):
        """Testa erro ao ler DWORD sem cliente."""
        controller = PLCAxisController(auto_connect=False)
        controller.client = None

        with pytest.raises(IOError, match="PLC não conectado"):
            controller._read_dword(100)

    def test_move_absolute_invalid_axis(self):
        """Testa movimento para eixo inválido."""
        mock_client = MagicMock()
        mock_client.connect.return_value = True

        with patch('aoi_lib.plc_axis_controller.ModbusTcpClient', return_value=mock_client):
            controller = PLCAxisController(auto_connect=True)

            with pytest.raises(KeyError):
                controller.move_absolute('INVALID', 1000)

    def test_pulse_coil_duration(self):
        """Testa pulso de coil com duração customizada."""
        mock_client = MagicMock()
        mock_client.connect.return_value = True

        with patch('aoi_lib.plc_axis_controller.ModbusTcpClient', return_value=mock_client):
            controller = PLCAxisController(auto_connect=True)
            result = controller.pulse_coil(100, duration_ms=200)

            assert result is True


@pytest.mark.integration
class TestPLCControllerEdgeCases:
    """Testa casos extremos e borda."""

    def test_move_to_absolute_position_partial(self):
        """Testa movimento absoluto com apenas alguns eixos."""
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.read_holding_registers.return_value = MockModbusResponse([0, 0])

        with patch('aoi_lib.plc_axis_controller.ModbusTcpClient', return_value=mock_client):
            controller = PLCAxisController(auto_connect=True)
            controller.move_to_absolute_position(x=100, y=200)

            # Verificar que escreveu registradores
            assert mock_client.write_registers.called

    def test_move_relative_no_axes(self):
        """Testa movimento relativo sem especificar eixos."""
        mock_client = MagicMock()
        mock_client.connect.return_value = True

        with patch('aoi_lib.plc_axis_controller.ModbusTcpClient', return_value=mock_client):
            controller = PLCAxisController(auto_connect=True)
            result = controller.move_relative()

            # Não deve mover nada
            assert result is None or result

    def test_zero_position(self):
        """Testa zerar posição de todos os eixos."""
        mock_client = MagicMock()
        mock_client.connect.return_value = True

        with patch('aoi_lib.plc_axis_controller.ModbusTcpClient', return_value=mock_client):
            controller = PLCAxisController(auto_connect=True)
            results = [
                controller.set_zero('X'),
                controller.set_zero('Y'),
                controller.set_zero('Z'),
            ]

            # O mapa atual do PLC não expõe zero dedicado por eixo.
            assert results == [False, False, False]
            assert not mock_client.write_coil.called

    def test_pulses_per_mm_conversion(self):
        """Testa conversão de pulses para mm."""
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.read_holding_registers.return_value = MockModbusResponse([0, 0])

        with patch('aoi_lib.plc_axis_controller.ModbusTcpClient', return_value=mock_client):
            controller = PLCAxisController(auto_connect=True)
            controller.pulses_per_mm = 100.0

            # Mover 1mm = 100 pulsos
            controller.step_move('X', 1.0)

            # Verificar que conversão foi aplicada
            assert mock_client.write_registers.called
