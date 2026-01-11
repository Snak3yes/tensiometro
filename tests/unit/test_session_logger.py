"""
Testes Unitários para SessionLogger

Testa o SessionLogger de forma isolada, focando em:
- Criação e gerenciamento de sessões
- Registro de ações
- Persistência em arquivo JSON
- Consulta de histórico e estatísticas
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import patch

from consumo_lib.managers.session_logger import SessionLogger


@pytest.fixture
def temp_log_dir(tmp_path):
    """Cria diretório temporário para logs."""
    return tmp_path / "sessions"


@pytest.fixture
def session_logger(temp_log_dir):
    """Cria SessionLogger com diretório temporário."""
    return SessionLogger(log_dir=str(temp_log_dir))


class TestSessionLoggerCreation:
    """Testa criação e inicialização do SessionLogger."""

    def test_create_session_logger(self, session_logger):
        """SessionLogger deve ser criado com sucesso."""
        assert session_logger is not None

    def test_log_dir_created(self, session_logger, temp_log_dir):
        """Diretório de logs deve ser criado."""
        assert temp_log_dir.exists()
        assert temp_log_dir.is_dir()

    def test_no_active_session_initially(self, session_logger):
        """Não deve ter sessão ativa inicialmente."""
        assert session_logger.is_session_active() is False
        assert session_logger.get_active_session() is None


class TestSessionLifecycle:
    """Testa ciclo de vida de sessões."""

    def test_log_session_start_returns_id(self, session_logger):
        """Iniciar sessão deve retornar ID."""
        session_id = session_logger.log_session_start(
            operator_id="OP-001",
            timestamp=datetime(2026, 1, 11, 14, 30, 0)
        )

        assert session_id is not None
        assert session_id.startswith("session-")

    def test_session_is_active_after_start(self, session_logger):
        """Sessão deve estar ativa após iniciar."""
        session_logger.log_session_start("OP-001")

        assert session_logger.is_session_active() is True
        assert session_logger.get_active_session() is not None

    def test_active_session_has_operator_id(self, session_logger):
        """Sessão ativa deve ter operator ID."""
        session_logger.log_session_start(operator_id="OP-123")

        active = session_logger.get_active_session()

        assert active["operator_id"] == "OP-123"

    def test_active_session_has_timestamp(self, session_logger):
        """Sessão ativa deve ter timestamp."""
        timestamp = datetime(2026, 1, 11, 15, 45, 30)
        session_logger.log_session_start("OP-001", timestamp=timestamp)

        active = session_logger.get_active_session()

        assert active["start_time"] == timestamp.isoformat()

    def test_log_session_end_deactivates_session(self, session_logger):
        """Finalizar sessão deve desativá-la."""
        session_id = session_logger.log_session_start("OP-001")
        session_logger.log_session_end(session_id)

        assert session_logger.is_session_active() is False
        assert session_logger.get_active_session() is None

    def test_log_session_end_without_active_session_returns_false(self, session_logger):
        """Finalizar sem sessão ativa deve retornar False."""
        result = session_logger.log_session_end("nonexistent")

        assert result is False

    def test_session_end_adds_end_time(self, session_logger):
        """Finalizar sessão deve adicionar end_time."""
        session_id = session_logger.log_session_start("OP-001")

        end_timestamp = datetime(2026, 1, 11, 16, 0, 0)
        session_logger.log_session_end(session_id, timestamp=end_timestamp)

        # Verifica arquivo gravado
        log_files = list(Path(session_logger.log_dir).glob("session-*.json"))
        assert len(log_files) == 1

        with open(log_files[0], 'r') as f:
            sessions = json.load(f)
            if not isinstance(sessions, list):
                sessions = [sessions]

            assert sessions[0]["end_time"] == end_timestamp.isoformat()


class TestActionLogging:
    """Testa registro de ações durante sessão."""

    def test_log_action_to_active_session(self, session_logger):
        """Deve registrar ação na sessão ativa."""
        session_id = session_logger.log_session_start("OP-001")

        action = {
            "type": "test_action",
            "data": "test_data"
        }

        result = session_logger.log_action(session_id, action)

        assert result is True

        active = session_logger.get_active_session()
        assert len(active["actions"]) == 1
        assert active["actions"][0]["type"] == "test_action"

    def test_log_action_adds_timestamp_if_missing(self, session_logger):
        """Deve adicionar timestamp se não fornecido."""
        session_id = session_logger.log_session_start("OP-001")

        action = {"type": "test"}
        session_logger.log_action(session_id, action)

        active = session_logger.get_active_session()
        assert "timestamp" in active["actions"][0]

    def test_log_action_without_active_session_returns_false(self, session_logger):
        """Registrar ação sem sessão ativa deve retornar False."""
        result = session_logger.log_action("nonexistent", {"type": "test"})

        assert result is False

    def test_log_action_with_wrong_session_id_returns_false(self, session_logger):
        """Registrar ação com ID errado deve retornar False."""
        session_id = session_logger.log_session_start("OP-001")

        result = session_logger.log_action("wrong_id", {"type": "test"})

        assert result is False

    def test_log_multiple_actions(self, session_logger):
        """Deve registrar múltiplas ações."""
        session_id = session_logger.log_session_start("OP-001")

        for i in range(3):
            session_logger.log_action(session_id, {"type": f"action_{i}"})

        active = session_logger.get_active_session()
        assert len(active["actions"]) == 3


class TestSessionPersistence:
    """Testa persistência de sessões em arquivo."""

    def test_session_saved_to_file(self, session_logger):
        """Sessão deve ser salva ao arquivo."""
        session_id = session_logger.log_session_start("OP-001")
        session_logger.log_session_end(session_id)

        log_files = list(Path(session_logger.log_dir).glob("session-*.json"))
        assert len(log_files) == 1

        # Verifica conteúdo
        with open(log_files[0], 'r') as f:
            data = json.load(f)
            if not isinstance(data, list):
                data = [data]

            assert len(data) == 1
            assert data[0]["operator_id"] == "OP-001"

    def test_multiple_sessions_in_same_file(self, session_logger):
        """Múltiplas sessões do mesmo operador devem estar no mesmo arquivo."""
        # Cria primeira sessão
        session1 = session_logger.log_session_start("OP-001")
        session_logger.log_session_end(session1)

        # Cria segunda sessão no mesmo dia
        session2 = session_logger.log_session_start("OP-001")
        session_logger.log_session_end(session2)

        # Verifica arquivo
        log_files = list(Path(session_logger.log_dir).glob("session-OP-001-*.json"))
        assert len(log_files) == 1

        with open(log_files[0], 'r') as f:
            sessions = json.load(f)
            assert len(sessions) == 2

    def test_file_naming_includes_operator_and_date(self, session_logger):
        """Nome do arquivo deve incluir operator ID e data."""
        session_id = session_logger.log_session_start(
            operator_id="OP-123",
            timestamp=datetime(2026, 1, 11, 14, 30, 0)
        )
        session_logger.log_session_end(session_id)

        log_files = list(Path(session_logger.log_dir).glob("session-OP-123-*.json"))
        assert len(log_files) == 1
        # Nome deve ter a data
        assert "2026-01-11" in log_files[0].name


class TestSessionHistory:
    """Testa consulta de histórico de sessões."""

    def test_get_history_returns_all_sessions(self, session_logger):
        """Deve retornar todas as sessões."""
        # Cria 3 sessões
        for i in range(3):
            session_id = session_logger.log_session_start(f"OP-{i:03d}")
            session_logger.log_action(session_id, {"type": f"action_{i}"})
            session_logger.log_session_end(session_id)

        history = session_logger.get_session_history()

        assert len(history) == 3

    def test_history_sorted_by_date_descending(self, session_logger):
        """Histórico deve estar ordenado por data (mais recente primeiro)."""
        # Cria sessões em tempos diferentes
        session1 = session_logger.log_session_start(
            "OP-001",
            timestamp=datetime(2026, 1, 11, 10, 0, 0)
        )
        session_logger.log_session_end(session1)

        session2 = session_logger.log_session_start(
            "OP-001",
            timestamp=datetime(2026, 1, 11, 12, 0, 0)
        )
        session_logger.log_session_end(session2)

        history = session_logger.get_session_history()

        # Mais recente primeiro
        assert history[0]["start_time"] > history[1]["start_time"]

    def test_filter_history_by_operator(self, session_logger):
        """Deve filtrar histórico por operador."""
        # Cria sessões de 2 operadores
        session1 = session_logger.log_session_start("OP-001")
        session_logger.log_session_end(session1)

        session2 = session_logger.log_session_start("OP-002")
        session_logger.log_session_end(session2)

        # Filtra por OP-001
        history = session_logger.get_session_history(operator_id="OP-001")

        assert len(history) == 1
        assert history[0]["operator_id"] == "OP-001"

    def test_filter_history_by_date_range(self, session_logger):
        """Deve filtrar histórico por intervalo de datas."""
        # Cria sessões em datas diferentes
        session1 = session_logger.log_session_start(
            "OP-001",
            timestamp=datetime(2026, 1, 10, 12, 0, 0)
        )
        session_logger.log_session_end(session1)

        session2 = session_logger.log_session_start(
            "OP-001",
            timestamp=datetime(2026, 1, 12, 12, 0, 0)
        )
        session_logger.log_session_end(session2)

        # Filtra por data
        history = session_logger.get_session_history(
            start_date=datetime(2026, 1, 11, 0, 0, 0),
            end_date=datetime(2026, 1, 13, 23, 59, 59)
        )

        # Apenas session2 deve estar no intervalo
        assert len(history) == 1
        assert "2026-01-12" in history[0]["start_time"]


class TestSessionStatistics:
    """Testa estatísticas de sessões."""

    def test_get_statistics_returns_total_count(self, session_logger):
        """Estatísticas devem incluir total de sessões."""
        # Cria 3 sessões
        for i in range(3):
            session_id = session_logger.log_session_start(f"OP-{i:03d}")
            session_logger.log_session_end(session_id)

        stats = session_logger.get_session_statistics()

        assert stats["total_sessions"] == 3

    def test_get_statistics_returns_total_actions(self, session_logger):
        """Estatísticas devem incluir total de ações."""
        session_id = session_logger.log_session_start("OP-001")

        # Adiciona 5 ações
        for i in range(5):
            session_logger.log_action(session_id, {"type": f"action_{i}"})

        session_logger.log_session_end(session_id)

        stats = session_logger.get_session_statistics()

        assert stats["total_actions"] == 5

    def test_get_statistics_calculates_average_duration(self, session_logger):
        """Estatísticas devem calcular duração média das sessões."""
        # Cria 2 sessões com durações conhecidas
        session1 = session_logger.log_session_start(
            "OP-001",
            timestamp=datetime(2026, 1, 11, 10, 0, 0)
        )
        session_logger.log_session_end(
            session1,
            timestamp=datetime(2026, 1, 11, 10, 30, 0)  # 30 min
        )

        session2 = session_logger.log_session_start(
            "OP-001",
            timestamp=datetime(2026, 1, 11, 11, 0, 0)
        )
        session_logger.log_session_end(
            session2,
            timestamp=datetime(2026, 1, 11, 11, 10, 0)  # 10 min
        )

        stats = session_logger.get_session_statistics()

        # Média: (30 + 10) / 2 = 20 minutos
        assert stats["average_session_duration_minutes"] == 20.0

    def test_get_statistics_identifies_common_actions(self, session_logger):
        """Estatísticas devem identificar ações mais comuns."""
        session_id = session_logger.log_session_start("OP-001")

        # Adiciona ações com frequências diferentes
        for _ in range(5):
            session_logger.log_action(session_id, {"type": "inspection_started"})
        for _ in range(3):
            session_logger.log_action(session_id, {"type": "stencil_selected"})
        for _ in range(1):
            session_logger.log_action(session_id, {"type": "other"})

        session_logger.log_session_end(session_id)

        stats = session_logger.get_session_statistics()

        common_actions = stats["most_common_actions"]
        assert len(common_actions) == 3
        assert common_actions[0]["type"] == "inspection_started"
        assert common_actions[0]["count"] == 5

    def test_get_statistics_filtered_by_operator(self, session_logger):
        """Estatísticas podem ser filtradas por operador."""
        # Sessões de 2 operadores
        for _ in range(3):
            session_id = session_logger.log_session_start("OP-001")
            session_logger.log_session_end(session_id)

        for _ in range(2):
            session_id = session_logger.log_session_start("OP-002")
            session_logger.log_session_end(session_id)

        stats = session_logger.get_session_statistics(operator_id="OP-001")

        assert stats["total_sessions"] == 3
