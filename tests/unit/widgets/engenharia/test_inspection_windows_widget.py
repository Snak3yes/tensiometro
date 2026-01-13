"""
Unit tests for InspectionWindowsWidget.

Tests the inspection windows configuration widget including:
- Data models (InspectionWindow, WindowConfig, WindowGroup, WindowLibrary)
- Auto-grouping logic
- Configuration management
- Library operations
"""

import pytest
import logging
from pathlib import Path
from tempfile import TemporaryDirectory
from dataclasses import asdict

from consumo_lib.models.inspection_window import (
    InspectionWindow,
    WindowConfig,
    WindowGroup,
    WindowLibrary,
    WindowStatus,
    BinarizationMethod,
    PreprocessMethod,
    GroupingCriteria,
    create_groups_from_windows,
    create_default_config
)

logger = logging.getLogger(__name__)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_config():
    """Create sample WindowConfig."""
    return WindowConfig(
        ok_threshold=90.0,
        partial_threshold=70.0,
        binarization_method=BinarizationMethod.OTSU,
        preprocess_method=PreprocessMethod.BLUR
    )


@pytest.fixture
def sample_windows():
    """Create list of sample InspectionWindow objects."""
    windows = [
        InspectionWindow(
            id=1,
            x_mm=10.0,
            y_mm=20.0,
            kind="circle",
            dimensions={"diameter_mm": 0.5}
        ),
        InspectionWindow(
            id=2,
            x_mm=15.0,
            y_mm=25.0,
            kind="circle",
            dimensions={"diameter_mm": 0.5}
        ),
        InspectionWindow(
            id=3,
            x_mm=20.0,
            y_mm=30.0,
            kind="circle",
            dimensions={"diameter_mm": 0.8}
        ),
        InspectionWindow(
            id=4,
            x_mm=25.0,
            y_mm=35.0,
            kind="rect",
            dimensions={"width_mm": 1.0, "height_mm": 0.5}
        ),
        InspectionWindow(
            id=5,
            x_mm=30.0,
            y_mm=40.0,
            kind="rect",
            dimensions={"width_mm": 1.0, "height_mm": 0.5}
        ),
    ]
    return windows


# ============================================================================
# TEST: WindowConfig
# ============================================================================

class TestWindowConfig:
    """Test WindowConfig model."""

    def test_default_config(self):
        """Test default configuration creation."""
        config = create_default_config()

        assert config.ok_threshold == 90.0
        assert config.partial_threshold == 70.0
        assert config.binarization_method == BinarizationMethod.OTSU
        assert config.preprocess_method == PreprocessMethod.BLUR

    def test_validation_valid(self, sample_config):
        """Test configuration validation with valid values."""
        assert sample_config.validate() is True

    def test_validation_invalid_thresholds(self):
        """Test configuration validation with invalid thresholds."""
        config = WindowConfig(
            ok_threshold=70.0,  # Less than partial
            partial_threshold=90.0
        )
        assert config.validate() is False

    def test_validation_out_of_range(self):
        """Test configuration validation with out-of-range values."""
        config = WindowConfig(
            ok_threshold=150.0,  # > 100
            partial_threshold=50.0
        )
        assert config.validate() is False

    def test_to_dict(self, sample_config):
        """Test serialization to dictionary."""
        data = sample_config.to_dict()

        assert data["ok_threshold"] == 90.0
        assert data["partial_threshold"] == 70.0
        assert data["binarization_method"] == "otsu"
        assert data["preprocess_method"] == "blur"

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "ok_threshold": 85.0,
            "partial_threshold": 65.0,
            "binarization_method": "adaptive",
            "preprocess_method": "denoise",
            "custom_parameters": {"custom": "value"}
        }

        config = WindowConfig.from_dict(data)

        assert config.ok_threshold == 85.0
        assert config.partial_threshold == 65.0
        assert config.binarization_method == BinarizationMethod.ADAPTIVE
        assert config.preprocess_method == PreprocessMethod.DENOISE
        assert config.custom_parameters == {"custom": "value"}

    def test_string_representation(self, sample_config):
        """Test string representation."""
        str_repr = str(sample_config)

        assert "90%" in str_repr
        assert "70%" in str_repr
        assert "Otsu" in str_repr


