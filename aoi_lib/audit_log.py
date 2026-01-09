"""
Log de Auditoria - Sistema de Rastreabilidade

Registra inspeções descartadas e ações críticas para rastreabilidade.
Não visível para operadores, apenas para engenharia/admin.
"""

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class AuditEntry:
    """
    Entrada de log de auditoria

    Atributos:
        audit_id: ID único da entrada de auditoria
        session_id: ID da sessão de inspeção
        timestamp: Data/hora do evento
        event_type: Tipo de evento (DISCARDED, REJECTED, APPROVED, etc.)
        operator: Usuário que realizou a ação
        stencil_code: Código do stencil
        session_type: Tipo de sessão (Limpeza XPTO, etc.)
        reason: Motivo da ação (opcional)
        defects: Lista de defeitos identificados
        action: Ação tomada pelo usuário
        metadata: Dados adicionais (opcional)
    """
    audit_id: str
    session_id: str
    timestamp: str
    event_type: str
    operator: str
    stencil_code: str
    session_type: str
    reason: Optional[str] = None
    defects: Optional[List[Dict]] = None
    action: Optional[str] = None
    metadata: Optional[Dict] = None

    def to_dict(self) -> Dict:
        """Converte para dicionário"""
        return asdict(self)


class AuditLog:
    """
    Sistema de log de auditoria

    Registra eventos críticos do sistema, especialmente inspeções
    descartadas que não entram no histórico do usuário.
    """

    # Tipos de eventos
    EVENT_DISCARDED = "DISCARDED"
    EVENT_REJECTED = "REJECTED"
    EVENT_APPROVED_AUTO = "APPROVED_AUTO"
    EVENT_APPROVED_USER = "APPROVED_USER"
    EVENT_CANCELLED = "CANCELLED"
    EVENT_ERROR = "ERROR"

    def __init__(self, log_dir: Optional[Path] = None):
        """
        Inicializa sistema de auditoria

        Args:
            log_dir: Diretório para armazenar logs (default: data/audit/)
        """
        if log_dir is None:
            # Default: data/audit/
            log_dir = Path(__file__).parent.parent / "data" / "audit"

        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Arquivo de log atual
        self.current_log_file = self.log_dir / f"audit_{datetime.now().strftime('%Y%m%d')}.jsonl"

        logger.info(f"AuditLog inicializado: {self.log_dir}")

    def log_discarded_inspection(
        self,
        session_id: str,
        operator: str,
        stencil_code: str,
        session_type: str,
        defects: List[Dict],
        reason: Optional[str] = None
    ) -> AuditEntry:
        """
        Registra inspeção descartada (NÃO salva no histórico)

        Args:
            session_id: ID da sessão
            operator: Nome do operador
            stencil_code: Código do stencil
            session_type: Tipo de sessão (ex: "Limpeza XPTO")
            defects: Lista de defeitos confirmados
            reason: Motivo do descarte (opcional)

        Returns:
            AuditEntry criada
        """
        audit_id = f"AUDIT-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        # Conta defeitos por tipo
        defect_summary = self._summarize_defects(defects)

        entry = AuditEntry(
            audit_id=audit_id,
            session_id=session_id,
            timestamp=datetime.now().isoformat(),
            event_type=self.EVENT_DISCARDED,
            operator=operator,
            stencil_code=stencil_code,
            session_type=session_type,
            reason=reason or f"{len(defects)} defeitos confirmados",
            defects=defects,
            action="Operador descartou e vai realizar correção",
            metadata={
                "defect_summary": defect_summary,
                "will_reinspect": True
            }
        )

        self._write_entry(entry)

        logger.info(f"Inspeção descartada registrada: {audit_id} - {operator} - {stencil_code}")

        return entry

    def log_rejected_inspection(
        self,
        session_id: str,
        operator: str,
        stencil_code: str,
        session_type: str,
        defects: List[Dict]
    ) -> AuditEntry:
        """
        Registra inspeção reprovada (salva no histórico como REPROV)

        Args:
            session_id: ID da sessão
            operator: Nome do operador
            stencil_code: Código do stencil
            session_type: Tipo de sessão
            defects: Lista de defeitos confirmados

        Returns:
            AuditEntry criada
        """
        audit_id = f"AUDIT-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        entry = AuditEntry(
            audit_id=audit_id,
            session_id=session_id,
            timestamp=datetime.now().isoformat(),
            event_type=self.EVENT_REJECTED,
            operator=operator,
            stencil_code=stencil_code,
            session_type=session_type,
            reason=f"{len(defects)} defeitos confirmados",
            defects=defects,
            action="Salvo no histórico como REPROV",
            metadata={
                "defect_summary": self._summarize_defects(defects),
                "saved_to_history": True
            }
        )

        self._write_entry(entry)

        logger.info(f"Inspeção reprovada registrada: {audit_id} - {operator} - {stencil_code}")

        return entry

    def log_user_approved(
        self,
        session_id: str,
        operator: str,
        stencil_code: str,
        session_type: str,
        defects_judged: Dict
    ) -> AuditEntry:
        """
        Registra aprovação com julgamento (defeitos julgados como falhas falsas)

        Args:
            session_id: ID da sessão
            operator: Nome do operador
            stencil_code: Código do stencil
            session_type: Tipo de sessão
            defects_judged: Dict com contagem de defeitos julgados
                           Ex: {"false_alarms": 12, "confirmed_real": 0}

        Returns:
            AuditEntry criada
        """
        audit_id = f"AUDIT-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        entry = AuditEntry(
            audit_id=audit_id,
            session_id=session_id,
            timestamp=datetime.now().isoformat(),
            event_type=self.EVENT_APPROVED_USER,
            operator=operator,
            stencil_code=stencil_code,
            session_type=session_type,
            reason=f"{defects_judged.get('false_alarms', 0)} defeitos julgados como falhas falsas",
            defects=None,
            action="Salvo no histórico como APROVADO COM JULGAMENTO",
            metadata={
                **defects_judged,
                "saved_to_history": True
            }
        )

        self._write_entry(entry)

        logger.info(f"Aprovação com julgamento registrada: {audit_id} - {operator} - {stencil_code}")

        return entry

    def log_auto_approved(
        self,
        session_id: str,
        operator: str,
        stencil_code: str,
        session_type: str
    ) -> AuditEntry:
        """
        Registra aprovação automática (sem defeitos detectados)

        Args:
            session_id: ID da sessão
            operator: Nome do operador
            stencil_code: Código do stencil
            session_type: Tipo de sessão

        Returns:
            AuditEntry criada
        """
        audit_id = f"AUDIT-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        entry = AuditEntry(
            audit_id=audit_id,
            session_id=session_id,
            timestamp=datetime.now().isoformat(),
            event_type=self.EVENT_APPROVED_AUTO,
            operator=operator,
            stencil_code=stencil_code,
            session_type=session_type,
            reason="Nenhum defeito detectado",
            defects=None,
            action="Salvo no histórico como APROVADO AUTOMÁTICO",
            metadata={
                "defects_found": 0,
                "saved_to_history": True
            }
        )

        self._write_entry(entry)

        logger.info(f"Aprovação automática registrada: {audit_id} - {operator} - {stencil_code}")

        return entry

    def log_cancelled_inspection(
        self,
        session_id: str,
        operator: str,
        stencil_code: str,
        reason: str
    ) -> AuditEntry:
        """
        Registra inspeção cancelada pelo usuário

        Args:
            session_id: ID da sessão
            operator: Nome do operador
            stencil_code: Código do stencil
            reason: Motivo do cancelamento

        Returns:
            AuditEntry criada
        """
        audit_id = f"AUDIT-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        entry = AuditEntry(
            audit_id=audit_id,
            session_id=session_id,
            timestamp=datetime.now().isoformat(),
            event_type=self.EVENT_CANCELLED,
            operator=operator,
            stencil_code=stencil_code,
            session_type="Unknown",
            reason=reason,
            defects=None,
            action="Inspeção cancelada, dados descartados",
            metadata={
                "data_discarded": True
            }
        )

        self._write_entry(entry)

        logger.info(f"Inspeção cancelada registrada: {audit_id} - {operator} - {stencil_code}")

        return entry

    def _write_entry(self, entry: AuditEntry):
        """
        Escreve entrada de log no arquivo JSONL

        Args:
            entry: Entrada de auditoria
        """
        try:
            # Converte para JSON e escreve no arquivo (JSONL = um JSON por linha)
            json_line = json.dumps(entry.to_dict(), ensure_ascii=False)

            with open(self.current_log_file, 'a', encoding='utf-8') as f:
                f.write(json_line + '\n')

        except Exception as e:
            logger.error(f"Erro ao escrever no log de auditoria: {e}")

    def _summarize_defects(self, defects: List[Dict]) -> Dict:
        """
        Gera resumo estatístico dos defeitos

        Args:
            defects: Lista de defeitos

        Returns:
            Dicionário com contagem por tipo
        """
        if not defects:
            return {"total": 0}

        summary = {
            "total": len(defects),
            "by_type": {},
            "by_severity": {"high": 0, "medium": 0, "low": 0}
        }

        for defect in defects:
            # Conta por tipo
            defect_type = defect.get("type", "Unknown")
            summary["by_type"][defect_type] = summary["by_type"].get(defect_type, 0) + 1

            # Conta por severidade
            severity = defect.get("severity", "unknown")
            if severity in summary["by_severity"]:
                summary["by_severity"][severity] += 1

        return summary

    def get_discarded_count(self, stencil_code: Optional[str] = None) -> int:
        """
        Retorna quantidade de inspeções descartadas

        Args:
            stencil_code: Filtrar por stencil específico (opcional)

        Returns:
            Número de inspeções descartadas
        """
        count = 0

        try:
            # Lê arquivo atual
            if self.current_log_file.exists():
                with open(self.current_log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())

                            # Filtra por tipo e opcionalmente por stencil
                            if entry.get("event_type") == self.EVENT_DISCARDED:
                                if stencil_code is None or entry.get("stencil_code") == stencil_code:
                                    count += 1

                        except json.JSONDecodeError:
                            continue

        except Exception as e:
            logger.error(f"Erro ao ler log de auditoria: {e}")

        return count

    def get_recent_entries(
        self,
        limit: int = 100,
        event_type: Optional[str] = None,
        stencil_code: Optional[str] = None
    ) -> List[AuditEntry]:
        """
        Retorna entradas recentes do log

        Args:
            limit: Número máximo de entradas
            event_type: Filtrar por tipo de evento (opcional)
            stencil_code: Filtrar por stencil (opcional)

        Returns:
            Lista de AuditEntry (mais recentes primeiro)
        """
        entries = []

        try:
            # Lê arquivo atual
            if self.current_log_file.exists():
                with open(self.current_log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            entry_dict = json.loads(line.strip())

                            # Aplica filtros
                            if event_type and entry_dict.get("event_type") != event_type:
                                continue

                            if stencil_code and entry_dict.get("stencil_code") != stencil_code:
                                continue

                            # Cria AuditEntry
                            entry = AuditEntry(**entry_dict)
                            entries.append(entry)

                        except json.JSONDecodeError:
                            continue

        except Exception as e:
            logger.error(f"Erro ao ler log de auditoria: {e}")

        # Ordena por timestamp (mais recente primeiro) e limita
        entries.sort(key=lambda e: e.timestamp, reverse=True)

        return entries[:limit]


# Instância global do audit log
_audit_log_instance: Optional[AuditLog] = None


def get_audit_log() -> AuditLog:
    """
    Retorna instância singleton do AuditLog

    Returns:
        Instância de AuditLog
    """
    global _audit_log_instance

    if _audit_log_instance is None:
        _audit_log_instance = AuditLog()

    return _audit_log_instance
