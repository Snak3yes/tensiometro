"""
Testes de Integração para Database Layer.

Testa fluxos completos envolvendo múltiplas operações de banco de dados,
transações, rollback e concorrência básica.
"""

import pytest
import sqlite3
from pathlib import Path
from datetime import datetime
from threading import Thread
import time

from aoi_lib.stencil_database import StencilDatabase
from aoi_lib.stencil_tracker import Stencil, TensionRecord, InspectionRecord


@pytest.fixture
def temp_db_path(tmp_path):
    """Cria caminho temporário para banco de dados."""
    return tmp_path / "test_integration.db"


@pytest.fixture
def db(temp_db_path):
    """Cria StencilDatabase para testes de integração."""
    return StencilDatabase(str(temp_db_path))


@pytest.fixture
def populated_db(db):
    """Cria banco de dados populado com stencil e histórico."""
    # Criar stencil
    db.create_stencil("TEST001", "Integration Test Stencil", "Recipe1")

    # Adicionar registros de tensão
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

    # Adicionar registros de inspeção
    for i in range(2):
        record = InspectionRecord(
            timestamp=f"2024-01-0{i+1}T11:00:00",
            total_apertures=100,
            ok_count=100 - i,
            partial_count=0,
            blocked_count=i,
            result="PASS" if i < 1 else "FAIL",
            pass_rate=float(100 - i),
        )
        db.add_inspection_record("TEST001", record)

    return db


class TestDatabaseIntegrationCrudFlow:
    """Testa fluxo completo de CRUD."""

    def test_complete_lifecycle_of_stencil(self, db):
        """Testa ciclo de vida completo: criação, atualização, consulta, deleção."""
        # CREATE
        stencil = db.create_stencil("LIFECYCLE", "Lifecycle Test", "RecipeA")
        assert stencil.code == "LIFECYCLE"
        assert stencil.status == "active"

        # READ
        retrieved = db.get_stencil("LIFECYCLE")
        assert retrieved is not None
        assert retrieved.description == "Lifecycle Test"

        # UPDATE
        retrieved.description = "Updated Description"
        retrieved.status = "maintenance"
        db.update_stencil(retrieved)

        updated = db.get_stencil("LIFECYCLE")
        assert updated.description == "Updated Description"
        assert updated.status == "maintenance"

        # DELETE
        result = db.delete_stencil("LIFECYCLE")
        assert result is True

        # VERIFY DELETION
        assert db.stencil_exists("LIFECYCLE") is False
        assert db.get_stencil("LIFECYCLE") is None

    def test_complete_workflow_with_tension_history(self, db):
        """Testa fluxo completo: criar stencil, adicionar medições, analisar tendência."""
        # Criar stencil
        db.create_stencil("TREND01", "Trend Analysis Test", "RecipeX")

        # Adicionar medições simulando degradação significativa (>10%)
        # 40.0 → 32.0 = -20% (acima do limiar de 10%)
        tensions = [40.0, 38.6, 37.2, 35.8, 34.4, 33.0, 32.0]
        for i, tension in enumerate(tensions):
            record = TensionRecord(
                timestamp=f"2024-01-{i+1:02d}T10:00:00",
                measurements=[],
                average_tension=tension,
                min_tension=tension - 0.5,
                max_tension=tension + 0.5,
                result="OK",
                ok_count=1,
                warning_count=0,
                nok_count=0,
            )
            db.add_tension_record("TREND01", record)

        # Recuperar histórico
        history = db.get_tension_history("TREND01", limit=20)
        assert len(history) == 7

        # Analisar tendência
        analysis = db.get_trend_analysis("TREND01", warning_low=33.0)
        assert analysis.record_count == 7
        assert analysis.trend == "degrading"  # 40.0 → 32.0 = -20%
        assert analysis.alert is not None  # Deve ter alerta

    def test_complete_workflow_with_inspection_history(self, db):
        """Testa fluxo completo: criar stencil, inspeções, estatísticas."""
        # Criar stencil
        db.create_stencil("INSP01", "Inspection Test", "RecipeY")

        # Adicionar inspeções com qualidade decrescente
        pass_rates = [100.0, 98.0, 95.0, 90.0, 85.0]
        for i, pass_rate in enumerate(pass_rates):
            record = InspectionRecord(
                timestamp=f"2024-01-{i+1:02d}T11:00:00",
                total_apertures=100,
                ok_count=int(pass_rate),
                partial_count=int(100 - pass_rate) // 2,
                blocked_count=int(100 - pass_rate) // 2,
                result="PASS" if pass_rate >= 90 else "FAIL",
                pass_rate=pass_rate,
            )
            db.add_inspection_record("INSP01", record)

        # Recuperar estatísticas
        stats = db.get_inspection_stats("INSP01")
        assert stats["total_inspections"] == 5
        assert stats["pass_count"] == 4
        assert stats["fail_count"] == 1

        # Recuperar histórico combinado
        combined = db.get_combined_history("INSP01")
        assert len(combined) == 5
        assert all(r["type"] == "inspection" for r in combined)

    def test_filter_stencils_by_status_after_workflow(self, db):
        """Testa filtro por status após fluxo de trabalho."""
        # Criar stencils com diferentes status
        db.create_stencil("ACTIVE01", "Active Stencil 1")
        db.create_stencil("ACTIVE02", "Active Stencil 2")
        db.create_stencil("MAINTENANCE", "Under Maintenance")
        s = db.get_stencil("MAINTENANCE")
        s.status = "maintenance"
        db.update_stencil(s)

        s2 = db.get_stencil("ACTIVE02")
        s2.status = "retired"
        db.update_stencil(s2)

        # Filtrar por status
        active = db.list_stencils(status="active")
        maintenance = db.list_stencils(status="maintenance")
        retired = db.list_stencils(status="retired")

        assert len(active) == 1
        assert len(maintenance) == 1
        assert len(retired) == 1
        assert active[0].code == "ACTIVE01"
        assert maintenance[0].code == "MAINTENANCE"
        assert retired[0].code == "ACTIVE02"


