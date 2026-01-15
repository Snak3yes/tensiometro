"""
Testes para SqliteInspectionRepository.

Testa a implementação concreta do repositório de registros de inspeção usando SQLite.
"""

import pytest
import json
from datetime import datetime
from pathlib import Path

from aoi_lib.database.connection import SqliteConnection
from aoi_lib.database.repositories.inspection_repository import InspectionRepository
from aoi_lib.stencil_tracker import InspectionRecord, TensionRecord


@pytest.fixture
def temp_db_path(tmp_path):
    """Cria caminho temporário para banco de dados."""
    return tmp_path / "test.db"


@pytest.fixture
def sqlite_conn(temp_db_path):
    """Cria conexão SQLite para testes."""
    return SqliteConnection(str(temp_db_path))


@pytest.fixture
def init_schema(sqlite_conn):
    """Inicializa schema do banco de dados."""
    schema_sql = """
    CREATE TABLE IF NOT EXISTS stencils (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        created_at TEXT NOT NULL,
        last_inspection TEXT,
        inspection_count INTEGER DEFAULT 0,
        status TEXT DEFAULT 'active',
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

    CREATE TABLE IF NOT EXISTS inspection_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stencil_id INTEGER NOT NULL,
        timestamp TEXT NOT NULL,
        total_apertures INTEGER DEFAULT 0,
        ok_count INTEGER DEFAULT 0,
        partial_count INTEGER DEFAULT 0,
        blocked_count INTEGER DEFAULT 0,
        result TEXT DEFAULT 'PASS',
        pass_rate REAL DEFAULT 100.0,
        gerber_file TEXT,
        operator TEXT,
        recipe_name TEXT,
        report_path TEXT,
        defects_json TEXT,
        notes TEXT DEFAULT '',
        FOREIGN KEY (stencil_id) REFERENCES stencils(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_inspection_stencil ON inspection_records(stencil_id);
    CREATE INDEX IF NOT EXISTS idx_inspection_timestamp ON inspection_records(timestamp);
    """
    sqlite_conn.init_schema(schema_sql)


@pytest.fixture
def inspection_repo(sqlite_conn):
    """Cria repositório de inspeção para testes."""
    from aoi_lib.database.repositories.sqlite_inspection_repository import SqliteInspectionRepository
    return SqliteInspectionRepository(sqlite_conn)


@pytest.fixture
def tension_repo(sqlite_conn):
    """Cria repositório de tensão para testes (para get_combined_history)."""
    from aoi_lib.database.repositories.sqlite_tension_repository import SqliteTensionRepository
    return SqliteTensionRepository(sqlite_conn)


@pytest.fixture
def create_stencil(inspection_repo, init_schema):
    """Helper para criar stencil no banco."""
    now = datetime.now().isoformat()
    with inspection_repo.connection.connect() as conn:
        conn.execute("""
            INSERT INTO stencils (code, created_at, updated_at)
            VALUES (?, ?, ?)
        """, ("TEST001", now, now))
    return "TEST001"


