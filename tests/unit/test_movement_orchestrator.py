
import pytest
from unittest.mock import Mock, patch, MagicMock
from aoi_lib.movement_orchestrator import MovementOrchestrator

# Define a dummy class for spec to avoid 'cnc' attribute auto-creation
class MockControllerSpec:
    is_connected = True
    machine_status = "Idle"
    max_feed = {'x': 5000, 'y': 5000, 'z': 800}
    def jog_start(self, axis, direction, speed): pass
    def jog_stop(self): pass
    def step_move(self, axis, distance, speed): pass
    def move_to_absolute_position(self, x, y, z, feed_rate): pass
    def backlight_set(self, on): pass
    def send_soft_reset(self): pass
    def unlock(self): pass
    def wait_for_idle(self): pass

@pytest.fixture
def mock_controller():
    # Use spec to prevent auto-creation of 'cnc' attribute
    ctrl = Mock(spec=MockControllerSpec)
    ctrl.is_connected = True
    ctrl.machine_status = "Idle"
    ctrl.max_feed = {'x': 5000, 'y': 5000, 'z': 800}
    return ctrl

@pytest.fixture
def orchestrator(mock_controller):
    return MovementOrchestrator(mock_controller)

def test_validate_connection_success(orchestrator, mock_controller):
    res = orchestrator._validate_connection()
    assert res.success is True

def test_validate_connection_failure(orchestrator, mock_controller):
    mock_controller.is_connected = False
    res = orchestrator._validate_connection()
    assert res.success is False
    assert "não conectada" in res.error_message

def test_validate_machine_state_alarm(orchestrator, mock_controller):
    mock_controller.machine_status = "Alarm:1"
    res = orchestrator._validate_machine_state()
    assert res.success is False
    assert "em alarme" in res.error_message

def test_validate_feed_rate_valid(orchestrator):
    res = orchestrator.validate_feed_rate(1000)
    assert res.success is True
    assert res.data['feed'] == 1000
    assert res.data['clamped'] is False

def test_validate_feed_rate_clamp(orchestrator):
    res = orchestrator.validate_feed_rate(6000) # Max is 5000
    assert res.success is True
    assert res.data['feed'] == 5000
    assert res.data['clamped'] is True

def test_jog_success(orchestrator, mock_controller):
    res = orchestrator.jog('X', 1, 1000)
    assert res.success is True
    mock_controller.jog_start.assert_called_with('X', 1, 1000)

def test_jog_fail_connection(orchestrator, mock_controller):
    mock_controller.is_connected = False
    res = orchestrator.jog('X', 1, 1000)
    assert res.success is False

def test_stop_jog(orchestrator, mock_controller):
    res = orchestrator.stop_jog()
    assert res.success is True
    mock_controller.jog_stop.assert_called()

def test_step_move_success(orchestrator, mock_controller):
    res = orchestrator.step_move('Y', -1, 10, 500)
    assert res.success is True
    # distance = step * dir = 10 * -1 = -10
    mock_controller.step_move.assert_called_with('Y', -10, 500)

def test_move_absolute_success(orchestrator, mock_controller):
    res = orchestrator.move_absolute(10, 20, 5, 500)
    assert res.success is True
    mock_controller.move_to_absolute_position.assert_called_with(10, 20, 5, feed_rate=500)

def test_backlight_success(orchestrator, mock_controller):
    # Mocking backlight_set method existence
    # Note: spec includes backlight_set, so it exists
    res = orchestrator.set_backlight(True)
    assert res.success is True
    mock_controller.backlight_set.assert_called_with(True)

def test_backlight_not_supported(orchestrator, mock_controller):
    # Ensure no backlight_set method by creating a controller without it
    class NoBacklightSpec:
        is_connected = True
        machine_status = "Idle"
        
    ctrl = Mock(spec=NoBacklightSpec)
    ctrl.is_connected = True
    
    orch = MovementOrchestrator(ctrl)
    res = orch.set_backlight(True)
    assert res.success is False
    assert "não suporta" in res.error_message

def test_emergency_stop(orchestrator, mock_controller):
    res = orchestrator.emergency_stop()
    assert res.success is True
    mock_controller.send_soft_reset.assert_called()

def test_unlock(orchestrator, mock_controller):
    res = orchestrator.unlock()
    assert res.success is True
    mock_controller.unlock.assert_called()

def test_home_plc(orchestrator, mock_controller):
    # Need to patch where the class is DEFINED, because it is imported inside the method
    # and isinstance checks against the imported class.
    # We patch aoi_lib.plc_axis_controller.PLCAxisController
    
    with patch('aoi_lib.plc_axis_controller.PLCAxisController') as MockPLCClass:
        # We need mock_controller to be an instance of this MockPLCClass for isinstance to work?
        # No, isinstance(obj, MockClass) works if we setup correctly.
        # But MockPLCClass is a Mock object. isinstance(obj, Mock) returns False usually unless spec.
        
        # Easier way: The code does `from aoi_lib.plc_axis_controller import PLCAxisController`
        # We can mock the module import using sys.modules or patch.
        
        # Let's try patching the class in its module.
        # And we need mock_controller to be recognized as instance.
        
        # Since we cannot easily make a Mock verify as isinstance of another Mock unless we use spec,
        # and the code does local import, we need to ensure the local import returns something 
        # that mock_controller is an instance of.
        
        # Trick: mock the class, and say mock_controller is an instance of it.
        MockPLCClass.return_value = mock_controller # Not quite right for isinstance
        
        # Let's side_step the isinstance check by mocking the local import return value
        # The code does: if isinstance(self.cnc, PLCAxisController):
        
        # We can just make `mock_controller` be an instance of the REAL PLCAxisController? 
        # No, that requires dependencies.
        
        # Let's create a dummy class to mock PLCAxisController logic
        pass

    # New approach for this test:
    # We want to test the 'if isinstance(...):' branch.
    # We can rely on the fact that if we patch 'aoi_lib.plc_axis_controller.PLCAxisController',
    # the local import will get that mock.
    # We just need `isinstance(mock_controller, ThatMock)` to be true.
    # Mocks don't support isinstance well against other Mocks.
    
    # Alternative: Refactor MovementOrchestrator to not use local import for type checking?
    # No, I should test existing code.
    
    # Correct way to test isinstance with Mocks:
    # Create a dummy class, and patch PLCAxisController to BE that dummy class.
    class DummyPLC:
        is_connected = True
        machine_status = "Idle"
        def wait_for_idle(self): pass
        
    mock_controller.__class__ = DummyPLC
    
    with patch('aoi_lib.plc_axis_controller.PLCAxisController', DummyPLC):
        mock_controller.client = Mock() # needs client for write_coil
        
        res = orchestrator.home()
        assert res.success is True
        # Should call write_coil multiple times
        assert mock_controller.client.write_coil.call_count > 0