# ============================================================================
# TEST: InspectionWindow
# ============================================================================

class TestInspectionWindow:
    """Test InspectionWindow model."""

    def test_group_key_circle(self):
        """Test group key generation for circles."""
        window = InspectionWindow(
            id=1,
            x_mm=10.0,
            y_mm=20.0,
            kind="circle",
            dimensions={"diameter_mm": 0.5}
        )

        assert window.group_key == "circle_0.50mm"

    def test_group_key_rect(self):
        """Test group key generation for rectangles."""
        window = InspectionWindow(
            id=1,
            x_mm=10.0,
            y_mm=20.0,
            kind="rect",
            dimensions={"width_mm": 1.0, "height_mm": 0.5}
        )

        assert window.group_key == "rect_1.00x0.50mm"

    def test_group_key_oval(self):
        """Test group key generation for ovals."""
        window = InspectionWindow(
            id=1,
            x_mm=10.0,
            y_mm=20.0,
            kind="oval",
            dimensions={"width_mm": 0.8, "height_mm": 1.2}
        )

        assert window.group_key == "oval_0.80x1.20mm"

    def test_group_key_unknown(self):
        """Test group key generation for unknown types."""
        window = InspectionWindow(
            id=1,
            x_mm=10.0,
            y_mm=20.0,
            kind="macro",
            dimensions={}
        )

        assert "macro" in window.group_key
        assert "1" in window.group_key

    def test_to_dict(self):
        """Test serialization to dictionary."""
        window = InspectionWindow(
            id=1,
            x_mm=10.0,
            y_mm=20.0,
            kind="circle",
            dimensions={"diameter_mm": 0.5},
            config=WindowConfig(ok_threshold=85.0),
            status=WindowStatus.CONFIGURED
        )

        data = window.to_dict()

        assert data["id"] == 1
        assert data["x_mm"] == 10.0
        assert data["y_mm"] == 20.0
        assert data["kind"] == "circle"
        assert data["config"]["ok_threshold"] == 85.0
        assert data["status"] == "configured"


# ============================================================================
# TEST: WindowGroup
# ============================================================================

class TestWindowGroup:
    """Test WindowGroup model."""

    def test_add_window(self, sample_windows):
        """Test adding windows to group."""
        group = WindowGroup(
            name="0.5mm Circle",
            key="circle_0.50mm"
        )

        group.add_window(sample_windows[0])
        group.add_window(sample_windows[1])

        assert group.count == 2

    def test_add_duplicate_window(self, sample_windows):
        """Test that duplicate windows are not added."""
        group = WindowGroup(
            name="0.5mm Circle",
            key="circle_0.50mm"
        )

        group.add_window(sample_windows[0])
        group.add_window(sample_windows[0])  # Same window

        assert group.count == 1

    def test_get_window_by_id(self, sample_windows):
        """Test retrieving window by ID."""
        group = WindowGroup(
            name="0.5mm Circle",
            key="circle_0.50mm"
        )

        group.add_window(sample_windows[0])

        window = group.get_window_by_id(1)
        assert window is not None
        assert window.id == 1

    def test_apply_config_to_group(self, sample_windows, sample_config):
        """Test applying configuration to group."""
        group = WindowGroup(
            name="0.5mm Circle",
            key="circle_0.50mm"
        )

        group.add_window(sample_windows[0])
        group.add_window(sample_windows[1])

        group.apply_config_to_group(sample_config, confirm=True)

        assert group.config == sample_config
        assert group.status == WindowStatus.CONFIRMED
        assert sample_windows[0].config == sample_config
        assert sample_windows[0].status == WindowStatus.CONFIRMED

    def test_apply_config_with_exception(self, sample_windows, sample_config):
        """Test applying config with exceptions."""
        group = WindowGroup(
            name="0.5mm Circle",
            key="circle_0.50mm"
        )

        group.add_window(sample_windows[0])
        group.add_window(sample_windows[1])

        # Mark first window as exception
        sample_windows[0].is_exception = True
        group.exceptions = [1]

        group.apply_config_to_group(sample_config)

        # Exception window should not be updated
        assert sample_windows[0].config is None
        assert sample_windows[1].config == sample_config

    def test_properties(self, sample_windows):
        """Test group properties."""
        group = WindowGroup(
            name="0.5mm Circle",
            key="circle_0.50mm"
        )

        for window in sample_windows[:3]:
            group.add_window(window)

        # Mark first as exception
        sample_windows[0].is_exception = True
        group.exceptions = [1]

        assert group.count == 3
        assert group.exception_count == 1
        assert group.standard_count == 2


