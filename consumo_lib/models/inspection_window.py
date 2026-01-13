"""
Inspection window models for engineering workflow.

This module defines data models for configuring inspection windows (apertures)
in the Gerber inspection workflow, including grouping, thresholds, and library management.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS
# ============================================================================

class WindowStatus(Enum):
    """Status of an inspection window configuration."""
    NOT_CONFIGURED = "not_configured"  # ⚪ No configuration applied
    CONFIGURED = "configured"  # 🟢 Configuration applied but not confirmed
    CONFIRMED = "confirmed"  # ✅ Configuration confirmed by user


class BinarizationMethod(Enum):
    """Binarization methods for inspection."""
    OTSU = "otsu"
    ADAPTIVE = "adaptive"
    FIXED = "fixed"


class PreprocessMethod(Enum):
    """Preprocessing methods."""
    NONE = "none"
    BLUR = "blur"
    DENOISE = "denoise"
    MEDIAN = "median"


class GroupingCriteria(Enum):
    """Criteria for grouping windows."""
    EXACT_DIMENSIONS = "exact"  # 0.5mm = 0.5mm only
    TOLERANCE = "tolerance"  # 0.48-0.52mm ≈ 0.5mm
    DIMENSION_AND_SHAPE = "dimension_shape"  # 0.5mm circle ≠ 0.5mm square


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class WindowConfig:
    """
    Configuration for inspection windows.

    Attributes:
        ok_threshold: Minimum percentage for OK classification (default 90%)
        partial_threshold: Minimum percentage for PARTIAL classification (default 70%)
        binarization_method: Method for image binarization
        preprocess_method: Preprocessing method
        custom_parameters: Additional parameters for advanced configuration
    """
    ok_threshold: float = 90.0
    partial_threshold: float = 70.0
    binarization_method: BinarizationMethod = BinarizationMethod.OTSU
    preprocess_method: PreprocessMethod = PreprocessMethod.BLUR
    custom_parameters: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> bool:
        """Validate configuration values."""
        return (
            0.0 <= self.ok_threshold <= 100.0 and
            0.0 <= self.partial_threshold <= 100.0 and
            self.partial_threshold < self.ok_threshold
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "ok_threshold": self.ok_threshold,
            "partial_threshold": self.partial_threshold,
            "binarization_method": self.binarization_method.value,
            "preprocess_method": self.preprocess_method.value,
            "custom_parameters": self.custom_parameters
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WindowConfig":
        """Deserialize from dictionary."""
        return cls(
            ok_threshold=data.get("ok_threshold", 90.0),
            partial_threshold=data.get("partial_threshold", 70.0),
            binarization_method=BinarizationMethod(
                data.get("binarization_method", "otsu")
            ),
            preprocess_method=PreprocessMethod(
                data.get("preprocess_method", "blur")
            ),
            custom_parameters=data.get("custom_parameters", {})
        )

    def __str__(self) -> str:
        """String representation."""
        return (
            f"OK ≥ {self.ok_threshold:.0f}%, "
            f"PARTIAL ≥ {self.partial_threshold:.0f}%, "
            f"{self.binarization_method.value.title()}"
        )


@dataclass
class InspectionWindow:
    """
    Represents a single inspection window (aperture) from Gerber.

    Attributes:
        id: Unique identifier (from Gerber object ID)
        x_mm: X position in mm
        y_mm: Y position in mm
        kind: Shape type (circle, rect, oval, macro, region)
        dimensions: Dictionary with dimension parameters
        config: Configuration for this window (None = use group config)
        status: Configuration status
        is_exception: True if this window has custom configuration
    """
    id: int
    x_mm: float
    y_mm: float
    kind: str
    dimensions: Dict[str, float] = field(default_factory=dict)
    config: Optional[WindowConfig] = None
    status: WindowStatus = WindowStatus.NOT_CONFIGURED
    is_exception: bool = False

    @property
    def group_key(self) -> str:
        """
        Generate grouping key based on dimensions.

        Returns:
            String key for grouping (e.g., "circle_0.5mm" or "rect_0.8x1.2mm")
        """
        if self.kind == "circle":
            diameter = self.dimensions.get("diameter_mm", 0)
            return f"circle_{diameter:.2f}mm"
        elif self.kind == "rect":
            width = self.dimensions.get("width_mm", 0)
            height = self.dimensions.get("height_mm", 0)
            return f"rect_{width:.2f}x{height:.2f}mm"
        elif self.kind == "oval":
            width = self.dimensions.get("width_mm", 0)
            height = self.dimensions.get("height_mm", 0)
            return f"oval_{width:.2f}x{height:.2f}mm"
        else:
            return f"{self.kind}_{self.id}"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "x_mm": self.x_mm,
            "y_mm": self.y_mm,
            "kind": self.kind,
            "dimensions": self.dimensions,
            "config": self.config.to_dict() if self.config else None,
            "status": self.status.value,
            "is_exception": self.is_exception
        }

    @classmethod
    def from_gerber_object(cls, gerber_obj: Any) -> "InspectionWindow":
        """
        Create InspectionWindow from Gerber object.

        Args:
            gerber_obj: GerberObject from gerber_parser

        Returns:
            InspectionWindow instance
        """
        dimensions = {}

        if hasattr(gerber_obj, 'params'):
            if 'dia_mm' in gerber_obj.params:
                dimensions['diameter_mm'] = gerber_obj.params['dia_mm']
            if 'width_mm' in gerber_obj.params:
                dimensions['width_mm'] = gerber_obj.params['width_mm']
            if 'height_mm' in gerber_obj.params:
                dimensions['height_mm'] = gerber_obj.params['height_mm']

        return cls(
            id=gerber_obj.id,
            x_mm=getattr(gerber_obj, 'x_mm', 0.0),
            y_mm=getattr(gerber_obj, 'y_mm', 0.0),
            kind=gerber_obj.kind.replace("flash_", "") if "flash_" in gerber_obj.kind else gerber_obj.kind,
            dimensions=dimensions
        )


@dataclass
class WindowGroup:
    """
    Group of inspection windows with same configuration.

    Attributes:
        name: Group name (e.g., "0.5mm Circle")
        key: Grouping key for identification
        windows: List of windows in this group
        config: Configuration for the group
        status: Configuration status
        exceptions: List of window IDs with custom configuration
    """
    name: str
    key: str
    windows: List[InspectionWindow] = field(default_factory=list)
    config: Optional[WindowConfig] = None
    status: WindowStatus = WindowStatus.NOT_CONFIGURED
    exceptions: List[int] = field(default_factory=list)

    @property
    def count(self) -> int:
        """Total number of windows in group."""
        return len(self.windows)

    @property
    def exception_count(self) -> int:
        """Number of windows with custom configuration."""
        return len(self.exceptions)

    @property
    def standard_count(self) -> int:
        """Number of windows using group configuration."""
        return self.count - self.exception_count

    def add_window(self, window: InspectionWindow) -> None:
        """Add window to group."""
        if window.id not in [w.id for w in self.windows]:
            self.windows.append(window)

    def get_window_by_id(self, window_id: int) -> Optional[InspectionWindow]:
        """Get window by ID."""
        for window in self.windows:
            if window.id == window_id:
                return window
        return None

    def apply_config_to_group(self, config: WindowConfig, confirm: bool = False) -> None:
        """
        Apply configuration to all non-exception windows.

        Args:
            config: Configuration to apply
            confirm: Whether to mark as confirmed
        """
        self.config = config
        self.status = WindowStatus.CONFIRMED if confirm else WindowStatus.CONFIGURED

        for window in self.windows:
            if not window.is_exception:
                window.config = config
                window.status = self.status

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "key": self.key,
            "count": self.count,
            "config": self.config.to_dict() if self.config else None,
            "status": self.status.value,
            "exceptions": self.exceptions,
            "windows": [w.to_dict() for w in self.windows]
        }


@dataclass
class WindowLibrary:
    """
    Library of reusable window configurations.

    Stores configurations by group key for automatic application.
    """
    configs: Dict[str, WindowConfig] = field(default_factory=dict)

    def add_config(self, key: str, config: WindowConfig) -> None:
        """Add or update configuration in library."""
        self.configs[key] = config

    def get_config(self, key: str) -> Optional[WindowConfig]:
        """Get configuration by key."""
        return self.configs.get(key)

    def remove_config(self, key: str) -> None:
        """Remove configuration from library."""
        if key in self.configs:
            del self.configs[key]

    def has_config(self, key: str) -> bool:
        """Check if configuration exists for key."""
        return key in self.configs

    def suggest_config(self, key: str) -> Optional[WindowConfig]:
        """
        Suggest configuration using fuzzy matching.

        Args:
            key: Group key to find config for

        Returns:
            Best matching configuration or None
        """
        # First try exact match
        if key in self.configs:
            return self.configs[key]

        # Try fuzzy match (similar dimensions)
        best_match = None
        best_score = 0.0

        for lib_key, config in self.configs.items():
            score = self._calculate_similarity(key, lib_key)
            if score > best_score and score >= 0.8:  # 80% similarity threshold
                best_match = config
                best_score = score

        return best_match

    def _calculate_similarity(self, key1: str, key2: str) -> float:
        """
        Calculate similarity between two group keys.

        Simple implementation: checks if keys are of same type
        and have similar dimensions.
        """
        # Extract type and dimensions
        parts1 = key1.split('_')
        parts2 = key2.split('_')

        if len(parts1) < 2 or len(parts2) < 2:
            return 0.0

        # Check if same type
        if parts1[0] != parts2[0]:
            return 0.0

        # Extract dimensions (numeric parts)
        dims1 = [float(p.replace('mm', '').replace('x', '_')) for p in parts1[1:]]
        dims2 = [float(p.replace('mm', '').replace('x', '_')) for p in parts2[1:]]

        if len(dims1) != len(dims2):
            return 0.0

        # Calculate average similarity
        similarities = []
        for d1, d2 in zip(dims1, dims2):
            if d1 == d2:
                similarities.append(1.0)
            else:
                sim = 1.0 - abs(d1 - d2) / max(d1, d2)
                similarities.append(sim)

        return sum(similarities) / len(similarities) if similarities else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            key: config.to_dict()
            for key, config in self.configs.items()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WindowLibrary":
        """Deserialize from dictionary."""
        library = cls()
        for key, config_data in data.items():
            library.configs[key] = WindowConfig.from_dict(config_data)
        return library

    def save(self, filepath: Path) -> None:
        """Save library to JSON file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        logger.info(f"Library saved to {filepath}")

    @classmethod
    def load(cls, filepath: Path) -> "WindowLibrary":
        """Load library from JSON file."""
        if not filepath.exists():
            logger.warning(f"Library file not found: {filepath}")
            return cls()

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        logger.info(f"Library loaded from {filepath}")
        return cls.from_dict(data)


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_default_config() -> WindowConfig:
    """Create default window configuration."""
    return WindowConfig(
        ok_threshold=90.0,
        partial_threshold=70.0,
        binarization_method=BinarizationMethod.OTSU,
        preprocess_method=PreprocessMethod.BLUR
    )


