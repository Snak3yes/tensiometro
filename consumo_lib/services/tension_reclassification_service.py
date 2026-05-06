"""Helpers para reclassificar historico de tensao com criterios atuais."""

from copy import deepcopy
from typing import Any

from aoi_lib.recipe_manager import TensionAcceptance
from aoi_lib.stencil_tracker import TensionRecord


def reclassify_tension_record(record: TensionRecord, criteria: TensionAcceptance | None) -> TensionRecord:
    """Retorna uma copia do registro com status/counts recalculados."""
    if criteria is None:
        return record

    data = record.to_dict() if hasattr(record, "to_dict") else dict(record)
    measurements = deepcopy(data.get("measurements", []) or [])

    if measurements:
        tensions = []
        ok_count = warning_count = nok_count = 0
        for measurement in measurements:
            tension = _to_float(measurement.get("parsed_value", measurement.get("tension")), 0.0)
            measurement["tension"] = tension
            measurement["parsed_value"] = tension
            status = criteria.classify(tension)
            measurement["status"] = status
            tensions.append(tension)

            if status == "OK":
                ok_count += 1
            elif status == "WARNING":
                warning_count += 1
            else:
                nok_count += 1

        total = len(measurements)
        if nok_count > 0:
            result = "NOK"
        elif warning_count > total * 0.2:
            result = "WARNING"
        else:
            result = "OK"

        data["measurements"] = measurements
        data["average_tension"] = sum(tensions) / total
        data["min_tension"] = min(tensions)
        data["max_tension"] = max(tensions)
        data["ok_count"] = ok_count
        data["warning_count"] = warning_count
        data["nok_count"] = nok_count
        data["result"] = result
        return TensionRecord.from_dict(data)

    average = _to_float(data.get("average_tension"), 0.0)
    data["result"] = criteria.classify(average)
    data["ok_count"] = 1 if data["result"] == "OK" else 0
    data["warning_count"] = 1 if data["result"] == "WARNING" else 0
    data["nok_count"] = 1 if data["result"] == "NOK" else 0
    return TensionRecord.from_dict(data)


def reclassify_tension_history(
    history: list[TensionRecord],
    criteria: TensionAcceptance | None,
) -> list[TensionRecord]:
    """Reclassifica uma lista de registros de tensao."""
    return [reclassify_tension_record(record, criteria) for record in (history or [])]


def _to_float(value: Any, default: float = 0.0) -> float:
    if value in (None, ""):
        return default
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip().replace(",", "."))
    except (TypeError, ValueError):
        return default
