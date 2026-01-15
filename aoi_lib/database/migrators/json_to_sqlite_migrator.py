"""
JSON to SQLite Migrator.

Migrates data from JSON format to SQLite database using repositories.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any

from aoi_lib.database.connection import DatabaseConnection
from aoi_lib.database.repositories import (
    SqliteStencilRepository,
    SqliteTensionRepository,
    SqliteInspectionRepository,
)
from aoi_lib.stencil_tracker import TensionRecord, InspectionRecord

log = logging.getLogger(__name__)


class JsonToSqliteMigrator:
    """
    Migrates stencil data from JSON files to SQLite database.

    This class handles migration of legacy JSON data to the new SQLite
    database structure, using repositories for data access.

    Migration structure:
    - data/stencils/
      - STENCIL1/
        - info.json (stencil metadata)
        - history/
          - 2024-01-10_tension.json
          - 2024-01-15_inspection.json
      - STENCIL2/
        - info.json
    """

    def __init__(self, connection: DatabaseConnection):
        """
        Initialize migrator with database connection.

        Args:
            connection: DatabaseConnection instance
        """
        self.connection = connection
        self.stencil_repo = SqliteStencilRepository(connection)
        self.tension_repo = SqliteTensionRepository(connection)
        self.inspection_repo = SqliteInspectionRepository(connection)

    def migrate(self, json_dir: str) -> Dict[str, int]:
        """
        Migrate all stencil data from JSON directory to SQLite.

        Args:
            json_dir: Path to directory containing stencil JSON data

        Returns:
            Dictionary with migration statistics:
            - stencils: Number of stencils migrated
            - tension_records: Number of tension records migrated
            - inspection_records: Number of inspection records migrated

        Notes:
            - Skips stencils that already exist (by code)
            - Continues on individual file errors (logs warning)
            - Idempotent: safe to run multiple times
        """
        json_path = Path(json_dir)

        if not json_path.exists():
            log.warning(f"Diretório JSON não encontrado: {json_dir}")
            return {
                "stencils": 0,
                "tension_records": 0,
                "inspection_records": 0,
            }

        stats = {
            "stencils": 0,
            "tension_records": 0,
            "inspection_records": 0,
        }

        log.info(f"Iniciando migração de: {json_path}")

        for item in json_path.iterdir():
            if not item.is_dir():
                continue

            info_path = item / "info.json"
            if not info_path.exists():
                continue

            try:
                # Migrate stencil
                code = self._migrate_stencil(info_path, item.name)
                if code:
                    stats["stencils"] += 1
                    log.debug(f"Stencil migrado: {code}")

                    # Migrate tension history
                    tension_count = self._migrate_tension_history(
                        item / "history", code
                    )
                    stats["tension_records"] += tension_count

                    # Migrate inspection history
                    inspection_count = self._migrate_inspection_history(
                        item / "history", code
                    )
                    stats["inspection_records"] += inspection_count

            except Exception as e:
                log.error(f"Erro ao migrar {item}: {e}")

        log.info(f"Migração concluída: {stats}")
        return stats

    def _migrate_stencil(self, info_path: Path, default_code: str) -> str:
        """
        Migrate a single stencil from info.json.

        Args:
            info_path: Path to info.json file
            default_code: Default code from directory name

        Returns:
            Stencil code if migrated, None if already exists
        """
        try:
            with open(info_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            log.warning(f"JSON inválido em {info_path}: {e}")
            return ""

        code = data.get("code", default_code)

        # Skip if already exists
        if self.stencil_repo.exists(code):
            log.debug(f"Stencil {code} já existe, pulando")
            return ""

        # Use repository create() method for initial insert
        # But extract created_at from JSON to preserve it
        created_at = data.get("created_at")
        if not created_at:
            from datetime import datetime
            created_at = datetime.now().isoformat()

        # Insert directly to preserve created_at
        with self.connection.connect() as conn:
            conn.execute("""
                INSERT INTO stencils
                (code, description, recipe_name, created_at, last_inspection,
                 inspection_count, status, notes, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                code,
                data.get("description", ""),
                data.get("recipe_name"),
                created_at,
                data.get("last_inspection"),
                data.get("inspection_count", 0),
                data.get("status", "active"),
                data.get("notes", ""),
                created_at,  # updated_at same as created_at initially
            ))

        return code

    def _migrate_tension_history(self, history_dir: Path, code: str) -> int:
        """
        Migrate tension history files for a stencil.

        Args:
            history_dir: Path to history directory
            code: Stencil code

        Returns:
            Number of records migrated
        """
        if not history_dir.exists():
            return 0

        count = 0
        for hist_file in history_dir.glob("*_tension.json"):
            try:
                with open(hist_file, "r", encoding="utf-8") as f:
                    record_data = json.load(f)

                record = TensionRecord.from_dict(record_data)
                self.tension_repo.add(code, record)
                count += 1
                log.debug(f"Tension migrado: {hist_file.name}")

            except Exception as e:
                log.warning(f"Erro ao migrar {hist_file}: {e}")

        return count

    def _migrate_inspection_history(self, history_dir: Path, code: str) -> int:
        """
        Migrate inspection history files for a stencil.

        Args:
            history_dir: Path to history directory
            code: Stencil code

        Returns:
            Number of records migrated
        """
        if not history_dir.exists():
            return 0

        count = 0
        for hist_file in history_dir.glob("*_inspection.json"):
            try:
                with open(hist_file, "r", encoding="utf-8") as f:
                    record_data = json.load(f)

                record = InspectionRecord.from_dict(record_data)
                self.inspection_repo.add(code, record)
                count += 1
                log.debug(f"Inspection migrado: {hist_file.name}")

            except Exception as e:
                log.warning(f"Erro ao migrar {hist_file}: {e}")

        return count
