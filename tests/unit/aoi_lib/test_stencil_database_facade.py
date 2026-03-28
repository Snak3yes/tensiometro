"""
Testes para StencilDatabase como fachada.
"""

import json
from pathlib import Path
from datetime import datetime

import pytest

from aoi_lib.stencil_database import StencilDatabase
from aoi_lib.stencil_tracker import Stencil, TensionRecord


@pytest.fixture
def temp_db_path(tmp_path):
    return tmp_path / "test.db"


@pytest.fixture
def db(temp_db_path):
    return StencilDatabase(str(temp_db_path))


class TestStencilDatabaseFacade:
    def test_init_creates_database_file(self, db):
        assert db.db_path.exists()

    def test_stencil_exists_delegates_to_repository(self, db):
        db.create_stencil("TEST001", "Test Stencil")
        assert db.stencil_exists("TEST001") is True
        assert db.stencil_exists("NONEXISTENT") is False

    def test_get_stencil_delegates_to_repository(self, db):
        db.create_stencil("TEST001", "Test Stencil")
        stencil = db.get_stencil("TEST001")

        assert stencil is not None
        assert stencil.code == "TEST001"
        assert stencil.description == "Test Stencil"

    def test_create_stencil_delegates_to_repository(self, db):
        stencil = db.create_stencil("TEST001", "Test", "Recipe1")

        assert stencil.code == "TEST001"
        assert stencil.description == "Test"
        assert stencil.recipe_name == "Recipe1"

    def test_create_stencil_raises_for_duplicate(self, db):
        db.create_stencil("TEST001")
        with pytest.raises(ValueError, match="já existe"):
            db.create_stencil("TEST001")

    def test_update_stencil_delegates_to_repository(self, db):
        db.create_stencil("TEST001", "Original")
        stencil = db.get_stencil("TEST001")
        stencil.description = "Updated"

        db.update_stencil(stencil)
        updated = db.get_stencil("TEST001")

        assert updated.description == "Updated"

    def test_update_stencil_raises_for_nonexistent(self, db):
        stencil = Stencil(code="NONEXISTENT", description="Test")
        with pytest.raises(ValueError, match="não existe"):
            db.update_stencil(stencil)

    def test_list_stencils_delegates_to_repository(self, db):
        db.create_stencil("TEST001", "Test 1")
        db.create_stencil("TEST002", "Test 2")

        stencils = db.list_stencils()
        codes = {s.code for s in stencils}
        assert codes == {"TEST001", "TEST002"}

    def test_delete_stencil_delegates_to_repository(self, db):
        db.create_stencil("TEST001")

        result = db.delete_stencil("TEST001")

        assert result is True
        assert db.stencil_exists("TEST001") is False

    def test_add_tension_record_delegates_to_repository(self, db):
        db.create_stencil("TEST001")
        record = TensionRecord(
            timestamp=datetime.now().isoformat(),
            measurements=[],
            average_tension=30.0,
            min_tension=30.0,
            max_tension=30.0,
            result="OK",
            ok_count=1,
            warning_count=0,
            nok_count=0,
        )

        db.add_tension_record("TEST001", record)
        history = db.get_tension_history("TEST001")

        assert len(history) == 1
        assert history[0].average_tension == 30.0

    def test_get_tension_history_delegates_to_repository(self, db):
        db.create_stencil("TEST001")

        for i in range(3):
            record = TensionRecord(
                timestamp=f"2024-01-0{i+1}T10:00:00",
                measurements=[],
                average_tension=30.0 + i,
                min_tension=30.0 + i,
                max_tension=30.0 + i,
                result="OK",
                ok_count=1,
                warning_count=0,
                nok_count=0,
            )
            db.add_tension_record("TEST001", record)

        history = db.get_tension_history("TEST001")

        assert len(history) == 3
        assert history[0].average_tension == 32.0
        assert history[1].average_tension == 31.0
        assert history[2].average_tension == 30.0

    def test_get_tension_records_by_period_delegates_to_repository(self, db):
        db.create_stencil("TEST001")

        record1 = TensionRecord(
            timestamp="2024-01-05T10:00:00",
            measurements=[],
            average_tension=30.0,
            min_tension=30.0,
            max_tension=30.0,
            result="OK",
            ok_count=1,
            warning_count=0,
            nok_count=0,
        )
        record2 = TensionRecord(
            timestamp="2024-01-15T10:00:00",
            measurements=[],
            average_tension=31.0,
            min_tension=31.0,
            max_tension=31.0,
            result="OK",
            ok_count=1,
            warning_count=0,
            nok_count=0,
        )

        db.add_tension_record("TEST001", record1)
        db.add_tension_record("TEST001", record2)

        results = db.get_tension_records_by_period(
            "2024-01-01T00:00:00",
            "2024-01-10T23:59:59",
            "TEST001",
        )

        assert len(results) == 1
        assert results[0]["average_tension"] == 30.0

    def test_migrate_from_json_delegates_to_migrator(self, db, tmp_path):
        json_dir = tmp_path / "stencils"
        json_dir.mkdir()

        stencil_dir = json_dir / "TEST001"
        stencil_dir.mkdir()

        info = {"code": "TEST001", "description": "Migrated"}
        with open(stencil_dir / "info.json", "w", encoding="utf-8") as file:
            json.dump(info, file)

        stats = db.migrate_from_json(str(json_dir))

        assert stats["stencils"] == 1
        assert db.stencil_exists("TEST001")

    def test_backup_database_works(self, db, tmp_path):
        backup_path = tmp_path / "backup.db"
        result_path = db.backup_database(str(backup_path))

        assert Path(result_path).exists()
        assert Path(result_path).stat().st_size > 0

    def test_get_database_stats_returns_aggregates(self, db):
        stats = db.get_database_stats()

        assert "total_stencils" in stats
        assert "total_tension_records" in stats
        assert "database_size_bytes" in stats
