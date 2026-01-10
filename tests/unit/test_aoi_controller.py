import pytest
from unittest.mock import Mock, patch, MagicMock, call
from aoi_lib.aoi_controller import CNCAOIController, InspectionPosition, InspectionSequence

@pytest.fixture
def mock_dependencies():
    # Patch dependencies where they are DEFINED or imported globally
    with patch('aoi_lib.aoi_controller.PLCAxisController') as MockPLC, \
         patch('aoi_lib.aoi_controller.CameraController') as MockCam, \
         patch('aoi_lib.config_manager.AOIConfigManager') as MockCfg:
        
        # Setup mock PLC
        from aoi_lib.plc_axis_controller import PLCAxisController
        plc_instance = Mock(spec=PLCAxisController)
        plc_instance.is_connected = True
        plc_instance.pulses_per_mm = 80.0
        # Mocking get_current_position
        plc_instance.get_current_position.return_value = {'x': 100, 'y': 200, 'z': 10}
        MockPLC.return_value = plc_instance
        
        # Setup mock Cam
        cam_instance = MockCam.return_value
        cam_instance.connect.return_value = True
        cam_instance.capture_frame.return_value = (True, "fake_frame")
        
        # Setup mock Config
        cfg_instance = MockCfg.return_value
        cfg_instance.get.return_value = 1.0 
        
        yield {'plc': plc_instance, 'cam': cam_instance, 'cfg': cfg_instance}

def test_initialization(mock_dependencies):
    """Testa inicialização do controlador."""
    controller = CNCAOIController()
    assert controller.cnc == mock_dependencies['plc']
    assert controller.camera == mock_dependencies['cam']
    assert controller.is_running_sequence is False

def test_connect_disconnect(mock_dependencies):
    """Testa métodos de conexão delegados."""
    controller = CNCAOIController()
    assert controller.connect() is True
    assert controller.disconnect() is True
    mock_dependencies['plc'].close.assert_called_once()

def test_delegated_movement_methods(mock_dependencies):
    """Testa delegação de métodos de movimento para o CNC."""
    controller = CNCAOIController()
    controller.step_move('x', 10)
    mock_dependencies['plc'].step_move.assert_called_with('x', 10)

def test_getattr_fallback(mock_dependencies):
    """Testa erro de atributo inexistente."""
    controller = CNCAOIController()
    with pytest.raises(AttributeError):
        controller.metodo_inexistente()

def test_run_gcode_file_loading(mock_dependencies):
    """Testa carregamento de GCODE (mockado)."""
    controller = CNCAOIController()
    
    with patch('aoi_lib.gcode_manager.GCodeManager') as MockGCode:
        gcode_mgr = MockGCode.return_value
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

def test_add_current_position(mock_dependencies):
    """Testa adicionar posição atual."""
    controller = CNCAOIController()
    pos = controller.add_current_position("Home")
    
    assert pos.name == "Home"
    assert pos.x == 100
    assert pos.y == 200
    assert pos.z == 10
    
    # Verifica se foi adicionado ao gerenciador
    assert len(controller.position_manager.positions) == 1

def test_connect_camera(mock_dependencies):
    """Testa conexão de câmera."""
    controller = CNCAOIController()
    controller.connect_camera(1)
    mock_dependencies['cam'].connect.assert_called_with(1)