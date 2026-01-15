"""
stencil_database.py
-------------------
Fachada para persistência SQLite de stencils.

Esta classe fornece uma interface de compatibilidade (backward compatibility)
para a API original, delegando as operações para os repositórios apropriados.

ARQUITETURA:
    StencilDatabase (Fachada)
    ├── DatabaseConnection (gerenciamento de conexão)
    ├── SqliteStencilRepository (CRUD de stencils)
    ├── SqliteTensionRepository (histórico de tensão)
    ├── SqliteInspectionRepository (histórico de inspeção)
    └── JsonToSqliteMigrator (migração JSON → SQLite)

DEPRECATION:
    Esta fachada mantém compatibilidade com código legado.
    Novo código deve usar os repositórios diretamente.
"""

import logging
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any

from .stencil_tracker import (
    Stencil, TensionRecord, InspectionRecord, TrendAnalysis
)
from .database.connection import SqliteConnection
from .database.repositories import (
    SqliteStencilRepository,
    SqliteTensionRepository,
    SqliteInspectionRepository,
)
from .database.migrators import JsonToSqliteMigrator

log = logging.getLogger(__name__)


class StencilDatabase:
    """
    Fachada para gerenciamento de banco de dados SQLite para stencils.

    Esta classe mantém compatibilidade com a API original enquanto delega
    as operações para os repositórios apropriados (Repository Pattern).

    Atributos:
        db_path: Caminho para o arquivo de banco de dados SQLite
        MOVING_AVERAGE_WINDOW: Janela para média móvel (análise de tendência)
        DEGRADATION_THRESHOLD: Limiar para alerta de degradação (10%)
    """

    MOVING_AVERAGE_WINDOW = 5
    DEGRADATION_THRESHOLD = 0.10

    def __init__(self, db_path: str = None):
        """
        Inicializa a fachada do banco de dados.

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

        # Inicializa conexão e repositórios
        self._connection = SqliteConnection(str(self.db_path))

        # Inicializa schema do banco
        self._init_database()

        # Inicializa repositórios
        self._stencil_repo = SqliteStencilRepository(self._connection)
        self._tension_repo = SqliteTensionRepository(self._connection)
        self._inspection_repo = SqliteInspectionRepository(self._connection)

        log.info(f"StencilDatabase inicializado em: {self.db_path}")

    def _init_database(self):
        """Inicializa schema do banco de dados."""
        from .database.connection import CREATE_TABLES

        # Executa schema SQL
        self._connection.init_schema(CREATE_TABLES)

        log.debug("Banco de dados inicializado")

    # -------------------------------------------------------------------------
    #  CRUD DE STENCILS (delega para SqliteStencilRepository)
    # -------------------------------------------------------------------------

    def stencil_exists(self, code: str) -> bool:
        """Verifica se um stencil existe."""
        return self._stencil_repo.exists(code)

    def get_stencil(self, code: str) -> Optional[Stencil]:
        """Obtém um stencil pelo código."""
        return self._stencil_repo.get(code)

    def create_stencil(self, code: str,
                       description: str = "",
                       recipe_name: str = None) -> Stencil:
        """Cria um novo stencil."""
        return self._stencil_repo.create(code, description, recipe_name)

    def update_stencil(self, stencil: Stencil) -> None:
        """Atualiza dados de um stencil existente."""
        self._stencil_repo.update(stencil)

    def delete_stencil(self, code: str) -> bool:
        """Remove um stencil (retorna True se removido, False se não existe)."""
        return self._stencil_repo.delete(code)

    def list_stencils(self, status: str = None) -> List[Stencil]:
        """Lista stencils, opcionalmente filtrando por status."""
        return self._stencil_repo.list(status)

    def search_stencils(self, query: str, status: str = None) -> List[Stencil]:
        """Busca stencils por código ou descrição."""
        return self._stencil_repo.search(query, status)

    def get_stencils_by_recipe(self, recipe_name: str) -> List[Stencil]:
        """Obtém todos os stencils de uma receita específica."""
        return self._stencil_repo.get_by_recipe(recipe_name)

    # -------------------------------------------------------------------------
    #  CRUD DE TENSÃO (delega para SqliteTensionRepository)
    # -------------------------------------------------------------------------

    def add_tension_record(self, code: str, record: TensionRecord) -> None:
        """Adiciona registro de medição de tensão."""
        self._tension_repo.add(code, record)

    def get_tension_history(self, code: str, limit: int = 50) -> List[TensionRecord]:
        """Obtém histórico de medições de tensão de um stencil."""
        return self._tension_repo.get_history(code, limit)

    def get_tension_records_by_period(self,
                                      start_date: str,
                                      end_date: str,
                                      code: str = None) -> List[Dict[str, Any]]:
        """Obtém registros de tensão por período."""
        return self._tension_repo.get_by_period(start_date, end_date, code)

    def get_latest_tension(self, code: str) -> Optional[TensionRecord]:
        """Obtém medição de tensão mais recente de um stencil."""
        return self._tension_repo.get_latest(code)

    # -------------------------------------------------------------------------
    #  CRUD DE INSPEÇÃO (delega para SqliteInspectionRepository)
    # -------------------------------------------------------------------------

    def add_inspection_record(self, code: str, record: InspectionRecord) -> None:
        """Adiciona registro de inspeção visual."""
        self._inspection_repo.add(code, record)

    def get_inspection_history(self, code: str, limit: int = 50) -> List[InspectionRecord]:
        """Obtém histórico de inspeções de um stencil."""
        return self._inspection_repo.get_history(code, limit)

    def get_inspection_records_by_period(self,
                                        start_date: str,
                                        end_date: str,
                                        code: str = None) -> List[Dict[str, Any]]:
        """Obtém registros de inspeção por período."""
        return self._inspection_repo.get_by_period(start_date, end_date, code)

    def get_inspection_stats(self, code: str) -> Dict[str, Any]:
        """Obtém estatísticas de inspeção de um stencil."""
        return self._inspection_repo.get_stats(code)

    def get_combined_history(self, code: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Obtém histórico combinado (tensão + inspeção) de um stencil."""
        return self._inspection_repo.get_combined_history(code, limit)

    # -------------------------------------------------------------------------
    #  SERVIÇOS DE ANÁLISE (mantidos na fachada - lógica complexa)
    # -------------------------------------------------------------------------

    def get_trend_analysis(self, code: str,
                           warning_low: float = None) -> TrendAnalysis:
        """
        Analisa tendência de degradação de um stencil.

        Calcula estatísticas de tendência baseado no histórico
        de medições de tensão.
        """
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
    #  UTILITÁRIOS
    # -------------------------------------------------------------------------

    def get_database_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas gerais do banco de dados."""
        stats = {}

        # Total de stencils por status
        stencils = self._stencil_repo.list()
        stats["total_stencils"] = len(stencils)
        stats["stencils_by_status"] = {}
        for s in stencils:
            stats["stencils_by_status"][s.status] = \
                stats["stencils_by_status"].get(s.status, 0) + 1

        # Total de registros (contagem aproximada)
        stats["total_tension_records"] = 0
        stats["total_inspection_records"] = 0

        for code in [s.code for s in stencils]:
            tension_count = len(self._tension_repo.get_history(code, limit=999999))
            stats["total_tension_records"] += tension_count

            inspection_count = len(self._inspection_repo.get_history(code, limit=999999))
            stats["total_inspection_records"] += inspection_count

        # Tamanho do banco
        stats["database_size_bytes"] = self.db_path.stat().st_size if self.db_path.exists() else 0

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
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.db_path.parent / f"stencils_backup_{timestamp}.db"

        backup_path = Path(backup_path)
        shutil.copy2(self.db_path, backup_path)

        log.info(f"Backup criado: {backup_path}")
        return str(backup_path)

    # -------------------------------------------------------------------------
    #  MIGRAÇÃO (delega para JsonToSqliteMigrator)
    # -------------------------------------------------------------------------

    def migrate_from_json(self, json_dir: str) -> Dict[str, int]:
        """
        Migra dados do formato JSON para SQLite.

        Args:
            json_dir: Caminho do diretório com dados JSON

        Returns:
            Estatísticas da migração
        """
        migrator = JsonToSqliteMigrator(self._connection)
        return migrator.migrate(json_dir)


# ============================================================================
#  FUNÇÃO DE CONVENIÊNCIA (compatibilidade com código legado)
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
