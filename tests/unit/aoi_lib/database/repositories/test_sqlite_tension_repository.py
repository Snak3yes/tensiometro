"""
Testes para SqliteTensionRepository.

Testa a implementação concreta do repositório de registros de tensão usando SQLite.
"""

import pytest
import json
from datetime import datetime
from pathlib import Path

from aoi_lib.database.connection import SqliteConnection
from aoi_lib.database.repositories.tension_repository import TensionRepository
from aoi_lib.stencil_tracker import TensionRecord


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

    CREATE INDEX IF NOT EXISTS idx_tension_stencil ON tension_records(stencil_id);
    CREATE INDEX IF NOT EXISTS idx_tension_timestamp ON tension_records(timestamp);
    """
    sqlite_conn.init_schema(schema_sql)


@pytest.fixture
def tension_repo(sqlite_conn):
    """Cria repositório de tensão para testes."""
    from aoi_lib.database.repositories.sqlite_tension_repository import SqliteTensionRepository
    return SqliteTensionRepository(sqlite_conn)


@pytest.fixture
def create_stencil(tension_repo, init_schema):
    """Helper para criar stencil no banco."""
    now = datetime.now().isoformat()
    with tension_repo.connection.connect() as conn:
        conn.execute("""
            INSERT INTO stencils (code, created_at, updated_at)
            VALUES (?, ?, ?)
        """, ("TEST001", now, now))
    return "TEST001"


class TestSqliteTensionRepository:
    """Testa SqliteTensionRepository."""

    def test_is_concrete_implementation(self, tension_repo):
        """Verifica se SqliteTensionRepository implementa TensionRepository."""
        assert isinstance(tension_repo, TensionRepository)

    def test_add_adds_tension_record(self, tension_repo, init_schema, create_stencil):
        """Verifica se add() adiciona registro de tensão."""
        # Criar registro
        record = TensionRecord(
            timestamp=datetime.now().isoformat(),
            measurements=[
                {"x": 0, "y": 0, "value": 30.0},
                {"x": 1, "y": 0, "value": 31.0},
            ],
            average_tension=30.5,
            min_tension=30.0,
            max_tension=31.0,
            result="OK",
            ok_count=2,
            warning_count=0,
            nok_count=0,
            operator="operator1",
            recipe_name="Recipe1",
        )

        # Adicionar
        tension_repo.add(create_stencil, record)

        # Verificar se foi adicionado
        history = tension_repo.get_history(create_stencil)
        assert len(history) == 1
        assert history[0].average_tension == 30.5

    def test_add_updates_stencil_metadata(self, tension_repo, init_schema, create_stencil):
        """Verifica se add() atualiza metadados do stencil."""
        now = datetime.now().isoformat()
        record = TensionRecord(
            timestamp=now,
            measurements=[],
            average_tension=30.0,
            min_tension=30.0,
            max_tension=30.0,
            result="OK",
            ok_count=1,
            warning_count=0,
            nok_count=0,
        )

        tension_repo.add(create_stencil, record)

        # Verificar se stencil foi atualizado
        with tension_repo.connection.connect() as conn:
            cursor = conn.execute("""
                SELECT last_inspection, inspection_count, status
                FROM stencils WHERE code = ?
            """, (create_stencil,))
            row = cursor.fetchone()

            assert row["last_inspection"] == now
            assert row["inspection_count"] == 1
            assert row["status"] == "active"

    def test_add_sets_warning_status_for_nok(self, tension_repo, init_schema, create_stencil):
        """Verifica se add() define status warning para resultado NOK."""
        record = TensionRecord(
            timestamp=datetime.now().isoformat(),
            measurements=[],
            average_tension=20.0,
            min_tension=20.0,
            max_tension=20.0,
            result="NOK",
            ok_count=0,
            warning_count=0,
            nok_count=1,
        )

        tension_repo.add(create_stencil, record)

        # Verificar se status mudou para warning
        with tension_repo.connection.connect() as conn:
            cursor = conn.execute("SELECT status FROM stencils WHERE code = ?", (create_stencil,))
            assert cursor.fetchone()["status"] == "warning"

    def test_add_raises_error_for_nonexistent_stencil(self, tension_repo, init_schema):
        """Verifica se add() levanta erro para stencil inexistente."""
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

        with pytest.raises(ValueError, match="não encontrado"):
            tension_repo.add("NONEXISTENT", record)

    def test_get_history_returns_records(self, tension_repo, init_schema, create_stencil):
        """Verifica se get_history() retorna histórico."""
        # Adicionar 2 registros com timestamps diferentes
        record1 = TensionRecord(
            timestamp="2024-01-01T10:00:00",
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
            timestamp="2024-01-02T10:00:00",
            measurements=[],
            average_tension=31.0,
            min_tension=31.0,
            max_tension=31.0,
            result="OK",
            ok_count=1,
            warning_count=0,
            nok_count=0,
        )

        tension_repo.add(create_stencil, record1)
        tension_repo.add(create_stencil, record2)

        # Buscar histórico
        history = tension_repo.get_history(create_stencil)

        assert len(history) == 2
        # Deve estar em ordem decrescente (mais recente primeiro)
        assert history[0].average_tension == 31.0
        assert history[1].average_tension == 30.0

    def test_get_history_respects_limit(self, tension_repo, init_schema, create_stencil):
        """Verifica se get_history() respeita parâmetro limit."""
        # Adicionar 5 registros
        for i in range(5):
            record = TensionRecord(
                timestamp=datetime.now().isoformat(),
                measurements=[],
                average_tension=float(30 + i),
                min_tension=float(30 + i),
                max_tension=float(30 + i),
                result="OK",
                ok_count=1,
                warning_count=0,
                nok_count=0,
            )
            tension_repo.add(create_stencil, record)

        # Buscar com limit=3
        history = tension_repo.get_history(create_stencil, limit=3)

        assert len(history) == 3

    def test_get_history_returns_empty_for_nonexistent(self, tension_repo, init_schema):
        """Verifica se get_history() retorna lista vazia para código inexistente."""
        history = tension_repo.get_history("NONEXISTENT")
        assert history == []

    def test_get_by_period_filters_by_date(self, tension_repo, init_schema, create_stencil):
        """Verifica se get_by_period() filtra por período."""
        # Adicionar registros em datas diferentes
        record1 = TensionRecord(
            timestamp="2024-01-01T10:00:00",
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

        tension_repo.add(create_stencil, record1)
        tension_repo.add(create_stencil, record2)

        # Buscar por período (primeira quinzena de janeiro)
        results = tension_repo.get_by_period(
            "2024-01-01T00:00:00",
            "2024-01-10T23:59:59",
            create_stencil
        )

        assert len(results) == 1
        assert results[0]["average_tension"] == 30.0

    def test_get_by_period_without_code_filters_all(self, tension_repo, init_schema):
        """Verifica se get_by_period() busca todos os stencils quando code=None."""
        # Criar 2 stencils
        now = datetime.now().isoformat()

        with tension_repo.connection.connect() as conn:
            conn.execute("INSERT INTO stencils (code, created_at, updated_at) VALUES (?, ?, ?)",
                       ("STENCIL1", now, now))
            conn.execute("INSERT INTO stencils (code, created_at, updated_at) VALUES (?, ?, ?)",
                       ("STENCIL2", now, now))

        # Adicionar registro para cada stencil
        record1 = TensionRecord(
            timestamp="2024-01-01T10:00:00",
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
            timestamp="2024-01-01T11:00:00",
            measurements=[],
            average_tension=31.0,
            min_tension=31.0,
            max_tension=31.0,
            result="OK",
            ok_count=1,
            warning_count=0,
            nok_count=0,
        )

        tension_repo.add("STENCIL1", record1)
        tension_repo.add("STENCIL2", record2)

        # Buscar todos (sem filtro de code)
        results = tension_repo.get_by_period(
            "2024-01-01T00:00:00",
            "2024-01-01T23:59:59",
            None
        )

        assert len(results) == 2

    def test_get_latest_returns_most_recent(self, tension_repo, init_schema, create_stencil):
        """Verifica se get_latest() retorna registro mais recente."""
        # Adicionar 2 registros
        record1 = TensionRecord(
            timestamp="2024-01-01T10:00:00",
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
            timestamp="2024-01-02T10:00:00",
            measurements=[],
            average_tension=31.0,
            min_tension=31.0,
            max_tension=31.0,
            result="OK",
            ok_count=1,
            warning_count=0,
            nok_count=0,
        )

        tension_repo.add(create_stencil, record1)
        tension_repo.add(create_stencil, record2)

        # Buscar mais recente
        latest = tension_repo.get_latest(create_stencil)

        assert latest is not None
        assert latest.average_tension == 31.0

    def test_get_latest_returns_none_for_nonexistent(self, tension_repo, init_schema):
        """Verifica se get_latest() retorna None para código inexistente."""
        latest = tension_repo.get_latest("NONEXISTENT")
        assert latest is None

    def test_get_latest_returns_none_when_no_records(self, tension_repo, init_schema, create_stencil):
        """Verifica se get_latest() retorna None quando não há registros."""
        # Stencil existe mas sem registros de tensão
        latest = tension_repo.get_latest(create_stencil)
        assert latest is None
