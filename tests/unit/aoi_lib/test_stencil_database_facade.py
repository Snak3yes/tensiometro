"""
Testes para StencilDatabase como fachada.

Testa backward compatibility após refatoração para Repository Pattern.
"""

import pytest
import json
from pathlib import Path
from datetime import datetime

from aoi_lib.stencil_database import StencilDatabase
from aoi_lib.stencil_tracker import Stencil, TensionRecord, InspectionRecord


@pytest.fixture
def temp_db_path(tmp_path):
    """Cria caminho temporário para banco de dados."""
    return tmp_path / "test.db"


@pytest.fixture
def db(temp_db_path):
    """Cria StencilDatabase para testes."""
    return StencilDatabase(str(temp_db_path))


class TestStencilDatabaseFacade:
    """Testa backward compatibility de StencilDatabase."""

    def test_init_creates_database_file(self, db):
        """Verifica se __init__ cria arquivo de banco."""
        assert db.db_path.exists()

    def test_stencil_exists_delegates_to_repository(self, db):
        """Verifica se stencil_exists delega para repositório."""
        db.create_stencil("TEST001", "Test Stencil")
        assert db.stencil_exists("TEST001") is True
        assert db.stencil_exists("NONEXISTENT") is False

    def test_get_stencil_delegates_to_repository(self, db):
        """Verifica se get_stencil delega para repositório."""
        db.create_stencil("TEST001", "Test Stencil")
        stencil = db.get_stencil("TEST001")

        assert stencil is not None
        assert stencil.code == "TEST001"
        assert stencil.description == "Test Stencil"

    def test_create_stencil_delegates_to_repository(self, db):
        """Verifica se create_stencil delega para repositório."""
        stencil = db.create_stencil("TEST001", "Test", "Recipe1")

        assert stencil.code == "TEST001"
        assert stencil.description == "Test"
        assert stencil.recipe_name == "Recipe1"

    def test_create_stencil_raises_for_duplicate(self, db):
        """Verifica se create_stencil levanta erro para código duplicado."""
        db.create_stencil("TEST001")
        with pytest.raises(ValueError, match="já existe"):
            db.create_stencil("TEST001")

    def test_update_stencil_delegates_to_repository(self, db):
        """Verifica se update_stencil delega para repositório."""
        db.create_stencil("TEST001", "Original")
        stencil = db.get_stencil("TEST001")
        stencil.description = "Updated"

        db.update_stencil(stencil)
        updated = db.get_stencil("TEST001")

        assert updated.description == "Updated"

    def test_update_stencil_raises_for_nonexistent(self, db):
        """Verifica se update_stencil levanta erro para stencil inexistente."""
        stencil = Stencil(code="NONEXISTENT", description="Test")
        with pytest.raises(ValueError, match="não existe"):
            db.update_stencil(stencil)

    def test_list_stencils_delegates_to_repository(self, db):
        """Verifica se list_stencils delega para repositório."""
        db.create_stencil("TEST001", "Test 1")
        db.create_stencil("TEST002", "Test 2")

        stencils = db.list_stencils()

        assert len(stencils) == 2
        codes = {s.code for s in stencils}
        assert codes == {"TEST001", "TEST002"}

    def test_list_stencils_filters_by_status(self, db):
        """Verifica se list_stencils filtra por status."""
        db.create_stencil("TEST001", "Test 1")
        db.create_stencil("TEST002", "Test 2")
        s = db.get_stencil("TEST002")
        s.status = "retired"
        db.update_stencil(s)

        active = db.list_stencils(status="active")
        retired = db.list_stencils(status="retired")

        assert len(active) == 1
        assert len(retired) == 1
        assert active[0].code == "TEST001"
        assert retired[0].code == "TEST002"

    def test_delete_stencil_delegates_to_repository(self, db):
        """Verifica se delete_stencil delega para repositório."""
        db.create_stencil("TEST001")

        result = db.delete_stencil("TEST001")

        assert result is True
        assert db.stencil_exists("TEST001") is False

    def test_delete_stencil_returns_false_for_nonexistent(self, db):
        """Verifica se delete_stencil retorna False para inexistente."""
        result = db.delete_stencil("NONEXISTENT")
        assert result is False

    def test_search_stencils_delegates_to_repository(self, db):
        """Verifica se search_stencils delega para repositório."""
        db.create_stencil("ABC001", "Stencil Alpha")
        db.create_stencil("XYZ001", "Stencil Beta")

        results = db.search_stencils("Alpha")

        assert len(results) == 1
        assert results[0].code == "ABC001"

    def test_get_stencils_by_recipe_delegates_to_repository(self, db):
        """Verifica se get_stencils_by_recipe delega para repositório."""
        db.create_stencil("TEST001", "Test 1", "RecipeA")
        db.create_stencil("TEST002", "Test 2", "RecipeA")
        db.create_stencil("TEST003", "Test 3", "RecipeB")

        results = db.get_stencils_by_recipe("RecipeA")

        assert len(results) == 2
        codes = {s.code for s in results}
        assert codes == {"TEST001", "TEST002"}

    def test_add_tension_record_delegates_to_repository(self, db):
        """Verifica se add_tension_record delega para repositório."""
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
        """Verifica se get_tension_history delega para repositório."""
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
        # Deve estar em ordem decrescente (mais recente primeiro)
        assert history[0].average_tension == 32.0
        assert history[1].average_tension == 31.0
        assert history[2].average_tension == 30.0

    def test_get_tension_records_by_period_delegates_to_repository(self, db):
        """Verifica se get_tension_records_by_period delega para repositório."""
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
            "TEST001"
        )

        assert len(results) == 1
        assert results[0]["average_tension"] == 30.0

    def test_add_inspection_record_delegates_to_repository(self, db):
        """Verifica se add_inspection_record delega para repositório."""
        db.create_stencil("TEST001")
        record = InspectionRecord(
            timestamp=datetime.now().isoformat(),
            total_apertures=100,
            ok_count=95,
            partial_count=3,
            blocked_count=2,
            result="PASS",
            pass_rate=95.0,
        )

        db.add_inspection_record("TEST001", record)
        history = db.get_inspection_history("TEST001")

        assert len(history) == 1
        assert history[0].total_apertures == 100

    def test_get_inspection_history_delegates_to_repository(self, db):
        """Verifica se get_inspection_history delega para repositório."""
        db.create_stencil("TEST001")

        for i in range(3):
            record = InspectionRecord(
                timestamp=f"2024-01-0{i+1}T10:00:00",
                total_apertures=100,
                ok_count=100 - i,
                partial_count=0,
                blocked_count=i,
                result="PASS" if i < 2 else "FAIL",
                pass_rate=float(100 - i),
            )
            db.add_inspection_record("TEST001", record)

        history = db.get_inspection_history("TEST001")

        assert len(history) == 3
        # Ordem decrescente (timestamp DESC)
        assert history[0].pass_rate == 98.0
        assert history[1].pass_rate == 99.0
        assert history[2].pass_rate == 100.0

    def test_get_inspection_stats_delegates_to_repository(self, db):
        """Verifica se get_inspection_stats delega para repositório."""
        db.create_stencil("TEST001")

        db.add_inspection_record("TEST001", InspectionRecord(
            timestamp="2024-01-01T10:00:00",
            total_apertures=100,
            ok_count=90,
            partial_count=5,
            blocked_count=5,
            result="PASS",
            pass_rate=90.0,
        ))

        db.add_inspection_record("TEST001", InspectionRecord(
            timestamp="2024-01-02T10:00:00",
            total_apertures=100,
            ok_count=95,
            partial_count=3,
            blocked_count=2,
            result="PASS",
            pass_rate=95.0,
        ))

        stats = db.get_inspection_stats("TEST001")

        assert stats["total_inspections"] == 2
        assert stats["pass_count"] == 2
        assert stats["fail_count"] == 0
        assert stats["pass_rate"] == 100.0

    def test_get_combined_history_delegates_to_repository(self, db):
        """Verifica se get_combined_history delega para repositório."""
        db.create_stencil("TEST001")

        db.add_tension_record("TEST001", TensionRecord(
            timestamp="2024-01-01T10:00:00",
            measurements=[],
            average_tension=30.0,
            min_tension=30.0,
            max_tension=30.0,
            result="OK",
            ok_count=1,
            warning_count=0,
            nok_count=0,
        ))

        db.add_inspection_record("TEST001", InspectionRecord(
            timestamp="2024-01-02T10:00:00",
            total_apertures=100,
            ok_count=95,
            partial_count=3,
            blocked_count=2,
            result="PASS",
            pass_rate=95.0,
        ))

        combined = db.get_combined_history("TEST001")

        assert len(combined) == 2
        # Inspeção mais recente primeiro
        assert combined[0]["type"] == "inspection"
        assert combined[1]["type"] == "tension"

    def test_get_inspection_records_by_period_delegates_to_repository(self, db):
        """Verifica se get_inspection_records_by_period delega para repositório."""
        db.create_stencil("TEST001")

        record1 = InspectionRecord(
            timestamp="2024-01-05T10:00:00",
            total_apertures=100,
            ok_count=90,
            partial_count=5,
            blocked_count=5,
            result="PASS",
            pass_rate=90.0,
        )

        record2 = InspectionRecord(
            timestamp="2024-01-15T10:00:00",
            total_apertures=100,
            ok_count=95,
            partial_count=3,
            blocked_count=2,
            result="PASS",
            pass_rate=95.0,
        )

        db.add_inspection_record("TEST001", record1)
        db.add_inspection_record("TEST001", record2)

        results = db.get_inspection_records_by_period(
            "2024-01-01T00:00:00",
            "2024-01-10T23:59:59",
            "TEST001"
        )

        assert len(results) == 1
        assert results[0]["pass_rate"] == 90.0

    def test_migrate_from_json_delegates_to_migrator(self, db, tmp_path):
        """Verifica se migrate_from_json delega para JsonToSqliteMigrator."""
        json_dir = tmp_path / "stencils"
        json_dir.mkdir()

        stencil_dir = json_dir / "TEST001"
        stencil_dir.mkdir()

        info = {"code": "TEST001", "description": "Migrated"}
        with open(stencil_dir / "info.json", "w") as f:
            json.dump(info, f)

        stats = db.migrate_from_json(str(json_dir))

        assert stats["stencils"] == 1
        assert db.stencil_exists("TEST001")

    def test_backup_database_works(self, db, tmp_path):
        """Verifica se backup_database funciona."""
        backup_path = tmp_path / "backup.db"
        result_path = db.backup_database(str(backup_path))

        assert Path(result_path).exists()
        assert Path(result_path).stat().st_size > 0

    def test_get_database_stats_returns_aggregates(self, db):
        """Verifica se get_database_stats retorna estatísticas agregadas."""
        stats = db.get_database_stats()

        assert "total_stencils" in stats
        assert "total_tension_records" in stats
        assert "total_inspection_records" in stats
        assert "database_size_bytes" in stats