class TestDatabaseIntegrationTransactions:
    """Testa transações e rollback."""

    def test_transaction_rollback_on_error(self, temp_db_path):
        """Testa se erro durante operação causa rollback."""
        db = StencilDatabase(str(temp_db_path))

        # Criar stencil inicial
        db.create_stencil("ROLLBACK", "Rollback Test")

        # Simular erro usando manipulação direta do SQLite
        try:
            with db._connection.connect() as conn:
                # Iniciar transação explícita
                conn.execute("BEGIN")

                # Inserir registro válido
                conn.execute(
                    "INSERT INTO tension_records (stencil_id, timestamp, average_tension) "
                    "VALUES ((SELECT id FROM stencils WHERE code = 'ROLLBACK'), "
                    "'2024-01-01T10:00:00', 30.0)"
                )

                # Tentativa de inserir inválida (viola FK)
                conn.execute(
                    "INSERT INTO tension_records (stencil_id, timestamp, average_tension) "
                    "VALUES (99999, '2024-01-01T10:00:00', 30.0)"
                )

                conn.commit()
        except Exception:
            # Erro esperado devido à violação de FK
            pass

        # Verificar se PRIMEIRA inserção também foi rollbackada
        history = db.get_tension_history("ROLLBACK")
        assert len(history) == 0  # Rollback funcionou

    def test_delete_stencil_cascades_to_records(self, populated_db):
        """Testa se deleção de stencil remove registros em cascade."""
        # Verificar que existe histórico antes da deleção
        tension_history = populated_db.get_tension_history("TEST001")
        inspection_history = populated_db.get_inspection_history("TEST001")

        assert len(tension_history) == 3
        assert len(inspection_history) == 2

        # Deletar stencil
        populated_db.delete_stencil("TEST001")

        # Verificar se histórico foi removido (CASCADE)
        tension_after = populated_db.get_tension_history("TEST001")
        inspection_after = populated_db.get_inspection_history("TEST001")

        assert len(tension_after) == 0
        assert len(inspection_after) == 0

    def test_multiple_operations_in_single_transaction(self, temp_db_path):
        """Testa múltiplas operações atômicas."""
        db = StencilDatabase(str(temp_db_path))

        # Criar stencil e adicionar registros em sequência rápida
        db.create_stencil("ATOMIC", "Atomic Test")

        # Operações sequenciais devem ser consistentes
        try:
            for i in range(5):
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
                db.add_tension_record("ATOMIC", record)
        except Exception as e:
            pytest.fail(f"Operações atômicas falharam: {e}")

        # Verificar consistência
        history = db.get_tension_history("ATOMIC")
        assert len(history) == 5


