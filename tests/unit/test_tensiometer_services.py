"""
Unit Tests for Tensiometer Services

Tests for GridCalculationService and MeasurementAnalysisService.
These services are 100% testable without PyQt6 or hardware dependencies.

Track: solid_refactoring_phase1_20260114 - Phase 1, Task 1.10
Created: 2026-01-14
"""

import pytest
import numpy as np
from datetime import datetime
from pathlib import Path

from aoi_lib.tensiometer.models import (
    GridPoint,
    TensionMeasurement,
    GridParameters,
    MeasurementSession,
    TensionUnit
)
from aoi_lib.tensiometer.measurement_service import (
    GridCalculationService,
    MeasurementAnalysisService,
    ValidationError
)


# ==================== GRID POINT MODEL TESTS ====================

class TestGridPoint:
    """Test GridPoint dataclass."""

    def test_grid_point_creation(self):
        """Test basic GridPoint creation."""
        point = GridPoint(x=10.0, y=20.0, index=0, grid_position=(0, 0))

        assert point.x == 10.0
        assert point.y == 20.0
        assert point.index == 0
        assert point.grid_position == (0, 0)

    def test_grid_point_coordinates_property(self):
        """Test coordinates property returns tuple."""
        point = GridPoint(x=10.5, y=20.7, index=0)

        coords = point.coordinates
        assert coords == (10.5, 20.7)
        assert isinstance(coords, tuple)

    def test_grid_point_to_dict(self):
        """Test serialization to dictionary."""
        point = GridPoint(x=10.0, y=20.0, index=5, grid_position=(1, 2))

        result = point.to_dict()

        assert result['x'] == 10.0
        assert result['y'] == 20.0
        assert result['index'] == 5
        assert result['grid_position'] == [1, 2]

    def test_grid_point_equality(self):
        """Test GridPoint equality."""
        point1 = GridPoint(x=10.0, y=20.0, index=0)
        point2 = GridPoint(x=10.0, y=20.0, index=0)
        point3 = GridPoint(x=15.0, y=20.0, index=0)

        assert point1 == point2
        assert point1 != point3


# ==================== TENSION MEASUREMENT MODEL TESTS ====================

class TestTensionMeasurement:
    """Test TensionMeasurement dataclass."""

    def test_measurement_creation(self):
        """Test basic measurement creation."""
        point = GridPoint(x=10.0, y=20.0, index=0)
        measurement = TensionMeasurement(
            point=point,
            z_height=5.0,
            tension_value="35.50",
            unit=TensionUnit.N_CM2
        )

        assert measurement.point == point
        assert measurement.z_height == 5.0
        assert measurement.tension_value == "35.50"
        assert measurement.unit == TensionUnit.N_CM2

    def test_measurement_parsing_on_creation(self):
        """Test automatic value parsing on creation."""
        point = GridPoint(x=10.0, y=20.0, index=0)
        measurement = TensionMeasurement(
            point=point,
            z_height=5.0,
            tension_value="42.75"
        )

        assert measurement.parsed_value == 42.75
        assert measurement.is_valid

    def test_measurement_invalid_value(self):
        """Test measurement with invalid value."""
        point = GridPoint(x=10.0, y=20.0, index=0)
        measurement = TensionMeasurement(
            point=point,
            z_height=5.0,
            tension_value="invalid"
        )

        assert measurement.parsed_value is None
        assert not measurement.is_valid

    def test_measurement_to_dict(self):
        """Test serialization to dictionary."""
        point = GridPoint(x=10.0, y=20.0, index=0)
        measurement = TensionMeasurement(
            point=point,
            z_height=5.0,
            tension_value="35.50"
        )

        result = measurement.to_dict()

        assert result['x'] == 10.0
        assert result['y'] == 20.0
        assert result['z'] == 5.0
        assert result['tension'] == "35.50"
        assert 'timestamp' in result


# ==================== GRID PARAMETERS MODEL TESTS ====================

class TestGridParameters:
    """Test GridParameters dataclass."""

    def test_parameters_creation(self):
        """Test basic parameters creation."""
        params = GridParameters(
            start_point=(0.0, 0.0),
            end_point=(100.0, 100.0),
            grid_size=3,
            z_height=5.0,
            z_move=10.0
        )

        assert params.start_point == (0.0, 0.0)
        assert params.end_point == (100.0, 100.0)
        assert params.grid_size == 3
        assert params.z_height == 5.0
        assert params.z_move == 10.0


# ==================== MEASUREMENT SESSION MODEL TESTS ====================

