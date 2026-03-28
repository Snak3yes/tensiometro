"""
stencil_database.py
-------------------
Fachada para persistência SQLite de stencils e histórico de tensão.
"""

import logging
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any

from .stencil_tracker import Stencil, TensionRecord, TrendAnalysis
from .database.connection import SqliteConnection
from .database.repositories import SqliteStencilRepository, SqliteTensionRepository
from .database.migrators import JsonToSqliteMigrator

log = logging.getLogger(__name__)


class StencilDatabase:
    """
    Fachada para gerenciamento de banco de dados SQLite para stencils.
    """

    MOVING_AVERAGE_WINDOW = 5
    DEGRADATION_THRESHOLD = 0.10

    def __init__(self, db_path: str = None):
        if db_path is None:
            base = Path(__file__).parent.parent
            self.db_path = base / "data" / "stencils.db"
        else:
            self.db_path = Path(db_path)

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = SqliteConnection(str(self.db_path))
        self._init_database()

        self._stencil_repo = SqliteStencilRepository(self._connection)
        self._tension_repo = SqliteTensionRepository(self._connection)

        log.info(f"StencilDatabase inicializado em: {self.db_path}")

    def _init_database(self):
        from .database.connection import CREATE_TABLES

        self._connection.init_schema(CREATE_TABLES)
        log.debug("Banco de dados inicializado")

    def stencil_exists(self, code: str) -> bool:
        return self._stencil_repo.exists(code)

    def get_stencil(self, code: str) -> Optional[Stencil]:
        return self._stencil_repo.get(code)

    def create_stencil(self, code: str, description: str = "", recipe_name: str = None) -> Stencil:
        return self._stencil_repo.create(code, description, recipe_name)

    def update_stencil(self, stencil: Stencil) -> None:
        self._stencil_repo.update(stencil)

    def delete_stencil(self, code: str) -> bool:
        return self._stencil_repo.delete(code)

    def list_stencils(self, status: str = None) -> List[Stencil]:
        return self._stencil_repo.list(status)

    def search_stencils(self, query: str, status: str = None) -> List[Stencil]:
        return self._stencil_repo.search(query, status)

    def get_stencils_by_recipe(self, recipe_name: str) -> List[Stencil]:
        return self._stencil_repo.get_by_recipe(recipe_name)

    def add_tension_record(self, code: str, record: TensionRecord) -> None:
        self._tension_repo.add(code, record)

    def get_tension_history(self, code: str, limit: int = 50) -> List[TensionRecord]:
        return self._tension_repo.get_history(code, limit)

    def get_tension_records_by_period(
        self,
        start_date: str,
        end_date: str,
        code: str = None
    ) -> List[Dict[str, Any]]:
        return self._tension_repo.get_by_period(start_date, end_date, code)

    def get_latest_tension(self, code: str) -> Optional[TensionRecord]:
        return self._tension_repo.get_latest(code)

    def get_trend_analysis(self, code: str, warning_low: float = None) -> TrendAnalysis:
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
            alert = f"Tensão média ({moving_avg:.1f}) abaixo do limite ({warning_low:.1f})"
        elif trend == "degrading":
            alert = f"Tendência de queda: {abs(variation) * 100:.1f}% desde primeira medição"

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

    def check_degradation_alert(self, code: str, warning_low: float = None) -> Optional[str]:
        analysis = self.get_trend_analysis(code, warning_low)
        return analysis.alert

    def get_database_stats(self) -> Dict[str, Any]:
        stats = {}

        stencils = self._stencil_repo.list()
        stats["total_stencils"] = len(stencils)
        stats["stencils_by_status"] = {}
        for stencil in stencils:
            stats["stencils_by_status"][stencil.status] = (
                stats["stencils_by_status"].get(stencil.status, 0) + 1
            )

        stats["total_tension_records"] = 0
        for code in [s.code for s in stencils]:
            stats["total_tension_records"] += len(
                self._tension_repo.get_history(code, limit=999999)
            )

        stats["database_size_bytes"] = self.db_path.stat().st_size if self.db_path.exists() else 0
        return stats

    def backup_database(self, backup_path: str = None) -> str:
        if backup_path is None:
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.db_path.parent / f"stencils_backup_{timestamp}.db"

        backup_path = Path(backup_path)
        shutil.copy2(self.db_path, backup_path)

        log.info(f"Backup criado: {backup_path}")
        return str(backup_path)

    def migrate_from_json(self, json_dir: str) -> Dict[str, int]:
        migrator = JsonToSqliteMigrator(self._connection)
        return migrator.migrate(json_dir)


def migrate_json_to_sqlite(json_dir: str = None, db_path: str = None) -> Dict[str, int]:
    if json_dir is None:
        base = Path(__file__).parent.parent
        json_dir = base / "data" / "stencils"

    db = StencilDatabase(db_path)
    return db.migrate_from_json(str(json_dir))


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) > 1 and sys.argv[1] == "migrate":
        stats = migrate_json_to_sqlite()
        print("\nMigração concluída!")
        print(f"   Stencils: {stats['stencils']}")
        print(f"   Registros de tensão: {stats['tension_records']}")
    else:
        print("Uso: python stencil_database.py migrate")