def create_groups_from_windows(
    windows: List[InspectionWindow],
    criteria: GroupingCriteria = GroupingCriteria.EXACT_DIMENSIONS,
    tolerance: float = 0.02
) -> List[WindowGroup]:
    """
    Create groups from list of windows based on criteria.

    Args:
        windows: List of inspection windows
        criteria: Grouping criteria to use
        tolerance: Tolerance for grouping (in mm, if using TOLERANCE criteria)

    Returns:
        List of WindowGroup objects
    """
    groups_dict: Dict[str, WindowGroup] = {}

    for window in windows:
        key = window.group_key

        # Apply tolerance if specified
        if criteria == GroupingCriteria.TOLERANCE:
            key = _normalize_key_with_tolerance(key, tolerance)

        # Create or get group
        if key not in groups_dict:
            group_name = _generate_group_name(key, window)
            groups_dict[key] = WindowGroup(
                name=group_name,
                key=key
            )

        # Add window to group
        groups_dict[key].add_window(window)

    return list(groups_dict.values())


def _normalize_key_with_tolerance(key: str, tolerance: float) -> str:
    """
    Normalize group key to apply tolerance.

    Rounds dimensions to nearest multiple of tolerance.
    """
    parts = key.split('_')
    if len(parts) < 2:
        return key

    # Round numeric parts
    normalized = [parts[0]]  # Keep type
    for part in parts[1:]:
        num_str = part.replace('mm', '').replace('x', '_')
        try:
            value = float(num_str)
            rounded = round(value / tolerance) * tolerance
            normalized.append(f"{rounded:.2f}mm")
        except ValueError:
            normalized.append(part)

    return '_'.join(normalized)


def _generate_group_name(key: str, window: InspectionWindow) -> str:
    """Generate human-readable group name."""
    parts = key.split('_')

    if window.kind == "circle":
        diameter = window.dimensions.get("diameter_mm", 0)
        return f"{diameter:.2f}mm Círculo"
    elif window.kind == "rect":
        width = window.dimensions.get("width_mm", 0)
        height = window.dimensions.get("height_mm", 0)
        return f"{width:.2f}x{height:.2f}mm Retângulo"
    elif window.kind == "oval":
        width = window.dimensions.get("width_mm", 0)
        height = window.dimensions.get("height_mm", 0)
        return f"{width:.2f}x{height:.2f}mm Oval"
    else:
        return f"{window.kind.title()} ({window.id})"
