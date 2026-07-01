"""
stencil_tracker.py
-------------------
Gerenciamento de stencils individuais e seu histórico de medições de tensão.
"""

import json
import logging
from datetime import datetime
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, List, Dict, Any
from .runtime_paths import get_runtime_path
from .system_change_log import get_system_change_log

log = logging.getLogger(__name__)


def normalize_stencil_code(code: Any) -> str:
    """Normaliza codigos de stencil vindos de leitura manual ou leitor USB."""
    return str(code or "").strip().upper()


@dataclass
class Stencil:
    """Representa um stencil físico individual."""

    code: str
    description: str = ""
    recipe_name: Optional[str] = None
    created_at: str = ""
    last_inspection: Optional[str] = None
    inspection_count: int = 0
    status: str = "active"
    notes: str = ""

    def __post_init__(self):
        self.code = normalize_stencil_code(self.code)
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Stencil":
        return cls(
            code=data.get("code", ""),
            description=data.get("description", ""),
            recipe_name=data.get("recipe_name"),
            created_at=data.get("created_at", ""),
            last_inspection=data.get("last_inspection"),
            inspection_count=data.get("inspection_count", 0),
            status=data.get("status", "active"),
            notes=data.get("notes", ""),
        )


@dataclass
class TensionRecord:
    """Registro de uma medição de tensão."""

    timestamp: str
    measurements: List[Dict[str, Any]] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    average_tension: float = 0.0
    min_tension: float = 0.0
    max_tension: float = 0.0
    result: str = "OK"
    ok_count: int = 0
    warning_count: int = 0
    nok_count: int = 0
    operator: Optional[str] = None
    recipe_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TensionRecord":
        return cls(
            timestamp=data.get("timestamp", ""),
            measurements=data.get("measurements", []),
            parameters=data.get("parameters", {}),
            average_tension=data.get("average_tension", 0.0),
            min_tension=data.get("min_tension", 0.0),
            max_tension=data.get("max_tension", 0.0),
            result=data.get("result", "OK"),
            ok_count=data.get("ok_count", 0),
            warning_count=data.get("warning_count", 0),
            nok_count=data.get("nok_count", 0),
            operator=data.get("operator"),
            recipe_name=data.get("recipe_name"),
        )

    @classmethod
    def from_tension_data(
        cls,
        tension_data: Dict[str, Any],
        recipe_name: str = None,
        operator: str = None
    ) -> "TensionRecord":
        measurements = tension_data.get("measurements", [])

        if not measurements:
            return cls(
                timestamp=datetime.now().isoformat(),
                parameters=tension_data.get("parameters", {}),
                recipe_name=recipe_name,
                operator=operator,
            )

        tensions = [float(m.get("tension", 0)) for m in measurements]
        ok_count = sum(1 for m in measurements if m.get("status") == "OK")
        warning_count = sum(1 for m in measurements if m.get("status") == "WARNING")
        nok_count = sum(1 for m in measurements if m.get("status") == "NOK")

        if nok_count > 0:
            result = "NOK"
        elif warning_count > len(measurements) * 0.2:
            result = "WARNING"
        else:
            result = "OK"

        return cls(
            timestamp=datetime.now().isoformat(),
            measurements=measurements,
            parameters=tension_data.get("parameters", {}),
            average_tension=sum(tensions) / len(tensions) if tensions else 0,
            min_tension=min(tensions) if tensions else 0,
            max_tension=max(tensions) if tensions else 0,
            result=result,
            ok_count=ok_count,
            warning_count=warning_count,
            nok_count=nok_count,
            operator=operator,
            recipe_name=recipe_name,
        )


@dataclass
class TrendAnalysis:
    """Resultado da análise de tendência de um stencil."""

    stencil_code: str
    record_count: int
    first_average: float
    last_average: float
    moving_average: float
    variation_percent: float
    trend: str
    alert: Optional[str] = None