class TestSqliteInspectionRepository:
    """Testa SqliteInspectionRepository."""

    def test_is_concrete_implementation(self, inspection_repo):
        """Verifica se SqliteInspectionRepository implementa InspectionRepository."""
        assert isinstance(inspection_repo, InspectionRepository)

    def test_add_adds_inspection_record(self, inspection_repo, init_schema, create_stencil):
        """Verifica se add() adiciona registro de inspeção."""
        # Criar registro
        record = InspectionRecord(
            timestamp=datetime.now().isoformat(),
            total_apertures=100,
            ok_count=95,
            partial_count=3,
            blocked_count=2,
            result="PASS",
            pass_rate=95.0,
            gerber_file="test.ger",
            operator="operator1",
            recipe_name="Recipe1",
            report_path="/path/report.pdf",
            defects=[{"x": 10, "y": 20, "type": "blocked"}],
            notes="Test notes",
        )

        # Adicionar
        inspection_repo.add(create_stencil, record)

        # Verificar se foi adicionado
        history = inspection_repo.get_history(create_stencil)
        assert len(history) == 1
        assert history[0].total_apertures == 100
        assert history[0].pass_rate == 95.0

    def test_add_updates_stencil_metadata(self, inspection_repo, init_schema, create_stencil):
        """Verifica se add() atualiza metadados do stencil."""
        now = datetime.now().isoformat()
        record = InspectionRecord(
            timestamp=now,
            total_apertures=100,
            ok_count=100,
            partial_count=0,
            blocked_count=0,
            result="PASS",
            pass_rate=100.0,
        )

        inspection_repo.add(create_stencil, record)

        # Verificar se stencil foi atualizado
        with inspection_repo.connection.connect() as conn:
            cursor = conn.execute("""
                SELECT last_inspection, inspection_count, status
                FROM stencils WHERE code = ?
            """, (create_stencil,))
            row = cursor.fetchone()

            assert row["last_inspection"] == now
            assert row["inspection_count"] == 1
            assert row["status"] == "active"

    def test_add_sets_warning_status_for_fail(self, inspection_repo, init_schema, create_stencil):
        """Verifica se add() define status warning para resultado FAIL."""
        record = InspectionRecord(
            timestamp=datetime.now().isoformat(),
            total_apertures=100,
            ok_count=50,
            partial_count=20,
            blocked_count=30,
            result="FAIL",
            pass_rate=50.0,
        )

        inspection_repo.add(create_stencil, record)

        # Verificar se status mudou para warning
        with inspection_repo.connection.connect() as conn:
            cursor = conn.execute("SELECT status FROM stencils WHERE code = ?", (create_stencil,))
            assert cursor.fetchone()["status"] == "warning"

    def test_add_raises_error_for_nonexistent_stencil(self, inspection_repo, init_schema):
        """Verifica se add() levanta erro para stencil inexistente."""
        record = InspectionRecord(
            timestamp=datetime.now().isoformat(),
            total_apertures=100,
            ok_count=100,
            partial_count=0,
            blocked_count=0,
            result="PASS",
            pass_rate=100.0,
        )

        with pytest.raises(ValueError, match="não encontrado"):
            inspection_repo.add("NONEXISTENT", record)

    def test_get_history_returns_records(self, inspection_repo, init_schema, create_stencil):
        """Verifica se get_history() retorna histórico."""
        # Adicionar 2 registros
        record1 = InspectionRecord(
            timestamp="2024-01-01T10:00:00",
            total_apertures=100,
            ok_count=90,
            partial_count=5,
            blocked_count=5,
            result="PASS",
            pass_rate=90.0,
        )

        record2 = InspectionRecord(
            timestamp="2024-01-02T10:00:00",
            total_apertures=100,
            ok_count=95,
            partial_count=3,
            blocked_count=2,
            result="PASS",
            pass_rate=95.0,
        )

        inspection_repo.add(create_stencil, record1)
        inspection_repo.add(create_stencil, record2)

        # Buscar histórico
        history = inspection_repo.get_history(create_stencil)

        assert len(history) == 2
        # Deve estar em ordem decrescente (mais recente primeiro)
        assert history[0].pass_rate == 95.0
        assert history[1].pass_rate == 90.0

    def test_get_history_respects_limit(self, inspection_repo, init_schema, create_stencil):
        """Verifica se get_history() respeita parâmetro limit."""
        # Adicionar 5 registros
        for i in range(5):
            record = InspectionRecord(
                timestamp=datetime.now().isoformat(),
                total_apertures=100,
                ok_count=100 - i,
                partial_count=0,
                blocked_count=i,
                result="PASS" if i < 2 else "FAIL",
                pass_rate=float(100 - i),
            )
            inspection_repo.add(create_stencil, record)

        # Buscar com limit=3
        history = inspection_repo.get_history(create_stencil, limit=3)

        assert len(history) == 3

    def test_get_history_returns_empty_for_nonexistent(self, inspection_repo, init_schema):
        """Verifica se get_history() retorna lista vazia para código inexistente."""
        history = inspection_repo.get_history("NONEXISTENT")
        assert history == []

    def test_get_by_period_filters_by_date(self, inspection_repo, init_schema, create_stencil):
        """Verifica se get_by_period() filtra por período."""
        # Adicionar registros em datas diferentes
        record1 = InspectionRecord(
            timestamp="2024-01-01T10:00:00",
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

        inspection_repo.add(create_stencil, record1)
        inspection_repo.add(create_stencil, record2)

        # Buscar por período (primeira quinzena de janeiro)
        results = inspection_repo.get_by_period(
            "2024-01-01T00:00:00",
            "2024-01-10T23:59:59",
            create_stencil
        )

        assert len(results) == 1
        assert results[0]["pass_rate"] == 90.0

    def test_get_by_period_without_code_filters_all(self, inspection_repo, init_schema):
        """Verifica se get_by_period() busca todos os stencils quando code=None."""
        # Criar 2 stencils
        now = datetime.now().isoformat()

        with inspection_repo.connection.connect() as conn:
            conn.execute("INSERT INTO stencils (code, created_at, updated_at) VALUES (?, ?, ?)",
                       ("STENCIL1", now, now))
            conn.execute("INSERT INTO stencils (code, created_at, updated_at) VALUES (?, ?, ?)",
                       ("STENCIL2", now, now))

        # Adicionar registro para cada stencil
        record1 = InspectionRecord(
            timestamp="2024-01-01T10:00:00",
            total_apertures=100,
            ok_count=95,
            partial_count=3,
            blocked_count=2,
            result="PASS",
            pass_rate=95.0,
        )

        record2 = InspectionRecord(
            timestamp="2024-01-01T11:00:00",
            total_apertures=100,
            ok_count=90,
            partial_count=5,
            blocked_count=5,
            result="PASS",
            pass_rate=90.0,
        )

        inspection_repo.add("STENCIL1", record1)
        inspection_repo.add("STENCIL2", record2)

        # Buscar todos (sem filtro de code)
        results = inspection_repo.get_by_period(
            "2024-01-01T00:00:00",
            "2024-01-01T23:59:59",
            None
        )

        assert len(results) == 2

    def test_get_stats_calculates_statistics(self, inspection_repo, init_schema, create_stencil):
        """Verifica se get_stats() calcula estatísticas corretamente."""
        # Adicionar 3 inspeções (2 PASS, 1 FAIL)
        inspection_repo.add(create_stencil, InspectionRecord(
            timestamp="2024-01-01T10:00:00",
            total_apertures=100,
            ok_count=90,
            partial_count=5,
            blocked_count=5,
            result="PASS",
            pass_rate=90.0,
        ))

        inspection_repo.add(create_stencil, InspectionRecord(
            timestamp="2024-01-02T10:00:00",
            total_apertures=100,
            ok_count=95,
            partial_count=3,
            blocked_count=2,
            result="PASS",
            pass_rate=95.0,
        ))

        inspection_repo.add(create_stencil, InspectionRecord(
            timestamp="2024-01-03T10:00:00",
            total_apertures=100,
            ok_count=50,
            partial_count=20,
            blocked_count=30,
            result="FAIL",
            pass_rate=50.0,
        ))

        # Buscar estatísticas
        stats = inspection_repo.get_stats(create_stencil)

        assert stats["total_inspections"] == 3
        assert stats["pass_count"] == 2
        assert stats["fail_count"] == 1
        assert stats["pass_rate"] == 66.66666666666666  # (2/3) * 100
        assert abs(stats["avg_pass_rate"] - 78.333) < 0.01  # (90 + 95 + 50) / 3
        assert stats["last_result"] == "FAIL"

    def test_get_stats_returns_zeros_for_no_inspections(self, inspection_repo, init_schema, create_stencil):
        """Verifica se get_stats() retorna zeros quando não há inspeções."""
        stats = inspection_repo.get_stats(create_stencil)

        assert stats["total_inspections"] == 0
        assert stats["pass_count"] == 0
        assert stats["fail_count"] == 0
        assert stats["pass_rate"] == 0.0
        assert stats["avg_pass_rate"] == 0.0
        assert stats["last_result"] is None

    def test_get_stats_returns_zeros_for_nonexistent(self, inspection_repo, init_schema):
        """Verifica se get_stats() retorna zeros para stencil inexistente."""
        stats = inspection_repo.get_stats("NONEXISTENT")

        assert stats["total_inspections"] == 0
        assert stats["pass_count"] == 0
        assert stats["fail_count"] == 0
        assert stats["pass_rate"] == 0.0
        assert stats["avg_pass_rate"] == 0.0
        assert stats["last_result"] is None

    def test_get_combined_history_merges_records(self, inspection_repo, init_schema, create_stencil, tension_repo):
        """Verifica se get_combined_history() merge tensão + inspeção."""
        # Adicionar registro de tensão
        tension_repo.add(create_stencil, TensionRecord(
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

        # Adicionar registro de inspeção
        inspection_repo.add(create_stencil, InspectionRecord(
            timestamp="2024-01-02T10:00:00",
            total_apertures=100,
            ok_count=95,
            partial_count=3,
            blocked_count=2,
            result="PASS",
            pass_rate=95.0,
        ))

        # Buscar histórico combinado
        combined = inspection_repo.get_combined_history(create_stencil)

        assert len(combined) == 2
        assert combined[0]["type"] == "inspection"  # Mais recente
        assert combined[1]["type"] == "tension"

    def test_get_combined_history_orders_by_timestamp(self, inspection_repo, init_schema, create_stencil, tension_repo):
        """Verifica se get_combined_history() ordena por timestamp."""
        # Adicionar em ordem aleatória
        inspection_repo.add(create_stencil, InspectionRecord(
            timestamp="2024-01-02T10:00:00",
            total_apertures=100,
            ok_count=95,
            partial_count=3,
            blocked_count=2,
            result="PASS",
            pass_rate=95.0,
        ))

        tension_repo.add(create_stencil, TensionRecord(
            timestamp="2024-01-03T10:00:00",
            measurements=[],
            average_tension=31.0,
            min_tension=31.0,
            max_tension=31.0,
            result="OK",
            ok_count=1,
            warning_count=0,
            nok_count=0,
        ))

        inspection_repo.add(create_stencil, InspectionRecord(
            timestamp="2024-01-01T10:00:00",
            total_apertures=100,
            ok_count=90,
            partial_count=5,
            blocked_count=5,
            result="PASS",
            pass_rate=90.0,
        ))

        # Buscar histórico combinado
        combined = inspection_repo.get_combined_history(create_stencil)

        # Deve estar ordenado por timestamp DESC
        assert combined[0]["timestamp"] == "2024-01-03T10:00:00"
        assert combined[1]["timestamp"] == "2024-01-02T10:00:00"
        assert combined[2]["timestamp"] == "2024-01-01T10:00:00"

    def test_get_combined_history_respects_limit(self, inspection_repo, init_schema, create_stencil, tension_repo):
        """Verifica se get_combined_history() respeita parâmetro limit."""
        # Adicionar 5 registros (3 tensão + 2 inspeção)
        for i in range(3):
            tension_repo.add(create_stencil, TensionRecord(
                timestamp=f"2024-01-0{i+1}T10:00:00",
                measurements=[],
                average_tension=30.0,
                min_tension=30.0,
                max_tension=30.0,
                result="OK",
                ok_count=1,
                warning_count=0,
                nok_count=0,
            ))

        for i in range(2):
            inspection_repo.add(create_stencil, InspectionRecord(
                timestamp=f"2024-01-0{i+4}T10:00:00",
                total_apertures=100,
                ok_count=100,
                partial_count=0,
                blocked_count=0,
                result="PASS",
                pass_rate=100.0,
            ))

        # Buscar com limit=3
        combined = inspection_repo.get_combined_history(create_stencil, limit=3)

        assert len(combined) == 3

    def test_get_combined_history_returns_empty_for_nonexistent(self, inspection_repo, init_schema):
        """Verifica se get_combined_history() retorna lista vazia para código inexistente."""
        combined = inspection_repo.get_combined_history("NONEXISTENT")
        assert combined == []
