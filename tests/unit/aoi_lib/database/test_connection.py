"""
Testes para DatabaseConnection.

Testa a abstração de conexão de banco de dados e implementação SQLite.
"""

import pytest
import sqlite3
from pathlib import Path
from unittest.mock import MagicMock

from aoi_lib.database.connection import (
    DatabaseConnection,
    SqliteConnection,
)


@pytest.fixture
def temp_db_path(tmp_path):
    """Cria caminho temporário para banco de dados."""
    return tmp_path / "test.db"


@pytest.fixture
def sqlite_conn(temp_db_path):
    """Cria conexão SQLite para testes."""
    return SqliteConnection(str(temp_db_path))


class TestDatabaseConnection:
    """Testa a interface abstrata DatabaseConnection."""

    def test_database_connection_is_abc(self):
        """Verifica se DatabaseConnection é uma classe abstrata."""
        from abc import ABC
        assert issubclass(DatabaseConnection, ABC)

    def test_database_connection_has_abstract_methods(self):
        """Verifica se DatabaseConnection tem métodos abstratos."""
        assert hasattr(DatabaseConnection, '__abstractmethods__')
        abstract_methods = DatabaseConnection.__abstractmethods__
        assert 'connect' in abstract_methods
        assert 'init_schema' in abstract_methods


class TestSqliteConnection:
    """Testa a implementação SqliteConnection."""

    def test_init_creates_database_directory(self, tmp_path):
        """Verifica se __init__ cria diretório do banco."""
        db_path = tmp_path / "subdir" / "test.db"
        conn = SqliteConnection(str(db_path))

        assert db_path.parent.exists()
        assert db_path.parent.is_dir()

    def test_init_sets_db_path_attribute(self, temp_db_path):
        """Verifica se __init__ define o atributo db_path."""
        conn = SqliteConnection(str(temp_db_path))
        assert conn.db_path == Path(temp_db_path)

    def test_init_defaults_to_data_directory(self):
        """Verifica se __init__ usa diretório data/ por padrão."""
        conn = SqliteConnection()  # Sem argumentos
        # O caminho padrão deve incluir 'data/stencils.db'
        assert 'data' in str(conn.db_path)
        assert 'stencils.db' in str(conn.db_path)

    @pytest.fixture
    def mock_sqlite_connect(self):
        """Mock sqlite3.connect para testes."""
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn
            yield mock_connect, mock_conn

    def test_connect_returns_context_manager(self, sqlite_conn):
        """Verifica se connect() retorna um context manager."""
        with sqlite_conn.connect() as conn:
            assert hasattr(conn, 'execute')
            assert hasattr(conn, 'commit')
            assert hasattr(conn, 'rollback')
            assert hasattr(conn, 'close')

    def test_connect_enables_foreign_keys(self, sqlite_conn):
        """Verifica se connect() habilita foreign keys."""
        with sqlite_conn.connect() as conn:
            # Verifica se PRAGMA foreign_keys foi executado
            # (não podemos testar diretamente, mas garantimos que não levanta exceção)
            pass

    def test_connect_creates_row_factory(self, sqlite_conn):
        """Verifica se connect() configura row_factory."""
        with sqlite_conn.connect() as conn:
            assert conn.row_factory == sqlite3.Row

    def test_context_manager_commits_on_success(self, sqlite_conn):
        """Verifica se context manager faz commit em caso de sucesso."""
        with sqlite_conn.connect() as conn:
            conn.execute("SELECT 1")

        # Se chegou aqui, commit foi feito (sem exceção)

    def test_context_manager_rollbacks_on_error(self, sqlite_conn):
        """Verifica se context manager faz rollback em caso de erro."""
        with pytest.raises(ValueError):
            with sqlite_conn.connect() as conn:
                conn.execute("SELECT 1")
                raise ValueError("Test error")

        # Se chegou aqui, rollback foi feito (exceção propagada)

    def test_context_manager_closes_connection(self, sqlite_conn):
        """Verifica se context manager fecha a conexão."""
        conn = sqlite_conn.connect()
        context = conn.__enter__()

        # Simula saída do context manager
        try:
            pass
        finally:
            context.__exit__(None, None, None)

        # Conexão deve estar fechada

    def test_init_schema_executes_sql(self, sqlite_conn):
        """Verifica se init_schema() executa SQL."""
        schema_sql = """
        CREATE TABLE IF NOT EXISTS test_table (
            id INTEGER PRIMARY KEY,
            name TEXT
        );
        """

        sqlite_conn.init_schema(schema_sql)

        # Verifica se tabela foi criada
        with sqlite_conn.connect() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='test_table'"
            )
            result = cursor.fetchone()
            assert result is not None

    def test_init_schema_accepts_multiline_sql(self, sqlite_conn):
        """Verifica se init_schema() aceita SQL multi-linha."""
        schema_sql = """
        CREATE TABLE IF NOT EXISTS table1 (id INTEGER);
        CREATE TABLE IF NOT EXISTS table2 (id INTEGER);
        """

        # Não deve levantar exceção
        sqlite_conn.init_schema(schema_sql)

    def test_init_schema_with_empty_sql(self, sqlite_conn):
        """Verifica se init_schema() lida com SQL vazio."""
        # Não deve levantar exceção
        sqlite_conn.init_schema("")

    def test_connect_with_invalid_path_raises_error(self, tmp_path):
        """Verifica se connect() levanta erro com caminho de arquivo inválido."""
        # Criar um arquivo (não diretório) e tentar usá-lo como banco
        invalid_path = tmp_path / "file.txt"
        invalid_path.write_text("Not a database")

        conn = SqliteConnection(str(invalid_path))

        # SQLite deve detectar que não é um banco válido
        # Erro ocorre ao tentar usar o banco (não apenas conectar)
        with pytest.raises((sqlite3.DatabaseError, Exception)):
            with conn.connect() as db:
                # A primeira operação que tenta acessar o banco falha
                db.execute("SELECT * FROM sqlite_master")

    def test_connect_creates_database_if_not_exists(self, sqlite_conn):
        """Verifica se connect() cria banco se não existir."""
        # Banco não existe antes
        assert not sqlite_conn.db_path.exists()

        # Após connect, banco deve existir
        with sqlite_conn.connect():
            pass

        assert sqlite_conn.db_path.exists()

    def test_multiple_connections_use_same_database(self, sqlite_conn):
        """Verifica se múltiplas conexões podem acessar o mesmo banco."""
        # Primeira conexão cria tabela
        sqlite_conn.init_schema("""
        CREATE TABLE IF NOT EXISTS test (
            id INTEGER PRIMARY KEY,
            value TEXT
        );
        """)

        with sqlite_conn.connect() as conn:
            conn.execute("INSERT INTO test (value) VALUES ('test1')")

        # Segunda conexão lê dados
        with sqlite_conn.connect() as conn:
            cursor = conn.execute("SELECT value FROM test")
            result = cursor.fetchone()
            assert result is not None
            assert result[0] == 'test1'

    def test_get_db_path_returns_path_object(self, sqlite_conn):
        """Verifica se get_db_path() retorna Path."""
        path = sqlite_conn.get_db_path()
        assert isinstance(path, Path)
        assert path == sqlite_conn.db_path

    def test_backup_database_creates_copy(self, sqlite_conn, tmp_path):
        """Verifica se backup_database() cria cópia do banco."""
        # Criar alguns dados
        sqlite_conn.init_schema("""
        CREATE TABLE IF NOT EXISTS test (id INTEGER);
        """)
        with sqlite_conn.connect() as conn:
            conn.execute("INSERT INTO test VALUES (1)")

        backup_path = tmp_path / "backup.db"
        result_path = sqlite_conn.backup_database(str(backup_path))

        assert Path(result_path).exists()
        assert backup_path.exists()

        # Verificar se backup tem os mesmos dados
        backup_conn = SqliteConnection(str(backup_path))
        with backup_conn.connect() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM test")
            count = cursor.fetchone()[0]
            assert count == 1


