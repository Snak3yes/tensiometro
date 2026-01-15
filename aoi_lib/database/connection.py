"""
Database connection abstraction for SQLite.

This module provides:
- DatabaseConnection (ABC): Abstract interface for database connections
- SqliteConnection: Concrete implementation for SQLite databases
"""

import sqlite3
import shutil
import logging
from abc import ABC, abstractmethod
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlite3 import Connection

log = logging.getLogger(__name__)


class DatabaseConnection(ABC):
    """
    Abstract base class for database connections.

    This interface defines the contract that all database connections must follow,
    enabling dependency inversion and easy testing through mocking.
    """

    def __init__(self, db_path: str):
        """
        Initialize the database connection.

        Args:
            db_path: Path to the database file
        """
        self.db_path = Path(db_path)

    @abstractmethod
    @contextmanager
    def connect(self) -> Generator['Connection', None, None]:
        """
        Context manager for database connection.

        Yields:
            Connection: Database connection object

        Example:
            >>> with db.connect() as conn:
            ...     conn.execute("SELECT * FROM table")
        """
        pass

    @abstractmethod
    def init_schema(self, schema_sql: str) -> None:
        """
        Initialize database schema.

        Args:
            schema_sql: SQL script to create tables and indexes
        """
        pass

    def get_db_path(self) -> Path:
        """
        Get the database file path.

        Returns:
            Path: Path object pointing to database file
        """
        return self.db_path

    def backup_database(self, backup_path: Optional[str] = None) -> str:
        """
        Create a backup of the database.

        Args:
            backup_path: Path for backup file (optional, auto-generated if None)

        Returns:
            str: Path to the created backup file

        Raises:
            FileNotFoundError: If database file doesn't exist
        """
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database file not found: {self.db_path}")

        if backup_path is None:
            timestamp = __import__('datetime').datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.db_path.parent / f"{self.db_path.stem}_backup_{timestamp}.db"

        backup_path = Path(backup_path)
        shutil.copy2(self.db_path, backup_path)

        log.info(f"Database backup created: {backup_path}")
        return str(backup_path)


class SqliteConnection(DatabaseConnection):
    """
    SQLite implementation of DatabaseConnection.

    This class manages SQLite database connections with proper transaction handling,
    foreign key support, and row factory configuration.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize SQLite connection.

        Args:
            db_path: Path to .db file. If None, uses default: ./data/stencils.db
        """
        if db_path is None:
            # Default path: ./data/stencils.db
            base = Path(__file__).parent.parent.parent
            db_path = base / "data" / "stencils.db"

        super().__init__(db_path)

        # Ensure directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        log.debug(f"SqliteConnection initialized with db_path: {self.db_path}")

    @contextmanager
    def connect(self) -> Generator['Connection', None, None]:
        """
        Context manager for SQLite connection.

        Automatically handles:
        - Connection creation
        - Transaction management (commit/rollback)
        - Connection cleanup

        Yields:
            Connection: SQLite connection with row_factory configured

        Example:
            >>> conn = SqliteConnection("test.db")
            >>> with conn.connect() as db:
            ...     db.execute("CREATE TABLE test (id INTEGER)")
            ...     # Auto-commit on success, rollback on error
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")

        try:
            yield conn
            conn.commit()
            log.debug("Transaction committed successfully")
        except Exception as e:
            conn.rollback()
            log.error(f"Transaction rolled back due to error: {e}")
            raise
        finally:
            conn.close()

    def init_schema(self, schema_sql: str) -> None:
        """
        Initialize database schema from SQL script.

        Executes the provided SQL script to create tables, indexes, and other
        database objects. Can be called multiple times safely (uses IF NOT EXISTS).

        Args:
            schema_sql: SQL script (typically multi-line with CREATE TABLE statements)

        Example:
            >>> conn = SqliteConnection("test.db")
            >>> schema = '''
            ... CREATE TABLE IF NOT EXISTS users (
            ...     id INTEGER PRIMARY KEY,
            ...     name TEXT
            ... );
            ... '''
            >>> conn.init_schema(schema)
        """
        if not schema_sql or not schema_sql.strip():
            log.debug("Empty schema SQL provided, skipping")
            return

        with self.connect() as conn:
            conn.executescript(schema_sql)

        log.info(f"Database schema initialized at: {self.db_path}")