class TestMeasurementSession:
    """Test MeasurementSession dataclass."""

    def test_session_creation(self):
        """Test basic session creation."""
        params = GridParameters(
            start_point=(0.0, 0.0),
            end_point=(100.0, 100.0),
            grid_size=3,
            z_height=5.0,
            z_move=10.0
        )
        session = MeasurementSession(
            parameters=params,
            measurements=[],
            user_feed=1000.0,
            stabilization_time_ms=500
        )

        assert session.parameters == params
        assert len(session.measurements) == 0
        assert session.user_feed == 1000.0
        assert session.stabilization_time_ms == 500

    def test_add_measurement(self):
        """Test adding measurement to session."""
        params = GridParameters(
            start_point=(0.0, 0.0),
            end_point=(100.0, 100.0),
            grid_size=3,
            z_height=5.0,
            z_move=10.0
        )
        session = MeasurementSession(parameters=params, measurements=[])

        point = GridPoint(x=10.0, y=20.0, index=0)
        measurement = TensionMeasurement(
            point=point,
            z_height=5.0,
            tension_value="35.50"
        )

        session.add_measurement(measurement)

        assert len(session.measurements) == 1
        assert session.measurements[0] == measurement

    def test_valid_measurements_property(self):
        """Test filtering valid measurements."""
        params = GridParameters(
            start_point=(0.0, 0.0),
            end_point=(100.0, 100.0),
            grid_size=3,
            z_height=5.0,
            z_move=10.0
        )
        session = MeasurementSession(parameters=params, measurements=[])

        # Add valid measurement
        point1 = GridPoint(x=0.0, y=0.0, index=0)
        session.add_measurement(TensionMeasurement(
            point=point1, z_height=5.0, tension_value="35.50"
        ))

        # Add invalid measurement
        point2 = GridPoint(x=10.0, y=10.0, index=1)
        session.add_measurement(TensionMeasurement(
            point=point2, z_height=5.0, tension_value="invalid"
        ))

        valid = session.valid_measurements
        assert len(valid) == 1
        assert valid[0].tension_value == "35.50"

    def test_average_tension(self):
        """Test calculating average tension."""
        params = GridParameters(
            start_point=(0.0, 0.0),
            end_point=(100.0, 100.0),
            grid_size=3,
            z_height=5.0,
            z_move=10.0
        )
        session = MeasurementSession(parameters=params, measurements=[])

        # Add measurements
        for i in range(3):
            point = GridPoint(x=float(i * 10), y=0.0, index=i)
            session.add_measurement(TensionMeasurement(
                point=point, z_height=5.0, tension_value=f"{30.0 + i}.00"
            ))

        avg = session.average_tension
        assert avg == 31.0  # (30 + 31 + 32) / 3

    def test_complete_session(self):
        """Test completing session."""
        params = GridParameters(
            start_point=(0.0, 0.0),
            end_point=(100.0, 100.0),
            grid_size=3,
            z_height=5.0,
            z_move=10.0
        )
        session = MeasurementSession(parameters=params, measurements=[])

        assert session.end_time is None
        assert session.duration_seconds is None

        session.complete_session()

        assert session.end_time is not None
        assert session.duration_seconds is not None
        assert session.duration_seconds >= 0


# ==================== GRID CALCULATION SERVICE TESTS ====================

