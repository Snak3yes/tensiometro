"""
Measurement Service for Tension Measurement System

Business logic layer for tension measurement operations.
This module contains pure business logic without UI dependencies,
making it fully testable without PyQt6.

Created: 2026-01-14 (Phase 1 - SOLID Refactoring)
"""

import logging
import numpy as np
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
from .models import (
    GridPoint,
    GridParameters,
    TensionMeasurement,
    MeasurementSession,
    TensionUnit
)

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when validation of parameters fails."""
    pass


class GridCalculationService:
    """
    Service for calculating grid measurement points.

    This service contains pure business logic for:
    - Grid point generation (zig-zag pattern)
    - Parameter validation
    - Grid statistics

    All methods are pure functions without side effects,
    making them easy to test without UI dependencies.
    """

    @staticmethod
    def calculate_grid_points(parameters: GridParameters) -> List[GridPoint]:
        """
        Calculate grid points for tension measurement.

        Generates an NxN grid of points between start and end coordinates.
        Points are ordered in zig-zag pattern to optimize CNC movement.

        Args:
            parameters: GridParameters with bounds and grid size

        Returns:
            List of GridPoint objects ordered for measurement

        Raises:
            ValidationError: If parameters are invalid

        Example:
            >>> params = GridParameters(
            ...     start_point=(0, 0), end_point=(100, 100),
            ...     grid_size=3, z_height=5.0
            ... )
            >>> points = GridCalculationService.calculate_grid_points(params)
            >>> len(points)
            9
        """
        # Validate parameters
        GridCalculationService.validate_parameters(parameters)

        # Generate coordinate arrays
        x_coords = np.linspace(
            parameters.start_point[0],
            parameters.end_point[0],
            parameters.grid_size
        )
        y_coords = np.linspace(
            parameters.start_point[1],
            parameters.end_point[1],
            parameters.grid_size
        )

        # Generate grid with zig-zag pattern
        points = []
        index = 0

        for row_idx, y in enumerate(y_coords):
            # Reverse X order on alternating rows (zig-zag)
            x_values = x_coords if row_idx % 2 == 0 else x_coords[::-1]

            for col_idx, x in enumerate(x_values):
                point = GridPoint(
                    x=float(x),
                    y=float(y),
                    index=index,
                    grid_position=(row_idx, col_idx)
                )
                points.append(point)
                index += 1

        logger.info(
            f"Gerados {len(points)} pontos de medição "
            f"({parameters.grid_size}x{parameters.grid_size} grid)"
        )

        return points

    @staticmethod
    def validate_parameters(parameters: GridParameters) -> None:
        """
        Validate grid parameters.

        Args:
            parameters: GridParameters to validate

        Raises:
            ValidationError: If any parameter is invalid
        """
        errors = []

        # Validate grid size
        if parameters.grid_size < 2:
            errors.append(
                f"Grid size deve ser >= 2, recebido: {parameters.grid_size}"
            )

        if parameters.grid_size > 20:
            errors.append(
                f"Grid size muito grande: {parameters.grid_size} "
                f"(máximo recomendado: 20)"
            )

        # Validate coordinates
        sx, sy = parameters.start_point
        ex, ey = parameters.end_point

        if sx == ex and sy == ey:
            errors.append(
                "Ponto inicial e final não podem ser iguais"
            )

        # Validate Z heights
        if parameters.z_height < 0:
            errors.append(
                f"Altura Z de medição deve ser >= 0, recebido: {parameters.z_height}"
            )

        if parameters.z_move < 0:
            errors.append(
                f"Altura Z de movimento deve ser >= 0, recebido: {parameters.z_move}"
            )

        if parameters.z_move >= parameters.z_height:
            errors.append(
                f"Altura Z de movimento ({parameters.z_move}) deve ser menor "
                f"que altura de medição ({parameters.z_height})"
            )

        # Check for grid explosion (too many points)
        total_points = parameters.grid_size ** 2
        if total_points > 400:
            errors.append(
                f"Grid muito grande: {total_points} pontos "
                f"(máximo recomendado: 400 = 20x20)"
            )

        if errors:
            error_msg = "Erros de validação:\n" + "\n".join(f"  - {e}" for e in errors)
            logger.error(error_msg)
            raise ValidationError(error_msg)

        logger.debug("Parâmetros validados com sucesso")

    @staticmethod
    def get_grid_statistics(points: List[GridPoint]) -> Dict:
        """
        Calculate statistics for the measurement grid.

        Args:
            points: List of GridPoint objects

        Returns:
            Dictionary with grid statistics
        """
        if not points:
            return {
                "total_points": 0,
                "grid_size": 0,
                "bounds": {"x_min": 0, "x_max": 0, "y_min": 0, "y_max": 0},
                "total_distance": 0.0
            }

        x_values = [p.x for p in points]
        y_values = [p.y for p in points]

        # Calculate total distance between consecutive points
        total_distance = 0.0
        for i in range(len(points) - 1):
            dx = points[i + 1].x - points[i].x
            dy = points[i + 1].y - points[i].y
            distance = (dx ** 2 + dy ** 2) ** 0.5
            total_distance += distance

        return {
            "total_points": len(points),
            "grid_size": int(len(points) ** 0.5),
            "bounds": {
                "x_min": min(x_values),
                "x_max": max(x_values),
                "y_min": min(y_values),
                "y_max": max(y_values)
            },
            "total_distance_mm": round(total_distance, 2),
            "avg_distance_mm": round(total_distance / (len(points) - 1), 2) if len(points) > 1 else 0
        }


class MeasurementAnalysisService:
    """
    Service for analyzing tension measurement results.

    Provides statistical analysis and classification of measurements.
    """

    @staticmethod
    def analyze_session(session: MeasurementSession) -> Dict:
        """
        Perform complete analysis of measurement session.

        Args:
            session: MeasurementSession with completed measurements

        Returns:
            Dictionary with analysis results including:
            - Statistics (mean, std, min, max)
            - Classification (OK, WARNING, CRITICAL)
            - Outliers detection
            - Recommendations
        """
        if not session.measurements:
            return {
                "status": "empty",
                "message": "Nenhuma medição disponível para análise"
            }

        valid_measurements = session.valid_measurements

        if not valid_measurements:
            return {
                "status": "no_valid_data",
                "message": "Nenhuma medição válida disponível",
                "total_measurements": len(session.measurements)
            }

        # Extract values
        values = [m.parsed_value for m in valid_measurements if m.parsed_value is not None]

        if not values:
            return {
                "status": "no_parsed_values",
                "message": "Não foi possível parsear nenhum valor",
                "total_measurements": len(session.measurements)
            }

        # Calculate statistics
        mean_val = np.mean(values)
        std_val = np.std(values)
        min_val = np.min(values)
        max_val = np.max(values)
        median_val = np.median(values)

        # Detect outliers (values outside 2 standard deviations)
        outliers = []
        threshold = 2 * std_val
        for measurement in valid_measurements:
            if measurement.parsed_value is not None:
                deviation = abs(measurement.parsed_value - mean_val)
                if deviation > threshold:
                    outliers.append({
                        "point": measurement.point.index,
                        "coordinates": (measurement.point.x, measurement.point.y),
                        "value": measurement.parsed_value,
                        "deviation": round(deviation, 2)
                    })

        # Classification based on typical tension values (N/cm²)
        # Adjust thresholds based on your specific requirements
        classification = MeasurementAnalysisService._classify_tension(
            mean_val, std_val
        )

        return {
            "status": "success",
            "statistics": {
                "count": len(values),
                "mean": round(mean_val, 2),
                "median": round(median_val, 2),
                "std": round(std_val, 2),
                "min": round(min_val, 2),
                "max": round(max_val, 2),
                "range": round(max_val - min_val, 2),
                "coefficient_of_variation": round((std_val / mean_val) * 100, 2) if mean_val > 0 else 0
            },
            "classification": classification,
            "outliers": {
                "count": len(outliers),
                "items": outliers
            },
            "completeness": {
                "measured": len(session.measurements),
                "valid": len(valid_measurements),
                "total": session.parameters.total_points if session.parameters else 0,
                "percentage": session.progress_percentage
            }
        }

    @staticmethod
    def _classify_tension(mean: float, std: float) -> Dict:
        """
        Classify tension measurement based on statistical analysis.

        Args:
            mean: Mean tension value
            std: Standard deviation

        Returns:
            Dictionary with classification and recommendations
        """
        # Typical tension ranges for stencil mesh (N/cm²)
        # Adjust these thresholds based on your requirements

        classification = {
            "category": "UNKNOWN",
            "color": "GRAY",
            "message": "",
            "recommendations": []
        }

        # Check uniformity (coefficient of variation)
        if mean > 0:
            cv = (std / mean) * 100
        else:
            cv = 0

        # Classification logic
        if mean < 20:
            classification.update({
                "category": "CRITICAL",
                "color": "RED",
                "message": f"Tensão muito baixa ({mean:.1f} N/cm²)",
                "recommendations": [
                    "Verificar se o stencil está properly tensioned",
                    "Considerar retensioning do stencil",
                    "Inspecionar danos na malha do stencil"
                ]
            })
        elif mean > 50:
            classification.update({
                "category": "WARNING",
                "color": "ORANGE",
                "message": f"Tensão muito alta ({mean:.1f} N/cm²)",
                "recommendations": [
                    "Tensão acima do especificado",
                    "Verificar risco de dano ao stencil",
                    "Considerar redução da tensão"
                ]
            })
        elif cv > 15:
            classification.update({
                "category": "WARNING",
                "color": "YELLOW",
                "message": f"Tensão não uniforme (CV={cv:.1f}%)",
                "recommendations": [
                    "Alta variação na tensão da malha",
                    "Verificar pontos de tensão irregular",
                    "Inspecionar fixtures de montagem"
                ]
            })
        else:
            # Optimal range: 20-50 N/cm² with good uniformity
            classification.update({
                "category": "OK",
                "color": "GREEN",
                "message": f"Tensão adequada ({mean:.1f} ± {std:.1f} N/cm²)",
                "recommendations": [
                    "Tensão dentro da especificação",
                    "Uniformidade boa (CV < 15%)",
                    "Stencil pronto para uso"
                ]
            })

        return classification

    @staticmethod
    def generate_report(session: MeasurementSession) -> str:
        """
        Generate human-readable report of measurement session.

        Args:
            session: MeasurementSession to report

        Returns:
            Formatted string report
        """
        analysis = MeasurementAnalysisService.analyze_session(session)

        if analysis["status"] == "empty":
            return "Relatório: Nenhuma medição disponível"

        lines = [
            "=" * 60,
            "RELATÓRIO DE MEDIÇÃO DE TENSÃO",
            "=" * 60,
            ""
        ]

        # Statistics section
        if "statistics" in analysis:
            stats = analysis["statistics"]
            lines.extend([
                "ESTATÍSTICAS:",
                f"  Medições válidas: {stats['count']}",
                f"  Média: {stats['mean']} N/cm²",
                f"  Mediana: {stats['median']} N/cm²",
                f"  Desvio padrão: {stats['std']} N/cm²",
                f"  Mínimo: {stats['min']} N/cm²",
                f"  Máximo: {stats['max']} N/cm²",
                f"  Variação (CV): {stats['coefficient_of_variation']}%",
                ""
            ])

        # Classification section
        if "classification" in analysis:
            cls = analysis["classification"]
            lines.extend([
                f"CLASSIFICAÇÃO: {cls['category']}",
                f"  {cls['message']}",
                ""
            ])

            if cls["recommendations"]:
                lines.append("RECOMENDAÇÕES:")
                for rec in cls["recommendations"]:
                    lines.append(f"  • {rec}")
                lines.append("")

        # Outliers section
        if "outliers" in analysis and analysis["outliers"]["count"] > 0:
            lines.extend([
                f"OUTLIERS DETECTADOS: {analysis['outliers']['count']}",
                ""
            ])
            for outlier in analysis["outliers"]["items"]:
                lines.append(
                    f"  Ponto {outlier['point']} "
                    f"({outlier['coordinates'][0]:.1f}, {outlier['coordinates'][1]:.1f}): "
                    f"{outlier['value']:.2f} N/cm² "
                    f"(desvio: {outlier['deviation']:.2f})"
                )
            lines.append("")

        lines.append("=" * 60)

        return "\n".join(lines)
