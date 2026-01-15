"""
SQLite implementation of Stencil Repository.

Provides concrete implementation of StencilRepository using SQLite database.
"""

import logging
from datetime import datetime
from typing import List, Optional

from aoi_lib.database.connection import DatabaseConnection
from aoi_lib.database.repositories.stencil_repository import StencilRepository
from aoi_lib.stencil_tracker import Stencil

log = logging.getLogger(__name__)


class SqliteStencilRepository(StencilRepository):
    """
    SQLite implementation of stencil repository.

    This repository manages stencil data persistence using SQLite,
    implementing all CRUD operations defined in StencilRepository interface.
    """

    def __init__(self, connection: DatabaseConnection):
        """
        Initialize repository with database connection.

        Args:
            connection: DatabaseConnection instance (typically SqliteConnection)
        """
        self.connection = connection

    def exists(self, code: str) -> bool:
        """
        Check if a stencil exists in the database.

        Args:
            code: Stencil code (unique identifier)

        Returns:
            True if stencil exists, False otherwise
        """
        with self.connection.connect() as conn:
            cursor = conn.execute(
                "SELECT 1 FROM stencils WHERE code = ?",
                (code,)
            )
            return cursor.fetchone() is not None

    def get(self, code: str) -> Optional[Stencil]:
        """
        Retrieve a stencil by its code.

        Args:
            code: Stencil code (unique identifier)

        Returns:
            Stencil object if found, None otherwise
        """
        with self.connection.connect() as conn:
            cursor = conn.execute(
                "SELECT * FROM stencils WHERE code = ?",
                (code,)
            )
            row = cursor.fetchone()

            if row is None:
                return None

            return Stencil(
                code=row["code"],
                description=row["description"] or "",
                recipe_name=row["recipe_name"],
                created_at=row["created_at"],
                last_inspection=row["last_inspection"],
                inspection_count=row["inspection_count"],
                status=row["status"],
                notes=row["notes"] or "",
            )

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
        if self.exists(code):
            raise ValueError(f"Stencil '{code}' já existe")

        now = datetime.now().isoformat()

        with self.connection.connect() as conn:
            conn.execute("""
                INSERT INTO stencils (code, description, recipe_name, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (code, description, recipe_name, now, now))

        log.info(f"Stencil criado: {code}")
        return self.get(code)

    def update(self, stencil: Stencil) -> None:
        """
        Update an existing stencil.

        Args:
            stencil: Stencil object with updated data

        Raises:
            ValueError: If stencil does not exist
        """
        if not self.exists(stencil.code):
            raise ValueError(f"Stencil '{stencil.code}' não existe")

        now = datetime.now().isoformat()

        with self.connection.connect() as conn:
            conn.execute("""
                UPDATE stencils SET
                    description = ?,
                    recipe_name = ?,
                    last_inspection = ?,
                    inspection_count = ?,
                    status = ?,
                    notes = ?,
                    updated_at = ?
                WHERE code = ?
            """, (
                stencil.description,
                stencil.recipe_name,
                stencil.last_inspection,
                stencil.inspection_count,
                stencil.status,
                stencil.notes,
                now,
                stencil.code,
            ))

        log.info(f"Stencil atualizado: {stencil.code}")

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
        if not self.exists(code):
            return False

        with self.connection.connect() as conn:
            conn.execute("DELETE FROM stencils WHERE code = ?", (code,))

        log.info(f"Stencil removido: {code}")
        return True

    def list(self, status: Optional[str] = None) -> List[Stencil]:
        """
        List all stencils, optionally filtered by status.

        Args:
            status: Filter by status ('active', 'retired', 'warning').
                    If None, returns all stencils.

        Returns:
            List of Stencil objects, ordered by last_inspection DESC
        """
        with self.connection.connect() as conn:
            if status:
                cursor = conn.execute("""
                    SELECT * FROM stencils WHERE status = ?
                    ORDER BY last_inspection DESC NULLS LAST, created_at DESC
                """, (status,))
            else:
                cursor = conn.execute("""
                    SELECT * FROM stencils
                    ORDER BY last_inspection DESC NULLS LAST, created_at DESC
                """)

            stencils = []
            for row in cursor.fetchall():
                stencils.append(Stencil(
                    code=row["code"],
                    description=row["description"] or "",
                    recipe_name=row["recipe_name"],
                    created_at=row["created_at"],
                    last_inspection=row["last_inspection"],
                    inspection_count=row["inspection_count"],
                    status=row["status"],
                    notes=row["notes"] or "",
                ))

            return stencils

    def search(self, query: str, status: Optional[str] = None) -> List[Stencil]:
        """
        Search stencils by code or description.

        Args:
            query: Search term (matches code or description using LIKE)
            status: Optional filter by status

        Returns:
            List of matching Stencil objects
        """
        with self.connection.connect() as conn:
            sql = """
                SELECT * FROM stencils
                WHERE (code LIKE ? OR description LIKE ?)
            """
            params = [f"%{query}%", f"%{query}%"]

            if status:
                sql += " AND status = ?"
                params.append(status)

            sql += " ORDER BY last_inspection DESC NULLS LAST"

            cursor = conn.execute(sql, params)

            stencils = []
            for row in cursor.fetchall():
                stencils.append(Stencil(
                    code=row["code"],
                    description=row["description"] or "",
                    recipe_name=row["recipe_name"],
                    created_at=row["created_at"],
                    last_inspection=row["last_inspection"],
                    inspection_count=row["inspection_count"],
                    status=row["status"],
                    notes=row["notes"] or "",
                ))

            return stencils

    def get_by_recipe(self, recipe_name: str) -> List[Stencil]:
        """
        Retrieve all stencils that use a specific recipe.

        Args:
            recipe_name: Recipe name to filter by

        Returns:
            List of Stencil objects using the specified recipe
        """
        with self.connection.connect() as conn:
            cursor = conn.execute("""
                SELECT * FROM stencils WHERE recipe_name = ? ORDER BY code
            """, (recipe_name,))

            stencils = []
            for row in cursor.fetchall():
                stencils.append(Stencil(
                    code=row["code"],
                    description=row["description"] or "",
                    recipe_name=row["recipe_name"],
                    created_at=row["created_at"],
                    last_inspection=row["last_inspection"],
                    inspection_count=row["inspection_count"],
                    status=row["status"],
                    notes=row["notes"] or "",
                ))

            return stencils
