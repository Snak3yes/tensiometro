import pytest
from unittest.mock import Mock, patch, MagicMock
from aoi_lib.plc_axis_controller import PLCAxisController

@pytest.fixture
def mock_modbus_client():
    with patch('aoi_lib.plc_axis_controller.ModbusTcpClient') as MockClient:
        client_instance = MockClient.return_value
        client_instance.connect.return_value = True
        client_instance.close.return_value = True
        
        # Simula leitura de registros
        read_response = Mock()
        read_response.isError.return_value = False
        read_response.registers = [0, 0, 0, 0]
        client_instance.read_holding_registers.return_value = read_response
        
        # Simula escrita
        write_response = Mock()
        write_response.isError.return_value = False
        client_instance.write_coil.return_value = write_response
        client_instance.write_registers.return_value = write_response
        
        yield client_instance

def test_initialization():
    """Testa inicialização do controlador PLC."""
    with patch('aoi_lib.plc_axis_controller.ModbusTcpClient'):
        plc = PLCAxisController(host='127.0.0.1', port=5020, auto_connect=False)
        assert plc.host == '127.0.0.1'
        assert plc.port == 5020
        assert plc.is_connected is False

def test_connect_success(mock_modbus_client):
    """Testa conexão bem sucedida."""
    plc = PLCAxisController(auto_connect=False)
    assert plc.connect() is True
    assert plc.is_connected is True
    mock_modbus_client.connect.assert_called_once()

def test_connect_failure(mock_modbus_client):
    """Testa falha na conexão."""
    mock_modbus_client.connect.return_value = False
    plc = PLCAxisController(auto_connect=False)
    
    with pytest.raises(ConnectionError):
        plc.connect()
        
    assert plc.is_connected is False

def test_move_absolute(mock_modbus_client):
    """Testa comando de movimento absoluto."""
    plc = PLCAxisController(auto_connect=True)
    
    # Use uppercase axis 'X' as required by ADDRESSES
    success = plc.move_absolute('X', 100.0)
    assert success is True
    mock_modbus_client.write_registers.assert_called()

def test_read_position(mock_modbus_client):
    """Testa leitura de posição."""
    plc = PLCAxisController(auto_connect=True)
    
    # Mock return
    read_response = Mock()
    read_response.isError.return_value = False
    read_response.registers = [0, 100] 
    mock_modbus_client.read_holding_registers.return_value = read_response
    
    pos = plc.get_current_position()
    assert mock_modbus_client.read_holding_registers.called

def test_backlight_control(mock_modbus_client):
    """Testa controle de backlight."""
    plc = PLCAxisController(auto_connect=True)
    plc.backlight_coil_address = 10
    
    plc.backlight_turn_on()
    mock_modbus_client.write_coil.assert_called_with(10, True)
    
    plc.backlight_turn_off()
    mock_modbus_client.write_coil.assert_called_with(10, False)