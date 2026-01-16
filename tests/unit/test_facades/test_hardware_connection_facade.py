"""
Tests for HardwareConnectionFacade

Unit tests for HardwareConnectionFacade component.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch


class TestHardwareConnectionFacade:
    """Test cases for HardwareConnectionFacade."""

    @pytest.fixture
    def connection_manager(self):
        """Mock connection manager."""
        manager = Mock()
        manager.connect_plc = Mock(return_value=True)
        manager.connect_cnc = Mock(return_value=True)
        manager.connect_camera = Mock(return_value=True)
        manager.test_camera = Mock(return_value=True)
        manager.refresh_serial_ports = Mock(return_value=["COM1", "COM2"])
        manager.is_plc_connected = Mock(return_value=False)
        manager.is_cnc_connected = Mock(return_value=False)
        manager.is_camera_connected = Mock(return_value=False)
        return manager

    @pytest.fixture
    def main_window(self):
        """Mock main window."""
        window = Mock()
        window.statusBar = Mock()
        window.statusBar().showMessage = Mock()
        return window

    @pytest.fixture
    def facade(self, connection_manager, main_window):
        """Create HardwareConnectionFacade instance."""
        from consumo_lib.facades.hardware_connection_facade import HardwareConnectionFacade

        return HardwareConnectionFacade(
            connection_manager,
            main_window
        )

    def test_init(self, facade):
        """Test HardwareConnectionFacade initialization."""
        assert facade.connection_manager is not None
        assert facade.main_window is not None

    def test_connect_plc_success(self, facade):
        """Test successful PLC connection."""
        result = facade.connect_plc("192.168.1.5", 502)

        assert result is True
        facade.connection_manager.connect_plc.assert_called_once_with("192.168.1.5", 502)

    def test_connect_plc_failure(self, facade):
        """Test failed PLC connection."""
        facade.connection_manager.connect_plc = Mock(return_value=False)

        result = facade.connect_plc("192.168.1.5", 502)

        assert result is False

    def test_connect_cnc_success(self, facade):
        """Test successful CNC connection."""
        result = facade.connect_cnc("COM3")

        assert result is True
        facade.connection_manager.connect_cnc.assert_called_once_with("COM3")

    def test_connect_camera_success(self, facade):
        """Test successful camera connection."""
        result = facade.connect_camera("0")

        assert result is True
        facade.connection_manager.connect_camera.assert_called_once_with("0")

    def test_test_camera(self, facade):
        """Test camera testing."""
        result = facade.test_camera()

        assert result is True
        facade.connection_manager.test_camera.assert_called_once()

    def test_refresh_ports(self, facade):
        """Test port refreshing."""
        ports = facade.refresh_ports()

        assert ports == ["COM1", "COM2"]
        facade.connection_manager.refresh_serial_ports.assert_called_once()

    def test_is_plc_connected(self, facade):
        """Test PLC connection status check."""
        facade.connection_manager.is_plc_connected = Mock(return_value=True)

        result = facade.is_plc_connected()

        assert result is True

    def test_is_cnc_connected(self, facade):
        """Test CNC connection status check."""
        facade.connection_manager.is_cnc_connected = Mock(return_value=True)

        result = facade.is_cnc_connected()

        assert result is True

    def test_is_camera_connected(self, facade):
        """Test camera connection status check."""
        facade.connection_manager.is_camera_connected = Mock(return_value=True)

        result = facade.is_camera_connected()

        assert result is True
