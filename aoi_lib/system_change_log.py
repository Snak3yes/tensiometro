"""
Log local de alteracoes de configuracao e cadastros do sistema.

Registra em JSONL as mudancas persistidas com contexto do usuario atual
(DRT, modo de autenticacao e detalhes da alteracao).
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from aoi_lib.auth.auth_service import get_current_auth_context
from aoi_lib.runtime_paths import get_runtime_path

logger = logging.getLogger(__name__)


@dataclass
class SystemChangeEntry:
    """Entrada serializavel do log local de alteracoes."""

    change_id: str
    timestamp: str
    category: str
    action: str
    target_type: str
    target_id: str
    description: str
    actor: dict[str, Any]
    changes: Optional[dict[str, Any]] = None
    metadata: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SystemChangeLog:
    """Persistencia simples de alteracoes locais em arquivos JSONL diarios."""

    def __init__(self, log_dir: Optional[Path] = None):
        self.log_dir = Path(log_dir) if log_dir else get_runtime_path("data", "audit")
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def log_config_change(
        self,
        config_path: str,
        old_value: Any,
        new_value: Any,
        *,
        description: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Optional[SystemChangeEntry]:
        """Registra uma alteracao persistida de configuracao."""
        if old_value == new_value:
            return None

        return self.log_event(
            category="config",
            action="updated",
            target_type="config",
            target_id=config_path,
            description=description or f"Configuracao alterada: {config_path}",
            changes={"old": old_value, "new": new_value},
            metadata=metadata,
        )

    def log_event(
        self,
        *,
        category: str,
        action: str,
        target_type: str,
        target_id: str,
        description: str,
        changes: Optional[dict[str, Any]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> SystemChangeEntry:
        """Registra um evento generico de alteracao local."""
        timestamp = datetime.now().isoformat()
        entry = SystemChangeEntry(
            change_id=f"CHANGE-{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}",
            timestamp=timestamp,
            category=category,
            action=action,
            target_type=target_type,
            target_id=target_id,
            description=description,
            actor=self._normalize_value(get_current_auth_context()),
            changes=self._normalize_value(changes),
            metadata=self._normalize_value(metadata),
        )
        self._write_entry(entry)
        return entry

    def _write_entry(self, entry: SystemChangeEntry):
        try:
            with open(self._get_current_log_file(), "a", encoding="utf-8") as stream:
                stream.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")
        except Exception as exc:
            logger.error("Erro ao escrever log local de alteracoes: %s", exc)

    def _get_current_log_file(self) -> Path:
        return self.log_dir / f"system_changes_{datetime.now().strftime('%Y%m%d')}.jsonl"

    def _normalize_value(self, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, Path):
            return str(value)
        if is_dataclass(value):
            return self._normalize_value(asdict(value))
        if isinstance(value, dict):
            return {str(key): self._normalize_value(item) for key, item in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [self._normalize_value(item) for item in value]
        return str(value)


_system_change_log_instance: Optional[SystemChangeLog] = None


def get_system_change_log() -> SystemChangeLog:
    """Retorna a instancia singleton do logger local de alteracoes."""
    global _system_change_log_instance
    if _system_change_log_instance is None:
        _system_change_log_instance = SystemChangeLog()
    return _system_change_log_instance
