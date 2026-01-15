"""
Stencil Repository Interface.

Defines the abstract interface for stencil data persistence.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from aoi_lib.stencil_tracker import Stencil


class StencilRepository(ABC):
    """
    Abstract repository for stencil data persistence.

    This interface defines the contract for all stencil repository implementations,
    following the Repository Pattern for data access abstraction.

    Responsibilities:
    - CRUD operations for stencils
    - Search and filtering
    - Recipe-based queries
    """

    @abstractmethod
    def exists(self, code: str) -> bool:
        """
        Check if a stencil exists in the database.

        Args:
            code: Stencil code (unique identifier)

        Returns:
            True if stencil exists, False otherwise
        """
        pass

    @abstractmethod
    def get(self, code: str) -> Optional[Stencil]:
        """
        Retrieve a stencil by its code.

        Args:
            code: Stencil code (unique identifier)

        Returns:
            Stencil object if found, None otherwise
        """
        pass

    @abstractmethod
    def create(self, code: str, description: str = "",
               recipe_name: Optional[str] = None) -> Stencil:
        """
        Create a new stencil.

        Args:
            code: Stencil code (must be unique)
            description: Stencil description
            recipe_name: Associated recipe name

        Returns:
            Created Stencil object

        Raises:
            ValueError: If stencil with same code already exists
        """
        pass

    @abstractmethod
    def update(self, stencil: Stencil) -> None:
        """
        Update an existing stencil.

        Args:
            stencil: Stencil object with updated data

        Raises:
            ValueError: If stencil does not exist
        """
        pass

    @abstractmethod
    def delete(self, code: str) -> bool:
        """
        Delete a stencil from the database.

        Args:
            code: Stencil code to delete

        Returns:
            True if deleted, False if not found

        Note:
            Cascade delete will remove all related tension and inspection records.
        """
        pass

    @abstractmethod
    def list(self, status: Optional[str] = None) -> List[Stencil]:
        """
        List all stencils, optionally filtered by status.

        Args:
            status: Filter by status ('active', 'retired', 'warning').
                    If None, returns all stencils.

        Returns:
            List of Stencil objects, ordered by last_inspection DESC
        """
        pass

    @abstractmethod
    def search(self, query: str, status: Optional[str] = None) -> List[Stencil]:
        """
        Search stencils by code or description.

        Args:
            query: Search term (matches code or description using LIKE)
            status: Optional filter by status

        Returns:
            List of matching Stencil objects
        """
        pass

    @abstractmethod
    def get_by_recipe(self, recipe_name: str) -> List[Stencil]:
        """
        Retrieve all stencils that use a specific recipe.

        Args:
            recipe_name: Recipe name to filter by

        Returns:
            List of Stencil objects using the specified recipe
        """
        pass
