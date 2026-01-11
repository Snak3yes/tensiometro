"""
managers/session_logger.py
--------------------------
Registra sessões de operadores e ações executadas.
"""
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from PyQt6.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)


class SessionLogger(QObject):
    """
    Registra sessões de usuários e ações executadas.

    Responsabilidades:
        - Registrar início/fim de sessões
        - Registrar ações durante sessões
        - Manazer histórico de sessões em arquivo JSON
        - Fornecer dados para auditoria

    Formato do Log:
        {
            "session_id": "session-20260111-143052",
            "operator_id": "OP-001",
            "start_time": "2026-01-11T14:30:52",
            "end_time": "2026-01-11T15:45:30",
            "actions": [
                {
                    "type": "inspection_started",
                    "timestamp": "2026-01-11T14:35:10",
                    "details": {...}
                }
            ]
        }
    """

    # Signals
    session_logged = pyqtSignal(str)  # session_id
    action_logged = pyqtSignal(str, str)  # session_id, action_type

    def __init__(self, log_dir: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.log_dir = Path(log_dir) if log_dir else Path("data/sessions")
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Sessão ativa
        self._active_session: Optional[Dict] = None

        logger.info(f"SessionLogger inicializado. Diretório: {self.log_dir}")

    def log_session_start(
        self,
        operator_id: str,
        timestamp: Optional[datetime] = None
    ) -> str:
        """
        Registra o início de uma sessão.

        Args:
            operator_id: ID do operador
            timestamp: Timestamp da sessão (usa datetime.now() se None)

        Returns:
            ID da sessão criada
        """
        if timestamp is None:
            timestamp = datetime.now()

        session_id = f"session-{timestamp.strftime('%Y%m%d-%H%M%S')}"

        session = {
            "session_id": session_id,
            "operator_id": operator_id,
            "start_time": timestamp.isoformat(),
            "end_time": None,
            "actions": []
        }

        self._active_session = session

        logger.info(f"Sessão iniciada: {session_id} (operador: {operator_id})")
        self.session_logged.emit(session_id)

        return session_id

    def log_session_end(
        self,
        session_id: str,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Registra o fim de uma sessão e salva em arquivo.

        Args:
            session_id: ID da sessão
            timestamp: Timestamp do fim (usa datetime.now() se None)

        Returns:
            True se salvo com sucesso
        """
        if self._active_session is None:
            logger.error("Nenhuma sessão ativa para finalizar")
            return False

        if timestamp is None:
            timestamp = datetime.now()

        self._active_session["end_time"] = timestamp.isoformat()

        # Salva sessão em arquivo
        success = self._save_session(self._active_session)

        if success:
            logger.info(f"Sessão finalizada: {session_id}")

        # Limpa sessão ativa
        self._active_session = None

        return success

    def log_action(self, session_id: str, action: Dict[str, Any]) -> bool:
        """
        Registra uma ação durante a sessão ativa.

        Args:
            session_id: ID da sessão
            action: Dicionário com dados da ação
                - type: Tipo da ação (e.g., "inspection_started")
                - timestamp: ISO timestamp
                - details: Dicionário com detalhes específicos

        Returns:
            True se registrado com sucesso
        """
        if self._active_session is None:
            logger.error("Nenhuma sessão ativa para registrar ação")
            return False

        if self._active_session["session_id"] != session_id:
            logger.error(
                f"Session ID mismatch: esperado={self._active_session['session_id']}, "
                f"recebido={session_id}"
            )
            return False

        # Adiciona timestamp se não fornecido
        if "timestamp" not in action:
            action["timestamp"] = datetime.now().isoformat()

        self._active_session["actions"].append(action)

        logger.debug(
            f"Ação registrada: session={session_id}, type={action.get('type')}"
        )
        self.action_logged.emit(session_id, action.get("type", "unknown"))

        return True

    def get_active_session(self) -> Optional[Dict]:
        """
        Retorna a sessão ativa atual.

        Returns:
            Dicionário da sessão ou None se nenhuma sessão ativa
        """
        return self._active_session

    def is_session_active(self) -> bool:
        """
        Verifica se há uma sessão ativa.

        Returns:
            True se há sessão ativa
        """
        return self._active_session is not None

    def _save_session(self, session: Dict) -> bool:
        """
        Salva sessão em arquivo JSON.

        Args:
            session: Dicionário da sessão

        Returns:
            True se salvo com sucesso
        """
        try:
            # Nome do arquivo: session-<operator_id>-<date>.json
            operator_id = session["operator_id"]
            date_str = session["start_time"][:10]  # YYYY-MM-DD
            filename = f"session-{operator_id}-{date_str}.json"
            filepath = self.log_dir / filename

            # Se arquivo já existe, lê e adiciona nova sessão
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if not isinstance(data, list):
                        data = [data]
                    data.append(session)
            else:
                data = [session]

            # Salva arquivo
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"Sessão salva: {filepath}")
            return True

        except Exception as e:
            logger.error(f"Erro ao salvar sessão: {e}")
            return False

    def get_session_history(
        self,
        operator_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Retorna histórico de sessões com filtros opcionais.

        Args:
            operator_id: Filtra por operador específico
            start_date: Data inicial do filtro
            end_date: Data final do filtro

        Returns:
            Lista de sessões que correspondem aos filtros
        """
        sessions = []

        # Lista todos os arquivos de sessão
        for filepath in self.log_dir.glob("session-*.json"):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if not isinstance(data, list):
                        data = [data]

                    for session in data:
                        # Aplica filtros
                        if operator_id and session.get("operator_id") != operator_id:
                            continue

                        session_start = datetime.fromisoformat(session["start_time"])
                        if start_date and session_start < start_date:
                            continue
                        if end_date and session_start > end_date:
                            continue

                        sessions.append(session)

            except Exception as e:
                logger.error(f"Erro ao ler arquivo {filepath}: {e}")

        # Ordena por data (mais recente primeiro)
        sessions.sort(key=lambda s: s["start_time"], reverse=True)

        return sessions

    def get_session_statistics(
        self,
        operator_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retorna estatísticas de sessões.

        Args:
            operator_id: Filtra por operador específico

        Returns:
            Dicionário com estatísticas:
                - total_sessions: Número total de sessões
                - total_actions: Número total de ações
                - average_session_duration: Duração média em minutos
                - most_common_actions: Lista de ações mais comuns
        """
        sessions = self.get_session_history(operator_id=operator_id)

        total_sessions = len(sessions)
        total_actions = sum(len(s.get("actions", [])) for s in sessions)

        # Calcula duração média
        durations = []
        for session in sessions:
            if session.get("end_time"):
                start = datetime.fromisoformat(session["start_time"])
                end = datetime.fromisoformat(session["end_time"])
                duration_min = (end - start).total_seconds() / 60
                durations.append(duration_min)

        average_duration = sum(durations) / len(durations) if durations else 0

        # Conta tipos de ações
        action_counts = {}
        for session in sessions:
            for action in session.get("actions", []):
                action_type = action.get("type", "unknown")
                action_counts[action_type] = action_counts.get(action_type, 0) + 1

        # Top 5 ações mais comuns
        most_common = sorted(
            action_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        return {
            "total_sessions": total_sessions,
            "total_actions": total_actions,
            "average_session_duration_minutes": round(average_duration, 2),
            "most_common_actions": [
                {"type": action, "count": count}
                for action, count in most_common
            ]
        }
