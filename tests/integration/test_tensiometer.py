"""
Testes de integração para TensiometerSerialManager.

Estes testes validam a comunicação serial com o tensiômetro AS-120N,
usando mocks para simular o hardware sem necessidade de conexão física.

Cobertura alvo: 85%+ do módulo stencil_tension.py
"""

import pytest
import serial
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from aoi_lib.tensiometer import TensiometerSerialManager


class MockSerialResponse:
    """Mock para resposta serial do tensiômetro AS-120N.

    Simula o protocolo de 9 bytes:
    Byte 0: 0x10 (header)
    Byte 1: 0x19 (comando)
    Byte 2: 0x19 (cmd echo)
    Byte 3: flags + casas decimais
    Byte 4-5: unidade (0x04=kg/cm², 0x05=N/cm², 0x06=lb/cm²)
    Byte 6-8: dígitos BCD (d3, d2, d1)
    """

    @staticmethod
    def create_frame(value: float, unit: int = 0x05) -> bytes:
        """
        Cria um frame de 9 bytes válido para o AS-120N.

        Args:
            value: Valor da tensão (ex: 2.34)
            unit: Código da unidade (0x05=N/cm², 0x04=kg/cm², 0x06=lb/cm²)

        Returns:
            Frame de 9 bytes em formato bytes
        """
        # Converte valor para string
        value_str = f"{value:.2f}"
        parts = value_str.split('.')
        integer_part = int(parts[0])
        decimal_part = int(parts[1]) if len(parts) > 1 else 0

        # Extrai dígitos
        # raw = d3*100 + d2*10 + d1, onde raw = valor * 100
        # Para 5.67: raw = 567, então d1=7, d2=6, d3=5
        raw = int(round(value * 100))  # Converte para centésimos
        d1 = raw % 10
        d2 = (raw // 10) % 10
        d3 = (raw // 100) % 10

        # Calcula casas decimais (sempre 2 para nosso formato)
        casas = 2

        # Byte 3: flags + casas (bits 4-6 = casas, bit 7 = sign)
        byte3 = (casas << 4) & 0x70

        # Codifica dígitos em BCD com offset de 0x0A (nibble baixo)
        # Formato: byte = 0xA0 + dígito (não OR!)
        # Exemplo: dígito 7 → 0xA7, dígito 0 → 0xA0
        bcd_d1 = 0xA0 + d1
        bcd_d2 = 0xA0 + d2
        bcd_d3 = 0xA0 + d3

        # Monta frame
        frame = bytes([
            0x10,           # Byte 0: Header
            0x19,           # Byte 1: Command
            0x19,           # Byte 2: Cmd echo
            byte3,          # Byte 3: Flags + casas
            unit,           # Byte 4: Unidade (MSB)
            0x00,           # Byte 5: Unidade (LSB)
            bcd_d3,         # Byte 6: Dígito 3
            bcd_d2,         # Byte 7: Dígito 2
            bcd_d1          # Byte 8: Dígito 1
        ])

        return frame

    @staticmethod
    def create_invalid_frame() -> bytes:
        """Cria um frame inválido (header errado)."""
        return bytes([0xFF, 0x19, 0x19, 0x20, 0x05, 0x00, 0xBA, 0xBA, 0xBA])

    @staticmethod
    def create_incomplete_frame() -> bytes:
        """Cria um frame incompleto (menos de 9 bytes)."""
        return bytes([0x10, 0x19, 0x19, 0x20, 0x05])


@pytest.fixture
def mock_serial():
    """
    Mock da conexão serial e contexto de patch.

    Retorna tupla (mock_serial, patcher).
    """
    mock = MagicMock()
    mock.is_open = False
    mock.port = None
    mock.baudrate = 2400

    # Configura propriedades da porta serial
    type(mock).dtr = PropertyMock(return_value=False)
    type(mock).rts = PropertyMock(return_value=False)

    # Por padrão, retorna uma resposta válida
    mock.read.return_value = MockSerialResponse.create_frame(12.34)
    mock.write.return_value = None
    mock.flush.return_value = None
    mock.reset_input_buffer.return_value = None
    mock.close.return_value = None

    patcher = patch('serial.Serial', return_value=mock)
    return mock, patcher


@pytest.fixture
def mock_list_ports():
    """Mock para serial.tools.list_ports."""
    with patch('serial.tools.list_ports.comports') as mock_ports:
        # Simula 3 portas disponíveis
        port1 = MagicMock(device='/dev/ttyUSB0', description='USB-Serial')
        port2 = MagicMock(device='/dev/ttyUSB1', description='USB-Serial')
        port3 = MagicMock(device='COM3', description='COM Port')

        # Configura mock para retornar lista quando chamado
        mock_ports.return_value = [port1, port2, port3]

        yield mock_ports


@pytest.mark.integration
class TestTensiometerBasics:
    """Testa inicialização e configuração básica do tensiômetro."""

    def test_initialization_default_params(self):
        """Testa inicialização com parâmetros padrão."""
        manager = TensiometerSerialManager()

        assert manager.serial_connection is None
        assert manager.is_connected is False
        assert manager.port is None
        assert manager.baudrate == 2400
        assert manager.timeout == 1.0
        assert manager.last_error == ""
        assert manager.REQ_COMMAND == b'\x20'
        assert manager.FRAME_LEN == 9

    def test_constants_defined(self):
        """Testa que constantes do protocolo estão definidas."""
        manager = TensiometerSerialManager()

        assert hasattr(manager, 'REQ_COMMAND')
        assert hasattr(manager, 'FRAME_LEN')
        assert hasattr(manager, 'UNIT_MAP')

        # Verifica mapa de unidades
        assert 0x05 in manager.UNIT_MAP
        assert manager.UNIT_MAP[0x05] == "N/cm²"
        assert manager.UNIT_MAP[0x04] == "kg/cm²"
        assert manager.UNIT_MAP[0x06] == "lb/cm²"


@pytest.mark.integration
class TestTensiometerProtocol:
    """Testa decodificação do protocolo AS-120N."""

    def test_real_dig_conversion(self):
        """Testa conversão de nibble para dígito."""
        manager = TensiometerSerialManager()

        # Testa dígitos 0-9
        # O formato é: (nibble & 0x0F) + 10, depois % 10
        # Então se o nibble tem valor 0x0A (10), resultado é 0
        # Se tem valor 0x0B (11), resultado é 1

        test_cases = [
            (0x0A, 0),  # (10 + 10) % 10 = 0
            (0x0B, 1),  # (11 + 10) % 10 = 1
            (0x0C, 2),  # (12 + 10) % 10 = 2
            (0x0D, 3),  # (13 + 10) % 10 = 3
            (0x0E, 4),  # (14 + 10) % 10 = 4
            (0x0F, 5),  # (15 + 10) % 10 = 5
            (0x00, 0),  # (0 + 10) % 10 = 0
            (0x09, 9),  # (9 + 10) % 10 = 9
        ]

        for nibble, expected in test_cases:
            result = manager._real_dig(nibble)
            assert result == expected, f"Falha para nibble 0x{nibble:02X}: esperado {expected}, obteve {result}"

    def test_decode_frame_valid_2_34(self):
        """Testa decodificação de frame válido para 2.34."""
        manager = TensiometerSerialManager()
        frame = MockSerialResponse.create_frame(2.34)

        value = manager._decode_frame(frame)

        assert value is not None
        assert abs(value - 2.34) < 0.01

    def test_decode_frame_valid_0_00(self):
        """Testa decodificação de frame válido para 0.00."""
        manager = TensiometerSerialManager()
        frame = MockSerialResponse.create_frame(0.00)

        value = manager._decode_frame(frame)

        assert value is not None
        assert abs(value - 0.00) < 0.01

    def test_decode_frame_valid_9_99(self):
        """Testa decodificação de frame válido para 9.99 (valor máximo)."""
        manager = TensiometerSerialManager()
        frame = MockSerialResponse.create_frame(9.99)

        value = manager._decode_frame(frame)

        assert value is not None
        assert abs(value - 9.99) < 0.01

    def test_decode_frame_invalid_header(self):
        """Testa rejeição de frame com header inválido."""
        manager = TensiometerSerialManager()
        frame = MockSerialResponse.create_invalid_frame()

        value = manager._decode_frame(frame)

        assert value is None

    def test_decode_frame_incomplete(self):
        """Testa rejeição de frame incompleto."""
        manager = TensiometerSerialManager()
        frame = MockSerialResponse.create_incomplete_frame()

        value = manager._decode_frame(frame)

        assert value is None

    def test_decode_frame_wrong_command(self):
        """Testa rejeição de frame com comando errado no byte 2."""
        manager = TensiometerSerialManager()

        # Cria frame com comando errado no byte 2
        frame = bytearray(MockSerialResponse.create_frame(12.34))
        frame[2] = 0xFF  # Comando errado

        value = manager._decode_frame(bytes(frame))

        assert value is None

    def test_decode_frame_zero_decimals(self):
        """Testa decodificação com 0 casas decimais."""
        manager = TensiometerSerialManager()

        # Cria frame com 0 casas decimais (valor 9)
        # d1=9, d2=0, d3=0 → raw=9 / 10^0 = 9
        frame = bytearray([
            0x10,           # Byte 0: Header
            0x19,           # Byte 1: Command
            0x19,           # Byte 2: Cmd echo
            0x00,           # Byte 3: 0 casas
            0x05, 0x00,     # Byte 4-5: Unidade
            0xBA,           # Byte 6: d3=0
            0xBA,           # Byte 7: d2=0
            0xB9            # Byte 8: d1=9
        ])

        value = manager._decode_frame(bytes(frame))

        assert value is not None
        assert abs(value - 9.0) < 0.1

    def test_decode_frame_one_decimal(self):
        """Testa decodificação com 1 casa decimal."""
        manager = TensiometerSerialManager()

        # Cria frame com 1 casa decimal (valor 9.5)
        # d1=5, d2=9, d3=0 → raw=95 / 10^1 = 9.5
        frame = bytearray([
            0x10,           # Byte 0: Header
            0x19,           # Byte 1: Command
            0x19,           # Byte 2: Cmd echo
            0x10,           # Byte 3: 1 casa
            0x05, 0x00,     # Byte 4-5: Unidade
            0xBA,           # Byte 6: d3=0
            0xB9,           # Byte 7: d2=9
            0xBF            # Byte 8: d1=5
        ])

        value = manager._decode_frame(bytes(frame))

        assert value is not None
        assert abs(value - 9.5) < 0.1


@pytest.mark.integration
class TestTensiometerConnection:
    """Testa conexão e desconexão do tensiômetro."""

    def test_get_available_ports(self, mock_list_ports):
        """Testa listagem de portas seriais disponíveis."""
        manager = TensiometerSerialManager()
        ports = manager.get_available_ports()

        assert isinstance(ports, list)
        assert len(ports) == 3
        assert '/dev/ttyUSB0' in ports
        assert '/dev/ttyUSB1' in ports
        assert 'COM3' in ports

    def test_connect_success(self, mock_serial):
        """Testa conexão bem-sucedida."""
        mock, patcher = mock_serial
        with patcher:
            manager = TensiometerSerialManager()
            result = manager.connect('/dev/ttyUSB0', 2400, 1.0)

            assert result is True
            assert manager.is_connected is True
            assert manager.port == '/dev/ttyUSB0'
            assert manager.baudrate == 2400
            assert manager.serial_connection is not None

            # Verifica que a porta serial foi criada com parâmetros corretos
            serial.Serial.assert_called_once_with(
                port='/dev/ttyUSB0',
                baudrate=2400,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1.0
            )

    def test_connect_custom_baudrate(self, mock_serial):
        """Testa conexão com baudrate customizado."""
        mock, patcher = mock_serial
        with patcher:
            manager = TensiometerSerialManager()
            result = manager.connect('/dev/ttyUSB0', baudrate=9600)

            assert result is True
            assert manager.baudrate == 9600

            serial.Serial.assert_called_once()

    def test_connect_failure(self, mock_serial):
        """Testa falha ao conectar (porta inválida)."""
        mock, patcher = mock_serial

        with patcher:
            # Simula erro na criação da porta serial
            serial.Serial.side_effect = serial.SerialException("Port not found")

            manager = TensiometerSerialManager()
            result = manager.connect('/dev/ttyUSB99')

            assert result is False
            assert manager.is_connected is False
            assert manager.last_error != ""

    def test_disconnect(self, mock_serial):
        """Testa desconexão do tensiômetro."""
        mock, patcher = mock_serial
        mock.is_open = True

        with patcher:
            manager = TensiometerSerialManager()
            manager.connect('/dev/ttyUSB0')

            # Modifica o mock para indicar que está aberto
            mock.is_open = True

            manager.disconnect()

            assert manager.is_connected is False
            assert manager.serial_connection is None
            assert manager.port is None
            mock.close.assert_called_once()

    def test_reconnect(self, mock_serial):
        """Testa reconexão (desconecta antes de conectar)."""
        mock, patcher = mock_serial

        with patcher:
            manager = TensiometerSerialManager()

            # Primeira conexão
            mock.is_open = True
            manager.connect('/dev/ttyUSB0')
            assert manager.is_connected is True

            # Reconexão (deve desconectar primeiro)
            mock.is_open = True
            manager.connect('/dev/ttyUSB1')

            # Verifica que close foi chamado antes da nova conexão
            assert mock.close.call_count >= 1


@pytest.mark.integration
class TestTensiometerReading:
    """Testa leitura de valores do tensiômetro."""

    def test_read_tension_value_valid(self, mock_serial):
        """Testa leitura de valor válido (5.67)."""
        mock, patcher = mock_serial
        mock.read.return_value = MockSerialResponse.create_frame(5.67)

        with patcher:
            manager = TensiometerSerialManager()
            manager.connect('/dev/ttyUSB0')
            mock.is_open = True

            value = manager.read_tension_value()

            assert value == "5.67"

            # Verifica sequência de operações
            mock.reset_input_buffer.assert_called_once()
            mock.write.assert_called_once_with(b'\x20')
            mock.flush.assert_called_once()
            mock.read.assert_called_once_with(9)

    def test_read_tension_value_zero(self, mock_serial):
        """Testa leitura de valor zero."""
        mock, patcher = mock_serial
        mock.read.return_value = MockSerialResponse.create_frame(0.00)

        with patcher:
            manager = TensiometerSerialManager()
            manager.connect('/dev/ttyUSB0')
            mock.is_open = True

            value = manager.read_tension_value()

            assert value == "0.00"

    def test_read_tension_value_high(self, mock_serial):
        """Testa leitura de valor alto (9.99 - valor máximo)."""
        mock, patcher = mock_serial
        mock.read.return_value = MockSerialResponse.create_frame(9.99)

        with patcher:
            manager = TensiometerSerialManager()
            manager.connect('/dev/ttyUSB0')
            mock.is_open = True

            value = manager.read_tension_value()

            assert value == "9.99"

    def test_read_tension_not_connected(self, mock_serial):
        """Testa leitura sem conexão retorna "0"."""
        mock, patcher = mock_serial

        with patcher:
            manager = TensiometerSerialManager()
            # Não conecta

            value = manager.read_tension_value()

            assert value == ""
            assert "nao conectado" in manager.last_error.lower()

    def test_read_tension_no_response(self, mock_serial):
        """Testa leitura sem resposta do tensiômetro."""
        mock, patcher = mock_serial
        mock.read.return_value = b''  # Resposta vazia

        with patcher:
            manager = TensiometerSerialManager()
            manager.connect('/dev/ttyUSB0')
            mock.is_open = True

            value = manager.read_tension_value()

            assert value == ""
            assert "sem resposta" in manager.last_error.lower()

    def test_read_tension_incomplete_frame(self, mock_serial):
        """Testa leitura com frame incompleto."""
        mock, patcher = mock_serial
        mock.read.return_value = MockSerialResponse.create_incomplete_frame()

        with patcher:
            manager = TensiometerSerialManager()
            manager.connect('/dev/ttyUSB0')
            mock.is_open = True

            value = manager.read_tension_value()

            assert value == ""
            assert "incompleto" in manager.last_error.lower()

    def test_read_tension_invalid_frame(self, mock_serial):
        """Testa leitura com frame inválido."""
        mock, patcher = mock_serial
        mock.read.return_value = MockSerialResponse.create_invalid_frame()

        with patcher:
            manager = TensiometerSerialManager()
            manager.connect('/dev/ttyUSB0')
            mock.is_open = True

            value = manager.read_tension_value()

            assert value == ""
            assert "invalido" in manager.last_error.lower()

    def test_read_tension_exception(self, mock_serial):
        """Testa tratamento de exceção na leitura."""
        mock, patcher = mock_serial
        mock.read.side_effect = serial.SerialException("Read error")

        with patcher:
            manager = TensiometerSerialManager()
            manager.connect('/dev/ttyUSB0')
            mock.is_open = True

            value = manager.read_tension_value()

            assert value == ""
            assert manager.last_error != ""


@pytest.mark.integration
class TestTensiometerCommands:
    """Testa envio de comandos para o tensiômetro."""

    def test_send_command_success(self, mock_serial):
        """Testa envio bem-sucedido de comando."""
        mock, patcher = mock_serial

        with patcher:
            manager = TensiometerSerialManager()
            manager.connect('/dev/ttyUSB0')
            mock.is_open = True

            result = manager.send_command("TEST")

            assert result is True
            mock.write.assert_called_once_with(b'TEST\r\n')
            mock.flush.assert_called()

    def test_send_command_not_connected(self, mock_serial):
        """Testa envio de comando sem conexão."""
        mock, patcher = mock_serial

        with patcher:
            manager = TensiometerSerialManager()
            # Não conecta

            result = manager.send_command("TEST")

            assert result is False

    def test_send_command_failure(self, mock_serial):
        """Testa falha ao enviar comando."""
        mock, patcher = mock_serial
        mock.write.side_effect = serial.SerialException("Write error")

        with patcher:
            manager = TensiometerSerialManager()
            manager.connect('/dev/ttyUSB0')
            mock.is_open = True

            result = manager.send_command("TEST")

            assert result is False
            assert manager.last_error != ""


@pytest.mark.integration
class TestTensiometerErrors:
    """Testa tratamento de erros diversos."""

    def test_list_ports_exception(self):
        """Testa tratamento de erro ao listar portas."""
        with patch('serial.tools.list_ports.comports') as mock:
            mock.side_effect = Exception("System error")

            manager = TensiometerSerialManager()
            ports = manager.get_available_ports()

            assert ports == []

    def test_disconnect_exception(self, mock_serial):
        """Testa tratamento de exceção ao desconectar."""
        mock, patcher = mock_serial
        mock.close.side_effect = Exception("Close error")

        with patcher:
            manager = TensiometerSerialManager()
            manager.connect('/dev/ttyUSB0')
            mock.is_open = True

            # Não deve levantar exceção
            manager.disconnect()

            assert manager.is_connected is False

    def test_multiple_readings(self, mock_serial):
        """Testa múltiplas leituras consecutivas."""
        mock, patcher = mock_serial

        # Simula valores diferentes para cada leitura
        readings = [
            MockSerialResponse.create_frame(1.5),
            MockSerialResponse.create_frame(2.2),
            MockSerialResponse.create_frame(3.8),
            MockSerialResponse.create_frame(4.1),
            MockSerialResponse.create_frame(5.9),
        ]
        mock.read.side_effect = readings

        with patcher:
            manager = TensiometerSerialManager()
            manager.connect('/dev/ttyUSB0')
            mock.is_open = True

            values = []
            for i in range(5):
                value = manager.read_tension_value()
                values.append(float(value))

            assert len(values) == 5
            assert abs(values[0] - 1.5) < 0.1
            assert abs(values[1] - 2.2) < 0.1
            assert abs(values[2] - 3.8) < 0.1
            assert abs(values[3] - 4.1) < 0.1
            assert abs(values[4] - 5.9) < 0.1


@pytest.mark.integration
class TestTensiometerIntegration:
    """Testes de integração simulando cenários reais."""

    def test_measurement_workflow(self, mock_serial):
        """Testa fluxo completo de medição."""
        mock, patcher = mock_serial

        # Simula 5 medições em diferentes pontos
        readings = [
            MockSerialResponse.create_frame(2.5),
            MockSerialResponse.create_frame(3.2),
            MockSerialResponse.create_frame(1.8),
            MockSerialResponse.create_frame(2.9),
            MockSerialResponse.create_frame(3.5),
        ]
        mock.read.side_effect = readings

        with patcher:
            manager = TensiometerSerialManager()

            # Conecta
            assert manager.connect('/dev/ttyUSB0') is True
            mock.is_open = True

            # Realiza medições
            measurements = []
            for i in range(5):
                value = manager.read_tension_value()
                measurements.append(float(value))

            # Desconecta
            manager.disconnect()

            # Verifica resultados
            assert len(measurements) == 5
            assert all(v > 0 for v in measurements)
            assert abs(measurements[0] - 2.5) < 0.1
            assert abs(measurements[4] - 3.5) < 0.1

    def test_reconnect_after_error(self, mock_serial):
        """Testa reconexão após erro de leitura."""
        mock, patcher = mock_serial
        mock.is_open = True

        with patcher:
            manager = TensiometerSerialManager()

            # Primeira conexão
            assert manager.connect('/dev/ttyUSB0') is True

            # Simula erro na leitura
            mock.read.side_effect = serial.SerialException("Communication error")
            value = manager.read_tension_value()
            assert value == ""

            # Desconecta e reconecta
            manager.disconnect()
            mock.read.side_effect = None  # Remove erro
            mock.is_open = True
            mock.read.return_value = MockSerialResponse.create_frame(5.0)

            # Reconecta
            assert manager.connect('/dev/ttyUSB1') is True
            mock.is_open = True

            # Nova leitura deve funcionar
            value = manager.read_tension_value()
            assert abs(float(value) - 5.0) < 0.1
