"""
Tests for SequenceManager

Unit tests for SequenceManager component.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path


class TestSequenceManager:
    """Test cases for SequenceManager."""

    @pytest.fixture
    def sequence_controller(self):
        """Mock sequence controller."""
        controller = Mock()
        controller.run_sequence = Mock(return_value=True)
        controller.stop_sequence = Mock(return_value=True)
        return controller

    @pytest.fixture
    def main_window(self):
        """Mock main window."""
        window = Mock()
        window.position_list_widget = Mock()
        window.position_list_widget.get_positions = Mock(return_value=[])
        window.statusBar = Mock()
        window.statusBar().showMessage = Mock()
        return window

    @pytest.fixture
    def sequence_manager(self, sequence_controller, main_window):
        """Create SequenceManager instance."""
        from consumo_lib.managers.sequence_manager import SequenceManager

        return SequenceManager(
            sequence_controller,
            main_window
        )

    def test_init(self, sequence_manager):
        """Test SequenceManager initialization."""
        assert sequence_manager.sequence_controller is not None
        assert sequence_manager.main_window is not None
        assert sequence_manager.is_running_sequence is False
        assert sequence_manager.current_sequence == []

    def test_create_sequence(self, sequence_manager):
        """Test sequence creation."""
        positions = [(10.0, 20.0, 5.0), (30.0, 40.0, 5.0)]

        result = sequence_manager.create_sequence(positions)

        assert result is True
        assert sequence_manager.current_sequence == positions

    def test_create_sequence_from_registry_empty(self, sequence_manager):
        """Test sequence creation from empty registry."""
        sequence_manager.main_window.position_list_widget.get_positions = Mock(
            return_value=[]
        )

        result = sequence_manager.create_sequence_from_registry()

        assert result is False

    def test_run_sequence_success(self, sequence_manager):
        """Test successful sequence execution."""
        sequence_manager.create_sequence([(10.0, 20.0, 5.0)])

        result = sequence_manager.run_sequence()

        assert result is True
        assert sequence_manager.is_running_sequence is True

    def test_run_sequence_empty(self, sequence_manager):
        """Test running empty sequence."""
        result = sequence_manager.run_sequence()

        assert result is False

    def test_stop_sequence(self, sequence_manager):
        """Test stopping sequence."""
        sequence_manager.create_sequence([(10.0, 20.0, 5.0)])
        sequence_manager.run_sequence()

        result = sequence_manager.stop_sequence()

        assert result is True
        assert sequence_manager.is_running_sequence is False

    def test_save_program(self, sequence_manager, tmp_path):
        """Test saving program to JSON."""
        import json

        sequence_manager.create_sequence([(10.0, 20.0, 5.0)])
        filepath = tmp_path / "test_program.json"

        result = sequence_manager.save_program(str(filepath))

        assert result is True
        assert filepath.exists()

        # Verify content
        with open(filepath, 'r') as f:
            data = json.load(f)
            assert data['total_positions'] == 1
            assert data['positions'][0] == [10.0, 20.0, 5.0]

    def test_save_program_empty(self, sequence_manager, tmp_path):
        """Test saving empty program."""
        filepath = tmp_path / "test_program.json"

        result = sequence_manager.save_program(str(filepath))

        assert result is False

    def test_load_program(self, sequence_manager, tmp_path):
        """Test loading program from JSON."""
        import json

        # Create test file
        filepath = tmp_path / "test_program.json"
        data = {
            'positions': [[10.0, 20.0, 5.0], [30.0, 40.0, 5.0]],
            'total_positions': 2
        }
        with open(filepath, 'w') as f:
            json.dump(data, f)

        result = sequence_manager.load_program(str(filepath))

        assert result is True
        assert len(sequence_manager.current_sequence) == 2
        assert sequence_manager.current_sequence[0] == [10.0, 20.0, 5.0]

    def test_save_gcode(self, sequence_manager, tmp_path):
        """Test exporting sequence as G-code."""
        sequence_manager.create_sequence([(10.0, 20.0, 5.0)])
        filepath = tmp_path / "test_program.gcode"

        result = sequence_manager.save_gcode(str(filepath))

        assert result is True
        assert filepath.exists()

        # Verify content
        content = filepath.read_text()
        assert "G0 X10.000 Y20.000 Z5.000" in content

    def test_save_gcode_empty(self, sequence_manager, tmp_path):
        """Test exporting empty sequence as G-code."""
        filepath = tmp_path / "test_program.gcode"

        result = sequence_manager.save_gcode(str(filepath))

        assert result is False
