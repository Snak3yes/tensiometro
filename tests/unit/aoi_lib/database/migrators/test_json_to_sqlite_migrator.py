"""
Testes para JsonToSqliteMigrator.
"""

import json

import pytest

from aoi_lib.database.connection import SqliteConnection
from aoi_lib.database.migrators import JsonToSqliteMigrator


@pytest.fixture
def temp_json_dir(tmp_path):
    json_dir = tmp_path / "stencils"
    json_dir.mkdir()

    stencil1_dir = json_dir / "STENCIL1"
    stencil1_dir.mkdir()

    info1 = {
        "code": "STENCIL1",
        "description": "Stencil Teste 1",
        "recipe_name": "Recipe1",
        "created_at": "2024-01-01T10:00:00",
        "last_inspection": "2024-01-15T10:00:00",
        "inspection_count": 5,
        "status": "active",
        "notes": "Test notes",
    }
    with open(stencil1_dir / "info.json", "w", encoding="utf-8") as file:
        json.dump(info1, file)

    history1_dir = stencil1_dir / "history"
    history1_dir.mkdir()

    tension1 = {
        "timestamp": "2024-01-10T10:00:00",
        "measurements": [{"x": 0, "y": 0, "value": 30.0}],
        "average_tension": 30.0,
        "min_tension": 30.0,
        "max_tension": 30.0,
        "result": "OK",
        "ok_count": 1,
        "warning_count": 0,
        "nok_count": 0,
    }
    with open(history1_dir / "2024-01-10_tension.json", "w", encoding="utf-8") as file:
        json.dump(tension1, file)

    stencil2_dir = json_dir / "STENCIL2"
    stencil2_dir.mkdir()
    info2 = {
        "code": "STENCIL2",
        "description": "Stencil Teste 2",
        "recipe_name": "Recipe2",
        "created_at": "2024-01-01T10:00:00",
        "status": "active",
    }
    with open(stencil2_dir / "info.json", "w", encoding="utf-8") as file:
        json.dump(info2, file)

    invalid_dir = json_dir / "INVALID"
    invalid_dir.mkdir()
    (invalid_dir / "data.txt").write_text("not json", encoding="utf-8")

    return json_dir


@pytest.fixture
def temp_db_path(tmp_path):
    return tmp_path / "test.db"


@pytest.fixture
def sqlite_conn(temp_db_path):
    return SqliteConnection(str(temp_db_path))


@pytest.fixture
def init_schema(sqlite_conn):
    schema_sql = """
    CREATE TABLE IF NOT EXISTS stencils (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        description TEXT,
        recipe_name TEXT,
        created_at TEXT NOT NULL,
        last_inspection TEXT,
        inspection_count INTEGER DEFAULT 0,
        status TEXT DEFAULT 'active',
        notes TEXT,
        updated_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS tension_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stencil_id INTEGER NOT NULL,
        timestamp TEXT NOT NULL,
        average_tension REAL DEFAULT 0,
        min_tension REAL DEFAULT 0,
        max_tension REAL DEFAULT 0,
        result TEXT DEFAULT 'OK',
        ok_count INTEGER DEFAULT 0,
        warning_count INTEGER DEFAULT 0,
        nok_count INTEGER DEFAULT 0,
        operator TEXT,
        recipe_name TEXT,
        measurements_json TEXT,
        FOREIGN KEY (stencil_id) REFERENCES stencils(id) ON DELETE CASCADE
    );
    """
    sqlite_conn.init_schema(schema_sql)


@pytest.fixture
def migrator(sqlite_conn, init_schema):
    return JsonToSqliteMigrator(sqlite_conn)


class TestJsonToSqliteMigrator:
    def test_migrate_stencils_from_json(self, migrator, temp_json_dir):
        stats = migrator.migrate(str(temp_json_dir))

        assert stats["stencils"] == 2
        assert stats["tension_records"] == 1

    def test_migrate_creates_stencil_with_all_fields(self, migrator, temp_json_dir):
        migrator.migrate(str(temp_json_dir))

        from aoi_lib.database.repositories import SqliteStencilRepository

        repo = SqliteStencilRepository(migrator.connection)
        stencil = repo.get("STENCIL1")

        assert stencil is not None
        assert stencil.code == "STENCIL1"
        assert stencil.description == "Stencil Teste 1"
        assert stencil.recipe_name == "Recipe1"

    def test_migrate_loads_tension_history(self, migrator, temp_json_dir):
        migrator.migrate(str(temp_json_dir))

        from aoi_lib.database.repositories import SqliteTensionRepository

        repo = SqliteTensionRepository(migrator.connection)
        history = repo.get_history("STENCIL1")
        assert len(history) == 1
        assert history[0].average_tension == 30.0
        assert history[0].result == "OK"

    def test_migrate_skips_existing_stencils(self, migrator, temp_json_dir):
        from aoi_lib.database.repositories import SqliteStencilRepository

        repo = SqliteStencilRepository(migrator.connection)
        repo.create("STENCIL1", "Existing", "RecipeX")

        stats = migrator.migrate(str(temp_json_dir))

        assert stats["stencils"] == 1
        stencil = repo.get("STENCIL1")
        assert stencil.description == "Existing"
        assert stencil.recipe_name == "RecipeX"

    def test_migrate_handles_missing_json_dir(self, migrator, tmp_path):
        stats = migrator.migrate(str(tmp_path / "missing"))
        assert stats == {"stencils": 0, "tension_records": 0}
