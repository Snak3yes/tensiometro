import pytest
from unittest.mock import Mock, patch, MagicMock
from aoi_lib.aoi_controller import CNCAOIController, InspectionPosition

@pytest.fixture
def mock_dependencies():
    # Patch dependencies where they are DEFINED or imported globally
    with patch('aoi_lib.aoi_controller.PLCAxisController') as MockPLC, \
         patch('aoi_lib.aoi_controller.CameraController') as MockCam, \
         patch('aoi_lib.config_manager.AOIConfigManager') as MockCfg:
        
        # Setup mock PLC with a spec to prevent auto-creation of attributes
        # We use a real class or a list of attributes as spec
        plc_instance = MockPLC.return_value
        plc_instance.is_connected = True
        plc_instance.pulses_per_mm = 80.0
        
        # Configure spec to only allow existing attributes + close + step_move
        # Easier way: just ensure hasattr returns false for unknown stuff if we didn't use spec=True
        # But since we didn't use spec=True, Mock allows everything.
        # We need to manually set side_effect for getattr on the mock? No.
        # Ideally we use autospec=True in patch, but let's just make the test more robust
        # by deleting the attribute from the mock to ensure hasattr returns False? 
        # Mocks are tricky with hasattr.
        
        # Alternative: We can mock the __getattr__ behavior of the controller directly in the test?
        # No, we are testing the controller.
        
        # Let's use spec for PLC to make hasattr behave correctly
        from aoi_lib.plc_axis_controller import PLCAxisController
        plc_instance = Mock(spec=PLCAxisController)
        plc_instance.is_connected = True
        plc_instance.pulses_per_mm = 80.0
        MockPLC.return_value = plc_instance
        
        # Setup mock Config
        cfg_instance = MockCfg.return_value
        cfg_instance.get.return_value = 1.0 
        
        yield {'plc': plc_instance, 'cam': MockCam.return_value, 'cfg': cfg_instance}

def test_initialization(mock_dependencies):
    """Testa inicialização do controlador."""
    controller = CNCAOIController()
    assert controller.cnc == mock_dependencies['plc']
    assert controller.camera == mock_dependencies['cam']
    assert controller.is_running_sequence is False

def test_connect_disconnect(mock_dependencies):
    """Testa métodos de conexão delegados."""
    controller = CNCAOIController()
    
    # Connect (property check)
    assert controller.connect() is True
    
    # Disconnect
    assert controller.disconnect() is True
    mock_dependencies['plc'].close.assert_called_once()

def test_delegated_movement_methods(mock_dependencies):
    """Testa delegação de métodos de movimento para o CNC."""
    controller = CNCAOIController()
    
    # Add step_move to the mock spec/instance so hasattr returns True
    # Since we used spec=PLCAxisController, we need to ensure PLCAxisController has step_move
    # It does.
    
    controller.step_move('x', 10)
    mock_dependencies['plc'].step_move.assert_called_with('x', 10)

def test_getattr_fallback(mock_dependencies):
    """Testa erro de atributo inexistente."""
    controller = CNCAOIController()
    
    # Ensure the method is NOT on the PLC mock
    # With spec=PLCAxisController, 'metodo_inexistente' shouldn't exist
    
    with pytest.raises(AttributeError):
        controller.metodo_inexistente()

def test_run_gcode_file_loading(mock_dependencies):
    """Testa carregamento de GCODE (mockado)."""
    controller = CNCAOIController()
    
    with patch('aoi_lib.gcode_manager.GCodeManager') as MockGCode:
        gcode_mgr = MockGCode.return_value
        # Simula retorno de dados COM sequence_name
        gcode_mgr.read_gcode_file.return_value = {
            'sequence_name': 'Test Sequence',
            'positions': [
                {'name': 'P1', 'x': 10, 'y': 20},
                {'name': 'P2', 'x': 30, 'y': 40}
            ]
        }
        
        # Mock do método de execução real
        controller.run_sequence = Mock()
        
        controller.run_gcode_file("teste.gcode")
        
        controller.run_sequence.assert_called_once()
        sequence_name = controller.run_sequence.call_args[0][0]
        assert sequence_name == 'Test Sequence'