class TestGridCalculationService:
    """Test GridCalculationService."""

    def test_calculate_grid_points_2x2(self):
        """Test grid calculation for 2x2 grid."""
        params = GridParameters(
            start_point=(0.0, 0.0),
            end_point=(100.0, 100.0),
            grid_size=2,
            z_height=5.0,
            z_move=10.0
        )

        points = GridCalculationService.calculate_grid_points(params)

        assert len(points) == 4  # 2x2 = 4 points

        # Check first point (bottom-left)
        assert points[0].x == 0.0
        assert points[0].y == 0.0
        assert points[0].index == 0

        # Check that all corners exist (zig-zag pattern changes order)
        coords = [(p.x, p.y) for p in points]
        assert (0.0, 0.0) in coords  # Bottom-left
        assert (100.0, 0.0) in coords  # Bottom-right
        assert (0.0, 100.0) in coords  # Top-left
        assert (100.0, 100.0) in coords  # Top-right

    def test_calculate_grid_points_3x3(self):
        """Test grid calculation for 3x3 grid."""
        params = GridParameters(
            start_point=(0.0, 0.0),
            end_point=(100.0, 100.0),
            grid_size=3,
            z_height=5.0,
            z_move=10.0
        )

        points = GridCalculationService.calculate_grid_points(params)

        assert len(points) == 9  # 3x3 = 9 points

        # Check corners
        corners = [points[0], points[2], points[6], points[8]]
        corner_coords = [(p.x, p.y) for p in corners]

        assert (0.0, 0.0) in corner_coords  # Bottom-left
        assert (100.0, 0.0) in corner_coords  # Bottom-right
        assert (0.0, 100.0) in corner_coords  # Top-left
        assert (100.0, 100.0) in corner_coords  # Top-right

    def test_zig_zag_pattern(self):
        """Test zig-zag pattern for CNC optimization."""
        params = GridParameters(
            start_point=(0.0, 0.0),
            end_point=(100.0, 100.0),
            grid_size=3,
            z_height=5.0,
            z_move=10.0
        )

        points = GridCalculationService.calculate_grid_points(params)

        # Row 0 (bottom): X increases left to right
        row0_start = points[0]
        row0_end = points[2]
        assert row0_start.x < row0_end.x

        # Row 1 (middle): X decreases right to left (zig-zag)
        row1_start = points[3]
        row1_end = points[5]
        assert row1_start.x > row1_end.x

        # Row 2 (top): X increases left to right
        row2_start = points[6]
        row2_end = points[8]
        assert row2_start.x < row2_end.x

    def test_validate_parameters_valid(self):
        """Test validation with valid parameters."""
        params = GridParameters(
            start_point=(0.0, 0.0),
            end_point=(100.0, 100.0),
            grid_size=5,
            z_height=5.0,
            z_move=10.0
        )

        # Should not raise
        GridCalculationService.validate_parameters(params)

    def test_validate_parameters_grid_too_small(self):
        """Test validation fails for grid size < 2."""
        params = GridParameters(
            start_point=(0.0, 0.0),
            end_point=(100.0, 100.0),
            grid_size=1,  # Invalid
            z_height=5.0,
            z_move=10.0
        )

        with pytest.raises(ValidationError) as exc_info:
            GridCalculationService.validate_parameters(params)

        assert "Grid size deve ser >= 2" in str(exc_info.value)

    def test_validate_parameters_grid_too_large(self):
        """Test validation fails for grid size > 20."""
        params = GridParameters(
            start_point=(0.0, 0.0),
            end_point=(100.0, 100.0),
            grid_size=25,  # Invalid
            z_height=5.0,
            z_move=10.0
        )

        with pytest.raises(ValidationError) as exc_info:
            GridCalculationService.validate_parameters(params)

        assert "Grid size muito grande" in str(exc_info.value)

    def test_validate_parameters_z_move_too_low(self):
        """Test validation fails when Z move <= Z height."""
        params = GridParameters(
            start_point=(0.0, 0.0),
            end_point=(100.0, 100.0),
            grid_size=5,
            z_height=5.0,
            z_move=3.0  # Invalid (should be > 5.0)
        )

        with pytest.raises(ValidationError) as exc_info:
            GridCalculationService.validate_parameters(params)

        assert "Altura Z de movimento deve ser maior" in str(exc_info.value)

    def test_get_grid_statistics(self):
        """Test grid statistics calculation."""
        params = GridParameters(
            start_point=(0.0, 0.0),
            end_point=(100.0, 100.0),
            grid_size=5,
            z_height=5.0,
            z_move=10.0
        )

        points = GridCalculationService.calculate_grid_points(params)
        stats = GridCalculationService.get_grid_statistics(points)

        assert stats['grid_size'] == 5
        assert stats['total_points'] == 25  # 5x5
        assert stats['total_distance_mm'] > 0
        assert 'min_x' in stats
        assert 'max_x' in stats
        assert 'min_y' in stats
        assert 'max_y' in stats


# ==================== MEASUREMENT ANALYSIS SERVICE TESTS ====================

