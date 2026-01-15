"""
Testes para SqliteStencilRepository.

Testa a implementação concreta do repositório de stencils usando SQLite.
"""

import pytest
from datetime import datetime
from pathlib import Path

from aoi_lib.database.connection import SqliteConnection
from aoi_lib.database.repositories.stencil_repository import StencilRepository
from aoi_lib.stencil_tracker import Stencil


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
        description TEXT DEFAULT '',
        recipe_name TEXT,
        created_at TEXT NOT NULL,
        last_inspection TEXT,
        inspection_count INTEGER DEFAULT 0,
        status TEXT DEFAULT 'active',
        notes TEXT DEFAULT '',
        updated_at TEXT NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_stencils_code ON stencils(code);
    CREATE INDEX IF NOT EXISTS idx_stencils_status ON stencils(status);
    """
    sqlite_conn.init_schema(schema_sql)


@pytest.fixture
def stencil_repo(sqlite_conn):
    """Cria repositório de stencils para testes."""
    from aoi_lib.database.repositories.sqlite_stencil_repository import SqliteStencilRepository
    return SqliteStencilRepository(sqlite_conn)


class TestSqliteStencilRepository:
    """Testa SqliteStencilRepository."""

    def test_is_concrete_implementation(self, stencil_repo):
        """Verifica se SqliteStencilRepository implementa StencilRepository."""
        assert isinstance(stencil_repo, StencilRepository)

    def test_exists_returns_true_for_existing_stencil(self, stencil_repo, init_schema):
        """Verifica se exists() retorna True para stencil existente."""
        # Criar stencil
        now = datetime.now().isoformat()
        with stencil_repo.connection.connect() as conn:
            conn.execute("""
                INSERT INTO stencils (code, description, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            """, ("TEST001", "Test Stencil", now, now))

        # Verificar
        assert stencil_repo.exists("TEST001") is True

    def test_exists_returns_false_for_nonexistent_stencil(self, stencil_repo, init_schema):
        """Verifica se exists() retorna False para stencil inexistente."""
        assert stencil_repo.exists("NONEXISTENT") is False

    def test_get_returns_stencil(self, stencil_repo, init_schema):
        """Verifica se get() retorna stencil correto."""
        # Criar stencil
        now = datetime.now().isoformat()
        with stencil_repo.connection.connect() as conn:
            conn.execute("""
                INSERT INTO stencils (code, description, recipe_name, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, ("TEST002", "Test Stencil", "Recipe1", now, now))

        # Buscar
        stencil = stencil_repo.get("TEST002")

        assert stencil is not None
        assert stencil.code == "TEST002"
        assert stencil.description == "Test Stencil"
        assert stencil.recipe_name == "Recipe1"

    def test_get_returns_none_for_nonexistent(self, stencil_repo, init_schema):
        """Verifica se get() retorna None para código inexistente."""
        assert stencil_repo.get("NONEXISTENT") is None

    def test_create_creates_new_stencil(self, stencil_repo, init_schema):
        """Verifica se create() cria novo stencil."""
        # Criar
        stencil = stencil_repo.create("TEST003", "New Stencil", "Recipe1")

        assert stencil is not None
        assert stencil.code == "TEST003"
        assert stencil.description == "New Stencil"
        assert stencil.recipe_name == "Recipe1"
        assert stencil.status == "active"

        # Verificar se foi salvo no banco
        assert stencil_repo.exists("TEST003") is True

    def test_create_raises_error_for_duplicate_code(self, stencil_repo, init_schema):
        """Verifica se create() levanta erro para código duplicado."""
        # Criar primeiro stencil
        stencil_repo.create("TEST004", "First", "Recipe1")

        # Tentar criar duplicado
        with pytest.raises(ValueError, match="já existe"):
            stencil_repo.create("TEST004", "Duplicate", "Recipe2")

    def test_update_updates_existing_stencil(self, stencil_repo, init_schema):
        """Verifica se update() atualiza stencil existente."""
        # Criar stencil
        stencil = stencil_repo.create("TEST005", "Original", "Recipe1")

        # Modificar
        stencil.description = "Modified"
        stencil.notes = "Test notes"

        # Atualizar
        stencil_repo.update(stencil)

        # Verificar
        updated = stencil_repo.get("TEST005")
        assert updated.description == "Modified"
        assert updated.notes == "Test notes"

    def test_update_raises_error_for_nonexistent(self, stencil_repo, init_schema):
        """Verifica se update() levanta erro para stencil inexistente."""
        stencil = Stencil(
            code="NONEXISTENT",
            description="Test",
            recipe_name=None,
            created_at=datetime.now().isoformat(),
        )

        with pytest.raises(ValueError, match="não existe"):
            stencil_repo.update(stencil)

    def test_delete_deletes_stencil(self, stencil_repo, init_schema):
        """Verifica se delete() remove stencil."""
        # Criar
        stencil_repo.create("TEST006", "To Delete", "Recipe1")

        # Deletar
        result = stencil_repo.delete("TEST006")

        assert result is True
        assert stencil_repo.exists("TEST006") is False

    def test_delete_returns_false_for_nonexistent(self, stencil_repo, init_schema):
        """Verifica se delete() retorna False para código inexistente."""
        assert stencil_repo.delete("NONEXISTENT") is False

    def test_list_returns_all_stencils(self, stencil_repo, init_schema):
        """Verifica se list() retorna todos os stencils."""
        # Criar múltiplos stencils
        stencil_repo.create("LIST001", "Stencil 1", "Recipe1")
        stencil_repo.create("LIST002", "Stencil 2", "Recipe2")
        stencil_repo.create("LIST003", "Stencil 3", "Recipe1")

        # Listar todos
        stencils = stencil_repo.list()

        assert len(stencils) == 3
        codes = [s.code for s in stencils]
        assert "LIST001" in codes
        assert "LIST002" in codes
        assert "LIST003" in codes

    def test_list_filters_by_status(self, stencil_repo, init_schema):
        """Verifica se list() filtra por status."""
        # Criar stencils com status diferente
        s1 = stencil_repo.create("STATUS001", "Active 1", "Recipe1")
        s2 = stencil_repo.create("STATUS002", "Active 2", "Recipe2")

        # Modificar status de um
        s2.status = "retired"
        stencil_repo.update(s2)

        # Listar apenas active
        active = stencil_repo.list(status="active")

        assert len(active) == 1
        assert active[0].code == "STATUS001"

    def test_search_finds_by_code(self, stencil_repo, init_schema):
        """Verifica se search() busca por código."""
        stencil_repo.create("SEARCH001", "Test", "Recipe1")
        stencil_repo.create("SEARCH002", "Test", "Recipe2")

        # Buscar por código
        results = stencil_repo.search("SEARCH001")

        assert len(results) == 1
        assert results[0].code == "SEARCH001"

    def test_search_finds_by_description(self, stencil_repo, init_schema):
        """Verifica se search() busca por descrição."""
        stencil_repo.create("SEARCH003", "Special Stencil", "Recipe1")
        stencil_repo.create("SEARCH004", "Normal Stencil", "Recipe2")

        # Buscar por descrição
        results = stencil_repo.search("Special")

        assert len(results) == 1
        assert results[0].code == "SEARCH003"

    def test_get_by_recipe_returns_stencils(self, stencil_repo, init_schema):
        """Verifica se get_by_recipe() retorna stencils por receita."""
        # Criar stencils com receitas diferentes
        stencil_repo.create("RECIPE001", "Stencil 1", "RecipeA")
        stencil_repo.create("RECIPE002", "Stencil 2", "RecipeB")
        stencil_repo.create("RECIPE003", "Stencil 3", "RecipeA")

        # Buscar por RecipeA
        results = stencil_repo.get_by_recipe("RecipeA")

        assert len(results) == 2
        codes = [s.code for s in results]
        assert "RECIPE001" in codes
        assert "RECIPE003" in codes

    def test_list_orders_by_last_inspection(self, stencil_repo, init_schema):
        """Verifica se list() ordena por last_inspection DESC."""
        now = datetime.now().isoformat()

        # Criar stencils com datas diferentes
        with stencil_repo.connection.connect() as conn:
            conn.execute("""
                INSERT INTO stencils (code, created_at, last_inspection, updated_at)
                VALUES (?, ?, ?, ?)
            """, ("ORDER001", now, "2024-01-01T10:00:00", now))

            conn.execute("""
                INSERT INTO stencils (code, created_at, last_inspection, updated_at)
                VALUES (?, ?, ?, ?)
            """, ("ORDER002", now, "2024-01-02T10:00:00", now))

            conn.execute("""
                INSERT INTO stencils (code, created_at, updated_at)
                VALUES (?, ?, ?)
            """, ("ORDER003", now, now))

        # Listar
        stencils = stencil_repo.list()

        # ORDER002 (mais recente) deve vir primeiro
        assert stencils[0].code == "ORDER002"
        # ORDER003 (sem inspeção, NULL) deve vir por último
        assert stencils[-1].code == "ORDER003"
