import pytest

from aoi_lib.stencil_database import StencilDatabase
from aoi_lib.stencil_tracker import TensionRecord


@pytest.fixture
def db(tmp_path):
    db_file = tmp_path / "test_stencils.db"
    return StencilDatabase(db_path=str(db_file))


def test_create_and_get_stencil(db):
    db.create_stencil(code="STENCIL_001", description="Test Stencil")

    retrieved = db.get_stencil("STENCIL_001")
    assert retrieved is not None
    assert retrieved.code == "STENCIL_001"
    assert retrieved.description == "Test Stencil"


def test_create_and_get_stencil_normalizes_lowercase_code(db):
    created = db.create_stencil(code="stencil_abc", description="Test Stencil")

    retrieved = db.get_stencil("stencil_abc")

    assert created.code == "STENCIL_ABC"
    assert retrieved is not None
    assert retrieved.code == "STENCIL_ABC"


def test_stencil_exists(db):
    db.create_stencil(code="EXISTS_001")

    assert db.stencil_exists("EXISTS_001") is True
    assert db.stencil_exists("NON_EXISTENT") is False


def test_list_stencils(db):
    db.create_stencil(code="S1")
    db.create_stencil(code="S2")

    stencils = db.list_stencils()
    codes = [s.code for s in stencils]
    assert "S1" in codes
    assert "S2" in codes


def test_delete_stencil(db):
    db.create_stencil(code="TO_DELETE")
    assert db.stencil_exists("TO_DELETE") is True

    db.delete_stencil("TO_DELETE")
    assert db.stencil_exists("TO_DELETE") is False


def test_update_stencil(db):
    stencil = db.create_stencil(code="S_UPDATE", description="Original")
    stencil.description = "Updated"
    stencil.notes = "Some notes"

    db.update_stencil(stencil)

    updated = db.get_stencil("S_UPDATE")
    assert updated.description == "Updated"
    assert updated.notes == "Some notes"


def test_add_and_get_tension_records(db):
    db.create_stencil(code="STENCIL_TENSION")

    record = TensionRecord(
        timestamp="2026-01-10T10:00:00",
        average_tension=35.5,
        result="OK",
        measurements=[{"x": 10, "y": 20, "tension": 35.5, "status": "OK"}],
    )

    db.add_tension_record("STENCIL_TENSION", record)

    history = db.get_tension_history("STENCIL_TENSION")
    assert len(history) == 1
    assert history[0].average_tension == 35.5
    assert history[0].result == "OK"


def test_get_database_stats(db):
    db.create_stencil(code="STATS")
    db.add_tension_record(
        "STATS",
        TensionRecord(timestamp="2026-01-10T10:00:00", average_tension=30.0, result="OK"),
    )

    stats = db.get_database_stats()
    assert stats["total_stencils"] >= 1
    assert stats["total_tension_records"] >= 1
