
import pytest
from unittest.mock import Mock, patch, MagicMock
from aoi_lib.inspection_flow_service import InspectionFlowService
from aoi_lib.stencil_inspector import InspectionResult

@pytest.fixture
def mock_inspector():
    with patch('aoi_lib.inspection_flow_service.StencilInspector') as MockClass:
        instance = MockClass.return_value
        instance.load_gerber.return_value = True
        instance.inspect.return_value = InspectionResult()
        instance.get_result_overlay.return_value = "fake_overlay"
        yield instance

@pytest.fixture
def service(mock_inspector):
    return InspectionFlowService()

def test_execute_inspection_success(service, mock_inspector):
    with patch('os.path.exists', return_value=True), \
         patch('cv2.imread', return_value="fake_image"):
        
        res, overlay = service.execute_inspection("path/to/gerber.gbr", "path/to/image.png")
        
        assert res is not None
        assert overlay == "fake_overlay"
        mock_inspector.load_gerber.assert_called_with("path/to/gerber.gbr")
        mock_inspector.set_mosaic.assert_called_with("fake_image")
        mock_inspector.inspect.assert_called()

def test_execute_inspection_file_not_found_gerber(service):
    with patch('os.path.exists', side_effect=[False, True]): # Gerber missing
        with pytest.raises(FileNotFoundError, match="Gerber não encontrado"):
            service.execute_inspection("missing.gbr", "ok.png")

def test_execute_inspection_file_not_found_mosaic(service):
    with patch('os.path.exists', side_effect=[True, False]): # Mosaic missing
        with pytest.raises(FileNotFoundError, match="mosaico não encontrado"):
            service.execute_inspection("ok.gbr", "missing.png")

def test_execute_inspection_image_load_fail(service):
    with patch('os.path.exists', return_value=True), \
         patch('cv2.imread', return_value=None):
        
        with pytest.raises(ValueError, match="Falha ao decodificar"):
            service.execute_inspection("ok.gbr", "corrupt.png")

def test_execute_inspection_gerber_load_fail(service, mock_inspector):
    mock_inspector.load_gerber.return_value = False
    with patch('os.path.exists', return_value=True):
        with pytest.raises(Exception, match="Falha ao processar arquivo Gerber"):
            service.execute_inspection("bad.gbr", "ok.png")

def test_execute_inspection_with_alignment(service, mock_inspector):
    with patch('os.path.exists', return_value=True), \
         patch('cv2.imread', return_value="img"):
        
        align = {'tx': 10, 'ty': 20, 'angle': 45, 'scale': 1.0}
        service.execute_inspection("g.gbr", "m.png", alignment_config=align)
        
        mock_inspector.set_alignment.assert_called()
        # Verify transform values if possible, but assert_called is enough for flow check

def test_execute_inspection_with_thresholds(service, mock_inspector):
    from aoi_lib.stencil_inspector import InspectionThresholds
    t = InspectionThresholds(ok_threshold=99)
    
    with patch('os.path.exists', return_value=True), \
         patch('cv2.imread', return_value="img"):
         
        service.execute_inspection("g.gbr", "m.png", thresholds=t)
        
        assert service.inspector.thresholds == t