class StencilTracker:
    """Gerencia stencils e histórico local em JSON."""

    MOVING_AVERAGE_WINDOW = 5
    DEGRADATION_THRESHOLD = 0.10

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            self.data_dir = get_runtime_path("data", "stencils")
        else:
            self.data_dir = Path(data_dir)

        self._cache: Dict[str, Stencil] = {}
        self._ensure_directories()

    def _ensure_directories(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _get_stencil_dir(self, code: str) -> Path:
        code = normalize_stencil_code(code)
        return self.data_dir / code

    def _get_stencil_info_path(self, code: str) -> Path:
        code = normalize_stencil_code(code)
        return self._get_stencil_dir(code) / "info.json"

    def _get_history_dir(self, code: str) -> Path:
        code = normalize_stencil_code(code)
        return self._get_stencil_dir(code) / "history"

    def stencil_exists(self, code: str) -> bool:
        raw_code = str(code or "").strip()
        code = normalize_stencil_code(code)
        return self._get_stencil_info_path(code).exists() or (
            bool(raw_code) and (self.data_dir / raw_code / "info.json").exists()
        )

    def get_stencil(self, code: str) -> Optional[Stencil]:
        raw_code = str(code or "").strip()
        code = normalize_stencil_code(code)
        if code in self._cache:
            return self._cache[code]

        info_path = self._get_stencil_info_path(code)
        if not info_path.exists() and raw_code:
            legacy_info_path = self.data_dir / raw_code / "info.json"
            if legacy_info_path.exists():
                info_path = legacy_info_path
        if not info_path.exists():
            return None

        try:
            with open(info_path, "r", encoding="utf-8") as file:
                stencil = Stencil.from_dict(json.load(file))
        except Exception as exc:
            log.error(f"Erro ao carregar stencil {code}: {exc}")
            return None

        self._cache[code] = stencil
        return stencil

    def create_stencil(
        self,
        code: str,
        description: str = "",
        recipe_name: str = None
    ) -> Stencil:
        code = normalize_stencil_code(code)
        if self.stencil_exists(code):
            raise ValueError(f"Stencil '{code}' já existe")

        stencil = Stencil(
            code=code,
            description=description,
            recipe_name=recipe_name,
        )

        self._get_stencil_dir(code).mkdir(parents=True, exist_ok=True)
        self._get_history_dir(code).mkdir(parents=True, exist_ok=True)
        self._save_stencil(stencil)
        get_system_change_log().log_event(
            category="stencil",
            action="created",
            target_type="stencil",
            target_id=code,
            description=f"Stencil criado: {code}",
            metadata={
                "description": description,
                "recipe_name": recipe_name,
                "stencil_dir": str(self._get_stencil_dir(code)),
            },
        )

        log.info(f"Stencil criado: {code}")
        return stencil

    def update_stencil(self, stencil: Stencil) -> None:
        stencil.code = normalize_stencil_code(stencil.code)
        if not self.stencil_exists(stencil.code):
            raise ValueError(f"Stencil '{stencil.code}' não existe")

        previous_data = None
        info_path = self._get_stencil_info_path(stencil.code)
        if info_path.exists():
            try:
                with open(info_path, "r", encoding="utf-8") as file:
                    previous_data = json.load(file)
            except Exception as exc:
                log.warning(f"Erro ao ler estado anterior do stencil {stencil.code}: {exc}")
        self._save_stencil(stencil)
        get_system_change_log().log_event(
            category="stencil",
            action="updated",
            target_type="stencil",
            target_id=stencil.code,
            description=f"Stencil atualizado: {stencil.code}",
            changes={"old": previous_data, "new": stencil.to_dict()},
        )
        log.info(f"Stencil atualizado: {stencil.code}")

    def _save_stencil(self, stencil: Stencil) -> None:
        stencil.code = normalize_stencil_code(stencil.code)
        with open(self._get_stencil_info_path(stencil.code), "w", encoding="utf-8") as file:
            json.dump(stencil.to_dict(), file, indent=2, ensure_ascii=False)
        self._cache[stencil.code] = stencil

    def list_stencils(self, status: str = None) -> List[Stencil]:
        stencils = []
        for stencil_dir in self.data_dir.iterdir():
            if not stencil_dir.is_dir():
                continue
            stencil = self.get_stencil(stencil_dir.name)
            if not stencil:
                continue
            if status and stencil.status != status:
                continue
            stencils.append(stencil)

        stencils.sort(key=lambda s: s.last_inspection or s.created_at, reverse=True)
        return stencils

    def delete_stencil(self, code: str) -> bool:
        import shutil

        code = normalize_stencil_code(code)
        stencil_dir = self._get_stencil_dir(code)
        if not stencil_dir.exists():
            return False

        try:
            shutil.rmtree(stencil_dir)
            self._cache.pop(code, None)
            get_system_change_log().log_event(
                category="stencil",
                action="deleted",
                target_type="stencil",
                target_id=code,
                description=f"Stencil removido: {code}",
                metadata={"stencil_dir": str(stencil_dir)},
            )
            log.info(f"Stencil removido: {code}")
            return True
        except Exception as exc:
            log.error(f"Erro ao remover stencil {code}: {exc}")
            return False

    def add_tension_record(self, code: str, record: TensionRecord) -> None:
        code = normalize_stencil_code(code)
        stencil = self.get_stencil(code)
        if not stencil:
            raise ValueError(f"Stencil '{code}' não encontrado")

        history_dir = self._get_history_dir(code)
        history_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.fromisoformat(record.timestamp)
        filepath = history_dir / timestamp.strftime("%Y-%m-%d_%H%M%S_tension.json")
        with open(filepath, "w", encoding="utf-8") as file:
            json.dump(record.to_dict(), file, indent=2, ensure_ascii=False)

        stencil.last_inspection = record.timestamp
        stencil.inspection_count += 1
        if record.result == "NOK":
            stencil.status = "retired"
        elif record.result == "WARNING":
            stencil.status = "warning"
        elif record.result == "OK":
            stencil.status = "active"

        self._save_stencil(stencil)
        log.info(f"Registro de tensão adicionado para {code}: {record.result}")

    def delete_tension_record(self, code: str, timestamp: str) -> bool:
        """
        Remove uma medição de tensão específica do histórico do stencil.

        Args:
            code: Código do stencil
            timestamp: Timestamp ISO persistido no registro da medição

        Returns:
            True se a medição foi encontrada e removida, False caso contrário.
        """
        code = normalize_stencil_code(code)
        stencil = self.get_stencil(code)
        if not stencil:
            raise ValueError(f"Stencil '{code}' não encontrado")

        history_dir = self._get_history_dir(code)
        if not history_dir.exists():
            return False

        target_path = None
        deleted_record = None

        for filepath in history_dir.glob("*_tension.json"):
            try:
                with open(filepath, "r", encoding="utf-8") as file:
                    record_data = json.load(file)
            except Exception as exc:
                log.warning(f"Erro ao ler {filepath} para exclusão: {exc}")
                continue

            if record_data.get("timestamp") == timestamp:
                target_path = filepath
                deleted_record = record_data
                break

        if target_path is None:
            return False

        target_path.unlink()
        self._refresh_tension_metadata(code)

        get_system_change_log().log_event(
            category="stencil",
            action="tension_record_deleted",
            target_type="tension_record",
            target_id=f"{code}:{timestamp}",
            description=f"Medição de tensão excluída: {code} em {timestamp}",
            changes={"deleted": deleted_record},
            metadata={"history_file": str(target_path)},
        )
        log.info(f"Registro de tensão removido para {code}: {timestamp}")
        return True

    def get_tension_history(self, code: str, limit: int = 50) -> List[TensionRecord]:
        code = normalize_stencil_code(code)
        history_dir = self._get_history_dir(code)
        if not history_dir.exists():
            return []

        records: List[TensionRecord] = []
        files = sorted(history_dir.glob("*_tension.json"), reverse=True)

        for filepath in files[:limit]:
            try:
                with open(filepath, "r", encoding="utf-8") as file:
                    records.append(TensionRecord.from_dict(json.load(file)))
            except Exception as exc:
                log.warning(f"Erro ao carregar {filepath}: {exc}")

        return records

    def _refresh_tension_metadata(self, code: str) -> None:
        """Recalcula metadados do stencil após alteração no histórico."""
        code = normalize_stencil_code(code)
        stencil = self.get_stencil(code)
        if stencil is None:
            return

        history = self.get_tension_history(code, limit=1_000_000)
        stencil.inspection_count = len(history)

        if not history:
            stencil.last_inspection = None
            stencil.status = "active"
            self._save_stencil(stencil)
            return

        latest_record = history[0]
        stencil.last_inspection = latest_record.timestamp
        if latest_record.result == "NOK":
            stencil.status = "retired"
        elif latest_record.result == "WARNING":
            stencil.status = "warning"
        else:
            stencil.status = "active"

        self._save_stencil(stencil)

    def get_trend_analysis(self, code: str, warning_low: float = None) -> TrendAnalysis:
        code = normalize_stencil_code(code)
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
        averages = [record.average_tension for record in history]

        first_avg = averages[0]
        last_avg = averages[-1]
        window = min(self.MOVING_AVERAGE_WINDOW, len(averages))
        moving_avg = sum(averages[-window:]) / window

        variation = (last_avg - first_avg) / first_avg if first_avg > 0 else 0

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
        return self.get_trend_analysis(code, warning_low).alert
