"""
Tension Repository Interface.

Defines the abstract interface for tension measurement records persistence.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from aoi_lib.stencil_tracker import TensionRecord


class TensionRepository(ABC):
    """
    Abstract repository for tension measurement records.

    This interface defines the contract for all tension repository implementations,
    following the Repository Pattern for data access abstraction.

    Responsibilities:
    - Add tension measurements
    - Retrieve historical data
    - Period-based queries
    """

    @abstractmethod
    def add(self, code: str, record: TensionRecord) -> None:
        """
        Add a tension measurement record to the database.

        Args:
            code: Stencil code (must exist in stencils table)
            record: TensionRecord object with measurement data

        Raises:
            ValueError: If stencil code does not exist
        """
        pass

    @abstractmethod
    def get_history(self, code: str, limit: int = 50) -> List[TensionRecord]:
        """
        Retrieve tension measurement history for a stencil.

        Args:
            code: Stencil code
            limit: Maximum number of records to retrieve (default: 50)

        Returns:
            List of TensionRecord objects, ordered by timestamp DESC
            (most recent first)
        """
        pass

    @abstractmethod
    def get_by_period(self, start_date: str, end_date: str,
                      code: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve tension records within a date range.

        Args:
            start_date: Start date in ISO format (YYYY-MM-DDTHH:MM:SS)
            end_date: End date in ISO format (YYYY-MM-DDTHH:MM:SS)
            code: Optional stencil code filter. If None, returns all stencils.

        Returns:
            List of dictionaries containing:
            - stencil_code: Stencil identifier
            - timestamp: Measurement timestamp
            - average_tension: Average tension value
            - min_tension: Minimum tension value
            - max_tension: Maximum tension value
            - result: Classification (OK/WARNING/NOK)
            - ok_count: Number of OK measurements
            - warning_count: Number of WARNING measurements
            - nok_count: Number of NOK measurements
        """
        pass

    @abstractmethod
    def get_latest(self, code: str) -> Optional[TensionRecord]:
        """
        Retrieve the most recent tension measurement for a stencil.

        Args:
            code: Stencil code

        Returns:
            Latest TensionRecord if found, None otherwise
        """
        pass