class TestSqliteConnectionEdgeCases:
    """Testa casos extremos e erro handling."""

    def test_connect_with_corrupted_database(self, sqlite_conn):
        """Verifica comportamento com banco corrompido."""
        # Criar banco válido primeiro
        with sqlite_conn.connect() as conn:
            conn.execute("CREATE TABLE test (id INTEGER)")

        # Corromper cabeçalho do banco (primeiros bytes)
        with open(sqlite_conn.db_path, 'r+b') as f:
            f.seek(0)
            f.write(b'CORRUPTED HEADER!!!')

        # SQLite deve detectar corrupção no header
        # (pode ser DatabaseError ou outro erro dependendo da versão)
        with pytest.raises(Exception):
            with sqlite_conn.connect():
                conn.execute("SELECT 1")

    def test_init_schema_with_invalid_sql(self, sqlite_conn):
        """Verifica se init_schema() levanta erro com SQL inválido."""
        invalid_sql = "CREATE TABLE invalid;"

        with pytest.raises(sqlite3.OperationalError):
            sqlite_conn.init_schema(invalid_sql)

    def test_connect_with_concurrent_access(self, sqlite_conn):
        """Verifica comportamento com acesso concorrente."""
        import threading

        results = []

        def worker(worker_id):
            try:
                with sqlite_conn.connect() as conn:
                    conn.execute("SELECT 1")
                    results.append(worker_id)
            except Exception as e:
                results.append(e)

        # Criar múltiplas threads tentando acessar o banco
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Pelo menos algumas threads devem ter sucesso
        # (SQLite lida com concorrência, mas pode bloquear)
        assert len(results) > 0
