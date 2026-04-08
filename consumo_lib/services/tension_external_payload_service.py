"""
Build, persist, and send external integration payloads for tension measurements.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from urllib import error, request


class TensionExternalPayloadService:
    """Create JSON payloads compatible with the external tension API."""

    BASE_OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "tension_routines"
    DEFAULT_PAYLOAD_DIR = BASE_OUTPUT_DIR / "integration_payloads"
    DEFAULT_SEND_LOG_DIR = BASE_OUTPUT_DIR / "integration_send_logs"

    def __init__(
        self,
        output_dir: Optional[Path] = None,
        send_log_dir: Optional[Path] = None,
    ):
        self.output_dir = Path(output_dir) if output_dir is not None else self.DEFAULT_PAYLOAD_DIR
        self.send_log_dir = (
            Path(send_log_dir) if send_log_dir is not None else self.DEFAULT_SEND_LOG_DIR
        )

    def build_payload(
        self,
        *,
        stencil_code: str,
        measurements: list[dict[str, Any]],
        user_id: Any = None,
        line_name: Optional[str] = None,
        stencil_status: Any = None,
    ) -> dict[str, Any]:
        ordered_measurements = sorted(measurements, key=self._measurement_sort_key)
        tension_log = [self._build_log_entry(measurement) for measurement in ordered_measurements]

        return {
            "codigo_stencil": stencil_code,
            "idusuario": self._normalize_user_id(user_id),
            "nmlinha": (line_name or "").strip(),
            "idstencil_status": stencil_status,
            "log_tensao": tension_log,
        }

    def save_payload(
        self,
        payload: dict[str, Any],
        *,
        stencil_code: str,
        timestamp: Optional[str] = None,
    ) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)

        resolved_timestamp = self._normalize_timestamp(timestamp)
        safe_stencil_code = self._sanitize_filename_part(stencil_code)
        filename = f"external_tension_payload_{safe_stencil_code}_{resolved_timestamp}.json"
        filepath = self.output_dir / filename

        with open(filepath, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=4, ensure_ascii=False)

        return filepath

    def send_payload(
        self,
        payload: dict[str, Any],
        *,
        endpoint_url: str,
        payload_path: Optional[Path] = None,
        timeout_sec: float = 10.0,
    ) -> dict[str, Any]:
        attempt = {
            "timestamp": datetime.now().isoformat(),
            "endpoint_url": endpoint_url,
            "payload_path": str(payload_path) if payload_path is not None else None,
            "timeout_sec": timeout_sec,
            "send_log_path": None,
            "success": False,
            "status_code": None,
            "response_body": None,
            "error": None,
        }

        if not endpoint_url.strip():
            attempt["error"] = "endpoint_url not configured"
            log_path = self._append_send_attempt(attempt)
            attempt["send_log_path"] = str(log_path)
            return attempt

        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        http_request = request.Request(
            endpoint_url,
            data=body,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )

        try:
            with request.urlopen(http_request, timeout=float(timeout_sec)) as response:
                response_body = response.read().decode("utf-8", errors="replace")
                attempt["success"] = 200 <= response.status < 300
                attempt["status_code"] = response.status
                attempt["response_body"] = response_body[:2000] if response_body else ""
        except error.HTTPError as exc:
            response_body = exc.read().decode("utf-8", errors="replace")
            attempt["status_code"] = exc.code
            attempt["response_body"] = response_body[:2000] if response_body else ""
            attempt["error"] = f"HTTPError: {exc}"
        except error.URLError as exc:
            attempt["error"] = f"URLError: {exc}"
        except Exception as exc:
            attempt["error"] = f"{type(exc).__name__}: {exc}"

        log_path = self._append_send_attempt(attempt)
        attempt["send_log_path"] = str(log_path)
        return attempt

    def _append_send_attempt(self, attempt: dict[str, Any]) -> Path:
        self.send_log_dir.mkdir(parents=True, exist_ok=True)

        log_filename = f"tension_send_attempts_{datetime.now().strftime('%Y%m%d')}.jsonl"
        log_path = self.send_log_dir / log_filename

        with open(log_path, "a", encoding="utf-8") as stream:
            stream.write(json.dumps(attempt, ensure_ascii=False) + "\n")

        return log_path

    @staticmethod
    def _measurement_sort_key(measurement: dict[str, Any]) -> tuple[int, int, int]:
        index = measurement.get("index")
        if index is not None:
            try:
                return (0, int(index), 0)
            except (TypeError, ValueError):
                pass

        grid_position = measurement.get("grid_position") or {}
        if isinstance(grid_position, dict):
            row = grid_position.get("row", 0)
            col = grid_position.get("col", 0)
        else:
            row, col = 0, 0

        try:
            row = int(row)
        except (TypeError, ValueError):
            row = 0

        try:
            col = int(col)
        except (TypeError, ValueError):
            col = 0

        return (1, row, col)

    def _build_log_entry(self, measurement: dict[str, Any]) -> dict[str, Any]:
        value = measurement.get("parsed_value", measurement.get("tension"))
        try:
            normalized_value: Any = float(value) if value is not None else None
        except (TypeError, ValueError):
            normalized_value = value

        return {
            "valor_tensao": normalized_value,
            "unidade": self._normalize_unit(measurement.get("unit")),
        }

    @staticmethod
    def _normalize_user_id(user_id: Any) -> Any:
        if user_id is None:
            return None

        if isinstance(user_id, str):
            stripped = user_id.strip()
            if not stripped:
                return None
            if stripped.isdigit():
                return int(stripped)
            return stripped

        if isinstance(user_id, float) and user_id.is_integer():
            return int(user_id)

        return user_id

    @staticmethod
    def _normalize_unit(unit: Any) -> str:
        normalized = str(unit or "").strip()
        normalized_ascii = normalized.replace("²", "2").replace("Â²", "2").replace("Ã‚Â²", "2")
        unit_map = {
            "N/cm2": "N/cm",
            "kg/cm2": "kg/cm",
            "lb/cm2": "lb/cm",
        }
        return unit_map.get(normalized_ascii, normalized or "N/cm")

    @staticmethod
    def _normalize_timestamp(timestamp: Optional[str]) -> str:
        if isinstance(timestamp, str) and timestamp.strip():
            safe = timestamp.strip().replace(":", "").replace("-", "").replace("T", "_")
            return safe.replace(".", "_")
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    @staticmethod
    def _sanitize_filename_part(value: str) -> str:
        safe_chars = []
        for char in value:
            if char.isalnum() or char in ("-", "_"):
                safe_chars.append(char)
            else:
                safe_chars.append("_")
        return "".join(safe_chars) or "stencil"
