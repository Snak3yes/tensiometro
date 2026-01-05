"""
stencil_database.py
-------------------
Persistência SQLite para rastreabilidade de stencils.

Este módulo substitui a persistência JSON por SQLite para:
- Melhor performance com grande volume de dados
- Consultas mais complexas (filtros, agregações)
- Integridade referencial
- Backup mais simples (arquivo único)

Estrutura do banco:
    stencils        - Dados dos stencils cadastrados
    tension_records - Histórico de medições de tensão
    inspection_records - Histórico de inspeções visuais

Migração:
    O módulo detecta automaticamente se há dados JSON existentes
    e oferece migração para o banco SQLite.
"""

import sqlite3
import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager

from .stencil_tracker import (
    Stencil, TensionRecord, InspectionRecord, TrendAnalysis
)

log = logging.getLogger(__name__)


# ============================================================================
#  SCHEMA DO BANCO DE DADOS
# ============================================================================

SCHEMA_VERSION = 1

CREATE_TABLES = """
-- Tabela de stencils
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

-- Índices para stencils
CREATE INDEX IF NOT EXISTS idx_stencils_code ON stencils(code);
CREATE INDEX IF NOT EXISTS idx_stencils_status ON stencils(status);
CREATE INDEX IF NOT EXISTS idx_stencils_last_inspection ON stencils(last_inspection);

-- Tabela de medições de tensão
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

-- Índices para tension_records
CREATE INDEX IF NOT EXISTS idx_tension_stencil ON tension_records(stencil_id);
CREATE INDEX IF NOT EXISTS idx_tension_timestamp ON tension_records(timestamp);
CREATE INDEX IF NOT EXISTS idx_tension_result ON tension_records(result);

-- Tabela de inspeções visuais
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

-- Índices para inspection_records
CREATE INDEX IF NOT EXISTS idx_inspection_stencil ON inspection_records(stencil_id);
CREATE INDEX IF NOT EXISTS idx_inspection_timestamp ON inspection_records(timestamp);
CREATE INDEX IF NOT EXISTS idx_inspection_result ON inspection_records(result);

-- Tabela de metadados do banco
CREATE TABLE IF NOT EXISTS db_metadata (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""


# ============================================================================
#  CLASSE DO BANCO DE DADOS
# ============================================================================

class StencilDatabase:
    """
    Gerenciador de banco de dados SQLite para stencils.
    
    Substitui a persistência JSON do StencilTracker por SQLite,
    mantendo compatibilidade com os modelos de dados existentes.
    """
    
    MOVING_AVERAGE_WINDOW = 5
    DEGRADATION_THRESHOLD = 0.10
    
    def __init__(self, db_path: str = None):
        """
        Inicializa o banco de dados.
        
        Args:
            db_path: Caminho do arquivo .db. 
                     Default: ./data/stencils.db
        """
        if db_path is None:
            base = Path(__file__).parent.parent
            self.db_path = base / "data" / "stencils.db"
        else:
            self.db_path = Path(db_path)
        
        # Garante diretório
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Inicializa banco
        self._init_database()
        
        log.info(f"StencilDatabase inicializado em: {self.db_path}")
    
    @contextmanager
    def _get_connection(self):
        """Context manager para conexão com o banco."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _init_database(self):
        """Cria tabelas se não existirem."""
        with self._get_connection() as conn:
            conn.executescript(CREATE_TABLES)
            
            # Verifica versão do schema
            cursor = conn.execute(
                "SELECT value FROM db_metadata WHERE key = 'schema_version'"
            )
            row = cursor.fetchone()
            
            if row is None:
                conn.execute(
                    "INSERT INTO db_metadata (key, value) VALUES (?, ?)",
                    ("schema_version", str(SCHEMA_VERSION))
                )
                conn.execute(
                    "INSERT INTO db_metadata (key, value) VALUES (?, ?)",
                    ("created_at", datetime.now().isoformat())
                )
            
            log.debug("Banco de dados inicializado")
    
    # -------------------------------------------------------------------------
    #  CRUD DE STENCILS
    # -------------------------------------------------------------------------
    
    def stencil_exists(self, code: str) -> bool:
        """Verifica se um stencil existe."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT 1 FROM stencils WHERE code = ?", (code,)
            )
            return cursor.fetchone() is not None
    
    def get_stencil(self, code: str) -> Optional[Stencil]:
        """Obtém um stencil pelo código."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM stencils WHERE code = ?", (code,)
            )
            row = cursor.fetchone()
            
            if row is None:
                return None
            
            return Stencil(
                code=row["code"],
                description=row["description"] or "",
                recipe_name=row["recipe_name"],
                created_at=row["created_at"],
                last_inspection=row["last_inspection"],
                inspection_count=row["inspection_count"],
                status=row["status"],
                notes=row["notes"] or "",
            )
    
    def create_stencil(self, code: str, 
                       description: str = "",
                       recipe_name: str = None) -> Stencil:
        """Cria um novo stencil."""
        if self.stencil_exists(code):
            raise ValueError(f"Stencil '{code}' já existe")
        
        now = datetime.now().isoformat()
        
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO stencils 
                (code, description, recipe_name, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (code, description, recipe_name, now, now))
        
        log.info(f"Stencil criado: {code}")
        return self.get_stencil(code)
    
    def update_stencil(self, stencil: Stencil) -> None:
        """Atualiza dados de um stencil existente."""
        if not self.stencil_exists(stencil.code):
            raise ValueError(f"Stencil '{stencil.code}' não existe")
        
        now = datetime.now().isoformat()
        
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE stencils SET
                    description = ?,
                    recipe_name = ?,
                    last_inspection = ?,
                    inspection_count = ?,
                    status = ?,
                    notes = ?,
                    updated_at = ?
                WHERE code = ?
            """, (
                stencil.description,
                stencil.recipe_name,
                stencil.last_inspection,
                stencil.inspection_count,
                stencil.status,
                stencil.notes,
                now,
                stencil.code,
            ))
        
        log.info(f"Stencil atualizado: {stencil.code}")
    
    def list_stencils(self, status: str = None) -> List[Stencil]:
        """Lista todos os stencils cadastrados."""
        with self._get_connection() as conn:
            if status:
                cursor = conn.execute(
                    """SELECT * FROM stencils WHERE status = ? 
                       ORDER BY last_inspection DESC NULLS LAST, created_at DESC""",
                    (status,)
                )
            else:
                cursor = conn.execute(
                    """SELECT * FROM stencils 
                       ORDER BY last_inspection DESC NULLS LAST, created_at DESC"""
                )
            
            stencils = []
            for row in cursor.fetchall():
                stencils.append(Stencil(
                    code=row["code"],
                    description=row["description"] or "",
                    recipe_name=row["recipe_name"],
                    created_at=row["created_at"],
                    last_inspection=row["last_inspection"],
                    inspection_count=row["inspection_count"],
                    status=row["status"],
                    notes=row["notes"] or "",
                ))
            
            return stencils
    
    def delete_stencil(self, code: str) -> bool:
        """Remove um stencil e todo seu histórico."""
        if not self.stencil_exists(code):
            return False
        
        with self._get_connection() as conn:
            conn.execute("DELETE FROM stencils WHERE code = ?", (code,))
        
        log.info(f"Stencil removido: {code}")
        return True
    
    def _get_stencil_id(self, conn, code: str) -> Optional[int]:
        """Obtém ID interno do stencil."""
        cursor = conn.execute(
            "SELECT id FROM stencils WHERE code = ?", (code,)
        )
        row = cursor.fetchone()
        return row["id"] if row else None
    
    # -------------------------------------------------------------------------
    #  HISTÓRICO DE MEDIÇÕES DE TENSÃO
    # -------------------------------------------------------------------------
    
    def add_tension_record(self, code: str, record: TensionRecord) -> None:
        """Adiciona registro de medição de tensão."""
        with self._get_connection() as conn:
            stencil_id = self._get_stencil_id(conn, code)
            if not stencil_id:
                raise ValueError(f"Stencil '{code}' não encontrado")
            
            # Insere registro
            conn.execute("""
                INSERT INTO tension_records 
                (stencil_id, timestamp, average_tension, min_tension, max_tension,
                 result, ok_count, warning_count, nok_count, operator, recipe_name,
                 measurements_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                stencil_id,
                record.timestamp,
                record.average_tension,
                record.min_tension,
                record.max_tension,
                record.result,
                record.ok_count,
                record.warning_count,
                record.nok_count,
                record.operator,
                record.recipe_name,
                json.dumps(record.measurements),
            ))
            
            # Atualiza stencil
            conn.execute("""
                UPDATE stencils SET 
                    last_inspection = ?,
                    inspection_count = inspection_count + 1,
                    status = CASE WHEN ? = 'NOK' THEN 'warning' ELSE status END,
                    updated_at = ?
                WHERE id = ?
            """, (record.timestamp, record.result, datetime.now().isoformat(), stencil_id))
        
        log.info(f"Registro de tensão adicionado para {code}: {record.result}")
    
    def get_tension_history(self, code: str, limit: int = 50) -> List[TensionRecord]:
        """Obtém histórico de medições de tensão."""
        with self._get_connection() as conn:
            stencil_id = self._get_stencil_id(conn, code)
            if not stencil_id:
                return []
            
            cursor = conn.execute("""
                SELECT * FROM tension_records 
                WHERE stencil_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (stencil_id, limit))
            
            records = []
            for row in cursor.fetchall():
                measurements = json.loads(row["measurements_json"]) if row["measurements_json"] else []
                records.append(TensionRecord(
                    timestamp=row["timestamp"],
                    measurements=measurements,
                    average_tension=row["average_tension"],
                    min_tension=row["min_tension"],
                    max_tension=row["max_tension"],
                    result=row["result"],
                    ok_count=row["ok_count"],
                    warning_count=row["warning_count"],
                    nok_count=row["nok_count"],
                    operator=row["operator"],
                    recipe_name=row["recipe_name"],
                ))
            
            return records
    
    # -------------------------------------------------------------------------
    #  HISTÓRICO DE INSPEÇÕES VISUAIS
    # -------------------------------------------------------------------------
    
    def add_inspection_record(self, code: str, record: InspectionRecord) -> None:
        """Adiciona registro de inspeção visual."""
        with self._get_connection() as conn:
            stencil_id = self._get_stencil_id(conn, code)
            if not stencil_id:
                raise ValueError(f"Stencil '{code}' não encontrado")
            
            # Insere registro
            conn.execute("""
                INSERT INTO inspection_records 
                (stencil_id, timestamp, total_apertures, ok_count, partial_count,
                 blocked_count, result, pass_rate, gerber_file, operator, recipe_name,
                 report_path, defects_json, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                stencil_id,
                record.timestamp,
                record.total_apertures,
                record.ok_count,
                record.partial_count,
                record.blocked_count,
                record.result,
                record.pass_rate,
                record.gerber_file,
                record.operator,
                record.recipe_name,
                record.report_path,
                json.dumps(record.defects),
                record.notes,
            ))
            
            # Atualiza stencil
            conn.execute("""
                UPDATE stencils SET 
                    last_inspection = ?,
                    inspection_count = inspection_count + 1,
                    status = CASE WHEN ? = 'FAIL' THEN 'warning' ELSE status END,
                    updated_at = ?
                WHERE id = ?
            """, (record.timestamp, record.result, datetime.now().isoformat(), stencil_id))
        
        log.info(f"Registro de inspeção adicionado para {code}: {record.result}")
    
    def get_inspection_history(self, code: str, limit: int = 50) -> List[InspectionRecord]:
        """Obtém histórico de inspeções visuais."""
        with self._get_connection() as conn:
            stencil_id = self._get_stencil_id(conn, code)
            if not stencil_id:
                return []
            
            cursor = conn.execute("""
                SELECT * FROM inspection_records 
                WHERE stencil_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (stencil_id, limit))
            
            records = []
            for row in cursor.fetchall():
                defects = json.loads(row["defects_json"]) if row["defects_json"] else []
                records.append(InspectionRecord(
                    timestamp=row["timestamp"],
                    total_apertures=row["total_apertures"],
                    ok_count=row["ok_count"],
                    partial_count=row["partial_count"],
                    blocked_count=row["blocked_count"],
                    result=row["result"],
                    pass_rate=row["pass_rate"],
                    gerber_file=row["gerber_file"],
                    operator=row["operator"],
                    recipe_name=row["recipe_name"],
                    report_path=row["report_path"],
                    defects=defects,
                    notes=row["notes"] or "",
                ))
            
            return records
    
    def get_combined_history(self, code: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Obtém histórico combinado de tensão e inspeção visual."""
        combined = []
        
        for record in self.get_tension_history(code, limit=limit):
            combined.append({
                "type": "tension",
                "timestamp": record.timestamp,
                "record": record,
            })
        
        for record in self.get_inspection_history(code, limit=limit):
            combined.append({
                "type": "inspection",
                "timestamp": record.timestamp,
                "record": record,
            })
        
        combined.sort(key=lambda x: x["timestamp"], reverse=True)
        return combined[:limit]
    
    def get_inspection_stats(self, code: str) -> Dict[str, Any]:
        """Obtém estatísticas de inspeções visuais de um stencil."""
        history = self.get_inspection_history(code, limit=100)
        
        if not history:
            return {
                "total_inspections": 0,
                "pass_count": 0,
                "fail_count": 0,
                "pass_rate": 0.0,
                "avg_pass_rate": 0.0,
                "last_result": None,
            }
        
        pass_count = sum(1 for r in history if r.result == "PASS")
        fail_count = len(history) - pass_count
        avg_pass_rate = sum(r.pass_rate for r in history) / len(history)
        
        return {
            "total_inspections": len(history),
            "pass_count": pass_count,
            "fail_count": fail_count,
            "pass_rate": (pass_count / len(history)) * 100 if history else 0,
            "avg_pass_rate": avg_pass_rate,
            "last_result": history[0].result if history else None,
        }
    
    # -------------------------------------------------------------------------
    #  ANÁLISE DE TENDÊNCIA
    # -------------------------------------------------------------------------
    
    def get_trend_analysis(self, code: str, 
                           warning_low: float = None) -> TrendAnalysis:
        """Analisa tendência de degradação de um stencil."""
        history = self.get_tension_history(code, limit=20)
        
        if not history:
            return TrendAnalysis(
                stencil_code=code,
                record_count=0,
                first_average=0,
                last_average=0,
                moving_average=0,
                variation_percent=0,
                trend="stable",
            )
        
        # Inverte para ordem cronológica
        history = list(reversed(history))
        averages = [r.average_tension for r in history]
        
        first_avg = averages[0]
        last_avg = averages[-1]
        
        window = min(self.MOVING_AVERAGE_WINDOW, len(averages))
        moving_avg = sum(averages[-window:]) / window
        
        if first_avg > 0:
            variation = (last_avg - first_avg) / first_avg
        else:
            variation = 0
        
        if variation < -self.DEGRADATION_THRESHOLD:
            trend = "degrading"
        elif variation > self.DEGRADATION_THRESHOLD:
            trend = "improving"
        else:
            trend = "stable"
        
        alert = None
        if warning_low and moving_avg < warning_low:
            alert = f"⚠️ Tensão média ({moving_avg:.1f}) abaixo do limite ({warning_low:.1f})"
        elif trend == "degrading":
            alert = f"📉 Tendência de queda: {abs(variation)*100:.1f}% desde primeira medição"
        
        return TrendAnalysis(
            stencil_code=code,
            record_count=len(history),
            first_average=first_avg,
            last_average=last_avg,
            moving_average=moving_avg,
            variation_percent=variation * 100,
            trend=trend,
            alert=alert,
        )
    
    def check_degradation_alert(self, code: str, 
                                 warning_low: float = None) -> Optional[str]:
        """Verifica se há alerta de degradação."""
        analysis = self.get_trend_analysis(code, warning_low)
        return analysis.alert
    
    # -------------------------------------------------------------------------
    #  CONSULTAS AVANÇADAS
    # -------------------------------------------------------------------------
    
    def search_stencils(self, query: str, status: str = None) -> List[Stencil]:
        """
        Busca stencils por código ou descrição.
        
        Args:
            query: Texto para buscar (código ou descrição)
            status: Filtrar por status (opcional)
        """
        with self._get_connection() as conn:
            sql = """
                SELECT * FROM stencils 
                WHERE (code LIKE ? OR description LIKE ?)
            """
            params = [f"%{query}%", f"%{query}%"]
            
            if status:
                sql += " AND status = ?"
                params.append(status)
            
            sql += " ORDER BY last_inspection DESC NULLS LAST"
            
            cursor = conn.execute(sql, params)
            
            return [
                Stencil(
                    code=row["code"],
                    description=row["description"] or "",
                    recipe_name=row["recipe_name"],
                    created_at=row["created_at"],
                    last_inspection=row["last_inspection"],
                    inspection_count=row["inspection_count"],
                    status=row["status"],
                    notes=row["notes"] or "",
                )
                for row in cursor.fetchall()
            ]
    
    def get_stencils_by_recipe(self, recipe_name: str) -> List[Stencil]:
        """Obtém todos os stencils de uma receita específica."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM stencils WHERE recipe_name = ? ORDER BY code",
                (recipe_name,)
            )
            
            return [
                Stencil(
                    code=row["code"],
                    description=row["description"] or "",
                    recipe_name=row["recipe_name"],
                    created_at=row["created_at"],
                    last_inspection=row["last_inspection"],
                    inspection_count=row["inspection_count"],
                    status=row["status"],
                    notes=row["notes"] or "",
                )
                for row in cursor.fetchall()
            ]
    
    def get_tension_records_by_period(self, 
                                       start_date: str, 
                                       end_date: str,
                                       code: str = None) -> List[Dict[str, Any]]:
        """
        Obtém registros de tensão por período.
        
        Args:
            start_date: Data inicial (ISO format)
            end_date: Data final (ISO format)
            code: Código do stencil (opcional, todos se None)
        """
        with self._get_connection() as conn:
            if code:
                stencil_id = self._get_stencil_id(conn, code)
                cursor = conn.execute("""
                    SELECT tr.*, s.code as stencil_code
                    FROM tension_records tr
                    JOIN stencils s ON tr.stencil_id = s.id
                    WHERE tr.stencil_id = ?
                    AND tr.timestamp >= ? AND tr.timestamp <= ?
                    ORDER BY tr.timestamp DESC
                """, (stencil_id, start_date, end_date))
            else:
                cursor = conn.execute("""
                    SELECT tr.*, s.code as stencil_code
                    FROM tension_records tr
                    JOIN stencils s ON tr.stencil_id = s.id
                    WHERE tr.timestamp >= ? AND tr.timestamp <= ?
                    ORDER BY tr.timestamp DESC
                """, (start_date, end_date))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_inspection_records_by_period(self,
                                          start_date: str,
                                          end_date: str,
                                          code: str = None) -> List[Dict[str, Any]]:
        """
        Obtém registros de inspeção por período.
        
        Args:
            start_date: Data inicial (ISO format)
            end_date: Data final (ISO format)
            code: Código do stencil (opcional)
        """
        with self._get_connection() as conn:
            if code:
                stencil_id = self._get_stencil_id(conn, code)
                cursor = conn.execute("""
                    SELECT ir.*, s.code as stencil_code
                    FROM inspection_records ir
                    JOIN stencils s ON ir.stencil_id = s.id
                    WHERE ir.stencil_id = ?
                    AND ir.timestamp >= ? AND ir.timestamp <= ?
                    ORDER BY ir.timestamp DESC
                """, (stencil_id, start_date, end_date))
            else:
                cursor = conn.execute("""
                    SELECT ir.*, s.code as stencil_code
                    FROM inspection_records ir
                    JOIN stencils s ON ir.stencil_id = s.id
                    WHERE ir.timestamp >= ? AND ir.timestamp <= ?
                    ORDER BY ir.timestamp DESC
                """, (start_date, end_date))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas gerais do banco de dados."""
        with self._get_connection() as conn:
            stats = {}
            
            # Total de stencils por status
            cursor = conn.execute("""
                SELECT status, COUNT(*) as count 
                FROM stencils GROUP BY status
            """)
            stats["stencils_by_status"] = {
                row["status"]: row["count"] for row in cursor.fetchall()
            }
            
            # Total de registros
            cursor = conn.execute("SELECT COUNT(*) FROM stencils")
            stats["total_stencils"] = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM tension_records")
            stats["total_tension_records"] = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM inspection_records")
            stats["total_inspection_records"] = cursor.fetchone()[0]
            
            # Tamanho do banco
            stats["database_size_bytes"] = self.db_path.stat().st_size
            
            return stats
    
    # -------------------------------------------------------------------------
    #  MIGRAÇÃO DE DADOS JSON
    # -------------------------------------------------------------------------
    
    def migrate_from_json(self, json_dir: str) -> Dict[str, int]:
        """
        Migra dados do formato JSON para SQLite.
        
        Args:
            json_dir: Caminho do diretório com dados JSON (data/stencils/)
            
        Returns:
            Dicionário com contagem de registros migrados
        """
        json_path = Path(json_dir)
        
        if not json_path.exists():
            log.warning(f"Diretório JSON não encontrado: {json_dir}")
            return {"stencils": 0, "tension_records": 0, "inspection_records": 0}
        
        stats = {
            "stencils": 0,
            "tension_records": 0,
            "inspection_records": 0,
        }
        
        log.info(f"Iniciando migração de: {json_dir}")
        
        for item in json_path.iterdir():
            if not item.is_dir():
                continue
            
            info_path = item / "info.json"
            if not info_path.exists():
                continue
            
            try:
                # Migra stencil
                with open(info_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                code = data.get("code", item.name)
                
                if not self.stencil_exists(code):
                    with self._get_connection() as conn:
                        conn.execute("""
                            INSERT INTO stencils 
                            (code, description, recipe_name, created_at, 
                             last_inspection, inspection_count, status, notes, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            code,
                            data.get("description", ""),
                            data.get("recipe_name"),
                            data.get("created_at", datetime.now().isoformat()),
                            data.get("last_inspection"),
                            data.get("inspection_count", 0),
                            data.get("status", "active"),
                            data.get("notes", ""),
                            datetime.now().isoformat(),
                        ))
                    stats["stencils"] += 1
                    log.debug(f"Stencil migrado: {code}")
                
                # Migra histórico de tensão
                history_dir = item / "history"
                if history_dir.exists():
                    for hist_file in history_dir.glob("*_tension.json"):
                        try:
                            with open(hist_file, "r", encoding="utf-8") as f:
                                record_data = json.load(f)
                            
                            record = TensionRecord.from_dict(record_data)
                            self.add_tension_record(code, record)
                            stats["tension_records"] += 1
                        except Exception as e:
                            log.warning(f"Erro ao migrar {hist_file}: {e}")
                    
                    # Migra histórico de inspeção
                    for hist_file in history_dir.glob("*_inspection.json"):
                        try:
                            with open(hist_file, "r", encoding="utf-8") as f:
                                record_data = json.load(f)
                            
                            record = InspectionRecord.from_dict(record_data)
                            self.add_inspection_record(code, record)
                            stats["inspection_records"] += 1
                        except Exception as e:
                            log.warning(f"Erro ao migrar {hist_file}: {e}")
                
            except Exception as e:
                log.error(f"Erro ao migrar {item}: {e}")
        
        log.info(f"Migração concluída: {stats}")
        return stats
    
    def backup_database(self, backup_path: str = None) -> str:
        """
        Cria backup do banco de dados.
        
        Args:
            backup_path: Caminho para o backup (opcional)
            
        Returns:
            Caminho do arquivo de backup criado
        """
        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.db_path.parent / f"stencils_backup_{timestamp}.db"
        
        backup_path = Path(backup_path)
        shutil.copy2(self.db_path, backup_path)
        
        log.info(f"Backup criado: {backup_path}")
        return str(backup_path)


# ============================================================================
#  FUNÇÃO DE MIGRAÇÃO
# ============================================================================

def migrate_json_to_sqlite(json_dir: str = None, db_path: str = None) -> Dict[str, int]:
    """
    Função utilitária para migrar dados JSON para SQLite.
    
    Args:
        json_dir: Diretório com dados JSON (default: data/stencils/)
        db_path: Caminho do banco SQLite (default: data/stencils.db)
        
    Returns:
        Estatísticas da migração
    """
    if json_dir is None:
        base = Path(__file__).parent.parent
        json_dir = base / "data" / "stencils"
    
    db = StencilDatabase(db_path)
    return db.migrate_from_json(str(json_dir))


if __name__ == "__main__":
    # Teste de migração standalone
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) > 1 and sys.argv[1] == "migrate":
        stats = migrate_json_to_sqlite()
        print(f"\n✅ Migração concluída!")
        print(f"   Stencils: {stats['stencils']}")
        print(f"   Registros de tensão: {stats['tension_records']}")
        print(f"   Registros de inspeção: {stats['inspection_records']}")
    else:
        print("Uso: python stencil_database.py migrate")
