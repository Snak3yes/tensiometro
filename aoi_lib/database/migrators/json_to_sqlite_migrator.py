"""
JSON to SQLite Migrator.

Migrates tension-oriented stencil data from JSON format to SQLite database.
"""

import json
import logging
from pathlib import Path
from typing import Dict

from aoi_lib.database.connection import DatabaseConnection
from aoi_lib.database.repositories import SqliteStencilRepository, SqliteTensionRepository
from aoi_lib.stencil_tracker import TensionRecord

log = logging.getLogger(__name__)


class JsonToSqliteMigrator:
    """Migrates stencil data from JSON files to SQLite database."""

    def __init__(self, connection: DatabaseConnection):
        self.connection = connection
        self.stencil_repo = SqliteStencilRepository(connection)
        self.tension_repo = SqliteTensionRepository(connection)

    def migrate(self, json_dir: str) -> Dict[str, int]:
        json_path = Path(json_dir)

        if not json_path.exists():
            log.warning(f"Diretório JSON não encontrado: {json_dir}")
            return {
                "stencils": 0,
                "tension_records": 0,
            }

        stats = {
            "stencils": 0,
            "tension_records": 0,
        }

        log.info(f"Iniciando migração de: {json_path}")

        for item in json_path.iterdir():
            if not item.is_dir():
                continue

            info_path = item / "info.json"
            if not info_path.exists():
                continue

            try:
                code = self._migrate_stencil(info_path, item.name)
                if code:
                    stats["stencils"] += 1
                    stats["tension_records"] += self._migrate_tension_history(item / "history", code)
            except Exception as exc:
                log.error(f"Erro ao migrar {item}: {exc}")

        log.info(f"Migração concluída: {stats}")
        return stats

    def _migrate_stencil(self, info_path: Path, default_code: str) -> str:
        try:
            with open(info_path, "r", encoding="utf-8") as file:
                data = json.load(file)
        except json.JSONDecodeError as exc:
            log.warning(f"JSON inválido em {info_path}: {exc}")
            return ""

        code = data.get("code", default_code)

        if self.stencil_repo.exists(code):
            log.debug(f"Stencil {code} já existe, pulando")
            return ""

        created_at = data.get("created_at")
        if not created_at:
            from datetime import datetime
            created_at = datetime.now().isoformat()

        with self.connection.connect() as conn:
            conn.execute(
                """
                INSERT INTO stencils
                (code, description, recipe_name, created_at, last_inspection,
                 inspection_count, status, notes, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    code,
                    data.get("description", ""),
                    data.get("recipe_name"),
                    created_at,
                    data.get("last_inspection"),
                    data.get("inspection_count", 0),
                    data.get("status", "active"),
                    data.get("notes", ""),
                    created_at,
                ),
            )

        return code

    def _migrate_tension_history(self, history_dir: Path, code: str) -> int:
        if not history_dir.exists():
            return 0

        count = 0
        for hist_file in history_dir.glob("*_tension.json"):
            try:
                with open(hist_file, "r", encoding="utf-8") as file:
                    record_data = json.load(file)

                record = TensionRecord.from_dict(record_data)
                self.tension_repo.add(code, record)
                count += 1
                log.debug(f"Tension migrado: {hist_file.name}")
            except Exception as exc:
                log.warning(f"Erro ao migrar {hist_file}: {exc}")

        return count