# ============================================================================
# TEST: WindowLibrary
# ============================================================================

class TestWindowLibrary:
    """Test WindowLibrary model."""

    def test_add_config(self, sample_config):
        """Test adding configuration to library."""
        library = WindowLibrary()
        library.add_config("circle_0.50mm", sample_config)

        assert library.has_config("circle_0.50mm")
        assert library.get_config("circle_0.50mm") == sample_config

    def test_remove_config(self, sample_config):
        """Test removing configuration from library."""
        library = WindowLibrary()
        library.add_config("circle_0.50mm", sample_config)
        library.remove_config("circle_0.50mm")

        assert not library.has_config("circle_0.50mm")

    def test_suggest_config_exact_match(self, sample_config):
        """Test configuration suggestion with exact match."""
        library = WindowLibrary()
        library.add_config("circle_0.50mm", sample_config)

        suggested = library.suggest_config("circle_0.50mm")

        assert suggested == sample_config

    def test_suggest_config_fuzzy_match(self, sample_config):
        """Test configuration suggestion with fuzzy match."""
        library = WindowLibrary()
        library.add_config("circle_0.50mm", sample_config)

        # Similar dimension (within tolerance)
        suggested = library.suggest_config("circle_0.51mm")

        assert suggested is not None
        assert suggested.ok_threshold == 90.0

    def test_suggest_config_no_match(self, sample_config):
        """Test configuration suggestion with no match."""
        library = WindowLibrary()
        library.add_config("circle_0.50mm", sample_config)

        # Very different dimension
        suggested = library.suggest_config("circle_2.00mm")

        # Should not suggest (too different)
        assert suggested is None or suggested.ok_threshold != 90.0

    def test_save_and_load(self, sample_config):
        """Test saving and loading library."""
        with TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "library.json"

            # Create and save library
            library = WindowLibrary()
            library.add_config("circle_0.50mm", sample_config)
            library.save(filepath)

            # Load library
            loaded = WindowLibrary.load(filepath)

            assert loaded.has_config("circle_0.50mm")
            loaded_config = loaded.get_config("circle_0.50mm")
            assert loaded_config.ok_threshold == sample_config.ok_threshold

    def test_load_nonexistent_file(self):
        """Test loading from nonexistent file."""
        library = WindowLibrary.load(Path("nonexistent.json"))

        assert len(library.configs) == 0

    def test_to_dict(self, sample_config):
        """Test serialization to dictionary."""
        library = WindowLibrary()
        library.add_config("circle_0.50mm", sample_config)

        data = library.to_dict()

        assert "circle_0.50mm" in data
        assert data["circle_0.50mm"]["ok_threshold"] == 90.0

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "circle_0.50mm": {
                "ok_threshold": 90.0,
                "partial_threshold": 70.0,
                "binarization_method": "otsu",
                "preprocess_method": "blur",
                "custom_parameters": {}
            }
        }

        library = WindowLibrary.from_dict(data)

        assert library.has_config("circle_0.50mm")
        config = library.get_config("circle_0.50mm")
        assert config.ok_threshold == 90.0


# ============================================================================
# TEST: Grouping Functions
# ============================================================================

