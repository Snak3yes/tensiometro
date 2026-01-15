"""
Statistics Calculator Service

Statistical calculations service for report data.
Responsible for basic statistics, percentages, outliers, and trends.
"""

import logging
from typing import Dict, List, Optional, Tuple
import numpy as np

log = logging.getLogger(__name__)


class StatisticsCalculator:
    """
    Statistical calculations service.

    Responsibilities:
    - Calculate basic statistics (mean, median, std, min, max)
    - Calculate percentages (OK, WARNING, NOK)
    - Detect outliers
    - Calculate trends
    - Classify values based on thresholds

    This service isolates all statistical logic, making it easier
    to test and maintain report builders.
    """

    def __init__(self):
        """Initialize statistics calculator."""
        pass

    # ======================================================================== #
    # BASIC STATISTICS
    # ======================================================================== #

    def calculate_basic_stats(
        self,
        data: List[float],
        include_cv: bool = True
    ) -> Dict[str, float]:
        """
        Calculate basic statistics for a list of values.

        Args:
            data: List of numeric values
            include_cv: Include coefficient of variation

        Returns:
            Dictionary with statistics (mean, median, std, min, max, count, cv)
        """
        if not data:
            return {
                'mean': 0.0,
                'median': 0.0,
                'std': 0.0,
                'min': 0.0,
                'max': 0.0,
                'count': 0,
                'cv': 0.0,
            }

        data_array = np.array(data)
        stats = {
            'mean': float(np.mean(data_array)),
            'median': float(np.median(data_array)),
            'std': float(np.std(data_array)),
            'min': float(np.min(data_array)),
            'max': float(np.max(data_array)),
            'count': len(data),
        }

        if include_cv and stats['mean'] != 0:
            stats['cv'] = stats['std'] / abs(stats['mean']) * 100
        else:
            stats['cv'] = 0.0

        return stats

    def calculate_percentages(
        self,
        classifications: List[str]
    ) -> Dict[str, float]:
        """
        Calculate percentages of classification (OK, WARNING, NOK).

        Args:
            classifications: List of status strings

        Returns:
            Dictionary with counts and percentages
        """
        if not classifications:
            return {
                'ok_count': 0,
                'ok_pct': 0.0,
                'warning_count': 0,
                'warning_pct': 0.0,
                'nok_count': 0,
                'nok_pct': 0.0,
                'total': 0,
            }

        total = len(classifications)

        # Count by status (case-insensitive)
        ok_count = sum(1 for s in classifications if s.upper() == 'OK')
        warning_count = sum(1 for s in classifications if s.upper() in ('WARNING', 'WARN'))
        nok_count = sum(1 for s in classifications if s.upper() == 'NOK')

        return {
            'ok_count': ok_count,
            'ok_pct': 100 * ok_count / total if total else 0.0,
            'warning_count': warning_count,
            'warning_pct': 100 * warning_count / total if total else 0.0,
            'nok_count': nok_count,
            'nok_pct': 100 * nok_count / total if total else 0.0,
            'total': total,
        }

    # ======================================================================== #
    # OUTLIER DETECTION
    # ======================================================================== #

    def detect_outliers(
        self,
        data: List[float],
        method: str = "iqr",
        threshold: float = 1.5
    ) -> List[int]:
        """
        Detect outliers in data.

        Args:
            data: List of numeric values
            method: Detection method ('iqr' or 'zscore')
            threshold: Threshold value (1.5 for IQR, 3.0 for z-score)

        Returns:
            List of indices of outliers
        """
        if not data or len(data) < 4:
            return []

        data_array = np.array(data)
        outliers = []

        if method == "iqr":
            # IQR method
            q1 = np.percentile(data_array, 25)
            q3 = np.percentile(data_array, 75)
            iqr = q3 - q1

            lower_bound = q1 - threshold * iqr
            upper_bound = q3 + threshold * iqr

            outliers = [
                i for i, val in enumerate(data)
                if val < lower_bound or val > upper_bound
            ]

        elif method == "zscore":
            # Z-score method
            mean = np.mean(data_array)
            std = np.std(data_array)

            if std > 0:
                z_scores = np.abs((data_array - mean) / std)
                outliers = [
                    i for i, z in enumerate(z_scores)
                    if z > threshold
                ]

        return outliers

    # ======================================================================== #
    # TREND ANALYSIS
    # ======================================================================== #

    def calculate_trend(
        self,
        data: List[float],
        window: int = 3
    ) -> Dict[str, any]:
        """
        Calculate trend of data over time.

        Args:
            data: List of values in chronological order
            window: Window size for moving average

        Returns:
            Dictionary with trend direction, slope, and confidence
        """
        if len(data) < 2:
            return {
                'direction': 'stable',
                'slope': 0.0,
                'confidence': 'low',
            }

        # Fit linear trend
        x = np.arange(len(data))
        y = np.array(data)

        # Calculate slope using linear regression
        if len(data) >= 3:
            try:
                # Polyfit degree 1 (linear)
                coeffs = np.polyfit(x, y, 1)
                slope = coeffs[0]

                # Determine direction
                if abs(slope) < 0.01:
                    direction = 'stable'
                elif slope > 0:
                    direction = 'increasing'
                else:
                    direction = 'decreasing'

                # Calculate R² for confidence
                y_pred = np.poly1d(coeffs)(x)
                ss_res = np.sum((y - y_pred) ** 2)
                ss_tot = np.sum((y - np.mean(y)) ** 2)
                r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

                # Confidence based on R²
                if r_squared > 0.7:
                    confidence = 'high'
                elif r_squared > 0.4:
                    confidence = 'medium'
                else:
                    confidence = 'low'

                return {
                    'direction': direction,
                    'slope': float(slope),
                    'confidence': confidence,
                    'r_squared': float(r_squared),
                }

            except Exception as e:
                log.warning(f"Erro ao calcular tendência: {e}")

        # Fallback for small datasets
        first_half = data[:len(data)//2] if len(data) > 2 else data
        second_half = data[len(data)//2:] if len(data) > 2 else data

        if not first_half or not second_half:
            return {
                'direction': 'stable',
                'slope': 0.0,
                'confidence': 'low',
            }

        avg_first = np.mean(first_half)
        avg_second = np.mean(second_half)

        if abs(avg_second - avg_first) < 0.5:
            direction = 'stable'
        elif avg_second > avg_first:
            direction = 'increasing'
        else:
            direction = 'decreasing'

        return {
            'direction': direction,
            'slope': avg_second - avg_first,
            'confidence': 'low',
        }

    # ======================================================================== #
    # CLASSIFICATION
    # ======================================================================== #

    def classify_value(
        self,
        value: float,
        thresholds: Dict[str, float]
    ) -> str:
        """
        Classify value as OK, WARNING, or NOK based on thresholds.

        Args:
            value: Value to classify
            thresholds: Dictionary with 'ok_min', 'ok_max', 'warning_low', 'warning_high'

        Returns:
            Classification string ('OK', 'WARNING', or 'NOK')
        """
        ok_min = thresholds.get('ok_min', 26.0)
        ok_max = thresholds.get('ok_max', 32.0)
        warn_low = thresholds.get('warning_low', 24.0)
        warn_high = thresholds.get('warning_high', 35.0)

        if ok_min <= value <= ok_max:
            return 'OK'
        elif warn_low <= value < ok_min or ok_max < value <= warn_high:
            return 'WARNING'
        else:
            return 'NOK'

    def classify_batch(
        self,
        values: List[float],
        thresholds: Dict[str, float]
    ) -> List[str]:
        """
        Classify multiple values.

        Args:
            values: List of values to classify
            thresholds: Dictionary with threshold values

        Returns:
            List of classification strings
        """
        return [
            self.classify_value(v, thresholds)
            for v in values
        ]

    # ======================================================================== #
    # UTILITY METHODS
    # ======================================================================== #

    def calculate_cv(self, mean: float, std: float) -> float:
        """
        Calculate coefficient of variation.

        Args:
            mean: Mean value
            std: Standard deviation

        Returns:
            Coefficient of variation as percentage
        """
        if mean == 0:
            return 0.0
        return (std / abs(mean)) * 100

    def generate_summary(
        self,
        stats: Dict[str, float],
        classifications: Dict[str, float] = None
    ) -> str:
        """
        Generate human-readable summary of statistics.

        Args:
            stats: Statistics dictionary from calculate_basic_stats
            classifications: Optional classification results

        Returns:
            Formatted summary text
        """
        lines = []

        # Basic statistics
        lines.append(f"Média: {stats.get('mean', 0):.2f}")
        lines.append(f"Desvio Padrão: {stats.get('std', 0):.2f}")
        lines.append(f"Mínimo: {stats.get('min', 0):.2f}")
        lines.append(f"Máximo: {stats.get('max', 0):.2f}")

        # Coefficient of variation
        cv = stats.get('cv', 0)
        lines.append(f"CV: {cv:.1f}%")

        # Classifications
        if classifications:
            lines.append("")
            lines.append("Classificação:")
            lines.append(f"  OK: {classifications.get('ok_count', 0)} ({classifications.get('ok_pct', 0):.0f}%)")
            lines.append(f"  WARNING: {classifications.get('warning_count', 0)} ({classifications.get('warning_pct', 0):.0f}%)")
            lines.append(f"  NOK: {classifications.get('nok_count', 0)} ({classifications.get('nok_pct', 0):.0f}%)")

        return "\n".join(lines)
