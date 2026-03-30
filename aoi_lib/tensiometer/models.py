"""
Data Models for Tension Measurement System

This module contains all data structures used for tension measurement operations.
Uses dataclasses for type safety and immutability where appropriate.

Created: 2026-01-14 (Phase 1 - SOLID Refactoring)
Author: SOLID Refactoring Track
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from enum import Enum


class TensionUnit(Enum):
    """Units for tension measurement"""
    N_CM2 = "N/cm²"
    KG_CM2 = "kg/cm²"
    LB_CM2 = "lb/cm²"


@dataclass(frozen=True)
class GridPoint:
    """
    Represents a single measurement point in the grid.

    Attributes:
        x: X coordinate in mm
        y: Y coordinate in mm
        index: Linear index in the measurement sequence (0-based)
        grid_position: (row, col) position in the NxN grid
    """
    x: float
    y: float
    index: int
    grid_position: Tuple[int, int] = (0, 0)

    def __post_init__(self):
        """Validate coordinates"""
        if not isinstance(self.x, (int, float)) or not isinstance(self.y, (int, float)):
            raise ValueError("Coordinates must be numeric")

    @property
    def coordinates(self) -> Tuple[float, float]:
        """Return point as (x, y) tuple"""
        return (self.x, self.y)


@dataclass
class TensionMeasurement:
    """
    Single tension measurement at a grid point.

    Attributes:
        point: GridPoint where measurement was taken
        z_height: Z axis position during measurement (mm)
        tension_value: Measured tension value (as string from device)
        unit: Unit of measurement (default: N/cm²)
        timestamp: When measurement was taken
        raw_value: Raw string from tensiometer
        parsed_value: Parsed float value (if conversion successful)
    """
    point: GridPoint
    z_height: float
    tension_value: str
    unit: TensionUnit = TensionUnit.N_CM2
    timestamp: datetime = field(default_factory=datetime.now)
    raw_value: str = ""
    parsed_value: Optional[float] = None

    def __post_init__(self):
        """Parse tension value to float if possible"""
        if self.raw_value == "" and self.tension_value:
            object.__setattr__(self, 'raw_value', self.tension_value)

        try:
            object.__setattr__(self, 'parsed_value', float(self.tension_value))
        except (ValueError, TypeError):
            # Keep as None if parsing fails
            pass

    @property
    def is_valid(self) -> bool:
        """Check if measurement has a valid parsed value"""
        return self.parsed_value is not None

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "index": self.point.index,
            "grid_position": {
                "row": self.point.grid_position[0],
                "col": self.point.grid_position[1]
            },
            "x": self.point.x,
            "y": self.point.y,
            "z": self.z_height,
            "tension": self.tension_value,
            "unit": self.unit.value,
            "timestamp": self.timestamp.isoformat(),
            "parsed_value": self.parsed_value,
            "is_valid": self.is_valid
        }


@dataclass
class GridParameters:
    """
    Parameters for defining the measurement grid.

    Attributes:
        start_point: (x, y) starting position in mm
        end_point: (x, y) ending position in mm
        grid_size: N for NxN grid (e.g., 3 for 3x3 grid)
        z_height: Z axis measurement height in mm
        z_move: Safe Z height for movement between points
    """
    start_point: Tuple[float, float]
    end_point: Tuple[float, float]
    grid_size: int
    z_height: float
    z_move: float = 5.0  # Default safe height

    def __post_init__(self):
        """Validate parameters"""
        if self.grid_size < 2:
            raise ValueError("Grid size must be >= 2")
        if self.z_height < 0 or self.z_move < 0:
            raise ValueError("Z heights must be non-negative")

    @property
    def total_points(self) -> int:
        """Total number of measurement points"""
        return self.grid_size ** 2


@dataclass
class MeasurementSession:
    """
    Complete measurement session with all measurements.

    Attributes:
        parameters: Grid configuration used
        measurements: List of all measurements taken
        start_time: Session start timestamp
        end_time: Session end timestamp (None until complete)
        user_feed: Optional feed rate for CNC movements (mm/min)
        stabilization_time_ms: Stabilization delay after Z movement (ms)
    """
    parameters: GridParameters
    measurements: List[TensionMeasurement] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    user_feed: Optional[float] = None  # None preserves the current PLC speed
    stabilization_time_ms: int = 500  # milliseconds

    @property
    def is_complete(self) -> bool:
        """Check if all grid points have been measured"""
        return len(self.measurements) == self.parameters.total_points

    @property
    def progress_percentage(self) -> float:
        """Progress as percentage (0-100)"""
        if self.parameters.total_points == 0:
            return 0.0
        return (len(self.measurements) / self.parameters.total_points) * 100

    @property
    def valid_measurements(self) -> List[TensionMeasurement]:
        """Return only measurements with valid parsed values"""
        return [m for m in self.measurements if m.is_valid]

    @property
    def average_tension(self) -> Optional[float]:
        """Calculate average tension from valid measurements"""
        valid = self.valid_measurements
        if not valid:
            return None
        # Safe: all valid measurements have non-None parsed_value
        values = [m.parsed_value for m in valid if m.parsed_value is not None]
        return sum(values) / len(values) if values else None

    @property
    def min_tension(self) -> Optional[float]:
        """Get minimum tension value"""
        valid = self.valid_measurements
        if not valid:
            return None
        # Safe: all valid measurements have non-None parsed_value
        values = [m.parsed_value for m in valid if m.parsed_value is not None]
        return min(values) if values else None

    @property
    def max_tension(self) -> Optional[float]:
        """Get maximum tension value"""
        valid = self.valid_measurements
        if not valid:
            return None
        # Safe: all valid measurements have non-None parsed_value
        values = [m.parsed_value for m in valid if m.parsed_value is not None]
        return max(values) if values else None

    def add_measurement(self, measurement: TensionMeasurement) -> None:
        """Add a measurement to the session"""
        self.measurements.append(measurement)

    def complete_session(self) -> None:
        """Mark session as complete"""
        if self.end_time is None:
            self.end_time = datetime.now()

    def to_dict(self) -> Dict:
        """Convert session to dictionary for JSON serialization"""
        return {
            "type": "stencil_tension_session",
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "parameters": {
                "start": {"x": self.parameters.start_point[0], "y": self.parameters.start_point[1]},
                "end": {"x": self.parameters.end_point[0], "y": self.parameters.end_point[1]},
                "grid_size": self.parameters.grid_size,
                "z_height": self.parameters.z_height,
                "z_move": self.parameters.z_move,
                "feed_rate": self.user_feed,
                "stabilization_time_ms": self.stabilization_time_ms
            },
            "statistics": {
                "total_points": self.parameters.total_points,
                "measured_points": len(self.measurements),
                "valid_measurements": len(self.valid_measurements),
                "progress_percentage": round(self.progress_percentage, 2),
                "average_tension": self.average_tension,
                "min_tension": self.min_tension,
                "max_tension": self.max_tension
            },
            "measurements": [m.to_dict() for m in self.measurements]
        }


@dataclass
class TensiometerConfig:
    """
    Configuration for tensiometer serial communication.

    Attributes:
        port: Serial port (e.g., 'COM3', '/dev/ttyUSB0')
        baudrate: Communication speed (default: 2400 for AS-120N)
        timeout: Read timeout in seconds
        req_command: Byte command to request measurement
        frame_length: Expected response frame length
        unit_map: Mapping from unit byte to string representation
    """
    port: Optional[str] = None
    baudrate: int = 2400
    timeout: float = 1.0
    req_command: bytes = b'\x20'
    frame_length: int = 9
    unit_map: Dict[int, str] = field(default_factory=lambda: {
        0x05: "N/cm²",
        0x04: "kg/cm²",
        0x06: "lb/cm²"
    })
