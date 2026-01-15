"""
Testes para JsonToSqliteMigrator.

Testa a migração de dados JSON para SQLite usando TDD.
"""

import pytest
import json
from pathlib import Path
from datetime import datetime

from aoi_lib.database.connection import SqliteConnection
from aoi_lib.database.repositories import (
    SqliteStencilRepository,
    SqliteTensionRepository,
    SqliteInspectionRepository,
)
from aoi_lib.database.migrators import JsonToSqliteMigrator


@pytest.fixture
def temp_json_dir(tmp_path):
    """Cria diretório temporário com dados JSON para teste."""
    json_dir = tmp_path / "stencils"
    json_dir.mkdir()

    # Cria stencil 1 com histórico completo
    stencil1_dir = json_dir / "STENCIL1"
    stencil1_dir.mkdir()

    # info.json
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
    with open(stencil1_dir / "info.json", "w") as f:
        json.dump(info1, f)

    # Histórico de tensão
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
    with open(history1_dir / "2024-01-10_tension.json", "w") as f:
        json.dump(tension1, f)

    # Histórico de inspeção
    inspection1 = {
        "timestamp": "2024-01-15T10:00:00",
        "total_apertures": 100,
        "ok_count": 95,
        "partial_count": 3,
        "blocked_count": 2,
        "result": "PASS",
        "pass_rate": 95.0,
        "defects": [{"x": 10, "y": 20, "type": "blocked"}],
    }
    with open(history1_dir / "2024-01-15_inspection.json", "w") as f:
        json.dump(inspection1, f)

    # Cria stencil 2 sem histórico
    stencil2_dir = json_dir / "STENCIL2"
    stencil2_dir.mkdir()

    info2 = {
        "code": "STENCIL2",
        "description": "Stencil Teste 2",
        "recipe_name": "Recipe2",
        "created_at": "2024-01-01T10:00:00",
        "status": "active",
    }
    with open(stencil2_dir / "info.json", "w") as f:
        json.dump(info2, f)

    # Cria subdiretório inválido (sem info.json)
    invalid_dir = json_dir / "INVALID"
    invalid_dir.mkdir()
    (invalid_dir / "data.txt").write_text("not json")

    return json_dir


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
    CREATE INDEX IF NOT EXISTS idx_tension_stencil ON tension_records(stencil_id);
    CREATE INDEX IF NOT EXISTS idx_tension_timestamp ON tension_records(timestamp);
    """
    sqlite_conn.init_schema(schema_sql)


@pytest.fixture
def migrator(sqlite_conn, init_schema):
    """Cria migrador para testes."""
    return JsonToSqliteMigrator(sqlite_conn)


class TestJsonToSqliteMigrator:
    """Testa JsonToSqliteMigrator."""

    def test_migrate_stencils_from_json(self, migrator, temp_json_dir):
        """Verifica se migra stencils do JSON para SQLite."""
        stats = migrator.migrate(str(temp_json_dir))

        assert stats["stencils"] == 2  # STENCIL1 e STENCIL2
        assert stats["tension_records"] == 1  # Apenas STENCIL1 tem
        assert stats["inspection_records"] == 1  # Apenas STENCIL1 tem

    def test_migrate_creates_stencil_with_all_fields(self, migrator, temp_json_dir):
        """Verifica se cria stencil com todos os campos do JSON."""
        migrator.migrate(str(temp_json_dir))

        from aoi_lib.database.repositories import SqliteStencilRepository
        repo = SqliteStencilRepository(migrator.connection)

        stencil = repo.get("STENCIL1")
        assert stencil is not None
        assert stencil.code == "STENCIL1"
        assert stencil.description == "Stencil Teste 1"
        assert stencil.recipe_name == "Recipe1"
        assert stencil.created_at == "2024-01-01T10:00:00"
        assert stencil.last_inspection == "2024-01-15T10:00:00"
        # inspection_count é incrementado quando registros são adicionados (5 original + 2 novos)
        assert stencil.inspection_count == 7
        assert stencil.status == "active"
        assert stencil.notes == "Test notes"

    def test_migrate_loads_tension_history(self, migrator, temp_json_dir):
        """Verifica se migra histórico de tensão."""
        migrator.migrate(str(temp_json_dir))

        from aoi_lib.database.repositories import SqliteTensionRepository
        repo = SqliteTensionRepository(migrator.connection)

        history = repo.get_history("STENCIL1")
        assert len(history) == 1
        assert history[0].average_tension == 30.0
        assert history[0].result == "OK"

    def test_migrate_loads_inspection_history(self, migrator, temp_json_dir):
        """Verifica se migra histórico de inspeção."""
        migrator.migrate(str(temp_json_dir))

        from aoi_lib.database.repositories import SqliteInspectionRepository
        repo = SqliteInspectionRepository(migrator.connection)

        history = repo.get_history("STENCIL1")
        assert len(history) == 1
        assert history[0].total_apertures == 100
        assert history[0].pass_rate == 95.0
        assert history[0].result == "PASS"

    def test_migrate_skips_existing_stencils(self, migrator, temp_json_dir):
        """Verifica se pula stencils que já existem."""
        from aoi_lib.database.repositories import SqliteStencilRepository
        repo = SqliteStencilRepository(migrator.connection)

        # Criar STENCIL1 manualmente antes da migração
        repo.create("STENCIL1", "Existing", "RecipeX")

        stats = migrator.migrate(str(temp_json_dir))

        # STENCIL1 já existia, então apenas STENCIL2 foi criado
        assert stats["stencils"] == 1

        # Verificar que STENCIL1 mantém dados originais
        stencil = repo.get("STENCIL1")
        assert stencil.description == "Existing"
        assert stencil.recipe_name == "RecipeX"

    def test_migrate_handles_missing_json_dir(self, migrator, tmp_path):
        """Verifica se retorna zeros quando diretório não existe."""
        nonexistent = tmp_path / "nonexistent"

        stats = migrator.migrate(str(nonexistent))

        assert stats["stencils"] == 0
        assert stats["tension_records"] == 0
        assert stats["inspection_records"] == 0

    def test_migrate_handles_corrupted_json_file(self, migrator, temp_json_dir):
        """Verifica se lida com arquivo JSON corrompido."""
        # Criar arquivo JSON inválido
        invalid_file = temp_json_dir / "STENCIL1" / "history" / "corrupted_tension.json"
        invalid_file.write_text("{invalid json content")

        stats = migrator.migrate(str(temp_json_dir))

        # Deve migrar os arquivos válidos mesmo com um corrompido
        assert stats["stencils"] == 2
        assert stats["tension_records"] == 1  # Apenas o válido
        assert stats["inspection_records"] == 1

    def test_migrate_handles_missing_history_dir(self, migrator, temp_json_dir):
        """Verifica se lida com stencil sem diretório history."""
        # STENCIL2 não tem diretório history, deve migrar sem erro
        stats = migrator.migrate(str(temp_json_dir))

        assert stats["stencils"] == 2
        assert stats["tension_records"] == 1
        assert stats["inspection_records"] == 1

    def test_migrate_uses_default_values(self, migrator, temp_json_dir):
        """Verifica se usa valores padrão quando campos faltam."""
        # Remover alguns campos do info.json do STENCIL2
        info_path = temp_json_dir / "STENCIL2" / "info.json"
        with open(info_path, "r") as f:
            data = json.load(f)

        # Remover campos opcionais
        data.pop("created_at", None)
        data.pop("last_inspection", None)
        data.pop("inspection_count", None)

        with open(info_path, "w") as f:
            json.dump(data, f)

        migrator.migrate(str(temp_json_dir))

        from aoi_lib.database.repositories import SqliteStencilRepository
        repo = SqliteStencilRepository(migrator.connection)

        stencil = repo.get("STENCIL2")
        assert stencil is not None
        # Valores devem ter padrões razoáveis
        assert stencil.code == "STENCIL2"
        assert stencil.status == "active"  # Default do banco

    def test_migrate_preserves_stencil_code_from_filename(self, migrator, temp_json_dir):
        """Verifica se usa nome do diretório como code quando não está no JSON."""
        # Criar stencil sem code no info.json
        stencil3_dir = temp_json_dir / "STENCIL3"
        stencil3_dir.mkdir()

        info3 = {"description": "Sem code"}
        with open(stencil3_dir / "info.json", "w") as f:
            json.dump(info3, f)

        migrator.migrate(str(temp_json_dir))

        from aoi_lib.database.repositories import SqliteStencilRepository
        repo = SqliteStencilRepository(migrator.connection)

        stencil = repo.get("STENCIL3")
        assert stencil is not None
        assert stencil.code == "STENCIL3"

    def test_migrate_validates_json_structure(self, migrator, temp_json_dir):
        """Verifica se valida estrutura básica do JSON."""
        # Criar info.json sem estrutura válida
        invalid_dir = temp_json_dir / "INVALID2"
        invalid_dir.mkdir()

        # JSON válido mas sem campos mínimos
        with open(invalid_dir / "info.json", "w") as f:
            json.dump({"random": "data"}, f)

        stats = migrator.migrate(str(temp_json_dir))

        # Deve usar nome do diretório como code
        assert stats["stencils"] == 3  # STENCIL1, STENCIL2, INVALID2

    def test_migrate_handles_empty_directory(self, migrator, tmp_path):
        """Verifica se lida com diretório vazio."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        stats = migrator.migrate(str(empty_dir))

        assert stats["stencils"] == 0
        assert stats["tension_records"] == 0
        assert stats["inspection_records"] == 0

    def test_migrate_returns_correct_statistics(self, migrator, temp_json_dir):
        """Verifica se retorna estatísticas corretas."""
        stats = migrator.migrate(str(temp_json_dir))

        assert isinstance(stats, dict)
        assert "stencils" in stats
        assert "tension_records" in stats
        assert "inspection_records" in stats
        assert stats["stencils"] == 2
        assert stats["tension_records"] == 1
        assert stats["inspection_records"] == 1

    def test_is_idempotent(self, migrator, temp_json_dir):
        """Verifica se migração é idempotente (pode rodar múltiplas vezes)."""
        # Primeira migração
        stats1 = migrator.migrate(str(temp_json_dir))

        # Segunda migração (mesmos dados)
        stats2 = migrator.migrate(str(temp_json_dir))

        # Segunda não deve adicionar nada novo
        assert stats2["stencils"] == 0
        assert stats2["tension_records"] == 0
        assert stats2["inspection_records"] == 0

        # Total deve ser o mesmo da primeira
        from aoi_lib.database.repositories import SqliteStencilRepository
        repo = SqliteStencilRepository(migrator.connection)
        stencils = repo.list()
        assert len(stencils) == stats1["stencils"]
