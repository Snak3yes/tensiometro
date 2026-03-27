from aoi_lib.tensiometer.measurement_service import (
    GridCalculationService,
    MeasurementAnalysisService,
    ValidationError,
)
from aoi_lib.tensiometer.models import (
    GridParameters,
    GridPoint,
    MeasurementSession,
    TensionMeasurement,
)


def _build_measurement(value, index, row, col):
    return TensionMeasurement(
        point=GridPoint(x=float(col), y=float(row), index=index, grid_position=(row, col)),
        z_height=5.0,
        tension_value=str(value),
    )


def test_calculate_grid_points_generates_zig_zag_order():
    parameters = GridParameters(
        start_point=(0.0, 0.0),
        end_point=(20.0, 10.0),
        grid_size=3,
        z_height=5.0,
        z_move=10.0,
    )

    points = GridCalculationService.calculate_grid_points(parameters)

    assert [(point.x, point.y) for point in points] == [
        (0.0, 0.0),
        (10.0, 0.0),
        (20.0, 0.0),
        (20.0, 5.0),
        (10.0, 5.0),
        (0.0, 5.0),
        (0.0, 10.0),
        (10.0, 10.0),
        (20.0, 10.0),
    ]


def test_validate_parameters_rejects_large_grid_and_invalid_z_motion():
    parameters = GridParameters(
        start_point=(0.0, 0.0),
        end_point=(100.0, 50.0),
        grid_size=21,
        z_height=5.0,
        z_move=4.0,
    )

    try:
        GridCalculationService.validate_parameters(parameters)
    except ValidationError as exc:
        message = str(exc)
    else:
        raise AssertionError("ValidationError was expected")

    assert "Grid size muito grande" in message
    assert "Altura Z de movimento (4.0) deve ser maior" in message


def test_get_grid_statistics_returns_distance_and_bounds():
    parameters = GridParameters(
        start_point=(0.0, 0.0),
        end_point=(10.0, 10.0),
        grid_size=2,
        z_height=5.0,
        z_move=10.0,
    )

    points = GridCalculationService.calculate_grid_points(parameters)
    stats = GridCalculationService.get_grid_statistics(points)

    assert stats["total_points"] == 4
    assert stats["bounds"] == {"x_min": 0.0, "x_max": 10.0, "y_min": 0.0, "y_max": 10.0}
    assert stats["total_distance_mm"] == 30.0
    assert stats["avg_distance_mm"] == 10.0


def test_analyze_session_classifies_uniform_measurements_as_ok():
    session = MeasurementSession(
        parameters=GridParameters(
            start_point=(0.0, 0.0),
            end_point=(10.0, 10.0),
            grid_size=2,
            z_height=5.0,
            z_move=10.0,
        )
    )
    for index, value in enumerate([30.0, 31.0, 29.5, 30.5]):
        session.add_measurement(_build_measurement(value, index, index // 2, index % 2))

    analysis = MeasurementAnalysisService.analyze_session(session)

    assert analysis["status"] == "success"
    assert analysis["classification"]["category"] == "OK"
    assert analysis["statistics"]["mean"] == 30.25


def test_analyze_session_handles_invalid_measurements_only():
    session = MeasurementSession(
        parameters=GridParameters(
            start_point=(0.0, 0.0),
            end_point=(10.0, 10.0),
            grid_size=2,
            z_height=5.0,
            z_move=10.0,
        )
    )
    session.add_measurement(_build_measurement("erro", 0, 0, 0))

    analysis = MeasurementAnalysisService.analyze_session(session)

    assert analysis["status"] == "no_valid_data"
    assert analysis["total_measurements"] == 1


def test_generate_report_includes_classification_category():
    session = MeasurementSession(
        parameters=GridParameters(
            start_point=(0.0, 0.0),
            end_point=(10.0, 10.0),
            grid_size=2,
            z_height=5.0,
            z_move=10.0,
        )
    )
    for index, value in enumerate([10.0, 11.0, 12.0, 13.0]):
        session.add_measurement(_build_measurement(value, index, index // 2, index % 2))

    report = MeasurementAnalysisService.generate_report(session)

    assert "CRITICAL" in report
    assert "10.0" in report
