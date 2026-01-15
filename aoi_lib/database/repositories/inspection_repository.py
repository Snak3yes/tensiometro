"""
Inspection Repository Interface.

Defines the abstract interface for visual inspection records persistence.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from aoi_lib.stencil_tracker import InspectionRecord


class InspectionRepository(ABC):
    """
    Abstract repository for visual inspection records.

    This interface defines the contract for all inspection repository implementations,
    following the Repository Pattern for data access abstraction.

    Responsibilities:
    - Add inspection records
    - Retrieve historical data
    - Calculate statistics
    - Combined timeline queries (tension + inspection)
    """

    @abstractmethod
    def add(self, code: str, record: InspectionRecord) -> None:
        """
        Add a visual inspection record to the database.

        Args:
            code: Stencil code (must exist in stencils table)
            record: InspectionRecord object with inspection data

        Raises:
            ValueError: If stencil code does not exist
        """
        pass

    @abstractmethod
    def get_history(self, code: str, limit: int = 50) -> List[InspectionRecord]:
        """
        Retrieve visual inspection history for a stencil.

        Args:
            code: Stencil code
            limit: Maximum number of records to retrieve (default: 50)

        Returns:
            List of InspectionRecord objects, ordered by timestamp DESC
            (most recent first)
        """
        pass

    @abstractmethod
    def get_by_period(self, start_date: str, end_date: str,
                      code: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve inspection records within a date range.

        Args:
            start_date: Start date in ISO format (YYYY-MM-DDTHH:MM:SS)
            end_date: End date in ISO format (YYYY-MM-DDTHH:MM:SS)
            code: Optional stencil code filter. If None, returns all stencils.

        Returns:
            List of dictionaries containing:
            - stencil_code: Stencil identifier
            - timestamp: Inspection timestamp
            - total_apertures: Total number of apertures inspected
            - ok_count: Number of OK apertures
            - partial_count: Number of PARTIAL apertures
            - blocked_count: Number of BLOCKED apertures
            - result: Classification (PASS/FAIL)
            - pass_rate: Pass rate percentage
            - gerber_file: Gerber file used
            - operator: Operator name
            - recipe_name: Recipe used
            - report_path: PDF report path
        """
        pass

    @abstractmethod
    def get_stats(self, code: str) -> Dict[str, Any]:
        """
        Calculate inspection statistics for a stencil.

        Args:
            code: Stencil code

        Returns:
            Dictionary containing:
            - total_inspections: Total number of inspections
            - pass_count: Number of PASS inspections
            - fail_count: Number of FAIL inspections
            - pass_rate: Pass rate percentage
            - avg_pass_rate: Average pass rate across all inspections
            - last_result: Result of most recent inspection (PASS/FAIL)
        """
        pass

    @abstractmethod
    def get_combined_history(self, code: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Retrieve combined timeline of tension and inspection records.

        This method merges both types of records into a single chronological
        timeline for comprehensive stencil history.

        Args:
            code: Stencil code
            limit: Maximum number of total records to retrieve (default: 50)

        Returns:
            List of dictionaries, each containing:
            - type: Record type ('tension' or 'inspection')
            - timestamp: Record timestamp
            - record: Original record object (TensionRecord or InspectionRecord)

            Ordered by timestamp DESC (most recent first)
        """
        pass