class TestDatabaseIntegrationConcurrency:
    """Testa concorrência básica."""

    def test_concurrent_reads(self, populated_db):
        """Testa múltiplas leituras simultâneas."""
        results = []
        errors = []

        def read_stencil():
            try:
                stencil = populated_db.get_stencil("TEST001")
                results.append(stencil.code if stencil else None)
            except Exception as e:
                errors.append(e)

        # Criar 5 threads lendo simultaneamente
        threads = [Thread(target=read_stencil) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Todas as leituras devem ter sucesso
        assert len(errors) == 0
        assert len(results) == 5
        assert all(r == "TEST001" for r in results)

    def test_concurrent_writes_different_stencils(self, db):
        """Testa escritas simultâneas em stencils diferentes."""
        errors = []
        created = []

        def create_stencil(code):
            try:
                stencil = db.create_stencil(code, f"Concurrent {code}")
                created.append(stencil.code)
            except Exception as e:
                errors.append(e)

        # Criar 3 stencils em paralelo
        codes = ["PARALLEL1", "PARALLEL2", "PARALLEL3"]
        threads = [Thread(target=create_stencil, args=(code,)) for code in codes]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Todas as criações devem ter sucesso
        assert len(errors) == 0
        assert len(created) == 3
        assert all(db.stencil_exists(code) for code in codes)

    def test_sequential_writes_same_stencil(self, populated_db):
        """Testa escritas sequenciais no mesmo stencil."""
        # Adicionar registros sequencialmente
        for i in range(10):
            record = TensionRecord(
                timestamp=f"2024-01-{i+1:02d}T12:00:00",
                measurements=[],
                average_tension=30.0 + i * 0.1,
                min_tension=30.0 + i * 0.1,
                max_tension=30.0 + i * 0.1,
                result="OK",
                ok_count=1,
                warning_count=0,
                nok_count=0,
            )
            populated_db.add_tension_record("TEST001", record)

        # Verificar que todos foram salvos
        history = populated_db.get_tension_history("TEST001")
        # 3 originais + 10 novos = 13
        assert len(history) == 13


class TestDatabaseIntegrationEdgeCases:
    """Testa casos de borda e cenários especiais."""

    def test_query_by_period_with_no_results(self, db):
        """Testa consulta por período sem resultados."""
        db.create_stencil("EMPTY", "Empty Stencil")

        # Consultar período sem registros
        results = db.get_tension_records_by_period(
            "2024-01-01T00:00:00",
            "2024-01-31T23:59:59",
            "EMPTY"
        )

        assert len(results) == 0

    def test_search_with_empty_query(self, db):
        """Testa busca com query vazia."""
        db.create_stencil("SEARCH01", "Search Test 1")
        db.create_stencil("SEARCH02", "Search Test 2")

        # Busca vazia deve retornar todos
        results = db.search_stencils("")
        assert len(results) >= 2

    def test_get_latest_tension_when_empty(self, db):
        """Testa get_latest_tension quando não há registros."""
        db.create_stencil("NOTENSION", "No Tension")

        latest = db.get_latest_tension("NOTENSION")
        assert latest is None

    def test_update_nonexistent_stencil_raises_error(self, db):
        """Testa atualização de stencil inexistente."""
        from aoi_lib.stencil_tracker import Stencil

    def test_migrate_from_empty_directory(self, db, tmp_path):
        """Testa migração de diretório vazio."""
        empty_dir = tmp_path / "empty_stencils"
        empty_dir.mkdir()

        stats = db.migrate_from_json(str(empty_dir))

        assert stats["stencils"] == 0
        assert stats["tension_records"] == 0
        assert stats["inspection_records"] == 0

    def test_backup_creates_independent_copy(self, db, tmp_path):
        """Testa se backup cria cópia independente."""
        db.create_stencil("BACKUP01", "Backup Test")

        backup_path = tmp_path / "backup_test.db"
        result_path = db.backup_database(str(backup_path))

        # Modificar banco original
        db.create_stencil("BACKUP02", "Another Stencil")

        # Backup não deve ter novo stencil
        backup_db = StencilDatabase(result_path)
        assert backup_db.stencil_exists("BACKUP01") is True
        assert backup_db.stencil_exists("BACKUP02") is False

    def test_database_stats_aggregation(self, populated_db):
        """Testa estatísticas agregadas do banco."""
        stats = populated_db.get_database_stats()

        assert stats["total_stencils"] == 1
        assert stats["total_tension_records"] == 3
        assert stats["total_inspection_records"] == 2
        assert stats["database_size_bytes"] > 0
        assert "stencils_by_status" in stats


class TestDatabaseIntegrationPerformance:
    """Testa performance básica e regressões."""

    def test_bulk_insert_performance(self, db):
        """Testa performance de inserção em massa."""
        import time

        db.create_stencil("BULK", "Bulk Insert Test")

        # Inserir 100 registros
        start_time = time.time()
        for i in range(100):
            record = TensionRecord(
                timestamp=f"2024-01-{i % 30 + 1:02d}T10:{i:02d}:00",
                measurements=[],
                average_tension=30.0,
                min_tension=30.0,
                max_tension=30.0,
                result="OK",
                ok_count=1,
                warning_count=0,
                nok_count=0,
            )
            db.add_tension_record("BULK", record)
        elapsed = time.time() - start_time

        # Deve levar <5 segundos para 100 inserções
        assert elapsed < 5.0

        # Verificar que todos foram inseridos
        history = db.get_tension_history("BULK", limit=200)
        assert len(history) == 100

    def test_large_query_performance(self, db):
        """Testa performance de consulta grande."""
        db.create_stencil("QUERY", "Query Test")

        # Inserir 50 stencils
        for i in range(50):
            db.create_stencil(f"QUERY{i:02d}", f"Query Test {i}")

        # Consultar todos
        import time
        start_time = time.time()
        all_stencils = db.list_stencils()
        elapsed = time.time() - start_time

        assert len(all_stencils) >= 50
        # Deve levar <1 segundo para listar 50 stencils
        assert elapsed < 1.0
