import pytest
import sqlite3
import os
import json
from pathlib import Path
from aoi_lib.stencil_database import StencilDatabase
from aoi_lib.stencil_tracker import Stencil, TensionRecord, InspectionRecord

@pytest.fixture
def db(tmp_path):
    """Cria um banco de dados em arquivo temporário para testes."""
    db_file = tmp_path / "test_stencils.db"
    database = StencilDatabase(db_path=str(db_file))
    return database

def test_create_and_get_stencil(db):
    """Testa criação e recuperação de um stencil."""
    db.create_stencil(code="STENCIL_001", description="Test Stencil")
    
    retrieved = db.get_stencil("STENCIL_001")
    assert retrieved is not None
    assert retrieved.code == "STENCIL_001"
    assert retrieved.description == "Test Stencil"

def test_stencil_exists(db):
    """Testa verificação de existência."""
    db.create_stencil(code="EXISTS_001")
    
    assert db.stencil_exists("EXISTS_001") is True
    assert db.stencil_exists("NON_EXISTENT") is False

def test_list_stencils(db):
    """Testa listagem de stencils."""
    db.create_stencil(code="S1")
    db.create_stencil(code="S2")
    
    stencils = db.list_stencils()
    assert len(stencils) >= 2
    codes = [s.code for s in stencils]
    assert "S1" in codes
    assert "S2" in codes

def test_delete_stencil(db):
    """Testa remoção de stencil."""
    db.create_stencil(code="TO_DELETE")
    assert db.stencil_exists("TO_DELETE") is True
    
    db.delete_stencil("TO_DELETE")
    assert db.stencil_exists("TO_DELETE") is False

def test_update_stencil(db):
    """Testa atualização de dados do stencil."""
    stencil = db.create_stencil(code="S_UPDATE", description="Original")
    stencil.description = "Updated"
    stencil.notes = "Some notes"
    
    db.update_stencil(stencil)
    
    updated = db.get_stencil("S_UPDATE")
    assert updated.description == "Updated"
    assert updated.notes == "Some notes"

def test_add_and_get_tension_records(db):
    """Testa adição e recuperação de registros de tensão."""
    db.create_stencil(code="STENCIL_TENSION")
    
    record = TensionRecord(
        timestamp="2026-01-10T10:00:00",
        average_tension=35.5,
        result="OK",
        measurements=[{"x": 10, "y": 20, "tension": 35.5, "status": "OK"}]
    )
    
    db.add_tension_record("STENCIL_TENSION", record)
    
    history = db.get_tension_history("STENCIL_TENSION")
    assert len(history) == 1
    assert history[0].average_tension == 35.5
    assert history[0].result == "OK"

def test_add_and_get_inspection_records(db):
    """Testa adição e recuperação de registros de inspeção visual."""
    db.create_stencil(code="STENCIL_INSP")
    
    record = InspectionRecord(
        timestamp="2026-01-10T11:00:00",
        total_apertures=100,
        ok_count=95,
        result="PASS",
        pass_rate=95.0
    )
    
    db.add_inspection_record("STENCIL_INSP", record)
    
    history = db.get_inspection_history("STENCIL_INSP")
    assert len(history) == 1
    assert history[0].total_apertures == 100
    assert history[0].result == "PASS"