class TestGroupingFunctions:
    """Test grouping functions."""

    def test_create_groups_exact_dimensions(self, sample_windows):
        """Test grouping by exact dimensions."""
        groups = create_groups_from_windows(
            sample_windows,
            criteria=GroupingCriteria.EXACT_DIMENSIONS
        )

        # Should create 3 groups: 0.5mm circle, 0.8mm circle, 1.0x0.5mm rect
        assert len(groups) == 3

        # Check 0.5mm circle group has 2 windows
        circle_05_group = next(g for g in groups if "0.50mm" in g.key and "circle" in g.key)
        assert circle_05_group.count == 2

        # Check rect group has 2 windows
        rect_group = next(g for g in groups if "rect" in g.key)
        assert rect_group.count == 2

    def test_create_groups_with_tolerance(self):
        """Test grouping with tolerance."""
        windows = [
            InspectionWindow(
                id=i,
                x_mm=float(i * 5),
                y_mm=20.0,
                kind="circle",
                dimensions={"diameter_mm": 0.5 + (i * 0.005)}  # 0.500, 0.505, 0.510
            )
            for i in range(3)
        ]

        groups = create_groups_from_windows(
            windows,
            criteria=GroupingCriteria.TOLERANCE,
            tolerance=0.02
        )

        # All should be grouped together (within 0.02 tolerance)
        # 0.500 -> 0.50, 0.505 -> 0.50, 0.510 -> 0.52 (rounds to nearest)
        # With tolerance 0.02, 0.505 rounds to 0.50 (round(0.505/0.02)*0.02 = round(25.25)*0.02 = 25*0.02 = 0.50)
        # Actually let's check: 0.500/0.02=25.0, 0.505/0.02=25.25->25, 0.510/0.02=25.5->26
        # So we get 2 groups: 0.50mm (2 windows) and 0.52mm (1 window)
        assert len(groups) == 2

    def test_group_names_are_readable(self, sample_windows):
        """Test that group names are human-readable."""
        groups = create_groups_from_windows(sample_windows)

        for group in groups:
            # Names should not be just technical keys
            assert "mm" in group.name or "Círculo" in group.name or "Retângulo" in group.name

    def test_empty_windows_list(self):
        """Test grouping with empty list."""
        groups = create_groups_from_windows([])

        assert len(groups) == 0


# ============================================================================
# TEST: Integration
# ============================================================================

class TestIntegration:
    """Integration tests for complete workflows."""

    def test_complete_workflow(self, sample_windows):
        """Test complete workflow: group -> configure -> save."""
        # 1. Group windows
        groups = create_groups_from_windows(sample_windows)

        # 2. Configure first group
        config = create_default_config()
        groups[0].apply_config_to_group(config, confirm=True)

        # 3. Add to library
        library = WindowLibrary()
        library.add_config(groups[0].key, config)

        # 4. Verify
        assert groups[0].status == WindowStatus.CONFIRMED
        assert library.has_config(groups[0].key)

    def test_multiple_groups_workflow(self, sample_windows):
        """Test workflow with multiple groups."""
        # Group all windows
        groups = create_groups_from_windows(sample_windows)

        # Configure each group differently
        configs = [
            WindowConfig(ok_threshold=90.0, partial_threshold=70.0),
            WindowConfig(ok_threshold=85.0, partial_threshold=65.0),
            WindowConfig(ok_threshold=95.0, partial_threshold=75.0),
        ]

        for group, config in zip(groups, configs):
            group.apply_config_to_group(config, confirm=True)

        # Verify all groups are confirmed
        assert all(g.status == WindowStatus.CONFIRMED for g in groups)

    def test_exception_workflow(self, sample_windows):
        """Test creating and managing exceptions."""
        groups = create_groups_from_windows(sample_windows[:3])  # 2 circles + 1 different

        config = create_default_config()
        groups[0].apply_config_to_group(config)

        # Mark first window as exception
        exception_config = WindowConfig(ok_threshold=95.0, partial_threshold=80.0)
        sample_windows[0].is_exception = True
        sample_windows[0].config = exception_config
        groups[0].exceptions = [1]

        # Verify counts
        assert groups[0].exception_count == 1
        assert groups[0].standard_count == 1

        # Verify configs
        assert sample_windows[0].config.ok_threshold == 95.0
        assert sample_windows[1].config.ok_threshold == 90.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