class TestMeasurementAnalysisService:
    """Test MeasurementAnalysisService."""

    @pytest.fixture
    def sample_session(self):
        """Create a sample measurement session for testing."""
        params = GridParameters(
            start_point=(0.0, 0.0),
            end_point=(100.0, 100.0),
            grid_size=3,
            z_height=5.0,
            z_move=10.0
        )
        session = MeasurementSession(
            parameters=params,
            measurements=[],
            user_feed=1000.0,
            stabilization_time_ms=500
        )

        # Add measurements with values around 35 N/cm²
        values = [34.5, 35.0, 35.5, 36.0, 34.0, 35.0, 35.5, 34.5, 35.0]
        for i, value in enumerate(values):
            point = GridPoint(x=float(i * 10), y=0.0, index=i)
            session.add_measurement(TensionMeasurement(
                point=point,
                z_height=5.0,
                tension_value=f"{value:.2f}"
            ))

        session.complete_session()
        return session

    def test_analyze_session_basic(self, sample_session):
        """Test basic session analysis."""
        analysis = MeasurementAnalysisService.analyze_session(sample_session)

        assert 'statistics' in analysis
        assert 'classification' in analysis
        assert 'outliers' in analysis

        stats = analysis['statistics']
        assert 'mean' in stats
        assert 'median' in stats
        assert 'std' in stats
        assert 'min' in stats
        assert 'max' in stats
        assert 'count' in stats

    def test_analyze_session_statistics(self, sample_session):
        """Test statistical calculations."""
        analysis = MeasurementAnalysisService.analyze_session(sample_session)
        stats = analysis['statistics']

        expected_mean = 35.0  # Average of 34.5, 35.0, 35.5, etc.
        assert abs(stats['mean'] - expected_mean) < 0.1

        assert stats['count'] == 9
        assert stats['min'] < stats['mean']
        assert stats['max'] > stats['mean']
        assert stats['std'] >= 0

    def test_classify_tension_ok(self):
        """Test classification for OK tension."""
        classification = MeasurementAnalysisService._classify_tension(
            mean=35.0,
            std=2.0
        )

        assert classification['category'] == 'OK'
        assert classification['color'] == 'GREEN'
        assert 'adequada' in classification['message'].lower()

    def test_classify_tension_critical_low(self):
        """Test classification for critically low tension."""
        classification = MeasurementAnalysisService._classify_tension(
            mean=15.0,  # Too low
            std=1.0
        )

        assert classification['category'] == 'CRITICAL'
        assert classification['color'] == 'RED'
        assert 'muito baixa' in classification['message'].lower()

    def test_classify_tension_warning_high(self):
        """Test classification for high tension."""
        classification = MeasurementAnalysisService._classify_tension(
            mean=55.0,  # Too high
            std=1.0
        )

        assert classification['category'] == 'WARNING'
        assert classification['color'] == 'ORANGE'
        assert 'muito alta' in classification['message'].lower()

    def test_classify_tension_warning_non_uniform(self):
        """Test classification for non-uniform tension."""
        # Mean OK but high coefficient of variation (>15%)
        classification = MeasurementAnalysisService._classify_tension(
            mean=35.0,
            std=8.0  # CV = (8/35)*100 ≈ 23%
        )

        assert classification['category'] == 'WARNING'
        assert classification['color'] == 'YELLOW'
        assert 'não uniforme' in classification['message'].lower()

    def test_detect_outliers(self, sample_session):
        """Test outlier detection."""
        # Add an outlier
        outlier_point = GridPoint(x=999.0, y=999.0, index=9)
        sample_session.add_measurement(TensionMeasurement(
            point=outlier_point,
            z_height=5.0,
            tension_value="50.00"  # Much higher than others
        ))

        analysis = MeasurementAnalysisService.analyze_session(sample_session)
        outliers = analysis['outliers']

        assert len(outliers) > 0
        # Check that outlier has high deviation
        assert outliers[0]['deviation'] > 0

    def test_generate_report(self, sample_session):
        """Test report generation."""
        report = MeasurementAnalysisService.generate_report(sample_session)

        assert isinstance(report, str)
        assert len(report) > 0

        # Check key sections
        assert 'Sessão de Medição de Tensão' in report
        assert 'Estatísticas' in report
        assert 'Classificação' in report
        assert 'N/cm²' in report


# ==================== INTEGRATION TESTS ====================

class TestIntegration:
    """Integration tests for complete workflow."""

    def test_complete_measurement_workflow(self):
        """Test complete workflow from parameters to analysis."""
        # 1. Create parameters
        params = GridParameters(
            start_point=(0.0, 0.0),
            end_point=(50.0, 50.0),
            grid_size=2,
            z_height=5.0,
            z_move=10.0
        )

        # 2. Calculate grid
        points = GridCalculationService.calculate_grid_points(params)
        assert len(points) == 4

        # 3. Create session
        session = MeasurementSession(parameters=params, measurements=[])

        # 4. Simulate measurements
        for point in points:
            measurement = TensionMeasurement(
                point=point,
                z_height=5.0,
                tension_value="35.00"
            )
            session.add_measurement(measurement)

        # 5. Complete session
        session.complete_session()

        # 6. Analyze results
        analysis = MeasurementAnalysisService.analyze_session(session)

        assert analysis['statistics']['count'] == 4
        assert analysis['classification']['category'] == 'OK'

        # 7. Generate report
        report = MeasurementAnalysisService.generate_report(session)
        assert '4 pontos' in report
