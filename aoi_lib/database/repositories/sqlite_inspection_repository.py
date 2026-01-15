"""
SQLite implementation of Inspection Repository.

Provides concrete implementation of InspectionRepository using SQLite database.
"""

import json
import logging
from typing import List, Dict, Any, Optional

from aoi_lib.database.connection import DatabaseConnection
from aoi_lib.database.repositories.inspection_repository import InspectionRepository
from aoi_lib.stencil_tracker import InspectionRecord

log = logging.getLogger(__name__)


class SqliteInspectionRepository(InspectionRepository):
    """
    SQLite implementation of inspection records repository.

    This repository manages inspection data persistence using SQLite,
    implementing all operations defined in InspectionRepository interface.

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

    def add(self, code: str, record: InspectionRecord) -> None:
        """
        Add an inspection record to the database.

        Args:
            code: Stencil code (must exist in stencils table)
            record: InspectionRecord object with inspection data

        Raises:
            ValueError: If stencil code does not exist
        """
        with self.connection.connect() as conn:
            stencil_id = self._get_stencil_id(code)
            if not stencil_id:
                raise ValueError(f"Stencil '{code}' não encontrado")

            # Insert record
            conn.execute("""
                INSERT INTO inspection_records
                (stencil_id, timestamp, total_apertures, ok_count, partial_count,
                 blocked_count, result, pass_rate, gerber_file, operator,
                 recipe_name, report_path, defects_json, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                stencil_id,
                record.timestamp,
                record.total_apertures,
                record.ok_count,
                record.partial_count,
                record.blocked_count,
                record.result,
                record.pass_rate,
                record.gerber_file,
                record.operator,
                record.recipe_name,
                record.report_path,
                json.dumps(record.defects) if record.defects else None,
                record.notes,
            ))

            # Update stencil metadata
            conn.execute("""
                UPDATE stencils SET
                    last_inspection = ?,
                    inspection_count = inspection_count + 1,
                    status = CASE WHEN ? = 'FAIL' THEN 'warning' ELSE status END,
                    updated_at = ?
                WHERE id = ?
            """, (record.timestamp, record.result,
                  __import__('datetime').datetime.now().isoformat(), stencil_id))

        log.info(f"Registro de inspeção adicionado para {code}: {record.result}")

    def get_history(self, code: str, limit: int = 50) -> List[InspectionRecord]:
        """
        Retrieve inspection history for a stencil.

        Args:
            code: Stencil code
            limit: Maximum number of records to retrieve (default: 50)

        Returns:
            List of InspectionRecord objects, ordered by timestamp DESC
            (most recent first)
        """
        with self.connection.connect() as conn:
            stencil_id = self._get_stencil_id(code)
            if not stencil_id:
                return []

            cursor = conn.execute("""
                SELECT * FROM inspection_records
                WHERE stencil_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (stencil_id, limit))

            records = []
            for row in cursor.fetchall():
                defects = json.loads(row["defects_json"]) if row["defects_json"] else []
                records.append(InspectionRecord(
                    timestamp=row["timestamp"],
                    total_apertures=row["total_apertures"],
                    ok_count=row["ok_count"],
                    partial_count=row["partial_count"],
                    blocked_count=row["blocked_count"],
                    result=row["result"],
                    pass_rate=row["pass_rate"],
                    gerber_file=row["gerber_file"],
                    operator=row["operator"],
                    recipe_name=row["recipe_name"],
                    report_path=row["report_path"],
                    defects=defects,
                    notes=row["notes"] or "",
                ))

            return records

    def get_by_period(self, start_date: str, end_date: str,
                      code: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve inspection records within a date range.

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
                    SELECT ir.*, s.code as stencil_code
                    FROM inspection_records ir
                    JOIN stencils s ON ir.stencil_id = s.id
                    WHERE ir.stencil_id = ?
                    AND ir.timestamp >= ? AND ir.timestamp <= ?
                    ORDER BY ir.timestamp DESC
                """, (stencil_id, start_date, end_date))
            else:
                cursor = conn.execute("""
                    SELECT ir.*, s.code as stencil_code
                    FROM inspection_records ir
                    JOIN stencils s ON ir.stencil_id = s.id
                    WHERE ir.timestamp >= ? AND ir.timestamp <= ?
                    ORDER BY ir.timestamp DESC
                """, (start_date, end_date))

            return [dict(row) for row in cursor.fetchall()]

    def get_stats(self, code: str) -> Dict[str, Any]:
        """
        Calculate inspection statistics for a stencil.

        Args:
            code: Stencil code

        Returns:
            Dictionary with statistics:
            - total_inspections: Total number of inspections
            - pass_count: Number of PASS results
            - fail_count: Number of FAIL results
            - pass_rate: Percentage of PASS results (0-100)
            - avg_pass_rate: Average pass_rate across all inspections
            - last_result: Result of most recent inspection (or None)
        """
        with self.connection.connect() as conn:
            stencil_id = self._get_stencil_id(code)
            if not stencil_id:
                return {
                    "total_inspections": 0,
                    "pass_count": 0,
                    "fail_count": 0,
                    "pass_rate": 0.0,
                    "avg_pass_rate": 0.0,
                    "last_result": None,
                }

            cursor = conn.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN result = 'PASS' THEN 1 ELSE 0 END) as pass_count,
                    SUM(CASE WHEN result = 'FAIL' THEN 1 ELSE 0 END) as fail_count,
                    AVG(pass_rate) as avg_pass_rate,
                    MAX(timestamp) as last_timestamp,
                    MAX(CASE WHEN timestamp = (SELECT MAX(timestamp) FROM inspection_records WHERE stencil_id = ?)
                        THEN result END) as last_result
                FROM inspection_records
                WHERE stencil_id = ?
            """, (stencil_id, stencil_id))

            row = cursor.fetchone()

            total = row["total"] or 0
            pass_count = row["pass_count"] or 0
            fail_count = row["fail_count"] or 0
            avg_pass_rate = row["avg_pass_rate"] or 0.0

            return {
                "total_inspections": total,
                "pass_count": pass_count,
                "fail_count": fail_count,
                "pass_rate": (pass_count / total * 100) if total > 0 else 0.0,
                "avg_pass_rate": avg_pass_rate,
                "last_result": row["last_result"],
            }

    def get_combined_history(self, code: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Retrieve combined history of tension and inspection records.

        This method merges both types of records into a single timeline,
        ordered by timestamp (most recent first).

        Args:
            code: Stencil code
            limit: Maximum number of records to retrieve (default: 50)

        Returns:
            List of dictionaries with keys:
            - type: "tension" or "inspection"
            - timestamp: ISO format timestamp
            - result: Result code (OK/NOK or PASS/FAIL)
            - Plus type-specific fields
        """
        with self.connection.connect() as conn:
            stencil_id = self._get_stencil_id(code)
            if not stencil_id:
                return []

            # Get tension records
            cursor = conn.execute("""
                SELECT 'tension' as type, timestamp, result,
                       average_tension, ok_count, warning_count, nok_count
                FROM tension_records
                WHERE stencil_id = ?
            """, (stencil_id,))

            tension_records = [dict(row) for row in cursor.fetchall()]

            # Get inspection records
            cursor = conn.execute("""
                SELECT 'inspection' as type, timestamp, result,
                       total_apertures, ok_count, partial_count, blocked_count, pass_rate
                FROM inspection_records
                WHERE stencil_id = ?
            """, (stencil_id,))

            inspection_records = [dict(row) for row in cursor.fetchall()]

            # Combine and sort by timestamp DESC
            combined = tension_records + inspection_records
            combined.sort(key=lambda x: x["timestamp"], reverse=True)

            return combined[:limit]
