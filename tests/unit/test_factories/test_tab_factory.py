"""
Tests for TabFactory

Unit tests for TabFactory component.
"""

import pytest
from unittest.mock import Mock


class TestTabFactory:
    """Test cases for TabFactory."""

    @pytest.fixture
    def controller(self):
        """Mock controller."""
        controller = Mock()
        controller.read_position = Mock(return_value=0.0)
        return controller

    @pytest.fixture
    def config(self):
        """Mock config manager."""
        config = Mock()
        config.get = Mock(return_value="192.168.1.5")
        return config

    @pytest.fixture
    def stencil_tracker(self):
        """Mock stencil tracker."""
        return Mock()

    @pytest.fixture
    def main_window(self):
        """Mock main window."""
        window = Mock()
        window.statusBar = Mock()
        window.statusBar().showMessage = Mock()
        return window

    @pytest.fixture
    def tab_factory(self, controller, config, stencil_tracker, main_window):
        """Create TabFactory instance."""
        from consumo_lib.factories.tab_factory import TabFactory

        return TabFactory(
            controller,
            config,
            stencil_tracker,
            main_window
        )

    def test_init(self, tab_factory):
        """Test TabFactory initialization."""
        assert tab_factory.controller is not None
        assert tab_factory.config is not None
        assert tab_factory.stencil_tracker is not None
        assert tab_factory.main_window is not None

    @pytest.mark.skip("Requer parent QWidget real, não Mock")
    def test_create_cnc_control_tab(self, tab_factory):
        """Test CNC control tab creation."""
        tab = tab_factory.create_cnc_control_tab()

        assert tab is not None
        assert hasattr(tab, 'camera_preview') or hasattr(tab, 'movement_widget')

    @pytest.mark.skip("Requer parent QWidget real, não Mock")
    def test_create_tension_tab(self, tab_factory):
        """Test tension tab creation."""
        tab = tab_factory.create_tension_tab()

        assert tab is not None
        assert hasattr(tab, 'visualization')

    @pytest.mark.skip("Requer parent QWidget real, não Mock")
    def test_create_tracking_tab(self, tab_factory):
        """Test tracking tab creation."""
        tab = tab_factory.create_tracking_tab()

        assert tab is not None
        assert hasattr(tab, 'stencil_identification')
