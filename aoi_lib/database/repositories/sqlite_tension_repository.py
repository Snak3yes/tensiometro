"""
SQLite implementation of Tension Repository.

Provides concrete implementation of TensionRepository using SQLite database.
"""

import json
import logging
from typing import List, Dict, Any, Optional

from aoi_lib.database.connection import DatabaseConnection
from aoi_lib.database.repositories.tension_repository import TensionRepository
from aoi_lib.stencil_tracker import TensionRecord

log = logging.getLogger(__name__)


class SqliteTensionRepository(TensionRepository):
    """
    SQLite implementation of tension measurement records repository.

    This repository manages tension measurement data persistence using SQLite,
    implementing all operations defined in TensionRepository interface.

    It also updates stencil metadata (last_inspection, inspection_count, status)
    when new records are added.
    """

    def __init__(self, connection: DatabaseConnection):
        """
        Initialize repository with database connection.

        Args:
            connection: DatabaseConnection instance (typically SqliteConnection)
        """
        self.connection = connection

    def _get_stencil_id(self, code: str) -> Optional[int]:
        """
        Get internal database ID for a stencil code.

        Args:
            code: Stencil code

        Returns:
            Internal ID if found, None otherwise
        """
        with self.connection.connect() as conn:
            cursor = conn.execute(
                "SELECT id FROM stencils WHERE code = ?",
                (code,)
            )
            row = cursor.fetchone()
            return row["id"] if row else None

    def add(self, code: str, record: TensionRecord) -> None:
        """
        Add a tension measurement record to the database.

        Args:
            code: Stencil code (must exist in stencils table)
            record: TensionRecord object with measurement data

        Raises:
            ValueError: If stencil code does not exist
        """
        with self.connection.connect() as conn:
            stencil_id = self._get_stencil_id(code)
            if not stencil_id:
                raise ValueError(f"Stencil '{code}' não encontrado")

            # Insert record
            conn.execute("""
                INSERT INTO tension_records
                (stencil_id, timestamp, average_tension, min_tension, max_tension,
                 result, ok_count, warning_count, nok_count, operator, recipe_name,
                 measurements_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                stencil_id,
                record.timestamp,
                record.average_tension,
                record.min_tension,
                record.max_tension,
                record.result,
                record.ok_count,
                record.warning_count,
                record.nok_count,
                record.operator,
                record.recipe_name,
                json.dumps(record.measurements),
            ))

            # Update stencil metadata
            conn.execute("""
                UPDATE stencils SET
                    last_inspection = ?,
                    inspection_count = inspection_count + 1,
                    status = CASE WHEN ? = 'NOK' THEN 'warning' ELSE status END,
                    updated_at = ?
                WHERE id = ?
            """, (record.timestamp, record.result,
                  __import__('datetime').datetime.now().isoformat(), stencil_id))

        log.info(f"Registro de tensão adicionado para {code}: {record.result}")

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
        with self.connection.connect() as conn:
            stencil_id = self._get_stencil_id(code)
            if not stencil_id:
                return []

            cursor = conn.execute("""
                SELECT * FROM tension_records
                WHERE stencil_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (stencil_id, limit))

            records = []
            for row in cursor.fetchall():
                measurements = json.loads(row["measurements_json"]) if row["measurements_json"] else []
                records.append(TensionRecord(
                    timestamp=row["timestamp"],
                    measurements=measurements,
                    average_tension=row["average_tension"],
                    min_tension=row["min_tension"],
                    max_tension=row["max_tension"],
                    result=row["result"],
                    ok_count=row["ok_count"],
                    warning_count=row["warning_count"],
                    nok_count=row["nok_count"],
                    operator=row["operator"],
                    recipe_name=row["recipe_name"],
                ))

            return records

    def get_by_period(self, start_date: str, end_date: str,
                      code: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve tension records within a date range.

        Args:
            start_date: Start date in ISO format (YYYY-MM-DDTHH:MM:SS)
            end_date: End date in ISO format (YYYY-MM-DDTHH:MM:SS)
            code: Optional stencil code filter. If None, returns all stencils.

        Returns:
            List of dictionaries containing record data
        """
        with self.connection.connect() as conn:
            if code:
                stencil_id = self._get_stencil_id(code)
                cursor = conn.execute("""
                    SELECT tr.*, s.code as stencil_code
                    FROM tension_records tr
                    JOIN stencils s ON tr.stencil_id = s.id
                    WHERE tr.stencil_id = ?
                    AND tr.timestamp >= ? AND tr.timestamp <= ?
                    ORDER BY tr.timestamp DESC
                """, (stencil_id, start_date, end_date))
            else:
                cursor = conn.execute("""
                    SELECT tr.*, s.code as stencil_code
                    FROM tension_records tr
                    JOIN stencils s ON tr.stencil_id = s.id
                    WHERE tr.timestamp >= ? AND tr.timestamp <= ?
                    ORDER BY tr.timestamp DESC
                """, (start_date, end_date))

            return [dict(row) for row in cursor.fetchall()]

    def get_latest(self, code: str) -> Optional[TensionRecord]:
        """
        Retrieve the most recent tension measurement for a stencil.

        Args:
            code: Stencil code

        Returns:
            Latest TensionRecord if found, None otherwise
        """
        with self.connection.connect() as conn:
            stencil_id = self._get_stencil_id(code)
            if not stencil_id:
                return None

            cursor = conn.execute("""
                SELECT * FROM tension_records
                WHERE stencil_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """, (stencil_id,))

            row = cursor.fetchone()
            if not row:
                return None

            measurements = json.loads(row["measurements_json"]) if row["measurements_json"] else []
            return TensionRecord(
                timestamp=row["timestamp"],
                measurements=measurements,
                average_tension=row["average_tension"],
                min_tension=row["min_tension"],
                max_tension=row["max_tension"],
                result=row["result"],
                ok_count=row["ok_count"],
                warning_count=row["warning_count"],
                nok_count=row["nok_count"],
                operator=row["operator"],
                recipe_name=row["recipe_name"],
            )
